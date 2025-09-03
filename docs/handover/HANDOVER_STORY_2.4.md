# 📋 Handover Document - Story 2.4 ValidationOrchestratorV2 Integration

## 🎯 Current Status

### ✅ Completed Today (2025-09-02)

#### Documentation Cleanup (PRs #15, #16)
- **PR #15**: Canonicalization + content corrections (MERGED)
- **PR #16**: Doc-lint hooks + architecture consolidation (MERGED)
- Pre-commit hooks now active for doc quality

#### Story 2.4 Initial Patch (PR #17)
- **PR #17**: DEV_MODE guard for V2 validation (OPEN)
- Branch: `feat/story-2.4-validation-v2-integration`
- Safe, non-breaking change behind environment flag
- Smoke tests included

## 🚀 Next Steps - Story 2.4 Completion

### Phase 1: Core Integration (Priority: HIGH)
**Estimated: 2-3 dagen**

#### 1.1 DefinitionOrchestratorV2 Integration
```python
# File: src/services/definition/definition_orchestrator_v2.py
# TODO: Replace direct validation calls with ValidationOrchestratorInterface
# - Remove validation logic from orchestrator
# - Inject ValidationOrchestratorV2 via constructor
# - Update all validation method calls
```

#### 1.2 Service Container Wiring
```python
# File: src/services/container.py
# TODO: Wire ValidationOrchestratorV2 into container
# - Register ValidationOrchestratorV2 as singleton
# - Update orchestrator factory to inject validation service
# - Ensure proper async context management
```

#### 1.3 Migration van UI Validation Calls
**Files to update:**
- `src/ui/components/definition_tab.py` - validatie tijdens generatie
- `src/ui/components/export_tab.py` - pre-export validatie
- `src/ui/components/review_tab.py` - review validatie flows
- `src/api/endpoints/validation.py` - API endpoint routing

### Phase 2: Legacy Cleanup (Priority: MEDIUM)
**Estimated: 1 dag**

#### 2.1 Remove V1 Adapter Code
```bash
# Files to remove/clean:
- src/services/validation/v1_adapter.py (remove)
- src/services/validation/definition_validator.py (deprecate)
- Legacy imports in service container
```

#### 2.2 Update Tests
```bash
# Test files requiring updates:
- tests/services/validation/test_orchestrator_v2.py
- tests/integration/test_validation_flow.py
- Remove dual-path test coverage
```

### Phase 3: Validation & Rollout (Priority: HIGH)
**Estimated: 1 dag**

#### 3.1 Comprehensive Testing
```bash
# Run full test suite
pytest tests/services/validation/ -v

# Performance benchmarks
python scripts/benchmark_validation.py

# Smoke tests (already created)
./run_smoke_tests.sh
```

#### 3.2 Gradual Rollout Strategy
1. **Development**: DEV_MODE=true testing
2. **Staging**: Remove DEV_MODE guard, test fully on V2
3. **Production**: Deploy with monitoring

## 📊 Technical Decisions to Make

### 1. Async Pattern Choice
```python
# Option A: Full async chain
async def validate_definition(self, request):
    result = await self.validation_orchestrator.validate(request)

# Option B: Sync wrapper for compatibility
def validate_definition_sync(self, request):
    return asyncio.run(self.validate_async(request))
```
**Recommendation**: Option A - full async chain

### 2. Error Handling Strategy
```python
# Centralized error mapping needed for:
- ValidationError → UI-friendly messages
- Timeout handling (async operations)
- Partial validation failures
```

### 3. Configuration Management
```yaml
# config/validation_v2.yaml structure:
validation:
  mode: "v2"  # or "legacy"
  timeout: 30
  parallel: true
  max_workers: 4
```

## 🔧 Quick Commands

### Test V2 Validation Locally
```bash
# Enable V2 mode
export DEV_MODE=true

# Run app
streamlit run src/main.py

# Test via API
curl -X POST localhost:8501/api/validate \
  -H "Content-Type: application/json" \
  -d '{"text": "Een test is een methode", "category": "proces"}'
```

### Run Integration Tests
```bash
# Specific V2 tests
pytest tests/services/validation/test_orchestrator_v2.py -v

# Full validation suite
pytest tests/ -k validation -v
```

## ⚠️ Risk Areas & Mitigations

### Risk 1: Performance Regression
- **Mitigation**: Benchmark before/after, keep DEV_MODE guard until verified
- **Monitoring**: Add timing logs for validation calls

### Risk 2: Async Context Issues
- **Mitigation**: Proper event loop management in UI components
- **Testing**: Concurrent request testing

### Risk 3: Missing Validation Rules
- **Mitigation**: Compare V1 vs V2 rule coverage
- **Validation**: Golden test suite with known inputs/outputs

## 📝 Definition of Done

### Story 2.4 Complete When:
- [ ] All validation calls use ValidationOrchestratorV2
- [ ] Zero references to V1 adapter in production code
- [ ] All tests pass (unit, integration, smoke)
- [ ] Performance metrics equal or better than V1
- [ ] Documentation updated (architecture diagrams, API docs)
- [ ] DEV_MODE guard removed after successful testing

## 💡 Tips for Next Developer

1. **Start Small**: Test one UI component at a time
2. **Use Debugging**: Set `VALIDATION_DEBUG=true` for verbose logs
3. **Check Async**: Watch for event loop issues in Streamlit
4. **Monitor Memory**: V2 may have different memory profile
5. **Keep PR Small**: Break Phase 1 into multiple PRs if needed

## 📞 Contact & Resources

### Key Files
- Story definition: `docs/stories/epic-2-story-2.4-integration-migration.md`
- V2 Implementation: `src/services/validation/validation_orchestrator_v2.py`
- Container: `src/services/container.py`
- Smoke tests: `tests/smoke/test_validation_v2_smoke.py`

### Related PRs
- PR #17: Initial DEV_MODE patch
- PR #14: Story 2.1 ValidationInterface implementation
- PR #13: ValidationOrchestratorV2 documentation

### Commands Created
- `./run_smoke_tests.sh` - Quick V2 validation test
- `export DEV_MODE=true` - Enable V2 validation

---

*Generated: 2025-09-02*
*Story Owner: Senior Developer*
*Status: In Progress - Initial patch complete*
