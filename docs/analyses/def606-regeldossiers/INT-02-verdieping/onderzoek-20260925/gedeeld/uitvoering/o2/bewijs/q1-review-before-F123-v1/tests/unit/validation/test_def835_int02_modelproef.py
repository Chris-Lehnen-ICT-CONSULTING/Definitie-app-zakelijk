"""DEF-835 — technische proefrunner voor INT-02, volledig offline getoetst.

De runner (`scripts/analysis/def835_int02_modelproef.py`) gebruikt de echte
keten Int02AssessmentService → AIServiceV2 → AsyncGPTClient → AnthropicClient
→ Anthropic-SDK → httpx. Alleen de netwerkgrens is hier een
`httpx.MockTransport` (nep-provider); sockets zijn in elke test geblokkeerd.
Bewezen: voorbereiding zonder netwerk of sleutel, manifest- en akkoordbinding,
harde maxima (ook bij foutcalls), geen retry/cache/fallback, stop bij
afwijkende usage, kostenvariant, afkapping, ongeldig citaat of fout, geen
fixturelabels in verzoeken, geen overschrijven en geen ruwe providertekst.
Niet bewezen: gedrag van de echte provider of kwaliteit van het model.
"""

from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import json
import logging
import os
import socket
import sys
import time
from pathlib import Path

import httpx
import pytest

from services.validation.int02_assessment_service import (
    bouw_int02_prompt,
    laad_int02_norm,
)

pytestmark = [pytest.mark.unit]

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "analysis" / "def835_int02_modelproef.py"
FIXTURE = json.loads(
    (ROOT / "tests/fixtures/def835_int02_ontwerpgevallen.json").read_text("utf-8")
)
GEVALLEN = {g["id"]: g for g in FIXTURE["gevallen"]}
IDS = ("C105", "C107", "C112")
SLEUTEL = "sk-ant-offline-GEHEIM-SLEUTEL-0123456789"
GEHEIM = "GEHEIM-PROVIDERTEKST-9Z"
VERWACHT = {"C105": "fail", "C107": "review_required", "C112": "pass"}


def _laad_runner():
    spec = importlib.util.spec_from_file_location("def835_int02_modelproef", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


m = _laad_runner()


@pytest.fixture(autouse=True)
def geen_netwerk(monkeypatch):
    """Elke socketverbinding faalt: de tests bewijzen nul netwerk."""

    def weiger(*args, **kwargs):
        msg = "netwerk is in deze test verboden"
        raise AssertionError(msg)

    monkeypatch.setattr(socket.socket, "connect", weiger)
    monkeypatch.setattr(socket, "create_connection", weiger)
    monkeypatch.setattr(socket, "getaddrinfo", weiger)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _usage(**over):
    """Usage in de vorm van de geïnstalleerde SDK (`anthropic.types.Usage`)."""
    usage = {
        "input_tokens": 1500,
        "output_tokens": 400,
        "cache_creation": {
            "ephemeral_1h_input_tokens": 0,
            "ephemeral_5m_input_tokens": 0,
        },
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
        "inference_geo": "global",
        "output_tokens_details": {"thinking_tokens": 0},
        "server_tool_use": None,
        "service_tier": "standard",
    }
    usage.update(over)
    return usage


def _bericht(tekst, *, stop="end_turn", usage=None, zonder_usage=False):
    bericht = {
        "id": "msg_offline",
        "type": "message",
        "role": "assistant",
        "model": m.MODEL,
        "content": [{"type": "text", "text": tekst}],
        "stop_reason": stop,
        "stop_sequence": None,
        "usage": usage if usage is not None else _usage(),
    }
    if zonder_usage:
        del bericht["usage"]
    return bericht


def _fixtureantwoord(geval_id):
    """Nep-modeltekst: alleen de nep-provider kent dit, nooit het verzoek."""
    return json.dumps(GEVALLEN[geval_id]["modelrespons"], ensure_ascii=False)


class NepProvider:
    """Nep-Anthropic-API achter httpx.MockTransport; registreert elk verzoek."""

    def __init__(self, antwoorden=None, telling=1200):
        self.verzoeken: list[dict] = []
        self.telling = telling
        self._antwoorden = list(
            antwoorden
            if antwoorden is not None
            else [_bericht(_fixtureantwoord(i)) for i in IDS]
        )

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.verzoeken.append(
            {
                "pad": request.url.path,
                "body": json.loads(request.content),
                "ruw": request.content,
                "headers": dict(request.headers),
                "cwd": os.getcwd(),
            }
        )
        if request.url.path.endswith("/count_tokens"):
            return httpx.Response(200, json={"input_tokens": self.telling})
        antwoord = self._antwoorden.pop(0)
        if callable(antwoord):
            return antwoord(request)
        return httpx.Response(200, json=antwoord)

    def paden(self):
        return [v["pad"] for v in self.verzoeken]

    def inferenties(self):
        return [v for v in self.verzoeken if v["pad"] == "/v1/messages"]


def _akkoord(pad: Path, manifest: Path, **over) -> Path:
    data = {
        "soort": m.AKKOORD_SOORT,
        "manifest_sha256": _sha(manifest.read_bytes()),
        "profiel_id": m.PROFIEL_ID,
        "experimenteel": True,
        "geen_def815_kwalificatie": True,
        "live_verzending_toegestaan": True,
        "akkoord_door": "offline testbeoordelaar",
        "akkoord_op": "2026-09-28",
        "akkoord_bron": "offline unittest; geen echte toestemming",
    }
    data.update(over)
    data = {k: v for k, v in data.items() if v is not ...}
    pad.write_text(json.dumps(data), "utf-8")
    return pad


@pytest.fixture
async def manifest(tmp_path) -> Path:
    pad = tmp_path / "manifest.json"
    await m.voorbereid(pad, payloads_pad=tmp_path / "payloads.json")
    return pad


async def _live(tmp_path, manifest, provider, *, sleutel=lambda: SLEUTEL, **kw):
    akkoord = kw.pop("akkoord", None) or _akkoord(tmp_path / "akkoord.json", manifest)
    resultaat = tmp_path / "resultaat.json"
    data = await m.voer_live_uit(
        manifest,
        akkoord,
        resultaat,
        sleutel=sleutel,
        binnen=httpx.MockTransport(provider),
        **kw,
    )
    return data, resultaat


# --- voorbereiding --------------------------------------------------------------


async def test_voorbereiding_maakt_pending_manifest_zonder_netwerk(tmp_path):
    pad = tmp_path / "manifest.json"
    data = await m.voorbereid(pad)
    assert json.loads(pad.read_text("utf-8")) == data
    assert data["toestemming"] == "pending"
    identiteit = data["identiteit"]
    assert identiteit["profiel"]["profiel_id"] == "def835-technische-proef-opus5-v1"
    assert identiteit["profiel"]["experimenteel"] is True
    assert identiteit["profiel"]["def815_kwalificatie"] is False
    assert identiteit["limieten"] == {
        "max_inferentie": 3,
        "max_telverzoeken": 3,
        "max_uitvoertokens": 6000,
        "max_geschatte_invoertokens": 16000,
        "deadline_seconden": 120.0,
        "totale_looptijd_seconden": 600.0,
        "budget_usd": 1.0,
    }
    assert identiteit["prijzen_per_token"]["input"] == pytest.approx(0.000005)
    assert identiteit["prijzen_per_token"]["output"] == pytest.approx(0.000025)
    assert [g["id"] for g in identiteit["gevallen"]] == list(IDS)
    assert identiteit["normhash"] == laad_int02_norm().normhash
    # R2: de effectieve SDK-transportconfiguratie hoort bij de identiteit.
    assert identiteit["transport"] == {
        "basis_url": "https://api.anthropic.com",
        "anthropic_version": "2023-06-01",
        "authenticatie": "x-api-key",
        "headernamen": STANDAARDHEADERNAMEN,
    }
    assert data["identiteit_sha256"] == m.hash_json(identiteit)
    # Zonder expliciet payloaddoel wordt niets anders geschreven.
    assert sorted(p.name for p in tmp_path.iterdir()) == ["manifest.json"]


async def test_payload_bevat_alleen_invoer_en_geen_cache_tools_of_labels(
    tmp_path, manifest
):
    payloads = json.loads((tmp_path / "payloads.json").read_text("utf-8"))
    identiteit = json.loads(manifest.read_text("utf-8"))["identiteit"]
    norm = laad_int02_norm()
    for geval, vast in zip(identiteit["gevallen"], payloads["gevallen"], strict=True):
        ruw = vast["payload"].encode("utf-8")
        assert _sha(ruw) == geval["payload_sha256"]
        body = json.loads(ruw)
        assert set(body) <= {
            "model",
            "max_tokens",
            "messages",
            "system",
            "thinking",
            "temperature",  # alleen volgens het bestaande routerbeleid
        }
        assert body["model"] == "claude-opus-5"
        assert body["max_tokens"] == 6000
        assert body.get("thinking", {"type": "disabled"}) == {"type": "disabled"}
        assert "cache_control" not in vast["payload"]
        [bericht] = body["messages"]
        invoer = GEVALLEN[geval["id"]]["invoer"]
        assert json.loads(bericht["content"]) == {"invoer": invoer}
        assert body["system"] == bouw_int02_prompt(m.lees_invoer(invoer), norm)[0]
        respons = GEVALLEN[geval["id"]]["modelrespons"]
        assert respons["reason"] not in vast["payload"]
        assert "verwacht" not in vast["payload"]


async def test_bestaand_manifest_wordt_niet_overschreven(tmp_path):
    pad = tmp_path / "manifest.json"
    pad.write_text("bestaand", "utf-8")
    with pytest.raises(FileExistsError):
        await m.voorbereid(pad)
    assert pad.read_text("utf-8") == "bestaand"


async def test_voorbereiding_is_deterministisch_en_leest_geen_sleutel(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("ANTHROPIC_API_KEY", SLEUTEL)
    een = await m.voorbereid(tmp_path / "a.json")
    twee = await m.voorbereid(tmp_path / "b.json")
    assert een["identiteit"] == twee["identiteit"]
    assert SLEUTEL not in (tmp_path / "a.json").read_text("utf-8")


# --- akkoord en identiteit --------------------------------------------------------


@pytest.mark.parametrize(
    "over",
    [
        {"manifest_sha256": "0" * 64},
        {"experimenteel": False},
        {"geen_def815_kwalificatie": ...},
        {"live_verzending_toegestaan": "ja"},
        {"profiel_id": "ander-profiel"},
        {"akkoord_door": " "},
        {"extra": "veld"},
        {"soort": "iets-anders"},
    ],
    ids=lambda o: next(iter(o)),
)
async def test_live_weigert_ongeldig_akkoord_zonder_verzoek_of_sleutel(
    tmp_path, manifest, over
):
    provider = NepProvider()
    gelezen = []
    akkoord = _akkoord(tmp_path / "akkoord.json", manifest, **over)
    with pytest.raises(m.ProefGeweigerdError) as fout:
        await _live(
            tmp_path,
            manifest,
            provider,
            akkoord=akkoord,
            sleutel=lambda: gelezen.append(1) or SLEUTEL,
        )
    assert fout.value.reden == "akkoord_ongeldig"
    assert provider.verzoeken == []
    assert gelezen == []
    assert not (tmp_path / "resultaat.json").exists()


async def test_live_weigert_bij_gewijzigde_identiteit(tmp_path, manifest):
    data = json.loads(manifest.read_text("utf-8"))
    data["identiteit"]["gevallen"][0]["payload_sha256"] = "f" * 64
    data["identiteit_sha256"] = m.hash_json(data["identiteit"])
    gewijzigd = tmp_path / "gewijzigd.json"
    gewijzigd.write_text(json.dumps(data), "utf-8")
    provider = NepProvider()
    with pytest.raises(m.ProefGeweigerdError) as fout:
        await _live(
            tmp_path,
            gewijzigd,
            provider,
            akkoord=_akkoord(tmp_path / "akkoord.json", gewijzigd),
        )
    assert fout.value.reden == "identiteit_gewijzigd"
    assert provider.verzoeken == []


async def test_live_weigert_zonder_sleutel(tmp_path, manifest):
    provider = NepProvider()
    with pytest.raises(m.ProefGeweigerdError) as fout:
        await _live(tmp_path, manifest, provider, sleutel=lambda: None)
    assert fout.value.reden == "sleutel_ontbreekt"
    assert provider.verzoeken == []


# --- de echte keten met nep-provider ------------------------------------------------


async def test_live_keten_drie_tellingen_drie_inferenties_en_exacte_usage(
    tmp_path, manifest, caplog
):
    caplog.set_level(logging.DEBUG)
    provider = NepProvider()
    data, resultaat = await _live(tmp_path, manifest, provider)
    assert provider.paden() == ["/v1/messages/count_tokens", "/v1/messages"] * 3
    identiteit = json.loads(manifest.read_text("utf-8"))["identiteit"]
    for verzoek, geval in zip(
        provider.inferenties(), identiteit["gevallen"], strict=True
    ):
        assert _sha(verzoek["ruw"]) == geval["payload_sha256"]
        assert verzoek["headers"]["x-stainless-retry-count"] == "0"
        assert "anthropic-beta" not in verzoek["headers"]
        assert verzoek["headers"]["x-api-key"] == SLEUTEL
        assert Path(verzoek["cwd"]) != ROOT
    for telling, inferentie in zip(
        provider.verzoeken[::2], provider.inferenties(), strict=True
    ):
        # Zelfde inhoud (zonder max_tokens/temperature) en zelfde authenticatie.
        velden = ("model", "system", "messages", "thinking")
        body = inferentie["body"]
        assert telling["body"] == {k: body[k] for k in velden if k in body}
        for header in ("x-api-key", "anthropic-version"):
            assert telling["headers"][header] == inferentie["headers"][header]
        # R2: telling en inference delen exact de authenticatiecontext.
        assert "authorization" not in telling["headers"]
        assert "authorization" not in inferentie["headers"]
        assert sorted(inferentie["headers"]) == STANDAARDHEADERNAMEN
        assert set(telling["headers"]) <= set(STANDAARDHEADERNAMEN)
    assert Path.cwd() == ROOT
    assert data["stopreden"] is None
    assert data["tellingen"] == {"inferenties": 3, "telverzoeken": 3}
    per_geval = {g["id"]: g for g in data["gevallen"]}
    for geval_id, status in VERWACHT.items():
        geval = per_geval[geval_id]
        assert geval["status"] == status
        assert geval["document"]["status"] == status
        assert geval["meting"]["usage"] == {"input_tokens": 1500, "output_tokens": 400}
        assert geval["meting"]["geschatte_invoertokens"] == 1200
        assert geval["meting"]["gerapporteerd_model"] == "claude-opus-5"
        assert geval["meting"]["inference_geo"] == "global"
        assert geval["meting"]["service_tier"] == "standard"
    kosten = 3 * (1500 * 0.000005 + 400 * 0.000025)
    assert data["kosten_usd_berekend"] == pytest.approx(kosten)
    assert data["kosten_onzeker"] == []
    tekst = resultaat.read_text("utf-8")
    assert json.loads(tekst) == data
    assert SLEUTEL not in tekst
    assert SLEUTEL not in caplog.text


def _ander_oordeel(geval_id):
    """Geldig volgens WP1, maar een ander verdict dan de referentie."""
    kern = GEVALLEN[geval_id]["invoer"]["kern"]
    verdict, functie = (
        ("fail", "actor_prescription") if geval_id == "C112" else ("pass", "criterion")
    )
    grond = {"field": "kern", "ref": None, "quote": None, "start": None, "end": None}
    passage = {
        "quote": kern,
        "start": 0,
        "end": len(kern),
        "function": functie,
        "ground": grond,
    }
    return json.dumps(
        {
            "verdict": verdict,
            "passages": [passage],
            "reason": "Offline nep-oordeel.",
            "question": None,
            "uncertainty": "none",
            "scope_reason": None,
            "coverage": "complete",
        }
    )


async def test_semantisch_ander_oordeel_is_bevinding_zonder_herhaling(
    tmp_path, manifest
):
    provider = NepProvider([_bericht(_ander_oordeel(i)) for i in IDS])
    data, _ = await _live(tmp_path, manifest, provider)
    assert len(provider.inferenties()) == 3
    assert data["stopreden"] is None
    statussen = [g["status"] for g in data["gevallen"]]
    assert statussen == ["pass", "pass", "fail"]
    assert statussen != [VERWACHT[i] for i in IDS]


def _met_foute_positie():
    respons = dict(GEVALLEN["C105"]["modelrespons"])
    respons["passages"] = [dict(respons["passages"][0], start=1)]
    return json.dumps(respons)


@pytest.mark.parametrize(
    ("eerste", "reden"),
    [
        (_bericht("{}", zonder_usage=True), "usage_ontbreekt"),
        (_bericht("{}", usage={"input_tokens": 10}), "usage_ontbreekt"),
        (_bericht("{}", usage=_usage(cache_read_input_tokens=5)), "kostenvariant"),
        (_bericht("{}", usage=_usage(service_tier="priority")), "kostenvariant"),
        (_bericht("{}", usage=_usage(service_tier=...)), "kostenvariant"),
        (_bericht("{}", usage=_usage(onbekend_veld=1)), "kostenvariant"),
        (_bericht("{}", usage=_usage(inference_geo="us")), "kostenvariant"),
        (_bericht("{}", usage=_usage(inference_geo="onbekend")), "kostenvariant"),
        (_bericht("{}", usage=_usage(inference_geo=...)), "kostenvariant"),
        (_bericht("{}", usage=_usage(inference_geo=None)), "kostenvariant"),
        (
            _bericht(
                "{}",
                usage=_usage(output_tokens_details={"thinking_tokens": 0, "x": 1}),
            ),
            "kostenvariant",
        ),
        (
            _bericht(
                "{}", usage=_usage(output_tokens_details={"thinking_tokens": 401})
            ),
            "kostenvariant",
        ),
        (
            _bericht("{}", usage=_usage(output_tokens_details="veel")),
            "kostenvariant",
        ),
        (
            _bericht(
                "{}",
                usage=_usage(
                    server_tool_use={"web_search_requests": 1, "web_fetch_requests": 0}
                ),
            ),
            "kostenvariant",
        ),
        (
            _bericht(
                "{}",
                usage=_usage(
                    cache_creation={"ephemeral_5m_input_tokens": 0, "iets": 0}
                ),
            ),
            "kostenvariant",
        ),
        (_bericht("{}", usage=_usage(output_tokens=6001)), "usage_boven_limiet"),
        (_bericht(_fixtureantwoord("C105"), stop="max_tokens"), "truncated_response"),
        (_bericht(_met_foute_positie()), "invalid_citation"),
    ],
    ids=[
        "geen-usage",
        "onvolledige-usage",
        "cache",
        "priority",
        "geen-tier",
        "onbekend-veld",
        "geo-us",
        "geo-onbekend",
        "geo-ontbreekt",
        "geo-null",
        "details-extra-veld",
        "details-boven-totaal",
        "details-geen-object",
        "servertool-gebruikt",
        "cache-creation-onbekend-veld",
        "boven-limiet",
        "afgekapt",
        "ongeldig-citaat",
    ],
)
async def test_afwijking_stopt_verdere_calls(tmp_path, manifest, eerste, reden):
    if isinstance(eerste.get("usage"), dict):
        eerste["usage"] = {k: v for k, v in eerste["usage"].items() if v is not ...}
    provider = NepProvider([eerste, _bericht("{}"), _bericht("{}")])
    data, _ = await _live(tmp_path, manifest, provider)
    assert len(provider.inferenties()) == 1
    assert data["stopreden"] == reden
    assert data["tellingen"]["inferenties"] == 1
    assert [g["id"] for g in data["gevallen"]] == ["C105"]


def _providerfout(request):
    fout = {"type": "overloaded_error", "message": GEHEIM}
    return httpx.Response(529, json={"type": "error", "error": fout})


def _transportfout(request):
    raise httpx.ConnectError(GEHEIM, request=request)


@pytest.mark.parametrize(
    ("antwoord", "fouttype"),
    [(_providerfout, "overloaded_error"), (_transportfout, "ConnectError")],
)
async def test_fout_telt_mee_zonder_retry_en_zonder_ruwe_tekst(
    tmp_path, manifest, caplog, antwoord, fouttype
):
    caplog.set_level(logging.DEBUG)
    provider = NepProvider([antwoord, _bericht("{}"), _bericht("{}")])
    data, resultaat = await _live(tmp_path, manifest, provider)
    assert len(provider.inferenties()) == 1  # geen SDK- of appretry
    assert data["tellingen"]["inferenties"] == 1
    assert data["stopreden"] in {"providerfout", "transportfout"}
    assert data["gevallen"][0]["meting"]["fouttype"] == fouttype
    assert data["gevallen"][0]["status"] == "error"
    assert GEHEIM not in resultaat.read_text("utf-8")
    assert GEHEIM not in caplog.text
    assert logging.getLogger("services.ai.anthropic_client").disabled is False


async def test_te_hoge_invoerschatting_stopt_voor_inferentie(tmp_path, manifest):
    provider = NepProvider(telling=16001)
    data, _ = await _live(tmp_path, manifest, provider)
    assert provider.paden() == ["/v1/messages/count_tokens"]
    assert data["stopreden"] == "invoerschatting_te_hoog"
    assert data["tellingen"] == {"inferenties": 0, "telverzoeken": 1}


# --- de waarnemer aan de httpx-grens ------------------------------------------------


STANDAARD_URL = "https://api.anthropic.com/v1/messages"
#: Headernamen die de geïnstalleerde SDK (0.107.1) zonder envopties verstuurt.
STANDAARDHEADERNAMEN = [
    "accept",
    "accept-encoding",
    "anthropic-version",
    "connection",
    "content-length",
    "content-type",
    "host",
    "user-agent",
    "x-api-key",
    "x-stainless-arch",
    "x-stainless-async",
    "x-stainless-lang",
    "x-stainless-os",
    "x-stainless-package-version",
    "x-stainless-read-timeout",
    "x-stainless-retry-count",
    "x-stainless-runtime",
    "x-stainless-runtime-version",
    "x-stainless-timeout",
]


def _verzoek(body: dict, url: str = STANDAARD_URL, **headers) -> httpx.Request:
    standaard = {
        "x-api-key": SLEUTEL,
        "anthropic-version": "2023-06-01",
        "accept": "application/json",
        "content-type": "application/json",
        "user-agent": "AsyncAnthropic/Python 0.107.1",
        "x-stainless-retry-count": "0",
    }
    return httpx.Request(
        "POST",
        url,
        headers={**standaard, **headers},
        content=json.dumps(body).encode(),
    )


BODY = {
    "model": "claude-opus-5",
    "max_tokens": 6000,
    "system": "s",
    "messages": [{"role": "user", "content": "{}"}],
    "thinking": {"type": "disabled"},
}


def _waarnemer(provider, **over):
    verwacht = {"C105": _sha(json.dumps(BODY).encode())}
    limieten = m.Limieten(**{**m.LIMIETEN.__dict__, **over})
    return m.Waarnemer(
        modus="live",
        binnen=httpx.MockTransport(provider),
        verwacht=verwacht,
        prijzen={"input": 0.000005, "output": 0.000025},
        limieten=limieten,
    )


PAYLOAD = "payload_niet_toegestaan"
TRANSPORT = "transport_niet_toegestaan"
BESTEMMING = "onverwachte_bestemming"


@pytest.mark.parametrize(
    ("body", "url", "headers", "reden"),
    [
        ({**BODY, "tools": []}, STANDAARD_URL, {}, PAYLOAD),
        ({**BODY, "stream": True}, STANDAARD_URL, {}, PAYLOAD),
        ({**BODY, "max_tokens": 6001}, STANDAARD_URL, {}, PAYLOAD),
        ({**BODY, "model": "claude-fable-5"}, STANDAARD_URL, {}, PAYLOAD),
        (
            {**BODY, "thinking": {"type": "enabled", "budget_tokens": 10}},
            STANDAARD_URL,
            {},
            PAYLOAD,
        ),
        (
            {**BODY, "system": [{"type": "text", "text": "s", "cache_control": {}}]},
            STANDAARD_URL,
            {},
            PAYLOAD,
        ),
        (
            {
                **BODY,
                "messages": [
                    {
                        "role": "user",
                        "content": "{}",
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
            },
            STANDAARD_URL,
            {},
            PAYLOAD,
        ),
        (BODY, STANDAARD_URL, {"anthropic-beta": "iets"}, TRANSPORT),
        (BODY, STANDAARD_URL, {"x-stainless-retry-count": "1"}, TRANSPORT),
        # R2: poort, gebruikerinfo en headerdrift aan de verzendgrens.
        (BODY, "https://api.anthropic.com:8443/v1/messages", {}, BESTEMMING),
        (
            BODY,
            "https://gebruiker:geheim@api.anthropic.com/v1/messages",
            {},
            BESTEMMING,
        ),
        (BODY, STANDAARD_URL, {"authorization": "Bearer SYNTHETISCH"}, TRANSPORT),
        (BODY, STANDAARD_URL, {"anthropic-version": "2099-01-01"}, TRANSPORT),
        (BODY, STANDAARD_URL, {"x-extra": "1"}, TRANSPORT),
        (BODY, STANDAARD_URL, {"host": "proxy.example"}, TRANSPORT),
    ],
    ids=[
        "tools",
        "stream",
        "max-tokens",
        "model",
        "thinking",
        "cache-systeem",
        "cache-bericht",
        "beta",
        "retry",
        "poort-8443",
        "gebruikerinfo",
        "authorization",
        "api-versie",
        "extra-header",
        "host-header",
    ],
)
async def test_waarnemer_weigert_niet_toegestaan_verzoek(body, url, headers, reden):
    provider = NepProvider()
    waarnemer = _waarnemer(provider)
    waarnemer.huidig = "C105"
    with pytest.raises(m.ProefStopError):
        await waarnemer.handle_async_request(_verzoek(body, url, **headers))
    assert provider.verzoeken == []
    assert waarnemer.stopreden == reden


async def test_waarnemer_weigert_hashmismatch_en_budget_voor_verzending():
    provider = NepProvider()
    waarnemer = _waarnemer(provider)
    waarnemer.huidig = "C105"
    with pytest.raises(m.ProefStopError):
        await waarnemer.handle_async_request(_verzoek({**BODY, "system": "t"}))
    assert waarnemer.stopreden == "payload_hash_mismatch"
    krap = _waarnemer(provider, budget_usd=0.2)
    krap.huidig = "C105"
    with pytest.raises(m.ProefStopError):
        await krap.handle_async_request(_verzoek(BODY))
    assert krap.stopreden == "budget_ontoereikend"
    assert provider.paden() == ["/v1/messages/count_tokens"]


async def test_harde_limiet_telt_ook_mislukte_verzoeken():
    provider = NepProvider([_transportfout, _bericht("{}")])
    waarnemer = _waarnemer(provider)
    waarnemer.huidig = "C105"
    with pytest.raises(httpx.ConnectError):
        await waarnemer.handle_async_request(_verzoek(BODY))
    assert waarnemer.inferenties == 1
    waarnemer.stopreden = None  # alleen om de teller los te toetsen
    beperkt = _waarnemer(provider, max_inferentie=1)
    beperkt.huidig = "C105"
    beperkt.inferenties = waarnemer.inferenties
    with pytest.raises(m.ProefStopError):
        await beperkt.handle_async_request(_verzoek(BODY))
    assert beperkt.stopreden == "inferentielimiet"
    assert len(provider.inferenties()) == 1


async def test_tellimiet_stopt_voor_telverzoek():
    provider = NepProvider()
    waarnemer = _waarnemer(provider, max_telverzoeken=1)
    waarnemer.huidig = "C105"
    waarnemer.telverzoeken = 1  # eerder telverzoek, ook als dat mislukte
    with pytest.raises(m.ProefStopError):
        await waarnemer.handle_async_request(_verzoek(BODY))
    assert waarnemer.stopreden == "tellimiet"
    assert provider.verzoeken == []


# --- correcties na review: R1 model, R2 transport, provider-usage, deadline ------------


@pytest.mark.parametrize(
    "model",
    ["ander-model", "claude-opus-5-20260101", "claude-opus-5-latest", "", 123, ...],
    ids=["ander", "revisie", "alias", "leeg", "geen-tekst", "ontbreekt"],
)
async def test_r1_afwijkend_responsemodel_stopt_zonder_oordeel_of_opus_kosten(
    tmp_path, manifest, model
):
    # Minimale usage (optionele SDK-velden weggelaten): de modelbinding staat
    # hier los van de usagecontrole, zoals in de reviewreproductie.
    kaal = {"input_tokens": 1500, "output_tokens": 400, "service_tier": "standard"}
    antwoorden = [_bericht(_fixtureantwoord(i), usage=dict(kaal)) for i in IDS]
    for antwoord in antwoorden:
        antwoord["model"] = model
        if model is ...:
            del antwoord["model"]
    provider = NepProvider(antwoorden)
    data, _ = await _live(tmp_path, manifest, provider)
    assert len(provider.inferenties()) == 1
    assert data["tellingen"] == {"inferenties": 1, "telverzoeken": 1}
    assert data["stopreden"] == "model_afwijkend"
    [geval] = data["gevallen"]
    assert geval["status"] == "error"
    assert geval["document"]["oordeel"] is None
    gemeld = model if isinstance(model, str) else None
    assert geval["meting"]["gerapporteerd_model"] == gemeld
    assert geval["meting"]["usage"] == {"input_tokens": 1500, "output_tokens": 400}
    assert geval["meting"]["kosten_usd"] is None
    assert data["kosten_usd_berekend"] is None
    assert data["kosten_onzeker"] == ["C105"]


_REVIEWDRIFT = {
    "ANTHROPIC_BASE_URL": "https://api.anthropic.com:8443",
    "ANTHROPIC_CUSTOM_HEADERS": (
        "anthropic-version: 2099-01-01\nAuthorization: Bearer SYNTHETIC-REVIEW"
    ),
}


@pytest.mark.parametrize(
    "omgeving",
    [
        _REVIEWDRIFT,
        {"ANTHROPIC_BASE_URL": "https://api.anthropic.com:8443"},
        {"ANTHROPIC_BASE_URL": "https://gebruiker:geheim@api.anthropic.com"},
        {"ANTHROPIC_BASE_URL": "http://api.anthropic.com"},
        {"ANTHROPIC_BASE_URL": "https://api.anthropic.com/proxy"},
        {"ANTHROPIC_BASE_URL": "https://proxy.example"},
        {"ANTHROPIC_CUSTOM_HEADERS": "anthropic-version: 2099-01-01"},
        {"ANTHROPIC_CUSTOM_HEADERS": "Authorization: Bearer SYNTHETIC"},
        {"ANTHROPIC_CUSTOM_HEADERS": "X-Extra: 1"},
    ],
    ids=[
        "review-8443-auth",
        "poort",
        "gebruikerinfo",
        "http",
        "pad",
        "andere-host",
        "versieheader",
        "authheader",
        "extra-header",
    ],
)
async def test_r2_sdk_transportdrift_weigert_voor_sleutel_en_verzending(
    tmp_path, manifest, monkeypatch, caplog, omgeving
):
    caplog.set_level(logging.DEBUG)
    for naam, waarde in omgeving.items():
        monkeypatch.setenv(naam, waarde)
    provider = NepProvider()
    gelezen = []
    with pytest.raises(m.ProefGeweigerdError) as fout:
        await _live(
            tmp_path,
            manifest,
            provider,
            sleutel=lambda: gelezen.append(1) or SLEUTEL,
        )
    assert fout.value.reden == "transportconfig_niet_toegestaan"
    assert provider.verzoeken == []
    assert gelezen == []
    assert not (tmp_path / "resultaat.json").exists()
    assert "SYNTHETIC" not in caplog.text
    assert "geheim" not in caplog.text


async def test_r2_voorbereiding_weigert_transportdrift(tmp_path, monkeypatch):
    for naam, waarde in _REVIEWDRIFT.items():
        monkeypatch.setenv(naam, waarde)
    with pytest.raises(m.ProefGeweigerdError) as fout:
        await m.voorbereid(tmp_path / "manifest.json")
    assert fout.value.reden == "transportconfig_niet_toegestaan"
    assert not (tmp_path / "manifest.json").exists()


@pytest.mark.parametrize(
    "omgeving",
    [
        {"ANTHROPIC_BASE_URL": "https://api.anthropic.com"},
        {"ANTHROPIC_AUTH_TOKEN": "SYNTHETISCH-TOKEN"},
    ],
    ids=["standaard-basis-expliciet", "authtoken-genegeerd-bij-api-key"],
)
async def test_r2_equivalente_standaardconfiguratie_blijft_toegestaan(
    tmp_path, manifest, monkeypatch, omgeving
):
    for naam, waarde in omgeving.items():
        monkeypatch.setenv(naam, waarde)
    provider = NepProvider()
    data, _ = await _live(tmp_path, manifest, provider)
    assert data["stopreden"] is None
    assert all("authorization" not in v["headers"] for v in provider.verzoeken)


async def test_actuele_sdk_usage_details_worden_niet_opgeteld(tmp_path, manifest):
    usage = _usage(output_tokens_details={"thinking_tokens": 37})
    provider = NepProvider([_bericht(_fixtureantwoord(i), usage=usage) for i in IDS])
    data, _ = await _live(tmp_path, manifest, provider)
    assert data["stopreden"] is None
    assert len(provider.inferenties()) == 3
    # output_tokens is het inclusieve facturatietotaal; details tellen niet op.
    kosten = 3 * (1500 * 0.000005 + 400 * 0.000025)
    assert data["kosten_usd_berekend"] == pytest.approx(kosten)
    assert data["gevallen"][0]["meting"]["thinking_tokens"] == 37


async def test_deadline_breekt_hangende_inferentie_af_zonder_vervolgcall(
    tmp_path, caplog
):
    caplog.set_level(logging.DEBUG)
    grens = m.Limieten(deadline_seconden=0.05)
    manifest = tmp_path / "manifest.json"
    await m.voorbereid(manifest, limieten=grens)

    async def hangt(request):
        await asyncio.sleep(30)  # wordt na 0,05 s afgebroken
        raise AssertionError(GEHEIM)

    provider = NepProvider([hangt, _bericht("{}"), _bericht("{}")])
    start = time.monotonic()
    data, resultaat = await _live(tmp_path, manifest, provider, limieten=grens)
    assert time.monotonic() - start < 5
    assert data["stopreden"] == "timeout"
    assert data["tellingen"] == {"inferenties": 1, "telverzoeken": 1}
    assert len(provider.inferenties()) == 1
    [geval] = data["gevallen"]
    assert geval["status"] == "error"
    assert geval["meting"]["fouttype"] == "CancelledError"
    assert GEHEIM not in resultaat.read_text("utf-8")
    assert SLEUTEL not in caplog.text


# --- Q1: kwalificatieprofiel op een bevroren extern gevallenmanifest -------------------
#
# De fixture `def835_int02_kwalificatie_runner.json` is uitsluitend technisch:
# geen goldset, geen hold-out, willekeurige labels. Zij toetst de runner, nooit
# het model. Elke fase draait de echte keten met een nep-provider.

KWALFIXTURE = ROOT / "tests" / "fixtures" / "def835_int02_kwalificatie_runner.json"
KWAL = json.loads(KWALFIXTURE.read_text("utf-8"))
KWAL_PER_ID = {g["id"]: g for g in KWAL["gevallen"]}
PER_KERN = {g["invoer"]["kern"]: g["id"] for g in KWAL["gevallen"]}
FASE_IDS = {
    fase: [g["id"] for g in KWAL["gevallen"] if g["fase"] == fase]
    for fase in ("regressie", "ontwikkeling", "holdout")
}
LABELMERKTEKENS = [g["label"]["normgrond"] for g in KWAL["gevallen"]]
KOSTEN_PER_CALL = 1500 * 0.000005 + 400 * 0.000025
RESERVERING_PER_CALL = 16000 * 0.000005 + 6000 * 0.000025
OUDE_IDENTITEITSVELDEN = {
    "profiel",
    "limieten",
    "dienstbudget",
    "prijzen_per_token",
    "router",
    "transport",
    "normhash",
    "t_tekst_sha256",
    "bestanden",
    "versies",
    "gevallen",
}


def test_kwalificatiefixture_is_zichtbaar_geen_goldset():
    assert KWAL["technische_testfixture"] is True
    assert KWAL["goldset"] is False
    assert "GEEN goldset" in KWAL["gebruik"]
    assert [len(FASE_IDS[f]) for f in FASE_IDS] == [3, 24, 16]
    assert FASE_IDS["regressie"] == ["C105", "C107", "C112"]
    for geval_id in FASE_IDS["regressie"]:
        assert KWAL_PER_ID[geval_id]["invoer"] == GEVALLEN[geval_id]["invoer"]


def _oordeel(invoer: dict, soort: str) -> str:
    """Geldig WP1-antwoord met het gevraagde verdict (of een citaatfout)."""
    if soort == "review_required":
        return json.dumps(
            {
                "verdict": "insufficient_information",
                "passages": [],
                "reason": "Offline: betekenisgrond ontbreekt.",
                "question": "Welke bedoeling geldt?",
                "uncertainty": "decisive",
                "scope_reason": None,
                "coverage": "partial",
            }
        )
    kern = invoer["kern"]
    grond = {"field": "kern", "ref": None, "quote": None, "start": None, "end": None}
    passage = {
        "quote": kern,
        "start": 1 if soort == "citaatfout" else 0,
        "end": len(kern),
        "function": "actor_prescription" if soort == "fail" else "criterion",
        "ground": grond,
    }
    return json.dumps(
        {
            "verdict": "fail" if soort == "fail" else "pass",
            "passages": [passage],
            "reason": "Offline nep-oordeel.",
            "question": None,
            "uncertainty": "none",
            "scope_reason": None,
            "coverage": "complete",
        }
    )


class KwalProvider:
    """Nep-provider: antwoordt per geval volgens het label, tenzij afwijkend.

    Het geval wordt uit de verzonden invoer herkend (de kern), nooit uit een
    label: het verzoek bevat geen labels. Met `grootboek` wordt bij elk
    verzoek de dan geldende laatste grootboekregel vastgelegd.
    """

    def __init__(self, afwijkend=None, *, telling=1200, grootboek=None, usage=None):
        self.verzoeken: list[dict] = []
        self.afwijkend = dict(afwijkend or {})
        self.telling = telling
        self.grootboek = grootboek
        self.usage = usage
        self.boekstand: list[tuple[str, str, dict]] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        invoer = json.loads(body["messages"][0]["content"])["invoer"]
        geval = PER_KERN[invoer["kern"]]
        self.verzoeken.append({"pad": request.url.path, "geval": geval, "ruw": request})
        if self.grootboek is not None:
            laatste = self.grootboek.read_text("utf-8").splitlines()[-1]
            self.boekstand.append((request.url.path, geval, json.loads(laatste)))
        if request.url.path.endswith("/count_tokens"):
            return httpx.Response(200, json={"input_tokens": self.telling})
        actie = self.afwijkend.get(geval, KWAL_PER_ID[geval]["label"]["status"])
        if callable(actie):
            return actie(request)
        return httpx.Response(
            200, json=_bericht(_oordeel(invoer, actie), usage=self.usage)
        )

    def paden(self):
        return [v["pad"] for v in self.verzoeken]

    def inferenties(self):
        return [v["geval"] for v in self.verzoeken if v["pad"] == "/v1/messages"]

    def ruw(self) -> str:
        return "".join(v["ruw"].content.decode("utf-8") for v in self.verzoeken)


class Kwal:
    def __init__(self, tmp_path: Path, gevallen: Path) -> None:
        self.tmp = tmp_path
        self.gevallen = gevallen
        self.proefmap = tmp_path / "proef"
        self.manifest = tmp_path / "kwal-manifest.json"
        self.payloads = tmp_path / "kwal-payloads.json"

    @property
    def grootboek(self) -> Path:
        return self.proefmap / "grootboek.jsonl"

    def stand(self) -> dict:
        boek = m.Grootboek.lees(self.grootboek, _sha(self.manifest.read_bytes()))
        return boek.stand()


def _submap(tmp_path: Path, naam: str) -> Path:
    pad = tmp_path / naam
    pad.mkdir()
    return pad


def _gevallenbestand(tmp_path: Path, wijzig=None, naam="gevallen.json") -> Path:
    data = json.loads(json.dumps(KWAL))
    if wijzig is not None:
        wijzig(data)
    pad = tmp_path / naam
    pad.write_text(json.dumps(data, ensure_ascii=False), "utf-8")
    return pad


async def _kwal(tmp_path: Path, *, limieten=None, wijzig=None) -> Kwal:
    k = Kwal(tmp_path, _gevallenbestand(tmp_path, wijzig))
    await m.voorbereid_kwalificatie(
        k.gevallen,
        k.proefmap,
        k.manifest,
        payloads_pad=k.payloads,
        limieten=limieten or m.KWALIFICATIELIMIETEN,
    )
    return k


def _kwalakkoord(pad: Path, k: Kwal, **over) -> Path:
    grens = json.loads(k.manifest.read_text("utf-8"))["identiteit"]["limieten"]
    data = {
        "soort": m.KWALIFICATIE_AKKOORD_SOORT,
        "manifest_sha256": _sha(k.manifest.read_bytes()),
        "gevallenmanifest_sha256": _sha(k.gevallen.read_bytes()),
        "protocol_sha256": m.PROTOCOL_SHA256,
        "profiel_id": m.KWALIFICATIE_PROFIEL_ID,
        "geen_def815_kwalificatie": True,
        "live_verzending_toegestaan": True,
        "max_inferenties": grens["max_inferentie"],
        "max_tokenmetingen": grens["max_telverzoeken"],
        "budget_usd": grens["budget_usd"],
        "akkoord_door": "offline testbeoordelaar",
        "akkoord_op": "2026-09-28",
        "akkoord_bron": "offline unittest; geen echte toestemming",
    }
    data.update(over)
    data = {k2: v for k2, v in data.items() if v is not ...}
    pad.write_text(json.dumps(data), "utf-8")
    return pad


async def _fase(k: Kwal, fase: str, provider, *, akkoord=None, **kw):
    if akkoord is None:
        akkoord = k.tmp / "kwal-akkoord.json"
        if not akkoord.exists():
            _kwalakkoord(akkoord, k)
    kw.setdefault("sleutel", lambda: SLEUTEL)
    kw.setdefault("limieten", m.KWALIFICATIELIMIETEN)
    return await m.voer_kwalificatie_uit(
        k.manifest,
        akkoord,
        k.gevallen,
        fase,
        binnen=httpx.MockTransport(provider),
        **kw,
    )


async def _tot_en_met(k: Kwal, laatste: str) -> None:
    for fase in ("regressie", "ontwikkeling", "holdout"):
        data = await _fase(k, fase, KwalProvider())
        assert data["evaluatie"]["mechanisch_geslaagd"] is True
        if fase == laatste:
            return


# --- Q1: voorbereiding en freeze --------------------------------------------------------


async def test_kwal_voorbereiding_bindt_invoer_labels_splitsing_en_profiel(
    tmp_path, monkeypatch
):
    def geen_sleutel():
        raise AssertionError("voorbereiding leest geen sleutel")

    monkeypatch.setattr(m, "_lees_sleutel", geen_sleutel)
    k = await _kwal(tmp_path)
    data = json.loads(k.manifest.read_text("utf-8"))
    assert data["soort"] == m.KWALIFICATIE_MANIFEST_SOORT != m.MANIFEST_SOORT
    assert data["toestemming"] == "pending"
    identiteit = data["identiteit"]
    assert data["identiteit_sha256"] == m.hash_json(identiteit)
    profiel = identiteit["profiel"]
    assert profiel["profiel_id"] == m.KWALIFICATIE_PROFIEL_ID != m.PROFIEL_ID
    assert (profiel["provider"], profiel["model"]) == ("anthropic", "claude-opus-5")
    assert profiel["def815_kwalificatie"] is False
    assert identiteit["limieten"] == {
        "max_inferentie": 43,
        "max_telverzoeken": 43,
        "max_uitvoertokens": 6000,
        "max_geschatte_invoertokens": 16000,
        "deadline_seconden": 120.0,
        "totale_looptijd_seconden": 6000.0,
        "budget_usd": 12.0,
    }
    assert identiteit["protocol_sha256"] == (
        "53a199fdff49c7ec40c10e84c79356fd72dcba6190cb75c715ce077c1054f18f"
    )
    assert identiteit["gevallenmanifest"]["sha256"] == _sha(k.gevallen.read_bytes())
    assert identiteit["gevallenmanifest"]["technische_testfixture"] is True
    assert identiteit["gevallenmanifest"]["freeze"] == KWAL["freeze"]
    assert identiteit["fasen"] == FASE_IDS
    assert identiteit["proefmap"] == str(k.proefmap.resolve())
    assert identiteit["router"]["uitkomst"] == ["anthropic", "claude-opus-5"]
    assert "scripts/analysis/def835_int02_modelproef.py" in identiteit["bestanden"]
    per_geval = {g["id"]: g for g in identiteit["gevallen"]}
    assert list(per_geval) == [g["id"] for g in KWAL["gevallen"]]
    for geval_id, geval in per_geval.items():
        bron = KWAL_PER_ID[geval_id]
        assert geval["fase"] == bron["fase"]
        assert geval["invoer_sha256"] == m.hash_json(bron["invoer"])
        assert geval["label_sha256"] == m.hash_json(bron["label"])
    # Offline: geen proefmap, geen grootboek, alleen manifest en payloads.
    assert not k.proefmap.exists()
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "gevallen.json",
        "kwal-manifest.json",
        "kwal-payloads.json",
    ]
    tekst = k.manifest.read_text("utf-8") + k.payloads.read_text("utf-8")
    assert all(merk not in tekst for merk in LABELMERKTEKENS)


async def test_kwal_labels_raken_payload_niet_maar_wel_de_identiteit(tmp_path):
    een = await _kwal(_submap(tmp_path, "a"))

    def ander_label(data):
        for geval in data["gevallen"]:
            if geval["id"] == "TQ-O01":
                geval["label"] = {"status": "fail", "normgrond": "ANDER-LABEL"}

    twee = await _kwal(_submap(tmp_path, "b"), wijzig=ander_label)
    i1 = json.loads(een.manifest.read_text("utf-8"))["identiteit"]
    i2 = json.loads(twee.manifest.read_text("utf-8"))["identiteit"]
    p1 = [g["payload_sha256"] for g in i1["gevallen"]]
    p2 = [g["payload_sha256"] for g in i2["gevallen"]]
    assert p1 == p2  # het verzoek hangt niet van labels af
    l1 = {g["id"]: g["label_sha256"] for g in i1["gevallen"]}
    l2 = {g["id"]: g["label_sha256"] for g in i2["gevallen"]}
    assert [i for i in l1 if l1[i] != l2[i]] == ["TQ-O01"]
    assert m.hash_json(i1) != m.hash_json(i2)
    payloads = json.loads(een.payloads.read_text("utf-8"))["gevallen"]
    for vast in payloads:
        body = json.loads(vast["payload"])
        [bericht] = body["messages"]
        assert json.loads(bericht["content"]) == {
            "invoer": KWAL_PER_ID[vast["id"]]["invoer"]
        }
        assert "TECHNISCH-TESTLABEL" not in vast["payload"]
        assert "normgrond" not in vast["payload"]


def _zet(geval_id, veld, waarde):
    def wijzig(data):
        for geval in data["gevallen"]:
            if geval["id"] == geval_id:
                geval[veld] = waarde

    return wijzig


def _zonder(veld):
    def wijzig(data):
        del data[veld]

    return wijzig


def _topveld(veld, waarde):
    def wijzig(data):
        data[veld] = waarde

    return wijzig


def _dubbel(data):
    data["gevallen"].append(dict(data["gevallen"][5]))


def _holdout_naar_ontwikkeling(data):
    data["gevallen"][-1]["fase"] = "ontwikkeling"


_BASISINVOER = KWAL_PER_ID["TQ-O01"]["invoer"]


@pytest.mark.parametrize(
    ("wijzig", "reden"),
    [
        (_zonder("freeze"), "freeze_ontbreekt"),
        (
            _topveld("freeze", {**KWAL["freeze"], "status": "concept"}),
            "freeze_ontbreekt",
        ),
        (
            _topveld("freeze", {**KWAL["freeze"], "geaccepteerd_door": " "}),
            "freeze_ontbreekt",
        ),
        (
            _topveld("freeze", {**KWAL["freeze"], "geaccepteerd_op": "morgen"}),
            "freeze_ontbreekt",
        ),
        (_topveld("protocol_sha256", "0" * 64), "protocol_afwijkend"),
        (_topveld("soort", m.MANIFEST_SOORT), "gevallenmanifest_ongeldig"),
        (_topveld("goldset", "nee"), "gevallenmanifest_ongeldig"),
        (_dubbel, "gevallenmanifest_ongeldig"),
        (_zet("TQ-O01", "label", {"status": "misschien"}), "gevallenmanifest_ongeldig"),
        (
            _zet("TQ-O01", "label", {"status": "pass", "extra": 1}),
            "gevallenmanifest_ongeldig",
        ),
        (
            _zet("TQ-O01", "invoer", {**_BASISINVOER, "label": "pass"}),
            "gevallenmanifest_ongeldig",
        ),
        (
            _zet("TQ-O01", "invoer", {**_BASISINVOER, "organisatorische_context": []}),
            "gevallenmanifest_ongeldig",
        ),
        (_zet("TQ-O01", "verwacht", "pass"), "gevallenmanifest_ongeldig"),
        (
            _zet("C107", "invoer", {**GEVALLEN["C107"]["invoer"], "bedoeling": "x"}),
            "splitsing_ongeldig",
        ),
        (_zet("C107", "label", {"status": "fail"}), "splitsing_ongeldig"),
        (_zet("C105", "fase", "ontwikkeling"), "splitsing_ongeldig"),
        (_zet("TQ-O01", "fase", "training"), "splitsing_ongeldig"),
        (_holdout_naar_ontwikkeling, "splitsing_ongeldig"),
        (_zet("TQ-H01", "label", {"status": "fail"}), "verdeling_afwijkend"),
    ],
    ids=[
        "geen-freeze",
        "freeze-concept",
        "freeze-zonder-acceptant",
        "freeze-datum",
        "protocol",
        "oud-manifestsoort",
        "goldsetvlag",
        "dubbel-id",
        "labelstatus",
        "labelveld",
        "label-in-invoer",
        "ne-invoer",
        "onbekend-gevalveld",
        "regressie-invoer",
        "regressie-label",
        "regressie-fase",
        "onbekende-fase",
        "aantallen",
        "holdoutverdeling",
    ],
)
async def test_kwal_voorbereiding_weigert_ongeldig_of_niet_bevroren_manifest(
    tmp_path, wijzig, reden
):
    gevallen = _gevallenbestand(tmp_path, wijzig)
    with pytest.raises(m.ProefGeweigerdError) as fout:
        await m.voorbereid_kwalificatie(
            gevallen, tmp_path / "proef", tmp_path / "manifest.json"
        )
    assert fout.value.reden == reden
    assert not (tmp_path / "manifest.json").exists()


async def test_kwal_dryrun_gebruikt_geen_echt_transport(tmp_path, monkeypatch):
    async def verboden(self, request):
        raise AssertionError("dry-run verstuurt niets")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", verboden)
    k = await _kwal(tmp_path)
    assert json.loads(k.manifest.read_text("utf-8"))["toestemming"] == "pending"


async def test_driecasusmodus_identiteitsvorm_ongewijzigd(tmp_path):
    data = await m.voorbereid(tmp_path / "manifest.json")
    assert data["soort"] == "def835-int02-modelproef-manifest/1"
    assert set(data["identiteit"]) == OUDE_IDENTITEITSVELDEN
    assert m.PROFIEL_ID == "def835-technische-proef-opus5-v1"
    assert (m.LIMIETEN.max_inferentie, m.LIMIETEN.budget_usd) == (3, 1.0)
    assert m.AKKOORD_SOORT == "def835-int02-modelproef-akkoord/1"


# --- Q1: akkoord, oud mandaat en identiteit ------------------------------------------------


@pytest.mark.parametrize(
    "over",
    [
        {"manifest_sha256": "0" * 64},
        {"gevallenmanifest_sha256": "0" * 64},
        {"protocol_sha256": "0" * 64},
        {"profiel_id": "def835-technische-proef-opus5-v1"},
        {"soort": "def835-int02-modelproef-akkoord/1"},
        {"max_inferenties": 44},
        {"max_tokenmetingen": ...},
        {"budget_usd": 13.0},
        {"live_verzending_toegestaan": "ja"},
        {"geen_def815_kwalificatie": False},
        {"akkoord_door": " "},
        {"akkoord_op": "gisteren"},
        {"extra": "veld"},
    ],
    ids=lambda o: next(iter(o)),
)
async def test_kwal_weigert_ongeldig_akkoord_zonder_verzoek_sleutel_of_proefmap(
    tmp_path, over
):
    k = await _kwal(tmp_path)
    provider = KwalProvider()
    gelezen = []
    akkoord = _kwalakkoord(tmp_path / "ander-akkoord.json", k, **over)
    with pytest.raises(m.ProefGeweigerdError) as fout:
        await _fase(
            k,
            "regressie",
            provider,
            akkoord=akkoord,
            sleutel=lambda: gelezen.append(1) or SLEUTEL,
        )
    assert fout.value.reden == "akkoord_ongeldig"
    assert provider.verzoeken == [] and gelezen == []
    assert not k.proefmap.exists()


async def test_kwal_weigert_ontbrekend_akkoord(tmp_path):
    k = await _kwal(tmp_path)
    provider = KwalProvider()
    with pytest.raises(m.ProefGeweigerdError) as fout:
        await _fase(k, "regressie", provider, akkoord=tmp_path / "bestaat-niet.json")
    assert fout.value.reden == "akkoord_ontbreekt"
    assert provider.verzoeken == []
    assert not k.proefmap.exists()


async def test_kwal_oud_driecallmandaat_telt_nooit_als_kwalificatieakkoord(
    tmp_path, manifest
):
    k = await _kwal(tmp_path)
    provider = KwalProvider()
    # (a) Een oud driecallakkoord, zelfs op het nieuwe manifest gericht.
    oud = _akkoord(tmp_path / "oud-akkoord.json", k.manifest)
    with pytest.raises(m.ProefGeweigerdError) as fout:
        await _fase(k, "regressie", provider, akkoord=oud)
    assert fout.value.reden == "akkoord_ongeldig"
    # (b) Het oude driecasusmanifest met een kwalificatieakkoord erop.
    oude_k = Kwal(tmp_path, k.gevallen)
    oude_k.manifest = manifest
    akkoord = tmp_path / "kwal-op-oud.json"
    akkoord.write_text(
        json.dumps(
            {
                **json.loads(_kwalakkoord(tmp_path / "hulp.json", k).read_text()),
                "manifest_sha256": _sha(manifest.read_bytes()),
            }
        ),
        "utf-8",
    )
    with pytest.raises(m.ProefGeweigerdError) as fout:
        await _fase(oude_k, "regressie", provider, akkoord=akkoord)
    assert fout.value.reden == "akkoord_ongeldig"
    # (c) Een kwalificatieakkoord opent de oude driecasusmodus niet.
    oude_provider = NepProvider()
    with pytest.raises(m.ProefGeweigerdError) as fout:
        await _live(tmp_path, manifest, oude_provider, akkoord=akkoord)
    assert fout.value.reden == "akkoord_ongeldig"
    assert provider.verzoeken == [] and oude_provider.verzoeken == []
    assert not k.proefmap.exists()


def _wijzig_invoer(data):
    for geval in data["gevallen"]:
        if geval["id"] == "TQ-O02":
            geval["invoer"] = {**geval["invoer"], "kern": "Andere technische kern."}


def _wijzig_label(data):
    for geval in data["gevallen"]:
        if geval["id"] == "TQ-O02":
            geval["label"] = {**geval["label"], "status": "fail"}


def _wissel_splitsing(data):
    """TQ-O01 (pass) en TQ-H01 (pass) wisselen van fase; aantallen blijven."""
    for geval in data["gevallen"]:
        if geval["id"] == "TQ-O01":
            geval["fase"] = "holdout"
        elif geval["id"] == "TQ-H01":
            geval["fase"] = "ontwikkeling"


def _wijzig_freeze(data):
    data["freeze"] = {**data["freeze"], "bron": "andere freeze"}


@pytest.mark.parametrize(
    "wijzig",
    [_wijzig_invoer, _wijzig_label, _wissel_splitsing, _wijzig_freeze],
    ids=["invoer", "label", "splitsing", "freeze"],
)
async def test_kwal_gewijzigd_gevallenmanifest_weigert_ook_met_nieuw_akkoord(
    tmp_path, wijzig
):
    k = await _kwal(tmp_path)
    provider = KwalProvider()
    # Een akkoord op het oude gevallenbestand past niet meer.
    oud_akkoord = _kwalakkoord(tmp_path / "akkoord-oud.json", k)
    data = json.loads(k.gevallen.read_text("utf-8"))
    wijzig(data)
    k.gevallen.write_text(json.dumps(data, ensure_ascii=False), "utf-8")
    with pytest.raises(m.ProefGeweigerdError) as fout:
        await _fase(k, "regressie", provider, akkoord=oud_akkoord)
    assert fout.value.reden == "akkoord_ongeldig"
    # Ook een akkoord dat het gewijzigde bestand noemt, past niet bij het manifest.
    nieuw_akkoord = _kwalakkoord(tmp_path / "akkoord-nieuw.json", k)
    with pytest.raises(m.ProefGeweigerdError) as fout:
        await _fase(k, "regressie", provider, akkoord=nieuw_akkoord)
    assert fout.value.reden == "identiteit_gewijzigd"
    assert provider.verzoeken == []
    assert not k.proefmap.exists()


async def test_kwal_gewijzigde_configuratie_weigert(tmp_path):
    k = await _kwal(tmp_path)
    provider = KwalProvider()
    ander = m.Limieten(**{**m.KWALIFICATIELIMIETEN.__dict__, "deadline_seconden": 90.0})
    with pytest.raises(m.ProefGeweigerdError) as fout:
        await _fase(k, "regressie", provider, limieten=ander)
    assert fout.value.reden == "identiteit_gewijzigd"
    assert provider.verzoeken == []


async def test_kwal_testfixture_gaat_nooit_echt_live(tmp_path):
    k = await _kwal(tmp_path)
    gelezen = []
    with pytest.raises(m.ProefGeweigerdError) as fout:
        await m.voer_kwalificatie_uit(
            k.manifest,
            _kwalakkoord(tmp_path / "akkoord.json", k),
            k.gevallen,
            "regressie",
            sleutel=lambda: gelezen.append(1) or SLEUTEL,
            binnen=None,
        )
    assert fout.value.reden == "testfixture_niet_live"
    assert gelezen == []
    assert not k.proefmap.exists()


# --- Q1: fasen, grootboek en stops ------------------------------------------------------


async def test_kwal_regressiefase_precies_drie_calls_en_duurzaam_grootboek(
    tmp_path, caplog
):
    caplog.set_level(logging.DEBUG)
    k = await _kwal(tmp_path)
    provider = KwalProvider(grootboek=k.grootboek)
    data = await _fase(k, "regressie", provider)
    # Geen verborgen overgang: alleen de drie regressiegevallen.
    assert provider.paden() == ["/v1/messages/count_tokens", "/v1/messages"] * 3
    assert provider.inferenties() == ["C105", "C107", "C112"]
    assert data["fase"] == "regressie"
    assert data["stopreden"] is None
    assert data["tellingen"] == {"inferenties": 3, "telverzoeken": 3}
    assert data["evaluatie"]["mechanisch_geslaagd"] is True
    tellers = data["evaluatie"]["tellers"]
    assert tellers["juist"] == {"teller": 3, "noemer": 3}
    assert tellers["false_pass"] == {"teller": 0, "noemer": 2}
    assert tellers["citaatfout"] == {"teller": 0, "noemer": 3}
    assert data["inhoudelijke_beoordeling"]["status"] == "open"
    assert "Chris" in data["inhoudelijke_beoordeling"]["beoordelaar"]
    assert [g["label_status"] for g in data["gevallen"]] == [
        "fail",
        "review_required",
        "pass",
    ]
    # Reservering staat vóór elk transport duurzaam in het grootboek.
    for pad, geval, laatste in provider.boekstand:
        verwacht = (
            "tel_reservering"
            if pad.endswith("count_tokens")
            else "inferentie_reservering"
        )
        assert (laatste["gebeurtenis"], laatste["geval"]) == (verwacht, geval)
    stand = k.stand()
    assert stand["inferenties"] == 3 and stand["telverzoeken"] == 3
    assert stand["besteed_usd"] == pytest.approx(3 * KOSTEN_PER_CALL)
    assert stand["onzekere_calls"] == []
    assert stand["fasen"] == {"regressie": True}
    assert stand["open_fase"] is None
    resultaat = k.proefmap / "regressie-resultaat.json"
    assert json.loads(resultaat.read_text("utf-8")) == data
    bundel = json.loads((k.proefmap / "regressie-bundel.json").read_text("utf-8"))
    assert [g["id"] for g in bundel["gevallen"]] == ["C105", "C107", "C112"]
    # Geen labels in verzoeken; geen sleutel of kerntekst in logs of bewijs.
    assert all(merk not in provider.ruw() for merk in LABELMERKTEKENS)
    assert "review_required" not in json.dumps(
        [json.loads(v["ruw"].content)["messages"] for v in provider.verzoeken]
    )
    assert SLEUTEL not in caplog.text
    assert all(g["invoer"]["kern"] not in caplog.text for g in KWAL["gevallen"])
    assert SLEUTEL not in k.grootboek.read_text("utf-8")
    assert SLEUTEL not in resultaat.read_text("utf-8")


async def test_kwal_drie_fasen_in_volgorde_cumulatief_binnen_43_calls(tmp_path):
    k = await _kwal(tmp_path)
    await _fase(k, "regressie", KwalProvider())
    provider = KwalProvider()
    ontwikkeling = await _fase(k, "ontwikkeling", provider)
    assert provider.inferenties() == FASE_IDS["ontwikkeling"]
    assert ontwikkeling["evaluatie"]["mechanisch_geslaagd"] is True
    assert ontwikkeling["cumulatief"]["inferenties"] == 27
    provider = KwalProvider()
    holdout = await _fase(k, "holdout", provider)
    assert provider.inferenties() == FASE_IDS["holdout"]
    assert holdout["evaluatie"]["mechanisch_geslaagd"] is True
    assert holdout["evaluatie"]["tellers"]["juist"] == {"teller": 16, "noemer": 16}
    assert holdout["cumulatief"]["inferenties"] == 43
    assert holdout["cumulatief"]["telverzoeken"] == 43
    assert holdout["cumulatief"]["kosten_usd_conservatief"] == pytest.approx(
        43 * KOSTEN_PER_CALL
    )
    stand = k.stand()
    assert stand["fasen"] == {"regressie": True, "ontwikkeling": True, "holdout": True}
    # Na de laatste fase is geen enkele fase opnieuw te starten.
    for fase in ("regressie", "ontwikkeling", "holdout"):
        provider = KwalProvider()
        with pytest.raises(m.ProefGeweigerdError) as fout:
            await _fase(k, fase, provider)
        assert fout.value.reden in {"proefmap_bestaat", "fase_al_uitgevoerd"}
        assert provider.verzoeken == []


@pytest.mark.parametrize(
    ("voorafgaand", "fase", "reden"),
    [
        (None, "ontwikkeling", "fasevolgorde"),
        (None, "holdout", "fasevolgorde"),
        ("regressie", "holdout", "fasevolgorde"),
        ("regressie", "regressie", "proefmap_bestaat"),
        ("ontwikkeling", "ontwikkeling", "fase_al_uitgevoerd"),
        (None, "training", "fase_onbekend"),
    ],
)
async def test_kwal_verkeerde_fasevolgorde_weigert_zonder_calls(
    tmp_path, voorafgaand, fase, reden
):
    k = await _kwal(tmp_path)
    if voorafgaand is not None:
        await _tot_en_met(k, voorafgaand)
    provider = KwalProvider()
    gelezen = []
    with pytest.raises(m.ProefGeweigerdError) as fout:
        await _fase(k, fase, provider, sleutel=lambda: gelezen.append(1) or SLEUTEL)
    assert fout.value.reden == reden
    assert provider.verzoeken == [] and gelezen == []


async def test_kwal_nieuw_akkoord_op_zelfde_manifest_reset_de_administratie_niet(
    tmp_path,
):
    k = await _kwal(tmp_path)
    await _fase(k, "regressie", KwalProvider())
    tweede = _kwalakkoord(tmp_path / "tweede.json", k, akkoord_door="iemand anders")
    provider = KwalProvider()
    with pytest.raises(m.ProefGeweigerdError) as fout:
        await _fase(k, "regressie", provider, akkoord=tweede)
    assert fout.value.reden == "proefmap_bestaat"
    data = await _fase(k, "ontwikkeling", provider, akkoord=tweede)
    assert data["tellingen"]["inferenties"] == 24
    assert data["cumulatief"]["inferenties"] == 27


async def test_kwal_onjuiste_regressiestatus_blokkeert_volgende_fase(tmp_path):
    k = await _kwal(tmp_path)
    # De historische bevinding: C107 fail in plaats van review_required.
    provider = KwalProvider({"C107": "fail"})
    data = await _fase(k, "regressie", provider)
    assert provider.inferenties() == ["C105", "C107", "C112"]
    assert data["stopreden"] is None
    assert data["evaluatie"]["mechanisch_geslaagd"] is False
    assert data["evaluatie"]["tellers"]["juist"] == {"teller": 2, "noemer": 3}
    assert k.stand()["fasen"] == {"regressie": False}
    volgende = KwalProvider()
    with pytest.raises(m.ProefGeweigerdError) as fout:
        await _fase(k, "ontwikkeling", volgende)
    assert fout.value.reden == "fasevolgorde"
    assert volgende.verzoeken == []


def _overbelast(request):
    return httpx.Response(
        529, json={"type": "error", "error": {"type": "overloaded_error"}}
    )


@pytest.mark.parametrize(
    ("fase", "afwijkend", "calls", "reden"),
    [
        ("regressie", {"C105": "pass"}, 1, "kritieke_false_pass"),
        ("regressie", {"C112": "citaatfout"}, 3, "invalid_citation"),
        ("ontwikkeling", {"TQ-O02": "citaatfout"}, 2, "invalid_citation"),
        ("ontwikkeling", {"TQ-O03": "pass"}, 3, "kritieke_false_pass"),
        ("ontwikkeling", {"TQ-O01": _overbelast}, 1, "providerfout"),
        ("holdout", {"TQ-H09": "pass"}, 9, "kritieke_false_pass"),
    ],
    ids=[
        "regressie-false-pass",
        "regressie-citaat",
        "ontwikkeling-citaat",
        "ontwikkeling-false-pass",
        "ontwikkeling-providerfout",
        "holdout-false-pass",
    ],
)
async def test_kwal_fout_of_kritieke_false_pass_stopt_direct(
    tmp_path, fase, afwijkend, calls, reden
):
    k = await _kwal(tmp_path)
    vorige = {"regressie": None, "ontwikkeling": "regressie", "holdout": "ontwikkeling"}
    if vorige[fase] is not None:
        await _tot_en_met(k, vorige[fase])
    provider = KwalProvider(afwijkend)
    data = await _fase(k, fase, provider)
    assert len(provider.inferenties()) == calls  # geen retry, geen vervolgcall
    assert data["stopreden"] == reden
    assert data["evaluatie"]["mechanisch_geslaagd"] is False
    assert k.stand()["fasen"][fase] is False
    assert k.stand()["open_fase"] is None


@pytest.mark.parametrize(
    ("afwijkend", "geslaagd"),
    [
        ({"TQ-O01": "fail", "TQ-O02": "fail", "TQ-O04": "pass"}, True),
        (
            {"TQ-O01": "fail", "TQ-O02": "fail", "TQ-O04": "pass", "TQ-O05": "fail"},
            False,
        ),
    ],
    ids=["21-van-24", "20-van-24"],
)
async def test_kwal_ontwikkelcriterium_21_van_24(tmp_path, afwijkend, geslaagd):
    k = await _kwal(tmp_path)
    await _tot_en_met(k, "regressie")
    provider = KwalProvider(afwijkend)
    data = await _fase(k, "ontwikkeling", provider)
    assert len(provider.inferenties()) == 24  # alle gevallen gerapporteerd
    assert data["stopreden"] is None
    assert data["evaluatie"]["mechanisch_geslaagd"] is geslaagd
    tellers = data["evaluatie"]["tellers"]
    assert tellers["juist"]["noemer"] == 24
    assert tellers["false_pass"]["teller"] == 1  # onterechte pass op review_required
    assert tellers["kritieke_false_pass"]["teller"] == 0


H_PASS = [i for i in FASE_IDS["holdout"] if KWAL_PER_ID[i]["label"]["status"] == "pass"]
H_FAIL = [i for i in FASE_IDS["holdout"] if KWAL_PER_ID[i]["label"]["status"] == "fail"]
H_RR = [
    i
    for i in FASE_IDS["holdout"]
    if KWAL_PER_ID[i]["label"]["status"] == "review_required"
]


@pytest.mark.parametrize(
    ("afwijkend", "geslaagd"),
    [
        ({}, True),
        ({H_PASS[0]: "fail", H_RR[0]: "fail"}, True),  # 7/8 pass, 3/4 RR, 14/16
        ({H_PASS[0]: "review_required", H_PASS[1]: "fail"}, False),  # 6/8 pass
        ({H_RR[0]: "fail", H_RR[1]: "fail"}, False),  # 2/4 RR
        ({H_FAIL[0]: "review_required"}, False),  # 3/4 fail
        ({H_RR[0]: "pass"}, False),  # onterechte goedkeuring
    ],
    ids=[
        "alles-juist",
        "14-van-16",
        "pass-6-van-8",
        "rr-2-van-4",
        "fail-3-van-4",
        "rr-pass",
    ],
)
async def test_kwal_holdoutcriteria(tmp_path, afwijkend, geslaagd):
    k = await _kwal(tmp_path)
    await _tot_en_met(k, "ontwikkeling")
    provider = KwalProvider(afwijkend)
    data = await _fase(k, "holdout", provider)
    assert len(provider.inferenties()) == 16
    assert data["stopreden"] is None
    assert data["evaluatie"]["mechanisch_geslaagd"] is geslaagd


# --- Q1: limieten en onzekere calls -----------------------------------------------------


def _boekregel(k: Kwal, regel: dict) -> None:
    with k.grootboek.open("a", encoding="utf-8") as bestand:
        bestand.write(json.dumps(regel) + "\n")


async def test_kwal_open_fase_in_grootboek_blokkeert_hergebruik(tmp_path):
    k = await _kwal(tmp_path)
    await _fase(k, "regressie", KwalProvider())
    # Een afgebroken proces: fase gestart, reservering zonder boeking en einde.
    _boekregel(k, {"gebeurtenis": "fase_start", "fase": "ontwikkeling"})
    _boekregel(
        k,
        {
            "gebeurtenis": "inferentie_reservering",
            "call": 4,
            "geval": "TQ-O01",
            "reservering_usd": RESERVERING_PER_CALL,
        },
    )
    stand = k.stand()
    assert stand["open_fase"] == "ontwikkeling"
    assert stand["onzekere_calls"] == [4]
    assert stand["besteed_usd"] == pytest.approx(
        3 * KOSTEN_PER_CALL + RESERVERING_PER_CALL
    )
    provider = KwalProvider()
    with pytest.raises(m.ProefGeweigerdError) as fout:
        await _fase(k, "ontwikkeling", provider)
    assert fout.value.reden == "grootboek_open"
    assert provider.verzoeken == []


async def test_kwal_mislukte_call_telt_mee_tegen_volle_reservering(tmp_path):
    k = await _kwal(tmp_path)
    await _tot_en_met(k, "regressie")

    def transportfout(request):
        raise httpx.ConnectError(GEHEIM, request=request)

    data = await _fase(k, "ontwikkeling", KwalProvider({"TQ-O01": transportfout}))
    assert data["stopreden"] == "transportfout"
    stand = k.stand()
    assert stand["inferenties"] == 4
    assert stand["onzekere_calls"] == [4]
    assert stand["besteed_usd"] == pytest.approx(
        3 * KOSTEN_PER_CALL + RESERVERING_PER_CALL
    )
    assert data["cumulatief"]["kosten_usd_conservatief"] == pytest.approx(
        stand["besteed_usd"]
    )
    assert GEHEIM not in k.grootboek.read_text("utf-8")


@pytest.mark.parametrize(
    "vervalsing",
    ["ander-manifest", "onbekende-gebeurtenis", "onleesbaar"],
)
async def test_kwal_grootboek_van_ander_manifest_of_onleesbaar_weigert(
    tmp_path, vervalsing
):
    k = await _kwal(tmp_path)
    await _fase(k, "regressie", KwalProvider())
    regels = k.grootboek.read_text("utf-8").splitlines()
    if vervalsing == "ander-manifest":
        kop = json.loads(regels[0])
        regels[0] = json.dumps({**kop, "manifest_sha256": "0" * 64})
    elif vervalsing == "onbekende-gebeurtenis":
        regels.append(json.dumps({"gebeurtenis": "reset", "fase": "regressie"}))
    else:
        regels.append("{afgekapt")
    k.grootboek.write_text("\n".join(regels) + "\n", "utf-8")
    provider = KwalProvider()
    with pytest.raises(m.ProefGeweigerdError) as fout:
        await _fase(k, "ontwikkeling", provider)
    assert fout.value.reden == "grootboek_ongeldig"
    assert provider.verzoeken == []


async def test_kwal_calllimiet_ontoereikend_bij_verbruikte_calls(tmp_path):
    k = await _kwal(tmp_path)
    await _fase(k, "regressie", KwalProvider())
    # Na de afgesloten regressie: extra verbruikte reserveringen (bv. uit
    # een eerdere afgebroken call) laten minder dan 24 calls over (3+17+24>43).
    regels = k.grootboek.read_text("utf-8").splitlines()
    einde = regels.pop()
    for call in range(4, 21):
        regels.append(
            json.dumps(
                {
                    "gebeurtenis": "inferentie_reservering",
                    "call": call,
                    "geval": "C112",
                    "fase": "regressie",
                    "reservering_usd": RESERVERING_PER_CALL,
                }
            )
        )
    regels.append(einde)
    k.grootboek.write_text("\n".join(regels) + "\n", "utf-8")
    provider = KwalProvider()
    with pytest.raises(m.ProefGeweigerdError) as fout:
        await _fase(k, "ontwikkeling", provider)
    assert fout.value.reden == "calllimiet_ontoereikend"
    assert provider.verzoeken == []


async def test_kwal_cumulatief_budget_weigert_voor_de_fase(tmp_path):
    k = await _kwal(tmp_path)
    await _fase(k, "regressie", KwalProvider())
    regels = [json.loads(r) for r in k.grootboek.read_text("utf-8").splitlines()]
    for regel in regels:
        if regel["gebeurtenis"] == "inferentie_boeking":
            regel["kosten_usd"] = 2.5  # 7,50 besteed: 24 x 0,23 past niet meer
    k.grootboek.write_text("".join(json.dumps(r) + "\n" for r in regels), "utf-8")
    provider = KwalProvider()
    with pytest.raises(m.ProefGeweigerdError) as fout:
        await _fase(k, "ontwikkeling", provider)
    assert fout.value.reden == "budget_ontoereikend"
    assert provider.verzoeken == []


async def test_kwal_budgetplafond_dekt_43_calls_bij_de_voorbereiding(tmp_path):
    krap = m.Limieten(**{**m.KWALIFICATIELIMIETEN.__dict__, "budget_usd": 9.0})
    with pytest.raises(m.ProefGeweigerdError) as fout:
        await m.voorbereid_kwalificatie(
            _gevallenbestand(tmp_path),
            tmp_path / "proef",
            tmp_path / "m.json",
            limieten=krap,
        )
    assert fout.value.reden == "budget_ontoereikend"


async def test_kwal_cumulatieve_looptijd_weigert_voor_de_fase(tmp_path):
    kort = m.Limieten(
        **{**m.KWALIFICATIELIMIETEN.__dict__, "totale_looptijd_seconden": 300.0}
    )
    k = await _kwal(tmp_path, limieten=kort)
    provider = KwalProvider()
    with pytest.raises(m.ProefGeweigerdError) as fout:
        await _fase(k, "regressie", provider, limieten=kort)
    assert fout.value.reden == "looptijd_ontoereikend"  # 3 x 120 s > 300 s
    assert provider.verzoeken == []
    assert not k.proefmap.exists()


async def test_kwal_tokengrenzen_stoppen_zonder_vervolgcall(tmp_path):
    k = await _kwal(tmp_path)
    provider = KwalProvider(telling=16001)
    data = await _fase(k, "regressie", provider)
    assert provider.paden() == ["/v1/messages/count_tokens"]
    assert data["stopreden"] == "invoerschatting_te_hoog"
    assert k.stand()["telverzoeken"] == 1 and k.stand()["inferenties"] == 0
    k2 = await _kwal(_submap(tmp_path, "b"))
    provider = KwalProvider(usage=_usage(output_tokens=6001))
    data = await _fase(k2, "regressie", provider)
    assert provider.inferenties() == ["C105"]
    assert data["stopreden"] == "usage_boven_limiet"


async def test_kwal_waarnemer_start_met_cumulatieve_stand(tmp_path):
    """Budget en calllimiet gelden over runs: de waarnemer erft de stand."""
    k = await _kwal(tmp_path)
    await _fase(k, "regressie", KwalProvider())
    stand = k.stand()
    waarnemer = m.Waarnemer(
        modus="live",
        limieten=m.KWALIFICATIELIMIETEN,
        binnen=httpx.MockTransport(KwalProvider()),
        prijzen={"input": 0.000005, "output": 0.000025},
    )
    waarnemer.neem_stand_over(stand)
    assert waarnemer.inferenties == 3 and waarnemer.telverzoeken == 3
    assert waarnemer.besteed_usd == pytest.approx(stand["besteed_usd"])


def test_kwal_cli_voorbereiding(tmp_path):
    gevallen = _gevallenbestand(tmp_path)
    code = m.main(
        [
            "--kwalificatie",
            str(gevallen),
            "--proefmap",
            str(tmp_path / "proef"),
            "--manifest",
            str(tmp_path / "manifest.json"),
        ]
    )
    assert code == 0
    data = json.loads((tmp_path / "manifest.json").read_text("utf-8"))
    assert data["soort"] == m.KWALIFICATIE_MANIFEST_SOORT
    assert not (tmp_path / "proef").exists()
