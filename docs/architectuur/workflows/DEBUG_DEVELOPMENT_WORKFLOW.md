# 🔄 Debug & Development Workflow

**Versie**: 1.0
**Datum**: 2025-08-25
**Status**: Actief
**Doel**: Gestructureerde aanpak voor debugging, development, testing en code review

---

## 📋 Workflow Overzicht

Deze workflow bestaat uit 4 opeenvolgende fases:

1. **🔍 Debug Fase** - Probleem identificatie en analyse
2. **💻 Development Fase** - Code schrijven/herschrijven
3. **🧪 Test Fase** - Functionaliteit verificatie
4. **✅ Review Fase** - Code kwaliteit controle

---

## Fase 1: 🔍 Debug Fase

### Doel
Systematisch identificeren en analyseren van problemen in de codebase.

### Stappen

#### 1.1 Probleem Definitie
```bash
□ Wat is het exacte probleem?
□ Wanneer treedt het op?
□ Is het reproduceerbaar?
□ Wat is de verwachte vs actuele output?
□ Zijn er error messages?
```

#### 1.2 Context Verzameling
```python
# Debug informatie verzamelen
import logging
import traceback

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_context():
    """Verzamel debug context informatie."""
    context = {
        "timestamp": datetime.now(),
        "python_version": sys.version,
        "environment": os.environ.get("ENV", "development"),
        "stack_trace": traceback.format_stack()
    }
    logger.debug(f"Debug context: {context}")
    return context
```

#### 1.3 Root Cause Analysis
```bash
□ Controleer logs voor patterns
□ Identificeer wanneer het probleem begon
□ Check recente code wijzigingen
□ Verifieer dependencies
□ Test edge cases
```

#### 1.4 Debug Tools
```python
# Interactive debugging
import pdb
pdb.set_trace()  # Breakpoint

# Performance profiling
import cProfile
cProfile.run('problematic_function()')

# Memory debugging
from memory_profiler import profile
@profile
def memory_intensive_function():
    pass
```

### Output
- **Debug Report** met:
  - Probleem beschrijving
  - Root cause
  - Reproductie stappen
  - Voorgestelde oplossing

---

## Fase 2: 💻 Development Fase

### Doel
Code schrijven of herschrijven op basis van debug bevindingen.

### Stappen

#### 2.1 Planning
```markdown
## Development Plan
- [ ] Backup huidige code
- [ ] Definieer nieuwe/aangepaste functionaliteit
- [ ] Identificeer affected modules
- [ ] Plan incrementele implementatie
- [ ] Definieer succes criteria
```

#### 2.2 Code Implementatie
```python
# Voorbeeld structuur voor nieuwe/aangepaste code
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class ImprovedImplementation:
    """
    Verbeterde implementatie van [functionaliteit].

    Deze versie lost [probleem] op door [aanpak].
    """

    def __init__(self, config: Optional[dict] = None):
        """Initialiseer met optionele configuratie."""
        self.config = config or self._default_config()
        self._validate_config()
        logger.info(f"Geïnitialiseerd met config: {self.config}")

    def process(self, data: Any) -> Result:
        """
        Verwerk data met verbeterde error handling.

        Args:
            data: Input data om te verwerken

        Returns:
            Result object met verwerkte data

        Raises:
            ValidationError: Als input invalid is
            ProcessingError: Als verwerking faalt
        """
        try:
            # Valideer input
            self._validate_input(data)

            # Verwerk met nieuwe logica
            result = self._improved_processing(data)

            # Log succes
            logger.info(f"Succesvol verwerkt: {len(data)} items")

            return result

        except ValidationError as e:
            logger.error(f"Validatie fout: {e}")
            raise
        except Exception as e:
            logger.error(f"Onverwachte fout: {e}", exc_info=True)
            raise ProcessingError(f"Verwerking mislukt: {e}")
```

#### 2.3 Refactoring Checklist
```bash
□ Verwijder duplicate code
□ Split lange functies (>20 regels)
□ Voeg type hints toe
□ Implementeer error handling
□ Voeg logging toe
□ Nederlandse docstrings en comments
```

#### 2.4 Code Quality Standards
```python
# Naming conventions
class DefinitieValidator:  # PascalCase voor classes
    def valideer_definitie(self):  # snake_case voor functies
        max_lengte = 500  # snake_case voor variabelen

# Constants
MAX_RETRIES = 3  # UPPER_CASE voor constanten

# Private methods
def _interne_functie(self):  # Underscore prefix voor private
    pass
```

### Output
- **Nieuwe/aangepaste code** met:
  - Volledige functionaliteit
  - Error handling
  - Logging
  - Documentatie

---

## Fase 3: 🧪 Test Fase

### Doel
Verifiëren dat de nieuwe/aangepaste code correct werkt.

### Stappen

#### 3.1 Unit Tests
```python
import pytest
from unittest.mock import Mock, patch

class TestImprovedImplementation:
    """Test suite voor verbeterde implementatie."""

    def test_happy_path(self):
        """Test normale werking."""
        impl = ImprovedImplementation()
        result = impl.process(valid_data)

        assert result.status == "success"
        assert len(result.data) > 0

    def test_error_handling(self):
        """Test error scenarios."""
        impl = ImprovedImplementation()

        with pytest.raises(ValidationError):
            impl.process(invalid_data)

    def test_edge_cases(self):
        """Test edge cases."""
        test_cases = [
            (None, ValidationError),
            ("", ValidationError),
            ([], EmptyDataError),
            (very_large_data, PerformanceWarning)
        ]

        for data, expected_error in test_cases:
            with pytest.raises(expected_error):
                impl.process(data)

    @patch('external_service.api_call')
    def test_with_mocked_dependencies(self, mock_api):
        """Test met gemockte externe dependencies."""
        mock_api.return_value = {"status": "ok"}

        result = impl.process_with_external(data)
        assert mock_api.called
        assert result.external_status == "ok"
```

#### 3.2 Integration Tests
```python
def test_database_integration():
    """Test database operaties."""
    with test_database() as db:
        # Setup test data
        db.add_test_records()

        # Test operatie
        result = impl.process_from_database()

        # Verify
        assert db.record_count() > 0
        assert result.processed_count == db.record_count()

def test_api_integration():
    """Test API integratie."""
    with mock_api_server() as server:
        impl = ImprovedImplementation(api_url=server.url)

        result = impl.fetch_and_process()

        assert server.request_count == 1
        assert result.source == "api"
```

#### 3.3 Performance Tests
```python
import pytest
import time

@pytest.mark.performance
def test_processing_speed():
    """Verifieer performance requirements."""
    impl = ImprovedImplementation()
    large_dataset = generate_test_data(10000)

    start_time = time.time()
    result = impl.process(large_dataset)
    duration = time.time() - start_time

    assert duration < 5.0  # Max 5 seconden
    assert result.items_per_second > 2000

@pytest.mark.memory
def test_memory_usage():
    """Controleer memory gebruik."""
    import psutil
    import os

    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss

    # Voer operatie uit
    impl.process_large_dataset()

    final_memory = process.memory_info().rss
    memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB

    assert memory_increase < 100  # Max 100MB increase
```

#### 3.4 Test Coverage
```bash
# Run tests met coverage
pytest --cov=src --cov-report=html

# Check coverage percentage
coverage report

# Minimum coverage targets
□ Overall coverage: > 80%
□ Critical modules: > 90%
□ New code: 100%
```

### Output
- **Test Report** met:
  - Alle tests groen
  - Coverage rapport
  - Performance metrics
  - Integration test resultaten

---

## Fase 4: ✅ Review Fase

### Doel
Code review volgens het vastgestelde protocol om kwaliteit te waarborgen.

### Stappen

#### 4.1 Pre-Review Checklist
```bash
□ Alle tests draaien groen
□ Linting geen errors (ruff, black)
□ Type checking passed (mypy)
□ Documentation compleet
□ Git diff gecontroleerd
```

#### 4.2 Code Review Protocol Uitvoering

##### Phase 1: Quick Existence Check (5 min)
```bash
□ Bestaat het bestand/de module?
□ Kan het geïmporteerd worden zonder errors?
□ Zijn er obvious syntax errors?
□ Bestaat de documentatie?
□ Type hints aanwezig en correct?
```

##### Phase 2: Dependency Analysis (10 min)
```bash
□ Lijst alle imports
□ Verifieer dat alle dependencies bestaan
□ Check of import namen kloppen
□ Identificeer circulaire dependencies
□ Controleer versie compatibiliteit
```

##### Phase 3: Functionality Test (20 min)
```bash
□ Start de functionaliteit op
□ Voer happy path test uit
□ Test edge cases
□ Test error handling
□ Verifieer output format
```

##### Phase 4: Security & Performance (15 min)
```bash
## Security
□ Input validation compleet?
□ SQL Injection preventie?
□ Authentication/Authorization correct?
□ Secrets management veilig?

## Performance
□ Database queries geoptimaliseerd?
□ Caching strategy aanwezig?
□ Memory leaks check
□ Async waar nodig?
```

#### 4.3 Review Output Format
```markdown
# Component: [Naam]
**Review Datum**: [YYYY-MM-DD]
**Reviewer**: BMad QA Agent
**Claimed Status**: [Development claim]
**Actual Status**: [Verified status]

## Bevindingen

### ✅ Wat Werkt
- [Feature X] werkt correct met [metrics]
- Performance binnen targets: [latency]ms

### ❌ Wat Niet Werkt
- [Issue Y] met root cause [Z]

### ⚠️ Verbeterpunten
- [Suggestie A] voor betere [aspect]

## Quality Metrics
- **Code Coverage**: 85% (Target: 80%) ✅
- **Cyclomatic Complexity**: 8 (Target: <10) ✅
- **Security Score**: 92/100 ✅

## Action Items
1. 🔴 **CRITICAL**: [Geen]
2. 🟠 **HIGH**: [Security headers toevoegen]
3. 🟡 **MEDIUM**: [Refactor lange functie X]
```

### Output
- **Review Report** met:
  - Verified functionaliteit
  - Quality metrics
  - Security assessment
  - Action items voor verbetering

---

## 🚀 Workflow Automatisering

### Git Hooks
```bash
# .git/hooks/pre-commit
#!/bin/bash
echo "Running pre-commit checks..."

# Syntax check
python -m py_compile $(git diff --cached --name-only --diff-filter=ACM | grep '\.py$')

# Linting
ruff check $(git diff --cached --name-only --diff-filter=ACM | grep '\.py$')

# Tests
pytest tests/unit/

echo "Pre-commit checks passed!"
```

### CI/CD Pipeline
```yaml
# .github/workflows/debug-dev-workflow.yml
name: Debug & Development Workflow

on: [push, pull_request]

jobs:
  phase1-debug:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Collect debug info
        run: |
          python scripts/collect_debug_info.py

  phase2-develop:
    needs: phase1-debug
    steps:
      - name: Lint code
        run: |
          ruff check src/
          black --check src/

  phase3-test:
    needs: phase2-develop
    steps:
      - name: Run tests
        run: |
          pytest --cov=src

  phase4-review:
    needs: phase3-test
    steps:
      - name: Code review
        run: |
          python scripts/automated_review.py
```

---

## 📊 Workflow Metrics

### KPIs te Monitoren
- **Debug Time**: Tijd van probleem identificatie tot root cause
- **Development Velocity**: Features/fixes per sprint
- **Test Coverage**: Percentage code coverage
- **Review Turnaround**: Tijd voor code review completion
- **Defect Escape Rate**: Bugs gevonden na review

### Continuous Improvement
1. **Weekly Retrospective**: Evalueer workflow effectiviteit
2. **Metrics Review**: Analyseer KPIs trends
3. **Process Updates**: Pas workflow aan op basis van feedback
4. **Tool Evaluation**: Evalueer nieuwe tools/technieken

---

## 🎯 Best Practices

### Debug Fase
- Reproduceer eerst, fix daarna
- Document alle bevindingen
- Gebruik systematische aanpak

### Development Fase
- Write tests first (TDD)
- Keep changes small
- Refactor continuously

### Test Fase
- Test edge cases
- Mock external dependencies
- Measure performance

### Review Fase
- Be constructive
- Focus on high-risk areas
- Suggest improvements

---

**Workflow Eigenaar**: BMad Development Team
**Laatste Update**: 2025-08-25
**Volgende Review**: 2025-09-25
