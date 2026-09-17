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


# DEF-751: de elf waarden die de CHECK-constraint op `definities.categorie`
# toestaat (schema.sql) — de vier generatiecategorieën plus de zeven
# opslagcodes uit eerdere imports. Hoofdlettergevoelig, zoals de CHECK.
OPSLAGCATEGORIEEN: tuple[str, ...] = (
    *(categorie.value for categorie in OntologischeCategorie),
    "ENT",
    "ACT",
    "REL",
    "ATT",
    "AUT",
    "STA",
    "OTH",
)
