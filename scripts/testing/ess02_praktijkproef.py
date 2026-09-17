#!/usr/bin/env python3
"""ESS-02-praktijkproef (DEF-751): de echte generatieketen met echte modelantwoorden.

Beproeft PromptServiceV2 + geconfigureerde ModelRouter/AIServiceV2 + parser
(`services.modelantwoord`) + DefinitionOrchestratorV2-afhandeling met een
begrensd aantal verse `definition_core`-aanroepen, en de toetsroute (echte
ESS-02-regel via ModularValidationService) zonder modelaanroep.

Standaard offline (dry-run): bouwt de echte prompts, registreert hash en
lengte, draait de toetsroute en roept geen model aan. Alleen met ``--live``
worden modelaanroepen gedaan: sequentieel, hard begrensd (``MAX_LIVE_CALLS``),
cache uit, timeout en max_tokens uit de normale app-instelling. Verwachte
betekenistoetsen staan hier vast vóór de run en komen nooit in de prompt.

Geen productie-DB: uitsluitend een nieuwe SQLite in de uitvoermap. Geen
secrets in uitvoer: de API-key gaat alleen via de runtime-loader naar de
app-client; alle geschreven tekst wordt op sleutelpatronen gescrubd.

Bewust vervangen (afgebakende proef, geen claim over de hele productieflow):
synoniemverrijking, web lookup, RAG, voorbeeldgeneratie en de AI-bronbeoordeling
(CON-02, taak `validation`) staan uit; documentbronnen gaan via dezelfde
`context["documents"]`-route als de UI-handler. UI-handler en ServiceAdapter
staan buiten de lus (gedekt door `tests/unit/ui/test_def751_verduidelijking_keten.py`).

Gebruik:
    python scripts/testing/ess02_praktijkproef.py                # offline
    python scripts/testing/ess02_praktijkproef.py --live --dotenv /pad/naar/.env
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

logger = logging.getLogger("ess02_praktijkproef")

#: Harde bovengrens op verse modelaanroepen per run (inclusief hergeneratie).
MAX_LIVE_CALLS = 8
#: Zelfde patroon als `services.ai.base_client.sanitize_error`.
_SECRET_RE = re.compile(r"sk-[\w-]{10,}")
CONTRACT_DEFINITIE = "definitie"
CONTRACT_CONFLICT = "conflict"
CONTRACT_NA_VERDUIDELIJKING = "definitie_na_verduidelijking"

#: Twee synthetische documentbronnen met een tegengestelde betekenislaag;
#: letterlijk overgenomen uit `tests/unit/services/prompts/
#: test_def750_ess02_promptnorm.py::CONFLICTBRONNEN` (bestaande regressietest).
#: Deze broncase staat níet in het casusregister (v1); E2-03 daaruit
#: (type-label versus activiteitkern) is door het niveau/aard-overlapbesluit
#: géén werkelijke tegenspraak en wordt bewust niet als conflict getoetst.
CONFLICTBRONNEN: tuple[dict[str, Any], ...] = (
    {
        "provider": "documents",
        "doc_id": "doc-activiteit",
        "filename": "handboek.txt",
        "title": "handboek.txt",
        "snippet": (
            "Registratie is de activiteit waarbij meetwaarden in het register "
            "worden vastgelegd."
        ),
        "score": 1.0,
        "selection_basis": "term_match",
    },
    {
        "provider": "documents",
        "doc_id": "doc-uitkomst",
        "filename": "besluit.txt",
        "title": "besluit.txt",
        "snippet": (
            "Onder registratie wordt uitsluitend de uitkomst verstaan: de in het "
            "register vastgelegde meetwaarden."
        ),
        "score": 1.0,
        "selection_basis": "term_match",
    },
)

#: De expliciete verduidelijking voor de hergeneratie na het conflict:
#: synthetische gebruikersbedoeling, geen bronfeit.
VERDUIDELIJKING_C3 = (
    "Bedoeld wordt de activiteit van het vastleggen; het vastgelegde resultaat "
    "is een afzonderlijk begrip."
)

REGISTER = (
    "docs/analyses/ess02-20260916-samenwerking/casusregister-geintegreerd-v1.json "
    "(synthetisch; geen juridische goldset)"
)

#: Ronde 2: één synthetische, gewone bron die de activiteit beschrijft zonder
#: het begrip te definiëren of een verwachting/instructie te dragen. Dezelfde
#: inhoudelijke grond voor de categorieën proces en type.
ACTIVITEITSBRON: tuple[dict[str, Any], ...] = (
    {
        "provider": "documents",
        "doc_id": "doc-werkinstructie",
        "filename": "werkinstructie.txt",
        "title": "werkinstructie.txt",
        "snippet": (
            "Bij de registratie leest de medewerker de meetwaarden van de sensor "
            "af, controleert het meetnummer en legt de waarden vervolgens in het "
            "register vast."
        ),
        "score": 1.0,
        "selection_basis": "term_match",
    },
)
#: Harde bovengrens voor ronde 2 (coördinatorbesluit 17-09-2026).
MAX_LIVE_CALLS_R2 = 5


@dataclass(frozen=True)
class GeneratieCasus:
    """Eén live-casus: invoer voor de app én de vooraf vastgelegde betekenistoets."""

    id: str
    begrip: str
    ontologische_categorie: str | None
    organisatorische_context: tuple[str, ...]
    herkomst: str
    contract: str
    #: Vooraf vastgelegde verwachting (menselijke betekenistoets); nooit in de prompt.
    verwachting: str
    documenten: tuple[dict[str, Any], ...] = ()
    betekenisverduidelijking: str | None = None
    #: Verwijst naar de casus waarvan dit de hergeneratie is (zelfde invoer).
    vervolg_op: str | None = None


#: Live-casussen in vaste volgorde; samen precies MAX_LIVE_CALLS aanroepen.
LIVE_CASUSSEN: tuple[GeneratieCasus, ...] = (
    GeneratieCasus(
        id="E02-001",
        begrip="dossierstuk",
        ontologische_categorie=None,
        organisatorische_context=("Archiefdienst",),
        herkomst=f"{REGISTER} E02-001 (labelvrij: geen categorie opgegeven)",
        contract=CONTRACT_DEFINITIE,
        verwachting=(
            "Heldere documentkern (genus document + onderscheidend kenmerk) "
            "zonder markerwoord; geen geforceerd conflict; voldoet op de "
            "betekenisgrens zonder categorielabel."
        ),
    ),
    GeneratieCasus(
        id="E02-002-proces",
        begrip="registratie",
        ontologische_categorie="proces",
        organisatorische_context=("Meetdienst",),
        herkomst=f"{REGISTER} E02-002 (categorie proces)",
        contract=CONTRACT_DEFINITIE,
        verwachting=(
            "Generieke activiteit als kern (het registreren), niet de "
            "vastgelegde waarden; geen vermenging activiteit/uitkomst."
        ),
    ),
    GeneratieCasus(
        id="E02-002-type",
        begrip="registratie",
        ontologische_categorie="type",
        organisatorische_context=("Meetdienst",),
        herkomst=f"{REGISTER} E02-002 (categorie type: overlap type/proces)",
        contract=CONTRACT_DEFINITIE,
        verwachting=(
            "Type + activiteit voldoet: overlap type/proces is geen conflict; "
            "geen conflictmelding, geen gemengde kern."
        ),
    ),
    GeneratieCasus(
        id="E02-004",
        begrip="registratie",
        ontologische_categorie="proces",
        organisatorische_context=("Meetdienst",),
        herkomst=f"{REGISTER} E02-004 (activiteit met resultaatrelatie)",
        contract=CONTRACT_DEFINITIE,
        verwachting=(
            "Activiteit als kern; een genoemd resultaat is gerelateerd object, "
            "geen tweede kern; geen afkeur enkel wegens proces- én resultaatwoorden."
        ),
    ),
    GeneratieCasus(
        id="E02-003",
        begrip="registratie",
        ontologische_categorie="resultaat",
        organisatorische_context=("Meetdienst",),
        herkomst=f"{REGISTER} E02-003 (categorie resultaat)",
        contract=CONTRACT_DEFINITIE,
        verwachting=(
            "Uitkomst als kern (het vastgelegde), niet de handeling; geen "
            "vermenging."
        ),
    ),
    GeneratieCasus(
        id="E02-009",
        begrip="meting M-17",
        ontologische_categorie="exemplaar",
        organisatorische_context=("Meetdienst",),
        herkomst=f"{REGISTER} E02-009 (specifiek voorval)",
        contract=CONTRACT_DEFINITIE,
        verwachting=(
            "Eén specifieke gebeurtenis met behoud van de procesaard; geen "
            "verzonnen identificatie (tijd/sensor komen niet uit de invoer); "
            "het woord exemplaar is niet vereist."
        ),
    ),
    GeneratieCasus(
        id="C3-CONFLICTBRONNEN",
        begrip="registratie",
        ontologische_categorie=None,
        organisatorische_context=("Meetdienst",),
        herkomst=(
            "tests/unit/services/prompts/test_def750_ess02_promptnorm.py::"
            "CONFLICTBRONNEN (handboek.txt: activiteit; besluit.txt: uitsluitend "
            "de uitkomst) — niet in het casusregister"
        ),
        contract=CONTRACT_CONFLICT,
        verwachting=(
            "Werkelijke tegenspraak tussen twee aangeleverde bronnen: het model "
            "meldt een verduidelijkingsvraag met ≥ 2 lezingen, elk gegrond op "
            "bron 1/bron 2; geen definitie, niets opgeslagen, geen samensmelting."
        ),
        documenten=CONFLICTBRONNEN,
    ),
    GeneratieCasus(
        id="C3-CONFLICTBRONNEN-verduidelijkt",
        begrip="registratie",
        ontologische_categorie=None,
        organisatorische_context=("Meetdienst",),
        herkomst="hergeneratie van C3-CONFLICTBRONNEN met expliciete verduidelijking",
        contract=CONTRACT_NA_VERDUIDELIJKING,
        verwachting=(
            "De verduidelijking staat volledig als DATA in de nieuwe prompt; het "
            "model definieert de activiteit van het vastleggen (gekozen "
            "betekenis behouden), zonder het resultaat als tweede kern, zonder "
            "de bronnen te herschrijven en zonder nieuw conflict."
        ),
        documenten=CONFLICTBRONNEN,
        betekenisverduidelijking=VERDUIDELIJKING_C3,
        vervolg_op="C3-CONFLICTBRONNEN",
    ),
)

#: Ronde 2 (na de promptcorrecties uit live-run-1): dezelfde conflictroute en
#: de activiteitcasussen met een inhoudelijke activiteitsbron; ≤ MAX_LIVE_CALLS_R2.
LIVE_CASUSSEN_R2: tuple[GeneratieCasus, ...] = (
    LIVE_CASUSSEN[6],
    LIVE_CASUSSEN[7],
    GeneratieCasus(
        id="E02-004-r2",
        begrip="registratie",
        ontologische_categorie="proces",
        organisatorische_context=("Meetdienst",),
        herkomst=f"{REGISTER} E02-004 (proces) + ACTIVITEITSBRON (werkinstructie.txt)",
        contract=CONTRACT_DEFINITIE,
        verwachting=LIVE_CASUSSEN[3].verwachting,
        documenten=ACTIVITEITSBRON,
    ),
    GeneratieCasus(
        id="E02-002-type-r2",
        begrip="registratie",
        ontologische_categorie="type",
        organisatorische_context=("Meetdienst",),
        herkomst=(
            f"{REGISTER} E02-002 (type) + ACTIVITEITSBRON (werkinstructie.txt): "
            "zelfde inhoudelijke grond als E02-004-r2 (proces)"
        ),
        contract=CONTRACT_DEFINITIE,
        verwachting=(
            "Zelfde activiteitkern als bij proces (labelwissel verandert de "
            "betekenis niet); geen conflictmelding, geen gemengde kern, geen "
            "ambigu 'vastlegging' als enige kern."
        ),
        documenten=ACTIVITEITSBRON,
    ),
)


@dataclass(frozen=True)
class ToetsCasus:
    """Alleen-toetsen: de exacte aangeleverde tekst door de echte ESS-02-regel."""

    id: str
    begrip: str
    tekst: str
    metadata: dict[str, Any]
    herkomst: str
    verwachting: str


TOETS_CASUSSEN: tuple[ToetsCasus, ...] = (
    ToetsCasus(
        "E02-005",
        "registratie",
        "activiteit of resultaat van het vastleggen van meetwaarden",
        {},
        f"{REGISTER} E02-005 (gemengde kern)",
        "Signaal op de gemengde kern; review_required zonder cijfer; geen autoherstel.",
    ),
    ToetsCasus(
        "E02-006",
        "registratie",
        "activiteit of resultaat van het vastleggen van meetwaarden",
        {"marker": "proces"},
        f"{REGISTER} E02-006 (marker als geruststelling)",
        "Marker geeft geen vrijstelling: geen pass, review_required blijft.",
    ),
    ToetsCasus(
        "E02-007",
        "registratie",
        "activiteit waarbij meetwaarden in een register worden vastgelegd",
        {"ontologische_categorie": "resultaat"},
        f"{REGISTER} E02-007 (label resultaat, kern activiteit)",
        "Geen automatische label- of tekstwijziging; conflict blijft menselijk oordeel.",
    ),
    ToetsCasus(
        "E02-010",
        "meetrapport R-17",
        "exemplaar van een rapport dat het resultaat van meting M-17 vastlegt",
        {},
        f"{REGISTER} E02-010 (particulier/resultaat-overlap)",
        "Geen afkeur wegens twee categoriehits; geen automatisch positief oordeel.",
    ),
    ToetsCasus(
        "E02-011",
        "lege-invoer",
        "",
        {"marker": "type"},
        f"{REGISTER} E02-011 (leeg + marker)",
        "Geen positieve ESS-02-beoordeling uit een label; lege invoer apart (VAL-EMP-001).",
    ),
    ToetsCasus(
        "E02-013",
        "observatie",
        "manier om gegevens te verzamelen",
        {},
        f"{REGISTER} E02-013 (lage zekerheid, betekenis onbepaald)",
        "Nog te beoordelen; geen verplicht woord geëist, geen verzonnen keuze.",
    ),
    ToetsCasus(
        "E2-16",
        "observatie",
        "Observatie is een manier om gegevens te verzamelen.",
        {"marker": "type"},
        f"{REGISTER} E2-16 (marker type op zin met kopregel)",
        "Marker is geen bewijs: geen pass door marker; invoerbytes ongewijzigd.",
    ),
)


# ---------------------------------------------------------------------------
# Registrerende client: alles wat de app naar het model stuurt en terugkrijgt.
# ---------------------------------------------------------------------------


class LiveBudgetOverschredenError(RuntimeError):
    """Geen `AIClientError`-subklasse: de retry-lus van AsyncGPTClient mag niet herhalen."""


@dataclass
class ModelAanroep:
    volgnummer: int
    model_gevraagd: str
    temperature: float
    max_tokens: int
    timeout: float | None
    messages: list[dict[str, str]]
    prompt_sha256: str
    prompt_lengte: int
    gestart_utc: str
    duur_s: float | None = None
    respons_tekst: str | None = None
    respons_model: str | None = None
    tokens_used: int | None = None
    respons_metadata: dict[str, Any] = field(default_factory=dict)
    sdk: dict[str, Any] = field(default_factory=dict)
    fout: str | None = None

    @property
    def afgekapt(self) -> bool | None:
        reden = self.sdk.get("stop_reason") or self.sdk.get("finish_reason")
        if reden is None:
            return None
        return reden in ("max_tokens", "length")


class RegistrerendeClient:
    """AsyncAIClient-proxy: registreert elke aanroep en bewaakt het budget.

    Gedrag van de echte client blijft ongewijzigd (zelfde messages, model,
    parameters, fouten); alleen de waarneming komt erbij.
    """

    def __init__(self, echt: Any, budget: int) -> None:
        self._echt = echt
        self._budget = budget
        self.aanroepen: list[ModelAanroep] = []
        self.sdk_max_retries: int | None = None
        self._koppel_sdk_registratie()

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
        prompt = "\n".join(m.content for m in messages)
        aanroep = ModelAanroep(
            volgnummer=len(self.aanroepen) + 1,
            model_gevraagd=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            prompt_sha256=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            prompt_lengte=len(prompt),
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
            aanroep.fout = f"{type(exc).__name__}: {scrub(str(exc))}"
            raise
        aanroep.duur_s = time.monotonic() - start
        aanroep.respons_tekst = respons.text
        aanroep.respons_model = respons.model
        aanroep.tokens_used = respons.tokens_used
        aanroep.respons_metadata = dict(respons.metadata or {})
        return respons

    async def close(self) -> None:
        await self._echt.close()

    def _koppel_sdk_registratie(self) -> None:
        """Lees stop_reason/usage van de ruwe SDK-respons mee (waar beschikbaar).

        Anthropic: `_client.messages.create`; OpenAI: `_client.chat.completions.create`.
        De respons wordt ongewijzigd doorgegeven; ontbreekt de structuur, dan
        blijft `sdk` leeg en wordt afkapping als 'onbekend' gerapporteerd.
        """
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
            naam: getattr(usage, naam, None)
            for naam in (
                "input_tokens",
                "output_tokens",
                "prompt_tokens",
                "completion_tokens",
                "total_tokens",
            )
            if getattr(usage, naam, None) is not None
        }
    return meta


# ---------------------------------------------------------------------------
# Hulpfuncties
# ---------------------------------------------------------------------------


def scrub(tekst: str) -> str:
    """Verwijder API-sleutelpatronen uit alles wat naar schijf gaat."""
    return _SECRET_RE.sub("[REDACTED]", tekst)


def schrijf_json(pad: Path, data: Any) -> None:
    pad.parent.mkdir(parents=True, exist_ok=True)
    tekst = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    pad.write_text(scrub(tekst), encoding="utf-8")


def git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "onbekend"


def bevestig_buiten_productie(db_pad: Path) -> None:
    """Weiger elke DB onder `data/` van het project of een bestaand bestand."""
    productie = (ROOT / "data").resolve()
    pad = db_pad.resolve()
    if pad == productie or productie in pad.parents:
        msg = f"DB-pad {pad} ligt onder de projectdata; alleen een tijdelijke DB"
        raise SystemExit(msg)
    if pad.exists():
        msg = f"DB-pad {pad} bestaat al; geen bestaand bewijs overschrijven"
        raise SystemExit(msg)


def ess02_uit(validation_result: Any) -> dict[str, Any]:
    """Compacte ESS-02-uitkomst uit een validatieresultaat (dict-contract)."""
    if not isinstance(validation_result, dict):
        return {"beschikbaar": False}
    statuses = validation_result.get("rule_statuses") or {}
    review = [
        r
        for r in (validation_result.get("review_required") or [])
        if isinstance(r, dict) and r.get("rule_id") == "ESS-02"
    ]
    return {
        "beschikbaar": True,
        "status": statuses.get("ESS-02"),
        "in_passed_rules": "ESS-02" in (validation_result.get("passed_rules") or []),
        "violation": any(
            isinstance(v, dict) and v.get("code") == "ESS-02"
            for v in (validation_result.get("violations") or [])
        ),
        "reason": review[0].get("reason") if review else None,
        "overall_score": validation_result.get("overall_score"),
        "validation_status": validation_result.get("validation_status"),
    }


def _toets_uitkomst(naam: str, ok: bool, detail: str = "") -> dict[str, Any]:
    return {"toets": naam, "ok": bool(ok), "detail": detail}


def automatische_toetsen(
    casus: GeneratieCasus,
    response: Any,
    aanroep: ModelAanroep | None,
    records_voor: int,
    records_na: int,
) -> list[dict[str, Any]]:
    """Contracttoetsen op de app-uitkomst — géén inhoudelijk betekenisoordeel."""
    meta = dict(response.metadata or {})
    uit: list[dict[str, Any]] = []
    if aanroep is not None:
        uit.append(
            _toets_uitkomst(
                "respons niet afgekapt",
                aanroep.afgekapt is False,
                f"stop_reason={aanroep.sdk.get('stop_reason') or aanroep.sdk.get('finish_reason')!r}",
            )
        )
    if casus.contract == CONTRACT_CONFLICT:
        conflict = meta.get("betekenisconflict") or {}
        lezingen = conflict.get("lezingen") or []
        bronnen = {str(lz.get("bron")) for lz in lezingen if isinstance(lz, dict)}
        uit += [
            _toets_uitkomst("success is False", response.success is False),
            _toets_uitkomst(
                "error_type == betekenisconflict",
                meta.get("error_type") == "betekenisconflict",
                f"error_type={meta.get('error_type')!r}",
            ),
            _toets_uitkomst("vraag aanwezig", bool(conflict.get("vraag"))),
            _toets_uitkomst(
                "minstens 2 lezingen", len(lezingen) >= 2, f"{len(lezingen)} lezingen"
            ),
            _toets_uitkomst(
                "gronden verwijzen naar bron 1/bron 2",
                bool(bronnen) and bronnen <= {"bron 1", "bron 2"},
                f"bronnen={sorted(bronnen)}",
            ),
            _toets_uitkomst("geen definitie", response.definition is None),
            _toets_uitkomst(
                "niets opgeslagen",
                records_na == records_voor,
                f"{records_voor}→{records_na}",
            ),
        ]
        return uit
    definitie = getattr(response.definition, "definitie", "") or ""
    ess02 = ess02_uit(response.validation_result)
    uit += [
        _toets_uitkomst(
            "success is True",
            response.success is True,
            f"error_type={meta.get('error_type')!r} error={scrub(str(response.error))!r}",
        ),
        _toets_uitkomst("geen betekenisconflict", "betekenisconflict" not in meta),
        _toets_uitkomst("definitie niet leeg", bool(definitie.strip())),
        _toets_uitkomst(
            "ESS-02 review_required, geen pass/violation/cijfer",
            ess02.get("status") == "review_required"
            and not ess02.get("in_passed_rules")
            and not ess02.get("violation"),
            f"status={ess02.get('status')!r} overall_score={ess02.get('overall_score')!r}",
        ),
        _toets_uitkomst(
            "opgeslagen als concept in de proef-DB",
            records_na == records_voor + 1,
            f"{records_voor}→{records_na}",
        ),
    ]
    if casus.contract == CONTRACT_NA_VERDUIDELIJKING:
        from services.prompts.modules.context_awareness_module import (
            verduidelijking_datalijn,
        )

        prompt = aanroep.messages[-1]["content"] if aanroep else ""
        uit += [
            _toets_uitkomst(
                "betekenisverduidelijking_gebruikt",
                meta.get("betekenisverduidelijking_gebruikt") is True,
            ),
            _toets_uitkomst(
                "verduidelijking volledig als DATA-regel in de prompt",
                verduidelijking_datalijn(casus.betekenisverduidelijking or "")
                in prompt,
            ),
            _toets_uitkomst(
                "bronnen ongewijzigd in de prompt",
                all(b["snippet"] in prompt for b in casus.documenten),
            ),
        ]
    return uit


# ---------------------------------------------------------------------------
# Keten opbouwen
# ---------------------------------------------------------------------------


def _schakel_voorbeelden_uit() -> None:
    """Seam: geen voorbeeldgeneratie (aparte modelaanroepen, buiten scope)."""
    from voorbeelden import unified_voorbeelden

    async def _geen(**_: Any) -> dict[str, Any]:
        return {}

    unified_voorbeelden.genereer_alle_voorbeelden_async = _geen  # type: ignore[assignment]


def maak_proefclient(provider: str, api_key: str, budget: int) -> RegistrerendeClient:
    """De echte app-client (via `create_ai_client`) achter de registrerende proxy,
    met SDK-interne retries uit.

    Codex-review P2 (17-09-2026): de proxy telt `chat_completion`-aanroepen,
    maar de SDK deed daarbinnen standaard nog twee eigen retries (budget 1 →
    drie transportpogingen). Voor deze opt-in proef gaat de bestaande
    factory-knop `AI_SDK_MAX_RETRIES` (DEF-566, alleen dit proces) op 0 en
    wordt dat fail-closed op de SDK-client geverifieerd; het productbeleid
    (default 2) blijft ongewijzigd. Eén geregistreerde aanroep is zo precies
    één poging op het netwerk.
    """
    from services.ai import create_ai_client

    os.environ["AI_SDK_MAX_RETRIES"] = "0"
    echt = create_ai_client(provider=provider, api_key=api_key)
    sdk_max_retries = getattr(getattr(echt, "_client", None), "max_retries", None)
    if sdk_max_retries != 0:
        msg = (
            f"SDK-retries niet uitgeschakeld voor provider {provider!r} "
            f"(max_retries={sdk_max_retries!r}); proef niet gestart"
        )
        raise SystemExit(msg)
    client = RegistrerendeClient(echt, budget)
    client.sdk_max_retries = sdk_max_retries
    return client


def bouw_ai_service(live: bool, budget: int) -> tuple[Any, Any, dict[str, Any]]:
    """Echte, geconfigureerde ModelRouter/AIServiceV2 (cache uit) — één keer per
    run, zodat het budget over alle casussen geldt.

    Geeft (ai_service, registrerende client of None, modelinfo) terug.
    """
    from config.config_manager import get_config_manager
    from services.ai.model_router import ModelRouter
    from services.ai_service_v2 import AIServiceV2
    from toetsregels.rule_cache import get_rule_cache

    get_rule_cache().clear_cache()
    _schakel_voorbeelden_uit()

    config = get_config_manager()
    router = ModelRouter.from_config()
    provider, model = router.get_model("definition_core")
    modelinfo = {
        "provider_geconfigureerd": config.api.ai_provider,
        "provider_router": provider,
        "model_definition_core": model,
        "temperature_bron": "get_prompt_temperature('definition')",
        "max_tokens": 500,
        "timeout_seconds": 30,
        "cache": False,
    }

    client: Any = None
    if live:
        key = (
            config.api.anthropic_api_key
            if config.api.ai_provider == "anthropic"
            else config.api.openai_api_key
        )
        if not key:
            msg = (
                f"geen API-key voor provider {config.api.ai_provider!r} via de "
                "runtime-loader; geef --dotenv of zet de omgevingsvariabele"
            )
            raise SystemExit(msg)
        client = maak_proefclient(config.api.ai_provider, key, budget)
        del key
        modelinfo["sdk_max_retries"] = client.sdk_max_retries
        ai_service: Any = AIServiceV2(
            use_cache=False, ai_client=client, model_router=router
        )
    else:
        ai_service = _OfflineAIService()
    return ai_service, client, modelinfo


def bouw_orchestrator(db_pad: Path, ai_service: Any) -> Any:
    """Echte PromptServiceV2, echte ModularValidationService, echte
    SecurityService en een verse SQLite op `db_pad`.

    Per casus een eigen DB: de duplicaatwacht van de app (zelfde begrip en
    context) mag geen tweede casus blokkeren; alleen een hergeneratie deelt
    bewust de DB van haar voorganger.
    """
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

    bevestig_buiten_productie(db_pad)
    repository = DefinitionRepository(str(db_pad))
    cleaning = CleaningService(CleaningConfig())
    validatie = ValidationOrchestratorV2(
        validation_service=ModularValidationService(
            get_cached_toetsregel_manager(),
            None,
            ValidationConfig.from_yaml(str(SRC / "config" / "validation_rules.yaml")),
            repository=repository,
        ),
        cleaning_service=cleaning,
        source_assessment_service=None,  # seam: geen AI-bronbeoordeling (CON-02)
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
        source_assessment_service=validatie.source_assessment_service,
    )


class _OfflineAIService:
    """Dry-run: de echte prompt wordt gebouwd, daarna stopt de keten vóór het model."""

    def __init__(self) -> None:
        self.prompts: list[str] = []

    async def generate_definition(self, prompt: str, **kwargs: Any) -> Any:
        self.prompts.append(prompt)
        msg = "offline: geen modelaanroep (gebruik --live)"
        raise OfflineStopError(msg)


class OfflineStopError(RuntimeError):
    """Markeert de bewuste stop vóór de modelaanroep in de dry-run."""


def maak_request(casus: GeneratieCasus) -> Any:
    from services.interfaces import GenerationRequest

    return GenerationRequest(
        id=f"ess02-proef-{casus.id}",
        begrip=casus.begrip,
        ontologische_categorie=casus.ontologische_categorie,
        organisatorische_context=list(casus.organisatorische_context),
        juridische_context=[],
        wettelijke_basis=[],
        actor="ess02_praktijkproef",
        betekenisverduidelijking=casus.betekenisverduidelijking,
    )


def maak_context(casus: GeneratieCasus) -> dict[str, Any] | None:
    if not casus.documenten:
        return None
    return {
        "documents": {
            "snippets": [dict(d) for d in casus.documenten],
            "selected_ids": [d["doc_id"] for d in casus.documenten],
        }
    }


def aantal_records(db_pad: Path, begrip: str) -> int:
    import sqlite3

    with sqlite3.connect(str(db_pad)) as conn:
        (aantal,) = conn.execute(
            "SELECT COUNT(*) FROM definities WHERE begrip = ?", (begrip,)
        ).fetchone()
    return int(aantal)


def _registratie_van(db_pad: Path, definition_id: int | None) -> dict[str, Any] | None:
    if not definition_id:
        return None
    from database.definitie_repository import DefinitieRepository

    record = DefinitieRepository(str(db_pad)).get_definitie(int(definition_id))
    if record is None:
        return None
    registratie = record.get_generatieregistratie() or {}
    return {
        "id": record.id,
        "definitie": record.definitie,
        "categorie": record.categorie,
        "status": getattr(record, "status", None),
        "betekenisverduidelijking": registratie.get("betekenisverduidelijking"),
        "prompt_bevat_verduidelijking": bool(
            registratie.get("betekenisverduidelijking")
            and registratie.get("betekenisverduidelijking")
            in (registratie.get("prompt") or "")
        ),
    }


# ---------------------------------------------------------------------------
# Uitvoering
# ---------------------------------------------------------------------------


async def voer_generatie_uit(
    casus: GeneratieCasus,
    orchestrator: Any,
    client: RegistrerendeClient | None,
    db_pad: Path,
    uitmap: Path,
    live: bool,
) -> dict[str, Any]:
    from services.modelantwoord import lees_modelantwoord

    records_voor = aantal_records(db_pad, casus.begrip)
    aanroepen_voor = len(client.aanroepen) if client else 0
    verslag: dict[str, Any] = {
        "casus": asdict(casus),
        "modus": "live" if live else "offline",
        "gestart_utc": datetime.now(UTC).isoformat(),
    }
    start = time.monotonic()
    response = await orchestrator.create_definition(
        maak_request(casus), context=maak_context(casus)
    )
    verslag["duur_s"] = round(time.monotonic() - start, 3)
    meta = dict(response.metadata or {})
    nieuwe = client.aanroepen[aanroepen_voor:] if client else []
    aanroep = nieuwe[-1] if nieuwe else None

    # De orchestrator vangt elke uitzondering en geeft haar als
    # `Generation failed: …` terug; dat is een infrastructurele blokkade
    # (offline-stop, budget, auth/netwerk), geen functionele uitkomst.
    if meta.get("error_type") == OfflineStopError.__name__:
        prompt = orchestrator.ai_service.prompts[-1]
        verslag.update(
            {
                "uitkomst": "OFFLINE",
                "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                "prompt_lengte": len(prompt),
                "prompt_bevat_verwachting": casus.verwachting in prompt,
            }
        )
        (uitmap / f"{casus.id}.prompt.txt").write_text(scrub(prompt), encoding="utf-8")
        return verslag
    if str(response.error or "").startswith("Generation failed:"):
        verslag.update(
            {
                "uitkomst": "BLOCKED",
                "reden": f"{meta.get('error_type')}: {scrub(str(response.error))}",
                "aantal_modelaanroepen": len(nieuwe),
                "aanroepen": [asdict(a) for a in nieuwe],
                "afgekapt": aanroep.afgekapt if aanroep else None,
            }
        )
        _schrijf_prompt_en_respons(uitmap, casus.id, aanroep)
        return verslag

    records_na = aantal_records(db_pad, casus.begrip)
    toetsen = automatische_toetsen(casus, response, aanroep, records_voor, records_na)
    definitie_id = getattr(response.definition, "id", None)
    verslag.update(
        {
            "uitkomst": "PASS" if all(t["ok"] for t in toetsen) else "FAIL",
            "aantal_modelaanroepen": len(nieuwe),
            "aanroepen": [asdict(a) for a in nieuwe],
            "afgekapt": aanroep.afgekapt if aanroep else None,
            "parser": (
                {
                    "soort": lees_modelantwoord(aanroep.respons_tekst or "").soort,
                    "code": lees_modelantwoord(aanroep.respons_tekst or "").code,
                }
                if aanroep and aanroep.respons_tekst is not None
                else None
            ),
            "response": {
                "success": response.success,
                "error": scrub(str(response.error)) if response.error else None,
                "error_type": meta.get("error_type"),
                "definitie": getattr(response.definition, "definitie", None),
                "ontologische_categorie": getattr(
                    response.definition, "ontologische_categorie", None
                ),
                "betekenisconflict": meta.get("betekenisconflict"),
                "betekenisverduidelijking_gebruikt": meta.get(
                    "betekenisverduidelijking_gebruikt"
                ),
                "code": meta.get("code"),
                "reden": meta.get("reden"),
            },
            "ess02": ess02_uit(response.validation_result),
            "record": _registratie_van(db_pad, definitie_id),
            "prompt_bevat_verwachting": bool(
                aanroep and casus.verwachting in aanroep.messages[-1]["content"]
            ),
            "toetsen": toetsen,
            "menselijke_observatie": None,
        }
    )
    _schrijf_prompt_en_respons(uitmap, casus.id, aanroep)
    return verslag


def _schrijf_prompt_en_respons(
    uitmap: Path, casus_id: str, aanroep: ModelAanroep | None
) -> None:
    if aanroep is None:
        return
    (uitmap / f"{casus_id}.prompt.txt").write_text(
        scrub(aanroep.messages[-1]["content"]), encoding="utf-8"
    )
    if aanroep.respons_tekst is not None:
        (uitmap / f"{casus_id}.respons.txt").write_text(
            scrub(aanroep.respons_tekst), encoding="utf-8"
        )


async def voer_toetsing_uit(casus: ToetsCasus) -> dict[str, Any]:
    """Exacte tekst door de echte regelset; invoerbytes en oordeelgrens bewaakt."""
    from services.validation.modular_validation_service import (
        ModularValidationService,
    )
    from toetsregels.manager import get_toetsregel_manager

    invoer_bytes = casus.tekst.encode("utf-8")
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    result = await svc.validate_definition(
        begrip=casus.begrip,
        text=casus.tekst,
        context={"organisatorisch": ["uitvoering"], **casus.metadata},
    )
    ess02 = ess02_uit(result)
    tekstvelden = {
        k: result.get(k)
        for k in ("cleaned_text", "text", "definition_text", "suggested_text")
        if k in result
    }
    toetsen = [
        _toets_uitkomst(
            "invoerbytes ongewijzigd", casus.tekst.encode("utf-8") == invoer_bytes
        ),
        _toets_uitkomst(
            "geen tekst teruggegeven die van de invoer afwijkt (geen autoherstel)",
            all(v in (None, casus.tekst) for v in tekstvelden.values()),
            f"tekstvelden={list(tekstvelden)}",
        ),
        _toets_uitkomst(
            "ESS-02 review_required",
            ess02.get("status") == "review_required",
            f"status={ess02.get('status')!r}",
        ),
        _toets_uitkomst(
            "ESS-02 niet in passed_rules", not ess02.get("in_passed_rules")
        ),
        _toets_uitkomst("ESS-02 geen violation", not ess02.get("violation")),
        _toets_uitkomst("geen cijfer (no_score)", ess02.get("overall_score") is None),
        _toets_uitkomst(
            "reden zonder positief oordeel",
            "voldoet"
            not in (ess02.get("reason") or "").lower().replace("voldoet niet", ""),
        ),
    ]
    return {
        "casus": asdict(casus),
        "uitkomst": "PASS" if all(t["ok"] for t in toetsen) else "FAIL",
        "ess02": ess02,
        "toetsen": toetsen,
        "menselijke_observatie": None,
    }


def samenvatting(
    verslagen: list[dict[str, Any]], toetsingen: list[dict[str, Any]]
) -> str:
    regels = [
        "| casus | contract | uitkomst | modelaanroepen | afgekapt | ESS-02 | opmerking |",
        "|---|---|---|---|---|---|---|",
    ]
    for v in verslagen:
        c = v["casus"]
        resp = v.get("response") or {}
        opm = resp.get("error_type") or v.get("reden") or ""
        regels.append(
            f"| {c['id']} | {c['contract']} | {v['uitkomst']} | "
            f"{v.get('aantal_modelaanroepen', 0)} | {v.get('afgekapt')} | "
            f"{(v.get('ess02') or {}).get('status')} | {scrub(str(opm))[:80]} |"
        )
    regels += [
        "",
        "| toetscasus | uitkomst | ESS-02 | reden (begin) |",
        "|---|---|---|---|",
    ]
    for t in toetsingen:
        regels.append(
            f"| {t['casus']['id']} | {t['uitkomst']} | {t['ess02'].get('status')} | "
            f"{(t['ess02'].get('reason') or '')[:70]} |"
        )
    return "\n".join(regels) + "\n"


async def hoofd(args: argparse.Namespace) -> int:
    uitmap = Path(args.out)
    if uitmap.exists():
        msg = f"uitvoermap {uitmap} bestaat al; kies een nieuwe map"
        raise SystemExit(msg)
    uitmap.mkdir(parents=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(uitmap / "runner.log", encoding="utf-8")],
    )

    if args.dotenv:
        from config.dotenv_loader import load_project_dotenv

        geladen = load_project_dotenv(pad=Path(args.dotenv))
        logger.info("dotenv geladen via runtime-loader: %s", geladen)

    ronde_casussen, ronde_max = (
        (LIVE_CASUSSEN_R2, MAX_LIVE_CALLS_R2)
        if args.ronde == 2
        else (LIVE_CASUSSEN, MAX_LIVE_CALLS)
    )
    budget = min(int(args.max_calls), ronde_max)
    geselecteerd = [
        c for c in ronde_casussen if not args.casus or c.id in set(args.casus)
    ]
    ai_service, client, modelinfo = bouw_ai_service(args.live, budget)
    manifest: dict[str, Any] = {
        "source_sha": git_sha(),
        "sessie": args.sessie or os.getenv("CLAUDE_SESSION_ID") or None,
        "gestart_utc": datetime.now(UTC).isoformat(),
        "modus": "live" if args.live else "offline",
        "ronde": args.ronde,
        "budget_modelaanroepen": budget if args.live else 0,
        "max_live_calls_hard": ronde_max,
        "db": f"{uitmap}/<casus-id>.db (per casus; hergeneratie deelt de DB van haar voorganger)",
        "model": modelinfo,
        "seams_vervangen": [
            "synonym_orchestrator=None",
            "web_lookup_service=None",
            "rag_service=None",
            "voorbeelden.genereer_alle_voorbeelden_async → {}",
            "source_assessment_service=None (CON-02 AI-bronbeoordeling uit)",
            "UI-handler/ServiceAdapter buiten de lus (documenten via context['documents'])",
        ],
        "casussen_live": [c.id for c in geselecteerd],
        "casussen_toetsing": [c.id for c in TOETS_CASUSSEN],
    }
    schrijf_json(uitmap / "manifest.json", manifest)

    verslagen: list[dict[str, Any]] = []
    overgeslagen: set[str] = set()
    orchestrators: dict[str, Any] = {}
    for casus in geselecteerd:
        if casus.vervolg_op and casus.vervolg_op in overgeslagen:
            verslagen.append(
                {
                    "casus": asdict(casus),
                    "uitkomst": "BLOCKED",
                    "reden": f"voorganger {casus.vervolg_op} leverde geen conflict",
                }
            )
            continue
        db_pad = uitmap / f"{casus.vervolg_op or casus.id}.db"
        orchestrator = orchestrators.get(str(db_pad))
        if orchestrator is None:
            orchestrator = bouw_orchestrator(db_pad, ai_service)
            orchestrators[str(db_pad)] = orchestrator
        verslag = await voer_generatie_uit(
            casus, orchestrator, client, db_pad, uitmap, args.live
        )
        verslag["db"] = str(db_pad)
        verslagen.append(verslag)
        schrijf_json(uitmap / f"{casus.id}.json", verslag)
        if casus.contract == CONTRACT_CONFLICT and verslag["uitkomst"] not in (
            "PASS",
            "OFFLINE",
        ):
            overgeslagen.add(casus.id)

    toetsingen = [await voer_toetsing_uit(t) for t in TOETS_CASUSSEN]
    schrijf_json(uitmap / "toetsing.json", toetsingen)

    if client is not None:
        schrijf_json(
            uitmap / "modelaanroepen.json", [asdict(a) for a in client.aanroepen]
        )
        await client.close()
    manifest["afgerond_utc"] = datetime.now(UTC).isoformat()
    manifest["modelaanroepen_gedaan"] = len(client.aanroepen) if client else 0
    schrijf_json(uitmap / "manifest.json", manifest)
    (uitmap / "samenvatting.md").write_text(
        samenvatting(verslagen, toetsingen), encoding="utf-8"
    )
    sys.stdout.write(samenvatting(verslagen, toetsingen))
    sys.stdout.write(f"\nuitvoer: {uitmap}\n")
    alles_ok = all(v["uitkomst"] in ("PASS", "OFFLINE") for v in verslagen) and all(
        t["uitkomst"] == "PASS" for t in toetsingen
    )
    return 0 if alles_ok else 1


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "--live",
        action="store_true",
        help="doe echte modelaanroepen (default: offline)",
    )
    parser.add_argument(
        "--max-calls",
        type=int,
        default=MAX_LIVE_CALLS,
        help=f"budget voor modelaanroepen (hard maximum {MAX_LIVE_CALLS})",
    )
    parser.add_argument(
        "--dotenv", default=None, help="pad naar een .env voor de runtime-loader"
    )
    parser.add_argument(
        "--out",
        default=f"/tmp/ess02-praktijkproef/{datetime.now(UTC):%Y%m%dT%H%M%SZ}",
        help="nieuwe uitvoermap (mag nog niet bestaan)",
    )
    parser.add_argument("--sessie", default=None, help="sessie-id voor het manifest")
    parser.add_argument(
        "--casus", nargs="*", default=None, help="alleen deze live-casus-id's"
    )
    parser.add_argument(
        "--ronde",
        type=int,
        choices=(1, 2),
        default=1,
        help=f"1 = volledige set (max {MAX_LIVE_CALLS}); 2 = gerichte herverificatie (max {MAX_LIVE_CALLS_R2})",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    sys.exit(asyncio.run(hoofd(parse_args())))
