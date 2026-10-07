"""DEF-835 reviewcorrectie (Codex, 07-10-2026): bewaarde /1-documenten na /2.

Een geldig document onder contract def835-int02-assessment/1 (posities door
de beoordelaar) moet na de overgang naar /2 `review_required` / `historical`
worden en niet `error`. De integriteitscontrole volgt daarom de *originele*
contractversie van het document; pas daarna komt de bestaande historische
bindingstoets. De manipulatiecontrole blijft even streng: een gewijzigd /1-
of /2-document en een onbekende contractversie geven `error`.

De /1-documenten komen uit `tests/fixtures/def835_int02_contract_v1_documenten.json`.
Die zijn gemaakt met de /1-contractcode die letterlijk uit git is geladen
(`scripts/analysis/def835_int02_v1_referentiedocumenten.py`, revisie
3ba526dae, contract-SHA-256 6dcae57b…), dus niet met de code onder test.

Sinds /3 (besluit 12, review Codex 07-10-2026): het /2-document is het in
kwalificatieproef v5 door de echte /2-code bewaarde C107-document
(`kwalificatieproef-v5/regressie-resultaat.json`), ook niet gemaakt met de
code onder test. Documenten via de actuele `beoordeel` zijn /3 en heten hier
"actueel".
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from domain.int02.contract import (
    CONTRACTVERSIE,
    MELDING_E,
    MELDING_HISTORISCH,
    Beoordelingsdocument,
    Binding,
    Configuratie,
    Uitvoering,
    beoordeel,
    maak_invoer,
    toets_actualiteit,
)

pytestmark = [pytest.mark.unit]

ROOT = Path(__file__).resolve().parents[3]
REFERENTIE = json.loads(
    (ROOT / "tests/fixtures/def835_int02_contract_v1_documenten.json").read_text(
        "utf-8"
    )
)
V1 = "def835-int02-assessment/1"
V2 = "def835-int02-assessment/2"
IDS = [d["id"] for d in REFERENTIE["documenten"]]
V5_RESULTAAT = (
    ROOT / "docs/analyses/def606-regeldossiers/INT-02-verdieping/"
    "onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/"
    "goldset-freeze-v1/kwalificatieproef-v5/regressie-resultaat.json"
)


def _configuratie() -> Configuratie:
    return Configuratie(**REFERENTIE["configuratie"])


def _uit_dict(item: dict) -> Beoordelingsdocument:
    """Een bewaard /1-document terug als object (geen `foutdetail` onder /1)."""
    data = item["document"]
    return Beoordelingsdocument(
        contractversie=data["contractversie"],
        invoer=maak_invoer(**data["invoer"]),
        binding=Binding(**data["binding"]),
        uitvoering=Uitvoering(**data["uitvoering"]),
        status=data["status"],
        reden=data["reden"],
        melding=data["melding"],
        vraag=data["vraag"],
        foutcategorie=data["foutcategorie"],
        oordeel_json=item["oordeel_json"],
    )


def _item(geval_id: str) -> dict:
    return next(d for d in REFERENTIE["documenten"] if d["id"] == geval_id)


def _actualiteit(document: Beoordelingsdocument, item: dict):
    invoer = maak_invoer(**item["document"]["invoer"])
    return toets_actualiteit(document, invoer, _configuratie())


def _met_oordeel(document: Beoordelingsdocument, oordeel: dict):
    return dataclasses.replace(
        document, oordeel_json=json.dumps(oordeel, ensure_ascii=False, sort_keys=True)
    )


def test_referentie_komt_uit_de_v1_code():
    herkomst = REFERENTIE["herkomst"]
    assert herkomst["contract_sha256"] == (
        "6dcae57bc60d1edec09d49fa35d21d135cf0dd43e587ef7e8ba60dac22f16ca8"
    )
    assert "SYN-niet-uniek" in IDS and len(IDS) >= 5
    for item in REFERENTIE["documenten"]:
        assert item["document"]["contractversie"] == V1
        assert item["document"]["binding"]["contractversie"] == V1
        assert item["document"]["status"] != "error"
    assert CONTRACTVERSIE != V1


# --- (a) geldig /1-document → historisch ---------------------------------------


@pytest.mark.parametrize("geval_id", IDS)
def test_geldig_v1_document_wordt_historisch_en_geen_error(geval_id):
    item = _item(geval_id)
    actualiteit = _actualiteit(_uit_dict(item), item)
    assert (actualiteit.status, actualiteit.reden, actualiteit.melding) == (
        "review_required",
        "historical",
        MELDING_HISTORISCH,
    )


def test_v1_document_met_niet_uniek_citaat_blijft_onder_v1_regels_geldig():
    """Onder /1 mocht een citaat op een expliciete positie meer dan eens voorkomen."""
    item = _item("SYN-niet-uniek")
    oordeel = json.loads(item["oordeel_json"])
    kern = item["document"]["invoer"]["kern"]
    quote = oordeel["passages"][0]["quote"]
    assert kern.count(quote) == 2
    assert _actualiteit(_uit_dict(item), item).reden == "historical"


def test_v1_document_blijft_ongewijzigd():
    item = _item("C112")
    document = _uit_dict(item)
    voor = document.als_dict()
    _actualiteit(document, item)
    assert document.als_dict() == voor


# --- (b) /1 met gemanipuleerde positie → error --------------------------------


@pytest.mark.parametrize(
    ("geval_id", "pad", "delta"),
    [
        ("C112", ("start",), 1),
        ("C112", ("end",), -1),
        ("C105", ("ground", "start"), 1),
        ("C105", ("ground", "end"), 1),
        ("SYN-niet-uniek", ("start",), 1),
    ],
    ids=["start", "end", "grond-start", "grond-end", "niet-uniek-start"],
)
def test_v1_document_met_gemanipuleerde_positie_is_error(geval_id, pad, delta):
    item = _item(geval_id)
    oordeel = json.loads(item["oordeel_json"])
    doel = oordeel["passages"][0]
    for stap in pad[:-1]:
        doel = doel[stap]
    doel[pad[-1]] += delta
    actualiteit = _actualiteit(_met_oordeel(_uit_dict(item), oordeel), item)
    assert (actualiteit.status, actualiteit.melding) == ("error", MELDING_E)


def test_v1_document_zonder_posities_is_error():
    item = _item("C112")
    oordeel = json.loads(item["oordeel_json"])
    for passage in oordeel["passages"]:
        del passage["start"], passage["end"]
        del passage["ground"]["start"], passage["ground"]["end"]
    actualiteit = _actualiteit(_met_oordeel(_uit_dict(item), oordeel), item)
    assert actualiteit.status == "error"


# --- (c) /1 met gewijzigde quote → error --------------------------------------


@pytest.mark.parametrize("wijziging", ["citaat", "citaat-consistent", "grondcitaat"])
def test_v1_document_met_gewijzigde_quote_is_error(wijziging):
    item = _item("C105")
    oordeel = json.loads(item["oordeel_json"])
    passage = oordeel["passages"][0]
    if wijziging == "citaat":
        passage["quote"] = passage["quote"].upper()
    elif wijziging == "citaat-consistent":
        # Een ander, wel op zijn posities staand citaat: de melding past niet meer.
        kern = item["document"]["invoer"]["kern"]
        passage.update({"quote": kern[0:13], "start": 0, "end": 13})
    else:
        passage["ground"]["quote"] = passage["ground"]["quote"] + "!"
    actualiteit = _actualiteit(_met_oordeel(_uit_dict(item), oordeel), item)
    assert (actualiteit.status, actualiteit.melding) == ("error", MELDING_E)


@pytest.mark.parametrize("veld", ["status", "melding"])
def test_v1_document_met_gewijzigde_uitkomst_is_error(veld):
    item = _item("C105")
    vervanging = {"status": "pass", "melding": "INT-02 — Voldoet."}[veld]
    document = dataclasses.replace(_uit_dict(item), **{veld: vervanging})
    assert _actualiteit(document, item).status == "error"


# --- (d) actueel (/3) document gemanipuleerd → error ----------------------------


def _actueel_document(item: dict) -> Beoordelingsdocument:
    """Een document onder de actuele contractversie (/3) via `beoordeel`."""
    oordeel = json.loads(item["oordeel_json"])
    for passage in oordeel["passages"]:
        del passage["start"], passage["end"]
        del passage["ground"]["start"], passage["ground"]["end"]
    return beoordeel(
        maak_invoer(**item["document"]["invoer"]),
        _configuratie(),
        oordeel,
        Uitvoering(actor="ai", status="completed"),
    )


@pytest.mark.parametrize(
    "manipulatie", ["positie", "quote", "status", "melding", "als-v1-zonder-posities"]
)
def test_gemanipuleerd_actueel_document_is_error(manipulatie):
    item = _item("C105")
    document = _actueel_document(item)
    assert document.contractversie == CONTRACTVERSIE != V2
    assert _actualiteit(document, item).status == "fail"  # ongemanipuleerd actueel
    oordeel = document.oordeel
    if manipulatie == "positie":
        oordeel["passages"][0]["start"] += 1
        document = _met_oordeel(document, oordeel)
    elif manipulatie == "quote":
        oordeel["passages"][0]["quote"] += " "
        document = _met_oordeel(document, oordeel)
    elif manipulatie == "status":
        document = dataclasses.replace(document, status="pass")
    elif manipulatie == "melding":
        document = dataclasses.replace(document, melding="INT-02 — Voldoet.")
    else:
        # /1-label op een /2-oordeel zonder posities: onder /1 ongeldige vorm.
        for passage in oordeel["passages"]:
            del passage["start"], passage["end"]
            del passage["ground"]["start"], passage["ground"]["end"]
        document = dataclasses.replace(
            _met_oordeel(document, oordeel),
            contractversie=V1,
            binding=dataclasses.replace(document.binding, contractversie=V1),
        )
    actualiteit = _actualiteit(document, item)
    assert (actualiteit.status, actualiteit.melding) == ("error", MELDING_E)


# --- (d2) echt /2-document (kwalificatieproef v5): historisch; gemanipuleerd → error


def _v2_proefdocument() -> Beoordelingsdocument:
    """Het in kwalificatieproef v5 door de /2-code bewaarde C107-document."""
    resultaat = json.loads(V5_RESULTAAT.read_text("utf-8"))
    (geval,) = [g for g in resultaat["gevallen"] if g["id"] == "C107"]
    data = geval["document"]
    return Beoordelingsdocument(
        contractversie=data["contractversie"],
        invoer=maak_invoer(**data["invoer"]),
        binding=Binding(**data["binding"]),
        uitvoering=Uitvoering(**data["uitvoering"]),
        status=data["status"],
        reden=data["reden"],
        melding=data["melding"],
        vraag=data["vraag"],
        foutcategorie=data["foutcategorie"],
        oordeel_json=json.dumps(data["oordeel"], ensure_ascii=False, sort_keys=True),
        foutdetail=data["foutdetail"],
    )


def _actualiteit_eigen(document: Beoordelingsdocument):
    """Actuele invoer en configuratie = die van het document zelf."""
    return toets_actualiteit(document, document.invoer, document.binding.configuratie())


def test_v2_proefdocument_is_echt_v2_en_wordt_historisch():
    document = _v2_proefdocument()
    assert document.contractversie == document.binding.contractversie == V2
    assert document.status == "fail"
    actualiteit = _actualiteit_eigen(document)
    assert (actualiteit.status, actualiteit.reden, actualiteit.melding) == (
        "review_required",
        "historical",
        MELDING_HISTORISCH,
    )


@pytest.mark.parametrize(
    ("pad", "delta"),
    [
        (("start",), 1),
        (("start",), -1),
        (("end",), -1),
        (("end",), 1),
        (("ground", "start"), 1),
        (("ground", "end"), -1),
    ],
    ids=["start+1", "start-1", "end-1", "end+1", "grond-start+1", "grond-end-1"],
)
def test_v2_proefdocument_met_gemanipuleerde_positie_is_error(pad, delta):
    document = _v2_proefdocument()
    oordeel = document.oordeel
    doel = oordeel["passages"][0]
    for stap in pad[:-1]:
        doel = doel[stap]
    doel[pad[-1]] += delta
    actualiteit = _actualiteit_eigen(_met_oordeel(document, oordeel))
    assert (actualiteit.status, actualiteit.melding) == ("error", MELDING_E)


def test_v2_proefdocument_zonder_posities_is_error():
    document = _v2_proefdocument()
    oordeel = document.oordeel
    for passage in oordeel["passages"]:
        del passage["start"], passage["end"]
        del passage["ground"]["start"], passage["ground"]["end"]
    assert _actualiteit_eigen(_met_oordeel(document, oordeel)).status == "error"


@pytest.mark.parametrize(
    "wijziging",
    ["citaat", "citaat-consistent", "grondcitaat", "grondcitaat-consistent"],
)
def test_v2_proefdocument_met_gewijzigde_quote_is_error(wijziging):
    document = _v2_proefdocument()
    kern = document.invoer.kern
    oordeel = document.oordeel
    passage = oordeel["passages"][0]
    if wijziging == "citaat":
        passage["quote"] = passage["quote"].upper()
    elif wijziging == "citaat-consistent":
        # Een ander, wel uniek en op zijn posities staand citaat.
        passage.update({"quote": kern[0:12], "start": 0, "end": 12})
    elif wijziging == "grondcitaat":
        passage["ground"]["quote"] += "!"
    else:
        passage["ground"].update({"quote": kern[13:48], "start": 13, "end": 48})
    actualiteit = _actualiteit_eigen(_met_oordeel(document, oordeel))
    assert (actualiteit.status, actualiteit.melding) == ("error", MELDING_E)


# --- (e) onbekende contractversie → error -------------------------------------


def _basisdocument(basis: str) -> tuple[Beoordelingsdocument, object]:
    """(document, actualiteitsfunctie) voor /1, echt /2 of actueel /3."""
    if basis == "v2":
        return _v2_proefdocument(), _actualiteit_eigen
    item = _item("C112")
    document = _uit_dict(item) if basis == "v1" else _actueel_document(item)
    return document, lambda doc: _actualiteit(doc, item)


@pytest.mark.parametrize(
    "versie",
    ["def835-int02-assessment/0", "def835-int02-assessment/9", "onbekend"],
)
@pytest.mark.parametrize("basis", ["v1", "v2", "v3"])
def test_onbekende_contractversie_is_error(versie, basis):
    document, actualiteit_van = _basisdocument(basis)
    document = dataclasses.replace(
        document,
        contractversie=versie,
        binding=dataclasses.replace(document.binding, contractversie=versie),
    )
    actualiteit = actualiteit_van(document)
    assert (actualiteit.status, actualiteit.melding) == ("error", MELDING_E)


@pytest.mark.parametrize(
    ("basis", "ander"),
    [("v1", CONTRACTVERSIE), ("v2", CONTRACTVERSIE), ("v2", V1), ("v3", V2)],
)
def test_document_en_binding_met_verschillende_versie_is_error(basis, ander):
    document, actualiteit_van = _basisdocument(basis)
    document = dataclasses.replace(document, contractversie=ander)
    assert actualiteit_van(document).status == "error"
