"""CON-01 — het contextcontract (DEF-622, besluiten B-01/B-02/B-04/B-06/B-08).

Pure domeinlogica, zonder Streamlit, database of regelrecord. De evaluator
(`services.validation.evaluators.context_metadata`) roept `beoordeel_context`
aan en vertaalt de uitkomst naar het runtimecontract.

Wat de regel toetst:

- **B-01 context aanwezig** — minstens één betekenisvolle contextwaarde in de
  drie lijsten. Zonder context: *Voldoet niet*. Dat is een inhoudelijke
  overtreding van het record, geen ontbrekende meting.
- **B-02/B-04 naamfunctie** — een geselecteerde contextwaarde die letterlijk
  in de definitiezin staat is een *beoordelingssignaal*, geen afkeurgrond.
  Pas na menselijke beoordeling van de functie van die naam volgt de
  uitkomst: registratiecontext genoemd → *Voldoet niet*; inhoudelijk
  noodzakelijk voor afbakening/identificatie → *Voldoet*; onduidelijk →
  *Nog te beoordelen*. Er is bewust géén automatische afkeurheuristiek op
  meta-frasen ("in de context van", "juridisch"): die is niet goedgekeurd.
- **B-06 geen cijfer** — de regel levert een uitkomst met motivering, nooit
  een score. Het ontbreken van een cijfer is geen 0 en geen 1.
- **B-08 samenstelling** — alle vereiste onderdelen voldoen → *Voldoet*;
  minstens één inhoudelijke overtreding → *Voldoet niet*; anders → *Nog te
  beoordelen*. Alle deeluitkomsten blijven zichtbaar, ook naast elkaar.

De menselijke beoordeling (`context_review`) is gebonden aan een
vingerafdruk over term, exacte tekst, canonieke context en contractversie
(en de definitieversie wanneer die beschikbaar is). Wijzigt daar iets, dan
geldt de eerdere beoordeling niet meer en staat het naamsignaal opnieuw open
(B-07: aanpassingen moeten opnieuw beoordeeld zijn).
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from domain.context.normalisatie import canoniseer_contextlijst, contextsleutel

logger = logging.getLogger(__name__)

__all__ = [
    "CONTEXT_VELDEN",
    "CONTRACTVERSIE",
    "FUNCTIE_NOODZAKELIJK",
    "FUNCTIE_ONDUIDELIJK",
    "FUNCTIE_REGISTRATIE",
    "ONDERDEEL_CONTEXT",
    "STATUS_ERROR",
    "STATUS_FAIL",
    "STATUS_OPEN",
    "STATUS_PASS",
    "ContextUitkomst",
    "Deeluitkomst",
    "beoordeel_context",
    "bereken_vingerafdruk",
    "vind_naamtreffers",
]

#: Versie van dit contract. Onderdeel van de vingerafdruk: verandert de norm,
#: dan vervalt elke eerdere beoordeling vanzelf.
CONTRACTVERSIE = "con01/1"

CONTEXT_VELDEN: tuple[str, str, str] = (
    "organisatorische_context",
    "juridische_context",
    "wettelijke_basis",
)

ONDERDEEL_CONTEXT = "context_aanwezig"

STATUS_PASS = "pass"
STATUS_FAIL = "fail"
STATUS_OPEN = "review_required"
STATUS_ERROR = "error"

_UITLEG_DEELFOUT = (
    "Dit onderdeel kon niet worden gecontroleerd. De beoordeling is nog onvolledig."
)
_ACTIE_DEELFOUT = (
    "Controleer opnieuw. Blijft dit terugkomen, meld het dan als technisch probleem."
)

# De drie beoordelingsuitkomsten van een naamtreffer (B-04).
FUNCTIE_REGISTRATIE = "registration"
FUNCTIE_NOODZAKELIJK = "necessary"
FUNCTIE_ONDUIDELIJK = "unclear"
_BEKENDE_FUNCTIES = frozenset(
    {FUNCTIE_REGISTRATIE, FUNCTIE_NOODZAKELIJK, FUNCTIE_ONDUIDELIJK}
)

# Gebruikersuitleg (B-08): aanleiding, reden en vervolgstap in begrijpelijk
# Nederlands. Bewust hier en niet in de UI, zodat elke consument (UI, export,
# review) dezelfde tekst toont.
_UITLEG_GEEN_CONTEXT = (
    "Bij dit record is geen organisatorische context, juridische context of "
    "wettelijke basis vastgelegd."
)
_ACTIE_GEEN_CONTEXT = (
    "Leg minstens één contextwaarde vast bij het record; de context hoort "
    "naast de definitie, niet erin."
)
_UITLEG_CONTEXT_AANWEZIG = "Er is minstens één contextwaarde vastgelegd."

_ACTIE_OPEN = (
    "Laat de expert de functie van de naam beoordelen en de reden vastleggen: "
    "registratiecontext (verwijderen uit de definitiezin) of inhoudelijk "
    "noodzakelijk voor de afbakening (mag blijven staan)."
)
_ACTIE_REGISTRATIE = (
    "Verwijder de zinsnede uit de definitie en behoud de context bij het record."
)


@dataclass(frozen=True)
class Naamtreffer:
    """Eén letterlijke treffer van een geselecteerde contextwaarde in de tekst."""

    veld: str
    contextwaarde: str
    gevonden: str
    positie: int

    @property
    def id(self) -> str:
        # De positie hoort bij de identiteit: dezelfde naam kan op twee
        # plekken een verschillende functie hebben.
        return f"naam:{self.veld}:{self.contextwaarde.casefold()}@{self.positie}"


@dataclass(frozen=True)
class Deeluitkomst:
    """Eén zichtbare deelcontrole met aanleiding, reden en vervolgstap."""

    id: str
    status: str
    reason: str
    action: str
    evidence: str | None = None
    context_value: str | None = None
    field: str | None = None
    position: int | None = None

    def als_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status,
            "evidence": self.evidence,
            "context_value": self.context_value,
            "field": self.field,
            "position": self.position,
            "reason": self.reason,
            "action": self.action,
        }


@dataclass(frozen=True)
class ContextUitkomst:
    """De samengestelde CON-01-uitkomst: status, vingerafdruk en delen."""

    status: str
    fingerprint: str
    parts: tuple[Deeluitkomst, ...]
    review: dict[str, Any] | None = None

    @property
    def naamsignalen(self) -> tuple[str, ...]:
        return tuple(p.evidence for p in self.parts if p.evidence)

    def als_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "score": None,
            "contract_version": CONTRACTVERSIE,
            "fingerprint": self.fingerprint,
            "parts": [p.als_dict() for p in self.parts],
            "review": self.review,
        }


def bereken_vingerafdruk(
    begrip: str,
    tekst: str,
    contexten: Mapping[str, Any],
    definitie_versie: int | str | None = None,
) -> str:
    """Bind een beoordeling aan term, exacte tekst, canonieke context en versie.

    De term hoort erbij: dezelfde zin met dezelfde context kan onder een ander
    begrip een andere beoordeling vragen. De context gaat als vergelijkings-
    sleutel mee, zodat schrijfwijze en volgorde van dezelfde waarden geen
    nieuwe beoordeling afdwingen. De tekst gaat exact mee: één teken verschil
    is een nieuwe beoordeling.
    """
    bron = {
        "versie": CONTRACTVERSIE,
        "term": str(begrip or ""),
        "tekst": str(tekst or ""),
        "context": {
            veld: list(contextsleutel(contexten.get(veld))) for veld in CONTEXT_VELDEN
        },
        "definitie_versie": (
            None if definitie_versie is None else str(definitie_versie)
        ),
    }
    return hashlib.sha256(
        json.dumps(bron, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class _GevouwenTekst:
    """De tekst in casefold-vorm plus de terugvertaling naar originele posities.

    Casefold kan de lengte veranderen (`ß` → `ss`), dus een treffer in de
    gevouwen tekst moet naar de oorspronkelijke tekst worden teruggerekend om
    de werkelijk gevonden schrijfwijze en positie te kunnen rapporteren.
    """

    gevouwen: str
    #: Per index in `gevouwen`: de index in de oorspronkelijke tekst.
    origineel_van: tuple[int, ...]

    @classmethod
    def van(cls, tekst: str) -> _GevouwenTekst:
        delen: list[str] = []
        terug: list[int] = []
        for index, teken in enumerate(tekst):
            gevouwen = teken.casefold()
            delen.append(gevouwen)
            terug.extend([index] * len(gevouwen))
        return cls("".join(delen), tuple(terug))

    def origineel_bereik(self, start: int, einde: int) -> tuple[int, int]:
        """Vertaal een [start, einde) in de gevouwen tekst naar het origineel."""
        if start >= len(self.origineel_van):
            return len(self.origineel_van), len(self.origineel_van)
        eerste = self.origineel_van[start]
        laatste = self.origineel_van[einde - 1] if einde > start else eerste
        return eerste, laatste + 1


def _patroon_voor(waarde: str) -> re.Pattern[str]:
    """Woordgrenspatroon voor één contextwaarde, op de gevouwen tekst.

    De waarde wordt met dezelfde casefold-normalisatie gezocht als waarmee de
    context zelf wordt vergeleken (`contextsleutel`): schrijfwijze van de
    opgeslagen waarde bepaalt dus niet óf er een signaal is. Een gewoon woord
    dat samenvalt met een contextwaarde (`om` bij context `OM`) is daarmee
    een signaal dat de mens beoordeelt (B-04) — er is bewust geen eigen
    heuristiek die dat onderscheid automatisch maakt. Meerdere spaties in de
    waarde matchen willekeurige whitespace.
    """
    delen = [re.escape(deel) for deel in waarde.casefold().split()]
    kern = r"\s+".join(delen)
    return re.compile(rf"(?<!\w){kern}(?!\w)")


def vind_naamtreffers(tekst: str, contexten: Mapping[str, Any]) -> list[Naamtreffer]:
    """Alle letterlijke treffers van geselecteerde contextwaarden in de tekst.

    Alleen de wérkelijk geselecteerde waarden tellen; er is geen vaste
    naamlijst en geen aliasmapping (`DJI` en `Dienst Justitiële Inrichtingen`
    zijn twee waarden). `gevonden` en `positie` slaan op de oorspronkelijke
    tekst. Gesorteerd op positie.
    """
    gevouwen = _GevouwenTekst.van(tekst)
    treffers: list[Naamtreffer] = []
    for veld in CONTEXT_VELDEN:
        for waarde in canoniseer_contextlijst(contexten.get(veld)):
            for match in _patroon_voor(waarde).finditer(gevouwen.gevouwen):
                start, einde = gevouwen.origineel_bereik(match.start(), match.end())
                treffers.append(
                    Naamtreffer(
                        veld=veld,
                        contextwaarde=waarde,
                        gevonden=tekst[start:einde],
                        positie=start,
                    )
                )
    treffers.sort(key=lambda t: (t.positie, t.veld, t.contextwaarde.casefold()))
    return treffers


def _tekst(waarde: Any) -> str:
    """Een getrimde tekst, of leeg wanneer de waarde geen tekst is."""
    return waarde.strip() if isinstance(waarde, str) else ""


def _geldige_beoordeling(
    review: Any, fingerprint: str
) -> tuple[dict[str, dict[str, str]], dict[str, Any]]:
    """Filter de aangeleverde beoordeling op bruikbaarheid.

    Geeft (beslissingen per onderdeel, samenvatting voor het resultaat). Een
    beoordeling telt alleen bij een gelijke vingerafdruk én een benoemde
    actor; een beslissing telt alleen met een bekende functie én een
    vastgelegde reden. Wat niet telt, wordt in de samenvatting benoemd — een
    genegeerde beoordeling mag niet stil verdwijnen.
    """
    if not isinstance(review, Mapping):
        return {}, {"applied": False, "reason": "geen beoordeling aangeleverd"}

    # Alleen een échte, niet-lege tekst telt als beoordelaar, vingerafdruk of
    # reden. Een `str(...)`-conversie zou van `True` of `[""]` een niet-lege
    # string maken en zo een beoordeling zonder geldige beoordelaar of
    # onderbouwing laten doortellen (reviewbevinding op de contractcommit).
    actor = _tekst(review.get("actor"))
    aangeleverd = _tekst(review.get("fingerprint"))
    samenvatting: dict[str, Any] = {
        "applied": False,
        "actor": actor or None,
        "fingerprint": aangeleverd or None,
    }
    if aangeleverd != fingerprint:
        samenvatting["reason"] = (
            "eerdere beoordeling geldt niet meer: tekst, context, term of "
            "versie is gewijzigd"
        )
        return {}, samenvatting
    if not actor:
        samenvatting["reason"] = "beoordeling zonder benoemde beoordelaar genegeerd"
        return {}, samenvatting

    beslissingen: dict[str, dict[str, str]] = {}
    genegeerd: list[str] = []
    ruwe = review.get("decisions")
    for onderdeel, beslissing in (ruwe.items() if isinstance(ruwe, Mapping) else ()):
        if not isinstance(beslissing, Mapping) or not isinstance(onderdeel, str):
            genegeerd.append(str(onderdeel))
            continue
        functie = _tekst(beslissing.get("function")).lower()
        reden = _tekst(beslissing.get("reason"))
        if functie not in _BEKENDE_FUNCTIES or not reden:
            genegeerd.append(onderdeel)
            continue
        beslissingen[onderdeel] = {"function": functie, "reason": reden}

    samenvatting["applied"] = bool(beslissingen)
    if genegeerd:
        samenvatting["ignored"] = sorted(genegeerd)
        samenvatting["reason"] = (
            "beslissing(en) zonder bekende functie of zonder reden genegeerd"
        )
    return beslissingen, samenvatting


def _naamdeel(treffer: Naamtreffer, beslissing: dict[str, str] | None) -> Deeluitkomst:
    aanleiding = (
        f"De naam '{treffer.gevonden}' staat in de definitiezin en is ook "
        f"vastgelegd als {_veldnaam(treffer.veld)} ('{treffer.contextwaarde}')."
    )
    if beslissing is None:
        return Deeluitkomst(
            id=treffer.id,
            status=STATUS_OPEN,
            evidence=treffer.gevonden,
            context_value=treffer.contextwaarde,
            field=treffer.veld,
            position=treffer.positie,
            reason=(
                f"{aanleiding} Nog niet is vastgesteld of de naam nodig is om "
                "dit begrip af te bakenen of alleen de registratiecontext noemt."
            ),
            action=_ACTIE_OPEN,
        )

    functie = beslissing["function"]
    motivering = beslissing["reason"]
    if functie == FUNCTIE_REGISTRATIE:
        return Deeluitkomst(
            id=treffer.id,
            status=STATUS_FAIL,
            evidence=treffer.gevonden,
            context_value=treffer.contextwaarde,
            field=treffer.veld,
            position=treffer.positie,
            reason=(
                f"{aanleiding} Beoordeeld als registratiecontext: {motivering} "
                "Registratiecontext hoort buiten de definitiezin."
            ),
            action=_ACTIE_REGISTRATIE,
        )
    if functie == FUNCTIE_NOODZAKELIJK:
        return Deeluitkomst(
            id=treffer.id,
            status=STATUS_PASS,
            evidence=treffer.gevonden,
            context_value=treffer.contextwaarde,
            field=treffer.veld,
            position=treffer.positie,
            reason=(
                f"{aanleiding} Beoordeeld als inhoudelijk noodzakelijk voor de "
                f"afbakening of identificatie: {motivering}"
            ),
            action="Geen actie nodig; de naam mag in de definitiezin blijven.",
        )
    return Deeluitkomst(
        id=treffer.id,
        status=STATUS_OPEN,
        evidence=treffer.gevonden,
        context_value=treffer.contextwaarde,
        field=treffer.veld,
        position=treffer.positie,
        reason=(
            f"{aanleiding} De expert vond de functie nog onduidelijk: {motivering}"
        ),
        action=_ACTIE_OPEN,
    )


def _veldnaam(veld: str) -> str:
    return {
        "organisatorische_context": "organisatorische context",
        "juridische_context": "juridische context",
        "wettelijke_basis": "wettelijke basis",
    }.get(veld, veld)


def _samengesteld(parts: tuple[Deeluitkomst, ...]) -> str:
    """B-08: één fail → fail; alles pass → pass; technische fout → error; anders open.

    Een bewezen overtreding blijft leidend, ook naast een mislukt onderdeel.
    Zonder overtreding maakt een mislukt onderdeel de regel als geheel een
    technische fout — geen 'Voldoet', want een vereiste beoordeling is niet
    uitgevoerd, en geen 'Voldoet niet', want een fout bewijst geen
    overtreding.
    """
    statussen = {p.status for p in parts}
    if STATUS_FAIL in statussen:
        return STATUS_FAIL
    if STATUS_ERROR in statussen:
        return STATUS_ERROR
    if statussen == {STATUS_PASS}:
        return STATUS_PASS
    return STATUS_OPEN


def _naamdeel_veilig(
    treffer: Naamtreffer, beslissing: dict[str, str] | None
) -> Deeluitkomst:
    """Eén deelcontrole; een fout erin raakt de overige onderdelen niet.

    Het mislukte onderdeel wordt als apart `error`-deel gepubliceerd, mét de
    aanleiding (evidence) maar zonder interne foutdetails als normuitleg
    (B-08). De technische oorzaak is voor het log van de aanroeper.
    """
    try:
        return _naamdeel(treffer, beslissing)
    except Exception as exc:
        logger.warning(
            "CON-01: deelcontrole voor naamsignaal %s mislukte: %s: %s",
            treffer.id,
            type(exc).__name__,
            exc,
            exc_info=True,
        )
        return Deeluitkomst(
            id=treffer.id,
            status=STATUS_ERROR,
            evidence=treffer.gevonden,
            context_value=treffer.contextwaarde,
            field=treffer.veld,
            position=treffer.positie,
            reason=_UITLEG_DEELFOUT,
            action=_ACTIE_DEELFOUT,
        )


def beoordeel_context(
    begrip: str,
    tekst: str,
    contexten: Mapping[str, Any],
    *,
    review: Any = None,
    definitie_versie: int | str | None = None,
) -> ContextUitkomst:
    """De CON-01-beoordeling van één definitietekst met zijn recordcontext.

    `contexten` is de metadata-mapping met (mogelijk) de drie lijsten;
    `review` is de eerder vastgelegde menselijke beoordeling
    (`{"fingerprint", "actor", "decisions": {onderdeel: {"function", "reason"}}}`).
    """
    fingerprint = bereken_vingerafdruk(begrip, tekst, contexten, definitie_versie)
    heeft_context = any(
        canoniseer_contextlijst(contexten.get(v)) for v in CONTEXT_VELDEN
    )

    if not heeft_context:
        deel = Deeluitkomst(
            id=ONDERDEEL_CONTEXT,
            status=STATUS_FAIL,
            reason=_UITLEG_GEEN_CONTEXT,
            action=_ACTIE_GEEN_CONTEXT,
        )
        return ContextUitkomst(
            status=STATUS_FAIL,
            fingerprint=fingerprint,
            parts=(deel,),
            review=None,
        )

    beslissingen, samenvatting = _geldige_beoordeling(review, fingerprint)
    parts: list[Deeluitkomst] = [
        Deeluitkomst(
            id=ONDERDEEL_CONTEXT,
            status=STATUS_PASS,
            reason=_UITLEG_CONTEXT_AANWEZIG,
            action="Geen actie nodig.",
        )
    ]
    for treffer in vind_naamtreffers(tekst, contexten):
        parts.append(_naamdeel_veilig(treffer, beslissingen.get(treffer.id)))

    delen = tuple(parts)
    return ContextUitkomst(
        status=_samengesteld(delen),
        fingerprint=fingerprint,
        parts=delen,
        review=samenvatting if review is not None else None,
    )
