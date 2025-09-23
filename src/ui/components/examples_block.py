"""
Shared Examples Block for Edit and Expert tabs.

- Resolves examples via session/metadata/last_generation_result/DB
- Renders lists in the same style as the Edit tab
- Optional: generate examples (AI) in Edit tab
- Optional: edit + save examples to DB in Expert tab
"""

from __future__ import annotations

from typing import Any, Dict

import streamlit as st

from ui.session_state import SessionStateManager
from ui.helpers.examples import resolve_examples


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
    current_examples: Dict[str, Any] = resolve_examples(
        examples_state_key, definition, repository=repository
    )

    # Optional: generate via AI (Edit tab only)
    if allow_generate:
        col_left, col_right = st.columns([1, 1])
        with col_left:
            can_call = True
            import os as _os

            if not (_os.getenv("OPENAI_API_KEY") or _os.getenv("OPENAI_API_KEY_PROD")):
                st.info("ℹ️ Geen OPENAI_API_KEY gevonden — voorbeelden genereren is uitgeschakeld.")
                can_call = False
            if st.button("✨ Genereer voorbeelden (AI)", disabled=not can_call, key=k("gen_examples")):
                try:
                    begrip = SessionStateManager.get_value(k("begrip")) or getattr(definition, "begrip", "") or ""
                    definitie_text = SessionStateManager.get_value(k("definitie")) or getattr(definition, "definitie", "") or ""
                    org_ctx = SessionStateManager.get_value(k("organisatorische_context")) or []
                    jur_ctx = SessionStateManager.get_value(k("juridische_context")) or []
                    wet_ctx = SessionStateManager.get_value(k("wettelijke_basis")) or []

                    context_dict = {
                        "organisatorisch": list(org_ctx),
                        "juridisch": list(jur_ctx),
                        "wettelijk": list(wet_ctx),
                    }

                    with st.spinner("🧠 Voorbeelden genereren met AI..."):
                        from ui.helpers.async_bridge import run_async
                        from voorbeelden.unified_voorbeelden import genereer_alle_voorbeelden_async

                        result = run_async(
                            genereer_alle_voorbeelden_async(
                                begrip=begrip,
                                definitie=definitie_text,
                                context_dict=context_dict,
                            ),
                            timeout=90,
                        )
                        SessionStateManager.set_value(examples_state_key, result or {})
                        current_examples = result or {}
                        st.success("✅ Voorbeelden gegenereerd!")
                except Exception as e:
                    st.error(f"❌ Fout bij genereren voorbeelden: {e}")

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
                st.markdown(f"- {str(it)}")
        else:
            st.info(empty_msg)

    _render_list("📄 Voorbeeldzinnen", "voorbeeldzinnen", "Geen voorbeeldzinnen")
    _render_list("💼 Praktijkvoorbeelden", "praktijkvoorbeelden", "Geen praktijkvoorbeelden")
    _render_list("❌ Tegenvoorbeelden", "tegenvoorbeelden", "Geen tegenvoorbeelden")
    _render_list("🔄 Synoniemen", "synoniemen", "Geen synoniemen")
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

    # Optional: edit + save to DB (Expert tab)
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

            vz = st.text_area(
                "📄 Voorbeeldzinnen (één per regel)",
                value="\n".join(_get_list("voorbeeldzinnen")),
                height=120,
                key=k("vz_edit"),
            )
            pv = st.text_area(
                "💼 Praktijkvoorbeelden (één per regel)",
                value="\n".join(_get_list("praktijkvoorbeelden")),
                height=120,
                key=k("pv_edit"),
            )
            tv = st.text_area(
                "❌ Tegenvoorbeelden (één per regel)",
                value="\n".join(_get_list("tegenvoorbeelden")),
                height=120,
                key=k("tv_edit"),
            )
            syn = st.text_input(
                "🔄 Synoniemen (komma-gescheiden)",
                value=", ".join(_get_list("synoniemen")),
                key=k("syn_edit"),
            )
            ant = st.text_input(
                "↔️ Antoniemen (komma-gescheiden)",
                value=", ".join(_get_list("antoniemen")),
                key=k("ant_edit"),
            )
            tol = st.text_area(
                "📝 Toelichting (korte tekst)",
                value=str(current_examples.get("toelichting") or ""),
                height=80,
                key=k("tol_edit"),
            )

            col_s1, _ = st.columns([1, 3])
            with col_s1:
                if st.button("💾 Voorbeelden opslaan", key=k("save_examples")):
                    try:
                        def _split_lines(text: str) -> list[str]:
                            return [ln.strip() for ln in (text or "").splitlines() if ln.strip()]

                        def _split_csv(text: str) -> list[str]:
                            return [p.strip() for p in (text or "").split(",") if p.strip()]

                        new_examples: dict[str, list[str]] = {
                            "voorbeeldzinnen": _split_lines(vz),
                            "praktijkvoorbeelden": _split_lines(pv),
                            "tegenvoorbeelden": _split_lines(tv),
                            "synoniemen": _split_csv(syn),
                            "antoniemen": _split_csv(ant),
                        }
                        if tol and tol.strip():
                            new_examples["toelichting"] = [tol.strip()]

                        # Persist in DB
                        reviewer = SessionStateManager.get_value("reviewer_name") or "expert"
                        repository.save_voorbeelden(
                            definitie_id=int(definition.id),
                            voorbeelden_dict=new_examples,
                            gegenereerd_door=str(reviewer or "expert"),
                            generation_model="manual",
                            generation_params=None,
                        )

                        # Update session state (flatten explanation back to str)
                        updated = {
                            "voorbeeldzinnen": new_examples.get("voorbeeldzinnen", []),
                            "praktijkvoorbeelden": new_examples.get("praktijkvoorbeelden", []),
                            "tegenvoorbeelden": new_examples.get("tegenvoorbeelden", []),
                            "synoniemen": new_examples.get("synoniemen", []),
                            "antoniemen": new_examples.get("antoniemen", []),
                            "toelichting": tol.strip() if tol and tol.strip() else "",
                        }
                        SessionStateManager.set_value(examples_state_key, updated)
                        st.success("✅ Voorbeelden opgeslagen")
                    except Exception as e:
                        st.error(f"❌ Opslaan mislukt: {e}")
