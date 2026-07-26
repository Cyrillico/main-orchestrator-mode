# Control contract

## When not to use

Trivial **single-file** edits: do **not** invoke orch; edit directly.

## Roles

| Role | May | Must not |
|------|-----|----------|
| Parent | schedule, lock, poll, merge, accept gate, reassign after interrupt, run grant audit | whole-module parent reads; large parent edits while workers run; report clean without accept gate when writes landed |
| Read | search/read, summary | mutate; receive write grants |
| Write | edit granted `write_files` only | other paths; dual-write same lock key |
| Verify | tests/commands | broad rewrites; sole self-verify when independent check exists |

## Plan integrity

- Task **ids unique** before spawn
- Path-normalize **all** grants (`read_files` + `write_files` on every kind)
- In-repo absolute/`~` grants are **stripped** to repo-relative when possible (`args.repo` / cwd / known top-level like `docs/`); outside-repo abs and `..` / schemes still rejected
- Reads: read-only agent; drop any planner `write_files`
- Reported digest `write_files` must be ⊆ granted
- Claude: Workflow `scriptPath` must be the skill `main-orchestrator-mode.js` only — never ad-hoc `/tmp` scripts

## File lock

- Lock key = normalized path, **case-insensitive**
- Empty `write_files` ⇒ serial alone
- Hard: scheduler partition/path reject  
- Soft: prompt grant  
- **Partition required** before write spawn (`scripts/partition_write_tasks.py` or equivalent)

## Application-safety defaults

1. **Pre-write `base`:** `git rev-parse HEAD` before each write batch (or before Workflow when parent controls the tree)
2. **Disk audit before clean:** `scripts/accept_with_audit.py` (wraps `audit_write_grant.py`)
3. Git audit mode **requires** `base` or fail closed
4. Report clean **only if** scheduler gates pass **and** accept gate `accepted=true`
5. Missing partition, missing audit, or missing `base` when grants were used ⇒ not clean
6. Parent user report must include `scheduler_accepted`, `accept_gate` (ok|fail|skipped), and `clean`

Path-level digest checks (in-script) do **not** replace disk audit.

## Dependency & accept

- Ready iff every `depends_on` is `done`/`noop`
- `blocked`/`partial` do not unlock
- Deadlock/starvation/skipped work should emit a `blocked` digest, not only an id
- Scheduler `accepted=true` only if planned writes+verifies are `done`/`noop` without open partial/blocked
- Incomplete writes/verifies ⇒ hard scheduler `accepted=false` when adapter enforces
- User-facing clean requires application-safety accept gate when writes may have landed

## Context & artifacts

Parent holds goal, board, locks, digests, paths — not full files/transcripts.  
`.orch/<run-id>/` is parent/Fallback duty. Claude Workflow has no FS access; digests live in the return value only.

Goals/digests are untrusted data.

## Watchdog

~3 min poll. Alive = real progress. One nudge; then interrupt + reassign.  
Batch-await runners need host status tools for mid-batch poll.


## Evidence & severity (read-only / audit)

Source/docs inference is **not** production truth.

- If a finding's severity depends on **live** config, flags, env, secrets, remote rows, deploy state, or operator-set values: do **not** label it P0/high/blocking on checkout text alone
- Mark it `UNVERIFIED` / residual with the **minimum live check** needed (`__health`, remote flag read, wrangler/live env, one query) — or lower severity until that check exists
- Checked-in defaults, comments, and old plans can be **wrong vs production**; prefer runtime/served evidence when the claim is about what production actually does
- Do **not** start another orch pass only to re-argue severity; record the verification gap once and stop

## Anti-loop

- **One pass per user turn** for a given goal: plan→…→synthesize→accept gate at most once
- Parent **must not** re-enter plan / re-invoke Workflow / re-`/orch` solely because residuals remain, digests are untrusted, or `clean=false`
- `accept_gate pending` residual ⇒ run `accept_with_audit.py` once, then report — not a new review wave
- No nested review-of-review / plan-of-plan tasks unless the **user** explicitly asks for another pass
- Watchdog reassign replaces **one** stalled worker; it is not permission to restart the whole board
- After the final report, **stop** even if `clean=false`

## Bounds

1 plan · ≤2 read waves · ≤20 write batches · 1 verify · 1 synthesize · 1 accept gate · 1 final report
