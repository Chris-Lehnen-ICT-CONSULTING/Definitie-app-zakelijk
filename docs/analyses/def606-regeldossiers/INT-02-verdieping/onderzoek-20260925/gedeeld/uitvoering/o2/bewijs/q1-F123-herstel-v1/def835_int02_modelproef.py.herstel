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

Kwalificatieprofiel (Q1, kwalificatieprotocol-v1). Naast de driecasusmodus
leest `--kwalificatie` een bevroren extern gevallenmanifest (regressie 3,
ontwikkeling 24, hold-out 16) met labels die nooit in een verzoek komen. Het
eigen manifest, akkoord en profiel-ID staan los van de driecallproef: een oud
akkoord of manifest wordt geweigerd. Elke run voert precies één fase uit, in
vaste volgorde. Een alleen-toevoegend grootboek in de proefmap legt elke
reservering vóór het transport duurzaam vast; tellers, budget en looptijd
lopen daarmee door over runs van hetzelfde manifest. Een onafgesloten fase
blokkeert verdere runs (geen hervatting). De runner beoordeelt alleen de
hoofdstatus mechanisch; passagegronden beoordeelt Chris.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import hashlib
import importlib
import json
import logging
import math
import os
import platform
import re
import sys
import tempfile
import time
from collections.abc import Callable, Iterator
from dataclasses import asdict, dataclass, field
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

# --- kwalificatieprofiel (Q1) -------------------------------------------------------

KWALIFICATIE_PROFIEL_ID = "def835-kwalificatieproef-opus5-v1"
#: kwalificatieprotocol-v1.md, geaccordeerd op 28-09-2026 (vervolg-akkoord-v1).
PROTOCOL_SHA256 = "53a199fdff49c7ec40c10e84c79356fd72dcba6190cb75c715ce077c1054f18f"
GEVALLEN_SOORT = "def835-int02-kwalificatie-gevallen/1"
KWALIFICATIE_MANIFEST_SOORT = "def835-int02-kwalificatie-manifest/1"
KWALIFICATIE_AKKOORD_SOORT = "def835-int02-kwalificatie-akkoord/1"
KWALIFICATIE_RESULTAAT_SOORT = "def835-int02-kwalificatie-resultaat/1"
GROOTBOEK_SOORT = "def835-int02-kwalificatie-grootboek/1"
GROOTBOEK_NAAM = "grootboek.jsonl"
KWALIFICATIE_AKKOORDVELDEN = (
    "soort",
    "manifest_sha256",
    "gevallenmanifest_sha256",
    "protocol_sha256",
    "profiel_id",
    "geen_def815_kwalificatie",
    "live_verzending_toegestaan",
    "max_inferenties",
    "max_tokenmetingen",
    "budget_usd",
    "akkoord_door",
    "akkoord_op",
    "akkoord_bron",
)
KWALIFICATIE_CLAIM = (
    "Kwalificatieproef van het bestaande INT-02-profiel volgens "
    "kwalificatieprotocol-v1: mechanische vergelijking van de hoofdstatus met "
    "vooraf bevroren labels. Inhoudelijke passagegronden beoordeelt Chris; geen "
    "DEF-815-kwalificatie of activering. Kosten = gemelde usage x routerprijzen, "
    "een onzekere call telt voor de volle reservering; geen providerfactuurplafond."
)
FASEN = ("regressie", "ontwikkeling", "holdout")
LABELSTATUSSEN = frozenset({"pass", "fail", "review_required"})
#: Mechanische toelatingsgrenzen per fase (protocol §2). `min_juist_per_label`
#: en `verdeling` gelden voor de hold-out; een andere verdeling vraagt een
#: nieuw protocolbesluit en wordt geweigerd.
FASECRITERIA: dict[str, dict[str, Any]] = {
    "regressie": {
        "aantal": 3,
        "min_juist": 3,
        "min_juist_per_label": {},
        "max_false_pass": 0,
        "verdeling": None,
    },
    "ontwikkeling": {
        "aantal": 24,
        "min_juist": 21,
        "min_juist_per_label": {},
        "max_false_pass": None,
        "verdeling": None,
    },
    "holdout": {
        "aantal": 16,
        "min_juist": 14,
        "min_juist_per_label": {"fail": 4, "pass": 7, "review_required": 3},
        "max_false_pass": 0,
        "verdeling": {"fail": 4, "pass": 8, "review_required": 4},
    },
}
INHOUDELIJK_OPEN = {
    "status": "open",
    "beoordelaar": "Chris (acceptatie-eigenaar)",
    "toelichting": (
        "Passagegronden, normgrond en relevantie van de vraag zijn niet "
        "mechanisch vastgesteld; de runner vult hier geen akkoord in."
    ),
}
_MANIFESTVELDEN = frozenset(
    {"soort", "technische_testfixture", "goldset", "protocol_sha256", "freeze"}
    | {"gevallen", "gebruik"}
)
_FREEZEVELDEN = frozenset({"status", "geaccepteerd_door", "geaccepteerd_op", "bron"})
_GEVALVELDEN = frozenset({"id", "fase", "familie", "herkomst", "invoer", "label"})
_LABELVELDEN = frozenset({"status", "reden", "passages", "normgrond"})

#: 43 inferenties en tokenmetingen, 6.000 s en US$12 cumulatief over de fasen.
KWALIFICATIELIMIETEN = Limieten(
    max_inferentie=43,
    max_telverzoeken=43,
    totale_looptijd_seconden=6000.0,
    budget_usd=12.0,
)


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


def _bedrag(waarde: Any) -> bool:
    return (
        isinstance(waarde, int | float)
        and not isinstance(waarde, bool)
        and math.isfinite(waarde)
        and waarde >= 0
    )


def _reservering(grens: Limieten, prijzen: dict[str, float]) -> float:
    """Conservatieve kosten van één call bij de tokenmaxima."""
    return (
        grens.max_geschatte_invoertokens * prijzen["input"]
        + grens.max_uitvoertokens * prijzen["output"]
    )


# --- het grootboek van een kwalificatiemandaat ---------------------------------------


class Grootboek:
    """Alleen-toevoegend, duurzaam register van één kwalificatiemanifest.

    Eén JSON-regel per gebeurtenis, na elke regel flush en fsync. Tel- en
    inferentiereserveringen staan erin vóór het transport; een reservering
    zonder betrouwbare boeking telt voor het volle gereserveerde bedrag.
    Borging is procedureel: wie grootboek of proefmap verwijdert, verwijdert
    bewijs; dat kan de runner niet voorkomen.
    """

    def __init__(self, pad: Path, regels: list[dict[str, Any]]) -> None:
        self.pad = pad
        self.regels = regels

    @classmethod
    def nieuw(cls, proefmap: Path, manifest_sha: str, akkoord_sha: str) -> Grootboek:
        try:
            proefmap.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            raise ProefGeweigerdError("proefmap_bestaat") from None
        boek = cls(proefmap / GROOTBOEK_NAAM, [])
        boek.schrijf(
            {
                "gebeurtenis": "mandaat",
                "soort": GROOTBOEK_SOORT,
                "manifest_sha256": manifest_sha,
                "akkoord_sha256": akkoord_sha,
            }
        )
        return boek

    @classmethod
    def lees(cls, pad: Path, manifest_sha: str) -> Grootboek:
        try:
            regels = [json.loads(r) for r in pad.read_text("utf-8").splitlines()]
        except (OSError, ValueError):
            raise ProefGeweigerdError("grootboek_ongeldig") from None
        kop = regels[0] if regels else None
        if not (
            isinstance(kop, dict)
            and kop.get("gebeurtenis") == "mandaat"
            and kop.get("soort") == GROOTBOEK_SOORT
            and kop.get("manifest_sha256") == manifest_sha
        ):
            raise ProefGeweigerdError("grootboek_ongeldig")
        boek = cls(pad, regels)
        boek.stand()  # valideert elke regel
        return boek

    def schrijf(self, regel: dict[str, Any]) -> None:
        regel = {"tijd": _nu(), **regel}
        with self.pad.open("a", encoding="utf-8") as bestand:
            bestand.write(json.dumps(regel, ensure_ascii=False, sort_keys=True) + "\n")
            bestand.flush()
            os.fsync(bestand.fileno())
        self.regels.append(regel)

    def stand(self) -> dict[str, Any]:
        """Cumulatieve tellers, conservatieve besteding en fasestatus."""
        reserveringen: dict[int, float] = {}
        kosten: dict[int, float | None] = {}
        stand: dict[str, Any] = {
            "telverzoeken": 0,
            "looptijd_seconden": 0.0,
            "fasen": {},
            "open_fase": None,
        }
        for regel in self.regels[1:]:
            if not (
                isinstance(regel, dict)
                and self._verwerk(regel, stand, reserveringen, kosten)
            ):
                raise ProefGeweigerdError("grootboek_ongeldig")
        stand["inferenties"] = len(reserveringen)
        stand["onzekere_calls"] = sorted(
            c for c in reserveringen if kosten.get(c) is None
        )
        stand["besteed_usd"] = sum(
            b if (b := kosten.get(c)) is not None else r
            for c, r in reserveringen.items()
        )
        return stand

    @staticmethod
    def _verwerk(
        regel: dict[str, Any],
        stand: dict[str, Any],
        reserveringen: dict[int, float],
        kosten: dict[int, float | None],
    ) -> bool:
        soort, fase = regel.get("gebeurtenis"), regel.get("fase")
        call, duur = regel.get("call"), regel.get("looptijd_seconden")
        if soort == "tel_reservering":
            stand["telverzoeken"] += 1
        elif soort == "inferentie_reservering":
            if not (_geheel(call) and call not in reserveringen):
                return False
            if not _bedrag(regel.get("reservering_usd")):
                return False
            reserveringen[call] = float(regel["reservering_usd"])
        elif soort == "inferentie_boeking":
            if call not in reserveringen or call in kosten:
                return False
            bedrag = regel.get("kosten_usd")
            kosten[call] = float(bedrag) if _bedrag(bedrag) else None
        elif soort == "fase_start":
            if fase not in FASEN or stand["open_fase"] or fase in stand["fasen"]:
                return False
            stand["open_fase"] = fase
        elif soort == "fase_einde":
            geslaagd = regel.get("mechanisch_geslaagd")
            if fase != stand["open_fase"] or not isinstance(geslaagd, bool):
                return False
            if not _bedrag(duur):
                return False
            stand["fasen"][fase] = geslaagd
            stand["looptijd_seconden"] += float(duur)
            stand["open_fase"] = None
        else:
            return False
        return True


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
        #: Kwalificatie: reserveringen en boekingen gaan duurzaam naar hier.
        self.grootboek: Grootboek | None = None

    def neem_stand_over(self, stand: dict[str, Any]) -> None:
        """Kwalificatie: tellers en besteding lopen door over runs heen."""
        self.inferenties = stand["inferenties"]
        self.telverzoeken = stand["telverzoeken"]
        self.besteed_usd = stand["besteed_usd"]

    def _registreer(self, regel: dict[str, Any]) -> None:
        """Vóór een transport: faalt het schrijven, dan volgt geen verzending."""
        if self.grootboek is not None:
            self.grootboek.schrijf({"geval": self.huidig, **regel})

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
        reservering = _reservering(grens, self._prijzen)
        meting["reservering_usd"] = reservering
        if self.besteed_usd + reservering > grens.budget_usd:
            self._stop("budget_ontoereikend")
        call = self.inferenties + 1
        self._registreer(
            {
                "gebeurtenis": "inferentie_reservering",
                "call": call,
                "reservering_usd": reservering,
            }
        )
        try:
            return await self._verstuur(request, meting)
        finally:
            # Ook bij een fout of afbreking; zonder kosten telt de reservering.
            self._registreer(
                {
                    "gebeurtenis": "inferentie_boeking",
                    "call": call,
                    "kosten_usd": meting.get("kosten_usd"),
                    "usage": meting.get("usage"),
                }
            )

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
        self._registreer(
            {"gebeurtenis": "tel_reservering", "tel": self.telverzoeken + 1}
        )
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
    router: Any,
    waarnemer: Waarnemer,
    sleutel: str,
    kwalificatie: str,
    profiel_id: str = PROFIEL_ID,
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
        profiel=Modelprofiel(profiel_id, PROVIDER, MODEL, kwalificatie),
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
    #: Kwalificatie: per geval-ID fase en label (alleen lokale evaluatie).
    kwalgevallen: dict[str, _Kwalgeval] = field(default_factory=dict)


def _prijzen(router: Any, limieten: Limieten) -> dict[str, float]:
    """Routerprijzen van het proefmodel; het plafond dekt alle calls vooraf."""
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
    if limieten.max_inferentie * _reservering(limieten, prijzen) > limieten.budget_usd:
        raise ProefGeweigerdError("budget_ontoereikend")
    return prijzen


async def _vang(
    router: Any,
    limieten: Limieten,
    gevallen: list[tuple[str, Any]],
    profiel_id: str,
) -> Waarnemer:
    """Dry-run door de echte keten: de exacte payload per geval, zonder netwerk."""
    waarnemer = Waarnemer(modus="dry-run", limieten=limieten)
    dienst, http = _bouw_dienst(
        router, waarnemer, DRYRUN_SLEUTEL, DRYRUN_KWALIFICATIE, profiel_id
    )
    try:
        with _stil(["services.validation.int02_assessment_service"]):
            for geval_id, invoer in gevallen:
                waarnemer.huidig = geval_id
                await dienst.assess(invoer)
                if geval_id not in waarnemer.opgevangen:
                    raise ProefGeweigerdError(waarnemer.stopreden or "geen_payload")
    finally:
        await http.aclose()
    return waarnemer


def _gevalhashes(geval_id: str, invoer: Any, waarnemer: Waarnemer) -> dict[str, Any]:
    from services.validation.int02_assessment_service import (
        bouw_int02_prompt,
        laad_int02_norm,
    )

    systeem, data = bouw_int02_prompt(invoer, laad_int02_norm(NORM_PAD))
    return {
        "id": geval_id,
        "invoer_sha256": hash_json(invoer.als_dict()),
        "systeemprompt_sha256": _sha(systeem.encode("utf-8")),
        "dataprompt_sha256": _sha(data.encode("utf-8")),
        "payload_sha256": _sha(waarnemer.opgevangen[geval_id]),
        "payload_bytes": len(waarnemer.opgevangen[geval_id]),
    }


def _payloads(gevallen: list[tuple[str, Any]], waarnemer: Waarnemer) -> list[dict]:
    return [
        {"id": geval_id, "payload": waarnemer.opgevangen[geval_id].decode("utf-8")}
        for geval_id, _ in gevallen
    ]


def _profiel(profiel_id: str, **soort: bool) -> dict[str, Any]:
    from services.validation.int02_assessment_service import PROMPT_VERSION, TASK_TYPE

    return {
        "profiel_id": profiel_id,
        "provider": PROVIDER,
        "model": MODEL,
        "task_type": TASK_TYPE,
        "promptversie": PROMPT_VERSION,
        **soort,
        "def815_kwalificatie": False,
    }


def _ketenidentiteit(
    router: Any, prijzen: dict[str, float], limieten: Limieten, waarnemer: Waarnemer
) -> dict[str, Any]:
    """Limieten, prijzen, router, transport, norm/T, bronhashes en versies."""
    import anthropic

    from services.validation.int02_assessment_service import (
        T_TEKST,
        TASK_TYPE,
        laad_int02_norm,
    )

    norm = laad_int02_norm(NORM_PAD)
    provider, model = router.get_model(TASK_TYPE)
    return {
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
    }


async def _bereken(limieten: Limieten) -> _Voorbereiding:
    """Driecasusmodus, offline: de exacte payload per geval via de echte keten."""
    router = _bouw_router()
    prijzen = _prijzen(router, limieten)
    gevallen = _lees_gevallen()
    waarnemer = await _vang(router, limieten, gevallen, PROFIEL_ID)
    identiteit = {
        "profiel": _profiel(PROFIEL_ID, experimenteel=True),
        **_ketenidentiteit(router, prijzen, limieten, waarnemer),
        "gevallen": [_gevalhashes(g, invoer, waarnemer) for g, invoer in gevallen],
    }
    return _Voorbereiding(identiteit, _payloads(gevallen, waarnemer), router, gevallen)


# --- kwalificatie: het bevroren gevallenmanifest ------------------------------------------


@dataclass(frozen=True)
class _Kwalgeval:
    id: str
    fase: str
    invoer: Any
    label: dict[str, Any]


def _bevroren(freeze: Any) -> bool:
    if not (isinstance(freeze, dict) and set(freeze) == _FREEZEVELDEN):
        return False
    try:
        date.fromisoformat(freeze["geaccepteerd_op"])
    except (TypeError, ValueError):
        return False
    return (
        freeze["status"] == "bevroren"
        and _gevuld(freeze["geaccepteerd_door"])
        and _gevuld(freeze["bron"])
    )


def _kwalgeval(ruw: Any, gezien: set[str]) -> _Kwalgeval:
    """Eén geval: gesloten velden, geldig label, contractinvoer met kern en context."""
    from domain.int02.contract import ontbrekende_invoer

    ongeldig = ProefGeweigerdError("gevallenmanifest_ongeldig")
    if not (
        isinstance(ruw, dict)
        and {"id", "fase", "invoer", "label"} <= set(ruw) <= _GEVALVELDEN
        and _gevuld(ruw["id"])
        and ruw["id"] not in gezien
    ):
        raise ongeldig
    label = ruw["label"]
    if not (
        isinstance(label, dict)
        and set(label) <= _LABELVELDEN
        and label.get("status") in LABELSTATUSSEN
    ):
        raise ongeldig
    if ruw["fase"] not in FASEN:
        raise ProefGeweigerdError("splitsing_ongeldig")
    try:
        invoer = lees_invoer(ruw["invoer"])
    except (TypeError, ValueError):
        raise ongeldig from None
    if ontbrekende_invoer(invoer) is not None:
        raise ongeldig  # NE: geen modelaanroep, dus niet kwalificeerbaar
    gezien.add(ruw["id"])
    return _Kwalgeval(ruw["id"], ruw["fase"], invoer, label)


def _eis_splitsing(gevallen: list[_Kwalgeval]) -> None:
    """Aantallen per fase, de drie bekende regressies en de hold-outverdeling."""
    ontwerp = {
        g["id"]: g for g in json.loads(FIXTURE_PAD.read_text("utf-8"))["gevallen"]
    }
    per_fase = {f: [g for g in gevallen if g.fase == f] for f in FASEN}
    regressie = per_fase["regressie"]
    if any(len(per_fase[f]) != FASECRITERIA[f]["aantal"] for f in FASEN) or [
        g.id for g in regressie
    ] != list(GEVAL_IDS):
        raise ProefGeweigerdError("splitsing_ongeldig")
    for geval in regressie:
        bekend = ontwerp[geval.id]
        if (
            geval.invoer.als_dict() != bekend["invoer"]
            or geval.label["status"] != bekend["verwacht"]["status"]
        ):
            raise ProefGeweigerdError("splitsing_ongeldig")
    for fase in FASEN:
        verdeling = FASECRITERIA[fase]["verdeling"]
        telling = dict.fromkeys(sorted(LABELSTATUSSEN), 0)
        for geval in per_fase[fase]:
            telling[geval.label["status"]] += 1
        if verdeling is not None and telling != verdeling:
            raise ProefGeweigerdError("verdeling_afwijkend")


def _lees_kwalificatiegevallen(
    pad: Path,
) -> tuple[bytes, dict[str, Any], list[_Kwalgeval]]:
    """Het volledige, bevroren externe manifest; weigert elke afwijking."""
    bron = pad.read_bytes()
    data = _json(bron)
    if not (isinstance(data, dict) and data.get("soort") == GEVALLEN_SOORT):
        raise ProefGeweigerdError("gevallenmanifest_ongeldig")
    if not _bevroren(data.get("freeze")):
        raise ProefGeweigerdError("freeze_ontbreekt")
    if data.get("protocol_sha256") != PROTOCOL_SHA256:
        raise ProefGeweigerdError("protocol_afwijkend")
    vlaggen = (data.get("goldset"), data.get("technische_testfixture"))
    if not (
        set(data) <= _MANIFESTVELDEN
        and all(isinstance(v, bool) for v in vlaggen)
        and vlaggen[0] is not vlaggen[1]
        and isinstance(data.get("gevallen"), list)
    ):
        raise ProefGeweigerdError("gevallenmanifest_ongeldig")
    gezien: set[str] = set()
    gevallen = [_kwalgeval(ruw, gezien) for ruw in data["gevallen"]]
    _eis_splitsing(gevallen)
    return bron, data, gevallen


async def _bereken_kwalificatie(
    limieten: Limieten, gevallen_pad: Path, proefmap: Path
) -> _Voorbereiding:
    """Kwalificatie, offline: identiteit over invoer, labels, splitsing en keten."""
    bron, data, kwalgevallen = _lees_kwalificatiegevallen(gevallen_pad)
    router = _bouw_router()
    prijzen = _prijzen(router, limieten)
    gevallen = [(g.id, g.invoer) for g in kwalgevallen]
    waarnemer = await _vang(router, limieten, gevallen, KWALIFICATIE_PROFIEL_ID)
    identiteit = {
        "profiel": _profiel(KWALIFICATIE_PROFIEL_ID, kwalificatieproef=True),
        **_ketenidentiteit(router, prijzen, limieten, waarnemer),
        "protocol_sha256": PROTOCOL_SHA256,
        "gevallenmanifest": {
            "sha256": _sha(bron),
            "goldset": data["goldset"],
            "technische_testfixture": data["technische_testfixture"],
            "freeze": data["freeze"],
        },
        "fasen": {f: [g.id for g in kwalgevallen if g.fase == f] for f in FASEN},
        "criteria": FASECRITERIA,
        "proefmap": str(proefmap),
        "gevallen": [
            {
                **_gevalhashes(g.id, g.invoer, waarnemer),
                "fase": g.fase,
                "label_sha256": hash_json(g.label),
            }
            for g in kwalgevallen
        ],
    }
    return _Voorbereiding(
        identiteit,
        _payloads(gevallen, waarnemer),
        router,
        gevallen,
        {g.id: g for g in kwalgevallen},
    )


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


# --- kwalificatie: voorbereiding en fasen ---------------------------------------------------


async def voorbereid_kwalificatie(
    gevallen_pad: Path,
    proefmap: Path,
    manifest_pad: Path,
    *,
    payloads_pad: Path | None = None,
    limieten: Limieten = KWALIFICATIELIMIETEN,
) -> dict[str, Any]:
    """Offline kwalificatiemanifest (pending); geen netwerk, sleutel of proefmap."""
    gevallen_pad = Path(gevallen_pad).resolve()
    proefmap = Path(proefmap).resolve()
    manifest_pad = Path(manifest_pad).resolve()
    payloads_pad = Path(payloads_pad).resolve() if payloads_pad else None
    _eis_nieuw(manifest_pad, payloads_pad)
    if proefmap.exists():
        raise ProefGeweigerdError("proefmap_bestaat")
    with _proefomgeving():
        voorbereiding = await _bereken_kwalificatie(limieten, gevallen_pad, proefmap)
    identiteit = voorbereiding.identiteit
    manifest = {
        "soort": KWALIFICATIE_MANIFEST_SOORT,
        "toestemming": "pending",
        "aangemaakt": _nu(),
        "claim": KWALIFICATIE_CLAIM,
        "akkoordvelden": list(KWALIFICATIE_AKKOORDVELDEN),
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


def _gelijk_getal(waarde: Any, verwacht: Any) -> bool:
    return _bedrag(waarde) and _bedrag(verwacht) and waarde == verwacht


def _controleer_kwalificatieakkoord(
    akkoord: Any, manifest_bytes: bytes, manifest: Any, gevallen_bytes: bytes
) -> None:
    """Nieuw, strikt akkoord; een oud driecallakkoord of -manifest past nooit."""
    identiteit = manifest.get("identiteit") if isinstance(manifest, dict) else None
    grens = identiteit.get("limieten") if isinstance(identiteit, dict) else None
    geldig = (
        isinstance(akkoord, dict)
        and isinstance(grens, dict)
        and tuple(sorted(akkoord)) == tuple(sorted(KWALIFICATIE_AKKOORDVELDEN))
        and manifest.get("soort") == KWALIFICATIE_MANIFEST_SOORT
        and manifest.get("toestemming") == "pending"
        and akkoord["soort"] == KWALIFICATIE_AKKOORD_SOORT
        and akkoord["manifest_sha256"] == _sha(manifest_bytes)
        and akkoord["gevallenmanifest_sha256"] == _sha(gevallen_bytes)
        and akkoord["protocol_sha256"] == PROTOCOL_SHA256
        and akkoord["profiel_id"] == KWALIFICATIE_PROFIEL_ID
        and akkoord["geen_def815_kwalificatie"] is True
        and akkoord["live_verzending_toegestaan"] is True
        and _gelijk_getal(akkoord["max_inferenties"], grens.get("max_inferentie"))
        and _gelijk_getal(akkoord["max_tokenmetingen"], grens.get("max_telverzoeken"))
        and _gelijk_getal(akkoord["budget_usd"], grens.get("budget_usd"))
        and _gevuld(akkoord["akkoord_door"])
        and _gevuld(akkoord["akkoord_bron"])
        and isinstance(akkoord["akkoord_op"], str)
    )
    if geldig:
        try:
            date.fromisoformat(akkoord["akkoord_op"])
        except ValueError:
            geldig = False
    if not geldig:
        raise ProefGeweigerdError("akkoord_ongeldig")


def _eis_toelaatbaar(stand: dict[str, Any], fase: str) -> None:
    """Vaste volgorde; elke fase één keer; een open fase blokkeert alles."""
    if stand["open_fase"] is not None:
        raise ProefGeweigerdError("grootboek_open")
    if fase in stand["fasen"]:
        raise ProefGeweigerdError("fase_al_uitgevoerd")
    if any(stand["fasen"].get(v) is not True for v in FASEN[: FASEN.index(fase)]):
        raise ProefGeweigerdError("fasevolgorde")


def _stand_voor_fase(proefmap: Path, manifest_sha: str, fase: str) -> dict[str, Any]:
    """Alleen lezen: is `fase` nu toelaatbaar, en wat is al verbruikt?"""
    if fase == FASEN[0]:
        if proefmap.exists():
            raise ProefGeweigerdError("proefmap_bestaat")
        return {
            "inferenties": 0,
            "telverzoeken": 0,
            "besteed_usd": 0.0,
            "onzekere_calls": [],
            "looptijd_seconden": 0.0,
            "fasen": {},
            "open_fase": None,
        }
    boekpad = proefmap / GROOTBOEK_NAAM
    if not boekpad.exists():
        raise ProefGeweigerdError("fasevolgorde")
    stand = Grootboek.lees(boekpad, manifest_sha).stand()
    _eis_toelaatbaar(stand, fase)
    return stand


def _eis_ruimte(
    stand: dict[str, Any], gepland: int, grens: Limieten, prijzen: dict[str, float]
) -> None:
    """Resterende calls, budget en looptijd dekken de hele fase vooraf."""
    if (
        stand["inferenties"] + gepland > grens.max_inferentie
        or stand["telverzoeken"] + gepland > grens.max_telverzoeken
    ):
        raise ProefGeweigerdError("calllimiet_ontoereikend")
    if stand["besteed_usd"] + gepland * _reservering(grens, prijzen) > grens.budget_usd:
        raise ProefGeweigerdError("budget_ontoereikend")
    resterend = grens.totale_looptijd_seconden - stand["looptijd_seconden"]
    if resterend < gepland * grens.deadline_seconden:
        raise ProefGeweigerdError("looptijd_ontoereikend")


def _evalueer(verwacht: str, beoordeling: Any) -> dict[str, Any]:
    """Alleen lokaal: hoofdstatus tegen het bevroren label."""
    from domain.int02.contract import FOUT_CITAAT

    status = beoordeling.status
    fout = status == "error"
    citaat = fout and beoordeling.document.foutcategorie == FOUT_CITAAT
    return {
        "verwacht": verwacht,
        "waargenomen": status,
        "juist": status == verwacht,
        "technische_fout": bool(beoordeling.gecachet) or (fout and not citaat),
        "citaatfout": citaat,
        "kritieke_false_pass": verwacht == "fail" and status == "pass",
    }


#: Teller per categorie: (noemer, teller) als functies van (verwacht, waargenomen).
_TELLERS: dict[str, tuple[Callable[[str, str], bool], Callable[[str, str], bool]]] = {
    "juist": (lambda v, w: True, lambda v, w: v == w),
    "false_pass": (lambda v, w: v != "pass", lambda v, w: w == "pass"),
    "kritieke_false_pass": (lambda v, w: v == "fail", lambda v, w: w == "pass"),
    "false_fail": (lambda v, w: v != "fail", lambda v, w: w == "fail"),
    "gemiste_overtreding": (lambda v, w: v == "fail", lambda v, w: w != "fail"),
    "gepaste_onthouding": (
        lambda v, w: v == "review_required",
        lambda v, w: w == "review_required",
    ),
    "onterechte_onthouding": (
        lambda v, w: v != "review_required",
        lambda v, w: w == "review_required",
    ),
    "onzekerheid": (lambda v, w: True, lambda v, w: w == "review_required"),
}


def _tellers(uitkomsten: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    paren = [(u["verwacht"], u["waargenomen"]) for u in uitkomsten]
    tellers = {}
    for naam, (noemer, teller) in _TELLERS.items():
        binnen = [p for p in paren if noemer(*p)]
        tellers[naam] = {
            "teller": sum(teller(*p) for p in binnen),
            "noemer": len(binnen),
        }
    for status in sorted(LABELSTATUSSEN):
        binnen = [p for p in paren if p[0] == status]
        tellers[f"juist_{status}"] = {
            "teller": sum(v == w for v, w in binnen),
            "noemer": len(binnen),
        }
    for soort in ("technische_fout", "citaatfout"):
        tellers[soort] = {
            "teller": sum(bool(u[soort]) for u in uitkomsten),
            "noemer": len(uitkomsten),
        }
    return tellers


def _beoordeel_fase(
    fase: str, uitkomsten: list[dict[str, Any]], stopreden: str | None, voltooid: bool
) -> dict[str, Any]:
    """Mechanische toelatingsgrenzen; het inhoudelijke oordeel blijft open."""
    criteria = FASECRITERIA[fase]
    tellers = _tellers(uitkomsten)
    redenen = []
    if not voltooid or stopreden is not None or len(uitkomsten) != criteria["aantal"]:
        redenen.append("niet_volledig_uitgevoerd")
    if tellers["technische_fout"]["teller"] or tellers["citaatfout"]["teller"]:
        redenen.append("technische_of_citaatfout")
    if tellers["kritieke_false_pass"]["teller"]:
        redenen.append("kritieke_false_pass")
    maximum = criteria["max_false_pass"]
    if maximum is not None and tellers["false_pass"]["teller"] > maximum:
        redenen.append("onterechte_goedkeuring")
    if tellers["juist"]["teller"] < criteria["min_juist"]:
        redenen.append("te_weinig_juist")
    for status, minimum in criteria["min_juist_per_label"].items():
        if tellers[f"juist_{status}"]["teller"] < minimum:
            redenen.append(f"te_weinig_juist_{status}")
    return {
        "mechanisch_geslaagd": not redenen,
        "redenen": redenen,
        "tellers": tellers,
        "criteria": criteria,
    }


def _latentie(resultaten: list[dict[str, Any]]) -> dict[str, int | None]:
    duren = sorted(d for r in resultaten if _geheel(d := r["meting"].get("duur_ms")))
    if not duren:
        return {"max_ms": None, "p95_ms": None}
    return {"max_ms": duren[-1], "p95_ms": duren[math.ceil(0.95 * len(duren)) - 1]}


async def _draai_fase(
    dienst: Any,
    waarnemer: Waarnemer,
    voorbereiding: _Voorbereiding,
    fase: str,
    resterend: Callable[[], float],
) -> tuple[list[dict[str, Any]], str | None]:
    """Eén fase, sequentieel; stopt direct bij fout of kritieke false-pass."""
    resultaten: list[dict[str, Any]] = []
    for geval_id, invoer in voorbereiding.gevallen:
        if voorbereiding.kwalgevallen[geval_id].fase != fase:
            continue
        label = voorbereiding.kwalgevallen[geval_id].label
        if resterend() < waarnemer.limieten.deadline_seconden:
            return resultaten, "looptijd_ontoereikend"
        waarnemer.huidig = geval_id
        beoordeling = await dienst.assess(
            invoer, correlation_id=f"def835-kwalificatie-{geval_id}"
        )
        evaluatie = _evalueer(label["status"], beoordeling)
        resultaten.append(
            {
                **_samenvatting(geval_id, beoordeling, waarnemer),
                "fase": fase,
                "label_status": label["status"],
                "evaluatie": evaluatie,
            }
        )
        stopreden = waarnemer.stopreden or _stopreden(beoordeling)
        if stopreden is None and evaluatie["kritieke_false_pass"]:
            stopreden = "kritieke_false_pass"
        if stopreden is not None:
            return resultaten, stopreden
    return resultaten, None


async def voer_kwalificatie_uit(
    manifest_pad: Path,
    akkoord_pad: Path,
    gevallen_pad: Path,
    fase: str,
    *,
    sleutel: Callable[[], str | None] = _lees_sleutel,
    binnen: httpx.AsyncBaseTransport | None = None,
    limieten: Limieten = KWALIFICATIELIMIETEN,
) -> dict[str, Any]:
    """Precies één kwalificatiefase na akkoord; geen overgang naar de volgende."""
    start, gestart = time.monotonic(), _nu()
    if fase not in FASEN:
        raise ProefGeweigerdError("fase_onbekend")
    try:
        akkoord_bytes = Path(akkoord_pad).read_bytes()
    except FileNotFoundError:
        raise ProefGeweigerdError("akkoord_ontbreekt") from None
    manifest_bytes = Path(manifest_pad).read_bytes()
    gevallen_pad = Path(gevallen_pad).resolve()
    manifest = _json(manifest_bytes)
    _controleer_kwalificatieakkoord(
        _json(akkoord_bytes), manifest_bytes, manifest, gevallen_pad.read_bytes()
    )
    manifest_sha, akkoord_sha = _sha(manifest_bytes), _sha(akkoord_bytes)
    proefmap = Path(manifest["identiteit"]["proefmap"])
    stand = _stand_voor_fase(proefmap, manifest_sha, fase)
    with _proefomgeving():
        voorbereiding = await _bereken_kwalificatie(limieten, gevallen_pad, proefmap)
        identiteit = voorbereiding.identiteit
        if identiteit != manifest.get("identiteit") or hash_json(
            identiteit
        ) != manifest.get("identiteit_sha256"):
            raise ProefGeweigerdError("identiteit_gewijzigd")
        prijzen = identiteit["prijzen_per_token"]
        _eis_ruimte(stand, len(identiteit["fasen"][fase]), limieten, prijzen)
        if binnen is None and identiteit["gevallenmanifest"]["technische_testfixture"]:
            raise ProefGeweigerdError("testfixture_niet_live")
        api_sleutel = sleutel()
        if not _gevuld(api_sleutel):
            raise ProefGeweigerdError("sleutel_ontbreekt")
        waarnemer = Waarnemer(
            modus="live",
            limieten=limieten,
            binnen=binnen or httpx.AsyncHTTPTransport(retries=0),
            verwacht={g["id"]: g["payload_sha256"] for g in identiteit["gevallen"]},
            prijzen=prijzen,
        )
        kwalificatie = f"kwalificatieproef:akkoord:{akkoord_sha}:geen-DEF-815"
        dienst, http = _bouw_dienst(
            voorbereiding.router,
            waarnemer,
            str(api_sleutel),
            kwalificatie,
            KWALIFICATIE_PROFIEL_ID,
        )
        try:
            # Vanaf hier kan verzending volgen: eerst het grootboek.
            if fase == FASEN[0]:
                boek = Grootboek.nieuw(proefmap, manifest_sha, akkoord_sha)
            else:
                boek = Grootboek.lees(proefmap / GROOTBOEK_NAAM, manifest_sha)
            begin = boek.stand()
            _eis_toelaatbaar(begin, fase)
            waarnemer.neem_stand_over(begin)
            waarnemer.grootboek = boek
            boek.schrijf(
                {
                    "gebeurtenis": "fase_start",
                    "fase": fase,
                    "akkoord_sha256": akkoord_sha,
                }
            )
            resultaten: list[dict[str, Any]] = []
            stopreden: str | None = None
            voltooid = False

            def resterend() -> float:
                verbruikt = begin["looptijd_seconden"] + time.monotonic() - start
                return limieten.totale_looptijd_seconden - verbruikt

            try:
                async with asyncio.timeout(resterend()):
                    resultaten, stopreden = await _draai_fase(
                        dienst, waarnemer, voorbereiding, fase, resterend
                    )
                voltooid = True
            except TimeoutError:
                stopreden = waarnemer.stopreden or "totale_looptijd"
            finally:
                evaluatie = _beoordeel_fase(
                    fase, [r["evaluatie"] for r in resultaten], stopreden, voltooid
                )
                boek.schrijf(
                    {
                        "gebeurtenis": "fase_einde",
                        "fase": fase,
                        "looptijd_seconden": round(time.monotonic() - start, 3),
                        "stopreden": stopreden,
                        "mechanisch_geslaagd": evaluatie["mechanisch_geslaagd"],
                    }
                )
        finally:
            await http.aclose()
    eind = boek.stand()
    data = {
        "soort": KWALIFICATIE_RESULTAAT_SOORT,
        "claim": KWALIFICATIE_CLAIM,
        "fase": fase,
        "manifest_sha256": manifest_sha,
        "akkoord_sha256": akkoord_sha,
        "identiteit_sha256": manifest["identiteit_sha256"],
        "gevallenmanifest_sha256": identiteit["gevallenmanifest"]["sha256"],
        "technische_testfixture": identiteit["gevallenmanifest"][
            "technische_testfixture"
        ],
        "gestart": gestart,
        "beeindigd": _nu(),
        "looptijd_seconden": round(time.monotonic() - start, 3),
        "stopreden": stopreden,
        "tellingen": {
            "inferenties": eind["inferenties"] - begin["inferenties"],
            "telverzoeken": eind["telverzoeken"] - begin["telverzoeken"],
        },
        "cumulatief": {
            "inferenties": eind["inferenties"],
            "telverzoeken": eind["telverzoeken"],
            "kosten_usd_conservatief": eind["besteed_usd"],
            "onzekere_calls": eind["onzekere_calls"],
            "looptijd_seconden": eind["looptijd_seconden"],
        },
        "kosten_onzeker": waarnemer.kosten_onzeker,
        "evaluatie": evaluatie,
        "inhoudelijke_beoordeling": INHOUDELIJK_OPEN,
        "latentie": _latentie(resultaten),
        "gevallen": resultaten,
    }
    data = json.loads(json.dumps(data, ensure_ascii=False))
    _schrijf_nieuw(proefmap / f"{fase}-resultaat.json", data)
    fase_ids = set(identiteit["fasen"][fase])
    _schrijf_nieuw(
        proefmap / f"{fase}-bundel.json",
        {
            "soort": PAYLOAD_SOORT,
            "synthetisch": True,
            "fase": fase,
            "identiteit_sha256": manifest["identiteit_sha256"],
            "gevallen": [p for p in voorbereiding.payloads if p["id"] in fase_ids],
            "antwoorden": waarnemer.antwoorden,
        },
    )
    return data


# --- CLI ----------------------------------------------------------------------------------


def _main_kwalificatie(
    parser: argparse.ArgumentParser, args: argparse.Namespace
) -> int:
    if not args.live:
        if args.proefmap is None:
            parser.error("--kwalificatie vereist --proefmap")
        manifest = asyncio.run(
            voorbereid_kwalificatie(
                args.kwalificatie,
                args.proefmap,
                args.manifest,
                payloads_pad=args.payloads,
            )
        )
        logger.info("kwalificatiemanifest (pending): %s", manifest["identiteit_sha256"])
        return 0
    if args.akkoord is None or args.fase is None:
        parser.error("--live --kwalificatie vereist --akkoord en --fase")
    data = asyncio.run(
        voer_kwalificatie_uit(args.manifest, args.akkoord, args.kwalificatie, args.fase)
    )
    geslaagd = data["evaluatie"]["mechanisch_geslaagd"]
    logger.info(
        "fase %s: stopreden %s; mechanisch geslaagd %s; cumulatief %s",
        data["fase"],
        data["stopreden"],
        geslaagd,
        data["cumulatief"],
    )
    return 0 if geslaagd else 3


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--payloads", type=Path, help="nieuw bewijsbestand")
    parser.add_argument("--live", action="store_true", help="echte verzending")
    parser.add_argument("--akkoord", type=Path)
    parser.add_argument("--resultaat", type=Path)
    parser.add_argument(
        "--kwalificatie",
        type=Path,
        metavar="GEVALLEN",
        help="bevroren gevallenmanifest: kwalificatieprofiel i.p.v. driecasusmodus",
    )
    parser.add_argument("--proefmap", type=Path, help="nieuwe proefmap (voorbereiding)")
    parser.add_argument("--fase", help="kwalificatiefase: " + ", ".join(FASEN))
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(message)s")
    logger.setLevel(logging.INFO)
    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))
    try:
        if args.kwalificatie is not None:
            return _main_kwalificatie(parser, args)
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
