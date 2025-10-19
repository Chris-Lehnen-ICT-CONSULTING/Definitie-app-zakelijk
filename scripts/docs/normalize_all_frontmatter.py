#!/usr/bin/env python3
"""
Normalize frontmatter for ALL backlog files (EPICs, US, BUG, REQ).

Rules:
- EPICs: canonical=true (if not already set)
- US: canonical=false (always)
- REQ: canonical=false (unless explicitly true)
- BUG: canonical=false (always)
- All: ensure owner, applies_to, last_verified exist
- Normalize status values to canonical set
"""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKLOG_DIR = ROOT / "docs/backlog"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL | re.MULTILINE)

# Canonical status mappings
STATUS_MAPPINGS = {
    # EPIC statuses → canonical
    "IN_UITVOERING": "active",
    "Nogtebepalen": "proposed",
    "TE_DOEN": "active",
    "Active": "active",
    "active": "active",
    "proposed": "proposed",
    "completed": "completed",
    "Voltooid": "completed",
    "READY": "active",
    "Open": "proposed",
    "Deferred": "deferred",
    "DEFERRED": "deferred",
    "COMPLETED": "completed",
    # US statuses → canonical
    "TODO": "open",
    "todo": "open",
    "Todo": "open",
    "Backlog": "open",
    "OPEN": "open",
    "open": "open",
    "IN_PROGRESS": "in_progress",
    "Inuitvoering": "in_progress",
    "in_progress": "in_progress",
    "GEREED": "completed",
    "pending": "open",
    "Ready": "open",
    "Gepland": "open",
    "Done": "completed",
    "DONE": "completed",
    "DRAFT": "open",
    "Completed": "completed",
}


def parse_frontmatter(text: str) -> tuple[dict | None, str]:
    """Extract frontmatter dict and body from markdown text."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, text

    block = m.group(1)
    kv = {}
    current_key = None
    current_list = []

    for line in block.splitlines():
        line = line.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue

        # Check for list item
        if line.strip().startswith("- "):
            if current_key:
                current_list.append(line.strip()[2:])
            continue

        # Check for key-value
        if ":" in line:
            # Save previous list if exists
            if current_key and current_list:
                kv[current_key] = current_list
                current_list = []

            k, v = line.split(":", 1)
            current_key = k.strip()
            v = v.strip().strip("'\"")
            if v:  # Has value on same line
                kv[current_key] = v
                current_key = None
            else:  # Value on next lines (list)
                kv[current_key] = None

    # Save last list if exists
    if current_key and current_list:
        kv[current_key] = current_list

    body = text[m.end() :]
    return kv, body


def render_frontmatter(kv: dict) -> str:
    """Render frontmatter dict back to YAML block."""
    order = [
        "id",
        "epic",
        "titel",
        "title",
        "type",
        "status",
        "prioriteit",
        "priority",
        "story_points",
        "sprint",
        "aangemaakt",
        "created",
        "bijgewerkt",
        "updated",
        "owner",
        "applies_to",
        "canonical",
        "last_verified",
        "vereisten",
        "requirements",
        "epics",
        "stories",
        "stakeholders",
        "tags",
        "links",
        "sources",
    ]

    lines = []
    used_keys = set()

    # Ordered keys first
    for key in order:
        if key in kv:
            val = kv[key]
            if isinstance(val, list):
                lines.append(f"{key}:")
                for item in val:
                    lines.append(f"  - {item}")
            elif val is None:
                lines.append(f"{key}:")
            else:
                lines.append(f"{key}: {val}")
            used_keys.add(key)

    # Remaining keys
    for k, v in kv.items():
        if k not in used_keys:
            if isinstance(v, list):
                lines.append(f"{k}:")
                for item in v:
                    lines.append(f"  - {item}")
            elif v is None:
                lines.append(f"{k}:")
            else:
                lines.append(f"{k}: {v}")

    return "---\n" + "\n".join(lines) + "\n---\n"


def normalize_file(path: Path) -> bool:
    """Normalize frontmatter for a single file. Returns True if changed."""
    text = path.read_text(encoding="utf-8")
    kv, body = parse_frontmatter(text)

    if kv is None:
        # No frontmatter - skip files without frontmatter for now
        # (add minimal frontmatter if needed)
        return False

    today = date.today().isoformat()
    changed = False

    # Determine file type
    is_epic = "EPIC-" in path.stem and path.parent.name.startswith("EPIC-")
    is_us = "US-" in path.stem and "US-" in path.parent.name
    is_bug = "BUG-" in path.stem
    is_req = "REQ-" in path.stem

    # Rule 1: Set canonical correctly
    if is_epic:
        if kv.get("canonical") != "true":
            kv["canonical"] = "true"
            changed = True
    elif is_us or is_bug:
        if kv.get("canonical") != "false":
            kv["canonical"] = "false"
            changed = True
    elif is_req:
        # REQ files should default to false unless explicitly true
        if "canonical" not in kv:
            kv["canonical"] = "false"
            changed = True

    # Rule 2: Ensure required fields
    if "owner" not in kv or not kv.get("owner"):
        # Default owner based on type
        if is_epic or is_req:
            kv["owner"] = "product-owner"
        else:
            kv["owner"] = "development-team"
        changed = True

    if "applies_to" not in kv or not kv.get("applies_to"):
        kv["applies_to"] = "definitie-app@current"
        changed = True

    if "last_verified" not in kv or not kv.get("last_verified"):
        kv["last_verified"] = today
        changed = True

    # Rule 3: Normalize status values
    if "status" in kv:
        old_status = kv["status"]
        if old_status in STATUS_MAPPINGS:
            new_status = STATUS_MAPPINGS[old_status]
            if new_status != old_status:
                kv["status"] = new_status
                changed = True

    if changed:
        new_text = render_frontmatter(kv) + body
        path.write_text(new_text, encoding="utf-8")
        return True

    return False


def main() -> int:
    """Normalize all backlog files."""
    changed_count = 0
    total_count = 0

    # Process all markdown files in backlog
    for md_file in BACKLOG_DIR.rglob("*.md"):
        # Skip non-backlog files
        if "dashboard" in str(md_file) or "portal" in str(md_file):
            continue

        total_count += 1
        if normalize_file(md_file):
            changed_count += 1
            print(f"✓ {md_file.relative_to(ROOT)}")

    print(f"\n📊 Summary: {changed_count}/{total_count} files updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
