# DefinitieAgent Rebuild Timeline

**Document Status**: Planning
**Created**: 2025-10-02
**Owner**: Technical Architecture Team
**Target Audience**: Stakeholders, Development Team

---

## Executive Summary

**Mission**: Rebuild DefinitieAgent from 83k LOC legacy Streamlit monolith to modern ~25k LOC FastAPI/React architecture with PostgreSQL.

**Timeline**: 10-14 weeks (vs 15-20 weeks refactor)
**Advantage**: 25-40% faster, cleaner architecture, no technical debt
**Risk Level**: Medium (mitigated by phased rollout with decision gates)

### Key Numbers

| Metric | Current | Target | Reduction |
|--------|---------|--------|-----------|
| **Total LOC** | 83,000 | ~25,000 | 70% |
| **Python Files** | 321 | ~80 | 75% |
| **Business Logic** | 46 rules + orchestrators | 46 rules (extracted) | Clean separation |
| **UI Components** | 37 Streamlit tabs | ~15 React components | Modern stack |
| **Timeline** | 15-20 weeks (refactor) | 10-14 weeks (rebuild) | 30% faster |

---

## Phase Breakdown

### Phase 0: Business Logic Extraction (Weeks 1-2)
**Duration**: 2 weeks
**Critical**: This is foundation - must be complete before proceeding
**Deliverable**: Documented, version-controlled business rules

### Phase 1: Modern Stack Setup (Weeks 3-4)
**Duration**: 2 weeks
**Deliverable**: Working infrastructure with CI/CD

### Phase 2: Core Features MVP (Weeks 5-7)
**Duration**: 3 weeks
**Deliverable**: Basic definition generation + validation working

### Phase 3: Advanced Features (Weeks 8-10)
**Duration**: 3 weeks
**Deliverable**: Full feature parity with legacy system

### Phase 4: Testing & Migration (Weeks 11-12)
**Duration**: 2 weeks
**Deliverable**: Production-ready system with data migration

### Phase 5: Go-Live & Documentation (Weeks 13-14)
**Duration**: 2 weeks (buffer)
**Deliverable**: Live system with full documentation

---

## Detailed Week-by-Week Plan

## PHASE 0: Business Logic Extraction (Foundation)

### Week 1: Validation Rules Extraction

**Goal**: Extract and document all 46 validation rules as pure business logic

**Tasks**:
- [ ] Audit all 46 validation rule files (`src/toetsregels/regels/*.py`)
- [ ] Extract business logic from each rule (remove Streamlit/tech dependencies)
- [ ] Document rule logic in declarative format (JSON schemas + Python functions)
- [ ] Create rule test fixtures with input/output examples
- [ ] Version control: Git tag `business-logic-v1.0-rules`

**Deliverables**:
```
docs/business-logic/
├── validation-rules/
│   ├── ARAI-01.md          # Business logic documentation
│   ├── ARAI-01.json        # Rule metadata
│   ├── ARAI-01-tests.json  # Test cases
│   └── [... 45 more rules]
└── validation-rules-index.md
```

**Success Criteria**:
- [ ] All 46 rules documented with business logic separated from tech
- [ ] Each rule has 3+ test cases (pass/fail/edge case)
- [ ] Business stakeholder review completed
- [ ] No hardcoded Streamlit/SQLite references in rule logic

**Time Allocation**:
- Rule audit: 2 days
- Extraction: 2 days
- Documentation: 1 day

---

### Week 2: Orchestrator & Workflow Logic Extraction

**Goal**: Extract orchestration logic and hardcoded business rules

**Tasks**:
- [ ] Extract logic from `ValidationOrchestratorV2` (251 LOC)
- [ ] Extract logic from `DefinitionOrchestratorV2` (11-phase flow)
- [ ] Document hardcoded business rules (currently ~250 LOC scattered)
- [ ] Map orchestration flows as state machines/workflow diagrams
- [ ] Create integration test scenarios
- [ ] Version control: Git tag `business-logic-v1.0-complete`

**Deliverables**:
```
docs/business-logic/
├── orchestration/
│   ├── validation-flow.md       # ValidationOrchestratorV2 logic
│   ├── definition-flow.md       # DefinitionOrchestratorV2 logic
│   ├── state-machine.mermaid    # Workflow diagrams
│   └── integration-tests.json   # End-to-end scenarios
├── hardcoded-rules/
│   ├── approval-gate-policy.md  # EPIC-016 logic
│   ├── context-validation.md    # Context-specific rules
│   └── quality-thresholds.md    # Quality scoring logic
└── business-logic-index.md      # Master index
```

**Success Criteria**:
- [ ] Orchestration flows documented as tech-agnostic workflows
- [ ] All hardcoded rules extracted and categorized
- [ ] Integration test scenarios defined (10+ scenarios)
- [ ] **DECISION GATE**: Business logic complete? (Go/No-Go)

**Decision Gate Criteria**:
- ✅ 100% business rules documented
- ✅ Stakeholder sign-off on completeness
- ✅ Test coverage plan approved
- ❌ Abort if: <90% rules extracted OR stakeholder concerns

**Time Allocation**:
- Orchestrator extraction: 2 days
- Hardcoded rules: 2 days
- Documentation + review: 1 day

---

## PHASE 1: Modern Stack Setup (Infrastructure)

### Week 3: Backend Infrastructure

**Goal**: FastAPI + PostgreSQL foundation with CI/CD

**Tasks**:
- [ ] Setup FastAPI project structure
- [ ] Configure PostgreSQL database (Docker Compose)
- [ ] Implement database schema (from legacy SQLite schema)
- [ ] Setup Alembic migrations
- [ ] Configure Poetry dependency management
- [ ] Setup pytest infrastructure
- [ ] GitHub Actions CI/CD pipeline
- [ ] Docker containerization (dev + prod)

**Deliverables**:
```
rebuild/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Configuration
│   │   ├── database.py          # Database setup
│   │   └── __init__.py
│   ├── alembic/                 # Migrations
│   ├── tests/                   # Test infrastructure
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── docker-compose.yml
├── .github/
│   └── workflows/
│       └── ci.yml               # CI/CD pipeline
└── README.md
```

**Success Criteria**:
- [ ] FastAPI app starts successfully
- [ ] PostgreSQL connection works
- [ ] Alembic migrations run cleanly
- [ ] CI/CD pipeline passes (lint + test + build)
- [ ] Docker containers build and run

**Time Allocation**:
- FastAPI setup: 1 day
- PostgreSQL + migrations: 1 day
- CI/CD + Docker: 1.5 days
- Testing infrastructure: 1.5 days

---

### Week 4: Frontend Infrastructure + AI Service

**Goal**: React frontend + OpenAI integration

**Tasks**:
- [ ] Setup Vite + React + TypeScript
- [ ] Configure Tailwind CSS
- [ ] Implement authentication (JWT)
- [ ] Setup React Router
- [ ] Configure API client (Axios/Fetch)
- [ ] Implement OpenAI service (backend)
- [ ] Create API contracts (OpenAPI/Swagger)
- [ ] Setup environment configuration

**Deliverables**:
```
rebuild/
├── frontend/
│   ├── src/
│   │   ├── main.tsx            # App entry
│   │   ├── App.tsx             # Root component
│   │   ├── api/                # API client
│   │   ├── components/         # Shared components
│   │   ├── pages/              # Page components
│   │   └── hooks/              # Custom hooks
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── Dockerfile
├── backend/
│   └── app/
│       ├── api/                # API routes
│       ├── services/
│       │   └── ai_service.py   # OpenAI integration
│       └── schemas/            # Pydantic schemas
└── docs/
    └── api/
        └── openapi.json        # API specification
```

**Success Criteria**:
- [ ] React app runs in dev mode
- [ ] Authentication flow works end-to-end
- [ ] API client connects to backend
- [ ] OpenAI service makes successful API calls
- [ ] OpenAPI docs generated and accessible

**Time Allocation**:
- React setup: 1.5 days
- Auth + routing: 1 day
- API integration: 1 day
- OpenAI service: 1.5 days

---

## PHASE 2: Core Features MVP (Basic Functionality)

### Week 5: Validation Engine

**Goal**: Implement 46 validation rules in modern architecture

**Tasks**:
- [ ] Implement validation rule engine (backend)
- [ ] Port all 46 validation rules from extracted logic
- [ ] Create rule execution framework (async/parallel)
- [ ] Implement validation result aggregation
- [ ] Build validation API endpoints
- [ ] Write unit tests for each rule
- [ ] Create validation UI component (basic)

**Deliverables**:
```
rebuild/backend/app/
├── validation/
│   ├── engine.py               # Rule execution engine
│   ├── rules/
│   │   ├── base.py            # Base rule class
│   │   ├── arai_01.py         # Rule implementations
│   │   └── [... 45 more]
│   ├── aggregator.py          # Result aggregation
│   └── schemas.py             # Validation schemas
├── api/
│   └── validation.py          # Validation endpoints
└── tests/
    └── validation/
        └── test_rules.py      # Rule tests (46 rules)

rebuild/frontend/src/
├── components/
│   └── ValidationResults.tsx  # Basic UI
└── pages/
    └── ValidationPage.tsx     # Validation page
```

**Success Criteria**:
- [ ] All 46 rules execute successfully
- [ ] Rules run in parallel (performance boost)
- [ ] API returns validation results in <2s
- [ ] Unit test coverage >90% for rules
- [ ] UI displays validation results correctly

**Time Allocation**:
- Engine framework: 1 day
- Rule implementation: 2 days
- API + tests: 1 day
- UI component: 1 day

---

### Week 6: Definition Generator (Core)

**Goal**: Basic definition generation working end-to-end

**Tasks**:
- [ ] Implement prompt service (from extracted logic)
- [ ] Build definition generator API
- [ ] Create context management
- [ ] Implement quality scoring
- [ ] Build generation UI (form + results)
- [ ] Integration tests (generation → validation)
- [ ] Performance optimization (caching)

**Deliverables**:
```
rebuild/backend/app/
├── generation/
│   ├── prompt_service.py      # Prompt building
│   ├── generator.py           # Core generator
│   ├── context_manager.py     # Context handling
│   └── quality_scorer.py      # Quality scoring
├── api/
│   └── definitions.py         # Definition endpoints
└── tests/
    └── generation/
        └── test_integration.py # End-to-end tests

rebuild/frontend/src/
├── components/
│   ├── DefinitionForm.tsx     # Input form
│   └── DefinitionResult.tsx   # Result display
└── pages/
    └── GeneratePage.tsx       # Main generation page
```

**Success Criteria**:
- [ ] Generate definition from user input
- [ ] Validation runs automatically on generated text
- [ ] Results display with quality score
- [ ] Response time <5s (target: 3s)
- [ ] **DECISION GATE**: MVP validates? (Continue/Pivot)

**Decision Gate Criteria**:
- ✅ Core flow works (generate → validate → display)
- ✅ Performance acceptable (<5s)
- ✅ Quality comparable to legacy system
- ⚠️ Pivot if: Performance >10s OR quality issues
- ❌ Abort if: Core flow fundamentally broken

**Time Allocation**:
- Generator logic: 2 days
- API + context: 1 day
- UI: 1.5 days
- Integration + optimization: 0.5 day

---

### Week 7: Repository & Data Layer

**Goal**: Database operations + search functionality

**Tasks**:
- [ ] Implement definition repository (CRUD)
- [ ] Build search service (full-text)
- [ ] Create history/audit logging
- [ ] Implement version control for definitions
- [ ] Build history UI
- [ ] Add filters and sorting
- [ ] Performance optimization (indexing)

**Deliverables**:
```
rebuild/backend/app/
├── repository/
│   ├── definition_repo.py     # CRUD operations
│   ├── search_service.py      # Search functionality
│   └── audit_logger.py        # Audit trail
├── models/
│   ├── definition.py          # SQLAlchemy model
│   └── audit_log.py           # Audit model
└── tests/
    └── repository/
        └── test_crud.py       # Repository tests

rebuild/frontend/src/
├── components/
│   ├── DefinitionList.tsx     # List view
│   └── SearchBar.tsx          # Search component
└── pages/
    └── HistoryPage.tsx        # History page
```

**Success Criteria**:
- [ ] CRUD operations work correctly
- [ ] Search returns relevant results (<500ms)
- [ ] Audit trail captures all changes
- [ ] History UI shows all saved definitions
- [ ] Pagination works for large datasets

**Time Allocation**:
- Repository implementation: 1.5 days
- Search service: 1 day
- Audit logging: 0.5 day
- UI + tests: 2 days

---

## PHASE 3: Advanced Features (Feature Parity)

### Week 8: Web Lookup & Enrichment

**Goal**: External data sources integration

**Tasks**:
- [ ] Port ModernWebLookupService logic
- [ ] Implement Wikipedia integration
- [ ] Implement SRU (legal database) integration
- [ ] Build enrichment orchestrator
- [ ] Create caching layer (Redis)
- [ ] Implement timeout handling
- [ ] Build enrichment UI

**Deliverables**:
```
rebuild/backend/app/
├── enrichment/
│   ├── web_lookup_service.py  # Main service
│   ├── providers/
│   │   ├── wikipedia.py      # Wikipedia provider
│   │   └── sru.py            # SRU provider
│   ├── cache_service.py       # Redis caching
│   └── enrichment_orchestrator.py
├── tests/
│   └── enrichment/
│       └── test_providers.py  # Provider tests
└── docker-compose.yml         # Add Redis

rebuild/frontend/src/
├── components/
│   └── EnrichmentPanel.tsx    # Enrichment UI
└── pages/
    └── EnrichPage.tsx         # Enrichment page
```

**Success Criteria**:
- [ ] Wikipedia lookups work (timeout <5s)
- [ ] SRU integration functional
- [ ] Cache reduces API calls by >70%
- [ ] Enrichment results improve definition quality
- [ ] UI allows manual enrichment triggers

**Time Allocation**:
- Web lookup service: 2 days
- Caching layer: 1 day
- UI + integration: 2 days

---

### Week 9: Export & Document Handling

**Goal**: Export to multiple formats + document processing

**Tasks**:
- [ ] Implement JSON export
- [ ] Implement DOCX export (python-docx)
- [ ] Implement PDF export
- [ ] Build export templates
- [ ] Create document upload handler
- [ ] Implement text extraction (DOCX/PDF)
- [ ] Build export/import UI

**Deliverables**:
```
rebuild/backend/app/
├── export/
│   ├── export_service.py      # Main export service
│   ├── formatters/
│   │   ├── json_formatter.py # JSON export
│   │   ├── docx_formatter.py # DOCX export
│   │   └── pdf_formatter.py  # PDF export
│   └── templates/            # Export templates
├── import/
│   ├── document_processor.py  # Document handling
│   └── text_extractor.py      # Text extraction
└── tests/
    └── export/
        └── test_formatters.py # Export tests

rebuild/frontend/src/
├── components/
│   ├── ExportOptions.tsx      # Export options
│   └── FileUpload.tsx         # Upload component
└── pages/
    └── ExportPage.tsx         # Export/import page
```

**Success Criteria**:
- [ ] Export to JSON/DOCX/PDF works
- [ ] Exports maintain formatting and metadata
- [ ] Document upload and text extraction works
- [ ] Export speed <2s per definition
- [ ] UI provides clear export options

**Time Allocation**:
- Export service: 2 days
- Document processing: 1.5 days
- UI + tests: 1.5 days

---

### Week 10: Advanced Validation Features

**Goal**: Expert review, quality gates, configuration UI

**Tasks**:
- [ ] Implement approval gate policy (from EPIC-016)
- [ ] Build expert review workflow
- [ ] Create configuration UI for validation rules
- [ ] Implement rule enable/disable functionality
- [ ] Build quality threshold management
- [ ] Create validation analytics dashboard
- [ ] Performance optimization

**Deliverables**:
```
rebuild/backend/app/
├── validation/
│   ├── approval_gate.py       # Approval policy
│   ├── expert_review.py       # Review workflow
│   └── config_manager.py      # Rule configuration
├── api/
│   └── admin.py               # Admin endpoints
└── tests/
    └── validation/
        └── test_approval.py   # Approval tests

rebuild/frontend/src/
├── components/
│   ├── ApprovalGate.tsx       # Approval UI
│   ├── RuleConfig.tsx         # Rule configuration
│   └── Analytics.tsx          # Analytics dashboard
└── pages/
    ├── AdminPage.tsx          # Admin panel
    └── AnalyticsPage.tsx      # Analytics page
```

**Success Criteria**:
- [ ] Approval gate enforces quality thresholds
- [ ] Expert review workflow functional
- [ ] Rules can be configured via UI
- [ ] Analytics show validation trends
- [ ] **DECISION GATE**: Feature parity? (Ship/Extend)

**Decision Gate Criteria**:
- ✅ All legacy features implemented
- ✅ Performance matches or exceeds legacy
- ✅ User acceptance testing passed
- ⚠️ Extend if: Minor features missing (1-2 weeks)
- ❌ Abort if: Major functionality gaps

**Time Allocation**:
- Approval gate: 1.5 days
- Expert review: 1 day
- Configuration UI: 1.5 days
- Analytics + optimization: 1 day

---

## PHASE 4: Testing & Migration (Production Readiness)

### Week 11: Comprehensive Testing

**Goal**: Full test coverage + performance testing

**Tasks**:
- [ ] Increase unit test coverage to >80%
- [ ] Write integration tests for all flows
- [ ] End-to-end tests with Playwright
- [ ] Load testing with Locust (100+ concurrent users)
- [ ] Security testing (OWASP top 10)
- [ ] Accessibility testing (WCAG 2.1)
- [ ] Performance benchmarking
- [ ] Fix all critical bugs

**Deliverables**:
```
rebuild/
├── backend/tests/
│   ├── unit/              # Unit tests (>80% coverage)
│   ├── integration/       # Integration tests
│   └── load/
│       └── locustfile.py  # Load test scenarios
├── frontend/tests/
│   ├── unit/              # Jest tests
│   └── e2e/
│       └── *.spec.ts      # Playwright tests
└── docs/
    └── testing/
        ├── test-plan.md       # Test strategy
        ├── test-results.md    # Test results
        └── performance-report.md
```

**Success Criteria**:
- [ ] Unit test coverage >80%
- [ ] Integration tests cover all user flows
- [ ] E2E tests pass (10+ scenarios)
- [ ] Load test: 100 concurrent users with <5s response
- [ ] No critical security vulnerabilities
- [ ] WCAG 2.1 AA compliance

**Time Allocation**:
- Unit tests: 2 days
- Integration + E2E: 1.5 days
- Load + security testing: 1 day
- Bug fixes: 0.5 day

---

### Week 12: Data Migration & Deployment Prep

**Goal**: Migrate data from legacy system + deployment infrastructure

**Tasks**:
- [ ] Create SQLite → PostgreSQL migration script
- [ ] Validate data integrity after migration
- [ ] Setup production infrastructure (AWS/GCP)
- [ ] Configure production database
- [ ] Setup Redis for caching
- [ ] Configure monitoring (Prometheus + Grafana)
- [ ] Setup logging (ELK stack or similar)
- [ ] Create deployment runbooks
- [ ] Dry-run deployment to staging

**Deliverables**:
```
rebuild/
├── migrations/
│   ├── migrate_sqlite_to_postgres.py
│   └── validate_migration.py
├── infrastructure/
│   ├── terraform/         # IaC for cloud resources
│   ├── kubernetes/        # K8s manifests
│   └── docker-compose.prod.yml
├── monitoring/
│   ├── prometheus.yml     # Prometheus config
│   └── grafana/           # Grafana dashboards
└── docs/
    └── deployment/
        ├── runbook.md         # Deployment procedures
        └── rollback.md        # Rollback procedures
```

**Success Criteria**:
- [ ] All legacy data migrated successfully
- [ ] Data validation: 100% integrity
- [ ] Production infrastructure provisioned
- [ ] Monitoring dashboards operational
- [ ] Staging deployment successful
- [ ] Rollback procedure tested

**Time Allocation**:
- Migration script: 1.5 days
- Infrastructure setup: 2 days
- Monitoring + logging: 1 day
- Staging deployment: 0.5 day

---

## PHASE 5: Go-Live & Documentation (Launch)

### Week 13: Production Deployment

**Goal**: Go-live with production system

**Tasks**:
- [ ] Final production deployment
- [ ] Smoke tests on production
- [ ] Performance monitoring (first 24h)
- [ ] User training sessions
- [ ] Create user documentation
- [ ] Setup support channels
- [ ] Monitor error rates and performance
- [ ] Hot-fix any critical issues

**Deliverables**:
```
rebuild/
└── docs/
    ├── user-guide/
    │   ├── getting-started.md
    │   ├── features.md
    │   └── faq.md
    ├── admin-guide/
    │   ├── configuration.md
    │   ├── maintenance.md
    │   └── troubleshooting.md
    └── deployment/
        ├── production-deployment.md
        └── post-deployment-checklist.md
```

**Success Criteria**:
- [ ] Production system live and stable
- [ ] No critical errors in first 24h
- [ ] Response times <5s (p95)
- [ ] User training completed
- [ ] Support team ready
- [ ] Documentation complete

**Time Allocation**:
- Deployment: 1 day
- Monitoring + fixes: 2 days
- Training + docs: 2 days

---

### Week 14: Buffer & Handover

**Goal**: Buffer week for unexpected issues + formal handover

**Tasks**:
- [ ] Address any production issues
- [ ] Performance tuning
- [ ] Complete technical documentation
- [ ] Create architecture diagrams
- [ ] Knowledge transfer sessions
- [ ] Post-mortem analysis
- [ ] Plan future enhancements
- [ ] Formal project closure

**Deliverables**:
```
rebuild/
└── docs/
    ├── architecture/
    │   ├── system-architecture.md
    │   ├── data-model.md
    │   └── api-reference.md
    ├── development/
    │   ├── setup-guide.md
    │   ├── contribution-guide.md
    │   └── coding-standards.md
    └── project/
        ├── post-mortem.md
        ├── lessons-learned.md
        └── future-roadmap.md
```

**Success Criteria**:
- [ ] All documentation complete
- [ ] Knowledge transfer completed
- [ ] Team can maintain system independently
- [ ] Post-mortem conducted
- [ ] Future roadmap defined

**Time Allocation**:
- Issue resolution: 2 days
- Documentation: 2 days
- Knowledge transfer: 1 day

---

## Milestone Definitions

### Milestone 1: Business Logic Documented (Week 2)
**Checkpoint**: Foundation for rebuild

**Deliverables**:
- 46 validation rules documented
- Orchestration flows mapped
- Hardcoded rules extracted
- Test scenarios defined

**Success Criteria**:
- 100% business logic extracted
- Stakeholder sign-off
- Test coverage plan approved

**Go/No-Go Decision**:
- ✅ GO: All criteria met, proceed to Phase 1
- ❌ NO-GO: <90% extraction, stakeholder concerns → extend Phase 0

---

### Milestone 2: MVP Working (Week 6)
**Checkpoint**: Core functionality proven

**Deliverables**:
- FastAPI + React infrastructure
- Validation engine (46 rules)
- Basic definition generator
- PostgreSQL integration

**Success Criteria**:
- Core flow works (generate → validate)
- Performance <5s
- Quality comparable to legacy

**Go/No-Go Decision**:
- ✅ GO: MVP validates, continue to Phase 3
- ⚠️ PIVOT: Performance/quality issues → adjust architecture
- ❌ NO-GO: Core flow broken → reconsider rebuild

---

### Milestone 3: Feature Parity (Week 10)
**Checkpoint**: Ready for testing

**Deliverables**:
- All legacy features implemented
- Advanced validation features
- Export/import functionality
- Web lookup integration

**Success Criteria**:
- Feature parity achieved
- Performance matches/exceeds legacy
- User acceptance testing passed

**Go/No-Go Decision**:
- ✅ GO: Ship to production testing
- ⚠️ EXTEND: Minor features missing (add 1-2 weeks)
- ❌ NO-GO: Major functionality gaps → reassess scope

---

### Milestone 4: Production Ready (Week 12)
**Checkpoint**: Launch readiness

**Deliverables**:
- Test coverage >80%
- Data migration complete
- Infrastructure provisioned
- Monitoring operational

**Success Criteria**:
- All tests passing
- Data integrity validated
- Staging deployment successful
- Rollback procedure tested

**Go/No-Go Decision**:
- ✅ GO: Launch to production
- ⚠️ DELAY: Test failures → fix and retest
- ❌ NO-GO: Critical issues → postpone launch

---

## Decision Point Framework

### Decision Point 1: Week 2 - Business Logic Complete?

**Question**: Do we have complete, validated business logic?

**Criteria**:
- ✅ 100% validation rules extracted
- ✅ Orchestration logic documented
- ✅ Stakeholder approval received
- ✅ Test scenarios defined

**Outcomes**:
- **GO**: Proceed to Phase 1 (infrastructure setup)
- **EXTEND**: Add 1 week if 90-99% complete
- **ABORT**: <90% complete OR major stakeholder concerns

**Abort Consequences**: Return to refactor approach

---

### Decision Point 2: Week 6 - MVP Validates?

**Question**: Does the core flow work acceptably?

**Criteria**:
- ✅ Generate → validate flow works end-to-end
- ✅ Performance <5s (target: 3s)
- ✅ Quality score comparable to legacy (±10%)
- ✅ No critical bugs

**Outcomes**:
- **CONTINUE**: Proceed to Phase 3 (advanced features)
- **PIVOT**: Adjust architecture if performance/quality issues (add 1-2 weeks)
- **ABORT**: Core flow fundamentally broken (>10s OR quality issues)

**Abort Consequences**: 6 weeks invested, switch to refactor approach

---

### Decision Point 3: Week 10 - Feature Parity?

**Question**: Have we achieved feature parity with legacy?

**Criteria**:
- ✅ All legacy features implemented
- ✅ Performance matches or exceeds legacy
- ✅ User acceptance testing passed
- ✅ No major feature gaps

**Outcomes**:
- **SHIP**: Proceed to testing & deployment (Phase 4)
- **EXTEND**: Minor features missing (add 1-2 weeks)
- **ABORT**: Major functionality gaps (>20% features missing)

**Abort Consequences**: 10 weeks invested, consider hybrid approach

---

### Decision Point 4: Week 12 - Production Ready?

**Question**: Is the system ready for production launch?

**Criteria**:
- ✅ Test coverage >80%
- ✅ Load testing passed (100 concurrent users)
- ✅ Data migration successful
- ✅ Infrastructure stable

**Outcomes**:
- **LAUNCH**: Go-live in Week 13
- **DELAY**: Test failures or migration issues (add 1 week)
- **POSTPONE**: Critical issues found (reassess timeline)

**Postpone Consequences**: Extend timeline but stay on rebuild path

---

## Resource Planning

### Development Time Allocation

**Total Weeks**: 14 weeks
**Total Development Days**: 70 days (14 weeks × 5 days)

| Phase | Weeks | Days | % of Total |
|-------|-------|------|------------|
| **Phase 0: Business Logic** | 2 | 10 | 14% |
| **Phase 1: Infrastructure** | 2 | 10 | 14% |
| **Phase 2: Core MVP** | 3 | 15 | 21% |
| **Phase 3: Advanced Features** | 3 | 15 | 21% |
| **Phase 4: Testing & Migration** | 2 | 10 | 14% |
| **Phase 5: Go-Live** | 2 | 10 | 14% |
| **Buffer** | Distributed | - | Built-in |

---

### Learning Curve Budget

**New Technologies**: FastAPI, React, PostgreSQL
**Current Stack**: Streamlit, SQLite

| Technology | Learning Time | Mitigation |
|------------|---------------|------------|
| **FastAPI** | 3 days | Extensive docs, similar to Flask |
| **React + TypeScript** | 5 days | Use component library (shadcn/ui) |
| **PostgreSQL** | 2 days | Similar to SQLite, well-documented |
| **Docker/K8s** | 3 days | Use templates, focus on basics |
| **Testing (Playwright)** | 2 days | Good documentation, intuitive API |
| **Total** | 15 days | Integrated into phases |

**Strategy**: Learning is integrated into implementation weeks (not separate)

---

### Testing Time Allocation

| Test Type | Phase | Days | Coverage |
|-----------|-------|------|----------|
| **Unit Tests** | Weeks 5-11 | 10 days | >80% coverage |
| **Integration Tests** | Week 11 | 2 days | All user flows |
| **E2E Tests** | Week 11 | 1.5 days | 10+ scenarios |
| **Load Tests** | Week 11 | 1 day | 100 concurrent users |
| **Security Tests** | Week 11 | 0.5 day | OWASP top 10 |
| **Total** | - | 15 days | Comprehensive |

---

### Documentation Time Allocation

| Document Type | Phase | Days | Audience |
|---------------|-------|------|----------|
| **Business Logic** | Week 1-2 | 3 days | All stakeholders |
| **API Docs** | Week 4 | 1 day | Developers |
| **User Guide** | Week 13 | 2 days | End users |
| **Admin Guide** | Week 13 | 1 day | Administrators |
| **Architecture Docs** | Week 14 | 2 days | Developers |
| **Total** | - | 9 days | - |

---

### Buffer for Unknowns

**Built-in Buffer**: 14 days (20% of total time)

**Distributed Buffer**:
- Week 6: 1 day (MVP testing)
- Week 10: 1 day (feature testing)
- Week 12: 2 days (deployment prep)
- Week 14: 5 days (dedicated buffer week)
- Distributed: 5 days across weeks

**Risk Scenarios**:
- **Minor delays** (1-3 days): Absorbed by distributed buffer
- **Medium delays** (1 week): Use Week 14 buffer
- **Major delays** (>2 weeks): Trigger decision gate (extend or abort)

---

## Timeline Scenarios

### Best Case: 10 Weeks

**Assumptions**:
- No major technical blockers
- All decision gates pass first time
- Minimal rework needed
- Team velocity high

**Timeline**:
- Phase 0: 1.5 weeks (instead of 2)
- Phase 1: 1.5 weeks (instead of 2)
- Phase 2: 2.5 weeks (instead of 3)
- Phase 3: 2.5 weeks (instead of 3)
- Phase 4: 1.5 weeks (instead of 2)
- Phase 5: 0.5 week (quick go-live)

**Probability**: 15% (optimistic)

---

### Likely Case: 12 Weeks

**Assumptions**:
- Normal development pace
- Minor issues at decision gates
- Some rework required
- Expected learning curve

**Timeline**:
- Phase 0: 2 weeks (as planned)
- Phase 1: 2 weeks (as planned)
- Phase 2: 3 weeks (as planned)
- Phase 3: 3 weeks (as planned)
- Phase 4: 1.5 weeks (slight speedup)
- Phase 5: 0.5 week (buffer unused)

**Probability**: 60% (most likely)

---

### Worst Case: 14 Weeks

**Assumptions**:
- Some technical challenges
- One decision gate requires rework
- More rework than expected
- Full buffer utilized

**Timeline**:
- Phase 0: 2 weeks (as planned)
- Phase 1: 2 weeks (as planned)
- Phase 2: 3.5 weeks (+0.5 week rework)
- Phase 3: 3.5 weeks (+0.5 week rework)
- Phase 4: 2 weeks (as planned)
- Phase 5: 1 week (half buffer used)

**Probability**: 25% (conservative)

---

### Abort Scenarios

**Week 2 Abort**: Business logic extraction fails
- **Investment**: 2 weeks
- **Consequence**: Switch to refactor (minimal loss)
- **Timeline Impact**: +2 weeks to refactor timeline

**Week 6 Abort**: MVP doesn't validate
- **Investment**: 6 weeks
- **Consequence**: Switch to refactor or hybrid
- **Timeline Impact**: +6 weeks lost

**Week 10 Abort**: Feature parity not achieved
- **Investment**: 10 weeks
- **Consequence**: Hybrid approach (keep some components)
- **Timeline Impact**: Reassess, likely extend

---

## Critical Path Analysis

### Critical Path Dependencies

**Sequential Dependencies** (cannot parallelize):

1. **Business Logic → Infrastructure** (Week 2 → Week 3)
   - Cannot build infrastructure without knowing business rules
   - **Risk**: Delays in Phase 0 cascade to all phases
   - **Mitigation**: Strict 2-week deadline, daily progress reviews

2. **Infrastructure → Core Features** (Week 4 → Week 5)
   - Cannot implement features without working infrastructure
   - **Risk**: Infrastructure issues delay feature development
   - **Mitigation**: Use proven technologies, avoid cutting-edge

3. **Core Features → Advanced Features** (Week 7 → Week 8)
   - Advanced features depend on core functionality
   - **Risk**: Core bugs delay advanced features
   - **Mitigation**: Thorough testing in Week 7

4. **Features → Testing** (Week 10 → Week 11)
   - Cannot test incomplete features
   - **Risk**: Late feature completion delays testing
   - **Mitigation**: Rolling testing during development

5. **Testing → Migration** (Week 11 → Week 12)
   - Cannot migrate without validated system
   - **Risk**: Test failures delay migration
   - **Mitigation**: Parallel test + migration prep

---

### Parallel Work Opportunities

**Can Be Parallelized**:

1. **Week 3-4**: Backend + Frontend infrastructure (separate teams)
2. **Week 5-7**: Validation engine + Definition generator (overlap)
3. **Week 8-10**: Web lookup + Export + Advanced features (3 streams)
4. **Week 11**: Testing + Documentation (separate activities)
5. **Week 13-14**: Training + Monitoring + Hot-fixes (3 streams)

**Resource Optimization**: Single developer → sequential, but tasks organized for efficiency

---

### Critical Path Timeline

**Critical Path** (longest dependency chain):

```
Week 1-2: Business Logic Extraction (10 days)
    ↓
Week 3: Backend Infrastructure (5 days)
    ↓
Week 4: AI Service Integration (5 days)
    ↓
Week 5: Validation Engine (5 days)
    ↓
Week 6: Definition Generator (5 days)
    ↓
Week 7: Repository Layer (5 days)
    ↓
Week 8: Web Lookup (5 days)
    ↓
Week 9: Export Service (5 days)
    ↓
Week 10: Advanced Validation (5 days)
    ↓
Week 11: Testing (5 days)
    ↓
Week 12: Migration (5 days)
    ↓
Week 13: Go-Live (5 days)
    ↓
Week 14: Buffer (5 days)

Total: 70 days (14 weeks)
```

**Critical Path Length**: 70 days (100% of timeline)
**Float**: 0 days on critical path, 5-10 days on non-critical tasks

---

## Risk-Adjusted Schedule

### Risk Categories

| Risk Category | Probability | Impact | Mitigation | Buffer |
|---------------|-------------|--------|------------|--------|
| **Technical Complexity** | 30% | High | Use proven tech, avoid bleeding-edge | +3 days |
| **Scope Creep** | 20% | Medium | Strict decision gates, clear requirements | +2 days |
| **Integration Issues** | 25% | Medium | Early integration testing | +3 days |
| **Performance Problems** | 15% | High | Performance testing from Week 5 | +2 days |
| **Data Migration** | 20% | High | Dry-run migration in Week 11 | +3 days |
| **Learning Curve** | 40% | Low | Integrated learning, use tutorials | +2 days |

**Total Risk Buffer**: 15 days (21% of timeline)
**Buffer Allocation**: Distributed across critical phases

---

### Risk Mitigation Timeline

**Week-by-Week Risk Management**:

| Week | Primary Risk | Mitigation Strategy | Contingency |
|------|--------------|---------------------|-------------|
| **1-2** | Incomplete extraction | Daily progress reviews | Extend to Week 2.5 |
| **3-4** | Infrastructure setup | Use Docker Compose templates | Simplify architecture |
| **5-6** | Core flow broken | Incremental testing | Adjust architecture |
| **7** | Repository performance | Early benchmarking | Optimize queries |
| **8-10** | Feature complexity | Simplify features | Defer non-critical |
| **11** | Test failures | Rolling testing | Prioritize critical bugs |
| **12** | Migration issues | Dry-run migration | Fallback to manual |
| **13-14** | Production issues | Monitoring + alerts | Rollback plan ready |

---

## Rebuild vs Refactor Comparison

### Timeline Comparison

| Approach | Duration | Confidence | Risk Level |
|----------|----------|------------|------------|
| **Refactor** | 15-20 weeks | 70% | Medium-High |
| **Rebuild (Best Case)** | 10 weeks | 85% | Low |
| **Rebuild (Likely)** | 12 weeks | 75% | Medium |
| **Rebuild (Worst Case)** | 14 weeks | 65% | Medium |

**Conclusion**: Rebuild is 25-40% faster than refactor in likely scenarios

---

### Rebuild Advantages

1. **Speed**: 12 weeks vs 15-20 weeks (25-40% faster)
2. **Clean Architecture**: No technical debt, modern patterns
3. **Performance**: Modern stack → better performance
4. **Maintainability**: Smaller codebase (25k vs 83k LOC)
5. **Scalability**: Ready for production (multi-user, cloud)
6. **Developer Experience**: Better tooling (TypeScript, FastAPI)

---

### Rebuild Risks

1. **Business Logic Loss**: Mitigated by Phase 0 extraction
2. **Integration Complexity**: Mitigated by proven technologies
3. **Learning Curve**: Mitigated by integrated learning
4. **Timeline Pressure**: Mitigated by decision gates
5. **Scope Creep**: Mitigated by strict phase boundaries

---

### Decision Matrix

**When to Rebuild**:
- ✅ Phase 0 extraction successful (Week 2)
- ✅ MVP validates (Week 6)
- ✅ Team comfortable with new stack
- ✅ Stakeholders support clean slate

**When to Refactor**:
- ❌ Phase 0 extraction fails (<90% complete)
- ❌ MVP doesn't validate (core issues)
- ❌ Team prefers incremental approach
- ❌ Stakeholders risk-averse

---

## Success Metrics

### Phase 0 Success Metrics
- [ ] 100% validation rules documented
- [ ] 100% orchestration logic extracted
- [ ] Stakeholder approval received
- [ ] Test scenarios complete (10+ scenarios)

### Phase 1 Success Metrics
- [ ] FastAPI app responds in <100ms
- [ ] PostgreSQL queries <50ms
- [ ] CI/CD pipeline <5 minutes
- [ ] Docker build time <3 minutes

### Phase 2 Success Metrics
- [ ] Generation time <5s (target: 3s)
- [ ] Validation time <2s
- [ ] Quality score ±10% of legacy
- [ ] API response time <500ms

### Phase 3 Success Metrics
- [ ] Web lookup timeout <5s
- [ ] Cache hit rate >70%
- [ ] Export generation <2s
- [ ] Feature parity: 100%

### Phase 4 Success Metrics
- [ ] Test coverage >80%
- [ ] Load test: 100 users, <5s response
- [ ] Data migration: 100% integrity
- [ ] Zero critical vulnerabilities

### Phase 5 Success Metrics
- [ ] Production uptime >99.9%
- [ ] Error rate <0.1%
- [ ] User satisfaction >80%
- [ ] Documentation completeness: 100%

---

## Appendix A: Technology Stack

### Backend Stack
- **Framework**: FastAPI 0.100+
- **Database**: PostgreSQL 15+
- **Cache**: Redis 7+
- **ORM**: SQLAlchemy 2.0+
- **Migrations**: Alembic
- **API Docs**: Swagger/OpenAPI 3.0
- **Testing**: Pytest + pytest-asyncio
- **Code Quality**: Ruff + Black + mypy

### Frontend Stack
- **Framework**: React 18+
- **Language**: TypeScript 5+
- **Bundler**: Vite 4+
- **Styling**: Tailwind CSS 3+
- **UI Library**: shadcn/ui
- **State Management**: Zustand or React Query
- **Testing**: Jest + Playwright
- **API Client**: Axios or Fetch API

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Orchestration**: Kubernetes (production)
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack (or CloudWatch)
- **Cloud**: AWS/GCP (TBD)

---

## Appendix B: Decision Log Template

### Decision Template

```markdown
## Decision: [Title]

**Date**: YYYY-MM-DD
**Decision Point**: Week X
**Decision Maker**: [Name/Role]

**Context**:
[What led to this decision?]

**Options Considered**:
1. [Option 1]
2. [Option 2]
3. [Option 3]

**Decision**:
[What was decided?]

**Rationale**:
[Why was this chosen?]

**Impact**:
- Timeline: [+/- days]
- Resources: [impact]
- Risk: [change in risk]

**Action Items**:
- [ ] Task 1
- [ ] Task 2
```

---

## Appendix C: Glossary

| Term | Definition |
|------|------------|
| **Business Logic** | Rules and workflows independent of technology |
| **Decision Gate** | Go/No-Go checkpoint at phase boundaries |
| **Feature Parity** | Rebuild has all features of legacy system |
| **Critical Path** | Longest sequence of dependent tasks |
| **MVP** | Minimum Viable Product (core functionality) |
| **Validation Rule** | Business rule for quality checking |
| **Orchestrator** | Service coordinating multiple operations |
| **LOC** | Lines of Code |
| **E2E** | End-to-End (testing) |
| **CI/CD** | Continuous Integration/Continuous Deployment |

---

## Document Control

- **Version**: 1.0
- **Status**: Planning
- **Owner**: Technical Architecture Team
- **Created**: 2025-10-02
- **Next Review**: 2025-10-09 (or at each decision gate)
- **Distribution**: Stakeholders, Development Team, Architecture Board

---

**END OF REBUILD TIMELINE**
