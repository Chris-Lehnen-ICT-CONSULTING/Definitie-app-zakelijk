"""
Examples helper: resolve examples (voorbeelden) for UI tabs.

Priority order:
1) Session-scoped examples (already generated/edited in this tab)
2) Definition.metadata.voorbeelden (if present on object)
3) last_generation_result.agent_result.voorbeelden (from Generator tab)
"""

from __future__ import annotations

from typing import Any

from ui.session_state import SessionStateManager

# Import canonicalize_examples from utils (moved for layer separation - DEF-173)
from utils.example_formatters import canonicalize_examples


def resolve_examples(
    state_key: str, definition: Any | None, *, repository: Any | None = None
) -> dict[str, Any]:
    """Return examples dict using common resolution order.

    Args:
        state_key: Session key to read/write current examples (e.g., 'edit_<id>_examples')
        definition: Definition/DefinitieRecord or None

    Returns:
        Dict with keys: voorbeeldzinnen, praktijkvoorbeelden, tegenvoorbeelden, synoniemen, antoniemen, toelichting
    """
    import logging as _logging
    import os as _os

    logger = _logging.getLogger(__name__)
    debug_mode = _os.getenv("DEV_MODE")

    def_id = getattr(definition, "id", None) if definition else None

    # DEF-156 Fix 2C: Debug logging to track resolution path
    if debug_mode:
        logger.debug(
            f"[RESOLVE] Starting voorbeelden resolution for key={state_key}, def_id={def_id}"
        )

    # 1) Session state (al gecanonicaliseerd in eerdere stap of direct opslaan)
    try:
        sess_val = SessionStateManager.get_value(state_key)
        if isinstance(sess_val, dict) and sess_val:
            result = canonicalize_examples(sess_val)
            if debug_mode:
                count = sum(
                    len(v) if isinstance(v, list) else 0 for v in result.values()
                )
                logger.debug(
                    f"[RESOLVE] ✅ Tier 1 (Session): {count} items for {state_key}"
                )
            return result
    except Exception as e:
        if debug_mode:
            logger.debug(f"[RESOLVE] ❌ Tier 1 (Session) failed: {e}")

    # 2) Definition.metadata.voorbeelden
    try:
        if definition is not None and getattr(definition, "metadata", None):
            md = definition.metadata
            if isinstance(md, dict):
                v = md.get("voorbeelden") or {}
                if isinstance(v, dict):
                    canon = canonicalize_examples(v)
                    if any(
                        canon.get(k)
                        for k in (
                            "voorbeeldzinnen",
                            "praktijkvoorbeelden",
                            "tegenvoorbeelden",
                            "synoniemen",
                            "antoniemen",
                            "toelichting",
                        )
                    ):
                        SessionStateManager.set_value(state_key, canon)
                        if debug_mode:
                            count = sum(
                                len(v) if isinstance(v, list) else 0
                                for v in canon.values()
                            )
                            logger.debug(
                                f"[RESOLVE] ✅ Tier 2 (Metadata): {count} items for def_id={def_id}"
                            )
                        return canon
    except Exception as e:
        if debug_mode:
            logger.debug(f"[RESOLVE] ❌ Tier 2 (Metadata) failed: {e}")

    # 3) last_generation_result → agent_result.voorbeelden
    try:
        lgr = SessionStateManager.get_value("last_generation_result")
        if isinstance(lgr, dict):
            ar = lgr.get("agent_result") or {}
            if isinstance(ar, dict):
                v = ar.get("voorbeelden") or {}
                if isinstance(v, dict) and v:
                    canon = canonicalize_examples(v)
                    SessionStateManager.set_value(state_key, canon)
                    if debug_mode:
                        count = sum(
                            len(v) if isinstance(v, list) else 0 for v in canon.values()
                        )
                        logger.debug(
                            f"[RESOLVE] ✅ Tier 3 (Last generation): {count} items"
                        )
                    return canon
    except Exception as e:
        if debug_mode:
            logger.debug(f"[RESOLVE] ❌ Tier 3 (Last generation) failed: {e}")

    # 4) Database fallback via repository (Expert/Edit)
    try:
        if (
            definition is not None
            and hasattr(definition, "id")
            and int(definition.id) > 0
        ):
            # Gebruik meegegeven repository indien beschikbaar, anders shared repo
            if repository is None:
                from database.definitie_repository import get_definitie_repository

                repo = get_definitie_repository()
            else:
                repo = repository
            vdb = repo.get_voorbeelden_by_type(int(definition.id))
            if isinstance(vdb, dict) and any(vdb.values()):
                # Canonicaliseer DB-keys naar UI-canoniek (sentence→voorbeeldzinnen, etc.)
                canon = canonicalize_examples(vdb)
                SessionStateManager.set_value(state_key, canon)
                if debug_mode:
                    count = sum(
                        len(v) if isinstance(v, list) else 0 for v in canon.values()
                    )
                    logger.debug(
                        f"[RESOLVE] ✅ Tier 4 (Database): {count} items for def_id={def_id}"
                    )
                return canon
    except Exception as e:
        if debug_mode:
            logger.debug(f"[RESOLVE] ❌ Tier 4 (Database) failed: {e}")

    if debug_mode:
        logger.debug(
            f"[RESOLVE] ⚠️ No voorbeelden found for {state_key}, def_id={def_id}"
        )

    return {}
