#!/usr/bin/env python3
"""
Normalize and fix broken documentation links to the canonical backlog structure.

Rules implemented:
- stories → canonical
  - docs/backlog/stories/US-XXX.md → docs/backlog/EPIC-YYY/US-XXX/US-XXX.md (lookup)
- epics → canonical
  - docs/backlog/epics/EPIC-XXX*.md → docs/backlog/EPIC-XXX/EPIC-XXX.md
- requirements spelling/paths → canonical
  - vereistes|vereisten|requirements/REQ-XXX.md → docs/backlog/requirements/REQ-XXX.md
- leading slash → relative
  - /docs/... → docs/...
- Missing US file under EPIC-012 references → keep plain text (remove link)

The script attempts safe in-place modifications for .md and .html under docs/.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"

MD_LINK = re.compile(r"\[(?P<text>[^\]]+)\]\((?P<href>[^)]+)\)")
HTML_HREF = re.compile(r"href=\"(?P<href>[^\"]+)\"")

US_ID = re.compile(r"US-(\d{3})\b")
EPIC_ID = re.compile(r"EPIC-(\d{3})\b")
REQ_ID = re.compile(r"REQ-(\d{3})\b")


def build_us_lookup() -> dict[str, Path]:
    lookup: dict[str, Path] = {}
    for p in DOCS.glob("backlog/EPIC-*/US-*/US-*.md"):
        m = US_ID.search(p.name)
        if m:
            lookup[m.group(0)] = p
    return lookup


def canonical_epic_path(epic_id: str) -> Path:
    return DOCS / "backlog" / epic_id / f"{epic_id}.md"


def canonical_req_path(req_id: str) -> Path:
    return DOCS / "backlog" / "requirements" / f"{req_id}.md"


def normalize_href(href: str) -> str:
    # strip anchors/queries for existence checks
    core = href.split('#', 1)[0].split('?', 1)[0]
    return core


def replace_in_text(text: str, base: Path, us_lookup: dict[str, Path]) -> str:
    def replace_md(m: re.Match) -> str:
        label = m.group('text')
        href = m.group('href')
        new_href = fix_href(href, base, us_lookup)
        if new_href is None:
            # leave original
            return m.group(0)
        if new_href == "__REMOVE_LINK_KEEP_TEXT__":
            return label
        return f"[{label}]({new_href})"

    def replace_html(m: re.Match) -> str:
        href = m.group('href')
        new_href = fix_href(href, base, us_lookup)
        if new_href is None:
            return m.group(0)
        if new_href == "__REMOVE_LINK_KEEP_TEXT__":
            # cannot drop href attribute cleanly; keep original
            return m.group(0)
        return f"href=\"{new_href}\""

    text = MD_LINK.sub(replace_md, text)
    text = HTML_HREF.sub(replace_html, text)
    return text


def rel_from(to_path: Path, base: Path) -> str:
    try:
        return to_path.relative_to(base).as_posix()
    except Exception:
        return to_path.as_posix()


def fix_href(href: str, base: Path, us_lookup: dict[str, Path]) -> str | None:
    if href.startswith(("http://", "https://", "mailto:", "#")):
        return None
    h = href
    # Drop leading slash for repo-root links
    if h.startswith("/docs/"):
        h = h[1:]

    core = normalize_href(h)

    # Map stories old path → canonical by ID
    if "/backlog/stories/US-" in core:
        m = US_ID.search(core)
        if m and m.group(0) in us_lookup:
            target = us_lookup[m.group(0)]
            return rel_from(target, base)

    # Map epics old path → canonical EPIC-XXX/EPIC-XXX.md
    if "/backlog/epics/" in core:
        m = EPIC_ID.search(core)
        if m:
            target = canonical_epic_path(m.group(0))
            return rel_from(target, base)

    # Map requirements misspellings → canonical requirements path
    if any(seg in core for seg in ("/vereistes/", "/vereisten/", "/requirements/")) and "REQ-" in core:
        m = REQ_ID.search(core)
        if m:
            target = canonical_req_path(m.group(0))
            return rel_from(target, base)

    # Keep docs/... absolute (repo-root) intact
    if core.startswith("docs/"):
        # if target doesn't exist, try EPIC/US mapping by IDs
        p = ROOT / core
        if p.exists():
            return h.lstrip('/')
        # try ID-based mapping fallback
        m = US_ID.search(core)
        if m and m.group(0) in us_lookup:
            return rel_from(us_lookup[m.group(0)], base)
        m2 = EPIC_ID.search(core)
        if m2:
            return rel_from(canonical_epic_path(m2.group(0)), base)

    # If the link points to a non-existing EPIC-012 US file, drop link but keep text
    # Example: ./US-065/US-065.md under EPIC-012 that doesn't exist yet
    if ("EPIC-012" in str(base)) and US_ID.search(core):
        return "__REMOVE_LINK_KEEP_TEXT__"

    # If nothing matched but it started with /docs, return without leading slash
    if href.startswith("/docs/"):
        return h

    return None


def main() -> int:
    us_lookup = build_us_lookup()
    changed = 0
    files = list(DOCS.rglob("*.md")) + list(DOCS.rglob("*.html"))
    for f in files:
        try:
            s = f.read_text(encoding="utf-8")
        except Exception:
            continue
        new = replace_in_text(s, f.parent, us_lookup)
        if new != s:
            f.write_text(new, encoding="utf-8")
            changed += 1
    print(f"Updated files: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

