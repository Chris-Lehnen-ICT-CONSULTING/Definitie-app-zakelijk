"""DEF-842: CON-02-bronbeoordeling — JSON rond tekst/fences en afgekapte antwoorden.

Reproductie van "technische fout (malformed_response): modelantwoord is geen
(volledig) JSON-object" met nep-antwoorden op de AI-grens (geen netwerk, geen
echt model):

* geldige JSON met omringende tekst, codefences of accolades in die tekst
  wordt gelezen;
* een op het tokenbudget afgekapt antwoord (`stop_reason` max_tokens/length)
  krijgt precies één herhaling met een hoger budget en is daarna, als het nog
  steeds afgekapt is, de herkenbare technische fout `truncated_response`;
* de route vraagt geen ruwe antwoordcache (een gecachet afgekapt antwoord
  mist de stopreden en zou steeds terugkomen);
* half-geldige JSON wordt nooit gerepareerd en de foutreden bevat geen
  antwoordinhoud.
"""

import json
import time

import pytest

from domain.sources.contract import (
    ONDERDEEL_GEZAG,
    ONDERDEEL_STEUN,
    ONDERDEEL_VERWIJZING,
)
from services.ai.base_client import ChatResponse
from services.ai_service_v2 import AIServiceV2
from services.interfaces import AIGenerationResult, AITimeoutError
from services.validation.source_assessment_service import (
    SourceAssessmentService,
    lees_modeluitvoer,
    parse_modeluitvoer,
)
from utils.async_api import RateLimitConfig

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]

BEGRIP = "verdachte"
TEKST = (
    "Persoon te wiens aanzien uit feiten of omstandigheden een redelijk "
    "vermoeden van schuld aan een strafbaar feit voortvloeit."
)
CONTEXT = {
    "organisatorische_context": ["OM"],
    "juridische_context": ["strafrecht"],
    "wettelijke_basis": ["Wetboek van Strafvordering"],
}
PASSAGE = (
    "Artikel 27. Als verdachte wordt aangemerkt degene te wiens aanzien uit "
    "feiten of omstandigheden een redelijk vermoeden van schuld aan eenig "
    "strafbaar feit voortvloeit."
)
BRONNEN = [
    {
        "provider": "documents",
        "doc_id": "sv-27",
        "filename": "wetboek-van-strafvordering.txt",
        "citation_label": "art. 27",
        "bron_type": "wet",
        "url": "https://intern.example/sv#art-27",
        "snippet": PASSAGE,
        "score": 1.0,
    }
]
CITAAT = "een redelijk vermoeden van schuld aan eenig strafbaar feit"


def _uitvoer():
    bewijs = [{"source_id": "doc:sv-27", "quote": CITAAT}]
    return {
        ONDERDEEL_GEZAG: {
            "status": "pass",
            "reason": "Wettelijke definitiebepaling.",
            "uncertainty": None,
            "sources": [
                {
                    "source_id": "doc:sv-27",
                    "profile": "wet_regelgeving",
                    "applicable": True,
                    "reason": "definitiebepaling",
                }
            ],
            "evidence": list(bewijs),
        },
        ONDERDEEL_STEUN: {
            "status": "pass",
            "reason": "Het redelijk vermoeden van schuld is gedekt.",
            "uncertainty": None,
            "claims": [
                {
                    "aspect": "kenmerk",
                    "text": "redelijk vermoeden van schuld",
                    "supported": True,
                    "source_id": "doc:sv-27",
                }
            ],
            "evidence": list(bewijs),
        },
        ONDERDEEL_VERWIJZING: {
            "status": "pass",
            "reason": "Artikel en hyperlink aanwezig.",
            "uncertainty": None,
            "sources": [
                {"source_id": "doc:sv-27", "locatable": True, "reason": "art. 27"}
            ],
            "evidence": [{"source_id": "doc:sv-27", "quote": "Artikel 27"}],
        },
    }


GELDIG = json.dumps(_uitvoer(), ensure_ascii=False, indent=2)
AFGEKAPT = GELDIG[: len(GELDIG) * 2 // 3]


class NepProvider:
    """AI-grens die per aanroep (tekst, stop_reason) of een exception teruggeeft
    en de kwargs vastlegt."""

    def __init__(self, *antwoorden):
        self.antwoorden = list(antwoorden)
        self.calls = []
        self.default_model = "nep-model"

    async def generate_definition(self, prompt, **kwargs):
        self.calls.append(kwargs)
        uitkomst = self.antwoorden.pop(0)
        if isinstance(uitkomst, Exception):
            raise uitkomst
        tekst, stop_reason = uitkomst
        return AIGenerationResult(
            text=tekst,
            model="nep-model-1",
            tokens_used=10,
            generation_time=0.01,
            metadata={} if stop_reason is None else {"stop_reason": stop_reason},
        )


class NepRouter:
    def get_model(self, task_type):
        return "anthropic", "nep-opus"


def _service(*antwoorden, **kw):
    ai = NepProvider(*antwoorden)
    return SourceAssessmentService(ai, model_router=NepRouter(), **kw), ai


async def _assess(service):
    beoordeling = await service.assess(
        BEGRIP, TEKST, CONTEXT, BRONNEN, peildatum="2026-10-07"
    )
    return beoordeling.als_dict()


# --- parser ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "antwoord",
    [
        GELDIG,
        "```json\n" + GELDIG + "\n```",
        "```JSON\n" + GELDIG + "\n```",
        "```\n" + GELDIG + "\n```",
        "Hier is het gevraagde object:\n" + GELDIG + "\nEinde van de beoordeling.",
        "Ik geef {zoals gevraagd} het object:\n" + GELDIG,
        GELDIG + "\nToelichting: zie {bron} en artikel 27.",
        "```json\n" + GELDIG + "\n```\nNoot: de passage {art. 27} is leidend.",
        '{"los": 1}\n' + GELDIG,
        "[" + GELDIG + "]",
    ],
    ids=[
        "kaal",
        "fences-json",
        "fences-JSON",
        "fences-zonder-taal",
        "tekst-ervoor-en-erna",
        "accolade-in-tekst-ervoor",
        "accolade-in-tekst-erna",
        "fences-plus-toelichting-met-accolade",
        "los-object-ervoor",
        "enkel-object-in-lijst",  # zoals de oude parser: eenduidig, één object
    ],
)
async def test_geldige_json_rond_tekst_of_fences_wordt_gelezen(antwoord):
    geparsed, reden = lees_modeluitvoer(antwoord)
    assert reden is None
    assert geparsed == _uitvoer()


async def test_letterlijk_regeleinde_in_tekstwaarde_wordt_geaccepteerd():
    tekst = GELDIG.replace(
        "Wettelijke definitiebepaling.", "Wettelijke\ndefinitiebepaling."
    )
    with pytest.raises(json.JSONDecodeError):
        json.loads(tekst)  # strikte JSON weigert een letterlijk regeleinde
    geparsed = parse_modeluitvoer(tekst)
    assert geparsed is not None
    assert geparsed[ONDERDEEL_GEZAG]["reason"] == "Wettelijke\ndefinitiebepaling."


@pytest.mark.parametrize(
    ("antwoord", "reden_bevat"),
    [
        (AFGEKAPT, "onvolledig of ongeldig JSON-object"),
        ("```json\n" + AFGEKAPT, "onvolledig of ongeldig JSON-object"),
        ("Hier komt het:\n" + AFGEKAPT, "onvolledig of ongeldig JSON-object"),
        (GELDIG + "\n" + GELDIG, "niet eenduidig"),
        ("Dit is geen JSON.", "geen JSON-object"),
        ("[]", "geen JSON-object"),
        ("", "leeg antwoord"),
        (None, "leeg antwoord"),
        # Bewust fail-closed: een objectbegin in proza dat geen JSON is,
        # maakt het antwoord ongeldig (geen gok welk object bedoeld is).
        ('Het veld {"status"} volgt:\n' + GELDIG, "onvolledig of ongeldig"),
    ],
    ids=[
        "afgekapt",
        "afgekapt-in-fence",
        "afgekapt-na-tekst",
        "twee-volledige-antwoorden",
        "geen-json",
        "lijst",
        "leeg",
        "geen-tekst",
        "json-achtige-proza-ervoor",
    ],
)
async def test_onbruikbaar_antwoord_wordt_niet_gerepareerd(antwoord, reden_bevat):
    geparsed, reden = lees_modeluitvoer(antwoord)
    assert geparsed is None
    assert reden_bevat in reden


async def test_afgekapt_object_wordt_niet_op_deelobjecten_doorzocht():
    """Een afgekapt antwoord bevat volledige deelobjecten; die tellen niet."""
    assert '"evidence": [' in AFGEKAPT
    assert parse_modeluitvoer(AFGEKAPT) is None


async def test_foutreden_bevat_geen_antwoordinhoud():
    geheim = '{"source_authority": {"reason": "UNIEK-GEHEIM-CITAAT'
    _, reden = lees_modeluitvoer(geheim)
    assert "UNIEK-GEHEIM-CITAAT" not in reden


# --- service --------------------------------------------------------------------


async def test_geldig_antwoord_in_fences_met_tekst_wordt_beoordeeld():
    antwoord = "Beoordeling:\n```json\n" + GELDIG + "\n```\nZie {art. 27}."
    service, ai = _service((antwoord, "end_turn"))
    d = await _assess(service)
    assert d["status"] == "assessed"
    assert d["error"] is None
    assert len(ai.calls) == 1
    assert d["parts"][ONDERDEEL_STEUN]["status"] == "pass"


async def test_gewone_aanroep_zonder_ruwe_cache_en_met_ruim_budget():
    service, ai = _service((GELDIG, "end_turn"))
    d = await _assess(service)
    assert d["status"] == "assessed"
    assert len(ai.calls) == 1
    assert ai.calls[0]["use_cache"] is False
    assert ai.calls[0]["max_tokens"] == 5000
    # De SDK-requesttimeout volgt de deadline (niet de 30 s-clientdefault).
    assert ai.calls[0]["timeout_seconds"] == 45
    assert ai.calls[0]["request_timeout"] == 45
    assert d["attribution"]["attempts"] == 1
    assert d["attribution"]["max_tokens"] == 5000
    assert d["attribution"]["stop_reason"] == "end_turn"


@pytest.mark.parametrize("stopreden", ["max_tokens", "length"])
async def test_afgekapt_antwoord_krijgt_een_herhaling_met_hoger_budget(stopreden):
    service, ai = _service((AFGEKAPT, stopreden), (GELDIG, "end_turn"))
    d = await _assess(service)
    assert d["status"] == "assessed"
    assert [c["max_tokens"] for c in ai.calls] == [5000, 10000]
    # De herhaling krijgt een naar rato langere deadline, ook voor de SDK.
    assert [c["timeout_seconds"] for c in ai.calls] == [45, 90]
    assert [c["request_timeout"] for c in ai.calls] == [45, 90]
    assert all(c["use_cache"] is False for c in ai.calls)
    assert d["attribution"]["attempts"] == 2
    assert d["attribution"]["max_tokens"] == 10000


async def test_ook_na_herhaling_afgekapt_is_truncated_response_en_niet_gecachet():
    service, ai = _service(
        (AFGEKAPT, "max_tokens"),
        (AFGEKAPT, "max_tokens"),
        (GELDIG, "end_turn"),
    )
    d = await _assess(service)
    assert d["status"] == "error"
    assert d["error"]["type"] == "truncated_response"
    assert "afgekapt op het tokenbudget" in d["error"]["message"]
    assert "max_tokens=10000" in d["error"]["message"]
    assert d["parts"] == {}
    assert d["raw_response_sha256"]
    assert len(ai.calls) == 2
    # Niet gecachet: een nieuwe beoordeling vraagt het model opnieuw.
    opnieuw = await _assess(service)
    assert opnieuw["status"] == "assessed"
    assert len(ai.calls) == 3


async def test_afgekapt_maar_toevallig_parseerbaar_telt_niet_als_oordeel():
    service, _ = _service((GELDIG, "max_tokens"), (GELDIG, "max_tokens"))
    d = await _assess(service)
    assert d["error"]["type"] == "truncated_response"
    assert d["parts"] == {}


async def test_afgekapte_json_zonder_stopreden_blijft_malformed_zonder_herhaling():
    service, ai = _service((AFGEKAPT, None))
    d = await _assess(service)
    assert d["status"] == "error"
    assert d["error"]["type"] == "malformed_response"
    assert "onvolledig of ongeldig JSON-object" in d["error"]["message"]
    assert len(ai.calls) == 1


async def test_herhalingsbudget_nooit_lager_dan_eerste_budget():
    service, ai = _service(
        (AFGEKAPT, "max_tokens"),
        (GELDIG, "end_turn"),
        max_tokens=3000,
        max_tokens_herhaling=1000,
    )
    await _assess(service)
    assert [c["max_tokens"] for c in ai.calls] == [3000, 3000]


async def test_fout_tijdens_herhaling_behoudt_de_afkapcontext():
    service, ai = _service(
        (AFGEKAPT, "max_tokens"), AITimeoutError("AI generation timed out")
    )
    d = await _assess(service)
    assert d["status"] == "error"
    assert d["error"]["type"] == "timeout"
    assert "tijdens de herhaling" in d["error"]["message"]
    assert d["attribution"]["attempts"] == 2
    assert d["attribution"]["max_tokens"] == 10000
    assert len(ai.calls) == 2


async def test_fout_bij_eerste_poging_noemt_geen_herhaling():
    service, _ = _service(AITimeoutError("AI generation timed out"))
    d = await _assess(service)
    assert d["error"]["type"] == "timeout"
    assert "herhaling" not in d["error"]["message"]
    assert d["attribution"]["attempts"] == 1


# --- AI-laag: request_timeout-opt-in (echte AIServiceV2 + AsyncGPTClient) --------


class _Netwerkgrens:
    """Providerclient aan de netwerkgrens; legt de timeout per aanroep vast."""

    provider_name = "nep"

    def __init__(self):
        self.timeouts = []

    async def chat_completion(
        self, messages, model, temperature=0.7, max_tokens=300, timeout=None, **kw
    ):
        self.timeouts.append(timeout)
        return ChatResponse(
            text=GELDIG, tokens_used=3, model=model, stop_reason="end_turn"
        )


def _ai_service(grens):
    class Router:
        def get_model(self, task_type):
            return "nep", "nep-model"

    return AIServiceV2(
        rate_limit_config=RateLimitConfig(max_retries=1, backoff_factor=1.0),
        use_cache=True,
        ai_client=grens,
        model_router=Router(),
    )


async def test_request_timeout_reist_door_naar_de_providerclient():
    grens = _Netwerkgrens()
    resultaat = await _ai_service(grens).generate_definition(
        prompt=f"p-{time.time_ns()}",
        task_type="validation",
        use_cache=False,
        request_timeout=90,
    )
    assert grens.timeouts == [90.0]
    assert resultaat.metadata.get("stop_reason") == "end_turn"


async def test_zonder_request_timeout_blijft_de_clientdefault():
    grens = _Netwerkgrens()
    await _ai_service(grens).generate_definition(
        prompt=f"p-{time.time_ns()}", task_type="validation", use_cache=False
    )
    assert grens.timeouts == [None]


async def test_con02_end_to_end_via_echte_ai_laag_zonder_ruwe_cache():
    """Zonder eigen dienstcache gaan twee identieke beoordelingen beide naar de
    provider: de ruwe 1-uurscache van de gedeelde AIServiceV2(use_cache=True)
    wordt niet gebruikt (die zou een afgekapt antwoord zonder stopreden blijven
    teruggeven). Beide met de requesttimeout van de dienst."""
    grens = _Netwerkgrens()
    service = SourceAssessmentService(
        _ai_service(grens), model_router=NepRouter(), cache_size=0
    )
    assert (await _assess(service))["status"] == "assessed"
    assert (await _assess(service))["status"] == "assessed"
    assert grens.timeouts == [45.0, 45.0]
