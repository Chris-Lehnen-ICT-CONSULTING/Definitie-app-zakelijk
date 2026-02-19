"""Constanten voor de RAG pipeline (DEF-365).

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

RECHTSGEBIEDEN: tuple[str, ...] = (
    "strafrecht",
    "civiel recht",
    "bestuursrecht",
    "staatsrecht",
    "belastingrecht",
)
