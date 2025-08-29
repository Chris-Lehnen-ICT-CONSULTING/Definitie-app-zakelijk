# Story 2.1: ValidationOrchestratorInterface Definition

**Epic**: Epic 2 - ValidationOrchestratorV2 Implementation  
**Status**: Ready  
**Priority**: High  
**Size**: 3 story points  
**Duration**: 2 days  
**Owner**: Senior Developer  

## User Story

**Als een** architect,  
**Wil ik** een gedefinieerde ValidationOrchestratorInterface met contract specificatie,  
**Zodat** alle validatie implementaties een consistent contract volgen en toekomstige uitbreidingen mogelijk zijn.

## Business Value

- Establishes clear contract boundaries voor alle validation operations
- Enables multiple ValidationOrchestrator implementations (V2, testing mocks, future variants)
- Provides type safety en IDE autocomplete voor development team
- Creates foundation voor contract testing en validation

## Acceptance Criteria

### AC1: Interface Definition Complete
- [ ] `src/services/interfaces/validation.py` exists met complete interface definitie
- [ ] Interface bevat alle 3 async methods: `validate_text()`, `validate_definition()`, `batch_validate()`
- [ ] Type hints zijn volledig gedefinieerd voor alle parameters en return types
- [ ] Interface follows Python ABC (Abstract Base Class) pattern

### AC2: ValidationResult Contract Compliance
- [ ] ValidationResult dataclass matches JSON Schema exact contract
- [ ] All required fields zijn gedefinieerd met correct types
- [ ] Optional fields hebben proper defaults
- [ ] Dataclass supports JSON serialization/deserialization

### AC3: Validation Context Support
- [ ] ValidationContext dataclass supports correlation_id tracking
- [ ] Context supports profile/rule configuratie per validation request
- [ ] Context allows voor custom metadata passing

### AC4: Contract Testing Framework
- [ ] Contract tests validate interface compliance tegen JSON Schema
- [ ] Tests verificeren all required fields in ValidationResult
- [ ] Tests validate error code format (VAL-XXX-000 pattern)
- [ ] Mock implementatie available voor downstream testing

## Technical Tasks

### Core Interface Implementation
- [ ] Create `src/services/interfaces/validation.py`
- [ ] Define `ValidationOrchestratorInterface` abstract base class
- [ ] Implement `validate_text(text: str, context: ValidationContext) -> ValidationResult`
- [ ] Implement `validate_definition(definition: Definition) -> ValidationResult`  
- [ ] Implement `batch_validate(items: List[Validatable]) -> List[ValidationResult]`
- [ ] Add comprehensive type hints en docstrings

### Data Structures
- [ ] Create `ValidationResult` dataclass in `src/models/validation.py`
- [ ] Create `ValidationContext` dataclass
- [ ] Create `RuleViolation` dataclass voor violation objects
- [ ] Add JSON serialization methods (`to_dict()`, `from_dict()`)
- [ ] Add `__str__` en `__repr__` methods voor debugging

### Contract Testing
- [ ] Create `tests/contracts/test_validation_interface.py`
- [ ] Implement JSON Schema validation tests
- [ ] Create reference ValidationResult fixtures
- [ ] Add contract compliance test suite
- [ ] Create mock ValidationOrchestrator implementatie

### Documentation
- [ ] Add interface documentation in docstrings
- [ ] Create usage examples in interface comments
- [ ] Document error code conventions
- [ ] Add type annotation examples

## Definition of Done

- [ ] Interface is fully defined en type-hinted
- [ ] ValidationResult matches JSON Schema 100%
- [ ] Contract tests pass with 100% coverage
- [ ] Mock implementation available voor testing
- [ ] Code review approved by senior developer
- [ ] Documentation is complete en accurate
- [ ] No breaking changes to existing codebase
- [ ] Interface supports async/await patterns

## Test Scenarios

### Happy Path
```python
# Should successfully validate interface contract
result = await orchestrator.validate_text("sample text", context)
assert isinstance(result, ValidationResult)
assert result.version == "1.0.0"
assert 0.0 <= result.overall_score <= 1.0
```

### Edge Cases
```python
# Empty text validation
result = await orchestrator.validate_text("", context)
assert result.is_acceptable == False

# Large batch validation
items = [create_test_item() for _ in range(100)]
results = await orchestrator.batch_validate(items)
assert len(results) == 100
```

### Error Handling
```python
# Invalid context should raise appropriate error
with pytest.raises(ValidationError):
    await orchestrator.validate_text("test", None)

# Network timeout should return degraded result
result = await orchestrator.validate_text("test", context, timeout=0.001)
assert result.system.error is not None
```

## Dependencies

### Prerequisites
- [ ] JSON Schema voor ValidationResult is finalized
- [ ] Modern validation rules zijn gedefinieerd in `src/validation/`
- [ ] Definition en Validatable models exist

### Downstream Impact
- [ ] DefinitionOrchestratorV2 will depend on this interface
- [ ] Test mocks will implement this interface
- [ ] Container registration will use this interface

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Schema drift tijdens development | High | Medium | Lock schema version, CI validation |
| Interface changes breaking downstream | High | Low | Comprehensive contract tests |
| Type hint conflicts | Low | Medium | Use `typing_extensions` voor compatibility |
| Performance impact van type checking | Low | Low | Profile critical paths |

## Integration Points

- **AIServiceV2**: ValidationOrchestrator will use AsyncGPTClient
- **DefinitionOrchestratorV2**: Will depend on ValidationOrchestrator interface  
- **Container System**: DI registration voor interface implementations
- **Testing Framework**: Mock implementations voor unit tests

## Success Metrics

- [ ] Interface completeness: 100% coverage van validation use cases
- [ ] Contract compliance: 100% JSON Schema adherence  
- [ ] Type safety: Zero MyPy errors in interface usage
- [ ] Developer experience: Positive feedback on interface clarity

---

**Created**: 2025-08-29  
**Story Owner**: Senior Developer  
**Technical Reviewer**: Senior Architect  
**Stakeholders**: Development Team, QA Engineer