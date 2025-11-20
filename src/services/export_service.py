"""
Export Service.

Service voor het exporteren van definities naar verschillende formaten.
Gebruikt DataAggregationService om data te verzamelen zonder directe UI dependencies.
"""

import json
import logging
from datetime import UTC, datetime, timedelta

UTC = UTC  # Python 3.10 compatibility
from enum import Enum
from pathlib import Path
from typing import Any

from database.definitie_repository import DefinitieRecord, DefinitieRepository
from services.data_aggregation_service import (
    DataAggregationService,
    DefinitieExportData,
)

logger = logging.getLogger(__name__)


class ExportFormat(Enum):
    """Ondersteunde export formaten."""

    TXT = "txt"
    JSON = "json"
    CSV = "csv"
    EXCEL = "xlsx"
    DOCX = "docx"
    PDF = "pdf"


class ExportLevel(Enum):
    """Export detail levels - hoeveel velden worden geëxporteerd."""

    BASIS = "basis"  # 17 velden: definitie + voorbeelden
    UITGEBREID = "uitgebreid"  # 25 velden: + metadata, process, users
    COMPLEET = "compleet"  # 37 velden: alle database velden


# Field configuration per export level
EXPORT_LEVEL_FIELDS = {
    ExportLevel.BASIS: {
        "definitie": [
            "begrip",
            "definitie",
            "categorie",
            "organisatorische_context",
            "juridische_context",
            "wettelijke_basis",
            "status",
            "validation_score",
            "created_at",
            "updated_at",
        ],
        "voorbeelden": [
            "voorkeursterm",
            "voorbeeld_zinnen",
            "praktijkvoorbeelden",
            "tegenvoorbeelden",
            "synoniemen",
            "antoniemen",
            "toelichting",
        ],
    },
    ExportLevel.UITGEBREID: {
        "definitie": [
            "begrip",
            "definitie",
            "categorie",
            "organisatorische_context",
            "juridische_context",
            "wettelijke_basis",
            "ufo_categorie",  # + Ontologie
            "status",
            "validation_score",
            "validation_date",  # + Validatie details
            "validation_issues",  # + Validatie details
            "toelichting_proces",  # + Proces notities
            "source_type",  # + Bron tracking
            "created_at",
            "updated_at",
            "created_by",  # + User info
            "updated_by",  # + User info
            "ketenpartners",  # + Team info
        ],
        "voorbeelden": [
            "voorkeursterm",
            "voorbeeld_zinnen",
            "praktijkvoorbeelden",
            "tegenvoorbeelden",
            "synoniemen",
            "antoniemen",
            "toelichting",
        ],
    },
    ExportLevel.COMPLEET: {
        "definitie": [
            "id",
            "begrip",
            "definitie",
            "categorie",
            "organisatorische_context",
            "juridische_context",
            "wettelijke_basis",
            "ufo_categorie",
            "toelichting_proces",
            "status",
            "version_number",
            "previous_version_id",
            "validation_score",
            "validation_date",
            "validation_issues",
            "source_type",
            "source_reference",
            "imported_from",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "datum_voorstel",
            "ketenpartners",
            "approved_by",
            "approved_at",
            "approval_notes",
            "last_exported_at",
            "export_destinations",
        ],
        "voorbeelden": [
            "voorkeursterm",
            "voorbeeld_zinnen",
            "praktijkvoorbeelden",
            "tegenvoorbeelden",
            "synoniemen",
            "antoniemen",
            "toelichting",
        ],
    },
}


class ExportService:
    """
    Service voor het exporteren van definities.

    Deze service:
    - Gebruikt DataAggregationService voor data verzameling
    - Ondersteunt meerdere export formaten
    - Beheert export bestanden en directories
    - Biedt consistente export functionaliteit
    """

    def __init__(
        self,
        repository: DefinitieRepository,
        data_aggregation_service: DataAggregationService | None = None,
        export_dir: str = "exports",
        validation_orchestrator: Any | None = None,
        enable_validation_gate: bool = False,
    ):
        """
        Initialiseer export service.

        Args:
            repository: Definitie repository
            data_aggregation_service: Data aggregation service (optioneel)
            export_dir: Directory voor exports
        """
        self.repository = repository
        self.data_aggregation_service = (
            data_aggregation_service or DataAggregationService(repository)
        )
        self.export_dir = Path(export_dir)
        self.validation_orchestrator = validation_orchestrator
        self.enable_validation_gate = enable_validation_gate

        # Maak export directory indien nodig
        self.export_dir.mkdir(exist_ok=True)

        logger.info(f"ExportService geïnitialiseerd met export dir: {self.export_dir}")

    def export_definitie(
        self,
        definitie_id: int | None = None,
        definitie_record: DefinitieRecord | None = None,
        additional_data: dict[str, Any] | None = None,
        format: ExportFormat = ExportFormat.TXT,
    ) -> str:
        """
        Exporteer een definitie naar het opgegeven formaat.

        Args:
            definitie_id: ID van definitie om te exporteren
            definitie_record: Definitie record (optioneel)
            additional_data: Extra data voor export
            format: Export formaat

        Returns:
            Pad naar het geëxporteerde bestand
        """
        # Aggregeer data
        try:
            export_data = self.data_aggregation_service.aggregate_definitie_for_export(
                definitie_id=definitie_id,
                definitie_record=definitie_record,
                additional_data=additional_data,
            )
        except ValueError as e:
            # Definitie niet gevonden in database
            logger.error(
                f"Export failed: definitie not found (ID: {definitie_id}): {e}"
            )
            msg = f"Kan definitie {definitie_id} niet exporteren: niet gevonden"
            raise ValueError(msg) from e
        except Exception as e:
            # Database of aggregatie fout
            logger.error(
                f"Export failed: data aggregation error (ID: {definitie_id}): {e}",
                exc_info=True,
            )
            msg = f"Export mislukt: {e!s}"
            raise RuntimeError(msg) from e

        # Validatiegate alleen via async pad ondersteund
        if self.enable_validation_gate and self.validation_orchestrator is not None:
            msg = "Export validatiegate vereist async pad. Roep export_definitie_async aan vanuit de UI via async_bridge."
            raise NotImplementedError(msg)

        # Export naar gekozen formaat
        if format == ExportFormat.TXT:
            return self._export_to_txt(export_data)
        if format == ExportFormat.JSON:
            return self._export_to_json(export_data)
        if format == ExportFormat.CSV:
            return self._export_to_csv(export_data)
        msg = f"Export formaat {format} nog niet geïmplementeerd"
        raise NotImplementedError(msg)

    async def export_definitie_async(
        self,
        definitie_id: int | None = None,
        definitie_record: DefinitieRecord | None = None,
        additional_data: dict[str, Any] | None = None,
        format: ExportFormat = ExportFormat.TXT,
    ) -> str:
        """Asynchrone export met optionele validatiegate."""
        export_data = self.data_aggregation_service.aggregate_definitie_for_export(
            definitie_id=definitie_id,
            definitie_record=definitie_record,
            additional_data=additional_data,
        )
        # Optionele async validatiegate
        if self.enable_validation_gate and self.validation_orchestrator is not None:
            text_for_validation = (
                export_data.definitie_aangepast
                or export_data.definitie_gecorrigeerd
                or export_data.definitie_origineel
            )
            try:
                result = await self.validation_orchestrator.validate_text(
                    begrip=export_data.begrip,
                    text=text_for_validation,
                    ontologische_categorie=None,
                    context=None,
                )
            except Exception as e:  # pragma: no cover - defensive
                msg = f"Validatie mislukt vóór export: {e!s}"
                raise ValueError(msg) from e
            if not isinstance(result, dict) or not result.get("is_acceptable", False):
                msg = "Export geblokkeerd: definitie niet acceptabel volgens validatiegate"
                raise ValueError(msg)

        # Export uitvoeren
        if format == ExportFormat.TXT:
            return self._export_to_txt(export_data)
        if format == ExportFormat.JSON:
            return self._export_to_json(export_data)
        if format == ExportFormat.CSV:
            return self._export_to_csv(export_data)
        msg = f"Export formaat {format} nog niet geïmplementeerd"
        raise NotImplementedError(msg)

    def _export_to_txt(self, export_data: DefinitieExportData) -> str:
        """
        Exporteer naar TXT formaat.

        Dit gebruikt de legacy export functie voor backwards compatibility.
        """
        # Import legacy export functie
        from export.export_txt import exporteer_naar_txt

        # Bereid data voor in legacy formaat
        legacy_data = self.data_aggregation_service.prepare_export_dict(export_data)

        # Gebruik legacy export
        return exporteer_naar_txt(legacy_data)

    def _export_to_json(self, export_data: DefinitieExportData) -> str:
        """Exporteer naar JSON formaat."""
        # Genereer bestandsnaam
        tijdstempel = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        begrip_clean = export_data.begrip.replace(" ", "_").lower()
        bestandsnaam = f"definitie_{begrip_clean}_{tijdstempel}.json"
        pad = self.export_dir / bestandsnaam

        # Bereid data voor
        json_data = {
            "export_info": {
                "export_timestamp": datetime.now(UTC).isoformat(),
                "export_version": "2.0",
                "format": "json",
            },
            "definitie": {
                "begrip": export_data.begrip,
                "definitie_origineel": export_data.definitie_origineel,
                "definitie_gecorrigeerd": export_data.definitie_gecorrigeerd,
                "definitie_aangepast": export_data.definitie_aangepast,
                "marker": export_data.marker,
                "voorkeursterm": export_data.voorkeursterm,
            },
            "metadata": export_data.metadata,
            "context": export_data.context_dict,
            "voorbeelden": {
                "voorbeeld_zinnen": export_data.voorbeeld_zinnen,
                "praktijkvoorbeelden": export_data.praktijkvoorbeelden,
                "tegenvoorbeelden": export_data.tegenvoorbeelden,
            },
            "taalkundig": {
                "synoniemen": export_data.synoniemen,
                "antoniemen": export_data.antoniemen,
                "toelichting": export_data.toelichting,
            },
            "validatie": {
                "toetsresultaten": export_data.toetsresultaten,
                "beoordeling": export_data.beoordeling,
                "beoordeling_gen": export_data.beoordeling_gen,
            },
            "bronnen": {
                "bronnen": export_data.bronnen,
                "bronnen_gebruikt": export_data.bronnen_gebruikt,
            },
            "review": {
                "expert_review": export_data.expert_review,
            },
            "technisch": {
                "prompt_text": export_data.prompt_text,
                "created_at": (
                    export_data.created_at.isoformat()
                    if export_data.created_at
                    else None
                ),
                "updated_at": (
                    export_data.updated_at.isoformat()
                    if export_data.updated_at
                    else None
                ),
            },
        }

        # Schrijf naar bestand
        with open(pad, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Definitie geëxporteerd naar JSON: {pad}")
        return str(pad)

    def _export_to_csv(self, export_data: DefinitieExportData) -> str:
        """Exporteer naar CSV formaat."""
        import csv

        # Genereer bestandsnaam
        tijdstempel = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        begrip_clean = export_data.begrip.replace(" ", "_").lower()
        bestandsnaam = f"definitie_{begrip_clean}_{tijdstempel}.csv"
        pad = self.export_dir / bestandsnaam

        # CSV velden
        fieldnames = [
            "begrip",
            "definitie_origineel",
            "definitie_gecorrigeerd",
            "definitie_aangepast",
            "status",
            "categorie",
            "organisatorische_context",
            "juridische_context",
            "wettelijke_basis",
            "voorkeursterm",
            "synoniemen",
            "antoniemen",
            "toelichting",
            "expert_review",
            "created_at",
            "updated_at",
        ]

        # Schrijf CSV
        with open(pad, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            row = {
                "begrip": export_data.begrip,
                "definitie_origineel": export_data.definitie_origineel,
                "definitie_gecorrigeerd": export_data.definitie_gecorrigeerd,
                "definitie_aangepast": export_data.definitie_aangepast or "",
                "status": export_data.metadata.get("status", ""),
                "categorie": export_data.metadata.get("categorie", ""),
                "organisatorische_context": export_data.metadata.get(
                    "organisatorische_context", ""
                ),
                "juridische_context": export_data.metadata.get(
                    "juridische_context", ""
                ),
                "wettelijke_basis": export_data.metadata.get("wettelijke_basis", ""),
                "voorkeursterm": export_data.voorkeursterm,
                "synoniemen": export_data.synoniemen,
                "antoniemen": export_data.antoniemen,
                "toelichting": export_data.toelichting,
                "expert_review": export_data.expert_review,
                "created_at": (
                    export_data.created_at.isoformat() if export_data.created_at else ""
                ),
                "updated_at": (
                    export_data.updated_at.isoformat() if export_data.updated_at else ""
                ),
            }

            writer.writerow(row)

        logger.info(f"Definitie geëxporteerd naar CSV: {pad}")
        return str(pad)

    def export_multiple_definitions(
        self,
        definitions: list[DefinitieRecord],
        format: ExportFormat = ExportFormat.CSV,
        level: ExportLevel = ExportLevel.BASIS,
    ) -> str:
        """
        Exporteer meerdere definities naar het opgegeven formaat.

        Args:
            definitions: Lijst van definitie records
            format: Export formaat
            level: Export detail level (BASIS, UITGEBREID, COMPLEET)

        Returns:
            Pad naar het geëxporteerde bestand
        """
        if format == ExportFormat.CSV:
            return self._export_multiple_to_csv(definitions, level)
        if format == ExportFormat.EXCEL:
            return self._export_multiple_to_excel(definitions, level)
        if format == ExportFormat.JSON:
            return self._export_multiple_to_json(definitions, level)
        if format == ExportFormat.TXT:
            return self._export_multiple_to_txt(definitions, level)
        raise NotImplementedError(
            f"Bulk export voor formaat {format} nog niet geïmplementeerd"
        )

    def _generate_export_path(self, format: ExportFormat) -> Path:
        """
        Generate timestamped export file path.

        Args:
            format: Export format (determines file extension)

        Returns:
            Path object for export file

        Example:
            >>> self._generate_export_path(ExportFormat.CSV)
            Path("/exports/definities_export_20250128_143022.csv")
        """
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        filename = f"definities_export_{timestamp}.{format.value}"
        return self.export_dir / filename

    def _prepare_export_data(
        self,
        definitions: list[DefinitieRecord],
        level: ExportLevel,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """
        Collect and build export rows for all definitions.

        Args:
            definitions: List of DefinitieRecord to export
            level: Export level determining which fields to include

        Returns:
            Tuple of (rows, fieldnames) where:
            - rows: List of dictionaries with export data
            - fieldnames: List of field names in order

        Raises:
            No exceptions raised - skips definitions with errors and logs warning

        Example:
            >>> data, fields = self._prepare_export_data(definitions, ExportLevel.BASIS)
            >>> len(fields)  # BASIS has 17 fields
            17
        """
        fields_config = EXPORT_LEVEL_FIELDS[level]
        fieldnames = fields_config["definitie"] + fields_config["voorbeelden"]

        data = []
        for d in definitions:
            try:
                export_data = (
                    self.data_aggregation_service.aggregate_definitie_for_export(
                        definitie_record=d
                    )
                )
                row = self._build_export_row(d, export_data, level)
                data.append(row)
            except Exception as e:
                # Log maar skip deze definitie - geen hele export laten falen
                logger.warning(
                    f"Definitie {d.id} ({d.begrip}) overgeslagen bij export: {e}",
                    exc_info=True,
                )
                continue

        return data, fieldnames

    def _build_export_row(
        self,
        definitie: DefinitieRecord,
        export_data: DefinitieExportData,
        level: ExportLevel,
    ) -> dict[str, Any]:
        """
        Build export row dict met velden volgens export level.

        Args:
            definitie: Definitie record uit database
            export_data: Geaggregeerde export data (met voorbeelden)
            level: Export detail level

        Returns:
            Dictionary met geselecteerde velden
        """
        fields_config = EXPORT_LEVEL_FIELDS[level]
        row = {}

        # Definitie velden uit database
        for field in fields_config["definitie"]:
            value = getattr(definitie, field, None)

            # Special handling voor bepaalde velden
            if field in ["created_at", "updated_at"] and value:
                # Voor Excel: strip timezone
                row[field] = value.replace(tzinfo=None) if value.tzinfo else value
            elif field in [
                "validation_issues",
                "ketenpartners",
                "export_destinations",
            ]:
                # JSON velden: converteer naar string
                row[field] = str(value) if value else ""
            elif field == "datum_voorstel" and value:
                row[field] = (
                    value.isoformat() if hasattr(value, "isoformat") else str(value)
                )
            else:
                row[field] = value or ""

        # Voorbeelden velden uit export_data
        if "voorkeursterm" in fields_config["voorbeelden"]:
            row["voorkeursterm"] = export_data.voorkeursterm or ""
        if "voorbeeld_zinnen" in fields_config["voorbeelden"]:
            # Use semicolon delimiter (Dutch CSV standard) to avoid conflicts with pipe characters in text
            row["voorbeeld_zinnen"] = (
                "; ".join(export_data.voorbeeld_zinnen)
                if export_data.voorbeeld_zinnen
                else ""
            )
        if "praktijkvoorbeelden" in fields_config["voorbeelden"]:
            # Use semicolon delimiter (Dutch CSV standard) to avoid conflicts with pipe characters in text
            row["praktijkvoorbeelden"] = (
                "; ".join(export_data.praktijkvoorbeelden)
                if export_data.praktijkvoorbeelden
                else ""
            )
        if "tegenvoorbeelden" in fields_config["voorbeelden"]:
            # Use semicolon delimiter (Dutch CSV standard) to avoid conflicts with pipe characters in text
            row["tegenvoorbeelden"] = (
                "; ".join(export_data.tegenvoorbeelden)
                if export_data.tegenvoorbeelden
                else ""
            )
        if "synoniemen" in fields_config["voorbeelden"]:
            row["synoniemen"] = export_data.synoniemen or ""
        if "antoniemen" in fields_config["voorbeelden"]:
            row["antoniemen"] = export_data.antoniemen or ""
        if "toelichting" in fields_config["voorbeelden"]:
            row["toelichting"] = export_data.toelichting or ""

        return row

    def _export_multiple_to_csv(
        self,
        definitions: list[DefinitieRecord],
        level: ExportLevel = ExportLevel.BASIS,
    ) -> str:
        """Exporteer meerdere definities naar CSV."""
        import csv

        # Prepare data using helper
        data, fieldnames = self._prepare_export_data(definitions, level)
        path = self._generate_export_path(ExportFormat.CSV)

        # Format-specific: CSV writing
        with open(path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in data:
                # Convert datetime to ISO string for CSV compatibility
                for field in fieldnames:
                    if field in row and isinstance(row[field], datetime):
                        row[field] = row[field].isoformat()
                writer.writerow(row)

        logger.info(
            f"{len(data)} definities geëxporteerd naar CSV ({level.value}): {path}"
        )
        return str(path)

    def _export_multiple_to_excel(
        self,
        definitions: list[DefinitieRecord],
        level: ExportLevel = ExportLevel.BASIS,
    ) -> str:
        """Exporteer meerdere definities naar Excel."""
        import pandas as pd

        # Prepare data using helper (datetime already timezone-naive in helper)
        data, fieldnames = self._prepare_export_data(definitions, level)
        path = self._generate_export_path(ExportFormat.EXCEL)

        # Format-specific: Excel writing with pandas
        df = pd.DataFrame(data, columns=fieldnames)
        df.to_excel(path, index=False, engine="openpyxl")

        logger.info(
            f"{len(data)} definities geëxporteerd naar Excel ({level.value}): {path}"
        )
        return str(path)

    def _export_multiple_to_json(
        self,
        definitions: list[DefinitieRecord],
        level: ExportLevel = ExportLevel.BASIS,
    ) -> str:
        """Exporteer meerdere definities naar JSON."""
        # Prepare data using helper
        data, _ = self._prepare_export_data(definitions, level)
        path = self._generate_export_path(ExportFormat.JSON)

        # Format-specific: JSON structure with metadata
        json_data = {
            "export_info": {
                "export_timestamp": datetime.now(UTC).isoformat(),
                "export_version": "2.0",
                "format": "json",
                "export_level": level.value,
                "total_definitions": len(data),
            },
            "definities": [],
        }

        # Convert datetime objects to ISO strings for JSON
        for row in data:
            for key, value in row.items():
                if isinstance(value, datetime):
                    row[key] = value.isoformat()
            json_data["definities"].append(row)

        # Write to file
        with open(path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        logger.info(
            f"{len(data)} definities geëxporteerd naar JSON ({level.value}): {path}"
        )
        return str(path)

    def _export_multiple_to_txt(
        self,
        definitions: list[DefinitieRecord],
        level: ExportLevel = ExportLevel.BASIS,
    ) -> str:
        """Exporteer meerdere definities naar TXT."""
        # Prepare data using helper
        data, _ = self._prepare_export_data(definitions, level)
        path = self._generate_export_path(ExportFormat.TXT)

        # Format-specific: Human-readable text with headers
        lines = [
            "DEFINITIE EXPORT",
            "=" * 80,
            f"Aantal definities: {len(data)}",
            f"Export niveau: {level.value.upper()}",
            f"Export datum: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 80,
            "",
        ]

        # Field labels voor mooie weergave
        field_labels = {
            "id": "ID",
            "begrip": "Begrip",
            "definitie": "Definitie",
            "categorie": "Categorie",
            "organisatorische_context": "Organisatorische context",
            "juridische_context": "Juridische context",
            "wettelijke_basis": "Wettelijke basis",
            "ufo_categorie": "UFO categorie",
            "toelichting_proces": "Toelichting proces",
            "status": "Status",
            "version_number": "Versie",
            "previous_version_id": "Vorige versie ID",
            "validation_score": "Validatie score",
            "validation_date": "Validatie datum",
            "validation_issues": "Validatie issues",
            "source_type": "Bron type",
            "source_reference": "Bron referentie",
            "imported_from": "Geïmporteerd van",
            "created_at": "Aangemaakt op",
            "updated_at": "Bijgewerkt op",
            "created_by": "Aangemaakt door",
            "updated_by": "Bijgewerkt door",
            "datum_voorstel": "Datum voorstel",
            "ketenpartners": "Ketenpartners",
            "approved_by": "Goedgekeurd door",
            "approved_at": "Goedgekeurd op",
            "approval_notes": "Goedkeurings notities",
            "last_exported_at": "Laatst geëxporteerd op",
            "export_destinations": "Export bestemmingen",
            "voorkeursterm": "Voorkeursterm",
            "voorbeeld_zinnen": "Voorbeeld zinnen",
            "praktijkvoorbeelden": "Praktijkvoorbeelden",
            "tegenvoorbeelden": "Tegenvoorbeelden",
            "synoniemen": "Synoniemen",
            "antoniemen": "Antoniemen",
            "toelichting": "Toelichting",
        }

        # Format each definition
        for row in data:
            # Toon alleen niet-lege velden
            for field, value in row.items():
                if value:  # Skip lege strings, None, etc.
                    # Converteer datetime naar leesbare string
                    if isinstance(value, datetime):
                        value = value.strftime("%Y-%m-%d %H:%M:%S")

                    label = field_labels.get(field, field.replace("_", " ").title())

                    # Speciale weergave voor lijst velden (komen als "; " separated string)
                    if field in [
                        "voorbeeld_zinnen",
                        "praktijkvoorbeelden",
                        "tegenvoorbeelden",
                    ]:
                        lines.append(f"{label}:")
                        items = value.split("; ") if isinstance(value, str) else []
                        for item in items:
                            if item:
                                lines.append(f"  - {item}")
                        lines.append("")
                    else:
                        lines.append(f"{label}: {value}")

            lines.extend(["-" * 80, ""])

        # Write to file
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info(
            f"{len(data)} definities geëxporteerd naar TXT ({level.value}): {path}"
        )
        return str(path)

    def get_export_history(self, begrip: str | None = None) -> list[dict[str, Any]]:
        """
        Haal export geschiedenis op.

        Args:
            begrip: Filter op specifiek begrip (optioneel)

        Returns:
            Lijst met export informatie
        """
        exports = []

        for file_path in self.export_dir.iterdir():
            if file_path.is_file():
                # Parse bestandsnaam
                parts = file_path.stem.split("_")
                if len(parts) >= 3 and parts[0] == "definitie":
                    file_begrip = "_".join(parts[1:-2])

                    if (
                        begrip is None
                        or file_begrip == begrip.replace(" ", "_").lower()
                    ):
                        exports.append(
                            {
                                "file": file_path.name,
                                "path": str(file_path),
                                "begrip": file_begrip.replace("_", " "),
                                "format": file_path.suffix[1:],
                                "size": file_path.stat().st_size,
                                "created": datetime.fromtimestamp(
                                    file_path.stat().st_ctime
                                ),
                            }
                        )

        # Sorteer op datum (nieuwste eerst)
        exports.sort(key=lambda x: x["created"], reverse=True)

        return exports

    def cleanup_old_exports(self, days: int = 30) -> int:
        """
        Verwijder oude export bestanden.

        Args:
            days: Aantal dagen om te behouden

        Returns:
            Aantal verwijderde bestanden
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        removed = 0

        for file_path in self.export_dir.iterdir():
            if file_path.is_file():
                file_date = datetime.fromtimestamp(file_path.stat().st_ctime)
                if file_date < cutoff_date:
                    file_path.unlink()
                    removed += 1
                    logger.debug(f"Verwijderd oud export bestand: {file_path}")

        logger.info(f"Cleanup: {removed} oude export bestanden verwijderd")
        return removed
