"""Web lookup module voor het zoeken van definities in externe bronnen.

Biedt functionaliteit voor het zoeken naar definities in verschillende
online bronnen zoals Wikipedia, overheid.nl, wetten.nl, etc.
"""

# Importeer alle zoekfuncties uit lookup module
from .lookup import (
    zoek_definitie_op_wikipedia,      # Wikipedia zoekfunctie
    zoek_definitie_op_overheidnl,     # Overheid.nl zoekfunctie
    zoek_definitie_op_wettennl,       # Wetten.nl zoekfunctie
    zoek_definitie_op_wiktionary,     # Wiktionary zoekfunctie
    zoek_definitie_op_ensie,          # Ensie.nl zoekfunctie
    zoek_definitie_op_strafrechtketen, # Strafrechtketen zoekfunctie
    zoek_definitie_op_kamerstukken,   # Kamerstukken zoekfunctie
    zoek_definitie_op_iate,           # IATE terminologie database
    zoek_definitie_combinatie,        # Gecombineerde zoekfunctie
    is_plurale_tantum,                # Plurale tantum checker
)

# Exporteer publieke interface - alle zoekfuncties
__all__ = [
    "zoek_definitie_op_wikipedia",      # Wikipedia zoeken
    "zoek_definitie_op_overheidnl",     # Overheid.nl zoeken
    "zoek_definitie_op_wettennl",       # Wetten.nl zoeken
    "zoek_definitie_op_wiktionary",     # Wiktionary zoeken
    "zoek_definitie_op_ensie",          # Ensie.nl zoeken
    "zoek_definitie_op_strafrechtketen", # Strafrechtketen zoeken
    "zoek_definitie_op_kamerstukken",   # Kamerstukken zoeken
    "zoek_definitie_op_iate",           # IATE terminologie zoeken
    "zoek_definitie_combinatie",        # Gecombineerd zoeken
    "is_plurale_tantum",                # Grammatica checker
]
