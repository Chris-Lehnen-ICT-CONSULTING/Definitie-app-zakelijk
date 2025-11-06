"""
Comprehensive test suite for caching system.
Tests cache functionality, TTL management, performance, and integration.
"""

import os
import shutil
import tempfile
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, call, patch

import pytest
from utils.cache import cached, clear_cache, get_cache_stats

# Import CacheManager and EnhancedCache if they exist
try:
    from utils.cache import CacheManager
except ImportError:
    CacheManager = None

try:
    from utils.cache import EnhancedCache
except ImportError:
    EnhancedCache = None


class TestCacheDecorator:
    """Test suite for @cached decorator."""

    def setup_method(self):
        """Setup for each test method."""
        clear_cache()

    def test_basic_caching(self):
        """Test basic caching functionality."""
        call_count = 0

        @cached(ttl=60)
        def test_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call should execute function
        result1 = test_function(5)
        assert result1 == 10
        assert call_count == 1

        # Second call should use cache
        result2 = test_function(5)
        assert result2 == 10
        assert call_count == 1  # No additional call

        # Different argument should execute function
        result3 = test_function(3)
        assert result3 == 6
        assert call_count == 2

    def test_cache_expiration(self, monkeypatch):
        """Test cache TTL expiration."""
        call_count = 0

        # Use injected CacheManager with controllable clock to avoid real sleep
        try:
            from utils.cache import CacheManager
        except ImportError:
            CacheManager = None  # type: ignore

        if CacheManager is not None:
            import tempfile

            with tempfile.TemporaryDirectory() as td:
                cm = CacheManager(cache_dir=td)

                fake_now = [0.0]

                def _fake_now():
                    return fake_now[0]

                monkeypatch.setattr(cm, "_now", _fake_now, raising=True)

                @cached(ttl=0.1, cache_manager=cm)  # 100ms TTL
                def test_function(x):
                    nonlocal call_count
                    call_count += 1
                    return x * 2

                # First call
                result1 = test_function(5)
                assert result1 == 10
                assert call_count == 1

                # Second call within TTL
                result2 = test_function(5)
                assert result2 == 10
                assert call_count == 1

                # Advance clock beyond TTL
                fake_now[0] += 0.2

                # Third call after TTL expiration
                result3 = test_function(5)
                assert result3 == 10
                assert call_count == 2  # Function called again
        else:
            # Fallback: keep a very small real sleep to preserve semantics
            @cached(ttl=0.001)
            def test_function(x):
                nonlocal call_count
                call_count += 1
                return x * 2

            test_function(5)
            test_function(5)
            time.sleep(0.002)
            test_function(5)
            assert call_count == 2

    def test_cache_with_different_argument_types(self):
        """Test caching with various argument types."""
        call_count = 0

        @cached(ttl=60)
        def test_function(a, b=None, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            return f"{a}-{b}-{args}-{kwargs}"

        # Test different argument combinations
        result1 = test_function("hello")
        result2 = test_function("hello")  # Should use cache
        assert result1 == result2
        assert call_count == 1

        test_function("hello", b="world")
        assert call_count == 2  # Different arguments

        test_function("hello", "world", "extra")
        assert call_count == 3  # Different arguments

        test_function("hello", key="value")
        assert call_count == 4  # Different arguments

    def test_cache_key_generation(self):
        """Test cache key generation for different scenarios."""

        @cached(ttl=60)
        def test_function(x, y=None):
            return x + (y or 0)

        # Test that different argument orders create different keys
        result1 = test_function(1, 2)
        result2 = test_function(1, y=2)
        result3 = test_function(x=1, y=2)

        # All should give same result but should be cached separately
        assert result1 == result2 == result3 == 3

    def test_cache_stats(self):
        """Test cache statistics tracking."""
        clear_cache()

        @cached(ttl=60)
        def test_function(x):
            return x * 2

        # Make some calls
        test_function(1)  # Miss
        test_function(1)  # Hit
        test_function(2)  # Miss
        test_function(2)  # Hit
        test_function(1)  # Hit

        stats = get_cache_stats()
        assert stats["hits"] == 3
        assert stats["misses"] == 2
        assert stats["hit_rate"] == 0.6  # 3/5


@pytest.mark.skipif(CacheManager is None, reason="CacheManager not available")
class TestCacheManager:
    """Test suite for CacheManager class."""

    def setup_method(self):
        """Setup for each test method."""
        # Create temporary directory for cache
        self.temp_dir = tempfile.mkdtemp()
        self.cache_manager = CacheManager(cache_dir=self.temp_dir)

    def teardown_method(self):
        """Cleanup after each test method."""
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cache_manager_initialization(self):
        """Test CacheManager initialization."""
        assert self.cache_manager.cache_dir == self.temp_dir
        assert os.path.exists(self.temp_dir)
        assert self.cache_manager.max_size > 0
        assert self.cache_manager.default_ttl > 0

    def test_cache_set_get(self):
        """Test basic cache set and get operations."""
        # Test setting and getting values
        self.cache_manager.set("key1", "value1", ttl=60)
        result = self.cache_manager.get("key1")
        assert result == "value1"

        # Test non-existent key
        result = self.cache_manager.get("nonexistent")
        assert result is None

        # Test default value
        result = self.cache_manager.get("nonexistent", default="default_value")
        assert result == "default_value"

    def test_cache_expiration_in_manager(self, monkeypatch):
        """Test cache expiration in manager."""
        # Patch clock BEFORE set to control expiry
        base = [0.0]

        def _fake_now():
            return base[0]

        if hasattr(self.cache_manager, "_now"):
            monkeypatch.setattr(self.cache_manager, "_now", _fake_now, raising=True)

        # Set value with 1 second TTL at t=0
        self.cache_manager.set("key1", "value1", ttl=1)

        # Should exist immediately
        result = self.cache_manager.get("key1")
        assert result == "value1", "Value should be available immediately after setting"

        # Advance internal clock by > 1s (no real sleep)
        base[0] = 2.0

        # Should be expired with advanced clock
        result = self.cache_manager.get("key1")
        assert result is None, "Value should be expired after TTL"

    def test_cache_delete(self):
        """Test cache deletion."""
        # Set value
        self.cache_manager.set("key1", "value1", ttl=60)
        assert self.cache_manager.get("key1") == "value1"

        # Delete value
        self.cache_manager.delete("key1")
        assert self.cache_manager.get("key1") is None

        # Delete non-existent key should not raise error
        self.cache_manager.delete("nonexistent")

    def test_cache_clear(self):
        """Test cache clearing."""
        # Set multiple values
        self.cache_manager.set("key1", "value1", ttl=60)
        self.cache_manager.set("key2", "value2", ttl=60)

        # Verify values exist
        assert self.cache_manager.get("key1") == "value1"
        assert self.cache_manager.get("key2") == "value2"

        # Clear cache
        self.cache_manager.clear()

        # Verify values are gone
        assert self.cache_manager.get("key1") is None
        assert self.cache_manager.get("key2") is None

    def test_cache_size_management(self):
        """Test cache size management."""
        # Set max size to small value for testing
        small_cache = CacheManager(cache_dir=self.temp_dir, max_size=2)

        # Add items up to max size
        small_cache.set("key1", "value1", ttl=60)
        small_cache.set("key2", "value2", ttl=60)

        # Both should exist
        assert small_cache.get("key1") == "value1"
        assert small_cache.get("key2") == "value2"

        # Add third item (should trigger eviction)
        small_cache.set("key3", "value3", ttl=60)

        # One of the earlier items should be evicted
        # (depends on eviction policy - LRU)
        assert small_cache.get("key3") == "value3"

    def test_cache_persistence(self):
        """Test cache persistence to disk."""
        # Set value with file cache
        self.cache_manager.set("persistent_key", "persistent_value", ttl=60)

        # Create new cache manager with same directory
        new_cache_manager = CacheManager(cache_dir=self.temp_dir)

        # Value should be persisted
        result = new_cache_manager.get("persistent_key")
        assert result == "persistent_value"

    def test_cache_stats_in_manager(self):
        """Test cache statistics in manager."""
        # Perform various operations
        self.cache_manager.set("key1", "value1", ttl=60)
        self.cache_manager.get("key1")  # Hit
        self.cache_manager.get("key1")  # Hit
        self.cache_manager.get("nonexistent")  # Miss

        stats = self.cache_manager.get_stats()
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats
        assert stats["hits"] >= 2
        assert stats["misses"] >= 1


@pytest.mark.skipif(EnhancedCache is None, reason="EnhancedCache not available")
class TestEnhancedCache:
    """Test suite for EnhancedCache class."""

    def setup_method(self):
        """Setup for each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.enhanced_cache = EnhancedCache(cache_dir=self.temp_dir)

    def teardown_method(self):
        """Cleanup after each test method."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_enhanced_cache_initialization(self):
        """Test EnhancedCache initialization."""
        assert self.enhanced_cache.cache_dir == self.temp_dir
        assert hasattr(self.enhanced_cache, "memory_cache")
        assert hasattr(self.enhanced_cache, "file_cache")

    def test_multi_level_caching(self):
        """Test multi-level caching (memory + file)."""
        # Set value
        self.enhanced_cache.set("key1", "value1", ttl=60)

        # Should be in memory cache
        result = self.enhanced_cache.get("key1")
        assert result == "value1"

        # Clear memory cache but keep file cache
        self.enhanced_cache.memory_cache.clear()

        # Should still be available from file cache
        result = self.enhanced_cache.get("key1")
        assert result == "value1"

    def test_cache_warming(self):
        """Test cache warming functionality."""

        # Mock function to warm cache
        def warm_function():
            return {"key1": "value1", "key2": "value2"}

        # Warm cache
        self.enhanced_cache.warm_cache(warm_function)

        # Values should be available
        assert self.enhanced_cache.get("key1") == "value1"
        assert self.enhanced_cache.get("key2") == "value2"

    def test_cache_cleanup(self, monkeypatch):
        """Test cache cleanup functionality."""
        # Set values with different TTLs
        self.enhanced_cache.set("key1", "value1", ttl=0.1)  # Short TTL
        self.enhanced_cache.set("key2", "value2", ttl=60)  # Long TTL

        # Try to advance internal clock if available; fallback to tiny real sleep
        advanced = False
        for attr in ("_now", "now", "time", "_time"):
            if hasattr(self.enhanced_cache, attr):
                base = [0.0]

                def _fake_now():
                    return base[0] + 1.0

                try:
                    monkeypatch.setattr(
                        self.enhanced_cache, attr, _fake_now, raising=True
                    )
                    advanced = True
                    break
                except Exception:
                    pass

        if not advanced:
            # Minimal sleep to preserve intent without slowing suite
            time.sleep(0.02)

        # Run cleanup
        self.enhanced_cache.cleanup_expired()

        # Expired key should be gone, valid key should remain
        assert self.enhanced_cache.get("key1") is None
        assert self.enhanced_cache.get("key2") == "value2"

    def test_cache_preloading(self):
        """Test cache preloading functionality."""
        # Define preload data
        preload_data = {
            "preload_key1": "preload_value1",
            "preload_key2": "preload_value2",
        }

        # Preload cache
        self.enhanced_cache.preload(preload_data, ttl=60)

        # Values should be available
        assert self.enhanced_cache.get("preload_key1") == "preload_value1"
        assert self.enhanced_cache.get("preload_key2") == "preload_value2"

    def test_cache_performance_monitoring(self):
        """Test cache performance monitoring."""
        # Perform operations
        self.enhanced_cache.set("key1", "value1", ttl=60)
        self.enhanced_cache.get("key1")  # Hit
        self.enhanced_cache.get("key1")  # Hit
        self.enhanced_cache.get("nonexistent")  # Miss

        # Get performance metrics
        metrics = self.enhanced_cache.get_performance_metrics()

        assert "hit_rate" in metrics
        assert "average_response_time" in metrics
        assert "memory_usage" in metrics
        assert "cache_size" in metrics

        assert metrics["hit_rate"] > 0
        assert metrics["average_response_time"] >= 0


class TestCacheIntegration:
    """Integration tests for cache system."""

    def setup_method(self):
        """Setup for each test method."""
        clear_cache()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Cleanup after each test method."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cache_decorator_with_manager(self):
        """Test integration between cache decorator and manager."""
        # Create cache manager
        cache_manager = CacheManager(cache_dir=self.temp_dir)

        @cached(ttl=60, cache_manager=cache_manager)
        def test_function(x):
            return x * 2

        # Test function caching
        result1 = test_function(5)
        result2 = test_function(5)

        assert result1 == result2 == 10

        # Verify in cache manager
        # Note: The actual key depends on implementation
        stats = cache_manager.get_stats()
        assert stats["hits"] > 0

    def test_cache_configuration_integration(self):
        """Test cache integration with configuration system."""
        from config import get_cache_config

        # Get cache configuration
        cache_config = get_cache_config()
        cache_settings = cache_config.get_cache_config()

        # Create cache manager with configuration
        cache_manager = CacheManager(
            cache_dir=cache_settings["cache_dir"],
            max_size=cache_settings["max_cache_size"],
            default_ttl=cache_settings["default_ttl"],
        )

        # Test that configuration is applied
        assert cache_manager.default_ttl == cache_settings["default_ttl"]
        assert cache_manager.max_size == cache_settings["max_cache_size"]

    def test_cache_with_different_data_types(self):
        """Test caching with various data types."""

        @cached(ttl=60)
        def test_function(data_type, value):
            return f"{data_type}: {value}"

        # Test different data types
        test_cases = [
            ("string", "hello"),
            ("int", 42),
            ("float", 3.14),
            ("list", [1, 2, 3]),
            ("dict", {"key": "value"}),
            ("tuple", (1, 2, 3)),
            ("bool", True),
            ("none", None),
        ]

        for data_type, value in test_cases:
            result = test_function(data_type, value)
            assert result == f"{data_type}: {value}"

            # Second call should use cache
            result2 = test_function(data_type, value)
            assert result2 == result

    def test_cache_error_handling(self):
        """Test cache error handling."""

        @cached(ttl=60)
        def error_function():
            msg = "Test error"
            raise ValueError(msg)

        # Error should not be cached
        with pytest.raises(ValueError):
            error_function()

        with pytest.raises(ValueError):
            error_function()  # Should raise again, not use cache

    def test_cache_memory_pressure(self):
        """Test cache behavior under memory pressure."""
        # Create cache with small size
        small_cache = CacheManager(cache_dir=self.temp_dir, max_size=5)

        # Add many items
        for i in range(10):
            small_cache.set(f"key_{i}", f"value_{i}", ttl=60)

        # Should have evicted some items
        stats = small_cache.get_stats()
        assert stats["evictions"] > 0

    def test_concurrent_cache_access(self):
        """Test concurrent access to cache."""
        import threading

        cache_manager = CacheManager(cache_dir=self.temp_dir)
        results = []

        def cache_worker(worker_id):
            # Each worker performs cache operations
            for i in range(10):
                key = f"worker_{worker_id}_key_{i}"
                value = f"worker_{worker_id}_value_{i}"
                cache_manager.set(key, value, ttl=60)
                result = cache_manager.get(key)
                results.append(result == value)

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=cache_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All operations should succeed
        assert all(results)
        assert len(results) == 50  # 5 workers * 10 operations each


@pytest.mark.skipif(CacheManager is None, reason="CacheManager not available")
class TestCachePerformance:
    """Performance tests for cache system."""

    def setup_method(self):
        """Setup for each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_manager = CacheManager(cache_dir=self.temp_dir)

    def teardown_method(self):
        """Cleanup after each test method."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cache_performance_benchmark(self):
        """Benchmark cache performance."""
        import time

        # Measure cache set performance
        start_time = time.time()
        for i in range(1000):
            self.cache_manager.set(f"key_{i}", f"value_{i}", ttl=60)
        set_time = time.time() - start_time

        # Measure cache get performance
        start_time = time.time()
        for i in range(1000):
            self.cache_manager.get(f"key_{i}")
        get_time = time.time() - start_time

        # Performance should be reasonable
        assert set_time < 5.0  # Should set 1000 items in < 5 seconds
        assert get_time < 1.0  # Should get 1000 items in < 1 second

        # Hit rate should be high
        stats = self.cache_manager.get_stats()
        assert stats["hit_rate"] > 0.9  # 90% hit rate

    def test_memory_usage_monitoring(self):
        """Test memory usage monitoring."""
        import os

        import psutil

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Add many items to cache
        for i in range(5000):
            self.cache_manager.set(f"key_{i}", f"value_{i}" * 100, ttl=60)

        # Check memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable
        assert memory_increase < 100 * 1024 * 1024  # < 100MB increase

    def test_cache_efficiency_metrics(self):
        """Test cache efficiency metrics."""
        # Simulate realistic access patterns
        # 80% hits, 20% misses (typical cache behavior)

        # First, populate cache
        for i in range(100):
            self.cache_manager.set(f"key_{i}", f"value_{i}", ttl=60)

        # Simulate access pattern
        for _ in range(1000):
            import random

            if random.random() < 0.8:  # 80% hits
                key = f"key_{random.randint(0, 99)}"
                self.cache_manager.get(key)
            else:  # 20% misses
                key = f"miss_key_{random.randint(0, 99)}"
                self.cache_manager.get(key)

        # Check efficiency metrics
        stats = self.cache_manager.get_stats()
        assert stats["hit_rate"] > 0.7  # Should be > 70%
        assert stats["hit_rate"] < 0.9  # Should be < 90% (due to misses)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
