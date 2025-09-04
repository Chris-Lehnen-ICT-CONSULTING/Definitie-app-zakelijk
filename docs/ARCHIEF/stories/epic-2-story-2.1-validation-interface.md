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

### AC1: Interface Definition Complete (async‑first, expliciete domeinvelden)
- [ ] `src/services/interfaces/validation.py` bestaat met complete interface definitie
- [ ] Interface bevat 3 async methods:
  - `validate_text(begrip: str, text: str, ontologische_categorie: str | None = None, context: ValidationContext | None = None) -> ValidationResult`
  - `validate_definition(definition: Definition, context: ValidationContext | None = None) -> ValidationResult`
  - `batch_validate(items: Iterable[ValidationRequest], max_concurrency: int = 1) -> list[ValidationResult]`
- [ ] Type hints volledig voor alle parameters en return types
- [ ] Interface volgt Python ABC‑pattern (of Protocol indien passend)

### AC2: ValidationResult Contract Compliance (schema‑eerste)
- [ ] `ValidationResult` is contract‑gebonden aan `validation_result.schema.json` (TypedDict/Pydantic of runtime schema‑validatie aan de boundary)
- [ ] Alle schema-verplichte velden aanwezig met correcte types (incl. `version`, `overall_score`, `is_acceptable`, `violations`, `passed_rules`, `detailed_scores`).
- [ ] Policy: `system.correlation_id` is een geldige UUID en wordt door de implementatie gegenereerd indien afwezig in de aangeleverde context.
- [ ] Optionele velden (o.a. `improvement_suggestions`, `system.timings`) worden alleen toegevoegd indien relevant
- [ ] Contracttests valideren responses tegen het JSON Schema

### AC3: Validation Context Support (privacy‑bewust)
- [ ] `ValidationContext` (frozen dataclass) bevat minimaal: `correlation_id: UUID | None`, `profile: str | None`, `locale: str | None`, `trace_parent: str | None`, `feature_flags: Mapping[str, bool]`
- [ ] Geen PII in context (geen user_id/e‑mail). Extra metadata via `feature_flags` of gecontroleerde `metadata: Mapping[str, Any]` indien noodzakelijk
- [ ] Context is optioneel in API; bij ontbreken genereert de implementatie zelf een `correlation_id`

### AC4: Contract & Error Testing Framework
- [ ] Contracttests valideren interface‑responses tegen JSON Schema (happy/edge)
- [ ] Tests verifiëren alle verplichte velden + `violations[*].code` patroon `^[A-Z]{3}-[A-Z]{3}-\d{3}$`
- [ ] Mock implementatie beschikbaar voor downstream (returns schema‑conforme resultaten)
- [ ] Degraded‑pad test: operationele fout resulteert in schema‑conform resultaat met `SYS-...` code en `system.error`

## Technical Tasks

### Core Interface Implementation
- [ ] Create `src/services/interfaces/validation.py`
- [ ] Define `ValidationOrchestratorInterface` abstract base class
- [ ] Signatures met expliciete domeinvelden (zie AC1)
- [ ] `ValidationRequest` (frozen) met `begrip`, `text`, `ontologische_categorie?`, `context?`
- [ ] Uitgebreide docstrings (parameters, returns, errorbeleid)

### Data Structures
- [ ] Create `ValidationContext` (frozen dataclass)
- [ ] Create `ValidationRequest` (frozen dataclass)
- [ ] `ValidationResult` niet als eigen dataclass; koppel aan JSON Schema via TypedDict/Pydantic of boundary‑validatie

### Contract Testing
- [ ] Create `tests/contracts/test_validation_interface.py`
- [ ] JSON Schema validatie van responses (happy/edge/degraded)
- [ ] Reference fixtures voor `ValidationResult` conform schema (incl. echte UUID voor `system.correlation_id`)
- [ ] Mock `ValidationOrchestrator` implementatie

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
result = await orchestrator.validate_text(
    begrip="natuurlijk persoon",
    text="mens van vlees en bloed ...",
    ontologische_categorie="juridisch",
    context=ctx,
)
assert isinstance(result, ValidationResult)
assert result.version == "1.0.0"
assert 0.0 <= result.overall_score <= 1.0
```

### Edge Cases
```python
# Empty text validation
result = await orchestrator.validate_text(begrip="x", text="", context=ctx)
assert result.is_acceptable == False

# Large batch validation
items = [ValidationRequest(begrip="a", text="...", context=ctx) for _ in range(100)]
results = await orchestrator.batch_validate(items, max_concurrency=1)
assert len(results) == 100
```

### Error Handling
```python
# Operational timeout should return degraded result (no exception)
result = await orchestrator.validate_text(begrip="x", text="test", context=ctx)
assert isinstance(result.system.get("correlation_id"), str)
assert result.version == "1.0.0"
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
