# Web Lookup Test Suite

**Status**: ✅ **47 Tests Passing**  
**Coverage**: 80-89% on new code  
**Framework**: pytest + pytest-asyncio  
**Last Run**: 2025-08-15

## 🧪 Test Overview

Comprehensive test suite for the modern web lookup implementation using Strangler Fig pattern.

### Test Statistics
- **Total Tests**: 47 passing + 3 integration (disabled by default)
- **Unit Tests**: 37 tests covering core functionality  
- **Integration Tests**: 10 tests with real API calls
- **Coverage**: 80% ModernWebLookupService, 89% WikipediaService
- **Execution Time**: ~1.4 seconds

## 🏃‍♀️ Quick Start

### Run All Tests
```bash
# Basic test run
python run_tests.py

# With coverage report  
RUN_COVERAGE=1 python run_tests.py

# Include integration tests (requires network)
RUN_INTEGRATION_TESTS=1 python run_tests.py
```

### Run Specific Test Files
```bash
# pytest directly
pytest tests/test_modern_web_lookup_service.py -v
pytest tests/test_wikipedia_service.py -v

# With async support
pytest tests/ --asyncio-mode=auto -v
```

## 📁 Test Structure

```
tests/
├── test_modern_web_lookup_service.py  # 27 tests - Core service
├── test_wikipedia_service.py          # 20 tests - Wikipedia API  
├── run_tests.py                       # Test runner script
└── README.md                          # This file
```

## 🔍 Test Categories

### ModernWebLookupService Tests (27 tests)

#### Core Functionality
- `test_service_implements_interface()` - Interface compliance
- `test_service_initialization()` - Proper setup
- `test_source_configuration()` - Source management
- `test_get_available_sources()` - Source listing

#### Lookup Operations  
- `test_lookup_empty_results()` - No results handling
- `test_lookup_with_exception_handling()` - Error scenarios
- `test_lookup_single_source()` - Single source operations
- `test_lookup_concurrent_requests()` - Async concurrency

#### Source Management
- `test_determine_sources_*()` - Smart source selection
- `test_validate_source_*()` - Source validation
- `test_get_source_status()` - Status monitoring

#### Legacy Integration
- `test_legacy_fallback_*()` - Fallback mechanisms
- `test_convert_legacy_result()` - Result conversion

#### Utility Functions
- `test_find_juridical_references()` - Legal reference detection
- `test_detect_duplicates()` - Duplicate detection
- `test_calculate_similarity()` - Text similarity

### WikipediaService Tests (20 tests)

#### Core Wikipedia API
- `test_successful_lookup()` - Happy path scenarios
- `test_lookup_no_search_results()` - Empty results
- `test_lookup_*_error()` - Various error conditions

#### API Integration
- `test_build_lookup_result_*()` - Result building logic
- `test_get_page_categories()` - Category extraction
- `test_suggest_search_terms()` - Search suggestions

#### Service Management
- `test_context_manager()` - Async context handling
- `test_lookup_without_*()` - Error conditions

### Integration Tests (3 tests, disabled by default)
- `test_real_wikipedia_lookup()` - Live API calls
- `test_real_wikipedia_suggestions()` - Live suggestion API

## 🎯 Test Features

### Async Testing
```python
@pytest.mark.asyncio
async def test_async_operation():
    service = ModernWebLookupService()
    result = await service.lookup_single_source("test", "wikipedia")
    assert result is not None
```

### Mock Testing  
```python
def test_with_mocks(self, service, mock_session):
    mock_session.get.return_value = MockResponse(200, mock_data)
    # Test with controlled responses
```

### Exception Testing
```python
async def test_error_handling():
    with patch.object(service, 'method', side_effect=Exception("Test error")):
        result = await service.lookup(request)
        assert result == []  # Graceful handling
```

### Concurrent Testing
```python
async def test_concurrent_operations():
    tasks = [service.lookup(request) for _ in range(3)]
    results = await asyncio.gather(*tasks)
    assert len(results) == 3
```

## 📊 Coverage Report

Recent coverage analysis:

```
Name                                    Stmts   Miss  Cover
--------------------------------------------------------
modern_web_lookup_service.py             162     33    80%
wikipedia_service.py                     123     14    89%  
test_modern_web_lookup_service.py        222      8    96%
test_wikipedia_service.py               193     12    94%
```

### Coverage Details
- **High coverage** on new modern implementation
- **Lower coverage** on legacy code (expected)
- **Excellent coverage** on test suites themselves

## 🔧 Test Configuration

### pytest.ini Configuration
```ini
[tool:pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_functions = test_*
python_classes = Test*
addopts = -v --tb=short
markers =
    asyncio: async test functions
    integration: tests requiring network access
```

### Environment Variables
- `RUN_INTEGRATION_TESTS=1` - Enable integration tests
- `RUN_COVERAGE=1` - Generate coverage report
- `PYTEST_CURRENT_TEST` - Current test identifier

## 🐛 Debugging Tests

### Common Issues

#### Import Errors
```python
# If modules not found, check PYTHONPATH
import sys
sys.path.insert(0, 'src')
```

#### Async Issues  
```python
# Missing pytest-asyncio
pip install pytest-asyncio

# Wrong async syntax
@pytest.mark.asyncio  # Required for async tests
async def test_async_function():
    ...
```

#### Mock Issues
```python  
# Incorrect patch target
with patch('services.modern_web_lookup_service.method'):  # ✅ Correct
with patch('services.method'):  # ❌ Wrong
```

### Debug Mode
```bash
# Verbose output
pytest tests/ -v -s

# Stop on first failure
pytest tests/ -x

# Debug with pdb
pytest tests/ --pdb
```

### Test-Specific Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Will show detailed service logs during tests
```

## 📈 Test Metrics

### Performance Benchmarks
- **Unit test suite**: ~1.4s execution time
- **Individual tests**: 1-50ms each
- **Integration tests**: 100-500ms each
- **Concurrent tests**: Validate async performance

### Quality Metrics
- **Zero test failures** in latest run
- **47 passing tests** out of 47 total
- **96% coverage** on test code itself
- **No flaky tests** (consistent results)

## 🛠️ Test Development

### Adding New Tests

1. **Create test function**:
```python
def test_new_feature(self, service):
    # Arrange
    request = LookupRequest(term="test")
    
    # Act  
    result = await service.new_method(request)
    
    # Assert
    assert result.success is True
```

2. **Add to appropriate test class**:
```python
class TestModernWebLookupService:
    def test_new_feature(self, service):
        ...
```

3. **Run and verify**:
```bash
pytest tests/test_modern_web_lookup_service.py::TestModernWebLookupService::test_new_feature -v
```

### Test Fixtures
```python
@pytest.fixture
def service():
    """Reusable service instance for tests."""
    return ModernWebLookupService()

@pytest.fixture  
def sample_request():
    """Standard test request."""
    return LookupRequest(term="test_term", sources=["wikipedia"])
```

### Mock Patterns
```python
# Mock external dependencies
@patch('services.web_lookup.wikipedia_service.aiohttp.ClientSession')
def test_with_mock_session(mock_session_class):
    ...

# Mock specific methods
with patch.object(service, 'method_name', return_value=expected_value):
    ...
```

## 🎯 Future Test Plans

### Next Sprint
- [ ] **SRU Service Tests** - When SRU implementation is complete
- [ ] **A/B Testing Framework Tests** - Compare old vs new implementations  
- [ ] **Performance Tests** - Load testing and benchmarks

### Medium Term
- [ ] **Migration Tests** - Test dependent module migration
- [ ] **Stress Tests** - High concurrency scenarios
- [ ] **Security Tests** - Input validation and injection prevention

### Long Term  
- [ ] **End-to-End Tests** - Full workflow testing
- [ ] **Property-Based Tests** - Hypothesis testing
- [ ] **Mutation Tests** - Test quality assessment

---

**🔗 Related Documentation:**
- [Modern Web Lookup Guide](../docs/MODERN_WEB_LOOKUP_GUIDE.md)
- [API Documentation](../docs/WEB_LOOKUP_API.md)

**🏃‍♀️ Quick Commands:**
```bash
# Standard test run
python run_tests.py

# Full testing with coverage and integration
RUN_INTEGRATION_TESTS=1 RUN_COVERAGE=1 python run_tests.py
```