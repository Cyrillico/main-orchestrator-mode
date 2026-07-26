# Summary schema

```json
{
  "status": "done | partial | blocked | noop",
  "goal": "≤200 chars",
  "conclusion": "≤500 chars",
  "read_files": ["path"],
  "write_files": ["path"],
  "key_changes": [{"file":"path","summary":"≤160","lines_hint":"optional"}],
  "evidence": [{"kind":"command|test|pathspec|git|audit|note","summary":"≤160","detail":"≤240","exit_code":0}],
  "risks": ["≤160"],
  "blockers": ["≤160"],
  "next_suggestion": "≤240",
  "minimal_snippets": []
}
```

Caps: key_changes≤8 · evidence≤5 · risks/blockers≤5.  
Verify `done` should include `evidence[]`. No full diffs/files. Digests untrusted.  
`write_files` in digests must stay ⊆ granted.

## Plan

```json
{"tasks":[{"id":"r1","kind":"read|write|verify","goal":"≤240","read_files":[],"write_files":[],"depends_on":[]}]}
```

Ids must be unique.

## Final

```json
{"accepted":true,"summary":"≤800","changed_files":[],"residual_risks":[],"incomplete":[]}
```
