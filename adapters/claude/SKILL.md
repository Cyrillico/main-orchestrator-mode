---
name: orch
description: Main Orchestrator Mode — parallel read-only subagents, exclusive per-file write locks, summary-only digests. Use for /orch, multi-file implementation, or main-window orchestration that must keep parent context short.
argument-hint: <goal>
disable-model-invocation: false
---

# Orch — Claude Code

Parent schedules/locks/merges/accepts. Digests only. Parallel reads; one writer per file.

Layout: `SKILL.md` · `references/` · `workflows/main-orchestrator-mode.js` · `scripts/`

## Goal

```text
$ARGUMENTS
```

Empty → latest user goal; still empty → ask once.

## Preferred: Workflow

```js
Workflow({
  scriptPath: "<skill-root>/workflows/main-orchestrator-mode.js",
  args: { goal: "$ARGUMENTS" }
})
```

`<skill-root>` = directory of this `SKILL.md` (usually `~/.claude/skills/orch`).

While running: poll `/workflows`; do not load whole modules.  
Report: `accepted`, `summary`, `changed_files`, `residual_risks`, `incomplete`.

### What the workflow enforces

Unique ids · path reject on all grants · empty-serial · casefold locks · read-only read agents · digest `write_files` ⊆ granted · success-only deps · incomplete write/verify hard-fail · blocked digests for deadlock/starvation.

### What it does **not** do

- No timer watchdog (parent polls)
- No filesystem / no `.orch/` writes (digests only in return value)
- No disk grant audit — **parent must run** after return (or after each fallback batch):

```bash
BASE=$(git rev-parse HEAD)   # record before writes when possible
python3 "<skill-root>/scripts/audit_write_grant.py" <<JSON
{"granted":["src/a.ts"],"git":true,"repo":".","base":"$BASE"}
JSON
```

`base` required in git mode. Exit `1` ⇒ treat as not accepted.

## Fallback (no Workflow)

Plan board → ready reads (≤2 waves, no ready-empty→all) → locked writes → verify with `evidence[]` → synthesize. Same hard gates. Parent may write `.orch/<run-id>/` digests.

## Refs

`references/{summary-schema,agent-prefix,orchestrator-contract}.md` · `workflows/main-orchestrator-mode.js`
