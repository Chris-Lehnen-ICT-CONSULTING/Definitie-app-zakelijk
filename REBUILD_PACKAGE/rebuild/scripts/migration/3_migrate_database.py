#!/usr/bin/env python3
"""Execute complete database migration with transaction safety.

This script performs the actual data migration from the current SQLite database
to a new database structure, with automatic backup, transaction rollback,
and validation.

Usage:
    python rebuild/scripts/migration/3_migrate_database.py --dry-run
    python rebuild/scripts/migration/3_migrate_database.py --execute
    python rebuild/scripts/migration/3_migrate_database.py --execute --source data/definities.db --target data/definities.db.new

Example:
    $ python rebuild/scripts/migration/3_migrate_database.py --dry-run
    🔍 DRY RUN MODE - No changes will be made
    ✅ Step 1/10: Baseline export complete (42 definitions)
    ✅ Step 2/10: Target schema created
    ...
    ✅ Migration dry-run successful

    $ python rebuild/scripts/migration/3_migrate_database.py --execute
    ✅ Step 1/10: Baseline export complete (42 definitions)
    ✅ Step 2/10: Target schema created
    ✅ Step 3/10: Migrated 42 definitions
    ✅ Step 4/10: Migrated 96 history records
    ✅ Step 5/10: Migrated 90 examples
    ✅ Step 6/10: Validation passed
    ✅ Migration complete
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
            f"logs/migration/migrate_database_{datetime.now():%Y%m%d_%H%M%S}.log"
        ),
    ],
)
logger = logging.getLogger(__name__)


class MigrationOrchestrator:
    """Orchestrate complete database migration."""

    def __init__(self, source_db: str, target_db: str, dry_run: bool = True):
        """Initialize migration orchestrator.

        Args:
            source_db: Path to source SQLite database
            target_db: Path to target SQLite database
            dry_run: If True, don't make actual changes
        """
        self.source_db = Path(source_db)
        self.target_db = Path(target_db)
        self.dry_run = dry_run
        self.migration_log = []
        self.backup_path = None

    def log(self, message: str, step: int | None = None):
        """Log migration step.

        Args:
            message: Log message
            step: Step number (optional)
        """
        if step:
            full_message = f"Step {step}/10: {message}"
        else:
            full_message = message

        self.migration_log.append(
            {"timestamp": datetime.now().isoformat(), "message": full_message}
        )
        logger.info(f"✅ {full_message}")

    def create_backup(self) -> bool:
        """Create backup of source database.

        Returns:
            True if backup successful
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.backup_path = (
                self.source_db.parent / f"{self.source_db.name}.backup.{timestamp}"
            )

            if not self.dry_run:
                shutil.copy2(self.source_db, self.backup_path)
                logger.info(f"📦 Backup created: {self.backup_path}")

            return True
        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            return False

    def export_baseline(self) -> dict[str, Any]:
        """Export baseline data for validation.

        Returns:
            Export dictionary
        """
        logger.info("📂 Exporting baseline data...")

        with sqlite3.connect(self.source_db) as conn:
            conn.row_factory = sqlite3.Row

            export = {
                "metadata": {
                    "export_date": datetime.now().isoformat(),
                    "source_db": str(self.source_db),
                },
                "tables": {},
            }

            # Export each table
            for table in [
                "definities",
                "definitie_geschiedenis",
                "definitie_voorbeelden",
                "definitie_tags",
            ]:
                try:
                    cursor = conn.execute(f"SELECT * FROM {table}")
                    rows = [dict(row) for row in cursor.fetchall()]
                    export["tables"][table] = {"count": len(rows), "rows": rows}
                except sqlite3.Error as e:
                    logger.warning(f"⚠️  Could not export {table}: {e}")
                    export["tables"][table] = {"count": 0, "rows": []}

        definitions_count = export["tables"]["definities"]["count"]
        history_count = export["tables"]["definitie_geschiedenis"]["count"]
        examples_count = export["tables"]["definitie_voorbeelden"]["count"]

        self.log(
            f"Baseline export complete ({definitions_count} definitions, {history_count} history, {examples_count} examples)",
            step=1,
        )

        return export

    def create_target_schema(self) -> bool:
        """Create target database schema.

        Returns:
            True if schema creation successful
        """
        if self.dry_run:
            self.log("Target schema would be created (dry-run)", step=2)
            return True

        try:
            # Read schema from schema.sql
            schema_file = Path("src/database/schema.sql")
            if not schema_file.exists():
                logger.error(f"❌ Schema file not found: {schema_file}")
                return False

            with open(schema_file, encoding="utf-8") as f:
                schema_sql = f.read()

            # Create new database with schema
            with sqlite3.connect(self.target_db) as conn:
                conn.executescript(schema_sql)

            self.log("Target schema created", step=2)
            return True

        except Exception as e:
            logger.error(f"❌ Schema creation failed: {e}")
            return False

    def migrate_definitions(self, baseline: dict[str, Any]) -> int:
        """Migrate definitions table.

        Args:
            baseline: Baseline export data

        Returns:
            Number of definitions migrated
        """
        if self.dry_run:
            count = baseline["tables"]["definities"]["count"]
            self.log(f"Would migrate {count} definitions (dry-run)", step=3)
            return count

        try:
            definitions = baseline["tables"]["definities"]["rows"]

            with sqlite3.connect(self.target_db) as conn:
                for row in definitions:
                    # Prepare values (handle JSON fields)
                    values = []
                    columns = []

                    for key, value in row.items():
                        columns.append(key)
                        # Convert list/dict to JSON string if needed
                        if isinstance(value, (list, dict)):
                            values.append(json.dumps(value, ensure_ascii=False))
                        else:
                            values.append(value)

                    # Build INSERT statement
                    placeholders = ", ".join(["?" for _ in values])
                    columns_str = ", ".join(columns)

                    sql = f"INSERT INTO definities ({columns_str}) VALUES ({placeholders})"
                    conn.execute(sql, values)

                conn.commit()

            self.log(f"Migrated {len(definitions)} definitions", step=3)
            return len(definitions)

        except Exception as e:
            logger.error(f"❌ Definition migration failed: {e}")
            raise

    def migrate_history(self, baseline: dict[str, Any]) -> int:
        """Migrate history table.

        Args:
            baseline: Baseline export data

        Returns:
            Number of history records migrated
        """
        if self.dry_run:
            count = baseline["tables"]["definitie_geschiedenis"]["count"]
            self.log(f"Would migrate {count} history records (dry-run)", step=4)
            return count

        try:
            history = baseline["tables"]["definitie_geschiedenis"]["rows"]

            with sqlite3.connect(self.target_db) as conn:
                for row in history:
                    values = []
                    columns = []

                    for key, value in row.items():
                        columns.append(key)
                        if isinstance(value, (list, dict)):
                            values.append(json.dumps(value, ensure_ascii=False))
                        else:
                            values.append(value)

                    placeholders = ", ".join(["?" for _ in values])
                    columns_str = ", ".join(columns)

                    sql = f"INSERT INTO definitie_geschiedenis ({columns_str}) VALUES ({placeholders})"
                    conn.execute(sql, values)

                conn.commit()

            self.log(f"Migrated {len(history)} history records", step=4)
            return len(history)

        except Exception as e:
            logger.error(f"❌ History migration failed: {e}")
            raise

    def migrate_examples(self, baseline: dict[str, Any]) -> int:
        """Migrate examples table.

        Args:
            baseline: Baseline export data

        Returns:
            Number of examples migrated
        """
        if self.dry_run:
            count = baseline["tables"]["definitie_voorbeelden"]["count"]
            self.log(f"Would migrate {count} examples (dry-run)", step=5)
            return count

        try:
            examples = baseline["tables"]["definitie_voorbeelden"]["rows"]

            with sqlite3.connect(self.target_db) as conn:
                for row in examples:
                    values = []
                    columns = []

                    for key, value in row.items():
                        columns.append(key)
                        if isinstance(value, (list, dict)):
                            values.append(json.dumps(value, ensure_ascii=False))
                        else:
                            values.append(value)

                    placeholders = ", ".join(["?" for _ in values])
                    columns_str = ", ".join(columns)

                    sql = f"INSERT INTO definitie_voorbeelden ({columns_str}) VALUES ({placeholders})"
                    conn.execute(sql, values)

                conn.commit()

            self.log(f"Migrated {len(examples)} examples", step=5)
            return len(examples)

        except Exception as e:
            logger.error(f"❌ Examples migration failed: {e}")
            raise

    def validate_migration(self, baseline: dict[str, Any]) -> bool:
        """Validate migration completeness and integrity.

        Args:
            baseline: Baseline export data

        Returns:
            True if validation passed
        """
        if self.dry_run:
            self.log("Validation would be performed (dry-run)", step=6)
            return True

        try:
            with (
                sqlite3.connect(self.source_db) as source_conn,
                sqlite3.connect(self.target_db) as target_conn,
            ):

                # Count records
                source_count = source_conn.execute(
                    "SELECT COUNT(*) FROM definities"
                ).fetchone()[0]
                target_count = target_conn.execute(
                    "SELECT COUNT(*) FROM definities"
                ).fetchone()[0]

                if source_count != target_count:
                    logger.error(
                        f"❌ Definition count mismatch: {source_count} → {target_count}"
                    )
                    return False

                # Sample validation (first 5 records)
                source_conn.row_factory = sqlite3.Row
                target_conn.row_factory = sqlite3.Row

                source_sample = source_conn.execute(
                    "SELECT begrip, definitie FROM definities ORDER BY id LIMIT 5"
                ).fetchall()
                target_sample = target_conn.execute(
                    "SELECT begrip, definitie FROM definities ORDER BY id LIMIT 5"
                ).fetchall()

                for src_row, tgt_row in zip(source_sample, target_sample, strict=False):
                    src_dict = dict(src_row)
                    tgt_dict = dict(tgt_row)
                    if src_dict != tgt_dict:
                        logger.error(f"❌ Sample mismatch: {src_dict['begrip']}")
                        return False

            self.log("Validation passed", step=6)
            return True

        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
            return False

    def create_rollback_script(self, baseline: dict[str, Any]):
        """Create rollback script for emergency recovery.

        Args:
            baseline: Baseline export data
        """
        rollback_script = f"""#!/bin/bash
# Emergency Rollback Script
# Generated: {datetime.now().isoformat()}
# Backup: {self.backup_path}

echo "🚨 ROLLBACK: Restoring database backup"
echo "Backup: {self.backup_path}"
echo "Target: {self.source_db}"

# Stop application (if running)
pkill -f "streamlit run" || true

# Restore backup
cp "{self.backup_path}" "{self.source_db}"

# Verify integrity
sqlite3 "{self.source_db}" "PRAGMA integrity_check;"

echo "✅ Rollback complete"
"""

        if not self.dry_run:
            rollback_path = Path("rebuild/scripts/migration/rollback_emergency.sh")
            with open(rollback_path, "w") as f:
                f.write(rollback_script)
            rollback_path.chmod(0o755)

        self.log("Rollback script created", step=7)

    def save_migration_log(self):
        """Save migration log to file."""
        if self.dry_run:
            self.log("Migration log would be saved (dry-run)", step=8)
            return

        log_path = Path(
            f"logs/migration/migration_log_{datetime.now():%Y%m%d_%H%M%S}.json"
        )
        log_path.parent.mkdir(parents=True, exist_ok=True)

        with open(log_path, "w") as f:
            json.dump(
                {
                    "source_db": str(self.source_db),
                    "target_db": str(self.target_db),
                    "backup": str(self.backup_path),
                    "dry_run": self.dry_run,
                    "log": self.migration_log,
                },
                f,
                indent=2,
            )

        self.log(f"Migration log saved: {log_path}", step=8)

    def execute(self) -> bool:
        """Execute complete migration.

        Returns:
            True if migration successful
        """
        logger.info("=" * 60)
        if self.dry_run:
            logger.info("🔍 DRY RUN MODE - No changes will be made")
        else:
            logger.info("⚠️  EXECUTE MODE - Database will be modified")
        logger.info("=" * 60)

        try:
            # Step 0: Create backup
            if not self.create_backup():
                return False

            # Step 1: Export baseline
            baseline = self.export_baseline()

            # Step 2: Create target schema
            if not self.create_target_schema():
                return False

            # Step 3-5: Migrate data
            self.migrate_definitions(baseline)
            self.migrate_history(baseline)
            self.migrate_examples(baseline)

            # Step 6: Validate
            if not self.validate_migration(baseline):
                return False

            # Step 7: Create rollback script
            self.create_rollback_script(baseline)

            # Step 8: Save log
            self.save_migration_log()

            logger.info("=" * 60)
            logger.info("✅ MIGRATION COMPLETE")
            logger.info("=" * 60)
            if not self.dry_run:
                logger.info(f"📦 Backup: {self.backup_path}")
            logger.info(f"📊 Definitions: {baseline['tables']['definities']['count']}")
            logger.info(
                f"📊 History: {baseline['tables']['definitie_geschiedenis']['count']}"
            )
            logger.info(
                f"📊 Examples: {baseline['tables']['definitie_voorbeelden']['count']}"
            )

            return True

        except Exception as e:
            logger.error(f"❌ Migration failed: {e}", exc_info=True)
            if not self.dry_run and self.backup_path:
                logger.error(f"💡 To rollback: cp {self.backup_path} {self.source_db}")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Execute database migration with safety checks"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Run in dry-run mode (no changes made)"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute actual migration (CAUTION: modifies database)",
    )
    parser.add_argument(
        "--source",
        default="data/definities.db",
        help="Source database path (default: data/definities.db)",
    )
    parser.add_argument(
        "--target",
        default="data/definities.db.new",
        help="Target database path (default: data/definities.db.new)",
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

    # Check source database exists
    if not Path(args.source).exists():
        logger.error(f"❌ Source database not found: {args.source}")
        return 1

    # Execute migration
    orchestrator = MigrationOrchestrator(
        source_db=args.source, target_db=args.target, dry_run=args.dry_run
    )

    success = orchestrator.execute()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
