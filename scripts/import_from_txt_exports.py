#!/usr/bin/env python3
"""
Import definities from TXT exports back into database.

Used for data recovery after accidental database overwrites.
"""

import re
import sqlite3
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class DefinitieExportParser:
    """Parser for TXT export format."""

    def __init__(self, export_file: Path):
        self.export_file = export_file
        self.content = export_file.read_text(encoding="utf-8")

    def parse_all(self) -> List[Dict]:
        """Parse all definitions from export file."""
        definitions = []

        # Split by separator lines (both === and ---)
        # First split by === headers
        blocks = re.split(r"={80,}", self.content)

        # Then split each block by --- separators
        all_blocks = []
        for block in blocks:
            sub_blocks = re.split(r"-{80,}", block)
            all_blocks.extend(sub_blocks)

        # Find definition blocks (contain "ID:")
        for block in all_blocks:
            if "\nID:" in block or block.strip().startswith("ID:"):
                definition = self._parse_definition_block(block)
                if definition:
                    definitions.append(definition)

        return definitions

    def _parse_definition_block(self, block: str) -> Optional[Dict]:
        """Parse a single definition block."""
        lines = block.strip().split("\n")

        data = {}
        current_field = None
        current_value = []

        for line in lines:
            # Check for field: value pattern
            match = re.match(r"^([\w\s]+):\s*(.*)$", line)
            if match:
                # Save previous field
                if current_field:
                    data[current_field] = "\n".join(current_value).strip()

                current_field = match.group(1).strip()
                current_value = [match.group(2)]
            else:
                # Continuation of previous field
                if current_field:
                    current_value.append(line)

        # Save last field
        if current_field:
            data[current_field] = "\n".join(current_value).strip()

        # Extract required fields
        if "ID" not in data or "Begrip" not in data:
            return None

        return {
            "id": int(data.get("ID", 0)),
            "begrip": data.get("Begrip", ""),
            "definitie": data.get("Definitie", ""),
            "categorie": data.get("Categorie", "type"),
            "organisatorische_context": data.get("Organisatorische context", "[]"),
            "juridische_context": data.get("Juridische context", "[]"),
            "wettelijke_basis": data.get("Wettelijke basis", "[]"),
            "status": data.get("Status", "draft"),
            "version_number": int(data.get("Versie", "1")),
            "source_type": data.get("Bron type", "generated"),
            "source_reference": data.get("Geïmporteerd van", None),
            "created_at": self._parse_timestamp(data.get("Aangemaakt op")),
            "updated_at": self._parse_timestamp(data.get("Bijgewerkt op")),
            "toelichting_proces": data.get("Toelichting", None),
            "voorbeelden": self._extract_voorbeelden(data),
        }

    def _parse_timestamp(self, ts_str: Optional[str]) -> Optional[str]:
        """Parse timestamp string."""
        if not ts_str:
            return None
        try:
            # Try ISO format first
            if "T" in ts_str:
                return ts_str
            # Try space-separated format
            dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
            return dt.isoformat()
        except Exception:
            return None

    def _extract_voorbeelden(self, data: Dict) -> List[str]:
        """Extract example sentences."""
        voorbeelden = []

        if "Voorbeeld zinnen" in data:
            lines = data["Voorbeeld zinnen"].split("\n")
            for line in lines:
                line = line.strip()
                if line.startswith("-"):
                    voorbeelden.append(line[1:].strip())

        return voorbeelden


class DatabaseImporter:
    """Import parsed definitions into database."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path))
        self.cursor = self.conn.cursor()

    def import_definition(self, definition: Dict, overwrite: bool = False) -> bool:
        """Import a single definition."""
        def_id = definition["id"]

        # Check if exists
        self.cursor.execute("SELECT id FROM definities WHERE id = ?", (def_id,))
        exists = self.cursor.fetchone() is not None

        if exists and not overwrite:
            print(f"  ⏭️  ID {def_id} bestaat al, overslaan")
            return False

        if exists:
            # Update existing
            print(f"  🔄 ID {def_id} ({definition['begrip']}): OVERSCHRIJVEN")
            self._update_definition(definition)
        else:
            # Insert new
            print(f"  ✅ ID {def_id} ({definition['begrip']}): TOEVOEGEN")
            self._insert_definition(definition)

        # Import voorbeelden
        self._import_voorbeelden(def_id, definition.get("voorbeelden", []))

        return True

    def _insert_definition(self, definition: Dict):
        """Insert new definition."""
        sql = """
            INSERT INTO definities (
                id, begrip, definitie, categorie,
                organisatorische_context, juridische_context, wettelijke_basis,
                toelichting_proces, status, version_number,
                source_type, source_reference,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        self.cursor.execute(sql, (
            definition["id"],
            definition["begrip"],
            definition["definitie"],
            definition["categorie"],
            definition["organisatorische_context"],
            definition["juridische_context"],
            definition["wettelijke_basis"],
            definition.get("toelichting_proces"),
            definition["status"],
            definition["version_number"],
            definition["source_type"],
            definition.get("source_reference"),
            definition.get("created_at"),
            definition.get("updated_at"),
        ))

    def _update_definition(self, definition: Dict):
        """Update existing definition."""
        sql = """
            UPDATE definities SET
                begrip = ?,
                definitie = ?,
                categorie = ?,
                organisatorische_context = ?,
                juridische_context = ?,
                wettelijke_basis = ?,
                toelichting_proces = ?,
                status = ?,
                version_number = ?,
                source_type = ?,
                source_reference = ?,
                updated_at = ?
            WHERE id = ?
        """

        self.cursor.execute(sql, (
            definition["begrip"],
            definition["definitie"],
            definition["categorie"],
            definition["organisatorische_context"],
            definition["juridische_context"],
            definition["wettelijke_basis"],
            definition.get("toelichting_proces"),
            definition["status"],
            definition["version_number"],
            definition["source_type"],
            definition.get("source_reference"),
            definition.get("updated_at"),
            definition["id"],
        ))

    def _import_voorbeelden(self, definitie_id: int, voorbeelden: List[str]):
        """Import example sentences."""
        # Clear existing voorbeelden
        self.cursor.execute(
            "DELETE FROM definitie_voorbeelden WHERE definitie_id = ?",
            (definitie_id,)
        )

        # Insert new voorbeelden with volgorde
        volgorde = 1
        for voorbeeld_text in voorbeelden:
            if voorbeeld_text.strip():
                self.cursor.execute(
                    """
                    INSERT INTO definitie_voorbeelden (
                        definitie_id, voorbeeld_tekst, voorbeeld_type, voorbeeld_volgorde
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (definitie_id, voorbeeld_text.strip(), "sentence", volgorde)
                )
                volgorde += 1

    def commit(self):
        """Commit changes."""
        self.conn.commit()

    def close(self):
        """Close connection."""
        self.conn.close()


def main():
    """Main import function."""
    print("🔄 DEFINITIE RECOVERY - TXT EXPORT IMPORT")
    print("=" * 60)

    # Paths
    project_root = Path(__file__).parent.parent
    db_path = project_root / "data" / "definities.db"
    exports_dir = project_root / "exports"

    if not db_path.exists():
        print(f"❌ Database niet gevonden: {db_path}")
        return 1

    # Find export files with missing IDs
    target_ids = {77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 90, 91}

    export_files = [
        exports_dir / "definities_export_20251029_130927.txt",  # IDs 80-88
        exports_dir / "definities_export_20251030_100359.txt",  # ID 90
        exports_dir / "definities_export_20251030_101334.txt",  # ID 91
    ]

    # Check files exist
    for export_file in export_files:
        if not export_file.exists():
            print(f"⚠️  Export bestand niet gevonden: {export_file.name}")

    export_files = [f for f in export_files if f.exists()]

    if not export_files:
        print("❌ Geen export bestanden gevonden!")
        return 1

    print(f"\n📁 Export bestanden: {len(export_files)}")
    for f in export_files:
        print(f"  - {f.name}")

    # Parse exports
    print("\n🔍 Parsing exports...")
    all_definitions = []

    for export_file in export_files:
        print(f"  📄 {export_file.name}")
        parser = DefinitieExportParser(export_file)
        definitions = parser.parse_all()

        # Filter for target IDs only
        target_defs = [d for d in definitions if d["id"] in target_ids]
        all_definitions.extend(target_defs)

        print(f"    Gevonden: {len(target_defs)} target definities")

    if not all_definitions:
        print("\n❌ Geen target definities gevonden in exports!")
        return 1

    print(f"\n✅ Totaal gevonden: {len(all_definitions)} definities")
    print(f"   IDs: {sorted([d['id'] for d in all_definitions])}")

    # Ask for confirmation (or skip in non-interactive mode)
    print(f"\n⚠️  IMPORTEREN naar database: {db_path}")

    if sys.stdin.isatty():
        response = input("   Doorgaan? (y/N): ").strip().lower()
        if response != "y":
            print("❌ Geannuleerd")
            return 0
    else:
        print("   (Non-interactive mode: auto-confirming)")
        print("   Doorgaan? YES (auto)")

    # Import
    print("\n🔄 Importeren...")
    importer = DatabaseImporter(db_path)

    imported = 0
    skipped = 0

    for definition in sorted(all_definitions, key=lambda d: d["id"]):
        if importer.import_definition(definition, overwrite=False):
            imported += 1
        else:
            skipped += 1

    importer.commit()
    importer.close()

    print("\n" + "=" * 60)
    print(f"✅ KLAAR!")
    print(f"   Geïmporteerd: {imported}")
    print(f"   Overgeslagen: {skipped}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
