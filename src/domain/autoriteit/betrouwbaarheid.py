"""
Betrouwbaarheids- en autoriteitsscores voor juridische bronnen.

Geëxtraheerd uit legacy bron_lookup.py om domeinkennis
over Nederlandse juridische hiërarchie te bewaren.
"""

from dataclasses import dataclass
from enum import Enum


class BronType(Enum):
    """Types van juridische en beleidsmatige bronnen met autoriteit rangorde."""

    WETGEVING = "wetgeving"  # Hoogste autoriteit: wetten en regelingen
    JURISPRUDENTIE = "jurisprudentie"  # Rechterlijke uitspraken
    BELEID = "beleid"  # Beleidsdocumenten en richtlijnen
    LITERATUUR = "literatuur"  # Juridische literatuur en publicaties
    INTERNE_DEFINITIE = "interne_definitie"  # Intern vastgestelde definities
    EXTERNE_BRON = "externe_bron"  # Externe bronnen (websites, databases)
    ONBEKEND = "onbekend"  # Type kon niet worden bepaald


class BronValiditeit(Enum):
    """Validiteitsstatus van juridische bronnen."""

    GELDIG = "geldig"  # Bron is actueel en rechtsgeldig
    VEROUDERD = "verouderd"  # Bron is vervangen door nieuwere versie
    INGETROKKEN = "ingetrokken"  # Bron is expliciet ingetrokken
    ONBEKEND = "onbekend"  # Validiteit kon niet worden vastgesteld


@dataclass
class AutoriteitsScore:
    """Betrouwbaarheidsscore met toelichting."""

    score: float  # 0.0 - 1.0
    basis_score: float
    domein_bonus: float = 0.0
    wet_bonus: float = 0.0
    domein_penalty: float = 0.0
    toelichting: str = ""


class BetrouwbaarheidsCalculator:
    """
    Nederlandse juridische autoriteit en betrouwbaarheidsregels.

    Gebaseerd op de hiërarchie van het Nederlandse rechtssysteem
    en government.nl domein autoriteiten.
    """

    # Bron type autoriteit scores (gebaseerd op Nederlandse rechtsorde)
    TYPE_SCORES = {
        BronType.WETGEVING: 1.0,  # Formele wetgeving - hoogste autoriteit
        BronType.JURISPRUDENTIE: 0.9,  # Rechterlijke uitspraken - zeer hoog
        BronType.BELEID: 0.8,  # Overheidsbeleid - hoog
        BronType.LITERATUUR: 0.7,  # Juridische doctrine - gemiddeld-hoog
        BronType.INTERNE_DEFINITIE: 0.6,  # Interne definities - gemiddeld
        BronType.EXTERNE_BRON: 0.4,  # Externe bronnen - laag
        BronType.ONBEKEND: 0.3,  # Onbekend type - zeer laag
    }

    # Vertrouwde Nederlandse overheids- en juridische domeinen
    VERTROUWDE_DOMEINEN = {
        # Centrale overheidsdomeinen
        "wetten.overheid.nl",  # Officiële wetgeving
        "rechtspraak.nl",  # Rechterlijke macht
        "rijksoverheid.nl",  # Centrale overheid
        "government.nl",  # Internationale overheid
        # Europese autoriteiten
        "europa.eu",  # EU instellingen
        "eur-lex.europa.eu",  # EU wetgeving
        # Specifieke juridische instanties
        "justid.nl",  # Justitie ID
        "dji.nl",  # Dienst Justitiële Inrichtingen
        "om.nl",  # Openbaar Ministerie
        "rechtbanken.nl",  # Rechtbanken
        "gerechtshoven.nl",  # Gerechtshoven
        "hogeraad.nl",  # Hoge Raad
        # Semi-officiële juridische bronnen
        "advocatenblad.nl",  # Nederlandse Orde van Advocaten
        "rechters.nl",  # Nederlandse Vereniging voor Rechtspraak
    }

    # Bekende Nederlandse wetten (kernwetgeving)
    BEKENDE_WETTEN = {
        # Strafrecht
        "Wetboek van Strafrecht",
        "Wetboek van Strafvordering",
        # Civiel recht
        "Burgerlijk Wetboek",
        "Wetboek van Burgerlijke Rechtsvordering",
        # Bestuursrecht
        "Algemene wet bestuursrecht",
        "Wet openbaarheid van bestuur",
        # Specifieke domeinen
        "Wet op de rechtsbijstand",
        "Penitentiaire beginselenwet",
        "Wet op de identificatie",
        "Paspoortwet",
        "Wet basisregistratie personen",
        "Vreemdelingenwet",
        "Rijkswet op het Nederlanderschap",
        # Procedureel
        "Wet op de rechterlijke organisatie",
        "Advocatenwet",
        "Gerechtsdeurwaarderswet",
    }

    @classmethod
    def bereken_betrouwbaarheid(
        cls, bron_type: BronType, naam: str = "", url: str = ""
    ) -> AutoriteitsScore:
        """
        Bereken betrouwbaarheidsscore volgens Nederlandse juridische hiërarchie.

        Args:
            bron_type: Type juridische bron
            naam: Naam van de bron/wet
            url: URL van de bron (voor domein validatie)

        Returns:
            AutoriteitsScore met gedetailleerde score breakdown
        """
        # Basis score op type
        basis_score = cls.TYPE_SCORES.get(bron_type, 0.3)

        domein_bonus = 0.0
        wet_bonus = 0.0
        domein_penalty = 0.0
        toelichting_parts = []

        # URL domein validatie
        if url:
            is_vertrouwd = any(
                domein in url.lower() for domein in cls.VERTROUWDE_DOMEINEN
            )
            if is_vertrouwd:
                domein_bonus = 0.2
                toelichting_parts.append("Vertrouwd overheidsdomein")
            else:
                domein_penalty = 0.1
                toelichting_parts.append("Onbekend domein")

        # Bekende wetgeving bonus
        if naam and any(wet.lower() in naam.lower() for wet in cls.BEKENDE_WETTEN):
            wet_bonus = 0.1
            toelichting_parts.append("Bekende Nederlandse wetgeving")

        # Totaal score berekening
        totaal_score = basis_score + domein_bonus + wet_bonus - domein_penalty
        totaal_score = max(0.0, min(1.0, totaal_score))  # Clampen tussen 0-1

        toelichting = f"Type: {bron_type.value} (basis: {basis_score:.1f})"
        if toelichting_parts:
            toelichting += f", {', '.join(toelichting_parts)}"

        return AutoriteitsScore(
            score=totaal_score,
            basis_score=basis_score,
            domein_bonus=domein_bonus,
            wet_bonus=wet_bonus,
            domein_penalty=domein_penalty,
            toelichting=toelichting,
        )

    @classmethod
    def is_vertrouwd_domein(cls, url: str) -> bool:
        """Check of een URL van een vertrouwd domein komt."""
        if not url:
            return False

        url_lower = url.lower()
        return any(domein in url_lower for domein in cls.VERTROUWDE_DOMEINEN)

    @classmethod
    def is_bekende_wet(cls, naam: str) -> bool:
        """Check of een naam refereert naar bekende Nederlandse wetgeving."""
        if not naam:
            return False

        naam_lower = naam.lower()
        return any(wet.lower() in naam_lower for wet in cls.BEKENDE_WETTEN)
