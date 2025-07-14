"""Logs package voor DefinitieAgent applicatie logging.

Biedt gestructureerde logging functionaliteit voor definitie generatie,
toetsing processen, en applicatie gebeurtenissen.
"""

# Log package initializer voor DefinitieAgent logging systeem
from .log_definitie import get_logger, log_definitie, parse_toetsing_regels  # Logging functionaliteit

# Exporteer publieke interface - alle logging componenten
__all__ = [
    "get_logger",            # Factory functie voor logger instanties
    "log_definitie",         # Specifieke logging voor definitie processen
    "parse_toetsing_regels", # Parser voor toetsing regel logging
]
