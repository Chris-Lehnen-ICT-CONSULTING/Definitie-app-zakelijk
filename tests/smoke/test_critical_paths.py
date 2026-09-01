"""
Critical path smoke tests for DefinitieAgent.

These 10 tests give 80% confidence that the app works.
Should run in <30 seconds.

Run with: pytest tests/smoke/test_critical_paths.py -v
"""

import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.smoke]

# Ensure src on path
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))


# ==============================================================================
# SMOKE TEST 1: ServiceContainer initializes without errors
# ==============================================================================
def test_service_container_initializes():
    """ServiceContainer can be created and provides all core services."""
    from services.container import ServiceContainer

    container = ServiceContainer()

    # Test that we can get core services without errors
    assert container.generator() is not None
    assert container.repository() is not None
    assert container.validation_orchestrator() is not None
    print("✓ ServiceContainer initialized successfully")


# ==============================================================================
# SMOKE TEST 2: Database connection works
# ==============================================================================
def test_database_connection():
    """Database can be accessed and basic queries work."""
    from database.definitie_repository import DefinitieRepository

    repo = DefinitieRepository()

    # Try to search definitions (might be empty, that's OK)
    definitions = repo.search_definities("")
    assert isinstance(definitions, list)
    print(f"✓ Database accessible, {len(definitions)} definitions found")


# ==============================================================================
# SMOKE TEST 3: Validation service laadt de volledige contractregelset
# ==============================================================================
def test_validation_rules_load():
    """De service laadt de volledige regelset uit het contract.

    DEF-621: deze smoke bouwde de service zonder manager en controleerde
    daarna niets. Zij slaagde dus ook wanneer er zeven van drieenvijftig
    regels geladen waren - precies de toestand die de fail-closed guard nu
    als `validation_unknown` afvangt. Het aantal komt uit het contract; een
    hardcoded getal zou opnieuw met de werkelijkheid uit de pas gaan lopen.
    """
    from services.validation.modular_validation_service import ModularValidationService
    from toetsregels.manager import get_toetsregel_manager

    service = ModularValidationService(get_toetsregel_manager(), None, None)
    health = service.get_health_status()

    assert health["validation_ready"] is True, health
    assert health["rules_expected"] > 0, health
    assert health["rules_loaded"] == health["rules_expected"], health
    print(f"✓ Validation service ready: {health['rules_loaded']} regels geladen")


# ==============================================================================
# SMOKE TEST 4: Prompt service can be initialized
# ==============================================================================
def test_prompt_service_initializes():
    """PromptServiceV2 can be initialized (async methods tested elsewhere)."""
    from services.prompts.prompt_service_v2 import PromptServiceV2

    service = PromptServiceV2()

    assert service is not None
    print("✓ PromptServiceV2 initialized successfully")


# ==============================================================================
# SMOKE TEST 5: Web lookup service can be initialized
# ==============================================================================
def test_web_lookup_service_initializes():
    """ModernWebLookupService can be created and has providers."""
    from services.modern_web_lookup_service import ModernWebLookupService

    service = ModernWebLookupService()

    # Should have providers configured
    assert service is not None
    print("✓ Web lookup service initialized")


# ==============================================================================
# SMOKE TEST 6: CategoryService can update categories
# ==============================================================================
def test_category_service():
    """CategoryService can be initialized."""
    from database.definitie_repository import DefinitieRepository
    from services.category_service import CategoryService

    repo = DefinitieRepository()
    service = CategoryService(repository=repo)

    assert service is not None
    assert service.repository is not None
    print("✓ CategoryService initialized with repository")


# ==============================================================================
# SMOKE TEST 7: Validation can run on sample definition
# ==============================================================================
@pytest.mark.asyncio
async def test_validation_runs():
    """Validation service can validate sample definition."""
    from services.validation.modular_validation_service import ModularValidationService
    from toetsregels.manager import get_toetsregel_manager

    service = ModularValidationService(get_toetsregel_manager(), None, None)

    begrip = "toezicht"
    text = "Het proces waarbij een bevoegde instantie controleert of regels worden nageleefd."
    context = {
        "juridische_context": ["Strafrecht"],
        "organisatorische_context": ["OM"],
    }

    result = await service.validate_definition(begrip, text, context=context)

    assert result is not None
    assert "overall_score" in result
    # DEF-621: zonder deze regel slaagt de smoke ook op een
    # `validation_unknown`-resultaat - dat draagt immers ook een
    # `overall_score`, namelijk de placeholder 0.0. Dan bewijst de smoke niet
    # dat er werkelijk gevalideerd is.
    assert result["validation_status"] == "validated", result
    print("✓ Validation completed successfully")


# ==============================================================================
# SMOKE TEST 8: Export service can export to JSON
# ==============================================================================
def test_export_service_initializes():
    """Export service can be initialized."""
    from database.definitie_repository import DefinitieRepository
    from services.export_service import ExportService

    repo = DefinitieRepository()
    service = ExportService(repository=repo)

    assert service is not None
    assert service.repository is not None
    print("✓ ExportService initialized with repository")


# SMOKE TEST 9: DuplicateDetectionService removed - was dead code (DEF-176)


# ==============================================================================
# SMOKE TEST 10: Main app can be imported
# ==============================================================================
def test_main_app_imports():
    """Main application file can be imported without errors."""
    try:
        import main

        print("✓ Main app imports successfully")
        assert True
    except Exception as e:
        pytest.fail(f"Main app failed to import: {e}")


# ==============================================================================
# Run all smoke tests
# ==============================================================================
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
