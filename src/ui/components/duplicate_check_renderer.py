"""Duplicate Check Renderer - Renders duplicate check results with actions.

Extracted from definition_generator_tab.py to reduce God Class complexity.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import streamlit as st

from integration.definitie_checker import CheckAction
from ui.components.formatters import format_record_context
from ui.session_state import SessionStateManager
from utils.type_helpers import ensure_dict

if TYPE_CHECKING:
    from database.definitie_repository import DefinitieRecord
    from integration.definitie_checker import CheckResult

logger = logging.getLogger(__name__)


def _has_min_one_context() -> bool:
    """Check if at least one context field has a value.

    This is a standalone helper to avoid dependency on the main tab class.
    """
    try:
        ctx = ensure_dict(SessionStateManager.get_value("global_context", {}))
        org_list = ctx.get("organisatorische_context", []) or []
        jur_list = ctx.get("juridische_context", []) or []
        wet_list = ctx.get("wettelijke_basis", []) or []
        return bool(org_list or jur_list or wet_list)
    except Exception as e:
        logger.error(f"Context validation check crashed: {e}")
        return False


class DuplicateCheckRenderer:
    """Renders duplicate check results with interactive actions.

    This component handles:
    - Displaying duplicate check results (PROCEED/USE_EXISTING/etc)
    - Showing existing definition details with action buttons
    - Rendering list of potential duplicates
    - Navigation actions (use existing, edit, generate new)
    """

    def render_check_results(self, check_result: CheckResult) -> None:
        """Render complete duplicate check results section.

        Displays:
        - Main result message (PROCEED/USE_EXISTING/etc)
        - Confidence indicator with color coding
        - Existing definition details (if found)
        - Duplicate matches list (if any)

        Args:
            check_result: Result from DefinitieChecker.check_for_duplicates()
        """
        st.markdown("### 🔍 Duplicate Check Resultaten")

        # Main result
        if check_result.action == CheckAction.PROCEED:
            st.success(f"✅ {check_result.message}")
        elif check_result.action == CheckAction.USE_EXISTING:
            st.warning(f"⚠️ {check_result.message}")
        else:
            st.info(f"i️ {check_result.message}")

        # Show confidence with color coding
        confidence_color = (
            "green"
            if check_result.confidence > 0.8
            else "orange" if check_result.confidence > 0.5 else "red"
        )
        st.markdown(
            f"**Vertrouwen:** <span style='color: {confidence_color}'>"
            f"{check_result.confidence:.1%}</span>",
            unsafe_allow_html=True,
        )

        # Show existing definition if found
        if check_result.existing_definitie:
            self._render_existing_definition(check_result.existing_definitie)

        # Show duplicates if found
        if check_result.duplicates:
            self._render_duplicate_matches(check_result.duplicates)

    def _render_existing_definition(self, definitie: DefinitieRecord) -> None:
        """Render existing definition details with action buttons."""
        st.markdown("#### 📋 Bestaande Definitie")

        with st.expander(f"Definitie Details (ID: {definitie.id})", expanded=True):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"**Definitie:** {definitie.definitie}")
                org, jur, wet = format_record_context(definitie)
                if org:
                    st.markdown(f"**Organisatorisch:** {org}")
                if jur:
                    st.markdown(f"**Juridisch:** {jur}")
                if wet:
                    st.markdown(f"**Wettelijk:** {wet}")

            with col2:
                st.markdown(f"**Status:** `{definitie.status}`")
                st.markdown(f"**Categorie:** `{definitie.categorie}`")
                if definitie.validation_score:
                    st.markdown(f"**Score:** {definitie.validation_score:.2f}")
                st.markdown(
                    f"**Gemaakt:** {definitie.created_at.strftime('%Y-%m-%d') if definitie.created_at else 'Onbekend'}"
                )

            # Action buttons
            st.markdown("---")
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("✅ Gebruik Deze", key=f"use_{definitie.id}"):
                    self._use_existing_definition(definitie)

            with col2:
                if st.button("📝 Bewerk", key=f"edit_{definitie.id}"):
                    self._edit_existing_definition(definitie)

            with col3:
                can_generate = _has_min_one_context()
                if not can_generate:
                    st.caption("Minstens één context vereist om nieuw te genereren.")
                if st.button(
                    "🔄 Genereer Nieuw",
                    key=f"new_{definitie.id}",
                    disabled=not can_generate,
                ):
                    self._trigger_new_generation()

    def _render_duplicate_matches(self, duplicates: list) -> None:
        """Render list of potential duplicates (max 3)."""
        st.markdown("#### 🔍 Mogelijke Duplicates")

        for i, dup_match in enumerate(duplicates[:3]):
            definitie = dup_match.definitie_record
            score = dup_match.match_score
            reasons = dup_match.match_reasons

            with st.expander(
                f"Match {i+1}: {definitie.begrip} (Score: {score:.2f})",
                expanded=i == 0,
            ):
                st.markdown(f"**Definitie:** {definitie.definitie}")
                org, jur, wet = format_record_context(definitie)
                ctx_parts = []
                if org:
                    ctx_parts.append(f"Organisatorisch: {org}")
                if jur:
                    ctx_parts.append(f"Juridisch: {jur}")
                if wet:
                    ctx_parts.append(f"Wettelijk: {wet}")
                st.markdown(
                    f"**Context:** {' | '.join(ctx_parts) if ctx_parts else '—'}"
                )
                st.markdown(f"**Redenen:** {', '.join(reasons)}")

                if st.button("Gebruik deze definitie", key=f"dup_use_{definitie.id}"):
                    self._use_existing_definition(definitie)

    def _use_existing_definition(self, definitie: DefinitieRecord) -> None:
        """Set definition as selected in session state."""
        SessionStateManager.set_value("selected_definition", definitie)

    def _edit_existing_definition(self, definitie: DefinitieRecord) -> None:
        """Navigate to edit tab with definition loaded."""
        SessionStateManager.set_value("editing_definition_id", definitie.id)
        SessionStateManager.set_value("active_tab", "edit")
        st.success("✏️ Bewerk-tab geopend — laden van definitie…")
        st.rerun()

    def _trigger_new_generation(self) -> None:
        """Trigger new generation with force flags."""
        options = ensure_dict(SessionStateManager.get_value("generation_options", {}))
        options["force_generate"] = True
        options["force_duplicate"] = True
        SessionStateManager.set_value("generation_options", options)
        try:
            SessionStateManager.clear_value("last_check_result")
            SessionStateManager.clear_value("selected_definition")
        except Exception as e:
            logger.warning(f"Failed to clear session state: {e}")
        # Trigger automatische generatie bij volgende render
        SessionStateManager.set_value("trigger_auto_generation", True)
        st.rerun()
