---
canonical: true
status: active
owner: architecture
last_verified: 2025-09-04
applies_to: definitie-app@v2
---

# PER-007 Context Flow Refactoring - Executive Summary

## Critical Architecture Decision

**THE KEY INSIGHT:** The UI preview string ("📋 Org: OM | ⚖️ Juridisch: Strafrecht | 📜 Wet: Sv") is a **presentation layer artifact** and must **NEVER** be used as a data source for prompt injection.

## What This Means

### ✅ CORRECT Approach (What We're Implementing)
- **Structured lists** (organisatorische_context, juridische_context, wettelijke_basis) are the **ONLY source of truth**
- UI preview is **DERIVED** from EnrichedContext via shared formatter
- Custom "Anders..." entries remain possible within structured lists
- Complete **separation of concerns** between UI and data layers

### ❌ WRONG Approach (What We're Preventing)
- Using concatenated UI strings as data input
- Mixing presentation formatting with business logic
- Parsing emojis and UI decorators for data extraction
- Creating dependencies between UI changes and core functionality

## Business Impact

| Aspect | Without PER-007 | With PER-007 | Business Value |
|--------|----------------|--------------|----------------|
| **Data Integrity** | UI changes break logic | UI independent | Reliability |
| **Custom Entries** | "Anders..." fails | Fully supported | Flexibility |
| **ASTRA Compliance** | Blocking errors | Warnings only | Justice alignment |
| **Maintainability** | UI/logic coupled | Clean separation | Lower TCO |
| **Testing** | UI-dependent tests | Pure logic tests | Quality |

## Implementation Status

### Documents Created/Updated
1. **CFR-CONSOLIDATED-REFACTOR-PLAN.md** - Single source implementation plan (CANONICAL)
2. **ADR-PER-007-presentation-data-separation.md** - Architecture decision record
3. **PER-007-tdd-test-plan.md** - TDD test strategy with CI guards

### Timeline
- **Sprint 1** (Weeks 1-2): Core refactoring - DefinitionGeneratorContext as single source
- **Sprint 2** (Weeks 3-4): UI separation - Implement shared formatters
- **Sprint 3** (Weeks 5-6): Testing & rollout - CI guards, phased deployment

## Technical Safeguards

### Automated Protection
```python
# CI Pipeline Guards (Automatic)
- Block any code using UI preview for data
- Enforce structured list usage
- Validate separation in all PRs
- Prevent regression to old patterns
```

### Architecture Enforcement
- **Single Path:** All context flows through DefinitionGeneratorContext
- **Type Safety:** Structured data types, no string parsing
- **Validation:** ASTRA warnings, never blocking
- **Monitoring:** Metrics on context flow performance

## Key Stakeholders

| Role | Concern | How PER-007 Addresses |
|------|---------|----------------------|
| **Product Owner** | User flexibility | "Anders..." entries fully supported |
| **Justice Domain Expert** | ASTRA compliance | Proper validation without blocking |
| **Development Team** | Code maintainability | Clean separation of concerns |
| **QA Team** | Testability | UI-independent testing |
| **Operations** | Production stability | Phased rollout with fallback |

## Risk Mitigation

### Identified Risks
1. **Breaking existing flows** → Mitigated by phased rollout
2. **Custom entry failures** → Solved by structured list support
3. **ASTRA validation blocks** → Changed to warnings only
4. **Regression to old patterns** → Prevented by CI guards

### Rollback Strategy
- Feature flags for instant rollback
- Parallel legacy path during transition
- Comprehensive smoke tests before cutover

## Success Criteria

✅ **Must Have**
- UI preview NEVER used as data source
- All tests pass with new architecture
- "Anders..." entries work without errors
- ASTRA compliance as warnings only

✅ **Should Have**
- Performance improvement (<5s generation)
- Reduced code complexity
- Better test coverage (>80%)
- Clear documentation

## Next Steps

1. **Immediate:** Review and approve this executive summary
2. **Week 1:** Begin Sprint 1 implementation
3. **Week 2:** First integration tests
4. **Week 4:** Sprint 2 UI separation
5. **Week 6:** Production deployment

## Questions & Approval

**For approval or questions, contact:**
- Architecture Team: For technical decisions
- Product Owner: For business impact
- QA Lead: For testing strategy

**Document Status:** READY FOR APPROVAL
**Priority:** CRITICAL - Blocks production deployment

---
*Generated: 2025-09-04 by Doc Standards Guardian*
