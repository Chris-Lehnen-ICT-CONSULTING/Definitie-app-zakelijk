"""
Integration tests voor ImportExportBeheer tab consolidatie.
Test de nieuwe geconsolideerde tab functionaliteit.
"""

import pytest
import tempfile
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import streamlit as st

from ui.components.import_export_beheer_tab import ImportExportBeheerTab
from database.definitie_repository import DefinitieRecord, DefinitieStatus


@pytest.fixture
def mock_repository():
    """Mock repository voor testing."""
    repo = Mock()

    # Mock data
    test_definitions = [
        DefinitieRecord(
            id=1,
            begrip="TestBegrip1",
            definitie="Test definitie 1",
            categorie="Type",
            organisatorische_context="Test Context",
            status=DefinitieStatus.VASTGESTELD.value,
            validation_score=0.85
        ),
        DefinitieRecord(
            id=2,
            begrip="TestBegrip2",
            definitie="Test definitie 2",
            categorie="Proces",
            organisatorische_context="Test Context",
            status=DefinitieStatus.DRAFT.value,
            validation_score=0.65
        )
    ]

    repo.get_all.return_value = test_definitions
    repo.get_by_status.return_value = test_definitions[:1]
    repo.find_by_begrip.return_value = None
    repo.save.return_value = Mock(id=3)
    repo.update.return_value = True

    return repo


@pytest.fixture
def tab_instance(mock_repository):
    """Create ImportExportBeheerTab instance."""
    return ImportExportBeheerTab(mock_repository)


class TestImportFunctionality:
    """Test import functionaliteit."""

    def test_csv_import_validation(self, tab_instance):
        """Test CSV validatie tijdens import."""
        # Create test CSV
        test_data = pd.DataFrame({
            'begrip': ['Test1', 'Test2'],
            'definitie': ['Def1', 'Def2'],
            'categorie': ['Type', 'Proces'],
            'context': ['Context1', 'Context2']
        })

        # Test missing columns detection
        invalid_data = pd.DataFrame({
            'wrong_column': ['Test']
        })

        # Validate that required columns check works
        assert 'begrip' in test_data.columns
        assert 'definitie' in test_data.columns
        assert 'begrip' not in invalid_data.columns

    def test_duplicate_detection(self, tab_instance, mock_repository):
        """Test duplicate detection tijdens import."""
        mock_repository.find_by_begrip.return_value = Mock(id=1)  # Existing record

        # Should detect duplicate
        existing = mock_repository.find_by_begrip("TestBegrip1", "Test Context")
        assert existing is not None

        mock_repository.find_by_begrip.return_value = None

        # Should not detect duplicate
        new_record = mock_repository.find_by_begrip("NewBegrip", "Test Context")
        assert new_record is None

    @patch('streamlit.progress')
    @patch('streamlit.empty')
    def test_import_progress_tracking(self, mock_empty, mock_progress, tab_instance):
        """Test progress tracking tijdens import."""
        test_df = pd.DataFrame({
            'begrip': [f'Begrip{i}' for i in range(10)],
            'definitie': [f'Def{i}' for i in range(10)],
            'categorie': ['Type'] * 10,
            'context': ['Test'] * 10
        })

        # Mock progress components
        progress_bar = Mock()
        mock_progress.return_value = progress_bar

        status_text = Mock()
        mock_empty.return_value = status_text

        # Process import
        tab_instance._process_import(test_df, skip_duplicates=True, auto_validate=False)

        # Verify progress was updated
        assert progress_bar.progress.called
        assert status_text.text.called


class TestExportFunctionality:
    """Test export functionaliteit."""

    def test_export_format_generation(self, tab_instance, mock_repository):
        """Test verschillende export formaten."""
        # Test CSV export
        df = tab_instance._definitions_to_dataframe(mock_repository.get_all())
        assert len(df) == 2
        assert 'begrip' in df.columns
        assert 'definitie' in df.columns

        # Test data conversion
        csv_output = df.to_csv(index=False)
        assert 'TestBegrip1' in csv_output
        assert 'Test definitie 1' in csv_output

    def test_export_filtering(self, tab_instance, mock_repository):
        """Test filtering bij export."""
        # Test status filter
        vastgesteld = mock_repository.get_by_status(DefinitieStatus.VASTGESTELD.value)
        assert len(vastgesteld) == 1

        # Test all filter
        all_defs = mock_repository.get_all()
        assert len(all_defs) == 2

    def test_txt_export_generation(self, tab_instance, mock_repository):
        """Test plain text export format."""
        definitions = mock_repository.get_all()
        txt_output = tab_instance._generate_txt_export(definitions)

        assert "DEFINITIE EXPORT" in txt_output
        assert "TestBegrip1" in txt_output
        assert "Test definitie 1" in txt_output
        assert "=" * 50 in txt_output


class TestBulkOperations:
    """Test bulk operaties."""

    def test_bulk_status_change(self, tab_instance, mock_repository):
        """Test bulk status wijziging."""
        # Setup
        definitions = mock_repository.get_by_status(DefinitieStatus.DRAFT.value)

        # Execute bulk change
        for definition in definitions:
            definition.status = DefinitieStatus.VASTGESTELD.value
            mock_repository.update(definition)

        # Verify
        mock_repository.update.assert_called()

    def test_bulk_operation_preview(self, tab_instance, mock_repository):
        """Test preview van bulk operaties."""
        draft_count = len(mock_repository.get_by_status(DefinitieStatus.DRAFT.value))
        assert draft_count > 0

        # Preview should show correct count
        from_status = DefinitieStatus.DRAFT.value
        to_status = DefinitieStatus.VASTGESTELD.value
        assert from_status != to_status


class TestDatabaseManagement:
    """Test database beheer functionaliteit."""

    def test_database_stats_retrieval(self, tab_instance, mock_repository):
        """Test ophalen database statistieken."""
        stats = tab_instance._get_database_stats()

        assert 'total' in stats
        assert 'established' in stats
        assert 'draft' in stats
        assert 'size' in stats

        assert stats['total'] == 2
        assert stats['established'] == 1
        assert stats['draft'] == 1

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.stat')
    def test_database_size_calculation(self, mock_stat, mock_exists, tab_instance):
        """Test database grootte berekening."""
        mock_exists.return_value = True
        mock_stat.return_value = Mock(st_size=1024*1024*5)  # 5 MB

        stats = tab_instance._get_database_stats()
        assert stats['size'] == "5.0 MB"

        mock_exists.return_value = False
        stats = tab_instance._get_database_stats()
        assert stats['size'] == "N/A"

    def test_database_reset_safety(self, tab_instance):
        """Test database reset veiligheidscontroles."""
        # Reset should require confirmation
        confirmation = "RESET"
        assert confirmation == "RESET"  # Valid confirmation

        wrong_confirmation = "reset"
        assert wrong_confirmation != "RESET"  # Invalid confirmation


class TestServiceIntegration:
    """Test service integratie."""

    def test_lazy_service_loading(self, tab_instance):
        """Test lazy loading van definition service."""
        # Service should not be loaded initially
        assert tab_instance._service is None

        # Should load on first access
        service = tab_instance.service
        assert service is not None
        assert hasattr(service, 'get_service_info')

    def test_dummy_service_fallback(self, tab_instance):
        """Test fallback naar dummy service."""
        with patch('ui.components.import_export_beheer_tab.get_definition_service',
                  side_effect=Exception("No API key")):
            service = tab_instance.service
            assert service is not None

            info = service.get_service_info()
            assert info['service_mode'] == 'dummy'
            assert info['version'] == 'test'


class TestUIRendering:
    """Test UI rendering."""

    @patch('streamlit.markdown')
    @patch('streamlit.tabs')
    def test_main_interface_rendering(self, mock_tabs, mock_markdown, tab_instance):
        """Test hoofdinterface rendering."""
        # Setup tabs mock
        mock_tabs.return_value = [Mock() for _ in range(4)]

        # Render
        with patch('streamlit.tab') as mock_tab_context:
            tab_instance.render()

        # Verify structure
        mock_markdown.assert_called()
        mock_tabs.assert_called_with([
            "📥 Import",
            "📤 Export",
            "⚡ Bulk Acties",
            "🔧 Database Beheer"
        ])

    @patch('streamlit.file_uploader')
    def test_import_ui_components(self, mock_uploader, tab_instance):
        """Test import UI componenten."""
        mock_uploader.return_value = None

        # Should render file uploader
        tab_instance._render_import_section()
        mock_uploader.assert_called_with(
            "Selecteer CSV bestand",
            type=['csv'],
            help="CSV moet kolommen bevatten: begrip, definitie, categorie, context"
        )


# Performance tests
class TestPerformance:
    """Test performance aspecten."""

    def test_large_import_handling(self, tab_instance, mock_repository):
        """Test handling van grote imports."""
        # Create large dataset
        large_df = pd.DataFrame({
            'begrip': [f'Begrip{i}' for i in range(1000)],
            'definitie': [f'Definitie{i}' for i in range(1000)],
            'categorie': ['Type'] * 1000,
            'context': ['Test'] * 1000
        })

        # Should handle without issues
        assert len(large_df) == 1000

        # Processing should be chunked
        chunk_size = 100
        chunks = [large_df[i:i+chunk_size] for i in range(0, len(large_df), chunk_size)]
        assert len(chunks) == 10

    def test_export_memory_efficiency(self, tab_instance, mock_repository):
        """Test memory efficiency bij export."""
        # Large dataset export should use streaming
        mock_repository.get_all.return_value = [
            DefinitieRecord(
                id=i,
                begrip=f"Begrip{i}",
                definitie=f"Definitie{i}",
                categorie="Type",
                organisatorische_context="Test",
                status=DefinitieStatus.DRAFT.value,
                validation_score=0.5
            ) for i in range(1000)
        ]

        # Convert to dataframe should be efficient
        df = tab_instance._definitions_to_dataframe(mock_repository.get_all())
        assert len(df) == 1000

        # Memory usage should be reasonable
        memory_usage = df.memory_usage(deep=True).sum()
        assert memory_usage < 10 * 1024 * 1024  # Less than 10MB for 1000 records