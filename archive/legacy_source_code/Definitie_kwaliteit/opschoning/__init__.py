# opschoning/__init__.py

"""
De opschoning-module biedt één hoofdfunctie:
- opschonen(definitie: str, begrip: str) -> str
  Verwijdert alle verboden aanhefconstructies, dwingt hoofdletter en punt af.
"""

from .opschoning import opschonen  # exposeer de opschonen-functie

__all__ = ["opschonen"]
