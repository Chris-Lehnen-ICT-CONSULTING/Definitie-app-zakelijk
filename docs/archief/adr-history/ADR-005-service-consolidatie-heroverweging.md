# ADR-005: Service Consolidatie Heroverweging

**Status:** Accepted ✅
**Datum:** 2025-01-18
**Deciders:** Development Team
**Decision Date:** 2025-01-18
**Relates to:** ADR-004 (Incrementele Migratie Strategie)

## Context

De poging om drie legacy services te consolideren in één `UnifiedDefinitionService` heeft geleid tot een problematische God Object met meer dan 1000 regels code. Deze consolidatie-aanpak creëert meer problemen dan het oplost.

### Huidige Situatie
- `UnifiedDefinitionService` combineert: generatie, validatie, orchestratie, caching
- Mix van synchrone en asynchrone operaties zonder duidelijke strategie
- Complexe conditional imports voor backward compatibility
- Legacy compatibility layers verhindere clean design
- Tight coupling met alle delen van de applicatie

### Waarom de Consolidatie Faalt
1. **Te Veel Verantwoordelijkheden**: Schendt Single Responsibility Principle
2. **Complexiteit**: Moeilijk te begrijpen, testen en onderhouden
3. **Rigiditeit**: Elke wijziging heeft impact op meerdere functionaliteiten
4. **Performance**: Geen mogelijkheid voor targeted optimalisatie
5. **Testing**: Onmogelijk om geïsoleerd te testen

## Probleemstelling

Hoe restructureren we de service layer om maintainability, testability en flexibility te verbeteren zonder de incrementele migratie strategie (ADR-004) te verstoren?

## Beslissing

We stoppen met de UnifiedDefinitionService consolidatie en adopteren een **Clean Service Architecture** met focused services en dependency injection.

### Nieuwe Service Structuur

```python
# Service Interfaces
class DefinitionGeneratorInterface(ABC):
    @abstractmethod
    async def generate(self, request: GenerationRequest) -> Definition:
        pass

class DefinitionValidatorInterface(ABC):
    @abstractmethod
    def validate(self, definition: Definition) -> ValidationResult:
        pass

class DefinitionRepositoryInterface(ABC):
    @abstractmethod
    def save(self, definition: Definition) -> int:
        pass

# Orchestration Service
class DefinitionOrchestrator:
    def __init__(
        self,
        generator: DefinitionGeneratorInterface,
        validator: DefinitionValidatorInterface,
        repository: DefinitionRepositoryInterface
    ):
        self.generator = generator
        self.validator = validator
        self.repository = repository

    async def create_definition(self, request: DefinitionRequest) -> DefinitionResponse:
        # Orchestrate the flow
        definition = await self.generator.generate(request)
        validation = self.validator.validate(definition)
        if validation.is_valid:
            definition_id = self.repository.save(definition)
        return DefinitionResponse(definition, validation)
```

## Rationale

1. **Single Responsibility**: Elke service heeft één duidelijke verantwoordelijkheid
2. **Testability**: Services kunnen geïsoleerd getest worden met mocks
3. **Flexibility**: Implementaties kunnen gewisseld worden zonder impact
4. **Incremental Migration**: Legacy code kan stap voor stap vervangen worden
5. **Clear Dependencies**: Expliciete dependencies via constructor injection

## Gevolgen

### Positief
- ✅ Clean, understandable code structure
- ✅ Verbeterde testability (unit tests mogelijk)
- ✅ Flexibele deployment opties (async waar nodig)
- ✅ Makkelijker te debuggen en profileren
- ✅ Team kan parallel aan verschillende services werken
- ✅ Legacy code kan geleidelijk uitgefaseerd worden

### Negatief
- ❌ Meer boilerplate code (interfaces, injection)
- ❌ Initial refactoring effort is significant
- ❌ Team moet dependency injection patterns leren
- ❌ Meer files en directories

## Implementatie Strategie

### Fase 1: Interfaces & Abstractions (Week 1)
1. Definieer service interfaces
2. Creëer abstract base classes
3. Setup dependency injection container

### Fase 2: Service Extraction (Week 2-3)
1. Extract `DefinitionGenerator` uit UnifiedDefinitionService
2. Extract `DefinitionValidator` (gebruik bestaande validator)
3. Implementeer `DefinitionRepository` pattern
4. Creëer `DefinitionOrchestrator`

### Fase 3: Legacy Adapters (Week 4)
1. Creëer adapters voor legacy code
2. Update UI om nieuwe services te gebruiken
3. Behoud backward compatibility waar nodig

### Fase 4: Cleanup (Week 5)
1. Verwijder UnifiedDefinitionService
2. Cleanup unused legacy code
3. Update documentatie

## Alternatieven Overwogen

1. **Doorgaan met UnifiedDefinitionService**
   - Rejected: Complexity blijft groeien

2. **Complete Rewrite**
   - Rejected: Te risicovol, conflicteert met ADR-004

3. **Microservices**
   - Rejected: Overkill voor huidige schaal

## Risico's en Mitigatie

| Risico | Impact | Mitigatie |
|--------|--------|-----------|
| Breaking changes | High | Comprehensive test suite eerste |
| Team weerstand | Medium | Training en pair programming |
| Performance regressie | Low | Benchmark voor/na refactoring |
| Scope creep | Medium | Strikte fase planning |

## Metrics voor Succes

- Code coverage: >80% voor nieuwe services
- Cyclomatic complexity: <10 per method
- Response time: Geen regressie
- Team velocity: Verbeterd na week 6

## Review Datum

Deze beslissing wordt geëvalueerd na implementatie van Fase 2 (ongeveer 3 weken).

---
*Voor de oorspronkelijke incrementele migratie strategie, zie [ADR-004](ADR-004-incrementele-migratie-strategie.md)*
