# STORY-006: Test Suite Restoration

## User Story
Als een **developer**  
wil ik een werkende test suite met minimaal 60% coverage  
zodat ik met vertrouwen nieuwe features kan ontwikkelen zonder regressies.

## Acceptance Criteria
- [ ] Import errors in tests gefixed
- [ ] Basis unit tests werkend (60% coverage)
- [ ] Integration tests voor core flows
- [ ] Test data fixtures gecreëerd
- [ ] CI/CD pipeline voorbereid
- [ ] Test documentatie bijgewerkt

## Technical Notes

### Current Test Status
```
Total Tests: 50+
Passing: 7 (14%)
Failing: 43 (86%)
Coverage: Unknown (likely <20%)
```

### Common Test Failures

1. **Import Errors**
   ```python
   # BROKEN
   from services.definition_service import DefinitionService
   
   # FIXED
   from src.services.unified_definition_service import UnifiedDefinitionService
   ```

2. **Missing Fixtures**
   ```python
   # tests/fixtures/definitions.py
   @pytest.fixture
   def sample_definition():
       return {
           "term": "authenticatie",
           "definition": "Het proces waarbij...",
           "context": "juridisch",
           "score": 85
       }
   
   @pytest.fixture
   def mock_openai_response():
       return {
           "choices": [{
               "message": {
                   "content": "Test definitie"
               }
           }]
       }
   ```

3. **Async Test Issues**
   ```python
   # Proper async test
   @pytest.mark.asyncio
   async def test_async_generation():
       service = UnifiedDefinitionService.get_instance()
       result = await service.generate_definition_async("test")
       assert result is not None
   ```

### Test Structure to Implement

```
tests/
├── unit/
│   ├── test_unified_service.py      # Core service tests
│   ├── test_validators.py           # All 46 validators
│   ├── test_config.py              # Configuration tests
│   └── test_utils.py               # Utility tests
├── integration/
│   ├── test_definition_flow.py     # Full flow test
│   ├── test_ui_integration.py      # UI component tests
│   └── test_database.py            # DB operations
├── fixtures/
│   ├── __init__.py
│   ├── definitions.py              # Definition fixtures
│   ├── validation_results.py       # Validation fixtures
│   └── mock_responses.py           # API mocks
└── conftest.py                     # Pytest configuration
```

### Priority Test Cases

1. **Definition Generation Flow**
   ```python
   def test_complete_definition_flow():
       # Generate definition
       # Validate with rules
       # Save to database
       # Retrieve from history
   ```

2. **Validation Rules**
   ```python
   @pytest.mark.parametrize("validator,input,expected", [
       (SAM_01, "Auth is auth", False),  # Circular
       (STR_01, "lowercase", False),      # No capital
       (STR_02, "No period", False),      # No period
   ])
   def test_validators(validator, input, expected):
       result = validator.validate(input, "term", {})
       assert result.passed == expected
   ```

3. **UI Component Tests**
   ```python
   def test_tab_navigation():
       # Test all tabs load
       # Test state persistence
       # Test error handling
   ```

### Test Data Management
```python
# Create test database
TEST_DB = "sqlite:///test.db"

@pytest.fixture(scope="session")
def test_db():
    engine = create_engine(TEST_DB)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
```

### Coverage Goals
- Core services: 80%+
- Validators: 90%+
- UI components: 60%+
- Utilities: 70%+
- Overall: 60%+

## QA Notes

### Test Execution Plan
1. **Phase 1: Fix Infrastructure**
   - Fix all import errors
   - Create base fixtures
   - Setup test database

2. **Phase 2: Unit Tests**
   - Service layer tests
   - Validator tests
   - Utility tests

3. **Phase 3: Integration Tests**
   - End-to-end flows
   - UI integration
   - Database operations

4. **Phase 4: Coverage & CI**
   - Reach 60% coverage
   - Setup coverage reporting
   - Prepare CI/CD config

### Manual Test Protocol
Document key manual test scenarios:
1. Definition generation happy path
2. Error handling scenarios
3. Performance under load
4. UI responsiveness

### Expected Behavior
- All tests run without import errors
- Test suite completes in <2 minutes
- Coverage report generated
- Clear failure messages

## Definition of Done
- [ ] No import errors in any test
- [ ] 60%+ code coverage achieved
- [ ] All core flows have tests
- [ ] Test fixtures documented
- [ ] CI/CD configuration ready
- [ ] Test README updated
- [ ] Manual test protocol documented

## Priority
**High** - Testing is critical for stability

## Estimated Effort
**13 story points** - 5 days of development

## Sprint
Sprint 3-4 - Testing & Stabilization

## Dependencies
- pytest and plugins
- Mock libraries
- Coverage tools
- Test database setup

## Notes
- Start with fixing imports
- Focus on critical paths first
- Use mocks for external services
- Consider test performance
- Document testing patterns

---
*Story generated from PRD Epic 4: Testing & Stabilisatie*