#!/usr/bin/env python3
"""Create pytest fixtures from production definitions."""

import json
from pathlib import Path


def create_fixtures(definitions_file: Path, output_dir: Path):
    """Generate pytest fixtures for baseline testing."""

    with open(definitions_file) as f:
        definitions = json.load(f)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Group by category
    by_category = {}
    for defn in definitions:
        cat = defn["categorie"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(defn)

    # Create fixture file
    fixture_file = output_dir / "baseline_fixtures.py"

    with open(fixture_file, "w", encoding="utf-8") as f:
        f.write('"""Pytest fixtures for baseline validation tests."""\n\n')
        f.write("import pytest\n")
        f.write("from typing import List, Dict\n\n")

        # All definitions fixture
        f.write("@pytest.fixture\n")
        f.write("def baseline_definitions() -> List[Dict]:\n")
        f.write('    """All 42 baseline definitions."""\n')
        f.write(
            f"    return {json.dumps(definitions, indent=4, ensure_ascii=False)}\n\n"
        )

        # Category fixtures
        for category, defs in by_category.items():
            fixture_name = f"baseline_definitions_{category.lower()}"
            f.write("@pytest.fixture\n")
            f.write(f"def {fixture_name}() -> List[Dict]:\n")
            f.write(f'    """Baseline definitions for category: {category}."""\n')
            f.write(f"    return {json.dumps(defs, indent=4, ensure_ascii=False)}\n\n")

        # High-quality subset
        high_quality = [d for d in definitions if d.get("validation_score", 0) >= 0.9]
        f.write("@pytest.fixture\n")
        f.write("def baseline_high_quality() -> List[Dict]:\n")
        f.write('    """High-quality baseline definitions (score >= 0.9)."""\n')
        f.write(
            f"    return {json.dumps(high_quality, indent=4, ensure_ascii=False)}\n\n"
        )

        # Edge cases
        edge_cases = [d for d in definitions if d.get("validation_score", 1.0) < 0.8]
        f.write("@pytest.fixture\n")
        f.write("def baseline_edge_cases() -> List[Dict]:\n")
        f.write('    """Edge case baseline definitions (score < 0.8)."""\n')
        f.write(
            f"    return {json.dumps(edge_cases, indent=4, ensure_ascii=False)}\n\n"
        )

    print(f"✓ Created fixture file: {fixture_file}")
    print(f"  Total definitions: {len(definitions)}")
    print(f"  Categories: {len(by_category)}")
    print(f"  High quality: {len(high_quality)}")
    print(f"  Edge cases: {len(edge_cases)}")


if __name__ == "__main__":
    definitions_file = Path("rebuild/extracted/tests/production_definitions.json")
    output_dir = Path("rebuild/extracted/tests/fixtures")

    create_fixtures(definitions_file, output_dir)
