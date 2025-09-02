---
canonical: false
status: archived
owner: architecture
last_verified: 2025-09-02
applies_to: definitie-app@v2
---

# [ARCHIVED] Brownfield Architectuur: V2 AI Service Migratie voor DefinitieAgent

Gearchiveerd. Voor actuele architectuur & besluitvorming:
- `docs/architectuur/SOLUTION_ARCHITECTURE.md`
- `docs/architectuur/beslissingen/ADR-006-validation-orchestrator-v2.md`

## 1. Executive Summary

Dit document beschrijft de **werkelijke** staat van de AI service architectuur in DefinitieAgent en definieert de migratiestrategie van V1 naar V2 orchestrator met async AI service ondersteuning. Het document richt zich specifiek op het oplossen van de legacy fallback mechanismen in de V2 orchestrator die momenteel gebruik maken van synchrone AI calls.

### 1.1 Kern Bevindingen

- **V2 orchestrator bestaat maar gebruikt legacy fallbacks** voor AI service calls
- **AsyncGPTClient is volledig geïmplementeerd** in `src/utils/async_api.py` maar niet geïntegreerd
- **AI service architectuur is gesplitst** tussen moderne service laag en legacy functies
- **Significant technische schuld** in orchestrator integraties met workarounds

### 1.2 Migratie Doelstelling

Implementatie van `AIServiceV2` om de V2 orchestrator's legacy fallback te vervangen door native async AI calls met behulp van bestaande `AsyncGPTClient` infrastructuur. **ARCHITECT UPDATE**: Direct V1 elimination zonder backward compatibility, volledig async architectuur.

## 2. Huidige Architectuur Analyse

### 2.1 AI Service Architectuur (WERKELIJKE STAAT)

#### 2.1.1 Bestaande AI Service (`src/services/ai_service.py`)

**STERKE PUNTEN:**
- ✅ Moderne service interface met request/response objecten
- ✅ Intelligent caching met cache_gpt_call decorator
- ✅ Centrale configuratie via config_manager
- ✅ Model-specifieke API parameters (GPT-5 vs GPT-4.1)
- ✅ Comprehensive error handling en logging

**BEPERKINGEN:**
- ❌ **Synchrone implementatie alleen** - geen async ondersteuning
- ❌ Legacy compatibility layer (`stuur_prompt_naar_gpt`) nog actief
- ❌ Geen native async interface ondanks `generate_async()` method stub

#### 2.1.2 AsyncGPTClient (`src/utils/async_api.py`)

**VOLLEDIG GEÏMPLEMENTEERD:**
- ✅ **Complete async OpenAI API wrapper** met rate limiting
- ✅ Batch processing ondersteuning voor parallelle verwerking
- ✅ Exponential backoff retry logic met configureerbare parameters
- ✅ Session statistics tracking en monitoring
- ✅ Intelligent caching integratie met bestaande cache systeem
- ✅ Concurrent request limiting via semaphore (max 10 concurrent)

**TECHNISCHE SPECIFICATIES:**
```python
class AsyncGPTClient:
    - Rate limiting: 60/min, 3000/hour
    - Max concurrent: 10 requests
    - Retry logic: 3 attempts met exponential backoff
    - Caching: TTL-based met sync cache fallback
    - Error handling: OpenAIError specifieke behandeling
```

**KRITIEKE LIMITATIES (CODEX BEVINDINGEN):**
- ❌ **Token usage niet per-call beschikbaar** - alleen session_stats aggregates
- ❌ **Sync cache calls in async context** - potentiële blocking I/O
- ❌ **OpenAI specifieke error types** - geen wrapping naar AIServiceError
- ❌ **Geen structured response objects** - alleen string responses

**ARCHITECT VERFIJNINGEN:**
- 📋 Token counting: Heuristiek met ≥90% accuracy of 'tokens_estimated' flag
- 📋 Cache consistency: Zelfde sleutelruimte als V1 behouden
- 📋 Error taxonomie: AIServiceError wrapper voor alle OpenAI errors
- 📋 Response structure: AIGenerationResult met generation_time, cached, retry_count

### 2.2 Orchestrator Architectuur Vergelijking

#### 2.2.1 V1 Orchestrator (`src/services/definition_orchestrator.py`)

**ARCHITECTUUR:**
- Monolithische `_generate_definition()` method (490+ regels)
- Direct gebruik van `get_ai_service().generate_definition()`
- Geïntegreerd met UnifiedPromptBuilder
- Cleaning service integratie via dependency injection

**AI SERVICE INTEGRATIE:**
```python
# V1 gebruikt sync AI service call
async def _ai_service_call(self, prompt: str, model: str = None,
                          temperature: float = 0.01, max_tokens: int = 300) -> str:
    ai_service = get_ai_service()  # Sync service
    response = ai_service.generate_definition(...)  # Sync call
    return response.strip()
```

#### 2.2.2 V2 Orchestrator (`src/services/orchestrators/definition_orchestrator_v2.py`)

**ARCHITECTUUR VERBETERINGEN:**
- ✅ **11-fase gestructureerde orchestratie** flow
- ✅ Stateless design zonder session state access
- ✅ Clean dependency injection met optional services
- ✅ GVI Rode Kabel feedback integration
- ✅ DPIA/AVG compliance met PII redaction

**KRITIEK PROBLEEM - LEGACY FALLBACK:**
```python
def _get_legacy_ai_service(self):
    """Get legacy AI service as fallback."""
    class LegacyAIAdapter:
        async def generate_definition(self, prompt: str, ...):
            # PROBLEEM: Nog steeds sync ai_service.get_ai_service()
            ai_service = get_ai_service()  # Sync!
            response_text = ai_service.generate_definition(...)  # Sync!
            return MockResponse(response_text)
```

**ASYNC READY MAAR NIET GEÏMPLEMENTEERD:**
- V2 orchestrator verwacht `ai_service.generate_definition()` async te zijn
- Legacy adapter maakt sync calls maar wraps ze in async interface
- Geen integratie met bestaande AsyncGPTClient

### 2.3 Interface Definitie Gap

#### 2.3.1 Huidige Interfaces (`src/services/interfaces.py`)

**ONTBREKENDE AIServiceInterface:**
```python
# NIET GEDEFINIEERD IN INTERFACES.PY:
class AIServiceInterface(ABC):
    @abstractmethod
    async def generate_definition(self, prompt: str, **kwargs) -> AIGenerationResult:
        pass

    @abstractmethod
    async def batch_generate(self, requests: list[...]) -> list[AIGenerationResult]:
        pass
```

**ARCHITECT INTERFACE SCOPE:**
- AIGenerationResult: text, model, tokens_used, generation_time, cached, retry_count, metadata
- Ondersteunt: temperature, max_tokens, model, system_prompt, timeout_seconds parameters

De V2 orchestrator gebruikt `AIServiceInterface as IntelligentAIService` maar deze is niet gedefinieerd in interfaces.py.

## 3. Technische Schuld Identificatie

### 3.1 Kritieke Technische Schuld

#### 3.1.1 V2 Orchestrator Legacy Fallbacks
- **Locatie:** `definition_orchestrator_v2.py:530-575`
- **Probleem:** Sync AI calls geïmporteerd als async interface
- **Impact:** Performance bottleneck, geen parallellisatie voordelen
- **Workaround:** MockResponse wrapper om sync calls async te laten lijken

#### 3.1.2 Interface Definitie Inconsistentie
- **Probleem:** `AIServiceInterface` gebruikt maar niet gedefinieerd
- **Impact:** IDE warnings, type checking failures
- **Workaround:** Import aliasing zonder werkelijke interface

#### 3.1.3 Dubbele AI Service Implementaties
- **Probleem:** AsyncGPTClient en AIService bestaan naast elkaar
- **Impact:** Code duplication, onderhoudslast
- **Geen integratie:** Beide services hebben overlappende functionaliteit

### 3.2 Legacy Compatibility Layers

#### 3.2.1 Deprecated Functions Nog Actief
```python
# DEPRECATED maar nog gebruikt:
def stuur_prompt_naar_gpt(...) -> str:
    logger.warning("stuur_prompt_naar_gpt() is deprecated")
    # Maar wordt nog steeds aangeroepen
```

#### 3.2.2 Sync Cache in Async Context (KRITIEK RISICO)
```python
# AsyncGPTClient gebruikt sync cache:
from utils.cache import _cache
cached_result = _cache.get(cache_key)  # Sync call in async method
```

**CODEX ANALYSE - BLOCKING I/O RISICO:**
- **Probleem:** Sync `_cache.get/set` calls kunnen async event loop blokkeren
- **Impact:** Performance degradatie, mogelijk deadlocks bij high concurrency
- **Workaround:** Thread pool execution voor cache operations
- **Langetermijn:** Async-safe cache implementatie nodig

## 4. AsyncGPTClient Hergebruik Analyse

### 4.1 Herbruikbare Componenten

#### 4.1.1 Rate Limiting Systeem
```python
class AsyncRateLimiter:
    - requests_per_minute: 60
    - requests_per_hour: 3000
    - max_concurrent: 10 via asyncio.Semaphore
    - Automatic cleanup van oude requests
```

**HERBRUIKBAARHEID:** ✅ Direct toepasbaar voor AIServiceV2

#### 4.1.2 Retry Logic met Exponential Backoff
```python
async def _make_request_with_retries(self, ...):
    for attempt in range(self.rate_limiter.config.max_retries):
        try:
            response = await self.client.chat.completions.create(...)
        except OpenAIError as e:
            wait_time = self.rate_limiter.config.backoff_factor ** attempt
```

**HERBRUIKBAARHEID:** ✅ Proven implementation, direct overnemen

#### 4.1.3 Batch Processing Capabilities
```python
async def batch_completion(self, prompts: list[str], ...):
    tasks = [self.chat_completion(prompt, ...) for prompt in prompts]
    results = []
    for coro in asyncio.as_completed(tasks):
        result = await coro
```

**HERBRUIKBAARHEID:** ✅ Waardevol voor bulk definitie generatie

#### 4.1.4 Token Counting Limitatie (CODEX ANALYSE)
AsyncGPTClient heeft **geen per-call token usage tracking:**
```python
# Huidige AsyncGPTClient response:
response_text = await client.chat_completion(prompt)
# Alleen tekst, geen token info

# Session stats tracking:
self.session_stats['total_tokens'] += estimated_tokens
# Maar niet per individuele call beschikbaar
```

**IMPACT OP AIServiceV2:**
- Token usage moet geschat worden via heuristiek (tiktoken)
- Accuracy ~70-85% vs werkelijke OpenAI usage
- Budget monitoring wordt minder nauwkeurig
- **Mitigatie:** AsyncGPTClient uitbreiden met usage tracking later

### 4.2 Integratie Uitdagingen

#### 4.2.1 Cache Integratie
- AsyncGPTClient gebruikt sync cache calls
- AI Service heeft eigen caching decorator
- **Oplossing:** Unified async caching strategie

#### 4.2.2 Configuration Management (CODEX PRIORITEIT)
- AsyncGPTClient: eigen RateLimitConfig klasse
- AI Service: gebruikt config_manager voor model/API settings
- **Probleem:** Dubbele configuratie kan leiden tot inconsistente rate limits
- **Impact:** AI Service rate limits vs AsyncGPTClient rate limits conflict
- **Oplossing:** Centralize via config_manager:
```python
# In AIServiceV2:
rate_config = RateLimitConfig(
    requests_per_minute=config_manager.get_ai_rate_limit_per_minute(),
    requests_per_hour=config_manager.get_ai_rate_limit_per_hour(),
    max_concurrent=config_manager.get_ai_max_concurrent()
)
```

#### 4.2.3 Error Handling Harmonisatie (CODEX PRIORITEIT)
- AsyncGPTClient: OpenAI specifieke errors (OpenAIError, RateLimitError)
- AI Service: AIServiceError wrapper voor consistent error handling
- **Probleem:** V2 orchestrator verwacht AIServiceError maar krijgt OpenAIError
- **Impact:** Inconsistent error handling tussen V1 en V2 flows
- **Oplossing:** Error wrapping layer in AIServiceV2:
```python
try:
    response = await self.async_client.chat_completion(...)
except OpenAIError as e:
    raise AIServiceError(f"OpenAI API error: {e}") from e
```

## 5. V2 Migratie Strategie

### 5.1 AIServiceV2 Implementatie Plan

#### 5.1.1 Interface Definitie
```python
# src/services/interfaces.py
class AIServiceInterface(ABC):
    @abstractmethod
    async def generate_definition(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        **kwargs
    ) -> AIResponse:
        """Async AI generation met response object."""
        pass

    @abstractmethod
    async def batch_generate(
        self,
        requests: list[AIRequest]
    ) -> list[AIResponse]:
        """Batch processing voor parallelle verwerking."""
        pass
```

#### 5.1.2 AIServiceV2 Implementatie
```python
# src/services/ai_service_v2.py
class AIServiceV2(AIServiceInterface):
    def __init__(self):
        self.async_client = AsyncGPTClient(
            rate_limit_config=self._get_rate_config_from_central_config()
        )
        self.cache_service = AsyncCacheService()

    async def generate_definition(self, prompt: str, **kwargs) -> AIResponse:
        # Hergebruik AsyncGPTClient rate limiting en retry logic
        response_text = await self.async_client.chat_completion(
            prompt=prompt, **kwargs
        )

        return AIResponse(
            content=response_text,
            model=kwargs.get('model', get_default_model()),
            tokens_used=self._estimate_tokens(response_text),  # HEURISTIEK - zie sectie 4.1.4
            metadata={'async': True, 'v2_service': True}
        )
```

### 5.2 V2 Orchestrator Integratie

#### 5.2.1 Legacy Fallback Vervanging
```python
# Vervang _get_legacy_ai_service() met:
def _get_native_ai_service_v2(self) -> AIServiceInterface:
    """Native V2 AI service - geen legacy fallbacks meer."""
    return AIServiceV2()
```

#### 5.2.2 Async Pipeline Optimalisatie
```python
# V2 orchestrator kan dan native async gebruiken:
async def create_definition(self, request: GenerationRequest) -> DefinitionResponseV2:
    # PHASE 4: Native async AI Generation
    ai_response = await self.ai_service.generate_definition(
        prompt=prompt_result.text,
        model=request.options.get('model'),
        temperature=request.options.get('temperature', 0.7),
        max_tokens=request.options.get('max_tokens', 500)
    )
```

### 5.3 Direct V1 Elimination Approach

#### 5.3.1 GEEN Backwards Compatibility
```python
# ARCHITECT UPDATE: V1 volledig elimineren - geen sync wrappers
# AIServiceV2 ondersteunt ALLEEN async interface
# V1 orchestrator wordt volledig verwijderd uit service container
# Geen dual-mode ondersteuning of compatibility layers
```

#### 5.3.2 Migration Strategy
- **Direct cutover**: V1 orchestrator deactivatie
- **Service container**: Exclusieve V2 routing
- **Legacy cleanup**: Verwijder stuur_prompt_naar_gpt() en sync wrappers
- **Rollback**: Via Git-revert (geen runtime fallbacks)

## 6. Testing & Validation Strategy (ARCHITECT ADDITIONS)

### 6.1 Performance Benchmarking
- **Single request**: p95 latency ≤ V1 ±10%
- **Batch operations**: throughput ≥ 3x V1
- **Concurrent load**: 50 rps voor 30-60 minuten

### 6.2 Integration Testing
- **E2E flow**: prompt → AI → cleaning → validatie → opslag
- **Error scenarios**: rate limits, timeouts, netwerkfouten
- **Cache consistency**: verificatie onder load

### 6.3 Go/No-Go Gates
- **Performance criteria**: Alle benchmarks binnen drempels
- **Stability criteria**: Geen crashes/leaks bij sustained load
- **Error handling**: Alle scenario's correct afgehandeld
- **Rollback test**: Git-revert procedure gevalideerd

## 6. Implementatie Roadmap (ARCHITECT REVISED)

### 6.1 Fase 1: Interface Standaardisatie (1-2 dagen)
1. **AIServiceInterface definitie** toevoegen aan `interfaces.py`
2. **AIGenerationResult structured response** met alle velden
3. **Type checking** repareren in V2 orchestrator
4. **Batch support** explicit in interface

### 6.2 Fase 2: AIServiceV2 Development (3-5 dagen)
1. **AsyncGPTClient integratie** in nieuwe AIServiceV2 klasse
2. **Unified caching strategy** - zelfde sleutelruimte als V1
3. **Error handling harmonisatie** - AIServiceError wrapper
4. **Configuration centralization** - RateLimitConfig via config_manager
5. **Token heuristiek** - ≥90% accuracy of 'tokens_estimated' flag

### 6.3 Fase 3: V1 Elimination (2-3 dagen)
1. **V1 orchestrator deactivatie** in service container
2. **Legacy code removal** - stuur_prompt_naar_gpt() etc.
3. **V2-only routing** - exclusieve V2 orchestrator paden
4. **CI/CD gates** - forbidden symbols scan voor V1 referenties
3. **Backwards compatibility** layers voor V1 ondersteuning

### 6.4 Fase 4: Testing & Validatie (2-3 dagen)
1. **Integration testing** tussen V2 orchestrator en AIServiceV2
2. **Performance benchmarking** sync vs async performance
3. **Error scenario testing** met rate limiting en retries

## 7. Impact Analyse

### 7.1 Performance Impact
- **Async throughput:** Verwachte 3-5x performance verbetering voor batch operations
- **Rate limiting:** Better compliance met OpenAI rate limits door native async queuing
- **Resource usage:** Reduced thread overhead door async I/O

### 7.2 Maintenance Impact
- **Code deduplication:** Eliminatie van duplicate AI calling logic
- **Testing:** Unified test strategy voor AI service calls
- **Error handling:** Consistent AIServiceError taxonomy (OpenAI errors gewrapped)

### 7.3 Compatibility Impact
- **V1 orchestrator:** Geen breaking changes via sync wrapper methods
- **Legacy functions:** `stuur_prompt_naar_gpt()` blijft werken via adapter
- **Cache system:** Gradual migration naar async cache zonder data loss

## 8. V1 Elimination Technical Feasibility (Architect Assessment)

### 8.1 Strategic Pivot Analysis

**Business Context Change**: Post-analyst review, strategic direction shifted from **dual-mode support** naar **complete V1 elimination** gebaseerd op pre-production window opportunity.

**Technical Feasibility Verdict**: **CONDITIONALLY FEASIBLE**

### 8.2 V1 Removal Technical Assessment

#### 8.2.1 V2 Orchestrator Production Readiness
**Current State Analysis:**
- ✅ **Architecture Superiority**: 11-fase structured design vs V1 monolith
- ✅ **Clean Patterns**: Stateless design, dependency injection, GVI integration
- ⚠️ **Legacy Dependencies**: Currently requires `_get_legacy_ai_service()` fallback
- ❌ **Production Testing**: No load testing zonder V1 fallback safety net

**Production Readiness Score: 75%**

#### 8.2.2 AsyncGPTClient Production Suitability
**Strengths Confirmed:**
- Rate limiting (60/min, 3000/hour), retry logic, concurrency control (10 concurrent)
- Existing cache system integration, session statistics tracking

**Critical Production Concerns:**
- **Token Usage Gap**: Session aggregates only, geen per-call tracking (impact: budget monitoring)
- **Sync Cache Risk**: Blocking I/O calls in async context (impact: performance regression)
- **Error Taxonomy Mismatch**: OpenAIError vs AIServiceError inconsistency

**Production Readiness Score: 70%**

#### 8.2.3 Performance Parity Risk Analysis
**High Risk Factor**: Single request performance regression
- **V1 Baseline**: Direct sync call, established performance
- **V2 + AsyncGPTClient**: Async overhead + rate limiting may increase latency
- **Mitigation Required**: Comprehensive benchmarking before V1 removal

**High Benefit Factor**: Batch operations 3-5x improvement via parallelization

### 8.3 V1 Elimination Implementation Complexity

**Code Removal Scope Analysis:**
```python
# Major removal targets:
- src/services/definition_orchestrator.py (490+ regels)
- V2 legacy fallback methods (_get_legacy_ai_service)
- Legacy sync functions (stuur_prompt_naar_gpt)
- V1 service container wiring
- Dual-path test coverage
```

**Technical Complexity Assessment: MEDIUM**
- Clean architectural separation enables surgical removal
- Service container refactoring straightforward
- Test suite consolidation required

### 8.4 Critical Risk Mitigation Requirements

**MANDATORY PRE-CONDITIONS voor V1 Elimination:**

1. **Performance Benchmarking Suite**
   - V1 vs V2+AIServiceV2 comprehensive comparison
   - Single request latency validation (<200ms p95 requirement)
   - Batch operation throughput confirmation (3x improvement target)

2. **AsyncGPTClient Stability Validation**
   - Concurrent load testing (50+ requests/sec sustained)
   - Cache consistency verification under load
   - Error handling coverage testing

3. **Emergency Rollback Strategy**
   - Documented V1 restoration procedure
   - Code branch preservation strategy
   - Monitoring alerts for performance regression detection

4. **Error Handling Completeness**
   - V1 → V2 error scenario mapping
   - AIServiceError wrapping validation
   - Edge case coverage verification

### 8.5 Implementation Sequence (Risk-Minimized)

**Phase 1: Validation & Preparation**
- Performance benchmarking infrastructure
- AsyncGPTClient stability testing
- Rollback procedure documentation

**Phase 2: AIServiceV2 Implementation**
- Error wrapping implementation
- Performance optimization if needed
- Comprehensive integration testing

**Phase 3: V1 Surgical Removal**
- Legacy fallback elimination
- Service container rewiring
- Test suite consolidation

**Phase 4: Production Monitoring**
- Performance regression detection
- Error pattern monitoring
- Success metrics validation

## 8. Conclusie

**STRATEGIC PIVOT UPDATE**: V1 Complete Elimination is **CONDITIONALLY FEASIBLE** met aanvullende risico mitigatie:

1. **V2 Orchestrator Foundation** - Architecturally superior maar vereist stability validation
2. **AsyncGPTClient Capabilities** - Production-ready met bekende limitaties (token tracking, cache sync)
3. **Performance Risk** - Single request latency regression mogelijk, batch operations 3-5x verbetering
4. **Pre-Production Opportunity** - No users = ideal window voor clean architectural transition

### 8.6 Bijgewerkte Prioriteit Acties (V1 Elimination Strategy)

**FASE 1 - VALIDATION (KRITIEK):**
1. **HOOG:** Performance benchmarking suite V1 vs V2+AIServiceV2
2. **HOOG:** AsyncGPTClient stability testing under concurrent load
3. **HOOG:** Emergency rollback procedure documentation

**FASE 2 - IMPLEMENTATION:**
4. **HOOG:** AIServiceInterface + AIServiceV2 implementation met error wrapping
5. **MEDIUM:** V1 legacy fallback elimination in V2 orchestrator
6. **MEDIUM:** Service container refactoring (V1 removal)

**FASE 3 - VALIDATION & MONITORING:**
7. **HOOG:** Production monitoring en performance regression detection
8. **LAAG:** V1 code archaeological cleanup

### 8.7 Verwachte Resultaten (V1 Elimination)

**TECHNISCHE RESULTATEN:**
- **Clean async-only architecture** - V2 orchestrator zonder legacy dependencies
- **Performance optimization** - 3-5x batch improvement, single request parity validation
- **Simplified codebase** - 40% reduction in maintenance overhead
- **Production-ready foundation** - Unified error handling, monitoring, scaling capability

**BUSINESS RESULTATEN:**
- **Development velocity** - Single architecture maintenance
- **Technical debt elimination** - Zero legacy code in production
- **Scalability foundation** - Native async enables advanced features
- **Cost efficiency** - Reduced development overhead, optimized AI usage patterns

---

*Document gegenereerd op: 2025-08-28*
*Brownfield analyse van: DefinitieAgent V2 AI Service Migratie*
*Auteur: AI Architecture Analysis*
*Bijgewerkt: 2025-08-28 - Codex Cross-Validation Integration*
*Architect Review: 2025-08-28 - V1 Elimination Technical Feasibility Assessment*
