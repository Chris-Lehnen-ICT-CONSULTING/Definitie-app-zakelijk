"""
Juridische structuurherkenning voor Nederlandse wetteksten.

Herkent hiërarchie: Titel > Boek > Hoofdstuk > Afdeling > Paragraaf > Artikel > Lid > Bijlage
en levert een flat list van structuur-elementen gesorteerd op positie.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ── Structuur-elementen ──────────────────────────────────────────

STRUCTUUR_TYPES = (
    "titel",
    "boek",
    "hoofdstuk",
    "afdeling",
    "paragraaf",
    "artikel",
    "lid",
    "bijlage",
    "definitieblok",
    "inleiding",
)


@dataclass
class JuridischeStructuur:
    """Een herkend structuur-element in een wettekst."""

    type: str  # Een van STRUCTUUR_TYPES
    nummer: str  # "1", "2a", "I", "10:1", etc.
    start: int  # Startpositie in de tekst
    eind: int  # Eindpositie (start van volgende element, of einde tekst)
    tekst: str  # De volledige tekst van dit element
    pagina_nummer: int | None = None


# ── Regex patronen ───────────────────────────────────────────────

# Titel: "TITEL 1", "Titel I"
_RE_TITEL = re.compile(
    r"^(?:TITEL|Titel)\s+(\d+|[IVXLC]+)\.?\s*.*",
    re.MULTILINE,
)

# Boek: "BOEK 1", "Boek 7"
_RE_BOEK = re.compile(
    r"^(?:BOEK|Boek)\s+(\d+|[IVXLC]+)\.?\s*.*",
    re.MULTILINE,
)

# Hoofdstuk: "HOOFDSTUK 1", "Hoofdstuk I", "Hoofdstuk 1. Algemene bepalingen"
_RE_HOOFDSTUK = re.compile(
    r"^(?:HOOFDSTUK|Hoofdstuk)\s+(\d+|[IVXLC]+)\.?\s*.*",
    re.MULTILINE,
)

# Afdeling: "Afdeling 1", "AFDELING 2. Titel"
_RE_AFDELING = re.compile(
    r"^(?:AFDELING|Afdeling)\s+(\d+|[IVXLC]+)\.?\s*.*",
    re.MULTILINE,
)

# Paragraaf: "Paragraaf 1", "§ 1", "PARAGRAAF 2"
_RE_PARAGRAAF = re.compile(
    r"^(?:PARAGRAAF|Paragraaf|§)\s+(\d+|[IVXLC]+)\.?\s*.*",
    re.MULTILINE,
)

# Artikel: "Artikel 1", "Art. 1", "ARTIKEL 1", "artikel 1a", "Artikel 10:1" (BW),
# "Artikel 5.3.2" (samengestelde nummers)
# Geen $ anchor: tekst mag na het nummer volgen (bijv. "Artikel 1 Strafvordering")
_RE_ARTIKEL = re.compile(
    r"^(?:ARTIKEL|Artikel|artikel|Art\.?)\s+(\d+(?:[.:]\d+)*[a-zA-Z]?)\.?\s*",
    re.MULTILINE,
)

# Bijlage: "Bijlage I", "BIJLAGE A", "Bijlage 1"
_RE_BIJLAGE = re.compile(
    r"^(?:BIJLAGE|Bijlage)\s+([IVXLCA-Z0-9]+)\.?\s*.*",
    re.MULTILINE,
)

# Lid: genummerde of geletterde opsomming aan begin van regel
# Group 1: numeriek ("1.", "2."), Group 2: letter ("a.", "b.")
# Alleen bruikbaar binnen de context van een artikel
_RE_LID = re.compile(
    r"^(?:(\d+)|([a-z]))\.\s+\S",
    re.MULTILINE,
)

# Definitieblok patronen
_RE_DEFINITIE_START = re.compile(
    r"(?:In\s+deze\s+(?:wet|regeling|verordening|besluit|algemene\s+maatregel)"
    r"\s+wordt\s+verstaan\s+onder|"
    r"Voor\s+de\s+toepassing\s+van\s+deze\s+(?:wet|regeling|verordening|besluit)"
    r"\s+wordt\s+verstaan\s+onder|"
    r"In\s+dit\s+(?:besluit|artikel)\s+wordt\s+verstaan\s+onder)",
    re.IGNORECASE,
)

# Wet-naam patronen
_RE_WET_NAAM = re.compile(
    r"((?:Wet\s+op\s+de|Wet\s+tot|Wetboek\s+van|Besluit|"
    r"Regeling|Verordening)\s+[\w\s]+?)(?:\n|$)",
    re.IGNORECASE,
)

# Nederlandse afkortingen die geen zinsgrens vormen
_AFKORTINGEN_PATTERN = r"(?<!\b(?:Mr|Dr|Prof|mr|dr|prof|drs|ing|ir|art|Art|lid|nr|Nr|resp|bijv|evt|zgn|e\.d|o\.a|m\.b\.t|t\.a\.v|i\.v\.m|a\.s|d\.d|i\.h\.b))"


# ── Recognizer ───────────────────────────────────────────────────


class LegalStructureRecognizer:
    """Herkent juridische structuur in Nederlandse wetteksten."""

    # Minimum aantal artikelen om als juridisch document te classificeren
    MIN_ARTIKELEN = 2

    def is_juridisch_document(self, tekst: str) -> bool:
        """Bepaal of tekst een juridisch document is (>= 2 artikelen)."""
        if not tekst or not tekst.strip():
            return False
        # Normaliseer \f (PDF page breaks) zodat ^ in MULTILINE werkt
        tekst_norm = tekst.replace("\f", "\n")
        matches = _RE_ARTIKEL.findall(tekst_norm)
        return len(matches) >= self.MIN_ARTIKELEN

    def detecteer_structuur(self, tekst: str) -> list[JuridischeStructuur]:
        """
        Detecteer alle structuur-elementen in de tekst.

        Returns:
            Flat list van JuridischeStructuur, gesorteerd op startpositie.
        """
        if not tekst or not tekst.strip():
            return []

        elementen: list[JuridischeStructuur] = []
        pagina_grenzen = self._detecteer_pagina_grenzen(tekst)

        # Normaliseer \f naar \n zodat regexes met ^ (MULTILINE) werken.
        # Posities blijven gelijk omdat \f en \n beide 1 karakter zijn.
        tekst_norm = tekst.replace("\f", "\n")

        # Detecteer hoofdstructuren
        for pattern, stype in [
            (_RE_TITEL, "titel"),
            (_RE_BOEK, "boek"),
            (_RE_HOOFDSTUK, "hoofdstuk"),
            (_RE_AFDELING, "afdeling"),
            (_RE_PARAGRAAF, "paragraaf"),
            (_RE_ARTIKEL, "artikel"),
            (_RE_BIJLAGE, "bijlage"),
        ]:
            for m in pattern.finditer(tekst_norm):
                pagina = self._bepaal_pagina(m.start(), pagina_grenzen)
                elementen.append(
                    JuridischeStructuur(
                        type=stype,
                        nummer=m.group(1),
                        start=m.start(),
                        eind=m.end(),  # Tijdelijk, wordt later bijgewerkt
                        tekst="",  # Wordt later ingevuld
                        pagina_nummer=pagina,
                    )
                )

        # Sorteer op positie
        elementen.sort(key=lambda e: e.start)

        # Voeg inleiding-chunk toe als er tekst is vóór het eerste herkende element
        if elementen and elementen[0].start > 0:
            inleiding_tekst = tekst_norm[: elementen[0].start].strip()
            if inleiding_tekst:
                pagina = self._bepaal_pagina(0, pagina_grenzen)
                elementen.insert(
                    0,
                    JuridischeStructuur(
                        type="inleiding",
                        nummer="",
                        start=0,
                        eind=0,  # Wordt overschreven door de positie-loop hieronder
                        tekst=inleiding_tekst,
                        pagina_nummer=pagina,
                    ),
                )

        # Vul tekst en eind-posities in
        for i, elem in enumerate(elementen):
            volgende_start = (
                elementen[i + 1].start if i + 1 < len(elementen) else len(tekst_norm)
            )
            elem.eind = volgende_start
            elem.tekst = tekst_norm[elem.start : elem.eind].strip()

        # Markeer definitieblokken
        return self._markeer_definitieblokken(elementen)

    def detecteer_leden(
        self, artikel_tekst: str, include_letter_leden: bool = True
    ) -> list[JuridischeStructuur]:
        """
        Detecteer leden (genummerde en geletterde opsommingen) binnen een artikel.

        Args:
            artikel_tekst: Tekst van een enkel artikel.
            include_letter_leden: Of letter-leden (a., b.) meegenomen worden.

        Returns:
            Lijst van lid-elementen, gesorteerd op positie.
        """
        leden: list[JuridischeStructuur] = []

        for m in _RE_LID.finditer(artikel_tekst):
            numeriek = m.group(1)  # "1", "2", etc. of None
            letter = m.group(2)  # "a", "b", etc. of None
            if letter and not include_letter_leden:
                continue
            leden.append(
                JuridischeStructuur(
                    type="lid",
                    nummer=numeriek or letter or "",
                    start=m.start(),
                    eind=m.end(),
                    tekst="",
                )
            )

        # Sorteer en vul tekst in
        leden.sort(key=lambda e: e.start)
        for i, lid in enumerate(leden):
            volgende_start = (
                leden[i + 1].start if i + 1 < len(leden) else len(artikel_tekst)
            )
            lid.eind = volgende_start
            lid.tekst = artikel_tekst[lid.start : lid.eind].strip()

        return leden

    def detecteer_wet_naam(self, tekst: str) -> str | None:
        """Detecteer de naam van de wet/regeling uit de tekst header."""
        if not tekst:
            return None
        # Zoek in eerste 2000 karakters (PDF headers/metadata kunnen lang zijn)
        header = tekst[:2000]
        m = _RE_WET_NAAM.search(header)
        if m:
            return m.group(1).strip()
        return None

    def _detecteer_pagina_grenzen(self, tekst: str) -> list[int]:
        """Detecteer pagina-grenzen via form-feed characters (\\f)."""
        return [i for i, ch in enumerate(tekst) if ch == "\f"]

    def _bepaal_pagina(self, positie: int, grenzen: list[int]) -> int | None:
        """Bepaal paginanummer op basis van positie en pagina-grenzen."""
        if not grenzen:
            return None
        pagina = 1
        for grens in grenzen:
            if positie > grens:
                pagina += 1
            else:
                break
        return pagina

    def _markeer_definitieblokken(
        self, elementen: list[JuridischeStructuur]
    ) -> list[JuridischeStructuur]:
        """Markeer artikelen die definitieblokken bevatten."""
        for elem in elementen:
            if elem.type == "artikel" and self._is_definitieblok(elem.tekst):
                elem.type = "definitieblok"
        return elementen

    @staticmethod
    def _is_definitieblok(tekst: str) -> bool:
        """
        Bepaal of een tekst een definitieblok is.

        Combineert twee signalen:
        1. Opening phrase: "wordt verstaan onder" of vergelijkbaar
        2. Lettered of genummerde enumeration: a., b., c. of 1), 2), 3) items
        Beide moeten aanwezig zijn om false positives te voorkomen.
        """
        if not tekst:
            return False
        if not _RE_DEFINITIE_START.search(tekst):
            return False
        # Check voor opsomming: letter (a., b.) OF genummerd (1), 2))
        return bool(
            re.search(r"^\s*(?:[a-z][.)]\s+\S|\d+\)\s+\S)", tekst, re.MULTILINE)
        )
