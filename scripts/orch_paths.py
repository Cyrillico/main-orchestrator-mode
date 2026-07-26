"""Shared path normalization for orch scripts.

Granted paths must end up repo-relative. Absolute paths that clearly live under
the repo (or under a known repo top-level like docs/src/worker) are stripped
instead of hard-rejected, so planner abs-path habits do not empty a whole run.
Paths outside the repo (e.g. /etc/passwd) still fail closed.
"""

from __future__ import annotations

import os
import re
from typing import Iterable, Optional

class PathError(ValueError):
    pass


# Last match wins so /Volumes/.../Noodlize/docs/x → docs/x.
_REPO_TOP_RE = re.compile(
    r"/(docs|src|worker|web|App|Core|Features|scripts|tests|packages|apps|"
    r"lib|internal|cmd|adapters|references|workflows|ios|android|public|"
    r"config|tools|examples|Resources|Sources)(/.*)?$",
    re.IGNORECASE,
)


def _clean(p: str) -> str:
    return str(p or "").replace("\\", "/").strip()


def _is_abs(s: str) -> bool:
    if not s:
        return False
    if s.startswith("/") or s.startswith("~"):
        return True
    if len(s) >= 2 and s[1] == ":":
        return True
    if s.startswith("//"):
        return True
    return False


def _strip_root_prefix(s: str, root: str) -> Optional[str]:
    r = _clean(root).rstrip("/")
    if not r:
        return None
    # Windows drive normalize
    if len(r) >= 2 and r[1] == ":":
        r = r[0].upper() + r[1:]
        if len(s) >= 2 and s[1] == ":":
            s = s[0].upper() + s[1:]
    if s == r:
        return ""
    if s.startswith(r + "/"):
        return s[len(r) + 1 :]
    return None


def _candidate_roots(repo_root: Optional[str] = None) -> list[str]:
    roots: list[str] = []
    for raw in (
        repo_root,
        os.environ.get("ORCH_REPO_ROOT"),
        os.environ.get("PWD"),
    ):
        if not raw:
            continue
        c = _clean(raw)
        if c and c not in roots:
            roots.append(c)
        try:
            real = _clean(os.path.realpath(raw))
            if real and real not in roots:
                roots.append(real)
        except OSError:
            pass
    try:
        cwd = _clean(os.getcwd())
        if cwd and cwd not in roots:
            roots.append(cwd)
        real = _clean(os.path.realpath(cwd))
        if real and real not in roots:
            roots.append(real)
    except OSError:
        pass
    return roots


def relativize_path(p: str, repo_root: Optional[str] = None) -> str:
    """Turn a granted path into a candidate repo-relative string (may still be invalid)."""
    s = _clean(p)
    if not s:
        return s
    if s.startswith("file://"):
        s = s[7:]
        if s.startswith("//"):  # file://host/path
            # drop host
            parts = s[2:].split("/", 1)
            s = "/" + parts[1] if len(parts) > 1 else ""
        elif not s.startswith("/"):
            s = "/" + s

    if s.startswith("~/"):
        # Cannot expand home portably without guessing; drop ~user prefix and hope remainder is relative.
        s = s[2:]
    elif s.startswith("~"):
        # ~ alone or ~user
        if "/" in s:
            s = s.split("/", 1)[1]
        else:
            raise PathError(f"home path not allowed: {p!r}")

    if _is_abs(s) or (len(s) >= 2 and s[1] == ":"):
        for root in _candidate_roots(repo_root):
            stripped = _strip_root_prefix(s, root)
            if stripped is not None:
                s = stripped
                break

    if _is_abs(s) or (len(s) >= 2 and s[1] == ":"):
        matches = list(_REPO_TOP_RE.finditer(s))
        if matches:
            s = matches[-1].group(0).lstrip("/")
        else:
            raise PathError(f"absolute/home path not allowed: {p!r}")

    return s


def normalize_path(p: str, repo_root: Optional[str] = None) -> str:
    s = relativize_path(p, repo_root=repo_root)
    if not s:
        raise PathError("empty path")
    if s.startswith("~") or s.startswith("/"):
        raise PathError(f"absolute/home path not allowed: {p!r}")
    if len(s) >= 2 and s[1] == ":":
        raise PathError(f"absolute path not allowed: {p!r}")
    if s.startswith("//"):
        raise PathError(f"unc path not allowed: {p!r}")
    if "://" in s:
        raise PathError(f"scheme path not allowed: {p!r}")
    while s.startswith("./"):
        s = s[2:]
    parts: list[str] = []
    for part in s.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            raise PathError(f"parent path segment not allowed: {p!r}")
        parts.append(part)
    if not parts:
        raise PathError(f"invalid path: {p!r}")
    return "/".join(parts)


def lock_key(p: str, repo_root: Optional[str] = None) -> str:
    """Case-insensitive lock identity for APFS/Windows-safe exclusivity."""
    return normalize_path(p, repo_root=repo_root).lower()


def normalize_paths(paths: Iterable, repo_root: Optional[str] = None) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for p in paths or []:
        n = normalize_path(p, repo_root=repo_root)
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out
