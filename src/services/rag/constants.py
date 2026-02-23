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

# Geldige bron_type waarden voor rag_chunks.bron_type.
# Let op: dit is een aparte taxonomie van de `externe_bronnen` tabel
# (schema.sql CHECK: 'database', 'api', 'file', 'manual') — die tabel
# beschrijft externe datakoppelingen, niet RAG-brondocumenten.
BRON_TYPES: tuple[str, ...] = ("wetgeving", "website", "pdf", "api")

# DEF-379: mapping van collection type key naar bron_type voor rag_chunks.
# Alleen "wetgeving" heeft een directe equivalent in BRON_TYPES.
# Overige types (kamerstukken, beleid, keten, vrij) geven None terug —
# bron_type blijft dan NULL in de database.
COLLECTION_TYPE_TO_BRON_TYPE: dict[str, str | None] = {
    "wetgeving": "wetgeving",
    "kamerstukken": None,
    "beleid": None,
    "keten": None,
    "vrij": None,
}

__all__ = [
    "BRON_TYPES",
    "COLLECTION_TYPES",
    "COLLECTION_TYPE_MAP",
    "COLLECTION_TYPE_TO_BRON_TYPE",
    "RECHTSGEBIEDEN",
    "CollectionType",
    "normaliseer_rechtsgebied",
]
