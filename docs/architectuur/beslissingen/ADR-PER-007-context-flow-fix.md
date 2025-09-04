---
canonical: true
status: proposed
owner: architecture
last_verified: 2025-09-04
applies_to: definitie-app@v2
---

# ADR-PER-007: Context Flow Fix for Justice Domain Integration

## Status
**Proposed** - Under Review

## Context

The current DefinitieAgent application collects three critical context fields through the UI:
- `organisatorische_context` (list[str]) - Organization context like "DJI", "OM", "KMAR"
- `juridische_context` (list[str]) - Legal domain context like "Strafrecht", "Bestuursrecht"
- `wettelijke_basis` (list[str]) - Legal basis references like "Art. 27 Sv", "Art. 6:162 BW"

However, these fields are NOT properly mapped through the system architecture:
1. The `GenerationRequest` interface lacks these three specific list fields
2. The `definition_generator_context.py` only processes generic `context: str`
3. Context categorization happens through string parsing instead of explicit field mapping
4. The modular prompt system doesn't receive structured context data

This violates ASTRA guidelines for justice chain integration which require explicit context handling.

## Decision

We will implement a three-phase approach to fix the context flow while maintaining backward compatibility:

### Phase 1: Interface Extension (Non-breaking)
- Extend `GenerationRequest` with optional fields:
  ```python
  organisatorische_context: list[str] | None = None
  juridische_context: list[str] | None = None
  wettelijke_basis: list[str] | None = None
  ```
- Maintain existing `context: str` field for backward compatibility
- Follow Interface Segregation Principle (ISP) from SOLID

### Phase 2: Context Mapping Enhancement
- Update `HybridContextManager._build_base_context()` to:
  - First check for new explicit fields
  - Map directly to appropriate categories without parsing
  - Fall back to string parsing only when new fields are absent
- Implement validation against ASTRA organization registry

### Phase 3: Modular Prompt Integration
- Update `context_awareness_module.py` to consume structured context
- Pass context through `EnrichedContext` dataclass to prompt orchestrator
- Ensure context appears in correct prompt sections

## Consequences

### Positive
1. **ASTRA Compliance**: Meets justice sector requirements for explicit context handling
2. **Data Quality**: Eliminates ambiguity in context categorization
3. **Validation**: Enables validation against official registries (ASTRA organizations)
4. **Modularity**: Maintains clean separation between UI, services, and prompt generation
5. **Backward Compatibility**: Existing integrations continue to work unchanged
6. **Auditability**: Clear data flow for compliance auditing

### Negative
1. **Interface Complexity**: Three additional fields in `GenerationRequest`
2. **Migration Effort**: UI components need updating to use new fields
3. **Testing Overhead**: Additional test scenarios for field combinations

### Neutral
1. **Performance**: Minimal impact (<10ms) for direct mapping vs parsing
2. **Storage**: Slight increase in request payload size

## Architecture Alignment

### Modular Prompt Architecture
- ✅ Maintains module independence (context_awareness_module remains isolated)
- ✅ Uses existing `EnrichedContext` dataclass for data flow
- ✅ No changes to prompt orchestrator required

### Clean Architecture (SA Document)
- ✅ Follows layered architecture: UI → Facade → Services → Repository
- ✅ Data flows through proper DTOs (GenerationRequest, EnrichedContext)
- ✅ No direct UI coupling in business logic

### ASTRA Guidelines
- ✅ Organizations validated against official registry
- ✅ Legal references follow Dutch citation standards
- ✅ Context categories align with justice domain taxonomy

### NORA Principles
- ✅ **Principle 3**: Explicit data modeling for government entities
- ✅ **Principle 7**: Standardized information exchange
- ✅ **Principle 10**: Traceable decision support

## Implementation Risks

### Risk 1: Legacy System Integration
- **Probability**: High
- **Impact**: Medium
- **Mitigation**: Maintain backward compatibility through dual-path processing

### Risk 2: Incomplete Context Migration
- **Probability**: Medium
- **Impact**: Low
- **Mitigation**: Implement feature flag for gradual rollout

### Risk 3: Performance Degradation
- **Probability**: Low
- **Impact**: Low
- **Mitigation**: Direct mapping is faster than parsing; add caching if needed

## Validation Approach

1. **Unit Tests**: Test both new and legacy paths
2. **Integration Tests**: Verify end-to-end context flow
3. **ASTRA Compliance Tests**: Validate organization names
4. **Performance Tests**: Measure context processing time
5. **Regression Tests**: Ensure backward compatibility

## Decision Makers
- Lead Architect: Architecture Team
- Technical Lead: Development Team
- Compliance Officer: Legal/Compliance Team
- Product Owner: Business Team

## Related Decisions
- ADR-005: GVI Pattern Implementation
- ADR-MOD-001: Modular Prompt System Architecture
- ADR-CLEAN-001: Clean Architecture Services

## References
- PER-007 Test Scenarios: `/docs/testing/PER-007-test-scenarios.md`
- ASTRA Architecture Guidelines: https://www.astra.nl/architecture
- NORA Principles: https://www.noraonline.nl/wiki/NORA_online
- Justice Chain Integration Standards: Internal documentation

## Review History
- 2025-09-04: Initial proposal (Architecture Team)
- [Pending]: Technical review (Development Team)
- [Pending]: Compliance review (Legal Team)
- [Pending]: Final approval (Architecture Board)
