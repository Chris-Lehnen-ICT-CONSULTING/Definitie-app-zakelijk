"""
Modular AI Toetser - new orchestrator for validation rules.
This replaces the monolithic core.py with a clean, modular architecture.
"""

import logging
from typing import Dict, List, Any, Optional

from .validators import (
    ValidationContext,
    ValidationOutput,
    ValidationResult,
    validation_registry
)

# Import all validator modules to register them
from .validators.content_rules import CON01Validator, CON02Validator
from .validators.essential_rules import (
    ESS01Validator, ESS02Validator, ESS03Validator, 
    ESS04Validator, ESS05Validator
)
from .validators.structure_rules import (
    STR01Validator, STR02Validator, STR03Validator, STR04Validator,
    STR05Validator, STR06Validator, STR07Validator, STR08Validator,
    STR09Validator
)

# Initialize logger
logger = logging.getLogger(__name__)


class ModularToetser:
    """
    Modular definition validator that orchestrates all validation rules.
    
    This class replaces the monolithic approach with a clean, extensible
    architecture where each rule is a separate, testable class.
    """
    
    def __init__(self):
        self._initialize_validators()
    
    def _initialize_validators(self):
        """Register all validators in the global registry."""
        # Content rules
        validation_registry.register(CON01Validator())
        validation_registry.register(CON02Validator())
        
        # Essential rules
        validation_registry.register(ESS01Validator())
        validation_registry.register(ESS02Validator())
        validation_registry.register(ESS03Validator())
        validation_registry.register(ESS04Validator())
        validation_registry.register(ESS05Validator())
        
        # Structure rules
        validation_registry.register(STR01Validator())
        validation_registry.register(STR02Validator())
        validation_registry.register(STR03Validator())
        validation_registry.register(STR04Validator())
        validation_registry.register(STR05Validator())
        validation_registry.register(STR06Validator())
        validation_registry.register(STR07Validator())
        validation_registry.register(STR08Validator())
        validation_registry.register(STR09Validator())
        
        logger.info(f"Initialized {len(validation_registry.get_all_validators())} validators")
    
    def validate_definition(
        self,
        definitie: str,
        toetsregels: Dict[str, Dict[str, Any]],
        begrip: str = "",
        marker: Optional[str] = None,
        voorkeursterm: Optional[str] = None,
        bronnen_gebruikt: Optional[str] = None,
        contexten: Optional[Dict[str, List[str]]] = None,
        gebruik_logging: bool = False
    ) -> List[str]:
        """
        Validate definition using all applicable rules.
        
        Args:
            definitie: Definition text to validate
            toetsregels: Rule configurations from JSON
            begrip: Original term being defined
            marker: Ontological category marker
            voorkeursterm: Preferred term
            bronnen_gebruikt: Sources used
            contexten: Context information
            gebruik_logging: Whether to use detailed logging
            
        Returns:
            List of validation result strings (for backward compatibility)
        """
        if gebruik_logging:
            logger.info(f"Starting validation for term: {begrip}")
        
        # Create validation context
        context = ValidationContext(
            definitie=definitie,
            begrip=begrip,
            regel=None,  # Will be set per rule
            contexten=contexten or {},
            bronnen_gebruikt=bronnen_gebruikt,
            voorkeursterm=voorkeursterm,
            marker=marker,
            gebruik_logging=gebruik_logging
        )
        
        # Run all validations
        results = validation_registry.validate_all(context, toetsregels)
        
        # Convert to string format for backward compatibility
        string_results = [str(result) for result in results]
        
        # Calculate statistics
        passed = sum(1 for r in results if r.result == ValidationResult.PASS)
        failed = sum(1 for r in results if r.result == ValidationResult.FAIL)
        warnings = sum(1 for r in results if r.result == ValidationResult.WARNING)
        total = len(results)
        
        if gebruik_logging:
            logger.info(f"Validation complete: {passed} passed, {failed} failed, {warnings} warnings")
        
        # Add summary to results (at the beginning for visibility)
        if total > 0:
            score_percentage = (passed / total) * 100
            summary = f"📊 **Toetsing Samenvatting**: {passed}/{total} regels geslaagd ({score_percentage:.1f}%)"
            if failed > 0:
                summary += f" | ❌ {failed} gefaald"
            if warnings > 0:
                summary += f" | ⚠️ {warnings} waarschuwingen"
            
            string_results.insert(0, summary)
        
        return string_results
    
    def get_available_rules(self) -> List[str]:
        """Get list of available validation rules."""
        return list(validation_registry.get_all_validators().keys())
    
    def validate_single_rule(
        self,
        rule_id: str,
        definitie: str,
        regel_config: Dict[str, Any],
        **kwargs
    ) -> Optional[ValidationOutput]:
        """
        Validate using a single rule.
        
        Args:
            rule_id: ID of the rule to use
            definitie: Definition text
            regel_config: Rule configuration
            **kwargs: Additional context parameters
            
        Returns:
            ValidationOutput or None if rule not found
        """
        validator = validation_registry.get_validator(rule_id)
        if not validator:
            logger.warning(f"Validator {rule_id} not found")
            return None
        
        context = ValidationContext(
            definitie=definitie,
            regel=regel_config,
            **kwargs
        )
        
        return validator.validate(context)


# Global instance for backward compatibility
modular_toetser = ModularToetser()


def toets_definitie(
    definitie: str,
    toetsregels: Dict[str, Dict[str, Any]],
    begrip: str = "",
    marker: Optional[str] = None,
    voorkeursterm: Optional[str] = None,
    bronnen_gebruikt: Optional[str] = None,
    contexten: Optional[Dict[str, List[str]]] = None,
    gebruik_logging: bool = False
) -> List[str]:
    """
    Main entry point for definition validation.
    
    This function maintains backward compatibility with the existing API
    while using the new modular architecture under the hood.
    
    Args:
        definitie: Definition text to validate
        toetsregels: Rule configurations from JSON
        begrip: Original term being defined
        marker: Ontological category marker
        voorkeursterm: Preferred term
        bronnen_gebruikt: Sources used
        contexten: Context information
        gebruik_logging: Whether to use detailed logging
        
    Returns:
        List of validation result strings
    """
    return modular_toetser.validate_definition(
        definitie=definitie,
        toetsregels=toetsregels,
        begrip=begrip,
        marker=marker,
        voorkeursterm=voorkeursterm,
        bronnen_gebruikt=bronnen_gebruikt,
        contexten=contexten,
        gebruik_logging=gebruik_logging
    )