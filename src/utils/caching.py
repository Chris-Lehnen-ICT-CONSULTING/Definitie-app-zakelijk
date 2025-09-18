"""
Performance caching utilities for validation and other expensive operations.
"""

import functools
import hashlib
import json
import logging
import time
from typing import Any, Callable, Optional

import streamlit as st

logger = logging.getLogger(__name__)


def cache_validation_results(ttl: int = 300):
    """
    Decorator voor caching validation results.

    Args:
        ttl: Time-to-live in seconden (default 5 minuten)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Genereer cache key gebaseerd op functie naam en argumenten
            cache_key = _generate_cache_key(func.__name__, args, kwargs)

            # Check Streamlit session state cache
            if 'validation_cache' not in st.session_state:
                st.session_state.validation_cache = {}

            cache = st.session_state.validation_cache

            # Check of resultaat in cache zit en nog geldig is
            if cache_key in cache:
                cached_result, timestamp = cache[cache_key]
                if time.time() - timestamp < ttl:
                    logger.debug(f"Cache hit voor {func.__name__} (key: {cache_key[:8]}...)")
                    return cached_result

            # Voer functie uit en cache resultaat
            logger.debug(f"Cache miss voor {func.__name__}, uitvoeren...")
            result = func(*args, **kwargs)
            cache[cache_key] = (result, time.time())

            # Cleanup oude cache entries
            _cleanup_cache(cache, ttl)

            return result
        return wrapper
    return decorator


@st.cache_data(ttl=600)
def get_cached_validation_rules():
    """
    Get validation rules met Streamlit native caching.

    Returns:
        List van validation rules
    """
    from toetsregels.toetsregel_manager import get_toetsregel_manager

    logger.info("Loading validation rules into cache...")
    manager = get_toetsregel_manager()
    rules = manager.get_all_rules() if manager else []
    logger.info(f"Cached {len(rules)} validation rules")
    return rules


@st.cache_data(ttl=300)
def process_validation_results(validation_details: dict) -> dict:
    """
    Process validation results met caching.

    Args:
        validation_details: Raw validation details dict

    Returns:
        Processed validation results
    """
    if not validation_details:
        return {
            "overall_score": 0.0,
            "violations": [],
            "passed_rules": [],
            "summary": {}
        }

    # Process violations voor UI rendering
    processed_violations = []
    for violation in validation_details.get("violations", []):
        processed_violations.append({
            "rule_id": violation.get("rule_id", "unknown"),
            "severity": violation.get("severity", "low"),
            "description": violation.get("description", ""),
            "suggestion": violation.get("suggestion", "")
        })

    # Process passed rules
    processed_passed = []
    for rule in validation_details.get("passed_rules", []):
        if isinstance(rule, dict):
            processed_passed.append({
                "rule_id": rule.get("rule_id", "unknown"),
                "name": rule.get("name", "")
            })
        else:
            processed_passed.append({"rule_id": str(rule), "name": str(rule)})

    return {
        "overall_score": float(validation_details.get("overall_score", 0.0)),
        "violations": processed_violations,
        "passed_rules": processed_passed,
        "summary": validation_details.get("summary", {})
    }


def _generate_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """
    Genereer unieke cache key voor functie call.

    Args:
        func_name: Naam van de functie
        args: Positional arguments
        kwargs: Keyword arguments

    Returns:
        Hexadecimal cache key string
    """
    # Converteer args en kwargs naar JSON string voor hashing
    key_data = {
        "func": func_name,
        "args": _make_hashable(args),
        "kwargs": _make_hashable(kwargs)
    }

    key_string = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_string.encode()).hexdigest()


def _make_hashable(obj: Any) -> Any:
    """
    Maak object hashable voor cache key generatie.

    Args:
        obj: Object om hashable te maken

    Returns:
        Hashable representatie
    """
    if isinstance(obj, dict):
        return tuple(sorted((k, _make_hashable(v)) for k, v in obj.items()))
    elif isinstance(obj, list):
        return tuple(_make_hashable(item) for item in obj)
    elif isinstance(obj, set):
        return tuple(sorted(_make_hashable(item) for item in obj))
    elif hasattr(obj, "__dict__"):
        return _make_hashable(obj.__dict__)
    else:
        return obj


def _cleanup_cache(cache: dict, ttl: int):
    """
    Verwijder verlopen cache entries.

    Args:
        cache: Cache dictionary
        ttl: Time-to-live in seconden
    """
    current_time = time.time()
    expired_keys = [
        key for key, (_, timestamp) in cache.items()
        if current_time - timestamp > ttl
    ]

    for key in expired_keys:
        del cache[key]

    if expired_keys:
        logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")


class ValidationCache:
    """
    Singleton cache manager voor validation operations.
    """

    _instance: Optional["ValidationCache"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._cache = {}
            self._ttl = 300  # 5 minuten default
            self._initialized = True

    def get(self, key: str) -> Optional[Any]:
        """Get cached value als nog geldig."""
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self._ttl:
                return value
            else:
                del self._cache[key]
        return None

    def set(self, key: str, value: Any):
        """Set cache value met timestamp."""
        self._cache[key] = (value, time.time())
        self._cleanup()

    def clear(self):
        """Clear alle cache entries."""
        self._cache.clear()

    def _cleanup(self):
        """Verwijder verlopen entries."""
        current_time = time.time()
        expired = [
            k for k, (_, ts) in self._cache.items()
            if current_time - ts > self._ttl
        ]
        for key in expired:
            del self._cache[key]


# Global cache instance
validation_cache = ValidationCache()