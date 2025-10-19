#!/usr/bin/env python3
"""
Analyse tool voor CoreInstructionsModule van ModularPromptBuilder.

Dit script analyseert de output van de eerste module (_build_role_and_basic_rules)
voor verschillende test cases om de kwaliteit en consistentie te evalueren.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.services.definition_generator_config import UnifiedGeneratorConfig
from src.services.definition_generator_context import EnrichedContext
from src.services.prompts.modular_prompt_builder import (
    ModularPromptBuilder,
    PromptComponentConfig,
)

# Setup logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CoreModuleAnalyzer:
    """Analyseert de CoreInstructionsModule output."""

    def __init__(self):
        """Initialize analyzer met test configuratie."""
        # Configuratie voor alleen core module
        config = PromptComponentConfig(
            include_role=True,  # Alleen deze module
            include_context=False,
            include_ontological=False,
            include_validation_rules=False,
            include_forbidden_patterns=False,
            include_final_instructions=False,
        )
        self.builder = ModularPromptBuilder(config)
        self.results = []

    def analyze_single_case(
        self, begrip: str, context_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Analyseer output voor een enkele test case."""
        logger.info(f"Analyseren van begrip: {begrip}")

        # Create context
        EnrichedContext(
            base_context=context_data.get("base_context", {}),
            sources=[],
            expanded_terms=context_data.get("expanded_terms", {}),
            confidence_scores=context_data.get("confidence_scores", {}),
            metadata=context_data.get("metadata", {}),
        )

        # Create config
        config = UnifiedGeneratorConfig()
        # Override specific values if needed
        config.gpt.max_tokens = context_data.get("max_tokens", 4000)

        try:
            # Build alleen de core module
            # We moeten de private method direct aanroepen voor isolatie
            module_output = self.builder._build_role_and_basic_rules(begrip)

            # Analyseer output
            analysis = {
                "begrip": begrip,
                "output_length": len(module_output),
                "line_count": len(module_output.split("\n")),
                "sections": self._identify_sections(module_output),
                "warnings": self._check_for_warnings(module_output),
                "character_info": self._extract_character_info(module_output),
                "success": True,
                "output": module_output,
            }

        except Exception as e:
            logger.error(f"Error analyzing {begrip}: {e}")
            analysis = {"begrip": begrip, "success": False, "error": str(e)}

        return analysis

    def _identify_sections(self, output: str) -> list[str]:
        """Identificeer de verschillende secties in de module output."""
        sections = []

        # Zoek naar section markers
        markers = [
            "Je bent een ervaren Nederlandse",
            "**Je opdracht**:",
            "### Aanvullende context:",
            "⚠️ LET OP:",
            "BELANGRIJK:",
            "📌 Focus op:",
        ]

        for marker in markers:
            if marker in output:
                sections.append(marker.strip(":"))

        return sections

    def _check_for_warnings(self, output: str) -> list[str]:
        """Check voor waarschuwingen in de output."""
        warnings = []

        if "⚠️ WAARSCHUWING:" in output:
            # Extract warning text
            warning_start = output.find("⚠️ WAARSCHUWING:")
            warning_end = output.find("\n", warning_start)
            if warning_end > warning_start:
                warnings.append(output[warning_start:warning_end])

        return warnings

    def _extract_character_info(self, output: str) -> dict[str, Any]:
        """Extract karakter limit informatie."""
        info = {"has_limit": False, "limit_value": None, "remaining_indication": False}

        # Check for character limit mentions
        if "karakters" in output.lower():
            info["has_limit"] = True

            # Try to extract numeric limit
            import re

            numbers = re.findall(r"\d+", output)
            for num in numbers:
                if int(num) > 1000:  # Likely a character limit
                    info["limit_value"] = int(num)
                    break

        if "resterende" in output.lower() or "over voor" in output.lower():
            info["remaining_indication"] = True

        return info

    def analyze_test_set(self, test_cases: list[dict[str, Any]]) -> None:
        """Analyseer een set van test cases."""
        logger.info(f"Analyseren van {len(test_cases)} test cases...")

        for case in test_cases:
            result = self.analyze_single_case(case["begrip"], case.get("context", {}))
            self.results.append(result)

    def generate_report(self) -> dict[str, Any]:
        """Genereer een samenvattend rapport."""
        successful = [r for r in self.results if r.get("success", False)]

        return {
            "total_cases": len(self.results),
            "successful": len(successful),
            "failed": len(self.results) - len(successful),
            "average_output_length": (
                sum(r["output_length"] for r in successful) / len(successful)
                if successful
                else 0
            ),
            "common_sections": self._find_common_sections(successful),
            "character_limit_usage": self._analyze_character_limits(successful),
            "detailed_results": self.results,
        }


    def _find_common_sections(self, results: list[dict[str, Any]]) -> list[str]:
        """Vind secties die in alle outputs voorkomen."""
        if not results:
            return []

        # Start with sections from first result
        common = set(results[0].get("sections", []))

        # Intersect with other results
        for r in results[1:]:
            common &= set(r.get("sections", []))

        return list(common)

    def _analyze_character_limits(
        self, results: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Analyseer hoe character limits worden gebruikt."""
        total = len(results)
        with_limit = sum(
            1 for r in results if r.get("character_info", {}).get("has_limit")
        )
        with_remaining = sum(
            1
            for r in results
            if r.get("character_info", {}).get("remaining_indication")
        )

        limits = [
            r.get("character_info", {}).get("limit_value")
            for r in results
            if r.get("character_info", {}).get("limit_value")
        ]

        return {
            "percentage_with_limit": (with_limit / total * 100) if total > 0 else 0,
            "percentage_with_remaining": (
                (with_remaining / total * 100) if total > 0 else 0
            ),
            "common_limits": list(set(limits)),
            "varying_limits": len(set(limits)) > 1,
        }


def main():
    """Hoofdfunctie voor module analyse."""
    # Test cases
    test_cases = [
        {
            "begrip": "blockchain",
            "context": {
                "base_context": {
                    "categorie": "Technologie",
                    "subcategorie": "Informatiesystemen",
                },
                "metadata": {"max_chars": 2500},
            },
        },
        {
            "begrip": "opsporing",
            "context": {
                "base_context": {
                    "categorie": "Juridisch",
                    "subcategorie": "Strafrecht",
                },
                "metadata": {"max_chars": 4000},
            },
        },
        {
            "begrip": "natuurinclusief bouwen",
            "context": {
                "base_context": {
                    "categorie": "Duurzaamheid",
                    "subcategorie": "Bouwkunde",
                },
                "metadata": {"max_chars": 1500},
            },
        },
        {
            "begrip": "AI",  # Kort begrip
            "context": {
                "base_context": {
                    "categorie": "Technologie",
                    "subcategorie": "Kunstmatige Intelligentie",
                },
                "metadata": {},
            },
        },
        {
            "begrip": "zeer-lange-begrip-met-veel-woorden-en-koppeltekens-voor-edge-case-testing",
            "context": {"base_context": {}, "metadata": {"max_chars": 3000}},
        },
    ]

    # Run analyse
    analyzer = CoreModuleAnalyzer()
    analyzer.analyze_test_set(test_cases)

    # Generate report
    report = analyzer.generate_report()

    # Save report
    output_file = Path("core_module_analysis_report.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    logger.info(f"Analyse compleet. Rapport opgeslagen in: {output_file}")

    # Print summary
    print("\n=== Core Module Analyse Samenvatting ===")
    print(f"Totaal geanalyseerd: {report['total_cases']}")
    print(f"Succesvol: {report['successful']}")
    print(f"Mislukt: {report['failed']}")
    print(f"Gemiddelde output lengte: {report['average_output_length']:.0f} karakters")
    print(f"\nGemeenschappelijke secties: {', '.join(report['common_sections'])}")
    print("\nKarakter limit gebruik:")
    print(
        f"  - Met limiet: {report['character_limit_usage']['percentage_with_limit']:.0f}%"
    )
    print(
        f"  - Met 'resterende' indicatie: {report['character_limit_usage']['percentage_with_remaining']:.0f}%"
    )
    print(f"  - Gevonden limieten: {report['character_limit_usage']['common_limits']}")

    # Show sample output
    if report["successful"] > 0 and report["detailed_results"]:
        print("\n=== Sample Output (eerste case) ===")
        first_success = next(r for r in report["detailed_results"] if r.get("success"))
        print(first_success.get("output", "")[:500] + "...")


if __name__ == "__main__":
    main()
