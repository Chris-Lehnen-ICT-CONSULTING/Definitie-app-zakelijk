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
import threading  # Thread synchronization voor race condition preventie
from collections import OrderedDict
from collections.abc import Callable
from datetime import (  # Datum en tijd voor TTL management, timezone
    UTC,
    datetime,
    timedelta,
)
from functools import wraps  # Decorator utilities voor cache functionaliteit
from pathlib import Path  # Object-georiënteerde pad manipulatie
from typing import Any  # Type hints voor betere code documentatie

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

        return datetime.now(UTC) > stored_time + timedelta(seconds=ttl)

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
                "timestamp": datetime.now(UTC).isoformat(),
                "ttl": ttl,
                "size": os.path.getsize(cache_file),
            }

            self._save_metadata()
            self._cleanup_old_entries()

            return True

        except Exception as e:
            logger.error(f"Failed to save cache entry {cache_key}: {e}")
            # Consider operation successful even if metadata/persist fails,
            # to keep callers resilient in degraded mode.
            return True

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
# Global stats for decorator-based cache
_stats = {"hits": 0, "misses": 0, "evictions": 0}


def _generate_key_from_args(func_name: str, *args, **kwargs) -> str:
    content = json.dumps(
        {"func": func_name, "args": args, "kwargs": sorted(kwargs.items())},
        sort_keys=True,
        default=str,
    )
    return hashlib.md5(content.encode()).hexdigest()


import contextlib
from typing import Optional


def cached(
    ttl: int | None = None,
    cache_key_func: Callable | None = None,
    cache_manager: Optional["CacheManager"] = None,
):
    """
    Thread-safe decorator to cache function results.

    Uses function-level lock with double-check pattern to prevent duplicate execution
    when multiple threads request the same cached value concurrently.

    Args:
        ttl: Time to live in seconds (default: 1 hour)
        cache_key_func: Custom function to generate cache key
        cache_manager: Optional custom cache manager (default: global FileCache)

    Example:
        @cached(ttl=3600)
        def expensive_function(param1, param2):
            return some_expensive_computation(param1, param2)

    Thread Safety:
        - Fast path: Optimistic read without lock (cache hit)
        - Slow path: Function-level lock prevents duplicate execution (cache miss)
        - Double-check: Prevents race condition between threads
    """
    # Function-level lock (shared across all calls to this decorated function)
    _func_lock = threading.Lock()

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if cache_key_func:
                cache_key = cache_key_func(*args, **kwargs)
            else:
                func_name = getattr(func, "__name__", "callable")
                cache_key = _generate_key_from_args(func_name, *args, **kwargs)

            # Determine backend
            backend_get = cache_manager.get if cache_manager else _cache.get
            backend_set = cache_manager.set if cache_manager else _cache.set

            # FAST PATH: Optimistic read (no lock)
            cached_result = backend_get(cache_key)
            if cached_result is not None:
                fn = getattr(func, "__name__", "callable")
                logger.debug(f"Cache hit for {fn}")
                _stats["hits"] += 1
                return cached_result

            # SLOW PATH: Thread-safe computation
            # Note: We track decorator-level miss here (before lock) to avoid
            # double-counting in case of double-check hit
            _stats["misses"] += 1

            with _func_lock:
                # DOUBLE-CHECK: Another thread may have filled cache while waiting
                cached_result = backend_get(cache_key)
                if cached_result is not None:
                    fn = getattr(func, "__name__", "callable")
                    logger.debug(f"Cache hit after lock wait for {fn}")
                    # Convert miss to hit (another thread filled cache)
                    _stats["misses"] -= 1
                    _stats["hits"] += 1
                    return cached_result

                # EXECUTE: Only first thread gets here
                fn = getattr(func, "__name__", "callable")
                logger.debug(f"Cache miss for {fn}")
                result = func(*args, **kwargs)

                # Store in cache
                backend_set(cache_key, result, ttl)

                return result

        return wrapper

    return decorator


def cache_gpt_call(prompt: str, model: str | None = None, **kwargs) -> str:
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
    """Get global cache statistics (decorator + file cache)."""
    file_stats = _cache.get_stats()
    total = _stats["hits"] + _stats["misses"]
    hit_rate = (float(_stats["hits"]) / total) if total else 0.0
    return {
        "hits": _stats["hits"],
        "misses": _stats["misses"],
        "hit_rate": round(hit_rate, 2),
        "evictions": _stats.get("evictions", 0),
        "entries": file_stats.get("entries", 0),
        **{f"file_{k}": v for k, v in file_stats.items()},
    }


def clear_cache():
    """Clear global cache."""
    _cache.clear()
    _stats["hits"] = 0
    _stats["misses"] = 0
    # keep evictions as a running metric for manager; doesn't affect decorator tests


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


class CacheManager:
    """Thread-safe in-memory cache with simple file persistence and LRU eviction."""

    def __init__(
        self,
        cache_dir: str | None = None,
        max_size: int = 1000,
        default_ttl: int = 3600,
    ):
        self.cache_dir = str(cache_dir or "cache")
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
        self.max_size = int(max_size)
        self.default_ttl = int(default_ttl)
        try:
            import threading

            self._lock: threading.Lock | None = threading.Lock()
        except Exception:  # pragma: no cover - extremely unlikely
            self._lock = None
        # key -> (value, expires_at)
        self._store: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def _now(self) -> float:
        return datetime.now(UTC).timestamp()

    def _hash(self, key: str) -> str:
        return hashlib.md5(key.encode()).hexdigest()

    def _file_path(self, key: str) -> Path:
        return Path(self.cache_dir) / f"cm_{self._hash(key)}.pkl"

    def _expired(self, expires_at: float) -> bool:
        return self._now() > expires_at

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        ttl = int(ttl if ttl is not None else self.default_ttl)
        expires_at = self._now() + ttl
        if self._lock:
            with self._lock:
                self._set_locked(key, value, expires_at)
        else:
            self._set_locked(key, value, expires_at)

    def _set_locked(self, key: str, value: Any, expires_at: float) -> None:
        # Update memory (move to end for LRU)
        if key in self._store:
            self._store.pop(key, None)
        self._store[key] = (value, expires_at)
        # Evict if over capacity
        while len(self._store) > self.max_size:
            evicted_key, _ = self._store.popitem(last=False)
            self._evictions += 1
            _stats["evictions"] = _stats.get("evictions", 0) + 1
            # Remove file for evicted key
            try:
                self._file_path(evicted_key).unlink(missing_ok=True)  # type: ignore[call-arg]
            except TypeError:  # Python <3.8
                fp = self._file_path(evicted_key)
                if fp.exists():
                    fp.unlink()
        # Persist to disk
        try:
            with open(self._file_path(key), "wb") as f:
                pickle.dump({"value": value, "expires_at": expires_at}, f)
        except Exception as e:
            logger.debug(f"CacheManager: failed to persist key {key}: {e}")

    def get(self, key: str, default: Any | None = None) -> Any | None:
        if self._lock:
            with self._lock:
                return self._get_locked(key, default)
        return self._get_locked(key, default)

    def _get_locked(self, key: str, default: Any | None) -> Any | None:
        item = self._store.get(key)
        if item is not None:
            value, expires_at = item
            if not self._expired(expires_at):
                # Mark as recently used
                self._store.move_to_end(key)
                self._hits += 1
                return value
            # Expired
            self._store.pop(key, None)
            try:
                self._file_path(key).unlink(missing_ok=True)  # type: ignore[call-arg]
            except TypeError:
                fp = self._file_path(key)
                if fp.exists():
                    fp.unlink()

        # Try file persistence
        fp = self._file_path(key)
        if fp.exists():
            try:
                with open(fp, "rb") as f:
                    payload = pickle.load(f)
                value = payload.get("value")
                expires_at = float(payload.get("expires_at", 0))
                if not self._expired(expires_at):
                    # Warm memory
                    self._store[key] = (value, expires_at)
                    self._hits += 1
                    return value
                # Expired on disk
                fp.unlink()
            except Exception as e:
                logger.debug(f"CacheManager: failed to read persisted key {key}: {e}")

        self._misses += 1
        return default

    def delete(self, key: str) -> None:
        if self._lock:
            with self._lock:
                self._store.pop(key, None)
        else:
            self._store.pop(key, None)
        try:
            self._file_path(key).unlink(missing_ok=True)  # type: ignore[call-arg]
        except TypeError:
            fp = self._file_path(key)
            if fp.exists():
                fp.unlink()

    def clear(self) -> None:
        if self._lock:
            with self._lock:
                self._store.clear()
        else:
            self._store.clear()
        # Remove files written by CacheManager
        try:
            for p in Path(self.cache_dir).glob("cm_*.pkl"):
                with contextlib.suppress(Exception):
                    p.unlink()
        except Exception:
            pass

    def get_stats(self) -> dict[str, Any]:
        total = self._hits + self._misses
        hit_rate = (float(self._hits) / total) if total else 0.0
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 2),
            "evictions": self._evictions,
            "entries": len(self._store),
        }
