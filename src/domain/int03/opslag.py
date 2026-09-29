"""INT-03 (DEF-772 WP4): de opgeslagen AI-verwijzingsbeoordeling, gebonden aan de kandidaat.

De persistentielaag bewaart de door de wrapper verkregen INT-03-beoordeling
(store-ready document van `domain.int03.contract`) in de generatieregistratie
van het record (`generation_prompt_data`, JSON — geen kolom, geen
schemawijziging) onder de sleutels hieronder, met een append-only historie
van vervangen documenten (ESS-03-patroon, DEF-766). Of het document nog bij
dít record hoort, beslist uitsluitend de replay van het contract
(`beoordeel_verwijzingen`): vingerafdruk over term, exacte tekst, drie
contextlijsten en toelichting, plus de actuele prompt-, norm- en
provider/modelbinding. Een afwijking maakt de beoordeling historisch —
zichtbaar, nooit toegepast, nooit stil pass.

`exportdocument` is de gestructureerde exportvorm: de actuele uitkomst van de
replay mét binding, herkomst (AI-beoordeling, geen deskundigenoordeel), het
volledige document en de tellingen — zodat een export nooit een stale of
ontbrekende beoordeling als actuele goedkeuring draagt. `exportregels` is de
leesbare TXT-vorm van datzelfde document. Geen cijfer, geen poort.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from domain.context.contract import CONTEXT_VELDEN
from domain.int03.contract import (
    ASSESSMENT_STATUSSEN,
    Beoordelingsbinding,
    beoordeel_verwijzingen,
)

__all__ = [
    "EXPORTSCHEMA",
    "HERKOMST",
    "INT03_ASSESSMENT_HISTORY_KEY",
    "INT03_ASSESSMENT_KEY",
    "INT03_OWNED_KEYS",
    "exportdocument",
    "exportregels",
    "vormfout",
]

#: Sleutels in `generation_prompt_data` (DEF-772): de actuele
#: AI-verwijzingsbeoordeling van INT-03 en de append-only historie van
#: vervangen beoordelingen. Geen kolom, geen schema; een vervallen binding
#: herleeft nooit — alleen een nieuwe toetsing levert een actuele beoordeling.
INT03_ASSESSMENT_KEY = "int03_assessment"
INT03_ASSESSMENT_HISTORY_KEY = "int03_assessment_history"
#: Sleutels die uitsluitend de persistentielaag schrijft; een ruwe
#: registratie-aanlevering kan ze niet overschrijven of wissen.
INT03_OWNED_KEYS: tuple[str, ...] = (
    INT03_ASSESSMENT_KEY,
    INT03_ASSESSMENT_HISTORY_KEY,
)
EXPORTSCHEMA = "def772-int03-export/1"
#: De herkomst zoals de export haar benoemt: nooit een menselijk oordeel.
HERKOMST = "AI-beoordeling (geen deskundigenoordeel, geen vaststelling)"

_STATUSLABEL: dict[str, str] = {
    "pass": "voldoet",
    "fail": "voldoet niet",
    "review_required": "nog te beoordelen",
    "error": "technisch probleem",
    "not_evaluated": "niet beoordeeld",
}
_VERWIJZINGSLABEL: dict[str, str] = {
    "clear": "eenduidig antecedent",
    "ambiguous": "meer plausibele lezingen",
    "no_antecedent": "geen antecedent in de definitie",
    "non_referring": "niet verwijzend gebruikt",
    "undetermined": "nog te beoordelen",
}


def _tekst(waarde: Any) -> str:
    return waarde.strip() if isinstance(waarde, str) else ""


def vormfout(invoer: Any) -> str | None:
    """Waarom `invoer` nooit een INT-03-beoordelingsdocument kan zijn, of None.

    Vormcontrole vóór een schrijfactie: een object met een niet-lege
    vingerafdruk en een bekende technische status. Of het document nog bij
    het record hoort, beslist de replay bij het lezen; hier wordt alleen
    geweigerd wat nooit een beoordeling kan zijn.
    """
    if not isinstance(invoer, Mapping) or not _tekst(invoer.get("fingerprint")):
        return "int03_assessment moet een dict met een niet-lege fingerprint zijn"
    if invoer.get("status") not in ASSESSMENT_STATUSSEN:
        return f"int03_assessment heeft een onbekende status {invoer.get('status')!r}"
    return None


def _bindingsdeel(samenvatting: Mapping[str, Any]) -> dict[str, Any]:
    return {
        sleutel: samenvatting.get(sleutel)
        for sleutel in ("prompt_version", "norm_sha256", "provider", "model")
    }


def _lijst(waarde: Any) -> list[Any]:
    if isinstance(waarde, (list, tuple)):
        return list(waarde)
    return [waarde] if waarde else []


def _kandidaat(
    begrip: str,
    tekst: str,
    contexten: Mapping[str, Any] | None,
    toelichting: str | None,
    velden: Mapping[str, str] | None,
) -> dict[str, Any]:
    """De kandidaat waaraan de replay bond — exact wat de export draagt — en
    uit welke exportvelden die waarden komen, zodat een export met twee
    teksten (origineel én aangepast) of een vervangen toelichting niet
    misleidt over wat er beoordeeld is."""
    contexten = contexten or {}
    return {
        "begrip": str(begrip or ""),
        "text": str(tekst or ""),
        "toelichting": _tekst(toelichting) or None,
        "context": {veld: _lijst(contexten.get(veld)) for veld in CONTEXT_VELDEN},
        "fields": dict(velden or {}),
    }


def exportdocument(
    begrip: str,
    tekst: str,
    contexten: Mapping[str, Any] | None,
    toelichting: str | None,
    *,
    assessment: Any,
    binding: Beoordelingsbinding | None,
    history_count: int = 0,
    kandidaatvelden: Mapping[str, str] | None = None,
) -> dict[str, Any] | None:
    """De gestructureerde exportvorm van de opgeslagen INT-03-beoordeling.

    Replay van het document op exact deze kandidaat en de actuele binding
    (geen AI-aanroep): status, of zij is toegepast (`applied`) dan wel
    historisch/ongeldig met de reden, het (eventueel historische) verdict en
    de bevinding, de verwijzingen mét kandidaten (alleen wanneer toegepast),
    de vingerafdruk, de binding van het document en de verwachte binding,
    de gebonden kandidaat (`candidate`: begrip, tekst, toelichting, context
    en — via `kandidaatvelden` — uit welke exportvelden die komen) en het
    volledige document. `None` zonder opgeslagen beoordeling: er wordt
    niets verzonnen; de exportlagen maken dat zichtbaar als niet beoordeeld.
    """
    if assessment is None:
        return None
    uitkomst = beoordeel_verwijzingen(
        begrip, tekst, contexten, toelichting, assessment=assessment, binding=binding
    ).als_dict()
    samenvatting = dict((uitkomst.get("review") or {}).get("assessment") or {})
    delen = uitkomst.get("parts") or []
    deel = dict(delen[0]) if delen else {}
    toegepast = samenvatting.get("applied") is True
    oordeel = assessment.get("judgment") if isinstance(assessment, Mapping) else None
    verwijzingen = (
        deepcopy(list(oordeel.get("references") or []))
        if toegepast and isinstance(oordeel, Mapping)
        else []
    )
    return {
        "schema": EXPORTSCHEMA,
        "rule_id": "INT-03",
        "herkomst": HERKOMST,
        "contract_version": uitkomst.get("contract_version"),
        "status": uitkomst.get("status"),
        "score": None,
        "applied": toegepast,
        "historical": bool(samenvatting.get("historical")),
        "invalid": bool(samenvatting.get("invalid")),
        "reason": deel.get("reason") if toegepast else samenvatting.get("reason"),
        "action": deel.get("action"),
        "verdict": samenvatting.get("verdict"),
        "finding": samenvatting.get("finding"),
        "question": samenvatting.get("question"),
        "references": verwijzingen,
        "fingerprint": uitkomst.get("fingerprint"),
        "binding": _bindingsdeel(samenvatting),
        "expected_binding": samenvatting.get("expected_binding"),
        "candidate": _kandidaat(begrip, tekst, contexten, toelichting, kandidaatvelden),
        "history_count": int(history_count),
        "document": (
            deepcopy(dict(assessment)) if isinstance(assessment, Mapping) else None
        ),
    }


def _kandidatentekst(kandidaten: Any) -> str:
    return ", ".join(
        f"'{k.get('quote')}' ({k.get('reason')})"
        for k in (kandidaten if isinstance(kandidaten, list) else [])
        if isinstance(k, Mapping)
    )


def _verwijzingsregel(verwijzing: Mapping[str, Any]) -> str:
    status = str(verwijzing.get("status") or "")
    label = _VERWIJZINGSLABEL.get(status, status)
    regel = f"  - '{verwijzing.get('word')}' in “{verwijzing.get('passage')}”: {label}"
    kandidaten = _kandidatentekst(verwijzing.get("candidates"))
    if kandidaten:
        regel += f" — kandidaten: {kandidaten}"
    lezing = _tekst(verwijzing.get("reading"))
    if lezing:
        regel += f" ({lezing})"
    return regel


def exportregels(gelezen: Mapping[str, Any] | None) -> list[str]:
    """Leesbare regels voor de tekstexport; leeg zonder opgeslagen beoordeling."""
    if not gelezen:
        return []
    status = _STATUSLABEL.get(str(gelezen.get("status")), str(gelezen.get("status")))
    binding = gelezen.get("binding") or {}
    model = binding.get("model") if isinstance(binding, Mapping) else None
    provider = binding.get("provider") if isinstance(binding, Mapping) else None
    attributie = f" · {provider or 'onbekende provider'} · {model}" if model else ""
    kop = f"INT-03 — {status} (geen cijfer; AI-beoordeling{attributie})"
    if not gelezen.get("applied"):
        kop += f" — niet toegepast: {gelezen.get('reason')}"
    regels = [kop, f"  {gelezen.get('reason') or ''}".rstrip()]
    kandidaat = gelezen.get("candidate")
    if isinstance(kandidaat, Mapping):
        # Aan welke kandidaat de replay bond (de geëxporteerde), en uit welk
        # tekstveld — een tweede tekst in de export is dus niet de beoordeelde.
        velden = kandidaat.get("fields")
        tekstveld = velden.get("text") if isinstance(velden, Mapping) else None
        toelichting = (
            "aanwezig (zie Toelichting)"
            if _tekst(kandidaat.get("toelichting"))
            else "geen"
        )
        regels.append(
            f"  Gebonden aan: '{kandidaat.get('begrip')}' — {tekstveld or 'tekst'}: "
            f"“{kandidaat.get('text')}” — toelichting: {toelichting}"
        )
    for verwijzing in gelezen.get("references") or []:
        if isinstance(verwijzing, Mapping):
            regels.append(_verwijzingsregel(verwijzing))
    vraag = _tekst(gelezen.get("question"))
    if gelezen.get("applied") and vraag:
        regels.append(f"  Vraag: {vraag}")
    if gelezen.get("action"):
        regels.append(f"  Vervolgstap: {gelezen.get('action')}")
    return regels
