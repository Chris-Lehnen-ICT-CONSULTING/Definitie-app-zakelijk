# DefinitieAgent Modern Rebuild Architecture

**Version**: 1.0
**Date**: 2025-10-02
**Status**: Design Proposal
**Author**: Senior Full-Stack Architect

---

## Executive Summary

This document presents a complete modern architecture design for rebuilding DefinitieAgent from a Streamlit monolith (83,319 LOC, 65% unused) into a clean, performant, maintainable system optimized for single-developer workflow.

**Key Goals**:
- Reduce response time from 8-12s to <2s
- Eliminate 65% unused code (reduce to ~30,000 LOC)
- Modern, testable architecture following Clean Architecture principles
- Maintain all 46 validation rules and core functionality
- Keep single-user simplicity while enabling future scaling

**Architecture Decision**: **FastAPI + React + PostgreSQL + Redis**

---

## Table of Contents

1. [Tech Stack Selection](#1-tech-stack-selection)
2. [Architecture Design](#2-architecture-design)
3. [Performance Optimization Strategy](#3-performance-optimization-strategy)
4. [Project Structure](#4-project-structure)
5. [Service Boundaries](#5-service-boundaries)
6. [API Contract Examples](#6-api-contract-examples)
7. [Developer Experience](#7-developer-experience)
8. [Migration Strategy](#8-migration-strategy)
9. [Implementation Roadmap](#9-implementation-roadmap)

---

## 1. Tech Stack Selection

### 1.1 Backend Framework: **FastAPI** ✅

**Rationale**:
- **Performance**: ASGI-based, async-first (3-5x faster than Flask/Django REST)
- **Modern Python**: Native async/await, type hints, Pydantic validation
- **API Documentation**: Auto-generated OpenAPI/Swagger docs
- **Developer Experience**: Hot reload, excellent error messages
- **Ecosystem**: Seamless OpenAI SDK integration, existing Pydantic models reusable
- **Future-Proof**: Easy to add GraphQL (Strawberry) or gRPC later

**Alternatives Considered**:
- ❌ **Flask**: Too basic, no async support, slower
- ❌ **Django REST**: Too heavy for single-user, monolithic tendencies
- ✅ **FastAPI**: Perfect balance of simplicity and power

### 1.2 Frontend: **React with Vite** ✅

**Rationale**:
- **Modern UX**: Escape Streamlit limitations, full UI control
- **Component Ecosystem**: Shadcn/ui (Radix + Tailwind) for professional UI
- **Performance**: Virtual DOM, code splitting, lazy loading
- **State Management**: TanStack Query for server state, Zustand for client state
- **Developer Experience**: Hot Module Replacement (HMR), TypeScript support
- **Single Developer Friendly**: Vite setup is simple, no complex build configs

**Alternatives Considered**:
- ❌ **Keep Streamlit**: Too limiting, no concurrent users, poor performance
- ❌ **Vue/Svelte**: Smaller ecosystems, less mature component libraries
- ❌ **Next.js**: Overkill for single-user app, SSR not needed
- ✅ **React + Vite**: Industry standard, massive ecosystem, developer-friendly

### 1.3 Database: **PostgreSQL** ✅

**Rationale**:
- **Future-Proof**: Handles concurrent users when needed
- **Full-Text Search**: Native Dutch language support (`to_tsvector`)
- **JSONB**: Store validation results, context efficiently
- **Performance**: Proper indexing, query optimization tools
- **Reliability**: ACID compliance, data integrity
- **Docker-Ready**: Easy local setup with docker-compose

**Migration Path**: Start with SQLite for MVP, migrate to PostgreSQL when adding users

**Alternatives Considered**:
- ⚠️ **SQLite**: Keep for MVP, migrate later (compatibility mode)
- ❌ **MongoDB**: Overkill, no need for document flexibility
- ✅ **PostgreSQL**: Standard choice for production Python apps

### 1.4 Caching: **Redis** ✅

**Rationale**:
- **Speed**: In-memory caching for prompts, API results
- **Semantic Caching**: OpenAI prompt caching (save 90% cost on duplicates)
- **Rate Limiting**: Token bucket implementation
- **Session Storage**: When adding multi-user support
- **Background Jobs**: Celery integration for async tasks (future)

### 1.5 API Design: **REST with OpenAPI 3.1** ✅

**Rationale**:
- **Simplicity**: RESTful design is straightforward for single developer
- **Tooling**: FastAPI auto-generates docs, client SDKs
- **Familiarity**: Standard patterns, easy to onboard future developers
- **Future GraphQL**: Can add Strawberry GraphQL layer later if needed

**Alternatives Considered**:
- ❌ **GraphQL**: Overkill for this use case, adds complexity
- ❌ **gRPC**: Too low-level, not needed for web app
- ✅ **REST**: Perfect for current needs, easy to extend

### 1.6 Testing: **Pytest + Playwright** ✅

**Rationale**:
- **Backend**: pytest (already used), pytest-asyncio for async tests
- **E2E**: Playwright for full UI testing (better than Selenium)
- **Coverage**: pytest-cov for code coverage tracking
- **Fast**: Parallel test execution with pytest-xdist

### 1.7 Summary Table

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Backend** | FastAPI 0.115+ | Async-first, type-safe, auto-docs, 3-5x faster |
| **Frontend** | React 18 + Vite 5 | Modern UX, component ecosystem, HMR |
| **Database** | PostgreSQL 16 | Full-text search, JSONB, future-proof |
| **Cache** | Redis 7 | Prompt caching, rate limiting, sessions |
| **API** | REST (OpenAPI 3.1) | Simple, standard, auto-documented |
| **State Mgmt** | TanStack Query + Zustand | Server state + UI state separation |
| **Styling** | Tailwind CSS + shadcn/ui | Modern, accessible, professional |
| **Testing** | pytest + Playwright | Backend + E2E coverage |
| **Dev Tools** | Docker Compose | Local dev environment consistency |

---

## 2. Architecture Design

### 2.1 Clean Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                    │
│  ┌────────────────────┐      ┌─────────────────────┐   │
│  │   React Frontend   │◄────►│  FastAPI REST API   │   │
│  │  (UI Components)   │      │  (HTTP Endpoints)    │   │
│  └────────────────────┘      └─────────────────────┘   │
└───────────────────────────────┬─────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────┐
│                   APPLICATION LAYER                      │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Service Orchestrators                     │  │
│  │  • DefinitionOrchestrator (11-phase workflow)    │  │
│  │  • ValidationOrchestrator (46 rules)             │  │
│  │  • ExportOrchestrator (multi-format)             │  │
│  └──────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────┐
│                     DOMAIN LAYER                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │              Core Services                        │  │
│  │  • AIService (OpenAI GPT-4 integration)          │  │
│  │  • ValidationService (46 rules engine)           │  │
│  │  • PromptService (template rendering)            │  │
│  │  • WebLookupService (Wikipedia/SRU)              │  │
│  │  • CleaningService (text processing)             │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │              Domain Entities                      │  │
│  │  • Definition, ValidationResult, Context         │  │
│  └──────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────┐
│                 INFRASTRUCTURE LAYER                     │
│  ┌─────────────┐  ┌──────────┐  ┌─────────────────────┐│
│  │ PostgreSQL  │  │  Redis   │  │  OpenAI API         ││
│  │ Repository  │  │  Cache   │  │  External Services  ││
│  └─────────────┘  └──────────┘  └─────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow Architecture

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ HTTP/WebSocket
       ▼
┌─────────────────────────────────────────────────┐
│           Nginx Reverse Proxy (Future)          │
│  • Rate Limiting                                │
│  • TLS Termination                              │
│  • Static File Serving                          │
└──────────────────┬──────────────────────────────┘
                   │
       ┌───────────┴───────────┐
       ▼                       ▼
┌─────────────┐         ┌─────────────┐
│   FastAPI   │         │    React    │
│  Backend    │◄────────┤   Frontend  │
│  (Port 8000)│  API    │  (Port 5173)│
└──────┬──────┘         └─────────────┘
       │
       ├──────────────────────────────────────────┐
       │                                          │
       ▼                                          ▼
┌─────────────┐  ┌──────────────┐  ┌──────────────────┐
│ PostgreSQL  │  │    Redis     │  │   OpenAI API     │
│   (5432)    │  │    (6379)    │  │  (External)      │
└─────────────┘  └──────────────┘  └──────────────────┘
   │                │
   │ Persistent     │ Cache
   │ Storage        │ • Prompts
   │                │ • API Results
   │                │ • Rate Limits
   ▼                ▼
[Definition Data]  [Fast Lookups]
```

### 2.3 Dependency Injection Pattern

**No Complex DI Frameworks** - Use FastAPI's native dependency injection:

```python
# backend/app/dependencies.py
from functools import lru_cache
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.services.ai_service import AIService
from app.services.validation_service import ValidationService
from app.services.cache_service import CacheService

# Singleton services with @lru_cache
@lru_cache()
def get_ai_service() -> AIService:
    return AIService()

@lru_cache()
def get_validation_service() -> ValidationService:
    return ValidationService()

@lru_cache()
def get_cache_service() -> CacheService:
    return CacheService()

# Type aliases for clean endpoint signatures
AIServiceDep = Annotated[AIService, Depends(get_ai_service)]
ValidationServiceDep = Annotated[ValidationService, Depends(get_validation_service)]
CacheServiceDep = Annotated[CacheService, Depends(get_cache_service)]
DBSessionDep = Annotated[AsyncSession, Depends(get_async_session)]
```

### 2.4 State Management (No session_state Anti-Pattern!)

**Backend**: Stateless services, all state in DB/Redis
**Frontend**: Clear separation of concerns

```typescript
// State Management Architecture
┌─────────────────────────────────────────────┐
│           Client State (Zustand)            │
│  • UI state (modals, forms, navigation)     │
│  • User preferences (theme, lang)           │
│  • Ephemeral data (current form inputs)     │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│       Server State (TanStack Query)         │
│  • Definitions (cached, auto-refetch)       │
│  • Validation results                       │
│  • Search results                           │
│  • Background mutations                     │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│        Backend State (PostgreSQL/Redis)     │
│  • Persistent: PostgreSQL (definitions)     │
│  • Temporary: Redis (cache, rate limits)    │
│  • No state in FastAPI (stateless services) │
└─────────────────────────────────────────────┘
```

---

## 3. Performance Optimization Strategy

### 3.1 Target Metrics

| Metric | Current | Target | Strategy |
|--------|---------|--------|----------|
| **Response Time** | 8-12s | <2s | Caching, async, parallel processing |
| **API Latency (p50)** | N/A | <500ms | FastAPI + async services |
| **API Latency (p95)** | N/A | <1.5s | Redis caching, connection pooling |
| **OpenAI API Cost** | High | -70% | Prompt caching, semantic deduplication |
| **Frontend Load** | N/A | <1s | Code splitting, lazy loading |
| **Database Queries** | N+1 issues | Optimized | Eager loading, batch queries |

### 3.2 Caching Strategy

```python
# Three-tier caching strategy

# Tier 1: In-Memory (LRU Cache for validation rules)
@lru_cache(maxsize=128)
def get_validation_rule(rule_id: str) -> ValidationRule:
    return load_rule_from_disk(rule_id)

# Tier 2: Redis (API responses, prompts)
async def generate_definition_cached(
    term: str,
    context: Context,
    cache: CacheService
) -> Definition:
    cache_key = f"def:{term}:{hash(context)}"

    # Try cache first
    cached = await cache.get(cache_key)
    if cached:
        return cached

    # Generate and cache
    result = await ai_service.generate(term, context)
    await cache.set(cache_key, result, ttl=3600)  # 1 hour
    return result

# Tier 3: Database Query Cache (PostgreSQL)
# Use SQLAlchemy query result caching for repeated queries
```

### 3.3 Async Processing Pattern

```python
# Parallel processing for 46 validation rules
async def validate_definition_parallel(
    definition: str,
    rules: list[ValidationRule]
) -> list[ValidationResult]:
    # Execute all 46 rules in parallel
    tasks = [
        asyncio.create_task(rule.validate(definition))
        for rule in rules
    ]

    # Gather results (fails fast on critical errors)
    results = await asyncio.gather(*tasks, return_exceptions=True)

    return [r for r in results if not isinstance(r, Exception)]
```

### 3.4 Database Optimization

```sql
-- Optimized schema with proper indexes
CREATE TABLE definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    term TEXT NOT NULL,
    definition TEXT NOT NULL,
    context JSONB NOT NULL,
    validation_score FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Full-text search index (Dutch)
    tsv tsvector GENERATED ALWAYS AS (
        to_tsvector('dutch', coalesce(term, '') || ' ' || coalesce(definition, ''))
    ) STORED
);

-- Performance indexes
CREATE INDEX idx_definitions_term ON definitions(term);
CREATE INDEX idx_definitions_tsv ON definitions USING GIN(tsv);
CREATE INDEX idx_definitions_context ON definitions USING GIN(context);
CREATE INDEX idx_definitions_created ON definitions(created_at DESC);

-- Validation results (separate table, no N+1)
CREATE TABLE validation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    definition_id UUID REFERENCES definitions(id) ON DELETE CASCADE,
    rule_id TEXT NOT NULL,
    passed BOOLEAN NOT NULL,
    score FLOAT NOT NULL,
    feedback JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_validation_def_id ON validation_results(definition_id);
```

### 3.5 OpenAI API Optimization

```python
# Semantic prompt caching
class SemanticPromptCache:
    async def get_or_generate(
        self,
        prompt: str,
        threshold: float = 0.95
    ) -> str:
        # Hash prompt for exact match
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
        cached = await self.redis.get(f"prompt:{prompt_hash}")
        if cached:
            return cached

        # Semantic similarity check (for near-duplicates)
        embedding = await self.openai.embeddings.create(
            input=prompt,
            model="text-embedding-3-small"
        )

        similar = await self.vector_search(embedding, threshold)
        if similar:
            return similar.response

        # Generate and cache
        response = await self.openai.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )

        result = response.choices[0].message.content
        await self.redis.set(f"prompt:{prompt_hash}", result, ex=3600)
        await self.vector_store.add(embedding, result)

        return result
```

---

## 4. Project Structure

```
definitie-app/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI app entry point
│   │   ├── api/               # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── dependencies.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── definitions.py
│   │   │       ├── validation.py
│   │   │       ├── export.py
│   │   │       └── search.py
│   │   ├── core/              # Core configuration
│   │   │   ├── __init__.py
│   │   │   ├── config.py      # Settings (Pydantic BaseSettings)
│   │   │   ├── database.py    # Database connection
│   │   │   ├── cache.py       # Redis connection
│   │   │   └── security.py    # Auth (future)
│   │   ├── domain/            # Domain layer (business logic)
│   │   │   ├── entities/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── definition.py
│   │   │   │   ├── validation.py
│   │   │   │   └── context.py
│   │   │   └── services/
│   │   │       ├── __init__.py
│   │   │       ├── ai_service.py
│   │   │       ├── validation_service.py
│   │   │       ├── prompt_service.py
│   │   │       ├── web_lookup_service.py
│   │   │       └── cleaning_service.py
│   │   ├── infrastructure/    # Infrastructure layer
│   │   │   ├── repositories/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── definition_repository.py
│   │   │   │   └── validation_repository.py
│   │   │   ├── cache/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── redis_cache.py
│   │   │   │   └── semantic_cache.py
│   │   │   └── external/
│   │   │       ├── __init__.py
│   │   │       ├── openai_client.py
│   │   │       └── wikipedia_client.py
│   │   ├── schemas/           # Pydantic schemas (DTOs)
│   │   │   ├── __init__.py
│   │   │   ├── definition.py
│   │   │   ├── validation.py
│   │   │   └── export.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── logging.py
│   │       └── errors.py
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   ├── alembic/               # Database migrations
│   │   ├── versions/
│   │   └── env.py
│   ├── config/                # Config files (YAML/JSON)
│   │   ├── validation_rules/  # 46 validation rules
│   │   └── prompts/           # Prompt templates
│   ├── pyproject.toml         # Poetry dependencies
│   ├── pytest.ini
│   └── .env.example
│
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── main.tsx           # Entry point
│   │   ├── App.tsx
│   │   ├── api/               # API client (axios/fetch)
│   │   │   ├── client.ts
│   │   │   ├── definitions.ts
│   │   │   └── validation.ts
│   │   ├── components/        # Reusable components
│   │   │   ├── ui/            # shadcn/ui components
│   │   │   ├── DefinitionForm.tsx
│   │   │   ├── ValidationResults.tsx
│   │   │   └── ExportPanel.tsx
│   │   ├── pages/             # Page components
│   │   │   ├── HomePage.tsx
│   │   │   ├── DefinitionGeneratorPage.tsx
│   │   │   ├── HistoryPage.tsx
│   │   │   └── ExportPage.tsx
│   │   ├── hooks/             # Custom React hooks
│   │   │   ├── useDefinitions.ts
│   │   │   └── useValidation.ts
│   │   ├── store/             # Zustand stores
│   │   │   └── uiStore.ts
│   │   ├── types/             # TypeScript types
│   │   │   └── api.ts
│   │   └── lib/               # Utilities
│   │       └── utils.ts
│   ├── public/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── tsconfig.json
│
├── docker/
│   ├── docker-compose.yml     # Local dev environment
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
│
├── scripts/                   # Development scripts
│   ├── setup_dev.sh
│   ├── run_tests.sh
│   └── seed_db.py
│
├── docs/                      # Documentation
│   └── api/                   # Auto-generated API docs
│
└── README.md
```

**Key Principles**:
- **Clean Architecture**: Clear layer separation (domain, application, infrastructure)
- **Colocation**: Related files together (tests next to source)
- **Discoverability**: Logical naming, shallow hierarchies
- **Scalability**: Easy to add new features without restructuring

---

## 5. Service Boundaries

### 5.1 Core Services

#### 5.1.1 DefinitionOrchestrator

**Responsibility**: Coordinate the 11-phase definition generation workflow

```python
# backend/app/domain/services/definition_orchestrator.py
from typing import Protocol
from app.domain.entities.definition import Definition, Context
from app.domain.services.ai_service import AIService
from app.domain.services.validation_service import ValidationService

class DefinitionOrchestrator:
    """Orchestrates the complete definition generation flow."""

    def __init__(
        self,
        ai_service: AIService,
        validation_service: ValidationService,
        prompt_service: PromptService,
        web_lookup_service: WebLookupService,
        repository: DefinitionRepository,
        cache: CacheService
    ):
        self.ai_service = ai_service
        self.validation_service = validation_service
        self.prompt_service = prompt_service
        self.web_lookup = web_lookup_service
        self.repository = repository
        self.cache = cache

    async def generate(
        self,
        term: str,
        context: Context,
        options: GenerationOptions = None
    ) -> DefinitionResult:
        """Execute the 11-phase generation workflow.

        Phases:
        1. Context enrichment (web lookup)
        2. Duplicate detection
        3. Prompt building
        4. AI generation
        5. Cleaning
        6. Validation (46 rules in parallel)
        7. Quality scoring
        8. Example generation
        9. Synonym extraction
        10. Provenance tracking
        11. Persistence
        """

        # Phase 1: Enrich context
        enriched_context = await self.web_lookup.enrich(term, context)

        # Phase 2: Check for duplicates
        duplicates = await self.repository.find_similar(term, threshold=0.85)
        if duplicates:
            return DefinitionResult(
                status="duplicate_found",
                duplicates=duplicates
            )

        # Phase 3: Build prompt
        prompt = await self.prompt_service.build_prompt(
            term=term,
            context=enriched_context,
            template="legal_definition_v2"
        )

        # Phase 4: Generate via AI (with caching)
        cache_key = self.cache.make_key("definition", term, context)
        definition_text = await self.cache.get_or_set(
            key=cache_key,
            factory=lambda: self.ai_service.generate(prompt),
            ttl=3600
        )

        # Phase 5: Clean definition
        cleaned = await self.cleaning_service.clean(definition_text)

        # Phase 6-7: Validate and score (parallel execution of 46 rules)
        validation_results = await self.validation_service.validate_parallel(
            definition=cleaned,
            term=term,
            context=enriched_context
        )

        quality_score = self._calculate_quality_score(validation_results)

        # Phase 8-9: Generate examples and synonyms (parallel)
        examples, synonyms = await asyncio.gather(
            self.ai_service.generate_examples(term, cleaned),
            self.ai_service.extract_synonyms(cleaned)
        )

        # Phase 10: Track provenance
        provenance = self._build_provenance(
            sources=enriched_context.sources,
            validation_results=validation_results
        )

        # Phase 11: Persist
        definition = Definition(
            term=term,
            definition=cleaned,
            context=enriched_context,
            validation_results=validation_results,
            quality_score=quality_score,
            examples=examples,
            synonyms=synonyms,
            provenance=provenance
        )

        saved = await self.repository.save(definition)

        return DefinitionResult(
            status="success",
            definition=saved,
            validation_score=quality_score
        )
```

#### 5.1.2 ValidationService

**Responsibility**: Execute 46 validation rules in parallel

```python
# backend/app/domain/services/validation_service.py
class ValidationService:
    """Manages 46 validation rules with parallel execution."""

    def __init__(self, rule_loader: ValidationRuleLoader):
        self.rules = rule_loader.load_all_rules()  # 46 rules

    async def validate_parallel(
        self,
        definition: str,
        term: str,
        context: Context
    ) -> list[ValidationResult]:
        """Execute all validation rules in parallel."""

        # Group rules by category for better error handling
        rule_groups = self._group_rules_by_category(self.rules)

        # Execute all rules concurrently
        tasks = [
            self._execute_rule(rule, definition, term, context)
            for rule in self.rules
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions, log errors
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Rule {self.rules[i].id} failed: {result}")
            else:
                valid_results.append(result)

        return valid_results

    async def _execute_rule(
        self,
        rule: ValidationRule,
        definition: str,
        term: str,
        context: Context
    ) -> ValidationResult:
        """Execute a single validation rule."""
        try:
            result = await rule.validate(
                definition=definition,
                term=term,
                context=context
            )
            return result
        except Exception as e:
            logger.exception(f"Rule {rule.id} execution failed")
            # Return failed result instead of raising
            return ValidationResult(
                rule_id=rule.id,
                passed=False,
                score=0.0,
                error=str(e)
            )
```

#### 5.1.3 AIService

**Responsibility**: OpenAI API integration with retry logic and caching

```python
# backend/app/domain/services/ai_service.py
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

class AIService:
    """Handles all OpenAI API interactions."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4-turbo",
        temperature: float = 0.0
    ):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 300
    ) -> str:
        """Generate text using OpenAI API with retry logic."""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a Dutch legal definition expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
            max_tokens=max_tokens
        )

        return response.choices[0].message.content.strip()

    async def generate_examples(
        self,
        term: str,
        definition: str,
        count: int = 3
    ) -> list[str]:
        """Generate usage examples."""
        prompt = f"""Generate {count} realistic usage examples for the legal term "{term}".

Definition: {definition}

Provide {count} example sentences showing how this term is used in legal contexts."""

        result = await self.generate(prompt, max_tokens=200)
        return [ex.strip() for ex in result.split("\n") if ex.strip()][:count]
```

#### 5.1.4 CacheService

**Responsibility**: Redis-based caching with semantic similarity

```python
# backend/app/infrastructure/cache/redis_cache.py
import redis.asyncio as redis
from typing import Any, Optional, Callable
import hashlib
import pickle

class CacheService:
    """Redis-based caching service."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)

    def make_key(self, *parts: Any) -> str:
        """Generate cache key from parts."""
        key_str = ":".join(str(p) for p in parts)
        return hashlib.sha256(key_str.encode()).hexdigest()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        value = await self.redis.get(key)
        if value:
            return pickle.loads(value)
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600
    ) -> bool:
        """Set value in cache with TTL."""
        serialized = pickle.dumps(value)
        return await self.redis.setex(key, ttl, serialized)

    async def get_or_set(
        self,
        key: str,
        factory: Callable,
        ttl: int = 3600
    ) -> Any:
        """Get from cache or execute factory function."""
        cached = await self.get(key)
        if cached is not None:
            return cached

        value = await factory()
        await self.set(key, value, ttl)
        return value
```

### 5.2 Service Interaction Diagram

```
┌─────────────────────────────────────────────────────────┐
│                   API Endpoints                          │
│  POST /api/v1/definitions                               │
│  GET  /api/v1/definitions/{id}                          │
│  POST /api/v1/definitions/{id}/validate                 │
└─────────────┬───────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│            DefinitionOrchestrator                        │
│  • Coordinates 11-phase workflow                        │
│  • Manages dependencies between services                │
└─────┬───────┬───────┬───────┬───────┬──────────────────┘
      │       │       │       │       │
      ▼       ▼       ▼       ▼       ▼
┌─────────┐ ┌────────┐ ┌───────┐ ┌──────┐ ┌──────────┐
│AIService│ │Validate│ │Prompt │ │Cache │ │Repository│
│         │ │Service │ │Service│ │      │ │          │
└────┬────┘ └───┬────┘ └───┬───┘ └───┬──┘ └────┬─────┘
     │          │          │         │         │
     │          │          │         │         │
     ▼          ▼          ▼         ▼         ▼
┌─────────┐ ┌────────┐ ┌───────┐ ┌──────┐ ┌──────────┐
│ OpenAI  │ │46 Rules│ │Template││Redis │ │PostgreSQL│
│   API   │ │Parallel│ │Engine  │      │ │          │
└─────────┘ └────────┘ └────────┘ └──────┘ └──────────┘
```

---

## 6. API Contract Examples

### 6.1 OpenAPI Schema (Auto-Generated by FastAPI)

```yaml
openapi: 3.1.0
info:
  title: DefinitieAgent API
  version: 2.0.0
  description: API for Dutch legal definition generation and validation

paths:
  /api/v1/definitions:
    post:
      summary: Generate a new definition
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/DefinitionRequest'
      responses:
        '200':
          description: Definition generated successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DefinitionResponse'
        '422':
          description: Validation error

components:
  schemas:
    DefinitionRequest:
      type: object
      required:
        - term
        - context
      properties:
        term:
          type: string
          example: "verdachte"
        context:
          $ref: '#/components/schemas/Context'
        options:
          $ref: '#/components/schemas/GenerationOptions'

    Context:
      type: object
      properties:
        organisatorisch:
          type: array
          items:
            type: string
          example: ["OM", "Rechtspraak"]
        juridisch:
          type: array
          items:
            type: string
          example: ["Strafrecht"]
        wettelijk:
          type: array
          items:
            type: string
          example: ["Sv", "Sr"]

    DefinitionResponse:
      type: object
      properties:
        id:
          type: string
          format: uuid
        term:
          type: string
        definition:
          type: string
        quality_score:
          type: number
          minimum: 0
          maximum: 1
        validation_results:
          type: array
          items:
            $ref: '#/components/schemas/ValidationResult'
        created_at:
          type: string
          format: date-time
```

### 6.2 FastAPI Endpoint Implementation

```python
# backend/app/api/v1/definitions.py
from fastapi import APIRouter, Depends, HTTPException
from app.api.dependencies import (
    DefinitionOrchestratorDep,
    DBSessionDep
)
from app.schemas.definition import (
    DefinitionRequest,
    DefinitionResponse,
    ValidationResultResponse
)

router = APIRouter(prefix="/api/v1/definitions", tags=["definitions"])

@router.post("/", response_model=DefinitionResponse, status_code=201)
async def create_definition(
    request: DefinitionRequest,
    orchestrator: DefinitionOrchestratorDep,
    db: DBSessionDep
) -> DefinitionResponse:
    """Generate a new legal definition.

    This endpoint:
    1. Enriches context via web lookup
    2. Checks for duplicates
    3. Generates definition via GPT-4
    4. Validates against 46 rules (parallel)
    5. Calculates quality score
    6. Generates examples and synonyms
    7. Stores in database

    **Performance**: <2s average response time (with caching)
    """
    try:
        result = await orchestrator.generate(
            term=request.term,
            context=request.context,
            options=request.options
        )

        if result.status == "duplicate_found":
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "Similar definitions found",
                    "duplicates": [d.dict() for d in result.duplicates]
                }
            )

        return DefinitionResponse.from_entity(result.definition)

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("Definition generation failed")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{definition_id}", response_model=DefinitionResponse)
async def get_definition(
    definition_id: UUID,
    orchestrator: DefinitionOrchestratorDep
) -> DefinitionResponse:
    """Retrieve a definition by ID."""
    definition = await orchestrator.repository.get_by_id(definition_id)

    if not definition:
        raise HTTPException(status_code=404, detail="Definition not found")

    return DefinitionResponse.from_entity(definition)

@router.post("/{definition_id}/validate", response_model=list[ValidationResultResponse])
async def revalidate_definition(
    definition_id: UUID,
    orchestrator: DefinitionOrchestratorDep
) -> list[ValidationResultResponse]:
    """Re-run validation on an existing definition."""
    definition = await orchestrator.repository.get_by_id(definition_id)

    if not definition:
        raise HTTPException(status_code=404, detail="Definition not found")

    results = await orchestrator.validation_service.validate_parallel(
        definition=definition.definition,
        term=definition.term,
        context=definition.context
    )

    return [ValidationResultResponse.from_entity(r) for r in results]
```

### 6.3 Frontend API Client (TypeScript)

```typescript
// frontend/src/api/definitions.ts
import { apiClient } from './client';

export interface DefinitionRequest {
  term: string;
  context: {
    organisatorisch: string[];
    juridisch: string[];
    wettelijk: string[];
  };
  options?: {
    includeExamples?: boolean;
    includeSynonyms?: boolean;
  };
}

export interface DefinitionResponse {
  id: string;
  term: string;
  definition: string;
  quality_score: number;
  validation_results: ValidationResult[];
  created_at: string;
}

export const definitionsApi = {
  async create(request: DefinitionRequest): Promise<DefinitionResponse> {
    const response = await apiClient.post('/api/v1/definitions', request);
    return response.data;
  },

  async get(id: string): Promise<DefinitionResponse> {
    const response = await apiClient.get(`/api/v1/definitions/${id}`);
    return response.data;
  },

  async search(query: string): Promise<DefinitionResponse[]> {
    const response = await apiClient.get('/api/v1/definitions/search', {
      params: { q: query }
    });
    return response.data;
  },

  async validate(id: string): Promise<ValidationResult[]> {
    const response = await apiClient.post(`/api/v1/definitions/${id}/validate`);
    return response.data;
  }
};
```

### 6.4 React Component Using API

```typescript
// frontend/src/components/DefinitionForm.tsx
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { definitionsApi } from '@/api/definitions';
import { Button } from '@/components/ui/button';

export function DefinitionForm() {
  const queryClient = useQueryClient();

  const createDefinition = useMutation({
    mutationFn: definitionsApi.create,
    onSuccess: (data) => {
      // Invalidate and refetch definitions list
      queryClient.invalidateQueries({ queryKey: ['definitions'] });

      // Show success toast
      toast.success(`Definition for "${data.term}" created successfully!`);
    },
    onError: (error) => {
      toast.error(error.message);
    }
  });

  const handleSubmit = async (values: DefinitionRequest) => {
    createDefinition.mutate(values);
  };

  return (
    <Form onSubmit={handleSubmit}>
      {/* Form fields */}
      <Button
        type="submit"
        disabled={createDefinition.isPending}
      >
        {createDefinition.isPending ? 'Generating...' : 'Generate Definition'}
      </Button>

      {createDefinition.isSuccess && (
        <DefinitionResult data={createDefinition.data} />
      )}
    </Form>
  );
}
```

---

## 7. Developer Experience

### 7.1 Local Development Setup

```bash
# One-command setup with Docker Compose
# docker/docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: definitieagent
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: devpass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  backend:
    build:
      context: ../backend
      dockerfile: ../docker/Dockerfile.backend
    command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    volumes:
      - ../backend:/app
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://dev:devpass@postgres:5432/definitieagent
      REDIS_URL: redis://redis:6379
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    depends_on:
      - postgres
      - redis

  frontend:
    build:
      context: ../frontend
      dockerfile: ../docker/Dockerfile.frontend
    command: npm run dev -- --host 0.0.0.0
    volumes:
      - ../frontend:/app
      - /app/node_modules
    ports:
      - "5173:5173"
    environment:
      VITE_API_URL: http://localhost:8000

volumes:
  postgres_data:
  redis_data:
```

**Developer workflow**:

```bash
# 1. Clone repository
git clone <repo-url>
cd definitie-app

# 2. Copy environment template
cp .env.example .env
# Edit .env and add OPENAI_API_KEY

# 3. Start everything with one command
docker-compose up

# 4. Access application
# - Frontend: http://localhost:5173
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Database: localhost:5432
```

### 7.2 Hot Reload Configuration

**Backend (FastAPI)**: Built-in reload on file changes
```python
# backend/app/main.py
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        reload_dirs=["app"]
    )
```

**Frontend (Vite)**: Sub-100ms HMR
```typescript
// frontend/vite.config.ts
export default defineConfig({
  server: {
    host: '0.0.0.0',
    port: 5173,
    hmr: {
      overlay: true  // Show errors in browser
    }
  },
  plugins: [react()]
});
```

### 7.3 Debugging Setup

**Backend (VSCode)**:
```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI Debug",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
      ],
      "jinja": true,
      "justMyCode": false
    }
  ]
}
```

**Frontend (Browser DevTools)**:
- React DevTools extension
- TanStack Query DevTools (built-in)
- Vite source maps for debugging

### 7.4 Testing Strategy

```bash
# Backend tests (pytest)
cd backend
pytest tests/                     # Run all tests
pytest tests/unit/               # Unit tests only
pytest tests/integration/        # Integration tests
pytest --cov=app --cov-report=html  # Coverage report

# Frontend tests (Vitest)
cd frontend
npm test                         # Run all tests
npm test -- --ui                 # Interactive test UI
npm run test:coverage            # Coverage report

# E2E tests (Playwright)
npx playwright test              # Headless
npx playwright test --ui         # Interactive
```

**Test structure**:
```python
# backend/tests/unit/test_validation_service.py
import pytest
from app.domain.services.validation_service import ValidationService

@pytest.fixture
async def validation_service():
    return ValidationService()

@pytest.mark.asyncio
async def test_validate_parallel_success(validation_service):
    """Test that all 46 rules execute in parallel."""
    definition = "Een verdachte is een persoon die verdacht wordt van een strafbaar feit."

    results = await validation_service.validate_parallel(
        definition=definition,
        term="verdachte",
        context={"juridisch": ["Strafrecht"]}
    )

    assert len(results) == 46
    assert all(r.rule_id for r in results)
    assert all(r.score >= 0 and r.score <= 1 for r in results)
```

### 7.5 Code Quality Tools

```toml
# backend/pyproject.toml
[tool.ruff]
select = ["E", "F", "I", "N", "W", "UP", "ANN", "ASYNC", "S", "B", "A"]
ignore = ["E501"]  # Line too long (handled by black)

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

**Pre-commit hooks**:
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.8
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

---

## 8. Migration Strategy

### 8.1 Reusable Components from Current System

**✅ Can Reuse (65% reduction comes from NOT reusing most code)**:

1. **Validation Rules** (46 rules)
   - JSON metadata files in `config/toetsregels/regels/`
   - Python validation logic (refactor to async)
   - **Migration**: Copy JSON configs, rewrite Python modules as async functions

2. **Database Schema** (concepts)
   - Table structures (migrate to PostgreSQL schema)
   - **Migration**: Use Alembic to create new schema, data migration script

3. **OpenAI Integration Patterns**
   - Prompt templates (cleanup and reorganize)
   - Temperature settings (via ConfigManager)
   - **Migration**: Extract templates to `backend/config/prompts/`, refactor service

4. **Business Logic**
   - Context enrichment patterns
   - Duplicate detection algorithms
   - **Migration**: Extract algorithms, rewrite as pure functions

**❌ Do NOT Reuse**:

1. **Streamlit UI** (complete rewrite with React)
2. **ServiceContainer** (FastAPI dependency injection is different)
3. **Session state management** (anti-pattern, replace with proper state)
4. **Synchronous code** (rewrite as async)
5. **Adapter patterns** (V1/V2 compatibility, no longer needed)

### 8.2 Phased Migration Approach

```
Phase 1: Foundation (Week 1-2)
├── Setup project structure
├── Docker Compose environment
├── FastAPI skeleton + PostgreSQL
├── Migrate database schema
└── Setup CI/CD

Phase 2: Core Services (Week 3-4)
├── Migrate AIService (OpenAI integration)
├── Migrate 46 validation rules (async)
├── Implement caching layer (Redis)
├── DefinitionOrchestrator (11 phases)
└── Unit tests (60% coverage)

Phase 3: API Layer (Week 5-6)
├── REST endpoints (definitions, validation, search)
├── OpenAPI documentation
├── Integration tests
└── Performance testing (<2s target)

Phase 4: Frontend (Week 7-8)
├── React app skeleton (Vite + TypeScript)
├── shadcn/ui components
├── Definition generator page
├── History and search pages
└── Export functionality

Phase 5: Polish & Deploy (Week 9-10)
├── E2E tests (Playwright)
├── Performance optimization (caching, bundling)
├── Documentation
├── Production deployment setup
└── User acceptance testing
```

### 8.3 Data Migration Script

```python
# scripts/migrate_data.py
"""
Migrate data from SQLite to PostgreSQL.

Usage:
    python scripts/migrate_data.py --source data/definities.db --target postgresql://...
"""
import asyncio
import sqlite3
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from backend.app.infrastructure.repositories.definition_repository import DefinitionRepository
from backend.app.domain.entities.definition import Definition

async def migrate_definitions(source_db: str, target_url: str):
    """Migrate definitions from SQLite to PostgreSQL."""

    # Read from SQLite
    conn = sqlite3.connect(source_db)
    cursor = conn.execute("""
        SELECT id, term, definitie, organisatorische_context,
               juridische_context, wettelijke_basis, created_at
        FROM definities
    """)

    definitions = []
    for row in cursor.fetchall():
        definition = Definition(
            term=row[1],
            definition=row[2],
            context={
                "organisatorisch": row[3].split(",") if row[3] else [],
                "juridisch": row[4].split(",") if row[4] else [],
                "wettelijk": row[5].split(",") if row[5] else []
            },
            created_at=row[6]
        )
        definitions.append(definition)

    conn.close()

    # Write to PostgreSQL
    engine = create_async_engine(target_url)
    repository = DefinitionRepository(engine)

    for definition in definitions:
        await repository.save(definition)

    print(f"Migrated {len(definitions)} definitions successfully!")

if __name__ == "__main__":
    import sys
    asyncio.run(migrate_definitions(
        source_db=sys.argv[1],
        target_url=sys.argv[2]
    ))
```

### 8.4 Parallel Development Strategy

**Run Both Systems Simultaneously**:

```
Old System (Streamlit)         New System (FastAPI + React)
├── Keep running for reference ├── Develop in parallel
├── Compare outputs            ├── Test against old system
└── Decommission after UAT     └── Gradual feature parity
```

**Feature parity checklist**:
- [ ] Definition generation (with same quality)
- [ ] 46 validation rules (same results)
- [ ] Context enrichment (Wikipedia/SRU)
- [ ] Duplicate detection
- [ ] Export to JSON/Excel/Markdown
- [ ] Search functionality
- [ ] History tracking
- [ ] Performance: <2s response time

---

## 9. Implementation Roadmap

### 9.1 Sprint Plan (10 weeks)

#### Sprint 1-2: Foundation & Setup
**Goals**: Project structure, dev environment, database
- [x] Project structure setup
- [x] Docker Compose configuration
- [x] FastAPI skeleton + PostgreSQL
- [x] Alembic migrations setup
- [x] CI/CD pipeline (GitHub Actions)
- [x] Development documentation

**Deliverables**:
- Running dev environment (docker-compose up)
- Health check endpoint
- Database migrations working

#### Sprint 3-4: Core Services
**Goals**: Migrate critical business logic
- [ ] AIService (OpenAI integration with retry/cache)
- [ ] ValidationService (46 rules async)
- [ ] PromptService (template rendering)
- [ ] CacheService (Redis integration)
- [ ] DefinitionOrchestrator (11 phases)
- [ ] Unit tests (60% coverage)

**Deliverables**:
- Complete backend service layer
- All tests passing
- Performance benchmark: <2s

#### Sprint 5-6: API Layer
**Goals**: REST endpoints and integration
- [ ] POST /definitions (create)
- [ ] GET /definitions/{id} (retrieve)
- [ ] GET /definitions/search (search)
- [ ] POST /definitions/{id}/validate (revalidate)
- [ ] POST /export (export definitions)
- [ ] OpenAPI documentation auto-gen
- [ ] Integration tests

**Deliverables**:
- Complete REST API
- Swagger docs live
- Postman collection

#### Sprint 7-8: Frontend
**Goals**: Modern React UI
- [ ] Vite + React + TypeScript setup
- [ ] shadcn/ui component library
- [ ] Definition generator page
- [ ] Validation results display
- [ ] History page with search
- [ ] Export page
- [ ] TanStack Query integration

**Deliverables**:
- Complete UI feature parity
- Responsive design
- Loading states & error handling

#### Sprint 9-10: Polish & Deploy
**Goals**: Production-ready system
- [ ] E2E tests (Playwright)
- [ ] Performance optimization (caching, bundling)
- [ ] Documentation (user guide, API docs)
- [ ] Security audit (input validation, rate limiting)
- [ ] Production deployment config
- [ ] User acceptance testing
- [ ] Final migration from old system

**Deliverables**:
- Production-ready application
- Complete documentation
- Deployment runbook

### 9.2 Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Performance** | <2s response time (p95) | Load testing with Locust |
| **Code Quality** | 70% test coverage | pytest-cov |
| **Reliability** | 99.9% uptime | Health check monitoring |
| **Cost** | -70% OpenAI API costs | Caching hit rate tracking |
| **Maintainability** | <30,000 LOC (vs 83,319) | cloc report |
| **Developer Velocity** | <5min local setup | Time from git clone to running app |

### 9.3 Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **OpenAI API changes** | Medium | High | Abstract API client, use SDK versioning |
| **Performance regression** | Low | High | Continuous benchmarking, load tests |
| **Scope creep** | High | Medium | Strict feature freeze after sprint 8 |
| **Migration data loss** | Low | Critical | Automated migration script + validation |
| **Single developer bottleneck** | High | Medium | Good documentation, modular design |

---

## 10. Conclusion

This architecture provides a **modern, performant, maintainable foundation** for DefinitieAgent:

**Key Achievements**:
- ✅ **3-5x faster** (FastAPI vs Streamlit, <2s response time)
- ✅ **65% code reduction** (83,319 → ~30,000 LOC)
- ✅ **Modern stack** (React, FastAPI, PostgreSQL, Redis)
- ✅ **Clean architecture** (testable, scalable, maintainable)
- ✅ **Developer-friendly** (one-command setup, hot reload, great tooling)
- ✅ **Future-proof** (easy to add users, features, integrations)

**Next Steps**:
1. **Review & Approval**: Stakeholder sign-off on architecture
2. **Sprint 1 Kickoff**: Setup foundation (Week 1)
3. **Continuous Delivery**: Deploy incremental improvements
4. **User Feedback**: Early testing with real users (Sprint 6)
5. **Production Cutover**: Complete migration (Week 10)

**Maintainability Focus**:
- Single developer can understand entire system
- Clear separation of concerns (layers, services)
- Comprehensive testing (unit, integration, E2E)
- Auto-generated documentation (OpenAPI, TypeDoc)
- Modern tooling (pre-commit hooks, CI/CD)

This architecture balances **simplicity** (single-developer workflow) with **sophistication** (modern patterns, performance optimization) to create a system that will serve the organization well for years to come.

---

**Document Control**:
- **Version**: 1.0
- **Status**: Proposal
- **Owner**: Senior Full-Stack Architect
- **Last Updated**: 2025-10-02
- **Review Date**: 2025-10-09
