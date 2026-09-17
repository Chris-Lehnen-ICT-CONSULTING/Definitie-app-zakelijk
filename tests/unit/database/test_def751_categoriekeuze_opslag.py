"""DEF-751 B2 — categoriekeuze opslaan, teruglezen en verouderen (DB-laag).

Echte tijdelijke SQLite via `DefinitieRepository`; readback altijd via een
nieuwe repository-instantie. De keuze reist als structurele sleutel
`category_choice` in `update_definitie` mee (zelfde patroon als
`source_evidence`), landt in de bestaande generatieregistratie en raakt de
CON-01-/CON-02-markers niet.
"""

from __future__ import annotations

import json

import pytest

from database.definitie_repository import DefinitieRecord, DefinitieRepository
from database.models import (
    CATEGORY_CHOICE_HISTORY_KEY,
    CATEGORY_CHOICE_KEY,
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


def test_editorkeuze_met_opgegeven_naam_overleeft_nieuwe_repository(db_path):
    did = _record(db_path)
    ok = _repo(db_path).update_definitie(
        did,
        {
            "categorie": "proces",
            "category_choice": {
                "origin": "editor",
                "actor": "Reviewer Rood",
                "actor_source": "typed_name",
            },
        },
        "Reviewer Rood",
    )
    assert ok is True

    record = _repo(db_path).get_definitie(did)
    assert record.categorie == "proces"
    keuze = record.get_category_choice()
    assert keuze["schema"] == CATEGORY_CHOICE_SCHEMA
    assert keuze["value"] == "proces" and keuze["origin"] == "editor"
    assert keuze["actor"] == "Reviewer Rood" and keuze["actor_source"] == "typed_name"
    assert keuze["recorded_at"] and keuze["record_version_at_write"] == 1
    assert keuze["candidate"]["begrip"] == "keurmerk"
    assert keuze["candidate"]["organisatorische_context"] == ["DJI"]
    status = record.get_category_choice_status()
    assert status["status"] == "manual_confirmed"
    assert "niet geverifieerd" in status["reason"]
    assert record.get_category_choice_history() == []


def test_zonder_actor_blijft_de_keuze_ongeattribueerd(db_path):
    did = _record(db_path)
    assert _repo(db_path).update_definitie(
        did, {"categorie": "proces", "category_choice": {"origin": "editor"}}, "system"
    )
    record = _repo(db_path).get_definitie(did)
    assert record.get_category_choice()["actor"] is None
    assert record.get_category_choice_status()["status"] == "manual_unattributed"


def test_actor_die_afwijkt_van_de_handelende_gebruiker_wordt_voor_mutatie_geweigerd(
    db_path,
):
    did = _record(db_path)
    with pytest.raises(ValueError, match="handelende gebruiker"):
        _repo(db_path).update_definitie(
            did,
            {
                "categorie": "proces",
                "category_choice": {
                    "origin": "editor",
                    "actor": "Iemand Anders",
                    "actor_source": "typed_name",
                },
            },
            "Reviewer Rood",
        )
    record = _repo(db_path).get_definitie(did)
    assert record.categorie == "type" and record.version_number == 1
    assert record.get_category_choice() is None


@pytest.mark.parametrize("herkomst", ["manual", "model", "import", "default"])
def test_alleen_de_editorroute_mag_via_update_een_keuze_schrijven(db_path, herkomst):
    """`update_definitie` is de opslagroute van de editor/toepassen-actie;
    model-, import- en default-events ontstaan alleen waar die code zelf loopt."""
    did = _record(db_path)
    if herkomst == "manual":
        assert _repo(db_path).update_definitie(
            did, {"categorie": "proces", "category_choice": {"origin": herkomst}}, None
        )
        return
    with pytest.raises(ValueError, match="herkomst"):
        _repo(db_path).update_definitie(
            did, {"categorie": "proces", "category_choice": {"origin": herkomst}}, None
        )


def test_keuze_zonder_categoriekolom_of_met_afwijkende_waarde_wordt_geweigerd(db_path):
    did = _record(db_path)
    with pytest.raises(ValueError, match="categorie"):
        _repo(db_path).update_definitie(
            did, {"category_choice": {"origin": "editor"}}, None
        )
    with pytest.raises(ValueError, match="opslagwaarde"):
        _repo(db_path).update_definitie(
            did, {"categorie": "Type", "category_choice": {"origin": "editor"}}, None
        )
    assert _repo(db_path).get_definitie(did).version_number == 1


def test_versieconflict_schrijft_niets(db_path):
    did = _record(db_path)
    ok = _repo(db_path).update_definitie(
        did,
        {
            "categorie": "proces",
            "category_choice": {"origin": "editor"},
            "version_number": 7,
        },
        None,
    )
    assert ok is False
    record = _repo(db_path).get_definitie(did)
    assert record.categorie == "type" and record.get_category_choice() is None


def test_nieuwe_keuze_verplaatst_de_vorige_onveranderd_naar_de_historie(db_path):
    did = _record(db_path)
    repo = _repo(db_path)
    assert repo.update_definitie(
        did,
        {
            "categorie": "proces",
            "category_choice": {
                "origin": "editor",
                "actor": "A",
                "actor_source": "typed_name",
            },
        },
        "A",
    )
    eerste = _repo(db_path).get_definitie(did).get_category_choice()
    assert repo.update_definitie(
        did, {"categorie": "resultaat", "category_choice": {"origin": "editor"}}, None
    )
    record = _repo(db_path).get_definitie(did)
    assert record.get_category_choice()["value"] == "resultaat"
    historie = record.get_category_choice_history()
    assert len(historie) == 1
    assert historie[0]["event"] == eerste  # exact, niets bijgewerkt
    assert historie[0]["superseded_on_version"] == 2
    assert historie[0]["superseded_at"]


def test_term_of_contextwijziging_maakt_de_keuze_stale_tekst_niet(db_path):
    did = _record(db_path)
    repo = _repo(db_path)
    assert repo.update_definitie(
        did, {"categorie": "proces", "category_choice": {"origin": "editor"}}, None
    )
    assert repo.update_definitie(did, {"definitie": "Andere tekst."}, None)
    na_tekst = _repo(db_path).get_definitie(did)
    assert na_tekst.get_category_choice_status()["status"] == "manual_unattributed"
    assert na_tekst.get_category_choice()["value"] == "proces"

    assert repo.update_definitie(did, {"begrip": "ander begrip"}, None)
    na_term = _repo(db_path).get_definitie(did)
    status = na_term.get_category_choice_status()
    assert status["status"] == "stale" and status["underlying"] == "manual_unattributed"
    # Het event zelf is niet herschreven.
    assert na_term.get_category_choice()["candidate"]["begrip"] == "keurmerk"


def test_categoriekolom_zonder_event_herschrijven_maakt_geen_keuze_actueel(db_path):
    did = _record(db_path)
    repo = _repo(db_path)
    assert repo.update_definitie(
        did, {"categorie": "proces", "category_choice": {"origin": "editor"}}, None
    )
    # Kolom terug naar 'type' zonder keuze-event (bv. een oude route).
    assert repo.update_definitie(did, {"categorie": "type"}, None)
    record = _repo(db_path).get_definitie(did)
    status = record.get_category_choice_status()
    assert status["status"] == "stale"
    assert "wijkt af" in status["reason"]
    # En terug naar 'proces' zonder event maakt het oude event niet opnieuw
    # bevestigd: de kolom klopt weer, maar de keuze bleef ongewijzigd en
    # de historie meldt niets — precies wat er gebeurde.
    assert repo.update_definitie(did, {"categorie": "proces"}, None)
    record = _repo(db_path).get_definitie(did)
    assert record.get_category_choice_status()["status"] == "manual_unattributed"
    assert record.get_category_choice()["record_version_at_write"] == 1


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
    assert repo.update_definitie(
        did, {"categorie": "proces", "category_choice": {"origin": "editor"}}, None
    )
    registratie = _repo(db_path).get_definitie(did).get_generatieregistratie()
    assert registratie["prompt"] == "p" and registratie["vreemd"] is True
    assert registratie[SOURCE_REVIEW_HISTORY_KEY] == [{"x": 1}]
    assert registratie[CATEGORY_CHOICE_KEY]["value"] == "proces"
    assert registratie[CATEGORY_CHOICE_HISTORY_KEY] == []
