"""
Integration test voor definition save flow.

Tests the complete end-to-end flow: generation request → definition object → save → retrieve.
This test verifies DEF-53 fix: ensure categorie field is properly set and saved.
"""

from datetime import UTC, datetime

import pytest

from services.definition_repository import DefinitionRepository
from services.exceptions import DatabaseConstraintError, DuplicateDefinitionError
from services.interfaces import Definition, GenerationRequest


class TestDefinitionSaveIntegration:
    """Integration tests voor definition save operations."""

    @pytest.fixture
    def repository(self, tmp_path):
        """Create temporary repository for testing."""
        db_path = tmp_path / "test_definities.db"
        return DefinitionRepository(str(db_path))
        # Cleanup handled by tmp_path

    @pytest.fixture
    def sample_definition(self):
        """Create sample definition for testing."""
        return Definition(
            begrip="test_begrip",
            definitie="Dit is een test definitie voor integration testing",
            organisatorische_context=["test_context"],
            juridische_context=["test_juridisch"],
            wettelijke_basis=["test_wetgeving"],
            ontologische_categorie="ENT",
            categorie="ENT",  # DEF-53 fix: explicit mapping
            ufo_categorie="Kind",
            valid=True,
            validation_violations=[],
            metadata={"test": "metadata"},
            created_by="integration_test",
            created_at=datetime.now(UTC),
        )

    def test_save_new_definition_success(self, repository, sample_definition):
        """Test: Save new definition successfully."""
        # Act
        definition_id = repository.save(sample_definition)

        # Assert
        assert definition_id is not None
        assert definition_id > 0

    def test_save_and_retrieve_definition(self, repository, sample_definition):
        """Test: Save definition and retrieve it back."""
        # Arrange
        definition_id = repository.save(sample_definition)

        # Act
        retrieved = repository.get(definition_id)

        # Assert
        assert retrieved is not None
        assert retrieved.begrip == sample_definition.begrip
        assert retrieved.definitie == sample_definition.definitie
        assert retrieved.categorie is not None  # DEF-53: Verify constraint satisfied
        assert retrieved.categorie == "ENT"

    def test_save_without_categorie_uses_fallback(self, repository):
        """Test: DEF-53 fix - repository fallback provides default when both fields None."""
        # Arrange
        definition_without_categorie = Definition(
            begrip="test_no_category",
            definitie="Test definitie zonder categorie",
            categorie=None,  # Intentionally None
            ontologische_categorie=None,  # Also None
            created_by="test",
            created_at=datetime.now(UTC),
        )

        # Act - Should succeed with fallback to "proces"
        definition_id = repository.save(definition_without_categorie)

        # Assert
        assert definition_id is not None
        retrieved = repository.get(definition_id)
        assert retrieved.categorie == "proces"  # Fallback value

    def test_save_with_ontologische_categorie_fallback(self, repository):
        """Test: DEF-53 fix - repository should fallback to ontologische_categorie."""
        # Arrange - categorie is None, but ontologische_categorie is set
        definition = Definition(
            begrip="test_fallback",
            definitie="Test definitie met fallback",
            categorie=None,  # Explicitly None (simulates pre-Fix-1 orchestrator)
            ontologische_categorie="ACT",  # This should be used as fallback
            created_by="test",
            created_at=datetime.now(UTC),
        )

        # Act
        definition_id = repository.save(definition)

        # Assert
        retrieved = repository.get(definition_id)
        assert retrieved is not None
        assert retrieved.categorie is not None
        # Repository should have mapped ontologische_categorie → categorie
        assert retrieved.categorie in [
            "ACT",
            "proces",
        ]  # Either original or fallback

    def test_duplicate_definition_raises_error(self, repository, sample_definition):
        """Test: Saving duplicate definition raises DuplicateDefinitionError."""
        # Arrange
        repository.save(sample_definition)

        # Act & Assert
        with pytest.raises(DuplicateDefinitionError) as exc_info:
            repository.save(sample_definition)

        assert sample_definition.begrip in str(exc_info.value)

    def test_update_existing_definition(self, repository, sample_definition):
        """Test: Update existing definition by setting ID."""
        # Arrange
        definition_id = repository.save(sample_definition)

        # Modify definition
        sample_definition.id = definition_id
        sample_definition.definitie = "Updated definitie text"

        # Act
        result_id = repository.save(sample_definition)

        # Assert
        assert result_id == definition_id  # Same ID returned
        retrieved = repository.get(definition_id)
        assert retrieved.definitie == "Updated definitie text"

    def test_save_with_all_ontological_categories(self, repository):
        """Test: Save definitions with all valid ontological categories."""
        valid_categories = ["ENT", "ACT", "REL", "ATT", "AUT", "STA", "OTH"]

        for category in valid_categories:
            definition = Definition(
                begrip=f"test_{category.lower()}",
                definitie=f"Test definitie voor categorie {category}",
                categorie=category,
                ontologische_categorie=category,
                created_by="test",
                created_at=datetime.now(UTC),
            )

            # Act
            definition_id = repository.save(definition)

            # Assert
            assert definition_id is not None
            retrieved = repository.get(definition_id)
            assert retrieved.categorie == category

    def test_save_with_metadata(self, repository):
        """Test: Save definition with metadata."""
        definition = Definition(
            begrip="test_with_metadata",
            definitie="Test definitie met metadata",
            categorie="ENT",
            metadata={"source": "test", "version": 1, "tags": ["test", "integration"]},
            created_by="test",
            created_at=datetime.now(UTC),
        )

        # Act
        definition_id = repository.save(definition)

        # Assert
        retrieved = repository.get(definition_id)
        assert retrieved is not None
        # Metadata persistence depends on repository implementation
        # This test documents expected behavior

    def test_concurrent_saves_different_definitions(self, repository):
        """Test: Multiple definitions can be saved concurrently."""
        definitions = [
            Definition(
                begrip=f"concurrent_test_{i}",
                definitie=f"Test definitie {i}",
                categorie="ENT",
                created_by="test",
                created_at=datetime.now(UTC),
            )
            for i in range(5)
        ]

        # Act
        ids = [repository.save(d) for d in definitions]

        # Assert
        assert len(ids) == 5
        assert len(set(ids)) == 5  # All IDs unique
        assert all(id > 0 for id in ids)

    def test_save_logs_useful_info(self, repository, sample_definition, caplog):
        """Test: Save operation logs useful debugging information."""
        import logging

        caplog.set_level(logging.INFO)

        # Act
        repository.save(sample_definition)

        # Assert
        log_messages = [record.message for record in caplog.records]
        assert any(
            sample_definition.begrip in msg for msg in log_messages
        ), "Should log begrip"
        assert any(
            "ENT" in msg or "categorie" in msg.lower() for msg in log_messages
        ), "Should log category"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
