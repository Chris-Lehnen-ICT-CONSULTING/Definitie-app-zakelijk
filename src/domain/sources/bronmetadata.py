"""Opgegeven bronmetadata bij een geüpload document (DEF-808).

Een gebruiker kan van een geüpload document de bekende hyperlink, bronversie
en exacte vindplaats opgeven — bij de upload, of achteraf op de documentbronnen
van een opgeslagen record. Dit is één gedeelde laag voor beide routes:

- **validatie**: de hyperlink volgt exact de DEF-806-regel
  (`is_bruikbare_hyperlink`; een interne http(s)-link volstaat, geen
  netwerkcontrole); versie en vindplaats zijn vrije, niet-lege tekst; zonder
  enige waarde is er geen metadata. Ongeldige invoer levert een zichtbare
  reden en níets op — er wordt nooit iets stil weggelaten of doorgegeven;
- **toepassen**: de velden landen onder de sleutels die het broncontract al
  leest (`url`, `source_version`, `locator`) én blijven herkenbaar als
  *opgegeven* metadata in een apart herkomstblok (`declared_metadata`: door
  wie, wanneer). Dat blok is feitelijke bronmetadata en reist mee in de
  bronidentiteit en dus in de bronvingerafdruk: een eerdere AI-beoordeling of
  deskundige uitzondering geldt daarna niet meer en wordt opnieuw verkregen.

Een opgave is geen authenticiteitsbewijs, geen gezag en geen goedkeuring: de
kern beoordeelt brongezag, betekenissteun en verwijskwaliteit onverminderd.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from domain.sources.contract import is_bruikbare_hyperlink

__all__ = [
    "DECLARED_METADATA_KEY",
    "Bronmetadata",
    "pas_bronmetadata_toe",
    "valideer_bronmetadata",
    "vul_documentbronnen_aan",
]

#: Sleutel van het herkomstblok op een bron: de opgegeven waarden plus door
#: wie en wanneer zij zijn opgegeven. Bewust géén lid van
#: `NIET_SUBSTANTIEVE_VELDEN`: de opgave is feitelijke bronmetadata.
DECLARED_METADATA_KEY = "declared_metadata"

_VELDEN: tuple[str, str, str] = ("url", "source_version", "locator")


def _tekst(waarde: Any) -> str | None:
    """Een getrimde, niet-lege tekst of None (nooit de tekst 'None')."""
    if waarde is None or isinstance(waarde, bool):
        return None
    tekst = str(waarde).strip()
    return tekst or None


@dataclass(frozen=True)
class Bronmetadata:
    """Eén opgave: de drie coördinaten (elk optioneel) en haar herkomst."""

    url: str | None
    source_version: str | None
    locator: str | None
    declared_by: str | None
    declared_at: str

    def als_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "source_version": self.source_version,
            "locator": self.locator,
            "declared_by": self.declared_by,
            "declared_at": self.declared_at,
        }

    @classmethod
    def uit_dict(cls, waarde: Any) -> Bronmetadata | None:
        """Een bewaarde opgave terug als object; None als er geen coördinaat in staat."""
        if not isinstance(waarde, Mapping):
            return None
        velden = {veld: _tekst(waarde.get(veld)) for veld in _VELDEN}
        if not any(velden.values()):
            return None
        return cls(
            url=velden["url"],
            source_version=velden["source_version"],
            locator=velden["locator"],
            declared_by=_tekst(waarde.get("declared_by")),
            declared_at=_tekst(waarde.get("declared_at")) or "",
        )


def valideer_bronmetadata(
    url: Any,
    source_version: Any,
    locator: Any,
    *,
    declared_by: Any = None,
    declared_at: str | None = None,
    bestaand: Mapping[str, Any] | None = None,
) -> tuple[Bronmetadata | None, list[str]]:
    """Controleer een opgave; geeft (metadata of None, zichtbare fouten).

    `bestaand` is een eerdere opgave (herkomstblok of documentopgave): velden
    die nu niet worden opgegeven behouden hun eerdere waarde (aanvullen, niet
    wissen); de herkomst is die van de laatste opgave. Een ongeldige hyperlink
    is een fout — ook als versie of vindplaats wél kloppen: dan wordt niets
    opgeleverd, zodat een onbruikbare link nooit stil verdwijnt.
    """
    fouten: list[str] = []
    waarden = {
        "url": _tekst(url),
        "source_version": _tekst(source_version),
        "locator": _tekst(locator),
    }
    if waarden["url"] is not None and not is_bruikbare_hyperlink(waarden["url"]):
        fouten.append(
            f"hyperlink is niet bruikbaar: {waarden['url']!r} (vereist: http(s) met "
            "host, zonder witruimte; een interne link volstaat)"
        )
    eerder = Bronmetadata.uit_dict(bestaand)
    if eerder is not None:
        for veld in _VELDEN:
            if waarden[veld] is None:
                waarden[veld] = getattr(eerder, veld)
    if not any(waarden.values()):
        fouten.append(
            "geen bronmetadata opgegeven (hyperlink, bronversie of exacte vindplaats)"
        )
    if fouten:
        return None, fouten
    return (
        Bronmetadata(
            url=waarden["url"],
            source_version=waarden["source_version"],
            locator=waarden["locator"],
            declared_by=_tekst(declared_by),
            declared_at=declared_at or datetime.now(UTC).isoformat(),
        ),
        [],
    )


def pas_bronmetadata_toe(
    bron: Mapping[str, Any], metadata: Bronmetadata
) -> dict[str, Any]:
    """Een kopie van de bron met de opgave erop; de invoer blijft onaangeroerd.

    Alleen opgegeven coördinaten worden gezet (een eerder aanwezige waarde
    wordt niet gewist); het herkomstblok wordt volledig vervangen door deze
    opgave. Passage, kwitantieadministratie en overige velden blijven exact.
    """
    kopie = deepcopy(dict(bron))
    for veld in _VELDEN:
        waarde = getattr(metadata, veld)
        if waarde is not None:
            kopie[veld] = waarde
    kopie[DECLARED_METADATA_KEY] = metadata.als_dict()
    return kopie


def _is_documentbron_van(bron: Mapping[str, Any], doc_id: str) -> bool:
    provider = (_tekst(bron.get("provider")) or "").casefold()
    return (
        provider in ("documents", "document") and _tekst(bron.get("doc_id")) == doc_id
    )


def vul_documentbronnen_aan(
    bronnen: Iterable[Mapping[str, Any]], doc_id: str, metadata: Bronmetadata
) -> tuple[list[dict[str, Any]], int]:
    """Pas de opgave toe op elke documentpassage met dit `doc_id`.

    Geeft (nieuwe bronlijst als kopie, aantal geraakte bronnen). Bronnen van
    andere documenten of aanvoerroutes komen ongewijzigd (als kopie) terug;
    de invoer wordt niet gemuteerd.
    """
    doel = _tekst(doc_id) or ""
    resultaat: list[dict[str, Any]] = []
    aantal = 0
    for bron in bronnen:
        if isinstance(bron, Mapping) and doel and _is_documentbron_van(bron, doel):
            resultaat.append(pas_bronmetadata_toe(bron, metadata))
            aantal += 1
        else:
            resultaat.append(
                deepcopy(dict(bron)) if isinstance(bron, Mapping) else bron
            )
    return resultaat, aantal
