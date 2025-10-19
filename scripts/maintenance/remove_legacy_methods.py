#!/usr/bin/env python3
"""
Remove legacy fallback methods from definition_orchestrator_v2.py

This script removes the following legacy methods that are no longer needed:
- _get_legacy_validation_service() (lines 896-921)
- _get_legacy_cleaning_service() (lines 923-954)
- _get_legacy_repository() (lines 956-959+)
"""

import sys
from pathlib import Path


def remove_legacy_methods():
    """Remove legacy fallback methods from the V2 orchestrator."""

    # Path to the file
    file_path = Path(
        "/Users/chrislehnen/Projecten/Definitie-app/src/services/orchestrators/definition_orchestrator_v2.py"
    )

    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        return False

    # Read the file
    with open(file_path, encoding="utf-8") as f:
        lines = f.readlines()

    print(f"Original file has {len(lines)} lines")

    # Lines to remove:
    # - _get_legacy_validation_service(): lines 896-921
    # - _get_legacy_cleaning_service(): lines 923-954
    # - _get_legacy_repository(): lines 956-964
    # Total: lines 896-964 (but keep line 895 - empty line before, and line 965 - empty line after)

    # Keep all lines except 896-964
    new_lines = []
    for i, line in enumerate(lines, 1):
        if i < 896 or i > 964:
            new_lines.append(line)
        elif i == 896:
            print(f"Starting to remove at line {i}: {line.strip()[:50]}...")
        elif i == 964:
            print(f"Last line removed at {i}: {line.strip()[:50]}...")

    print(f"New file will have {len(new_lines)} lines")
    print(f"Removed {len(lines) - len(new_lines)} lines")

    # Write the file back
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"✅ Successfully removed legacy methods from {file_path}")
    return True


def verify_removal():
    """Verify that legacy methods have been removed."""

    file_path = Path(
        "/Users/chrislehnen/Projecten/Definitie-app/src/services/orchestrators/definition_orchestrator_v2.py"
    )

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    legacy_methods = [
        "_get_legacy_validation_service",
        "_get_legacy_cleaning_service",
        "_get_legacy_repository",
    ]

    found_methods = []
    for method in legacy_methods:
        if method in content:
            found_methods.append(method)

    if found_methods:
        print(f"❌ ERROR: Legacy methods still found: {found_methods}")
        return False
    print("✅ All legacy methods successfully removed")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("REMOVING LEGACY FALLBACK METHODS FROM V2 ORCHESTRATOR")
    print("=" * 60)

    if remove_legacy_methods():
        verify_removal()
        print("\n✅ Legacy method removal complete!")
    else:
        print("\n❌ Failed to remove legacy methods")
        sys.exit(1)
