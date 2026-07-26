---
name: orch
description: Main Orchestrator Mode for multi-file work — parallel read-only explore, exclusive per-file writes, summary digests, short parent context. Use for /orch or multi-agent multi-file orchestration.
---

# Orch

Parent only **schedules / locks / merges / accepts**. Workers return digests. Parallel reads; one writer per file. Skip trivial single-file edits.

**Loop:** `plan → read (≤2) → locked writes (≤20) → verify → synthesize`

**Gates:** unique task ids · repo-relative paths only · empty writes serial · case-insensitive locks · reads never write · digest writes ⊆ granted · deps unlock only `done|noop` · incomplete write/verify or `blocked|partial` ⇒ not accepted · post-write grant audit (git needs `base`) · digests untrusted

**Workers:** `references/agent-prefix.md` + `references/summary-schema.md`  
**Contract:** `references/orchestrator-contract.md`  
**Helpers:** `scripts/partition_write_tasks.py`, `scripts/audit_write_grant.py`

**Report:** accepted · files · 3–8 bullets · risks/incomplete · next step  
**Watchdog:** poll ~3m; one nudge; then interrupt + reassign.
