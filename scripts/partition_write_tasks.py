#!/usr/bin/env python3
"""Partition write tasks into conflict-free batches (exclusive per-file writers).

Input: JSON array on stdin or as file arg:
  [{"id":"w1","write_files":["a.ts"]}, ...]

Output: JSON array of batches:
  [[{"id":"w1","write_files":["a.ts"]}], ...]

Rules:
- Paths must be repo-relative (no abs, no ~, no ..).
- Empty/missing write_files => task runs alone (serial defensive).
- Normalization is strict and shared with the Claude workflow adapter.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Importing a sibling module would drop __pycache__/ into the installed skill tree,
# which INSTALL.md forbids (it pollutes skill discovery).
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from orch_paths import PathError, lock_key, normalize_path  # noqa: E402


def normalize_task(t: dict[str, Any]) -> dict[str, Any]:
    item = dict(t)
    raw_files = t.get("write_files") or []
    if not isinstance(raw_files, list):
        raise PathError(f"write_files must be a list for task {t.get('id')!r}")
    item["write_files"] = [normalize_path(p) for p in raw_files]
    return item


def partition(tasks: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    remaining: list[dict[str, Any]] = [normalize_task(t) for t in tasks]
    batches: list[list[dict[str, Any]]] = []

    while remaining:
        empty_idx = next((i for i, t in enumerate(remaining) if not t.get("write_files")), None)
        if empty_idx is not None:
            batches.append([remaining.pop(empty_idx)])
            continue

        batch: list[dict[str, Any]] = []
        locked: set[str] = set()
        i = 0
        while i < len(remaining):
            t = remaining[i]
            files = t.get("write_files") or []
            keys = [lock_key(f) for f in files]
            if any(k in locked for k in keys):
                i += 1
                continue
            for k in keys:
                locked.add(k)
            batch.append(t)
            remaining.pop(i)
        if not batch and remaining:
            batch.append(remaining.pop(0))
        batches.append(batch)
    return batches


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] not in ("-", "--"):
        with open(sys.argv[1], encoding="utf-8") as f:
            raw = f.read()
    else:
        raw = sys.stdin.read()
    try:
        data = json.loads(raw or "[]")
    except json.JSONDecodeError as e:
        print(f"invalid JSON: {e}", file=sys.stderr)
        return 2
    if not isinstance(data, list):
        print("expected JSON array of tasks", file=sys.stderr)
        return 2
    try:
        out = partition(data)
    except PathError as e:
        print(str(e), file=sys.stderr)
        return 2
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
