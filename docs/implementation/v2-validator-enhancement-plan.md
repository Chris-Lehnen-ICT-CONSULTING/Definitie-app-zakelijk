# V2 Validator Enhancement Plan - Final Consolidated Version

## Executive Summary
Direct enhancement of `ModularValidationService` to achieve feature parity with legacy validator. No new modules, no backwards compatibility, just targeted improvements delivered incrementally over 4 days.

## Core Principles
- **Refactor, don't preserve**: Following project philosophy - improve code, not compatibility
- **Direct enhancement**: Modify existing service, no new abstractions
- **Incremental value**: Each day delivers working improvements
- **User-focused**: Prioritize based on actual user impact

## Priority Order (Based on User Impact)

### 1. CRITICAL: Category Scoring & Acceptance Gates (Day 1)
**Why first**: Users cannot save definitions without proper validation gates. This blocks the primary workflow.

**Implementation**:
```python
# In modular_validation_service.py, line ~410 (in validate_definition)

# Add after line 415 (before result dict creation):
# Category aggregation
category_scores = self._aggregate_by_category(detailed)
category_acceptable = self._check_category_minimums(category_scores)

# Acceptance gate logic
gate_passed = is_ok and category_acceptable
if gate_passed and self._repository:
    # Check required fields for saving
    gate_passed = self._check_save_requirements(eval_ctx)

# Modify result dict (line 409):
result: dict[str, Any] = {
    "version": CONTRACT_VERSION,
    "overall_score": overall,
    "is_acceptable": gate_passed,  # Changed from is_ok
    "category_scores": category_scores,  # NEW
    "gate_status": {  # NEW
        "passed": gate_passed,
        "score_ok": is_ok,
        "categories_ok": category_acceptable,
        "save_ready": gate_passed and bool(eval_ctx.voorbeelden)
    },
    ...
}
```

**New methods to add**:
```python
def _aggregate_by_category(self, detailed_scores: dict[str, float]) -> dict[str, float]:
    """Aggregate scores by category prefix (ARAI, CON, ESS, etc.)."""
    categories = {}
    for code, score in detailed_scores.items():
        cat = code.split('-')[0] if '-' in code else 'OTHER'
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(score)

    # Calculate weighted average per category
    return {cat: sum(scores)/len(scores) for cat, scores in categories.items()}

def _check_category_minimums(self, category_scores: dict[str, float]) -> bool:
    """Check if all categories meet minimum thresholds."""
    minimums = {
        'ESS': 0.6,  # Essential content must score 60%+
        'CON': 0.5,  # Context must score 50%+
        'INT': 0.5,  # Integrity must score 50%+
    }
    for cat, min_score in minimums.items():
        if cat in category_scores and category_scores[cat] < min_score:
            return False
    return True
```

### 2. HIGH: Additional Pattern Support (Day 1-2)
**Why second**: Many rules fail to detect issues because patterns are missing. This directly impacts validation quality.

**Implementation**:
```python
# In modular_validation_service.py, line ~523 (_evaluate_json_rule method)

# Add at the beginning of the method:
from validation.additional_patterns import get_additional_patterns

# After line 540 (before special cases):
# Enhance with additional patterns
extra_patterns = get_additional_patterns(code)
if extra_patterns:
    if 'herkenbaar_patronen' in rule:
        rule['herkenbaar_patronen'].extend(extra_patterns)
    else:
        rule['herkenbaar_patronen'] = extra_patterns
```

### 3. HIGH: Comprehensive Rule Loading (Day 2)
**Why third**: Only 7 rules are active vs 45+ available. Users miss important validations.

**Implementation**:
```python
# In modular_validation_service.py, line ~94 (_load_rules_from_manager)

def _load_rules_from_manager(self):
    """Load ALL rules from ToetsregelManager, not just subset."""
    if not self.toetsregel_manager:
        return

    all_rules = self.toetsregel_manager.get_all_rules()

    # Build internal structures
    self._internal_rules = []
    self._weights = {}
    self._json_rules = {}

    for rule in all_rules:
        rule_id = rule.get('id', '')
        if not rule_id:
            continue

        self._internal_rules.append(rule_id)

        # Calculate weight from priority/recommendation
        priority = rule.get('prioriteit', 'laag')
        recommendation = rule.get('aanbeveling', 'optioneel')
        weight = self._calculate_rule_weight(priority, recommendation)
        self._weights[rule_id] = weight

        # Store full rule for JSON evaluation
        self._json_rules[rule_id] = rule
```

### 4. MEDIUM: Improved Suggestions (Day 2-3)
**Why fourth**: Users need actionable feedback to improve definitions.

**Implementation**:
```python
# In modular_validation_service.py, line ~444 (_suggestion_for_internal_rule)

def _suggestion_for_json_rule(self, rule: dict, ctx: EvaluationContext) -> str:
    """Generate contextual suggestion based on rule and violation."""
    rule_id = rule.get('id', '')

    # Map of rule patterns to suggestions
    suggestions = {
        'CON-01': "Vermijd expliciete context. Focus op wat het begrip IS, niet waar het gebruikt wordt.",
        'ESS-01': "Beschrijf WAT het is, niet het doel. Vermijd 'om te', 'bedoeld om'.",
        'INT-01': "Gebruik één enkele zin. Vermijd punt-komma of meerdere zinnen.",
        'STR-01': "Begin met het begrip zelf of een categorisering, niet met 'is' of 'het'.",
        'STR-02': "Wees specifieker. Vermijd vage termen zoals 'proces' of 'activiteit' zonder details.",
    }

    base_suggestion = suggestions.get(rule_id, rule.get('suggestie', ''))

    # Add examples if available
    if 'voorbeelden' in rule:
        base_suggestion += f"\nVoorbeeld: {rule['voorbeelden'][0]}"

    return base_suggestion
```

### 5. MEDIUM: Python Module Execution (Day 3)
**Why fifth**: Complex validations need Python logic that JSON can't express.

**Implementation**:
```python
# In modular_validation_service.py, add after line ~420

async def _execute_python_validator(self, rule_id: str, ctx: EvaluationContext) -> tuple[float, dict]:
    """Execute Python validator module if available."""
    if not self.toetsregel_manager:
        return 1.0, None

    try:
        validator = self.toetsregel_manager.get_validator(rule_id)
        if validator and hasattr(validator, 'validate'):
            result = await validator.validate(
                begrip=ctx.begrip,
                definitie=ctx.cleaned_text,
                context={'ontological_category': ctx.ontologische_categorie}
            )

            if result.get('valid', True):
                return result.get('score', 1.0), None
            else:
                return 0.0, {
                    'code': rule_id,
                    'message': result.get('message', 'Validation failed'),
                    'suggestion': result.get('suggestion', '')
                }
    except Exception as e:
        logger.debug(f"Python validator {rule_id} failed: {e}")
        return 1.0, None  # Pass on error
```

### 6. LOW: Failure Reason Tracking (Day 3-4)
**Why sixth**: Helps with debugging but doesn't impact user experience directly.

**Implementation**:
```python
# In modular_validation_service.py, modify result dict (line ~409)

result: dict[str, Any] = {
    ...
    "detailed_failures": self._format_failures(violations),  # NEW
    "metrics": {  # NEW
        "rules_evaluated": len(self._internal_rules),
        "rules_passed": len(passed_rules),
        "rules_failed": len(violations),
        "evaluation_time_ms": int((time.time() - start_time) * 1000)
    }
}
```

### 7. LOW: Metrics Collection (Day 4)
**Why last**: Nice for monitoring but not user-facing.

**Implementation**: Already included above in metrics field.

## Implementation Timeline

### Day 1: Critical Foundation (4-6 hours)
- [ ] Category scoring aggregation
- [ ] Acceptance gates with thresholds
- [ ] Save requirements check
- [ ] Additional patterns integration (start)

### Day 2: Rule Coverage (4-6 hours)
- [ ] Complete additional patterns
- [ ] Load all 45+ rules
- [ ] Weight calculation refinement
- [ ] Basic suggestion improvements

### Day 3: Advanced Features (4-6 hours)
- [ ] Python module execution
- [ ] Context-aware suggestions
- [ ] Failure tracking
- [ ] Initial metrics

### Day 4: Polish & Testing (3-4 hours)
- [ ] Complete metrics
- [ ] Integration testing
- [ ] Performance optimization
- [ ] Documentation update

## Test Coverage

Each enhancement needs tests:

```python
# tests/services/validation/test_modular_validation_service_enhanced.py

async def test_category_scoring():
    """Test that category scores are properly aggregated."""

async def test_acceptance_gates():
    """Test gate logic blocks unacceptable definitions."""

async def test_additional_patterns():
    """Test patterns from additional_patterns.py are used."""

async def test_all_rules_loaded():
    """Test that all 45+ rules are active."""
```

## Success Criteria

1. **Category Scoring**: All 7 categories have individual scores
2. **Acceptance Gates**: Definitions fail if ESS < 0.6 or CON < 0.5
3. **Pattern Coverage**: Each rule uses both JSON and additional patterns
4. **Rule Coverage**: 45+ rules active (not just 7)
5. **Actionable Feedback**: Each violation has specific suggestion
6. **No Breaking Changes**: Existing orchestrator continues working

## Risk Mitigation

- **No new files**: All changes in existing `modular_validation_service.py`
- **Backward compatible output**: Keep existing fields, add new ones
- **Graceful degradation**: If Python modules fail, fall back to JSON
- **Incremental delivery**: Each day's work is independently valuable

## Conclusion

This plan delivers maximum value with minimum complexity. By enhancing the existing service directly, we avoid architectural debates and deliver user value immediately. The 4-day timeline is realistic, with each day producing tangible improvements that users will notice.

The key insight: We don't need a perfect validator, we need one that catches the important issues and helps users improve their definitions. This plan achieves that goal efficiently.