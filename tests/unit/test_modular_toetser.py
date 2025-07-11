"""
Test the new modular AI Toetser architecture.
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_modular_toetser_imports():
    """Test that the new modular toetser can be imported."""
    from ai_toetser.modular_toetser import ModularToetser, toets_definitie
    
    assert ModularToetser
    assert toets_definitie


def test_modular_toetser_creation():
    """Test that ModularToetser can be created and initialized."""
    from ai_toetser.modular_toetser import ModularToetser
    
    toetser = ModularToetser()
    assert toetser is not None
    
    # Check that validators are registered
    available_rules = toetser.get_available_rules()
    assert len(available_rules) > 0
    
    # Check for specific rules we implemented
    assert "CON-01" in available_rules
    assert "CON-02" in available_rules
    assert "ESS-01" in available_rules
    assert "STR-01" in available_rules


def test_backward_compatibility():
    """Test that the new implementation maintains backward compatibility."""
    from ai_toetser import toets_definitie
    
    # Test with minimal parameters
    result = toets_definitie(
        definitie="Een handeling waarbij iets wordt vastgelegd",
        toetsregels={}
    )
    
    assert isinstance(result, list)


def test_validation_context():
    """Test ValidationContext creation and usage."""
    from ai_toetser.validators import ValidationContext
    
    context = ValidationContext(
        definitie="Test definitie",
        begrip="test"
    )
    
    assert context.definitie == "Test definitie"
    assert context.begrip == "test"
    assert context.contexten == {}  # default value


def test_validation_output():
    """Test ValidationOutput creation."""
    from ai_toetser.validators import ValidationOutput, ValidationResult
    
    output = ValidationOutput(
        rule_id="TEST-01",
        result=ValidationResult.PASS,
        message="Test passed"
    )
    
    assert output.rule_id == "TEST-01"
    assert output.result == ValidationResult.PASS
    assert output.message == "Test passed"
    
    # Test string representation
    result_str = str(output)
    assert "✔️" in result_str
    assert "TEST-01" in result_str
    assert "Test passed" in result_str


def test_individual_validators():
    """Test that individual validators can be used."""
    from ai_toetser.validators.content_rules import CON01Validator
    from ai_toetser.validators import ValidationContext
    
    validator = CON01Validator()
    
    context = ValidationContext(
        definitie="Een proces waarbij data wordt verwerkt",
        regel={"herkenbaar_patronen": []},
        contexten={}
    )
    
    result = validator.validate(context)
    
    assert result is not None
    assert result.rule_id == "CON-01"


def test_validation_registry():
    """Test the validation registry functionality."""
    from ai_toetser.validators import validation_registry
    from ai_toetser.validators.content_rules import CON01Validator
    
    # Test getting a validator
    validator = validation_registry.get_validator("CON-01")
    assert validator is not None
    assert isinstance(validator, CON01Validator)
    
    # Test getting all validators
    all_validators = validation_registry.get_all_validators()
    assert len(all_validators) > 0
    assert "CON-01" in all_validators


if __name__ == "__main__":
    pytest.main([__file__, "-v"])