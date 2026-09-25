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
  afkorting die ook een zin kan afsluiten ('enz. Het ...') is onzeker, net
  als een punt na een woordvorm zonder klinker, ook met hoofdletter ('volgens
  nvr. Nieuwe ...', 'Chr. Huygens'); de punten van een afkorting die de tekst
  zelf verklaart ('(v.qr. = ...)'), zijn intern, maar zo'n afkorting direct
  na een haakje maakt de aansluiting onzeker;
- een slotteken dat een haakjesdeel afsluit, is onzeker (ook bij één woord
  en aan het eind van de kern), tenzij het haakjesdeel alleen uit getallen en
  bekende afkortingen met hun punt bestaat;
- een punt gevolgd door een kleine letter (buiten een bekende afkorting) is
  altijd onzeker: zonder woordsoortkennis is een onderwerp in het vervolg
  niet te bewijzen. Ook een voor een mens duidelijke tweede zin met kleine
  beginletter wordt zo doorverwezen (conservatief, sinds contract /3);
- een beletselteken gevolgd door verdere tekst is onzeker;
- een puntkomma en een dubbele punt zijn nooit een zelfstandige grens (K4);
  een opsomming die na ':', ';' of ',' doorloopt, blijft één formulering;
  een los label dat op een dubbele punt eindigt, is onzeker;
- een regelomloop is niet vanzelf een tweede zin; een alinea- of
  opsommingsstructuur zonder inleidend teken wordt als onzeker getoond;
- aanhalingstekens rond de hele kern maken twee zinnen niet één en geven
  altijd een open onderdeel broncitaat; interne leestekens van een ingesloten
  citaat vormen geen grens van de buitenste zin, binnen haakjes zijn ze
  onzeker. Een slotteken direct vóór het sluitende aanhalingsteken kan ook de
  buitenste zin afsluiten: zonder aantoonbare voortzetting (voorzetselgroepen
  of een vóór het citaat geopende bijzin) blijft het onzeker; een voortzetting
  waarvan de woordrollen niet bewezen zijn ('‘Klaar?’ waarop de namen staan')
  gaat naar inhoudelijke beoordeling;
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

#: Versie van de vorm én de betekenis van de INT-01-deeluitkomst in
#: `rule_results`. /2: herziene grensclassificatie na de T24-proef. /3:
#: conservatieve automatische beoordeling — alleen ondersteunde patronen
#: krijgen een zekere uitkomst, twijfel gaat naar inhoudelijke beoordeling
#: (conservatieve-beoordeling-besluit-v1). /4: eindproef-correctie — slotteken
#: aan het eind van een afsluitend haakjesdeel en een afkortingsachtige
#: woordvorm zonder klinker vóór de punt zijn onzeker; ingebedde citaten met
#: een open bijzin uit naamwoordgroepen of een vervolg uit voorzetselgroepen
#: zijn één formulering (herstelanalyse-v8). /5: herproefcorrectie — de
#: punten van een in de tekst zelf verklaarde afkorting zijn intern, en zo'n
#: afkorting direct na een haakje geeft onzekerheid over de aansluiting
#: (logs/def770-vervolg). /6: titelbeleid (titel-en-budgetbesluit-v1) — de
#: positieve herkenning van een betrekkelijke bijzin met 'waar' + voorzetsel
#: na een citaatslot uit /5 vervalt; zo'n voortzetting met onbewezen
#: woordrollen is onzeker. Een opgeslagen uitkomst onder een andere versie
#: geldt niet meer als actueel.
CONTRACTVERSIE = "def770-int01/6"

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
#: Letters zonder klinker ('nvr', 'Chr', 'NVR', 'mm'): geen gewoon Nederlands
#: woord maar een afkortingsachtige vorm, die de punt kan verklaren.
#: Hoofdlettergebruik bewijst niet dat het geen afkorting is.
_ZONDER_KLINKER = re.compile(r"[b-df-hj-np-tv-xz]{2,}", re.IGNORECASE)
_GETAL = re.compile(r"\d+(?:[.,]\d+)*")
#: Een afkorting met een interne punt ('v.qr', 'dk.st').
_AFKORTINGSVORM = r"[A-Za-z]+(?:\.[A-Za-z]+)+"
#: De tekst verklaart een afkorting zelf: '(v.qr. = vakcodering …)', of een
#: haakjesdeel dat alleen de afkorting noemt, eventueel na 'hierna' of
#: 'afgekort' ('… standaard (hierna: dk.st.)').
_VERKLARING_IS = re.compile(rf"\(\s*({_AFKORTINGSVORM})\.?\s*=")
_VERKLARING_HAAKJES = re.compile(
    rf"\(\s*(?:(?:hierna|afgekort)\s*:?\s*)?({_AFKORTINGSVORM})\.?\s*\)",
    re.IGNORECASE,
)
_VERKLARINGSDEEL = re.compile(
    rf"(?:(?:hierna|afgekort)\s*:?\s*)?{_AFKORTINGSVORM}\.?", re.IGNORECASE
)
#: Tegenwoordige en verleden persoonsvormen van hulp- en koppelwerkwoorden en
#: veelvoorkomende definitiewerkwoorden. Na een citaatslot sluit een herkende
#: persoonsvorm een bewezen voortzetting uit; afwezigheid bewijst niets.
_PERSOONSVORMEN = frozenset(
    {"is", "wordt", "worden", "werd", "werden", "blijft", "blijven", "bleef"}
    | {"bleven", "heeft", "hebben", "had", "hadden", "kan", "kunnen", "kon"}
    | {"konden", "moet", "moeten", "moest", "moesten", "mag", "mogen", "mocht"}
    | {"mochten", "zal", "zullen", "zou", "zouden", "geldt", "bevat", "bevatten"}
)
_ZEKER_ZINSBEGIN = re.compile(r"[.?!…]\s+(?=[A-ZÀ-Ý\d])")
#: Woorden die een bijzin of betrekkelijke bijzin inleiden (open bijzin vóór
#: een citaat).
_ONDERSCHIKKEND = frozenset(
    {"die", "dat", "wat", "wie", "welke", "waar", "waarbij", "waarin", "waarop"}
    | {"waarvan", "waardoor", "waarmee", "waarna", "als", "indien", "mits"}
    | {"tenzij", "omdat", "doordat", "zodat", "terwijl", "nadat", "voordat"}
    | {"totdat", "hoewel", "zodra", "wanneer"}
)
#: Voorzetsels die een slotwoordgroep na een citaat kunnen openen.
_VOORZETSELS = frozenset(
    {"aan", "achter", "bij", "binnen", "boven", "buiten", "door", "in", "langs"}
    | {"met", "na", "naar", "naast", "onder", "op", "over", "per", "sinds"}
    | {"tegen", "tijdens", "tot", "uit", "van", "vanaf", "via", "volgens"}
    | {"voor", "zonder", "ter", "ten"}
)
_LIDWOORDEN = frozenset(
    {"de", "het", "een", "deze", "dit", "elke", "ieder", "iedere", "geen"}
    | {"alle", "zijn", "haar", "hun"}
)

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
    #: Het teken staat binnen een ingesloten citaat (niet: haakjes).
    in_citaat: bool = False
    #: Positie van het openende aanhalingsteken van dat citaat (anders -1).
    citaatbegin: int = -1
    #: Inhoud van het haakjesdeel dat het teken direct afsluit (anders None).
    haakjesdeel: str | None = None


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
    onzeker.extend(_regelgrenzen(tekst))
    onzeker.extend(_label_zonder_vervolg(tekst))
    onzeker.extend(_aansluiting_na_haakje(tekst))
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
        omvattend = [(s, e) for s, e in ingesloten if s < match.start() < e]
        haakjesdeel = _gesloten_haakjesdeel(tekst, match, omvattend)
        if haakjesdeel is None and (
            not tekst[index:].strip() or not tekst[index].isspace()
        ):
            # Slotteken, of een punt binnen een getal, afkorting of adres.
            continue
        # Het binnenste omvattende paar bepaalt de functie.
        in_citaat = bool(omvattend) and tekst[max(omvattend)[0]] in _CITAATOPENERS
        kandidaten.append(
            _Kandidaat(
                start=match.start(),
                einde=index,
                teken=match.group(),
                woord=_vorig_woord(tekst, match.start()),
                volgend=tekst[index:].lstrip().lstrip(_OPENERS),
                ingesloten=bool(omvattend),
                sluiter_direct_na=index > match.end(),
                voorwoord=_woord_ervoor(tekst, match.start()),
                in_citaat=in_citaat,
                citaatbegin=max(omvattend)[0] if in_citaat else -1,
                haakjesdeel=haakjesdeel,
            )
        )
    return kandidaten


def _gesloten_haakjesdeel(
    tekst: str, match: re.Match[str], omvattend: list[tuple[int, int]]
) -> str | None:
    """De inhoud van het haakjesdeel dat het teken direct afsluit ('(De
    beheerder wist deze na de oefening.)', '(Stop!)'), ook als er daarna geen
    tekst meer volgt; anders None."""
    if not omvattend:
        return None
    start, eind = max(omvattend)
    if tekst[start] not in "([" or eind != match.end():
        return None
    return tekst[start + 1 : match.start()]


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
    if kandidaat.haakjesdeel is not None:
        if _VERKLARINGSDEEL.fullmatch(kandidaat.haakjesdeel.strip() + kandidaat.teken):
            # Het haakjesdeel verklaart alleen een afkorting ('(hierna: dk.st.)').
            return "geen", ""
        return _classificeer_haakjesslot(kandidaat.haakjesdeel + kandidaat.teken)
    if kandidaat.in_citaat and not kandidaat.sluiter_direct_na:
        # Interne citaatpunctuatie ('“Beleid. Uitvoering”'): hoort bij het
        # citaat, de buitenste zin loopt door.
        return "geen", ""
    if kandidaat.in_citaat and _begin(kandidaat.volgend) not in ("hoofd", "cijfer"):
        # Het slotteken staat direct vóór het sluitende aanhalingsteken: dat
        # kan het citaat én de buitenste zin afsluiten.
        return _classificeer_citaatslot(kandidaat, tekst)
    if kandidaat.teken in ("...", "…"):
        return _classificeer_weglating(kandidaat)
    if kandidaat.teken in "?!":
        return _classificeer_vraag_uitroep(kandidaat)
    if kandidaat.woord.lower() in _verklaarde_afkortingen(tekst):
        return _classificeer_verklaarde_afkorting(kandidaat, tekst)
    afkorting = _afkortingsfunctie(kandidaat.woord)
    if afkorting is not None:
        return _classificeer_afkorting(afkorting, kandidaat)
    if kandidaat.woord.isdigit():
        return _classificeer_getal(kandidaat, tekst)
    return _classificeer_punt(kandidaat)


def _verklaarde_afkortingen(tekst: str) -> frozenset[str]:
    """Afkortingen die de tekst zelf verklaart (kleine letters, zonder slotpunt).

    Alleen vormen met een interne punt ('v.qr'); zo'n vorm is geen woord dat
    een zelfstandige zin kan zijn, en de verklaring maakt haar punten intern."""
    return frozenset(
        treffer.group(1).lower()
        for patroon in (_VERKLARING_IS, _VERKLARING_HAAKJES)
        for treffer in patroon.finditer(tekst)
    )


def _classificeer_verklaarde_afkorting(
    kandidaat: _Kandidaat, tekst: str
) -> tuple[str, str]:
    """Slotpunt van een in de tekst verklaarde afkorting.

    De punten tussen de delen ('v.qr') zijn geen kandidaat; de verklaring
    bewijst de afkortingsfunctie. De slotpunt kan tegelijk zinseinde zijn:
    de verklaring bewijst geen ononderbroken vervolg. Alleen in de verklaring
    zelf (direct gevolgd door '=' of het sluitende haakje) is zij aantoonbaar
    intern. Staat de vermelding direct na een sluitend haakje, dan meldt
    `_aansluiting_na_haakje` die overgang al als onduidelijke aansluiting, met
    een passage die deze punt omvat; een tweede melding met de afkorting als
    reden zou de verkeerde grond geven. Elders blijft de slotpunt onzeker."""
    if kandidaat.volgend[:1] in ("=", ")"):
        return "geen", ""
    if _begin(kandidaat.volgend) in ("hoofd", "cijfer"):
        return (
            "onzeker",
            (
                "verklaarde afkorting gevolgd door een hoofdletter of cijfer: "
                "afkorting of zinseinde niet vast te stellen"
            ),
        )
    begin_vermelding = kandidaat.start - len(kandidaat.woord)
    if begin_vermelding in _vermeldingen_na_haakje(tekst):
        # Dezelfde overgang staat al als onduidelijke aansluiting gemeld.
        return "geen", ""
    return (
        "onzeker",
        (
            "slotpunt van een verklaarde afkorting gevolgd door verdere tekst: "
            "afkortingspunt of ook zinseinde niet vast te stellen"
        ),
    )


def _aansluiting_na_haakje(tekst: str) -> list[Zinsgrens]:
    """Een verklaarde afkorting direct na een sluitend haakje ('(v.qr. = …)
    v.qr. bepaalt …'): de afkorting is een naamwoord, en zonder verbindend woord
    is niet vast te stellen of de formulering doorloopt of een nieuwe mededeling
    begint. Onzeker, met passage en positie van het haakje.

    De vermeldingen komen uit `_vermeldingen_na_haakje`, dezelfde bron die de
    classificatie gebruikt om de afkortingsmelding op precies die overgang te
    laten vervallen: onderdrukking en vervangende melding delen één voorwaarde.
    """
    grenzen: list[Zinsgrens] = []
    for begin, haakje in _vermeldingen_na_haakje(tekst).items():
        links = re.search(r"\S*$", tekst[:haakje])
        rechts = re.match(r"\s*\S+(?:\s+\S+){0,3}", tekst[begin:])
        start = links.start() if links else haakje
        einde = begin + (rechts.end() if rechts else 0)
        grenzen.append(
            Zinsgrens(
                haakje,
                " ".join(tekst[start:einde].split()),
                (
                    "onduidelijke aansluiting na het haakje: een verklaarde "
                    "afkorting volgt zonder verbindend woord; doorlopende "
                    "formulering of nieuwe mededeling niet vast te stellen"
                ),
            )
        )
    return grenzen


def _vermeldingen_na_haakje(tekst: str) -> dict[int, int]:
    """Begin van elke vermelding van een verklaarde afkorting die direct (na
    nul of meer witruimte) op een sluitend haakje volgt, met de positie van
    dat haakje."""
    verklaard = _verklaarde_afkortingen(tekst)
    vermeldingen: dict[int, int] = {}
    for treffer in re.finditer(rf"\)\s*({_AFKORTINGSVORM})\.?(?![\w.])", tekst):
        if treffer.group(1).lower() in verklaard:
            vermeldingen[treffer.start(1)] = treffer.start()
    return vermeldingen


def _classificeer_haakjesslot(haakjesdeel: str) -> tuple[str, str]:
    """Slotteken dat een haakjesdeel afsluit (`haakjesdeel` inclusief dat
    slotteken).

    Alleen een haakjesdeel dat geheel uit getallen en bekende afkortingen met
    hun punt bestaat ('(max. 5 st.)', '(o.a.)', '(3.)') bevat geen woord dat
    een zelfstandige zin kan dragen. Anders kan tussen de haakjes een
    zelfstandige zin staan, ook bij één woord ('(Stop!)', '(Psst!)') of een
    slotafkorting ('(De registratie sluit in dec.)'), en ook als er daarna
    niets meer volgt: onzeker, nooit automatisch fail.
    """
    if all(map(_fragmentdeel, haakjesdeel.split())):
        return "geen", ""
    return (
        "onzeker",
        (
            "slotteken aan het eind van een haakjesdeel: zelfstandige zin tussen "
            "haakjes niet uit te sluiten"
        ),
    )


def _fragmentdeel(token: str) -> bool:
    """Een getal, of een bekende afkorting met haar punt ('max.', 'o.a.').

    Een onbekende vorm zonder klinker ('Psst', 'mm') of een losse letter
    ('O') bewijst geen afkortingsfunctie; een getal maakt een volgend
    onbekend woord geen eenheid."""
    token = token.rstrip(",;:")
    if _GETAL.fullmatch(token.rstrip(".?!")):
        return True
    functie = _afkortingsfunctie(token[:-1]) if token.endswith(".") else None
    return functie in ("titel", "verwijzing", "mogelijk_zinslot", "afkorting")


def _classificeer_citaatslot(kandidaat: _Kandidaat, tekst: str) -> tuple[str, str]:
    """Slotteken plus sluitend aanhalingsteken, gevolgd door een kleine letter.

    Alleen een aantoonbare voortzetting van de buitenste zin maakt het één
    formulering. Het ontbreken van een herkende persoonsvorm bewijst dat niet.
    Twee vormen gelden als bewijs, beide zonder herkende persoonsvorm in het
    vervolg:

    - een vervolg uit voorzetselgroepen: telkens voorzetsel, hooguit een
      lidwoord en één woord ('“Gereed.” op het scherm', '‘Wie betaalt?’ van de
      commissie', '‘…?’ voor het reconstrueren van een vaarvolgorde');
    - een bijzin die vóór het citaat is geopend en waarin tot het citaat alleen
      naamwoordgroepen staan ('die de melding “Gereed.” …', 'waarmee een
      bediener de melding “…” …'), met als
      vervolg alleen het slotwerkwoord ('… toont') of een woordgroep die met
      een voorzetsel begint ('… op het scherm laat verschijnen').

    Al het andere ('… voor gebruik is controle vereist', '… de controle volgt
    later', een langere woordgroep) blijft onzeker, met passage en positie.
    Dat geldt ook voor een betrekkelijke bijzin met 'waar' + voorzetsel
    ('‘Wie woont hier?’ waarop de aanwijzingen staan'): zonder woordsoortkennis
    zijn de rollen niet te bewijzen ('waarop het werkt de deelnemers wachten'),
    dus inhoudelijke beoordeling (titel-en-budgetbesluit-v1).
    """
    woorden = _woorden_tot_zeker_zinsbegin(kandidaat.volgend)
    if woorden and not any(woord in _PERSOONSVORMEN for woord in woorden):
        functiewoord = _VOORZETSELS | _LIDWOORDEN
        # Het vervolg eindigt niet op een losse voorzetsel of lidwoord.
        afgerond = woorden[-1] not in functiewoord
        bijzin_slot = (
            _open_bijzin(tekst[: kandidaat.citaatbegin])
            and afgerond
            and (len(woorden) == 1 or woorden[0] in _VOORZETSELS)
        )
        if _voorzetselgroepen(woorden) or bijzin_slot:
            return "geen", ""
    return (
        "onzeker",
        (
            "slotteken vóór een sluitend aanhalingsteken gevolgd door verdere "
            "tekst: einde van het citaat of ook van de buitenste zin niet vast te "
            "stellen"
        ),
    )


def _open_bijzin(voor: str) -> bool:
    """Vlak vóór het citaat is een bijzin geopend waarin tot het citaat alleen
    naamwoordgroepen staan: markering, dan één of meer keer lidwoord 'de' of
    'een' plus één woord ('die de melding', 'waarmee een bediener de
    melding'). Die lidwoorden kunnen geen zelfstandig voornaamwoord zijn, dus
    elk woord erna is de kern van een naamwoordgroep en niet het werkwoord;
    zo is elk woord tussen markering en citaat verklaard. Een los woord ('die
    meldt', 'een bediener meldt') of een voornaamwoord ('die het meldt') kan
    het werkwoord al bevatten: geen bewijs."""
    woorden = re.findall(r"[a-zà-ÿ]+", voor.lower())
    groepen = 0
    while len(woorden) >= 3 and woorden[-2] in ("de", "een"):
        if woorden[-1] in _LIDWOORDEN | _VOORZETSELS | _ONDERSCHIKKEND:
            return False
        del woorden[-2:]
        groepen += 1
    return groepen > 0 and woorden[-1] in _ONDERSCHIKKEND


def _classificeer_weglating(kandidaat: _Kandidaat) -> tuple[str, str]:
    if _begin(kandidaat.volgend) == "hoofd":
        return "onzeker", "weglatingsteken gevolgd door een hoofdletter"
    return (
        "onzeker",
        (
            "beletselteken gevolgd door verdere tekst: onderbreking binnen de zin "
            "of zinseinde niet vast te stellen"
        ),
    )


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
        if _ZONDER_KLINKER.fullmatch(kandidaat.woord):
            # 'volgens nvr. Nieuwe ...': de punt kan bij een onbekende afkorting
            # horen of ook de zin afsluiten.
            return (
                "onzeker",
                (
                    "punt na een afkortingsachtige woordvorm zonder klinker: "
                    "onbekende afkorting of zinseinde niet vast te stellen"
                ),
            )
        return "zeker", "punt gevolgd door een nieuw zinsbegin"
    if begin == "klein":
        # Contract /3 (conservatieve-beoordeling-uitwerking-v2): zonder
        # woordsoortkennis is een onderwerp na de punt niet te bewijzen; ook een
        # lidwoordgroep kan een tijdsbepaling zijn. Altijd onzeker.
        return (
            "onzeker",
            (
                "punt gevolgd door een kleine letter: onbekende afkorting of nieuwe "
                "zin zonder hoofdletter"
            ),
        )
    return "onzeker", "punt gevolgd door een teken dat geen zinsbegin is"


def _voorzetselgroepen(woorden: list[str]) -> bool:
    """Het vervolg bestaat volledig uit voorzetselgroepen: telkens voorzetsel,
    hooguit een lidwoord en één kernwoord ('op het scherm', 'voor het
    reconstrueren van een vaarvolgorde'). Elk woord is dan verklaard en er is
    geen plaats voor een persoonsvorm. Een onvolledige groep ('op', 'op de'),
    een extra woord ('op het grote scherm') of een woord buiten een groep
    ('na afloop volgt ...') bewijst niets."""
    functiewoord = _VOORZETSELS | _LIDWOORDEN
    index = 0
    while index < len(woorden):
        if woorden[index] not in _VOORZETSELS:
            return False
        index += 1
        if index < len(woorden) and woorden[index] in _LIDWOORDEN:
            index += 1
        if index >= len(woorden) or woorden[index] in functiewoord:
            return False
        index += 1
    return bool(woorden)


def _woorden_tot_zeker_zinsbegin(tekst: str) -> list[str]:
    eerste_zin = _ZEKER_ZINSBEGIN.split(tekst, 1)[0].lower()
    return re.findall(r"[a-zà-ÿ]+", eerste_zin)


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
            if voor[-1] in ":;,":
                # Opsomming die na een inleidend of scheidend teken doorloopt:
                # één formulering (K4), geen grens.
                continue
            grond = "opsommingsteken of regelstructuur"
        elif re.match(r"[ \t]*\n", rest):
            grond = "alinea-overgang zonder slotteken"
        else:
            continue
        grenzen.append(Zinsgrens(index, _regelpassage(voor, rest), grond))
    return grenzen


def _label_zonder_vervolg(tekst: str) -> list[Zinsgrens]:
    """Een kern die op een dubbele punt eindigt ('Oefenstatus:'): onzeker."""
    kern = tekst.rstrip()
    if not kern.endswith(":"):
        return []
    return [
        Zinsgrens(
            len(kern) - 1,
            " ".join(kern.split()[-3:]),
            (
                "dubbele punt aan het einde zonder vervolg: onduidelijk of een "
                "afgeronde definitieformulering aanwezig is"
            ),
        )
    ]


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
    if seg.geheel_geciteerd:
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
        melding = f"INT-01 — Zinsgrens onzeker bij {passages}; beoordeling nodig."
    else:
        melding = "INT-01 — Eén definitieformulering vastgesteld."
    if seg.geheel_geciteerd:
        melding += (
            " De hele kern is een citaat: beoordeel bewust of een afwijking wordt "
            "gedocumenteerd of een brongebonden parafrase wordt voorgesteld."
        )
    return f"{melding} {_OPEN_COMPACT_BEGRIJPELIJK}"
