# Main Orchestrator Mode (`orch`)

Host-neutral multi-agent orchestration skill for multi-file work.

**Core idea:** parent only schedules / locks / merges; workers return short digests; many readers may run in parallel; **at most one writer per file**.

This repository packages:

- a portable orchestration **contract**
- worker **summary schemas**
- a small **write-batch partitioner**
- host adapters for **Claude Code** and **Codex**

> Status: packaging draft for open source. Runtime skill bodies may still be copied in from local installs before v0.1 release.

## Why

Multi-agent coding often fails in three ways:

1. Parent context explodes from full files / full diffs / long logs
2. Two agents edit the same path
3. Parent treats wait-timeout as "dead" and spam-continues healthy workers

`orch` enforces a control loop that avoids those failure modes.

## Hard rules

1. **Parent / main window**
   - Schedule, lock, merge, accept only
   - Do not load whole modules into parent context
   - Do not implement large edits while workers are active
   - Prefer digests under `.orch/<run-id>/`
2. **Workers**
   - Return summary only (`references/summary-schema.md`)
   - Never return full source, full diffs, or long logs
3. **Concurrency**
   - `read`: parallel OK
   - `write`: exclusive per file
   - different files may write in parallel
4. **Watchdog**
   - Poll active lanes about every **~3 min** (range 2–5)
   - Alive = any reasoning / tool / file / log / process progress
   - Bare wait-timeout alone is **not** dead
   - One short progress nudge if silent; reassign after nudge + another silent interval

## Control loop

```text
classify → plan → read wave(s) → write batches (file-locked) → verify → synthesize
```

Default bounds (raise only if user asks):

- 1 plan
- ≤2 read waves
- ≤20 write batches
- 1 verify wave
- 1 synthesize

## Directory layout

```text
main-orchestrator-mode/
├── README.md
├── LICENSE
├── AGENTS.md                      # AI install / operate instructions
├── prompts/
│   └── install-and-use.md         # short copy-paste prompt for AI
├── SKILL.md                       # host-neutral skill entry (canonical contract)
├── references/
│   ├── agent-prefix.md
│   ├── orchestrator-contract.md
│   └── summary-schema.md
├── scripts/
│   └── partition_write_tasks.py
├── adapters/
│   ├── claude/
│   │   ├── SKILL.md
│   │   └── workflows/
│   │       └── main-orchestrator-mode.js
│   └── codex/
│       └── SKILL.md
└── examples/
    ├── sample-board.json
    └── sample-digest.json
```

### What goes where

| Path | Role |
|------|------|
| `SKILL.md` | Canonical, host-neutral rules |
| `references/` | Schemas and contracts loaded on demand |
| `scripts/` | Pure helpers with no host dependency |
| `adapters/claude/` | Claude Code skill + Workflow script |
| `adapters/codex/` | Codex skill entry |
| `AGENTS.md` | Instructions for AI installers/operators |
| `prompts/install-and-use.md` | Short prompt a human can paste to an AI |

## Install

### Option A — ask an AI to install

Paste `prompts/install-and-use.md` into Claude Code / Codex and point it at this repo path or GitHub URL.

Also see `AGENTS.md` for machine-oriented install steps.

### Option B — Claude Code manual

```bash
# from this repo root
mkdir -p ~/.claude/skills/orch
cp adapters/claude/SKILL.md ~/.claude/skills/orch/SKILL.md
cp -R references ~/.claude/skills/orch/
mkdir -p ~/.claude/skills/orch/workflows
cp adapters/claude/workflows/main-orchestrator-mode.js \
  ~/.claude/skills/orch/workflows/
# ensure SKILL.md uses relative/local skill path, not a hardcoded /Users/... path
```

### Option C — Codex manual

```bash
# Codex skills root is commonly ~/.codex/skills or your configured skills dir
mkdir -p ~/.codex/skills/orch
cp adapters/codex/SKILL.md ~/.codex/skills/orch/SKILL.md
cp -R references ~/.codex/skills/orch/
mkdir -p ~/.codex/skills/orch/scripts
cp scripts/partition_write_tasks.py ~/.codex/skills/orch/scripts/
```

### Verify partition helper

```bash
python3 scripts/partition_write_tasks.py <<'JSON'
[
  {"id":"w1","write_files":["a.ts"]},
  {"id":"w2","write_files":["a.ts","b.ts"]},
  {"id":"w3","write_files":["c.ts"]}
]
JSON
```

Expected idea: `w1` and `w3` can share a batch; `w2` conflicts with `w1` on `a.ts`.

## Usage

Trigger phrases:

- `/orch <goal>`
- "use main orchestrator mode"
- multi-file implementation / refactor that needs parallel explore then locked writes

Parent final report should stay short:

1. Accepted? yes/no
2. Changed files + 3–8 bullets
3. Residual risks / blockers
4. Next step if not accepted

Do **not** paste worker transcripts.

## Artifact layout during a run

Prefer project-local:

```text
.orch/<run-id>/
  board.md
  digests/<task-id>.json
```

Add `.orch/` to `.gitignore` if needed.

## Non-goals

- Not a full agent runtime
- Not a replacement for Claude Workflow / Codex multi-agent host APIs
- Not for trivial single-file edits (just edit directly)

## License

MIT — see `LICENSE`.

## Provenance note

Originally extracted from personal Claude Code / Codex skill installs and generalized for public packaging. Host-specific wiring lives under `adapters/`.
