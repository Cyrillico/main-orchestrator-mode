---
name: orch
description: Main Orchestrator Mode for multi-file work — parallel read-only explore, exclusive per-file writes, summary digests, short parent context. Use for /orch or multi-agent multi-file orchestration. Skip trivial single-file edits.
---

# Orch (Codex)

**Do not use** for trivial single-file edits — edit directly.

Parent schedules/locks/merges/accepts. Digests only. Parallel reads; exclusive writes. Prefer digests in `.orch/<run-id>/`. Use Codex multi-agent tools.

## Required control loop

`plan → read (≤2) → write batches → verify → synthesize → accept gate`

**Before every write batch (non-optional):**

```bash
BASE=$(git rev-parse HEAD)
python3 "<skill-root>/scripts/partition_write_tasks.py" <<'JSON'
[{"id":"w1","write_files":["src/a.ts"]},{"id":"w2","write_files":["src/b.ts"]}]
JSON
```

Spawn only one partition batch at a time (exclusive locks). Empty `write_files` ⇒ serial alone.

**After every write batch and before final clean report (non-optional):**

```bash
python3 "<skill-root>/scripts/accept_with_audit.py" <<JSON
{
  "scheduler_accepted": true,
  "granted": ["src/a.ts","src/b.ts"],
  "git": true,
  "repo": ".",
  "base": "$BASE"
}
JSON
```

- Skip partition / skip audit / missing `base` ⇒ `accepted=false` (fail closed)
- Scheduler-looking success without disk audit is **not** clean
- Out-of-grant ⇒ stop batch, do not unlock dependents as success

**Gates:** unique ids · path reject · empty-write serial · casefold locks · reads read-only · digest ⊆ grant · deps `done|noop` only · incomplete/blocked/partial fail accept

**Load when needed:** `references/agent-prefix.md`, `references/summary-schema.md`, `references/orchestrator-contract.md`  
**Helpers:** `scripts/partition_write_tasks.py`, `scripts/audit_write_grant.py`, `scripts/accept_with_audit.py`

**Out:** accepted · files · short bullets · risks · next step. Poll ~3m; interrupt then reassign.
