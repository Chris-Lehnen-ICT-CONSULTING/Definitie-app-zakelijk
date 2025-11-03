"""
DEF-90: Tests for ValidationOrchestratorV2 lazy loading optimization.

Tests verify that ValidationOrchestratorV2 is NOT initialized until first use,
reducing ServiceContainer initialization from 616ms to 271ms (-345ms, 56%).
"""

import time
from unittest.mock import Mock, patch

import pytest

# DEF-90 Performance targets
MAX_ORCHESTRATOR_INIT_WITH_VALIDATION_MS = 400  # With both lazy loads
MAX_VALIDATION_LOAD_TIME_MS = 500  # Validation creation time


class TestValidationServiceLazyLoading:
    """Test that ValidationOrchestratorV2 is lazy-loaded in DefinitionOrchestratorV2."""

    def test_orchestrator_init_does_not_create_validation_service(self):
        """
        CRITICAL: Orchestrator __init__ should NOT create ValidationOrchestratorV2.

        This is the core of DEF-90 fix - defer expensive validation initialization.
        """
        from services.orchestrators.definition_orchestrator_v2 import (
            DefinitionOrchestratorV2,
        )

        # Mock all required dependencies
        ai_service = Mock()
        cleaning_service = Mock()
        repository = Mock()

        # Track if ValidationOrchestratorV2 was instantiated
        with patch(
            "services.orchestrators.validation_orchestrator_v2.ValidationOrchestratorV2"
        ) as mock_validation_class:
            # Create orchestrator WITHOUT passing validation_service
            orchestrator = DefinitionOrchestratorV2(
                prompt_service=None,  # DEF-66 lazy
                ai_service=ai_service,
                validation_service=None,  # DEF-90 lazy (key test)
                cleaning_service=cleaning_service,
                repository=repository,
            )

            # Verify ValidationOrchestratorV2 was NOT instantiated during __init__
            mock_validation_class.assert_not_called()
            assert orchestrator is not None

    def test_validation_service_created_on_first_use(self):
        """
        ValidationOrchestratorV2 should be created only when first needed.
        """
        from services.orchestrators.definition_orchestrator_v2 import (
            DefinitionOrchestratorV2,
        )

        # Mock all required dependencies
        ai_service = Mock()
        cleaning_service = Mock()
        repository = Mock()

        # Create orchestrator with lazy validation service
        orchestrator = DefinitionOrchestratorV2(
            prompt_service=None,
            ai_service=ai_service,
            validation_service=None,  # DEF-90: Trigger lazy loading
            cleaning_service=cleaning_service,
            repository=repository,
        )

        # Mock ValidationOrchestratorV2 to track instantiation
        with patch(
            "services.orchestrators.validation_orchestrator_v2.ValidationOrchestratorV2"
        ) as mock_validation_class:
            mock_validation_instance = Mock()
            mock_validation_class.return_value = mock_validation_instance

            # Access validation_service property (should trigger creation)
            _ = orchestrator.validation_service

            # Verify ValidationOrchestratorV2 was instantiated on first access
            mock_validation_class.assert_called_once()

    def test_validation_service_cached_after_first_access(self):
        """
        ValidationOrchestratorV2 should be created once and cached.
        """
        from services.orchestrators.definition_orchestrator_v2 import (
            DefinitionOrchestratorV2,
        )

        # Mock all required dependencies
        ai_service = Mock()
        cleaning_service = Mock()
        repository = Mock()

        orchestrator = DefinitionOrchestratorV2(
            prompt_service=None,
            ai_service=ai_service,
            validation_service=None,
            cleaning_service=cleaning_service,
            repository=repository,
        )

        with patch(
            "services.orchestrators.validation_orchestrator_v2.ValidationOrchestratorV2"
        ) as mock_validation_class:
            mock_validation_instance = Mock()
            mock_validation_class.return_value = mock_validation_instance

            # Access multiple times
            service1 = orchestrator.validation_service
            service2 = orchestrator.validation_service
            service3 = orchestrator.validation_service

            # Verify ValidationOrchestratorV2 was instantiated only ONCE
            mock_validation_class.assert_called_once()

            # Verify same instance returned
            assert service1 is service2
            assert service2 is service3

    def test_validation_service_none_before_access(self):
        """
        Internal _validation_service should be None before first access.
        """
        from services.orchestrators.definition_orchestrator_v2 import (
            DefinitionOrchestratorV2,
        )

        orchestrator = DefinitionOrchestratorV2(
            prompt_service=None,
            ai_service=Mock(),
            validation_service=None,
            cleaning_service=Mock(),
            repository=Mock(),
        )

        # Verify internal state is None (lazy not triggered)
        assert orchestrator._validation_service is None


class TestCombinedLazyLoading:
    """Test combined DEF-66 + DEF-90 lazy loading."""

    def test_both_prompt_and_validation_lazy_loaded(self):
        """
        Both PromptServiceV2 and ValidationOrchestratorV2 should be lazy-loaded.
        """
        from services.orchestrators.definition_orchestrator_v2 import (
            DefinitionOrchestratorV2,
        )

        orchestrator = DefinitionOrchestratorV2(
            prompt_service=None,  # DEF-66 lazy
            ai_service=Mock(),
            validation_service=None,  # DEF-90 lazy
            cleaning_service=Mock(),
            repository=Mock(),
        )

        # Verify both are None before access
        assert orchestrator._prompt_service is None
        assert orchestrator._validation_service is None

        # Access both
        _ = orchestrator.prompt_service
        _ = orchestrator.validation_service

        # Verify both are now loaded
        assert orchestrator._prompt_service is not None
        assert orchestrator._validation_service is not None

    def test_orchestrator_init_fast_with_both_lazy(self):
        """
        Orchestrator initialization should be fast with both services lazy.

        Target: <100ms for orchestrator creation (without heavy services).
        """
        from services.orchestrators.definition_orchestrator_v2 import (
            DefinitionOrchestratorV2,
        )

        start = time.perf_counter()
        orchestrator = DefinitionOrchestratorV2(
            prompt_service=None,  # DEF-66 lazy
            ai_service=Mock(),
            validation_service=None,  # DEF-90 lazy
            cleaning_service=Mock(),
            repository=Mock(),
        )
        duration_ms = (time.perf_counter() - start) * 1000

        # Should be very fast without loading heavy services
        assert duration_ms < 100, (
            f"Orchestrator init took {duration_ms:.1f}ms (expected <100ms). "
            f"Lazy loading may not be working."
        )

        assert orchestrator is not None


class TestBackwardsCompatibilityValidation:
    """Ensure lazy loading doesn't break existing code."""

    def test_orchestrator_with_explicit_validation_service_still_works(self):
        """
        Existing code that passes validation_service explicitly should still work.

        Backwards compatibility requirement.
        """
        from services.orchestrators.definition_orchestrator_v2 import (
            DefinitionOrchestratorV2,
        )

        # Mock all dependencies
        validation_service = Mock()
        ai_service = Mock()
        cleaning_service = Mock()
        repository = Mock()

        # Old way: passing validation_service explicitly
        orchestrator = DefinitionOrchestratorV2(
            prompt_service=None,
            ai_service=ai_service,
            validation_service=validation_service,  # Explicit (old way)
            cleaning_service=cleaning_service,
            repository=repository,
        )

        # Verify orchestrator was created
        assert orchestrator is not None

        # Verify validation_service is available
        assert orchestrator.validation_service is validation_service


class TestServiceContainerIntegration:
    """Test ServiceContainer integration with DEF-90 lazy loading."""

    def test_container_orchestrator_has_lazy_validation(self):
        """
        ServiceContainer should create orchestrator with lazy validation.
        """
        from utils.container_manager import get_cached_container

        # Clear cache
        get_cached_container.cache_clear()

        # Create container and orchestrator
        container = get_cached_container()
        orchestrator = container.orchestrator()

        # Verify validation is lazy (None before first access)
        assert orchestrator._validation_service is None

        # Access validation (trigger lazy load)
        validation = orchestrator.validation_service

        # Verify now loaded
        assert validation is not None
        assert orchestrator._validation_service is not None

    def test_container_validation_orchestrator_method(self):
        """
        Container.validation_orchestrator() should return same instance as orchestrator.validation_service.
        """
        from utils.container_manager import get_cached_container

        get_cached_container.cache_clear()

        container = get_cached_container()
        orchestrator = container.orchestrator()

        # Access via orchestrator property
        validation_from_orch = orchestrator.validation_service

        # Access via container method
        validation_from_container = container.validation_orchestrator()

        # Should be same instance
        assert validation_from_orch is validation_from_container


class TestPerformanceRegressionValidation:
    """Performance regression tests for DEF-90."""

    def test_orchestrator_init_under_400ms_with_both_lazy(self):
        """
        Orchestrator initialization should be <400ms with DEF-66 + DEF-90 optimizations.

        This tests the combined effect of both lazy loading optimizations.
        """
        from utils.container_manager import get_cached_container

        # Clear cache
        get_cached_container.cache_clear()

        # Measure orchestrator creation time
        container = get_cached_container()

        start = time.perf_counter()
        orchestrator = container.orchestrator()
        duration_ms = (time.perf_counter() - start) * 1000

        # DEF-66 + DEF-90 target: significant improvement
        assert duration_ms < MAX_ORCHESTRATOR_INIT_WITH_VALIDATION_MS, (
            f"Orchestrator creation took {duration_ms:.1f}ms "
            f"(expected <{MAX_ORCHESTRATOR_INIT_WITH_VALIDATION_MS}ms with DEF-66 + DEF-90). "
            f"Lazy loading optimizations may not be effective."
        )

        assert orchestrator is not None
