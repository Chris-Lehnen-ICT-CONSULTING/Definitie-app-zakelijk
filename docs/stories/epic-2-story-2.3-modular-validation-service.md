# Story 2.3: ModularValidationService Implementation

**Epic**: Epic 2 - ValidationOrchestratorV2 Implementation
**Status**: In Progress
**Priority**: High
**Size**: 5 story points
**Duration**: 2 days
**Owner**: Senior Developer

## User Story

**Als een** architect,
**Wil ik** een modulaire ValidationService die direct de 45+ toetsregels gebruikt,
**Zodat** we een SA-conforme, uitbreidbare en testbare validatie architectuur hebben zonder monolithische wrappers.

## Business Value

- Eliminates monolithic V1 adapter layer voor cleaner architecture
- Enables individual validator module testing en maintenance
- Provides direct access to business rules zonder translation layers
- Creates foundation voor parallel validation processing
- Improves maintainability door single responsibility per module

## Acceptance Criteria

### AC1: ModularValidationService Implementation
- [ ] `src/services/validation/modular_validation_service.py` implements `ValidationServiceInterface`
- [ ] Service directly uses `ToetsregelManager` voor rule loading
- [ ] All 45+ validator modules zijn accessible via service
- [ ] Async interface met sync validator execution (sequential initially)
- [ ] Service produces `ValidationResult` conform existing schema

### AC2: EvaluationContext & Shared Artifacts
- [ ] `EvaluationContext` contains pre-computed shared data (cleaned text, tokens, etc.)
- [ ] Context is computed once en passed to all validators
- [ ] No duplicate text processing across validators
- [ ] Context includes correlation_id voor tracing

### AC3: Configuration & Weights System
- [ ] YAML-based configuration in `src/config/validation_rules.yaml`
- [ ] Per-rule configuration: enabled, weight, threshold, params
- [ ] Aggregation method: gewogen som / som gewichten, afronding 2 decimalen
- [ ] Environment variable overlay: default + optional local overlay via ENV path
- [ ] Configuration validation at startup met fallback to defaults on error
- [ ] Acceptatiekader: `thresholds.overall_accept` (default 0.75) + category minima
- [ ] V1-pariteit: weights/thresholds extracted from existing DefinitionValidator

### AC4: Error Isolation & Telemetry
- [ ] Individual validator failures don't crash validation (exceptions caught per rule)
- [ ] Failed validators marked as "errored" in results, validation continues
- [ ] Validation fails completely only on systemic errors (invalid config, no rules loaded)
- [ ] JSON structured logging: correlation_id, path, latency_ms, score, violations_count
- [ ] Metrics: `validation.rules_evaluated_total`, `validation.errors_total{rule=}`, `validation.latency_seconds`
- [ ] Deterministic results: rules sorted by code, violations normalized (order-insensitive)
- [ ] Fixed precision: scores rounded to 2 decimals

## Technical Tasks

### Core Service Implementation
- [ ] Create `src/services/validation/modular_validation_service.py`
- [ ] Implement `ValidationServiceInterface` async methods
- [ ] Integrate `ToetsregelManager` voor rule loading (sync, wrapped via `asyncio.to_thread`)
- [ ] Create sequential evaluation loop (sorted by rule code for determinism)
- [ ] Implement score aggregation: Σ(weight × score) / Σ(weights)
- [ ] Add result mapping to `ValidationResult` schema
- [ ] Rule-set versioning: add `ruleset_version: "1.0.0"` to output metadata

### Supporting Components
- [ ] Create `src/services/validation/types_internal.py`
  - [ ] Define `EvaluationContext` dataclass with fields:
    - `raw_text: str` - Original input text
    - `cleaned_text: str` - Pre-processed text (via CleaningService)
    - `locale: str | None` - Language context (nl/en)
    - `profile: str | None` - Validation profile
    - `correlation_id: str` - Request tracing ID
    - `tokens: list[str]` - Pre-computed tokenization (if needed)
    - `metadata: dict[str, Any]` - Additional context
  - [ ] Define `RuleResult` internal type
  - [ ] Define aggregation helpers
- [ ] Create `src/services/validation/module_adapter.py`
  - [ ] Wrap sync validators voor async interface
  - [ ] Implement error isolation per validator
  - [ ] Add timeout protection (1s per rule)
- [ ] Create `src/services/validation/config.py`
  - [ ] YAML config loader
  - [ ] Environment variable overlay
  - [ ] Config validation logic
  - [ ] Default configuration factory

### Configuration Files
- [ ] Create `src/config/validation_rules.yaml`
  - [ ] Define weights voor all 45+ rules
  - [ ] Set thresholds per category (ESS, CON, STR, etc.)
  - [ ] Configure aggregation parameters
  - [ ] Document each configuration option
- [ ] Update `.env.example` met configuration examples

### Container Wiring (Direct Cutover)
- [ ] Update `src/services/container.py`
  - [ ] Replace `ValidationServiceAdapterV1toV2` met `ModularValidationService`
  - [ ] Wire `ToetsregelManager` as dependency
  - [ ] Wire `CleaningService` as optional dependency
  - [ ] Remove V1 adapter from DI completely

### Testing Infrastructure
- [ ] Create `tests/fixtures/golden_definitions.yaml`
  - [ ] 15-30 test cases met expected results
  - [ ] Cover happy path, edge cases, errors
  - [ ] Document business rules per case
- [ ] Create `tests/services/test_modular_validation_service.py`
  - [ ] Unit tests voor service methods
  - [ ] Contract tests voor schema compliance
  - [ ] Determinism tests (identical runs = identical results)
  - [ ] Error isolation tests
- [ ] Create `tests/integration/test_validation_v2_flow.py`
  - [ ] End-to-end test met orchestrator
  - [ ] Golden dataset validation
  - [ ] Performance benchmarks

### Documentation
- [ ] Create `docs/validation_rulebook.md`
  - [ ] Document each violation code
  - [ ] Explain weights en thresholds (source: V1 DefinitionValidator)
  - [ ] Provide examples from golden set
  - [ ] Add "Adding a New Validator" section:
    1. Create module in `src/toetsregels/validators/XXX_NN.py`
    2. Add config entry in `validation_rules.yaml`
    3. Define weight, threshold, params
    4. Add golden test case
    5. Run validation checks
- [ ] Create `docs/adr/ADR-007-modular-validation.md`
  - [ ] Document architecture decision
  - [ ] Explain V1 replacement rationale
  - [ ] List consequences en trade-offs
  - [ ] Note rule-set version strategy

## Definition of Done

- [ ] ModularValidationService fully implements ValidationServiceInterface
- [ ] All 45+ validators work via new service
- [ ] Golden tests pass (15+ cases green)
- [ ] Contract tests validate schema compliance
- [ ] Deterministic behavior verified
- [ ] Error isolation works per validator
- [ ] Container uses ModularValidationService exclusively
- [ ] V1 adapter removed from dependency injection
- [ ] Documentation complete (rulebook + ADR)
- [ ] Code review approved by senior developer
- [ ] Performance meets or exceeds V1 baseline

## Test Scenarios

### Golden Test Example
```python
# tests/fixtures/golden_definitions.yaml
metadata:
  ruleset_version: "1.0.0"
  source: "V1 DefinitionValidator baseline"
cases:
  - id: "perfect_definition"
    begrip: "belastingplichtige"
    text: "natuurlijk persoon of rechtspersoon die volgens de belastingwet..."
    expected:
      overall_score: 0.85  # Σ(weight × score) / Σ(weights), rounded to 2 decimals
      is_acceptable: true  # score >= thresholds.overall_accept (0.75)
      violations: []

  - id: "circular_definition"
    begrip: "belasting"
    text: "belasting is een belasting die door de belastingdienst..."
    expected:
      overall_score: 0.30
      is_acceptable: false
      violations: ["CON-01", "ESS-03"]  # Sorted codes for determinism
```

### Contract Compliance Test
```python
async def test_validation_result_schema():
    """Result must comply with ValidationResult schema."""
    service = ModularValidationService(manager, cleaning)

    result = await service.validate_definition(
        begrip="test",
        text="test definitie",
        context={"correlation_id": str(uuid4())}
    )

    assert_matches_schema(result, ValidationResult)
    assert result.version == "1.0.0"
    assert 0.0 <= result.overall_score <= 1.0
```

### Determinism Test
```python
async def test_deterministic_results():
    """Two identical runs produce identical results."""
    service = ModularValidationService(manager, cleaning)

    result1 = await service.validate_definition("begrip", "text")
    result2 = await service.validate_definition("begrip", "text")

    assert result1.overall_score == result2.overall_score
    assert result1.violations == result2.violations
    assert result1.detailed_scores == result2.detailed_scores
```

### Error Isolation Test
```python
async def test_validator_failure_isolation():
    """One validator failure doesn't crash validation."""
    # Mock one validator to throw exception
    mock_validator_to_fail("ESS-01")

    result = await service.validate_definition("test", "text")

    assert result is not None
    assert result.overall_score >= 0.0
    assert "ESS-01" in result.system.get("errored_rules", [])
```

## Dependencies

### Prerequisites
- [x] Story 2.1 completed (ValidationInterface defined)
- [x] Story 2.2 completed (ValidationOrchestratorV2 implemented)
- [x] ToetsregelManager operational met 45+ validators
- [x] CleaningService available voor text preprocessing

### Downstream Impact
- [ ] DefinitionOrchestratorV2 continues using ValidationServiceInterface
- [ ] No breaking changes to external contracts
- [ ] V1 adapter can be archived after validation

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Validator incompatibility | High | Low | Module adapter pattern voor version handling |
| Performance degradation | Medium | Medium | Start sequential, add parallelism later |
| Missing business logic | High | Low | Golden tests validate gegen V1 baseline |
| Config parsing errors | Medium | Low | Validation at startup, fallback defaults |
| Memory usage increase | Low | Low | EvaluationContext limits, text size caps |

## Integration Points

- **ToetsregelManager**: Primary source voor validation rules
- **CleaningService**: Optional text preprocessing
- **ValidationOrchestratorV2**: Consumes this service
- **Container System**: Dependency injection wiring
- **Configuration System**: YAML + ENV variables

## Success Metrics

- [ ] All 45+ validators operational: 100% coverage
- [ ] Golden test compliance: 95%+ accuracy vs V1
- [ ] Performance: Equal or better than V1 baseline
- [ ] Error rate: < 1% validator failures
- [ ] Determinism: 100% identical results for identical input
- [ ] Maintainability: New validator addition < 30 minutes

## Test Implementation Status

✅ **COMPLETED** - All tests implemented (2025-01-09)
- 20 golden test cases in `tests/fixtures/golden_definitions.yaml`
- Full test suite covering all acceptance criteria
- See: `docs/testing/story-2.3-test-implementation.md`

---

**Created**: 2025-01-09
**Story Owner**: Senior Developer
**Technical Reviewer**: Senior Architect
**Stakeholders**: Development Team, QA Engineer
