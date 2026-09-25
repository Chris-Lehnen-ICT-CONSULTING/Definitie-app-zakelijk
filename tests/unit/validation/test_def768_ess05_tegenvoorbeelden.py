"""DEF-768 / ADR-003: ontwerptegenvoorbeelden naar de foutvormen uit R7.

Synthetische gevallen (geen R7-invoer, -uitvoer of -labels) die de drie open
foutvormen structureel nabootsen, telkens met een positieve variant:

* R705-vorm — een letterlijk, maar niet dragend citaat met een ongegronde
  uitsluiting: de vaste controles laten het door (het fragment bestaat); alleen
  een afwijzing door de verifier voorkomt een oordeel.
* R712-vorm — een indicator die de reden tegenspreekt: `lacks_differentia`
  bestaat niet meer als modelveld (gesloten schema) en volgt uit de
  kenmerkenlijst; een lege lijst geeft altijd `fail`, nooit `pass`. Tweede
  variant: een letterlijke maar lege profielverwijzing als kenmerk — de vaste
  structuur aanvaardt haar, alleen een verifierafwijzing voorkomt toepassing;
  een inhoudelijk kenmerk wordt wel toegepast.
* R719-vorm — een parafrase met ruimere strekking naast een letterlijk
  citaat: na afwijzing geen oordeel; na goedkeuring toont de vaste weergave
  exact de gecontroleerde claim met het citaat, geen nieuwe zin.

De verifier is een stub: deze tests bewijzen dat de keten een afwijzing
correct en fail-closed verwerkt en een goedkeuring exact weergeeft, níet dat
een echte verifier zo'n fout herkent (dat blijft een open semantische vraag
tot een echte modelproef).
"""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

import pytest

from domain.ess05.bewijs import Ess05Concept
from domain.ess05.contract import (
    FOUT_SEMANTISCH,
    STATUS_ERROR,
    STATUS_FAIL,
    STATUS_PASS,
    beoordeel_onderscheid,
)
from tests.fixtures.def768_fakes import (
    concept_uit_spec,
    materiaal_uit_prompt,
    verificatie_voor,
)
from tests.unit.validation.test_def768_ess05_assessment_service import (
    BUREN_E05,
    CONTEXT,
    LENER,
    _service,
)

pytestmark = [pytest.mark.unit]

BEGRIP = "lener"


class _Scenario:
    """Eerste aanroep: concept (eventueel aangepast); tweede: verificatie."""

    def __init__(
        self,
        spec: dict[str, Any],
        *,
        wijzig=None,
        afgekeurd: dict[str, str] | None = None,
    ) -> None:
        self.spec = spec
        self.wijzig = wijzig
        self.afgekeurd = afgekeurd or {}
        self.concept: dict[str, Any] | None = None

    def beoordeling(self, prompt: str) -> Any:
        concept = concept_uit_spec(self.spec, materiaal_uit_prompt(prompt))
        if self.wijzig is not None:
            concept = self.wijzig(concept)
        self.concept = concept
        return concept

    def verificatie(self, _prompt: str) -> dict[str, Any]:
        assert self.concept is not None
        return verificatie_voor(self.concept, uitkomsten=self.afgekeurd)


async def _toets(
    scenario: _Scenario, tekst: str = LENER
) -> tuple[Any, dict[str, Any], dict[str, Any]]:
    ai, svc = _service(scenario.beoordeling, scenario.verificatie)
    doc = (await svc.assess(BEGRIP, tekst, CONTEXT, [], buren=BUREN_E05)).als_dict()
    uitkomst = beoordeel_onderscheid(
        BEGRIP,
        tekst,
        CONTEXT,
        [],
        buren=[b.als_dict() for b in BUREN_E05],
        assessment=doc,
        binding=svc.binding(),
    ).als_dict()
    return ai, doc, uitkomst


def _buurspec(**over: Any) -> dict[str, Any]:
    buur = {
        "neighbour_id": BUREN_E05[0].id,
        "distinction": "distinguished",
        "distinguishing_feature_quote": "met een actuele lening",
        "missing_feature": None,
        "reason": "De kern noemt een actuele lening; een werknemer heeft die niet.",
        "uncertainty": None,
    }
    buur.update(over)
    return {
        "lacks_differentia": False,
        "reason": "De kern noemt een actuele lening bij de instelling.",
        "neighbours": [buur],
        "proposed_neighbours": [],
        "question": None,
    }


def _alle_teksten(uitkomst: dict[str, Any]) -> str:
    return json.dumps(uitkomst, ensure_ascii=False)


# --- R705-vorm: niet-dragend citaat ---------------------------------------------------

NIET_DRAGEND = _buurspec(
    distinguishing_feature_quote="bij de instelling",
    reason="Geen werknemer kan iets bij de instelling hebben.",
)


@pytest.mark.asyncio
async def test_r705_vorm_verifierafwijzing_geeft_geen_oordeel():
    buur = f"neighbour:{BUREN_E05[0].id}"
    ai, doc, uitkomst = await _toets(
        _Scenario(NIET_DRAGEND, afgekeurd={buur: "unsupported"})
    )
    assert [c["task_type"] for c in ai.calls] == ["validation", "ess05_verification"]
    # De vaste controles lieten het concept door: het fragment bestaat letterlijk.
    assert doc["concept"] is not None
    assert (doc["status"], doc["error"]["type"]) == ("error", FOUT_SEMANTISCH)
    assert doc["judgment"] is None
    assert uitkomst["status"] == STATUS_ERROR
    assert "Geen werknemer kan" not in _alle_teksten(uitkomst)


@pytest.mark.asyncio
async def test_r705_vorm_positief_dragend_citaat_voldoet():
    ai, doc, uitkomst = await _toets(_Scenario(_buurspec()))
    assert doc["status"] == "assessed"
    assert uitkomst["status"] == STATUS_PASS


# --- R712-vorm: indicator tegen de reden in -------------------------------------------


def _met_modelindicator(concept: dict[str, Any]) -> dict[str, Any]:
    return {**concept, "lacks_differentia": False}


@pytest.mark.asyncio
async def test_r712_vorm_modelindicator_is_een_structuurfout_zonder_verifier():
    spec = _buurspec(
        distinction="not_distinguished",
        distinguishing_feature_quote=None,
        missing_feature="een eigen kenmerk",
    )
    spec["lacks_differentia"] = True
    ai, doc, uitkomst = await _toets(_Scenario(spec, wijzig=_met_modelindicator))
    assert [c["task_type"] for c in ai.calls] == ["validation"]
    assert doc["status"] == "error"
    assert doc["error"]["type"] == "malformed_response"
    assert uitkomst["status"] == STATUS_ERROR


@pytest.mark.asyncio
async def test_r712_vorm_lege_kenmerkenlijst_leidt_af_tot_fail_nooit_pass():
    spec = _buurspec(
        distinction="not_distinguished",
        distinguishing_feature_quote=None,
        missing_feature="een eigen kenmerk",
    )
    spec["lacks_differentia"] = True
    _, doc, uitkomst = await _toets(_Scenario(spec))
    assert doc["concept"]["core_features"] == []
    assert doc["judgment"]["lacks_differentia"] is True
    assert uitkomst["status"] == STATUS_FAIL


# R712-vorm, tweede variant: een letterlijke maar lege profielverwijzing als kenmerk.
PROFIEL = "Persoon met een bepaald profiel bij de instelling."
LEGE_VERWIJZING = "met een bepaald profiel"


def _kenmerkspec(citaat: str) -> dict[str, Any]:
    spec = _buurspec(
        distinction="not_distinguished",
        distinguishing_feature_quote=None,
        missing_feature="een eigen kenmerk",
        reason="De kern noemt geen kenmerk dat een werknemer uitsluit.",
    )
    spec["core_feature_quotes"] = [citaat]
    return spec


def _kenmerkcitaten(doc: dict[str, Any]) -> list[str]:
    plaatsen = {e["id"]: e["quote"] for e in doc["concept"]["evidence"]}
    return [plaatsen[k["evidence"]] for k in doc["concept"]["core_features"]]


@pytest.mark.asyncio
async def test_r712_vorm_lege_profielverwijzing_door_vaste_structuur_aanvaard():
    """Controle: de vaste structuur aanvaardt de lege verwijzing als kenmerk (het
    fragment staat letterlijk in de kern) en leidt `lacks_differentia=False`
    af. Alleen de semantische verificatie kan dit tegenhouden (volgende test)."""
    _, doc, _ = await _toets(_Scenario(_kenmerkspec(LEGE_VERWIJZING)), PROFIEL)
    assert _kenmerkcitaten(doc) == [LEGE_VERWIJZING]
    assert doc["status"] == "assessed"
    assert doc["judgment"]["lacks_differentia"] is False


@pytest.mark.asyncio
async def test_r712_vorm_lege_profielverwijzing_na_afwijzing_geen_oordeel():
    scenario = _Scenario(
        _kenmerkspec(LEGE_VERWIJZING),
        afgekeurd={"core_features": "unsupported", "feature:F0": "unsupported"},
    )
    ai, doc, uitkomst = await _toets(scenario, PROFIEL)
    assert [c["task_type"] for c in ai.calls] == ["validation", "ess05_verification"]
    assert _kenmerkcitaten(doc) == [LEGE_VERWIJZING]  # structuur liet het door
    assert (doc["status"], doc["error"]["type"]) == ("error", FOUT_SEMANTISCH)
    assert doc["judgment"] is None
    assert uitkomst["status"] == STATUS_ERROR


@pytest.mark.asyncio
async def test_r712_vorm_positief_inhoudelijk_kenmerk_wordt_toegepast():
    kenmerk = "met een actuele lening"
    _, doc, uitkomst = await _toets(_Scenario(_kenmerkspec(kenmerk)))
    assert _kenmerkcitaten(doc) == [kenmerk]
    assert doc["status"] == "assessed"
    assert doc["judgment"]["lacks_differentia"] is False
    assert uitkomst["status"] != STATUS_ERROR


# --- R719-vorm: parafrase met ruimere strekking ---------------------------------------

RUIME_PARAFRASE = "Volgens het materiaal is een lening geen afzonderlijk begrip."


def _parafrase(concept: dict[str, Any]) -> dict[str, Any]:
    concept["claims"][0]["text"] = RUIME_PARAFRASE
    return concept


@pytest.mark.asyncio
async def test_r719_vorm_afgekeurde_parafrase_verschijnt_nergens():
    scenario = _Scenario(
        _buurspec(), wijzig=_parafrase, afgekeurd={"claim:C-reden": "unsupported"}
    )
    _, doc, uitkomst = await _toets(scenario)
    assert (doc["status"], doc["error"]["type"]) == ("error", FOUT_SEMANTISCH)
    assert uitkomst["status"] == STATUS_ERROR
    assert RUIME_PARAFRASE not in _alle_teksten(uitkomst)


@pytest.mark.asyncio
async def test_r719_vorm_positief_vaste_weergave_zonder_nieuwe_zin():
    scenario = _Scenario(_buurspec())
    _, doc, uitkomst = await _toets(scenario)
    assert uitkomst["status"] == STATUS_PASS
    claim = scenario.concept["claims"][0]
    citaat = scenario.concept["evidence"][0]["quote"]
    # Vaste rendering: exact de gecontroleerde claimtekst met het letterlijke
    # citaat; het totaaloordeel bevat geen andere, ongecontroleerde tekst.
    tekst = claim["text"].rstrip(".")
    assert doc["judgment"]["reason"] == f"{tekst}. [definitie: “{citaat}”]"


# --- replay: verificatie van een ander concept met herschreven verifierhash -----------


def _replay(doc: dict[str, Any], binding: Any) -> dict[str, Any]:
    return beoordeel_onderscheid(
        BEGRIP,
        LENER,
        CONTEXT,
        [],
        buren=[b.als_dict() for b in BUREN_E05],
        assessment=doc,
        binding=binding,
    ).als_dict()


@pytest.mark.asyncio
async def test_replay_weigert_verificatie_van_ander_concept_met_herschreven_verifierhash():
    """Concept en `verification.candidate_hash` consistent gewijzigd,
    `verification_input.candidate_hash` (door de dienst vastgelegd bij het
    verzenden) ongemoeid: de hash in het verifierantwoord past dan bij het
    concept, dus alleen de binding aan de verzonden invoer kan weigeren."""
    scenario = _Scenario(_buurspec())
    _, svc = _service(scenario.beoordeling, scenario.verificatie)
    doc = (await svc.assess(BEGRIP, LENER, CONTEXT, [], buren=BUREN_E05)).als_dict()
    binding = svc.binding()
    # Positieve controle: het ongewijzigde document wordt toegepast.
    assert _replay(doc, binding)["status"] == STATUS_PASS

    ander = deepcopy(doc)
    ander["concept"]["claims"][0]["text"] += " Aangevuld."
    nieuw = Ess05Concept(deepcopy(ander["concept"])).hash
    ander["verification"]["candidate_hash"] = nieuw
    verzonden = ander["verification_input"]["candidate_hash"]
    assert verzonden == doc["verification_input"]["candidate_hash"] != nieuw

    uitkomst = _replay(ander, binding)
    assert uitkomst["status"] != STATUS_PASS
    assert "verificatie hoort niet bij dit conceptoordeel" in _alle_teksten(uitkomst)
