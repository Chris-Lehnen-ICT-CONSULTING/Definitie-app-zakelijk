# Case Study: Van 15% naar 100% Test Coverage

Een praktijkvoorbeeld van hoe we de test coverage hebben verbeterd voor drie kritieke services in het DefinitieAgent project.

## Executive Summary

In dit project hebben we de test coverage drastisch verbeterd voor drie services:
- **DefinitionGenerator**: 20% → 100% (+80%)
- **DefinitionRepository**: 15% → 100% (+85%)
- **ServiceFactory**: 20% → 100% (+80%)

Totaal: **82 nieuwe tests** geschreven met moderne test patterns en 100% coverage bereikt.

## De Uitdaging

Het DefinitieAgent project had verschillende services met lage test coverage:
- Legacy code zonder tests
- Complexe dependencies (AI APIs, databases, UI frameworks)
- Async/sync gemixte code
- Tight coupling met externe services

## Aanpak per Service

### 1. DefinitionRepository (15% → 100%)

**Uitdagingen:**
- Database interacties
- Legacy repository wrapper
- Complex data conversies
- SQLite specifieke code

**Oplossingen:**
```python
# Mock de legacy repository
@pytest.fixture
def repository(mock_legacy_repo):
    with patch('services.definition_repository.LegacyRepository',
               return_value=mock_legacy_repo):
        return DefinitionRepository(db_path=':memory:')

# Mock SQLite rows
mock_row = Mock(spec=sqlite3.Row)
row_data = [1, 'Test', 'Test def', '2024-01-01']
mock_row.__getitem__ = Mock(side_effect=lambda x: row_data[x])
```

**Resultaat:** 39 tests, alle CRUD operaties + edge cases gedekt

### 2. DefinitionGenerator (20% → 100%)

**Uitdagingen:**
- OpenAI API calls
- Async wrappers om sync code
- Optionele dependencies (monitoring, ontologie)
- Complex prompt building

**Oplossingen:**
```python
# Mock op de juiste import locatie
with patch('services.definition_generator.stuur_prompt_naar_gpt') as mock_gpt:
    mock_gpt.return_value = "AI response"

# Handle optionele dependencies
with patch('services.definition_generator.MONITORING_AVAILABLE', True):
    # Test monitoring pad
```

**Resultaat:** 20 tests, alle generatie scenarios + enhancements gedekt

### 3. ServiceFactory (20% → 100%)

**Uitdagingen:**
- Streamlit UI components
- Feature flags via environment/session
- Lazy imports
- Service orchestration

**Oplossingen:**
```python
# Mock Streamlit context manager
mock_sidebar.__enter__ = Mock(return_value=mock_st)
mock_sidebar.__exit__ = Mock(return_value=None)

# Test feature flags
with patch.dict(os.environ, {'USE_NEW_SERVICES': 'true'}):
    service = get_definition_service()
```

**Resultaat:** 23 tests, alle paths en UI interacties gedekt

## Key Learnings

### 1. Mock Waar Het Gebruikt Wordt
```python
# FOUT
with patch('external_module.function'):

# GOED
with patch('my_module.function'):  # waar my_module het importeert
```

### 2. Test Branch Coverage
Voor 100% coverage moet je ALLE branches testen:
```python
# Code met if/else
if config.enable_cleaning:
    result = clean(data)
else:
    result = data

# Tests nodig voor beide branches
def test_with_cleaning_enabled():
    config.enable_cleaning = True
    # test...

def test_with_cleaning_disabled():
    config.enable_cleaning = False
    # test...
```

### 3. Handle None/Empty Cases
Deze worden vaak vergeten maar zijn cruciaal:
```python
def test_empty_list_handling():
    results = repository.search([])
    assert results == []

def test_none_conversion():
    with patch.object(repo, '_convert', return_value=None):
        results = repo.get_all()
        assert results == []  # Filtered out None values
```

### 4. AsyncMock vs Mock
```python
# Voor async methods
orchestrator = AsyncMock()

# Maar sync methods op AsyncMock need explicit Mock
orchestrator.get_stats = Mock(return_value={'stats': 'data'})
```

## Coverage Evolutie

### Week 1: Baseline (gem. 20%)
- Identificatie van services met lage coverage
- Prioritering op basis van kritikaliteit
- Setup van test infrastructuur

### Week 2: Repository Service (15% → 100%)
- 39 tests geschreven
- Alle database operaties gemockt
- Edge cases geïdentificeerd en getest

### Week 3: Generator & Factory (20% → 100%)
- 43 tests geschreven (20 + 23)
- Complexe mocking patterns ontwikkeld
- UI component testing toegevoegd

### Week 4: Documentatie & Consolidatie
- Test strategie gedocumenteerd
- Patterns en best practices vastgelegd
- Quick start guide gemaakt

## Impact

### Kwantitatief
- **3 services** naar 100% coverage
- **82 tests** toegevoegd
- **~250% gemiddelde coverage verbetering**

### Kwalitatief
- Meer vertrouwen bij refactoring
- Bugs gevonden tijdens test schrijven
- Betere code documentatie via tests
- Team knowledge sharing verbeterd

## Tools & Setup

### Dependencies
```bash
pip install pytest pytest-cov pytest-asyncio
```

### Configuration (.coveragerc)
```ini
[run]
source = src
branch = True
fail_under = 80

[report]
exclude_lines =
    pragma: no cover
    if TYPE_CHECKING:
```

### Useful Commands
```bash
# Single service coverage
pytest tests/services/test_service.py \
    --cov=services.service \
    --cov-report=term-missing

# HTML report
pytest --cov=src --cov-report=html
```

## Recommendations

1. **Start met de laagste coverage** - grootste impact
2. **Test publieke interfaces eerst** - belangrijkste functionaliteit
3. **Mock agressief** - tests moeten snel zijn
4. **Branch coverage is key** - niet alleen line coverage
5. **Documenteer patterns** - voor team adoptie

## Conclusie

100% test coverage is haalbaar, zelfs voor complexe legacy services. De key is:
- Systematische aanpak
- Goede mocking strategies
- Focus op branch coverage
- Pragmatisch zijn over wat echt getest moet worden

De investering in test coverage betaalt zich terug in:
- Minder bugs in productie
- Snellere development cycles
- Meer vertrouwen in de codebase
- Betere onboarding voor nieuwe developers

---

*"Coverage is een tool, geen doel. Maar 100% coverage dwingt je om over alle edge cases na te denken."*
