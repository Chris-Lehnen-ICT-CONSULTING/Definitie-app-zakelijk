"""Constanten voor de RAG pipeline (DEF-365, DEF-371, DEF-376, DEF-377).

Collection types — DRY bron voor UI en service laag.
Rechtsgebied-logica leeft in domain.rechtsgebieden (DEF-377: circulaire import fix).
"""

from __future__ import annotations

from typing import NamedTuple

from domain.rechtsgebieden import RECHTSGEBIEDEN, normaliseer_rechtsgebied


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

__all__ = [
    "COLLECTION_TYPES",
    "COLLECTION_TYPE_MAP",
    "RECHTSGEBIEDEN",
    "CollectionType",
    "normaliseer_rechtsgebied",
]
