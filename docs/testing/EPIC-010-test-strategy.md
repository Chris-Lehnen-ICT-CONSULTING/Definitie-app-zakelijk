---
canonical: true
status: active
owner: quality-assurance
last_verified: 2025-09-08
applies_to: definitie-app@current
epic: EPIC-010
---

# EPIC-010 Context Flow Refactoring - Test Strategy

## Executive Summary

This document outlines the comprehensive test strategy for EPIC-010, covering the critical context flow refactoring that addresses system-breaking bugs preventing legal compliance. The strategy follows TDD principles with tests written BEFORE implementation to guide development.

## Test Scope

### User Stories Covered
- **US-041**: Fix Context Field Mapping to Prompts
- **US-042**: Fix "Anders..." Custom Context Option
- **US-043**: Remove Legacy Context Routes

### Critical Bugs Addressed
- **CFR-BUG-001**: Context fields not passed to prompts
- **CFR-BUG-002**: "Anders..." option crashes application
- **CFR-BUG-003**: GenerationResult import error blocking tests

## Test Suite Structure

### 1. Unit Tests (250+ test cases)
Located in `/tests/unit/`:

#### US-041 Context Field Mapping
- **File**: `test_us041_context_field_mapping.py`
- **Classes**: 7 test classes
- **Coverage**: Context field validation, prompt integration, justice domain scenarios
- **Expected Outcome**: All tests FAIL before fix, PASS after implementation

#### US-042 Anders Option Fix
- **File**: `test_us042_anders_option_fix.py`
- **Classes**: 8 test classes
- **Coverage**: Anders functionality, special characters, UI behavior, state persistence
- **Expected Outcome**: Validation errors before fix, smooth operation after

#### US-043 Legacy Route Removal
- **File**: `test_us043_remove_legacy_routes.py`
- **Classes**: 10 test classes
- **Coverage**: Single flow path, performance improvements, memory efficiency
- **Expected Outcome**: Multiple paths detected before, single path after

#### Edge Cases & Security
- **File**: `test_anders_edge_cases.py`
- **Classes**: 10 test classes
- **Coverage**: XSS/SQL injection, extreme inputs, unicode, concurrency
- **Expected Outcome**: Vulnerabilities blocked, all edge cases handled

#### Feature Flags
- **File**: `test_feature_flags_context_flow.py`
- **Classes**: 9 test classes
- **Coverage**: A/B testing, rollout percentages, fallback mechanisms
- **Expected Outcome**: Gradual rollout capability verified

### 2. Integration Tests
Located in `/tests/integration/`:

#### Context Flow Integration
- **File**: `test_context_flow_epic_cfr.py`
- **Classes**: 5 test classes
- **Coverage**: End-to-end flow, all user stories integrated, audit trail
- **Expected Outcome**: Complete context propagation UI → AI

### 3. Performance Tests
Located in `/tests/performance/`:

#### Performance Benchmarks
- **File**: `test_context_flow_performance.py`
- **Classes**: 8 test classes
- **Metrics**:
  - Latency: p50 <50ms, p95 <100ms, p99 <200ms
  - Throughput: >100 requests/second
  - Memory: <50MB overhead
  - CPU: <80% utilization
- **Expected Outcome**: >20% performance improvement

### 4. Compliance Tests
Located in `/tests/compliance/`:

#### ASTRA/NORA Compliance
- **File**: `test_astra_nora_context_compliance.py`
- **Classes**: 9 test classes
- **Coverage**: Audit trails, privacy, interoperability, accessibility
- **Expected Outcome**: Full compliance with justice sector standards

### 5. UI Component Tests
Located in `/tests/ui/`:

#### Context Selector Tests
- **File**: `test_context_selector_anders_fix.py`
- **Coverage**: Streamlit widget behavior, custom text input, validation
- **Expected Outcome**: No UI crashes, smooth user experience

## Test Execution Phases

### Phase 0: Pre-Implementation (TDD)
**Duration**: 2-4 hours
**Purpose**: Establish test baseline BEFORE any fixes

```bash
# Verify all tests can be collected (fix CFR-BUG-003 first)
pytest --co -q

# Run all tests to document current failures
pytest tests/unit/test_us04* -v --tb=short > baseline_failures.txt

# Document specific error patterns
pytest tests/unit/test_us041_context_field_mapping.py::test_context_propagation -v
```

### Phase 1: Unit Test Development
**Duration**: 8 hours
**Purpose**: Write comprehensive unit tests for each user story

```bash
# US-041: Context field mapping tests
pytest tests/unit/test_us041_context_field_mapping.py -v

# US-042: Anders option tests
pytest tests/unit/test_us042_anders_option_fix.py -v

# US-043: Legacy route removal tests
pytest tests/unit/test_us043_remove_legacy_routes.py -v
```

### Phase 2: Implementation Guidance
**Duration**: Ongoing during development
**Purpose**: Use failing tests to guide implementation

```bash
# Run specific failing test to understand requirements
pytest tests/unit/test_us041_context_field_mapping.py::test_juridische_context_mapping -vv

# Watch mode for rapid feedback during coding
pytest-watch tests/unit/ -n auto

# Coverage tracking to ensure completeness
pytest tests/unit/ --cov=src.services.prompts --cov-report=term-missing
```

### Phase 3: Integration Validation
**Duration**: 4 hours
**Purpose**: Verify components work together

```bash
# Full context flow integration
pytest tests/integration/test_context_flow_epic_cfr.py -v

# UI component integration
pytest tests/ui/test_context_selector_anders_fix.py -v

# End-to-end scenarios
pytest tests/integration/ -v --tb=short
```

### Phase 4: Performance Validation
**Duration**: 4 hours
**Purpose**: Ensure performance targets met

```bash
# Performance benchmarks
pytest tests/performance/test_context_flow_performance.py -v --benchmark

# Memory profiling
pytest tests/performance/ --memprof

# Load testing
pytest tests/performance/ -k "concurrent" -v
```

### Phase 5: Compliance Verification
**Duration**: 4 hours
**Purpose**: Validate ASTRA/NORA compliance

```bash
# Compliance tests
pytest tests/compliance/test_astra_nora_context_compliance.py -v

# Audit trail verification
pytest tests/integration/ -k "audit" -v

# Security validation
pytest tests/unit/test_anders_edge_cases.py -k "security" -v
```

## Test Data Requirements

### Context Test Data
```python
TEST_CONTEXTS = {
    "juridische_context": ["Strafrecht", "Bestuursrecht", "Anders: Custom Legal"],
    "wettelijke_basis": ["Wetboek van Strafrecht", "AWB", "Anders: Special Law"],
    "organisatorische_context": ["OM", "DJI", "Rechtspraak", "Anders: CJIB"]
}
```

### Edge Case Data
- Empty contexts: `[]`
- Single values: `["OM"]`
- Maximum values: 10+ selections
- Special characters: `["Anders: <script>alert('xss')</script>"]`
- Unicode: `["Anders: 法律 🚨 context"]`
- Extreme length: 10,000+ character strings

## Success Metrics

### Coverage Targets
- **Unit Tests**: >95% coverage for new code
- **Integration**: >80% coverage for context flow
- **Edge Cases**: 100% coverage for Anders option
- **Performance**: All SLA metrics tested

### Quality Gates
1. **Pre-commit**: All unit tests must pass
2. **PR Merge**: Integration tests must pass
3. **Deployment**: Performance benchmarks met
4. **Production**: Compliance tests verified

### Test Pass Criteria
- **Functional**: 100% of acceptance criteria met
- **Performance**: >20% improvement over baseline
- **Security**: Zero vulnerabilities in edge cases
- **Compliance**: Full ASTRA/NORA adherence

## Risk Mitigation

### Test Environment Risks
- **Mock Complexity**: Extensive Streamlit mocking required
  - *Mitigation*: Comprehensive fixture library
- **Test Flakiness**: UI tests may be unstable
  - *Mitigation*: Retry mechanisms, stable selectors

### Coverage Risks
- **Hidden Paths**: Legacy code may have untested paths
  - *Mitigation*: Code coverage analysis, mutation testing
- **Integration Gaps**: Component interactions missed
  - *Mitigation*: Contract testing, E2E scenarios

## Test Maintenance

### Daily Activities
- Monitor test execution in CI/CD
- Update tests for new requirements
- Review and fix flaky tests

### Sprint Activities
- Update test documentation
- Performance baseline reviews
- Coverage analysis and improvement

### Release Activities
- Full regression test suite execution
- Compliance verification
- Performance benchmarking

## Test Automation

### CI/CD Integration
```yaml
# GitHub Actions workflow
name: EPIC-010 Test Suite
on: [push, pull_request]

jobs:
  test:
    strategy:
      matrix:
        test-type: [unit, integration, performance, compliance]
    steps:
      - uses: actions/checkout@v2
      - name: Run ${{ matrix.test-type }} tests
        run: |
          pytest tests/${{ matrix.test-type }}/ -v --tb=short
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

### Test Reporting
- **Coverage Reports**: Generated for each PR
- **Performance Trends**: Tracked over time
- **Compliance Dashboard**: Updated daily
- **Test Results**: Published to team dashboard

## Related Documentation

### Primary Documents
- **Epic**: [EPIC-010: Context Flow Refactoring](../backlog/epics/EPIC-010-context-flow-refactoring.md)
- **Implementation Plan**: [EPIC-010 Implementation Plan](../implementation/EPIC-010-implementation-plan.md)
- **Test Suite Summary**: [250+ Test Cases](./EPIC_010_TEST_SUITE_SUMMARY.md)

### User Stories
- **US-041**: [Fix Context Field Mapping](../backlog/stories/US-041.md)
- **US-042**: [Fix "Anders..." Custom Context](../backlog/stories/US-042.md)
- **US-043**: [Remove Legacy Context Routes](../backlog/stories/US-043.md)

### Bug Reports
- **CFR-BUG-003**: [GenerationResult Import Error](../backlog/bugs/CFR-BUG-003-generation-result-import.md)

### Test Files Created for This Strategy
#### Unit Tests
- [`/tests/unit/test_us041_context_field_mapping.py`](../../tests/unit/test_us041_context_field_mapping.py) - Context field mapping (7 test classes)
- [`/tests/unit/test_us042_anders_option_fix.py`](../../tests/unit/test_us042_anders_option_fix.py) - Anders option functionality (8 test classes)
- [`/tests/unit/test_us043_remove_legacy_routes.py`](../../tests/unit/test_us043_remove_legacy_routes.py) - Legacy route removal (10 test classes)
- [`/tests/unit/test_anders_edge_cases.py`](../../tests/unit/test_anders_edge_cases.py) - Edge case coverage (10 test classes)
- [`/tests/unit/test_feature_flags_context_flow.py`](../../tests/unit/test_feature_flags_context_flow.py) - Feature flag testing (9 test classes)
- [`/tests/unit/test_context_payload_schema.py`](../../tests/unit/test_context_payload_schema.py) - Schema validation (10 test classes)

#### Integration Tests
- [`/tests/integration/test_context_flow_epic_cfr.py`](../../tests/integration/test_context_flow_epic_cfr.py) - End-to-end context flow (5 test classes)

#### Performance Tests
- [`/tests/performance/test_context_flow_performance.py`](../../tests/performance/test_context_flow_performance.py) - Performance benchmarks (8 test classes)

#### Compliance Tests
- [`/tests/compliance/test_astra_nora_context_compliance.py`](../../tests/compliance/test_astra_nora_context_compliance.py) - ASTRA/NORA validation (8 test classes)

## Conclusion

This test strategy ensures comprehensive validation of the EPIC-010 context flow refactoring through:
- **TDD Approach**: Tests written before implementation
- **Complete Coverage**: 250+ test cases across all scenarios
- **Performance Focus**: Measurable improvement targets
- **Compliance Validation**: ASTRA/NORA requirements verified
- **Risk Mitigation**: Edge cases and security thoroughly tested

The strategy provides clear guidance for developers, with specific test files and execution commands for each phase of implementation.
