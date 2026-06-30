"""Tests voor de voorkeursterm-persistentie in VoorbeeldenRepository (DEF-469).

`_update_voorkeursterm` swallowt voorheen elke exception (en deed een eigen
commit), waardoor een mislukte voorkeursterm-update de door de gebruiker gekozen
term stil verloor. De fix laat de methode binnen de transactie van de aanroeper
draaien: geen eigen commit en geen swallow, zodat een fout terugrolt en
zichtbaar propageert.
"""

from __future__ import annotations

import sqlite3
from unittest.mock import Mock

import pytest

from database.voorbeelden_repository import VoorbeeldenRepository

pytestmark = [pytest.mark.unit]


def _repo() -> VoorbeeldenRepository:
    # _update_voorkeursterm gebruikt alleen het conn-argument, geen self-state.
    return VoorbeeldenRepository.__new__(VoorbeeldenRepository)


def test_update_voorkeursterm_propagates_error():
    """Een DB-fout wordt niet langer stil geslikt maar propageert."""
    repo = _repo()
    conn = Mock()
    conn.cursor.return_value.execute.side_effect = sqlite3.OperationalError("boom")

    with pytest.raises(sqlite3.OperationalError):
        repo._update_voorkeursterm(conn, 1, "voorkeursterm")


def test_update_voorkeursterm_does_not_commit_itself():
    """De methode commit niet zelf; de aanroeper commit de hele transactie."""
    repo = _repo()
    conn = Mock()

    repo._update_voorkeursterm(conn, 1, "voorkeursterm")

    conn.commit.assert_not_called()


def test_update_voorkeursterm_sets_null_when_empty():
    """Lege voorkeursterm zet de kolom op NULL."""
    repo = _repo()
    conn = Mock()
    cursor = conn.cursor.return_value

    repo._update_voorkeursterm(conn, 7, None)

    sql = cursor.execute.call_args.args[0]
    assert "NULL" in sql


def test_update_voorkeursterm_strips_and_binds_term():
    """Een geldige term wordt gestript en als bind-parameter doorgegeven."""
    repo = _repo()
    conn = Mock()
    cursor = conn.cursor.return_value

    repo._update_voorkeursterm(conn, 42, "  Mijn Term  ")

    sql, params = cursor.execute.call_args.args
    assert "NULL" not in sql
    assert params == ("Mijn Term", 42)


def _raise_voorkeursterm(*_args, **_kwargs):
    raise sqlite3.OperationalError("voorkeursterm boom")


def test_save_voorbeelden_propagates_voorkeursterm_error(tmp_path, monkeypatch):
    """End-to-end: een voorkeursterm-fout propageert (niet langer stil geslikt).

    Dit is de kern van DEF-469: de gebruiker/aanroeper ziet dat de voorkeursterm
    niet is opgeslagen i.p.v. een stille `logger.warning`. (Volledige rollback-
    atomariteit van de multi-step save valt onder DEF-391; deze connectie draait
    in autocommit, dus reeds geschreven voorbeelden-rijen blijven hier bestaan.)
    """
    from database.definitie_repository import DefinitieRecord, DefinitieRepository

    db_path = str(tmp_path / "voorbeelden_propagate.db")
    repo = DefinitieRepository(db_path)
    def_id = repo.create_definitie(
        DefinitieRecord(
            begrip="propagate_begrip",
            definitie="Definitie voor propagatie-test",
            categorie="proces",
            organisatorische_context="TEST_ORG",
        )
    )

    # Forceer een fout in de voorkeursterm-stap.
    monkeypatch.setattr(
        repo._voorbeelden, "_update_voorkeursterm", _raise_voorkeursterm
    )

    # De fout wordt niet langer stil geslikt maar propageert.
    with pytest.raises(sqlite3.OperationalError):
        repo.save_voorbeelden(
            def_id, {"sentence": ["Voorbeeld X"]}, voorkeursterm="term"
        )
