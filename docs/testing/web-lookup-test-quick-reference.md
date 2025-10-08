# Web Lookup Tests - Quick Reference Guide

**Quick commands en voorbeelden voor developers**

## Quick Start

```bash
# Run alle web lookup tests (129 tests)
pytest tests/services/web_lookup/ tests/integration/test_improved_web_lookup.py -v

# Run specifieke test suite
pytest tests/services/web_lookup/test_synonym_service.py -v
pytest tests/services/web_lookup/test_juridisch_ranker.py -v
pytest tests/integration/test_improved_web_lookup.py -v

# Run met coverage
pytest tests/services/web_lookup/ --cov=src/services/web_lookup --cov-report=html

# Run specifieke test
pytest tests/services/web_lookup/test_synonym_service.py::TestGetSynoniemen::test_get_synoniemen_for_hoofdterm -v

# Run tests matching pattern
pytest -k "synonym" -v
pytest -k "ranking" -v
pytest -k "integration" -v
```

## Test Structure Overview

```
tests/
├── services/web_lookup/
│   ├── test_synonym_service.py         # 52 tests - JuridischeSynoniemlService
│   └── test_juridisch_ranker.py        # 64 tests - Ranking functions
├── integration/
│   └── test_improved_web_lookup.py     # 13 tests - End-to-end pipeline
└── fixtures/
    └── web_lookup_fixtures.py          # 25+ reusable fixtures
```

## Using Fixtures

### Mock LookupResult
```python
def test_something(mock_lookup_result):
    result = mock_lookup_result(
        term="voorlopige hechtenis",
        definition="Artikel 12 Sv bepaalt...",
        url="https://www.rechtspraak.nl/123",
        confidence=0.7,
        is_juridical=True
    )
    assert result.term == "voorlopige hechtenis"
```

### Pre-configured Results
```python
def test_with_juridische_result(juridische_lookup_result):
    # Pre-configured juridisch result
    assert juridische_lookup_result.source.is_juridical is True

def test_with_wikipedia_result(wikipedia_lookup_result):
    # Pre-configured Wikipedia result
    assert "wikipedia.org" in wikipedia_lookup_result.source.url
```

### Synonym Service
```python
def test_with_basic_synoniemen(synonym_service_basic):
    # Service met voorlopige_hechtenis, onherroepelijk, verdachte
    synoniemen = synonym_service_basic.get_synoniemen("voorlopige hechtenis")
    assert "voorarrest" in synoniemen
```

### Custom YAML
```python
def test_custom_synoniemen(temp_synonym_yaml):
    yaml_path = temp_synonym_yaml("""
test_term:
  - syn1
  - syn2
    """)
    service = JuridischeSynoniemlService(config_path=str(yaml_path))
    assert service.has_synoniemen("test_term")
```

## Common Test Patterns

### Testing Synonym Lookup
```python
def test_bidirectional_lookup(synonym_service_basic):
    # Forward: hoofdterm → synoniemen
    synoniemen = synonym_service_basic.get_synoniemen("verdachte")
    assert "beklaagde" in synoniemen

    # Reverse: synoniem → hoofdterm + andere synoniemen
    reverse = synonym_service_basic.get_synoniemen("beklaagde")
    assert "verdachte" in reverse
    assert "beschuldigde" in reverse
```

### Testing Juridische Ranking
```python
def test_ranking_boost(mock_lookup_result):
    result = mock_lookup_result(
        definition="Artikel 12 Sr regelt voorlopige hechtenis",
        url="https://www.rechtspraak.nl/123",
        confidence=0.5
    )

    boost = calculate_juridische_boost(result)

    # Verwacht: 1.2 (bron) × 1.15 (artikel) × keywords
    assert boost > 1.2
```

### Testing Integration Pipeline
```python
@pytest.mark.asyncio
async def test_full_pipeline(synonym_service_basic, mock_lookup_result):
    # 1. Expand query
    expanded = synonym_service_basic.expand_query_terms("verdachte", max_synonyms=2)

    # 2. Simulate lookup
    results = [mock_lookup_result(term=expanded[0], definition="...")]

    # 3. Apply ranking
    boosted = boost_juridische_resultaten(results)

    assert len(boosted) > 0
```

## Test Data Examples

### Sample Juridische Definitie
```python
def test_with_juridische_content(sample_juridische_definitie):
    # "Artikel 12 lid 2 Sv bepaalt dat de rechter..."
    assert count_juridische_keywords(sample_juridische_definitie) >= 5
    assert contains_artikel_referentie(sample_juridische_definitie)
```

### Sample Synoniemen YAML
```yaml
voorlopige_hechtenis:
  - voorarrest
  - bewaring
  - inverzekeringstelling

onherroepelijk:
  - kracht van gewijsde
  - rechtskracht
  - definitieve uitspraak
```

## Debugging Tips

### Print Test Details
```python
def test_debug_boost(mock_lookup_result, caplog):
    import logging
    caplog.set_level(logging.DEBUG)

    result = mock_lookup_result(definition="Artikel 12 rechter vonnis")
    boost = calculate_juridische_boost(result)

    # Check logs
    for record in caplog.records:
        print(f"{record.levelname}: {record.message}")
```

### Inspect Fixture Data
```python
def test_inspect_service(synonym_service_basic):
    stats = synonym_service_basic.get_stats()
    print(f"Hoofdtermen: {stats['hoofdtermen']}")
    print(f"Synoniemen: {stats['totaal_synoniemen']}")

    all_terms = synonym_service_basic.get_all_terms()
    print(f"Alle termen: {sorted(all_terms)}")
```

### Test Isolation
```python
def test_isolated(tmp_path):
    # Use tmp_path for isolated test data
    yaml_file = tmp_path / "test.yaml"
    yaml_file.write_text("test:\n  - syn1\n")

    service = JuridischeSynoniemlService(config_path=str(yaml_file))
    # Test runs in isolation
```

## Performance Testing

### Time Measurement
```python
import time

def test_performance(synonym_service_basic):
    start = time.time()

    for i in range(1000):
        synoniemen = synonym_service_basic.get_synoniemen("voorlopige hechtenis")

    elapsed = time.time() - start
    print(f"1000 lookups: {elapsed:.3f}s")
    assert elapsed < 1.0  # Should be fast
```

### Async Performance
```python
@pytest.mark.asyncio
async def test_async_performance(mock_slow_lookup_service):
    import asyncio

    tasks = [mock_slow_lookup_service("term") for _ in range(10)]
    start = time.time()
    results = await asyncio.gather(*tasks)
    elapsed = time.time() - start

    print(f"10 concurrent lookups: {elapsed:.3f}s")
```

## CI/CD Integration

### Pytest INI Configuration
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
```

### GitHub Actions Example
```yaml
- name: Run Web Lookup Tests
  run: |
    pytest tests/services/web_lookup/ tests/integration/test_improved_web_lookup.py \
      --cov=src/services/web_lookup \
      --cov-report=xml \
      --junit-xml=test-results.xml \
      -v
```

## Troubleshooting

### Import Errors
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=/path/to/project:$PYTHONPATH

# Or use -m pytest
python -m pytest tests/services/web_lookup/
```

### Fixture Not Found
```python
# Import fixtures explicitly
from tests.fixtures.web_lookup_fixtures import mock_lookup_result

# Or use pytest.fixture in conftest.py
```

### YAML Loading Issues
```python
def test_yaml_loading(tmp_path):
    # Ensure encoding is UTF-8
    yaml_file = tmp_path / "test.yaml"
    yaml_file.write_text("test:\n  - syn\n", encoding="utf-8")

    service = JuridischeSynoniemlService(config_path=str(yaml_file))
```

### Async Test Issues
```python
# Ensure @pytest.mark.asyncio is used
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

## Quick Reference: Key Functions

### Synonym Service
```python
# Get synoniemen (bidirectional)
synoniemen = service.get_synoniemen("term")

# Expand query
expanded = service.expand_query_terms("term", max_synonyms=3)

# Check if has synoniemen
has = service.has_synoniemen("term")

# Find matches in text
matches = service.find_matching_synoniemen("text...")

# Get stats
stats = service.get_stats()
```

### Juridische Ranker
```python
# Check if juridische bron
is_jur = is_juridische_bron("https://rechtspraak.nl/...")

# Count keywords
count = count_juridische_keywords("rechter vonnis wetboek")

# Check artikel reference
has_art = contains_artikel_referentie("Artikel 12 bepaalt")

# Calculate boost
boost = calculate_juridische_boost(result, context=["Sv"])

# Boost results
boosted = boost_juridische_resultaten(results, context=["strafrecht"])

# Get juridische score
score = get_juridische_score(result)
```

## Test Coverage Goals

| Module | Target | Current |
|--------|--------|---------|
| synonym_service.py | >80% | ~95% ✅ |
| juridisch_ranker.py | >80% | ~95% ✅ |
| Integration pipeline | >70% | ~85% ✅ |

## Common Assertions

```python
# Synonym service
assert "voorarrest" in service.get_synoniemen("voorlopige hechtenis")
assert service.has_synoniemen("verdachte") is True
assert len(service.expand_query_terms("term")) >= 1

# Juridische ranking
assert is_juridische_bron("https://rechtspraak.nl/123") is True
assert count_juridische_keywords("rechter vonnis") >= 2
assert contains_artikel_referentie("Art. 12") is True
assert boost_factor > 1.0

# Integration
assert len(boosted_results) > 0
assert boosted_results[0].source.confidence >= original_confidence
```

## Resources

- **Test Files:**
  - `tests/services/web_lookup/test_synonym_service.py`
  - `tests/services/web_lookup/test_juridisch_ranker.py`
  - `tests/integration/test_improved_web_lookup.py`

- **Fixtures:**
  - `tests/fixtures/web_lookup_fixtures.py`

- **Documentation:**
  - `docs/testing/web-lookup-improvements-test-summary.md`
  - `docs/testing/web-lookup-test-quick-reference.md` (this file)

- **Source Code:**
  - `src/services/web_lookup/synonym_service.py`
  - `src/services/web_lookup/juridisch_ranker.py`

## Need Help?

1. **Check test summary:** `docs/testing/web-lookup-improvements-test-summary.md`
2. **Run specific test:** `pytest tests/path/to/test.py::TestClass::test_method -v`
3. **Debug with prints:** Use `-s` flag: `pytest -s test_file.py`
4. **Check fixtures:** `pytest --fixtures tests/fixtures/`

---

**Quick Start Command:**
```bash
# Run all tests, see results
pytest tests/services/web_lookup/ tests/integration/test_improved_web_lookup.py -v
```

**Expected Output:**
```
129 passed in 0.15s ✅
```
