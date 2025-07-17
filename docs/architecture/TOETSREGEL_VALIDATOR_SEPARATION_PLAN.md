# Plan: Scheiding ToetsregelValidator van DefinitieGenerator

## Huidige Situatie

De validatie (toetsing) is momenteel sterk gekoppeld aan generatie:
1. **UnifiedDefinitionService** combineert beide verantwoordelijkheden
2. **DefinitieAgent** heeft een vaste Generate→Validate→Feedback loop
3. **UI** verwacht altijd beide resultaten samen
4. **Session State** slaat alles als één geheel op

## Doel

- ToetsregelValidator volledig onafhankelijk maken van DefinitieGenerator
- Validatie mogelijk maken voor ELKE definitie (AI, mens, import)
- Aparte UI componenten voor validatie resultaten
- Flexibele architectuur waar validatie optioneel is

## Implementatie Plan

### Fase 1: Ontkoppel Service Layer (Week 1)

#### 1.1 Creëer Standalone ValidationService
```python
# src/services/validation_service.py
class ValidationService:
    """Onafhankelijke service voor definitie validatie."""
    
    def __init__(self):
        self.validator = ModularToetser()
        self.rule_manager = ToetsregelManager()
    
    def validate_definition(
        self,
        definitie: str,
        begrip: str,
        context: Dict[str, Any]
    ) -> ValidationResult:
        """Valideer een definitie onafhankelijk van bron."""
        # Pure validatie zonder kennis van generatie
```

#### 1.2 Refactor UnifiedDefinitionService
- VERWIJDER directe validatie calls uit `generate_definition()`
- Maak validatie een OPTIONELE stap
- Return alleen generatie resultaten

```python
# Oude flow:
result = generate_definition()  # Bevat definitie + validatie

# Nieuwe flow:
definition_result = generate_definition()  # Alleen definitie
validation_result = validate_definition()  # Aparte call indien gewenst
```

### Fase 2: UI Componenten Scheiding (Week 1-2)

#### 2.1 Creëer Dedicated Validation Component
```python
# src/ui/components/validation_panel.py
class ValidationPanel:
    """Standalone component voor validatie resultaten."""
    
    def render(self, definitie: str, begrip: str, context: Dict):
        # "Valideer" knop
        # Resultaten display
        # Export mogelijkheden
```

#### 2.2 Refactor DefinitionGeneratorTab
- VERWIJDER automatische validatie na generatie
- Voeg "Valideer Definitie" knop toe
- Toon validatie in apart panel/expander

#### 2.3 Nieuwe UI Flow
```
[Genereer Definitie] → Definitie verschijnt
                    ↓
[Valideer Definitie] → Validatie resultaten in apart panel
                    ↓
[Exporteer] → Keuze: alleen definitie OF definitie + validatie
```

### Fase 3: Session State Ontkoppeling (Week 2)

#### 3.1 Splits Session State
```python
# Oude structuur:
st.session_state.definition_results = {
    "definitie": "...",
    "beoordeling": [...],
    "score": 0.8
}

# Nieuwe structuur:
st.session_state.definitions = {
    "id_123": {
        "definitie": "...",
        "begrip": "...",
        "context": {...}
    }
}

st.session_state.validations = {
    "id_123": {
        "result": ValidationResult,
        "timestamp": "..."
    }
}
```

#### 3.2 Aparte Storage Functions
- `save_definition()` - Alleen definitie
- `save_validation()` - Alleen validatie
- `link_validation_to_definition()` - Koppel indien gewenst

### Fase 4: DefinitieAgent Refactoring (Week 2-3)

#### 4.1 Maak Validatie Optioneel
```python
class DefinitieAgent:
    def generate_definition(
        self,
        validate_iterations: bool = True  # Nu optioneel
    ):
        if validate_iterations:
            # Huidige flow
        else:
            # Alleen generatie
```

#### 4.2 Event-Based Architecture
```python
# Publish events in plaats van directe calls
self.event_bus.publish("definition.generated", result)
# ValidationService kan luisteren indien actief
```

### Fase 5: Modulaire Validator Verbetering (Week 3)

#### 5.1 Complete Alle Validators
- Implementeer ontbrekende validators (INT, SAM, VER, ARAI)
- Verwijder afhankelijkheid van legacy core.py

#### 5.2 Validator Registry Improvements
```python
# Auto-discovery van validators
validators = discover_validators("src/validation/validators/")
registry.register_all(validators)
```

#### 5.3 Performance Optimalisaties
- Parallel validation waar mogelijk
- Caching van regel configuraties
- Lazy loading van validators

## UI/UX Ontwerp

### Validation Results Display
```
┌─────────────────────────────────────┐
│ 📋 Definitie Validatie              │
├─────────────────────────────────────┤
│ Score: 85% (17/20 regels)          │
│                                     │
│ ✅ Geslaagd (17)                   │
│ ├─ CON-01: Context specifiek       │
│ ├─ ESS-01: Essentie beschreven     │
│ └─ ...                             │
│                                     │
│ ❌ Gefaald (3)                     │
│ ├─ INT-03: Onduidelijke verwijzing │
│ │  → "deze" op regel 2             │
│ │  💡 Vervang door "het proces"    │
│ └─ ...                             │
│                                     │
│ [📊 Details] [💾 Export] [🔄 Opnieuw]│
└─────────────────────────────────────┘
```

### Aparte Validatie Tab
```
Tabs: [Generator] [Validatie] [Historie] [Expert]
                      ↑
                  Nieuwe tab
```

## Testing Strategie

### Unit Tests
- ValidationService isolation tests
- Validator module tests
- UI component tests

### Integration Tests
- End-to-end validation flow
- Session state management
- Export functionality

### Performance Tests
- Bulk validation (100+ definities)
- Parallel processing
- Memory usage

## Rollout Plan

### Week 1
- [ ] Implementeer ValidationService
- [ ] Begin UI component separation
- [ ] Create feature flag voor nieuwe flow

### Week 2  
- [ ] Complete UI refactoring
- [ ] Session state splitting
- [ ] Begin DefinitieAgent refactor

### Week 3
- [ ] Complete all validators
- [ ] Performance optimizations
- [ ] Full testing suite

### Week 4
- [ ] User acceptance testing
- [ ] Documentation update
- [ ] Gradual rollout

## Success Criteria

1. **Functioneel**
   - Validatie werkt voor ELKE definitie bron
   - UI toont duidelijk gescheiden resultaten
   - Export ondersteunt beide opties

2. **Performance**
   - Validatie < 500ms voor enkele definitie
   - Bulk validatie schaalt lineair

3. **Maintainability**
   - Zero dependencies tussen validator en generator
   - Alle validators gedocumenteerd
   - 90%+ test coverage

## Risico's en Mitigatie

1. **Breaking Changes**
   - Mitigatie: Feature flags, gradual rollout
   
2. **User Confusion**
   - Mitigatie: Duidelijke UI, tooltips, documentatie

3. **Performance Degradatie**
   - Mitigatie: Caching, lazy loading, profiling