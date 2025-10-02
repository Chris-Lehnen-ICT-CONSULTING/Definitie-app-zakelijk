#!/usr/bin/env python3
"""
Fix Documentation Issues Script
Automatisch corrigeren van gedetecteerde taalfouten in documentatie
"""

import os
import re
import glob
from pathlib import Path
from typing import Dict, List, Tuple
import argparse
from datetime import datetime

# Vertaal mappings voor systematische fouten
REPLACEMENTS = {
    # Taalfouten door automatische vertaling
    r'\bAuDanticatie\b': 'authenticatie',
    r'\bAuDanticeren\b': 'authenticeren',
    r'\bstEnaarden\b': 'standaarden',
    r'\bstEnaard\b': 'standaard',
    r'\bEnardized\b': 'gestandaardiseerd',
    r'\bupDatumd\b': 'bijgewerkt',
    r'\bupDatumen\b': 'bijwerken',
    r'\bHOOGer\b': 'hoger',
    r'\bTestdekking\b': 'testdekking',
    r'\bProductie\b': 'productie',
    r'\bEnantiori\b': 'anteriori',
    r'\bDan\b': 'dan',
    r'\b En \b': ' en ',
    r'\bVereisten\b': 'vereisten',
    r'\bAangemaakt\b': 'aangemaakt',
    r'\bAdhankelijkheden\b': 'afhankelijkheden',

    # SMART criteria vertalingen
    r'\*\*Specific\*\*': '**Specifiek**',
    r'\*\*Measurable\*\*': '**Meetbaar**',
    r'\*\*Achievable\*\*': '**Haalbaar**',
    r'\*\*Relevant\*\*': '**Relevant**',
    r'\*\*Time-bound\*\*': '**Tijdgebonden**',

    # Engelse fragmenten in SMART criteria
    r'Zero vulnerabilities in Beveiliging scans': 'Geen kwetsbaarheden in beveiligingsscans',
    r'KRITIEK for justitiesector': 'KRITIEK voor justitiesector',
    r'Must be operational before Productie deployment': 'Moet operationeel zijn voor productie-uitrol',
    r'Using established Beveiliging libraries En patterns': 'Met gebruik van gevestigde beveiligingsbibliotheken en patronen',
    r'gegevensbescherming compliance': 'gegevensbeschermingscompliance',
    r'100% Testdekking': '100% testdekking',

    # User story vertalingen
    r'\bWil ik\b': 'wil ik',
    r'\bZodat\b': 'zodat',
    r'\bGegeven\b': 'gegeven',
    r'\bWanneer\b': 'wanneer',

    # Algemene correcties
    r'Beveiliging': 'beveiliging',
    r'HOOG-quality': 'hoogwaardige',
    r'HOOGer-value': 'waardevoller',
}

class DocumentationFixer:
    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.fixed_files = []
        self.total_replacements = 0
        self.errors = []

    def fix_file(self, filepath: Path) -> Tuple[bool, int]:
        """Fix een enkel bestand"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content
            replacements_count = 0

            # Pas alle vervangingen toe
            for pattern, replacement in REPLACEMENTS.items():
                new_content, count = re.subn(pattern, replacement, content)
                if count > 0:
                    replacements_count += count
                    if self.verbose:
                        print(f"  - {pattern} → {replacement}: {count}x")
                content = new_content

            # Schrijf alleen als er wijzigingen zijn
            if content != original_content:
                if not self.dry_run:
                    # Maak backup
                    backup_path = filepath.with_suffix(filepath.suffix + '.backup')
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        f.write(original_content)

                    # Schrijf gefixte content
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)

                return True, replacements_count

            return False, 0

        except Exception as e:
            self.errors.append((filepath, str(e)))
            return False, 0

    def fix_directory(self, directory: Path, pattern: str = "*.md"):
        """Fix alle markdown bestanden in een directory"""
        files = list(directory.rglob(pattern))
        print(f"\n📁 Processing {len(files)} files in {directory}")

        for filepath in files:
            # Skip backup files
            if '.backup' in str(filepath):
                continue

            if self.verbose:
                print(f"\n📄 Processing: {filepath.relative_to(directory.parent)}")

            fixed, count = self.fix_file(filepath)

            if fixed:
                self.fixed_files.append(filepath)
                self.total_replacements += count
                if not self.verbose:
                    print(f"  ✅ Fixed: {filepath.relative_to(directory.parent)} ({count} replacements)")

    def print_summary(self):
        """Print samenvatting van fixes"""
        print("\n" + "="*80)
        print("📊 FIX SUMMARY")
        print("="*80)

        if self.dry_run:
            print("⚠️  DRY RUN MODE - No files were actually modified")

        print(f"\n✅ Files fixed: {len(self.fixed_files)}")
        print(f"🔄 Total replacements: {self.total_replacements}")

        if self.errors:
            print(f"\n❌ Errors encountered: {len(self.errors)}")
            for filepath, error in self.errors:
                print(f"  - {filepath}: {error}")

        if self.fixed_files:
            print(f"\n📝 Modified files:")
            for filepath in self.fixed_files[:10]:  # Show first 10
                print(f"  - {filepath.relative_to(Path.cwd())}")
            if len(self.fixed_files) > 10:
                print(f"  ... and {len(self.fixed_files) - 10} more")

def main():
    parser = argparse.ArgumentParser(description='Fix documentation language issues')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be fixed without making changes')
    parser.add_argument('--verbose', action='store_true',
                       help='Show detailed replacement information')
    parser.add_argument('--path', type=str, default='docs',
                       help='Path to documentation directory (default: docs)')

    args = parser.parse_args()

    # Get project root
    project_root = Path.cwd()
    docs_path = project_root / args.path

    if not docs_path.exists():
        print(f"❌ Error: Path {docs_path} does not exist")
        return 1

    print("🔧 Documentation Fixer")
    print("="*80)
    print(f"📁 Target directory: {docs_path}")
    print(f"🔍 Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"📊 Verbose: {args.verbose}")
    print("="*80)

    # Create fixer instance
    fixer = DocumentationFixer(dry_run=args.dry_run, verbose=args.verbose)

    # Fix documentation
    print("\n🔄 Starting fixes...")

    # Fix specific directories
    directories = [
        'requirements',
        'epics',
        'stories',
    ]

    for dir_name in directories:
        dir_path = docs_path / dir_name
        if dir_path.exists():
            fixer.fix_directory(dir_path)

    # Print summary
    fixer.print_summary()

    if not args.dry_run and fixer.fixed_files:
        print("\n💡 Tip: Backup files created with .backup extension")
        print("   To remove backups: find docs -name '*.backup' -delete")

    return 0

if __name__ == '__main__':
    exit(main())
