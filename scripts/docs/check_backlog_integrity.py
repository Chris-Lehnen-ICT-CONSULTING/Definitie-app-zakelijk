#!/usr/bin/env python3
"""Backlog integrity checks

Checks:
- Global uniqueness of US IDs (frontmatter: id: US-XXX)
- Global uniqueness of BUG IDs (id: BUG-XXX or CFR-BUG-XXX)
- Broken local links in Markdown (repo-relative or relative paths)

Exit code 1 on violations.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
ID_RE = re.compile(r"^id:\s*([A-Za-z0-9\-]+)\s*$", re.M)
CANONICAL_RE = re.compile(r"^canonical:\s*(true|false)\s*$", re.M | re.IGNORECASE)
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def iter_markdown_files(base: Path) -> Iterable[Path]:
    for p in base.rglob("*.md"):
        # Skip generated portal
        if p.is_file() and "docs/portal/" in str(p.as_posix()):
            continue
        yield p


def parse_frontmatter(text: str) -> tuple[str | None, bool]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, False
    fm = m.group(1)
    mi = ID_RE.search(fm)
    mc = CANONICAL_RE.search(fm)
    canonical = False
    if mc:
        canonical = mc.group(1).lower() == "true"
    return (mi.group(1).strip() if mi else None), canonical


def is_external_link(href: str) -> bool:
    return (
        href.startswith("http://")
        or href.startswith("https://")
        or href.startswith("mailto:")
    )


def resolve_link(md_path: Path, href: str) -> Path:
    # Normalize anchors and query
    href_clean = href.split("#", 1)[0].split("?", 1)[0]
    if not href_clean:
        return md_path
    p = Path(href_clean)
    if p.is_absolute():
        # Absolute likely repo-absolute (starts with /Users.. in local), consider not supported
        return ROOT / href_clean.lstrip("/")
    # Relative to document location
    return (md_path.parent / p).resolve()


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    # Collect IDs
    us_ids: dict[str, list[str]] = {}
    bug_ids: dict[str, list[str]] = {}

    for md in iter_markdown_files(DOCS):
        try:
            text = md.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:  # pragma: no cover - file read error shouldn't crash
            warnings.append(f"WARN: cannot read {md}: {e}")
            continue
        fid, canonical = parse_frontmatter(text)
        fid = fid or ""
        if fid.startswith("US-"):
            us_ids.setdefault(fid, []).append(str(md.relative_to(ROOT)))
        elif fid.startswith("BUG-") or fid.startswith("CFR-BUG-"):
            bug_ids.setdefault(fid, []).append(str(md.relative_to(ROOT)))

        # Link checks (only repo/local links)
        for m in MD_LINK_RE.finditer(text):
            href = m.group(1).strip().strip("\"'")
            if is_external_link(href):
                continue
            target = resolve_link(md, href)
            # Only check links inside repo docs or markdown/html
            if target.suffix.lower() not in {".md", ".html"}:
                continue
            if not target.exists():
                rel = str(md.relative_to(ROOT))
                # Fail only if canonical doc and not in archief; otherwise warn
                in_archief = "/docs/archief/" in ("/" + rel)
                if canonical and not in_archief:
                    errors.append(f"BROKEN LINK: {rel} -> {href}")
                else:
                    warnings.append(f"WARN BROKEN LINK: {rel} -> {href}")

    # Uniqueness checks
    dup_us = {k: v for k, v in us_ids.items() if len(v) > 1}
    dup_bug = {k: v for k, v in bug_ids.items() if len(v) > 1}

    for k, paths in dup_us.items():
        errors.append(f"DUPLICATE US ID: {k} used in: {', '.join(paths)}")
    for k, paths in dup_bug.items():
        errors.append(f"DUPLICATE BUG ID: {k} used in: {', '.join(paths)}")

    if warnings:
        for w in warnings:
            print(w)

    if errors:
        print("\nErrors found (backlog integrity):")
        for e in errors:
            print(e)
        return 1

    print("Backlog integrity OK: no duplicate IDs and no broken links.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
