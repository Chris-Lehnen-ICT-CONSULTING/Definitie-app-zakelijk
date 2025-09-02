#!/usr/bin/env python3
"""
Pre-commit hook: Check doc frontmatter metadata for canonical active docs.
Warn if `last_verified` is older than 90 days; do not fail the commit.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path


def parse_frontmatter(path: Path) -> dict[str, str]:
    meta: dict[str, str] = {}
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return meta
    if not text.startswith("---\n"):
        return meta
    end = text.find("\n---\n", 4)
    if end == -1:
        return meta
    header = text[4:end]
    for line in header.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta


def main() -> int:
    files = [Path(p) for p in sys.argv[1:] if p.endswith(".md")]
    warnings: list[str] = []
    cutoff = datetime.utcnow() - timedelta(days=90)
    for f in files:
        p = str(f)
        if not p.startswith("docs/"):
            continue
        meta = parse_frontmatter(f)
        if meta.get("canonical", "false").lower() != "true":
            continue
        if meta.get("status", "").lower() != "active":
            continue
        lv = meta.get("last_verified")
        if not lv:
            warnings.append(f"{p}: missing last_verified")
            continue
        try:
            dt = datetime.strptime(lv, "%Y-%m-%d")
        except ValueError:
            warnings.append(f"{p}: invalid last_verified format '{lv}' (YYYY-MM-DD)")
            continue
        if dt < cutoff:
            warnings.append(f"{p}: last_verified {lv} older than 90 days")

    if warnings:
        print("⚠️  Doc metadata warnings:\n")
        for w in warnings:
            print(f"  - {w}")
        # Do not fail the commit for now
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

