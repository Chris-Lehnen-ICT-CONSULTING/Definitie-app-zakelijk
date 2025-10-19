"""
Format Export component - Verplaatst van import_export_beheer_tab.py.

Bevat alle export functionaliteit, exact zoals het al werkte.
"""

import io
import logging
from datetime import datetime

import pandas as pd
import streamlit as st

from database.definitie_repository import (
    DefinitieRecord,
    DefinitieRepository,
    DefinitieStatus,
)

logger = logging.getLogger(__name__)


class FormatExporter:
    """Handles export naar verschillende formaten."""

    def __init__(self, repository: DefinitieRepository):
        """Initialize met repository dependency."""
        self.repository = repository

    def render(self):
        """Render export sectie - verplaatst van _render_export_section."""
        st.markdown("### Export Definities")

        # Export filters
        col1, col2, col3 = st.columns(3)

        with col1:
            export_format = st.selectbox(
                "Export formaat",
                ["CSV", "Excel", "JSON", "TXT"],
                help="Selecteer het gewenste export formaat",
            )

        with col2:
            status_filter = st.selectbox(
                "Status filter",
                ["Alle"] + [status.value for status in DefinitieStatus],
                help="Filter op definitie status",
            )

        with col3:
            limit = st.number_input(
                "Maximum aantal",
                min_value=0,
                max_value=10000,
                value=0,
                step=100,
                help="0 = geen limiet",
            )

        # Export knop
        if st.button("📥 Genereer Export", type="primary"):
            self._generate_export(export_format, status_filter, limit)

    def _generate_export(self, format: str, status_filter: str, limit: int):
        """Genereer export bestand - exact verplaatst van origineel."""
        with st.spinner("Export genereren..."):
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

                # Converteer naar DataFrame
                df = self._definitions_to_dataframe(definitions)

                # Genereer export
                if format == "CSV":
                    output = df.to_csv(index=False)
                    mime_type = "text/csv"
                    extension = "csv"
                elif format == "Excel":
                    output = io.BytesIO()
                    df.to_excel(output, index=False, engine="openpyxl")
                    output.seek(0)
                    mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    extension = "xlsx"
                elif format == "JSON":
                    output = df.to_json(orient="records", indent=2)
                    mime_type = "application/json"
                    extension = "json"
                else:  # TXT
                    output = self._generate_txt_export(definitions)
                    mime_type = "text/plain"
                    extension = "txt"

                # Download button
                filename = f"definities_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}"

                st.download_button(
                    label=f"📥 Download {format} ({len(definitions)} definities)",
                    data=(
                        output if isinstance(output, str | bytes) else output.getvalue()
                    ),
                    file_name=filename,
                    mime=mime_type,
                )

                st.success(f"✅ Export gegenereerd: {len(definitions)} definities")

            except Exception as e:
                st.error(f"Fout bij genereren export: {e!s}")

    def _definitions_to_dataframe(
        self, definitions: list[DefinitieRecord]
    ) -> pd.DataFrame:
        """Converteer definities naar DataFrame - exact verplaatst."""
        data = []
        for d in definitions:
            data.append(
                {
                    "begrip": d.begrip,
                    "definitie": d.definitie,
                    "categorie": d.categorie,
                    "context": d.organisatorische_context,
                    "status": d.status,
                    "validation_score": d.validation_score,
                    "aangemaakt": d.aangemaakt_op,
                    "laatst_gewijzigd": d.laatst_gewijzigd,
                }
            )
        return pd.DataFrame(data)

    def _generate_txt_export(self, definitions: list[DefinitieRecord]) -> str:
        """Genereer platte tekst export - exact verplaatst."""
        lines = ["DEFINITIE EXPORT", "=" * 50, ""]

        for d in definitions:
            lines.extend(
                [
                    f"Begrip: {d.begrip}",
                    f"Definitie: {d.definitie}",
                    f"Categorie: {d.categorie}",
                    f"Context: {d.organisatorische_context}",
                    f"Status: {d.status}",
                    "-" * 30,
                    "",
                ]
            )

        return "\n".join(lines)
