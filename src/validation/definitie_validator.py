"""
DefinitieValidator Module - Intelligente definitie validatie met gedetailleerde feedback.
Interpreteert toetsregels als validatie criteria voor kwalitatieve beoordeling.

Deze module bevat de kwaliteitscontrole logica voor gegenereerde definities,
inclusief regel-gebaseerde validatie en score berekening.
"""

import json
import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from domain.ontological_categories import OntologischeCategorie
from toetsregels.manager import get_toetsregel_manager

logger = logging.getLogger(__name__)


class ViolationSeverity(Enum):
    """Ernstigheidsniveaus voor regel violations."""

    CRITICAL = "critical"  # Verplicht + hoog prioriteit
    HIGH = "high"  # Verplicht
    MEDIUM = "medium"  # Hoog prioriteit
    LOW = "low"  # Aanbevolen


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
    patterns_to_avoid: list[str] = None  # Regex patronen om te vermijden
    required_elements: list[str] = None  # Vereiste elementen
    structure_checks: list[str] = None  # Structurele controles
    scoring_weight: float = 1.0  # Gewicht in totaalscore
    severity: ViolationSeverity = (
        ViolationSeverity.MEDIUM
    )  # Ernst niveau van de validatie regel

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
    detected_pattern: str | None = None
    suggestion: str | None = None
    position: int | None = None  # Positie in tekst waar violation gevonden


@dataclass
class ValidationResult:
    """Resultaat van definitie validatie."""

    definitie: str
    overall_score: float  # 0.0 - 1.0
    violations: list[RuleViolation]
    passed_rules: list[str]
    categorie_compliance: float  # Compliance voor specifieke categorie
    is_acceptable: bool  # Of definitie geaccepteerd wordt
    improvement_suggestions: list[str]
    detailed_scores: dict[str, float] = None  # Score per regel

    def __post_init__(self):
        if self.detailed_scores is None:
            self.detailed_scores = {}

    def get_critical_violations(self) -> list[RuleViolation]:
        """Haal kritieke violations op."""
        return [v for v in self.violations if v.severity == ViolationSeverity.CRITICAL]

    def get_violation_count_by_severity(self) -> dict[ViolationSeverity, int]:
        """Tel violations per severity."""
        counts = dict.fromkeys(ViolationSeverity, 0)
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

    def for_validation(self, regel_data: dict[str, Any]) -> ValidationCriterion:
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
            severity=severity,
        )

    def _extract_forbidden_patterns(self, regel_data: dict[str, Any]) -> list[str]:
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
                r"\bvolgens het Wetboek van\b",
            ],
            "ESS-01": [
                r"\b(om te|met als doel|bedoeld om|teneinde|zodat)\b",
                r"\b(gericht op|ten behoeve van)\b",
            ],
            "INT-01": [
                r"\.\s+[A-Z]",  # Meerdere zinnen
                r";\s*[a-z]",  # Semicolon gevolgd door kleine letter (mogelijk nieuwe zin)
            ],
            "INT-03": [
                r"\b(deze|dit|die|daarvan)\b(?!\s+(begrip|definitie|regel))",  # Onduidelijke verwijzingen
            ],
            "STR-01": [
                r"^(is|de|het|een|wordt|betreft)\b",  # Start niet met artikel/hulpwerkwoord
            ],
            "STR-02": [
                r"\b(proces|activiteit|handeling|zaak|ding)\b(?!\s+\w+)",  # Vage termen zonder specificatie
            ],
        }

        all_patterns = base_patterns + additional_patterns.get(regel_id, [])
        return [pattern for pattern in all_patterns if pattern]  # Filter lege patronen

    def _extract_required_elements(self, regel_data: dict[str, Any]) -> list[str]:
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
            "CON-02": ["authentieke_bron_basis"],
        }

        return requirements.get(regel_id, [])

    def _extract_structure_checks(self, regel_data: dict[str, Any]) -> list[str]:
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
            "ESS-02": ["explicit_ontological_category"],
        }

        return structure_checks.get(regel_id, [])

    def _determine_severity(self, regel_data: dict[str, Any]) -> ViolationSeverity:
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
        if aanbeveling == "verplicht":
            return ViolationSeverity.HIGH
        if prioriteit == "hoog":
            return ViolationSeverity.MEDIUM
        return ViolationSeverity.LOW

    def _calculate_weight(self, regel_data: dict[str, Any]) -> float:
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
        requirement_multipliers = {
            "verplicht": 1.5,
            "aanbevolen": 1.0,
            "optioneel": 0.8,
        }
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
            "overall_score": 0.8,  # 80% algehele naleving
            "critical_violations": 0,  # Geen kritieke violations
            "category_compliance": 0.75,  # 75% categorie-specifieke naleving
        }

    def validate(
        self,
        definitie: str,
        categorie: OntologischeCategorie,
        context: dict[str, Any] | None = None,
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
        logger.info(
            f"Valideren definitie voor categorie {categorie.value}: '{definitie[:50]}...'"
        )

        # 1. Laad validatie criteria voor deze categorie
        criteria = self._load_validation_criteria(categorie)

        # 2. Voer validaties uit tegen alle criteria
        violations = []
        passed_rules = []
        detailed_scores = {}

        for criterium in criteria:
            rule_violations, rule_score = self._validate_against_criterion(
                definitie, criterium
            )

            detailed_scores[criterium.rule_id] = rule_score

            if rule_violations:
                violations.extend(rule_violations)
            else:
                passed_rules.append(criterium.rule_id)

        # 3. Bereken algehele en categorie-specifieke scores
        overall_score = self._calculate_overall_score(detailed_scores, criteria)
        category_compliance = self._calculate_category_compliance(
            detailed_scores, categorie
        )

        # 4. Bepaal of definitie acceptabel is
        is_acceptable = self._determine_acceptance(
            overall_score, violations, category_compliance
        )

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
            detailed_scores=detailed_scores,
        )

    def _load_validation_criteria(
        self, categorie: OntologischeCategorie
    ) -> list[ValidationCriterion]:
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
        alle_regels = {
            regel["id"]: regel for regel in kritieke_regels + categorie_regels
        }

        # Converteer toetsregels naar validatie criteria
        for regel_data in alle_regels.values():
            criterium = self.interpreter.for_validation(regel_data)
            criteria.append(criterium)

        logger.debug(
            f"Geladen {len(criteria)} validatie criteria voor {categorie.value}"
        )
        return criteria

    def _validate_against_criterion(
        self, definitie: str, criterium: ValidationCriterion
    ) -> tuple[list[RuleViolation], float]:
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
                        suggestion=self._get_pattern_suggestion(
                            criterium.rule_id, match.group()
                        ),
                    )
                    violations.append(violation)

                # Deduct score based on severity
                rule_score -= (
                    0.3 * len(matches) * self._severity_multiplier(criterium.severity)
                )

        # 2. Check required elements
        for required_element in criterium.required_elements:
            if not self._check_required_element(
                definitie, required_element, criterium.rule_id
            ):
                violation = RuleViolation(
                    rule_id=criterium.rule_id,
                    rule_name=self._get_rule_name(criterium.rule_id),
                    violation_type=ViolationType.MISSING_ELEMENT,
                    severity=criterium.severity,
                    description=f"Vereist element ontbreekt: {required_element}",
                    suggestion=self._get_missing_element_suggestion(
                        criterium.rule_id, required_element
                    ),
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
                    suggestion=self._get_structure_suggestion(structure_check),
                )
                violations.append(violation)
                rule_score -= 0.25 * self._severity_multiplier(criterium.severity)

        # Ensure score doesn't go below 0
        rule_score = max(0.0, rule_score)

        return violations, rule_score

    def _check_required_element(
        self, definitie: str, element: str, rule_id: str
    ) -> bool:
        """Check of vereist element aanwezig is."""
        element_checks = {
            "ontologische_categorie_expliciet": lambda d: self._has_ontological_category(
                d
            ),
            "unieke_identificatie_criterium": lambda d: self._has_unique_identification(
                d
            ),
            "objectief_toetsbaar_element": lambda d: self._has_testable_element(d),
            "onderscheidend_kenmerk": lambda d: self._has_distinguishing_feature(d),
            "enkele_zin_structuur": lambda d: self._is_single_sentence(d),
            "start_met_zelfstandig_naamwoord": lambda d: self._starts_with_noun(d),
            "authentieke_bron_basis": lambda d: self._has_authentic_source_basis(d),
        }

        checker = element_checks.get(element)
        return checker(definitie) if checker else True

    def _check_structure(self, definitie: str, structure_check: str) -> bool:
        """Check structurele vereiste."""
        structure_checkers = {
            "max_one_sentence": lambda d: len(re.split(r"[.!?]+", d.strip()))
            <= 2,  # Allow empty string after split
            "clear_structure": lambda d: len(d.split())
            >= 5,  # Minimum woorden voor duidelijkheid
            "clear_pronoun_references": lambda d: not re.search(
                r"\b(deze|dit|die)\b(?!\s+(begrip|definitie))", d
            ),
            "clear_article_references": lambda d: not re.search(
                r"\bde\s+(proces|activiteit)\b(?!\s+\w+)", d
            ),
            "proper_noun_start": lambda d: self._starts_with_noun(d),
            "concrete_terminology": lambda d: not re.search(
                r"\b(proces|activiteit|zaak|ding)\b(?!\s+\w+)", d
            ),
            "explicit_ontological_category": lambda d: self._has_ontological_category(
                d
            ),
        }

        checker = structure_checkers.get(structure_check)
        return checker(definitie) if checker else True

    def _has_ontological_category(self, definitie: str) -> bool:
        """Check of ontologische categorie expliciet is."""
        # Zoek naar indicatoren van categorie
        type_indicators = r"\b(soort|type|categorie|klasse)\b"
        process_indicators = r"\b(proces|activiteit|handeling|procedure)\b"
        result_indicators = r"\b(resultaat|uitkomst|product|effect)\b"
        instance_indicators = r"\b(exemplaar|instantie|specifiek)\b"

        return bool(
            re.search(
                f"({type_indicators}|{process_indicators}|{result_indicators}|{instance_indicators})",
                definitie,
                re.IGNORECASE,
            )
        )

    def _has_unique_identification(self, definitie: str) -> bool:
        """Check of unieke identificatie criterium aanwezig is."""
        unique_indicators = (
            r"\b(uniek|specifiek|identificeer|registratie|nummer|code|id)\b"
        )
        return bool(re.search(unique_indicators, definitie, re.IGNORECASE))

    def _has_testable_element(self, definitie: str) -> bool:
        """Check of objectief toetsbaar element aanwezig is."""
        testable_indicators = r"\b(\d+|binnen|na|voor|volgens|conform|gebaseerd op)\b"
        return bool(re.search(testable_indicators, definitie, re.IGNORECASE))

    def _has_distinguishing_feature(self, definitie: str) -> bool:
        """Check of onderscheidend kenmerk aanwezig is."""
        # Check op specificerende elementen
        distinguishing_patterns = (
            r"\b(onderscheidt|specifiek|bijzonder|kenmerk|eigenschap)\b"
        )
        return (
            bool(re.search(distinguishing_patterns, definitie, re.IGNORECASE))
            or len(definitie.split()) > 8
        )

    def _is_single_sentence(self, definitie: str) -> bool:
        """Check of definitie één zin is."""
        sentence_endings = re.findall(r"[.!?]+", definitie.strip())
        return len(sentence_endings) <= 1

    def _starts_with_noun(self, definitie: str) -> bool:
        """Check of definitie start met zelfstandig naamwoord."""
        # Check of het NIET start met verboden woorden
        forbidden_starts = r"^(is|de|het|een|wordt|betreft|zijn|kan|moet|mag)\b"
        return not bool(re.search(forbidden_starts, definitie.strip(), re.IGNORECASE))

    def _has_authentic_source_basis(self, definitie: str) -> bool:
        """Check of definitie gebaseerd is op authentieke bron."""
        source_indicators = (
            r"\b(volgens|conform|gebaseerd|bepaald|bedoeld|wet|regeling)\b"
        )
        return bool(re.search(source_indicators, definitie, re.IGNORECASE))

    def _severity_multiplier(self, severity: ViolationSeverity) -> float:
        """Haal multiplier op voor severity."""
        multipliers = {
            ViolationSeverity.CRITICAL: 2.0,
            ViolationSeverity.HIGH: 1.5,
            ViolationSeverity.MEDIUM: 1.0,
            ViolationSeverity.LOW: 0.5,
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
            "STR-01": "Start met het kernzelfstandig naamwoord dat het begrip weergeeft.",
        }
        return suggestions.get(
            rule_id, f"Vermijd het gebruik van '{pattern}' in de definitie."
        )

    def _get_missing_element_suggestion(self, rule_id: str, element: str) -> str:
        """Genereer suggestie voor ontbrekend element."""
        suggestions = {
            "ESS-02": "Maak expliciet of het begrip een type, proces, resultaat of exemplaar betreft.",
            "ESS-03": "Voeg unieke identificerende kenmerken toe om verschillende instanties te onderscheiden.",
            "ESS-04": "Voeg objectief toetsbare elementen toe zoals aantallen, deadlines of meetbare criteria.",
            "ESS-05": "Benadruk wat dit begrip onderscheidt van gerelateerde begrippen.",
            "STR-01": "Start de definitie met het centrale zelfstandig naamwoord.",
        }
        return suggestions.get(rule_id, f"Voeg ontbrekend element toe: {element}")

    def _get_structure_suggestion(self, structure_check: str) -> str:
        """Genereer suggestie voor structuur probleem."""
        suggestions = {
            "max_one_sentence": "Formuleer de definitie als één enkele zin.",
            "clear_pronoun_references": "Vervang onduidelijke verwijzingen door concrete begrippen.",
            "proper_noun_start": "Start met het kernzelfstandig naamwoord.",
            "concrete_terminology": "Gebruik specifieke termen in plaats van vage begrippen.",
        }
        return suggestions.get(
            structure_check, f"Verbeter structuur: {structure_check}"
        )

    def _calculate_overall_score(
        self, detailed_scores: dict[str, float], criteria: list[ValidationCriterion]
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
        self, detailed_scores: dict[str, float], categorie: OntologischeCategorie
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
        violations: list[RuleViolation],
        category_compliance: float,
    ) -> bool:
        """Bepaal of definitie geaccepteerd wordt."""
        # Check critical violations
        critical_violations = [
            v for v in violations if v.severity == ViolationSeverity.CRITICAL
        ]
        if len(critical_violations) > self.acceptance_thresholds["critical_violations"]:
            return False

        # Check overall score
        if overall_score < self.acceptance_thresholds["overall_score"]:
            return False

        # Check category compliance
        if category_compliance < self.acceptance_thresholds["category_compliance"]:
            return False

        return True

    def _generate_improvement_suggestions(
        self, violations: list[RuleViolation]
    ) -> list[str]:
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
                    suggestions.append(
                        f"Vermijd deze patronen: {', '.join(set(patterns))}"
                    )

            elif v_type == ViolationType.MISSING_ELEMENT:
                missing = [v.description.split(": ")[1] for v in v_list]
                if missing:
                    suggestions.append(f"Voeg toe: {', '.join(set(missing))}")

            elif v_type == ViolationType.STRUCTURE_ISSUE:
                suggestions.append(
                    "Verbeter de structuur: gebruik één duidelijke zin die start met een zelfstandig naamwoord"
                )

        # Voeg specifieke suggesties toe uit violations
        for violation in violations:
            if violation.suggestion and violation.suggestion not in suggestions:
                suggestions.append(violation.suggestion)

        return suggestions[:5]  # Limiteer tot 5 belangrijkste suggesties


# Convenience functions
def validate_definitie(
    definitie: str, categorie: str = "type", context: dict[str, Any] | None = None
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
        "exemplaar": OntologischeCategorie.EXEMPLAAR,
    }

    cat_enum = cat_mapping.get(categorie.lower(), OntologischeCategorie.TYPE)

    return validator.validate(definitie, cat_enum, context)


# Modular validator consistency checker
def valideer_modulaire_toetsregels_consistentie(
    regels_dir: str | None = None,
) -> dict[str, Any]:
    """
    Valideer consistentie tussen JSON configs en Python validators in modulaire architectuur.

    Controleert:
    - Of elke JSON een bijbehorende Python module heeft
    - Of elke Python module een bijbehorende JSON heeft
    - Of naamgeving consistent is (beide - of beide _)
    - Of Python modules de juiste validator class hebben

    Args:
        regels_dir: Pad naar regels directory (default: config/toetsregels/regels/)

    Returns:
        Dictionary met validatie resultaten
    """
    from pathlib import Path

    # Default path naar modulaire regels
    if not regels_dir:
        regels_dir = Path(__file__).parents[1] / "config" / "toetsregels" / "regels"
    else:
        regels_dir = Path(regels_dir)

    if not regels_dir.exists():
        return {"error": f"Regels directory bestaat niet: {regels_dir}"}

    # Verzamel alle JSON en Python bestanden
    json_files = {}
    python_files = {}

    for file in regels_dir.iterdir():
        if file.suffix == ".json":
            rule_id = file.stem
            json_files[rule_id] = file
        elif file.suffix == ".py" and file.stem != "__init__":
            rule_id = file.stem
            python_files[rule_id] = file

    # Analyseer resultaten
    results = {
        "json_count": len(json_files),
        "python_count": len(python_files),
        "missing_python": [],
        "missing_json": [],
        "naming_inconsistencies": [],
        "invalid_validators": [],
        "incomplete_rules": [],
        "consistent_rules": [],
        "consistency_percentage": 0.0,
    }

    # Check voor ontbrekende Python modules
    for json_id in json_files:
        # Probeer beide naamgevingen (- en _)
        python_id = json_id.replace("-", "_")
        if json_id not in python_files and python_id not in python_files:
            results["missing_python"].append(json_id)
        elif json_id not in python_files and python_id in python_files:
            results["naming_inconsistencies"].append(
                {
                    "json": json_id,
                    "python": python_id,
                    "issue": "JSON gebruikt '-', Python gebruikt '_'",
                }
            )

    # Check voor ontbrekende JSON configs
    for python_id in python_files:
        # Probeer beide naamgevingen (_ en -)
        json_id = python_id.replace("_", "-")
        if python_id not in json_files and json_id not in json_files:
            results["missing_json"].append(python_id)

    # Valideer Python module structuur
    for python_id, python_file in python_files.items():
        try:
            with open(python_file, encoding="utf-8") as f:
                content = f.read()

            # Check voor validator class
            class_name = f"{python_id.replace('_', '').replace('-', '')}Validator"
            if f"class {class_name}" not in content:
                # Probeer ook zonder underscore/dash
                alt_class_name = (
                    f"{python_id.upper().replace('_', '').replace('-', '')}Validator"
                )
                if f"class {alt_class_name}" not in content:
                    results["invalid_validators"].append(
                        {
                            "file": python_id,
                            "issue": f"Validator class '{class_name}' niet gevonden",
                        }
                    )

            # Check voor validate methode
            if "def validate(" not in content:
                results["invalid_validators"].append(
                    {"file": python_id, "issue": "validate() methode niet gevonden"}
                )
        except Exception as e:
            results["invalid_validators"].append(
                {"file": python_id, "issue": f"Kon bestand niet lezen: {e!s}"}
            )

    # Check JSON volledigheid
    for json_id, json_file in json_files.items():
        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)

            issues = []
            if "id" not in data:
                issues.append("id ontbreekt")
            if "naam" not in data or not data["naam"]:
                issues.append("naam ontbreekt")
            if "uitleg" not in data or not data["uitleg"]:
                issues.append("uitleg ontbreekt")

            if issues:
                results["incomplete_rules"].append(
                    {"rule_id": json_id, "issues": issues}
                )
            else:
                # Check of er een werkende Python module is
                python_id = json_id.replace("-", "_")
                if (json_id in python_files or python_id in python_files) and not any(
                    v["file"] == json_id or v["file"] == python_id
                    for v in results["invalid_validators"]
                ):
                    results["consistent_rules"].append(json_id)

        except Exception as e:
            results["incomplete_rules"].append(
                {"rule_id": json_id, "issues": [f"JSON parse error: {e!s}"]}
            )

    # Bereken consistentie percentage
    total_rules = max(len(json_files), len(python_files))
    if total_rules > 0:
        results["consistency_percentage"] = (
            len(results["consistent_rules"]) / total_rules
        ) * 100

    return results


def format_modulaire_consistency_report(results: dict[str, Any]) -> str:
    """
    Format modulaire consistency validation results as a readable report.

    Args:
        results: Results from valideer_modulaire_toetsregels_consistentie()

    Returns:
        Formatted report string
    """
    if "error" in results:
        return f"❌ Fout: {results['error']}"

    report_lines = [
        "\n📊 VALIDATIERAPPORT MODULAIRE TOETSREGELS",
        "=" * 50,
        f"📋 JSON configs: {results['json_count']}",
        f"🐍 Python modules: {results['python_count']}",
        f"✅ Consistente regels: {len(results['consistent_rules'])} ({results['consistency_percentage']:.1f}%)",
        "",
    ]

    # Naming inconsistencies (most important)
    if results["naming_inconsistencies"]:
        report_lines.append("🔴 NAAMGEVING INCONSISTENTIES:")
        for inc in results["naming_inconsistencies"]:
            report_lines.append(
                f"   - {inc['json']} (JSON) vs {inc['python']} (Python)"
            )
            report_lines.append(f"     → {inc['issue']}")
        report_lines.append("")

    # Missing Python modules
    if results["missing_python"]:
        report_lines.append("🟥 ONTBREKENDE PYTHON MODULES:")
        for rule_id in results["missing_python"]:
            report_lines.append(f"   - {rule_id}.py ontbreekt")
        report_lines.append("")

    # Missing JSON configs
    if results["missing_json"]:
        report_lines.append("🟨 PYTHON MODULES ZONDER JSON CONFIG:")
        for rule_id in results["missing_json"]:
            report_lines.append(f"   - {rule_id}.json ontbreekt")
        report_lines.append("")

    # Invalid validators
    if results["invalid_validators"]:
        report_lines.append("⚠️ ONGELDIGE VALIDATOR MODULES:")
        for invalid in results["invalid_validators"]:
            report_lines.append(f"   - {invalid['file']}: {invalid['issue']}")
        report_lines.append("")

    # Incomplete rules
    if results["incomplete_rules"]:
        report_lines.append("🟨 ONVOLLEDIGE JSON CONFIGS:")
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

    # Aanbevelingen
    if results["naming_inconsistencies"]:
        report_lines.append(
            "\n💡 AANBEVELING: Maak naamgeving consistent (gebruik overal - of overal _)"
        )

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

    print("\n🔍 Validatie slechte definitie:")
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

    print("\n✅ Validatie goede definitie:")
    print(f"📊 Overall score: {result2.overall_score:.2f}")
    print(f"❌ Violations: {len(result2.violations)}")
    print(f"✅ Passed rules: {len(result2.passed_rules)}")
    print(f"🎯 Acceptable: {result2.is_acceptable}")

    # Test convenience function
    quick_result = validate_definitie(
        "Registratie is het vastleggen van gegevens", "proces"
    )
    print(
        f"\n🔧 Quick validatie: Score {quick_result.overall_score:.2f}, Violations: {len(quick_result.violations)}"
    )

    # Test modulaire consistentie validatie
    print("\n🔍 Testing Modulaire Consistentie Validatie:")
    consistency_results = valideer_modulaire_toetsregels_consistentie()
    consistency_report = format_modulaire_consistency_report(consistency_results)
    print(consistency_report)

    print("\n🎯 DefinitieValidator test voltooid!")
