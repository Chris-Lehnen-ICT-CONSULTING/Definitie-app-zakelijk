"""Top-level configuration adapters and helpers.

Provides simple adapter functions expected by tests while delegating to the
central ConfigManager implementation.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

# Legacy loaders kept for back-compat (used by some docs/tools)
from .config_loader import laad_toetsregels, laad_verboden_woorden
from .config_manager import APIConfig
from .config_manager import CacheConfig as _CacheCfg
from .config_manager import ConfigSection
from .config_manager import PathsConfig as _PathsCfg
from .config_manager import ValidationConfig as _ValCfg
from .config_manager import (get_config, get_config_manager, get_default_model,
                             get_default_temperature)


class APIConfigAdapter:
    """Light adapter exposing helper methods around API config."""

    def __init__(self, config: APIConfig):
        self.config = config

    def get_model_config(self, model: str | None = None) -> dict[str, Any]:
        m = model or self.config.default_model
        settings = self.config.model_settings or {}
        entry = settings.get(m)
        if entry:
            return {
                "model": m,
                "temperature": entry.get(
                    "temperature", self.config.default_temperature
                ),
                "max_tokens": entry.get("max_tokens", self.config.default_max_tokens),
            }
        # Fallback to defaults when model not found
        return {
            "model": m,
            "temperature": self.config.default_temperature,
            "max_tokens": self.config.default_max_tokens,
        }

    def get_gpt_call_params(
        self,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        base = self.get_model_config(model)
        # Apply explicit overrides (None preserves defaults)
        if temperature is not None:
            base["temperature"] = temperature
        if max_tokens is not None:
            base["max_tokens"] = max_tokens
        if model is not None:
            base["model"] = model
        # Merge extra parameters
        base.update(kwargs)
        return base

    def ensure_api_key(self) -> str:
        key = self.config.openai_api_key or ""
        if not key:
            # In tests it's acceptable to raise
            raise ValueError("OPENAI_API_KEY not configured")
        return key


class CacheConfigAdapter:
    def __init__(self, config: _CacheCfg):
        self.config = config

    def get_cache_config(self) -> dict[str, Any]:
        return {
            "enabled": bool(self.config.enabled),
            "cache_dir": str(self.config.cache_dir),
            "default_ttl": int(self.config.default_ttl),
            "max_cache_size": int(self.config.max_cache_size),
        }

    def get_operation_ttl(self, name: str) -> int:
        # Map known operations; fall back to default TTL
        mapping = {
            "definition": getattr(
                self.config, "definition_ttl", self.config.default_ttl
            ),
            "examples": getattr(self.config, "examples_ttl", self.config.default_ttl),
            "synonyms": getattr(self.config, "synonyms_ttl", self.config.default_ttl),
            "validation": getattr(
                self.config, "validation_ttl", self.config.default_ttl
            ),
        }
        return int(mapping.get(name, self.config.default_ttl))

    def get_cache_key_prefix(self) -> str:
        return "defapp:"


class PathsConfigAdapter:
    def __init__(self, config: _PathsCfg):
        self.config = config

    def get_directory(self, name: str) -> str:
        mapping = {
            "cache": self.config.cache_dir,
            "exports": self.config.exports_dir,
            "logs": self.config.logs_dir,
            "reports": self.config.reports_dir,
            "config": self.config.config_dir,
            "base": self.config.base_dir,
        }
        return str(mapping.get(name, self.config.base_dir))

    def get_file_path(self, name: str) -> str:
        mapping = {
            "toetsregels": self.config.toetsregels_file,
            "verboden_woorden": self.config.verboden_woorden_file,
            "context_mapping": self.config.context_mapping_file,
            "rate_limit_history": self.config.rate_limit_history_file,
        }
        return str(mapping.get(name, self.config.config_dir))

    def resolve_path(self, path: str) -> str:
        return str(Path(path).resolve())


# Adapter factories expected by tests
def get_api_config() -> APIConfigAdapter:
    return APIConfigAdapter(get_config(ConfigSection.API))


def get_cache_config() -> CacheConfigAdapter:
    return CacheConfigAdapter(get_config(ConfigSection.CACHE))


def get_paths_config() -> PathsConfigAdapter:
    return PathsConfigAdapter(get_config(ConfigSection.PATHS))


def get_openai_api_key() -> str:
    cfg = get_config(ConfigSection.API)
    if not cfg.openai_api_key:
        raise ValueError("OPENAI_API_KEY not configured")
    return cfg.openai_api_key


class ValidationConfigAdapter:
    def __init__(self, config: _ValCfg):
        self.config = config

    def get_validation_limits(self) -> dict[str, int]:
        return {
            "max_text_length": int(getattr(self.config, "max_text_length", 10000)),
        }


def get_validation_config() -> ValidationConfigAdapter:
    return ValidationConfigAdapter(get_config(ConfigSection.VALIDATION))


__all__ = [
    # Legacy
    "laad_toetsregels",
    "laad_verboden_woorden",
    # Adapters
    "get_api_config",
    "get_cache_config",
    "get_paths_config",
    "get_validation_config",
    # Direct config helpers
    "get_config_manager",
    "get_config",
    "get_default_model",
    "get_default_temperature",
    "get_openai_api_key",
]
