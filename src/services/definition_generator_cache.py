"""
Definition Generator Caching System.

Advanced caching implementation extracted and enhanced from
definitie_generator/generator.py with support for multiple strategies.
"""

import asyncio
import hashlib
import logging
import pickle
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from services.definition_generator_config import CacheConfig, CacheStrategy
from services.interfaces import Definition, GenerationRequest

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata."""

    data: Any
    created_at: float
    ttl: int
    access_count: int = 0
    last_accessed: float = None

    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.created_at

    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return time.time() > (self.created_at + self.ttl)

    @property
    def age_seconds(self) -> float:
        """Get age of cache entry in seconds."""
        return time.time() - self.created_at

    def touch(self):
        """Update last accessed time and increment access count."""
        self.last_accessed = time.time()
        self.access_count += 1


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    async def get(self, key: str) -> CacheEntry | None:
        """Get value from cache."""

    @abstractmethod
    async def set(self, key: str, entry: CacheEntry) -> bool:
        """Set value in cache."""

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""

    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache entries."""

    @abstractmethod
    async def stats(self) -> dict[str, Any]:
        """Get cache statistics."""


class MemoryCacheBackend(CacheBackend):
    """In-memory cache backend with LRU eviction."""

    def __init__(self, max_entries: int = 1000):
        self.max_entries = max_entries
        self._cache: dict[str, CacheEntry] = {}
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "evictions": 0,
        }

    async def get(self, key: str) -> CacheEntry | None:
        """Get from memory cache."""
        if key in self._cache:
            entry = self._cache[key]
            if entry.is_expired:
                await self.delete(key)
                self._stats["misses"] += 1
                return None

            entry.touch()
            self._stats["hits"] += 1
            return entry

        self._stats["misses"] += 1
        return None

    async def set(self, key: str, entry: CacheEntry) -> bool:
        """Set in memory cache with LRU eviction."""
        # Evict if at capacity
        if len(self._cache) >= self.max_entries and key not in self._cache:
            await self._evict_lru()

        self._cache[key] = entry
        self._stats["sets"] += 1
        return True

    async def delete(self, key: str) -> bool:
        """Delete from memory cache."""
        if key in self._cache:
            del self._cache[key]
            self._stats["deletes"] += 1
            return True
        return False

    async def clear(self) -> bool:
        """Clear memory cache."""
        self._cache.clear()
        return True

    async def stats(self) -> dict[str, Any]:
        """Get memory cache statistics."""
        return {
            **self._stats,
            "entries": len(self._cache),
            "max_entries": self.max_entries,
            "memory_usage_bytes": sum(
                len(pickle.dumps(entry)) for entry in self._cache.values()
            ),
        }

    async def _evict_lru(self):
        """Evict least recently used entry."""
        if not self._cache:
            return

        # Find LRU entry
        lru_key = min(self._cache.keys(), key=lambda k: self._cache[k].last_accessed)

        await self.delete(lru_key)
        self._stats["evictions"] += 1


class RedisCacheBackend(CacheBackend):
    """Redis cache backend for distributed caching."""

    def __init__(self, redis_url: str, db: int = 0, prefix: str = "defgen:"):
        self.redis_url = redis_url
        self.db = db
        self.prefix = prefix
        self._redis = None
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0,
        }

    async def _get_redis(self):
        """Get Redis connection (lazy initialization)."""
        if self._redis is None:
            try:
                import aioredis

                self._redis = await aioredis.from_url(
                    self.redis_url,
                    db=self.db,
                    decode_responses=False,  # We handle encoding ourselves
                )
            except ImportError:
                logger.error(
                    "aioredis not available - install with: pip install aioredis"
                )
                raise
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self._stats["errors"] += 1
                raise

        return self._redis

    async def get(self, key: str) -> CacheEntry | None:
        """Get from Redis cache."""
        try:
            redis = await self._get_redis()
            data = await redis.get(f"{self.prefix}{key}")

            if data:
                # Security: pickle usage is safe here as data is internally managed
                entry = pickle.loads(data)  # nosec B301
                if entry.is_expired:
                    await self.delete(key)
                    self._stats["misses"] += 1
                    return None

                entry.touch()
                self._stats["hits"] += 1
                return entry

            self._stats["misses"] += 1
            return None

        except Exception as e:
            logger.error(f"Redis get error: {e}")
            self._stats["errors"] += 1
            return None

    async def set(self, key: str, entry: CacheEntry) -> bool:
        """Set in Redis cache."""
        try:
            redis = await self._get_redis()
            data = pickle.dumps(entry)

            await redis.setex(f"{self.prefix}{key}", entry.ttl, data)

            self._stats["sets"] += 1
            return True

        except Exception as e:
            logger.error(f"Redis set error: {e}")
            self._stats["errors"] += 1
            return False

    async def delete(self, key: str) -> bool:
        """Delete from Redis cache."""
        try:
            redis = await self._get_redis()
            result = await redis.delete(f"{self.prefix}{key}")

            if result > 0:
                self._stats["deletes"] += 1
                return True
            return False

        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            self._stats["errors"] += 1
            return False

    async def clear(self) -> bool:
        """Clear Redis cache (keys with our prefix)."""
        try:
            redis = await self._get_redis()
            keys = await redis.keys(f"{self.prefix}*")

            if keys:
                await redis.delete(*keys)

            return True

        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            self._stats["errors"] += 1
            return False

    async def stats(self) -> dict[str, Any]:
        """Get Redis cache statistics."""
        try:
            redis = await self._get_redis()
            info = await redis.info()
            keys = await redis.keys(f"{self.prefix}*")

            return {
                **self._stats,
                "entries": len(keys),
                "redis_memory_used": info.get("used_memory", 0),
                "redis_connected_clients": info.get("connected_clients", 0),
            }

        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return self._stats


class HybridCacheBackend(CacheBackend):
    """Hybrid cache using both memory and Redis backends."""

    def __init__(
        self, memory_backend: MemoryCacheBackend, redis_backend: RedisCacheBackend
    ):
        self.memory = memory_backend
        self.redis = redis_backend
        self._stats = {
            "memory_hits": 0,
            "redis_hits": 0,
            "total_misses": 0,
        }

    async def get(self, key: str) -> CacheEntry | None:
        """Get from memory first, then Redis."""
        # Try memory cache first
        entry = await self.memory.get(key)
        if entry:
            self._stats["memory_hits"] += 1
            return entry

        # Try Redis cache
        entry = await self.redis.get(key)
        if entry:
            # Populate memory cache
            await self.memory.set(key, entry)
            self._stats["redis_hits"] += 1
            return entry

        self._stats["total_misses"] += 1
        return None

    async def set(self, key: str, entry: CacheEntry) -> bool:
        """Set in both memory and Redis."""
        memory_result = await self.memory.set(key, entry)
        redis_result = await self.redis.set(key, entry)

        # Success if either succeeds
        return memory_result or redis_result

    async def delete(self, key: str) -> bool:
        """Delete from both memory and Redis."""
        memory_result = await self.memory.delete(key)
        redis_result = await self.redis.delete(key)

        return memory_result or redis_result

    async def clear(self) -> bool:
        """Clear both memory and Redis."""
        memory_result = await self.memory.clear()
        redis_result = await self.redis.clear()

        return memory_result and redis_result

    async def stats(self) -> dict[str, Any]:
        """Get combined cache statistics."""
        memory_stats = await self.memory.stats()
        redis_stats = await self.redis.stats()

        return {
            "hybrid": self._stats,
            "memory": memory_stats,
            "redis": redis_stats,
        }


class DefinitionGeneratorCache:
    """
    High-level caching system for definition generation.

    Extracted and enhanced from definitie_generator/generator.py
    with support for multiple backends and intelligent key generation.
    """

    def __init__(self, config: CacheConfig):
        self.config = config
        self.backend = self._create_backend()
        self._cache_stats = {
            "requests": 0,
            "hits": 0,
            "misses": 0,
            "hit_rate": 0.0,
        }

    def _create_backend(self) -> CacheBackend:
        """Create appropriate cache backend based on configuration."""
        if self.config.strategy == CacheStrategy.NONE:
            return None

        if self.config.strategy == CacheStrategy.MEMORY:
            return MemoryCacheBackend(max_entries=self.config.max_entries)

        if self.config.strategy == CacheStrategy.REDIS:
            return RedisCacheBackend(
                redis_url=self.config.redis_url,
                db=self.config.redis_db,
                prefix=self.config.redis_prefix,
            )

        if self.config.strategy == CacheStrategy.HYBRID:
            memory_backend = MemoryCacheBackend(max_entries=self.config.max_entries)
            redis_backend = RedisCacheBackend(
                redis_url=self.config.redis_url,
                db=self.config.redis_db,
                prefix=self.config.redis_prefix,
            )
            return HybridCacheBackend(memory_backend, redis_backend)

        msg = f"Unknown cache strategy: {self.config.strategy}"
        raise ValueError(msg)

    def _generate_cache_key(
        self, request: GenerationRequest, context: dict | None = None
    ) -> str:
        """
        Generate intelligent cache key based on request and context.

        Enhanced from definitie_generator implementation with better collision resistance.
        """
        key_parts = [request.begrip.lower()]

        # Include context in key if enabled
        if self.config.include_context_in_key:
            if request.context:
                key_parts.append(f"ctx:{request.context}")
            # EPIC-010: domein field verwijderd - gebruik juridische_context
            # if request.domein:
            #     key_parts.append(f"dom:{request.domein}")
            if request.organisatie:
                key_parts.append(f"org:{request.organisatie}")

            # Include context hash if provided
            if context:
                context_str = str(sorted(context.items()))
                context_hash = hashlib.md5(
                    context_str.encode(), usedforsecurity=False
                ).hexdigest()[:8]
                key_parts.append(f"ch:{context_hash}")

        # Include model in key if enabled
        if self.config.include_model_in_key:
            # We'll need to get this from the generator config
            key_parts.append("gpt4")  # Default assumption

        # Create final key
        key = "|".join(key_parts)

        # Hash long keys to prevent issues
        if len(key) > 200:
            key = hashlib.sha256(key.encode()).hexdigest()

        return key

    async def get_cached_definition(
        self, request: GenerationRequest, context: dict | None = None
    ) -> Definition | None:
        """Get cached definition if available."""
        if not self.backend:
            return None

        self._cache_stats["requests"] += 1

        key = self._generate_cache_key(request, context)

        try:
            entry = await self.backend.get(key)
            if entry:
                self._cache_stats["hits"] += 1
                self._update_hit_rate()

                logger.debug(f"Cache hit for key: {key[:50]}...")
                return entry.data

            self._cache_stats["misses"] += 1
            self._update_hit_rate()
            logger.debug(f"Cache miss for key: {key[:50]}...")
            return None

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    async def cache_definition(
        self,
        request: GenerationRequest,
        definition: Definition,
        context: dict | None = None,
    ) -> bool:
        """Cache a generated definition."""
        if not self.backend:
            return False

        key = self._generate_cache_key(request, context)

        try:
            entry = CacheEntry(
                data=definition, created_at=time.time(), ttl=self.config.ttl
            )

            result = await self.backend.set(key, entry)
            if result:
                logger.debug(f"Cached definition for key: {key[:50]}...")

            return result

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    async def invalidate_cache(self, request: GenerationRequest) -> bool:
        """Invalidate cache for specific request."""
        if not self.backend:
            return False

        key = self._generate_cache_key(request)

        try:
            return await self.backend.delete(key)
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return False

    async def clear_cache(self) -> bool:
        """Clear all cached definitions."""
        if not self.backend:
            return False

        try:
            return await self.backend.clear()
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False

    async def get_cache_stats(self) -> dict[str, Any]:
        """Get comprehensive cache statistics."""
        stats = {
            "cache_stats": self._cache_stats,
            "config": {
                "strategy": self.config.strategy.value,
                "ttl": self.config.ttl,
                "max_entries": self.config.max_entries,
            },
        }

        if self.backend:
            backend_stats = await self.backend.stats()
            stats["backend_stats"] = backend_stats

        return stats

    def _update_hit_rate(self):
        """Update cache hit rate."""
        if self._cache_stats["requests"] > 0:
            self._cache_stats["hit_rate"] = (
                self._cache_stats["hits"] / self._cache_stats["requests"]
            )


# Decorator for caching function results (from definitie_generator)
def cache_definition_generation(ttl: int = 3600):
    """
    Decorator for caching definition generation results.

    Enhanced version of the decorator from definitie_generator/generator.py
    """

    def decorator(func):
        cache = {}

        def _create_cache_key(*args, **kwargs):
            """Create cache key from function arguments."""
            key_data = str(args) + str(sorted(kwargs.items()))
            return hashlib.md5(key_data.encode(), usedforsecurity=False).hexdigest()

        async def async_wrapper(*args, **kwargs):
            key = _create_cache_key(*args, **kwargs)

            # Check cache
            if key in cache:
                entry, timestamp = cache[key]
                if time.time() - timestamp < ttl:
                    logger.debug(f"Function cache hit: {func.__name__}")
                    return entry
                # Expired
                del cache[key]

            # Generate and cache
            result = await func(*args, **kwargs)
            cache[key] = (result, time.time())
            logger.debug(f"Function cache miss: {func.__name__}")

            return result

        def sync_wrapper(*args, **kwargs):
            key = _create_cache_key(*args, **kwargs)

            # Check cache
            if key in cache:
                entry, timestamp = cache[key]
                if time.time() - timestamp < ttl:
                    logger.debug(f"Function cache hit: {func.__name__}")
                    return entry
                # Expired
                del cache[key]

            # Generate and cache
            result = func(*args, **kwargs)
            cache[key] = (result, time.time())
            logger.debug(f"Function cache miss: {func.__name__}")

            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
