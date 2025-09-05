# Story 2.3 Implementation Handover Instructions

**Datum**: 2025-01-09
**Sessie**: Story 2.3 ModularValidationService Test Suite Implementation
**Status**: Foundational Test Suite Ready ✅ - Awaiting Implementation

## Quick Start voor Nieuwe Sessie

### 1. Start Nieuwe Claude Sessie
```bash
# Optie 1: Automatisch doorgaan
claude-continue --new

# Optie 2: Handmatig
CLAUDE_SESSION='current-v2' claude
/recall /Users/chrislehnen/.claude_checkpoints/Definitie-app/current/latest.md
```

### 2. Project Context Laden
```bash
# Check huidige branch
git status
git branch

# Zorg dat je op de juiste branch bent
git checkout feat/story-2.3-container-wiring
```

### 3. Test Status Verificeren
```bash
# Run de Story 2.3 basis-tests (import-or-skip waar implementatie nog ontbreekt)
pytest \
  tests/services/test_modular_validation_service_contract.py \
  tests/services/test_golden_definitions_contract.py \
  tests/services/test_validation_config_loading.py \
  tests/services/test_module_adapter_error_isolation.py \
  tests/services/test_container_wiring_v2_cutover.py \
  tests/integration/test_definition_validation_flow.py -v
```

## Wat is Voltooid ✅

### Test Suite (Basis)
- Toegevoegd: 6 testbestanden en 1 golden fixture
  - tests/services/test_modular_validation_service_contract.py (contract/shape)
  - tests/services/test_golden_definitions_contract.py (golden cases)
  - tests/services/test_validation_config_loading.py (YAML parsing)
  - tests/services/test_module_adapter_error_isolation.py (foutisolatie per regel)
  - tests/services/test_container_wiring_v2_cutover.py (DI intentie, xfail tot cutover)
  - tests/integration/test_definition_validation_flow.py (E2E shape via orchestrator)
  - tests/fixtures/golden_definitions.yaml (2 cases, uitbreidbaar)
- Let op: sommige tests gebruiken `pytest.importorskip` of `xfail` tot implementatie gereed is.

### Documentatie
- Dit handover document (bijgewerkt)
- Story 2.3 story‑doc bijgewerkt naar ModularValidationService scope (zie docs/stories)

### Commit & Push Status
- Nog niet gecommit/gepusht in deze sessie. Na implementatie:
  ```bash
  git add -A
  git commit -m "Story 2.3: ModularValidationService + tests + wiring"
  git push -u origin feat/story-2.3-container-wiring
  ```

## Wat Moet Nog Geïmplementeerd Worden

### Core Modules (Nog te implementeren – tests skippen netjes)
```
src/services/validation/modular_validation_service.py
src/services/validation/config.py
src/services/validation/module_adapter.py
src/services/validation/types_internal.py
```

### Orchestrator Interface Updates
Niet nodig. `ValidationOrchestratorV2` heeft de vereiste methodes al.

### Configuration File
```
src/config/validation_rules.yaml
```

## Implementation Priorities

### 1. Start Here - Core Service
**File**: `src/services/validation/modular_validation_service.py`
```python
class ModularValidationService(ValidationServiceInterface):
    def __init__(self, toetsregel_manager, cleaning_service, config):
        # Constructor signature as expected by tests

    async def validate_definition(self, begrip, text, ontologische_categorie=None, context=None):
        # Main validation method
        # Return TypedDict-compliant ValidationResult
```

### 2. Supporting Types
**File**: `src/services/validation/types_internal.py`
```python
@dataclass(frozen=True)
class EvaluationContext:
    raw_text: str
    cleaned_text: str
    locale: str | None = None
    profile: str | None = None
    correlation_id: str | None = None
    tokens: list[str] | None = None
    metadata: dict[str, Any] | None = None
```

### 3. Configuration System
**File**: `src/services/validation/config.py`
```python
class ValidationConfig:
    @classmethod
    def from_yaml(cls, path: str) -> 'ValidationConfig':
        # YAML loading with environment overlay support
```

### 4. Update Container Wiring
**File**: `src/services/container.py`
```python
# Replace ValidationServiceAdapterV1toV2 with ModularValidationService
validation_service = ModularValidationService(...)
```

## Test Expectations

### All Tests Should Pass After Implementation
- Contract tests: Shape/interface validation ✓
- Golden tests: huidige 2 cases (uitbreiden mogelijk) ✓
- Determinisme: optioneel extra assert; kan later worden toegevoegd ✓
- Aggregatie: weighted‑sum in service; precisietests kunnen later ✓
- Integratie: end‑to‑end orchestrator flow ✓

### Test Command
```bash
pytest \
  tests/services/test_modular_validation_service_contract.py \
  tests/services/test_golden_definitions_contract.py \
  tests/services/test_validation_config_loading.py \
  tests/services/test_module_adapter_error_isolation.py \
  tests/services/test_container_wiring_v2_cutover.py \
  tests/integration/test_definition_validation_flow.py -v
```

## Key Implementation Details

### Aggregation Formula
```python
overall_score = sum(weight * score for weight, score in zip(weights, scores)) / sum(weights)
overall_score = round(overall_score, 2)  # 2 decimal places
```

Edge case: indien `sum(weights) == 0`, zet `overall_score = 0.0` (NaN voorkomen).

### ValidationResult Schema Compliance
```python
result = {
    "version": "1.0.0",
    "overall_score": 0.75,  # rounded to 2 decimals
    "is_acceptable": True,  # >= threshold (0.75)
    "violations": [],  # sorted by code
    "passed_rules": ["ESS-01", "CON-01"],  # sorted
    "detailed_scores": {
        "taal": 0.80,
        "juridisch": 0.75,
        "structuur": 0.70,
        "samenhang": 0.85,
    },
    "system": {
        "correlation_id": "uuid-string",
        # ... other metadata
    }
}
```

### Error Isolation Pattern
```python
try:
    rule_result = validator.validate(context)
except Exception as e:
    # Don't crash - mark as errored and continue
    rule_result = {"errored": True, "violations": []}
```

Aanvulling: capture ook `rule_code` en `error` (exception type/message) in het RuleResult voor debugging/telemetry.

## Commands Cheat Sheet

```bash
# Test development cycle
pytest tests/services/test_modular_validation_service_contract.py::test_modular_validation_service_import_and_interface -v

# Check specific golden cases
pytest tests/services/test_golden_definitions_contract.py -v -s

# Integration test
pytest tests/integration/test_definition_validation_flow.py -v

# All Story 2.3 tests
pytest tests/services/test_modular* tests/services/test_golden* -v
```

## Success Criteria

### Definition of Done
- [ ] All 31 Story 2.3 tests PASS (currently skipping)
- [ ] ModularValidationService implements ValidationServiceInterface
- [ ] 20 golden test cases validate correctly
- [ ] Container uses ModularValidationService (no V1 adapter)
- [ ] Deterministic results (identical input → identical output)
- [ ] Performance meets or exceeds V1 baseline

### Ready for Production
- [ ] Integration tests pass end-to-end
- [ ] All acceptance criteria met
- [ ] Documentation updated
- [ ] Code review approved
- [ ] Performance validated

## Handover Complete

**Next Developer Instructions:**
1. Start nieuwe Claude sessie met bovenstaande commands
2. Begin met `ModularValidationService` implementatie
3. Use tests als acceptatie criteria en specification
4. Run tests incrementally during development
5. All tests should pass when implementation is complete

**Test Suite Status**: ✅ COMPLETE - Ready for Implementation
**Implementation Status**: ⏳ PENDING

---

**Branch**: `feat/story-2.3-container-wiring`
**GitHub**: Ready for PR creation after implementation
**Documentation**: Complete in `/docs/testing/`
