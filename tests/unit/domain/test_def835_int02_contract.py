"""DEF-835 WP1: het interne INT-02-beoordelingscontract def835-int02-assessment/1.

Bron: plan-v1.md §Ontwerpvoorstel en §WP1 (akkoord 26-09-2026), synthese v5
§2/§4 (norm def771-int02/2, T-tekst, appmeldingen, statusmapping) en het
gezamenlijke casusregister v5. De verwachte appmeldingen worden rechtstreeks
uit synthese §4 gelezen, niet uit de implementatie.

Wat deze tests bewijzen (zuiver domein, geen model, geen app-route):

- de exact aangeleverde invoer wordt onveranderlijk en bytegelijk bewaard,
  met defensieve kopieën;
- de binding dekt begrip, kern, bedoeling, context, bronnen, norm (versie en
  hash), promptversie, routeringshash en gevraagde provider/model; elke
  component apart maakt een bewaard document historisch;
- de modeluitvoer is een gesloten structuur (onbekende velden, verkeerde
  typen en bool-als-int worden geweigerd) en wordt nooit gerepareerd;
- elk passagecitaat staat exact op de opgegeven nulgebaseerde posities
  (einde exclusief) in de kern; een geciteerde grond staat exact in het
  genoemde invoerveld of de genoemde bron;
- de statusmapping uit synthese §4: pass, fail, review_required
  (inhoudelijk onvoldoende informatie tegenover nog niet beoordeeld en
  historisch), not_evaluated, error, not_applicable; nooit een cijfer;
- ongeldige uitvoer of citaten geven error, nooit fail of review_required.

Wat deze tests niet bewijzen: dat een model de juiste functie kiest of dat
de gedeclareerde dekking semantisch volledig is. De casussen zijn
ontwikkelgevallen met handmatig ingevulde modelresponsen, geen goldset.

Eigen formuleringen (geen letterlijk sjabloon in synthese §4, ter
beoordeling door coördinator/review): de melding voor nog niet beoordeeld,
de melding voor niet van toepassing, de grondweergave en de koppeling van
de discretievariant aan de VN-melding.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from decimal import Decimal
from pathlib import Path

import pytest

from domain.int02.contract import (
    Configuratie,
    Int02ContractError,
    Uitvoering,
    beoordeel,
    bereken_binding,
    maak_invoer,
    ontbrekende_invoer,
    toets_actualiteit,
)

pytestmark = [pytest.mark.unit]

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = json.loads(
    (ROOT / "tests/fixtures/def835_int02_ontwerpgevallen.json").read_text("utf-8")
)
_SYN = (
    ROOT / "docs/analyses/def606-regeldossiers/INT-02-verdieping"
    "/onderzoek-20260925/gedeeld/gezamenlijke-synthese-v5.md"
).read_text(encoding="utf-8")
_APP = next(
    r for r in _SYN.splitlines() if r.startswith("**Appmeldingen [V, B3 V06]:**")
)
V, VN, VN_DISCRETIE, ONVOLDOENDE, NE, E, HISTORISCH = re.findall(r'"([^"]+)"', _APP)
CONTRACTDOC = ROOT / "docs/architectuur/contracts/int02_assessment_contract_v1.md"

# Eigen formuleringen (zie moduledocstring); de T-tekst noemt de toestand
# "nog te beoordelen — beoordeling niet uitgevoerd".
NIET_BEOORDEELD = "INT-02 — Nog te beoordelen — beoordeling niet uitgevoerd."
NVT = "INT-02 — Niet van toepassing. {reikwijdtegrond}. Er is geen oordeel over de definitiekern."
GRONDLABEL = {
    "kern": "de kern",
    "begrip": "het begrip",
    "bedoeling": "de bevestigde bedoeling",
    "organisatorische_context": "de organisatorische context",
    "juridische_context": "de juridische context",
    "wettelijke_basis": "de wettelijke basis",
}
FUNCTIELABEL = {"criterion": "een criterium", "derivation": "een afleiding"}

NORMHASH = hashlib.sha256(b"testnorm def771-int02/2").hexdigest()
ROUTERINGSHASH = hashlib.sha256(b"testroutering").hexdigest()
ONBEKEND = "unknown"
HEX64 = re.compile(r"[0-9a-f]{64}")


def _geval(case_id: str, variant: str | None = None) -> dict:
    return copy.deepcopy(
        next(
            g
            for g in FIXTURE["gevallen"]
            if g["id"] == case_id and g.get("variant") == variant
        )
    )


def _configuratie(**wijziging) -> Configuratie:
    velden = {
        "normversie": "def771-int02/2",
        "normhash": NORMHASH,
        "promptversie": "def835-int02-prompt/testfixture",
        "routeringshash": ROUTERINGSHASH,
        "provider": "fake-provider",
        "model": "fake-model-1",
    }
    velden.update(wijziging)
    return Configuratie(**velden)


def _uitvoering(**wijziging) -> Uitvoering:
    velden = {"actor": "ai", "status": "completed"}
    velden.update(wijziging)
    return Uitvoering(**velden)


def _beoordeel(invoerdata: dict, respons, **uitvoering):
    return beoordeel(
        maak_invoer(**invoerdata), _configuratie(), respons, _uitvoering(**uitvoering)
    )


def _grondtekst(grond: dict) -> str:
    if grond["field"] == "bron":
        label = f"bronpassage {grond['ref']}"
    else:
        label = GRONDLABEL[grond["field"]]
    if grond["quote"] is not None:
        label += f" ('{grond['quote']}')"
    return label


def _zonder_slotpunt(tekst: str) -> str:
    return tekst[:-1] if tekst.endswith(".") else tekst


def _sleutels(waarde) -> set[str]:
    if isinstance(waarde, dict):
        return set(waarde) | {s for v in waarde.values() for s in _sleutels(v)}
    if isinstance(waarde, list | tuple):
        return {s for v in waarde for s in _sleutels(v)}
    return set()


def _basis_invoer() -> dict:
    """C112 met synthetische, testlokale context en bron (geen casusclaim)."""
    data = _geval("C112")["invoer"]
    data["juridische_context"] = ["synthetisch verbintenissenrecht"]
    data["wettelijke_basis"] = ["synthetische regeling art. 1"]
    data["bronnen"] = [
        {"id": "B1", "tekst": "Synthetische bron: een verplichting rust op een partij."}
    ]
    return data


# --- Ontwerpgevallen uit de fixture ----------------------------------------------

_ENKELVOUDIG = [g for g in FIXTURE["gevallen"] if "versies" not in g]


@pytest.mark.parametrize(
    "geval",
    _ENKELVOUDIG,
    ids=[
        g["id"] + ("-" + g["variant"] if "variant" in g else "") for g in _ENKELVOUDIG
    ],
)
def test_ontwerpgeval_geeft_verwachte_status(geval):
    assert "geen goldset" in FIXTURE["gebruik"].lower()
    assert geval["herkomst"] and geval["referentie"]
    verwacht = geval["verwacht"]
    if verwacht["status"] in ("pass", "fail") or verwacht["reden"]:
        # Betekenisafhankelijk label: gekoppeld aan expliciete bedoeling of
        # aan een expliciet vastgelegde onbekende bedoeling.
        assert geval["invoer"]["bedoeling"] or any(
            "bedoeling expliciet onbekend" in a for a in geval["aanvullingen"]
        )

    doc = _beoordeel(
        geval["invoer"], copy.deepcopy(geval["modelrespons"]), **geval["uitvoering"]
    )

    assert doc.status == verwacht["status"]
    assert doc.reden == verwacht["reden"]
    if "foutcategorie" in verwacht:
        assert doc.foutcategorie == verwacht["foutcategorie"]
        assert doc.melding == E
        assert doc.oordeel is None
    if "ontbreekt" in verwacht:
        assert doc.melding == NE.replace("{kern/context}", verwacht["ontbreekt"])
        assert doc.oordeel is None


def test_c118_oud_oordeel_wordt_historisch_voor_nieuwe_versie():
    geval = _geval("C118")
    v1, v2 = geval["versies"]
    oud = _beoordeel(v1["invoer"], v1["modelrespons"], **v1["uitvoering"])
    assert oud.status == "pass"
    voor = oud.als_dict()

    replay = toets_actualiteit(oud, maak_invoer(**v2["invoer"]), _configuratie())

    assert (replay.status, replay.reden) == ("review_required", "historical")
    assert replay.melding == HISTORISCH
    assert oud.als_dict() == voor  # het oude document blijft ongewijzigd
    nieuw = _beoordeel(v2["invoer"], v2["modelrespons"], **v2["uitvoering"])
    assert nieuw.status == "fail"


# --- Exacte, onveranderlijke invoer --------------------------------------------


def test_kern_wordt_bytegelijk_bewaard():
    data = _basis_invoer()
    data["kern"] = "  Getal dat even is indien het\r\ndeelbaar is.  "
    invoer = maak_invoer(**data)
    assert invoer.kern == data["kern"]
    doc = beoordeel(invoer, _configuratie(), None, _uitvoering(status="not_executed"))
    assert doc.als_dict()["invoer"]["kern"] == data["kern"]


def test_invoer_is_defensieve_kopie():
    data = _basis_invoer()
    invoer = maak_invoer(**data)
    data["organisatorische_context"].append("later toegevoegd")
    data["juridische_context"].clear()
    data["bronnen"][0]["tekst"] = "gewijzigd"
    data["bronnen"].append({"id": "B2", "tekst": "later"})
    assert invoer.organisatorische_context == ("synthetische begrippenstudie",)
    assert invoer.juridische_context == ("synthetisch verbintenissenrecht",)
    assert [(b.id, b.tekst) for b in invoer.bronnen] == [
        ("B1", "Synthetische bron: een verplichting rust op een partij.")
    ]


def test_invoer_is_onveranderlijk():
    invoer = maak_invoer(**_basis_invoer())
    with pytest.raises(AttributeError):
        invoer.kern = "andere kern"


def test_onbekende_bedoeling_blijft_expliciet_onbekend():
    data = _basis_invoer()
    data["bedoeling"] = None
    doc = beoordeel(
        maak_invoer(**data), _configuratie(), None, _uitvoering(status="not_executed")
    )
    assert doc.als_dict()["invoer"]["bedoeling"] is None


@pytest.mark.parametrize(
    "wijziging",
    [
        {"kern": 12},
        {"begrip": None},
        {"bedoeling": 3},
        {"organisatorische_context": "los"},
        {"juridische_context": [True]},
        {"wettelijke_basis": [None]},
        {"bronnen": [{"id": "B1"}]},
        {"bronnen": [{"id": "B1", "tekst": "x", "url": "https://voorbeeld"}]},
        {"bronnen": [{"id": "", "tekst": "x"}]},
        {"bronnen": [{"id": "B1", "tekst": "x"}, {"id": "B1", "tekst": "y"}]},
    ],
    ids=[
        "kern-geen-str",
        "begrip-none",
        "bedoeling-geen-str",
        "context-geen-lijst",
        "context-bool",
        "wettelijke-basis-none",
        "bron-zonder-tekst",
        "bron-onbekend-veld",
        "bron-lege-id",
        "bron-dubbele-id",
    ],
)
def test_ongeldige_invoer_wordt_geweigerd(wijziging):
    data = _basis_invoer()
    data.update(wijziging)
    with pytest.raises(Int02ContractError):
        maak_invoer(**data)


# --- Binding en historie -------------------------------------------------------

_BRON_B1 = {
    "id": "B1",
    "tekst": "Synthetische bron: een verplichting rust op een partij.",
}
BINDINGSWIJZIGINGEN = [
    ("begrip", {"begrip": "verbintenis"}, {}, "begrip_hash"),
    (
        "kern-witruimte",
        {
            "kern": "Verplichting van een partij om de overeengekomen prestatie te verrichten. "
        },
        {},
        "kern_hash",
    ),
    ("bedoeling", {"bedoeling": None}, {}, "bedoeling_hash"),
    (
        "organisatorische-context",
        {"organisatorische_context": ["ander loket"]},
        {},
        "context_hash",
    ),
    ("juridische-context", {"juridische_context": []}, {}, "context_hash"),
    (
        "wettelijke-basis",
        {"wettelijke_basis": ["synthetische regeling art. 2"]},
        {},
        "context_hash",
    ),
    (
        "brontekst",
        {"bronnen": [{"id": "B1", "tekst": "Andere bron."}]},
        {},
        "bronnen_hash",
    ),
    ("bron-id", {"bronnen": [{**_BRON_B1, "id": "B2"}]}, {}, "bronnen_hash"),
    (
        "bron-erbij",
        {"bronnen": [_BRON_B1, {"id": "B2", "tekst": "Extra."}]},
        {},
        "bronnen_hash",
    ),
    ("normversie", {}, {"normversie": "def771-int02/3"}, "normversie"),
    (
        "normhash",
        {},
        {"normhash": hashlib.sha256(b"andere norm").hexdigest()},
        "normhash",
    ),
    (
        "promptversie",
        {},
        {"promptversie": "def835-int02-prompt/anders"},
        "promptversie",
    ),
    (
        "routeringshash",
        {},
        {"routeringshash": hashlib.sha256(b"andere routering").hexdigest()},
        "routeringshash",
    ),
    ("provider", {}, {"provider": "andere-provider"}, "provider"),
    ("model", {}, {"model": "fake-model-2"}, "model"),
]
_BINDINGSVELDEN = (
    "contractversie",
    "normversie",
    "normhash",
    "promptversie",
    "routeringshash",
    "provider",
    "model",
    "begrip_hash",
    "kern_hash",
    "bedoeling_hash",
    "context_hash",
    "bronnen_hash",
)


def test_binding_legt_versies_en_hashes_vast():
    binding = bereken_binding(maak_invoer(**_basis_invoer()), _configuratie())
    assert binding.contractversie == "def835-int02-assessment/1"
    assert binding.normversie == "def771-int02/2"
    assert (binding.normhash, binding.routeringshash) == (NORMHASH, ROUTERINGSHASH)
    assert (binding.provider, binding.model) == ("fake-provider", "fake-model-1")
    assert binding.promptversie == "def835-int02-prompt/testfixture"
    for veld in (
        "begrip_hash",
        "kern_hash",
        "bedoeling_hash",
        "context_hash",
        "bronnen_hash",
    ):
        assert HEX64.fullmatch(getattr(binding, veld)), veld


@pytest.mark.parametrize(
    ("invoerwijziging", "configwijziging", "veld"),
    [w[1:] for w in BINDINGSWIJZIGINGEN],
    ids=[w[0] for w in BINDINGSWIJZIGINGEN],
)
def test_elke_bindingscomponent_maakt_oud_oordeel_historisch(
    invoerwijziging, configwijziging, veld
):
    basis = _basis_invoer()
    geval = _geval("C112")
    doc = beoordeel(
        maak_invoer(**basis), _configuratie(), geval["modelrespons"], _uitvoering()
    )
    assert doc.status == "pass"
    nieuw_invoer = maak_invoer(**{**basis, **invoerwijziging})
    nieuw_config = _configuratie(**configwijziging)

    oud_binding = bereken_binding(maak_invoer(**basis), _configuratie())
    nieuw_binding = bereken_binding(nieuw_invoer, nieuw_config)
    verschil = {
        v
        for v in _BINDINGSVELDEN
        if getattr(oud_binding, v) != getattr(nieuw_binding, v)
    }
    assert verschil == {veld}

    replay = toets_actualiteit(doc, nieuw_invoer, nieuw_config)
    assert (replay.status, replay.reden, replay.melding) == (
        "review_required",
        "historical",
        HISTORISCH,
    )


@pytest.mark.parametrize("case_id", ["C116", "C105", "C107"])
def test_ongewijzigde_binding_geeft_bewaard_oordeel(case_id):
    geval = _geval(case_id)
    doc = _beoordeel(geval["invoer"], geval["modelrespons"])
    replay = toets_actualiteit(doc, maak_invoer(**geval["invoer"]), _configuratie())
    assert (replay.status, replay.reden, replay.melding) == (
        doc.status,
        doc.reden,
        doc.melding,
    )


def test_ontbrekend_document_is_nog_niet_beoordeeld():
    geval = _geval("C116")
    replay = toets_actualiteit(None, maak_invoer(**geval["invoer"]), _configuratie())
    assert (replay.status, replay.reden, replay.melding) == (
        "review_required",
        "not_assessed",
        NIET_BEOORDEELD,
    )


def test_niet_uitgevoerde_beoordeling_is_nog_te_beoordelen():
    geval = _geval("C116")
    doc = _beoordeel(geval["invoer"], None, status="not_executed")
    assert (doc.status, doc.reden, doc.melding) == (
        "review_required",
        "not_assessed",
        NIET_BEOORDEELD,
    )
    assert doc.oordeel is None and doc.vraag is None


def test_ontbrekend_document_zonder_context_is_niet_uitgevoerd():
    invoer = maak_invoer(**_geval("C56")["invoer"])
    replay = toets_actualiteit(None, invoer, _configuratie())
    assert replay.status == "not_evaluated"
    assert replay.melding == NE.replace("{kern/context}", "context")


@pytest.mark.parametrize(
    "wijziging",
    [
        {"normhash": "abc"},
        {"routeringshash": "Z" * 64},
        {"provider": ""},
        {"model": True},
        {"promptversie": None},
    ],
    ids=[
        "normhash-kort",
        "routeringshash-geen-hex",
        "provider-leeg",
        "model-bool",
        "prompt-none",
    ],
)
def test_ongeldige_configuratie_wordt_geweigerd(wijziging):
    with pytest.raises(Int02ContractError):
        _configuratie(**wijziging)


# --- Onveranderlijk document en replay-integriteit ----------------------------


def test_oordeel_is_een_kopie_en_invoerrespons_blijft_ongewijzigd():
    geval = _geval("C116")
    respons = copy.deepcopy(geval["modelrespons"])
    doc = _beoordeel(geval["invoer"], respons)
    assert respons == geval["modelrespons"]  # geen reparatie of mutatie
    respons["verdict"] = "fail"
    uitgelezen = doc.oordeel
    uitgelezen["passages"].clear()
    assert doc.oordeel == geval["modelrespons"]


def test_document_is_onveranderlijk():
    geval = _geval("C105")
    doc = _beoordeel(geval["invoer"], geval["modelrespons"])
    with pytest.raises(AttributeError):
        doc.status = "pass"


@pytest.mark.parametrize("veld", ["status", "melding", "invoer"])
def test_gemanipuleerd_document_wordt_niet_als_actueel_geaccepteerd(veld):
    geval = _geval("C105")
    doc = _beoordeel(geval["invoer"], geval["modelrespons"])
    vervanging = {
        "status": "pass",
        "melding": "INT-02 — Voldoet.",
        "invoer": maak_invoer(**_geval("C116")["invoer"]),
    }[veld]
    object.__setattr__(doc, veld, vervanging)
    replay = toets_actualiteit(doc, maak_invoer(**geval["invoer"]), _configuratie())
    assert (replay.status, replay.melding) == ("error", E)


def test_document_is_json_serialiseerbaar_zonder_score():
    geval = _geval("C116")
    doc = _beoordeel(geval["invoer"], geval["modelrespons"])
    data = json.loads(json.dumps(doc.als_dict(), ensure_ascii=False))
    assert data["contractversie"] == "def835-int02-assessment/1"
    assert data["binding"]["normversie"] == "def771-int02/2"
    assert not any("score" in s or "cijfer" in s for s in _sleutels(data))
    assert not hasattr(doc, "score")


# --- Gesloten modeluitvoer: structuur --------------------------------------------


def _mut(pad: tuple, waarde):
    def toepassen(r):
        doel = r
        for stap in pad[:-1]:
            doel = doel[stap]
        if waarde is _WEG:
            del doel[pad[-1]]
        else:
            doel[pad[-1]] = waarde
        return r

    return toepassen


_WEG = object()
STRUCTUURFOUTEN = {
    "geen-object": lambda r: ["pass"],
    "veld-ontbreekt": _mut(("coverage",), _WEG),
    "onbekend-veld-score": _mut(("score",), 1),
    "verdict-onbekend": _mut(("verdict",), "voldoet"),
    "verdict-none": _mut(("verdict",), None),
    "passages-geen-lijst": _mut(("passages",), {}),
    "passage-geen-object": _mut(("passages", 0), "gelijk is"),
    "passage-onbekend-veld": _mut(("passages", 0, "confidence"), 0.9),
    "passage-veld-ontbreekt": _mut(("passages", 0, "ground"), _WEG),
    "functie-onbekend": _mut(("passages", 0, "function"), "rule"),
    "start-float": _mut(("passages", 0, "start"), 14.0),
    "start-str": _mut(("passages", 0, "start"), "14"),
    "reason-leeg": _mut(("reason",), ""),
    "reason-geen-str": _mut(("reason",), 1),
    "question-lijst": _mut(("question",), ["Welke?"]),
    "uncertainty-onbekend": _mut(("uncertainty",), "low"),
    "coverage-onbekend": _mut(("coverage",), "full"),
    "scope-reason-geen-str": _mut(("scope_reason",), 5),
    "grond-onbekend-veld": _mut(("passages", 0, "ground", "confidence"), 1),
    "grond-veld-onbekend": _mut(("passages", 0, "ground", "field"), "toelichting"),
    "grond-ref-ontbreekt": _mut(("passages", 0, "ground", "ref"), _WEG),
    "grond-start-bool": _mut(("passages", 0, "ground", "start"), False),
    "grond-citaat-zonder-positie": _mut(("passages", 0, "ground", "start"), None),
    "grond-kern-met-ref": _mut(
        ("passages", 0, "ground"),
        {"field": "kern", "ref": "K1", "quote": None, "start": None, "end": None},
    ),
}


@pytest.mark.parametrize(
    "mutatie", list(STRUCTUURFOUTEN.values()), ids=list(STRUCTUURFOUTEN)
)
def test_structureel_ongeldige_uitvoer_is_technische_fout(mutatie):
    geval = _geval("C116")
    doc = _beoordeel(geval["invoer"], mutatie(copy.deepcopy(geval["modelrespons"])))
    assert (doc.status, doc.foutcategorie, doc.melding) == (
        "error",
        "invalid_output",
        E,
    )
    assert doc.oordeel is None and doc.reden is None


def test_bool_is_geen_passagepositie():
    geval = _geval("C105")  # passage begint op 0: False == 0 mag niet slagen
    geval["modelrespons"]["passages"][0]["start"] = False
    doc = _beoordeel(geval["invoer"], geval["modelrespons"])
    assert (doc.status, doc.foutcategorie) == ("error", "invalid_output")


def test_voltooide_uitvoering_zonder_uitvoer_is_technische_fout():
    doc = _beoordeel(_geval("C116")["invoer"], None)
    assert (doc.status, doc.foutcategorie, doc.melding) == (
        "error",
        "invalid_output",
        E,
    )


# --- Citaten en posities ------------------------------------------------------


CITAATFOUTEN = {
    "verschoven": {"start": 15, "end": 78},
    "einde-inclusief": {"end": 76},
    "einde-voorbij-kern": {"start": 14, "end": 79},
    "negatieve-start": {"start": -1},
    "leeg-citaat": {"quote": "", "start": 14, "end": 14},
    "hoofdletter": {
        "quote": "Gelijk is aan de som van de bedragen van de verkopen op die dag"
    },
    "niet-in-kern": {"quote": "de som van alle bedragen", "start": 20, "end": 44},
}


@pytest.mark.parametrize(
    "wijziging", list(CITAATFOUTEN.values()), ids=list(CITAATFOUTEN)
)
def test_onjuist_passagecitaat_is_technische_fout(wijziging):
    geval = _geval("C116")
    geval["modelrespons"]["passages"][0].update(wijziging)
    doc = _beoordeel(geval["invoer"], geval["modelrespons"])
    assert (doc.status, doc.foutcategorie, doc.melding) == (
        "error",
        "invalid_citation",
        E,
    )


def test_citaat_wordt_niet_genormaliseerd():
    data = _basis_invoer()
    data["kern"] = "Getal dat even is."
    respons = copy.deepcopy(_geval("C112")["modelrespons"])
    respons["passages"][0].update({"quote": "dat even", "start": 6, "end": 14})
    doc = beoordeel(maak_invoer(**data), _configuratie(), respons, _uitvoering())
    assert (doc.status, doc.foutcategorie) == ("error", "invalid_citation")


def _met_grond(grond: dict):
    respons = copy.deepcopy(_geval("C112")["modelrespons"])
    respons["passages"][0]["ground"] = grond
    return beoordeel(
        maak_invoer(**_basis_invoer()), _configuratie(), respons, _uitvoering()
    )


def _grond(field, ref=None, quote=None, start=None, end=None):
    return {"field": field, "ref": ref, "quote": quote, "start": start, "end": end}


@pytest.mark.parametrize(
    "grond",
    [
        _grond("bron", "B1", "een verplichting rust op een partij", 19, 54),
        _grond("bron", "B1"),
        _grond("juridische_context", 0, "verbintenissenrecht", 12, 31),
        _grond("wettelijke_basis", 0),
        _grond("kern", None, "Verplichting", 0, 12),
        _grond("begrip"),
    ],
    ids=[
        "bron-geciteerd",
        "bron-verwezen",
        "context-geciteerd",
        "wettelijke-basis",
        "kern",
        "begrip",
    ],
)
def test_herleidbare_grond_wordt_geaccepteerd(grond):
    doc = _met_grond(grond)
    assert doc.status == "pass"
    assert doc.oordeel["passages"][0]["ground"] == grond


@pytest.mark.parametrize(
    ("grond", "categorie"),
    [
        (_grond("bron", "B9"), "invalid_citation"),
        (
            _grond("bron", "B1", "een verplichting rust op een partij", 18, 53),
            "invalid_citation",
        ),
        (_grond("bron", "B1", "verzonnen bronzin", 0, 17), "invalid_citation"),
        (_grond("organisatorische_context", 5), "invalid_citation"),
        (_grond("organisatorische_context", True), "invalid_output"),
        (_grond("organisatorische_context", "0"), "invalid_output"),
        (_grond("bron", None), "invalid_output"),
    ],
    ids=[
        "onbekende-bron",
        "bronpositie-verschoven",
        "verzonnen-broncitaat",
        "contextindex-buiten-lijst",
        "contextindex-bool",
        "contextindex-str",
        "bron-zonder-id",
    ],
)
def test_niet_herleidbare_grond_is_technische_fout(grond, categorie):
    doc = _met_grond(grond)
    assert (doc.status, doc.foutcategorie, doc.melding) == ("error", categorie, E)


def test_grond_op_onbekende_bedoeling_is_niet_herleidbaar():
    data = _basis_invoer()
    data["bedoeling"] = None
    respons = _geval("C112")["modelrespons"]  # grond verwijst naar de bedoeling
    doc = beoordeel(maak_invoer(**data), _configuratie(), respons, _uitvoering())
    assert (doc.status, doc.foutcategorie) == ("error", "invalid_citation")


# --- Statusmapping en exacte meldingen -----------------------------------------


@pytest.mark.parametrize("case_id", ["C112", "C116"])
def test_pass_geeft_exacte_voldoet_melding(case_id):
    geval = _geval(case_id)
    doc = _beoordeel(geval["invoer"], geval["modelrespons"])
    passage = geval["modelrespons"]["passages"][0]
    assert doc.status == "pass" and doc.reden is None and doc.vraag is None
    assert doc.melding == (
        V.replace("{passage}", passage["quote"])
        .replace("{criterium/afleiding/kenmerk}", FUNCTIELABEL[passage["function"]])
        .replace("{grond}", _grondtekst(passage["ground"]))
    )


def test_actorvoorschrift_geeft_exacte_voldoet_niet_melding():
    geval = _geval("C105")
    doc = _beoordeel(geval["invoer"], geval["modelrespons"])
    passage = geval["modelrespons"]["passages"][0]
    assert doc.melding == (
        VN.replace("{passage}", passage["quote"])
        .replace("{handeling/afweging}", "een handeling")
        .replace("{grond}", _grondtekst(passage["ground"]))
    )


def test_discretionaire_beslisregel_geeft_discretievariant():
    geval = _geval("C101")
    doc = _beoordeel(geval["invoer"], geval["modelrespons"])
    passage = geval["modelrespons"]["passages"][0]
    basis = (
        VN.replace("{passage}", passage["quote"])
        .replace("{handeling/afweging}", "een afweging")
        .replace("{grond}", _grondtekst(passage["ground"]))
    )
    assert doc.melding == basis + " " + VN_DISCRETIE.replace(
        "{citaat}", passage["quote"]
    )


def test_onvoldoende_informatie_geeft_precies_een_vraag():
    geval = _geval("C107")
    doc = _beoordeel(geval["invoer"], geval["modelrespons"])
    respons = geval["modelrespons"]
    assert (doc.status, doc.reden) == ("review_required", "insufficient_information")
    assert doc.vraag == respons["question"]
    assert doc.melding == (
        ONVOLDOENDE.replace(
            "{ontbrekende of strijdige betekenisgrond}",
            _zonder_slotpunt(respons["reason"]),
        ).replace("{één vraag}", respons["question"])
    )
    assert doc.melding != NIET_BEOORDEELD


def test_fail_blijft_fail_met_open_vraag_en_onzekerheid():
    geval = _geval("C105")
    respons = geval["modelrespons"]
    respons["passages"].append(
        {
            "quote": "de aanvrager",
            "start": 19,
            "end": 31,
            "function": "unclear",
            "ground": _grond("kern"),
        }
    )
    respons.update(
        {
            "question": "Welke aanvrager wordt bedoeld?",
            "uncertainty": "decisive",
            "coverage": "partial",
        }
    )
    doc = _beoordeel(geval["invoer"], respons)
    assert (doc.status, doc.reden) == ("fail", None)
    assert doc.vraag == "Welke aanvrager wordt bedoeld?"


def test_not_applicable_met_reikwijdtegrond():
    respons = {
        "verdict": "not_applicable",
        "passages": [],
        "reason": "De aangeleverde tekst valt buiten het definitietoetsbereik.",
        "question": None,
        "uncertainty": "none",
        "scope_reason": "De tekst is een toelichting bij een tabel, geen definitiekern.",
        "coverage": "none",
    }
    doc = _beoordeel(_basis_invoer(), respons)
    assert (doc.status, doc.reden) == ("not_applicable", None)
    assert doc.melding == NVT.replace(
        "{reikwijdtegrond}", _zonder_slotpunt(respons["scope_reason"])
    )


def _variant(case_id: str, **wijziging):
    geval = _geval(case_id)
    geval["modelrespons"].update(wijziging)
    return geval


INCONSISTENT = {
    # Onbewijsbare pass.
    "pass-zonder-passages": _variant("C116", passages=[]),
    "pass-gedeeltelijke-dekking": _variant("C116", coverage="partial"),
    "pass-geen-dekking": _variant("C116", coverage="none"),
    "pass-beslissende-onzekerheid": _variant("C116", uncertainty="decisive"),
    "pass-met-vraag": _variant("C116", question="Is dit een afleiding?"),
    "pass-met-reikwijdtegrond": _variant("C116", scope_reason="buiten bereik"),
    "pass-met-onduidelijke-passage": _variant(
        "C107", verdict="pass", uncertainty="none", question=None
    ),
    "pass-met-voorschrift": _variant("C105", verdict="pass"),
    # Fail zonder bewezen gebrek.
    "fail-zonder-gebrek": _variant("C116", verdict="fail"),
    "fail-zonder-passages": _variant("C105", passages=[]),
    "fail-met-twee-vragen": _variant("C105", question="Wie? Wanneer?"),
    # Onvoldoende informatie zonder precies één vraag, of met bewezen gebrek.
    "o-zonder-vraag": _variant("C107", question=None),
    "o-met-twee-vragen": _variant("C107", question="Wat is bedoeld? Welke bron geldt?"),
    "o-vraag-zonder-vraagteken": _variant("C107", question="Geef de bedoeling."),
    "o-lege-vraag": _variant("C107", question="  "),
    "o-zonder-beslissende-onzekerheid": _variant("C107", uncertainty="none"),
    "o-met-bewezen-gebrek": _variant(
        "C105",
        verdict="insufficient_information",
        question="Wie?",
        uncertainty="decisive",
    ),
    # Niet van toepassing zonder reikwijdtegrond of voor een afleiding.
    "na-zonder-reikwijdtegrond": _variant(
        "C116", verdict="not_applicable", passages=[], coverage="none"
    ),
    "na-voor-afleiding": _variant(
        "C116",
        verdict="not_applicable",
        scope_reason="Rekenregel, geen definitie.",
        coverage="none",
    ),
    "na-met-dekking": _variant(
        "C116",
        verdict="not_applicable",
        passages=[],
        scope_reason="Buiten bereik.",
        coverage="complete",
    ),
    "na-met-vraag": _variant(
        "C116",
        verdict="not_applicable",
        passages=[],
        scope_reason="Buiten bereik.",
        coverage="none",
        question="Is dit een definitie?",
    ),
}


@pytest.mark.parametrize("geval", list(INCONSISTENT.values()), ids=list(INCONSISTENT))
def test_inconsistent_oordeel_is_technische_fout_zonder_reparatie(geval):
    respons = copy.deepcopy(geval["modelrespons"])
    doc = _beoordeel(geval["invoer"], respons)
    assert (doc.status, doc.foutcategorie, doc.melding) == (
        "error",
        "invalid_output",
        E,
    )
    assert doc.oordeel is None
    assert respons == geval["modelrespons"]


def test_niet_beslissende_onzekerheid_blokkeert_pass_niet():
    geval = _variant("C116", uncertainty="non_decisive")
    assert _beoordeel(geval["invoer"], geval["modelrespons"]).status == "pass"


# --- Niet uitgevoerd en technische fout -----------------------------------------


@pytest.mark.parametrize(
    ("kern", "context", "ontbreekt"),
    [
        ("", ["loket"], "kern"),
        ("   \n", ["loket"], "kern"),
        ("Toegang:", ["loket"], "kern"),
        ("Geheel getal dat zonder rest door twee deelbaar is.", [], "context"),
        ("Toegang:", [], "kern en context"),
        ("Geheel getal dat zonder rest door twee deelbaar is.", ["loket"], None),
    ],
    ids=["leeg", "witruimte", "label", "geen-context", "beide", "compleet"],
)
def test_ontbrekende_invoer(kern, context, ontbreekt):
    data = {**_basis_invoer(), "kern": kern, "organisatorische_context": context}
    data.update({"juridische_context": [], "wettelijke_basis": []})
    assert ontbrekende_invoer(maak_invoer(**data)) == ontbreekt


def test_niet_uitgevoerd_negeert_meegegeven_oordeel():
    data = _geval("C56")["invoer"]
    kern = data["kern"]
    quote = "indien hij in de vijf jaar voorafgaand aan het laatste feit"
    start = kern.index(quote)
    respons = copy.deepcopy(_geval("C116")["modelrespons"])
    respons["passages"][0].update(
        {
            "quote": quote,
            "start": start,
            "end": start + len(quote),
            "function": "criterion",
        }
    )
    respons["passages"][0]["ground"] = _grond("kern")
    doc = _beoordeel(data, respons)
    assert doc.status == "not_evaluated"
    assert doc.melding == NE.replace("{kern/context}", "context")
    assert doc.oordeel is None


def test_label_zonder_kern_is_niet_uitgevoerd_ook_bij_na_oordeel():
    data = {**_basis_invoer(), "kern": "Toegang:"}
    respons = {
        "verdict": "not_applicable",
        "passages": [],
        "reason": "Geen definitie.",
        "question": None,
        "uncertainty": "none",
        "scope_reason": "Alleen een label.",
        "coverage": "none",
    }
    doc = _beoordeel(data, respons)
    assert doc.status == "not_evaluated"
    assert doc.melding == NE.replace("{kern/context}", "kern")


def test_transportfout_negeert_meegegeven_uitvoer():
    geval = _geval("C116")
    doc = _beoordeel(
        geval["invoer"],
        geval["modelrespons"],
        status="failed",
        foutcategorie="transport",
    )
    assert (doc.status, doc.foutcategorie, doc.melding) == ("error", "transport", E)
    assert doc.oordeel is None


# --- Woordpatronen hebben geen normatieve rol -----------------------------------


def test_voorwaardewoord_leidt_niet_tot_afkeur():
    data = {
        **_basis_invoer(),
        "kern": "Getal dat even is indien het zonder rest door twee deelbaar is.",
    }
    data["bedoeling"] = None
    quote = "indien het zonder rest door twee deelbaar is"
    respons = copy.deepcopy(_geval("C116")["modelrespons"])
    respons["passages"][0] = {
        "quote": quote,
        "start": 18,
        "end": 18 + len(quote),
        "function": "criterion",
        "ground": _grond("kern", None, quote, 18, 18 + len(quote)),
    }
    assert _beoordeel(data, respons).status == "pass"


def test_code_overrulet_modelfunctie_niet_op_woorden():
    data = {
        **_basis_invoer(),
        "kern": "Geheel getal dat zonder rest door twee deelbaar is.",
    }
    data["bedoeling"] = None
    kern = data["kern"]
    respons = copy.deepcopy(_geval("C105")["modelrespons"])
    respons["passages"][0].update({"quote": kern, "start": 0, "end": len(kern)})
    respons["passages"][0]["ground"] = _grond("kern")
    # Geen signaalwoord in de kern: de code bewijst geen semantiek en keurt
    # de (handmatig ingevulde) functie niet op woorden goed of af.
    assert _beoordeel(data, respons).status == "fail"


# --- Uitvoeringsmetadata -------------------------------------------------------


def test_ontbrekende_metingen_zijn_expliciet_onbekend():
    uitvoering = _uitvoering()
    for veld in (
        "tijdstip",
        "transportpogingen",
        "invoertokens",
        "uitvoertokens",
        "duur_ms",
        "kosten",
        "modelversie",
    ):
        assert getattr(uitvoering, veld) == ONBEKEND, veld
    assert uitvoering.foutcategorie is None


def test_gerapporteerde_metingen_blijven_behouden_in_document():
    uitvoering = _uitvoering(
        actor="human",
        tijdstip="2026-09-26T12:00:00+00:00",
        transportpogingen=1,
        invoertokens=812,
        uitvoertokens=240,
        duur_ms=1530,
        kosten=Decimal("0.0042"),
        modelversie="fake-model-1-20260901",
    )
    geval = _geval("C116")
    doc = beoordeel(
        maak_invoer(**geval["invoer"]),
        _configuratie(),
        geval["modelrespons"],
        uitvoering,
    )
    assert doc.uitvoering == uitvoering
    assert doc.status == "pass"
    metadata = doc.als_dict()["uitvoering"]
    assert (metadata["actor"], metadata["invoertokens"], metadata["kosten"]) == (
        "human",
        812,
        "0.0042",
    )


@pytest.mark.parametrize(
    "wijziging",
    [
        {"transportpogingen": True},
        {"invoertokens": -1},
        {"uitvoertokens": "240"},
        {"duur_ms": 1.5},
        {"kosten": 0.5},
        {"tijdstip": 123},
        {"actor": "robot"},
        {"status": "done"},
        {"status": "failed"},
        {"foutcategorie": "timeout"},
        {"status": "failed", "foutcategorie": "invalid_citation"},
        {"status": "failed", "foutcategorie": "boom"},
    ],
    ids=[
        "pogingen-bool",
        "tokens-negatief",
        "tokens-str",
        "duur-float",
        "kosten-float",
        "tijdstip-int",
        "actor-onbekend",
        "status-onbekend",
        "fout-zonder-categorie",
        "voltooid-met-categorie",
        "codecategorie-als-transportfout",
        "categorie-onbekend",
    ],
)
def test_ongeldige_uitvoeringsmetadata_wordt_geweigerd(wijziging):
    with pytest.raises(Int02ContractError):
        _uitvoering(**wijziging)


# --- Gepubliceerd contractdocument ---------------------------------------------


def test_contractdocument_legt_versies_en_exacte_meldingen_vast():
    tekst = CONTRACTDOC.read_text(encoding="utf-8")
    for verplicht in (
        "def835-int02-assessment/1",
        "def771-int02/2",
        V,
        VN,
        VN_DISCRETIE,
        ONVOLDOENDE,
        NE,
        E,
        HISTORISCH,
        NIET_BEOORDEELD,
        NVT,
    ):
        assert verplicht in tekst, verplicht
