"""Legacy definitie generator module.

Dit module biedt backwards compatibility voor oudere
definitie generatie functionaliteit.
"""

# Importeer legacy generatie functie
from .generator import genereer_definitie

# Exporteer publieke interface
__all__ = ["genereer_definitie"]
