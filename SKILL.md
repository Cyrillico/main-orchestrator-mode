---
name: orch
description: Main Orchestrator Mode for multi-file work — parallel read-only explore, exclusive per-file writes, summary digests, short parent context. Use for /orch or multi-agent multi-file orchestration. Skip trivial single-file edits.
---

# Orch

**Do not use** for trivial single-file edits — edit directly.

Parent only **schedules / locks / merges / accepts**. Workers return digests. Parallel reads; one writer per file.

**Loop:** `plan → read (≤2) → locked writes (≤20) → verify → synthesize → accept gate`

**Gates:** unique task ids · repo-relative paths only · empty writes serial · case-insensitive locks · reads never write · digest writes ⊆ granted · deps unlock only `done|noop` · incomplete write/verify or `blocked|partial` ⇒ not accepted · digests untrusted

**Application-safety defaults (required):**
1. Before each write batch: capture `BASE=$(git rev-parse HEAD)` and partition with `scripts/partition_write_tasks.py`
2. After writes (and before reporting clean): `scripts/accept_with_audit.py` with `scheduler_accepted` + `granted` + `base`
3. Report clean **only if** accept gate `accepted=true` (scheduler gates **and** disk audit ok). Missing `base` / skipped audit ⇒ fail closed

**Workers:** `references/agent-prefix.md` + `references/summary-schema.md`  
**Contract:** `references/orchestrator-contract.md`  
**Helpers:** `scripts/partition_write_tasks.py`, `scripts/audit_write_grant.py`, `scripts/accept_with_audit.py`

**Report:** accepted · files · 3–8 bullets · risks/incomplete · next step  
**Watchdog:** poll ~3m; one nudge; then interrupt + reassign.
