"""Validation configuration loading and helpers for ModularValidationService.

Provides a small, self-contained config system with:
- ValidationConfig dataclass with YAML loading helpers
- Environment overlay support via VALIDATION_CONFIG_OVERLAY
- Basic validation and deep-merge utilities
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


def _safe_import_yaml():
    try:
        import yaml  # type: ignore

        return yaml
    except Exception as e:  # pragma: no cover - import guard
        raise RuntimeError(f"PyYAML is required for loading validation config: {e!s}")


@dataclass
class ValidationConfig:
    """Typed configuration for modular validation.

    Fields map directly to YAML structure and are intentionally permissive.
    """

    enabled_codes: list[str] = field(default_factory=list)
    weights: dict[str, float] = field(default_factory=dict)
    thresholds: dict[str, Any] = field(
        default_factory=lambda: {"overall_accept": 0.75, "category_min": {}}
    )
    params: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: str) -> ValidationConfig:
        yaml = _safe_import_yaml()
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        # Basic normalization: accept None sections gracefully
        enabled = list(data.get("enabled_codes") or [])
        weights = dict(data.get("weights") or {})
        thresholds = dict(data.get("thresholds") or {})
        params = dict(data.get("params") or {})
        return cls(
            enabled_codes=enabled, weights=weights, thresholds=thresholds, params=params
        )

    @classmethod
    def from_yaml_with_fallback(cls, path: str) -> ValidationConfig:
        try:
            return cls.from_yaml(path)
        except Exception:
            # Fallback to defaults if file is unreadable/invalid
            default = get_default_config()
            return cls(
                enabled_codes=default.enabled_codes,
                weights=default.weights,
                thresholds=default.thresholds,
                params=default.params,
            )


def deep_merge_configs(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Deep-merge two dictionaries (overlay wins)."""

    def _merge(a: Any, b: Any) -> Any:
        if isinstance(a, dict) and isinstance(b, dict):
            result: dict[str, Any] = {}
            # Union of keys
            for k in set(a.keys()) | set(b.keys()):
                if k in a and k in b:
                    result[k] = _merge(a[k], b[k])
                elif k in b:
                    result[k] = b[k]
                else:
                    result[k] = a[k]
            return result
        # For non-dicts (lists, scalars) the overlay fully replaces base
        return b

    return _merge(base, overlay)


def load_with_env_overlay(base_path: str) -> ValidationConfig:
    """Load base YAML and optionally deep-merge overlay from env var path."""
    yaml = _safe_import_yaml()
    base_cfg = ValidationConfig.from_yaml_with_fallback(base_path)

    overlay_path = os.getenv("VALIDATION_CONFIG_OVERLAY")
    if not overlay_path or not os.path.exists(overlay_path):
        return base_cfg

    try:
        with open(overlay_path, encoding="utf-8") as f:
            overlay_data = yaml.safe_load(f) or {}
    except Exception:
        return base_cfg

    merged = deep_merge_configs(
        {
            "enabled_codes": base_cfg.enabled_codes,
            "weights": base_cfg.weights,
            "thresholds": base_cfg.thresholds,
            "params": base_cfg.params,
        },
        overlay_data,
    )
    return ValidationConfig(
        enabled_codes=list(merged.get("enabled_codes", [])),
        weights=dict(merged.get("weights", {})),
        thresholds=dict(merged.get("thresholds", {})),
        params=dict(merged.get("params", {})),
    )


def validate_config(cfg: dict[str, Any]) -> list[str]:
    """Validate a raw configuration dictionary.

    Returns list of human-readable error messages; empty means valid.
    """
    errors: list[str] = []

    enabled = set(cfg.get("enabled_codes", []) or [])
    weights: dict[str, Any] = cfg.get("weights", {}) or {}
    thresholds: dict[str, Any] = cfg.get("thresholds", {}) or {}

    # Validate weights in [0.0, 1.0]
    for k, v in weights.items():
        try:
            val = float(v)
        except Exception:
            errors.append(f"weight for {k} must be a number")
            continue
        if not (0.0 <= val <= 1.0):
            errors.append(f"weight {k} out of range [0,1]: {val}")
        if enabled and k not in enabled:
            errors.append(f"weight provided for disabled code: {k}")

    # Validate thresholds
    if "overall_accept" in thresholds:
        try:
            oa = float(thresholds["overall_accept"])  # type: ignore[index]
            if not (0.0 <= oa <= 1.0):
                errors.append(f"threshold overall_accept out of range [0,1]: {oa}")
        except Exception:
            errors.append("threshold overall_accept must be a number")

    # Validate category_min map if present
    cat_min = thresholds.get("category_min") or {}
    if isinstance(cat_min, dict):
        for cat, v in cat_min.items():
            try:
                val = float(v)
            except Exception:
                errors.append(f"category_min for {cat} must be a number")
                continue
            if not (0.0 <= val <= 1.0):
                errors.append(f"category_min {cat} out of range [0,1]: {val}")

    return errors


def get_default_config() -> ValidationConfig:
    """Return conservative default configuration.

    These defaults are intentionally minimal and safe.
    """
    return ValidationConfig(
        enabled_codes=[
            "ESS-01",
            "CON-01",
            "STR-01",
        ],
        weights={
            "ESS-01": 1.0,
            "CON-01": 0.8,
            "STR-01": 0.6,
        },
        thresholds={"overall_accept": 0.75, "category_min": {}},
        params={},
    )


def extract_v1_config(v1_validator: Any) -> dict[str, Any]:
    """Extract a config-like dict from a V1 validator instance.

    This is best-effort and tolerant of missing attributes as it is only used
    for parity/exploration in tests.
    """
    weights = getattr(v1_validator, "rule_weights", {}) or {}
    overall = getattr(v1_validator, "min_score", None)
    category_thresholds = getattr(v1_validator, "category_thresholds", {}) or {}

    thresholds: dict[str, Any] = {}
    if overall is not None:
        thresholds["overall_accept"] = overall
    if category_thresholds:
        thresholds["category_min"] = dict(category_thresholds)

    return {
        "enabled_codes": list(weights.keys()) if weights else [],
        "weights": dict(weights),
        "thresholds": thresholds or {"overall_accept": 0.75},
    }
