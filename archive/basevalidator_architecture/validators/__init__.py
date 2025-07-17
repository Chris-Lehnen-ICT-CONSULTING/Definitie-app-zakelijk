"""
Validators package voor AI Toetser.

Bevat basis validator klassen en registratie systeem
voor het valideren van AI gegenereerde content.
"""

# Importeer basis validator componenten voor AI content validatie
from .base_validator import (
    BaseValidator,        # Basis validator klasse voor extensie
    ValidationContext,    # Context informatie voor validatie
    ValidationOutput,     # Gestructureerde validatie output
    ValidationResult,     # Individueel validatie resultaat
    ValidationRegistry,   # Registratie systeem voor validators
    validation_registry   # Globale validator registry instantie
)

# Exporteer publieke interface - alle validator componenten
__all__ = [
    "BaseValidator",        # Basis validator voor inheritance
    "ValidationContext",    # Validatie context klasse
    "ValidationOutput",     # Output container klasse
    "ValidationResult",     # Resultaat container klasse
    "ValidationRegistry",   # Registry voor validator management
    "validation_registry"   # Pre-geïnstantieerde registry
]