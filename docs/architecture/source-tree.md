# Source Tree Structure - DefinitieAgent

## Wijzigingshistorie

- 2025-08-28: AS‑IS/TO‑BE gescheiden en entry point gecorrigeerd; auto‑generated sectie toegevoegd.

## Overzicht

Dit document beschrijft de structuur van de DefinitieAgent codebase, inclusief de organisatie van modules, verantwoordelijkheden en belangrijke design beslissingen.

## Root Directory Structure

```
definitie-app/
├── .bmad-core/           # BMad method configuratie en agents
├── .github/              # GitHub Actions workflows
├── docs/                 # Projectdocumentatie
│   ├── architectuur/     # Architectuur documenten
│   ├── archief/          # Gearchiveerde documentatie
│   └── brief.md          # Project brief
├── src/                  # Source code (zie details hieronder)
├── tests/                # Test suites
├── src/main.py           # Streamlit applicatie entry point
├── pyproject.toml        # Project configuratie en dependencies
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variables template
└── README.md            # Project overview
```

## Source Code Structure (`src/`)

### AS‑IS (auto‑gegenereerd)

Onderstaande boom kan automatisch bijgewerkt worden tussen de markers door `scripts/generate_source_tree.py`.

<!-- AS-IS: BEGIN AUTO-GENERATED -->

```
src/
├── __pycache__
│   ├── __init__.cpython-313.pyc
│   ├── centrale_module_definitie_kwaliteit.cpython-313.pyc
│   ├── config_loader.cpython-313.pyc
│   └── main.cpython-313.pyc
├── ai_toetser
│   ├── __pycache__
│   ├── __init__.py
│   ├── json_validator_loader.py
│   ├── modular_toetser.py
│   └── toetser.py
├── analysis
│   ├── __pycache__
│   ├── __init__.py
│   └── toetsregels_usage_analysis.py
├── api
│   └── feature_status_api.py
├── archive
│   └── migration_scripts
├── cache
│   ├── __pycache__
│   ├── 09ce1cda1485b55decb1b3745ecd86a4.pkl
│   ├── 2ec3d84152e9893d0c847c1a8a64898b.pkl
│   ├── 3756d4afb463cc876cc2f5e113ef2875.pkl
│   ├── 3e9c995fa09f252011d4f63901c0d1bb.pkl
│   ├── 4d9bc87498b81fd8349c3283165ca757.pkl
│   ├── 646cd8e5ce9dc8405916ef5fba83047a.pkl
│   ├── 950d3e24259c33f1b326c187ec23a146.pkl
│   ├── 98274140200e784d33d6462905c13d8c.pkl
│   ├── __init__.py
│   ├── b841c923a42f591c2172d543f8139009.pkl
│   ├── bc978332231ab7318c2b4081f025628d.pkl
│   ├── d8e0cc41ecf197968bcf76f1819b74ea.pkl
│   └── metadata.json
├── config
│   ├── __pycache__
│   ├── __init__.py
│   ├── config_adapters.py
│   ├── config_loader.py
│   ├── config_manager.py
│   ├── context_wet_mapping.json
│   ├── rate_limit_config.py
│   ├── verboden_woorden.json
│   └── verboden_woorden.py
├── data
│   └── uploaded_documents
├── database
│   ├── __pycache__
│   ├── migrations
│   ├── __init__.py
│   ├── definitie_repository.py
│   ├── migrate_database.py
│   └── schema.sql
├── document_processing
│   ├── __pycache__
│   ├── __init__.py
│   ├── document_extractor.py
│   └── document_processor.py
├── domain
│   ├── __pycache__
│   ├── autoriteit
│   ├── context
│   ├── juridisch
│   ├── linguistisch
│   ├── __init__.py
│   └── ontological_categories.py
├── export
│   ├── __pycache__
│   ├── __init__.py
│   └── export_txt.py
├── exports
│   ├── __pycache__
│   └── __init__.py
├── external
│   ├── __pycache__
│   ├── __init__.py
│   └── external_source_adapter.py
├── hybrid_context
│   ├── __pycache__
│   ├── __init__.py
│   ├── context_fusion.py
│   ├── hybrid_context_engine.py
│   ├── smart_source_selector.py
│   └── test_hybrid_context.py
├── integration
│   ├── __pycache__
│   ├── __init__.py
│   └── definitie_checker.py
├── models
│   ├── __pycache__
│   └── category_models.py
├── monitoring
│   ├── __pycache__
│   ├── __init__.py
│   └── api_monitor.py
├── ontologie
│   ├── __pycache__
│   ├── __init__.py
│   └── ontological_analyzer.py
├── opschoning
│   ├── __pycache__
│   ├── __init__.py
│   ├── opschoning.py
│   ├── opschoning_enhanced.py
│   └── README.md
├── orchestration
│   ├── __pycache__
│   ├── __init__.py
│   └── definitie_agent.py
├── reports
│   ├── __pycache__
│   └── __init__.py
├── security
│   ├── __pycache__
│   ├── __init__.py
│   └── security_middleware.py
├── services
│   ├── __pycache__
│   ├── adapters
│   ├── feedback
│   ├── orchestrators
│   ├── prompts
│   ├── providers
│   ├── security
│   ├── web_lookup
│   ├── __init__.py
│   ├── ab_testing_framework.py
│   ├── ai_service_v2.py
│   ├── category_service.py
│   ├── category_state_manager.py
│   ├── cleaning_service.py
│   ├── container.py
│   ├── data_aggregation_service.py
│   ├── definition_generator_cache.py
│   ├── definition_generator_config.py
│   ├── definition_generator_context.py
│   ├── definition_generator_enhancement.py
│   ├── definition_generator_monitoring.py
│   ├── definition_generator_prompts.py
│   ├── definition_repository.py
│   ├── definition_validator.py
│   ├── duplicate_detection_service.py
│   ├── export_service.py
│   ├── interfaces.py
│   ├── modern_web_lookup_service.py
│   ├── null_repository.py
│   ├── regeneration_service.py
│   ├── service_factory.py
│   └── workflow_service.py
├── toetsregels
│   ├── __pycache__
│   ├── regels
│   ├── sets
│   ├── validators
│   ├── __init__.py
│   ├── adapter.py
│   ├── loader.py
│   ├── manager.py
│   ├── modular_loader.py
│   └── toetsregels-manager.json
├── tools
│   ├── __pycache__
│   ├── __init__.py
│   ├── definitie_manager.py
│   └── setup_database.py
├── ui
│   ├── __pycache__
│   ├── components
│   ├── services
│   ├── __init__.py
│   ├── async_progress.py
│   ├── cache_manager.py
│   ├── components.py
│   ├── components_adapter.py
│   ├── regeneration_handler.py
│   ├── session_state.py
│   └── tabbed_interface.py
├── utils
│   ├── __pycache__
│   ├── __init__.py
│   ├── async_api.py
│   ├── cache.py
│   ├── enhanced_retry.py
│   ├── exceptions.py
│   ├── integrated_resilience.py
│   ├── optimized_resilience.py
│   ├── performance_monitor.py
│   ├── resilience.py
│   ├── resilience_summary.py
│   └── smart_rate_limiter.py
├── validation
│   ├── __pycache__
│   ├── log
│   ├── __init__.py
│   ├── definitie_validator.py
│   ├── dutch_text_validator.py
│   ├── input_validator.py
│   └── sanitizer.py
├── voorbeelden
│   ├── __pycache__
│   ├── __init__.py
│   ├── async_voorbeelden.py
│   ├── cached_voorbeelden.py
│   ├── unified_voorbeelden.py
│   └── voorbeelden.py
├── web_lookup
│   └── __pycache__
├── __init__.py
├── main.py
└── test_export.json
```

<!-- AS-IS: END AUTO-GENERATED -->

### Top-Level Modules (TO‑BE)

```
src/
├── __init__.py
├── ai_toetser/          # AI validatie componenten
├── config/              # Configuratie management
├── database/            # Database layer en migrations
├── document_processing/ # Document verwerking
├── domain/              # Domain models en business logic
├── orchestration/       # Orchestratie logica
├── services/            # Core services
├── toetsregels/         # Validatie regels
├── ui/                  # Streamlit UI componenten
├── utils/               # Utilities en helpers
├── validation/          # Input validatie
└── web_lookup/          # Externe data integratie
```

### Module Details

#### `ai_toetser/` - AI Validation Components

**Doel**: Bevat AI-gebaseerde validatie en toetsing functionaliteit.

```
ai_toetser/
├── __init__.py
├── ai_toetser.py        # Hoofdklasse voor AI toetsing
└── prompts/             # Prompt templates voor validatie
```

**Verantwoordelijkheden**:
- AI-gebaseerde kwaliteitscontrole
- Definitie validatie via LLM
- Suggesties voor verbeteringen

#### `config/` - Configuration Management

**Doel**: Centraal configuratiebeheer voor de applicatie.

```
config/
├── __init__.py
├── config_manager.py    # ConfigManager class
├── exceptions.py        # Configuratie exceptions
└── schemas/            # Configuratie schema's
```

**Verantwoordelijkheden**:
- Environment variable management
- YAML configuratie parsing
- Feature flags
- Runtime configuratie

#### `database/` - Database Layer

**Doel**: Database abstractie, models en migrations.

```
database/
├── __init__.py
├── models.py           # SQLAlchemy models
├── repository.py       # Repository pattern implementatie
├── migrations/         # Database migrations
│   └── schema.sql     # Database schema definitie
└── session.py         # Database session management
```

**Verantwoordelijkheden**:
- Database connectiviteit
- CRUD operaties
- Schema management
- Query optimalisatie

#### `document_processing/` - Document Processing

**Doel**: Document parsing, extractie en verwerking.

```
document_processing/
├── __init__.py
├── processor.py        # Document processor
├── extractors/         # Content extractors
└── formatters/         # Output formatters
```

**Verantwoordelijkheden**:
- PDF/Word document parsing
- Content extractie
- Metadata verwerking
- Format conversies

#### `domain/` - Domain Models

**Doel**: Core business domain models en logica.

```
domain/
├── __init__.py
├── models.py           # Domain entities
├── value_objects.py    # Value objects
├── enums.py           # Domain enumeraties
└── exceptions.py       # Domain exceptions
```

**Key Models**:
- `Definition`: Hoofdmodel voor definities
- `DefinitionCategory`: Type, Proces, Resultaat, Exemplaar
- `ValidationResult`: Validatie resultaten
- `DefinitionContext`: Context informatie

#### `orchestration/` - Orchestration Logic

**Doel**: Coördinatie van complexe workflows en processen.

```
orchestration/
├── __init__.py
├── base_orchestrator.py    # Abstract orchestrator
├── v2_orchestrator.py      # V2 async orchestrator
└── strategies/             # Orchestratie strategieën
```

**Verantwoordelijkheden**:
- Multi-step workflow coördinatie
- Service compositie
- Error recovery
- State management

#### `services/` - Core Services

**Doel**: Belangrijkste business services en functionaliteit.

AS‑IS (korte greep):
```
services/
├── ai_service_v2.py
├── definition_orchestrator.py
├── modern_web_lookup_service.py
├── definition_repository.py
├── definition_validator.py
└── prompts/
```

TO‑BE (beoogd):
```
services/
├── interfaces.py
├── orchestrators/
├── prompts/
└── service_factory.py
```

```
services/
├── __init__.py
├── ai_service.py           # AI service interface
├── ai_service_v2.py        # V2 AI implementatie
├── async_gpt_client.py     # Async OpenAI client
├── cache_service.py        # Caching functionaliteit
├── definition_service.py    # Definitie business logic
├── orchestrators/          # Service-specifieke orchestrators
│   ├── definition_orchestrator_v2.py
│   ├── validation_orchestrator_v2.py
│   └── prompt_orchestrator.py
├── prompts/               # Prompt management
│   ├── base_module.py    # Base prompt module
│   ├── module_registry.py # Module registratie
│   └── modules/          # 18+ prompt modules
└── service_container.py   # Dependency injection container
```

**Key Services**:
- **AIService**: Interface voor AI operaties
- **CacheService**: In-memory caching
- **DefinitionService**: Definitie CRUD en business logic
- **AsyncGPTClient**: Async OpenAI integratie

#### `services/prompts/modules/` - Prompt Modules

**Doel**: Modulaire prompt generatie systeem.

```
modules/
├── achtergrond.py         # Context achtergrond
├── algemene_kennis.py     # Algemene kennis integratie
├── beschrijving.py        # Beschrijving generatie
├── context.py             # Context verwerking
├── dynamische_elementen.py # Dynamische content
├── gerelateerde_begrippen.py # Gerelateerde termen
├── gvi.py                 # Generation-Validation-Integration
├── juridische_context.py   # Juridische context
├── ontologie.py           # Ontologische classificatie
├── prompt_formatter.py     # Prompt formatting
├── reflectie.py           # Zelf-reflectie
├── samenvatting.py        # Samenvattingen
├── structuur.py           # Structurele formatting
├── taal.py                # Taal verwerking
├── validatie.py           # Validatie prompts
├── verbetering.py         # Verbetering suggesties
├── voorbeeld.py           # Voorbeeld generatie
└── voorbeeld_zin.py       # Voorbeeld zinnen
```

#### `toetsregels/` - Validation Rules

**Doel**: Implementatie van 40+ validatie regels.

```
toetsregels/
├── __init__.py
├── base_rule.py           # Abstract base regel
├── regel_factory.py       # Regel instantiatie
├── arai/                  # Afbakening regels
├── con/                   # Context regels
├── ess/                   # Essentiële element regels
├── int/                   # Integriteit regels
├── sam/                   # Samenhang regels
├── str/                   # Structuur regels
└── ver/                   # Verificatie regels
```

**Regel Categorieën**:
- **ARAI**: Afbakening, Reikwijdte, Afbakening Inhoud
- **CON**: Context, Consistentie
- **ESS**: Essentiële elementen
- **INT**: Integriteit, Internal consistency
- **SAM**: Samenhang, Samenvatting
- **STR**: Structuur validatie
- **VER**: Verificatie

#### `ui/` - User Interface

**Doel**: Streamlit UI componenten en pages.

```
ui/
├── __init__.py
├── main_page.py           # Hoofdpagina
├── components/            # Herbruikbare UI componenten
│   ├── definition_form.py
│   ├── results_display.py
│   └── sidebar.py
├── pages/                 # Streamlit pages
│   ├── generator.py      # Definitie generator
│   ├── validator.py      # Validatie interface
│   └── history.py        # Historie weergave
└── styles/               # CSS en styling
```

**Verantwoordelijkheden**:
- User interface rendering
- Form handling
- Session state management
- Result visualisatie

AS‑IS voorbeelden:
```
ui/
├── tabbed_interface.py
└── components/
```

#### `utils/` - Utilities

**Doel**: Algemene utilities en helper functies.

```
utils/
├── __init__.py
├── async_utils.py         # Async helpers
├── cache_utils.py         # Cache utilities
├── logging_utils.py       # Logging configuratie
├── resilience.py          # Circuit breakers, retries
├── sanitizer.py           # Input sanitization
└── validators.py          # Input validators
```

**Key Utilities**:
- **AsyncUtils**: Async pattern helpers
- **Resilience**: Retry logic, circuit breakers
- **Sanitizer**: XSS preventie, input cleaning
- **Validators**: Format validatie

#### `validation/` - Input Validation

**Doel**: Input validatie en sanitization.

```
validation/
├── __init__.py
├── input_validator.py     # Input validatie logic
├── schemas.py            # Validatie schema's
└── exceptions.py         # Validatie exceptions
```

#### `web_lookup/` - External Data Integration

**Doel**: Integratie met externe data bronnen.

```
web_lookup/
├── __init__.py
├── lookup_service.py      # Web lookup service
├── scrapers/             # Web scrapers
├── parsers/              # Content parsers
└── enrichment.py         # Data verrijking
```

## Test Structure

```
tests/
├── __init__.py
├── conftest.py           # Pytest configuratie
├── fixtures/             # Test data
├── unit/                 # Unit tests per module
│   ├── services/
│   ├── toetsregels/
│   └── utils/
├── integration/          # Integratie tests
│   ├── test_ai_integration.py
│   └── test_db_integration.py
├── e2e/                  # End-to-end tests
└── performance/          # Performance tests
```

## Design Patterns

### Service Pattern
- Alle business logic in services
- Clean interfaces
- Dependency injection via ServiceContainer

### Repository Pattern
- Database abstractie
- Scheiding van domein en persistentie
- Testbare data access

### Module Pattern
- Prompt modules voor flexibiliteit
- Regel modules voor validatie
- Plugin architectuur

### Factory Pattern
- RegelFactory voor regel instantiatie
- ServiceContainer voor service creatie
- ModuleRegistry voor prompt modules

## Key Design Decisions

### 1. Modular Prompt System
- 18+ gespecialiseerde modules
- Flexibele compositie
- Makkelijk uitbreidbaar

### 2. Async-First Architecture
- AsyncGPTClient voor AI calls
- Async database operations
- Non-blocking I/O

### 3. Validation Framework
- 40+ validatie regels
- Categorie-gebaseerde organisatie
- Pluggable regel systeem

### 4. Service-Oriented Architecture
- Clear separation of concerns
- Dependency injection
- Testbare componenten

## Module Dependencies

```mermaid
graph TD
    UI[UI Layer] --> Services[Service Layer]
    Services --> Domain[Domain Layer]
    Services --> Database[Database Layer]
    Services --> AIToetser[AI Toetser]
    Services --> WebLookup[Web Lookup]
    Services --> Utils[Utilities]

    Orchestration[Orchestration] --> Services
    Validation[Validation] --> Domain
    Toetsregels[Toetsregels] --> Domain

    Services --> Config[Configuration]
    Database --> Config

    AIToetser --> Utils
    WebLookup --> Utils
```

## AS‑IS → TO‑BE Mapping (Kernservices)

| Domein | AS‑IS (pad) | TO‑BE (beoogd) | Notities |
|---|---|---|---|
| Orchestrator | `src/services/definition_orchestrator.py` | `src/services/orchestrators/definition_orchestrator_v2.py` | UI roept orchestrator‑first aan; geen directe generator/validator aanroepen in UI |
| AI Service | `src/services/ai_service_v2.py` | `src/services/interfaces.py` (AI‑interface) + providers (infra) | Interfaces in services; providers in infra; UI/Services zien geen SDK |
| Repository | `src/services/definition_repository.py`, `src/database/definitie_repository.py` | `src/infrastructure/database/definition_repository_<db>.py` + `DefinitionRepositoryInterface` | Repository pattern; paging/filtering; N+1 oplossen |
| Web Lookup | `src/services/modern_web_lookup_service.py` | `src/services/web_lookup/modern_web_lookup_service.py` + interface | Timeouts/retries configurabel; UI‑tab gebruikt moderne service |
| Prompts | `src/services/definition_generator_prompts.py` | `src/services/prompts/*` + PromptBuilder‑interface | Golden tests voor prompts; orchestrator vraagt builder |
| Validatie | `src/services/definition_validator.py`, `src/toetsregels/*` | `src/services/orchestrators/validation_orchestrator_v2.py` + `src/services/interfaces/validation.py` | ValidationOrchestratorV2 scheidt validatie van definitie-generatie; moderne validator als dependency |
| UI | `src/ui/tabbed_interface.py`, `src/ui/components/*` | UI→Services (via factory/container) | Geen DB/OpenAI imports in UI; feature flags voor cutover |

## Stepping Plan (kort)

- Orchestrator:
  - Stap 1: Leid alle UI‑generaties via `DefinitionOrchestrator.create_definition` (auditeer imports in `ui/*`).
  - Stap 2: Contracttests voor het orchestrator‑pad (generate→validate→enrich→store); smoke per tab.
  - Stap 3: Activeer `FEATURE_ORCHESTRATOR_ONLY` in dev/staging; monitor diff t.o.v. legacy paden.

- AI‑service:
  - Stap 1: Finaliseer AI‑interfacecontract in docs; handhaaf huidige `ai_service_v2` tot cutover.
  - Stap 2: Voorbereidende contracttests (mock provider) zonder codewijzigingen in UI/services.
  - Stap 3: Plan provider‑implementatie in infra en cutover met feature flag (aparte PR).

- Repository:
  - Stap 1: Verplaats DB‑specifieke code naar infra‑implementatie; houd interface in services.
  - Stap 2: Voeg paging/filtering toe; elimineer N+1 in hotspots; update factory.
  - Stap 3: Integratie‑smokes en performance metingen (p95, query count).

- Web Lookup:
  - Stap 1: UI‑tab aansluiten op `ModernWebLookupService`; stel timeouts/retries/config in.
  - Stap 2: Flag `FEATURE_MODERN_LOOKUP` aan in dev/staging; verwijder legacy imports uit actieve paden.
  - Stap 3: Monitoring op fouten/latency; daarna legacy opruimen.

- Prompts:
  - Stap 1: Leg `PromptBuilderInterface` vast in docs; laat `UnifiedPromptBuilder` daarop aansluiten in een aparte batch.
  - Stap 2: Voeg golden snapshot tests toe (input→prompt) als regressie‑anker.
  - Stap 3: Cutover orchestrator→builder; meet tokenbudget/kwaliteit.

- Validatie:
  - Stap 1: Valideer huidige 45/46 regels; voeg ontbrekende regel met tests.
  - Stap 2: Contracttests validatorinterface; score‑alignement op golden set.
  - Stap 3: Telemetrie op violations/score trends.

- UI:
  - Stap 1: Audit op directe DB/OpenAI imports; vervangen door services/factory.
  - Stap 2: Smoke‑tests per tab; feature flags zichtbaar in Management tab.
  - Stap 3: Verwijder legacy koppelingen na stabiele staging.

- Cross‑cutting:
  - Stap 1: Lint rule voor importgrenzen (geen UI→infra/SDK); CI‑check toevoegen.
  - Stap 2: Observability uitbreiden (structured logs, metrics, tracing) voor cutover‑monitoring.
  - Stap 3: Documenteer ADR’s en update de mappingtabel bij iedere batch.

- Roll‑out:
  - Dual‑run/shadow‑mode met diff‑rapportage → toggle feature flag → cleanup.

## Best Practices

### Module Organization
1. Elke module heeft een duidelijke verantwoordelijkheid
2. Minimale dependencies tussen modules
3. Publieke interfaces gedefinieerd in `__init__.py`
4. Private implementaties met underscore prefix

### Code Organization
1. Groepeer gerelateerde functionaliteit
2. Gebruik descriptieve bestandsnamen
3. Houd bestanden klein en focused
4. Documenteer publieke APIs

### Import Structure
1. Standaard library imports eerst
2. Third-party imports daarna
3. Lokale applicatie imports laatst
4. Alfabetisch binnen elke groep

### Testing
1. Mirror source structure in tests
2. Een test file per source file
3. Fixtures in centrale locatie
4. Integration tests voor cross-module functionaliteit

---

Deze source tree documentatie wordt bijgewerkt wanneer de structuur van de applicatie verandert.
