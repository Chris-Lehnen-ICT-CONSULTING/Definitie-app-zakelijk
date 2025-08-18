# Epic 7: Test Suite Restoration

**Epic Goal**: Creëer betrouwbare test coverage voor confident development.

**Business Value**: Minder bugs, snellere development cycles, team confidence.

**Total Story Points**: 18

**Target Sprint**: 5-6

## Current State

- Total tests: 50+
- Passing: 7 (14%)
- Failing: 43 (86%)
- Coverage: Unknown (likely <20%)
- Main issues: Import errors, missing fixtures, outdated assertions

## Target State

- All tests passing
- Coverage: 60%+ overall, 80%+ for critical paths
- CI/CD pipeline active
- Test execution time: <5 minutes

## Stories

### STORY-007-01: Fix Import Paths

**Story Points**: 2

**Als een** developer  
**wil ik** consistente imports  
**zodat** tests kunnen draaien.

#### Acceptance Criteria
- [ ] Alle imports werkend
- [ ] Geen circular dependencies
- [ ] Import style guide
- [ ] Auto-fix script

#### Common Import Issues
```python
# BROKEN - Relative imports failing
from services.definition_service import DefinitionService
from ..models import Definition

# FIXED - Absolute imports from src
from src.services.unified_definition_service import UnifiedDefinitionService
from src.models.definition import Definition

# FIXED - Test-specific imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
```

#### Import Fixer Script
```python
#!/usr/bin/env python3
"""Fix all import statements in test files."""

import os
import re
from pathlib import Path

class ImportFixer:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.src_path = project_root / "src"
        
    def fix_imports_in_file(self, file_path: Path):
        """Fix imports in a single file."""
        content = file_path.read_text()
        
        # Fix patterns
        replacements = [
            # Old service imports
            (r'from services\.definition_service', 'from src.services.unified_definition_service'),
            (r'from services\.', 'from src.services.'),
            
            # Relative imports
            (r'from \.\.models', 'from src.models'),
            (r'from \.\.', 'from src.'),
            
            # Missing src prefix
            (r'from (ai_toetsing|generation|validation|web_lookup)',
             r'from src.\1'),
        ]
        
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)
        
        file_path.write_text(content)
        
    def add_path_setup(self, test_file: Path):
        """Add path setup to test file if missing."""
        content = test_file.read_text()
        
        if 'sys.path.insert' not in content:
            setup = '''import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

'''
            content = setup + content
            test_file.write_text(content)
```

---

### STORY-007-02: Create Test Fixtures

**Story Points**: 3

**Als een** developer  
**wil ik** herbruikbare test data  
**zodat** tests consistent zijn.

#### Acceptance Criteria
- [ ] Definition fixtures
- [ ] User fixtures
- [ ] Validation result fixtures
- [ ] Mock API responses

#### Fixture Structure
```python
# tests/fixtures/__init__.py
from .definitions import *
from .users import *
from .validations import *
from .api_mocks import *

# tests/fixtures/definitions.py
import pytest
from datetime import datetime
from src.models.definition import Definition

@pytest.fixture
def sample_definition():
    """Basic definition fixture."""
    return Definition(
        id=1,
        term="aansprakelijkheid",
        definition="De juridische verantwoordelijkheid voor schade.",
        context="juridisch",
        context_type="algemeen",
        validation_score=85,
        created_at=datetime.now()
    )

@pytest.fixture
def enriched_definition(sample_definition):
    """Definition with enrichments."""
    definition = sample_definition
    definition.synonyms = ["verantwoordelijkheid", "liability"]
    definition.antonyms = ["onschuld", "vrijwaring"]
    definition.examples = [
        "De aansprakelijkheid ligt bij de veroorzaker.",
        "Beperkte aansprakelijkheid is mogelijk."
    ]
    return definition

@pytest.fixture
def definitions_batch():
    """Multiple definitions for testing."""
    terms = ["contract", "overeenkomst", "verbintenis"]
    return [
        Definition(
            term=term,
            definition=f"Test definitie voor {term}",
            context="juridisch"
        )
        for term in terms
    ]
```

#### Mock Fixtures
```python
# tests/fixtures/api_mocks.py
@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "gpt-4",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Een aansprakelijkheid is..."
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 150,
            "completion_tokens": 100,
            "total_tokens": 250
        }
    }

@pytest.fixture
def mock_openai_client(mocker, mock_openai_response):
    """Mock OpenAI client."""
    mock_client = mocker.Mock()
    mock_client.chat.completions.create.return_value = mock_openai_response
    return mock_client
```

---

### STORY-007-03: Fix Unit Tests Core

**Story Points**: 5

**Als een** developer  
**wil ik** werkende unit tests  
**zodat** business logic gedekt is.

#### Acceptance Criteria
- [ ] Service layer tests
- [ ] Validator tests
- [ ] 80% coverage target
- [ ] Fast execution (<30s)

#### Service Tests
```python
# tests/unit/test_unified_definition_service.py
import pytest
from unittest.mock import Mock, patch
from src.services.unified_definition_service import UnifiedDefinitionService

class TestUnifiedDefinitionService:
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup before each test."""
        # Reset singleton
        UnifiedDefinitionService._instance = None
        self.service = UnifiedDefinitionService.get_instance()
    
    def test_singleton_pattern(self):
        """Test singleton returns same instance."""
        service1 = UnifiedDefinitionService.get_instance()
        service2 = UnifiedDefinitionService.get_instance()
        assert service1 is service2
    
    @patch('src.services.unified_definition_service.OpenAI')
    def test_generate_definition(self, mock_openai, sample_definition):
        """Test definition generation."""
        # Setup mock
        mock_openai.return_value.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Test definitie"))]
        )
        
        # Test
        result = self.service.generate_definition(
            term="test",
            context="algemeen"
        )
        
        # Assertions
        assert result is not None
        assert result.term == "test"
        assert "definitie" in result.definition.lower()
    
    def test_validation_integration(self, sample_definition):
        """Test validation is called correctly."""
        with patch.object(self.service, 'validator') as mock_validator:
            mock_validator.validate.return_value = Mock(
                score=85,
                passed_rules=40,
                total_rules=46
            )
            
            result = self.service.validate_definition(sample_definition)
            
            assert result.score == 85
            mock_validator.validate.assert_called_once()
```

#### Validator Tests
```python
# tests/unit/test_validators.py
import pytest
from src.ai_toetsing.validators import (
    SAM_01_CircularityValidator,
    STR_01_CapitalizationValidator,
    LEN_01_LengthValidator
)

class TestValidators:
    
    @pytest.mark.parametrize("definition,expected", [
        ("Aansprakelijkheid is aansprakelijkheid", False),
        ("De juridische verantwoordelijkheid", True),
        ("Een term is een term", False),
    ])
    def test_circularity_validator(self, definition, expected):
        """Test SAM-01 circular definition detection."""
        validator = SAM_01_CircularityValidator()
        result = validator.validate(definition, "aansprakelijkheid")
        assert result.passed == expected
    
    @pytest.mark.parametrize("definition,expected", [
        ("de juridische term", False),  # No capital
        ("De juridische term", True),   # Correct
        ("DE JURIDISCHE TERM", True),   # All caps OK
    ])
    def test_capitalization_validator(self, definition, expected):
        """Test STR-01 capitalization rule."""
        validator = STR_01_CapitalizationValidator()
        result = validator.validate(definition, "test")
        assert result.passed == expected
```

---

### STORY-007-04: Add Integration Tests

**Story Points**: 5

**Als een** developer  
**wil ik** end-to-end tests  
**zodat** user flows getest zijn.

#### Acceptance Criteria
- [ ] Happy path scenarios
- [ ] Error scenarios
- [ ] UI interaction tests
- [ ] API integration tests

#### Integration Test Examples
```python
# tests/integration/test_definition_flow.py
import pytest
from sqlalchemy import create_engine
from src.app import create_app
from src.database import Base

class TestDefinitionFlow:
    
    @pytest.fixture
    def test_db(self):
        """Create test database."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        yield engine
        Base.metadata.drop_all(engine)
    
    @pytest.fixture
    def client(self, test_db):
        """Create test client."""
        app = create_app(test_db)
        return app.test_client()
    
    def test_complete_definition_flow(self, client, mock_openai_client):
        """Test full flow from input to storage."""
        # 1. Generate definition
        response = client.post('/api/generate', json={
            'term': 'test_term',
            'context': 'juridisch'
        })
        
        assert response.status_code == 200
        definition_id = response.json['id']
        
        # 2. Validate definition
        response = client.post(f'/api/validate/{definition_id}')
        assert response.status_code == 200
        assert 'score' in response.json
        
        # 3. Enrich definition
        response = client.post(f'/api/enrich/{definition_id}')
        assert response.status_code == 200
        assert 'synonyms' in response.json
        
        # 4. Export definition
        response = client.get(f'/api/export/{definition_id}?format=json')
        assert response.status_code == 200
        assert response.json['term'] == 'test_term'
```

#### UI Integration Tests
```python
# tests/integration/test_streamlit_ui.py
from streamlit.testing.v1 import AppTest

def test_definition_generation_ui():
    """Test definition generation through UI."""
    at = AppTest.from_file("src/app.py")
    at.run()
    
    # Enter term
    at.text_input[0].input("aansprakelijkheid")
    
    # Select context
    at.selectbox[0].select("juridisch")
    
    # Click generate
    at.button[0].click()
    
    # Check results
    at.run()
    assert "aansprakelijkheid" in at.markdown[0].value
    assert at.success[0].value == "Definitie gegenereerd!"
```

---

### STORY-007-05: Setup CI Pipeline

**Story Points**: 3

**Als een** team  
**willen wij** automated testing  
**zodat** bugs vroeg gevangen worden.

#### Acceptance Criteria
- [ ] Tests run on commit
- [ ] Coverage reports
- [ ] Build status badges
- [ ] Failed test notifications

#### GitHub Actions Configuration
```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      redis:
        image: redis:6
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run linting
      run: |
        black --check src tests
        isort --check-only src tests
        flake8 src tests
    
    - name: Run tests with coverage
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      run: |
        pytest tests/ \
          --cov=src \
          --cov-report=xml \
          --cov-report=html \
          --cov-report=term-missing \
          -v
    
    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
    
    - name: Check coverage threshold
      run: |
        coverage report --fail-under=60
```

#### Build Status Badge
```markdown
# In README.md
[![Test Suite](https://github.com/org/definitie-app/actions/workflows/test.yml/badge.svg)](https://github.com/org/definitie-app/actions/workflows/test.yml)
[![Coverage](https://codecov.io/gh/org/definitie-app/branch/main/graph/badge.svg)](https://codecov.io/gh/org/definitie-app)
```

## Definition of Done (Epic Level)

- [ ] All tests passing (0 failures)
- [ ] Coverage >60% overall
- [ ] Critical paths >80% coverage
- [ ] CI pipeline green
- [ ] Test execution <5 minutes
- [ ] Documentation updated
- [ ] Team trained on test practices

## Test Strategy

### Unit Tests (60% of tests)
- Fast, isolated, no external dependencies
- Mock all I/O operations
- Focus on business logic

### Integration Tests (30% of tests)
- Test component interactions
- Use test database
- Mock external APIs

### E2E Tests (10% of tests)
- Critical user journeys only
- Run nightly, not on every commit
- Real browser testing

## Success Metrics

- Bug reduction: -40%
- Development velocity: +20%
- Deployment confidence: High
- Production incidents: -50%

---
*Epic owner: QA Team*  
*Last updated: 2025-01-18*