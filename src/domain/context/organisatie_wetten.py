"""
Organisatie-naar-wet koppelingen voor de Nederlandse justitieketen.

Geëxtraheerd uit context_wet_mapping.json om domeinkennis
over juridische toepassingsgebieden te bewaren.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ContextType(Enum):
    """Types van juridische contexten."""

    ORGANISATORISCH = "organisatorisch"
    JURIDISCH = "juridisch"
    WETTELIJK = "wettelijk"


@dataclass
class OrganisatieContext:
    """Organisatie met bijbehorende wetten."""

    naam: str
    afkorting: str
    wetten: list[str]
    beschrijving: str = ""


class OrganisatieWettenMapper:
    """
    Nederlandse justitieketen organisatie-wet koppelingen.

    Bevat kennis over welke wetten relevant zijn voor
    specifieke organisaties binnen de justitieketen.
    """

    # Organisatorische context mappings
    ORGANISATIE_WETTEN = {
        "OM": {
            "volledige_naam": "Openbaar Ministerie",
            "wetten": [
                "Wetboek van Strafvordering",
                "Wetboek van Strafrecht",
                "Wet op de economische delicten",
            ],
            "beschrijving": "Vervolgingsinstantie in strafzaken",
        },
        "ZM": {
            "volledige_naam": "Zittende Magistratuur",
            "wetten": [
                "Wetboek van Strafvordering",
                "Wet op de rechterlijke organisatie",
                "Wetboek van Strafrecht",
            ],
            "beschrijving": "Rechterlijke macht",
        },
        "Reclassering": {
            "volledige_naam": "Reclassering Nederland",
            "wetten": [
                "Penitentiaire beginselenwet",
                "Wetboek van Strafrecht",
                "Wet forensische zorg",
            ],
            "beschrijving": "Begeleiding ex-gedetineerden",
        },
        "DJI": {
            "volledige_naam": "Dienst Justitiële Inrichtingen",
            "wetten": [
                "Penitentiaire beginselenwet",
                "Penitentiaire maatregel",
                "Wet langdurige zorg",
                "Vreemdelingenwet 2000",
                "Vreemdelingenbesluit 2000",
            ],
            "beschrijving": "Gevangeniswezen en vreemdelingendetentie",
        },
        "NP": {
            "volledige_naam": "Nederlandse Politie",
            "wetten": [
                "Wet politiegegevens",
                "Politiewet 2012",
                "Wetboek van Strafvordering",
                "Vreemdelingenwet 2000",
                "Vreemdelingenbesluit 2000",
            ],
            "beschrijving": "Opsporing en handhaving",
        },
        "Justid": {
            "volledige_naam": "Justid (Justitie Identiteit)",
            "wetten": [
                "Wet politiegegevens",
                "Algemene verordening gegevensbescherming (AVG)",
                "Wet justitiële en strafvorderlijke gegevens",
            ],
            "beschrijving": "Identiteits- en toegangsbeheer Justitie",
        },
        "KMAR": {
            "volledige_naam": "Koninklijke Marechaussee",
            "wetten": [
                "Wet op de KMar",
                "Wetboek van Strafrecht",
                "Wetboek van Strafvordering",
                "Vreemdelingenwet 2000",
                "Vreemdelingenbesluit 2000",
            ],
            "beschrijving": "Grensbewaking en militaire politie",
        },
        "FIOD": {
            "volledige_naam": "Fiscale Inlichtingen- en Opsporingsdienst",
            "wetten": [
                "Wet op de economische delicten",
                "Wetboek van Strafrecht",
                "Algemene wet inzake rijksbelastingen",
            ],
            "beschrijving": "Fiscale opsporing",
        },
        "CJIB": {
            "volledige_naam": "Centraal Justitieel Incassobureau",
            "wetten": [
                "Wet administratiefrechtelijke handhaving verkeersvoorschriften",
                "Wetboek van Strafrecht",
            ],
            "beschrijving": "Incasso van boetes",
        },
    }

    # Juridische domein mappings
    JURIDISCHE_DOMEINEN = {
        "Strafrecht": [
            "Wetboek van Strafrecht",
            "Wetboek van Strafvordering",
            "Wet op de economische delicten",
        ],
        "Civiel recht": [
            "Burgerlijk Wetboek",
            "Wetboek van Burgerlijke Rechtsvordering",
        ],
        "Bestuursrecht": [
            "Algemene wet bestuursrecht",
            "Wet open overheid",
            "Wet politiegegevens",
        ],
        "Internationaal recht": [
            "Verdrag betreffende de Europese Unie",
            "Europees Verdrag voor de Rechten van de Mens (EVRM)",
            "Internationaal verdrag inzake burgerrechten en politieke rechten",
        ],
    }

    # Specifieke wetgeving
    SPECIFIEKE_WETTEN = {
        "Wetboek van Strafvordering (huidig)",
        "Wetboek van Strafvordering (toekomstig)",
        "Wet op de Identificatieplicht",
        "Wet op de politiegegevens",
        "Wetboek van Strafrecht",
        "Algemene verordening gegevensbescherming",
    }

    @classmethod
    def get_wetten_voor_organisatie(cls, organisatie: str) -> list[str]:
        """
        Krijg relevante wetten voor een organisatie.

        Args:
            organisatie: Organisatie afkorting (bijv. "OM", "DJI")

        Returns:
            Lijst van relevante wetten
        """
        org_info = cls.ORGANISATIE_WETTEN.get(organisatie.upper(), {})
        wetten = org_info.get("wetten", [])
        return list(wetten) if wetten else []

    @classmethod
    def get_organisatie_info(cls, organisatie: str) -> dict[str, Any]:
        """
        Krijg volledige informatie over een organisatie.

        Args:
            organisatie: Organisatie afkorting

        Returns:
            Dict met naam, wetten, beschrijving
        """
        return cls.ORGANISATIE_WETTEN.get(organisatie.upper(), {})

    @classmethod
    def get_wetten_voor_domein(cls, domein: str) -> list[str]:
        """
        Krijg wetten voor een juridisch domein.

        Args:
            domein: Juridisch domein (bijv. "Strafrecht")

        Returns:
            Lijst van relevante wetten
        """
        return cls.JURIDISCHE_DOMEINEN.get(domein, [])

    @classmethod
    def zoek_organisaties_met_wet(cls, wet: str) -> list[str]:
        """
        Zoek organisaties die met een specifieke wet werken.

        Args:
            wet: Naam van de wet

        Returns:
            Lijst van organisatie afkortingen
        """
        resultaat = []
        for org, info in cls.ORGANISATIE_WETTEN.items():
            if wet in info.get("wetten", []):
                resultaat.append(org)
        return resultaat

    @classmethod
    def get_alle_organisaties(cls) -> list[str]:
        """Krijg lijst van alle organisatie afkortingen."""
        return list(cls.ORGANISATIE_WETTEN.keys())

    @classmethod
    def get_alle_juridische_domeinen(cls) -> list[str]:
        """Krijg lijst van alle juridische domeinen."""
        return list(cls.JURIDISCHE_DOMEINEN.keys())

    @classmethod
    def is_bekende_organisatie(cls, organisatie: str) -> bool:
        """Check of een organisatie bekend is."""
        return organisatie.upper() in cls.ORGANISATIE_WETTEN

    @classmethod
    def is_bekend_juridisch_domein(cls, domein: str) -> bool:
        """Check of een juridisch domein bekend is."""
        return domein in cls.JURIDISCHE_DOMEINEN
