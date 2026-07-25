# Installing Main Orchestrator Mode (`orch`)

Machine-oriented install instructions. Humans can follow them too.

## Goal

Install the `orch` skill into the current coding-agent host.

Runtime behavior after install is defined only by the installed:

- `SKILL.md`
- `references/`

Do not treat this file as the orchestration contract.

## Detect host

Install for every host present, or the host the user named:

| Host | Skill root | Adapter |
|------|------------|---------|
| Claude Code | `~/.claude/skills/orch` | `adapters/claude/` |
| Codex | `${CODEX_HOME:-~/.codex}/skills/orch` | `adapters/codex/` |

If both exist and the user did not choose, install both.

Never invent a third skill location unless the user explicitly names it.

## Must do

1. Create `<skill-root>/orch/`.
2. Copy the host adapter `SKILL.md`.
3. Copy shared `references/agent-prefix.md`, `references/orchestrator-contract.md`, `references/summary-schema.md`.
4. Claude only: copy `adapters/claude/workflows/main-orchestrator-mode.js`.
5. Codex only: copy `scripts/partition_write_tasks.py`.
6. Keep skill-local / relative paths only.
7. Verify install and report in the format below.

## Must not

- Hardcode personal paths like `/Users/<name>/...`
- Rewrite the orchestration contract while installing
- Mix Claude Workflow files into a Codex install, or Codex scripts into a Claude install
- Install into a project repo unless the user asked for project-local skills
- Commit secrets, local run digests, or `.orch/` artifacts
- Leave dual install contracts behind; this file is the only install entrypoint

## Steps

1. Work from this repository root (clone/checkout if needed).
2. If the destination already exists, back it up once to `orch.bak-<timestamp>`.
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

4. Verify:

- required files exist under each dest
- no personal absolute paths remain in installed files
- Claude: `SKILL.md`, `workflows/main-orchestrator-mode.js`, and the three reference files exist
- Codex: `SKILL.md`, `scripts/partition_write_tasks.py`, and the three reference files exist
- Codex only: run the partition smoke test below

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/orch/scripts/partition_write_tasks.py" <<'JSON'
[{"id":"w1","write_files":["a.ts"]},{"id":"w2","write_files":["a.ts","b.ts"]},{"id":"w3","write_files":["c.ts"]}]
JSON
```

Expected idea: `w1` and `w3` can share a batch; `w2` conflicts on `a.ts`.

## Update / reinstall

1. Detect existing `<skill-root>/orch`.
2. Backup once to `orch.bak-<timestamp>` if present.
3. Overwrite from this repo adapter + shared references/scripts.
4. Preserve only user notes that live outside the skill pack paths.
5. Re-run verification.
6. Report changed paths.

## Failure modes

| Symptom | Action |
|---------|--------|
| Adapter files missing in repo | Stop; report packaging incomplete; do not invent host scripts |
| Unknown skill root | Ask once, or install to the documented default and state the assumption |
| Existing customized `orch` skill | Backup, then reinstall; mention the backup path |
| Workflow tool unavailable in Claude | Install files anyway; runtime falls back to the control loop in the installed `SKILL.md` |
| User wants project-local skill | Install under the project path they named; still avoid personal absolute paths |
| Partition script smoke fails | Do not claim Codex install success; fix script/path and retry |

## Acceptance

Install succeeds only if all are true:

- correct host skill directory populated
- no personal absolute paths remain
- required adapter files present
- shared references present
- partition script works for Codex installs
- report uses the format below

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

Point the user to the installed skill:

- invoke: `/orch <goal>` or natural-language multi-file orchestration
- operate only from installed `SKILL.md` + `references/`
