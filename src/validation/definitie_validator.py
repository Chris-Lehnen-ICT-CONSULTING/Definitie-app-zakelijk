"""
DefinitieValidator Module - Intelligente definitie validatie met gedetailleerde feedback.
Interpreteert toetsregels als validatie criteria voor kwalitatieve beoordeling.

Deze module bevat de kwaliteitscontrole logica voor gegenereerde definities,
inclusief regel-gebaseerde validatie en score berekening.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json

from config.toetsregel_manager import get_toetsregel_manager, ToetsregelManager
from generation.definitie_generator import OntologischeCategorie

logger = logging.getLogger(__name__)


class ViolationSeverity(Enum):
    """Ernstigheidsniveaus voor regel violations."""
    CRITICAL = "critical"    # Verplicht + hoog prioriteit
    HIGH = "high"           # Verplicht
    MEDIUM = "medium"       # Hoog prioriteit
    LOW = "low"            # Aanbevolen


class ViolationType(Enum):
    """Types van regel violations."""
    FORBIDDEN_PATTERN = "forbidden_pattern"
    MISSING_ELEMENT = "missing_element"
    STRUCTURE_ISSUE = "structure_issue"
    CONTENT_ISSUE = "content_issue"
    CLARITY_ISSUE = "clarity_issue"


@dataclass
class ValidationCriterion:
    """Validatie criterium uit een toetsregel."""
    rule_id: str
    description: str
    patterns_to_avoid: List[str] = None      # Regex patronen om te vermijden
    required_elements: List[str] = None       # Vereiste elementen
    structure_checks: List[str] = None        # Structurele controles
    scoring_weight: float = 1.0               # Gewicht in totaalscore
    severity: ViolationSeverity = ViolationSeverity.MEDIUM  # Ernst niveau van de validatie regel
    
    def __post_init__(self):  # Post-initialisatie voor default waarden
        if self.patterns_to_avoid is None:
            self.patterns_to_avoid = []
        if self.required_elements is None:
            self.required_elements = []
        if self.structure_checks is None:
            self.structure_checks = []


@dataclass
class RuleViolation:
    """Specifieke regel overtreding."""
    rule_id: str
    rule_name: str
    violation_type: ViolationType
    severity: ViolationSeverity
    description: str
    detected_pattern: Optional[str] = None
    suggestion: Optional[str] = None
    position: Optional[int] = None  # Positie in tekst waar violation gevonden
    

@dataclass
class ValidationResult:
    """Resultaat van definitie validatie."""
    definitie: str
    overall_score: float                     # 0.0 - 1.0
    violations: List[RuleViolation]
    passed_rules: List[str]
    categorie_compliance: float              # Compliance voor specifieke categorie
    is_acceptable: bool                      # Of definitie geaccepteerd wordt
    improvement_suggestions: List[str]
    detailed_scores: Dict[str, float] = None # Score per regel
    
    def __post_init__(self):
        if self.detailed_scores is None:
            self.detailed_scores = {}
    
    def get_critical_violations(self) -> List[RuleViolation]:
        """Haal kritieke violations op."""
        return [v for v in self.violations if v.severity == ViolationSeverity.CRITICAL]
    
    def get_violation_count_by_severity(self) -> Dict[ViolationSeverity, int]:
        """Tel violations per severity."""
        counts = {severity: 0 for severity in ViolationSeverity}
        for violation in self.violations:
            counts[violation.severity] += 1
        return counts


class ValidationRegelInterpreter:
    """Interpreteert toetsregels voor validatie doeleinden.
    
    Deze klasse converteerd toetsregels naar validatie criteria
    die gebruikt kunnen worden voor automatische kwaliteitscontrole.
    """
    
    def __init__(self):
        self.rule_manager = get_toetsregel_manager()
    
    def for_validation(self, regel_data: Dict[str, Any]) -> ValidationCriterion:
        """
        Converteer toetsregel naar validatie criterium.
        
        Deze methode transformeert een toetsregel uit de configuratie
        naar een uitvoerbaar validatie criterium met patronen en checks.
        
        Args:
            regel_data: Regel data uit ToetsregelManager
            
        Returns:
            ValidationCriterion met validatie patronen en criteria
        """
        regel_id = regel_data.get("id", "")
        description = regel_data.get("uitleg", "")
        
        # Extraheer verboden patronen uit regel definitie
        patterns = self._extract_forbidden_patterns(regel_data)
        
        # Extraheer vereiste elementen voor validatie
        required = self._extract_required_elements(regel_data)
        
        # Structurele controles voor definitie kwaliteit
        structure = self._extract_structure_checks(regel_data)
        
        # Bepaal ernst niveau van regel overtreding
        severity = self._determine_severity(regel_data)
        
        # Bereken scoring gewicht op basis van prioriteit
        weight = self._calculate_weight(regel_data)
        
        return ValidationCriterion(
            rule_id=regel_id,
            description=description,
            patterns_to_avoid=patterns,
            required_elements=required,
            structure_checks=structure,
            scoring_weight=weight,
            severity=severity
        )
    
    def _extract_forbidden_patterns(self, regel_data: Dict[str, Any]) -> List[str]:
        """Extraheer verboden patronen uit regel.
        
        Args:
            regel_data: Regel configuratie data
            
        Returns:
            Lijst met regex patronen die vermeden moeten worden
        """
        regel_id = regel_data.get("id", "")
        
        # Gebruik bestaande herkenbare patronen uit regel configuratie
        base_patterns = regel_data.get("herkenbaar_patronen", [])
        
        # Regel-specifieke aanvullingen voor betere detectie
        additional_patterns = {
            "CON-01": [
                r"\b(in de context van|binnen de context|juridische context)\b",
                r"\b(DJI|OM|KMAR|Openbaar Ministerie)\b",
                r"\bvolgens het Wetboek van\b"
            ],
            "ESS-01": [
                r"\b(om te|met als doel|bedoeld om|teneinde|zodat)\b",
                r"\b(gericht op|ten behoeve van)\b"
            ],
            "INT-01": [
                r"\.\s+[A-Z]",  # Meerdere zinnen
                r";\s*[a-z]",   # Semicolon gevolgd door kleine letter (mogelijk nieuwe zin)
            ],
            "INT-03": [
                r"\b(deze|dit|die|daarvan)\b(?!\s+(begrip|definitie|regel))",  # Onduidelijke verwijzingen
            ],
            "STR-01": [
                r"^(is|de|het|een|wordt|betreft)\b",  # Start niet met artikel/hulpwerkwoord
            ],
            "STR-02": [
                r"\b(proces|activiteit|handeling|zaak|ding)\b(?!\s+\w+)",  # Vage termen zonder specificatie
            ]
        }
        
        all_patterns = base_patterns + additional_patterns.get(regel_id, [])
        return [pattern for pattern in all_patterns if pattern]  # Filter lege patronen
    
    def _extract_required_elements(self, regel_data: Dict[str, Any]) -> List[str]:
        """Extraheer vereiste elementen uit regel.
        
        Args:
            regel_data: Regel configuratie data
            
        Returns:
            Lijst met vereiste elementen die aanwezig moeten zijn
        """
        regel_id = regel_data.get("id", "")
        
        requirements = {
            "ESS-02": ["ontologische_categorie_expliciet"],
            "ESS-03": ["unieke_identificatie_criterium"],
            "ESS-04": ["objectief_toetsbaar_element"],
            "ESS-05": ["onderscheidend_kenmerk"],
            "INT-01": ["enkele_zin_structuur"],
            "STR-01": ["start_met_zelfstandig_naamwoord"],
            "CON-02": ["authentieke_bron_basis"]
        }
        
        return requirements.get(regel_id, [])
    
    def _extract_structure_checks(self, regel_data: Dict[str, Any]) -> List[str]:
        """Extraheer structurele controles uit regel.
        
        Args:
            regel_data: Regel configuratie data
            
        Returns:
            Lijst met structurele controles die uitgevoerd moeten worden
        """
        regel_id = regel_data.get("id", "")
        
        structure_checks = {
            "INT-01": ["max_one_sentence", "clear_structure"],
            "INT-03": ["clear_pronoun_references"],
            "INT-04": ["clear_article_references"],
            "STR-01": ["proper_noun_start"],
            "STR-02": ["concrete_terminology"],
            "ESS-02": ["explicit_ontological_category"]
        }
        
        return structure_checks.get(regel_id, [])
    
    def _determine_severity(self, regel_data: Dict[str, Any]) -> ViolationSeverity:
        """Bepaal severity op basis van prioriteit en aanbeveling.
        
        Args:
            regel_data: Regel configuratie data
            
        Returns:
            ViolationSeverity enum waarde
        """
        prioriteit = regel_data.get("prioriteit", "midden")
        aanbeveling = regel_data.get("aanbeveling", "optioneel")
        
        if aanbeveling == "verplicht" and prioriteit == "hoog":
            return ViolationSeverity.CRITICAL
        elif aanbeveling == "verplicht":
            return ViolationSeverity.HIGH
        elif prioriteit == "hoog":
            return ViolationSeverity.MEDIUM
        else:
            return ViolationSeverity.LOW
    
    def _calculate_weight(self, regel_data: Dict[str, Any]) -> float:
        """Bereken scoring weight voor regel.
        
        Args:
            regel_data: Regel configuratie data
            
        Returns:
            Float waarde voor scoring gewicht
        """
        prioriteit = regel_data.get("prioriteit", "midden")
        aanbeveling = regel_data.get("aanbeveling", "optioneel")
        
        # Base weight op prioriteit
        priority_weights = {"hoog": 1.0, "midden": 0.7, "laag": 0.4}
        base_weight = priority_weights.get(prioriteit, 0.5)
        
        # Multiplier op aanbeveling
        requirement_multipliers = {"verplicht": 1.5, "aanbevolen": 1.0, "optioneel": 0.8}
        multiplier = requirement_multipliers.get(aanbeveling, 1.0)
        
        return base_weight * multiplier


class DefinitieValidator:
    """Intelligente validator voor definities met gedetailleerde feedback.
    
    Deze klasse voert uitgebreide validatie uit op definities door toetsregels
    te interpreteren en toe te passen. Biedt gedetailleerde feedback en scores.
    """
    
    def __init__(self):
        self.rule_manager = get_toetsregel_manager()
        self.interpreter = ValidationRegelInterpreter()
        
        # Acceptatie criteria voor definitie goedkeuring
        self.acceptance_thresholds = {
            "overall_score": 0.8,           # 80% algehele naleving
            "critical_violations": 0,        # Geen kritieke violations
            "category_compliance": 0.75      # 75% categorie-specifieke naleving
        }
    
    def validate(
        self, 
        definitie: str, 
        categorie: OntologischeCategorie,
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Valideer definitie tegen toetsregels.
        
        Voert uitgebreide validatie uit door toetsregels te interpreteren
        en toe te passen op de definitie. Genereert gedetailleerde feedback.
        
        Args:
            definitie: Te valideren definitie
            categorie: Ontologische categorie
            context: Optionele context informatie
            
        Returns:
            ValidationResult met gedetailleerde feedback
        """
        logger.info(f"Valideren definitie voor categorie {categorie.value}: '{definitie[:50]}...'")
        
        # 1. Laad validatie criteria voor deze categorie
        criteria = self._load_validation_criteria(categorie)
        
        # 2. Voer validaties uit tegen alle criteria
        violations = []
        passed_rules = []
        detailed_scores = {}
        
        for criterium in criteria:
            rule_violations, rule_score = self._validate_against_criterion(definitie, criterium)
            
            detailed_scores[criterium.rule_id] = rule_score
            
            if rule_violations:
                violations.extend(rule_violations)
            else:
                passed_rules.append(criterium.rule_id)
        
        # 3. Bereken algehele en categorie-specifieke scores
        overall_score = self._calculate_overall_score(detailed_scores, criteria)
        category_compliance = self._calculate_category_compliance(detailed_scores, categorie)
        
        # 4. Bepaal of definitie acceptabel is
        is_acceptable = self._determine_acceptance(overall_score, violations, category_compliance)
        
        # 5. Genereer verbeteringsvoorstellen
        improvements = self._generate_improvement_suggestions(violations)
        
        return ValidationResult(
            definitie=definitie,
            overall_score=overall_score,
            violations=violations,
            passed_rules=passed_rules,
            categorie_compliance=category_compliance,
            is_acceptable=is_acceptable,
            improvement_suggestions=improvements,
            detailed_scores=detailed_scores
        )
    
    def _load_validation_criteria(self, categorie: OntologischeCategorie) -> List[ValidationCriterion]:
        """Laad relevante validatie criteria voor categorie.
        
        Args:
            categorie: Ontologische categorie
            
        Returns:
            Lijst met ValidationCriterion objecten
        """
        criteria = []
        
        # Laad kritieke regels die altijd van toepassing zijn
        kritieke_regels = self.rule_manager.get_kritieke_regels()
        
        # Laad categorie-specifieke regels
        categorie_regels = self.rule_manager.get_regels_voor_categorie(categorie.value)
        
        # Combineer en deduplicate regel sets
        alle_regels = {regel['id']: regel for regel in kritieke_regels + categorie_regels}
        
        # Converteer toetsregels naar validatie criteria
        for regel_data in alle_regels.values():
            criterium = self.interpreter.for_validation(regel_data)
            criteria.append(criterium)
        
        logger.debug(f"Geladen {len(criteria)} validatie criteria voor {categorie.value}")
        return criteria
    
    def _validate_against_criterion(
        self, 
        definitie: str, 
        criterium: ValidationCriterion
    ) -> Tuple[List[RuleViolation], float]:
        """Valideer definitie tegen specifiek criterium."""
        violations = []
        rule_score = 1.0  # Start met perfecte score
        
        # 1. Check forbidden patterns
        for pattern in criterium.patterns_to_avoid:
            matches = list(re.finditer(pattern, definitie, re.IGNORECASE))
            if matches:
                for match in matches:
                    violation = RuleViolation(
                        rule_id=criterium.rule_id,
                        rule_name=self._get_rule_name(criterium.rule_id),
                        violation_type=ViolationType.FORBIDDEN_PATTERN,
                        severity=criterium.severity,
                        description=f"Verboden patroon gevonden: '{match.group()}'",
                        detected_pattern=match.group(),
                        position=match.start(),
                        suggestion=self._get_pattern_suggestion(criterium.rule_id, match.group())
                    )
                    violations.append(violation)
                
                # Deduct score based on severity
                rule_score -= 0.3 * len(matches) * self._severity_multiplier(criterium.severity)
        
        # 2. Check required elements
        for required_element in criterium.required_elements:
            if not self._check_required_element(definitie, required_element, criterium.rule_id):
                violation = RuleViolation(
                    rule_id=criterium.rule_id,
                    rule_name=self._get_rule_name(criterium.rule_id),
                    violation_type=ViolationType.MISSING_ELEMENT,
                    severity=criterium.severity,
                    description=f"Vereist element ontbreekt: {required_element}",
                    suggestion=self._get_missing_element_suggestion(criterium.rule_id, required_element)
                )
                violations.append(violation)
                rule_score -= 0.4 * self._severity_multiplier(criterium.severity)
        
        # 3. Check structure requirements
        for structure_check in criterium.structure_checks:
            if not self._check_structure(definitie, structure_check):
                violation = RuleViolation(
                    rule_id=criterium.rule_id,
                    rule_name=self._get_rule_name(criterium.rule_id),
                    violation_type=ViolationType.STRUCTURE_ISSUE,
                    severity=criterium.severity,
                    description=f"Structuur probleem: {structure_check}",
                    suggestion=self._get_structure_suggestion(structure_check)
                )
                violations.append(violation)
                rule_score -= 0.25 * self._severity_multiplier(criterium.severity)
        
        # Ensure score doesn't go below 0
        rule_score = max(0.0, rule_score)
        
        return violations, rule_score
    
    def _check_required_element(self, definitie: str, element: str, rule_id: str) -> bool:
        """Check of vereist element aanwezig is."""
        element_checks = {
            "ontologische_categorie_expliciet": lambda d: self._has_ontological_category(d),
            "unieke_identificatie_criterium": lambda d: self._has_unique_identification(d),
            "objectief_toetsbaar_element": lambda d: self._has_testable_element(d),
            "onderscheidend_kenmerk": lambda d: self._has_distinguishing_feature(d),
            "enkele_zin_structuur": lambda d: self._is_single_sentence(d),
            "start_met_zelfstandig_naamwoord": lambda d: self._starts_with_noun(d),
            "authentieke_bron_basis": lambda d: self._has_authentic_source_basis(d)
        }
        
        checker = element_checks.get(element)
        return checker(definitie) if checker else True
    
    def _check_structure(self, definitie: str, structure_check: str) -> bool:
        """Check structurele vereiste."""
        structure_checkers = {
            "max_one_sentence": lambda d: len(re.split(r'[.!?]+', d.strip())) <= 2,  # Allow empty string after split
            "clear_structure": lambda d: len(d.split()) >= 5,  # Minimum woorden voor duidelijkheid
            "clear_pronoun_references": lambda d: not re.search(r'\b(deze|dit|die)\b(?!\s+(begrip|definitie))', d),
            "clear_article_references": lambda d: not re.search(r'\bde\s+(proces|activiteit)\b(?!\s+\w+)', d),
            "proper_noun_start": lambda d: self._starts_with_noun(d),
            "concrete_terminology": lambda d: not re.search(r'\b(proces|activiteit|zaak|ding)\b(?!\s+\w+)', d),
            "explicit_ontological_category": lambda d: self._has_ontological_category(d)
        }
        
        checker = structure_checkers.get(structure_check)
        return checker(definitie) if checker else True
    
    def _has_ontological_category(self, definitie: str) -> bool:
        """Check of ontologische categorie expliciet is."""
        # Zoek naar indicatoren van categorie
        type_indicators = r'\b(soort|type|categorie|klasse)\b'
        process_indicators = r'\b(proces|activiteit|handeling|procedure)\b'
        result_indicators = r'\b(resultaat|uitkomst|product|effect)\b'
        instance_indicators = r'\b(exemplaar|instantie|specifiek)\b'
        
        return bool(re.search(f'({type_indicators}|{process_indicators}|{result_indicators}|{instance_indicators})', 
                            definitie, re.IGNORECASE))
    
    def _has_unique_identification(self, definitie: str) -> bool:
        """Check of unieke identificatie criterium aanwezig is."""
        unique_indicators = r'\b(uniek|specifiek|identificeer|registratie|nummer|code|id)\b'
        return bool(re.search(unique_indicators, definitie, re.IGNORECASE))
    
    def _has_testable_element(self, definitie: str) -> bool:
        """Check of objectief toetsbaar element aanwezig is."""
        testable_indicators = r'\b(\d+|binnen|na|voor|volgens|conform|gebaseerd op)\b'
        return bool(re.search(testable_indicators, definitie, re.IGNORECASE))
    
    def _has_distinguishing_feature(self, definitie: str) -> bool:
        """Check of onderscheidend kenmerk aanwezig is."""
        # Check op specificerende elementen
        distinguishing_patterns = r'\b(onderscheidt|specifiek|bijzonder|kenmerk|eigenschap)\b'
        return bool(re.search(distinguishing_patterns, definitie, re.IGNORECASE)) or len(definitie.split()) > 8
    
    def _is_single_sentence(self, definitie: str) -> bool:
        """Check of definitie één zin is."""
        sentence_endings = re.findall(r'[.!?]+', definitie.strip())
        return len(sentence_endings) <= 1
    
    def _starts_with_noun(self, definitie: str) -> bool:
        """Check of definitie start met zelfstandig naamwoord."""
        # Check of het NIET start met verboden woorden
        forbidden_starts = r'^(is|de|het|een|wordt|betreft|zijn|kan|moet|mag)\b'
        return not bool(re.search(forbidden_starts, definitie.strip(), re.IGNORECASE))
    
    def _has_authentic_source_basis(self, definitie: str) -> bool:
        """Check of definitie gebaseerd is op authentieke bron."""
        source_indicators = r'\b(volgens|conform|gebaseerd|bepaald|bedoeld|wet|regeling)\b'
        return bool(re.search(source_indicators, definitie, re.IGNORECASE))
    
    def _severity_multiplier(self, severity: ViolationSeverity) -> float:
        """Haal multiplier op voor severity."""
        multipliers = {
            ViolationSeverity.CRITICAL: 2.0,
            ViolationSeverity.HIGH: 1.5,
            ViolationSeverity.MEDIUM: 1.0,
            ViolationSeverity.LOW: 0.5
        }
        return multipliers.get(severity, 1.0)
    
    def _get_rule_name(self, rule_id: str) -> str:
        """Haal regel naam op."""
        regel = self.rule_manager.load_regel(rule_id)
        return regel.get("naam", rule_id) if regel else rule_id
    
    def _get_pattern_suggestion(self, rule_id: str, pattern: str) -> str:
        """Genereer suggestie voor verboden patroon."""
        suggestions = {
            "CON-01": "Vermijd expliciete context vermelding. Maak de definitie context-specifiek zonder de context te benoemen.",
            "ESS-01": "Beschrijf wat het begrip IS, niet wat het doel is. Gebruik 'is/betreft' in plaats van 'om te'.",
            "INT-03": "Gebruik concrete verwijzingen. Vervang 'deze/dit/die' door het specifieke begrip.",
            "STR-01": "Start met het kernzelfstandig naamwoord dat het begrip weergeeft."
        }
        return suggestions.get(rule_id, f"Vermijd het gebruik van '{pattern}' in de definitie.")
    
    def _get_missing_element_suggestion(self, rule_id: str, element: str) -> str:
        """Genereer suggestie voor ontbrekend element."""
        suggestions = {
            "ESS-02": "Maak expliciet of het begrip een type, proces, resultaat of exemplaar betreft.",
            "ESS-03": "Voeg unieke identificerende kenmerken toe om verschillende instanties te onderscheiden.",
            "ESS-04": "Voeg objectief toetsbare elementen toe zoals aantallen, deadlines of meetbare criteria.",
            "ESS-05": "Benadruk wat dit begrip onderscheidt van gerelateerde begrippen.",
            "STR-01": "Start de definitie met het centrale zelfstandig naamwoord."
        }
        return suggestions.get(rule_id, f"Voeg ontbrekend element toe: {element}")
    
    def _get_structure_suggestion(self, structure_check: str) -> str:
        """Genereer suggestie voor structuur probleem."""
        suggestions = {
            "max_one_sentence": "Formuleer de definitie als één enkele zin.",
            "clear_pronoun_references": "Vervang onduidelijke verwijzingen door concrete begrippen.",
            "proper_noun_start": "Start met het kernzelfstandig naamwoord.",
            "concrete_terminology": "Gebruik specifieke termen in plaats van vage begrippen."
        }
        return suggestions.get(structure_check, f"Verbeter structuur: {structure_check}")
    
    def _calculate_overall_score(
        self, 
        detailed_scores: Dict[str, float], 
        criteria: List[ValidationCriterion]
    ) -> float:
        """Bereken overall compliance score."""
        if not detailed_scores:
            return 0.0
        
        # Weighted average based on rule importance
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for criterium in criteria:
            if criterium.rule_id in detailed_scores:
                score = detailed_scores[criterium.rule_id]
                weight = criterium.scoring_weight
                total_weighted_score += score * weight
                total_weight += weight
        
        return total_weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _calculate_category_compliance(
        self, 
        detailed_scores: Dict[str, float], 
        categorie: OntologischeCategorie
    ) -> float:
        """Bereken category-specifieke compliance."""
        # Voor nu simple average van alle scores
        # Later kunnen we category-specifieke weights toevoegen
        if not detailed_scores:
            return 0.0
        
        return sum(detailed_scores.values()) / len(detailed_scores)
    
    def _determine_acceptance(
        self, 
        overall_score: float, 
        violations: List[RuleViolation], 
        category_compliance: float
    ) -> bool:
        """Bepaal of definitie geaccepteerd wordt."""
        # Check critical violations
        critical_violations = [v for v in violations if v.severity == ViolationSeverity.CRITICAL]
        if len(critical_violations) > self.acceptance_thresholds["critical_violations"]:
            return False
        
        # Check overall score
        if overall_score < self.acceptance_thresholds["overall_score"]:
            return False
        
        # Check category compliance
        if category_compliance < self.acceptance_thresholds["category_compliance"]:
            return False
        
        return True
    
    def _generate_improvement_suggestions(self, violations: List[RuleViolation]) -> List[str]:
        """Genereer improvement suggestions op basis van violations."""
        suggestions = []
        
        # Group violations by type
        violation_groups = {}
        for violation in violations:
            v_type = violation.violation_type
            if v_type not in violation_groups:
                violation_groups[v_type] = []
            violation_groups[v_type].append(violation)
        
        # Generate suggestions per type
        for v_type, v_list in violation_groups.items():
            if v_type == ViolationType.FORBIDDEN_PATTERN:
                patterns = [v.detected_pattern for v in v_list if v.detected_pattern]
                if patterns:
                    suggestions.append(f"Vermijd deze patronen: {', '.join(set(patterns))}")
            
            elif v_type == ViolationType.MISSING_ELEMENT:
                missing = [v.description.split(': ')[1] for v in v_list]
                if missing:
                    suggestions.append(f"Voeg toe: {', '.join(set(missing))}")
            
            elif v_type == ViolationType.STRUCTURE_ISSUE:
                suggestions.append("Verbeter de structuur: gebruik één duidelijke zin die start met een zelfstandig naamwoord")
        
        # Voeg specifieke suggesties toe uit violations
        for violation in violations:
            if violation.suggestion and violation.suggestion not in suggestions:
                suggestions.append(violation.suggestion)
        
        return suggestions[:5]  # Limiteer tot 5 belangrijkste suggesties


# Convenience functions
def validate_definitie(
    definitie: str,
    categorie: str = "type",
    context: Optional[Dict[str, Any]] = None
) -> ValidationResult:
    """
    Convenience functie voor snelle definitie validatie.
    
    Args:
        definitie: Te valideren definitie
        categorie: Ontologische categorie ("type", "proces", "resultaat", "exemplaar")
        context: Optionele context informatie
        
    Returns:
        ValidationResult met gedetailleerde feedback
    """
    validator = DefinitieValidator()
    
    # Converteer string naar enum
    cat_mapping = {
        "type": OntologischeCategorie.TYPE,
        "proces": OntologischeCategorie.PROCES,
        "resultaat": OntologischeCategorie.RESULTAAT,
        "exemplaar": OntologischeCategorie.EXEMPLAAR
    }
    
    cat_enum = cat_mapping.get(categorie.lower(), OntologischeCategorie.TYPE)
    
    return validator.validate(definitie, cat_enum, context)


# Additional validator functionality from validatie_toetsregels/validator.py
def valideer_toetsregels_consistentie(
    json_path: Optional[str] = None,
    python_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Valideer consistentie tussen JSON toetsregels en Python implementaties.
    Geïntegreerde versie van validatie_toetsregels/validator.py
    
    Args:
        json_path: Pad naar toetsregels JSON (optioneel)
        python_path: Pad naar Python implementatie (optioneel)
        
    Returns:
        Dictionary met validatie resultaten
    """
    import os
    from pathlib import Path
    from config.config_loader import load_toetsregels
    
    # Default paths
    if not json_path:
        json_path = Path(__file__).parents[1] / "config" / "toetsregels.json"
    if not python_path:
        python_path = Path(__file__).parents[1] / "ai_toetser" / "core.py"
    
    # Load JSON rules
    try:
        data = load_toetsregels(str(json_path)) if json_path else load_toetsregels()
        json_regels = data.get("regels", {})
    except Exception as e:
        return {"error": f"Kon JSON niet laden: {str(e)}"}
    
    # Detect functions in Python code
    try:
        with open(python_path, "r", encoding="utf-8") as f:
            inhoud = f.read()
        
        matches = re.findall(r"def\s+toets_([A-Z0-9_]+)\s*\(", inhoud)
        code_ids = {match.replace("_", "-") for match in matches}
    except Exception as e:
        return {"error": f"Kon Python code niet analyseren: {str(e)}"}
    
    # Perform validation
    results = {
        "json_rules_count": len(json_regels),
        "python_functions_count": len(code_ids),
        "missing_in_code": [],
        "missing_in_json": [],
        "incomplete_rules": [],
        "consistent_rules": [],
        "consistency_percentage": 0.0
    }
    
    # Check missing functions
    results["missing_in_code"] = [rid for rid in json_regels if rid not in code_ids]
    
    # Check missing JSON entries
    results["missing_in_json"] = [cid for cid in code_ids if cid not in json_regels]
    
    # Check incomplete rules
    for rid, data in json_regels.items():
        issues = []
        if "uitleg" not in data or not isinstance(data["uitleg"], str) or not data["uitleg"].strip():
            issues.append("uitleg ontbreekt")
        if "herkenbaar_patronen" not in data or not data["herkenbaar_patronen"]:
            issues.append("herkenbare patronen ontbreken")
        
        if issues:
            results["incomplete_rules"].append({
                "rule_id": rid,
                "issues": issues
            })
    
    # Check consistent rules
    results["consistent_rules"] = [
        rid for rid in json_regels
        if rid in code_ids
        and isinstance(json_regels[rid].get("uitleg"), str) and json_regels[rid]["uitleg"].strip()
        and "herkenbaar_patronen" in json_regels[rid] and json_regels[rid]["herkenbaar_patronen"]
    ]
    
    # Calculate consistency percentage
    if json_regels:
        results["consistency_percentage"] = (len(results["consistent_rules"]) / len(json_regels)) * 100
    
    return results


def format_consistency_report(results: Dict[str, Any]) -> str:
    """
    Format consistency validation results as a readable report.
    
    Args:
        results: Results from valideer_toetsregels_consistentie()
        
    Returns:
        Formatted report string
    """
    if "error" in results:
        return f"❌ Fout: {results['error']}"
    
    report_lines = [
        "\n📊 VALIDATIERAPPORT TOETSREGELS CONSISTENTIE",
        "=" * 50,
        f"📋 JSON regels: {results['json_rules_count']}",
        f"🐍 Python functies: {results['python_functions_count']}",
        f"✅ Consistente regels: {len(results['consistent_rules'])} ({results['consistency_percentage']:.1f}%)",
        ""
    ]
    
    # Missing functions
    if results["missing_in_code"]:
        report_lines.append("🟥 ONTBREKENDE FUNCTIES IN PYTHON:")
        for rule_id in results["missing_in_code"]:
            report_lines.append(f"   - {rule_id}")
        report_lines.append("")
    else:
        report_lines.append("✅ Alle JSON regels hebben een Python functie")
        report_lines.append("")
    
    # Missing JSON entries
    if results["missing_in_json"]:
        report_lines.append("🟨 PYTHON FUNCTIES ZONDER JSON REGEL:")
        for func_id in results["missing_in_json"]:
            report_lines.append(f"   - {func_id}")
        report_lines.append("")
    
    # Incomplete rules
    if results["incomplete_rules"]:
        report_lines.append("🟨 ONVOLLEDIGE REGELS IN JSON:")
        for incomplete in results["incomplete_rules"]:
            issues_str = " | ".join(incomplete["issues"])
            report_lines.append(f"   - {incomplete['rule_id']}: {issues_str}")
        report_lines.append("")
    
    # Summary
    if results["consistency_percentage"] >= 90:
        report_lines.append("🎉 UITSTEKENDE CONSISTENTIE!")
    elif results["consistency_percentage"] >= 75:
        report_lines.append("✅ GOEDE CONSISTENTIE")
    elif results["consistency_percentage"] >= 50:
        report_lines.append("⚠️ MATIGE CONSISTENTIE - VERBETERING NODIG")
    else:
        report_lines.append("❌ SLECHTE CONSISTENTIE - ACTIE VEREIST")
    
    return "\n".join(report_lines)


if __name__ == "__main__":
    # Test de DefinitieValidator
    print("🔍 Testing DefinitieValidator")
    print("=" * 30)
    
    # Test ValidationRegelInterpreter
    interpreter = ValidationRegelInterpreter()
    rule_manager = get_toetsregel_manager()
    
    # Test met CON-01 regel
    con01 = rule_manager.load_regel("CON-01")
    if con01:
        criterium = interpreter.for_validation(con01)
        print(f"✅ CON-01 criterium: {criterium.description[:80]}...")
        print(f"🚫 Patronen om te vermijden: {len(criterium.patterns_to_avoid)}")
        print(f"⚠️ Severity: {criterium.severity.value}")
    
    # Test DefinitieValidator
    validator = DefinitieValidator()
    
    # Test slechte definitie
    slechte_definitie = "Toezicht is een proces om te controleren binnen DJI context"
    result = validator.validate(slechte_definitie, OntologischeCategorie.PROCES)
    
    print(f"\n🔍 Validatie slechte definitie:")
    print(f"📊 Overall score: {result.overall_score:.2f}")
    print(f"❌ Violations: {len(result.violations)}")
    print(f"✅ Passed rules: {len(result.passed_rules)}")
    print(f"🎯 Acceptable: {result.is_acceptable}")
    
    # Toon violations
    for violation in result.violations[:3]:  # Eerste 3
        print(f"   - {violation.rule_id}: {violation.description}")
    
    # Test goede definitie
    goede_definitie = "Verificatie waarbij identiteitsgegevens systematisch worden gecontroleerd tegen authentieke bronregistraties"
    result2 = validator.validate(goede_definitie, OntologischeCategorie.PROCES)
    
    print(f"\n✅ Validatie goede definitie:")
    print(f"📊 Overall score: {result2.overall_score:.2f}")
    print(f"❌ Violations: {len(result2.violations)}")
    print(f"✅ Passed rules: {len(result2.passed_rules)}")
    print(f"🎯 Acceptable: {result2.is_acceptable}")
    
    # Test convenience function
    quick_result = validate_definitie("Registratie is het vastleggen van gegevens", "proces")
    print(f"\n🔧 Quick validatie: Score {quick_result.overall_score:.2f}, Violations: {len(quick_result.violations)}")
    
    # Test consistentie validatie
    print("\n🔍 Testing Consistentie Validatie:")
    consistency_results = valideer_toetsregels_consistentie()
    consistency_report = format_consistency_report(consistency_results)
    print(consistency_report)
    
    print("\n🎯 DefinitieValidator test voltooid!")