"""
Unit tests voor voorbeelden functionaliteit in DefinitieRepository.

Test de connection bug fixes voor:
- save_voorbeelden
- get_voorbeelden
- beoordeel_voorbeeld
- delete_voorbeelden
"""

import os
import tempfile

import pytest

from src.database.definitie_repository import (DefinitieRecord,
                                               DefinitieRepository,
                                               VoorbeeldenRecord)


@pytest.fixture()
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture()
def repository(temp_db):
    """Create repository instance with temp database."""
    return DefinitieRepository(temp_db)


@pytest.fixture()
def test_definitie(repository):
    """Create test definitie for voorbeelden tests."""
    record = DefinitieRecord(
        begrip="test_begrip",
        definitie="Test definitie voor voorbeelden tests",
        categorie="proces",
        organisatorische_context="TEST_ORG",
    )
    return repository.create_definitie(record)


class TestVoorbeeldenFunctionality:
    """Test suite voor voorbeelden management na connection fixes."""

    def test_save_voorbeelden_basic(self, repository, test_definitie):
        """Test basis save_voorbeelden functionaliteit."""
        voorbeelden = {
            "sentence": ["Voorbeeld zin 1", "Voorbeeld zin 2"],
            "practical": ["Praktisch voorbeeld"],
        }

        saved_ids = repository.save_voorbeelden(test_definitie, voorbeelden)

        assert len(saved_ids) == 3
        assert all(isinstance(id, int) for id in saved_ids)

    def test_save_voorbeelden_with_empty_entries(self, repository, test_definitie):
        """Test save_voorbeelden met lege entries."""
        voorbeelden = {
            "sentence": ["Valid example", ""],  # Empty string
            "practical": [],  # Empty list
            "counter": ["   "],  # Whitespace only
        }

        saved_ids = repository.save_voorbeelden(test_definitie, voorbeelden)

        # Should only save the valid example
        assert len(saved_ids) == 1

    def test_save_voorbeelden_with_generation_params(self, repository, test_definitie):
        """Test save_voorbeelden met generation parameters."""
        voorbeelden = {"sentence": ["Generated example"]}
        gen_params = {"temperature": 0.7, "model": "gpt-4"}

        repository.save_voorbeelden(
            test_definitie,
            voorbeelden,
            generation_model="gpt-4",
            generation_params=gen_params,
            gegenereerd_door="ai_system",
        )

        # Verify saved with params
        retrieved = repository.get_voorbeelden(test_definitie)[0]
        assert retrieved.generation_model == "gpt-4"
        assert retrieved.gegenereerd_door == "ai_system"
        assert retrieved.get_generation_parameters_dict() == gen_params

    def test_get_voorbeelden_all(self, repository, test_definitie):
        """Test get all voorbeelden."""
        # Save test data
        voorbeelden = {
            "sentence": ["Example 1", "Example 2"],
            "practical": ["Practical example"],
        }
        repository.save_voorbeelden(test_definitie, voorbeelden)

        # Get all
        retrieved = repository.get_voorbeelden(test_definitie)

        assert len(retrieved) == 3
        assert all(isinstance(v, VoorbeeldenRecord) for v in retrieved)
        assert all(v.definitie_id == test_definitie for v in retrieved)

    def test_get_voorbeelden_by_type(self, repository, test_definitie):
        """Test get voorbeelden filtered by type."""
        # Save test data
        voorbeelden = {
            "sentence": ["Sentence 1", "Sentence 2"],
            "practical": ["Practical 1"],
        }
        repository.save_voorbeelden(test_definitie, voorbeelden)

        # Get only sentence type
        sentences = repository.get_voorbeelden(
            test_definitie, voorbeeld_type="sentence"
        )

        assert len(sentences) == 2
        assert all(v.voorbeeld_type == "sentence" for v in sentences)

    def test_get_voorbeelden_inactive(self, repository, test_definitie):
        """Test get voorbeelden including inactive."""
        # Save and then deactivate
        voorbeelden = {"sentence": ["Active example"]}
        repository.save_voorbeelden(test_definitie, voorbeelden)

        # Save again (this deactivates previous)
        repository.save_voorbeelden(test_definitie, {"sentence": ["New example"]})

        # Get all including inactive
        all_voorbeelden = repository.get_voorbeelden(test_definitie, actief_only=False)
        active_only = repository.get_voorbeelden(test_definitie, actief_only=True)

        assert len(all_voorbeelden) > len(active_only)

    def test_get_voorbeelden_by_type_dict(self, repository, test_definitie):
        """Test get_voorbeelden_by_type returns dict format."""
        voorbeelden = {"sentence": ["S1", "S2"], "practical": ["P1"], "counter": ["C1"]}
        repository.save_voorbeelden(test_definitie, voorbeelden)

        by_type = repository.get_voorbeelden_by_type(test_definitie)

        assert isinstance(by_type, dict)
        assert len(by_type["sentence"]) == 2
        assert len(by_type["practical"]) == 1
        assert len(by_type["counter"]) == 1
        assert by_type["sentence"] == ["S1", "S2"]

    def test_beoordeel_voorbeeld(self, repository, test_definitie):
        """Test beoordeel_voorbeeld functionaliteit."""
        # Save voorbeeld
        voorbeelden = {"sentence": ["Test example"]}
        saved_ids = repository.save_voorbeelden(test_definitie, voorbeelden)
        voorbeeld_id = saved_ids[0]

        # Beoordeel
        success = repository.beoordeel_voorbeeld(
            voorbeeld_id, "goed", "Excellent example!", "reviewer_123"
        )

        assert success is True

        # Verify beoordeling saved
        retrieved = repository.get_voorbeelden(test_definitie)[0]
        assert retrieved.beoordeeld is True
        assert retrieved.beoordeeling == "goed"
        assert retrieved.beoordeeling_notities == "Excellent example!"
        assert retrieved.beoordeeld_door == "reviewer_123"
        assert retrieved.beoordeeld_op is not None

    def test_beoordeel_voorbeeld_invalid_rating(self, repository, test_definitie):
        """Test beoordeel_voorbeeld with invalid rating."""
        voorbeelden = {"sentence": ["Test"]}
        saved_ids = repository.save_voorbeelden(test_definitie, voorbeelden)

        with pytest.raises(ValueError) as exc_info:
            repository.beoordeel_voorbeeld(saved_ids[0], "invalid_rating")

        assert "moet 'goed', 'matig' of 'slecht' zijn" in str(exc_info.value)

    def test_beoordeel_nonexistent_voorbeeld(self, repository):
        """Test beoordeel non-existent voorbeeld."""
        success = repository.beoordeel_voorbeeld(99999, "goed")
        assert success is False

    def test_delete_voorbeelden_all(self, repository, test_definitie):
        """Test delete all voorbeelden for definitie."""
        # Save multiple types
        voorbeelden = {"sentence": ["S1", "S2"], "practical": ["P1"], "counter": ["C1"]}
        repository.save_voorbeelden(test_definitie, voorbeelden)

        # Delete all
        deleted = repository.delete_voorbeelden(test_definitie)

        assert deleted == 4

        # Verify deleted
        remaining = repository.get_voorbeelden(test_definitie)
        assert len(remaining) == 0

    def test_delete_voorbeelden_by_type(self, repository, test_definitie):
        """Test delete voorbeelden by specific type."""
        # Save multiple types
        voorbeelden = {"sentence": ["S1", "S2"], "practical": ["P1"], "counter": ["C1"]}
        repository.save_voorbeelden(test_definitie, voorbeelden)

        # Delete only sentence type
        deleted = repository.delete_voorbeelden(test_definitie, "sentence")

        assert deleted == 2

        # Verify only sentences deleted
        remaining = repository.get_voorbeelden(test_definitie)
        assert len(remaining) == 2
        assert all(v.voorbeeld_type != "sentence" for v in remaining)

    def test_delete_nonexistent_voorbeelden(self, repository, test_definitie):
        """Test delete voorbeelden that don't exist."""
        deleted = repository.delete_voorbeelden(test_definitie)
        assert deleted == 0


class TestVoorbeeldenIntegration:
    """Integration tests voor complete voorbeelden workflow."""

    def test_complete_voorbeelden_lifecycle(self, repository, test_definitie):
        """Test complete lifecycle: create, update, review, delete."""
        # 1. Create voorbeelden
        voorbeelden = {
            "sentence": ["Example sentence 1", "Example sentence 2"],
            "practical": ["Practical use case"],
            "counter": ["Counter example"],
        }
        saved_ids = repository.save_voorbeelden(test_definitie, voorbeelden)
        assert len(saved_ids) == 4

        # 2. Get and verify
        retrieved = repository.get_voorbeelden(test_definitie)
        assert len(retrieved) == 4

        # 3. Review some examples
        for i, voorbeeld in enumerate(retrieved[:2]):
            rating = "goed" if i == 0 else "matig"
            success = repository.beoordeel_voorbeeld(
                voorbeeld.id, rating, f"Review note {i}", "reviewer"
            )
            assert success

        # 4. Update by saving new examples (deactivates old)
        new_voorbeelden = {
            "sentence": ["New sentence example"],
            "practical": ["New practical example"],
        }
        repository.save_voorbeelden(test_definitie, new_voorbeelden)

        # 5. Verify old are inactive, new are active
        all_examples = repository.get_voorbeelden(test_definitie, actief_only=False)
        active_examples = repository.get_voorbeelden(test_definitie, actief_only=True)

        assert len(all_examples) == 6  # 4 old + 2 new
        assert len(active_examples) == 2  # Only new ones

        # 6. Delete specific type
        repository.delete_voorbeelden(test_definitie, "sentence")

        # 7. Final verification
        final = repository.get_voorbeelden(test_definitie, actief_only=False)
        sentence_examples = [v for v in final if v.voorbeeld_type == "sentence"]
        assert len(sentence_examples) == 0

    def test_concurrent_operations(self, repository, test_definitie):
        """Test concurrent voorbeelden operations don't cause locks."""
        import threading

        results = {"errors": []}

        def save_voorbeelden(thread_id):
            try:
                voorbeelden = {"sentence": [f"Thread {thread_id} example"]}
                repository.save_voorbeelden(test_definitie, voorbeelden)
            except Exception as e:
                results["errors"].append(str(e))

        # Create multiple threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=save_voorbeelden, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all to complete
        for t in threads:
            t.join()

        # Check no errors
        assert len(results["errors"]) == 0

        # Verify all saved
        all_voorbeelden = repository.get_voorbeelden(test_definitie, actief_only=False)
        assert len(all_voorbeelden) >= 5  # At least one per thread


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
