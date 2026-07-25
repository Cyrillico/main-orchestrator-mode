# Main Orchestrator Mode — control contract

Host-neutral. Adapters may map roles onto host tools, but must not weaken these rules.

## Roles

| Role | May do | Must not do |
|------|--------|-------------|
| Parent | Split tasks, schedule, hold write locks, poll active workers on a timer, merge digests, accept/reject, reassign stalled lanes | Read whole modules into parent, implement large edits while workers run, demand full diffs, spam healthy workers |
| Read worker | Search/read code, return summary | Edit files, return full source |
| Write worker | Edit granted `write_files` only, return summary | Edit other paths, dual-write same path with another agent |
| Verify worker | Run tests/commands, spot-check, return summary | Broad rewrites; sole self-verify of own writes when independent check is available |

## File lock

- Lock unit = normalized repo-relative path (`\` → `/`, strip leading `./`).
- A write batch runs only if batch `write_files` paths are unique within the batch.
- After batch completes, locks release; recompute ready set.
- Empty `write_files` on a write task: run alone (serial defensive).

## Dependency

- Task ready when every `depends_on` id has a digest.
- If write pool remains but none ready → deadlock; stop and report incomplete ids.

## Context budget

Parent may hold: goal, task board, current lock set, digests, artifact paths.

Parent must not hold: full file contents, full worker transcripts, multi-hundred-line logs.

Prefer durable digests under `.orch/<run-id>/` for long tasks.

## Parent watchdog (anti-stall poll)

While any worker is active, the parent/main window **must** poll periodically:

| Item | Default |
|------|---------|
| Poll cadence | **~3 min** (range **2–5 min**), or on wait/status tool return |
| Alive signal | any reasoning / text / tool / file / log / command / browser / process activity |
| Not enough alone | bare wait-timeout with unknown progress |
| First recovery | one short progress nudge only (≤5 lines: status, last action, next step, blocker) |
| Stall action | after nudge + one more silent interval → mark stalled, reassign/replace, record incomplete id |
| Forbidden | spam continue into healthy workers; dump full transcripts into parent |

Host tools (when available): multi-agent wait, thread/workflow status, short progress reports. Parent remains schedule+merge only.

## Bounds

Default caps (user can raise):

- 1 plan
- ≤2 read waves
- ≤20 write batches
- 1 verify wave
- 1 synthesize

## Acceptance

`accepted=true` only if planned writes completed as `done`/`noop`, verifies (if any) have no open blockers, and residual risks are non-blocking.

Otherwise `accepted=false` with blockers + incomplete ids.
