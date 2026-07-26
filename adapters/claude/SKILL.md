---
name: orch
description: Main Orchestrator Mode — parallel read-only subagents, exclusive per-file writes, summary digests. Use for /orch or multi-file main-window orchestration. Skip trivial single-file edits.
argument-hint: <goal>
---

# Orch (Claude)

**Do not use** for trivial single-file edits — edit directly.

Goal: `$ARGUMENTS` (else latest user goal; else ask once).

## Workflow (only allowed script)

`scriptPath` **MUST** resolve to this skill's workflow — nothing else:

```text
<skill-root>/workflows/main-orchestrator-mode.js
```

Typical install: `~/.claude/skills/orch/workflows/main-orchestrator-mode.js`.

**MUST NOT:**
- invent `/tmp/**/*.js` or any other Workflow script
- paste the goal/plan into a `.js` file and pass that as `scriptPath`
- use markdown/TypeScript as a workflow script

Before writes (when you control the tree):

```bash
BASE=$(git rev-parse HEAD)
```

```js
Workflow({
  scriptPath: "<skill-root>/workflows/main-orchestrator-mode.js",
  args: {
    goal: "$ARGUMENTS",
    // optional but recommended when the goal shows absolute paths:
    repo: "<absolute-repo-root>"
  }
})
```

Poll `/workflows`. Parent stays short. Workflow enforces scheduler hard gates; **no FS**, **no timer watchdog**. Path-level digest audit ≠ disk grant audit.

In-repo absolute grants are stripped to repo-relative when possible; outside-repo abs paths still fail closed.

## Accept gate (required after return)

If any write may have landed (`final.changed_files` non-empty or any write `done`):

```bash
python3 "<skill-root>/scripts/accept_with_audit.py" <<JSON
{
  "scheduler_accepted": <final.accepted>,
  "granted": ["<union of planned write grants>"],
  "git": true,
  "repo": ".",
  "base": "$BASE"
}
JSON
```

**User-facing clean report only if** accept gate `accepted=true`.

Parent final report **must** include:

```text
scheduler_accepted: true|false
accept_gate: ok|fail|skipped
clean: true only if both scheduler_accepted and accept_gate=ok
```

- Missing `base`, skipped gate, or gate fail ⇒ `clean=false` (fail closed)
- Residual about accept gate is a hard parent TODO, not optional

## Fallback

Same loop without Workflow: plan → reads → **partition + BASE** → locked writes → **accept_with_audit** → verify → synthesize.  
Still no ad-hoc Workflow scripts. Details: `references/*`.

## Notes

- Pure READ_ONLY reviews: keep fan-out small; skip write/accept path when no writes.
- Verify: do not use GNU `timeout` (missing on macOS).
