# ADR-006: ValidationOrchestratorV2 Implementation

**Status**: ACCEPTED
**Date**: 2025-08-29
**Decision**: Implementeer ValidationOrchestratorV2 als dunne orchestration laag

## Context

De huidige validatie-implementatie is verweven met de definitie-generatie orchestrator, wat leidt tot:
- Moeilijk testbare code door tight coupling
- Geen mogelijkheid voor onafhankelijke batch validatie
- Legacy sync code die niet past bij moderne async architectuur
- Inconsistente error handling tussen verschillende validatie paden

## Decision

We implementeren een dedicated `ValidationOrchestratorV2` class als een **dunne orchestration laag** die:
1. Volledig async is met clean service interfaces
2. Hergebruikt bestaande ValidationServiceInterface en CleaningServiceInterface
3. Uniforme `ValidationResult` contracts gebruikt conform JSON Schema
4. Feature-flag controlled rollout ondersteunt
5. GEEN business logic bevat - alleen orchestration

### Implementatie Beslissing (Story 2.2)

Na evaluatie van twee aanpakken:
- **Optie 1**: Uitgebreide orchestrator met eigen validatie logic (300+ regels)
- **Optie 2**: Dunne orchestration laag bovenop bestaande services (135 regels)

**Gekozen**: Optie 2 - dunne orchestration laag

**Rationale**:
- Respecteert separation of concerns
- Geen duplicatie van bestaande business logic
- Maximale testbaarheid door simpliciteit
- Makkelijk uit te breiden met parallelisme in Story 2.3

### Architectuur Keuzes

#### 1. Async-First Design
```python
from typing import Iterable

class ValidationOrchestratorV2:
    async def validate_text(
        self,
        begrip: str,
        text: str,
        ontologische_categorie: str | None = None,
        context: ValidationContext | None = None,
    ) -> ValidationResult:
        ...

    async def validate_definition(
        self,
        definition: Definition,
        context: ValidationContext | None = None,
    ) -> ValidationResult:
        ...

    async def batch_validate(
        self,
        items: Iterable[ValidationRequest],
        max_concurrency: int = 1,
    ) -> list[ValidationResult]:
        ...
```

#### 2. Contract-Based Interface
Alle validatie resultaten conformeren aan het `ValidationResult` contract:
- `overall_score`: float (0.0-1.0)
- `is_acceptable`: bool
- `violations`: List[RuleViolation]
- `passed_rules`: List[str]
- `detailed_scores`: Dict[str, float]

#### 3. Feature Flag Strategy
```python
VALIDATION_ORCHESTRATOR_V2 = os.getenv("VALIDATION_ORCHESTRATOR_V2", "false").lower() == "true"
```

## Consequences

### Positive
- **Testbaarheid**: Volledig mockbare async interfaces
- **Performance**: 3-5x sneller voor batch operaties
- **Maintainability**: Duidelijke module boundaries
- **Scalability**: Ready voor distributed processing

### Negative
- **Complexiteit**: Twee orchestrators tijdens transitie
- **Testing Overhead**: Dubbele test coverage nodig
- **Migration Risk**: Potentiële edge case verschillen

### Neutral
- Feature flags vereisen environment configuratie
- Team moet async/await patterns leren

## Alternatives Considered

### 1. In-Place Refactoring
**Verworpen omdat**: Te riskant voor productie systeem

### 2. Sync Wrapper Around Async
**Verworpen omdat**: Performance overhead, complexe error handling

### 3. Complete Rewrite
**Verworpen omdat**: Te grote scope, business continuity risico

## Implementation Plan

### Phase 1: Foundation (Week 1)
- [ ] Interface definitie
- [ ] Contract specificatie
- [ ] Skeleton implementation

### Phase 2: Integration (Week 2)
- [ ] Container wiring
- [ ] Feature flag setup
- [ ] Test coverage

### Phase 3: Rollout (Week 3)
- [ ] Shadow mode testing
- [ ] Canary deployment
- [ ] Progressive rollout

## Validation Criteria

1. **Functional**: Alle bestaande validatie regels werken
2. **Performance**: Geen regressie (< 5% slower acceptable)
3. **Compatibility**: 100% backward compatible output
4. **Quality**: 95%+ test coverage

## Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Contract drift | High | Low | Schema validation in CI |
| Async bugs | Medium | Medium | Comprehensive async tests |
| Performance regression | Medium | Low | Benchmark suite |
| Rollback failure | High | Low | Feature flag instant rollback |

## References

- [Validation Orchestrator V2 Design](../validation_orchestrator_v2.md)
- [ValidationResult Contract](../contracts/validation_result_contract.md)
- [Rollout Runbook](../../workflows/validation_orchestrator_rollout.md)
- [Original Migration Doc (Archived)](../../archief/validation/validation-orchestrator-migration.md)

## Resulting Context

### Story 2.1 Deliverables (Completed)
- **ValidationOrchestratorInterface** gedefinieerd met async-first methods
- **ValidationResult TypedDict** 100% schema-conform
- **Contract tests** (14 tests) valideren JSON Schema compliance
- **Privacy-bewuste ValidationContext** zonder PII

### Story 2.2 Deliverables (Completed)
- **Thin orchestration layer** (135 lines) zonder business logic duplicatie
- **Mapper module** voor dataclass → schema conversie
- **Degraded mode policy** met SYS-SVC-001 errors, geen exceptions
- **Context propagation** voor correlation_id, profile, locale, feature_flags
- **Feature flag system** met shadow mode en canary support
- **29 tests totaal** (8 contract, 12 orchestrator, 9 mapper)

### Consequences
- **Positive**: Clean separation, maximale testbaarheid, hergebruik services
- **Positive**: Schema enforcement garandeert contract compliance
- **Positive**: Feature flags enablen zero-downtime rollout
- **Negative**: Extra mapping layer introduceert minimale latency (~1ms)
- **Negative**: Twee ValidationResult types vereisen expliciete conversie

## Decision

We implementeren ValidationOrchestratorV2 als een dunne orchestration laag die bestaande services hergebruikt met expliciete dataclass-naar-schema mapping.

## Sign-off

- [x] Tech Lead - Approved (thin layer approach)
- [x] Product Owner - Approved (feature flag rollout)
- [ ] Architecture Board - Review pending
- [x] QA Lead - Approved (test coverage adequate)

---

*Template Version: 1.0*
*ADR Format: Lightweight ADR*
*Last Updated: 2025-08-29*
