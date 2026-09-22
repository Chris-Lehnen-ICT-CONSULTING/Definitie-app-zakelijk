"""Deterministische stand-ins voor de ESS-03-AI-grens (DEF-766).

Geen model, geen netwerk, geen productie-DB. `bouw_ess03_beoordeling` maakt
een *geldige*, aan exact deze invoer gebonden beoordeling (contract
`domain.ess03.contract`) met een geverifieerd citaat uit de kandidaat, per
scenario `pass` / `fail` / `not_applicable` / `insufficient` / `error` /
`unavailable`. `FakeEss03Assessor` boots de `Ess03AssessmentService`-grens na
die de actieve wrapper aanroept, telt aanroepen en bewaart de laatst
ontvangen invoer (bewijs dat de keten exact de kandidaat doorgaf).
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from domain.ess03.contract import (
    CONTRACTVERSIE,
    Beoordelingsbinding,
    Intentie,
    beoordeling_niet_beschikbaar,
    beoordeling_technische_fout,
    beoordelingsmateriaal,
    bereken_ess03_vingerafdruk,
    materiaalhashes,
    valideer_oordeel,
)
from services.validation.ess03_assessment_service import Ess03Assessment

PROMPT_VERSION = "ess03-assess/1"
NORM_SHA256 = "n" * 64
PROVIDER = "fake"
MODEL = "fake-ess03-model"

#: De actuele binding van de fake-dienst (R1): documenten van `bouw_ess03_beoordeling`
#: met het standaardmodel voldoen eraan.
BINDING = Beoordelingsbinding(
    prompt_version=PROMPT_VERSION,
    norm_sha256=NORM_SHA256,
    provider=PROVIDER,
    model=MODEL,
)


def _citaat(tekst: str) -> str:
    """Een letterlijk fragment uit de kandidaat (eerste twee woorden)."""
    woorden = str(tekst or "").split()
    return " ".join(woorden[:2]) if woorden else ""


def bouw_ess03_beoordeling(
    begrip: str,
    tekst: str,
    contexten: dict[str, Any] | None,
    bronnen_ruw: Any = None,
    *,
    intentie: Intentie | None = None,
    scenario: str = "pass",
    reden: str | None = None,
    vraag: str = "Binnen welk register en welke populatie geldt het nummer?",
    model: str | None = MODEL,
) -> dict[str, Any]:
    """Een contractconforme ESS-03-beoordeling voor exact deze invoer."""
    intentie = intentie or Intentie()
    vingerafdruk = bereken_ess03_vingerafdruk(
        begrip, tekst, contexten, bronnen_ruw or [], intentie=intentie
    )
    if scenario == "error":
        return beoordeling_technische_fout(
            vingerafdruk,
            "timeout",
            "synthetische time-out",
            prompt_version=PROMPT_VERSION,
            norm_sha256=NORM_SHA256,
            attribution={"provider": "fake", "model": model, "task_type": "validation"},
        )
    if scenario == "unavailable":
        return beoordeling_niet_beschikbaar(vingerafdruk, "synthetisch: geen dienst")

    materiaal = beoordelingsmateriaal(
        begrip, tekst, contexten, bronnen_ruw or [], intentie
    )
    verdict, applicability = {
        "pass": ("pass", "applicable"),
        "fail": ("fail", "applicable"),
        "not_applicable": ("not_applicable", "not_applicable"),
        "insufficient": ("insufficient_information", "undetermined"),
    }[scenario]
    ruw = {
        "verdict": verdict,
        "applicability": applicability,
        "unit": None if scenario == "not_applicable" else "de afzonderlijke instantie",
        "reason": reden or f"Synthetisch oordeel {verdict} voor de proef.",
        "evidence": (
            []
            if scenario == "insufficient"
            else [{"location": "definition", "quote": _citaat(tekst)}]
        ),
        "missing_information": (
            "Geen registerafspraak aangeleverd." if scenario == "insufficient" else None
        ),
        "question": vraag if scenario == "insufficient" else None,
        "uncertainty": None,
    }
    oordeel, rejected = valideer_oordeel(ruw, materiaal)
    assert oordeel is not None, rejected
    return {
        "contract_version": CONTRACTVERSIE,
        "prompt_version": PROMPT_VERSION,
        "norm_sha256": NORM_SHA256,
        "fingerprint": vingerafdruk,
        "status": "assessed",
        "error": None,
        "assessed_at": "2026-09-21T09:00:00+00:00",
        "attribution": {
            "provider": "fake",
            "model": model,
            "task_type": "validation",
            "cached": False,
            "tokens_used": 7,
        },
        # R1: de materiaalbinding zoals de echte dienst haar vastlegt.
        "input": {
            "intentie": intentie.als_dict(),
            "materiaal": materiaalhashes(materiaal),
        },
        "judgment": oordeel.als_dict(),
        "rejected": rejected,
        "raw_response_sha256": "r" * 64,
    }


class FakeEss03Assessor:
    """De `Ess03AssessmentService`-grens: telt aanroepen, levert per scenario."""

    def __init__(self, *, scenario: str = "pass", fout: Exception | None = None):
        self.scenario = scenario
        self.fout = fout
        self.calls: list[dict[str, Any]] = []
        self.norm_sha256 = NORM_SHA256
        self.max_passage_chars = 8000

    def binding(self) -> Beoordelingsbinding:
        """De actuele beoordelingsbinding van de fake (R1), zonder netwerk."""
        return BINDING

    async def assess(
        self,
        begrip,
        tekst,
        contexten,
        bronnen_ruw,
        *,
        intentie=None,
        correlation_id=None,
    ):
        self.calls.append(
            {
                "begrip": begrip,
                "tekst": tekst,
                "contexten": deepcopy(dict(contexten or {})),
                "bronnen": deepcopy(bronnen_ruw),
                "intentie": intentie,
                "correlation_id": correlation_id,
            }
        )
        if self.fout is not None:
            raise self.fout
        return Ess03Assessment(
            bouw_ess03_beoordeling(
                begrip,
                tekst,
                contexten,
                bronnen_ruw,
                intentie=intentie,
                scenario=self.scenario,
            )
        )
