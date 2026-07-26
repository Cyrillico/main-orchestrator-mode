#!/usr/bin/env python3
"""Path strip/normalize regressions for scripts/orch_paths.py."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.dont_write_bytecode = True

from orch_paths import PathError, normalize_path  # noqa: E402

failures = 0

def check(name: str, cond: bool, detail=None) -> None:
    global failures
    print(f"{'PASS' if cond else 'FAIL'}  {name}")
    if not cond:
        failures += 1
        if detail is not None:
            print("       ", detail)

check(
    "relative unchanged",
    normalize_path("docs/plans/x.md") == "docs/plans/x.md",
)
check(
    "heuristic strip volumes path",
    normalize_path("/Volumes/cc/Relocated/cyril-20260416/Noodlize/docs/plans/x.md")
    == "docs/plans/x.md",
)
check(
    "repo_root strip unusual layout",
    normalize_path("/work/myrepo/pkg/util/a.go", repo_root="/work/myrepo")
    == "pkg/util/a.go",
)
try:
    normalize_path("/etc/shadow")
    check("outside-repo abs rejected", False)
except PathError:
    check("outside-repo abs rejected", True)

try:
    normalize_path("../secret")
    check("parent segment rejected", False)
except PathError:
    check("parent segment rejected", True)

print(f"\n{failures} FAILURE(S)" if failures else "\nall green")
raise SystemExit(1 if failures else 0)
