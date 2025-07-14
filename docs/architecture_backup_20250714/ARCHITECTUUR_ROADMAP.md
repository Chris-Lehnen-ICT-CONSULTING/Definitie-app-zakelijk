# 🏗️ Architectuur Roadmap - DefinitieAgent Target State

**Document Versie:** 1.0  
**Datum:** 2025-07-14  
**Status:** Target Architecture Definition  
**Eigenaar:** Architecture Team  

---

## 🎯 **Visie & Doelstelling**

**Huidige Staat:** Fragmented monolith met overlappende services  
**Target Staat:** Modern, layered architecture met domain-driven design  
**Transformatie:** Van 50,000+ lines chaos naar gestructureerde, maintainable codebase  

### **Architecturale Principes**
- **Domain-Driven Design**: Business logic gescheiden per domein
- **Dependency Injection**: Loose coupling tussen components  
- **Layered Architecture**: Clear separation of concerns
- **API-First**: Consistent interface contracts
- **Security by Design**: Security op elke laag
- **Performance First**: Async-first, caching strategy

---

## 📐 **Target Architecture Overview**

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                       │
├─────────────────────────────────────────────────────────────┤
│  UI Components (Atomic Design)  │    API Gateway           │
│  ├── Atoms (inputs, buttons)    │    ├── Authentication    │
│  ├── Molecules (forms, cards)   │    ├── Rate Limiting     │
│  ├── Organisms (dashboards)     │    ├── Logging          │
│  └── Templates (layouts)        │    └── Error Handling   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                        │
├─────────────────────────────────────────────────────────────┤
│  Service Orchestration  │  Use Case Handlers  │  DTOs      │
│  ├── Definition Service │  ├── Generate Def   │  ├── Input │
│  ├── Validation Service │  ├── Validate Def   │  ├── Output│
│  ├── Web Lookup Service │  ├── Search Web     │  └── Events│
│  └── Integration Svc    │  └── Export Data    │           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     DOMAIN LAYER                           │
├─────────────────────────────────────────────────────────────┤
│  Definition Domain    │  Validation Domain   │  Web Domain │
│  ├── Entities        │  ├── Rules Engine    │  ├── Sources│
│  ├── Value Objects   │  ├── Validators      │  ├── Lookups│
│  ├── Domain Services │  ├── Results         │  └── Cache  │
│  └── Repositories    │  └── Aggregators     │             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  INFRASTRUCTURE LAYER                      │
├─────────────────────────────────────────────────────────────┤
│  Data Access     │  External APIs    │  Cross-Cutting      │
│  ├── Database    │  ├── OpenAI       │  ├── Logging        │
│  ├── File System │  ├── Web Sources  │  ├── Monitoring     │
│  ├── Cache       │  └── Auth         │  ├── Error Handling │
│  └── Migrations  │                   │  └── Configuration  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🗂️ **Target Directory Structure**

```
src/
├── presentation/                    # UI & API Layer
│   ├── web/                        # Streamlit Web Interface
│   │   ├── components/             # Atomic Design Components
│   │   │   ├── atoms/              # Basic UI elements
│   │   │   ├── molecules/          # Composite components
│   │   │   ├── organisms/          # Complex components
│   │   │   └── templates/          # Page layouts
│   │   ├── pages/                  # Page definitions
│   │   ├── state/                  # State management
│   │   └── utils/                  # UI utilities
│   ├── api/                        # REST API Layer (future)
│   │   ├── routes/                 # API endpoints
│   │   ├── middleware/             # Request/response middleware
│   │   └── schemas/                # API contracts
│   └── cli/                        # Command Line Interface
│
├── application/                     # Application Services Layer
│   ├── services/                   # Service Orchestration
│   │   ├── definition_service.py   # Definition generation workflow
│   │   ├── validation_service.py   # Validation orchestration
│   │   ├── web_lookup_service.py   # External lookup coordination
│   │   └── integration_service.py  # Cross-service coordination
│   ├── use_cases/                  # Business Use Cases
│   │   ├── generate_definition.py  # Core definition generation
│   │   ├── validate_definition.py  # Quality validation
│   │   ├── search_external.py      # External source lookup
│   │   └── export_results.py       # Data export workflows
│   ├── dto/                        # Data Transfer Objects
│   │   ├── requests/               # Input DTOs
│   │   ├── responses/              # Output DTOs
│   │   └── events/                 # Event DTOs
│   └── interfaces/                 # Service contracts
│
├── domain/                          # Core Business Logic
│   ├── definition/                 # Definition Domain
│   │   ├── entities/               # Definition, Begriff, Context
│   │   ├── value_objects/          # DefinitionId, Status, Quality
│   │   ├── services/               # Domain services
│   │   ├── repositories/           # Repository interfaces
│   │   └── events/                 # Domain events
│   ├── validation/                 # Validation Domain
│   │   ├── engine/                 # Validation engine core
│   │   │   ├── validation_engine.py    # Single entry point
│   │   │   ├── rule_registry.py        # Centralized rule management
│   │   │   └── result_aggregator.py    # Result consolidation
│   │   ├── rules/                  # Validation Rules
│   │   │   ├── content_rules.py    # CON-01, CON-02, etc.
│   │   │   ├── essential_rules.py  # ESS-01 t/m ESS-05
│   │   │   ├── structure_rules.py  # STR-01 t/m STR-09
│   │   │   ├── language_rules.py   # LANG-01 t/m LANG-04
│   │   │   └── quality_rules.py    # QUAL-01 t/m QUAL-10
│   │   ├── schemas/                # Rule & result schemas
│   │   └── aggregators/            # Result aggregation logic
│   ├── web_lookup/                 # External Sources Domain
│   │   ├── sources/                # Source implementations
│   │   ├── cache/                  # Lookup caching
│   │   └── strategies/             # Lookup strategies
│   └── shared/                     # Shared domain concepts
│       ├── value_objects/          # Common value objects
│       ├── specifications/         # Domain specifications
│       └── exceptions/             # Domain exceptions
│
├── infrastructure/                  # Infrastructure Layer
│   ├── persistence/                # Data Access
│   │   ├── database/               # Database implementations
│   │   │   ├── repositories/       # Repository implementations
│   │   │   ├── models/             # ORM models
│   │   │   ├── migrations/         # Database migrations
│   │   │   └── connection/         # Connection management
│   │   ├── file_system/            # File storage
│   │   └── cache/                  # Caching implementations
│   ├── external/                   # External Services
│   │   ├── openai/                 # OpenAI API client
│   │   ├── web_sources/            # Web scraping clients
│   │   └── auth/                   # Authentication providers
│   ├── configuration/              # Configuration Management
│   │   ├── config_loader.py        # Single configuration authority
│   │   ├── settings/               # Environment-specific settings
│   │   └── validation/             # Configuration validation
│   ├── security/                   # Security Infrastructure
│   │   ├── key_management/         # Secure key storage (Vault)
│   │   ├── input_validation/       # Input sanitization
│   │   ├── authentication/         # Auth mechanisms
│   │   └── encryption/             # Data encryption
│   ├── monitoring/                 # Observability
│   │   ├── logging/                # Structured logging
│   │   ├── metrics/                # Application metrics
│   │   ├── tracing/                # Distributed tracing
│   │   └── health/                 # Health checks
│   └── messaging/                  # Event/Message handling
│       ├── events/                 # Event bus implementation
│       └── queues/                 # Message queues
│
├── shared/                          # Cross-cutting Concerns
│   ├── utils/                      # Utility functions
│   │   ├── resilience/             # Unified resilience utilities
│   │   ├── async_helpers/          # Async operation helpers
│   │   ├── validation/             # Input validation helpers
│   │   └── formatters/             # Data formatting utilities
│   ├── exceptions/                 # Application exceptions
│   ├── constants/                  # Application constants
│   └── types/                      # Type definitions
│
└── tests/                          # Test Organization
    ├── unit/                       # Unit tests (by layer)
    │   ├── domain/                 # Domain logic tests
    │   ├── application/            # Service tests
    │   ├── infrastructure/         # Infrastructure tests
    │   └── presentation/           # UI/API tests
    ├── integration/                # Integration tests
    │   ├── database/               # Database integration
    │   ├── external_apis/          # External service integration
    │   └── end_to_end/             # Full workflow tests
    ├── performance/                # Performance tests
    ├── security/                   # Security tests
    └── fixtures/                   # Test data and utilities
```

---

## 🔄 **Transformatie Fases**

### **Fase 1: Foundation (Week 1-4)**
**Focus:** Clean Architecture Foundation

#### **Week 1-2: Dependency Cleanup**
```
Current:                           Target:
src/services/                   →  src/application/services/
├── circular imports            →  ├── clean interfaces
├── tight coupling              →  ├── dependency injection
└── mixed concerns             →  └── single responsibility

Critical Actions:
✅ Break circular imports tussen services en integration
✅ Implement dependency injection container
✅ Create clear service interfaces
```

#### **Week 3-4: Layer Separation**
```
Current:                           Target:
Mixed business + data logic     →  Clean layer separation
├── UI calls database directly →  ├── UI → Application → Domain → Infrastructure
├── Services mixed with DB     →  ├── Clear contracts between layers
└── No domain models          →  └── Rich domain models
```

### **Fase 2: Domain Modeling (Week 5-8)**
**Focus:** Domain-Driven Design Implementation

#### **Week 5-6: Validation Domain**
```
Current State:                     Target State:
3 overlapping validation systems → Unified Validation Domain

src/ai_toetser/core.py (45 rules)     →  domain/validation/
├── Monolithic dispatcher          →  ├── engine/validation_engine.py
├── Mixed concerns                 →  ├── rules/ (organized by category)
└── Hard to extend                →  ├── schemas/ (contracts)
                                  →  └── aggregators/ (result handling)

src/ai_toetser/validators/ (16)    →  [DEPRECATED]
src/validation/definitie_validator.py → [MIGRATED]
```

#### **Week 7-8: Definition Domain**
```
Target Domain Structure:
domain/definition/
├── entities/
│   ├── definition.py           # Core Definition entity
│   ├── begrip.py              # Begriff (term) entity  
│   └── context.py             # Context entity
├── value_objects/
│   ├── definition_id.py       # Unique identifiers
│   ├── quality_score.py       # Quality metrics
│   └── status.py              # Definition status
├── services/
│   ├── definition_generator.py # Domain service for generation
│   └── quality_assessor.py    # Domain service for quality
└── repositories/
    └── definition_repository.py # Repository interface
```

### **Fase 3: Service Layer (Week 9-12)**
**Focus:** Application Services & Use Cases

#### **Week 9-10: Service Unification**
```
Current Services (3 overlapping):     Target (Single Service Layer):
├── services/integrated_service.py → application/services/definition_service.py
├── integration/definitie_checker  → application/services/validation_service.py
└── [various scattered services]   → application/services/web_lookup_service.py

Dependency Flow:
UI → Application Services → Domain Services → Infrastructure
```

#### **Week 11-12: Use Case Implementation**
```
application/use_cases/
├── generate_definition.py      # Orchestrates entire generation flow
│   ├── 1. Validate input
│   ├── 2. Generate definition (via domain service)
│   ├── 3. Validate quality (via validation domain)
│   ├── 4. Lookup external sources
│   └── 5. Return aggregated result
├── validate_definition.py      # Quality validation workflow
├── search_external.py         # External source lookup
└── export_results.py          # Data export workflows
```

### **Fase 4: Infrastructure (Week 13-16)**
**Focus:** Infrastructure & Security

#### **Week 13-14: Data Layer**
```
Current Database Issues:           Target Infrastructure:
├── No connection pooling      →  infrastructure/persistence/database/
├── Concurrent access errors   →  ├── connection/pool_manager.py
├── No migration strategy     →  ├── repositories/ (implementations)
└── Mixed data access         →  ├── migrations/ (versioned scripts)
                              →  └── models/ (ORM definitions)
```

#### **Week 15-16: Security & Monitoring**
```
Security Infrastructure:           Monitoring Infrastructure:
infrastructure/security/           infrastructure/monitoring/
├── key_management/            →  ├── logging/structured_logger.py
│   └── vault_client.py       →  ├── metrics/prometheus_metrics.py
├── input_validation/         →  ├── tracing/jaeger_tracer.py
│   └── sanitizer.py          →  └── health/health_checks.py
└── authentication/
    └── oauth_provider.py
```

---

## 🔧 **Component Interfaces**

### **Service Layer Contracts**

```python
# application/interfaces/definition_service.py
from abc import ABC, abstractmethod
from application.dto.requests import GenerateDefinitionRequest
from application.dto.responses import GenerateDefinitionResponse

class IDefinitionService(ABC):
    @abstractmethod
    async def generate_definition(
        self, 
        request: GenerateDefinitionRequest
    ) -> GenerateDefinitionResponse:
        """Generate a definition with full validation pipeline"""
        pass

# application/interfaces/validation_service.py  
class IValidationService(ABC):
    @abstractmethod
    async def validate_definition(
        self,
        definition: str,
        context: ValidationContext
    ) -> ValidationResult:
        """Validate definition against all rules"""
        pass
```

### **Domain Repository Interfaces**

```python
# domain/definition/repositories/definition_repository.py
from abc import ABC, abstractmethod
from domain.definition.entities import Definition
from domain.shared.value_objects import DefinitionId

class IDefinitionRepository(ABC):
    @abstractmethod
    async def save(self, definition: Definition) -> None:
        """Save definition to persistence layer"""
        pass
    
    @abstractmethod
    async def find_by_id(self, definition_id: DefinitionId) -> Definition | None:
        """Find definition by unique identifier"""
        pass
    
    @abstractmethod
    async def find_by_term(self, term: str) -> list[Definition]:
        """Find all definitions for a term"""
        pass
```

### **Validation Engine Contract**

```python
# domain/validation/engine/validation_engine.py
from domain.validation.schemas import ValidationRequest, ValidationResult

class ValidationEngine:
    def __init__(self, rule_registry: IRuleRegistry):
        self._rule_registry = rule_registry
        self._result_aggregator = ResultAggregator()
    
    async def validate(self, request: ValidationRequest) -> ValidationResult:
        """Execute all applicable rules and aggregate results"""
        applicable_rules = self._rule_registry.get_rules_for_context(request.context)
        
        results = await asyncio.gather(*[
            rule.execute(request) for rule in applicable_rules
        ])
        
        return self._result_aggregator.aggregate(results)
```

---

## 🚀 **Migration Strategy**

### **Incremental Migration Approach**

#### **Phase 1: Parallel Implementation**
```
Keep existing system running while building new architecture
├── Build new domain layer alongside existing code
├── Implement new service interfaces
├── Route specific use cases to new architecture
└── Maintain backward compatibility
```

#### **Phase 2: Feature Flags**
```python
# Feature flag controlled migration
if feature_flags.use_new_validation_engine:
    result = new_validation_service.validate(definition)
else:
    result = legacy_ai_toetser.validate(definition)
```

#### **Phase 3: Gradual Cutover**
```
Week 1-2: Build new validation domain (run in parallel)
Week 3-4: Migrate definition generation (feature flagged)
Week 5-6: Migrate web lookup (feature flagged)
Week 7-8: Full cutover, remove legacy code
```

### **Data Migration Strategy**

```python
# Database migration approach
class DatabaseMigrationPlan:
    """
    1. Schema versioning for backward compatibility
    2. Data transformation scripts
    3. Rollback procedures
    4. Connection pooling implementation
    """
    
    migrations = [
        "001_add_connection_pooling.sql",
        "002_normalize_validation_results.sql", 
        "003_add_audit_tables.sql",
        "004_optimize_indexes.sql"
    ]
```

---

## 📊 **Architecture Quality Metrics**

### **Target Metrics per Layer**

| Layer | Metric | Current | Target | Week 16 |
|-------|--------|---------|--------|---------|
| **Domain** | Cyclomatic Complexity | Unknown | <10 | <8 |
| **Application** | Service Cohesion | Low | High | High |
| **Infrastructure** | Coupling | High | Low | Low |
| **Presentation** | Component Size | >100 LOC | <50 LOC | <50 LOC |

### **Dependency Metrics**

```
Target Dependency Flow:
Presentation → Application → Domain ← Infrastructure

Forbidden Dependencies:
❌ Domain → Infrastructure
❌ Domain → Application  
❌ Infrastructure → Application
❌ Circular dependencies (any layer)

Monitoring:
✅ Automated dependency analysis in CI/CD
✅ Architecture decision records (ADRs)
✅ Regular architecture reviews
```

### **Performance Targets**

| Component | Current | Target | Architecture Impact |
|-----------|---------|--------|-------------------|
| **Definition Generation** | 5-8s | <2s | Async pipelines, caching |
| **Validation Engine** | ~3s | <500ms | Parallel rule execution |
| **Web Lookup** | Failed | <1s | Connection pooling, async |
| **Database Operations** | Locks | <100ms | Connection pooling, WAL mode |

---

## 🔒 **Security Architecture**

### **Defense in Depth Strategy**

```
┌─────────────────────────────────────────────────────────────┐
│  PRESENTATION LAYER SECURITY                                │
├─────────────────────────────────────────────────────────────┤
│  ├── Input Validation & Sanitization                       │
│  ├── XSS Protection                                         │
│  ├── CSRF Protection                                        │
│  └── Rate Limiting                                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  APPLICATION LAYER SECURITY                                 │
├─────────────────────────────────────────────────────────────┤
│  ├── Authentication & Authorization                         │
│  ├── Business Logic Validation                              │
│  ├── Audit Logging                                          │
│  └── Error Handling (no info disclosure)                    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  INFRASTRUCTURE LAYER SECURITY                              │
├─────────────────────────────────────────────────────────────┤
│  ├── Key Management (Vault)                                 │
│  ├── Database Security (parameterized queries)              │
│  ├── Network Security (TLS, VPN)                            │
│  └── Monitoring & Alerting                                  │
└─────────────────────────────────────────────────────────────┘
```

### **Key Management Architecture**

```python
# Target: Secure key management
infrastructure/security/key_management/
├── vault_client.py              # HashiCorp Vault integration
├── key_rotation.py              # Automated key rotation
└── audit_logger.py              # Key access auditing

# Migration from:
# ❌ Environment variables (current)
# ✅ Azure Key Vault / HashiCorp Vault (target)
```

---

## 🎯 **Architecture Decision Records (ADRs)**

### **ADR-001: Layered Architecture Pattern**
**Status:** Approved  
**Decision:** Implement 4-layer architecture (Presentation, Application, Domain, Infrastructure)  
**Rationale:** Clear separation of concerns, testability, maintainability  
**Consequences:** Initial complexity, but long-term maintainability gains  

### **ADR-002: Domain-Driven Design**
**Status:** Approved  
**Decision:** Model core business concepts as domain entities  
**Rationale:** Better business alignment, reduced complexity  
**Consequences:** Requires domain modeling expertise  

### **ADR-003: Dependency Injection**
**Status:** Approved  
**Decision:** Use dependency injection for service wiring  
**Rationale:** Loose coupling, testability, flexibility  
**Consequences:** Additional container configuration  

### **ADR-004: Async-First Design**
**Status:** Approved  
**Decision:** Design all I/O operations as async  
**Rationale:** Better performance, scalability  
**Consequences:** Complexity in error handling, debugging  

### **ADR-005: Single Validation Authority**
**Status:** Approved  
**Decision:** Consolidate 3 validation systems into 1  
**Rationale:** Reduce duplication, improve consistency  
**Consequences:** Major refactoring effort  

---

## 📈 **Success Criteria & Validation**

### **Architecture Quality Gates**

#### **Week 4 Gate: Foundation**
- [ ] Zero circular dependencies
- [ ] Clean layer separation implemented
- [ ] Dependency injection operational
- [ ] Service interfaces defined

#### **Week 8 Gate: Domain**  
- [ ] Domain models implemented
- [ ] Validation engine unified
- [ ] Business logic separated from infrastructure
- [ ] Repository pattern implemented

#### **Week 12 Gate: Services**
- [ ] Application services operational
- [ ] Use cases implemented
- [ ] Cross-cutting concerns extracted
- [ ] Service contracts stable

#### **Week 16 Gate: Production**
- [ ] Security architecture implemented
- [ ] Performance targets met
- [ ] Monitoring operational
- [ ] Documentation complete

### **Continuous Validation**

```python
# Automated architecture tests
def test_no_circular_dependencies():
    """Ensure no circular imports exist"""
    assert analyze_dependencies() == []

def test_layer_separation():
    """Domain layer should not depend on infrastructure"""
    assert not domain_depends_on_infrastructure()

def test_service_contracts():
    """All services should implement defined interfaces"""
    assert all_services_implement_contracts()
```

---

## 🔄 **Rollback Strategy**

### **Risk Mitigation**

```
Each phase includes rollback procedures:

Phase 1: Feature flags for new dependency injection
├── Rollback: Disable feature flags
├── Impact: Return to current state
└── Time: < 1 hour

Phase 2: Parallel validation systems
├── Rollback: Route traffic back to old system
├── Impact: Temporary performance degradation
└── Time: < 30 minutes

Phase 3: Service layer migration
├── Rollback: Revert service registrations
├── Impact: Return to legacy services
└── Time: < 2 hours

Phase 4: Infrastructure changes
├── Rollback: Database migration rollback scripts
├── Impact: Potential data migration required
└── Time: < 4 hours
```

---

## 📞 **Architecture Governance**

### **Architecture Review Board**
- **Technical Lead** (architecture decisions)
- **Senior Developer** (implementation oversight)
- **Security Specialist** (security architecture)
- **QA Engineer** (quality validation)

### **Decision Process**
1. **Proposal** - Architecture change request
2. **Review** - Technical assessment
3. **Discussion** - Team alignment
4. **Decision** - Approved/rejected with rationale
5. **Documentation** - ADR creation
6. **Implementation** - Execution with validation

### **Review Schedule**
- **Weekly**: Architecture progress review
- **Bi-weekly**: Architecture decision review
- **Monthly**: Full architecture health check
- **Quarterly**: Architecture roadmap adjustment

---

**Next Review:** Weekly during implementation phases  
**Document Owner:** Technical Lead  
**Approval Status:** ✅ Ready for implementation  

---

*This architecture roadmap provides the target state and transformation path for DefinitieAgent's evolution from fragmented monolith to modern, maintainable application.*