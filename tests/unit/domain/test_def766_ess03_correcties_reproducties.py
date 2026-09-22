"""DEF-766 correctieronde 1 — gedragsmatige reproducties van R1, R2, R3, R7 en R9.

Deze tests gebruiken uitsluitend de API van fase 1 en asserteren het
gecorrigeerde gedrag. Vóór de correctie falen zij op gedrag (niet op een
ontbrekende import): een stale prompt/norm/model werd toegepast (R1), een
omhuld antwoord werd geaccepteerd (R2), een verzonnen citaat naast een echt
citaat liet een 'fail' staan (R3), een afgekapte passage kreeg een volledig
oordeel (R7) en 'onvoldoende informatie' droeg het generieke label (R9).
"""

from __future__ import annotations

import json

import pytest

from domain.ess03.contract import (
    STATUS_FAIL,
    STATUS_OPEN,
    VERDICT_FAIL,
    VERDICT_INSUFFICIENT,
    Intentie,
    beoordeel_telbaarheid,
    beoordelingsmateriaal,
    bereken_ess03_vingerafdruk,
    valideer_oordeel,
)
from domain.sources.normalisatie import canoniseer_bronnen
from services.validation.ess03_assessment_service import parse_modeluitvoer
from ui.components import validation_view

pytestmark = [pytest.mark.unit]

BEGRIP = "boekexemplaar"
TEKST = (
    "Boekexemplaar dat uitsluitend door zijn ISBN van andere fysieke exemplaren "
    "wordt onderscheiden."
)
CONTEXT = {
    "organisatorische_context": ["Synthetische Bibliotheek"],
    "juridische_context": [],
    "wettelijke_basis": [],
}
BRON = {
    "provider": "documents",
    "doc_id": "reglement-1",
    "snippet": (
        "Een ISBN identificeert een uitgave. Meerdere fysieke exemplaren van "
        "dezelfde uitgave dragen hetzelfde ISBN."
    ),
}
INTENTIE = Intentie(toelichting="Bedoeld: het afzonderlijke fysieke exemplaar.")
BRON_ID = canoniseer_bronnen([BRON])[0].source_id


def _oordeel(**over) -> dict:
    basis = {
        "verdict": VERDICT_FAIL,
        "applicability": "applicable",
        "unit": "het afzonderlijke fysieke exemplaar",
        "reason": "Het ISBN onderscheidt geen fysieke exemplaren.",
        "evidence": [
            {"location": "definition", "quote": "uitsluitend door zijn ISBN"},
        ],
        "missing_information": None,
        "question": None,
        "uncertainty": None,
    }
    basis.update(over)
    return basis


def _document(**over) -> dict:
    materiaal = beoordelingsmateriaal(BEGRIP, TEKST, CONTEXT, [BRON], INTENTIE)
    gevalideerd, rejected = valideer_oordeel(_oordeel(), materiaal)
    assert gevalideerd is not None, rejected
    document = {
        "contract_version": "ess03/1",
        "prompt_version": "obsolete-prompt",
        "norm_sha256": "obsolete-norm",
        "fingerprint": bereken_ess03_vingerafdruk(
            BEGRIP, TEKST, CONTEXT, [BRON], intentie=INTENTIE
        ),
        "status": "assessed",
        "error": None,
        "assessed_at": "2026-09-21T12:00:00+00:00",
        "attribution": {
            "provider": "retired-provider",
            "model": "retired-model",
            "task_type": "validation",
            "cached": False,
            "tokens_used": 1,
        },
        "input": {
            "intentie": INTENTIE.als_dict(),
            "materiaal": {"definition": "0" * 64},
        },
        "judgment": gevalideerd.als_dict(),
        "rejected": rejected,
        "raw_response_sha256": "r" * 64,
    }
    document.update(over)
    return document


def test_r1_stale_prompt_norm_model_en_materiaal_zijn_niet_actueel():
    # Reproductie uit de review: correcte kandidaatvingerafdruk, maar
    # obsolete-prompt / obsolete-norm / retired-model / onjuiste materiaalhash.
    uitkomst = beoordeel_telbaarheid(
        BEGRIP, TEKST, CONTEXT, [BRON], intentie=INTENTIE, assessment=_document()
    )
    assert uitkomst.status == STATUS_OPEN
    assert uitkomst.review["assessment"]["applied"] is False


def test_r2_omhuld_antwoord_wordt_niet_stil_tot_object_teruggebracht():
    goed = json.dumps(_oordeel(), ensure_ascii=False)
    assert parse_modeluitvoer("Hier is het antwoord:\n" + goed) is None
    assert parse_modeluitvoer(goed + "\nGroet, het model") is None


def test_r2_twee_vragen_in_een_string_is_niet_een_gerichte_vraag():
    materiaal = beoordelingsmateriaal(BEGRIP, TEKST, CONTEXT, [BRON], INTENTIE)
    oordeel = _oordeel(
        verdict=VERDICT_INSUFFICIENT,
        applicability="undetermined",
        evidence=[],
        missing_information="bron en tijdvak",
        question="Welke bron? Welk tijdvak?",
    )
    gevalideerd, rejected = valideer_oordeel(oordeel, materiaal)
    assert gevalideerd is None
    assert rejected and rejected[0]["reason"] == "structuurfout"


def test_r2_onbekend_veld_is_geen_geldig_antwoord():
    materiaal = beoordelingsmateriaal(BEGRIP, TEKST, CONTEXT, [BRON], INTENTIE)
    gevalideerd, rejected = valideer_oordeel(
        {**_oordeel(), "confidence": 0.9}, materiaal
    )
    assert gevalideerd is None
    assert rejected and rejected[0]["reason"] == "structuurfout"


def test_r3_een_verzonnen_citaat_naast_een_echt_citaat_draagt_geen_oordeel():
    materiaal = beoordelingsmateriaal(BEGRIP, TEKST, CONTEXT, [BRON], INTENTIE)
    oordeel = _oordeel(
        evidence=[
            {"location": "definition", "quote": "uitsluitend door zijn ISBN"},
            {"location": "source:missing", "quote": "hetzelfde ISBN"},
        ]
    )
    gevalideerd, rejected = valideer_oordeel(oordeel, materiaal)
    assert gevalideerd is None
    assert any(r["reason"] == "onbekende vindplaats" for r in rejected)


def test_r3_geldig_bewijs_blijft_gewoon_een_oordeel():
    materiaal = beoordelingsmateriaal(BEGRIP, TEKST, CONTEXT, [BRON], INTENTIE)
    gevalideerd, rejected = valideer_oordeel(_oordeel(), materiaal)
    assert gevalideerd is not None and gevalideerd.status == STATUS_FAIL
    assert rejected == []


def test_r9_onvoldoende_informatie_draagt_een_eigen_label(monkeypatch):
    materiaal = beoordelingsmateriaal(BEGRIP, TEKST, CONTEXT, [BRON], INTENTIE)
    oordeel = _oordeel(
        verdict=VERDICT_INSUFFICIENT,
        applicability="undetermined",
        evidence=[],
        missing_information="registerafspraak",
        question="Binnen welk register geldt het nummer?",
    )
    gevalideerd, _ = valideer_oordeel(oordeel, materiaal)
    assert gevalideerd is not None
    detail = {
        "status": "review_required",
        "score": None,
        "contract_version": "ess03/1",
        "fingerprint": "f" * 64,
        "parts": [
            {
                "id": "countability",
                "status": "review_required",
                "evidence": None,
                "context_value": None,
                "field": "ess03_assessment",
                "position": None,
                "reason": "AI-beoordeling van telbaarheid (m): registerafspraak ontbreekt.",
                "action": "Beantwoord de vraag.",
            }
        ],
        "review": {
            "assessment": {
                "applied": True,
                "status": "assessed",
                "verdict": VERDICT_INSUFFICIENT,
                "question": "Binnen welk register geldt het nummer?",
                "model": "m",
                "provider": "p",
            }
        },
    }
    shown: dict[str, list[str]] = {"markdown": [], "warning": [], "info": []}
    for api in shown:
        monkeypatch.setattr(
            validation_view.st,
            api,
            lambda t, *a, _api=api, **kw: shown[_api].append(str(t)),
            raising=False,
        )
    validation_view.render_rule_results({"ESS-03": detail})
    assert "Onvoldoende informatie" in shown["markdown"][0]
    assert "Nog te beoordelen" not in shown["markdown"][0]
    assert any("Onvoldoende informatie" in t for t in shown["warning"])
