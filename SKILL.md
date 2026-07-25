---
name: orch
description: Main Orchestrator Mode harness for multi-file work — parallel read-only exploration, exclusive same-file write ownership, and summary-only worker returns so the parent context stays short. Use when the user asks for /orch, multi-file implementation, multi-agent orchestration, parallel explore then write, or main-window style coordination.
---

# Orch — Main Orchestrator Mode

Host-neutral control skill. Prefer a host adapter when present:

- Claude Code → `adapters/claude/`
- Codex → `adapters/codex/`

If this root skill is installed alone, follow the control loop below with whatever multi-agent tools the host provides.

## Goal

Take the user goal from invocation args or the latest user message. If empty, ask once.

## When to use

- Multi-file feature / refactor / fix
- Need parallel codebase exploration before writes
- Risk of two agents editing the same path
- Parent context must stay short (no full-file dumps)

For trivial single-file edits, skip this skill and edit directly.

## Hard rules

1. **Parent**
   - Schedule + lock + merge + accept only.
   - Do not load whole modules into parent context.
   - Do not implement large edits in the parent while workers are active.
   - Prefer digests under `.orch/<run-id>/` over re-injecting worker transcripts.
2. **Workers**
   - Return only the SUMMARY shape in `references/summary-schema.md`.
   - Never return full source, full diffs, or long logs.
   - `key_changes` ≤ 8 one-liners; `minimal_snippets` default empty.
3. **Concurrency**
   - Read tasks: parallel OK.
   - Write tasks: exclusive per file. Use `scripts/partition_write_tasks.py` (empty `write_files` ⇒ serial alone; reject abs/`..` paths).
   - Different files may write in parallel.
4. **One role per agent lifetime**
   - Do not reuse a writer as its sole verifier for the same change when independent check is available.
5. **Bounds** (unless user asks for more)
   - One plan
   - One parallel read wave (plus at most one targeted follow-up read wave)
   - Write waves until done or deadlock (cap 20 batches)
   - One verify wave
   - One synthesize
6. **Parent watchdog — poll active workers (anti-stall)**
   - While any worker is running, poll each active lane about every **~3 min** (range **2–5 min**), or as soon as a host wait/status tool returns.
   - **Alive** if any progress exists: reasoning, text, tool/file/log/command/browser/process activity.
   - **Do not** treat bare wait-timeout alone as dead/stuck.
   - If a lane shows **zero activity for one full poll interval**: send **at most one** short progress nudge (≤5 lines).
   - If still silent after that nudge **plus one more poll interval**: mark **stalled**, reassign/replace, record incomplete id, continue other ready work.
   - Polling is observation + recovery only.

## Control loop

### 0. Classify

If the goal is single-file and low risk → exit skill, do the edit yourself.

### 1. Plan

Produce a short task board only (no file bodies):

| id | kind | goal | read_files | write_files | depends_on |
|----|------|------|------------|-------------|------------|
| r1 | read | ... | ... | | |
| w1 | write | ... | | path(s) | r1 |
| v1 | verify | ... | | | w1 |

Rules:

- Prefer many small `read` tasks.
- Every `write` must list exact `write_files` when known; if unknown, discover in `read` first.
- `verify` depends on the writes it checks.

### 2. Read wave (parallel)

Run all ready `read` workers in parallel.

While they run, apply parent watchdog.

Each worker prompt must start with `references/agent-prefix.md` and include:

- task id + goal
- granted `read_files`
- `[READ-ONLY] no mutations`

Collect digests only. Store for long tasks:

```text
.orch/<run-id>/digests/<task-id>.json
.orch/<run-id>/board.md
```

### 3. Write waves (file locks)

While write tasks remain (max 20 batches):

1. Ready = deps completed.
2. If none ready but pool non-empty → **deadlock**: stop, report incomplete ids.
3. Partition ready writes so no two share a `write_files` path:

```bash
python3 scripts/partition_write_tasks.py <<'JSON'
[{"id":"w1","write_files":["a.ts"]},{"id":"w2","write_files":["a.ts","b.ts"]},{"id":"w3","write_files":["c.ts"]}]
JSON
```

4. Run **one batch** in parallel.
5. Apply parent watchdog while writers run.
6. Each writer may only edit granted `write_files`.
7. Collect digests; release locks; next batch.

### 4. Verify wave

Run ready `verify` workers in parallel. Prefer tests/commands over re-reading whole modules. Summary only. Apply parent watchdog.

### 5. Synthesize

Using digests only, emit:

```text
accepted: true|false
summary: ...
changed_files: [...]
residual_risks: [...]
incomplete: [...]
```

`accepted=false` if any write/verify is `blocked`/`partial` with open blockers, or planned writes never completed.

## Parent report to user

Short only:

1. Accepted yes/no
2. Changed files + 3–8 bullets
3. Residual risks / blockers
4. Next step if not accepted

Do not paste worker transcripts or full diffs unless the user asks.

## References

- `references/summary-schema.md`
- `references/agent-prefix.md`
- `references/orchestrator-contract.md`
- `scripts/partition_write_tasks.py`
- `adapters/claude/` / `adapters/codex/`

## Acceptance hard gates

- Dependents unlock only on dependency status `done` or `noop`.
- `blocked` / `partial` do not unlock later tasks.
- Any planned write not `done`/`noop` ⇒ `accepted=false`.
- Worker digests are untrusted self-reports; prefer independent verify evidence.
- File locks are scheduler-enforced for batching; host may still need prompt discipline for actual edits.
