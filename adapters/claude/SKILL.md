---
name: orch
description: Main Orchestrator Mode — parallel read-only subagents, exclusive per-file writes, summary digests. Use for /orch or multi-file main-window orchestration. Skip trivial single-file edits.
argument-hint: <goal>
---

# Orch (Claude)

**Do not use** for trivial single-file edits — edit directly.

Goal: `$ARGUMENTS` (else latest user goal; else ask once).

## Workflow (preferred)

Before writes (parent duty if Fallback, or record before invoking when you control the tree):

```bash
BASE=$(git rev-parse HEAD)
```

```js
Workflow({
  scriptPath: "<skill-root>/workflows/main-orchestrator-mode.js",
  args: { goal: "$ARGUMENTS" }
})
```

`<skill-root>` = this skill dir. Poll `/workflows`. Parent stays short.

Workflow enforces scheduler hard gates in code. It has **no FS** (no `.orch/`) and **no timer watchdog**. Path-level digest audit ≠ disk grant audit.

## Accept gate (required after return)

Do **not** treat the run as clean until this passes when any write may have landed:

```bash
python3 "<skill-root>/scripts/accept_with_audit.py" <<JSON
{
  "scheduler_accepted": true,
  "granted": ["src/a.ts"],
  "git": true,
  "repo": ".",
  "base": "$BASE"
}
JSON
```

- `scheduler_accepted` = Workflow `final.accepted`
- `granted` = union of planned write grants (or batch grants)
- Missing `base`, skipped gate, or `accepted=false` ⇒ report **not clean**
- Workflow residual about grant audit is a hard parent TODO, not optional

## Fallback

Same loop without Workflow: plan → ready reads (≤2) → **partition + BASE** → locked writes → audit/accept gate → verify → synthesize.  
Details: `references/*`. Gates match contract; digests untrusted.
