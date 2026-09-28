#!/usr/bin/env python3
"""DEF-835 — technische proefrunner voor INT-02 (experimenteel).

Experimenteel technisch proefprofiel `def835-technische-proef-opus5-v1`. Een
proefautorisatie is geen inhoudelijke modelkwalificatie en geen
DEF-815-kwaliteitsclaim. Acceptatiecriteria: technische-modelproef-voorstel-v1.

Keten (ongewijzigd): Int02AssessmentService → AIServiceV2 → AsyncGPTClient →
AnthropicClient → Anthropic-SDK → httpx. De runner voegt alleen een
`Waarnemer` toe als httpx-transport van de SDK-client: die ziet het exacte
verzoek, begrenst de payload (geen tools, cache, stream, beta of retry), telt
elke verzending (ook mislukte), vraagt vooraf de provider-tokenmeting op
dezelfde inhoud en boekt de door de provider gemelde usage.

Standaard: voorbereiding zonder netwerk en zonder sleutel. De keten draait
met een dry-run-transport dat elk verzoek opvangt en niets verstuurt; het
manifest bindt invoer, prompt, payload, configuratie, bronbestanden, profiel,
limieten en prijzen, met `toestemming: pending`. Live (`--live`) vereist een
apart, door een mens opgesteld akkoordbestand dat exact dat manifest bindt;
de runner maakt nooit zelf een akkoord. Live herberekent eerst offline de
identiteit en weigert bij elke afwijking vóór een sleutel wordt gelezen.

Binding (correcties na review). Het gerapporteerde model moet exact
`claude-opus-5` zijn, anders stopt de proef en bereikt het antwoord de keten
niet. De SDK-transportconfiguratie (basis-URL, env-headers, authenticatie)
moet de standaard zijn; afwijking wordt vóór verzending geweigerd. Tier en
geografie worden pas na het antwoord gecontroleerd (`CONTROLEMOMENTEN`).

Grenzen. Tokenmeting is een schatting; berekende kosten (gemelde usage ×
routerprijzen) zijn geen factuurgarantie; zonder betrouwbare prijs blijven
ze onbekend. Monitoring en cache van de keten
schrijven in een tijdelijke werkmap. Provider-foutteksten worden niet
gelogd of bewaard: alleen type en categorie. Geen retentieclaim over de
provider. Fixture: alleen het veld `invoer` van C105, C107 en C112.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import hashlib
import importlib
import json
import logging
import os
import platform
import re
import sys
import tempfile
import time
from collections.abc import Callable, Iterator
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, NoReturn

import httpx

logger = logging.getLogger("def835_int02_modelproef")

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "src"
CONFIG_PAD = REPO / "config" / "config.yaml"
NORM_PAD = SRC / "toetsregels" / "regels" / "INT-02.json"
FIXTURE_PAD = REPO / "tests" / "fixtures" / "def835_int02_ontwerpgevallen.json"
#: Bronbestanden van de keten; hun hash hoort bij de identiteit.
KETENBESTANDEN = (
    "config/config.yaml",
    "src/toetsregels/regels/INT-02.json",
    "tests/fixtures/def835_int02_ontwerpgevallen.json",
    "src/domain/int02/contract.py",
    "src/services/validation/int02_assessment_service.py",
    "src/services/validation/ess03_assessment_service.py",
    "src/toetsregels/runtime_contract.py",
    "src/services/ai_service_v2.py",
    "src/utils/async_api.py",
    "src/services/ai/anthropic_client.py",
    "src/services/ai/base_client.py",
    "src/services/ai/model_router.py",
    "scripts/analysis/def835_int02_modelproef.py",
)

PROFIEL_ID = "def835-technische-proef-opus5-v1"
PROVIDER = "anthropic"
MODEL = "claude-opus-5"
GEVAL_IDS = ("C105", "C107", "C112")
MANIFEST_SOORT = "def835-int02-modelproef-manifest/1"
AKKOORD_SOORT = "def835-int02-modelproef-akkoord/1"
RESULTAAT_SOORT = "def835-int02-modelproef-resultaat/1"
PAYLOAD_SOORT = "def835-int02-modelproef-payloads/1"
#: Exacte velden van een akkoordbestand (zie het verslag).
AKKOORDVELDEN = (
    "soort",
    "manifest_sha256",
    "profiel_id",
    "experimenteel",
    "geen_def815_kwalificatie",
    "live_verzending_toegestaan",
    "akkoord_door",
    "akkoord_op",
    "akkoord_bron",
)
CLAIM = (
    "Experimentele technische proef van de INT-02-keten op drie synthetische "
    "ontwikkelgevallen; geen inhoudelijke modelkwalificatie, geen "
    "DEF-815-kwaliteitsclaim. Kosten = gemelde usage x routerprijzen; geen "
    "factuurgarantie."
)
DRYRUN_SLEUTEL = "dry-run-zonder-sleutel"
DRYRUN_KWALIFICATIE = "experimenteel:dry-run:geen-kwalificatie"
#: Tekenbudget van de dienst (WP2-`Budget`); tokens/deadline via `Limieten`.
DIENSTBUDGET = {
    "max_invoertekens_veld": 2000,
    "max_invoertekens_totaal": 6000,
    "max_antwoordtekens": 24000,
}

API_HOST = "api.anthropic.com"
BERICHTEN = "/v1/messages"
TELLEN = "/v1/messages/count_tokens"
TOEGESTANE_VELDEN = frozenset(
    {"model", "max_tokens", "messages", "system", "thinking", "temperature"}
)
TELVELDEN = ("model", "system", "messages", "thinking")
#: Goedgekeurde API-versie en authenticatie: de SDK-default, zonder envopties.
API_VERSIE = "2023-06-01"
BASIS_URL = f"https://{API_HOST}"
#: Headernamen die anthropic 0.107.1 zonder envopties verstuurt; alles
#: daarbuiten (Authorization, beta, eigen headers) wordt geweigerd.
SDK_HEADERS = frozenset(
    {
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
    }
)
VASTE_HEADERS = {
    "host": API_HOST,
    "anthropic-version": API_VERSIE,
    "accept": "application/json",
    "content-type": "application/json",
    "x-stainless-retry-count": "0",
}
DOORGEGEVEN_HEADERS = frozenset(
    {"x-api-key", "anthropic-version", "user-agent", "accept"}
)
#: Velden van `anthropic.types.Usage` (SDK 0.107.1). `output_tokens` is het
#: inclusieve facturatietotaal; `output_tokens_details` telt niet op.
USAGE_VELDEN = frozenset(
    {
        "input_tokens",
        "output_tokens",
        "cache_creation_input_tokens",
        "cache_read_input_tokens",
        "cache_creation",
        "inference_geo",
        "output_tokens_details",
        "server_tool_use",
        "service_tier",
    }
)
_SUBVELDEN = {
    "cache_creation": frozenset(
        {"ephemeral_1h_input_tokens", "ephemeral_5m_input_tokens"}
    ),
    "server_tool_use": frozenset({"web_fetch_requests", "web_search_requests"}),
}
#: Standaardprijs geldt alleen voor aantoonbaar global uitgevoerde inference.
STANDAARD_GEO = "global"
#: Wat vóór verzending wordt afgedwongen en wat pas na het antwoord blijkt.
CONTROLEMOMENTEN = {
    "voor_verzending": [
        "SDK-configuratie: standaard HTTPS-eindpunt, geen env-headers of andere auth",
        "bestemming, headers, API-versie en payloadvelden per verzoek",
        "payloadhash tegen het manifest",
        "harde limieten tellingen en inferenties",
        "provider-tokenschatting en budgetreservering",
    ],
    "na_antwoord": [
        "gerapporteerd model exact het proefmodel",
        "service_tier standard (niet vooraf gepind in het verzoek)",
        "inference_geo global",
        "usagevorm, cache- en servertoolgebruik, tokenlimieten, budget",
    ],
}
_FOUTTYPE = re.compile(r"[a-z_]{1,64}")
#: Loggers die ruwe provider-uitzonderingen of payloads kunnen tonen.
_STILLE_LOGGERS = (
    "services.ai.anthropic_client",
    "services.ai.base_client",
    "services.ai_service_v2",
    "utils.async_api",
)
_STILLE_PREFIXEN = ("anthropic", "httpx", "httpcore")
_KETENMODULES = (
    "anthropic",
    "services.ai.anthropic_client",
    "services.ai_service_v2",
    "utils.async_api",
    "services.validation.int02_assessment_service",
)


@dataclass(frozen=True)
class Limieten:
    max_inferentie: int = 3
    max_telverzoeken: int = 3
    max_uitvoertokens: int = 6000
    max_geschatte_invoertokens: int = 16000
    deadline_seconden: float = 120.0
    totale_looptijd_seconden: float = 600.0
    budget_usd: float = 1.0


LIMIETEN = Limieten()


class ProefGeweigerdError(Exception):
    """De proef start niet (geen verzending); `reden` is een code."""

    def __init__(self, reden: str) -> None:
        super().__init__(reden)
        self.reden = reden


class ProefStopError(Exception):
    """De waarnemer houdt een verzoek tegen; `reden` is een code."""

    def __init__(self, reden: str) -> None:
        super().__init__(reden)
        self.reden = reden


class _OpgevangenError(Exception):
    """Dry-run: het verzoek is opgevangen en niet verstuurd."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_json(waarde: Any) -> str:
    tekst = json.dumps(waarde, sort_keys=True, separators=(",", ":"))
    return _sha(tekst.encode("ascii"))


def _geheel(waarde: Any) -> bool:
    return isinstance(waarde, int) and not isinstance(waarde, bool) and waarde >= 0


def _gevuld(waarde: Any) -> bool:
    return isinstance(waarde, str) and bool(waarde.strip())


def _json(inhoud: bytes) -> Any:
    try:
        return json.loads(inhoud)
    except ValueError:
        return None


def _fouttype(data: Any) -> str:
    """Alleen het fouttype van de provider, nooit het foutbericht."""
    fout = data.get("error") if isinstance(data, dict) else None
    soort = fout.get("type") if isinstance(fout, dict) else None
    return (
        soort if isinstance(soort, str) and _FOUTTYPE.fullmatch(soort) else "onbekend"
    )


def _niet_nul(waarde: Any) -> bool:
    if waarde is None:
        return False
    if isinstance(waarde, dict):
        return any(
            _niet_nul(v) if isinstance(v, dict) else v not in (None, 0)
            for v in waarde.values()
        )
    return True


def _vorm(waarde: Any, velden: frozenset[str]) -> bool:
    """None, of een object met alleen bekende velden en gehele waarden."""
    if waarde is None:
        return True
    return (
        isinstance(waarde, dict)
        and set(waarde) <= velden
        and all(_geheel(v) for v in waarde.values())
    )


def _standaard_basis(url: httpx.URL) -> bool:
    return (
        url.scheme == "https"
        and url.host == API_HOST
        and url.port is None
        and url.userinfo == b""
        and url.path in ("", "/")
        and url.query == b""
        and url.fragment == ""
    )


def _bevat_sleutel(waarde: Any, sleutel: str) -> bool:
    if isinstance(waarde, dict):
        return sleutel in waarde or any(
            _bevat_sleutel(v, sleutel) for v in waarde.values()
        )
    if isinstance(waarde, list):
        return any(_bevat_sleutel(v, sleutel) for v in waarde)
    return False


# --- de waarnemer aan de httpx-grens --------------------------------------------


class Waarnemer(httpx.AsyncBaseTransport):
    """httpx-transport van de SDK-client: begrenzen, tellen, meten en boeken."""

    def __init__(
        self,
        *,
        modus: str,
        limieten: Limieten = LIMIETEN,
        binnen: httpx.AsyncBaseTransport | None = None,
        verwacht: dict[str, str] | None = None,
        prijzen: dict[str, float] | None = None,
    ) -> None:
        self.modus = modus
        self.limieten = limieten
        self._binnen = binnen
        self._verwacht = dict(verwacht or {})
        self._prijzen = dict(prijzen or {})
        self.huidig: str | None = None
        self.inferenties = 0
        self.telverzoeken = 0
        self.besteed_usd = 0.0
        self.stopreden: str | None = None
        self.opgevangen: dict[str, bytes] = {}
        self.headernamen: set[str] = set()
        self.metingen: dict[str, dict[str, Any]] = {}
        self.antwoorden: dict[str, str] = {}

    @property
    def kosten_onzeker(self) -> list[str]:
        """Verstuurde inferenties zonder betrouwbaar berekende kosten."""
        return [
            geval
            for geval, meting in self.metingen.items()
            if meting.get("verstuurd") and meting.get("kosten_usd") is None
        ]

    def _stop(self, reden: str) -> NoReturn:
        self.stopreden = self.stopreden or reden
        raise ProefStopError(reden)

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        if self.stopreden is not None:
            raise ProefStopError(self.stopreden)
        body = await request.aread()
        payload = self._controleer(request, body)
        if self.modus == "dry-run":
            self.opgevangen[str(self.huidig)] = body
            raise _OpgevangenError
        meting: dict[str, Any] = {"payload_sha256": _sha(body)}
        self.metingen[str(self.huidig)] = meting
        grens = self.limieten
        if self.inferenties >= grens.max_inferentie:
            self._stop("inferentielimiet")
        if meting["payload_sha256"] != self._verwacht.get(str(self.huidig)):
            self._stop("payload_hash_mismatch")
        if await self._tel(request, payload, meting) > grens.max_geschatte_invoertokens:
            self._stop("invoerschatting_te_hoog")
        reservering = (
            grens.max_geschatte_invoertokens * self._prijzen["input"]
            + grens.max_uitvoertokens * self._prijzen["output"]
        )
        meting["reservering_usd"] = reservering
        if self.besteed_usd + reservering > grens.budget_usd:
            self._stop("budget_ontoereikend")
        return await self._verstuur(request, meting)

    def _controleer(self, request: httpx.Request, body: bytes) -> dict[str, Any]:
        url = request.url
        if not (
            request.method == "POST"
            and _standaard_basis(url.copy_with(path="/"))
            and url.path == BERICHTEN
        ):
            self._stop("onverwachte_bestemming")
        namen = set(request.headers.keys())
        if not (
            namen <= SDK_HEADERS
            and {"host", "anthropic-version", "x-api-key"} <= namen
            and all(
                request.headers[k] == v for k, v in VASTE_HEADERS.items() if k in namen
            )
        ):
            self._stop("transport_niet_toegestaan")
        self.headernamen |= namen
        payload = _json(body)
        berichten = payload.get("messages") if isinstance(payload, dict) else None
        toegestaan = (
            isinstance(payload, dict)
            and set(payload) <= TOEGESTANE_VELDEN
            and payload.get("model") == MODEL
            and payload.get("max_tokens") == self.limieten.max_uitvoertokens
            and payload.get("thinking", {"type": "disabled"}) == {"type": "disabled"}
            and isinstance(payload.get("system"), str)
            and isinstance(berichten, list)
            and len(berichten) == 1
            and berichten[0].get("role") == "user"
            and isinstance(berichten[0].get("content"), str)
            and not _bevat_sleutel(payload, "cache_control")
        )
        if not toegestaan:
            self._stop("payload_niet_toegestaan")
        return payload

    async def _tel(
        self, request: httpx.Request, payload: dict[str, Any], meting: dict[str, Any]
    ) -> int:
        """Provider-tokenmeting op exact dezelfde inhoud (telt mee in de limiet)."""
        if self.telverzoeken >= self.limieten.max_telverzoeken:
            self._stop("tellimiet")
        verzoek = httpx.Request(
            "POST",
            request.url.copy_with(path=TELLEN),
            # Na de headercontrole is x-api-key de enige authenticatie; die
            # gaat identiek mee, zodat telling en inference één context delen.
            headers={
                k: v for k, v in request.headers.items() if k in DOORGEGEVEN_HEADERS
            },
            json={k: payload[k] for k in TELVELDEN if k in payload},
        )
        meting["telpayload_sha256"] = _sha(verzoek.content)
        self.telverzoeken += 1
        status, data = None, None
        try:
            antwoord = await self._binnen.handle_async_request(verzoek)  # type: ignore[union-attr]
            status, data = antwoord.status_code, _json(await antwoord.aread())
        except Exception as exc:
            meting["fouttype"] = type(exc).__name__
        schatting = data.get("input_tokens") if isinstance(data, dict) else None
        if status != 200 or not _geheel(schatting):
            meting.setdefault("fouttype", _fouttype(data))
            meting["tel_http_status"] = status
            self._stop("tokenmeting_mislukt")
        meting["geschatte_invoertokens"] = schatting
        return int(schatting)

    async def _verstuur(
        self, request: httpx.Request, meting: dict[str, Any]
    ) -> httpx.Response:
        self.inferenties += 1  # telt vóór verzending: ook een mislukte call
        meting["verstuurd"] = True
        meting["kosten_usd"] = None  # pas gezet na betrouwbare boeking
        start = time.monotonic()
        try:
            antwoord = await self._binnen.handle_async_request(request)  # type: ignore[union-attr]
            inhoud = await antwoord.aread()
        except BaseException as exc:
            # Ook afbreken door een deadline (CancelledError) wordt vastgelegd;
            # de reden komt dan van de dienst (timeout).
            meting["fouttype"] = type(exc).__name__
            if isinstance(exc, Exception):
                self.stopreden = self.stopreden or "transportfout"
            raise
        finally:
            meting["duur_ms"] = round((time.monotonic() - start) * 1000)
        meting["http_status"] = antwoord.status_code
        meting["request_id"] = antwoord.headers.get("request-id")
        data = _json(inhoud)
        if antwoord.status_code != 200:
            meting["fouttype"] = _fouttype(data)
            reden: str | None = "providerfout"
        elif not isinstance(data, dict):
            reden = "antwoord_onleesbaar"
        else:
            self.antwoorden[str(self.huidig)] = inhoud.decode("utf-8", "replace")
            blokken = (
                data.get("content") if isinstance(data.get("content"), list) else []
            )
            model = data.get("model")
            meting["gerapporteerd_model"] = model if isinstance(model, str) else None
            meting["stop_reason"] = data.get("stop_reason")
            meting["inhoudsblokken"] = [
                b.get("type") if isinstance(b, dict) else None for b in blokken
            ]
            if model != MODEL:
                # R1: exact het proefmodel; geen prefix of alias. Het antwoord
                # bereikt de keten niet (geen oordeel) en krijgt geen Opus-prijs.
                self._tokens(data.get("usage"), meting)
                self._stop("model_afwijkend")
            reden = self._boek(data.get("usage"), meting)
            if reden is None and set(meting["inhoudsblokken"]) - {"text"}:
                reden = "onverwacht_inhoudsblok"
        if reden is not None:
            self.stopreden = self.stopreden or reden
        return antwoord

    @staticmethod
    def _tokens(usage: Any, meting: dict[str, Any]) -> tuple[int, int] | None:
        """Registreer de gemelde in-/uitvoertokens (zonder prijs)."""
        if not isinstance(usage, dict):
            return None
        invoer, uitvoer = usage.get("input_tokens"), usage.get("output_tokens")
        if not (_geheel(invoer) and _geheel(uitvoer)):
            return None
        meting["usage"] = {"input_tokens": invoer, "output_tokens": uitvoer}
        return invoer, uitvoer

    def _boek(self, usage: Any, meting: dict[str, Any]) -> str | None:
        """Boek de gemelde usage; een afwijking stopt verdere calls.

        Alleen standaardgebruik (tier standard, geo global, geen cache of
        servertools, bekende vorm) krijgt een prijs; anders blijven de kosten
        onbekend (`kosten_usd` None).
        """
        tokens = self._tokens(usage, meting)
        if tokens is None:
            return "usage_ontbreekt"
        invoer, uitvoer = tokens
        meting["service_tier"] = usage.get("service_tier")
        geo = usage.get("inference_geo")
        meting["inference_geo"] = geo if isinstance(geo, str) else None
        details = usage.get("output_tokens_details")
        denken = details.get("thinking_tokens") if isinstance(details, dict) else None
        if isinstance(details, dict):
            meting["thinking_tokens"] = denken
        onbekend = sorted(set(usage) - USAGE_VELDEN)
        if onbekend:
            meting["onbekende_usagevelden"] = onbekend
        if (
            onbekend
            or usage.get("service_tier") != "standard"
            or geo != STANDAARD_GEO
            or usage.get("cache_creation_input_tokens") not in (None, 0)
            or usage.get("cache_read_input_tokens") not in (None, 0)
            or not all(_vorm(usage.get(k), v) for k, v in _SUBVELDEN.items())
            or _niet_nul(usage.get("cache_creation"))
            or _niet_nul(usage.get("server_tool_use"))
            or not (
                details is None
                or (
                    set(details) == {"thinking_tokens"}
                    and _geheel(denken)
                    and denken <= uitvoer
                )
            )
        ):
            return "kostenvariant"
        kosten = invoer * self._prijzen["input"] + uitvoer * self._prijzen["output"]
        self.besteed_usd += kosten
        meting["kosten_usd"] = kosten
        grens = self.limieten
        if (
            invoer > grens.max_geschatte_invoertokens
            or uitvoer > grens.max_uitvoertokens
        ):
            return "usage_boven_limiet"
        if self.besteed_usd > grens.budget_usd:
            return "budget_overschreden"
        return None

    async def aclose(self) -> None:
        if self._binnen is not None:
            await self._binnen.aclose()


# --- omgeving en keten ------------------------------------------------------------


@contextlib.contextmanager
def _stil(namen: list[str]) -> Iterator[None]:
    """Zet loggers uit voor de duur van de proef en herstel ze daarna."""
    loggers = [logging.getLogger(naam) for naam in namen]
    vorige = [lg.disabled for lg in loggers]
    for lg in loggers:
        lg.disabled = True
    try:
        yield
    finally:
        for lg, stand in zip(loggers, vorige, strict=True):
            lg.disabled = stand


@contextlib.contextmanager
def _proefomgeving() -> Iterator[None]:
    """Tijdelijke werkmap (monitoring/cache) en stille providerloggers."""
    vorige = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="def835-modelproef-") as scratch:
        os.chdir(scratch)
        try:
            # Na de chdir: modules die bij import relatief schrijven, doen dat hier.
            for module in _KETENMODULES:
                importlib.import_module(module)
            namen = [
                naam
                for naam, lg in logging.root.manager.loggerDict.items()
                if isinstance(lg, logging.Logger)
                and (naam in _STILLE_LOGGERS or naam.split(".")[0] in _STILLE_PREFIXEN)
            ]
            with _stil(namen):
                yield
        finally:
            os.chdir(vorige)


def lees_invoer(invoer: dict[str, Any]) -> Any:
    from domain.int02.contract import maak_invoer

    return maak_invoer(**invoer)


def _lees_gevallen() -> list[tuple[str, Any]]:
    """Alleen het veld `invoer`; modelrespons en verwachting worden niet gelezen."""
    gevallen = json.loads(FIXTURE_PAD.read_text("utf-8"))["gevallen"]
    per_id = {g["id"]: g["invoer"] for g in gevallen if g.get("id") in GEVAL_IDS}
    if tuple(per_id) != GEVAL_IDS:
        raise ProefGeweigerdError("fixture_onvolledig")
    return [(geval_id, lees_invoer(per_id[geval_id])) for geval_id in GEVAL_IDS]


def _bouw_router() -> Any:
    """Bestaande ModelRouter op config.yaml; provider vast volgens die config.

    Alleen `active_provider` komt niet uit ENV/ConfigManager (geen `.env` en
    geen sleutels in de voorbereiding); tiers, capability-beleid en prijzen
    zijn die van de bestaande router.
    """
    import yaml

    from services.ai.model_router import ModelRouter

    class _ConfigRouter(ModelRouter):
        @property
        def active_provider(self) -> str:
            return str(self._config.get("active_provider"))

    config = yaml.safe_load(CONFIG_PAD.read_text("utf-8"))
    routing = config.get("model_routing") if isinstance(config, dict) else None
    if not isinstance(routing, dict):
        raise ProefGeweigerdError("config_onbekend")
    return _ConfigRouter(routing)


def _bouw_dienst(
    router: Any, waarnemer: Waarnemer, sleutel: str, kwalificatie: str
) -> tuple[Any, httpx.AsyncClient]:
    from anthropic import AsyncAnthropic

    from services.ai.anthropic_client import AnthropicClient
    from services.ai_service_v2 import AIServiceV2
    from services.validation.int02_assessment_service import (
        Budget,
        Int02AssessmentService,
        Modelprofiel,
        laad_int02_norm,
    )
    from utils.async_api import RateLimitConfig

    grens = waarnemer.limieten
    adapter = AnthropicClient(
        api_key=sleutel,
        timeout=grens.deadline_seconden,
        max_retries=0,
        model_router=router,
        rebind_on_new_loop=False,
    )
    http = httpx.AsyncClient(transport=waarnemer)
    # De adapter bouwt zijn SDK-client uit `_sdk_opties`; alleen hier wordt
    # de httpx-client van de waarnemer toegevoegd.
    adapter._sdk_opties["http_client"] = http
    sdk = adapter._client = AsyncAnthropic(**adapter._sdk_opties)
    if sdk._client is not http or sdk.max_retries != 0:
        raise ProefGeweigerdError("sdk_interceptie_onbetrouwbaar")
    # R2: de SDK leest ANTHROPIC_BASE_URL en ANTHROPIC_CUSTOM_HEADERS uit de
    # omgeving. Alleen de standaardconfiguratie met x-api-key is toegestaan;
    # dit gebeurt vóór verzending en (live) vóór het lezen van de sleutel,
    # omdat de dry-run dezelfde omgeving eerst doorloopt.
    if not (
        _standaard_basis(sdk.base_url)
        and not sdk._custom_headers
        and not sdk._custom_query
        and sdk.auth_token is None
        and sdk.credentials is None
        and sdk.custom_auth is None
        and sdk.api_key == sleutel
    ):
        raise ProefGeweigerdError("transportconfig_niet_toegestaan")
    ai = AIServiceV2(
        rate_limit_config=RateLimitConfig(
            requests_per_minute=grens.max_inferentie,
            requests_per_hour=grens.max_inferentie,
            max_concurrent=1,
            backoff_factor=1.0,
            max_retries=1,
        ),
        use_cache=False,
        ai_client=adapter,
        model_router=router,
    )
    dienst = Int02AssessmentService(
        ai,
        router,
        profiel=Modelprofiel(PROFIEL_ID, PROVIDER, MODEL, kwalificatie),
        budget=Budget(
            max_uitvoertokens=grens.max_uitvoertokens,
            deadline_seconden=grens.deadline_seconden,
            **DIENSTBUDGET,
        ),
        norm=laad_int02_norm(NORM_PAD),
        cache_size=0,
    )
    return dienst, http


@dataclass
class _Voorbereiding:
    identiteit: dict[str, Any]
    payloads: list[dict[str, str]]
    router: Any
    gevallen: list[tuple[str, Any]]


async def _bereken(limieten: Limieten) -> _Voorbereiding:
    """Offline: vang via de echte keten de exacte payload per geval op."""
    import anthropic

    from services.validation.int02_assessment_service import (
        PROMPT_VERSION,
        T_TEKST,
        TASK_TYPE,
        bouw_int02_prompt,
        laad_int02_norm,
    )

    router = _bouw_router()
    prijzen = router.get_active_pricing().get(MODEL)
    if not (
        isinstance(prijzen, dict)
        and all(
            isinstance(prijzen.get(k), float) and prijzen[k] > 0
            for k in ("input", "output")
        )
    ):
        raise ProefGeweigerdError("prijs_onbekend")
    prijzen = {"input": prijzen["input"], "output": prijzen["output"]}
    maximum = limieten.max_inferentie * (
        limieten.max_geschatte_invoertokens * prijzen["input"]
        + limieten.max_uitvoertokens * prijzen["output"]
    )
    if maximum > limieten.budget_usd:
        raise ProefGeweigerdError("budget_ontoereikend")
    gevallen = _lees_gevallen()
    waarnemer = Waarnemer(modus="dry-run", limieten=limieten)
    dienst, http = _bouw_dienst(router, waarnemer, DRYRUN_SLEUTEL, DRYRUN_KWALIFICATIE)
    try:
        with _stil(["services.validation.int02_assessment_service"]):
            for geval_id, invoer in gevallen:
                waarnemer.huidig = geval_id
                await dienst.assess(invoer)
                if geval_id not in waarnemer.opgevangen:
                    raise ProefGeweigerdError(waarnemer.stopreden or "geen_payload")
    finally:
        await http.aclose()
    norm = laad_int02_norm(NORM_PAD)
    provider, model = router.get_model(TASK_TYPE)
    per_geval = []
    for geval_id, invoer in gevallen:
        systeem, data = bouw_int02_prompt(invoer, norm)
        per_geval.append(
            {
                "id": geval_id,
                "invoer_sha256": hash_json(invoer.als_dict()),
                "systeemprompt_sha256": _sha(systeem.encode("utf-8")),
                "dataprompt_sha256": _sha(data.encode("utf-8")),
                "payload_sha256": _sha(waarnemer.opgevangen[geval_id]),
                "payload_bytes": len(waarnemer.opgevangen[geval_id]),
            }
        )
    identiteit = {
        "profiel": {
            "profiel_id": PROFIEL_ID,
            "provider": PROVIDER,
            "model": MODEL,
            "task_type": TASK_TYPE,
            "promptversie": PROMPT_VERSION,
            "experimenteel": True,
            "def815_kwalificatie": False,
        },
        "limieten": asdict(limieten),
        "dienstbudget": dict(DIENSTBUDGET),
        "prijzen_per_token": prijzen,
        "router": {
            "uitkomst": [provider, model],
            "accepts_temperature": router.accepts_temperature(model, provider=provider),
            "thinking_default_on": router.thinking_default_on(model, provider=provider),
        },
        "transport": {
            "basis_url": BASIS_URL,
            "anthropic_version": API_VERSIE,
            "authenticatie": "x-api-key",
            "headernamen": sorted(waarnemer.headernamen),
        },
        "normhash": norm.normhash,
        "t_tekst_sha256": _sha(T_TEKST.encode("utf-8")),
        "bestanden": {pad: _sha((REPO / pad).read_bytes()) for pad in KETENBESTANDEN},
        "versies": {
            "python": platform.python_version(),
            "anthropic": anthropic.__version__,
            "httpx": httpx.__version__,
        },
        "gevallen": per_geval,
    }
    payloads = [
        {"id": geval_id, "payload": waarnemer.opgevangen[geval_id].decode("utf-8")}
        for geval_id, _ in gevallen
    ]
    return _Voorbereiding(identiteit, payloads, router, gevallen)


def _schrijf_nieuw(pad: Path, data: Any) -> None:
    """Schrijf alleen naar een nieuw bestand; nooit overschrijven."""
    with pad.open("x", encoding="utf-8") as bestand:
        bestand.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def _eis_nieuw(*paden: Path | None) -> None:
    for pad in paden:
        if pad is not None and pad.exists():
            raise FileExistsError(str(pad))


def _nu() -> str:
    return datetime.now(UTC).isoformat()


# --- voorbereiding --------------------------------------------------------------------


async def voorbereid(
    manifest_pad: Path,
    *,
    payloads_pad: Path | None = None,
    limieten: Limieten = LIMIETEN,
) -> dict[str, Any]:
    """Offline manifest (toestemming pending); geen netwerk, geen sleutel."""
    manifest_pad = Path(manifest_pad).resolve()
    payloads_pad = Path(payloads_pad).resolve() if payloads_pad else None
    _eis_nieuw(manifest_pad, payloads_pad)
    with _proefomgeving():
        voorbereiding = await _bereken(limieten)
    identiteit = voorbereiding.identiteit
    manifest = {
        "soort": MANIFEST_SOORT,
        "toestemming": "pending",
        "aangemaakt": _nu(),
        "claim": CLAIM,
        "akkoordvelden": list(AKKOORDVELDEN),
        "controlemomenten": CONTROLEMOMENTEN,
        "identiteit_sha256": hash_json(identiteit),
        "identiteit": identiteit,
    }
    _schrijf_nieuw(manifest_pad, manifest)
    if payloads_pad is not None:
        _schrijf_nieuw(
            payloads_pad,
            {
                "soort": PAYLOAD_SOORT,
                "synthetisch": True,
                "identiteit_sha256": manifest["identiteit_sha256"],
                "gevallen": voorbereiding.payloads,
            },
        )
    return manifest


# --- live ---------------------------------------------------------------------------------


def _controleer_akkoord(akkoord: Any, manifest_bytes: bytes, manifest: Any) -> None:
    geldig = (
        isinstance(akkoord, dict)
        and isinstance(manifest, dict)
        and tuple(sorted(akkoord)) == tuple(sorted(AKKOORDVELDEN))
        and akkoord["soort"] == AKKOORD_SOORT
        and akkoord["manifest_sha256"] == _sha(manifest_bytes)
        and akkoord["profiel_id"] == PROFIEL_ID
        and all(
            akkoord[k] is True
            for k in (
                "experimenteel",
                "geen_def815_kwalificatie",
                "live_verzending_toegestaan",
            )
        )
        and _gevuld(akkoord["akkoord_door"])
        and _gevuld(akkoord["akkoord_bron"])
        and isinstance(akkoord["akkoord_op"], str)
        and manifest.get("soort") == MANIFEST_SOORT
        and manifest.get("toestemming") == "pending"
    )
    if geldig:
        try:
            date.fromisoformat(akkoord["akkoord_op"])
        except ValueError:
            geldig = False
    if not geldig:
        raise ProefGeweigerdError("akkoord_ongeldig")


def _lees_sleutel() -> str | None:
    """Alleen live: de sleutel uit de bestaande lokale configuratie."""
    from config.config_manager import get_config_manager

    sleutel = get_config_manager().api.anthropic_api_key
    return sleutel if _gevuld(sleutel) else None


def _stopreden(beoordeling: Any) -> str | None:
    if beoordeling.reden is not None:
        return str(beoordeling.reden)
    if beoordeling.status == "error" or beoordeling.gecachet:
        return str(beoordeling.document.foutcategorie or "error")
    return None


def _samenvatting(geval_id: str, beoordeling: Any, waarnemer: Waarnemer) -> dict:
    oordeel = beoordeling.document.oordeel
    return {
        "id": geval_id,
        "status": beoordeling.status,
        "reden": beoordeling.reden,
        "verdict": oordeel["verdict"] if oordeel else None,
        "stop_reason": beoordeling.stop_reason,
        "uitzonderingstype": beoordeling.uitzonderingstype,
        "prompt_sha256": beoordeling.prompt_sha256,
        "antwoord_sha256": beoordeling.antwoord_sha256,
        "gecachet": beoordeling.gecachet,
        "meting": waarnemer.metingen.get(geval_id, {}),
        "document": beoordeling.document.als_dict(),
    }


async def voer_live_uit(
    manifest_pad: Path,
    akkoord_pad: Path,
    resultaat_pad: Path,
    *,
    sleutel: Callable[[], str | None] = _lees_sleutel,
    binnen: httpx.AsyncBaseTransport | None = None,
    payloads_pad: Path | None = None,
    limieten: Limieten = LIMIETEN,
) -> dict[str, Any]:
    """Live proef na akkoord; sequentieel, stopt bij de eerste afwijking."""
    start, gestart = time.monotonic(), _nu()
    manifest_pad, akkoord_pad = (
        Path(manifest_pad).resolve(),
        Path(akkoord_pad).resolve(),
    )
    resultaat_pad = Path(resultaat_pad).resolve()
    payloads_pad = Path(payloads_pad).resolve() if payloads_pad else None
    _eis_nieuw(resultaat_pad, payloads_pad)
    manifest_bytes = manifest_pad.read_bytes()
    akkoord_bytes = akkoord_pad.read_bytes()
    manifest = _json(manifest_bytes)
    _controleer_akkoord(_json(akkoord_bytes), manifest_bytes, manifest)
    with _proefomgeving():
        voorbereiding = await _bereken(limieten)
        identiteit = voorbereiding.identiteit
        if identiteit != manifest.get("identiteit") or hash_json(
            identiteit
        ) != manifest.get("identiteit_sha256"):
            raise ProefGeweigerdError("identiteit_gewijzigd")
        api_sleutel = sleutel()
        if not _gevuld(api_sleutel):
            raise ProefGeweigerdError("sleutel_ontbreekt")
        waarnemer = Waarnemer(
            modus="live",
            limieten=limieten,
            binnen=binnen or httpx.AsyncHTTPTransport(retries=0),
            verwacht={g["id"]: g["payload_sha256"] for g in identiteit["gevallen"]},
            prijzen=identiteit["prijzen_per_token"],
        )
        kwalificatie = f"experimenteel:proefakkoord:{_sha(akkoord_bytes)}:geen-DEF-815"
        dienst, http = _bouw_dienst(
            voorbereiding.router, waarnemer, str(api_sleutel), kwalificatie
        )
        resultaten: list[dict[str, Any]] = []
        stopreden: str | None = None
        try:
            resterend = limieten.totale_looptijd_seconden - (time.monotonic() - start)
            async with asyncio.timeout(resterend):
                for geval_id, invoer in voorbereiding.gevallen:
                    waarnemer.huidig = geval_id
                    beoordeling = await dienst.assess(
                        invoer, correlation_id=f"def835-modelproef-{geval_id}"
                    )
                    resultaten.append(_samenvatting(geval_id, beoordeling, waarnemer))
                    stopreden = waarnemer.stopreden or _stopreden(beoordeling)
                    if stopreden is not None:
                        break
        except TimeoutError:
            stopreden = waarnemer.stopreden or "totale_looptijd"
        finally:
            await http.aclose()
    data = {
        "soort": RESULTAAT_SOORT,
        "claim": CLAIM,
        "manifest_sha256": _sha(manifest_bytes),
        "akkoord_sha256": _sha(akkoord_bytes),
        "identiteit_sha256": manifest["identiteit_sha256"],
        "gestart": gestart,
        "beeindigd": _nu(),
        "looptijd_seconden": round(time.monotonic() - start, 3),
        "stopreden": stopreden,
        "tellingen": {
            "inferenties": waarnemer.inferenties,
            "telverzoeken": waarnemer.telverzoeken,
        },
        # Onbekend (None) zodra één verstuurde inferentie geen betrouwbare
        # prijs heeft (modelafwijking, kostenvariant, fout, geen usage).
        "kosten_usd_berekend": (
            None if waarnemer.kosten_onzeker else waarnemer.besteed_usd
        ),
        "kosten_usd_bekend_deel": waarnemer.besteed_usd,
        "kosten_onzeker": waarnemer.kosten_onzeker,
        "gevallen": resultaten,
    }
    data = json.loads(json.dumps(data, ensure_ascii=False))
    _schrijf_nieuw(resultaat_pad, data)
    if payloads_pad is not None:
        _schrijf_nieuw(
            payloads_pad,
            {
                "soort": PAYLOAD_SOORT,
                "synthetisch": True,
                "identiteit_sha256": manifest["identiteit_sha256"],
                "gevallen": voorbereiding.payloads,
                "antwoorden": waarnemer.antwoorden,
            },
        )
    return data


# --- CLI ----------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--payloads", type=Path, help="nieuw bewijsbestand")
    parser.add_argument("--live", action="store_true", help="echte verzending")
    parser.add_argument("--akkoord", type=Path)
    parser.add_argument("--resultaat", type=Path)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(message)s")
    logger.setLevel(logging.INFO)
    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))
    try:
        if not args.live:
            manifest = asyncio.run(
                voorbereid(args.manifest, payloads_pad=args.payloads)
            )
            logger.info("manifest (pending): %s", manifest["identiteit_sha256"])
            return 0
        if args.akkoord is None or args.resultaat is None:
            parser.error("--live vereist --akkoord en --resultaat")
        data = asyncio.run(
            voer_live_uit(
                args.manifest, args.akkoord, args.resultaat, payloads_pad=args.payloads
            )
        )
    except ProefGeweigerdError as fout:
        logger.error("geweigerd: %s", fout.reden)
        return 2
    except FileExistsError as fout:
        logger.error("bestaat al, niet overschreven: %s", fout)
        return 2
    logger.info("stopreden: %s; tellingen: %s", data["stopreden"], data["tellingen"])
    return 0 if data["stopreden"] is None else 3


if __name__ == "__main__":
    sys.exit(main())
