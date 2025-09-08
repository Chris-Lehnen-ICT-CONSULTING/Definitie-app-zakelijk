# Session Overdracht - Story 2.3 ModularValidationService Implementatie

**Datum**: 09-01-2025 17:30
**Sessie**: Story 2.3 - Batch Processing & Bug Fixes Needed
**Branch**: `feat/story-2.3-container-wiring`
**Status**: 🟨 70% COMPLEET - Core werkt, batch processing ontbreekt

## 📊 ACTUELE STATUS OVERZICHT

### ✅ WAT IS AF (Werkend)
1. **ModularValidationService** volledig geïmplementeerd met:
   - 9 interne validatieregels (VAL, ESS, CON, LANG, STR)
   - Async `validate_definition` methode
   - Deterministische output
   - Error isolation per regel
   - Gewogen aggregatie

2. **Supporting modules compleet**:
   - `aggregation.py` - Weighted scoring
   - `config.py` - YAML configuratie
   - `types_internal.py` - Data classes
   - `module_adapter.py` - Error wrapper
   - `interfaces.py` - CONTRACT_VERSION en schemas

3. **Container integration actief**:
   - Direct gebruik van ModularValidationService
   - Export service validation gate werkend

### ❌ WAT ONTBREEKT (Moet nog)

#### 1. **BATCH_VALIDATE METHODE** (Hoogste Prioriteit)
```python
# DEZE METHODE MOET TOEGEVOEGD WORDEN AAN modular_validation_service.py:
async def batch_validate(
    self,
    items: Iterable[ValidationRequest],
    max_concurrency: int = 1,
) -> list[ValidationResult]:
    """Batch validatie met order preservation en error isolation."""
```

**7 tests falen hierop**:
- `test_batch_validate_interface`
- `test_batch_validate_order_preservation`
- `test_batch_validate_with_max_concurrency`
- `test_batch_validate_individual_failure_handling`
- `test_batch_validate_with_validation_request_objects`
- `test_batch_validate_empty_input`
- `test_batch_validate_performance_benefit`

#### 2. **BUG FIXES NODIG**:

**Aggregation Rounding Bug**:
- Test verwacht 0.80, krijgt 0.81
- File: `tests/services/test_modular_validation_aggregation.py`
- Regel 66: `({"r1": 0.7, "r2": 0.8, "r3": 0.9}, {"r1": 1.1, "r2": 1.2, "r3": 1.3}, 0.80)`
- Berekening: (0.77 + 0.96 + 1.17) / 3.6 = 0.8055 → rondt af naar 0.81
- **FIX**: Test expectation aanpassen naar 0.81

**Golden Test Type Issue**:
- Test faalt op: `assert res["overall_score"] >= pytest.approx(exp["min_overall_score"], rel=1e-3)`
- Error: `TypeError: '>=' not supported between instances of 'float' and 'ApproxScalar'`
- **FIX**: Assertion syntax aanpassen

## 🎯 IMPLEMENTATIE PLAN

### Stap 1: Batch Validate Toevoegen
```python
# Voeg toe aan modular_validation_service.py na regel 263:

async def batch_validate(
    self,
    items: Any,
    max_concurrency: int = 1,
) -> list[dict[str, Any]]:
    """Batch validatie van meerdere items."""
    import asyncio
    from collections.abc import Iterable

    # Convert items to list
    if not isinstance(items, list):
        items = list(items) if isinstance(items, Iterable) else []

    if not items:
        return []

    async def validate_item(item: Any) -> dict[str, Any]:
        try:
            # Support dict and object access
            if isinstance(item, dict):
                begrip = item.get("begrip", "")
                text = item.get("text", "")
                ontologische_categorie = item.get("ontologische_categorie")
                context = item.get("context")
            else:
                begrip = getattr(item, "begrip", "")
                text = getattr(item, "text", "")
                ontologische_categorie = getattr(item, "ontologische_categorie", None)
                context = getattr(item, "context", None)

            return await self.validate_definition(
                begrip=begrip,
                text=text,
                ontologische_categorie=ontologische_categorie,
                context=context
            )
        except Exception as e:
            # Return degraded result
            return {
                "version": CONTRACT_VERSION,
                "overall_score": 0.0,
                "is_acceptable": False,
                "violations": [{
                    "code": "SYS-ERR-001",
                    "severity": "error",
                    "message": f"Validation error: {str(e)}",
                    "rule_id": "SYS-ERR-001",
                    "category": "system",
                }],
                "passed_rules": [],
                "detailed_scores": {
                    "taal": 0.0,
                    "juridisch": 0.0,
                    "structuur": 0.0,
                    "samenhang": 0.0,
                },
                "system": {
                    "correlation_id": str(uuid.uuid4()),
                    "error": str(e),
                },
            }

    if max_concurrency <= 1:
        # Sequential
        results = []
        for item in items:
            result = await validate_item(item)
            results.append(result)
        return results
    else:
        # Concurrent with semaphore
        semaphore = asyncio.Semaphore(max_concurrency)

        async def validate_with_semaphore(item: Any) -> dict[str, Any]:
            async with semaphore:
                return await validate_item(item)

        tasks = [validate_with_semaphore(item) for item in items]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        return results
```

### Stap 2: Fix Test Bugs

**Fix 1 - Aggregation test**:
```python
# In tests/services/test_modular_validation_aggregation.py regel 66:
# CHANGE FROM:
({"r1": 0.7, "r2": 0.8, "r3": 0.9}, {"r1": 1.1, "r2": 1.2, "r3": 1.3}, 0.80),
# CHANGE TO:
({"r1": 0.7, "r2": 0.8, "r3": 0.9}, {"r1": 1.1, "r2": 1.2, "r3": 1.3}, 0.81),
```

**Fix 2 - Golden test assertion**:
```python
# In tests/services/test_golden_definitions_contract.py regel 39:
# CHANGE FROM:
assert res["overall_score"] >= pytest.approx(exp["min_overall_score"], rel=1e-3)
# CHANGE TO:
assert res["overall_score"] >= exp["min_overall_score"] - 0.001
```

### Stap 3: Test Commands

```bash
# Test batch processing na implementatie:
pytest tests/services/test_batch_validation.py -v

# Test aggregation fix:
pytest tests/services/test_modular_validation_aggregation.py::test_aggregation_two_decimal_rounding -xvs

# Test golden definitions:
pytest tests/services/test_golden_definitions_contract.py -v

# Full test suite:
pytest tests/services/test_modular* tests/services/test_golden* tests/services/test_batch* -v
```

## 📁 RELEVANTE BESTANDEN

### Core Implementatie:
- `/src/services/validation/modular_validation_service.py` - Hoofdservice (batch_validate toevoegen!)
- `/src/services/validation/interfaces.py` - Interface definities
- `/src/services/validation/aggregation.py` - Score berekening
- `/src/services/validation/config.py` - Configuratie loader
- `/src/services/validation/types_internal.py` - Data classes
- `/src/services/validation/module_adapter.py` - Error isolation

### Test Files (met issues):
- `/tests/services/test_batch_validation.py` - 7 failures (batch_validate ontbreekt)
- `/tests/services/test_modular_validation_aggregation.py` - 1 failure (rounding)
- `/tests/services/test_golden_definitions_contract.py` - 1 failure (assertion)

### Configuration:
- `/src/config/validation_rules.yaml` - Weights en thresholds
- `/src/services/container.py` - Service wiring

## 🔍 HUIDIGE TEST STATUS

```bash
# Laatste test run resultaten:
Total Tests: 43
Passed: 30 (70%)
Failed: 12
Errors: 1

# Specifiek:
- Batch validation: 7/7 FAILED (methode ontbreekt)
- Aggregation: 5/6 PASSED (1 rounding issue)
- Golden tests: 0/1 PASSED (assertion syntax)
- Contract tests: 3/3 PASSED ✅
- Determinism: 5/5 PASSED ✅
```

## ⚡ QUICK START VOOR VOLGENDE SESSIE

```bash
# 1. Check branch
git checkout feat/story-2.3-container-wiring

# 2. Check status
git status

# 3. Open key file voor batch_validate implementatie
code src/services/validation/modular_validation_service.py

# 4. Voeg batch_validate methode toe (zie implementatie plan hierboven)

# 5. Fix test bugs (zie Fix 1 en Fix 2)

# 6. Run tests
pytest tests/services/test_batch_validation.py -v

# 7. Als alles werkt, commit:
git add -A
git commit -m "feat: implement batch_validate method for ModularValidationService

- Add async batch_validate with max_concurrency support
- Implement error isolation per item
- Preserve input order in results
- Fix aggregation test rounding expectation
- Fix golden test assertion syntax

All 43 tests now passing for Story 2.3"
```

## 📈 VERWACHTE RESULTAAT NA IMPLEMENTATIE

Na toevoegen van batch_validate en fixes:
- ✅ Alle 43 tests zouden moeten slagen
- ✅ Story 2.3 100% compleet
- ✅ ModularValidationService volledig production-ready
- ✅ Container gebruikt nieuwe service zonder adapters

## 🎉 DEFINITIE VAN "KLAAR"

Story 2.3 is compleet wanneer:
- [ ] `batch_validate` methode werkt met alle 7 tests
- [ ] Aggregation rounding test slaagt
- [ ] Golden definitions test slaagt
- [ ] Alle 43 tests in de suite zijn groen
- [ ] Code is gecommit naar `feat/story-2.3-container-wiring`

## 💡 BELANGRIJKE NOTITIES

1. **Batch processing moet order preserving zijn** - resultaten in zelfde volgorde als input
2. **Error isolation is kritiek** - één failende item mag niet hele batch laten falen
3. **max_concurrency=1 betekent sequentieel** - niet parallel
4. **CONTRACT_VERSION = "1.0.0"** moet in alle responses
5. **Import asyncio alleen binnen batch_validate** OM circular imports te voorkomen

---

**Geschatte tijd voor completion**: 30-45 minuten
**Complexiteit**: Laag - vooral copy/paste werk
**Risico**: Minimaal - core functionaliteit werkt al
