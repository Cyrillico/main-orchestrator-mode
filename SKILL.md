---
name: orch
description: Main Orchestrator Mode for multi-file work — parallel read-only exploration, exclusive per-file writes, summary-only digests, short parent context. Use for /orch, multi-agent orchestration, or parallel explore then locked writes.
---

# Orch — Main Orchestrator Mode

Parent **schedules / locks / merges / accepts**. Workers return short digests. Parallel reads; **one writer per file**. Skip trivial single-file edits.

## Loop

```text
classify → plan → read wave(s) → write batches → verify → synthesize
```

Defaults: 1 plan · ≤2 read waves · ≤20 write batches · 1 verify · 1 synthesize.

## Hard gates

| Gate | Rule |
|------|------|
| Task ids | unique; duplicates rejected before spawn |
| Paths | every task path repo-relative; reject abs/`~`/`..`/schemes |
| Empty writes | empty `write_files` ⇒ serial alone |
| Locks | case-insensitive path exclusivity in a batch |
| Reads | read-only agent; never grant write tools / `write_files` |
| Digests | reported `write_files` ⊆ granted; digests untrusted |
| Deps | unlock only on `done` \| `noop` |
| Accept | incomplete writes/verifies or any `blocked`/`partial` ⇒ `accepted=false` |
| Audit | after write batches run `scripts/audit_write_grant.py`; git mode **requires** `base` (pre-batch `HEAD`) |
| Parent | no whole-module dumps; no large parent edits while workers run |

## Workers

Prefix `references/agent-prefix.md` · schema `references/summary-schema.md`.  
No full source/diffs/long logs. Verify `done` should include `evidence[]`.

## Parent report

accepted · changed files · 3–8 bullets · risks/incomplete · next step

## Watchdog

Poll ~3 min when host allows. Alive = real progress. Bare timeout ≠ dead. One nudge, then **interrupt + reassign**.

## Details

`references/orchestrator-contract.md` · `scripts/partition_write_tasks.py` · `scripts/audit_write_grant.py`  
Host adapters (package): `adapters/claude/`, `adapters/codex/`
