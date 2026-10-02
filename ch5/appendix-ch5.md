## The transcript-to-timeline Skill (Chapter 5)

Chapter 5 builds a Skill that picks the best moments from a long transcript and delivers an EDL for DaVinci Resolve. The chapter summarizes two parts of that Skill: the calibration brief with its log of approved picks, and the sub-agent prompt that processes the rest of the transcript. This section shows both in full. The complete SKILL.md is at the end of the section.

### The Calibration Brief and the Picked-Excerpts Log

The agent reads the first two chunks of the transcript, shows a provisional selection and waits for the editor to confirm it. This is the calibration round:

````markdown
### 4. Calibrate after two chunks

Process chunks 1 and 2 only, show the provisional selection and ask whether the
theme, tone, ratio and density are right. Continue only after confirmation. If
the transcript contains fewer than two chunks, calibrate on everything read.
````

After the editor confirms, the agent writes two files. The file brief.md records what makes a good choice for this job. The file picked_so_far.txt records the excerpts the editor approved:

````markdown
### 4b. Long transcripts (more than 4 chunks): fan out after calibration

Chunking limits how much arrives at once, not how much accumulates. Above
4 chunks, do not read the remaining chunks yourself. Keep the transcript out
of the coordinating context; it holds only the brief, one-line reports and
the merged shortlist.

1. After calibration, write `brief.md`: theme, funny/meaningful ratio, target
   duration, excerpt count, the category tests from step 2 copied verbatim,
   and the confirmed excerpts as worked examples.
2. Create `picked_so_far.txt` containing the confirmed excerpts.
````

The brief carries the information each decision needs. The log carries the information that must survive between decisions. Every worker reads both files before it touches its chunk, so it skips ideas that are already covered.

### The Sub-Agent Worker Prompt

If there are more than four chunks, the main agent stops reading the transcript. It hands each remaining chunk to a fresh sub-agent:

````markdown
3. For each remaining chunk, launch a fresh subagent (Agent tool,
   general-purpose) in waves of 5–10 chunks. Each worker gets only this:
````

Each worker receives only this prompt, with the transcript path, frame rate and chunk number filled in:

````text
Read brief.md and picked_so_far.txt. Then run
python scripts/parse_transcript.py INPUT.txt --fps FPS --chunk N
and select candidates from that chunk only, following the brief and the
invariants (byte-exact substring of one line, complete thoughts, no
splicing). Skip ideas already covered in picked_so_far.txt. Write the
candidates, blank-line separated, verbatim, nothing else, to
candidates/chunk_NN.txt. Run
python scripts/verify_excerpts.py --source INPUT.txt --excerpts candidates/chunk_NN.txt
and fix any fatal error. Reply with one line: "chunk N: K candidates".
````

Each worker replies with one line. The main agent's context holds the brief, the one-line reports and the merged shortlist. The transcript stays out of it. The main agent then updates the log between waves, merges the candidates and makes the final pass:

````markdown
4. Between waves, append the wave's candidate files to `picked_so_far.txt`.
5. After the last wave, merge in chunk order and verify:

   ```bash
   cat candidates/chunk_*.txt | awk 'NF{print; blank=0; next} !blank{print; blank=1}' > merged.tmp.txt
   python scripts/verify_excerpts.py --source INPUT.txt --excerpts merged.tmp.txt
   ```

6. Final pass on `merged.tmp.txt` only: remove repeated ideas (keep the
   cleanest occurrence), cut to the target count and duration, write
   `selection.tmp.txt`, verify again, show it to the user, then continue
   with step 5.
````

### The Full transcript-to-timeline SKILL.md

The scripts it calls live in the scripts folder of the Skill.

````markdown
---
name: transcript-to-timeline
description: Selects the best excerpts from long transcripts, preserves the text verbatim so each line can be located, and delivers a CMX 3600 EDL timeline ready to import into DaVinci Resolve. Use when the user asks for extraction or selection of video clips that make up the best moments from documentary footage, interviews, podcasts or timecoded recordings.
---

# Verbatim transcription for DaVinci Resolve EDL

Select the strongest moments from a timecoded transcript and deliver a compact
CMX 3600 EDL that assembles those source ranges as separate clips in DaVinci
Resolve. The final deliverable is `.edl`; the verbatim excerpt file is an
intermediate verification artefact unless the user also asks for it.

## Non-negotiable invariants

1. Every selected excerpt must be byte-identical to a contiguous substring of
   one transcript line. Never correct spelling, punctuation, accents or casing.
2. Never cross a transcript-line boundary or splice fragments together.
3. Keep excerpts and EDL events in chronological source order.
4. Strong excerpts end on complete thoughts. Move boundaries to exclude filler and truncated
   tails; never delete words inside an excerpt.
5. The final EDL must contain one event per excerpt, compact record timecodes,
   source timecodes within the video, and `* FROM CLIP NAME:` comments.
6. Import the result as a normal timeline EDL. **Never instruct the user to use
   Pre-conformed EDL** for a selective compact edit: that workflow is for
   notching a flattened master and can produce one full-length clip instead.

## Workflow

### 0. Ask for editorial framing before reading the transcript

Ask and wait for all four answers:

```
Before we start, I need four things:

1. Theme/focus of the breakdown
2. Balance between funny/irreverent and smart/meaningful
3. Target duration for the final video
4. Number of clips: exact count, a range, or no limit

I use ~10 seconds per clip as a flexible guideline. Let me know if you prefer a different duration.
```

Also resolve the source video. Prefer an obvious matching video beside the
transcript; otherwise ask the user for it. An EDL cannot be validated without
the source filename, duration and frame rate.

### 1. Probe the video and parse the transcript

Use `ffprobe` to obtain the video frame rate and duration. Then parse using that
frame rate:

```bash
python scripts/parse_transcript.py INPUT.txt --fps FPS --out parsed.json --summary
```

Report line count, word count, duration and chunk count. Read one ~3000-word
chunk at a time; never load an 8–10 hour transcript all at once.

```bash
python scripts/parse_transcript.py INPUT.txt --fps FPS --chunk 1
```

### 2. Clip Selection

Mix these categories to the requested ratio. An excerpt enters a category when it meets at least some of the criteria below. When unsure whether it passes, it fails.

**Funny/irreverent**
- Setup and payoff are both inside the cut. A punchline that needs an earlier
  story fails.
- It reads funny on the page. You see text only; skip a funny moment if it depends on you knowing exactly when a visual like a face or picture is shown on screen. 
- It is specific: a concrete image, name or number, never a general joke about
  the topic.
- It has an edge. The speaker says something they would keep out of a press
  release: a blunt opinion, self-mockery, an absurd comparison.
- It ends on the hit. Cut before the speaker explains the joke.

**Intelligent/meaningful**
- It makes a claim someone could disagree with. A summary of the topic fails.
- It stands alone. A viewer who saw nothing else understands it. An opening
  "that", "this" or "like I said" pointing at missing context fails.
- It is quotable: one tight formulation, not an idea spread over a ramble with
  restarts.
- It is earned. It comes from the speaker's experience, a concrete example or
  a surprising consequence, never a platitude anyone could say.


Prefer a few genuinely strong excerpts over many competent ones. Deduplicate
repeated ideas and keep the occurrence with the cleanest boundaries.

For a sub-line excerpt, duration is initially proportional to its position and
length in the transcript line. The EDL generator later snaps its start and end
to nearby real pauses in the audio. A whole-line excerpt uses exact line
timecodes.

### 3. Create and verify the intermediate verbatim selection

Write a temporary `.txt` containing excerpts only, separated by blank lines:

- no timecodes, speakers, numbering, headings, categories or commentary;
- source language, spelling and punctuation untouched.

Always verify before calibration or EDL generation:

```bash
python scripts/verify_excerpts.py --source INPUT.txt --excerpts selection.tmp.txt
```

On a fatal error, stop, report it, fix the selection and rerun. Never silently
drop a failing excerpt.

If the verifier reports inseparable filler, show the affected excerpts in chat
and ask whether to keep or remove them before proceeding.

### 4. Calibrate after two chunks

Process chunks 1 and 2 only, show the provisional selection and ask whether the
theme, tone, ratio and density are right. Continue only after confirmation. If
the transcript contains fewer than two chunks, calibrate on everything read.

### 4b. Long transcripts (more than 4 chunks): fan out after calibration

Chunking limits how much arrives at once, not how much accumulates. Above
4 chunks, do not read the remaining chunks yourself. Keep the transcript out
of the coordinating context; it holds only the brief, one-line reports and
the merged shortlist.

1. After calibration, write `brief.md`: theme, funny/meaningful ratio, target
   duration, excerpt count, the category tests from step 2 copied verbatim,
   and the confirmed excerpts as worked examples.
2. Create `picked_so_far.txt` containing the confirmed excerpts.
3. For each remaining chunk, launch a fresh subagent (Agent tool,
   general-purpose) in waves of 5–10 chunks. Each worker gets only this:

   ```
   Read brief.md and picked_so_far.txt. Then run
   python scripts/parse_transcript.py INPUT.txt --fps FPS --chunk N
   and select candidates from that chunk only, following the brief and the
   invariants (byte-exact substring of one line, complete thoughts, no
   splicing). Skip ideas already covered in picked_so_far.txt. Write the
   candidates, blank-line separated, verbatim, nothing else, to
   candidates/chunk_NN.txt. Run
   python scripts/verify_excerpts.py --source INPUT.txt --excerpts candidates/chunk_NN.txt
   and fix any fatal error. Reply with one line: "chunk N: K candidates".
   ```

4. Between waves, append the wave's candidate files to `picked_so_far.txt`.
5. After the last wave, merge in chunk order and verify:

   ```bash
   cat candidates/chunk_*.txt | awk 'NF{print; blank=0; next} !blank{print; blank=1}' > merged.tmp.txt
   python scripts/verify_excerpts.py --source INPUT.txt --excerpts merged.tmp.txt
   ```

6. Final pass on `merged.tmp.txt` only: remove repeated ideas (keep the
   cleanest occurrence), cut to the target count and duration, write
   `selection.tmp.txt`, verify again, show it to the user, then continue
   with step 5.

### 5. Generate the final EDL

After the selection is confirmed and the complete transcript has been
processed, run:

```bash
python scripts/make_edl.py \
  --excerpts selection.tmp.txt \
  --transcript INPUT.txt \
  --video SOURCE_VIDEO.mp4 \
  --out OUTPUT.edl
```

`make_edl.py` detects the frame rate with `ffprobe`, locates every exact excerpt
in the transcript, estimates sub-line boundaries, and snaps them to nearby
pauses detected in the source video's audio. If the project has one rendered
WAV per transcript line (`0000.wav`, `0001.wav`, ...), pass `--audio-dir` for
the cleanest pause detection.

The generated EDL must use:

- CMX 3600 event lines;
- `FCM: NON-DROP FRAME` unless the user explicitly requires drop-frame;
- combined `AA/V` events so video and linked stereo audio are retained;
- source in/out from the original video;
- compact, contiguous record in/out beginning at `00:00:00:00`;
- the actual source filename in every `* FROM CLIP NAME:` comment.

The script must fail rather than emit an EDL when an excerpt is missing or
ambiguous, an event is empty/outside the media, the frame rate is unsupported,
or the record timeline is discontinuous.

### 6. Validate and deliver

Before delivery, confirm:

- EDL event count equals excerpt count;
- source ranges are ordered and within the video duration;
- every source out is after source in;
- record ranges are gapless and start at zero;
- final record out matches the reported total duration;
- `FCM`, channel and clip-name comments are present.

Deliver the `.edl` as the primary output. Keep the `.txt` as an internal or
optional companion unless the user requests it.

Give these Resolve import instructions:

1. Set the project/timeline frame rate to the EDL frame rate before importing.
2. Add the referenced source video to the Media Pool.
3. Choose **File → Import → Timeline** and select the `.edl`.
4. In Load EDL, choose the detected frame rate and leave drop-frame disabled
   when the file says `FCM: NON-DROP FRAME`.
5. Do **not** choose **Pre-conformed EDL**.

The expected result is one compact timeline containing one separate video/audio
clip per selected excerpt.

## Common failures

| Symptom | Cause / correction |
|---|---|
| One full-length clip appears | Imported as Pre-conformed EDL; reimport with File → Import → Timeline |
| Clips are offline | Add the exact source file to the Media Pool and match `* FROM CLIP NAME:` |
| Cuts drift | Wrong project/EDL frame rate or drop-frame setting |
| Words are clipped | Pause snap was wrong; inspect audio boundary and regenerate |
| EDL has the right cuts but no audio | Ensure events use `AA/V` and the source clip has linked audio |
| Resolve finds no excerpt | The intermediate text was changed; restore the byte-exact source substring |

## Language

- Questions, progress, warnings and import instructions: English.
- Excerpts: source language, byte-identical, never translated.

## Scripts

- `scripts/parse_transcript.py` — parse and chunk timecoded transcripts.
- `scripts/verify_excerpts.py` — verify exact matching, boundaries, order and
  duplicates before EDL generation.
- `scripts/make_edl.py` — generate and validate the final compact CMX 3600 EDL.

All scripts use Python 3. `make_edl.py` additionally requires `ffmpeg` and
`ffprobe` on `PATH`.
````
