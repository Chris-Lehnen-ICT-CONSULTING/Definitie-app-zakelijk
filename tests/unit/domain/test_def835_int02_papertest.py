"""DEF-835 besluit 16 — de paper test van het bronfunctie-ontwerp als tabeltest.

Bron: `goldset-voorbereiding/bronfuncties-ontwerp-v1.md` §3.2 (verwachte
kernvorm en bronfuncties per geval) en §3.3 (27/27). Per geval wordt
modeluitvoer gesynthetiseerd zoals de labelreden aangeeft; contract /4 moet
daaruit het label afleiden.

Gelezen worden ALLEEN regressie en ontwikkeling:

- regressie (C105, C107, C112): de invoer uit de verstuurde payloads in
  `kwalificatieproef-v7/regressie-bundel.json` en het label uit
  `kwalificatieproef-v7/regressie-resultaat.json`;
- ontwikkeling (24 G-gevallen): `goldset-freeze-v1/ontwikkeling-v1.json`.

Het gezamenlijke gevallenbestand (met de hold-out) en het payloadbestand van
het manifest worden niet geopend. 7A: dit is een consistentietoets van de
regel, geen bewijs van modelprestatie; de regel is ontworpen terwijl deze 27
gevallen zichtbaar waren.

Citaten: een passagecitaat is het labelcitaat of een letterlijk deel van de
kern; een bronfunctiecitaat is de hele tekst van die grondbron (altijd
letterlijk en uniek). Contextitems zwijgen in alle gevallen (ontwerp §3.1).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from domain.int02 import contract
from domain.int02.contract import Configuratie, Uitvoering, beoordeel, maak_invoer
from tests.fixtures.def835_int02_v4 import passage, uitvoer

pytestmark = [pytest.mark.unit]

ROOT = Path(__file__).resolve().parents[3]
D = (
    ROOT / "docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925"
    "/gedeeld/uitvoering/o2/goldset-voorbereiding/goldset-freeze-v1"
)
ONTWIKKELING = D / "ontwikkeling-v1.json"
REGRESSIE_BUNDEL = D / "kwalificatieproef-v7/regressie-bundel.json"
REGRESSIE_RESULTAAT = D / "kwalificatieproef-v7/regressie-resultaat.json"

FUNCTIE = {
    "C": "criterion",
    "D": "derivation",
    "A": "actor_prescription",
    "R": "discretionary_decision_rule",
    "N": "not_a_criterion",
    "O": "unclear",
}
SLEUTEL = {"bed": "bedoeling", "B1": "bron/B1", "B2": "bron/B2", "B3": "bron/B3"}
KERN = None  # passagecitaat = de hele kern

#: Ontwerp §3.2, kolom "Verwachte kernvorm en bronfuncties" en "Pad"; bij een
#: keuze in het ontwerp ("B1 R/A", "bed C of –") staat de gekozen invulling.
#: Per passage: (citaat: None = hele kern, int = labelpassage, str = letterlijk
#: deel van de kern; kernvorm; bronfuncties; zwijgende bronnen weggelaten).
SPEC: dict[str, tuple[list[tuple[Any, str, dict[str, str]]], str]] = {
    "C105": ([(KERN, "instruction", {"bed": "A"})], "voorschrift_in_kern"),
    "C107": ([(KERN, "discretion_form", {})], "discretie_zonder_bedoeling"),
    "C112": ([(KERN, "descriptive_act", {"bed": "C"})], "bronnen_beschrijvend"),
    "G011": ([(0, "no_act", {"bed": "C", "B1": "D"})], "bronnen_beschrijvend"),
    "G015": (
        [
            (0, "no_act", {"bed": "C", "B1": "C"}),
            (1, "descriptive_act", {"bed": "C", "B1": "C"}),
        ],
        "bronnen_beschrijvend",
    ),
    "G019": ([(0, "no_act", {"bed": "C", "B1": "C"})], "bronnen_beschrijvend"),
    "G027": ([(0, "no_act", {"bed": "D", "B1": "D"})], "bronnen_beschrijvend"),
    "G030": (
        [(0, "descriptive_act", {"B1": "C", "B2": "C"})],
        "bronnen_beschrijvend",
    ),
    "G039": ([(0, "descriptive_act", {"bed": "C", "B1": "C"})], "bronnen_beschrijvend"),
    "G007": ([(0, "no_act", {"bed": "C", "B1": "C"})], "bronnen_beschrijvend"),
    "G021": ([(0, "discretion_form", {"B1": "C"})], "bronnen_beschrijvend"),
    "G037": (
        [
            (0, "descriptive_act", {"bed": "C", "B1": "C"}),
            (1, "no_act", {"bed": "C", "B1": "C"}),
        ],
        "bronnen_beschrijvend",
    ),
    "G041": ([(0, "obligation_form", {"B1": "C"})], "bronnen_beschrijvend"),
    "G046": (
        [(0, "descriptive_act", {"B1": "C", "B2": "C"})],
        "bronnen_beschrijvend",
    ),
    "G055": (
        [
            (0, "no_act", {"bed": "C", "B1": "C", "B2": "C"}),
            (1, "descriptive_act", {"bed": "C", "B1": "C", "B2": "C"}),
        ],
        "bronnen_beschrijvend",
    ),
    "G008": ([(0, "instruction", {"B1": "A"})], "voorschrift_in_kern"),
    "G012": ([(0, "instruction", {"B1": "A"})], "voorschrift_in_kern"),
    "G036": ([(0, "obligation_form", {"B1": "A"})], "voorschrift_bevestigd"),
    "G048": (
        [
            (
                "Meting van de grondwaterstand tussen twee reguliere meetmomenten",
                "no_act",
                {"B1": "C", "B2": "C"},
            ),
            (0, "descriptive_act", {"B1": "A", "B2": "N"}),
        ],
        "voorschrift_bevestigd",
    ),
    "G050": (
        [
            (0, "no_act", {"B1": "D", "B2": "D"}),
            (1, "discretion_form", {"B1": "R"}),
        ],
        "voorschrift_bevestigd",
    ),
    "G052": ([(0, "instruction", {"B1": "A"})], "voorschrift_in_kern"),
    "G042": (
        [(0, "descriptive_act", {"B1": "A", "B2": "O"})],
        "bronvoorschrift_niet_overgenomen",
    ),
    "G045": ([(0, "descriptive_act", {"B1": "O", "B2": "O"})], "bronnen_open"),
    "G047": (
        [(0, "descriptive_act", {"B1": "A"})],
        "bronvoorschrift_niet_overgenomen",
    ),
    "G060": ([(0, "descriptive_act", {"B1": "A", "B2": "C"})], "conflict"),
    "G070": ([(0, "descriptive_act", {"B1": "C", "B2": "A"})], "conflict"),
    "G076": ([(0, "descriptive_act", {"B1": "C", "B2": "N", "B3": "O"})], "conflict"),
}
REGRESSIE = ("C105", "C107", "C112")


def _gevallen() -> dict[str, dict[str, Any]]:
    """{id: {"invoer": Int02Invoer, "label": status, "passages": [citaten]}}."""
    gevallen: dict[str, dict[str, Any]] = {}
    bundel = json.loads(REGRESSIE_BUNDEL.read_text("utf-8"))
    resultaat = json.loads(REGRESSIE_RESULTAAT.read_text("utf-8"))
    labels = {g["id"]: g["label_status"] for g in resultaat["gevallen"]}
    assert bundel["fase"] == "regressie"
    for geval in bundel["gevallen"]:
        payload = json.loads(geval["payload"])
        (bericht,) = payload["messages"]
        data = json.loads(bericht["content"])
        gevallen[geval["id"]] = {
            "invoer": maak_invoer(**data["invoer"]),
            "label": labels[geval["id"]],
            "passages": [],
        }
    ontwikkeling = json.loads(ONTWIKKELING.read_text("utf-8"))
    assert ontwikkeling["soort"] == "def835-int02-goldset-ontwikkeling/1"
    for item in ontwikkeling["gevallen"]:
        geval = item["geval"]
        gevallen[item["id"]] = {
            "invoer": maak_invoer(
                begrip=geval["begrip"],
                kern=geval["kern"],
                bedoeling=geval["bedoeling"],
                **geval["context"],
                bronnen=[
                    {"id": b["id"], "tekst": b["tekst"]} for b in geval["bronnen"]
                ],
            ),
            "label": item["label"]["status"],
            "passages": [p["citaat"] for p in item["label"]["passages"]],
        }
    return gevallen


GEVALLEN = _gevallen()


def _brontekst(invoer, sleutel: str) -> str:
    if sleutel == "bedoeling":
        assert invoer.bedoeling is not None, "spec noemt een onbekende bedoeling"
        return invoer.bedoeling
    return {f"bron/{b.id}": b.tekst for b in invoer.bronnen}[sleutel]


def _modeluitvoer(geval_id: str, verdict: str) -> dict[str, Any]:
    geval = GEVALLEN[geval_id]
    invoer = geval["invoer"]
    passages = []
    for citaat, kernvorm, codes in SPEC[geval_id][0]:
        if citaat is None:
            citaat = invoer.kern
        elif isinstance(citaat, int):
            citaat = geval["passages"][citaat]
        functies = {}
        for kort, code in codes.items():
            sleutel = SLEUTEL[kort]
            functies[sleutel] = (
                FUNCTIE[code],
                None if code == "O" else _brontekst(invoer, sleutel),
            )
        passages.append(passage(invoer, citaat, kernvorm, functies))
    return uitvoer(passages, verdict, reason="Synthetische paper-testinvulling.")


def _configuratie() -> Configuratie:
    return Configuratie(
        normhash=hashlib.sha256(b"testnorm def771-int02/2").hexdigest(),
        promptversie="def835-int02-prompt/testfixture",
        routeringshash=hashlib.sha256(b"testroutering").hexdigest(),
        provider="fake-provider",
        model="fake-model-1",
    )


def _beoordeel(geval_id: str, verdict: str):
    return beoordeel(
        GEVALLEN[geval_id]["invoer"],
        _configuratie(),
        _modeluitvoer(geval_id, verdict),
        Uitvoering(actor="ai", status="completed"),
    )


LABELVERDICT = {
    "pass": "pass",
    "fail": "fail",
    "review_required": "insufficient_information",
}


def test_precies_de_27_regressie_en_ontwikkelgevallen_zonder_holdout():
    assert set(GEVALLEN) == set(SPEC)
    assert len(GEVALLEN) == 27
    assert [g for g in GEVALLEN if g.startswith("C")] == list(REGRESSIE)
    labels = [GEVALLEN[g]["label"] for g in GEVALLEN if g.startswith("G")]
    assert {s: labels.count(s) for s in set(labels)} == {
        "pass": 12,
        "fail": 6,
        "review_required": 6,
    }


@pytest.mark.parametrize("modelverdict", ["label", "pass", "fail"])
@pytest.mark.parametrize("geval_id", list(SPEC))
def test_papertest_geval_volgt_het_label_via_het_ontwerppad(geval_id, modelverdict):
    label = GEVALLEN[geval_id]["label"]
    verdict = LABELVERDICT[label] if modelverdict == "label" else modelverdict
    document = _beoordeel(geval_id, verdict)
    assert document.status == label, (document.status, document.foutcategorie)
    afleiding = document.oordeel["dienst"]["afleiding"]
    assert afleiding == SPEC[geval_id][1]
    # 2A: alleen bij een afwijkend modelverdict een zichtbare omzetting.
    if LABELVERDICT[label] == verdict:
        assert document.omzetting is None
    else:
        assert document.omzetting == afleiding
    assert document.oordeel["verdict"] == verdict


def test_papertest_27_van_27_met_6_van_6_review():
    juist = {"regressie": 0, "ontwikkeling": 0, "review_required": 0}
    for geval_id in SPEC:
        label = GEVALLEN[geval_id]["label"]
        if _beoordeel(geval_id, "pass").status == label:
            juist["regressie" if geval_id in REGRESSIE else "ontwikkeling"] += 1
            if label == "review_required" and geval_id.startswith("G"):
                juist["review_required"] += 1
    assert juist == {"regressie": 3, "ontwikkeling": 24, "review_required": 6}


# --- §3.3: gevoeligheid onder de gekozen opties (diagnostisch) -------------------------


def _met(geval_id: str, index: int, sleutel: str, functie: str):
    """De papertest-invulling met één andere bronfunctie (citaat: hele brontekst)."""
    respons = _modeluitvoer(geval_id, "pass")
    invoer = GEVALLEN[geval_id]["invoer"]
    for bf in respons["passages"][index]["bronfuncties"]:
        if bf["bron"] == sleutel:
            bf["function"] = functie
            bf["quote"] = (
                None
                if functie in ("not_addressed", "unclear")
                else _brontekst(invoer, sleutel)
            )
    return beoordeel(
        invoer, _configuratie(), respons, Uitvoering(actor="ai", status="completed")
    )


def test_1b_beschermt_g036_en_g047_tegen_een_beschrijvend_ingevulde_bedoeling():
    """Ontwerp §3.3: onder 1A zouden deze een false pass worden."""
    for geval_id in ("G036", "G047"):
        document = _met(geval_id, 0, "bedoeling", "criterion")
        assert document.status == "review_required"
        assert document.oordeel["dienst"]["afleiding"] == "conflict"


def test_5a_beschermt_c107_bij_een_beschrijvend_ingevulde_kernvorm():
    respons = _modeluitvoer("C107", "pass")
    respons["passages"][0]["kernvorm"] = "descriptive_act"
    document = beoordeel(
        GEVALLEN["C107"]["invoer"],
        _configuratie(),
        respons,
        Uitvoering(actor="ai", status="completed"),
    )
    assert document.status == "review_required"
    assert document.oordeel["dienst"]["afleiding"] == "geen_grond_zonder_bedoeling"


@pytest.mark.parametrize("modelverdict", ["label", "pass", "fail"])
def test_g060_met_kale_bron_ids_volgt_het_label_via_conflict(modelverdict):
    """Besluit 19 (keuze 1A), uitslag v8: het model schreef "B1" en "B2" in
    plaats van "bron/B1" en "bron/B2". De dienst leest ze als die sleutels;
    het bewaarde oordeel is canoniek en gelijk aan dat van de juiste sleutels."""
    label = GEVALLEN["G060"]["label"]
    verdict = LABELVERDICT[label] if modelverdict == "label" else modelverdict
    canoniek = _modeluitvoer("G060", verdict)
    kaal = json.loads(json.dumps(canoniek))
    for bf in kaal["passages"][0]["bronfuncties"]:
        if bf["bron"] in ("bron/B1", "bron/B2"):
            bf["bron"] = bf["bron"].removeprefix("bron/")
    assert {bf["bron"] for bf in kaal["passages"][0]["bronfuncties"]} >= {"B1", "B2"}
    invoer = GEVALLEN["G060"]["invoer"]
    uitvoering = Uitvoering(actor="ai", status="completed")
    document = beoordeel(invoer, _configuratie(), kaal, uitvoering)
    assert document.status == label == "review_required", (
        document.foutcategorie,
        document.foutdetail,
    )
    assert document.oordeel["dienst"]["afleiding"] == "conflict"
    assert document == beoordeel(invoer, _configuratie(), canoniek, uitvoering)


def test_g045_blijft_een_false_pass_als_het_model_b1_als_criterium_invult():
    """Bekend restrisico (ontwerp §3.3, §4.3): de regel verzint geen grond."""
    document = _met("G045", 0, "bron/B1", "criterion")
    assert document.status == "pass"
    assert contract.CONTRACTVERSIE == "def835-int02-assessment/4"
