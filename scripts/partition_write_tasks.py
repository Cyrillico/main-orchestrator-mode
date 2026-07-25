#!/usr/bin/env python3
"""Partition write tasks into conflict-free batches (exclusive per-file writers).

Input: JSON array on stdin or as file arg:
  [{"id":"w1","write_files":["a.ts"]}, ...]

Output: JSON array of batches:
  [[{"id":"w1","write_files":["a.ts"]}], ...]
"""

from __future__ import annotations

import json
import sys
from typing import Any


def normalize_path(p: str) -> str:
    return str(p or "").replace("\\", "/").lstrip("./")


def partition(tasks: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    remaining: list[dict[str, Any]] = []
    for t in tasks:
        item = dict(t)
        item["write_files"] = [normalize_path(p) for p in (t.get("write_files") or [])]
        remaining.append(item)

    batches: list[list[dict[str, Any]]] = []
    while remaining:
        batch: list[dict[str, Any]] = []
        locked: set[str] = set()
        i = 0
        while i < len(remaining):
            t = remaining[i]
            files = t.get("write_files") or []
            conflict = any(f in locked for f in files)
            if not conflict:
                for f in files:
                    locked.add(f)
                batch.append(t)
                remaining.pop(i)
            else:
                i += 1
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
    data = json.loads(raw or "[]")
    if not isinstance(data, list):
        print("expected JSON array of tasks", file=sys.stderr)
        return 2
    print(json.dumps(partition(data), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
