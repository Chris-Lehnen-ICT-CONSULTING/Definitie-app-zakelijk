#!/usr/bin/env python3
"""
Converter: App Export (JSON/CSV) → Batch Import CSV (canoniek)

Doel: Zet een exportbestand (JSON van de app of CSV met velden) om naar
het batch-import CSV-formaat dat de Management-tab verwacht:
  begrip, definitie, categorie, organisatorische_context, juridische_context, wettelijke_basis

Gebruik:
  python scripts/import/convert_export_to_import_csv.py \
      --input src/test_export.json \
      --output samples/import/sbb_identiteitsvaststelling.csv

Opmerking:
- Contextvelden worden genormaliseerd naar komma-gescheiden lijsten.
- Categorie default naar "proces" indien ontbreekt.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


CANONICAL_HEADERS = [
    "begrip",
    "definitie",
    "categorie",
    "organisatorische_context",
    "juridische_context",
    "wettelijke_basis",
]


def to_list(val: Any) -> list[str]:
    if val is None:
        return []
    if isinstance(val, list):
        return [str(x).strip() for x in val if str(x).strip()]
    s = str(val).strip()
    if not s:
        return []
    # Split op komma als het een string is
    return [t.strip() for t in s.split(",") if t.strip()]


def normalize_row(d: dict[str, Any]) -> dict[str, str]:
    begrip = d.get("begrip") or d.get("term") or d.get("naam") or ""
    definitie = d.get("definitie") or d.get("omschrijving") or d.get("description") or ""
    categorie = d.get("categorie") or d.get("category") or "proces"

    org = d.get("organisatorische_context") or d.get("context") or d.get("organisatie") or []
    jur = d.get("juridische_context") or d.get("juridisch") or []
    wet = d.get("wettelijke_basis") or d.get("wet") or []

    org_list = to_list(org)
    jur_list = to_list(jur)
    wet_list = to_list(wet)

    return {
        "begrip": str(begrip).strip(),
        "definitie": str(definitie).strip(),
        "categorie": str(categorie).strip() or "proces",
        "organisatorische_context": ", ".join(org_list),
        "juridische_context": ", ".join(jur_list),
        "wettelijke_basis": ", ".join(wet_list),
    }


def load_json(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "definities" in data:
        return list(data.get("definities") or [])
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # Enkel object → als lijst behandelen
        return [data]
    raise ValueError("Onbekend JSON-formaat voor export")


def load_csv(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def write_import_csv(out_path: Path, rows: list[dict[str, str]]):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CANONICAL_HEADERS)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Convert export (JSON/CSV) to import CSV format")
    ap.add_argument("--input", required=True, help="Pad naar exportbestand (JSON/CSV)")
    ap.add_argument("--output", required=True, help="Pad voor output import CSV")
    args = ap.parse_args(argv)

    in_path = Path(args.input)
    out_path = Path(args.output)
    if not in_path.exists():
        print(f"❌ Input niet gevonden: {in_path}")
        return 2

    try:
        if in_path.suffix.lower() == ".json":
            raw = load_json(in_path)
        elif in_path.suffix.lower() == ".csv":
            raw = load_csv(in_path)
        else:
            print("⚠️ Onbekend inputtype; probeer JSON of CSV")
            return 3

        norm = [normalize_row(d) for d in raw]
        write_import_csv(out_path, norm)
        print(f"✅ Geschreven: {out_path} ({len(norm)} records)")
        return 0
    except Exception as e:
        print(f"❌ Conversie mislukt: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

