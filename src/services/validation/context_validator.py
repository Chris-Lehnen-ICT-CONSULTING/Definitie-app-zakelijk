"""
Context Validator - Validation service for context data.

Provides centralized validation for all context operations,
ensuring data integrity and business rule compliance.
"""

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """Represents a validation error."""

    field: str
    message: str
    severity: str  # "error", "warning", "info"
    suggestion: str | None = None


class ContextValidator:
    """
    Centralized context validation service.

    Validates context data according to business rules and data integrity requirements.
    """

    # Maximum lengths for custom input (US-042 requirement)
    MAX_CUSTOM_LENGTH = 200
    MAX_ITEMS_PER_FIELD = 10

    # Valid predefined values
    VALID_ORGANISATIES = {
        "OM",
        "ZM",
        "Reclassering",
        "DJI",
        "NP",
        "Justid",
        "KMAR",
        "FIOD",
        "CJIB",
        "Strafrechtketen",
        "Migratieketen",
        "Justitie en Veiligheid",
    }

    VALID_JURIDISCH = {
        "Strafrecht",
        "Civiel recht",
        "Bestuursrecht",
        "Internationaal recht",
        "Europees recht",
        "Migratierecht",
    }

    VALID_WETTELIJK = {
        "Wetboek van Strafvordering (huidige versie)",
        "Wetboek van strafvordering (nieuwe versie)",
        "Wet op de Identificatieplicht",
        "Wet op de politiegegevens",
        "Wetboek van Strafrecht",
        "Algemene verordening gegevensbescherming",
    }

    def __init__(self):
        """Initialize the validator."""
        logger.info("ContextValidator initialized")

    def validate(self, context_data: dict[str, Any]) -> bool:
        """
        Quick validation check.

        Args:
            context_data: Context data to validate

        Returns:
            True if valid, False otherwise
        """
        errors = self.validate_detailed(context_data)
        return len([e for e in errors if e.severity == "error"]) == 0

    def validate_detailed(self, context_data: dict[str, Any]) -> list[ValidationError]:
        """
        Detailed validation with error reporting.

        Args:
            context_data: Context data to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Validate structure
        errors.extend(self._validate_structure(context_data))

        # Validate field types
        errors.extend(self._validate_field_types(context_data))

        # Validate field values
        errors.extend(self._validate_field_values(context_data))

        # Validate business rules
        errors.extend(self._validate_business_rules(context_data))

        return errors

    def _validate_structure(
        self, context_data: dict[str, Any]
    ) -> list[ValidationError]:
        """Validate basic structure."""
        errors = []

        if not isinstance(context_data, dict):
            errors.append(
                ValidationError(
                    field="root",
                    message="Context data must be a dictionary",
                    severity="error",
                )
            )
            return errors  # Can't continue validation

        # Check for unexpected fields
        expected_fields = {
            "organisatorische_context",
            "juridische_context",
            "wettelijke_basis",
            "metadata",
        }
        unexpected = set(context_data.keys()) - expected_fields

        for field in unexpected:
            errors.append(
                ValidationError(
                    field=field,
                    message=f"Unexpected field: {field}",
                    severity="warning",
                    suggestion="Remove field or add to expected fields",
                )
            )

        return errors

    def _validate_field_types(
        self, context_data: dict[str, Any]
    ) -> list[ValidationError]:
        """Validate field types."""
        errors = []

        # List fields
        list_fields = [
            "organisatorische_context",
            "juridische_context",
            "wettelijke_basis",
        ]

        for field in list_fields:
            value = context_data.get(field)

            if value is None:
                continue  # None is allowed (will be converted to empty list)

            if not isinstance(value, (list, str)):
                errors.append(
                    ValidationError(
                        field=field,
                        message=f"Field must be a list or string, got {type(value).__name__}",
                        severity="error",
                        suggestion="Convert to list of strings",
                    )
                )
            elif isinstance(value, list):
                # Check all items are strings
                for i, item in enumerate(value):
                    if item is not None and not isinstance(item, str):
                        errors.append(
                            ValidationError(
                                field=f"{field}[{i}]",
                                message=f"Item must be a string, got {type(item).__name__}",
                                severity="error",
                            )
                        )

        # Metadata field
        metadata = context_data.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            errors.append(
                ValidationError(
                    field="metadata",
                    message=f"Metadata must be a dictionary, got {type(metadata).__name__}",
                    severity="error",
                )
            )

        return errors

    def _validate_field_values(
        self, context_data: dict[str, Any]
    ) -> list[ValidationError]:
        """Validate field values against business rules."""
        errors = []

        # Validate organisatorische context
        org_context = context_data.get("organisatorische_context", [])
        if isinstance(org_context, list):
            errors.extend(
                self._validate_list_field(
                    "organisatorische_context", org_context, self.VALID_ORGANISATIES
                )
            )

        # Validate juridische context
        jur_context = context_data.get("juridische_context", [])
        if isinstance(jur_context, list):
            errors.extend(
                self._validate_list_field(
                    "juridische_context", jur_context, self.VALID_JURIDISCH
                )
            )

        # Validate wettelijke basis
        wet_basis = context_data.get("wettelijke_basis", [])
        if isinstance(wet_basis, list):
            errors.extend(
                self._validate_list_field(
                    "wettelijke_basis", wet_basis, self.VALID_WETTELIJK
                )
            )

        return errors

    def _validate_list_field(
        self, field_name: str, values: list[str], valid_set: set[str]
    ) -> list[ValidationError]:
        """Validate a list field against valid values."""
        errors = []

        # Check maximum items
        if len(values) > self.MAX_ITEMS_PER_FIELD:
            errors.append(
                ValidationError(
                    field=field_name,
                    message=f"Too many items ({len(values)}), maximum is {self.MAX_ITEMS_PER_FIELD}",
                    severity="error",
                    suggestion=f"Reduce to {self.MAX_ITEMS_PER_FIELD} most relevant items",
                )
            )

        # Check each value
        for value in values:
            if not value or not value.strip():
                errors.append(
                    ValidationError(
                        field=field_name,
                        message="Empty value not allowed",
                        severity="error",
                    )
                )
                continue

            # Check length for custom values
            if value not in valid_set and len(value) > self.MAX_CUSTOM_LENGTH:
                errors.append(
                    ValidationError(
                        field=field_name,
                        message=f"Custom value too long ({len(value)} chars), maximum is {self.MAX_CUSTOM_LENGTH}",
                        severity="error",
                        suggestion="Shorten the custom value",
                    )
                )

            # Info about custom values (not an error)
            if value not in valid_set and len(value) <= self.MAX_CUSTOM_LENGTH:
                errors.append(
                    ValidationError(
                        field=field_name,
                        message=f"Custom value: '{value}'",
                        severity="info",
                    )
                )

        return errors

    def _validate_business_rules(
        self, context_data: dict[str, Any]
    ) -> list[ValidationError]:
        """Validate business rules and relationships between fields."""
        errors = []

        org_context = context_data.get("organisatorische_context", [])
        jur_context = context_data.get("juridische_context", [])
        wet_basis = context_data.get("wettelijke_basis", [])

        # Ensure lists are not None
        org_context = org_context if org_context else []
        jur_context = jur_context if jur_context else []
        wet_basis = wet_basis if wet_basis else []

        # Rule: Strafrecht context often requires strafvordering wetgeving
        if jur_context and "Strafrecht" in jur_context:
            has_straf_wet = any(
                "strafvordering" in w.lower() or "strafrecht" in w.lower()
                for w in wet_basis
            )
            if not has_straf_wet:
                errors.append(
                    ValidationError(
                        field="wettelijke_basis",
                        message="Strafrecht context usually requires strafvordering or strafrecht wetgeving",
                        severity="warning",
                        suggestion="Consider adding Wetboek van Strafvordering or Wetboek van Strafrecht",
                    )
                )

        # Rule: DJI context often relates to detentie wetgeving
        if org_context and "DJI" in org_context and not wet_basis:
            errors.append(
                ValidationError(
                    field="wettelijke_basis",
                    message="DJI context usually requires detentie-gerelateerde wetgeving",
                    severity="info",
                    suggestion="Consider adding relevant detention laws",
                )
            )

        # Rule: At least one context field should be filled
        if not org_context and not jur_context and not wet_basis:
            errors.append(
                ValidationError(
                    field="root",
                    message="At least one context field should be specified",
                    severity="warning",
                    suggestion="Add organisatorische, juridische, or wettelijke context",
                )
            )

        return errors

    def sanitize_custom_input(self, value: str) -> str | None:
        """
        Sanitize custom input values.

        Args:
            value: Raw input value

        Returns:
            Sanitized value or None if invalid
        """
        if not value:
            return None

        # Strip whitespace
        sanitized = value.strip()

        # Check length
        if len(sanitized) > self.MAX_CUSTOM_LENGTH:
            sanitized = sanitized[: self.MAX_CUSTOM_LENGTH]

        # Remove dangerous characters
        dangerous_chars = ["<", ">", "&", '"', "'", "\n", "\r", "\t"]
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, "")

        # Return None if nothing left
        return sanitized if sanitized else None
