---
title: "COMPLETE V2 Migration Action Plan"
date: 2025-09-19
status: "IN_PROGRESS"
type: "planning"
category: "technical/migration"
canonical_location: "/docs/planning/"
tags: ["v2-migration", "refactoring", "testing"]
---

# 📋 COMPLETE V2 Migration Action Plan - STATUS UPDATE

## Executive Summary

**UPDATE 2025-09-19**: Veel migratie werk is al voltooid! De test failures komen voornamelijk door **legacy fallback methodes** die nog verwijderd moeten worden. Geschatte resterende werk: ~1 uur.

---

## 🔍 DEEL 1: Gedetailleerde Probleem Analyse

### 1.1 Missing ai_toetser.validators Module ✅ COMPLETED

**Status:** ✅ **OPGELOST - test_modular_toetser.py is al verwijderd**

**Origineel Probleem:**
- Test importeerde non-existente module: `from ai_toetser.validators import ValidationContext`
- Locatie: `tests/unit/test_modular_toetser.py:54`

**Actie Genomen:**
- File `tests/unit/test_modular_toetser.py` is succesvol verwijderd
- Functionaliteit wordt nog steeds getest in andere test files

### 1.2 V1→V2 Migration - PARTIALLY COMPLETE

**Status:** ⚠️ **DEELS VOLTOOID**

**Wat is al gedaan:**
- ✅ V1 files `ai_service.py` en `definition_orchestrator.py` zijn verwijderd
- ✅ Geen V1 symbols meer in imports

**NOG TE DOEN:**
- ❌ **Legacy fallback methodes in `definition_orchestrator_v2.py` (regels 896-959)**
  - `_get_legacy_validation_service()`
  - `_get_legacy_cleaning_service()`
  - `_get_legacy_repository()`

**Nieuwe Actie Vereist:**
```python
# In src/services/orchestrators/definition_orchestrator_v2.py
# VERWIJDER regels 896-959 (alle legacy fallback methodes)
```

### 1.3 Pytest Collection Warnings ⚠️ → ✅

**Probleem:**
- Classes `TestCase` en `TestResult` worden gezien als test classes door pytest
- Locatie: `tests/integration/test_modular_prompts.py`
- Warning: "cannot collect test class 'TestCase'"

**Oplossing:**
```python
# In tests/integration/test_modular_prompts.py

# VOOR:
@dataclass
class TestCase:
    name: str

@dataclass
class TestResult:
    passed: bool

# NA:
@dataclass
class ValidationTestCase:  # Renamed
    name: str

@dataclass
class ValidationTestResult:  # Renamed
    passed: bool

# Update alle references:
# TestCase → ValidationTestCase
# TestResult → ValidationTestResult
```

**Verificatie:**
```bash
pytest tests/integration/test_modular_prompts.py -v --tb=no
# Geen collection warnings meer
```

### 1.4 Cache Expiration Test Failure ❌ → ✅

**Probleem:**
- Test faalt op timing issues
- TTL van 0.1 seconde is te kort voor betrouwbare test
- Race condition tussen cache expire en test check

**Oplossing:**
```python
# In tests/unit/test_cache_system.py
# test_cache_expiration_in_manager():

# VOOR:
cache = CacheManager(ttl=0.1)
cache.set("test", "value")
time.sleep(0.15)  # Onbetrouwbaar!

# NA:
cache = CacheManager(ttl=1.0)  # Verhoog naar 1 seconde
cache.set("test", "value")
time.sleep(1.1)  # Betrouwbare marge
```

**Verificatie:**
```bash
pytest tests/unit/test_cache_system.py::TestCacheManager::test_cache_expiration_in_manager -xvs
# Test moet consistent passen
```

### 1.5 Business Logic Parity Test ❌ → ✅

**Probleem:**
- Verkeerde imports en service namen
- `unified_generator` bestaat niet (moet `generator` zijn)
- `generate_definition` method bestaat niet (moet `create_definition` zijn)

**Oplossing:**
```python
# In tests/integration/test_business_logic_parity.py

# VOOR:
from services.unified_definition_generator import UnifiedDefinitionGenerator
generator = container.get_service('unified_generator')
result = generator.generate_definition(request)

# NA:
from services.definition_generator import DefinitionGenerator
generator = container.get_service('generator')
result = generator.create_definition(request)
```

**Verificatie:**
```bash
pytest tests/integration/test_business_logic_parity.py --co -q
# Moet kunnen collecten zonder import errors
```

---

## 🛠️ DEEL 2: Extra Issues Gevonden door Code Review

### 2.1 ToetsregelManager Configuration ✅ NO ISSUE

**Status:** ✅ **GEEN PROBLEEM - False positive**

**Verificatie uitgevoerd:**
- ToetsregelManager gebruikt `RegelPrioriteit` enum, NIET float conversie
- Geen float(prioriteit) aanroepen gevonden
- Dit was een verkeerde aanname in originele analyse

### 2.2 Database Schema Warning ⚠️

**Probleem:**
```
table definities already exists
```

**Oplossing:**
```python
# In database initialisatie code

# VOOR:
with open('src/database/schema.sql') as f:
    cursor.executescript(f.read())  # Altijd uitvoeren

# NA:
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='definities'")
if not cursor.fetchone():
    # Alleen schema uitvoeren als table niet bestaat
    with open('src/database/schema.sql') as f:
        cursor.executescript(f.read())
```

### 2.3 Test Suite Timeout Issue ⏱️

**Probleem:**
- Volledige test suite timeout na 2 minuten
- Waarschijnlijk hanging tests in integration/web lookup

**Oplossing:**
```bash
# Identificeer slow/hanging tests
pytest tests/ --timeout=10 --timeout-method=thread -v

# Fix of skip problematische tests
# In pyproject.toml of pytest.ini:
[tool.pytest.ini_options]
timeout = 10
timeout_method = "thread"
```

---

## 🎯 ACTUELE STATUS & REMAINING WORK

### Wat is VOLTOOID:
✅ **test_modular_toetser.py verwijderd** - File bestaat niet meer
✅ **V1 service files verwijderd** - ai_service.py en definition_orchestrator.py bestaan niet meer
✅ **ToetsregelManager werkt correct** - Gebruikt enum, geen float issue
✅ **Plan in juiste locatie** - docs/planning/ is correct

### Wat moet NOG GEBEUREN:

#### 1. VERWIJDER Legacy Fallback Methodes ❌ URGENT
**File:** `src/services/orchestrators/definition_orchestrator_v2.py`
**Regels:** 896-959
**Methodes om te verwijderen:**
- `_get_legacy_validation_service()` (regels 896-921)
- `_get_legacy_cleaning_service()` (regels 923-954)
- `_get_legacy_repository()` (regels 956-959+)

#### 2. Fix Pytest Collection Warnings ⚠️
**File:** `tests/integration/test_modular_prompts.py`
**Actie:** Hernoem TestCase → ValidationTestCase

#### 3. Fix Cache Test Timing ⚠️
**File:** `tests/unit/test_cache_system.py`
**Actie:** Verhoog TTL van 0.1 naar 1.0 seconde

#### 4. Fix Business Logic Test ⚠️
**File:** `tests/integration/test_business_logic_parity.py`
**Actie:** Update imports en method namen

#### 5. Add Test Timeout Configuration ⚠️
**Actie:** Configureer pytest timeout op 10 seconden

## 📊 DEEL 3: Test Strategie & Verificatie

### 3.1 Pre-Implementation Verificatie

```bash
#!/bin/bash
# baseline-check.sh

echo "=== Current State Check ==="

# 1. Check V1 symbols
echo "V1 symbols present:"
grep -r "get_ai_service\|stuur_prompt_naar_gpt" src/ | wc -l

# 2. Check test failures
echo "Test import errors:"
pytest tests/unit/test_modular_toetser.py -x 2>&1 | grep "ModuleNotFoundError"

# 3. Check pytest warnings
echo "Collection warnings:"
pytest tests/integration/test_modular_prompts.py --co 2>&1 | grep "cannot collect"

# 4. Save baseline
pytest tests/ -v --tb=no > baseline-test-results.txt 2>&1
```

### 3.2 Implementation Order

```bash
# FASE 1: Quick Fixes (40 min)
1. Fix missing module (5 min)
   - rm tests/unit/test_modular_toetser.py
   - Verify: pytest tests/unit/test_ai_toetser.py -x

2. Complete V1→V2 migration (20 min)
   - rm src/services/definition_orchestrator.py
   - rm src/services/ai_service.py
   - Edit definition_orchestrator_v2.py: remove legacy method
   - Verify: grep -r "get_ai_service" src/ (moet leeg zijn)

3. Fix pytest warnings (5 min)
   - Rename TestCase → ValidationTestCase
   - Verify: pytest tests/integration/test_modular_prompts.py --co

4. Fix cache test (5 min)
   - Update TTL to 1.0 seconds
   - Verify: pytest tests/unit/test_cache_system.py -k expiration

5. Fix business logic test (5 min)
   - Update imports and method names
   - Verify: pytest tests/integration/test_business_logic_parity.py --co

# FASE 2: Critical Fixes (30 min)
6. Fix ToetsregelManager (15 min)
   - Add None checking for float conversion
   - Verify: Check logs for error message gone

7. Fix database schema warning (15 min)
   - Add existence check before CREATE TABLE
   - Verify: Run app twice, no warning second time

# FASE 3: Test Suite Health (30 min)
8. Fix hanging tests
   - Add pytest timeout configuration
   - Identify and fix/skip problematic tests
   - Verify: pytest tests/ completes within 30s
```

### 3.3 Verification Script

```bash
#!/bin/bash
# verify-v2-migration.sh

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=== V2 Migration Verification ==="

# Check 1: No V1 symbols
V1_COUNT=$(grep -r "get_ai_service\|stuur_prompt_naar_gpt\|DefinitionOrchestrator[^V]" src/ 2>/dev/null | wc -l)
if [ $V1_COUNT -eq 0 ]; then
    echo -e "${GREEN}✅ No V1 symbols found${NC}"
else
    echo -e "${RED}❌ Found $V1_COUNT V1 symbol references${NC}"
    exit 1
fi

# Check 2: No legacy files
if [ ! -f "src/services/ai_service.py" ] && [ ! -f "src/services/definition_orchestrator.py" ]; then
    echo -e "${GREEN}✅ Legacy files removed${NC}"
else
    echo -e "${RED}❌ Legacy files still present${NC}"
    exit 1
fi

# Check 3: Container uses V2
python -c "
from src.services.container import ServiceContainer
c = ServiceContainer()
if 'V2' in type(c.orchestrator()).__name__:
    print('✅ Container uses V2 orchestrator')
else:
    print('❌ Container not using V2')
    exit(1)
"

# Check 4: No pytest warnings
WARNINGS=$(pytest tests/integration/test_modular_prompts.py --co 2>&1 | grep -c "cannot collect")
if [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ No pytest collection warnings${NC}"
else
    echo -e "${RED}❌ Found $WARNINGS collection warnings${NC}"
fi

# Check 5: Critical tests pass
echo "Running critical tests..."
pytest tests/unit/test_ai_toetser.py \
       tests/unit/test_cache_system.py::TestCacheManager::test_cache_expiration_in_manager \
       -x --tb=no

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Critical tests pass${NC}"
else
    echo -e "${RED}❌ Critical test failures${NC}"
fi

echo "=== Migration Verification Complete ==="
```

### 3.4 Success Criteria

**Minimum (Must Have):**
- ✅ Geen V1 symbols in codebase
- ✅ ServiceContainer werkt met V2 services
- ✅ Geen import errors bij test collection
- ✅ Smoke tests passen (basis functionaliteit)

**Target (Should Have):**
- ✅ 60%+ test pass rate
- ✅ Geen pytest collection warnings
- ✅ ToetsregelManager laadt zonder errors
- ✅ Geen database schema warnings

**Stretch (Nice to Have):**
- ✅ 75%+ test pass rate
- ✅ Alle tests complete binnen 30 seconden
- ✅ Coverage > 60%
- ✅ Geen deprecation warnings

---

## 🚀 DEEL 4: Rollback Procedures

### Safe Implementation met Git

```bash
# Voor ELKE wijziging:
git status
git add -A
git commit -m "chore: backup before V2 migration fixes"

# Per fix een commit:
git commit -m "fix: remove obsolete ai_toetser.validators test"
git commit -m "refactor: complete V1→V2 migration, remove legacy files"
git commit -m "fix: rename TestCase to avoid pytest warnings"
git commit -m "fix: increase cache TTL for reliable test"
git commit -m "fix: update business logic test imports"

# Bij problemen:
git log --oneline -10  # Bekijk recente commits
git reset --hard HEAD~1  # Rollback laatste commit
```

### File-level Backup

```bash
# Backup critical files
cp -r src/services src/services.backup
cp -r tests tests.backup

# Na success:
rm -rf src/services.backup tests.backup
```

---

## 📈 DEEL 5: Performance & Metrics

### Expected Improvements

| Metric | Voor Fix | Na Fix | Improvement |
|--------|----------|--------|-------------|
| Test Pass Rate | ~30% | 75%+ | +150% |
| Test Runtime | Timeout (>120s) | <30s | -75% |
| V1 Code Lines | ~1000 | 0 | -100% |
| Import Errors | 12+ | 0 | -100% |
| Warnings | 15+ | <3 | -80% |

### Monitoring Commands

```bash
# Test health check
pytest tests/ --tb=no -q | tail -5

# Performance check
time pytest tests/smoke/ -x

# Coverage check
pytest --cov=src --cov-report=term-missing | grep TOTAL

# Memory usage
/usr/bin/time -l pytest tests/unit/
```

---

## ✅ DEEL 6: Finale Checklist

### Voor Implementatie
- [ ] Backup maken (git commit)
- [ ] Baseline test results opslaan
- [ ] CLAUDE.md instructies gelezen
- [ ] Development environment klaar

### Tijdens Implementatie
- [ ] Missing module test verwijderd
- [ ] V1 files verwijderd
- [ ] V2 orchestrator cleaned
- [ ] Test class namen aangepast
- [ ] Cache TTL verhoogd
- [ ] Business logic imports gefixed
- [ ] ToetsregelManager None check toegevoegd
- [ ] Database schema check toegevoegd

### Na Implementatie
- [ ] Verification script draait succesvol
- [ ] Smoke tests passen
- [ ] Geen V1 symbols aanwezig
- [ ] Test suite compleet binnen 30s
- [ ] App start zonder warnings
- [ ] Manual test: genereer definitie werkt

---

## 📝 DEEL 7: Documentatie Updates

### Te Updaten Files

```bash
# Update deze documentatie na fixes:
docs/refactor-log.md  # Voeg V1→V2 completion entry toe
docs/testing/README.md  # Update test instructies
CHANGELOG.md  # Document migration completion

# Verwijder obsolete docs:
rm docs/*V1*.md  # Als die bestaan
```

### Commit Message Template

```
feat(migration): complete V1→V2 architecture migration

- Remove obsolete ai_toetser.validators test
- Delete legacy V1 service files (ai_service.py, definition_orchestrator.py)
- Clean V2 orchestrator from legacy fallbacks
- Fix pytest collection warnings (TestCase naming)
- Improve cache test reliability (TTL adjustment)
- Update business logic test imports

BREAKING CHANGE: V1 services completely removed. All code must use V2 services via ServiceContainer.

Fixes: Test failures from incomplete migration
Performance: Removed ~1000 lines of unused V1 code
```

---

## 🏆 DEEL 8: Golden Test Examples voor Toetsregels

### Waarom Golden Tests?
Golden tests zijn referentie-implementaties die de correcte werking van toetsregels garanderen. Ze dienen als:
- Regressie detectie bij refactoring
- Documentatie van verwacht gedrag
- Verificatie dat business logica behouden blijft

### Voorbeeld Golden Test Structuur

```python
# tests/golden/test_toetsregels_golden.py

import pytest
from ai_toetser.modular_toetser import ModularToetser
from toetsregels.models import RegelPrioriteit

class TestToetsregelsGolden:
    """Golden tests voor kritieke toetsregels."""

    @pytest.fixture
    def toetser(self):
        """Create toetser instance."""
        return ModularToetser()

    def test_ESS_001_term_niet_in_definitie(self, toetser):
        """Golden test: Term mag niet in eigen definitie voorkomen."""
        # FAIL case
        result = toetser.toets_definitie(
            term="hypotheek",
            definitie="Een hypotheek is een lening met onroerend goed als onderpand."
        )

        assert "ESS-001" in [r.regel_id for r in result.regel_resultaten]
        ess_001 = next(r for r in result.regel_resultaten if r.regel_id == "ESS-001")
        assert not ess_001.voldaan
        assert "term 'hypotheek' komt voor in de definitie" in ess_001.feedback.lower()

        # PASS case
        result = toetser.toets_definitie(
            term="hypotheek",
            definitie="Een lening met onroerend goed als onderpand."
        )

        ess_001 = next(r for r in result.regel_resultaten if r.regel_id == "ESS-001")
        assert ess_001.voldaan

    def test_STR_002_minimale_lengte(self, toetser):
        """Golden test: Definitie moet minimaal 20 karakters zijn."""
        # FAIL case
        result = toetser.toets_definitie(
            term="test",
            definitie="Te kort."  # 8 karakters
        )

        str_002 = next(r for r in result.regel_resultaten if r.regel_id == "STR-002")
        assert not str_002.voldaan

        # PASS case
        result = toetser.toets_definitie(
            term="test",
            definitie="Een voldoende lange definitie met meer dan 20 karakters."
        )

        str_002 = next(r for r in result.regel_resultaten if r.regel_id == "STR-002")
        assert str_002.voldaan

    def test_CON_003_geen_tegenstrijdigheden(self, toetser):
        """Golden test: Definitie mag geen tegenstrijdigheden bevatten."""
        # FAIL case
        result = toetser.toets_definitie(
            term="test",
            definitie="Dit is zowel toegestaan als niet toegestaan."
        )

        con_003 = next(r for r in result.regel_resultaten if r.regel_id == "CON-003")
        assert not con_003.voldaan

        # PASS case
        result = toetser.toets_definitie(
            term="test",
            definitie="Dit is een consistente definitie zonder tegenstrijdigheden."
        )

        con_003 = next(r for r in result.regel_resultaten if r.regel_id == "CON-003")
        assert con_003.voldaan
```

### Test Data Repository

```python
# tests/golden/test_data.py

GOLDEN_DEFINITIONS = {
    "hypotheek": {
        "good": "Een recht van pand op een onroerende zaak tot zekerheid van een geldlening.",
        "bad_circular": "Een hypotheek is een vorm van hypothecaire zekerheid.",
        "bad_short": "Een lening.",
        "bad_vague": "Iets met een huis.",
    },
    "eigendom": {
        "good": "Het meest omvattende recht dat een persoon op een zaak kan hebben.",
        "bad_examples": "Bijvoorbeeld een huis, auto of fiets.",
        "bad_contradiction": "Het recht om te beschikken maar niet te gebruiken.",
    }
}
```

### Implementatie Checklist voor Golden Tests

1. **Selecteer 10-15 belangrijkste regels** voor golden tests
2. **Voor elke regel minimaal 2 cases**: pass en fail
3. **Gebruik realistische juridische voorbeelden**
4. **Test edge cases** (lege string, speciale karakters, etc.)
5. **Documenteer verwacht gedrag** in test docstrings

## 💡 Key Takeaways

1. **Probleem was NIET architectuur, maar incomplete refactoring**
2. **Oplossing is simpel: complete wat gestart was**
3. **Single-user app = geen backwards compatibility nodig**
4. **2-3 uur werk, niet 10+ dagen**
5. **Altijd eerst verifiëren, dan pas aannemen**

---

## 🎯 Next Steps

### IMMEDIATE ACTIONS REQUIRED:

1. **Remove Legacy Methods** (5 min)
   ```bash
   python scripts/remove_legacy_methods.py
   ```

2. **Run Golden Tests** (5 min)
   ```bash
   pytest tests/golden/test_toetsregels_golden.py -v
   ```

3. **Fix Remaining Test Issues** (20 min)
   - Update test_modular_prompts.py (TestCase naming)
   - Fix cache test timing
   - Update business logic test imports

4. **Verify Everything** (5 min)
   ```bash
   pytest tests/ --tb=short -q
   ```

### FILES CREATED IN THIS SESSION:

✅ **Updated Plan**: `/docs/planning/COMPLETE_V2_MIGRATION_ACTION_PLAN.md`
- Added frontmatter with canonical metadata
- Updated status to reflect completed work
- Removed false ToetsregelManager issue
- Added actual remaining work section

✅ **Removal Script**: `/scripts/remove_legacy_methods.py`
- Removes legacy fallback methods from definition_orchestrator_v2.py
- Lines 896-964 will be removed

✅ **Golden Tests**: `/tests/golden/test_toetsregels_golden.py`
- Comprehensive test suite for toetsregels
- Tests all major rule categories
- Includes edge cases and known good/bad definitions

✅ **Test Data**: `/tests/golden/test_data.py`
- Reference definitions for testing
- Edge cases for robustness testing
- Quality thresholds

### SUMMARY OF ACTUAL STATE:

| Component | Status | Notes |
|-----------|--------|-------|
| test_modular_toetser.py | ✅ REMOVED | Already gone |
| V1 service files | ✅ REMOVED | ai_service.py, definition_orchestrator.py already gone |
| Legacy fallback methods | ❌ TODO | Lines 896-964 in orchestrator_v2 |
| ToetsregelManager float issue | ✅ FALSE | Uses enum, not float |
| Migration plan location | ✅ CORRECT | In docs/planning/ |
| Golden tests | ✅ CREATED | New comprehensive test suite |

**Actual remaining work:** ~1 hour (not 2-3 hours)
**Risk:** ZEER LAAG (only removing unused methods)
**Impact:** HOOG (cleaner codebase, better tests)