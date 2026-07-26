---
name: orch
description: Main Orchestrator Mode for multi-file work — parallel read-only explore, exclusive per-file writes, summary digests, short parent context. Use for /orch or multi-agent multi-file orchestration.
---

# Orch (Codex)

Parent schedules/locks/merges/accepts. Digests only. Parallel reads; exclusive writes.

**Loop:** `plan → read (≤2) → write batches → verify → synthesize`  
Prefer digests in `.orch/<run-id>/`. Use Codex multi-agent tools.

**Gates:** unique ids · path reject · empty-write serial · casefold locks · reads read-only · digest ⊆ grant · deps `done|noop` only · incomplete/blocked/partial fail accept · after each write batch audit with `base`:

```bash
BASE=$(git rev-parse HEAD)
python3 scripts/audit_write_grant.py <<JSON
{"granted":["src/a.ts"],"git":true,"repo":".","base":"$BASE"}
JSON
```

**Load when needed:** `references/agent-prefix.md`, `references/summary-schema.md`, `references/orchestrator-contract.md`  
**Helpers:** `scripts/partition_write_tasks.py`

**Out:** accepted · files · short bullets · risks · next step. Poll ~3m; interrupt then reassign.
