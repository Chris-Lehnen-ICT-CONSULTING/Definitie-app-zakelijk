#!/usr/bin/env python3
"""
Migrate validation rules from JSON+Python to consolidated YAML format.

Converts dual-format validation rules to single YAML files suitable for rebuild.
"""

import ast
import json
from pathlib import Path
from typing import Any

import yaml

SOURCE_JSON_DIR = Path("src/toetsregels/regels")
SOURCE_PY_DIR = Path("src/toetsregels/regels")
TARGET_DIR = Path("rebuild/config/validation_rules")


def extract_python_metadata(py_file: Path) -> dict[str, Any]:
    """Extract metadata from Python validation rule file."""
    try:
        with open(py_file, encoding="utf-8") as f:
            content = f.read()

        # Parse Python AST to extract docstrings and class info
        tree = ast.parse(content)

        metadata = {
            "implementation": "python",
            "source_file": str(py_file),
            "validation_logic": "See Python implementation for complex validation",
        }

        # Extract class docstring if available
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                docstring = ast.get_docstring(node)
                if docstring:
                    metadata["validation_description"] = docstring.strip()
                break

        return metadata
    except Exception as e:
        return {"implementation": "python", "error": f"Could not parse: {e}"}


def convert_json_to_yaml(json_file: Path) -> dict[str, Any]:
    """Convert JSON validation rule to YAML structure."""
    with open(json_file, encoding="utf-8") as f:
        data = json.load(f)

    # Create consolidated YAML structure
    yaml_data = {
        "id": data.get("id"),
        "name": data.get("naam"),
        "description": data.get("uitleg"),
        "explanation": data.get("toelichting"),
        "test_question": data.get("toetsvraag"),
        "metadata": {
            "priority": data.get("prioriteit"),
            "recommendation": data.get("aanbeveling"),
            "validity": data.get("geldigheid"),
            "status": data.get("status"),
            "type": data.get("type"),
            "theme": data.get("thema"),
            "source_document": data.get("brondocument"),
        },
        "validation": {
            "patterns": data.get("herkenbaar_patronen", []),
            "good_examples": data.get("goede_voorbeelden", []),
            "bad_examples": data.get("foute_voorbeelden", []),
        },
        "references": data.get("relatie", []),
    }

    return yaml_data


def migrate_single_rule(json_file: Path) -> bool:
    """Migrate a single validation rule to YAML."""
    rule_id = json_file.stem

    # Find corresponding Python file
    py_file = SOURCE_PY_DIR / f"{rule_id}.py"

    # Convert JSON to YAML structure
    yaml_data = convert_json_to_yaml(json_file)

    # Add Python metadata if file exists
    if py_file.exists():
        py_metadata = extract_python_metadata(py_file)
        yaml_data["implementation_details"] = py_metadata

    # Write consolidated YAML
    target_file = TARGET_DIR / f"{rule_id}.yaml"
    with open(target_file, "w", encoding="utf-8") as f:
        yaml.dump(
            yaml_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False
        )

    return True


def main():
    """Migrate all validation rules."""
    print("🔄 Migrating validation rules JSON → YAML...")
    print(f"Source: {SOURCE_JSON_DIR}")
    print(f"Target: {TARGET_DIR}")

    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    json_files = sorted(SOURCE_JSON_DIR.glob("*.json"))

    migrated = 0
    failed = 0

    for json_file in json_files:
        try:
            if migrate_single_rule(json_file):
                migrated += 1
                print(f"✅ {json_file.stem}")
            else:
                failed += 1
                print(f"❌ {json_file.stem} - Migration failed")
        except Exception as e:
            failed += 1
            print(f"❌ {json_file.stem} - Error: {e}")

    print("\n📊 Migration complete:")
    print(f"   ✅ Migrated: {migrated}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📁 Output: {TARGET_DIR}")


if __name__ == "__main__":
    main()
