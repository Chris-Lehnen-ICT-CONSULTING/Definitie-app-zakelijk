"""Approval Gate Policy loader and service (US-160 Option B).

Provides a small, self-contained loader for the validation gate policy with:
- YAML config (config/approval_gate.yaml) + optional env overlay
- Sane defaults when config missing/invalid
- Lightweight TTL-based caching for DI container
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, cast

logger = logging.getLogger(__name__)


def _safe_import_yaml():
    try:
        import yaml  # type: ignore

        return yaml
    except Exception as e:  # pragma: no cover - import guard
        msg = f"PyYAML is required for loading approval gate config: {e!s}"
        raise RuntimeError(msg) from e


DEFAULT_POLICY: dict[str, dict[str, Any]] = {
    "hard_requirements": {
        "min_one_context_required": True,
        "forbid_critical_issues": True,
    },
    "thresholds": {
        "hard_min_score": 0.75,
        "soft_min_score": 0.65,
    },
    "soft_requirements": {
        "allow_high_issues_with_override": True,
        "missing_wettelijke_basis_soft": True,
        # Nieuw: sta override toe zelfs bij hard blocks (alleen met gemotiveerde reden)
        "allow_hard_override": False,
    },
    "cache": {
        "ttl_seconds": 60,
    },
}


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Deep-merge two dictionaries (overlay wins)."""

    def _merge(a: Any, b: Any) -> Any:
        if isinstance(a, dict) and isinstance(b, dict):
            result: dict[str, Any] = {}
            for k in set(a.keys()) | set(b.keys()):
                if k in a and k in b:
                    result[k] = _merge(a[k], b[k])
                elif k in b:
                    result[k] = b[k]
                else:
                    result[k] = a[k]
            return result
        return b

    return cast(dict[str, Any], _merge(base, overlay))


@dataclass
class GatePolicy:
    """Typed view on the approval gate policy."""

    hard_requirements: dict[str, Any] = field(
        default_factory=lambda: dict(DEFAULT_POLICY["hard_requirements"])
    )
    thresholds: dict[str, Any] = field(
        default_factory=lambda: dict(DEFAULT_POLICY["thresholds"])
    )
    soft_requirements: dict[str, Any] = field(
        default_factory=lambda: dict(DEFAULT_POLICY["soft_requirements"])
    )
    cache: dict[str, Any] = field(default_factory=lambda: dict(DEFAULT_POLICY["cache"]))

    @property
    def hard_min_score(self) -> float:
        try:
            return float(self.thresholds.get("hard_min_score", 0.75))
        except (TypeError, ValueError):
            # DEF-246: Invalid threshold config, use default
            return 0.75

    @property
    def soft_min_score(self) -> float:
        try:
            return float(self.thresholds.get("soft_min_score", 0.65))
        except (TypeError, ValueError):
            # DEF-246: Invalid threshold config, use default
            return 0.65

    @property
    def ttl_seconds(self) -> int:
        try:
            return int(self.cache.get("ttl_seconds", 60))
        except (TypeError, ValueError):
            # DEF-246: Invalid cache config, use default
            return 60


class GatePolicyService:
    """Service to load and cache the approval gate policy."""

    def __init__(self, base_path: str | None = None):
        # Default to top-level config path used elsewhere in the repo
        self.base_path = base_path or "config/approval_gate.yaml"
        self._cached_policy: GatePolicy | None = None
        self._loaded_at: float | None = None

    def get_policy(self) -> GatePolicy:
        """Return current policy, reloading when TTL expired or not loaded."""
        if self._cached_policy and self._loaded_at is not None:
            ttl = self._cached_policy.ttl_seconds
            if time.time() - self._loaded_at < ttl:
                return self._cached_policy

        policy = self._load_policy()
        self._cached_policy = policy
        self._loaded_at = time.time()
        return policy

    # Internal API
    def _load_policy(self) -> GatePolicy:
        yaml = _safe_import_yaml()

        base_data: dict[str, Any] = {}
        try:
            if os.path.exists(self.base_path):
                with open(self.base_path, encoding="utf-8") as f:
                    base_data = yaml.safe_load(f) or {}
            else:
                logger.warning(
                    "Approval gate config not found at %s - using defaults",
                    self.base_path,
                )
        except Exception as e:
            logger.warning("Invalid approval gate config (%s) - using defaults", e)
            base_data = {}

        # Optional overlay via env var
        overlay_path = os.getenv("APPROVAL_GATE_CONFIG_OVERLAY")
        overlay_data: dict[str, Any] = {}
        if overlay_path and os.path.exists(overlay_path):
            try:
                with open(overlay_path, encoding="utf-8") as f:
                    overlay_data = yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning("Failed to load overlay %s: %s", overlay_path, e)

        merged = _deep_merge(DEFAULT_POLICY, _deep_merge(base_data, overlay_data))
        return GatePolicy(
            hard_requirements=dict(merged.get("hard_requirements", {})),
            thresholds=dict(merged.get("thresholds", {})),
            soft_requirements=dict(merged.get("soft_requirements", {})),
            cache=dict(merged.get("cache", {})),
        )
