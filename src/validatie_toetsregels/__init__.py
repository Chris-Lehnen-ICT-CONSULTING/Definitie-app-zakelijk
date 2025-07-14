"""Validatie toetsregels module voor kwaliteitscontrole.

Dit module bevat legacy functionaliteit voor het laden en
toepassen van validatie regels op gegenereerde definities.
"""

# Importeer functie voor het laden van JSON regel IDs
from .validator import laad_json_ids

# Exporteer publieke interface (corrigeer typo in origineel)
__all__ = ["laad_json_ids"]