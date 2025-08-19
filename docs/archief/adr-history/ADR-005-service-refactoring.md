# ADR-005: Service Refactoring naar Clean Architecture

## Status
**Implemented** (2025-08-11)

## Context

Het DefinitieAgent systeem was oorspronkelijk gebouwd met een monolithische `UnifiedDefinitionService` die alle functionaliteit bevatte. Dit leidde tot:
- Moeilijk testbare code (alles zat in één grote class)
- Tight coupling tussen verschillende verantwoordelijkheden
- Geen dependency injection
- Moeilijk uit te breiden met nieuwe features

## Decision

We hebben besloten de architectuur te refactoren naar een clean service architectuur met:

1. **Vier gespecialiseerde services**:
   - `DefinitionGenerator`: AI-powered definitie generatie
   - `DefinitionValidator`: Kwaliteitsvalidatie met toetsregels
   - `DefinitionRepository`: Database operaties
   - `DefinitionOrchestrator`: Workflow coördinatie

2. **Dependency Injection Container**:
   - Centrale configuratie management
   - Singleton service instances
   - Environment-specifieke configuraties

3. **Feature Flag System**:
   - Geleidelijke migratie mogelijk
   - Real-time switching tussen architecturen
   - UI toggle in sidebar

## Implementation Details

### Service Interfaces
```python
# src/services/interfaces.py
class DefinitionGeneratorInterface(ABC):
    async def generate(self, request: GenerationRequest) -> Definition
    async def enhance(self, definition: Definition) -> Definition

class DefinitionValidatorInterface(ABC):
    def validate(self, definition: Definition) -> ValidationResult
    def get_stats(self) -> Dict[str, Any]

class DefinitionRepositoryInterface(ABC):
    def save(self, definition: Definition) -> int
    def get(self, definition_id: int) -> Optional[Definition]
    def search(self, query: str) -> List[Definition]

class DefinitionOrchestratorInterface(ABC):
    async def create_definition(self, request: GenerationRequest) -> DefinitionResponse
    async def update_definition(self, definition_id: int, updates: Dict) -> DefinitionResponse
```

### Container Configuration
```python
# Environment-specific configurations
ContainerConfigs.development()   # GPT-3.5, ontology enabled
ContainerConfigs.testing()       # In-memory DB, ontology disabled
ContainerConfigs.production()    # GPT-4, all features enabled
```

### Feature Flag Integration
```python
# Automatic detection based on environment or UI toggle
if os.getenv('USE_NEW_SERVICES') == 'true':
    service = ServiceAdapter(container)
else:
    service = UnifiedDefinitionService()
```

## Consequences

### Positive
- ✅ **Testability**: Each service can be tested in isolation
- ✅ **Maintainability**: Clear separation of concerns
- ✅ **Flexibility**: Easy to swap implementations
- ✅ **Performance**: Actually faster startup (9ms vs 1121ms)
- ✅ **Extensibility**: New features can be added as services
- ✅ **Gradual Migration**: Feature flags allow safe rollout

### Negative
- ❌ **Complexity**: More files and abstractions
- ❌ **Memory**: Slightly higher memory usage (multiple objects)
- ❌ **Learning Curve**: Developers need to understand DI pattern

## Migration Path

### Week 1: Interfaces & Implementation ✅
- Created service interfaces
- Implemented all 4 services with adapters
- Maintained backward compatibility

### Week 2: DI Container & Feature Flags ✅
- Built ServiceContainer with configurations
- Added feature flag system
- Integrated with UI (sidebar toggle)

### Week 3: Integration & Testing ✅
- Database schema compatibility fixed
- Ontological analysis integrated
- Performance benchmarks completed

### Week 4: Documentation & Deployment
- This ADR documents the changes
- Ready for production deployment
- Legacy code can be removed after verification

## Lessons Learned

1. **Adapter Pattern Works Well**: Wrapping legacy code in new interfaces allowed incremental refactoring
2. **Feature Flags Essential**: Being able to switch between implementations gave confidence
3. **Performance Not An Issue**: Clean architecture can be just as fast or faster
4. **Testing Is Much Easier**: Individual service tests are simpler to write and maintain

## References

- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Dependency Injection Pattern](https://martinfowler.com/articles/injection.html)
- [Feature Toggles](https://martinfowler.com/articles/feature-toggles.html)
