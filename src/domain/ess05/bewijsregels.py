"""ESS-05 — beperkte bewijsregels `ess05-bewijsregels/6` (DEF-768).

Contract: `docs/technisch/ess05-bewijsregels-contract-v6.md` (delta op v5). Pure domeinlogica,
zonder AI-client, Streamlit of database.

Het model interpreteert bronnen tot getypeerde feiten (`ess05-interpretatie/3`);
deze module doet de rest, in twee strikt gescheiden fasen:

1. **Geldigheid** (`valideer_interpretatie`): schema, bewijs per onderwerp via
   door de app genummerde eenheden (zinnen, `Vergelijkingsinvoer.eenheden`;
   hergebruik over antwoorden mag), een negatief anker (in een bron met meer
   begrippen is een eenheid die alleen een ander begrip noemt geen bewijs; geen
   bewijs van inhoudelijke betrekking), context, de door de app bepaalde bewijsdoelen, tekstdekking van
   de kern, consistentie van buurgroepen, ondersteund bereik (een
   voorwaardelijke doeleis is `buiten_bereik`) en dekking van
   `onbesproken`. Elke afwijking is een `BewijsregelfoutError` → `error`, vóór
   iedere inhoudelijke uitkomst.
2. **Regels** (`pas_regels_toe`), alleen op een geldige interpretatie: per
   groep (hele buur of beschreven deelgroep) bewezen binnen de kern, bewezen
   buiten de doelbetekenis, afgegrensd of gedeeld; `fail` alleen met een
   beschreven tegengeval, nooit uit een onbekend of conflicterend kenmerk.

`controle_eenheden` bouwt per onderwerp één lokaal controlepakket uit vaste
sjablonen (broninterpretatie, geen volledigheids- of afgrenzingscertificaat);
positieve feiten gelden als bepaling binnen het volledige gebonden materiaal en
de vastgelegde context, niet daarbuiten;
`render` drukt alleen het regelresultaat uit.

Grens: tekstdekking is een tekstcontrole, geen bewijs dat de kenmerken het
fragment volledig of juist weergeven; dat blijft een gecontroleerde
modelinterpretatie (contract §7). Geen appgarantie.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from domain.ess05.bewijs import _BRONPREFIX, _BUURPREFIX, _DEFINITIE, _treffers
from domain.ess05.lokale_controle import (
    Citaatverwijzing,
    Lokaalpakket,
    bouw_materiaalpakket,
)

__all__ = [
    "BEREIKZIN",
    "BEWIJSREGELVERSIE",
    "DOEL",
    "INTERPRETATIESCHEMA",
    "RENDERVERSIE",
    "Aspect",
    "BewijsregelfoutError",
    "Buuroordeel",
    "Controle_eenheid",
    "Groepsoordeel",
    "Interpretatie",
    "Regelfout",
    "Regeluitkomst",
    "Vergelijkingsinvoer",
    "bepaal",
    "controle_eenheden",
    "pas_regels_toe",
    "regelcontract",
    "render",
    "valideer_interpretatie",
    "zinnen",
]

BEWIJSREGELVERSIE = "ess05-bewijsregels/6"
INTERPRETATIESCHEMA = "ess05-interpretatie/3"
RENDERVERSIE = "ess05-bewijsregels-render/2"
DOEL = "doel"
BEREIKZIN = (
    "Bereik: beperkte bewijsregels over het aangeleverde, gebonden materiaal; geen "
    "volledige ESS-05-beoordeling van de app."
)

_BEVESTIGD, _ONTKEND, _ONBESPROKEN = "bevestigd", "ontkend", "onbesproken"
_GEMENGD, _DEELS, _CONFLICT = "gemengd", "deels", "conflict"
_BASIS = (_BEVESTIGD, _ONTKEND, _ONBESPROKEN)
_BUURNIVEAU = (*_BASIS, _GEMENGD, _DEELS)
_ENIG = frozenset({_ONBESPROKEN, _GEMENGD, _DEELS})
_CONTEXTEN = ("algemeen", "zaakcontext", "andere")
_BETEKENIS = "meaning"
_CONTEXTMATERIAAL = "context"
#: Woorden die buiten een kerncitaat mogen vallen (alleen nevenschikking).
_VRIJE_WOORDEN = frozenset({"en"})
_WOORD = re.compile(r"\w+")
#: v6: een zin loopt tot en met . ! ? gevolgd door witruimte, of tot het einde.
_ZIN = re.compile(r"\S.*?(?:[.!?](?=\s)|\Z)", re.DOTALL)
#: v6: materiaal zonder bewijseenheden (de kern citeert de definitie letterlijk;
#: context is nooit bewijs voor een antwoord).
_ZONDER_EENHEDEN = frozenset({_DEFINITIE, _CONTEXTMATERIAAL})


def zinnen(tekst: str) -> tuple[tuple[int, int], ...]:
    """Halfopen bereiken van de zinnen in `tekst`, zonder omringende witruimte.

    Grens: '.', '!' of '?' gevolgd door witruimte. Afkortingen als 'bijv. een'
    splitsen dus ook; dat maakt een eenheid korter, nooit onvindbaar.
    """
    return tuple(
        (m.start(), m.start() + len(m.group().rstrip())) for m in _ZIN.finditer(tekst)
    )


_VELDEN = frozenset(
    {
        "schema_version",
        "kern",
        "buiten_kern",
        "buurgroepen",
        "buiten_bereik",
        "antwoorden",
    }
)
_KERNVELDEN = frozenset({"bovenbegrip", "kenmerken"})
_KENMERKVELDEN = frozenset({"id", "kenmerk", "waarde", "citaat"})
_BETEKENISVELDEN = frozenset({"id", "kenmerk", "waarde"})
_GROEPVELDEN = frozenset({"id", "buur", "omschrijving", "citaten"})
_BEREIKVELDEN = frozenset({"citaat", "reden"})
_ANTWOORDVELDEN = frozenset(
    {"kenmerk_id", "onderwerp", "toestand", "voorwaarden", "context", "citaten"}
)


def regelcontract() -> dict[str, str]:
    """De versies die een proef of freeze aan deze module bindt."""
    return {
        "bewijsregel_version": BEWIJSREGELVERSIE,
        "interpretation_schema_version": INTERPRETATIESCHEMA,
        "render_version": RENDERVERSIE,
    }


class BewijsregelfoutError(ValueError):
    """Een ongeldige interpretatie: altijd `error`, nooit een inhoudelijk oordeel."""

    def __init__(self, soort: str, melding: str) -> None:
        super().__init__(f"{soort}: {melding}")
        self.soort = soort
        self.melding = melding


# --- invoer en getypeerde feiten ------------------------------------------------------------


@dataclass(frozen=True)
class Vergelijkingsinvoer:
    """Gebonden materiaal, door de app bevestigde buren en onvolledig gebonden materiaal."""

    term: str
    materiaal: Mapping[str, str]
    buren: tuple[tuple[str, str], ...]
    onvolledig: frozenset[str] = field(default_factory=frozenset)

    def termen(self) -> dict[str, str]:
        return dict(self.buren)

    def eenheden(self) -> dict[str, Citaatverwijzing]:
        """Genummerde bewijseenheden (U1, U2, …): elke zin van elk materiaal
        behalve definitie en context, in de volgorde van de prompt (gesorteerd
        materiaal-ID). Prompt en geldigheidscontrole gebruiken deze ene bron."""
        uit: dict[str, Citaatverwijzing] = {}
        for mid in sorted(self.materiaal):
            if mid in _ZONDER_EENHEDEN:
                continue
            for start, end in zinnen(self.materiaal[mid]):
                uit[f"U{len(uit) + 1}"] = Citaatverwijzing(mid, start, end)
        return uit

    def relevant(self, buur: str | None) -> tuple[str, ...]:
        """Relevant materiaal: doel = betekenis + bronnen; buur = eigen beschrijving erbij."""
        bronnen = sorted(m for m in self.materiaal if m.startswith(_BRONPREFIX))
        betekenis = [_BETEKENIS] if _BETEKENIS in self.materiaal else []
        if buur is None:
            return (*betekenis, *bronnen)
        eigen = f"{_BUURPREFIX}{buur}"
        return (*([eigen] if eigen in self.materiaal else []), *betekenis, *bronnen)


@dataclass(frozen=True)
class Kenmerk:
    id: str
    kenmerk: str
    waarde: str
    citaat: str | None
    in_kern: bool


@dataclass(frozen=True)
class Buurgroep:
    id: str
    buur: str
    omschrijving: str
    citaten: tuple[Citaatverwijzing, ...]


@dataclass(frozen=True)
class Antwoord:
    kenmerk_id: str
    onderwerp: str
    toestand: str
    voorwaarden: tuple[str, ...]
    context: str
    citaten: tuple[Citaatverwijzing, ...]


@dataclass(frozen=True)
class Interpretatie:
    """Een geldige interpretatie: alle geldigheidscontroles doorstaan."""

    invoer: Vergelijkingsinvoer
    bovenbegrip: str
    kenmerken: tuple[Kenmerk, ...]
    groepen: tuple[Buurgroep, ...]
    antwoorden: tuple[Antwoord, ...]
    buiten_bereik: tuple[str, ...] = ()

    @property
    def kern(self) -> tuple[Kenmerk, ...]:
        return tuple(k for k in self.kenmerken if k.in_kern)

    def antwoorden_voor(self, kenmerk_id: str, onderwerp: str) -> tuple[Antwoord, ...]:
        return tuple(
            a
            for a in self.antwoorden
            if a.kenmerk_id == kenmerk_id and a.onderwerp == onderwerp
        )

    def groepen_van(self, buur: str) -> tuple[Buurgroep, ...]:
        return tuple(g for g in self.groepen if g.buur == buur)

    def buur_van(self, onderwerp: str) -> str | None:
        """None voor het doel; anders de buur van dit onderwerp (buur of deelgroep)."""
        if onderwerp == DOEL:
            return None
        groep = next((g for g in self.groepen if g.id == onderwerp), None)
        return groep.buur if groep is not None else onderwerp


# --- fase 1: geldigheid ---------------------------------------------------------------------


def _fout(soort: str, melding: str) -> BewijsregelfoutError:
    return BewijsregelfoutError(soort, melding)


def _velden(item: Any, velden: frozenset[str], pad: str) -> Mapping[str, Any]:
    if not isinstance(item, Mapping):
        raise _fout("schemafout", f"{pad} is geen object")
    anders = sorted(set(item) ^ velden)
    if anders:
        raise _fout("schemafout", f"{pad}: onbekende of ontbrekende velden {anders}")
    return item


def _lijst(waarde: Any, pad: str) -> list[Any]:
    if not isinstance(waarde, list):
        raise _fout("schemafout", f"{pad} is geen lijst")
    return waarde


def _tekstveld(waarde: Any, pad: str) -> str:
    if not isinstance(waarde, str) or not waarde.strip():
        raise _fout("schemafout", f"{pad} is geen niet-lege tekst")
    return waarde


def _plaats(
    materiaal: Mapping[str, str], material_id: str, citaat: str, pad: str
) -> Citaatverwijzing:
    tekst = materiaal.get(material_id)
    if tekst is None:
        raise _fout("citaatfout", f"{pad}: onbekend materiaal {material_id!r}")
    treffers = _treffers(tekst, citaat)
    if len(treffers) != 1:
        raise _fout(
            "citaatfout",
            f"{pad}: citaat {citaat[:80]!r} staat {len(treffers)} keer letterlijk in "
            f"{material_id!r} (precies één vereist)",
        )
    return Citaatverwijzing(material_id, treffers[0], treffers[0] + len(citaat))


def _noemt(tekst: str, term: str) -> bool:
    """Het begrip staat als heel woord in de tekst, hoofdletterongevoelig."""
    patroon = rf"(?<!\w){re.escape(term)}(?!\w)"
    return re.search(patroon, tekst, re.IGNORECASE) is not None


def _onderwerpbinding(
    invoer: Vergelijkingsinvoer, ref: Citaatverwijzing, term: str, pad: str
) -> None:
    """Negatief anker (contract v6): noemt een bron meer dan één geregistreerd
    begrip, dan is een eenheid die een ander begrip noemt en het eigen onderwerp
    niet, geen bewijs voor dat onderwerp. Een eenheid zonder begripsnaam of met
    beide namen gaat door; inhoudelijke betrekking toetst de semantische
    controle."""
    if not ref.material_id.startswith(_BRONPREFIX):
        return
    bron = invoer.materiaal[ref.material_id]
    termen = list(dict.fromkeys([invoer.term, *(t for _, t in invoer.buren)]))
    if sum(_noemt(bron, t) for t in termen) < 2:
        return
    eenheid = bron[ref.start : ref.end]
    anderen = [t for t in termen if t != term and _noemt(eenheid, t)]
    if anderen and not _noemt(eenheid, term):
        raise _fout(
            "onderwerpfout",
            f"{pad}: de eenheid noemt {anderen} en niet {term!r}; zij is geen bewijs "
            f"voor {term!r} (eenheid {eenheid[:80]!r})",
        )


def _citaten(
    invoer: Vergelijkingsinvoer,
    ruw: Any,
    toegestaan: Sequence[str],
    pad: str,
    term: str,
) -> tuple[Citaatverwijzing, ...]:
    """v6: bewijs is een lijst eenheidsnummers; hergebruik over antwoorden mag."""
    eenheden = invoer.eenheden()
    refs: list[Citaatverwijzing] = []
    for nummer, uid in enumerate(_lijst(ruw, pad), start=1):
        if not isinstance(uid, str) or uid not in eenheden:
            raise _fout("citaatfout", f"{pad}[{nummer}]: onbekende eenheid {uid!r}")
        ref = eenheden[uid]
        if ref.material_id not in toegestaan:
            raise _fout(
                "onderwerpfout",
                f"{pad}[{nummer}]: {uid} uit {ref.material_id!r} hoort niet bij dit "
                f"onderwerp (toegestaan: {list(toegestaan)})",
            )
        _onderwerpbinding(invoer, ref, term, f"{pad}[{nummer}] ({uid})")
        if ref not in refs:
            refs.append(ref)
    return tuple(refs)


def _uniek(ids: Iterable[str], pad: str) -> None:
    lijst = list(ids)
    if len(set(lijst)) != len(lijst):
        raise _fout("schemafout", f"{pad}: dubbele ID's {lijst}")


def _kern(ruw: Any, invoer: Vergelijkingsinvoer) -> tuple[str, list[Kenmerk]]:
    kern = _velden(ruw, _KERNVELDEN, "kern")
    definitie = invoer.materiaal.get(_DEFINITIE)
    if not definitie:
        raise _fout("schemafout", "de invoer heeft geen definitie")
    bovenbegrip = _tekstveld(kern["bovenbegrip"], "kern.bovenbegrip")
    spannen = [_plaats(invoer.materiaal, _DEFINITIE, bovenbegrip, "kern.bovenbegrip")]
    kenmerken = []
    for nummer, item in enumerate(_lijst(kern["kenmerken"], "kern.kenmerken"), start=1):
        pad = f"kern.kenmerken[{nummer}]"
        k = _velden(item, _KENMERKVELDEN, pad)
        kid = _tekstveld(k["id"], f"{pad}.id")
        if not re.fullmatch(r"K\d+", kid):
            raise _fout("schemafout", f"{pad}: id {kid!r} is geen K-nummer")
        citaat = _tekstveld(k["citaat"], f"{pad}.citaat")
        spannen.append(_plaats(invoer.materiaal, _DEFINITIE, citaat, pad))
        kenmerken.append(
            Kenmerk(
                kid,
                _tekstveld(k["kenmerk"], f"{pad}.kenmerk"),
                _tekstveld(k["waarde"], f"{pad}.waarde"),
                citaat,
                True,
            )
        )
    # Tekstdekking: elk woord van de volledige definitie valt in een citaat.
    # Alleen een tekstcontrole; zij bewijst geen juiste of volledige typering.
    los = [
        w.group()
        for w in _WOORD.finditer(definitie)
        if w.group().casefold() not in _VRIJE_WOORDEN
        and not any(s.start <= w.start() and w.end() <= s.end for s in spannen)
    ]
    if los:
        raise _fout(
            "kerndekking_onvolledig",
            "niet door een citaat gedekte woorden van de definitie: "
            + ", ".join(repr(w) for w in los),
        )
    return bovenbegrip, kenmerken


def _buiten_kern(ruw: Any) -> list[Kenmerk]:
    uit = []
    for nummer, item in enumerate(_lijst(ruw, "buiten_kern"), start=1):
        pad = f"buiten_kern[{nummer}]"
        m = _velden(item, _BETEKENISVELDEN, pad)
        mid = _tekstveld(m["id"], f"{pad}.id")
        if not re.fullmatch(r"M\d+", mid):
            raise _fout("schemafout", f"{pad}: id {mid!r} is geen M-nummer")
        uit.append(
            Kenmerk(
                mid,
                _tekstveld(m["kenmerk"], f"{pad}.kenmerk"),
                _tekstveld(m["waarde"], f"{pad}.waarde"),
                None,
                False,
            )
        )
    return uit


def _groepen(ruw: Any, invoer: Vergelijkingsinvoer) -> list[Buurgroep]:
    termen = invoer.termen()
    uit = []
    for nummer, item in enumerate(_lijst(ruw, "buurgroepen"), start=1):
        pad = f"buurgroepen[{nummer}]"
        g = _velden(item, _GROEPVELDEN, pad)
        gid = _tekstveld(g["id"], f"{pad}.id")
        if not re.fullmatch(r"G\d+", gid):
            raise _fout("schemafout", f"{pad}: id {gid!r} is geen G-nummer")
        buur = g["buur"]
        if buur not in termen:
            raise _fout("schemafout", f"{pad}: onbekende buur {buur!r}")
        if not g["citaten"]:
            raise _fout("schemafout", f"{pad}: een deelgroep vraagt een eigen citaat")
        uit.append(
            Buurgroep(
                gid,
                buur,
                _tekstveld(g["omschrijving"], f"{pad}.omschrijving"),
                _citaten(
                    invoer,
                    g["citaten"],
                    invoer.relevant(buur),
                    f"{pad}.citaten",
                    termen[buur],
                ),
            )
        )
    return uit


def _buiten_bereik(ruw: Any, invoer: Vergelijkingsinvoer) -> list[str]:
    uit = []
    for nummer, item in enumerate(_lijst(ruw, "buiten_bereik"), start=1):
        pad = f"buiten_bereik[{nummer}]"
        b = _velden(item, _BEREIKVELDEN, pad)
        citaat = _tekstveld(b["citaat"], f"{pad}.citaat")
        if not any(citaat in tekst for tekst in invoer.materiaal.values()):
            raise _fout("citaatfout", f"{pad}: citaat {citaat[:80]!r} staat nergens")
        uit.append(f"{citaat!r}: {_tekstveld(b['reden'], f'{pad}.reden')}")
    return uit


def _antwoord(
    item: Any,
    nummer: int,
    invoer: Vergelijkingsinvoer,
    kenmerken: Mapping[str, Kenmerk],
    buur_van: Mapping[str, str | None],
) -> Antwoord:
    pad = f"antwoorden[{nummer}]"
    a = _velden(item, _ANTWOORDVELDEN, pad)
    kid, onderwerp, toestand = a["kenmerk_id"], a["onderwerp"], a["toestand"]
    if kid not in kenmerken:
        raise _fout("schemafout", f"{pad}: onbekend kenmerk {kid!r}")
    if onderwerp not in buur_van:
        raise _fout("schemafout", f"{pad}: onbekend onderwerp {onderwerp!r}")
    hele_buur = onderwerp in invoer.termen()
    if toestand not in (_BUURNIVEAU if hele_buur else _BASIS):
        raise _fout(
            "schemafout",
            f"{pad}: toestand {toestand!r} is niet toegestaan voor {onderwerp!r} "
            "(gemengd/deels alleen voor de hele buur)",
        )
    if a["context"] not in _CONTEXTEN:
        raise _fout("schemafout", f"{pad}: onbekende context {a['context']!r}")
    if a["context"] == "andere":
        raise _fout(
            "contextfout",
            f"{pad}: een feit uit een andere context is niet combineerbaar met deze "
            "vergelijking",
        )
    voorwaarden = tuple(
        _tekstveld(v, f"{pad}.voorwaarden")
        for v in _lijst(a["voorwaarden"], f"{pad}.voorwaarden")
    )
    if voorwaarden and onderwerp != DOEL:
        raise _fout(
            "schemafout",
            f"{pad}: een voorwaarde aan de buurzijde hoort in een eigen deelgroep",
        )
    citaten_ruw = _lijst(a["citaten"], f"{pad}.citaten")
    if toestand == _ONBESPROKEN:
        if citaten_ruw or voorwaarden:
            raise _fout(
                "schemafout",
                f"{pad}: onbesproken draagt geen citaten of voorwaarden; de app bindt "
                "zelf het volledige relevante materiaal",
            )
        citaten: tuple[Citaatverwijzing, ...] = ()
    else:
        if not citaten_ruw:
            raise _fout("schemafout", f"{pad}: {toestand} vraagt minstens één citaat")
        buur = buur_van[onderwerp]
        citaten = _citaten(
            invoer,
            citaten_ruw,
            invoer.relevant(buur),
            f"{pad}.citaten",
            invoer.term if buur is None else invoer.termen()[buur],
        )
    return Antwoord(kid, onderwerp, toestand, voorwaarden, a["context"], citaten)


def _toestand(antwoorden: Sequence[Antwoord]) -> str:
    soorten = {a.toestand for a in antwoorden}
    if soorten == {_BEVESTIGD, _ONTKEND}:
        return _CONFLICT
    (soort,) = soorten
    return soort


def _vereist(antwoorden: Sequence[Antwoord]) -> bool:
    """Doelbetekenis vereist het kenmerk: onvoorwaardelijk bevestigd, geen conflict."""
    return _toestand(antwoorden) == _BEVESTIGD and any(
        not a.voorwaarden for a in antwoorden
    )


def _onverwerkte_voorwaarden(interpretatie: Interpretatie) -> list[str]:
    """Voorwaardelijke doeleisen die deze proef niet verwerkt (K4-rest, v3).

    Verwerkt is een voorwaardelijk doelantwoord alleen als hetzelfde kenmerk ook
    onvoorwaardelijk dezelfde toestand heeft: dan voegt de voorwaarde niets toe.
    Elke andere wordt met tekst en citaten teruggegeven, niet weggegooid.
    """
    per_id = {k.id: k for k in interpretatie.kenmerken}
    materiaal = interpretatie.invoer.materiaal
    onverwerkt = []
    for a in interpretatie.antwoorden:
        if a.onderwerp != DOEL or not a.voorwaarden:
            continue
        if any(
            b.toestand == a.toestand and not b.voorwaarden
            for b in interpretatie.antwoorden_voor(a.kenmerk_id, DOEL)
        ):
            continue
        k = per_id[a.kenmerk_id]
        citaten = ", ".join(
            f"{c.material_id}: «{materiaal[c.material_id][c.start : c.end]}»"
            for c in a.citaten
        )
        onverwerkt.append(
            f"{k.id} ({k.kenmerk}: {k.waarde}) is in de doelbetekenis {a.toestand} alleen "
            f"onder de voorwaarde {' en '.join(a.voorwaarden)} [{citaten}]; voorwaardelijke "
            "doeleisen worden in deze proef niet verwerkt"
        )
    return onverwerkt


def _controleer_samenhang(interpretatie: Interpretatie) -> None:
    invoer = interpretatie.invoer
    kenmerken = interpretatie.kenmerken
    # Betekeniskenmerken moeten door de doelbetekenis gedragen zijn.
    for m in (k for k in kenmerken if not k.in_kern):
        if _toestand(interpretatie.antwoorden_voor(m.id, DOEL)) != _BEVESTIGD:
            raise _fout(
                "betekenisfout",
                f"{m.id} ({m.kenmerk}: {m.waarde}) is als betekeniskenmerk opgegeven "
                "zonder bevestiging in de doelbetekenis",
            )
    buiten = [*interpretatie.buiten_bereik, *_onverwerkte_voorwaarden(interpretatie)]
    if buiten:
        raise _fout("buiten_bereik", "; ".join(buiten))
    for buur, term in invoer.buren:
        gemengd = [
            k.id
            for k in kenmerken
            if _toestand(interpretatie.antwoorden_voor(k.id, buur)) == _GEMENGD
        ]
        if len(gemengd) > 1:
            raise _fout(
                "buiten_bereik",
                f"{term}: meer dan één gemengd kenmerk ({gemengd}); combinaties van "
                "variaties worden niet ondersteund",
            )
    # Deelgroepen moeten passen bij de toestand van de hele buur.
    for buur, term in invoer.buren:
        groepen = interpretatie.groepen_van(buur)
        for k in kenmerken:
            geheel = _toestand(interpretatie.antwoorden_voor(k.id, buur))
            delen = [
                _toestand(interpretatie.antwoorden_voor(k.id, g.id)) for g in groepen
            ]
            if geheel in _BASIS:
                fout = any(d != geheel for d in delen)
            elif geheel == _GEMENGD:
                fout = not ({_BEVESTIGD, _ONTKEND} <= set(delen))
            elif geheel == _DEELS:
                fout = not ({_BEVESTIGD, _ONTKEND} & set(delen))
            else:
                fout = False
            if fout:
                raise _fout(
                    "inconsistent",
                    f"{term}/{k.id}: de deelgroepen ({delen}) passen niet bij de "
                    f"toestand {geheel!r} van de hele buur",
                )
    # Onbesproken (of deels) over onvolledig gebonden materiaal bewijst niets.
    for a in interpretatie.antwoorden:
        if a.toestand not in (_ONBESPROKEN, _DEELS):
            continue
        onvolledig = sorted(
            set(invoer.relevant(interpretatie.buur_van(a.onderwerp)))
            & invoer.onvolledig
        )
        if onvolledig:
            raise _fout(
                "dekking_ontbreekt",
                f"{a.kenmerk_id}/{a.onderwerp}: {a.toestand} over onvolledig gebonden "
                f"materiaal {onvolledig}; een informatiegebrek is niet vastgesteld",
            )


def valideer_interpretatie(ruw: Any, invoer: Vergelijkingsinvoer) -> Interpretatie:
    """Alle geldigheids-, dekkings- en bereikcontroles; een fout is altijd `error`."""
    data = _velden(ruw, _VELDEN, "interpretatie")
    if data["schema_version"] != INTERPRETATIESCHEMA:
        raise _fout("schemafout", f"schema_version moet {INTERPRETATIESCHEMA!r} zijn")
    bovenbegrip, kern = _kern(data["kern"], invoer)
    kenmerken = [*kern, *_buiten_kern(data["buiten_kern"])]
    _uniek((k.id for k in kenmerken), "kenmerken")
    _uniek((k.kenmerk.casefold() for k in kenmerken), "kenmerklabels")
    groepen = _groepen(data["buurgroepen"], invoer)
    _uniek((g.id for g in groepen), "buurgroepen")
    buiten = _buiten_bereik(data["buiten_bereik"], invoer)
    per_id = {k.id: k for k in kenmerken}
    buur_van: dict[str, str | None] = {DOEL: None}
    buur_van.update({b: b for b, _ in invoer.buren})
    buur_van.update({g.id: g.buur for g in groepen})
    antwoorden = [
        _antwoord(item, nummer, invoer, per_id, buur_van)
        for nummer, item in enumerate(_lijst(data["antwoorden"], "antwoorden"), start=1)
    ]
    # De app bepaalt de bewijsdoelen: elk kenmerk × doel, elke buur, elke deelgroep.
    ontbrekend = []
    for k in kenmerken:
        for onderwerp in buur_van:
            gevonden = [
                a
                for a in antwoorden
                if (a.kenmerk_id, a.onderwerp) == (k.id, onderwerp)
            ]
            if not gevonden:
                ontbrekend.append(f"{k.id}/{onderwerp}")
            elif len(gevonden) > 1 and {a.toestand for a in gevonden} & _ENIG:
                raise _fout(
                    "schemafout",
                    f"{k.id}/{onderwerp}: onbesproken, gemengd of deels is het enige "
                    "antwoord voor een bewijsdoel",
                )
    if ontbrekend:
        raise _fout(
            "doeldekking_onvolledig",
            f"verplichte bewijsdoelen zonder antwoord: {', '.join(ontbrekend)}",
        )
    interpretatie = Interpretatie(
        invoer,
        bovenbegrip,
        tuple(kenmerken),
        tuple(groepen),
        tuple(antwoorden),
        tuple(buiten),
    )
    _controleer_samenhang(interpretatie)
    return interpretatie


# --- fase 2: regels (alleen op een geldige interpretatie) -----------------------------------


@dataclass(frozen=True)
class Regelfout:
    soort: str
    melding: str


@dataclass(frozen=True)
class Aspect:
    """Eén kenmerk tegenover de hele buur."""

    kenmerk_id: str
    kenmerk: str
    waarde: str
    in_kern: bool
    aspect: str
    reden: str | None


@dataclass(frozen=True)
class Groepsoordeel:
    """`tegengeval`, `afgegrensd`, `gedeeld` of `onbeslist`, met de dragende kenmerken."""

    id: str
    omschrijving: str
    oordeel: str
    kenmerken: tuple[str, ...]


@dataclass(frozen=True)
class Buuroordeel:
    buur_id: str
    term: str
    oordeel: str
    overlap: bool
    aspecten: tuple[Aspect, ...]
    groepen: tuple[Groepsoordeel, ...]


@dataclass(frozen=True)
class Regeluitkomst:
    uitkomst: str
    fout: Regelfout | None
    term: str
    buren: tuple[Buuroordeel, ...] = ()
    kern_zonder_kenmerk: bool = False
    kenmerken: tuple[Kenmerk, ...] = ()


def _aspect(k: Kenmerk, vereist: bool, geheel: str) -> Aspect:
    if geheel == _ONTKEND and vereist:
        soort, reden = ("afgrenzend" if k.in_kern else "buiten_doel"), None
    elif geheel == _BEVESTIGD:
        soort, reden = "gedeeld", None
    else:
        soort = "onbeslist"
        reden = {
            _ONBESPROKEN: "onbekend",
            _CONFLICT: "conflict",
            _GEMENGD: "gemengd",
            _DEELS: "deels",
            _ONTKEND: "doelbetekenis_niet_vastgesteld",
        }[geheel]
    return Aspect(k.id, k.kenmerk, k.waarde, k.in_kern, soort, reden)


def _groepsoordeel(
    interpretatie: Interpretatie,
    onderwerp: str,
    omschrijving: str,
    vereist: Mapping[str, bool],
) -> Groepsoordeel:
    s = {
        k.id: _toestand(interpretatie.antwoorden_voor(k.id, onderwerp))
        for k in interpretatie.kenmerken
    }
    kern = interpretatie.kern
    binnen_kern = bool(kern) and all(s[k.id] == _BEVESTIGD for k in kern)
    buiten_doel = [f for f, v in vereist.items() if v and s[f] == _ONTKEND]
    afgrenzend = [k.id for k in kern if vereist[k.id] and s[k.id] == _ONTKEND]
    if binnen_kern and buiten_doel:
        return Groepsoordeel(onderwerp, omschrijving, "tegengeval", tuple(buiten_doel))
    if afgrenzend:
        return Groepsoordeel(onderwerp, omschrijving, "afgegrensd", tuple(afgrenzend))
    if binnen_kern and all(s[f] == _BEVESTIGD for f, v in vereist.items() if v):
        return Groepsoordeel(onderwerp, omschrijving, "gedeeld", ())
    return Groepsoordeel(onderwerp, omschrijving, "onbeslist", ())


def _buuroordeel(
    interpretatie: Interpretatie, buur: str, term: str, vereist: Mapping[str, bool]
) -> Buuroordeel:
    staat = {
        k.id: _toestand(interpretatie.antwoorden_voor(k.id, buur))
        for k in interpretatie.kenmerken
    }
    aspecten = tuple(
        _aspect(k, vereist[k.id], staat[k.id]) for k in interpretatie.kenmerken
    )
    geheel = _groepsoordeel(interpretatie, buur, f"elk geval van {term}", vereist)
    delen = tuple(
        _groepsoordeel(interpretatie, g.id, g.omschrijving, vereist)
        for g in interpretatie.groepen_van(buur)
    )
    groepen = (geheel, *delen)
    if any(g.oordeel == "tegengeval" for g in groepen):
        return Buuroordeel(buur, term, "niet_onderscheiden", False, aspecten, groepen)
    if geheel.oordeel == "afgegrensd":
        return Buuroordeel(buur, term, "onderscheiden", False, aspecten, groepen)
    # Splitsing: precies één niet-uniform kenmerk, een gemengd vereist kernkenmerk;
    # de deelgroepen dekken dan elk buurgeval (wel of niet dat kenmerk).
    niet_uniform = [f for f, t in staat.items() if t not in _BASIS]
    kern_ids = {k.id for k in interpretatie.kern}
    if (
        delen
        and len(niet_uniform) == 1
        and niet_uniform[0] in kern_ids
        and staat[niet_uniform[0]] == _GEMENGD
        and vereist[niet_uniform[0]]
        and all(g.oordeel in ("afgegrensd", "gedeeld") for g in delen)
    ):
        overlap = any(g.oordeel == "gedeeld" for g in delen)
        return Buuroordeel(buur, term, "onderscheiden", overlap, aspecten, groepen)
    return Buuroordeel(buur, term, "open", False, aspecten, groepen)


def pas_regels_toe(interpretatie: Interpretatie) -> Regeluitkomst:
    """Afleiding op een geldige interpretatie: fail vóór open, pass alleen bewezen."""
    invoer = interpretatie.invoer
    if not interpretatie.kern:
        return Regeluitkomst(
            "fail", None, invoer.term, kern_zonder_kenmerk=True,
            kenmerken=interpretatie.kenmerken,
        )  # fmt: skip
    vereist = {
        k.id: _vereist(interpretatie.antwoorden_voor(k.id, DOEL))
        for k in interpretatie.kenmerken
    }
    buren = tuple(
        _buuroordeel(interpretatie, buur, term, vereist) for buur, term in invoer.buren
    )
    oordelen = {b.oordeel for b in buren}
    if "niet_onderscheiden" in oordelen:
        uitkomst = "fail"
    elif "open" in oordelen or not buren:
        uitkomst = "review_required"
    else:
        uitkomst = "pass"
    return Regeluitkomst(
        uitkomst, None, invoer.term, buren, kenmerken=interpretatie.kenmerken
    )


def bepaal(ruw: Any, invoer: Vergelijkingsinvoer) -> Regeluitkomst:
    """Geldigheid, dan regels; een geldigheidsfout wordt `error` vóór alle inhoud."""
    try:
        interpretatie = valideer_interpretatie(ruw, invoer)
    except BewijsregelfoutError as exc:
        return Regeluitkomst("error", Regelfout(exc.soort, exc.melding), invoer.term)
    return pas_regels_toe(interpretatie)


# --- controle van de interpretatie ----------------------------------------------------------


@dataclass(frozen=True)
class Controle_eenheid:  # noqa: N801 - naam volgt het contract
    naam: str
    pakket: Lokaalpakket


class _Route:
    """Citaten in volgorde van eerste gebruik; elk feit noemt zijn eigen nummers."""

    def __init__(self) -> None:
        self.refs: list[Citaatverwijzing] = []

    def cite(self, refs: Iterable[Citaatverwijzing]) -> str:
        nummers = []
        for ref in refs:
            if ref not in self.refs:
                self.refs.append(ref)
            nummers.append(f"B{self.refs.index(ref) + 1}")
        return "(" + ", ".join(dict.fromkeys(nummers)) + ")"


def _volledig(
    invoer: Vergelijkingsinvoer, ids: Iterable[str]
) -> list[Citaatverwijzing]:
    return [Citaatverwijzing(m, 0, len(invoer.materiaal[m])) for m in ids]


def _feitzin(
    route: _Route,
    interpretatie: Interpretatie,
    k: Kenmerk,
    a: Antwoord,
    label: str,
    buurterm: str | None,
) -> str | None:
    invoer = interpretatie.invoer
    kenmerk = f"{k.kenmerk}: {k.waarde}"
    if a.toestand == _ONBESPROKEN:
        bereik = invoer.relevant(interpretatie.buur_van(a.onderwerp))
        if not bereik:
            return None  # geen materiaal: door de app vastgesteld, niets te controleren
        cite = route.cite(_volledig(invoer, bereik))
        return f"het volledige geciteerde materiaal {cite} zegt over {label} niets over {kenmerk} of het tegendeel"
    cite = route.cite(a.citaten)
    if a.toestand == _GEMENGD:
        return (
            f"onder {buurterm} vallen zowel gevallen waarvoor {kenmerk} geldt als "
            f"gevallen waarvoor het niet geldt {cite}"
        )
    if a.toestand == _DEELS:
        return (
            f"alleen voor een deel van de gevallen van {buurterm} zegt het materiaal "
            f"of {kenmerk} geldt {cite}"
        )
    ontkenning = " niet" if a.toestand == _ONTKEND else ""
    voorwaarde = (
        f", alleen onder de voorwaarde {' en '.join(a.voorwaarden)}"
        if a.voorwaarden
        else ""
    )
    return f"voor {label} geldt {kenmerk}{ontkenning}{voorwaarde} {cite}"


def _reikwijdte(route: _Route, invoer: Vergelijkingsinvoer, term: str) -> str:
    """Kop bij positieve feiten: een bepaling binnen het gebonden domein (v4 §6).

    Cijfert de volledige tekst van elk gebruikt materiaal plus de vastgelegde
    context, ongeacht het contextveld van het model; claimt niets daarbuiten.
    """
    ids = list(dict.fromkeys(r.material_id for r in route.refs))
    context = _CONTEXTMATERIAAL in invoer.materiaal
    if context and _CONTEXTMATERIAAL not in ids:
        ids.append(_CONTEXTMATERIAAL)
    domein = " en de vastgelegde context" if context else ""
    return (
        f"Binnen het gebonden materiaal{domein} {route.cite(_volledig(invoer, ids))}, "
        f"niet daarbuiten, is elk feit hieronder over {term} een bepaling in dat "
        "materiaal: geen enkel voorval en geen voorwaardelijke afspraak, tenzij het "
        "feit zijn voorwaarde zelf noemt"
    )


def _eenheid(
    naam: str,
    delen: list[str],
    route: _Route,
    invoer: Vergelijkingsinvoer,
    binding: Mapping[str, Any],
    kopterm: str | None,
) -> Controle_eenheid | None:
    """kopterm: het onderwerp als de eenheid een positief feit draagt, anders None."""
    if not route.refs:
        return None
    kop = f"{_reikwijdte(route, invoer, kopterm)}. " if kopterm else ""
    uitspraak = kop + "Volgens de citaten: " + "; ".join(delen) + "."
    pakket = bouw_materiaalpakket(
        uitspraak,
        route.refs,
        invoer.materiaal,
        buurtermen=invoer.termen(),
        binding={**binding, "eenheid": naam},
    )
    return Controle_eenheid(naam, pakket)


def controle_eenheden(
    interpretatie: Interpretatie, invoer: Vergelijkingsinvoer
) -> list[Controle_eenheid]:
    """Per onderwerp één materiaalclaim uit vaste sjablonen: kern, doel, elke buur.

    De kerncontrole toetst per fragment de typering (met elke beperking,
    ontkenning, voorwaarde en relatie) en per betekeniskenmerk dat de
    definitie het niet uitdrukt; zij certificeert geen volledigheid en geen
    afgrenzing — dat doen de regels.
    """
    binding = {"regelversie": BEWIJSREGELVERSIE}
    definitie = invoer.materiaal[_DEFINITIE]
    kerndelen = [f"'{interpretatie.bovenbegrip}' is het bovenbegrip"]
    kerndelen += [
        f"het deel '{k.citaat}' drukt precies het kenmerk {k.kenmerk}: {k.waarde} uit, "
        "met elke beperking, ontkenning, voorwaarde en relatie die in dat deel staat"
        for k in interpretatie.kern
    ]
    kerndelen += [
        f"de definitie drukt het kenmerk {m.kenmerk}: {m.waarde} niet uit, ook niet "
        "anders geformuleerd"
        for m in interpretatie.kenmerken
        if not m.in_kern
    ]
    kern = bouw_materiaalpakket(
        "In de definitie (B1): " + "; ".join(kerndelen) + ".",
        [Citaatverwijzing(_DEFINITIE, 0, len(definitie))],
        invoer.materiaal,
        binding={**binding, "eenheid": "kern"},
    )
    eenheden = [Controle_eenheid("kern", kern)]
    route, delen, positief = _Route(), [], False
    for k in interpretatie.kenmerken:
        for a in interpretatie.antwoorden_voor(k.id, DOEL):
            positief |= a.toestand != _ONBESPROKEN
            zin = _feitzin(route, interpretatie, k, a, invoer.term, None)
            if zin:
                delen.append(zin)
    kopterm = invoer.term if positief else None
    if (doel := _eenheid("doel", delen, route, invoer, binding, kopterm)) is not None:
        eenheden.append(doel)
    for buur, term in invoer.buren:
        route, delen = _Route(), []
        positief = bool(interpretatie.groepen_van(buur))
        for k in interpretatie.kenmerken:
            for a in interpretatie.antwoorden_voor(k.id, buur):
                positief |= a.toestand != _ONBESPROKEN
                zin = _feitzin(route, interpretatie, k, a, term, term)
                if zin:
                    delen.append(zin)
        for g in interpretatie.groepen_van(buur):
            label = f"de deelgroep '{g.omschrijving}' van {term}"
            delen.append(
                f"het materiaal beschrijft de deelgroep '{g.omschrijving}' van {term} "
                f"{route.cite(g.citaten)}"
            )
            for k in interpretatie.kenmerken:
                for a in interpretatie.antwoorden_voor(k.id, g.id):
                    zin = _feitzin(route, interpretatie, k, a, label, term)
                    if zin:
                        delen.append(zin)
        eenheid = _eenheid(
            f"buur:{buur}", delen, route, invoer, binding, term if positief else None
        )
        if eenheid is not None:
            eenheden.append(eenheid)
    return eenheden


# --- weergave --------------------------------------------------------------------------------


def _aspectzin(a: Aspect, term: str, doelterm: str) -> str:
    kenmerk = f"{a.kenmerk} '{a.waarde}'" + ("" if a.in_kern else " (niet in de kern)")
    if a.aspect == "afgrenzend":
        return f"{kenmerk} in de kern grenst af: volgens het materiaal geldt dit niet voor {term}."
    if a.aspect == "buiten_doel":
        return (
            f"{kenmerk} hoort volgens het materiaal bij {doelterm} maar niet bij {term}; "
            "de kern drukt dit kenmerk niet uit."
        )
    if a.aspect == "gedeeld":
        return f"{kenmerk} geldt volgens het materiaal ook voor {term}; het grenst niet af."
    return {
        "onbekend": (
            f"Of {kenmerk} voor {term} geldt, stelt het aangeleverde materiaal niet vast; "
            "dat is onbekend, geen ontkenning."
        ),
        "conflict": (
            f"Over {kenmerk} bij {term} is het materiaal tegenstrijdig; dat wordt niet "
            "beslist."
        ),
        "gemengd": f"Het materiaal beschrijft gevallen van {term} met en zonder {kenmerk}.",
        "deels": (
            f"Alleen voor een deel van de gevallen van {term} legt het materiaal {kenmerk} "
            "vast; voor de rest is het onbekend, geen ontkenning."
        ),
        "doelbetekenis_niet_vastgesteld": (
            f"Dat {doelterm} {kenmerk} vereist, stelt het aangeleverde materiaal niet "
            "onvoorwaardelijk vast."
        ),
    }[a.reden or ""]


def _groepzin(g: Groepsoordeel, kenmerken: Mapping[str, Kenmerk], doelterm: str) -> str:
    namen = ", ".join(
        f"{kenmerken[f].kenmerk} '{kenmerken[f].waarde}'" for f in g.kenmerken
    )
    if g.oordeel == "tegengeval":
        return (
            f"de kern mist {namen}: deze gevallen hebben alle kernkenmerken, maar volgens "
            f"het materiaal niet {namen}, dat {doelterm} vereist."
        )
    if g.oordeel == "afgegrensd":
        return f"afgegrensd door {namen}."
    if g.oordeel == "gedeeld":
        return "gedeelde gevallen: alle kernkenmerken en de vereiste betekenis gelden."
    return "niet beslist."


def render(uitkomst: Regeluitkomst) -> str:
    """Alleen het regelresultaat, in begrensde zinnen, altijd met de bereikzin."""
    if uitkomst.uitkomst == "error":
        fout = uitkomst.fout
        return (
            f"Geen oordeel ({fout.soort if fout else 'fout'}): "
            f"{fout.melding if fout else ''}. Dit zegt niets over de definitie.\n{BEREIKZIN}"
        )
    if uitkomst.kern_zonder_kenmerk:
        return (
            "Uitkomst: fail — de kern drukt naast het bovenbegrip geen kenmerk uit."
            f"\n{BEREIKZIN}"
        )
    kop = {
        "pass": "Uitkomst: pass — onderscheidend ten opzichte van elk aangeleverd verwant begrip.",
        "fail": "Uitkomst: fail — een beschreven tegengeval blijft binnen de kern.",
        "review_required": (
            "Uitkomst: open — het aangeleverde materiaal draagt het oordeel niet volledig."
        ),
    }[uitkomst.uitkomst]
    per_id = {k.id: k for k in uitkomst.kenmerken}
    regels = [kop]
    for buur in uitkomst.buren:
        regels.append(f"Ten opzichte van {buur.term}:")
        regels += [
            f"- {_aspectzin(a, buur.term, uitkomst.term)}" for a in buur.aspecten
        ]
        for g in buur.groepen:
            if g.id == buur.buur_id:
                continue
            regels.append(
                f"- Deelgroep '{g.omschrijving}': {_groepzin(g, per_id, uitkomst.term)}"
            )
        geheel = buur.groepen[0] if buur.groepen else None
        if (
            buur.oordeel == "niet_onderscheiden"
            and geheel
            and geheel.oordeel == "tegengeval"
        ):
            regels.append(
                f"- Elk geval van {buur.term}: {_groepzin(geheel, per_id, uitkomst.term)}"
            )
        if buur.oordeel == "onderscheiden":
            regels.append(
                f"De kern grenst {buur.term} af"
                + ("; gedeelde gevallen blijven mogelijk." if buur.overlap else ".")
            )
        elif buur.oordeel == "open":
            regels.append(
                f"Ten opzichte van {buur.term} is geen afgrenzing vastgesteld; geen "
                "uitspraak over andere mogelijke verschillen."
            )
    regels.append(BEREIKZIN)
    return "\n".join(regels)
