#!/usr/bin/env python3
"""
Test script voor het genereren en analyseren van prompts uit het modulaire systeem.

Dit script:
1. Genereert prompts met verschillende configuraties
2. Telt validatieregels
3. Controleert of alle secties aanwezig zijn
4. Meet prompt lengtes voor en na truncatie
5. Slaat prompts op voor analyse
"""

import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Output directory configuration: write artifacts under reports/modular_prompts by default
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_DEFAULT_OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "reports", "modular_prompts")
OUTPUT_DIR = os.environ.get("MODULAR_PROMPT_OUTPUT_DIR", _DEFAULT_OUTPUT_DIR)
os.makedirs(OUTPUT_DIR, exist_ok=True)

from src.services.definition_generator_config import UnifiedGeneratorConfig
from src.services.definition_generator_context import EnrichedContext
from src.services.prompts.modular_prompt_builder import (
    ModularPromptBuilder,
    PromptComponentConfig,
)


@dataclass
class ValidationTestCase:
    """Test case configuratie."""

    name: str
    begrip: str
    context: dict[str, list[str]]
    ontologische_categorie: str
    config_overrides: dict[str, Any] = None


@dataclass
class ValidationTestResult:
    """Test resultaat."""

    test_name: str
    begrip: str
    prompt_length: int
    prompt_length_after_truncation: int
    validation_rule_count: int
    sections_found: list[str]
    missing_sections: list[str]
    execution_time_ms: float
    metadata: dict[str, Any]


def count_validation_rules(prompt: str) -> int:
    """Tel het aantal validatieregels in de prompt."""
    # Zoek naar regel patterns
    rule_patterns = ["CON-", "ESS-", "INT-", "SAM-", "STR-", "ARAI-"]

    rule_count = 0
    for line in prompt.split("\n"):
        for pattern in rule_patterns:
            if pattern in line and "**" in line:  # Bold regel headers
                rule_count += 1
                break

    return rule_count


def find_sections(prompt: str) -> list[str]:
    """Vind alle secties in de prompt."""
    sections = []
    section_markers = [
        "# Je rol en expertise",
        "## Output specificaties",
        "### ✅ Richtlijnen voor de definitie:",
        "## Context en achtergrond",
        "## Semantische categorisatie",
        "### Templates en voorbeelden",
        "## Grammaticale regels",
        "## Structuurregels voor definities",
        "## Integriteitsregels",
        "## Fouten om te voorkomen",
        "## Kwaliteitsmetriek",
        "## Je taak",
        "### ❌ Wat je NIET mag doen:",
        "### Verboden patronen",
        # Also check for variations that appear in the actual prompts
        "Je bent een expert",
        "### 📏 OUTPUT FORMAT VEREISTEN:",
        "### 📝 Grammatica en Taalgebruik:",
        "📌 Context:",
        "### 📐 Let op betekenislaag",
        "BELANGRIJKE VEREISTEN:",
    ]

    for marker in section_markers:
        if marker in prompt:
            sections.append(marker)

    return sections


def expected_sections() -> list[str]:
    """Lijst van verwachte secties."""
    return [
        "# Je rol en expertise",
        "## Output specificaties",
        "### ✅ Richtlijnen voor de definitie:",
        "## Context en achtergrond",
        "## Semantische categorisatie",
        "## Grammaticale regels",
        "## Fouten om te voorkomen",
        "## Je taak",
    ]


def run_test_case(test_case: ValidationTestCase) -> ValidationTestResult:
    """Voer een test case uit."""
    import time

    print(f"\n{'='*60}")
    print(f"Running test: {test_case.name}")
    print(f"Begrip: {test_case.begrip}")
    print(f"Context: {test_case.context}")
    print(f"Categorie: {test_case.ontologische_categorie}")

    # Maak configuratie met ontologische categorie
    config = UnifiedGeneratorConfig()
    # Store ontological category in quality config if needed
    config.quality.semantic_category = test_case.ontologische_categorie

    # Maak enriched context
    enriched_context = EnrichedContext(
        base_context=test_case.context,
        sources=[],
        expanded_terms={},
        confidence_scores={},
        metadata={"ontologische_categorie": test_case.ontologische_categorie},
    )

    # Maak prompt builder
    component_config = PromptComponentConfig()
    if test_case.config_overrides:
        for key, value in test_case.config_overrides.items():
            setattr(component_config, key, value)

    builder = ModularPromptBuilder(component_config)

    # Meet execution tijd
    start_time = time.time()

    # Genereer prompt
    prompt = builder.build_prompt(
        begrip=test_case.begrip, context=enriched_context, config=config
    )

    execution_time = (time.time() - start_time) * 1000  # ms

    # Analyseer prompt
    original_length = len(prompt)

    # Simuleer truncatie
    truncated_length = min(original_length, component_config.max_prompt_length)

    # Tel regels
    rule_count = count_validation_rules(prompt)

    # Vind secties
    sections = find_sections(prompt)
    expected = expected_sections()
    missing = [s for s in expected if s not in sections]

    # Haal metadata op
    metadata = builder.get_component_metadata(test_case.begrip, enriched_context)

    result = ValidationTestResult(
        test_name=test_case.name,
        begrip=test_case.begrip,
        prompt_length=original_length,
        prompt_length_after_truncation=truncated_length,
        validation_rule_count=rule_count,
        sections_found=sections,
        missing_sections=missing,
        execution_time_ms=execution_time,
        metadata=metadata,
    )

    # Print samenvatting
    print("\nResultaten:")
    print(f"- Prompt lengte: {original_length} karakters")
    print(f"- Na truncatie: {truncated_length} karakters")
    print(f"- Validatieregels gevonden: {rule_count}")
    print(f"- Secties gevonden: {len(sections)}")
    print(f"- Ontbrekende secties: {len(missing)}")
    print(f"- Execution tijd: {execution_time:.2f}ms")

    if missing:
        print(f"  Ontbreken: {', '.join(missing)}")

    # Sla prompt op
    filename = f"prompt_{test_case.name.replace(' ', '_').lower()}.txt"
    file_path = os.path.join(OUTPUT_DIR, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"# Test Case: {test_case.name}\n")
        f.write(f"# Begrip: {test_case.begrip}\n")
        f.write(f"# Context: {json.dumps(test_case.context)}\n")
        f.write(f"# Categorie: {test_case.ontologische_categorie}\n")
        f.write(f"# Gegenereerd op: {datetime.now().isoformat()}\n")
        f.write(f"# Lengte: {original_length} karakters\n")
        f.write(f"# Validatieregels: {rule_count}\n")
        f.write("# " + "=" * 50 + "\n\n")
        f.write(prompt)

    print(f"✓ Prompt opgeslagen als: {file_path}")

    return result


def main():
    """Hoofdfunctie."""
    print("🔬 Modular Prompt System Test")
    print("=" * 60)

    # Definieer test cases
    test_cases = [
        ValidationTestCase(
            name="Simple Case",
            begrip="toezicht",
            context={"organisatorisch": ["DJI"]},
            ontologische_categorie="proces",
        ),
        ValidationTestCase(
            name="Compact Mode",
            begrip="toezicht",
            context={"organisatorisch": ["DJI"]},
            ontologische_categorie="proces",
            config_overrides={"compact_mode": True},
        ),
        ValidationTestCase(
            name="No ARAI Rules",
            begrip="toezicht",
            context={"organisatorisch": ["DJI"]},
            ontologische_categorie="proces",
            config_overrides={"include_arai_rules": False},
        ),
        ValidationTestCase(
            name="Complex Context",
            begrip="registratie",
            context={
                "organisatorisch": ["DJI", "OM"],
                "juridisch": ["Wetboek van Strafrecht"],
            },
            ontologische_categorie="resultaat",
        ),
    ]

    # Voer tests uit
    results = []
    for test_case in test_cases:
        try:
            result = run_test_case(test_case)
            results.append(result)
        except Exception as e:
            print(f"❌ Test '{test_case.name}' failed: {e}")
            import traceback

            traceback.print_exc()

    # Genereer samenvattend rapport
    print("\n" + "=" * 60)
    print("📊 SAMENVATTEND RAPPORT")
    print("=" * 60)

    report = {
        "test_run": datetime.now().isoformat(),
        "total_tests": len(results),
        "results": [],
    }

    for result in results:
        print(f"\n{result.test_name}:")
        print(f"  - Prompt lengte: {result.prompt_length:,} karakters")
        print(f"  - Validatieregels: {result.validation_rule_count}")
        print(f"  - Secties: {len(result.sections_found)}/{len(expected_sections())}")
        print(f"  - Execution tijd: {result.execution_time_ms:.2f}ms")

        report["results"].append(asdict(result))

    # Sla rapport op
    report_path = os.path.join(OUTPUT_DIR, "modular_prompt_test_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Test rapport opgeslagen als: {report_path}")

    # Analyseer validatieregels
    print("\n📏 Validatieregel Analyse:")
    for result in results:
        expected_rules = 34 if "No ARAI" not in result.test_name else 25
        print(
            f"  - {result.test_name}: {result.validation_rule_count}/{expected_rules} regels"
        )

    # Check module metadata
    print("\n🔧 Module Metadata:")
    for result in results:
        if "modules" in result.metadata:
            print(
                f"  - {result.test_name}: {len(result.metadata['modules'])} modules geregistreerd"
            )


if __name__ == "__main__":
    main()
