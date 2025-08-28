# ADR-005: V1 Orchestrator Direct Elimination Exception

**Status:** Proposed
**Datum:** 2025-08-28
**Deciders:** Development Team
**Supersedes:** Partial exception to ADR-004 for internal architecture refactoring

## Context

DefinitieAgent heeft een legacy V1 orchestrator die vervangen wordt door een moderne V2 orchestrator. ADR-004 mandateert incrementele "Strangler Fig" migratie voor alle system changes, maar deze specifieke refactoring heeft unieke karakteristieken die een exception rechtvaardigen.

**Unieke Context Factoren:**
- **Pre-production status**: Geen production users = geen service disruption risk
- **Internal architecture**: V1/V2 orchestrator zijn internal implementation details, niet user-facing features
- **Technical debt window**: Ideale gelegenheid voor clean architecture voordat production launch
- **Existing async infrastructure**: AsyncGPTClient volledig geïmplementeerd en production-ready

## Probleemstelling

Hoe kunnen we V1 orchestrator elimineren zonder ADR-004 Strangler Fig requirements te violeren, terwijl we de governance principes respecteren?

## Beslissing

We creëren een **gerichte exception op ADR-004** voor V1 orchestrator elimination gebaseerd op:

1. **Internal Architecture Scope**: V1/V2 orchestrator zijn implementation details zonder direct user impact
2. **Pre-production Window**: No users = traditional migration risks niet van toepassing
3. **Technical Debt Elimination**: Clean start opportuniteit voordat production constraints apply
4. **Proven Alternative Infrastructure**: AsyncGPTClient gevalideerd en production-ready

### Exception Parameters

**Scope**: Beperkt tot `src/services/definition_orchestrator.py` elimination en V2 orchestrator native implementation
**Timeline**: Eenmalige refactoring, niet iteratieve feature migration
**Rollback**: Git-based rollback mechanism i.p.v. feature flags

## Rationale

### Why Exception is Justified

1. **No User-Facing Impact**
   - V1/V2 orchestrator verschil is invisible voor eindgebruikers
   - API endpoints blijven identiek
   - Response formats unchanged

2. **Pre-Production Advantage**
   - Zero users = geen service disruption mogelijk
   - Perfect window voor architectural cleanup
   - Post-production zou ADR-004 wel van toepassing zijn

3. **Technical Debt Prevention**
   - V1 maintenance overhead elimination
   - Clean codebase voor production launch
   - Prevents accumulation of dual-path complexity

4. **Risk Mitigation Still Present**
   - Comprehensive testing required (performance benchmarking, load testing)
   - Emergency rollback via git revert + deployment
   - Monitoring and validation gates maintained

### Alignment with ADR-004 Principles

**Preserved ADR-004 Values:**
- ✅ **Zero downtime**: Pre-production = niet van toepassing
- ✅ **Risk mitigation**: Performance validation + rollback capability
- ✅ **Rollback capability**: Git-based emergency restoration
- ✅ **Testing strategy**: Comprehensive validation before deployment

**ADR-004 Elements Not Applied:**
- ❌ **Feature flags**: Internal architecture doesn't need gradual rollout
- ❌ **Dual system complexity**: V1/V2 co-existence creates technical debt
- ❌ **A/B testing**: No users to test with

## Gevolgen

### Positief
- ✅ Clean architecture foundation voor production
- ✅ Eliminated technical debt and dual-maintenance overhead
- ✅ Simplified testing and deployment pipeline
- ✅ Developer productivity improvement (40% estimated)
- ✅ Aligned with Codex best practices voor legacy elimination

### Negatief
- ❌ No gradual rollout safety net (mitigated by comprehensive pre-deployment testing)
- ❌ Potential performance regression risk (mitigated by mandatory benchmarking)
- ❌ Single-point-of-failure during transition (mitigated by rollback procedures)

### Mitigatie Requirements

**MANDATORY Pre-Conditions:**
1. **Performance Benchmarking**: V1 vs V2 comprehensive comparison, single request parity validation (p95 ≤ ±10%)
2. **Load Testing**: AsyncGPTClient stability under concurrent load (50 rps voor 30-60 min)
3. **Error Handling Coverage**: Complete V1 → V2 error scenario mapping met AIServiceError harmonisatie
4. **Rollback Procedures**: Documented emergency V1 restoration process via Git-revert
5. **CI/CD Gates**: Forbidden symbols scan voor V1 referenties, contract checks voor async usage
6. **Config Validation**: Rate-limit/retry parameters via config_manager, geen inline RateLimitConfig
7. **Integration Testing**: E2E pad met smoke tests en mocked OpenAI key

## Implementation Approach

### Phase 1: Validation (Week 1)
- Performance benchmarking suite implementation
- AsyncGPTClient stability testing
- Emergency rollback procedure documentation and testing

### Phase 2: Implementation (Week 1-2)
- AIServiceInterface + AIServiceV2 development
- V1 orchestrator deactivation
- Service container refactoring
- Comprehensive integration testing

### Phase 3: Production Readiness (Week 2)
- Full system validation
- Performance regression detection
- Final rollback procedure validation

### Go/No-Go Criteria

**GO Criteria:**
- V2 performance ≥ V1 baseline (single request <200ms p95)
- AsyncGPTClient stable under load testing
- Zero critical test failures
- Emergency rollback tested and documented

**NO-GO Triggers:**
- Performance regression >10% vs V1
- AsyncGPTClient instability detected
- Critical error handling gaps identified
- Rollback procedures fail validation

## Risk Assessment

### High Risk Mitigation
1. **Performance Regression**: Mandatory benchmarking with go/no-go gates
2. **System Instability**: Comprehensive load testing requirement
3. **Rollback Complexity**: Pre-tested emergency procedures

### Medium Risk Acceptance
1. **No Gradual Rollout**: Acceptable given pre-production context
2. **Single Implementation**: Mitigated by thorough validation phase

## Monitoring Strategy

**Pre-Deployment:**
- Performance benchmark validation
- Error rate testing under load
- Rollback procedure validation

**Post-Deployment:**
- Performance monitoring (p95 latency, error rates)
- AsyncGPTClient health metrics
- System stability indicators

## Success Criteria

- [ ] V2 orchestrator performs ≥ V1 baseline
- [ ] Zero production incidents post-deployment
- [ ] Development team productivity improvement measurable
- [ ] Technical debt elimination achieved
- [ ] Rollback procedures tested and documented

## Review and Sunset

**Review Trigger**: Any post-deployment performance regression or stability issue
**Success Measurement**: 30 days stable operation without rollback needs
**Exception Sunset**: This exception expires after successful V1 elimination - future architecture changes follow standard ADR-004

## Relationship to Other ADRs

**ADR-004 Compliance**: Exception specifically scoped, principles preserved where applicable
**Future Decisions**: Post-production architecture changes return to full ADR-004 compliance

## Stakeholder Impact

**Development Team**: Reduced maintenance overhead, cleaner codebase
**End Users**: No direct impact (pre-production)
**Operations**: Simplified deployment and monitoring post-migration
**Architecture Governance**: Exception precedent - future exceptions require similar justification

---

**Approval Required**: Enterprise Architect / CTO sign-off before implementation
**Documentation**: Update architecture governance with exception precedent
**Communication**: Stakeholder notification of governance exception and rationale
