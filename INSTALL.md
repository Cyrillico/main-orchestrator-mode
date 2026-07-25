# Installing Main Orchestrator Mode (`orch`)

Machine-oriented install instructions. Humans can follow them too.

## Goal

Install the `orch` skill into the current coding-agent host so multi-file work can use Main Orchestrator Mode.

## Detect host

Install for every host present, or the host the user named:

| Host | Skill root | Adapter |
|------|------------|---------|
| Claude Code | `~/.claude/skills/orch` | `adapters/claude/` |
| Codex | `${CODEX_HOME:-~/.codex}/skills/orch` | `adapters/codex/` |

If both exist and the user did not choose, install both.

## Steps

1. Work from this repository root (clone/checkout if needed).
2. If `<skill-root>` already exists, back it up once to `orch.bak-<timestamp>`.
3. Install files:

### Claude Code

```bash
DEST="${HOME}/.claude/skills/orch"
mkdir -p "$DEST/workflows" "$DEST/references"
cp adapters/claude/SKILL.md "$DEST/SKILL.md"
cp references/agent-prefix.md references/orchestrator-contract.md references/summary-schema.md "$DEST/references/"
cp adapters/claude/workflows/main-orchestrator-mode.js "$DEST/workflows/"
```

### Codex

```bash
DEST="${CODEX_HOME:-$HOME/.codex}/skills/orch"
mkdir -p "$DEST/scripts" "$DEST/references"
cp adapters/codex/SKILL.md "$DEST/SKILL.md"
cp references/agent-prefix.md references/orchestrator-contract.md references/summary-schema.md "$DEST/references/"
cp scripts/partition_write_tasks.py "$DEST/scripts/"
chmod +x "$DEST/scripts/partition_write_tasks.py" || true
```

4. Do **not** hardcode personal paths like `/Users/<name>/...`.
5. Do **not** rewrite the orchestration contract while installing.
6. Verify:

- required files exist under each dest
- no personal absolute paths remain in installed files
- Codex only: run the partition smoke test below

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/orch/scripts/partition_write_tasks.py" <<'JSON'
[{"id":"w1","write_files":["a.ts"]},{"id":"w2","write_files":["a.ts","b.ts"]},{"id":"w3","write_files":["c.ts"]}]
JSON
```

Expected idea: `w1` and `w3` can share a batch; `w2` conflicts on `a.ts`.

## Report format

Return only:

```text
installed: yes|no
host: claude|codex|both|unknown
dest: <path(s)>
files:
- ...
invoke: /orch <goal>
notes:
- ...
```

## After install

When the user says `/orch <goal>` or asks for multi-file orchestration:

- parent only schedules / locks / merges
- workers return short digests only
- one writer per file
- poll active workers ~every 3 min; bare wait-timeout is not dead

Runtime contract after install: the installed `SKILL.md` and `references/`.

## Update / reinstall

1. Detect existing `<skill-root>/orch`.
2. Backup once to `orch.bak-<timestamp>` if present.
3. Overwrite from this repo adapter + shared references/scripts.
4. Re-run verification.

## Do not

- Hardcode personal paths like `/Users/<name>/...`
- Rewrite the orchestration contract while installing
- Mix Claude Workflow files into a Codex install, or Codex scripts into a Claude install
- Install into a project repo unless the user asked for project-local skills
