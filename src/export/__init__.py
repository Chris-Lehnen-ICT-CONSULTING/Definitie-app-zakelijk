"""Export module voor het exporteren van definities naar verschillende formaten.

Biedt functionaliteit voor het exporteren van gegenereerde definities
naar tekstbestanden en andere formaten.
"""

# Importeer export functionaliteit
from .export_txt import exporteer_naar_txt  # TXT export functie

# Maakt de functie beschikbaar via: from export import exporteer_naar_txt
# Zorgt dat export/ als net package fungeert
# Draagt bij aan duidelijke projectstructuur en IDE-autocompletion

# Exporteer publieke interface
__all__ = ["exporteer_naar_txt"]