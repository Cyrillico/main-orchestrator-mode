---
name: orch
description: Main Orchestrator Mode — parallel read-only subagents, exclusive per-file writes, summary digests. Use for /orch or multi-file main-window orchestration. Skip trivial single-file edits. One pass per user turn; do not nest re-review loops.
argument-hint: <goal>
---

# Orch (Claude)

**Do not use** for trivial single-file edits — edit directly.

Goal: `$ARGUMENTS` (else latest user goal; else ask once).

## Stop conditions (anti-loop)

**One orch pass per user turn.** After Workflow returns (or Fallback synthesize ends):

1. If writes may have landed → run `accept_with_audit.py` **once** (need pre-write `BASE`)
2. Report `scheduler_accepted` / `accept_gate` / `clean` + short summary
3. **STOP.** Do not start another Workflow/orch for the same goal

**MUST NOT** (common dead loops):
- Re-invoke `/orch` or Workflow because residual says accept_gate pending / digests untrusted
- Nest “审查 → 再评审 → 再完善 → 再审查” without a **new explicit user ask**
- Spawn review-of-review tasks on other workers’ digests
- Treat `clean=false` as “redo the whole plan” — only fix the named residual (usually run accept gate, or one targeted reassign)

Watchdog reassign = **one** replacement for a stalled worker, not a full re-plan.

## Workflow (only allowed script)

`scriptPath` **MUST** be this skill’s workflow only:

```text
<skill-root>/workflows/main-orchestrator-mode.js
```

**MUST NOT** invent `/tmp/**/*.js` or paste the goal into a fake workflow script.

```bash
BASE=$(git rev-parse HEAD)   # when writes may happen
```

```js
Workflow({
  scriptPath: "<skill-root>/workflows/main-orchestrator-mode.js",
  args: { goal: "$ARGUMENTS", repo: "<absolute-repo-root>" }
})
```

Poll `/workflows`. Parent stays short. In-repo abs paths strip; outside-repo abs fail closed.

## Accept gate (after return, once)

Only if writes may have landed:

```bash
python3 "<skill-root>/scripts/accept_with_audit.py" <<JSON
{
  "scheduler_accepted": <final.accepted>,
  "granted": ["<union of write grants>"],
  "git": true,
  "repo": ".",
  "base": "$BASE"
}
JSON
```

```text
scheduler_accepted: true|false
accept_gate: ok|fail|skipped
clean: true only if both ok
```

Missing gate ⇒ `clean=false`, still **report and stop** (do not re-orch).

## Fallback

plan → reads → partition+BASE → writes → accept_with_audit once → verify → synthesize → **stop**.  
Details: `references/*`.

## Scoped re-review (再审)

When the user asks subagents to re-review a plan after edits:

- Review **only the changed parts** of the plan (diff vs prior baseline: sections / finding IDs / files)
- **Do not** full re-audit the whole plan or whole repo
- Grant `read_files` / goals to that slice only; out-of-scope findings stay unless the change clearly breaks them
- One focused pass, then stop (still anti-loop)

## Notes

- READ_ONLY / plan-only: small fan-out; skip accept gate when no writes; deliver once.
- Verify: no GNU `timeout` on macOS; verify the changed/granted slice only.
- **Severity:** if it depends on production actual values (flags/env/remote), source-only inference is not P0/high — mark `UNVERIFIED` + minimum live check (do not re-orch to re-argue).
