"""Constanten voor de RAG pipeline (DEF-365, DEF-371, DEF-376).

Collection types en rechtsgebieden — DRY bron voor UI en service laag.
"""

from __future__ import annotations

from typing import NamedTuple


class CollectionType(NamedTuple):
    """Beschrijving van een RAG collection type."""

    key: str
    label: str
    icon: str


COLLECTION_TYPES: tuple[CollectionType, ...] = (
    CollectionType("wetgeving", "Wetgeving", "\U0001f4dc"),
    CollectionType("kamerstukken", "Kamerstukken", "\U0001f4cb"),
    CollectionType("beleid", "Beleid", "\U0001f4d1"),
    CollectionType("keten", "Keten", "\U0001f517"),
    CollectionType("vrij", "Vrij", "\U0001f4c1"),
)

COLLECTION_TYPE_MAP: dict[str, CollectionType] = {ct.key: ct for ct in COLLECTION_TYPES}

RECHTSGEBIEDEN: dict[str, str] = {
    "strafrecht": "Strafrecht",
    "burgerlijk_recht": "Burgerlijk recht",
    "bestuursrecht": "Bestuursrecht",
    "staatsrecht": "Staatsrecht",
    "belastingrecht": "Belastingrecht",
    "ondernemingsrecht": "Ondernemingsrecht",
    "arbeidsrecht": "Arbeidsrecht",
    "europees_recht": "Europees recht",
    "internationaal_recht": "Internationaal recht",
    "migratierecht": "Migratierecht",
    "jeugdrecht": "Jeugdrecht",
    "vreemdelingenrecht": "Vreemdelingenrecht",
    "sanctierecht": "Sanctierecht",
    "penitentiair_recht": "Penitentiair recht",
    "familierecht": "Familierecht",
}


def _register_alias(lookup: dict[str, str], alias: str, key: str) -> None:
    """Registreer een lookup-alias met collision-detectie."""
    existing = lookup.get(alias)
    if existing is not None and existing != key:
        raise RuntimeError(
            f"Rechtsgebied lookup collision: '{alias}' mapt naar zowel "
            f"'{existing}' als '{key}'"
        )
    lookup[alias] = key


# Reverse-lookup: diverse varianten → genormaliseerde key
# Alleen lowercase entries — normaliseer_rechtsgebied() doet altijd .lower()
_RECHTSGEBIED_LOOKUP: dict[str, str] = {}
for _key, _label in RECHTSGEBIEDEN.items():
    _register_alias(_RECHTSGEBIED_LOOKUP, _key, _key)
    _register_alias(_RECHTSGEBIED_LOOKUP, _label.lower(), _key)

# Extra aliassen voor gangbare varianten
_register_alias(_RECHTSGEBIED_LOOKUP, "civiel recht", "burgerlijk_recht")
_register_alias(_RECHTSGEBIED_LOOKUP, "civiel_recht", "burgerlijk_recht")
_register_alias(_RECHTSGEBIED_LOOKUP, "privaatrecht", "burgerlijk_recht")

del _key, _label


def normaliseer_rechtsgebied(invoer: str | None) -> str | None:
    """Normaliseer vrije tekst naar een gestandaardiseerde rechtsgebied-key.

    Returns None als de invoer leeg is of het rechtsgebied niet herkend wordt.
    """
    if not invoer or not invoer.strip():
        return None
    return _RECHTSGEBIED_LOOKUP.get(invoer.strip().lower())
