"""Regelingenregister: matrix van wet- en regelgeving × rechtsgebied (DEF-846).

Eén lijst in ``config/bronnenlijst.yaml`` (besluit Chris, 10-10-2026) voor:

- de keuzelijst "wettelijke basis" in de contextkiezer en de bewerk-tab;
- de koppeling regeling → collectie in de bronbibliotheek (``data/bronnen.db``);
- de rechtsgebieden waar een regeling bij hoort.

Een regeling zonder ``formaat`` heeft geen bibliotheekbron: zij blijft kiesbaar
als context, maar levert geen bibliotheekpassages. Het importscript
(``scripts/rag_bronnenlijst.py``) leest dezelfde lijst en slaat zulke regelingen
over.

Kenmerken:

``alleen_expliciete_keuze``
    De regeling telt niet mee als de bronnen via een rechtsgebied worden
    gekozen, alleen als zij zelf als wettelijke basis is gekozen (B-2: het
    nieuwe Wetboek van Strafvordering vóór inwerkingtreding).
``alle_rechtsgebieden``
    De regeling hoort bij elk rechtsgebied (B-5: het EVRM). Dan staat er geen
    ``rechtsgebieden``-lijst bij.

De labels zijn de waarden die in opgeslagen definities staan; een label
wijzigen vraagt dus een datamigratie (contextsleutel, duplicaatcontrole en
vaststelling vergelijken op de opgeslagen tekst). ``aliassen`` vangen een
hernoeming op in de keuzelijst, niet in die opgeslagen data.

Het register wordt bij het opstarten van de app gelezen (``main``) en daarna
per proces bewaard; een wijziging in de YAML vraagt een herstart.

Deze module bevat alleen het register zelf. De bronselectie op basis van het
register is DEF-631; de waarschuwing bij een combinatie buiten de matrix is
DEF-849.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from domain.context.normalisatie import lees_contextwaarden
from domain.rechtsgebieden import RECHTSGEBIEDEN

STANDAARD_PAD = Path(__file__).resolve().parents[3] / "config" / "bronnenlijst.yaml"

ALLEEN_EXPLICIETE_KEUZE = "alleen_expliciete_keuze"
ALLE_RECHTSGEBIEDEN = "alle_rechtsgebieden"
KENMERKEN = frozenset({ALLEEN_EXPLICIETE_KEUZE, ALLE_RECHTSGEBIEDEN})
FORMATEN = frozenset({"bwb", "op", "eu"})
# "Anders..." is de vaste UI-keuze voor vrije invoer; geen regelingnaam.
GERESERVEERD = frozenset({"anders..."})


class RegisterError(ValueError):
    """Het regelingenregister is ongeldig; de app toont dan bij het opstarten een fout."""


def _vergelijkvorm(tekst: str) -> str:
    return " ".join(tekst.split()).casefold()


@dataclass(frozen=True)
class Regeling:
    """Eén regeling uit het register."""

    sleutel: str
    label: str
    naam: str
    rechtsgebieden: tuple[str, ...]
    collectie: str | None = None
    aliassen: tuple[str, ...] = ()
    alleen_expliciete_keuze: bool = False
    alle_rechtsgebieden: bool = False

    @property
    def heeft_bibliotheekbron(self) -> bool:
        return self.collectie is not None

    def hoort_bij(self, rechtsgebied: str) -> bool:
        """Staat de combinatie met dit rechtsgebied (sleutel) in de matrix?"""
        return self.alle_rechtsgebieden or rechtsgebied in self.rechtsgebieden


@dataclass(frozen=True)
class Regelingenregister:
    """Het ingelezen en gecontroleerde register."""

    regelingen: tuple[Regeling, ...]

    def labels(self) -> list[str]:
        """De keuzelijst "wettelijke basis", in de volgorde van het register."""
        return [r.label for r in self.regelingen]

    def zoek(self, waarde: str | None) -> Regeling | None:
        """Regeling bij een label of alias (hoofdletters/witruimte genegeerd)."""
        if not waarde or not waarde.strip():
            return None
        doel = _vergelijkvorm(waarde)
        for regeling in self.regelingen:
            if doel in {
                _vergelijkvorm(n) for n in (regeling.label, *regeling.aliassen)
            }:
                return regeling
        return None

    def normaliseer(self, waarden: object) -> list[str]:
        """Vertaal labels en aliassen naar het huidige label; vrije invoer blijft.

        Accepteert alles wat ``lees_contextwaarden`` accepteert (lijst,
        JSON-tekst, losse tekst). Dubbelingen vallen weg, de volgorde blijft.
        """
        uit: list[str] = []
        for waarde in lees_contextwaarden(waarden):
            regeling = self.zoek(waarde)
            nieuw = regeling.label if regeling else waarde
            if nieuw not in uit:
                uit.append(nieuw)
        return uit

    def voor_rechtsgebied(self, rechtsgebied: str) -> list[Regeling]:
        """Regelingen die via dit rechtsgebied (sleutel) meetellen.

        Regelingen met ``alleen_expliciete_keuze`` tellen hier nooit mee.
        """
        return [
            r
            for r in self.regelingen
            if r.hoort_bij(rechtsgebied) and not r.alleen_expliciete_keuze
        ]

    def vergelijk_collecties(
        self, bestaande: Iterable[str]
    ) -> tuple[list[str], list[str]]:
        """Vergelijk het register met de collecties in de bronbibliotheek.

        Returns:
            (collecties zonder registerregel, registercollecties die ontbreken),
            elk gesorteerd. De uploadcollectie valt onder de eerste groep; de
            aanroeper beslist wat daarmee gebeurt.
        """
        bekend = {r.collectie for r in self.regelingen if r.collectie}
        aanwezig = set(bestaande)
        return sorted(aanwezig - bekend), sorted(bekend - aanwezig)


def lees_register(pad: Path = STANDAARD_PAD) -> Regelingenregister:
    """Lees ``bronnenlijst.yaml`` en controleer het register.

    Raises:
        RegisterError: bij een ontbrekend verplicht veld, een onbekend
            rechtsgebied of kenmerk, een regeling zonder rechtsgebied, een
            dubbele sleutel, een dubbel label of alias (ongeacht hoofdletters)
            of een dubbele collectie.
    """
    data = yaml.safe_load(Path(pad).read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict) or not isinstance(data.get("bronnen"), list):
        raise RegisterError("verwacht een lijst onder 'bronnen'")
    regelingen: list[Regeling] = []
    sleutels: set[str] = set()
    namen: dict[str, str] = {}
    collecties: set[str] = set()

    for nr, item in enumerate(data["bronnen"], 1):
        if not isinstance(item, dict):
            raise RegisterError(f"regeling {nr} is geen mapping")
        sleutel = str(item.get("sleutel") or "").strip()
        if not sleutel:
            raise RegisterError(f"regeling {nr} heeft geen sleutel")
        if sleutel in sleutels:
            raise RegisterError(f"dubbele sleutel: {sleutel}")
        sleutels.add(sleutel)

        label = _verplicht(item, "label", sleutel)
        naam = _verplicht(item, "naam", sleutel)
        aliassen = _tekstlijst(item, "aliassen", sleutel)
        for tekst in (label, *aliassen):
            vorm = _vergelijkvorm(tekst)
            if vorm in GERESERVEERD:
                raise RegisterError(f"{sleutel}: {tekst!r} is gereserveerd")
            if vorm in namen:
                raise RegisterError(
                    f"{sleutel}: dubbel label of alias {tekst!r} (ook bij {namen[vorm]})"
                )
            namen[vorm] = sleutel

        kenmerken = set(_tekstlijst(item, "kenmerken", sleutel))
        if onbekend := kenmerken - KENMERKEN:
            raise RegisterError(f"{sleutel}: onbekend kenmerk {sorted(onbekend)}")
        if kenmerken >= KENMERKEN:
            raise RegisterError(
                f"{sleutel}: alle_rechtsgebieden en alleen_expliciete_keuze sluiten elkaar uit"
            )

        rechtsgebieden = _tekstlijst(item, "rechtsgebieden", sleutel)
        if ALLE_RECHTSGEBIEDEN in kenmerken:
            if rechtsgebieden:
                raise RegisterError(
                    f"{sleutel}: bij alle_rechtsgebieden hoort geen rechtsgebiedenlijst"
                )
        elif not rechtsgebieden:
            raise RegisterError(f"{sleutel}: geen rechtsgebied")
        if onbekend_rg := [r for r in rechtsgebieden if r not in RECHTSGEBIEDEN]:
            raise RegisterError(f"{sleutel}: onbekend rechtsgebied {onbekend_rg}")
        if len(set(rechtsgebieden)) != len(rechtsgebieden):
            raise RegisterError(f"{sleutel}: rechtsgebied dubbel genoemd")

        collectie = None
        if formaat := item.get("formaat"):
            if formaat not in FORMATEN:
                raise RegisterError(f"{sleutel}: onbekend formaat {formaat!r}")
            collectie = _verplicht(item, "collectie", sleutel)
            if collectie in collecties:
                raise RegisterError(f"{sleutel}: dubbele collectie {collectie!r}")
            collecties.add(collectie)

        regelingen.append(
            Regeling(
                sleutel=sleutel,
                label=label,
                naam=naam,
                rechtsgebieden=rechtsgebieden,
                collectie=collectie,
                aliassen=aliassen,
                alleen_expliciete_keuze=ALLEEN_EXPLICIETE_KEUZE in kenmerken,
                alle_rechtsgebieden=ALLE_RECHTSGEBIEDEN in kenmerken,
            )
        )
    if not regelingen:
        raise RegisterError("het register is leeg")
    return Regelingenregister(tuple(regelingen))


def _tekstlijst(item: dict, veld: str, sleutel: str) -> tuple[str, ...]:
    """Een optionele lijst niet-lege teksten (een losse tekst is een fout)."""
    waarde = item.get(veld)
    if waarde is None:
        return ()
    if not isinstance(waarde, list):
        raise RegisterError(f"{sleutel}: {veld!r} moet een lijst zijn")
    teksten = tuple(str(w).strip() for w in waarde if w is not None)
    if len(teksten) != len(waarde) or not all(teksten):
        raise RegisterError(f"{sleutel}: lege waarde in {veld!r}")
    return teksten


def _verplicht(item: dict, veld: str, sleutel: str) -> str:
    waarde = str(item.get(veld) or "").strip()
    if not waarde:
        raise RegisterError(f"{sleutel}: veld {veld!r} ontbreekt")
    return waarde


@lru_cache(maxsize=1)
def register() -> Regelingenregister:
    """Het register uit ``config/bronnenlijst.yaml`` (eenmaal per proces gelezen)."""
    return lees_register(STANDAARD_PAD)


__all__ = [
    "ALLEEN_EXPLICIETE_KEUZE",
    "ALLE_RECHTSGEBIEDEN",
    "Regeling",
    "Regelingenregister",
    "RegisterError",
    "lees_register",
    "register",
]
