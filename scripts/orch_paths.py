"""Shared path normalization for orch scripts."""

from __future__ import annotations


class PathError(ValueError):
    pass


def normalize_path(p: str) -> str:
    s = str(p or "").replace("\\", "/").strip()
    if not s:
        raise PathError("empty path")
    if s.startswith("~") or s.startswith("/"):
        raise PathError(f"absolute/home path not allowed: {p!r}")
    if len(s) >= 2 and s[1] == ":":
        raise PathError(f"absolute path not allowed: {p!r}")
    if s.startswith("//"):
        raise PathError(f"unc path not allowed: {p!r}")
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


def normalize_paths(paths) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for p in paths or []:
        n = normalize_path(p)
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out
