"""
Validation package for DefinitieAgent.
Provides comprehensive input validation, sanitization, and Dutch text validation.
"""

from .input_validator import (
    InputValidator,
    ValidationSchema,
    ValidationRule,
    ValidationResult,
    ValidationSeverity,
    ValidationType,
    get_validator,
    validate_input,
    is_valid_input,
    get_input_errors,
    validate_input_decorator
)

from .sanitizer import (
    ContentSanitizer,
    SanitizationResult,
    SanitizationLevel,
    SanitizationRule,
    ContentType,
    get_sanitizer,
    sanitize_content,
    sanitize_for_definition,
    sanitize_user_input,
    detect_threats,
    sanitize_input_decorator
)

from .dutch_text_validator import (
    DutchTextValidator,
    DutchValidationResult,
    DutchTextType,
    ValidationSeverity as DutchValidationSeverity,
    get_dutch_validator,
    validate_dutch_text,
    suggest_dutch_improvements,
    dutch_text_decorator
)

__all__ = [
    # Input validation
    "InputValidator",
    "ValidationSchema",
    "ValidationRule",
    "ValidationResult",
    "ValidationSeverity",
    "ValidationType",
    "get_validator",
    "validate_input",
    "is_valid_input",
    "get_input_errors",
    "validate_input_decorator",
    
    # Sanitization
    "ContentSanitizer",
    "SanitizationResult",
    "SanitizationLevel",
    "SanitizationRule",
    "ContentType",
    "get_sanitizer",
    "sanitize_content",
    "sanitize_for_definition",
    "sanitize_user_input",
    "detect_threats",
    "sanitize_input_decorator",
    
    # Dutch text validation
    "DutchTextValidator",
    "DutchValidationResult",
    "DutchTextType",
    "DutchValidationSeverity",
    "get_dutch_validator",
    "validate_dutch_text",
    "suggest_dutch_improvements",
    "dutch_text_decorator"
]

# Version info
__version__ = "1.0.0"
__author__ = "DefinitieAgent Development Team"
__description__ = "Comprehensive validation and sanitization system for Dutch government definitions"
