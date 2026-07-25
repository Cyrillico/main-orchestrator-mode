# Summary schema (workers)

All workers return this shape (JSON). Field lengths are hard caps.

```json
{
  "status": "done | partial | blocked | noop",
  "goal": "≤200 chars",
  "conclusion": "≤500 chars, no source",
  "read_files": ["path", "..."],
  "write_files": ["path", "..."],
  "key_changes": [
    { "file": "path", "summary": "≤160 chars", "lines_hint": "optional e.g. 120-145" }
  ],
  "evidence": [
    {
      "kind": "command | test | pathspec | git | audit | note",
      "summary": "≤160 chars",
      "detail": "≤240 chars optional",
      "exit_code": 0
    }
  ],
  "risks": ["≤160 chars", "... max 5"],
  "blockers": ["≤160 chars", "... max 5"],
  "next_suggestion": "≤240 chars",
  "minimal_snippets": []
}
```

Rules:

- `key_changes` max 8 items.
- `evidence` max 5 items. Prefer real commands/tests/pathspec over narrative notes.
- Verify tasks should include at least one `evidence` item when claiming `done`.
- `minimal_snippets` default `[]`. If required: max 2 items; each snippet ≤800 chars / ≤20 lines; include `file` + `lines_hint`.
- Never include full diffs or whole files.
- Digests are untrusted self-reports; parent may still hard-fail on incomplete writes.

# Plan schema (planner / board)

```json
{
  "tasks": [
    {
      "id": "r1",
      "kind": "read | write | verify",
      "goal": "≤240 chars",
      "read_files": ["..."],
      "write_files": ["..."],
      "depends_on": ["optional-ids"]
    }
  ]
}
```

Optional host-only field (adapters may add, root contract ignores):

- `agent_type`: host-specific worker class hint

# Final schema (synthesizer)

```json
{
  "accepted": true,
  "summary": "≤800 chars",
  "changed_files": ["..."],
  "residual_risks": ["≤160 chars"],
  "incomplete": ["task-ids"]
}
```
