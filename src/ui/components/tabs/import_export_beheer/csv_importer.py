"""
CSV Import component - Verplaatst van import_export_beheer_tab.py.

Bevat alle CSV import functionaliteit, exact zoals het al werkte.
"""

from __future__ import (
    annotations,  # DEF-175: Enable string annotations for TYPE_CHECKING
)

import io
import logging
from typing import TYPE_CHECKING, Protocol

import pandas as pd
import streamlit as st

if TYPE_CHECKING:
    from database.definitie_repository import DefinitieRepository


class _UploadedFile(Protocol):
    """Minimaal contract van een Streamlit UploadedFile dat we nodig hebben."""

    size: int

    def seek(self, pos: int, whence: int = ..., /) -> int: ...

    def read(self, size: int = ..., /) -> bytes: ...


# Status values as string literals (avoids runtime import of DefinitieStatus enum)
_STATUS_DRAFT = "draft"

# DEF-470: import-hardening
# Encodings die we (in volgorde) proberen bij het inlezen van een CSV.
# `latin-1` staat als laatste vangnet: het kan elke byte decoderen.
_CSV_ENCODINGS = ("utf-8-sig", "cp1252", "latin-1")
# Maximale bestandsgrootte (10 MB) — boven deze grens weigeren we de import.
_MAX_FILE_SIZE_MB = 10
_MAX_FILE_SIZE_BYTES = _MAX_FILE_SIZE_MB * 1024 * 1024

logger = logging.getLogger(__name__)


def _cell_str(value: object) -> str:
    """Normaliseer een CSV-cel naar een gestripte string.

    Pandas levert lege cellen als ``NaN`` (float) aan; ``str(nan)`` zou
    ``"nan"`` opleveren. Deze helper geeft dan een lege string terug zodat
    de leeg-verplichte-waarde-check (DEF-470) correct werkt.
    """
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


class CSVImporter:
    """Handles CSV import functionaliteit."""

    def __init__(self, repository: DefinitieRepository):
        """Initialize met repository dependency."""
        self.repository = repository

    def render(self) -> None:
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
                # Lees CSV met encoding-fallback + grootte-/leegcheck (DEF-470)
                df = self._read_csv_safe(uploaded_file)

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

    def _read_csv_safe(self, uploaded_file: _UploadedFile) -> pd.DataFrame:
        """Lees een CSV met grootte-/leegcheck en encoding-fallback (DEF-470).

        Weigert lege en te grote bestanden met een nette ``ValueError`` en
        probeert meerdere encodings zodat een niet-utf-8-bestand (export uit
        Excel/Windows) niet hard crasht.
        """
        # Grootte-/leegcheck op basis van de door Streamlit aangeleverde .size
        if uploaded_file.size > _MAX_FILE_SIZE_BYTES:
            raise ValueError(
                f"Het CSV-bestand is te groot (max {_MAX_FILE_SIZE_MB} MB)."
            )

        # Lees de ruwe bytes één keer. Pandas onthoudt state op een hergebruikt
        # file-object (de encoding-fallback faalt dan); een verse BytesIO per
        # poging voorkomt dat.
        uploaded_file.seek(0)
        raw = uploaded_file.read()
        if not raw:
            raise ValueError("Het CSV-bestand is leeg.")
        if len(raw) > _MAX_FILE_SIZE_BYTES:
            raise ValueError(
                f"Het CSV-bestand is te groot (max {_MAX_FILE_SIZE_MB} MB)."
            )

        last_error: Exception | None = None
        for encoding in _CSV_ENCODINGS:
            try:
                df = pd.read_csv(io.BytesIO(raw), encoding=encoding)
            except UnicodeDecodeError as e:
                last_error = e
                continue
            except pd.errors.EmptyDataError as e:
                raise ValueError("Het CSV-bestand bevat geen data.") from e

            if df.empty and len(df.columns) == 0:
                raise ValueError("Het CSV-bestand bevat geen data.")
            return df

        raise ValueError(
            "Kon het CSV-bestand niet decoderen (onbekende encoding)."
        ) from last_error

    def _process_import(
        self, df: pd.DataFrame, skip_duplicates: bool, auto_validate: bool
    ) -> None:
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
                # DEF-470: normaliseer cellen (NaN/None -> "") en weiger rijen
                # waarin een verplichte waarde ontbreekt i.p.v. stil een leeg
                # record op te slaan.
                begrip = _cell_str(row.get("begrip", ""))
                definitie = _cell_str(row.get("definitie", ""))
                if not begrip or not definitie:
                    errors.append(
                        f"Rij {idx + 1}: verplichte waarde ontbreekt "
                        "(begrip en/of definitie is leeg)"
                    )
                    continue

                context = _cell_str(row.get("context", "")) or "Algemeen"
                categorie = _cell_str(row.get("categorie", "")) or "Type"

                # Check duplicaat
                if skip_duplicates:
                    # DEF-439: DB-laag DefinitieRepository heet find_definitie
                    # (begrip + organisatorische_context), niet find_by_begrip.
                    existing = self.repository.find_definitie(begrip, context)
                    if existing:
                        skipped += 1
                        continue

                # Maak record
                record = DefinitieRecord(
                    begrip=begrip,
                    definitie=definitie,
                    categorie=categorie,
                    organisatorische_context=context,
                    status=_STATUS_DRAFT,
                    validation_score=0.0,
                )

                # Save (DEF-439: DB-laag heet create_definitie, niet save)
                self.repository.create_definitie(record)
                imported += 1

                # Auto validatie indien gewenst
                if auto_validate:
                    # Auto-validatie wordt in een aparte story geïmplementeerd
                    pass

            except Exception as e:
                # Brede catch is bewust: één kapotte rij mag de hele import niet
                # stoppen. We maskeren de fout echter niet langer stil — hij wordt
                # gelogd (met stacktrace) én aan de gebruiker getoond (DEF-470).
                logger.exception("CSV-import: rij %s gefaald", idx + 1)
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
