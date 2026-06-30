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
