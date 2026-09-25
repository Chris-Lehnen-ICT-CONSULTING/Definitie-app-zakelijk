"""DEF-770 G24-harnas (runplan-t24-g24-v3 §3) — gescheiden fasen, observeert alleen.

Fasen (elk een eigen aanroep; alleen `count` en `run` raken het netwerk):

1. prepare  — offline, per variant tegen een exacte git-archive-tar. Bouwt per
   invoer het `GenerationRequest` zoals `service_factory` dat doet, past
   `SecurityService.sanitize_request` en de contextvereiste van de
   orchestrator toe, fragmenteert iedere bronpassage en de doelgroep verliesloos
   onder de appgrens per fragment (proefconfig: `PROEF_DOCUMENT_ENV`, gelijk in
   beide armen), normaliseert de fragmenten zoals fase 2.9 van de
   orchestrator en bouwt de prompt met de échte
   `PromptServiceV2.build_generation_prompt` van die variant (tweemaal, met
   een verse service: determinismecontrole). Controleert via de
   source_receipt dat elk fragment gebruikt, niet afgekapt, inhoudelijk gelijk
   aan het aangeleverde en als XML letterlijk in de prompt staat, en dat de
   fragmenten per bron exact de (witruimte-genormaliseerde) bron herbouwen;
   anders exit 1. Model, temperatuur en thinking komen uit de ModelRouter en
   `AnthropicClient._verzendbeleid`-policy van de variant.
2. manifest — zonder applicatiecode: bundelt beide armen, eist gelijke invoer,
   gelijke gesanitiseerde requestvelden, context, proefconfig en
   API-instellingen (alles behalve de prompttekst), en legt invoeren x 2 armen
   x N herhalingen vast met een sha256 per canoniek API-verzoek. Kleine
   smoke-manifesten mogen; de netwerkfasen weigeren ze (`_poort_ontwerp`).
3. count    — NIET in de voorbereidingsbeurt. Alleen voor het vaste ontwerp
   (6 invoeren x 2 armen x 2 herhalingen = 24 calls). `messages.count_tokens`
   per uniek verzoek, max_retries=0, begrensde timeout; raamt de maximale
   kosten.
4. run      — NIET in de voorbereidingsbeurt. Vereist het vaste ontwerp,
   claude-opus-5, max_tokens 1000, plafond <= USD 5 en een schriftelijk
   goedkeuringsbestand dat manifest en counts bij sha256 noemt; de binding
   staat in `run-binding.json`. Per call eerst een duurzame, exclusieve
   aanvraagregistratie, dan pas verzenden; een aanvraag zonder resultaat wordt
   nooit opnieuw verzonden. Sequentieel, geen retries, geen fallback; elk
   resultaat eerst ongewijzigd atomair bewaard, dan getoetst (model,
   stop_reason, usage tegen telling en max_tokens, cumulatieve kosten tegen
   plafond). Elke stop wordt blijvend vastgelegd in `RUN-STOP.json`; een
   herstart gaat dan niet verder.
5. nabewerk — offline, per variant: ruwe tekst -> lees_modelantwoord ->
   opschoning zoals fase 6 van de orchestrator (definitie_origineel via
   opschonen_enhanced, kern via extract_definition_from_gpt_response,
   CleaningService.clean_text). Geen validatie, geen enhancement. Ontbreekt
   een verwacht resultaat, dan is de uitvoer onvolledig (exit 2).

Alle externe paden worden in elke fase opgelost vóór de bronactivering (die
de werkmap wisselt).

Sleutels: alleen uit de omgeving of een opgegeven bestaand .env-bestand;
alleen hun aanwezigheid wordt gemeld, nooit de waarde.
Afwijkingen van de app-keten staan in `AFWIJKINGEN` en in elk artefact.
"""

from __future__ import annotations

import argparse
import asyncio
import dataclasses
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import effectproef_bron as eb

INVOERVELDEN = (
    "id",
    "stratum",
    "begrip",
    "organisatorische_context",
    "juridische_context",
    "wettelijke_basis",
    "bronpassages",
    "bedoelde_betekenis",
    "doelgroep",
    "beschermde_kenmerken",
    "beschermde_namen",
    "beschermde_negaties",
)
LIJSTVELDEN = (
    "organisatorische_context",
    "juridische_context",
    "wettelijke_basis",
    "beschermde_kenmerken",
    "beschermde_namen",
    "beschermde_negaties",
)
#: Velden die nooit naar het model gaan (beoordelaarsinformatie).
NIET_NAAR_MODEL = (
    "stratum",
    "bedoelde_betekenis",
    "beschermde_kenmerken",
    "beschermde_namen",
    "beschermde_negaties",
)
VERWACHT_MODEL = "claude-opus-5"
VERWACHTE_PROVIDER = "anthropic"
TAAKTYPE = "definition_core"  # AIServiceV2.default_model
MAX_TOKENS = 1000
HERHALINGEN = 2
PLAFOND_USD = 5.0
PRIJS_INPUT_PER_MTOK = 5.0
PRIJS_OUTPUT_PER_MTOK = 25.0
DOELGROEP_ID = "doelgroep"
AANTAL_INVOEREN = 6
ARMEN = ("oud", "nieuw")
TOEGESTANE_VERZOEKVELDEN = {
    "model",
    "max_tokens",
    "messages",
    "thinking",
    "temperature",
}
STOPBESTAND = "RUN-STOP.json"
BINDINGBESTAND = "run-binding.json"

#: Appgrens per documentfragment: `_sanitized_passage(raw, max_length=500)` in
#: prompt_service_v2 (oud en nieuw gelijk). Fragmenten blijven er ruim onder.
APP_FRAGMENTGRENS = 500
FRAGMENT_MAX = 450
#: Expliciete, in beide armen identieke proefconfig van het documentkanaal via
#: de ondersteunde env-route (gelezen per aanroep door PromptServiceV2). De
#: productieconfig blijft ongewijzigd; app-default is 16 fragmenten / 800 tekens.
PROEF_DOCUMENT_ENV = {
    "DOCUMENT_SNIPPETS_ENABLED": "true",
    "DOCUMENT_SNIPPETS_MAX": "200",
    "DOCUMENT_SNIPPETS_MAX_CHARS": "40000",
}
WITRUIMTE = re.compile(r"\s+")  # = WS_RE in services/web_lookup/sanitization.py

AFWIJKINGEN = (
    (
        "Alleen de generatiecall: geen feedbackhistorie, synoniemverrijking (AI), "
        "web lookup, RAG, voorbeelden, validatie, ESS/CON-AI-calls of enhancement."
    ),
    (
        "Transport van bronpassages: als geüploade korte documenten (UI-vorm "
        "selection_basis=selected_short_document, score 0.0), title/filename = "
        "herkomst. Iedere passage wordt verliesloos gefragmenteerd tot fragmenten "
        "van ten hoogste FRAGMENT_MAX (450) tekens, onder de appgrens van 500 per "
        "fragment: doc_id '<passage-id>#<k>/<n>', citation_label 'fragment k van "
        "n'. Knippen gebeurt op een spatie (scheiding ' ' vastgelegd) of, zonder "
        "spatie, hard (scheiding ''). Daarna fase-2.9-normalisatie van de "
        "orchestrator nagebouwd (code identiek in oud en nieuw)."
    ),
    (
        "Witruimtenormalisatie vooraf, alleen wat de app zelf doet: "
        "sanitize_snippet vervangt iedere witruimtereeks door één spatie en "
        "stript (WS_RE). Per bron vastgelegd of dit iets wijzigde; de "
        "reconstructie wordt tegen die genormaliseerde bron getoetst."
    ),
    (
        "Doelgroep: de app heeft geen doelgroepveld; doorgegeven als extra "
        "document (bron-id 'doelgroep', tekst 'Doelgroep: <doelgroep>'), op "
        "dezelfde manier gefragmenteerd, na de bronpassages, identiek in beide "
        "armen."
    ),
    (
        "Documentkanaal-proefconfig via env (beide armen identiek): "
        "DOCUMENT_SNIPPETS_MAX=200, DOCUMENT_SNIPPETS_MAX_CHARS=40000 i.p.v. "
        "app-default 16/800. Wordt een fragment weggelaten, afgekapt of "
        "gewijzigd, dan faalt prepare; er is geen terugval naar een andere route."
    ),
    (
        "document_context (UI-samenvatting) = None; options = None; "
        "organisatie = ''; ontologische_categorie = None (niet in het invoerschema)."
    ),
    "max_tokens 1000 i.p.v. app-default 500, alleen in de API-aanroep.",
    (
        "Directe SDK-aanroep (messages.create) met het API-verzoek dat de "
        "AnthropicClient zou sturen: één user-bericht, geen system, temperature en "
        "thinking volgens model_routing.capabilities; max_retries=0 en eigen "
        "begrensde timeout i.p.v. de app-retrylus en 30 s."
    ),
    (
        "Nabewerking offline per variant op de ruwe tekst (tekstblokken met '\\n' "
        "samengevoegd en gestript, zoals AnthropicClient)."
    ),
)

_SLEUTELPATROON = re.compile(r"sk-[A-Za-z0-9_\-]{8,}")


# ---------------------------------------------------------------- invoer


def lees_invoer(pad: Path) -> list[dict[str, Any]]:
    data = json.loads(pad.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise SystemExit("invoer moet een niet-lege JSON-lijst zijn")
    gezien: set[str] = set()
    for i, inv in enumerate(data):
        if not isinstance(inv, dict) or set(inv) != set(INVOERVELDEN):
            raise SystemExit(f"invoer {i}: sleutels moeten exact {INVOERVELDEN} zijn")
        for veld in LIJSTVELDEN:
            if not isinstance(inv[veld], list) or not all(
                isinstance(x, str) for x in inv[veld]
            ):
                raise SystemExit(f"invoer {i}: {veld} moet een lijst tekst zijn")
        for veld in ("id", "stratum", "begrip", "bedoelde_betekenis", "doelgroep"):
            if not isinstance(inv[veld], str):
                raise SystemExit(f"invoer {i}: {veld} moet tekst zijn")
        passages = inv["bronpassages"]
        if not isinstance(passages, list) or not all(
            isinstance(p, dict)
            and set(p) == {"id", "tekst", "herkomst"}
            and all(isinstance(p[k], str) for k in p)
            for p in passages
        ):
            raise SystemExit(
                f"invoer {i}: bronpassages = lijst van {{id,tekst,herkomst}}"
            )
        if any(not app_witruimte(p["tekst"]) for p in passages):
            raise SystemExit(f"invoer {i}: lege bronpassage")
        if any("#" in p["id"] for p in passages):
            raise SystemExit(f"invoer {i}: '#' in passage-id is gereserveerd")
        if DOELGROEP_ID in {p["id"] for p in passages}:
            raise SystemExit(f"invoer {i}: passage-id {DOELGROEP_ID!r} is gereserveerd")
        if inv["id"] in gezien:
            raise SystemExit(f"invoer {i}: dubbel id {inv['id']!r}")
        gezien.add(inv["id"])
    return data


def app_witruimte(tekst: str) -> str:
    """De witruimtestap van sanitize_snippet: WS_RE -> ' ', daarna strip."""
    return WITRUIMTE.sub(" ", tekst).strip()


def fragmenteer(tekst: str, grens: int = FRAGMENT_MAX) -> list[tuple[str, str]]:
    """Verliesloos: [(fragment, scheiding_na)], ''.join(f + s) == tekst.

    Verwacht genormaliseerde tekst (enkele spaties, geen rand-witruimte). Knipt
    op de laatste spatie binnen de grens (die spatie wordt de scheiding), of
    hard op de grens als er geen spatie is (scheiding ''). Geen fragment begint
    of eindigt daardoor met witruimte, zodat de app er niets van afstript.
    """
    delen: list[tuple[str, str]] = []
    rest = tekst
    while len(rest) > grens:
        knip = rest.rfind(" ", 1, grens + 1)
        if knip <= 0:
            delen.append((rest[:grens], ""))
            rest = rest[grens:]
        else:
            delen.append((rest[:knip], " "))
            rest = rest[knip + 1 :]
    delen.append((rest, ""))
    return delen


def reconstrueer(
    relaties: list[dict[str, Any]], inhoud: dict[int, str]
) -> dict[str, str | None]:
    """Herbouw per bron uit fragmentinhoud (per input_index); None bij een gat."""
    per_bron: dict[str, list[dict[str, Any]]] = {}
    for r in relaties:
        per_bron.setdefault(r["bron_id"], []).append(r)
    uit: dict[str, str | None] = {}
    for bron_id, delen in per_bron.items():
        delen.sort(key=lambda r: r["fragment_nr"])
        compleet = [r["fragment_nr"] for r in delen] == list(
            range(1, delen[0]["aantal"] + 1)
        ) and all(r["input_index"] in inhoud for r in delen)
        uit[bron_id] = (
            "".join(inhoud[r["input_index"]] + r["scheiding_na"] for r in delen)
            if compleet
            else None
        )
    return uit


def bron_snippets(
    inv: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Fragmenten in UI-vorm (`_build_document_snippets`) + relaties + normalisatie.

    Alleen bron en doelgroep; geen beoordelaarsvelden (NIET_NAAR_MODEL).
    """
    bronnen = [(p["id"], p["herkomst"], p["tekst"]) for p in inv["bronpassages"]]
    bronnen.append((DOELGROEP_ID, DOELGROEP_ID, f"Doelgroep: {inv['doelgroep']}"))
    snippets: list[dict[str, Any]] = []
    relaties: list[dict[str, Any]] = []
    normalisatie: dict[str, Any] = {}
    for bron_id, herkomst, tekst in bronnen:
        norm = app_witruimte(tekst)
        delen = fragmenteer(norm)
        normalisatie[bron_id] = {
            "origineel_sha256": eb.sha256_bytes(tekst.encode("utf-8")),
            "genormaliseerd": norm,
            "genormaliseerd_sha256": eb.sha256_bytes(norm.encode("utf-8")),
            "witruimte_gewijzigd": norm != tekst,
            "lengte_origineel": len(tekst),
            "lengte_genormaliseerd": len(norm),
            "fragmenten": len(delen),
        }
        for k, (deel, scheiding) in enumerate(delen, start=1):
            doc_id = f"{bron_id}#{k}/{len(delen)}"
            relaties.append(
                {
                    "bron_id": bron_id,
                    "fragment_nr": k,
                    "aantal": len(delen),
                    "doc_id": doc_id,
                    "input_index": len(snippets),
                    "scheiding_na": scheiding,
                    "lengte": len(deel),
                }
            )
            snippets.append(
                {
                    "provider": "documents",
                    "title": herkomst,
                    "filename": herkomst,
                    "doc_id": doc_id,
                    "snippet": deel,
                    "score": 0.0,
                    "selection_basis": "selected_short_document",
                    "used_in_prompt": True,
                    "citation_label": f"fragment {k} van {len(delen)}",
                }
            )
    eigen = reconstrueer(relaties, {i: s["snippet"] for i, s in enumerate(snippets)})
    if eigen != {b: n["genormaliseerd"] for b, n in normalisatie.items()}:
        raise SystemExit(f"{inv['id']}: fragmentering niet verliesloos")
    return snippets, relaties, normalisatie


def fase_29(snippets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Nabouw van PHASE 2.9 in definition_orchestrator_v2 (identiek in beide)."""
    uit = []
    for s in snippets:
        uit.append(
            {
                "provider": "documents",
                **{
                    k: s[k]
                    for k in (
                        "filename",
                        "citation_label",
                        "selection_basis",
                        "source_version",
                        "locator",
                        "declared_metadata",
                    )
                    if s.get(k) is not None
                },
                "title": str(s.get("title") or s.get("filename") or "document"),
                "url": s.get("url"),
                "snippet": str(s.get("snippet", "")),
                "score": float(s.get("score", 0.0) or 0.0),
                "used_in_prompt": True,
                "doc_id": s.get("doc_id"),
                "source_label": "Geüpload document",
            }
        )
    return uit


# ---------------------------------------------------------------- prepare


def _beleid() -> dict[str, Any]:
    from config.config_manager import get_prompt_temperature
    from services.ai.anthropic_client import _THINKING_DISABLED
    from services.ai.model_router import ModelRouter

    router = ModelRouter.from_config()
    provider, model = router.get_model(TAAKTYPE)
    if provider != VERWACHTE_PROVIDER or model != VERWACHT_MODEL:
        raise SystemExit(
            f"router geeft {provider}/{model}, verwacht "
            f"{VERWACHTE_PROVIDER}/{VERWACHT_MODEL}; geen fallback"
        )
    temperatuur = get_prompt_temperature("definition")
    neemt_temp = router.accepts_temperature(model, provider=provider)
    denken_uit = router.thinking_default_on(model, provider=provider)
    return {
        "provider": provider,
        "model": model,
        "taaktype": TAAKTYPE,
        "config_temperatuur_definition": temperatuur,
        "temperature_meegestuurd": neemt_temp,
        "thinking": dict(_THINKING_DISABLED) if denken_uit else None,
        "max_tokens": MAX_TOKENS,
        "system": None,
    }


def api_verzoek(beleid: dict[str, Any], prompt: str) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": beleid["model"],
        "max_tokens": beleid["max_tokens"],
        "messages": [{"role": "user", "content": prompt}],
    }
    if beleid["thinking"] is not None:
        body["thinking"] = beleid["thinking"]
    if beleid["temperature_meegestuurd"]:
        body["temperature"] = beleid["config_temperatuur_definition"]
    return body


def _controleer_receipt(
    receipt: dict[str, Any],
    snippets: list[dict[str, Any]],
    relaties: list[dict[str, Any]],
    normalisatie: dict[str, Any],
    prompt: str,
) -> dict[str, Any]:
    """Volledigheidspoort: elk fragment gebruikt, heel, gelijk en in de prompt,
    en per bron exact herbouwbaar uit wat de app werkelijk opnam."""
    gebruikt = {
        r["input_index"]: r
        for r in receipt.get("sources", [])
        if r.get("source_type") == "document"
    }
    per_fragment = []
    for idx, s in enumerate(snippets):
        rec = gebruikt.get(idx)
        per_fragment.append(
            {
                "doc_id": s["doc_id"],
                "gebruikt": rec is not None,
                "afgekapt": rec["truncated"] if rec else None,
                "gesanitiseerd": rec["sanitized"] if rec else None,
                "xml_letterlijk_in_prompt": bool(rec) and rec["xml"] in prompt,
                "inhoud_gelijk_aan_aangeleverd": bool(rec)
                and rec["content"] == s["snippet"],
            }
        )
    fragmenten_ok = len(gebruikt) == len(snippets) and all(
        f["gebruikt"]
        and f["afgekapt"] is False
        and f["xml_letterlijk_in_prompt"]
        and f["inhoud_gelijk_aan_aangeleverd"]
        for f in per_fragment
    )
    herbouwd = reconstrueer(
        relaties, {i: rec["content"] for i, rec in gebruikt.items()}
    )
    per_bron = {
        bron_id: {
            "herbouwd_gelijk_aan_genormaliseerde_bron": herbouwd.get(bron_id)
            == n["genormaliseerd"],
            "witruimte_gewijzigd": n["witruimte_gewijzigd"],
            "fragmenten": n["fragmenten"],
        }
        for bron_id, n in normalisatie.items()
    }
    return {
        "fragmenten": per_fragment,
        "per_bron": per_bron,
        "weggelaten": receipt.get("omitted", []),
        "fouten": receipt.get("errors", []),
        "alles_volledig_in_prompt": fragmenten_ok
        and all(
            b["herbouwd_gelijk_aan_genormaliseerde_bron"] for b in per_bron.values()
        )
        and not receipt.get("omitted")
        and not receipt.get("errors"),
    }


async def _bouw(request: Any, context: dict[str, Any]) -> Any:
    from services.prompts.prompt_service_v2 import PromptServiceV2

    return await PromptServiceV2().build_generation_prompt(
        request, feedback_history=None, context=context
    )


async def _prepare_invoer(
    inv: dict[str, Any], beleid: dict[str, Any]
) -> dict[str, Any]:
    from services.interfaces import GenerationRequest
    from services.orchestrators.definition_orchestrator_v2 import (
        heeft_inhoudelijke_context,
    )
    from services.security_service import SecurityService

    org = list(inv["organisatorische_context"])
    request = GenerationRequest(
        id=f"def770-g24-{inv['id']}",
        begrip=inv["begrip"],
        organisatorische_context=org,
        juridische_context=list(inv["juridische_context"]),
        wettelijke_basis=list(inv["wettelijke_basis"]),
        organisatie="",
        extra_instructies=None,
        ontologische_categorie=None,
        ufo_categorie=None,
        actor="legacy_ui",
        legal_basis="legitimate_interest",
        context=", ".join(org),
        options=None,
        document_context=None,
        rag_collection_ids=None,
        betekenisverduidelijking=None,
    )
    uit: dict[str, Any] = {"invoer_id": inv["id"]}
    if not heeft_inhoudelijke_context(request):
        uit["weigering"] = "geen inhoudelijke context (orchestrator-vereiste)"
        return uit
    schoon = await SecurityService().sanitize_request(request)
    ruwe_snippets, relaties, normalisatie = bron_snippets(inv)
    snippets = fase_29(ruwe_snippets)
    context = {"documents": {"snippets": snippets}}
    eerste = await _bouw(schoon, json.loads(json.dumps(context)))
    tweede = await _bouw(schoon, json.loads(json.dumps(context)))
    receipt = (eerste.metadata or {}).get("source_receipt", eb.NIET_AANWEZIG)
    controle = (
        _controleer_receipt(receipt, snippets, relaties, normalisatie, eerste.text)
        if isinstance(receipt, dict)
        else {"alles_volledig_in_prompt": False, "reden": "geen source_receipt"}
    )
    body = api_verzoek(beleid, eerste.text)
    uit.update(
        {
            "request_velden": dataclasses.asdict(schoon),
            "sanitize_wijzigde_request": dataclasses.asdict(schoon)
            != dataclasses.asdict(request),
            "context": context,
            "fragmentrelaties": relaties,
            "bronnormalisatie": normalisatie,
            "prompt": eerste.text,
            "prompt_sha256": eb.sha256_bytes(eerste.text.encode("utf-8")),
            "prompt_deterministisch": eerste.text == tweede.text,
            "token_count_app": eerste.token_count,
            "components_used": eerste.components_used,
            "source_receipt": receipt,
            "controle": controle,
            # Observatie, geen poort: een korte waarde kan toevallig ook uit
            # begrip, context of bron in de prompt staan.
            "beoordelaarsvelden_letterlijk_in_prompt": {
                veld: [
                    w
                    for w in ([inv[veld]] if isinstance(inv[veld], str) else inv[veld])
                    if w.strip() and w in eerste.text
                ]
                for veld in NIET_NAAR_MODEL
            },
            "api_verzoek": body,
            "api_verzoek_sha256": eb.sha256_bytes(eb.canoniek_json(body)),
        }
    )
    return uit


def _proefconfig() -> dict[str, Any]:
    """Zet de documentkanaal-proefconfig (beide armen identiek) en leg haar vast."""
    voor = {k: os.environ.get(k) for k in PROEF_DOCUMENT_ENV}
    os.environ.update(PROEF_DOCUMENT_ENV)
    return {
        "document_env": dict(PROEF_DOCUMENT_ENV),
        "document_env_voor_zetten": voor,
        "app_fragmentgrens": APP_FRAGMENTGRENS,
        "fragment_max": FRAGMENT_MAX,
        "witruimtenormalisatie": "re.sub(r'\\s+', ' ', tekst).strip() (WS_RE)",
        "fragmentering": "op laatste spatie <= fragment_max, anders hard; "
        "scheiding per fragment vastgelegd",
    }


def cmd_prepare(a: argparse.Namespace) -> int:
    # Externe paden vóór activeer_bron (die de werkmap wisselt).
    uit = a.output.resolve()
    invoerpad = a.input.resolve()
    repo = a.repo.resolve()
    werkmap = (a.werkmap or uit.with_name(uit.name + ".werk")).resolve()
    if uit.exists():
        raise SystemExit(f"{uit} bestaat al")
    invoer_bytes = invoerpad.read_bytes()
    invoer = lees_invoer(invoerpad)
    binding = eb.bronbinding(repo, a.verwachte_commit)
    werkmap.mkdir(exist_ok=False)
    bron = werkmap / "bron"
    uitpak = eb.pak_uit(repo, bron)
    offline = eb.activeer_bron(bron, werkmap / "sessie")
    logging.disable(logging.CRITICAL)

    proefconfig = _proefconfig()
    beleid = _beleid()
    per_invoer = [asyncio.run(_prepare_invoer(inv, beleid)) for inv in invoer]
    klaar = all(
        "weigering" not in r
        and r["prompt_deterministisch"]
        and r["controle"]["alles_volledig_in_prompt"]
        for r in per_invoer
    )
    rapport = {
        "soort": "DEF-770 G24 prepare-arm (offline; geen API-aanroep)",
        "arm": a.arm,
        "klaar": klaar,
        "script_sha256": eb.sha256_bestand(Path(__file__).resolve()),
        "helper_sha256": eb.sha256_bestand(Path(eb.__file__).resolve()),
        "python": sys.version,
        "bron": {
            **binding,
            **uitpak,
            "sleutelbestanden_sha256": eb.sleutelhashes(bron),
        },
        "moduleherkomst": eb.herkomstcontrole(
            bron,
            (
                "tests.offline_bootstrap",
                "services.prompts.prompt_service_v2",
                "services.security_service",
                "services.orchestrators.definition_orchestrator_v2",
                "services.ai.model_router",
                "services.ai.anthropic_client",
                "config.config_manager",
            ),
        ),
        "offline_gate_actief": offline.gate_is_actief(),
        "document_env": {
            k: os.environ.get(k, "(default)")
            for k in (
                "DOCUMENT_SNIPPETS_ENABLED",
                "DOCUMENT_SNIPPETS_MAX",
                "DOCUMENT_SNIPPETS_MAX_CHARS",
            )
        },
        "invoer": {
            "pad": str(invoerpad),
            "sha256": eb.sha256_bytes(invoer_bytes),
        },
        "proefconfig": proefconfig,
        "niet_naar_model": NIET_NAAR_MODEL,
        "afwijkingen": AFWIJKINGEN,
        "beleid": beleid,
        "per_invoer": per_invoer,
    }
    digest = eb.schrijf_nieuw(uit, rapport)
    print(f"arm {a.arm} commit {binding['commit']} klaar {klaar}")
    print(f"uitvoer {uit}")
    print(f"sha256 {digest}")
    return 0 if klaar else 1


# ---------------------------------------------------------------- manifest


def _lees_json(pad: Path) -> tuple[dict[str, Any], str]:
    data = pad.read_bytes()
    return json.loads(data), eb.sha256_bytes(data)


def _zonder_prompt(body: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in body.items() if k != "messages"} | {
        "rollen": [m["role"] for m in body["messages"]]
    }


def cmd_manifest(a: argparse.Namespace) -> int:
    uit = a.output.resolve()
    paden = {"oud": a.oud.resolve(), "nieuw": a.nieuw.resolve()}
    if uit.exists():
        raise SystemExit(f"{uit} bestaat al")
    armen = {naam: _lees_json(pad) for naam, pad in paden.items()}
    fouten = []
    for naam, (arm, _) in armen.items():
        if arm.get("arm") != naam or not arm.get("klaar"):
            fouten.append(f"arm {naam}: niet klaar of verkeerd label")
        if not arm.get("proefconfig"):
            fouten.append(f"arm {naam}: geen vastgelegde proefconfig")
    oud, nieuw = armen["oud"][0], armen["nieuw"][0]
    if oud["invoer"]["sha256"] != nieuw["invoer"]["sha256"]:
        fouten.append("armen gebruiken verschillende invoer")
    if oud["beleid"] != nieuw["beleid"]:
        fouten.append("API-beleid verschilt tussen armen")
    if oud.get("proefconfig") != nieuw.get("proefconfig"):
        fouten.append("proefconfig verschilt tussen armen")
    ids_oud = [r["invoer_id"] for r in oud["per_invoer"]]
    if ids_oud != [r["invoer_id"] for r in nieuw["per_invoer"]]:
        fouten.append("invoervolgorde verschilt")
    per_invoer = []
    for ro, rn in zip(oud["per_invoer"], nieuw["per_invoer"], strict=False):
        gelijk = {
            "request_velden": ro.get("request_velden") == rn.get("request_velden"),
            "context": ro.get("context") == rn.get("context"),
            "fragmentrelaties": ro.get("fragmentrelaties")
            == rn.get("fragmentrelaties"),
            "api_instellingen": _zonder_prompt(ro["api_verzoek"])
            == _zonder_prompt(rn["api_verzoek"]),
        }
        if not all(gelijk.values()):
            fouten.append(f"{ro['invoer_id']}: arm-invoer niet gelijk {gelijk}")
        per_invoer.append(
            {
                "invoer_id": ro["invoer_id"],
                "gelijk": gelijk,
                "prompt_identiek_oud_nieuw": ro["prompt"] == rn["prompt"],
                "prompt_sha256": {
                    "oud": ro["prompt_sha256"],
                    "nieuw": rn["prompt_sha256"],
                },
            }
        )
    if fouten:
        for f in fouten:
            print("FOUT", f)
        return 1

    verzoeken: dict[str, Any] = {}
    aanroepen = []
    for naam, (arm, _) in armen.items():
        for r in arm["per_invoer"]:
            body = r["api_verzoek"]
            h = eb.sha256_bytes(eb.canoniek_json(body))
            if h != r["api_verzoek_sha256"]:
                raise SystemExit(f"hash van {naam}/{r['invoer_id']} klopt niet")
            verzoeken[h] = body
            for n in range(1, a.herhalingen + 1):
                aanroepen.append(
                    {
                        "call_id": f"{r['invoer_id']}__{naam}__h{n}",
                        "invoer_id": r["invoer_id"],
                        "arm": naam,
                        "herhaling": n,
                        "request_sha256": h,
                        "begrip_gesanitiseerd": r["request_velden"]["begrip"],
                    }
                )
    manifest = {
        "soort": "DEF-770 G24 manifest (geen API-aanroep)",
        "script_sha256": eb.sha256_bestand(Path(__file__).resolve()),
        "armen": {
            naam: {
                "bestand": str(pad),
                "sha256": armen[naam][1],
                "commit": armen[naam][0]["bron"]["commit"],
                "archief_sha256": armen[naam][0]["bron"]["archief_sha256"],
            }
            for naam, pad in paden.items()
        },
        "invoer_sha256": oud["invoer"]["sha256"],
        "beleid": oud["beleid"],
        "proefconfig": oud["proefconfig"],
        "herhalingen": a.herhalingen,
        "plafond_usd": PLAFOND_USD,
        "prijzen_usd_per_mtok": {
            "input": PRIJS_INPUT_PER_MTOK,
            "output": PRIJS_OUTPUT_PER_MTOK,
        },
        "afwijkingen": AFWIJKINGEN,
        "per_invoer": per_invoer,
        "unieke_verzoeken": len(verzoeken),
        "geplande_aanroepen": len(aanroepen),
        "verzoeken": verzoeken,
        "aanroepen": aanroepen,
    }
    ontwerpfouten = _poort_ontwerp(manifest)
    manifest["betaald_ontwerp"] = {
        "voldoet": not ontwerpfouten,
        "afwijkingen": ontwerpfouten,
        "noot": "alleen informatief; count en run toetsen zelf opnieuw",
    }
    digest = eb.schrijf_nieuw(uit, manifest)
    print(f"unieke verzoeken {len(verzoeken)} geplande aanroepen {len(aanroepen)}")
    print(f"betaald ontwerp: {'ja' if not ontwerpfouten else 'nee (alleen smoke)'}")
    print(f"manifest {uit}")
    print(f"sha256 {digest}")
    return 0


# ---------------------------------------------------------------- netwerkfasen


def _laad_manifest(pad: Path) -> tuple[dict[str, Any], str]:
    manifest, digest = _lees_json(pad)
    for h, body in manifest["verzoeken"].items():
        if eb.sha256_bytes(eb.canoniek_json(body)) != h:
            raise SystemExit(f"manifest: verzoek {h} is gewijzigd")
    return manifest, digest


def _api_sleutel(env_file: Path | None) -> str:
    """Lees ANTHROPIC_API_KEY; meld alleen aanwezigheid."""
    waarde = os.environ.get("ANTHROPIC_API_KEY", "")
    herkomst = "omgeving"
    if not waarde and env_file is not None:
        herkomst = f"bestand {env_file}"
        for regel in env_file.read_text(encoding="utf-8").splitlines():
            naam, _, rest = regel.strip().partition("=")
            if naam.strip() == "ANTHROPIC_API_KEY":
                waarde = rest.strip().strip('"').strip("'")
    print(f"ANTHROPIC_API_KEY aanwezig: {'ja' if waarde else 'nee'} ({herkomst})")
    if not waarde:
        raise SystemExit("geen API-sleutel; gestopt")
    return waarde


def _redigeer(tekst: str) -> str:
    return _SLEUTELPATROON.sub("[GEREDIGEERD]", tekst)


def _max_kosten(input_tokens: int, max_tokens: int) -> float:
    return (
        input_tokens * PRIJS_INPUT_PER_MTOK + max_tokens * PRIJS_OUTPUT_PER_MTOK
    ) / 1_000_000


def _poort_ontwerp(manifest: dict[str, Any]) -> list[str]:
    """Het vaste betaalde ontwerp: 6 invoeren x 2 armen x 2 herhalingen = 24."""
    f: list[str] = []
    beleid = manifest.get("beleid") or {}
    if beleid.get("model") != VERWACHT_MODEL:
        f.append(f"beleid.model {beleid.get('model')!r} != {VERWACHT_MODEL}")
    if beleid.get("max_tokens") != MAX_TOKENS:
        f.append(f"beleid.max_tokens {beleid.get('max_tokens')!r} != {MAX_TOKENS}")
    if manifest.get("herhalingen") != HERHALINGEN:
        f.append(f"herhalingen {manifest.get('herhalingen')!r} != {HERHALINGEN}")
    try:
        plafond = float(manifest.get("plafond_usd", 0))
    except (TypeError, ValueError):
        plafond = 0.0
    if not 0 < plafond <= PLAFOND_USD:
        f.append(f"manifest-plafond {manifest.get('plafond_usd')!r} niet in (0, 5]")
    aanroepen = manifest.get("aanroepen") or []
    verzoeken = manifest.get("verzoeken") or {}
    ids = [c.get("call_id") for c in aanroepen]
    verwacht = AANTAL_INVOEREN * len(ARMEN) * HERHALINGEN
    if len(aanroepen) != verwacht:
        f.append(f"{len(aanroepen)} aanroepen, verwacht {verwacht}")
    if len(set(ids)) != len(ids):
        f.append("call_id's niet uniek")
    if {c.get("arm") for c in aanroepen} != set(ARMEN):
        f.append("armen wijken af van oud/nieuw")
    invoeren = sorted({c.get("invoer_id") for c in aanroepen})
    if len(invoeren) != AANTAL_INVOEREN:
        f.append(f"{len(invoeren)} invoeren, verwacht {AANTAL_INVOEREN}")
    for inv in invoeren:
        for arm in ARMEN:
            groep = [
                c for c in aanroepen if (c.get("invoer_id"), c.get("arm")) == (inv, arm)
            ]
            if sorted(c.get("herhaling") for c in groep) != list(
                range(1, HERHALINGEN + 1)
            ):
                f.append(f"{inv}/{arm}: herhalingen niet exact 1..{HERHALINGEN}")
            if len({c.get("request_sha256") for c in groep}) > 1:
                f.append(f"{inv}/{arm}: herhalingen met verschillend verzoek")
            for c in groep:
                if c.get("call_id") != f"{inv}__{arm}__h{c.get('herhaling')}":
                    f.append(f"call_id {c.get('call_id')!r} past niet bij zijn paar")
    for c in aanroepen:
        if c.get("request_sha256") not in verzoeken:
            f.append(f"{c.get('call_id')}: verzoek ontbreekt in manifest")
    for h, body in verzoeken.items():
        if set(body) - TOEGESTANE_VERZOEKVELDEN:
            f.append(
                f"verzoek {h[:12]}: extra velden {sorted(set(body) - TOEGESTANE_VERZOEKVELDEN)}"
            )
        if body.get("model") != VERWACHT_MODEL or body.get("max_tokens") != MAX_TOKENS:
            f.append(f"verzoek {h[:12]}: model/max_tokens wijkt af")
        if [m.get("role") for m in body.get("messages", [])] != ["user"]:
            f.append(f"verzoek {h[:12]}: niet precies één user-bericht")
    return f


def _poort_budget(
    manifest: dict[str, Any],
    counts: dict[str, Any],
    akkoord: dict[str, Any],
    m_sha: str,
    c_sha: str,
) -> tuple[list[str], float]:
    """Binding manifest <- counts <- goedkeuring en hard plafond <= USD 5."""
    f: list[str] = []
    if counts.get("manifest_sha256") != m_sha:
        f.append("counts horen niet bij dit manifest")
    if akkoord.get("manifest_sha256") != m_sha:
        f.append("goedkeuring noemt een ander manifest")
    if akkoord.get("counts_sha256") != c_sha:
        f.append("goedkeuring noemt andere counts")
    if not str(akkoord.get("goedgekeurd_door") or "").strip():
        f.append("goedkeuring zonder goedgekeurd_door")
    try:
        akkoord_plafond = float(akkoord.get("plafond_usd", 0))
        plafond = min(akkoord_plafond, float(manifest["plafond_usd"]))
    except (TypeError, ValueError, KeyError):
        akkoord_plafond = plafond = 0.0
    if not (0 < plafond <= PLAFOND_USD and akkoord_plafond <= PLAFOND_USD):
        f.append(f"plafond {akkoord.get('plafond_usd')!r} niet in (0, {PLAFOND_USD}]")
    tellingen = counts.get("tellingen") or {}
    verzoeken = manifest.get("verzoeken") or {}
    if set(tellingen) != set(verzoeken) or not all(
        isinstance(t.get("input_tokens"), int) and t["input_tokens"] > 0
        for t in tellingen.values()
    ):
        f.append("tellingen dekken de verzoeken niet (exact, positief)")
        return f, plafond
    totaal = sum(
        _max_kosten(
            tellingen[c["request_sha256"]]["input_tokens"],
            verzoeken[c["request_sha256"]]["max_tokens"],
        )
        for c in manifest.get("aanroepen", [])
        if c.get("request_sha256") in verzoeken
    )
    if totaal > plafond:
        f.append(f"maximale raming USD {totaal:.4f} boven plafond {plafond}")
    return f, plafond


def cmd_count(a: argparse.Namespace) -> int:
    import anthropic

    if not a.opdracht_ref.strip():
        raise SystemExit("--opdracht-ref is verplicht (schriftelijke opdracht)")
    uit = a.output.resolve()
    manifest_pad = a.manifest.resolve()
    env_file = a.env_file.resolve() if a.env_file else None
    if uit.exists():
        raise SystemExit(f"{uit} bestaat al")
    manifest, m_sha = _laad_manifest(manifest_pad)
    fouten = _poort_ontwerp(manifest)
    if fouten:
        for fout in fouten:
            print("GEWEIGERD", fout)
        return 2
    client = anthropic.Anthropic(
        api_key=_api_sleutel(env_file), max_retries=0, timeout=a.timeout
    )
    tellingen: dict[str, Any] = {}
    for h, body in manifest["verzoeken"].items():
        velden = {k: body[k] for k in ("model", "messages", "thinking") if k in body}
        try:
            resp = client.messages.count_tokens(**velden)
        except anthropic.APIError as exc:
            print(
                "STOP providerfout bij count:", type(exc).__name__, _redigeer(str(exc))
            )
            return 4
        tellingen[h] = {"input_tokens": resp.input_tokens}
    per_aanroep = [
        _max_kosten(
            tellingen[c["request_sha256"]]["input_tokens"],
            manifest["verzoeken"][c["request_sha256"]]["max_tokens"],
        )
        for c in manifest["aanroepen"]
    ]
    totaal = sum(per_aanroep)
    rapport = {
        "soort": "DEF-770 G24 count_tokens",
        "opdracht_ref": a.opdracht_ref,
        "manifest_sha256": m_sha,
        "tijd": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "tellingen": tellingen,
        "max_kosten_usd_totaal": round(totaal, 6),
        "raming": "per aanroep input x $5/MTok + max_tokens x $25/MTok",
        "plafond_usd": manifest["plafond_usd"],
        "binnen_plafond": totaal <= manifest["plafond_usd"],
    }
    digest = eb.schrijf_nieuw(uit, rapport)
    print(f"max kosten USD {totaal:.4f} plafond {manifest['plafond_usd']}")
    print(f"counts {uit}")
    print(f"sha256 {digest}")
    return 0 if rapport["binnen_plafond"] else 3


def _schrijf_atomair(doel: Path, obj: Any) -> str:
    """Tijdelijk bestand (exclusief) + os.link: bestaat het doel, dan faalt het."""
    tmp = doel.with_name(f".{doel.name}.{os.getpid()}.tmp")
    digest = eb.schrijf_nieuw(tmp, obj)
    try:
        os.link(tmp, doel)
    finally:
        tmp.unlink()
    return digest


def _kosten(usage: dict[str, Any]) -> float:
    return (
        usage["input_tokens"] * PRIJS_INPUT_PER_MTOK
        + usage["output_tokens"] * PRIJS_OUTPUT_PER_MTOK
    ) / 1_000_000


def _toets_response(
    record: dict[str, Any], body: dict[str, Any], geteld: int
) -> str | None:
    """Toets een (al bewaard) resultaat tegen model, stopreden en begroting."""
    if record.get("model") != body["model"]:
        return f"modelafwijking: {record.get('model')!r} != {body['model']!r}"
    if record.get("stop_reason") != "end_turn":
        return f"stop_reason {record.get('stop_reason')!r} (cutoff of afwijzing)"
    u = record.get("usage") or {}
    if not isinstance(u.get("input_tokens"), int) or not isinstance(
        u.get("output_tokens"), int
    ):
        return "usage ontbreekt of is onvolledig"
    if u["input_tokens"] > geteld:
        return f"input_tokens {u['input_tokens']} boven telling {geteld}"
    if u["output_tokens"] > body["max_tokens"]:
        return (
            f"output_tokens {u['output_tokens']} boven max_tokens {body['max_tokens']}"
        )
    if _kosten(u) > _max_kosten(geteld, body["max_tokens"]):
        return "werkelijke kosten boven de vooraframing van deze call"
    return None


def _stop(
    map_: Path, call_id: str | None, reden: str, code: int, **details: Any
) -> int:
    """Leg een blijvende stop vast (eerste stop blijft staan) en geef de code."""
    record = {
        "call_id": call_id,
        "reden": reden,
        "exitcode": code,
        "tijd": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        **details,
    }
    try:
        _schrijf_atomair(map_ / STOPBESTAND, record)
    except FileExistsError:
        pass  # een eerdere stop staat al vast
    print(f"STOP {call_id}: {reden} (vastgelegd in {STOPBESTAND})")
    return code


def _valideer_resultaat(
    pad: Path,
    aanvraag: Path,
    call: dict[str, Any],
    body: dict[str, Any],
    geteld: int,
    binding: dict[str, Any],
) -> tuple[str | None, float]:
    """Volledige identiteits- en begrotingscontrole van een bestaand resultaat."""
    try:
        r = json.loads(pad.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return f"resultaat onleesbaar: {type(exc).__name__}", 0.0
    if not aanvraag.exists():
        return "resultaat zonder voorafgaande aanvraagregistratie", 0.0
    for sleutel, verwacht in (
        ("call_id", call["call_id"]),
        ("request_sha256", call["request_sha256"]),
        ("manifest_sha256", binding["manifest_sha256"]),
        ("counts_sha256", binding["counts_sha256"]),
        ("goedkeuring_sha256", binding["goedkeuring_sha256"]),
    ):
        if r.get(sleutel) != verwacht:
            return f"bestaand resultaat: {sleutel} past niet", 0.0
    fout = _toets_response(r, body, geteld)
    return fout, (_kosten(r["usage"]) if fout is None else 0.0)


def cmd_run(a: argparse.Namespace) -> int:
    import anthropic

    manifest_pad = a.manifest.resolve()
    counts_pad = a.counts.resolve()
    akkoord_pad = a.goedkeuring.resolve()
    map_ = a.uitvoermap.resolve()
    env_file = a.env_file.resolve() if a.env_file else None
    manifest, m_sha = _laad_manifest(manifest_pad)
    counts, c_sha = _lees_json(counts_pad)
    akkoord, g_sha = _lees_json(akkoord_pad)
    budgetfouten, plafond = _poort_budget(manifest, counts, akkoord, m_sha, c_sha)
    fouten = _poort_ontwerp(manifest) + budgetfouten
    if fouten:
        for fout in fouten:
            print("GEWEIGERD", fout)
        return 2
    binding = {
        "manifest_sha256": m_sha,
        "counts_sha256": c_sha,
        "goedkeuring_sha256": g_sha,
        "plafond_usd": plafond,
    }
    map_.mkdir(exist_ok=True)
    slot = map_ / ".run.lock"
    with open(slot, "x", encoding="utf-8") as f:  # één schrijver tegelijk
        f.write(f"{os.getpid()} {m_sha}\n")
    try:
        bindpad = map_ / BINDINGBESTAND
        if bindpad.exists():
            if json.loads(bindpad.read_text(encoding="utf-8")) != binding:
                print("GEWEIGERD uitvoermap hoort bij een andere binding")
                return 2
        else:
            _schrijf_atomair(bindpad, binding)
        if (map_ / STOPBESTAND).exists():
            print(f"STOP eerder vastgelegd in {STOPBESTAND}; coördinator beslist")
            return 4
        client = anthropic.Anthropic(
            api_key=_api_sleutel(env_file), max_retries=0, timeout=a.timeout
        )
        return _run_lus(client, manifest, counts, binding, map_)
    finally:
        slot.unlink()


def _run_lus(
    client: Any,
    manifest: dict[str, Any],
    counts: dict[str, Any],
    binding: dict[str, Any],
    map_: Path,
) -> int:
    plafond = binding["plafond_usd"]
    besteed = 0.0
    for call in manifest["aanroepen"]:
        cid, h = call["call_id"], call["request_sha256"]
        body = manifest["verzoeken"][h]
        geteld = counts["tellingen"][h]["input_tokens"]
        resultaat = map_ / f"{cid}.json"
        aanvraag = map_ / f"{cid}.aanvraag.json"
        if resultaat.exists():
            fout, kosten = _valideer_resultaat(
                resultaat, aanvraag, call, body, geteld, binding
            )
            if fout:
                return _stop(map_, cid, fout, 4)
            besteed += kosten
            if besteed > plafond:
                return _stop(map_, cid, "cumulatieve kosten boven plafond", 3)
            print(f"overgeslagen (volledig gecontroleerd) {cid}")
            continue
        if aanvraag.exists():
            return _stop(
                map_,
                cid,
                "onbesliste aanvraag: verzonden zonder resultaat; niet opnieuw verzonden",
                4,
            )
        if besteed + _max_kosten(geteld, body["max_tokens"]) > plafond:
            return _stop(
                map_,
                cid,
                "budget: volgende call past niet meer",
                3,
                besteed_usd=besteed,
            )
        # Duurzaam en exclusief vastleggen vóór verzending.
        _schrijf_atomair(
            aanvraag,
            {
                "call_id": cid,
                "request_sha256": h,
                **binding,
                "tijd": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "status": "verzonden; onbeslist zolang er geen resultaat is",
            },
        )
        start = time.time()
        try:
            resp = client.messages.create(**body)
        except Exception as exc:  # providerfout: vastleggen, nooit opnieuw
            return _stop(
                map_,
                cid,
                "providerfout",
                4,
                fouttype=type(exc).__name__,
                status_code=getattr(exc, "status_code", None),
                boodschap=_redigeer(str(exc)),
                duur_s=round(time.time() - start, 3),
            )
        usage = resp.usage.model_dump()
        record = {
            "call_id": cid,
            "request_sha256": h,
            **{
                k: binding[k]
                for k in ("manifest_sha256", "counts_sha256", "goedkeuring_sha256")
            },
            "geteld_input_tokens": geteld,
            "tijd": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "duur_s": round(time.time() - start, 3),
            "bericht_id": resp.id,
            "model": resp.model,
            "stop_reason": resp.stop_reason,
            "usage": usage,
            "tekst": "\n".join(
                b.text for b in resp.content if hasattr(b, "text")
            ).strip(),
            "ruwe_response": resp.model_dump(mode="json"),
        }
        try:
            digest = _schrijf_atomair(resultaat, record)  # eerst ongewijzigd bewaren
        except Exception as exc:
            return _stop(
                map_,
                cid,
                "opslagfout resultaat",
                4,
                fouttype=type(exc).__name__,
                bericht_id=resp.id,
                model=resp.model,
                stop_reason=resp.stop_reason,
                usage=usage,
            )
        kosten = _kosten(usage)
        besteed += kosten
        print(f"{cid} {resp.stop_reason} sha256 {digest} besteed USD {besteed:.4f}")
        fout = _toets_response(record, body, geteld)
        if fout:
            return _stop(map_, cid, fout, 5, kosten_usd=kosten, besteed_usd=besteed)
        if besteed > plafond:
            return _stop(
                map_, cid, "cumulatieve kosten boven plafond", 3, besteed_usd=besteed
            )
    return 0


# ---------------------------------------------------------------- nabewerk


async def _nabewerk_een(raw: str, begrip: str) -> dict[str, Any]:
    from services.modelantwoord import SOORT_DEFINITIE, lees_modelantwoord

    antwoord = lees_modelantwoord(raw)
    uit: dict[str, Any] = {
        "soort": antwoord.soort,
        "code": antwoord.code,
        "reden": antwoord.reden,
    }
    if antwoord.soort != SOORT_DEFINITIE:
        uit["opmerking"] = "orchestrator takt hier af: geen opschoning"
        return uit
    from opschoning.opschoning_enhanced import (
        extract_definition_from_gpt_response,
        opschonen_enhanced,
    )
    from services.cleaning_service import CleaningConfig, CleaningService

    schoon = await CleaningService(CleaningConfig()).clean_text(raw, begrip)
    uit.update(
        {
            "opgeschoonde_kandidaat": schoon.cleaned_text,
            "opschoonregels": list(schoon.applied_rules),
            "definitie_origineel": opschonen_enhanced(
                raw, begrip, handle_gpt_format=True
            ),
            "definitie_kern": extract_definition_from_gpt_response(raw),
        }
    )
    return uit


def cmd_nabewerk(a: argparse.Namespace) -> int:
    # Externe paden vóór activeer_bron (die de werkmap wisselt).
    uit = a.output.resolve()
    manifest_pad = a.manifest.resolve()
    uitvoermap = a.uitvoermap.resolve()
    repo = a.repo.resolve()
    werkmap = (a.werkmap or uit.with_name(uit.name + ".werk")).resolve()
    if uit.exists():
        raise SystemExit(f"{uit} bestaat al")
    if not uitvoermap.is_dir():
        raise SystemExit(f"uitvoermap {uitvoermap} bestaat niet")
    manifest, m_sha = _laad_manifest(manifest_pad)
    binding = eb.bronbinding(repo, manifest["armen"][a.arm]["commit"])
    werkmap.mkdir(exist_ok=False)
    bron = werkmap / "bron"
    eb.pak_uit(repo, bron)
    offline = eb.activeer_bron(bron, werkmap / "sessie")
    logging.disable(logging.CRITICAL)

    rijen = []
    ontbrekend = []
    for call in manifest["aanroepen"]:
        if call["arm"] != a.arm:
            continue
        pad = uitvoermap / f"{call['call_id']}.json"
        if not pad.exists():
            ontbrekend.append(call["call_id"])
            rijen.append({"call_id": call["call_id"], "resultaat": eb.NIET_AANWEZIG})
            continue
        r = json.loads(pad.read_text(encoding="utf-8"))
        if (
            r.get("call_id") != call["call_id"]
            or r.get("request_sha256") != call["request_sha256"]
            or r.get("manifest_sha256") != m_sha
        ):
            raise SystemExit(f"{pad}: identiteit past niet bij het manifest")
        rijen.append(
            {
                "call_id": call["call_id"],
                "resultaat_sha256": eb.sha256_bestand(pad),
                "stop_reason": r["stop_reason"],
                "ruwe_tekst": r["tekst"],
                **asyncio.run(_nabewerk_een(r["tekst"], call["begrip_gesanitiseerd"])),
            }
        )
    rapport = {
        "soort": "DEF-770 G24 nabewerking (offline; geen validatie/enhancement)",
        "arm": a.arm,
        "manifest_sha256": m_sha,
        "script_sha256": eb.sha256_bestand(Path(__file__).resolve()),
        "bron": {**binding, "sleutelbestanden_sha256": eb.sleutelhashes(bron)},
        "offline_gate_actief": offline.gate_is_actief(),
        "uitvoermap": str(uitvoermap),
        "compleet": not ontbrekend,
        "ontbrekend": ontbrekend,
        "rijen": rijen,
    }
    digest = eb.schrijf_nieuw(uit, rapport)
    print(f"nabewerk {a.arm} {uit} sha256 {digest}")
    if ontbrekend:
        print(f"ONVOLLEDIG: {len(ontbrekend)} verwachte resultaten ontbreken")
        return 2
    return 0


# ---------------------------------------------------------------- cli


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="fase", required=True)

    pr = sub.add_parser("prepare", help="offline, per arm")
    pr.add_argument("--arm", choices=("oud", "nieuw"), required=True)
    pr.add_argument("--repo", type=Path, required=True)
    pr.add_argument("--input", type=Path, required=True)
    pr.add_argument("--output", type=Path, required=True)
    pr.add_argument("--werkmap", type=Path)
    pr.add_argument("--verwachte-commit")

    ma = sub.add_parser("manifest", help="bundelt beide armen, offline")
    ma.add_argument("--oud", type=Path, required=True)
    ma.add_argument("--nieuw", type=Path, required=True)
    ma.add_argument("--output", type=Path, required=True)
    ma.add_argument("--herhalingen", type=int, default=HERHALINGEN)

    co = sub.add_parser("count", help="NETWERK: count_tokens (alleen op opdracht)")
    co.add_argument("--manifest", type=Path, required=True)
    co.add_argument("--output", type=Path, required=True)
    co.add_argument("--env-file", type=Path)
    co.add_argument("--timeout", type=float, default=30.0)
    co.add_argument("--opdracht-ref", required=True)

    ru = sub.add_parser("run", help="NETWERK, BETAALD: alleen met goedkeuring")
    ru.add_argument("--manifest", type=Path, required=True)
    ru.add_argument("--counts", type=Path, required=True)
    ru.add_argument("--goedkeuring", type=Path, required=True)
    ru.add_argument("--uitvoermap", type=Path, required=True)
    ru.add_argument("--env-file", type=Path)
    ru.add_argument("--timeout", type=float, default=120.0)

    nb = sub.add_parser("nabewerk", help="offline, per arm")
    nb.add_argument("--arm", choices=("oud", "nieuw"), required=True)
    nb.add_argument("--repo", type=Path, required=True)
    nb.add_argument("--manifest", type=Path, required=True)
    nb.add_argument("--uitvoermap", type=Path, required=True)
    nb.add_argument("--output", type=Path, required=True)
    nb.add_argument("--werkmap", type=Path)

    a = p.parse_args()
    return {
        "prepare": cmd_prepare,
        "manifest": cmd_manifest,
        "count": cmd_count,
        "run": cmd_run,
        "nabewerk": cmd_nabewerk,
    }[a.fase](a)


if __name__ == "__main__":
    raise SystemExit(main())
