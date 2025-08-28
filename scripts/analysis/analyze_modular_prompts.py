#!/usr/bin/env python3
"""
Analyze and summarize the modular prompt test results.
"""

import json
import os


def analyze_results():
    """Analyze the test results and generated prompts."""

    # Read the report
    with open("modular_prompt_test_report.json", encoding="utf-8") as f:
        report = json.load(f)

    print("🔍 MODULAR PROMPT ANALYSIS REPORT")
    print("=" * 60)
    print(f"Test run: {report['test_run']}")
    print(f"Total tests: {report['total_tests']}")
    print()

    # Analyze each test
    for result in report["results"]:
        print(f"\n📊 {result['test_name']} - {result['begrip']}")
        print("-" * 40)

        # Basic metrics
        metadata = result.get("metadata", {})
        last_exec = metadata.get("last_execution", {})

        print("Prompt size:")
        print(f"  - Original: {last_exec.get('prompt_length', 'N/A'):,} chars")
        print(f"  - Truncated: {result['prompt_length']:,} chars")
        print(
            f"  - Truncation: {last_exec.get('prompt_length', 0) - result['prompt_length']:,} chars lost"
        )

        print("\nValidation rules:")
        module_meta = last_exec.get("module_metadata", {})
        quality_meta = module_meta.get("quality_rules", {})
        print(f"  - Expected: {quality_meta.get('total_rules', 'N/A')}")
        print(f"  - Found in output: {result['validation_rule_count']}")
        print(f"  - ARAI included: {quality_meta.get('include_arai', 'N/A')}")

        print("\nModule execution:")
        print(f"  - Total modules: {metadata.get('total_available_components', 'N/A')}")
        print(f"  - Active components: {metadata.get('active_components', 'N/A')}")
        print(f"  - Execution time: {last_exec.get('execution_time_ms', 'N/A')} ms")

        # Module failures
        failures = []
        for mod_id, mod_meta in module_meta.items():
            if "error" in mod_meta:
                failures.append((mod_id, mod_meta["error"]))
            elif "skipped_reason" in mod_meta:
                failures.append((mod_id, mod_meta["skipped_reason"]))

        if failures:
            print("\n⚠️  Module issues:")
            for mod_id, reason in failures:
                print(f"  - {mod_id}: {reason}")

        # Sections analysis
        print("\nSections:")
        print(f"  - Found: {len(result['sections_found'])}")
        print(f"  - Missing: {len(result['missing_sections'])}")

    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)

    # Overall statistics
    total_rules = sum(r["validation_rule_count"] for r in report["results"])
    avg_rules = total_rules / len(report["results"])

    total_original = sum(
        r["metadata"].get("last_execution", {}).get("prompt_length", 0)
        for r in report["results"]
    )
    total_truncated = sum(r["prompt_length"] for r in report["results"])

    print(f"Average validation rules: {avg_rules:.1f}")
    print(f"Total original prompt size: {total_original:,} chars")
    print(f"Total truncated size: {total_truncated:,} chars")
    print(
        f"Total loss: {total_original - total_truncated:,} chars ({((total_original - total_truncated) / total_original * 100):.1f}%)"
    )

    # Common issues
    print("\n🔧 Common issues:")
    print("  - Metrics module: EnrichedContext missing 'org_contexts' attribute")
    print("  - Template module: Cannot find semantic category")
    print("  - Prompt truncation: All prompts exceed 20K char limit")

    # Rule count analysis
    print("\n📏 Validation rule analysis:")
    for result in report["results"]:
        meta = result["metadata"].get("last_execution", {}).get("module_metadata", {})
        qr = meta.get("quality_rules", {})
        expected = qr.get("total_rules", "N/A")
        found = result["validation_rule_count"]

        status = "✅" if found >= expected else "❌"
        print(f"  {status} {result['test_name']}: {found}/{expected} rules")

    # Check prompt files
    print("\n📄 Generated prompt files:")
    prompt_files = [
        f for f in os.listdir(".") if f.startswith("prompt_") and f.endswith(".txt")
    ]
    for pf in sorted(prompt_files):
        size = os.path.getsize(pf)
        print(f"  - {pf}: {size:,} bytes")


def examine_prompt_structure(filename):
    """Examine the structure of a specific prompt file."""
    with open(filename, encoding="utf-8") as f:
        content = f.read()

    print(f"\n📄 Examining: {filename}")
    print("=" * 60)

    # Find major sections
    sections = []
    for line in content.split("\n"):
        if line.strip() and (line.startswith("#") or line.startswith("🔹")):
            sections.append(line.strip())

    print("Major sections found:")
    for section in sections[:20]:  # First 20 sections
        print(f"  {section}")

    if len(sections) > 20:
        print(f"  ... and {len(sections) - 20} more")

    # Count validation rules by type
    rule_counts = {"CON": 0, "ESS": 0, "INT": 0, "SAM": 0, "STR": 0, "ARAI": 0}

    for line in content.split("\n"):
        for rule_type in rule_counts:
            if f"**{rule_type}-" in line:
                rule_counts[rule_type] += 1

    print("\nValidation rules by category:")
    total = 0
    for rule_type, count in rule_counts.items():
        if count > 0:
            print(f"  - {rule_type}: {count} rules")
            total += count
    print(f"  Total: {total} rules")


if __name__ == "__main__":
    analyze_results()
    print("\n" + "=" * 80)
    examine_prompt_structure("prompt_simple_case.txt")
