# Installing Main Orchestrator Mode (`orch`)

Machine-oriented install instructions. Humans can follow them too.

## Goal

Install the `orch` skill into the current coding-agent host.

Runtime behavior after install is defined only by the installed:

- `SKILL.md`
- `references/`
- host adapter extras (`workflows/` or `scripts/`)

## Trust / integrity

Prefer a **pinned** checkout, not floating `main` content alone:

```bash
git clone https://github.com/Cyrillico/main-orchestrator-mode.git
cd main-orchestrator-mode
git checkout v0.1.9   # or a full commit SHA
```

If you must fetch `INSTALL.md` over HTTP, pin the URL to a tag or commit:

```text
https://raw.githubusercontent.com/Cyrillico/main-orchestrator-mode/v0.1.9/INSTALL.md
```

Do not treat unpinned `main` as an integrity guarantee.

## Detect host

Install only for hosts the user named. If unspecified and both exist, **ask once**; only install both when the user says so.

| Host | Skill root | Adapter |
|------|------------|---------|
| Claude Code | `~/.claude/skills/orch` | `adapters/claude/` |
| Codex | `${CODEX_HOME:-~/.codex}/skills/orch` | `adapters/codex/` |

Print the resolved realpath of each destination before writing.

## Must do

1. Create destination skill dir.
2. If destination exists, **backup outside the skills tree** first.
3. Copy host adapter + shared references + host scripts (`workflows/` and/or `scripts/`).
4. Keep skill-local paths only.
5. Verify install and report.

## Must not

- Hardcode personal paths like `/Users/<name>/...`
- Rewrite the orchestration contract while installing
- Mix Claude and Codex adapter files into the wrong host
- Backup into `.../skills/orch.bak-*` (pollutes skill discovery)
- Install into a project repo unless the user asked for project-local skills

## Backup location

Use a directory **outside** any skills root:

```bash
BACKUP_ROOT="${XDG_DATA_HOME:-$HOME/.local/share}/orch-backups"
mkdir -p "$BACKUP_ROOT"
```

If destination exists:

```bash
TS=$(date +%Y%m%dT%H%M%S%z)
BACKUP="$BACKUP_ROOT/orch-$(basename "$(dirname "$DEST")")-$TS"
mv "$DEST" "$BACKUP"
test -d "$BACKUP"
```

Never leave `SKILL.md` backups under `~/.claude/skills/` or `~/.codex/skills/`.

## Steps

Work from this repository root (pinned checkout).

### Claude Code

```bash
DEST="${HOME}/.claude/skills/orch"
BACKUP_ROOT="${XDG_DATA_HOME:-$HOME/.local/share}/orch-backups"
mkdir -p "$BACKUP_ROOT"
if [ -e "$DEST" ]; then
  TS=$(date +%Y%m%dT%H%M%S%z)
  mv "$DEST" "$BACKUP_ROOT/orch-claude-$TS"
  test -d "$BACKUP_ROOT/orch-claude-$TS"
fi
mkdir -p "$DEST/workflows" "$DEST/references" "$DEST/scripts"
cp adapters/claude/SKILL.md "$DEST/SKILL.md"
cp references/agent-prefix.md references/orchestrator-contract.md references/summary-schema.md "$DEST/references/"
cp adapters/claude/workflows/main-orchestrator-mode.js "$DEST/workflows/"
cp scripts/audit_write_grant.py scripts/orch_paths.py "$DEST/scripts/"
chmod +x "$DEST/scripts/audit_write_grant.py" || true
```

`scripts/` is required: `references/orchestrator-contract.md` names
`scripts/audit_write_grant.py` as the write-grant audit layer, so a Claude install
without it leaves that reference dangling. The Claude scheduler partitions write
batches in the workflow script, so `partition_write_tasks.py` is Codex-only.

### Codex

```bash
DEST="${CODEX_HOME:-$HOME/.codex}/skills/orch"
BACKUP_ROOT="${XDG_DATA_HOME:-$HOME/.local/share}/orch-backups"
mkdir -p "$BACKUP_ROOT"
if [ -e "$DEST" ]; then
  TS=$(date +%Y%m%dT%H%M%S%z)
  mv "$DEST" "$BACKUP_ROOT/orch-codex-$TS"
  test -d "$BACKUP_ROOT/orch-codex-$TS"
fi
mkdir -p "$DEST/scripts" "$DEST/references"
cp adapters/codex/SKILL.md "$DEST/SKILL.md"
cp references/agent-prefix.md references/orchestrator-contract.md references/summary-schema.md "$DEST/references/"
cp scripts/partition_write_tasks.py scripts/orch_paths.py scripts/audit_write_grant.py "$DEST/scripts/"
chmod +x "$DEST/scripts/partition_write_tasks.py" "$DEST/scripts/audit_write_grant.py" || true
```

## Verify

- required files exist
- no personal absolute paths in installed skill files
- no `orch.bak-*` directories remain under skills roots
- both hosts: audit smoke test (exit 1, `out_of_grant: ["src/c.ts"]`)

```bash
python3 "<skill-root>/scripts/audit_write_grant.py" <<'JSON'
{"granted":["src/a.ts"],"changed":["src/a.ts","src/c.ts"]}
JSON
```

- both hosts: git mode must **reject a missing `base`** (exit 2). A pre-0.1.5 script
  answers `ok: true` here, which is the signal that the install is stale and the audit
  is blind to committed edits.

```bash
python3 "<skill-root>/scripts/audit_write_grant.py" <<'JSON'
{"granted":["src/a.ts"],"git":true,"repo":"."}
JSON
```

- Codex: partition smoke test

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/orch/scripts/partition_write_tasks.py" <<'JSON'
[
  {"id":"e1","write_files":[]},
  {"id":"w1","write_files":["a.ts"]},
  {"id":"w2","write_files":["././a.ts"]},
  {"id":"w3","write_files":["b.ts"]}
]
JSON
```

Expected idea:

- `e1` alone
- `w1` then `w2` (same normalized path `a.ts`, exclusive)
- `w3` may share a batch with neither conflicting empty task

Reject paths with `..` or absolute prefixes.

## Update / reinstall

Same as install: backup outside skills tree, overwrite, verify, report backup path.

## Failure modes

| Symptom | Action |
|---------|--------|
| Adapter files missing | Stop; do not invent files |
| Unknown skill root | Ask; do not guess a third location |
| Backup fails | Abort install (fail closed) |
| `orch.bak-*` under skills/ | Move them to `~/.local/share/orch-backups/` and remove from skills discovery |
| Partition smoke fails | Do not claim Codex success |
| Audit smoke fails | Do not claim the write-grant audit layer is available |

## Report format

```text
installed: yes|no
host: claude|codex|both|unknown
dest: <realpath(s)>
backup: <path(s)|none>
files:
- ...
invoke: /orch <goal>
notes:
- ...
```
