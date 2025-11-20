"""
Shared Examples Block for Edit and Expert tabs.

- Resolves examples via session/metadata/last_generation_result/DB
- Renders lists in the same style as the Edit tab
- Optional: generate examples (AI) in Edit tab
- Optional: edit + save examples to DB in Expert tab
"""

from __future__ import annotations

import contextlib
import logging
import re
from typing import Any

import streamlit as st

from ui.helpers.examples import resolve_examples
from ui.session_state import SessionStateManager, force_cleanup_voorbeelden

logger = logging.getLogger(__name__)

# DEF-56: Configuration for voorbeeld field mappings (single source of truth)
_VOORBEELD_FIELD_CONFIG = [
    # (data_key, widget_suffix, join_separator)
    # join_separator: "\n" for list fields with newlines, ", " for comma-separated, None for string
    ("voorbeeldzinnen", "vz_edit", "\n"),
    ("praktijkvoorbeelden", "pv_edit", "\n"),
    ("tegenvoorbeelden", "tv_edit", "\n"),
    ("synoniemen", "syn_edit", ", "),
    ("antoniemen", "ant_edit", ", "),
    ("toelichting", "tol_edit", None),  # String field, not list
]


def _reset_voorbeelden_context(prefix: str, definition_id: int | None = None) -> None:
    """Reset voorbeelden context when crossing definition boundaries.

    Tracks last synced definition ID and forces cleanup when it changes.
    Handles None IDs correctly using sentinel object comparison.

    Args:
        prefix: Session key prefix (e.g., 'edit_106')
        definition_id: Current definition ID (None for unsaved definitions)

    Business Logic:
        - Tracks last synced definition per prefix
        - Forces cleanup if definition_id changes
        - Uses sentinel object to handle None IDs correctly
        - Prevents stale voorbeelden across definition switches

    Example:
        # Before rendering voorbeelden in Edit tab
        _reset_voorbeelden_context("edit_106", definition_id=106)
        _sync_voorbeelden_to_widgets(voorbeelden, "edit_106")

    DEF-110: Fixes stale voorbeelden bug when switching definitions.
    """
    # Track context per prefix
    context_key = f"{prefix}_context_id"

    # Sentinel for first-time initialization (handles None != None correctly)
    sentinel = object()
    last_definition_id = SessionStateManager.get_value(context_key, sentinel)

    # Force cleanup if context changed
    if last_definition_id is not definition_id:
        force_cleanup_voorbeelden(prefix)
        SessionStateManager.set_value(context_key, definition_id)

        # Debug logging
        logger.debug(
            f"[DEF-110 CONTEXT RESET] {prefix}: {last_definition_id} → {definition_id}"
        )


def _sync_voorbeelden_to_widgets(
    voorbeelden: dict[str, Any],
    prefix: str,
    force_overwrite: bool = False,
    definition_id: int | None = None,
) -> None:
    """Sync voorbeelden dict to Streamlit widget session state keys.

    Handles all voorbeeld fields (voorbeeldzinnen, synoniemen, toelichting, etc.)
    with appropriate formatting (newline-separated lists, comma-separated lists, strings).

    Args:
        voorbeelden: Dict with example fields (voorbeeldzinnen, synoniemen, etc.)
        prefix: Session key prefix (e.g. 'edit_42')
        force_overwrite: If True, overwrite existing widget values (post-generation sync)
                        If False, only initialize unset widgets (pre-widget-declaration sync)
        definition_id: Definition ID for tracking (triggers force resync on change)

    Business Logic:
        - Tracks last synced definition ID per prefix (prevents stale state)
        - Forces resync when definition_id changes (prevents stale data)
        - Preserves user edits within same definition
        - Gebruikt SessionStateManager voor alle session state toegang (VERPLICHT)
        - Formatted output per field type (list vs string, newline vs comma join)
    """

    def k(name: str) -> str:
        return f"{prefix}_{name}"

    # Track last synced definition for this prefix (prevents stale voorbeelden)
    last_synced_key = f"{prefix}_last_synced_id"
    last_synced = SessionStateManager.get_value(last_synced_key, None)

    # Force resync if definition changed (prevents stale state on definition switch)
    # Note: Only track/compare when definition_id is provided to avoid false positives
    if definition_id is not None:
        if last_synced != definition_id:
            force_overwrite = True
            logger.info(
                f"🔄 Definition switch detected ({last_synced} → {definition_id}). "
                f"Forcing voorbeelden resync for prefix '{prefix}'"
            )
        # Update tracking even if no switch detected (idempotent, prevents None→int false positives)
        SessionStateManager.set_value(last_synced_key, definition_id)

    try:
        for field, widget_suffix, join_sep in _VOORBEELD_FIELD_CONFIG:
            widget_key = k(widget_suffix)

            # Skip if already set (unless forcing overwrite) - preserveert user edits
            if not force_overwrite:
                existing = SessionStateManager.get_value(widget_key, None)
                if existing is not None:
                    logger.debug(
                        f"Preserving existing widget value for {widget_key} "
                        f"(def_id={definition_id})"
                    )
                    continue

            val = voorbeelden.get(field, [])

            # Format content based on field type
            if join_sep is None:  # String field (toelichting)
                content = str(val) if val else ""
            elif isinstance(val, list):
                content = join_sep.join(val)
            else:
                content = str(val) if val else ""

            # DEF-56 FIX: Use SessionStateManager (NO direct st.session_state access)
            SessionStateManager.set_value(widget_key, content)

            if force_overwrite:
                logger.debug(f"[SYNC] {widget_key} = '{content[:50]}...'")

    except Exception as e:
        logger.error(
            f"[SYNC ERROR] Failed to sync voorbeelden to widgets: {e}", exc_info=True
        )
        # Re-raise to let caller handle (don't fail silently)
        raise


def render_examples_block(
    definition: Any,
    *,
    state_prefix: str,
    allow_generate: bool = False,
    allow_edit: bool = False,
    repository: Any | None = None,
) -> None:
    """Render the examples block consistently across tabs.

    Args:
        definition: Definition/DefinitieRecord (must have .id)
        state_prefix: Prefix for session keys (e.g. 'edit_42', 'review_42')
        allow_generate: Show AI generation button (Edit tab)
        allow_edit: Show edit form + save to DB (Expert tab)
        repository: Repository with save_voorbeelden() for DB persistence (required when allow_edit)
    """
    if not definition or not getattr(definition, "id", None):
        return

    def k(name: str) -> str:
        return f"{state_prefix}_{name}"

    st.markdown("### 📚 Gegenereerde Content")

    # Resolve current examples (session/metadata/last_generation_result/DB)
    examples_state_key = k("examples")
    current_examples: dict[str, Any] = resolve_examples(
        examples_state_key, definition, repository=repository
    )

    # DEBUG: Log resolved examples (only in dev mode)
    import os as _os

    if _os.getenv("DEV_MODE"):
        logger.debug(
            f"[EXAMPLES] state_key={examples_state_key}, "
            f"counts: vz={len(current_examples.get('voorbeeldzinnen', []))}, "
            f"syn={len(current_examples.get('synoniemen', []))}"
        )

    # Optional: generate via AI (Edit tab only)
    if allow_generate:
        col_left, col_right = st.columns([1, 1])
        with col_left:
            can_call = True
            import os as _os2

            if not (
                _os2.getenv("OPENAI_API_KEY") or _os2.getenv("OPENAI_API_KEY_PROD")
            ):
                st.info(
                    "i Geen OPENAI_API_KEY gevonden — voorbeelden genereren is uitgeschakeld."
                )
                can_call = False
            if st.button(
                "✨ Genereer voorbeelden (AI)",
                disabled=not can_call,
                key=k("gen_examples"),
            ):
                try:
                    begrip = (
                        SessionStateManager.get_value(k("begrip"))
                        or getattr(definition, "begrip", "")
                        or ""
                    )
                    definitie_text = (
                        SessionStateManager.get_value(k("definitie"))
                        or getattr(definition, "definitie", "")
                        or ""
                    )
                    org_ctx = (
                        SessionStateManager.get_value(k("organisatorische_context"))
                        or []
                    )
                    jur_ctx = (
                        SessionStateManager.get_value(k("juridische_context")) or []
                    )
                    wet_ctx = SessionStateManager.get_value(k("wettelijke_basis")) or []

                    context_dict = {
                        "organisatorisch": list(org_ctx),
                        "juridisch": list(jur_ctx),
                        "wettelijk": list(wet_ctx),
                    }

                    with st.spinner("🧠 Voorbeelden genereren met AI (max 90s)..."):
                        from ui.helpers.async_bridge import run_async
                        from voorbeelden.unified_voorbeelden import (
                            genereer_alle_voorbeelden_async,
                        )

                        result = run_async(
                            genereer_alle_voorbeelden_async(
                                begrip=begrip,
                                definitie=definitie_text,
                                context_dict=context_dict,
                            ),
                            timeout=90,
                        )

                        if not result:
                            st.error(
                                "❌ Geen voorbeelden gegenereerd. Controleer logs."
                            )
                            logger.error(
                                f"[GENERATE] genereer_alle_voorbeelden_async returned empty for term: {begrip}"
                            )
                            return

                        # DEBUG: Log generated result (only in dev mode)
                        if _os.getenv("DEV_MODE"):
                            logger.debug(f"[GENERATE] Generated {len(result)} fields")

                        # STAP 1: Update session state met generated voorbeelden
                        SessionStateManager.set_value(examples_state_key, result)
                        current_examples = result

                        # DEF-56 FIX: FORCE sync naar widget keys VOOR st.rerun()
                        # Safety measure voor Streamlit widget state race condition
                        _sync_voorbeelden_to_widgets(
                            result,
                            state_prefix,
                            force_overwrite=True,
                            definition_id=getattr(definition, "id", None),
                        )
                        logger.info("[GENERATE] Completed sync to widget keys")

                        st.success("✅ Voorbeelden gegenereerd!")

                        # Rerun to refresh UI and populate edit fields with generated examples
                        st.rerun()

                except TimeoutError:
                    st.error(
                        "⏱️ Timeout: Voorbeelden generatie duurde langer dan 90 seconden"
                    )
                    logger.error(
                        f"[GENERATE] Timeout during voorbeelden generation for term: {begrip}"
                    )
                except Exception as e:
                    st.error(f"❌ Fout bij genereren voorbeelden: {e}")
                    logger.exception(
                        "[GENERATE] Exception during voorbeelden generation"
                    )

        with col_right:
            if st.checkbox("🔍 Debug: Voorbeelden Content", key=k("debug_examples")):
                st.code(current_examples)

    # Render lists (Edit tab style)
    def _render_list(title: str, key_name: str, empty_msg: str = "—"):
        st.markdown(f"#### {title}")
        items = []
        try:
            val = current_examples.get(key_name)
            if isinstance(val, list):
                items = val
        except Exception:
            items = []
        if items:
            for it in items:
                st.markdown(f"- {it!s}")
        else:
            st.info(empty_msg)

    _render_list("📄 Voorbeeldzinnen", "voorbeeldzinnen", "Geen voorbeeldzinnen")
    _render_list(
        "💼 Praktijkvoorbeelden", "praktijkvoorbeelden", "Geen praktijkvoorbeelden"
    )
    _render_list("❌ Tegenvoorbeelden", "tegenvoorbeelden", "Geen tegenvoorbeelden")

    # Special handling for synoniemen with voorkeursterm
    st.markdown("#### 🔄 Synoniemen")
    synoniemen = []
    voorkeursterm_display = None  # Waarde uit DB (synoniem met is_voorkeursterm=True)
    voorkeursterm_render = (
        None  # Waarde voor weergave (DB of session fallback, kan ook begrip zijn)
    )

    try:
        val = current_examples.get("synoniemen")
        if isinstance(val, list):
            synoniemen = val
    except Exception:
        synoniemen = []

    # Get voorkeursterm from DB if available
    if repository is not None and definition.id:
        with contextlib.suppress(Exception):
            voorkeursterm_display = repository.get_voorkeursterm(definition.id)

    # Fallback naar session-keuze voor directe feedback (zoals generator-tab)
    try:
        sess_vt = SessionStateManager.get_value("voorkeursterm", "")
    except Exception:
        sess_vt = ""

    begrip = getattr(definition, "begrip", "") or ""
    # Kies render-waarde: DB > session
    if voorkeursterm_display:
        voorkeursterm_render = voorkeursterm_display
    elif sess_vt:
        voorkeursterm_render = str(sess_vt)

    # Toon actuele voorkeursterm boven de lijst (ook als dit het begrip is)
    if voorkeursterm_render:
        if begrip and voorkeursterm_render == begrip:
            st.success(f"✅ Huidige voorkeursterm: {begrip}")
        else:
            st.success(f"✅ Huidige voorkeursterm: {voorkeursterm_render}")

    if synoniemen:
        for syn in synoniemen:
            # Markeer voorkeursterm in de lijst (DB-waarde of session fallback)
            if syn == (voorkeursterm_render or voorkeursterm_display):
                st.markdown(f"- {syn} ⭐ *(voorkeursterm)*")
            else:
                st.markdown(f"- {syn}")
    else:
        st.info("Geen synoniemen")

    _render_list("↔️ Antoniemen", "antoniemen", "Geen antoniemen")

    st.markdown("#### 📝 Toelichting")
    toel = ""
    try:
        val = current_examples.get("toelichting")
        toel = val if isinstance(val, str) else ""
    except Exception:
        toel = ""
    if toel:
        st.info(toel)
    else:
        st.info("Geen toelichting")

    # Optional: edit + save to DB (Expert tab / Edit tab)
    if allow_edit and repository is not None:
        # Let op: deze sectie kan binnen een ouder-expander staan (Expert-tab
        # gebruikt "📋 Definitie Details"). Streamlit staat geen geneste
        # expanders toe, dus gebruik een container i.p.v. een expander.
        with st.container():
            st.markdown("#### ✏️ Bewerk Voorbeelden")
            # Prefill from DB if needed
            if not current_examples:
                try:
                    db_examples = repository.get_voorbeelden_by_type(definition.id)
                    if isinstance(db_examples, dict) and db_examples:
                        current_examples = db_examples
                        SessionStateManager.set_value(examples_state_key, db_examples)
                except Exception:
                    pass

            def _get_list(name: str) -> list[str]:
                val = current_examples.get(name)
                if isinstance(val, list):
                    return val
                if isinstance(val, str) and val.strip():
                    return [s.strip() for s in val.split(",") if s.strip()]
                return []

            # DEF-56 FIX: Sync voorbeelden naar widget keys VOOR declaratie
            # Dit zorgt dat widgets auto-syncen met session state na st.rerun()
            _sync_voorbeelden_to_widgets(
                current_examples,
                state_prefix,
                force_overwrite=False,
                definition_id=getattr(definition, "id", None),
            )

            # DEF-56 FIX: Gebruik ALLEEN key parameter (geen value)
            # Streamlit widgets met key auto-syncen met session state
            vz = st.text_area(
                "📄 Voorbeeldzinnen (één per regel)",
                height=120,
                key=k("vz_edit"),
                help="Positieve voorbeelden (één per regel)",
            )
            pv = st.text_area(
                "💼 Praktijkvoorbeelden (één per regel)",
                height=120,
                key=k("pv_edit"),
                help="Praktische toepassingsvoorbeelden",
            )
            tv = st.text_area(
                "❌ Tegenvoorbeelden (één per regel)",
                height=120,
                key=k("tv_edit"),
                help="Negatieve voorbeelden (incorrect gebruik)",
            )
            syn = st.text_input(
                "🔄 Synoniemen (komma-gescheiden)",
                key=k("syn_edit"),
                help="Alternatieve termen (gescheiden door komma's)",
            )

            # Voorkeursterm selector voor Expert Review en Edit tabs
            def _split_synonyms(text: str) -> list[str]:
                parts = re.split(r"(?:,|;|\||\r?\n|\s+[•*\--—]\s+)+", text or "")
                out: list[str] = []
                for p in parts:
                    t = str(p).strip().lstrip("*•--— ")
                    if t:
                        out.append(t)
                return out

            synoniemen_list = _split_synonyms(syn or "")
            current_voorkeursterm = None

            # Get current voorkeursterm from DB
            if repository is not None and definition.id:
                with contextlib.suppress(Exception):
                    current_voorkeursterm = repository.get_voorkeursterm(definition.id)

            selected_voorkeursterm = None
            # Toon selector als er synoniemen zijn, met zelfde gedrag als Generator-tab:
            # opties: Geen, begrip zelf, en alle synoniemen
            if synoniemen_list:
                begrip = getattr(definition, "begrip", "") or ""

                # Deduplicate while preserving order (na 'Geen voorkeursterm')
                voorkeursterm_options = ["Geen voorkeursterm"]
                seen: set[str] = set()
                for term in ([begrip] if begrip else []) + synoniemen_list:
                    if term and term not in seen:
                        voorkeursterm_options.append(term)
                        seen.add(term)

                # Bepaal default selectie: DB → session → geen
                default_index = 0
                try:
                    target = None
                    if current_voorkeursterm:
                        target = current_voorkeursterm
                    else:
                        sess_vt = SessionStateManager.get_value("voorkeursterm", "")
                        target = sess_vt or None
                    if target and target in voorkeursterm_options:
                        default_index = voorkeursterm_options.index(target)
                except Exception:
                    default_index = 0

                selected = st.selectbox(
                    "⭐ Voorkeursterm selecteren",
                    options=voorkeursterm_options,
                    index=min(max(default_index, 0), len(voorkeursterm_options) - 1),
                    key=k("voorkeursterm_select"),
                    help="Selecteer de voorkeurs-term (kan ook het begrip zelf zijn)",
                )

                # Normaliseer selectie
                if selected == "Geen voorkeursterm":
                    selected_voorkeursterm = None
                else:
                    selected_voorkeursterm = selected

                # Houd de keuze ook bij in de (globale) session state net als in generator-tab
                with contextlib.suppress(Exception):
                    SessionStateManager.set_value(
                        "voorkeursterm", selected_voorkeursterm or ""
                    )

            # DEF-56 FIX: Antoniemen en Toelichting ook zonder value parameter
            ant = st.text_input(
                "↔️ Antoniemen (komma-gescheiden)",
                key=k("ant_edit"),
                help="Tegenovergestelde termen (gescheiden door komma's)",
            )

            tol = st.text_area(
                "📝 Toelichting (korte tekst)",
                height=80,
                key=k("tol_edit"),
                help="Uitleg over het begrip en gebruik",
            )

            col_s1, _ = st.columns([1, 3])
            with col_s1:
                if st.button("💾 Voorbeelden opslaan", key=k("save_examples")):
                    try:

                        def _split_lines(text: str) -> list[str]:
                            return [
                                ln.strip()
                                for ln in (text or "").splitlines()
                                if ln.strip()
                            ]

                        def _split_csv(text: str) -> list[str]:
                            return _split_synonyms(text or "")

                        new_examples: dict[str, list[str]] = {
                            "voorbeeldzinnen": _split_lines(vz),
                            "praktijkvoorbeelden": _split_lines(pv),
                            "tegenvoorbeelden": _split_lines(tv),
                            "synoniemen": _split_csv(syn),
                            "antoniemen": _split_csv(ant),
                        }
                        if tol and tol.strip():
                            new_examples["toelichting"] = [tol.strip()]

                        # Persist in DB with voorkeursterm
                        from pydantic import ValidationError

                        from models.voorbeelden_validation import (
                            validate_save_voorbeelden_input,
                        )

                        reviewer = (
                            SessionStateManager.get_value("reviewer_name") or "expert"
                        )

                        try:
                            # DEF-74: Validate input before saving
                            validated = validate_save_voorbeelden_input(
                                definitie_id=int(definition.id),
                                voorbeelden_dict=new_examples,
                                gegenereerd_door=str(reviewer or "expert"),
                                generation_model="manual",
                                generation_params=None,
                                voorkeursterm=selected_voorkeursterm,
                            )
                            repository.save_voorbeelden(**validated.model_dump())
                        except ValidationError as e:
                            logger.error(f"Voorbeelden validation failed: {e}")
                            st.error("⚠️ Ongeldige voorbeelden - controleer invoer")
                            raise

                        # Update session state (flatten explanation back to str)
                        updated = {
                            "voorbeeldzinnen": new_examples.get("voorbeeldzinnen", []),
                            "praktijkvoorbeelden": new_examples.get(
                                "praktijkvoorbeelden", []
                            ),
                            "tegenvoorbeelden": new_examples.get(
                                "tegenvoorbeelden", []
                            ),
                            "synoniemen": new_examples.get("synoniemen", []),
                            "antoniemen": new_examples.get("antoniemen", []),
                            "toelichting": tol.strip() if tol and tol.strip() else "",
                        }
                        SessionStateManager.set_value(examples_state_key, updated)
                        st.success("✅ Voorbeelden opgeslagen")
                    except Exception as e:
                        st.error(f"❌ Opslaan mislukt: {e}")
