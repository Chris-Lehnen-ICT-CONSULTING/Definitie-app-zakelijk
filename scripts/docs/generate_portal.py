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
import os
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
PORTAL = DOCS / "portal"

# Eenvoudige glob‑set voor scanning. Config (sources.yaml) is voor latere fases.
INCLUDE = ["**/*.md"]
EXCLUDE_DIRS = {"portal"}

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
US_ID_RE = re.compile(r"\bUS-(\d{3})\b")
EPIC_ID_RE = re.compile(r"\bEPIC-(\d{3})\b")
REQ_ID_RE = re.compile(r"\bREQ-(\d{3})\b")


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


# Canonical type set used by the portal UI
ALLOWED_TYPES = {"REQ", "EPIC", "US", "BUG", "ARCH", "GUIDE", "TEST", "COMP", "DOC"}

# Lightweight synonym mapping from frontmatter 'type' → canonical portal type
# Only applied when path heuristic returns DOC.
TYPE_SYNONYMS = {
    # user stories
    "story": "US",
    "user_story": "US",
    "user story": "US",
    # bugs / defects
    "bug": "BUG",
    "defect": "BUG",
    "issue": "BUG",
    # requirements
    "requirement": "REQ",
    # architecture / design
    "architecture": "ARCH",
    "architectuur": "ARCH",
    "design": "ARCH",
    # guides / handbooks / how-to
    "guide": "GUIDE",
    "gids": "GUIDE",
    "howto": "GUIDE",
    "how-to": "GUIDE",
    "manual": "GUIDE",
    # testing / qa
    "test": "TEST",
    "testing": "TEST",
    "qa": "TEST",
    # components / compliance
    "component": "COMP",
    "comp": "COMP",
    "compliance": "COMP",
    # generic reports / logs / analyses → treat as DOC in the portal
    "report": "DOC",
    "rapport": "DOC",
    "log": "DOC",
    "analysis": "DOC",
    "analyse": "DOC",
    "technische-analyse": "DOC",
    "tech-analysis": "DOC",
    "compliance-report": "DOC",
    # generic catch-alls
    "feature": "DOC",
    # additional safe catch-alls frequently seen
    "enhancement": "DOC",
    "feature-enhancement": "DOC",
    "technical-debt": "DOC",
    "technical_debt": "DOC",
    "technical-improvement": "DOC",
    "tooling": "DOC",
    "refactor": "DOC",
    "implementation-plan": "GUIDE",
    "ci-cd": "DOC",
    "business-requirements": "REQ",
    "audit-report": "DOC",
    "prestaties": "DOC",
    # bug synonyms
    "bug-fix": "BUG",
    "bugfix": "BUG",
}


def normalize_type(classified: str, fm_type: object) -> str:
    """Return a canonical portal type.

    - If a file is heuristically classified (not DOC), keep that.
    - Else, map frontmatter 'type' through synonyms; default to DOC when unknown.
    """
    if classified and classified != "DOC":
        return str(classified)
    if not fm_type:
        return "DOC"
    key = str(fm_type).strip().lower()
    mapped = TYPE_SYNONYMS.get(key)
    if mapped:
        return mapped
    # If user already used a canonical label, accept it; else fall back to DOC
    up = str(fm_type).strip().upper()
    return up if up in ALLOWED_TYPES else "DOC"


def rel_url(path: Path) -> str:
    """Maak paden relatief t.o.v. docs/portal/ zodat openen vanuit index.html werkt."""
    try:
        abs_path = (ROOT / path).resolve()
    except Exception:
        abs_path = path if path.is_absolute() else (ROOT / path).resolve()
    rel = os.path.relpath(abs_path, start=PORTAL)
    return Path(rel).as_posix()


def load_traceability() -> dict:
    tpath = DOCS / "traceability.json"
    if not tpath.exists():
        return {}
    try:
        return json.loads(tpath.read_text(encoding="utf-8"))
    except Exception:
        return {}


# (Geen pre-rendering of viewer rendering in deze fase – alleen index/JSON output)


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
        classified = classify(md)
        fm_type = fm.get("type")
        doc_type = normalize_type(classified, fm_type)

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

        # Extract ID-like references for simple traceability (best-effort)
        found_us_ids = sorted(set(m.group(0) for m in US_ID_RE.finditer(text)))
        found_epic_ids = sorted(set(m.group(0) for m in EPIC_ID_RE.finditer(text)))
        found_req_ids = sorted(set(m.group(0) for m in REQ_ID_RE.finditer(text)))

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
            "category": fm_type or None,
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
            # lightweight refs (not authoritative)
            "_refs": {
                "us": found_us_ids,
                "epic": found_epic_ids,
                "req": found_req_ids,
            },
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
    # Build id->item map and path lookups
    by_id: dict[str, dict] = {}
    for it in items:
        iid = it.get("id")
        if iid:
            by_id[str(iid)] = it

    # Load traceability and derive relations
    tr = load_traceability()
    epic_to_reqs: dict[str, list[str]] = {}
    for k, v in tr.items():
        if k.startswith("EPIC-"):
            epic_to_reqs[k] = list(v.get("requirements", []) or [])
    req_to_epics: dict[str, list[str]] = {}
    for epic, reqs in epic_to_reqs.items():
        for r in reqs:
            req_to_epics.setdefault(r, []).append(epic)

    # Compute REQ -> US via naive refs in REQ docs
    req_to_us: dict[str, list[str]] = {}
    for it in items:
        if (it.get("type") == "REQ") and it.get("id"):
            us_ids = [u for u in (it.get("_refs", {}).get("us") or []) if u in by_id]
            if us_ids:
                req_to_us[it["id"]] = sorted(set(us_ids))

    # Attach relations to items
    for it in items:
        t = str(it.get("type") or "")
        iid = it.get("id")
        if t == "REQ" and iid:
            it["linked_epics"] = sorted(set(req_to_epics.get(iid, []))) or None
            it["linked_stories"] = sorted(set(req_to_us.get(iid, []))) or None
        elif t == "EPIC" and iid:
            it["linked_reqs"] = sorted(set(epic_to_reqs.get(iid, []))) or None
        elif t == "US" and iid:
            # derive linked REQs by inversion of req_to_us
            linked = sorted(set(r for r, us in req_to_us.items() if iid in us))
            it["linked_reqs"] = linked or None

    # Optional top-level relations summary
    relations = {
        "req_to_epics": req_to_epics,
        "req_to_us": req_to_us,
    }
    data = {
        "documents": items,
        "aggregate": {
            "counts": aggregate_counts(items),
            "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        },
        "sources": ["docs"],
        "relations": relations,
    }
    write_portal_index(data)
    inject_inline_json(data)
    print(f"Generated {len(items)} items → docs/portal/index.html + portal-index.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
