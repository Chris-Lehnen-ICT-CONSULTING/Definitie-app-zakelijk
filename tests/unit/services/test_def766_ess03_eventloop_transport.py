"""DEF-766 correctieronde 2, punt C — verbindingsfout bij hergebruik van de
providerclient over opeenvolgende UI-eventloops.

Browserwaarneming (browser-verification-v2.md): call 1 HTTP 200, call 2 in
dezelfde editor 1 ms na start "Anthropic connection error" zonder
httpx-requestlog, handmatige herkansing 200. Oorzaak (bewezen met de echte
SDK/httpx-stack tegen een lokale fake server, zie
`scripts/ess03/proef_eventloop_transport.py` en `c2-c-transportproef.json`):
het httpx-verbindingspool van de gedeelde `AsyncAnthropic`-client
(containersingleton) is gebonden aan de eventloop van het vorige gebruik; de
UI draait iedere aanroep in een eigen `asyncio.run()`-loop
(`ui.helpers.async_bridge.run_async`), en een keep-alive-verbinding uit een
gesloten loop geeft `APIConnectionError` ← `RuntimeError: Event loop is closed`.

Deze pytest-tests draaien binnen de offline-testgate (geen sockets, ook geen
loopback) en toetsen de correctie op de SDK-grens: een fake SDK die — zoals
het echte pool — aan de loop van zijn eerste gebruik gebonden is, achter de
echte `AnthropicClient` → `AIServiceV2` → `Ess03AssessmentService`, met
opeenvolgende aanroepen via `run_async` (drie loops). Geen retries.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import anthropic
import httpx
import pytest

from services.ai import anthropic_client as anthropic_mod, openai_client as openai_mod
from services.ai.anthropic_client import AnthropicClient
from services.ai.base_client import AIConnectionClientError, ChatMessage, Eventloopwacht
from services.ai.openai_client import OpenAIClient
from services.ai_service_v2 import AIServiceV2
from services.validation.ess03_assessment_service import Ess03AssessmentService
from ui.helpers.async_bridge import run_async
from utils.async_api import RateLimitConfig

pytestmark = [pytest.mark.unit]

ANTWOORD = json.dumps(
    {
        "verdict": "not_applicable",
        "applicability": "not_applicable",
        "unit": None,
        "reason": "Stoflezing zonder gekozen telbare eenheid.",
        "evidence": [
            {"location": "definition", "quote": "Vloeistof bestaande uit H2O."}
        ],
        "missing_information": None,
        "question": None,
        "uncertainty": None,
    },
    ensure_ascii=False,
)


class _Blok:
    def __init__(self, text: str) -> None:
        self.text = text


class _Usage:
    input_tokens = 10
    output_tokens = 20


class _Bericht:
    def __init__(self, text: str) -> None:
        self.content = [_Blok(text)]
        self.usage = _Usage()
        self.model = "claude-fake"


class _LoopgebondenSdk:
    """Fake SDK-client die zich gedraagt als een client met verbindingspool: de
    eerste aanroep bindt hem aan de draaiende loop; een aanroep uit een andere
    loop faalt zoals httpx/httpcore dat doen (`Event loop is closed`)."""

    constructies: list[dict[str, Any]] = []

    def __init__(self, **opties: Any) -> None:
        _LoopgebondenSdk.constructies.append(opties)
        self._loop: Any = None
        self.messages = self
        self.chat = self  # OpenAI-vorm
        self.completions = self

    def with_options(self, **_: Any) -> _LoopgebondenSdk:
        return self

    async def create(self, **_: Any) -> _Bericht:
        loop = asyncio.get_running_loop()
        if self._loop is None:
            self._loop = loop
        elif self._loop is not loop:
            oorzaak = RuntimeError("Event loop is closed")
            raise anthropic.APIConnectionError(
                request=httpx.Request("POST", "http://fake/v1/messages")
            ) from oorzaak
        return _Bericht(ANTWOORD)


@pytest.fixture
def fake_sdk(monkeypatch):
    _LoopgebondenSdk.constructies = []
    monkeypatch.setattr(anthropic_mod, "AsyncAnthropic", _LoopgebondenSdk)
    return _LoopgebondenSdk


class _Router:
    def get_model(self, task_type):
        return "anthropic", "claude-fake"

    def accepts_temperature(self, model, provider=None):
        return False


def _dienst(client: AnthropicClient) -> Ess03AssessmentService:
    ai = AIServiceV2(
        rate_limit_config=RateLimitConfig(max_retries=1, backoff_factor=1.0),
        use_cache=False,
        ai_client=client,
        model_router=_Router(),
    )
    return Ess03AssessmentService(ai, model_router=_Router(), cache_size=0)


def _beoordeel(dienst: Ess03AssessmentService) -> dict[str, Any]:
    # Zoals de UI: iedere aanroep zijn eigen `asyncio.run()`-loop.
    return run_async(
        dienst.assess(
            "water",
            "Vloeistof bestaande uit H2O.",
            {"organisatorische_context": ["Synthetisch Lab"]},
            [],
            correlation_id="def766-c",
        )
    ).als_dict()


def test_zonder_correctie_faalt_de_tweede_ui_aanroep_met_verbindingsfout(fake_sdk):
    client = AnthropicClient(
        api_key="sk-ant-test", timeout=5, max_retries=0, rebind_on_new_loop=False
    )
    dienst = _dienst(client)
    assert _beoordeel(dienst)["status"] == "assessed"
    tweede = _beoordeel(dienst)
    assert tweede["status"] == "error"
    assert tweede["error"]["type"] == "connection"
    assert tweede["attribution"]["attempts_observed"] == 1
    assert len(fake_sdk.constructies) == 1


def test_met_correctie_slagen_opeenvolgende_ui_aanroepen_zonder_retries(fake_sdk):
    client = AnthropicClient(api_key="sk-ant-test", timeout=5, max_retries=0)
    dienst = _dienst(client)
    uitkomsten = [_beoordeel(dienst) for _ in range(3)]
    assert [u["status"] for u in uitkomsten] == ["assessed"] * 3
    assert [u["judgment"]["verdict"] for u in uitkomsten] == ["not_applicable"] * 3
    assert [u["attribution"]["attempts_observed"] for u in uitkomsten] == [1, 1, 1]
    assert [u["attribution"]["retries_observed"] for u in uitkomsten] == [0, 0, 0]
    # Eén constructie bij opstart + één verse client per nieuwe loop (2 en 3);
    # dezelfde opties (sleutel, timeout, retries) als de oorspronkelijke.
    assert len(fake_sdk.constructies) == 3
    assert all(o == fake_sdk.constructies[0] for o in fake_sdk.constructies)


def test_binnen_dezelfde_loop_blijft_dezelfde_sdk_client(fake_sdk):
    client = AnthropicClient(api_key="sk-ant-test", timeout=5, max_retries=0)
    bericht = [ChatMessage(role="user", content="x")]

    async def _twee_keer():
        eerste = client._sdk_voor_deze_loop()
        await client.chat_completion(bericht, model="claude-fake")
        await client.chat_completion(bericht, model="claude-fake")
        return eerste is client._sdk_voor_deze_loop()

    assert asyncio.run(_twee_keer()) is True
    assert len(fake_sdk.constructies) == 1


def test_verbindingsfout_logt_de_oorzaakketen_zonder_geheim(fake_sdk, caplog):
    client = AnthropicClient(
        api_key="sk-ant-geheimesleutel1234567890",
        timeout=5,
        max_retries=0,
        rebind_on_new_loop=False,
    )
    bericht = [ChatMessage(role="user", content="x")]
    asyncio.run(client.chat_completion(bericht, model="claude-fake"))
    with (
        caplog.at_level("ERROR", logger="services.ai.anthropic_client"),
        pytest.raises(AIConnectionClientError),
    ):
        asyncio.run(client.chat_completion(bericht, model="claude-fake"))
    tekst = "\n".join(r.getMessage() for r in caplog.records)
    assert "APIConnectionError" in tekst and "Event loop is closed" in tekst
    assert "geheimesleutel" not in tekst


def test_eventloopwacht_herkent_een_andere_loop_en_geen_loop():
    wacht = Eventloopwacht()
    assert wacht.gewisseld() is False  # geen draaiende loop: geen wissel

    async def _check():
        return wacht.gewisseld()

    assert asyncio.run(_check()) is False  # eerste registratie
    assert asyncio.run(_check()) is True  # nieuwe loop
    assert asyncio.run(_check()) is True


def test_openai_client_neemt_dezelfde_loopwacht(monkeypatch):
    _LoopgebondenSdk.constructies = []
    monkeypatch.setattr(openai_mod, "AsyncOpenAI", _LoopgebondenSdk)
    client = OpenAIClient(api_key="sk-test", timeout=5, max_retries=0)

    async def _sdk():
        return client._sdk_voor_deze_loop()

    a = asyncio.run(_sdk())
    b = asyncio.run(_sdk())
    assert a is not b and len(_LoopgebondenSdk.constructies) == 2
