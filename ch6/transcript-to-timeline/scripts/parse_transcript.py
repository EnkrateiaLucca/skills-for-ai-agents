#!/usr/bin/env python3
"""
Parse a DaVinci Resolve .txt transcript export into structured lines and
self-contained chunks.

Input format (speaker label optional):
    [00:00:00:00 - 00:00:07:00] Marina: When people picture the Amazon...
    [00:00:07:00 - 00:00:21:00] The first thing to understand is...

Output: JSON with one entry per transcript line, grouped into chunks that
never split a line. Timecodes and speaker labels are metadata for the agent
only -- they must never appear in the final excerpt file.

Usage:
    python parse_transcript.py INPUT.txt --out parsed.json [--chunk-words 3000] [--fps 25]
    python parse_transcript.py INPUT.txt --out parsed.json --chunk 1   # print one chunk
"""

import argparse
import json
import re
import sys

# [HH:MM:SS:FF - HH:MM:SS:FF] optionally followed by "Speaker: "
LINE_RE = re.compile(
    r"^\s*\[\s*(\d{1,2}:\d{2}:\d{2}[:.;]\d{1,3})\s*-\s*(\d{1,2}:\d{2}:\d{2}[:.;]\d{1,3})\s*\]\s*(.*)$"
)
# A speaker label: short, no sentence punctuation, followed by a colon.
SPEAKER_RE = re.compile(r"^([^:]{1,40}?):\s+(.*)$")


def tc_to_seconds(tc, fps):
    parts = re.split(r"[:.;]", tc)
    h, m, s, f = (int(p) for p in parts)
    return h * 3600 + m * 60 + s + (f / fps if fps else 0)


def looks_like_speaker(candidate):
    """Speaker labels are short names, not sentence fragments."""
    if not candidate or len(candidate) > 40:
        return False
    if any(ch in candidate for ch in ".!?,;"):
        return False
    return len(candidate.split()) <= 4


def parse(path, fps=25.0):
    with open(path, "r", encoding="utf-8-sig") as fh:
        raw_lines = fh.read().splitlines()

    entries = []
    for raw in raw_lines:
        if not raw.strip():
            continue
        m = LINE_RE.match(raw)
        if not m:
            # Continuation of the previous line (soft-wrapped export).
            if entries:
                entries[-1]["text"] = entries[-1]["text"].rstrip() + " " + raw.strip()
            continue

        start_tc, end_tc, rest = m.group(1), m.group(2), m.group(3)
        speaker = None
        sm = SPEAKER_RE.match(rest)
        if sm and looks_like_speaker(sm.group(1)):
            speaker, rest = sm.group(1).strip(), sm.group(2)

        entries.append(
            {
                "index": len(entries),
                "start_tc": start_tc,
                "end_tc": end_tc,
                "start_s": round(tc_to_seconds(start_tc, fps), 3),
                "end_s": round(tc_to_seconds(end_tc, fps), 3),
                "speaker": speaker,
                "text": rest.strip(),
            }
        )

    for e in entries:
        e["duration_s"] = round(e["end_s"] - e["start_s"], 2)
        e["word_count"] = len(e["text"].split())

    return entries


def chunk(entries, chunk_words=3000):
    """Group lines into chunks of ~chunk_words, cutting only at line boundaries."""
    chunks, current, words = [], [], 0
    for e in entries:
        current.append(e)
        words += e["word_count"]
        if words >= chunk_words:
            chunks.append(current)
            current, words = [], 0
    if current:
        chunks.append(current)

    return [
        {
            "chunk_id": i + 1,
            "line_from": c[0]["index"],
            "line_to": c[-1]["index"],
            "word_count": sum(x["word_count"] for x in c),
            "start_tc": c[0]["start_tc"],
            "end_tc": c[-1]["end_tc"],
            "lines": c,
        }
        for i, c in enumerate(chunks)
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--out", default=None, help="write full parsed JSON here")
    ap.add_argument("--chunk-words", type=int, default=3000)
    ap.add_argument("--fps", type=float, default=25.0)
    ap.add_argument("--chunk", type=int, default=None, help="print only this chunk id")
    ap.add_argument("--summary", action="store_true", help="print counts only")
    args = ap.parse_args()

    entries = parse(args.input, args.fps)
    if not entries:
        print("ERRO: nenhuma linha com timecode reconhecida. Verifique o formato do ficheiro.",
              file=sys.stderr)
        sys.exit(2)

    chunks = chunk(entries, args.chunk_words)
    doc = {
        "source": args.input,
        "fps": args.fps,
        "line_count": len(entries),
        "word_count": sum(e["word_count"] for e in entries),
        "total_duration_s": round(entries[-1]["end_s"] - entries[0]["start_s"], 2),
        "chunk_count": len(chunks),
        "chunks": chunks,
    }

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=1)

    if args.summary:
        print(json.dumps({k: v for k, v in doc.items() if k != "chunks"},
                         ensure_ascii=False, indent=1))
    elif args.chunk is not None:
        sel = next((c for c in chunks if c["chunk_id"] == args.chunk), None)
        if sel is None:
            print(f"ERRO: chunk {args.chunk} nao existe (total: {len(chunks)})", file=sys.stderr)
            sys.exit(2)
        print(json.dumps(sel, ensure_ascii=False, indent=1))
    elif not args.out:
        print(json.dumps(doc, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
