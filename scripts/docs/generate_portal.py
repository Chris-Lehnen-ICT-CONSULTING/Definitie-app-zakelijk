#!/usr/bin/env python3
"""
Minimal portal generator (MVP)
Scant docs/, leest frontmatter (YAML-achtig) en schrijft:
- docs/portal/portal-index.json (export)
- injecteert inline JSON in docs/portal/index.html tussen PORTAL-DATA markers

Ontworpen om zonder externe dependencies te draaien.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
PORTAL = DOCS / "portal"

# Eenvoudige glob‑set voor scanning. Config (sources.yaml) is voor latere fases.
INCLUDE = ["**/*.md"]
EXCLUDE_DIRS = {"portal"}

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


def parse_frontmatter(text: str) -> dict:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    block = m.group(1)
    data: dict[str, object] = {}
    for line in block.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        # naive key: value parser (geen nested YAML)
        if ":" in line:
            k, v = line.split(":", 1)
            data[k.strip()] = v.strip().strip("'\"")
    return data


def first_heading(text: str) -> str | None:
    m = H1_RE.search(text)
    return m.group(1).strip() if m else None


def classify(path: Path) -> str:
    p = str(path).replace("\\", "/")
    if "/backlog/requirements/REQ-" in p:
        return "REQ"
    if "/backlog/EPIC-" in p and p.endswith("/EPIC-" + path.parent.name + ".md"):
        return "EPIC"
    if "/backlog/EPIC-" in p and "/US-" in p and p.endswith("/US-" + path.parent.name + ".md"):
        return "US"
    if "/BUG-" in p or "/CFR-BUG-" in p:
        return "BUG"
    if "/architectuur/" in p:
        return "ARCH"
    if "/guidelines/" in p:
        return "GUIDE"
    if "/testing/" in p:
        return "TEST"
    if "/compliance/" in p:
        return "COMP"
    return "DOC"


def rel_url(path: Path) -> str:
    # linkbaar in repo viewer; voor lokaal gebruik blijft href naar pad werken
    return str(path.as_posix())


def scan_docs() -> list[dict]:
    items: list[dict] = []
    for md in DOCS.rglob("*.md"):
        if any(part in EXCLUDE_DIRS for part in md.relative_to(DOCS).parts[:1]):
            continue
        try:
            text = md.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        fm = parse_frontmatter(text)
        title = fm.get("titel") or fm.get("title") or first_heading(text) or md.stem
        doc_type = fm.get("type") or classify(md)

        # Planning gerelateerde velden
        sprint = fm.get("sprint") or ""
        story_points = fm.get("story_points") or fm.get("storypoints") or ""
        prioriteit = fm.get("prioriteit") or ""
        completion = fm.get("completion") or fm.get("progress") or ""
        target_release = fm.get("target_release") or ""

        # derive numeric sprint if mogelijk
        sprint_number = None
        if isinstance(sprint, str):
            mnum = re.search(r"(\d+)", sprint)
            if mnum:
                try:
                    sprint_number = int(mnum.group(1))
                except Exception:
                    sprint_number = None

        # prioriteit/type ranking
        pr_rank = {"KRITIEK": 1, "HOOG": 2, "GEMIDDELD": 3, "LAAG": 4}
        type_rank = {"EPIC": 1, "US": 2, "BUG": 3, "REQ": 4}
        priority_rank = pr_rank.get(str(prioriteit).upper(), 5)
        tr = type_rank.get(str(doc_type).upper(), 9)

        # parent ids uit pad
        parent_epic = None
        parent_us = None
        for ppart in md.parts:
            if re.match(r"EPIC-\d+", ppart):
                parent_epic = ppart
            if re.match(r"US-\d+", ppart):
                parent_us = ppart

        item = {
            "id": fm.get("id") or None,
            "type": str(doc_type),
            "title": str(title),
            "path": rel_url(md.relative_to(ROOT)),
            "url": rel_url(md.relative_to(ROOT)),
            "status": fm.get("status") or None,
            "prioriteit": prioriteit or None,
            "owner": fm.get("owner") or None,
            "canonical": True if str(fm.get("canonical")).lower() == "true" else False,
            "last_verified": fm.get("last_verified") or None,
            "applies_to": fm.get("applies_to") or None,
            "sprint": sprint or None,
            "story_points": story_points or None,
            "completion": completion or None,
            "target_release": target_release or None,
            "planning": {
                "sprint_number": sprint_number,
                "priority_rank": priority_rank,
                "type_rank": tr,
            },
            "parent_epic": parent_epic,
            "parent_us": parent_us,
        }
        items.append(item)
    return items


def aggregate_counts(items: list[dict]) -> dict:
    counts: dict[str, int] = {}
    for it in items:
        t = it.get("type") or "DOC"
        counts[t] = counts.get(t, 0) + 1
    return counts


def write_portal_index(data: dict) -> None:
    out = PORTAL / "portal-index.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def inject_inline_json(data: dict) -> None:
    html = PORTAL / "index.html"
    if not html.exists():
        return
    s = html.read_text(encoding="utf-8")
    start = "<!--PORTAL-DATA-START-->"
    end = "<!--PORTAL-DATA-END-->"
    before, middle, after = s.partition(start)
    if not middle:
        # no markers found; do nothing
        return
    _, middle2, after2 = after.partition(end)
    if not middle2:
        return
    payload = f"\n    <script id=\"portal-data\" type=\"application/json\">{json.dumps(data, ensure_ascii=False)}</script>\n"
    new = before + start + payload + end + after2
    html.write_text(new, encoding="utf-8")


def main() -> int:
    PORTAL.mkdir(parents=True, exist_ok=True)
    items = scan_docs()
    data = {
        "documents": items,
        "aggregate": {
            "counts": aggregate_counts(items),
            "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        },
        "sources": ["docs"]
    }
    write_portal_index(data)
    inject_inline_json(data)
    print(f"Generated {len(items)} items → docs/portal/index.html + portal-index.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
