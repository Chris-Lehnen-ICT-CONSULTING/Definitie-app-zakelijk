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


def _extract_pytestmark_block(content: str) -> str:
    """Extract the full pytestmark assignment block (may span multiple lines)."""
    lines = content.splitlines()
    block_lines: list[str] = []
    in_block = False
    bracket_depth = 0
    for line in lines:
        stripped = line.strip()
        if not in_block and stripped.startswith("pytestmark"):
            in_block = True
        if in_block:
            block_lines.append(stripped)
            bracket_depth += stripped.count("[") - stripped.count("]")
            if bracket_depth <= 0 and not stripped.endswith("\\"):
                break
    return " ".join(block_lines)


def check_file(filepath: Path) -> bool:
    """Return True if file has a pytestmark with a classification marker."""
    block = _extract_pytestmark_block(filepath.read_text())
    return any(f"pytest.mark.{m}" in block for m in CLASSIFICATION_MARKERS)


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
