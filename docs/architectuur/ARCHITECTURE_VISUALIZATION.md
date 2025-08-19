# Architectuur Visualisatie - Definitie App

Dit document biedt een visuele weergave van zowel de huidige (AS-IS) als gewenste (TO-BE) architectuur van de Definitie App, met specifieke aandacht voor Python bestanden en hun functies.

## 1. Huidige Architectuur (AS-IS)

### 1.1 Component Overzicht

```mermaid
graph TB
    subgraph "UI Layer"
        MAIN[main.py<br/>Entry Point]
        UI_COMP[UI Components<br/>src/ui/]
        TAB1[definition_generator_tab.py<br/>✅ Functional]
        TAB2[management_tab.py<br/>✅ Functional]
        TAB3[web_lookup_tab.py<br/>✅ Functional]
        TAB4[history_tab.py<br/>❌ Not Implemented]
        TAB5[quality_tab.py<br/>❌ Not Implemented]
        TAB6[expert_tab.py<br/>❌ Not Implemented]
        TAB7[export_tab.py<br/>❌ Not Implemented]
        TAB8[sources_tab.py<br/>❌ Not Implemented]
        TAB9[monitoring_tab.py<br/>❌ Not Implemented]
        TAB10[orchestration_tab.py<br/>❌ Not Implemented]
    end

    subgraph "Service Layer (Mixed State)"
        SC[container.py<br/>ServiceContainer<br/>✅ DI Pattern]
        ORCH[definition_orchestrator.py<br/>Workflow Coordination<br/>✅ Production Ready]
        GEN[unified_definition_generator.py<br/>AI Integration<br/>⚠️ 80% Complete]
        VAL[definition_validator.py<br/>Rule Engine<br/>✅ 95% Complete]
        REPO[definition_repository.py<br/>Data Access<br/>✅ 90% Complete]
        WEB[modern_web_lookup_service.py<br/>External Data<br/>⚠️ 60% Complete]
    end

    subgraph "Legacy Layer"
        AGENT[definitie_agent.py<br/>876 LOC<br/>High Complexity]
        UDS[unified_definition_service.py<br/>1043 LOC<br/>God Object]
        OLD_VAL[old_validator.py<br/>Legacy Rules]
    end

    subgraph "Data Layer"
        DB[(SQLite<br/>definities.db<br/>❌ No Migrations)]
        CONFIG[JSON Files<br/>Toetsregels<br/>Templates]
    end

    MAIN --> UI_COMP
    UI_COMP --> TAB1
    UI_COMP --> TAB2
    UI_COMP --> TAB3

    TAB1 --> SC
    TAB2 --> SC
    TAB3 --> SC

    SC --> ORCH
    ORCH --> GEN
    ORCH --> VAL
    ORCH --> REPO
    GEN --> WEB

    GEN -.-> UDS
    VAL -.-> OLD_VAL
    AGENT -.-> GEN

    REPO --> DB
    VAL --> CONFIG

    classDef complete fill:#90EE90,stroke:#228B22,stroke-width:2px
    classDef partial fill:#FFE4B5,stroke:#FF8C00,stroke-width:2px
    classDef legacy fill:#FFB6C1,stroke:#DC143C,stroke-width:2px
    classDef notimpl fill:#D3D3D3,stroke:#696969,stroke-width:2px

    class SC,ORCH,VAL,REPO,TAB1,TAB2,TAB3 complete
    class GEN,WEB partial
    class AGENT,UDS,OLD_VAL,DB legacy
    class TAB4,TAB5,TAB6,TAB7,TAB8,TAB9,TAB10 notimpl
```

### 1.2 Python Bestanden en Hun Functies

#### UI Components (`src/ui/`)
| Bestand | Status | Primaire Functie | Dependencies |
|---------|--------|------------------|--------------|
| `main.py` | ✅ Active | Streamlit app entry point, session management | All UI components |
| `tabbed_interface.py` | ✅ Active | Tab navigation controller | Individual tab modules |
| `definition_generator_tab.py` | ✅ Working | Create new definitions UI | ServiceContainer |
| `management_tab.py` | ✅ Working | Manage existing definitions | ServiceContainer |
| `web_lookup_tab.py` | ✅ Working | External source lookup | ServiceContainer |
| `history_tab.py` | ❌ Stub | Definition history view | Not implemented |
| `quality_tab.py` | ❌ Stub | Quality control dashboard | Not implemented |
| `expert_tab.py` | ❌ Stub | Expert review interface | Not implemented |
| `export_tab.py` | ❌ Stub | Export functionality | Not implemented |
| `sources_tab.py` | ❌ Stub | External sources config | Not implemented |
| `monitoring_tab.py` | ❌ Stub | System monitoring | Not implemented |
| `orchestration_tab.py` | ❌ Stub | Workflow orchestration | Not implemented |

#### Service Layer (`src/services/`)
| Bestand | Status | Primaire Functie | Key Methods |
|---------|--------|------------------|-------------|
| `container.py` | ✅ Production | Dependency injection container | `get_orchestrator()`, `get_repository()` |
| `definition_orchestrator.py` | ✅ Production | Workflow coordination | `generate_definition()`, `validate_definition()` |
| `unified_definition_generator.py` | ⚠️ Partial | AI-powered generation | `generate()`, `_enhance_with_context()` |
| `definition_validator.py` | ✅ Production | Rule-based validation | `validate()`, `_check_rules()` |
| `definition_repository.py` | ✅ Production | Data persistence | `save()`, `get()`, `update()`, `delete()` |
| `modern_web_lookup_service.py` | ⚠️ Partial | External data fetching | `lookup()`, `_fetch_from_source()` |

#### Legacy Components (`src/legacy/`)
| Bestand | Lines | Complexity | Still Used | Migration Status |
|---------|-------|------------|------------|------------------|
| `definitie_agent.py` | 876 | 24 | Yes - Wrapper | Needs full replacement |
| `unified_definition_service.py` | 1043 | 31 | Partially | 60% migrated to new services |
| `old_validator.py` | 456 | 15 | As fallback | Can be removed |

### 1.3 Data Flow - Huidige Situatie

```mermaid
sequenceDiagram
    participant U as User
    participant UI as Streamlit UI
    participant SC as ServiceContainer
    participant O as Orchestrator
    participant G as Generator
    participant V as Validator
    participant R as Repository
    participant L as Legacy Code

    U->>UI: Create Definition
    UI->>SC: Get Orchestrator
    SC->>O: generate_definition(begrip, category)
    O->>G: generate(request)
    G->>L: Fallback to legacy generator
    L-->>G: Generated text
    G-->>O: Definition draft
    O->>V: validate(definition)
    V-->>O: Validation result
    O->>R: save(definition)
    R-->>O: Saved definition
    O-->>UI: Complete definition
    UI-->>U: Display result

    Note over G,L: 80% new code, 20% legacy fallback
    Note over UI: Only 3/10 tabs functional
```

## 2. Gewenste Architectuur (TO-BE)

### 2.1 Component Overzicht

```mermaid
graph TB
    subgraph "Client Layer"
        UI[Streamlit UI<br/>Enhanced]
        CLI[CLI Interface<br/>New]
        MOBILE[Mobile App<br/>Future]
    end

    subgraph "API Gateway"
        GW[API Gateway<br/>- JWT Auth<br/>- Rate Limiting<br/>- Request Routing]
    end

    subgraph "Application Services"
        ORCH[DefinitionOrchestrator<br/>- Saga Pattern<br/>- Transaction Management]
        GEN[GeneratorService<br/>- AI Integration<br/>- Template Engine<br/>- Multi-model Support]
        VAL[ValidatorService<br/>- Rule Engine v2<br/>- ML-based Scoring<br/>- Custom Rules API]
        REPO[RepositoryService<br/>- CQRS Pattern<br/>- Event Sourcing<br/>- Multi-tenant]
    end

    subgraph "Supporting Services"
        WEB[WebLookupService<br/>- Multi-source<br/>- Smart Caching<br/>- Rate Management]
        AUTH[AuthService<br/>- JWT/OAuth2<br/>- RBAC<br/>- API Keys]
        MON[MonitoringService<br/>- Metrics<br/>- Alerts<br/>- Dashboards]
        NOTIF[NotificationService<br/>- Email/SMS<br/>- Webhooks<br/>- Real-time]
    end

    subgraph "Data Layer"
        PG[(PostgreSQL<br/>Primary DB<br/>With Migrations)]
        REDIS[(Redis<br/>Cache & Pub/Sub)]
        S3[S3 Storage<br/>Documents<br/>Exports]
        KAFKA[Kafka<br/>Event Bus]
    end

    UI --> GW
    CLI --> GW
    MOBILE --> GW

    GW --> ORCH
    GW --> AUTH

    ORCH --> GEN
    ORCH --> VAL
    ORCH --> REPO
    ORCH --> NOTIF

    GEN --> WEB
    WEB --> REDIS

    REPO --> PG
    REPO --> KAFKA

    MON --> KAFKA
    NOTIF --> KAFKA

    ORCH --> S3

    classDef future fill:#E6E6FA,stroke:#4B0082,stroke-width:2px
    classDef enhanced fill:#98FB98,stroke:#006400,stroke-width:2px
    classDef new fill:#87CEEB,stroke:#4682B4,stroke-width:2px

    class UI enhanced
    class CLI,MOBILE,GW,AUTH,MON,NOTIF,PG,REDIS,S3,KAFKA new
    class MOBILE future
```

### 2.2 Target Service Architecture

#### Core Application Services
```python
# src/services/definition_orchestrator.py
class DefinitionOrchestrator:
    """
    Verantwoordelijkheden:
    - Workflow coordination met Saga pattern
    - Transaction management
    - Event publishing
    - Service composition
    """
    async def create_definition_workflow(self, request: CreateDefinitionRequest) -> Definition:
        # 1. Start transaction/saga
        # 2. Generate via GeneratorService
        # 3. Validate via ValidatorService
        # 4. Persist via RepositoryService
        # 5. Publish events
        # 6. Handle compensation on failure

# src/services/generator_service.py
class GeneratorService:
    """
    Verantwoordelijkheden:
    - AI model integration (OpenAI, Anthropic, etc.)
    - Prompt template management
    - Context enhancement
    - Response caching
    """
    async def generate(self, request: GenerationRequest) -> GeneratedDefinition:
        # 1. Select optimal AI model
        # 2. Build context from cache
        # 3. Apply templates
        # 4. Stream response
        # 5. Cache result

# src/services/validator_service.py
class ValidatorService:
    """
    Verantwoordelijkheden:
    - Rule engine v2 with hot reload
    - ML-based quality scoring
    - Custom validation rules API
    - Detailed feedback generation
    """
    async def validate(self, definition: Definition) -> ValidationResult:
        # 1. Apply rule sets
        # 2. ML quality prediction
        # 3. Generate feedback
        # 4. Calculate scores

# src/services/repository_service.py
class RepositoryService:
    """
    Verantwoordelijkheden:
    - CQRS implementation
    - Event sourcing
    - Query optimization
    - Multi-tenant support
    """
    async def save(self, definition: Definition) -> str:
        # 1. Validate command
        # 2. Store in write model
        # 3. Publish domain event
        # 4. Update read model
```

### 2.3 Target Folder Structure

```
definitie-app/
├── src/
│   ├── api/                      # API Gateway & REST endpoints
│   │   ├── gateway/
│   │   ├── middleware/
│   │   └── routes/
│   ├── services/                 # Business logic services
│   │   ├── core/                # Core domain services
│   │   │   ├── definition_orchestrator.py
│   │   │   ├── generator_service.py
│   │   │   ├── validator_service.py
│   │   │   └── repository_service.py
│   │   ├── supporting/          # Supporting services
│   │   │   ├── web_lookup_service.py
│   │   │   ├── auth_service.py
│   │   │   ├── notification_service.py
│   │   │   └── monitoring_service.py
│   │   └── shared/              # Shared utilities
│   │       ├── interfaces.py
│   │       ├── exceptions.py
│   │       └── utils.py
│   ├── domain/                  # Domain models
│   │   ├── models/
│   │   ├── events/
│   │   └── commands/
│   ├── infrastructure/          # Infrastructure code
│   │   ├── database/
│   │   ├── cache/
│   │   ├── messaging/
│   │   └── storage/
│   ├── ui/                      # UI applications
│   │   ├── streamlit/          # Current UI
│   │   ├── cli/               # New CLI
│   │   └── shared/            # Shared UI components
│   └── tests/                  # All tests
│       ├── unit/
│       ├── integration/
│       └── e2e/
├── infrastructure/             # IaC definitions
│   ├── kubernetes/
│   ├── terraform/
│   └── docker/
├── migrations/                 # Database migrations
├── docs/                      # Documentation
└── scripts/                   # Utility scripts
```

### 2.4 API Design

```yaml
# API Endpoints Overview
openapi: 3.0.0
info:
  title: Definitie App API
  version: 2.0.0

paths:
  /api/v1/definitions:
    post:
      summary: Create new definition
      tags: [Definitions]
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateDefinitionRequest'
      responses:
        201:
          description: Definition created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Definition'

  /api/v1/definitions/{id}:
    get:
      summary: Get definition by ID
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
            format: uuid

  /api/v1/definitions/validate:
    post:
      summary: Validate definition text
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                text:
                  type: string
                category:
                  type: string
                  enum: [type, proces, resultaat, exemplaar]
```

### 2.5 Migration Path

```mermaid
graph LR
    subgraph "Phase 1: Foundation"
        A1[Complete Service<br/>Extraction]
        A2[Add API Gateway]
        A3[Implement Auth]
        A4[Setup Monitoring]
    end

    subgraph "Phase 2: Data Layer"
        B1[PostgreSQL<br/>Migration]
        B2[Add Redis Cache]
        B3[Implement<br/>Event Bus]
        B4[Add Migrations]
    end

    subgraph "Phase 3: Features"
        C1[Complete All<br/>UI Tabs]
        C2[Add CLI]
        C3[Performance<br/>Optimization]
        C4[Advanced<br/>Validation]
    end

    subgraph "Phase 4: Production"
        D1[Kubernetes<br/>Deployment]
        D2[Full Monitoring]
        D3[Security<br/>Hardening]
        D4[Documentation]
    end

    A1 --> A2 --> A3 --> A4
    A4 --> B1 --> B2 --> B3 --> B4
    B4 --> C1 --> C2 --> C3 --> C4
    C4 --> D1 --> D2 --> D3 --> D4
```

## 3. Key Differences Summary

### 3.1 Architecture Evolution

| Aspect | Current (AS-IS) | Target (TO-BE) |
|--------|-----------------|----------------|
| **Pattern** | Hybrid monolith/services | True microservices |
| **Database** | SQLite, no migrations | PostgreSQL with migrations |
| **Caching** | None | Redis multi-layer |
| **Auth** | None | JWT/OAuth2 + RBAC |
| **API** | Direct function calls | REST API Gateway |
| **Events** | None | Kafka event bus |
| **UI** | 30% functional | 100% + CLI + Mobile |
| **Monitoring** | Basic logging | Full observability |
| **Deployment** | Manual | Kubernetes + CI/CD |
| **Performance** | 8-12s response | <2s response |

### 3.2 Service Comparison

```mermaid
graph TB
    subgraph "Current Services"
        CUR_ORCH[Orchestrator<br/>Basic coordination]
        CUR_GEN[Generator<br/>Single AI model<br/>No caching]
        CUR_VAL[Validator<br/>Static rules]
        CUR_REPO[Repository<br/>Simple CRUD]
        CUR_WEB[Web Lookup<br/>Basic fetch]
    end

    subgraph "Target Services"
        NEW_ORCH[Orchestrator<br/>Saga pattern<br/>Transactions]
        NEW_GEN[Generator<br/>Multi-model<br/>Smart caching]
        NEW_VAL[Validator<br/>ML scoring<br/>Dynamic rules]
        NEW_REPO[Repository<br/>CQRS + Events]
        NEW_WEB[Web Lookup<br/>Multi-source<br/>Rate limited]
        NEW_AUTH[Auth Service<br/>New]
        NEW_MON[Monitoring<br/>New]
        NEW_NOTIF[Notifications<br/>New]
    end

    CUR_ORCH -.->|Enhance| NEW_ORCH
    CUR_GEN -.->|Upgrade| NEW_GEN
    CUR_VAL -.->|Extend| NEW_VAL
    CUR_REPO -.->|Refactor| NEW_REPO
    CUR_WEB -.->|Complete| NEW_WEB
```

## 4. Browser-Friendly Views

Deze diagrammen zijn geoptimaliseerd voor weergave in browsers:
- Mermaid diagrammen werken in GitHub, GitLab, en vele markdown viewers
- Kleuren geven status aan: Groen (✅), Oranje (⚠️), Rood (❌), Grijs (niet geïmplementeerd)
- Interactieve elementen in ondersteunde viewers

Voor het beste resultaat:
1. Open dit bestand in GitHub of een Mermaid-compatible viewer
2. Gebruik een moderne browser (Chrome, Firefox, Safari)
3. Voor offline viewing: gebruik een tool zoals Mermaid Live Editor

## 5. Quick Reference

### Current State Issues
- 70% UI non-functional
- No authentication/security
- Performance 4-6x slower than target
- 23% code duplication
- No proper testing (11% coverage)

### Target State Benefits
- Full functionality across all interfaces
- <2s response times
- Secure multi-tenant architecture
- 80%+ test coverage
- Automated deployment & monitoring

---

*Document gemaakt door: Winston (Architect)*
*Datum: 2024-01-19*
*Versie: 1.0*
