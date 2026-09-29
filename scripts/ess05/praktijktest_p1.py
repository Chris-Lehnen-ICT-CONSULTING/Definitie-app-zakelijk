"""DEF-768 P1 — rooktest van de ESS-05-bewijsregelroute op drie echte definities.

Besluit Chris (optie A, logs/def768/echte-test-v1/budgetbesluit-p1-v1.json):
records 277 (verdachte), 365 (authenticatie) en 278 (raadsman) gaan elk exact
eenmaal door de nieuwe ESS-05-route zoals de app die gebruikt:

- `ValidationOrchestratorV2._enrich_context_with_definition_fields` en
  `_beoordeel_onderscheid` (repository-buren, bevestigingsbeleid B) →
  `Ess05BewijsregelService.voor_app(...).assess` (interpretatie + lokale
  controles) — alleen ESS-05, geen ESS-03/INT-03/CON-02/INT-02;
- `DistinctionAssessmentEvaluator` → uitkomst en de regels die de UI toont
  (`ui.components.validation_view`).

Veiligheid:
- De echte database wordt alleen gelezen (bytekopie) en nooit geopend; alles
  draait op de kopie in de uitvoermap. sha256 van het origineel vóór en na.
- Al het modelverkeer loopt door de bestaande transportweg, omsloten door een
  harde teller: max 15 aanroepen, geen retry, stop bij het plafond of bij een
  technische fout. Per aanroep: volgnummer, record, soort, promptversie,
  prompt-sha, ruwe respons, tokens, kosten (echt) en duur.
- Echte aanroepen alleen met `--echt` én het gepinde budgetbesluit; anders
  weigert het script vóór er een client bestaat. Zonder `--echt` (`--droog`)
  draait een stubmodel onder een netwerkblokkade.
- Een bestaande uitvoermap wordt geweigerd: geen tweede poging over uitvoer.

Herhaling (besluit Chris 29-09, na de robuustheidsronde): één echte run naar
`echt-p1-v2` op het restbudget van hetzelfde besluit. Aanroepen en kosten van
de echte v1-run komen uit diens gepinde samenvatting (sha256 en onderlinge
consistentie gecontroleerd); de teller krijgt 15 min het v1-verbruik en het
kostenplafond USD 1,00 min de v1-kosten. Een echte run naar een andere map,
of zonder die samenvatting, wordt geweigerd.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Zet onder meer AI_SDK_MAX_RETRIES=0 vóór de app-imports; levert _laad_env en
# geen_netwerk.
import run_ess05_proef as rp

ECHTE_DB = Path("/Users/chrislehnen/Projecten/Definitie-app/data/definities.db")
RECORDS = (277, 365, 278)
BESLUIT = PROJECT_ROOT / "logs/def768/echte-test-v1/budgetbesluit-p1-v1.json"
BESLUIT_SHA256 = "5b2c128130b012fb1480b2a351cf3baefca5a977090f17d749894bf4239ab99d"
UITVOERBASIS = PROJECT_ROOT / "logs/def768/echte-test-v1"
V1_SAMENVATTING = UITVOERBASIS / "echt-p1-v1" / "samenvatting.json"
V1_SAMENVATTING_SHA256 = (
    "203eafc69fdd54d4acf67972e589100d27d347c404839ee43835f11862d20b9a"
)
HERHAAL_UITMAP = UITVOERBASIS / "echt-p1-v2"
REGEL = PROJECT_ROOT / "src/toetsregels/regels/ESS-05.json"

MAX_AANROEPEN = 15
#: claude-opus-5: USD 5 / 25 per miljoen tokens = 5000 / 25000 n$ per token.
TARIEF_INVOER_NUSD = 5_000
TARIEF_UITVOER_NUSD = 25_000
PLAFOND_NUSD = 1_000_000_000  # USD 1,00
STAPMARGE_NUSD = 150_000_000  # USD 0,15 ruimte voor de volgende aanroep


class PlafondstopError(RuntimeError):
    """De harde teller staat geen (verdere) modelaanroep toe."""


def sha256_bestand(pad: Path) -> str:
    h = hashlib.sha256()
    with pad.open("rb") as f:
        for blok in iter(lambda: f.read(1 << 20), b""):
            h.update(blok)
    return h.hexdigest()


def _soorten() -> dict[str, tuple[str, str]]:
    from services.validation.ess05_bewijsregel_service import Ess05BewijsregelService
    from services.validation.ess05_local_verification_service import (
        Ess05LocalVerificationService as Lokaal,
    )

    return {
        Ess05BewijsregelService.TASK_TYPE: (
            "interpretatie",
            Ess05BewijsregelService.PROMPT_VERSION,
        ),
        Lokaal.TASK_TYPE: ("controle", Lokaal.PROMPT_VERSION),
    }


# --- harde teller --------------------------------------------------------------


@dataclass
class Teller:
    """Telt elke ESS-05-modelaanroep; weigert vóór de 16e, bij retry of na een fout."""

    maximum: int = MAX_AANROEPEN
    eis_kosten: bool = False
    plafond_nusd: int = PLAFOND_NUSD
    geheimen: tuple[str, ...] = ()
    aanroepen: list[dict[str, Any]] = field(default_factory=list)
    record: int | None = None
    gestopt: str | None = None
    huidig: dict[str, Any] | None = None

    @property
    def kosten_nusd(self) -> int:
        return sum(int(a.get("kosten_nusd") or 0) for a in self.aanroepen)

    def stop(self, reden: str) -> PlafondstopError:
        if self.gestopt is None:
            self.gestopt = reden
        return PlafondstopError(reden)

    def scrub(self, tekst: str) -> str:
        for geheim in self.geheimen:
            if geheim:
                tekst = tekst.replace(geheim, "[GEHEIM]")
        return tekst

    def _toelating(self, task_type: str) -> tuple[str, str]:
        if self.gestopt is not None:
            raise PlafondstopError(f"teller gestopt: {self.gestopt}")
        if len(self.aanroepen) >= self.maximum:
            raise self.stop(f"plafond van {self.maximum} modelaanroepen bereikt")
        if self.eis_kosten and self.kosten_nusd + STAPMARGE_NUSD > self.plafond_nusd:
            raise self.stop(
                f"lokaal kostenplafond USD {self.plafond_nusd / 1e9:.6f}"
                " (met stapmarge 0,15)"
            )
        soort = _soorten().get(task_type)
        if soort is None:
            raise self.stop(f"onverwachte taak {task_type!r}: alleen ESS-05 toegestaan")
        return soort

    @contextlib.contextmanager
    def grens(self, task_type: str, prompt_sha256: str) -> Iterator[dict[str, Any]]:
        """De ESS-05-aanroepgrens (`aanroepgrens`): één teleenheid per aanroep."""
        soort, versie = self._toelating(task_type)
        entry: dict[str, Any] = {
            "volgnummer": len(self.aanroepen) + 1,
            "record": self.record,
            "soort": soort,
            "task_type": task_type,
            "promptversie": versie,
            "prompt_sha256": prompt_sha256,
            "provider_aanroepen": 0,
            "sdk_aanroepen": 0,
            "ruwe_respons": None,
            "tokens_used": None,
            "invoertokens": None,
            "uitvoertokens": None,
            "kosten_nusd": None,
            "fout": None,
        }
        self.aanroepen.append(entry)
        self.huidig = entry
        start = time.perf_counter()
        try:
            yield entry
        except BaseException as exc:
            entry["fout"] = self.scrub(f"{type(exc).__name__}: {exc}")
            self.stop(f"technische fout in aanroep {entry['volgnummer']}")
            raise
        finally:
            entry["duur_s"] = round(time.perf_counter() - start, 3)
            self.huidig = None
        if self.eis_kosten and entry["kosten_nusd"] is None:
            self.stop(f"kosten van aanroep {entry['volgnummer']} onbekend")

    def actief(self, laag: str) -> dict[str, Any]:
        if self.huidig is None:
            raise self.stop(f"{laag}-aanroep buiten de ESS-05-teller")
        return self.huidig


class TellendeClient:
    """AsyncAIClient-proxy: precies één poging per teleenheid, SDK-retries 0."""

    def __init__(self, echt: Any, teller: Teller) -> None:
        self._echt = echt
        self._teller = teller

    def __getattr__(self, naam: str) -> Any:
        return getattr(self._echt, naam)

    async def chat_completion(self, messages: Any, model: str, **kwargs: Any) -> Any:
        entry = self._teller.actief("client")
        if kwargs.get("max_retries") != 0:
            msg = f"max_retries moet 0 zijn, kreeg {kwargs.get('max_retries')!r}"
            raise self._teller.stop(msg)
        if entry["provider_aanroepen"] >= 1:
            msg = f"tweede poging binnen aanroep {entry['volgnummer']}: geen retry"
            raise self._teller.stop(msg)
        entry["provider_aanroepen"] += 1
        entry["model"] = model
        antwoord = await self._echt.chat_completion(messages, model, **kwargs)
        entry["ruwe_respons"] = getattr(antwoord, "text", None)
        entry["tokens_used"] = getattr(antwoord, "tokens_used", None)
        entry["stop_reason"] = getattr(antwoord, "stop_reason", None)
        entry["model_gemeld"] = getattr(antwoord, "model", None)
        return antwoord


def installeer_sdk_teller(klasse: Any, teller: Teller) -> Callable[[], None]:
    """Bewaak `klasse.create` (Anthropic `AsyncMessages`): één SDK-aanroep per
    teleenheid, `max_retries == 0` op de SDK-client, usage en kosten vastgelegd.
    Geeft een herstelfunctie terug."""
    origineel = klasse.create

    async def create(self: Any, *args: Any, **kwargs: Any) -> Any:
        entry = teller.actief("SDK")
        retries = getattr(getattr(self, "_client", None), "max_retries", None)
        if retries != 0:
            raise teller.stop(f"SDK-client met max_retries={retries!r} geweigerd")
        if entry["sdk_aanroepen"] >= 1:
            raise teller.stop(f"tweede SDK-aanroep in aanroep {entry['volgnummer']}")
        entry["sdk_aanroepen"] += 1
        resp = await origineel(self, *args, **kwargs)
        usage = getattr(resp, "usage", None)
        if usage is not None:
            invoer = int(getattr(usage, "input_tokens", 0) or 0)
            uitvoer = int(getattr(usage, "output_tokens", 0) or 0)
            entry["invoertokens"], entry["uitvoertokens"] = invoer, uitvoer
            entry["kosten_nusd"] = (
                invoer * TARIEF_INVOER_NUSD + uitvoer * TARIEF_UITVOER_NUSD
            )
        return resp

    klasse.create = create
    return lambda: setattr(klasse, "create", origineel)


# --- stubmodel (droog) ---------------------------------------------------------

_PAKKETHASH = re.compile(r'<controlepakket packet_hash="([0-9a-f]{64})">')
_DEFINITIE = re.compile(r'<materiaal id="definition"[^>]*>(.*?)</materiaal>', re.S)
_BUUR_ID = re.compile(r"^- (.+?): ", re.M)


def _stubinterpretatie(user: str) -> dict[str, Any]:
    """Een schema-vormige interpretatie: kern in twee citaten, alles onbesproken.

    Alleen om de keten te laten lopen; zegt niets over de echte uitkomst. De
    splitsing behoudt de letterlijke witruimte (citaten moeten exact zijn).
    """
    from domain.ess05 import app_bewijsregels as app, bewijsregels as br

    gevonden = _DEFINITIE.search(user)
    definitie = str(app.ontsnap(gevonden.group(1))).strip() if gevonden else ""
    grens = definitie.find(" ", len(definitie) // 2)
    grens = grens if grens > 0 else len(definitie)
    kop, staart = definitie[:grens].strip(), definitie[grens:].strip()
    kopdeel = user.split("Materiaal (gegevens", 1)[0]
    onderwerpen = ["doel", *_BUUR_ID.findall(kopdeel)]
    return {
        "schema_version": br.INTERPRETATIESCHEMA,
        "kern": {
            "bovenbegrip": kop,
            "kenmerken": [
                {"id": "K1", "kenmerk": "stub", "waarde": staart, "citaat": staart}
            ],
        },
        "buiten_kern": [],
        "buurgroepen": [],
        "buiten_bereik": [],
        "antwoorden": [
            {
                "kenmerk_id": "K1",
                "onderwerp": onderwerp,
                "toestand": "onbesproken",
                "voorwaarden": [],
                "context": "algemeen",
                "citaten": [],
            }
            for onderwerp in onderwerpen
        ],
    }


def _stubcontrole(user: str) -> dict[str, Any]:
    from domain.ess05.lokale_controle import CONTROLE_ITEM, LOKAAL_VERIFICATIESCHEMA

    gevonden = _PAKKETHASH.search(user)
    return {
        "schema_version": LOKAAL_VERIFICATIESCHEMA,
        "packet_hash": gevonden.group(1) if gevonden else "",
        "checks": [{"item": CONTROLE_ITEM, "outcome": "supported", "finding": "stub"}],
    }


class StubClient:
    """Providerclient zonder netwerk: interpretatie of controle op de systeemprompt."""

    provider_name = "stub"

    async def chat_completion(self, messages: Any, model: str, **_: Any) -> Any:
        from services.ai.base_client import ChatResponse
        from services.validation.ess05_bewijsregel_service import (
            interpretatiesysteemprompt,
        )

        system = next((m.content for m in messages if m.role == "system"), "")
        user = next((m.content for m in messages if m.role == "user"), "")
        inhoud = (
            _stubinterpretatie(user)
            if system == interpretatiesysteemprompt()
            else _stubcontrole(user)
        )
        return ChatResponse(
            text=json.dumps(inhoud, ensure_ascii=False),
            tokens_used=0,
            model=f"stub-{model}",
            stop_reason="end_turn",
        )


# --- besluit, database, omgeving -----------------------------------------------


def controleer_besluit(
    pad: Path = BESLUIT, verwacht: str = BESLUIT_SHA256
) -> dict[str, Any]:
    """Het gepinde budgetbesluit, of SystemExit vóór er een client bestaat."""
    if not Path(pad).is_file():
        msg = f"budgetbesluit ontbreekt: {pad}; geen modelaanroep"
        raise SystemExit(msg)
    werkelijk = sha256_bestand(Path(pad))
    if werkelijk != verwacht:
        msg = f"budgetbesluit wijkt af (sha256 {werkelijk} ≠ gepind {verwacht})"
        raise SystemExit(msg)
    besluit = json.loads(Path(pad).read_text(encoding="utf-8"))
    eisen = {
        "extra_modelaanroepen_max": MAX_AANROEPEN,
        "records": list(RECORDS),
        "reserve": 0,
        "retry": False,
        "cache": False,
        "lokaal_kostenplafond_usd": "1.00",
    }
    for sleutel, waarde in eisen.items():
        if besluit.get(sleutel) != waarde:
            msg = f"budgetbesluit: {sleutel}={besluit.get(sleutel)!r}, verwacht {waarde!r}"
            raise SystemExit(msg)
    return besluit


@dataclass(frozen=True)
class Restbudget:
    """Wat na de echte v1-run van het besluit over is."""

    aanroepen: int
    kosten_nusd: int
    bron: str
    bron_sha256: str

    def als_dict(self) -> dict[str, Any]:
        return {
            "aanroepen": self.aanroepen,
            "kosten_nusd": self.kosten_nusd,
            "bron": self.bron,
            "bron_sha256": self.bron_sha256,
        }


def restbudget(
    pad: Path = V1_SAMENVATTING, verwacht: str = V1_SAMENVATTING_SHA256
) -> Restbudget:
    """Restbudget uit de gepinde v1-samenvatting, of SystemExit bij elke twijfel."""
    if not Path(pad).is_file():
        msg = f"v1-samenvatting ontbreekt: {pad}; restbudget onbekend"
        raise SystemExit(msg)
    werkelijk = sha256_bestand(Path(pad))
    if werkelijk != verwacht:
        msg = f"v1-samenvatting wijkt af (sha256 {werkelijk} ≠ gepind {verwacht})"
        raise SystemExit(msg)
    s = json.loads(Path(pad).read_text(encoding="utf-8"))
    teller = s.get("teller") or {}
    lijst = s.get("aanroepen") or []
    kosten = teller.get("kosten_nusd")
    eisen = [
        (s.get("modus") == "echt", "modus is niet echt"),
        (s.get("budgetbesluit_sha256") == BESLUIT_SHA256, "ander budgetbesluit"),
        (s.get("database_ongewijzigd") is True, "database niet ongewijzigd"),
        (
            [r.get("record_id") for r in s.get("records") or []] == list(RECORDS),
            "andere records",
        ),
        (teller.get("maximum") == MAX_AANROEPEN, "ander teller-maximum"),
        (teller.get("aanroepen") == len(lijst), "teller-aanroepen ≠ aanroepenlijst"),
        (
            all(a.get("sdk_aanroepen") == 1 for a in lijst),
            "sdk_aanroepen ≠ 1 (retry of ontbrekend)",
        ),
        (
            isinstance(kosten, int)
            and kosten == sum(int(a.get("kosten_nusd") or 0) for a in lijst),
            "teller-kosten ≠ som van de aanroepkosten",
        ),
    ]
    for ok, reden in eisen:
        if not ok:
            msg = f"v1-samenvatting onbruikbaar voor het restbudget: {reden}"
            raise SystemExit(msg)
    rest = Restbudget(
        aanroepen=MAX_AANROEPEN - len(lijst),
        kosten_nusd=PLAFOND_NUSD - kosten,
        bron=str(pad),
        bron_sha256=werkelijk,
    )
    if rest.aanroepen <= 0 or rest.kosten_nusd <= STAPMARGE_NUSD:
        msg = f"geen restbudget over: {rest.aanroepen} aanroepen, {rest.kosten_nusd} n$"
        raise SystemExit(msg)
    return rest


def controleer_bijbestanden(bron: Path) -> None:
    """Weiger een WAL met frames: dan staat niet alles in het hoofdbestand.

    Een lege -wal (en de bijbehorende -shm) blijft achter na een read-only
    opening van een WAL-database; zonder frames is het hoofdbestand volledig.
    """
    wal = Path(f"{bron}-wal")
    if wal.exists() and wal.stat().st_size > 0:
        msg = f"{wal} bevat frames: bytekopie niet consistent, geweigerd"
        raise SystemExit(msg)


def kopieer_database(bron: Path, doel: Path) -> str:
    """Bytekopie van de database (origineel alleen gelezen); geeft de sha256."""
    controleer_bijbestanden(bron)
    voor = sha256_bestand(bron)
    doel.parent.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(bron, doel)
    controleer_bijbestanden(bron)
    if sha256_bestand(doel) != voor or sha256_bestand(bron) != voor:
        msg = "kopie wijkt af van het origineel"
        raise SystemExit(msg)
    return voor


def sleutel_aanwezig() -> tuple[str, bool, str]:
    """(.env-herkomst, sleutel aanwezig, sleutelwaarde) — de waarde wordt nooit getoond."""
    from config.config_manager import get_config_manager

    herkomst = rp._laad_env()
    config = get_config_manager()
    sleutel = config.api.anthropic_api_key or ""
    if config.api.ai_provider != "anthropic":
        msg = f"provider is {config.api.ai_provider!r}, verwacht 'anthropic'"
        raise SystemExit(msg)
    return herkomst, bool(sleutel), sleutel


def echte_client(teller: Teller) -> tuple[Any, Callable[[], None]]:
    """De echte Anthropic-client achter de teller (alleen na het besluit)."""
    import anthropic.resources.messages as sdk_messages

    from services.ai import create_ai_client

    _, aanwezig, sleutel = sleutel_aanwezig()
    if not aanwezig:
        msg = "geen API-sleutel in omgeving/.env; geen aanroep gedaan"
        raise SystemExit(msg)
    teller.geheimen = (sleutel,)
    herstel = installeer_sdk_teller(sdk_messages.AsyncMessages, teller)
    client = create_ai_client(provider="anthropic", api_key=sleutel, timeout=60.0)
    return TellendeClient(client, teller), herstel


# --- de app-route per record ---------------------------------------------------


def bouw_route(db: Path, provider_client: Any) -> tuple[Any, Any, Any]:
    """(orchestrator, repository, validatieservice) zoals de app ze bedraadt."""
    from services.ai.model_router import ModelRouter
    from services.ai_service_v2 import AIServiceV2
    from services.definition_repository import DefinitionRepository
    from services.orchestrators.validation_orchestrator_v2 import (
        ValidationOrchestratorV2,
    )
    from services.validation.ess05_bewijsregel_service import Ess05BewijsregelService
    from services.validation.modular_validation_service import (
        ModularValidationService,
    )
    from toetsregels.manager import get_toetsregel_manager

    router = ModelRouter.from_config()
    ai = AIServiceV2(use_cache=False, ai_client=provider_client, model_router=router)
    repo = DefinitionRepository(str(db))
    dienst = Ess05BewijsregelService.voor_app(ai, model_router=router)
    validatie = ModularValidationService(get_toetsregel_manager(), repository=None)
    orch = ValidationOrchestratorV2(
        validatie, ess05_assessment_service=dienst, ess05_burenbron=repo
    )
    return orch, repo, validatie


def evalueer_ess05(validatie: Any, definitie: Any, ctx: dict[str, Any]) -> Any:
    """De ESS-05-evaluator met de invoerbewaking van de validatieservice."""
    from services.validation.evaluators.base import EvaluationDeps, EvaluationOutcome
    from services.validation.evaluators.distinction_assessment import (
        DistinctionAssessmentEvaluator,
    )
    from services.validation.types_internal import EvaluationContext
    from toetsregels.runtime_contract import build_rule_record, missing_inputs

    record = build_rule_record("ESS-05", json.loads(REGEL.read_text(encoding="utf-8")))
    ectx = EvaluationContext(
        raw_text=definitie.definitie,
        cleaned_text=definitie.definitie,
        begrip=definitie.begrip,
        metadata=ctx,
    )
    beschikbaar = validatie._available_inputs(ectx)
    ontbrekend = missing_inputs(record, beschikbaar)
    if ontbrekend:
        return EvaluationOutcome.not_evaluated(
            f"vereiste invoer ontbreekt: {', '.join(map(str, ontbrekend))}"
        )
    deps = EvaluationDeps(support=validatie, available_inputs=beschikbaar)
    return DistinctionAssessmentEvaluator().evaluate(record, ectx, deps)


def ui_regels(detail: dict[str, Any]) -> list[str]:
    """De tekst die `render_rule_results` voor ESS-05 zou tonen, zonder Streamlit."""
    from ui.components import validation_view as vv

    status = str(detail.get("status") or "")
    label = vv._inhoudelijk_label(detail) or vv._UITKOMSTLABEL.get(status, status)
    regels = [f"ESS-05 · {label} — zonder cijfer (uitkomst met motivering)"]
    for part in detail.get("parts") or []:
        if isinstance(part, dict):
            regels.append(f"{part.get('status')}: {part.get('reason') or ''}")
            if part.get("action"):
                regels.append(f"Vervolgstap: {part['action']}")
    review = detail.get("review")
    if isinstance(review, dict):
        regels.extend(vv._review_regels(review))
    return regels


def verwachte_aanroepen(document: dict[str, Any] | None) -> dict[str, Any]:
    """Bovengrens volgens de route: interpretatie + kern + (doel) + één per buur."""
    invoer = (document or {}).get("input") or {}
    buren = invoer.get("buren") or []
    materiaal = invoer.get("materiaal") or {}
    doel = any(k == "meaning" or k.startswith("source:") for k in materiaal)
    maximum = 0 if not buren else 2 + (1 if doel else 0) + len(buren)
    return {"buren": len(buren), "doelmateriaal": doel, "maximum": maximum}


async def beoordeel_record(
    orch: Any, repo: Any, validatie: Any, record_id: int, teller: Teller
) -> dict[str, Any]:
    """Eén record exact eenmaal door de ESS-05-route van de app."""
    teller.record = record_id
    definitie = repo.get(record_id)
    if definitie is None:
        return {"record_id": record_id, "fout": "record niet gevonden in de kopie"}
    ctx = orch._enrich_context_with_definition_fields(
        orch._context_dict(None), definitie
    )
    document = await orch._beoordeel_onderscheid(
        definitie.begrip, ctx["record_text"], ctx, f"def768-p1-{record_id}"
    )
    if document is not None:
        ctx["ess05_assessment"] = document
    uitkomst = evalueer_ess05(validatie, definitie, ctx)
    detail = dict((uitkomst.metadata or {}).get("rule_result") or {})
    fout = (document or {}).get("error")
    return {
        "record_id": record_id,
        "begrip": definitie.begrip,
        "definitie": definitie.definitie,
        "invoermateriaal": ((document or {}).get("input") or {}).get("materiaal"),
        "buren": ctx.get("ess05_actieve_buren"),
        "uitgesloten_termen": ctx.get("ess05_uitgesloten_termen"),
        "verwacht": verwachte_aanroepen(document),
        "document": document,
        "evaluator": str(getattr(uitkomst.status, "name", uitkomst.status)),
        "rule_result": detail,
        "ui_regels": ui_regels(detail),
        "fout": fout,
        "aanroepen": [a for a in teller.aanroepen if a["record"] == record_id],
    }


# --- uitvoering ----------------------------------------------------------------


def _git(*args: str) -> str:
    uit = subprocess.run(
        ["git", *args], cwd=PROJECT_ROOT, capture_output=True, text=True, check=False
    )
    return uit.stdout.strip()


def _schrijf_json(pad: Path, data: Any) -> None:
    with pad.open("x", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        f.write("\n")


@dataclass
class Opdracht:
    uitmap: Path
    echt: bool = False
    db: Path = ECHTE_DB
    records: Sequence[int] = RECORDS
    besluit: Path = BESLUIT
    besluit_sha256: str = BESLUIT_SHA256
    #: v1-samenvatting voor het restbudget; verplicht bij --echt.
    vorige: Path | None = None
    vorige_sha256: str = V1_SAMENVATTING_SHA256
    #: De enige map waarnaar een echte run mag schrijven.
    echte_uitmap: Path = HERHAAL_UITMAP


async def _draai(opdracht: Opdracht, teller: Teller, client: Any) -> list[dict]:
    from services.validation.ess05_verification_service import aanroepgrens

    kopie = opdracht.uitmap / "db-kopie" / "definities.db"
    orch, repo, validatie = bouw_route(kopie, client)
    resultaten: list[dict[str, Any]] = []
    with aanroepgrens(teller.grens):
        for record_id in opdracht.records:
            if teller.gestopt is not None:
                resultaten.append(
                    {"record_id": record_id, "overgeslagen": teller.gestopt}
                )
                continue
            resultaten.append(
                await beoordeel_record(orch, repo, validatie, record_id, teller)
            )
    return resultaten


def voer_uit(opdracht: Opdracht) -> dict[str, Any]:
    """Weigeringen eerst; dan kopie, route, per-recordbestanden en samenvatting."""
    if opdracht.uitmap.exists():
        msg = f"uitvoermap bestaat al: {opdracht.uitmap}; geen tweede poging"
        raise SystemExit(msg)
    besluit = None
    if opdracht.echt:
        besluit = controleer_besluit(opdracht.besluit, opdracht.besluit_sha256)
        if opdracht.uitmap.resolve() != opdracht.echte_uitmap.resolve():
            msg = (
                f"echte run alleen naar {opdracht.echte_uitmap}, niet {opdracht.uitmap}"
            )
            raise SystemExit(msg)
        if opdracht.vorige is None:
            msg = "echte run zonder v1-samenvatting: restbudget onbekend"
            raise SystemExit(msg)
    rest = (
        restbudget(opdracht.vorige, opdracht.vorige_sha256)
        if opdracht.vorige is not None
        else None
    )
    controleer_bijbestanden(opdracht.db)
    opdracht.uitmap.mkdir(parents=True, exist_ok=False)
    db_voor = kopieer_database(
        opdracht.db, opdracht.uitmap / "db-kopie" / "definities.db"
    )
    teller = Teller(eis_kosten=opdracht.echt)
    if rest is not None:
        teller = Teller(
            maximum=rest.aanroepen,
            eis_kosten=opdracht.echt,
            plafond_nusd=rest.kosten_nusd,
        )
    start = datetime.now(UTC).isoformat()
    herstel: Callable[[], None] = lambda: None  # noqa: E731
    resultaten: list[dict[str, Any]] = []
    fout = None
    try:
        if opdracht.echt:
            client, herstel = echte_client(teller)
            resultaten = asyncio.run(_draai(opdracht, teller, client))
        else:
            with rp.geen_netwerk():
                resultaten = asyncio.run(
                    _draai(opdracht, teller, TellendeClient(StubClient(), teller))
                )
    except Exception as exc:
        fout = teller.scrub(f"{type(exc).__name__}: {exc}")
    finally:
        herstel()
    db_na = sha256_bestand(opdracht.db)
    samenvatting = {
        "proef": "DEF-768-P1",
        "modus": "echt" if opdracht.echt else "droog (stubmodel, netwerk geblokkeerd)",
        "start": start,
        "einde": datetime.now(UTC).isoformat(),
        "head": _git("rev-parse", "HEAD"),
        "git_status": _git("status", "--porcelain"),
        "budgetbesluit": str(opdracht.besluit) if besluit is not None else None,
        "budgetbesluit_sha256": (
            opdracht.besluit_sha256 if besluit is not None else None
        ),
        "database": str(opdracht.db),
        "database_sha256_voor": db_voor,
        "database_sha256_na": db_na,
        "database_ongewijzigd": db_voor == db_na,
        "restbudget": rest.als_dict() if rest is not None else None,
        "teller": {
            "maximum": teller.maximum,
            "aanroepen": len(teller.aanroepen),
            "gestopt": teller.gestopt,
            "kosten_nusd": teller.kosten_nusd if opdracht.echt else None,
            "kostenplafond_nusd": teller.plafond_nusd,
        },
        "fout": fout,
        "records": [_kort(r) for r in resultaten],
        "aanroepen": teller.aanroepen,
    }
    for resultaat in resultaten:
        _schrijf_json(
            opdracht.uitmap / f"record-{resultaat['record_id']}.json", resultaat
        )
    _schrijf_json(opdracht.uitmap / "samenvatting.json", samenvatting)
    (opdracht.uitmap / "samenvatting.md").write_text(
        samenvatting_md(samenvatting), encoding="utf-8"
    )
    return samenvatting


def _kort(resultaat: dict[str, Any]) -> dict[str, Any]:
    document = resultaat.get("document") or {}
    fout = resultaat.get("fout")
    return {
        "record_id": resultaat.get("record_id"),
        "begrip": resultaat.get("begrip"),
        "overgeslagen": resultaat.get("overgeslagen"),
        "document_status": document.get("status"),
        "evaluator": resultaat.get("evaluator"),
        "fout": fout if isinstance(fout, (str, type(None))) else fout.get("type"),
        "aanroepen": len(resultaat.get("aanroepen") or []),
        "verwacht": resultaat.get("verwacht"),
        "buren": [
            {k: b.get(k) for k in ("id", "term", "herkomst", "bevestigd")}
            for b in resultaat.get("buren") or []
        ],
        "ui_regels": resultaat.get("ui_regels"),
    }


def samenvatting_md(s: dict[str, Any]) -> str:
    kosten = s["teller"]["kosten_nusd"]
    regels = [
        "# DEF-768 P1 — rooktest ESS-05 op echte definities",
        "",
        f"- Modus: {s['modus']}",
        f"- HEAD: `{s['head']}`",
        f"- Budgetbesluit: {s['budgetbesluit_sha256'] or '— (niet vereist in droog)'}",
        (
            f"- Database ongewijzigd: {'ja' if s['database_ongewijzigd'] else 'NEE'}"
            f" (sha256 `{s['database_sha256_voor']}`)"
        ),
        f"- Modelaanroepen: {s['teller']['aanroepen']} van max {s['teller']['maximum']}"
        + (f"; kosten USD {kosten / 1e9:.6f}" if kosten is not None else ""),
        (
            f"- Restbudget uit v1: {rest['aanroepen']} aanroepen, USD "
            f"{rest['kosten_nusd'] / 1e9:.6f} (`{rest['bron_sha256']}`)"
            if (rest := s.get("restbudget"))
            else "- Restbudget uit v1: — (volledig besluitbudget)"
        ),
        f"- Teller gestopt: {s['teller']['gestopt'] or 'nee'}",
        f"- Fout: {s['fout'] or 'geen'}",
        "",
    ]
    for r in s["records"]:
        regels += [f"## Record {r['record_id']} — {r.get('begrip') or '?'}", ""]
        if r.get("overgeslagen"):
            regels += [f"Overgeslagen: {r['overgeslagen']}", ""]
            continue
        buren = "; ".join(
            f"{b['term']} ({b['herkomst']}, "
            f"{'bevestigd' if b['bevestigd'] else 'onbevestigd'})"
            for b in r["buren"]
        )
        verwacht = r.get("verwacht") or {}
        regels += [
            f"- Documentstatus: {r['document_status']}; evaluator: {r['evaluator']}",
            f"- Fout: {r['fout'] or 'geen'}",
            f"- Aanroepen: {r['aanroepen']} (bovengrens {verwacht.get('maximum')})",
            f"- Buren: {buren or 'geen'}",
            "- UI:",
            *(f"  - {regel}" for regel in r.get("ui_regels") or []),
            "",
        ]
    return "\n".join(regels)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    modus = parser.add_mutually_exclusive_group()
    modus.add_argument("--echt", action="store_true", help="echte modelaanroepen")
    modus.add_argument("--droog", action="store_true", help="stubmodel (standaard)")
    parser.add_argument("--uitmap", type=Path, required=True)
    args = parser.parse_args(argv)
    s = voer_uit(
        Opdracht(
            uitmap=args.uitmap,
            echt=args.echt,
            vorige=V1_SAMENVATTING,
            vorige_sha256=V1_SAMENVATTING_SHA256,
            echte_uitmap=HERHAAL_UITMAP,
        )
    )
    print(samenvatting_md(s))
    if not opdracht_ok(s):
        return 1
    return 0


def opdracht_ok(s: dict[str, Any]) -> bool:
    return s["fout"] is None and s["database_ongewijzigd"]


if __name__ == "__main__":
    raise SystemExit(main())
