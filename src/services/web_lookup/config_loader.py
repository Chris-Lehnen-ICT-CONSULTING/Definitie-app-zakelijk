"""
Config loader for Web Lookup defaults (Epic 3).
"""

from __future__ import annotations

import logging
import os
from contextlib import suppress
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def load_web_lookup_config(path: str | None = None) -> dict[str, Any]:
    """Load web lookup configuration from YAML.

    Args:
        path: Optional explicit path. Falls back to config/web_lookup_defaults.yaml

    Returns:
        Parsed configuration dictionary.
    """
    if path is None:
        # 1) Explicit env override takes precedence
        if os.getenv("WEB_LOOKUP_CONFIG"):
            path = os.getenv("WEB_LOOKUP_CONFIG")
        else:
            # 2) Prefer development config when present (we operate in dev-only envs)
            dev_path = Path("config") / "web_lookup_development.yaml"
            default_path = Path("config") / "web_lookup_defaults.yaml"
            path = str(dev_path if dev_path.exists() else default_path)

    config_path = Path(path)
    if not config_path.exists():
        msg = f"Web lookup config not found: {config_path}"
        raise FileNotFoundError(msg)

    with config_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    with suppress(Exception):
        logger.info("Web lookup config loaded: %s", config_path)

    return data
