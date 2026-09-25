"""DEF-751 B2 — einddelta P1: de weigering van een wissende
`generation_prompt_data`-write moet óók gelden voor beheerde gegevens die
pas ná A's voorcontrole (vóór A's transactie) door B zijn geschreven.

Interleaving (twee repositories, echte tijdelijke SQLite):
1. A leest versie 1 zonder keuze-event en passeert de controle vóór de lock.
2. Vóór A's transactie schrijft B twee expliciete keuzes (versie 3: actueel
   event + één historie-entry), naast prompt en een vreemde sleutel.
3. A schrijft — zonder verwachte versie — `None` / `'not-json'` / `'null'` /
   `'[]'` plus een ander veld.

Vereist: A wordt binnen de transactie, op het vers gelezen record, geweigerd
(ValueError); niets is geschreven (ook het andere veld niet): versie 3,
event, staat, historie, prompt, vreemde sleutel, categorie en CON-02-historie
blijven exact; readback via een nieuwe repository.
"""

from __future__ import annotations

import json
import sqlite3

import pytest

from database.definitie_crud import DefinitieCrudRepository
from database.definitie_repository import DefinitieRecord, DefinitieRepository
from database.models import (
    CATEGORY_CHOICE_HISTORY_KEY,
    CATEGORY_CHOICE_KEY,
    CATEGORY_CHOICE_STATE_KEY,
    SOURCE_REVIEW_HISTORY_KEY,
)

pytestmark = [pytest.mark.unit]


@pytest.fixture
def db_path(tmp_path) -> str:
    return str(tmp_path / "race.db")


def _record(db_path: str) -> int:
    did = DefinitieRepository(db_path).create_definitie(
        DefinitieRecord(
            begrip="keurmerk",
            definitie="kern",
            categorie="type",
            organisatorische_context=json.dumps(["DJI"]),
            generation_prompt_data=json.dumps(
                {"prompt": "p", SOURCE_REVIEW_HISTORY_KEY: [{"x": 1}], "vreemd": True}
            ),
        )
    )
    # DEF-770: sinds INT-01 draagt elk nieuw record een beheerde deeluitkomst.
    # Deze interleaving vereist een record zónder beheerde gegevens bij A's
    # voorcontrole: een record van vóór DEF-770 (registratie zonder INT-01).
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE definities SET generation_prompt_data = ? WHERE id = ?",
            (
                json.dumps(
                    {
                        "prompt": "p",
                        SOURCE_REVIEW_HISTORY_KEY: [{"x": 1}],
                        "vreemd": True,
                    }
                ),
                did,
            ),
        )
    return did


def _b_schrijft_twee_keuzes(db_path: str, did: int) -> None:
    repo_b = DefinitieRepository(db_path)
    for waarde in ("proces", "resultaat"):
        versie = repo_b.get_definitie(did).version_number
        assert repo_b.record_category_choice(
            did,
            {},
            waarde=waarde,
            herkomst="editor",
            actor="B",
            actor_source="typed_name",
            updated_by="B",
            expected_version=versie,
        )
    na_b = repo_b.get_definitie(did)
    assert na_b.version_number == 3
    assert len(na_b.get_category_choice_history()) == 1


@pytest.mark.parametrize("ruw", [None, "not-json", "null", "[]"])
def test_b_schrijft_tussen_voorcontrole_en_transactie_van_a(db_path, monkeypatch, ruw):
    did = _record(db_path)
    repo_a = DefinitieRepository(db_path)
    origineel = DefinitieCrudRepository._weiger_wissende_registratie
    aanroepen: list[int] = []

    def _voorcontrole_dan_b(actueel, velden):
        # De bestaande controle zelf; daarna — alleen bij de eerste aanroep,
        # dus vóór A's transactie — de gelijktijdige writes van B.
        origineel(actueel, velden)
        aanroepen.append(actueel.version_number)
        if len(aanroepen) == 1:
            _b_schrijft_twee_keuzes(db_path, did)

    monkeypatch.setattr(
        DefinitieCrudRepository,
        "_weiger_wissende_registratie",
        staticmethod(_voorcontrole_dan_b),
    )

    with pytest.raises(ValueError, match="beheerde"):
        repo_a.update_definitie(
            did, {"generation_prompt_data": ruw, "toelichting_proces": "van A"}, "A"
        )

    # A's voorcontrole zag versie 1 (geen beheerde gegevens); de herhaling
    # binnen de transactie zag B's versie 3 en weigerde.
    assert aanroepen[0] == 1

    na = DefinitieRepository(db_path).get_definitie(did)
    assert na.version_number == 3
    assert na.toelichting_proces is None  # geen gedeeltelijke write
    assert na.categorie == "resultaat"
    registratie = na.get_generatieregistratie()
    assert registratie[CATEGORY_CHOICE_KEY]["value"] == "resultaat"
    assert registratie[CATEGORY_CHOICE_KEY]["actor"] == "B"
    assert registratie[CATEGORY_CHOICE_STATE_KEY]["current"] is True
    assert len(registratie[CATEGORY_CHOICE_HISTORY_KEY]) == 1
    assert registratie[SOURCE_REVIEW_HISTORY_KEY] == [{"x": 1}]
    assert registratie["prompt"] == "p" and registratie["vreemd"] is True
    assert na.get_category_choice_status()["status"] == "manual_confirmed"
