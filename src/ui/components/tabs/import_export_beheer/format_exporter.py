"""
Format Export component - UI wrapper voor ExportService.

Bevat UI logica, delegeert export naar ExportService.
"""

from __future__ import (
    annotations,  # DEF-175: Enable string annotations for TYPE_CHECKING
)

import logging
from typing import TYPE_CHECKING

import streamlit as st

from services.data_aggregation_service import DataAggregationService
from services.export_service import ExportFormat, ExportLevel, ExportService
from ui.session_state import SessionStateManager

if TYPE_CHECKING:
    from database.definitie_repository import DefinitieRepository

# Status values as string literals (avoids runtime import of DefinitieStatus enum)
_DEFINITIE_STATUSES = ["draft", "review", "established", "archived", "imported"]

logger = logging.getLogger(__name__)


class FormatExporter:
    """UI wrapper voor export functionaliteit via ExportService."""

    def __init__(self, repository: DefinitieRepository):
        """Initialize met repository dependency."""
        self.repository = repository
        # Initialize export service
        data_agg = DataAggregationService(repository)
        self.export_service = ExportService(
            repository=repository, data_aggregation_service=data_agg
        )

    def render(self):
        """Render export sectie - verplaatst van _render_export_section."""
        st.markdown("### Export Definities")

        # Export mode selector
        export_mode = st.radio(
            "Export modus",
            ["Bulk Export (alle of gefilterd)", "Individuele Selectie"],
            horizontal=True,
            help="Kies tussen bulk export of individuele definitie selectie",
        )

        if export_mode == "Bulk Export (alle of gefilterd)":
            self._render_bulk_export()
        else:
            self._render_individual_export()

    def _render_bulk_export(self):
        """Render bulk export UI."""
        # Export filters
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            export_format = st.selectbox(
                "Export formaat",
                ["CSV", "Excel", "JSON", "TXT"],
                help="Selecteer het gewenste export formaat",
                key="bulk_format",
            )

        with col2:
            export_level = st.selectbox(
                "Export niveau",
                ["Basis", "Uitgebreid", "Compleet"],
                help="Basis: 17 velden (definitie + voorbeelden)\n"
                "Uitgebreid: 25 velden (+ metadata, proces, users)\n"
                "Compleet: 36 velden (alle database velden)",
                key="bulk_level",
            )

        with col3:
            status_filter = st.selectbox(
                "Status filter",
                ["Alle"] + _DEFINITIE_STATUSES,
                help="Filter op definitie status",
                key="bulk_status",
            )

        with col4:
            limit = st.number_input(
                "Maximum aantal",
                min_value=0,
                max_value=10000,
                value=0,
                step=100,
                help="0 = geen limiet",
                key="bulk_limit",
            )

        # Export knop
        if st.button("📥 Genereer Bulk Export", type="primary", key="bulk_export_btn"):
            self._generate_bulk_export(
                export_format, export_level, status_filter, limit
            )

    def _render_individual_export(self):
        """Render individuele definitie selectie UI."""
        st.markdown("#### Selecteer Definities")

        # Filters voor selectie
        col1, col2, col3 = st.columns(3)

        with col1:
            status_filter = st.selectbox(
                "Filter op status",
                ["Alle"] + _DEFINITIE_STATUSES,
                help="Filter beschikbare definities op status",
                key="individual_status",
            )

        with col2:
            export_format = st.selectbox(
                "Export formaat",
                ["CSV", "Excel", "JSON", "TXT"],
                help="Selecteer het gewenste export formaat",
                key="individual_format",
            )

        with col3:
            export_level = st.selectbox(
                "Export niveau",
                ["Basis", "Uitgebreid", "Compleet"],
                help="Basis: 17 velden (definitie + voorbeelden)\n"
                "Uitgebreid: 25 velden (+ metadata, proces, users)\n"
                "Compleet: 36 velden (alle database velden)",
                key="individual_level",
            )

        # Haal definities op voor selectie
        if status_filter == "Alle":
            available_definitions = self.repository.get_all()
        else:
            available_definitions = self.repository.get_by_status(status_filter)

        if not available_definitions:
            st.warning("Geen definities gevonden met de huidige filter")
            return

        # Maak selectie opties
        st.markdown(f"**{len(available_definitions)} definities beschikbaar**")

        # Zoek functionaliteit
        search_term = st.text_input(
            "🔍 Zoek begrip",
            placeholder="Type om te zoeken...",
            help="Zoek op begrip naam",
            key="individual_search",
        )

        # Filter op zoekterm
        if search_term:
            filtered_defs = [
                d
                for d in available_definitions
                if search_term.lower() in d.begrip.lower()
            ]
        else:
            filtered_defs = available_definitions

        if not filtered_defs:
            st.warning(f"Geen definities gevonden met zoekterm '{search_term}'")
            return

        # Multi-select voor individuele definities
        st.markdown(f"**{len(filtered_defs)} definities gevonden**")

        # Maak opties lijst met meer info
        options = []
        definitions_map = {}
        for d in filtered_defs:
            label = f"{d.begrip} ({d.categorie}, {d.status})"
            options.append(label)
            definitions_map[label] = d

        # Select all / Deselect all knoppen
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✅ Selecteer Alle", key="select_all"):
                SessionStateManager.set_value("selected_definitions", options.copy())
        with col2:
            if st.button("❌ Deselecteer Alle", key="deselect_all"):
                SessionStateManager.set_value("selected_definitions", [])

        # Multi-select widget
        selected_labels = st.multiselect(
            "Selecteer definities om te exporteren",
            options=options,
            default=SessionStateManager.get_value("selected_definitions", default=[]),
            help="Selecteer één of meerdere definities",
            key="individual_multiselect",
        )

        # Update session state
        SessionStateManager.set_value("selected_definitions", selected_labels)

        # Preview van selectie
        if selected_labels:
            st.info(f"📋 **{len(selected_labels)} definitie(s) geselecteerd**")

            # Toon preview in expander
            with st.expander("👁️ Bekijk geselecteerde definities"):
                for label in selected_labels:
                    d = definitions_map[label]
                    st.markdown(f"**{d.begrip}**")
                    st.caption(
                        f"Status: {d.status} | Categorie: {d.categorie} | "
                        f"Context: {d.organisatorische_context}"
                    )
                    st.markdown("---")

        # Export knop (alleen tonen als er selecties zijn)
        if selected_labels:
            if st.button(
                f"📥 Exporteer {len(selected_labels)} Definitie(s)",
                type="primary",
                key="individual_export_btn",
            ):
                # Haal definitie objecten op
                selected_definitions = [
                    definitions_map[label] for label in selected_labels
                ]
                self._generate_individual_export(
                    selected_definitions, export_format, export_level
                )
        else:
            st.warning("⚠️ Selecteer minimaal 1 definitie om te exporteren")

    def _generate_bulk_export(
        self, format: str, level: str, status_filter: str, limit: int
    ):
        """Genereer bulk export bestand via ExportService."""
        with st.spinner("Bulk export genereren..."):
            try:
                # Haal definities op
                if status_filter == "Alle":
                    definitions = self.repository.get_all()
                else:
                    definitions = self.repository.get_by_status(status_filter)

                # Apply limit
                if limit > 0:
                    definitions = definitions[:limit]

                if not definitions:
                    st.warning("Geen definities gevonden voor export")
                    return

                self._execute_export(definitions, format, level, "bulk")

            except Exception as e:
                st.error(f"Fout bij genereren bulk export: {e!s}")
                logger.exception("Bulk export fout")

    def _generate_individual_export(self, definitions: list, format: str, level: str):
        """Genereer export voor individueel geselecteerde definities."""
        with st.spinner(f"Export genereren voor {len(definitions)} definitie(s)..."):
            try:
                if not definitions:
                    st.warning("Geen definities geselecteerd voor export")
                    return

                self._execute_export(definitions, format, level, "individual")

            except Exception as e:
                st.error(f"Fout bij genereren export: {e!s}")
                logger.exception("Individual export fout")

    def _execute_export(
        self, definitions: list, format: str, level: str, export_type: str
    ):
        """Voer de daadwerkelijke export uit (herbruikbaar voor bulk en individual)."""
        # Map format naar ExportFormat enum
        format_map = {
            "CSV": ExportFormat.CSV,
            "Excel": ExportFormat.EXCEL,
            "JSON": ExportFormat.JSON,
            "TXT": ExportFormat.TXT,
        }
        export_format = format_map.get(format, ExportFormat.CSV)

        # Map level naar ExportLevel enum
        level_map = {
            "Basis": ExportLevel.BASIS,
            "Uitgebreid": ExportLevel.UITGEBREID,
            "Compleet": ExportLevel.COMPLEET,
        }
        export_level = level_map.get(level, ExportLevel.BASIS)

        # Gebruik ExportService voor export met geselecteerd niveau
        file_path = self.export_service.export_multiple_definitions(
            definitions=definitions, format=export_format, level=export_level
        )

        # Lees bestand en toon download button
        with open(file_path, "rb") as f:
            file_data = f.read()

        # Bepaal mime type
        mime_types = {
            "CSV": "text/csv",
            "Excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "JSON": "application/json",
            "TXT": "text/plain",
        }
        mime_type = mime_types.get(format, "application/octet-stream")

        # Download button
        import os

        filename = os.path.basename(file_path)

        st.download_button(
            label=f"📥 Download {format} ({len(definitions)} definitie(s))",
            data=file_data,
            file_name=filename,
            mime=mime_type,
            key=f"download_{export_type}_{format}_{level}",
        )

        # Toon veldenaantal per niveau
        field_counts = {
            "Basis": "17 velden",
            "Uitgebreid": "25 velden",
            "Compleet": "36 velden",
        }
        field_count = field_counts.get(level, "17 velden")

        st.success(
            f"✅ Export gegenereerd: {len(definitions)} definitie(s) "
            f"met {level} niveau ({field_count})"
        )
        st.info(f"📁 Bestand opgeslagen: {file_path}")
