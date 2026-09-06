"""
Integration tests for voorbeelden validation chain (DEF-83).

Tests the full validation chain from UI → validation → repository → database → error propagation.
Ensures ValidationError messages propagate correctly and logging integration works.

Created: 2025-10-31
Related: DEF-74 (Pydantic validation), DEF-68/69 (logging), DEF-83 (integration tests)

DEF-519: de tests draaiden op seedrij id 1 uit schema.sql in plaats van op de
eigen definitie, en caplog stond op de facade-logger terwijl de meldingen uit
database.voorbeelden_repository komen. Beide zijn hier gecorrigeerd; de
readback loopt nu via een eigen verbinding op het databasebestand.
"""

import json
import logging
import sqlite3
from pathlib import Path

import pytest
from pydantic import ValidationError

from database.definitie_repository import DefinitieRecord, DefinitieRepository

pytestmark = [pytest.mark.integration]

# Test Data Constants


# DEF-519: de facade delegeert save_voorbeelden naar VoorbeeldenRepository; dáár
# staat de logger die "Saving voorbeelden" schrijft. caplog moet op deze naam.
VOORBEELDEN_LOGGER = "database.voorbeelden_repository"

# schema.sql seedt twee definities (id 1 en 2). Die zijn nooit van deze test;
# id 1 dient uitsluitend als discriminator voor verkeerde associatie.
SEED_DEFINITIE_ID = 1
INVALID_NEGATIVE_ID = -1  # Invalid: negative ID
INVALID_ZERO_ID = 0  # Invalid: zero is not allowed
INVALID_EXTREME_NEGATIVE_ID = -999  # Invalid: extreme negative value


# Helper Functions


def assert_error_contains(exc_info, *keywords: str) -> None:
    """Assert that error message contains any of the given keywords.

    Args:
        exc_info: pytest ExcInfo object from pytest.raises()
        *keywords: Keywords to search for (case-insensitive). If multiple
                   keywords provided, at least one must be present.

    Raises:
        AssertionError: If none of the keywords found in error message

    Example:
        with pytest.raises(ValidationError) as exc_info:
            some_function()
        assert_error_contains(exc_info, "definitie_id", "positive")
    """
    error_msg = str(exc_info.value).lower()
    assert any(
        kw.lower() in error_msg for kw in keywords
    ), f"Error '{exc_info.value!s}' should contain one of: {keywords}"


def _readback_actief(db_path: Path, definitie_id: int) -> list[dict]:
    """Lees de actieve voorbeelden terug via een eigen, verse verbinding.

    Bewust niet via ``repository._get_connection()``: die geeft de thread-local
    verbinding van de repository terug, dus dan bewijst de readback niets over
    wat er werkelijk op schijf staat. De eigen verbinding wordt in ``finally``
    gesloten — de SQLite-contextmanager doet dat niet, die commit alleen.
    """
    conn = sqlite3.connect(str(db_path))
    try:
        conn.row_factory = sqlite3.Row
        rijen = conn.execute(
            """
            SELECT definitie_id, voorbeeld_type, voorbeeld_tekst, voorbeeld_volgorde,
                   gegenereerd_door, generation_model, generation_parameters, actief
            FROM definitie_voorbeelden
            WHERE definitie_id = ? AND actief = TRUE
            ORDER BY voorbeeld_type, voorbeeld_volgorde
            """,
            (definitie_id,),
        ).fetchall()
        return [dict(rij) for rij in rijen]
    finally:
        conn.close()


def _totaal_voorbeeld_rijen(db_path: Path) -> int:
    """Alle rijen in definitie_voorbeelden — ook inactieve, ook van seeddata."""
    conn = sqlite3.connect(str(db_path))
    try:
        return conn.execute("SELECT COUNT(*) FROM definitie_voorbeelden").fetchone()[0]
    finally:
        conn.close()


def _sluit_repository(repository: DefinitieRepository) -> None:
    """Sluit de thread-local verbinding van de repository."""
    state = getattr(repository._db._thread_local, "state", None)
    if state is not None:
        state.close()


# Fixtures


@pytest.fixture
def test_db_path(tmp_path: Path) -> Path:
    """Create temporary database for testing."""
    return tmp_path / "test_voorbeelden.db"


@pytest.fixture
def repository(test_db_path: Path):
    """Repository op een verse tmp-database; verbinding sluit in finally."""
    repo = DefinitieRepository(str(test_db_path))
    try:
        yield repo
    finally:
        _sluit_repository(repo)


@pytest.fixture
def eigen_definitie_id(repository: DefinitieRepository) -> int:
    """Id van de definitie die deze test zélf aanmaakt via de echte API.

    DEF-519: eerder gingen alle tests uit van id 1. Dat is een seedrij uit
    schema.sql, niet de eigen rij — de tests bewezen dus niets over eigen data.
    """
    definitie_id = repository.create_definitie(
        DefinitieRecord(
            begrip="testbegrip",
            definitie="Een testdefinitie voor integration testing",
            categorie="type",  # Valid category from schema constraint
            organisatorische_context="Test Organisatie",
        )
    )
    assert (
        definitie_id != SEED_DEFINITIE_ID
    ), "eigen record moet te onderscheiden zijn van de seedrijen"
    return definitie_id


def test_invalid_definitie_id_rejection(
    repository: DefinitieRepository, eigen_definitie_id: int, test_db_path: Path
):
    """Test 1: Invalid definitie_id rejected at repository level.

    DEF-83 requirement: Test invalid definitie_id rejection
    """
    # Invalid: negative ID
    with pytest.raises(ValidationError) as exc_info:
        repository.save_voorbeelden(
            definitie_id=INVALID_NEGATIVE_ID,
            voorbeelden_dict={"voorbeeldzinnen": ["test"]},
        )

    # Check error message contains useful info
    assert_error_contains(exc_info, "definitie_id")
    assert_error_contains(exc_info, "positive", "greater than")

    # Invalid: zero
    with pytest.raises(ValidationError) as exc_info:
        repository.save_voorbeelden(
            definitie_id=INVALID_ZERO_ID,
            voorbeelden_dict={"voorbeeldzinnen": ["test"]},
        )

    assert_error_contains(exc_info, "definitie_id")

    # Afgewezen invoer mag niets hebben weggeschreven — ook niet inactief.
    assert _totaal_voorbeeld_rijen(test_db_path) == 0
    assert _readback_actief(test_db_path, eigen_definitie_id) == []


def test_invalid_voorbeelden_dict_type_rejection(
    repository: DefinitieRepository, eigen_definitie_id: int, test_db_path: Path
):
    """Test 2: Invalid voorbeelden_dict type rejected.

    DEF-83 requirement: Test invalid voorbeelden_dict type rejection
    """
    # Invalid: string instead of dict
    with pytest.raises(ValidationError) as exc_info:
        repository.save_voorbeelden(
            definitie_id=eigen_definitie_id,
            voorbeelden_dict="not a dict",  # type: ignore
        )

    assert_error_contains(exc_info, "voorbeelden_dict", "dict")

    # Invalid: list instead of dict
    with pytest.raises(ValidationError) as exc_info:
        repository.save_voorbeelden(
            definitie_id=eigen_definitie_id,
            voorbeelden_dict=["not", "a", "dict"],  # type: ignore
        )

    assert_error_contains(exc_info, "dict")

    # Invalid: dict with non-string keys
    with pytest.raises(ValidationError) as exc_info:
        repository.save_voorbeelden(
            definitie_id=eigen_definitie_id,
            voorbeelden_dict={123: ["test"]},  # type: ignore
        )

    assert_error_contains(exc_info, "key", "string")

    # Invalid: dict with non-list values
    with pytest.raises(ValidationError) as exc_info:
        repository.save_voorbeelden(
            definitie_id=eigen_definitie_id,
            voorbeelden_dict={"voorbeeldzinnen": "should be list"},  # type: ignore
        )

    assert_error_contains(exc_info, "list")

    assert _totaal_voorbeeld_rijen(test_db_path) == 0
    assert _readback_actief(test_db_path, eigen_definitie_id) == []


def test_empty_voorbeelden_dict_rejection(
    repository: DefinitieRepository, eigen_definitie_id: int, test_db_path: Path
):
    """Test 3: Empty voorbeelden_dict rejected.

    DEF-83 requirement: Test empty voorbeelden_dict rejection
    """
    # Empty dict
    with pytest.raises(ValidationError) as exc_info:
        repository.save_voorbeelden(
            definitie_id=eigen_definitie_id,
            voorbeelden_dict={},
        )

    assert_error_contains(exc_info, "example", "empty")

    # Dict with only empty lists
    with pytest.raises(ValidationError) as exc_info:
        repository.save_voorbeelden(
            definitie_id=eigen_definitie_id,
            voorbeelden_dict={
                "voorbeeldzinnen": [],
                "praktijkvoorbeelden": [],
            },
        )

    assert "example" in str(exc_info.value).lower()

    # Dict with only whitespace strings
    with pytest.raises(ValidationError) as exc_info:
        repository.save_voorbeelden(
            definitie_id=eigen_definitie_id,
            voorbeelden_dict={
                "voorbeeldzinnen": ["   ", "\t", "\n"],
            },
        )

    # After filtering whitespace, should be empty -> rejected
    assert "example" in str(exc_info.value).lower()

    assert _totaal_voorbeeld_rijen(test_db_path) == 0
    assert _readback_actief(test_db_path, eigen_definitie_id) == []


def test_valid_data_acceptance_and_logging(
    repository: DefinitieRepository,
    eigen_definitie_id: int,
    test_db_path: Path,
    caplog,
):
    """Test 4: Valid data accepted and logged correctly.

    DEF-83 requirement: Test valid data acceptance + logging
    DEF-68/69 requirement: Verify logging integration
    """
    caplog.set_level(logging.INFO, logger=VOORBEELDEN_LOGGER)

    # Valid voorbeelden dict
    valid_voorbeelden = {
        "voorbeeldzinnen": ["Voorbeeld 1", "Voorbeeld 2"],
        "praktijkvoorbeelden": ["Praktijk 1"],
        "tegenvoorbeelden": ["Tegen 1"],
    }

    # Should succeed
    result = repository.save_voorbeelden(
        definitie_id=eigen_definitie_id,
        voorbeelden_dict=valid_voorbeelden,
        generation_model="gpt-4",
        gegenereerd_door="test_system",
    )

    # Verify result
    assert isinstance(result, list)
    assert len(result) == 4  # 2 zinnen + 1 praktijk + 1 tegenvoorbeeld

    # Verse, onafhankelijke readback: exacte inhoud op de eigen definitie
    rijen = _readback_actief(test_db_path, eigen_definitie_id)
    assert [
        (rij["voorbeeld_type"], rij["voorbeeld_tekst"], rij["voorbeeld_volgorde"])
        for rij in rijen
    ] == [
        ("counter", "Tegen 1", 1),
        ("practical", "Praktijk 1", 1),
        ("sentence", "Voorbeeld 1", 1),
        ("sentence", "Voorbeeld 2", 2),
    ]
    for rij in rijen:
        assert rij["definitie_id"] == eigen_definitie_id
        assert rij["actief"] == 1
        assert rij["generation_model"] == "gpt-4"
        assert rij["gegenereerd_door"] == "test_system"

    # Discriminator: niets mag onder de seedrij zijn beland.
    assert _readback_actief(test_db_path, SEED_DEFINITIE_ID) == []
    assert _totaal_voorbeeld_rijen(test_db_path) == 4

    # Verify logging (DEF-68/69 integration) op de logger die het écht schrijft
    save_records = [
        record
        for record in caplog.records
        if record.name == VOORBEELDEN_LOGGER and "Saving voorbeelden" in record.message
    ]
    assert save_records, "save_voorbeelden hoort op INFO te loggen"
    assert any(
        f"definitie {eigen_definitie_id}" in record.message for record in save_records
    )


def test_error_message_clarity(
    repository: DefinitieRepository, eigen_definitie_id: int
):
    """Test 5: Error messages are clear and actionable.

    DEF-83 requirement: Test error message clarity for end users
    """
    # Test error for invalid ID
    with pytest.raises(ValidationError) as exc_info:
        repository.save_voorbeelden(
            definitie_id=INVALID_EXTREME_NEGATIVE_ID,
            voorbeelden_dict={"voorbeeldzinnen": ["test"]},
        )

    error = exc_info.value

    # Error should contain field name
    assert any("definitie_id" in str(err) for err in error.errors())

    # Error should contain constraint info
    assert_error_contains(exc_info, "positive", "greater")

    # Test error for wrong type
    with pytest.raises(ValidationError) as exc_info:
        repository.save_voorbeelden(
            definitie_id=eigen_definitie_id,
            voorbeelden_dict={"voorbeeldzinnen": "not a list"},  # type: ignore
        )

    error = exc_info.value

    # Should mention the problematic field
    assert any(
        "voorbeeldzinnen" in str(err) or "list" in str(err) for err in error.errors()
    )


def test_logging_integration_with_context(
    repository: DefinitieRepository, eigen_definitie_id: int, caplog
):
    """Test 6: Logging contains expected context (DEF-68/69).

    DEF-83 requirement: Test logging integration (DEF-68/69)
    Verifies that error logging includes contextual information.
    """
    caplog.set_level(logging.ERROR, logger=VOORBEELDEN_LOGGER)

    # Trigger validation error
    with pytest.raises(ValidationError):
        repository.save_voorbeelden(
            definitie_id=INVALID_NEGATIVE_ID,
            voorbeelden_dict={"voorbeeldzinnen": ["test"]},
        )

    # Find error log record
    error_records = [
        r
        for r in caplog.records
        if r.levelname == "ERROR" and r.name == VOORBEELDEN_LOGGER
    ]
    assert len(error_records) > 0, "Should have logged error"

    error_record = error_records[0]

    # Verify error log contains context (DEF-68/69)
    assert "Validation failed" in error_record.message
    assert "definitie" in error_record.message.lower()

    # Verify exc_info is set (for stack traces)
    assert error_record.exc_info is not None

    # Verify extra context is logged (DEF-68/69 structured logging)
    # Repository logs: definitie_id, error_details, error_count
    assert error_record.definitie_id == INVALID_NEGATIVE_ID
    assert error_record.definitie_id != eigen_definitie_id
    assert error_record.error_count > 0


def test_validation_chain_end_to_end(
    repository: DefinitieRepository,
    eigen_definitie_id: int,
    test_db_path: Path,
    caplog,
):
    """Test 7: Complete end-to-end validation chain.

    Tests full flow: input → Pydantic validation → repository → database → logging
    """
    caplog.set_level(logging.INFO, logger=VOORBEELDEN_LOGGER)

    # Valid flow
    valid_result = repository.save_voorbeelden(
        definitie_id=eigen_definitie_id,
        voorbeelden_dict={
            "voorbeeldzinnen": ["Zin 1", "Zin 2"],
            "praktijkvoorbeelden": ["Praktijk"],
        },
        generation_model="gpt-4",
        generation_params={"temperature": 0.7},
        gegenereerd_door="integration_test",
    )

    assert len(valid_result) == 3
    assert all(isinstance(id, int) for id in valid_result)

    # Verify database state — verse readback, exacte inhoud en actorvelden
    rijen = _readback_actief(test_db_path, eigen_definitie_id)
    assert [
        (rij["voorbeeld_type"], rij["voorbeeld_tekst"], rij["voorbeeld_volgorde"])
        for rij in rijen
    ] == [
        ("practical", "Praktijk", 1),
        ("sentence", "Zin 1", 1),
        ("sentence", "Zin 2", 2),
    ]
    for rij in rijen:
        assert rij["definitie_id"] == eigen_definitie_id
        assert rij["actief"] == 1
        assert rij["gegenereerd_door"] == "integration_test"
        assert json.loads(rij["generation_parameters"]) == {"temperature": 0.7}

    # Verkeerde associatie moet leeg blijven.
    assert _readback_actief(test_db_path, SEED_DEFINITIE_ID) == []

    # Verify logging
    info_records = [
        r
        for r in caplog.records
        if r.levelname == "INFO" and r.name == VOORBEELDEN_LOGGER
    ]
    assert any("Saving voorbeelden" in r.message for r in info_records)
    assert any(f"definitie {eigen_definitie_id}" in r.message for r in info_records)

    # Invalid flow - verify error propagation
    caplog.clear()
    caplog.set_level(logging.ERROR, logger=VOORBEELDEN_LOGGER)

    with pytest.raises(ValidationError):
        repository.save_voorbeelden(
            definitie_id=INVALID_ZERO_ID,
            voorbeelden_dict={"voorbeeldzinnen": ["test"]},
        )

    # Verify error was logged
    error_records = [
        r
        for r in caplog.records
        if r.levelname == "ERROR" and r.name == VOORBEELDEN_LOGGER
    ]
    assert len(error_records) > 0
    assert any("Validation failed" in r.message for r in error_records)

    # De afgewezen save mag de geldige rijen niet hebben aangeraakt.
    assert _readback_actief(test_db_path, eigen_definitie_id) == rijen
    assert _totaal_voorbeeld_rijen(test_db_path) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
