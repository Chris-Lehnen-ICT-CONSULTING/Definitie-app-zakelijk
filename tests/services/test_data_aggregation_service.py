"""
Tests voor DataAggregationService.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock

from database.definitie_repository import DefinitieRecord, DefinitieRepository
from services.data_aggregation_service import DataAggregationService, DefinitieExportData


class TestDataAggregationService:
    """Test cases voor DataAggregationService."""

    @pytest.fixture
    def mock_repository(self):
        """Create mock repository."""
        return Mock(spec=DefinitieRepository)

    @pytest.fixture
    def service(self, mock_repository):
        """Create service instance."""
        return DataAggregationService(mock_repository)

    @pytest.fixture
    def sample_definitie_record(self):
        """Create sample definitie record."""
        record = Mock(spec=DefinitieRecord)
        record.id = 1
        record.begrip = "test begrip"
        record.definitie = "test definitie"
        record.status = "DRAFT"
        record.versie = 1
        record.categorie = "proces"
        record.domein = "juridisch"
        record.context = {
            "organisatorisch": ["OM", "ZM"],
            "juridisch": ["Strafrecht"],
            "wettelijk": ["Wetboek van Strafvordering"]
        }
        record.created_at = datetime.now()
        record.updated_at = datetime.now()
        record.created_by = "test_user"
        record.organisatorische_context = "OM, ZM"
        record.juridische_context = "Strafrecht"
        return record

    def test_aggregate_definitie_for_export_with_record(self, service, sample_definitie_record):
        """Test export aggregatie met definitie record."""
        # Act
        result = service.aggregate_definitie_for_export(
            definitie_record=sample_definitie_record
        )

        # Assert
        assert isinstance(result, DefinitieExportData)
        assert result.begrip == "test begrip"
        assert result.definitie_origineel == "test definitie"
        assert result.definitie_gecorrigeerd == "test definitie"
        assert result.metadata["id"] == 1
        assert result.metadata["status"] == "DRAFT"
        assert result.metadata["categorie"] == "proces"
        assert result.context_dict == sample_definitie_record.context
        assert result.created_at == sample_definitie_record.created_at

    def test_aggregate_definitie_for_export_with_id(self, service, mock_repository, sample_definitie_record):
        """Test export aggregatie met definitie ID."""
        # Arrange
        mock_repository.get_definitie.return_value = sample_definitie_record

        # Act
        result = service.aggregate_definitie_for_export(definitie_id=1)

        # Assert
        mock_repository.get_definitie.assert_called_once_with(1)
        assert result.begrip == "test begrip"
        assert result.metadata["id"] == 1

    def test_aggregate_definitie_for_export_invalid_id(self, service, mock_repository):
        """Test export aggregatie met ongeldig ID."""
        # Arrange
        mock_repository.get_definitie.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Definitie met ID 999 niet gevonden"):
            service.aggregate_definitie_for_export(definitie_id=999)

    def test_aggregate_with_additional_data(self, service, sample_definitie_record):
        """Test aggregatie met additionele data."""
        # Arrange
        additional_data = {
            "definitie_aangepast": "aangepaste definitie",
            "toelichting": "test toelichting",
            "synoniemen": "syn1, syn2",
            "voorkeursterm": "voorkeursterm",
            "expert_review": "Expert goedgekeurd",
            "voorbeeld_zinnen": ["voorbeeld 1", "voorbeeld 2"],
            "praktijkvoorbeelden": ["praktijk 1"],
            "tegenvoorbeelden": ["tegen 1"],
            "beoordeling": ["✔️ Test regel"],
            "toetsresultaten": {"score": 0.85},
            "ketenpartners": ["ZM", "OM"],
            "marker": "proces",
            "prompt_text": "test prompt"
        }

        # Act
        result = service.aggregate_definitie_for_export(
            definitie_record=sample_definitie_record,
            additional_data=additional_data
        )

        # Assert
        assert result.definitie_aangepast == "aangepaste definitie"
        assert result.toelichting == "test toelichting"
        assert result.synoniemen == "syn1, syn2"
        assert result.voorkeursterm == "voorkeursterm"
        assert result.expert_review == "Expert goedgekeurd"
        assert result.voorbeeld_zinnen == ["voorbeeld 1", "voorbeeld 2"]
        assert result.praktijkvoorbeelden == ["praktijk 1"]
        assert result.tegenvoorbeelden == ["tegen 1"]
        assert result.beoordeling == ["✔️ Test regel"]
        assert result.toetsresultaten == {"score": 0.85}
        assert result.metadata["ketenpartners"] == ["ZM", "OM"]
        assert result.marker == "proces"
        assert result.prompt_text == "test prompt"

    def test_prepare_export_dict(self, service):
        """Test conversie naar export dictionary."""
        # Arrange
        export_data = DefinitieExportData(
            begrip="test begrip",
            definitie_origineel="origineel",
            definitie_gecorrigeerd="gecorrigeerd",
            definitie_aangepast="aangepast",
            metadata={"test": "metadata"},
            context_dict={"organisatorisch": ["OM"]},
            toetsresultaten={"score": 0.9},
            toelichting="toelichting",
            synoniemen="syn1",
            voorkeursterm="pref",
            expert_review="review"
        )

        # Act
        result = service.prepare_export_dict(export_data)

        # Assert
        assert isinstance(result, dict)
        assert result["begrip"] == "test begrip"
        assert result["definitie_origineel"] == "origineel"
        assert result["definitie_gecorrigeerd"] == "gecorrigeerd"
        assert result["definitie_aangepast"] == "aangepast"
        assert result["metadata"] == {"test": "metadata"}
        assert result["context_dict"] == {"organisatorisch": ["OM"]}
        assert result["toetsresultaten"] == {"score": 0.9}
        assert result["toelichting"] == "toelichting"
        assert result["synoniemen"] == "syn1"
        assert result["voorkeursterm"] == "pref"
        assert result["expert_review"] == "review"

    def test_aggregate_from_generation_result(self, service):
        """Test aggregatie vanuit generatie resultaat."""
        # Arrange
        generation_result = {
            "begrip": "test begrip",
            "definitie": "gegenereerde definitie",
            "definitie_gecorrigeerd": "opgeschoonde definitie",
            "voorbeeld_zinnen": ["voorbeeld 1"],
            "praktijkvoorbeelden": ["praktijk 1"],
            "tegenvoorbeelden": ["tegen 1"],
            "toelichting": "uitleg",
            "synoniemen": "syn1, syn2",
            "antoniemen": "ant1",
            "bronnen": ["bron1", "bron2"],
            "toetsresultaten": {"violations": []},
            "marker": "proces"
        }

        context_dict = {
            "organisatorisch": ["OM"],
            "juridisch": ["Strafrecht"]
        }

        metadata = {
            "generated_by": "AI",
            "model": "GPT-4"
        }

        # Act
        result = service.aggregate_from_generation_result(
            generation_result, context_dict, metadata
        )

        # Assert
        assert result.begrip == "test begrip"
        assert result.definitie_origineel == "gegenereerde definitie"
        assert result.definitie_gecorrigeerd == "opgeschoonde definitie"
        assert result.voorbeeld_zinnen == ["voorbeeld 1"]
        assert result.praktijkvoorbeelden == ["praktijk 1"]
        assert result.tegenvoorbeelden == ["tegen 1"]
        assert result.toelichting == "uitleg"
        assert result.synoniemen == "syn1, syn2"
        assert result.antoniemen == "ant1"
        assert result.bronnen == ["bron1", "bron2"]
        assert result.toetsresultaten == {"violations": []}
        assert result.marker == "proces"
        assert result.context_dict == context_dict
        assert result.metadata == metadata
        assert result.created_at is not None
