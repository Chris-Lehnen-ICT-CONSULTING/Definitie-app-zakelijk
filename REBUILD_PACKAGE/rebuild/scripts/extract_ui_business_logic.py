#!/usr/bin/env python3
"""
Extract business logic from UI god objects to rebuild/business-logic/

Identifies and extracts business logic embedded in Streamlit UI components.
"""

import ast
import re
from pathlib import Path
from typing import Any

# UI God Objects to analyze
GOD_OBJECTS = [
    "src/ui/components/definition_generator_tab.py",
    "src/ui/components/expert_review_tab.py",
]

OUTPUT_DIR = Path("rebuild/business-logic/extracted-from-ui")


def is_business_logic_method(method_name: str, method_body: str) -> bool:
    """Determine if a method contains business logic vs UI rendering."""

    # UI rendering patterns (NOT business logic)
    ui_patterns = [
        r"st\.",  # Streamlit calls
        r"render",
        r"display",
        r"show",
        r"_render",
        r"_display",
    ]

    # Business logic patterns
    business_patterns = [
        r"workflow",
        r"orchestrat",
        r"validat",
        r"calculat",
        r"generat.*reasoning",
        r"transform",
        r"process",
        r"check.*duplicate",
        r"categorize",
        r"classify",
    ]

    # Check method name
    for pattern in business_patterns:
        if re.search(pattern, method_name, re.IGNORECASE):
            # But exclude if it's primarily UI rendering
            ui_ratio = sum(1 for p in ui_patterns if re.search(p, method_body))
            if ui_ratio < 5:  # Threshold: max 5 streamlit calls
                return True

    return False


def extract_business_logic_from_file(filepath: Path) -> dict[str, Any]:
    """Extract business logic methods from a Python file."""

    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    tree = ast.parse(content)

    extracted = {
        "source_file": str(filepath),
        "total_lines": len(content.splitlines()),
        "business_logic_methods": [],
        "hardcoded_business_rules": [],
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            method_name = node.name
            method_start = node.lineno
            method_end = node.end_lineno
            method_body = content.splitlines()[method_start - 1 : method_end]
            method_text = "\n".join(method_body)

            if is_business_logic_method(method_name, method_text):
                extracted["business_logic_methods"].append(
                    {
                        "name": method_name,
                        "start_line": method_start,
                        "end_line": method_end,
                        "lines": method_end - method_start + 1,
                        "docstring": ast.get_docstring(node),
                    }
                )

        # Extract hardcoded dictionaries (business rules)
        if isinstance(node, ast.Dict):
            # Look for pattern: category reasoning, workflow states, etc.
            dict_line = node.lineno
            extracted["hardcoded_business_rules"].append(
                {
                    "type": "dict",
                    "line": dict_line,
                }
            )

    return extracted


def generate_extraction_report():
    """Generate report of business logic to extract."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("🔍 Analyzing UI god objects for business logic...")
    print()

    all_results = []

    for god_object in GOD_OBJECTS:
        filepath = Path(god_object)
        if not filepath.exists():
            print(f"⚠️  {god_object} not found")
            continue

        print(f"📄 {filepath.name}")
        result = extract_business_logic_from_file(filepath)
        all_results.append(result)

        print(f"   Total lines: {result['total_lines']}")
        print(f"   Business logic methods: {len(result['business_logic_methods'])}")

        for method in result["business_logic_methods"]:
            print(f"      - {method['name']} ({method['lines']} LOC)")

        print()

    # Generate markdown report
    report_path = OUTPUT_DIR / "EXTRACTION_REPORT.md"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Business Logic Extraction Report\n\n")
        f.write("## UI God Objects Analysis\n\n")

        for result in all_results:
            f.write(f"### {Path(result['source_file']).name}\n\n")
            f.write(f"**Total lines:** {result['total_lines']}\n\n")
            f.write(
                f"**Business logic methods identified:** {len(result['business_logic_methods'])}\n\n"
            )

            if result["business_logic_methods"]:
                f.write("| Method | Lines | Start | End | Purpose |\n")
                f.write("|--------|-------|-------|-----|---------||\n")

                for method in result["business_logic_methods"]:
                    docstring = (method["docstring"] or "")[:50].replace("\n", " ")
                    f.write(
                        f"| `{method['name']}` | {method['lines']} | {method['start_line']} | {method['end_line']} | {docstring} |\n"
                    )

                f.write("\n")

            f.write(
                f"**Hardcoded business rules:** {len(result['hardcoded_business_rules'])}\n\n"
            )
            f.write("---\n\n")

    print(f"📊 Report generated: {report_path}")

    # Summary
    total_methods = sum(len(r["business_logic_methods"]) for r in all_results)
    total_rules = sum(len(r["hardcoded_business_rules"]) for r in all_results)

    print()
    print("=" * 60)
    print(f"SUMMARY: {total_methods} business logic methods found")
    print(f"         {total_rules} hardcoded business rules found")
    print("=" * 60)


if __name__ == "__main__":
    generate_extraction_report()
