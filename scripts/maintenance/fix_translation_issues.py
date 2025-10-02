#!/usr/bin/env python3
"""
Script om vertaalproblemen in documentatie op te lossen.
Fixes translation issues in documentation files.
"""

import re
from pathlib import Path


def fix_authentication_typos(file_path: Path) -> int:
    """Fix 'auDantication' typos to 'authenticatie'."""
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    original = content

    # Fix various forms of the typo
    replacements = [
        (r"auDantication", "authenticatie"),
        (r"AuDantication", "Authenticatie"),
        (r"auDanticatie", "authenticatie"),
        (r"AuDanticatie", "Authenticatie"),
        (r"auDanticeren", "authenticeren"),
        (r"geauDanticeerd", "geauthenticeerd"),
        (r"re-auDantication", "re-authenticatie"),
    ]

    count = 0
    for pattern, replacement in replacements:
        content, n = re.subn(pattern, replacement, content)
        count += n

    if content != original:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    return count


def fix_todo_placeholders(file_path: Path) -> int:
    """Replace TE_DOEN placeholders with proper content."""
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    original = content

    # Context-aware replacements
    replacements = [
        (
            r"TE_DOEN - File path to be determined",
            "Nog te bepalen tijdens implementatie",
        ),
        (
            r"TE_DOEN - Auth service not yet implemented",
            "Authenticatie service nog te implementeren",
        ),
        (r"TE_DOEN - English locale planned", "Engelse lokalisatie gepland"),
        (r"TE_DOEN", "Nog te bepalen"),
    ]

    count = 0
    for pattern, replacement in replacements:
        content, n = re.subn(pattern, replacement, content)
        count += n

    if content != original:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    return count


def process_directory(directory: Path, patterns: list[str]) -> dict[str, int]:
    """Process all matching files in a directory."""
    stats = {
        "files_processed": 0,
        "auth_fixes": 0,
        "todo_fixes": 0,
    }

    for pattern in patterns:
        for file_path in directory.glob(pattern):
            if file_path.is_file():
                print(f"Processing: {file_path}")

                auth_count = fix_authentication_typos(file_path)
                todo_count = fix_todo_placeholders(file_path)

                if auth_count > 0:
                    print(f"  - Fixed {auth_count} authentication typos")
                    stats["auth_fixes"] += auth_count

                if todo_count > 0:
                    print(f"  - Fixed {todo_count} TODO placeholders")
                    stats["todo_fixes"] += todo_count

                if auth_count > 0 or todo_count > 0:
                    stats["files_processed"] += 1

    return stats


def main():
    """Main execution function."""
    project_root = Path("/Users/chrislehnen/Projecten/Definitie-app")
    docs_dir = project_root / "docs"

    print("🔧 Starting translation issue fixes...")
    print("=" * 50)

    # Process different document types
    directories = [
        (docs_dir / "requirements", ["*.md"]),
        (docs_dir / "epics", ["*.md"]),
        (docs_dir / "stories", ["*.md"]),
    ]

    total_stats = {
        "files_processed": 0,
        "auth_fixes": 0,
        "todo_fixes": 0,
    }

    for directory, patterns in directories:
        if directory.exists():
            print(f"\n📁 Processing {directory.relative_to(project_root)}...")
            stats = process_directory(directory, patterns)

            for key in total_stats:
                total_stats[key] += stats[key]

    # Print summary
    print("\n" + "=" * 50)
    print("✅ Translation fixes completed!")
    print("📊 Summary:")
    print(f"  - Files modified: {total_stats['files_processed']}")
    print(f"  - Authentication typos fixed: {total_stats['auth_fixes']}")
    print(f"  - TODO placeholders replaced: {total_stats['todo_fixes']}")

    return total_stats


if __name__ == "__main__":
    main()
