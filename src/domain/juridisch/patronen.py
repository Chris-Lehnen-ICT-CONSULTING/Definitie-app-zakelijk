"""
Juridische patroon herkenning voor Nederlandse wetgeving.

Geëxtraheerd uit legacy juridische_lookup.py om domeinkennis
te bewaren in een herbruikbare vorm.
"""

import re
from dataclasses import dataclass
from re import Pattern


@dataclass
class JuridischeVerwijzing:
    """Representeert een juridische verwijzing met alle componenten."""

    wet: str | None = None
    boek: str | None = None
    artikel: str | None = None
    lid: str | None = None
    sub: str | None = None
    herkend_via: str | None = None

    def to_dict(self) -> dict[str, str]:
        """Converteer naar dict, filter None waardes."""
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class JuridischPatroon:
    """Definitie van een juridisch herkenningspatroon."""

    id: str
    beschrijving: str
    pattern: Pattern[str]

    def match_in_text(self, tekst: str) -> list[JuridischeVerwijzing]:
        """Vind alle matches van dit patroon in de gegeven tekst."""
        resultaten = []

        for match in self.pattern.finditer(tekst):
            verwijzing = JuridischeVerwijzing(
                herkend_via=self.id, **{k: v for k, v in match.groupdict().items() if v}
            )
            resultaten.append(verwijzing)

        return resultaten


class JuridischePatronen:
    """
    Nederlandse juridische patroon herkenning.

    Bevat alle regex patronen voor het herkennen van Nederlandse
    juridische verwijzingen in verschillende formaten.
    """

    # Wetboek afkortingen en hun volledige namen
    WETBOEK_AFKORTINGEN = {
        "BW": "Burgerlijk Wetboek",
        "Sv": "Wetboek van Strafvordering",
        "Sr": "Wetboek van Strafrecht",
        "Rv": "Wetboek van Burgerlijke Rechtsvordering",
        "RvS": "Raad van State",
    }

    @classmethod
    def get_patronen(cls) -> list[JuridischPatroon]:
        """
        Retourneert alle juridische herkenningspatronen.

        Gebaseerd op de originele _REGEX_PATRONEN uit juridische_lookup.py
        maar gestructureerd als herbruikbare domein objecten.
        """
        return [
            JuridischPatroon(
                id="klassiek_format",
                beschrijving="Klassiek format: 'Wetboek van Strafrecht, artikel 123'",
                pattern=re.compile(
                    r"(?P<wet>Wetboek van [A-Z][a-z]+)(?:,\s*boek\s*(?P<boek>[0-9]+))?,?\s*artikel\s*(?P<artikel>[0-9a-zA-Z]+)(?:\s*lid\s*(?P<lid>[0-9]+))?",
                    re.IGNORECASE,
                ),
            ),
            JuridischPatroon(
                id="verkort_format_bw_sv",
                beschrijving="Verkort format: 'art. 123:45 BW'",
                pattern=re.compile(
                    r"art\.?\s*(?P<artikel>[0-9]+:[0-9a-zA-Z]+)\s+(?P<wet>BW|Sv|Sr|Rv|RvS)",
                    re.IGNORECASE,
                ),
            ),
            JuridischPatroon(
                id="normale_artikel_wet",
                beschrijving="Normaal format: 'artikel 123 van de Wet op ...'",
                pattern=re.compile(
                    r"artikel\s+(?P<artikel>[0-9]+[a-zA-Z]?)\s+van\s+de\s+(?P<wet>[A-Z][a-zA-Z\s]+)",
                    re.IGNORECASE,
                ),
            ),
            JuridischPatroon(
                id="artikel_lid_onder_wet",
                beschrijving="Uitgebreid format: 'artikel 123 lid 4 onder a van de Wet ...'",
                pattern=re.compile(
                    r"artikel\s+(?P<artikel>[0-9]+[a-zA-Z]?)\s+lid\s+(?P<lid>[0-9]+)\s+(onder\s+(?P<sub>[a-z]))?\s+van\s+de\s+(?P<wet>[A-Z][a-zA-Z\s]+)",
                    re.IGNORECASE,
                ),
            ),
        ]

    @classmethod
    def zoek_alle_verwijzingen(cls, tekst: str) -> list[JuridischeVerwijzing]:
        """
        Zoek alle juridische verwijzingen in de gegeven tekst.

        Vervangt de originele zoek_wetsartikelstructuur functie
        met een meer object-georiënteerde aanpak.
        """
        alle_verwijzingen = []

        for patroon in cls.get_patronen():
            verwijzingen = patroon.match_in_text(tekst)
            alle_verwijzingen.extend(verwijzingen)

        return alle_verwijzingen

    @classmethod
    def expandeer_afkorting(cls, afkorting: str) -> str | None:
        """Expandeer wetboek afkorting naar volledige naam."""
        return cls.WETBOEK_AFKORTINGEN.get(afkorting.upper())
