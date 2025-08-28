"""
Modulaire implementatie van CoreInstructionsModule.

Splitst de verantwoordelijkheden op in kleinere, testbare componenten.
"""

from typing import Any


class CoreInstructionsBuilder:
    """Bouwt core instructions op uit modulaire componenten."""

    def __init__(self):
        """Initialize met component builders."""
        self.role_builder = RoleDefinitionBuilder()
        self.task_builder = TaskInstructionBuilder()
        self.word_type_advisor = WordTypeAdvisor()
        self.requirements_builder = RequirementsBuilder()
        self.limits_builder = CharacterLimitBuilder()

    def build(self, begrip: str, metadata: dict[str, Any] = None) -> str:
        """
        Bouw volledige core instructions uit componenten.

        Args:
            begrip: Het te definiëren begrip
            metadata: Optionele metadata zoals max_chars

        Returns:
            Gestructureerde core instructions
        """
        metadata = metadata or {}

        # Verzamel componenten
        sections = []

        # 1. Rol definitie
        sections.append(self.role_builder.build())

        # 2. Taak instructie
        sections.append(self.task_builder.build())

        # 3. Woordsoort-specifiek advies
        word_type_advice = self.word_type_advisor.get_advice(begrip)
        if word_type_advice:
            sections.append(word_type_advice)

        # 4. Kwaliteitsvereisten
        sections.append(self.requirements_builder.build())

        # 5. Karakter limieten (indien nodig)
        limit_warning = self.limits_builder.build(metadata)
        if limit_warning:
            sections.append(limit_warning)

        # Combineer secties met juiste spacing
        return self._combine_sections(sections)

    def _combine_sections(self, sections: list[str]) -> str:
        """Combineer secties met consistente spacing."""
        # Filter lege secties
        sections = [s for s in sections if s and s.strip()]

        # Voeg secties samen met dubbele newline
        result = sections[0]
        for section in sections[1:]:
            # Check of vorige sectie eindigt met newline
            if not result.endswith("\n"):
                result += "\n"
            result += "\n" + section

        return result


class RoleDefinitionBuilder:
    """Bouwt de expert rol definitie."""

    def build(self) -> str:
        """Retourneer rol definitie."""
        return "Je bent een ervaren Nederlandse expert in beleidsmatige definities voor overheidsgebruik."


class TaskInstructionBuilder:
    """Bouwt de opdracht instructie."""

    def build(self) -> str:
        """Retourneer opdracht instructie."""
        return "\n**Je opdracht**: Formuleer een heldere, eenduidige definitie in één enkele zin, zonder toelichting."


class WordTypeAdvisor:
    """Geeft advies gebaseerd op woordsoort detectie."""

    # Suffix mappings
    WERKWOORD_SUFFIXEN = ["eren", "elen", "enen", "igen", "iken", "ijven"]
    DEVERBAAL_SUFFIXEN = ["ing", "atie", "age", "ment", "tie", "sie"]

    # Advies templates
    WERKWOORD_ADVIES = "Als het begrip een handeling beschrijft, definieer het dan als proces of activiteit."
    DEVERBAAL_ADVIES = "Als het begrip een resultaat is, beschrijf het dan als uitkomst van een proces."
    DEFAULT_ADVIES = (
        "Gebruik een zakelijke en generieke stijl voor het definiëren van dit begrip."
    )

    def get_advice(self, begrip: str) -> str:
        """
        Geef woordsoort-specifiek advies.

        Args:
            begrip: Het te analyseren begrip

        Returns:
            Contextueel schrijfadvies
        """
        word_type = self._detect_word_type(begrip)

        advice_map = {
            "werkwoord": self.WERKWOORD_ADVIES,
            "deverbaal": self.DEVERBAAL_ADVIES,
            "overig": self.DEFAULT_ADVIES,
        }

        return advice_map.get(word_type, self.DEFAULT_ADVIES)

    def _detect_word_type(self, begrip: str) -> str:
        """
        Detecteer woordsoort van begrip.

        Returns:
            'werkwoord', 'deverbaal', of 'overig'
        """
        begrip_lower = begrip.lower()

        # Check werkwoord
        if any(begrip_lower.endswith(suffix) for suffix in self.WERKWOORD_SUFFIXEN):
            return "werkwoord"

        # Check deverbaal
        if any(begrip_lower.endswith(suffix) for suffix in self.DEVERBAAL_SUFFIXEN):
            return "deverbaal"

        return "overig"


class RequirementsBuilder:
    """Bouwt de kwaliteitsvereisten sectie."""

    def build(self) -> str:
        """Retourneer vereisten sectie."""
        requirements = [
            "\n**Vereisten**:",
            "• Begin NIET met lidwoorden (de, het, een)",
            "• Gebruik geen cirkelredeneringen",
            "• Wees volledig maar beknopt",
            "• Geschikt voor officiële overheidsdocumenten",
        ]
        return "\n".join(requirements)


class CharacterLimitBuilder:
    """Bouwt karakter limiet waarschuwingen."""

    # Configuratie
    PROMPT_OVERHEAD_ESTIMATE = 1500
    WARNING_THRESHOLD = 2500

    def build(self, metadata: dict[str, Any]) -> str:
        """
        Bouw karakter limiet waarschuwing indien nodig.

        Args:
            metadata: Metadata met max_chars

        Returns:
            Waarschuwing string of lege string
        """
        max_chars = metadata.get("max_chars", 4000)
        available = max_chars - self.PROMPT_OVERHEAD_ESTIMATE

        if available < self.WARNING_THRESHOLD:
            return f"• ⚠️ Maximaal {available} karakters beschikbaar voor de definitie"

        return ""


# Adapter voor gebruik in ModularPromptBuilder
class CoreInstructionsAdapter:
    """Adapter om nieuwe modulaire implementatie te gebruiken in bestaande systeem."""

    def __init__(self):
        """Initialize met builder."""
        self.builder = CoreInstructionsBuilder()

    def build_role_and_basic_rules(
        self, begrip: str, metadata: dict[str, Any] = None
    ) -> str:
        """
        Build core instructions met modulaire aanpak.

        Dit is een drop-in replacement voor de monolithische methode.
        """
        return self.builder.build(begrip, metadata)


# Voorbeeld gebruik
if __name__ == "__main__":
    # Test verschillende scenario's
    adapter = CoreInstructionsAdapter()

    test_cases = [
        {"begrip": "blockchain", "metadata": {"max_chars": 4000}},
        {"begrip": "opsporing", "metadata": {"max_chars": 2000}},
        {"begrip": "beheren", "metadata": {"max_chars": 1500}},
    ]

    for case in test_cases:
        output = adapter.build_role_and_basic_rules(case["begrip"], case["metadata"])
        print(f"\n=== {case['begrip']} ===")
        print(f"Max chars: {case['metadata']['max_chars']}")
        print("-" * 50)
        print(output)
        print(f"\nOutput length: {len(output)} chars")
