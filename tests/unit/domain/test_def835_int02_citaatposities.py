"""DEF-835 besluit 9 (optie A): citaatposities worden door de dienst bepaald.

Contract def835-int02-assessment/2. De beoordelaar levert per passage- en
grondcitaat alleen het letterlijke citaat en het veld; de code bepaalt
`start`/`end` deterministisch. Het citaat moet precies één keer als exacte
substring (Python-codepunten, geen normalisatie) in de tekst van het
opgegeven veld voorkomen: dan is `start` die vindplaats en `end` = `start` +
`len(quote)`. Nul keer, meer dan één keer (ook overlappend) of een leeg
citaat is `invalid_citation` met een onderscheidbare `foutdetail`.

Modeluitvoer die toch `start`/`end` bevat, wordt geweigerd als onbekend veld
(`invalid_output`), net als elk ander onbekend veld in het gesloten schema:
ook juiste posities worden niet stil overgenomen of gecorrigeerd.

Het bewaarde oordeel houdt `start`/`end` (door de dienst berekend), zodat
melding, UI en export onveranderd werken; replay leidt ze opnieuw af.

De verwachte posities zijn met de hand uitgeschreven, niet met dezelfde
zoeklogica als de implementatie berekend. Het C112-geval gebruikt alleen de
kern- en bedoelingstekst en de ruwe modeluitvoer uit de v4-regressie
(`kwalificatieproef-v4/regressie-bundel.json`); geen andere goldset- of
hold-outinhoud.

Sinds /4 (besluit 16) gelden deze regels voor de hercontrole van bewaarde
/2- en /3-documenten; de module toetst ze met /3 als actuele versie
(`contract_drie`). De positieregels van /4 staan in
`test_def835_int02_bronfuncties.py`.
"""

from __future__ import annotations

import copy
import dataclasses
import hashlib
import json
import unicodedata

import pytest

from domain.int02 import contract
from domain.int02.contract import (
    _GRONDVELDEN,
    _PASSAGEVELDEN,
    MELDING_E,
    Configuratie,
    Uitvoering,
    beoordeel,
    bereken_binding,
    maak_invoer,
    toets_actualiteit,
)

pytestmark = [pytest.mark.unit]


@pytest.fixture(autouse=True)
def contract_drie(monkeypatch):
    """Besluit 16: de /3-regels met /3 als actuele versie (zie moduledocstring)."""
    monkeypatch.setattr(contract, "CONTRACTVERSIE", "def835-int02-assessment/3")


NORMHASH = hashlib.sha256(b"testnorm def771-int02/2").hexdigest()
ROUTERINGSHASH = hashlib.sha256(b"testroutering").hexdigest()

KERN_DIACRIET = unicodedata.normalize(
    "NFC", "Één café-eigenaar die naïef reçu's bewaart."
)
KERN_ASTRAAL = "Ding 𝔸 met 😀 dat een criterium draagt."

#: Ruwe v4-modeluitvoer voor C112 (regressie-bundel v4, antwoord C112), letterlijk.
#: Het model telde `end` te kort: 71 i.p.v. 73 (kern) en 46 i.p.v. 47 (bedoeling).
C112_KERN = "Verplichting van een partij om de overeengekomen prestatie te verrichten."
C112_BEDOELING = "Synthetische beschrijving van verplichting zelf"
C112_RUW_V4 = (
    '{"verdict":"pass","passages":[{"quote":"Verplichting van een partij om de '
    'overeengekomen prestatie te verrichten.","start":0,"end":71,"function":'
    '"criterion","ground":{"field":"bedoeling","ref":null,"quote":"Synthetische '
    'beschrijving van verplichting zelf","start":0,"end":46}}],"reason":"De kern '
    "beschrijft het begrip 'verplichting' met kenmerken (gebondenheid van een "
    "partij tot de overeengekomen prestatie) en richt zich niet tot een actor als "
    "handelingsvoorschrift of procedure; de bevestigde bedoeling bevestigt dat het "
    "om een beschrijving van het begrip zelf gaat. Het benoemen van een "
    "verplichting tot presteren is een begripskenmerk, geen discretionaire "
    'beslisregel.","question":null,"uncertainty":"none","scope_reason":null,'
    '"coverage":"complete"}'
)


def _configuratie() -> Configuratie:
    return Configuratie(
        normhash=NORMHASH,
        promptversie="def835-int02-prompt/testfixture",
        routeringshash=ROUTERINGSHASH,
        provider="fake-provider",
        model="fake-model-1",
    )


def _uitvoering() -> Uitvoering:
    return Uitvoering(actor="ai", status="completed")


def _invoer(**over) -> dict:
    data = {
        "begrip": "eigenaar",
        "kern": KERN_DIACRIET,
        "bedoeling": "Synthetische bedoeling: een café-eigenaar met reçu's.",
        "organisatorische_context": ["synthetische begrippenstudie"],
        "juridische_context": ["synthetisch privaatrecht"],
        "wettelijke_basis": [],
        "bronnen": [{"id": "B1", "tekst": "Synthetische bron: reçu's zijn bewijs."}],
    }
    data.update(over)
    return data


def _grond(field="kern", ref=None, quote=None) -> dict:
    return {"field": field, "ref": ref, "quote": quote}


def _uitvoer(*passages: dict) -> dict:
    return {
        "verdict": "pass",
        "passages": list(passages),
        "reason": "Synthetische onderbouwing.",
        "question": None,
        "uncertainty": "none",
        "scope_reason": None,
        "coverage": "complete",
    }


def _passage(quote: str, ground: dict | None = None, function="criterion") -> dict:
    return {"quote": quote, "function": function, "ground": ground or _grond()}


def _beoordeel(invoerdata: dict, uitvoer):
    return beoordeel(maak_invoer(**invoerdata), _configuratie(), uitvoer, _uitvoering())


# --- versie en schema ------------------------------------------------------------


def test_contractversie_is_drie_met_de_positieregel_van_twee():
    # /3 (besluit 12) voegt alleen de dienstregel toe; de positieregel van /2 blijft.
    assert contract.CONTRACTVERSIE == "def835-int02-assessment/3"
    binding = bereken_binding(maak_invoer(**_invoer()), _configuratie())
    assert binding.contractversie == "def835-int02-assessment/3"


def test_modelschema_bevat_geen_positievelden_meer():
    assert set(_PASSAGEVELDEN) == {"quote", "function", "ground"}
    assert set(_GRONDVELDEN) == {"field", "ref", "quote"}


# --- uniek citaat: posities door de dienst ----------------------------------------


@pytest.mark.parametrize(
    ("kern", "quote", "start", "end"),
    [
        (KERN_DIACRIET, "Één café-eigenaar", 0, 17),
        (KERN_DIACRIET, "naïef reçu's", 22, 34),
        (KERN_DIACRIET, "reçu's bewaart.", 28, 43),
        (KERN_DIACRIET, KERN_DIACRIET, 0, 43),
        (KERN_ASTRAAL, "dat een criterium draagt.", 13, 38),
    ],
    ids=[
        "begin-van-veld",
        "midden-diacrieten",
        "eind-van-veld",
        "hele-veld",
        "astraal",
    ],
)
def test_uniek_passagecitaat_krijgt_posities_van_de_dienst(kern, quote, start, end):
    uitvoer = _uitvoer(_passage(quote))
    doc = _beoordeel(_invoer(kern=kern), uitvoer)
    assert doc.status == "pass", doc.foutcategorie
    passage = doc.oordeel["passages"][0]
    assert (passage["start"], passage["end"]) == (start, end)
    assert kern[passage["start"] : passage["end"]] == quote


@pytest.mark.parametrize(
    ("grond", "start", "end"),
    [
        (_grond("bedoeling", None, "café-eigenaar"), 28, 41),
        (_grond("bron", "B1", "reçu's zijn bewijs."), 19, 38),
        (_grond("juridische_context", 0, "privaatrecht"), 12, 24),
        (_grond("kern", None, "Één"), 0, 3),
    ],
    ids=["bedoeling", "bron-eind", "context", "kern-begin"],
)
def test_uniek_grondcitaat_krijgt_posities_van_de_dienst(grond, start, end):
    doc = _beoordeel(_invoer(), _uitvoer(_passage("naïef reçu's", grond)))
    assert doc.status == "pass", doc.foutcategorie
    opgeslagen = doc.oordeel["passages"][0]["ground"]
    assert opgeslagen == {**grond, "start": start, "end": end}


def test_grond_zonder_citaat_houdt_lege_posities():
    doc = _beoordeel(_invoer(), _uitvoer(_passage("naïef reçu's", _grond("begrip"))))
    assert doc.status == "pass"
    assert doc.oordeel["passages"][0]["ground"] == {
        "field": "begrip",
        "ref": None,
        "quote": None,
        "start": None,
        "end": None,
    }


def test_meegegeven_modeluitvoer_wordt_niet_gemuteerd():
    uitvoer = _uitvoer(_passage("naïef reçu's", _grond("kern", None, "Één")))
    voor = copy.deepcopy(uitvoer)
    doc = _beoordeel(_invoer(), uitvoer)
    assert doc.status == "pass"
    assert uitvoer == voor


def test_melding_volgt_de_eerste_passage_op_afgeleide_positie():
    later = _passage("reçu's bewaart.")
    eerder = _passage("Één café-eigenaar")
    doc = _beoordeel(_invoer(), _uitvoer(later, eerder))
    assert doc.status == "pass"
    assert "'Één café-eigenaar'" in doc.melding


# --- niet gevonden, niet uniek, leeg ----------------------------------------------


def _citaatfout(doc, detail: str) -> None:
    assert (doc.status, doc.foutcategorie, doc.foutdetail, doc.melding) == (
        "error",
        "invalid_citation",
        detail,
        MELDING_E,
    )
    assert doc.oordeel is None and doc.reden is None


@pytest.mark.parametrize(
    "quote",
    [
        "café eigenaar",  # leesteken anders
        "één café-eigenaar",  # hoofdletter anders
        "naïef  reçu's",  # witruimte anders
        unicodedata.normalize("NFD", "café-eigenaar"),  # andere Unicode-vorm
        "de som van alle bedragen",  # verzonnen
    ],
    ids=["leesteken", "hoofdletter", "witruimte", "nfd", "verzonnen"],
)
def test_passagecitaat_niet_gevonden_is_invalid_citation(quote):
    _citaatfout(_beoordeel(_invoer(), _uitvoer(_passage(quote))), "niet_gevonden")


def test_grondcitaat_niet_gevonden_is_invalid_citation():
    grond = _grond("bron", "B1", "een verzonnen bronzin")
    doc = _beoordeel(_invoer(), _uitvoer(_passage("naïef reçu's", grond)))
    _citaatfout(doc, "niet_gevonden")


def test_passagecitaat_alleen_in_ander_veld_is_niet_gevonden():
    # Staat letterlijk in de bedoeling, niet in de kern: het veld telt.
    doc = _beoordeel(_invoer(), _uitvoer(_passage("Synthetische bedoeling")))
    _citaatfout(doc, "niet_gevonden")


@pytest.mark.parametrize(
    ("kern", "quote"),
    [
        ("Getal dat even is en dat even blijft.", "dat even"),
        ("Een na na na-regel.", "na na"),  # overlappend: posities 4 en 7
    ],
    ids=["tweemaal", "overlappend"],
)
def test_passagecitaat_meer_dan_eens_is_invalid_citation(kern, quote):
    doc = _beoordeel(_invoer(kern=kern), _uitvoer(_passage(quote)))
    _citaatfout(doc, "niet_uniek")


def test_grondcitaat_meer_dan_eens_is_invalid_citation():
    bron = [{"id": "B1", "tekst": "Een reçu is een reçu."}]
    grond = _grond("bron", "B1", "reçu")
    doc = _beoordeel(_invoer(bronnen=bron), _uitvoer(_passage("naïef reçu's", grond)))
    _citaatfout(doc, "niet_uniek")


def test_leeg_passagecitaat_is_invalid_citation():
    _citaatfout(_beoordeel(_invoer(), _uitvoer(_passage(""))), "leeg")


def test_leeg_grondcitaat_is_invalid_citation():
    grond = _grond("kern", None, "")
    doc = _beoordeel(_invoer(), _uitvoer(_passage("naïef reçu's", grond)))
    _citaatfout(doc, "leeg")


def test_niet_herleidbare_grond_heeft_eigen_foutdetail():
    grond = _grond("bron", "B9")
    doc = _beoordeel(_invoer(), _uitvoer(_passage("naïef reçu's", grond)))
    _citaatfout(doc, "grond_niet_herleidbaar")


def test_geldig_oordeel_heeft_geen_foutdetail():
    doc = _beoordeel(_invoer(), _uitvoer(_passage("naïef reçu's")))
    assert doc.status == "pass" and doc.foutdetail is None
    assert doc.als_dict()["foutdetail"] is None


# --- modeluitvoer met posities: geweigerd als onbekend veld -------------------------


@pytest.mark.parametrize(
    "posities",
    [
        {"passage": {"start": 22, "end": 34}},  # juist, toch geweigerd
        {"passage": {"start": 0}},
        {"passage": {"end": 34}},
        {"grond": {"start": None, "end": None}},
        {"grond": {"start": 0, "end": 3}},
    ],
    ids=["passage-juist", "passage-start", "passage-end", "grond-null", "grond-juist"],
)
def test_modeluitvoer_met_positievelden_is_invalid_output(posities):
    passage = _passage("naïef reçu's", _grond("kern", None, "Één"))
    passage.update(posities.get("passage", {}))
    passage["ground"].update(posities.get("grond", {}))
    doc = _beoordeel(_invoer(), _uitvoer(passage))
    assert (doc.status, doc.foutcategorie, doc.foutdetail) == (
        "error",
        "invalid_output",
        None,
    )
    assert doc.oordeel is None


# --- C112-regressie uit kwalificatieproef v4 ----------------------------------------


def _c112_invoer() -> dict:
    return _invoer(
        begrip="verplichting",
        kern=C112_KERN,
        bedoeling=C112_BEDOELING,
        juridische_context=[],
        bronnen=[],
    )


def _zonder_posities(uitvoer: dict) -> dict:
    uitvoer = copy.deepcopy(uitvoer)
    for passage in uitvoer["passages"]:
        del passage["start"], passage["end"]
        del passage["ground"]["start"], passage["ground"]["end"]
    return uitvoer


def test_c112_ruwe_v4_uitvoer_met_te_korte_posities_wordt_geweigerd():
    doc = _beoordeel(_c112_invoer(), json.loads(C112_RUW_V4))
    assert (doc.status, doc.foutcategorie) == ("error", "invalid_output")


def test_c112_ruwe_v4_uitvoer_zonder_posities_is_geldige_pass():
    uitvoer = _zonder_posities(json.loads(C112_RUW_V4))
    doc = _beoordeel(_c112_invoer(), uitvoer)
    assert (doc.status, doc.foutcategorie) == ("pass", None)
    passage = doc.oordeel["passages"][0]
    assert (passage["start"], passage["end"]) == (0, 73)
    assert (passage["ground"]["start"], passage["ground"]["end"]) == (0, 47)
    assert doc.melding == (
        "INT-02 — Voldoet. 'Verplichting van een partij om de overeengekomen "
        "prestatie te verrichten.' beschrijft een criterium; grond: de bevestigde "
        "bedoeling ('Synthetische beschrijving van verplichting zelf'). Andere "
        "toetsregels zijn hiermee niet beoordeeld."
    )


# --- replay leidt de posities opnieuw af -------------------------------------------


def test_replay_aanvaardt_het_document_met_afgeleide_posities():
    invoerdata = _c112_invoer()
    doc = _beoordeel(invoerdata, _zonder_posities(json.loads(C112_RUW_V4)))
    replay = toets_actualiteit(doc, maak_invoer(**invoerdata), _configuratie())
    assert (replay.status, replay.melding) == ("pass", doc.melding)


@pytest.mark.parametrize(
    "pad",
    [("start",), ("end",), ("ground", "start"), ("ground", "end")],
    ids=["start", "end", "grond-start", "grond-end"],
)
def test_replay_weigert_een_gemanipuleerde_bewaarde_positie(pad):
    invoerdata = _c112_invoer()
    doc = _beoordeel(invoerdata, _zonder_posities(json.loads(C112_RUW_V4)))
    oordeel = doc.oordeel
    doel = oordeel["passages"][0]
    for stap in pad[:-1]:
        doel = doel[stap]
    doel[pad[-1]] -= 1
    vervalst = dataclasses.replace(
        doc, oordeel_json=json.dumps(oordeel, ensure_ascii=False, sort_keys=True)
    )
    replay = toets_actualiteit(vervalst, maak_invoer(**invoerdata), _configuratie())
    assert (replay.status, replay.melding) == ("error", MELDING_E)


def test_replay_weigert_een_bewaard_oordeel_zonder_posities():
    invoerdata = _c112_invoer()
    uitvoer = _zonder_posities(json.loads(C112_RUW_V4))
    doc = _beoordeel(invoerdata, uitvoer)
    vervalst = dataclasses.replace(
        doc, oordeel_json=json.dumps(uitvoer, ensure_ascii=False, sort_keys=True)
    )
    replay = toets_actualiteit(vervalst, maak_invoer(**invoerdata), _configuratie())
    assert replay.status == "error"
