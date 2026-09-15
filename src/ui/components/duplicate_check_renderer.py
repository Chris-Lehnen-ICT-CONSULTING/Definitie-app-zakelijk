"""Duplicate Check Renderer - Renders duplicate check results with actions.

Extracted from definition_generator_tab.py to reduce God Class complexity.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import streamlit as st

from integration.definitie_checker import CheckAction
from ui.components.formatters import format_record_context
from ui.helpers.context_helpers import has_min_one_context
from ui.session_state import SessionStateManager
from utils.type_helpers import ensure_dict

if TYPE_CHECKING:
    from database.definitie_repository import DefinitieRecord
    from integration.definitie_checker import DefinitieCheckResult

logger = logging.getLogger(__name__)


# NOTE: _has_min_one_context() moved to ui.helpers.context_helpers (DEF-260)
# Import: from ui.helpers.context_helpers import has_min_one_context


class DuplicateCheckRenderer:
    """Renders duplicate check results with interactive actions.

    This component handles:
    - Displaying duplicate check results (PROCEED/USE_EXISTING/etc)
    - Showing existing definition details with action buttons
    - Rendering list of potential duplicates
    - Navigation actions (use existing, edit, generate new)
    """

    def render_check_results(self, check_result: DefinitieCheckResult) -> None:
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
                # DEF-743 (besluit 3): geen totaalcijfer als kwaliteitsoordeel —
                # ook niet de historische `validation_score` uit het record.
                st.markdown(
                    f"**Gemaakt:** {definitie.created_at.strftime('%Y-%m-%d') if definitie.created_at else 'Onbekend'}"
                )

            # Action buttons — de drie bestaande keuzes blijven behouden (B-09).
            st.markdown("---")
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("✅ Gebruik Deze", key=f"use_{definitie.id}"):
                    self._use_existing_definition(definitie)
                    st.rerun()

            with col2:
                if st.button("📝 Bewerk", key=f"edit_{definitie.id}"):
                    self._edit_existing_definition(definitie)

            with col3:
                can_generate = has_min_one_context()
                if not can_generate:
                    st.caption("Minstens één context vereist om nieuw te genereren.")
                # Bewust naast een bestaande definitie genereren vraagt een
                # reden: die gaat mee in de audit van het nieuwe concept
                # (DEF-622, besluit 5). Het bestaande record wijzigt niet.
                reden = st.text_input(
                    "Reden om toch een nieuw concept te genereren",
                    key=f"new_reason_{definitie.id}",
                    placeholder="Bijv. de bestaande definitie dekt de nieuwe regeling niet",
                )
                if st.button(
                    "🔄 Genereer Nieuw",
                    key=f"new_{definitie.id}",
                    disabled=not can_generate,
                ):
                    self._trigger_new_generation(reden=reden)

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

    def render_selected_definition(self, definitie: DefinitieRecord) -> None:
        """Toon het met 'Gebruik Deze' gekozen record (B-09).

        De keuze is pas een keuze als de gebruiker ziet waarmee hij verder
        werkt: tekst, context, status en id, plus de weg naar bewerken.
        """
        st.markdown("### ✅ Gekozen bestaande definitie")
        st.markdown(f"**{definitie.begrip}** (ID: {definitie.id})")
        st.markdown(f"**Definitie:** {definitie.definitie}")
        org, jur, wet = format_record_context(definitie)
        if org:
            st.markdown(f"**Organisatorisch:** {org}")
        if jur:
            st.markdown(f"**Juridisch:** {jur}")
        if wet:
            st.markdown(f"**Wettelijk:** {wet}")
        st.markdown(f"**Status:** `{definitie.status}`")
        if st.button("📝 Open in Bewerk-tab", key=f"selected_edit_{definitie.id}"):
            self._edit_existing_definition(definitie)

    def _use_existing_definition(self, definitie: DefinitieRecord) -> None:
        """Kies het bestaande record om mee verder te werken.

        De duplicaatmelding maakt plaats voor het gekozen record; anders
        blijven melding en keuze naast elkaar staan en is niet zichtbaar dat
        er gekozen is.
        """
        SessionStateManager.set_value("selected_definition", definitie)
        SessionStateManager.clear_value("last_check_result")

    def _edit_existing_definition(self, definitie: DefinitieRecord) -> None:
        """Navigate to edit tab with definition loaded."""
        SessionStateManager.set_value("editing_definition_id", definitie.id)
        SessionStateManager.set_value("active_tab", "edit")
        st.success("✏️ Bewerk-tab geopend — laden van definitie…")
        st.rerun()

    def _trigger_new_generation(self, reden: str | None = None) -> None:
        """Start een nieuwe generatie naast het bestaande record, met reden.

        Zonder reden gebeurt er niets: bewust naast een bestaande definitie
        genereren is een keuze die in de audit van het nieuwe concept moet
        staan (DEF-622, besluit 5). De force-opties zijn eenmalig; de handler
        ruimt ze na de generatie op zodat ze niet blijven plakken.
        """
        reden = (reden or "").strip()
        if not reden:
            st.warning(
                "Geef een reden op om toch een nieuw concept te genereren; "
                "die reden wordt bij het nieuwe concept vastgelegd."
            )
            return
        options = ensure_dict(SessionStateManager.get_value("generation_options", {}))
        options["force_generate"] = True
        options["force_duplicate"] = True
        options["force_duplicate_reason"] = reden
        SessionStateManager.set_value("generation_options", options)
        SessionStateManager.clear_value("last_check_result")
        SessionStateManager.clear_value("selected_definition")
        # Trigger automatische generatie bij volgende render
        SessionStateManager.set_value("trigger_auto_generation", True)
        st.rerun()
