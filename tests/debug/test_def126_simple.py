#!/usr/bin/env python3
"""
DEF-126: Simple demonstration of ontological category redundancy.

This test shows how the same category instructions are injected multiple times.
"""

import re
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def analyze_module_file(filepath: str, module_name: str):
    """Analyze a module file for category instructions."""
    print(f"\n📁 {module_name}:")
    print(f"   File: {filepath}")

    with open(filepath) as f:
        content = f.read()

    # Look for patterns
    patterns = {
        "PROCES begrippen": r"PROCES begrippen.*?start met.*?activiteit waarbij",
        "TYPE begrippen": r"TYPE begrippen.*?start met.*?kernwoord",
        "RESULTAAT begrippen": r"RESULTAAT begrippen.*?resultaat van",
        "EXEMPLAAR begrippen": r"EXEMPLAAR begrippen.*?exemplaar van",
        "Bepaal de categorie": r"Bepaal de juiste categorie|moet één van de vier categorieën",
        "Ontologische categorie": r"ontologische[_\s]categorie|ontological[_\s]category",
        "ESS-02": r"ESS-02.*?[Oo]ntologische",
        "Category guidance": r"PROCES CATEGORIE|TYPE CATEGORIE|RESULTAAT CATEGORIE",
    }

    found_patterns = []
    for name, pattern in patterns.items():
        matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
        if matches:
            found_patterns.append((name, len(matches)))
            # Show first match location
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                lines_before = content[: match.start()].count("\n")
                print(
                    f"   ✓ {name}: {len(matches)} occurrence(s) starting at line {lines_before + 1}"
                )

    # Count total lines with category instructions
    lines = content.split("\n")
    category_lines = 0
    for line in lines:
        if any(
            keyword in line
            for keyword in [
                "PROCES",
                "TYPE",
                "RESULTAAT",
                "EXEMPLAAR",
                "activiteit waarbij",
                "handeling die",
                "proces waarin",
                "kernwoord",
                "resultaat van",
                "uitkomst van",
                "ontologische",
                "categorie",
            ]
        ):
            category_lines += 1

    print(f"   📊 Total lines with category keywords: {category_lines}/{len(lines)}")

    return found_patterns, category_lines, len(lines)


def main():
    print("=" * 80)
    print("DEF-126: ONTOLOGICAL CATEGORY REDUNDANCY ANALYSIS")
    print("=" * 80)

    # Modules to analyze
    modules = [
        (
            "src/services/prompts/modules/semantic_categorisation_module.py",
            "SemanticCategorisationModule",
        ),
        ("src/services/prompts/modules/expertise_module.py", "ExpertiseModule"),
        (
            "src/services/prompts/modules/definition_task_module.py",
            "DefinitionTaskModule",
        ),
        ("src/services/prompts/modules/template_module.py", "TemplateModule"),
        ("src/services/prompts/modules/ess_rules_module.py", "EssRulesModule"),
        (
            "src/services/prompts/modules/context_awareness_module.py",
            "ContextAwarenessModule",
        ),
    ]

    total_category_lines = 0
    total_lines = 0
    all_patterns = {}

    for filepath, name in modules:
        full_path = Path(__file__).parent.parent.parent / filepath
        if full_path.exists():
            patterns, cat_lines, lines = analyze_module_file(str(full_path), name)
            total_category_lines += cat_lines
            total_lines += lines

            # Aggregate patterns
            for pattern_name, count in patterns:
                if pattern_name not in all_patterns:
                    all_patterns[pattern_name] = 0
                all_patterns[pattern_name] += count
        else:
            print(f"\n⚠️  {name}: File not found")

    # Summary
    print("\n" + "=" * 80)
    print("📊 AGGREGATED REDUNDANCY METRICS:")
    print("=" * 80)

    print("\n🔢 Pattern Occurrences Across All Modules:")
    for pattern, count in sorted(
        all_patterns.items(), key=lambda x: x[1], reverse=True
    ):
        print(f"   {pattern}: {count} total occurrences")

    print("\n📈 Line Analysis:")
    print(f"   Total lines analyzed: {total_lines}")
    print(f"   Lines with category keywords: {total_category_lines}")
    print(f"   Redundancy percentage: {total_category_lines/total_lines*100:.1f}%")

    print("\n" + "=" * 80)
    print("💡 KEY FINDINGS:")
    print("=" * 80)

    print(
        """
1. PROBLEM: Multiple modules inject overlapping category instructions:
   - SemanticCategorisationModule: Full ESS-02 instructions for ALL categories
   - ExpertiseModule: Word type advice (werkwoord/deverbaal mapping)
   - DefinitionTaskModule: Category hints in checklist
   - TemplateModule: Category-based template selection
   - EssRulesModule: May include ESS-02 rules

2. ISSUE: The category is ALREADY DETERMINED by the UI/classifier, but:
   - We still inject "determine the category" instructions
   - We include guidance for ALL 4 categories instead of just the selected one
   - Multiple modules repeat similar instructions

3. IMPACT:
   - Estimated 2500 tokens of redundant instructions
   - Confusing prompts with contradictory guidance
   - Wasted API tokens and slower generation

4. SOLUTION (from DEF-126 documents):
   - Single Source of Truth: SemanticCategorisationModule ONLY injects relevant category
   - Remove all "determine category" instructions
   - Other modules use shared state, no own category logic
   - Expected reduction: 92% fewer tokens for category instructions
"""
    )

    # Check for already-created analysis documents
    analysis_docs = [
        "docs/analyses/DEF-126-CATEGORIE-SPECIFIEKE-INJECTIE.md",
        "docs/analyses/DEF-126-ONTOLOGISCHE-CATEGORIE-MAPPING.md",
        "docs/analyses/DEF-126-REDUNDANTIE-OPLOSSING.md",
    ]

    print("\n📚 EXISTING SOLUTION DOCUMENTS:")
    for doc in analysis_docs:
        doc_path = Path(__file__).parent.parent.parent / doc
        if doc_path.exists():
            print(f"   ✅ {doc}")
        else:
            print(f"   ❌ {doc} (not found)")

    print("\n✅ RECOMMENDATION: Implement the DEF-126 solution as documented!")


if __name__ == "__main__":
    main()
