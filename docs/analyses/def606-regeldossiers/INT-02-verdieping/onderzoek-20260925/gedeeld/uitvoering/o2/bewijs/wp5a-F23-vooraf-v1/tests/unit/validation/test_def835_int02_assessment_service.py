"""DEF-835 WP2 — de begrensde INT-02-AI-dienst op een fake AI-grens.

Echte async aanroepen van `Int02AssessmentService.assess`. De AI-grens is
een fake die `AIServiceInterface.generate_definition` nabootst, of de echte
`AIServiceV2` + `AsyncGPTClient` met alleen een fake providerclient aan de
netwerkgrens. Geen netwerk, geen echt model, geen productiedata.

Bewezen wordt wat code kan bewijzen: expliciet profiel en budget vóór elke
aanroep, routing via task_type `validation` zonder nieuwe routertaak, één
transportpoging zonder SDK-retries, herstelcall of ruwe cache, een begrensde
deadline, begrensde invoer en uitvoer, fail-closed parsing (ook dubbele
sleutels), de WP1-contractbeoordeling ongewijzigd, eerlijke attributie
(onbekend blijft `unknown`), logging zonder inhoud, en een begrensde cache
die alleen volledig geldige, volledig gebonden resultaten onthoudt. Niet
bewezen: dat een model de juiste functie, passage of vraag kiest (WP4).
"""

from __future__ import annotations

import asyncio
import copy
import dataclasses
import json
import logging
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from domain.int02.contract import (
    MELDING_E,
    MELDING_NIET_BEOORDEELD,
    NORMVERSIE,
    ONBEKEND,
    Int02ContractError,
    maak_invoer,
    toets_actualiteit,
)
from services.ai.anthropic_client import AnthropicClient
from services.ai.base_client import AIConnectionClientError, ChatResponse
from services.ai.model_router import ModelRouter
from services.ai.openai_client import OpenAIClient
from services.ai_service_v2 import AIServiceV2
from services.interfaces import (
    AIGenerationResult,
    AIRateLimitError,
    AIServiceError,
    AITimeoutError,
)
from services.validation import int02_assessment_service as dienstmodule
from services.validation.int02_assessment_service import (
    PROMPT_VERSION,
    TASK_TYPE,
    Budget,
    Int02AssessmentService,
    Int02ServiceConfigError,
    Modelprofiel,
    bouw_int02_prompt,
    laad_int02_norm,
)
from utils.async_api import RateLimitConfig

pytestmark = [pytest.mark.unit]

ROOT = Path(__file__).resolve().parents[3]
DIENSTLOGGER = "services.validation.int02_assessment_service"

PROVIDER = "fakeprovider"
MODEL = "fake-int02-model"

BEGRIP = "aanvraag"
KERN = "Aanvraag die de behandelaar moet afwijzen bij een ontbrekende bijlage."
PASSAGE = "de behandelaar moet afwijzen bij een ontbrekende bijlage"


def _profiel(**over) -> Modelprofiel:
    velden = {
        "profiel_id": "fixture-offline-1",
        "provider": PROVIDER,
        "model": MODEL,
        "kwalificatie": "testfixture; geen kwaliteitsclaim",
    }
    velden.update(over)
    return Modelprofiel(**velden)


def _budget(**over) -> Budget:
    velden = {
        "max_uitvoertokens": 800,
        "deadline_seconden": 5.0,
        "max_invoertekens_veld": 2000,
        "max_invoertekens_totaal": 6000,
        "max_antwoordtekens": 20000,
    }
    velden.update(over)
    return Budget(**velden)


def _invoer(**over):
    velden = {
        "begrip": BEGRIP,
        "kern": KERN,
        "bedoeling": "Een verzoek om een besluit.",
        "organisatorische_context": ["Synthetische Dienst"],
        "juridische_context": [],
        "wettelijke_basis": [],
        "bronnen": [
            {"id": "B1", "tekst": "Een aanvraag is een verzoek om een besluit."}
        ],
    }
    velden.update(over)
    return maak_invoer(**velden)


def _grond(**over):
    grond = {"field": "kern", "ref": None, "quote": None, "start": None, "end": None}
    grond.update(over)
    return grond


def _fail_uitvoer(kern: str = KERN, quote: str = PASSAGE, **over):
    start = kern.index(quote)
    uitvoer = {
        "verdict": "fail",
        "passages": [
            {
                "quote": quote,
                "start": start,
                "end": start + len(quote),
                "function": "actor_prescription",
                "ground": _grond(),
            }
        ],
        "reason": "De passage schrijft de behandelaar een handeling voor.",
        "question": None,
        "uncertainty": "none",
        "scope_reason": None,
        "coverage": "complete",
    }
    uitvoer.update(over)
    return uitvoer


def _onvoldoende_uitvoer():
    return {
        "verdict": "insufficient_information",
        "passages": [],
        "reason": "De bedoelde betekenis van de bijlage ontbreekt.",
        "question": "Welke bijlage is bedoeld?",
        "uncertainty": "decisive",
        "scope_reason": None,
        "coverage": "partial",
    }


class FakeRouter:
    """Routergrens met dezelfde publieke vorm als `ModelRouter`.

    Correctie F2: naast `get_model` ook de capability-policy
    (`accepts_temperature`, `thinking_default_on`) die het verzendbeleid van
    de bestaande adapter bepaalt, zodat een policywijziging testbaar is.
    """

    def __init__(
        self,
        provider=PROVIDER,
        model=MODEL,
        fout=None,
        temperature=True,
        thinking=False,
        beleidsfout=None,
    ):
        self.provider = provider
        self.model = model
        self.fout = fout
        self.temperature = temperature
        self.thinking = thinking
        self.beleidsfout = beleidsfout
        self.calls: list[str] = []

    def get_model(self, task_type):
        self.calls.append(task_type)
        if self.fout is not None:
            raise self.fout
        return self.provider, self.model

    def accepts_temperature(self, model, provider=None):
        if self.beleidsfout is not None:
            raise self.beleidsfout
        return self.temperature

    def thinking_default_on(self, model, provider=None):
        if self.beleidsfout is not None:
            raise self.beleidsfout
        return self.thinking


class Hang:
    """Uitkomst die nooit terugkomt (deadline-test)."""


class FakeAI:
    """AI-grens: per aanroep de volgende geplande uitkomst, alle kwargs vastgelegd.

    Correctie F1: standaard meldt de fake een afgeronde stopreden
    (`end_turn`, zoals de Anthropic-adapter); `stop_reason=None` laat de
    reden weg, zoals de bestaande OpenAI-adapter doet.
    """

    def __init__(self, *uitkomsten, model=None, cached=False, stop_reason="end_turn"):
        self.uitkomsten = list(uitkomsten)
        self.calls: list[dict] = []
        self.model = model
        self.cached = cached
        self.stop_reason = stop_reason

    async def generate_definition(self, prompt, **kwargs):
        self.calls.append({"prompt": prompt, **kwargs})
        uitkomst = self.uitkomsten.pop(0) if self.uitkomsten else _fail_uitvoer()
        if isinstance(uitkomst, Hang):
            await asyncio.Event().wait()
        if isinstance(uitkomst, BaseException):
            raise uitkomst
        tekst = (
            uitkomst
            if isinstance(uitkomst, str) or uitkomst is None
            else json.dumps(uitkomst, ensure_ascii=False)
        )
        metadata = {"tokens_estimated": True}
        if self.stop_reason is not None:
            metadata["stop_reason"] = self.stop_reason
        return AIGenerationResult(
            text=tekst,
            model=self.model if self.model is not None else kwargs.get("model"),
            tokens_used=None,
            generation_time=0.01,
            cached=self.cached,
            metadata=metadata,
        )


def _dienst(ai=None, router=None, **over):
    kwargs = {"profiel": _profiel(), "budget": _budget()}
    kwargs.update(over)
    return Int02AssessmentService(
        ai if ai is not None else FakeAI(),
        router if router is not None else FakeRouter(),
        **kwargs,
    )


# --- constructie en configuratie ----------------------------------------------


def test_ai_service_en_router_moeten_expliciet_geinjecteerd_zijn():
    with pytest.raises(Int02ServiceConfigError):
        Int02AssessmentService(None, FakeRouter(), profiel=_profiel(), budget=_budget())
    with pytest.raises(Int02ServiceConfigError):
        Int02AssessmentService(FakeAI(), None, profiel=_profiel(), budget=_budget())


@pytest.mark.parametrize(
    "over",
    [
        {"profiel_id": ""},
        {"provider": " "},
        {"model": ""},
        {"model": None},
        {"kwalificatie": ""},
        {"kwalificatie": "   "},
    ],
)
def test_ongeldig_modelprofiel_wordt_geweigerd(over):
    with pytest.raises(Int02ServiceConfigError):
        _profiel(**over)


@pytest.mark.parametrize(
    "over",
    [
        {"max_uitvoertokens": 0},
        {"max_uitvoertokens": True},
        {"max_uitvoertokens": 1.5},
        {"deadline_seconden": 0},
        {"deadline_seconden": -1},
        {"deadline_seconden": float("inf")},
        {"deadline_seconden": float("nan")},
        {"deadline_seconden": True},
        {"max_invoertekens_veld": 0},
        {"max_invoertekens_totaal": -5},
        {"max_antwoordtekens": 0},
    ],
)
def test_ongeldig_budget_wordt_geweigerd(over):
    with pytest.raises(Int02ServiceConfigError):
        _budget(**over)


def test_taak_is_de_bestaande_routertaak_validation():
    assert TASK_TYPE == "validation"
    assert "validation" in ModelRouter._DEFAULT_CONFIG["task_tiers"]["critical"]


def test_dienst_wordt_niet_door_de_container_aangemaakt():
    container = (ROOT / "src/services/container.py").read_text(encoding="utf-8")
    assert "int02_assessment" not in container
    assert "Int02AssessmentService" not in container


async def test_aanroeper_moet_een_int02invoer_leveren():
    dienst = _dienst()
    with pytest.raises(Int02ContractError):
        await dienst.assess({"kern": KERN})


# --- NE: kern of context ontbreekt → geen aanroep --------------------------------


@pytest.mark.parametrize(
    ("over", "deel"),
    [
        ({"kern": ""}, "kern"),
        ({"kern": "   "}, "kern"),
        ({"kern": "Toegang:"}, "kern"),
        ({"organisatorische_context": []}, "context"),
        ({"kern": "", "organisatorische_context": []}, "kern en context"),
    ],
)
async def test_ontbrekende_kern_of_context_is_ne_zonder_aanroep(over, deel):
    ai = FakeAI()
    resultaat = await _dienst(ai).assess(_invoer(**over))
    assert ai.calls == []
    assert resultaat.status == "not_evaluated"
    assert f"Niet uitgevoerd: {deel} ontbreekt" in resultaat.melding
    assert resultaat.document.oordeel is None
    assert resultaat.reden == "missing_input"


async def test_ne_gaat_voor_ontbrekend_profiel():
    ai = FakeAI()
    resultaat = await _dienst(ai, profiel=None).assess(_invoer(kern=""))
    assert ai.calls == []
    assert resultaat.status == "not_evaluated"


# --- profiel, budget en router: geblokkeerd zonder aanroep ----------------------


def _assert_geblokkeerd(resultaat, ai, reden):
    assert ai.calls == []
    assert resultaat.reden == reden
    assert resultaat.status == "review_required"
    assert resultaat.document.reden == "not_assessed"
    assert resultaat.melding == MELDING_NIET_BEOORDEELD
    assert resultaat.document.oordeel is None
    assert resultaat.document.uitvoering.status == "not_executed"
    assert resultaat.document.uitvoering.transportpogingen == 0
    assert resultaat.gecachet is False


async def test_zonder_profiel_geen_aanroep_en_geen_routerdefault_als_kwalificatie():
    ai = FakeAI()
    resultaat = await _dienst(ai, profiel=None).assess(_invoer())
    _assert_geblokkeerd(resultaat, ai, "profile_missing")
    # De routerdefault wordt niet als gevraagd/gekwalificeerd model gebonden.
    assert resultaat.document.binding.provider == ONBEKEND
    assert resultaat.document.binding.model == ONBEKEND
    assert resultaat.profiel_id is None


async def test_zonder_budget_geen_aanroep():
    ai = FakeAI()
    resultaat = await _dienst(ai, budget=None).assess(_invoer())
    _assert_geblokkeerd(resultaat, ai, "budget_missing")


async def test_ongekwalificeerd_profiel_geen_aanroep():
    ai = FakeAI()
    resultaat = await _dienst(ai, profiel=_profiel(kwalificatie=None)).assess(_invoer())
    _assert_geblokkeerd(resultaat, ai, "profile_unqualified")


@pytest.mark.parametrize(
    "router",
    [FakeRouter(model="ander-model"), FakeRouter(provider="andere-provider")],
    ids=["model", "provider"],
)
async def test_router_wijkt_af_van_profiel_geen_aanroep(router):
    ai = FakeAI()
    resultaat = await _dienst(ai, router).assess(_invoer())
    _assert_geblokkeerd(resultaat, ai, "router_mismatch")


async def test_router_onbeschikbaar_geen_aanroep_en_geen_foutekst_in_log(caplog):
    ai = FakeAI()
    router = FakeRouter(fout=RuntimeError("GEHEIM-ROUTER-7Q"))
    with caplog.at_level(logging.DEBUG):
        resultaat = await _dienst(ai, router).assess(_invoer())
    _assert_geblokkeerd(resultaat, ai, "router_unavailable")
    assert "GEHEIM-ROUTER-7Q" not in caplog.text
    assert "GEHEIM-ROUTER-7Q" not in repr(resultaat)


# --- begrensde invoer -----------------------------------------------------------


@pytest.mark.parametrize(
    "veld", ["begrip", "kern", "bedoeling", "context", "bron_id", "bron_tekst"]
)
async def test_te_lang_invoerveld_geen_aanroep(veld):
    lang = "x" * 51
    over = {
        "begrip": {"begrip": lang},
        "kern": {"kern": "Aanvraag " + lang},
        "bedoeling": {"bedoeling": lang},
        "context": {"juridische_context": [lang]},
        "bron_id": {"bronnen": [{"id": lang, "tekst": "t"}]},
        "bron_tekst": {"bronnen": [{"id": "B1", "tekst": lang}]},
    }[veld]
    velden = {"kern": "Aanvraag."}  # alle standaardvelden blijven onder de 50
    velden.update(over)
    ai = FakeAI()
    budget = _budget(max_invoertekens_veld=50, max_invoertekens_totaal=100000)
    resultaat = await _dienst(ai, budget=budget).assess(_invoer(**velden))
    _assert_geblokkeerd(resultaat, ai, "input_too_long")


async def test_totale_invoer_boven_budget_geen_aanroep():
    ai = FakeAI()
    invoer = _invoer(juridische_context=["y" * 40, "z" * 40])
    budget = _budget(max_invoertekens_veld=100, max_invoertekens_totaal=150)
    resultaat = await _dienst(ai, budget=budget).assess(invoer)
    _assert_geblokkeerd(resultaat, ai, "input_too_long")


async def test_invoer_precies_op_de_veldgrens_wordt_wel_beoordeeld():
    ai = FakeAI()
    budget = _budget(max_invoertekens_veld=len(KERN), max_invoertekens_totaal=100000)
    resultaat = await _dienst(ai, budget=budget).assess(_invoer())
    assert len(ai.calls) == 1
    assert resultaat.status == "fail"


async def test_niet_codeerbare_invoer_geen_aanroep():
    ai = FakeAI()
    resultaat = await _dienst(ai).assess(_invoer(bedoeling="los surrogaat \ud800"))
    _assert_geblokkeerd(resultaat, ai, "input_not_encodable")


# --- transport: één poging, opt-ins, routing --------------------------------------


async def test_aanroep_gebruikt_opt_ins_budget_en_routing():
    ai = FakeAI()
    router = FakeRouter()
    invoer = _invoer()
    await _dienst(ai, router).assess(invoer)
    assert len(ai.calls) == 1
    call = ai.calls[0]
    systeem, data = bouw_int02_prompt(invoer, laad_int02_norm())
    assert call["prompt"] == data
    assert call["system_prompt"] == systeem
    assert call["task_type"] == "validation"
    assert call["model"] == MODEL
    assert call["temperature"] == 0.0
    assert call["max_tokens"] == 800
    assert call["timeout_seconds"] == 5.0
    assert call["use_cache"] is False
    assert call["max_attempts"] == 1
    assert call["max_retries"] == 0
    assert call["token_estimate"] == "heuristic"
    assert call["offload_postprocessing"] is True
    assert set(router.calls) == {"validation"}


@pytest.mark.parametrize(
    "uitkomst",
    [
        "geen json",
        json.dumps(_fail_uitvoer(quote="bestaat niet", kern="bestaat niet")),
        AIServiceError("x"),
    ],
    ids=["malformed", "fictief-citaat", "transportfout"],
)
async def test_geen_herstelcall_na_fout(uitkomst):
    ai = FakeAI(uitkomst, _fail_uitvoer())
    resultaat = await _dienst(ai).assess(_invoer())
    assert len(ai.calls) == 1
    assert resultaat.status == "error"


# --- deadline ---------------------------------------------------------------------


async def test_hangende_aanroep_stopt_op_de_deadline():
    ai = FakeAI(Hang())
    start = time.perf_counter()
    resultaat = await _dienst(ai, budget=_budget(deadline_seconden=0.05)).assess(
        _invoer()
    )
    assert time.perf_counter() - start < 2.0
    assert resultaat.status == "error"
    assert resultaat.melding == MELDING_E
    assert resultaat.document.foutcategorie == "timeout"
    assert resultaat.document.uitvoering.status == "failed"
    assert resultaat.reden == "timeout"


async def test_te_laat_teruggekomen_antwoord_is_timeout_en_niet_gecachet():
    # Geïnjecteerde klok: elke aflezing tien seconden later (deadline 5 s).
    stand = {"t": 0.0}

    def klok() -> float:
        stand["t"] += 10.0
        return stand["t"]

    ai = FakeAI(_fail_uitvoer(), _fail_uitvoer())
    dienst = _dienst(ai, budget=_budget(deadline_seconden=5.0), klok=klok)
    resultaat = await dienst.assess(_invoer())
    assert len(ai.calls) == 1
    assert resultaat.status == "error"
    assert resultaat.document.foutcategorie == "timeout"
    assert resultaat.document.oordeel is None
    assert resultaat.reden == "timeout"
    tweede = await dienst.assess(_invoer())
    assert len(ai.calls) == 2
    assert tweede.gecachet is False


# --- technische fouten van de AI-laag ---------------------------------------------


@pytest.mark.parametrize(
    ("fout", "categorie", "reden"),
    [
        (AITimeoutError("GEHEIM-FOUT-7Q"), "timeout", "timeout"),
        (AIRateLimitError("GEHEIM-FOUT-7Q"), "transport", "rate_limit"),
        (AIServiceError("GEHEIM-FOUT-7Q"), "transport", "connection"),
        (RuntimeError("GEHEIM-FOUT-7Q"), "provider", "unknown"),
    ],
    ids=["timeout", "rate_limit", "connection", "unknown"],
)
async def test_technische_fout_is_error_zonder_uitzonderingstekst(
    fout, categorie, reden, caplog
):
    ai = FakeAI(fout)
    with caplog.at_level(logging.DEBUG):
        resultaat = await _dienst(ai).assess(_invoer())
    assert resultaat.status == "error"
    assert resultaat.melding == MELDING_E
    assert resultaat.document.foutcategorie == categorie
    assert resultaat.document.uitvoering.status == "failed"
    assert resultaat.document.oordeel is None
    assert resultaat.reden == reden
    assert resultaat.uitzonderingstype == type(fout).__name__
    assert "GEHEIM-FOUT-7Q" not in caplog.text
    assert "GEHEIM-FOUT-7Q" not in repr(resultaat)
    assert "GEHEIM-FOUT-7Q" not in json.dumps(resultaat.document.als_dict())


async def test_annulering_wordt_niet_als_beoordeling_ingeslikt():
    ai = FakeAI(asyncio.CancelledError())
    with pytest.raises(asyncio.CancelledError):
        await _dienst(ai).assess(_invoer())


# --- antwoordfouten: geen stille pass/fail -------------------------------------


async def test_afgekapt_antwoord_is_error_ook_als_json_toevallig_geldig_is():
    ai = FakeAI(_fail_uitvoer(), stop_reason="max_tokens")
    resultaat = await _dienst(ai).assess(_invoer())
    assert resultaat.status == "error"
    assert resultaat.document.foutcategorie == "invalid_output"
    assert resultaat.reden == "truncated_response"
    assert resultaat.stop_reason == "max_tokens"
    assert resultaat.document.oordeel is None


@pytest.mark.parametrize(
    "tekst",
    [
        "",
        "   ",
        None,
        "geen json",
        "Hier is het oordeel: " + json.dumps(_fail_uitvoer()),
        json.dumps(_fail_uitvoer()) + json.dumps(_fail_uitvoer()),
        json.dumps([_fail_uitvoer()]),
        json.dumps(_fail_uitvoer())[:-5],
        json.dumps(_fail_uitvoer()).replace('"none"', "NaN", 1),
    ],
    ids=[
        "leeg",
        "witruimte",
        "none",
        "tekst",
        "tekst-ervoor",
        "twee-objecten",
        "lijst",
        "afgekapt",
        "nan",
    ],
)
async def test_misvormd_antwoord_is_error(tekst):
    ai = FakeAI(tekst)
    resultaat = await _dienst(ai).assess(_invoer())
    assert resultaat.status == "error"
    assert resultaat.document.foutcategorie == "invalid_output"
    assert resultaat.reden == "malformed_response"
    assert resultaat.document.oordeel is None


@pytest.mark.parametrize(
    "tekst",
    [
        '{"verdict": "pass", ' + json.dumps(_fail_uitvoer())[1:],
        json.dumps(_fail_uitvoer())[:-1] + ', "reason": "tweede reden"}',
        json.dumps(_fail_uitvoer()).replace(
            '"function": "actor_prescription"',
            '"function": "criterion", "function": "actor_prescription"',
        ),
    ],
    ids=["verdict-eerst", "reason-laatst", "genest"],
)
async def test_dubbele_sleutels_zijn_error_en_nooit_de_laatste_waarde(tekst):
    assert json.loads(tekst)  # stdlib zou stil de laatste waarde kiezen
    ai = FakeAI(tekst)
    resultaat = await _dienst(ai).assess(_invoer())
    assert resultaat.status == "error"
    assert resultaat.document.foutcategorie == "invalid_output"
    assert resultaat.reden == "duplicate_keys"


async def test_antwoord_boven_de_tekengrens_is_error():
    ai = FakeAI(json.dumps(_fail_uitvoer()))
    resultaat = await _dienst(ai, budget=_budget(max_antwoordtekens=50)).assess(
        _invoer()
    )
    assert resultaat.status == "error"
    assert resultaat.document.foutcategorie == "invalid_output"
    assert resultaat.reden == "response_too_long"


async def test_markdown_codeblok_rond_een_object_wordt_aanvaard():
    ai = FakeAI("```json\n" + json.dumps(_fail_uitvoer()) + "\n```")
    resultaat = await _dienst(ai).assess(_invoer())
    assert resultaat.status == "fail"


async def test_c117_fictief_citaat_is_invalid_citation():
    uitvoer = _fail_uitvoer()
    uitvoer["passages"][0]["quote"] = "de behandelaar moet weigeren"
    uitvoer["passages"][0]["end"] = uitvoer["passages"][0]["start"] + len(
        "de behandelaar moet weigeren"
    )
    ai = FakeAI(uitvoer)
    resultaat = await _dienst(ai).assess(_invoer())
    assert resultaat.status == "error"
    assert resultaat.document.foutcategorie == "invalid_citation"
    assert resultaat.reden == "invalid_citation"
    assert resultaat.document.oordeel is None


async def test_citaat_op_verkeerde_positie_is_invalid_citation():
    uitvoer = _fail_uitvoer()
    uitvoer["passages"][0]["start"] += 1
    uitvoer["passages"][0]["end"] += 1
    resultaat = await _dienst(FakeAI(uitvoer)).assess(_invoer())
    assert resultaat.document.foutcategorie == "invalid_citation"


async def test_scoreveld_in_de_uitvoer_is_invalid_output():
    resultaat = await _dienst(FakeAI(_fail_uitvoer(score=0.4))).assess(_invoer())
    assert resultaat.status == "error"
    assert resultaat.document.foutcategorie == "invalid_output"
    assert resultaat.reden == "invalid_output"


@pytest.mark.parametrize("gerapporteerd", ["ander-model", "", MODEL.upper()])
async def test_ander_of_onbekend_responsmodel_is_technische_fout(gerapporteerd):
    ai = FakeAI(_fail_uitvoer(), model=gerapporteerd)
    resultaat = await _dienst(ai).assess(_invoer())
    assert resultaat.status == "error"
    assert resultaat.document.foutcategorie == "provider"
    assert resultaat.reden == "model_mismatch"
    assert resultaat.document.oordeel is None


async def test_antwoord_uit_ruwe_cache_is_technische_fout():
    ai = FakeAI(_fail_uitvoer(), cached=True)
    resultaat = await _dienst(ai).assess(_invoer())
    assert resultaat.status == "error"
    assert resultaat.document.foutcategorie == "transport"
    assert resultaat.reden == "raw_cache_used"


# --- geldige beoordelingen via het WP1-contract -----------------------------------


async def test_geldig_fail_oordeel_met_volledige_binding_en_eerlijke_metadata():
    ai = FakeAI(_fail_uitvoer())
    norm = laad_int02_norm()
    invoer = _invoer()
    resultaat = await _dienst(ai).assess(invoer, correlation_id="c-1")
    doc = resultaat.document
    assert resultaat.status == "fail"
    assert resultaat.melding.startswith(f"INT-02 — Voldoet niet. '{PASSAGE}'")
    assert doc.oordeel == _fail_uitvoer()
    assert doc.invoer == invoer
    assert resultaat.reden is None
    assert resultaat.gecachet is False
    assert resultaat.task_type == "validation"
    assert resultaat.profiel_id == "fixture-offline-1"
    assert resultaat.promptversie == PROMPT_VERSION
    assert len(resultaat.prompt_sha256) == 64
    assert len(resultaat.antwoord_sha256) == 64
    assert resultaat.uitzonderingstype is None
    binding = doc.binding
    assert binding.provider == PROVIDER
    assert binding.model == MODEL
    assert binding.normversie == NORMVERSIE
    assert binding.normhash == norm.normhash
    assert binding.promptversie == PROMPT_VERSION
    uitvoering = doc.uitvoering
    assert uitvoering.actor == "ai"
    assert uitvoering.status == "completed"
    # Herijkt (review F3): de interface meldt het aantal pogingen niet; de
    # eerdere 1 was de beginwaarde van de logteller, geen meting.
    assert uitvoering.transportpogingen == ONBEKEND
    assert isinstance(uitvoering.duur_ms, int) and uitvoering.duur_ms >= 0
    assert uitvoering.tijdstip != ONBEKEND
    # AIServiceInterface meldt geen providerversie, geen in/uit-tokens en geen kosten.
    assert uitvoering.modelversie == ONBEKEND
    assert uitvoering.invoertokens == ONBEKEND
    assert uitvoering.uitvoertokens == ONBEKEND
    assert uitvoering.kosten == ONBEKEND
    # Het document is herleidbaar en actueel onder zijn eigen configuratie.
    actueel = toets_actualiteit(doc, invoer, binding.configuratie())
    assert (actueel.status, actueel.melding) == ("fail", resultaat.melding)


async def test_onvoldoende_informatie_wordt_review_required_met_een_vraag():
    resultaat = await _dienst(FakeAI(_onvoldoende_uitvoer())).assess(_invoer())
    assert resultaat.status == "review_required"
    assert resultaat.document.reden == "insufficient_information"
    assert resultaat.document.vraag == "Welke bijlage is bedoeld?"


async def test_offsets_zijn_python_unicode_codepoints():
    kern = "Ding 𝔸 met 😀 dat de behandelaar moet afwijzen."
    quote = "de behandelaar moet afwijzen"
    goed = _fail_uitvoer(kern=kern, quote=quote)
    resultaat = await _dienst(FakeAI(goed)).assess(_invoer(kern=kern))
    assert resultaat.status == "fail"
    utf16 = _fail_uitvoer(kern=kern, quote=quote)
    utf16["passages"][0][
        "start"
    ] += 2  # twee astrale tekens = twee extra UTF-16-eenheden
    utf16["passages"][0]["end"] += 2
    fout = await _dienst(FakeAI(utf16)).assess(_invoer(kern=kern))
    assert fout.document.foutcategorie == "invalid_citation"


# --- onveranderlijk resultaat ----------------------------------------------------


async def test_resultaat_en_document_zijn_onveranderlijk():
    resultaat = await _dienst(FakeAI(_fail_uitvoer())).assess(_invoer())
    with pytest.raises(dataclasses.FrozenInstanceError):
        resultaat.reden = "x"
    with pytest.raises(dataclasses.FrozenInstanceError):
        resultaat.document.status = "pass"


# --- cache ------------------------------------------------------------------------


async def test_zelfde_binding_levert_gecachet_resultaat_zonder_tweede_aanroep():
    ai = FakeAI(_fail_uitvoer())
    dienst = _dienst(ai)
    eerste = await dienst.assess(_invoer())
    tweede = await dienst.assess(_invoer())
    assert len(ai.calls) == 1
    assert eerste.gecachet is False
    assert tweede.gecachet is True
    assert tweede.document == eerste.document
    assert tweede.status == "fail"


async def test_mutatie_van_een_gelezen_oordeel_raakt_de_cache_niet():
    dienst = _dienst(FakeAI(_fail_uitvoer()))
    eerste = await dienst.assess(_invoer())
    kopie = eerste.document.oordeel
    kopie["verdict"] = "pass"
    tweede = await dienst.assess(_invoer())
    assert tweede.document.oordeel["verdict"] == "fail"


@pytest.mark.parametrize(
    "over",
    [
        {"kern": KERN + " "},
        {"begrip": "aanvraag2"},
        {"bedoeling": None},
        {"juridische_context": ["strafrecht"]},
        {"bronnen": [{"id": "B1", "tekst": "Andere brontekst."}]},
        {
            "bronnen": [
                {"id": "B2", "tekst": "Een aanvraag is een verzoek om een besluit."}
            ]
        },
    ],
    ids=["kern-witruimte", "begrip", "bedoeling", "context", "brontekst", "bron-id"],
)
async def test_gewijzigde_invoer_glipt_niet_langs_de_cache(over):
    ai = FakeAI(_fail_uitvoer(), _fail_uitvoer())
    dienst = _dienst(ai)
    await dienst.assess(_invoer())
    tweede = await dienst.assess(_invoer(**over))
    assert len(ai.calls) == 2
    assert tweede.gecachet is False


async def test_gewijzigde_router_glipt_niet_langs_de_cache():
    ai = FakeAI(_fail_uitvoer())
    router = FakeRouter()
    dienst = _dienst(ai, router)
    await dienst.assess(_invoer())
    router.model = "ander-model"
    tweede = await dienst.assess(_invoer())
    assert tweede.gecachet is False
    assert tweede.reden == "router_mismatch"
    assert tweede.document.oordeel is None


async def test_gewijzigde_prompttekst_glipt_niet_langs_de_cache(monkeypatch):
    ai = FakeAI(_fail_uitvoer(), _fail_uitvoer())
    dienst = _dienst(ai)
    eerste = await dienst.assess(_invoer())
    monkeypatch.setattr(dienstmodule, "T_TEKST", dienstmodule.T_TEKST + " Gewijzigd.")
    tweede = await dienst.assess(_invoer())
    assert len(ai.calls) == 2
    assert tweede.gecachet is False
    assert tweede.prompt_sha256 != eerste.prompt_sha256


async def test_gewijzigde_promptversie_glipt_niet_langs_de_cache(monkeypatch):
    ai = FakeAI(_fail_uitvoer(), _fail_uitvoer())
    dienst = _dienst(ai)
    await dienst.assess(_invoer())
    monkeypatch.setattr(dienstmodule, "PROMPT_VERSION", "def835-int02-prompt/99")
    tweede = await dienst.assess(_invoer())
    assert len(ai.calls) == 2
    assert tweede.document.binding.promptversie == "def835-int02-prompt/99"


async def test_norm_budget_en_profiel_zitten_in_de_binding():
    norm = laad_int02_norm()
    ander = dataclasses.replace(norm, toetsvraag=norm.toetsvraag + " Echt?")
    basis = await _dienst(FakeAI(_fail_uitvoer())).assess(_invoer())
    varianten = [
        await _dienst(FakeAI(_fail_uitvoer()), norm=ander).assess(_invoer()),
        await _dienst(
            FakeAI(_fail_uitvoer()), budget=_budget(max_uitvoertokens=801)
        ).assess(_invoer()),
        await _dienst(
            FakeAI(_fail_uitvoer()), profiel=_profiel(profiel_id="fixture-offline-2")
        ).assess(_invoer()),
        await _dienst(
            FakeAI(_fail_uitvoer()), profiel=_profiel(kwalificatie="ander besluit")
        ).assess(_invoer()),
    ]
    for variant in varianten:
        assert variant.status == "fail"
        assert variant.document.binding != basis.document.binding
        # Het oude document is onder de nieuwe configuratie historisch.
        actueel = toets_actualiteit(
            basis.document, _invoer(), variant.document.binding.configuratie()
        )
        assert actueel.reden == "historical"


@pytest.mark.parametrize(
    "fout",
    [
        "geen json",
        AIServiceError("x"),
        json.dumps(_fail_uitvoer(quote="bestaat niet", kern="bestaat niet")),
    ],
    ids=["malformed", "transport", "citaat"],
)
async def test_fouten_worden_nooit_gecachet(fout):
    ai = FakeAI(fout, _fail_uitvoer())
    dienst = _dienst(ai)
    eerste = await dienst.assess(_invoer())
    tweede = await dienst.assess(_invoer())
    assert eerste.status == "error"
    assert tweede.status == "fail"
    assert len(ai.calls) == 2


async def test_timeout_wordt_niet_gecachet():
    ai = FakeAI(Hang(), _fail_uitvoer())
    dienst = _dienst(ai, budget=_budget(deadline_seconden=0.05))
    eerste = await dienst.assess(_invoer())
    tweede = await dienst.assess(_invoer())
    assert eerste.reden == "timeout"
    assert tweede.status == "fail"
    assert len(ai.calls) == 2


async def test_cache_is_begrensd_lru():
    ai = FakeAI(*[_fail_uitvoer() for _ in range(5)])
    dienst = _dienst(ai, cache_size=2)
    for begrip in ("a", "b", "c"):
        await dienst.assess(_invoer(begrip=begrip))
    assert len(ai.calls) == 3
    await dienst.assess(_invoer(begrip="c"))
    assert len(ai.calls) == 3
    await dienst.assess(_invoer(begrip="a"))
    assert len(ai.calls) == 4


async def test_cachegrootte_nul_cachet_niets():
    ai = FakeAI(_fail_uitvoer(), _fail_uitvoer())
    dienst = _dienst(ai, cache_size=0)
    await dienst.assess(_invoer())
    await dienst.assess(_invoer())
    assert len(ai.calls) == 2


# --- logging zonder inhoud ---------------------------------------------------------

GEHEIM = "GEHEIM-INHOUD-7Q"


@pytest.mark.parametrize(
    "uitkomst",
    [
        "Tekst " + GEHEIM,
        AIServiceError(GEHEIM),
        Hang(),
        json.dumps(_fail_uitvoer(quote=GEHEIM, kern=GEHEIM)),
    ],
    ids=["misvormd", "uitzondering", "timeout", "fictief-citaat"],
)
async def test_log_bevat_geen_invoer_prompt_antwoord_of_uitzonderingstekst(
    uitkomst, caplog
):
    invoer = _invoer(
        kern=f"Aanvraag die {GEHEIM} bevat.",
        bronnen=[{"id": "B1", "tekst": GEHEIM}],
    )
    dienst = _dienst(FakeAI(uitkomst), budget=_budget(deadline_seconden=0.05))
    with caplog.at_level(logging.DEBUG):
        resultaat = await dienst.assess(invoer, correlation_id="corr-42")
    eigen = [r for r in caplog.records if r.name == DIENSTLOGGER]
    # Niet vacuüm: de technische fout wordt wél gelogd, met reden.
    assert any(r.levelno >= logging.WARNING for r in eigen)
    assert any(resultaat.reden in r.getMessage() for r in eigen)
    for record in eigen:
        assert GEHEIM not in record.getMessage()
        assert GEHEIM not in str(record.args)
    assert resultaat.status == "error"


# --- echte AIServiceV2 + AsyncGPTClient, fake provider aan de netwerkgrens -----


class _Provider:
    """Providerclient aan de netwerkgrens (AsyncAIClient-vorm)."""

    provider_name = PROVIDER

    def __init__(self, *uitkomsten, gerapporteerd_model=None, stop_reason="end_turn"):
        # Correctie F1: standaard een afgeronde stopreden, zoals de
        # Anthropic-adapter die in `ChatResponse.stop_reason` doorgeeft.
        self.uitkomsten = list(uitkomsten)
        self.calls: list[dict] = []
        self.gerapporteerd_model = gerapporteerd_model
        self.stop_reason = stop_reason

    async def chat_completion(
        self, messages, model, temperature=0.7, max_tokens=300, timeout=None, **kw
    ):
        self.calls.append(
            {"messages": messages, "model": model, "max_tokens": max_tokens, "kw": kw}
        )
        uitkomst = self.uitkomsten.pop(0) if self.uitkomsten else _fail_uitvoer()
        if isinstance(uitkomst, BaseException):
            raise uitkomst
        return ChatResponse(
            text=json.dumps(uitkomst, ensure_ascii=False),
            tokens_used=5,
            model=self.gerapporteerd_model or model,
            stop_reason=self.stop_reason,
        )


def _echte_ai(provider: _Provider) -> AIServiceV2:
    return AIServiceV2(
        rate_limit_config=RateLimitConfig(max_retries=3, backoff_factor=1.0),
        use_cache=True,
        ai_client=provider,
        model_router=FakeRouter(),
    )


async def test_echte_ai_laag_een_aanroep_met_sdk_retries_nul_en_exacte_berichten():
    provider = _Provider(_fail_uitvoer())
    invoer = _invoer()
    resultaat = await _dienst(_echte_ai(provider)).assess(invoer)
    assert resultaat.status == "fail"
    assert len(provider.calls) == 1
    call = provider.calls[0]
    assert call["kw"] == {"max_retries": 0}
    assert call["model"] == MODEL
    assert call["max_tokens"] == 800
    systeem, data = bouw_int02_prompt(invoer, laad_int02_norm())
    assert [(m.role, m.content) for m in call["messages"]] == [
        ("system", systeem),
        ("user", data),
    ]


async def test_echte_ai_laag_verbindingsfout_geeft_een_poging_ondanks_retryconfig():
    provider = _Provider(AIConnectionClientError("x"), _fail_uitvoer())
    resultaat = await _dienst(_echte_ai(provider)).assess(_invoer())
    assert len(provider.calls) == 1
    assert resultaat.status == "error"
    assert resultaat.document.foutcategorie == "transport"
    # Herijkt (review F3): het ene providercall is hierboven aan de netwerkgrens
    # gemeten; de dienst zelf kan dat via de interface niet vaststellen.
    assert resultaat.document.uitvoering.transportpogingen == ONBEKEND


async def test_echte_ai_laag_geen_ruwe_cache_ondanks_use_cache_true():
    provider = _Provider(_fail_uitvoer(), _fail_uitvoer())
    dienst = _dienst(_echte_ai(provider), cache_size=0)
    await dienst.assess(_invoer())
    await dienst.assess(_invoer())
    assert len(provider.calls) == 2


async def test_echte_ai_laag_afgekapt_antwoord_is_truncated_response():
    provider = _Provider(_fail_uitvoer(), stop_reason="max_tokens")
    resultaat = await _dienst(_echte_ai(provider)).assess(_invoer())
    assert resultaat.status == "error"
    assert resultaat.reden == "truncated_response"


async def test_echte_ai_laag_meldt_geen_providerversie_dus_modelversie_unknown():
    provider = _Provider(
        _fail_uitvoer(), gerapporteerd_model="fake-int02-model-20260927"
    )
    resultaat = await _dienst(_echte_ai(provider)).assess(_invoer())
    assert resultaat.status == "fail"
    assert resultaat.document.uitvoering.modelversie == ONBEKEND


# --- GREEN-aanvullingen (opdracht wp2-opdracht-claude-groen-v1, eerst rood) -----


@pytest.mark.parametrize(
    "constante", ["Infinity", "-Infinity"], ids=["infinity", "min-infinity"]
)
async def test_oneindigheid_in_het_antwoord_is_malformed(constante):
    tekst = json.dumps(_fail_uitvoer()).replace('"none"', constante, 1)
    resultaat = await _dienst(FakeAI(tekst)).assess(_invoer())
    assert resultaat.status == "error"
    assert resultaat.document.foutcategorie == "invalid_output"
    assert resultaat.reden == "malformed_response"


async def test_getal_boven_de_cijferlimiet_is_malformed_en_geen_uitzondering():
    uitvoer = _fail_uitvoer()
    tekst = json.dumps(uitvoer).replace(
        f'"start": {uitvoer["passages"][0]["start"]}', '"start": ' + "9" * 5000, 1
    )
    budget = _budget(max_antwoordtekens=100000)
    resultaat = await _dienst(FakeAI(tekst), budget=budget).assess(_invoer())
    assert resultaat.status == "error"
    assert resultaat.reden == "malformed_response"


async def test_te_diepe_nesting_is_malformed_en_geen_uitzondering():
    tekst = '{"verdict": ' + "[" * 200000 + "]" * 200000 + "}"
    budget = _budget(max_antwoordtekens=1000000)
    resultaat = await _dienst(FakeAI(tekst), budget=budget).assess(_invoer())
    assert resultaat.status == "error"
    assert resultaat.reden == "malformed_response"


async def test_antwoordgrens_geldt_voor_het_parsen():
    # Te lang én misvormd: de grens wint, er wordt niet eerst geparst.
    tekst = "[" * 5000
    resultaat = await _dienst(
        FakeAI(tekst), budget=_budget(max_antwoordtekens=100)
    ).assess(_invoer())
    assert resultaat.reden == "response_too_long"


async def test_snapshot_bewaart_exacte_tekst_terwijl_de_log_die_niet_bevat(caplog):
    kern = f"Aanvraag die {GEHEIM} bevat."
    invoer = _invoer(kern=kern)
    with caplog.at_level(logging.DEBUG):
        resultaat = await _dienst(FakeAI("geen json")).assess(invoer)
    # Bewust bewaard: de exacte invoersnapshot hoort bij het document.
    assert resultaat.document.invoer.kern == kern
    assert GEHEIM in json.dumps(resultaat.document.als_dict(), ensure_ascii=False)
    # Geen loglek: de eigen log bevat die tekst niet, wel de reden.
    eigen = [r for r in caplog.records if r.name == DIENSTLOGGER]
    assert any("malformed_response" in r.getMessage() for r in eigen)
    assert all(GEHEIM not in r.getMessage() for r in eigen)


async def test_norm_is_een_snapshot_bij_constructie(monkeypatch):
    oorspronkelijk = laad_int02_norm()
    dienst = _dienst(FakeAI(_fail_uitvoer(), _fail_uitvoer()))
    ander = dataclasses.replace(oorspronkelijk, toetsvraag="Andere toetsvraag?")
    monkeypatch.setattr(dienstmodule, "laad_int02_norm", lambda *a, **k: ander)
    resultaat = await dienst.assess(_invoer())
    assert resultaat.document.binding.normhash == oorspronkelijk.normhash
    # Pas een nieuwe instantie leest de (gewijzigde) norm opnieuw.
    nieuw = await _dienst(FakeAI(_fail_uitvoer())).assess(_invoer())
    assert nieuw.document.binding.normhash == ander.normhash


# --- correcties na review wp2-codex-review-v1 (eerst rood) ----------------------

# F1: alleen een aantoonbaar afgerond antwoord kan een oordeel dragen.


async def test_f1_ontbrekende_stopreden_is_geen_oordeel_en_wordt_niet_gecachet():
    ai = FakeAI(_fail_uitvoer(), _fail_uitvoer(), stop_reason=None)
    dienst = _dienst(ai)
    eerste = await dienst.assess(_invoer())
    tweede = await dienst.assess(_invoer())
    assert eerste.status == "error"
    assert eerste.document.foutcategorie == "invalid_output"
    assert eerste.reden == "unconfirmed_completion"
    assert eerste.document.oordeel is None
    assert tweede.gecachet is False
    assert len(ai.calls) == 2


@pytest.mark.parametrize("reden", ["refusal", "pause_turn", "tool_use", "iets_nieuws"])
async def test_f1_onbekende_of_niet_afgeronde_stopreden_is_geen_oordeel(reden):
    resultaat = await _dienst(FakeAI(_fail_uitvoer(), stop_reason=reden)).assess(
        _invoer()
    )
    assert resultaat.status == "error"
    assert resultaat.reden == "unconfirmed_completion"
    assert resultaat.stop_reason == reden


async def test_f1_openai_afkapreden_length_is_afgekapt():
    resultaat = await _dienst(FakeAI(_fail_uitvoer(), stop_reason="length")).assess(
        _invoer()
    )
    assert resultaat.status == "error"
    assert resultaat.reden == "truncated_response"


class _OpenAISDK:
    """Fake OpenAI-SDK aan de netwerkgrens; de adapter zelf is echt."""

    def __init__(self, finish_reason):
        self.finish_reason = finish_reason
        self.calls = 0
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def with_options(self, **kwargs):
        assert kwargs == {"max_retries": 0}
        return self

    async def create(self, **kwargs):
        self.calls += 1
        bericht = SimpleNamespace(content=json.dumps(_fail_uitvoer()))
        return SimpleNamespace(
            choices=[
                SimpleNamespace(message=bericht, finish_reason=self.finish_reason)
            ],
            usage=SimpleNamespace(total_tokens=800),
            model=kwargs["model"],
        )


def _openai_dienst(sdk: _OpenAISDK):
    client = OpenAIClient(api_key="offline-testsleutel-zonder-netwerk")
    client._sdk_voor_deze_loop = lambda: sdk
    router = FakeRouter(provider="openai", model="gpt-4.1")
    ai = AIServiceV2(
        rate_limit_config=RateLimitConfig(max_retries=3, backoff_factor=1.0),
        use_cache=True,
        ai_client=client,
        model_router=router,
    )
    return _dienst(ai, router, profiel=_profiel(provider="openai", model="gpt-4.1"))


async def test_f1_echte_openai_adapter_afgekapt_antwoord_is_geen_oordeel():
    sdk = _OpenAISDK("length")
    dienst = _openai_dienst(sdk)
    eerste = await dienst.assess(_invoer())
    tweede = await dienst.assess(_invoer())
    assert eerste.status == "error"
    assert eerste.document.oordeel is None
    # De adapter geeft finish_reason niet door: niet aantoonbaar afgerond.
    assert eerste.reden == "unconfirmed_completion"
    assert tweede.gecachet is False
    assert sdk.calls == 2


async def test_f1_openai_route_blijft_geblokkeerd_zolang_de_stopreden_ontbreekt():
    # Ook finish_reason "stop" bereikt de dienst niet: bewuste beperking.
    resultaat = await _openai_dienst(_OpenAISDK("stop")).assess(_invoer())
    assert resultaat.status == "error"
    assert resultaat.reden == "unconfirmed_completion"


# F2: het effectieve capability-beleid van de router zit in de binding.


def _router_met_beleid():
    config = copy.deepcopy(ModelRouter._DEFAULT_CONFIG)
    provider, model = ModelRouter(copy.deepcopy(config)).get_model("validation")
    config["capabilities"] = {
        provider: {
            "temperature": {"model_families": [model]},
            "thinking_default_on": {"model_families": [model]},
        }
    }
    return config, ModelRouter(config), provider, model


async def test_f2_gewijzigd_beleid_bij_zelfde_model_geen_cache_en_historisch():
    config, router, provider, model = _router_met_beleid()
    adapter = AnthropicClient(api_key="offline-testsleutel", model_router=router)
    oud_beleid = repr(adapter._verzendbeleid(model, 0.0))
    profiel = _profiel(provider=provider, model=model)
    ai = FakeAI(_fail_uitvoer(), _fail_uitvoer())
    dienst = _dienst(ai, router, profiel=profiel)
    oud = await dienst.assess(_invoer())
    for beleid in config["capabilities"][provider].values():
        beleid["model_families"].clear()
    # Het echte verzendbeleid van de bestaande adapter is werkelijk veranderd.
    assert repr(adapter._verzendbeleid(model, 0.0)) != oud_beleid
    assert router.get_model("validation") == (provider, model)
    nieuw = await dienst.assess(_invoer())
    assert nieuw.gecachet is False
    assert len(ai.calls) == 2
    vers = await _dienst(FakeAI(_fail_uitvoer()), router, profiel=profiel).assess(
        _invoer()
    )
    assert vers.document.binding != oud.document.binding
    actueel = toets_actualiteit(
        oud.document, _invoer(), vers.document.binding.configuratie()
    )
    assert actueel.reden == "historical"


@pytest.mark.parametrize(
    ("veld", "waarde"), [("temperature", False), ("thinking", True)]
)
async def test_f2_elk_beleidsonderdeel_verandert_de_binding(veld, waarde):
    basis = await _dienst(FakeAI(_fail_uitvoer())).assess(_invoer())
    router = FakeRouter(**{veld: waarde})
    ander = await _dienst(FakeAI(_fail_uitvoer()), router).assess(_invoer())
    assert ander.status == "fail"
    assert ander.document.binding != basis.document.binding


class _RouterZonderBeleid:
    def get_model(self, task_type):
        return PROVIDER, MODEL


@pytest.mark.parametrize(
    "router",
    [
        FakeRouter(beleidsfout=RuntimeError("GEHEIM-BELEID-7Q")),
        FakeRouter(temperature="ja"),
        FakeRouter(thinking=None),
        _RouterZonderBeleid(),
    ],
    ids=["fout", "geen-bool-temperature", "geen-bool-thinking", "geen-beleid"],
)
async def test_f2_onbekend_beleid_blokkeert_zonder_verzonnen_default(router, caplog):
    ai = FakeAI()
    with caplog.at_level(logging.DEBUG):
        resultaat = await _dienst(ai, router).assess(_invoer())
    _assert_geblokkeerd(resultaat, ai, "router_policy_unavailable")
    assert "GEHEIM-BELEID-7Q" not in caplog.text
    assert "GEHEIM-BELEID-7Q" not in repr(resultaat)


# F3: geen transportpoging rapporteren die niet is vastgesteld.


async def test_f3_wachten_op_capaciteit_geeft_nul_providercalls_en_geen_verzonnen_poging():
    provider = _Provider()
    ai = _echte_ai(provider)
    ai._get_client().rate_limiter.semaphore = asyncio.Semaphore(0)
    resultaat = await _dienst(ai, budget=_budget(deadline_seconden=0.03)).assess(
        _invoer()
    )
    assert resultaat.reden == "timeout"
    assert provider.calls == []
    assert resultaat.document.uitvoering.transportpogingen == ONBEKEND


async def test_f3_uitzondering_van_de_ai_laag_geeft_onbekend_aantal_pogingen():
    resultaat = await _dienst(FakeAI(AIServiceError("x"))).assess(_invoer())
    assert resultaat.status == "error"
    assert resultaat.document.uitvoering.transportpogingen == ONBEKEND
