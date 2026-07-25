# Directory scheme (packaging plan)

Public package layout for Main Orchestrator Mode.

## Canonical tree

```text
main-orchestrator-mode/
├── README.md
├── LICENSE
├── STRUCTURE.md
├── prompts/
│   └── install-and-use.md
├── SKILL.md
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

## Source mapping (local → public)

| Local source | Public destination |
|--------------|--------------------|
| Claude skill `SKILL.md` | `adapters/claude/SKILL.md` (path-cleaned) |
| Claude `workflows/main-orchestrator-mode.js` | `adapters/claude/workflows/main-orchestrator-mode.js` |
| Claude/Codex `references/*` | merged into `references/*` |
| Codex skill `SKILL.md` | `adapters/codex/SKILL.md` (path-cleaned) |
| Codex `scripts/partition_write_tasks.py` | `scripts/partition_write_tasks.py` |
| best of both contracts | root `SKILL.md` + `references/orchestrator-contract.md` |

## Layering rules

1. **Root contract is host-neutral**
2. **Adapters may mention host tools** (`Workflow`, Codex multi-agent wait, etc.)
3. **Scripts must run with plain Python 3** and no host APIs
4. **Examples contain only fake paths** (`src/a.ts`), never personal machine paths
5. **No `.orch/` run artifacts** in git

## v0.1 release checklist

- [x] Root `SKILL.md` written
- [x] `references/` merged and de-personalized
- [x] Claude adapter path-cleaned
- [x] Codex adapter path-cleaned
- [x] `partition_write_tasks.py` copied + smoke-tested
- [x] examples added
- [x] script smoke + personal-path scan clean
- [x] docs/scripts ready for `INSTALL.md` install flow
- [ ] live host install dry-run (Claude + Codex skill dirs)
- [x] GitHub public repo created and pushed

## Out of scope for v0.1

- npm/pypi packaging
- auto-updater
- GUI installer
- non-Claude/non-Codex hosts (can be future adapters)
