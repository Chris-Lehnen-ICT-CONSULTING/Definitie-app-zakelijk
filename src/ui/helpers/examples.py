"""
Examples helper: resolve examples (voorbeelden) for UI tabs.

Priority order:
1) Session-scoped examples (already generated/edited in this tab)
2) Definition.metadata.voorbeelden (if present on object)
3) last_generation_result.agent_result.voorbeelden (from Generator tab)
"""

from __future__ import annotations

from typing import Any, Dict

from ui.session_state import SessionStateManager


def resolve_examples(state_key: str, definition: Any | None) -> Dict[str, Any]:
    """Return examples dict using common resolution order.

    Args:
        state_key: Session key to read/write current examples (e.g., 'edit_<id>_examples')
        definition: Definition/DefinitieRecord or None

    Returns:
        Dict with keys: voorbeeldzinnen, praktijkvoorbeelden, tegenvoorbeelden, synoniemen, antoniemen, toelichting
    """
    # 1) Session state
    try:
        sess_val = SessionStateManager.get_value(state_key)
        if isinstance(sess_val, dict) and sess_val:
            return sess_val  # already cached for this tab
    except Exception:
        pass

    # 2) Definition.metadata.voorbeelden
    try:
        if definition is not None and getattr(definition, "metadata", None):
            md = definition.metadata
            if isinstance(md, dict):
                v = md.get("voorbeelden") or {}
                if isinstance(v, dict) and any(
                    v.get(k) for k in (
                        "voorbeeldzinnen",
                        "praktijkvoorbeelden",
                        "tegenvoorbeelden",
                        "synoniemen",
                        "antoniemen",
                        "toelichting",
                    )
                ):
                    SessionStateManager.set_value(state_key, v)
                    return v
    except Exception:
        pass

    # 3) last_generation_result → agent_result.voorbeelden
    try:
        lgr = SessionStateManager.get_value("last_generation_result")
        if isinstance(lgr, dict):
            ar = lgr.get("agent_result") or {}
            if isinstance(ar, dict):
                v = ar.get("voorbeelden") or {}
                if isinstance(v, dict) and v:
                    SessionStateManager.set_value(state_key, v)
                    return v
    except Exception:
        pass

    return {}

