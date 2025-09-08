---
canonical: true
status: active
owner: development
last_verified: 2025-09-08
applies_to: definitie-app@current
epic: EPIC-010
sprint: sprint-36
priority: KRITIEK
---

# EPIC-010: Context Flow Refactoring - Implementation Plan

## Executive Summary

This document provides the detailed 9-phase implementation plan for fixing KRITIEK context flow issues that are blocking legal compliance and causing system failures. The plan addresses both immediate bugs and long-term architectural improvements.

## Current Status

| Component | Status | Blocking Issue |
|-----------|--------|----------------|
| **Test Suite** | ❌ BLOCKED | CFR-BUG-003: GenerationResult import error (36 tests) |
| **Context Flow** | ❌ BROKEN | Context fields not passed to prompts |
| **Custom Context** | ❌ CRASHES | "Anders..." option causes validation errors |
| **Legacy Routes** | ⚠️ MIXED | Multiple inconsistent data paths |
| **ASTRA Compliance** | ❌ FAILED | No context traceability |

## Implementation Phases

### FASE 0: Pre-flight Analysis & Emergency Fix (2-4 hours)
**Status:** IN PROGRESS
**Bug:** CFR-BUG-003

#### Context Schema Analysis
```python
# Expected schema for context fields
context_schema = {
    "juridische_context": List[str],      # ["Strafrecht", "Bestuursrecht"]
    "wettelijke_basis": List[str],        # ["Wetboek van Strafrecht", "AWB"]
    "organisatorische_context": List[str], # ["OM", "DJI", "Anders: custom"]
    "domein": str                          # "justice" (deprecated, remove in US-043)
}
```

#### Immediate Actions
1. **Apply GenerationResult shim fix**:
   ```python
   # In src/models/generation_result.py
   GenerationResult = LegacyGenerationResult  # Temporary alias
   ```

2. **Verify test collection**:
   ```bash
   pytest --co -q  # Should collect all 36 tests
   pytest -x       # Find first actual failure
   ```

3. **Document test baseline**:
   - Record which tests pass/fail BEFORE changes
   - Create test recovery metrics

### FASE 1: GenerationResult Shim & Test Recovery (4 hours)
**Status:** PENDING
**Story:** Pre-US-041

#### Objectives
- Restore test suite functionality
- Establish baseline test metrics
- Unblock CI/CD pipeline

#### Implementation
1. Apply shim fix in `src/models/generation_result.py`
2. Run full test suite and categorize failures
3. Create test recovery report
4. Update CI/CD configuration if needed

#### Success Criteria
- [ ] All 36 tests can be collected
- [ ] No ImportError failures
- [ ] Test failures documented and categorized

#### Test Files
- Run existing integration test: `tests/integration/test_context_flow_epic_cfr.py`
- Verify test collection works for all unit tests

### FASE 2: Test Coverage Restoration (8 hours)
**Status:** PENDING
**Story:** Test preparation for US-041

#### Objectives
- Fix critical test failures
- Establish >60% test coverage
- Create context flow test suite

#### Test Categories to Fix
1. **Unit Tests**: Mock context properly
2. **Integration Tests**: Test context propagation
3. **E2E Tests**: Full context flow validation

#### New Test Cases Required
```python
def test_context_field_mapping():
    """Verify context fields reach prompt"""
    
def test_anders_option_handling():
    """Test custom context without crashes"""
    
def test_context_type_validation():
    """Ensure all contexts are List[str]"""
```

#### Test Files to Execute
- **Unit Tests**: 
  - `tests/unit/test_us041_context_field_mapping.py`
  - `tests/unit/test_us042_anders_option_fix.py`
  - `tests/unit/test_us043_remove_legacy_routes.py`
- **Integration**: `tests/integration/test_context_flow_epic_cfr.py`
- **Performance**: `tests/performance/test_context_flow_performance.py`

### FASE 3: Fix Context Field Mapping (US-041) (8 hours)
**Status:** PENDING
**Story:** US-041
**Priority:** KRITIEK

#### Problem
Context fields collected in UI but not passed to AI prompts.

#### Fix Locations
1. **`src/services/prompts/prompt_service_v2.py`** (lines 158-176):
   ```python
   def _convert_request_to_context(self, request):
       # Map UI context fields to prompt context
       base_context["juridische_context"] = request.juridische_context
       base_context["wettelijke_basis"] = request.wettelijke_basis
       base_context["organisatorische_context"] = request.organisatorische_context
   ```

2. **`src/ui/tabbed_interface.py`**:
   - Ensure context collection preserves List[str] types
   - Pass context through to generation request

3. **`src/services/definition_generator_context.py`**:
   - Validate context presence in generation flow

#### Validation Gates
- [ ] Context visible in debug prompts
- [ ] All three context types properly mapped
- [ ] Context preserved through full flow

#### Test Files for US-041
- **Primary Test**: `tests/unit/test_us041_context_field_mapping.py`
  - Tests all context field mapping scenarios
  - Validates prompt inclusion
  - Checks justice domain specifics
- **Edge Cases**: `tests/unit/test_anders_edge_cases.py`
- **Integration**: `tests/integration/test_context_flow_epic_cfr.py`

#### Test Execution
```bash
# Run US-041 specific tests
pytest tests/unit/test_us041_context_field_mapping.py -v

# Verify context propagation
pytest tests/integration/test_context_flow_epic_cfr.py::TestContextFlowIntegration -v
```

### FASE 4: Fix "Anders..." Custom Context (US-042) (5 hours)
**Status:** PENDING
**Story:** US-042
**Priority:** KRITIEK

#### Problem
"Anders..." selection causes: "The default value 'test' is not part of the options"

#### Root Cause
Multiselect widget crashes when final list differs from initial options.

#### Fix Implementation
```python
# src/ui/components/context_selector.py (lines 137-183)
def handle_anders_option(context_type, options, selected):
    if "Anders..." in selected:
        # Show text input for custom value
        custom_value = st.text_input(f"Custom {context_type}")
        if custom_value:
            # Add with "Anders: " prefix
            selected.remove("Anders...")
            selected.append(f"Anders: {custom_value}")
    return selected
```

#### Test Cases
- [ ] Select "Anders..." alone
- [ ] Mix "Anders..." with predefined options
- [ ] Multiple "Anders..." across different contexts
- [ ] Special characters in custom text

#### Test Files for US-042
- **Primary Test**: `tests/unit/test_us042_anders_option_fix.py`
  - Complete Anders option coverage
  - UI behavior validation
  - State persistence tests
- **UI Component Test**: `tests/ui/test_context_selector_anders_fix.py`
- **Edge Cases**: `tests/unit/test_anders_edge_cases.py`
  - XSS/SQL injection prevention
  - Unicode handling
  - Extreme length inputs

#### Test Execution
```bash
# Run US-042 specific tests
pytest tests/unit/test_us042_anders_option_fix.py -v

# Test UI components
pytest tests/ui/test_context_selector_anders_fix.py -v

# Stress test edge cases
pytest tests/unit/test_anders_edge_cases.py -v
```

### FASE 5: Remove Legacy Context Routes (US-043) (8 hours)
**Status:** PENDING
**Story:** US-043
**Priority:** HOOG
**Dependencies:** US-041, US-042

#### Legacy Routes to Remove
1. **Direct `context` field (string)**:
   - Location: `src/models/generation_request.py`
   - Action: Deprecate and remove

2. **Separate `domein` field**:
   - Location: Multiple files
   - Action: Consolidate into context lists

3. **V1 orchestrator context**:
   - Location: `src/orchestration/orchestrator.py`
   - Action: Remove V1 code paths

4. **Session state context storage**:
   - Location: `src/ui/state_manager.py`
   - Action: Refactor to use proper types

5. **Multiple context_dict creation**:
   - Locations: Search with `grep -r "context_dict"`
   - Action: Consolidate to single source

#### Migration Strategy
- Use feature flags for gradual rollout
- Maintain backward compatibility temporarily
- Log deprecation warnings

#### Test Files for US-043
- **Primary Test**: `tests/unit/test_us043_remove_legacy_routes.py`
  - Validates single context flow path
  - Performance improvement verification (>20% target)
  - Memory efficiency checks
- **Feature Flags**: `tests/unit/test_feature_flags_context_flow.py`
- **Performance**: `tests/performance/test_context_flow_performance.py`

#### Test Execution
```bash
# Run US-043 specific tests
pytest tests/unit/test_us043_remove_legacy_routes.py -v

# Verify performance improvements
pytest tests/performance/test_context_flow_performance.py -v --benchmark

# Test feature flag rollout
pytest tests/unit/test_feature_flags_context_flow.py -v
```

### FASE 6: Feature Flags & Monitoring (4 hours)
**Status:** PENDING
**Story:** Infrastructure for safe rollout

#### Feature Flag Implementation
```python
# config/feature_flags.yaml
context_flow_refactor:
  enabled: true
  rollout_percentage: 10
  audit_enabled: true
  fallback_to_legacy: true
```

#### Monitoring Points
1. Context field population rates
2. "Anders..." usage frequency
3. Error rates per context type
4. Performance impact metrics

#### Test Files for Monitoring
- **Feature Flags**: `tests/unit/test_feature_flags_context_flow.py`
  - A/B testing scenarios
  - Percentage-based rollouts
  - Fallback mechanisms
- **Performance Monitoring**: `tests/performance/test_context_flow_performance.py`

#### Test Execution
```bash
# Test feature flag configurations
pytest tests/unit/test_feature_flags_context_flow.py -v

# Monitor performance under flags
pytest tests/performance/test_context_flow_performance.py::test_with_feature_flags -v
```

### FASE 7: Grep-Gate Validation (4 hours)
**Status:** PENDING
**Story:** Automated validation gates

#### Validation Commands
```bash
# No direct string context remains
grep -r "context.*:.*str" src/ --include="*.py"

# All context fields are lists
grep -r "juridische_context\|wettelijke_basis\|organisatorische_context" src/

# No legacy imports
grep -r "from orchestration import orchestrator" tests/

# GenerationResult properly used
grep -r "GenerationResult" src/ tests/
```

#### Success Criteria
- [ ] Zero string context fields
- [ ] All contexts validated as List[str]
- [ ] No legacy orchestrator imports
- [ ] Consistent GenerationResult usage

### FASE 8: Audit Trail & ASTRA Compliance (8 hours)
**Status:** PENDING
**Story:** US-045 (follow-up)

#### Audit Implementation
```python
# src/services/audit/context_auditor.py
class ContextAuditor:
    def log_context_decision(self, request_id, context_data):
        """Log context usage for ASTRA compliance"""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "juridische_context": context_data.get("juridische_context", []),
            "wettelijke_basis": context_data.get("wettelijke_basis", []),
            "organisatorische_context": context_data.get("organisatorische_context", []),
            "authoritative_sources": self._get_sources(context_data),
            "retention_until": self._calculate_retention_date()  # 7 years
        }
        self._write_immutable_log(audit_entry)
```

#### Compliance Checklist
- [ ] Full context attribution in logs
- [ ] Immutable audit trail
- [ ] 7-year retention configured
- [ ] Authoritative source linking
- [ ] Privacy impact assessed

#### Test Files for Compliance
- **ASTRA/NORA Compliance**: `tests/compliance/test_astra_nora_context_compliance.py`
  - Audit trail requirements
  - Privacy and data protection
  - Interoperability standards
  - Justice domain specifics

#### Test Execution
```bash
# Run compliance tests
pytest tests/compliance/test_astra_nora_context_compliance.py -v

# Verify audit logging
pytest tests/integration/test_context_flow_epic_cfr.py::test_audit_trail -v
```

### FASE 9: Production Rollout & Verification (8 hours)
**Status:** PENDING
**Story:** Final deployment

#### Rollout Steps
1. **Deploy with 10% feature flag**
2. **Monitor for 24 hours**
3. **Increase to 50% if stable**
4. **Full rollout after 48 hours**
5. **Remove legacy code after 1 week**

#### Production Verification
- [ ] Context visible in all definitions
- [ ] Zero context-related errors
- [ ] ASTRA compliance validated
- [ ] Performance within SLAs
- [ ] User satisfaction >90%

## Risk Mitigation

| Risk | Impact | Mitigation | Owner |
|------|--------|------------|-------|
| Test suite remains broken | KRITIEK | Immediate shim fix in FASE 0 | Dev Team |
| Context loss during migration | HOOG | Feature flags with fallback | Architecture |
| Performance degradation | GEMIDDELD | Performance gates in each phase | DevOps |
| User confusion | GEMIDDELD | Clear communication plan | Product |
| Compliance failure | KRITIEK | Early ASTRA validation | Compliance |

## Success Metrics

### Phase Metrics
- **FASE 0-1**: Test suite restored (36 tests collectible)
- **FASE 2**: >60% test coverage achieved
- **FASE 3**: 100% context field mapping verified
- **FASE 4**: Zero "Anders..." crashes
- **FASE 5**: All legacy routes removed
- **FASE 6-7**: Monitoring and validation gates active
- **FASE 8**: ASTRA compliance achieved
- **FASE 9**: Production deployment successful

### Overall Success Criteria
- [ ] **Context Propagation**: 100% of UI context reaches prompts
- [ ] **Error Rate**: Zero context-related errors in production
- [ ] **Test Coverage**: >80% for context flow code
- [ ] **Performance**: <200ms additional latency
- [ ] **Compliance**: Full ASTRA/NORA compliance
- [ ] **User Satisfaction**: >90% satisfaction score

## Timeline

| Phase | Duration | Dependencies | Target Date |
|-------|----------|--------------|-------------|
| FASE 0 | 2-4 hours | None | 08-09-2025 |
| FASE 1 | 4 hours | FASE 0 | 08-09-2025 |
| FASE 2 | 8 hours | FASE 1 | 09-09-2025 |
| FASE 3 | 8 hours | FASE 2 | 09-09-2025 |
| FASE 4 | 5 hours | FASE 2 | 10-09-2025 |
| FASE 5 | 8 hours | FASE 3, 4 | 10-09-2025 |
| FASE 6 | 4 hours | FASE 5 | 11-09-2025 |
| FASE 7 | 4 hours | FASE 6 | 11-09-2025 |
| FASE 8 | 8 hours | FASE 7 | 12-09-2025 |
| FASE 9 | 8 hours | FASE 8 | 12-09-2025 |

**Total Duration**: ~59 hours (7-8 working days)
**Target Completion**: End of Sprint 36 (12-09-2025)

## Related Documents

### Epic & Stories
- **Epic**: [EPIC-010: Context Flow Refactoring](../backlog/epics/EPIC-010-context-flow-refactoring.md)
- **User Stories**:
  - [US-041: Fix Context Field Mapping](../backlog/stories/US-041.md)
  - [US-042: Fix "Anders..." Custom Context](../backlog/stories/US-042.md)
  - [US-043: Remove Legacy Context Routes](../backlog/stories/US-043.md)

### Bug Reports
- **CFR-BUG-003**: [GenerationResult Import Error](../backlog/bugs/CFR-BUG-003-generation-result-import.md)

### Test Documentation
- **Test Strategy**: [EPIC-010 Test Strategy](../testing/EPIC-010-test-strategy.md)
- **Test Suite Summary**: [250+ Test Cases](../../tests/EPIC_010_TEST_SUITE_SUMMARY.md)

### Test Files Referenced in This Plan
- **Unit Tests**:
  - [`test_us041_context_field_mapping.py`](../../tests/unit/test_us041_context_field_mapping.py) - US-041 context mapping
  - [`test_us042_anders_option_fix.py`](../../tests/unit/test_us042_anders_option_fix.py) - US-042 Anders option
  - [`test_us043_remove_legacy_routes.py`](../../tests/unit/test_us043_remove_legacy_routes.py) - US-043 legacy removal
  - [`test_anders_edge_cases.py`](../../tests/unit/test_anders_edge_cases.py) - Edge case coverage
  - [`test_feature_flags_context_flow.py`](../../tests/unit/test_feature_flags_context_flow.py) - Feature flags
- **Integration Tests**:
  - [`test_context_flow_epic_cfr.py`](../../tests/integration/test_context_flow_epic_cfr.py) - End-to-end flow
- **Performance Tests**:
  - [`test_context_flow_performance.py`](../../tests/performance/test_context_flow_performance.py) - Performance metrics

### Architecture
- **Technical Architecture**: [Technical Architecture](../architectuur/TECHNICAL_ARCHITECTURE.md)

## Wijzigingslog

| Datum | Versie | Wijzigingen |
|-------|--------|-------------|
| 08-09-2025 | 1.0 | Initial implementation plan created |

---

*This implementation plan is a living document and will be updated as work progresses through each phase.*