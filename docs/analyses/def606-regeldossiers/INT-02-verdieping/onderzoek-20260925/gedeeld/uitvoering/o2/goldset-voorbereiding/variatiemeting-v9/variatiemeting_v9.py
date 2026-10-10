#!/usr/bin/env python3
"""DEF-835 — variatiemeting v9 op de ontwikkelset (besluit 21), buiten het kwalificatieprotocol.

Beoordeelt de 24 ontwikkelgevallen N keer extra (standaard 2, hard maximaal
48 calls) via exact dezelfde keten als kwalificatieproef v9: dienst
`Int02AssessmentService`, profiel, router, `claude-opus-5`, prompt /6,
contract /4, schema `d3ad029e…`, de limieten per call en `use_cache=False`
komen uit de proefrunner (`scripts/analysis/def835_int02_modelproef.py`),
inclusief diens `Waarnemer` aan de httpx-grens (payloadcontrole, tokenmeting,
boeking van gemelde usage). Er wordt niets gerepareerd.

Buiten het protocol: het akkoord en het grootboek van de kwalificatie worden
niet gelezen of geschreven. Manifest v9 wordt alleen gelezen als ijkpunt
(promptversie, schemahash, prijzen, bestands- en payloadhashes van de
ontwikkelgevallen); de uitkomst is een meting van variatie, geen kwalificatie,
geen herhaling van een kwalificatiefase en geen DEF-815-claim.

Invoer: uitsluitend de 24 gevallen uit `goldset-freeze-v1/ontwikkeling-v1.json`.
Het script opent nooit een bestand met holdout, hold-out of hold_out in de
naam, en ook niet de payload- of gevallenbestanden van de kwalificatie (die
bevatten hold-outinvoer). Het label blijft lokaal en komt nooit in een verzoek.

Vóór elke call: promptversie /6 en schemahash `d3ad029e…`, de bestandshashes
van de keten en per geval invoer-, prompt- en payloadhash gelijk aan manifest
v9; anders stopt het script zonder call. Kostenplafond: vóór elke call moet de
conservatieve besteding (gemelde usage x prijzen uit manifest v9; een call
zonder betrouwbare boeking telt voor de volle reservering) plus de volle
reservering van die call binnen US$3,00 blijven.

Standaard een droge run: de keten draait met het opvangtransport van de
runner, verstuurt niets en leest geen sleutel; het script toont wat er
gestuurd zou worden en een kostenraming. Alleen met `--live` gaat er verkeer
naar de provider. Geen automatische herhaling: één poging per call. Een
transport-, provider-, kosten- of modelafwijking stopt de meting; een
citaat- of uitvoerfout van het model (`invalid_citation`, `invalid_output`)
wordt vastgelegd en de meting gaat door, want dat is zelf modelvariatie.

Sleutel (alleen live): `ANTHROPIC_API_KEY` uit de omgeving, nooit uit een
`.env`, nooit gelogd of bewaard. De aanroeper zet `DEFINITIE_DISABLE_DOTENV`;
live weigert zonder die instelling.

Uitvoer (live) in een nieuwe map: `herkomst.json`, per call een regel in
`calls.jsonl` (met het ruwe antwoord), tot slot `samenvatting.json` en
`samenvatting.md`.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.util
import json
import logging
import os
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger("def835_int02_variatiemeting_v9")

SCRIPT_PAD = Path(__file__).resolve()
MAP = SCRIPT_PAD.parent
FREEZE = MAP.parent / "goldset-freeze-v1"
ONTWIKKELING_PAD = FREEZE / "ontwikkeling-v1.json"
MANIFEST_PAD = FREEZE / "kwalificatie-manifest-v9.json"
V9_RESULTAAT_PAD = FREEZE / "kwalificatieproef-v9" / "ontwikkeling-resultaat.json"
RUNNER_RELATIEF = Path("scripts/analysis/def835_int02_modelproef.py")

#: Besluit 20: SHA-256 van `kwalificatie-manifest-v9.json`.
MANIFEST_V9_SHA256 = "30129863ebf6a379fd5eb4d667ccb22720e7e35129f5683acf8437437e98d09d"
VERWACHTE_PROMPTVERSIE = "def835-int02-prompt/6"
VERWACHTE_SCHEMAHASH = (
    "d3ad029e24b6b96242f4730686d3a4ebfebd9f46993607e41016761bc7fce715"
)
VERWACHTE_CONTRACTVERSIE = "def835-int02-assessment/4"
ONTWIKKELING_SOORT = "def835-int02-goldset-ontwikkeling/1"
AANTAL_GEVALLEN = 24
STANDAARD_HERHALINGEN = 2
MAX_CALLS = 48
MAX_HERHALINGEN = MAX_CALLS // AANTAL_GEVALLEN
KOSTENPLAFOND_USD = 3.00
#: Ruim boven 48 x de deadline per call (120 s).
TOTALE_LOOPTIJD_SECONDEN = 6000.0
#: Bestandsnamen die het script nooit opent (hold-outinvoer of -payloads).
VERBODEN_NAAMDELEN = (
    "holdout",
    "hold-out",
    "hold_out",
    "kwalificatie-payloads",
    "kwalificatie-gevallen",
)
WAARHEIDSWAARDEN = frozenset({"1", "true", "yes", "on"})
KWALIFICATIE_TEKST = "variatiemeting:besluit-21:buiten-kwalificatie:geen-DEF-815"
HERKOMST_SOORT = "def835-int02-variatiemeting-v9-herkomst/1"
CALL_SOORT = "def835-int02-variatiemeting-v9-call/1"
SAMENVATTING_SOORT = "def835-int02-variatiemeting-v9-samenvatting/1"
CLAIM = (
    "Variatiemeting op de 24 ontwikkelgevallen buiten het kwalificatieprotocol "
    "(besluit 21): dezelfde keten als kwalificatieproef v9 (prompt /6, schema "
    "d3ad029e…), N extra herhalingen. Geen kwalificatie, geen herhaling van een "
    "kwalificatiefase, geen DEF-815-claim; ontwikkelgevallen zijn een "
    "consistentietoets (7A). Kosten = gemelde usage x prijzen manifest v9; geen "
    "providerfactuur."
)
V9_RUN = "v9-fase2"


def _vind_repo() -> Path:
    for kandidaat in SCRIPT_PAD.parents:
        if (kandidaat / RUNNER_RELATIEF).is_file():
            return kandidaat
    msg = "repository met de proefrunner niet gevonden"
    raise RuntimeError(msg)


REPO = _vind_repo()
SRC = REPO / "src"


def _laad_runner() -> Any:
    """De proefrunner als module; hergebruikt een al geladen exemplaar."""
    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))
    naam = "def835_int02_modelproef"
    if naam in sys.modules:
        return sys.modules[naam]
    spec = importlib.util.spec_from_file_location(naam, REPO / RUNNER_RELATIEF)
    if spec is None or spec.loader is None:
        msg = "proefrunner niet laadbaar"
        raise RuntimeError(msg)
    module = importlib.util.module_from_spec(spec)
    sys.modules[naam] = module
    spec.loader.exec_module(module)
    return module


runner = _laad_runner()


class MetingGeweigerdError(Exception):
    """De meting start niet (niets verstuurd); `reden` is een code."""

    def __init__(self, reden: str) -> None:
        super().__init__(reden)
        self.reden = reden


@dataclass(frozen=True)
class Geval:
    id: str
    label: str
    invoer: Any


# --- lezen ------------------------------------------------------------------------


def _eis_toegestaan(pad: Path) -> Path:
    """Weigert vóór het openen elk pad met een hold-out- of kwalificatienaam."""
    naam = pad.name.lower()
    if any(deel in naam for deel in VERBODEN_NAAMDELEN):
        raise MetingGeweigerdError("verboden_bestand")
    return pad


def _lees_bytes(pad: Path) -> bytes:
    return _eis_toegestaan(pad).read_bytes()


def _lees_json(pad: Path) -> Any:
    try:
        return json.loads(_lees_bytes(pad))
    except (OSError, ValueError):
        raise MetingGeweigerdError(f"onleesbaar:{pad.name}") from None


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def lees_manifest() -> dict[str, Any]:
    """Manifest v9 als ijkpunt; alleen de ontwikkeldelen worden gebruikt."""
    bron = _lees_bytes(MANIFEST_PAD)
    if _sha(bron) != MANIFEST_V9_SHA256:
        raise MetingGeweigerdError("manifest_v9_afwijkend")
    manifest = json.loads(bron)
    identiteit = manifest["identiteit"]
    if (
        manifest.get("soort") != runner.KWALIFICATIE_MANIFEST_SOORT
        or runner.hash_json(identiteit) != manifest.get("identiteit_sha256")
        or identiteit["profiel"]["promptversie"] != VERWACHTE_PROMPTVERSIE
        or identiteit["profiel"]["model"] != runner.MODEL
        or identiteit["router"]["antwoordschema_sha256"] != VERWACHTE_SCHEMAHASH
        or identiteit["contractversie"] != VERWACHTE_CONTRACTVERSIE
    ):
        raise MetingGeweigerdError("manifest_v9_afwijkend")
    return manifest


def _ontwikkelhashes(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        g["id"]: g
        for g in manifest["identiteit"]["gevallen"]
        if g.get("fase") == "ontwikkeling"
    }


def _invoer_uit_geval(geval: dict[str, Any]) -> Any:
    """Contractinvoer uit een goldsetgeval; herkomstvelden blijven buiten."""
    context = geval["context"]
    return runner.lees_invoer(
        {
            "begrip": geval["begrip"],
            "kern": geval["kern"],
            "bedoeling": geval["bedoeling"],
            "organisatorische_context": context["organisatorische_context"],
            "juridische_context": context["juridische_context"],
            "wettelijke_basis": context["wettelijke_basis"],
            "bronnen": [{"id": b["id"], "tekst": b["tekst"]} for b in geval["bronnen"]],
        }
    )


def lees_ontwikkelset(manifest: dict[str, Any]) -> list[Geval]:
    """De 24 ontwikkelgevallen in de volgorde van manifest v9 (en fase 2)."""
    data = _lees_json(ONTWIKKELING_PAD)
    if not (
        isinstance(data, dict)
        and data.get("soort") == ONTWIKKELING_SOORT
        and isinstance(data.get("freeze"), dict)
        and data["freeze"].get("status") == "bevroren"
        and isinstance(data.get("gevallen"), list)
    ):
        raise MetingGeweigerdError("ontwikkelset_ongeldig")
    volgorde = manifest["identiteit"]["fasen"]["ontwikkeling"]
    per_id: dict[str, Geval] = {}
    for ruw in data["gevallen"]:
        geval_id = ruw.get("id") if isinstance(ruw, dict) else None
        if geval_id not in volgorde or geval_id in per_id:
            raise MetingGeweigerdError("geval_buiten_ontwikkelset")
        label, geval = ruw.get("label"), ruw.get("geval")
        if not (
            isinstance(label, dict)
            and label.get("status") in runner.LABELSTATUSSEN
            and isinstance(geval, dict)
            and geval.get("id") == geval_id
        ):
            raise MetingGeweigerdError("ontwikkelset_ongeldig")
        try:
            invoer = _invoer_uit_geval(geval)
        except (KeyError, TypeError, ValueError):
            raise MetingGeweigerdError("ontwikkelset_ongeldig") from None
        per_id[geval_id] = Geval(geval_id, label["status"], invoer)
    if len(per_id) != AANTAL_GEVALLEN or set(per_id) != set(volgorde):
        raise MetingGeweigerdError("ontwikkelset_onvolledig")
    return [per_id[geval_id] for geval_id in volgorde]


def lees_v9_fase2() -> dict[str, dict[str, Any]]:
    """De bewaarde v9-uitkomsten van fase 2 (alleen ontwikkelgevallen)."""
    data = _lees_json(V9_RESULTAAT_PAD)
    if not (
        isinstance(data, dict)
        and data.get("fase") == "ontwikkeling"
        and data.get("manifest_sha256") == MANIFEST_V9_SHA256
    ):
        raise MetingGeweigerdError("v9_resultaat_afwijkend")
    return {g["id"]: g for g in data.get("gevallen") or []}


# --- controles vóór de eerste call ---------------------------------------------------


def controleer_keten(manifest: dict[str, Any], router: Any) -> dict[str, float]:
    """Promptversie, schemahash, router, prijzen en ketenbestanden; geeft prijzen.

    Het schema wordt zowel in het contract als in de dienstmodule getoetst:
    de dienst bindt pin en schema bij import en verstuurt die waarden.
    """
    import services.validation.int02_assessment_service as dienst
    from domain.int02 import contract
    from services.ai.base_client import response_schema_sha256

    if dienst.PROMPT_VERSION != VERWACHTE_PROMPTVERSIE:
        raise MetingGeweigerdError("promptversie_afwijkend")
    for schema, pin in (
        (contract.ANTWOORDSCHEMA, contract.ANTWOORDSCHEMA_SHA256),
        (dienst.ANTWOORDSCHEMA, dienst.ANTWOORDSCHEMA_SHA256),
    ):
        if pin != VERWACHTE_SCHEMAHASH or (
            response_schema_sha256(schema) != VERWACHTE_SCHEMAHASH
        ):
            raise MetingGeweigerdError("schemahash_afwijkend")
    identiteit = manifest["identiteit"]
    if list(router.get_model(dienst.TASK_TYPE)) != identiteit["router"]["uitkomst"]:
        raise MetingGeweigerdError("router_afwijkend")
    for pad, verwacht in identiteit["bestanden"].items():
        if _sha((REPO / pad).read_bytes()) != verwacht:
            raise MetingGeweigerdError("ketenbestand_afwijkend")
    # De runner eist dat één volle reservering in het budget past; het plafond
    # bewaakt hieronder elke call vooraf.
    router_prijzen = runner._prijzen(router, _meetlimieten(1))
    prijzen = dict(identiteit["prijzen_per_token"])
    if router_prijzen != prijzen:
        raise MetingGeweigerdError("prijzen_afwijkend")
    return prijzen


def _meetlimieten(calls: int) -> Any:
    """Limieten per call gelijk aan de kwalificatie; aantal en plafond eigen."""
    return replace(
        runner.KWALIFICATIELIMIETEN,
        max_inferentie=calls,
        max_telverzoeken=calls,
        budget_usd=KOSTENPLAFOND_USD,
        totale_looptijd_seconden=TOTALE_LOOPTIJD_SECONDEN,
    )


def _eis_herhalingen(herhalingen: int) -> None:
    if isinstance(herhalingen, bool) or not isinstance(herhalingen, int):
        raise MetingGeweigerdError("herhalingen_ongeldig")
    if not 1 <= herhalingen <= MAX_HERHALINGEN:
        raise MetingGeweigerdError("herhalingen_buiten_grens")


async def _bereid_voor(herhalingen: int) -> dict[str, Any]:
    """Offline: controles, gevallen en de opgevangen payloads (niets verstuurd)."""
    manifest = lees_manifest()
    router = runner._bouw_router()
    prijzen = controleer_keten(manifest, router)
    gevallen = lees_ontwikkelset(manifest)
    waarnemer = await runner._vang(
        router,
        runner.KWALIFICATIELIMIETEN,
        [(g.id, g.invoer) for g in gevallen],
        runner.KWALIFICATIE_PROFIEL_ID,
    )
    ijk = _ontwikkelhashes(manifest)
    hashes = {}
    for geval in gevallen:
        gemeten = runner._gevalhashes(geval.id, geval.invoer, waarnemer)
        verwacht = {k: ijk[geval.id].get(k) for k in gemeten}
        if gemeten != verwacht:
            raise MetingGeweigerdError("payload_afwijkend_van_manifest_v9")
        hashes[geval.id] = gemeten
    v9 = lees_v9_fase2()
    reservering = runner._reservering(_meetlimieten(1), prijzen)
    return {
        "manifest": manifest,
        "router": router,
        "prijzen": prijzen,
        "gevallen": gevallen,
        "hashes": hashes,
        "v9": v9,
        "reservering": reservering,
        "raming": kostenraming(gevallen, herhalingen, v9, reservering),
        "opgevangen": len(waarnemer.opgevangen),
    }


# --- kosten -----------------------------------------------------------------------


def kostenraming(
    gevallen: list[Geval],
    herhalingen: int,
    v9: dict[str, dict[str, Any]],
    reservering: float,
) -> dict[str, Any]:
    """Verwacht = gemeten v9-kosten per geval (gemiddelde waar v9 niet draaide)."""
    bekend = {
        g.id: v9[g.id]["meting"]["kosten_usd"]
        for g in gevallen
        if isinstance((v9.get(g.id) or {}).get("meting", {}).get("kosten_usd"), float)
    }
    gemiddeld = sum(bekend.values()) / len(bekend) if bekend else reservering
    per_ronde = sum(bekend.get(g.id, gemiddeld) for g in gevallen)
    calls = len(gevallen) * herhalingen
    return {
        "calls": calls,
        "verwacht_usd": per_ronde * herhalingen,
        "gemiddeld_per_call_v9_usd": gemiddeld,
        "gevallen_zonder_v9_meting": [g.id for g in gevallen if g.id not in bekend],
        "reservering_per_call_usd": reservering,
        "slechtste_geval_usd": calls * reservering,
        "plafond_usd": KOSTENPLAFOND_USD,
        "calls_binnen_plafond_bij_volle_reservering": int(
            (KOSTENPLAFOND_USD + 1e-9) // reservering
        ),
    }


def _besteding(verstuurd: int, geboekt: float, reservering: float) -> float:
    """Conservatief: een verstuurde call zonder betrouwbare boeking telt voor
    de volle reservering (zie variatiemeting C107)."""
    onzeker = verstuurd - (1 if geboekt > 0 else 0)
    return geboekt + max(onzeker, 0) * reservering


# --- uitkomst per call --------------------------------------------------------------


def kern_uit_document(document: dict[str, Any]) -> dict[str, Any]:
    """Status, kernvormen en bronfuncties uit een (bewaard) beoordelingsdocument."""
    oordeel = document.get("oordeel") or {}
    dienst = oordeel.get("dienst") or {}
    passages = [
        {
            "kernvorm": p.get("kernvorm"),
            "quote": p.get("quote"),
            "start": p.get("start"),
            "end": p.get("end"),
            "bronfuncties": [
                {"bron": b.get("bron"), "function": b.get("function")}
                for b in p.get("bronfuncties") or []
            ],
        }
        for p in oordeel.get("passages") or []
    ]
    return {
        "status": document.get("status"),
        "modelverdict": oordeel.get("verdict"),
        "modelstatus": dienst.get("modelstatus"),
        "uncertainty": oordeel.get("uncertainty"),
        "coverage": oordeel.get("coverage"),
        "afleiding": dienst.get("afleiding"),
        "omzetting": document.get("omzetting"),
        "foutcategorie": document.get("foutcategorie"),
        "foutdetail": document.get("foutdetail"),
        "heeft_oordeel": bool(oordeel),
        "passages": passages,
    }


def _callregel(
    geval: Geval,
    herhaling: int,
    call: int,
    tijdstempel: str,
    beoordeling: Any,
    meting: dict[str, Any],
    ruw: str | None,
) -> dict[str, Any]:
    document = beoordeling.document.als_dict()
    oordeel = document.get("oordeel") or {}
    status = beoordeling.status
    return {
        "soort": CALL_SOORT,
        "geval": geval.id,
        "herhaling": herhaling,
        "call": call,
        "tijdstempel": tijdstempel,
        "label": geval.label,
        **kern_uit_document(document),
        "juist": status == geval.label,
        "onterechte_pass": geval.label != "pass" and status == "pass",
        "kritieke_false_pass": geval.label == "fail" and status == "pass",
        "reden": beoordeling.reden,
        "vraag": oordeel.get("question"),
        "redenering": oordeel.get("reason"),
        "usage": meting.get("usage"),
        "kosten_usd": meting.get("kosten_usd"),
        "reservering_usd": meting.get("reservering_usd"),
        "duur_ms": meting.get("duur_ms"),
        "dienst_duur_ms": (document.get("uitvoering") or {}).get("duur_ms"),
        "gerapporteerd_model": meting.get("gerapporteerd_model"),
        "stop_reason": beoordeling.stop_reason,
        "request_id": meting.get("request_id"),
        "payload_sha256": meting.get("payload_sha256"),
        "antwoord_sha256": beoordeling.antwoord_sha256,
        "promptversie": beoordeling.promptversie,
        "contractversie": document.get("contractversie"),
        "gecachet": beoordeling.gecachet,
        "ruw_antwoord": ruw,
    }


def _foutregel(
    geval: Geval, herhaling: int, call: int, tijdstempel: str, exc: BaseException
) -> dict[str, Any]:
    """Call zonder dienstresultaat: geen inhoud, alleen het uitzonderingstype."""
    return {
        "soort": CALL_SOORT,
        "geval": geval.id,
        "herhaling": herhaling,
        "call": call,
        "tijdstempel": tijdstempel,
        "label": geval.label,
        "status": "uitzondering",
        "heeft_oordeel": False,
        "passages": [],
        "foutcategorie": "uitzondering",
        "uitzonderingstype": type(exc).__name__,
    }


def _stopreden(beoordeling: Any) -> str | None:
    """Technische fouten stoppen; een citaat- of uitvoerfout van het model niet."""
    from domain.int02.contract import FOUT_CITAAT, FOUT_UITVOER

    if beoordeling.gecachet:
        return "gecachet"
    if beoordeling.status == "error" and beoordeling.document.foutcategorie in (
        FOUT_CITAAT,
        FOUT_UITVOER,
    ):
        return None
    return runner._stopreden(beoordeling)


def _schrijf_regel(pad: Path, regel: dict[str, Any]) -> None:
    with pad.open("a", encoding="utf-8") as bestand:
        bestand.write(json.dumps(regel, ensure_ascii=False, sort_keys=True) + "\n")
        bestand.flush()
        os.fsync(bestand.fileno())


async def _meet(
    voorbereiding: dict[str, Any],
    herhalingen: int,
    api_sleutel: str,
    binnen: httpx.AsyncBaseTransport | None,
    calls_pad: Path,
) -> dict[str, Any]:
    """Ronde na ronde alle 24 gevallen; stopt bij afwijking of kostenplafond."""
    gevallen: list[Geval] = voorbereiding["gevallen"]
    plan = [
        (geval, herhaling, f"{geval.id}-h{herhaling}")
        for herhaling in range(1, herhalingen + 1)
        for geval in gevallen
    ]
    if len(plan) > MAX_CALLS:
        raise MetingGeweigerdError("calllimiet")
    limieten = _meetlimieten(len(plan))
    waarnemer = runner.Waarnemer(
        modus="live",
        # Dienstconstructie als de kwalificatie, behalve de RateLimitConfig: die
        # volgt `max_inferentie` (43 per minuut én per uur). Bij 48 calls zou
        # call 44 op de uurgrens wachten tot de deadline van 120 s verloopt.
        # Het verzoek zelf (payload, max_tokens) hangt hier niet van af.
        limieten=replace(
            runner.KWALIFICATIELIMIETEN,
            max_inferentie=max(len(plan), runner.KWALIFICATIELIMIETEN.max_inferentie),
        ),
        binnen=binnen or httpx.AsyncHTTPTransport(retries=0),
        verwacht={
            sleutel: voorbereiding["hashes"][geval.id]["payload_sha256"]
            for geval, _, sleutel in plan
        },
        prijzen=voorbereiding["prijzen"],
    )
    dienst, http = runner._bouw_dienst(
        voorbereiding["router"],
        waarnemer,
        api_sleutel,
        KWALIFICATIE_TEKST,
        runner.KWALIFICATIE_PROFIEL_ID,
    )
    reservering = voorbereiding["reservering"]
    regels: list[dict[str, Any]] = []
    besteed = 0.0
    stopreden: str | None = None
    try:
        async with asyncio.timeout(TOTALE_LOOPTIJD_SECONDEN):
            for call, (geval, herhaling, sleutel) in enumerate(plan, start=1):
                if besteed + reservering > KOSTENPLAFOND_USD:
                    stopreden = "kostenplafond"
                    break
                # Precies één inferentie en één tokenmeting per call: een
                # tweede poging binnen dezelfde call stopt vóór verzending.
                waarnemer.limieten = replace(
                    limieten, max_inferentie=call, max_telverzoeken=call
                )
                waarnemer.besteed_usd = besteed
                waarnemer.huidig = sleutel
                voor = waarnemer.inferenties
                tijdstempel = runner._nu()
                try:
                    beoordeling = await dienst.assess(
                        geval.invoer,
                        correlation_id=f"def835-variatiemeting-v9-{sleutel}",
                    )
                except Exception as exc:
                    regel = _foutregel(geval, herhaling, call, tijdstempel, exc)
                    stopreden = waarnemer.stopreden or "uitzondering"
                else:
                    regel = _callregel(
                        geval,
                        herhaling,
                        call,
                        tijdstempel,
                        beoordeling,
                        waarnemer.metingen.get(sleutel, {}),
                        waarnemer.antwoorden.get(sleutel),
                    )
                    stopreden = waarnemer.stopreden or _stopreden(beoordeling)
                besteed += _besteding(
                    waarnemer.inferenties - voor,
                    waarnemer.besteed_usd - besteed,
                    reservering,
                )
                regel["besteed_usd_conservatief"] = besteed
                _schrijf_regel(calls_pad, regel)
                regels.append(regel)
                if stopreden is not None:
                    break
    except TimeoutError:
        stopreden = waarnemer.stopreden or "totale_looptijd"
    finally:
        await http.aclose()
    return {
        "regels": regels,
        "gepland": len(plan),
        "stopreden": stopreden,
        "inferenties": waarnemer.inferenties,
        "telverzoeken": waarnemer.telverzoeken,
        "besteed": besteed,
    }


# --- samenvatting -------------------------------------------------------------------


_AFKORTING = {"not_addressed": "–"}


def _bronkort(bron: str) -> str:
    if bron == "bedoeling":
        return "bed"
    return bron.removeprefix("bron/")


def bronfunctiekaart(kern: dict[str, Any]) -> dict[str, str]:
    """Per grondbron de functies over de passages, in passagevolgorde."""
    kaart: dict[str, list[str]] = {}
    for passage in kern.get("passages") or []:
        for bf in passage.get("bronfuncties") or []:
            kaart.setdefault(bf["bron"], []).append(str(bf["function"]))
    return {bron: "|".join(functies) for bron, functies in kaart.items()}


def _wisselende_bronnen(kernen: dict[str, dict[str, Any]]) -> dict[str, dict[str, str]]:
    """Per bron de waarde per run, alleen voor bronnen die wisselen."""
    kaarten = {
        run: bronfunctiekaart(kern)
        for run, kern in kernen.items()
        if kern.get("heeft_oordeel")
    }
    if len(kaarten) < 2:
        return {}
    bronnen = sorted({b for kaart in kaarten.values() for b in kaart})
    return {
        bron: {run: kaart.get(bron, "–") for run, kaart in kaarten.items()}
        for bron in bronnen
        if len({kaart.get(bron, "–") for kaart in kaarten.values()}) > 1
    }


def _functiekort(waarde: str) -> str:
    return "·".join(_AFKORTING.get(f, f) for f in waarde.split("|"))


def maak_samenvatting(
    gevallen: list[tuple[str, str]],
    runs: dict[str, dict[str, dict[str, Any]]],
    meta: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    """Samenvatting (JSON en markdown) over v9-fase 2 en de herhalingen.

    `gevallen`: (id, label) in vaste volgorde. `runs`: per run (bijvoorbeeld
    `v9-fase2`, `h1`, `h2`) per geval-ID de kern uit `kern_uit_document`;
    een geval dat in een run niet draaide, ontbreekt daar.
    """
    runnamen = list(runs)
    per_geval = []
    for geval_id, label in gevallen:
        kernen = {run: runs[run][geval_id] for run in runnamen if geval_id in runs[run]}
        statussen = {run: k.get("status") for run, k in kernen.items()}
        wisselend = _wisselende_bronnen(kernen)
        per_geval.append(
            {
                "geval": geval_id,
                "label": label,
                "statussen": statussen,
                "stabiel": (
                    len(set(statussen.values())) == 1 if len(statussen) > 1 else None
                ),
                "wisselende_bronfuncties": wisselend,
            }
        )
    per_run = {}
    for run in runnamen:
        uitkomsten = [
            (g["geval"], g["label"], g["statussen"][run])
            for g in per_geval
            if run in g["statussen"]
        ]
        per_run[run] = {
            "gedraaid": len(uitkomsten),
            "juist": sum(label == status for _, label, status in uitkomsten),
            "onterechte_passes": [
                i
                for i, label, status in uitkomsten
                if label != "pass" and status == "pass"
            ],
            "kritieke_false_passes": [
                i
                for i, label, status in uitkomsten
                if label == "fail" and status == "pass"
            ],
        }
    statuswissel = [g["geval"] for g in per_geval if g["stabiel"] is False]
    bronwissel = [g["geval"] for g in per_geval if g["wisselende_bronfuncties"]]
    data = {
        "soort": SAMENVATTING_SOORT,
        "claim": CLAIM,
        **meta,
        "runs": runnamen,
        "per_run": per_run,
        "gevallen_met_wisselende_status": statuswissel,
        "gevallen_met_wisselende_bronfuncties": bronwissel,
        "per_geval": per_geval,
    }
    return data, _markdown(data)


def _markdown(data: dict[str, Any]) -> str:
    runs = data["runs"]
    regels = [
        "# INT-02 O2 — variatiemeting v9, samenvatting",
        "",
        f"Automatisch opgesteld door `variatiemeting_v9.py` ({data.get('modus')}). "
        "Buiten het kwalificatieprotocol (besluit 21): geen kwalificatie, geen "
        "herhaling van een kwalificatiefase, geen DEF-815-claim. De ontwikkelgevallen "
        "zijn een consistentietoets (7A).",
        "",
        f"- Calls: {data.get('inferenties')} van {data.get('gepland')} gepland; "
        f"stopreden: {data.get('stopreden') or '—'}.",
        f"- Kosten (conservatief, prijzen manifest v9): "
        f"US${data.get('kosten_usd_conservatief', 0.0):.5f}; "
        f"plafond US${data.get('kostenplafond_usd', KOSTENPLAFOND_USD):.2f}.",
        "",
        "## Totaal",
        "",
        "| | " + " | ".join(runs) + " |",
        "|---|" + "---|" * len(runs),
    ]
    per_run = data["per_run"]

    def rij(naam: str, waarde: Callable[[dict[str, Any]], str]) -> str:
        return f"| {naam} | " + " | ".join(waarde(per_run[r]) for r in runs) + " |"

    def lijst(ids: list[str]) -> str:
        return f"{len(ids)} ({', '.join(ids)})" if ids else "0"

    regels += [
        rij("gedraaid", lambda p: str(p["gedraaid"])),
        rij("juist", lambda p: f"{p['juist']}/{p['gedraaid']}"),
        rij("onterechte passes", lambda p: lijst(p["onterechte_passes"])),
        rij("kritieke false passes", lambda p: lijst(p["kritieke_false_passes"])),
        "",
        f"- Gevallen met wisselende status: "
        f"{lijst(data['gevallen_met_wisselende_status'])}.",
        f"- Gevallen met wisselende bronfuncties: "
        f"{lijst(data['gevallen_met_wisselende_bronfuncties'])}.",
        "",
        "## Per geval",
        "",
        "Bronfuncties per bron in passagevolgorde (`·` scheidt passages, `–` = "
        "`not_addressed`); `bed` = bedoeling. Een status met ✘ wijkt af van het label.",
        "",
        "| Geval | Label | "
        + " | ".join(runs)
        + " | Stabiel | Wisselende bronfuncties |",
        "|---|---|" + "---|" * len(runs) + "---|---|",
    ]
    for g in data["per_geval"]:
        cellen = []
        for run in runs:
            status = g["statussen"].get(run)
            if status is None:
                cellen.append("niet gedraaid")
            else:
                cellen.append(f"`{status}`" + ("" if status == g["label"] else " ✘"))
        stabiel = {True: "ja", False: "**nee**", None: "—"}[g["stabiel"]]
        wissel = "; ".join(
            f"{_bronkort(bron)}: "
            + " / ".join(f"{run} {_functiekort(w)}" for run, w in waarden.items())
            for bron, waarden in g["wisselende_bronfuncties"].items()
        )
        regels.append(
            f"| {g['geval']} | {g['label']} | "
            + " | ".join(cellen)
            + f" | {stabiel} | {wissel or '—'} |"
        )
    return "\n".join(regels) + "\n"


def _runs_voor_samenvatting(
    v9: dict[str, dict[str, Any]], regels: list[dict[str, Any]]
) -> dict[str, dict[str, dict[str, Any]]]:
    runs: dict[str, dict[str, dict[str, Any]]] = {
        V9_RUN: {i: kern_uit_document(g["document"]) for i, g in v9.items()}
    }
    for regel in regels:
        runs.setdefault(f"h{regel['herhaling']}", {})[regel["geval"]] = regel
    return runs


# --- uitvoering ---------------------------------------------------------------------


def _git(*args: str) -> str | None:
    try:
        uit = subprocess.run(
            ["git", *args], cwd=REPO, capture_output=True, text=True, check=True
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return uit.stdout.strip()


def _herkomst(
    voorbereiding: dict[str, Any], modus: str, herhalingen: int
) -> dict[str, Any]:
    import anthropic

    from domain.int02.contract import CONTRACTVERSIE
    from services.validation.int02_assessment_service import PROMPT_VERSION

    gewijzigd = _git("status", "--porcelain", "--", *runner.KETENBESTANDEN)
    return {
        "soort": HERKOMST_SOORT,
        "claim": CLAIM,
        "aangemaakt": runner._nu(),
        "modus": modus,
        "herhalingen": herhalingen,
        "git_head": _git("rev-parse", "HEAD"),
        "ketenbestanden_lokaal_gewijzigd": (
            gewijzigd.splitlines() if gewijzigd is not None else None
        ),
        "script_sha256": _sha(SCRIPT_PAD.read_bytes()),
        "manifest_v9_sha256": MANIFEST_V9_SHA256,
        "ontwikkelset_sha256": _sha(_lees_bytes(ONTWIKKELING_PAD)),
        "v9_resultaat_sha256": _sha(_lees_bytes(V9_RESULTAAT_PAD)),
        "profiel_id": runner.KWALIFICATIE_PROFIEL_ID,
        "provider": runner.PROVIDER,
        "model": runner.MODEL,
        "promptversie": PROMPT_VERSION,
        "contractversie": CONTRACTVERSIE,
        "schemahash": VERWACHTE_SCHEMAHASH,
        "limieten_per_call": asdict(_meetlimieten(1)),
        "kostenplafond_usd": KOSTENPLAFOND_USD,
        "max_calls": MAX_CALLS,
        "prijzen_per_token": voorbereiding["prijzen"],
        "raming": voorbereiding["raming"],
        "gevallen": [
            {**voorbereiding["hashes"][g.id], "fase": "ontwikkeling"}
            for g in voorbereiding["gevallen"]
        ],
        "versies": {
            "anthropic": anthropic.__version__,
            "httpx": httpx.__version__,
            "manifest_v9": voorbereiding["manifest"]["identiteit"]["versies"],
        },
    }


def lees_sleutel_uit_omgeving() -> str | None:
    """Alleen `ANTHROPIC_API_KEY` uit de omgeving; nooit uit een `.env`."""
    sleutel = os.environ.get("ANTHROPIC_API_KEY")
    return sleutel if runner._gevuld(sleutel) else None


def _dotenv_uit() -> bool:
    waarde = os.environ.get("DEFINITIE_DISABLE_DOTENV", "")
    return waarde.strip().lower() in WAARHEIDSWAARDEN


def _log_overzicht(voorbereiding: dict[str, Any], herhalingen: int) -> None:
    """Droge run: wat er gestuurd zou worden en de kostenraming."""
    v9 = voorbereiding["v9"]
    logger.info(
        "Droge run: niets verstuurd, geen sleutel gelezen. Ketencontrole tegen "
        "manifest v9 geslaagd (prompt %s, schema %s…, %d ketenbestanden gelijk).",
        VERWACHTE_PROMPTVERSIE,
        VERWACHTE_SCHEMAHASH[:8],
        len(voorbereiding["manifest"]["identiteit"]["bestanden"]),
    )
    logger.info(
        "%-5s %-16s %-16s %6s %-12s %s",
        "geval",
        "label",
        "v9 fase 2",
        "bytes",
        "payload",
        "calls",
    )
    for geval in voorbereiding["gevallen"]:
        h = voorbereiding["hashes"][geval.id]
        logger.info(
            "%-5s %-16s %-16s %6d %-12s %d x (gelijk aan manifest v9)",
            geval.id,
            geval.label,
            (v9.get(geval.id) or {}).get("status", "niet gedraaid"),
            h["payload_bytes"],
            h["payload_sha256"][:8] + "…",
            herhalingen,
        )
    r = voorbereiding["raming"]
    logger.info(
        "Calls: %d (%d gevallen x %d herhalingen; maximum %d).",
        r["calls"],
        len(voorbereiding["gevallen"]),
        herhalingen,
        MAX_CALLS,
    )
    logger.info(
        "Raming verwacht: US$%.2f (v9-kosten per geval; gemiddeld US$%.5f per "
        "call voor %d gevallen zonder v9-meting: %s).",
        r["verwacht_usd"],
        r["gemiddeld_per_call_v9_usd"],
        len(r["gevallen_zonder_v9_meting"]),
        ", ".join(r["gevallen_zonder_v9_meting"]) or "—",
    )
    logger.info(
        "Slechtste geval zonder plafond: US$%.2f (%d x volle reservering "
        "US$%.2f). Plafond US$%.2f: bij volle reservering per call stopt de "
        "meting na %d calls.",
        r["slechtste_geval_usd"],
        r["calls"],
        r["reservering_per_call_usd"],
        r["plafond_usd"],
        r["calls_binnen_plafond_bij_volle_reservering"],
    )


async def voer_uit(
    uitvoer: Path | None,
    *,
    herhalingen: int = STANDAARD_HERHALINGEN,
    live: bool = False,
    sleutel: Callable[[], str | None] | None = None,
    binnen: httpx.AsyncBaseTransport | None = None,
) -> dict[str, Any]:
    """Droge run (standaard) of live meting; geeft de samenvatting terug."""
    _eis_herhalingen(herhalingen)
    if AANTAL_GEVALLEN * herhalingen > MAX_CALLS:
        raise MetingGeweigerdError("calllimiet")
    uitvoer = Path(uitvoer).resolve() if uitvoer is not None else None
    if live and uitvoer is None:
        raise MetingGeweigerdError("uitvoermap_ontbreekt")
    if uitvoer is not None and uitvoer.exists():
        raise MetingGeweigerdError("uitvoermap_bestaat")
    api_sleutel = None
    if live:
        # Vóór de keten iets laadt: de sleutel komt uit de omgeving, niet uit
        # een .env die een ConfigManager later zou kunnen aanvullen.
        if not _dotenv_uit():
            raise MetingGeweigerdError("dotenv_niet_uitgeschakeld")
        api_sleutel = (sleutel or lees_sleutel_uit_omgeving)()
        if not runner._gevuld(api_sleutel):
            raise MetingGeweigerdError("sleutel_ontbreekt")
    modus = "live" if live else "dry-run"
    with runner._proefomgeving():
        voorbereiding = await _bereid_voor(herhalingen)
        if not live:
            _log_overzicht(voorbereiding, herhalingen)
            return {
                "soort": SAMENVATTING_SOORT,
                "modus": modus,
                "herhalingen": herhalingen,
                "inferenties": 0,
                "telverzoeken": 0,
                "opgevangen_zonder_verzending": voorbereiding["opgevangen"],
                "stopreden": None,
                "raming": voorbereiding["raming"],
            }
        assert uitvoer is not None
        try:
            uitvoer.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            raise MetingGeweigerdError("uitvoermap_bestaat") from None
        runner._schrijf_nieuw(
            uitvoer / "herkomst.json", _herkomst(voorbereiding, modus, herhalingen)
        )
        uitkomst = await _meet(
            voorbereiding,
            herhalingen,
            str(api_sleutel),
            binnen,
            uitvoer / "calls.jsonl",
        )
    gevallen = [(g.id, g.label) for g in voorbereiding["gevallen"]]
    data, markdown = maak_samenvatting(
        gevallen,
        _runs_voor_samenvatting(voorbereiding["v9"], uitkomst["regels"]),
        {
            "modus": modus,
            "afgerond": runner._nu(),
            "herhalingen": herhalingen,
            "gepland": uitkomst["gepland"],
            "inferenties": uitkomst["inferenties"],
            "telverzoeken": uitkomst["telverzoeken"],
            "stopreden": uitkomst["stopreden"],
            "kosten_usd_conservatief": uitkomst["besteed"],
            "kostenplafond_usd": KOSTENPLAFOND_USD,
        },
    )
    runner._schrijf_nieuw(uitvoer / "samenvatting.json", data)
    with (uitvoer / "samenvatting.md").open("x", encoding="utf-8") as bestand:
        bestand.write(markdown)
    return data


def _herhalingen(waarde: str) -> int:
    try:
        aantal = int(waarde)
    except ValueError:
        msg = "geen geheel getal"
        raise argparse.ArgumentTypeError(msg) from None
    if not 1 <= aantal <= MAX_HERHALINGEN:
        msg = f"herhalingen moet tussen 1 en {MAX_HERHALINGEN} liggen (max {MAX_CALLS} calls)"
        raise argparse.ArgumentTypeError(msg)
    return aantal


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--herhalingen",
        type=_herhalingen,
        default=STANDAARD_HERHALINGEN,
        help=f"herhalingen van de 24 gevallen (1-{MAX_HERHALINGEN}, standaard "
        f"{STANDAARD_HERHALINGEN})",
    )
    parser.add_argument(
        "--uitvoer", type=Path, help="nieuwe uitvoermap (verplicht bij --live)"
    )
    parser.add_argument("--live", action="store_true", help="echte verzending")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(message)s")
    logger.setLevel(logging.INFO)
    start = time.monotonic()
    try:
        data = asyncio.run(
            voer_uit(args.uitvoer, herhalingen=args.herhalingen, live=args.live)
        )
    except (MetingGeweigerdError, runner.ProefGeweigerdError) as fout:
        logger.error("geweigerd: %s", fout.reden)
        return 2
    if data["modus"] == "live":
        logger.info(
            "live: %d/%d calls, stopreden %s, kosten (conservatief) $%.6f, %.1f s",
            data["inferenties"],
            data["gepland"],
            data["stopreden"],
            data["kosten_usd_conservatief"],
            time.monotonic() - start,
        )
    else:
        logger.info("dry-run afgerond in %.1f s", time.monotonic() - start)
    return 0 if data["stopreden"] is None else 3


if __name__ == "__main__":
    sys.exit(main())
