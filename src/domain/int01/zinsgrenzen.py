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
- een punt gevolgd door een kleine letter is onzeker, tenzij het woord ervoor
  aantoonbaar een volledig woord is (een productief zelfstandignaamwoord-
  achtervoegsel zoals '-ing' of '-heid') én het vervolg met een positief
  herkend onderwerp begint (lidwoordgroep, of één woord met een eigen
  voorzetselgroep) en een ondubbelzinnig vervoegde persoonsvorm met aanvulling
  draagt
  die niet in een bijzin of infinitiefconstructie staat: dan is het een
  zekere tweede zin. Dit is een
  conservatieve heuristiek, geen taalgarantie;
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
  buitenste zin afsluiten: zonder aantoonbare voortzetting blijft het
  onzeker;
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
#: `rule_results`. /2: herziene grensclassificatie na de T24-proef; een
#: opgeslagen uitkomst onder een andere versie geldt niet meer als actueel.
CONTRACTVERSIE = "def770-int01/2"

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
#: Productieve zelfstandignaamwoord-achtervoegsels (ook meervoud). Een
#: afkorting breekt een woord gewoonlijk vóór zo'n achtervoegsel af ('afd.',
#: 'voorz.'); eindigt het woord erop, dan is het een volledig woord. Lengte of
#: klinkers bewijzen dat niet.
_VOLLEDIG_WOORD = re.compile(
    r"^[a-zà-ÿ]{3,}"
    r"(?:ingen|ing|heden|heid|schappen|schap|iteiten|iteit|ties|tie|ismen|isme)$"
)
#: Tegenwoordige en verleden persoonsvormen van hulp- en koppelwerkwoorden en
#: veelvoorkomende definitiewerkwoorden. Bewust niet: meervoudsvormen die ook
#: zelfstandig naamwoord of voornaamwoord zijn ('zijn', 'vormen', 'gelden').
_PERSOONSVORMEN = frozenset(
    {"is", "wordt", "worden", "werd", "werden", "blijft", "blijven", "bleef"}
    | {"bleven", "heeft", "hebben", "had", "hadden", "kan", "kunnen", "kon"}
    | {"konden", "moet", "moeten", "moest", "moesten", "mag", "mogen", "mocht"}
    | {"mochten", "zal", "zullen", "zou", "zouden", "geldt", "bevat", "bevatten"}
)
#: Tegenwoordige meervoudsvormen zijn gelijk aan de infinitief ('toegepast
#: worden'): zij bewijzen geen persoonsvorm en dus geen zelfstandige zin.
_INFINITIEF_HOMOGRAAF = frozenset(
    {"worden", "blijven", "hebben", "kunnen", "moeten", "mogen", "zullen"}
    | {"bevatten"}
)
#: Werkwoordelijke woordvorm (voltooid deelwoord met 'ge', onvoltooid
#: deelwoord op '-end(e)'/'-ande'): vóór de persoonsvorm geen bewijs van een
#: onderwerp. Een zelfstandig naamwoord met die vorm blijft zo onzeker.
_WERKWOORDELIJKE_VORM = re.compile(
    r"^(?:[a-z]*ge[a-z]+(?:t|d|en)|[a-z]{3,}(?:ende?|ande))$"
)
_ZEKER_ZINSBEGIN = re.compile(r"[.?!…]\s+(?=[A-ZÀ-Ý\d])")
#: Woorden die een bijzin, betrekkelijke bijzin of infinitiefconstructie
#: inleiden, of nevenschikken. Staan ze vóór de persoonsvorm, dan hoort die
#: persoonsvorm (mogelijk) bij een ondergeschikt deel: geen bewijs van een
#: zelfstandige hoofdzin.
_ONDERSCHIKKEND = frozenset(
    {"die", "dat", "wat", "wie", "welke", "waar", "waarbij", "waarin", "waarop"}
    | {"waarvan", "waardoor", "waarmee", "waarna", "als", "indien", "mits"}
    | {"tenzij", "omdat", "doordat", "zodat", "terwijl", "nadat", "voordat"}
    | {"totdat", "hoewel", "zodra", "wanneer"}
)
_BIJZIN_OF_INFINITIEF = _ONDERSCHIKKEND | {"om", "te", "en", "of", "maar"}
#: Een vervolg dat hiermee begint, opent geen onderwerp maar zet een
#: woordgroep of constructie voort (voorzetsel, voegwoord, infinitief).
_VOORZETSELS = frozenset(
    {"aan", "achter", "bij", "binnen", "boven", "buiten", "door", "in", "langs"}
    | {"met", "na", "naar", "naast", "onder", "op", "over", "per", "sinds"}
    | {"tegen", "tijdens", "tot", "uit", "van", "vanaf", "via", "volgens"}
    | {"voor", "zonder", "ter", "ten"}
)
_GEEN_ONDERWERPSBEGIN = _BIJZIN_OF_INFINITIEF | _VOORZETSELS | {"want", "dus"}
_LIDWOORDEN = frozenset(
    {"de", "het", "een", "deze", "dit", "elke", "ieder", "iedere", "geen"}
    | {"alle", "zijn", "haar", "hun"}
)
#: Lidwoorden en aanwijzende woorden die een onderwerpsgroep openen. Niet de
#: bezittelijke vormen: 'zijn'/'haar' zijn ook werkwoord of voornaamwoord.
_ONDERWERP_LIDWOORDEN = frozenset(
    {"de", "het", "een", "deze", "dit", "elke", "ieder", "iedere", "alle"}
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
        omvattend = [(s, e) for s, e in ingesloten if s < match.start() < e]
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
    afkorting = _afkortingsfunctie(kandidaat.woord)
    if afkorting is not None:
        return _classificeer_afkorting(afkorting, kandidaat)
    if kandidaat.woord.isdigit():
        return _classificeer_getal(kandidaat, tekst)
    return _classificeer_punt(kandidaat)


def _classificeer_citaatslot(kandidaat: _Kandidaat, tekst: str) -> tuple[str, str]:
    """Slotteken plus sluitend aanhalingsteken, gevolgd door een kleine letter.

    Alleen een aantoonbare voortzetting van de buitenste zin maakt het één
    formulering. Het ontbreken van een herkende persoonsvorm bewijst dat niet.
    Twee vormen gelden als bewijs, beide zonder herkende persoonsvorm in het
    vervolg:

    - een korte slotwoordgroep: voorzetsel, hooguit een lidwoord en één woord
      ('“Gereed.” op het scherm', '‘Wie betaalt?’ van de commissie');
    - een bijzin die vlak vóór het citaat is geopend en waarin alleen het
      geciteerde lijdend voorwerp staat ('die de melding “Gereed.” …'), met als
      vervolg alleen het slotwerkwoord ('… toont') of een woordgroep die met
      een voorzetsel begint ('… op het scherm laat verschijnen').

    Al het andere ('… voor gebruik is controle vereist', '… de controle volgt
    later', een langere woordgroep) blijft onzeker, met passage en positie.
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
        if _korte_slotgroep(woorden) or bijzin_slot:
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
    een lijdend voorwerp staat: markering, lidwoord 'de' of 'een' en één woord
    ('die de melding'). Die lidwoorden kunnen geen zelfstandig voornaamwoord
    zijn, dus het woord erna is de kern van een naamwoordgroep en niet het
    werkwoord. Een los woord na de markering ('die meldt') of een voornaamwoord
    ('die het meldt') kan het werkwoord al bevatten: geen bewijs."""
    staart = re.findall(r"[a-zà-ÿ]+", voor.lower())[-3:]
    if len(staart) < 3:
        return False
    return staart[0] in _ONDERSCHIKKEND and staart[1] in ("de", "een")


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
        return "zeker", "punt gevolgd door een nieuw zinsbegin"
    if begin == "klein":
        if (
            not kandidaat.ingesloten
            and _VOLLEDIG_WOORD.match(kandidaat.woord)
            and _eigen_onderwerp_en_persoonsvorm(kandidaat.volgend)
        ):
            return (
                "zeker",
                (
                    "punt na een volledig woord gevolgd door een zelfstandige zin "
                    "met kleine beginletter"
                ),
            )
        return (
            "onzeker",
            (
                "punt gevolgd door een kleine letter: onbekende afkorting of nieuwe "
                "zin zonder hoofdletter"
            ),
        )
    return "onzeker", "punt gevolgd door een teken dat geen zinsbegin is"


def _eigen_onderwerp_en_persoonsvorm(volgend: str) -> bool:
    """Het vervolg (tot het volgende zekere zinsbegin) draagt een persoonsvorm
    die niet vooraan staat.

    Positief bewijs, geen taalgarantie: het vervolg begint met een onderwerp
    (niet met een voorzetsel, voegwoord, betrekkelijk voornaamwoord of 'om'/
    'te') en de eerste persoonsvorm volgt zonder tussenliggende bijzin- of
    infinitiefmarkering. Staat de persoonsvorm vooraan ('voorz. wordt
    ondertekend'), dan kan de tekst vóór de punt het onderwerp of een bijzin
    daarvan zijn: één zin blijft mogelijk. Een ontbrekende persoonsvorm ('zie
    ook', 'controle volgens protocol') bewijst evenmin een zelfstandige zin.
    """
    woorden = _woorden_tot_zeker_zinsbegin(volgend)
    if len(woorden) < 2 or woorden[0] in _PERSOONSVORMEN | _GEEN_ONDERWERPSBEGIN:
        # Persoonsvorm vooraan, of een vervolg dat met een voorzetsel,
        # voegwoord, betrekkelijk voornaamwoord of 'om'/'te' begint: geen
        # onderwerp aan het begin, dus geen bewijs van een zelfstandige zin.
        return False
    for index, woord in enumerate(woorden[1:], start=1):
        if woord in _PERSOONSVORMEN:
            if not _bewezen_persoonsvorm(woorden, index):
                return False
            return _onderwerp_herkend(woorden, index)
        if woord in _BIJZIN_OF_INFINITIEF:
            # 'controle die blijft ...': de persoonsvorm hoort bij een bijzin.
            return False
    return False


def _bewezen_persoonsvorm(woorden: list[str], index: int) -> bool:
    """De eerste werkwoordvorm op `index` bewijst een hoofdzin, alleen als:

    - zij ondubbelzinnig vervoegd is ('worden' kan infinitief zijn);
    - er een aanvulling op volgt (hoofdzinvolgorde; 'controle nodig is' kan
      een bijzinrest zijn);
    - er geen 'te' direct voor staat en de woorden ervoor geen
      werkwoordelijke vorm bevatten ('toegepast', 'uitsluitend').
    Anders blijft de grens onzeker.
    """
    return (
        woorden[index] not in _INFINITIEF_HOMOGRAAF
        and index < len(woorden) - 1
        and woorden[index - 1] != "te"
        and not any(_WERKWOORDELIJKE_VORM.match(w) for w in woorden[:index])
    )


def _onderwerp_herkend(woorden: list[str], index: int) -> bool:
    """Positieve herkenning van het onderwerp vóór de persoonsvorm op `index`.

    Twee patronen, beide één zinsdeel op de eerste plaats (hoofdzinvolgorde):

    - een lidwoordgroep: lidwoord of aanwijzend woord plus ten minste één
      woord ('de controle blijft …', 'het toezicht is …');
    - één woord met een eigen voorzetselgroep ('controle volgens zqv. blijft
      …', 'toezicht op naleving is …'): een bijwoord vormt met een
      voorzetselgroep geen enkel zinsdeel, dus het woord is de kern van een
      naamwoordgroep. Dit geldt onder de aanname van een correcte zin.

    Een kaal woord direct vóór de persoonsvorm ('opnieuw wordt …', 'toezicht
    is …') is niet positief te herkennen: onzeker.
    """
    if woorden[0] in _ONDERWERP_LIDWOORDEN and index >= 2:
        return True
    if woorden[1] not in _VOORZETSELS:
        return False
    # Voorzetsel direct na het woord, met een eigen woord als voorwerp.
    functiewoord = _VOORZETSELS | _LIDWOORDEN
    return any(woord not in functiewoord for woord in woorden[2:index])


def _korte_slotgroep(woorden: list[str]) -> bool:
    """Voorzetsel plus één woord, of voorzetsel, lidwoord en één woord; een
    onvolledige groep ('op', 'op de') bewijst niets."""
    if not woorden or woorden[0] not in _VOORZETSELS:
        return False
    slot = woorden[-1] not in _VOORZETSELS | _LIDWOORDEN
    if len(woorden) == 2:
        return slot
    return len(woorden) == 3 and woorden[1] in _LIDWOORDEN and slot


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
