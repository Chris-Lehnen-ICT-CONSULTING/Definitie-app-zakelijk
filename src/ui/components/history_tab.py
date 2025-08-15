"""
History Tab - Interface voor definitie geschiedenis en audit trail.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime, timedelta

from database.definitie_repository import (
    DefinitieRepository,
    DefinitieRecord,
    DefinitieStatus,
)
from ui.session_state import SessionStateManager


class HistoryTab:
    """Tab voor definitie geschiedenis en audit trail."""

    def __init__(self, repository: DefinitieRepository):
        """Initialiseer history tab."""
        self.repository = repository

    def render(self):
        """Render history tab."""
        # Filter controls
        self._render_filter_controls()

        # History overview
        self._render_history_overview()

        # Detailed history
        self._render_detailed_history()

        # Statistics
        self._render_history_statistics()

    def _render_filter_controls(self):
        """Render filter controls voor history."""
        st.markdown("### 🔍 Filter Geschiedenis")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            # Date range filter
            date_range = st.selectbox(
                "Tijdsperiode",
                [
                    "Laatste week",
                    "Laatste maand",
                    "Laatste 3 maanden",
                    "Alle tijd",
                    "Aangepast...",
                ],
                key="history_date_range",
            )

            if date_range == "Aangepast...":
                start_date = st.date_input("Van datum", key="history_start_date")
                end_date = st.date_input("Tot datum", key="history_end_date")
            else:
                start_date, end_date = self._get_date_range(date_range)

        with col2:
            # Status filter
            status_filter = st.selectbox(
                "Status",
                ["Alle"] + [status.value for status in DefinitieStatus],
                key="history_status_filter",
            )

        with col3:
            # Context filter
            try:
                all_contexts = set()
                recent_defs = self.repository.search_definities(limit=100)
                for def_rec in recent_defs:
                    if def_rec.organisatorische_context:
                        all_contexts.add(def_rec.organisatorische_context)

                context_filter = st.selectbox(
                    "Context",
                    ["Alle"] + sorted(list(all_contexts)),
                    key="history_context_filter",
                )
            except:
                context_filter = "Alle"

        with col4:
            # Search
            search_term = st.text_input(
                "Zoeken",
                placeholder="Zoek in begrip of definitie...",
                key="history_search",
            )

        # Store filters in session
        SessionStateManager.set_value(
            "history_filters",
            {
                "date_range": date_range,
                "start_date": start_date,
                "end_date": end_date,
                "status": status_filter,
                "context": context_filter,
                "search": search_term,
            },
        )

    def _render_history_overview(self):
        """Render geschiedenis overzicht."""
        st.markdown("### 📊 Geschiedenis Overzicht")

        filters = SessionStateManager.get_value("history_filters", {})

        try:
            # Get filtered data
            filtered_definitions = self._get_filtered_definitions(filters)

            if not filtered_definitions:
                st.info("Geen definities gevonden met de geselecteerde filters")
                return

            # Overview metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("📋 Totaal Definities", len(filtered_definitions))

            with col2:
                established = len(
                    [
                        d
                        for d in filtered_definitions
                        if d.status == DefinitieStatus.ESTABLISHED.value
                    ]
                )
                st.metric("✅ Vastgesteld", established)

            with col3:
                in_review = len(
                    [
                        d
                        for d in filtered_definitions
                        if d.status == DefinitieStatus.REVIEW.value
                    ]
                )
                st.metric("🔄 In Review", in_review)

            with col4:
                if filtered_definitions:
                    avg_score = sum(
                        d.validation_score
                        for d in filtered_definitions
                        if d.validation_score
                    ) / len([d for d in filtered_definitions if d.validation_score])
                    st.metric(
                        "📈 Gem. Score", f"{avg_score:.2f}" if avg_score else "N/A"
                    )

            # Timeline visualization
            self._render_timeline_chart(filtered_definitions)

        except Exception as e:
            st.error(f"❌ Kon geschiedenis niet laden: {str(e)}")

    def _render_detailed_history(self):
        """Render gedetailleerde geschiedenis lijst."""
        st.markdown("### 📜 Definitie Geschiedenis")

        filters = SessionStateManager.get_value("history_filters", {})

        try:
            filtered_definitions = self._get_filtered_definitions(filters)

            if not filtered_definitions:
                return

            # Pagination
            items_per_page = 10
            total_pages = (
                len(filtered_definitions) + items_per_page - 1
            ) // items_per_page

            if total_pages > 1:
                page = (
                    st.number_input(
                        "Pagina",
                        min_value=1,
                        max_value=total_pages,
                        value=1,
                        key="history_page",
                    )
                    - 1
                )
            else:
                page = 0

            # Get page data
            start_idx = page * items_per_page
            end_idx = min(start_idx + items_per_page, len(filtered_definitions))
            page_definitions = filtered_definitions[start_idx:end_idx]

            # Display definitions
            for definitie in page_definitions:
                self._render_history_item(definitie)

            # Pagination info
            if total_pages > 1:
                st.caption(
                    f"Pagina {page + 1} van {total_pages} | Toon {len(page_definitions)} van {len(filtered_definitions)} definities"
                )

        except Exception as e:
            st.error(f"❌ Kon geschiedenis details niet laden: {str(e)}")

    def _render_history_item(self, definitie: DefinitieRecord):
        """Render één geschiedenis item."""
        with st.container():
            # Main info row
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

            with col1:
                # Begrip en definitie
                st.markdown(f"**{definitie.begrip}** ({definitie.categorie})")
                definitie_preview = (
                    definitie.definitie[:100] + "..."
                    if len(definitie.definitie) > 100
                    else definitie.definitie
                )
                st.markdown(f"*{definitie_preview}*")
                st.caption(f"Context: {definitie.organisatorische_context}")

            with col2:
                # Status met kleur
                status_colors = {
                    "draft": "🟡",
                    "review": "🔵",
                    "established": "🟢",
                    "archived": "🔴",
                }
                status_icon = status_colors.get(definitie.status, "⚪")
                st.markdown(f"{status_icon} **{definitie.status.upper()}**")

                if definitie.validation_score:
                    score_color = (
                        "green"
                        if definitie.validation_score > 0.8
                        else "orange" if definitie.validation_score > 0.6 else "red"
                    )
                    st.markdown(
                        f"Score: <span style='color: {score_color}'>{definitie.validation_score:.2f}</span>",
                        unsafe_allow_html=True,
                    )

            with col3:
                # Tijdsinformatie
                if definitie.created_at:
                    st.caption("📅 Gemaakt:")
                    st.caption(definitie.created_at.strftime("%Y-%m-%d %H:%M"))

                if (
                    definitie.updated_at
                    and definitie.updated_at != definitie.created_at
                ):
                    st.caption("🔄 Gewijzigd:")
                    st.caption(definitie.updated_at.strftime("%Y-%m-%d %H:%M"))

            with col4:
                # Actions
                if st.button("👁️", key=f"view_{definitie.id}", help="Bekijk details"):
                    self._show_definition_details(definitie)

                if st.button(
                    "📊", key=f"history_{definitie.id}", help="Bekijk historie"
                ):
                    self._show_audit_trail(definitie)

            st.markdown("---")

    def _render_timeline_chart(self, definitions: List[DefinitieRecord]):
        """Render timeline chart van definities."""
        if not definitions:
            return

        st.markdown("#### 📈 Activiteit Timeline")

        try:
            # Prepare data voor chart
            df_data = []
            for definitie in definitions:
                if definitie.created_at:
                    df_data.append(
                        {
                            "datum": definitie.created_at.date(),
                            "status": definitie.status,
                            "begrip": definitie.begrip,
                            "score": definitie.validation_score or 0,
                        }
                    )

            if df_data:
                df = pd.DataFrame(df_data)

                # Group by date en status
                timeline_data = (
                    df.groupby(["datum", "status"]).size().reset_index(name="count")
                )

                # Create timeline chart
                if not timeline_data.empty:
                    chart_data = timeline_data.pivot(
                        index="datum", columns="status", values="count"
                    ).fillna(0)
                    st.bar_chart(chart_data)
                else:
                    st.info("Geen timeline data beschikbaar")

        except Exception as e:
            st.warning(f"Timeline chart kon niet geladen worden: {str(e)}")

    def _render_history_statistics(self):
        """Render geschiedenis statistieken."""
        with st.expander("📊 Gedetailleerde Statistieken", expanded=False):
            try:
                stats = self.repository.get_statistics()

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("#### Status Verdeling")
                    if stats.get("by_status"):
                        for status, count in stats["by_status"].items():
                            st.write(f"**{status.upper()}:** {count}")

                with col2:
                    st.markdown("#### Categorie Verdeling")
                    if stats.get("by_category"):
                        for category, count in stats["by_category"].items():
                            st.write(f"**{category.upper()}:** {count}")

                # Additional metrics
                if stats.get("average_validation_score"):
                    st.markdown(
                        f"**Gemiddelde Kwaliteitsscore:** {stats['average_validation_score']}"
                    )

            except Exception as e:
                st.error(f"❌ Kon statistieken niet laden: {str(e)}")

    def _show_definition_details(self, definitie: DefinitieRecord):
        """Toon gedetailleerde definitie informatie."""
        with st.expander(f"📋 Details: {definitie.begrip}", expanded=True):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown("#### Definitie")
                st.info(definitie.definitie)

                st.markdown("#### Context")
                st.write(f"**Organisatorisch:** {definitie.organisatorische_context}")
                if definitie.juridische_context:
                    st.write(f"**Juridisch:** {definitie.juridische_context}")
                st.write(f"**Categorie:** {definitie.categorie}")

            with col2:
                st.markdown("#### Metadata")
                st.write(f"**ID:** {definitie.id}")
                st.write(f"**Status:** {definitie.status}")
                st.write(f"**Versie:** {definitie.version_number}")

                if definitie.validation_score:
                    st.write(f"**Score:** {definitie.validation_score:.2f}")

                if definitie.created_at:
                    st.write(
                        f"**Gemaakt:** {definitie.created_at.strftime('%Y-%m-%d %H:%M')}"
                    )

                if definitie.created_by:
                    st.write(f"**Door:** {definitie.created_by}")

                if definitie.approved_by:
                    st.write(f"**Goedgekeurd door:** {definitie.approved_by}")
                    st.write(
                        f"**Goedgekeurd op:** {definitie.approved_at.strftime('%Y-%m-%d %H:%M') if definitie.approved_at else 'Onbekend'}"
                    )

    def _show_audit_trail(self, definitie: DefinitieRecord):
        """Toon audit trail voor definitie."""
        st.info(
            f"🔍 Audit trail voor '{definitie.begrip}' (ID: {definitie.id}) - Feature komt binnenkort beschikbaar"
        )
        # TODO: Implement audit trail query from definitie_geschiedenis table

    def _get_filtered_definitions(
        self, filters: Dict[str, Any]
    ) -> List[DefinitieRecord]:
        """Haal gefilterde definities op."""
        # Build search parameters
        search_params = {}

        if filters.get("search"):
            search_params["query"] = filters["search"]

        if filters.get("status") and filters["status"] != "Alle":
            search_params["status"] = DefinitieStatus(filters["status"])

        if filters.get("context") and filters["context"] != "Alle":
            search_params["organisatorische_context"] = filters["context"]

        # Get definitions
        definitions = self.repository.search_definities(**search_params, limit=1000)

        # Apply date filter
        if filters.get("start_date") and filters.get("end_date"):
            start_date = filters["start_date"]
            end_date = filters["end_date"]

            definitions = [
                d
                for d in definitions
                if d.created_at and start_date <= d.created_at.date() <= end_date
            ]

        # Sort by creation date (newest first)
        definitions.sort(key=lambda x: x.created_at or datetime.min, reverse=True)

        return definitions

    def _get_date_range(self, range_name: str) -> tuple:
        """Convert range name naar start en end date."""
        now = datetime.now()
        today = now.date()

        if range_name == "Laatste week":
            start_date = today - timedelta(days=7)
            end_date = today
        elif range_name == "Laatste maand":
            start_date = today - timedelta(days=30)
            end_date = today
        elif range_name == "Laatste 3 maanden":
            start_date = today - timedelta(days=90)
            end_date = today
        else:  # Alle tijd
            start_date = datetime(2020, 1, 1).date()  # Far past
            end_date = today

        return start_date, end_date
