# ADR-006: ValidationOrchestratorV2 Implementation

**Status**: DRAFT
**Date**: 2025-08-29
**Decision**: Pending

## Context

De huidige validatie-implementatie is verweven met de definitie-generatie orchestrator, wat leidt tot:
- Moeilijk testbare code door tight coupling
- Geen mogelijkheid voor onafhankelijke batch validatie
- Legacy sync code die niet past bij moderne async architectuur
- Inconsistente error handling tussen verschillende validatie paden

## Decision

We implementeren een dedicated `ValidationOrchestratorV2` class die:
1. Volledig async is met native `AsyncGPTClient` integratie
2. Een duidelijke scheiding van verantwoordelijkheden handhaaft
3. Uniforme `ValidationResult` contracts gebruikt
4. Feature-flag controlled rollout ondersteunt

### Architectuur Keuzes

#### 1. Async-First Design
```python
class ValidationOrchestratorV2:
    async def validate_text(self, text: str, context: ValidationContext) -> ValidationResult
    async def validate_definition(self, definition: Definition) -> ValidationResult
    async def batch_validate(self, items: List[Validatable]) -> List[ValidationResult]
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
- [Implementation Workflow](../../workflows/VALIDATION_ORCHESTRATOR_V2_IMPLEMENTATION_WORKFLOW.md)
- [Original Migration Doc (Archived)](../../ARCHIEF/validation/validation-orchestrator-migration.md)

## Decision

_[To be completed after review]_

## Sign-off

- [ ] Tech Lead
- [ ] Product Owner
- [ ] Architecture Board
- [ ] QA Lead

---

*Template Version: 1.0*
*ADR Format: Lightweight ADR*
