---
name: orch
description: Main Orchestrator Mode — parallel read-only subagents, exclusive per-file writes, summary digests. Use for /orch or multi-file main-window orchestration.
argument-hint: <goal>
---

# Orch (Claude)

Goal: `$ARGUMENTS` (else latest user goal; else ask once).

## Workflow (preferred)

```js
Workflow({
  scriptPath: "<skill-root>/workflows/main-orchestrator-mode.js",
  args: { goal: "$ARGUMENTS" }
})
```

`<skill-root>` = this skill dir. Poll `/workflows`. Parent stays short. Report final fields only.

Workflow enforces the hard gates in code. It has **no FS** (no `.orch/`) and **no timer watchdog**.

**After it returns**, run grant audit (git needs pre-write `base`):

```bash
python3 "<skill-root>/scripts/audit_write_grant.py" <<JSON
{"granted":["src/a.ts"],"git":true,"repo":".","base":"$BASE"}
JSON
```

## Fallback

Same loop without Workflow: plan → ready reads (≤2) → locked writes → verify → synthesize.  
Details: `references/*`. Gates match contract; digests untrusted.
