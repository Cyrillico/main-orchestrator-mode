#!/usr/bin/env python3
"""Application-safety accept gate: scheduler success + disk grant audit.

Parent/adapters must not report a run as clean until this (or equivalent) passes
when write grants were used.

Input JSON (stdin or file arg):
{
  "scheduler_accepted": true,
  "granted": ["src/a.ts"],
  "base": "<pre-batch SHA>",   # required in git mode when audit runs via git
  "git": true,                 # default true when "changed" is omitted
  "repo": ".",
  "changed": ["src/a.ts"]      # optional explicit list; skips git discovery
}

Rules:
- scheduler_accepted false ⇒ accepted false
- granted non-empty (or explicit changed) ⇒ disk audit required
- granted empty and no changed ⇒ accepted mirrors scheduler_accepted
- accepted = scheduler_accepted AND audit.ok (when audit ran)

Exit codes:
  0 = accepted
  1 = not accepted (scheduler false or out-of-grant)
  2 = usage / path / git error
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_write_grant import audit  # noqa: E402


def gate(payload: dict[str, Any]) -> tuple[dict[str, Any], int]:
    if "scheduler_accepted" not in payload:
        out = {
            "ok": False,
            "accepted": False,
            "scheduler_accepted": False,
            "audit": None,
            "errors": ["scheduler_accepted is required"],
        }
        return out, 2

    scheduler_accepted = bool(payload.get("scheduler_accepted"))
    granted = payload.get("granted") or []
    if not isinstance(granted, list):
        out = {
            "ok": False,
            "accepted": False,
            "scheduler_accepted": scheduler_accepted,
            "audit": None,
            "errors": ["granted must be a list"],
        }
        return out, 2

    changed = payload.get("changed")

    # No write grants and no explicit changed list: nothing to audit on disk.
    if not granted and changed is None:
        out = {
            "ok": scheduler_accepted,
            "accepted": scheduler_accepted,
            "scheduler_accepted": scheduler_accepted,
            "audit": None,
            "errors": [] if scheduler_accepted else ["scheduler_accepted is false"],
        }
        return out, (0 if scheduler_accepted else 1)

    audit_payload: dict[str, Any] = {"granted": granted}
    if changed is not None:
        audit_payload["changed"] = changed
    else:
        audit_payload["git"] = True if payload.get("git", True) else False
        if audit_payload["git"]:
            audit_payload["repo"] = payload.get("repo") or "."
            if "base" in payload:
                audit_payload["base"] = payload.get("base")
        else:
            audit_payload["changed"] = []

    result = audit(audit_payload)
    errors = list(result.get("errors") or [])
    if not scheduler_accepted:
        errors = ["scheduler_accepted is false", *errors]

    accepted = scheduler_accepted and bool(result.get("ok"))
    out = {
        "ok": accepted,
        "accepted": accepted,
        "scheduler_accepted": scheduler_accepted,
        "audit": result,
        "errors": errors,
    }

    # Mirror audit_write_grant: pure git/path input errors → 2
    if result.get("errors") and not result.get("changed") and not result.get("out_of_grant"):
        if any(
            str(e).startswith("git:") or "not allowed" in str(e) for e in result["errors"]
        ):
            return out, 2
    return out, (0 if accepted else 1)


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

    result, code = gate(payload)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
