"""Tests voor DB-transactie-atomiciteit (DEF-391).

De connectie draait in autocommit (`isolation_level=None`), waardoor `with conn:`
en losse `conn.commit()`/`conn.rollback()` geen atomiciteit bieden: een multi-step
operatie die halverwege faalt liet de database in een inconsistente staat achter.

`DatabaseConnection.transaction()` lost dit op met expliciete BEGIN/COMMIT/ROLLBACK
en een nesting-guard (`conn.in_transaction`) zodat geneste aanroepen aansluiten bij
de buitenste transactie i.p.v. een — door SQLite verboden — geneste BEGIN.
"""

from __future__ import annotations

import sqlite3

import pytest

from database.db_connection import DatabaseConnection
from database.definitie_repository import DefinitieRecord, DefinitieRepository

pytestmark = [pytest.mark.unit]


def _db(tmp_path) -> DatabaseConnection:
    db = DatabaseConnection(str(tmp_path / "atomiciteit.db"))
    with db.get_connection() as conn:
        conn.execute("CREATE TABLE t (x INTEGER)")
    return db


# --- transaction() context manager ---------------------------------------


def test_transaction_commits_on_success(tmp_path):
    db = _db(tmp_path)
    with db.transaction() as conn:
        conn.execute("INSERT INTO t (x) VALUES (1)")

    count = db.get_connection().execute("SELECT COUNT(*) FROM t").fetchone()[0]
    assert count == 1


def test_transaction_rolls_back_on_exception(tmp_path):
    db = _db(tmp_path)

    def _insert_then_fail() -> None:
        with db.transaction() as conn:
            conn.execute("INSERT INTO t (x) VALUES (1)")
            raise RuntimeError("boom halverwege")

    with pytest.raises(RuntimeError):
        _insert_then_fail()

    count = db.get_connection().execute("SELECT COUNT(*) FROM t").fetchone()[0]
    assert count == 0


def test_transaction_nesting_joins_outer_rollback(tmp_path):
    """Een geneste transaction() sluit aan bij de buitenste; faalt de buitenste,
    dan rolt ook de binnenste-schrijf terug (bewijst: geen eigen commit)."""
    db = _db(tmp_path)

    def _nested_then_fail() -> None:
        with db.transaction() as outer:
            outer.execute("INSERT INTO t (x) VALUES (1)")
            # inner moet sluiten vóór de raise: bewijst dat inner niet zelf
            # commit terwijl outer nog openstaat.
            with db.transaction() as inner:
                inner.execute("INSERT INTO t (x) VALUES (2)")
            raise RuntimeError("buitenste faalt na geneste write")

    with pytest.raises(RuntimeError):
        _nested_then_fail()

    count = db.get_connection().execute("SELECT COUNT(*) FROM t").fetchone()[0]
    assert count == 0


def test_connection_is_autocommit(tmp_path):
    """transaction() gaat uit van autocommit (isolation_level=None); anders zou
    een expliciete BEGIN IMMEDIATE botsen met een impliciete module-transactie."""
    db = _db(tmp_path)
    assert db.get_connection().isolation_level is None


def test_read_within_transaction_does_not_commit(tmp_path):
    """Een read (SELECT) binnen een lopende transactie mag die transactie niet
    committen — bewijst dat de kale-conn reads (get_definitie/log_geschiedenis)
    de transactie van de aanroeper niet vroegtijdig sluiten."""
    db = _db(tmp_path)

    def _write_read_then_fail() -> None:
        with db.transaction() as conn:
            conn.execute("INSERT INTO t (x) VALUES (1)")
            # Read midden in de transactie (zoals get_definitie doet).
            conn.execute("SELECT COUNT(*) FROM t").fetchone()
            raise RuntimeError("faalt na read")

    with pytest.raises(RuntimeError):
        _write_read_then_fail()

    count = db.get_connection().execute("SELECT COUNT(*) FROM t").fetchone()[0]
    assert count == 0


def test_transaction_nesting_commits_together(tmp_path):
    db = _db(tmp_path)
    with db.transaction() as outer:
        outer.execute("INSERT INTO t (x) VALUES (1)")
        with db.transaction() as inner:
            inner.execute("INSERT INTO t (x) VALUES (2)")

    count = db.get_connection().execute("SELECT COUNT(*) FROM t").fetchone()[0]
    assert count == 2


# --- echte multi-step operaties ------------------------------------------


def _raise(*_args, **_kwargs):
    raise sqlite3.OperationalError("gesimuleerde fout halverwege")


def test_save_voorbeelden_rolls_back_partial_write(tmp_path, monkeypatch):
    """De kern van DEF-391: save_voorbeelden deactiveert eerst alle bestaande
    voorbeelden en inserteert dan nieuwe. Faalt de voorkeursterm-stap, dan moet
    de deactivering én de partiële insert terugrollen — de oorspronkelijke
    voorbeelden blijven ongewijzigd behouden i.p.v. verloren te gaan."""
    repo = DefinitieRepository(str(tmp_path / "rollback.db"))
    def_id = repo.create_definitie(
        DefinitieRecord(
            begrip="rollback_begrip",
            definitie="Definitie voor rollback-test",
            categorie="proces",
            organisatorische_context="TEST_ORG",
        )
    )
    repo.save_voorbeelden(def_id, {"sentence": ["Origineel A", "Origineel B"]})
    assert repo.get_voorbeelden_by_type(def_id) == {
        "sentence": ["Origineel A", "Origineel B"]
    }

    # Forceer een fout ná de inserts (in de voorkeursterm-stap).
    monkeypatch.setattr(repo._voorbeelden, "_update_voorkeursterm", _raise)
    with pytest.raises(sqlite3.OperationalError):
        repo.save_voorbeelden(def_id, {"sentence": ["Nieuw C"]}, voorkeursterm="term")

    # De originele voorbeelden zijn intact; niets partieel opgeslagen.
    assert repo.get_voorbeelden_by_type(def_id) == {
        "sentence": ["Origineel A", "Origineel B"]
    }


def test_create_definitie_rolls_back_on_audit_failure(tmp_path, monkeypatch):
    """create_definitie doet INSERT + audit-log. Faalt de audit-stap, dan moet
    de definitie-INSERT terugrollen (geen weesrecord zonder audit-trail)."""
    repo = DefinitieRepository(str(tmp_path / "create_rollback.db"))
    monkeypatch.setattr(repo._audit, "log_geschiedenis", _raise)

    with pytest.raises(sqlite3.OperationalError):
        repo.create_definitie(
            DefinitieRecord(
                begrip="weesrecord",
                definitie="Mag niet blijven bestaan",
                categorie="proces",
                organisatorische_context="TEST_ORG",
            )
        )

    with repo._db.get_connection() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM definities WHERE begrip = ?", ("weesrecord",)
        ).fetchone()[0]
    assert count == 0


def test_update_definitie_rolls_back_on_audit_failure(tmp_path, monkeypatch):
    """update_definitie doet UPDATE + audit-log; faalt de audit-stap, dan blijft
    de oorspronkelijke waarde staan (UPDATE teruggerold)."""
    repo = DefinitieRepository(str(tmp_path / "update_rollback.db"))
    def_id = repo.create_definitie(
        DefinitieRecord(
            begrip="update_begrip",
            definitie="Originele definitie",
            categorie="proces",
            organisatorische_context="TEST_ORG",
        )
    )
    monkeypatch.setattr(repo._audit, "log_geschiedenis", _raise)

    with pytest.raises(sqlite3.OperationalError):
        repo.update_definitie(def_id, {"definitie": "Gewijzigde definitie"})

    record = repo.get_definitie(def_id)
    assert record is not None
    assert record.definitie == "Originele definitie"


def test_change_status_rolls_back_on_audit_failure(tmp_path, monkeypatch):
    """change_status omhult update_definitie (join) + audit-log in één transactie.
    Faalt de audit-stap, dan rolt de statuswijziging mee terug."""
    from database.definitie_repository import DefinitieStatus

    repo = DefinitieRepository(str(tmp_path / "change_status_rollback.db"))
    def_id = repo.create_definitie(
        DefinitieRecord(
            begrip="status_begrip",
            definitie="Definitie voor status-test",
            categorie="proces",
            organisatorische_context="TEST_ORG",
        )
    )
    original = repo.get_definitie(def_id)
    assert original is not None

    monkeypatch.setattr(repo._audit, "log_geschiedenis", _raise)
    with pytest.raises(sqlite3.OperationalError):
        repo.change_status(def_id, DefinitieStatus.ESTABLISHED, changed_by="tester")

    # De statuswijziging is teruggerold — status blijft de oorspronkelijke.
    record = repo.get_definitie(def_id)
    assert record is not None
    assert record.status == original.status


def test_beoordeel_voorbeeld_not_found_returns_false(tmp_path):
    """Het rowcount==0-pad (niet-bestaand voorbeeld) geeft False zonder crash."""
    repo = DefinitieRepository(str(tmp_path / "beoordeel_notfound.db"))
    assert repo.beoordeel_voorbeeld(999999, "goed") is False


def test_update_definitie_optimistic_lock_returns_false(tmp_path):
    """Optimistic-lock mismatch (rowcount==0) geeft False; de no-op transactie
    commit zonder zij-effect en laat de definitie ongewijzigd."""
    repo = DefinitieRepository(str(tmp_path / "optimistic_lock.db"))
    def_id = repo.create_definitie(
        DefinitieRecord(
            begrip="lock_begrip",
            definitie="Originele definitie",
            categorie="proces",
            organisatorische_context="TEST_ORG",
        )
    )

    # version_number=999 matcht niet → WHERE mismatch → rowcount 0.
    ok = repo.update_definitie(def_id, {"definitie": "Nieuw", "version_number": 999})
    assert ok is False

    record = repo.get_definitie(def_id)
    assert record is not None
    assert record.definitie == "Originele definitie"
