#!/usr/bin/env python3
"""Build a compact CMX 3600 EDL from verified verbatim transcript excerpts.

Import the result in DaVinci Resolve with File > Import > Timeline. Do not use
Pre-conformed EDL; that workflow is for notching a flattened master rather than
assembling selected source ranges into a compact sequence.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_transcript import parse  # noqa: E402


SNAP_WINDOW_S = 1.5
SILENCE_DURATION_S = 0.18
SUPPORTED_NOMINAL_FPS = {24, 25, 30, 50, 60}


def fail(message):
    raise SystemExit(f"ERRO: {message}")


def capture(command, label):
    proc = subprocess.run(command, capture_output=True, text=True)
    if proc.returncode:
        detail = (proc.stderr or proc.stdout).strip().splitlines()
        fail(f"{label} falhou" + (f": {detail[-1]}" if detail else "."))
    return proc.stdout


def probe_video(path):
    if not shutil.which("ffprobe"):
        fail("ffprobe não está disponível no PATH.")
    raw = capture(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=avg_frame_rate,r_frame_rate:format=duration",
            "-of", "json", str(path),
        ],
        "ffprobe",
    )
    doc = json.loads(raw)
    streams = doc.get("streams") or []
    if not streams:
        fail("o ficheiro indicado não contém vídeo.")
    rate = streams[0].get("avg_frame_rate")
    if not rate or rate == "0/0":
        rate = streams[0].get("r_frame_rate")
    try:
        actual_fps = float(Fraction(rate))
        duration_s = float(doc["format"]["duration"])
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        fail("não foi possível determinar frame rate e duração do vídeo.")
    nominal_fps = round(actual_fps)
    if nominal_fps not in SUPPORTED_NOMINAL_FPS or abs(actual_fps - nominal_fps) > 0.11:
        fail(
            f"frame rate {actual_fps:.6f} não é compatível com este gerador "
            f"(nominais suportados: {sorted(SUPPORTED_NOMINAL_FPS)})."
        )
    return actual_fps, nominal_fps, duration_s


def tc_to_frames(tc, nominal_fps):
    parts = re.split(r"[:.;]", tc)
    if len(parts) != 4:
        fail(f"timecode inválido: {tc}")
    h, m, s, f = (int(value) for value in parts)
    if f >= nominal_fps:
        fail(f"frame {f} inválido para {nominal_fps} fps em {tc}.")
    return ((h * 60 + m) * 60 + s) * nominal_fps + f


def frames_to_tc(frames, nominal_fps):
    if frames < 0:
        fail("timecode negativo não é permitido.")
    frame = frames % nominal_fps
    seconds = frames // nominal_fps
    return (
        f"{seconds // 3600:02d}:{seconds // 60 % 60:02d}:"
        f"{seconds % 60:02d}:{frame:02d}"
    )


def silence_midpoints(media, start_s=None, duration_s=None):
    if not shutil.which("ffmpeg"):
        fail("ffmpeg não está disponível no PATH.")
    command = ["ffmpeg", "-hide_banner", "-nostats"]
    if start_s is not None:
        command += ["-ss", f"{start_s:.6f}"]
    if duration_s is not None:
        command += ["-t", f"{duration_s:.6f}"]
    command += [
        "-i", str(media), "-vn",
        "-af", f"silencedetect=noise=-35dB:d={SILENCE_DURATION_S}",
        "-f", "null", "-",
    ]
    proc = subprocess.run(command, capture_output=True, text=True)
    if proc.returncode:
        fail(f"não foi possível analisar pausas em {media.name}.")
    starts = [float(v) for v in re.findall(r"silence_start: ([\d.]+)", proc.stderr)]
    ends = [float(v) for v in re.findall(r"silence_end: ([\d.]+)", proc.stderr)]
    return [(a + b) / 2 for a, b in zip(starts, ends)]


def read_excerpts(path):
    raw = path.read_text(encoding="utf-8")
    return [block.strip("\n").strip() for block in re.split(r"\n\s*\n", raw) if block.strip()]


def nearest_pause(guess, pauses, edge, duration):
    if abs(guess - edge) < 0.35:
        return edge
    candidates = [pause for pause in pauses if abs(pause - guess) <= SNAP_WINDOW_S]
    return min(candidates, key=lambda pause: abs(pause - guess)) if candidates else guess


def build_events(args, actual_fps, nominal_fps, video_duration_s):
    transcript_lines = parse(str(args.transcript), nominal_fps)
    if not transcript_lines:
        fail("nenhuma linha com timecode foi reconhecida na transcrição.")
    excerpts = read_excerpts(args.excerpts)
    if not excerpts:
        fail("o ficheiro de seleção não contém trechos.")

    video_frames = round(video_duration_s * actual_fps)
    events = []
    last_source_in = -1

    for number, excerpt in enumerate(excerpts, 1):
        hits = [idx for idx, line in enumerate(transcript_lines) if excerpt in line["text"]]
        if not hits:
            fail(f"trecho #{number} não corresponde exatamente à transcrição: {excerpt[:90]}")
        if len(hits) > 1:
            fail(f"trecho #{number} aparece em {len(hits)} linhas; posição ambígua.")

        line_index = hits[0]
        line = transcript_lines[line_index]
        if line["text"].count(excerpt) > 1:
            fail(f"trecho #{number} repete-se dentro da mesma linha; posição ambígua.")

        line_in = tc_to_frames(line["start_tc"], nominal_fps)
        line_out = tc_to_frames(line["end_tc"], nominal_fps)
        line_frames = line_out - line_in
        if line_frames <= 0:
            fail(f"linha {line_index} tem duração inválida.")
        line_duration_s = line_frames / actual_fps

        offset_chars = line["text"].index(excerpt)
        whole_line = excerpt == line["text"]
        if whole_line:
            start_offset_s, end_offset_s = 0.0, line_duration_s
            method = "timecodes exatos (linha inteira)"
        else:
            start_guess = offset_chars / len(line["text"]) * line_duration_s
            end_guess = (offset_chars + len(excerpt)) / len(line["text"]) * line_duration_s

            wav = args.audio_dir / f"{line_index:04d}.wav" if args.audio_dir else None
            if wav and wav.exists():
                pauses = silence_midpoints(wav)
                pause_source = wav.name
            else:
                pauses = silence_midpoints(
                    args.video,
                    start_s=line_in / actual_fps,
                    duration_s=line_duration_s,
                )
                pause_source = args.video.name

            start_offset_s = nearest_pause(start_guess, pauses, 0.0, line_duration_s)
            end_offset_s = nearest_pause(end_guess, pauses, line_duration_s, line_duration_s)
            if end_offset_s - start_offset_s <= 0.5:
                start_offset_s, end_offset_s = start_guess, end_guess
                method = "estimativa proporcional; snap rejeitado"
            else:
                method = (
                    f"pausas em {pause_source} "
                    f"({start_guess:.2f}->{start_offset_s:.2f}, "
                    f"{end_guess:.2f}->{end_offset_s:.2f})"
                )

        source_in = line_in + round(start_offset_s * actual_fps)
        source_out = line_in + round(end_offset_s * actual_fps)
        if source_out <= source_in:
            fail(f"trecho #{number} gerou um evento vazio.")
        if source_in < 0 or source_out > video_frames + 1:
            fail(f"trecho #{number} fica fora da duração do vídeo.")
        if source_in < last_source_in:
            fail(f"trecho #{number} está fora da ordem cronológica.")
        last_source_in = source_in

        events.append(
            {
                "number": number,
                "source_in": source_in,
                "source_out": source_out,
                "length": source_out - source_in,
                "method": method,
                "excerpt": excerpt,
            }
        )

    return events


def render_edl(args, events, nominal_fps):
    record = tc_to_frames(args.record_start, nominal_fps)
    lines = [f"TITLE: {args.title}", "FCM: NON-DROP FRAME"]
    clip_name = args.video.name

    for event in events:
        source_in = frames_to_tc(event["source_in"], nominal_fps)
        source_out = frames_to_tc(event["source_out"], nominal_fps)
        record_in = frames_to_tc(record, nominal_fps)
        record += event["length"]
        record_out = frames_to_tc(record, nominal_fps)
        lines.append(
            f"{event['number']:03d}  {args.reel:<8}  {args.channel:<6}{'C':<9}"
            f"{source_in} {source_out} {record_in} {record_out}"
        )
        lines.append(f"* FROM CLIP NAME: {clip_name}")

    text = "\n".join(lines) + "\n"
    if text.count("* FROM CLIP NAME:") != len(events):
        fail("validação interna falhou: comentários de clip incompletos.")
    args.out.write_text(text, encoding="utf-8")
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--excerpts", required=True, type=Path)
    parser.add_argument("--transcript", required=True, type=Path)
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--audio-dir", type=Path)
    parser.add_argument("--reel", default="AX")
    parser.add_argument("--channel", default="AA/V")
    parser.add_argument("--record-start", default="00:00:00:00")
    parser.add_argument("--title", default="DECUPAGEM")
    args = parser.parse_args()

    for path, label in (
        (args.excerpts, "seleção"),
        (args.transcript, "transcrição"),
        (args.video, "vídeo"),
    ):
        if not path.is_file():
            fail(f"{label} não encontrado: {path}")
    if args.audio_dir and not args.audio_dir.is_dir():
        fail(f"diretório de áudio não encontrado: {args.audio_dir}")
    if args.out.suffix.lower() != ".edl":
        fail("o ficheiro de saída deve ter extensão .edl.")

    actual_fps, nominal_fps, duration_s = probe_video(args.video)
    events = build_events(args, actual_fps, nominal_fps, duration_s)
    record_end = render_edl(args, events, nominal_fps)
    record_start = tc_to_frames(args.record_start, nominal_fps)

    for event in events:
        print(
            f"#{event['number']}  "
            f"{frames_to_tc(event['source_in'], nominal_fps)} -> "
            f"{frames_to_tc(event['source_out'], nominal_fps)}  "
            f"{event['length'] / actual_fps:.2f}s  [{event['method']}]"
        )
    total_s = sum(event["length"] for event in events) / actual_fps
    print(
        f"\n{args.out}  ({len(events)} eventos, {total_s:.2f}s, "
        f"vídeo {actual_fps:.6f} fps / EDL {nominal_fps} fps NDF, "
        f"record out {frames_to_tc(record_end, nominal_fps)})"
    )
    if record_end - record_start != sum(event["length"] for event in events):
        fail("validação interna falhou: record timeline descontínua.")


if __name__ == "__main__":
    main()
