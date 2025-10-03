#!/usr/bin/env python3
"""
Migrate data from legacy SQLite to new database schema.

This script handles migration of:
- Definitions (definities table)
- Definition examples (definitie_voorbeelden)
- Definition history (definitie_geschiedenis)
- Definition tags (definitie_tags)

Features:
- Dry-run mode for safe testing
- Progress tracking with tqdm
- Rollback support on failure
- Data validation during migration
- Comprehensive logging
"""

import argparse
import json
import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/migration.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class DataMigrator:
    """Handles data migration from legacy SQLite to new schema."""

    def __init__(
        self, source_db: str, target_db: str, dry_run: bool = False, backup: bool = True
    ):
        """
        Initialize the data migrator.

        Args:
            source_db: Path to source SQLite database
            target_db: Path to target SQLite database
            dry_run: If True, don't commit changes
            backup: If True, create backup before migration
        """
        self.source_db = Path(source_db)
        self.target_db = Path(target_db)
        self.dry_run = dry_run
        self.backup = backup

        self.stats: dict[str, dict[str, int]] = {
            "definitions": {"migrated": 0, "failed": 0, "skipped": 0},
            "examples": {"migrated": 0, "failed": 0, "skipped": 0},
            "history": {"migrated": 0, "failed": 0, "skipped": 0},
            "tags": {"migrated": 0, "failed": 0, "skipped": 0},
        }

        # Validate source database exists
        if not self.source_db.exists():
            raise FileNotFoundError(f"Source database not found: {self.source_db}")

    def create_backup(self) -> Path | None:
        """Create backup of target database if it exists."""
        if not self.target_db.exists():
            logger.info("Target database doesn't exist yet, skipping backup")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = (
            self.target_db.parent / f"{self.target_db.stem}_backup_{timestamp}.db"
        )

        try:
            import shutil

            shutil.copy2(self.target_db, backup_path)
            logger.info(f"Backup created: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise

    def migrate_definitions(
        self, source_conn: sqlite3.Connection, target_conn: sqlite3.Connection
    ) -> tuple[int, int]:
        """Migrate definitions table."""
        logger.info("Migrating definitions...")

        cursor = source_conn.execute(
            """
            SELECT
                id, begrip, definitie, categorie,
                organisatorische_context, juridische_context, wettelijke_basis,
                ufo_categorie, status, version_number, previous_version_id,
                validation_score, validation_date, validation_issues,
                source_type, source_reference, imported_from,
                created_at, updated_at, created_by, updated_by,
                approved_by, approved_at, approval_notes,
                last_exported_at, export_destinations,
                datum_voorstel, ketenpartners, voorkeursterm, toelichting_proces
            FROM definities
            WHERE status != 'archived'
            ORDER BY id
        """
        )

        rows = cursor.fetchall()
        logger.info(f"Found {len(rows)} definitions to migrate")

        migrated = 0
        failed = 0

        try:
            from tqdm import tqdm

            iterator = tqdm(rows, desc="Definitions", disable=self.dry_run)
        except ImportError:
            iterator = rows
            logger.warning("tqdm not available, progress bar disabled")

        for row in iterator:
            try:
                # Parse JSON fields
                org_context = self._parse_json_field(row[4])
                jur_context = self._parse_json_field(row[5])
                wet_basis = self._parse_json_field(row[6])
                validation_issues = self._parse_json_field(row[13])
                export_dest = self._parse_json_field(row[25])
                ketenpartners = self._parse_json_field(row[27])

                # Insert into target
                target_conn.execute(
                    """
                    INSERT INTO definities (
                        id, begrip, definitie, categorie,
                        organisatorische_context, juridische_context, wettelijke_basis,
                        ufo_categorie, status, version_number, previous_version_id,
                        validation_score, validation_date, validation_issues,
                        source_type, source_reference, imported_from,
                        created_at, updated_at, created_by, updated_by,
                        approved_by, approved_at, approval_notes,
                        last_exported_at, export_destinations,
                        datum_voorstel, ketenpartners, voorkeursterm, toelichting_proces
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        row[0],
                        row[1],
                        row[2],
                        row[3],
                        json.dumps(org_context) if org_context else None,
                        json.dumps(jur_context) if jur_context else None,
                        json.dumps(wet_basis) if wet_basis else None,
                        row[7],
                        row[8],
                        row[9],
                        row[10],
                        row[11],
                        row[12],
                        json.dumps(validation_issues) if validation_issues else None,
                        row[14],
                        row[15],
                        row[16],
                        row[17],
                        row[18],
                        row[19],
                        row[20],
                        row[21],
                        row[22],
                        row[23],
                        row[24],
                        json.dumps(export_dest) if export_dest else None,
                        row[26],
                        json.dumps(ketenpartners) if ketenpartners else None,
                        row[28],
                        row[29],
                    ),
                )

                migrated += 1
                self.stats["definitions"]["migrated"] += 1

            except sqlite3.IntegrityError:
                logger.debug(f"Definition {row[0]} ({row[1]}) already exists, skipping")
                self.stats["definitions"]["skipped"] += 1
            except Exception as e:
                logger.error(f"Error migrating definition {row[0]} ({row[1]}): {e}")
                failed += 1
                self.stats["definitions"]["failed"] += 1

        logger.info(f"Definitions: {migrated} migrated, {failed} failed")
        return migrated, failed

    def migrate_examples(
        self, source_conn: sqlite3.Connection, target_conn: sqlite3.Connection
    ) -> tuple[int, int]:
        """Migrate definition examples."""
        logger.info("Migrating examples...")

        cursor = source_conn.execute(
            """
            SELECT
                id, definitie_id, voorbeeld_type, voorbeeld_tekst, voorbeeld_volgorde,
                gegenereerd_door, generation_model, generation_parameters,
                actief, beoordeeld, beoordeeling, beoordeeling_notities,
                beoordeeld_door, beoordeeld_op,
                aangemaakt_op, bijgewerkt_op
            FROM definitie_voorbeelden
        """
        )

        rows = cursor.fetchall()
        logger.info(f"Found {len(rows)} examples to migrate")

        migrated = 0
        failed = 0

        try:
            from tqdm import tqdm

            iterator = tqdm(rows, desc="Examples", disable=self.dry_run)
        except ImportError:
            iterator = rows

        for row in iterator:
            try:
                gen_params = self._parse_json_field(row[7])

                target_conn.execute(
                    """
                    INSERT INTO definitie_voorbeelden (
                        id, definitie_id, voorbeeld_type, voorbeeld_tekst, voorbeeld_volgorde,
                        gegenereerd_door, generation_model, generation_parameters,
                        actief, beoordeeld, beoordeeling, beoordeeling_notities,
                        beoordeeld_door, beoordeeld_op,
                        aangemaakt_op, bijgewerkt_op
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        row[0],
                        row[1],
                        row[2],
                        row[3],
                        row[4],
                        row[5],
                        row[6],
                        json.dumps(gen_params) if gen_params else None,
                        row[8],
                        row[9],
                        row[10],
                        row[11],
                        row[12],
                        row[13],
                        row[14],
                        row[15],
                    ),
                )

                migrated += 1
                self.stats["examples"]["migrated"] += 1

            except sqlite3.IntegrityError:
                self.stats["examples"]["skipped"] += 1
            except Exception as e:
                logger.error(f"Error migrating example {row[0]}: {e}")
                failed += 1
                self.stats["examples"]["failed"] += 1

        logger.info(f"Examples: {migrated} migrated, {failed} failed")
        return migrated, failed

    def migrate_history(
        self, source_conn: sqlite3.Connection, target_conn: sqlite3.Connection
    ) -> tuple[int, int]:
        """Migrate definition history."""
        logger.info("Migrating history...")

        cursor = source_conn.execute(
            """
            SELECT
                id, definitie_id, begrip, definitie_oude_waarde, definitie_nieuwe_waarde,
                wijziging_type, wijziging_reden,
                gewijzigd_door, gewijzigd_op,
                context_snapshot
            FROM definitie_geschiedenis
        """
        )

        rows = cursor.fetchall()
        logger.info(f"Found {len(rows)} history entries to migrate")

        migrated = 0
        failed = 0

        try:
            from tqdm import tqdm

            iterator = tqdm(rows, desc="History", disable=self.dry_run)
        except ImportError:
            iterator = rows

        for row in iterator:
            try:
                context_snap = self._parse_json_field(row[9])

                target_conn.execute(
                    """
                    INSERT INTO definitie_geschiedenis (
                        id, definitie_id, begrip, definitie_oude_waarde, definitie_nieuwe_waarde,
                        wijziging_type, wijziging_reden,
                        gewijzigd_door, gewijzigd_op,
                        context_snapshot
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        row[0],
                        row[1],
                        row[2],
                        row[3],
                        row[4],
                        row[5],
                        row[6],
                        row[7],
                        row[8],
                        json.dumps(context_snap) if context_snap else None,
                    ),
                )

                migrated += 1
                self.stats["history"]["migrated"] += 1

            except sqlite3.IntegrityError:
                self.stats["history"]["skipped"] += 1
            except Exception as e:
                logger.error(f"Error migrating history {row[0]}: {e}")
                failed += 1
                self.stats["history"]["failed"] += 1

        logger.info(f"History: {migrated} migrated, {failed} failed")
        return migrated, failed

    def migrate_tags(
        self, source_conn: sqlite3.Connection, target_conn: sqlite3.Connection
    ) -> tuple[int, int]:
        """Migrate definition tags."""
        logger.info("Migrating tags...")

        cursor = source_conn.execute(
            """
            SELECT
                id, definitie_id, tag_naam, tag_waarde,
                toegevoegd_door, toegevoegd_op
            FROM definitie_tags
        """
        )

        rows = cursor.fetchall()
        logger.info(f"Found {len(rows)} tags to migrate")

        migrated = 0
        failed = 0

        try:
            from tqdm import tqdm

            iterator = tqdm(rows, desc="Tags", disable=self.dry_run)
        except ImportError:
            iterator = rows

        for row in iterator:
            try:
                target_conn.execute(
                    """
                    INSERT INTO definitie_tags (
                        id, definitie_id, tag_naam, tag_waarde,
                        toegevoegd_door, toegevoegd_op
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (row[0], row[1], row[2], row[3], row[4], row[5]),
                )

                migrated += 1
                self.stats["tags"]["migrated"] += 1

            except sqlite3.IntegrityError:
                self.stats["tags"]["skipped"] += 1
            except Exception as e:
                logger.error(f"Error migrating tag {row[0]}: {e}")
                failed += 1
                self.stats["tags"]["failed"] += 1

        logger.info(f"Tags: {migrated} migrated, {failed} failed")
        return migrated, failed

    def verify_migration(
        self, source_conn: sqlite3.Connection, target_conn: sqlite3.Connection
    ) -> bool:
        """Verify migration completeness."""
        logger.info("\n" + "=" * 50)
        logger.info("MIGRATION VERIFICATION")
        logger.info("=" * 50)

        all_match = True

        tables = [
            ("definities", "Definitions"),
            ("definitie_voorbeelden", "Examples"),
            ("definitie_geschiedenis", "History"),
            ("definitie_tags", "Tags"),
        ]

        for table_name, display_name in tables:
            try:
                source_count = source_conn.execute(
                    f"SELECT COUNT(*) FROM {table_name}"
                ).fetchone()[0]

                target_count = target_conn.execute(
                    f"SELECT COUNT(*) FROM {table_name}"
                ).fetchone()[0]

                match = source_count == target_count
                all_match = all_match and match

                logger.info(f"\n{display_name}:")
                logger.info(f"  Source: {source_count}")
                logger.info(f"  Target: {target_count}")
                logger.info(f"  Match: {'✓ YES' if match else '✗ NO'}")

            except sqlite3.OperationalError as e:
                logger.warning(f"Could not verify {display_name}: {e}")

        return all_match

    def run(self) -> int:
        """
        Execute the migration.

        Returns:
            Exit code (0 = success, 1 = error, 2 = partial success)
        """
        logger.info("=" * 50)
        logger.info("DefinitieAgent Data Migration")
        logger.info(f"Source: {self.source_db}")
        logger.info(f"Target: {self.target_db}")
        logger.info(f"Dry Run: {self.dry_run}")
        logger.info("=" * 50)

        backup_path = None

        try:
            # Create backup if requested
            if self.backup and not self.dry_run:
                backup_path = self.create_backup()

            # Connect to databases
            logger.info(f"\nConnecting to source: {self.source_db}")
            source_conn = sqlite3.connect(str(self.source_db))

            logger.info(f"Connecting to target: {self.target_db}")
            target_conn = sqlite3.connect(str(self.target_db))

            # Enable foreign keys
            target_conn.execute("PRAGMA foreign_keys = ON")

            try:
                # Run migrations
                self.migrate_definitions(source_conn, target_conn)
                self.migrate_examples(source_conn, target_conn)
                self.migrate_history(source_conn, target_conn)
                self.migrate_tags(source_conn, target_conn)

                # Commit if not dry run
                if not self.dry_run:
                    target_conn.commit()
                    logger.info("\nChanges committed to database")
                else:
                    logger.info("\nDRY RUN: Changes NOT committed")

                # Verify
                all_match = self.verify_migration(source_conn, target_conn)

                # Print summary
                logger.info("\n" + "=" * 50)
                logger.info("MIGRATION SUMMARY")
                logger.info("=" * 50)

                for entity, stats in self.stats.items():
                    logger.info(f"\n{entity.capitalize()}:")
                    logger.info(f"  Migrated: {stats['migrated']}")
                    logger.info(f"  Skipped:  {stats['skipped']}")
                    logger.info(f"  Failed:   {stats['failed']}")

                total_migrated = sum(s["migrated"] for s in self.stats.values())
                total_failed = sum(s["failed"] for s in self.stats.values())

                logger.info("\n" + "=" * 50)
                logger.info(f"Total Migrated: {total_migrated}")
                logger.info(f"Total Failed: {total_failed}")
                logger.info("=" * 50)

                # Determine exit code
                if total_failed > 0:
                    logger.warning("\nMigration completed with errors")
                    return 2  # Partial success
                elif not all_match:
                    logger.warning("\nMigration completed but verification failed")
                    return 2
                else:
                    logger.info("\nMigration completed successfully!")
                    return 0

            finally:
                source_conn.close()
                target_conn.close()

        except Exception as e:
            logger.error(f"\nMigration failed: {e}", exc_info=True)

            # Restore from backup if available
            if backup_path and backup_path.exists():
                logger.info(f"Restoring from backup: {backup_path}")
                try:
                    import shutil

                    shutil.copy2(backup_path, self.target_db)
                    logger.info("Backup restored successfully")
                except Exception as restore_error:
                    logger.error(f"Failed to restore backup: {restore_error}")

            return 1

    @staticmethod
    def _parse_json_field(value: str | None) -> Any | None:
        """Parse JSON field, return None if invalid or empty."""
        if not value:
            return None

        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate data from legacy SQLite to new database schema",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to test migration
  python scripts/migrate_data.py --dry-run

  # Run migration with backup
  python scripts/migrate_data.py --source data/definities_old.db

  # Run migration without backup (dangerous!)
  python scripts/migrate_data.py --no-backup

  # Migrate to different target
  python scripts/migrate_data.py --target data/definities_new.db
        """,
    )

    parser.add_argument(
        "--source",
        type=str,
        default="data/definities.db",
        help="Source SQLite database path (default: data/definities.db)",
    )

    parser.add_argument(
        "--target",
        type=str,
        default="data/definities.db",
        help="Target SQLite database path (default: data/definities.db)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run migration without committing changes",
    )

    parser.add_argument(
        "--no-backup", action="store_true", help="Skip creating backup before migration"
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set logging level (default: INFO)",
    )

    args = parser.parse_args()

    # Configure logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # Ensure log directory exists
    Path("logs").mkdir(exist_ok=True)

    # Create migrator and run
    migrator = DataMigrator(
        source_db=args.source,
        target_db=args.target,
        dry_run=args.dry_run,
        backup=not args.no_backup,
    )

    exit_code = migrator.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
