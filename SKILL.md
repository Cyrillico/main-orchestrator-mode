---
name: orch
description: Main Orchestrator Mode for multi-file work — parallel read-only explore, exclusive per-file writes, summary digests, short parent context. Use for /orch or multi-agent multi-file orchestration. Skip trivial single-file edits.
---

# Orch

**Do not use** for trivial single-file edits — edit directly.

Parent only **schedules / locks / merges / accepts**. Workers return digests. Parallel reads; one writer per file.

**Loop:** `plan → read (≤2) → locked writes (≤20) → verify → synthesize → accept gate`

**Gates:** unique task ids · repo-relative paths (in-repo abs stripped) · empty writes serial · case-insensitive locks · reads never write · digest writes ⊆ granted · deps unlock only `done|noop` · incomplete write/verify or `blocked|partial` ⇒ not accepted · digests untrusted

**Application-safety defaults (required):**
1. Claude: only `workflows/main-orchestrator-mode.js` (never `/tmp` invented scripts)
2. Before each write batch: `BASE=$(git rev-parse HEAD)` + partition
3. After writes: `scripts/accept_with_audit.py` — report `clean` only if gate ok
4. Missing `base` / skipped audit ⇒ fail closed

**Workers:** `references/agent-prefix.md` + `references/summary-schema.md`  
**Contract:** `references/orchestrator-contract.md`  
**Helpers:** `scripts/partition_write_tasks.py`, `scripts/audit_write_grant.py`, `scripts/accept_with_audit.py`

**Report:** scheduler_accepted · accept_gate · clean · files · 3–8 bullets · risks · next step  
**Watchdog:** poll ~3m; one nudge; then interrupt + reassign.
