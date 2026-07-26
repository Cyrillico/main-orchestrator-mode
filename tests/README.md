# Tests

Regression tests for the parts of `orch` that are code rather than prompt. Not
installed to any host — they run from a repo checkout.

```bash
node tests/workflow-scheduler.test.mjs      # Claude adapter scheduler
python3 tests/test_audit_write_grant.py     # write-grant audit
```

Both accept an optional path argument so an **installed** skill can be checked
instead of the repo copy:

```bash
node tests/workflow-scheduler.test.mjs ~/.claude/skills/orch/workflows/main-orchestrator-mode.js
python3 tests/test_audit_write_grant.py ~/.codex/skills/orch/scripts
```

No dependencies beyond Node and Python 3. Each exits non-zero on failure.

The scheduler test evaluates the shipped workflow script with stubbed `agent` /
`parallel` / `log` / `phase` globals rather than reimplementing its logic, so it
tests the file that actually ships.
