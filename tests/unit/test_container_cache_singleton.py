"""
Unit tests for ServiceContainer singleton cache behavior.

Deze tests verifiëren dat get_cached_container() correct werkt als singleton,
zonder dubbele initialisatie door cache key verschillen.

US-202: Fix cache key duplication problem
Root cause: lru_cache behandelt func() en func(None) als verschillende cache keys.
Fix: Verwijder alle parameters van get_cached_container().
"""

import logging
from unittest.mock import patch

import pytest

from utils.container_manager import (
    clear_container_cache,
    get_cached_container,
    get_container_stats,
)


class TestContainerCacheSingleton:
    """Tests voor singleton cache behavior van ServiceContainer."""

    def setup_method(self):
        """Setup voor elke test - clear de cache."""
        clear_container_cache()

    def teardown_method(self):
        """Cleanup na elke test - clear de cache."""
        clear_container_cache()

    def test_container_singleton_same_instance(self):
        """Verify get_cached_container returns exact same instance."""
        # Arrange & Act
        container1 = get_cached_container()
        container2 = get_cached_container()
        container3 = get_cached_container()

        # Assert - Exact same object in memory
        assert (
            container1 is container2
        ), "Container 1 en 2 moeten dezelfde instance zijn"
        assert (
            container2 is container3
        ), "Container 2 en 3 moeten dezelfde instance zijn"
        assert id(container1) == id(container2), "Container IDs moeten identiek zijn"
        assert id(container2) == id(container3), "Container IDs moeten identiek zijn"

    def test_container_cache_hit_rate(self):
        """Verify cache statistics show proper hit/miss ratio."""
        # Arrange
        clear_container_cache()

        # Act - First call misses, rest hit
        get_cached_container()  # miss
        get_cached_container()  # hit
        get_cached_container()  # hit
        get_cached_container()  # hit

        # Assert
        cache_info = get_cached_container.cache_info()
        assert cache_info.misses == 1, "Moet exact 1 cache miss hebben (eerste call)"
        assert cache_info.hits == 3, "Moet exact 3 cache hits hebben"
        assert cache_info.currsize == 1, "Moet exact 1 item in cache hebben"
        assert cache_info.maxsize == 1, "Cache maxsize moet 1 zijn"

    def test_container_initialized_once(self, caplog):
        """Verify container initialization log appears only once."""
        # Arrange
        caplog.set_level(logging.INFO)
        clear_container_cache()

        # Act - Multiple calls
        get_cached_container()
        get_cached_container()
        get_cached_container()

        # Assert - Only one initialization log
        init_logs = [
            record
            for record in caplog.records
            if "Initialiseer ServiceContainer" in record.message
        ]
        assert len(init_logs) == 1, "Container mag maar 1x geïnitialiseerd worden"

    def test_clear_cache_forces_reinit(self):
        """Verify clearing cache forces new initialization."""
        # Arrange
        container1 = get_cached_container()
        first_id = id(container1)

        # Act - Clear and get new
        clear_container_cache()
        container2 = get_cached_container()
        second_id = id(container2)

        # Assert - Different instances after clear
        assert container1 is not container2, "Na clear moet nieuwe instance komen"
        assert first_id != second_id, "IDs moeten verschillend zijn na clear"

    def test_cache_stats_after_clear(self):
        """Verify cache stats reset correctly after clear."""
        # Arrange
        get_cached_container()
        get_cached_container()

        # Act
        clear_container_cache()

        # Assert
        cache_info = get_cached_container.cache_info()
        assert cache_info.currsize == 0, "Cache moet leeg zijn na clear"
        assert cache_info.hits == 0, "Hits moeten 0 zijn na clear"
        assert cache_info.misses == 0, "Misses moeten 0 zijn na clear"

    def test_container_stats_api(self):
        """Verify get_container_stats returns correct data."""
        # Arrange
        clear_container_cache()

        # Act
        stats = get_container_stats()

        # Assert
        assert stats["initialized"] is True, "Container moet initialized zijn"
        assert "service_count" in stats, "Stats moeten service_count bevatten"
        assert "services" in stats, "Stats moeten services list bevatten"
        assert "config" in stats, "Stats moeten config bevatten"
        assert "db_path" in stats["config"], "Config moet db_path bevatten"
        assert "has_api_key" in stats["config"], "Config moet has_api_key bevatten"

    def test_no_parameters_accepted(self):
        """Verify function signature has no parameters (except self)."""
        # Arrange & Act
        import inspect

        sig = inspect.signature(get_cached_container)

        # Assert - No parameters allowed
        params = [
            p
            for p in sig.parameters.values()
            if p.name != "self"  # Exclude self if it were a method
        ]
        assert len(params) == 0, "get_cached_container mag GEEN parameters hebben"

    def test_multiple_rapid_calls(self):
        """Verify rapid successive calls still return same instance."""
        # Arrange
        clear_container_cache()

        # Act - Rapid fire calls
        containers = [get_cached_container() for _ in range(10)]

        # Assert - All same instance
        first_container = containers[0]
        for container in containers[1:]:
            assert container is first_container, "Alle containers moeten identiek zijn"

        # Check cache stats
        cache_info = get_cached_container.cache_info()
        assert cache_info.misses == 1, "Moet exact 1 miss hebben"
        assert cache_info.hits == 9, "Moet exact 9 hits hebben"

    def test_container_services_persistent(self):
        """Verify services remain same across multiple get_cached_container calls."""
        # Arrange
        clear_container_cache()

        # Act
        container1 = get_cached_container()
        service1 = container1.orchestrator()  # Initialize a service
        service1_id = id(service1)

        container2 = get_cached_container()
        service2 = container2.orchestrator()  # Get same service
        service2_id = id(service2)

        # Assert
        assert service1 is service2, "Services moeten identiek zijn"
        assert service1_id == service2_id, "Service IDs moeten identiek zijn"

    @patch.dict("os.environ", {"APP_ENV": "development"})
    def test_environment_config_respected(self):
        """Verify environment variables are respected in singleton."""
        # Arrange
        clear_container_cache()

        # Act
        container = get_cached_container()
        stats = get_container_stats()

        # Assert
        assert container is not None, "Container moet geïnitialiseerd zijn"
        assert stats["initialized"] is True, "Stats moeten initialized status tonen"

    def test_cache_decorator_configuration(self):
        """Verify lru_cache is configured correctly."""
        # Act
        cache_info = get_cached_container.cache_info()

        # Assert
        assert cache_info.maxsize == 1, "lru_cache maxsize moet exact 1 zijn"
        assert hasattr(
            get_cached_container, "cache_clear"
        ), "Moet cache_clear method hebben"
        assert hasattr(
            get_cached_container, "cache_info"
        ), "Moet cache_info method hebben"


class TestContainerCacheEdgeCases:
    """Edge case tests voor container caching."""

    def setup_method(self):
        """Setup voor elke test - clear de cache."""
        clear_container_cache()

    def teardown_method(self):
        """Cleanup na elke test - clear de cache."""
        clear_container_cache()

    def test_container_survives_exception_in_caller(self):
        """Verify container remains cached even if caller raises exception."""
        # Arrange
        container1 = get_cached_container()

        # Act - Simulate exception in code that uses container
        try:
            _ = get_cached_container()
            msg = "Simulated error"
            raise ValueError(msg)
        except ValueError:
            pass

        # Get container again
        container2 = get_cached_container()

        # Assert - Same container despite exception
        assert container1 is container2, "Container moet blijven bestaan na exception"

    def test_concurrent_access_pattern(self):
        """Verify container works with rapid sequential access pattern."""
        # Arrange
        clear_container_cache()
        results = []

        # Act - Simulate concurrent-like sequential access
        for _ in range(5):
            container = get_cached_container()
            results.append(id(container))

        # Assert - All IDs identical
        assert len(set(results)) == 1, "Alle IDs moeten identiek zijn"
        assert results[0] == results[-1], "Eerste en laatste ID moeten gelijk zijn"


@pytest.mark.integration
class TestContainerIntegration:
    """Integration tests voor container met andere services."""

    def setup_method(self):
        """Setup voor elke test."""
        clear_container_cache()

    def teardown_method(self):
        """Cleanup na elke test."""
        clear_container_cache()

    def test_lazy_service_loading(self):
        """Verify lazy loading works correctly with cached container."""
        # Arrange
        from utils.container_manager import (
            get_cached_orchestrator,
            get_cached_repository,
            get_cached_web_lookup,
        )

        clear_container_cache()

        # Act
        orchestrator = get_cached_orchestrator()
        repository = get_cached_repository()
        web_lookup = get_cached_web_lookup()

        # Assert - Services are initialized
        assert orchestrator is not None, "Orchestrator moet geïnitialiseerd zijn"
        assert repository is not None, "Repository moet geïnitialiseerd zijn"
        assert web_lookup is not None, "Web lookup moet geïnitialiseerd zijn"

        # Verify they come from same container
        container = get_cached_container()
        assert container.orchestrator() is orchestrator, "Moet zelfde orchestrator zijn"
        assert container.repository() is repository, "Moet zelfde repository zijn"
        assert container.web_lookup() is web_lookup, "Moet zelfde web_lookup zijn"
