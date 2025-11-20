"""
Output Specification Module - Format specificaties en limieten.

Deze module is verantwoordelijk voor:
1. Output format vereisten
2. Karakter limiet waarschuwingen
3. Format specificaties
"""

import logging
from typing import Any

from .base_module import BasePromptModule, ModuleContext, ModuleOutput

logger = logging.getLogger(__name__)


class OutputSpecificationModule(BasePromptModule):
    """
    Module voor output format specificaties en limieten.

    Genereert instructies voor het gewenste output formaat
    en waarschuwt voor karakter limieten waar nodig.
    """

    def __init__(self):
        """Initialize de output specification module."""
        super().__init__(
            module_id="output_specification",
            module_name="Output Format Specifications",
            priority=90,  # Hoge prioriteit - output specificaties
        )
        self.default_min_chars = 150
        self.default_max_chars = 350

    def initialize(self, config: dict[str, Any]) -> None:
        """
        Initialize module met configuratie.

        Args:
            config: Module configuratie
        """
        self._config = config
        self.default_min_chars = config.get("default_min_chars", 150)
        self.default_max_chars = config.get("default_max_chars", 350)
        self._initialized = True
        logger.debug(
            f"OutputSpecificationModule geïnitialiseerd "
            f"(min={self.default_min_chars}, max={self.default_max_chars})"
        )

    def validate_input(self, context: ModuleContext) -> tuple[bool, str | None]:
        """
        Deze module draait altijd.

        Args:
            context: Module context

        Returns:
            Altijd (True, None)
        """
        return True, None

    def execute(self, context: ModuleContext) -> ModuleOutput:
        """
        Genereer output format specificaties.

        Args:
            context: Module context

        Returns:
            ModuleOutput met format specs
        """
        try:
            # Haal metadata op voor karakter limieten
            metadata = context.enriched_context.metadata
            min_chars = metadata.get("min_karakters", self.default_min_chars)
            max_chars = metadata.get("max_karakters", self.default_max_chars)

            # Check of er een karakter limiet waarschuwing nodig is
            needs_warning = (
                min_chars != self.default_min_chars
                or max_chars != self.default_max_chars
            )

            # Sla karakter limiet info op voor andere modules
            if needs_warning:
                context.set_shared(
                    "character_limit_warning", {"min": min_chars, "max": max_chars}
                )

            # Bouw output specificaties
            sections = []

            # Basis format vereisten (altijd)
            sections.append(self._build_basic_format_requirements())

            # Karakter limiet waarschuwing (indien nodig)
            if needs_warning:
                sections.append(
                    self._build_character_limit_warning(min_chars, max_chars)
                )

            # Extra format richtlijnen
            sections.append(self._build_format_guidelines())

            # Combineer secties
            content = "\n".join(sections)

            return ModuleOutput(
                content=content,
                metadata={
                    "has_limit_warning": needs_warning,
                    "min_chars": min_chars,
                    "max_chars": max_chars,
                },
            )

        except Exception as e:
            logger.error(
                f"OutputSpecificationModule execution failed: {e}", exc_info=True
            )
            return ModuleOutput(
                content="",
                metadata={"error": str(e)},
                success=False,
                error_message=f"Failed to generate output specifications: {e!s}",
            )

    def get_dependencies(self) -> list[str]:
        """
        Deze module heeft geen dependencies.

        Returns:
            Lege lijst
        """
        return []

    def _build_basic_format_requirements(self) -> str:
        """Bouw basis format vereisten."""
        return """### 📏 OUTPUT FORMAT VEREISTEN:
- Definitie in één enkele zin
- Geen punt aan het einde
- Geen haakjes BEHALVE voor afkortingen (bijv. DJI, AVG)
- Geen voorbeelden in de definitie
- Focus op WAT het is, niet het doel of gebruik"""

    def _build_character_limit_warning(self, min_chars: int, max_chars: int) -> str:
        """
        Bouw karakter limiet waarschuwing.

        Args:
            min_chars: Minimum aantal karakters
            max_chars: Maximum aantal karakters

        Returns:
            Waarschuwing tekst
        """
        return f"""
⚠️ **KARAKTER LIMIET WAARSCHUWING:**
Deze definitie heeft specifieke lengte-eisen:
- Minimum: {min_chars} karakters
- Maximum: {max_chars} karakters
- Streef naar een balans tussen volledigheid en beknoptheid
- Tel alleen de definitie zelf, niet de ontologische marker"""

    def _build_format_guidelines(self) -> str:
        """Bouw extra format richtlijnen."""
        return """### 📝 DEFINITIE KWALITEIT:
- Gebruik formele, zakelijke taal
- Vermijd jargon tenzij noodzakelijk voor het vakgebied
- Gebruik concrete, specifieke termen
- Vermijd vage kwalificaties (veel, weinig, meestal)
- Maak onderscheid tussen het begrip en verwante begrippen"""
