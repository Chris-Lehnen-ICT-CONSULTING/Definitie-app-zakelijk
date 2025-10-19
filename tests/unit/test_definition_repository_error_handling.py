"""Tests voor de defensieve paden in DefinitionRepository."""

import sqlite3
from contextlib import contextmanager
from unittest.mock import Mock

from services.definition_repository import DefinitionRepository
from services.interfaces import Definition


class _BadIterable:
    """Helper die iteratie forceert om te falen."""

    def __iter__(self):
        msg = "cannot iterate"
        raise ValueError(msg)


def _make_repo() -> DefinitionRepository:
    repo = DefinitionRepository.__new__(DefinitionRepository)  # bypass __init__
    repo.legacy_repo = Mock()  # type: ignore[attr-defined]
    repo.db_path = ":memory:"
    repo._stats = {  # type: ignore[attr-defined]
        "total_saves": 0,
        "total_searches": 0,
        "total_updates": 0,
        "total_deletes": 0,
    }
    repo._duplicate_service = None
    return repo


def test_definition_to_record_invalid_wettelijke_basis(caplog):
    repo = _make_repo()
    definition = Definition(begrip="Test", definitie="Foo")
    definition.wettelijke_basis = _BadIterable()

    with caplog.at_level("WARNING"):
        record = repo._definition_to_record(definition)

    assert record.wettelijke_basis == "[]"
    assert "Kon wettelijke basis normaliseren" in caplog.text


def test_definition_to_updates_invalid_wettelijke_basis(caplog):
    repo = _make_repo()
    definition = Definition(begrip="Test", definitie="Foo")
    definition.wettelijke_basis = _BadIterable()

    with caplog.at_level("WARNING"):
        updates = repo._definition_to_updates(definition)

    assert updates["wettelijke_basis"] is None
    assert "Kon wettelijke_basis serialiseren" in caplog.text


def test_get_stats_logs_when_query_fails(caplog):
    repo = _make_repo()

    @contextmanager
    def _failing_connection():
        msg = "boom"
        raise sqlite3.Error(msg)
        yield

    repo._get_connection = _failing_connection  # type: ignore[attr-defined]

    with caplog.at_level("WARNING"):
        stats = repo.get_stats()

    assert stats["total_saves"] == 0
    assert "Kon repository statistieken niet ophalen" in caplog.text
