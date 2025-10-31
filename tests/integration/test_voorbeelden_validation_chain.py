"""
Integration tests for voorbeelden validation chain (DEF-83).

Tests the full validation chain from UI → validation → repository → database → error propagation.
Ensures ValidationError messages propagate correctly and logging integration works.

Created: 2025-10-31
Related: DEF-74 (Pydantic validation), DEF-68/69 (logging), DEF-83 (integration tests)
"""

import logging
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from database.definitie_repository import DefinitieRepository


@pytest.fixture()
def test_db_path(tmp_path: Path) -> Path:
    """Create temporary database for testing."""
    return tmp_path / "test_voorbeelden.db"


@pytest.fixture()
def repository(test_db_path: Path) -> DefinitieRepository:
    """Create repository instance with test database."""
    repo = DefinitieRepository(str(test_db_path))

    # Create a test definitie to save voorbeelden to
    from database.definitie_repository import DefinitieRecord

    test_def = DefinitieRecord(
        begrip="testbegrip",
        definitie="Een testdefinitie voor integration testing",
        categorie="type",  # Valid category from schema constraint
        organisatorische_context="Test Organisatie",
    )

    # Insert via raw SQL to avoid dependencies
    with repo._get_connection() as conn:
        conn.execute(
            """
            INSERT INTO definities (begrip, definitie, categorie, organisatorische_context)
            VALUES (?, ?, ?, ?)
            """,
            (
                test_def.begrip,
                test_def.definitie,
                test_def.categorie,
                test_def.organisatorische_context,
            ),
        )
        conn.commit()

    return repo


def test_invalid_definitie_id_rejection(repository: DefinitieRepository):
    """Test 1: Invalid definitie_id rejected at repository level.

    DEF-83 requirement: Test invalid definitie_id rejection
    """
    # Invalid: negative ID
    with pytest.raises(ValidationError) as exc_info:
        repository.save_voorbeelden(
            definitie_id=-1,
            voorbeelden_dict={"voorbeeldzinnen": ["test"]},
        )

    # Check error message contains useful info
    error_msg = str(exc_info.value)
    assert "definitie_id" in error_msg.lower()
    assert "positive" in error_msg.lower() or "greater than" in error_msg.lower()

    # Invalid: zero
    with pytest.raises(ValidationError) as exc_info:
        repository.save_voorbeelden(
            definitie_id=0,
            voorbeelden_dict={"voorbeeldzinnen": ["test"]},
        )

    assert "definitie_id" in str(exc_info.value).lower()


def test_invalid_voorbeelden_dict_type_rejection(repository: DefinitieRepository):
    """Test 2: Invalid voorbeelden_dict type rejected.

    DEF-83 requirement: Test invalid voorbeelden_dict type rejection
    """
    # Invalid: string instead of dict
    with pytest.raises(ValidationError) as exc_info:
        repository.save_voorbeelden(
            definitie_id=1,
            voorbeelden_dict="not a dict",  # type: ignore
        )

    error_msg = str(exc_info.value)
    assert "voorbeelden_dict" in error_msg.lower() or "dict" in error_msg.lower()

    # Invalid: list instead of dict
    with pytest.raises(ValidationError) as exc_info:
        repository.save_voorbeelden(
            definitie_id=1,
            voorbeelden_dict=["not", "a", "dict"],  # type: ignore
        )

    assert "dict" in str(exc_info.value).lower()

    # Invalid: dict with non-string keys
    with pytest.raises(ValidationError) as exc_info:
        repository.save_voorbeelden(
            definitie_id=1,
            voorbeelden_dict={123: ["test"]},  # type: ignore
        )

    error_msg = str(exc_info.value)
    assert "key" in error_msg.lower() or "string" in error_msg.lower()

    # Invalid: dict with non-list values
    with pytest.raises(ValidationError) as exc_info:
        repository.save_voorbeelden(
            definitie_id=1,
            voorbeelden_dict={"voorbeeldzinnen": "should be list"},  # type: ignore
        )

    assert "list" in str(exc_info.value).lower()


def test_empty_voorbeelden_dict_rejection(repository: DefinitieRepository):
    """Test 3: Empty voorbeelden_dict rejected.

    DEF-83 requirement: Test empty voorbeelden_dict rejection
    """
    # Empty dict
    with pytest.raises(ValidationError) as exc_info:
        repository.save_voorbeelden(
            definitie_id=1,
            voorbeelden_dict={},
        )

    error_msg = str(exc_info.value)
    assert "example" in error_msg.lower() or "empty" in error_msg.lower()

    # Dict with only empty lists
    with pytest.raises(ValidationError) as exc_info:
        repository.save_voorbeelden(
            definitie_id=1,
            voorbeelden_dict={
                "voorbeeldzinnen": [],
                "praktijkvoorbeelden": [],
            },
        )

    assert "example" in str(exc_info.value).lower()

    # Dict with only whitespace strings
    with pytest.raises(ValidationError) as exc_info:
        repository.save_voorbeelden(
            definitie_id=1,
            voorbeelden_dict={
                "voorbeeldzinnen": ["   ", "\t", "\n"],
            },
        )

    # After filtering whitespace, should be empty -> rejected
    assert "example" in str(exc_info.value).lower()


def test_valid_data_acceptance_and_logging(repository: DefinitieRepository, caplog):
    """Test 4: Valid data accepted and logged correctly.

    DEF-83 requirement: Test valid data acceptance + logging
    DEF-68/69 requirement: Verify logging integration
    """
    caplog.set_level(logging.INFO, logger="database.definitie_repository")

    # Valid voorbeelden dict
    valid_voorbeelden = {
        "voorbeeldzinnen": ["Voorbeeld 1", "Voorbeeld 2"],
        "praktijkvoorbeelden": ["Praktijk 1"],
        "tegenvoorbeelden": ["Tegen 1"],
    }

    # Should succeed
    result = repository.save_voorbeelden(
        definitie_id=1,
        voorbeelden_dict=valid_voorbeelden,
        generation_model="gpt-4",
        gegenereerd_door="test_system",
    )

    # Verify result
    assert isinstance(result, list)
    assert len(result) > 0  # Should return IDs of saved voorbeelden

    # Verify logging (DEF-68/69 integration)
    assert any("Saving voorbeelden" in record.message for record in caplog.records)
    assert any("definitie 1" in record.message for record in caplog.records)


def test_error_message_clarity(repository: DefinitieRepository):
    """Test 5: Error messages are clear and actionable.

    DEF-83 requirement: Test error message clarity for end users
    """
    # Test error for invalid ID
    with pytest.raises(ValidationError) as exc_info:
        repository.save_voorbeelden(
            definitie_id=-999,
            voorbeelden_dict={"voorbeeldzinnen": ["test"]},
        )

    error = exc_info.value

    # Error should contain field name
    assert any("definitie_id" in str(err) for err in error.errors())

    # Error should contain constraint info
    error_str = str(error)
    assert "positive" in error_str.lower() or "greater" in error_str.lower()

    # Test error for wrong type
    with pytest.raises(ValidationError) as exc_info:
        repository.save_voorbeelden(
            definitie_id=1,
            voorbeelden_dict={"voorbeeldzinnen": "not a list"},  # type: ignore
        )

    error = exc_info.value

    # Should mention the problematic field
    assert any(
        "voorbeeldzinnen" in str(err) or "list" in str(err) for err in error.errors()
    )


def test_logging_integration_with_context(repository: DefinitieRepository, caplog):
    """Test 6: Logging contains expected context (DEF-68/69).

    DEF-83 requirement: Test logging integration (DEF-68/69)
    Verifies that error logging includes contextual information.
    """
    caplog.set_level(logging.ERROR, logger="database.definitie_repository")

    # Trigger validation error
    with pytest.raises(ValidationError):
        repository.save_voorbeelden(
            definitie_id=-1,
            voorbeelden_dict={"voorbeeldzinnen": ["test"]},
        )

    # Find error log record
    error_records = [r for r in caplog.records if r.levelname == "ERROR"]
    assert len(error_records) > 0, "Should have logged error"

    error_record = error_records[0]

    # Verify error log contains context (DEF-68/69)
    assert "Validation failed" in error_record.message
    assert "definitie" in error_record.message.lower()

    # Verify exc_info is set (for stack traces)
    assert error_record.exc_info is not None

    # Verify extra context is logged (DEF-68/69 structured logging)
    # Repository logs: definitie_id, error_details, error_count
    if hasattr(error_record, "definitie_id"):
        assert error_record.definitie_id == -1
    if hasattr(error_record, "error_count"):
        assert error_record.error_count > 0


def test_validation_chain_end_to_end(repository: DefinitieRepository, caplog):
    """Test 7: Complete end-to-end validation chain.

    Tests full flow: input → Pydantic validation → repository → database → logging
    """
    caplog.set_level(logging.INFO, logger="database.definitie_repository")

    # Valid flow
    valid_result = repository.save_voorbeelden(
        definitie_id=1,
        voorbeelden_dict={
            "voorbeeldzinnen": ["Zin 1", "Zin 2"],
            "praktijkvoorbeelden": ["Praktijk"],
        },
        generation_model="gpt-4",
        generation_params={"temperature": 0.7},
        gegenereerd_door="integration_test",
    )

    assert len(valid_result) > 0
    assert all(isinstance(id, int) for id in valid_result)

    # Verify database state
    with repository._get_connection() as conn:
        cursor = conn.execute(
            "SELECT COUNT(*) FROM definitie_voorbeelden WHERE definitie_id = 1 AND actief = TRUE"
        )
        count = cursor.fetchone()[0]
        assert count > 0, "Should have saved voorbeelden to database"

    # Verify logging
    info_records = [r for r in caplog.records if r.levelname == "INFO"]
    assert any("Saving voorbeelden" in r.message for r in info_records)

    # Invalid flow - verify error propagation
    caplog.clear()
    caplog.set_level(logging.ERROR, logger="database.definitie_repository")

    with pytest.raises(ValidationError):
        repository.save_voorbeelden(
            definitie_id=0,  # Invalid
            voorbeelden_dict={"voorbeeldzinnen": ["test"]},
        )

    # Verify error was logged
    error_records = [r for r in caplog.records if r.levelname == "ERROR"]
    assert len(error_records) > 0
    assert any("Validation failed" in r.message for r in error_records)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
