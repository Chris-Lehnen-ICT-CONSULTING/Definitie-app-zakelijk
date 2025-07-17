"""
Rich validation models voor AI Toetser.

Deze module breidt de bestaande validatie uit met rijkere datastructuren
voor betere feedback en scoring mogelijkheden.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional

from .validators.base_validator import ValidationResult as BaseValidationResult, ValidationOutput


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
class RuleViolation:
    """Specifieke regel overtreding met gedetailleerde informatie."""
    rule_id: str
    rule_name: str
    violation_type: ViolationType
    severity: ViolationSeverity
    description: str
    detected_pattern: Optional[str] = None
    suggestion: Optional[str] = None
    position: Optional[int] = None


@dataclass
class RichValidationOutput(ValidationOutput):
    """
    Uitgebreide validation output met scoring en violations.
    
    Erft van de bestaande ValidationOutput voor compatibiliteit.
    """
    score: float = 1.0  # 1.0 = perfect, 0.0 = volledig gefaald
    violations: List[RuleViolation] = field(default_factory=list)
    rule_name: str = ""
    
    def to_basic_output(self) -> ValidationOutput:
        """Converteer naar basis ValidationOutput voor backward compatibility."""
        return ValidationOutput(
            rule_id=self.rule_id,
            result=self.result,
            message=self.message,
            details=self.details
        )


@dataclass
class ToetsregelValidationResult:
    """
    Volledig resultaat van definitie validatie met rijke informatie.
    
    Dit combineert alle individuele validation outputs tot een
    geaggregeerd resultaat met scores en suggesties.
    """
    definitie: str
    overall_score: float  # 0.0 - 1.0
    outputs: List[ValidationOutput]  # Kan zowel basic als rich outputs bevatten
    passed_rules: List[str]
    failed_rules: List[str]
    warning_rules: List[str]
    skipped_rules: List[str] = field(default_factory=list)
    categorie_compliance: float = 1.0
    is_acceptable: bool = True
    improvement_suggestions: List[str] = field(default_factory=list)
    detailed_scores: Dict[str, float] = field(default_factory=dict)
    
    @property
    def violations(self) -> List[RuleViolation]:
        """Verzamel alle violations uit rich outputs."""
        all_violations = []
        for output in self.outputs:
            if isinstance(output, RichValidationOutput):
                all_violations.extend(output.violations)
        return all_violations
    
    def get_critical_violations(self) -> List[RuleViolation]:
        """Haal kritieke violations op."""
        return [v for v in self.violations if v.severity == ViolationSeverity.CRITICAL]
    
    def get_violation_count_by_severity(self) -> Dict[ViolationSeverity, int]:
        """Tel violations per severity."""
        counts = {severity: 0 for severity in ViolationSeverity}
        for violation in self.violations:
            counts[violation.severity] += 1
        return counts
    
    def get_outputs_by_result(self, result: BaseValidationResult) -> List[ValidationOutput]:
        """Filter outputs op resultaat type."""
        return [o for o in self.outputs if o.result == result]
    
    def to_string_list(self) -> List[str]:
        """
        Converteer naar string lijst voor UI compatibiliteit.
        
        Returns:
            List[str] zoals de huidige UI verwacht
        """
        string_results = []
        
        # Voeg samenvatting toe
        if self.outputs:
            score_percentage = self.overall_score * 100
            passed = len(self.passed_rules)
            total = len(self.outputs)
            
            summary = f"📊 **Toetsing Samenvatting**: {passed}/{total} regels geslaagd ({score_percentage:.1f}%)"
            if self.failed_rules:
                summary += f" | ❌ {len(self.failed_rules)} gefaald"
            if self.warning_rules:
                summary += f" | ⚠️ {len(self.warning_rules)} waarschuwingen"
            
            string_results.append(summary)
        
        # Voeg individuele resultaten toe
        for output in self.outputs:
            string_results.append(str(output))
        
        return string_results