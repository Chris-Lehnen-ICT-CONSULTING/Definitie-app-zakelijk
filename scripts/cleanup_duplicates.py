#!/usr/bin/env python3
"""
Script to clean up duplicate definitions before migration.
Archives duplicate records, keeping the one with highest quality.
"""

import sqlite3
from datetime import datetime
from pathlib import Path


def cleanup_duplicates():
    """Clean up duplicate definitions by archiving lower quality ones."""
    db_path = Path(__file__).parent.parent / "data" / "definities.db"

    print(f"Cleaning up duplicates in: {db_path}")
    print("=" * 80)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Strategy: Keep the record with:
    # 1. Highest status priority (established > review > draft)
    # 2. Highest validation_score
    # 3. Most recent created_at

    status_priority = {"established": 3, "review": 2, "draft": 1, "archived": 0}

    # Find duplicate groups
    # Business rule: (begrip, org_context, jur_context, wet_basis, categorie) must be unique
    query = """
        SELECT
            begrip,
            organisatorische_context,
            juridische_context,
            categorie,
            wettelijke_basis,
            GROUP_CONCAT(id) as ids
        FROM definities
        WHERE status != 'archived'
        GROUP BY
            begrip,
            organisatorische_context,
            juridische_context,
            categorie,
            wettelijke_basis
        HAVING COUNT(*) > 1
    """

    cursor.execute(query)
    duplicate_groups = cursor.fetchall()

    if not duplicate_groups:
        print("✅ No duplicates found - database is clean!")
        conn.close()
        return 0

    total_archived = 0

    for group in duplicate_groups:
        begrip, org_ctx, jur_ctx, cat, wet, ids_str = group
        ids = [int(x) for x in ids_str.split(",")]

        print(f"\nProcessing duplicate group: {begrip}")
        print(f"  IDs: {ids}")

        # Get full records for all duplicates
        records = []
        for record_id in ids:
            cursor.execute(
                """
                SELECT id, begrip, status, validation_score, created_at
                FROM definities
                WHERE id = ?
            """,
                (record_id,),
            )
            record = cursor.fetchone()
            records.append(
                {
                    "id": record[0],
                    "begrip": record[1],
                    "status": record[2],
                    "validation_score": record[3] or 0.0,
                    "created_at": record[4],
                }
            )

        # Sort by priority: status > validation_score > created_at
        def sort_key(r):
            return (
                status_priority.get(r["status"], 0),
                r["validation_score"],
                r["created_at"] or "",
            )

        records.sort(key=sort_key, reverse=True)

        # Keep first (highest priority), archive rest
        keep_record = records[0]
        archive_records = records[1:]

        print(
            f"  ✅ KEEPING: ID {keep_record['id']} (status={keep_record['status']}, score={keep_record['validation_score']:.2f})"
        )

        for record in archive_records:
            print(
                f"  🗑️  ARCHIVING: ID {record['id']} (status={record['status']}, score={record['validation_score']:.2f})"
            )

            # Archive the record
            cursor.execute(
                """
                UPDATE definities
                SET
                    status = 'archived',
                    updated_at = ?,
                    updated_by = 'system'
                WHERE id = ?
            """,
                (datetime.now().isoformat(), record["id"]),
            )

            total_archived += 1

    conn.commit()
    conn.close()

    print()
    print("=" * 80)
    print("✅ CLEANUP COMPLETE")
    print(f"   Duplicate groups processed: {len(duplicate_groups)}")
    print(f"   Records archived: {total_archived}")
    print()
    print("✅ Database is now ready for unique constraint migration!")

    return total_archived


if __name__ == "__main__":
    import sys

    num_archived = cleanup_duplicates()
    sys.exit(0)
