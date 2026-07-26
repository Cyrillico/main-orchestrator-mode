# Changelog

## Unreleased

## 0.1.12 — 2026-07-27

Anti-loop defaults (review/re-orch thrash):

- **One pass per user turn** then STOP — do not re-orch or re-Workflow for the same goal because residuals remain
- accept_gate pending residual: run accept_with_audit.py once, not a new review wave
- Forbid nested review-of-review / plan-of-plan without a new explicit user ask
- Watchdog reassign = one stalled worker only, not full board restart
- Planner/synthesize wording: no recursive re-audit recommendations

## 0.1.11 — 2026-07-27

Fixes from real Claude Code orch sessions:

- **In-repo absolute grants stripped** to repo-relative (heuristic top-level + `args.repo` / cwd); outside-repo abs still fail closed — stops empty runs when goals paste `/Volumes/.../docs/...`
- **Claude SKILL hard-locks Workflow** to skill `main-orchestrator-mode.js` only; forbids inventing `/tmp/**/*.js` scripts
- **Accept gate report contract:** parent must emit `scheduler_accepted` / `accept_gate` / `clean`; residual says NOT CLEAN until `accept_with_audit.py` ok
- Planner/verify prompts: repo-relative paths, small READ_ONLY fan-out, no GNU `timeout` on macOS
- Tests: path strip + residual wording; Python `test_orch_paths.py`

## 0.1.10 — 2026-07-26

Application-safety defaults (without gutting v0.1.5–0.1.7 hard gates):

- **Single-file skip** at the top of host-neutral and adapter SKILL docs
- **Codex control loop:** pre-batch `BASE` + `partition_write_tasks.py` and post-batch accept gate are required, not optional
- **Claude post-return:** parent must run accept gate before treating a write-bearing run as clean; Workflow residual names the gate
- New helper `scripts/accept_with_audit.py` — `scheduler_accepted` ∧ disk grant audit (`base` required in git mode)
- Contract section **Application-safety defaults**; INSTALL verify covers accept-gate smokes
- Claude installs ship partition script too (Fallback / explicit parent use)

## 0.1.9 — 2026-07-26

- Grill-me-style thinner SKILL triggers (~25–35 lines)
- Details stay in `references/` + workflow/scripts (gates not removed)
- Optional `agents/openai.yaml` (explicit invocation preference)

## 0.1.8 — 2026-07-26

- Slim skill surfaces on top of v0.1.7 hard gates (no runtime gate removal)
- Host-neutral + Claude/Codex SKILL docs compressed; contract/schema tightened
- README install stays complete (Claude gets scripts for post-run audit)

## 0.1.7 — 2026-07-26

Runtime-risk audit of v0.1.6, run against a real install. Every item below was
reproduced by executing the shipped script with stubbed Workflow globals before it was
fixed; each has a regression test in `tests/workflow-scheduler.test.mjs`.

- **Duplicate planner ids silently lost work and still reported success.** Every
  registry (`done`, `successIds`, `digestsById`) is keyed by task id, so two tasks
  sharing an id both ran in one batch, the second digest overwrote the first, the loser's
  `write_files` never reached `changed_files`, and dependents unlocked off whichever
  digest survived. `accepted=true` with real edits missing from the report. Duplicate ids
  are now rejected before spawn; the first task with an id keeps it.
- **Read workers could be handed write tools and a write grant.** `agent_type: 'claude'`
  on a `kind=read` task routed it to the full-tool catch-all agent, and the prompt printed
  `Granted write_files: [...]` directly above `[READ-ONLY] No file mutations allowed`.
  Because only *planned* writes feed `changed_files`, a read worker's edits landed
  invisibly and the run still accepted. Reads are now pinned to the read-only agent and
  their write grant is dropped (with a log line when the planner supplied one).
- **Worker-reported `write_files` was never re-checked.** The up-front guard validated
  what the planner asked for; a digest claiming `["src/a.ts","/etc/passwd"]` was accepted
  verbatim and flowed into `changed_files`. Pure path comparison needs no shell, so the
  scheduler now enforces reported ⊆ granted and blocks the task otherwise. The disk-level
  check still requires `scripts/audit_write_grant.py`.
- **Deadlocked, starved and skipped tasks left no digest.** A `depends_on` cycle or
  self-reference, exhausting the 20-batch guard, or a verify whose write never succeeded
  all failed closed correctly but surfaced only as an id in `incomplete[]` plus a log line
  the parent is told not to read. Each now gets a `blocked` digest naming the cause.
- Zero-verify plans still accept (the contract's "if any"), but now report
  `no verify task was planned` as a residual risk; a run with changed files also reports
  that the in-script audit is path-level only and `audit_write_grant.py` was not run.
- Docs: `.orch/<run-id>/` is a parent/Fallback duty. The workflow script has no
  filesystem access, so a Workflow run never creates it and digests exist only in the
  return value — `adapters/claude/SKILL.md` and `references/orchestrator-contract.md` said
  "prefer digests on disk" without saying nothing on the preferred path can write them.
- Docs: `references/agent-prefix.md` notes that the workflow script carries a hand-synced
  inline copy and cannot read the file at run time.

Deliberately unchanged: the script still ignores the `budget` global (fan-out is not
token-capped), still requests up to 40 concurrent writers in one batch, and still runs
every worker in the parent's working tree with no `isolation: 'worktree'` and no
prohibition on `git commit`/`push`. Those are policy calls, not defects.

## 0.1.6 — 2026-07-26

- Both Python scripts set `sys.dont_write_bytecode`: importing the shared `orch_paths`
  dropped a `__pycache__/` into the installed skill tree on every run, which
  `INSTALL.md` forbids as skill-discovery pollution. Found by running the 0.1.5 audit
  from a real install
- Audit test asserts it: the assertion clears the dir first, because an earlier-run
  cache made the first version of this check pass vacuously

## 0.1.5 — 2026-07-26

Audit and scheduler correctness. Found by reviewing the shipped code against the
contract; each item below was reproduced before it was fixed.

- **Audit was blind to committed changes.** `audit_write_grant.py` git mode read
  only `git status --porcelain`, so a worker that committed its out-of-grant edits
  left a clean tree and audited `ok`. Git mode now unions status with
  `git diff --name-only <base>..HEAD` and **requires** `base`; git mode without a
  baseline fails closed (exit 2) because a clean tree is ambiguous
- **Reads with `depends_on` were silently dropped.** The Claude workflow ran one
  read wave with an empty success set, so any read depending on another read never
  ran and every write behind it deadlocked (fail-closed, but the run was wasted).
  Now up to 2 waves, per the contract's own bound
- **Only `write_files` was path-checked.** `read_files`, and a verify task's
  `write_files`, reached workers as granted paths unnormalized — so a plan derived
  from an untrusted goal could grant an absolute path. The guard now runs over every
  task kind before any worker spawns; offending tasks are blocked
- A write worker returning no summary was re-spawned until the shared 20-batch guard
  drained. Now retried once, then blocked
- `changed_files` fell back to `[]` when the synthesizer returned null, hiding writes
  that had succeeded; it now falls back to the successful writes' digests
- Dead code: `doneIds` removed; `lockKey` wired into the JS partitioner (its Python
  twin `lock_key` was already live)
- Contract records all four rules; adapters document `base` in git mode
- New `tests/` (repo-only, no deps): 29 assertions covering every fix above. The
  scheduler suite stubs the Workflow runtime and evaluates the shipped script rather
  than reimplementing it; both suites accept a path so an installed skill can be
  checked in place
- INSTALL verify step gains a git-mode-without-`base` assertion, which is also how you
  detect a stale pre-0.1.5 install
## 0.1.4 — 2026-07-26

- Claude install now ships `scripts/audit_write_grant.py` + `scripts/orch_paths.py`; the contract's audit layer was previously Codex-only, so Claude installs had a dangling reference
- Claude adapter documents the post-workflow grant audit (workflow script cannot shell out) and that a skipped audit is a residual risk
- INSTALL/README: host-neutral audit smoke test + failure-mode row
- `partition_write_tasks.py` stays Codex-only (Claude partitions in the workflow script)

## 0.1.3 — 2026-07-26

- Claude: incomplete verifies hard-fail accept; no read ready-empty fallback
- Claude: path errors block only offending tasks; partial always open-blocker
- Case-insensitive lock keys (Foo.js vs foo.js)
- Reject scheme paths (`file://...`)
- README install aligned with INSTALL (external backup + full scripts)
- Codex: recommend audit_write_grant after each write batch

## 0.1.2 — 2026-07-26

- Add optional worker `evidence[]` (command/test/pathspec/git/audit/note)
- Add `scripts/audit_write_grant.py` post-batch grant audit
- Share path normalize via `scripts/orch_paths.py`
- Claude workflow surfaces missing verify evidence as residual risk

- Harden partitioner: empty-serial, strict repo-relative paths, reject abs/`..`
- Claude workflow: success-only deps, hard accept gate, incomplete in FINAL
- INSTALL: backup outside skills tree; prefer pinned tag/SHA; bak no longer under skills/
- Contracts clarify advisory vs scheduler hard gates; digests untrusted

- Removed root `AGENTS.md`
- `INSTALL.md` is the only install entrypoint and now includes update/reinstall, must-not, and failure modes
- Runtime contract remains only in `SKILL.md` + `references/`

## 0.1.0 — 2026-07-26

Initial public release.

- Host-neutral Main Orchestrator Mode contract (`SKILL.md`, `references/`)
- Claude Code adapter + Workflow script
- Codex adapter + `scripts/partition_write_tasks.py`
- Install docs and examples
