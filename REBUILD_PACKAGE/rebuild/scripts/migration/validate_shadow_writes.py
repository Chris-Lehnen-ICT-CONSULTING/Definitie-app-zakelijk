#!/usr/bin/env python3
"""Validate shadow database writes during parallel run.

This script validates that writes to the shadow (new) database during parallel
run match the writes to the primary (old) database, ensuring data consistency
before cutover.

Usage:
    python rebuild/scripts/migration/validate_shadow_writes.py
    python rebuild/scripts/migration/validate_shadow_writes.py --primary data/definities.db --shadow data/definities.db.shadow
    python rebuild/scripts/migration/validate_shadow_writes.py --since "2025-10-02 00:00:00"

Example:
    $ python rebuild/scripts/migration/validate_shadow_writes.py
    ✅ Write operations: 15/15 match (100%)
    ✅ Record consistency: 42/42 definitions match
    ✅ Timestamp alignment: Average drift 0.3s (< 5s tolerance)
    ✅ Shadow write validation: PASSED
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
            f"logs/migration/shadow_writes_{datetime.now():%Y%m%d_%H%M%S}.log"
        ),
    ],
)
logger = logging.getLogger(__name__)


class ShadowWriteValidator:
    """Validate shadow database writes."""

    def __init__(self, primary_db: str, shadow_db: str, since: str | None = None):
        """Initialize validator.

        Args:
            primary_db: Path to primary database
            shadow_db: Path to shadow database
            since: Optional timestamp to validate writes since
        """
        self.primary_db = Path(primary_db)
        self.shadow_db = Path(shadow_db)
        self.since = since
        self.validation_results = {
            "timestamp": datetime.now().isoformat(),
            "write_operations": {},
            "consistency": {},
            "timing": {},
            "discrepancies": [],
        }

    def validate_write_operations(self) -> dict[str, Any]:
        """Validate write operations match between databases.

        Returns:
            Validation results
        """
        logger.info("\n🔍 Validating write operations...")

        try:
            with (
                sqlite3.connect(self.primary_db) as primary_conn,
                sqlite3.connect(self.shadow_db) as shadow_conn,
            ):

                # Build WHERE clause for time filtering
                where_clause = ""
                if self.since:
                    where_clause = f"WHERE created_at >= '{self.since}'"

                # Count operations by type
                operation_types = []

                # New definitions
                primary_new = primary_conn.execute(
                    f"SELECT COUNT(*) FROM definities {where_clause}"
                ).fetchone()[0]
                shadow_new = shadow_conn.execute(
                    f"SELECT COUNT(*) FROM definities {where_clause}"
                ).fetchone()[0]

                operation_types.append(
                    {
                        "type": "new_definitions",
                        "primary": primary_new,
                        "shadow": shadow_new,
                        "match": primary_new == shadow_new,
                    }
                )

                # Updates (check history table)
                primary_updates = primary_conn.execute(
                    f"SELECT COUNT(*) FROM definitie_geschiedenis WHERE wijziging_type = 'updated' {where_clause.replace('created_at', 'gewijzigd_op')}"
                ).fetchone()[0]
                shadow_updates = shadow_conn.execute(
                    f"SELECT COUNT(*) FROM definitie_geschiedenis WHERE wijziging_type = 'updated' {where_clause.replace('created_at', 'gewijzigd_op')}"
                ).fetchone()[0]

                operation_types.append(
                    {
                        "type": "updates",
                        "primary": primary_updates,
                        "shadow": shadow_updates,
                        "match": primary_updates == shadow_updates,
                    }
                )

                # Status changes
                primary_status = primary_conn.execute(
                    f"SELECT COUNT(*) FROM definitie_geschiedenis WHERE wijziging_type = 'status_changed' {where_clause.replace('created_at', 'gewijzigd_op')}"
                ).fetchone()[0]
                shadow_status = shadow_conn.execute(
                    f"SELECT COUNT(*) FROM definitie_geschiedenis WHERE wijziging_type = 'status_changed' {where_clause.replace('created_at', 'gewijzigd_op')}"
                ).fetchone()[0]

                operation_types.append(
                    {
                        "type": "status_changes",
                        "primary": primary_status,
                        "shadow": shadow_status,
                        "match": primary_status == shadow_status,
                    }
                )

                # Calculate totals
                total_ops = len(operation_types)
                matching_ops = sum(1 for op in operation_types if op["match"])

                result = {
                    "total_operation_types": total_ops,
                    "matching": matching_ops,
                    "mismatched": total_ops - matching_ops,
                    "operations": operation_types,
                }

                self.validation_results["write_operations"] = result

                # Log discrepancies
                for op in operation_types:
                    if not op["match"]:
                        self.validation_results["discrepancies"].append(
                            {
                                "type": "operation_mismatch",
                                "operation": op["type"],
                                "primary": op["primary"],
                                "shadow": op["shadow"],
                            }
                        )

                status = "✅" if matching_ops == total_ops else "❌"
                logger.info(
                    f"{status} Write operations: {matching_ops}/{total_ops} match"
                )

                return result

        except Exception as e:
            logger.error(f"❌ Write operation validation failed: {e}")
            return {"error": str(e)}

    def validate_record_consistency(self) -> dict[str, Any]:
        """Validate record-level consistency between databases.

        Returns:
            Validation results
        """
        logger.info("\n🔍 Validating record consistency...")

        try:
            with (
                sqlite3.connect(self.primary_db) as primary_conn,
                sqlite3.connect(self.shadow_db) as shadow_conn,
            ):

                primary_conn.row_factory = sqlite3.Row
                shadow_conn.row_factory = sqlite3.Row

                # Get all records
                primary_defs = {
                    row["id"]: dict(row)
                    for row in primary_conn.execute(
                        "SELECT * FROM definities ORDER BY id"
                    ).fetchall()
                }

                shadow_defs = {
                    row["id"]: dict(row)
                    for row in shadow_conn.execute(
                        "SELECT * FROM definities ORDER BY id"
                    ).fetchall()
                }

                # Compare
                total_records = len(primary_defs)
                matching = 0
                mismatched = 0

                for def_id, primary_def in primary_defs.items():
                    if def_id not in shadow_defs:
                        mismatched += 1
                        self.validation_results["discrepancies"].append(
                            {
                                "type": "missing_in_shadow",
                                "id": def_id,
                                "begrip": primary_def["begrip"],
                            }
                        )
                        continue

                    shadow_def = shadow_defs[def_id]

                    # Compare key fields
                    key_fields = ["begrip", "definitie", "categorie", "status"]
                    fields_match = all(
                        primary_def.get(f) == shadow_def.get(f) for f in key_fields
                    )

                    if fields_match:
                        matching += 1
                    else:
                        mismatched += 1
                        self.validation_results["discrepancies"].append(
                            {
                                "type": "field_mismatch",
                                "id": def_id,
                                "begrip": primary_def["begrip"],
                                "fields": [
                                    f
                                    for f in key_fields
                                    if primary_def.get(f) != shadow_def.get(f)
                                ],
                            }
                        )

                result = {
                    "total_records": total_records,
                    "matching": matching,
                    "mismatched": mismatched,
                    "match_percentage": (
                        (matching / total_records * 100) if total_records > 0 else 0
                    ),
                }

                self.validation_results["consistency"] = result

                status = "✅" if mismatched == 0 else "❌"
                logger.info(
                    f"{status} Record consistency: {matching}/{total_records} definitions match "
                    f"({result['match_percentage']:.1f}%)"
                )

                return result

        except Exception as e:
            logger.error(f"❌ Record consistency validation failed: {e}")
            return {"error": str(e)}

    def validate_timing_alignment(self) -> dict[str, Any]:
        """Validate write timing alignment between databases.

        Returns:
            Validation results
        """
        logger.info("\n🔍 Validating timing alignment...")

        try:
            with (
                sqlite3.connect(self.primary_db) as primary_conn,
                sqlite3.connect(self.shadow_db) as shadow_conn,
            ):

                # Get recent write timestamps
                primary_times = primary_conn.execute(
                    """
                    SELECT id, created_at, updated_at
                    FROM definities
                    WHERE created_at >= datetime('now', '-24 hours')
                    ORDER BY id
                    """
                ).fetchall()

                shadow_times = shadow_conn.execute(
                    """
                    SELECT id, created_at, updated_at
                    FROM definities
                    WHERE created_at >= datetime('now', '-24 hours')
                    ORDER BY id
                    """
                ).fetchall()

                # Calculate time drifts
                drifts = []
                for primary_row, shadow_row in zip(
                    primary_times, shadow_times, strict=False
                ):
                    if primary_row[0] != shadow_row[0]:
                        continue

                    try:
                        primary_ts = datetime.fromisoformat(primary_row[1])
                        shadow_ts = datetime.fromisoformat(shadow_row[1])
                        drift = abs((shadow_ts - primary_ts).total_seconds())
                        drifts.append(drift)
                    except (ValueError, TypeError):
                        continue

                if drifts:
                    avg_drift = sum(drifts) / len(drifts)
                    max_drift = max(drifts)
                    min_drift = min(drifts)
                else:
                    avg_drift = max_drift = min_drift = 0.0

                result = {
                    "records_compared": len(drifts),
                    "average_drift_seconds": avg_drift,
                    "max_drift_seconds": max_drift,
                    "min_drift_seconds": min_drift,
                    "within_tolerance": avg_drift < 5.0,  # 5 second tolerance
                }

                self.validation_results["timing"] = result

                status = "✅" if result["within_tolerance"] else "⚠️ "
                logger.info(
                    f"{status} Timestamp alignment: Average drift {avg_drift:.1f}s "
                    f"(< 5s tolerance)"
                )

                return result

        except Exception as e:
            logger.error(f"❌ Timing alignment validation failed: {e}")
            return {"error": str(e)}

    def print_summary(self):
        """Print validation summary."""
        logger.info("\n" + "=" * 60)
        logger.info("SHADOW WRITE VALIDATION SUMMARY")
        logger.info("=" * 60)

        # Write operations
        write_ops = self.validation_results.get("write_operations", {})
        if "error" not in write_ops:
            logger.info(
                f"Write operations: {write_ops.get('matching', 0)}/{write_ops.get('total_operation_types', 0)} match"
            )

        # Consistency
        consistency = self.validation_results.get("consistency", {})
        if "error" not in consistency:
            logger.info(
                f"Record consistency: {consistency.get('matching', 0)}/{consistency.get('total_records', 0)} match "
                f"({consistency.get('match_percentage', 0):.1f}%)"
            )

        # Timing
        timing = self.validation_results.get("timing", {})
        if "error" not in timing:
            logger.info(
                f"Timing: Average drift {timing.get('average_drift_seconds', 0):.1f}s "
                f"(within tolerance: {timing.get('within_tolerance', False)})"
            )

        # Discrepancies
        disc_count = len(self.validation_results["discrepancies"])
        if disc_count > 0:
            logger.warning(f"\n⚠️  Found {disc_count} discrepancies:")
            for disc in self.validation_results["discrepancies"][:10]:
                logger.warning(f"  - {disc['type']}: {disc}")

        # Overall verdict
        logger.info("\n" + "=" * 60)
        has_errors = any(
            "error" in self.validation_results.get(key, {})
            for key in ["write_operations", "consistency", "timing"]
        )
        has_critical_discrepancies = disc_count > 0

        if has_errors or has_critical_discrepancies:
            logger.error("❌ Shadow write validation: FAILED")
        else:
            logger.info("✅ Shadow write validation: PASSED")

        logger.info("=" * 60)

    def save_results(self):
        """Save validation results to JSON file."""
        output_file = Path(
            f"logs/migration/shadow_writes_{datetime.now():%Y%m%d_%H%M%S}.json"
        )
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(self.validation_results, f, indent=2)

        logger.info(f"\n📄 Detailed results saved to: {output_file}")

    def execute(self) -> bool:
        """Execute validation.

        Returns:
            True if validation passed
        """
        logger.info("=" * 60)
        logger.info("SHADOW WRITE VALIDATION")
        logger.info("=" * 60)
        logger.info(f"Primary database: {self.primary_db}")
        logger.info(f"Shadow database: {self.shadow_db}")
        if self.since:
            logger.info(f"Validating writes since: {self.since}")

        # Run validations
        self.validate_write_operations()
        self.validate_record_consistency()
        self.validate_timing_alignment()

        # Print summary
        self.print_summary()

        # Save results
        self.save_results()

        # Determine success
        has_errors = any(
            "error" in self.validation_results.get(key, {})
            for key in ["write_operations", "consistency", "timing"]
        )
        has_critical_discrepancies = len(self.validation_results["discrepancies"]) > 0

        return not (has_errors or has_critical_discrepancies)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate shadow database writes during parallel run"
    )
    parser.add_argument(
        "--primary", default="data/definities.db", help="Path to primary database"
    )
    parser.add_argument(
        "--shadow", default="data/definities.db.shadow", help="Path to shadow database"
    )
    parser.add_argument(
        "--since", help="Validate writes since timestamp (YYYY-MM-DD HH:MM:SS)"
    )

    args = parser.parse_args()

    # Create logs directory
    Path("logs/migration").mkdir(parents=True, exist_ok=True)

    # Check databases exist
    if not Path(args.primary).exists():
        logger.error(f"❌ Primary database not found: {args.primary}")
        return 1

    if not Path(args.shadow).exists():
        logger.error(f"❌ Shadow database not found: {args.shadow}")
        return 1

    # Execute validation
    validator = ShadowWriteValidator(args.primary, args.shadow, args.since)
    success = validator.execute()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
