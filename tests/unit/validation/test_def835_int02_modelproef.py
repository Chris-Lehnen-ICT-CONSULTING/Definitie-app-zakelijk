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
