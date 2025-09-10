"""Robust caching system for voorbeelden generation.

This module implements a robust cache key generation system that includes
all relevant parameters to prevent cache collisions and ensure correctness.
"""

import hashlib
import json
import logging
import pickle
from datetime import UTC, datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any

from utils.voorbeelden_debug import DEBUG_ENABLED, debugger

logger = logging.getLogger(__name__)

# Version salt for cache invalidation when schema changes
CACHE_SCHEMA_VERSION = "v2"

# TTL configuration per example type (in seconds)
EXAMPLE_TTL_CONFIG = {
    "voorbeeldzinnen": 1800,  # 30 minutes
    "praktijkvoorbeelden": 1800,  # 30 minutes
    "tegenvoorbeelden": 1800,  # 30 minutes
    "synoniemen": 14400,  # 4 hours (more stable)
    "antoniemen": 14400,  # 4 hours (more stable)
    "toelichting": 3600,  # 1 hour
}


class RobustVoorbeeldenCache:
    """Robust cache implementation for voorbeelden generation."""

    def __init__(self, cache_dir: str = "cache/voorbeelden"):
        """Initialize the robust cache.

        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.cache_dir / "metadata.json"
        self._load_metadata()

        # Cache statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def _load_metadata(self):
        """Load cache metadata from disk."""
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
        """Save cache metadata to disk."""
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache metadata: {e}")

    def generate_robust_key(
        self,
        example_type: str,
        begrip: str,
        definitie: str,
        context_dict: dict[str, list] | None = None,
        max_examples: int | None = None,
        model: str | None = None,
        temperature: float | None = None,
        user_preferences: dict | None = None,
    ) -> str:
        """Generate a robust cache key including all relevant parameters.

        Args:
            example_type: Type of examples (e.g., 'synoniemen', 'antoniemen')
            begrip: The term to generate examples for
            definitie: The definition of the term
            context_dict: Context information (organization, legal, etc.)
            max_examples: Maximum number of examples to generate
            model: Model to use for generation
            temperature: Temperature setting for generation
            user_preferences: User-specific preferences

        Returns:
            A deterministic cache key
        """
        # Build key components
        key_parts = [
            CACHE_SCHEMA_VERSION,  # Schema version for invalidation
            example_type,  # Example type
            begrip.lower().strip(),  # Normalized begrip
        ]

        # Hash the definition (it can be long)
        def_hash = hashlib.md5(definitie.encode()).hexdigest()[:16]
        key_parts.append(def_hash)

        # Add max_examples if specified
        if max_examples is not None:
            key_parts.append(f"n{max_examples}")

        # Add model if specified
        if model:
            key_parts.append(model.replace("-", "_"))

        # Add temperature if specified
        if temperature is not None:
            key_parts.append(f"t{int(temperature * 100)}")

        # Hash context if provided
        if context_dict:
            context_str = json.dumps(context_dict, sort_keys=True)
            context_hash = hashlib.md5(context_str.encode()).hexdigest()[:8]
            key_parts.append(f"ctx{context_hash}")

        # Hash user preferences if provided
        if user_preferences:
            pref_str = json.dumps(user_preferences, sort_keys=True)
            pref_hash = hashlib.md5(pref_str.encode()).hexdigest()[:8]
            key_parts.append(f"pref{pref_hash}")

        # Join all parts with pipe separator
        cache_key = "|".join(key_parts)

        # Log cache key generation in debug mode
        if DEBUG_ENABLED:
            logger.debug(f"Generated cache key: {cache_key}")

        return cache_key

    def get(self, cache_key: str) -> Any | None:
        """Retrieve value from cache.

        Args:
            cache_key: The cache key to look up

        Returns:
            Cached value if found and not expired, None otherwise
        """
        # Check if key exists in metadata
        if cache_key not in self.metadata:
            self.misses += 1
            if DEBUG_ENABLED:
                debugger.log_cache_interaction("cache", cache_key, hit=False)
            return None

        # Check if expired
        entry = self.metadata[cache_key]
        stored_time = datetime.fromisoformat(entry["timestamp"])
        ttl = entry.get("ttl", 3600)

        if datetime.now(UTC) > stored_time + timedelta(seconds=ttl):
            # Expired
            self.misses += 1
            self.evictions += 1
            if DEBUG_ENABLED:
                debugger.log_cache_interaction("cache", cache_key, hit=False)
            # Remove expired entry
            del self.metadata[cache_key]
            self._save_metadata()
            return None

        # Load from file
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        if not cache_file.exists():
            self.misses += 1
            if DEBUG_ENABLED:
                debugger.log_cache_interaction("cache", cache_key, hit=False)
            return None

        try:
            with open(cache_file, "rb") as f:
                value = pickle.load(f)
            self.hits += 1
            if DEBUG_ENABLED:
                debugger.log_cache_interaction("cache", cache_key, hit=True, ttl=ttl)
            return value
        except Exception as e:
            logger.error(f"Failed to load cache file {cache_key}: {e}")
            self.misses += 1
            return None

    def set(self, cache_key: str, value: Any, ttl: int | None = None):
        """Store value in cache.

        Args:
            cache_key: The cache key
            value: Value to cache
            ttl: Time-to-live in seconds (optional)
        """
        # Determine TTL
        if ttl is None:
            # Try to extract example type from key
            parts = cache_key.split("|")
            if len(parts) > 1:
                example_type = parts[1]
                ttl = EXAMPLE_TTL_CONFIG.get(example_type, 3600)
            else:
                ttl = 3600  # Default 1 hour

        # Save to file
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        try:
            with open(cache_file, "wb") as f:
                pickle.dump(value, f)

            # Update metadata
            self.metadata[cache_key] = {
                "timestamp": datetime.now(UTC).isoformat(),
                "ttl": ttl,
                "size": cache_file.stat().st_size,
            }
            self._save_metadata()

            if DEBUG_ENABLED:
                logger.debug(f"Cached {cache_key} with TTL {ttl}s")

        except Exception as e:
            logger.error(f"Failed to save cache file {cache_key}: {e}")

    def clear_expired(self):
        """Remove all expired entries from cache."""
        expired_keys = []
        now = datetime.now(UTC)

        for key, entry in self.metadata.items():
            stored_time = datetime.fromisoformat(entry["timestamp"])
            ttl = entry.get("ttl", 3600)

            if now > stored_time + timedelta(seconds=ttl):
                expired_keys.append(key)

        for key in expired_keys:
            # Remove file
            cache_file = self.cache_dir / f"{key}.pkl"
            if cache_file.exists():
                cache_file.unlink()
            # Remove from metadata
            del self.metadata[key]
            self.evictions += 1

        if expired_keys:
            self._save_metadata()
            logger.info(f"Cleared {len(expired_keys)} expired cache entries")

    def get_statistics(self) -> dict:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "hit_rate": f"{hit_rate:.1f}%",
            "total_entries": len(self.metadata),
            "cache_dir": str(self.cache_dir),
        }


# Global cache instance
_cache_instance = None


def get_robust_cache() -> RobustVoorbeeldenCache:
    """Get or create the global cache instance.

    Returns:
        The global RobustVoorbeeldenCache instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RobustVoorbeeldenCache()
    return _cache_instance


def cache_voorbeelden(
    ttl: int | None = None,
    include_context: bool = True,
    include_preferences: bool = True,
):
    """Decorator for caching voorbeelden generation functions.

    Args:
        ttl: Time-to-live in seconds (optional, uses defaults per type)
        include_context: Include context in cache key
        include_preferences: Include user preferences in cache key
    """

    def decorator(func):
        @wraps(func)
        def wrapper(
            begrip: str, definitie: str, context_dict: dict | None = None, **kwargs
        ):
            cache = get_robust_cache()

            # Extract example type from function name or kwargs
            example_type = kwargs.get(
                "example_type", func.__name__.replace("genereer_", "")
            )

            # Generate cache key
            cache_key = cache.generate_robust_key(
                example_type=example_type,
                begrip=begrip,
                definitie=definitie,
                context_dict=context_dict if include_context else None,
                max_examples=kwargs.get("max_examples"),
                model=kwargs.get("model"),
                temperature=kwargs.get("temperature"),
                user_preferences=(
                    kwargs.get("user_preferences") if include_preferences else None
                ),
            )

            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                if DEBUG_ENABLED:
                    logger.debug(f"Cache hit for {example_type}: {begrip}")
                return cached_value

            # Generate new value
            result = func(begrip, definitie, context_dict, **kwargs)

            # Store in cache
            cache.set(cache_key, result, ttl=ttl)

            return result

        return wrapper

    return decorator
