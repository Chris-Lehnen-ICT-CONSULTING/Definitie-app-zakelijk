"""DEF-751 B2 — categoriekeuze opslaan, teruglezen en verouderen (DB-laag).

Echte tijdelijke SQLite via `DefinitieRepository`; readback altijd via een
nieuwe repository-instantie. Een menselijke keuze loopt uitsluitend via het
expliciete commando `record_category_choice` (editor-opslaan/toepassen), in
één UPDATE met de kolom, met verplichte versieguard; het event landt in de
bestaande generatieregistratie en raakt de CON-01-/CON-02-markers niet.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from database.definitie_repository import DefinitieRecord, DefinitieRepository
from database.models import (
    CATEGORY_CHOICE_HISTORY_KEY,
    CATEGORY_CHOICE_KEY,
    CATEGORY_CHOICE_STATE_KEY,
    SOURCE_REVIEW_HISTORY_KEY,
)
from domain.categorie_herkomst import CATEGORY_CHOICE_SCHEMA

pytestmark = [pytest.mark.unit]

ORG = json.dumps(["DJI"])
JUR = json.dumps(["Strafrecht"])


@pytest.fixture
def db_path(tmp_path) -> str:
    return str(tmp_path / "keuze.db")


def _repo(db_path: str) -> DefinitieRepository:
    return DefinitieRepository(db_path)


def _record(db_path: str, categorie: str = "type") -> int:
    return _repo(db_path).create_definitie(
        DefinitieRecord(
            begrip="keurmerk",
            definitie="Een synthetische definitie.",
            categorie=categorie,
            organisatorische_context=ORG,
            juridische_context=JUR,
            wettelijke_basis=json.dumps(["Pbw"]),
            created_by="seed",
        )
    )


def _keuze(
    db_path: str,
    did: int,
    waarde: str | None,
    *,
    actor: str | None = None,
    actor_source: str | None = None,
    updated_by: str | None = None,
    herkomst: str = "editor",
    expected_version: int | None = None,
    updates: dict[str, Any] | None = None,
) -> bool:
    versie = (
        expected_version
        if expected_version is not None
        else _repo(db_path).get_definitie(did).version_number
    )
    return _repo(db_path).record_category_choice(
        did,
        updates or {},
        waarde=waarde,
        herkomst=herkomst,
        actor=actor,
        actor_source=actor_source or ("typed_name" if actor else None),
        updated_by=updated_by if updated_by is not None else actor,
        expected_version=versie,
    )


def test_editorkeuze_met_opgegeven_naam_overleeft_nieuwe_repository(db_path):
    did = _record(db_path)
    assert _keuze(db_path, did, "proces", actor="Reviewer Rood") is True

    record = _repo(db_path).get_definitie(did)
    assert record.categorie == "proces" and record.version_number == 2
    keuze = record.get_category_choice()
    assert keuze["schema"] == CATEGORY_CHOICE_SCHEMA
    assert keuze["value"] == "proces" and keuze["origin"] == "editor"
    assert keuze["actor"] == "Reviewer Rood" and keuze["actor_source"] == "typed_name"
    assert keuze["recorded_at"] and keuze["record_version_at_write"] == 1
    assert keuze["candidate"]["begrip"] == "keurmerk"
    assert keuze["candidate"]["organisatorische_context"] == ["DJI"]
    assert isinstance(keuze["text_fingerprint"], str)  # tekstbasis ook bij editor
    staat = record.get_category_choice_state()
    assert staat["current"] is True and staat["text_changed"] is False
    status = record.get_category_choice_status()
    assert status["status"] == "manual_confirmed"
    assert "niet geverifieerd" in status["reason"]
    assert record.get_category_choice_history() == []


def test_zonder_actor_blijft_de_keuze_ongeattribueerd(db_path):
    did = _record(db_path)
    assert _keuze(db_path, did, "proces", updated_by="system")
    record = _repo(db_path).get_definitie(did)
    assert record.get_category_choice()["actor"] is None
    assert record.get_category_choice_status()["status"] == "manual_unattributed"


def test_actor_die_afwijkt_van_de_handelende_gebruiker_wordt_voor_mutatie_geweigerd(
    db_path,
):
    did = _record(db_path)
    with pytest.raises(ValueError, match="handelende gebruiker"):
        _keuze(
            db_path, did, "proces", actor="Iemand Anders", updated_by="Reviewer Rood"
        )
    record = _repo(db_path).get_definitie(did)
    assert record.categorie == "type" and record.version_number == 1
    assert record.get_category_choice() is None


@pytest.mark.parametrize("herkomst", ["model", "import", "default", "bevestigd"])
def test_commando_accepteert_alleen_menselijke_herkomst(db_path, herkomst):
    did = _record(db_path)
    with pytest.raises(ValueError, match="herkomst"):
        _keuze(db_path, did, "proces", herkomst=herkomst)
    assert _repo(db_path).get_definitie(did).version_number == 1


def test_generiek_updates_dict_kan_geen_keuze_dragen(db_path):
    did = _record(db_path)
    with pytest.raises(ValueError, match="record_category_choice"):
        _repo(db_path).update_definitie(
            did, {"categorie": "proces", "category_choice": {"origin": "editor"}}, None
        )
    assert _repo(db_path).get_definitie(did).version_number == 1


def test_ongeldige_waarde_wordt_geweigerd_niet_omgezet(db_path):
    did = _record(db_path)
    with pytest.raises(ValueError, match="opslagwaarde"):
        _keuze(db_path, did, "Type")
    assert _repo(db_path).get_definitie(did).version_number == 1


def test_versieconflict_schrijft_niets(db_path):
    did = _record(db_path)
    assert _keuze(db_path, did, "proces", expected_version=7) is False
    record = _repo(db_path).get_definitie(did)
    assert record.categorie == "type" and record.get_category_choice() is None


def test_versie_is_verplicht(db_path):
    did = _record(db_path)
    with pytest.raises(ValueError, match="expected_version"):
        _repo(db_path).record_category_choice(
            did,
            {},
            waarde="proces",
            herkomst="editor",
            actor=None,
            actor_source=None,
            updated_by=None,
            expected_version=None,  # type: ignore[arg-type]
        )


def test_nieuwe_keuze_verplaatst_de_vorige_onveranderd_naar_de_historie(db_path):
    did = _record(db_path)
    assert _keuze(db_path, did, "proces", actor="A")
    eerste = _repo(db_path).get_definitie(did).get_category_choice()
    assert _keuze(db_path, did, "resultaat")
    record = _repo(db_path).get_definitie(did)
    assert record.get_category_choice()["value"] == "resultaat"
    historie = record.get_category_choice_history()
    assert len(historie) == 1
    assert historie[0]["event"] == eerste  # exact, niets bijgewerkt
    assert historie[0]["state"]["current"] is True
    assert historie[0]["superseded_on_version"] == 2
    assert historie[0]["superseded_at"]


def test_term_of_contextwijziging_maakt_de_keuze_blijvend_stale_tekst_niet(db_path):
    did = _record(db_path)
    repo = _repo(db_path)
    assert _keuze(db_path, did, "proces")
    assert repo.update_definitie(did, {"definitie": "Andere tekst."}, None)
    na_tekst = _repo(db_path).get_definitie(did)
    status = na_tekst.get_category_choice_status()
    assert status["status"] == "manual_unattributed"
    assert status["text_unchanged"] is False and status["text_changed_on_version"] == 3

    assert repo.update_definitie(did, {"begrip": "ander begrip"}, None)
    na_term = _repo(db_path).get_definitie(did)
    status = na_term.get_category_choice_status()
    assert status["status"] == "stale" and status["underlying"] == "manual_unattributed"
    assert status["invalidated_on_version"] == 4
    # Het event zelf is niet herschreven; de staat wél (persistent).
    assert na_term.get_category_choice()["candidate"]["begrip"] == "keurmerk"
    assert na_term.get_category_choice_state()["current"] is False


def test_editor_opslaan_zonder_wijziging_van_identiteit_raakt_de_keuze_niet(db_path):
    """Een opslaan-actie schrijft alle velden opnieuw; gelijke waarden zijn
    geen wijziging (ook niet in een andere contextvolgorde/schrijfwijze)."""
    did = _record(db_path)
    assert _keuze(db_path, did, "proces")
    assert _repo(db_path).update_definitie(
        did,
        {
            "begrip": "keurmerk",
            "organisatorische_context": json.dumps(["dji"]),
            "juridische_context": JUR,
            "wettelijke_basis": json.dumps(["Pbw"]),
            "categorie": "proces",
            "definitie": "Een synthetische definitie.",
            "toelichting_proces": "extra",
        },
        None,
    )
    record = _repo(db_path).get_definitie(did)
    status = record.get_category_choice_status()
    assert status["status"] == "manual_unattributed"
    assert status["text_unchanged"] is True


def test_legacyrecord_zonder_event_is_unknown_origin(db_path):
    did = _record(db_path, "ENT")
    record = _repo(db_path).get_definitie(did)
    assert record.get_category_choice() is None
    status = record.get_category_choice_status()
    assert status["status"] == "unknown_origin" and "ENT" in status["reason"]


def test_keuze_laat_con02_historie_en_vreemde_sleutels_staan(db_path):
    did = _record(db_path)
    repo = _repo(db_path)
    assert repo.update_definitie(
        did,
        {
            "generation_prompt_data": json.dumps(
                {"prompt": "p", SOURCE_REVIEW_HISTORY_KEY: [{"x": 1}], "vreemd": True}
            )
        },
        None,
    )
    assert _keuze(db_path, did, "proces", updates={"toelichting_proces": "n"})
    registratie = _repo(db_path).get_definitie(did).get_generatieregistratie()
    assert registratie["prompt"] == "p" and registratie["vreemd"] is True
    assert registratie[SOURCE_REVIEW_HISTORY_KEY] == [{"x": 1}]
    assert registratie[CATEGORY_CHOICE_KEY]["value"] == "proces"
    assert registratie[CATEGORY_CHOICE_HISTORY_KEY] == []
    assert registratie[CATEGORY_CHOICE_STATE_KEY]["current"] is True
    # De overige updates landden in dezelfde UPDATE.
    assert _repo(db_path).get_definitie(did).toelichting_proces == "n"
