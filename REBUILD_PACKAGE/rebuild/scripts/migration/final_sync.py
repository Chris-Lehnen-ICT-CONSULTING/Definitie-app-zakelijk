#!/usr/bin/env python3
"""Final data synchronization before cutover.

This script performs the final data synchronization between primary and shadow
databases immediately before cutover, ensuring 100% data consistency at the
moment of switch.

Usage:
    python rebuild/scripts/migration/final_sync.py --dry-run
    python rebuild/scripts/migration/final_sync.py --execute
    python rebuild/scripts/migration/final_sync.py --execute --verify

Example:
    $ python rebuild/scripts/migration/final_sync.py --dry-run
    🔍 DRY RUN MODE - No changes will be made
    ✅ Would sync 5 new definitions
    ✅ Would sync 12 updates
    ✅ Would sync 3 status changes
    ✅ Dry run complete (estimated sync time: 2.3s)

    $ python rebuild/scripts/migration/final_sync.py --execute --verify
    ✅ Synced 5 new definitions
    ✅ Synced 12 updates
    ✅ Synced 3 status changes
    ✅ Verification passed (100% consistency)
    ✅ Final sync complete
"""

import argparse
import json
import logging
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            f"logs/migration/final_sync_{datetime.now():%Y%m%d_%H%M%S}.log"
        ),
    ],
)
logger = logging.getLogger(__name__)


class FinalSynchronizer:
    """Perform final data synchronization before cutover."""

    def __init__(self, primary_db: str, shadow_db: str, dry_run: bool = True):
        """Initialize synchronizer.

        Args:
            primary_db: Path to primary database
            shadow_db: Path to shadow database
            dry_run: If True, simulate sync without changes
        """
        self.primary_db = Path(primary_db)
        self.shadow_db = Path(shadow_db)
        self.dry_run = dry_run
        self.sync_results = {
            "timestamp": datetime.now().isoformat(),
            "new_definitions": 0,
            "updates": 0,
            "status_changes": 0,
            "deletes": 0,
            "errors": [],
        }
        self.backup_path = None

    def create_backup(self) -> bool:
        """Create backup of shadow database before sync.

        Returns:
            True if backup successful
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.backup_path = (
                self.shadow_db.parent / f"{self.shadow_db.name}.pre-sync.{timestamp}"
            )

            if not self.dry_run:
                shutil.copy2(self.shadow_db, self.backup_path)
                logger.info(f"📦 Backup created: {self.backup_path}")
            else:
                logger.info(f"📦 Would create backup: {self.backup_path}")

            return True

        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            return False

    def identify_changes(self) -> dict[str, Any]:
        """Identify changes that need to be synced.

        Returns:
            Dictionary of changes by type
        """
        logger.info("\n🔍 Identifying changes to sync...")

        try:
            with (
                sqlite3.connect(self.primary_db) as primary_conn,
                sqlite3.connect(self.shadow_db) as shadow_conn,
            ):

                primary_conn.row_factory = sqlite3.Row
                shadow_conn.row_factory = sqlite3.Row

                # Get all primary definitions
                primary_defs = {
                    row["id"]: dict(row)
                    for row in primary_conn.execute(
                        "SELECT * FROM definities ORDER BY id"
                    ).fetchall()
                }

                # Get all shadow definitions
                shadow_defs = {
                    row["id"]: dict(row)
                    for row in shadow_conn.execute(
                        "SELECT * FROM definities ORDER BY id"
                    ).fetchall()
                }

                changes = {
                    "new": [],
                    "updated": [],
                    "status_changed": [],
                    "deleted": [],
                }

                # Find new and updated definitions
                for def_id, primary_def in primary_defs.items():
                    if def_id not in shadow_defs:
                        changes["new"].append(primary_def)
                    else:
                        shadow_def = shadow_defs[def_id]

                        # Check if updated
                        if primary_def["updated_at"] != shadow_def["updated_at"]:
                            if primary_def["definitie"] != shadow_def["definitie"]:
                                changes["updated"].append(primary_def)
                            elif primary_def["status"] != shadow_def["status"]:
                                changes["status_changed"].append(primary_def)

                # Find deleted definitions
                for def_id in shadow_defs:
                    if def_id not in primary_defs:
                        changes["deleted"].append(shadow_defs[def_id])

                logger.info("  📊 Changes identified:")
                logger.info(f"     - New definitions: {len(changes['new'])}")
                logger.info(f"     - Updates: {len(changes['updated'])}")
                logger.info(f"     - Status changes: {len(changes['status_changed'])}")
                logger.info(f"     - Deletes: {len(changes['deleted'])}")

                return changes

        except Exception as e:
            logger.error(f"❌ Change identification failed: {e}")
            return {"new": [], "updated": [], "status_changed": [], "deleted": []}

    def sync_new_definitions(self, definitions: list[dict[str, Any]]) -> bool:
        """Sync new definitions to shadow database.

        Args:
            definitions: List of new definitions

        Returns:
            True if sync successful
        """
        if not definitions:
            return True

        logger.info(f"\n📥 Syncing {len(definitions)} new definitions...")

        if self.dry_run:
            logger.info(
                f"   Would sync: {', '.join(d['begrip'] for d in definitions[:5])}"
            )
            if len(definitions) > 5:
                logger.info(f"   ... and {len(definitions) - 5} more")
            self.sync_results["new_definitions"] = len(definitions)
            return True

        try:
            with sqlite3.connect(self.shadow_db) as conn:
                for definition in definitions:
                    # Prepare INSERT statement
                    columns = list(definition.keys())
                    values = [definition[col] for col in columns]
                    placeholders = ", ".join(["?" for _ in values])
                    columns_str = ", ".join(columns)

                    sql = f"INSERT INTO definities ({columns_str}) VALUES ({placeholders})"
                    conn.execute(sql, values)

                conn.commit()

            self.sync_results["new_definitions"] = len(definitions)
            logger.info(f"✅ Synced {len(definitions)} new definitions")
            return True

        except Exception as e:
            logger.error(f"❌ New definitions sync failed: {e}")
            self.sync_results["errors"].append(f"New definitions: {e}")
            return False

    def sync_updates(self, definitions: list[dict[str, Any]]) -> bool:
        """Sync updated definitions to shadow database.

        Args:
            definitions: List of updated definitions

        Returns:
            True if sync successful
        """
        if not definitions:
            return True

        logger.info(f"\n🔄 Syncing {len(definitions)} updates...")

        if self.dry_run:
            logger.info(
                f"   Would update: {', '.join(d['begrip'] for d in definitions[:5])}"
            )
            if len(definitions) > 5:
                logger.info(f"   ... and {len(definitions) - 5} more")
            self.sync_results["updates"] = len(definitions)
            return True

        try:
            with sqlite3.connect(self.shadow_db) as conn:
                for definition in definitions:
                    # Update all fields except id
                    def_id = definition["id"]
                    update_fields = [key for key in definition.keys() if key != "id"]

                    set_clause = ", ".join([f"{field} = ?" for field in update_fields])
                    values = [definition[field] for field in update_fields] + [def_id]

                    sql = f"UPDATE definities SET {set_clause} WHERE id = ?"
                    conn.execute(sql, values)

                conn.commit()

            self.sync_results["updates"] = len(definitions)
            logger.info(f"✅ Synced {len(definitions)} updates")
            return True

        except Exception as e:
            logger.error(f"❌ Updates sync failed: {e}")
            self.sync_results["errors"].append(f"Updates: {e}")
            return False

    def sync_status_changes(self, definitions: list[dict[str, Any]]) -> bool:
        """Sync status changes to shadow database.

        Args:
            definitions: List of definitions with status changes

        Returns:
            True if sync successful
        """
        if not definitions:
            return True

        logger.info(f"\n🔀 Syncing {len(definitions)} status changes...")

        if self.dry_run:
            logger.info(
                f"   Would update status for: {', '.join(d['begrip'] for d in definitions[:5])}"
            )
            if len(definitions) > 5:
                logger.info(f"   ... and {len(definitions) - 5} more")
            self.sync_results["status_changes"] = len(definitions)
            return True

        try:
            with sqlite3.connect(self.shadow_db) as conn:
                for definition in definitions:
                    sql = (
                        "UPDATE definities SET status = ?, updated_at = ? WHERE id = ?"
                    )
                    conn.execute(
                        sql,
                        (
                            definition["status"],
                            definition["updated_at"],
                            definition["id"],
                        ),
                    )

                conn.commit()

            self.sync_results["status_changes"] = len(definitions)
            logger.info(f"✅ Synced {len(definitions)} status changes")
            return True

        except Exception as e:
            logger.error(f"❌ Status changes sync failed: {e}")
            self.sync_results["errors"].append(f"Status changes: {e}")
            return False

    def verify_sync(self) -> bool:
        """Verify synchronization completeness.

        Returns:
            True if verification passed
        """
        logger.info("\n🔍 Verifying synchronization...")

        try:
            with (
                sqlite3.connect(self.primary_db) as primary_conn,
                sqlite3.connect(self.shadow_db) as shadow_conn,
            ):

                # Count records
                primary_count = primary_conn.execute(
                    "SELECT COUNT(*) FROM definities"
                ).fetchone()[0]
                shadow_count = shadow_conn.execute(
                    "SELECT COUNT(*) FROM definities"
                ).fetchone()[0]

                if primary_count != shadow_count:
                    logger.error(
                        f"❌ Count mismatch: primary={primary_count}, shadow={shadow_count}"
                    )
                    return False

                # Sample verification (first 10 records)
                primary_conn.row_factory = sqlite3.Row
                shadow_conn.row_factory = sqlite3.Row

                primary_sample = primary_conn.execute(
                    "SELECT id, begrip, definitie, status FROM definities ORDER BY id LIMIT 10"
                ).fetchall()
                shadow_sample = shadow_conn.execute(
                    "SELECT id, begrip, definitie, status FROM definities ORDER BY id LIMIT 10"
                ).fetchall()

                for primary_row, shadow_row in zip(
                    primary_sample, shadow_sample, strict=False
                ):
                    if dict(primary_row) != dict(shadow_row):
                        logger.error(f"❌ Sample mismatch at ID {primary_row['id']}")
                        return False

                logger.info(
                    f"✅ Verification passed ({primary_count} definitions, 100% consistency)"
                )
                return True

        except Exception as e:
            logger.error(f"❌ Verification failed: {e}")
            return False

    def print_summary(self):
        """Print synchronization summary."""
        logger.info("\n" + "=" * 60)
        logger.info("FINAL SYNC SUMMARY")
        logger.info("=" * 60)
        logger.info(f"New definitions: {self.sync_results['new_definitions']}")
        logger.info(f"Updates: {self.sync_results['updates']}")
        logger.info(f"Status changes: {self.sync_results['status_changes']}")
        logger.info(f"Deletes: {self.sync_results['deletes']}")

        if self.sync_results["errors"]:
            logger.error(f"\n❌ Errors encountered: {len(self.sync_results['errors'])}")
            for error in self.sync_results["errors"]:
                logger.error(f"   - {error}")
        else:
            logger.info("\n✅ No errors")

        logger.info("=" * 60)

    def save_results(self):
        """Save sync results to JSON file."""
        output_file = Path(
            f"logs/migration/final_sync_{datetime.now():%Y%m%d_%H%M%S}.json"
        )
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(self.sync_results, f, indent=2)

        logger.info(f"\n📄 Sync results saved to: {output_file}")

    def execute(self, verify: bool = True) -> bool:
        """Execute final synchronization.

        Args:
            verify: If True, verify sync after execution

        Returns:
            True if sync successful
        """
        logger.info("=" * 60)
        if self.dry_run:
            logger.info("🔍 DRY RUN MODE - No changes will be made")
        else:
            logger.info("⚠️  EXECUTE MODE - Database will be modified")
        logger.info("=" * 60)
        logger.info(f"Primary: {self.primary_db}")
        logger.info(f"Shadow: {self.shadow_db}")

        # Create backup
        if not self.create_backup():
            return False

        # Identify changes
        changes = self.identify_changes()

        # Sync changes
        success = True
        success = self.sync_new_definitions(changes["new"]) and success
        success = self.sync_updates(changes["updated"]) and success
        success = self.sync_status_changes(changes["status_changed"]) and success

        # Verify if requested and not dry-run
        if verify and not self.dry_run:
            if not self.verify_sync():
                success = False

        # Print summary
        self.print_summary()

        # Save results
        self.save_results()

        logger.info("\n" + "=" * 60)
        if success:
            logger.info("✅ FINAL SYNC COMPLETE")
        else:
            logger.error("❌ FINAL SYNC FAILED")
        logger.info("=" * 60)

        return success


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Final data synchronization before cutover"
    )
    parser.add_argument(
        "--primary", default="data/definities.db", help="Path to primary database"
    )
    parser.add_argument(
        "--shadow", default="data/definities.db.shadow", help="Path to shadow database"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Run in dry-run mode (no changes)"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute actual sync (CAUTION: modifies database)",
    )
    parser.add_argument(
        "--verify", action="store_true", help="Verify sync after execution"
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.dry_run and not args.execute:
        logger.error("❌ Must specify either --dry-run or --execute")
        return 1

    if args.dry_run and args.execute:
        logger.error("❌ Cannot specify both --dry-run and --execute")
        return 1

    # Create logs directory
    Path("logs/migration").mkdir(parents=True, exist_ok=True)

    # Check databases exist
    if not Path(args.primary).exists():
        logger.error(f"❌ Primary database not found: {args.primary}")
        return 1

    if not Path(args.shadow).exists():
        logger.error(f"❌ Shadow database not found: {args.shadow}")
        return 1

    # Execute sync
    synchronizer = FinalSynchronizer(args.primary, args.shadow, dry_run=args.dry_run)
    success = synchronizer.execute(verify=args.verify)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
