#!/usr/bin/env python3
"""Extract validation rule from Python file to YAML config."""

import ast
import sys
from pathlib import Path

import yaml


def extract_rule(rule_file: Path) -> dict:
    """Extract rule metadata from Python file."""

    with open(rule_file, encoding="utf-8") as f:
        content = f.read()

    # Parse Python AST
    tree = ast.parse(content)

    # Extract class name (e.g., ARAI01Validator)
    validator_class = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and "Validator" in node.name:
            validator_class = node
            break

    if not validator_class:
        raise ValueError(f"No validator class found in {rule_file}")

    # Extract docstring
    docstring = ast.get_docstring(validator_class) or ""

    # Extract patterns from validate method
    patterns = []
    for node in ast.walk(validator_class):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and "patroon" in target.id.lower():
                    # Extract pattern values
                    pass  # TODO: implement pattern extraction

    # Build config dict
    rule_id = rule_file.stem  # e.g., ARAI-01
    category = rule_id.split("-")[0]

    config = {
        "id": rule_id,
        "category": category,
        "priority": "medium",  # Default, will be updated manually
        "enabled": True,
        "metadata": {
            "naam": docstring.split("\n")[0] if docstring else rule_id,
            "uitleg": docstring,
            "version": "1.0",
            "code_reference": str(rule_file.resolve()),
        },
        "implementation": {
            "type": "regex",  # Default
            "patterns": patterns,
            "logic_description": "To be documented",
        },
        "validation": {
            "input_fields": ["definitie", "begrip", "context"],
            "output": {"success": "boolean", "message": "string", "score": "float"},
        },
        "examples": {"good": [], "bad": []},
        "generation_hints": [],
        "test_cases": [],
    }

    return config


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: extract_rule.py <rule_file.py>")
        sys.exit(1)

    rule_file = Path(sys.argv[1])
    config = extract_rule(rule_file)

    # Write YAML
    output_dir = Path("rebuild/extracted/validation") / config["category"].lower()
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{config['id']}.yaml"
    with open(output_file, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)

    print(f"✓ Extracted {config['id']} → {output_file}")
