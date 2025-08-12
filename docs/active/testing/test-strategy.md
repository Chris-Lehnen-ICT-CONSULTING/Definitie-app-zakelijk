# Test Strategie - DefinitieAgent Project

## Overzicht

Dit document beschrijft de test strategie voor het DefinitieAgent project, inclusief de patterns, best practices en technieken die we gebruiken om 100% test coverage te bereiken voor kritieke services.

## Doelstellingen

1. **Minimaal 80% test coverage** voor alle services
2. **100% test coverage** voor kritieke business logic
3. **Comprehensive testing** van alle error scenarios
4. **Maintainable tests** die makkelijk te begrijpen en updaten zijn

## Test Structuur

### Directory Layout
```
tests/
├── services/              # Service layer tests
│   ├── test_definition_generator.py
│   ├── test_definition_repository.py
│   ├── test_service_factory.py
│   └── ...
├── unit/                  # Pure unit tests
├── integration/           # Integration tests
├── conftest.py           # Shared fixtures
└── pytest.ini            # Pytest configuration
```

### Test Naming Conventions
- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName>`
- Test methods: `test_<what_is_being_tested>`
- Edge cases: `test_<method>_<edge_case>`

## Test Patterns & Technieken

### 1. Mocking External Dependencies

#### Pattern: Mock waar het gebruikt wordt
```python
# GOED: Mock in de module waar het geïmporteerd wordt
with patch('services.definition_generator.stuur_prompt_naar_gpt') as mock_gpt:
    mock_gpt.return_value = "Test response"

# FOUT: Mock in de originele module
with patch('prompt_builder.stuur_prompt_naar_gpt') as mock_gpt:  # Werkt niet!
```

#### Pattern: AsyncMock voor async methods
```python
@pytest.fixture
def mock_orchestrator():
    orchestrator = AsyncMock()
    # Sync methods op AsyncMock moeten expliciet Mock zijn
    orchestrator.get_stats = Mock(return_value={'stats': 'data'})
    return orchestrator
```

### 2. Database Testing

#### Pattern: Mock Repository Pattern
```python
@pytest.fixture
def mock_legacy_repo():
    """Mock voor legacy repository."""
    return Mock()

@pytest.fixture
def repository(mock_legacy_repo):
    """Repository met gemockte legacy dependency."""
    with patch('services.definition_repository.LegacyRepository', 
               return_value=mock_legacy_repo):
        return DefinitionRepository(db_path=':memory:')
```

#### Pattern: SQLite Row Mocking
```python
# Mock een database row
mock_row = Mock(spec=sqlite3.Row)
row_data = [1, 'Test', 'Test def', '2024-01-01T10:00:00']
mock_row.__getitem__ = Mock(side_effect=lambda x: row_data[x])
```

### 3. Streamlit UI Testing

#### Pattern: Context Manager Mocking
```python
def test_streamlit_sidebar():
    with patch('services.service_factory.st') as mock_st:
        mock_sidebar = Mock()
        mock_st.sidebar = mock_sidebar
        
        # Setup context manager behavior
        mock_sidebar.__enter__ = Mock(return_value=mock_st)
        mock_sidebar.__exit__ = Mock(return_value=None)
```

#### Pattern: Session State Mocking
```python
mock_st.session_state.get.return_value = False  # Feature flag OFF
mock_st.checkbox.return_value = True           # User input
```

### 4. Environment & Configuration Testing

#### Pattern: Environment Variable Mocking
```python
# Gebruik patch.dict voor environment variables
with patch.dict(os.environ, {'USE_NEW_SERVICES': 'true'}):
    result = get_definition_service()
```

#### Pattern: Multiple Environment Testing
```python
@pytest.mark.parametrize("env,expected_config", [
    ("development", "dev_config"),
    ("testing", "test_config"),
    ("production", "prod_config"),
])
def test_environment_configs(env, expected_config):
    with patch.dict(os.environ, {'APP_ENV': env}):
        # Test logic
```

### 5. Async Testing

#### Pattern: Async Test Fixtures
```python
@pytest.mark.asyncio
async def test_async_method():
    async with SomeAsyncContext() as ctx:
        result = await async_method()
        assert result == expected
```

#### Pattern: Mixed Async/Sync Testing
```python
# Gebruik run_in_executor pattern testing
loop = asyncio.get_event_loop()
result = await loop.run_in_executor(None, sync_function, *args)
```

### 6. Error & Edge Case Testing

#### Pattern: Exception Testing
```python
def test_error_handling():
    with pytest.raises(ValueError, match="Expected error message"):
        function_that_should_fail()
```

#### Pattern: None/Empty Value Testing
```python
def test_none_handling():
    # Test met None
    result = function(None)
    assert result == default_value
    
    # Test met lege collections
    result = function([])
    assert result == []
```

### 7. Coverage-Driven Testing

#### Pattern: Branch Coverage Testing
```python
def test_all_branches():
    # Test if branch
    with patch('module.condition', return_value=True):
        result = function()
        assert result == "if_result"
    
    # Test else branch
    with patch('module.condition', return_value=False):
        result = function()
        assert result == "else_result"
```

#### Pattern: Loop Coverage
```python
def test_loop_coverage():
    # Empty list - loop body not executed
    result = process_items([])
    assert result == []
    
    # Single item
    result = process_items([item])
    assert len(result) == 1
    
    # Multiple items
    result = process_items([item1, item2, item3])
    assert len(result) == 3
```

## Coverage Tools & Commands

### Installation
```bash
pip install pytest pytest-cov
```

### Configuration (.coveragerc)
```ini
[run]
source = src
branch = True
omit = 
    */tests/*
    */__init__.py
    */migrations/*

[report]
exclude_lines =
    pragma: no cover
    raise NotImplementedError
    if TYPE_CHECKING:
    except ImportError:

fail_under = 80
```

### Useful Commands
```bash
# Run tests with coverage report
pytest --cov=src --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=src --cov-report=html

# Test specific module with coverage
pytest tests/services/test_definition_generator.py \
    --cov=services.definition_generator \
    --cov-report=term-missing

# Run without failing on coverage threshold
pytest --cov=src --no-cov-on-fail
```

## Best Practices

### 1. Test Isolation
- Elke test moet onafhankelijk zijn
- Gebruik fixtures voor setup/teardown
- Mock externe dependencies

### 2. Clear Test Structure
```python
def test_example():
    # Arrange - setup test data
    test_data = create_test_data()
    
    # Act - execute the function
    result = function_under_test(test_data)
    
    # Assert - verify the result
    assert result == expected_result
```

### 3. Descriptive Test Names
```python
# GOED: Beschrijft wat er getest wordt
def test_save_new_definition_returns_id():
    pass

# SLECHT: Vaag of onduidelijk
def test_save():
    pass
```

### 4. Comprehensive Fixtures
```python
@pytest.fixture
def sample_definition():
    """Herbruikbare test data."""
    return Definition(
        begrip="Test",
        definitie="Test definitie",
        metadata={'test': True}
    )
```

### 5. Mock Verification
```python
# Verify mock was called correctly
mock.assert_called_once_with(expected_args)

# Verify specific call arguments
call_args = mock.call_args[0]
assert call_args[0] == expected_value

# Verify call count
assert mock.call_count == 2
```

## Integration Testing Strategy

### Service Integration Tests
```python
class TestServiceIntegration:
    """Test interactie tussen services."""
    
    def test_full_workflow(self):
        # Test complete flow van request tot response
        container = ServiceContainer()
        orchestrator = container.orchestrator()
        
        response = orchestrator.create_definition(request)
        assert response.success
```

### Database Integration Tests
- Gebruik in-memory SQLite voor snelle tests
- Test echte SQL queries en transactions
- Verify data integriteit

## Performance Considerations

1. **Gebruik mocks** voor externe API calls
2. **In-memory databases** voor repository tests
3. **Parallelle test execution** met pytest-xdist
4. **Skip slow tests** tijdens development met markers

```python
@pytest.mark.slow
def test_performance_intensive():
    pass

# Run zonder slow tests
pytest -m "not slow"
```

## Continuous Integration

### GitHub Actions Configuration
```yaml
- name: Run tests with coverage
  run: |
    pytest --cov=src --cov-report=xml --cov-report=term

- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
    fail_ci_if_error: true
```

## Metrics & Monitoring

### Coverage Doelen
- **Overall**: Minimaal 80%
- **Critical Services**: 100%
- **UI Components**: 70%
- **Utilities**: 90%

### Coverage Badges
```markdown
![Coverage](https://codecov.io/gh/user/repo/branch/main/graph/badge.svg)
```

## Troubleshooting

### Common Issues

1. **Import Errors in Tests**
   - Zorg dat `__init__.py` files aanwezig zijn
   - Gebruik absolute imports
   - Check PYTHONPATH

2. **Async Test Failures**
   - Gebruik `@pytest.mark.asyncio`
   - Let op AsyncMock vs Mock
   - Check event loop handling

3. **Mock Not Working**
   - Mock waar het geïmporteerd wordt
   - Check spelling en path
   - Verify mock setup

4. **Coverage Gaps**
   - Check branch coverage (`--branch`)
   - Test alle exception paths
   - Look for implicit else branches

## Conclusie

Deze test strategie heeft ons geholpen om van gemiddeld 20% naar 100% coverage te gaan voor kritieke services. Door consistent deze patterns toe te passen, kunnen we high-quality, maintainable tests schrijven die vertrouwen geven in onze codebase.

Remember: **Coverage is een tool, geen doel op zich**. Focus op het testen van kritieke business logic en edge cases, niet alleen op het bereiken van 100% coverage.