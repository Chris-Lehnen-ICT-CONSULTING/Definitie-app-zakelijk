"""
ai_toetser package voor DefinitieAgent.

Publieke API:
    Toetser         – OO-wrapper met `.is_verboden()` functionaliteit
    toets_definitie – functie basis voor definitie-toetsing tegen verboden woorden

Het package gebruikt nu een modulaire architectuur maar behoudt achterwaartse compatibiliteit.
De oude monolithische core.py is nog steeds beschikbaar, maar de nieuwe modular_toetser.py
biedt dezelfde API met betere onderhoudbaarheid en flexibiliteit.
"""

# Importeer hoofdklasse voor AI toetsing functionaliteit
from .toetser import Toetser  # OO-wrapper klasse voor verboden woorden toetsing

# Importeer van nieuwe modulaire architectuur met achterwaartse compatibiliteit
try:
    # Probeer nieuwe modulaire implementatie te laden
    from .modular_toetser import toets_definitie, ModularToetser  # Modulaire toetser implementatie
    
    # Importeer ook enhanced versie met rich validation
    from .enhanced_toetser import EnhancedModularToetser, validate_definitie_rich
    from .models import ToetsregelValidationResult, RichValidationOutput, RuleViolation
except ImportError:
    # Fallback naar oude implementatie als modulaire versie faalt
    from .core import toets_definitie  # Legacy toets_definitie functie
    ModularToetser = None  # Modulaire versie niet beschikbaar
    EnhancedModularToetser = None
    validate_definitie_rich = None
    ToetsregelValidationResult = None

# Exporteer publieke interface - alle toetsing componenten
__all__ = [
    "Toetser", 
    "toets_definitie", 
    "ModularToetser",
    "EnhancedModularToetser",
    "validate_definitie_rich",
    "ToetsregelValidationResult",
    "RichValidationOutput",
    "RuleViolation"
]  # Beschikbare klassen en functies
