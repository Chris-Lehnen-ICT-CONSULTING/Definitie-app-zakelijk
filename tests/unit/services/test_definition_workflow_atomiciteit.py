"""Atomiciteit van de vaststelling (DEF-482).

`DefinitionWorkflowService.approve()` is de kleinste unit-of-work van de
kwaliteitsketen: status, approval-metadata, ketenpartners, UFO-categorie en
de app-auditrij committen samen of helemaal niet. Deze tests draaien op een
tijdelijke file-backed database met de echte repository-facades; alleen de
gate wordt gestubd (die is DEF-611-terrein).

Audit-assertions tellen uitsluitend app-rijen (`wijziging_reden IS NOT NULL`):
een verse database uit schema.sql heeft een trigger die productie mist en die
per UPDATE een extra rij zonder reden schrijft (zie DEF-664).
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any
from unittest.mock import Mock

import pytest

from database.definitie_repository import (
    UNSET,
    DefinitieRecord,
    DefinitieStatus,
)
from services.definition_repository import DefinitionRepository
from services.definition_workflow_service import (
    DefinitionWorkflowService,
    ufo_categorie_uit_selectie,
)
from services.workflow_service import WorkflowService

pytestmark = [pytest.mark.unit]

GATE_PASS = {"status": "pass", "reasons": []}


def _service(tmp_path) -> tuple[DefinitionWorkflowService, DefinitionRepository]:
    repo = DefinitionRepository(str(tmp_path / "atomiciteit.db"))
    svc = DefinitionWorkflowService(workflow_service=WorkflowService(), repository=repo)
    svc._evaluate_gate = lambda _definition: dict(GATE_PASS)
    return svc, repo


def _review_definitie(repo: DefinitionRepository, ufo: str | None = None) -> int:
    return repo.legacy_repo.create_definitie(
        DefinitieRecord(
            begrip="atomiciteit_begrip",
            definitie="Definitie in review",
            categorie="proces",
            organisatorische_context='["ORG"]',
            status=DefinitieStatus.REVIEW.value,
            ufo_categorie=ufo,
        )
    )


def _rij(repo: DefinitionRepository, definitie_id: int) -> dict[str, Any]:
    conn = repo.legacy_repo._db.get_connection()
    row = conn.execute(
        "SELECT status, approved_by, approval_notes, ketenpartners, ufo_categorie,"
        " version_number FROM definities WHERE id = ?",
        (definitie_id,),
    ).fetchone()
    return dict(row)


def _audit_rijen(
    repo: DefinitionRepository, definitie_id: int, soort: str, *, alleen_app: bool
) -> int:
    """Tel geschiedenisrijen; ``alleen_app`` filtert de DEF-664-triggerrij weg."""
    conn = repo.legacy_repo._db.get_connection()
    filter_app = " AND wijziging_reden IS NOT NULL" if alleen_app else ""
    return conn.execute(
        "SELECT COUNT(*) FROM definitie_geschiedenis WHERE definitie_id = ?"
        f" AND wijziging_type = ?{filter_app}",
        (definitie_id, soort),
    ).fetchone()[0]


def _app_audit(repo: DefinitionRepository, definitie_id: int, soort: str) -> int:
    return _audit_rijen(repo, definitie_id, soort, alleen_app=True)


def _approve(svc, repo, definitie_id, *args, expected_version=None, **kwargs):
    """Roep approve() aan zoals de UI: met de versie uit het getoonde snapshot."""
    if expected_version is None:
        expected_version = _rij(repo, definitie_id)["version_number"]
    return svc.approve(definitie_id, *args, expected_version=expected_version, **kwargs)


def _assert_onveranderd(repo, definitie_id, voor):
    assert _rij(repo, definitie_id) == voor
    # Negatief: géén enkele status_changed-rij, ook niet een met lege reden.
    assert _audit_rijen(repo, definitie_id, "status_changed", alleen_app=False) == 0


TRANSACTIEGRENZEN = ("BEGIN", "COMMIT", "ROLLBACK", "SAVEPOINT", "RELEASE")


# --- T1a: alleen exact de beoordeelde versie mag worden vastgesteld ----------


def test_approve_weigert_definitie_die_na_de_gate_is_gewijzigd(tmp_path):
    svc, repo = _service(tmp_path)
    definitie_id = _review_definitie(repo)

    def gate_met_concurrente_wijziging(_definition):
        # Een andere sessie wijzigt de tekst tussen gate en UPDATE.
        assert repo.legacy_repo.update_definitie(
            definitie_id, {"definitie": "intussen gewijzigd"}, updated_by="ander"
        )
        return dict(GATE_PASS)

    svc._evaluate_gate = gate_met_concurrente_wijziging
    voor = _rij(repo, definitie_id)  # nog vóór de concurrente wijziging
    statements: list[str] = []
    conn = repo.legacy_repo._db.get_connection()
    conn.set_trace_callback(statements.append)
    try:
        result = _approve(svc, repo, definitie_id, "reviewer", user_role="reviewer")
    finally:
        conn.set_trace_callback(None)

    assert result.success is False
    assert result.gate_status == "stale"
    assert result.gate_reasons == []
    # Het stale-pad leest binnen de transactie; die read mag de transactie niet
    # committen (kale connectie), dus precies één BEGIN gevolgd door één ROLLBACK.
    grenzen = [s for s in statements if s.upper().startswith(TRANSACTIEGRENZEN)]
    assert grenzen[-2:] == ["BEGIN IMMEDIATE", "ROLLBACK"], grenzen
    na = _rij(repo, definitie_id)
    assert na["status"] == "review"
    assert na["approved_by"] is None
    assert na["version_number"] == voor["version_number"] + 1  # alleen de ander
    assert _audit_rijen(repo, definitie_id, "status_changed", alleen_app=False) == 0


# --- T1c: de UI-snapshot is ouder dan de database (reproductie Chris) --------


def test_approve_weigert_verouderd_ui_snapshot_zonder_gate_of_write(tmp_path):
    """Reviewer zag v1, een ander schreef v2: v2 mag niet als v3 worden vastgesteld."""
    svc, repo = _service(tmp_path)
    definitie_id = _review_definitie(repo)
    snapshot = _rij(repo, definitie_id)  # wat de reviewer op het scherm had
    assert repo.legacy_repo.update_definitie(
        definitie_id, {"definitie": "door een ander gewijzigd"}, updated_by="ander"
    )
    na_ander = _rij(repo, definitie_id)

    def gate_mag_niet_draaien(_definition):
        pytest.fail("de gate mag een verouderd snapshot niet beoordelen")

    svc._evaluate_gate = gate_mag_niet_draaien
    statements: list[str] = []
    conn = repo.legacy_repo._db.get_connection()
    conn.set_trace_callback(statements.append)
    try:
        result = _approve(
            svc,
            repo,
            definitie_id,
            "reviewer",
            user_role="reviewer",
            expected_version=snapshot["version_number"],
        )
    finally:
        conn.set_trace_callback(None)

    assert result.success is False
    assert result.gate_status == "stale"
    assert "intussen gewijzigd" in (result.error_message or "")
    assert [s for s in statements if s.upper().startswith(TRANSACTIEGRENZEN)] == []
    assert _rij(repo, definitie_id) == na_ander
    assert _audit_rijen(repo, definitie_id, "status_changed", alleen_app=False) == 0


# --- T1b: falende gecombineerde UPDATE rolt alles terug ---------------------


def test_approve_rolt_status_terug_als_ketenpartners_niet_opgeslagen_kan_worden(
    tmp_path, monkeypatch
):
    svc, repo = _service(tmp_path)
    definitie_id = _review_definitie(repo)
    voor = _rij(repo, definitie_id)
    crud = repo.legacy_repo._crud
    origineel = crud.update_definitie

    def faalt_op_ketenpartners(definitie_id_, updates, *args, **kwargs):
        if "ketenpartners" in updates:
            raise sqlite3.OperationalError("ketenpartners-kolom niet beschikbaar")
        return origineel(definitie_id_, updates, *args, **kwargs)

    monkeypatch.setattr(crud, "update_definitie", faalt_op_ketenpartners)

    result = _approve(
        svc,
        repo,
        definitie_id,
        "reviewer",
        ketenpartners=["Partner A"],
        user_role="reviewer",
    )

    assert result.success is False
    assert not hasattr(result, "warning")
    _assert_onveranderd(repo, definitie_id, voor)


# --- T2: falende app-audit rolt de gecombineerde UPDATE terug ---------------


def test_approve_rolt_terug_als_audit_faalt(tmp_path, monkeypatch, caplog):
    svc, repo = _service(tmp_path)
    definitie_id = _review_definitie(repo)
    voor = _rij(repo, definitie_id)

    def audit_faalt(*_args, **_kwargs):
        raise sqlite3.OperationalError("audit faalt")

    monkeypatch.setattr(repo.legacy_repo._audit, "log_geschiedenis", audit_faalt)

    result = _approve(
        svc,
        repo,
        definitie_id,
        "reviewer",
        ketenpartners=["Partner A"],
        user_role="reviewer",
    )

    assert result.success is False
    # Een repositoryfout is géén versieconflict: de herlezing binnen de open
    # transactie ziet de eigen, nog niet gecommitte versiebump en mag daaruit
    # geen "stale" afleiden (gereproduceerd door Chris, 4 september 2026).
    assert result.gate_status is None
    assert "intussen gewijzigd" not in (result.error_message or "")
    # DEF-469: de servicegrens vertaalt de ruwe SQLite-fout naar een vaste,
    # veilige melding; de oorzaak blijft alleen via exception chaining/log.
    from services.definition_repository import MELDING_DATABASEFOUT

    assert result.error_message == MELDING_DATABASEFOUT
    assert "audit faalt" not in result.error_message
    diagnose = [
        r for r in caplog.records if getattr(r, "operation", None) == "transaction"
    ]
    assert len(diagnose) == 1
    assert diagnose[0].error_type == "OperationalError"
    assert diagnose[0].sqlite_errorcode is None  # handmatig gemaakte fout
    assert diagnose[0].origin == "audit_faalt"
    assert diagnose[0].exc_info is None
    assert "audit faalt" not in caplog.text
    _assert_onveranderd(repo, definitie_id, voor)


def test_facade_slikt_geen_fout_binnen_een_open_transactie(tmp_path):
    """Binnen een transactie maskeert `False` een deelresultaat; dan moet de
    passthrough de fout doorgeven. Buiten een transactie blijft `False` (DEF-469)."""
    _svc, repo = _service(tmp_path)
    definitie_id = _review_definitie(repo)

    def gooit(*_args, **_kwargs):
        raise sqlite3.OperationalError("repository kapot")

    repo.legacy_repo.change_status = gooit  # type: ignore[method-assign]

    assert repo.change_status(definitie_id, DefinitieStatus.ESTABLISHED) is False
    with repo.transaction(), pytest.raises(sqlite3.OperationalError):
        repo.change_status(definitie_id, DefinitieStatus.ESTABLISHED)


# --- T3/T3b: succespad = één UPDATE, één versiebump, één auditrij -----------


def test_approve_schrijft_alles_in_een_versiebump(tmp_path):
    svc, repo = _service(tmp_path)
    definitie_id = _review_definitie(repo, ufo="Kind")
    voor = _rij(repo, definitie_id)

    result = _approve(
        svc,
        repo,
        definitie_id,
        "reviewer",
        notes="akkoord",
        ketenpartners=["Partner A", "Partner B"],
        ufo_categorie="Event",
        user_role="reviewer",
    )

    assert result.success is True, result.error_message
    assert result.new_status == DefinitieStatus.ESTABLISHED.value
    na = _rij(repo, definitie_id)
    assert na["status"] == "established"
    assert na["approved_by"] == "reviewer"
    assert na["approval_notes"] == "akkoord"
    assert json.loads(na["ketenpartners"]) == ["Partner A", "Partner B"]
    assert na["ufo_categorie"] == "Event"
    assert na["version_number"] == voor["version_number"] + 1
    assert _app_audit(repo, definitie_id, "status_changed") == 1
    assert result.events == []  # geen event bus geconfigureerd


@pytest.mark.parametrize(
    ("ufo_argument", "verwacht"),
    [
        pytest.param({"ufo_categorie": ""}, None, id="leeg-maakt-null"),
        pytest.param({"ufo_categorie": None}, None, id="none-maakt-null"),
        pytest.param({}, "Kind", id="weggelaten-laat-staan"),
        pytest.param({"ufo_categorie": UNSET}, "Kind", id="unset-laat-staan"),
    ],
)
def test_approve_ufo_sentinel(tmp_path, ufo_argument, verwacht):
    svc, repo = _service(tmp_path)
    definitie_id = _review_definitie(repo, ufo="Kind")

    result = _approve(
        svc, repo, definitie_id, "reviewer", user_role="reviewer", **ufo_argument
    )

    assert result.success is True, result.error_message
    assert _rij(repo, definitie_id)["ufo_categorie"] == verwacht


# --- T4a/T5: approve() is eigenaar van precies één transactie ---------------


def test_approve_doet_precies_een_begin_en_een_commit(tmp_path):
    svc, repo = _service(tmp_path)
    definitie_id = _review_definitie(repo)
    statements: list[str] = []
    conn = repo.legacy_repo._db.get_connection()
    conn.set_trace_callback(statements.append)
    try:
        result = _approve(
            svc,
            repo,
            definitie_id,
            "reviewer",
            ketenpartners=["Partner A"],
            user_role="reviewer",
        )
    finally:
        conn.set_trace_callback(None)

    assert result.success is True, result.error_message
    grenzen = [s for s in statements if s.upper().startswith(TRANSACTIEGRENZEN)]
    assert grenzen == ["BEGIN IMMEDIATE", "COMMIT"], grenzen


# --- T4b: een al open transactie wordt geweigerd, niet gejoind --------------


def test_approve_weigert_binnen_een_open_transactie(tmp_path):
    svc, repo = _service(tmp_path)
    definitie_id = _review_definitie(repo)
    voor = _rij(repo, definitie_id)

    with repo.transaction() as conn:
        result = _approve(svc, repo, definitie_id, "reviewer", user_role="reviewer")
        assert result.success is False
        assert "al een transactie actief" in (result.error_message or "")
        assert (
            conn.in_transaction
        ), "approve() mag de transactie van de aanroeper niet sluiten"

    _assert_onveranderd(repo, definitie_id, voor)


# --- T9: bijeffecten ná de commit veranderen het resultaat niet -------------


@pytest.mark.parametrize("bijeffect", ["event_bus", "audit_logger"])
def test_fout_in_bijeffect_na_commit_maakt_vaststelling_niet_ongedaan(
    tmp_path, bijeffect
):
    svc, repo = _service(tmp_path)
    definitie_id = _review_definitie(repo)
    kapot = Mock()
    kapot.publish.side_effect = RuntimeError("event bus down")
    kapot.log_transition.side_effect = RuntimeError("audit sink down")
    setattr(svc, bijeffect, kapot)

    result = _approve(svc, repo, definitie_id, "reviewer", user_role="reviewer")

    assert result.success is True, result.error_message
    assert _rij(repo, definitie_id)["status"] == "established"
    # Het bijeffect is wél geprobeerd; alleen het resultaat blijft succes.
    if bijeffect == "event_bus":
        kapot.publish.assert_called_once()
        assert result.events == []  # niet gepubliceerd, dus niet gerapporteerd
    else:
        kapot.log_transition.assert_called_once()


# --- niet-stale faalroute: UPDATE raakt nul rijen zonder versieconflict ------


def test_approve_meldt_generieke_fout_als_update_niets_raakt(tmp_path, monkeypatch):
    svc, repo = _service(tmp_path)
    definitie_id = _review_definitie(repo)
    voor = _rij(repo, definitie_id)
    monkeypatch.setattr(
        repo.legacy_repo._crud, "update_definitie", lambda *a, **k: False
    )

    result = _approve(svc, repo, definitie_id, "reviewer", user_role="reviewer")

    assert result.success is False
    assert result.gate_status is None
    assert result.gate_reasons is None
    assert result.error_message == "Status update mislukt in repository"
    _assert_onveranderd(repo, definitie_id, voor)


# --- herlezing na rowcount 0 mag een databasefout niet als stale melden ------


def test_databasefout_bij_stale_herlezing_is_geen_versieconflict(tmp_path, monkeypatch):
    svc, repo = _service(tmp_path)
    definitie_id = _review_definitie(repo)
    voor = _rij(repo, definitie_id)
    monkeypatch.setattr(
        repo.legacy_repo._crud, "update_definitie", lambda *a, **k: False
    )
    origineel = repo.legacy_repo.get_definitie
    aanroepen = {"n": 0}

    def faalt_bij_herlezing(definitie_id_):
        aanroepen["n"] += 1
        if aanroepen["n"] > 1:
            raise sqlite3.OperationalError("database is locked")
        return origineel(definitie_id_)

    monkeypatch.setattr(repo.legacy_repo, "get_definitie", faalt_bij_herlezing)

    result = _approve(svc, repo, definitie_id, "reviewer", user_role="reviewer")

    assert result.success is False
    assert result.gate_status is None
    from services.definition_repository import MELDING_DATABASEFOUT

    assert result.error_message == MELDING_DATABASEFOUT  # DEF-469: geen ruwe tekst
    _assert_onveranderd(repo, definitie_id, voor)


# --- UI-selectie naar contract ------------------------------------------------


@pytest.mark.parametrize(
    ("selectie", "verwacht"),
    [
        pytest.param(None, UNSET, id="geen-keuze-laat-staan"),
        pytest.param("", "", id="leeg-maakt-leeg"),
        pytest.param("Kind", "Kind", id="waarde-wordt-gezet"),
    ],
)
def test_ufo_categorie_uit_selectie(selectie, verwacht):
    assert ufo_categorie_uit_selectie(selectie) is verwacht or (
        ufo_categorie_uit_selectie(selectie) == verwacht
    )
