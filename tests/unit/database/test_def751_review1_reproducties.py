"""DEF-751 B2 — reproducties van de Codex-review op commit 1 (bevindingen 1/2/3/5).

Elke test reproduceert eerst het gerapporteerde defect op de echte
tmp-SQLite-keten en legt daarna het vereiste gedrag vast; readback altijd
via een nieuwe repository-instantie.

1. Een verouderde keuze mag niet herleven door term/context/categorie terug
   te zetten: de invalidatie wordt binnen dezelfde transactie blijvend
   vastgelegd; alleen een nieuwe bewuste keuze herstelt de actualiteit.
2. Import (JSON-bestand met een `manual_confirmed`-event), ruwe
   `generation_prompt_data` en `Definition.metadata` kunnen geen menselijke
   herkomst fabriceren: een toegeschreven keuze ontstaat uitsluitend via het
   expliciete servicecommando `record_category_choice`; aangeleverde events
   blijven als onbevestigde invoer bewaard maar worden nooit als bevestigd
   gelezen of getoond.
3. Toepassen- en editorroute dragen de versie van de getoonde kandidaat tot
   de uiteindelijke UPDATE: een gelijktijdige wijziging tussen voorcontrole
   en schrijven is een conflict — geen oude term terugschrijven, geen keuze
   op een ongeziene term.
5. Een tekstwijziging na een editor-/toepassen-keuze is zichtbaar in de
   keuzestatus (tekstbasis voor álle keuzes; geen historische herbevestiging).
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any
from unittest.mock import patch

import pytest

from database.definitie_repository import DefinitieRecord, DefinitieRepository
from database.models import CATEGORY_CHOICE_KEY
from services.category_service import CategoryService
from services.definition_edit_repository import DefinitionEditRepository
from services.definition_edit_service import DefinitionEditService
from services.definition_repository import DefinitionRepository
from services.interfaces import Definition
from ui.helpers.categorie_weergave import beschrijf_keuzestatus

pytestmark = [pytest.mark.unit]

ORG = json.dumps(["DJI"])
JUR = json.dumps(["Strafrecht"])
WET = json.dumps(["Pbw"])


@pytest.fixture
def db_path(tmp_path) -> str:
    return str(tmp_path / "review1.db")


def _repo(db_path: str) -> DefinitieRepository:
    return DefinitieRepository(db_path)


def _record(db_path: str, categorie: str = "type", **extra: Any) -> int:
    return _repo(db_path).create_definitie(
        DefinitieRecord(
            begrip="keurmerk",
            definitie="Een synthetische definitie.",
            categorie=categorie,
            organisatorische_context=ORG,
            juridische_context=JUR,
            wettelijke_basis=WET,
            created_by="seed",
            **extra,
        )
    )


def _keuze(db_path: str, did: int, waarde: str, actor: str | None = None) -> bool:
    """Het expliciete servicecommando: de editor-/toepassen-actie."""
    record = _repo(db_path).get_definitie(did)
    return _repo(db_path).record_category_choice(
        did,
        {},
        waarde=waarde,
        herkomst="editor",
        actor=actor,
        actor_source="typed_name" if actor else None,
        updated_by=actor,
        expected_version=record.version_number,
    )


def _status(db_path: str, did: int) -> dict[str, Any]:
    return _repo(db_path).get_definitie(did).get_category_choice_status()


# ---------------------------------------------------------------- bevinding 1


@pytest.mark.parametrize(
    ("wijziging", "herstel"),
    [
        ({"begrip": "vergunning"}, {"begrip": "keurmerk"}),
        ({"wettelijke_basis": "[]"}, {"wettelijke_basis": WET}),
        ({"categorie": "proces"}, {"categorie": "type"}),
    ],
    ids=["term", "context", "categorie"],
)
def test_verouderde_keuze_herleeft_niet_door_terugzetten(db_path, wijziging, herstel):
    did = _record(db_path)
    assert _keuze(db_path, did, "type", actor="Reviewer Rood")
    assert _status(db_path, did)["status"] == "manual_confirmed"

    assert _repo(db_path).update_definitie(did, wijziging, None)
    assert _status(db_path, did)["status"] == "stale"

    assert _repo(db_path).update_definitie(did, herstel, None)
    status = _status(db_path, did)
    assert status["status"] == "stale", "verouderde keuze herleefde door terugzetten"
    assert status["underlying"] == "manual_confirmed"
    assert "versie" in status["reason"]
    # Het event zelf is onveranderd bewaard.
    keuze = _repo(db_path).get_definitie(did).get_category_choice()
    assert keuze["actor"] == "Reviewer Rood" and keuze["value"] == "type"

    # Alleen een nieuwe bewuste keuze herstelt de actualiteit.
    assert _keuze(db_path, did, "type", actor="Reviewer Rood")
    assert _status(db_path, did)["status"] == "manual_confirmed"
    assert len(_repo(db_path).get_definitie(did).get_category_choice_history()) == 1


def test_invalidatie_landt_in_dezelfde_transactie_als_de_wijziging(db_path):
    did = _record(db_path)
    assert _keuze(db_path, did, "type")
    repo = _repo(db_path)
    # Een fout ná de UPDATE (audit) rolt ook de invalidatie terug.
    with (
        patch.object(
            repo._crud._audit,
            "log_geschiedenis",
            side_effect=sqlite3.OperationalError("x"),
        ),
        pytest.raises(sqlite3.OperationalError),
    ):
        repo.update_definitie(did, {"begrip": "vergunning"}, None)
    record = _repo(db_path).get_definitie(did)
    assert record.begrip == "keurmerk" and record.version_number == 2
    assert record.get_category_choice_status()["status"] == "manual_unattributed"


# ---------------------------------------------------------------- bevinding 2


def _vervalst_event() -> dict[str, Any]:
    return {
        "schema": "def751-categoriekeuze/1",
        "value": "type",
        "origin": "editor",
        "actor": "Vervalste Naam",
        "actor_source": "typed_name",
        "recorded_at": "2000-01-01T00:00:00+00:00",
        "record_version_at_write": 1,
        "candidate": {
            "begrip": "keurmerk",
            "organisatorische_context": ["DJI"],
            "juridische_context": ["Strafrecht"],
            "wettelijke_basis": ["Pbw"],
            "fingerprint": "sha256:vervalst",
        },
        "binding": "term_context",
        "generation_id": None,
        "text_fingerprint": None,
        "reasoning": None,
        "scores": None,
    }


def _geen_bevestiging(record: DefinitieRecord) -> None:
    keuze = record.get_category_choice()
    status = record.get_category_choice_status()
    assert keuze is None or keuze.get("actor") is None
    assert status["status"] != "manual_confirmed"
    tekst = beschrijf_keuzestatus(status, keuze)
    assert "Vervalste Naam" not in tekst and "2000-01-01" not in tekst
    assert "handmatig gekozen door" not in tekst


def test_json_import_met_manual_confirmed_event_wordt_niet_als_bevestigd_gelezen(
    db_path, tmp_path
):
    bestand = tmp_path / "import.json"
    bestand.write_text(
        json.dumps(
            {
                "definities": [
                    {
                        "begrip": "keurmerk",
                        "definitie": "kern",
                        "categorie": "type",
                        "organisatorische_context": ORG,
                        "generation_prompt_data": json.dumps(
                            {
                                "prompt": "p",
                                CATEGORY_CHOICE_KEY: _vervalst_event(),
                                "category_choice_state": {"current": True},
                            }
                        ),
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    assert _repo(db_path).import_from_json(str(bestand), "importeur") == (1, 0, [])
    record = _repo(db_path).search_definities(query="keurmerk")[0]
    assert record.source_type == "imported"
    _geen_bevestiging(record)
    status = record.get_category_choice_status()
    assert status["status"] == "imported"
    # De aangeleverde inhoud is als onbevestigde invoer bewaard, niet weg.
    registratie = record.get_generatieregistratie()
    assert registratie["prompt"] == "p"
    assert registratie["category_choice_imported"]["actor"] == "Vervalste Naam"


def test_ruwe_generation_prompt_data_update_kan_geen_keuze_fabriceren(db_path):
    did = _record(db_path)
    assert _repo(db_path).update_definitie(
        did,
        {
            "generation_prompt_data": json.dumps(
                {"prompt": "p", CATEGORY_CHOICE_KEY: _vervalst_event()}
            )
        },
        "Vervalste Naam",
    )
    record = _repo(db_path).get_definitie(did)
    _geen_bevestiging(record)
    assert record.get_category_choice_status()["status"] == "unknown_origin"
    assert record.get_generatieregistratie()["prompt"] == "p"


def test_metadata_en_updates_kunnen_geen_toegeschreven_keuze_maken(db_path):
    """Generieke metadata (create én update) en het generieke `updates`-dict
    dragen geen menselijke bevestiging; alleen het commando doet dat.
    (De proef uit de review: create met `manual`, daarna een update met
    ingevulde actor/`updated_by` leverde een toegeschreven editorkeuze op.)"""
    repo = DefinitionRepository(db_path)

    def _definitie(invoer: dict[str, Any]) -> Definition:
        return Definition(
            begrip="keurmerk",
            definitie="kern",
            categorie="type",
            organisatorische_context=["DJI"],
            metadata={"status": "draft", "category_choice_input": invoer},
        )

    # Een menselijke herkomst kan niet via metadata worden aangeleverd.
    with pytest.raises(Exception, match="herkomst"):
        repo.save(
            _definitie(
                {
                    "origin": "editor",
                    "actor": "Vervalste Naam",
                    "actor_source": "typed_name",
                }
            )
        )
    did = repo.save(
        _definitie(
            {
                "origin": "manual",
                "actor": "Vervalste Naam",
                "actor_source": "typed_name",
            }
        )
    )
    record = _repo(db_path).get_definitie(did)
    _geen_bevestiging(record)
    assert record.get_category_choice_status()["status"] == "manual_unattributed"

    geladen = DefinitionRepository(db_path).get(did)
    geladen.categorie = "proces"
    geladen.metadata["category_choice_input"] = {
        "origin": "editor",
        "actor": "Vervalste Naam",
        "actor_source": "typed_name",
    }
    geladen.metadata["updated_by"] = "Vervalste Naam"
    repo.update(did, geladen)
    _geen_bevestiging(_repo(db_path).get_definitie(did))

    with pytest.raises(ValueError, match="record_category_choice"):
        _repo(db_path).update_definitie(
            did,
            {
                "categorie": "type",
                "category_choice": {
                    "origin": "editor",
                    "actor": "Vervalste Naam",
                    "actor_source": "typed_name",
                },
            },
            "Vervalste Naam",
        )
    _geen_bevestiging(_repo(db_path).get_definitie(did))


def test_commando_legt_toegeschreven_keuze_vast_en_overleeft_nieuwe_repository(
    db_path,
):
    did = _record(db_path)
    assert _keuze(db_path, did, "proces", actor="Reviewer Rood")
    record = _repo(db_path).get_definitie(did)
    assert record.categorie == "proces"
    keuze = record.get_category_choice()
    assert keuze["actor"] == "Reviewer Rood" and keuze["origin"] == "editor"
    assert record.get_category_choice_status()["status"] == "manual_confirmed"
    assert "Reviewer Rood" in beschrijf_keuzestatus(
        record.get_category_choice_status(), keuze
    )


# ---------------------------------------------------------------- bevinding 3


def _concurrent(db_path: str, did: int, updates: dict[str, Any]) -> None:
    assert DefinitieRepository(db_path).update_definitie(did, updates, "ander")


def test_toepassen_route_weigert_bij_gelijktijdige_wijziging(db_path):
    did = _record(db_path)
    db = _repo(db_path)
    origineel = db.get_definitie

    def _lees_en_wijzig_concurrent(definitie_id: int):
        record = origineel(definitie_id)
        _concurrent(db_path, did, {"begrip": "vergunning"})
        return record

    with patch.object(db, "get_definitie", side_effect=_lees_en_wijzig_concurrent):
        resultaat = CategoryService(db).update_category_v2(
            did, "proces", user=None, expected_version=1
        )
    assert resultaat.success is False
    na = _repo(db_path).get_definitie(did)
    assert na.begrip == "vergunning" and na.categorie == "type"
    assert na.get_category_choice() is None


def test_editor_route_weigert_bij_gelijktijdige_wijziging(db_path):
    edit_repo = DefinitionEditRepository(db_path)
    did = edit_repo.save(
        Definition(
            begrip="keurmerk",
            definitie="kern",
            categorie="type",
            organisatorische_context=["DJI"],
            juridische_context=["Strafrecht"],
            wettelijke_basis=["Pbw"],
            metadata={"status": "draft"},
        )
    )
    service = DefinitionEditService(repository=edit_repo, validation_service=None)
    origineel = edit_repo.check_version_conflict

    def _na_voorcontrole_concurrent(definitie_id: int, version_number: int) -> bool:
        conflict = origineel(definitie_id, version_number)
        _concurrent(db_path, did, {"begrip": "vergunning"})
        return conflict

    with patch.object(
        edit_repo, "check_version_conflict", side_effect=_na_voorcontrole_concurrent
    ):
        resultaat = service.save_definition(
            did,
            {
                "begrip": "keurmerk",
                "definitie": "Nieuwe tekst.",
                "categorie": "proces",
                "version_number": 1,
            },
            user="system",
            validate=False,
            categoriekeuze={"herkomst": "editor", "actor": None},
        )
    assert resultaat["success"] is False
    na = _repo(db_path).get_definitie(did)
    assert na.begrip == "vergunning", "oude term werd teruggeschreven"
    assert na.categorie == "type" and na.get_definitie_tekst() == "kern"
    assert na.get_category_choice() is None


# ---------------------------------------------------------------- bevinding 5


def test_tekstwijziging_na_editorkeuze_is_zichtbaar_en_herleeft_niet(db_path):
    did = _record(db_path)
    assert _keuze(db_path, did, "type", actor="Reviewer Rood")
    assert _status(db_path, did)["text_unchanged"] is True

    assert _repo(db_path).update_definitie(
        did, {"definitie": "Volledig andere bedoeling."}, "Reviewer Rood"
    )
    record = _repo(db_path).get_definitie(did)
    status = record.get_category_choice_status()
    assert status["status"] == "manual_confirmed"
    assert status["text_unchanged"] is False
    caption = beschrijf_keuzestatus(status, record.get_category_choice())
    assert "tekst" in caption.lower() and "gewijzigd" in caption.lower()
    assert "versie 3" in caption  # v1 aanmaak, v2 keuze, v3 tekstwijziging
    assert "bevestigt de huidige tekst niet" in caption

    # Tekst terugzetten maakt de keuze niet opnieuw tekstgebonden.
    assert _repo(db_path).update_definitie(
        did, {"definitie": "Een synthetische definitie."}, "Reviewer Rood"
    )
    assert _status(db_path, did)["text_unchanged"] is False
