"""
Caching utilities voor DefinitieAgent.

Biedt intelligente caching voor dure GPT API calls
en andere kostbare operaties om prestaties te verbeteren.
"""

import hashlib  # Hash functionaliteit voor cache keys
import json  # JSON verwerking voor metadata opslag
import logging  # Logging faciliteiten voor debug en monitoring
import os  # Operating system interface voor bestandsoperaties
import pickle  # Python object serialisatie voor cache data
from collections.abc import Callable
from datetime import (  # Datum en tijd voor TTL management, timezone
    datetime,
    timedelta,
    timezone,
)
from functools import wraps  # Decorator utilities voor cache functionaliteit
from pathlib import Path  # Object-georiënteerde pad manipulatie
from typing import (  # Type hints voor betere code documentatie
    Any,
)

logger = logging.getLogger(__name__)  # Logger instantie voor cache module


class CacheConfig:
    """Configuratie voor cache systeem met aanpasbare instellingen."""

    def __init__(
        self,
        cache_dir: str = "cache",  # Directory voor cache bestanden
        default_ttl: int = 3600,  # Standaard TTL in seconden (1 uur)
        max_cache_size: int = 1000,  # Maximum aantal cache entries
        enable_cache: bool = True,  # Cache aan/uit schakelaar
    ):
        self.cache_dir = Path(cache_dir)  # Converteer naar Path object
        self.default_ttl = default_ttl  # Sla TTL instelling op
        self.max_cache_size = max_cache_size  # Sla size limiet op
        self.enable_cache = enable_cache  # Sla cache toggle op

        # Maak cache directory aan als deze nog niet bestaat
        self.cache_dir.mkdir(exist_ok=True)  # Maak directory met exist_ok=True


class FileCache:
    """Bestand-gebaseerde cache voor GPT responses en andere data."""

    def __init__(self, config: CacheConfig):
        """Initialiseer file cache met gegeven configuratie."""
        self.config = config  # Sla cache configuratie op
        self.cache_dir = config.cache_dir  # Cache directory referentie
        self.metadata_file = (
            self.cache_dir / "metadata.json"
        )  # Metadata bestand locatie
        self._load_metadata()  # Laad bestaande metadata

    def _load_metadata(self):
        """Load cache metadata."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file) as f:
                    self.metadata = json.load(f)
            else:
                self.metadata = {}
        except Exception as e:
            logger.warning(f"Failed to load cache metadata: {e}")
            self.metadata = {}

    def _save_metadata(self):
        """Save cache metadata."""
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache metadata: {e}")

    def _generate_cache_key(self, *args, **kwargs) -> str:
        """Generate cache key from function arguments."""
        # Create a deterministic hash from arguments
        content = json.dumps(
            {"args": args, "kwargs": sorted(kwargs.items())},
            sort_keys=True,
            default=str,
        )

        return hashlib.md5(content.encode()).hexdigest()

    def _is_expired(self, cache_key: str) -> bool:
        """Check if cache entry is expired."""
        if cache_key not in self.metadata:
            return True

        stored_time = datetime.fromisoformat(self.metadata[cache_key]["timestamp"])
        ttl = self.metadata[cache_key]["ttl"]

        return datetime.now(timezone.utc) > stored_time + timedelta(seconds=ttl)

    def get(self, cache_key: str) -> Any | None:
        """Get value from cache."""
        if not self.config.enable_cache:
            return None

        if self._is_expired(cache_key):
            self._delete_entry(cache_key)
            return None

        cache_file = self.cache_dir / f"{cache_key}.pkl"

        try:
            if cache_file.exists():
                with open(cache_file, "rb") as f:
                    return pickle.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cache entry {cache_key}: {e}")
            self._delete_entry(cache_key)

        return None

    def set(self, cache_key: str, value: Any, ttl: int | None = None) -> bool:
        """Set value in cache."""
        if not self.config.enable_cache:
            return False

        if ttl is None:
            ttl = self.config.default_ttl

        cache_file = self.cache_dir / f"{cache_key}.pkl"

        try:
            # Save the cached value
            with open(cache_file, "wb") as f:
                pickle.dump(value, f)

            # Update metadata
            self.metadata[cache_key] = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "ttl": ttl,
                "size": os.path.getsize(cache_file),
            }

            self._save_metadata()
            self._cleanup_old_entries()

            return True

        except Exception as e:
            logger.error(f"Failed to save cache entry {cache_key}: {e}")
            return False

    def _delete_entry(self, cache_key: str):
        """Delete cache entry."""
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        try:
            if cache_file.exists():
                cache_file.unlink()

            if cache_key in self.metadata:
                del self.metadata[cache_key]
                self._save_metadata()

        except Exception as e:
            logger.warning(f"Failed to delete cache entry {cache_key}: {e}")

    def _cleanup_old_entries(self):
        """Remove old cache entries to stay within size limit."""
        if len(self.metadata) <= self.config.max_cache_size:
            return

        # Sort by timestamp (oldest first)
        sorted_entries = sorted(self.metadata.items(), key=lambda x: x[1]["timestamp"])

        # Remove oldest entries
        entries_to_remove = len(self.metadata) - self.config.max_cache_size
        for cache_key, _ in sorted_entries[:entries_to_remove]:
            self._delete_entry(cache_key)

    def clear(self):
        """Clear all cache entries."""
        try:
            for cache_key in list(self.metadata.keys()):
                self._delete_entry(cache_key)

            logger.info("Cache cleared successfully")

        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_size = sum(entry["size"] for entry in self.metadata.values())

        return {
            "entries": len(self.metadata),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "oldest_entry": min(
                (entry["timestamp"] for entry in self.metadata.values()), default=None
            ),
            "newest_entry": max(
                (entry["timestamp"] for entry in self.metadata.values()), default=None
            ),
        }


# Global cache instance
_cache_config = CacheConfig()
_cache = FileCache(_cache_config)


def cached(ttl: int | None = None, cache_key_func: Callable | None = None):
    """
    Decorator to cache function results.

    Args:
        ttl: Time to live in seconds (default: 1 hour)
        cache_key_func: Custom function to generate cache key

    Example:
        @cached(ttl=3600)
        def expensive_function(param1, param2):
            return some_expensive_computation(param1, param2)
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if cache_key_func:
                cache_key = cache_key_func(*args, **kwargs)
            else:
                cache_key = _cache._generate_cache_key(func.__name__, *args, **kwargs)

            # Try to get from cache
            cached_result = _cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result

            # Cache miss - execute function
            logger.debug(f"Cache miss for {func.__name__}")
            result = func(*args, **kwargs)

            # Store in cache
            _cache.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


def cache_gpt_call(prompt: str, model: str = "gpt-5", **kwargs) -> str:
    """
    Generate cache key for GPT API calls.

    Args:
        prompt: The prompt text
        model: GPT model name
        **kwargs: Additional parameters

    Returns:
        Cache key string
    """
    content = {"prompt": prompt, "model": model, "params": sorted(kwargs.items())}

    return hashlib.md5(json.dumps(content, sort_keys=True).encode()).hexdigest()


def get_cache_stats() -> dict[str, Any]:
    """Get global cache statistics."""
    return _cache.get_stats()


def clear_cache():
    """Clear global cache."""
    _cache.clear()


def configure_cache(
    cache_dir: str = "cache",
    default_ttl: int = 3600,
    max_cache_size: int = 1000,
    enable_cache: bool = True,
):
    """
    Configure global cache settings.

    Args:
        cache_dir: Directory for cache files
        default_ttl: Default time to live in seconds
        max_cache_size: Maximum number of cache entries
        enable_cache: Whether to enable caching
    """
    global _cache_config, _cache

    _cache_config = CacheConfig(
        cache_dir=cache_dir,
        default_ttl=default_ttl,
        max_cache_size=max_cache_size,
        enable_cache=enable_cache,
    )

    _cache = FileCache(_cache_config)

    logger.info(
        f"Cache configured: {cache_dir}, TTL: {default_ttl}s, Max entries: {max_cache_size}"
    )


# Specialized cache decorators for common use cases
def cache_definition_generation(ttl: int = 3600):
    """Cache decorator specifically for definition generation."""

    def cache_key_func(
        begrip: str,
        context_dict: dict,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ):
        # Include all parameters in cache key to ensure proper caching
        cache_params = {
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs,
        }
        return cache_gpt_call(
            prompt=f"definition_{begrip}",
            context=json.dumps(context_dict, sort_keys=True),
            **cache_params,
        )

    return cached(ttl=ttl, cache_key_func=cache_key_func)


def cache_example_generation(ttl: int = 1800):  # 30 minutes
    """Cache decorator specifically for example generation."""

    def cache_key_func(begrip: str, definitie: str, context_dict: dict, **kwargs):
        return cache_gpt_call(
            prompt=f"examples_{begrip}",
            definitie=definitie,
            context=json.dumps(context_dict, sort_keys=True),
            **kwargs,
        )

    return cached(ttl=ttl, cache_key_func=cache_key_func)


def cache_synonym_generation(ttl: int = 7200):  # 2 hours
    """Cache decorator specifically for synonym generation."""

    def cache_key_func(begrip: str, context_dict: dict, **kwargs):
        return cache_gpt_call(
            prompt=f"synonyms_{begrip}",
            context=json.dumps(context_dict, sort_keys=True),
            **kwargs,
        )

    return cached(ttl=ttl, cache_key_func=cache_key_func)


# Async cache support functions


def cache_async_result(ttl: int | None = None):
    """
    Async version of the cached decorator.

    Args:
        ttl: Time to live in seconds (default: 1 hour)

    Example:
        @cache_async_result(ttl=3600)
        async def expensive_async_function(param1, param2):
            return await some_expensive_async_computation(param1, param2)
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = _cache._generate_cache_key(func.__name__, *args, **kwargs)

            # Try to get from cache
            cached_result = _cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result

            # Cache miss - execute async function
            logger.debug(f"Cache miss for {func.__name__}")
            result = await func(*args, **kwargs)

            # Store in cache
            _cache.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator
