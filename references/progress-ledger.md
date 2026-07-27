# Optional progress ledger (anti re-dispatch)

Prefer `.orch/<run-id>/progress.md` (parent/Fallback only; Claude Workflow has no FS).

```text
goal_hash: <short hash of user goal>
fix_rounds: <theme>=<n>/3
completed_task_ids: id1,id2
parked: <finding> — ruling: <why>
status: running|stopped|blocked
```

Rules:
- If `completed_task_ids` lists an id, do not re-dispatch it
- If any theme `fix_rounds` is 3, no more fix/re-review for that theme
- After final report, set `status: stopped` even when `clean=false`
