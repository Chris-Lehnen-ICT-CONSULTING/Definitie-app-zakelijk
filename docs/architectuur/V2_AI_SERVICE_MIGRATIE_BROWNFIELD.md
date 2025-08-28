# Brownfield Architectuur: V2 AI Service Migratie voor DefinitieAgent

## 1. Executive Summary

Dit document beschrijft de **werkelijke** staat van de AI service architectuur in DefinitieAgent en definieert de migratiestrategie van V1 naar V2 orchestrator met async AI service ondersteuning. Het document richt zich specifiek op het oplossen van de legacy fallback mechanismen in de V2 orchestrator die momenteel gebruik maken van synchrone AI calls.

### 1.1 Kern Bevindingen

- **V2 orchestrator bestaat maar gebruikt legacy fallbacks** voor AI service calls
- **AsyncGPTClient is volledig geïmplementeerd** in `src/utils/async_api.py` maar niet geïntegreerd
- **AI service architectuur is gesplitst** tussen moderne service laag en legacy functies
- **Significant technische schuld** in orchestrator integraties met workarounds

### 1.2 Migratie Doelstelling

Implementatie van `AIServiceV2` om de V2 orchestrator's legacy fallback te vervangen door native async AI calls met behulp van bestaande `AsyncGPTClient` infrastructuur.

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
    async def generate_definition(self, prompt: str, **kwargs) -> str:
        pass
```

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

#### 3.2.2 Sync Cache in Async Context
```python
# AsyncGPTClient gebruikt sync cache:
from utils.cache import _cache
cached_result = _cache.get(cache_key)  # Sync call in async method
```

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

### 4.2 Integratie Uitdagingen

#### 4.2.1 Cache Integratie
- AsyncGPTClient gebruikt sync cache calls
- AI Service heeft eigen caching decorator
- **Oplossing:** Unified async caching strategie

#### 4.2.2 Configuration Management
- AsyncGPTClient: eigen RateLimitConfig
- AI Service: gebruikt config_manager
- **Oplossing:** Centralize in config_manager

#### 4.2.3 Error Handling Harmonisatie
- AsyncGPTClient: OpenAI specifieke errors
- AI Service: AIServiceError wrapper
- **Oplossing:** Consistent error taxonomy

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
            tokens_used=self._estimate_tokens(response_text),
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

### 5.3 Backwards Compatibility

#### 5.3.1 V1 Orchestrator Ondersteuning
```python
# AIServiceV2 moet ook sync interface ondersteunen:
class AIServiceV2(AIServiceInterface):
    def generate_definition_sync(self, prompt: str, **kwargs) -> str:
        """Sync wrapper voor V1 orchestrator compatibility."""
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Als er al een loop draait, gebruik thread executor
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(self._run_async_in_thread, prompt, **kwargs)
                return future.result()
        else:
            # Normale async execution
            return loop.run_until_complete(self.generate_definition(prompt, **kwargs))
```

## 6. Implementatie Roadmap

### 6.1 Fase 1: Interface Standaardisatie (1-2 dagen)
1. **AIServiceInterface definitie** toevoegen aan `interfaces.py`
2. **Bestaande AI Service** aanpassen om interface te implementeren
3. **Type checking** repareren in V2 orchestrator

### 6.2 Fase 2: AIServiceV2 Development (3-5 dagen)
1. **AsyncGPTClient integratie** in nieuwe AIServiceV2 klasse
2. **Unified caching strategy** implementeren
3. **Error handling harmonisatie** tussen services
4. **Configuration centralization** via config_manager

### 6.3 Fase 3: V2 Orchestrator Integratie (2-3 dagen)
1. **Legacy fallback vervanging** door native AIServiceV2
2. **Async pipeline testing** en performance validatie
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
- **Error handling:** Consistent error taxonomy over alle services

### 7.3 Compatibility Impact
- **V1 orchestrator:** Geen breaking changes via sync wrapper methods
- **Legacy functions:** `stuur_prompt_naar_gpt()` blijft werken via adapter
- **Cache system:** Gradual migration naar async cache zonder data loss

## 8. Conclusie

De V2 AI Service migratie is **technisch haalbaar** met minimale risico's door:

1. **AsyncGPTClient is volledig operational** en production-ready
2. **V2 orchestrator architectuur** is ontworpen voor async AI services
3. **Interface contracts** zijn gedefinieerd maar nog niet geïmplementeerd
4. **Backwards compatibility** kan gegarandeerd worden via adapter patterns

### 8.1 Prioriteit Acties

1. **HOOG:** Implementeer AIServiceInterface in interfaces.py
2. **HOOG:** Creëer AIServiceV2 met AsyncGPTClient integratie  
3. **MEDIUM:** Vervang legacy fallbacks in V2 orchestrator
4. **LAAG:** Gradual deprecation van legacy compatibility layers

### 8.2 Verwachte Resultaten

- **Native async AI calls** in V2 orchestrator zonder legacy fallbacks
- **3-5x performance improvement** voor batch definition generation
- **Unified AI service architecture** met consistent error handling
- **Future-proof** basis voor AI service uitbreidingen

---

*Document gegenereerd op: 2025-08-28*  
*Brownfield analyse van: DefinitieAgent V2 AI Service Migratie*  
*Auteur: AI Architecture Analysis*