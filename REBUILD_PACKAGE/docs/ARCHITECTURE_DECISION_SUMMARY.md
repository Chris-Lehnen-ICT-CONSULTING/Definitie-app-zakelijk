# Architecture Decision Summary - DefinitieAgent Rebuild

**Quick Reference Guide**
**Date**: 2025-10-02

---

## 🎯 The Problem

- **Current**: Streamlit monolith, 83,319 LOC (65% unused), 8-12s response time
- **Goal**: Modern, fast (<2s), maintainable, single-developer friendly

---

## ✅ The Solution Stack

```
┌─────────────────────────────────────────────────────┐
│                  MODERN STACK                        │
├─────────────────────────────────────────────────────┤
│ Frontend:  React 18 + Vite + TypeScript             │
│ Backend:   FastAPI + Python 3.11 (async)            │
│ Database:  PostgreSQL 16 (SQLite MVP)               │
│ Cache:     Redis 7 (semantic + rate limiting)       │
│ API:       REST (OpenAPI 3.1 auto-docs)             │
│ UI Lib:    shadcn/ui + Tailwind CSS                 │
│ State:     TanStack Query + Zustand                 │
│ Tests:     pytest + Playwright                      │
└─────────────────────────────────────────────────────┘
```

---

## 📊 Why This Stack?

### FastAPI vs Flask/Django
✅ **FastAPI**: 3-5x faster, async-first, auto-docs, type-safe
❌ Flask: No async, slower
❌ Django: Too heavy, monolithic

### React vs Keep Streamlit
✅ **React**: Full UI control, component ecosystem, modern UX
❌ Streamlit: Limited, no concurrent users, slow

### PostgreSQL vs SQLite
✅ **PostgreSQL**: Full-text search, JSONB, concurrent users, production-ready
⚠️ SQLite: OK for MVP, migrate later

### Redis vs No Cache
✅ **Redis**: 70% cost savings (prompt caching), <2s response time
❌ No cache: Slow, expensive OpenAI API calls

---

## 🏗️ Architecture Layers

```
┌───────────────────────────────────────────────┐
│  PRESENTATION LAYER                           │
│  React (UI) + FastAPI (REST endpoints)        │
└───────────┬───────────────────────────────────┘
            │
┌───────────▼───────────────────────────────────┐
│  APPLICATION LAYER                            │
│  Orchestrators (Definition, Validation)       │
└───────────┬───────────────────────────────────┘
            │
┌───────────▼───────────────────────────────────┐
│  DOMAIN LAYER                                 │
│  Services: AI, Validation, Prompt, Cache      │
│  Entities: Definition, Context, Result        │
└───────────┬───────────────────────────────────┘
            │
┌───────────▼───────────────────────────────────┐
│  INFRASTRUCTURE LAYER                         │
│  PostgreSQL + Redis + OpenAI API              │
└───────────────────────────────────────────────┘
```

**Key Principles**:
- **Clean Architecture**: Domain logic independent of frameworks
- **Dependency Injection**: FastAPI's native DI (no complex frameworks)
- **Async-First**: All I/O operations async (OpenAI, DB, Redis)
- **Stateless Services**: No session_state anti-pattern!

---

## ⚡ Performance Strategy

| Optimization | Current | Target | How |
|--------------|---------|--------|-----|
| **Response Time** | 8-12s | <2s | Async + caching + parallel validation |
| **API Calls** | Every request | 70% cached | Redis semantic caching |
| **Validation** | Sequential | Parallel | 46 rules in asyncio.gather() |
| **Database** | N+1 queries | Optimized | Eager loading, proper indexes |
| **Frontend** | N/A | <1s load | Code splitting, lazy loading |

---

## 📁 Project Structure

```
definitie-app/
├── backend/                   # FastAPI backend
│   ├── app/
│   │   ├── api/v1/           # REST endpoints
│   │   ├── domain/           # Business logic
│   │   │   ├── entities/     # Definition, Context
│   │   │   └── services/     # AI, Validation, Prompt
│   │   ├── infrastructure/   # DB, Cache, External APIs
│   │   └── schemas/          # Pydantic DTOs
│   ├── tests/                # pytest tests
│   ├── config/               # Validation rules, prompts
│   └── pyproject.toml        # Poetry dependencies
│
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── api/             # API client
│   │   ├── components/      # React components (shadcn/ui)
│   │   ├── pages/           # Page components
│   │   ├── hooks/           # Custom hooks
│   │   └── store/           # Zustand state
│   ├── package.json
│   └── vite.config.ts
│
└── docker/
    └── docker-compose.yml    # Local dev environment
```

---

## 🔄 Migration Strategy

### What to Reuse ✅
- 46 validation rules (JSON configs + refactored Python)
- Database schema concepts (migrate to PostgreSQL)
- Prompt templates (cleanup and reorganize)
- Business logic (extract as pure functions)

### What to Rewrite ❌
- Streamlit UI → React
- ServiceContainer → FastAPI DI
- Session state → Proper state management
- Sync code → Async
- V1/V2 adapters → Single modern implementation

### Phased Approach (10 weeks)
```
Week 1-2:  Foundation (Docker, FastAPI, PostgreSQL)
Week 3-4:  Core Services (AI, Validation, Orchestrator)
Week 5-6:  API Layer (REST endpoints, OpenAPI docs)
Week 7-8:  Frontend (React, shadcn/ui, TanStack Query)
Week 9-10: Polish & Deploy (E2E tests, optimization, UAT)
```

---

## 🎯 Success Criteria

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **Performance** | <2s response (p95) | Load testing (Locust) |
| **Code Size** | <30,000 LOC | cloc (65% reduction) |
| **Test Coverage** | 70%+ | pytest-cov |
| **API Cost** | -70% OpenAI | Cache hit rate tracking |
| **Developer Setup** | <5 min | Time: git clone → running app |
| **Uptime** | 99.9% | Health check monitoring |

---

## 🛠️ Developer Experience

### One-Command Setup
```bash
docker-compose up
# ✅ Backend: http://localhost:8000
# ✅ Frontend: http://localhost:5173
# ✅ API Docs: http://localhost:8000/docs
# ✅ PostgreSQL: localhost:5432
# ✅ Redis: localhost:6379
```

### Hot Reload
- **Backend**: Uvicorn auto-reload on file change
- **Frontend**: Vite HMR (<100ms updates)

### Testing
```bash
# Backend
pytest tests/                    # All tests
pytest --cov=app                # Coverage

# Frontend
npm test                        # Vitest
npx playwright test             # E2E tests
```

---

## 🚀 Key Advantages

1. **Performance**: 3-5x faster (FastAPI vs Streamlit)
2. **Maintainability**: 65% less code, clean architecture
3. **Developer Joy**: Modern tools, hot reload, great DX
4. **Future-Proof**: Easy to add users, features, integrations
5. **Cost Efficient**: 70% lower OpenAI costs via caching
6. **Testability**: Clean architecture, 70%+ coverage
7. **Documentation**: Auto-generated OpenAPI docs

---

## 📝 Example API Endpoint

```python
# backend/app/api/v1/definitions.py
@router.post("/", response_model=DefinitionResponse)
async def create_definition(
    request: DefinitionRequest,
    orchestrator: DefinitionOrchestratorDep,  # DI
    db: DBSessionDep
) -> DefinitionResponse:
    """Generate definition (<2s with caching).

    Workflow:
    1. Context enrichment (web lookup)
    2. Duplicate detection
    3. AI generation (GPT-4, cached)
    4. 46 validation rules (parallel)
    5. Quality scoring
    6. Examples + synonyms
    7. Persistence
    """
    result = await orchestrator.generate(
        term=request.term,
        context=request.context
    )
    return DefinitionResponse.from_entity(result.definition)
```

```typescript
// frontend/src/api/definitions.ts
export const definitionsApi = {
  async create(request: DefinitionRequest): Promise<DefinitionResponse> {
    const response = await apiClient.post('/api/v1/definitions', request);
    return response.data;
  }
};

// frontend/src/components/DefinitionForm.tsx
const createDefinition = useMutation({
  mutationFn: definitionsApi.create,
  onSuccess: (data) => {
    queryClient.invalidateQueries(['definitions']);
    toast.success('Definition created!');
  }
});
```

---

## 🎓 Key Learnings

### Anti-Patterns to Avoid
❌ **Session State Management**: Streamlit's st.session_state caused major issues
✅ **Solution**: Stateless services + proper frontend state management

❌ **Backward Compatibility**: V1/V2 adapters added complexity
✅ **Solution**: Clean rebuild, no legacy baggage

❌ **Monolithic Services**: God objects with unclear responsibilities
✅ **Solution**: Single Responsibility Principle, clear service boundaries

### Best Practices
✅ **Async-First**: All I/O operations async (3-5x speedup)
✅ **Caching Strategy**: Three-tier (LRU, Redis, DB)
✅ **Type Safety**: Pydantic (backend) + TypeScript (frontend)
✅ **Parallel Execution**: 46 validation rules in parallel
✅ **Clean Architecture**: Domain logic independent of frameworks

---

## 📚 Next Steps

1. **Review**: Stakeholder approval of architecture
2. **Setup**: Sprint 1 - Foundation & Docker environment
3. **Develop**: Sprints 2-8 - Core services + API + Frontend
4. **Test**: Sprint 9 - E2E tests, performance tuning
5. **Deploy**: Sprint 10 - Production deployment, UAT
6. **Cutover**: Migrate from old system

---

## 📖 Full Documentation

See: `/Users/chrislehnen/Projecten/Definitie-app/docs/architectuur/MODERN_REBUILD_ARCHITECTURE.md`

**Includes**:
- Detailed tech stack rationale
- Complete service boundaries & contracts
- API examples (OpenAPI schemas)
- Database schema design
- Caching strategy details
- Migration scripts
- 10-week implementation roadmap

---

**Document Info**:
- **Version**: 1.0
- **Date**: 2025-10-02
- **Author**: Senior Full-Stack Architect
- **Status**: Proposal
