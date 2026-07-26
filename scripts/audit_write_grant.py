#!/usr/bin/env python3
"""Audit whether changed paths stay inside granted write_files.

Input JSON on stdin or file arg:
{
  "granted": ["src/a.ts", "./src/b.ts"],
  "changed": ["src/a.ts", "src/c.ts"]   # optional explicit list
}

Or ask the tool to read changes from git. `base` is REQUIRED in git mode: record
it with `git rev-parse HEAD` before the write batch starts. Without a baseline a
worker that commits its edits leaves a clean tree and would audit as ok.
{
  "granted": ["src/a.ts"],
  "git": true,
  "repo": ".",
  "base": "<pre-batch SHA>"
}

Git mode unions two sources so neither uncommitted nor committed edits hide:
  - `git status --porcelain -uall`  (working tree + index + untracked)
  - `git diff --name-only <base>..HEAD`  (commits made during the batch)

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
  2 = usage / path / git error (includes git mode without `base`)
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from orch_paths import PathError, normalize_path, normalize_paths  # noqa: E402


def _git(repo: str, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", repo, *args],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git {args[0]} failed")
    return proc.stdout


def git_status_changed(repo: str) -> list[str]:
    changed: list[str] = []
    for line in _git(repo, "status", "--porcelain", "-uall").splitlines():
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


def git_committed_changed(repo: str, base: str) -> list[str]:
    """Paths touched by commits between base and HEAD (renames yield both sides)."""
    out = _git(repo, "diff", "--name-only", "-z", f"{base}..HEAD")
    return [p for p in out.split("\0") if p]


def git_changed(repo: str, base: str) -> list[str]:
    """Union of uncommitted and committed changes, order-stable and deduped."""
    seen: set[str] = set()
    changed: list[str] = []
    for p in git_status_changed(repo) + git_committed_changed(repo, base):
        if p not in seen:
            seen.add(p)
            changed.append(p)
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
        base = str(payload.get("base") or "").strip()
        if not base:
            # Fail closed: a clean tree is ambiguous (nothing written vs all committed).
            return {
                "ok": False,
                "granted": granted,
                "changed": [],
                "out_of_grant": [],
                "errors": [
                    "git: base required (record `git rev-parse HEAD` before the batch); "
                    "without it committed edits are invisible"
                ],
            }
        try:
            changed_raw = git_changed(repo, base)
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

    # case-insensitive membership for grant checks
    granted_set = {p.lower() for p in granted}
    out_of_grant = [p for p in changed if p.lower() not in granted_set]

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
