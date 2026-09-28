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
