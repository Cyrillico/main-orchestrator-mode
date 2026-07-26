#!/usr/bin/env python3
"""Regression tests for scripts/accept_with_audit.py."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "scripts")
GATE = SCRIPTS / "accept_with_audit.py"
failures = 0


def check(name: str, cond: bool, detail=None) -> None:
    global failures
    if cond:
        print(f"ok  - {name}")
    else:
        failures += 1
        print(f"FAIL- {name}: {detail!r}")


def run_gate(payload: dict) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(GATE)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
    )
    try:
        out = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        out = {"_raw": proc.stdout, "_err": proc.stderr}
    return proc.returncode, out


code, out = run_gate({})
check("missing scheduler_accepted → exit 2", code == 2, out)

code, out = run_gate({"scheduler_accepted": True})
check("no grants, scheduler true → accepted", code == 0 and out.get("accepted") is True, out)

code, out = run_gate({"scheduler_accepted": False})
check("no grants, scheduler false → reject", code == 1 and out.get("accepted") is False, out)

code, out = run_gate(
    {"scheduler_accepted": True, "granted": ["src/a.ts"], "changed": ["src/a.ts"]}
)
check("in-grant explicit changed accepts", code == 0 and out.get("accepted") is True, out)

code, out = run_gate(
    {"scheduler_accepted": True, "granted": ["src/a.ts"], "changed": ["src/b.ts"]}
)
check("out-of-grant rejects", code == 1 and out.get("accepted") is False, out)

code, out = run_gate(
    {"scheduler_accepted": False, "granted": ["src/a.ts"], "changed": ["src/a.ts"]}
)
check("scheduler false rejects even if audit ok", code == 1 and out.get("accepted") is False, out)

code, out = run_gate({"scheduler_accepted": True, "granted": ["src/a.ts"], "git": True})
check("git mode without base fails closed (exit 2)", code == 2, out)

# no bytecode in skill tree
cache = SCRIPTS / "__pycache__"
shutil.rmtree(cache, ignore_errors=True)
run_gate({"scheduler_accepted": True, "granted": ["src/a.ts"], "changed": ["src/a.ts"]})
check("gate leaves no __pycache__", not cache.exists(), cache)

print(f"\n{failures} FAILURE(S)" if failures else "\nall green")
raise SystemExit(1 if failures else 0)
