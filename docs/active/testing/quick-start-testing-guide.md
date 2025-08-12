# Quick Start Testing Guide

Een praktische guide voor het schrijven van tests in het DefinitieAgent project.

## 🚀 Snel Starten

### 1. Test File Aanmaken

Voor een nieuwe service `my_service.py`, maak `tests/services/test_my_service.py`:

```python
"""
Unit tests voor MyService.

Test alle functionaliteit inclusief:
- Happy path scenarios
- Error handling
- Edge cases
"""
import pytest
from unittest.mock import Mock, patch

from services.my_service import MyService


class TestMyService:
    """Test suite voor MyService."""
    
    def test_basic_functionality(self):
        """Test basis functionaliteit."""
        # Arrange
        service = MyService()
        
        # Act
        result = service.do_something("input")
        
        # Assert
        assert result == "expected output"
```

### 2. Run Je Eerste Test

```bash
# Run de test
pytest tests/services/test_my_service.py -v

# Met coverage
pytest tests/services/test_my_service.py --cov=services.my_service --cov-report=term-missing
```

## 📋 Test Checklist

Voor elke nieuwe functie/method, test:

- [ ] **Happy path** - normale input, verwachte output
- [ ] **Edge cases** - lege strings, None, lege lists
- [ ] **Error cases** - ongeldige input, exceptions
- [ ] **Boundary values** - min/max waarden
- [ ] **State changes** - side effects, database updates

## 🔧 Common Test Patterns

### Pattern 1: Basic Test
```python
def test_calculate_sum():
    """Test sum calculation."""
    result = calculate_sum(2, 3)
    assert result == 5
```

### Pattern 2: Testing Exceptions
```python
def test_invalid_input_raises_error():
    """Test dat ongeldige input een error geeft."""
    with pytest.raises(ValueError, match="Invalid input"):
        process_data(None)
```

### Pattern 3: Mocking External Services
```python
def test_api_call(self):
    """Test functie die externe API aanroept."""
    with patch('services.my_service.requests.get') as mock_get:
        # Setup mock response
        mock_get.return_value.json.return_value = {'status': 'ok'}
        
        # Execute
        result = my_service.check_api_status()
        
        # Verify
        assert result == 'ok'
        mock_get.assert_called_once_with('https://api.example.com/status')
```

### Pattern 4: Testing Async Functions
```python
@pytest.mark.asyncio
async def test_async_operation():
    """Test async functie."""
    service = MyAsyncService()
    result = await service.fetch_data()
    assert result is not None
```

### Pattern 5: Parametrized Tests
```python
@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
    ("", ""),
    (None, None),
])
def test_uppercase_conversion(input, expected):
    """Test uppercase met verschillende inputs."""
    assert to_uppercase(input) == expected
```

## 🎯 Service-Specifieke Voorbeelden

### Repository Service Test
```python
class TestDefinitionRepository:
    @pytest.fixture
    def repository(self):
        """Create repository met mock database."""
        with patch('services.repository.Database') as mock_db:
            return DefinitionRepository(mock_db)
    
    def test_save_definition(self, repository):
        """Test opslaan van definitie."""
        # Arrange
        definition = Definition(begrip="Test", definitie="Test def")
        repository.db.insert.return_value = 123
        
        # Act
        result_id = repository.save(definition)
        
        # Assert
        assert result_id == 123
        repository.db.insert.assert_called_once()
```

### Generator Service Test
```python
def test_generate_with_mock_ai():
    """Test generatie met gemockte AI."""
    with patch('services.generator.ai_client') as mock_ai:
        # Setup
        mock_ai.generate.return_value = "Generated text"
        generator = DefinitionGenerator()
        
        # Execute
        result = generator.generate("Test begrip")
        
        # Verify
        assert "Generated text" in result.definitie
```

### Feature Flag Test
```python
def test_feature_flag_enabled():
    """Test met feature flag aan."""
    with patch.dict(os.environ, {'FEATURE_X': 'true'}):
        service = get_service()
        assert isinstance(service, NewService)
```

### Complex Service Factory Test
```python
class TestServiceFactory:
    """Voorbeeld van complexe mocking uit ServiceFactory tests."""
    
    def test_streamlit_context_manager_mocking(self):
        """Test Streamlit sidebar context manager."""
        with patch('services.service_factory.st') as mock_st:
            # Setup sidebar mock
            mock_sidebar = Mock()
            mock_st.sidebar = mock_sidebar
            
            # BELANGRIJK: Mock de context manager methods!
            mock_sidebar.__enter__ = Mock(return_value=mock_st)
            mock_sidebar.__exit__ = Mock(return_value=None)
            
            # Nu werkt: with st.sidebar:
            render_feature_flag_toggle()
            
            # Verify
            mock_sidebar.__enter__.assert_called_once()
            mock_sidebar.__exit__.assert_called_once()
    
    def test_async_mock_with_sync_method(self):
        """Test AsyncMock met sync methods."""
        # Maak AsyncMock voor async class
        orchestrator = AsyncMock()
        
        # MAAR: sync methods moeten expliciet Mock zijn!
        orchestrator.get_stats = Mock(return_value={'stats': 'data'})
        
        # Nu werkt get_stats() correct
        stats = orchestrator.get_stats()
        assert stats == {'stats': 'data'}
```

## 🐛 Debugging Tips

### 1. Print Debug Info
```python
def test_complex_logic():
    result = complex_function(input_data)
    print(f"Debug: result = {result}")  # Wordt getoond met pytest -s
    assert result == expected
```

### 2. Check Mock Calls
```python
# Zie alle calls naar een mock
print(mock_function.call_args_list)

# Verify specifieke call
mock_function.assert_called_with(arg1, arg2)

# Check aantal calls
assert mock_function.call_count == 2
```

### 3. Use Debugger
```python
def test_debugging():
    import pdb; pdb.set_trace()  # Breakpoint
    result = function_to_debug()
```

## 📊 Coverage Tips

### Check Coverage Gaps
```bash
# Zie welke regels niet gecovered zijn
pytest --cov=services.my_service --cov-report=term-missing

# Genereer HTML report
pytest --cov=services.my_service --cov-report=html
# Open htmlcov/index.html in browser
```

### Target Specific Lines
Als coverage laat zien dat regel 42-45 niet gecovered zijn:
1. Kijk wat die code doet
2. Schrijf een test die dat pad triggert
3. Run coverage weer

## ⚡ Snelle Fixes

### Import Error?
```python
# In je test file
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
```

### Mock Not Working?
```python
# Mock waar het GEBRUIKT wordt, niet waar het GEDEFINIEERD is
with patch('services.my_service.external_function'):  # GOED
with patch('external_module.external_function'):      # FOUT (meestal)
```

### Async Test Failing?
```python
# Vergeet niet de decorator!
@pytest.mark.asyncio  # <-- Deze!
async def test_async_stuff():
    result = await async_function()
```

## 📚 Verdere Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Python Mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- Onze [Test Strategy Document](./test-strategy.md)

## 💡 Golden Rules

1. **Test gedrag, niet implementatie**
2. **Een test test één ding**
3. **Tests moeten snel zijn**
4. **Tests moeten deterministisch zijn**
5. **Mocks zijn je vrienden**

---

Happy Testing! 🎉

Als je vastloopt, check de bestaande tests in `tests/services/` voor voorbeelden.