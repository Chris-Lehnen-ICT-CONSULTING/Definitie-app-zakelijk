"""DEF-751 B2 — het categorieherkomstcontract (puur domein).

Eén onveranderlijk keuze-event: gekozen waarde, herkomst, actor waar echt
bekend, tijd en de kandidaat waarvoor de keuze gold (term + drie contexten,
bij generatie ook de gegenereerde tekst). De status wordt bij lezen afgeleid
uit het event en de actuele recordstaat — er schuift niets mee.
"""

from __future__ import annotations

import pytest

from domain.categorie_herkomst import (
    BINDING_GENERATIEKANDIDAAT,
    BINDING_TERM_CONTEXT,
    CATEGORY_CHOICE_SCHEMA,
    HERKOMST_DEFAULT,
    HERKOMST_EDITOR,
    HERKOMST_HANDMATIG,
    HERKOMST_IMPORT,
    HERKOMST_MODEL,
    bepaal_keuzestatus,
    bereken_kandidaatvingerafdruk,
    bereken_tekstvingerafdruk,
    bouw_categoriekeuze,
    lees_keuze_invoer,
)
from domain.ontological_categories import OPSLAGCATEGORIEEN

pytestmark = [pytest.mark.unit]

CONTEXTEN = {
    "organisatorische_context": ["DJI"],
    "juridische_context": ["Strafrecht"],
    "wettelijke_basis": ["Pbw"],
}


def test_opslagcategorieen_zijn_de_elf_schemawaarden():
    assert OPSLAGCATEGORIEEN == (
        "type",
        "proces",
        "resultaat",
        "exemplaar",
        "ENT",
        "ACT",
        "REL",
        "ATT",
        "AUT",
        "STA",
        "OTH",
    )


def test_kandidaatvingerafdruk_is_ongevoelig_voor_volgorde_en_witruimte():
    a = bereken_kandidaatvingerafdruk("Keurmerk", CONTEXTEN)
    b = bereken_kandidaatvingerafdruk(
        " keurmerk ",
        {**CONTEXTEN, "organisatorische_context": ["dji", " DJI "]},
    )
    assert a == b
    assert a != bereken_kandidaatvingerafdruk(
        "Keurmerk", {**CONTEXTEN, "wettelijke_basis": []}
    )
    assert bereken_tekstvingerafdruk("x") != bereken_tekstvingerafdruk("y")


def test_event_is_volledig_en_zonder_meeschuivende_versie():
    event = bouw_categoriekeuze(
        waarde="type",
        herkomst=HERKOMST_HANDMATIG,
        begrip="keurmerk",
        contexten=CONTEXTEN,
        actor=None,
        recorded_at="2026-09-17T08:00:00+00:00",
        record_version=3,
        definitie_tekst="Een keurmerk is …",
        generation_id="gen-1",
    )
    assert event["schema"] == CATEGORY_CHOICE_SCHEMA
    assert event["value"] == "type" and event["origin"] == HERKOMST_HANDMATIG
    assert event["actor"] is None and event["actor_source"] is None
    assert event["recorded_at"] == "2026-09-17T08:00:00+00:00"
    assert event["record_version_at_write"] == 3  # informatief, nooit bijgewerkt
    assert event["candidate"]["begrip"] == "keurmerk"
    assert event["candidate"]["fingerprint"] == bereken_kandidaatvingerafdruk(
        "keurmerk", CONTEXTEN
    )
    assert event["binding"] == BINDING_GENERATIEKANDIDAAT
    assert event["generation_id"] == "gen-1"
    assert event["text_fingerprint"] == bereken_tekstvingerafdruk("Een keurmerk is …")
    assert "version_number" not in event


def test_actor_alleen_bij_menselijke_herkomst_en_altijd_als_opgegeven_naam():
    event = bouw_categoriekeuze(
        waarde="proces",
        herkomst=HERKOMST_EDITOR,
        begrip="k",
        contexten=CONTEXTEN,
        actor="Reviewer Rood",
        actor_source="typed_name",
    )
    assert event["actor"] == "Reviewer Rood" and event["actor_source"] == "typed_name"
    assert event["binding"] == BINDING_TERM_CONTEXT
    for herkomst in (HERKOMST_MODEL, HERKOMST_IMPORT, HERKOMST_DEFAULT):
        with pytest.raises(ValueError, match="actor"):
            bouw_categoriekeuze(
                waarde="type",
                herkomst=herkomst,
                begrip="k",
                contexten=CONTEXTEN,
                actor="Iemand",
            )
    with pytest.raises(ValueError, match="actor_source"):
        bouw_categoriekeuze(
            waarde="type",
            herkomst=HERKOMST_HANDMATIG,
            begrip="k",
            contexten=CONTEXTEN,
            actor="Iemand",
            actor_source="authenticated",
        )


@pytest.mark.parametrize("waarde", ["Type", "entiteit", "", "proces "])
def test_ongeldige_waarde_wordt_geweigerd_niet_genormaliseerd(waarde):
    with pytest.raises(ValueError, match="opslagwaarde"):
        bouw_categoriekeuze(
            waarde=waarde, herkomst=HERKOMST_IMPORT, begrip="k", contexten=CONTEXTEN
        )


def test_onbekende_herkomst_wordt_geweigerd():
    with pytest.raises(ValueError, match="herkomst"):
        bouw_categoriekeuze(
            waarde="type", herkomst="bevestigd", begrip="k", contexten=CONTEXTEN
        )


def test_lees_keuze_invoer_neemt_alleen_getypeerde_velden_en_nooit_een_actor():
    """De grens voor publiek aangeleverde invoer (options/metadata/payload):
    alleen herkomst manual/model + reasoning/scores; een meegestuurde actor,
    tijd of status wordt genegeerd; editor/import/default zijn hier ongeldig."""
    invoer = lees_keuze_invoer(
        {
            "origin": "manual",
            "actor": "Henk",
            "actor_source": "session_user",
            "recorded_at": "2020-01-01",
            "status": "manual_confirmed",
            "reasoning": "r",
            "scores": {"type": 0.9},
        }
    )
    assert invoer == {"origin": "manual", "reasoning": "r", "scores": {"type": 0.9}}
    assert lees_keuze_invoer(None) is None
    assert lees_keuze_invoer({"reasoning": "x"}) is None
    for verboden in ("editor", "import", "default", "bevestigd"):
        with pytest.raises(ValueError, match="herkomst"):
            lees_keuze_invoer({"origin": verboden})


def _event(**over):
    basis = {
        "waarde": "type",
        "herkomst": HERKOMST_HANDMATIG,
        "begrip": "keurmerk",
        "contexten": CONTEXTEN,
        "actor": "Reviewer Rood",
        "actor_source": "typed_name",
        "definitie_tekst": "Tekst A",
        "generation_id": "gen-1",
    }
    basis.update(over)
    return bouw_categoriekeuze(**basis)


def _status(event, **over):
    staat = {
        "categorie": "type",
        "begrip": "keurmerk",
        "contexten": CONTEXTEN,
        "definitie_tekst": "Tekst A",
    }
    staat.update(over)
    return bepaal_keuzestatus(event, **staat)


def test_status_zes_gevallen():
    assert _status(None)["status"] == "unknown_origin"
    assert _status(None, categorie=None)["status"] == "absent"
    assert _status(_event())["status"] == "manual_confirmed"
    assert (
        _status(_event(actor=None, actor_source=None))["status"]
        == "manual_unattributed"
    )
    assert (
        _status(_event(herkomst=HERKOMST_MODEL, actor=None, actor_source=None))[
            "status"
        ]
        == "model_suggestion"
    )
    assert (
        _status(_event(herkomst=HERKOMST_IMPORT, actor=None, actor_source=None))[
            "status"
        ]
        == "imported"
    )
    assert (
        _status(
            _event(
                herkomst=HERKOMST_IMPORT, actor=None, actor_source=None, waarde=None
            ),
            categorie=None,
        )["status"]
        == "imported_missing"
    )
    assert (
        _status(_event(herkomst=HERKOMST_DEFAULT, actor=None, actor_source=None))[
            "status"
        ]
        == "default"
    )
    assert _status({"schema": "anders"})["status"] == "invalid"


def test_status_wordt_stale_bij_term_context_of_waardewijziging_niet_bij_tekst():
    event = _event()
    assert _status(event, begrip="ander begrip")["status"] == "stale"
    assert (
        _status(event, contexten={**CONTEXTEN, "wettelijke_basis": []})["status"]
        == "stale"
    )
    assert _status(event, categorie="proces")["status"] == "stale"
    # Tekstwijziging: keuze blijft actueel, maar de generatiekandidaat is
    # niet meer de tekst waarvoor zij gold — zichtbaar, geen herbevestiging.
    na_tekst = _status(event, definitie_tekst="Tekst B")
    assert na_tekst["status"] == "manual_confirmed"
    assert na_tekst["binding"] == BINDING_GENERATIEKANDIDAAT
    assert na_tekst["text_unchanged"] is False
    assert _status(event)["text_unchanged"] is True
    stale = _status(event, begrip="ander begrip")
    assert stale["underlying"] == "manual_confirmed"
    assert "term" in stale["reason"].lower() or "context" in stale["reason"].lower()
