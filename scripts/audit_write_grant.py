#!/usr/bin/env python3
"""Audit whether changed paths stay inside granted write_files.

Input JSON on stdin or file arg:
{
  "granted": ["src/a.ts", "./src/b.ts"],
  "changed": ["src/a.ts", "src/c.ts"]   # optional explicit list
}

Or ask the tool to read git porcelain from cwd / repo:
{
  "granted": ["src/a.ts"],
  "git": true,
  "repo": "."
}

Output JSON:
{
  "ok": false,
  "granted": ["src/a.ts"],
  "changed": ["src/a.ts", "src/c.ts"],
  "out_of_grant": ["src/c.ts"],
  "errors": []
}

Exit codes:
  0 = ok (no out-of-grant)
  1 = out-of-grant or empty granted with changes
  2 = usage / path / git error
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from orch_paths import PathError, normalize_path, normalize_paths  # noqa: E402


def git_changed(repo: str) -> list[str]:
    proc = subprocess.run(
        ["git", "-C", repo, "status", "--porcelain", "-uall"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git status failed")
    changed: list[str] = []
    for line in proc.stdout.splitlines():
        if not line or len(line) < 4:
            continue
        # XY<space>path or rename "old -> new"
        path_part = line[3:]
        if " -> " in path_part:
            path_part = path_part.split(" -> ", 1)[1]
        path_part = path_part.strip().strip('"')
        if path_part:
            changed.append(path_part)
    return changed


def audit(payload: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    try:
        granted = normalize_paths(payload.get("granted") or [])
    except PathError as e:
        return {
            "ok": False,
            "granted": [],
            "changed": [],
            "out_of_grant": [],
            "errors": [str(e)],
        }

    changed_raw = payload.get("changed")
    if changed_raw is None and payload.get("git"):
        repo = str(payload.get("repo") or ".")
        try:
            changed_raw = git_changed(repo)
        except Exception as e:  # noqa: BLE001
            return {
                "ok": False,
                "granted": granted,
                "changed": [],
                "out_of_grant": [],
                "errors": [f"git: {e}"],
            }
    if changed_raw is None:
        changed_raw = []

    try:
        changed = normalize_paths(changed_raw)
    except PathError as e:
        return {
            "ok": False,
            "granted": granted,
            "changed": [],
            "out_of_grant": [],
            "errors": [str(e)],
        }

    granted_set = set(granted)
    out_of_grant = [p for p in changed if p not in granted_set]

    # empty grant with any change is fail-closed
    if not granted and changed:
        errors.append("empty granted write_files but changes present")
        out_of_grant = changed[:]

    ok = not out_of_grant and not errors
    return {
        "ok": ok,
        "granted": granted,
        "changed": changed,
        "out_of_grant": out_of_grant,
        "errors": errors,
    }


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] not in ("-", "--"):
        raw = Path(sys.argv[1]).read_text(encoding="utf-8")
    else:
        raw = sys.stdin.read()
    try:
        payload = json.loads(raw or "{}")
    except json.JSONDecodeError as e:
        print(f"invalid JSON: {e}", file=sys.stderr)
        return 2
    if not isinstance(payload, dict):
        print("expected JSON object", file=sys.stderr)
        return 2

    result = audit(payload)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("errors") and not result.get("changed") and not result.get("out_of_grant"):
        # pure input/git error
        if any(str(e).startswith("git:") or "not allowed" in str(e) for e in result["errors"]):
            return 2
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
