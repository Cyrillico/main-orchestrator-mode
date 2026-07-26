# Directory scheme (packaging plan)

Public package layout for Main Orchestrator Mode.

## Canonical tree

```text
main-orchestrator-mode/
├── README.md
├── INSTALL.md
├── CHANGELOG.md
├── VERSION
├── LICENSE
├── STRUCTURE.md
├── .gitignore
├── prompts/
│   └── install-and-use.md
├── SKILL.md
├── references/
│   ├── README.md
│   ├── agent-prefix.md
│   ├── orchestrator-contract.md
│   └── summary-schema.md
├── scripts/
│   ├── README.md
│   ├── partition_write_tasks.py
│   ├── audit_write_grant.py
│   └── orch_paths.py
├── adapters/
│   ├── claude/
│   │   ├── README.md
│   │   ├── SKILL.md
│   │   └── workflows/
│   │       └── main-orchestrator-mode.js
│   └── codex/
│       ├── README.md
│       └── SKILL.md
├── examples/
│   ├── README.md
│   ├── sample-board.json
│   └── sample-digest.json
└── tests/
    ├── README.md
    ├── workflow-scheduler.test.mjs
    └── test_audit_write_grant.py
```

`tests/` is repo-only and never installed to a host. Both suites take an optional
path argument so an installed skill can be tested in place.

## Install subsets (per host)

| Host | Gets |
|------|------|
| Claude Code | `adapters/claude/SKILL.md`, `references/{agent-prefix,orchestrator-contract,summary-schema}.md`, `adapters/claude/workflows/main-orchestrator-mode.js`, `scripts/{audit_write_grant,orch_paths}.py` |
| Codex | `adapters/codex/SKILL.md`, same three `references/`, `scripts/{partition_write_tasks,orch_paths,audit_write_grant}.py` |

`partition_write_tasks.py` is Codex-only: the Claude scheduler partitions write
batches inside the workflow script. `audit_write_grant.py` ships to **both** —
`references/orchestrator-contract.md` names it as the write-grant audit layer, so
an install that omits it has no audit layer. `orch_paths.py` is a shared import of
both scripts and must travel with either one.

## Source mapping (local → public)

| Local source | Public destination |
|--------------|--------------------|
| Claude skill `SKILL.md` | `adapters/claude/SKILL.md` (path-cleaned) |
| Claude `workflows/main-orchestrator-mode.js` | `adapters/claude/workflows/main-orchestrator-mode.js` |
| Claude/Codex `references/*` | merged into `references/*` |
| Codex skill `SKILL.md` | `adapters/codex/SKILL.md` (path-cleaned) |
| Codex `scripts/partition_write_tasks.py` | `scripts/partition_write_tasks.py` |
| shared path normalize/reject | `scripts/orch_paths.py` (imported by both scripts) |
| post-batch write-grant audit | `scripts/audit_write_grant.py` (host-neutral, both installs) |
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
- [x] live host install (Claude + Codex skill dirs) run from `INSTALL.md`, audit + partition smoke green (v0.1.4)
- [x] GitHub public repo created and pushed

## Out of scope for v0.1

- npm/pypi packaging
- auto-updater
- GUI installer
- non-Claude/non-Codex hosts (can be future adapters)
