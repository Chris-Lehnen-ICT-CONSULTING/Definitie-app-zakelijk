#!/usr/bin/env python3
"""DEF-821 effectproef: echte voor/na-uitvoer op de volledige appprompts.

Vergelijkt twee bronversies van de app op dezelfde, vooraf vastgelegde
casussen: ``basis`` (commit ``BASIS_REF``, via ``git archive`` in een
tijdelijke map; geen branch wordt gewijzigd) en ``nieuw`` (een kopie van de
huidige werkboom, ``src/`` + ``config/``). Elke versie draait in een eigen
subprocess met uitsluitend haar eigen ``src`` op ``sys.path`` en een eigen
lege werkmap als ``cwd`` (schijfcaches zoals ``cache/`` blijven gescheiden).

App-route (per casus, per versie, per herhaling):
``DefinitionOrchestratorV2.create_definition`` met de echte
``PromptServiceV2``, ``SecurityService``, ``CleaningService``,
``ValidationOrchestratorV2``/``ModularValidationService`` en
``DefinitionRepository`` op een verse SQLite in de uitvoermap, en een echte
``AIServiceV2(use_cache=False, model_router=ModelRouter.from_config())``
met de client uit ``services.ai.create_ai_client`` achter een registrerende
proxy (telt en bewaart elke aanroep; SDK-retries op 0). Bewust vervangen,
identiek voor beide versies: synoniemverrijking, web lookup, RAG,
voorbeeldgeneratie en de AI-bronbeoordeling (CON-02) staan uit; documenten
gaan via ``context["documents"]`` zoals de UI-handler ze aanlevert.
UI-handler en ``ServiceAdapter`` liggen buiten de lus (die zijn gedekt door
``tests/unit/ui/test_def821_ontbrekende_grond_ui.py``).

Standaard offline: alleen de volledige prompts van beide versies worden
gebouwd (de keten stopt vóór het model) en de model-/instellingsinfo wordt
vergeleken. Alleen met ``--live`` volgen modelaanroepen: sequentieel,
tegengebalanceerd (h1: basis→nieuw, h2: nieuw→basis), hard begrensd op
``MAX_LIVE_CALLS`` (32) en vooraf geweigerd als casussen × 2 versies ×
herhalingen dat overschrijdt. De API-sleutel komt alleen via de
runtime-loader (``--dotenv``, read-only) in het proces; alle geschreven tekst
wordt op sleutelpatronen en op de exacte sleutelwaarde gescrubd.

Casusschema (``--cases``; JSON-lijst, JSON-object ``{"casussen": [...]}``
of JSONL met één casus per regel) — zie ``CASUS_SCHEMA`` of ``--schema``.

Gebruik:
    PYTHONPATH=src .venv/bin/python scripts/testing/def821_effectproef.py \\
        --cases scripts/testing/def821_ontwikkelcasussen.json --out /tmp/x
    ... --live --dotenv /pad/naar/.env
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import io
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tarfile
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BASIS_REF = "b687c1615d4abd30b5b6d38dd55e64f6a758e187"
VERSIES = ("basis", "nieuw")
#: Harde bovengrens op verse modelaanroepen over de hele proef.
MAX_LIVE_CALLS = 32
HERHALINGEN = 2
#: Volgorde van de live-workers: tegengebalanceerd tegen tijdsdrift.
LIVE_VOLGORDE: tuple[tuple[int, str], ...] = (
    (1, "basis"),
    (1, "nieuw"),
    (2, "nieuw"),
    (2, "basis"),
)
#: Zelfde patroon als `services.ai.base_client.sanitize_error`.
_SECRET_RE = re.compile(r"sk-[\w-]{10,}")
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
UITKOMSTEN = ("definitie", "ontbrekende_grond", "conflict", "onbeslist")

CASUS_SCHEMA: dict[str, Any] = {
    "id": "str, verplicht, uniek; [A-Za-z0-9_.-], max 64 tekens (bestandsnaam)",
    "begrip": "str, verplicht, niet leeg",
    "verwachting": (
        "str, verplicht: vooraf vastgelegde normverwachting; komt nooit in de "
        "prompt (wordt gecontroleerd)"
    ),
    "organisatorische_context": "list[str], optioneel (default [])",
    "juridische_context": "list[str], optioneel (default [])",
    "wettelijke_basis": "list[str], optioneel (default [])",
    "ontologische_categorie": (
        "str|null, optioneel: type|proces|resultaat|exemplaar of null (labelvrij)"
    ),
    "documenten": (
        "list[object], optioneel: expliciete, synthetische bronpassages; per "
        "document verplicht 'doc_id' en 'snippet', optioneel 'filename', "
        "'title'. Gaan als documentbronnen via context['documents'] naar de "
        "orchestrator (geen netwerk)"
    ),
    "betekenisverduidelijking": (
        "str|null, optioneel: exacte waarde van het typed veld "
        "GenerationRequest.betekenisverduidelijking. De UI-handler bouwt die "
        "waarde als ketenregel (ui.helpers.betekenisconflict."
        "verduidelijking_uit_keten: genummerde vraag-antwoordparen); geef "
        "die vorm mee om de UI-route na te bootsen"
    ),
    "verwachte_uitkomst": f"optioneel, een van {list(UITKOMSTEN)}",
    "herkomst": "str, optioneel: waar de casus vandaan komt",
}
_CASUS_SLEUTELS = frozenset(CASUS_SCHEMA)
_DOCUMENT_SLEUTELS = frozenset({"doc_id", "snippet", "filename", "title"})
_CATEGORIEEN = ("type", "proces", "resultaat", "exemplaar")

logger = logging.getLogger("def821_effectproef")


# ---------------------------------------------------------------------------
# Casussen
# ---------------------------------------------------------------------------


class CasusFoutError(ValueError):
    """Een casusbestand voldoet niet aan `CASUS_SCHEMA`."""


@dataclass(frozen=True)
class Casus:
    id: str
    begrip: str
    verwachting: str
    organisatorische_context: tuple[str, ...] = ()
    juridische_context: tuple[str, ...] = ()
    wettelijke_basis: tuple[str, ...] = ()
    ontologische_categorie: str | None = None
    documenten: tuple[dict[str, str], ...] = ()
    betekenisverduidelijking: str | None = None
    verwachte_uitkomst: str | None = None
    herkomst: str | None = None


def _tekstlijst(waarde: Any, veld: str, cid: str) -> tuple[str, ...]:
    if waarde is None:
        return ()
    if not isinstance(waarde, list) or not all(
        isinstance(w, str) and w.strip() for w in waarde
    ):
        msg = f"casus {cid}: '{veld}' moet een lijst niet-lege teksten zijn"
        raise CasusFoutError(msg)
    return tuple(w.strip() for w in waarde)


def _documenten(waarde: Any, cid: str) -> tuple[dict[str, str], ...]:
    if waarde is None:
        return ()
    if not isinstance(waarde, list):
        msg = f"casus {cid}: 'documenten' moet een lijst zijn"
        raise CasusFoutError(msg)
    uit: list[dict[str, str]] = []
    for doc in waarde:
        if not isinstance(doc, dict) or set(doc) - _DOCUMENT_SLEUTELS:
            msg = f"casus {cid}: document met onbekende sleutel of geen object"
            raise CasusFoutError(msg)
        if not all(isinstance(v, str) and v.strip() for v in doc.values()):
            msg = f"casus {cid}: documentvelden moeten niet-lege teksten zijn"
            raise CasusFoutError(msg)
        if "doc_id" not in doc or "snippet" not in doc:
            msg = f"casus {cid}: document mist 'doc_id' of 'snippet'"
            raise CasusFoutError(msg)
        uit.append(dict(doc))
    return tuple(uit)


def casus_uit_dict(data: Any) -> Casus:
    if not isinstance(data, dict):
        msg = "een casus moet een JSON-object zijn"
        raise CasusFoutError(msg)
    cid = data.get("id")
    if not isinstance(cid, str) or not _ID_RE.match(cid):
        msg = f"ongeldige of ontbrekende casus-id: {cid!r}"
        raise CasusFoutError(msg)
    onbekend = set(data) - _CASUS_SLEUTELS
    if onbekend:
        msg = f"casus {cid}: onbekende sleutel(s) {sorted(onbekend)}"
        raise CasusFoutError(msg)
    for veld in ("begrip", "verwachting"):
        if not isinstance(data.get(veld), str) or not data[veld].strip():
            msg = f"casus {cid}: '{veld}' is verplicht en niet leeg"
            raise CasusFoutError(msg)
    categorie = data.get("ontologische_categorie")
    if categorie is not None and categorie not in _CATEGORIEEN:
        msg = f"casus {cid}: ongeldige ontologische_categorie {categorie!r}"
        raise CasusFoutError(msg)
    uitkomst = data.get("verwachte_uitkomst")
    if uitkomst is not None and uitkomst not in UITKOMSTEN:
        msg = f"casus {cid}: ongeldige verwachte_uitkomst {uitkomst!r}"
        raise CasusFoutError(msg)
    verduidelijking = data.get("betekenisverduidelijking")
    if verduidelijking is not None and not (
        isinstance(verduidelijking, str) and verduidelijking.strip()
    ):
        msg = f"casus {cid}: 'betekenisverduidelijking' moet tekst of null zijn"
        raise CasusFoutError(msg)
    herkomst = data.get("herkomst")
    if herkomst is not None and not isinstance(herkomst, str):
        msg = f"casus {cid}: 'herkomst' moet tekst zijn"
        raise CasusFoutError(msg)
    return Casus(
        id=cid,
        begrip=data["begrip"].strip(),
        verwachting=data["verwachting"].strip(),
        organisatorische_context=_tekstlijst(
            data.get("organisatorische_context"), "organisatorische_context", cid
        ),
        juridische_context=_tekstlijst(
            data.get("juridische_context"), "juridische_context", cid
        ),
        wettelijke_basis=_tekstlijst(
            data.get("wettelijke_basis"), "wettelijke_basis", cid
        ),
        ontologische_categorie=categorie,
        documenten=_documenten(data.get("documenten"), cid),
        betekenisverduidelijking=verduidelijking,
        verwachte_uitkomst=uitkomst,
        herkomst=herkomst,
    )


def lees_casussen(pad: Path) -> list[Casus]:
    """Lees JSON (lijst of ``{"casussen": [...]}``) of JSONL; valideer strikt."""
    tekst = pad.read_text(encoding="utf-8")
    ruw: Any
    if pad.suffix.lower() == ".jsonl":
        ruw = [json.loads(r) for r in tekst.splitlines() if r.strip()]
    else:
        ruw = json.loads(tekst)
        if isinstance(ruw, dict) and set(ruw) == {"casussen"}:
            ruw = ruw["casussen"]
    if not isinstance(ruw, list) or not ruw:
        msg = "casusbestand bevat geen niet-lege lijst casussen"
        raise CasusFoutError(msg)
    casussen = [casus_uit_dict(c) for c in ruw]
    ids = [c.id for c in casussen]
    if len(set(ids)) != len(ids):
        msg = "dubbele casus-id's"
        raise CasusFoutError(msg)
    return casussen


def controleer_budget(aantal_casussen: int, herhalingen: int, max_calls: int) -> int:
    """Het benodigde aantal live-aanroepen, of een weigering vóór elke aanroep."""
    grens = min(int(max_calls), MAX_LIVE_CALLS)
    nodig = aantal_casussen * len(VERSIES) * herhalingen
    if nodig > grens:
        msg = (
            f"{aantal_casussen} casussen × {len(VERSIES)} versies × "
            f"{herhalingen} herhalingen = {nodig} aanroepen > grens {grens}"
        )
        raise SystemExit(msg)
    return nodig


# ---------------------------------------------------------------------------
# Scrubbing en I/O
# ---------------------------------------------------------------------------


class Scrubber:
    """Verwijder sleutelpatronen en (indien bekend) de exacte sleutelwaarde."""

    def __init__(self) -> None:
        self._geheimen: list[str] = []

    def registreer(self, geheim: str | None) -> None:
        if geheim and len(geheim) >= 8:
            self._geheimen.append(geheim)

    def __call__(self, tekst: str) -> str:
        for geheim in self._geheimen:
            tekst = tekst.replace(geheim, "[REDACTED]")
        return _SECRET_RE.sub("[REDACTED]", tekst)


SCRUB = Scrubber()


class _ScrubFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = SCRUB(record.getMessage())
        record.args = ()
        return True


def schrijf_json(pad: Path, data: Any) -> None:
    pad.parent.mkdir(parents=True, exist_ok=True)
    tekst = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    pad.write_text(SCRUB(tekst), encoding="utf-8")


def schrijf_tekst(pad: Path, tekst: str) -> None:
    pad.parent.mkdir(parents=True, exist_ok=True)
    pad.write_text(SCRUB(tekst), encoding="utf-8")


def sha256(tekst: str) -> str:
    return hashlib.sha256(tekst.encode("utf-8")).hexdigest()


def _git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def boom_hash(wortel: Path) -> str:
    """Inhoudshash van ``src/`` + ``config/`` (zonder bytecode)."""
    h = hashlib.sha256()
    for deel in ("src", "config"):
        for pad in sorted((wortel / deel).rglob("*")):
            if not pad.is_file() or "__pycache__" in pad.parts or pad.suffix == ".pyc":
                continue
            h.update(str(pad.relative_to(wortel)).encode("utf-8") + b"\0")
            h.update(pad.read_bytes() + b"\0")
    return h.hexdigest()


def maak_basis_snapshot(ref: str, doel: Path) -> dict[str, Any]:
    """``git archive <ref> src config`` → ``doel`` (read-only voor de repo)."""
    sha = _git("rev-parse", "--verify", f"{ref}^{{commit}}")
    archief = subprocess.check_output(
        ["git", "-C", str(ROOT), "archive", "--format=tar", sha, "src", "config"]
    )
    doel.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(archief)) as tar:
        tar.extractall(doel, filter="data")
    return {
        "bron": "git archive",
        "ref": ref,
        "commit": sha,
        "boom_sha256": boom_hash(doel),
    }


def maak_nieuw_snapshot(doel: Path) -> dict[str, Any]:
    """Kopie van de huidige werkboom (``src/`` + ``config/``), met herkomst."""
    negeer = shutil.ignore_patterns("__pycache__", "*.pyc")
    doel.mkdir(parents=True)
    for deel in ("src", "config"):
        shutil.copytree(ROOT / deel, doel / deel, ignore=negeer)
    diff = _git("diff", "--binary", "HEAD", "--", "src", "config")
    return {
        "bron": "kopie werkboom",
        "werkboom": str(ROOT),
        "head": _git("rev-parse", "HEAD"),
        "branch": _git("branch", "--show-current"),
        "diff_t_o_v_head_sha256": sha256(diff),
        "ongetrackt_in_src_config": _git(
            "ls-files", "--others", "--exclude-standard", "--", "src", "config"
        ).splitlines(),
        "boom_sha256": boom_hash(doel),
    }


# ---------------------------------------------------------------------------
# Worker: draait binnen één bronsnapshot
# ---------------------------------------------------------------------------


class LiveBudgetOverschredenError(RuntimeError):
    """Geen `AIClientError`-subklasse: de retry-lus van de app herhaalt niet."""


class OfflineStopError(RuntimeError):
    """Bewuste stop vóór de modelaanroep (offline: alleen prompts bouwen)."""


@dataclass
class ModelAanroep:
    volgnummer: int
    model_gevraagd: str
    temperature: float
    max_tokens: int
    timeout: float | None
    messages: list[dict[str, str]]
    prompt_sha256: str
    gestart_utc: str
    duur_s: float | None = None
    respons_tekst: str | None = None
    respons_model: str | None = None
    tokens_used: int | None = None
    sdk: dict[str, Any] = field(default_factory=dict)
    fout: str | None = None


class RegistrerendeClient:
    """AsyncAIClient-proxy: registreert elke aanroep en bewaakt het budget."""

    def __init__(self, echt: Any, budget: int) -> None:
        self._echt = echt
        self._budget = budget
        self.aanroepen: list[ModelAanroep] = []
        self._koppel_sdk()

    @property
    def provider_name(self) -> str:
        return str(self._echt.provider_name)

    async def chat_completion(
        self,
        messages: list[Any],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 300,
        timeout: float | None = None,
    ) -> Any:
        if len(self.aanroepen) >= self._budget:
            msg = f"live-budget van {self._budget} modelaanroepen is op"
            raise LiveBudgetOverschredenError(msg)
        aanroep = ModelAanroep(
            volgnummer=len(self.aanroepen) + 1,
            model_gevraagd=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            prompt_sha256=sha256(messages[-1].content),
            gestart_utc=datetime.now(UTC).isoformat(),
        )
        self.aanroepen.append(aanroep)
        start = time.monotonic()
        try:
            respons = await self._echt.chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
            )
        except Exception as exc:
            aanroep.duur_s = time.monotonic() - start
            aanroep.fout = f"{type(exc).__name__}: {SCRUB(str(exc))}"
            raise
        aanroep.duur_s = time.monotonic() - start
        aanroep.respons_tekst = respons.text
        aanroep.respons_model = respons.model
        aanroep.tokens_used = respons.tokens_used
        return respons

    async def close(self) -> None:
        await self._echt.close()

    def _koppel_sdk(self) -> None:
        """Lees stop_reason/usage van de ruwe SDK-respons mee (Anthropic/OpenAI)."""
        sdk = getattr(self._echt, "_client", None)
        doel = getattr(sdk, "messages", None) or getattr(
            getattr(sdk, "chat", None), "completions", None
        )
        origineel = getattr(doel, "create", None)
        if origineel is None:
            return

        async def _create(*args: Any, **kwargs: Any) -> Any:
            resp = await origineel(*args, **kwargs)
            if self.aanroepen:
                self.aanroepen[-1].sdk = _sdk_metadata(resp)
            return resp

        doel.create = _create


def _sdk_metadata(resp: Any) -> dict[str, Any]:
    usage = getattr(resp, "usage", None)
    meta: dict[str, Any] = {
        "id": getattr(resp, "id", None),
        "model": getattr(resp, "model", None),
        "stop_reason": getattr(resp, "stop_reason", None),
    }
    keuzes = getattr(resp, "choices", None)
    if keuzes:
        meta["finish_reason"] = getattr(keuzes[0], "finish_reason", None)
    if usage is not None:
        meta["usage"] = {
            naam: getattr(usage, naam)
            for naam in ("input_tokens", "output_tokens", "prompt_tokens")
            if isinstance(getattr(usage, naam, None), int)
        }
    return meta


class _OfflineAI:
    """Offline: de volledige prompt wordt gebouwd; de keten stopt vóór het model."""

    def __init__(self) -> None:
        self.prompts: list[str] = []

    async def generate_definition(self, prompt: str, **kwargs: Any) -> Any:
        self.prompts.append(prompt)
        self.kwargs = dict(kwargs)
        msg = "offline: geen modelaanroep"
        raise OfflineStopError(msg)


def _bevestig_bron(bron: Path) -> None:
    """Fail-closed: de app-modules moeten uit het snapshot komen."""
    import services

    herkomst = Path(services.__file__).resolve()
    if (bron / "src").resolve() not in herkomst.parents:
        msg = f"app-modules komen niet uit het snapshot ({herkomst})"
        raise SystemExit(msg)


def _modelinfo(live_client: RegistrerendeClient | None) -> dict[str, Any]:
    from config.config_manager import get_config_manager, get_prompt_temperature
    from services.ai.model_router import ModelRouter

    config = get_config_manager()
    provider, model = ModelRouter.from_config().get_model("definition_core")
    info: dict[str, Any] = {
        "provider_geconfigureerd": config.api.ai_provider,
        "provider_router": provider,
        "model_definition_core": model,
        "temperature_definition": get_prompt_temperature("definition"),
        "max_tokens_orchestrator_default": 500,
        "timeout_seconds_aiservice_default": 30,
        "ai_service_cache": False,
    }
    if live_client is not None:
        info["sdk_max_retries"] = getattr(
            getattr(live_client._echt, "_client", None), "max_retries", None
        )
    return info


def _bouw_orchestrator(db_pad: Path, ai_service: Any) -> Any:
    from services.cleaning_service import CleaningConfig, CleaningService
    from services.definition_repository import DefinitionRepository
    from services.interfaces import OrchestratorConfig
    from services.orchestrators.definition_orchestrator_v2 import (
        DefinitionOrchestratorV2,
    )
    from services.orchestrators.validation_orchestrator_v2 import (
        ValidationOrchestratorV2,
    )
    from services.prompts.prompt_service_v2 import PromptServiceV2
    from services.security_service import SecurityService
    from services.validation.config import ValidationConfig
    from services.validation.modular_validation_service import (
        ModularValidationService,
    )
    from toetsregels.cached_manager import get_cached_toetsregel_manager

    if db_pad.exists():
        msg = f"DB-pad {db_pad} bestaat al; geen bestaand bewijs overschrijven"
        raise SystemExit(msg)
    repository = DefinitionRepository(str(db_pad))
    cleaning = CleaningService(CleaningConfig())
    src = Path(sys.modules["services"].__file__).resolve().parents[1]
    validatie = ValidationOrchestratorV2(
        validation_service=ModularValidationService(
            get_cached_toetsregel_manager(),
            None,
            ValidationConfig.from_yaml(str(src / "config" / "validation_rules.yaml")),
            repository=repository,
        ),
        cleaning_service=cleaning,
        source_assessment_service=None,
    )
    return DefinitionOrchestratorV2(
        prompt_service=PromptServiceV2(),
        ai_service=ai_service,
        validation_service=validatie,
        cleaning_service=cleaning,
        repository=repository,
        security_service=SecurityService(),
        config=OrchestratorConfig(
            enable_feedback_loop=False, enable_enhancement=False, enable_caching=False
        ),
        web_lookup_service=None,
        synonym_orchestrator=None,
        rag_service=None,
        source_assessment_service=None,
    )


def _request_en_context(casus: Casus, versie: str, herhaling: int) -> tuple[Any, Any]:
    from services.interfaces import GenerationRequest

    request = GenerationRequest(
        id=f"def821-{versie}-h{herhaling}-{casus.id}",
        begrip=casus.begrip,
        ontologische_categorie=casus.ontologische_categorie,
        organisatorische_context=list(casus.organisatorische_context),
        juridische_context=list(casus.juridische_context),
        wettelijke_basis=list(casus.wettelijke_basis),
        actor="def821_effectproef",
        betekenisverduidelijking=casus.betekenisverduidelijking,
    )
    context = None
    if casus.documenten:
        snippets = [
            {
                "provider": "documents",
                "doc_id": d["doc_id"],
                "filename": d.get("filename") or f"{d['doc_id']}.txt",
                "title": d.get("title") or d.get("filename") or d["doc_id"],
                "snippet": d["snippet"],
                "score": 1.0,
                "selection_basis": "term_match",
            }
            for d in casus.documenten
        ]
        context = {
            "documents": {
                "snippets": snippets,
                "selected_ids": [d["doc_id"] for d in casus.documenten],
            }
        }
    return request, context


def _aantal_records(db_pad: Path, begrip: str) -> int:
    import sqlite3

    with sqlite3.connect(str(db_pad)) as conn:
        (aantal,) = conn.execute(
            "SELECT COUNT(*) FROM definities WHERE begrip = ?", (begrip,)
        ).fetchone()
    return int(aantal)


def _readback(db_pad: Path, definition_id: Any) -> dict[str, Any] | None:
    if not definition_id:
        return None
    from database.definitie_repository import DefinitieRepository

    record = DefinitieRepository(str(db_pad)).get_definitie(int(definition_id))
    if record is None:
        return None
    return {
        "id": record.id,
        "definitie": record.definitie,
        "categorie": record.categorie,
    }


def _app_uitkomst(response: Any) -> dict[str, Any]:
    meta = dict(response.metadata or {})
    return {
        "success": response.success,
        "error_type": meta.get("error_type"),
        "error": SCRUB(str(response.error)) if response.error else None,
        "definitie": getattr(response.definition, "definitie", None),
        "definition_id": getattr(response.definition, "id", None),
        "betekenisgrond_ontbreekt": meta.get("betekenisgrond_ontbreekt"),
        "betekenisconflict": meta.get("betekenisconflict"),
        "code": meta.get("code"),
        "reden": meta.get("reden"),
    }


def _schakel_voorbeelden_uit() -> None:
    from voorbeelden import unified_voorbeelden

    async def _geen(**_: Any) -> dict[str, Any]:
        return {}

    unified_voorbeelden.genereer_alle_voorbeelden_async = _geen  # type: ignore[assignment]


async def _worker_prompts(
    casussen: list[Casus], versie: str, uitmap: Path
) -> dict[str, Any]:
    ai = _OfflineAI()
    prompts: dict[str, Any] = {}
    for casus in casussen:
        orchestrator = _bouw_orchestrator(uitmap / "db" / f"{casus.id}.db", ai)
        request, context = _request_en_context(casus, versie, 0)
        response = await orchestrator.create_definition(request, context=context)
        meta = dict(response.metadata or {})
        if meta.get("error_type") != OfflineStopError.__name__:
            msg = f"casus {casus.id}: keten stopte niet bij het model ({meta.get('error_type')})"
            raise SystemExit(msg)
        prompt = ai.prompts[-1]
        schrijf_tekst(uitmap / "prompts" / f"{casus.id}.prompt.txt", prompt)
        prompts[casus.id] = {
            "sha256": sha256(prompt),
            "lengte": len(prompt),
            "verwachting_in_prompt": casus.verwachting in prompt,
            "generate_kwargs": {
                k: v
                for k, v in ai.kwargs.items()
                if k in ("temperature", "max_tokens", "model")
            },
        }
    return {"modelinfo": _modelinfo(None), "prompts": prompts}


async def _worker_live(
    casussen: list[Casus],
    versie: str,
    herhaling: int,
    uitmap: Path,
    budget: int,
) -> dict[str, Any]:
    from config.config_manager import get_config_manager
    from services.ai import create_ai_client
    from services.ai.model_router import ModelRouter
    from services.ai_service_v2 import AIServiceV2

    config = get_config_manager()
    provider = config.api.ai_provider
    key = (
        config.api.anthropic_api_key
        if provider == "anthropic"
        else config.api.openai_api_key
    )
    if not key:
        msg = f"geen API-key voor provider {provider!r} via de runtime-loader"
        raise SystemExit(msg)
    SCRUB.registreer(key)
    os.environ["AI_SDK_MAX_RETRIES"] = "0"
    echt = create_ai_client(provider=provider, api_key=key)
    del key
    if getattr(getattr(echt, "_client", None), "max_retries", None) != 0:
        msg = "SDK-retries niet uitgeschakeld; proef niet gestart"
        raise SystemExit(msg)
    client = RegistrerendeClient(echt, budget)
    ai_service = AIServiceV2(
        use_cache=False, ai_client=client, model_router=ModelRouter.from_config()
    )
    verslagen: list[dict[str, Any]] = []
    try:
        for casus in casussen:
            db_pad = uitmap / "db" / f"{casus.id}.db"
            orchestrator = _bouw_orchestrator(db_pad, ai_service)
            request, context = _request_en_context(casus, versie, herhaling)
            voor = _aantal_records(db_pad, casus.begrip)
            eerder = len(client.aanroepen)
            start = time.monotonic()
            response = await orchestrator.create_definition(request, context=context)
            nieuwe = client.aanroepen[eerder:]
            uitkomst = _app_uitkomst(response)
            na = _aantal_records(db_pad, casus.begrip)
            laatste = nieuwe[-1] if nieuwe else None
            verslag = {
                "casus_id": casus.id,
                "versie": versie,
                "herhaling": herhaling,
                "duur_s": round(time.monotonic() - start, 3),
                "aantal_modelaanroepen": len(nieuwe),
                "aanroepen": [asdict(a) for a in nieuwe],
                "prompt_sha256": laatste.prompt_sha256 if laatste else None,
                "respons_tekst": laatste.respons_tekst if laatste else None,
                "app": uitkomst,
                "records_voor": voor,
                "records_na": na,
                "readback": _readback(db_pad, uitkomst["definition_id"]),
                "infrastructuur_geblokkeerd": str(response.error or "").startswith(
                    "Generation failed:"
                ),
            }
            verslagen.append(verslag)
            schrijf_json(uitmap / f"{casus.id}.json", verslag)
            if laatste is not None:
                schrijf_tekst(
                    uitmap / f"{casus.id}.prompt.txt", laatste.messages[-1]["content"]
                )
                if laatste.respons_tekst is not None:
                    schrijf_tekst(
                        uitmap / f"{casus.id}.respons.txt", laatste.respons_tekst
                    )
    finally:
        await client.close()
    return {
        "modelinfo": _modelinfo(client),
        "modelaanroepen": len(client.aanroepen),
        "verslagen": verslagen,
    }


def _worker_classificeer(uitmap: Path) -> dict[str, Any]:
    """Classificeer álle ruwe antwoorden met de parser van déze (nieuwe) versie."""
    from services.modelantwoord import lees_modelantwoord

    uit: dict[str, Any] = {}
    for pad in sorted(uitmap.glob("live/*/h*/resultaat.json")):
        for verslag in json.loads(pad.read_text(encoding="utf-8"))["verslagen"]:
            tekst = verslag.get("respons_tekst")
            sleutel = (
                f"{verslag['versie']}/h{verslag['herhaling']}/{verslag['casus_id']}"
            )
            if tekst is None:
                uit[sleutel] = {"soort": None, "code": None}
                continue
            antwoord = lees_modelantwoord(tekst)
            uit[sleutel] = {"soort": antwoord.soort, "code": antwoord.code}
    return uit


def worker_main(args: argparse.Namespace) -> int:
    bron = Path(args.bron).resolve()
    uitmap = Path(args.uitmap).resolve()
    sys.path.insert(0, str(bron / "src"))
    werkmap = uitmap / "werkmap"
    werkmap.mkdir(parents=True, exist_ok=True)
    os.chdir(werkmap)
    handler = logging.FileHandler(uitmap / "worker.log", encoding="utf-8")
    handler.addFilter(_ScrubFilter())
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        handlers=[handler],
    )
    if args.dotenv:
        from config.dotenv_loader import load_project_dotenv

        load_project_dotenv(pad=Path(args.dotenv))
    _bevestig_bron(bron)
    from toetsregels.rule_cache import get_rule_cache

    get_rule_cache().clear_cache()
    _schakel_voorbeelden_uit()

    if args.worker == "classificeer":
        schrijf_json(
            uitmap / "classificatie.json", _worker_classificeer(Path(args.proefmap))
        )
        return 0
    casussen = [
        casus_uit_dict(c) for c in json.loads(Path(args.cases_json).read_text("utf-8"))
    ]
    if args.worker == "prompts":
        resultaat = asyncio.run(_worker_prompts(casussen, args.versie, uitmap))
    else:
        resultaat = asyncio.run(
            _worker_live(casussen, args.versie, args.herhaling, uitmap, args.budget)
        )
    schrijf_json(uitmap / "resultaat.json", resultaat)
    return 0


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def _start_worker(bron: Path, uitmap: Path, *extra: str) -> dict[str, Any]:
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    uitmap.mkdir(parents=True, exist_ok=True)
    proces = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--bron",
            str(bron),
            "--uitmap",
            str(uitmap),
            *extra,
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=3600,
    )
    schrijf_tekst(uitmap / "worker.stdout.txt", proces.stdout)
    schrijf_tekst(uitmap / "worker.stderr.txt", proces.stderr)
    if proces.returncode != 0:
        msg = f"worker {extra[:2]} faalde (exit {proces.returncode}); zie {uitmap}"
        raise SystemExit(msg)
    pad = uitmap / (
        "classificatie.json" if "classificeer" in extra else "resultaat.json"
    )
    return json.loads(pad.read_text(encoding="utf-8"))


def _vergelijk_modelinfo(
    info: dict[str, dict[str, Any]], prompts: dict[str, dict[str, Any]]
) -> list[str]:
    """Verschillen in model/instellingen tussen de versies (leeg = gelijk).

    Naast de configuratie ook de werkelijke parameters waarmee de
    orchestrator per casus het model zou aanroepen (temperature,
    max_tokens, model).
    """
    basis, nieuw = info["basis"], info["nieuw"]
    verschil = [k for k in set(basis) | set(nieuw) if basis.get(k) != nieuw.get(k)]
    for cid, p in prompts["basis"].items():
        if p.get("generate_kwargs") != prompts["nieuw"].get(cid, {}).get(
            "generate_kwargs"
        ):
            verschil.append(f"generate_kwargs:{cid}")
    return sorted(verschil)


def _samenvatting(manifest: dict[str, Any]) -> str:
    regels = [
        f"# DEF-821 effectproef — {manifest['modus']}",
        "",
        f"- basis: {manifest['versies']['basis']['commit']}",
        (
            f"- nieuw: HEAD {manifest['versies']['nieuw']['head']} + diff-sha "
            f"{manifest['versies']['nieuw']['diff_t_o_v_head_sha256'][:12]}"
        ),
        f"- model/instellingen gelijk: {not manifest['modelinfo_verschillen']}",
        "",
        "| casus | versie | promptlengte | prompt-sha (12) |",
        "|---|---|---|---|",
    ]
    for versie in VERSIES:
        for cid, p in manifest["prompts"][versie].items():
            regels.append(f"| {cid} | {versie} | {p['lengte']} | {p['sha256'][:12]} |")
    live = manifest.get("live")
    if live:
        regels += [
            "",
            "| casus | versie | h | app | error_type | nieuwe parser | aanroepen | opgeslagen |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for rij in live["rijen"]:
            regels.append(
                f"| {rij['casus_id']} | {rij['versie']} | {rij['herhaling']} | "
                f"{rij['success']} | {rij['error_type']} | {rij['classificatie']} | "
                f"{rij['aanroepen']} | {rij['opgeslagen']} |"
            )
        regels.append(f"\nTotaal modelaanroepen: {live['totaal_aanroepen']}")
    return "\n".join(regels) + "\n"


def driver_main(args: argparse.Namespace) -> int:
    casussen = lees_casussen(Path(args.cases))
    herhalingen = int(args.herhalingen)
    if herhalingen not in (1, 2):
        msg = "herhalingen moet 1 of 2 zijn"
        raise SystemExit(msg)
    nodig = controleer_budget(len(casussen), herhalingen, args.max_calls)
    uitmap = Path(args.out).resolve()
    if uitmap.exists():
        msg = f"uitvoermap {uitmap} bestaat al; kies een nieuwe map"
        raise SystemExit(msg)
    data = (ROOT / "data").resolve()
    if uitmap == data or data in uitmap.parents:
        msg = "uitvoermap mag niet onder de projectdata liggen"
        raise SystemExit(msg)
    uitmap.mkdir(parents=True)
    casusbestand = uitmap / "casussen.json"
    schrijf_json(casusbestand, [asdict(c) for c in casussen])

    bronnen = {"basis": uitmap / "bron" / "basis", "nieuw": uitmap / "bron" / "nieuw"}
    manifest: dict[str, Any] = {
        "gestart_utc": datetime.now(UTC).isoformat(),
        "modus": "live" if args.live else "offline",
        "casussen_bron": str(Path(args.cases).resolve()),
        "casussen_sha256": sha256(Path(args.cases).read_text(encoding="utf-8")),
        "herhalingen": herhalingen,
        "max_live_calls": MAX_LIVE_CALLS,
        "live_aanroepen_gepland": nodig if args.live else 0,
        "app_route": (
            "DefinitionOrchestratorV2.create_definition + echte PromptServiceV2, "
            "SecurityService, CleaningService, ValidationOrchestratorV2/"
            "ModularValidationService, DefinitionRepository (verse SQLite per "
            "casus/versie/herhaling), AIServiceV2(use_cache=False, "
            "ModelRouter.from_config()) met create_ai_client achter een "
            "registrerende proxy (SDK-retries 0)"
        ),
        "seams_vervangen": [
            "synonym_orchestrator=None",
            "web_lookup_service=None",
            "rag_service=None",
            "voorbeelden.genereer_alle_voorbeelden_async → {}",
            "source_assessment_service=None (CON-02 AI-bronbeoordeling uit)",
            "UI-handler/ServiceAdapter buiten de lus (documenten via context['documents'])",
        ],
        "versies": {
            "basis": maak_basis_snapshot(args.basis_ref, bronnen["basis"]),
            "nieuw": maak_nieuw_snapshot(bronnen["nieuw"]),
        },
    }
    schrijf_json(uitmap / "manifest.json", manifest)

    prompts: dict[str, Any] = {}
    modelinfo: dict[str, Any] = {}
    for versie in VERSIES:
        res = _start_worker(
            bronnen[versie],
            uitmap / "prompts" / versie,
            "--worker",
            "prompts",
            "--versie",
            versie,
            "--cases-json",
            str(casusbestand),
        )
        prompts[versie] = res["prompts"]
        modelinfo[versie] = res["modelinfo"]
    manifest["prompts"] = prompts
    manifest["modelinfo"] = modelinfo
    manifest["modelinfo_verschillen"] = _vergelijk_modelinfo(modelinfo, prompts)
    lekken = [
        f"{v}/{cid}"
        for v in VERSIES
        for cid, p in prompts[v].items()
        if p["verwachting_in_prompt"]
    ]
    if lekken:
        msg = f"verwachting staat in de prompt: {lekken}"
        raise SystemExit(msg)
    if manifest["modelinfo_verschillen"]:
        schrijf_json(uitmap / "manifest.json", manifest)
        msg = f"model/instellingen verschillen per versie: {manifest['modelinfo_verschillen']}"
        raise SystemExit(msg)

    if args.live:
        manifest["live"] = _voer_live_uit(
            args, bronnen, uitmap, casusbestand, casussen, prompts
        )
    manifest["afgerond_utc"] = datetime.now(UTC).isoformat()
    schrijf_json(uitmap / "manifest.json", manifest)
    samenvatting = _samenvatting(manifest)
    schrijf_tekst(uitmap / "samenvatting.md", samenvatting)
    sys.stdout.write(samenvatting + f"\nuitvoer: {uitmap}\n")
    return 0


def _voer_live_uit(
    args: argparse.Namespace,
    bronnen: dict[str, Path],
    uitmap: Path,
    casusbestand: Path,
    casussen: list[Casus],
    prompts: dict[str, Any],
) -> dict[str, Any]:
    dotenv = ["--dotenv", str(Path(args.dotenv).resolve())] if args.dotenv else []
    totaal = 0
    resultaten: list[dict[str, Any]] = []
    volgorde = [(h, v) for h, v in LIVE_VOLGORDE if h <= int(args.herhalingen)]
    for herhaling, versie in volgorde:
        res = _start_worker(
            bronnen[versie],
            uitmap / "live" / versie / f"h{herhaling}",
            "--worker",
            "live",
            "--versie",
            versie,
            "--herhaling",
            str(herhaling),
            "--budget",
            str(len(casussen)),
            "--cases-json",
            str(casusbestand),
            *dotenv,
        )
        totaal += int(res["modelaanroepen"])
        resultaten.extend(res["verslagen"])
    if totaal > MAX_LIVE_CALLS:
        msg = f"{totaal} modelaanroepen > {MAX_LIVE_CALLS}"
        raise SystemExit(msg)
    classificatie = _start_worker(
        bronnen["nieuw"],
        uitmap / "classificatie",
        "--worker",
        "classificeer",
        "--proefmap",
        str(uitmap),
    )
    rijen = []
    for v in resultaten:
        sleutel = f"{v['versie']}/h{v['herhaling']}/{v['casus_id']}"
        app = v["app"]
        rijen.append(
            {
                "casus_id": v["casus_id"],
                "versie": v["versie"],
                "herhaling": v["herhaling"],
                "success": app["success"],
                "error_type": app["error_type"],
                "classificatie": (classificatie.get(sleutel) or {}).get("soort"),
                "aanroepen": v["aantal_modelaanroepen"],
                "opgeslagen": v["records_na"] - v["records_voor"],
                "prompt_gelijk_aan_offline": v["prompt_sha256"]
                == prompts[v["versie"]][v["casus_id"]]["sha256"],
            }
        )
    return {"totaal_aanroepen": totaal, "rijen": rijen, "classificatie": classificatie}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n", 1)[0])
    parser.add_argument("--cases", help="casusbestand (JSON of JSONL)")
    parser.add_argument("--out", help="nieuwe uitvoermap (mag nog niet bestaan)")
    parser.add_argument("--live", action="store_true", help="echte modelaanroepen")
    parser.add_argument("--dotenv", default=None, help=".env voor de runtime-loader")
    parser.add_argument("--basis-ref", default=BASIS_REF)
    parser.add_argument("--herhalingen", type=int, default=HERHALINGEN)
    parser.add_argument("--max-calls", type=int, default=MAX_LIVE_CALLS)
    parser.add_argument("--schema", action="store_true", help="toon casusschema")
    # Interne workervlaggen.
    parser.add_argument(
        "--worker", choices=("prompts", "live", "classificeer"), help=argparse.SUPPRESS
    )
    parser.add_argument("--bron", help=argparse.SUPPRESS)
    parser.add_argument("--uitmap", help=argparse.SUPPRESS)
    parser.add_argument("--versie", choices=VERSIES, help=argparse.SUPPRESS)
    parser.add_argument("--herhaling", type=int, default=0, help=argparse.SUPPRESS)
    parser.add_argument("--budget", type=int, default=0, help=argparse.SUPPRESS)
    parser.add_argument("--cases-json", help=argparse.SUPPRESS)
    parser.add_argument("--proefmap", help=argparse.SUPPRESS)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.schema:
        sys.stdout.write(json.dumps(CASUS_SCHEMA, ensure_ascii=False, indent=2) + "\n")
        return 0
    if args.worker:
        return worker_main(args)
    if not args.cases or not args.out:
        msg = "--cases en --out zijn verplicht"
        raise SystemExit(msg)
    return driver_main(args)


if __name__ == "__main__":
    sys.exit(main())
