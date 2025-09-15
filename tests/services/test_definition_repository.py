"""
Unit tests voor DefinitionRepository service.

Test alle functionaliteit van de DefinitionRepository inclusief:
- CRUD operaties (Create, Read, Update, Delete)
- Zoekfunctionaliteit
- Statistieken tracking
- Error handling
- Data conversie tussen Definition en DefinitieRecord
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timezone
import sqlite3
import json

from services.definition_repository import DefinitionRepository
from services.interfaces import Definition
from database.definitie_repository import DefinitieRecord, DefinitieStatus, SourceType


@pytest.fixture
def mock_legacy_repo():
    """Mock voor de legacy DefinitieRepository."""
    return Mock()


@pytest.fixture
def repository(mock_legacy_repo):
    """DefinitionRepository instance met gemockte legacy repo."""
    with patch('services.definition_repository.LegacyRepository', return_value=mock_legacy_repo):
        repo = DefinitionRepository(db_path=':memory:')
        return repo


@pytest.fixture
def sample_definition():
    """Sample Definition voor tests."""
    return Definition(
        begrip="Identiteitsbewijs",
        definitie="Een officieel document uitgegeven door de overheid.",
        organisatorische_context=["Overheidsadministratie"],
        juridische_context=["Wet op de identificatieplicht"],
        categorie="type",
        toelichting="Dit wordt gebruikt voor identificatie.",
        bron="AI-gegenereerd",
        metadata={
            "status": "draft",
            "validation_score": 0.95,
        },
    )


@pytest.fixture
def sample_record():
    """Sample DefinitieRecord voor tests."""
    record = DefinitieRecord()
    record.id = 123
    record.begrip = "Identiteitsbewijs"
    record.definitie = "Een officieel document uitgegeven door de overheid."
    record.organisatorische_context = "[\"Overheidsadministratie\"]"
    record.categorie = "type"
    record.status = DefinitieStatus.DRAFT.value
    record.source_type = SourceType.GENERATED.value
    record.created_at = datetime.now(timezone.utc)
    record.updated_at = datetime.now(timezone.utc)
    record.validation_score = 0.95
    record.juridische_context = "[\"Wet op de identificatieplicht\"]"
    return record


class TestDefinitionRepository:
    """Test suite voor DefinitionRepository."""

    def test_initialization(self, mock_legacy_repo):
        """Test repository initialisatie."""
        with patch('services.definition_repository.LegacyRepository', return_value=mock_legacy_repo) as mock_class:
            repo = DefinitionRepository(db_path='test.db')

            mock_class.assert_called_once_with('test.db')
            assert repo.db_path == 'test.db'
            assert repo.legacy_repo == mock_legacy_repo
            assert repo._stats['total_saves'] == 0
            assert repo._stats['total_searches'] == 0
            assert repo._stats['total_updates'] == 0
            assert repo._stats['total_deletes'] == 0

    def test_save_new_definition(self, repository, mock_legacy_repo, sample_definition):
        """Test opslaan van nieuwe definitie zonder ID."""
        # Setup
        mock_legacy_repo.create_definitie.return_value = 123

        # Execute
        result_id = repository.save(sample_definition)

        # Verify
        assert result_id == 123
        assert repository._stats['total_saves'] == 1
        mock_legacy_repo.create_definitie.assert_called_once()

        # Verify the record was created correctly
        call_args = mock_legacy_repo.create_definitie.call_args[0][0]
        assert isinstance(call_args, DefinitieRecord)
        assert call_args.begrip == "Identiteitsbewijs"
        assert "Toelichting: Dit wordt gebruikt voor identificatie." in call_args.definitie

    def test_save_existing_definition(self, repository, mock_legacy_repo, sample_definition):
        """Test update van bestaande definitie met ID."""
        # Setup
        sample_definition.id = 456

        # Execute
        result_id = repository.save(sample_definition)

        # Verify
        assert result_id == 456
        assert repository._stats['total_saves'] == 1
        mock_legacy_repo.update_definitie.assert_called_once()
        # Verify it was called with ID and a DefinitieRecord
        call_args = mock_legacy_repo.update_definitie.call_args[0]
        assert call_args[0] == 456
        assert isinstance(call_args[1], DefinitieRecord)
        mock_legacy_repo.create_definitie.assert_not_called()

    def test_save_error_handling(self, repository, mock_legacy_repo, sample_definition):
        """Test error handling bij save."""
        # Setup
        mock_legacy_repo.create_definitie.side_effect = Exception("Database error")

        # Execute & Verify
        with pytest.raises(Exception, match="Database error"):
            repository.save(sample_definition)

    def test_get_definition_by_id(self, repository, mock_legacy_repo, sample_record):
        """Test ophalen definitie op ID."""
        # Setup
        mock_legacy_repo.get_definitie.return_value = sample_record

        # Execute
        result = repository.get(123)

        # Verify
        assert result is not None
        assert result.id == 123
        assert result.begrip == "Identiteitsbewijs"
        assert result.definitie == "Een officieel document uitgegeven door de overheid."
        assert result.metadata['status'] == DefinitieStatus.DRAFT.value
        assert result.metadata['validation_score'] == 0.95
        mock_legacy_repo.get_definitie.assert_called_once_with(123)

    def test_get_nonexistent_definition(self, repository, mock_legacy_repo):
        """Test ophalen niet-bestaande definitie."""
        # Setup
        mock_legacy_repo.get_definitie.return_value = None

        # Execute
        result = repository.get(999)

        # Verify
        assert result is None
        mock_legacy_repo.get_definitie.assert_called_once_with(999)

    def test_get_error_handling(self, repository, mock_legacy_repo):
        """Test error handling bij get."""
        # Setup
        mock_legacy_repo.get_definitie.side_effect = Exception("Connection lost")

        # Execute
        result = repository.get(123)

        # Verify - should return None on error
        assert result is None

    def test_search(self, repository, mock_legacy_repo, sample_record):
        """Test zoekfunctionaliteit."""
        # Setup
        mock_legacy_repo.search.return_value = [sample_record]

        # Execute
        results = repository.search("identiteit", limit=5)

        # Verify
        assert len(results) == 1
        assert results[0].begrip == "Identiteitsbewijs"
        assert repository._stats['total_searches'] == 1
        mock_legacy_repo.search.assert_called_once_with(
            search_term="identiteit",
            limit=5
        )

    def test_search_with_none_records(self, repository, mock_legacy_repo):
        """Test search wanneer sommige records None worden bij conversie."""
        # Setup - mix van valide en invalide records
        valid_record = DefinitieRecord()
        valid_record.begrip = "Valid"
        valid_record.definitie = "Valid def"

        invalid_record = Mock()  # This will cause issues in conversion

        # Create a proper Definition object for valid conversion
        valid_definition = Definition(begrip="Valid", definitie="Valid def")

        # Mock _record_to_definition to return None for invalid record
        with patch.object(repository, '_record_to_definition') as mock_convert:
            mock_convert.side_effect = lambda r: None if r == invalid_record else valid_definition
            mock_legacy_repo.search.return_value = [valid_record, invalid_record]

            # Execute
            results = repository.search("test")

            # Verify - only valid record should be in results
            assert len(results) == 1
            assert results[0].begrip == "Valid"

    def test_search_empty_results(self, repository, mock_legacy_repo):
        """Test zoeken zonder resultaten."""
        # Setup
        mock_legacy_repo.search.return_value = []

        # Execute
        results = repository.search("nonexistent")

        # Verify
        assert results == []
        assert repository._stats['total_searches'] == 1

    def test_search_error_handling(self, repository, mock_legacy_repo):
        """Test error handling bij search."""
        # Setup
        mock_legacy_repo.search.side_effect = Exception("Query failed")

        # Execute
        results = repository.search("test")

        # Verify - should return empty list on error
        assert results == []
        assert repository._stats['total_searches'] == 1

    def test_update(self, repository, mock_legacy_repo, sample_definition):
        """Test update functionaliteit."""
        # Setup
        sample_definition.id = 123

        # Execute
        result = repository.update(123, sample_definition)

        # Verify
        assert result is True
        assert repository._stats['total_updates'] == 1
        mock_legacy_repo.update_definitie.assert_called_once()

        # Verify the record parameter
        call_args = mock_legacy_repo.update_definitie.call_args[0]
        assert call_args[0] == 123  # ID
        assert isinstance(call_args[1], DefinitieRecord)  # Record

    def test_update_error_handling(self, repository, mock_legacy_repo, sample_definition):
        """Test error handling bij update."""
        # Setup
        mock_legacy_repo.update_definitie.side_effect = Exception("Update failed")

        # Execute
        result = repository.update(123, sample_definition)

        # Verify - should return False on error
        assert result is False
        assert repository._stats['total_updates'] == 1

    def test_delete(self, repository, mock_legacy_repo, sample_record):
        """Test soft delete functionaliteit."""
        # Setup
        mock_legacy_repo.get_definitie.return_value = sample_record

        # Execute
        result = repository.delete(123)

        # Verify
        assert result is True
        assert repository._stats['total_deletes'] == 1

        # Verify soft delete (status change)
        mock_legacy_repo.get_definitie.assert_called_once_with(123)
        mock_legacy_repo.update_definitie.assert_called_once()

        # Check that status was set to ARCHIVED
        update_call = mock_legacy_repo.update_definitie.call_args[0]
        assert update_call[0] == 123
        assert update_call[1].status == DefinitieStatus.ARCHIVED.value

    def test_delete_nonexistent(self, repository, mock_legacy_repo):
        """Test delete van niet-bestaande definitie."""
        # Setup
        mock_legacy_repo.get_definitie.return_value = None

        # Execute
        result = repository.delete(999)

        # Verify
        assert result is False
        assert repository._stats['total_deletes'] == 1
        mock_legacy_repo.update_definitie.assert_not_called()

    def test_delete_error_handling(self, repository, mock_legacy_repo):
        """Test error handling bij delete."""
        # Setup
        mock_legacy_repo.get_definitie.side_effect = Exception("Delete failed")

        # Execute
        result = repository.delete(123)

        # Verify
        assert result is False
        assert repository._stats['total_deletes'] == 1

    def test_find_by_begrip(self, repository):
        """Test find_by_begrip met database connectie."""
        with patch.object(repository, '_get_connection') as mock_get_conn:
            # Setup mock connection and cursor
            mock_cursor = Mock()
            # Use a proper sqlite3.Row mock
            mock_row = Mock(spec=sqlite3.Row)
            mock_row.__getitem__ = Mock(side_effect=lambda x: [1, 'Test', 'Test def', 'draft'][x])
            mock_cursor.fetchone.return_value = mock_row
            mock_cursor.description = [('id',), ('begrip',), ('definitie',), ('status',)]

            mock_conn = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_conn.__enter__ = Mock(return_value=mock_conn)
            mock_conn.__exit__ = Mock(return_value=None)

            mock_get_conn.return_value = mock_conn

            # Execute
            result = repository.find_by_begrip("Test")

            # Verify
            assert result is not None
            assert result.begrip == "Test"
            mock_cursor.execute.assert_called_once()
            assert "SELECT * FROM definities" in mock_cursor.execute.call_args[0][0]

    def test_find_by_begrip_not_found(self, repository):
        """Test find_by_begrip wanneer begrip niet gevonden wordt."""
        with patch.object(repository, '_get_connection') as mock_get_conn:
            # Setup
            mock_cursor = Mock()
            mock_cursor.fetchone.return_value = None

            mock_conn = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_conn.__enter__ = Mock(return_value=mock_conn)
            mock_conn.__exit__ = Mock(return_value=None)

            mock_get_conn.return_value = mock_conn

            # Execute
            result = repository.find_by_begrip("NonExistent")

            # Verify
            assert result is None

    def test_find_by_begrip_error_handling(self, repository):
        """Test error handling in find_by_begrip."""
        with patch.object(repository, '_get_connection') as mock_get_conn:
            # Setup
            mock_get_conn.side_effect = Exception("Database error")

            # Execute
            result = repository.find_by_begrip("Test")

            # Verify
            assert result is None

    def test_find_duplicates(self, repository, mock_legacy_repo, sample_record):
        """Test find_duplicates functionaliteit."""
        # Setup
        mock_match = Mock()
        mock_match.definitie_record = sample_record  # Use sample_record instead
        mock_legacy_repo.find_duplicates.return_value = [mock_match]

        # Create a definition to search for duplicates
        definition = Definition(begrip="Test", definitie="Test def")

        # Execute
        results = repository.find_duplicates(definition)

        # Verify
        assert len(results) == 1
        assert results[0].begrip == "Identiteitsbewijs"
        mock_legacy_repo.find_duplicates.assert_called_once()

    def test_find_duplicates_with_none_conversion(self, repository, mock_legacy_repo):
        """Test find_duplicates wanneer conversie None teruggeeft."""
        # Setup
        mock_match = Mock()
        mock_match.definitie_record = Mock()  # Invalid record

        # Mock _record_to_definition to return None
        with patch.object(repository, '_record_to_definition', return_value=None):
            mock_legacy_repo.find_duplicates.return_value = [mock_match]

            definition = Definition(begrip="Test", definitie="Test def")

            # Execute
            results = repository.find_duplicates(definition)

            # Verify - empty list because conversion failed
            assert results == []

    def test_find_duplicates_error_handling(self, repository, mock_legacy_repo, sample_definition):
        """Test error handling in find_duplicates."""
        # Setup
        mock_legacy_repo.find_duplicates.side_effect = Exception("Duplicate check failed")

        # Execute
        results = repository.find_duplicates(sample_definition)

        # Verify
        assert results == []

    def test_get_by_status(self, repository, mock_legacy_repo, sample_record):
        """Test get_by_status functionaliteit."""
        # Setup
        mock_legacy_repo.get_by_status.return_value = [sample_record]

        # Execute
        results = repository.get_by_status("draft", limit=10)

        # Verify
        assert len(results) == 1
        assert results[0].begrip == "Identiteitsbewijs"
        mock_legacy_repo.get_by_status.assert_called_once_with("draft", 10)

    def test_get_by_status_with_none_conversion(self, repository, mock_legacy_repo):
        """Test get_by_status wanneer conversie None teruggeeft."""
        # Setup
        valid_record = DefinitieRecord()
        valid_record.begrip = "Valid"
        valid_record.definitie = "Valid def"

        invalid_record = Mock()

        # Create a proper Definition object
        valid_definition = Definition(begrip="Valid", definitie="Valid def")

        # Mock _record_to_definition to return None for invalid
        with patch.object(repository, '_record_to_definition') as mock_convert:
            mock_convert.side_effect = lambda r: None if r == invalid_record else valid_definition
            mock_legacy_repo.get_by_status.return_value = [valid_record, invalid_record]

            # Execute
            results = repository.get_by_status("draft")

            # Verify
            assert len(results) == 1
            assert results[0].begrip == "Valid"

    def test_get_by_status_error_handling(self, repository, mock_legacy_repo):
        """Test error handling in get_by_status."""
        # Setup
        mock_legacy_repo.get_by_status.side_effect = Exception("Status query failed")

        # Execute
        results = repository.get_by_status("draft")

        # Verify
        assert results == []

    def test_definition_to_record_with_toelichting(self, repository, sample_definition):
        """Test conversie van Definition naar Record met toelichting."""
        # Execute
        record = repository._definition_to_record(sample_definition)

        # Verify
        assert isinstance(record, DefinitieRecord)
        assert record.begrip == "Identiteitsbewijs"
        assert "Toelichting: Dit wordt gebruikt voor identificatie." in record.definitie
        assert record.categorie == "type"
        assert record.status == "draft"
        assert record.validation_score == 0.95

    def test_definition_to_record_minimal(self, repository):
        """Test conversie met minimale Definition."""
        # Create minimal definition
        definition = Definition(
            begrip="Test",
            definitie="Test definitie"
        )

        # Execute
        record = repository._definition_to_record(definition)

        # Verify defaults
        assert record.begrip == "Test"
        assert record.definitie == "Test definitie"
        assert record.categorie == "proces"  # Default
        assert record.status == DefinitieStatus.DRAFT.value  # Default
        assert record.organisatorische_context == "[]"

    def test_definition_to_record_with_source_reference(self, repository):
        """Test conversie met source_reference in metadata."""
        # Create definition with source_reference
        definition = Definition(
            begrip="Test",
            definitie="Test definitie",
            metadata={
                'source_reference': 'https://example.com/source',
                'created_by': 'test_user'
            }
        )

        # Execute
        record = repository._definition_to_record(definition)

        # Verify
        assert record.source_reference == 'https://example.com/source'
        assert record.created_by == 'test_user'

    def test_record_to_definition_with_toelichting(self, repository):
        """Test conversie van Record naar Definition met toelichting."""
        # Create record with toelichting
        record = DefinitieRecord()
        record.id = 1
        record.begrip = "Test"
        record.definitie = "Test definitie\n\nToelichting: Extra uitleg hier"
        record.status = "draft"
        record.validation_issues = '["issue1", "issue2"]'

        # Execute
        definition = repository._record_to_definition(record)

        # Verify
        assert definition.begrip == "Test"
        assert definition.definitie == "Test definitie"
        assert definition.toelichting == "Extra uitleg hier"
        assert definition.metadata['validation_issues'] == ["issue1", "issue2"]

    def test_record_to_definition_invalid_json(self, repository):
        """Test record conversie met ongeldige JSON."""
        # Create record with invalid JSON
        record = DefinitieRecord()
        record.id = 1
        record.begrip = "Test"
        record.definitie = "Test"
        record.validation_issues = "invalid json"

        # Execute
        definition = repository._record_to_definition(record)

        # Verify - should handle gracefully
        assert 'validation_issues' not in definition.metadata

    def test_get_stats(self, repository):
        """Test statistieken ophalen."""
        with patch.object(repository, '_get_connection') as mock_get_conn:
            # Setup database mocks
            mock_cursor = Mock()
            mock_cursor.fetchone.return_value = (42,)  # Total count
            mock_cursor.fetchall.return_value = [
                ('draft', 10),
                ('established', 30),
                ('archived', 2)
            ]

            mock_conn = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_conn.__enter__ = Mock(return_value=mock_conn)
            mock_conn.__exit__ = Mock(return_value=None)

            mock_get_conn.return_value = mock_conn

            # Do some operations
            repository._stats['total_saves'] = 5
            repository._stats['total_searches'] = 10

            # Execute
            stats = repository.get_stats()

            # Verify
            assert stats['total_saves'] == 5
            assert stats['total_searches'] == 10
            assert stats['total_definitions'] == 42
            assert stats['by_status']['draft'] == 10
            assert stats['by_status']['established'] == 30

    def test_get_stats_error_handling(self, repository):
        """Test stats met database error."""
        with patch.object(repository, '_get_connection') as mock_get_conn:
            # Setup - database error
            mock_get_conn.side_effect = Exception("DB Error")

            # Execute
            stats = repository.get_stats()

            # Verify - should still return basic stats
            assert 'total_saves' in stats
            assert 'total_searches' in stats
            assert 'total_definitions' not in stats  # DB stats missing

    def test_reset_stats(self, repository):
        """Test reset van statistieken."""
        # Setup - set some stats
        repository._stats['total_saves'] = 10
        repository._stats['total_searches'] = 20

        # Execute
        repository.reset_stats()

        # Verify
        assert repository._stats['total_saves'] == 0
        assert repository._stats['total_searches'] == 0
        assert repository._stats['total_updates'] == 0
        assert repository._stats['total_deletes'] == 0

    def test_row_to_record(self, repository):
        """Test _row_to_record conversie."""
        # Create mock row that behaves like sqlite3.Row
        mock_row = Mock(spec=sqlite3.Row)
        row_data = [1, 'Test', 'Test def', '2024-01-01T10:00:00', '2024-01-01T11:00:00']
        mock_row.__getitem__ = Mock(side_effect=lambda x: row_data[x])

        # Mock description
        description = [
            ('id',), ('begrip',), ('definitie',),
            ('created_at',), ('updated_at',)
        ]

        # Execute
        record = repository._row_to_record(mock_row, description)

        # Verify
        assert record.id == 1
        assert record.begrip == 'Test'
        assert isinstance(record.created_at, datetime)

    def test_row_to_record_with_invalid_datetime(self, repository):
        """Test _row_to_record met ongeldige datetime."""
        # Create mock row with invalid datetime
        mock_row = Mock(spec=sqlite3.Row)
        row_data = [1, 'Test', 'Test def', 'invalid-date', None]
        mock_row.__getitem__ = Mock(side_effect=lambda x: row_data[x])

        # Mock description
        description = [
            ('id',), ('begrip',), ('definitie',),
            ('created_at',), ('updated_at',)
        ]

        # Execute
        record = repository._row_to_record(mock_row, description)

        # Verify - invalid date should remain as string
        assert record.created_at == 'invalid-date'
        assert record.updated_at is None

    def test_get_connection_context_manager(self, repository):
        """Test _get_connection context manager."""
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_connect.return_value = mock_conn

            # Use context manager
            with repository._get_connection() as conn:
                assert conn == mock_conn
                assert conn.row_factory == sqlite3.Row

            # Verify connection was closed
            mock_conn.close.assert_called_once()


class TestDefinitionRepositoryIntegration:
    """Integration-style tests voor complexe scenarios."""

    def test_save_and_retrieve_cycle(self, repository, mock_legacy_repo):
        """Test complete save en retrieve cycle."""
        # Setup
        definition = Definition(
            begrip="CycleTest",
            definitie="Test voor complete cycle",
            metadata={'test': True}
        )

        mock_legacy_repo.create_definitie.return_value = 789
        mock_legacy_repo.get_definitie.return_value = DefinitieRecord(
            id=789,
            begrip="CycleTest",
            definitie="Test voor complete cycle",
            status="draft"
        )

        # Execute
        saved_id = repository.save(definition)
        retrieved = repository.get(saved_id)

        # Verify
        assert saved_id == 789
        assert retrieved.begrip == "CycleTest"
        assert repository._stats['total_saves'] == 1

    def test_record_conversion_edge_cases(self, repository):
        """Test edge cases in record conversie."""
        # Test 1: Record met None waarden
        record1 = DefinitieRecord()
        record1.begrip = "Test1"
        record1.definitie = "Test"
        record1.metadata = None

        def1 = repository._record_to_definition(record1)
        assert def1.begrip == "Test1"

        # Test 2: Definition zonder metadata voor _definition_to_record branches
        def2 = Definition(begrip="Test2", definitie="Test2 def")
        rec2 = repository._definition_to_record(def2)
        assert rec2.validation_score is None  # No metadata, so no validation_score

        # Test 3: Toelichting zonder prefix
        record3 = DefinitieRecord()
        record3.begrip = "Test3"
        record3.definitie = "Test definitie zonder toelichting"

        def3 = repository._record_to_definition(record3)
        assert def3.toelichting is None  # No toelichting marker found

    def test_search_and_update_flow(self, repository, mock_legacy_repo):
        """Test search gevolgd door update."""
        # Setup
        record = DefinitieRecord(
            id=100,
            begrip="UpdateTest",
            definitie="Original",
            status="draft"
        )
        mock_legacy_repo.search.return_value = [record]

        # Execute
        results = repository.search("UpdateTest")
        assert len(results) == 1

        # Update the found definition
        updated_def = results[0]
        updated_def.definitie = "Updated"
        success = repository.update(100, updated_def)

        # Verify
        assert success is True
        assert repository._stats['total_searches'] == 1
        assert repository._stats['total_updates'] == 1
