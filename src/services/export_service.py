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
        export_data = self.data_aggregation_service.aggregate_definitie_for_export(
            definitie_id=definitie_id,
            definitie_record=definitie_record,
            additional_data=additional_data,
        )

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
                raise ValueError(msg)
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
    ) -> str:
        """
        Exporteer meerdere definities naar het opgegeven formaat.

        Args:
            definitions: Lijst van definitie records
            format: Export formaat

        Returns:
            Pad naar het geëxporteerde bestand
        """
        if format == ExportFormat.CSV:
            return self._export_multiple_to_csv(definitions)
        elif format == ExportFormat.EXCEL:
            return self._export_multiple_to_excel(definitions)
        elif format == ExportFormat.JSON:
            return self._export_multiple_to_json(definitions)
        elif format == ExportFormat.TXT:
            return self._export_multiple_to_txt(definitions)
        else:
            raise NotImplementedError(
                f"Bulk export voor formaat {format} nog niet geïmplementeerd"
            )

    def _export_multiple_to_csv(self, definitions: list[DefinitieRecord]) -> str:
        """Exporteer meerdere definities naar CSV."""
        import csv

        # Genereer bestandsnaam
        tijdstempel = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        bestandsnaam = f"definities_export_{tijdstempel}.csv"
        pad = self.export_dir / bestandsnaam

        # CSV velden - inclusief voorbeelden!
        fieldnames = [
            "begrip",
            "definitie",
            "categorie",
            "organisatorische_context",
            "juridische_context",
            "wettelijke_basis",
            "status",
            "validation_score",
            "voorkeursterm",
            "synoniemen",
            "antoniemen",
            "toelichting",
            "voorbeeld_zinnen",
            "praktijkvoorbeelden",
            "tegenvoorbeelden",
            "created_at",
            "updated_at",
        ]

        # Schrijf CSV
        with open(pad, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for d in definitions:
                # Aggregeer data inclusief voorbeelden
                export_data = (
                    self.data_aggregation_service.aggregate_definitie_for_export(
                        definitie_record=d
                    )
                )

                row = {
                    "begrip": d.begrip,
                    "definitie": d.definitie,
                    "categorie": d.categorie,
                    "organisatorische_context": d.organisatorische_context,
                    "juridische_context": d.juridische_context or "",
                    "wettelijke_basis": d.wettelijke_basis or "",
                    "status": d.status,
                    "validation_score": d.validation_score or "",
                    "voorkeursterm": export_data.voorkeursterm or "",
                    "synoniemen": export_data.synoniemen or "",
                    "antoniemen": export_data.antoniemen or "",
                    "toelichting": export_data.toelichting or "",
                    "voorbeeld_zinnen": (
                        " | ".join(export_data.voorbeeld_zinnen)
                        if export_data.voorbeeld_zinnen
                        else ""
                    ),
                    "praktijkvoorbeelden": (
                        " | ".join(export_data.praktijkvoorbeelden)
                        if export_data.praktijkvoorbeelden
                        else ""
                    ),
                    "tegenvoorbeelden": (
                        " | ".join(export_data.tegenvoorbeelden)
                        if export_data.tegenvoorbeelden
                        else ""
                    ),
                    "created_at": d.created_at.isoformat() if d.created_at else "",
                    "updated_at": d.updated_at.isoformat() if d.updated_at else "",
                }

                writer.writerow(row)

        logger.info(f"{len(definitions)} definities geëxporteerd naar CSV: {pad}")
        return str(pad)

    def _export_multiple_to_excel(self, definitions: list[DefinitieRecord]) -> str:
        """Exporteer meerdere definities naar Excel."""
        import pandas as pd

        # Genereer bestandsnaam
        tijdstempel = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        bestandsnaam = f"definities_export_{tijdstempel}.xlsx"
        pad = self.export_dir / bestandsnaam

        # Verzamel data
        data = []
        for d in definitions:
            export_data = self.data_aggregation_service.aggregate_definitie_for_export(
                definitie_record=d
            )

            # Convert timezone-aware datetimes to naive for Excel compatibility
            created_at_naive = None
            if d.created_at:
                created_at_naive = (
                    d.created_at.replace(tzinfo=None)
                    if d.created_at.tzinfo
                    else d.created_at
                )

            updated_at_naive = None
            if d.updated_at:
                updated_at_naive = (
                    d.updated_at.replace(tzinfo=None)
                    if d.updated_at.tzinfo
                    else d.updated_at
                )

            data.append(
                {
                    "begrip": d.begrip,
                    "definitie": d.definitie,
                    "categorie": d.categorie,
                    "organisatorische_context": d.organisatorische_context,
                    "juridische_context": d.juridische_context or "",
                    "wettelijke_basis": d.wettelijke_basis or "",
                    "status": d.status,
                    "validation_score": d.validation_score,
                    "voorkeursterm": export_data.voorkeursterm or "",
                    "synoniemen": export_data.synoniemen or "",
                    "antoniemen": export_data.antoniemen or "",
                    "toelichting": export_data.toelichting or "",
                    "voorbeeld_zinnen": (
                        " | ".join(export_data.voorbeeld_zinnen)
                        if export_data.voorbeeld_zinnen
                        else ""
                    ),
                    "praktijkvoorbeelden": (
                        " | ".join(export_data.praktijkvoorbeelden)
                        if export_data.praktijkvoorbeelden
                        else ""
                    ),
                    "tegenvoorbeelden": (
                        " | ".join(export_data.tegenvoorbeelden)
                        if export_data.tegenvoorbeelden
                        else ""
                    ),
                    "created_at": created_at_naive,
                    "updated_at": updated_at_naive,
                }
            )

        # Maak DataFrame en export naar Excel
        df = pd.DataFrame(data)
        df.to_excel(pad, index=False, engine="openpyxl")

        logger.info(f"{len(definitions)} definities geëxporteerd naar Excel: {pad}")
        return str(pad)

    def _export_multiple_to_json(self, definitions: list[DefinitieRecord]) -> str:
        """Exporteer meerdere definities naar JSON."""
        # Genereer bestandsnaam
        tijdstempel = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        bestandsnaam = f"definities_export_{tijdstempel}.json"
        pad = self.export_dir / bestandsnaam

        # Verzamel data
        json_data = {
            "export_info": {
                "export_timestamp": datetime.now(UTC).isoformat(),
                "export_version": "2.0",
                "format": "json",
                "total_definitions": len(definitions),
            },
            "definities": [],
        }

        for d in definitions:
            export_data = self.data_aggregation_service.aggregate_definitie_for_export(
                definitie_record=d
            )

            json_data["definities"].append(
                {
                    "begrip": export_data.begrip,
                    "definitie": d.definitie,
                    "categorie": d.categorie,
                    "context": {
                        "organisatorische_context": d.organisatorische_context,
                        "juridische_context": d.juridische_context or "",
                        "wettelijke_basis": d.wettelijke_basis or "",
                    },
                    "status": d.status,
                    "validation_score": d.validation_score,
                    "voorkeursterm": export_data.voorkeursterm,
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
                    "metadata": {
                        "created_at": (
                            d.created_at.isoformat() if d.created_at else None
                        ),
                        "updated_at": (
                            d.updated_at.isoformat() if d.updated_at else None
                        ),
                    },
                }
            )

        # Schrijf naar bestand
        with open(pad, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        logger.info(f"{len(definitions)} definities geëxporteerd naar JSON: {pad}")
        return str(pad)

    def _export_multiple_to_txt(self, definitions: list[DefinitieRecord]) -> str:
        """Exporteer meerdere definities naar TXT."""
        # Genereer bestandsnaam
        tijdstempel = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        bestandsnaam = f"definities_export_{tijdstempel}.txt"
        pad = self.export_dir / bestandsnaam

        lines = [
            "DEFINITIE EXPORT",
            "=" * 80,
            f"Aantal definities: {len(definitions)}",
            f"Export datum: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 80,
            "",
        ]

        for d in definitions:
            export_data = self.data_aggregation_service.aggregate_definitie_for_export(
                definitie_record=d
            )

            lines.extend(
                [
                    f"Begrip: {d.begrip}",
                    f"Definitie: {d.definitie}",
                    f"Categorie: {d.categorie}",
                    f"Context: {d.organisatorische_context}",
                    f"Status: {d.status}",
                    f"Validation score: {d.validation_score or 'n/a'}",
                    "",
                ]
            )

            if export_data.voorkeursterm:
                lines.append(f"Voorkeursterm: {export_data.voorkeursterm}")

            if export_data.voorbeeld_zinnen:
                lines.append("Voorbeeld zinnen:")
                for vb in export_data.voorbeeld_zinnen:
                    lines.append(f"  - {vb}")
                lines.append("")

            if export_data.praktijkvoorbeelden:
                lines.append("Praktijkvoorbeelden:")
                for vb in export_data.praktijkvoorbeelden:
                    lines.append(f"  - {vb}")
                lines.append("")

            if export_data.tegenvoorbeelden:
                lines.append("Tegenvoorbeelden:")
                for vb in export_data.tegenvoorbeelden:
                    lines.append(f"  - {vb}")
                lines.append("")

            if export_data.toelichting:
                lines.append(f"Toelichting: {export_data.toelichting}")
                lines.append("")

            lines.extend(["-" * 80, ""])

        # Schrijf naar bestand
        with open(pad, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info(f"{len(definitions)} definities geëxporteerd naar TXT: {pad}")
        return str(pad)

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
