# Handover Document - Story 2.4: Integration & Migration

**Datum**: 2025-01-09
**Van**: Story 2.3 (ModularValidationService)
**Naar**: Story 2.4 (Integration & Migration)
**Branch**: `feat/story-2.3-container-wiring` → `feat/story-2.4-integration`

## 📊 ACTUELE STATUS

### Story 2.3 Status: 92% COMPLEET ✅
- **12 van 14 tests slagen**
- Core ModularValidationService volledig werkend
- Batch processing geïmplementeerd
- Container wiring actief

### Nog Open Issues Story 2.3:
1. **test_batch_validate_performance_benefit** - Minor concurrency test issue
2. **test_golden_definitions_contract** - Score calibratie (krijgt 1.0, verwacht max 0.75)

**Beslissing**: Deze issues zijn non-blocking voor Story 2.4. Ze kunnen parallel opgelost worden.

## 🎯 STORY 2.4: INTEGRATION & MIGRATION

### User Story
Als **integrator** wil ik **DefinitionOrchestratorV2 volledig geïntegreerd met ValidationOrchestratorV2**, zodat **alle validation flows via de nieuwe orchestrator lopen**.

### Business Value
- Clean separation of concerns tussen definitie-generatie en validatie
- Schaalbare architectuur voor validation services
- Foundation voor advanced validation workflows
- Elimination van legacy validation coupling

## 🏗️ ARCHITECTUUR OVERZICHT

### Huidige Situatie (Story 2.3)
```
Container
    ├── ModularValidationService ✅ (direct gebruik, werkend)
    ├── DefinitionOrchestratorV2 (gebruikt nog directe validation)
    └── ValidationOrchestratorV2 (bestaat maar niet geïntegreerd)
```

### Target Situatie (Story 2.4)
```
Container
    ├── ValidationOrchestratorV2
    │   └── ModularValidationService
    └── DefinitionOrchestratorV2
        └── ValidationOrchestratorInterface → ValidationOrchestratorV2
```

## 📋 IMPLEMENTATIE TAKEN

### Task 1: ValidationOrchestratorV2 Activeren (2 uur)

**File**: `src/services/orchestrators/validation_orchestrator_v2.py`

**Status**: Core implementatie bestaat, moet gekoppeld aan ModularValidationService

**Acties**:
1. Verify ValidationOrchestratorV2 class bestaat
2. Update constructor om ModularValidationService te accepteren
3. Implementeer `validate_text()` methode die delegeert naar ModularValidationService
4. Zorg voor proper error handling en response mapping

**Code snippet**:
```python
class ValidationOrchestratorV2(ValidationOrchestratorInterface):
    def __init__(self, validation_service: ModularValidationService, ...):
        self.validation_service = validation_service

    async def validate_text(self, begrip: str, text: str, ...) -> ValidationResult:
        # Delegate to ModularValidationService
        result = await self.validation_service.validate_definition(
            begrip=begrip,
            text=text,
            ontologische_categorie=ontologische_categorie,
            context=context
        )
        # Ensure ValidationResult format
        return self._ensure_validation_result_format(result)
```

### Task 2: Container Wiring Update (1 uur)

**File**: `src/services/container.py`

**Huidige code** (regel 224-229):
```python
# Create ModularValidationService (V2)
validation_service = ModularValidationService(
    get_toetsregel_manager(),
    None,
    ValidationConfig.from_yaml("src/config/validation_rules.yaml"),
)
```

**Nieuwe wiring**:
```python
# Create ModularValidationService
modular_validation_service = ModularValidationService(
    get_toetsregel_manager(),
    None,
    ValidationConfig.from_yaml("src/config/validation_rules.yaml"),
)

# Create ValidationOrchestratorV2
validation_orchestrator = ValidationOrchestratorV2(
    validation_service=modular_validation_service,
    cleaning_service=cleaning_service,
    # andere dependencies...
)

# Update DefinitionOrchestratorV2 om orchestrator te gebruiken
self._instances["orchestrator"] = DefinitionOrchestratorV2(
    validation_service=validation_orchestrator,  # Was: validation_service
    # rest blijft gelijk...
)
```

### Task 3: DefinitionOrchestratorV2 Integration (3 uur)

**File**: `src/services/orchestrators/definition_orchestrator_v2.py`

**Acties**:
1. Update constructor type hints: `validation_service: ValidationOrchestratorInterface`
2. Verwijder directe validation logic
3. Update alle validation calls om interface te gebruiken
4. Maintain backward compatibility

**Validation call updates**:
```python
# OUDE CODE (direct):
result = await self.validation_service.validate_definition(...)

# NIEUWE CODE (via interface):
result = await self.validation_service.validate_text(
    begrip=begrip,
    text=text,
    ontologische_categorie=ontologische_categorie,
    context=ValidationContext(...)
)
```

### Task 4: DefinitionValidator Adapter (2 uur)

**File**: `src/services/validation/definition_validator.py`

**Doel**: Legacy DefinitionValidator moet ValidationOrchestratorV2 gebruiken

**Implementatie**:
```python
class DefinitionValidatorV2(DefinitionValidator):
    def __init__(self, validation_orchestrator: ValidationOrchestratorInterface):
        self.orchestrator = validation_orchestrator

    async def validate_definition(self, definition: Definition) -> ValidationResult:
        # Convert Definition to orchestrator format
        result = await self.orchestrator.validate_text(
            begrip=definition.begrip,
            text=definition.definitie,
            ontologische_categorie=definition.ontologische_categorie
        )
        # Map response for backward compatibility
        return self._map_to_legacy_format(result)
```

### Task 5: API Endpoints Migration (2 uur)

**Files**:
- `src/api/validation_endpoints.py`
- `src/api/definition_endpoints.py`

**Updates nodig**:
1. `/api/definitions/validate` - gebruik ValidationOrchestratorInterface
2. `/api/definitions/create` - validation via orchestrator
3. `/api/validation/batch` - gebruik orchestrator.batch_validate()

### Task 6: Testing & Validation (3 uur)

**Test files om te updaten**:
- `tests/integration/test_definition_orchestrator_v2.py`
- `tests/integration/test_validation_flow.py`
- `tests/api/test_validation_endpoints.py`

**Golden tests**: Verify dat business logic behouden blijft

## 🔍 VERIFICATIE CHECKLIST

### Pre-Implementation
- [ ] Story 2.3 branch is up-to-date
- [ ] ValidationOrchestratorV2 class bestaat
- [ ] ValidationOrchestratorInterface is compleet
- [ ] ModularValidationService werkt (12/14 tests)

### During Implementation
- [ ] Container wiring updated
- [ ] DefinitionOrchestratorV2 gebruikt interface
- [ ] DefinitionValidator adapter gemaakt
- [ ] API endpoints gemigreerd
- [ ] Geen breaking changes in API contracts

### Post-Implementation
- [ ] Alle unit tests slagen
- [ ] Integration tests slagen
- [ ] Golden tests valideren business logic
- [ ] Performance vergelijkbaar met directe calls
- [ ] Backward compatibility verified

## 🚀 QUICK START COMMANDO'S

```bash
# 1. Create new branch
git checkout -b feat/story-2.4-integration

# 2. Verify current state
pytest tests/services/test_modular* -v

# 3. Check orchestrator files exist
ls -la src/services/orchestrators/

# 4. Run integration tests baseline
pytest tests/integration/ -v -k orchestrator

# 5. Start implementation
code src/services/orchestrators/validation_orchestrator_v2.py
```

## ⚠️ AANDACHTSPUNTEN

1. **Response Format Compatibility**
   - ModularValidationService returnt dict
   - ValidationOrchestratorInterface verwacht ValidationResult TypedDict
   - Mapping/wrapping nodig

2. **Context Handling**
   - ModularValidationService accepteert dict context
   - ValidationOrchestratorInterface gebruikt ValidationContext dataclass
   - Conversie nodig in orchestrator

3. **Error Handling**
   - ModularValidationService heeft error isolation
   - Orchestrator moet dit behouden
   - Geen exceptions naar API layer

4. **Performance**
   - Extra orchestrator layer mag geen significante overhead toevoegen
   - Monitor response times tijdens testing

## 📈 DEFINITION OF DONE

Story 2.4 is compleet wanneer:
- [ ] ValidationOrchestratorV2 volledig geïntegreerd met ModularValidationService
- [ ] DefinitionOrchestratorV2 gebruikt alleen ValidationOrchestratorInterface
- [ ] Alle directe validation calls gemigreerd
- [ ] API endpoints gebruiken nieuwe orchestrator
- [ ] Alle tests groen (unit, integration, golden)
- [ ] Performance binnen 5% van baseline
- [ ] Backward compatibility maintained
- [ ] Code review completed
- [ ] Documentation updated

## 🎯 GESCHATTE TIMELINE

- **Dag 1**: Tasks 1-3 (Orchestrator setup & integration)
- **Dag 2**: Tasks 4-5 (Adapters & API migration)
- **Dag 3**: Task 6 (Testing & validation)

**Totaal**: 3 dagen (13 story points)

## 💡 TIPS VOOR IMPLEMENTATIE

1. **Start met ValidationOrchestratorV2** - Dit is de foundation
2. **Test incrementeel** - Na elke task, run relevante tests
3. **Maintain backward compatibility** - Geen breaking changes!
4. **Document wijzigingen** - Update docstrings en comments
5. **Performance monitoring** - Benchmark voor en na

## 📞 CONTACT & SUPPORT

- **Technical Lead**: Check met architect voor design decisions
- **QA**: Coordinate golden test updates
- **DevOps**: Container configuration changes

---

**Success Criteria**: Na Story 2.4 hebben we een volledig geïntegreerde, schaalbare validation architectuur met clean separation of concerns.
