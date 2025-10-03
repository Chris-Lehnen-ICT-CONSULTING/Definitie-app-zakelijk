#!/usr/bin/env python3
"""Validate exported baseline data completeness and integrity.

This script performs comprehensive validation on the exported baseline data,
checking record counts, data integrity, foreign key relationships, and UTF-8 encoding.

Usage:
    python rebuild/scripts/migration/2_validate_export.py data/migration_baseline.json
    python rebuild/scripts/migration/2_validate_export.py data/migration_baseline.json --strict

Example:
    $ python rebuild/scripts/migration/2_validate_export.py data/migration_baseline.json
    ✅ Record count validation passed
    ✅ UTF-8 encoding validation passed
    ✅ Foreign key integrity passed
    ✅ All validation tests passed (4/4)
"""

import argparse
import json
import logging
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
            f"logs/migration/validate_export_{datetime.now():%Y%m%d_%H%M%S}.log"
        ),
    ],
)
logger = logging.getLogger(__name__)


class ValidationResult:
    """Track validation test results."""

    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.warnings = 0
        self.errors = []

    def add_pass(self, test_name: str):
        """Record a passing test."""
        self.tests_run += 1
        self.tests_passed += 1
        logger.info(f"✅ {test_name}")

    def add_fail(self, test_name: str, message: str):
        """Record a failing test."""
        self.tests_run += 1
        self.tests_failed += 1
        self.errors.append(f"{test_name}: {message}")
        logger.error(f"❌ {test_name}: {message}")

    def add_warning(self, message: str):
        """Record a warning."""
        self.warnings += 1
        logger.warning(f"⚠️  {message}")

    @property
    def success(self) -> bool:
        """Check if all tests passed."""
        return self.tests_failed == 0

    def print_summary(self):
        """Print validation summary."""
        logger.info("=" * 60)
        logger.info("VALIDATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Tests run: {self.tests_run}")
        logger.info(f"Passed: {self.tests_passed}")
        logger.info(f"Failed: {self.tests_failed}")
        logger.info(f"Warnings: {self.warnings}")

        if self.errors:
            logger.error("\nErrors:")
            for error in self.errors:
                logger.error(f"  - {error}")


def load_export(export_path: str) -> dict[str, Any]:
    """Load and parse export JSON file.

    Args:
        export_path: Path to export JSON file

    Returns:
        Parsed export dictionary
    """
    export_file = Path(export_path)

    if not export_file.exists():
        logger.error(f"❌ Export file not found: {export_path}")
        sys.exit(1)

    logger.info(f"📂 Loading export: {export_path}")

    with open(export_file, encoding="utf-8") as f:
        export = json.load(f)

    logger.info("✅ Export loaded successfully")
    return export


def validate_metadata(export: dict[str, Any], result: ValidationResult):
    """Validate export metadata completeness.

    Args:
        export: Export dictionary
        result: ValidationResult to record results
    """
    logger.info("\n🔍 Validating metadata...")

    required_fields = [
        "export_date",
        "source_database",
        "source_version",
        "schema_version",
    ]

    metadata = export.get("metadata", {})
    for field in required_fields:
        if field not in metadata:
            result.add_fail("Metadata validation", f"Missing field: {field}")
        else:
            logger.debug(f"  {field}: {metadata[field]}")

    if all(field in metadata for field in required_fields):
        result.add_pass("Metadata validation")


def validate_record_counts(
    export: dict[str, Any], result: ValidationResult, strict: bool = False
):
    """Validate record counts match expectations.

    Args:
        export: Export dictionary
        result: ValidationResult to record results
        strict: If True, enforce exact counts from production
    """
    logger.info("\n🔍 Validating record counts...")

    tables = export.get("tables", {})

    # Expected counts from production (42/96/90)
    expected = {
        "definities": 42,
        "definitie_geschiedenis": 96,
        "definitie_voorbeelden": 90,
    }

    all_match = True
    for table_name, expected_count in expected.items():
        if table_name not in tables:
            result.add_fail("Record count", f"Missing table: {table_name}")
            all_match = False
            continue

        actual_count = tables[table_name].get("count", 0)
        rows_count = len(tables[table_name].get("rows", []))

        # Check count matches row length
        if actual_count != rows_count:
            result.add_fail(
                "Record count",
                f"{table_name}: count mismatch ({actual_count} != {rows_count})",
            )
            all_match = False
            continue

        # Check against expected count
        if strict and actual_count != expected_count:
            result.add_fail(
                "Record count",
                f"{table_name}: expected {expected_count}, got {actual_count}",
            )
            all_match = False
        elif actual_count != expected_count:
            result.add_warning(
                f"{table_name}: expected {expected_count}, got {actual_count} (not strict mode)"
            )
        else:
            logger.info(f"  ✓ {table_name}: {actual_count} records")

    if all_match:
        result.add_pass("Record count validation")


def validate_foreign_keys(export: dict[str, Any], result: ValidationResult):
    """Validate foreign key relationships are intact.

    Args:
        export: Export dictionary
        result: ValidationResult to record results
    """
    logger.info("\n🔍 Validating foreign key integrity...")

    tables = export.get("tables", {})

    # Get all definition IDs
    definition_ids = {row["id"] for row in tables.get("definities", {}).get("rows", [])}

    if not definition_ids:
        result.add_fail("Foreign key validation", "No definitions found")
        return

    # Check history references
    history_rows = tables.get("definitie_geschiedenis", {}).get("rows", [])
    orphaned_history = []
    for row in history_rows:
        if row["definitie_id"] not in definition_ids:
            orphaned_history.append(row["id"])

    if orphaned_history:
        result.add_fail(
            "Foreign key validation",
            f"Found {len(orphaned_history)} orphaned history records",
        )
    else:
        logger.info(
            f"  ✓ All {len(history_rows)} history records have valid definition references"
        )

    # Check example references
    example_rows = tables.get("definitie_voorbeelden", {}).get("rows", [])
    orphaned_examples = []
    for row in example_rows:
        if row["definitie_id"] not in definition_ids:
            orphaned_examples.append(row["id"])

    if orphaned_examples:
        result.add_fail(
            "Foreign key validation",
            f"Found {len(orphaned_examples)} orphaned example records",
        )
    else:
        logger.info(
            f"  ✓ All {len(example_rows)} example records have valid definition references"
        )

    if not orphaned_history and not orphaned_examples:
        result.add_pass("Foreign key integrity")


def validate_utf8_encoding(export: dict[str, Any], result: ValidationResult):
    """Validate UTF-8 encoding for Dutch characters.

    Args:
        export: Export dictionary
        result: ValidationResult to record results
    """
    logger.info("\n🔍 Validating UTF-8 encoding...")

    tables = export.get("tables", {})
    definition_rows = tables.get("definities", {}).get("rows", [])

    # Check for common Dutch characters
    dutch_chars = ["ë", "ï", "é", "è", "ê", "ô", "û", "ü", "á", "à"]
    found_dutch = False
    encoding_errors = []

    for row in definition_rows:
        begrip = row.get("begrip", "")
        definitie = row.get("definitie", "")

        # Check if Dutch characters are present and correctly encoded
        for char in dutch_chars:
            if char in begrip or char in definitie:
                found_dutch = True
                try:
                    begrip.encode("utf-8")
                    definitie.encode("utf-8")
                except UnicodeEncodeError as e:
                    encoding_errors.append(f"ID {row['id']}: {e}")

    if encoding_errors:
        result.add_fail(
            "UTF-8 encoding", f"Found {len(encoding_errors)} encoding errors"
        )
        for error in encoding_errors[:5]:  # Show first 5
            logger.error(f"  {error}")
    else:
        if found_dutch:
            logger.info("  ✓ Dutch characters found and properly encoded")
        result.add_pass("UTF-8 encoding validation")


def validate_required_fields(export: dict[str, Any], result: ValidationResult):
    """Validate required fields are present and non-null.

    Args:
        export: Export dictionary
        result: ValidationResult to record results
    """
    logger.info("\n🔍 Validating required fields...")

    tables = export.get("tables", {})
    definition_rows = tables.get("definities", {}).get("rows", [])

    required_fields = ["id", "begrip", "definitie", "categorie", "status"]
    field_errors = []

    for row in definition_rows:
        for field in required_fields:
            if field not in row or row[field] is None or row[field] == "":
                field_errors.append(f"ID {row.get('id', '?')}: missing/empty {field}")

    if field_errors:
        result.add_fail(
            "Required fields", f"Found {len(field_errors)} missing/empty fields"
        )
        for error in field_errors[:10]:  # Show first 10
            logger.error(f"  {error}")
    else:
        logger.info(f"  ✓ All {len(definition_rows)} definitions have required fields")
        result.add_pass("Required fields validation")


def validate_json_fields(export: dict[str, Any], result: ValidationResult):
    """Validate JSON fields can be parsed.

    Args:
        export: Export dictionary
        result: ValidationResult to record results
    """
    logger.info("\n🔍 Validating JSON fields...")

    tables = export.get("tables", {})
    definition_rows = tables.get("definities", {}).get("rows", [])

    json_fields = ["organisatorische_context", "juridische_context", "wettelijke_basis"]
    json_errors = []

    for row in definition_rows:
        for field in json_fields:
            value = row.get(field)
            if value:
                try:
                    if isinstance(value, str):
                        json.loads(value)
                    elif not isinstance(value, (list, dict)):
                        json_errors.append(
                            f"ID {row['id']}, field {field}: not JSON or list/dict"
                        )
                except json.JSONDecodeError as e:
                    json_errors.append(f"ID {row['id']}, field {field}: {e}")

    if json_errors:
        result.add_fail("JSON fields", f"Found {len(json_errors)} JSON parsing errors")
        for error in json_errors[:10]:
            logger.error(f"  {error}")
    else:
        logger.info("  ✓ All JSON fields valid")
        result.add_pass("JSON fields validation")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate exported baseline data")
    parser.add_argument(
        "export_file",
        help="Path to export JSON file (e.g., data/migration_baseline.json)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enforce strict record count validation (must match 42/96/90)",
    )

    args = parser.parse_args()

    # Create logs directory
    Path("logs/migration").mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("EXPORT VALIDATION - DefinitieAgent Migration")
    logger.info("=" * 60)

    result = ValidationResult()

    try:
        # Load export
        export = load_export(args.export_file)

        # Run validation tests
        validate_metadata(export, result)
        validate_record_counts(export, result, strict=args.strict)
        validate_foreign_keys(export, result)
        validate_utf8_encoding(export, result)
        validate_required_fields(export, result)
        validate_json_fields(export, result)

        # Print summary
        result.print_summary()

        if result.success:
            logger.info("\n✅ All validation tests passed")
            return 0
        else:
            logger.error("\n❌ Validation failed - please review errors")
            return 1

    except Exception as e:
        logger.error(f"❌ Validation error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
