"""CON-02 — het broncontract (DEF-743, besluiten van 15 september 2026).

Pure domeinlogica, zonder Streamlit, database of AI-client. De evaluator
(`services.validation.evaluators.source_evidence`) roept `beoordeel_bronbasis`
aan en vertaalt de uitkomst naar het runtimecontract; de beoordelingsservice
(`services.validation.source_assessment_service`) gebruikt `valideer_beoordeling`
om de modeluitvoer fail-closed te valideren; de persistentielaag gebruikt
`bereken_bronvingerafdruk` en `valideer_bronreview` om opgeslagen gegevens aan
exact dezelfde invoer te binden.

Wat de regel toetst — drie onafhankelijke onderdelen, elk met eigen status:

- **brongezag/toepasselijkheid** (`source_authority`): is de bron passend en
  gezaghebbend voor begrip, betekenis, context en peildatum? Aanvoerroute,
  zoekscore, confidence en routelabels zijn geen gezag.
- **betekenissteun** (`semantic_support`): dekt de bron de bepalende
  kenmerken, beperkingen en uitzonderingen van de definitie?
- **verwijskwaliteit** (`reference_quality`): is de bron precies en beknopt
  terugvindbaar via een gerichte verwijzing? Een correcte inline citatie is
  geen zelfstandige afkeurgrond.

Rolverdeling: **code** controleert technische feiten en citaatbestaan (is het
citaat werkelijk aanwezig in dié aangeleverde passage?); de **AI** beoordeelt
gezag, toepasselijkheid en betekenissteun met bewijsplaatsen en onzekerheden;
de **deskundige** kan twee uitzonderingen vastleggen (geen passende bron na
gedocumenteerd zoeken; bestaande bron zonder bruikbare hyperlink). Een
uitzondering blijft zichtbaar een uitzondering — nooit een gewoon 'Voldoet'.

Uitkomsten: *Voldoet* vereist positieve, onderbouwde toepasselijke controles;
*Voldoet niet* vereist een aantoonbare tekortkoming (met citaat); *Nog te
beoordelen* behoudt ontbrekend bewijs of oordeel; een technische fout is
apart herkenbaar. Geen cijfer.

Alles is gebonden aan een vingerafdruk over term, exacte kandidaattekst, de
drie contextlijsten, peildatum, de canonieke bronidentiteit (inhoudshash,
versie, url, vindplaats, titel, profiel en feitelijke metadata) en de
beleidsversie. Wijzigt daar iets, dan geldt een eerdere beoordeling of
uitzondering niet meer.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from collections.abc import Iterable, Mapping
from copy import deepcopy
from dataclasses import dataclass, replace
from typing import Any

from domain.context.contract import CONTEXT_VELDEN, Deeluitkomst, is_versienummer
from domain.context.normalisatie import contextsleutel
from domain.sources.normalisatie import (
    PROFIELEN,
    Bronidentiteit,
    bron_op_id,
    canoniseer_bronnen,
)

logger = logging.getLogger(__name__)

__all__ = [
    "AI_ONDERDELEN",
    "ASSESSMENT_STATUSSEN",
    "BASIS_ASSESSMENT",
    "BASIS_REVIEW",
    "CONTRACTVERSIE",
    "ONDERDEEL_GEZAG",
    "ONDERDEEL_STEUN",
    "ONDERDEEL_UITZONDERING_GEEN_BRON",
    "ONDERDEEL_VERWIJZING",
    "REVIEW_TYPE_CORRECTIE",
    "REVIEW_TYPE_GEEN_BRON",
    "REVIEW_TYPE_VERWIJZING",
    "STATUS_ERROR",
    "STATUS_FAIL",
    "STATUS_OPEN",
    "STATUS_PASS",
    "BronUitkomst",
    "GevalideerdDeel",
    "beoordeel_bronbasis",
    "beoordeling_niet_beschikbaar",
    "beoordeling_technische_fout",
    "bereken_bronvingerafdruk",
    "valideer_beoordeling",
    "valideer_bronreview",
    "valideer_onderdelen",
    "verzonden_passages",
    "vind_citaat",
]

#: Beleidsversie van dit contract; onderdeel van de vingerafdruk.
CONTRACTVERSIE = "con02/1"

ONDERDEEL_GEZAG = "source_authority"
ONDERDEEL_STEUN = "semantic_support"
ONDERDEEL_VERWIJZING = "reference_quality"
ONDERDEEL_UITZONDERING_GEEN_BRON = "expert_exception:no_source"
AI_ONDERDELEN: tuple[str, str, str] = (
    ONDERDEEL_GEZAG,
    ONDERDEEL_STEUN,
    ONDERDEEL_VERWIJZING,
)

STATUS_PASS = "pass"
STATUS_FAIL = "fail"
STATUS_OPEN = "review_required"
STATUS_ERROR = "error"
_DEELSTATUSSEN = frozenset({STATUS_PASS, STATUS_FAIL, STATUS_OPEN})

#: Waarde van `Deeluitkomst.field`: waar het oordeel vandaan komt.
BASIS_ASSESSMENT = "source_assessment"
BASIS_REVIEW = "source_review"

#: De twee goedgekeurde deskundige uitzonderingen (bevroren platte vorm) en de
#: deskundige correctie van één AI-onderdeel (geen uitzondering: het
#: onderdeel krijgt het deskundige oordeel mét gebonden bewijs; het
#: oorspronkelijke AI-oordeel blijft zichtbaar in het resultaat).
REVIEW_TYPE_VERWIJZING = "reference_exception"
REVIEW_TYPE_GEEN_BRON = "no_appropriate_source"
REVIEW_TYPE_CORRECTIE = "part_correction"
_BEKENDE_REVIEW_TYPES = frozenset(
    {REVIEW_TYPE_VERWIJZING, REVIEW_TYPE_GEEN_BRON, REVIEW_TYPE_CORRECTIE}
)

#: Technische status van een verkregen beoordeling.
ASSESSMENT_STATUSSEN: tuple[str, ...] = (
    "assessed",
    "error",
    "no_sources",
    "unavailable",
)

_ONDERDEELNAAM = {
    ONDERDEEL_GEZAG: "brongezag/toepasselijkheid",
    ONDERDEEL_STEUN: "betekenissteun",
    ONDERDEEL_VERWIJZING: "verwijskwaliteit",
}

_ACTIE_GEEN_BRONNEN = (
    "Lever passende bronpassages aan (upload, RAG of web), of laat een deskundige "
    "na gedocumenteerd zoeken het ontbreken van een passende bron als uitzondering "
    "vastleggen."
)
_ACTIE_NIET_BEOORDEELD = (
    "Valideer opnieuw; de bronbeoordeling wordt daarbij automatisch uitgevoerd."
)
_ACTIE_DEELFOUT = (
    "Controleer opnieuw. Blijft dit terugkomen, meld het dan als technisch probleem."
)
_ACTIE_OPEN = (
    "Laat een deskundige het onderdeel beoordelen of lever aanvullend bronbewijs aan."
)
_ACTIE_FAIL = (
    "Pas de definitie aan zodat zij de bron volgt, of lever een passende bron aan. "
    "Een verbetervoorstel kan apart worden aangevraagd; er is geen automatisch herstel."
)
_ACTIE_PASS = "Geen actie nodig."
_ACTIE_UITZONDERING = (
    "Geen verdere actie voor dit onderdeel; de uitzondering blijft zichtbaar en "
    "vaststelling blijft een deskundig besluit (DEF-630)."
)

_WHITESPACE = re.compile(r"\s+")


# --- vingerafdruk en bewijstoets -------------------------------------------------


def _canoniek(bronnen: Any) -> tuple[Bronidentiteit, ...]:
    if isinstance(bronnen, tuple) and all(
        isinstance(b, Bronidentiteit) for b in bronnen
    ):
        return bronnen
    if (
        isinstance(bronnen, list | tuple)
        and bronnen
        and all(isinstance(b, Bronidentiteit) for b in bronnen)
    ):
        return tuple(sorted(bronnen, key=lambda b: (b.source_id, b.content_hash)))
    return canoniseer_bronnen(bronnen)


def _peildatum(waarde: Any) -> str | None:
    if waarde is None or isinstance(waarde, bool):
        return None
    tekst = str(waarde).strip()
    return tekst or None


def bereken_bronvingerafdruk(
    begrip: str,
    tekst: str,
    contexten: Mapping[str, Any] | None,
    bronnen: Any,
    *,
    peildatum: str | None = None,
) -> str:
    """Bind een beoordeling aan term, exacte tekst, context, peildatum en bronnen.

    `bronnen` mag de ruwe aangeleverde lijst zijn of een canonieke tuple. Per
    bron gaan id, inhoudshash, versie, url, vindplaats, titel, profiel en de
    feitelijke metadata mee (`Bronidentiteit.vingerafdrukdeel`): een wijziging
    in bijvoorbeeld vaststellingsstatus of rechtsgebied raakt het oordeel over
    gezag en verwijzing en maakt een eerdere beoordeling dus stale. Zoekscore
    en promptvlaggen zitten er bewust niet in.
    """
    contexten = contexten or {}
    bron = {
        "versie": CONTRACTVERSIE,
        "term": str(begrip or ""),
        "tekst": str(tekst or ""),
        "context": {
            veld: list(contextsleutel(contexten.get(veld))) for veld in CONTEXT_VELDEN
        },
        "peildatum": _peildatum(peildatum),
        "bronnen": [b.vingerafdrukdeel() for b in _canoniek(bronnen)],
    }
    return hashlib.sha256(
        json.dumps(bron, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def _genormaliseerd(tekst: str) -> str:
    return _WHITESPACE.sub(" ", str(tekst or "")).strip()


def vind_citaat(passage: str, citaat: str) -> bool:
    """Staat het citaat letterlijk in de passage? Whitespace-tolerant, verder exact.

    Dit is de enige bewijstoets van de code: bestaan, geen interpretatie.
    """
    citaat_norm = _genormaliseerd(citaat)
    if not citaat_norm:
        return False
    return citaat_norm in _genormaliseerd(passage)


# --- beoordelingsdocumenten (store-ready dicts) ----------------------------------


def beoordeling_niet_beschikbaar(fingerprint: str, reden: str) -> dict[str, Any]:
    """Een beoordeling die niet kon worden verkregen: geen dienst geïnjecteerd."""
    return {
        "contract_version": CONTRACTVERSIE,
        "prompt_version": None,
        "fingerprint": fingerprint,
        "status": "unavailable",
        "error": None,
        "assessed_at": None,
        "attribution": {
            "provider": None,
            "model": None,
            "task_type": None,
            "cached": None,
            "tokens_used": None,
        },
        "peildatum": None,
        "sources": [],
        "parts": {},
        "rejected": [],
        "raw_response_sha256": None,
        "assessment_receipt": None,
        "reason": str(reden or "bronbeoordelingsdienst niet beschikbaar"),
    }


def beoordeling_technische_fout(
    fingerprint: str,
    soort: str,
    melding: str,
    *,
    sources: Iterable[Bronidentiteit] = (),
    prompt_version: str | None = None,
    attribution: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Een beoordeling die technisch mislukte (timeout, misvormd antwoord, kwitantiefout)."""
    return {
        "contract_version": CONTRACTVERSIE,
        "prompt_version": prompt_version,
        "fingerprint": fingerprint,
        "status": "error",
        "error": {"type": str(soort or "unknown"), "message": str(melding or "")},
        "assessed_at": None,
        "attribution": {
            "provider": None,
            "model": None,
            "task_type": None,
            "cached": None,
            "tokens_used": None,
            **dict(attribution or {}),
        },
        "peildatum": None,
        "sources": [b.als_dict() for b in sources],
        "parts": {},
        "rejected": [],
        "raw_response_sha256": None,
        "assessment_receipt": None,
    }


# --- validatie van de AI-beoordeling ---------------------------------------------


@dataclass(frozen=True)
class GevalideerdDeel:
    """Eén AI-onderdeel na de codecontrole: status, reden en geverifieerd bewijs."""

    status: str
    reason: str
    uncertainty: str | None
    evidence: tuple[dict[str, Any], ...]
    extra: dict[str, Any]

    def als_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "reason": self.reason,
            "uncertainty": self.uncertainty,
            "evidence": [dict(e) for e in self.evidence],
            **deepcopy(self.extra),
        }


def _tekst(waarde: Any) -> str:
    return waarde.strip() if isinstance(waarde, str) else ""


def _eerste_reden(controles: Iterable[tuple[bool, str]]) -> str | None:
    """De reden van de eerste falende controle, in aanroepvolgorde; anders None.

    Mechanische vorm van een keten guard-clauses: dezelfde volgorde, dezelfde
    eerste tekortkoming, één uitgang.
    """
    for faalt, reden in controles:
        if faalt:
            return reden
    return None


def _citaattekst(waarde: Any) -> str:
    """Het citaat als tekst; alles wat geen tekst is, is een leeg citaat."""
    return waarde if isinstance(waarde, str) else ""


def _verifieer_bewijs(
    ruw: Any, bronnen: tuple[Bronidentiteit, ...], onderdeel: str, rejected: list[dict]
) -> tuple[dict[str, Any], ...]:
    """Alleen bewijs dat werkelijk in een bestaande, aangeleverde passage staat."""
    geverifieerd: list[dict[str, Any]] = []
    for item in ruw if isinstance(ruw, list) else ():
        if not isinstance(item, Mapping):
            rejected.append(
                {
                    "part": onderdeel,
                    "reason": "bewijsitem is geen object",
                    "detail": repr(item)[:120],
                }
            )
            continue
        source_id = item.get("source_id")
        citaat = _citaattekst(item.get("quote"))
        bron = bron_op_id(bronnen, source_id)
        if bron is None:
            rejected.append(
                {
                    "part": onderdeel,
                    "reason": "onbekend bron-id",
                    "detail": str(source_id)[:120],
                }
            )
            continue
        if not citaat.strip():
            rejected.append(
                {"part": onderdeel, "reason": "leeg citaat", "detail": bron.source_id}
            )
            continue
        if not vind_citaat(bron.passage, citaat):
            rejected.append(
                {
                    "part": onderdeel,
                    "reason": "citaat niet in bron",
                    "detail": f"{bron.source_id}: {citaat[:120]}",
                }
            )
            continue
        geverifieerd.append(
            {"source_id": bron.source_id, "quote": citaat, "locator": bron.locator}
        )
    return tuple(geverifieerd)


def _valideer_bronlijst(
    ruw: Any,
    bronnen: tuple[Bronidentiteit, ...],
    onderdeel: str,
    rejected: list[dict],
    *,
    profiel: bool,
) -> list[dict[str, Any]]:
    """Per-bron-oordelen: alleen bestaande id's en, waar van toepassing, bekende profielen."""
    geldig: list[dict[str, Any]] = []
    for item in ruw if isinstance(ruw, list) else ():
        if not isinstance(item, Mapping):
            continue
        bron = bron_op_id(bronnen, item.get("source_id"))
        if bron is None:
            rejected.append(
                {
                    "part": onderdeel,
                    "reason": "onbekend bron-id",
                    "detail": str(item.get("source_id"))[:120],
                }
            )
            continue
        entry: dict[str, Any] = {
            "source_id": bron.source_id,
            "reason": _tekst(item.get("reason")),
        }
        if profiel:
            gekozen = item.get("profile")
            if gekozen not in PROFIELEN:
                rejected.append(
                    {
                        "part": onderdeel,
                        "reason": "onbekend profiel",
                        "detail": f"{bron.source_id}: {gekozen!r}"[:120],
                    }
                )
                continue
            entry["profile"] = gekozen
            entry["applicable"] = (
                item.get("applicable")
                if isinstance(item.get("applicable"), bool)
                else None
            )
        else:
            entry["locatable"] = (
                item.get("locatable")
                if isinstance(item.get("locatable"), bool)
                else None
            )
        geldig.append(entry)
    return geldig


def _valideer_claims(
    ruw: Any, bronnen: tuple[Bronidentiteit, ...], rejected: list[dict]
) -> list[dict[str, Any]]:
    geldig: list[dict[str, Any]] = []
    for item in ruw if isinstance(ruw, list) else ():
        if not isinstance(item, Mapping):
            continue
        source_id = item.get("source_id")
        if source_id is not None and bron_op_id(bronnen, source_id) is None:
            rejected.append(
                {
                    "part": ONDERDEEL_STEUN,
                    "reason": "onbekend bron-id",
                    "detail": str(source_id)[:120],
                }
            )
            source_id = None
        aspect = item.get("aspect")
        geldig.append(
            {
                "aspect": (
                    aspect
                    if aspect in ("kenmerk", "beperking", "uitzondering")
                    else "kenmerk"
                ),
                "text": _tekst(item.get("text")),
                "supported": (
                    item.get("supported")
                    if isinstance(item.get("supported"), bool)
                    else None
                ),
                "source_id": source_id if isinstance(source_id, str) else None,
            }
        )
    return geldig


def _valideer_deel(
    onderdeel: str, ruw: Any, bronnen: tuple[Bronidentiteit, ...], rejected: list[dict]
) -> GevalideerdDeel:
    """Eén onderdeel van de modeluitvoer, fail-closed naar 'nog te beoordelen'."""
    if not isinstance(ruw, Mapping):
        rejected.append(
            {
                "part": onderdeel,
                "reason": "onderdeel ontbreekt of is geen object",
                "detail": repr(ruw)[:120],
            }
        )
        return GevalideerdDeel(
            STATUS_OPEN,
            "Het model leverde voor dit onderdeel geen bruikbaar oordeel.",
            None,
            (),
            {},
        )

    status = ruw.get("status")
    reden = _tekst(ruw.get("reason"))
    onzekerheid = _tekst(ruw.get("uncertainty")) or None
    bewijs = _verifieer_bewijs(ruw.get("evidence"), bronnen, onderdeel, rejected)
    extra: dict[str, Any] = {}
    if onderdeel == ONDERDEEL_GEZAG:
        extra["sources"] = _valideer_bronlijst(
            ruw.get("sources"), bronnen, onderdeel, rejected, profiel=True
        )
    elif onderdeel == ONDERDEEL_STEUN:
        extra["claims"] = _valideer_claims(ruw.get("claims"), bronnen, rejected)
    else:
        extra["sources"] = _valideer_bronlijst(
            ruw.get("sources"), bronnen, onderdeel, rejected, profiel=False
        )

    if status not in _DEELSTATUSSEN:
        rejected.append(
            {
                "part": onderdeel,
                "reason": "ongeldige status",
                "detail": repr(status)[:120],
            }
        )
        return GevalideerdDeel(
            STATUS_OPEN,
            (f"{reden} " if reden else "")
            + f"Ongeldige status {status!r} van het model; het onderdeel blijft open.",
            onzekerheid,
            bewijs,
            extra,
        )
    if status in (STATUS_PASS, STATUS_FAIL) and not bewijs:
        rejected.append(
            {
                "part": onderdeel,
                "reason": "oordeel zonder geverifieerd bewijs",
                "detail": status,
            }
        )
        return GevalideerdDeel(
            STATUS_OPEN,
            (f"{reden} " if reden else "")
            + "Onvoldoende onderbouwd: geen aantoonbaar citaat in de aangeleverde bronnen; "
            + (
                "het oordeel 'voldoet' "
                if status == STATUS_PASS
                else "de gemelde tekortkoming "
            )
            + "telt daarom niet.",
            onzekerheid,
            (),
            extra,
        )
    if status == STATUS_PASS:
        tegenspraak = _positieve_onderbouwing_ontbreekt(onderdeel, bewijs, extra)
        if tegenspraak is not None:
            rejected.append(
                {
                    "part": onderdeel,
                    "reason": "oordeel zonder consistente onderbouwing",
                    "detail": tegenspraak[:120],
                }
            )
            return GevalideerdDeel(
                STATUS_OPEN,
                (f"{reden} " if reden else "")
                + f"Het oordeel 'voldoet' wordt niet gedragen door de eigen onderbouwing: "
                f"{tegenspraak}. Het onderdeel blijft open; de gestructureerde "
                "bevindingen blijven zichtbaar.",
                onzekerheid,
                bewijs,
                extra,
            )
    return GevalideerdDeel(
        status, reden or "Geen toelichting van het model.", onzekerheid, bewijs, extra
    )


def _tegenstrijdig_per_bron(entries: list[dict[str, Any]], veld: str) -> str | None:
    """Dezelfde bron tegelijk positief én negatief/onbekend beoordeeld?

    Een onafhankelijke negatieve entry over een ándere bron is geen
    tegenspraak (niet elke verzamelde bron hoeft gezaghebbend te zijn); twee
    oordelen over hetzelfde bron-id die elkaar uitsluiten wel — dat is een
    reviewpunt, geen pass.
    """
    oordelen: dict[str, set[Any]] = {}
    for entry in entries:
        oordelen.setdefault(entry["source_id"], set()).add(entry.get(veld))
    strijdig = sorted(
        bron
        for bron, waarden in oordelen.items()
        if True in waarden and len(waarden) > 1
    )
    if strijdig:
        return (
            f"tegenstrijdige oordelen over dezelfde bron ({veld}) voor: "
            + ", ".join(strijdig)
        )
    return None


def _gezag_onderbouwing_ontbreekt(
    bewijsbronnen: set[str], entries: list[dict[str, Any]]
) -> str | None:
    """Brongezag: geen tegenspraak, ≥1 toepasselijke bron waaruit het bewijs komt."""
    strijdig = _tegenstrijdig_per_bron(entries, "applicable")
    if strijdig is not None:
        return strijdig
    toepasselijk = [s for s in entries if s.get("applicable") is True]
    return _eerste_reden(
        (
            (
                not toepasselijk,
                "geen bron is als toepasselijk (applicable: true) aangemerkt",
            ),
            (
                not any(s["source_id"] in bewijsbronnen for s in toepasselijk),
                "het bewijs komt niet uit een als toepasselijk aangemerkte bron",
            ),
        )
    )


def _steun_onderbouwing_ontbreekt(
    bewijsbronnen: set[str], claims: list[dict[str, Any]]
) -> str | None:
    """Betekenissteun: claims aanwezig, alle gesteund én elk aan bewijs gebonden."""
    if not claims:
        return "geen enkel kenmerk, beperking of uitzondering is als claim onderbouwd"
    niet_gesteund = [c for c in claims if c.get("supported") is not True]
    if niet_gesteund:
        return (
            f"{len(niet_gesteund)} kenmerk(en) zijn niet (aantoonbaar) gesteund: "
            + "; ".join(_tekst(c.get("text")) or "?" for c in niet_gesteund)
        )
    ongebonden = [c for c in claims if c.get("source_id") not in bewijsbronnen]
    if ongebonden:
        return (
            f"{len(ongebonden)} gesteund(e) kenmerk(en) zijn niet aan een bron met "
            "geverifieerd bewijs gebonden: "
            + "; ".join(_tekst(c.get("text")) or "?" for c in ongebonden)
        )
    return None


def _verwijzing_onderbouwing_ontbreekt(
    bewijsbronnen: set[str], entries: list[dict[str, Any]]
) -> str | None:
    """Verwijskwaliteit: geen tegenspraak, ≥1 terugvindbare bron waaruit het bewijs komt."""
    strijdig = _tegenstrijdig_per_bron(entries, "locatable")
    if strijdig is not None:
        return strijdig
    terugvindbaar = [s for s in entries if s.get("locatable") is True]
    return _eerste_reden(
        (
            (
                not terugvindbaar,
                "geen bron is als terugvindbaar (locatable: true) aangemerkt",
            ),
            (
                not any(s["source_id"] in bewijsbronnen for s in terugvindbaar),
                "het bewijs komt niet uit een als terugvindbaar aangemerkte bron",
            ),
        )
    )


def _positieve_onderbouwing_ontbreekt(
    onderdeel: str, bewijs: tuple[dict[str, Any], ...], extra: Mapping[str, Any]
) -> str | None:
    """Waarom een 'pass' niet strookt met de gestructureerde onderbouwing, of None.

    Een citaat alleen licentieert geen positief oordeel: brongezag vraagt een
    bron die als toepasselijk is aangemerkt én waaruit het bewijs komt;
    betekenissteun vraagt dat élke claim gesteund is én aan een bron met
    geverifieerd bewijs is gebonden (een ongebonden of onbekende claim lift
    niet mee op een gebonden claim); verwijskwaliteit vraagt een terugvindbaar
    verklaarde bron waaruit het bewijs komt. Tegenstrijdige oordelen over
    dezelfde bron zijn een reviewpunt. Negatieve of onbekende bevindingen
    worden niet herschreven — ze maken het onderdeel open en blijven staan.
    """
    bewijsbronnen = {item["source_id"] for item in bewijs}
    if onderdeel == ONDERDEEL_GEZAG:
        return _gezag_onderbouwing_ontbreekt(
            bewijsbronnen, list(extra.get("sources", []))
        )
    if onderdeel == ONDERDEEL_STEUN:
        return _steun_onderbouwing_ontbreekt(
            bewijsbronnen, list(extra.get("claims", []))
        )
    return _verwijzing_onderbouwing_ontbreekt(
        bewijsbronnen, list(extra.get("sources", []))
    )


def valideer_onderdelen(
    parts: Any,
    bronnen: Any,
) -> tuple[dict[str, GevalideerdDeel], list[dict[str, Any]]]:
    """Valideer de drie AI-onderdelen tegen de (verzonden) bronpassages.

    Gedeeld door de beoordelingsservice (op de modeluitvoer, tegen de
    passages zoals verzonden) en door `valideer_beoordeling` (replay, tegen
    de canonieke passages). Geeft (onderdelen, afgewezen items).
    """
    canoniek = _canoniek(bronnen)
    rejected: list[dict[str, Any]] = []
    ruw = parts if isinstance(parts, Mapping) else {}
    gevalideerd = {
        onderdeel: _valideer_deel(onderdeel, ruw.get(onderdeel), canoniek, rejected)
        for onderdeel in AI_ONDERDELEN
    }
    return gevalideerd, rejected


def _statusafwijzing(assessment: Mapping[str, Any], status: Any) -> str | None:
    """Waarom een beoordeling op haar technische status al niet telt, of None."""
    if status == "unavailable":
        return (
            _tekst(assessment.get("reason"))
            or "bronbeoordelingsdienst niet beschikbaar"
        )
    if status == "error":
        fout = assessment.get("error")
        soort = _tekst(fout.get("type")) if isinstance(fout, Mapping) else ""
        melding = _tekst(fout.get("message")) if isinstance(fout, Mapping) else ""
        return f"technische fout ({soort or 'unknown'}): {melding}".strip()
    if status == "no_sources":
        return "geen bronnen aangeleverd; geen AI-beoordeling uitgevoerd"
    if status != "assessed":
        return f"onbekende beoordelingsstatus {status!r}"
    return None


def _bindingsafwijzing(
    assessment: Mapping[str, Any], fingerprint: str, model: str | None
) -> str | None:
    """Contractversie, vingerafdruk en herkomst — in die volgorde."""
    return _eerste_reden(
        (
            (
                assessment.get("contract_version") != CONTRACTVERSIE,
                (
                    f"beoordeling hoort bij contractversie "
                    f"{assessment.get('contract_version')!r}; "
                    f"actueel is {CONTRACTVERSIE!r}"
                ),
            ),
            (
                _tekst(assessment.get("fingerprint")) != fingerprint,
                (
                    "eerdere beoordeling geldt niet meer: tekst, context, term, "
                    "peildatum of bronnen zijn gewijzigd"
                ),
            ),
            (
                not model,
                "beoordeling zonder benoemd model (herkomst onbekend) genegeerd",
            ),
        )
    )


def valideer_beoordeling(
    assessment: Any,
    fingerprint: str,
    bronnen: Any,
    *,
    max_passage_chars: int | None = None,
) -> tuple[dict[str, GevalideerdDeel], dict[str, Any]]:
    """Valideer een (opgeslagen of zojuist verkregen) beoordeling tegen de invoer.

    Geeft (gevalideerde onderdelen, samenvatting). Een beoordeling telt alleen
    bij gelijke contractversie én vingerafdruk, status `assessed` en een
    benoemd model; per onderdeel wordt het bewijs opnieuw tegen de
    aangeleverde passages gelegd. Wat niet telt wordt in de samenvatting
    benoemd — nooit stil genegeerd.
    """
    canoniek = _canoniek(bronnen)
    samenvatting: dict[str, Any] = {
        "applied": False,
        "status": None,
        "reason": None,
        "model": None,
        "provider": None,
        "prompt_version": None,
        "rejected": 0,
    }
    if not isinstance(assessment, Mapping):
        samenvatting["reason"] = (
            "AI-beoordeling nog niet uitgevoerd (geen beoordeling aangeleverd)"
            if assessment is None
            else "beoordeling is geen object"
        )
        return {}, samenvatting

    status = assessment.get("status")
    samenvatting["status"] = status if isinstance(status, str) else None
    samenvatting["prompt_version"] = (
        assessment.get("prompt_version")
        if isinstance(assessment.get("prompt_version"), str)
        else None
    )
    attributie = assessment.get("attribution")
    if isinstance(attributie, Mapping):
        samenvatting["model"] = _tekst(attributie.get("model")) or None
        samenvatting["provider"] = _tekst(attributie.get("provider")) or None
    rejected_bestaand = assessment.get("rejected")
    samenvatting["rejected"] = (
        len(rejected_bestaand) if isinstance(rejected_bestaand, list) else 0
    )

    reden = _statusafwijzing(assessment, status) or _bindingsafwijzing(
        assessment, fingerprint, samenvatting["model"]
    )
    parts = assessment.get("parts")
    if reden is None and not isinstance(parts, Mapping):
        reden = "beoordeling zonder onderdelen"
    if reden is not None:
        samenvatting["reason"] = reden
        return {}, samenvatting

    # Citaten worden getoetst tegen wat het model wérkelijk zag: de passages
    # uit de beoordelingskwitantie (afgekapt) — niet tegen de volledige bron.
    verzonden, kwitantiefout = verzonden_passages(
        assessment.get("assessment_receipt"),
        canoniek,
        max_passage_chars=max_passage_chars,
    )
    if kwitantiefout is not None:
        samenvatting["reason"] = kwitantiefout
        return {}, samenvatting

    gevalideerd, rejected = valideer_onderdelen(parts, verzonden)
    samenvatting["applied"] = True
    samenvatting["rejected"] = samenvatting["rejected"] + len(rejected)
    return gevalideerd, samenvatting


def _kwitantiegrens(
    receipt: Mapping[str, Any], max_passage_chars: int | None
) -> tuple[int | None, str | None]:
    """De geldige afkapgrens van de kwitantie, of de reden waarom zij niet telt."""
    grens = receipt.get("max_passage_chars")
    if not isinstance(grens, int) or isinstance(grens, bool) or grens <= 0:
        return None, f"beoordelingskwitantie: ongeldige afkapgrens {grens!r}"
    if max_passage_chars is not None and grens != max_passage_chars:
        return None, (
            f"beoordelingskwitantie: afkapgrens {grens} wijkt af van de werkelijke "
            f"dienstgrens {max_passage_chars}"
        )
    return grens, None


def _kwitantierecords(
    records: list[Any], bekend: set[str]
) -> tuple[dict[str, Mapping[str, Any]], str | None]:
    """Records per bron-id: geldig id, geen dubbelen, geen onbekende bronnen."""
    per_id: dict[str, Mapping[str, Any]] = {}
    for item in records:
        if not isinstance(item, Mapping) or not isinstance(item.get("source_id"), str):
            return {}, "beoordelingskwitantie: bronrecord zonder geldig source_id"
        if item["source_id"] in per_id:
            return (
                {},
                f"beoordelingskwitantie: bron {item['source_id']} staat er dubbel in",
            )
        per_id[item["source_id"]] = item
    onbekend = sorted(set(per_id) - bekend)
    if onbekend:
        return {}, "beoordelingskwitantie noemt onbekende bron(nen): " + ", ".join(
            onbekend
        )
    return per_id, None


def _verzonden_bron(
    bron: Bronidentiteit, item: Mapping[str, Any] | None, grens: int
) -> tuple[Bronidentiteit | None, str | None]:
    """Eén bron met haar verzonden passage uit de kwitantie, of de afwijzingsreden.

    Controlevolgorde: aanwezig → oorspronkelijke hash → inhoud is tekst →
    inhoud == passage[:grens] → hash van de inhoud → afkapmarkering → bronversie.
    De hash wordt pas berekend nadat de inhoud als exacte prefix is geaccepteerd:
    niet-UTF-8-codeerbare tekst (los surrogaat) valt zo op de prefixcontrole met
    haar eigen reden, in plaats van op een exception.
    """
    if item is None:
        return None, f"beoordelingskwitantie noemt bron {bron.source_id} niet"
    inhoud = _citaattekst(item.get("content"))
    vooraf = _eerste_reden(
        (
            (
                _tekst(item.get("original_content_hash")) != bron.content_hash,
                (
                    "beoordelingskwitantie hoort niet bij deze bronnen: oorspronkelijke "
                    f"hash van {bron.source_id} wijkt af"
                ),
            ),
            (
                not isinstance(item.get("content"), str),
                f"beoordelingskwitantie zonder verzonden inhoud voor {bron.source_id}",
            ),
            (
                inhoud != bron.passage[:grens],
                (
                    f"beoordelingskwitantie: verzonden inhoud van {bron.source_id} "
                    f"is niet de canonieke passage tot de afkapgrens {grens}"
                ),
            ),
        )
    )
    if vooraf is not None:
        return None, vooraf
    afgekapt = item.get("truncated")
    reden = _eerste_reden(
        (
            (
                hashlib.sha256(inhoud.encode("utf-8")).hexdigest()
                != _tekst(item.get("content_hash")),
                (
                    "beoordelingskwitantie: hash van verzonden inhoud van "
                    f"{bron.source_id} klopt niet"
                ),
            ),
            (
                not isinstance(afgekapt, bool)
                or afgekapt != (len(bron.passage) > grens),
                (
                    f"beoordelingskwitantie: afkapmarkering van {bron.source_id} "
                    "klopt niet met passage en grens"
                ),
            ),
            (
                (_tekst(item.get("source_version")) or None) != bron.version,
                (
                    f"beoordelingskwitantie: bronversie van {bron.source_id} "
                    f"is niet de bewaarde versie {bron.version!r}"
                ),
            ),
        )
    )
    if reden is not None:
        return None, reden
    return replace(bron, passage=inhoud), None


def verzonden_passages(
    receipt: Any,
    bronnen: tuple[Bronidentiteit, ...],
    *,
    max_passage_chars: int | None = None,
) -> tuple[tuple[Bronidentiteit, ...], str | None]:
    """De bronnen met de passages zoals de beoordeling ze ontving, of een fout.

    Zonder beoordelingskwitantie (`None`) gelden de volledige canonieke
    passages. Mét kwitantie wordt zij strikt aan de canonieke bronnen gebonden:
    een geldige afkapgrens (positief geheel getal; gelijk aan de werkelijke
    dienstgrens wanneer de aanroeper die meegeeft), exact dezelfde bronset,
    per bron `original_content_hash` == canonieke inhoudshash, `content` ==
    `passage[:grens]`, `content_hash` == hash(content), `truncated` == of de
    passage langer is dan de grens, en `source_version` == bronversie. Elke
    afwijking maakt de beoordeling niet-toepasbaar (de beoordeling zelf blijft
    onaangeroerd als historisch document); een citaat voorbij de grens kan zo
    nooit als verzonden gelden.
    """
    if receipt is None:
        return bronnen, None
    if not isinstance(receipt, Mapping) or not isinstance(receipt.get("sources"), list):
        return (), "beoordelingskwitantie is misvormd"
    grens, grensfout = _kwitantiegrens(receipt, max_passage_chars)
    if grens is None:
        return (), grensfout
    per_id, recordfout = _kwitantierecords(
        receipt["sources"], {b.source_id for b in bronnen}
    )
    if recordfout is not None:
        return (), recordfout
    resultaat: list[Bronidentiteit] = []
    for bron in bronnen:
        verzonden, bronfout = _verzonden_bron(bron, per_id.get(bron.source_id), grens)
        if verzonden is None:
            return (), bronfout
        resultaat.append(verzonden)
    return tuple(resultaat), None


# --- deskundige uitzonderingen -----------------------------------------------------


def _versieconflict(beoordeeld: Any, definitie_versie: Any) -> str | None:
    """Dezelfde versiebinding als CON-01 (E2/V2b), als tekst of None."""
    if definitie_versie is None:
        return None
    if not is_versienummer(definitie_versie):
        return (
            f"recordversie {definitie_versie!r} is geen geldig versienummer; de "
            "versiebinding van de beoordeling is niet te controleren"
        )
    if not is_versienummer(beoordeeld):
        return (
            "beoordeling draagt geen geldig versienummer; het record is versie "
            f"{definitie_versie} en vraagt een nieuwe beoordeling"
        )
    if beoordeeld != definitie_versie:
        return (
            f"beoordeling hoort bij versie {beoordeeld}; het record is inmiddels "
            f"versie {definitie_versie}"
        )
    return None


def _valideer_verwijzing(
    review: Mapping[str, Any], bronnen: tuple[Bronidentiteit, ...]
) -> str | None:
    """Eisen van besluit 1 (15-09-2026); geeft de afwijzingsreden of None."""
    bron = bron_op_id(bronnen, review.get("source_id"))
    if bron is None:
        return f"bron-id {review.get('source_id')!r} is onbekend in de bronset"
    locator = _tekst(review.get("locator"))
    return _eerste_reden(
        (
            (
                _tekst(review.get("content_hash")) != bron.content_hash,
                "content_hash komt niet overeen met de bewaarde passage van deze bron",
            ),
            (
                bron.version is not None
                and _tekst(review.get("source_version")) != bron.version,
                f"bronversie {review.get('source_version')!r} is niet de bewaarde versie {bron.version!r}",
            ),
            (not locator, "exacte vindplaats ontbreekt"),
            (
                bron.locator is not None and locator != bron.locator,
                f"vindplaats {locator!r} wijkt af van de bronvindplaats {bron.locator!r}",
            ),
            (
                bool(bron.url),
                "bron heeft een bruikbare hyperlink; de verwijzingsuitzondering is niet van toepassing",
            ),
        )
    )


def _valideer_correctiebewijs(
    item: Any, bronnen: tuple[Bronidentiteit, ...]
) -> tuple[str | None, dict[str, Any] | None]:
    """Eén bewijsclaim van een deskundige, in dezelfde vorm als het AI-bewijs.

    De claim moet aan de bewaarde bron gebonden zijn: bestaand id, gelijke
    inhoudshash, gelijke bronversie, een citaat dat werkelijk in de passage
    staat en — als de bron een vindplaats heeft — precies die vindplaats.
    Geeft (afwijzingsreden, genormaliseerd item).
    """
    if not isinstance(item, Mapping):
        return "bewijs: item is geen object", None
    bron = bron_op_id(bronnen, item.get("source_id"))
    if bron is None:
        return (
            f"bewijs: bron-id {item.get('source_id')!r} is onbekend in de bronset",
            None,
        )
    versie = _tekst(item.get("source_version")) or None
    citaat = _citaattekst(item.get("quote"))
    locator = _tekst(item.get("locator")) or None
    reden = _eerste_reden(
        (
            (
                _tekst(item.get("content_hash")) != bron.content_hash,
                f"bewijs: content_hash komt niet overeen met de bewaarde passage van {bron.source_id}",
            ),
            (
                versie != bron.version,
                f"bewijs: bronversie {versie!r} is niet de bewaarde versie {bron.version!r}",
            ),
            (not citaat.strip(), f"bewijs: leeg citaat voor {bron.source_id}"),
            (
                not vind_citaat(bron.passage, citaat),
                f"bewijs: citaat staat niet in de bewaarde passage van {bron.source_id}",
            ),
            (
                bron.locator is not None and locator != bron.locator,
                (
                    f"bewijs: vindplaats {locator!r} wijkt af van de bronvindplaats "
                    f"{bron.locator!r} van {bron.source_id}"
                ),
            ),
        )
    )
    if reden is not None:
        return reden, None
    return None, {
        "source_id": bron.source_id,
        "content_hash": bron.content_hash,
        "source_version": bron.version,
        "quote": citaat,
        "locator": bron.locator if bron.locator is not None else locator,
    }


def _correctievorm(onderdeel: Any, status: Any, ruw: Any) -> str | None:
    """Vormeisen van een correctie: bekend AI-onderdeel, geldige status, bewijslijst."""
    if onderdeel not in AI_ONDERDELEN:
        return (
            f"onderdeel {onderdeel!r} is geen corrigeerbaar AI-onderdeel "
            f"({', '.join(AI_ONDERDELEN)})"
        )
    if status not in _DEELSTATUSSEN:
        return f"status {status!r} is ongeldig (pass, fail of review_required)"
    if not isinstance(ruw, list):
        return "bewijs moet een lijst claims zijn (evidence)"
    return None


def _correctiebewijseis(
    onderdeel: Any, status: Any, bewijs: list[dict[str, Any]]
) -> str | None:
    """Bewijseis bij een positief of negatief oordeel; open mag zonder bewijs."""
    if status not in (STATUS_PASS, STATUS_FAIL):
        return None
    if not bewijs:
        return (
            f"een oordeel {status!r} vereist minstens één gebonden bewijsclaim "
            "(bewijs ontbreekt)"
        )
    if onderdeel == ONDERDEEL_VERWIJZING and any(
        not _tekst(item.get("locator")) for item in bewijs
    ):
        return (
            "verwijskwaliteit vereist per bewijsclaim een exacte vindplaats "
            "(vindplaats ontbreekt)"
        )
    return None


def _valideer_correctie(
    review: Mapping[str, Any], bronnen: tuple[Bronidentiteit, ...]
) -> tuple[str | None, list[dict[str, Any]]]:
    """Eisen aan een deskundige correctie van één AI-onderdeel.

    Een positief of negatief oordeel vereist echt, gebonden en — voor de
    verwijskwaliteit — terugvindbaar bewijs; een open oordeel mag zonder
    bewijs het ontbreken ervan motiveren. Nooit een globale uitspraak: alleen
    het genoemde onderdeel wordt vervangen.
    """
    onderdeel = review.get("part_id")
    status = review.get("status")
    ruw = review.get("evidence")
    vormfout = _correctievorm(onderdeel, status, ruw)
    if vormfout is not None:
        return vormfout, []
    bewijs: list[dict[str, Any]] = []
    for item in ruw if isinstance(ruw, list) else []:
        reden, genormaliseerd = _valideer_correctiebewijs(item, bronnen)
        if reden is not None:
            return reden, []
        bewijs.append(genormaliseerd or {})
    bewijsfout = _correctiebewijseis(onderdeel, status, bewijs)
    if bewijsfout is not None:
        return bewijsfout, []
    return None, bewijs


def _valideer_geen_bron(review: Mapping[str, Any]) -> str | None:
    search = review.get("search")
    if not isinstance(search, Mapping):
        return "gedocumenteerd zoeken ontbreekt (search: queries/consulted/conclusion)"
    queries = search.get("queries")
    if not isinstance(queries, list) or not any(_tekst(q) for q in queries):
        return "gedocumenteerd zoeken zonder zoekvragen (search.queries)"
    if not _tekst(search.get("conclusion")):
        return "gedocumenteerd zoeken zonder conclusie (search.conclusion)"
    return None


def _algemene_reviewafwijzing(
    review: Mapping[str, Any],
    *,
    soort: str,
    actor: str,
    aangeleverd: str,
    fingerprint: str,
    definitie_versie: int | str | None,
) -> str | None:
    """De algemene eisen aan elke deskundige beoordeling, in vaste volgorde.

    type → expliciete acceptatie → beoordelaar → motivering → vingerafdruk →
    versiebinding. De eerste tekortkoming is de reden.
    """
    conflict = _versieconflict(review.get("version_number"), definitie_versie)
    return _eerste_reden(
        (
            (
                soort not in _BEKENDE_REVIEW_TYPES,
                (
                    f"beoordelingstype {soort or None!r} wordt niet ondersteund "
                    "(handmatige correctie van een AI-onderdeel is in con02/1 niet gebouwd)"
                ),
            ),
            (
                review.get("accepted") is not True,
                "uitzondering is niet expliciet geaccepteerd (accepted moet true zijn)",
            ),
            (not actor, "beoordeling zonder benoemde beoordelaar genegeerd"),
            (
                not _tekst(review.get("rationale")),
                "uitzondering zonder motivering (rationale) genegeerd",
            ),
            (
                aangeleverd != fingerprint,
                (
                    "eerdere beoordeling geldt niet meer: tekst, context, term, "
                    "peildatum of bronnen zijn gewijzigd"
                ),
            ),
            (conflict is not None, conflict or ""),
        )
    )


def _typespecifieke_review(
    review: Mapping[str, Any],
    *,
    soort: str,
    actor: str,
    canoniek: tuple[Bronidentiteit, ...],
) -> tuple[str | None, dict[str, Any], dict[str, Any]]:
    """(afwijzingsreden, toepasbare review, samenvattingsvelden) per reviewtype."""
    toepasbaar = deepcopy(dict(review))
    if soort == REVIEW_TYPE_CORRECTIE:
        reden, bewijs = _valideer_correctie(review, canoniek)
        if reden is not None:
            return reden, {}, {}
        toepasbaar["evidence"] = bewijs
        return (
            None,
            toepasbaar,
            {
                "applied_correction": {
                    "part_id": review["part_id"],
                    "status": review["status"],
                    "actor": actor,
                    "evidence": deepcopy(bewijs),
                }
            },
        )
    reden = (
        _valideer_verwijzing(review, canoniek)
        if soort == REVIEW_TYPE_VERWIJZING
        else _valideer_geen_bron(review)
    )
    if reden is not None:
        return reden, {}, {}
    return (
        None,
        toepasbaar,
        {
            "accepted_exception": (
                "reference" if soort == REVIEW_TYPE_VERWIJZING else "no_source"
            )
        },
    )


def valideer_bronreview(
    review: Any,
    fingerprint: str,
    bronnen: Any,
    definitie_versie: int | str | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Filter een deskundige uitzondering op bruikbaarheid (bevroren platte vorm).

    Geeft (toepasbare review of None, samenvatting). Volgorde van de
    controles: type → expliciete acceptatie → beoordelaar → motivering →
    vingerafdruk → versiebinding → type-specifieke eisen. De eerste
    tekortkoming is de reden; een review die niet telt verdwijnt nooit stil.
    """
    samenvatting: dict[str, Any] = {
        "applied": False,
        "actor": None,
        "fingerprint": None,
        "type": None,
        "accepted_exception": None,
        "applied_correction": None,
        "reason": None,
    }
    if review is None:
        samenvatting["reason"] = "geen deskundige beoordeling aangeleverd"
        return None, samenvatting
    if not isinstance(review, Mapping):
        samenvatting["reason"] = "deskundige beoordeling is geen object"
        return None, samenvatting

    soort = _tekst(review.get("type"))
    actor = _tekst(review.get("actor"))
    aangeleverd = _tekst(review.get("fingerprint"))
    samenvatting.update(
        {
            "actor": actor or None,
            "fingerprint": aangeleverd or None,
            "type": soort or None,
        }
    )

    reden = _algemene_reviewafwijzing(
        review,
        soort=soort,
        actor=actor,
        aangeleverd=aangeleverd,
        fingerprint=fingerprint,
        definitie_versie=definitie_versie,
    )
    toepasbaar: dict[str, Any] = {}
    extra: dict[str, Any] = {}
    if reden is None:
        reden, toepasbaar, extra = _typespecifieke_review(
            review, soort=soort, actor=actor, canoniek=_canoniek(bronnen)
        )
    if reden is not None:
        samenvatting["reason"] = reden
        return None, samenvatting
    samenvatting.update(extra)
    samenvatting["applied"] = True
    return toepasbaar, samenvatting


# --- samenstelling ------------------------------------------------------------------


@dataclass(frozen=True)
class BronUitkomst:
    """De samengestelde CON-02-uitkomst: status, vingerafdruk, onderdelen, review."""

    status: str
    fingerprint: str
    parts: tuple[Deeluitkomst, ...]
    review: dict[str, Any] | None

    def als_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "score": None,
            "contract_version": CONTRACTVERSIE,
            "fingerprint": self.fingerprint,
            "parts": [p.als_dict() for p in self.parts],
            "review": deepcopy(self.review),
        }


def _samengesteld(parts: tuple[Deeluitkomst, ...]) -> str:
    statussen = {p.status for p in parts}
    if STATUS_FAIL in statussen:
        return STATUS_FAIL
    if STATUS_ERROR in statussen:
        return STATUS_ERROR
    if statussen == {STATUS_PASS}:
        return STATUS_PASS
    return STATUS_OPEN


def _open_deel(onderdeel: str, reden: str, actie: str) -> Deeluitkomst:
    return Deeluitkomst(id=onderdeel, status=STATUS_OPEN, reason=reden, action=actie)


def _bewijstekst(bewijs: tuple[dict[str, Any], ...]) -> str:
    stukken = []
    for item in bewijs:
        vindplaats = f", {item['locator']}" if item.get("locator") else ""
        stukken.append(f"bron {item['source_id']}{vindplaats}: “{item['quote']}”")
    return "; ".join(stukken)


def _ai_deel(
    onderdeel: str, deel: GevalideerdDeel, samenvatting: Mapping[str, Any]
) -> Deeluitkomst:
    naam = _ONDERDEELNAAM[onderdeel]
    model = samenvatting.get("model") or "onbekend model"
    kop = f"AI-beoordeling van {naam} ({model}): {deel.reason}"
    if deel.uncertainty:
        kop += f" Onzekerheid: {deel.uncertainty}"
    bewijs = _bewijstekst(deel.evidence)
    if bewijs:
        kop += f" Bewijs: {bewijs}."
    if deel.status == STATUS_PASS:
        actie = _ACTIE_PASS
    elif deel.status == STATUS_FAIL:
        actie = _ACTIE_FAIL
    else:
        actie = _ACTIE_OPEN
    return Deeluitkomst(
        id=onderdeel,
        status=deel.status,
        evidence=deel.evidence[0]["quote"] if deel.evidence else None,
        field=BASIS_ASSESSMENT,
        reason=kop,
        action=actie,
    )


def _foutdeel(onderdeel: str, reden: str) -> Deeluitkomst:
    return Deeluitkomst(
        id=onderdeel,
        status=STATUS_ERROR,
        field=BASIS_ASSESSMENT,
        reason=f"De bronbeoordeling van {_ONDERDEELNAAM[onderdeel]} kon niet worden uitgevoerd: {reden}.",
        action=_ACTIE_DEELFOUT,
    )


def _ai_onderdelen(
    bronnen: tuple[Bronidentiteit, ...],
    gevalideerd: Mapping[str, GevalideerdDeel],
    samenvatting: Mapping[str, Any],
) -> list[Deeluitkomst]:
    # Een technische fout (verzamelfout, timeout, misvormd antwoord) gaat vóór
    # "geen bronnen": een kapotte aanlevering mag niet als gewoon open ogen.
    if samenvatting.get("status") == "error":
        reden = samenvatting.get("reason") or "technische fout"
        return [_foutdeel(o, reden) for o in AI_ONDERDELEN]
    if not bronnen:
        reden = (
            "Er zijn geen bronnen aangeleverd of gevonden; de {naam} kan niet worden "
            "beoordeeld. Een bronwoord in de definitiezin is geen bewijs."
        )
        return [
            _open_deel(o, reden.format(naam=_ONDERDEELNAAM[o]), _ACTIE_GEEN_BRONNEN)
            for o in AI_ONDERDELEN
        ]
    if not samenvatting.get("applied"):
        reden = samenvatting.get("reason") or "AI-beoordeling nog niet uitgevoerd"
        if samenvatting.get("status") in (None, "no_sources"):
            reden = "AI-beoordeling nog niet uitgevoerd"
        return [
            _open_deel(
                o,
                f"De {_ONDERDEELNAAM[o]} is nog niet beoordeeld: {reden}.",
                _ACTIE_NIET_BEOORDEELD,
            )
            for o in AI_ONDERDELEN
        ]
    return [_ai_deel(o, gevalideerd[o], samenvatting) for o in AI_ONDERDELEN]


def _pas_correctie_toe(
    parts: list[Deeluitkomst],
    review: Mapping[str, Any],
) -> tuple[list[Deeluitkomst], dict[str, Any]]:
    """Vervang precies één AI-onderdeel door het deskundige oordeel.

    Het oorspronkelijke oordeel blijft zichtbaar: in de reden van het
    onderdeel én als `original` in de reviewsamenvatting (audit). Andere
    onderdelen en de samenstelling blijven ongewijzigd — er is geen globale
    uitspraak.
    """
    actor = _tekst(review.get("actor"))
    motivering = _tekst(review.get("rationale"))
    onderdeel = review["part_id"]
    status = review["status"]
    bewijs = tuple(
        dict(item) for item in review.get("evidence") or () if isinstance(item, Mapping)
    )
    origineel_deel = next(p for p in parts if p.id == onderdeel)
    origineel = {
        "status": origineel_deel.status,
        "field": origineel_deel.field,
        "reason": origineel_deel.reason,
        "evidence": origineel_deel.evidence,
    }
    if status == STATUS_PASS:
        actie = _ACTIE_PASS
    elif status == STATUS_FAIL:
        actie = _ACTIE_FAIL
    else:
        actie = _ACTIE_OPEN
    bewijstekst = _bewijstekst(bewijs)
    reden = (
        f"Deskundige correctie van {_ONDERDEELNAAM[onderdeel]} door {actor}: "
        f"{motivering}"
        + (f" Bewijs: {bewijstekst}." if bewijstekst else "")
        + f" Oorspronkelijk oordeel ({origineel['status']}): {origineel['reason']}"
    )
    vervangen = [
        (
            Deeluitkomst(
                id=onderdeel,
                status=status,
                evidence=bewijs[0]["quote"] if bewijs else None,
                field=BASIS_REVIEW,
                reason=reden,
                action=actie,
            )
            if p.id == onderdeel
            else p
        )
        for p in parts
    ]
    return vervangen, origineel


def _pas_review_toe(
    parts: list[Deeluitkomst],
    review: Mapping[str, Any],
    bronnen: tuple[Bronidentiteit, ...],
) -> list[Deeluitkomst]:
    actor = _tekst(review.get("actor"))
    motivering = _tekst(review.get("rationale"))
    if review.get("type") == REVIEW_TYPE_GEEN_BRON:
        search = review.get("search") or {}
        conclusie = (
            _tekst(search.get("conclusion")) if isinstance(search, Mapping) else ""
        )
        parts.append(
            Deeluitkomst(
                id=ONDERDEEL_UITZONDERING_GEEN_BRON,
                status=STATUS_OPEN,
                field=BASIS_REVIEW,
                reason=(
                    f"Geaccepteerde deskundige uitzondering (geen passende bron) door {actor}: "
                    f"{motivering} Gedocumenteerd zoeken: {conclusie} Dit is een uitzondering, "
                    "geen 'voldoet'."
                ),
                action=_ACTIE_UITZONDERING,
            )
        )
        return parts

    bron = bron_op_id(bronnen, review.get("source_id"))
    locator = _tekst(review.get("locator"))
    hash_kort = (bron.content_hash[:12] if bron else "") + "…"
    vervangen: list[Deeluitkomst] = []
    for part in parts:
        if part.id != ONDERDEEL_VERWIJZING:
            vervangen.append(part)
            continue
        ai_oordeel = (
            f" AI-oordeel over de verwijzing blijft zichtbaar: {part.reason}"
            if part.field == BASIS_ASSESSMENT
            else ""
        )
        vervangen.append(
            Deeluitkomst(
                id=ONDERDEEL_VERWIJZING,
                status=STATUS_OPEN,
                evidence=locator,
                field=BASIS_REVIEW,
                reason=(
                    f"Geaccepteerde deskundige verwijzingsuitzondering door {actor}: {motivering} "
                    f"Bron {review.get('source_id')} zonder bruikbare hyperlink; exacte vindplaats "
                    f"{locator}; bewaarde passage {hash_kort}. Dit is een uitzondering, geen "
                    f"'voldoet'.{ai_oordeel}"
                ),
                action=_ACTIE_UITZONDERING,
            )
        )
    return vervangen


def beoordeel_bronbasis(
    begrip: str,
    tekst: str,
    contexten: Mapping[str, Any] | None,
    bronnen_ruw: Any,
    *,
    assessment: Any = None,
    review: Any = None,
    definitie_versie: int | str | None = None,
    peildatum: str | None = None,
    max_passage_chars: int | None = None,
) -> BronUitkomst:
    """De CON-02-beoordeling van één kandidaattekst met haar bronnen (replay).

    Zuiver en synchroon: consumeert een eerder verkregen, gestructureerde
    beoordeling (`assessment`, §5 van het contract) en een deskundige
    uitzondering (`review`, §6) en bindt beide aan de vingerafdruk van exact
    deze invoer. Voert zelf geen AI-aanroep uit.
    """
    bronnen = canoniseer_bronnen(bronnen_ruw)
    fingerprint = bereken_bronvingerafdruk(
        begrip, tekst, contexten, bronnen, peildatum=peildatum
    )
    try:
        gevalideerd, beoordeling = valideer_beoordeling(
            assessment, fingerprint, bronnen, max_passage_chars=max_passage_chars
        )
    except Exception as exc:  # pragma: no cover - defensief: replay mag nooit crashen
        logger.warning(
            "CON-02: validatie van de beoordeling mislukte: %s: %s",
            type(exc).__name__,
            exc,
            exc_info=True,
        )
        gevalideerd, beoordeling = {}, {
            "applied": False,
            "status": None,
            "reason": "beoordeling onleesbaar",
            "model": None,
            "provider": None,
            "prompt_version": None,
            "rejected": 0,
        }
    parts = _ai_onderdelen(bronnen, gevalideerd, beoordeling)

    toepasbaar, reviewsamenvatting = valideer_bronreview(
        review, fingerprint, bronnen, definitie_versie
    )
    if toepasbaar is not None and toepasbaar.get("type") == REVIEW_TYPE_CORRECTIE:
        parts, origineel = _pas_correctie_toe(parts, toepasbaar)
        reviewsamenvatting["applied_correction"]["original"] = origineel
    elif toepasbaar is not None:
        parts = _pas_review_toe(parts, toepasbaar, bronnen)

    delen = tuple(parts)
    return BronUitkomst(
        status=_samengesteld(delen),
        fingerprint=fingerprint,
        parts=delen,
        review={**reviewsamenvatting, "assessment": dict(beoordeling)},
    )
