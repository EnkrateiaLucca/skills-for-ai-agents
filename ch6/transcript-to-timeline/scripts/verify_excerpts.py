#!/usr/bin/env python3
"""
Verify that every selected excerpt is a byte-exact, contiguous substring of a
single transcript line -- the condition DaVinci Resolve needs to match the text.

Checks performed:
  1. EXACT      -- excerpt appears verbatim inside one line's text
  2. SINGLE     -- excerpt never spans two lines
  3. ORDER      -- excerpts are in chronological source order
  4. DUPLICATE  -- no excerpt repeated (normalised comparison)
  5. TRUNCATED  -- excerpt ends on sentence-final punctuation
  6. FILLER     -- reports internal filler that could not be trimmed away

Any failure of 1-4 is fatal: the script exits non-zero and reports. Do not
deliver a partial file -- stop and report to the user.

Usage:
    python verify_excerpts.py --source INPUT.txt --excerpts saida.txt [--fps 25] [--json]
"""

import argparse
import json
import re
import sys
import unicodedata

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from parse_transcript import parse  # noqa: E402

FILLER_PT = [
    "tipo", "né", "ne", "assim", "então tipo", "ãh", "ah", "eh", "hum",
    "sabe", "digamos", "quer dizer", "é isso", "pronto", "tá", "ok assim",
]
FILLER_EN = [
    "um", "uh", "erm", "like", "you know", "i mean", "sort of", "kind of",
    "basically", "actually", "right?", "so yeah",
]
SENTENCE_END = (".", "!", "?", "…", '."', '?"', '!"', ".)", "?)", "!)", ".'", "?'", "!'")


def norm(s):
    """Normalise for duplicate comparison only -- never for matching."""
    s = unicodedata.normalize("NFKC", s).casefold()
    return re.sub(r"\s+", " ", s).strip()


def read_excerpts(path):
    """Excerpts are blank-line-separated blocks."""
    with open(path, "r", encoding="utf-8") as fh:
        raw = fh.read()
    return [b.strip("\n").strip() for b in re.split(r"\n\s*\n", raw) if b.strip()]


def find_filler(text):
    low = " " + norm(text) + " "
    hits = []
    for w in FILLER_PT + FILLER_EN:
        if re.search(r"(?<![\w])" + re.escape(w) + r"(?![\w])", low):
            hits.append(w)
    return hits


def verify(source, excerpts_path, fps=25.0):
    lines = parse(source, fps)
    texts = [ln["text"] for ln in lines]
    excerpts = read_excerpts(excerpts_path)

    results, fatal = [], []
    last_line_idx = -1

    for i, ex in enumerate(excerpts):
        r = {"n": i + 1, "excerpt": ex, "errors": [], "warnings": []}

        if "\n" in ex:
            r["errors"].append("MULTILINHA: o trecho contém quebra de linha "
                               "(tem de caber numa única linha do transcript).")

        matches = [j for j, t in enumerate(texts) if ex in t]
        if not matches:
            r["errors"].append("NAO_ENCONTRADO: o texto não corresponde "
                               "exatamente a nenhuma linha do ficheiro original.")
        else:
            line_idx = matches[0]
            ln = lines[line_idx]
            r["line_index"] = line_idx
            r["start_tc"] = ln["start_tc"]
            r["occurrences"] = len(matches)

            if len(ex.split()) == ln["word_count"] and ex == ln["text"]:
                r["duration_s"] = ln["duration_s"]
                r["duration_method"] = "B/timecode"
            else:
                share = len(ex.split()) / max(ln["word_count"], 1)
                r["duration_s"] = round(ln["duration_s"] * share, 1)
                r["duration_method"] = "A/estimativa"

            if line_idx < last_line_idx:
                r["errors"].append(
                    f"FORA_DE_ORDEM: aparece na linha {line_idx}, depois da linha {last_line_idx}."
                )
            last_line_idx = max(last_line_idx, line_idx)

        if not ex.endswith(SENTENCE_END):
            r["warnings"].append("TRUNCADO: não termina em pontuação final de frase.")

        filler = find_filler(ex)
        if filler:
            r["warnings"].append("FILLER: " + ", ".join(sorted(set(filler))))

        results.append(r)

    seen = {}
    for r in results:
        key = norm(r["excerpt"])
        if key in seen:
            r["errors"].append(f"DUPLICADO: idêntico ao trecho #{seen[key]}.")
        else:
            seen[key] = r["n"]

    for r in results:
        if r["errors"]:
            fatal.append(r)

    total = sum(r.get("duration_s", 0) for r in results)
    return {
        "source": source,
        "excerpt_count": len(results),
        "total_duration_s": round(total, 1),
        "total_duration_mmss": f"{int(total // 60)}m{int(total % 60):02d}s",
        "fatal_count": len(fatal),
        "results": results,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--excerpts", required=True)
    ap.add_argument("--fps", type=float, default=25.0)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rep = verify(args.source, args.excerpts, args.fps)

    if args.json:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    else:
        print(f"Trechos: {rep['excerpt_count']}   "
              f"Duração estimada: {rep['total_duration_mmss']}   "
              f"Erros fatais: {rep['fatal_count']}")
        for r in rep["results"]:
            if r["errors"] or r["warnings"]:
                head = r["excerpt"][:70] + ("..." if len(r["excerpt"]) > 70 else "")
                print(f"\n#{r['n']} [{r.get('start_tc', '??')}] {head}")
                for e in r["errors"]:
                    print(f"   ERRO   {e}")
                for w in r["warnings"]:
                    print(f"   AVISO  {w}")

    sys.exit(1 if rep["fatal_count"] else 0)


if __name__ == "__main__":
    main()
