"""
Examples helper: resolve examples (voorbeelden) for UI tabs.

Priority order:
1) Session-scoped examples (already generated/edited in this tab)
2) Definition.metadata.voorbeelden (if present on object)
3) last_generation_result.agent_result.voorbeelden (from Generator tab)
"""

from __future__ import annotations

import re
from typing import Any

from ui.session_state import SessionStateManager


def _to_list(val: Any) -> list[str]:
    if isinstance(val, list):
        return [str(x).strip() for x in val if str(x).strip()]
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return []
        # Support diverse scheiders: komma, puntkomma, pipe, nieuwe regel,
        # en bullet/asterisk/hyphen varianten met spaties eromheen
        parts = re.split(r"(?:,|;|\||\r?\n|\s+[•*\-–—]\s+)+", s)
        out: list[str] = []
        for p in parts:
            t = str(p).strip().lstrip("*•-–— ")
            if t:
                out.append(t)
        return out
    return []


def canonicalize_examples(raw: dict[str, Any] | None) -> dict[str, Any]:
    """Map diverse voorbeeld-type keys naar de canonieke UI-sleutels.

    Returns dict met keys: voorbeeldzinnen, praktijkvoorbeelden, tegenvoorbeelden, synoniemen, antoniemen, toelichting.
    """
    data = raw or {}
    out: dict[str, Any] = {
        "voorbeeldzinnen": [],
        "praktijkvoorbeelden": [],
        "tegenvoorbeelden": [],
        "synoniemen": [],
        "antoniemen": [],
        "toelichting": "",
    }

    # Key aliases per categorie
    aliases = {
        "voorbeeldzinnen": {
            "voorbeeldzinnen",
            "zinnen",
            "voorbeeldzin",
            "sentences",
            "sentence",
            "example_sentences",
        },
        "praktijkvoorbeelden": {
            "praktijkvoorbeelden",
            "praktijk",
            "praktijkvoorbeeld",
            "practical_examples",
            "practical",
        },
        "tegenvoorbeelden": {
            "tegenvoorbeelden",
            "tegen",
            "counterexamples",
            "counter",
        },
        "synoniemen": {"synoniemen", "synonym", "synonyms"},
        "antoniemen": {"antoniemen", "antonym", "antonyms"},
        "toelichting": {"toelichting", "uitleg", "notes", "comment", "explanation"},
    }

    # Lower-case keys for robust matching
    lower_map = {str(k).strip().lower(): v for k, v in (data or {}).items()}

    # Collect lists
    for canon, keys in aliases.items():
        if canon == "toelichting":
            continue
        items: list[str] = []
        for k in keys:
            if k in lower_map:
                items.extend(_to_list(lower_map[k]))
        # de-dup preserve order
        seen: set[str] = set()
        deduped: list[str] = []
        for it in items:
            if it not in seen:
                seen.add(it)
                deduped.append(it)
        out[canon] = deduped

    # Toelichting als string (neem eerste uit lijst indien nodig)
    for k in aliases["toelichting"]:
        if k in lower_map:
            val = lower_map[k]
            if isinstance(val, list):
                out["toelichting"] = str(val[0]).strip() if val else ""
            elif isinstance(val, str):
                out["toelichting"] = val.strip()
            break

    return out


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
                # Canonicaliseer DB-keys naar UI‑canoniek (sentence→voorbeeldzinnen, etc.)
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
