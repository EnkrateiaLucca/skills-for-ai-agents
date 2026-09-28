## The branded-handout Skill (Chapter 2)

Chapter 2 uses the branded-handout Skill to show what each of the three optional folders is for, quoting a few lines of its SKILL.md along the way. This section holds the complete SKILL.md and its three reference files. The script and the two brand assets are in the book's repository at https://github.com/EnkrateiaLucca/skills-for-ai-agents, in the `ch2/branded-handout/` folder.

The Skill follows one placement rule. Instructions that apply to every handout, including the voice and style rules, live in SKILL.md. Instructions that only some handouts need live in `references/`, one file per handout type. SKILL.md names the file to read for each type.

````text
branded-handout/
├── SKILL.md
├── scripts/
│   └── create-handout.py
├── references/
│   ├── course-handouts.md
│   ├── social-posts.md
│   └── technical-explanations.md
└── assets/
    ├── logo.svg
    └── footer-mark.svg
````

The full SKILL.md:

````markdown
---
name: branded-handout
description: Generates branded PDF handouts (cheat sheets, study sheets, reference cards, workshop material) in the Automata Learning Lab style from a PDF, a markdown file, URLs, or a raw topic. Use when the user asks for a handout, cheat sheet, reference card, course or workshop material, or a "branded PDF", or wants to turn content into a polished document to share.
---

# Branded Handout

Turn source material into a print-ready PDF handout in the Automata Learning Lab style. You decide what goes into the handout and write it as JSON. `scripts/create-handout.py` validates that JSON and renders the PDF, so every handout gets the same fonts, colors, logo, and layout.

## Workflow

Copy this checklist and check off each step:

```
- [ ] 1. Gather the content
- [ ] 2. Pick the handout type
- [ ] 3. Write handout.json
- [ ] 4. Render the PDF
- [ ] 5. Check the PDF and report
```

### 1. Gather the content

- **File** (PDF, markdown, text): read it and pull out the concepts, steps, and commands a reader needs.
- **URLs**: fetch each page and keep only what the reader can act on.
- **Topic**: use what you know. Search the web for anything that changes often, such as versions, prices, and APIs.

### 2. Pick the handout type

The rules in "Voice and style" below apply to every handout. Some handout types need extra rules. Read the matching file before you write:

- Cheat sheet or reference card (default): nothing extra.
- Workshop or course material (class, lesson, students, exercises): read `references/course-handouts.md`.
- Handout meant to be shared online (LinkedIn, Instagram, "post this"): read `references/social-posts.md`.
- Handout that teaches code, CLI tools, APIs, or AI workflows: read `references/technical-explanations.md`.

If a request matches two types, read both files.

### 3. Write handout.json

Save the content as `handout.json` in the working directory:

```json
{
  "title": "Main handout title",
  "subtitle": "Optional context line",
  "accent_color": "coral",
  "sections": [
    {
      "heading": "Section title",
      "body": "Optional paragraph.",
      "items": [
        "Plain bullet",
        {"bold": "Key term", "text": "Explanation of the term"}
      ],
      "callout": {"type": "tip", "title": "Optional title", "text": "Callout text"},
      "code": {"language": "bash", "content": "uv run app.py"},
      "subsections": [
        {"heading": "Subsection title", "items": ["Bullet"]}
      ]
    }
  ],
  "footer_note": "Optional footer text, such as a URL"
}
```

- `title` and `sections` are required. Every section and subsection needs a `heading`.
- `accent_color`: `coral` (default), `golden`, `sage`, or `sky`.
- `callout.type`: `info`, `tip` (default), `success`, or `alert`.
- Subsections take the same fields as sections and nest one level deep.

### 4. Render the PDF

Run the generator on the file you wrote:

`uv run scripts/create-handout.py handout.json --out handouts/`

The script checks the JSON before rendering. If it reports a missing or invalid field, fix `handout.json` and run it again. Do not edit the script to get past an error.

### 5. Check the PDF and report

Open the PDF and check two things: every heading sits on the same page as the content below it, and the handout fits the length the user asked for (two pages or fewer by default). If it runs long, cut content in `handout.json` and render again. Then give the user the PDF path.

## Voice and style (every handout)

- The title names what the reader will be able to do: "Write Prompts That Return JSON", not "Prompting Guide".
- Headings are labels a reader can scan: "Install the CLI", not "Getting Started".
- One idea per bullet. Bold the key term at the start.
- Explain each term in one sentence the first time it appears.
- Use at most one callout per section. Save it for a mistake the reader is likely to make or a tip that saves real time.
- Write direct, second-person instructions. No hype words ("unlock", "supercharge", "game-changer") and no exclamation marks.
- Put every command, file path, and code snippet in a `code` block.
- Order each section from the general idea to the specific step.

## Brand assets

The script places `assets/logo.svg` at the top of the first page and `assets/footer-mark.svg` in the footer. Never draw, generate, or restyle a logo, and never add other brand images. To update the brand, replace the file in `assets/` and keep its name.

The script also handles fonts, colors, borders, and the four-color accent bar. Pick one `accent_color` per handout.

## Requirements

- `uv`. The script declares its own Python dependencies inline.
- Chromium for Playwright. If rendering fails with a missing-browser error, run `uvx playwright install chromium` once and render again.
````

`references/course-handouts.md`, read for workshop and course material:

````markdown
# Course and workshop handouts

Read this when the handout supports a class, workshop, lesson, or exercise session.

## Structure

1. **Learning goals** as the first section: three to five bullets that start with a verb ("Write", "Run", "Compare").
2. **Setup** next, if the session needs installs, API keys, or files to download. Nothing else can start before setup, so it goes before any concept.
3. **One section per lesson block**, in the order the instructor teaches them. When the user provides slide or lesson titles, reuse them as headings.
4. **One exercise inside each block**: the task, the expected result, and a hint in a `tip` callout.
5. **Recap** as the last section: the commands or rules a student should keep after the session.

## Rules

- Write for a student who missed the explanation. Each exercise must be doable from the handout alone.
- Number exercises across the whole handout (Exercise 1, 2, 3...) so the instructor can point to them.
- Leave the answers out. If the user asks for a solutions version, render a second handout with `"subtitle": "Solutions"`.
- Put the course name and session date in `footer_note` when the user provides them.
- Workshop handouts can run to four pages. Keep each lesson block on one page.

## Example exercise section

```json
{
  "heading": "Exercise 2: Call the API from Python",
  "body": "Send one prompt and print the reply.",
  "code": {"language": "bash", "content": "uv run call_api.py \"Summarize this paragraph\""},
  "callout": {
    "type": "tip",
    "title": "Hint",
    "text": "The key goes in the ANTHROPIC_API_KEY environment variable, never in the script."
  }
}
```
````

`references/social-posts.md`, read for handouts meant to be shared online:

````markdown
# Handouts for social media

Read this when the handout will be shared as a post (LinkedIn, Instagram, X) rather than handed out in a class.

People read a social handout on a phone, in a feed, without having asked for it. The first screen decides whether they keep reading.

## Structure

- One page. Use two only if the user asks.
- Three to five sections. A full reference belongs in a course handout.
- The title states the payoff in eight words or fewer: "7 Git Commands That Undo Mistakes".
- The subtitle says who it is for: "For developers who just ran the wrong command".
- The first section delivers something useful right away. No introduction and no "why this matters" section.

## Rules

- Keep bullets under 12 words.
- Use one `code` block at most, under eight lines. Long code is unreadable on a phone.
- Use `coral` or `sky` as the `accent_color`. Both hold up at thumbnail size.
- Put the author's handle or site in `footer_note`, so the file keeps its attribution when it is reshared.
- End on the most useful item. No "Conclusion" or "Summary" section.

## Checklist before rendering

- [ ] The title promises one concrete result.
- [ ] Each bullet makes sense without the one before it.
- [ ] The handout fits on one page.
````

`references/technical-explanations.md`, read for handouts that teach code, tools, or AI workflows:

````markdown
# Explaining code, tools, and AI workflows

Read this when the handout teaches code, a CLI tool, an API, or an AI workflow.

## Order of explanation

For each concept, give the reader:

1. What it does, in one plain sentence.
2. The smallest working example, as a command or code.
3. What the output looks like, or what changes after running it.
4. The most common mistake, in an `alert` callout, if there is one worth the space.

## Code blocks

- Every code block must run as written. Use a placeholder like `<your-file>` only for a value the reader must supply, and say what goes there.
- Set `code.language` (`python`, `bash`, `json`) so the block gets a caption.
- Keep blocks under 15 lines. Split longer code into numbered steps.
- Show macOS and Linux commands. Add a Windows variant only if the user asks.

## AI concepts

- Define a term by what the reader can do with it: "A system prompt sets rules the model follows for the whole conversation", not "A system prompt is a special type of message".
- When behavior depends on a model, library, or tool version, name the version in the section body.
- Show a real input and a real output instead of describing them.

## Parameter lists

Use `{"bold": ..., "text": ...}` items for flags and parameters:

```json
{"bold": "--out", "text": "Folder for the PDF. The script creates it if it does not exist."}
```
````
