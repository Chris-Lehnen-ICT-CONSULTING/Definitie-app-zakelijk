"""
Config loader for Web Lookup defaults (Epic 3).

Performance Optimization:
    This module uses functools.lru_cache to eliminate redundant disk reads.
    During startup, load_web_lookup_config() is called 3x from different services.
    Without caching: 3 disk reads (~30-50ms waste)
    With caching: 1 disk read, 2 cache hits (~0ms)

Implementation:
    - _resolve_config_path(): Normalizes path to absolute string
    - _load_config_from_path(): Cached loader (maxsize=4)
    - load_web_lookup_config(): Public API that combines both

Cache Behavior:
    - First call: Reads from disk, caches result
    - Subsequent calls: Returns cached dict (same object reference)
    - Path normalization ensures cache hits for None vs explicit path
    - Cache persists for entire Python process lifetime
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def _resolve_config_path(path: str | None = None) -> str:
    """
    Resolve the config path to an absolute path string.

    This function is separated to ensure consistent path resolution
    before caching occurs.

    Args:
        path: Optional explicit path. Falls back to config/web_lookup_defaults.yaml

    Returns:
        Absolute path as string.
    """
    if path is None:
        # Highest priority: explicit override via env var, fallback to default
        override = os.getenv("WEB_LOOKUP_CONFIG")
        path = override or str(Path("config") / "web_lookup_defaults.yaml")

    # Resolve to absolute path for consistent caching
    return str(Path(path).resolve())


@lru_cache(maxsize=4)  # Cache up to 4 different config paths
def _load_config_from_path(resolved_path: str) -> dict[str, Any]:
    """
    Internal cached loader that loads config from a resolved path.

    Args:
        resolved_path: Absolute path to config file.

    Returns:
        Parsed configuration dictionary.
    """
    config_path = Path(resolved_path)

    if not config_path.exists():
        msg = f"Web lookup config not found: {config_path}"
        raise FileNotFoundError(msg)

    # Log only on actual disk read (first time for this path)
    logger.info("📖 Loading web lookup config from disk: %s", config_path)

    with config_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    logger.info("✅ Web lookup config loaded and cached: %d sections", len(data))

    return data


def load_web_lookup_config(path: str | None = None) -> dict[str, Any]:
    """
    Load web lookup configuration from YAML with caching.

    Uses LRU cache to ensure config is loaded from disk only once per path.
    Cache is process-wide and persists across multiple calls.

    Args:
        path: Optional explicit path. Falls back to config/web_lookup_defaults.yaml

    Returns:
        Parsed configuration dictionary.

    Note:
        Path is normalized to absolute path before caching to ensure cache hits
        even with different path formats (e.g., None vs explicit path).
    """
    resolved_path = _resolve_config_path(path)
    return _load_config_from_path(resolved_path)


def clear_config_cache() -> None:
    """
    Clear the web lookup config cache.

    Useful for testing or when config file is modified at runtime.
    """
    _load_config_from_path.cache_clear()
    logger.info("Web lookup config cache cleared")
