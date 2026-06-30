"""Validation configuration loading and helpers for ModularValidationService.

Provides a small, self-contained config system with:
- ValidationConfig dataclass with YAML loading helper (from_yaml)
- Basic validation of a raw config dictionary (validate_config)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _safe_import_yaml() -> Any:
    try:
        import yaml  # type: ignore

        return yaml
    except Exception as e:  # pragma: no cover - import guard
        msg = f"PyYAML is required for loading validation config: {e!s}"
        raise RuntimeError(msg) from e


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
