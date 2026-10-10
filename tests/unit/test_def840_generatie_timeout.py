"""DEF-840 — generatie liep na ±120 s vast met een lege foutmelding.

* (a) Een time-out of een exception zonder tekst geeft een begrijpelijke
  Nederlandse melding; nooit meer "❌ Fout bij generatie: " zonder tekst.
  Het UI-budget komt uit één bron (``definition_generation``).
* (b) De zes voorbeeldtypen worden gelijktijdig gegenereerd: de totale duur
  is ≈ de langste aanroep in plaats van de som, het resultaat is gelijk aan
  dat van een sequentiële run, de gelijktijdigheid is begrensd en één
  mislukt type breekt de rest niet af.
* (c) ``counter_examples`` is een bekende task_type van de ModelRouter.
"""

from __future__ import annotations

import asyncio
import dataclasses
import hashlib
import logging
import time
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from config.rate_limit_config import ENDPOINT_CONFIGS, get_endpoint_timeout
from integration.definitie_checker import CheckAction
from services.ai.base_client import ChatResponse
from services.ai.model_router import ModelRouter
from services.ai_service_v2 import AIServiceV2
from ui.handlers.definition_generation_handler import (
    DefinitionGenerationHandler,
    foutmelding_generatie,
    generatie_budget_s,
)
from ui.helpers.async_bridge import run_async
from utils.async_api import RateLimitConfig
from utils.integrated_resilience import cleanup_integrated_system
from voorbeelden import unified_voorbeelden as uv
from voorbeelden.unified_voorbeelden import (
    _EXAMPLE_TYPE_TO_TASK_TYPE,
    DEFAULT_EXAMPLE_COUNTS,
    ExampleRequest,
    ExampleType,
    GenerationMode,
    UnifiedExamplesGenerator,
    genereer_alle_voorbeelden_async,
)

pytestmark = [pytest.mark.unit]


# ------------------------------------------------------------- (a) melding


def test_timeout_geeft_melding_met_budget():
    melding = foutmelding_generatie(TimeoutError(), 120.0)
    assert "langer dan 120 s" in melding
    assert "afgebroken" in melding
    assert "opnieuw" in melding


def test_echte_bridge_timeout_geeft_geen_lege_melding():
    """De exception die run_async werkelijk gooit, heeft geen tekst."""
    with pytest.raises(TimeoutError) as info:
        run_async(asyncio.sleep(5), timeout=0.01)
    assert str(info.value) == ""  # de oorzaak van de lege melding
    melding = foutmelding_generatie(info.value, 0.01)
    assert "langer dan 0.01 s" in melding


def test_interne_timeout_met_tekst_noemt_geen_budget_en_geen_tekst():
    melding = foutmelding_generatie(
        TimeoutError("Rate limit timeout for examples_generation_counter"), 120.0
    )
    assert "interne tijdslimiet" in melding
    assert "examples_generation_counter" not in melding
    assert "120" not in melding


@pytest.mark.parametrize("fout", [RuntimeError(), ValueError("   "), KeyError()])
def test_exception_zonder_tekst_noemt_het_type(fout):
    melding = foutmelding_generatie(fout, 120.0)
    assert type(fout).__name__ in melding
    assert "opnieuw" in melding


# Synthetische geheimen en interne paden: horen in de log, nooit in de UI.
_GEHEIM = "sk-ant-api03-SYNTHETISCH-GEHEIM-9Z"
_PAD = "/Users/iemand/Projecten/intern/src/services/ai/geheim_pad.py"


@pytest.mark.parametrize(
    "fout",
    [
        RuntimeError(f"401 voor sleutel {_GEHEIM} in {_PAD}"),
        ValueError(f"{_PAD}: {_GEHEIM}"),
        TimeoutError(f"provider {_GEHEIM} bij {_PAD}"),
    ],
    ids=["runtime", "value", "interne-timeout"],
)
def test_melding_bevat_nooit_de_exceptiontekst(fout):
    melding = foutmelding_generatie(fout, 120.0)
    assert _GEHEIM not in melding
    assert _PAD not in melding
    assert "geheim_pad" not in melding
    assert "opnieuw" in melding


def test_algemene_fout_noemt_alleen_type_en_advies():
    melding = foutmelding_generatie(RuntimeError(f"stuk: {_GEHEIM}"), 120.0)
    assert melding == (
        "❌ Generatie mislukt door een onverwachte fout (RuntimeError). "
        "Probeer het opnieuw."
    )


@pytest.fixture
def budget_137(monkeypatch) -> float:
    """Configuratiebudget op een waarde die nergens anders voorkomt."""
    origineel = ENDPOINT_CONFIGS["definition_generation"]
    monkeypatch.setitem(
        ENDPOINT_CONFIGS,
        "definition_generation",
        dataclasses.replace(origineel, timeout=137.0),
    )
    return 137.0


def test_budget_komt_uit_rate_limit_config(budget_137):
    assert get_endpoint_timeout("definition_generation") == budget_137
    assert generatie_budget_s() == budget_137


class _FakeSM:
    def __init__(self, **waarden: Any) -> None:
        self.data: dict[str, Any] = {"generation_options": {}, **waarden}

    def get_value(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set_value(self, key: str, value: Any) -> None:
        self.data[key] = value

    def clear_value(self, key: str) -> None:
        self.data.pop(key, None)


class _NooitAangeroepenService:
    async def generate_definition(self, *args: Any, **kwargs: Any):
        raise AssertionError("run_async is gepatcht; de service draait niet")

    def to_ui_response(self, response):
        return response


def _genereer_via_handler(fout: BaseException) -> tuple[list[float], list[str]]:
    """Handler met een run_async die ``fout`` gooit: (bridge-budgetten, meldingen)."""
    checker = MagicMock()
    checker.check_before_generation.return_value = MagicMock(action=CheckAction.PROCEED)
    handler = DefinitionGenerationHandler(
        checker, _NooitAangeroepenService(), MagicMock()
    )
    ontvangen_budget: list[float] = []

    def _faal(coro, timeout=None):
        coro.close()
        ontvangen_budget.append(timeout)
        raise fout

    st = MagicMock()
    with patch("ui.helpers.async_bridge.run_async", _faal):
        handler.handle_definition_generation(
            "verdachte",
            {
                "organisatorische_context": ["OM"],
                "juridische_context": ["Strafrecht"],
                "wettelijke_basis": [],
            },
            _st=st,
            _sm=_FakeSM(determined_category="proces"),
        )
    return ontvangen_budget, [c.args[0] for c in st.error.call_args_list]


def test_handler_toont_timeoutmelding_en_gebruikt_het_configbudget(budget_137):
    """Keten: configbudget → bridge-argument; TimeoutError → melding met dat budget."""
    ontvangen_budget, meldingen = _genereer_via_handler(TimeoutError())

    assert ontvangen_budget == [137.0]
    assert len(meldingen) == 1
    assert "langer dan 137 s" in meldingen[0]
    assert "120" not in meldingen[0]


def test_handler_lekt_geen_exceptiontekst_naar_de_ui(caplog):
    fout = RuntimeError(f"401 voor sleutel {_GEHEIM} in {_PAD}")
    with caplog.at_level(logging.ERROR):
        _, meldingen = _genereer_via_handler(fout)

    assert meldingen == [foutmelding_generatie(fout, generatie_budget_s())]
    assert _GEHEIM not in meldingen[0]
    assert _PAD not in meldingen[0]
    # De technische details gaan wél naar de log.
    assert "Global generation failed (RuntimeError)" in caplog.text


# ------------------------------------------- (b) gelijktijdige voorbeelden

_VERTRAGING_S = 0.5


class _NepProvider:
    """Nep-AIServiceV2: vaste vertraging per aanroep, telt gelijktijdigheid.

    Het antwoord bevat een kenmerk van de prompt, zodat ook twee typen met
    dezelfde task_type (voorbeeldzinnen/praktijkvoorbeelden) onderscheidbaar
    zijn bij een verwisseling.
    """

    def __init__(
        self,
        vertraging_s: float = _VERTRAGING_S,
        faal_op: str = "",
        fout: type[BaseException] = RuntimeError,
    ) -> None:
        self.vertraging_s = vertraging_s
        self.faal_op = faal_op
        self.fout = fout
        self.actief = 0
        self.max_actief = 0
        self.task_types: list[str] = []
        self.taken: list[asyncio.Task] = []

    async def generate_definition(
        self,
        *,
        prompt,
        task_type,
        temperature,
        max_tokens,
        timeout_seconds=30,
        request_timeout=None,
    ):
        self.task_types.append(task_type)
        taak = asyncio.current_task()
        assert taak is not None
        self.taken.append(taak)
        self.actief += 1
        self.max_actief = max(self.max_actief, self.actief)
        try:
            await asyncio.sleep(self.vertraging_s)
        finally:
            self.actief -= 1
        if task_type == self.faal_op:
            raise self.fout("nep-providerfout")
        kenmerk = hashlib.sha256(prompt.encode()).hexdigest()[:8]
        regels = "\n".join(f"{i}. {task_type} {kenmerk} item {i}" for i in range(1, 6))
        return SimpleNamespace(text=regels)


@pytest.fixture
def nep_generator(monkeypatch, tmp_path):
    """Generator met nep-provider; resilience-laag echt, per test een schone staat.

    De resilience-laag schrijft historie naar het relatieve pad ``cache/``;
    chdir naar tmp_path houdt de repo schoon.
    """
    monkeypatch.chdir(tmp_path)
    asyncio.run(cleanup_integrated_system())
    generator = UnifiedExamplesGenerator()
    monkeypatch.setattr(uv, "get_examples_generator", lambda: generator)
    yield generator
    asyncio.run(cleanup_integrated_system())


def _sequentiele_referentie(generator: UnifiedExamplesGenerator) -> dict[str, Any]:
    """Wat de oude sequentiële keten opleverde, voor dezelfde nep-provider."""

    async def _run() -> dict[str, Any]:
        uitkomst: dict[str, Any] = {}
        for example_type in ExampleType:
            req = ExampleRequest(
                begrip="verdachte",
                definitie="Een verdachte is …",
                context_dict={},
                example_type=example_type,
                generation_mode=GenerationMode.RESILIENT,
                max_examples=DEFAULT_EXAMPLE_COUNTS[example_type.value],
            )
            resultaat = await generator._generate_resilient(req)
            uitkomst[example_type.value] = (
                resultaat[0] if example_type == ExampleType.TOELICHTING else resultaat
            )
        await cleanup_integrated_system()
        return uitkomst

    return asyncio.run(_run())


def _gelijktijdig(generator) -> tuple[dict[str, Any], float]:
    async def _run():
        start = time.perf_counter()
        uitkomst = await genereer_alle_voorbeelden_async(
            begrip="verdachte", definitie="Een verdachte is …", context_dict={}
        )
        duur = time.perf_counter() - start
        await cleanup_integrated_system()
        return uitkomst, duur

    return asyncio.run(_run())


def test_duur_is_ongeveer_de_langste_niet_de_som(nep_generator):
    provider = _NepProvider()
    nep_generator.ai_service = provider

    uitkomst, duur = _gelijktijdig(nep_generator)

    som = _VERTRAGING_S * len(ExampleType)
    assert duur < som / 2, f"duur {duur:.2f}s ≈ som {som:.2f}s: nog sequentieel"
    assert provider.max_actief == len(ExampleType)
    assert all(uitkomst[t.value] for t in ExampleType)


def test_resultaat_en_volgorde_gelijk_aan_sequentieel(nep_generator):
    nep_generator.ai_service = _NepProvider(vertraging_s=0.01)
    referentie = _sequentiele_referentie(nep_generator)

    nep_generator.ai_service = _NepProvider(vertraging_s=0.01)
    uitkomst, _ = _gelijktijdig(nep_generator)

    assert uitkomst == referentie
    assert list(uitkomst) == [t.value for t in ExampleType]
    # Zelfde task_type, andere prompt: een verwisseling zou hier opvallen.
    assert uitkomst["voorbeeldzinnen"] != uitkomst["praktijkvoorbeelden"]


def test_gelijktijdigheid_is_begrensd(nep_generator, monkeypatch):
    monkeypatch.setattr(uv, "MAX_GELIJKTIJDIGE_VOORBEELDTYPEN", 2)
    provider = _NepProvider(vertraging_s=0.3)
    nep_generator.ai_service = provider

    _gelijktijdig(nep_generator)

    assert provider.max_actief == 2
    assert len(provider.task_types) == len(ExampleType)


@pytest.mark.parametrize("fout", [RuntimeError, asyncio.CancelledError])
def test_een_mislukt_type_breekt_de_rest_niet_af(nep_generator, caplog, fout):
    """Ook een intern geannuleerd type (CancelledError) wordt een leeg veld."""
    nep_generator.ai_service = _NepProvider(
        vertraging_s=0.01, faal_op="synonyms", fout=fout
    )

    with caplog.at_level(logging.WARNING):
        uitkomst, _ = _gelijktijdig(nep_generator)

    assert uitkomst["synoniemen"] == []
    for t in ExampleType:
        if t != ExampleType.SYNONIEMEN:
            assert uitkomst[t.value], t.value
    assert f"Failed to generate synoniemen: {fout.__name__}" in caplog.text
    samenvatting = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING and "voorbeeldtypen leeg" in r.getMessage()
    ]
    assert len(samenvatting) == 1
    assert (
        f"1 van {len(ExampleType)} voorbeeldtypen leeg door een fout voor "
        f"'verdachte': synoniemen ({fout.__name__})"
    ) in samenvatting[0].getMessage()


def test_verlopen_budget_annuleert_alle_lopende_typen(nep_generator):
    """Direct na de time-out, nog in de draaiende loop, loopt geen aanroep meer.

    De controle staat bewust vóór de cleanup en vóór het einde van
    ``asyncio.run``: dat einde annuleert achtergebleven taken zelf en zou een
    afgeschermde (``asyncio.shield``) provideraanroep anders maskeren.
    """
    provider = _NepProvider(vertraging_s=5.0)
    nep_generator.ai_service = provider

    async def _run():
        start = time.perf_counter()
        with pytest.raises(TimeoutError):
            await asyncio.wait_for(
                genereer_alle_voorbeelden_async(
                    begrip="verdachte", definitie="Een verdachte is …", context_dict={}
                ),
                timeout=0.5,
            )
        duur = time.perf_counter() - start
        nog_actief = provider.actief
        lopende_taken = [t for t in provider.taken if not t.done()]
        await cleanup_integrated_system()
        return duur, nog_actief, lopende_taken

    duur, nog_actief, lopende_taken = asyncio.run(_run())

    assert duur < 2.0
    assert provider.max_actief == len(ExampleType)
    assert len(provider.taken) == len(ExampleType)
    assert nog_actief == 0, f"{nog_actief} provideraanroepen liepen door"
    assert lopende_taken == []


class _NepClient:
    """Nep-providerclient onder de échte AIServiceV2 + AsyncRateLimiter."""

    def __init__(self) -> None:
        self.aanroepen = 0

    async def chat_completion(self, messages, model, temperature, max_tokens, **_):
        self.aanroepen += 1
        await asyncio.sleep(0.02)  # houdt de limiter vast → wachtrij
        prompt = messages[-1].content
        kenmerk = hashlib.sha256(prompt.encode()).hexdigest()[:8]
        regels = "\n".join(f"{i}. {kenmerk} item {i}" for i in range(1, 6))
        return ChatResponse(text=regels, tokens_used=0, model=model)


def test_echte_limiter_overleeft_opeenvolgende_ui_loops(nep_generator, caplog):
    """Codex-reproductie: gedeelde AIServiceV2, wachtrij in de limiter, twee loops.

    Vóór de per-loop-semaphore gaf de tweede loop "bound to a different event
    loop" per type, wat ``gather`` stil in lege voorbeeldvelden veranderde.
    """
    client = _NepClient()
    nep_generator.ai_service = AIServiceV2(
        rate_limit_config=RateLimitConfig(max_concurrent=2, max_retries=1),
        default_model="claude-nep",
        use_cache=False,
        ai_client=client,
    )

    with caplog.at_level(logging.WARNING):
        for _ in range(2):
            uitkomst, _ = _gelijktijdig(nep_generator)
            leeg = [t.value for t in ExampleType if not uitkomst[t.value]]
            assert leeg == [], f"lege voorbeeldtypen: {leeg}"

    assert client.aanroepen == 2 * len(ExampleType)
    assert "different event loop" not in caplog.text
    assert "voorbeeldtypen leeg door een fout" not in caplog.text


# ----------------------------------------------- (c) task_type-routering


@pytest.mark.parametrize("task_type", sorted(set(_EXAMPLE_TYPE_TO_TASK_TYPE.values())))
def test_elke_voorbeeld_task_type_is_bekend_bij_de_router(task_type, caplog):
    router = ModelRouter({})
    with caplog.at_level(logging.WARNING, logger="services.ai.model_router"):
        router.get_model(task_type)
    assert "Unknown task_type" not in caplog.text


def test_counter_examples_valt_in_dezelfde_tier_als_examples():
    router = ModelRouter({})
    assert router._get_tier("counter_examples") == router._get_tier("examples")
    assert router._get_tier("counter_examples") == "critical"
