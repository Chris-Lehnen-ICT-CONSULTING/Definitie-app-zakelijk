#!/usr/bin/env python3
"""
Pre-commit hook: Check internal Markdown links resolve.
Scans changed Markdown files and verifies relative links refer to existing files.
Skips external (http/https/mailto) links and archived docs.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def is_external(link: str) -> bool:
    return link.startswith(("http://", "https://", "mailto:"))


def check_file(md_path: Path) -> list[str]:
    errors: list[str] = []
    try:
        text = md_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:  # pragma: no cover - defensive
        return [f"Cannot read {md_path}: {e!s}"]

    for match in LINK_RE.finditer(text):
        target = match.group(1).strip()
        if not target or is_external(target):
            continue
        # Ignore anchors and references
        if target.startswith("#"):
            continue
        # Normalize
        # Support absolute-from-repo links: treat as relative to repo root
        # Resolve target path
        if target.startswith("/"):
            # Treat repo-absolute links (/docs/...) as relative to repo root
            target_path = (Path.cwd() / target.lstrip("/\\")).resolve()
        else:
            target_path = (md_path.parent / target).resolve()

        # Skip archived/review targets (case-insensitive)
        lower_path = str(target_path).lower()
        if (
            "/archief/" in lower_path
            or "/archive/" in lower_path
            or "/reviews/" in lower_path
        ):
            continue
        if not target_path.exists():
            errors.append(f"Broken link in {md_path}: {target}")

    return errors


def main() -> int:
    files = [Path(p) for p in sys.argv[1:] if p.endswith(".md")]
    errors: list[str] = []
    for f in files:
        # Limit to docs only
        p = str(f)
        if not p.startswith("docs/"):
            continue
        # Skip archived/review docs (case-insensitive)
        pl = p.lower()
        if "/archief/" in pl or "/archive/" in pl or "/reviews/" in pl:
            continue
        errors.extend(check_file(f))

    if errors:
        print("❌ Broken internal links found:\n")
        for e in errors:
            print(f"  - {e}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
