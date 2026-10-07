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
import hashlib
import logging
import time
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from config.rate_limit_config import get_endpoint_timeout
from integration.definitie_checker import CheckAction
from services.ai.model_router import ModelRouter
from ui.handlers.definition_generation_handler import (
    DefinitionGenerationHandler,
    foutmelding_generatie,
    generatie_budget_s,
)
from ui.helpers.async_bridge import run_async
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


def test_interne_timeout_met_tekst_noemt_die_tekst_niet_het_budget():
    melding = foutmelding_generatie(
        TimeoutError("Rate limit timeout for examples_generation_counter"), 120.0
    )
    assert "Rate limit timeout for examples_generation_counter" in melding
    assert "120" not in melding


@pytest.mark.parametrize("fout", [RuntimeError(), ValueError("   "), KeyError()])
def test_exception_zonder_tekst_noemt_het_type(fout):
    melding = foutmelding_generatie(fout, 120.0)
    assert type(fout).__name__ in melding
    assert melding.rstrip() != "❌ Fout bij generatie:"


def test_exception_met_tekst_blijft_ongewijzigd():
    melding = foutmelding_generatie(RuntimeError("API onbereikbaar"), 120.0)
    assert melding == "❌ Fout bij generatie: API onbereikbaar"


def test_budget_komt_uit_rate_limit_config():
    assert generatie_budget_s() == get_endpoint_timeout("definition_generation")


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


def test_handler_toont_timeoutmelding_en_gebruikt_het_configbudget():
    """Keten: run_async gooit TimeoutError → st.error krijgt de nieuwe melding."""
    checker = MagicMock()
    checker.check_before_generation.return_value = MagicMock(action=CheckAction.PROCEED)
    handler = DefinitionGenerationHandler(
        checker, _NooitAangeroepenService(), MagicMock()
    )
    ontvangen_budget: list[float] = []

    def _time_out(coro, timeout=None):
        coro.close()
        ontvangen_budget.append(timeout)
        raise TimeoutError

    st = MagicMock()
    with patch("ui.helpers.async_bridge.run_async", _time_out):
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

    assert ontvangen_budget == [generatie_budget_s()]
    meldingen = [c.args[0] for c in st.error.call_args_list]
    assert meldingen == [foutmelding_generatie(TimeoutError(), generatie_budget_s())]


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

    async def generate_definition(self, *, prompt, task_type, temperature, max_tokens):
        self.task_types.append(task_type)
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

    with caplog.at_level(logging.ERROR):
        uitkomst, _ = _gelijktijdig(nep_generator)

    assert uitkomst["synoniemen"] == []
    for t in ExampleType:
        if t != ExampleType.SYNONIEMEN:
            assert uitkomst[t.value], t.value
    assert f"Failed to generate synoniemen: {fout.__name__}" in caplog.text


def test_verlopen_budget_annuleert_alle_lopende_typen(nep_generator):
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
        await cleanup_integrated_system()
        return duur

    duur = asyncio.run(_run())

    assert duur < 2.0
    assert provider.max_actief == len(ExampleType)
    assert provider.actief == 0  # geen aanroep loopt na de annulering door


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
