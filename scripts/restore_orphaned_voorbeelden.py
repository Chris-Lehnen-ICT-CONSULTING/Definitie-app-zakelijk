#!/usr/bin/env python3
"""
Restore Orphaned Voorbeelden - DEF-88

This script restores 29 orphaned voorbeelden records from definitie_voorbeelden_old2
back to the main definitie_voorbeelden table.

Discovery: Definitie 39 (identiteitsmiddel) has NO voorbeelden in current table,
but has 29 voorbeelden in old2 backup table - this is data loss from migration!
"""

import sqlite3
from datetime import datetime


def restore_orphaned_voorbeelden(db_path: str, dry_run: bool = True):
    """Restore orphaned voorbeelden from old2 table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("=" * 80)
    print("RESTORE ORPHANED VOORBEELDEN - DEF-88")
    print("=" * 80)
    print(f"Database: {db_path}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE - WILL RESTORE'}")
    print()

    # Check current state
    cursor.execute("SELECT COUNT(*) FROM definitie_voorbeelden WHERE definitie_id=39")
    current_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM definitie_voorbeelden_old2 WHERE definitie_id=39"
    )
    orphaned_count = cursor.fetchone()[0]

    print(f"Current voorbeelden for definitie 39: {current_count}")
    print(f"Orphaned voorbeelden in old2: {orphaned_count}")
    print()

    if current_count > 0:
        print("⚠️  WARNING: Definitie 39 already has voorbeelden!")
        print("   Please review manually to avoid duplicates.")
        conn.close()
        return

    if orphaned_count == 0:
        print("✅ No orphaned voorbeelden found - nothing to restore")
        conn.close()
        return

    # Get orphaned records
    cursor.execute(
        """
        SELECT
            definitie_id, voorbeeld_type, voorbeeld_tekst, voorbeeld_volgorde,
            gegenereerd_door, generation_model, generation_parameters,
            actief, beoordeeld, beoordeeling, beoordeeling_notities,
            beoordeeld_door, beoordeeld_op
        FROM definitie_voorbeelden_old2
        WHERE definitie_id = 39
        ORDER BY voorbeeld_volgorde
    """
    )

    orphaned_records = cursor.fetchall()

    print(f"Found {len(orphaned_records)} orphaned records to restore:")
    print("-" * 60)

    for i, rec in enumerate(orphaned_records[:5], 1):
        print(f"{i}. [{rec[1]}] {rec[2][:60]}...")

    if len(orphaned_records) > 5:
        print(f"   ... and {len(orphaned_records) - 5} more")

    print()

    if not dry_run:
        print("⚠️  RESTORING RECORDS...")

        # Insert records back into main table
        for rec in orphaned_records:
            cursor.execute(
                """
                INSERT INTO definitie_voorbeelden (
                    definitie_id, voorbeeld_type, voorbeeld_tekst, voorbeeld_volgorde,
                    gegenereerd_door, generation_model, generation_parameters,
                    actief, beoordeeld, beoordeeling, beoordeeling_notities,
                    beoordeeld_door, beoordeeld_op,
                    aangemaakt_op, bijgewerkt_op
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    rec[0],
                    rec[1],
                    rec[2],
                    rec[3],
                    rec[4],
                    rec[5],
                    rec[6],
                    rec[7],
                    rec[8],
                    rec[9],
                    rec[10],
                    rec[11],
                    rec[12],
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                ),
            )

        conn.commit()
        print(f"✅ Successfully restored {len(orphaned_records)} voorbeelden")
        print()

        # Verify
        cursor.execute(
            "SELECT COUNT(*) FROM definitie_voorbeelden WHERE definitie_id=39"
        )
        new_count = cursor.fetchone()[0]
        print(f"Verification: definitie 39 now has {new_count} voorbeelden")

    else:
        print("ℹ️  DRY RUN - No changes made")
        print("ℹ️  Run with --execute to restore records")

    conn.close()


def cleanup_backup_tables(db_path: str, dry_run: bool = True):
    """Drop backup tables after restoration."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print()
    print("=" * 80)
    print("CLEANUP BACKUP TABLES")
    print("=" * 80)

    tables_to_drop = ["definitie_voorbeelden_old", "definitie_voorbeelden_old2"]

    for table in tables_to_drop:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"{table}: {count} records")

    print()

    if not dry_run:
        print("⚠️  DROPPING BACKUP TABLES...")
        for table in tables_to_drop:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"  ✅ Dropped {table}")

        conn.commit()
        print("\n✅ Backup tables removed")
    else:
        print("ℹ️  DRY RUN - No tables dropped")
        print("ℹ️  Run with --execute --cleanup to drop tables")

    conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Restore orphaned voorbeelden")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute restoration (default is dry run)",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Also cleanup backup tables after restoration",
    )
    parser.add_argument(
        "--db",
        default="data/definities.db",
        help="Path to database file",
    )

    args = parser.parse_args()

    # Step 1: Restore orphaned records
    restore_orphaned_voorbeelden(args.db, dry_run=not args.execute)

    # Step 2: Cleanup backup tables (if requested)
    if args.cleanup:
        cleanup_backup_tables(args.db, dry_run=not args.execute)
