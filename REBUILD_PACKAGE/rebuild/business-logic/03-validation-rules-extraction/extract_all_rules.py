#!/usr/bin/env python3
"""
Validation Rules Extraction Script
Extracts ALL validation rules into detailed markdown documentation.

Agent 3: Validation Rules Expert
Date: 2025-10-02
"""

import json
import re
from pathlib import Path
from typing import Any

# Base paths
RULES_DIR = Path("/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels")
OUTPUT_DIR = Path(
    "/Users/chrislehnen/Projecten/Definitie-app/rebuild/business-logic/03-validation-rules-extraction"
)

# Category information
CATEGORIES = {
    "ARAI": {
        "name": "Aristotelian Structure",
        "description": "Rules ensuring Aristotelian definitional structure",
    },
    "CON": {"name": "Context", "description": "Rules for context-specific formulation"},
    "ESS": {
        "name": "Essential",
        "description": "Rules for essential definitional elements",
    },
    "INT": {
        "name": "Integrity",
        "description": "Rules for data integrity and consistency",
    },
    "SAM": {"name": "Semantic", "description": "Rules for semantic coherence"},
    "STR": {"name": "Structure", "description": "Rules for structural validation"},
    "VER": {"name": "Relation", "description": "Rules for relationship validation"},
    "DUP": {"name": "Duplicate", "description": "Rules for duplicate detection"},
    "VAL": {"name": "Validation", "description": "Basic validation rules"},
}


def extract_python_info(py_file: Path) -> dict[str, Any]:
    """Extract information from Python validator file."""
    info = {
        "file_path": str(py_file),
        "class_name": None,
        "methods": [],
        "patterns": [],
        "thresholds": [],
        "dependencies": [],
        "line_count": 0,
    }

    try:
        with open(py_file, encoding="utf-8") as f:
            content = f.read()
            info["line_count"] = len(content.split("\n"))

            # Extract class name
            class_match = re.search(r"class\s+(\w+)", content)
            if class_match:
                info["class_name"] = class_match.group(1)

            # Extract imports
            import_matches = re.findall(
                r"^(?:from|import)\s+(.+?)(?:\s+import|\n)", content, re.MULTILINE
            )
            info["dependencies"] = import_matches

            # Extract regex patterns
            pattern_matches = re.findall(r'r["\'](.+?)["\']', content)
            info["patterns"] = pattern_matches

            # Extract numeric thresholds (magic numbers)
            threshold_matches = re.findall(
                r"(?:score|threshold|limit|max|min)\s*[=:]\s*([0-9.]+)",
                content,
                re.IGNORECASE,
            )
            info["thresholds"] = list(set(threshold_matches))

    except Exception as e:
        print(f"Error reading {py_file}: {e}")

    return info


def extract_json_config(json_file: Path) -> dict[str, Any]:
    """Extract configuration from JSON file."""
    if not json_file.exists():
        return {}

    try:
        with open(json_file, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading {json_file}: {e}")
        return {}


def generate_rule_documentation(
    rule_id: str, py_info: dict, json_config: dict, category: str
) -> str:
    """Generate markdown documentation for a single rule."""

    # Normalize rule ID
    display_id = rule_id.replace("_", "-")

    # Extract key information
    naam = json_config.get("naam", "Unknown")
    uitleg = json_config.get("uitleg", "No explanation available")
    prioriteit = json_config.get("prioriteit", "unknown")
    status = json_config.get("status", "active")

    herkenbaar_patronen = json_config.get("herkenbaar_patronen", [])
    goede_voorbeelden = json_config.get("goede_voorbeelden", [])
    foute_voorbeelden = json_config.get("foute_voorbeelden", [])

    relatie = json_config.get("relatie", [])
    brondocument = json_config.get("brondocument", "Unknown")

    # Build markdown
    md = f"""# {display_id}: {naam}

## Metadata
- **ID:** {display_id}
- **Category:** {category}
- **Priority:** {prioriteit}
- **Status:** {status}
- **Source File:** `{py_info.get('file_path', 'unknown')}`
- **Class Name:** `{py_info.get('class_name', 'unknown')}`
- **Lines of Code:** {py_info.get('line_count', 0)}

## Business Purpose

### What
{uitleg}

### Why
{json_config.get('toelichting', 'Business rationale not explicitly documented.')}

### When Applied
Applied to: {json_config.get('geldigheid', 'all definitions')}
Recommendation: {json_config.get('aanbeveling', 'recommended')}

## Implementation

### Algorithm
```python
# Validation Logic (from {py_info.get('class_name', 'Validator')})
def validate(definitie: str, begrip: str, context: dict | None = None) -> tuple[bool, str, float]:
    # 1. Extract patterns from config
    # 2. Match patterns against definition
    # 3. Check good/bad examples
    # 4. Return (success, message, score)
    pass
```

**Key Steps:**
1. Load recognizable patterns from JSON config
2. Use regex matching to find violations
3. Compare with good/bad examples
4. Calculate score: 1.0 (pass), 0.5 (warning), 0.0 (fail)

### Patterns
"""

    if herkenbaar_patronen:
        md += (
            "```python\n# Regex patterns used for detection\nherkenbaar_patronen = [\n"
        )
        for pattern in herkenbaar_patronen:
            md += f'    r"{pattern}",\n'
        md += "]\n```\n\n"
    else:
        md += "*No specific patterns defined*\n\n"

    md += """### Thresholds
| Threshold | Value | Usage | Notes |
|-----------|-------|-------|-------|
| Pass score | 1.0 | Perfect validation | No violations found |
| Warning score | 0.5 | Partial pass | Minor issues detected |
| Fail score | 0.0 | Validation failed | Violations found |
"""

    if py_info.get("thresholds"):
        for threshold in py_info["thresholds"]:
            md += f"| Extracted value | {threshold} | Used in implementation | See Python code |\n"

    md += "\n"

    # Error messages
    md += """### Error Messages
- **Pass:** "✔️ {rule_id}: [validation passed message]"
- **Warning:** "🟡 {rule_id}: [warning message with details]"
- **Fail:** "❌ {rule_id}: [failure message with found violations]"

"""

    # Test cases
    md += "## Test Cases\n\n### Good Examples (Should PASS)\n"
    if goede_voorbeelden:
        for i, example in enumerate(goede_voorbeelden, 1):
            md += f'{i}. "{example}"\n'
    else:
        md += "*No good examples provided*\n"

    md += "\n### Bad Examples (Should FAIL)\n"
    if foute_voorbeelden:
        for i, example in enumerate(foute_voorbeelden, 1):
            md += f'{i}. "{example}"\n'
    else:
        md += "*No bad examples provided*\n"

    md += "\n### Edge Cases\n"
    md += "- Empty definition\n"
    md += "- Very short definition (< 10 characters)\n"
    md += "- Very long definition (> 500 characters)\n"
    md += "- Special characters and unicode\n"
    md += "- Multiple pattern matches\n\n"

    # Dependencies
    md += "## Dependencies\n"
    if py_info.get("dependencies"):
        md += "**Imports:**\n"
        for dep in py_info["dependencies"]:
            md += f"- `{dep}`\n"
    else:
        md += "- None (standalone validator)\n"

    md += "\n**Called by:**\n- ModularValidationService\n- ValidationOrchestratorV2\n\n"

    # ASTRA references
    md += "## ASTRA References\n"
    if relatie:
        for rel in relatie:
            fulltext = rel.get("fulltext", "Unknown")
            fullurl = rel.get("fullurl", "")
            md += f"- **Guideline:** {fulltext}\n"
            if fullurl:
                md += f"- **URL:** [{fullurl}]({fullurl})\n"
    else:
        md += "- **Source:** " + brondocument + "\n"

    md += f"\n**Compliance requirement:** {json_config.get('aanbeveling', 'recommended')}\n\n"

    # Notes
    md += "## Notes\n"
    md += f"- **Type:** {json_config.get('type', 'general')}\n"
    md += f"- **Theme:** {json_config.get('thema', 'general')}\n"
    if json_config.get("toetsvraag"):
        md += f"- **Test Question:** {json_config['toetsvraag']}\n"

    md += "\n## Extraction Date\n2025-10-02\n"

    return md


def get_category_from_rule_id(rule_id: str) -> str:
    """Extract category from rule ID."""
    # Handle various formats: ARAI-01, ARAI01, ARAI_01, etc.
    for cat in CATEGORIES:
        if rule_id.upper().startswith(cat):
            return cat
    return "VAL"  # Default


def main():
    """Main extraction process."""
    print("=" * 80)
    print("VALIDATION RULES EXTRACTION")
    print("=" * 80)
    print()

    # Find all Python rule files
    py_files = sorted(RULES_DIR.glob("*.py"))
    py_files = [f for f in py_files if not f.name.startswith("__")]

    print(f"Found {len(py_files)} Python rule files")
    print()

    rules_by_category = {}
    all_rules = []

    for py_file in py_files:
        rule_id = py_file.stem  # e.g., "ARAI-01" or "ARAI01"
        print(f"Processing: {rule_id}")

        # Find corresponding JSON
        json_candidates = [
            RULES_DIR / f"{rule_id}.json",
            RULES_DIR / f"{rule_id.replace('-', '_')}.json",
            RULES_DIR / f"{rule_id.replace('_', '-')}.json",
        ]

        json_file = None
        for candidate in json_candidates:
            if candidate.exists():
                json_file = candidate
                break

        # Extract information
        py_info = extract_python_info(py_file)
        json_config = extract_json_config(json_file) if json_file else {}

        category = get_category_from_rule_id(rule_id)

        # Generate documentation
        doc = generate_rule_documentation(rule_id, py_info, json_config, category)

        # Write to file
        output_file = OUTPUT_DIR / category / f"{rule_id.replace('_', '-')}.md"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(doc)

        print(f"  → Written to: {output_file}")

        # Track for index
        if category not in rules_by_category:
            rules_by_category[category] = []

        rules_by_category[category].append(
            {
                "id": rule_id,
                "name": json_config.get("naam", "Unknown"),
                "priority": json_config.get("prioriteit", "unknown"),
                "file": output_file.name,
            }
        )

        all_rules.append(
            {
                "id": rule_id,
                "category": category,
                "name": json_config.get("naam", "Unknown"),
                "priority": json_config.get("prioriteit", "unknown"),
            }
        )

    print()
    print("=" * 80)
    print(f"EXTRACTED {len(all_rules)} RULES")
    print("=" * 80)
    print()

    # Generate category READMEs
    for category, rules in rules_by_category.items():
        readme_content = generate_category_readme(category, rules)
        readme_file = OUTPUT_DIR / category / "README.md"

        with open(readme_file, "w", encoding="utf-8") as f:
            f.write(readme_content)

        print(f"Created category README: {category} ({len(rules)} rules)")

    # Generate master index
    master_index = generate_master_index(rules_by_category, all_rules)
    index_file = OUTPUT_DIR / "README.md"

    with open(index_file, "w", encoding="utf-8") as f:
        f.write(master_index)

    print(f"\nCreated master index: {index_file}")
    print()
    print("EXTRACTION COMPLETE!")


def generate_category_readme(category: str, rules: list[dict]) -> str:
    """Generate README for a category."""
    cat_info = CATEGORIES.get(category, {"name": category, "description": "Unknown"})

    md = f"""# {category} Validation Rules

## Overview
**Category:** {cat_info['name']}
**Description:** {cat_info['description']}

## Rules in This Category
"""

    for rule in sorted(rules, key=lambda x: x["id"]):
        md += f"- [{rule['id']}](./{rule['file']}): {rule['name']} (Priority: {rule['priority']})\n"

    # Statistics
    priority_counts = {}
    for rule in rules:
        pri = rule["priority"]
        priority_counts[pri] = priority_counts.get(pri, 0) + 1

    md += "\n## Category Statistics\n"
    md += f"- **Total rules:** {len(rules)}\n"
    md += "- **Priority breakdown:**\n"
    for pri, count in sorted(priority_counts.items()):
        md += f"  - {pri}: {count}\n"

    return md


def generate_master_index(rules_by_category: dict, all_rules: list) -> str:
    """Generate master index."""
    md = f"""# Validation Rules Extraction - Master Index

## Summary
- **Total Rules:** {len(all_rules)}
- **Categories:** {len(rules_by_category)}
- **Extraction Date:** 2025-10-02
- **Extraction Status:** COMPLETE

## Rules by Category

"""

    for category in sorted(rules_by_category.keys()):
        rules = rules_by_category[category]
        cat_info = CATEGORIES.get(
            category, {"name": category, "description": "Unknown"}
        )

        md += f"### {category} ({len(rules)} rules) - {cat_info['name']}\n"
        md += f"{cat_info['description']}\n\n"

        for rule in sorted(rules, key=lambda x: x["id"]):
            md += f"- [{rule['id']}](./{category}/{rule['file']}): {rule['name']}\n"

        md += "\n"

    # Priority breakdown
    md += "## Quick Reference Tables\n\n### By Priority\n"
    md += "| Priority | Count | Rules |\n"
    md += "|----------|-------|-------|\n"

    priority_groups = {}
    for rule in all_rules:
        pri = rule["priority"]
        if pri not in priority_groups:
            priority_groups[pri] = []
        priority_groups[pri].append(rule["id"])

    for pri in sorted(priority_groups.keys()):
        rule_list = ", ".join(priority_groups[pri])
        md += f"| {pri} | {len(priority_groups[pri])} | {rule_list} |\n"

    return md


if __name__ == "__main__":
    main()
