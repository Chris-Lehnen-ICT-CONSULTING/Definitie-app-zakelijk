"""
ai_toetser package voor DefinitieAgent.

Publieke API:
    Toetser         – OO-wrapper met `.is_verboden()` functionaliteit
    toets_definitie – functie basis voor definitie-toetsing tegen verboden woorden
    ModularToetser  – Modulaire implementatie van de toetser

Het package gebruikt een volledig modulaire architectuur met JSON configuratie
en Python validators voor maximale flexibiliteit en onderhoudbaarheid.
"""

# Importeer hoofdklasse voor AI toetsing functionaliteit
from .toetser import Toetser  # OO-wrapper klasse voor verboden woorden toetsing

# Importeer van nieuwe modulaire architectuur
from .modular_toetser import (
    toets_definitie,
    ModularToetser,
)  # Modulaire toetser implementatie

# Exporteer publieke interface - alle toetsing componenten
__all__ = [
    "Toetser",
    "toets_definitie",
    "ModularToetser",
]  # Beschikbare klassen en functies
