---
name: orch
description: Use when multi-file work needs parallel read-only subagents, exclusive per-file writes, and digest returns via /orch. Skip trivial single-file edits.
argument-hint: <goal>
---

# Orch (Claude)

Goal: `$ARGUMENTS` (else latest user goal; else ask once). Skip single-file edits.

## One pass → STOP

```bash
BASE=$(git rev-parse HEAD)   # if writes may land
```

```js
Workflow({
  scriptPath: "<skill-root>/workflows/main-orchestrator-mode.js",  // ONLY this path
  args: { goal: "$ARGUMENTS", repo: "<abs-repo-root>" }
})
```

Then: if writes landed → `scripts/accept_with_audit.py` **once** → report → **STOP**.

```text
scheduler_accepted: true|false
accept_gate: ok|fail|skipped
clean: true only if both ok
```

## Anti-loop (must)

| Rule | Limit |
|------|--------|
| Re-orch same goal for residuals | **forbidden** |
| Fix+scoped re-review per theme | **≤3** then park/BLOCKED |
| After full review | **≤1** fix wave + **≤1** re-review |
| Minor / UNVERIFIED / accept_gate pending | residual only — **no new review loop** |
| Watchdog reassign | **1** per stalled worker |
| Re-review scope | changed slice only (`references/re-review-prompt.md`) |

**MUST NOT:** invent `/tmp/**/*.js` Workflow scripts; nest 审查→再审→再完善 without a **new user ask**.

Fallback (no Workflow): same pass bounds + partition + BASE + accept once → stop.  
Contract: `references/orchestrator-contract.md`.
