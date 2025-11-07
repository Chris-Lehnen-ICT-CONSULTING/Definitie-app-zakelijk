"""
Validation package voor DefinitieAgent.

Biedt uitgebreide input validatie, content sanering, en Nederlandse tekst validatie.
Zorgt voor veilige en correcte verwerking van alle gebruikersinvoer en gegenereerde content.
"""

# Importeer Nederlandse tekst validatie voor taalkundige correctheid
from .dutch_text_validator import (
    DutchTextType,  # Type Nederlandse tekst (formeel, informeel)
)
from .dutch_text_validator import DutchTextValidator  # Validator voor Nederlandse tekst
from .dutch_text_validator import (
    DutchValidationResult,  # Resultaat van Nederlandse validatie
)
from .dutch_text_validator import (
    dutch_text_decorator,  # Decorator voor Nederlandse validatie
)
from .dutch_text_validator import (
    get_dutch_validator,  # Factory voor Nederlandse validator
)
from .dutch_text_validator import (
    suggest_dutch_improvements,  # Suggesties voor verbetering
)
from .dutch_text_validator import (
    validate_dutch_text,  # Nederlandse tekst validatie functie
)
from .dutch_text_validator import (
    ValidationSeverity as DutchValidationSeverity,  # Ernst niveau voor Nederlandse validatie
)

# Importeer input validatie componenten voor gebruikersinvoer controle
from .input_validator import (
    InputValidationResult,  # Resultaat van input validatie actie
)
from .input_validator import InputValidator  # Hoofdklasse voor input validatie
from .input_validator import ValidationRule  # Individuele validatie regel
from .input_validator import ValidationSchema  # Schema definitie voor validatie regels
from .input_validator import ValidationSeverity  # Ernst niveau van validatie issues
from .input_validator import (
    ValidationType,  # Type van validatie (tekst, numeriek, etc.)
)
from .input_validator import get_input_errors  # Fout extractie functie
from .input_validator import get_validator  # Factory functie voor validator instanties
from .input_validator import is_valid_input  # Boolean validatie check
from .input_validator import validate_input  # Directe validatie functie
from .input_validator import (
    validate_input_decorator,  # Decorator voor automatische validatie
)

# Importeer content sanering componenten voor veilige content verwerking
from .sanitizer import ContentSanitizer  # Hoofdklasse voor content sanering
from .sanitizer import ContentType  # Type content voor context-specifieke sanering
from .sanitizer import SanitizationLevel  # Niveau van sanering (basic, strict, etc.)
from .sanitizer import SanitizationResult  # Resultaat van sanering proces
from .sanitizer import SanitizationRule  # Individuele sanering regel
from .sanitizer import detect_threats  # Bedreiging detectie functie
from .sanitizer import get_sanitizer  # Factory voor sanitizer instanties
from .sanitizer import sanitize_content  # Algemene content sanering functie
from .sanitizer import sanitize_for_definition  # Definitie-specifieke sanering
from .sanitizer import sanitize_input_decorator  # Decorator voor automatische sanering
from .sanitizer import sanitize_user_input  # Gebruikersinvoer sanering

# Exporteer publieke interface - alle validatie en sanering componenten
__all__ = [
    # Content sanering - veilige content verwerking
    "ContentSanitizer",  # Hoofdklasse voor sanering
    "ContentType",  # Content type voor context
    "DutchTextType",  # Type Nederlandse tekst
    # Nederlandse tekst validatie - taalkundige correctheid
    "DutchTextValidator",  # Nederlandse tekst validator
    "DutchValidationResult",  # Nederlandse validatie resultaat
    "DutchValidationSeverity",  # Ernst niveau Nederlandse validatie
    "InputValidationResult",  # Input validatie resultaat container
    # Input validatie - gebruikersinvoer controle
    "InputValidator",  # Hoofdklasse voor input validatie
    "SanitizationLevel",  # Niveau van sanering proces
    "SanitizationResult",  # Sanering resultaat container
    "SanitizationRule",  # Individuele sanering regel
    "ValidationRule",  # Individuele validatie regel
    "ValidationSchema",  # Schema voor validatie regels
    "ValidationSeverity",  # Ernst niveau van validatie issues
    "ValidationType",  # Type van validatie proces
    "detect_threats",  # Bedreiging detectie
    "dutch_text_decorator",  # Decorator Nederlandse validatie
    "get_dutch_validator",  # Factory Nederlandse validator
    "get_input_errors",  # Fout extractie functie
    "get_sanitizer",  # Factory voor sanitizer instanties
    "get_validator",  # Factory voor validator instanties
    "is_valid_input",  # Boolean validatie check
    "sanitize_content",  # Algemene content sanering
    "sanitize_for_definition",  # Definitie-specifieke sanering
    "sanitize_input_decorator",  # Decorator voor auto sanering
    "sanitize_user_input",  # Gebruikersinvoer sanering
    "suggest_dutch_improvements",  # Verbeteringsuggesties
    "validate_dutch_text",  # Nederlandse tekst validatie
    "validate_input",  # Directe input validatie
    "validate_input_decorator",  # Decorator voor auto validatie
]

# Versie informatie en package metadata
__version__ = "1.0.0"  # Huidige versie van validation package
__author__ = "DefinitieAgent Development Team"  # Ontwikkelingsteam
__description__ = "Uitgebreid validatie en sanering systeem voor Nederlandse overheids definities"  # Package beschrijving
