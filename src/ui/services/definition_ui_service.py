"""
Definition UI Service.

Facade service die UI functionaliteit biedt zonder directe session state dependencies.
Dit is onderdeel van de GVI Week 0 implementatie.
"""

import logging
from typing import Any

from database.definitie_repository import DefinitieRecord, DefinitieRepository
from services.data_aggregation_service import DataAggregationService
from services.export_service import ExportFormat, ExportService
from services.workflow_service import WorkflowService

logger = logging.getLogger(__name__)


class DefinitionUIService:
    """
    Facade service voor UI operaties.

    Deze service:
    - Biedt een clean interface voor UI componenten
    - Verbergt complexiteit van onderliggende services
    - Elimineert directe UI-to-repository communicatie
    - Centraliseert business logic voor UI acties
    """

    def __init__(
        self,
        repository: DefinitieRepository,
        workflow_service: WorkflowService | None = None,
        export_service: ExportService | None = None,
        data_aggregation_service: DataAggregationService | None = None,
    ):
        """
        Initialiseer UI service.

        Args:
            repository: Definitie repository
            workflow_service: Workflow service (optioneel)
            export_service: Export service (optioneel)
            data_aggregation_service: Data aggregation service (optioneel)
        """
        self.repository = repository

        # Initialize services if not provided
        self.workflow_service = workflow_service or WorkflowService()
        self.data_aggregation_service = (
            data_aggregation_service or DataAggregationService(repository)
        )
        self.export_service = export_service or ExportService(
            repository=repository,
            data_aggregation_service=self.data_aggregation_service,
        )

        logger.info("DefinitionUIService geïnitialiseerd")

    def export_definition(
        self,
        definitie_id: int | None = None,
        definitie_record: DefinitieRecord | None = None,
        ui_data: dict[str, Any] | None = None,
        format: str = "txt",
    ) -> dict[str, Any]:
        """
        Exporteer een definitie vanuit de UI.

        Args:
            definitie_id: ID van definitie om te exporteren
            definitie_record: Definitie record (optioneel)
            ui_data: Extra data uit UI (zoals voorbeelden, review, etc.)
            format: Export formaat (txt, json, csv)

        Returns:
            Dictionary met:
            - success: bool
            - path: str (bestandspad)
            - filename: str (bestandsnaam)
            - message: str
            - error: Optional[str]
        """
        try:
            # Convert format string to enum
            export_format = ExportFormat(format.lower())

            # Prepare additional data from UI
            additional_data = (
                self._prepare_ui_data_for_export(ui_data) if ui_data else None
            )

            # Export via service
            export_path = self.export_service.export_definitie(
                definitie_id=definitie_id,
                definitie_record=definitie_record,
                additional_data=additional_data,
                format=export_format,
            )

            # Extract filename
            import os

            filename = os.path.basename(export_path)

            logger.info(f"Definitie geëxporteerd naar {export_path}")

            return {
                "success": True,
                "path": export_path,
                "filename": filename,
                "message": f"Definitie succesvol geëxporteerd naar {filename}",
                "error": None,
            }

        except Exception as e:
            logger.error(f"Export mislukt: {e}")
            return {
                "success": False,
                "path": None,
                "filename": None,
                "message": "Export mislukt",
                "error": str(e),
            }

    def _prepare_ui_data_for_export(self, ui_data: dict[str, Any]) -> dict[str, Any]:
        """
        Bereid UI data voor voor export.

        Transformeert UI-specifieke data naar export-vriendelijk formaat.
        """
        # Direct mappings
        prepared_data = {}

        # Map UI fields to export fields
        field_mappings = {
            "aangepaste_definitie": "definitie_aangepast",
            "expert_review": "expert_review",
            "voorkeursterm": "voorkeursterm",
            "voorbeeld_zinnen": "voorbeeld_zinnen",
            "praktijkvoorbeelden": "praktijkvoorbeelden",
            "tegenvoorbeelden": "tegenvoorbeelden",
            "synoniemen": "synoniemen",
            "antoniemen": "antoniemen",
            "toelichting": "toelichting",
            "bronnen_gebruikt": "bronnen_gebruikt",
            "beoordeling": "beoordeling",
            "beoordeling_gen": "beoordeling_gen",
            "toetsresultaten": "toetsresultaten",
            "ketenpartners": "ketenpartners",
            "marker": "marker",
            "prompt_text": "prompt_text",
        }

        for ui_field, export_field in field_mappings.items():
            if ui_field in ui_data:
                prepared_data[export_field] = ui_data[ui_field]

        # Handle context dict specially
        if "context_dict" in ui_data:
            prepared_data["context_dict"] = ui_data["context_dict"]
        elif any(
            key in ui_data
            for key in [
                "organisatorisch_context",
                "juridisch_context",
                "wettelijk_context",
            ]
        ):
            prepared_data["context_dict"] = {
                "organisatorisch": ui_data.get("organisatorisch_context", []),
                "juridisch": ui_data.get("juridisch_context", []),
                "wettelijk": ui_data.get("wettelijk_context", []),
            }

        # Handle metadata
        if "metadata" in ui_data:
            prepared_data["metadata"] = ui_data["metadata"]
        else:
            # Build metadata from individual fields
            metadata = {}
            metadata_fields = [
                "datum_voorstel",
                "voorgesteld_door",
                "organisatie",
                "categorie",
                "domein",
                "status",
                "versie",
            ]
            for field in metadata_fields:
                if field in ui_data:
                    metadata[field] = ui_data[field]

            if metadata:
                prepared_data["metadata"] = metadata

        return prepared_data

    def get_export_formats(self) -> list[dict[str, str]]:
        """
        Haal beschikbare export formaten op.

        Returns:
            Lijst met formaat informatie
        """
        formats = []
        for format in ExportFormat:
            format_info = {
                "value": format.value,
                "label": format.value.upper(),
                "description": self._get_format_description(format),
            }

            # Mark unavailable formats
            if format in [ExportFormat.DOCX, ExportFormat.PDF]:
                format_info["available"] = False
                format_info["label"] += " (binnenkort)"
            else:
                format_info["available"] = True

            formats.append(format_info)

        return formats

    def _get_format_description(self, format: ExportFormat) -> str:
        """Get description for export format."""
        descriptions = {
            ExportFormat.TXT: "Platte tekst formaat, geschikt voor eenvoudige opslag",
            ExportFormat.JSON: "Gestructureerd formaat, geschikt voor systeem integratie",
            ExportFormat.CSV: "Tabel formaat, geschikt voor Excel en data analyse",
            ExportFormat.DOCX: "Word document formaat, geschikt voor rapportage",
            ExportFormat.PDF: "PDF formaat, geschikt voor archivering",
        }
        return descriptions.get(format, "")

    def prepare_definition_for_review(
        self,
        definitie_id: int,
        reviewer_notes: str | None = None,
        user: str = "web_user",
    ) -> dict[str, Any]:
        """
        Bereid definitie voor voor review.

        Args:
            definitie_id: ID van definitie
            reviewer_notes: Notities van reviewer
            user: Gebruiker die actie uitvoert

        Returns:
            Dictionary met resultaat
        """
        try:
            # Get definition
            definitie = self.repository.get_definitie(definitie_id)
            if not definitie:
                return {
                    "success": False,
                    "message": f"Definitie {definitie_id} niet gevonden",
                    "error": "NOT_FOUND",
                }

            # Check if transition is allowed
            if not self.workflow_service.can_change_status(
                current_status=definitie.status, new_status="REVIEW"
            ):
                return {
                    "success": False,
                    "message": f"Definitie kan niet voor review worden ingediend vanuit status {definitie.status}",
                    "error": "INVALID_TRANSITION",
                }

            # Prepare status change
            change_data = self.workflow_service.submit_for_review(
                definition_id=definitie_id, user=user, notes=reviewer_notes
            )

            return {
                "success": True,
                "message": "Definitie klaar voor review",
                "change_data": change_data,
                "definition": definitie,
            }

        except Exception as e:
            logger.error(f"Fout bij voorbereiden review: {e}")
            return {
                "success": False,
                "message": "Technische fout bij voorbereiden review",
                "error": str(e),
            }

    def get_definition_summary(self, definitie_id: int) -> dict[str, Any] | None:
        """
        Haal samenvatting op voor een definitie.

        Args:
            definitie_id: ID van definitie

        Returns:
            Dictionary met definitie samenvatting of None
        """
        try:
            definitie = self.repository.get_definitie(definitie_id)
            if not definitie:
                return None

            return {
                "id": definitie.id,
                "begrip": definitie.begrip,
                "definitie": (
                    definitie.definitie[:200] + "..."
                    if len(definitie.definitie) > 200
                    else definitie.definitie
                ),
                "status": definitie.status,
                "categorie": definitie.categorie,
                "created_at": definitie.created_at,
                "created_by": definitie.created_by,
                "can_edit": self.workflow_service.can_change_status(
                    definitie.status, "DRAFT"
                ),
                "can_review": self.workflow_service.can_change_status(
                    definitie.status, "REVIEW"
                ),
                "can_approve": self.workflow_service.can_change_status(
                    definitie.status, "APPROVED"
                ),
            }

        except Exception as e:
            logger.error(f"Fout bij ophalen definitie samenvatting: {e}")
            return None
