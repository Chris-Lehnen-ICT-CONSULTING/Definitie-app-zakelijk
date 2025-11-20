#!/usr/bin/env python3
"""Fix ambiguous Unicode characters in Python files.

Replaces:
- NON-BREAKING HYPHEN (‑, U+2011) → HYPHEN-MINUS (-, U+002D)
- EN DASH (–, U+2013) → HYPHEN-MINUS (-, U+002D)
"""

import sys
from pathlib import Path


def fix_unicode_chars(file_path: Path) -> bool:
    """Fix ambiguous Unicode characters in a file.

    Returns True if file was modified, False otherwise.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        original_content = content

        # Replace NON-BREAKING HYPHEN with HYPHEN-MINUS
        content = content.replace("\u2011", "-")

        # Replace EN DASH with HYPHEN-MINUS
        content = content.replace("\u2013", "-")

        # Replace LEFT SINGLE QUOTATION MARK with APOSTROPHE
        content = content.replace("\u2018", "'")

        # Replace RIGHT SINGLE QUOTATION MARK with APOSTROPHE
        content = content.replace("\u2019", "'")

        # Replace LEFT DOUBLE QUOTATION MARK with QUOTATION MARK
        content = content.replace("\u201C", '"')

        # Replace RIGHT DOUBLE QUOTATION MARK with QUOTATION MARK
        content = content.replace("\u201D", '"')

        # Remove INFORMATION SOURCE emoji (ℹ️ → i)
        # Note: Keep checkmark ✅ and cross ❌ as they're intentional visual markers
        content = content.replace("ℹ️", "i")
        content = content.replace("ℹ", "i")

        # Replace HEAVY PLUS SIGN with PLUS SIGN
        content = content.replace("➕", "+")

        # Replace MULTIPLICATION SIGN with LETTER X
        content = content.replace("×", "x")

        if content != original_content:
            file_path.write_text(content, encoding="utf-8")
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}", file=sys.stderr)
        return False


def main():
    """Fix Unicode characters in all Python files."""
    src_dir = Path(__file__).parent.parent / "src"
    config_dir = Path(__file__).parent.parent / "config"

    total_fixed = 0

    for directory in [src_dir, config_dir]:
        if not directory.exists():
            continue

        for py_file in directory.rglob("*.py"):
            # Skip __pycache__ and similar
            if "__pycache__" in str(py_file) or "archief" in str(py_file).lower():
                continue

            if fix_unicode_chars(py_file):
                print(f"Fixed: {py_file.relative_to(directory.parent)}")
                total_fixed += 1

    print(f"\nTotal files fixed: {total_fixed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
