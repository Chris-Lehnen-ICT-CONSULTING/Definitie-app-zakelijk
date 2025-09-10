"""
UI Components Adapter.

Dit module biedt een brug tussen de legacy UI componenten die SessionStateManager gebruiken
en de nieuwe clean services die geen UI dependencies hebben.
"""

import logging
from typing import Any

import streamlit as st

from services.service_factory import get_definition_service
from ui.helpers.context_adapter import get_context_adapter
from ui.session_state import SessionStateManager

logger = logging.getLogger(__name__)


class UIComponentsAdapter:
    """
    Adapter die UI componenten verbindt met nieuwe services.

    Deze adapter:
    - Verzamelt data uit SessionStateManager
    - Roept nieuwe services aan
    - Update UI met resultaten
    - Handelt backwards compatibility af
    """

    def __init__(self):
        """Initialiseer adapter."""
        self.service = get_definition_service()
        logger.info("UIComponentsAdapter geïnitialiseerd")

    def export_definition(self, format: str = "txt") -> bool:
        """
        Export definitie vanuit UI.

        Args:
            format: Export formaat (txt, json, csv)

        Returns:
            True als export succesvol, anders False
        """
        try:
            # Verzamel UI data uit session state
            ui_data = self._collect_ui_data_for_export()

            # Check of we een definitie ID hebben
            definition_id = SessionStateManager.get_value("current_definition_id")

            # Roep service aan
            result = self.service.export_definition(
                definition_id=definition_id, ui_data=ui_data, format=format
            )

            # Handle resultaat
            if result["success"]:
                st.success(f"✅ {result['message']}")

                # Optioneel: bied download aan
                if result.get("path"):
                    with open(result["path"], "rb") as f:
                        st.download_button(
                            label=f"📥 Download {result['filename']}",
                            data=f,
                            file_name=result["filename"],
                            mime=self._get_mime_type(format),
                        )

                return True
            st.error(f"❌ Export mislukt: {result.get('error', 'Onbekende fout')}")
            return False

        except Exception as e:
            logger.error(f"Export fout: {e}")
            st.error(f"❌ Technische fout bij export: {e!s}")
            return False

    def _collect_ui_data_for_export(self) -> dict[str, Any]:
        """
        Verzamel alle relevante data uit SessionStateManager voor export.

        Returns:
            Dictionary met UI data
        """
        # Basis velden
        ui_data = {
            "begrip": SessionStateManager.get_value("begrip"),
            "definitie_origineel": SessionStateManager.get_value("gegenereerd"),
            "definitie_gecorrigeerd": SessionStateManager.get_value(
                "definitie_gecorrigeerd"
            ),
            "aangepaste_definitie": SessionStateManager.get_value(
                "aangepaste_definitie"
            ),
            "expert_review": SessionStateManager.get_value("expert_review", ""),
            "voorkeursterm": SessionStateManager.get_value("voorkeursterm", ""),
        }

        # Context: prefer centralized ContextManager via adapter; fallback to SessionStateManager
        try:
            adapter = get_context_adapter()
            cm = adapter.to_generation_request()
            ui_data["context_dict"] = {
                "organisatorisch": cm.get("organisatorische_context", []),
                "juridisch": cm.get("juridische_context", []),
                "wettelijk": cm.get("wettelijke_basis", []),
            }
        except Exception:
            ui_data["context_dict"] = {
                "organisatorisch": SessionStateManager.get_value("context", []),
                "juridisch": SessionStateManager.get_value("juridische_context", []),
                "wettelijk": SessionStateManager.get_value("wet_basis", []),
            }

        # Metadata
        ui_data["metadata"] = {
            "datum_voorstel": SessionStateManager.get_value("datum"),
            "voorgesteld_door": SessionStateManager.get_value("voorsteller", ""),
            "ketenpartners": SessionStateManager.get_value("ketenpartners", []),
            "marker": SessionStateManager.get_value("marker"),
        }

        # Voorbeelden en content
        ui_data["voorbeeld_zinnen"] = SessionStateManager.get_value(
            "voorbeeld_zinnen", []
        )
        ui_data["praktijkvoorbeelden"] = SessionStateManager.get_value(
            "praktijkvoorbeelden", []
        )
        ui_data["tegenvoorbeelden"] = SessionStateManager.get_value(
            "tegenvoorbeelden", []
        )
        ui_data["synoniemen"] = SessionStateManager.get_value("synoniemen", "")
        ui_data["antoniemen"] = SessionStateManager.get_value("antoniemen", "")
        ui_data["toelichting"] = SessionStateManager.get_value("toelichting", "")

        # Validatie en toetsing
        ui_data["beoordeling"] = SessionStateManager.get_value("beoordeling", [])
        ui_data["beoordeling_gen"] = SessionStateManager.get_value(
            "beoordeling_gen", []
        )
        ui_data["toetsresultaten"] = SessionStateManager.get_value(
            "toetsresultaten", {}
        )

        # Bronnen
        ui_data["bronnen_gebruikt"] = SessionStateManager.get_value(
            "bronnen_gebruikt", ""
        )
        ui_data["bronnen"] = SessionStateManager.get_value("bronnen", [])

        # Technical
        ui_data["prompt_text"] = SessionStateManager.get_value("prompt_text")

        # Filter out None values
        return {k: v for k, v in ui_data.items() if v is not None}

    def _get_mime_type(self, format: str) -> str:
        """Get MIME type voor download."""
        mime_types = {
            "txt": "text/plain",
            "json": "application/json",
            "csv": "text/csv",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "pdf": "application/pdf",
        }
        return mime_types.get(format, "application/octet-stream")

    def prepare_for_review(self, definition_id: int, notes: str | None = None) -> bool:
        """
        Bereid definitie voor voor review.

        Args:
            definition_id: ID van definitie
            notes: Review notities

        Returns:
            True als succesvol
        """
        try:
            result = self.service.ui_service.prepare_definition_for_review(
                definitie_id=definition_id,
                reviewer_notes=notes,
                user=SessionStateManager.get_value("current_user", "web_user"),
            )

            if result["success"]:
                st.success(f"✅ {result['message']}")
                return True
            st.error(f"❌ {result['message']}")
            return False

        except Exception as e:
            logger.error(f"Review voorbereiding fout: {e}")
            st.error(f"❌ Technische fout: {e!s}")
            return False

    def get_export_formats(self) -> list[dict[str, Any]]:
        """
        Haal beschikbare export formaten op.

        Returns:
            Lijst met formaat opties
        """
        try:
            return self.service.ui_service.get_export_formats()
        except Exception as e:
            logger.error(f"Fout bij ophalen export formaten: {e}")
            # Fallback
            return [
                {"value": "txt", "label": "TXT", "available": True},
                {"value": "json", "label": "JSON", "available": True},
                {"value": "csv", "label": "CSV", "available": True},
            ]


# Singleton instance
_adapter_instance = None


def get_ui_adapter() -> UIComponentsAdapter:
    """Get of create UI adapter instance."""
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = UIComponentsAdapter()
    return _adapter_instance


def render_export_button_new():
    """
    Nieuwe export button die de clean services gebruikt.

    Deze functie kan de legacy _render_export_button vervangen.
    """
    if SessionStateManager.has_generated_definition():
        adapter = get_ui_adapter()

        # Get beschikbare formaten
        formats = adapter.get_export_formats()
        available_formats = [f for f in formats if f.get("available", True)]

        # Render export opties
        col1, col2 = st.columns([3, 1])

        with col1:
            selected_format = st.selectbox(
                "Export formaat",
                options=[f["value"] for f in available_formats],
                format_func=lambda x: next(
                    f["label"] for f in formats if f["value"] == x
                ),
                key="export_format_select",
            )

        with col2:
            if st.button("📤 Exporteer", key="export_button_new"):
                adapter.export_definition(format=selected_format)
