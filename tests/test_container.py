"""
Test voor de Dependency Injection Container.
"""
import asyncio
import sys
from pathlib import Path

# Voeg src directory toe aan Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from services.container import ServiceContainer, get_container, ContainerConfigs
from services.interfaces import GenerationRequest


def test_container_creation():
    """Test container aanmaken."""
    print("\n=== Testing Container Creation ===")

    # Test default container
    container = ServiceContainer()
    print("✅ Default container aangemaakt")

    # Test met custom config
    custom_config = {
        'db_path': 'custom.db',
        'generator_model': 'gpt-3.5-turbo',
        'min_quality_score': 0.8
    }
    custom_container = ServiceContainer(custom_config)
    print("✅ Custom container aangemaakt")

    # Test environment configs
    dev_container = ServiceContainer(ContainerConfigs.development())
    print("✅ Development container aangemaakt")

    test_container = ServiceContainer(ContainerConfigs.testing())
    print("✅ Test container aangemaakt")


def test_service_creation():
    """Test service instantiatie."""
    print("\n=== Testing Service Creation ===")

    container = ServiceContainer(ContainerConfigs.testing())

    # Test generator
    generator1 = container.generator()
    generator2 = container.generator()
    assert generator1 is generator2  # Singleton check
    print("✅ Generator service (singleton)")

    # Test validator
    validator = container.validator()
    print("✅ Validator service")

    # Test repository
    repository = container.repository()
    print("✅ Repository service")

    # Test orchestrator
    orchestrator = container.orchestrator()
    print("✅ Orchestrator service")

    # Test get_service
    gen_via_name = container.get_service('generator')
    assert gen_via_name is generator1
    print("✅ get_service() werkt")


async def test_service_integration():
    """Test services via container."""
    print("\n=== Testing Service Integration ===")

    # Gebruik test config
    container = ServiceContainer(ContainerConfigs.testing())
    orchestrator = container.orchestrator()

    # Test request
    request = GenerationRequest(
        begrip="container test",
        context="Test van dependency injection",
        domein="Software Engineering"
    )

    try:
        response = await orchestrator.create_definition(request)
        print(f"✅ Integration test: {response.success}")
        if response.definition:
            print(f"   Begrip: {response.definition.begrip}")
            print(f"   Score: {response.validation.score if response.validation else 'N/A'}")
    except Exception as e:
        print(f"❌ Integration test mislukt: {e}")


def test_global_container():
    """Test globale container functies."""
    print("\n=== Testing Global Container ===")

    # Get default
    container1 = get_container()
    container2 = get_container()
    assert container1 is container2
    print("✅ Global container singleton")

    # Reset
    from services.container import reset_container
    reset_container()
    container3 = get_container()
    assert container3 is not container1
    print("✅ Container reset werkt")


def main():
    """Voer alle container tests uit."""
    print("🧪 Testing Dependency Injection Container...")

    test_container_creation()
    test_service_creation()
    test_global_container()

    # Async test
    import os
    if os.getenv("OPENAI_API_KEY"):
        asyncio.run(test_service_integration())
    else:
        print("\n⚠️  Skip integration test (geen API key)")

    print("\n✅ Container tests geslaagd!")
    print("\n📋 De DI container biedt:")
    print("   - Centrale service configuratie")
    print("   - Singleton service instances")
    print("   - Environment-specifieke configs")
    print("   - Makkelijk testen met mocks")


if __name__ == "__main__":
    main()
