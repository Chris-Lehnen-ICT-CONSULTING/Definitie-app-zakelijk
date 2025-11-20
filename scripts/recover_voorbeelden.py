#!/usr/bin/env python3
"""
Recover lost voorbeelden from TXT export files.

This script recovers all example types (practical, counter, synonyms, antonyms, explanation)
that were lost during the git branch switch on 2025-10-30 15:43.
"""

import re
import sqlite3
import sys
from pathlib import Path


class VoorbeeldenParser:
    """Parser for extracting all example types from TXT exports."""

    def __init__(self, export_file: Path):
        self.export_file = export_file
        self.content = export_file.read_text(encoding="utf-8")

    def parse_all(self) -> list[dict]:
        """Parse all definitions from export file."""
        definitions = []

        # Split by separator lines
        blocks = re.split(r"={80,}|-{80,}", self.content)

        # Find definition blocks (contain "ID:")
        for block in blocks:
            if "\nID:" in block or block.strip().startswith("ID:"):
                definition = self._parse_definition_block(block)
                if definition:
                    definitions.append(definition)

        return definitions

    def _parse_definition_block(self, block: str) -> dict | None:
        """Parse a single definition block with all example types."""
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
            elif current_field:
                current_value.append(line)

        # Save last field
        if current_field:
            data[current_field] = "\n".join(current_value).strip()

        # Extract ID
        if "ID" not in data:
            return None

        return {
            "id": int(data.get("ID", 0)),
            "begrip": data.get("Begrip", ""),
            "voorbeelden": self._extract_all_voorbeelden(data),
        }

    def _extract_all_voorbeelden(self, data: dict) -> dict:
        """Extract ALL types of examples from the export."""
        voorbeelden = {
            "sentence": [],
            "practical": [],
            "counter": [],
            "synonyms": [],
            "antonyms": [],
            "explanation": [],
        }

        # 1. Extract sentence examples (bulleted list)
        if "Voorbeeld zinnen" in data:
            content = data["Voorbeeld zinnen"]
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("-"):
                    text = line[1:].strip()
                    if text:
                        voorbeelden["sentence"].append(text)

        # 2. Extract practical examples (full text blocks)
        if "Praktijkvoorbeelden" in data:
            content = data["Praktijkvoorbeelden"].strip()
            if content:
                # Split by "### Voorbeeld" headers or keep as one block
                examples = re.split(r"\n### Voorbeeld \d+:", content)
                for example in examples:
                    example = example.strip()
                    if example:
                        voorbeelden["practical"].append(example)

        # 3. Extract counter examples
        if "Tegenvoorbeelden" in data:
            content = data["Tegenvoorbeelden"].strip()
            if content:
                # Split by bullet points if present, otherwise keep as block
                if "\n- " in content or content.startswith("- "):
                    parts = re.split(r"\n- ", content)
                    for part in parts:
                        part = part.strip()
                        if part and not part.startswith("-"):
                            voorbeelden["counter"].append(part)
                        elif part.startswith("-"):
                            voorbeelden["counter"].append(part[1:].strip())
                else:
                    voorbeelden["counter"].append(content)

        # 4. Extract synonyms (comma-separated)
        if "Synoniemen" in data:
            content = data["Synoniemen"].strip()
            if content and content != "N/A" and content != "-":
                # Split by comma and clean
                synonyms = [s.strip() for s in content.split(",") if s.strip()]
                voorbeelden["synonyms"].extend(synonyms)

        # 5. Extract antonyms (comma-separated)
        if "Antoniemen" in data:
            content = data["Antoniemen"].strip()
            if content and content != "N/A" and content != "-":
                # Split by comma and clean
                antonyms = [a.strip() for a in content.split(",") if a.strip()]
                voorbeelden["antonyms"].extend(antonyms)

        # 6. Extract explanation/toelichting
        if "Toelichting" in data:
            content = data["Toelichting"].strip()
            if content and content != "N/A" and content != "-":
                voorbeelden["explanation"].append(content)

        return voorbeelden


class VoorbeeldenRecovery:
    """Recover voorbeelden to database."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path))
        self.cursor = self.conn.cursor()

    def recover_definition_voorbeelden(
        self, definition: dict, dry_run: bool = False
    ) -> int:
        """Recover voorbeelden for a definition."""
        def_id = definition["id"]
        voorbeelden = definition["voorbeelden"]

        # Count what we'll add
        total_new = 0
        for vb_type, items in voorbeelden.items():
            if vb_type == "sentence":
                # Skip sentence - already exists
                continue
            total_new += len(items)

        if total_new == 0:
            print(f"  ⏭️  ID {def_id} ({definition['begrip']}): geen nieuwe voorbeelden")
            return 0

        print(
            f"  🔄 ID {def_id} ({definition['begrip']}): {total_new} voorbeelden toevoegen"
        )

        # Show breakdown
        for vb_type, items in voorbeelden.items():
            if vb_type == "sentence":
                continue
            if items:
                print(f"     - {vb_type}: {len(items)}")

        if dry_run:
            return total_new

        # Insert each example type
        added = 0
        for vb_type, items in voorbeelden.items():
            if vb_type == "sentence":
                # Skip - already exists
                continue

            for i, text in enumerate(items, 1):
                try:
                    self.cursor.execute(
                        """
                        INSERT INTO definitie_voorbeelden (
                            definitie_id, voorbeeld_type, voorbeeld_tekst, voorbeeld_volgorde,
                            gegenereerd_door, actief
                        )
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (def_id, vb_type, text, i, "recovered", True),
                    )
                    added += 1
                except sqlite3.IntegrityError:
                    # Already exists
                    print(f"       ⚠️  {vb_type} #{i} bestaat al, overslaan")

        return added

    def commit(self):
        """Commit changes."""
        self.conn.commit()

    def close(self):
        """Close connection."""
        self.conn.close()


def main():
    """Main recovery function."""
    print("🔄 VOORBEELDEN RECOVERY")
    print("=" * 60)
    print("Herstel verloren voorbeelden na git branch switch")
    print("Data loss: 2025-10-30 15:43 (feature/DEF-54 → main)")
    print("=" * 60)

    # Paths
    project_root = Path(__file__).parent.parent
    db_path = project_root / "data" / "definities.db"

    # Affected IDs
    target_ids = {79, 82, 83, 84, 85, 86, 87, 88, 90, 91}

    # Export files that contain these IDs
    export_files = [
        project_root / "exports" / "definities_export_20251029_130927.txt",  # IDs 79-88
        project_root / "exports" / "definities_export_20251030_100359.txt",  # ID 90
        project_root / "exports" / "definities_export_20251030_101334.txt",  # ID 91
    ]

    # Check files exist
    for export_file in export_files:
        if not export_file.exists():
            print(f"⚠️  Export niet gevonden: {export_file.name}")

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
        parser = VoorbeeldenParser(export_file)
        definitions = parser.parse_all()

        # Filter for target IDs only
        target_defs = [d for d in definitions if d["id"] in target_ids]
        all_definitions.extend(target_defs)

        print(f"    Gevonden: {len(target_defs)} target definities")

    if not all_definitions:
        print("\n❌ Geen target definities gevonden!")
        return 1

    print(f"\n✅ Totaal gevonden: {len(all_definitions)} definities")
    print(f"   IDs: {sorted([d['id'] for d in all_definitions])}")

    # Dry run first
    print("\n🔍 DRY RUN - controleren wat er toegevoegd wordt...")
    recovery = VoorbeeldenRecovery(db_path)

    total_to_add = 0
    for definition in sorted(all_definitions, key=lambda d: d["id"]):
        count = recovery.recover_definition_voorbeelden(definition, dry_run=True)
        total_to_add += count

    recovery.close()

    if total_to_add == 0:
        print("\n✅ Niets te herstellen - alle voorbeelden zijn al aanwezig!")
        return 0

    print(f"\n⚠️  TOTAAL TE HERSTELLEN: {total_to_add} voorbeelden")

    # Ask for confirmation
    if sys.stdin.isatty():
        response = input("\nDoorgaan met recovery? (y/N): ").strip().lower()
        if response != "y":
            print("❌ Geannuleerd")
            return 0
    else:
        print("(Non-interactive mode: auto-confirming)")

    # Actual recovery
    print("\n🔄 Herstellen...")
    recovery = VoorbeeldenRecovery(db_path)

    total_added = 0
    for definition in sorted(all_definitions, key=lambda d: d["id"]):
        added = recovery.recover_definition_voorbeelden(definition, dry_run=False)
        total_added += added

    recovery.commit()
    recovery.close()

    print("\n" + "=" * 60)
    print("✅ RECOVERY COMPLEET!")
    print(f"   Hersteld: {total_added} voorbeelden")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
