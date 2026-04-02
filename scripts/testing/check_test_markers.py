#!/usr/bin/env python3
"""CI guard: verify all test files have a classification marker.

Exits with code 1 if any test file is missing a pytestmark with a
classification marker. Prevents regression after DEF-397.

Usage:
    python scripts/testing/check_test_markers.py
    make test-markers-check
"""

import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent.parent.parent / "tests"

CLASSIFICATION_MARKERS = {
    "unit",
    "integration",
    "smoke",
    "smoke_web_lookup",
    "contract",
    "compliance",
    "regression",
    "performance",
    "benchmark",
    "acceptance",
    "golden",
    "red_phase",
    "antipattern",
    "ontological_category",
    "slow",
    "tdd",
    "flaky",
    "baseline",
    "parity",
}


def check_file(filepath: Path) -> bool:
    """Return True if file has a pytestmark with a classification marker."""
    content = filepath.read_text()
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("pytestmark"):
            for marker in CLASSIFICATION_MARKERS:
                if f"pytest.mark.{marker}" in stripped:
                    return True
    return False


def main() -> int:
    missing = []

    for f in sorted(TESTS_DIR.rglob("test_*.py")):
        rel = f.relative_to(TESTS_DIR)
        parts = rel.parts
        if any(p in ("archived", "__pycache__", ".pytest_cache") for p in parts):
            continue
        if not check_file(f):
            missing.append(rel)

    if missing:
        print(f"FAIL: {len(missing)} test file(s) missing classification marker:\n")
        for m in missing:
            print(f"  {m}")
        print("\nAdd pytestmark = [pytest.mark.<marker>] to each file.")
        print("Run: python scripts/testing/add_test_markers.py --dry-run")
        return 1

    total = sum(
        1
        for _ in TESTS_DIR.rglob("test_*.py")
        if not any(
            p in ("archived", "__pycache__", ".pytest_cache")
            for p in _.relative_to(TESTS_DIR).parts
        )
    )
    print(f"OK: All {total} test files have classification markers.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
