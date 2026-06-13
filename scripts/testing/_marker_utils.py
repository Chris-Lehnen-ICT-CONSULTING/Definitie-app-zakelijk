"""Shared utilities for test marker scripts.

Single source of truth for classification markers and pytestmark parsing.
Used by both add_test_markers.py and check_test_markers.py.
"""

from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent.parent.parent / "tests"

EXCLUDED_DIRS = {"archived", "__pycache__", ".pytest_cache", "manual"}

# Classification markers (not functional markers like asyncio, skip, xfail)
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


def extract_pytestmark_block(content: str) -> str:
    """Extract the full pytestmark assignment block (may span multiple lines).

    Returns the joined block text, or empty string if no pytestmark found.
    """
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


def has_classification_marker(content: str) -> bool:
    """Check if file content has a pytestmark with a classification marker."""
    block = extract_pytestmark_block(content)
    return any(f"pytest.mark.{m}" in block for m in CLASSIFICATION_MARKERS)


def find_test_files() -> list[Path]:
    """Find all test_*.py files, excluding archived and __pycache__."""
    files = []
    for f in sorted(TESTS_DIR.rglob("test_*.py")):
        rel = f.relative_to(TESTS_DIR)
        if any(p in EXCLUDED_DIRS for p in rel.parts):
            continue
        files.append(f)
    return files
