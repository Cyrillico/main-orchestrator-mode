---
name: orch
description: Main Orchestrator Mode for multi-file work — parallel read-only explore, exclusive per-file writes, summary digests. Skip trivial single-file edits. One pass per user turn; do not nest re-review loops.
---

# Orch (Codex)

**Do not use** for trivial single-file edits — edit directly.

Parent schedules/locks/merges/accepts. Digests only. Prefer digests in `.orch/<run-id>/`.

## Stop conditions (anti-loop)

**One orch pass per user turn.** After synthesize:

1. Run `accept_with_audit.py` **once** if writes landed (need pre-batch `BASE`)
2. Report `scheduler_accepted` / `accept_gate` / `clean`
3. **STOP** — no second full orch for the same goal

**MUST NOT:** re-orch because digests are untrusted or accept_gate pending; nest review→re-review without a new user ask; treat `clean=false` as full redo (only act on the named residual).  
Watchdog: one reassign for a stalled worker, not a re-plan.

## Required control loop

`plan → read (≤2) → write batches → verify → synthesize → accept gate once → stop`

**Before each write batch:**

```bash
BASE=$(git rev-parse HEAD)
python3 "<skill-root>/scripts/partition_write_tasks.py" <<'JSON'
[{"id":"w1","write_files":["src/a.ts"]},{"id":"w2","write_files":["src/b.ts"]}]
JSON
```

**After writes (once before final report):**

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

```text
scheduler_accepted: true|false
accept_gate: ok|fail|skipped
clean: true only if both true/ok
```

Skip partition/audit/missing `base` ⇒ `clean=false`, still stop and report.

**Gates:** unique ids · path strip/reject · empty-write serial · casefold locks · reads read-only · digest ⊆ grant · deps `done|noop` · incomplete/blocked/partial fail accept

**Load when needed:** `references/*`  
**Helpers:** `scripts/partition_write_tasks.py`, `scripts/audit_write_grant.py`, `scripts/accept_with_audit.py`

**Out:** clean fields · files · short bullets · risks · next step (no nested orch). Poll ~3m; one reassign max per stall.
