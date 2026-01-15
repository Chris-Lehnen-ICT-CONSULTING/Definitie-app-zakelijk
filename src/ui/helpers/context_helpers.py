"""Context helper functions for UI components.

Shared utilities for working with global context state.
Consolidates duplicate implementations from definition_generator_tab.py
and duplicate_check_renderer.py (DEF-260).
"""

from __future__ import annotations

import logging

from ui.session_state import SessionStateManager
from utils.type_helpers import ensure_dict

logger = logging.getLogger(__name__)


def get_global_context_lists() -> dict[str, list[str]]:
    """Read global UI context and normalize to lists.

    Returns:
        Dict with keys: organisatorische_context, juridische_context, wettelijke_basis
    """
    try:
        ctx = ensure_dict(SessionStateManager.get_value("global_context", {}))
    except Exception as e:
        logger.error(f"Failed to load global_context from session: {e}")
        ctx = {}
    org_list = ctx.get("organisatorische_context", []) or []
    jur_list = ctx.get("juridische_context", []) or []
    wet_list = ctx.get("wettelijke_basis", []) or []
    return {
        "organisatorische_context": list(org_list),
        "juridische_context": list(jur_list),
        "wettelijke_basis": list(wet_list),
    }


def has_min_one_context() -> bool:
    """Check if at least one context field has a value.

    Returns:
        True if any of org/jur/wet context lists have values
    """
    try:
        ctx = get_global_context_lists()
        return bool(
            ctx.get("organisatorische_context")
            or ctx.get("juridische_context")
            or ctx.get("wettelijke_basis")
        )
    except Exception as e:
        logger.error(f"Context validation check crashed: {e}")
        return False
