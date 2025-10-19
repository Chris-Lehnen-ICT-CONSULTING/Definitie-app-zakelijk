#!/usr/bin/env python3
"""
Archive Old Data Utility

Features:
- Archive definitions older than specified days
- Move to archive database/directory
- Maintain referential integrity
- Generate archive reports
- Dry-run mode for testing
"""

import argparse
import logging
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/archive.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class DataArchiver:
    """Handles archiving of old data."""

    def __init__(self, source_db: str, archive_db: str, dry_run: bool = False):
        """
        Initialize data archiver.

        Args:
            source_db: Path to source database
            archive_db: Path to archive database
            dry_run: If True, don't commit changes
        """
        self.source_db = Path(source_db)
        self.archive_db = Path(archive_db)
        self.dry_run = dry_run

        self.stats = {"definitions": 0, "examples": 0, "history": 0, "tags": 0}

        # Validate source database
        if not self.source_db.exists():
            msg = f"Source database not found: {self.source_db}"
            raise FileNotFoundError(msg)

        # Ensure archive directory exists
        self.archive_db.parent.mkdir(parents=True, exist_ok=True)

    def initialize_archive_db(self, source_conn: sqlite3.Connection):
        """Initialize archive database with same schema as source."""
        logger.info(f"Initializing archive database: {self.archive_db}")

        archive_conn = sqlite3.connect(str(self.archive_db))

        # Get schema from source
        cursor = source_conn.cursor()
        cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL"
        )

        for (create_statement,) in cursor.fetchall():
            try:
                archive_conn.execute(create_statement)
            except sqlite3.OperationalError as e:
                # Table might already exist
                logger.debug(f"Table creation skipped: {e}")

        archive_conn.commit()
        archive_conn.close()

        logger.info("Archive database initialized")

    def archive_definitions(
        self,
        source_conn: sqlite3.Connection,
        archive_conn: sqlite3.Connection,
        cutoff_date: datetime,
        status_filter: list[str] | None = None,
    ) -> tuple[int, int]:
        """
        Archive old definitions.

        Args:
            source_conn: Source database connection
            archive_conn: Archive database connection
            cutoff_date: Archive definitions older than this date
            status_filter: Only archive definitions with these statuses

        Returns:
            Tuple of (archived_count, skipped_count)
        """
        logger.info(f"Archiving definitions older than {cutoff_date}")

        # Build query
        query = """
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
            WHERE updated_at < ?
        """

        params = [cutoff_date.isoformat()]

        if status_filter:
            placeholders = ",".join("?" * len(status_filter))
            query += f" AND status IN ({placeholders})"
            params.extend(status_filter)

        query += " ORDER BY id"

        cursor = source_conn.execute(query, params)
        rows = cursor.fetchall()

        logger.info(f"Found {len(rows)} definitions to archive")

        archived = 0
        skipped = 0
        definition_ids = []

        for row in rows:
            definition_id = row[0]

            try:
                # Check if already archived
                archive_cursor = archive_conn.execute(
                    "SELECT id FROM definities WHERE id = ?", (definition_id,)
                )

                if archive_cursor.fetchone():
                    logger.debug(
                        f"Definition {definition_id} already archived, skipping"
                    )
                    skipped += 1
                    continue

                # Insert into archive
                archive_conn.execute(
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
                    row,
                )

                definition_ids.append(definition_id)
                archived += 1

            except Exception as e:
                logger.error(f"Failed to archive definition {definition_id}: {e}")

        self.stats["definitions"] = archived
        logger.info(f"Archived {archived} definitions, skipped {skipped}")

        return archived, skipped

    def archive_related_data(
        self,
        source_conn: sqlite3.Connection,
        archive_conn: sqlite3.Connection,
        definition_ids: list[int],
    ):
        """Archive data related to archived definitions."""
        if not definition_ids:
            return

        placeholders = ",".join("?" * len(definition_ids))

        # Archive examples
        logger.info("Archiving related examples...")
        cursor = source_conn.execute(
            f"""
            SELECT
                id, definitie_id, voorbeeld_type, voorbeeld_tekst, voorbeeld_volgorde,
                gegenereerd_door, generation_model, generation_parameters,
                actief, beoordeeld, beoordeeling, beoordeeling_notities,
                beoordeeld_door, beoordeeld_op,
                aangemaakt_op, bijgewerkt_op
            FROM definitie_voorbeelden
            WHERE definitie_id IN ({placeholders})
        """,
            definition_ids,
        )

        for row in cursor.fetchall():
            try:
                archive_conn.execute(
                    """
                    INSERT OR IGNORE INTO definitie_voorbeelden (
                        id, definitie_id, voorbeeld_type, voorbeeld_tekst, voorbeeld_volgorde,
                        gegenereerd_door, generation_model, generation_parameters,
                        actief, beoordeeld, beoordeeling, beoordeeling_notities,
                        beoordeeld_door, beoordeeld_op,
                        aangemaakt_op, bijgewerkt_op
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    row,
                )
                self.stats["examples"] += 1
            except Exception as e:
                logger.error(f"Failed to archive example {row[0]}: {e}")

        # Archive history
        logger.info("Archiving related history...")
        cursor = source_conn.execute(
            f"""
            SELECT
                id, definitie_id, begrip, definitie_oude_waarde, definitie_nieuwe_waarde,
                wijziging_type, wijziging_reden,
                gewijzigd_door, gewijzigd_op,
                context_snapshot
            FROM definitie_geschiedenis
            WHERE definitie_id IN ({placeholders})
        """,
            definition_ids,
        )

        for row in cursor.fetchall():
            try:
                archive_conn.execute(
                    """
                    INSERT OR IGNORE INTO definitie_geschiedenis (
                        id, definitie_id, begrip, definitie_oude_waarde, definitie_nieuwe_waarde,
                        wijziging_type, wijziging_reden,
                        gewijzigd_door, gewijzigd_op,
                        context_snapshot
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    row,
                )
                self.stats["history"] += 1
            except Exception as e:
                logger.error(f"Failed to archive history {row[0]}: {e}")

        # Archive tags
        logger.info("Archiving related tags...")
        cursor = source_conn.execute(
            f"""
            SELECT
                id, definitie_id, tag_naam, tag_waarde,
                toegevoegd_door, toegevoegd_op
            FROM definitie_tags
            WHERE definitie_id IN ({placeholders})
        """,
            definition_ids,
        )

        for row in cursor.fetchall():
            try:
                archive_conn.execute(
                    """
                    INSERT OR IGNORE INTO definitie_tags (
                        id, definitie_id, tag_naam, tag_waarde,
                        toegevoegd_door, toegevoegd_op
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                    row,
                )
                self.stats["tags"] += 1
            except Exception as e:
                logger.error(f"Failed to archive tag {row[0]}: {e}")

        logger.info(
            f"Archived {self.stats['examples']} examples, "
            f"{self.stats['history']} history entries, "
            f"{self.stats['tags']} tags"
        )

    def delete_archived_data(
        self, source_conn: sqlite3.Connection, definition_ids: list[int]
    ):
        """Delete archived data from source database."""
        if not definition_ids:
            return

        logger.info(
            f"Deleting {len(definition_ids)} archived definitions from source..."
        )

        placeholders = ",".join("?" * len(definition_ids))

        # Delete in correct order (respect foreign keys)
        source_conn.execute(
            f"DELETE FROM definitie_tags WHERE definitie_id IN ({placeholders})",
            definition_ids,
        )
        source_conn.execute(
            f"DELETE FROM definitie_voorbeelden WHERE definitie_id IN ({placeholders})",
            definition_ids,
        )
        source_conn.execute(
            f"DELETE FROM definitie_geschiedenis WHERE definitie_id IN ({placeholders})",
            definition_ids,
        )
        source_conn.execute(
            f"DELETE FROM definities WHERE id IN ({placeholders})", definition_ids
        )

        logger.info("Archived data deleted from source")

    def generate_report(self) -> str:
        """Generate archive report."""
        report = [
            "=" * 50,
            "ARCHIVE REPORT",
            "=" * 50,
            f"Archive Date: {datetime.now().isoformat()}",
            f"Source Database: {self.source_db}",
            f"Archive Database: {self.archive_db}",
            f"Dry Run: {self.dry_run}",
            "",
            "Archived Items:",
            f"  Definitions: {self.stats['definitions']}",
            f"  Examples: {self.stats['examples']}",
            f"  History: {self.stats['history']}",
            f"  Tags: {self.stats['tags']}",
            "",
            f"Total Items: {sum(self.stats.values())}",
            "=" * 50,
        ]

        return "\n".join(report)

    def run(
        self,
        days: int,
        status_filter: list[str] | None = None,
        delete_source: bool = False,
    ) -> int:
        """
        Execute the archive process.

        Args:
            days: Archive items older than this many days
            status_filter: Only archive items with these statuses
            delete_source: Delete archived items from source

        Returns:
            Exit code (0 = success, 1 = error)
        """
        logger.info("=" * 50)
        logger.info("Data Archive Process")
        logger.info("=" * 50)
        logger.info(f"Archive threshold: {days} days")
        logger.info(f"Status filter: {status_filter or 'None'}")
        logger.info(f"Delete from source: {delete_source}")
        logger.info(f"Dry run: {self.dry_run}")
        logger.info("=" * 50)

        cutoff_date = datetime.now() - timedelta(days=days)

        try:
            # Connect to databases
            source_conn = sqlite3.connect(str(self.source_db))

            # Initialize archive database if needed
            if not self.archive_db.exists():
                self.initialize_archive_db(source_conn)

            archive_conn = sqlite3.connect(str(self.archive_db))

            # Enable foreign keys
            source_conn.execute("PRAGMA foreign_keys = ON")
            archive_conn.execute("PRAGMA foreign_keys = ON")

            try:
                # Archive definitions
                archived, skipped = self.archive_definitions(
                    source_conn, archive_conn, cutoff_date, status_filter
                )

                # Get archived definition IDs
                cursor = archive_conn.execute("SELECT id FROM definities")
                definition_ids = [row[0] for row in cursor.fetchall()]

                # Archive related data
                self.archive_related_data(source_conn, archive_conn, definition_ids)

                # Delete from source if requested
                if delete_source and not self.dry_run:
                    self.delete_archived_data(source_conn, definition_ids)

                # Commit if not dry run
                if not self.dry_run:
                    archive_conn.commit()
                    if delete_source:
                        source_conn.commit()
                    logger.info("Changes committed")
                else:
                    logger.info("DRY RUN: Changes not committed")

                # Generate and print report
                report = self.generate_report()
                print(report)

                # Save report
                report_path = (
                    Path("logs")
                    / f"archive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                )
                report_path.write_text(report)
                logger.info(f"Report saved to: {report_path}")

                return 0

            finally:
                source_conn.close()
                archive_conn.close()

        except Exception as e:
            logger.error(f"Archive process failed: {e}", exc_info=True)
            return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Archive old data from database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run - archive items older than 180 days
  python scripts/archive_data.py --days 180 --dry-run

  # Archive and keep in source
  python scripts/archive_data.py --days 365

  # Archive and delete from source
  python scripts/archive_data.py --days 365 --delete-source

  # Archive only specific statuses
  python scripts/archive_data.py --days 180 --status archived rejected --delete-source
        """,
    )

    parser.add_argument(
        "--days",
        type=int,
        default=365,
        help="Archive items older than this many days (default: 365)",
    )

    parser.add_argument(
        "--source-db",
        type=str,
        default="data/definities.db",
        help="Source database path (default: data/definities.db)",
    )

    parser.add_argument(
        "--archive-db",
        type=str,
        default="data/archive/definities_archive.db",
        help="Archive database path (default: data/archive/definities_archive.db)",
    )

    parser.add_argument(
        "--status",
        nargs="+",
        help="Only archive definitions with these statuses (e.g., --status archived rejected)",
    )

    parser.add_argument(
        "--delete-source",
        action="store_true",
        help="Delete archived items from source database",
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="Run without committing changes"
    )

    args = parser.parse_args()

    # Ensure log directory exists
    Path("logs").mkdir(exist_ok=True)

    # Create archiver and run
    archiver = DataArchiver(
        source_db=args.source_db, archive_db=args.archive_db, dry_run=args.dry_run
    )

    exit_code = archiver.run(
        days=args.days, status_filter=args.status, delete_source=args.delete_source
    )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
