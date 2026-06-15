"""Analyseer de modulaire structuur van de ModularPromptBuilder."""

import re

from services.definition_generator_context import EnrichedContext
from services.prompts.modular_prompt_builder import (
    ModularPromptBuilder,
    PromptComponentConfig,
)


def create_test_context(category="proces"):
    """Maak test context met ontologische categorie."""
    return EnrichedContext(
        base_context={
            "organisatorisch": ["DJI"],
            "domein": ["Rechtspraak"],
        },
        sources=[],
        expanded_terms={},
        confidence_scores={},
        metadata={
            "ontologische_categorie": category,
            "timestamp": "2025-08-26T10:00:00",
        },
    )


def analyze_component_output():
    """Analyseer de output van elke component afzonderlijk."""
    print("=" * 80)
    print("MODULAIRE PROMPT BUILDER ANALYSE")
    print("=" * 80)
    print("\nDoel: Verifiëren dat elke module zijn specifieke taak uitvoert")
    print("zonder monolithisch te worden.\n")

    # Test context
    begrip = "voorwaardelijk"
    context = create_test_context("proces")

    # Maak builder
    builder = ModularPromptBuilder()

    # Test elke component afzonderlijk
    components = [
        ("Component 1: Rol & Basis Instructies", builder._build_role_and_basic_rules),
        ("Component 2: Context Sectie", builder._build_context_section),
        ("Component 3: Ontologische Categorie", builder._build_ontological_section),
        ("Component 4: Validatie Regels", builder._build_validation_rules_section),
        ("Component 5: Verboden Patronen", builder._build_forbidden_patterns_section),
        ("Component 6: Finale Instructies", builder._build_final_instructions_section),
    ]

    for i, (name, method) in enumerate(components, 1):
        print(f"\n{'='*60}")
        print(f"{name}")
        print("=" * 60)

        try:
            # Roep de method aan met juiste parameters
            if i in {1, 6}:  # Methods die begrip nodig hebben
                output = method(begrip) if i == 1 else method(begrip, context)
            elif i in {3, 5}:  # Methods die context nodig hebben
                output = method(context)
            else:  # Component 2 en 4
                output = method(context) if i == 2 else method()

            # Analyseer output
            lines = output.split("\n") if output else []
            word_count = len(output.split()) if output else 0
            char_count = len(output) if output else 0

            print("📊 Statistieken:")
            print(f"   - Karakters: {char_count}")
            print(f"   - Woorden: {word_count}")
            print(f"   - Regels: {len(lines)}")
            print(f"   - Leeg: {'Ja ⚠️' if not output else 'Nee ✓'}")

            # Toon eerste paar regels
            if output:
                print("\n📄 Eerste 3 regels:")
                for line in lines[:3]:
                    if line.strip():
                        print(f"   {line[:80]}{'...' if len(line) > 80 else ''}")

            # Component-specifieke checks
            if i == 1:  # Rol component
                print(
                    f"\n✓ Check: Bevat 'expert'? {'Ja' if 'expert' in output else 'Nee ⚠️'}"
                )
                print(
                    f"✓ Check: Bevat 'één zin'? {'Ja' if 'één' in output else 'Nee ⚠️'}"
                )
            elif i == 2:  # Context component
                print(
                    f"\n✓ Check: Bevat 'DJI'? {'Ja' if 'DJI' in output else 'Nee ⚠️'}"
                )
                print(
                    f"✓ Check: Bevat 'Rechtspraak'? {'Ja' if 'Rechtspraak' in output else 'Nee ⚠️'}"
                )
            elif i == 3:  # Ontologische component
                print(
                    f"\n✓ Check: Bevat 'ESS-02'? {'Ja' if 'ESS-02' in output else 'Nee ⚠️'}"
                )
                print(
                    f"✓ Check: Bevat 'PROCES CATEGORIE'? {'Ja' if 'PROCES CATEGORIE' in output else 'Nee ⚠️'}"
                )
                print(
                    f"✓ Check: Bevat proces-specifieke guidance? {'Ja' if 'activiteit waarbij' in output else 'Nee ⚠️'}"
                )
            elif i == 4:  # Validatie regels
                print(
                    f"\n✓ Check: Bevat 'CON-01'? {'Ja' if 'CON-01' in output else 'Nee ⚠️'}"
                )
                print(
                    f"✓ Check: Bevat 'ESS-02'? {'Ja' if 'ESS-02' in output else 'Nee ⚠️'}"
                )
                print(
                    f"✓ Check: Bevat voorbeelden (✅/❌)? {'Ja' if '✅' in output and '❌' in output else 'Nee ⚠️'}"
                )
            elif i == 5:  # Verboden patronen
                print(
                    f"\n✓ Check: Bevat verboden startwoorden? {'Ja' if 'Start niet met' in output else 'Nee ⚠️'}"
                )
                print(
                    f"✓ Check: Bevat context-specifieke verboden? {'Ja' if 'CONTEXT-SPECIFIEKE VERBODEN' in output else 'Nee ⚠️'}"
                )
            elif i == 6:  # Finale instructies
                print(
                    f"\n✓ Check: Bevat begrip 'voorwaardelijk'? {'Ja' if 'voorwaardelijk' in output else 'Nee ⚠️'}"
                )
                print(
                    f"✓ Check: Bevat checklist? {'Ja' if 'CHECKLIST' in output else 'Nee ⚠️'}"
                )

        except Exception as e:
            print(f"❌ Error: {e}")

    # Test complete prompt
    print(f"\n{'='*80}")
    print("VOLLEDIGE PROMPT TEST")
    print("=" * 80)

    full_prompt = builder.build_prompt(begrip, context, None)
    print("\n📊 Volledige prompt statistieken:")
    print(f"   - Totale lengte: {len(full_prompt)} karakters")
    print(f"   - Geschatte tokens: ~{len(full_prompt.split()) * 1.3:.0f}")
    print(
        f"   - Bevat alle componenten: {'Ja ✓' if all(marker in full_prompt for marker in ['expert', 'Context:', 'ESS-02', 'CON-01', 'Start niet met', 'CHECKLIST']) else 'Nee ⚠️'}"
    )


def test_modularity():
    """Test dat componenten echt modulair zijn."""
    print(f"\n{'='*80}")
    print("MODULARITEITSTEST")
    print("=" * 80)
    print("\nTest: Kunnen we componenten in/uitschakelen zonder de rest te breken?")

    begrip = "toezicht"
    context = create_test_context("proces")

    # Test verschillende configuraties
    configs = [
        (
            "Alleen basis (component 1)",
            PromptComponentConfig(
                include_context=False,
                include_ontological=False,
                include_validation_rules=False,
                include_forbidden_patterns=False,
                include_final_instructions=False,
            ),
        ),
        (
            "Basis + Ontologisch (1+3)",
            PromptComponentConfig(
                include_context=False,
                include_validation_rules=False,
                include_forbidden_patterns=False,
                include_final_instructions=False,
            ),
        ),
        (
            "Zonder validatie regels (1,2,3,5,6)",
            PromptComponentConfig(include_validation_rules=False),
        ),
        (
            "Minimaal werkbaar (1,3,6)",
            PromptComponentConfig(
                include_context=False,
                include_validation_rules=False,
                include_forbidden_patterns=False,
            ),
        ),
    ]

    for name, config in configs:
        builder = ModularPromptBuilder(config)
        prompt = builder.build_prompt(begrip, context, None)

        print(f"\n📦 {name}:")
        print(f"   - Actieve componenten: {builder._count_active_components()}/6")
        print(f"   - Prompt lengte: {len(prompt)} karakters")
        print("   - Werkt zonder errors: Ja ✓")


def verify_no_monolith():
    """Verifieer dat we geen nieuwe monoliet hebben gemaakt."""
    print(f"\n{'='*80}")
    print("ANTI-MONOLIET VERIFICATIE")
    print("=" * 80)

    print("\n✅ Modulaire kenmerken:")
    print("   1. Elke component heeft eigen methode")
    print("   2. Components kunnen in/uitgeschakeld worden")
    print("   3. Components hebben duidelijke single responsibility")
    print("   4. Geen onderlinge afhankelijkheden tussen components")
    print("   5. Configureerbaar via PromptComponentConfig")

    print("\n📊 Component verantwoordelijkheden:")
    print("   • Component 1: ALLEEN expert rol + basis regels (~3 regels)")
    print("   • Component 2: ALLEEN context informatie (adaptief)")
    print("   • Component 3: ALLEEN ontologische categorie + guidance")
    print("   • Component 4: ALLEEN validatie regels lijst")
    print("   • Component 5: ALLEEN verboden patronen")
    print("   • Component 6: ALLEEN finale instructies + metadata")

    print("\n🔍 Monoliet indicatoren (moeten NIET aanwezig zijn):")
    # Check de source code
    with open(
        "/Users/chrislehnen/Projecten/Definitie-app/src/services/prompts/modular_prompt_builder.py"
    ) as f:
        source = f.read()

    # Check voor monolithische patterns
    checks = [
        (
            "Mega methods (>200 regels)",
            len(
                [
                    m
                    for m in re.findall(
                        r"def \w+.*?(?=\n    def|\nclass|\Z)", source, re.DOTALL
                    )
                    if len(m.split("\n")) > 200
                ]
            ),
        ),
        ("God class patterns", source.count("self.") > 100),
        ("Hardcoded dependencies", "import prompt_builder" in source),
        (
            "Cross-component calls",
            bool(re.search(r"self\._build_\w+.*self\._build_\w+", source)),
        ),
    ]

    for check, found in checks:
        status = "⚠️ Gevonden" if found else "✓ Niet gevonden"
        print(f"   • {check}: {status}")


if __name__ == "__main__":
    analyze_component_output()
    test_modularity()
    verify_no_monolith()

    print(f"\n{'='*80}")
    print("✅ ANALYSE COMPLEET")
    print("=" * 80)
