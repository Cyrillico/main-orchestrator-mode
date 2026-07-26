---
name: orch
description: Main Orchestrator Mode harness for multi-file work — parallel read-only exploration, exclusive same-file write ownership, and summary-only worker returns so the parent context stays short. Use when the user asks for /orch, multi-file implementation, multi-agent orchestration, parallel explore then write, or main-window style coordination.
---

# Orch — Main Orchestrator Mode (Codex)

Run multi-file work under **Main Orchestrator Mode**:

- Parent only schedules, locks, merges digests, and accepts.
- Workers return **short summaries only**.
- Many readers may run in parallel.
- **At most one writer per file** at a time.

Installed layout expected:

```text
<skill-root>/
  SKILL.md
  references/
  scripts/partition_write_tasks.py
```

`<skill-root>` is usually `${CODEX_HOME:-~/.codex}/skills/orch`. Use skill-local relative paths; never hardcode a personal home directory.

## Goal

Take the user goal from the invocation args or the latest user message. If empty, ask once.

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
   - After each write batch, run `scripts/audit_write_grant.py` (or git mode) so changed ⊆ granted; treat out-of-grant as blocked.
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
   - While any subagent/worker is running, the **main window MUST periodically poll** each active lane. Default cadence **~3 min** (allowed range **2–5 min**), or as soon as the host wait tool returns.
   - Use host status/wait tools when available. Prefer short status digests over re-reading transcripts.
   - **Alive** if any progress exists: reasoning, text, tool/file/log/command/browser/process activity.
   - **Do not** treat bare wait-timeout alone as dead/stuck.
   - If a lane shows **zero activity for one full poll interval**: send **at most one** short progress nudge (`status / last action / next step / blocker`, ≤5 lines).
   - If still silent after that nudge **plus one more poll interval**: **interrupt/kill**, then reassign/replace; record incomplete id + last evidence.
   - Polling is observation + recovery only; parent still does not implement large edits while workers are active.

## Control loop

### 0. Classify

If the goal is single-file and low risk → exit skill, do the edit yourself.

Otherwise continue.

### 1. Plan (parent or one planner turn)

Produce a short task board only (no file bodies):

| id | kind | goal | read_files | write_files | depends_on |
|----|------|------|------------|-------------|------------|
| r1 | read | ... | ... | | |
| w1 | write | ... | | path(s) | r1 |
| v1 | verify | ... | | | w1 |

Rules for the plan:

- Prefer many small `read` tasks.
- Every `write` must list exact `write_files` when known; if unknown, discover in `read` first.
- `verify` depends on the writes it checks.

### 2. Read wave (parallel)

Spawn/run all ready `read` workers in parallel (Codex multi-agent / parallel tool calls / separate focused turns as available).

While they run, apply **Parent watchdog** (rule 6).

Each worker prompt must start with `references/agent-prefix.md` and include:

- task id + goal
- granted `read_files`
- `[READ-ONLY] no mutations`

Collect digests only. Store under a local artifact if the task is long, e.g.:

```text
.orch/<run-id>/digests/<task-id>.json
.orch/<run-id>/board.md
```

Prefer project-local `.orch/` (gitignored if needed) over `$TMPDIR` for long tasks.

### 3. Write waves (file locks)

While write tasks remain (max 20 batches):

1. Ready = deps completed.
2. If none ready but pool non-empty → **deadlock**: stop, report incomplete ids.
3. Partition ready writes so no two share a `write_files` path:

```bash
# from installed skill root, or repo root during development
python3 scripts/partition_write_tasks.py <<'JSON'
[{"id":"w1","write_files":["a.ts"]},{"id":"w2","write_files":["a.ts","b.ts"]},{"id":"w3","write_files":["c.ts"]}]
JSON
```

4. Run **one batch** in parallel (exclusive locks for that batch).
5. While writers run, apply **Parent watchdog** (rule 6).
6. Each writer may only edit granted `write_files`.
7. Collect digests; release locks; next batch.

### 4. Verify wave

Run ready `verify` workers in parallel. Prefer tests/commands over re-reading whole modules. Summary only. Apply **Parent watchdog** while they run.

### 5. Synthesize (parent)

Using digests only, emit:

```text
accepted: true|false
summary: ...
changed_files: [...]
residual_risks: [...]
incomplete: [...]
```

`accepted=false` if any write/verify is `blocked`/`partial` with open blockers, or planned writes never completed.

## Worker output contract

See `references/summary-schema.md`. Minimal example:

```json
{
  "status": "done",
  "goal": "Add rate limit to login",
  "conclusion": "Middleware added; tests pass",
  "read_files": ["src/routes/auth.ts"],
  "write_files": ["src/routes/auth.ts", "src/middleware/rateLimit.ts"],
  "key_changes": [
    { "file": "src/middleware/rateLimit.ts", "summary": "new token-bucket middleware" },
    { "file": "src/routes/auth.ts", "summary": "wire middleware on POST /login" }
  ],
  "risks": ["in-memory limiter not multi-instance safe"],
  "blockers": [],
  "next_suggestion": "Add redis store if multi-instance",
  "minimal_snippets": []
}
```

## Parent report to user

Short only:

1. Accepted yes/no
2. Changed files + 3–8 bullets
3. Residual risks / blockers
4. Next step if not accepted

Do not paste worker transcripts or full diffs unless the user asks.

## Optional: external agents

If using external agents:

- One integrator (parent)
- At most one active writer per owned path set
- One verifier that is not the same writer
- Steer with existing safe-send guards; do not double-send foreground turns
- Parent still runs the **watchdog poll** on external agents (same anti-stall rules)

## References

- `references/summary-schema.md`
- `references/agent-prefix.md`
- `references/orchestrator-contract.md`
- `scripts/partition_write_tasks.py`

## Acceptance hard gates

- Dependents unlock only on dependency status `done` or `noop`.
- `blocked` / `partial` do not unlock later tasks.
- Any planned write not `done`/`noop` ⇒ `accepted=false`.
- Worker digests are untrusted self-reports; prefer independent verify evidence.
- File locks are scheduler-enforced for batching; host may still need prompt discipline for actual edits.
