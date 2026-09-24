"""INT-01: functionele zinsgrenzen in plaats van een woordlijst (DEF-770).

Pure domeinlogica: de evaluator (`services.validation.evaluators.
sentence_boundary`) en de persistentielaag (`domain.int01.opslag`) gebruiken
exact dezelfde segmentatie en dezelfde deeluitkomst.

ASTRA INT-01 (revisie 8532) vraagt een compacte, begrijpelijke definitie in
één zin. De eerdere evaluator keurde af op losse woorden ('die', 'en') en
leestekens (komma, puntkomma): het ASTRA-goedvoorbeeld 'eis die ...' en
'dr. Smit' faalden, een vraagzin plus tweede zin passeerde. Deze evaluator
beoordeelt uitsluitend werkelijke zinsgrenzen, naar de functie van het teken
in de passage:

- '.', '?' of '!' gevolgd door witruimte en een nieuw zinsbegin is een grens;
- een punt in een afkorting, getal of naaminitiaal is geen grens; een
  afkorting die ook een zin kan afsluiten ('enz. Het ...') is onzeker;
- een puntkomma en een dubbele punt zijn nooit een zelfstandige grens (K4);
- een regelomloop is niet vanzelf een tweede zin; een alinea- of
  opsommingsstructuur wordt als onzeker getoond, niet stil genegeerd;
- aanhalingstekens rond de hele kern maken twee zinnen niet één; een grens
  binnen een ingesloten citaat of haakjes is onzeker;
- een naamwoordelijke kern zonder zelfstandige hoofdzin is geldig: er is geen
  hoofdzin- of persoonsvormplicht.

Eén vastgestelde zin is een deelbevinding. Compactheid en begrijpelijkheid
voor de doelgroep zijn daarmee niet beoordeeld; de regel als geheel wordt
daarom nooit stil `pass`. De uitkomst is `fail` (zekere tweede zin) of
`review_required` (één zin vastgesteld of grens onzeker), steeds met een
gestructureerde deeluitkomst in `metadata["rule_result"]`: per grens de
passage, positie en reden, en een apart open onderdeel voor compactheid en
begrijpelijkheid. Geen cijfer, geen automatische tekstwijziging.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

__all__ = [
    "CONTRACTVERSIE",
    "REDEN_MEERDERE_ZINNEN",
    "SUGGESTIE_MEERDERE_ZINNEN",
    "Segmentatie",
    "Zinsgrens",
    "melding_meerdere_zinnen",
    "open_melding",
    "regeluitkomst",
    "segmenteer",
]

# Uitkomststatussen (spiegelen `toetsregels.runtime_contract.ResultStatus`;
# de domeinlaag kent de servicelaag niet).
_PASS = "pass"
_FAIL = "fail"
_OPEN = "review_required"

#: Versie van de vorm van de INT-01-deeluitkomst in `rule_results`.
CONTRACTVERSIE = "def770-int01/1"

#: Sleutel waarmee de service de suggestie bij een tweede zin opbouwt.
REDEN_MEERDERE_ZINNEN = "int01_meerdere_zinnen"

SUGGESTIE_MEERDERE_ZINNEN = (
    "Bepaal eerst of de volgende zin afbakening bevat of alleen uitweiding over "
    "positionering of vergelijking. Voeg afbakening samen met de eerste zin en "
    "plaats alleen uitweiding in de toelichting. Behoud onderscheidende "
    "kenmerken, noodzakelijke namen, negaties en de bronbetekenis; maak de "
    "betekenis niet smaller of ruimer om korter te formuleren. De app herschrijft "
    "de tekst niet automatisch."
)

_OPEN_COMPACT_BEGRIJPELIJK = (
    "Compactheid en begrijpelijkheid zijn nog niet inhoudelijk beoordeeld."
)

_EINDTEKEN = re.compile(r"\.\.\.|…|[.?!]")
_SLUITERS = "\"'”’»)]"
_OPENERS = "\"'“‘„«(["
_PAREN = {"“": "”", "„": "”", "‘": "’", "«": "»", "(": ")", "[": "]"}
_CITAATOPENERS = frozenset({"“", "„", "‘", "«", '"', "'"})
_LIJSTREGEL = re.compile(r"[ \t]*(?:[-*•–]\s|\d{1,3}[.)]\s|[a-z][.)]\s)")
_VOORAFGAAND_WOORD = re.compile(r"[\w.]+$")
_GESTIPPELDE_AFKORTING = re.compile(r"^(?:[a-z]\.)+[a-z]$")

# Afkortingen naar hun functie (kleine letters, zonder slotpunt). Een lijst is
# hier geen afkeurgrond maar alleen een uitzondering; wat niet eenduidig is,
# wordt onzeker getoond.
_TITELS = frozenset(
    {"dr", "mr", "prof", "ir", "ing", "drs", "dhr", "mevr", "mw", "st", "ds"}
)
_VERWIJZINGEN = frozenset({"art", "nr", "hfst", "par", "blz", "jo", "vgl", "cf"})
_MOGELIJK_ZINSLOT = frozenset({"enz", "etc", "e.d", "e.a", "o.i.d", "e.v", "c.s"})
# Afkortingen die gewoonlijk vóór een getal staan ('art. 3', 'ca. 5', 'jan.
# 2020'). Alleen daar is een volgend getal geen grens; na elke andere
# afkorting kan een getal een nieuwe zin openen ('enz. 3 velden ...').
_VOOR_GETAL = frozenset(
    {"ca", "max", "min", "ong", "incl", "excl", "resp", "jan", "feb", "mrt", "apr"}
    | {"jun", "jul", "aug", "sep", "sept", "okt", "nov", "dec"}
)
_OVERIGE_AFKORTINGEN = frozenset(
    {
        "bijv",
        "bv",
        "ca",
        "resp",
        "evt",
        "incl",
        "excl",
        "max",
        "min",
        "ong",
        "zgn",
        "vs",
        "jan",
        "feb",
        "mrt",
        "apr",
        "jun",
        "jul",
        "aug",
        "sep",
        "sept",
        "okt",
        "nov",
        "dec",
    }
)


@dataclass(frozen=True)
class Zinsgrens:
    """Eén (mogelijke) zinsgrens: waar, in welke passage en waarom."""

    positie: int
    passage: str
    grond: str


@dataclass(frozen=True)
class Segmentatie:
    """Uitkomst van de functionele zinsgrensbepaling voor één kern."""

    zekere_grenzen: tuple[Zinsgrens, ...]
    onzekere_grenzen: tuple[Zinsgrens, ...]
    geheel_geciteerd: bool


@dataclass(frozen=True)
class _Kandidaat:
    """Een leesteken gevolgd door witruimte en verdere tekst."""

    start: int
    einde: int
    teken: str
    woord: str
    volgend: str
    ingesloten: bool
    sluiter_direct_na: bool
    #: Het woord vóór `woord` (zonder slotpunt), voor de naamcontext van een
    #: losse hoofdletter.
    voorwoord: str = ""


def segmenteer(tekst: str) -> Segmentatie | None:
    """Bepaal de zinsgrenzen van een definitiekern; None als er geen tekst is."""
    if not (tekst or "").strip():
        return None
    spans = _ingesloten_spans(tekst)
    geheel = _geheel_geciteerd(tekst, spans)
    ingesloten = [
        (start, eind) for start, eind in spans if not _dekt_geheel(tekst, start, eind)
    ]
    zeker: list[Zinsgrens] = []
    onzeker: list[Zinsgrens] = []
    for kandidaat in _leestekenkandidaten(tekst, ingesloten):
        soort, grond = _classificeer(kandidaat, tekst)
        _boek(
            soort,
            Zinsgrens(kandidaat.start, _passage(tekst, kandidaat), grond),
            zeker,
            onzeker,
        )
    for grens in _regelgrenzen(tekst):
        onzeker.append(grens)
    onzeker.sort(key=lambda grens: grens.positie)
    return Segmentatie(tuple(zeker), tuple(onzeker), geheel)


def _boek(
    soort: str, grens: Zinsgrens, zeker: list[Zinsgrens], onzeker: list[Zinsgrens]
) -> None:
    if soort == "zeker":
        zeker.append(grens)
    elif soort == "onzeker":
        onzeker.append(grens)


def _ingesloten_spans(tekst: str) -> list[tuple[int, int]]:
    """Gesloten paren van aanhalingstekens en haakjes als (open, sluit)."""
    spans: list[tuple[int, int]] = []
    stapel: list[tuple[str, int]] = []
    for index, teken in enumerate(tekst):
        if stapel and teken == stapel[-1][0]:
            _, start = stapel.pop()
            spans.append((start, index))
        elif teken in _PAREN:
            stapel.append((_PAREN[teken], index))
        elif teken == '"' or (teken == "'" and _opent_enkel(tekst, index)):
            stapel.append((teken, index))
    return spans


def _opent_enkel(tekst: str, index: int) -> bool:
    """Een recht enkel aanhalingsteken opent alleen vóór een woord ('s-... niet)."""
    vorig = tekst[index - 1] if index else " "
    volgend = tekst[index + 1 : index + 3]
    return (
        (vorig.isspace() or vorig in _OPENERS)
        and bool(volgend[:1])
        and volgend[:1].isalnum()
        and volgend != "s-"
    )


def _dekt_geheel(tekst: str, start: int, eind: int) -> bool:
    kern = tekst.strip()
    begin = len(tekst) - len(tekst.lstrip())
    staart = tekst[eind + 1 :].strip()
    return start == begin and all(teken in ".?!…" for teken in staart) and bool(kern)


def _geheel_geciteerd(tekst: str, spans: list[tuple[int, int]]) -> bool:
    return any(
        tekst[start] in _CITAATOPENERS and _dekt_geheel(tekst, start, eind)
        for start, eind in spans
    )


def _leestekenkandidaten(
    tekst: str, ingesloten: list[tuple[int, int]]
) -> list[_Kandidaat]:
    kandidaten: list[_Kandidaat] = []
    for match in _EINDTEKEN.finditer(tekst):
        index = match.end()
        while index < len(tekst) and tekst[index] in _SLUITERS:
            index += 1
        if not tekst[index:].strip() or not tekst[index].isspace():
            # Slotteken, of een punt binnen een getal, afkorting of adres.
            continue
        kandidaten.append(
            _Kandidaat(
                start=match.start(),
                einde=index,
                teken=match.group(),
                woord=_vorig_woord(tekst, match.start()),
                volgend=tekst[index:].lstrip().lstrip(_OPENERS),
                ingesloten=any(s < match.start() < e for s, e in ingesloten),
                sluiter_direct_na=index > match.end(),
                voorwoord=_woord_ervoor(tekst, match.start()),
            )
        )
    return kandidaten


def _vorig_woord(tekst: str, positie: int) -> str:
    treffer = _VOORAFGAAND_WOORD.search(tekst[:positie])
    return treffer.group().strip(".") if treffer else ""


def _woord_ervoor(tekst: str, positie: int) -> str:
    """Het woord vóór het woord dat op `positie` eindigt."""
    treffer = _VOORAFGAAND_WOORD.search(tekst[:positie])
    if not treffer:
        return ""
    return _vorig_woord(tekst, len(tekst[: treffer.start()].rstrip()))


def _naamcontext(voorwoord: str) -> bool:
    """Een titel ('dr. J.') of andere initiaal ('J. K.') maakt de naamfunctie
    van een losse hoofdletter duidelijk; al het andere niet."""
    return voorwoord.lower() in _TITELS or (
        len(voorwoord) == 1 and voorwoord.isalpha() and voorwoord.isupper()
    )


def _begin(volgend: str) -> str:
    """'hoofd', 'klein', 'cijfer' of 'overig' voor het volgende zinsdeel."""
    eerste = volgend[:1]
    if eerste.isdigit():
        return "cijfer"
    if eerste.isalpha():
        return "hoofd" if eerste.isupper() else "klein"
    return "overig"


def _classificeer(kandidaat: _Kandidaat, tekst: str) -> tuple[str, str]:
    """('zeker'|'onzeker'|'geen', grond) voor één leestekenkandidaat."""
    if kandidaat.teken in ("...", "…"):
        return _classificeer_weglating(kandidaat)
    if kandidaat.teken in "?!":
        return _classificeer_vraag_uitroep(kandidaat)
    afkorting = _afkortingsfunctie(kandidaat.woord)
    if afkorting is not None:
        return _classificeer_afkorting(afkorting, kandidaat)
    if kandidaat.woord.isdigit():
        return _classificeer_getal(kandidaat, tekst)
    return _classificeer_punt(kandidaat)


def _classificeer_weglating(kandidaat: _Kandidaat) -> tuple[str, str]:
    if _begin(kandidaat.volgend) == "hoofd":
        return "onzeker", "weglatingsteken gevolgd door een hoofdletter"
    return "geen", ""


def _classificeer_vraag_uitroep(kandidaat: _Kandidaat) -> tuple[str, str]:
    begin = _begin(kandidaat.volgend)
    if begin == "klein":
        if kandidaat.ingesloten or kandidaat.sluiter_direct_na:
            return "geen", ""
        return "onzeker", "vraag- of uitroepteken gevolgd door een kleine letter"
    if kandidaat.ingesloten:
        return (
            "onzeker",
            "vraag- of uitroepteken binnen een ingesloten citaat of haakjes",
        )
    return "zeker", "vraag- of uitroepteken gevolgd door een nieuw zinsbegin"


def _afkortingsfunctie(woord: str) -> str | None:
    laag = woord.lower()
    if len(woord) == 1 and woord.isalpha():
        return "initiaal" if woord.isupper() else "lijstletter"
    if laag in _TITELS:
        return "titel"
    if laag in _VERWIJZINGEN:
        return "verwijzing"
    if laag in _MOGELIJK_ZINSLOT:
        return "mogelijk_zinslot"
    if laag in _OVERIGE_AFKORTINGEN or _GESTIPPELDE_AFKORTING.match(laag):
        return "afkorting"
    return None


def _classificeer_afkorting(functie: str, kandidaat: _Kandidaat) -> tuple[str, str]:
    begin = _begin(kandidaat.volgend)
    if begin == "klein":
        return "geen", ""
    if begin == "cijfer":
        if functie == "verwijzing" or kandidaat.woord.lower() in _VOOR_GETAL:
            return "geen", ""
        return "onzeker", "afkorting gevolgd door een getal: mogelijk nieuw zinsbegin"
    if functie == "titel" and begin == "hoofd":
        return "geen", ""
    if functie == "initiaal" and begin == "hoofd":
        # Naaminitiaal ('J. Jansen') en zinseinde ('categorie A. Registratie
        # ...') zijn aan het volgende woord niet te onderscheiden. Alleen een
        # titel of een andere initiaal ervóór maakt de naam duidelijk; anders
        # zichtbaar onzeker, nooit stil één zin.
        if _naamcontext(kandidaat.voorwoord):
            return "geen", ""
        return (
            "onzeker",
            (
                "losse hoofdletter gevolgd door een hoofdletter: naaminitiaal of "
                "zinseinde niet vast te stellen"
            ),
        )
    if functie == "mogelijk_zinslot":
        return "onzeker", "afkorting die ook een zin kan afsluiten"
    return "onzeker", "afkorting gevolgd door een hoofdletter"


def _classificeer_getal(kandidaat: _Kandidaat, tekst: str) -> tuple[str, str]:
    regelbegin = tekst.rfind("\n", 0, kandidaat.start) + 1
    if (
        not tekst[regelbegin : kandidaat.start]
        .strip(" \t")
        .removesuffix(kandidaat.woord)
        .strip()
    ):
        return "onzeker", "genummerd opsommingsitem"
    if _begin(kandidaat.volgend) == "hoofd":
        if kandidaat.ingesloten:
            return "onzeker", "punt binnen een ingesloten citaat of haakjes"
        return "zeker", "getal aan zinseinde gevolgd door een nieuw zinsbegin"
    return "geen", ""


def _classificeer_punt(kandidaat: _Kandidaat) -> tuple[str, str]:
    begin = _begin(kandidaat.volgend)
    if begin in ("hoofd", "cijfer"):
        if kandidaat.ingesloten:
            return "onzeker", "punt binnen een ingesloten citaat of haakjes"
        return "zeker", "punt gevolgd door een nieuw zinsbegin"
    if begin == "klein":
        return (
            "onzeker",
            (
                "punt gevolgd door een kleine letter: onbekende afkorting of nieuwe "
                "zin zonder hoofdletter"
            ),
        )
    return "onzeker", "punt gevolgd door een teken dat geen zinsbegin is"


def _regelgrenzen(tekst: str) -> list[Zinsgrens]:
    """Alinea- en opsommingsstructuur zonder slotteken: zichtbaar onzeker.

    Een enkele regelomloop midden in een formulering is geen grens. Een
    regelovergang na een slotteken is al via het leesteken beoordeeld.
    """
    grenzen: list[Zinsgrens] = []
    for match in re.finditer(r"\n", tekst):
        index = match.start()
        voor = tekst[:index].rstrip()
        rest = tekst[index + 1 :]
        if not voor or not rest.strip() or voor[-1] in ".?!…":
            continue
        if _LIJSTREGEL.match(rest):
            grond = "opsommingsteken of regelstructuur"
        elif re.match(r"[ \t]*\n", rest):
            grond = "alinea-overgang zonder slotteken"
        else:
            continue
        grenzen.append(Zinsgrens(index, _regelpassage(voor, rest), grond))
    return grenzen


def _passage(tekst: str, kandidaat: _Kandidaat) -> str:
    links = " ".join(tekst[: kandidaat.start].split()[-3:])
    teken = tekst[kandidaat.start : kandidaat.einde]
    rechts = " ".join(tekst[kandidaat.einde :].split()[:4])
    return f"{links}{teken} {rechts}".strip()


def _regelpassage(voor: str, rest: str) -> str:
    links = " ".join(voor.split()[-3:])
    rechts = " ".join(rest.split()[:4])
    return f"{links} ↵ {rechts}".strip()


# ── Uitkomst ─────────────────────────────────────────────────────────────


def _deel(
    deel_id: str,
    status: str,
    reden: str,
    actie: str,
    grens: Zinsgrens | None = None,
) -> dict[str, Any]:
    return {
        "id": deel_id,
        "status": status,
        "evidence": grens.passage if grens else None,
        "context_value": None,
        "field": None,
        "position": grens.positie if grens else None,
        "reason": reden,
        "action": actie,
    }


def _grensdelen(seg: Segmentatie) -> list[dict[str, Any]]:
    delen = [
        _deel(
            f"zinsgrens_{nummer}",
            _FAIL,
            f"Nieuwe zin: {grens.grond}. INT-01 vraagt één zin.",
            SUGGESTIE_MEERDERE_ZINNEN,
            grens,
        )
        for nummer, grens in enumerate(seg.zekere_grenzen, start=1)
    ]
    delen += [
        _deel(
            f"zinsgrens_onzeker_{nummer}",
            _OPEN,
            f"Zinsgrens onzeker: {grens.grond}.",
            "Beoordeel of hier een nieuwe zin begint. Is het één formulering, dan "
            "voldoet de zinsstructuur; begint hier een tweede zin, behandel die dan "
            "als tweede zin.",
            grens,
        )
        for nummer, grens in enumerate(seg.onzekere_grenzen, start=1)
    ]
    if not delen:
        delen.append(
            _deel(
                "zinsstructuur",
                _PASS,
                "Eén definitieformulering vastgesteld; geen zinsgrens gevonden. Dit "
                "zegt niets over compactheid of begrijpelijkheid.",
                "Geen actie voor de zinsstructuur.",
            )
        )
    return delen


def _citaatdeel() -> dict[str, Any]:
    return _deel(
        "broncitaat",
        _OPEN,
        "De hele definitiekern staat tussen aanhalingstekens. Het geciteerde "
        "bronmateriaal telt inhoudelijk mee; aanhalingstekens maken meerdere "
        "zinnen niet één.",
        "Beslis bewust: documenteer een afwijking van deze aanbevolen regel voor "
        "het letterlijke broncitaat, of stel een brongebonden parafrase voor die "
        "de bronbetekenis behoudt. Er is geen automatische vrijstelling en de app "
        "parafraseert niet automatisch.",
    )


def _compactheidsdeel() -> dict[str, Any]:
    return _deel(
        "compactheid",
        _OPEN,
        "Compactheid is nog niet inhoudelijk beoordeeld; het aantal zinnen of "
        "de lengte bewijst die niet.",
        "Beoordeel in de integrale expertbeoordeling of elk kenmerk afbakening "
        "is of uitweiding over positionering of vergelijking; alleen uitweiding "
        "hoort in de toelichting. Noodzakelijke onderscheidende kenmerken, namen "
        "en negaties blijven in de kern.",
    )


def _begrijpelijkheidsdeel() -> dict[str, Any]:
    return _deel(
        "begrijpelijkheid",
        _OPEN,
        "Begrijpelijkheid is nog niet inhoudelijk beoordeeld. De app legt geen "
        "doelgroep vast, dus begrijpelijkheid voor de doelgroep is niet "
        "vastgesteld; de registratiecontext is geen doelgroep.",
        "Beoordeel in de integrale expertbeoordeling of een lezer uit de bedoelde "
        "doelgroep de zin in één lezing kan volgen; noem die doelgroep bij het "
        "oordeel en verzin er geen.",
    )


def regeluitkomst(seg: Segmentatie) -> dict[str, Any]:
    delen = _grensdelen(seg)
    if seg.geheel_geciteerd and seg.zekere_grenzen:
        delen.append(_citaatdeel())
    delen.append(_compactheidsdeel())
    delen.append(_begrijpelijkheidsdeel())
    status = _FAIL if seg.zekere_grenzen else _OPEN
    return {
        "status": status,
        "score": None,
        "contract_version": CONTRACTVERSIE,
        "fingerprint": None,
        "parts": delen,
        "review": None,
    }


def melding_meerdere_zinnen(seg: Segmentatie) -> str:
    eerste = seg.zekere_grenzen[0]
    aantal = len(seg.zekere_grenzen) + 1
    telling = f"ten minste {aantal}" if seg.onzekere_grenzen else str(aantal)
    melding = (
        f"INT-01 — De definitie bevat {telling} zinnen; INT-01 vraagt één zin. "
        f'Zinsgrens bij "{eerste.passage}" ({eerste.grond}).'
    )
    if seg.geheel_geciteerd:
        melding += (
            " De hele kern is een citaat: beoordeel bewust of een afwijking wordt "
            "gedocumenteerd of een brongebonden parafrase wordt voorgesteld."
        )
    return (
        f"{melding} Compactheid en begrijpelijkheid zijn niet automatisch beoordeeld."
    )


def open_melding(seg: Segmentatie) -> str:
    if seg.onzekere_grenzen:
        passages = "; ".join(
            f'"{grens.passage}" ({grens.grond})' for grens in seg.onzekere_grenzen
        )
        return (
            f"INT-01 — Zinsgrens onzeker bij {passages}; beoordeling nodig. "
            f"{_OPEN_COMPACT_BEGRIJPELIJK}"
        )
    return (
        f"INT-01 — Eén definitieformulering vastgesteld. {_OPEN_COMPACT_BEGRIJPELIJK}"
    )
