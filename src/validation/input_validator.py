"""
Comprehensive input validation framework for DefinitieAgent.
Provides schema-based validation, type checking, and business rule enforcement.
"""

import re
import logging
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Validation error severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationType(Enum):
    """Types of validation checks."""

    REQUIRED = "required"
    TYPE = "type"
    LENGTH = "length"
    PATTERN = "pattern"
    RANGE = "range"
    ENUM = "enum"
    CUSTOM = "custom"
    BUSINESS_RULE = "business_rule"


@dataclass
class ValidationRule:
    """Definition of a validation rule."""

    field_name: str
    validation_type: ValidationType
    severity: ValidationSeverity = ValidationSeverity.ERROR
    message: str = ""

    # Type validation
    expected_type: Optional[type] = None

    # Length validation
    min_length: Optional[int] = None
    max_length: Optional[int] = None

    # Pattern validation
    pattern: Optional[str] = None
    pattern_flags: int = 0

    # Range validation
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None

    # Enum validation
    allowed_values: Optional[List[Any]] = None

    # Custom validation
    custom_validator: Optional[Callable[[Any], bool]] = None

    # Business rule validation
    business_rule: Optional[Callable[[Dict[str, Any]], bool]] = None


@dataclass
class ValidationResult:
    """Result of a validation check."""

    field_name: str
    validation_type: ValidationType
    severity: ValidationSeverity
    passed: bool
    message: str
    actual_value: Any = None
    expected_value: Any = None


class ValidationSchema:
    """Schema for validating structured data."""

    def __init__(self, schema_name: str):
        self.schema_name = schema_name
        self.rules: List[ValidationRule] = []
        self.field_rules: Dict[str, List[ValidationRule]] = {}
        self.global_rules: List[ValidationRule] = []

    def add_rule(self, rule: ValidationRule):
        """Add a validation rule to the schema."""
        self.rules.append(rule)

        if rule.field_name == "*":  # Global rule
            self.global_rules.append(rule)
        else:
            if rule.field_name not in self.field_rules:
                self.field_rules[rule.field_name] = []
            self.field_rules[rule.field_name].append(rule)

    def required(self, field_name: str, message: str = ""):
        """Add required field validation."""
        rule = ValidationRule(
            field_name=field_name,
            validation_type=ValidationType.REQUIRED,
            severity=ValidationSeverity.ERROR,
            message=message or f"Field '{field_name}' is required",
        )
        self.add_rule(rule)
        return self

    def type_check(self, field_name: str, expected_type: type, message: str = ""):
        """Add type validation."""
        rule = ValidationRule(
            field_name=field_name,
            validation_type=ValidationType.TYPE,
            severity=ValidationSeverity.ERROR,
            expected_type=expected_type,
            message=message
            or f"Field '{field_name}' must be of type {expected_type.__name__}",
        )
        self.add_rule(rule)
        return self

    def length(
        self,
        field_name: str,
        min_length: int = None,
        max_length: int = None,
        message: str = "",
    ):
        """Add length validation."""
        rule = ValidationRule(
            field_name=field_name,
            validation_type=ValidationType.LENGTH,
            severity=ValidationSeverity.ERROR,
            min_length=min_length,
            max_length=max_length,
            message=message
            or f"Field '{field_name}' length must be between {min_length} and {max_length}",
        )
        self.add_rule(rule)
        return self

    def pattern(self, field_name: str, pattern: str, flags: int = 0, message: str = ""):
        """Add pattern validation."""
        rule = ValidationRule(
            field_name=field_name,
            validation_type=ValidationType.PATTERN,
            severity=ValidationSeverity.ERROR,
            pattern=pattern,
            pattern_flags=flags,
            message=message or f"Field '{field_name}' does not match required pattern",
        )
        self.add_rule(rule)
        return self

    def range_check(
        self,
        field_name: str,
        min_value: Union[int, float] = None,
        max_value: Union[int, float] = None,
        message: str = "",
    ):
        """Add range validation."""
        rule = ValidationRule(
            field_name=field_name,
            validation_type=ValidationType.RANGE,
            severity=ValidationSeverity.ERROR,
            min_value=min_value,
            max_value=max_value,
            message=message
            or f"Field '{field_name}' must be between {min_value} and {max_value}",
        )
        self.add_rule(rule)
        return self

    def enum(self, field_name: str, allowed_values: List[Any], message: str = ""):
        """Add enum validation."""
        rule = ValidationRule(
            field_name=field_name,
            validation_type=ValidationType.ENUM,
            severity=ValidationSeverity.ERROR,
            allowed_values=allowed_values,
            message=message or f"Field '{field_name}' must be one of: {allowed_values}",
        )
        self.add_rule(rule)
        return self

    def custom(
        self, field_name: str, validator: Callable[[Any], bool], message: str = ""
    ):
        """Add custom validation."""
        rule = ValidationRule(
            field_name=field_name,
            validation_type=ValidationType.CUSTOM,
            severity=ValidationSeverity.ERROR,
            custom_validator=validator,
            message=message or f"Field '{field_name}' failed custom validation",
        )
        self.add_rule(rule)
        return self

    def business_rule(
        self,
        rule_name: str,
        validator: Callable[[Dict[str, Any]], bool],
        message: str = "",
    ):
        """Add business rule validation."""
        rule = ValidationRule(
            field_name=rule_name,
            validation_type=ValidationType.BUSINESS_RULE,
            severity=ValidationSeverity.ERROR,
            business_rule=validator,
            message=message or f"Business rule '{rule_name}' validation failed",
        )
        self.add_rule(rule)
        return self


class InputValidator:
    """Main input validation system."""

    def __init__(self):
        self.schemas: Dict[str, ValidationSchema] = {}
        self.validation_history: List[Dict[str, Any]] = []
        self.load_built_in_schemas()

    def load_built_in_schemas(self):
        """Load built-in validation schemas."""
        # Definition generation schema
        definition_schema = ValidationSchema("definition_generation")
        definition_schema.required(
            "begrip", "Term is required for definition generation"
        ).type_check("begrip", str).length(
            "begrip", min_length=1, max_length=200
        ).pattern(
            "begrip",
            r"^[a-zA-Z0-9\s\-_()]+$",
            message="Term contains invalid characters",
        ).required(
            "context_dict"
        ).type_check(
            "context_dict", dict
        ).custom(
            "context_dict",
            self._validate_context_dict,
            "Invalid context dictionary structure",
        )

        self.schemas["definition_generation"] = definition_schema

        # User input schema
        user_input_schema = ValidationSchema("user_input")
        user_input_schema.required(
            "voorsteller", "Proposer name is required"
        ).type_check("voorsteller", str).length(
            "voorsteller", min_length=1, max_length=100
        ).pattern(
            "voorsteller",
            r"^[a-zA-Z\s\-']+$",
            message="Proposer name contains invalid characters",
        ).type_check(
            "datum", str
        ).pattern(
            "datum", r"^\d{4}-\d{2}-\d{2}$", message="Date must be in YYYY-MM-DD format"
        ).type_check(
            "ketenpartners", list
        ).custom(
            "ketenpartners",
            self._validate_ketenpartners,
            "Invalid ketenpartners format",
        )

        self.schemas["user_input"] = user_input_schema

        # Context validation schema
        context_schema = ValidationSchema("context_validation")
        context_schema.type_check("organisatorisch", list).type_check(
            "juridisch", list
        ).type_check("wettelijk", list).custom(
            "organisatorisch",
            self._validate_organisatorisch_context,
            "Invalid organisatorisch context",
        ).custom(
            "juridisch", self._validate_juridisch_context, "Invalid juridisch context"
        ).custom(
            "wettelijk", self._validate_wettelijk_context, "Invalid wettelijk context"
        )

        self.schemas["context_validation"] = context_schema

    def _validate_context_dict(self, context_dict: Dict[str, Any]) -> bool:
        """Validate context dictionary structure."""
        if not isinstance(context_dict, dict):
            return False

        required_keys = ["organisatorisch", "juridisch", "wettelijk"]
        for key in required_keys:
            if key not in context_dict:
                return False
            if not isinstance(context_dict[key], list):
                return False

        return True

    def _validate_ketenpartners(self, ketenpartners: List[str]) -> bool:
        """Validate ketenpartners list."""
        if not isinstance(ketenpartners, list):
            return False

        valid_partners = {
            "Openbaar Ministerie",
            "Politie",
            "Reclassering",
            "DJI",
            "Rechtspraak",
            "CJIB",
            "Halt",
            "Raad voor de Kinderbescherming",
            "Veiligheidshuizen",
            "Slachtofferhulp",
            "Anders",
        }

        for partner in ketenpartners:
            if not isinstance(partner, str) or partner not in valid_partners:
                return False

        return True

    def _validate_organisatorisch_context(self, context: List[str]) -> bool:
        """Validate organisatorisch context."""
        if not isinstance(context, list):
            return False

        valid_contexts = {
            "Strafrechtketen",
            "Civiele rechtketen",
            "Bestuursrechtketen",
            "Handhaving",
            "Toezicht",
            "Preventie",
            "Nazorg",
            "Anders",
        }

        for ctx in context:
            if not isinstance(ctx, str) or ctx not in valid_contexts:
                return False

        return True

    def _validate_juridisch_context(self, context: List[str]) -> bool:
        """Validate juridisch context."""
        if not isinstance(context, list):
            return False

        valid_contexts = {
            "Strafrecht",
            "Civiel recht",
            "Bestuursrecht",
            "Europees recht",
            "Internationaal recht",
            "Grondwet",
            "Verdragen",
            "Anders",
        }

        for ctx in context:
            if not isinstance(ctx, str) or ctx not in valid_contexts:
                return False

        return True

    def _validate_wettelijk_context(self, context: List[str]) -> bool:
        """Validate wettelijk context."""
        if not isinstance(context, list):
            return False

        # Allow any string for wettelijk context as it's more flexible
        for ctx in context:
            if not isinstance(ctx, str):
                return False
            # Check for reasonable length and content
            if len(ctx) > 500 or len(ctx.strip()) == 0:
                return False

        return True

    def validate(
        self, data: Dict[str, Any], schema_name: str
    ) -> List[ValidationResult]:
        """Validate data against a schema."""
        if schema_name not in self.schemas:
            raise ValueError(f"Schema '{schema_name}' not found")

        schema = self.schemas[schema_name]
        results = []

        # Track validation attempt
        validation_attempt = {
            "timestamp": datetime.now().isoformat(),
            "schema_name": schema_name,
            "data_keys": list(data.keys()) if isinstance(data, dict) else [],
            "validation_count": len(schema.rules),
        }

        try:
            # Validate each field
            for field_name, rules in schema.field_rules.items():
                field_value = data.get(field_name)

                for rule in rules:
                    result = self._validate_single_rule(field_value, rule, data)
                    results.append(result)

            # Validate global rules
            for rule in schema.global_rules:
                result = self._validate_single_rule(data, rule, data)
                results.append(result)

            # Update validation history
            validation_attempt["results_count"] = len(results)
            validation_attempt["errors_count"] = sum(
                1
                for r in results
                if not r.passed and r.severity == ValidationSeverity.ERROR
            )
            validation_attempt["warnings_count"] = sum(
                1
                for r in results
                if not r.passed and r.severity == ValidationSeverity.WARNING
            )
            validation_attempt["success"] = all(
                r.passed
                or r.severity in [ValidationSeverity.INFO, ValidationSeverity.WARNING]
                for r in results
            )

        except Exception as e:
            validation_attempt["error"] = str(e)
            validation_attempt["success"] = False
            logger.error(f"Validation error: {e}")

        # Store validation history (keep last 1000 entries)
        self.validation_history.append(validation_attempt)
        if len(self.validation_history) > 1000:
            self.validation_history.pop(0)

        return results

    def _validate_single_rule(
        self, value: Any, rule: ValidationRule, full_data: Dict[str, Any]
    ) -> ValidationResult:
        """Validate a single rule."""
        try:
            if rule.validation_type == ValidationType.REQUIRED:
                passed = value is not None and value != "" and value != []

            elif rule.validation_type == ValidationType.TYPE:
                passed = value is None or isinstance(value, rule.expected_type)

            elif rule.validation_type == ValidationType.LENGTH:
                if value is None:
                    passed = True
                else:
                    length = len(value) if hasattr(value, "__len__") else 0
                    passed = True
                    if rule.min_length is not None and length < rule.min_length:
                        passed = False
                    if rule.max_length is not None and length > rule.max_length:
                        passed = False

            elif rule.validation_type == ValidationType.PATTERN:
                if value is None:
                    passed = True
                else:
                    pattern = re.compile(rule.pattern, rule.pattern_flags)
                    passed = bool(pattern.match(str(value)))

            elif rule.validation_type == ValidationType.RANGE:
                if value is None:
                    passed = True
                else:
                    passed = True
                    if rule.min_value is not None and value < rule.min_value:
                        passed = False
                    if rule.max_value is not None and value > rule.max_value:
                        passed = False

            elif rule.validation_type == ValidationType.ENUM:
                passed = value is None or value in rule.allowed_values

            elif rule.validation_type == ValidationType.CUSTOM:
                if rule.custom_validator:
                    passed = rule.custom_validator(value)
                else:
                    passed = True

            elif rule.validation_type == ValidationType.BUSINESS_RULE:
                if rule.business_rule:
                    passed = rule.business_rule(full_data)
                else:
                    passed = True
            else:
                passed = True

            return ValidationResult(
                field_name=rule.field_name,
                validation_type=rule.validation_type,
                severity=rule.severity,
                passed=passed,
                message=(
                    rule.message
                    if not passed
                    else f"Validation passed for {rule.field_name}"
                ),
                actual_value=value,
            )

        except Exception as e:
            logger.error(f"Error validating rule {rule.field_name}: {e}")
            return ValidationResult(
                field_name=rule.field_name,
                validation_type=rule.validation_type,
                severity=ValidationSeverity.ERROR,
                passed=False,
                message=f"Validation error: {str(e)}",
                actual_value=value,
            )

    def is_valid(self, data: Dict[str, Any], schema_name: str) -> bool:
        """Check if data is valid according to schema."""
        results = self.validate(data, schema_name)
        return all(
            r.passed
            or r.severity in [ValidationSeverity.INFO, ValidationSeverity.WARNING]
            for r in results
        )

    def get_errors(
        self, data: Dict[str, Any], schema_name: str
    ) -> List[ValidationResult]:
        """Get only validation errors."""
        results = self.validate(data, schema_name)
        return [
            r
            for r in results
            if not r.passed and r.severity == ValidationSeverity.ERROR
        ]

    def get_warnings(
        self, data: Dict[str, Any], schema_name: str
    ) -> List[ValidationResult]:
        """Get only validation warnings."""
        results = self.validate(data, schema_name)
        return [
            r
            for r in results
            if not r.passed and r.severity == ValidationSeverity.WARNING
        ]

    def add_schema(self, schema: ValidationSchema):
        """Add a custom validation schema."""
        self.schemas[schema.schema_name] = schema

    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics."""
        if not self.validation_history:
            return {"total_validations": 0}

        total_validations = len(self.validation_history)
        successful_validations = sum(
            1 for v in self.validation_history if v.get("success", False)
        )

        # Schema usage statistics
        schema_usage = {}
        for validation in self.validation_history:
            schema_name = validation.get("schema_name", "unknown")
            schema_usage[schema_name] = schema_usage.get(schema_name, 0) + 1

        # Error statistics
        total_errors = sum(v.get("errors_count", 0) for v in self.validation_history)
        total_warnings = sum(
            v.get("warnings_count", 0) for v in self.validation_history
        )

        return {
            "total_validations": total_validations,
            "successful_validations": successful_validations,
            "success_rate": (
                successful_validations / total_validations
                if total_validations > 0
                else 0
            ),
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "schema_usage": schema_usage,
            "most_used_schema": (
                max(schema_usage.items(), key=lambda x: x[1])[0]
                if schema_usage
                else None
            ),
        }

    def export_validation_report(self, filename: Optional[str] = None) -> str:
        """Export validation report to file."""
        if filename is None:
            filename = (
                f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )

        filepath = Path("reports") / filename
        filepath.parent.mkdir(exist_ok=True)

        report = {
            "generated_at": datetime.now().isoformat(),
            "statistics": self.get_validation_stats(),
            "schemas": {
                name: len(schema.rules) for name, schema in self.schemas.items()
            },
            "recent_validations": (
                self.validation_history[-100:]
                if len(self.validation_history) > 100
                else self.validation_history
            ),
        }

        with open(filepath, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return str(filepath)


# Global validator instance
_global_validator: Optional[InputValidator] = None


def get_validator() -> InputValidator:
    """Get or create global validator instance."""
    global _global_validator
    if _global_validator is None:
        _global_validator = InputValidator()
    return _global_validator


def validate_input(data: Dict[str, Any], schema_name: str) -> List[ValidationResult]:
    """Convenience function for input validation."""
    validator = get_validator()
    return validator.validate(data, schema_name)


def is_valid_input(data: Dict[str, Any], schema_name: str) -> bool:
    """Convenience function to check if input is valid."""
    validator = get_validator()
    return validator.is_valid(data, schema_name)


def get_input_errors(data: Dict[str, Any], schema_name: str) -> List[ValidationResult]:
    """Convenience function to get input errors."""
    validator = get_validator()
    return validator.get_errors(data, schema_name)


# Validation decorators
def validate_input_decorator(schema_name: str):
    """Decorator to validate function inputs."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Assume first argument is data to validate
            if args:
                data = args[0] if isinstance(args[0], dict) else kwargs
            else:
                data = kwargs

            errors = get_input_errors(data, schema_name)
            if errors:
                error_messages = [
                    f"{error.field_name}: {error.message}" for error in errors
                ]
                raise ValueError(
                    f"Input validation failed: {'; '.join(error_messages)}"
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator


async def test_input_validator():
    """Test the input validation system."""
    print("🧪 Testing Input Validation System")
    print("=" * 35)

    validator = get_validator()

    # Test valid definition generation data
    valid_data = {
        "begrip": "identiteitsbehandeling",
        "context_dict": {
            "organisatorisch": ["Strafrechtketen"],
            "juridisch": ["Strafrecht"],
            "wettelijk": ["Wetboek van Strafrecht"],
        },
    }

    results = validator.validate(valid_data, "definition_generation")
    passed = all(r.passed for r in results)
    print(f"✅ Valid data test: {'PASSED' if passed else 'FAILED'}")

    # Test invalid data
    invalid_data = {
        "begrip": "",  # Empty term
        "context_dict": {
            "organisatorisch": ["Invalid Context"],  # Invalid context
            "juridisch": [],
            "wettelijk": [],
        },
    }

    results = validator.validate(invalid_data, "definition_generation")
    errors = [
        r for r in results if not r.passed and r.severity == ValidationSeverity.ERROR
    ]
    print(f"❌ Invalid data test: {len(errors)} errors found")

    # Test user input validation
    user_data = {
        "voorsteller": "Jan de Vries",
        "datum": "2025-07-09",
        "ketenpartners": ["Openbaar Ministerie", "Politie"],
    }

    results = validator.validate(user_data, "user_input")
    passed = all(r.passed for r in results)
    print(f"✅ User input test: {'PASSED' if passed else 'FAILED'}")

    # Show validation statistics
    stats = validator.get_validation_stats()
    print(f"📊 Total validations: {stats['total_validations']}")
    print(f"📊 Success rate: {stats['success_rate']:.1%}")
    print(f"📊 Total errors: {stats['total_errors']}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_input_validator())
