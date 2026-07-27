---
name: orch
description: Use when multi-file work needs parallel read-only explore, exclusive per-file writes, and short digests via multi-agent tools. Skip trivial single-file edits.
---

# Orch (Codex)

Parent schedules only. Digests in `.orch/<run-id>/` preferred. Skip single-file edits.

## One pass → STOP

`plan → read(≤2) → write batches → verify → synthesize → accept gate once → STOP`

Before each write batch: `BASE=$(git rev-parse HEAD)` + `scripts/partition_write_tasks.py`.  
After writes: `scripts/accept_with_audit.py` **once** (needs `base`).

```text
scheduler_accepted / accept_gate / clean
```

## Anti-loop (must)

| Rule | Limit |
|------|--------|
| Re-orch same goal for residuals | **forbidden** |
| Fix+scoped re-review per theme | **≤3** then park/BLOCKED |
| After full review | **≤1** fix wave + **≤1** re-review |
| Minor / UNVERIFIED / accept_gate pending | residual only |
| Watchdog reassign | **1** per stall |
| Re-review scope | `references/re-review-prompt.md` |

**Helpers:** `partition_write_tasks.py`, `audit_write_grant.py`, `accept_with_audit.py`  
**Contract:** `references/orchestrator-contract.md`
