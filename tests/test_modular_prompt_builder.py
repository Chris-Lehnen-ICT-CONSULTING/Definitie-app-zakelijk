"""
Tests voor ModularPromptBuilder - Modulaire Prompt Architectuur.

Test alle 6 componenten afzonderlijk en als geheel.
Volgt MODULAIRE_PROMPT_ARCHITECTUUR_WORKFLOW.md testing strategie.
"""

import pytest
from unittest.mock import Mock

from services.prompts.modular_prompt_builder import (
    ModularPromptBuilder,
    PromptComponentConfig
)
from services.definition_generator_context import EnrichedContext
from services.definition_generator_config import UnifiedGeneratorConfig


def create_test_context(
    ontologische_categorie: str = None,
    organisatorisch: list = None,
    domein: list = None
) -> EnrichedContext:
    """Helper function om test context te maken."""

    base_context = {}
    if organisatorisch:
        base_context["organisatorisch"] = organisatorisch
    if domein:
        base_context["domein"] = domein

    metadata = {}
    if ontologische_categorie:
        metadata["ontologische_categorie"] = ontologische_categorie

    return EnrichedContext(
        base_context=base_context,
        sources=[],
        expanded_terms={},
        confidence_scores={},
        metadata=metadata
    )


class TestModularPromptBuilderFoundation:
    """Test de foundation (Fase 1) van ModularPromptBuilder."""

    def test_modular_prompt_builder_initialization(self):
        """Test dat ModularPromptBuilder correct initialiseert."""

        # Default configuratie
        builder = ModularPromptBuilder()
        assert builder.component_config is not None
        assert builder.component_config.include_role is True
        assert builder.component_config.include_context is True
        assert builder.component_config.include_ontological is True

        # Custom configuratie
        custom_config = PromptComponentConfig(
            include_validation_rules=False,
            include_forbidden_patterns=False
        )
        builder_custom = ModularPromptBuilder(custom_config)
        assert builder_custom.component_config.include_validation_rules is False
        assert builder_custom.component_config.include_forbidden_patterns is False

    def test_prompt_component_config_defaults(self):
        """Test dat PromptComponentConfig juiste defaults heeft."""
        config = PromptComponentConfig()

        # Alle basis componenten standaard enabled
        assert config.include_role is True
        assert config.include_context is True
        assert config.include_ontological is True
        assert config.include_validation_rules is True
        assert config.include_forbidden_patterns is True
        assert config.include_final_instructions is True

        # Advanced configuratie
        assert config.detailed_category_guidance is True
        assert config.include_examples_in_rules is True
        assert config.compact_mode is False
        assert config.max_prompt_length == 20000
        assert config.enable_component_metadata is True

    def test_get_strategy_name(self):
        """Test dat strategy name correct is."""
        builder = ModularPromptBuilder()
        assert builder.get_strategy_name() == "modular"


class TestComponent1RoleAndBasicRules:
    """Test Component 1: Rol & Basis Instructies (Fase 1.2)."""

    def test_build_role_and_basic_rules(self):
        """Test dat Component 1 correct genereert."""
        builder = ModularPromptBuilder()

        role_section = builder._build_role_and_basic_rules("authenticatie")

        # Verificeer essentiële elementen uit legacy prompt
        assert "expert in beleidsmatige definities" in role_section
        assert "overheidsgebruik" in role_section
        assert "één enkele zin" in role_section
        assert "zonder toelichting" in role_section
        assert "zakelijke en generieke stijl" in role_section

        # Verificeer dat begrip NIET in deze component zit (dat is voor finale instructies)
        assert "authenticatie" not in role_section

    def test_build_role_with_different_terms(self):
        """Test dat Component 1 werkt voor verschillende begrippen."""
        builder = ModularPromptBuilder()

        terms = ["voorwaardelijk", "toezicht", "registratie", "maatregel"]

        for term in terms:
            role_section = builder._build_role_and_basic_rules(term)

            # Rol sectie moet identiek zijn ongeacht het begrip
            assert "expert in beleidsmatige definities" in role_section
            assert "één enkele zin" in role_section

            # Begrip zelf hoort niet in rol sectie
            assert term not in role_section


class TestComponent2ContextSection:
    """Test Component 2: Context Sectie (Fase 1.2)."""

    def test_build_context_section_with_org_and_domain(self):
        """Test dat Component 2 werkt met organisatorische en domein context."""
        builder = ModularPromptBuilder()

        context = create_test_context(
            organisatorisch=["NP"],
            domein=["Nederlands Politie"]
        )

        context_section = builder._build_context_section(context)

        # Verificeer format
        assert "📌 Context:" in context_section
        assert "Organisatorische context(en): NP" in context_section
        assert "domein: Nederlands Politie" in context_section

    def test_build_context_section_org_only(self):
        """Test Component 2 met alleen organisatorische context."""
        builder = ModularPromptBuilder()

        context = create_test_context(organisatorisch=["DJI"])
        context_section = builder._build_context_section(context)

        assert "📌 Context:" in context_section
        assert "Organisatorische context(en): DJI" in context_section
        assert "domein:" not in context_section

    def test_build_context_section_domain_only(self):
        """Test Component 2 met alleen domein context."""
        builder = ModularPromptBuilder()

        context = create_test_context(domein=["Rechtspraak"])
        context_section = builder._build_context_section(context)

        assert "📌 Context:" in context_section
        assert "domein: Rechtspraak" in context_section
        assert "Organisatorische context" not in context_section

    def test_build_context_section_empty_context(self):
        """Test dat Component 2 lege string teruggeeft zonder context."""
        builder = ModularPromptBuilder()

        context = create_test_context()  # Geen context
        context_section = builder._build_context_section(context)

        assert context_section == ""

    def test_build_context_section_multiple_values(self):
        """Test Component 2 met meerdere organisaties/domeinen."""
        builder = ModularPromptBuilder()

        context = create_test_context(
            organisatorisch=["NP", "DJI"],
            domein=["Politie", "Justitie"]
        )
        context_section = builder._build_context_section(context)

        assert "Organisatorische context(en): NP, DJI" in context_section
        assert "domein: Politie, Justitie" in context_section


class TestComponent3OntologicalSection:
    """Test Component 3: Ontologische Categorie Sectie (Fase 2.1) - KRITISCH COMPONENT."""

    def test_build_ontological_section_with_proces_category(self):
        """Test Component 3 met proces categorie."""
        builder = ModularPromptBuilder()
        context = create_test_context(ontologische_categorie="proces")

        ontological_section = builder._build_ontological_section(context)

        # Basis ESS-02 sectie moet aanwezig zijn
        assert "ESS-02" in ontological_section
        assert "Ontologische categorie" in ontological_section
        assert "type (soort), • exemplaar (specifiek geval), • proces (activiteit), • resultaat (uitkomst)" in ontological_section

        # Proces-specifieke guidance
        assert "PROCES CATEGORIE" in ontological_section
        assert "Focus op HANDELING en VERLOOP" in ontological_section
        assert "is een activiteit waarbij" in ontological_section
        assert "WIE doet WAT en HOE het verloopt" in ontological_section
        assert "BEGINT en EINDIGT" in ontological_section

    def test_build_ontological_section_with_type_category(self):
        """Test Component 3 met type categorie."""
        builder = ModularPromptBuilder()
        context = create_test_context(ontologische_categorie="type")

        ontological_section = builder._build_ontological_section(context)

        # Basis ESS-02 sectie
        assert "ESS-02" in ontological_section

        # Type-specifieke guidance
        assert "TYPE CATEGORIE" in ontological_section
        assert "Focus op CLASSIFICATIE en KENMERKEN" in ontological_section
        assert "is een soort" in ontological_section
        assert "ONDERSCHEIDENDE KENMERKEN" in ontological_section
        assert "bredere klasse" in ontological_section

    def test_build_ontological_section_with_resultaat_category(self):
        """Test Component 3 met resultaat categorie."""
        builder = ModularPromptBuilder()
        context = create_test_context(ontologische_categorie="resultaat")

        ontological_section = builder._build_ontological_section(context)

        # Resultaat-specifieke guidance
        assert "RESULTAAT CATEGORIE" in ontological_section
        assert "Focus op OORSPRONG en GEVOLG" in ontological_section
        assert "is het resultaat van" in ontological_section
        assert "CAUSALE RELATIE" in ontological_section
        assert "uitkomst, gevolg, product" in ontological_section

    def test_build_ontological_section_with_exemplaar_category(self):
        """Test Component 3 met exemplaar categorie."""
        builder = ModularPromptBuilder()
        context = create_test_context(ontologische_categorie="exemplaar")

        ontological_section = builder._build_ontological_section(context)

        # Exemplaar-specifieke guidance
        assert "EXEMPLAAR CATEGORIE" in ontological_section
        assert "Focus op SPECIFICITEIT en INDIVIDUALITEIT" in ontological_section
        assert "is een specifiek exemplaar van" in ontological_section
        assert "CONCRETE instantie" in ontological_section
        assert "UNIEK maakt" in ontological_section

    def test_build_ontological_section_without_category(self):
        """Test Component 3 zonder ontologische categorie."""
        builder = ModularPromptBuilder()
        context = create_test_context()  # Geen ontologische categorie

        ontological_section = builder._build_ontological_section(context)

        # Alleen basis ESS-02 sectie
        assert "ESS-02" in ontological_section
        assert "Ontologische categorie" in ontological_section
        assert "⚠️ Ondubbelzinnigheid is vereist" in ontological_section

        # Geen category-specifieke guidance
        assert "PROCES CATEGORIE" not in ontological_section
        assert "TYPE CATEGORIE" not in ontological_section
        assert "RESULTAAT CATEGORIE" not in ontological_section
        assert "EXEMPLAAR CATEGORIE" not in ontological_section

    def test_build_ontological_section_unknown_category(self):
        """Test Component 3 met onbekende categorie."""
        builder = ModularPromptBuilder()
        context = create_test_context(ontologische_categorie="onbekend")

        ontological_section = builder._build_ontological_section(context)

        # Basis ESS-02 sectie maar geen specifieke guidance
        assert "ESS-02" in ontological_section
        assert "ONBEKEND CATEGORIE" not in ontological_section

    def test_build_ontological_section_configurable_guidance(self):
        """Test dat category-specific guidance kan worden uitgeschakeld."""
        config = PromptComponentConfig(detailed_category_guidance=False)
        builder = ModularPromptBuilder(config)
        context = create_test_context(ontologische_categorie="proces")

        ontological_section = builder._build_ontological_section(context)

        # Basis ESS-02 sectie wel aanwezig
        assert "ESS-02" in ontological_section

        # Maar geen proces-specifieke guidance
        assert "PROCES CATEGORIE" not in ontological_section
        assert "Focus op HANDELING" not in ontological_section

    def test_category_specific_guidance_method(self):
        """Test _get_category_specific_guidance methode direct."""
        builder = ModularPromptBuilder()

        # Test alle ondersteunde categorieën
        categories = ["proces", "type", "resultaat", "exemplaar"]

        for category in categories:
            guidance = builder._get_category_specific_guidance(category)
            assert len(guidance) > 100  # Moet substantiële guidance bevatten
            assert category.upper() in guidance.upper()  # Category naam moet erin staan

        # Test onbekende categorie
        unknown_guidance = builder._get_category_specific_guidance("onbekend")
        assert unknown_guidance == ""

    def test_category_specific_differences(self):
        """Test dat verschillende categories daadwerkelijk verschillende guidance geven."""
        builder = ModularPromptBuilder()
        categories = ["proces", "type", "resultaat", "exemplaar"]
        guidances = {}

        for category in categories:
            context = create_test_context(ontologische_categorie=category)
            ontological_section = builder._build_ontological_section(context)
            guidances[category] = ontological_section

        # Verificeer dat alle guidances verschillend zijn
        unique_guidances = set(guidances.values())
        assert len(unique_guidances) == 4, "Elke categorie moet unieke guidance hebben"

        # Verificeer specifieke elementen per categorie
        assert "activiteit waarbij" in guidances["proces"]
        assert "soort" in guidances["type"]
        assert "resultaat van" in guidances["resultaat"]
        assert "specifiek exemplaar" in guidances["exemplaar"]


class TestBasicPromptGeneration:
    """Test basis prompt generatie met Component 1 & 2 (Fase 1.2)."""

    def test_basic_prompt_generation_framework(self):
        """Test dat basis framework werkt met alle componenten."""
        builder = ModularPromptBuilder()
        context = create_test_context(
            ontologische_categorie="proces",  # Toegevoegd zodat Component 3 actief wordt
            organisatorisch=["NP"],
            domein=["Nederlands Politie"]
        )
        config = UnifiedGeneratorConfig()

        # Genereer prompt
        prompt = builder.build_prompt("authenticatie", context, config)

        # Verificeer dat het framework werkt
        assert len(prompt) > 100  # Moet substantiële inhoud hebben
        assert "expert in beleidsmatige definities" in prompt  # Component 1
        assert "📌 Context:" in prompt  # Component 2
        assert "Organisatorische context(en): NP" in prompt  # Component 2 inhoud

        # Alle componenten moeten nu volledig geïmplementeerd zijn
        assert "### 📐 Let op betekenislaag" in prompt  # Component 3 geïmplementeerd
        assert "### ✅ Richtlijnen voor de definitie:" in prompt  # Component 4 geïmplementeerd
        assert "### ⚠️ Veelgemaakte fouten" in prompt  # Component 5 geïmplementeerd
        assert "### 🎯 FINALE INSTRUCTIES:" in prompt  # Component 6 geïmplementeerd

    def test_configurable_components(self):
        """Test dat componenten kunnen worden in/uitgeschakeld."""

        # Config zonder Component 2 (context)
        config_no_context = PromptComponentConfig(include_context=False)
        builder = ModularPromptBuilder(config_no_context)

        context = create_test_context(organisatorisch=["NP"])
        prompt = builder.build_prompt("test", context, UnifiedGeneratorConfig())

        # Component 1 moet aanwezig zijn
        assert "expert in beleidsmatige definities" in prompt

        # Component 2 moet afwezig zijn
        assert "📌 Context:" not in prompt
        assert "Organisatorische context" not in prompt

    def test_get_component_metadata(self):
        """Test metadata functionaliteit."""
        builder = ModularPromptBuilder()

        # Basis metadata zonder context
        metadata = builder.get_component_metadata()
        assert metadata["builder_type"] == "ModularPromptBuilder"
        assert metadata["total_available_components"] == 6
        assert metadata["active_components"] == 6  # Alle default enabled

        # Metadata met context
        context = create_test_context(
            ontologische_categorie="proces",
            organisatorisch=["NP"]
        )
        metadata_with_context = builder.get_component_metadata("voorwaardelijk", context)

        assert metadata_with_context["ontological_category"] == "proces"
        assert metadata_with_context["has_organizational_context"] is True
        assert metadata_with_context["has_domain_context"] is False
        assert "estimated_prompt_tokens" in metadata_with_context

    def test_error_handling_empty_begrip(self):
        """Test error handling voor lege begrippen."""
        builder = ModularPromptBuilder()
        context = create_test_context()
        config = UnifiedGeneratorConfig()

        # Empty string
        with pytest.raises(ValueError, match="Begrip mag niet leeg zijn"):
            builder.build_prompt("", context, config)

        # Whitespace only
        with pytest.raises(ValueError, match="Begrip mag niet leeg zijn"):
            builder.build_prompt("   ", context, config)

    def test_performance_baseline(self):
        """Test performance baseline voor Fase 1 componenten."""
        import time

        builder = ModularPromptBuilder()
        context = create_test_context(
            ontologische_categorie="proces",
            organisatorisch=["NP"],
            domein=["Nederlands Politie"]
        )
        config = UnifiedGeneratorConfig()

        start_time = time.time()
        prompt = builder.build_prompt("voorwaardelijk", context, config)
        generation_time = time.time() - start_time

        # Performance moet acceptabel zijn (< 1s voor basis componenten)
        assert generation_time < 1.0, f"Prompt generatie te langzaam: {generation_time:.3f}s"

        # Prompt moet volledige lengte hebben nu alle componenten geïmplementeerd zijn
        assert 5000 < len(prompt) < 20000  # Volledige prompt met alle 6 componenten


class TestComponent4ValidationRules:
    """Test suite voor Component 4: Validatie regels sectie."""

    def test_validation_rules_structure(self):
        """Test dat validatie regels de juiste structuur hebben."""
        builder = ModularPromptBuilder()
        rules = builder._build_validation_rules_section()

        # Check hoofdsecties aanwezig
        assert "### ✅ Richtlijnen voor de definitie:" in rules
        assert "🔷 STRUCTUUR (STR)" in rules
        assert "🔶 ESSENTIE (ESS)" in rules
        assert "🔸 CONTEXT (CON)" in rules
        assert "🔹 INTERNE COHERENTIE (INT)" in rules
        assert "🔺 SAMENHANG (SAM)" in rules
        assert "⚡ AI-SPECIFIEK (ARAI)" in rules
        assert "📋 SAMENVATTING KERNREGELS" in rules

    def test_critical_rules_present(self):
        """Test dat kritieke regels aanwezig zijn."""
        builder = ModularPromptBuilder()
        rules = builder._build_validation_rules_section()

        # Kritieke regels
        assert "STR-01" in rules  # Begin met zelfstandig naamwoord
        assert "STR-02" in rules  # Geen herhaling begrip
        assert "ESS-02" in rules  # Ontologische categorie (KRITIEK!)
        assert "ARAI-06" in rules  # Correcte start

        # Check voorbeelden
        assert "✅" in rules  # Goede voorbeelden
        assert "❌" in rules  # Foute voorbeelden

    def test_rule_examples(self):
        """Test dat regels concrete voorbeelden hebben."""
        builder = ModularPromptBuilder()
        rules = builder._build_validation_rules_section()

        # Check specifieke voorbeelden
        assert '"Een **overeenkomst** is..."' in rules
        assert '"**Controleren** is..." (werkwoord)' in rules
        assert 'Type: "is een soort/categorie..."' in rules
        assert 'Proces: "is een activiteit waarbij..."' in rules

    def test_validation_rules_integration(self):
        """Test integratie van validatie regels in volledige prompt."""
        config = PromptComponentConfig(
            include_role=True,
            include_context=True,
            include_ontological=True,
            include_validation_rules=True,
            include_forbidden_patterns=False,
            include_final_instructions=False
        )

        builder = ModularPromptBuilder(component_config=config)
        context = create_test_context()

        prompt = builder.build_prompt("testbegrip", context, UnifiedGeneratorConfig())

        # Validatie regels moeten aanwezig zijn
        assert "### ✅ Richtlijnen voor de definitie:" in prompt
        assert "STRUCTUUR (STR)" in prompt
        assert "ESSENTIE (ESS)" in prompt


class TestComponent5ForbiddenPatterns:
    """Test suite voor Component 5: Verboden patronen sectie."""

    def test_forbidden_patterns_structure(self):
        """Test dat verboden patronen sectie de juiste structuur heeft."""
        builder = ModularPromptBuilder()
        context = create_test_context()
        patterns = builder._build_forbidden_patterns_section(context)

        # Check hoofdsecties
        assert "### ⚠️ Veelgemaakte fouten (vermijden!):" in patterns
        assert "🚫 VERBODEN STARTWOORDEN" in patterns
        assert "🔴 VAGE CONTAINERBEGRIPPEN" in patterns
        assert "⛔ MODALE WERKWOORDEN" in patterns
        assert "🚨 CONTEXT-SPECIFIEKE VALKUILEN" in patterns
        assert "💥 TOELICHTING & UITWEIDINGEN" in patterns
        assert "📝 POSITIEVE ALTERNATIEVEN" in patterns

    def test_forbidden_start_words(self):
        """Test dat verboden startwoorden correct zijn."""
        builder = ModularPromptBuilder()
        context = create_test_context()
        patterns = builder._build_forbidden_patterns_section(context)

        # Verboden startwoorden
        assert '"Het..."' in patterns
        assert '"De..."' in patterns
        assert '"Een..." als het begrip al "een" bevat' in patterns
        assert 'Het begrip zelf' in patterns
        assert 'Werkwoorden' in patterns

        # Positieve alternatieven
        assert 'Direct het hoofdwoord' in patterns
        assert '"Activiteit waarbij..."' in patterns

    def test_container_begrippen(self):
        """Test dat vage containerbegrippen worden benoemd."""
        builder = ModularPromptBuilder()
        context = create_test_context()
        patterns = builder._build_forbidden_patterns_section(context)

        # Lexicale containers
        assert '"aspect"' in patterns
        assert '"element"' in patterns
        assert '"onderdeel"' in patterns

        # Ambtelijke containers
        assert '"aangelegenheid"' in patterns
        assert '"materie"' in patterns

        # Alternatieven
        assert '"proces"' in patterns
        assert '"document"' in patterns

    def test_modal_verbs(self):
        """Test dat modale werkwoorden correct worden behandeld."""
        builder = ModularPromptBuilder()
        context = create_test_context()
        patterns = builder._build_forbidden_patterns_section(context)

        # Verboden modaliteiten
        assert '"kan"' in patterns
        assert '"moet"' in patterns
        assert '"mag"' in patterns
        assert '"zou"' in patterns

        # Feitelijke alternatieven
        assert '"Een proces waarbij... wordt uitgevoerd"' in patterns
        assert '"Een document met..."' in patterns

    def test_forbidden_patterns_integration(self):
        """Test integratie van verboden patronen in volledige prompt."""
        config = PromptComponentConfig(
            include_role=True,
            include_context=False,
            include_ontological=False,
            include_validation_rules=False,
            include_forbidden_patterns=True,
            include_final_instructions=False
        )

        builder = ModularPromptBuilder(component_config=config)
        context = create_test_context()

        prompt = builder.build_prompt("testbegrip", context, UnifiedGeneratorConfig())

        # Verboden patronen sectie moet aanwezig zijn
        assert "### ⚠️ Veelgemaakte fouten (vermijden!):" in prompt
        assert "VERBODEN STARTWOORDEN" in prompt
        assert "VAGE CONTAINERBEGRIPPEN" in prompt

    def test_context_specific_forbidden_patterns(self):
        """Test dat context-specifieke verboden patronen worden toegevoegd."""
        builder = ModularPromptBuilder()

        # Test met organisatorische context
        context = create_test_context(
            organisatorisch=["DJI", "Gevangeniswezen"],
            domein=["Penitentiair recht"]
        )
        patterns = builder._build_forbidden_patterns_section(context)

        # Check dat context-specifieke verboden zijn toegevoegd
        assert "Gebruik de term 'DJI' of een variant daarvan niet letterlijk in de definitie." in patterns
        assert "Gebruik de term 'Gevangeniswezen' of een variant daarvan niet letterlijk in de definitie." in patterns
        assert "Vermijd expliciete vermelding van domein 'Penitentiair recht' in de definitie." in patterns


class TestComponent6FinalInstructions:
    """Test suite voor Component 6: Finale instructies sectie."""

    def test_final_instructions_structure(self):
        """Test dat finale instructies de juiste structuur hebben."""
        builder = ModularPromptBuilder()
        context = create_test_context()
        instructions = builder._build_final_instructions_section("testbegrip", context)

        # Check hoofdsecties
        assert "### 🎯 FINALE INSTRUCTIES:" in instructions
        assert "✏️ Definitieopdracht:" in instructions
        assert "📋 **CHECKLIST" in instructions
        assert "🔍 KWALITEITSCONTROLE:" in instructions
        assert "📊 METADATA voor traceerbaarheid:" in instructions
        assert "**ANTWOORD:**" in instructions

    def test_checklist_items(self):
        """Test dat checklist alle belangrijke items bevat."""
        builder = ModularPromptBuilder()
        context = create_test_context()
        instructions = builder._build_final_instructions_section("testbegrip", context)

        # Checklist items
        assert "Begint met zelfstandig naamwoord" in instructions
        assert "Eén enkele zin zonder punt" in instructions
        assert "Geen toelichting, voorbeelden of haakjes" in instructions
        assert "Ontologische categorie is duidelijk" in instructions
        assert "Geen verboden woorden" in instructions

    def test_context_awareness(self):
        """Test dat instructies zich aanpassen aan context."""
        builder = ModularPromptBuilder()

        # Zonder context
        no_context = create_test_context()
        instructions_no_ctx = builder._build_final_instructions_section("test", no_context)
        assert "algemeen gebruik" in instructions_no_ctx
        assert "Context beschikbaar: Nee" in instructions_no_ctx

        # Met context
        with_context = create_test_context(
            organisatorisch=["NP"],
            domein=["Politie"]
        )
        instructions_with_ctx = builder._build_final_instructions_section("test", with_context)
        assert "de gegeven context" in instructions_with_ctx
        assert "Context beschikbaar: Ja" in instructions_with_ctx

    def test_ontological_category_hint(self):
        """Test dat ontologische categorie hints worden getoond."""
        builder = ModularPromptBuilder()

        # Test verschillende categorieën
        categories = {
            "proces": "activiteit/handeling",
            "type": "soort/categorie",
            "resultaat": "uitkomst/gevolg",
            "exemplaar": "specifiek geval"
        }

        for cat, hint in categories.items():
            context = create_test_context(ontologische_categorie=cat)
            instructions = builder._build_final_instructions_section("test", context)
            assert f"Dit is een **{cat}**" in instructions
            assert hint in instructions

    def test_final_instructions_integration(self):
        """Test integratie van finale instructies in volledige prompt."""
        config = PromptComponentConfig(
            include_role=True,
            include_context=False,
            include_ontological=False,
            include_validation_rules=False,
            include_forbidden_patterns=False,
            include_final_instructions=True
        )

        builder = ModularPromptBuilder(component_config=config)
        context = create_test_context()

        prompt = builder.build_prompt("testbegrip", context, UnifiedGeneratorConfig())

        # Finale instructies moeten aanwezig zijn
        assert "### 🎯 FINALE INSTRUCTIES:" in prompt
        assert "CHECKLIST" in prompt
        assert "KWALITEITSCONTROLE" in prompt
        assert "**ANTWOORD:**" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
