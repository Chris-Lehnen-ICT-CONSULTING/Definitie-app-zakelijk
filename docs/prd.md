# DefinitieAgent Brownfield Enhancement PRD

## Intro Project Analysis and Context

### Analysis Source
Document-project output available at: `docs/architectuur/V2_AI_SERVICE_MIGRATIE_BROWNFIELD.md`

### Current Project State  
DefinitieAgent is een juridische definitie generatie service met een hybride architectuur:
- **V1 Orchestrator**: Monolithische sync implementatie (490+ regels, productie-klaar)
- **V2 Orchestrator**: 11-fase gestructureerde async flow met **legacy fallbacks**
- **AsyncGPTClient**: Volledig geïmplementeerde async OpenAI wrapper (rate limiting, caching, retries)
- **AI Service**: Sync service laag met moderne interface maar geen async ondersteuning

### Available Documentation Analysis
Document-project analysis available - using existing technical documentation:
- ✅ Tech Stack Documentatie 
- ✅ Source Tree/Architectuur
- ✅ API Documentatie  
- ✅ Externe API Documentatie
- ✅ Technische Schuld Documentatie

### Enhancement Scope Definition

**Enhancement Type**: ☑️ Integratie met Nieuwe Systemen (AsyncGPTClient → V2 Orchestrator)

**Enhancement Description**: 
Implementatie van AIServiceV2 om de legacy fallback mechanismen in V2 orchestrator te vervangen door native async AI calls via bestaande AsyncGPTClient infrastructuur.

**Impact Assessment**: ☑️ Gemiddelde Impact (enkele bestaande code wijzigingen)
- Nieuwe AIServiceV2 klasse toevoegen
- V2 orchestrator legacy fallback vervangen  
- Interface definitie toevoegen aan interfaces.py
- V1 orchestrator blijft ongewijzigd

### Goals and Background Context

**Goals**:
• Elimineer legacy sync fallbacks in V2 orchestrator
• Integreer bestaande AsyncGPTClient in service laag
• Behoud 100% backward compatibility met V1 flows
• Realiseer 3-5x performance verbetering voor batch operaties

**Background Context**:
De V2 orchestrator is gebouwd voor async AI verwerking maar valt terug op sync legacy calls vanwege ontbrekende AIServiceInterface implementatie. AsyncGPTClient bestaat al volledig met rate limiting, caching en retry logic, maar wordt niet gebruikt door de orchestrator laag. Deze migratie combineert bestaande technische componenten zonder nieuwe external dependencies.

**Change Log**:
| Wijziging | Datum | Versie | Beschrijving | Auteur |
|-----------|-------|--------|--------------|---------|
| Initial PRD | 2025-08-28 | 1.0 | V2 AI Service migratie requirements | PM John |

## Requirements

### Functionele Requirements

**FR1**: De V2 orchestrator moet native async AI calls kunnen maken via AIServiceV2 zonder legacy fallbacks

**FR2**: AIServiceV2 moet AsyncGPTClient hergebruiken voor rate limiting, caching, en retry logic

**FR3**: AIServiceInterface moet gedefinieerd worden in interfaces.py met async en batch methoden

**FR4**: **[PRE-MORTEM]** V2 orchestrator moet automatisch terugvallen naar V1 legacy calls als AIServiceV2 faalt

**FR5**: AIServiceV2 moet sync wrapper methoden bieden voor V1 orchestrator backward compatibility

### Niet-Functionele Requirements

**NFR1**: AIServiceV2 moet 3-5x performance verbetering leveren voor batch operaties vergeleken met legacy sync calls

**NFR2**: AIServiceV2 implementatie mag geen breaking changes veroorzaken voor bestaande V1 orchestrator flows

**NFR3**: **[PRE-MORTEM]** AsyncGPTClient rate limiter moet thread-safe zijn onder concurrent load (min 50 requests/sec)

**NFR4**: **[PRE-MORTEM]** AIServiceV2 moet gebruik maken van dezelfde cache keys als legacy AI service voor consistency

**NFR5**: **[PRE-MORTEM]** V2 orchestrator met AIServiceV2 moet minimaal gelijke performance hebben als V1 voor single requests

**NFR6**: **[PRE-MORTEM]** AIServiceV2 token counting moet binnen 10% accuraatheid zijn van werkelijke OpenAI response usage

### Compatibiliteit Requirements

**CR1**: AIServiceV2 moet implementeren van AIServiceInterface voor type safety in V2 orchestrator

**CR2**: Database schema compatibility - geen database wijzigingen vereist voor migratie

**CR3**: UI/UX consistency - eindgebruiker ervaart geen verschil tussen V1 en V2 orchestrator responses

**CR4**: Integration compatibility - bestaande API endpoints blijven ongewijzigd functioneren

**CR5**: **[PRE-MORTEM]** AIServiceV2 sync wrapper mag geen impact hebben op bestaande V1 orchestrator performance (max 5% overhead)

## Technische Constraints en Integratie Requirements

### Bestaande Technology Stack

**Talen**: Python 3.x  
**Frameworks**: FastAPI, AsyncIO  
**Database**: SQLite (definitie opslag)  
**Infrastructuur**: Service container architectuur met dependency injection  
**Externe Dependencies**: OpenAI API via AsyncGPTClient, bestaande cache systeem

### Integratie Benadering

**Database Integratie Strategie**: Geen database wijzigingen - AIServiceV2 gebruikt bestaande cache tabellen en configuratie

**API Integratie Strategie**: AIServiceV2 wordt geïnjecteerd via service container, V2 orchestrator krijgt AIServiceInterface i.p.v. legacy fallback

**Frontend Integratie Strategie**: Transparant - eindgebruiker ziet geen verschil tussen V1/V2 orchestrator responses

**Testing Integratie Strategie**: Uitbreiding bestaande test suite met async AI service tests, V1/V2 compatibility tests

### Code Organisatie en Standards

**File Structure Benadering**: Nieuwe AIServiceV2 in `src/services/ai_service_v2.py`, interface toevoegen aan `src/services/interfaces.py`

**Naming Conventions**: Volgen bestaande patterns - AIServiceV2, AsyncAIService, generate_definition_async()

**Coding Standards**: Consistente error handling met bestaande AIServiceError, async/await patterns zoals AsyncGPTClient

**Documentatie Standards**: Docstrings met type hints, README updates voor nieuwe V2 configuratie

### Deployment en Operations

**Build Process Integratie**: Geen wijzigingen - AIServiceV2 wordt geimporteerd zoals bestaande services

**Deployment Strategie**: Feature flag via USE_V2_AI_SERVICE environment variable, gradual rollout mogelijk

**Monitoring en Logging**: Hergebruik bestaande logging patterns, uitbreiding met async performance metrics

**Configuration Management**: Centraal via config_manager zoals bestaande services, AsyncGPTClient configuratie integratie

### Risico Beoordeling en Mitigatie

**Technische Risico's**: Thread safety issues in rate limiter, async/sync cache inconsistency, nested event loop problemen in sync wrapper

**Integratie Risico's**: V1 orchestrator performance degradatie, cache coherentie tussen legacy en nieuwe service, error handling verschillen

**Deployment Risico's**: Feature flag failures, gradual rollout complexiteit, rollback naar legacy fallbacks

**Mitigatie Strategieën**: Comprehensive async testing, V1/V2 compatibility test suite, performance benchmarking, graceful degradation mechanismen

## Epic en Story Structuur

### Epic Benadering

**Epic Structure Beslissing**: Enkele comprehensive epic met rationale - De V2 AI Service migratie vereist gecoördineerde wijzigingen over meerdere service lagen (interfaces, implementatie, container wiring) die samen één coherente feature leveren. Multiple epics zouden onnodige complexiteit toevoegen voor wat essentieel een integratie taak is.

## Epic 1: V2 AI Service Migratie - Native Async Implementatie

**Epic Goal**: Vervang legacy fallback mechanismen in V2 orchestrator door native async AI calls via AIServiceV2 gebaseerd op bestaande AsyncGPTClient infrastructuur

**Integratie Requirements**: Behoud volledige backward compatibility met V1 orchestrator, hergebruik bestaande AsyncGPTClient functionaliteit, implementeer graceful degradation voor production stability

### Story 1.1: AIServiceInterface Definitie

Als een **ontwikkelaar**,  
Wil ik **een gedefinieerde AIServiceInterface in interfaces.py**,  
Zodat **V2 orchestrator type-safe async AI calls kan maken**.

#### Acceptance Criteria
1. AIServiceInterface gedefinieerd met async generate_definition() methode
2. Interface bevat batch_generate() methode voor parallelle verwerking  
3. Type hints consistent met bestaande service interfaces
4. Interface ondersteunt optionele parameters (model, temperature, max_tokens)

#### Integratie Verificatie
**IV1**: Bestaande import statements in V2 orchestrator blijven werken zonder wijzigingen
**IV2**: IDE type checking rapporteert geen errors voor AIServiceInterface usage  
**IV3**: Bestaande services kunnen interface implementeren zonder breaking changes

### Story 1.2: AIServiceV2 Core Implementatie

Als een **V2 orchestrator**,  
Wil ik **een native async AI service die AsyncGPTClient hergebruikt**,  
Zodat **ik echte async AI calls kan maken zonder legacy fallbacks**.

#### Acceptance Criteria
1. AIServiceV2 implementeert AIServiceInterface volledig
2. Hergebruik AsyncGPTClient voor rate limiting, retries en caching
3. Structured response objecten met tokens, model, metadata
4. Error handling consistent met bestaande service patterns

#### Integratie Verificatie  
**IV1**: AsyncGPTClient rate limiter werkt correct onder concurrent requests
**IV2**: Cache integratie gebruikt dezelfde keys als legacy AI service
**IV3**: Performance voor single requests minimaal gelijk aan legacy service

### Story 1.3: V1 Backward Compatibility Wrapper

Als een **V1 orchestrator gebruiker**,  
Wil ik **dat mijn bestaande sync calls blijven werken**,  
Zodat **er geen breaking changes zijn tijdens de migratie**.

#### Acceptance Criteria
1. AIServiceV2 heeft sync wrapper methoden voor V1 compatibility
2. Sync wrapper gebruikt thread executor voor async calls
3. Response formats identiek aan legacy AI service
4. Error types en messages consistent met legacy implementatie

#### Integratie Verificatie
**IV1**: V1 orchestrator tests slagen zonder wijzigingen
**IV2**: Performance overhead sync wrapper < 5% vergeleken met legacy
**IV3**: Memory usage sync wrapper acceptabel voor production load

### Story 1.4: Service Container Integratie 

Als een **service container**,  
Wil ik **AIServiceV2 kunnen injecteren in V2 orchestrator**,  
Zodat **de legacy fallback vervangen wordt door native implementation**.

#### Acceptance Criteria
1. Container factory methode ai_service_v2() toegevoegd
2. V2 orchestrator krijgt AIServiceV2 i.p.v. None bij USE_V2_AI_SERVICE=true
3. Feature flag controleert welke AI service wordt geïnjecteerd
4. Graceful degradation naar legacy bij AIServiceV2 failures

#### Integratie Verificatie
**IV1**: Bestaande container tests blijven slagen 
**IV2**: V1 orchestrator injection ongewijzigd bij feature flag disabled
**IV3**: V2 orchestrator startup succesvol met nieuwe AI service injection

### Story 1.5: Testing en Validatie Suite

Als een **QA engineer**,  
Wil ik **comprehensive tests voor de V2 AI service migratie**,  
Zodat **production stability gegarandeerd is**.

#### Acceptance Criteria
1. Unit tests voor AIServiceV2 async behavior en error handling
2. Integration tests V2 orchestrator met AIServiceV2
3. V1/V2 compatibility test suite voor regression prevention
4. Performance benchmarks async vs sync voor verschillende request patterns

#### Integratie Verificatie
**IV1**: Alle bestaande tests blijven slagen na migratie
**IV2**: Performance benchmarks tonen verwachte verbetering voor batch operations
**IV3**: Error scenario tests valideren graceful degradation mechanismen