# Story 2.4: Integration & Migration

# Story 2.4: Integration & Migration

---
canonical: true
status: active
owner: validation
last_verified: 2025-09-02
applies_to: definitie-app@v2
---

**Epic**: Epic 2 - ValidationOrchestratorV2 Implementation
**Status**: Ready
**Priority**: Critical
**Size**: 8 story points
**Duration**: 3 days
**Owner**: Senior Developer

## User Story

**Als een** integrator,
**Wil ik** DefinitionOrchestratorV2 volledig geïntegreerd met ValidationOrchestratorV2,
**Zodat** alle validation flows via de nieuwe orchestrator lopen en we een clean separation of concerns hebben.

## Business Value

- Completes separation tussen definitie-generatie en validatie logic
- Eliminates legacy validation coupling in definition orchestrator
- Enables independent scaling van validation services
- Provides foundation voor advanced validation workflows

## Acceptance Criteria

### AC1: DefinitionOrchestratorV2 Integration
- [ ] DefinitionOrchestratorV2 gebruikt ValidationOrchestratorInterface instead van direct validator calls
- [ ] All validation logic removed from DefinitionOrchestratorV2 class
- [ ] Proper async integration with ValidationOrchestratorV2
- [ ] No breaking changes to existing DefinitionOrchestrator API

### AC2: DefinitionValidator V2 Mapping
- [ ] DefinitionValidator.validate_definition() routed through ValidationOrchestratorV2
- [ ] Response mapping maintains backward compatibility
- [ ] Error handling properly delegates to ValidationOrchestrator
- [ ] Performance comparable to direct validation calls

### AC3: Migration of Existing Validation Calls
- [ ] All direct validation calls in codebase updated
- [ ] API endpoints use ValidationOrchestratorInterface
- [ ] Background job validation migrated
- [ ] Batch processing flows updated

### AC4: Clean Cutover Validation
- [ ] Existing API contracts maintained (no breaking changes)
- [ ] Legacy response formats supported via mapping
- [ ] V1 adapter fully removed from dependency injection
- [ ] Golden tests validate business logic preservation

## Technical Tasks

### DefinitionOrchestratorV2 Integration
- [ ] Update `src/services/definition/definition_orchestrator_v2.py`
- [ ] Replace direct validation calls met ValidationOrchestratorInterface
- [ ] Remove validation logic from definition orchestrator
- [ ] Update constructor voor ValidationOrchestrator dependency injection
- [ ] Add proper error handling en logging

### DefinitionValidator V2 Mapping
- [ ] Update `src/services/validation/definition_validator.py`
- [ ] Create V2 implementation that delegates to ValidationOrchestratorV2
- [ ] Maintain existing method signatures
- [ ] Add response format conversion
- [ ] Implement proper error mapping

### API Endpoint Migration
- [ ] Update `/api/definitions/validate` endpoint
- [ ] Update `/api/definitions/create` validation flow
- [ ] Update `/api/validation/batch` endpoint
- [ ] Add endpoint versioning support
- [ ] Maintain response format consistency

### Background Job Integration
- [ ] Update definition processing jobs
- [ ] Update bulk validation jobs
- [ ] Add proper async/await support in job handlers
- [ ] Update job error handling
- [ ] Add job performance monitoring

### Response Format Compatibility
- [ ] Create response adapter voor legacy formats
- [ ] Add versioned API response handling
- [ ] Implement backward-compatible error codes
- [ ] Add response validation tests
- [ ] Create format conversion utilities

## Definition of Done

- [ ] DefinitionOrchestratorV2 fully integrated met ValidationOrchestratorV2
- [ ] All existing validation calls migrated
- [ ] No breaking changes to public APIs
- [ ] Feature flag controls migration rollout
- [ ] Integration tests pass 100%
- [ ] Performance regression < 5%
- [ ] Code review approved
- [ ] Migration guide documented

## Test Scenarios

### Integration Tests
```python
async def test_definition_orchestrator_uses_validation_orchestrator():
    definition_orchestrator = container.resolve(DefinitionOrchestratorV2)

    # Should delegate validation to ValidationOrchestratorV2
    result = await definition_orchestrator.create_definition(
        text="Test definitie",
        validate=True
    )

    # Verify validation was performed via ValidationOrchestrator
    assert result.validation_result is not None
    assert isinstance(result.validation_result, ValidationResult)
```

### API Compatibility Tests
```python
async def test_validate_endpoint_backward_compatibility():
    response = await client.post("/api/definitions/validate", json={
        "text": "Test definitie",
        "profile": "standard"
    })

    # Response format should match legacy format
    assert response.status_code == 200
    assert "overall_score" in response.json()
    assert "is_acceptable" in response.json()
    assert "violations" in response.json()
```

### Migration Flow Tests
```python
async def test_validation_flow_with_feature_flag():
    # Test both V1 and V2 paths produce compatible results

    # V1 path (feature flag disabled)
    with feature_flag("VALIDATION_ORCHESTRATOR_V2", False):
        result_v1 = await validate_definition(test_definition)

    # V2 path (feature flag enabled)
    with feature_flag("VALIDATION_ORCHESTRATOR_V2", True):
        result_v2 = await validate_definition(test_definition)

    # Results should be functionally equivalent
    assert result_v1.is_acceptable == result_v2.is_acceptable
    assert abs(result_v1.overall_score - result_v2.overall_score) < 0.1
```

### Performance Tests
```python
async def test_integration_performance():
    # V2 should not be significantly slower than V1
    test_items = [create_test_definition() for _ in range(100)]

    start_time = time.time()
    results = await definition_orchestrator.batch_validate_definitions(test_items)
    duration = time.time() - start_time

    # Should complete within performance budget
    assert duration < v1_baseline * 1.05  # Max 5% regression
    assert len(results) == 100
```

## Dependencies

### Prerequisites
- [ ] Story 2.1 completed (ValidationOrchestratorInterface)
- [ ] Story 2.2 completed (ValidationOrchestratorV2 core)
- [ ] Story 2.3 completed (Container wiring)
- [ ] DefinitionOrchestratorV2 exists en is functional

### Integration Dependencies
- [ ] ValidationOrchestratorInterface properly registered in container
- [ ] Feature flags infrastructure operational
- [ ] API versioning framework available
- [ ] Migration testing environment ready

## Migration Strategy

### Phase 1: Interface Integration
1. Update DefinitionOrchestratorV2 to use ValidationOrchestratorInterface
2. Create adapter layer voor response compatibility
3. Add feature flag gating
4. Test in development environment

### Phase 2: Call Site Migration
1. Update API endpoints to use new validation flow
2. Migrate background job validation calls
3. Update batch processing workflows
4. Add comprehensive integration tests

### Phase 3: Compatibility Validation
1. Run parallel validation tests (V1 vs V2)
2. Validate response format compatibility
3. Performance testing en optimization
4. Documentation updates

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Integration bugs causing validation failures | High | Medium | Comprehensive integration tests, feature flags |
| Performance regression in critical paths | Medium | Medium | Performance testing, optimization |
| Response format incompatibilities | High | Low | Adapter layer, backward compatibility tests |
| Complex error handling edge cases | Medium | Medium | Error scenario testing, fallback mechanisms |

## Performance Requirements

- **Integration Overhead**: < 50ms additional latency per validation
- **Memory Usage**: No significant increase in memory footprint
- **Throughput**: Support same validation throughput as V1
- **Error Rate**: < 0.1% increase in validation errors
- **Response Time**: P95 < 5 seconds voor single validations

## Backward Compatibility

### API Response Format
```json
{
  "overall_score": 0.85,
  "is_acceptable": true,
  "violations": [...],
  "passed_rules": [...],
  "detailed_scores": {...},
  "_metadata": {
    "orchestrator_version": "v2",
    "schema_version": "1.0.0"
  }
}
```

### Deprecated Patterns
- Direct validator instantiation → Use ValidationOrchestratorInterface
- Sync validation calls → Use async ValidationOrchestrator methods
- Manual error code mapping → Use ValidationResult error catalog

## Integration Points

- **DefinitionOrchestratorV2**: Primary integration point
- **API Layer**: All validation endpoints
- **Background Jobs**: Async validation processing
- **Batch Processing**: Bulk validation workflows
- **Error Handling**: Centralized error processing

## Success Metrics

- [ ] Integration completeness: 100% validation calls migrated
- [ ] Compatibility: Zero breaking changes in API responses
- [ ] Performance: < 5% regression in validation throughput
- [ ] Reliability: < 0.1% increase in validation error rate
- [ ] Feature coverage: All existing validation features supported

---

**Created**: 2025-08-29
**Story Owner**: Senior Developer
**Technical Reviewer**: Senior Architect
**Stakeholders**: Development Team, API Team, QA Engineer
