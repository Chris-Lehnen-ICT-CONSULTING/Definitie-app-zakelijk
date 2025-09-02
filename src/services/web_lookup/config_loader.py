"""
Config loader for Web Lookup defaults (Epic 3).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


def load_web_lookup_config(path: str | None = None) -> dict[str, Any]:
    """Load web lookup configuration from YAML.

    Args:
        path: Optional explicit path. Falls back to config/web_lookup_defaults.yaml

    Returns:
        Parsed configuration dictionary.
    """
    if path is None:
        # Default relative to project root
        path = os.getenv(
            "WEB_LOOKUP_CONFIG",
            str(Path("config") / "web_lookup_defaults.yaml"),
        )

    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Web lookup config not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return data
