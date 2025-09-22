# V2 Validator Technical Enhancement Proposal

## Executive Summary

This proposal addresses critical feature gaps in the V2 validation architecture, specifically focusing on:
- Category-specific compliance scoring (currently all categories mirror overall score)
- Acceptance gates from legacy system (critical/overall/category thresholds)
- Severity mapping and multipliers for proper violation impact
- Violation metadata enrichment for better debugging and audit

## Current State Analysis

### Working Components
✅ **ValidationOrchestratorV2**: Clean async orchestration layer
✅ **ModularValidationService**: Rule evaluation with 45+ validation rules
✅ **ApprovalGatePolicy**: Gate policy configuration (but not integrated)
✅ **Schema Compliance**: JSON Schema validation for all outputs

### Identified Gaps

#### 1. Category Scoring (HIGH Priority)
**Current**: All category scores (`taal`, `juridisch`, `structuur`, `samenhang`) mirror overall score
```python
# Line 386-392 in modular_validation_service.py
detailed = {
    "taal": overall,
    "juridisch": overall,
    "structuur": overall,
    "samenhang": overall,
}
```

**Impact**: Cannot track category-specific improvements or violations

#### 2. Acceptance Gates Not Integrated
**Current**: Simple threshold check (`overall >= 0.75`)
**Missing**:
- Critical violation blocking
- Category minimum thresholds
- Soft vs hard requirements
- ApprovalGatePolicy integration

#### 3. Severity Mapping Issues
**Current**: Simplistic severity assignment
```python
# Line 814-820
if aan == "verplicht" or pri == "hoog":
    return "error"
return "warning"
```
**Missing**: Proper impact calculation, multipliers, critical flagging

#### 4. Violation Metadata
**Current**: Basic violation structure
**Missing**:
- Impact scores
- Fix complexity
- Violation counts per category
- Remediation guidance

## Technical Design

### 1. Category-Specific Scoring

#### Implementation Approach
Create category-aware aggregation that groups rules by category and calculates weighted scores per category.

```python
# New module: src/services/validation/category_scorer.py

from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class CategoryScoreResult:
    """Result of category-specific scoring."""
    category: str
    score: float
    rule_count: int
    violation_count: int
    critical_violations: List[str]

class CategoryScorer:
    """Calculate category-specific compliance scores."""

    RULE_CATEGORIES = {
        # Taal rules
        "ARAI-": "taal",
        "VER-": "taal",

        # Juridisch rules
        "ESS-": "juridisch",
        "VAL-": "juridisch",

        # Structuur rules
        "STR-": "structuur",
        "INT-": "structuur",

        # Samenhang rules
        "CON-": "samenhang",
        "SAM-": "samenhang",
    }

    def calculate_category_scores(
        self,
        rule_scores: Dict[str, float],
        violations: List[Dict],
        weights: Dict[str, float]
    ) -> Dict[str, CategoryScoreResult]:
        """Calculate weighted scores per category."""

        # Group rules by category
        category_groups = self._group_by_category(rule_scores)

        # Calculate per-category scores
        results = {}
        for category, rules in category_groups.items():
            # Get violations for this category
            cat_violations = [
                v for v in violations
                if self._get_category(v.get("code", "")) == category
            ]

            # Calculate weighted score for category
            cat_scores = {r: rule_scores[r] for r in rules}
            cat_weights = {r: weights.get(r, 0.5) for r in rules}
            weighted_score = self._calculate_weighted(cat_scores, cat_weights)

            # Find critical violations
            critical = [
                v["code"] for v in cat_violations
                if v.get("severity") == "error"
            ]

            results[category] = CategoryScoreResult(
                category=category,
                score=weighted_score,
                rule_count=len(rules),
                violation_count=len(cat_violations),
                critical_violations=critical
            )

        return results
```

#### Integration Point
Modify `modular_validation_service.py` line 386-392:
```python
# Replace simple mirroring with category calculation
category_scorer = CategoryScorer()
category_results = category_scorer.calculate_category_scores(
    rule_scores, violations, weights
)

detailed = {
    cat: result.score
    for cat, result in category_results.items()
}

# Add category metadata to result
result["category_details"] = {
    cat: {
        "score": res.score,
        "violations": res.violation_count,
        "critical": len(res.critical_violations) > 0
    }
    for cat, res in category_results.items()
}
```

### 2. Acceptance Gate Integration

#### Implementation Approach
Create gate evaluator that uses ApprovalGatePolicy to determine acceptability.

```python
# New module: src/services/validation/gate_evaluator.py

from dataclasses import dataclass
from typing import Dict, List, Optional
from services.policies.approval_gate_policy import GatePolicyService

@dataclass
class GateEvaluation:
    """Result of gate evaluation."""
    passed: bool
    hard_failures: List[str]
    soft_failures: List[str]
    override_possible: bool
    reason: str

class GateEvaluator:
    """Evaluate validation results against acceptance gates."""

    def __init__(self, policy_service: GatePolicyService):
        self.policy_service = policy_service

    def evaluate(
        self,
        overall_score: float,
        category_scores: Dict[str, float],
        violations: List[Dict],
        context: Optional[Dict] = None
    ) -> GateEvaluation:
        """Evaluate against all gate criteria."""

        policy = self.policy_service.get_policy()
        hard_failures = []
        soft_failures = []

        # Check critical violations
        critical_violations = [
            v for v in violations
            if v.get("severity") == "error" and
            v.get("code", "").startswith(("ESS-", "VAL-"))
        ]

        if critical_violations and policy.hard_requirements.get("forbid_critical_issues"):
            hard_failures.append(f"Critical violations: {len(critical_violations)}")

        # Check overall threshold
        if overall_score < policy.hard_min_score:
            hard_failures.append(
                f"Score {overall_score:.2f} below hard minimum {policy.hard_min_score}"
            )
        elif overall_score < policy.soft_min_score:
            soft_failures.append(
                f"Score {overall_score:.2f} below soft minimum {policy.soft_min_score}"
            )

        # Check category minimums
        category_mins = policy.thresholds.get("category_minimums", {})
        for cat, min_score in category_mins.items():
            if cat in category_scores and category_scores[cat] < min_score:
                msg = f"{cat} score {category_scores[cat]:.2f} below minimum {min_score}"
                if cat in ["juridisch", "structuur"]:
                    hard_failures.append(msg)
                else:
                    soft_failures.append(msg)

        # Check context requirement
        if policy.hard_requirements.get("min_one_context_required"):
            has_context = bool(
                context and (
                    context.get("organisatorische_context") or
                    context.get("juridische_context")
                )
            )
            if not has_context:
                hard_failures.append("No context provided (required)")

        # Determine result
        passed = len(hard_failures) == 0
        override_possible = (
            len(hard_failures) == 0 and
            len(soft_failures) > 0 and
            policy.soft_requirements.get("allow_high_issues_with_override", False)
        )

        reason = self._build_reason(hard_failures, soft_failures, passed)

        return GateEvaluation(
            passed=passed,
            hard_failures=hard_failures,
            soft_failures=soft_failures,
            override_possible=override_possible,
            reason=reason
        )
```

#### Integration Point
Modify `modular_validation_service.py` after line 384:
```python
# Evaluate against gates
if hasattr(self, "gate_evaluator"):
    gate_result = self.gate_evaluator.evaluate(
        overall_score=overall,
        category_scores=detailed,
        violations=violations,
        context=context
    )
    is_ok = gate_result.passed

    # Add gate metadata to result
    result["acceptance_gate"] = {
        "passed": gate_result.passed,
        "reason": gate_result.reason,
        "override_possible": gate_result.override_possible,
        "hard_failures": gate_result.hard_failures,
        "soft_failures": gate_result.soft_failures
    }
else:
    # Fallback to simple threshold
    is_ok = determine_acceptability(overall, self._overall_threshold)
```

### 3. Severity Mapping Enhancement

#### Implementation Approach
Create severity calculator with proper multipliers and impact assessment.

```python
# New module: src/services/validation/severity_calculator.py

from enum import Enum
from typing import Dict, Optional

class SeverityLevel(Enum):
    """Severity levels with multipliers."""
    CRITICAL = ("critical", 0.0)    # Blocks acceptance
    ERROR = ("error", 0.3)           # Major impact
    WARNING = ("warning", 0.7)       # Minor impact
    INFO = ("info", 0.9)            # Minimal impact

    def __init__(self, label: str, multiplier: float):
        self.label = label
        self.multiplier = multiplier

class SeverityCalculator:
    """Calculate proper severity and impact for violations."""

    CRITICAL_RULES = {
        "VAL-EMP-001",  # Empty definition
        "ESS-CONT-001", # No essential content
        "CON-CIRC-001", # Circular definition
    }

    HIGH_PRIORITY_RULES = {
        "ESS-02", "ESS-03", "ESS-04",  # Essential elements
        "VAL-LEN-001",                   # Too short
        "INT-01",                        # Not integral
    }

    def calculate_severity(
        self,
        rule_code: str,
        rule_metadata: Dict,
        violation_context: Optional[Dict] = None
    ) -> Dict:
        """Calculate severity with impact metadata."""

        # Determine base severity
        if rule_code in self.CRITICAL_RULES:
            severity = SeverityLevel.CRITICAL
        elif rule_code in self.HIGH_PRIORITY_RULES:
            severity = SeverityLevel.ERROR
        elif rule_metadata.get("aanbeveling") == "verplicht":
            severity = SeverityLevel.ERROR
        elif rule_metadata.get("prioriteit") == "hoog":
            severity = SeverityLevel.WARNING
        else:
            severity = SeverityLevel.INFO

        # Calculate impact score (0-1, where 0 is worst)
        impact_score = severity.multiplier

        # Adjust for context
        if violation_context:
            # Multiple violations of same type increase impact
            similar_count = violation_context.get("similar_violations", 0)
            if similar_count > 2:
                impact_score *= 0.8

            # Violations in juridisch category are more severe
            if violation_context.get("category") == "juridisch":
                impact_score *= 0.9

        # Determine remediation complexity
        complexity = self._calculate_fix_complexity(rule_code, rule_metadata)

        return {
            "severity": severity.label,
            "impact_score": round(impact_score, 2),
            "multiplier": severity.multiplier,
            "fix_complexity": complexity,
            "blocks_acceptance": severity == SeverityLevel.CRITICAL
        }

    def _calculate_fix_complexity(
        self,
        rule_code: str,
        rule_metadata: Dict
    ) -> str:
        """Estimate complexity to fix violation."""

        # Simple fixes (typos, formatting)
        if rule_code.startswith("STR-"):
            return "simple"

        # Moderate fixes (rewording, restructuring)
        if rule_code.startswith(("INT-", "SAM-")):
            return "moderate"

        # Complex fixes (missing content, fundamental issues)
        if rule_code.startswith(("ESS-", "VAL-")):
            return "complex"

        return "unknown"
```

#### Integration Point
Modify `_severity_for_json_rule` in `modular_validation_service.py`:
```python
def _severity_for_json_rule(self, rule: dict[str, Any]) -> str:
    """Calculate enhanced severity with metadata."""
    if hasattr(self, "severity_calculator"):
        result = self.severity_calculator.calculate_severity(
            rule_code=rule.get("id", ""),
            rule_metadata=rule,
            violation_context={
                "category": self._category_for(rule.get("id", "")),
                "similar_violations": self._count_similar_violations(rule.get("id", ""))
            }
        )
        # Store metadata for later use
        self._severity_metadata[rule.get("id", "")] = result
        return result["severity"]

    # Fallback to existing logic
    aan = str(rule.get("aanbeveling", "")).lower()
    pri = str(rule.get("prioriteit", "")).lower()
    if aan == "verplicht" or pri == "hoog":
        return "error"
    return "warning"
```

### 4. Violation Metadata Enrichment

#### Implementation Approach
Add comprehensive metadata to each violation for better debugging and remediation.

```python
# Enhancement in modular_validation_service.py

def _enrich_violation(
    self,
    violation: Dict[str, Any],
    rule_code: str,
    rule_metadata: Dict,
    context: EvaluationContext
) -> Dict[str, Any]:
    """Enrich violation with additional metadata."""

    # Add severity metadata if available
    if hasattr(self, "_severity_metadata") and rule_code in self._severity_metadata:
        violation["impact"] = self._severity_metadata[rule_code]

    # Add rule metadata
    violation["metadata"] = {
        "rule_priority": rule_metadata.get("prioriteit", "unknown"),
        "rule_recommendation": rule_metadata.get("aanbeveling", "unknown"),
        "category": self._category_for(rule_code),
        "fix_guidance": self._get_fix_guidance(rule_code),
        "examples": self._get_rule_examples(rule_code),
    }

    # Add occurrence information
    violation["occurrence"] = {
        "text_position": self._find_text_position(violation, context.cleaned_text),
        "frequency": self._count_pattern_matches(violation, context.cleaned_text),
    }

    # Add improvement metrics
    violation["improvement"] = {
        "estimated_score_gain": self._estimate_score_gain(rule_code, rule_metadata),
        "fix_priority": self._calculate_fix_priority(violation),
    }

    return violation

def _get_fix_guidance(self, rule_code: str) -> Dict[str, str]:
    """Get detailed fix guidance for a rule."""
    guidance_map = {
        "VAL-EMP-001": {
            "action": "Add definition text",
            "example": "Een [begrip] is een [genus] dat [differentia]",
            "tips": "Start with the genus (broader category) then add distinguishing features"
        },
        "ESS-02": {
            "action": "Make ontological category explicit",
            "example": "Use markers like 'soort', 'type', 'proces', 'resultaat'",
            "tips": "Choose one clear category marker and use consistently"
        },
        # ... more guidance
    }
    return guidance_map.get(rule_code, {
        "action": "Review and fix according to rule requirements",
        "example": "",
        "tips": "Check rule documentation for specific requirements"
    })
```

## Implementation Plan

### Phase 1: Category Scoring (Week 1)
1. **Day 1-2**: Implement CategoryScorer class
2. **Day 3**: Integrate with ModularValidationService
3. **Day 4**: Update tests for category scoring
4. **Day 5**: Validate against golden test cases

**Acceptance Criteria:**
- Each category has independent score calculation
- Category scores reflect actual rule violations in that category
- Backward compatibility maintained (overall_score unchanged)

### Phase 2: Gate Integration (Week 2)
1. **Day 1-2**: Implement GateEvaluator class
2. **Day 3**: Connect ApprovalGatePolicy to validation flow
3. **Day 4**: Add gate evaluation to orchestrator
4. **Day 5**: Test gate scenarios (hard/soft failures)

**Acceptance Criteria:**
- Gates properly block/allow based on policy
- Hard vs soft failures clearly distinguished
- Override mechanism works for soft failures

### Phase 3: Severity Enhancement (Week 3)
1. **Day 1-2**: Implement SeverityCalculator
2. **Day 3**: Add impact scoring to violations
3. **Day 4**: Integrate fix complexity estimation
4. **Day 5**: Test severity scenarios

**Acceptance Criteria:**
- Critical violations properly identified
- Impact scores accurately reflect violation severity
- Fix complexity helps prioritize remediation

### Phase 4: Metadata Enrichment (Week 4)
1. **Day 1-2**: Implement violation enrichment
2. **Day 3**: Add fix guidance system
3. **Day 4**: Add occurrence tracking
4. **Day 5**: Final integration testing

**Acceptance Criteria:**
- Violations include actionable fix guidance
- Metadata helps developers understand issues
- Performance impact < 10ms per validation

## Testing Strategy

### Unit Tests
```python
# tests/services/validation/test_category_scorer.py
def test_category_scoring_independence():
    """Test that category scores are calculated independently."""

def test_critical_violation_detection():
    """Test that critical violations are properly flagged."""

# tests/services/validation/test_gate_evaluator.py
def test_hard_gate_blocking():
    """Test that hard failures block acceptance."""

def test_soft_gate_override():
    """Test that soft failures can be overridden."""
```

### Integration Tests
```python
# tests/integration/test_v2_validation_flow.py
async def test_full_validation_with_gates():
    """Test complete validation flow with all enhancements."""

async def test_category_specific_improvements():
    """Test that fixing category-specific issues improves that category score."""
```

### Regression Tests
- Run existing test suite to ensure no breaking changes
- Validate against golden test cases
- Performance benchmarks (must stay within 10% of current)

## Migration Approach

### Non-Breaking Implementation
All changes are additive:
1. New fields added to ValidationResult (backward compatible)
2. Existing fields maintain same values/behavior
3. New components are optional (graceful degradation)

### Rollout Strategy
1. **Feature flags**: Each enhancement behind feature flag
2. **Gradual activation**: Enable per component in stages
3. **Monitoring**: Track validation metrics before/after
4. **Rollback plan**: Feature flags allow instant rollback

## Risk Assessment

### Technical Risks
| Risk | Impact | Likelihood | Mitigation |
|------|---------|------------|------------|
| Performance degradation | High | Low | Benchmark continuously, optimize hot paths |
| Category scoring inaccuracy | Medium | Medium | Extensive testing with real data |
| Gate policy conflicts | Medium | Low | Clear precedence rules, comprehensive tests |
| Breaking changes | High | Low | All changes additive, extensive regression tests |

### Implementation Risks
| Risk | Impact | Likelihood | Mitigation |
|------|---------|------------|------------|
| Scope creep | Medium | Medium | Strict phase boundaries, clear acceptance criteria |
| Integration complexity | Medium | Medium | Incremental integration, comprehensive tests |
| Testing coverage gaps | High | Low | 90%+ coverage requirement per component |

## Success Metrics

### Functional Metrics
- ✅ All 4 feature gaps addressed
- ✅ 100% backward compatibility
- ✅ Category scores accurately reflect violations
- ✅ Gates properly enforce policy

### Quality Metrics
- ✅ 90%+ test coverage on new code
- ✅ Performance within 10% of baseline
- ✅ Zero regression bugs in production
- ✅ Documentation complete for all components

## Conclusion

This proposal provides a comprehensive, incremental approach to enhancing the V2 validator. Each enhancement is:
- **Additive**: No breaking changes to existing contracts
- **Testable**: Clear acceptance criteria and test strategies
- **Measurable**: Defined success metrics
- **Reversible**: Feature flags enable rollback

The implementation prioritizes the highest-impact features (category scoring and gates) first, with complexity increasing gradually through the phases. This approach minimizes risk while delivering maximum value to the validation system.