# Test Suite Recovery Solution Plan

**Status**: 🔴 ACTIEF
**Datum**: 2025-09-19
**Scope**: Test suite reparatie en architectuur verbetering
**Impact**: 31 gefaalde tests, architectuur inconsistenties

## Executive Summary

Dit document beschrijft een incrementele oplossing voor de test suite problemen in de DefinitieAgent applicatie. De hoofdoorzaak is een inconsistente ValidationResult interface tussen verschillende modules, gecombineerd met architecturele schendingen (Streamlit dependencies in service layer) en ontbrekende test utilities.

## 1. SOLUTION ARCHITECTURE

### 1.1 ValidationResult Interface Standaardisatie

**Probleem**: Meerdere incompatibele ValidationResult implementaties:
- `src/services/validation/interfaces.py`: TypedDict implementatie (modern)
- `src/services/interfaces.py`: @dataclass implementatie (legacy)
- `src/validation/`: Aparte result classes per validator type
- `src/services/validation/astra_validator.py`: Eigen ValidationResult class

**Oplossing**: Unificeer naar single source of truth met adapter pattern

```python
# Centraal interface contract (TypedDict-based)
ValidationResult = services.validation.interfaces.ValidationResult

# Legacy adapter voor backward compatibility tijdens refactor
class ValidationResultAdapter:
    """Converts between TypedDict and dataclass representations"""

    @staticmethod
    def from_dataclass(dc_result) -> ValidationResult:
        """Convert dataclass to TypedDict format"""

    @staticmethod
    def to_dataclass(dict_result) -> DataclassValidationResult:
        """Convert TypedDict to dataclass format"""
```

### 1.2 Streamlit Dependency Isolation

**Probleem**: Service layer importeert Streamlit direct:
- `src/services/service_factory.py`: gebruikt st.cache_data
- Tests falen omdat MockStreamlit cache_data niet implementeert

**Oplossing**: Abstract caching naar cache utilities layer

```python
# utils/cache.py uitbreiden met service caching
@cache_service_instance
def get_cached_service(service_class, *args, **kwargs):
    """Cache service instances zonder Streamlit dependency"""
    return service_class(*args, **kwargs)

# services/service_factory.py refactoren
from utils.cache import cache_service_instance
# NIET: import streamlit as st
```

### 1.3 Import Path Restructuring

**Probleem**: ModernWebLookupService niet vindbaar in tests

**Oplossing**: Centraliseer service exports

```python
# src/services/__init__.py
from .web_lookup.modern_web_lookup_service import ModernWebLookupService
__all__ = [..., "ModernWebLookupService"]
```

## 2. IMPLEMENTATION ROADMAP

### Fase 1: Quick Wins (2-4 uur) ✅

**Doel**: Krijg test suite weer werkend met minimale wijzigingen

1. **MockStreamlit cache_data toevoegen** [30 min]
   ```python
   # tests/mocks/streamlit_mock.py
   def cache_data(func):
       return func  # Simple passthrough for tests
   ```

2. **ValidationResult wrapper fix** [1 uur]
   ```python
   # src/services/validation/modular_validation_service.py
   class ValidationResultWrapper:
       @property
       def status(self):
           return "valid" if self.is_valid else "invalid"
   ```

3. **Import paths fixen** [30 min]
   - Update `src/services/__init__.py` met alle service exports
   - Fix relative imports in test files

4. **Ontbrekende test files toevoegen** [1 uur]
   - `tests/unit/test_modern_web_lookup_service.py`
   - `tests/unit/test_validation_result_wrapper.py`

**Verificatie**: `pytest -x` moet zonder fatale errors draaien

### Fase 2: Structural Fixes (1-2 dagen) 🔄

**Doel**: Elimineer architecturele schendingen en verenig interfaces

1. **Service Factory Refactoring** [4 uur]
   - Verwijder alle Streamlit imports uit service layer
   - Migreer naar utils.cache voor caching
   - Implementeer proper dependency injection

2. **ValidationResult Unificatie** [4 uur]
   - Maak centrale ValidationResult TypedDict leading
   - Implementeer adapters voor legacy code
   - Update alle validators om consistent interface te gebruiken

3. **Test Infrastructure** [2 uur]
   - Centraliseer test fixtures in `tests/fixtures/`
   - Maak reusable mock factories
   - Documenteer test patterns

**Verificatie**:
- `pytest --cov=src` > 60% coverage
- Geen Streamlit imports buiten UI layer

### Fase 3: Quality Improvements (2-3 dagen) 🎯

**Doel**: Robuuste test suite met goede coverage

1. **Comprehensive Test Coverage** [8 uur]
   - Schrijf missende unit tests voor alle services
   - Voeg integration tests toe voor orchestrators
   - Implementeer property-based testing voor validators

2. **Test Performance** [4 uur]
   - Parallelliseer test execution met pytest-xdist
   - Implementeer test result caching
   - Optimaliseer slow tests met mocking

3. **Documentation & Standards** [4 uur]
   - Documenteer test patterns in `docs/testing/TEST_PATTERNS.md`
   - Voeg test writing guidelines toe
   - Maak test coverage dashboard

**Verificatie**:
- `pytest` < 30 seconden voor volledige suite
- Coverage > 75%
- Alle tests groen

## 3. TECHNICAL SPECIFICATIONS

### 3.1 Concrete Interface Designs

```python
# src/services/validation/unified_interface.py
from typing import Protocol, TypedDict, runtime_checkable

class ValidationResult(TypedDict):
    """Canonical ValidationResult interface"""
    version: str
    overall_score: float
    is_acceptable: bool
    violations: list[dict]
    # ... full spec from interfaces.py

@runtime_checkable
class ValidationResultLike(Protocol):
    """Protocol for duck-typed validation results"""
    @property
    def is_valid(self) -> bool: ...
    @property
    def violations(self) -> list: ...
```

### 3.2 Mock Implementations

```python
# tests/mocks/validation_mocks.py
class MockValidationResult:
    """Test-friendly validation result"""
    def __init__(self, is_valid=True, violations=None):
        self._data = {
            'is_acceptable': is_valid,
            'violations': violations or [],
            'overall_score': 1.0 if is_valid else 0.0
        }

    @property
    def status(self):
        return "valid" if self._data['is_acceptable'] else "invalid"

    def __getitem__(self, key):
        return self._data[key]
```

### 3.3 Directory Structure Changes

```
tests/
├── fixtures/              # NEW: Centralized test fixtures
│   ├── __init__.py
│   ├── validation.py     # Validation result fixtures
│   ├── services.py       # Service mocks
│   └── data.py          # Test data generators
├── mocks/
│   ├── streamlit_mock.py # UPDATED: Add cache_data
│   └── validation_mocks.py # NEW: Validation mocks
├── unit/
│   ├── services/
│   │   └── test_modern_web_lookup_service.py # NEW
│   └── validation/
│       └── test_validation_result_wrapper.py # NEW
└── integration/
    └── test_validation_flow.py # NEW: E2E validation test
```

## 4. MIGRATION STRATEGY

### 4.1 Incremental Migration Approach

Deze applicatie is NIET in productie - geen backwards compatibility nodig!

1. **Direct Refactor** (AANBEVOLEN)
   - Pas interfaces direct aan
   - Update alle consumers tegelijk
   - Geen migration paths of feature flags

2. **Test-First Migration**
   - Fix tests eerst met minimal changes
   - Refactor code met werkende tests als safety net
   - Verwijder legacy code zodra nieuwe implementatie werkt

### 4.2 Test Suite Update Plan

```bash
# Stap 1: Fix immediate blockers
pytest -x  # Stop bij eerste failure
# Fix MockStreamlit
# Fix ValidationResult.status

# Stap 2: Identificeer remaining failures
pytest --tb=short > test_failures.txt
# Categoriseer per root cause

# Stap 3: Fix per category
pytest tests/unit/services/ -x  # Fix service tests
pytest tests/unit/validation/ -x # Fix validation tests

# Stap 4: Verify full suite
pytest --cov=src --cov-report=term-missing
```

### 4.3 Validation Approach

**Automated Validation**:
```bash
# scripts/validate_refactor.sh
#!/bin/bash
echo "Checking for Streamlit imports in service layer..."
grep -r "import streamlit" src/services/ && exit 1

echo "Verifying ValidationResult consistency..."
python scripts/check_validation_interfaces.py

echo "Running test suite..."
pytest -q

echo "Checking coverage..."
pytest --cov=src --cov-fail-under=60
```

## 5. RISK MITIGATION

### 5.1 Potential Breaking Changes

| Risk | Impact | Mitigation |
|------|--------|------------|
| ValidationResult interface change | HIGH | Use adapter pattern tijdens transitie |
| Service caching verandering | MEDIUM | Test performance voor/na |
| Import path wijzigingen | LOW | Update all imports atomically |

### 5.2 Rollback Procedures

**Git-based Rollback** (Single-user app):
```bash
# Tag current state
git tag pre-refactor-$(date +%Y%m%d)

# If rollback needed
git reset --hard pre-refactor-20250119
```

### 5.3 Test Verification Steps

**Pre-refactor Baseline**:
```bash
# Capture current state
pytest --json-report --json-report-file=baseline.json
python scripts/analyze_test_failures.py > baseline_analysis.txt
```

**Post-refactor Verification**:
```bash
# Verify improvements
pytest --json-report --json-report-file=post_refactor.json
python scripts/compare_test_results.py baseline.json post_refactor.json

# Expected outcomes:
# - Failed tests: 31 -> 0
# - Coverage: >60%
# - No Streamlit imports in services/
```

## 6. IMPLEMENTATION CHECKLIST

### Phase 1: Quick Wins ✅
- [ ] Add cache_data to MockStreamlit
- [ ] Fix ValidationResult.status property
- [ ] Update import paths in __init__ files
- [ ] Create missing test files
- [ ] Run `pytest -x` successfully

### Phase 2: Structural Fixes 🔄
- [ ] Remove Streamlit from service_factory.py
- [ ] Implement ValidationResultAdapter
- [ ] Unify ValidationResult interfaces
- [ ] Create test fixtures directory
- [ ] Achieve 60% test coverage

### Phase 3: Quality Improvements 🎯
- [ ] Write comprehensive unit tests
- [ ] Add integration tests
- [ ] Optimize test performance
- [ ] Document test patterns
- [ ] Achieve 75% coverage

## 7. SUCCESS CRITERIA

✅ **Immediate Success** (Fase 1):
- Test suite draait zonder fatale errors
- MockStreamlit volledig functioneel
- ValidationResult.status werkt overal

✅ **Structural Success** (Fase 2):
- Geen Streamlit dependencies in service layer
- Single ValidationResult interface
- 60% test coverage

✅ **Quality Success** (Fase 3):
- 75% test coverage
- Test suite < 30 seconden
- Alle architectuur violations opgelost

## APPENDICES

### A. Affected Files List

**Critical Files** (moet direct gefixed):
- `tests/mocks/streamlit_mock.py`
- `src/services/validation/modular_validation_service.py`
- `src/services/service_factory.py`

**Refactor Targets** (fase 2):
- `src/services/interfaces.py`
- `src/services/validation/interfaces.py`
- `src/validation/*.py`

### B. Command Reference

```bash
# Quick test commands
make test                    # Run full test suite
pytest -x                   # Stop on first failure
pytest --lf                 # Run last failed
pytest -k "validation"      # Run validation tests only

# Coverage analysis
pytest --cov=src --cov-report=html
open htmlcov/index.html

# Performance profiling
pytest --profile-svg
```

### C. Related Documentation

- `docs/architectuur/TECHNICAL_ARCHITECTURE.md` - System architecture
- `docs/testing/validation_orchestrator_testplan.md` - Test strategy
- `~/.ai-agents/UNIFIED_INSTRUCTIONS.md` - Development guidelines
- `~/.ai-agents/quality-gates.yaml` - Quality requirements

---

**Next Steps**: Begin met Fase 1 Quick Wins om test suite direct werkend te krijgen, daarna incrementeel verbeteren volgens dit plan.