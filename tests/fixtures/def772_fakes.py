"""Deterministische stand-ins voor de INT-03-AI-grens (DEF-772 WP3).

Geen model, geen netwerk, geen productie-DB. `bouw_int03_beoordeling` maakt
een *geldige*, aan exact deze invoer gebonden beoordeling (contract
`domain.int03.contract`) waarvan elk verwijzend woord, elke passage en elk
kandidaatscitaat letterlijk in de definitie staat, per scenario `pass` /
`no_word` / `non_referring` / `fail` / `no_antecedent` / `insufficient` /
`error` / `unavailable`. `FakeInt03Assessor` boots de
`Int03AssessmentService`-grens na die de actieve wrapper aanroept, telt
aanroepen en bewaart de laatst ontvangen invoer. `FakeModelgrens` is de
laag eronder: de AI-grens (`AIServiceInterface.generate_definition`) voor de
échte `Int03AssessmentService` — en tegelijk de generatiegrens — zodat de
DI-keten met de echte dienst en uitsluitend een gestubd model kan draaien.

De verwijzingen zijn synthetisch: zij bewijzen dat de keten en de
citaatcontrole werken, niets over de kwaliteit van een echt model.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from typing import Any

from domain.int03.contract import (
    CONTRACTVERSIE,
    VERDICT_FAIL,
    VERDICT_INSUFFICIENT,
    VERDICT_PASS,
    VERWIJZING_DUIDELIJK,
    VERWIJZING_GEEN_ANTECEDENT,
    VERWIJZING_MEERDUIDIG,
    VERWIJZING_NIET_VERWIJZEND,
    VERWIJZING_ONBESLIST,
    Beoordelingsbinding,
    beoordeling_niet_beschikbaar,
    beoordeling_technische_fout,
    bereken_int03_vingerafdruk,
    valideer_oordeel,
)
from services.interfaces import AIGenerationResult
from services.validation.int03_assessment_service import Int03Assessment

PROMPT_VERSION = "int03-assess/fake"
NORM_SHA256 = "n" * 64
PROVIDER = "fake"
MODEL = "fake-int03-model"

#: De actuele binding van de fake-dienst: documenten van `bouw_int03_beoordeling`
#: met het standaardmodel voldoen eraan.
BINDING = Beoordelingsbinding(
    prompt_version=PROMPT_VERSION,
    norm_sha256=NORM_SHA256,
    provider=PROVIDER,
    model=MODEL,
)

#: Woorden die de fake als 'verwijzend woord' aanwijst (zoekhulp, geen oordeel).
_SIGNAALWOORDEN = (
    "die",
    "dat",
    "deze",
    "dit",
    "het",
    "zijn",
    "haar",
    "hun",
    "waarbij",
    "waardoor",
    "waarmee",
    "daarvan",
)
_VRAAG = "Naar welk antecedent verwijst het aangewezen woord?"


def _eerste_signaalwoord(tekst: str) -> tuple[str, str] | None:
    """(woord, passage van maximaal vijf woorden rond het woord), of None."""
    woorden = str(tekst or "").split()
    for index, woord in enumerate(woorden):
        kaal = re.sub(r"[^\w]", "", woord).lower()
        if kaal in _SIGNAALWOORDEN:
            venster = woorden[max(0, index - 2) : index + 3]
            return kaal, " ".join(venster)
    return None


def _aangewezen_woord(tekst: str) -> tuple[str, str] | None:
    """Het eerste signaalwoord, of — synthetisch, zodat de fake voor élke
    niet-lege tekst een structureel geldig document kan maken (de keten
    hervalideert bijvoorbeeld een herschreven kandidaat) — het eerste woord."""
    treffer = _eerste_signaalwoord(tekst)
    if treffer is not None:
        return treffer
    woorden = str(tekst or "").split()
    if not woorden:
        return None
    kaal = re.sub(r"[^\w]", "", woorden[0])
    return (kaal, " ".join(woorden[:5])) if kaal else None


def _andere_woorden(tekst: str, woord: str, aantal: int = 2) -> list[str]:
    """Letterlijke fragmenten uit de tekst als synthetische kandidaten: eerst
    niet-signaalwoorden langer dan vier tekens, dan overige woorden, dan
    deelstrings — altijd letterlijk aanwezig, nooit betekenisvol."""
    gevonden: list[str] = []
    tokens = [re.sub(r"[^\w]", "", t) for t in str(tekst or "").split()]
    for lengtegrens in (4, 0):
        for kaal in tokens:
            if (
                len(kaal) > lengtegrens
                and kaal.lower() not in _SIGNAALWOORDEN
                and kaal.lower() != woord.lower()
                and kaal not in gevonden
            ):
                gevonden.append(kaal)
            if len(gevonden) == aantal:
                return gevonden
    plat = str(tekst or "").strip()
    for fragment in (plat[:2], plat[-2:], plat[1:3]):
        if fragment and fragment not in gevonden:
            gevonden.append(fragment)
        if len(gevonden) == aantal:
            break
    return gevonden


def _verwijzingen_voor(scenario: str, tekst: str) -> list[dict[str, Any]]:
    treffer = _aangewezen_woord(tekst)
    if scenario == "no_word" or treffer is None:
        return []
    woord, passage = treffer
    if scenario == "non_referring":
        return [
            {
                "word": woord,
                "passage": passage,
                "status": VERWIJZING_NIET_VERWIJZEND,
                "reading": "synthetisch: niet verwijzend gebruikt",
                "candidates": [],
            }
        ]
    if scenario == "pass":
        kandidaten = _andere_woorden(tekst, woord, 1)
        return [
            {
                "word": woord,
                "passage": passage,
                "status": VERWIJZING_DUIDELIJK,
                "reading": "synthetisch: eenduidig antecedent",
                "candidates": [
                    {"quote": k, "reason": "synthetisch antecedent"} for k in kandidaten
                ],
            }
        ]
    if scenario == "fail":
        kandidaten = _andere_woorden(tekst, woord, 2)
        if len(kandidaten) < 2:  # pragma: no cover - alleen bij een tekst < 3 tekens
            msg = f"tekst heeft te weinig kandidaatfragmenten voor 'fail': {tekst!r}"
            raise ValueError(msg)
        return [
            {
                "word": woord,
                "passage": passage,
                "status": VERWIJZING_MEERDUIDIG,
                "reading": "synthetisch: twee plausibele lezingen",
                "candidates": [
                    {"quote": kandidaten[0], "reason": "synthetische lezing 1"},
                    {"quote": kandidaten[1], "reason": "synthetische lezing 2"},
                ],
            }
        ]
    if scenario == "no_antecedent":
        return [
            {
                "word": woord,
                "passage": passage,
                "status": VERWIJZING_GEEN_ANTECEDENT,
                "reading": "synthetisch: geen antecedent in de definitie",
                "candidates": [],
            }
        ]
    if scenario == "insufficient":
        return [
            {
                "word": woord,
                "passage": passage,
                "status": VERWIJZING_ONBESLIST,
                "reading": "synthetisch: betekenisgrond ontbreekt",
                "candidates": [],
            }
        ]
    msg = f"onbekend scenario {scenario!r}"
    raise ValueError(msg)


_VERDICT_BIJ_SCENARIO = {
    "pass": VERDICT_PASS,
    "no_word": VERDICT_PASS,
    "non_referring": VERDICT_PASS,
    "fail": VERDICT_FAIL,
    "no_antecedent": VERDICT_FAIL,
    "insufficient": VERDICT_INSUFFICIENT,
}


def bouw_ruwe_modeluitvoer(
    tekst: str,
    scenario: str = "pass",
    *,
    verwijzingen: list[dict[str, Any]] | None = None,
    reden: str | None = None,
    vraag: str = _VRAAG,
) -> dict[str, Any]:
    """Het kale modelantwoord (de vijf antwoordvelden) voor exact deze tekst —
    wat een model op de INT-03-prompt zou teruggeven, nog vóór de controle
    door code."""
    verdict = _VERDICT_BIJ_SCENARIO[scenario]
    return {
        "verdict": verdict,
        "reason": reden or f"Synthetisch oordeel {verdict} voor de proef.",
        "references": (
            deepcopy(verwijzingen)
            if verwijzingen is not None
            else _verwijzingen_voor(scenario, tekst)
        ),
        "question": vraag if scenario == "insufficient" else None,
        "uncertainty": None,
    }


def bouw_int03_beoordeling(
    begrip: str,
    tekst: str,
    contexten: dict[str, Any] | None,
    toelichting: str | None = None,
    *,
    scenario: str = "pass",
    verwijzingen: list[dict[str, Any]] | None = None,
    reden: str | None = None,
    vraag: str = _VRAAG,
    model: str | None = MODEL,
) -> dict[str, Any]:
    """Een contractconforme INT-03-beoordeling voor exact deze invoer."""
    vingerafdruk = bereken_int03_vingerafdruk(begrip, tekst, contexten, toelichting)
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

    ruw = bouw_ruwe_modeluitvoer(
        tekst, scenario, verwijzingen=verwijzingen, reden=reden, vraag=vraag
    )
    oordeel, rejected = valideer_oordeel(ruw, tekst)
    assert oordeel is not None, rejected
    return {
        "contract_version": CONTRACTVERSIE,
        "prompt_version": PROMPT_VERSION,
        "norm_sha256": NORM_SHA256,
        "fingerprint": vingerafdruk,
        "status": "assessed",
        "error": None,
        "assessed_at": "2026-09-25T20:00:00+00:00",
        "attribution": {
            "provider": "fake",
            "model": model,
            "task_type": "validation",
            "cached": False,
            "tokens_used": 7,
        },
        "input": {"text_sha256": "t" * 64, "toelichting_sha256": None},
        "judgment": oordeel.als_dict(),
        "rejected": rejected,
        "raw_response_sha256": "r" * 64,
    }


class FakeInt03Assessor:
    """De `Int03AssessmentService`-grens: telt aanroepen, levert per scenario."""

    def __init__(self, *, scenario: str = "pass", fout: Exception | None = None):
        self.scenario = scenario
        self.fout = fout
        self.calls: list[dict[str, Any]] = []
        self.norm_sha256 = NORM_SHA256

    def binding(self) -> Beoordelingsbinding:
        """De actuele beoordelingsbinding van de fake, zonder netwerk."""
        return BINDING

    async def assess(
        self,
        begrip,
        tekst,
        contexten,
        *,
        toelichting=None,
        correlation_id=None,
    ):
        self.calls.append(
            {
                "begrip": begrip,
                "tekst": tekst,
                "contexten": deepcopy(dict(contexten or {})),
                "toelichting": toelichting,
                "correlation_id": correlation_id,
            }
        )
        if self.fout is not None:
            raise self.fout
        return Int03Assessment(
            bouw_int03_beoordeling(
                begrip, tekst, contexten, toelichting, scenario=self.scenario
            )
        )


#: Herkenbare regel uit de INT-03-gebruikersprompt (`bouw_beoordelingsprompt`);
#: de fake-modelgrens leest de te toetsen definitie hieruit, zoals een model
#: dat zou doen. Wijzigt de prompt, dan faalt dit luid — nooit stil een pass.
INT03_PROMPTMARKER = "enige bewijsplaats voor citaten"
_DEFINITIEREGEL = re.compile(
    r"^Definitie \([^)]*enige bewijsplaats voor citaten\): (?P<tekst>.*)$",
    re.MULTILINE,
)
GENERATIEMODEL = "offline"
INT03_MODEL = "fake-int03-model"


def definitie_uit_prompt(prompt: str) -> str | None:
    """De te toetsen definitie zoals zij als gegevens in de prompt staat."""
    treffer = _DEFINITIEREGEL.search(str(prompt or ""))
    return treffer.group("tekst") if treffer else None


def _resultaat(tekst: str, model: str, **metadata: Any) -> AIGenerationResult:
    return AIGenerationResult(
        text=tekst,
        model=model,
        tokens_used=7,
        generation_time=0.0,
        metadata=dict(metadata),
    )


class FakeModelgrens:
    """De AI-grens (`AIServiceInterface.generate_definition`) onder de échte
    `Int03AssessmentService` én onder de generatie: één gedeelde AI-service,
    zoals `DefinitionOrchestratorV2`/`ServiceContainer` die injecteren.

    - een generatieprompt (zonder `task_type`) krijgt `definitie` als kandidaat;
    - een INT-03-beoordelingsprompt (herkend aan `INT03_PROMPTMARKER`) krijgt
      een gepland antwoord uit `uitkomsten` (dict, ruwe tekst of exception) of
      anders het scenario-antwoord voor de definitie die in de prompt staat,
      met `beoordelingsmodel` als gebruikt model (zet dit op het door de echte
      ModelRouter gekozen model, anders is de binding niet actueel);
    - elke andere beoordelingsprompt (`task_type="validation"`: ESS-03, CON-02)
      krijgt bewust geen geldig antwoord (`{}` → technische fout, nooit pass);
    - elke voorbeeldenprompt (`examples`, `synonyms`, …) krijgt een leeg
      antwoord (geen voorbeelden), zodat de echte voorbeeldengenerator kan
      draaien zonder verzonnen inhoud.

    Legt elke aanroep vast; geen netwerk, geen model.
    """

    def __init__(
        self,
        *,
        definitie: str = "",
        scenario: str = "pass",
        uitkomsten: list[Any] | None = None,
        fout: Exception | None = None,
        beoordelingsmodel: str = INT03_MODEL,
    ) -> None:
        self.definitie = definitie
        self.scenario = scenario
        self.uitkomsten = list(uitkomsten or [])
        self.fout = fout
        self.beoordelingsmodel = beoordelingsmodel
        self.calls: list[dict[str, Any]] = []
        self.default_model = "fake-default-model"

    @property
    def int03_calls(self) -> list[dict[str, Any]]:
        return [c for c in self.calls if INT03_PROMPTMARKER in str(c["prompt"])]

    async def generate_definition(self, prompt: str, **kwargs: Any):
        self.calls.append({"prompt": prompt, **kwargs})
        taak = kwargs.get("task_type")
        if INT03_PROMPTMARKER not in str(prompt):
            if taak == "validation":
                return _resultaat("{}", "fake-other-assessment-model")
            if taak is None:
                return _resultaat(self.definitie, GENERATIEMODEL)
            return _resultaat("", "fake-examples-model")
        if self.fout is not None:
            raise self.fout
        if self.uitkomsten:
            uitkomst = self.uitkomsten.pop(0)
        else:
            tekst = definitie_uit_prompt(prompt)
            uitkomst = bouw_ruwe_modeluitvoer(
                tekst if tekst is not None else self.definitie, self.scenario
            )
        if isinstance(uitkomst, Exception):
            raise uitkomst
        antwoord = (
            uitkomst
            if isinstance(uitkomst, str)
            else json.dumps(uitkomst, ensure_ascii=False)
        )
        return _resultaat(antwoord, self.beoordelingsmodel)


class FakeRouter:
    """ModelRouter-grens: kiest per taak een vaste (provider, model)."""

    def __init__(self, provider: str = PROVIDER, model: str = INT03_MODEL) -> None:
        self.provider = provider
        self.model = model

    @classmethod
    def from_config(cls) -> FakeRouter:
        return cls()

    def get_model(self, task_type: str) -> tuple[str, str]:
        return self.provider, self.model
