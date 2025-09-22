#!/usr/bin/env python3
"""
One-off maintenance: verwijder 'nan'/'null'/'none' uit contextlijsten in de database.

Sommige CSV's leveren NaN voor lege cellen; als die als string 'nan' zijn opgeslagen
in organisatorische_context/juridische_context JSON-lijsten, verschijnen ze in de UI als 'Anders.../nan'.

Gebruik:
  python scripts/maintenance/cleanup_nan_contexts.py --db data/definities.db
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any


def _sanitize_list(val: Any) -> list[str]:
    try:
        if not val:
            return []
        if isinstance(val, str):
            items = json.loads(val) if val.strip().startswith("[") else [val]
        elif isinstance(val, list):
            items = val
        else:
            return []
    except Exception:
        return []

    cleaned: list[str] = []
    for it in items:
        s = str(it).strip()
        if not s:
            continue
        if s.lower() in ("nan", "none", "null"):
            continue
        cleaned.append(s)
    return cleaned


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/definities.db")
    args = ap.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"❌ DB niet gevonden: {db_path}")
        return 2

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, organisatorische_context, juridische_context, wettelijke_basis FROM definities")
    rows = cur.fetchall()

    updated = 0
    for row in rows:
        org = _sanitize_list(row["organisatorische_context"])
        jur = _sanitize_list(row["juridische_context"])
        wet = _sanitize_list(row["wettelijke_basis"])
        org_json = json.dumps(org, ensure_ascii=False)
        jur_json = json.dumps(jur, ensure_ascii=False)

        wet_json = json.dumps(wet, ensure_ascii=False)

        if (
            org_json != (row["organisatorische_context"] or "")
            or jur_json != (row["juridische_context"] or "")
            or wet_json != (row["wettelijke_basis"] or "")
        ):
            cur.execute(
                "UPDATE definities SET organisatorische_context=?, juridische_context=?, wettelijke_basis=? WHERE id=?",
                (org_json, jur_json, wet_json, row["id"]),
            )
            updated += 1

    conn.commit()
    conn.close()
    print(f"✅ Opschoning voltooid — {updated} records bijgewerkt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
