---
canonical: true
status: accepted
owner: architecture
last_verified: 2025-09-04
applies_to: definitie-app@v2
supersedes: [ADR-CFR-001, ADR-PER-007]
---

# ADR-016: Consolidated Context Flow Architecture

## Status
ACCEPTED

## Context

The Definitie-app suffered from critical context flow issues where justice domain context (organisatorische_context, juridische_context, wettelijke_basis) collected in the UI was not properly transmitted to AI prompts. This resulted in non-compliant legal definitions lacking required contextual information.

Multiple parallel efforts to address this issue (PER-007 and CFR initiatives) created:
- Documentation overlap and confusion
- Multiple proposed solutions without clear implementation path
- Competing architectural decisions
- Fragmented test scenarios

Additionally, the "Anders..." (custom entry) option in the UI caused system crashes and data loss, while ASTRA compliance requirements were interpreted as hard constraints that would block legitimate use cases.

## Decision

We will implement a consolidated context flow architecture with the following key decisions:

### 1. Single Source of Truth
**DefinitionGeneratorContext** will be THE sole component responsible for all context operations. All context data MUST flow through this component, with no alternative paths allowed.

### 2. Explicit Data Flow Path
The canonical data flow will be:
```
UI → GenerationRequest → DefinitionGeneratorContext → EnrichedContext → Prompt
```

No bypasses, shortcuts, or alternative routes are permitted.

### 3. Session State for UI Stability
The "Anders..." custom entry feature will use Streamlit session state to:
- Preserve user selections across rerenders
- Maintain insertion order
- Provide intelligent deduplication
- Handle empty entries gracefully

### 4. Warning-Based ASTRA Compliance
ASTRA validation will:
- Provide warnings and suggestions, not hard failures
- Use fuzzy matching to suggest corrections
- Never block definition generation
- Generate compliance reports for audit purposes

### 5. Enforcement Through Tooling
Legacy paths will be:
- Immediately removed from codebase
- Blocked by linting rules
- Monitored for reintroduction
- Documented as deprecated

## Consequences

### Positive
- **Clear Architecture**: Single, understandable context flow path
- **Improved Maintainability**: No duplicate code or competing implementations
- **Better User Experience**: Stable UI with helpful validation feedback
- **Easier Testing**: Single path to test and validate
- **Compliance Ready**: ASTRA warnings without blocking functionality
- **Performance**: Direct path without multiple parsing steps

### Negative
- **Breaking Change**: Existing integrations must be updated
- **Migration Effort**: All components must be refactored to use new path
- **Initial Complexity**: Session state management adds UI complexity
- **Training Required**: Developers must understand new architecture

### Neutral
- **Documentation Update**: All existing docs must be updated or archived
- **Monitoring Changes**: New metrics and dashboards required
- **Testing Rewrite**: Existing tests must be updated for new flow

## Alternatives Considered

### Alternative 1: Multiple Specialized Paths
**Description**: Maintain separate paths for different context types
**Rejected Because**:
- Increases complexity exponentially
- Difficult to maintain consistency
- Harder to test and debug

### Alternative 2: Hard ASTRA Enforcement
**Description**: Block all non-ASTRA-compliant entries
**Rejected Because**:
- Too restrictive for users
- Prevents legitimate edge cases
- Poor user experience

### Alternative 3: Client-Side Only Solution
**Description**: Handle all context in UI without backend changes
**Rejected Because**:
- Doesn't fix core architectural issue
- State management still problematic
- No validation or enrichment possible

### Alternative 4: Complete Rewrite
**Description**: Rebuild entire context system from scratch
**Rejected Because**:
- Too time consuming
- High risk of introducing new bugs
- Loses existing working functionality

## Implementation

### Phase 1: Foundation (Sprint 1)
1. Implement DefinitionGeneratorContext as single source
2. Remove all legacy context paths
3. Add linting rules to prevent reintroduction
4. Basic session state for "Anders..."

### Phase 2: Enhancement (Sprint 2)
1. Complete EnhancedContextSelector with deduplication
2. Implement ASTRA warning-based validation
3. Add fuzzy matching and suggestions
4. Create comprehensive tests

### Phase 3: Optimization (Sprint 3)
1. Add context caching layer
2. Implement monitoring and analytics
3. Performance optimization
4. Production deployment

## Validation

### Success Criteria
- Single context path verified through code analysis
- Zero legacy path usage in monitoring
- "Anders..." option works without crashes (>95% success rate)
- ASTRA compliance warnings shown but don't block (100% of validations)
- Context appears in 100% of generated prompts
- Performance impact <100ms

### Testing Strategy
- Unit tests for DefinitionGeneratorContext (>90% coverage)
- Integration tests for full context flow
- E2E tests for UI interactions including "Anders..."
- Performance tests for validation overhead
- User acceptance testing with legal professionals

## References

### Superseded Documents
- ADR-CFR-001-context-flow-refactoring.md (archived)
- ADR-PER-007-context-flow-fix.md (archived)
- PER-007-architectural-assessment.md (reference only)
- CFR-SOLUTION-OVERVIEW.md (replaced by consolidated plan)

### Current Documents
- [CFR-CONSOLIDATED-REFACTOR-PLAN.md](../CFR-CONSOLIDATED-REFACTOR-PLAN.md) - Implementation guide
- [SOLUTION_ARCHITECTURE.md](../SOLUTION_ARCHITECTURE.md) - Overall system architecture

### Related Code
- `src/services/definition_generator_context.py` - Primary implementation
- `src/ui/components/enhanced_context_selector.py` - UI improvements
- `src/services/validation/astra_validator.py` - Compliance validation

## Decision Makers

| Role | Name | Date |
|------|------|------|
| Lead Architect | Architecture Team | 2025-09-04 |
| Product Owner | [Pending] | - |
| Tech Lead | [Pending] | - |
| Security Officer | [Pending] | - |

## Review Date

This ADR will be reviewed after Sprint 1 completion (approximately 2025-09-18) to validate the approach based on initial implementation results.
