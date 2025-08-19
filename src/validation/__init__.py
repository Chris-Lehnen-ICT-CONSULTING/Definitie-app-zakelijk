"""
Validation package voor DefinitieAgent.

Biedt uitgebreide input validatie, content sanering, en Nederlandse tekst validatie.
Zorgt voor veilige en correcte verwerking van alle gebruikersinvoer en gegenereerde content.
"""

# Importeer Nederlandse tekst validatie voor taalkundige correctheid
from .dutch_text_validator import (
    DutchTextType,  # Type Nederlandse tekst (formeel, informeel)
    DutchTextValidator,  # Validator voor Nederlandse tekst
    DutchValidationResult,  # Resultaat van Nederlandse validatie
    ValidationSeverity as DutchValidationSeverity,  # Ernst niveau voor Nederlandse validatie
    dutch_text_decorator,  # Decorator voor Nederlandse validatie
    get_dutch_validator,  # Factory voor Nederlandse validator
    suggest_dutch_improvements,  # Suggesties voor verbetering
    validate_dutch_text,  # Nederlandse tekst validatie functie
)

# Importeer input validatie componenten voor gebruikersinvoer controle
from .input_validator import (
    InputValidator,  # Hoofdklasse voor input validatie
    ValidationResult,  # Resultaat van validatie actie
    ValidationRule,  # Individuele validatie regel
    ValidationSchema,  # Schema definitie voor validatie regels
    ValidationSeverity,  # Ernst niveau van validatie issues
    ValidationType,  # Type van validatie (tekst, numeriek, etc.)
    get_input_errors,  # Fout extractie functie
    get_validator,  # Factory functie voor validator instanties
    is_valid_input,  # Boolean validatie check
    validate_input,  # Directe validatie functie
    validate_input_decorator,  # Decorator voor automatische validatie
)

# Importeer content sanering componenten voor veilige content verwerking
from .sanitizer import (
    ContentSanitizer,  # Hoofdklasse voor content sanering
    ContentType,  # Type content voor context-specifieke sanering
    SanitizationLevel,  # Niveau van sanering (basic, strict, etc.)
    SanitizationResult,  # Resultaat van sanering proces
    SanitizationRule,  # Individuele sanering regel
    detect_threats,  # Bedreiging detectie functie
    get_sanitizer,  # Factory voor sanitizer instanties
    sanitize_content,  # Algemene content sanering functie
    sanitize_for_definition,  # Definitie-specifieke sanering
    sanitize_input_decorator,  # Decorator voor automatische sanering
    sanitize_user_input,  # Gebruikersinvoer sanering
)

# Exporteer publieke interface - alle validatie en sanering componenten
__all__ = [
    # Input validatie - gebruikersinvoer controle
    "InputValidator",  # Hoofdklasse voor input validatie
    "ValidationSchema",  # Schema voor validatie regels
    "ValidationRule",  # Individuele validatie regel
    "ValidationResult",  # Validatie resultaat container
    "ValidationSeverity",  # Ernst niveau van validatie issues
    "ValidationType",  # Type van validatie proces
    "get_validator",  # Factory voor validator instanties
    "validate_input",  # Directe input validatie
    "is_valid_input",  # Boolean validatie check
    "get_input_errors",  # Fout extractie functie
    "validate_input_decorator",  # Decorator voor auto validatie
    # Content sanering - veilige content verwerking
    "ContentSanitizer",  # Hoofdklasse voor sanering
    "SanitizationResult",  # Sanering resultaat container
    "SanitizationLevel",  # Niveau van sanering proces
    "SanitizationRule",  # Individuele sanering regel
    "ContentType",  # Content type voor context
    "get_sanitizer",  # Factory voor sanitizer instanties
    "sanitize_content",  # Algemene content sanering
    "sanitize_for_definition",  # Definitie-specifieke sanering
    "sanitize_user_input",  # Gebruikersinvoer sanering
    "detect_threats",  # Bedreiging detectie
    "sanitize_input_decorator",  # Decorator voor auto sanering
    # Nederlandse tekst validatie - taalkundige correctheid
    "DutchTextValidator",  # Nederlandse tekst validator
    "DutchValidationResult",  # Nederlandse validatie resultaat
    "DutchTextType",  # Type Nederlandse tekst
    "DutchValidationSeverity",  # Ernst niveau Nederlandse validatie
    "get_dutch_validator",  # Factory Nederlandse validator
    "validate_dutch_text",  # Nederlandse tekst validatie
    "suggest_dutch_improvements",  # Verbeteringsuggesties
    "dutch_text_decorator",  # Decorator Nederlandse validatie
]

# Versie informatie en package metadata
__version__ = "1.0.0"  # Huidige versie van validation package
__author__ = "DefinitieAgent Development Team"  # Ontwikkelingsteam
__description__ = "Uitgebreid validatie en sanering systeem voor Nederlandse overheids definities"  # Package beschrijving
