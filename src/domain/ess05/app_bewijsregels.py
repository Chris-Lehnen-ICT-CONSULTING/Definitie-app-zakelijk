"""ESS-05 in de app via de bewijsregelroute: document `ess05/3`, binding en replay (DEF-768).

Plan: `docs/plans/2026-09-29-DEF-768-ess05-app-aansluiting-plan-v1.md` en het
besluit in `-aanvulling-v1.md`. De adapter `Ess05BewijsregelService.assess`
schrijft het document; `domain.ess05.contract` speelt het af zonder AI-aanroep
en past daarna het app-bevestigingsbeleid toe (besluit B). Deze module kent
alleen de bewijsregelkant: binding, en uit het bewaarde document opnieuw
afleiden wat de regels zeggen.

Replay vertrouwt niets wat het document zelf als oordeel noemt. Uit de
ongewijzigd bewaarde ruwe interpretatie wordt de interpretatie opnieuw
gevalideerd, de controle-eenheden worden opnieuw uit het huidige materiaal
opgebouwd, en elke bewaarde controle moet exact bij haar pakket horen en
`supported` zijn. Pas dan gelden de regels. Pure domeinlogica: geen
AI-client, geen Streamlit, geen database.
"""

from __future__ import annotations

import hashlib
import html
from collections.abc import Mapping
from dataclasses import dataclass, fields
from typing import Any

from domain.ess05 import bewijsregels as br
from domain.ess05.lokale_controle import (
    LOKAAL_VERIFICATIESCHEMA,
    PAKKETSCHEMA,
    toets_lokale_verificatie,
)
from domain.modeluitvoer import parse_modeluitvoer

__all__ = [
    "DOCUMENTVERSIE",
    "Bewijsregeloordeel",
    "Ess05Bewijsregelbinding",
    "ontsnap",
    "speel_af",
]

#: Documentvorm van de bewijsregelroute. De vingerafdruk en de lege-ruimte-
#: bevestiging blijven `contract.CONTRACTVERSIE` (`ess05/2`): hun invoer en
#: betekenis zijn niet veranderd, dus een deskundige bevestiging blijft gelden.
DOCUMENTVERSIE = "ess05/3"

_OPTIONEEL = frozenset(
    {"provider", "model", "verification_provider", "verification_model"}
)


@dataclass(frozen=True)
class Ess05Bewijsregelbinding:
    """De actuele binding van de bewijsregelroute: prompts, versies en modellen.

    Een document geldt alleen onder exact deze binding; elke afwijking maakt
    het historisch (toets opnieuw).
    """

    prompt_version: str
    system_prompt_sha256: str
    verification_prompt_version: str
    provider: str | None
    model: str | None
    verification_provider: str | None
    verification_model: str | None
    rule_version: str = br.BEWIJSREGELVERSIE
    schema_version: str = br.INTERPRETATIESCHEMA
    renderer_version: str = br.RENDERVERSIE
    packet_schema_version: str = PAKKETSCHEMA
    verification_schema_version: str = LOKAAL_VERIFICATIESCHEMA

    def als_dict(self) -> dict[str, str | None]:
        return {veld.name: getattr(self, veld.name) for veld in fields(self)}

    @classmethod
    def uit_dict(cls, waarde: Any) -> Ess05Bewijsregelbinding | None:
        """Fail-closed: exact de bindingsvelden, versies als niet-lege tekst."""
        if not isinstance(waarde, Mapping):
            return None
        velden = {veld.name for veld in fields(cls)}
        if set(waarde) != velden:
            return None
        for veld in velden:
            inhoud = waarde[veld]
            if veld in _OPTIONEEL:
                if inhoud is not None and not isinstance(inhoud, str):
                    return None
            elif not isinstance(inhoud, str) or not inhoud.strip():
                return None
        return cls(**{veld: waarde[veld] for veld in velden})


@dataclass(frozen=True)
class Bewijsregeloordeel:
    """Het opnieuw afgeleide regelresultaat; `regels` is None zonder buren (D)."""

    regels: br.Regeluitkomst | None


def ontsnap(waarde: Any) -> Any:
    """Tekens die de prompt ontsnapte, terug naar de letterlijke materiaaltekst."""
    if isinstance(waarde, str):
        return html.unescape(waarde)
    if isinstance(waarde, list):
        return [ontsnap(w) for w in waarde]
    if isinstance(waarde, dict):
        return {k: ontsnap(v) for k, v in waarde.items()}
    return waarde


def _sha(tekst: str) -> str:
    return hashlib.sha256(tekst.encode("utf-8")).hexdigest()


def _interpretatie(
    document: Mapping[str, Any], invoer: br.Vergelijkingsinvoer
) -> tuple[br.Interpretatie | None, str]:
    registratie = document.get("interpretation")
    if not isinstance(registratie, Mapping):
        return None, "interpretatie ontbreekt"
    ruw = registratie.get("raw_response")
    if not isinstance(ruw, str) or _sha(ruw) != registratie.get("raw_response_sha256"):
        return None, "ruwe interpretatie ontbreekt of hoort niet bij haar hash"
    geparsed = parse_modeluitvoer(ruw)
    if geparsed is None:
        return None, "ruwe interpretatie is geen kaal JSON-object"
    try:
        return br.valideer_interpretatie(ontsnap(geparsed), invoer), ""
    except br.BewijsregelfoutError as exc:
        return None, f"interpretatie ongeldig op dit materiaal ({exc.soort})"


def _controlefout(
    document: Mapping[str, Any],
    interpretatie: br.Interpretatie,
    invoer: br.Vergelijkingsinvoer,
) -> str | None:
    """Waarom de bewaarde controles de interpretatie niet dragen, of None."""
    eenheden = br.controle_eenheden(interpretatie, invoer)
    controles = document.get("controls")
    if not isinstance(controles, list) or len(controles) != len(eenheden):
        return "de bewaarde controles dekken niet exact de controle-eenheden"
    for eenheid, controle in zip(eenheden, controles, strict=True):
        if not isinstance(controle, Mapping) or (
            controle.get("name"),
            controle.get("packet_hash"),
        ) != (eenheid.naam, eenheid.pakket.hash):
            return f"controle {eenheid.naam} hoort niet bij haar controlepakket"
        uitkomst = toets_lokale_verificatie(controle.get("raw"), eenheid.pakket)
        if uitkomst.soort is not None or uitkomst.uitkomst != "supported":
            return f"controle {eenheid.naam} draagt de interpretatie niet"
    return None


def speel_af(
    document: Mapping[str, Any], invoer: br.Vergelijkingsinvoer
) -> tuple[Bewijsregeloordeel | None, str]:
    """(oordeel, reden-als-niet) opnieuw uit het bewaarde document op dit materiaal.

    Status, vingerafdruk, binding en materiaal controleert het contract vooraf.
    """
    if not invoer.buren:
        if document.get("interpretation") is not None or document.get("controls"):
            return None, "beoordeling zonder buren draagt toch een interpretatie"
        return Bewijsregeloordeel(None), ""
    interpretatie, reden = _interpretatie(document, invoer)
    if interpretatie is None:
        return None, reden
    fout = _controlefout(document, interpretatie, invoer)
    if fout is not None:
        return None, fout
    return Bewijsregeloordeel(br.pas_regels_toe(interpretatie)), ""
