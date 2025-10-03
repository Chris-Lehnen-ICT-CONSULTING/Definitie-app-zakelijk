#!/usr/bin/env python3
"""
Export 42 baseline definitions from production database for rebuild validation testing.

This script extracts all definitions from the production database and stores them
in a canonical JSON format for use as baseline validation data during the rebuild.

Output: docs/business-logic/baseline_42_definitions.json

Usage:
    python scripts/export_baseline_definitions.py
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


def connect_database(db_path: Path) -> sqlite3.Connection:
    """Connect to SQLite database with proper settings."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def export_definitions(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """
    Export all definitions with complete metadata.

    Returns:
        List of definition dictionaries with all fields.
    """
    cursor = conn.cursor()

    # Export all definition fields
    cursor.execute(
        """
        SELECT
            id,
            begrip,
            definitie,
            categorie,
            organisatorische_context,
            juridische_context,
            wettelijke_basis,
            ufo_categorie,
            toelichting_proces,
            status,
            version_number,
            previous_version_id,
            validation_score,
            validation_date,
            validation_issues,
            source_type,
            source_reference,
            imported_from,
            created_at,
            updated_at,
            created_by,
            updated_by,
            approved_by,
            approved_at,
            approval_notes,
            last_exported_at,
            export_destinations,
            datum_voorstel,
            ketenpartners,
            voorkeursterm
        FROM definities
        ORDER BY created_at DESC
    """
    )

    definitions = []
    for row in cursor.fetchall():
        definition = dict(row)

        # Parse JSON fields
        for field in [
            "organisatorische_context",
            "juridische_context",
            "wettelijke_basis",
            "validation_issues",
            "export_destinations",
            "ketenpartners",
        ]:
            if definition.get(field):
                try:
                    definition[field] = json.loads(definition[field])
                except (json.JSONDecodeError, TypeError):
                    definition[field] = []
            else:
                definition[field] = []

        definitions.append(definition)

    return definitions


def export_voorbeelden(
    conn: sqlite3.Connection, definitie_id: int
) -> list[dict[str, Any]]:
    """
    Export voorbeelden (example sentences) for a definition.

    Args:
        conn: Database connection
        definitie_id: Definition ID

    Returns:
        List of voorbeelden dictionaries
    """
    cursor = conn.cursor()

    # Check if voorbeelden table exists
    cursor.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='voorbeelden'
    """
    )

    if not cursor.fetchone():
        # Table doesn't exist, return empty list
        return []

    cursor.execute(
        """
        SELECT
            id,
            definitie_id,
            voorbeeldtekst,
            type,
            bron,
            created_at
        FROM voorbeelden
        WHERE definitie_id = ?
        ORDER BY created_at
    """,
        (definitie_id,),
    )

    voorbeelden = []
    for row in cursor.fetchall():
        voorbeelden.append(dict(row))

    return voorbeelden


def export_validation_results(
    conn: sqlite3.Connection, definitie_id: int
) -> dict[str, Any]:
    """
    Export validation results for a definition (from latest validation).

    Args:
        conn: Database connection
        definitie_id: Definition ID

    Returns:
        Dictionary with validation metadata
    """
    cursor = conn.cursor()

    # Get latest validation from definitie table
    cursor.execute(
        """
        SELECT
            validation_score,
            validation_date,
            validation_issues
        FROM definities
        WHERE id = ?
    """,
        (definitie_id,),
    )

    row = cursor.fetchone()
    if not row:
        return {}

    validation = dict(row)

    # Parse validation_issues if present
    if validation.get("validation_issues"):
        try:
            validation["validation_issues"] = json.loads(
                validation["validation_issues"]
            )
        except (json.JSONDecodeError, TypeError):
            validation["validation_issues"] = []

    return validation


def export_baseline() -> None:
    """Main export function."""
    # Paths
    project_root = Path(__file__).parent.parent
    db_path = project_root / "data" / "definities.db"
    output_dir = project_root / "docs" / "business-logic"
    output_file = output_dir / "baseline_42_definitions.json"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Connect to database
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return

    print(f"📊 Connecting to database: {db_path}")
    conn = connect_database(db_path)

    try:
        # Export definitions
        print("📥 Exporting definitions...")
        definitions = export_definitions(conn)
        print(f"   Found {len(definitions)} definitions")

        # Enrich each definition with voorbeelden and validation results
        for definition in definitions:
            definitie_id = definition["id"]

            # Add voorbeelden
            voorbeelden = export_voorbeelden(conn, definitie_id)
            definition["voorbeelden"] = voorbeelden

            # Add detailed validation results
            validation = export_validation_results(conn, definitie_id)
            definition["validation_metadata"] = validation

        # Create export metadata
        export_data = {
            "export_metadata": {
                "export_date": datetime.now().isoformat(),
                "export_purpose": "Baseline validation for EPIC-026 rebuild",
                "total_definitions": len(definitions),
                "database_path": str(db_path),
                "schema_version": "1.0",
            },
            "definitions": definitions,
        }

        # Write to JSON file
        print(f"💾 Writing to: {output_file}")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)

        # Print statistics
        print("\n✅ Export complete!")
        print(f"   Total definitions: {len(definitions)}")
        print(f"   Output file: {output_file}")
        print(f"   File size: {output_file.stat().st_size / 1024:.1f} KB")

        # Print category breakdown
        categories = {}
        for defn in definitions:
            cat = defn.get("categorie", "unknown")
            categories[cat] = categories.get(cat, 0) + 1

        print("\n📊 Category breakdown:")
        for cat, count in sorted(categories.items()):
            print(f"   {cat}: {count}")

        # Print status breakdown
        statuses = {}
        for defn in definitions:
            status = defn.get("status", "unknown")
            statuses[status] = statuses.get(status, 0) + 1

        print("\n📊 Status breakdown:")
        for status, count in sorted(statuses.items()):
            print(f"   {status}: {count}")

        # Voorbeelden statistics
        total_voorbeelden = sum(len(d.get("voorbeelden", [])) for d in definitions)
        print("\n📊 Voorbeelden statistics:")
        print(f"   Total voorbeelden: {total_voorbeelden}")
        print(f"   Avg per definition: {total_voorbeelden / len(definitions):.1f}")

    finally:
        conn.close()
        print("\n🔒 Database connection closed")


if __name__ == "__main__":
    export_baseline()
