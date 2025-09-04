# Story 2.3: Container Wiring & Feature Flags

**Epic**: Epic 2 - ValidationOrchestratorV2 Implementation
**Status**: Ready
**Priority**: High
**Size**: 5 story points
**Duration**: 2 days
**Owner**: DevOps Engineer + Developer

## User Story

**Als een** DevOps engineer,
**Wil ik** proper dependency injection wiring met feature flag controle,
**Zodat** we veilig kunnen deployen, testen en rollbacken zonder downtime of risk.

## Business Value

- Enables safe deployment met zero-downtime rollout capability
- Provides instant rollback mechanism bij issues
- Allows environment-specific configuration (dev/test/prod)
- Creates foundation voor A/B testing en gradual feature rollout

## Acceptance Criteria

### AC1: Feature Flag Infrastructure
- [ ] `VALIDATION_ORCHESTRATOR_V2` environment variable properly configures feature activation
- [ ] Feature flag supports boolean values: `true`/`false`, `1`/`0`, `on`/`off`
- [ ] Feature flag defaults to `false` (safe default)
- [ ] Feature flag can be toggled without application restart

### AC2: Container Dual Registration
- [ ] Both ValidationOrchestratorV1 (legacy) en V2 kunnen registered zijn simultaneously
- [ ] Dependency injection correctly resolves based on feature flag
- [ ] No circular dependencies tussen orchestrator implementations
- [ ] Clean interface boundaries maintained

### AC3: Environment Configuration
- [ ] Development environment default: V2 enabled
- [ ] Test environment: configurable per test suite
- [ ] Production environment: V2 disabled by default initially
- [ ] Configuration validation prevents misconfiguration

### AC4: Rollback Procedures
- [ ] Instant rollback via feature flag toggle (< 30 seconds)
- [ ] Rollback procedures documented en tested
- [ ] Health checks validate orchestrator functionality
- [ ] Monitoring alerts op configuration changes

## Technical Tasks

### Feature Flag Implementation
- [ ] Create `src/config/feature_flags.py` module
- [ ] Implement `ValidationOrchestratorFeatureFlag` class
- [ ] Add environment variable parsing met validation
- [ ] Add runtime toggle support (via config reload)
- [ ] Create feature flag configuration schema

### Container Configuration
- [ ] Update `src/container/services.py` voor dual registration
- [ ] Create conditional registration logic
- [ ] Add interface-based resolution in container
- [ ] Implement factory pattern voor orchestrator selection
- [ ] Add container validation tests

### Environment Setup
- [ ] Update `.env.example` met nieuwe configuration
- [ ] Create environment-specific configs in `config/`
- [ ] Add configuration validation in startup
- [ ] Document configuration options
- [ ] Create configuration migration guide

### Health Checks & Monitoring
- [ ] Add health check endpoint voor orchestrator status
- [ ] Create metrics voor feature flag state
- [ ] Add configuration change logging
- [ ] Implement orchestrator readiness probes
- [ ] Create alerting voor unexpected toggles

### Rollback Infrastructure
- [ ] Create rollback playbook documentation
- [ ] Implement configuration hot-reload
- [ ] Add rollback validation tests
- [ ] Create monitoring dashboard voor rollback state
- [ ] Test rollback scenarios in staging environment

## Definition of Done

- [ ] Feature flag infrastructure is operational
- [ ] Container wiring supports both orchestrators
- [ ] Environment configuration is complete en validated
- [ ] Rollback procedures tested en documented
- [ ] Health checks provide accurate orchestrator status
- [ ] Configuration changes zijn properly logged/monitored
- [ ] Code review approved by DevOps en senior developer
- [ ] Infrastructure changes deployed to all environments

## Test Scenarios

### Feature Flag Tests
```python
def test_feature_flag_default_disabled():
    # Without env var, should default to V1
    flag = ValidationOrchestratorFeatureFlag()
    assert flag.is_v2_enabled() == False

def test_feature_flag_various_formats():
    # Test different boolean representations
    test_cases = [
        ("true", True), ("false", False),
        ("1", True), ("0", False),
        ("on", True), ("off", False),
        ("TRUE", True), ("False", False)
    ]
    for env_val, expected in test_cases:
        flag = ValidationOrchestratorFeatureFlag(env_val)
        assert flag.is_v2_enabled() == expected
```

### Container Resolution Tests
```python
def test_container_resolves_v1_when_disabled():
    container = create_test_container(validation_v2=False)

    orchestrator = container.resolve(ValidationOrchestratorInterface)

    assert isinstance(orchestrator, ValidationOrchestratorV1)

def test_container_resolves_v2_when_enabled():
    container = create_test_container(validation_v2=True)

    orchestrator = container.resolve(ValidationOrchestratorInterface)

    assert isinstance(orchestrator, ValidationOrchestratorV2)
```

### Environment Configuration Tests
```python
def test_dev_environment_defaults():
    config = EnvironmentConfig.load("development")

    assert config.validation_orchestrator_v2 == True
    assert config.feature_flags["VALIDATION_ORCHESTRATOR_V2"] == True

def test_prod_environment_safety():
    config = EnvironmentConfig.load("production")

    assert config.validation_orchestrator_v2 == False  # Safe default
```

### Rollback Tests
```python
async def test_instant_rollback():
    # Start with V2 enabled
    container = create_container(validation_v2=True)

    # Simulate feature flag toggle
    start_time = time.time()
    toggle_feature_flag("VALIDATION_ORCHESTRATOR_V2", False)
    container.reload_config()

    # Should resolve to V1 within 30 seconds
    orchestrator = container.resolve(ValidationOrchestratorInterface)
    assert isinstance(orchestrator, ValidationOrchestratorV1)
    assert time.time() - start_time < 30
```

## Dependencies

### Prerequisites
- [ ] Story 2.1 completed (ValidationOrchestratorInterface)
- [ ] Story 2.2 completed (ValidationOrchestratorV2 implementation)
- [ ] Existing container infrastructure in place
- [ ] Feature flag infrastructure available

### Infrastructure Dependencies
- [ ] Dependency injection container (existing)
- [ ] Environment configuration system
- [ ] Health check framework
- [ ] Monitoring en logging infrastructure

## Security Considerations

- [ ] Feature flags kunnen niet be manipulated by end users
- [ ] Configuration changes zijn logged voor audit
- [ ] No sensitive data in feature flag values
- [ ] Proper access controls op configuration files
- [ ] Validation of configuration values to prevent injection

## Environment Configuration

### Development Environment
```bash
# .env.development
VALIDATION_ORCHESTRATOR_V2=true
LOG_LEVEL=DEBUG
FEATURE_FLAG_REFRESH_INTERVAL=10
```

### Test Environment
```bash
# .env.test
VALIDATION_ORCHESTRATOR_V2=${TEST_V2_ENABLED:-false}
LOG_LEVEL=INFO
```

### Production Environment
```bash
# .env.production
VALIDATION_ORCHESTRATOR_V2=false  # Safe default
LOG_LEVEL=WARNING
FEATURE_FLAG_REFRESH_INTERVAL=60
```

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Container resolution failures | High | Low | Extensive testing, fallback mechanisms |
| Feature flag toggle race conditions | Medium | Low | Atomic config operations |
| Environment misconfiguration | High | Medium | Configuration validation, safe defaults |
| Rollback procedure failures | High | Low | Automated rollback testing |

## Rollback Procedures

### Emergency Rollback (< 2 minutes)
1. Set `VALIDATION_ORCHESTRATOR_V2=false` in environment
2. Restart application pods (or trigger config reload)
3. Verify health checks return to green
4. Monitor error rates en performance metrics

### Planned Rollback (< 15 minutes)
1. Schedule maintenance window
2. Update feature flag in configuration management
3. Deploy configuration changes
4. Run post-deployment validation
5. Update monitoring dashboards

## Integration Points

- **Container System**: Core dependency injection framework
- **Configuration Management**: Environment-based config loading
- **Health Checks**: Application readiness/liveness probes
- **Monitoring**: Feature flag state en toggle metrics
- **Deployment Pipeline**: Automated configuration deployment

## Success Metrics

- [ ] Feature flag functionality: 100% reliable toggle capability
- [ ] Container resolution: Zero failed dependency injections
- [ ] Rollback speed: < 30 seconds voor emergency rollback
- [ ] Configuration accuracy: Zero production misconfigurations
- [ ] Health check reliability: 100% accurate orchestrator status

---

**Created**: 2025-08-29
**Story Owner**: DevOps Engineer
**Technical Reviewer**: Senior Developer
**Stakeholders**: DevOps Team, Development Team, SRE
