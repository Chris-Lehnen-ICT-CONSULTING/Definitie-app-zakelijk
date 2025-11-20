"""
Grammar Module - Implementeert grammatica en taalregels voor definities.

Deze module is verantwoordelijk voor:
1. Grammaticale richtlijnen
2. Taalkundige conventies
3. Schrijfstijl regels
"""

import logging
from typing import Any

from .base_module import BasePromptModule, ModuleContext, ModuleOutput

logger = logging.getLogger(__name__)


class GrammarModule(BasePromptModule):
    """
    Module voor grammatica en taalkundige regels.

    Genereert grammaticale richtlijnen en schrijfstijl instructies
    voor het formuleren van definities.
    """

    def __init__(self):
        """Initialize de grammar module."""
        super().__init__(
            module_id="grammar",
            module_name="Grammar & Language Rules",
            priority=85,  # Hoge prioriteit - grammatica regels
        )
        self.include_examples = True
        self.strict_mode = False

    def initialize(self, config: dict[str, Any]) -> None:
        """
        Initialize module met configuratie.

        Args:
            config: Module configuratie met opties voor examples en strict mode
        """
        self._config = config
        self.include_examples = config.get("include_examples", True)
        self.strict_mode = config.get("strict_mode", False)
        self._initialized = True
        logger.debug(
            f"GrammarModule geïnitialiseerd "
            f"(examples={self.include_examples}, strict={self.strict_mode})"
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
        Genereer grammatica en taalregels.

        Args:
            context: Module context

        Returns:
            ModuleOutput met grammaticaregels
        """
        try:
            # Haal woordsoort op van ExpertiseModule indien beschikbaar
            word_type = context.get_shared("word_type", "overig")

            # Bouw grammatica sectie
            sections = []

            # Hoofdsectie
            sections.append("### 🔤 GRAMMATICA REGELS:")
            sections.append("")

            # Basis grammaticaregels
            sections.extend(self._build_basic_grammar_rules())

            # Woordsoort-specifieke regels
            word_type_rules = self._build_word_type_rules(word_type)
            if word_type_rules:
                sections.extend(word_type_rules)

            # Interpunctie regels (echte grammatica)
            sections.extend(self._build_punctuation_rules())

            # Strikte modus extra regels
            if self.strict_mode:
                sections.extend(self._build_strict_rules())

            # Combineer secties
            content = "\n".join(sections)

            return ModuleOutput(
                content=content,
                metadata={
                    "word_type": word_type,
                    "rules_count": len([s for s in sections if s.startswith("🔸")]),
                    "strict_mode": self.strict_mode,
                },
            )

        except Exception as e:
            logger.error(f"GrammarModule execution failed: {e}", exc_info=True)
            return ModuleOutput(
                content="",
                metadata={"error": str(e)},
                success=False,
                error_message=f"Failed to generate grammar rules: {e!s}",
            )

    def get_dependencies(self) -> list[str]:
        """
        Deze module kan afhankelijk zijn van ExpertiseModule voor woordsoort.

        Returns:
            Lijst met optionele dependencies
        """
        return []  # Soft dependency op expertise module via shared state

    def _build_basic_grammar_rules(self) -> list[str]:
        """Bouw basis grammaticaregels."""
        rules = []

        rules.append("🔸 **Enkelvoud als standaard**")
        rules.append(
            "- Gebruik enkelvoud tenzij het begrip een plurale-tantum is (alleen meervoud bestaat)"
        )
        rules.append("- Bij twijfel: gebruik enkelvoud")

        if self.include_examples:
            rules.append("  ✅ proces (niet: processen)")
            rules.append("  ✅ maatregel (niet: maatregelen)")
            rules.append(
                "  ✅ gegevens (plurale-tantum - alleen meervoudsvorm bestaat)"
            )
            rules.append("  ❌ gegeven (enkelvoud bestaat niet in Nederlandse taal)")
            rules.append("")

        rules.append("🔸 **Actieve vorm prefereren**")
        rules.append("- Gebruik waar mogelijk de actieve vorm")
        rules.append("- Passieve vorm alleen bij focus op het ondergaan van actie")

        if self.include_examples:
            rules.append("  ✅ instantie die toezicht houdt")
            rules.append("  ❌ instantie waardoor toezicht wordt gehouden")
            rules.append("")

        rules.append("🔸 **Tegenwoordige tijd**")
        rules.append("- Formuleer definities in de tegenwoordige tijd")
        rules.append("- Vermijd verleden of toekomende tijd")

        if self.include_examples:
            rules.append("  ✅ proces dat identificeert")
            rules.append("  ❌ proces dat zal identificeren")
            rules.append("  ❌ proces dat identificeerde")
            rules.append("")

        return rules

    def _build_word_type_rules(self, word_type: str) -> list[str]:
        """
        Bouw woordsoort-specifieke grammaticaregels.

        Args:
            word_type: Type woord (werkwoord/deverbaal/overig)

        Returns:
            Lijst met woordsoort-specifieke regels
        """
        rules = []

        if word_type == "werkwoord":
            rules.append("🔸 **Werkwoord-specifieke regels**")
            rules.append("- Definieer als handeling of proces")
            rules.append(
                "- Begin met een zelfstandig naamwoord dat de handeling beschrijft"
            )

            if self.include_examples:
                rules.append("  ✅ controleren: handeling waarbij...")
                rules.append("  ✅ registreren: proces van het vastleggen...")
                rules.append("  ❌ controleren: het controleren van...")
                rules.append("")

        elif word_type == "deverbaal":
            rules.append("🔸 **Deverbaal-specifieke regels**")
            rules.append("- Focus op het resultaat of de staat")
            rules.append("- Vermijd procesbeschrijvingen")

            if self.include_examples:
                rules.append("  ✅ registratie: vastgelegde gegevens...")
                rules.append("  ✅ controle: uitgevoerde verificatie...")
                rules.append("  ❌ registratie: het proces van registreren...")
                rules.append("")

        return rules

    def _build_punctuation_rules(self) -> list[str]:
        """Bouw interpunctie regels."""
        rules = []

        rules.append("🔸 **Komma gebruik**")
        rules.append(
            "- Gebruik komma's spaarzaam en alleen waar nodig voor duidelijkheid"
        )
        rules.append("- Bij opsommingen: gebruik komma's tussen elementen")
        rules.append("- Voor bijzinnen: plaats komma voor 'waarbij', 'waardoor', etc.")

        if self.include_examples:
            rules.append(
                "  ✅ proces waarbij gegevens worden verzameld, verwerkt en opgeslagen"
            )
            rules.append("  ❌ proces, waarbij, gegevens, worden verzameld")
            rules.append("")

        rules.append("🔸 **Afkortingen en haakjes**")
        rules.append("- Plaats afkortingen direct na de volledige term tussen haakjes")
        rules.append("- Gebruik haakjes ALLEEN voor afkortingen, niet voor uitleg")
        rules.append("- Schrijf afkortingen consistent in hoofdletters")

        if self.include_examples:
            rules.append("  ✅ Dienst Justitiële Inrichtingen (DJI)")
            rules.append("  ✅ Algemene Verordening Gegevensbescherming (AVG)")
            rules.append("  ❌ maatregel (corrigerend of preventief)")
            rules.append("  ❌ systeem (meestal digitaal)")
            rules.append("")

        return rules

    def _build_strict_rules(self) -> list[str]:
        """Bouw extra strikte regels voor strict mode."""
        rules = []

        rules.append("🔸 **[STRICT] Geen bijvoeglijke naamwoorden**")
        rules.append("- Vermijd alle niet-essentiële bijvoeglijke naamwoorden")
        rules.append("- Alleen objectieve, meetbare kwalificaties")

        rules.append("🔸 **[STRICT] Maximaal één bijzin**")
        rules.append("- Beperk complexiteit door maximaal één bijzin toe te staan")
        rules.append("- Prefereer meerdere korte zinnen boven één complexe")

        rules.append("🔸 **[STRICT] Geen voorzetsels aan het einde**")
        rules.append("- Eindig nooit een definitie met een voorzetsel")
        rules.append("- Herformuleer indien nodig")

        return rules
