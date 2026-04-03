#!/usr/bin/env python3
"""Add pytest classification markers to test files that are missing them.

Usage:
    python scripts/testing/add_test_markers.py          # dry-run (default)
    python scripts/testing/add_test_markers.py --apply   # apply changes
"""

import argparse
import re
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent.parent.parent / "tests"

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

# Directory -> marker(s) mapping
DIRECTORY_MARKERS: dict[str, list[str]] = {
    "unit": ["unit"],
    "integration": ["integration"],
    "smoke": ["smoke"],
    "regression": ["regression"],
    "performance": ["performance"],
    "contracts": ["contract"],
    "compliance": ["compliance"],
    "database": ["integration"],
    "golden": ["golden"],
    "repositories": ["integration"],
    "functionality": ["integration", "slow"],
    "rate_limiting": ["performance"],
    "debug": ["unit"],
    "manual": ["integration"],
    "ci": ["unit"],
    "scripts": ["unit"],
    "utils": ["unit"],
    "monitoring": ["unit"],
    "security": ["unit"],
    "validation": ["unit"],
    "validation_rules": ["unit"],
    "ui": ["unit"],
    "legacy": ["regression"],
}

# Filename pattern -> marker(s)
FILENAME_PATTERNS: list[tuple[str, list[str]]] = [
    (r"_integration", ["integration"]),
    (r"_performance", ["performance"]),
    (r"_acceptance", ["acceptance"]),
    (r"_regression", ["regression"]),
    (r"_smoke", ["smoke"]),
    (r"_contract", ["contract"]),
    (r"_red\b", ["red_phase"]),
    (r"_antipattern", ["antipattern"]),
]


def find_test_files() -> list[Path]:
    """Find all test_*.py files, excluding archived and __pycache__."""
    files = []
    for f in sorted(TESTS_DIR.rglob("test_*.py")):
        rel = f.relative_to(TESTS_DIR)
        parts = rel.parts
        if any(p in ("archived", "__pycache__", ".pytest_cache") for p in parts):
            continue
        files.append(f)
    return files


def _extract_pytestmark_block(content: str) -> str | None:
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
    return " ".join(block_lines) if block_lines else None


def get_existing_pytestmark(content: str) -> tuple[bool, bool, str | None]:
    """Check if file has pytestmark.

    Returns:
        (has_pytestmark, has_classification_marker, existing_pytestmark_line)
    """
    block = _extract_pytestmark_block(content)
    if block is None:
        return False, False, None
    has_classification = any(
        f"pytest.mark.{m}" in block for m in CLASSIFICATION_MARKERS
    )
    return True, has_classification, block


def has_per_function_markers(content: str) -> list[str]:
    """Find per-function classification markers."""
    found = []
    for match in re.finditer(r"@pytest\.mark\.(\w+)", content):
        marker_name = match.group(1)
        if marker_name in CLASSIFICATION_MARKERS:
            found.append(marker_name)
    return found


def classify_by_directory(filepath: Path) -> list[str] | None:
    """Classify based on directory name."""
    rel = filepath.relative_to(TESTS_DIR)
    parts = rel.parts

    if len(parts) > 1:
        top_dir = parts[0]
        if top_dir in DIRECTORY_MARKERS:
            return DIRECTORY_MARKERS[top_dir]

    return None


def classify_by_filename(filepath: Path) -> list[str] | None:
    """Classify based on filename patterns."""
    stem = filepath.stem
    for pattern, markers in FILENAME_PATTERNS:
        if re.search(pattern, stem):
            return markers
    return None


def classify_by_imports(content: str) -> list[str] | None:
    """Classify based on import analysis."""
    has_db = bool(
        re.search(
            r"(?:import sqlite3|from.*database.*import|from.*definitie_repository.*import)",
            content,
        )
    )
    has_mock = bool(
        re.search(
            r"(?:from unittest\.mock import|from unittest import mock|Mock\(|MagicMock\(|AsyncMock\(|@patch)",
            content,
        )
    )

    if has_db and not has_mock:
        return ["integration"]

    return None


def classify_file(filepath: Path, content: str) -> tuple[str, list[str]]:
    """Classify a test file and return (action, markers).

    Actions: SKIP, CONVERT, ADD
    """
    has_pytestmark, has_classification, existing_line = get_existing_pytestmark(content)

    if has_pytestmark and has_classification:
        return "SKIP", []

    # Determine markers using priority chain
    markers = classify_by_directory(filepath)
    if not markers:
        markers = classify_by_filename(filepath)
    if not markers:
        markers = classify_by_imports(content)
    if not markers:
        # Check per-function markers for dominant marker
        per_func = has_per_function_markers(content)
        if per_func:
            from collections import Counter

            most_common = Counter(per_func).most_common(1)[0][0]
            markers = [most_common]
    if not markers:
        markers = ["unit"]

    if has_pytestmark and not has_classification:
        return "CONVERT", markers

    return "ADD", markers


def find_insert_position(lines: list[str]) -> int:
    """Find the line index where pytestmark should be inserted.

    Insert after the last top-level import, before the first class/def/decorator.
    Only counts imports at indentation level 0 (not inside functions/classes).
    """
    last_import = -1
    in_docstring = False
    docstring_char = None

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Track module-level docstrings
        if not stripped:
            continue
        if stripped.startswith(('"""', "'''")):
            triple = stripped[:3]
            # Count occurrences to detect single-line vs multi-line docstrings
            if stripped.count(triple) >= 2:
                # Single-line docstring like """text""" — skip
                continue
            if not in_docstring:
                in_docstring = True
                docstring_char = triple
                continue
        if in_docstring:
            if docstring_char and docstring_char in stripped:
                in_docstring = False
            continue

        # Only consider top-level imports (no leading whitespace)
        if line and not line[0].isspace() and stripped.startswith(("import ", "from ")):
            # Handle multi-line imports
            if stripped.endswith("\\") or (
                stripped.endswith("(") and ")" not in stripped
            ):
                j = i + 1
                while j < len(lines):
                    if ")" in lines[j] or not lines[j].strip().endswith(("\\", ",")):
                        last_import = j
                        break
                    j += 1
            else:
                last_import = i

        # Stop at first top-level class or function definition
        if line and not line[0].isspace() and stripped.startswith(("class ", "def ")):
            break

    return last_import + 1


def has_pytest_import(lines: list[str]) -> bool:
    """Check if 'import pytest' is already present."""
    return any(re.match(r"^\s*import pytest\s*$", line) for line in lines)


def format_markers(markers: list[str]) -> str:
    """Format markers as pytestmark assignment."""
    if len(markers) == 1:
        return f"[pytest.mark.{markers[0]}]"
    parts = ", ".join(f"pytest.mark.{m}" for m in markers)
    return f"[{parts}]"


def _is_balanced(text: str) -> bool:
    """Check if parentheses and brackets are balanced in text."""
    depth_paren = 0
    depth_bracket = 0
    in_string = False
    string_char = None

    for ch in text:
        if in_string:
            if ch == string_char:
                in_string = False
            continue
        if ch in ('"', "'"):
            in_string = True
            string_char = ch
        elif ch == "(":
            depth_paren += 1
        elif ch == ")":
            depth_paren -= 1
        elif ch == "[":
            depth_bracket += 1
        elif ch == "]":
            depth_bracket -= 1

    return depth_paren == 0 and depth_bracket == 0


def apply_marker_to_file(filepath: Path, markers: list[str], action: str) -> str:
    """Apply marker to a file. Returns the modified content."""
    content = filepath.read_text()
    lines = content.splitlines()

    if action == "CONVERT":
        # Find existing pytestmark and collect the full expression (may be multi-line)
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("pytestmark"):
                # Collect the full pytestmark expression (handles multi-line)
                start_line = i
                full_expr_lines = [line]
                # Check if expression is complete (balanced parens/brackets)
                full_text = line
                while not _is_balanced(full_text) and i + 1 < len(lines):
                    i += 1
                    full_expr_lines.append(lines[i])
                    full_text += "\n" + lines[i]
                end_line = i

                # Extract the RHS of the assignment
                match = re.match(r"pytestmark\s*=\s*(.*)", full_text, re.DOTALL)
                if match:
                    existing_expr = match.group(1).strip()
                    new_markers = ", ".join(f"pytest.mark.{m}" for m in markers)

                    if existing_expr.startswith("["):
                        # Already a list — insert new markers at the start
                        inner = existing_expr[1:-1].strip()
                        replacement = f"pytestmark = [{new_markers}, {inner}]"
                    else:
                        # Single expression — wrap in list
                        replacement = f"pytestmark = [{new_markers}, {existing_expr}]"

                    # Replace the full range of lines
                    lines[start_line : end_line + 1] = [replacement]
                break
        return "\n".join(lines) + "\n"

    # Action == ADD
    insert_at = find_insert_position(lines)

    new_lines = lines[:insert_at]

    # Add import pytest if needed
    if not has_pytest_import(lines):
        new_lines.append("import pytest")

    # Add blank line before pytestmark if previous line isn't blank
    if new_lines and new_lines[-1].strip():
        new_lines.append("")

    new_lines.append(f"pytestmark = {format_markers(markers)}")

    # Add blank line after if next line isn't blank
    remaining = lines[insert_at:]
    if remaining and remaining[0].strip():
        new_lines.append("")

    new_lines.extend(remaining)
    return "\n".join(new_lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Add pytest markers to test files")
    parser.add_argument(
        "--apply", action="store_true", help="Apply changes (default: dry-run)"
    )
    args = parser.parse_args()

    files = find_test_files()
    print(f"Found {len(files)} test files\n")

    stats = {"SKIP": 0, "ADD": 0, "CONVERT": 0}
    actions: list[tuple[Path, str, list[str]]] = []

    for filepath in files:
        content = filepath.read_text()
        action, markers = classify_file(filepath, content)
        stats[action] += 1

        rel = filepath.relative_to(TESTS_DIR)
        if action == "SKIP":
            print(f"  [SKIP]    {rel}")
        elif action == "CONVERT":
            print(f"  [CONVERT] {rel} -> +{', '.join(markers)}")
            actions.append((filepath, action, markers))
        else:
            print(f"  [ADD]     {rel} -> {', '.join(markers)}")
            actions.append((filepath, action, markers))

    print(f"\n{'='*60}")
    print(f"SKIP:    {stats['SKIP']:>3} (already have classification marker)")
    print(f"ADD:     {stats['ADD']:>3} (new pytestmark needed)")
    print(f"CONVERT: {stats['CONVERT']:>3} (add classification to existing pytestmark)")
    print(f"TOTAL:   {sum(stats.values()):>3}")

    if not args.apply:
        print("\nDry-run complete. Use --apply to make changes.")
        return 0

    print(f"\nApplying changes to {len(actions)} files...")
    errors = 0
    for filepath, action, markers in actions:
        try:
            new_content = apply_marker_to_file(filepath, markers, action)
            filepath.write_text(new_content)
        except Exception as e:
            print(f"  ERROR: {filepath.relative_to(TESTS_DIR)}: {e}")
            errors += 1

    print(f"Done. {len(actions) - errors} files modified, {errors} errors.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
