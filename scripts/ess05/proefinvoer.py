"""DEF-768 WP7 — invoerlaag van de ESS-05-proefrunner (zonder netwerk).

- **Schema** (`valideer_gevallenbestand`): het generieke gevallenformaat
  `{gevallen: [{id, begrip, tekst, toelichting, categorie, context, bronnen,
  buren, verwacht, verwacht_per_buur, grond, …}], herhaal_ids: [4]}`,
  fail-closed. Het schema bekijkt alleen de vorm; het stelt geen label bij.
  `verwacht_per_buur` mag de ontwikkelmapping `{term: onderscheid}` of de
  afgesproken eindsetlijst `[{term, distinction, dragend_citaat,
  ontbrekend_kenmerk, grond}]` zijn (`per_buur_verwachtingen`).
- **Afscherming**: naar het model gaan uitsluitend de `MODELVELDEN`
  (whitelist). Al het andere — `verwacht`, `verwacht_per_buur`, `grond`,
  `doel`, herkomstnotities, onbekende velden — blijft lokaal;
  `controleer_afscherming` bewijst dat per geval (prompt onafhankelijk van
  drie labelmutaties; geen labeltekst in de prompt, behalve een citaatlabel
  dat letterlijk in de modelinvoer zelf staat of een per-buurverwijzing die
  exact een aangeleverde buurterm is).
- **Transport**: alleen vormaanpassing. Een bron met `doc_id` krijgt
  `provider: documents` (zoals de orchestrator documentsnippets doorgeeft);
  een meegeleverd buur-`id` vervalt, zodat de productie (`normaliseer_buren`)
  de ID's toekent. Inhoud en labels blijven ongewijzigd.
- **Routes** (`route`): dezelfde volgorde als
  `ValidationOrchestratorV2._beoordeel_onderscheid` — zonder term, tekst of
  context, met een ongeldige burenlijst, met een geldige lege-ruimte-
  bevestiging zonder buren, of met te lange passages eindigt het geval zonder
  modelcall (offline nulcallroute, buiten het callbudget).
- **G-varianten** (`basisvariant`): de echte productieprompt met uitsluitend
  de ESS-05-instructieregel vervangen door de basistekst; een regeldiff
  bewijst dat verder niets verschilt.
- **G-buren** (`bouw_g_prompt_met_buren`, WP7-G-kanaal): verwante begrippen
  reizen via de normale keten (request → orchestratorstap → promptservice) en
  zijn dus in beide varianten identiek; ze vormen zelf geen variant.
"""

from __future__ import annotations

import copy
import difflib
import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from domain.context.contract import CONTEXT_VELDEN
from domain.ess03.contract import Intentie
from domain.ess05.contract import (
    CONTRACTVERSIE,
    ONDERSCHEIDINGEN,
    Buur,
    OngeldigeBurenlijstError,
    beoordeel_onderscheid,
    beoordeling_technische_fout,
    beoordelingsmateriaal,
    bereken_ess05_vingerafdruk,
    heeft_context,
    lege_ruimte_geldig,
    normaliseer_buren,
)
from domain.sources.normalisatie import Bronidentiteit, canoniseer_bronnen
from services.validation.ess05_assessment_service import bouw_beoordelingsprompt

__all__ = [
    "MODELVELDEN",
    "STATUSSEN",
    "InvoerfoutError",
    "TPrompt",
    "basisvariant",
    "bind_lege_ruimte",
    "bouw_g_prompt",
    "bouw_g_prompt_met_buren",
    "bouw_t_prompt",
    "controleer_afscherming",
    "controleer_promptlengte",
    "g_promptgrens",
    "huidige_g_instructie",
    "intentie",
    "modelprojectie",
    "per_buur_verwachtingen",
    "replay",
    "route",
    "sha_json",
    "transport",
    "valideer_gevallenbestand",
]

#: Het enige wat van een geval naar het model gaat (whitelist).
MODELVELDEN: tuple[str, ...] = (
    "begrip",
    "tekst",
    "toelichting",
    "categorie",
    "betekenisverduidelijking",
    "verduidelijking",
    "context",
    "bronnen",
    "buren",
    "uitgesloten_termen",
)
#: Lokaal, bepaalt alleen de route (deskundige bevestiging), nooit naar het model.
_ROUTEVELDEN = frozenset({"lege_ruimte", "lege_ruimte_bevestiging"})
STATUSSEN = frozenset({"pass", "fail", "review_required", "error", "not_evaluated"})
_BRONVELDEN = ("doc_id", "title", "snippet")
_BUURVELDEN = ("term", "definitie", "herkomst", "bevestigd")
#: Afgesproken eindsetschema: `verwacht_per_buur` als lijst van deze velden.
_PER_BUUR_TEKSTVELDEN = ("dragend_citaat", "ontbrekend_kenmerk", "grond")
_PER_BUUR_VELDEN = ("term", "distinction", *_PER_BUUR_TEKSTVELDEN)
#: Labels die letterlijk uit de beoordeelde invoer mogen komen (citaten).
_CITAATVELDEN = frozenset({"dragend_citaat", "ontbrekend_kenmerk"})
#: Pad van de per-buurverwijzing: `verwacht_per_buur[].term` noemt een
#: aangeleverde buur en mag alleen exact gelijk zijn aan een buurterm.
_BUURVERWIJZING = ("verwacht_per_buur", "term")
_CITAAT, _VERWIJZING = "citaat", "verwijzing"
#: Kortere labelteksten zijn vaste antwoordwoordenschat ('pass', 'unclear').
_MIN_LABELLENGTE = 12
_AFGESCHERMD = "<<AFGESCHERMD>>"
#: Grens van `Ess05AssessmentService` (constructordefault).
MAX_PASSAGE_CHARS = 8000
_INSTRUCTIEKOP = "- **Instructie:** "


class InvoerfoutError(ValueError):
    """Het gevallen- of G-invoerbestand voldoet niet; er gaat niets naar het model."""


def sha_json(data: Any) -> str:
    tekst = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(tekst.encode("utf-8")).hexdigest()


# --- schema ---------------------------------------------------------------------


def _is_tekstlijst(waarde: Any) -> bool:
    return isinstance(waarde, list) and all(isinstance(v, str) for v in waarde)


def _controleer_context(gid: str, context: Any) -> None:
    if not isinstance(context, Mapping):
        msg = f"{gid}: context moet een object met {CONTEXT_VELDEN} zijn"
        raise InvoerfoutError(msg)
    for veld, waarde in context.items():
        if veld not in CONTEXT_VELDEN or not _is_tekstlijst(waarde):
            msg = f"{gid}: context.{veld} is geen van de drie contextlijsten"
            raise InvoerfoutError(msg)


def _controleer_bronnen(gid: str, bronnen: Any) -> None:
    if not isinstance(bronnen, list):
        msg = f"{gid}: bronnen moet een lijst zijn"
        raise InvoerfoutError(msg)
    for i, bron in enumerate(bronnen):
        if not isinstance(bron, Mapping) or not all(
            isinstance(bron.get(v), str) and bron.get(v).strip() for v in _BRONVELDEN
        ):
            msg = f"{gid}: bron[{i}] mist {'/'.join(_BRONVELDEN)}"
            raise InvoerfoutError(msg)


def _per_buur_item(item: Any) -> dict[str, Any] | None:
    """Eén lijstitem in de vaste vorm, of None bij een vormfout."""
    if not isinstance(item, Mapping) or not isinstance(item.get("term"), str):
        return None
    if "distinction" not in item:
        return None
    if any(
        item.get(v) is not None and not isinstance(item.get(v), str)
        for v in _PER_BUUR_TEKSTVELDEN
    ):
        return None
    return {
        "term": item["term"],
        "distinction": item["distinction"],
        **{v: item.get(v) for v in _PER_BUUR_TEKSTVELDEN},
        **{k: copy.deepcopy(v) for k, v in item.items() if k not in _PER_BUUR_VELDEN},
    }


def per_buur_verwachtingen(geval: Mapping[str, Any]) -> list[dict[str, Any]]:
    """`verwacht_per_buur` in één vorm: een lijst `{term, distinction, …}`.

    Twee aangeleverde vormen (alleen vormadapter, geen labelbijstelling):
    de ontwikkelmapping `{term: distinction}` en de afgesproken eindsetlijst
    `[{term, distinction, dragend_citaat, ontbrekend_kenmerk, grond}]`.
    Uitgebreide velden (en onbekende extra velden) blijven bewaard voor de
    inhoudelijke beoordeling. Een vormfout wordt `InvoerfoutError`.
    """
    per_buur = geval.get("verwacht_per_buur")
    if per_buur is None:
        return []
    if isinstance(per_buur, Mapping):
        return [
            {
                "term": term,
                "distinction": label,
                **dict.fromkeys(_PER_BUUR_TEKSTVELDEN),
            }
            for term, label in per_buur.items()
        ]
    items = (
        [_per_buur_item(i) for i in per_buur] if isinstance(per_buur, list) else [None]
    )
    if any(i is None for i in items):
        msg = (
            f"{geval.get('id')}: verwacht_per_buur moet een mapping term→onderscheid "
            "of een lijst {term, distinction, dragend_citaat, ontbrekend_kenmerk, "
            "grond} zijn"
        )
        raise InvoerfoutError(msg)
    return [i for i in items if i is not None]


def _controleer_labels(gid: str, geval: Mapping[str, Any]) -> None:
    if geval.get("verwacht") not in STATUSSEN:
        msg = f"{gid}: verwacht moet een van {sorted(STATUSSEN)} zijn"
        raise InvoerfoutError(msg)
    if not isinstance(geval.get("grond"), str) or not geval["grond"].strip():
        msg = f"{gid}: grond (vooraf vastgelegde reden) ontbreekt"
        raise InvoerfoutError(msg)
    verwachtingen = per_buur_verwachtingen(geval)
    termen = {b.get("term") for b in geval.get("buren") or [] if isinstance(b, Mapping)}
    genoemd = [v["term"] for v in verwachtingen]
    if len(set(genoemd)) != len(genoemd) or any(
        v["term"] not in termen or v["distinction"] not in ONDERSCHEIDINGEN
        for v in verwachtingen
    ):
        msg = f"{gid}: verwacht_per_buur moet aangeleverde buren (elk één keer) op {ONDERSCHEIDINGEN} afbeelden"
        raise InvoerfoutError(msg)


def _controleer_geval(geval: Any, gezien: set[str]) -> None:
    if not isinstance(geval, Mapping) or not isinstance(geval.get("id"), str):
        msg = "elk geval moet een object met een tekst-id zijn"
        raise InvoerfoutError(msg)
    gid = geval["id"]
    if gid in gezien:
        msg = f"{gid}: dubbel id"
        raise InvoerfoutError(msg)
    gezien.add(gid)
    for veld in ("begrip", "tekst"):
        if not isinstance(geval.get(veld), str):
            msg = f"{gid}: {veld} moet tekst zijn"
            raise InvoerfoutError(msg)
    _controleer_context(gid, geval.get("context"))
    _controleer_bronnen(gid, geval.get("bronnen", []))
    if not isinstance(geval.get("buren", []), list):
        msg = f"{gid}: buren moet een lijst zijn"
        raise InvoerfoutError(msg)
    _controleer_labels(gid, geval)


def valideer_gevallenbestand(
    data: Any, *, herhaal_vereist: bool
) -> tuple[list[dict[str, Any]], list[str]]:
    """(gevallen, herhaal_ids) na fail-closed vormcontrole."""
    if not isinstance(data, Mapping) or not isinstance(data.get("gevallen"), list):
        msg = "bestand moet een object met een lijst 'gevallen' zijn"
        raise InvoerfoutError(msg)
    gezien: set[str] = set()
    for geval in data["gevallen"]:
        _controleer_geval(geval, gezien)
    herhaal = data.get("herhaal_ids")
    if herhaal is None and not herhaal_vereist:
        return [dict(g) for g in data["gevallen"]], []
    if not isinstance(herhaal, list) or len(herhaal) != 4 or len(set(herhaal)) != 4:
        msg = "herhaal_ids moet precies vier verschillende ids bevatten"
        raise InvoerfoutError(msg)
    onbekend = [h for h in herhaal if h not in gezien]
    if onbekend:
        msg = f"herhaal_ids noemt onbekend id: {onbekend}"
        raise InvoerfoutError(msg)
    return [dict(g) for g in data["gevallen"]], list(herhaal)


# --- afscherming en transport ------------------------------------------------------


def modelprojectie(geval: Mapping[str, Any]) -> dict[str, Any]:
    """Uitsluitend de velden die het model mag zien (diepe kopie)."""
    return {v: copy.deepcopy(geval[v]) for v in MODELVELDEN if v in geval}


def transport(projectie: Mapping[str, Any]) -> tuple[list[Any], list[Any]]:
    """(bronnen_ruw, buren_ruw) in productievorm; inhoud ongewijzigd."""
    bronnen = []
    for bron in projectie.get("bronnen") or []:
        kopie = dict(bron)
        if kopie.get("doc_id") and "provider" not in kopie:
            kopie["provider"] = "documents"
        bronnen.append(kopie)
    buren = []
    for buur in projectie.get("buren") or []:
        if isinstance(buur, Mapping):
            buren.append({k: buur[k] for k in _BUURVELDEN if k in buur})
        else:
            buren.append(buur)  # de productie weigert dit (route → error)
    return bronnen, buren


def intentie(projectie: Mapping[str, Any]) -> Intentie:
    return Intentie(
        toelichting=projectie.get("toelichting"),
        categorie=projectie.get("categorie"),
        betekenisverduidelijking=projectie.get("betekenisverduidelijking"),
        verduidelijking=projectie.get("verduidelijking"),
    )


@dataclass(frozen=True)
class TPrompt:
    """De T-prompt zoals de productiedienst hem opbouwt, plus zijn invoer."""

    teksten: tuple[str, str]
    bronnen: tuple[Bronidentiteit, ...]
    buren: tuple[Buur, ...]
    bronnen_ruw: list[Any]
    buren_ruw: list[Any]

    @property
    def sha256(self) -> str:
        """Zelfde hash als `Ess05AssessmentService` in `input.prompt_sha256`."""
        system, user = self.teksten
        return hashlib.sha256((system + "\n␞\n" + user).encode("utf-8")).hexdigest()


def bouw_t_prompt(projectie: Mapping[str, Any], norm: Mapping[str, str]) -> TPrompt:
    bronnen_ruw, buren_ruw = transport(projectie)
    bronnen = canoniseer_bronnen(bronnen_ruw)
    buren = normaliseer_buren(buren_ruw)
    teksten = bouw_beoordelingsprompt(
        projectie["begrip"],
        projectie["tekst"],
        projectie.get("context") or {},
        bronnen,
        buren=buren,
        intentie=intentie(projectie),
        norm=norm,
    )
    return TPrompt(teksten, bronnen, buren, bronnen_ruw, buren_ruw)


def _labelsoort(soort: str | None, pad: tuple[str, ...]) -> str | None:
    if soort is not None:
        return soort
    if pad == _BUURVERWIJZING:
        return _VERWIJZING
    return _CITAAT if pad and pad[-1] in _CITAATVELDEN else None


def _labelteksten(
    waarde: Any, *, soort: str | None = None, pad: tuple[str, ...] = ()
) -> list[tuple[str, str | None]]:
    """(tekst, soort) van alle niet-triviale labelteksten, recursief.

    `soort` is `citaat` (onder een citaatveld), `verwijzing` (exact het pad
    `verwacht_per_buur[].term`; lijsten tellen niet als padstap) of None.
    """
    if isinstance(waarde, str):
        vocabulaire = waarde in STATUSSEN or waarde in ONDERSCHEIDINGEN
        if len(waarde.strip()) >= _MIN_LABELLENGTE and not vocabulaire:
            return [(waarde.strip(), soort)]
        return []
    if isinstance(waarde, Mapping):
        return [
            t
            for k, v in waarde.items()
            for t in _labelteksten(
                v,
                soort=_labelsoort(soort, (*pad, str(k))),
                pad=(*pad, str(k)),
            )
        ]
    if isinstance(waarde, list | tuple):
        return [t for v in waarde for t in _labelteksten(v, soort=soort, pad=pad)]
    return []


def _buurtermen(projectie: Mapping[str, Any]) -> frozenset[str]:
    """De termen van de aangeleverde buren in de modelinvoer (gestript)."""
    return frozenset(
        b["term"].strip()
        for b in projectie.get("buren") or []
        if isinstance(b, Mapping) and isinstance(b.get("term"), str)
    )


def _invoerteksten(waarde: Any) -> list[str]:
    """Alle teksten van de modelinvoer (het beoordeelde materiaal), recursief."""
    if isinstance(waarde, str):
        return [waarde]
    if isinstance(waarde, Mapping):
        return [t for v in waarde.values() for t in _invoerteksten(v)]
    if isinstance(waarde, list | tuple):
        return [t for v in waarde for t in _invoerteksten(v)]
    return []


def _bladen_vervangen(waarde: Any) -> Any:
    """Zelfde structuur, elk blad (ook genest) vervangen door een merkwaarde."""
    if isinstance(waarde, Mapping):
        return {k: _bladen_vervangen(v) for k, v in waarde.items()}
    if isinstance(waarde, list | tuple):
        return [_bladen_vervangen(v) for v in waarde]
    return _AFGESCHERMD


def _labelmutaties(
    geval: Mapping[str, Any], labels: Mapping[str, Any]
) -> list[dict[str, Any]]:
    basis = dict(geval)
    return [
        {**basis, **dict.fromkeys(labels, _AFGESCHERMD)},
        {k: v for k, v in basis.items() if k not in labels},
        {**basis, **{k: _bladen_vervangen(v) for k, v in labels.items()}},
    ]


def controleer_afscherming(
    geval: Mapping[str, Any], teksten: tuple[str, str], norm: Mapping[str, str]
) -> None:
    """Fail-closed: de prompt hangt niet af van labels en lekt er geen tekst van.

    1. **Invloed** — drie mutaties van alle niet-invoervelden (vervangen,
       weglaten, elk genest blad vervangen) moeten exact dezelfde prompt geven.
    2. **Tekstlek** — een labeltekst in de prompt is een lek, tenzij het een
       citaatlabel (`dragend_citaat`, `ontbrekend_kenmerk`) is dat letterlijk
       in de modelinvoer zelf staat: een verwacht citaat hoort juist in de
       kandidaat of bron te staan; of de per-buurverwijzing
       `verwacht_per_buur[].term` die exact gelijk is aan een aangeleverde
       buurterm: die noemt de buur en staat daarom terecht in de prompt.
       Overige labelteksten (grond, doel, vraag) in de prompt blijven een
       weigering, ook als zij toevallig gelijk zijn aan een buurterm.
    """
    labels = {
        k: v
        for k, v in geval.items()
        if k not in MODELVELDEN and k not in _ROUTEVELDEN and k != "id"
    }
    for vervalst in _labelmutaties(geval, labels):
        if bouw_t_prompt(modelprojectie(vervalst), norm).teksten != teksten:
            msg = f"{geval.get('id')}: de prompt hangt af van afgeschermde velden"
            raise InvoerfoutError(msg)
    projectie = modelprojectie({k: geval[k] for k in geval if k not in labels})
    invoer = _invoerteksten(projectie)
    buurtermen = _buurtermen(projectie)
    for label, soort in _labelteksten(labels):
        if not any(label in tekst for tekst in teksten):
            continue
        if soort == _CITAAT and any(label in tekst for tekst in invoer):
            continue  # legitieme overlap met het beoordeelde materiaal
        if soort == _VERWIJZING and label in buurtermen:
            continue  # verwijzing naar een aangeleverde buur
        msg = f"{geval.get('id')}: afgeschermde labeltekst staat in de prompt"
        raise InvoerfoutError(msg)


# --- routes -------------------------------------------------------------------------


def _vingerafdruk(projectie: Mapping[str, Any], buren: tuple[Buur, ...]) -> str:
    bronnen_ruw, _ = transport(projectie)
    return bereken_ess05_vingerafdruk(
        projectie["begrip"],
        projectie["tekst"],
        projectie.get("context") or {},
        canoniseer_bronnen(bronnen_ruw),
        intentie=intentie(projectie),
        buren=buren,
    )


def bind_lege_ruimte(
    projectie: Mapping[str, Any], bevestiging: Mapping[str, Any]
) -> dict[str, Any]:
    """Synthetische deskundige bevestiging, gebonden aan de actuele vingerafdruk.

    Alleen voor de offline routeproef: in de app bindt de deskundige zelf.
    """
    _, buren_ruw = transport(projectie)
    return {
        "contract_version": CONTRACTVERSIE,
        "fingerprint": _vingerafdruk(projectie, normaliseer_buren(buren_ruw)),
        "grond": bevestiging.get("grond"),
        "actor": bevestiging.get("actor"),
        "synthetisch_gebonden_door_runner": True,
    }


def replay(projectie: Mapping[str, Any], **kwargs: Any) -> dict[str, Any]:
    """De productie-uitkomst (`beoordeel_onderscheid`) voor deze invoer, zonder AI."""
    bronnen_ruw, buren_ruw = transport(projectie)
    return beoordeel_onderscheid(
        projectie.get("begrip") or "",
        projectie.get("tekst") or "",
        projectie.get("context") or {},
        bronnen_ruw,
        intentie=intentie(projectie),
        buren=buren_ruw,
        uitgesloten_termen=projectie.get("uitgesloten_termen") or (),
        **kwargs,
    ).als_dict()


def route(
    projectie: Mapping[str, Any],
    lege_ruimte: Any,
    *,
    max_passage_chars: int = MAX_PASSAGE_CHARS,
) -> dict[str, Any]:
    """`{soort: nulcall, uitkomst, reden}` of `{soort: aanroep, fingerprint}`."""
    begrip = str(projectie.get("begrip") or "")
    tekst = str(projectie.get("tekst") or "")
    if (
        not begrip.strip()
        or not tekst.strip()
        or not heeft_context(projectie.get("context"))
    ):
        return {
            "soort": "nulcall",
            "reden": "geen term, tekst of context",
            "uitkomst": replay(projectie),
        }
    bronnen_ruw, buren_ruw = transport(projectie)
    try:
        actief = normaliseer_buren(buren_ruw)
    except OngeldigeBurenlijstError as exc:
        return {
            "soort": "nulcall",
            "reden": f"ongeldige burenlijst: {exc}",
            "uitkomst": replay(projectie),
        }
    fingerprint = _vingerafdruk(projectie, actief)
    if not actief and lege_ruimte_geldig(lege_ruimte, fingerprint):
        return {
            "soort": "nulcall",
            "reden": "geen buren en geldige lege-ruimtebevestiging",
            "uitkomst": replay(projectie, lege_ruimte=lege_ruimte),
        }
    # Hetzelfde materiaal als `Ess05AssessmentService` (ADR-003): ook context
    # en bedoelde betekenis tellen voor de passagegrens.
    materiaal = beoordelingsmateriaal(
        begrip,
        tekst,
        canoniseer_bronnen(bronnen_ruw),
        actief,
        contexten=projectie.get("context") or {},
        intentie=intentie(projectie),
    )
    te_lang = sorted(
        plek
        for plek, inhoud in materiaal.items()
        if plek != "definition" and len(inhoud) > max_passage_chars
    )
    if te_lang:
        document = beoordeling_technische_fout(
            fingerprint,
            "input_truncated",
            f"passage(s) boven {max_passage_chars} tekens: {', '.join(te_lang)}",
        )
        return {
            "soort": "nulcall",
            "reden": f"input_truncated vóór het netwerk: {', '.join(te_lang)}",
            "uitkomst": replay(projectie, lege_ruimte=lege_ruimte, assessment=document),
        }
    return {"soort": "aanroep", "fingerprint": fingerprint}


# --- G-varianten ----------------------------------------------------------------------


def huidige_g_instructie() -> str:
    from services.prompts.modules.json_based_rules_module import JSONBasedRulesModule

    tekst = JSONBasedRulesModule(
        "ESS", "def768_wp7", "def768_wp7", "", "", 1
    )._get_instruction_for_rule("ESS-05")
    if not tekst:
        msg = "geen actuele ESS-05-generatie-instructie gevonden"
        raise InvoerfoutError(msg)
    return tekst


def basisvariant(
    prompt: str, huidig: str, basis: str
) -> tuple[str, dict[str, list[str]]]:
    """De prompt met uitsluitend de ESS-05-instructieregel vervangen; plus bewijs."""
    oud = f"{_INSTRUCTIEKOP}{huidig}"
    regels = prompt.split("\n")
    posities = [i for i, r in enumerate(regels) if r == oud]
    if len(posities) != 1:
        msg = (
            f"de actuele ESS-05-instructieregel moet precies één keer in de prompt "
            f"staan (gevonden: {len(posities)})"
        )
        raise InvoerfoutError(msg)
    nieuw_regels = list(regels)
    nieuw_regels[posities[0]] = f"{_INSTRUCTIEKOP}{basis}"
    verschil = {"verwijderd": [], "toegevoegd": []}
    for regel in difflib.ndiff(regels, nieuw_regels):
        if regel.startswith("- "):
            verschil["verwijderd"].append(regel[2:])
        elif regel.startswith("+ "):
            verschil["toegevoegd"].append(regel[2:])
    if verschil != {"verwijderd": [oud], "toegevoegd": [nieuw_regels[posities[0]]]}:
        msg = f"varianten verschillen in meer dan de instructieregel: {verschil}"
        raise InvoerfoutError(msg)
    return "\n".join(nieuw_regels), verschil


def _document(doc: Mapping[str, Any]) -> dict[str, Any]:
    """Zelfde vorm als de orchestrator (PHASE 2.9) documentsnippets doorgeeft."""
    return {
        "provider": "documents",
        "title": doc["title"],
        "url": doc.get("url"),
        "snippet": doc["snippet"],
        "score": 0.0,
        "used_in_prompt": True,
        "doc_id": doc["doc_id"],
        "source_label": "Geüpload document",
    }


class _VasteBurenbron:
    """Lokale standin voor de repositorylookup (`zoek_ess05_buren`) in de proef.

    De rijen (`repository_buren`: id, begrip, definitie) gelden als verse
    repository-buren in dezelfde context; er is geen productie-DB.
    """

    def __init__(self, rijen: Any) -> None:
        self._rijen = copy.deepcopy(list(rijen or []))

    def zoek_ess05_buren(
        self, begrip: str, contexten: Mapping[str, Any], eigen_id: Any
    ) -> list[dict[str, Any]]:
        return copy.deepcopy(self._rijen)


def g_promptgrens() -> int:
    """De harde kap op de complete generatieprompt, uit `PromptServiceV2` zelf."""
    from services.prompts.prompt_service_v2 import PromptServiceV2

    return PromptServiceV2().max_prompt_lengte()


def _te_lang(geval_id: str, variant: str, lengte: int, maximum: int) -> str:
    return (
        f"{geval_id}: generatieprompt te lang ({variant}: {lengte} tekens, "
        f"maximum {maximum}); geweigerd vóór het model, niets afgekapt"
    )


def controleer_promptlengte(geval_id: str, variant: str, tekst: str) -> None:
    """Elke G-variant onder dezelfde grens als de productieketen, vóór het netwerk."""
    maximum = g_promptgrens()
    if maximum < len(tekst):
        raise InvoerfoutError(_te_lang(geval_id, variant, len(tekst), maximum))


async def bouw_g_prompt(invoer: Mapping[str, Any], *, burenbron: Any = None) -> str:
    """De echte productiegeneratieprompt voor één G-invoer (zie `…_met_buren`)."""
    tekst, _ = await bouw_g_prompt_met_buren(invoer, burenbron=burenbron)
    return tekst


async def bouw_g_prompt_met_buren(
    invoer: Mapping[str, Any], *, burenbron: Any = None
) -> tuple[str, dict[str, Any]]:
    """(prompt, burenkwitantie) via de normale keten tot aan de providergrens.

    Het request draagt dezelfde velden als `ServiceAdapter.generate_definition`
    vult (begrip, drie contextlijsten, categorie, `ess05_buren`,
    `gerelateerde_begrippen`); de buren worden samengesteld door de
    orchestratorstap zelf (`DefinitionOrchestratorV2._met_generatieburen`) en
    de prompt door `PromptServiceV2`. `burenbron` is de repository (in tests)
    of de lokale standin met `repository_buren`. Aandachtspunten en andere
    labels gaan niet mee. Fail-closed als de burensamenstelling faalt, als het
    burenblok, een documentpassage of de actuele ESS-05-normuitleg niet in de
    prompt staat (een verouderde regelcache op schijf zou anders stil een oud
    record tonen).
    """
    from types import SimpleNamespace

    from services.interfaces import GenerationRequest
    from services.orchestrators.definition_orchestrator_v2 import (
        DefinitionOrchestratorV2,
    )
    from services.prompts.ess05_generatieburen import (
        GENERATIEBUREN_SLEUTEL,
        generatieburen_blok,
        generatieburen_kwitantie,
    )
    from services.prompts.modular_prompt_adapter import PromptTeLangError
    from services.prompts.prompt_service_v2 import PromptServiceV2
    from services.validation.ess05_assessment_service import laad_ess05_norm

    request = GenerationRequest(
        id=f"def768-wp7-{invoer['id']}",
        begrip=invoer["begrip"],
        organisatorische_context=list(invoer.get("organisatorische_context") or []),
        juridische_context=list(invoer.get("juridische_context") or []),
        wettelijke_basis=list(invoer.get("wettelijke_basis") or []),
        ontologische_categorie=invoer.get("ontologische_categorie"),
        actor="def768_wp7_proef",
        ess05_buren=copy.deepcopy(invoer.get("ess05_buren")),
        gerelateerde_begrippen=copy.deepcopy(invoer.get("gerelateerde_begrippen")),
    )
    if burenbron is None:
        burenbron = _VasteBurenbron(invoer.get("repository_buren"))
    context = DefinitionOrchestratorV2._met_generatieburen(
        SimpleNamespace(repository=burenbron),  # type: ignore[arg-type]
        request,
        {"documents": {"snippets": [_document(d) for d in invoer["documenten"]]}},
    )
    verzameling = context[GENERATIEBUREN_SLEUTEL]
    if verzameling.get("status") != "ok":
        msg = (
            f"{invoer['id']}: burensamenstelling mislukt "
            f"({verzameling.get('reden')}: {verzameling.get('detail')})"
        )
        raise InvoerfoutError(msg)
    try:
        resultaat = await PromptServiceV2().build_generation_prompt(
            request, context=context
        )
    except PromptTeLangError as exc:
        raise InvoerfoutError(
            _te_lang(invoer["id"], "actueel", exc.lengte, exc.maximum)
        ) from exc
    tekst = resultaat.text
    controleer_promptlengte(invoer["id"], "actueel", tekst)
    blok = generatieburen_blok(verzameling)
    if blok is not None and blok not in tekst:
        msg = f"{invoer['id']}: het burenblok staat niet in de prompt"
        raise InvoerfoutError(msg)
    for doc in invoer["documenten"]:
        if doc["snippet"] not in tekst:
            msg = f"{invoer['id']}: documentpassage {doc['doc_id']} staat niet in de prompt"
            raise InvoerfoutError(msg)
    uitleg = laad_ess05_norm()["uitleg"]
    if uitleg not in tekst:
        msg = (
            f"{invoer['id']}: de actuele ESS-05-normuitleg staat niet in de prompt "
            "(verouderde regelcache?)"
        )
        raise InvoerfoutError(msg)
    return tekst, generatieburen_kwitantie(verzameling) or {}
