"""
Integration test for synonym system wiring in ServiceContainer.

Tests that:
1. All synonym services can be initialized via ServiceContainer
2. Dependencies are properly wired
3. Cache invalidation callbacks are registered
4. Singleton pattern works correctly
"""

import pytest

from src.services.container import ServiceContainer


class TestSynonymContainerIntegration:
    """Test synonym system integration with ServiceContainer."""

    @pytest.fixture()
    def container(self):
        """Create a test container with in-memory database."""
        config = {
            "db_path": ":memory:",
            "use_json_rules": False,  # Skip validation rules for faster tests
        }
        return ServiceContainer(config)

    def test_synonym_registry_initialization(self, container):
        """Test that synonym_registry can be initialized."""
        registry = container.synonym_registry()

        assert registry is not None
        assert hasattr(registry, "get_synonyms")
        assert hasattr(registry, "register_invalidation_callback")

        # Test singleton pattern
        registry2 = container.synonym_registry()
        assert registry is registry2

    def test_gpt4_synonym_suggester_initialization(self, container):
        """Test that gpt4_synonym_suggester can be initialized."""
        suggester = container.gpt4_synonym_suggester()

        # Placeholder mode - should still initialize
        assert suggester is not None
        assert hasattr(suggester, "suggest_synonyms")

        # Test singleton pattern
        suggester2 = container.gpt4_synonym_suggester()
        assert suggester is suggester2

    def test_synonym_orchestrator_initialization(self, container):
        """Test that synonym_orchestrator can be initialized with dependencies."""
        orchestrator = container.synonym_orchestrator()

        assert orchestrator is not None
        assert hasattr(orchestrator, "get_synonyms_for_lookup")
        assert hasattr(orchestrator, "ensure_synonyms")
        assert hasattr(orchestrator, "invalidate_cache")
        assert hasattr(orchestrator, "get_cache_stats")

        # Verify dependencies are wired
        assert orchestrator.registry is not None
        assert orchestrator.gpt4_suggester is not None

        # Test singleton pattern
        orchestrator2 = container.synonym_orchestrator()
        assert orchestrator is orchestrator2

    def test_synonym_service_initialization(self, container):
        """Test that synonym_service (façade) can be initialized."""
        service = container.synonym_service()

        assert service is not None
        assert hasattr(service, "get_synoniemen")
        assert hasattr(service, "get_synonyms_with_weights")
        assert hasattr(service, "expand_query_terms")
        assert hasattr(service, "has_synoniemen")

        # Verify orchestrator dependency is wired
        assert service.orchestrator is not None

        # Test singleton pattern
        service2 = container.synonym_service()
        assert service is service2

    def test_cache_invalidation_callback_wiring(self, container):
        """Test that cache invalidation callbacks are properly wired."""
        # Get both registry and orchestrator
        registry = container.synonym_registry()
        orchestrator = container.synonym_orchestrator()

        # Verify callback is registered
        assert len(registry._invalidation_callbacks) > 0

        # Verify the callback is orchestrator's invalidate_cache method
        callback = registry._invalidation_callbacks[0]
        assert callback == orchestrator.invalidate_cache

    def test_get_service_method(self, container):
        """Test that all synonym services are accessible via get_service()."""
        # Test each service via get_service
        registry = container.get_service("synonym_registry")
        assert registry is not None

        suggester = container.get_service("gpt4_synonym_suggester")
        assert suggester is not None

        orchestrator = container.get_service("synonym_orchestrator")
        assert orchestrator is not None

        service = container.get_service("synonym_service")
        assert service is not None

    def test_service_dependency_chain(self, container):
        """Test that the entire dependency chain is properly wired."""
        # Start from the top-level façade
        service = container.synonym_service()

        # Follow the dependency chain
        orchestrator = service.orchestrator
        assert orchestrator is not None

        registry = orchestrator.registry
        assert registry is not None

        gpt4_suggester = orchestrator.gpt4_suggester
        assert gpt4_suggester is not None

        # Verify they match the singleton instances
        assert orchestrator is container.synonym_orchestrator()
        assert registry is container.synonym_registry()
        assert gpt4_suggester is container.gpt4_synonym_suggester()

    def test_orchestrator_cache_stats(self, container):
        """Test that orchestrator exposes cache statistics."""
        orchestrator = container.synonym_orchestrator()

        stats = orchestrator.get_cache_stats()

        # Verify stats structure
        assert "size" in stats
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats
        assert "max_size" in stats
        assert "ttl_seconds" in stats

        # Initial stats should be empty
        assert stats["size"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0.0

    def test_container_reset(self, container):
        """Test that container reset clears synonym services."""
        # Initialize all services
        container.synonym_registry()
        container.gpt4_synonym_suggester()
        container.synonym_orchestrator()
        service = container.synonym_service()

        # Verify they're cached
        assert "synonym_registry" in container._instances
        assert "gpt4_synonym_suggester" in container._instances
        assert "synonym_orchestrator" in container._instances
        assert "synonym_service" in container._instances

        # Reset container
        container.reset()

        # Verify instances are cleared
        assert "synonym_registry" not in container._instances
        assert "gpt4_synonym_suggester" not in container._instances
        assert "synonym_orchestrator" not in container._instances
        assert "synonym_service" not in container._instances

        # Verify we can re-initialize
        new_service = container.synonym_service()
        assert new_service is not None
        assert new_service is not service  # Different instance after reset

    def test_definition_orchestrator_has_synonym_orchestrator(self, container):
        """Test that DefinitionOrchestratorV2 has synonym_orchestrator injected (PHASE 3.1)."""
        # Get the definition orchestrator
        orchestrator = container.orchestrator()

        assert orchestrator is not None
        assert hasattr(orchestrator, "synonym_orchestrator")
        assert orchestrator.synonym_orchestrator is not None

        # Verify it's the same instance as from container
        synonym_orch = container.synonym_orchestrator()
        assert orchestrator.synonym_orchestrator is synonym_orch

        # Verify it has the expected methods
        assert hasattr(orchestrator.synonym_orchestrator, "ensure_synonyms")
        assert hasattr(orchestrator.synonym_orchestrator, "get_synonyms_for_lookup")
