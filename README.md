# Main Orchestrator Mode (`orch`)

Main Orchestrator Mode is a multi-agent orchestration skill for multi-file work. It keeps the parent agent short-context: schedule, lock, and merge only. Workers explore in parallel, write with exclusive per-file ownership, and return summary digests instead of full dumps.

## Quickstart

Install `orch` for your agent: [Ask an agent](#ask-an-agent), [Claude Code](#claude-code), [Codex](#codex).

## How it works

When the work spans multiple files, the parent does **not** load whole modules or implement large edits itself. It builds a short task board, runs read-only workers in parallel, then runs write workers in file-locked batches so two agents never own the same path at once.

Workers return short structured digests only. The parent accepts or rejects from those digests, not from full transcripts. While workers run, the parent polls about every three minutes, treats real activity as alive, and only reassigns after a silent interval plus one short progress nudge.

There is more detail in `SKILL.md` and `references/`, but that is the core loop: plan → read → locked writes → verify → synthesize.

## Installation

Installation differs by harness. If you use more than one, install `orch` separately for each one.

### Ask an agent

Tell your coding agent:

```text
Fetch and follow instructions from https://raw.githubusercontent.com/Cyrillico/main-orchestrator-mode/main/INSTALL.md
```

### Claude Code

From this repository root:

```bash
mkdir -p ~/.claude/skills/orch/workflows ~/.claude/skills/orch/references
cp adapters/claude/SKILL.md ~/.claude/skills/orch/SKILL.md
cp references/agent-prefix.md references/orchestrator-contract.md references/summary-schema.md   ~/.claude/skills/orch/references/
cp adapters/claude/workflows/main-orchestrator-mode.js   ~/.claude/skills/orch/workflows/
```

### Codex

From this repository root:

```bash
mkdir -p ~/.codex/skills/orch/scripts ~/.codex/skills/orch/references
cp adapters/codex/SKILL.md ~/.codex/skills/orch/SKILL.md
cp references/agent-prefix.md references/orchestrator-contract.md references/summary-schema.md   ~/.codex/skills/orch/references/
cp scripts/partition_write_tasks.py ~/.codex/skills/orch/scripts/
```

### Verify

```bash
python3 scripts/partition_write_tasks.py <<'JSON'
[
  {"id":"w1","write_files":["a.ts"]},
  {"id":"w2","write_files":["a.ts","b.ts"]},
  {"id":"w3","write_files":["c.ts"]}
]
JSON
```

`w1` and `w3` can share a batch; `w2` conflicts with `w1` on `a.ts`.

## The Basic Workflow

1. **Classify** — Skip the skill for trivial single-file edits.
2. **Plan** — Build a short task board with `read` / `write` / `verify` tasks and exact `write_files` when known.
3. **Read wave** — Run ready read-only workers in parallel; collect digests only.
4. **Write batches** — Partition ready writers so no two share a path; run one exclusive batch at a time.
5. **Verify** — Prefer tests/commands over re-reading whole modules.
6. **Synthesize** — Accept or reject from digests; report changed files, risks, and next step.

Trigger with `/orch <goal>` or by asking for multi-file orchestration under Main Orchestrator Mode.

## What's Inside

- `SKILL.md` — host-neutral orchestration contract
- `INSTALL.md` — install steps for agents and humans
- `references/` — worker prefix, control contract, summary schemas
- `scripts/partition_write_tasks.py` — exclusive write-batch partitioner
- `adapters/claude/` — Claude Code skill + Workflow script
- `adapters/codex/` — Codex skill
- `examples/` — sample board and digest

## License

MIT. See `LICENSE`.
