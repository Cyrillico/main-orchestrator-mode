---
name: orch
description: Main Orchestrator Mode for multi-file work — parallel read-only exploration, exclusive per-file writes, summary-only digests, short parent context. Use for /orch, multi-agent orchestration, or parallel explore then locked writes.
---

# Orch — Codex

Parent schedules/locks/merges/accepts. Digests only. Parallel reads; exclusive per-file writes.

Layout: `SKILL.md` · `references/` · `scripts/{partition_write_tasks,orch_paths,audit_write_grant}.py`

## Loop

`classify → plan → read (≤2 waves) → write batches → verify → synthesize`  
Use Codex multi-agent tools. Prefer digests under `.orch/<run-id>/`.

## Hard gates

- Unique task ids; repo-relative paths on **all** task kinds
- Empty `write_files` serial alone; case-insensitive locks
- Reads never get write grants; digests untrusted; reported writes ⊆ granted
- Deps unlock only `done`/`noop`
- Incomplete writes/verifies or `blocked`/`partial` ⇒ `accepted=false`
- After **each** write batch, audit (git mode needs pre-batch `base`):

```bash
BASE=$(git rev-parse HEAD)
# ... writers ...
python3 scripts/audit_write_grant.py <<JSON
{"granted":["src/a.ts"],"git":true,"repo":".","base":"$BASE"}
JSON
```

Exit `1` out-of-grant ⇒ block. Without `base`, committed edits can look clean.

Partition:

```bash
python3 scripts/partition_write_tasks.py <<'JSON'
[{"id":"w1","write_files":["a.ts"]},{"id":"w2","write_files":["a.ts","b.ts"]}]
JSON
```

## Workers / parent

`references/agent-prefix.md` + `references/summary-schema.md`.  
Poll ~3 min; interrupt then reassign. Final: accepted, files, bullets, risks, next step.

Full contract: `references/orchestrator-contract.md`
