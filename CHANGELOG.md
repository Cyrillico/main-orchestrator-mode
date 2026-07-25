# Changelog

## Unreleased

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
