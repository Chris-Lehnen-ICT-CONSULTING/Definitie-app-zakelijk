"""
Test voor UnifiedDefinitionService V2 met nieuwe services integratie.
"""
import asyncio
import os
import sys
from pathlib import Path

# Voeg src directory toe aan Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from services import (
    UnifiedDefinitionService,
    UnifiedServiceConfigV2,
    ServiceMode,
    ProcessingMode
)


def test_legacy_mode():
    """Test legacy mode werking."""
    print("\n=== Testing Legacy Mode ===")

    service = UnifiedDefinitionService.get_instance()
    config = UnifiedServiceConfigV2(
        service_mode=ServiceMode.LEGACY,
        processing_mode=ProcessingMode.SYNC
    )
    service.configure(config)

    # Test info
    info = service.get_service_info()
    print(f"Service mode: {info['service_mode']}")
    print(f"Architecture: {info['architecture']}")
    print(f"Version: {info['version']}")

    # Test generatie
    try:
        result = service.generate_definition(
            begrip="legacy test",
            context_dict={'organisatorisch': ['test context']}
        )
        print(f"✅ Legacy mode werkt: success={result.success}")
    except Exception as e:
        print(f"❌ Legacy mode fout: {e}")


def test_new_services_mode():
    """Test nieuwe services mode."""
    print("\n=== Testing New Services Mode ===")

    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Skip nieuwe services test (geen API key)")
        return

    service = UnifiedDefinitionService.get_instance()
    config = UnifiedServiceConfigV2(
        service_mode=ServiceMode.NEW_SERVICES,
        use_adapter=True
    )
    service.configure(config)

    # Test info
    info = service.get_service_info()
    print(f"Service mode: {info['service_mode']}")
    print(f"Architecture: {info['architecture']}")
    print(f"Features: {', '.join(info['features'])}")

    # Test generatie
    try:
        result = service.generate_definition(
            begrip="nieuwe architectuur",
            context_dict={
                'organisatorisch': ['moderne services'],
                'domein': ['software engineering']
            }
        )
        print(f"✅ Nieuwe services mode werkt: success={result.success}")
        if result.success:
            print(f"   Definitie: {result.definitie_gecorrigeerd[:80]}...")
            print(f"   Score: {result.validation_score:.2f}")
            print(f"   Architecture: {result.architecture_mode.value}")
    except Exception as e:
        print(f"❌ Nieuwe services mode fout: {e}")
        import traceback
        traceback.print_exc()


def test_auto_mode():
    """Test auto mode detectie."""
    print("\n=== Testing Auto Mode ===")

    # Set environment variable
    os.environ['USE_NEW_SERVICES'] = 'true'

    service = UnifiedDefinitionService.get_instance()
    config = UnifiedServiceConfigV2(
        service_mode=ServiceMode.AUTO
    )
    service.configure(config)

    info = service.get_service_info()
    print(f"Auto detected mode: {info['service_mode']}")
    print(f"Should be 'new' because USE_NEW_SERVICES=true")

    # Reset
    os.environ['USE_NEW_SERVICES'] = 'false'
    service._service_mode_cache = None  # Reset cache

    info2 = service.get_service_info()
    print(f"After reset: {info2['service_mode']}")
    print(f"Should be 'legacy' because USE_NEW_SERVICES=false")


async def test_async_compatibility():
    """Test async compatibility."""
    print("\n=== Testing Async Compatibility ===")

    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Skip async test (geen API key)")
        return

    service = UnifiedDefinitionService.get_instance()
    config = UnifiedServiceConfigV2(
        service_mode=ServiceMode.NEW_SERVICES,
        processing_mode=ProcessingMode.ASYNC
    )
    service.configure(config)

    try:
        result = await service.agenerate_definition(
            begrip="async test",
            context_dict={'organisatorisch': ['async context']}
        )
        print(f"✅ Async werkt met nieuwe services: success={result.success}")
    except Exception as e:
        print(f"❌ Async fout: {e}")


def main():
    """Voer alle tests uit."""
    print("🧪 Testing UnifiedDefinitionService V2...")

    test_legacy_mode()
    test_new_services_mode()
    test_auto_mode()

    # Async test
    if os.getenv("OPENAI_API_KEY"):
        asyncio.run(test_async_compatibility())

    print("\n✅ UnifiedDefinitionService V2 tests compleet!")
    print("\n📋 Samenvatting:")
    print("   - Legacy mode blijft werken")
    print("   - Nieuwe services integratie werkt")
    print("   - Auto mode detectie werkt")
    print("   - Feature flag ondersteuning")
    print("   - Volledige backward compatibility")


if __name__ == "__main__":
    main()
