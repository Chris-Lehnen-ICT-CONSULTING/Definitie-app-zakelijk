#!/usr/bin/env python3
"""
Script om JSON bestandsnamen van dash (-) naar underscore (_) te converteren.
Dit lost de inconsistentie op tussen JSON en Python bestandsnamen.
"""

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def fix_naming_consistency(regels_dir: Path, dry_run: bool = True):
    """
    Hernoem JSON files van dash naar underscore notatie.

    Args:
        regels_dir: Directory met toetsregels
        dry_run: Als True, toon alleen wat er zou gebeuren
    """
    if not regels_dir.exists():
        print(f"❌ Directory bestaat niet: {regels_dir}")
        return

    # Maak backup directory
    if not dry_run:
        backup_dir = (
            regels_dir.parent
            / f"regels_backup_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        )
        print(f"📁 Maak backup in: {backup_dir}")
        shutil.copytree(regels_dir, backup_dir)

    renamed_count = 0
    errors = []

    # Vind alle JSON files met dashes
    for json_file in regels_dir.glob("*.json"):
        if "-" in json_file.stem:
            old_name = json_file.name
            new_name = old_name.replace("-", "_")
            new_path = json_file.parent / new_name

            # Check of nieuwe naam al bestaat
            if new_path.exists():
                errors.append(f"⚠️  {old_name} → {new_name} (BESTAAT AL!)")
                continue

            # Check of er een matching Python file is
            expected_py = json_file.parent / f"{json_file.stem.replace('-', '_')}.py"
            if not expected_py.exists():
                errors.append(f"⚠️  {old_name} heeft geen matching Python file")

            if dry_run:
                print(f"📝 {old_name} → {new_name}")
            else:
                # Update ook de ID in de JSON file
                try:
                    with open(json_file, encoding="utf-8") as f:
                        data = json.load(f)

                    # Update ID van dash naar underscore
                    if "id" in data and "-" in data["id"]:
                        old_id = data["id"]
                        data["id"] = data["id"].replace("-", "_")
                        print(f"   📄 Update ID: {old_id} → {data['id']}")

                    # Schrijf aangepaste JSON
                    with open(json_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)

                    # Hernoem bestand
                    json_file.rename(new_path)
                    print(f"✅ {old_name} → {new_name}")

                except Exception as e:
                    errors.append(f"❌ Fout bij {old_name}: {e!s}")
                    continue

            renamed_count += 1

    # Rapportage
    print("\n📊 Samenvatting:")
    print(f"   - Te hernoemen: {renamed_count} bestanden")
    print(f"   - Fouten: {len(errors)}")

    if errors:
        print("\n⚠️  Problemen gevonden:")
        for error in errors:
            print(f"   {error}")

    if dry_run:
        print(
            "\n💡 Dit was een dry run. Gebruik --execute om daadwerkelijk te hernoemen."
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Fix naming consistency between JSON and Python toetsregel files",
        epilog="Example: python fix_naming_consistency.py --execute",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually rename files (default is dry-run)",
    )
    parser.add_argument(
        "--dir", type=Path, help="Custom directory to process (default: auto-detect)"
    )

    args = parser.parse_args()

    # Bepaal directory
    if args.dir:
        regels_dir = args.dir
    else:
        # Zoek vanaf script locatie (nu 2 levels omhoog vanuit tools/maintenance)
        regels_dir = (
            Path(__file__).parents[2] / "src" / "config" / "toetsregels" / "regels"
        )

    print("🔧 Fix Naming Consistency Script")
    print("=" * 40)
    print(f"📍 Directory: {regels_dir}")
    print(f"🔍 Mode: {'EXECUTE' if args.execute else 'DRY RUN'}")
    print(f"📅 Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    fix_naming_consistency(regels_dir, dry_run=not args.execute)
