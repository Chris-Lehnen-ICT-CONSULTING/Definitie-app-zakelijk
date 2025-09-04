# Story 2.2: ValidationOrchestratorV2 Core Implementation

**Epic**: Epic 2 - ValidationOrchestratorV2 Implementation
**Status**: Ready
**Priority**: Critical
**Size**: 8 story points
**Duration**: 4 days
**Owner**: Senior Developer

## User Story

**Als een** development team,
**Wil ik** de core ValidationOrchestratorV2 implementatie met async/await patterns,
**Zodat** we moderne, performante validatie logic hebben die volledig gescheiden is van definitie-generatie.

## Business Value

- Provides dedicated validation orchestration separated from definition generation
- Enables 3-5x performance improvement voor batch validation operations
- Creates foundation voor distributed validation processing
- Establishes modern async architecture patterns voor team

## Acceptance Criteria

### AC1: Core Class Implementation
- [ ] `ValidationOrchestratorV2` class implements `ValidationOrchestratorInterface`
- [ ] All 3 async methods zijn volledig geïmplementeerd en functional
- [ ] Class uses `AsyncGPTClient` voor AI service communication
- [ ] Error handling is robust with proper exception types

### AC2: Async Pattern Compliance
- [ ] All methods zijn native async (geen sync wrappers)
- [ ] Proper use van `asyncio` patterns (geen blocking calls)
- [ ] Context managers voor resource cleanup
- [ ] Cancellation support voor long-running operations

### AC3: Error Catalog Integration
- [ ] Standardized error codes volgens VAL-XXX-000 format
- [ ] Error catalog mapping voor all common failure scenarios
- [ ] Proper severity levels (info, warning, error)
- [ ] User-friendly error messages in Dutch/English

### AC4: Telemetry & Observability
- [ ] Correlation ID propagation door all operations
- [ ] Performance timing measurements
- [ ] Structured logging with relevant context
- [ ] Metrics hooks voor monitoring integration

## Technical Tasks

### Core Implementation
- [ ] Create `src/services/validation/validation_orchestrator_v2.py`
- [ ] Implement class constructor met dependency injection
- [ ] Implement `validate_text()` method met AI service integration
- [ ] Implement `validate_definition()` method met definition-specific logic
- [ ] Implement `batch_validate()` method met parallel processing
- [ ] Add proper async context management

### AI Service Integration
- [ ] Integrate with `AsyncGPTClient` voor validation requests
- [ ] Implement prompt engineering voor validation tasks
- [ ] Add retry logic met exponential backoff
- [ ] Handle rate limiting gracefully
- [ ] Parse AI responses into ValidationResult format

### Error Handling & Resilience
- [ ] Define ValidationError exception hierarchy
- [ ] Implement timeout handling voor slow validations
- [ ] Add graceful degradation voor partial failures
- [ ] Create error code catalog in `src/validation/errors.py`
- [ ] Add circuit breaker pattern voor AI service calls

### Batch Processing
- [ ] Implement parallel processing met `asyncio.gather()`
- [ ] Add batch size limits en chunking
- [ ] Handle partial batch failures gracefully
- [ ] Implement progress tracking voor large batches
- [ ] Add concurrency control (max parallel validations)

### Telemetry & Logging
- [ ] Add structured logging met correlation IDs
- [ ] Implement timing measurements voor performance tracking
- [ ] Add custom metrics voor monitoring dashboards
- [ ] Create telemetry context manager
- [ ] Add debug logging voor troubleshooting

## Definition of Done

- [ ] ValidationOrchestratorV2 class fully implements interface
- [ ] All async methods functional met proper error handling
- [ ] Integration tests pass met AIServiceV2
- [ ] Performance benchmarks meet targets (< 5% regression)
- [ ] Error catalog is complete en documented
- [ ] Telemetry produces useful metrics
- [ ] Code review approved by senior developer
- [ ] Security review completed (input validation, etc.)

## Test Scenarios

### Core Functionality Tests
```python
async def test_validate_text_success():
    orchestrator = ValidationOrchestratorV2(ai_service, validator)
    context = ValidationContext(correlation_id=uuid4())

    result = await orchestrator.validate_text("Test tekst", context)

    assert isinstance(result, ValidationResult)
    assert result.version == "1.0.0"
    assert 0.0 <= result.overall_score <= 1.0
    assert result.system.correlation_id == context.correlation_id

async def test_batch_validate_parallel():
    items = [create_validation_item() for _ in range(50)]
    start_time = time.time()

    results = await orchestrator.batch_validate(items)
    duration = time.time() - start_time

    assert len(results) == 50
    assert duration < 30  # Should be much faster than sequential
```

### Error Handling Tests
```python
async def test_ai_service_timeout():
    # Mock timeout scenario
    result = await orchestrator.validate_text("test", context, timeout=0.001)

    assert result.system.error is not None
    assert "timeout" in result.system.error.lower()
    assert result.is_acceptable == False

async def test_invalid_input_handling():
    with pytest.raises(ValidationError) as exc_info:
        await orchestrator.validate_text("", None)

    assert exc_info.value.code.startswith("VAL-")
```

### Performance Tests
```python
async def test_batch_performance_target():
    items = [create_large_validation_item() for _ in range(100)]

    start = time.time()
    results = await orchestrator.batch_validate(items)
    duration = time.time() - start

    # Should be at least 3x faster than sequential processing
    assert duration < sequential_baseline / 3
```

## Dependencies

### Prerequisites
- [ ] Story 2.1 completed (ValidationOrchestratorInterface)
- [ ] AIServiceV2 is operational met AsyncGPTClient
- [ ] Modern validation rules available in `src/validation/`
- [ ] JSON Schema voor ValidationResult is locked

### Integration Dependencies
- [ ] `AsyncGPTClient` voor AI service calls
- [ ] `ValidationResult` dataclass en serialization
- [ ] Error catalog infrastructure
- [ ] Logging en monitoring infrastructure

## Performance Requirements

- **Latency**: Single validation < 2 seconds P95
- **Throughput**: Batch validation > 100 items per minute
- **Memory**: < 100MB increase voor 100 concurrent validations
- **Error Rate**: < 1% failures onder normal load
- **Recovery**: < 30 seconds recovery from AI service outage

## Security Considerations

- [ ] Input sanitization voor all text inputs
- [ ] Rate limiting to prevent abuse
- [ ] Secure storage van correlation IDs
- [ ] No sensitive data in logs
- [ ] Proper exception sanitization (geen data leaks)

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| AI service reliability issues | High | Medium | Circuit breaker, graceful degradation |
| Memory leaks in async processing | Medium | Low | Proper context managers, testing |
| Performance regression vs V1 | High | Medium | Continuous benchmarking |
| Complex async debugging | Medium | Medium | Comprehensive logging, correlation IDs |

## Integration Points

- **AIServiceV2**: Primary dependency voor validation logic
- **ValidationInterface**: Implements the interface contract
- **Container System**: Dependency injection registration
- **Monitoring**: Metrics en alerting integration
- **DefinitionOrchestratorV2**: Will consume this orchestrator

## Success Metrics

- [ ] Implementation completeness: All 3 methods functional
- [ ] Performance targets: Meet latency/throughput requirements
- [ ] Error handling: All scenarios gracefully handled
- [ ] Code quality: Zero critical issues in code review
- [ ] Test coverage: > 95% line coverage

---

**Created**: 2025-08-29
**Story Owner**: Senior Developer
**Technical Reviewer**: Senior Architect
**Stakeholders**: Development Team, Performance Team
