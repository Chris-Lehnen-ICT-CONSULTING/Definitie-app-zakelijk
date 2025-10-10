"""
Analyse script om te controleren welke toetsregels gebruikt worden
bij generatie en validatie van definities.
"""

from typing import Any

# Import from deprecated location - this analysis script needs the real implementation
from deprecated.generation.definitie_generator import (DefinitieGenerator,
                                                       GenerationContext,
                                                       OntologischeCategorie)

from config.toetsregel_manager import get_toetsregel_manager
from validation.definitie_validator import DefinitieValidator


def analyze_rule_usage():
    """Analyseer welke regels gebruikt worden bij generatie en validatie."""

    print("📊 TOETSREGELS USAGE ANALYSIS")
    print("=" * 50)

    # Initialiseer componenten
    rule_manager = get_toetsregel_manager()
    generator = DefinitieGenerator()
    validator = DefinitieValidator()

    # Haal alle beschikbare regels op
    all_rules = rule_manager.get_available_regels()
    print(f"📋 Totaal aantal beschikbare regels: {len(all_rules)}")
    print(f"    Regel IDs: {sorted(all_rules)}")

    # Analyseer per ontologische categorie
    categorieën = [
        OntologischeCategorie.TYPE,
        OntologischeCategorie.PROCES,
        OntologischeCategorie.RESULTAAT,
        OntologischeCategorie.EXEMPLAAR,
    ]

    results = {}

    for categorie in categorieën:
        print(f"\n🎯 CATEGORIE: {categorie.value.upper()}")
        print("-" * 40)

        # Test generatie
        generation_rules = analyze_generation_rules(generator, categorie)

        # Test validatie
        validation_rules = analyze_validation_rules(validator, categorie)

        # Vergelijk
        comparison = compare_rule_usage(generation_rules, validation_rules, all_rules)

        results[categorie.value] = {
            "generation": generation_rules,
            "validation": validation_rules,
            "comparison": comparison,
        }

        print_category_analysis(
            categorie.value, generation_rules, validation_rules, comparison
        )

    # Overall analyse
    print_overall_analysis(results, all_rules)

    return results


def analyze_generation_rules(
    generator: DefinitieGenerator, categorie: OntologischeCategorie
) -> dict[str, Any]:
    """Analyseer welke regels gebruikt worden voor generatie."""

    # Maak test context
    context = GenerationContext(
        begrip="test_begrip",
        organisatorische_context="TEST_ORG",
        juridische_context="TEST_JURIDISCH",
        categorie=categorie,
    )

    # Genereer en haal gebruikte instructies op
    result = generator.generate(context)

    used_rules = {}
    rule_ids = set()

    for instructie in result.gebruikte_instructies:
        rule_id = instructie.rule_id
        rule_ids.add(rule_id)
        used_rules[rule_id] = {
            "guidance": (
                instructie.guidance[:100] + "..."
                if len(instructie.guidance) > 100
                else instructie.guidance
            ),
            "template": instructie.template,
            "focus_areas": instructie.focus_areas,
            "priority": instructie.priority,
        }

    return {
        "rule_ids": sorted(rule_ids),
        "count": len(rule_ids),
        "details": used_rules,
        "total_instructions": len(result.gebruikte_instructies),
    }


def analyze_validation_rules(
    validator: DefinitieValidator, categorie: OntologischeCategorie
) -> dict[str, Any]:
    """Analyseer welke regels gebruikt worden voor validatie."""

    # Test met dummy definitie
    test_definitie = "Test definitie waarbij alle patronen gedetecteerd kunnen worden binnen de context"

    # Valideer
    result = validator.validate(test_definitie, categorie)

    # Haal criteria op via private method (voor analyse)
    criteria = validator._load_validation_criteria(categorie)

    used_rules = {}
    rule_ids = set()

    for criterium in criteria:
        rule_id = criterium.rule_id
        rule_ids.add(rule_id)
        used_rules[rule_id] = {
            "description": (
                criterium.description[:100] + "..."
                if len(criterium.description) > 100
                else criterium.description
            ),
            "patterns_count": len(criterium.patterns_to_avoid),
            "required_elements": criterium.required_elements,
            "structure_checks": criterium.structure_checks,
            "severity": criterium.severity.value,
            "weight": criterium.scoring_weight,
        }

    return {
        "rule_ids": sorted(rule_ids),
        "count": len(rule_ids),
        "details": used_rules,
        "total_criteria": len(criteria),
        "validation_score": result.overall_score,
        "violations_found": len(result.violations),
    }


def compare_rule_usage(
    generation_rules: dict[str, Any],
    validation_rules: dict[str, Any],
    all_rules: list[str],
) -> dict[str, Any]:
    """Vergelijk regel gebruik tussen generatie en validatie."""

    gen_set = set(generation_rules["rule_ids"])
    val_set = set(validation_rules["rule_ids"])
    all_set = set(all_rules)

    return {
        "both_systems": sorted(gen_set & val_set),
        "only_generation": sorted(gen_set - val_set),
        "only_validation": sorted(val_set - gen_set),
        "unused_rules": sorted(all_set - (gen_set | val_set)),
        "coverage_generation": len(gen_set) / len(all_set) * 100,
        "coverage_validation": len(val_set) / len(all_set) * 100,
        "overlap_percentage": (
            len(gen_set & val_set) / len(gen_set | val_set) * 100
            if (gen_set | val_set)
            else 0
        ),
    }


def print_category_analysis(
    category: str,
    generation_rules: dict[str, Any],
    validation_rules: dict[str, Any],
    comparison: dict[str, Any],
):
    """Print analyse voor één categorie."""

    print("🔧 GENERATIE:")
    print(
        f"   Regels gebruikt: {generation_rules['count']} ({comparison['coverage_generation']:.1f}% van totaal)"
    )
    print(f"   Regel IDs: {generation_rules['rule_ids']}")

    print("\n🔍 VALIDATIE:")
    print(
        f"   Regels gebruikt: {validation_rules['count']} ({comparison['coverage_validation']:.1f}% van totaal)"
    )
    print(f"   Regel IDs: {validation_rules['rule_ids']}")

    print("\n📊 VERGELIJKING:")
    print(f"   Beide systemen: {len(comparison['both_systems'])} regels")
    print(f"   Alleen generatie: {len(comparison['only_generation'])} regels")
    print(f"   Alleen validatie: {len(comparison['only_validation'])} regels")
    print(f"   Ongebruikt: {len(comparison['unused_rules'])} regels")
    print(f"   Overlap percentage: {comparison['overlap_percentage']:.1f}%")

    if comparison["unused_rules"]:
        print(f"   ⚠️  Ongebruikte regels: {comparison['unused_rules']}")


def print_overall_analysis(results: dict[str, Any], all_rules: list[str]):
    """Print overall analyse over alle categorieën."""

    print("\n🎯 OVERALL ANALYSE")
    print("=" * 30)

    # Verzamel alle gebruikte regels over categorieën
    all_gen_rules = set()
    all_val_rules = set()

    for category_data in results.values():
        all_gen_rules.update(category_data["generation"]["rule_ids"])
        all_val_rules.update(category_data["validation"]["rule_ids"])

    total_used = all_gen_rules | all_val_rules
    unused_overall = set(all_rules) - total_used

    print(f"📋 Totaal regels in systeem: {len(all_rules)}")
    print(
        f"🔧 Gebruikt voor generatie: {len(all_gen_rules)} ({len(all_gen_rules)/len(all_rules)*100:.1f}%)"
    )
    print(
        f"🔍 Gebruikt voor validatie: {len(all_val_rules)} ({len(all_val_rules)/len(all_rules)*100:.1f}%)"
    )
    print(f"⚡ Gebruikt door beide: {len(all_gen_rules & all_val_rules)}")
    print(
        f"📊 Totaal gebruikt: {len(total_used)} ({len(total_used)/len(all_rules)*100:.1f}%)"
    )
    print(
        f"⚠️  Totaal ongebruikt: {len(unused_overall)} ({len(unused_overall)/len(all_rules)*100:.1f}%)"
    )

    if unused_overall:
        print(f"\n❌ ONGEBRUIKTE REGELS: {sorted(unused_overall)}")

    # Analyse per categorie verschillen
    print("\n📈 CATEGORIE VERSCHILLEN:")
    for category, data in results.items():
        gen_count = data["generation"]["count"]
        val_count = data["validation"]["count"]
        print(
            f"   {category.upper():<12}: Gen={gen_count:<2} Val={val_count:<2} Overlap={data['comparison']['overlap_percentage']:.0f}%"
        )


def analyze_critical_rules():
    """Specifieke analyse van kritieke regels."""

    print("\n🚨 KRITIEKE REGELS ANALYSE")
    print("=" * 30)

    rule_manager = get_toetsregel_manager()

    # Haal kritieke regels op
    kritieke_regels = rule_manager.get_kritieke_regels()
    verplichte_regels = rule_manager.get_verplichte_regels()

    print(f"🚨 Kritieke regels (verplicht + hoog): {len(kritieke_regels)}")
    kritieke_ids = [regel["id"] for regel in kritieke_regels]
    print(f"   IDs: {sorted(kritieke_ids)}")

    print(f"\n📋 Verplichte regels: {len(verplichte_regels)}")
    verplichte_ids = [regel["id"] for regel in verplichte_regels]
    print(f"   IDs: {sorted(verplichte_ids)}")

    # Check of alle kritieke regels gebruikt worden
    generator = DefinitieGenerator()
    validator = DefinitieValidator()

    context = GenerationContext(
        begrip="test",
        organisatorische_context="TEST",
        juridische_context="",
        categorie=OntologischeCategorie.TYPE,
    )

    gen_result = generator.generate(context)
    validator.validate("test definitie", OntologischeCategorie.TYPE)

    gen_used = [instr.rule_id for instr in gen_result.gebruikte_instructies]
    val_criteria = validator._load_validation_criteria(OntologischeCategorie.TYPE)
    val_used = [crit.rule_id for crit in val_criteria]

    print("\n✅ KRITIEKE REGELS IN GEBRUIK:")
    for rule_id in kritieke_ids:
        in_gen = "✅" if rule_id in gen_used else "❌"
        in_val = "✅" if rule_id in val_used else "❌"
        print(f"   {rule_id:<12}: Generatie {in_gen}  Validatie {in_val}")


def detailed_rule_analysis():
    """Gedetailleerde analyse van specifieke regels."""

    print("\n🔍 GEDETAILLEERDE REGEL ANALYSE")
    print("=" * 35)

    rule_manager = get_toetsregel_manager()
    generator = DefinitieGenerator()
    validator = DefinitieValidator()

    # Test specifieke belangrijke regels
    belangrijke_regels = [
        "CON-01",
        "CON-02",
        "ESS-01",
        "ESS-02",
        "ESS-05",
        "INT-03",
        "STR-01",
    ]

    for rule_id in belangrijke_regels:
        regel_data = rule_manager.load_regel(rule_id)
        if not regel_data:
            print(f"❌ {rule_id}: Niet gevonden")
            continue

        print(f"\n📋 {rule_id}: {regel_data.get('naam', 'Geen naam')[:60]}...")
        print(f"   Prioriteit: {regel_data.get('prioriteit', 'onbekend')}")
        print(f"   Aanbeveling: {regel_data.get('aanbeveling', 'onbekend')}")

        # Generatie interpretatie
        gen_interpreter = generator.interpreter
        gen_instruction = gen_interpreter.for_generation(regel_data)
        print(f"   🔧 Generatie: {gen_instruction.guidance[:80]}...")

        # Validatie interpretatie
        val_interpreter = validator.interpreter
        val_criterion = val_interpreter.for_validation(regel_data)
        print(
            f"   🔍 Validatie: {len(val_criterion.patterns_to_avoid)} patronen, {val_criterion.severity.value} severity"
        )


if __name__ == "__main__":
    # Voer complete analyse uit
    try:
        results = analyze_rule_usage()
        analyze_critical_rules()
        detailed_rule_analysis()

        print("\n✅ Analyse voltooid!")

    except Exception as e:
        print(f"❌ Fout tijdens analyse: {e}")
        import traceback

        traceback.print_exc()
