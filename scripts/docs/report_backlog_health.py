#!/usr/bin/env python3
"""Backlog Health Report

Generates a lightweight report about the docs backlog:
- Counts by type (EPIC, US, BUG, REQ, GUIDE, ARCH, DOC)
- Canonical vs non-canonical counts
- Duplicate US/BUG IDs
- Broken links (canonical only)

Outputs a JSON report (optional) and prints a summary.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
ID_RE = re.compile(r"^id:\s*([A-Za-z0-9\-]+)\s*$", re.M)
CANONICAL_RE = re.compile(r"^canonical:\s*(true|false)\s*$", re.M | re.IGNORECASE)
H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


def parse_frontmatter(text: str) -> dict[str, Any]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    block = m.group(1)
    data: dict[str, Any] = {}
    for line in block.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            data[k.strip()] = v.strip().strip("'\"")
    return data


def classify(path: Path) -> str:
    p = str(path).replace("\\", "/")
    if "/backlog/requirements/REQ-" in p:
        return "REQ"
    if "/backlog/EPIC-" in p and p.endswith("/EPIC-" + path.parent.name + ".md"):
        return "EPIC"
    if "/backlog/EPIC-" in p and "/US-" in p and path.name.startswith("US-"):
        return "US"
    if "/CFR-BUG-" in p or "/BUG-" in p:
        return "BUG"
    if "/architectuur/" in p:
        return "ARCH"
    if "/guidelines/" in p:
        return "GUIDE"
    return "DOC"


def first_heading(text: str) -> str | None:
    m = H1_RE.search(text)
    return m.group(1).strip() if m else None


def is_external_link(href: str) -> bool:
    return href.startswith(("http://", "https://", "mailto:"))


def resolve_link(md_path: Path, href: str) -> Path:
    href_clean = href.split("#", 1)[0].split("?", 1)[0]
    if not href_clean:
        return md_path
    p = Path(href_clean)
    if p.is_absolute():
        return ROOT / href_clean.lstrip("/")
    return (md_path.parent / p).resolve()


@dataclass
class Health:
    counts: dict[str, int]
    canonical_counts: dict[str, int]
    duplicate_us: dict[str, list[str]]
    duplicate_bug: dict[str, list[str]]
    broken_links: list[dict[str, str]]
    archived_broken_links: list[dict[str, str]]


def scan() -> Health:
    counts: dict[str, int] = {}
    canonical_counts: dict[str, int] = {}
    us_ids: dict[str, list[str]] = {}
    bug_ids: dict[str, list[str]] = {}
    broken_links: list[dict[str, str]] = []
    archived_broken_links: list[dict[str, str]] = []

    for md in DOCS.rglob("*.md"):
        # Skip generated portal
        if "docs/portal/" in str(md.as_posix()):
            continue
        try:
            text = md.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        fm = parse_frontmatter(text)
        doc_type = classify(md)
        counts[doc_type] = counts.get(doc_type, 0) + 1
        is_canonical = str(fm.get("canonical", "false")).lower() == "true"
        if is_canonical:
            canonical_counts[doc_type] = canonical_counts.get(doc_type, 0) + 1
        fid = str(fm.get("id") or "")
        if fid.startswith("US-"):
            us_ids.setdefault(fid, []).append(str(md.relative_to(ROOT)))
        if fid.startswith(("BUG-", "CFR-BUG-")):
            bug_ids.setdefault(fid, []).append(str(md.relative_to(ROOT)))

        # link scan
        in_archief = "docs/archief/" in str(md.as_posix())
        for m in re.finditer(r"\[[^\]]*\]\(([^)]+)\)", text):
            href = m.group(1).strip().strip("\"'")
            if is_external_link(href):
                continue
            target = resolve_link(md, href)
            if target.suffix.lower() not in {".md", ".html"}:
                continue
            if not target.exists():
                entry = {"source": str(md.relative_to(ROOT)), "href": href}
                if in_archief:
                    archived_broken_links.append(entry)
                elif is_canonical:
                    broken_links.append(entry)

    dup_us = {k: v for k, v in us_ids.items() if len(v) > 1}
    dup_bug = {k: v for k, v in bug_ids.items() if len(v) > 1}
    return Health(
        counts, canonical_counts, dup_us, dup_bug, broken_links, archived_broken_links
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=str, help="Write JSON report to path")
    args = ap.parse_args()

    health = scan()

    # Print concise summary
    print("Backlog Health Summary")
    print("- Counts:", health.counts)
    print("- Canonical:", health.canonical_counts)
    print("- Duplicate US IDs:", len(health.duplicate_us))
    print("- Duplicate BUG IDs:", len(health.duplicate_bug))
    print("- Broken links (canonical):", len(health.broken_links))
    print("- Broken links (archief - warnings):", len(health.archived_broken_links))

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(asdict(health), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"Report written to {out_path}")

    # Exit code is always 0 (this is a report). Failures are handled by the integrity checker.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
