"""
Error Prevention Module - Verboden patronen en veelgemaakte fouten.

Deze module is verantwoordelijk voor:
1. Basis verboden patronen
2. Context-aware verboden toevoegingen
3. Verboden startwoorden
4. Validatiematrix
"""

import logging
from typing import Any

from .base_module import BasePromptModule, ModuleContext, ModuleOutput

logger = logging.getLogger(__name__)


class ErrorPreventionModule(BasePromptModule):
    """
    Module voor het genereren van verboden patronen en veelgemaakte fouten.

    Genereert waarschuwingen voor veel voorkomende fouten en
    past context-specifieke verboden toe.
    """

    def __init__(self):
        """Initialize de error prevention module."""
        super().__init__(
            module_id="error_prevention",
            module_name="Error Prevention & Forbidden Patterns",
        )
        self.include_validation_matrix = True
        self.extended_forbidden_list = True

    def initialize(self, config: dict[str, Any]) -> None:
        """
        Initialize module met configuratie.

        Args:
            config: Module configuratie
        """
        self._config = config
        self.include_validation_matrix = config.get("include_validation_matrix", True)
        self.extended_forbidden_list = config.get("extended_forbidden_list", True)
        self._initialized = True
        logger.debug(
            f"ErrorPreventionModule geïnitialiseerd "
            f"(matrix={self.include_validation_matrix}, extended={self.extended_forbidden_list})"
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
        Genereer verboden patronen sectie.

        Args:
            context: Module context

        Returns:
            ModuleOutput met verboden patronen
        """
        try:
            # Haal context informatie op van ContextAwarenessModule
            # EPIC-010: Gebruik alle 3 actieve context types (domein is legacy)
            org_contexts = context.get_shared("organization_contexts", [])
            jur_contexts = context.get_shared("juridical_contexts", [])
            wet_contexts = context.get_shared("legal_basis_contexts", [])

            # Bouw secties
            sections = []

            # Header
            sections.append("### ⚠️ Veelgemaakte fouten (vermijden!):")

            # Basis fouten
            sections.extend(self._build_basic_errors())

            # Verboden startwoorden
            if self.extended_forbidden_list:
                sections.extend(self._build_forbidden_starters())

            # Context-specifieke verboden
            context_forbidden = self._build_context_forbidden(
                org_contexts, jur_contexts, wet_contexts
            )
            if context_forbidden:
                sections.append("\n### 🚨 CONTEXT-SPECIFIEKE VERBODEN:")
                sections.extend(context_forbidden)

            # Validatiematrix
            if self.include_validation_matrix:
                sections.append(self._build_validation_matrix())

            # Laatste waarschuwing
            sections.append(
                "\n🚫 Let op: context en bronnen mogen niet letterlijk of herleidbaar in de definitie voorkomen."
            )

            # Combineer alles
            content = "\n".join(sections)

            return ModuleOutput(
                content=content,
                metadata={
                    "context_forbidden_count": len(org_contexts)
                    + len(jur_contexts)
                    + len(wet_contexts),
                    "include_matrix": self.include_validation_matrix,
                    "extended_list": self.extended_forbidden_list,
                },
            )

        except Exception as e:
            logger.error(f"ErrorPreventionModule execution failed: {e}", exc_info=True)
            return ModuleOutput(
                content="",
                metadata={"error": str(e)},
                success=False,
                error_message=f"Failed to generate error prevention section: {e!s}",
            )

    def get_dependencies(self) -> list[str]:
        """
        Deze module is afhankelijk van ContextAwarenessModule.

        Returns:
            Lijst met dependency
        """
        return ["context_awareness"]

    def _build_basic_errors(self) -> list[str]:
        """Bouw basis veelgemaakte fouten."""
        return [
            "- ❌ Begin niet met lidwoorden ('de', 'het', 'een')",
            "- ❌ Gebruik geen koppelwerkwoord aan het begin ('is', 'betekent', 'omvat')",
            "- ❌ Herhaal het begrip niet letterlijk",
            "- ❌ Gebruik geen synoniem als definitie",
            "- ❌ Vermijd vage containerbegrippen ('aspect', 'element', 'factor', 'kwestie')",
            "- ❌ Gebruik enkelvoud; infinitief bij werkwoorden",
        ]

    def _build_forbidden_starters(self) -> list[str]:
        """Bouw uitgebreide lijst verboden startwoorden."""
        forbidden_starters = [
            "is",
            "betreft",
            "omvat",
            "betekent",
            "verwijst naar",
            "houdt in",
            "heeft betrekking op",
            "duidt op",
            "staat voor",
            "impliceert",
            "definieert",
            "beschrijft",
            "wordt",
            "zijn",
            "was",
            "waren",
            "behelst",
            "bevat",
            "bestaat uit",
            "de",
            "het",
            "een",
            "proces waarbij",
            "handeling die",
            "vorm van",
            "type van",
            "soort van",
            "methode voor",
            "wijze waarop",
            "manier om",
            "een belangrijk",
            "een essentieel",
            "een vaak gebruikte",
            "een veelvoorkomende",
        ]

        return [f"- ❌ Start niet met '{starter}'" for starter in forbidden_starters]

    def _build_context_forbidden(
        self, org_contexts: list[str], jur_contexts: list[str], wet_contexts: list[str]
    ) -> list[str]:
        """
        Bouw context-specifieke verboden.

        Args:
            org_contexts: Organisatorische contexten
            jur_contexts: Juridische contexten
            wet_contexts: Wettelijke basis contexten

        Returns:
            Lijst met context-specifieke verboden
        """
        forbidden = []

        # Organisatie mapping voor afkortingen
        org_mappings = {
            "NP": "Nederlands Politie",
            "DJI": "Dienst Justitiële Inrichtingen",
            "OM": "Openbaar Ministerie",
            "ZM": "Zittende Magistratuur",
            "3RO": "Samenwerkingsverband Reclasseringsorganisaties",
            "CJIB": "Centraal Justitieel Incassobureau",
            "KMAR": "Koninklijke Marechaussee",
            "FIOD": "Fiscale Inlichtingen- en Opsporingsdienst",
        }

        # Organisatorische context verboden
        for org in org_contexts:
            forbidden.append(
                f"- Gebruik de term '{org}' of een variant daarvan niet letterlijk in de definitie."
            )

            # Voeg volledige naam toe als het een afkorting is
            if org in org_mappings:
                forbidden.append(
                    f"- Gebruik de term '{org_mappings[org]}' of een variant daarvan niet letterlijk in de definitie."
                )

        # Juridische context verboden
        for jur in jur_contexts:
            forbidden.append(
                f"- Vermijd expliciete vermelding van juridisch context '{jur}' in de definitie."
            )

        # Wettelijke basis verboden
        for wet in wet_contexts:
            forbidden.append(
                f"- Vermijd expliciete vermelding van wetboek '{wet}' in de definitie."
            )

        return forbidden

    def _build_validation_matrix(self) -> str:
        """Bouw de validatiematrix."""
        return """
| Probleem                             | Afgedekt? | Toelichting                                |
|--------------------------------------|-----------|---------------------------------------------|
| Start met begrip                     | ✅        | Vermijd cirkeldefinities                     |
| Abstracte constructies               | ✅        | 'proces waarbij', 'handeling die', enz.      |
| Koppelwerkwoorden aan het begin      | ✅        | 'is', 'omvat', 'betekent'                    |
| Lidwoorden aan het begin             | ✅        | 'de', 'het', 'een'                           |
| Letterlijke contextvermelding        | ✅        | Noem context niet letterlijk                 |
| Afkortingen onverklaard              | ✅        | Licht afkortingen toe in de definitie       |
| Subjectieve termen                   | ✅        | Geen 'essentieel', 'belangrijk', 'adequaat' |
| Bijzinconstructies                   | ✅        | Vermijd 'die', 'waarin', 'zoals' enz.       |"""
