"""
CSV Import component - Verplaatst van import_export_beheer_tab.py.

Bevat alle CSV import functionaliteit, exact zoals het al werkte.
"""

from __future__ import (
    annotations,  # DEF-175: Enable string annotations for TYPE_CHECKING
)

import logging
from typing import TYPE_CHECKING

import pandas as pd
import streamlit as st

if TYPE_CHECKING:
    from database.definitie_repository import DefinitieRepository

# Status values as string literals (avoids runtime import of DefinitieStatus enum)
_STATUS_DRAFT = "draft"

logger = logging.getLogger(__name__)


class CSVImporter:
    """Handles CSV import functionaliteit."""

    def __init__(self, repository: DefinitieRepository):
        """Initialize met repository dependency."""
        self.repository = repository

    def render(self):
        """Render CSV import sectie - verplaatst van _render_import_section."""
        st.markdown("### CSV Import")
        st.info("Upload een CSV bestand met definities om te importeren.")

        # File upload
        uploaded_file = st.file_uploader(
            "Selecteer CSV bestand",
            type=["csv"],
            help="CSV moet kolommen bevatten: begrip, definitie, categorie, context",
        )

        if uploaded_file is not None:
            try:
                # Lees CSV
                df = pd.read_csv(uploaded_file)

                # Toon preview
                st.markdown("#### Preview")
                st.dataframe(df.head(), use_container_width=True)

                # Validatie
                required_cols = ["begrip", "definitie"]
                missing_cols = [col for col in required_cols if col not in df.columns]

                if missing_cols:
                    st.error(f"Missende verplichte kolommen: {', '.join(missing_cols)}")
                    return

                # Import opties
                col1, col2 = st.columns(2)
                with col1:
                    skip_duplicates = st.checkbox(
                        "Skip duplicaten",
                        value=True,
                        help="Sla rijen over die al bestaan (op basis van begrip + context)",
                    )

                with col2:
                    auto_validate = st.checkbox(
                        "Auto-validatie",
                        value=False,
                        help="Valideer geïmporteerde definities automatisch",
                    )

                # Import knop
                if st.button("🚀 Start Import", type="primary"):
                    self._process_import(df, skip_duplicates, auto_validate)

            except Exception as e:
                st.error(f"Fout bij lezen CSV: {e!s}")

    def _process_import(
        self, df: pd.DataFrame, skip_duplicates: bool, auto_validate: bool
    ):
        """Verwerk CSV import - exact verplaatst van origineel."""
        # Local import for record construction (avoids top-level database import)
        from database.definitie_repository import DefinitieRecord

        progress_bar = st.progress(0)
        status_text = st.empty()

        imported = 0
        skipped = 0
        errors = []

        total = len(df)

        for idx, row in df.iterrows():
            progress = (idx + 1) / total
            progress_bar.progress(progress)
            status_text.text(f"Verwerken: {idx + 1}/{total}")

            try:
                # Check duplicaat
                if skip_duplicates:
                    existing = self.repository.find_by_begrip(
                        row.get("begrip", ""), row.get("context", "")
                    )
                    if existing:
                        skipped += 1
                        continue

                # Maak record
                record = DefinitieRecord(
                    begrip=row.get("begrip", ""),
                    definitie=row.get("definitie", ""),
                    categorie=row.get("categorie", "Type"),
                    organisatorische_context=row.get("context", "Algemeen"),
                    status=_STATUS_DRAFT,
                    validation_score=0.0,
                )

                # Save
                self.repository.save(record)
                imported += 1

                # Auto validatie indien gewenst
                if auto_validate:
                    # Auto-validatie wordt in een aparte story geïmplementeerd
                    pass

            except Exception as e:
                errors.append(f"Rij {idx + 1}: {e!s}")

        # Resultaten
        progress_bar.empty()
        status_text.empty()

        st.success(
            f"✅ Import voltooid: {imported} geïmporteerd, {skipped} overgeslagen"
        )
        if errors:
            with st.expander(f"⚠️ {len(errors)} fouten opgetreden"):
                for error in errors[:10]:  # Max 10 fouten tonen
                    st.error(error)
