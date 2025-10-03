#!/usr/bin/env python3
"""Validate migrated data integrity against baseline.

This script performs comprehensive post-migration validation, comparing the
migrated database against the baseline export to ensure 100% data integrity.

Usage:
    python rebuild/scripts/migration/4_validate_migration.py
    python rebuild/scripts/migration/4_validate_migration.py --source data/definities.db --target data/definities.db.new
    python rebuild/scripts/migration/4_validate_migration.py --baseline data/migration_baseline.json

Example:
    $ python rebuild/scripts/migration/4_validate_migration.py
    ✅ Record count validation passed (42/42)
    ✅ Content validation passed (42/42 definitions match)
    ✅ Foreign key integrity passed
    ✅ All validation tests passed (5/5)
"""

import argparse
import json
import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            f"logs/migration/validate_migration_{datetime.now():%Y%m%d_%H%M%S}.log"
        ),
    ],
)
logger = logging.getLogger(__name__)


class MigrationValidator:
    """Validate migrated database against baseline."""

    def __init__(
        self, source_db: str, target_db: str, baseline_file: str | None = None
    ):
        """Initialize validator.

        Args:
            source_db: Path to source database
            target_db: Path to target database
            baseline_file: Optional path to baseline JSON
        """
        self.source_db = Path(source_db)
        self.target_db = Path(target_db)
        self.baseline_file = Path(baseline_file) if baseline_file else None
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0

    def add_pass(self, test_name: str):
        """Record passing test."""
        self.tests_run += 1
        self.tests_passed += 1
        logger.info(f"✅ {test_name}")

    def add_fail(self, test_name: str, message: str):
        """Record failing test."""
        self.tests_run += 1
        self.tests_failed += 1
        logger.error(f"❌ {test_name}: {message}")

    def validate_record_counts(self) -> bool:
        """Validate record counts match between source and target.

        Returns:
            True if counts match
        """
        logger.info("\n🔍 Validating record counts...")

        try:
            with (
                sqlite3.connect(self.source_db) as source_conn,
                sqlite3.connect(self.target_db) as target_conn,
            ):

                tables = [
                    ("definities", "definitions"),
                    ("definitie_geschiedenis", "history"),
                    ("definitie_voorbeelden", "examples"),
                ]

                all_match = True
                for source_table, display_name in tables:
                    source_count = source_conn.execute(
                        f"SELECT COUNT(*) FROM {source_table}"
                    ).fetchone()[0]
                    target_count = target_conn.execute(
                        f"SELECT COUNT(*) FROM {source_table}"
                    ).fetchone()[0]

                    if source_count != target_count:
                        self.add_fail(
                            f"Record count ({display_name})",
                            f"{source_count} → {target_count}",
                        )
                        all_match = False
                    else:
                        logger.info(f"  ✓ {display_name}: {source_count} records")

                if all_match:
                    self.add_pass("Record count validation")
                    return True
                return False

        except Exception as e:
            self.add_fail("Record count validation", str(e))
            return False

    def validate_content_integrity(self) -> bool:
        """Validate content matches exactly between source and target.

        Returns:
            True if content matches
        """
        logger.info("\n🔍 Validating content integrity...")

        try:
            with (
                sqlite3.connect(self.source_db) as source_conn,
                sqlite3.connect(self.target_db) as target_conn,
            ):

                source_conn.row_factory = sqlite3.Row
                target_conn.row_factory = sqlite3.Row

                # Get all definitions from both
                source_defs = source_conn.execute(
                    "SELECT id, begrip, definitie, categorie FROM definities ORDER BY id"
                ).fetchall()
                target_defs = target_conn.execute(
                    "SELECT id, begrip, definitie, categorie FROM definities ORDER BY id"
                ).fetchall()

                mismatches = []
                for src, tgt in zip(source_defs, target_defs, strict=False):
                    if dict(src) != dict(tgt):
                        mismatches.append(
                            {
                                "id": src["id"],
                                "begrip": src["begrip"],
                                "source": dict(src),
                                "target": dict(tgt),
                            }
                        )

                if mismatches:
                    self.add_fail(
                        "Content integrity",
                        f"Found {len(mismatches)} mismatched definitions",
                    )
                    for mismatch in mismatches[:5]:
                        logger.error(
                            f"  Mismatch ID {mismatch['id']}: {mismatch['begrip']}"
                        )
                    return False

                self.add_pass(
                    f"Content validation ({len(source_defs)}/{len(target_defs)} definitions match)"
                )
                return True

        except Exception as e:
            self.add_fail("Content integrity validation", str(e))
            return False

    def validate_foreign_keys(self) -> bool:
        """Validate foreign key relationships are intact.

        Returns:
            True if foreign keys valid
        """
        logger.info("\n🔍 Validating foreign key integrity...")

        try:
            with sqlite3.connect(self.target_db) as conn:
                # Enable foreign keys
                conn.execute("PRAGMA foreign_keys = ON")

                # Check for FK violations
                violations = conn.execute("PRAGMA foreign_key_check").fetchall()

                if violations:
                    self.add_fail(
                        "Foreign key integrity", f"Found {len(violations)} violations"
                    )
                    for violation in violations[:5]:
                        logger.error(f"  FK violation: {violation}")
                    return False

                self.add_pass("Foreign key integrity")
                return True

        except Exception as e:
            self.add_fail("Foreign key validation", str(e))
            return False

    def validate_indexes(self) -> bool:
        """Validate all indexes were created correctly.

        Returns:
            True if indexes valid
        """
        logger.info("\n🔍 Validating indexes...")

        try:
            with sqlite3.connect(self.target_db) as conn:
                # Get list of indexes
                indexes = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
                ).fetchall()

                required_indexes = [
                    "idx_definities_begrip",
                    "idx_definities_status",
                    "idx_definities_categorie",
                ]

                missing = []
                for req_idx in required_indexes:
                    if not any(idx[0] == req_idx for idx in indexes):
                        missing.append(req_idx)

                if missing:
                    self.add_fail(
                        "Index validation", f"Missing indexes: {', '.join(missing)}"
                    )
                    return False

                logger.info(f"  ✓ Found {len(indexes)} indexes")
                self.add_pass("Index validation")
                return True

        except Exception as e:
            self.add_fail("Index validation", str(e))
            return False

    def validate_utf8_encoding(self) -> bool:
        """Validate UTF-8 encoding for Dutch characters.

        Returns:
            True if encoding valid
        """
        logger.info("\n🔍 Validating UTF-8 encoding...")

        try:
            with sqlite3.connect(self.target_db) as conn:
                # Get definitions with special characters
                cursor = conn.execute(
                    "SELECT id, begrip, definitie FROM definities WHERE begrip LIKE '%ë%' OR begrip LIKE '%ï%' OR definitie LIKE '%ë%'"
                )
                rows = cursor.fetchall()

                encoding_errors = []
                for row in rows:
                    try:
                        row[1].encode("utf-8").decode("utf-8")
                        row[2].encode("utf-8").decode("utf-8")
                    except UnicodeError as e:
                        encoding_errors.append((row[0], str(e)))

                if encoding_errors:
                    self.add_fail(
                        "UTF-8 encoding",
                        f"Found {len(encoding_errors)} encoding errors",
                    )
                    return False

                logger.info(
                    f"  ✓ Validated {len(rows)} definitions with special characters"
                )
                self.add_pass("UTF-8 encoding validation")
                return True

        except Exception as e:
            self.add_fail("UTF-8 encoding validation", str(e))
            return False

    def validate_against_baseline(self) -> bool:
        """Validate against baseline JSON export.

        Returns:
            True if matches baseline
        """
        if not self.baseline_file or not self.baseline_file.exists():
            logger.info("\n⏭️  Skipping baseline validation (no baseline file)")
            return True

        logger.info(f"\n🔍 Validating against baseline: {self.baseline_file}")

        try:
            with open(self.baseline_file, encoding="utf-8") as f:
                baseline = json.load(f)

            with sqlite3.connect(self.target_db) as conn:
                # Check counts
                baseline_count = baseline["tables"]["definities"]["count"]
                target_count = conn.execute(
                    "SELECT COUNT(*) FROM definities"
                ).fetchone()[0]

                if baseline_count != target_count:
                    self.add_fail(
                        "Baseline validation",
                        f"Count mismatch: {baseline_count} → {target_count}",
                    )
                    return False

                # Sample check (first 5)
                baseline_sample = baseline["tables"]["definities"]["rows"][:5]
                conn.row_factory = sqlite3.Row
                target_sample = conn.execute(
                    "SELECT * FROM definities ORDER BY id LIMIT 5"
                ).fetchall()

                mismatches = []
                for base, target in zip(baseline_sample, target_sample, strict=False):
                    if base["begrip"] != target["begrip"]:
                        mismatches.append(
                            f"ID {base['id']}: {base['begrip']} != {target['begrip']}"
                        )

                if mismatches:
                    self.add_fail(
                        "Baseline validation", f"Sample mismatches: {len(mismatches)}"
                    )
                    for mismatch in mismatches:
                        logger.error(f"  {mismatch}")
                    return False

                self.add_pass("Baseline validation")
                return True

        except Exception as e:
            self.add_fail("Baseline validation", str(e))
            return False

    def execute(self) -> bool:
        """Execute all validation tests.

        Returns:
            True if all tests passed
        """
        logger.info("=" * 60)
        logger.info("MIGRATION VALIDATION")
        logger.info("=" * 60)

        # Run validation tests
        self.validate_record_counts()
        self.validate_content_integrity()
        self.validate_foreign_keys()
        self.validate_indexes()
        self.validate_utf8_encoding()
        self.validate_against_baseline()

        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("VALIDATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Tests run: {self.tests_run}")
        logger.info(f"Passed: {self.tests_passed}")
        logger.info(f"Failed: {self.tests_failed}")

        if self.tests_failed == 0:
            logger.info("\n✅ All validation tests passed")
            return True
        else:
            logger.error(f"\n❌ {self.tests_failed} test(s) failed")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate migrated database integrity")
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
    parser.add_argument("--baseline", help="Optional baseline JSON file for validation")

    args = parser.parse_args()

    # Create logs directory
    Path("logs/migration").mkdir(parents=True, exist_ok=True)

    # Check databases exist
    if not Path(args.source).exists():
        logger.error(f"❌ Source database not found: {args.source}")
        return 1

    if not Path(args.target).exists():
        logger.error(f"❌ Target database not found: {args.target}")
        return 1

    # Execute validation
    validator = MigrationValidator(args.source, args.target, args.baseline)
    success = validator.execute()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
