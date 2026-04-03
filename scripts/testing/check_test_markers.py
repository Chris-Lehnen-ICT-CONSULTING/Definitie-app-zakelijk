#!/usr/bin/env python3
"""CI guard: verify all test files have a classification marker.

Exits with code 1 if any test file is missing a pytestmark with a
classification marker. Prevents regression after DEF-397.

Usage:
    python scripts/testing/check_test_markers.py
    make test-markers-check
"""

import sys

from _marker_utils import find_test_files, has_classification_marker


def main() -> int:
    files = find_test_files()
    missing = [f for f in files if not has_classification_marker(f.read_text())]

    if missing:
        print(f"FAIL: {len(missing)} test file(s) missing classification marker:\n")
        for m in missing:
            print(f"  {m.name}")
        print("\nAdd pytestmark = [pytest.mark.<marker>] to each file.")
        print("Run: python scripts/testing/add_test_markers.py --dry-run")
        return 1

    print(f"OK: All {len(files)} test files have classification markers.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
