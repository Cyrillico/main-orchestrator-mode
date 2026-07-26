#!/usr/bin/env python3
"""Regression tests for scripts/audit_write_grant.py.

Usage: python3 tests/test_audit_write_grant.py [path-to-scripts-dir]
       (defaults to scripts/ in this repo)

Covers the case that made git mode useless before 0.1.5: a worker that COMMITS its
out-of-grant edits leaves a clean working tree, so a porcelain-only audit passed.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else REPO / "scripts"
AUDIT = SCRIPTS / "audit_write_grant.py"

failures = 0


def check(name: str, cond: bool, detail: object = None) -> None:
    global failures
    print(f"{'PASS' if cond else 'FAIL'}  {name}")
    if not cond:
        failures += 1
        if detail is not None:
            print("        ", detail)


def run_audit(payload: dict) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(AUDIT)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )
    try:
        out = json.loads(proc.stdout)
    except json.JSONDecodeError:
        out = {"_stdout": proc.stdout, "_stderr": proc.stderr}
    return proc.returncode, out


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def make_repo(tmp: Path) -> Path:
    git(tmp, "init", "-q", ".")
    git(tmp, "config", "user.email", "t@t")
    git(tmp, "config", "user.name", "t")
    (tmp / "src").mkdir()
    (tmp / "src/a.ts").write_text("a\n")
    (tmp / "src/c.ts").write_text("c\n")
    git(tmp, "add", "-A")
    git(tmp, "commit", "-qm", "init")
    return tmp


# ---- explicit changed list ----
code, out = run_audit({"granted": ["src/a.ts"], "changed": ["src/a.ts", "src/c.ts"]})
check("out-of-grant exits 1", code == 1, code)
check("out-of-grant names the path", out.get("out_of_grant") == ["src/c.ts"], out)

code, out = run_audit({"granted": ["src/a.ts", "./src/b.ts"], "changed": ["src/a.ts"]})
check("in-grant exits 0", code == 0, code)
check("leading ./ normalized in grant", out.get("granted") == ["src/a.ts", "src/b.ts"], out)

code, out = run_audit({"granted": ["src/a.ts"], "changed": ["src/A.ts"]})
check("grant match is case-insensitive", code == 0, out)

code, out = run_audit({"granted": ["/etc/passwd"], "changed": ["src/a.ts"]})
check("absolute grant path exits 2", code == 2, code)

code, out = run_audit({"granted": [], "changed": ["src/a.ts"]})
check("empty grant with changes fails closed", code == 1, out)

# ---- git mode ----
with tempfile.TemporaryDirectory() as td:
    repo = make_repo(Path(td))
    base = git(repo, "rev-parse", "HEAD")

    # worker COMMITS an out-of-grant edit: working tree ends up clean
    (repo / "src/c.ts").write_text("tampered\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "worker commits out-of-grant edit")
    check("tree is clean after the commit", git(repo, "status", "--porcelain") == "")

    code, out = run_audit(
        {"granted": ["src/a.ts"], "git": True, "repo": str(repo), "base": base}
    )
    check("committed out-of-grant edit is caught", code == 1, out)
    check("committed path reported", out.get("out_of_grant") == ["src/c.ts"], out)

    code, out = run_audit({"granted": ["src/a.ts"], "git": True, "repo": str(repo)})
    check("git mode without base fails closed (exit 2)", code == 2, out)

    head = git(repo, "rev-parse", "HEAD")
    (repo / "src/c.ts").write_text("uncommitted\n")
    code, out = run_audit(
        {"granted": ["src/a.ts"], "git": True, "repo": str(repo), "base": head}
    )
    check("uncommitted out-of-grant edit still caught", code == 1, out)

    git(repo, "checkout", "-q", "--", "src/c.ts")
    (repo / "src/a.ts").write_text("edited in grant\n")
    code, out = run_audit(
        {"granted": ["src/a.ts"], "git": True, "repo": str(repo), "base": head}
    )
    check("in-grant edit passes", code == 0, out)

    code, out = run_audit(
        {"granted": ["src/a.ts"], "git": True, "repo": str(repo), "base": "nope"}
    )
    check("bad base ref errors (exit 2)", code == 2, out)

# ---- no bytecode artifacts in the skill tree ----
# The script imports a sibling module; without sys.dont_write_bytecode that drops a
# __pycache__/ into the installed skill dir, which INSTALL.md forbids.
# Clear first: earlier runs in this file would otherwise make the check vacuous.
# (__pycache__ is a build artifact, safe to drop.)
cache = SCRIPTS / "__pycache__"
shutil.rmtree(cache, ignore_errors=True)
run_audit({"granted": ["src/a.ts"], "changed": ["src/a.ts"]})
check(
    "running the audit leaves no __pycache__ beside it",
    not cache.exists(),
    f"created {cache}",
)

print(f"\n{failures} FAILURE(S)" if failures else "\nall green")
raise SystemExit(1 if failures else 0)
