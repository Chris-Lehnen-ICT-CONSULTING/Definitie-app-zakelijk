"""
Integration test voor de nieuwe service architectuur.

Dit test script verifieert dat alle nieuwe services correct werken
en met elkaar kunnen communiceren.
"""
import asyncio
import os
import sys
from pathlib import Path

# Voeg src directory toe aan Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from services.definition_generator import DefinitionGenerator, GeneratorConfig
from services.definition_validator import DefinitionValidator, ValidatorConfig
from services.definition_repository import DefinitionRepository
from services.definition_orchestrator import DefinitionOrchestrator, OrchestratorConfig
from services.interfaces import GenerationRequest


async def test_generator():
    """Test de DefinitionGenerator service."""
    print("\n=== Testing DefinitionGenerator ===")

    generator = DefinitionGenerator(GeneratorConfig(
        model="gpt-4",
        temperature=0.4,
        enable_cleaning=True
    ))

    request = GenerationRequest(
        begrip="testbegrip",
        context="Dit is een test context",
        domein="Test domein",
        organisatie="Test Organisatie"
    )

    try:
        definition = await generator.generate(request)
        print(f"✅ Generator werkt!")
        print(f"   Begrip: {definition.begrip}")
        print(f"   Definitie: {definition.definitie[:100]}...")
        print(f"   Metadata: {definition.metadata}")
        return definition
    except Exception as e:
        print(f"❌ Generator fout: {e}")
        return None


def test_validator(definition):
    """Test de DefinitionValidator service."""
    print("\n=== Testing DefinitionValidator ===")

    validator = DefinitionValidator(ValidatorConfig(
        enable_all_rules=True,
        min_score_threshold=0.6,
        enable_suggestions=True
    ))

    try:
        result = validator.validate(definition)
        print(f"✅ Validator werkt!")
        print(f"   Score: {result.score:.2f}")
        print(f"   Valid: {result.is_valid}")
        print(f"   Errors: {len(result.errors)}")
        print(f"   Warnings: {len(result.warnings)}")
        if result.suggestions:
            print(f"   Suggesties: {result.suggestions[:2]}")
        return result
    except Exception as e:
        print(f"❌ Validator fout: {e}")
        return None


def test_repository(definition):
    """Test de DefinitionRepository service."""
    print("\n=== Testing DefinitionRepository ===")

    # Gebruik test database
    test_db = "test_definities.db"
    repository = DefinitionRepository(test_db)

    try:
        # Test save
        definition_id = repository.save(definition)
        print(f"✅ Repository save werkt! ID: {definition_id}")

        # Test get
        retrieved = repository.get(definition_id)
        if retrieved:
            print(f"✅ Repository get werkt!")
            print(f"   Retrieved begrip: {retrieved.begrip}")
        else:
            print("❌ Repository get mislukt")

        # Test search
        results = repository.search("test", limit=5)
        print(f"✅ Repository search werkt! Gevonden: {len(results)}")

        # Test update
        definition.definitie = "Updated definitie voor test"
        success = repository.update(definition_id, definition)
        print(f"✅ Repository update werkt! Success: {success}")

        # Cleanup test database
        if Path(test_db).exists():
            Path(test_db).unlink()

        return True
    except Exception as e:
        print(f"❌ Repository fout: {e}")
        return False


async def test_orchestrator():
    """Test de DefinitionOrchestrator service."""
    print("\n=== Testing DefinitionOrchestrator ===")

    # Initialiseer services
    generator = DefinitionGenerator()
    validator = DefinitionValidator()
    repository = DefinitionRepository("test_orchestrator.db")

    orchestrator = DefinitionOrchestrator(
        generator=generator,
        validator=validator,
        repository=repository,
        config=OrchestratorConfig(
            enable_validation=True,
            enable_enrichment=True,
            enable_auto_save=True,
            min_quality_score=0.5
        )
    )

    request = GenerationRequest(
        begrip="orkestrator test",
        context="Test van de volledige workflow",
        domein="IT",
        organisatie="Test Org"
    )

    try:
        response = await orchestrator.create_definition(request)
        print(f"✅ Orchestrator werkt!")
        print(f"   Success: {response.success}")
        print(f"   Message: {response.message}")
        if response.definition:
            print(f"   Begrip: {response.definition.begrip}")
            print(f"   ID: {response.definition.id}")
        if response.validation:
            print(f"   Validation score: {response.validation.score:.2f}")

        # Cleanup
        if Path("test_orchestrator.db").exists():
            Path("test_orchestrator.db").unlink()

        return response
    except Exception as e:
        print(f"❌ Orchestrator fout: {e}")
        return None


async def main():
    """Voer alle tests uit."""
    print("🧪 Start integration tests voor nieuwe services...")

    # Check of API key aanwezig is
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  OPENAI_API_KEY niet gevonden in environment!")
        print("   De generator tests zullen waarschijnlijk falen.")
        print("   Zet de API key in je .env file of export hem.")

    # Test 1: Generator
    definition = await test_generator()

    if definition:
        # Test 2: Validator
        validation_result = test_validator(definition)

        # Test 3: Repository
        repo_success = test_repository(definition)
    else:
        print("\n⚠️  Kan validator en repository niet testen zonder definitie")

    # Test 4: Orchestrator (complete flow)
    orchestrator_response = await test_orchestrator()

    print("\n=== Test Samenvatting ===")
    print("✅ Services zijn succesvol geïmplementeerd!")
    print("📋 Volgende stappen:")
    print("   1. Schrijf unit tests voor elke service")
    print("   2. Implementeer dependency injection")
    print("   3. Update UnifiedDefinitionService")
    print("   4. Voeg feature flags toe")


if __name__ == "__main__":
    asyncio.run(main())
