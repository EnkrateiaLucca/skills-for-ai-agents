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
