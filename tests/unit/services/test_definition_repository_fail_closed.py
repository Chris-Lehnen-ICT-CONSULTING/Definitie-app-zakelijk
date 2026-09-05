"""Fail-closed repositorymutaties op echte SQLite (DEF-469): save() negeerde een
falsey update-resultaat, hard_delete() committe nooit. Duurzaamheid wordt bewezen
via een onafhankelijke connectie; foutinjectie via de SQLite-authorizer op de
echte transactie, zonder gemockte commit."""

from __future__ import annotations

import logging
import sqlite3

import pytest

from database.definitie_repository import DefinitieRecord
from services.definition_repository import DefinitionRepository
from services.definition_workflow_service import _VaststellingMisluktError
from services.exceptions import (
    DatabaseConnectionError,
    DatabaseConstraintError,
    DefinitionServiceError,
    RepositoryError,
)
from services.interfaces import Definition

pytestmark = [pytest.mark.unit]

ORIGINEEL = "Originele definitie"


@pytest.fixture
def repo(tmp_path) -> DefinitionRepository:
    return DefinitionRepository(str(tmp_path / "fail_closed.db"))


def _bestaand(repo: DefinitionRepository, definitie: str = ORIGINEEL) -> int:
    record = DefinitieRecord(begrip=definitie, definitie=definitie, categorie="proces")
    return repo.legacy_repo.create_definitie(record)


def _definitie(definitie_id: int | None, tekst: str) -> Definition:
    return Definition(id=definitie_id, begrip="begrip", definitie=tekst)


def _lees(repo: DefinitionRepository, definitie_id: int) -> str | None:
    """Onafhankelijke lezer: eigen connectie, ziet uitsluitend gecommitte data."""
    conn = sqlite3.connect(repo.db_path)
    try:
        sql = "SELECT definitie FROM definities WHERE id = ?"
        row = conn.execute(sql, (definitie_id,)).fetchone()
    finally:
        conn.close()
    return None if row is None else row[0]


def _weiger(actie: int, *operaties: str):
    """Authorizer die één SQLite-actie weigert, optioneel alleen voor deze operaties."""

    def authorizer(soort: int, arg1: str | None, *_: object) -> int:
        geweigerd = soort == actie and (not operaties or arg1 in operaties)
        return sqlite3.SQLITE_DENY if geweigerd else sqlite3.SQLITE_OK

    return authorizer


def _assert_veilig(fout: Exception, tmp_path) -> None:
    melding = str(fout).lower()
    assert "sqlite" not in melding and "not authorized" not in melding
    assert str(tmp_path).lower() not in melding and "delete from" not in melding


def test_save_update_van_ontbrekend_id_is_typed_fout_zonder_succesclaim(repo, caplog):
    with caplog.at_level(logging.INFO), pytest.raises(RepositoryError) as exc:
        repo.save(_definitie(987654, "spookdefinitie"))

    assert exc.value.operation == "save_update"
    assert str(exc.value) == (
        "Opslaan niet bevestigd; ververs de definitie en probeer opnieuw."
    )
    assert _lees(repo, 987654) is None
    assert repo._stats["total_saves"] == 0
    assert "Updated definition" not in caplog.text


@pytest.mark.parametrize("via", ["create", "update"])
def test_save_is_na_return_zichtbaar_voor_onafhankelijke_lezer(repo, via):
    definitie_id = _bestaand(repo) if via == "update" else None

    resultaat = repo.save(_definitie(definitie_id, "bevestigde tekst"))

    assert resultaat > 0 and (definitie_id is None or resultaat == definitie_id)
    assert _lees(repo, resultaat) == "bevestigde tekst"
    assert repo._stats["total_saves"] == 1


@pytest.mark.parametrize("fout", ["commit-geweigerd", "update-trigger"])
def test_zelfstandige_save_update_fout_is_typed_met_veilige_melding(
    repo, tmp_path, fout
):
    """Standalone update loopt via de legacy-handlers: type en oorzaak blijven,
    maar de melding bevat geen ruwe SQLite-/SQL-/padtekst (Codex-review)."""
    verwacht = DatabaseConstraintError if fout == "update-trigger" else RepositoryError
    definitie_id = _bestaand(repo)
    conn = repo.legacy_repo._db.get_connection()
    if fout == "update-trigger":  # echte trigger; de fouttekst bevat SQL en een pad
        conn.execute(
            "CREATE TRIGGER weiger BEFORE UPDATE ON definities BEGIN "
            f"SELECT RAISE(ABORT, 'UPDATE definities; {tmp_path}'); END"
        )
    else:
        conn.set_authorizer(_weiger(sqlite3.SQLITE_TRANSACTION, "COMMIT"))
    try:
        with pytest.raises(verwacht) as exc:
            repo.save(_definitie(definitie_id, "gewijzigd"))
        assert not conn.in_transaction  # productie rolde zelf terug
    finally:
        conn.set_authorizer(None)

    assert isinstance(exc.value.__cause__, sqlite3.Error)
    _assert_veilig(exc.value, tmp_path)
    assert repo._stats["total_saves"] == 0
    assert _lees(repo, definitie_id) == ORIGINEEL


def test_hard_delete_verwijdert_rij_en_geeft_daarna_false(repo):
    definitie_id = _bestaand(repo)

    assert repo.hard_delete(definitie_id) is True
    assert _lees(repo, definitie_id) is None
    assert repo.hard_delete(definitie_id) is False  # afwezig ID: geen fout


def test_hard_delete_databasefout_is_typed_en_laat_rij_staan(repo, tmp_path):
    definitie_id = _bestaand(repo)
    conn = repo.legacy_repo._db.get_connection()
    conn.set_authorizer(_weiger(sqlite3.SQLITE_DELETE))
    try:
        with pytest.raises(DefinitionServiceError) as exc:
            repo.hard_delete(definitie_id)
    finally:
        conn.set_authorizer(None)

    assert isinstance(exc.value.__cause__, sqlite3.Error)
    _assert_veilig(exc.value, tmp_path)
    assert not conn.in_transaction
    assert _lees(repo, definitie_id) == ORIGINEEL


@pytest.mark.parametrize("via", ["create", "update"])
@pytest.mark.parametrize(
    "geweigerd",
    [("COMMIT",), ("COMMIT", "ROLLBACK")],
    ids=["commit-faalt", "commit-en-rollback-falen"],
)
def test_geneste_save_en_delete_geven_geen_succes_als_buitenste_commit_faalt(
    repo, tmp_path, caplog, geweigerd, via
):
    id_a, id_b = _bestaand(repo, "A"), _bestaand(repo, "B")
    caplog.set_level(logging.INFO)
    save_id = id_a if via == "update" else None
    gezien: list[int] = []  # het ID dat de geneste save teruggaf

    def genest() -> None:
        with repo.transaction():
            # Binnen de transactie bevestigt de return alleen uitvoering.
            opgeslagen = repo.save(_definitie(save_id, "gewijzigd"))
            assert opgeslagen == save_id if save_id else opgeslagen > 0
            gezien.append(opgeslagen)
            assert repo.hard_delete(id_b) is True
            assert repo._stats["total_saves"] == 0
            assert "Updated definition" not in caplog.text
            assert "Created definition" not in caplog.text

    conn = repo.legacy_repo._db.get_connection()
    conn.set_authorizer(_weiger(sqlite3.SQLITE_TRANSACTION, *geweigerd))
    try:
        with pytest.raises(DefinitionServiceError) as exc:
            genest()
        if "ROLLBACK" not in geweigerd:  # productie-rollback bewijzen vóór opruiming
            assert not conn.in_transaction
            assert _lees(repo, id_a) == "A" and _lees(repo, id_b) == "B"
    finally:
        conn.set_authorizer(None)
        if conn.in_transaction:  # alleen eigen opruiming na rollbackfalen
            conn.execute("ROLLBACK")

    assert isinstance(exc.value.__cause__, sqlite3.Error)
    _assert_veilig(exc.value, tmp_path)
    assert repo._stats["total_saves"] == 0
    assert _lees(repo, id_a) == "A" and _lees(repo, id_b) == "B"
    if via == "create":  # de geneste create bestaat na rollback niet
        assert _lees(repo, gezien[0]) is None
    rollback_logs = [r for r in caplog.records if "ROLLBACK" in r.getMessage()]
    if "ROLLBACK" in geweigerd:
        # De rollbackfout is gelogd, maar de oorzaak blijft de commitfout.
        assert rollback_logs
        assert exc.value.__cause__ is not rollback_logs[0].exc_info[1]
    else:
        assert not rollback_logs and not conn.in_transaction


@pytest.mark.parametrize(
    ("fout", "verwacht"),
    [
        (sqlite3.OperationalError("database is locked"), DatabaseConnectionError),
        (sqlite3.IntegrityError("UNIQUE constraint failed"), DatabaseConstraintError),
        (sqlite3.DatabaseError("not authorized"), RepositoryError),
        (sqlite3.ProgrammingError("Cannot operate on a closed database."), None),
        (RepositoryError("save_update", message="al getypeerd"), None),
        (_VaststellingMisluktError("workflow-signaal", gate_status="stale"), None),
    ],
    ids=["operational", "integrity", "overig", "programmeer", "typed", "workflow"],
)
def test_buitenste_transactie_vertaalt_alleen_ruwe_databasefouten(
    repo, tmp_path, fout, verwacht
):
    """``verwacht=None``: de fout loopt ongewijzigd (identiek object) door."""
    definitie_id = _bestaand(repo)

    def delete_dan_fout() -> None:
        with repo.transaction():
            assert repo.hard_delete(definitie_id) is True
            raise fout

    with pytest.raises(verwacht or type(fout)) as exc:
        delete_dan_fout()

    assert exc.value is fout if verwacht is None else exc.value.__cause__ is fout
    if verwacht is not None:
        _assert_veilig(exc.value, tmp_path)
    assert _lees(repo, definitie_id) == ORIGINEEL
