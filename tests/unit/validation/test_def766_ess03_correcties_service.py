"""DEF-766 correctieronde 1 — dienstcorrecties R2, R3, R6, R7 op de echte dienst.

Alleen de netwerkgrens is vervangen. Bewezen: een omhuld of niet-gesloten
antwoord en niet-verifieerbaar bewijs zijn technische fouten die niet worden
gecachet (R2/R3); de ruwe antwoordcache van een gedeelde `AIServiceV2` wordt
voor deze route omzeild (R3); de gehele beoordelingsoperatie valt onder één
harde deadline, ook bij blokkerende nabewerking (R6); de route krijgt
expliciet één transportpoging zonder SDK-retries en registreert werkelijk
waargenomen pogingen (R6); een te lange bronpassage is een technische
invoerbeperking zonder modelaanroep (R7); `binding()` levert de actuele
beoordelingsbinding zonder netwerk (R1).
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

import pytest

from domain.ess03.contract import (
    VERDICT_FAIL,
    VERDICT_INSUFFICIENT,
    Beoordelingsbinding,
    Intentie,
)
from domain.sources.normalisatie import canoniseer_bronnen
from services.ai.base_client import AIClientError, ChatResponse
from services.ai_service_v2 import AIServiceV2
from services.interfaces import AIGenerationResult
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


def _uitvoer(**over) -> dict:
    uitvoer = {
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
    }
    uitvoer.update(over)
    return uitvoer


class FakeAI:
    """AI-servicegrens: plant antwoorden, bewaart kwargs, kan traag of blokkerend zijn."""

    def __init__(self, *uitkomsten, blokkeer: float = 0.0, wacht: float = 0.0):
        self.uitkomsten = list(uitkomsten)
        self.calls: list[dict[str, Any]] = []
        self.blokkeer = blokkeer
        self.wacht = wacht
        self.default_model = "fake-default-model"

    async def generate_definition(self, prompt, **kwargs):
        self.calls.append({"prompt": prompt, **kwargs})
        if self.wacht:
            await asyncio.sleep(self.wacht)
        if self.blokkeer:
            time.sleep(self.blokkeer)  # blokkerende nabewerking (zoals tokenraming)
        uitkomst = self.uitkomsten.pop(0) if self.uitkomsten else _uitvoer()
        if isinstance(uitkomst, Exception):
            raise uitkomst
        tekst = (
            uitkomst
            if isinstance(uitkomst, str)
            else json.dumps(uitkomst, ensure_ascii=False)
        )
        return AIGenerationResult(
            text=tekst, model="fake-model-1", tokens_used=42, generation_time=0.01
        )


class FakeRouter:
    def get_model(self, task_type):
        return "fakeprovider", f"routed-{task_type}"


def _service(*uitkomsten, **kw):
    ai = FakeAI(*uitkomsten)
    return Ess03AssessmentService(ai, model_router=FakeRouter(), **kw), ai


async def _assess(service, *, bronnen=None, intentie=INTENTIE):
    return await service.assess(
        BEGRIP,
        TEKST,
        CONTEXT,
        [BRON] if bronnen is None else bronnen,
        intentie=intentie,
        correlation_id="def766-correctie",
    )


# --- R1: actuele binding zonder netwerk -------------------------------------------


def test_binding_komt_uit_code_regelrecord_en_router():
    service, _ = _service()
    binding = service.binding()
    assert binding == Beoordelingsbinding(
        prompt_version=Ess03AssessmentService.PROMPT_VERSION,
        norm_sha256=service.norm_sha256,
        provider="fakeprovider",
        model="routed-validation",
    )
    assert Ess03AssessmentService.PROMPT_VERSION == "ess03-assess/2"


# --- R2/R3: gesloten antwoord en bewijs → technische fout, niet gecachet -------


@pytest.mark.parametrize(
    ("antwoord", "soort", "fragment"),
    [
        (
            "Hier is mijn beoordeling:\n" + json.dumps(_uitvoer()),
            "malformed_response",
            "kaal",
        ),
        (
            json.dumps({**_uitvoer(), "confidence": 0.9}),
            "malformed_response",
            "onbekend veld",
        ),
        (
            json.dumps(
                _uitvoer(
                    verdict=VERDICT_INSUFFICIENT,
                    applicability="undetermined",
                    evidence=[],
                    question="Welke bron? Welk tijdvak?",
                )
            ),
            "malformed_response",
            "precies één",
        ),
        (
            json.dumps(
                _uitvoer(
                    evidence=[
                        {
                            "location": "definition",
                            "quote": "uitsluitend door zijn ISBN",
                        },
                        {"location": "source:missing", "quote": "hetzelfde ISBN"},
                    ]
                )
            ),
            "unverifiable_evidence",
            "onbekende vindplaats",
        ),
        (
            json.dumps(
                _uitvoer(evidence=[{"location": "definition", "quote": "verzonnen"}])
            ),
            "unverifiable_evidence",
            "citaat niet in materiaal",
        ),
    ],
)
async def test_niet_gesloten_of_onverifieerbaar_is_technische_fout_zonder_cache(
    antwoord, soort, fragment
):
    service, ai = _service(antwoord, antwoord)
    d = (await _assess(service)).als_dict()
    assert d["status"] == "error"
    assert d["error"]["type"] == soort
    assert fragment in d["error"]["message"]
    assert d["judgment"] is None
    if soort == "unverifiable_evidence":
        assert d["rejected"]
    # Niet gecachet: opnieuw toetsen gaat opnieuw naar het model.
    await _assess(service)
    assert len(ai.calls) == 2


async def test_geldig_antwoord_wordt_wel_gecachet_en_heeft_geen_rejected():
    service, ai = _service(_uitvoer(), _uitvoer())
    eerste = (await _assess(service)).als_dict()
    tweede = (await _assess(service)).als_dict()
    assert eerste["status"] == "assessed" and eerste["rejected"] == []
    assert tweede["attribution"]["cached"] is True
    assert len(ai.calls) == 1


# --- R6: deadline, één poging, waargenomen pogingen ----------------------------


async def test_route_vraagt_expliciet_geen_cache_een_poging_en_geen_sdk_retries():
    service, ai = _service(_uitvoer())
    await _assess(service)
    call = ai.calls[0]
    assert call["use_cache"] is False
    assert call["max_attempts"] == 1
    assert call["max_retries"] == 0
    assert call["token_estimate"] == "heuristic"
    assert call["timeout_seconds"] == service.timeout_seconds


async def test_vangnet_een_te_laat_teruggekeerd_antwoord_is_timeout_zonder_oordeel():
    """Vangnet (detectie achteraf), géén tijdbegrenzing: een AI-laag die de
    eventloop synchroon vasthoudt kán door asyncio niet worden onderbroken.
    Komt zo'n aanroep te laat terug, dan is dat een timeout zonder oordeel en
    zonder cache. De werkelijke begrenzing van de nabewerking staat in
    `test_vertraagde_nabewerking_op_de_echte_route_komt_binnen_de_deadline_terug`."""
    ai = FakeAI(_uitvoer(), blokkeer=0.3)
    service = Ess03AssessmentService(ai, model_router=FakeRouter(), timeout_seconds=0)
    service._timeout_seconds = 0.1  # type: ignore[assignment]
    d = (await _assess(service)).als_dict()
    assert d["status"] == "error"
    assert d["error"]["type"] == "timeout"
    assert "totale duur" in d["error"]["message"]
    assert d["judgment"] is None
    assert d["elapsed_seconds"] >= 0.3
    assert len(ai.calls) == 1
    # Niet gecachet: het (te late) antwoord telt niet als beoordeling.
    await _assess(service)
    assert len(ai.calls) == 2


async def test_vertraagde_nabewerking_op_de_echte_route_komt_binnen_de_deadline_terug(
    monkeypatch,
):
    """R6, correctieronde 2 (punt B): de deadline begrenst ook de nabewerking
    van de echte route. De provider antwoordt direct met een geldig oordeel;
    de productie-nabewerking van `AIServiceV2` (tokenraming, hier als trage
    encoder van 0,6 s) blokkeert. Met deadline 0,2 s keert de dienst binnen
    een kleine marge terug met een timeout — zonder inhoudelijk oordeel, zonder
    cache (dienst én AI-laag) — in plaats van pas ná 0,6 s te constateren dat
    het te laat was."""
    import services.ai_service_v2 as ai_mod

    def _trage_raming(self, prompt, response, model, *, heuristic=False):
        time.sleep(0.6)  # blokkerende nabewerking op het productiepad
        return 7

    monkeypatch.setattr(ai_mod.AIServiceV2, "_estimate_tokens", _trage_raming)
    provider = _Provider(faal=0, antwoord=json.dumps(_uitvoer(), ensure_ascii=False))
    ai = _echte_ai(provider)
    service = Ess03AssessmentService(ai, model_router=FakeRouter())
    service._timeout_seconds = 0.2  # type: ignore[assignment]

    start = time.perf_counter()
    d = (await _assess(service)).als_dict()
    duur = time.perf_counter() - start
    assert duur < 0.45, f"kwam pas na {duur:.3f} s terug (deadline 0,2 s)"
    assert d["status"] == "error"
    assert d["error"]["type"] == "timeout"
    assert d["judgment"] is None
    assert len(provider.calls) == 1
    assert service._cache == {}
    # Het te late antwoord landt nergens: een volgende aanroep gaat opnieuw
    # naar de provider (geen dienstcache, geen ruwe cache van de AI-laag).
    monkeypatch.setattr(ai_mod.AIServiceV2, "_estimate_tokens", lambda *a, **k: 7)
    await asyncio.sleep(0.5)  # laat de losgekoppelde nabewerking uitlopen
    d2 = (await _assess(service)).als_dict()
    assert d2["status"] == "assessed"
    assert len(provider.calls) == 2


async def test_zonder_opt_in_blijft_de_nabewerking_van_generate_definition_inline():
    """Andere appfuncties: geen opt-in → de tokenraming draait zoals voorheen
    in de eventloop-thread (geen gedragswijziging buiten de ESS-03-route)."""
    import threading

    gezien: dict[str, Any] = {}

    class _Raming(AIServiceV2):
        def _estimate_tokens(self, prompt, response, model, *, heuristic=False):
            gezien["thread"] = threading.get_ident()
            return 3

    provider = _Provider(faal=0, antwoord="ok")
    ai = _Raming(
        rate_limit_config=RateLimitConfig(max_retries=1, backoff_factor=1.0),
        use_cache=False,
        ai_client=provider,
        model_router=FakeRouter(),
    )
    await ai.generate_definition("p", task_type="validation")
    assert gezien["thread"] == threading.get_ident()
    gezien.clear()
    await ai.generate_definition(
        "p", task_type="validation", offload_postprocessing=True
    )
    assert gezien["thread"] != threading.get_ident()


async def test_trage_aanroep_wordt_door_de_deadline_afgebroken():
    ai = FakeAI(_uitvoer(), wacht=5.0)
    service = Ess03AssessmentService(ai, model_router=FakeRouter())
    service._timeout_seconds = 0.1  # type: ignore[assignment]
    start = time.perf_counter()
    d = (await _assess(service)).als_dict()
    assert time.perf_counter() - start < 1.5
    assert d["status"] == "error"
    assert d["error"]["type"] == "timeout"


class _Provider:
    """Providerclient aan de netwerkgrens die een tijdelijke fout geeft."""

    provider_name = "fake"

    def __init__(self, *, faal: int, antwoord: str):
        self.calls: list[dict[str, Any]] = []
        self.faal = faal
        self.antwoord = antwoord

    async def chat_completion(
        self, messages, model, temperature=0.7, max_tokens=300, timeout=None, **kw
    ):
        self.calls.append({"model": model, "kw": kw})
        if len(self.calls) <= self.faal:
            raise AIClientError("synthetische tijdelijke fout")
        return ChatResponse(text=self.antwoord, tokens_used=5, model=model)


def _echte_ai(provider: _Provider) -> AIServiceV2:
    return AIServiceV2(
        rate_limit_config=RateLimitConfig(max_retries=3, backoff_factor=1.0),
        use_cache=True,  # de gedeelde service cachet ruwe antwoorden …
        ai_client=provider,
        model_router=FakeRouter(),
    )


async def test_echte_ai_laag_doet_een_poging_en_registreert_die(monkeypatch):
    monkeypatch.setattr("asyncio.sleep", _geen_slaap)
    provider = _Provider(faal=5, antwoord="{}")
    service = Ess03AssessmentService(_echte_ai(provider), model_router=FakeRouter())
    d = (await _assess(service)).als_dict()
    assert d["status"] == "error"
    assert d["error"]["type"] == "connection"
    assert len(provider.calls) == 1
    assert provider.calls[0]["kw"] == {"max_retries": 0}
    assert d["attribution"]["attempts_observed"] == 1
    assert d["attribution"]["retries_observed"] == 0


async def test_waargenomen_herhalingen_worden_geteld_niet_hardgecodeerd():
    service, ai = _service(_uitvoer())

    async def _met_retrylog(prompt, **kwargs):
        logging.getLogger("anthropic._base_client").info(
            "Retrying request to /v1/messages in 0.5 seconds"
        )
        return await FakeAI.generate_definition(ai, prompt, **kwargs)

    ai.generate_definition = _met_retrylog  # type: ignore[method-assign]
    d = (await _assess(service)).als_dict()
    assert d["attribution"]["retries_observed"] == 1
    assert d["attribution"]["attempts_observed"] == 2


async def test_ruwe_cache_van_de_gedeelde_ai_laag_wordt_omzeild():
    # … maar de ESS-03-route mag daar niets uit terugkrijgen: een tweede
    # aanroep met hetzelfde (ongeldige) antwoord gaat opnieuw naar de provider.
    provider = _Provider(faal=0, antwoord="geen json")
    service = Ess03AssessmentService(_echte_ai(provider), model_router=FakeRouter())
    for _ in range(2):
        d = (await _assess(service)).als_dict()
        assert d["error"]["type"] == "malformed_response"
    assert len(provider.calls) == 2


# --- R7: te lange passage is een invoerbeperking, geen oordeel ------------------


async def test_te_lange_passage_is_technische_invoerbeperking_zonder_modelaanroep():
    lang = {**BRON, "snippet": "x" * 50 + " EINDE"}
    service, ai = _service(_uitvoer(), max_passage_chars=20)
    d = (await _assess(service, bronnen=[lang])).als_dict()
    assert ai.calls == []
    assert d["status"] == "error"
    assert d["error"]["type"] == "input_truncated"
    bron_id = canoniseer_bronnen([lang])[0].source_id
    assert bron_id in d["error"]["message"]
    assert "20" in d["error"]["message"]
    assert d["judgment"] is None


async def test_passage_binnen_de_grens_gaat_volledig_mee():
    service, ai = _service(
        _uitvoer(evidence=[{"location": "definition", "quote": "ISBN"}])
    )
    d = (await _assess(service)).als_dict()
    assert d["status"] == "assessed"
    assert PASSAGE in ai.calls[0]["prompt"]
    assert 'afgekapt="ja"' not in ai.calls[0]["prompt"]


async def _geen_slaap(*_a, **_k):
    return None
