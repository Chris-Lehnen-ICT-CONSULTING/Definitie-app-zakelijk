"""
Enhanced Modular Toetser - Uitbreiding met rich validation features.

Deze module breidt de bestaande ModularToetser uit met scoring,
violations tracking, en gedetailleerde feedback mogelijkheden.
"""

import logging
from typing import Dict, List, Any, Optional

from generation.definitie_generator import OntologischeCategorie
from config.toetsregel_manager import get_toetsregel_manager

from .modular_toetser import ModularToetser
from .models import (
    ToetsregelValidationResult,
    RichValidationOutput,
    RuleViolation,
    ViolationSeverity,
    ViolationType
)
from .validators import ValidationContext, ValidationOutput, ValidationResult

logger = logging.getLogger(__name__)


class EnhancedModularToetser(ModularToetser):
    """
    Uitgebreide versie van ModularToetser met rich validation support.
    
    Deze klasse voegt scoring, gedetailleerde violations, en suggesties toe
    aan de bestaande modulaire validator architectuur.
    """
    
    def __init__(self):
        super().__init__()
        self.rule_manager = get_toetsregel_manager()
        
        # Acceptatie drempels
        self.acceptance_thresholds = {
            "overall_score": 0.8,
            "critical_violations": 0,
            "category_compliance": 0.75
        }
    
    def validate_definition_rich(
        self,
        definitie: str,
        categorie: Optional[OntologischeCategorie] = None,
        toetsregels: Optional[Dict[str, Dict[str, Any]]] = None,
        begrip: str = "",
        marker: Optional[str] = None,
        voorkeursterm: Optional[str] = None,
        bronnen_gebruikt: Optional[str] = None,
        contexten: Optional[Dict[str, List[str]]] = None,
        organisatie_context: Optional[str] = None,
        gebruik_logging: bool = False
    ) -> ToetsregelValidationResult:
        """
        Valideer definitie met rich output.
        
        Args:
            definitie: Definitie tekst om te valideren
            categorie: Ontologische categorie
            toetsregels: Optionele toetsregels (anders alle regels)
            begrip: Term die gedefinieerd wordt
            marker: Categorie marker
            voorkeursterm: Voorkeurs term
            bronnen_gebruikt: Gebruikte bronnen
            contexten: Context informatie
            organisatie_context: Organisatie specifieke context
            gebruik_logging: Of logging gebruikt moet worden
            
        Returns:
            ToetsregelValidationResult met complete validatie informatie
        """
        if gebruik_logging:
            logger.info(f"Start rich validation voor term: {begrip}")
        
        # Haal toetsregels op indien niet meegegeven
        if toetsregels is None:
            toetsregels = self._get_applicable_rules(categorie)
        
        # Gebruik de basis validate_definition methode
        string_results = self.validate_definition(
            definitie=definitie,
            toetsregels=toetsregels,
            begrip=begrip,
            marker=marker or (categorie.value if categorie else None),
            voorkeursterm=voorkeursterm,
            bronnen_gebruikt=bronnen_gebruikt,
            contexten=contexten,
            gebruik_logging=gebruik_logging
        )
        
        # Converteer string results naar rich outputs
        outputs = self._convert_to_rich_outputs(string_results, toetsregels)
        
        # Creëer volledig validation result
        result = self._create_validation_result(definitie, outputs, categorie)
        
        if gebruik_logging:
            self._log_validation_summary(result)
        
        return result
    
    def _get_applicable_rules(self, categorie: Optional[OntologischeCategorie]) -> Dict[str, Dict]:
        """
        Haal toetsregels op die van toepassing zijn.
        
        Args:
            categorie: Ontologische categorie (optioneel)
            
        Returns:
            Dictionary met toetsregel configuraties
        """
        # Laad alle beschikbare regels
        all_rules = {}
        available_rules = self.rule_manager.get_available_regels()
        
        for rule_id in available_rules:
            regel = self.rule_manager.load_regel(rule_id)
            if regel:
                all_rules[rule_id] = regel
        
        if not categorie:
            return all_rules
        
        # Filter op categorie indien nodig
        applicable_rules = {}
        for rule_id, rule_config in all_rules.items():
            # Check of regel van toepassing is op deze categorie
            categories = rule_config.get("categorieën", [])
            if not categories or categorie.value in categories:
                applicable_rules[rule_id] = rule_config
        
        return applicable_rules
    
    def _convert_to_rich_outputs(
        self, 
        string_results: List[str],
        toetsregels: Dict[str, Dict]
    ) -> List[ValidationOutput]:
        """
        Converteer string results naar rich validation outputs.
        
        Args:
            string_results: Lijst met string resultaten
            toetsregels: Toetsregel configuraties
            
        Returns:
            Lijst van ValidationOutput objecten
        """
        outputs = []
        
        for result_str in string_results:
            # Skip de samenvatting regel
            if "Toetsing Samenvatting" in result_str:
                continue
            
            # Parse het resultaat
            output = self._parse_string_result(result_str, toetsregels)
            if output:
                outputs.append(output)
        
        return outputs
    
    def _parse_string_result(self, result_str: str, toetsregels: Dict) -> Optional[ValidationOutput]:
        """
        Parse een string resultaat naar ValidationOutput.
        
        Args:
            result_str: String resultaat van validator
            toetsregels: Toetsregel configuraties
            
        Returns:
            ValidationOutput of None
        """
        # Zoek naar bekende patterns
        for icon, result in [
            ("✅", ValidationResult.PASS),
            ("❌", ValidationResult.FAIL), 
            ("⚠️", ValidationResult.WARNING),
            ("🟡", ValidationResult.WARNING),
            ("⏭️", ValidationResult.INFO)
        ]:
            if icon in result_str:
                # Extract rule ID
                parts = result_str.split(":")
                if len(parts) >= 2:
                    rule_part = parts[0].replace(icon, "").strip()
                    # Zoek rule ID (bijv. "CON-01")
                    import re
                    match = re.search(r'([A-Z]{3}-\d{2})', rule_part)
                    if match:
                        rule_id = match.group(1)
                        message = ":".join(parts[1:]).strip()
                        
                        # Maak basis output
                        return ValidationOutput(
                            rule_id=rule_id,
                            result=result,
                            message=message
                        )
        
        return None
    
    def _create_validation_result(
        self, 
        definitie: str,
        outputs: List[ValidationOutput],
        categorie: Optional[OntologischeCategorie]
    ) -> ToetsregelValidationResult:
        """
        Creëer volledig validation result uit outputs.
        
        Args:
            definitie: Gevalideerde definitie
            outputs: Lijst van validation outputs
            categorie: Ontologische categorie
            
        Returns:
            ToetsregelValidationResult met alle details
        """
        # Categoriseer outputs
        passed_rules = []
        failed_rules = []
        warning_rules = []
        skipped_rules = []
        detailed_scores = {}
        
        for output in outputs:
            # Bereken score op basis van result
            if output.result == ValidationResult.PASS:
                score = 1.0
                passed_rules.append(output.rule_id)
            elif output.result == ValidationResult.FAIL:
                score = 0.0
                failed_rules.append(output.rule_id)
            elif output.result == ValidationResult.WARNING:
                score = 0.6
                warning_rules.append(output.rule_id)
            else:
                score = 0.5
                skipped_rules.append(output.rule_id)
            
            detailed_scores[output.rule_id] = score
        
        # Bereken overall score
        if outputs:
            overall_score = sum(detailed_scores.values()) / len(outputs)
        else:
            overall_score = 0.0
        
        # Bereken categorie compliance
        categorie_compliance = self._calculate_category_compliance(outputs, categorie)
        
        # Bepaal of definitie acceptabel is
        is_acceptable = (
            overall_score >= self.acceptance_thresholds["overall_score"] and
            len([o for o in outputs if o.result == ValidationResult.FAIL]) == 0
        )
        
        # Genereer verbetersuggesties
        suggestions = self._generate_improvement_suggestions(outputs)
        
        return ToetsregelValidationResult(
            definitie=definitie,
            overall_score=overall_score,
            outputs=outputs,
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            warning_rules=warning_rules,
            skipped_rules=skipped_rules,
            categorie_compliance=categorie_compliance,
            is_acceptable=is_acceptable,
            improvement_suggestions=suggestions,
            detailed_scores=detailed_scores
        )
    
    def _calculate_category_compliance(
        self,
        outputs: List[ValidationOutput],
        categorie: Optional[OntologischeCategorie]
    ) -> float:
        """
        Bereken compliance score voor specifieke categorie.
        
        Args:
            outputs: Validation outputs
            categorie: Ontologische categorie
            
        Returns:
            Compliance score (0.0 - 1.0)
        """
        if not categorie or not outputs:
            return 1.0
        
        # Filter outputs voor categorie-specifieke regels
        category_prefix = categorie.value[:3].upper()
        category_outputs = [
            o for o in outputs 
            if o.rule_id.startswith(category_prefix)
        ]
        
        if not category_outputs:
            return 1.0  # Geen categorie-specifieke regels
        
        # Bereken percentage passed
        passed = sum(1 for o in category_outputs if o.result == ValidationResult.PASS)
        return passed / len(category_outputs)
    
    def _generate_improvement_suggestions(
        self,
        outputs: List[ValidationOutput]
    ) -> List[str]:
        """
        Genereer concrete verbetersuggesties.
        
        Args:
            outputs: Validation outputs
            
        Returns:
            Lijst met suggesties
        """
        suggestions = []
        
        # Analyseer falende regels
        for output in outputs:
            if output.result == ValidationResult.FAIL:
                if "context" in output.message.lower():
                    suggestions.append("Herformuleer de definitie zonder de context expliciet te noemen")
                elif "bron" in output.message.lower():
                    suggestions.append("Voeg een authentieke bronvermelding toe")
                elif "zin" in output.message.lower():
                    suggestions.append("Vereenvoudig de definitie tot één duidelijke zin")
                elif "categorie" in output.message.lower():
                    suggestions.append("Maak de ontologische categorie expliciet")
        
        # Voeg algemene suggesties toe voor warnings
        warning_count = sum(1 for o in outputs if o.result == ValidationResult.WARNING)
        if warning_count > 3:
            suggestions.append("Overweeg de definitie te vereenvoudigen voor betere leesbaarheid")
        
        # Verwijder duplicaten en return
        return list(dict.fromkeys(suggestions))
    
    def _log_validation_summary(self, result: ToetsregelValidationResult):
        """Log samenvatting van validatie resultaat."""
        logger.info(f"Rich validation voltooid: {len(result.passed_rules)} geslaagd, "
                   f"{len(result.failed_rules)} gefaald, "
                   f"{len(result.warning_rules)} waarschuwingen")
        logger.info(f"Overall score: {result.overall_score:.2f}")
        logger.info(f"Definitie acceptabel: {result.is_acceptable}")


# Globale instantie voor gemakkelijk gebruik
enhanced_toetser = EnhancedModularToetser()


def validate_definitie_rich(
    definitie: str,
    categorie: Optional[OntologischeCategorie] = None,
    **kwargs
) -> ToetsregelValidationResult:
    """
    Hoofdfunctie voor rich definitie validatie.
    
    Args:
        definitie: Te valideren definitie
        categorie: Ontologische categorie
        **kwargs: Extra parameters voor validatie
        
    Returns:
        ToetsregelValidationResult met alle validatie informatie
    """
    return enhanced_toetser.validate_definition_rich(definitie, categorie, **kwargs)