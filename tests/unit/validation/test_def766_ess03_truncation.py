"""DEF-766 correctieronde 3 (F1) — afgekapt modelantwoord is fail-closed in ESS-03.

Echte `AIServiceV2` en echte `AsyncGPTClient`; alleen de providerclient is een
fake aan de netwerkgrens die `ChatResponse.stop_reason` zet. Bewezen:

* `stop_reason == "max_tokens"` reist als `metadata["stop_reason"]` mee in het
  `AIGenerationResult` (additief; bestaande retourvorm ongewijzigd);
* de ESS-03-dienst maakt daarvan `status: error` met eigen foutcode
  `truncated_response` — géén oordeel, niet gecachet, reden benoemt de
  afkapping — onderscheidbaar van `malformed_response`, ook als de afgekapte
  tekst toevallig nog parseerbaar is;
* `end_turn` en een provider zonder `stop_reason` (bestaande fakes) laten de
  normale route ongemoeid;
* de providerclient krijgt geen extra kwargs (het transport blijft binnen
  `AsyncGPTClient`/`AIServiceV2`).
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from domain.ess03.contract import VERDICT_FAIL, Intentie
from domain.sources.normalisatie import canoniseer_bronnen
from services.ai.base_client import ChatResponse
from services.ai_service_v2 import AIServiceV2
from services.validation.ess03_assessment_service import Ess03AssessmentService
from utils.async_api import RateLimitConfig

pytestmark = [pytest.mark.unit]

BEGRIP = "boekexemplaar"
TEKST = (
    "Boekexemplaar dat uitsluitend door zijn ISBN van andere fysieke exemplaren "
    "wordt onderscheiden."
)
CONTEXT = {"organisatorische_context": ["Synthetische Bibliotheek"]}
PASSAGE = (
    "Een ISBN identificeert een uitgave. Meerdere fysieke exemplaren van dezelfde "
    "uitgave dragen hetzelfde ISBN."
)
BRON = {"provider": "documents", "doc_id": "reglement-1", "snippet": PASSAGE}
BRON_ID = canoniseer_bronnen([BRON])[0].source_id
INTENTIE = Intentie(toelichting="Bedoeld: het afzonderlijke fysieke exemplaar.")

GELDIG_ANTWOORD = json.dumps(
    {
        "verdict": VERDICT_FAIL,
        "applicability": "applicable",
        "unit": "het afzonderlijke fysieke exemplaar",
        "reason": "Het ISBN onderscheidt volgens de bron geen fysieke exemplaren.",
        "evidence": [
            {"location": "definition", "quote": "uitsluitend door zijn ISBN"},
            {"location": f"source:{BRON_ID}", "quote": "dragen hetzelfde ISBN"},
        ],
        "missing_information": None,
        "question": None,
        "uncertainty": None,
    },
    ensure_ascii=False,
)
AFGEKAPT_ANTWOORD = GELDIG_ANTWOORD[: len(GELDIG_ANTWOORD) // 2]


class _Provider:
    """Providerclient aan de netwerkgrens die `stop_reason` meegeeft."""

    provider_name = "fake"

    def __init__(self, antwoord: str, stop_reason: str | None):
        self.calls: list[dict[str, Any]] = []
        self.antwoord = antwoord
        self.stop_reason = stop_reason

    async def chat_completion(
        self, messages, model, temperature=0.7, max_tokens=300, timeout=None, **kw
    ):
        self.calls.append({"model": model, "kw": kw})
        if self.stop_reason is None:
            return ChatResponse(text=self.antwoord, tokens_used=5, model=model)
        return ChatResponse(
            text=self.antwoord,
            tokens_used=5,
            model=model,
            stop_reason=self.stop_reason,
        )


class FakeRouter:
    def get_model(self, task_type):
        return "fakeprovider", f"routed-{task_type}"


def _echte_ai(provider: _Provider) -> AIServiceV2:
    return AIServiceV2(
        rate_limit_config=RateLimitConfig(max_retries=3, backoff_factor=1.0),
        use_cache=True,
        ai_client=provider,
        model_router=FakeRouter(),
    )


def _dienst(provider: _Provider) -> Ess03AssessmentService:
    return Ess03AssessmentService(_echte_ai(provider), model_router=FakeRouter())


async def _assess(service: Ess03AssessmentService):
    return await service.assess(
        BEGRIP, TEKST, CONTEXT, [BRON], intentie=INTENTIE, correlation_id="c3-f1"
    )


# --- transport door de AI-laag ---------------------------------------------------


async def test_stop_reason_reist_mee_in_de_metadata_van_het_generatieresultaat():
    provider = _Provider(AFGEKAPT_ANTWOORD, "max_tokens")
    resultaat = await _echte_ai(provider).generate_definition(
        prompt="p", task_type="validation", use_cache=False
    )
    assert resultaat.text == AFGEKAPT_ANTWOORD
    assert resultaat.metadata.get("stop_reason") == "max_tokens"
    # Het transport blijft binnen de AI-laag: de provider ziet geen extra kwargs.
    assert provider.calls[0]["kw"] == {}


async def test_zonder_stop_reason_blijft_de_metadata_zoals_voorheen():
    provider = _Provider("ok", None)
    resultaat = await _echte_ai(provider).generate_definition(
        prompt="p", task_type="validation", use_cache=False
    )
    assert "stop_reason" not in resultaat.metadata


# --- ESS-03: afkapping is een eigen technische fout -----------------------------


@pytest.mark.parametrize(
    "antwoord", [AFGEKAPT_ANTWOORD, GELDIG_ANTWOORD], ids=["afgekapt", "parseerbaar"]
)
async def test_max_tokens_is_truncated_response_zonder_oordeel_en_zonder_cache(
    antwoord,
):
    provider = _Provider(antwoord, "max_tokens")
    service = _dienst(provider)
    d = (await _assess(service)).als_dict()
    assert d["status"] == "error"
    assert d["error"]["type"] == "truncated_response"
    assert d["error"]["type"] != "malformed_response"
    assert "afgekapt" in d["error"]["message"]
    assert "max_tokens" in d["error"]["message"]
    assert d["judgment"] is None
    assert d["raw_response_sha256"]  # het ruwe antwoord blijft herleidbaar
    assert service._cache == {}
    assert provider.calls[0]["kw"] == {"max_retries": 0}
    # Niet gecachet: opnieuw toetsen gaat opnieuw naar het model.
    await _assess(service)
    assert len(provider.calls) == 2


async def test_end_turn_met_geldig_antwoord_blijft_assessed():
    provider = _Provider(GELDIG_ANTWOORD, "end_turn")
    d = (await _assess(_dienst(provider))).als_dict()
    assert d["status"] == "assessed"
    assert d["error"] is None
    assert d["judgment"]["verdict"] == VERDICT_FAIL


async def test_provider_zonder_stop_reason_blijft_malformed_bij_afgekapte_json():
    """Bestaande fakes zonder het veld: afgekapte JSON blijft `malformed_response`."""
    provider = _Provider(AFGEKAPT_ANTWOORD, None)
    d = (await _assess(_dienst(provider))).als_dict()
    assert d["status"] == "error"
    assert d["error"]["type"] == "malformed_response"
