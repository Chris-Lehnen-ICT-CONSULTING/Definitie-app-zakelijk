"""DEF-821 — de aftakking 'ontbrekende betekenisgrond' in de echte orchestrator.

Een geldige melding is een specifieke non-success (`success=False`) zonder
definitie, id of oordeel; voorbeelden, opschoning, validatie, opslag en
mislukte-poging-registratie draaien niet. De melding staat compleet in de
metadata voor transport naar de UI. Een gemengde of misvormde melding faalt
veilig (`modelantwoord_ongeldig`) zonder modeltekst in response of log. Er is
geen bronverificatie nodig: de melding noemt juist wat níét is aangeleverd.

Offline doubles (zelfde `Keten` als DEF-751); niets hier claimt modelkwaliteit.
"""

from __future__ import annotations

import json

import pytest

from services.modelantwoord import CONFLICT_SENTINEL, ONTBREKENDE_GROND_SENTINEL
from tests.unit.services.orchestrators.test_def751_betekenisconflict_keten import (
    DEFINITIE,
    LEZINGEN,
    Keten,
    _request,
)

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]

GROND = "de dagconventie: werkdagen of kalenderdagen"
VRAAG = "Tellen de drie dagen als werkdagen of als kalenderdagen?"


def melding(payload: dict | None = None) -> str:
    data = {"ontbrekende_grond": GROND, "vraag": VRAAG} if payload is None else payload
    return f"{ONTBREKENDE_GROND_SENTINEL} " + json.dumps(data, ensure_ascii=False)


async def test_ontbrekende_grond_is_specifieke_non_success_zonder_downstream(
    monkeypatch, caplog
):
    keten = Keten(monkeypatch, melding(), bron_nrs=())
    with caplog.at_level("INFO"):
        response = await keten.run()

    assert response.success is False
    assert response.definition is None
    assert response.validation_result is None
    md = response.metadata
    assert md["error_type"] == "betekenisgrond_ontbreekt"
    assert md["phases_completed"] == 4
    assert "betekenisconflict" not in md
    melding_md = md["betekenisgrond_ontbreekt"]
    assert melding_md["ontbrekende_grond"] == GROND
    assert melding_md["vraag"] == VRAAG
    assert melding_md["gemeld_door"] == "model"
    assert melding_md["begrip"] == "registratie"
    assert melding_md["ontologische_categorie"] == "proces"
    assert melding_md["organisatorische_context"] == ["DJI"]
    assert melding_md["juridische_context"] == ["Strafrecht"]
    assert melding_md["wettelijke_basis"] == []
    assert melding_md["generation_id"] == "11111111-2222-3333-4444-555555555555"
    assert VRAAG in (response.error or "")
    # Geen oordeel, geen categoriebevestiging, geen id.
    assert "category_choice" not in json.dumps(md)
    assert "saved_definition_id" not in md
    keten.geen_downstream()
    keten.monitoring.complete_generation.assert_awaited_once()
    assert keten.monitoring.complete_generation.await_args.kwargs["success"] is False
    # Geen modelinhoud in het log.
    assert VRAAG not in caplog.text and GROND not in caplog.text


@pytest.mark.parametrize(
    ("modeltekst", "code"),
    [
        (DEFINITIE + "\n" + melding(), "sentinel_niet_eerst"),
        (melding() + "\n" + DEFINITIE, "tekst_na_payload"),
        (
            melding()
            + "\n"
            + f"{CONFLICT_SENTINEL} "
            + json.dumps({"vraag": "v", "lezingen": LEZINGEN}),
            "gemengde_melding",
        ),
        (melding({"ontbrekende_grond": GROND}), "vraag_ontbreekt"),
        (
            melding({"ontbrekende_grond": GROND, "vraag": VRAAG, "x": 1}),
            "onbekende_sleutel",
        ),
        (f"**{ONTBREKENDE_GROND_SENTINEL}** {{}}", "payload_geen_json"),
    ],
)
async def test_gemengde_of_misvormde_melding_faalt_veilig(
    monkeypatch, modeltekst, code, caplog
):
    keten = Keten(monkeypatch, modeltekst)
    with caplog.at_level("INFO"):
        response = await keten.run()
    assert response.success is False and response.definition is None
    assert response.metadata["error_type"] == "modelantwoord_ongeldig"
    assert response.metadata["code"] == code
    assert "betekenisgrond_ontbreekt" not in response.metadata
    for tekst in (DEFINITIE, VRAAG, GROND):
        assert tekst not in json.dumps(response.metadata)
        assert tekst not in (response.error or "")
        assert tekst not in caplog.text
    keten.geen_downstream()


async def test_conflictroute_blijft_ongewijzigd_naast_de_nieuwe_uitkomst(monkeypatch):
    conflict = f"{CONFLICT_SENTINEL} " + json.dumps(
        {"vraag": "v?", "lezingen": LEZINGEN}, ensure_ascii=False
    )
    keten = Keten(monkeypatch, conflict)
    response = await keten.run()
    assert response.metadata["error_type"] == "betekenisconflict"
    assert "betekenisgrond_ontbreekt" not in response.metadata
    keten.geen_downstream()


async def test_gewone_definitie_loopt_ongewijzigd_door(monkeypatch):
    keten = Keten(monkeypatch, DEFINITIE)
    response = await keten.run()
    assert response.success is True
    assert response.definition is not None and response.definition.id == 42
    assert keten.cleaning.clean_text.await_args.args[0] == DEFINITIE
    assert "betekenisgrond_ontbreekt" not in response.metadata
