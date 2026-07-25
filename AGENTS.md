# AGENTS.md — install and operate Main Orchestrator Mode

This file is for AI agents installing, updating, or using this skill pack.

If you were only given a short prompt, still follow this file when present.

## Goal

Install `orch` (Main Orchestrator Mode) into the correct host skill directory, preserve the contract, and leave the user with a working `/orch` or skill trigger.

## Read first

1. `README.md` — product overview and layout
2. `LICENSE` — MIT
3. This file — install/operate rules
4. Host adapter under `adapters/<host>/`
5. `references/*` — do not invent alternate summary schemas

## Detect host

Choose one install target:

| Host | Typical skill root | Adapter source |
|------|--------------------|----------------|
| Claude Code | `~/.claude/skills` | `adapters/claude/` |
| Codex CLI / Desktop | `~/.codex/skills` or configured Codex skills root | `adapters/codex/` |

Detection hints:

- Claude Code session / `~/.claude` present → Claude path
- Codex session / `~/.codex` or `CODEX_HOME` present → Codex path
- If both exist and user did not specify, install both, or ask once

Never invent a third proprietary location unless the user explicitly names it.

## Install contract

### Must do

1. Create skill dir: `<skill-root>/orch/`
2. Copy **host adapter SKILL.md** into `<skill-root>/orch/SKILL.md`
3. Copy shared `references/` into `<skill-root>/orch/references/`
4. For Claude: copy `adapters/claude/workflows/main-orchestrator-mode.js` into `<skill-root>/orch/workflows/`
5. For Codex: copy `scripts/partition_write_tasks.py` into `<skill-root>/orch/scripts/`
6. Rewrite any absolute personal paths to skill-local / relative paths
7. Keep license copyright notice if redistributing

### Must not do

1. Do not hardcode `/Users/<name>/...` paths
2. Do not mix Claude Workflow JS APIs into Codex SKILL as if they were portable
3. Do not replace summary schema field names
4. Do not install into a project repo unless user asks for project-local skills
5. Do not commit secrets, local run digests, or `.orch/` artifacts
6. Do not "improve" the orchestration contract while installing

## Exact install steps

### Claude Code

```bash
REPO_ROOT="<this-repo>"
DEST="${HOME}/.claude/skills/orch"
mkdir -p "$DEST/workflows" "$DEST/references"
cp "$REPO_ROOT/adapters/claude/SKILL.md" "$DEST/SKILL.md"
cp "$REPO_ROOT/references/"*.md "$DEST/references/"
cp "$REPO_ROOT/adapters/claude/workflows/main-orchestrator-mode.js" \
  "$DEST/workflows/main-orchestrator-mode.js"
```

Post-check:

- `SKILL.md` exists
- `workflows/main-orchestrator-mode.js` exists
- `references/summary-schema.md` exists
- no `/Users/` absolute skill path remains in `SKILL.md`

If adapter SKILL still mentions Workflow `scriptPath`, it must resolve inside `$DEST/workflows/...` via relative path or an env/skill-local expression, not a personal home path.

### Codex

```bash
REPO_ROOT="<this-repo>"
DEST="${CODEX_HOME:-$HOME/.codex}/skills/orch"
mkdir -p "$DEST/scripts" "$DEST/references"
cp "$REPO_ROOT/adapters/codex/SKILL.md" "$DEST/SKILL.md"
cp "$REPO_ROOT/references/"*.md "$DEST/references/"
cp "$REPO_ROOT/scripts/partition_write_tasks.py" "$DEST/scripts/"
chmod +x "$DEST/scripts/partition_write_tasks.py" || true
```

Post-check:

- `python3 "$DEST/scripts/partition_write_tasks.py"` accepts the README sample JSON
- `SKILL.md` points to `scripts/partition_write_tasks.py` relatively
- references are present

## Update / reinstall

1. Detect existing `<skill-root>/orch`
2. Backup once if dirty/customized: copy to `orch.bak-<timestamp>`
3. Overwrite skill files from this repo adapter + shared references/scripts
4. Preserve user-local notes only if they live outside the skill pack paths
5. Report changed paths

## Operate after install

When user asks for multi-file orchestration:

1. Load skill rules
2. Parent schedules only
3. Workers return summary-only digests
4. Write tasks are file-locked
5. Parent polls ~every 3 minutes; bare wait-timeout ≠ dead
6. Final user report is short: accepted, changed files, risks, next step

If goal is trivial single-file: skip skill and edit directly.

## Acceptance for install task

Install is successful only if all are true:

- correct host skill directory populated
- no personal absolute paths remain
- required adapter files present
- shared references present
- partition script works for Codex installs
- user gets a one-screen summary of where it was installed and how to invoke it

## Failure modes

| Symptom | Action |
|---------|--------|
| Adapter files missing in repo | Stop; report packaging incomplete; do not invent host scripts |
| Unknown skill root | Ask once, or install to documented default and state assumption |
| Existing customized orch skill | Backup, then reinstall; mention backup path |
| Workflow tool unavailable in Claude | Fall back to SKILL.md control loop without Workflow script |
| User wants project-local skill | Install under project path they named; still avoid absolute personal paths |

## Output format after install

Return only:

```text
installed: yes|no
host: claude|codex|both|unknown
dest: <path(s)>
files:
- ...
invoke: /orch <goal> or natural-language trigger
notes:
- ...
```

No long transcripts.
