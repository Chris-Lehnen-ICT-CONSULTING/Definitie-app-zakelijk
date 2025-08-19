"""
Ontologische categorieën voor definitie classificatie.

Dit bestand bevat de enum voor ontologische categorieën om circulaire
imports te voorkomen tussen services en database modules.
"""

from enum import Enum


class OntologischeCategorie(Enum):
    """Ontologische categorieën (van generation implementatie)."""

    TYPE = "type"
    PROCES = "proces"
    RESULTAAT = "resultaat"
    EXEMPLAAR = "exemplaar"
