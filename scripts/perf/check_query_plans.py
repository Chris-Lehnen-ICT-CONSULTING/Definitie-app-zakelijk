#!/usr/bin/env python3
"""
SQLite query plan checker for hot-path queries in Definitie-app.

Runs EXPLAIN QUERY PLAN for representative queries against data/definities.db
and prints whether indexes are used. Non-destructive, read-only.
"""

import sqlite3
from pathlib import Path


DB_PATH = Path("data/definities.db")


def explain(cur: sqlite3.Cursor, sql: str, params: tuple) -> list[str]:
    cur.execute(f"EXPLAIN QUERY PLAN {sql}", params)
    rows = cur.fetchall()
    # Rows are tuples: (selectid, order, from, detail)
    return [str(r[-1]) for r in rows]


def main() -> int:
    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}")
        return 1

    conn = sqlite3.connect(str(DB_PATH))
    try:
        cur = conn.cursor()

        checks = [
            (
                "find_by_begrip",
                "SELECT * FROM definities WHERE begrip = ? AND status != ? ORDER BY updated_at DESC LIMIT 1",
                ("test", "archived"),
            ),
            (
                "by_categorie",
                "SELECT * FROM definities WHERE categorie = ? LIMIT 50",
                ("proces",),
            ),
            (
                "by_status",
                "SELECT * FROM definities WHERE status = ? LIMIT 50",
                ("established",),
            ),
            (
                "by_context",
                "SELECT * FROM definities WHERE organisatorische_context = ? AND juridische_context = ? LIMIT 10",
                ("OM", "Strafrecht"),
            ),
        ]

        print(f"Checking query plans on {DB_PATH}...\n")
        for name, sql, params in checks:
            details = explain(cur, sql, params)
            uses_index = any(
                "USING INDEX" in d.upper() or "INDEX" in d.upper() for d in details
            )
            print(f"[{name}] -> {'INDEX' if uses_index else 'NO INDEX'}")
            for d in details:
                print(f"  - {d}")
            print()

        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
