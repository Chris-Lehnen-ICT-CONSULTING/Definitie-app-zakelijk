"""
Security package voor DefinitieAgent.

Biedt uitgebreide beveiligings middleware, bedreiging detectie, en request validatie.
Zorgt voor veilige verwerking van alle requests en bescherming tegen beveiligingsrisico's.
"""

# Importeer beveiligings middleware componenten voor request bescherming
from .security_middleware import (
    SecurityEvent,  # Container voor beveiligings gebeurtenissen
)
from .security_middleware import (
    SecurityLevel,  # Beveiligings niveau (low, medium, high, critical)
)
from .security_middleware import (
    SecurityMiddleware,  # Hoofdklasse voor beveiligings middleware
)
from .security_middleware import ThreatType  # Type van gedetecteerde bedreiging
from .security_middleware import ValidationRequest  # Request container voor validatie
from .security_middleware import ValidationResponse  # Response container na validatie
from .security_middleware import (
    get_security_middleware,  # Factory voor middleware instanties
)
from .security_middleware import (
    security_middleware_decorator,  # Decorator voor automatische beveiliging
)

# Exporteer publieke interface - alle beveiligings componenten
__all__ = [
    "SecurityMiddleware",  # Hoofdklasse beveiligings middleware
    "SecurityEvent",  # Beveiligings gebeurtenis container
    "SecurityLevel",  # Beveiligings niveau enumeratie
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
