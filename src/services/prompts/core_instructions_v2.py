"""
Verbeterde CoreInstructionsModule implementatie.

Deze module biedt een uitgebreidere en meer gestructureerde versie van
de basis instructies voor definitie generatie.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class CoreInstructionsV2:
    """Verbeterde implementatie van core instructions voor definitie generatie."""

    # Template configuratie constanten
    MAX_DEFINITION_CHARS = 2500
    DEFAULT_MAX_CHARS = 4000
    MIN_CHARS_WARNING_THRESHOLD = 500

    def build_core_instructions(
        self, begrip: str, metadata: dict[str, Any] | None = None
    ) -> str:
        """
        Bouw uitgebreide core instructions met alle essentiële elementen.

        Args:
            begrip: Het te definiëren begrip
            metadata: Optionele metadata zoals max_chars

        Returns:
            Gestructureerde core instructions (800-1000 chars)
        """
        # Extract metadata
        max_chars = self.DEFAULT_MAX_CHARS
        if metadata and "max_chars" in metadata:
            max_chars = metadata["max_chars"]

        # Bereken beschikbare ruimte voor definitie
        # Schat in dat de volledige prompt ~1500 chars extra nodig heeft
        available_for_definition = min(
            self.MAX_DEFINITION_CHARS,
            max_chars - 1500 if max_chars > 2000 else self.MAX_DEFINITION_CHARS,
        )

        # Build instructions
        instructions = self._build_role_section()
        instructions += "\n\n" + self._build_task_section()
        instructions += "\n\n" + self._build_requirements_section()
        instructions += "\n\n" + self._build_quality_section()
        instructions += "\n\n" + self._build_warnings_section(available_for_definition)

        # Log metrics
        logger.debug(
            f"CoreInstructionsV2 generated {len(instructions)} chars "
            f"(available for def: {available_for_definition})"
        )

        return instructions

    def _build_role_section(self) -> str:
        """Bouw expert rol definitie sectie."""
        return (
            "Je bent een ervaren Nederlandse expert in het opstellen van "
            "beleidsmatige en juridische definities voor de Nederlandse overheid."
        )

    def _build_task_section(self) -> str:
        """Bouw opdracht omschrijving sectie."""
        return (
            "**Je opdracht**: Formuleer een heldere, eenduidige definitie "
            "voor het opgegeven begrip."
        )

    def _build_requirements_section(self) -> str:
        """Bouw definitie vereisten sectie."""
        return """### Definitie vereisten:
• **Formaat**: Één volledige zin die het begrip volledig verklaart
• **Stijl**: Zakelijk, formeel en geschikt voor officiële overheidsdocumenten
• **Structuur**: Begin met "[begrip] is..." of "[begrip] betreft..."
• **Taal**: Helder Nederlands zonder jargon (tenzij onvermijdelijk)"""

    def _build_quality_section(self) -> str:
        """Bouw kwaliteitscriteria sectie."""
        return """### Kwaliteitscriteria:
✓ **Ondubbelzinnig** - geen ruimte voor meerdere interpretaties
✓ **Volledig** - bevat alle essentiële kenmerken
✓ **Afgebakend** - maakt duidelijk wat WEL en NIET onder de definitie valt
✓ **Contextgevoelig** - past bij de Nederlandse overheidscontext"""

    def _build_warnings_section(self, available_chars: int) -> str:
        """
        Bouw waarschuwingen sectie met dynamische karakter info.

        Args:
            available_chars: Aantal beschikbare karakters voor definitie
        """
        base_warnings = """⚠️ **LET OP**:
- Geen toelichtingen, voorbeelden of extra uitleg toevoegen
- Alleen de definitie zelf in één zin
- Vermijd cirkelredeneringen (gebruik het begrip niet in de eigen definitie)"""

        # Voeg karakter limiet waarschuwing toe indien relevant
        if available_chars < self.MAX_DEFINITION_CHARS:
            char_warning = f"\n- Maximaal {available_chars} karakters beschikbaar"
            base_warnings += char_warning

            # Extra waarschuwing bij weinig ruimte
            if available_chars < self.MIN_CHARS_WARNING_THRESHOLD:
                base_warnings += f"\n- ⚠️ WAARSCHUWING: Slechts {available_chars} karakters - wees zeer beknopt!"

        # Afsluitende instructie
        base_warnings += "\n\nBELANGRIJK: Focus op precisie en helderheid. De definitie moet juridisch houdbaar zijn."

        return base_warnings

    def get_minimal_version(self) -> str:
        """
        Krijg minimale versie (backwards compatible met origineel).

        Returns:
            Originele 3-regel versie voor compatibility
        """
        return """Je bent een expert in beleidsmatige definities voor overheidsgebruik.
Formuleer een definitie in één enkele zin, zonder toelichting.
Gebruik een zakelijke en generieke stijl voor het definiëren van dit begrip."""

    def compare_versions(self, begrip: str = "test") -> dict[str, Any]:
        """
        Vergelijk oude en nieuwe versie voor analyse.

        Returns:
            Dictionary met vergelijkingsdata
        """
        old_version = self.get_minimal_version()
        new_version = self.build_core_instructions(begrip)

        return {
            "old": {
                "content": old_version,
                "length": len(old_version),
                "lines": len(old_version.split("\n")),
                "sections": 0,
                "has_structure": False,
                "has_warnings": False,
                "has_quality_criteria": False,
            },
            "new": {
                "content": new_version,
                "length": len(new_version),
                "lines": len(new_version.split("\n")),
                "sections": 4,
                "has_structure": True,
                "has_warnings": True,
                "has_quality_criteria": True,
            },
            "improvement": {
                "length_increase": len(new_version) - len(old_version),
                "length_ratio": len(new_version) / len(old_version),
                "added_sections": 4,
                "added_features": [
                    "Nederlandse expert context",
                    "Gestructureerde opdracht",
                    "Definitie vereisten",
                    "Kwaliteitscriteria",
                    "Waarschuwingen",
                    "Karakter limieten",
                ],
            },
        }


# Voorbeeld gebruik en test
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.DEBUG)

    # Test nieuwe implementatie
    module = CoreInstructionsV2()

    print("=== Verbeterde CoreInstructionsModule V2 ===\n")

    # Test met verschillende metadata
    test_cases = [
        {"begrip": "blockchain", "metadata": {"max_chars": 4000}},
        {"begrip": "opsporing", "metadata": {"max_chars": 2000}},
        {"begrip": "AI", "metadata": {"max_chars": 1000}},
    ]

    for case in test_cases:
        output = module.build_core_instructions(case["begrip"], case["metadata"])
        print(f"Begrip: {case['begrip']} (max_chars: {case['metadata']['max_chars']})")
        print(f"Output length: {len(output)} chars")
        print("-" * 50)
        print(output)
        print("=" * 50)
        print()

    # Vergelijking
    print("\n=== Versie Vergelijking ===")
    comparison = module.compare_versions()
    print(f"Oude versie: {comparison['old']['length']} chars")
    print(f"Nieuwe versie: {comparison['new']['length']} chars")
    print(
        f"Toename: {comparison['improvement']['length_increase']} chars "
        f"({comparison['improvement']['length_ratio']:.1f}x)"
    )
    print("\nToegevoegde features:")
    for feature in comparison["improvement"]["added_features"]:
        print(f"  - {feature}")
