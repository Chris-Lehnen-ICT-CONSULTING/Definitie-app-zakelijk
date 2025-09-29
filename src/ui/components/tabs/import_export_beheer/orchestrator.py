"""
Import Export Beheer Orchestrator - Hoofdcomponent die alles samenbrengt.

Deze orchestrator gebruikt de modulaire componenten in plaats van alle logica
in één bestand te hebben. Dit voorkomt het God Object anti-pattern.
"""

import logging
import streamlit as st

from database.definitie_repository import DefinitieRepository
from services.service_factory import get_definition_service
from ui.session_state import SessionStateManager

from .csv_importer import CSVImporter
from .format_exporter import FormatExporter
from .bulk_operations import BulkOperations
from .database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class ImportExportOrchestrator:
    """Orchestreert alle import/export/beheer componenten."""

    def __init__(self, repository: DefinitieRepository):
        """Initialize orchestrator met repository en componenten."""
        self.repository = repository
        self.session_state = SessionStateManager()

        # Initialize componenten (dependency injection)
        self.csv_importer = CSVImporter(repository)
        self.format_exporter = FormatExporter(repository)
        self.bulk_operations = BulkOperations(repository)
        self.database_manager = DatabaseManager(repository)

        # Lazy load service wanneer nodig
        self._service = None

    @property
    def service(self):
        """Lazy load definition service."""
        if self._service is None:
            try:
                self._service = get_definition_service()
            except Exception as e:
                logger.warning(f"Could not initialize service: {e}")
                # Dummy service voor test omgevingen
                class _DummyService:
                    def get_service_info(self) -> dict:
                        return {"service_mode": "dummy", "version": "test"}
                self._service = _DummyService()
        return self._service

    def render(self):
        """Render de hoofdinterface met tabs."""
        st.markdown("## 📦 Import, Export & Beheer")

        # Gebruik tabs voor duidelijke scheiding
        tab1, tab2, tab3, tab4 = st.tabs([
            "📥 Import",
            "📤 Export",
            "⚡ Bulk Acties",
            "🔧 Database Beheer"
        ])

        with tab1:
            self.csv_importer.render()

        with tab2:
            self.format_exporter.render()

        with tab3:
            self.bulk_operations.render()

        with tab4:
            self.database_manager.render()


# Backward compatibility alias
ImportExportBeheerTab = ImportExportOrchestrator