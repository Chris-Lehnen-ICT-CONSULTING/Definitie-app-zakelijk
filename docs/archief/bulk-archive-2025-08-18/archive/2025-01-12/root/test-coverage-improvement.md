# Test Coverage Verbetering - DefinitionGenerator

## Overzicht

We hebben de test coverage voor de `DefinitionGenerator` service succesvol verbeterd van **~20%** naar **100%**.

## Wat is er gedaan:

### 1. Unit Tests Toegevoegd

Nieuw bestand: `tests/services/test_definition_generator.py` met 20 comprehensive tests:

#### Basis Functionaliteit Tests:
- ✅ `test_generate_success` - Succesvolle definitie generatie met alle features
- ✅ `test_generate_without_ontology` - Generatie zonder ontologische analyse
- ✅ `test_generate_without_cleaning` - Generatie zonder tekst opschoning
- ✅ `test_generate_empty_begrip` - Validatie van verplichte velden
- ✅ `test_generate_api_error` - Error handling bij API fouten

#### Enhancement Tests:
- ✅ `test_enhance_success` - Succesvolle definitie verrijking
- ✅ `test_enhance_partial_response` - Gedeeltelijke enhancement response
- ✅ `test_enhance_error_returns_original` - Graceful degradation bij errors

#### Helper Method Tests:
- ✅ `test_simple_category_detection` - Categorie detectie patronen
- ✅ `test_build_context_dict` - Context dictionary opbouw
- ✅ `test_parse_enhancement_response` - Response parsing
- ✅ `test_stats_tracking` - Statistieken tracking
- ✅ `test_config_defaults` - Default configuratie

#### Edge Cases & 100% Coverage:
- ✅ `test_monitoring_success_path` - Monitoring voor succesvolle calls
- ✅ `test_monitoring_failure_path` - Monitoring voor gefaalde calls
- ✅ `test_opschoning_else_branch` - Opschoning marker logic
- ✅ `test_category_detection_proces_pattern` - Specifieke proces patronen
- ✅ `test_ontology_analyzer_import_error` - Import error handling
- ✅ `test_context_parsing_edge_cases` - Edge cases in context parsing
- ✅ `test_enhancement_malformed_response` - Malformed response handling

### 2. Test Infrastructuur

#### Requirements Update:
```python
pytest==8.3.4
pytest-cov==6.0.0
```

#### Coverage Configuratie (.coveragerc):
```ini
[run]
source = src
branch = True
omit =
    */tests/*
    */__init__.py
    */migrations/*
    # Legacy files
    */unified_definition_service.py

[report]
exclude_lines =
    pragma: no cover
    raise NotImplementedError
    if TYPE_CHECKING:
    # etc...

fail_under = 80
```

## Coverage Resultaten

### Voor:
- **DefinitionGenerator**: ~20% (alleen indirect via integration tests)
- Geen dedicated unit tests
- Kritieke paden ongetest

### Na:
- **DefinitionGenerator**: **100%** coverage
- 135 statements, 46 branches - allemaal gedekt
- Alle error scenarios getest
- Alle configuratie opties getest

## Test Commando's

```bash
# Run tests met coverage report
pytest tests/services/test_definition_generator.py --cov=services.definition_generator --cov-report=term-missing

# Genereer HTML report
pytest tests/services/test_definition_generator.py --cov=services.definition_generator --cov-report=html

# Open HTML report
open htmlcov/index.html
```

## Belangrijke Test Patterns

### 1. Mocking External Dependencies
```python
with patch('services.definition_generator.stuur_prompt_naar_gpt') as mock_gpt, \
     patch('services.definition_generator.opschonen') as mock_clean:
    # Test logic
```

### 2. Async Testing
```python
@pytest.mark.asyncio
async def test_generate_success(self, generator, sample_request):
    # Async test implementation
```

### 3. Configuration Testing
```python
generator_config.enable_monitoring = True
generator = DefinitionGenerator(generator_config)
```

## Lessons Learned

1. **Import Mocking**: Mock op de juiste import locatie (waar het gebruikt wordt)
2. **Error Message Matching**: Decorators kunnen error messages aanpassen
3. **Async Mocks**: Gebruik `AsyncMock` voor async dependencies
4. **Coverage Gaps**: Focus op if/else branches voor 100% coverage

## Volgende Stappen

1. **CI/CD Integration**: Voeg coverage checks toe aan CI pipeline
2. **Coverage Badge**: Voeg coverage badge toe aan README
3. **Andere Services**: Pas zelfde aanpak toe op andere services met lage coverage
4. **Integration Tests**: Update integration tests om nieuwe unit tests te complementeren
