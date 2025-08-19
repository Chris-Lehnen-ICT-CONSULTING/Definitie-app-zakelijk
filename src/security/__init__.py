"""
Security package voor DefinitieAgent.

Biedt uitgebreide beveiligings middleware, bedreiging detectie, en request validatie.
Zorgt voor veilige verwerking van alle requests en bescherming tegen beveiligingsrisico's.
"""

# Importeer beveiligings middleware componenten voor request bescherming
from .security_middleware import (
    SecurityEvent,  # Container voor beveiligings gebeurtenissen
    SecurityLevel,  # Beveiligings niveau (low, medium, high, critical)
    SecurityMiddleware,  # Hoofdklasse voor beveiligings middleware
    ThreatType,  # Type van gedetecteerde bedreiging
    ValidationRequest,  # Request container voor validatie
    ValidationResponse,  # Response container na validatie
    get_security_middleware,  # Factory voor middleware instanties
    security_middleware_decorator,  # Decorator voor automatische beveiliging
)

# Exporteer publieke interface - alle beveiligings componenten
__all__ = [
    "SecurityEvent",  # Beveiligings gebeurtenis container
    "SecurityLevel",  # Beveiligings niveau enumeratie
    "SecurityMiddleware",  # Hoofdklasse beveiligings middleware
    "ThreatType",  # Bedreiging type classificatie
    "ValidationRequest",  # Request validatie container
    "ValidationResponse",  # Response validatie container
    "get_security_middleware",  # Factory voor middleware instanties
    "security_middleware_decorator",  # Decorator voor auto beveiliging
]

# Versie informatie en package metadata
__version__ = "1.0.0"  # Huidige versie van security package
__author__ = "DefinitieAgent Development Team"  # Ontwikkelingsteam
__description__ = "Beveiligings middleware en bedreiging detectie systeem voor Nederlandse overheids applicaties"  # Package beschrijving
