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
