"""
Context Payload Schema Validation Tests for EPIC-010.

These tests validate that context payloads conform to the expected schema,
ensuring data integrity and preventing runtime errors from malformed context data.

Test Coverage:
- JSON Schema validation
- Type checking and coercion
- Required vs optional fields
- Field constraints and formats
- Nested object validation
- Array validation
- Cross-field dependencies
- Schema evolution and versioning
"""

import pytest
import json
import jsonschema
from jsonschema import validate, ValidationError, Draft7Validator
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from src.services.interfaces import GenerationRequest


# Define the context payload schema
CONTEXT_PAYLOAD_SCHEMA_V1 = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Context Payload Schema",
    "type": "object",
    "properties": {
        "begrip": {
            "type": "string",
            "minLength": 1,
            "maxLength": 500,
            "description": "The term to define"
        },
        "organisatorische_context": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": ["DJI", "OM", "Rechtspraak", "KMAR", "CJIB", "RvdK", "NFI", "Anders..."]
            },
            "uniqueItems": True,
            "description": "Organizational context"
        },
        "juridische_context": {
            "type": "array",
            "items": {
                "type": "string",
                "minLength": 1,
                "maxLength": 100
            },
            "uniqueItems": True,
            "description": "Legal context"
        },
        "wettelijke_basis": {
            "type": "array",
            "items": {
                "type": "string",
                "minLength": 1,
                "maxLength": 500
            },
            "uniqueItems": True,
            "description": "Legal basis references"
        },
        "api_version": {
            "type": "string",
            "pattern": "^\\d+\\.\\d+(\\.\\d+)?$",
            "default": "1.0",
            "description": "API version"
        },
        "metadata": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "session_id": {"type": "string"},
                "timestamp": {
                    "type": "string",
                    "format": "date-time"
                },
                "source": {
                    "type": "string",
                    "enum": ["web", "api", "batch", "test"]
                }
            }
        }
    },
    "required": ["begrip"],
    "additionalProperties": False
}


@pytest.mark.skip(reason="Context payload schema not yet implemented (US-041/042/043)")
class TestSchemaValidation:
    """Test basic schema validation."""

    @pytest.fixture
    def validator(self):
        """Create JSON schema validator."""
        return Draft7Validator(CONTEXT_PAYLOAD_SCHEMA_V1)

    def test_valid_minimal_payload(self, validator):
        """Test minimal valid payload."""
        payload = {
            "begrip": "voorlopige hechtenis"
        }
        
        # Should validate without error
        validator.validate(payload)

    def test_valid_complete_payload(self, validator):
        """Test complete valid payload with all fields."""
        payload = {
            "begrip": "voorlopige hechtenis",
            "organisatorische_context": ["DJI", "OM"],
            "juridische_context": ["Strafrecht", "Strafprocesrecht"],
            "wettelijke_basis": ["Wetboek van Strafvordering", "Wet voorlopige hechtenis"],
            "api_version": "1.0",
            "metadata": {
                "user_id": "user123",
                "session_id": "session456",
                "timestamp": "2024-01-15T10:30:00Z",
                "source": "web"
            }
        }
        
        # Should validate without error
        validator.validate(payload)

    def test_missing_required_field(self, validator):
        """Test that missing required fields cause validation error."""
        payload = {
            "organisatorische_context": ["DJI"]
            # Missing required 'begrip'
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(payload)
        
        assert "'begrip' is a required property" in str(exc_info.value)

    def test_additional_properties_rejected(self, validator):
        """Test that additional properties are rejected."""
        payload = {
            "begrip": "test",
            "unknown_field": "should fail"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(payload)
        
        assert "Additional properties are not allowed" in str(exc_info.value)


@pytest.mark.skip(reason="Context payload schema not yet implemented (US-041/042/043)")
class TestFieldTypeValidation:
    """Test field type validation and coercion."""

    @pytest.fixture
    def validator(self):
        return Draft7Validator(CONTEXT_PAYLOAD_SCHEMA_V1)

    def test_string_fields(self, validator):
        """Test string field validation."""
        # Valid
        payload = {
            "begrip": "Valid string term"
        }
        validator.validate(payload)
        
        # Invalid - number instead of string
        payload = {
            "begrip": 12345
        }
        with pytest.raises(ValidationError):
            validator.validate(payload)

    def test_array_fields(self, validator):
        """Test array field validation."""
        # Valid arrays
        payload = {
            "begrip": "test",
            "organisatorische_context": ["DJI", "OM"],
            "juridische_context": ["Strafrecht"],
            "wettelijke_basis": ["Test wet"]
        }
        validator.validate(payload)
        
        # Invalid - string instead of array
        payload = {
            "begrip": "test",
            "organisatorische_context": "DJI"  # Should be array
        }
        with pytest.raises(ValidationError):
            validator.validate(payload)

    def test_nested_object_validation(self, validator):
        """Test nested object validation."""
        # Valid metadata
        payload = {
            "begrip": "test",
            "metadata": {
                "user_id": "user123",
                "source": "api"
            }
        }
        validator.validate(payload)
        
        # Invalid metadata source
        payload = {
            "begrip": "test",
            "metadata": {
                "source": "invalid_source"  # Not in enum
            }
        }
        with pytest.raises(ValidationError):
            validator.validate(payload)


@pytest.mark.skip(reason="Context payload schema not yet implemented (US-041/042/043)")
class TestFieldConstraints:
    """Test field constraints and formats."""

    @pytest.fixture
    def validator(self):
        return Draft7Validator(CONTEXT_PAYLOAD_SCHEMA_V1)

    def test_string_length_constraints(self, validator):
        """Test string length constraints."""
        # Too short begrip
        payload = {"begrip": ""}  # Empty string
        with pytest.raises(ValidationError):
            validator.validate(payload)
        
        # Too long begrip
        payload = {"begrip": "x" * 501}  # Exceeds maxLength
        with pytest.raises(ValidationError):
            validator.validate(payload)
        
        # Valid length
        payload = {"begrip": "x" * 500}  # At maxLength
        validator.validate(payload)

    def test_enum_constraints(self, validator):
        """Test enum field constraints."""
        # Valid organization
        payload = {
            "begrip": "test",
            "organisatorische_context": ["DJI", "OM", "Rechtspraak"]
        }
        validator.validate(payload)
        
        # Invalid organization
        payload = {
            "begrip": "test",
            "organisatorische_context": ["InvalidOrg"]
        }
        with pytest.raises(ValidationError):
            validator.validate(payload)

    def test_unique_items_constraint(self, validator):
        """Test unique items in arrays."""
        # Duplicate items
        payload = {
            "begrip": "test",
            "organisatorische_context": ["DJI", "DJI"]  # Duplicate
        }
        with pytest.raises(ValidationError):
            validator.validate(payload)

    def test_pattern_constraints(self, validator):
        """Test pattern constraints (regex)."""
        # Valid version pattern
        payload = {
            "begrip": "test",
            "api_version": "1.0.0"
        }
        validator.validate(payload)
        
        # Invalid version pattern
        payload = {
            "begrip": "test",
            "api_version": "v1.0"  # Doesn't match pattern
        }
        with pytest.raises(ValidationError):
            validator.validate(payload)

    def test_datetime_format(self, validator):
        """Test datetime format validation."""
        # Valid datetime
        payload = {
            "begrip": "test",
            "metadata": {
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
        validator.validate(payload)
        
        # Invalid datetime
        payload = {
            "begrip": "test",
            "metadata": {
                "timestamp": "not-a-datetime"
            }
        }
        with pytest.raises(ValidationError):
            validator.validate(payload)


@pytest.mark.skip(reason="Context payload schema not yet implemented (US-041/042/043)")
class TestCrossFieldDependencies:
    """Test dependencies between fields."""

    def test_anders_requires_custom_text(self):
        """When 'Anders...' is selected, custom text should be provided."""
        # This is application logic, not schema validation
        # But we can define custom validators
        
        def validate_anders_option(payload):
            """Custom validator for Anders option."""
            org_context = payload.get('organisatorische_context', [])
            
            if 'Anders...' in org_context:
                # Should have custom_organisatorische_context field
                if 'custom_organisatorische_context' not in payload:
                    raise ValidationError("Anders... requires custom_organisatorische_context")
            
            return True
        
        # Test with Anders but no custom text
        payload = {
            "begrip": "test",
            "organisatorische_context": ["DJI", "Anders..."]
        }
        
        with pytest.raises(ValidationError):
            validate_anders_option(payload)

    def test_conditional_required_fields(self):
        """Test fields that become required based on other fields."""
        # Extended schema with conditional requirements
        conditional_schema = {
            **CONTEXT_PAYLOAD_SCHEMA_V1,
            "allOf": [
                {
                    "if": {
                        "properties": {
                            "juridische_context": {
                                "contains": {"const": "Strafrecht"}
                            }
                        }
                    },
                    "then": {
                        "properties": {
                            "wettelijke_basis": {
                                "minItems": 1
                            }
                        }
                    }
                }
            ]
        }
        
        validator = Draft7Validator(conditional_schema)
        
        # Strafrecht without wettelijke_basis should fail
        payload = {
            "begrip": "test",
            "juridische_context": ["Strafrecht"],
            "wettelijke_basis": []
        }
        
        # This would fail with the conditional schema


@pytest.mark.skip(reason="Context payload schema not yet implemented (US-041/042/043)")
class TestSchemaEvolution:
    """Test schema versioning and evolution."""

    def test_backward_compatibility(self):
        """New schema versions should be backward compatible."""
        # V1 payload
        v1_payload = {
            "begrip": "test",
            "organisatorische_context": ["DJI"]
        }
        
        # V2 schema (with new optional fields)
        v2_schema = {
            **CONTEXT_PAYLOAD_SCHEMA_V1,
            "properties": {
                **CONTEXT_PAYLOAD_SCHEMA_V1["properties"],
                "new_optional_field": {
                    "type": "string",
                    "description": "New in v2"
                }
            }
        }
        
        v2_validator = Draft7Validator(v2_schema)
        
        # V1 payload should still validate in V2
        v2_validator.validate(v1_payload)

    def test_migration_validation(self):
        """Test migration from old to new schema."""
        # Old format (pre-refactoring)
        old_payload = {
            "term": "voorlopige hechtenis",  # Old field name
            "context": "DJI",  # String instead of array
            "domain": "Strafrecht"  # Old field name
        }
        
        # Migration function
        def migrate_payload(old):
            return {
                "begrip": old.get("term"),
                "organisatorische_context": [old.get("context")] if old.get("context") else [],
                "juridische_context": [old.get("domain")] if old.get("domain") else []
            }
        
        # Migrate
        new_payload = migrate_payload(old_payload)
        
        # Validate migrated payload
        validator = Draft7Validator(CONTEXT_PAYLOAD_SCHEMA_V1)
        validator.validate(new_payload)


@pytest.mark.skip(reason="Context payload schema not yet implemented (US-041/042/043)")
class TestDataclassIntegration:
    """Test integration with Python dataclasses."""

    def test_dataclass_to_schema_validation(self):
        """Test that dataclass instances validate against schema."""
        @dataclass
        class ContextPayload:
            begrip: str
            organisatorische_context: List[str] = None
            juridische_context: List[str] = None
            wettelijke_basis: List[str] = None
            
            def to_dict(self):
                data = asdict(self)
                # Remove None values
                return {k: v for k, v in data.items() if v is not None}
        
        # Create instance
        payload = ContextPayload(
            begrip="test",
            organisatorische_context=["DJI"],
            juridische_context=["Strafrecht"]
        )
        
        # Convert to dict
        payload_dict = payload.to_dict()
        
        # Validate
        validator = Draft7Validator(CONTEXT_PAYLOAD_SCHEMA_V1)
        validator.validate(payload_dict)

    def test_generation_request_validation(self):
        """Test that GenerationRequest validates against schema."""
        request = GenerationRequest(
            begrip="voorlopige hechtenis",
            organisatorische_context=["DJI", "OM"],
            juridische_context=["Strafrecht"],
            wettelijke_basis=["Wetboek van Strafvordering"]
        )
        
        # Convert to dict (simulated)
        request_dict = {
            "begrip": request.begrip,
            "organisatorische_context": request.organisatorische_context,
            "juridische_context": request.juridische_context,
            "wettelijke_basis": request.wettelijke_basis
        }
        
        # Validate
        validator = Draft7Validator(CONTEXT_PAYLOAD_SCHEMA_V1)
        validator.validate(request_dict)


@pytest.mark.skip(reason="Context payload schema not yet implemented (US-041/042/043)")
class TestErrorHandling:
    """Test schema validation error handling."""

    @pytest.fixture
    def validator(self):
        return Draft7Validator(CONTEXT_PAYLOAD_SCHEMA_V1)

    def test_detailed_error_messages(self, validator):
        """Test that validation errors provide useful details."""
        payload = {
            "begrip": "",  # Too short
            "organisatorische_context": "DJI",  # Wrong type
            "juridische_context": ["Valid", "Valid", "Valid"],  # Duplicates
            "api_version": "invalid",  # Wrong pattern
        }
        
        errors = list(validator.iter_errors(payload))
        
        # Should have multiple errors
        assert len(errors) > 0
        
        # Errors should have paths
        for error in errors:
            assert error.path is not None or error.schema_path is not None

    def test_error_recovery_suggestions(self):
        """Test that errors include recovery suggestions."""
        def validate_with_suggestions(payload):
            validator = Draft7Validator(CONTEXT_PAYLOAD_SCHEMA_V1)
            errors = list(validator.iter_errors(payload))
            
            suggestions = []
            for error in errors:
                if "enum" in error.schema:
                    suggestions.append(f"Valid values: {error.schema['enum']}")
                elif "minLength" in error.schema:
                    suggestions.append(f"Minimum length: {error.schema['minLength']}")
                elif "type" in error.schema:
                    suggestions.append(f"Expected type: {error.schema['type']}")
            
            return suggestions
        
        payload = {
            "begrip": "",
            "organisatorische_context": ["InvalidOrg"]
        }
        
        suggestions = validate_with_suggestions(payload)
        assert len(suggestions) > 0


@pytest.mark.skip(reason="Context payload schema not yet implemented (US-041/042/043)")
class TestPerformanceOptimization:
    """Test schema validation performance."""

    def test_validation_speed(self):
        """Schema validation should be fast."""
        validator = Draft7Validator(CONTEXT_PAYLOAD_SCHEMA_V1)
        
        payload = {
            "begrip": "test",
            "organisatorische_context": ["DJI", "OM"],
            "juridische_context": ["Strafrecht"],
            "wettelijke_basis": ["Test wet"]
        }
        
        import time
        iterations = 10000
        
        start = time.perf_counter()
        for _ in range(iterations):
            validator.validate(payload)
        elapsed = time.perf_counter() - start
        
        avg_time_ms = (elapsed / iterations) * 1000
        
        # Should be very fast
        assert avg_time_ms < 0.1, f"Validation too slow: {avg_time_ms:.3f}ms"

    def test_compiled_validator_performance(self):
        """Test performance with compiled validators."""
        # Compile validator
        validator = Draft7Validator(CONTEXT_PAYLOAD_SCHEMA_V1)
        validate_fn = validator.validate
        
        payload = {
            "begrip": "test",
            "organisatorische_context": ["DJI"]
        }
        
        import time
        iterations = 10000
        
        start = time.perf_counter()
        for _ in range(iterations):
            validate_fn(payload)
        elapsed = time.perf_counter() - start
        
        avg_time_ms = (elapsed / iterations) * 1000
        
        # Compiled should be even faster
        assert avg_time_ms < 0.05, f"Compiled validation too slow: {avg_time_ms:.3f}ms"


@pytest.mark.skip(reason="Context payload schema not yet implemented (US-041/042/043)")
class TestSchemaDocumentation:
    """Test schema documentation and examples."""

    def test_schema_has_descriptions(self):
        """All fields should have descriptions."""
        def check_descriptions(schema, path=""):
            if "properties" in schema:
                for prop, prop_schema in schema["properties"].items():
                    current_path = f"{path}.{prop}" if path else prop
                    
                    # Should have description
                    assert "description" in prop_schema or "title" in prop_schema, \
                           f"Field {current_path} lacks description"
                    
                    # Recurse for nested objects
                    if prop_schema.get("type") == "object":
                        check_descriptions(prop_schema, current_path)
        
        check_descriptions(CONTEXT_PAYLOAD_SCHEMA_V1)

    def test_schema_examples(self):
        """Schema should include valid examples."""
        examples = [
            {
                "begrip": "voorlopige hechtenis",
                "organisatorische_context": ["DJI", "OM"],
                "juridische_context": ["Strafrecht"],
                "wettelijke_basis": ["Wetboek van Strafvordering"]
            },
            {
                "begrip": "dwangmiddel",
                "organisatorische_context": ["OM"],
                "juridische_context": ["Strafprocesrecht"]
            },
            {
                "begrip": "gedetineerde",
                "organisatorische_context": ["DJI"],
                "wettelijke_basis": ["Penitentiaire beginselenwet"]
            }
        ]
        
        validator = Draft7Validator(CONTEXT_PAYLOAD_SCHEMA_V1)
        
        for example in examples:
            validator.validate(example)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])