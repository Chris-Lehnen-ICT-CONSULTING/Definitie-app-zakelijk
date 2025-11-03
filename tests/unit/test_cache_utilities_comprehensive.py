"""
Comprehensive test suite for cache utilities (utils/cache.py).
Tests all helper functions, edge cases, and achieves 95%+ coverage.
"""

import asyncio
import json
import os
import pickle
import shutil
import tempfile
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from utils.cache import (
    CacheConfig,
    CacheManager,
    FileCache,
    cache_async_result,
    cache_definition_generation,
    cache_example_generation,
    cache_gpt_call,
    cache_synonym_generation,
    cached,
    clear_cache,
    configure_cache,
    get_cache_stats,
)


class TestCacheConfig:
    """Test CacheConfig initialization and defaults."""

    def test_default_config(self):
        """Test default configuration values."""
        config = CacheConfig()
        assert config.cache_dir == Path("cache")
        assert config.default_ttl == 3600
        assert config.max_cache_size == 1000
        assert config.enable_cache is True
        assert config.cache_dir.exists()

    def test_custom_config(self):
        """Test custom configuration values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = CacheConfig(
                cache_dir=temp_dir,
                default_ttl=7200,
                max_cache_size=500,
                enable_cache=False,
            )
            assert config.cache_dir == Path(temp_dir)
            assert config.default_ttl == 7200
            assert config.max_cache_size == 500
            assert config.enable_cache is False

    def test_cache_dir_creation(self):
        """Test that cache directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "test_cache"
            assert not cache_path.exists()
            CacheConfig(cache_dir=str(cache_path))
            assert cache_path.exists()


class TestFileCache:
    """Test FileCache functionality."""

    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = CacheConfig(cache_dir=self.temp_dir)
        self.cache = FileCache(self.config)

    def teardown_method(self):
        """Cleanup test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_metadata_loading(self):
        """Test metadata loading from file."""
        # Create metadata file
        metadata = {
            "test_key": {
                "timestamp": datetime.now(UTC).isoformat(),
                "ttl": 3600,
                "size": 100,
            }
        }
        metadata_file = Path(self.temp_dir) / "metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f)

        # Create new cache instance to load metadata
        cache = FileCache(self.config)
        assert cache.metadata == metadata

    def test_metadata_loading_error(self):
        """Test handling of corrupted metadata file."""
        metadata_file = Path(self.temp_dir) / "metadata.json"
        with open(metadata_file, "w") as f:
            f.write("corrupted json")

        with patch("utils.cache.logger") as mock_logger:
            cache = FileCache(self.config)
            assert cache.metadata == {}
            mock_logger.warning.assert_called()

    def test_generate_cache_key(self):
        """Test cache key generation."""
        key1 = self.cache._generate_cache_key("arg1", "arg2", kwarg1="value1")
        key2 = self.cache._generate_cache_key("arg1", "arg2", kwarg1="value1")
        key3 = self.cache._generate_cache_key("arg1", "arg3", kwarg1="value1")

        # Same arguments should produce same key
        assert key1 == key2
        # Different arguments should produce different key
        assert key1 != key3
        # Key should be hex string (MD5)
        assert len(key1) == 32
        assert all(c in "0123456789abcdef" for c in key1)

    def test_is_expired_no_metadata(self):
        """Test expiration check when no metadata exists."""
        assert self.cache._is_expired("nonexistent_key") is True

    def test_is_expired_with_valid_entry(self):
        """Test expiration check with valid entry."""
        cache_key = "test_key"
        self.cache.metadata[cache_key] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "ttl": 3600,
            "size": 100,
        }
        assert self.cache._is_expired(cache_key) is False

    def test_is_expired_with_expired_entry(self):
        """Test expiration check with expired entry."""
        cache_key = "test_key"
        past_time = datetime.now(UTC) - timedelta(hours=2)
        self.cache.metadata[cache_key] = {
            "timestamp": past_time.isoformat(),
            "ttl": 3600,  # 1 hour TTL
            "size": 100,
        }
        assert self.cache._is_expired(cache_key) is True

    def test_get_cache_disabled(self):
        """Test get when cache is disabled."""
        self.config.enable_cache = False
        result = self.cache.get("any_key")
        assert result is None

    def test_get_expired_entry(self):
        """Test getting expired cache entry."""
        cache_key = "test_key"
        # Create expired metadata
        past_time = datetime.now(UTC) - timedelta(hours=2)
        self.cache.metadata[cache_key] = {
            "timestamp": past_time.isoformat(),
            "ttl": 1,
            "size": 100,
        }
        # Create cache file
        cache_file = Path(self.temp_dir) / f"{cache_key}.pkl"
        with open(cache_file, "wb") as f:
            pickle.dump("test_value", f)

        result = self.cache.get(cache_key)
        assert result is None
        assert cache_key not in self.cache.metadata
        assert not cache_file.exists()

    def test_get_valid_entry(self):
        """Test getting valid cache entry."""
        cache_key = "test_key"
        test_value = {"data": "test", "number": 42}

        # Set cache entry
        self.cache.set(cache_key, test_value, ttl=3600)

        # Get cache entry
        result = self.cache.get(cache_key)
        assert result == test_value

    def test_get_corrupted_file(self):
        """Test handling of corrupted cache file."""
        cache_key = "test_key"
        self.cache.metadata[cache_key] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "ttl": 3600,
            "size": 100,
        }

        # Create corrupted cache file
        cache_file = Path(self.temp_dir) / f"{cache_key}.pkl"
        with open(cache_file, "w") as f:
            f.write("corrupted")

        with patch("utils.cache.logger") as mock_logger:
            result = self.cache.get(cache_key)
            assert result is None
            mock_logger.warning.assert_called()
            assert cache_key not in self.cache.metadata

    def test_set_cache_disabled(self):
        """Test set when cache is disabled."""
        self.config.enable_cache = False
        result = self.cache.set("test_key", "test_value")
        assert result is False

    def test_set_with_custom_ttl(self):
        """Test setting cache entry with custom TTL."""
        cache_key = "test_key"
        test_value = "test_value"
        custom_ttl = 7200

        result = self.cache.set(cache_key, test_value, ttl=custom_ttl)
        assert result is True
        assert self.cache.metadata[cache_key]["ttl"] == custom_ttl

    def test_set_with_default_ttl(self):
        """Test setting cache entry with default TTL."""
        cache_key = "test_key"
        test_value = "test_value"

        result = self.cache.set(cache_key, test_value)
        assert result is True
        assert self.cache.metadata[cache_key]["ttl"] == self.config.default_ttl

    def test_set_with_write_error(self):
        """Test handling of write errors."""
        cache_key = "test_key"

        # Make cache directory read-only
        os.chmod(self.temp_dir, 0o444)

        with patch("utils.cache.logger") as mock_logger:
            result = self.cache.set(cache_key, "test_value")
            # Restore permissions before assertions
            os.chmod(self.temp_dir, 0o755)
            assert result is False
            mock_logger.error.assert_called()

    def test_delete_entry(self):
        """Test deleting cache entry."""
        cache_key = "test_key"
        test_value = "test_value"

        # Set entry
        self.cache.set(cache_key, test_value)
        assert cache_key in self.cache.metadata

        # Delete entry
        self.cache._delete_entry(cache_key)
        assert cache_key not in self.cache.metadata
        cache_file = Path(self.temp_dir) / f"{cache_key}.pkl"
        assert not cache_file.exists()

    def test_delete_nonexistent_entry(self):
        """Test deleting nonexistent entry."""
        with patch("utils.cache.logger"):
            self.cache._delete_entry("nonexistent")
            # Should not raise error, just log warning if any issue

    def test_cleanup_old_entries(self):
        """Test cleanup of old entries when exceeding max size."""
        self.config.max_cache_size = 3

        # Add 5 entries (exceeds max_cache_size of 3)
        for i in range(5):
            time.sleep(0.01)  # Small delay to ensure different timestamps
            self.cache.set(f"key_{i}", f"value_{i}")

        # Should only keep 3 most recent entries
        assert len(self.cache.metadata) == 3
        assert "key_2" in self.cache.metadata
        assert "key_3" in self.cache.metadata
        assert "key_4" in self.cache.metadata
        assert "key_0" not in self.cache.metadata
        assert "key_1" not in self.cache.metadata

    def test_clear(self):
        """Test clearing all cache entries."""
        # Add some entries
        for i in range(3):
            self.cache.set(f"key_{i}", f"value_{i}")

        assert len(self.cache.metadata) == 3

        # Clear cache
        self.cache.clear()
        assert len(self.cache.metadata) == 0

        # Check files are deleted
        for i in range(3):
            cache_file = Path(self.temp_dir) / f"key_{i}.pkl"
            assert not cache_file.exists()

    def test_clear_with_error(self):
        """Test clear with deletion errors."""
        self.cache.set("test_key", "test_value")

        with (
            patch("utils.cache.logger") as mock_logger,
            patch.object(
                self.cache, "_delete_entry", side_effect=Exception("Delete error")
            ),
        ):
            self.cache.clear()
            mock_logger.error.assert_called()

    def test_get_stats_empty(self):
        """Test getting stats for empty cache."""
        stats = self.cache.get_stats()
        assert stats["entries"] == 0
        assert stats["total_size_bytes"] == 0
        assert stats["total_size_mb"] == 0
        assert stats["oldest_entry"] is None
        assert stats["newest_entry"] is None

    def test_get_stats_with_entries(self):
        """Test getting stats with cache entries."""
        # Add entries
        self.cache.set("key_1", "value_1")
        time.sleep(0.01)
        self.cache.set("key_2", "value_2")

        stats = self.cache.get_stats()
        assert stats["entries"] == 2
        assert stats["total_size_bytes"] > 0
        assert stats["total_size_mb"] > 0
        assert stats["oldest_entry"] is not None
        assert stats["newest_entry"] is not None
        assert stats["oldest_entry"] < stats["newest_entry"]


class TestCachedDecorator:
    """Test cached decorator functionality."""

    def setup_method(self):
        """Setup test environment."""
        clear_cache()

    def test_basic_caching(self):
        """Test basic caching with decorator."""
        call_count = 0

        @cached(ttl=60)
        def test_function(x, y=2):
            nonlocal call_count
            call_count += 1
            return x * y

        # First call
        result1 = test_function(5)
        assert result1 == 10
        assert call_count == 1

        # Second call (cached)
        result2 = test_function(5)
        assert result2 == 10
        assert call_count == 1  # No additional call

        # Different arguments
        result3 = test_function(5, y=3)
        assert result3 == 15
        assert call_count == 2

    def test_custom_cache_key_func(self):
        """Test decorator with custom cache key function."""
        call_count = 0

        def custom_key_func(*args, **kwargs):
            # Only use first argument for cache key
            return f"custom_{args[0]}"

        @cached(ttl=60, cache_key_func=custom_key_func)
        def test_function(x, y=2):
            nonlocal call_count
            call_count += 1
            return x * y

        # These should use same cache key (same x value)
        result1 = test_function(5, y=2)
        result2 = test_function(5, y=3)  # Different y, but same cache key
        assert result1 == result2 == 10  # Same cached result
        assert call_count == 1

    def test_with_cache_manager(self):
        """Test decorator with custom cache manager."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CacheManager(cache_dir=temp_dir)
            call_count = 0

            @cached(ttl=60, cache_manager=manager)
            def test_function(x):
                nonlocal call_count
                call_count += 1
                return x * 2

            result1 = test_function(5)
            result2 = test_function(5)
            assert result1 == result2 == 10
            assert call_count == 1

            # Check manager stats
            stats = manager.get_stats()
            assert stats["hits"] == 1
            assert stats["misses"] == 1


class TestSpecializedCacheDecorators:
    """Test specialized cache decorators."""

    def test_cache_definition_generation(self):
        """Test definition generation cache decorator."""
        decorator = cache_definition_generation(ttl=1800)
        mock_func = MagicMock(return_value="definition")

        wrapped = decorator(mock_func)

        # Test caching with various parameters
        result1 = wrapped(
            "test_term",
            {"context": "test"},
            model="gpt-4",
            temperature=0.7,
            max_tokens=100,
        )
        result2 = wrapped(
            "test_term",
            {"context": "test"},
            model="gpt-4",
            temperature=0.7,
            max_tokens=100,
        )

        assert result1 == result2 == "definition"
        mock_func.assert_called_once()  # Only called once due to caching

    def test_cache_example_generation(self):
        """Test example generation cache decorator."""
        decorator = cache_example_generation(ttl=900)
        mock_func = MagicMock(return_value="examples")

        wrapped = decorator(mock_func)

        result1 = wrapped("term", "definition", {"context": "test"})
        result2 = wrapped("term", "definition", {"context": "test"})

        assert result1 == result2 == "examples"
        mock_func.assert_called_once()

    def test_cache_synonym_generation(self):
        """Test synonym generation cache decorator."""
        decorator = cache_synonym_generation(ttl=3600)
        mock_func = MagicMock(return_value="synonyms")

        wrapped = decorator(mock_func)

        result1 = wrapped("term", {"context": "test"})
        result2 = wrapped("term", {"context": "test"})

        assert result1 == result2 == "synonyms"
        mock_func.assert_called_once()


class TestAsyncCache:
    """Test async cache functionality."""

    @pytest.mark.asyncio()
    async def test_cache_async_result(self):
        """Test async caching decorator."""
        call_count = 0

        @cache_async_result(ttl=60)
        async def async_function(x):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)  # Simulate async work
            return x * 2

        result1 = await async_function(5)
        assert result1 == 10
        assert call_count == 1

        result2 = await async_function(5)
        assert result2 == 10
        assert call_count == 1  # Cached, no additional call


class TestCacheManager:
    """Test CacheManager functionality."""

    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = CacheManager(cache_dir=self.temp_dir, max_size=3, default_ttl=60)

    def teardown_method(self):
        """Cleanup test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test CacheManager initialization."""
        assert self.manager.cache_dir == self.temp_dir
        assert self.manager.max_size == 3
        assert self.manager.default_ttl == 60
        assert len(self.manager._store) == 0
        assert self.manager._hits == 0
        assert self.manager._misses == 0
        assert self.manager._evictions == 0

    def test_set_and_get(self):
        """Test basic set and get operations."""
        self.manager.set("key1", "value1", ttl=60)
        result = self.manager.get("key1")
        assert result == "value1"
        assert self.manager._hits == 1

    def test_get_nonexistent(self):
        """Test getting nonexistent key."""
        result = self.manager.get("nonexistent", default="default")
        assert result == "default"
        assert self.manager._misses == 1

    def test_ttl_expiration(self):
        """Test TTL expiration."""
        self.manager.set("key1", "value1", ttl=0)  # Instant expiration
        time.sleep(0.01)
        result = self.manager.get("key1")
        assert result is None
        assert self.manager._misses == 1

    def test_lru_eviction(self):
        """Test LRU eviction when exceeding max_size."""
        # Fill cache to max_size
        self.manager.set("key1", "value1")
        self.manager.set("key2", "value2")
        self.manager.set("key3", "value3")

        # Access key1 to make it recently used
        self.manager.get("key1")

        # Add new item, should evict key2 (least recently used)
        self.manager.set("key4", "value4")

        assert len(self.manager._store) == 3
        assert "key1" in self.manager._store
        assert "key2" not in self.manager._store  # Evicted
        assert "key3" in self.manager._store
        assert "key4" in self.manager._store
        assert self.manager._evictions == 1

    def test_file_persistence(self):
        """Test file persistence of cache entries."""
        self.manager.set("key1", "value1")

        # Check file exists
        file_path = self.manager._file_path("key1")
        assert file_path.exists()

        # Load from file
        with open(file_path, "rb") as f:
            data = pickle.load(f)
            assert data["value"] == "value1"

    def test_file_persistence_error(self):
        """Test handling of file persistence errors."""
        with patch("builtins.open", side_effect=OSError("Write error")):
            with patch("utils.cache.logger") as mock_logger:
                self.manager.set("key1", "value1")
                # Should still work in memory
                assert "key1" in self.manager._store
                mock_logger.debug.assert_called()

    def test_get_from_disk(self):
        """Test loading value from disk when not in memory."""
        # Set value (persists to disk)
        self.manager.set("key1", "value1", ttl=3600)

        # Clear memory store
        self.manager._store.clear()

        # Should load from disk
        result = self.manager.get("key1")
        assert result == "value1"
        assert self.manager._hits == 1
        assert "key1" in self.manager._store  # Warmed in memory

    def test_delete(self):
        """Test deleting cache entry."""
        self.manager.set("key1", "value1")
        file_path = self.manager._file_path("key1")
        assert file_path.exists()

        self.manager.delete("key1")
        assert "key1" not in self.manager._store
        assert not file_path.exists()

    def test_clear(self):
        """Test clearing all cache entries."""
        # Add entries
        self.manager.set("key1", "value1")
        self.manager.set("key2", "value2")

        # Clear
        self.manager.clear()
        assert len(self.manager._store) == 0

        # Check files are deleted
        for key in ["key1", "key2"]:
            assert not self.manager._file_path(key).exists()

    def test_get_stats(self):
        """Test getting cache statistics."""
        self.manager.set("key1", "value1")
        self.manager.get("key1")  # Hit
        self.manager.get("key2")  # Miss

        stats = self.manager.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5
        assert stats["evictions"] == 0
        assert stats["entries"] == 1

    def test_thread_safety_without_lock(self):
        """Test operation without threading lock."""
        manager = CacheManager(cache_dir=self.temp_dir)
        with patch.object(manager, "_lock", None):
            # Should still work without lock
            manager.set("key1", "value1")
            result = manager.get("key1")
            assert result == "value1"


class TestUtilityFunctions:
    """Test utility functions."""

    def test_cache_gpt_call(self):
        """Test GPT call cache key generation."""
        key1 = cache_gpt_call("prompt", model="gpt-4", temperature=0.7)
        key2 = cache_gpt_call("prompt", model="gpt-4", temperature=0.7)
        key3 = cache_gpt_call("different", model="gpt-4", temperature=0.7)

        assert key1 == key2  # Same parameters
        assert key1 != key3  # Different prompt
        assert len(key1) == 32  # MD5 hash

    def test_get_cache_stats(self):
        """Test getting global cache statistics."""
        clear_cache()

        @cached(ttl=60)
        def test_func(x):
            return x * 2

        test_func(5)  # Miss
        test_func(5)  # Hit

        stats = get_cache_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5
        assert "file_entries" in stats

    def test_clear_cache(self):
        """Test clearing global cache."""

        @cached(ttl=60)
        def test_func(x):
            return x * 2

        test_func(5)
        stats_before = get_cache_stats()
        assert stats_before["misses"] > 0

        clear_cache()
        stats_after = get_cache_stats()
        assert stats_after["hits"] == 0
        assert stats_after["misses"] == 0

    def test_configure_cache(self):
        """Test configuring global cache."""
        with tempfile.TemporaryDirectory() as temp_dir:
            configure_cache(
                cache_dir=temp_dir,
                default_ttl=7200,
                max_cache_size=500,
                enable_cache=False,
            )

            # Test that configuration is applied
            from utils.cache import _cache, _cache_config

            assert _cache_config.cache_dir == Path(temp_dir)
            assert _cache_config.default_ttl == 7200
            assert _cache_config.max_cache_size == 500
            assert _cache_config.enable_cache is False


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_cache_with_none_values(self):
        """Test caching None values."""
        call_count = 0

        @cached(ttl=60)
        def test_func():
            nonlocal call_count
            call_count += 1

        result1 = test_func()
        result2 = test_func()
        assert result1 is None
        assert result2 is None
        # Should be called twice - None is not cached
        assert call_count == 2

    def test_cache_with_empty_values(self):
        """Test caching empty values."""

        @cached(ttl=60)
        def test_func(return_type):
            if return_type == "list":
                return []
            if return_type == "dict":
                return {}
            if return_type == "string":
                return ""
            return None

        # Empty values should be cached
        result1 = test_func("list")
        result2 = test_func("list")
        assert result1 == result2 == []

        result3 = test_func("dict")
        result4 = test_func("dict")
        assert result3 == result4 == {}

    def test_cache_with_large_values(self):
        """Test caching large values."""

        @cached(ttl=60)
        def test_func():
            return {"data": "x" * 1000000}  # 1MB string

        result1 = test_func()
        result2 = test_func()
        assert result1 == result2
        assert len(result1["data"]) == 1000000

    def test_cache_with_complex_objects(self):
        """Test caching complex objects."""

        class CustomObject:
            def __init__(self, value):
                self.value = value

            def __eq__(self, other):
                return self.value == other.value

        @cached(ttl=60)
        def test_func():
            return CustomObject(42)

        result1 = test_func()
        result2 = test_func()
        assert result1 == result2
        assert result1.value == 42

    def test_cache_manager_python38_compatibility(self):
        """Test CacheManager compatibility with Python 3.8."""
        manager = CacheManager(cache_dir=tempfile.mkdtemp())

        # Simulate Python 3.8 by making unlink raise TypeError
        with patch(
            "pathlib.Path.unlink",
            side_effect=TypeError("got an unexpected keyword argument 'missing_ok'"),
        ):
            # Should handle gracefully
            manager.delete("nonexistent")
            manager.clear()

    def test_file_cache_without_metadata_save(self):
        """Test FileCache when metadata save fails."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = CacheConfig(cache_dir=temp_dir)
            cache = FileCache(config)

            with patch.object(
                cache, "_save_metadata", side_effect=Exception("Save error")
            ):
                # Should still return True but log error
                result = cache.set("key1", "value1")
                assert result is True  # Operation succeeds despite metadata save error


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=utils.cache", "--cov-report=term-missing"])
