# Changelog

## Unreleased

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
