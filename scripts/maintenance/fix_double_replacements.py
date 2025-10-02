#!/usr/bin/env python3
"""
Fix double-replacement issues from normalization script.
Fixes patterns like "OM (Openbaar Ministerie (OM) (OM))" to "OM (Openbaar Ministerie)"
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

def find_docs_directory() -> Path:
    """Find the docs directory relative to script location."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    docs_dir = project_root / 'docs'

    if not docs_dir.exists():
        raise FileNotFoundError(f"Docs directory not found at {docs_dir}")

    return docs_dir

def fix_double_replacements(content: str) -> Tuple[str, int]:
    """Fix double-replacement patterns in content."""
    fixes_made = 0

    # Fix patterns like "OM (Openbaar Ministerie (OM) (OM))" -> "OM (Openbaar Ministerie)"
    patterns = [
        (r'OM \(Openbaar Ministerie \(OM\) \(OM\)\)', 'OM (Openbaar Ministerie)'),
        (r'OM \(Openbaar Ministerie \(OM\)\)', 'OM (Openbaar Ministerie)'),
        (r'DJI \(Dienst Justitiële Inrichtingen \(DJI\) \(DJI\)\)', 'DJI (Dienst Justitiële Inrichtingen)'),
        (r'DJI \(Dienst Justitiële Inrichtingen \(DJI\)\)', 'DJI (Dienst Justitiële Inrichtingen)'),
        # Also fix standalone double parentheses
        (r'\(OM\) \(OM\)', '(OM)'),
        (r'\(DJI\) \(DJI\)', '(DJI)'),
        # Fix repeated terminology
        (r'Openbaar Ministerie \(OM\) \(OM\)', 'Openbaar Ministerie (OM)'),
        (r'Dienst Justitiële Inrichtingen \(DJI\) \(DJI\)', 'Dienst Justitiële Inrichtingen (DJI)'),
    ]

    for pattern, replacement in patterns:
        matches = len(re.findall(pattern, content))
        if matches > 0:
            content = re.sub(pattern, replacement, content)
            fixes_made += matches

    return content, fixes_made

def process_file(file_path: Path) -> int:
    """Process a single file to fix double replacements."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        fixed_content, fixes_made = fix_double_replacements(content)

        if fixes_made > 0:
            # Write the fixed content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"  Fixed {fixes_made} double-replacements in {file_path.name}")
            return fixes_made

        return 0

    except Exception as e:
        print(f"  Error processing {file_path}: {e}")
        return 0

def main():
    """Main function to fix double replacements in all documentation."""
    docs_dir = find_docs_directory()

    print("Fixing double-replacement issues in documentation...")
    print("-" * 60)

    total_fixes = 0
    files_fixed = 0

    # Process all markdown files
    for md_file in docs_dir.rglob('*.md'):
        # Skip backup files
        if '.backup' in str(md_file) or '.normbackup' in str(md_file):
            continue

        fixes = process_file(md_file)
        if fixes > 0:
            total_fixes += fixes
            files_fixed += 1

    print("-" * 60)
    print(f"Total fixes made: {total_fixes}")
    print(f"Files fixed: {files_fixed}")

    return 0

if __name__ == '__main__':
    exit(main())
