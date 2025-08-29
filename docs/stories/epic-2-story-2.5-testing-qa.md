# Story 2.5: Testing & Quality Assurance

**Epic**: Epic 2 - ValidationOrchestratorV2 Implementation  
**Status**: Ready  
**Priority**: Critical  
**Size**: 8 story points  
**Duration**: 4 days  
**Owner**: QA Engineer + Developer  

## User Story

**Als een** QA engineer,  
**Wil ik** comprehensive test coverage voor de complete validation layer,  
**Zodat** we volledige vertrouwen hebben in de productie deployment en kunnen aantonen dat alle validation scenarios correct werken.

## Business Value

- Provides confidence in production deployment readiness
- Establishes baseline voor performance regression detection  
- Creates comprehensive test suite voor future validation changes
- Enables automated quality gates in CI/CD pipeline

## Acceptance Criteria

### AC1: Unit Test Coverage
- [ ] 95%+ line coverage voor ValidationOrchestratorV2 class
- [ ] 95%+ line coverage voor all validation interfaces
- [ ] 100% branch coverage voor error handling paths
- [ ] All async patterns properly tested

### AC2: Integration Test Suite
- [ ] End-to-end validation flow tests
- [ ] DefinitionOrchestrator integration tests  
- [ ] API endpoint integration tests
- [ ] Feature flag integration tests
- [ ] Container wiring integration tests

### AC3: Contract Compliance Testing
- [ ] ValidationResult schema compliance verified
- [ ] Interface contract adherence tested
- [ ] Error code format validation
- [ ] Response format backward compatibility

### AC4: Performance & Load Testing  
- [ ] Performance benchmarks established
- [ ] Load testing voor concurrent validation
- [ ] Memory usage profiling
- [ ] Latency regression testing

## Technical Tasks

### Unit Testing Infrastructure
- [ ] Create comprehensive test fixtures voor ValidationResult objects
- [ ] Mock AIServiceV2 integration voor isolated testing
- [ ] Create test utilities voor async validation testing
- [ ] Add parametrized tests voor different validation scenarios
- [ ] Create golden dataset test cases

### ValidationOrchestratorV2 Unit Tests
- [ ] Test `validate_text()` success paths
- [ ] Test `validate_definition()` comprehensive scenarios  
- [ ] Test `batch_validate()` parallel processing
- [ ] Test error handling en resilience patterns
- [ ] Test timeout scenarios en graceful degradation
- [ ] Test correlation ID propagation

### Integration Testing Suite
- [ ] Create integration test framework voor validation flows
- [ ] Test DefinitionOrchestratorV2 ↔ ValidationOrchestratorV2 integration
- [ ] Test API endpoint validation workflows
- [ ] Test background job validation integration
- [ ] Test feature flag switching during runtime

### Contract Compliance Tests
- [ ] JSON Schema validation tests voor all ValidationResult outputs
- [ ] Interface contract adherence verification  
- [ ] Error code format en consistency testing
- [ ] Response compatibility with legacy systems
- [ ] API contract testing (input/output validation)

### Performance Testing Framework
- [ ] Establish performance baselines voor V1 vs V2
- [ ] Load testing setup voor concurrent validations
- [ ] Memory profiling tests voor leak detection
- [ ] Latency distribution testing (P50, P95, P99)
- [ ] Throughput testing voor batch operations

### Golden Dataset Testing
- [ ] Create representative validation dataset
- [ ] Generate expected ValidationResult outputs
- [ ] Test V1 vs V2 output consistency
- [ ] Add regression testing voor critical validation cases
- [ ] Document validation behavior changes

## Definition of Done

- [ ] Unit test coverage > 95% voor all validation components
- [ ] Integration tests cover all major workflows
- [ ] Contract compliance tests pass 100%
- [ ] Performance tests meet established benchmarks
- [ ] Golden dataset regression tests implemented
- [ ] Test suite runs in < 10 minutes in CI
- [ ] Code review approved by QA lead en senior developer
- [ ] Test documentation is complete

## Test Scenarios

### Unit Test Examples
```python
class TestValidationOrchestratorV2:
    async def test_validate_text_success(self):
        orchestrator = ValidationOrchestratorV2(mock_ai_service, mock_validator)
        context = ValidationContext(correlation_id=uuid4())
        
        result = await orchestrator.validate_text("Goed geschreven definitie.", context)
        
        assert isinstance(result, ValidationResult)
        assert result.version == "1.0.0"
        assert 0.0 <= result.overall_score <= 1.0
        assert result.system.correlation_id == context.correlation_id
        assert len(result.passed_rules) > 0

    async def test_validate_text_with_violations(self):
        orchestrator = ValidationOrchestratorV2(mock_ai_service, mock_validator)
        
        result = await orchestrator.validate_text("slecht geschreven tekst", context)
        
        assert result.overall_score < 0.5
        assert result.is_acceptable == False
        assert len(result.violations) > 0
        assert all(v.code.startswith("VAL-") for v in result.violations)

    async def test_batch_validate_performance(self):
        items = [create_test_text() for _ in range(50)]
        start_time = time.time()
        
        results = await orchestrator.batch_validate(items)
        duration = time.time() - start_time
        
        assert len(results) == 50
        assert duration < 30  # Should be much faster than sequential
```

### Integration Test Examples
```python
class TestValidationIntegration:
    async def test_definition_orchestrator_integration(self):
        # Full integration test via DefinitionOrchestratorV2
        definition_result = await definition_orchestrator.create_definition(
            text="Test definitie tekst",
            validate=True
        )
        
        assert definition_result.validation is not None
        assert isinstance(definition_result.validation, ValidationResult)
        
    async def test_api_endpoint_integration(self):
        response = await client.post("/api/definitions/validate", json={
            "text": "Test definitie voor API validatie",
            "profile": "standard"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response matches ValidationResult schema
        validate_json_schema(data, validation_result_schema)
```

### Contract Compliance Tests
```python
class TestContractCompliance:
    def test_validation_result_schema_compliance(self):
        # Test various ValidationResult scenarios
        test_cases = [
            create_successful_validation_result(),
            create_failed_validation_result(),
            create_partial_validation_result(),
        ]
        
        for result in test_cases:
            # Should validate against JSON schema
            validate_json_schema(result.to_dict(), validation_result_schema)
            
    def test_error_code_format_consistency(self):
        result = create_validation_with_violations()
        
        for violation in result.violations:
            # All error codes should match VAL-XXX-000 format
            assert re.match(r"^[A-Z]{3}-[A-Z]{3}-\d{3}$", violation.code)
```

### Performance Tests
```python
class TestValidationPerformance:
    async def test_single_validation_latency(self):
        measurements = []
        
        for _ in range(100):
            start = time.time()
            result = await orchestrator.validate_text("Test tekst", context)
            duration = time.time() - start
            measurements.append(duration)
        
        p95_latency = numpy.percentile(measurements, 95)
        assert p95_latency < 2.0  # P95 should be under 2 seconds
        
    async def test_batch_validation_throughput(self):
        batch_sizes = [10, 50, 100, 200]
        
        for batch_size in batch_sizes:
            items = [create_test_text() for _ in range(batch_size)]
            
            start = time.time()
            results = await orchestrator.batch_validate(items)
            duration = time.time() - start
            
            throughput = batch_size / duration
            assert throughput > 5  # Should process > 5 items per second
```

## Dependencies

### Prerequisites
- [ ] Stories 2.1-2.4 completed (interface, implementation, wiring, integration)
- [ ] Test infrastructure en CI pipeline ready
- [ ] Performance testing tools available
- [ ] Golden dataset prepared

### Testing Infrastructure
- [ ] pytest-asyncio voor async test support
- [ ] Mock frameworks voor AI service simulation
- [ ] JSON Schema validation libraries
- [ ] Performance profiling tools
- [ ] Load testing framework

## Test Data Strategy

### Golden Dataset
- **Size**: 500 representative validation cases
- **Coverage**: All validation rule categories (taal, juridisch, structuur, samenhang)
- **Formats**: Various text lengths en complexity levels
- **Expected Results**: Pre-validated V1 outputs voor comparison

### Test Fixtures
```python
@pytest.fixture
def sample_validation_context():
    return ValidationContext(
        correlation_id=uuid4(),
        profile="standard",
        metadata={"test": True}
    )

@pytest.fixture  
def mock_ai_service():
    service = Mock(spec=AsyncGPTClient)
    service.validate_text.return_value = create_mock_ai_response()
    return service
```

## Quality Gates

### CI/CD Pipeline Integration
- [ ] All tests must pass before merge to main branch
- [ ] Code coverage must be > 95%
- [ ] Performance tests must not regress > 5%
- [ ] Contract compliance tests must pass 100%
- [ ] Security scans must pass

### Performance Benchmarks
- **Single Validation**: P95 < 2 seconds
- **Batch Validation**: > 100 items per minute  
- **Memory Usage**: < 100MB increase voor concurrent processing
- **Error Rate**: < 1% under normal load

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Test suite too slow for CI | Medium | Medium | Optimize test execution, parallel testing |
| Flaky async tests | Medium | Medium | Proper test isolation, deterministic mocking |
| Golden dataset becomes stale | Medium | Low | Automated dataset refresh, version control |
| Performance tests inconsistent | Medium | Medium | Dedicated performance testing environment |

## Test Environment Requirements

### Development Testing
- Local pytest execution
- Mock AI services
- SQLite test database
- Docker containers voor isolation

### CI/CD Testing  
- Parallel test execution
- Shared test database
- Mock external services
- Performance baseline storage

### Load Testing Environment
- Production-like infrastructure
- Real AI service integration (separate tenant)
- Monitoring en metrics collection
- Automated load generation

## Success Metrics

- [ ] Test coverage: > 95% line coverage, 100% branch coverage voor critical paths
- [ ] Test reliability: < 0.1% flaky test rate
- [ ] Test execution time: Complete suite in < 10 minutes
- [ ] Performance validation: All benchmarks within target ranges
- [ ] Contract compliance: 100% schema adherence

---

**Created**: 2025-08-29  
**Story Owner**: QA Engineer  
**Technical Reviewer**: Senior Developer  
**Stakeholders**: Development Team, QA Team, DevOps