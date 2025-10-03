#!/usr/bin/env python3
"""Export baseline data from current production database.

This script exports all production data (definitions, history, examples) to JSON
for validation and rollback purposes during the migration process.

Usage:
    python rebuild/scripts/migration/1_export_baseline.py
    python rebuild/scripts/migration/1_export_baseline.py --db data/definities.db --output data/migration_baseline.json

Example:
    $ python rebuild/scripts/migration/1_export_baseline.py
    ✅ Exported 42 definitions
    ✅ Exported 96 history records
    ✅ Exported 90 examples
    📦 Baseline export saved to: data/migration_baseline.json
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
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            f"logs/migration/export_baseline_{datetime.now():%Y%m%d_%H%M%S}.log"
        ),
    ],
)
logger = logging.getLogger(__name__)


def export_table(conn: sqlite3.Connection, table_name: str) -> dict[str, Any]:
    """Export complete table to dictionary format.

    Args:
        conn: Database connection
        table_name: Name of table to export

    Returns:
        Dictionary with 'count' and 'rows' keys
    """
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(f"SELECT * FROM {table_name}")
        rows = [dict(row) for row in cursor.fetchall()]

        logger.info(f"✅ Exported {len(rows)} rows from {table_name}")

        return {"count": len(rows), "rows": rows}
    except sqlite3.Error as e:
        logger.error(f"❌ Failed to export {table_name}: {e}")
        raise


def export_baseline(db_path: str, output_path: str) -> dict[str, Any]:
    """Export complete baseline from database.

    Args:
        db_path: Path to SQLite database
        output_path: Path for JSON output file

    Returns:
        Export dictionary with metadata and all table data
    """
    # Verify database exists
    db_file = Path(db_path)
    if not db_file.exists():
        logger.error(f"❌ Database not found: {db_path}")
        sys.exit(1)

    logger.info(f"📂 Connecting to database: {db_path}")

    # Connect and export
    with sqlite3.connect(db_path) as conn:
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")

        # Get database statistics
        cursor = conn.execute("SELECT COUNT(*) FROM definities")
        total_definitions = cursor.fetchone()[0]

        logger.info(f"📊 Database contains {total_definitions} definitions")

        # Build export structure
        export = {
            "metadata": {
                "export_date": datetime.now().isoformat(),
                "source_database": str(db_path),
                "source_version": "2.3.0",
                "schema_version": "v2.0",
                "exporter": "1_export_baseline.py",
            },
            "tables": {},
        }

        # Export core tables
        tables = [
            "definities",
            "definitie_geschiedenis",
            "definitie_voorbeelden",
            "definitie_tags",
        ]

        for table in tables:
            try:
                export["tables"][table] = export_table(conn, table)
            except sqlite3.Error as e:
                logger.warning(f"⚠️  Could not export {table}: {e}")
                export["tables"][table] = {"count": 0, "rows": [], "error": str(e)}

        # Calculate totals
        total_rows = sum(t["count"] for t in export["tables"].values())
        export["metadata"]["total_rows"] = total_rows

    # Save to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(export, f, indent=2, ensure_ascii=False, default=str)

    logger.info(f"📦 Baseline export saved to: {output_path}")
    logger.info(f"📊 Total rows exported: {total_rows}")

    return export


def validate_export(export: dict[str, Any]) -> bool:
    """Validate export completeness.

    Args:
        export: Export dictionary to validate

    Returns:
        True if validation passes
    """
    logger.info("🔍 Validating export...")

    validation_passed = True

    # Check required tables
    required_tables = ["definities", "definitie_geschiedenis", "definitie_voorbeelden"]
    for table in required_tables:
        if table not in export["tables"]:
            logger.error(f"❌ Missing table: {table}")
            validation_passed = False

    # Check definition count (should be 42)
    definitions_count = export["tables"].get("definities", {}).get("count", 0)
    if definitions_count != 42:
        logger.warning(f"⚠️  Expected 42 definitions, found {definitions_count}")
        # Not a hard failure - may be different in test environments

    # Check data integrity
    for table_name, table_data in export["tables"].items():
        if "error" in table_data:
            logger.error(f"❌ Export error in {table_name}: {table_data['error']}")
            validation_passed = False
            continue

        if table_data["count"] != len(table_data["rows"]):
            logger.error(
                f"❌ Row count mismatch in {table_name}: {table_data['count']} != {len(table_data['rows'])}"
            )
            validation_passed = False

    if validation_passed:
        logger.info("✅ Export validation passed")
    else:
        logger.error("❌ Export validation failed")

    return validation_passed


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Export baseline data from production database"
    )
    parser.add_argument(
        "--db",
        default="data/definities.db",
        help="Path to SQLite database (default: data/definities.db)",
    )
    parser.add_argument(
        "--output",
        default="data/migration_baseline.json",
        help="Output JSON file path (default: data/migration_baseline.json)",
    )
    parser.add_argument(
        "--validate", action="store_true", help="Run validation checks after export"
    )

    args = parser.parse_args()

    # Create logs directory
    Path("logs/migration").mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("BASELINE EXPORT - DefinitieAgent Migration")
    logger.info("=" * 60)

    try:
        # Export data
        export = export_baseline(args.db, args.output)

        # Validate if requested
        if args.validate:
            if not validate_export(export):
                logger.error("❌ Validation failed - please review export")
                sys.exit(1)

        logger.info("=" * 60)
        logger.info("✅ BASELINE EXPORT COMPLETE")
        logger.info("=" * 60)
        logger.info(f"📊 Definitions: {export['tables']['definities']['count']}")
        logger.info(
            f"📊 History: {export['tables']['definitie_geschiedenis']['count']}"
        )
        logger.info(
            f"📊 Examples: {export['tables']['definitie_voorbeelden']['count']}"
        )
        logger.info(f"📦 Output: {args.output}")

        return 0

    except Exception as e:
        logger.error(f"❌ Export failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
