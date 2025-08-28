# V2 AI Service Migratie - Technische Analyse

**Datum:** 28 augustus 2025
**Status:** Conceptanalyse
**Auteur:** AI Architectuur Specialist

## 1. Huidige Situatie Analyse

### 1.1 V1 Orchestrator Architectuur

De huidige V1 orchestrator gebruikt een **synchrone AI service** via de `AIService` klasse in `src/services/ai_service.py`:

```python
class AIService:
    def generate(self, request: AIRequest) -> AIResponse
    def generate_definition(self, prompt: str, ...) -> str
```

**Kernkenmerken V1:**
- Synchrone API calls via OpenAI client
- Ingebouwde caching via `@cached` decorator
- Legacy compatibility via `stuur_prompt_naar_gpt()`
- Model-specifieke parameter handling (GPT-5 vs GPT-4.1)
- Centrale configuratie integratie

### 1.2 V2 Orchestrator Architectuur

De V2 orchestrator (`definition_orchestrator_v2.py`) verwacht een **asynchrone AI service** interface:

```python
# Regel 81: Legacy fallback wordt gebruikt
self.ai_service = ai_service or self._get_legacy_ai_service()

# Regel 202: Async aanroep verwacht
generation_result = await self.ai_service.generate_definition(
    prompt=...,
    temperature=...,
    max_tokens=...,
    model=...
)
```

**V2 Verwachtingen:**
- Async/await pattern voor alle AI calls
- `AIServiceInterface` als formele interface (nog niet gedefinieerd)
- Integratie met monitoring service
- Feedback loop ondersteuning
- Security service integratie voor PII redactie

### 1.3 Bestaande Async Infrastructuur

Er bestaat al een `AsyncGPTClient` in `src/utils/async_api.py`:

```python
class AsyncGPTClient:
    async def chat_completion(self, prompt: str, ...) -> str
    async def batch_completion(self, prompts: list[str], ...) -> list[str]
```

**Kenmerken AsyncGPTClient:**
- Rate limiting met `AsyncRateLimiter`
- Exponential backoff retry logic
- Session statistics tracking
- Batch processing capabilities
- Caching integratie (sync cache wordt hergebruikt)

## 2. V2 Vereisten Analyse

### 2.1 Interface Vereisten

De V2 orchestrator verwacht de volgende interface (afgeleid uit gebruik):

```python
class AIServiceInterface:
    async def generate_definition(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        model: str | None
    ) -> GenerationResult
```

Waarbij `GenerationResult` minimaal moet bevatten:
- `text`: De gegenereerde definitie tekst
- `model`: Het gebruikte model
- `tokens_used`: Aantal gebruikte tokens

### 2.2 Niet-Functionele Vereisten

1. **Asynchrone Processing**
   - Alle calls moeten async/await ondersteunen
   - Geen blocking I/O operaties
   - Concurrent request handling

2. **Observability**
   - Integratie met `MonitoringServiceInterface`
   - Tracking van generation_id door de hele flow
   - Performance metrics (duration, token usage)

3. **Resilience**
   - Retry logic met backoff
   - Rate limiting compliance
   - Graceful degradation bij failures

4. **Security**
   - PII redactie ondersteuning via `SecurityServiceInterface`
   - Audit trail voor compliance

## 3. Hiaat Analyse (Gap Analysis)

### 3.1 Ontbrekende Componenten

1. **AIServiceInterface Definitie**
   - Interface bestaat niet in `interfaces.py`
   - Moet worden toegevoegd voor type safety

2. **GenerationResult Type**
   - Niet gedefinieerd in interfaces
   - V2 orchestrator gebruikt ad-hoc attributen

3. **Async Wrapper voor AIService**
   - Huidige AIService is volledig synchroon
   - `generate_async()` is slechts een placeholder

4. **Monitoring Integratie**
   - Geen koppeling tussen AI service en monitoring
   - Generation ID tracking ontbreekt

### 3.2 Integratie Hiaten

1. **Cache Synchronisatie**
   - AsyncGPTClient gebruikt sync cache
   - Potentiële thread safety issues

2. **Configuration Mismatch**
   - V1 gebruikt centrale config via `config_manager`
   - AsyncGPTClient heeft eigen `RateLimitConfig`

3. **Error Handling Inconsistentie**
   - V1 gooit `AIServiceError`
   - AsyncGPTClient gooit `OpenAIError`

## 4. Technische Beperkingen

### 4.1 Performance Beperkingen

1. **Sync Cache in Async Context**
   ```python
   # Probleem in async_api.py regel 139-145
   from utils.cache import _cache
   cached_result = _cache.get(cache_key)  # Blocking operation
   ```

2. **Legacy Adapter Overhead**
   - V2 maakt mock response objecten (regel 556-570)
   - Extra memory allocatie en processing

### 4.2 Architectuur Beperkingen

1. **Tight Coupling met OpenAI**
   - Directe OpenAI client dependencies
   - Moeilijk om andere AI providers toe te voegen

2. **Monolithische AIService**
   - Generate, caching, en config in één klasse
   - Lastig te testen en uit te breiden

## 5. Integratiepunten

### 5.1 Primaire Integratiepunten

1. **Container Service (container.py)**
   - Regel 81: AI service injection in V2 orchestrator
   - Regel 531-575: Legacy adapter implementatie

2. **V2 Orchestrator**
   - Regel 202-223: AI generation call
   - Regel 312-325: Metadata verzameling

3. **Prompt Service V2**
   - Genereert prompts voor AI service
   - Al werkend met ontologische categorieën

### 5.2 Secundaire Integratiepunten

1. **Monitoring Service**
   - Track AI calls voor performance monitoring
   - Correlatie met generation_id

2. **Security Service**
   - Pre-processing van prompts voor PII redactie
   - Post-processing van responses

3. **Feedback Engine**
   - Verzamel AI performance data
   - Verbeter toekomstige prompts

## 6. Risico Beoordeling

### 6.1 Hoog Risico

1. **Data Inconsistentie**
   - **Risico:** Sync/async cache conflicts
   - **Impact:** Corrupte cache data, performance degradatie
   - **Mitigatie:** Implementeer async-safe caching

2. **Performance Degradatie**
   - **Risico:** Inefficiënte async implementatie
   - **Impact:** Slechtere response times dan V1
   - **Mitigatie:** Benchmark en profile voor optimalisatie

### 6.2 Medium Risico

1. **Backward Compatibility**
   - **Risico:** V1 services breken bij V2 migratie
   - **Impact:** Bestaande functionaliteit faalt
   - **Mitigatie:** Uitgebreide adapter testing

2. **Rate Limit Violations**
   - **Risico:** Dubbele rate limiting (V1 + AsyncGPTClient)
   - **Impact:** Onnodige throttling
   - **Mitigatie:** Centrale rate limit configuratie

### 6.3 Laag Risico

1. **Monitoring Gaps**
   - **Risico:** Incomplete observability
   - **Impact:** Moeilijker debugging
   - **Mitigatie:** Incrementele monitoring uitrol

2. **Configuration Drift**
   - **Risico:** V1/V2 config verschillen
   - **Impact:** Onverwacht gedrag
   - **Mitigatie:** Configuratie validatie tools

## Aanbevelingen

### Korte Termijn (Sprint 1-2)
1. Definieer `AIServiceInterface` in `interfaces.py`
2. Implementeer async wrapper rond bestaande `AIService`
3. Voeg generation_id tracking toe

### Middellange Termijn (Sprint 3-4)
1. Migreer naar volledig async cache systeem
2. Integreer met monitoring service
3. Implementeer security pre/post processing

### Lange Termijn (Sprint 5+)
1. Refactor naar provider-agnostic AI interface
2. Implementeer advanced retry strategies
3. Voeg multi-model ensemble support toe
