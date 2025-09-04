# 🚀 Plan: Legacy Validation Verwijderen

> Status: VOLTOOID (v2.3.1). Legacy `DefinitionValidator` en `DefinitionValidatorInterface` zijn verwijderd. Deze pagina blijft bewaard als historisch migratieplan.

## Doel
Volledig verwijderen van legacy DefinitionValidator en overstappen naar V2 modulaire architectuur.

## Huidige Situatie

### Legacy Components
1. **src/services/definition_validator.py** (12KB)
   - Gebruikt door: ServiceContainer.validator()
   - Functionaliteit: Validatie + stats tracking

2. **src/validation/definitie_validator.py** (40KB)
   - ANDERE validator (niet gerelateerd aan services layer)
   - Gebruikt door: management_tab.py voor health checks
   - Dit kan blijven of apart gemigreerd worden

### Dependencies op Legacy DefinitionValidator

#### Productie Code
1. **ServiceContainer.validator()** (line 147-157)
   - Creëert DefinitionValidator instance
   - Gebruikt door ServiceFactory

2. **ServiceFactory.get_stats()** (line 309)
   - Roept `container.validator().get_stats()` aan
   - Stats: total_validations, passed, failed, average_score

#### Test Code (9 files)
- test_service_container.py
- test_definition_validator.py
- test_services_simple.py
- test_services_basic.py
- test_new_services_integration.py
- test_container.py
- benchmark_services.py
- simple_benchmark.py

## 📋 Migratieplan

### Stap 1: Stats Functionaliteit Toevoegen aan V2 (30 min)

**File**: `src/services/orchestrators/validation_orchestrator_v2.py`

```python
class ValidationOrchestratorV2(ValidationOrchestratorInterface):
    def __init__(self, ...):
        # Existing code
        self._stats = {
            "total_validations": 0,
            "passed_validations": 0,
            "failed_validations": 0,
            "average_score": 0.0
        }

    async def validate_text(self, ...):
        # Existing validation code
        result = await self._perform_validation(...)

        # Update stats
        self._update_stats(result)
        return result

    def _update_stats(self, result: ValidationResult):
        """Update statistics based on validation result."""
        self._stats["total_validations"] += 1
        if result.is_valid:
            self._stats["passed_validations"] += 1
        else:
            self._stats["failed_validations"] += 1

        # Update average score
        total = self._stats["total_validations"]
        current_avg = self._stats["average_score"]
        new_score = result.confidence_score
        self._stats["average_score"] = ((current_avg * (total - 1)) + new_score) / total

    def get_stats(self) -> dict:
        """Get validation statistics."""
        return self._stats.copy()
```

### Stap 2: ServiceContainer Updaten (15 min)

**File**: `src/services/container.py`

```python
def validator(self) -> ValidationOrchestratorInterface:
    """
    Get V2 validation orchestrator.
    Legacy DefinitionValidator is deprecated.
    """
    if "validator" not in self._instances:
        # Use V2 orchestrator for validation
        validation_service = self.get_validation_service()  # Implement this
        cleaning_service = self.get_cleaning_service()     # Optional

        self._instances["validator"] = ValidationOrchestratorV2(
            validation_service=validation_service,
            cleaning_service=cleaning_service
        )
        logger.info("ValidationOrchestratorV2 instance created as validator")
    return self._instances["validator"]
```

### Stap 3: ServiceFactory Aanpassen (10 min)

**File**: `src/services/service_factory.py`

```python
def get_stats(self) -> dict:
    """Get statistieken van alle services."""
    stats = {
        "generator": self.container.generator().get_stats(),
        "repository": self.container.repository().get_stats(),
        "orchestrator": self.orchestrator.get_stats(),
    }

    # Validator stats alleen als V2 orchestrator get_stats heeft
    validator = self.container.validator()
    if hasattr(validator, 'get_stats'):
        stats["validator"] = validator.get_stats()
    else:
        stats["validator"] = {"message": "V2 validator - stats not implemented"}

    return stats
```

### Stap 4: Tests Migreren (1-2 uur)

Voor elke test file die DefinitionValidator gebruikt:

**Van (Legacy)**:
```python
from services.definition_validator import DefinitionValidator

def test_validation():
    validator = DefinitionValidator(config)
    result = validator.validate_definition(definition)
    assert result.is_valid
```

**Naar (V2)**:
```python
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
import asyncio

def test_validation():
    orchestrator = ValidationOrchestratorV2(validation_service, cleaning_service)
    result = asyncio.run(orchestrator.validate_text(
        begrip=definition.begrip,
        text=definition.definitie
    ))
    assert result.is_valid
```

### Stap 5: Legacy Files Verwijderen (5 min)

```bash
# Verwijder legacy validator
rm src/services/definition_validator.py

# Verwijder oude tests (of update ze)
rm tests/services/test_definition_validator.py

# Update imports waar nodig
```

## ⚠️ Risico's & Mitigatie

| Risico | Impact | Mitigatie |
|--------|--------|-----------|
| Stats format verschilt | LOW | Map oude stats naar nieuwe format |
| Async vs Sync | MEDIUM | Gebruik asyncio.run() wrapper waar nodig |
| Test failures | LOW | Update tests incrementeel |
| Onbekende dependencies | LOW | Gebruik grep voor final check |

## 🎯 Eindresultaat

- **GEEN** DefinitionValidator meer in services layer
- **GEEN** dubbele validatie systemen
- **WEL** clean V2 architectuur
- **WEL** backwards compatible stats (indien nodig)

## Tijdsinschatting

- Stap 1: 30 minuten (stats toevoegen aan V2)
- Stap 2: 15 minuten (container update)
- Stap 3: 10 minuten (factory update)
- Stap 4: 1-2 uur (tests migreren)
- Stap 5: 5 minuten (cleanup)

**Totaal: 2-3 uur werk**

## Alternatief: Radicale Optie

Als stats NIET belangrijk zijn:

1. **Verwijder** regel 309 uit ServiceFactory.get_stats()
2. **Verwijder** container.validator() methode volledig
3. **Verwijder** src/services/definition_validator.py
4. **Update/verwijder** alle tests die het gebruiken

**Totaal: 30 minuten werk**

Dit is de cleanste optie als je echt GEEN backwards compatibility wilt!
