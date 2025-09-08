# 📋 Legacy Code Inventory - Complete Overzicht

## 🔍 Wat is al verwijderd
✅ **src/services/definition_validator.py** - VERWIJDERD
✅ **ServiceContainer.validator()** method - VERWIJDERD
✅ **ValidatorConfig** in container.py - VERWIJDERD
✅ **validator stats** uit ServiceFactory.get_stats() - VERWIJDERD

## ⚠️ Wat is NOG aanwezig (legacy code te verwijderen)

### 1. Interfaces (src/services/interfaces.py)

#### DefinitionValidatorInterface (lines 194-232)
```python
class DefinitionValidatorInterface(ABC):
    """DEPRECATED: Deze sync interface is onderdeel van V1 architectuur."""
    def validate(self, definition: Definition) -> ValidationResult
    def validate_field(self, field_name: str, value: Any) -> ValidationResult
```
**Gebruikt door**: Niemand meer (was voor DefinitionValidator)
**Actie**: Kan volledig verwijderd worden

### 2. Validator in andere locaties

#### src/validation/definitie_validator.py (40KB!)
- **ANDERE validator** (niet services layer)
- Gebruikt door management_tab.py voor health checks
- **Beslissing nodig**: Behouden of migreren naar V2?

### 3. Legacy Patterns te onderzoeken

#### UnifiedGenerator / UnifiedDefinitionGenerator
- **UnifiedGeneratorConfig** - Nog VEEL gebruikt (87+ references!)
- **UnifiedDefinitionGenerator** class - Verwijderd maar comments blijven
- **UnifiedPromptBuilder** - Nog in gebruik door tests
- **Beslissing nodig**: UnifiedGeneratorConfig behouden of vervangen?

#### Sync vs Async patterns
- Veel oude code is sync
- V2 is volledig async
- **Check nodig**: Welke sync code kan weg?

### 4. Test Files met Legacy References

#### Tests die DefinitionValidatorInterface gebruiken
- tests/services/test_service_container.py - Heeft nog imports
- tests/test_legacy_validation_removed.py - Test of het verwijderd is
- tests/test_container.py - Mogelijk legacy references

### 5. Dead Code Candidates

#### Mogelijk ongebruikte services
- [ ] Check of UnifiedGeneratorConfig nog gebruikt wordt
- [ ] Check of alle interfaces in interfaces.py nog nodig zijn
- [ ] Check voor duplicate service implementations

### 6. Import Analysis

#### Files die mogelijk legacy imports hebben
```python
# Files to check:
- src/services/service_factory.py
- src/services/container.py
- src/ui/components/*.py
- tests/**/*.py
```

## 📊 Dependency Matrix

| Component | Depends On | Used By | Status |
|-----------|-----------|---------|--------|
| DefinitionValidatorInterface | - | Nobody | ❌ Can remove |
| definitie_validator.py | toetsregels | management_tab | ⚠️ Different system |
| ValidatorConfig | - | Nobody | ✅ Already removed |
| DefinitionValidator | ValidatorConfig | Nobody | ✅ Already removed |

## 🎯 Removal Prioriteit

### High Prioriteit (Direct verwijderen)
1. **DefinitionValidatorInterface** - Geen afhankelijkheden meer
2. **Test file updates** - Update tests die oude interface verwachten

### Medium Prioriteit (Analyse nodig)
1. **src/validation/definitie_validator.py** - Andere validator, check gebruik
2. **Legacy imports** - Scan alle files voor oude imports

### Low Prioriteit (Nice to have)
1. **Dead code** - Ongebruikte classes/functions
2. **Comment cleanup** - Oude TODO's en DEPRECATED comments

## 🔧 Commands voor Analysis

```bash
# Find all validator references
grep -r "validator" src/ --include="*.py" | grep -v "__pycache__"

# Find all deprecated code
grep -r "DEPRECATED" src/ --include="*.py"

# Find all TODO comments
grep -r "TODO" src/ --include="*.py"

# Find unused imports
python -m pyflakes src/

# Find dead code
vulture src/ --min-confidence 80
```

## ⚡ Quick Wins

Deze kunnen direct verwijderd worden zonder risico:
1. DefinitionValidatorInterface uit interfaces.py
2. Alle mentions van DefinitionValidator in comments
3. Unused imports van validator classes

## ⚠️ Risico's

1. **src/validation/definitie_validator.py** - Mogelijk in gebruik door UI
2. **Health checks** - Management tab gebruikt mogelijk validators
3. **Hidden afhankelijkheden** - Dynamische imports niet gevonden door grep

## 📝 Recommended Approach

1. **Fase 1**: Verwijder obvious dead code (interfaces, comments)
2. **Fase 2**: Update alle tests OM legacy niet meer te verwachten
3. **Fase 3**: Analyseer src/validation/ directory voor consolidatie
4. **Fase 4**: Final cleanup van imports en comments

---
*Inventory gemaakt op: 09-01-2025*
*Status: Analyse compleet, wacht op goedkeuring voor removal*
