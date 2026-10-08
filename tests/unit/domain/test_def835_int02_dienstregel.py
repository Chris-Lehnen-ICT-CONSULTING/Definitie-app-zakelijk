"""DEF-835 besluit 12 (optie A): smalle dienstregel discretie zonder bedoeling.

Contract def835-int02-assessment/3. Geeft de beoordelaar (een model, actor
`ai`) `fail`, is de bevestigde bedoeling onbekend (`None`) en hebben ALLE
passages die de fail dragen functie `discretionary_decision_rule` met als
grond uitsluitend het veld `kern`, dan is de uitkomst `review_required` /
`insufficient_information` in plaats van `fail`. De omzetting is zichtbaar
(`Beoordelingsdocument.omzetting == "discretie_zonder_bedoeling"`), de vraag
is de vaste, invoeronafhankelijke vraag uit het contract en het bewaarde
oordeel blijft de geaccepteerde modeluitvoer (verdict `fail`, citaten en
posities zoals onder /2). Er komt geen pass-pad bij.

Draagt minstens één passage de fail anders (een `actor_prescription`, of een
discretionaire beslisregel met grond uit begrip, bedoeling, context of
bronpassage), dan blijft het `fail` (besluit 1: een expliciet actorvoorschrift
in de kern mag een fail dragen).

Keuze bij de vraag (besluit 12, gedocumenteerd in
`int02_assessment_contract_v3.md`): altijd de vaste vraag, ook als het model
bij zijn fail zelf een vraag gaf. Die modelvraag blijft zichtbaar in het
oordeel (`oordeel["question"]`).

Bewaarde /1- en /2-documenten blijven volgens hun eigen versie controleerbaar
en worden historisch. Het /2-document hier is het in kwalificatieproef v5
door de echte /2-code bewaarde document van C107; de ruwe modeluitvoer komt
letterlijk uit dezelfde proef (`kwalificatieproef-v5/regressie-bundel.json`).
Er wordt geen andere goldset- of hold-outinhoud gebruikt.

Sinds /4 (besluit 16) is deze dienstregel de laatste tak van de beslisregel;
de losse regel van /3 blijft gelden voor bewaarde /3-documenten. De module
draait daarom met /3 als actuele versie (`contract_drie`).
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path

import pytest

from domain.int02 import contract as int02_contract
from domain.int02.contract import (
    MELDING_E,
    MELDING_HISTORISCH,
    Beoordelingsdocument,
    Binding,
    Configuratie,
    Uitvoering,
    beoordeel,
    bereken_binding,
    maak_invoer,
    toets_actualiteit,
)
from services.ai.base_client import response_schema_sha256
from services.interfaces import AIGenerationResult
from services.validation.int02_assessment_service import (
    PROMPT_VERSION,
    Budget,
    Int02AssessmentService,
    Modelprofiel,
    bouw_int02_prompt,
    laad_int02_norm,
)

pytestmark = [pytest.mark.unit]

ROOT = Path(__file__).resolve().parents[3]
V5 = (
    ROOT / "docs/analyses/def606-regeldossiers/INT-02-verdieping/"
    "onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/"
    "goldset-freeze-v1/kwalificatieproef-v5"
)

V4 = "def835-int02-assessment/4"
V3 = "def835-int02-assessment/3"
V2 = "def835-int02-assessment/2"


@pytest.fixture(autouse=True)
def contract_drie(monkeypatch):
    """Besluit 16: /3 als actuele versie (zie moduledocstring)."""
    monkeypatch.setattr(int02_contract, "CONTRACTVERSIE", V3)


OMZETTING = "discretie_zonder_bedoeling"
VRAAG = (
    "Is de bedoeling dat deze passage een begripskenmerk beschrijft of de actor "
    "een afweging voorschrijft?"
)
#: Systeemprompt /3 volgens kwalificatie-manifest-v5 (`systeemprompt_sha256`).
SYSTEEMPROMPT_V3_SHA256 = (
    "da4a4112b580da2924b5940ac2723ef5e177ad48ef15890b66d8d91f285a7ca6"
)
#: SHA-256 van de systeemprompt van def835-int02-prompt/5 (besluit 16);
#: historische controle sinds /6.
SYSTEEMPROMPT_V5_SHA256 = (
    "3047bb1a34f878e77bd434d668d870f0dfcfb92e3e948ac0caee77af9c2d2b70"
)
#: SHA-256 van de systeemprompt van def835-int02-prompt/6 (besluit 19).
SYSTEEMPROMPT_V6_SHA256 = (
    "a8f701ac3ec262f44efa3415d34e4931f4b637eb4d430b33aa8694d77e89d8e7"
)

C107_KERN = (
    "Aanvraag die naar het gemotiveerde oordeel van de beoordelaar voldoende "
    "onderbouwd is."
)
C107_CITAAT = "naar het gemotiveerde oordeel van de beoordelaar voldoende onderbouwd is"
KERN_VOORSCHRIFT = (
    "Aanvraag die de behandelaar moet afwijzen, tenzij hij van oordeel is dat "
    "de aanvrager onevenredig wordt benadeeld."
)
VOORSCHRIFT = "de behandelaar moet afwijzen"
DISCRETIE = "tenzij hij van oordeel is dat de aanvrager onevenredig wordt benadeeld"
KENMERK = "Aanvraag die"


def _melding_o(citaat: str) -> str:
    return (
        "INT-02 — Onvoldoende informatie. De bevestigde bedoeling is onbekend; "
        f"alleen de kern zelf draagt de lezing van '{citaat}' als discretionaire "
        f"beslisregel. Vraag: {VRAAG}"
    )


# --- v5-bewijs ---------------------------------------------------------------------


def _v5_resultaat_c107() -> dict:
    resultaat = json.loads((V5 / "regressie-resultaat.json").read_text("utf-8"))
    (geval,) = [g for g in resultaat["gevallen"] if g["id"] == "C107"]
    return geval


def _c107_ruw_v5() -> str:
    """De ruwe modeltekst van C107 uit kwalificatieproef v5, letterlijk."""
    bundel = json.loads((V5 / "regressie-bundel.json").read_text("utf-8"))
    antwoord = json.loads(bundel["antwoorden"]["C107"])
    (blok,) = antwoord["content"]
    assert blok["type"] == "text"
    return blok["text"]


def _c107_uitvoer_v5() -> dict:
    return json.loads(_c107_ruw_v5())


# --- synthetische opbouw -------------------------------------------------------------


def _configuratie() -> Configuratie:
    return Configuratie(
        normhash=hashlib.sha256(b"testnorm def771-int02/2").hexdigest(),
        promptversie="def835-int02-prompt/3",
        routeringshash=hashlib.sha256(b"testroutering").hexdigest(),
        provider="fake-provider",
        model="fake-model-1",
    )


def _uitvoering(actor: str = "ai") -> Uitvoering:
    return Uitvoering(actor=actor, status="completed")


def _invoerdata(kern: str = C107_KERN, **over) -> dict:
    data = {
        "begrip": "voldoende onderbouwde aanvraag",
        "kern": kern,
        "bedoeling": None,
        "organisatorische_context": ["synthetische begrippenstudie"],
        "juridische_context": [],
        "wettelijke_basis": [],
        "bronnen": [{"id": "B1", "tekst": "Synthetische bron over een afweging."}],
    }
    data.update(over)
    return data


def _invoer(kern: str = C107_KERN, **over):
    return maak_invoer(**_invoerdata(kern, **over))


def _grond(field="kern", ref=None, quote=None) -> dict:
    return {"field": field, "ref": ref, "quote": quote}


def _passage(quote: str, function: str, ground: dict | None = None) -> dict:
    return {"quote": quote, "function": function, "ground": ground or _grond()}


def _uitvoer(verdict: str, *passages: dict, **over) -> dict:
    uitvoer = {
        "verdict": verdict,
        "passages": list(passages),
        "reason": "Synthetische onderbouwing.",
        "question": None,
        "uncertainty": "none",
        "scope_reason": None,
        "coverage": "complete",
    }
    uitvoer.update(over)
    return uitvoer


def _beoordeel(invoer, uitvoer, actor: str = "ai") -> Beoordelingsdocument:
    return beoordeel(invoer, _configuratie(), uitvoer, _uitvoering(actor))


def _herhaal(document: Beoordelingsdocument):
    return toets_actualiteit(document, document.invoer, _configuratie())


# --- versie en schema ------------------------------------------------------------------


def test_contractversie_is_drie():
    binding = bereken_binding(_invoer(), _configuratie())
    assert binding.contractversie == V3
    doc = _beoordeel(_invoer(), _c107_uitvoer_v5())
    assert doc.contractversie == V3


def test_vaste_vraag_is_precies_een_vraag_en_invoeronafhankelijk():
    assert VRAAG.count("?") == 1 and VRAAG.endswith("?")
    for kern, citaat in ((C107_KERN, C107_CITAAT), (KERN_VOORSCHRIFT, DISCRETIE)):
        uitvoer = _uitvoer("fail", _passage(citaat, "discretionary_decision_rule"))
        assert _beoordeel(_invoer(kern), uitvoer).vraag == VRAAG


def test_document_zonder_omzetting_draagt_het_veld_als_none():
    uitvoer = _uitvoer("fail", _passage(VOORSCHRIFT, "actor_prescription"))
    doc = _beoordeel(_invoer(KERN_VOORSCHRIFT), uitvoer)
    assert doc.omzetting is None
    assert doc.als_dict()["omzetting"] is None


# --- (a) C107-vorm uit v5 → review_required / insufficient_information ---------------


def test_ruwe_v5_uitvoer_is_letterlijk_die_uit_de_proef():
    ruw = _c107_ruw_v5()
    geval = _v5_resultaat_c107()
    assert hashlib.sha256(ruw.encode("utf-8")).hexdigest() == geval["antwoord_sha256"]
    assert geval["document"]["invoer"]["kern"] == C107_KERN
    assert geval["document"]["invoer"]["bedoeling"] is None


def test_c107_v5_fail_wordt_review_required_met_vaste_vraag_en_omzetting():
    invoer = maak_invoer(**_v5_resultaat_c107()["document"]["invoer"])
    uitvoer = _c107_uitvoer_v5()
    assert uitvoer["verdict"] == "fail"  # het model gaf fail

    doc = _beoordeel(invoer, uitvoer)

    assert (doc.status, doc.reden) == ("review_required", "insufficient_information")
    assert doc.omzetting == OMZETTING
    assert doc.vraag == VRAAG
    assert doc.melding == _melding_o(C107_CITAAT)
    assert (doc.foutcategorie, doc.foutdetail) == (None, None)
    data = doc.als_dict()
    assert data["omzetting"] == OMZETTING
    assert data["status"] == "review_required"
    # Het bewaarde oordeel blijft de geaccepteerde modeluitvoer (zichtbaar fail),
    # met de citaten en posities zoals onder /2.
    oordeel = doc.oordeel
    assert oordeel["verdict"] == "fail"
    (passage,) = oordeel["passages"]
    assert (passage["start"], passage["end"]) == (13, 85)
    assert (passage["ground"]["start"], passage["ground"]["end"]) == (13, 85)
    assert passage["function"] == "discretionary_decision_rule"
    assert oordeel["reason"] == uitvoer["reason"]
    # Geen pass-pad en de meegegeven uitvoer is niet gewijzigd.
    assert uitvoer == _c107_uitvoer_v5()
    actueel = toets_actualiteit(doc, invoer, _configuratie())
    assert (actueel.status, actueel.reden, actueel.melding) == (
        "review_required",
        "insufficient_information",
        doc.melding,
    )


@pytest.mark.parametrize("grondcitaat", [None, C107_CITAAT, "beoordelaar"])
def test_discretie_met_kerngrond_met_of_zonder_grondcitaat_wordt_omgezet(grondcitaat):
    uitvoer = _uitvoer(
        "fail",
        _passage(C107_CITAAT, "discretionary_decision_rule", _grond(quote=grondcitaat)),
        uncertainty="non_decisive",
    )
    doc = _beoordeel(_invoer(), uitvoer)
    assert (doc.status, doc.reden, doc.omzetting) == (
        "review_required",
        "insufficient_information",
        OMZETTING,
    )


def test_niet_dragende_passages_tellen_niet_mee():
    # Een begripscriterium met grond uit een bron draagt de fail niet; de
    # enige dragende passage is discretionair op grond van de kern.
    uitvoer = _uitvoer(
        "fail",
        _passage(KENMERK, "criterion", _grond("bron", "B1")),
        _passage(DISCRETIE, "discretionary_decision_rule"),
        _passage(VOORSCHRIFT, "unclear", _grond("organisatorische_context", 0)),
    )
    doc = _beoordeel(_invoer(KERN_VOORSCHRIFT), uitvoer)
    assert (doc.status, doc.omzetting) == ("review_required", OMZETTING)
    assert doc.melding == _melding_o(DISCRETIE)


def test_meerdere_discretionaire_kernpassages_noemen_de_eerste():
    uitvoer = _uitvoer(
        "fail",
        _passage(DISCRETIE, "discretionary_decision_rule"),
        _passage(VOORSCHRIFT, "discretionary_decision_rule"),
    )
    doc = _beoordeel(_invoer(KERN_VOORSCHRIFT), uitvoer)
    assert (doc.status, doc.omzetting) == ("review_required", OMZETTING)
    assert doc.melding == _melding_o(VOORSCHRIFT)  # eerste op afgeleide start


# --- (b) bedoeling bekend → blijft fail -------------------------------------------------


def test_c107_v5_met_bekende_bedoeling_blijft_fail():
    invoer = _invoer(bedoeling="Synthetische bedoeling: een afweging door de actor.")
    doc = _beoordeel(invoer, _c107_uitvoer_v5())
    assert (doc.status, doc.reden, doc.omzetting) == ("fail", None, None)
    assert doc.vraag is None
    assert doc.melding.startswith("INT-02 — Voldoet niet.")


# --- (c) actorvoorschrift in de kern, bedoeling onbekend → blijft fail (besluit 1) --


@pytest.mark.parametrize("grondcitaat", [None, VOORSCHRIFT])
def test_actorvoorschrift_met_kerngrond_zonder_bedoeling_blijft_fail(grondcitaat):
    uitvoer = _uitvoer(
        "fail", _passage(VOORSCHRIFT, "actor_prescription", _grond(quote=grondcitaat))
    )
    doc = _beoordeel(_invoer(KERN_VOORSCHRIFT), uitvoer)
    assert (doc.status, doc.reden, doc.omzetting) == ("fail", None, None)
    assert "schrijft een handeling voor" in doc.melding


# --- (d) discretionair/kern naast actorvoorschrift → blijft fail -----------------------


@pytest.mark.parametrize("volgorde", ["discretie-eerst", "voorschrift-eerst"])
def test_discretie_naast_actorvoorschrift_blijft_fail(volgorde):
    passages = [
        _passage(DISCRETIE, "discretionary_decision_rule"),
        _passage(VOORSCHRIFT, "actor_prescription"),
    ]
    if volgorde == "voorschrift-eerst":
        passages.reverse()
    doc = _beoordeel(_invoer(KERN_VOORSCHRIFT), _uitvoer("fail", *passages))
    assert (doc.status, doc.reden, doc.omzetting) == ("fail", None, None)


# --- (e) discretionair met andere grond, bedoeling onbekend → blijft fail --------------


@pytest.mark.parametrize(
    "grond",
    [
        _grond("organisatorische_context", 0),
        _grond("organisatorische_context", 0, "begrippenstudie"),
        _grond("bron", "B1"),
        _grond("bron", "B1", "een afweging"),
        _grond("begrip"),
    ],
    ids=["context", "context-citaat", "bron", "bron-citaat", "begrip"],
)
def test_discretie_met_andere_grond_zonder_bedoeling_blijft_fail(grond):
    uitvoer = _uitvoer(
        "fail", _passage(C107_CITAAT, "discretionary_decision_rule", grond)
    )
    doc = _beoordeel(_invoer(), uitvoer)
    assert (doc.status, doc.reden, doc.omzetting) == ("fail", None, None)


def test_discretie_naast_discretie_met_contextgrond_blijft_fail():
    uitvoer = _uitvoer(
        "fail",
        _passage(DISCRETIE, "discretionary_decision_rule"),
        _passage(
            VOORSCHRIFT,
            "discretionary_decision_rule",
            _grond("organisatorische_context", 0),
        ),
    )
    doc = _beoordeel(_invoer(KERN_VOORSCHRIFT), uitvoer)
    assert (doc.status, doc.omzetting) == ("fail", None)


def test_bedoelingsgrond_bij_onbekende_bedoeling_blijft_een_fout():
    # Ongewijzigd /2-gedrag: een onbekende bedoeling is geen grond (C117).
    uitvoer = _uitvoer(
        "fail",
        _passage(C107_CITAAT, "discretionary_decision_rule", _grond("bedoeling")),
    )
    doc = _beoordeel(_invoer(), uitvoer)
    assert (doc.status, doc.foutcategorie, doc.omzetting) == (
        "error",
        "invalid_citation",
        None,
    )


# --- (f) pass, onvoldoende, NA, NE, niet uitgevoerd en fout blijven ongewijzigd ---------


@pytest.mark.parametrize(
    ("uitvoer", "status", "reden"),
    [
        (_uitvoer("pass", _passage(C107_CITAAT, "criterion")), "pass", None),
        (
            _uitvoer(
                "insufficient_information",
                _passage(C107_CITAAT, "unclear"),
                question="Welke maatstaf hanteert de beoordelaar?",
                uncertainty="decisive",
                coverage="partial",
            ),
            "review_required",
            "insufficient_information",
        ),
        (
            _uitvoer(
                "not_applicable",
                scope_reason="Synthetische reikwijdtegrond.",
                coverage="none",
            ),
            "not_applicable",
            None,
        ),
    ],
    ids=["pass", "onvoldoende", "nvt"],
)
def test_andere_verdicts_blijven_ongewijzigd(uitvoer, status, reden):
    doc = _beoordeel(_invoer(), uitvoer)
    assert (doc.status, doc.reden, doc.omzetting) == (status, reden, None)
    assert doc.vraag == uitvoer["question"]
    if status == "review_required":
        assert doc.melding.endswith("Vraag: Welke maatstaf hanteert de beoordelaar?")


def test_ontbrekende_invoer_mislukte_en_niet_uitgevoerde_beoordeling_blijven():
    uitvoer = _c107_uitvoer_v5()
    zonder_context = _invoer(organisatorische_context=[])
    assert _beoordeel(zonder_context, uitvoer).status == "not_evaluated"
    mislukt = Uitvoering(actor="ai", status="failed", foutcategorie="timeout")
    doc = beoordeel(_invoer(), _configuratie(), uitvoer, mislukt)
    assert (doc.status, doc.omzetting) == ("error", None)
    niet = Uitvoering(actor="ai", status="not_executed")
    doc = beoordeel(_invoer(), _configuratie(), None, niet)
    assert (doc.status, doc.reden, doc.omzetting) == (
        "review_required",
        "not_assessed",
        None,
    )


def test_ongeldige_fail_uitvoer_blijft_error_en_wordt_niet_omgezet():
    uitvoer = _c107_uitvoer_v5()
    uitvoer["passages"][0]["quote"] = "niet in de kern"
    doc = _beoordeel(_invoer(), uitvoer)
    assert (doc.status, doc.foutdetail, doc.omzetting) == (
        "error",
        "niet_gevonden",
        None,
    )


def test_menselijke_beoordelaar_wordt_niet_omgezet():
    # Besluit 12 betreft de modeluitvoer; een menselijk oordeel blijft fail.
    doc = _beoordeel(_invoer(), _c107_uitvoer_v5(), actor="human")
    assert (doc.status, doc.omzetting) == ("fail", None)


# --- (g) model gaf zelf al een vraag → toch de vaste vraag --------------------------------


def test_modelvraag_bij_fail_wordt_niet_overgenomen_maar_blijft_zichtbaar():
    modelvraag = "Geldt voor de beoordelaar een openbaar beoordelingskader?"
    uitvoer = _c107_uitvoer_v5()
    uitvoer["question"] = modelvraag
    doc = _beoordeel(_invoer(), uitvoer)
    assert (doc.status, doc.omzetting) == ("review_required", OMZETTING)
    assert doc.vraag == VRAAG
    assert doc.melding == _melding_o(C107_CITAAT)
    assert modelvraag not in doc.melding
    assert doc.oordeel["question"] == modelvraag


# --- (h) hercontrole stabiel; manipulatie van de omzetting → error -------------------------


def _omgezet() -> Beoordelingsdocument:
    return _beoordeel(_invoer(), _c107_uitvoer_v5())


def test_hercontrole_van_een_omgezet_document_is_stabiel():
    doc = _omgezet()
    assert _beoordeel(_invoer(), _c107_uitvoer_v5()) == doc
    voor = doc.als_dict()
    for _ in range(2):
        actueel = _herhaal(doc)
        assert (actueel.status, actueel.reden, actueel.melding) == (
            "review_required",
            "insufficient_information",
            doc.melding,
        )
    assert doc.als_dict() == voor


@pytest.mark.parametrize(
    "wijziging",
    [
        {"omzetting": None},
        {"omzetting": "iets_anders"},
        {"omzetting": "discretie_zonder_bedoeling "},
        {"status": "fail", "reden": None},
        {"status": "fail", "reden": None, "omzetting": None},
        {"vraag": None},
        {"vraag": "Wat is bedoeld?"},
        {"reden": "historical"},
    ],
    ids=[
        "omzetting-weg",
        "omzetting-anders",
        "omzetting-spatie",
        "terug-naar-fail",
        "terug-naar-fail-zonder-omzetting",
        "vraag-weg",
        "vraag-anders",
        "reden-anders",
    ],
)
def test_gemanipuleerd_omgezet_document_is_error(wijziging):
    doc = dataclasses.replace(_omgezet(), **wijziging)
    actueel = _herhaal(doc)
    assert (actueel.status, actueel.melding) == ("error", MELDING_E)


def test_omgezet_document_met_andere_melding_is_error():
    doc = _omgezet()
    vn = _beoordeel(_invoer(bedoeling="Synthetische bedoeling."), _c107_uitvoer_v5())
    gemanipuleerd = dataclasses.replace(doc, melding=vn.melding)
    assert _herhaal(gemanipuleerd).status == "error"


@pytest.mark.parametrize("basis", ["fail", "pass", "onvoldoende"])
def test_omzetting_op_een_niet_omgezet_document_is_error(basis):
    if basis == "fail":
        doc = _beoordeel(
            _invoer(KERN_VOORSCHRIFT),
            _uitvoer("fail", _passage(VOORSCHRIFT, "actor_prescription")),
        )
    elif basis == "pass":
        doc = _beoordeel(
            _invoer(), _uitvoer("pass", _passage(C107_CITAAT, "criterion"))
        )
    else:
        doc = _beoordeel(
            _invoer(),
            _uitvoer(
                "insufficient_information",
                _passage(C107_CITAAT, "unclear"),
                question="Welke maatstaf geldt?",
                uncertainty="decisive",
            ),
        )
    assert _herhaal(doc).status == doc.status  # ongemanipuleerd actueel
    gemanipuleerd = dataclasses.replace(doc, omzetting=OMZETTING)
    assert _herhaal(gemanipuleerd).status == "error"


def test_omgezet_document_met_gewijzigd_oordeel_is_error():
    doc = _omgezet()
    oordeel = doc.oordeel
    oordeel["passages"][0]["function"] = "actor_prescription"
    gemanipuleerd = dataclasses.replace(
        doc, oordeel_json=json.dumps(oordeel, ensure_ascii=False, sort_keys=True)
    )
    assert _herhaal(gemanipuleerd).status == "error"


def test_bewijsgrens_gewijzigde_bewaarde_modelvraag_is_niet_aantoonbaar():
    # Review Codex 07-10-2026: na een omzetting hangen vraag en melding niet
    # van de modelvraag af. Een consistente wijziging van `oordeel.question`
    # (nog steeds precies één vraag) is daardoor niet uit de samenhang af te
    # leiden; dat is authenticiteit en hoort bij de opslaglaag (DEF-626).
    doc = _omgezet()
    oordeel = doc.oordeel
    oordeel["question"] = "Is dit een andere, achteraf ingevoegde vraag?"
    gemanipuleerd = dataclasses.replace(
        doc, oordeel_json=json.dumps(oordeel, ensure_ascii=False, sort_keys=True)
    )
    assert _herhaal(gemanipuleerd).status == "review_required"
    # Een vormfout in die vraag valt wel op (samenhang van een fail).
    oordeel["question"] = "Twee vragen? Echt?"
    vormfout = dataclasses.replace(
        doc, oordeel_json=json.dumps(oordeel, ensure_ascii=False, sort_keys=True)
    )
    assert _herhaal(vormfout).status == "error"


# --- (i) /2-document → historisch, niet error ------------------------------------------------


def _v2_proefdocument() -> Beoordelingsdocument:
    """Het in kwalificatieproef v5 door de /2-code bewaarde C107-document."""
    data = _v5_resultaat_c107()["document"]
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


def _actualiteit_v2(document: Beoordelingsdocument):
    """Actueel = dezelfde invoer en configuratie; alleen de contractversie verschilt."""
    return toets_actualiteit(document, document.invoer, document.binding.configuratie())


def test_v2_proefdocument_is_een_fail_onder_contract_2():
    doc = _v2_proefdocument()
    assert doc.contractversie == doc.binding.contractversie == V2
    assert (doc.status, doc.omzetting) == ("fail", None)
    assert doc.oordeel["passages"][0]["function"] == "discretionary_decision_rule"


def test_v2_proefdocument_wordt_historisch_en_niet_omgezet_of_error():
    doc = _v2_proefdocument()
    voor = doc.als_dict()
    actueel = _actualiteit_v2(doc)
    assert (actueel.status, actueel.reden, actueel.melding) == (
        "review_required",
        "historical",
        MELDING_HISTORISCH,
    )
    assert doc.als_dict() == voor  # het bewaarde document blijft ongewijzigd


def test_zelfde_uitvoer_onder_contract_3_wordt_wel_omgezet():
    oud = _v2_proefdocument()
    nieuw = beoordeel(
        oud.invoer,
        oud.binding.configuratie(),
        _c107_uitvoer_v5(),
        Uitvoering(actor="ai", status="completed"),
    )
    assert (nieuw.status, nieuw.omzetting) == ("review_required", OMZETTING)
    # Zelfde oordeel en posities als onder /2; alleen de uitkomst verschilt.
    assert nieuw.oordeel == oud.oordeel
    actueel = toets_actualiteit(nieuw, oud.invoer, oud.binding.configuratie())
    assert actueel.reden == "insufficient_information"


@pytest.mark.parametrize(
    "wijziging",
    [
        {"omzetting": OMZETTING},
        {
            "omzetting": OMZETTING,
            "status": "review_required",
            "reden": "insufficient_information",
        },
        {"status": "pass"},
        {"melding": MELDING_HISTORISCH},
    ],
    ids=["omzetting-erbij", "als-omgezet", "status", "melding"],
)
def test_gemanipuleerd_v2_proefdocument_is_error(wijziging):
    doc = dataclasses.replace(_v2_proefdocument(), **wijziging)
    actueel = _actualiteit_v2(doc)
    assert (actueel.status, actueel.melding) == ("error", MELDING_E)


def test_v2_proefdocument_als_v3_gelabeld_is_error():
    doc = _v2_proefdocument()
    doc = dataclasses.replace(
        doc,
        contractversie=V3,
        binding=dataclasses.replace(doc.binding, contractversie=V3),
    )
    # Onder /3 hoort bij dit oordeel de omzetting; het /2-document mist die.
    assert _actualiteit_v2(doc).status == "error"


# --- dienst: de ruwe v5-tekst via de echte dienst; prompt /3 ongewijzigd -------------------


class _Router:
    def get_model(self, task_type):
        return "fake-provider", "fake-model-1"

    def accepts_temperature(self, model, provider=None):
        return True

    def thinking_default_on(self, model, provider=None):
        return False


class _AI:
    def __init__(self, tekst: str):
        self.tekst = tekst
        self.calls = 0

    async def generate_definition(self, prompt, **kwargs):
        self.calls += 1
        metadata = {"stop_reason": "end_turn"}
        if kwargs.get("response_schema") is not None:
            # Zoals AIServiceV2 (besluit 14): schemahash en bloktypen.
            metadata["response_schema_sha256"] = response_schema_sha256(
                kwargs["response_schema"]
            )
            metadata["content_block_types"] = ["text"]
        return AIGenerationResult(
            text=self.tekst,
            model=kwargs.get("model"),
            tokens_used=None,
            generation_time=0.01,
            cached=False,
            metadata=metadata,
        )


def _dienst(ai: _AI) -> Int02AssessmentService:
    return Int02AssessmentService(
        ai,
        _Router(),
        profiel=Modelprofiel(
            profiel_id="fixture-offline-1",
            provider="fake-provider",
            model="fake-model-1",
            kwalificatie="testfixture; geen kwaliteitsclaim",
        ),
        budget=Budget(
            max_uitvoertokens=6000,
            deadline_seconden=5.0,
            max_invoertekens_veld=2000,
            max_invoertekens_totaal=6000,
            max_antwoordtekens=24000,
        ),
    )


def test_prompt_zes_vervangt_de_systeemprompt_van_drie_tot_vijf():
    # Besluit 14: /4 hield de tekst van /3; besluit 16: /5 vraagt bronfuncties;
    # besluit 19: /6 voegt de herhalingsregel toe.
    assert PROMPT_VERSION == "def835-int02-prompt/6"
    systeem, _ = bouw_int02_prompt(_invoer(), laad_int02_norm())
    digest = hashlib.sha256(systeem.encode("utf-8")).hexdigest()
    assert digest != SYSTEEMPROMPT_V3_SHA256
    assert digest != SYSTEEMPROMPT_V5_SHA256
    # Exacte pin op de /6-systeemprompt.
    assert digest == SYSTEEMPROMPT_V6_SHA256


async def test_dienst_zet_de_ruwe_v5_fail_om_onder_de_regels_van_drie():
    """De ruwe v5-tekst door de echte dienst, met /3 als actuele versie."""
    ai = _AI(_c107_ruw_v5())
    resultaat = await _dienst(ai).assess(_invoer())
    assert ai.calls == 1
    assert resultaat.status == "review_required"
    assert resultaat.reden is None  # geen servicereden: een geaccepteerd oordeel
    document = resultaat.document
    assert (document.reden, document.omzetting, document.vraag) == (
        "insufficient_information",
        OMZETTING,
        VRAAG,
    )
    assert document.binding.contractversie == V3


async def test_dienst_weigert_de_ruwe_v5_tekst_onder_contract_vier(monkeypatch):
    """Besluit 16: de /3-vorm (functie en grond per passage) past niet in /4;
    C107 onder /4 staat in de bronfunctie- en papertests."""
    monkeypatch.setattr(int02_contract, "CONTRACTVERSIE", V4)
    ai = _AI(_c107_ruw_v5())
    resultaat = await _dienst(ai).assess(_invoer())
    assert ai.calls == 1
    assert resultaat.status == "error"
    assert resultaat.document.foutcategorie == "invalid_output"
    assert resultaat.document.binding.contractversie == V4
    assert resultaat.promptversie == "def835-int02-prompt/6"
