# Changelog

## Unreleased

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
