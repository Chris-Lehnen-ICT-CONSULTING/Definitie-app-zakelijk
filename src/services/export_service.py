"""
Export Service.

Service voor het exporteren van definities naar verschillende formaten.
Gebruikt DataAggregationService om data te verzamelen zonder directe UI dependencies.
"""

import asyncio
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

        # Optionele validatiegate vóór export
        if self.enable_validation_gate and self.validation_orchestrator is not None:
            text_for_validation = (
                export_data.definitie_aangepast
                or export_data.definitie_gecorrigeerd
                or export_data.definitie_origineel
            )
            try:
                # Check if we're already in an async context
                loop = asyncio.get_running_loop()
                # In async context: run coroutine thread-safely
                fut = asyncio.run_coroutine_threadsafe(
                    self.validation_orchestrator.validate_text(
                        begrip=export_data.begrip,
                        text=text_for_validation,
                        ontologische_categorie=None,
                        context=None,
                    ),
                    loop,
                )
                result = fut.result()
            except RuntimeError:
                # No running loop: safe to run
                result = asyncio.run(
                    self.validation_orchestrator.validate_text(
                        begrip=export_data.begrip,
                        text=text_for_validation,
                        ontologische_categorie=None,
                        context=None,
                    )
                )
            except Exception as e:  # pragma: no cover - defensive
                msg = f"Validatie mislukt vóór export: {e!s}"
                raise ValueError(msg)
            if not isinstance(result, dict) or not result.get("is_acceptable", False):
                msg = "Export geblokkeerd: definitie niet acceptabel volgens validatiegate"
                raise ValueError(msg)

        # Export naar gekozen formaat
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
            "juridische_context",
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
                "juridische_context": export_data.metadata.get("juridische_context", ""),
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
