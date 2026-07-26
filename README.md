# Main Orchestrator Mode (`orch`)

Multi-agent skill for multi-file work: short parent context, parallel reads, exclusive per-file writes, digest-only returns.

Skip trivial single-file edits.

## Quickstart

[Ask an agent](#ask-an-agent) · [Claude Code](#claude-code) · [Codex](#codex)

## How it works

```text
classify → plan → read → locked writes → verify → synthesize → accept gate
```

Hard gates include unique task ids, path normalize (in-repo abs strip / outside-repo reject), empty-write serial, case-insensitive locks, read-only readers, digest ⊆ grant, success-only deps, incomplete write/verify fail-closed.

**Application-safety defaults:** partition write batches, capture pre-write `base`, and run `scripts/accept_with_audit.py` before reporting clean. Git audit mode requires `base`.

## Installation

Prefer a pinned tag. Full steps: [`INSTALL.md`](./INSTALL.md).

### Ask an agent

```text
Fetch and follow instructions from https://raw.githubusercontent.com/Cyrillico/main-orchestrator-mode/v0.1.11/INSTALL.md
```

### Claude Code

```bash
DEST="${HOME}/.claude/skills/orch"
BACKUP_ROOT="${XDG_DATA_HOME:-$HOME/.local/share}/orch-backups"
mkdir -p "$BACKUP_ROOT"
[ -e "$DEST" ] && mv "$DEST" "$BACKUP_ROOT/orch-claude-$(date +%Y%m%dT%H%M%S%z)"
mkdir -p "$DEST/workflows" "$DEST/references" "$DEST/scripts" "$DEST/agents"
cp adapters/claude/SKILL.md "$DEST/SKILL.md"
cp adapters/claude/agents/openai.yaml "$DEST/agents/" 2>/dev/null || true
cp references/agent-prefix.md references/orchestrator-contract.md references/summary-schema.md "$DEST/references/"
cp adapters/claude/workflows/main-orchestrator-mode.js "$DEST/workflows/"
cp scripts/partition_write_tasks.py scripts/orch_paths.py scripts/audit_write_grant.py scripts/accept_with_audit.py "$DEST/scripts/"
chmod +x "$DEST/scripts/"*.py || true
```

### Codex

```bash
DEST="${CODEX_HOME:-$HOME/.codex}/skills/orch"
BACKUP_ROOT="${XDG_DATA_HOME:-$HOME/.local/share}/orch-backups"
mkdir -p "$BACKUP_ROOT"
[ -e "$DEST" ] && mv "$DEST" "$BACKUP_ROOT/orch-codex-$(date +%Y%m%dT%H%M%S%z)"
mkdir -p "$DEST/scripts" "$DEST/references" "$DEST/agents"
cp adapters/codex/SKILL.md "$DEST/SKILL.md"
cp adapters/codex/agents/openai.yaml "$DEST/agents/" 2>/dev/null || true
cp references/agent-prefix.md references/orchestrator-contract.md references/summary-schema.md "$DEST/references/"
cp scripts/partition_write_tasks.py scripts/orch_paths.py scripts/audit_write_grant.py scripts/accept_with_audit.py "$DEST/scripts/"
chmod +x "$DEST/scripts/"*.py || true
```

### Verify

```bash
python3 scripts/partition_write_tasks.py <<'JSON'
[{"id":"w1","write_files":["a.ts"]},{"id":"w2","write_files":["././a.ts"]},{"id":"w3","write_files":["b.ts"]}]
JSON

python3 scripts/accept_with_audit.py <<'JSON'
{"scheduler_accepted":true,"granted":["a.ts"],"changed":["a.ts"]}
JSON
```

## Usage

`/orch <goal>`. Parent report: accepted, files, short bullets, risks, next step.

Clean report requires the accept gate when writes may have landed (`scheduler_accepted` + `accept_gate` + `clean`). Claude must use only the skill workflow script.

## What's inside

| Path | Role |
|------|------|
| `SKILL.md` / `adapters/*` | short contracts + safety defaults |
| `references/` | schema + full contract |
| `scripts/` | partition · paths · grant audit · accept gate |
| `INSTALL.md` | machine install |

## License

MIT. See `LICENSE`.
