---
canonical: true
status: active
owner: architecture
last_verified: 2025-09-04
applies_to: definitie-app@v2-cfr
---

# ADR-015: Context Flow Refactoring Architecture

## Status
Proposed

## Context
The current Definitie-app has critical failures in passing legal context information (juridische_context, wettelijke_basis, organisatorische_context) from the UI to AI prompts. This results in:
- Non-compliant legal definitions lacking required context
- System crashes when users select "Anders..." (custom) options
- Multiple conflicting data paths causing inconsistency
- Type confusion between strings and lists throughout the system
- No audit trail for ASTRA compliance demonstration

## Decision
We will implement a single, unidirectional context flow path with:

1. **Single Path Architecture**: One canonical route from UI → Service → Orchestrator → Prompt
2. **List-First Type System**: All context fields are `List[str]` throughout
3. **Inline Custom Entry Processing**: "Anders..." handled without multiselect widget conflicts
4. **Comprehensive Audit Trail**: Immutable logging of all context usage
5. **Type Validation Layer**: Enforce types at service boundaries

## Consequences

### Positive
- **Compliance**: Full ASTRA traceability for legal definitions
- **Stability**: Elimination of "Anders..." crashes
- **Maintainability**: Single path simplifies debugging and testing
- **Type Safety**: Consistent list types prevent conversion errors
- **Auditability**: Complete context chain-of-custody

### Negative
- **Migration Effort**: Requires updating multiple components
- **Breaking Changes**: Legacy string-based APIs need compatibility layer
- **Storage Costs**: 7-year audit retention requires tiered storage
- **Performance**: Additional validation adds ~100ms latency

## Implementation Plan

### Phase 1: Critical Fixes (Immediate)
```python
# Fix 1: service_factory.py line 229
# OLD: context=", ".join(context_dict.get("organisatorisch", [])),
# NEW:
organisatorische_context=context_dict.get("organisatorisch", []),
juridische_context=context_dict.get("juridisch", []),
wettelijke_basis=context_dict.get("wettelijk", []),

# Fix 2: prompt_service_v2.py lines 158-176
# Properly extract context fields from request
base_context = {
    "organisatorisch": request.organisatorische_context or [],
    "juridisch": request.juridische_context or [],
    "wettelijk": request.wettelijke_basis or [],
}

# Fix 3: context_selector.py Anders... handling
# Use checkbox instead of in-list option
use_custom = st.checkbox("Anders...")
if use_custom:
    custom_value = st.text_input("Custom value")
```

### Phase 2: Type Safety (Week 1)
- Implement `ContextValidator` service
- Add type conversion at boundaries
- Update `GenerationRequest` interface

### Phase 3: Audit Trail (Week 2)
- Deploy `AuditService` with PostgreSQL backend
- Implement immutable logging
- Add compliance reporting

### Phase 4: Cleanup (Week 3)
- Remove legacy paths with feature flags
- Update documentation
- Conduct user training

## Alternatives Considered

### Alternative 1: Minimal Fix
Only fix the immediate bugs without architectural refactoring.
- **Pros**: Quick implementation, low risk
- **Cons**: Technical debt remains, compliance issues persist

### Alternative 2: Complete Rewrite
Build entirely new context system from scratch.
- **Pros**: Clean implementation, optimal design
- **Cons**: High risk, long timeline, service disruption

### Alternative 3: Gradual Migration
Maintain dual paths with progressive migration.
- **Pros**: Low risk, backward compatible
- **Cons**: Complex maintenance, longer total effort

## Validation Criteria

The implementation is successful when:
1. All context fields pass from UI to prompts (verified in logs)
2. "Anders..." option works without crashes (E2E tests pass)
3. Single path verified through dependency analysis
4. Audit reports show 100% context traceability
5. Performance impact < 200ms (p95 latency)

## Technical Debt Addressed

This ADR resolves:
- **TD-001**: Multiple context paths causing maintenance burden
- **TD-002**: String/List type confusion throughout codebase
- **TD-003**: No audit trail for compliance
- **TD-004**: Hardcoded context handling in multiple locations

## References

- [Epic CFR User Stories](../../stories/MASTER-EPICS-USER-STORIES.md#epic-cfr-context-flow-refactoring)
- [EA-CFR](../EA-CFR.md) - Enterprise Architecture
- [SA-CFR](../SA-CFR.md) - Solution Architecture
- [TA-CFR](../TA-CFR.md) - Technical Architecture
- [ASTRA Compliance](../ASTRA_COMPLIANCE.md)
- [Bug Reports CFR-BUG-001/002](../../stories/MASTER-EPICS-USER-STORIES.md#bug-report-cfr-bug-001)
