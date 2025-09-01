# V2 Orchestrator Migration Plan

## Executive Summary

Deze analyse toont aan wat er nodig is om volledig over te schakelen van V1 (DefinitionOrchestrator) naar V2 (DefinitionOrchestratorV2) en V1 uit te kunnen zetten.

## Current State

### V1 (DefinitionOrchestrator)
- **Status**: Productie-ready, stabiel
- **Architectuur**: Monolithisch met service dependencies
- **Features**: Volledig geïmplementeerd

### V2 (DefinitionOrchestratorV2)
- **Status**: Partial implementation, test-ready
- **Architectuur**: 11-fase gestructureerde flow
- **Features**: ~50% geïmplementeerd (ValidationOrchestratorV2 core ready)

## Ontbrekende V2 Componenten

### 1. Core Services (KRITISCH)

#### AIServiceInterface
```python
# Nodig: src/services/ai_service_v2.py
class AIServiceV2(AIServiceInterface):
    async def generate_definition(
        self, prompt: str, temperature: float = 0.7,
        max_tokens: int = 500, model: str = None
    ) -> AIGenerationResult
```
**Status**: Gebruikt legacy fallback
**Prioriteit**: HOOG
**Geschatte tijd**: 2-3 dagen

#### ValidationOrchestratorV2
```python
# Gerealiseerd: src/services/orchestrators/validation_orchestrator_v2.py
class ValidationOrchestratorV2(ValidationOrchestratorInterface):
    async def validate_text(text: str, context: ValidationContext) -> ValidationResult
    async def validate_definition(definition: Definition) -> ValidationResult
    async def batch_validate(items: List[Validatable]) -> List[ValidationResult]
```
**Status**: ✅ PARTIAL IMPLEMENTATION (Epic 2, Story 2.1-2.2 COMPLETE)
**Voltooid**:
- ✅ ValidationOrchestratorInterface (Story 2.1)
- ✅ Core implementation - thin orchestration layer (Story 2.2)
- ✅ Dataclass → Schema mapper (services/validation/mappers.py)
- ✅ Feature flags system met shadow/canary support
- ✅ 29 tests (contract, orchestrator, mapper)

**Nog te doen**:
- ⏳ Container wiring (Story 2.3) - DI integratie
- ⏳ Feature flag activation - VALIDATION_ORCHESTRATOR_V2
- ⏳ Integration & Migration (Story 2.4)
- ⏳ Testing & QA (Story 2.5)
- ⏳ Production rollout (Story 2.6)

#### ValidationServiceV2
```python
# Nodig: src/services/validation_service_v2.py
class ValidationServiceV2(ValidationServiceInterface):
    async def validate_definition(
        self, begrip: str, text: str,
        ontologische_categorie: str = None
    ) -> ValidationResult
```
**Status**: Gebruikt legacy validator
**Prioriteit**: MEDIUM (na ValidationOrchestrator)
**Geschatte tijd**: 3-4 dagen

### 2. Enhancement Services (BELANGRIJK)

#### EnhancementService
```python
# Nodig: src/services/enhancement_service.py
class EnhancementService(EnhancementServiceInterface):
    async def enhance_definition(
        self, text: str, violations: list,
        context: GenerationRequest
    ) -> str
```
**Status**: Niet geïmplementeerd
**Prioriteit**: MEDIUM
**Geschatte tijd**: 4-5 dagen

### 3. Security & Compliance (VEREIST)

#### SecurityService
```python
# Nodig: src/services/security_service.py
class SecurityService(SecurityServiceInterface):
    async def sanitize_request(
        self, request: GenerationRequest
    ) -> GenerationRequest

    async def redact_pii(self, text: str) -> str
```
**Status**: Niet geïmplementeerd
**Prioriteit**: HOOG (DPIA/AVG compliance)
**Geschatte tijd**: 3-4 dagen

### 4. Monitoring & Feedback (NICE-TO-HAVE)

#### MonitoringService
```python
# Nodig: src/services/monitoring_service.py
class MonitoringService(MonitoringServiceInterface):
    async def start_generation(self, generation_id: str)
    async def complete_generation(self, generation_id: str, ...)
    async def track_error(self, generation_id: str, error: str)
```
**Status**: Niet geïmplementeerd
**Prioriteit**: LOW
**Geschatte tijd**: 2-3 dagen

#### FeedbackEngine
```python
# Nodig: src/services/feedback_engine.py
class FeedbackEngine(FeedbackEngineInterface):
    async def get_feedback_for_request(
        self, begrip: str, categorie: str
    ) -> list[Feedback]

    async def process_validation_feedback(
        self, definition_id: str,
        validation_result: ValidationResult,
        original_request: GenerationRequest
    )
```
**Status**: Niet geïmplementeerd
**Prioriteit**: LOW (GVI Rode Kabel)
**Geschatte tijd**: 5-7 dagen

## Ontbrekende V1 Features in V2

### 1. update_definition() Method
**V1**: Volledig geïmplementeerd
**V2**: Placeholder
**Impact**: API compatibiliteit
**Oplossing**: Kopieer V1 logica naar V2

### 2. validate_and_save() Method
**V1**: Volledig geïmplementeerd
**V2**: Placeholder
**Impact**: Workflow compatibiliteit
**Oplossing**: Kopieer V1 logica naar V2

### 3. Voorbeelden Generatie
**V1**: Geïntegreerd in workflow
**V2**: Niet geïmplementeerd
**Impact**: Feature verlies
**Oplossing**: Integreer in fase 8 van V2 flow

## Migratie Stappenplan

### Fase 1: Core Services (Week 1-2)
1. **AIServiceV2 implementeren**
   - Async interface bouwen
   - Caching integreren
   - Error handling verbeteren

2. **ValidationServiceV2 implementeren**
   - Async validatie
   - Ontologische categorie support
   - Performance optimalisatie

3. **SecurityService implementeren**
   - PII detectie en redactie
   - Request sanitization
   - DPIA compliance checks

### Fase 2: Feature Parity (Week 3)
1. **update_definition() implementeren**
   - Kopieer V1 logica
   - Maak async
   - Test compatibiliteit

2. **validate_and_save() implementeren**
   - Kopieer V1 logica
   - Integreer met V2 flow
   - Test compatibiliteit

3. **Voorbeelden integratie**
   - Voeg toe aan fase 8
   - Cache voorbeelden
   - Test performance

### Fase 3: Enhancement (Week 4)
1. **EnhancementService bouwen**
   - AI-based text enhancement
   - Violation-specific improvements
   - Iterative enhancement loop

### Fase 4: Monitoring & Feedback (Week 5)
1. **MonitoringService implementeren**
   - Metrics collection
   - Performance tracking
   - Error tracking

2. **FeedbackEngine bouwen**
   - Feedback storage
   - Learning integration
   - GVI Rode Kabel support

### Fase 5: Testing & Cutover (Week 6)
1. **Integration Testing**
   - End-to-end tests
   - Performance benchmarks
   - Regression testing

2. **Gradual Rollout**
   - A/B testing met feature flag
   - Monitor metrics
   - Rollback plan

3. **V1 Deprecation**
   - Documenteer breaking changes
   - Update alle dependencies
   - Verwijder V1 code

## Code Wijzigingen

### 1. Container Updates
```python
# src/services/container.py
def orchestrator(self):
    # Verwijder V1 fallback
    # Alleen V2 instantiëren
    return DefinitionOrchestratorV2(
        prompt_service=self.prompt_service_v2(),
        ai_service=self.ai_service_v2(),  # NEW
        validation_service=self.validation_service_v2(),  # NEW
        enhancement_service=self.enhancement_service(),  # NEW
        security_service=self.security_service(),  # NEW
        cleaning_service=self.cleaning_service(),
        repository=self.repository(),
        monitoring=self.monitoring_service(),  # NEW
        feedback_engine=self.feedback_engine(),  # NEW
        config=self.v2_config
    )
```

### 2. ServiceFactory Updates
```python
# src/services/service_factory.py
# Verwijder legacy checks
# Direct V2 gebruiken zonder fallback
```

### 3. Interface Definitions
```python
# src/services/interfaces.py
# Voeg toe:
class AIServiceInterface(ABC):
    @abstractmethod
    async def generate_definition(...) -> AIGenerationResult

class EnhancementServiceInterface(ABC):
    @abstractmethod
    async def enhance_definition(...) -> str

# etc...
```

## Risico's en Mitigatie

### Risico 1: Breaking Changes
**Impact**: Bestaande integraties kunnen breken
**Mitigatie**:
- Maintain backward compatibility layer
- Deprecation warnings
- Migration guide

### Risico 2: Performance Degradatie
**Impact**: V2 kan langzamer zijn door extra fases
**Mitigatie**:
- Performance benchmarks
- Parallel processing waar mogelijk
- Caching strategieën

### Risico 3: Data Loss
**Impact**: Failed attempts niet opgeslagen
**Mitigatie**:
- Implement _save_failed_attempt()
- Transaction support
- Backup strategie

## Geschatte Timeline

- **Week 1-2**: Core Services (AIService, ValidationService, SecurityService)
- **Week 3**: Feature Parity (update/save methods, voorbeelden)
- **Week 4**: Enhancement Service
- **Week 5**: Monitoring & Feedback
- **Week 6**: Testing & Cutover

**Totaal: 6 weken voor volledige migratie**

## Conclusie

De migratie naar V2 vereist substantiële ontwikkeling van ontbrekende services. De grootste uitdagingen zijn:

1. **6 nieuwe services bouwen**
2. **Feature parity met V1**
3. **Backward compatibility behouden**
4. **Performance optimalisatie**

Met de juiste prioritering en gefaseerde aanpak is volledige migratie haalbaar in 6 weken.
