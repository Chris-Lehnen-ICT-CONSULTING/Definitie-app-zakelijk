#!/usr/bin/env python3
"""
Migration script voor US-201: Migreer alle get_container() calls naar cached versie.

Dit script vervangt alle directe aanroepen van get_container() met de nieuwe
cached versie uit utils.container_manager om dubbele initialisatie te voorkomen.
"""

import os
import re
import sys
from pathlib import Path


def migrate_file(file_path: Path) -> bool:
    """
    Migreer een enkel Python bestand.

    Args:
        file_path: Path naar het te migreren bestand

    Returns:
        True als het bestand is aangepast, False anders
    """
    content = file_path.read_text()
    original_content = content

    # Skip dit migratie script zelf
    if file_path.name == "migrate_to_cached_container.py":
        return False

    # Skip container.py zelf (bevat de originele definitie)
    if file_path.name == "container.py" and "def get_container(" in content:
        print(f"  ⏭️  Skip {file_path} (bevat originele definitie)")
        return False

    # Skip container_manager.py (bevat de nieuwe implementatie)
    if file_path.name == "container_manager.py":
        print(f"  ⏭️  Skip {file_path} (nieuwe implementatie)")
        return False

    # Check of het bestand get_container importeert/gebruikt
    if "get_container" not in content:
        return False

    # Pattern voor import statements
    import_patterns = [
        (r'from services\.container import (.*?)get_container',
         r'from utils.container_manager import get_cached_container'),
        (r'from services import (.*?)get_container',
         r'from utils.container_manager import get_cached_container'),
    ]

    # Check en vervang imports
    for pattern, replacement in import_patterns:
        if re.search(pattern, content):
            # Extract andere imports uit dezelfde regel
            match = re.search(pattern + r'([^,\n]*)', content)
            if match:
                other_imports = match.group(1)
                if other_imports.strip() and other_imports.strip()[0] == ',':
                    # Er zijn andere imports, behoud deze
                    parts = re.findall(r'from services[.\w]* import (.*)', content)
                    if parts:
                        imports_list = [i.strip() for p in parts for i in p.split(',')]
                        imports_list = [i for i in imports_list if i and 'get_container' not in i]
                        if imports_list:
                            # Voeg de oude imports toe als aparte regel
                            new_import = f"from services.container import {', '.join(imports_list)}"
                            content = re.sub(pattern + r'.*', replacement + '\n' + new_import, content)
                        else:
                            content = re.sub(pattern + r'.*', replacement, content)
                else:
                    content = re.sub(pattern + r'.*', replacement, content)

    # Pattern voor function calls
    call_patterns = [
        (r'\bget_container\(\)', 'get_cached_container()'),
        (r'\bget_container\(config\)', 'get_container_with_config(config)'),
        (r'\bget_container\(([^)]+)\)', r'get_container_with_config(\1)'),
    ]

    # Vervang function calls
    for pattern, replacement in call_patterns:
        content = re.sub(pattern, replacement, content)

    # Check of er wijzigingen zijn
    if content != original_content:
        # Voeg import toe als die er nog niet is
        if 'from utils.container_manager import' not in content:
            # Voeg import toe na de laatste import
            import_lines = []
            other_lines = []
            in_imports = True

            for line in content.splitlines():
                if in_imports and (line.startswith('import ') or line.startswith('from ')):
                    import_lines.append(line)
                elif in_imports and line.strip() and not line.startswith('#'):
                    in_imports = False
                    other_lines.append(line)
                else:
                    other_lines.append(line)

            # Voeg nieuwe import toe
            import_lines.append('from utils.container_manager import get_cached_container')

            # Recombineer
            content = '\n'.join(import_lines) + '\n\n' + '\n'.join(other_lines)

        # Schrijf aangepaste content terug
        file_path.write_text(content)
        return True

    return False


def main():
    """Hoofdfunctie voor de migratie."""
    print("🚀 Start migratie naar cached container (US-201)")
    print("=" * 60)

    # Project root
    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src"

    if not src_dir.exists():
        print(f"❌ Src directory niet gevonden: {src_dir}")
        sys.exit(1)

    # Vind alle Python bestanden
    python_files = list(src_dir.rglob("*.py"))
    print(f"📁 Gevonden {len(python_files)} Python bestanden in {src_dir}")

    # Migreer bestanden
    migrated_files = []
    for file_path in python_files:
        try:
            if migrate_file(file_path):
                migrated_files.append(file_path)
                print(f"  ✅ Gemigreerd: {file_path.relative_to(project_root)}")
            else:
                # Alleen log als het bestand get_container bevat maar niet gemigreerd
                if "get_container" in file_path.read_text():
                    print(f"  ⏭️  Geen wijziging: {file_path.relative_to(project_root)}")
        except Exception as e:
            print(f"  ❌ Fout bij {file_path.relative_to(project_root)}: {e}")

    # Resultaten
    print("=" * 60)
    print(f"✨ Migratie compleet!")
    print(f"📊 {len(migrated_files)} bestanden aangepast")

    if migrated_files:
        print("\n📝 Aangepaste bestanden:")
        for f in migrated_files:
            print(f"  - {f.relative_to(project_root)}")

        print("\n⚠️  BELANGRIJK:")
        print("  1. Review de wijzigingen met: git diff")
        print("  2. Test de applicatie grondig")
        print("  3. Commit met: git commit -m 'fix(US-201): migrate to cached container'")
    else:
        print("\n✅ Geen bestanden hoefden te worden aangepast")


if __name__ == "__main__":
    main()