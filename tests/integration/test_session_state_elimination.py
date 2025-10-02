"""
Integratietest voor eliminatie van session state dependencies.

Deze tests verifiëren dat de nieuwe services werken zonder directe
afhankelijkheden van UI session state.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from database.definitie_repository import DefinitieRecord, DefinitieRepository
from services.data_aggregation_service import DataAggregationService
from services.export_service import ExportFormat, ExportService
from services.service_factory import ServiceAdapter, get_definition_service
from ui.services.definition_ui_service import DefinitionUIService


class TestSessionStateElimination:
    """Test eliminatie van session state dependencies."""

    @pytest.fixture()
    def mock_repository(self):
        """Create mock repository met sample data."""
        repo = Mock(spec=DefinitieRepository)

        # Sample definitie record
        sample_record = Mock(spec=DefinitieRecord)
        sample_record.id = 1
        sample_record.begrip = "authenticatie"
        sample_record.definitie = "Het proces van identiteitsverificatie"
        sample_record.status = "DRAFT"
        sample_record.versie = 1
        sample_record.categorie = "proces"
        sample_record.domein = "juridisch"
        sample_record.context = {
            "organisatorisch": ["OM", "ZM"],
            "juridisch": ["Strafrecht"],
        }
        sample_record.created_at = datetime.now()
        sample_record.updated_at = datetime.now()
        sample_record.created_by = "test_user"
        sample_record.organisatorische_context = "OM, ZM"
        sample_record.juridische_context = "Strafrecht"

        repo.get_definitie.return_value = sample_record
        return repo

    def test_data_aggregation_without_session_state(self, mock_repository):
        """Test dat DataAggregationService geen session state nodig heeft."""
        # Arrange
        service = DataAggregationService(mock_repository)

        # Additional data simulating UI input without session state
        ui_data = {
            "expert_review": "Definitie is goedgekeurd",
            "voorkeursterm": "authenticatie",
            "voorbeeld_zinnen": ["De gebruiker voert authenticatie uit"],
            "synoniemen": "identiteitsverificatie, inloggen",
        }

        # Act
        result = service.aggregate_definitie_for_export(
            definitie_id=1, additional_data=ui_data
        )

        # Assert
        assert result.begrip == "authenticatie"
        assert result.definitie_origineel == "Het proces van identiteitsverificatie"
        assert result.expert_review == "Definitie is goedgekeurd"
        assert result.voorkeursterm == "authenticatie"
        assert result.voorbeeld_zinnen == ["De gebruiker voert authenticatie uit"]
        assert result.synoniemen == "identiteitsverificatie, inloggen"
        assert result.metadata["id"] == 1
        assert result.context_dict["organisatorisch"] == ["OM", "ZM"]

    def test_export_service_without_session_state(self, mock_repository, tmp_path):
        """Test dat ExportService werkt zonder session state."""
        # Arrange
        data_agg_service = DataAggregationService(mock_repository)
        export_service = ExportService(
            repository=mock_repository,
            data_aggregation_service=data_agg_service,
            export_dir=str(tmp_path),
        )

        ui_data = {
            "expert_review": "Goedgekeurd door expert",
            "ketenpartners": ["ZM", "OM"],
        }

        with patch("export.export_txt.exporteer_naar_txt") as mock_export:
            mock_export.return_value = str(tmp_path / "test_export.txt")

            # Act
            result = export_service.export_definitie(
                definitie_id=1, additional_data=ui_data, format=ExportFormat.TXT
            )

            # Assert
            assert result.endswith("test_export.txt")
            mock_export.assert_called_once()

            # Verify data passed to export contains UI data
            call_args = mock_export.call_args[0][0]
            assert call_args["expert_review"] == "Goedgekeurd door expert"

    def test_definition_ui_service_facade(self, mock_repository):
        """Test DefinitionUIService facade functionaliteit."""
        # Arrange
        ui_service = DefinitionUIService(repository=mock_repository)

        # Test get export formats
        formats = ui_service.get_export_formats()
        assert len(formats) >= 3  # TXT, JSON, CSV minimaal
        assert any(f["value"] == "txt" for f in formats)
        assert any(f["value"] == "json" for f in formats)

        # Test definition summary
        summary = ui_service.get_definition_summary(1)
        assert summary is not None
        assert summary["begrip"] == "authenticatie"
        assert summary["status"] == "DRAFT"
        assert "can_edit" in summary
        assert "can_review" in summary

    def test_service_adapter_integration(self):
        """Test dat ServiceAdapter correct werkt met nieuwe services."""
        # Arrange
        with patch("services.service_factory.get_container") as mock_get_container:
            # Mock container with all services
            mock_container = Mock()
            mock_container.definition_ui_service.return_value = Mock()
            mock_container.orchestrator.return_value = Mock()
            mock_container.web_lookup.return_value = Mock()
            mock_get_container.return_value = mock_container

            # Act
            service = get_definition_service()

            # Assert
            assert isinstance(service, ServiceAdapter)
            assert hasattr(service, "ui_service")
            assert hasattr(service, "export_definition")

    def test_export_via_service_adapter(self, mock_repository):
        """Test export via ServiceAdapter zonder session state."""
        # Arrange
        with patch("services.service_factory.get_container") as mock_get_container:
            # Setup mock container
            mock_container = Mock()

            # Mock UI service
            mock_ui_service = Mock(spec=DefinitionUIService)
            mock_ui_service.export_definition.return_value = {
                "success": True,
                "path": "/test/export.txt",
                "filename": "export.txt",
                "message": "Export succesvol",
            }
            mock_container.definition_ui_service.return_value = mock_ui_service
            mock_container.orchestrator.return_value = Mock()
            mock_container.web_lookup.return_value = Mock()
            mock_get_container.return_value = mock_container

            service = get_definition_service()

            # UI data without session state
            ui_data = {
                "begrip": "authenticatie",
                "expert_review": "Goedgekeurd",
                "voorkeursterm": "authenticatie",
            }

            # Act
            result = service.export_definition(
                definition_id=1, ui_data=ui_data, format="json"
            )

            # Assert
            assert result["success"] is True
            assert result["filename"] == "export.txt"
            mock_ui_service.export_definition.assert_called_once_with(
                definitie_id=1, ui_data=ui_data, format="json"
            )

    def test_no_session_state_manager_imports(self):
        """Test dat nieuwe services geen SessionStateManager importeren."""
        # Deze test verifieert dat we de dependency echt hebben geëlimineerd

        import inspect

        from services import data_aggregation_service, export_service
        from ui.services import definition_ui_service

        # Check source code voor SessionStateManager imports
        das_source = inspect.getsource(data_aggregation_service)
        assert (
            "SessionStateManager" not in das_source
        ), "DataAggregationService mag geen SessionStateManager importeren"

        es_source = inspect.getsource(export_service)
        assert (
            "SessionStateManager" not in es_source
        ), "ExportService mag geen SessionStateManager importeren"

        # DefinitionUIService mag SessionStateManager NIET importeren
        # (het is een facade tussen UI en services, maar gebruikt geen session state intern)
        duis_source = inspect.getsource(definition_ui_service)
        assert (
            "SessionStateManager" not in duis_source
        ), "DefinitionUIService mag geen SessionStateManager importeren"

    def test_clean_architecture_boundaries(self, mock_repository):
        """Test dat architecture boundaries gerespecteerd worden."""
        # Services layer test
        data_service = DataAggregationService(mock_repository)
        export_service = ExportService(mock_repository)

        # Services mogen geen UI imports hebben
        assert not hasattr(data_service, "session_state")
        assert not hasattr(export_service, "session_state")

        # Services moeten werken met pure data
        result = data_service.aggregate_definitie_for_export(
            definitie_id=1,
            additional_data={"test": "data"},  # Pure dict, geen UI objecten
        )

        assert result is not None
        assert hasattr(result, "begrip")
        assert hasattr(result, "created_at")

    def test_backward_compatibility_maintained(self):
        """Test dat backward compatibility behouden blijft."""
        # Test dat bestaande interface nog werkt
        service = get_definition_service()

        # Deze methods moeten nog bestaan voor legacy UI
        assert hasattr(service, "generate_definition")
        assert hasattr(service, "get_stats")

        # Nieuwe methods zijn toegevoegd
        assert hasattr(service, "export_definition")
