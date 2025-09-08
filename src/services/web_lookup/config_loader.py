"""
Config loader for Web Lookup defaults (Epic 3).
"""

from __future__ import annotations

import contextlib
import logging
import os
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
        # Highest priority: explicit override via env var
        override = os.getenv("WEB_LOOKUP_CONFIG")
        if override:
            path = override
        else:
            # Default application config
            path = str(Path("config") / "web_lookup_defaults.yaml")

    config_path = Path(path)
    if not config_path.exists():
        msg = f"Web lookup config not found: {config_path}"
        raise FileNotFoundError(msg)

    with config_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    with contextlib.suppress(Exception):
        logger.info("Web lookup config loaded: %s", config_path)

    return data
