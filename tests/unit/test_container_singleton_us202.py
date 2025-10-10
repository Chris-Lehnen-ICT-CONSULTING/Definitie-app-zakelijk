"""
Test Container Singleton Behavior (US-202 Fix).

This test verifies that ServiceContainer is truly a singleton and that
no duplicate initialization occurs when accessed via different paths.

Issue: Container was being initialized 2x per session:
    - PATH 1 (13:00:02): SessionStateManager → utils.container_manager ✅
    - PATH 2 (13:00:16): TabbedInterface → direct get_cached_container() ❌

Fix: All paths now use get_cached_service_container() which uses session state.
"""

import pytest


class TestContainerSingleton:
    """Test ServiceContainer singleton behavior after US-202 fix."""

    def test_container_is_singleton_via_cached_services(self):
        """Verify that get_cached_service_container returns same instance."""
        from ui.cached_services import get_cached_service_container

        # Clear any existing cache
        from utils.container_manager import clear_container_cache

        clear_container_cache()

        # Get container twice
        container1 = get_cached_service_container()
        container2 = get_cached_service_container()

        # Must be the SAME instance (not just equal, but same object in memory)
        assert (
            container1 is container2
        ), "Container instances should be the same object in memory"

        # Verify same container ID
        assert container1.get_container_id() == container2.get_container_id()

    def test_container_via_utils_manager_is_singleton(self):
        """Verify that utils.container_manager returns same instance."""
        # Clear any existing cache
        from utils.container_manager import clear_container_cache, get_cached_container

        clear_container_cache()

        # Get container twice
        container1 = get_cached_container()
        container2 = get_cached_container()

        # Must be the SAME instance
        assert container1 is container2

        # Verify same container ID
        assert container1.get_container_id() == container2.get_container_id()

    def test_no_duplicate_initialization_paths(self):
        """
        Verify that TabbedInterface and SessionStateManager use the same container.

        This is the CRITICAL test for the US-202 fix.
        Before fix: 2 different containers were created.
        After fix: 1 shared singleton container.
        """
        # Clear all caches to start fresh
        from utils.container_manager import clear_container_cache

        clear_container_cache()

        # Simulate the app startup flow:
        # 1. SessionStateManager.initialize_session_state() creates container
        # 2. TabbedInterface.__init__() should reuse the SAME container

        # PATH 1: SessionStateManager initializes services
        from ui.cached_services import initialize_services_once
        from ui.session_state import SessionStateManager

        initialize_services_once()
        container_from_session = SessionStateManager.get_value("service_container")
        assert container_from_session is not None
        id_from_session = container_from_session.get_container_id()

        # PATH 2: TabbedInterface gets container
        from ui.cached_services import get_cached_service_container

        container_from_interface = get_cached_service_container()
        id_from_interface = container_from_interface.get_container_id()

        # CRITICAL: Must be the SAME container instance
        assert container_from_session is container_from_interface, (
            f"Container instances differ! "
            f"Session ID: {id_from_session}, Interface ID: {id_from_interface}"
        )

        # Verify IDs match
        assert id_from_session == id_from_interface

    def test_container_id_is_unique_per_instance(self):
        """Verify that different container instances have different IDs."""
        from services.container import ServiceContainer

        # Create two separate instances (outside the singleton cache)
        container1 = ServiceContainer()
        container2 = ServiceContainer()

        # These should have DIFFERENT IDs (they're different objects)
        id1 = container1.get_container_id()
        id2 = container2.get_container_id()

        assert id1 != id2, "Different container instances should have different IDs"

    def test_container_initialization_count(self):
        """Verify that container initialization count is tracked correctly."""
        from utils.container_manager import clear_container_cache, get_cached_container

        # Clear cache
        clear_container_cache()

        # First access - should initialize
        container1 = get_cached_container()
        count1 = container1.get_initialization_count()
        assert count1 >= 1

        # Second access - should return cached instance
        container2 = get_cached_container()
        count2 = container2.get_initialization_count()

        # Same instance, same count
        assert count1 == count2
        assert container1 is container2

    def test_container_id_logging(self, caplog):
        """Verify that container ID is logged during initialization."""
        import logging

        from utils.container_manager import clear_container_cache, get_cached_container

        # Clear cache
        clear_container_cache()

        # Capture logs
        with caplog.at_level(logging.INFO, logger="utils.container_manager"):
            container = get_cached_container()
            container_id = container.get_container_id()

            # Verify log contains container ID
            assert any(
                container_id in msg for msg in caplog.messages
            ), f"Container ID {container_id} not found in logs: {caplog.messages}"


class TestContainerCacheIntegrity:
    """Test cache integrity and defensive checks."""

    def test_lru_cache_info_single_hit(self):
        """Verify that LRU cache shows single hit for singleton access."""
        from utils.container_manager import clear_container_cache, get_cached_container

        # Clear cache
        clear_container_cache()

        # Access twice
        container1 = get_cached_container()
        container2 = get_cached_container()

        # Check cache info
        cache_info = get_cached_container.cache_info()

        # Should have 1 miss (first access) and 1 hit (second access)
        assert cache_info.misses >= 1, "Should have at least 1 cache miss"
        assert cache_info.hits >= 1, "Should have at least 1 cache hit"

        # Verify same instance
        assert container1 is container2

    def test_cache_clear_creates_new_instance(self):
        """Verify that clearing cache creates a new container instance."""
        from utils.container_manager import clear_container_cache, get_cached_container

        # Get first container
        container1 = get_cached_container()
        id1 = container1.get_container_id()

        # Clear cache
        clear_container_cache()

        # Get new container (should be different instance)
        container2 = get_cached_container()
        id2 = container2.get_container_id()

        # Should be different instances with different IDs
        assert container1 is not container2
        assert id1 != id2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
