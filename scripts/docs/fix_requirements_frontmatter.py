#!/usr/bin/env python3
"""
Normalize frontmatter for requirements under docs/backlog/requirements.

Adds missing keys according to Documentation Policy:
- owner: product (default) or architecture for nonfunctional
- applies_to: definitie-app@current
- last_verified: YYYY-MM-DD (today)
- canonical: false (safe default)

If a file lacks frontmatter, a minimal one is inserted using the ID inferred
from filename and default status 'Backlog'.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQ_DIR = ROOT / "docs/backlog/requirements"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def parse_kv(block: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in block.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip().strip("'\"")
    return out


def render_block(kv: dict[str, str]) -> str:
    # Preserve a reasonable order
    order = [
        "id",
        "titel",
        "type",
        "status",
        "prioriteit",
        "aangemaakt",
        "bijgewerkt",
        "owner",
        "applies_to",
        "canonical",
        "last_verified",
        "epics",
        "stories",
        "links",
        "sources",
    ]
    lines = []
    for key in order:
        if key in kv:
            val = kv[key]
            # simple scalar or list
            if isinstance(val, list):
                lines.append(f"{key}:")
                for it in val:
                    lines.append(f"  - {it}")
            else:
                lines.append(f"{key}: {val}")
    # add any remaining keys
    for k, v in kv.items():
        if k not in order:
            if isinstance(v, list):
                lines.append(f"{k}:")
                for it in v:
                    lines.append(f"  - {it}")
            else:
                lines.append(f"{k}: {v}")
    return "---\n" + "\n".join(lines) + "\n---\n"


def infer_id_from_filename(path: Path) -> str | None:
    m = re.search(r"REQ-\d{3}", path.name)
    return m.group(0) if m else None


def main() -> int:
    today = date.today().isoformat()
    changed = 0
    files = sorted(REQ_DIR.glob("REQ-*.md"))
    for f in files:
        if f.name == "REQ-REGISTRY.json":
            continue
        text = f.read_text(encoding="utf-8")
        m = FRONTMATTER_RE.match(text)
        if m:
            block = m.group(1)
            kv = parse_kv(block)
            # Determine defaults
            doc_type = (kv.get("type") or "").strip().lower()
            owner = kv.get("owner")
            if not owner:
                owner = "architecture" if "nonfunctional" in doc_type else "product"
                kv["owner"] = owner
            if "applies_to" not in kv or not kv.get("applies_to"):
                kv["applies_to"] = "definitie-app@current"
            if "canonical" not in kv or str(kv.get("canonical")).strip() == "":
                kv["canonical"] = "false"
            if "last_verified" not in kv or not kv.get("last_verified"):
                kv["last_verified"] = today
            new_block = render_block(kv)
            new_text = FRONTMATTER_RE.sub(new_block, text, count=1)
            if new_text != text:
                f.write_text(new_text, encoding="utf-8")
                changed += 1
        else:
            # Insert minimal frontmatter
            rid = infer_id_from_filename(f)
            kv = {
                "id": rid or "",
                "titel": f"{rid or f.stem}",
                "type": "functional",
                "status": "Backlog",
                "prioriteit": "GEMIDDELD",
                "owner": "product",
                "applies_to": "definitie-app@current",
                "canonical": "false",
                "last_verified": today,
            }
            new_text = render_block(kv) + text
            f.write_text(new_text, encoding="utf-8")
            changed += 1
    print(f"Updated {changed} requirement files with policy frontmatter fields")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
