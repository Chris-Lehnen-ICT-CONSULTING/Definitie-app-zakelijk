"""Compatibility adapters for tests expecting config.config_adapters.

Delegates to the top-level config adapters defined in config.__init__.
"""

from __future__ import annotations

from . import (
    get_api_config as _get_api_config,
    get_cache_config as _get_cache_config,
    get_paths_config as _get_paths_config,
)
from .config_manager import (
    get_default_model,
    get_default_temperature,
)


def get_api_config():
    return _get_api_config()


def get_cache_config():
    return _get_cache_config()


def get_paths_config():
    return _get_paths_config()


__all__ = [
    "get_api_config",
    "get_cache_config",
    "get_paths_config",
    "get_default_model",
    "get_default_temperature",
]

