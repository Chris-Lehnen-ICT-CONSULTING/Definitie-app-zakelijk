# 🔨 Refactoring Action Plan - UnifiedDefinitionService

**Beslissing**: Direct refactoren naar clean services (ADR-005)  
**Start**: Week 1  
**Doel**: God Object opsplitsen in focused services met dependency injection

## 📐 Target Architecture

```
┌─────────────────────────────────────────────┐
│             Streamlit UI Layer              │
├─────────────────────────────────────────────┤
│          Service Interfaces                 │
├─────────────────────────────────────────────┤
│   DefinitionGenerator │ DefinitionValidator │
│   DefinitionRepository│ DefinitionOrchestrator│
└─────────────────────────────────────────────┘
```

## 🚀 Week 1: Foundation & Extraction

### Dag 1-2: Setup & Interfaces
```python
# 1. Create service interfaces (src/services/interfaces.py)
from abc import ABC, abstractmethod

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
```

### Dag 3: Extract DefinitionGenerator
```python
# src/services/definition_generator.py
class DefinitionGenerator(DefinitionGeneratorInterface):
    """Focused service voor definitie generatie."""
    
    def __init__(self, ai_client: OpenAIClient):
        self.ai_client = ai_client
        self.prompt_builder = PromptBuilder()
    
    async def generate(self, request: GenerationRequest) -> Definition:
        # Extract logic from UnifiedDefinitionService
        prompt = self.prompt_builder.build(request)
        response = await self.ai_client.complete(prompt)
        return self._parse_response(response)
```

### Dag 4: Extract DefinitionValidator
```python
# src/services/definition_validator.py
class DefinitionValidator(DefinitionValidatorInterface):
    """Focused service voor validatie."""
    
    def __init__(self, rule_manager: RuleManager):
        self.rule_manager = rule_manager
    
    def validate(self, definition: Definition) -> ValidationResult:
        # Use existing validator logic
        return self.rule_manager.validate_all(definition)
```

### Dag 5: Create Orchestrator
```python
# src/services/definition_orchestrator.py
class DefinitionOrchestrator:
    """Orchestrates the definition creation flow."""
    
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
            definition.id = definition_id
        
        return DefinitionResponse(definition, validation)
```

## 🔄 Week 2: Migration & Testing

### Dependency Injection Setup
```python
# src/container.py
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    # Configuration
    config = providers.Configuration()
    
    # External services
    openai_client = providers.Singleton(
        OpenAIClient,
        api_key=config.openai.api_key
    )
    
    # Core services
    generator = providers.Singleton(
        DefinitionGenerator,
        ai_client=openai_client
    )
    
    validator = providers.Singleton(
        DefinitionValidator,
        rule_manager=providers.Singleton(RuleManager)
    )
    
    repository = providers.Singleton(
        DefinitionRepository,
        session_factory=providers.Factory(Session)
    )
    
    orchestrator = providers.Singleton(
        DefinitionOrchestrator,
        generator=generator,
        validator=validator,
        repository=repository
    )
```

### UI Integration with Feature Flag
```python
# src/app.py
def get_definition_service():
    """Get service based on feature flag."""
    if st.session_state.get('use_new_services', False):
        # New clean architecture
        container = Container()
        return container.orchestrator()
    else:
        # Legacy fallback
        return UnifiedDefinitionService.get_instance()

# In UI code
service = get_definition_service()
result = await service.create_definition(request)
```

## 📊 Migration Checklist

### Week 1 Deliverables
- [ ] Service interfaces defined
- [ ] DefinitionGenerator extracted
- [ ] DefinitionValidator extracted  
- [ ] DefinitionRepository created
- [ ] DefinitionOrchestrator implemented
- [ ] Basic DI container setup

### Week 2 Deliverables
- [ ] Feature flag system active
- [ ] UI integration complete
- [ ] Unit tests for each service
- [ ] Integration tests passing
- [ ] Performance benchmarks
- [ ] Gradual rollout plan

## 🧪 Testing Strategy

### Unit Tests per Service
```python
# tests/unit/test_definition_generator.py
class TestDefinitionGenerator:
    def test_generate_with_mock_ai(self, mock_openai):
        generator = DefinitionGenerator(mock_openai)
        result = await generator.generate(request)
        assert result.term == request.term

# tests/unit/test_orchestrator.py
class TestOrchestrator:
    def test_full_flow(self, mock_generator, mock_validator, mock_repo):
        orchestrator = DefinitionOrchestrator(
            mock_generator, mock_validator, mock_repo
        )
        result = await orchestrator.create_definition(request)
        assert result.success
```

## 🚦 Rollout Plan

### Phase 1: Internal Testing (Week 2)
- Team dogfooding met feature flag
- Performance comparison
- Bug fixing

### Phase 2: Beta Users (Week 3)
- 10% traffic naar nieuwe services
- Monitor error rates
- Collect feedback

### Phase 3: Full Rollout (Week 4)
- Gradual increase to 100%
- Remove legacy code
- Celebrate! 🎉

## ⚠️ Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Breaking changes | High | Feature flags + instant rollback |
| Performance regression | Medium | Benchmark before/after |
| Missing functionality | High | Comprehensive test suite |
| Team resistance | Low | Clear benefits + training |

## 📈 Success Metrics

- Code coverage: >80% for new services
- Response time: Same or better
- Error rate: <0.1%
- Team velocity: +20% after refactor
- Maintenance time: -50%

## 🔗 Related Documents

- ADR-005: Officiële beslissing
- Epic 1 & 2: Adjusted for refactoring time
- Test Strategy: Updated voor nieuwe architectuur

---
*Start: Week 1*  
*Completion: Week 4*  
*Owner: Backend Team*