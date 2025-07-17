"""
Base validator classes and interfaces for AI Toetser.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class ValidationResult(Enum):
    """Validation result types."""
    PASS = "✔️"
    FAIL = "❌"
    WARNING = "🟡"
    INFO = "ℹ️"


@dataclass
class ValidationContext:
    """Context information for validation."""
    definitie: str
    begrip: str = ""
    regel: Optional[Dict[str, Any]] = None
    contexten: Optional[Dict[str, List[str]]] = None
    bronnen_gebruikt: Optional[str] = None
    voorkeursterm: Optional[str] = None
    marker: Optional[str] = None
    gebruik_logging: bool = False
    
    def __post_init__(self):
        """Initialize default values after creation."""
        if self.contexten is None:
            self.contexten = {}


@dataclass
class ValidationOutput:
    """Standardized validation output."""
    rule_id: str
    result: ValidationResult
    message: str
    details: Optional[str] = None
    
    def __str__(self) -> str:
        """String representation for compatibility with existing code."""
        return f"{self.result.value} {self.rule_id}: {self.message}"


class BaseValidator(ABC):
    """
    Abstract base class for all validation rules.
    
    Provides common functionality and enforces consistent interface.
    """
    
    def __init__(self, rule_id: str, name: str, description: str):
        self.rule_id = rule_id
        self.name = name
        self.description = description
    
    @abstractmethod
    def validate(self, context: ValidationContext) -> ValidationOutput:
        """
        Validate the definition according to this rule.
        
        Args:
            context: Validation context with all necessary information
            
        Returns:
            ValidationOutput with result and message
        """
        pass
    
    def _create_result(
        self, 
        result: ValidationResult, 
        message: str, 
        details: Optional[str] = None
    ) -> ValidationOutput:
        """Helper to create consistent validation output."""
        return ValidationOutput(
            rule_id=self.rule_id,
            result=result,
            message=message,
            details=details
        )
    
    def _check_good_examples(self, definitie: str, regel: Dict[str, Any]) -> bool:
        """Check if definition matches good examples."""
        definitie_lc = definitie.lower()
        goede_voorbeelden = regel.get("goede_voorbeelden", [])
        return any(vb.lower() in definitie_lc for vb in goede_voorbeelden)
    
    def _check_bad_examples(self, definitie: str, regel: Dict[str, Any]) -> bool:
        """Check if definition matches bad examples."""
        definitie_lc = definitie.lower()
        foute_voorbeelden = regel.get("foute_voorbeelden", [])
        return any(vb.lower() in definitie_lc for vb in foute_voorbeelden)
    
    def _extract_rule_property(self, regel: Dict[str, Any], key: str, default: Any = None) -> Any:
        """Safely extract property from rule configuration."""
        if not regel:
            return default
        return regel.get(key, default)


class ValidationRegistry:
    """Registry for managing all validators."""
    
    def __init__(self):
        self._validators: Dict[str, BaseValidator] = {}
    
    def register(self, validator: BaseValidator):
        """Register a validator."""
        self._validators[validator.rule_id] = validator
    
    def get_validator(self, rule_id: str) -> Optional[BaseValidator]:
        """Get validator by rule ID."""
        return self._validators.get(rule_id)
    
    def get_all_validators(self) -> Dict[str, BaseValidator]:
        """Get all registered validators."""
        return self._validators.copy()
    
    def validate_all(self, context: ValidationContext, rule_configs: Dict[str, Dict]) -> List[ValidationOutput]:
        """
        Run all applicable validators.
        
        Args:
            context: Validation context
            rule_configs: Rule configurations from JSON
            
        Returns:
            List of validation results
        """
        results = []
        
        for rule_id, rule_config in rule_configs.items():
            validator = self.get_validator(rule_id)
            if validator:
                # Update context with current rule config
                validation_context = ValidationContext(
                    definitie=context.definitie,
                    begrip=context.begrip,
                    regel=rule_config,
                    contexten=context.contexten,
                    bronnen_gebruikt=context.bronnen_gebruikt,
                    voorkeursterm=context.voorkeursterm,
                    marker=context.marker,
                    gebruik_logging=context.gebruik_logging
                )
                
                try:
                    result = validator.validate(validation_context)
                    results.append(result)
                except Exception as e:
                    # Log error and create error result
                    error_result = ValidationOutput(
                        rule_id=rule_id,
                        result=ValidationResult.FAIL,
                        message=f"Validation error: {str(e)}",
                        details=f"Exception in {validator.__class__.__name__}"
                    )
                    results.append(error_result)
        
        return results


# Global registry instance
validation_registry = ValidationRegistry()