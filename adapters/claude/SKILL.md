---
name: orch
description: Main Orchestrator Mode harness — schedule subagents with parallel read-only exploration, exclusive same-file write locks, and short summary-only returns. Use when the user asks for /orch, multi-file implementation, multi-agent orchestration, parallel explore then write, or main-window orchestration that must keep the parent context short.
argument-hint: <goal>
disable-model-invocation: false
---

# Orch — Main Orchestrator Mode (Claude Code)

Run multi-file work under **Main Orchestrator Mode**: parent only schedules/merges; workers return short summaries; many read workers may run in parallel; **one writer per file at a time**.

Installed layout expected:

```text
<skill-root>/
  SKILL.md
  references/
  workflows/main-orchestrator-mode.js
  scripts/audit_write_grant.py
  scripts/orch_paths.py
```

`<skill-root>` is usually `~/.claude/skills/orch`. Resolve paths from this skill directory; never hardcode a personal `/Users/<name>/...` path.

## Goal

User goal (from args or message):

```text
$ARGUMENTS
```

If `$ARGUMENTS` is empty, use the latest user goal from the conversation. If still empty, ask once for the goal.

## Preferred path — Workflow tool

If the **Workflow** tool is available in this session, this skill invocation is your authorization. Launch:

```js
Workflow({
  // Resolve to this skill's workflows/main-orchestrator-mode.js (absolute path OK if derived from skill root)
  scriptPath: "<skill-root>/workflows/main-orchestrator-mode.js",
  args: { goal: "$ARGUMENTS" }
})
```

How to resolve `scriptPath`:

1. Prefer the directory that contains this `SKILL.md`
2. Append `workflows/main-orchestrator-mode.js`
3. If needed, expand `~/.claude/skills/orch/workflows/main-orchestrator-mode.js` for a default install
4. Do **not** embed another user's home path

Notes:

- Watch progress with `/workflows`.
- Parent should poll workflow/subagent status (~every 3 min) via host tools when available; recover stalled lanes with one nudge, then **interrupt and reassign**. The workflow script awaits batches and does not implement a timer watchdog itself.
- Parent session must **not** Read whole modules or paste long logs while the workflow runs.
- After the workflow returns, report only: `final.accepted`, `final.summary`, `final.changed_files`, `final.residual_risks`, plus any open blockers from digests.
- Do **not** re-read full sources to re-verify unless a digest marks `blocked` and the blocker requires a single path:line check (≤20 lines).

If Workflow is unavailable, use the **Fallback** section below.

## Hard rules (always)

1. **Parent / main window**
   - Schedule, lock, merge, accept — only.
   - **Watchdog poll** while any subagent is active: check each lane about every **~3 min** (range **2–5 min**), or when wait/workflow status returns.
   - Alive = any reasoning/text/tool/file/log/command/browser/process progress. Do **not** treat bare wait-timeout alone as stuck.
   - If zero activity for one poll interval → **one** short progress nudge (≤5 lines). If still silent after nudge + one more interval → mark stalled, reassign/replace, record incomplete id.
   - Forbidden: long-context reads (whole files/modules), large inline implementation, full transcript dumps, spam "continue" into healthy workers.
2. **Workers / subagents**
   - Return **summary only** (see schema in `references/summary-schema.md`).
   - Never return full source, full diffs, or long logs.
   - At most 8 one-line `key_changes`; `minimal_snippets` default empty (≤2 × ≤20 lines if unavoidable).
3. **Concurrency**
   - `kind=read`: parallel OK.
   - `kind=write`: exclusive per file; empty `write_files` run alone; paths repo-relative only (no abs/`..`).
   - Different files may write in parallel.
   - **Grant audit:** the workflow script cannot shell out, so after it returns (or after each
     fallback write batch) run `<skill-root>/scripts/audit_write_grant.py` to check
     changed ⊆ granted. Out-of-grant paths ⇒ treat that write as `blocked` and
     `accepted=false`. Skipping the audit is a residual risk, not a pass.

     Record the baseline **before** the batch, then audit against it. `base` is
     required in git mode: without it a worker that commits its edits leaves a clean
     tree and would audit as ok.

     ```bash
     BASE=$(git rev-parse HEAD)   # before the write batch
     python3 "<skill-root>/scripts/audit_write_grant.py" <<JSON
     {"granted":["src/a.ts","src/b.ts"],"git":true,"repo":".","base":"$BASE"}
     JSON
     ```

     Exit `0` = clean, `1` = out-of-grant (or empty grant with changes), `2` = usage/git error.
4. **Success**
   - Parent context stays short.
   - Prefer digests on disk (`.orch/<run-id>/`) over re-injecting worker transcripts.
   - Zero dual-writers on one file.
   - Acceptance decided from digests only.

## Fallback — no Workflow tool

Execute the same control loop in the parent, still without long parent reads:

### 1. Plan (one agent, short)

Spawn one planner agent. Prompt prefix from `references/agent-prefix.md`. Force a short task list:

- Each task: `id`, `kind` (`read`|`write`|`verify`), `goal`, `read_files[]`, `write_files[]`, optional `depends_on[]`
- No file bodies in the plan

### 2. Read wave (parallel)

For every `kind=read` task with satisfied deps, spawn **Explore** (or read-only) agents in parallel.

- Grant only listed `read_files` (or broader search if list empty, but still summary-only).
- Collect only SUMMARY fields.
- While running, apply parent watchdog poll (~3 min); progress-nudge once if silent; reassign if stalled.

### 3. Write waves (file-locked batches)

While write tasks remain:

1. Take tasks whose `depends_on` are done.
2. Greedy partition so no two tasks in a batch share a `write_files` path.
3. Run one batch in parallel; then recompute ready set.
4. While writers run, apply parent watchdog poll (~3 min); progress-nudge once if silent; reassign if stalled.
5. Writers may only edit granted `write_files`.

### 4. Verify (parallel when independent)

Spawn verify agents for `kind=verify` with deps done. Prefer tests/commands over re-reading entire modules. Summary only.

### 5. Synthesize

From digests only, produce:

```text
accepted: true|false
summary: ≤800 chars
changed_files: [...]
residual_risks: [...]
```

If any write/verify is `blocked`/`partial` with open blockers → `accepted=false`.

## Hard gates (workflow)

- Only `done`/`noop` unlocks dependents.
- Incomplete writes force `accepted=false` even if synthesizer says otherwise.
- Invalid write paths reject the batch.

## Output to user

Keep the final user-facing report short:

1. Accepted? yes/no
2. What changed (file list + 3–8 bullets from digests)
3. Residual risks / blockers
4. Suggested next step if not accepted

Do not paste worker transcripts.

## References

- Workflow script: `workflows/main-orchestrator-mode.js`
- Summary schema: `references/summary-schema.md`
- Agent prompt prefix: `references/agent-prefix.md`
- Control contract: `references/orchestrator-contract.md`
