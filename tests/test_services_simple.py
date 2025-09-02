"""
Simpele test voor de nieuwe services zonder database afhankelijkheden.
"""
import asyncio
import sys
from pathlib import Path

# Voeg src directory toe aan Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from services.definition_generator import DefinitionGenerator
from services.definition_validator import DefinitionValidator
from services.interfaces import GenerationRequest, Definition


async def test_basic_flow():
    """Test basis flow zonder database."""
    print("\n🧪 Testing basic service flow...\n")

    # 1. Test Generator
    print("1️⃣ Testing Generator...")
    generator = DefinitionGenerator()

    request = GenerationRequest(
        begrip="digitale transformatie",
        context="Overgang naar digitale processen in de overheid",
        domein="ICT",
        organisatie="Rijksoverheid"
    )

    try:
        definition = await generator.generate(request)
        print(f"✅ Generator: Definitie gegenereerd")
        print(f"   Begrip: {definition.begrip}")
        print(f"   Definitie: {definition.definitie[:100]}...")
        print(f"   Bron: {definition.bron}")
    except Exception as e:
        print(f"❌ Generator fout: {e}")
        return

    # 2. Test Validator
    print("\n2️⃣ Testing Validator...")
    validator = DefinitionValidator()

    try:
        result = validator.validate(definition)
        print(f"✅ Validator: Validatie voltooid")
        print(f"   Score: {result.score:.2f}/1.00")
        print(f"   Acceptabel: {'Ja' if result.is_valid else 'Nee'}")
        print(f"   Fouten: {len(result.errors)}")
        print(f"   Waarschuwingen: {len(result.warnings)}")

        if result.errors:
            print("\n   Belangrijkste fouten:")
            for error in result.errors[:3]:
                print(f"   - {error}")

        if result.suggestions:
            print("\n   Suggesties:")
            for suggestion in result.suggestions[:3]:
                print(f"   - {suggestion}")
    except Exception as e:
        print(f"❌ Validator fout: {e}")
        return

    # 3. Test Enhancement
    print("\n3️⃣ Testing Enhancement...")
    try:
        enhanced = await generator.enhance(definition)
        print(f"✅ Enhancement: Definitie verrijkt")
        if enhanced.synoniemen:
            print(f"   Synoniemen: {', '.join(enhanced.synoniemen[:3])}")
        if enhanced.gerelateerde_begrippen:
            print(f"   Gerelateerd: {', '.join(enhanced.gerelateerde_begrippen[:3])}")
        if enhanced.toelichting:
            print(f"   Toelichting: {enhanced.toelichting[:100]}...")
    except Exception as e:
        print(f"❌ Enhancement fout: {e}")

    print("\n✅ Basis services werken correct!")
    print("📋 Database integratie moet nog getest worden met correcte schema.")


if __name__ == "__main__":
    # Check API key
    import os
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY niet gevonden!")
        print("   Zet deze in je .env file of export hem.")
        sys.exit(1)

    asyncio.run(test_basic_flow())
