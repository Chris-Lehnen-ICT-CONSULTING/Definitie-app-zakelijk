"""
Toetsregels pakket - Validatie regels voor definities.

Dit pakket bevat:
- regels/      : JSON configuratie bestanden per toetsregel
- validators/  : Python implementaties per toetsregel
- manager.py   : ToetsregelManager voor beheer
- loader.py    : Functies voor het laden van toetsregels
- adapter.py   : Adapter voor legacy systemen
"""

from .manager import ToetsregelManager, get_toetsregel_manager
from .loader import load_toetsregels, get_toetsregels

__all__ = [
    "ToetsregelManager",
    "get_toetsregel_manager",
    "load_toetsregels",
    "get_toetsregels",
]
