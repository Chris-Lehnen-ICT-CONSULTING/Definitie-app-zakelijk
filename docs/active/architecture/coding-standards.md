# Coding Standards - DefinitieAgent

## Overview

Dit document definieert de coding standards en conventies voor het DefinitieAgent project. Alle code moet deze standards volgen voor consistentie en maintainability.

## Python Code Standards

### General Principles

1. **Readability First**: Code leesbaarheid heeft prioriteit boven cleverness
2. **Explicit is Better**: Wees expliciet in je intenties
3. **Consistency**: Volg bestaande patterns in de codebase
4. **Documentation**: Documenteer complexe logica altijd

### Code Style

#### Formatting
- **Formatter**: Black (line length: 88)
- **Import Sorter**: isort
- **Python Version**: 3.8+ (3.11+ aanbevolen)

```python
# Correct import order
import os
import sys
from typing import Dict, List, Optional

import pandas as pd
from sqlalchemy import create_engine

from src.services.unified_definition_service import UnifiedDefinitionService
from src.utils.exceptions import ValidationError
```

#### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Classes | PascalCase | `UnifiedDefinitionService` |
| Functions | snake_case | `generate_definition()` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRY_ATTEMPTS` |
| Private methods | _leading_underscore | `_validate_input()` |
| Module files | snake_case | `definition_service.py` |

### Type Hints

Gebruik type hints voor alle public functions:

```python
from typing import Dict, List, Optional, Union

def generate_definition(
    term: str,
    context: Optional[str] = None,
    temperature: float = 0.3
) -> Dict[str, Union[str, Dict[str, Any]]]:
    """
    Genereert een definitie voor het gegeven begrip.
    
    Args:
        term: Het te definiëren begrip
        context: Optionele context (juridisch, technisch, etc.)
        temperature: OpenAI temperature parameter
        
    Returns:
        Dictionary met definitie en metadata
    """
    pass
```

### Error Handling

```python
# Gebruik specifieke exceptions
try:
    result = process_definition(term)
except ValidationError as e:
    logger.error(f"Validation failed for term '{term}': {e}")
    raise
except Exception as e:
    logger.exception(f"Unexpected error processing '{term}'")
    raise ProcessingError(f"Failed to process definition: {str(e)}")

# Geen bare except clauses
# FOUT:
except:
    pass
    
# GOED:
except Exception as e:
    logger.error(f"Error: {e}")
```

### Documentation

#### Docstrings

Gebruik Google-style docstrings in het Nederlands voor business logic:

```python
def validate_definition(definition: str, term: str) -> ValidationResult:
    """
    Valideert een definitie tegen de 46 kwaliteitsregels.
    
    Deze functie controleert of de gegenereerde definitie voldoet aan
    alle verplichte en aanbevolen kwaliteitsregels. Bij het falen van
    verplichte regels wordt de definitie afgekeurd.
    
    Args:
        definition: De te valideren definitietekst
        term: Het gedefinieerde begrip
        
    Returns:
        ValidationResult object met score en details
        
    Raises:
        ValidationError: Als de input ongeldig is
        
    Example:
        >>> result = validate_definition("Een test is...", "test")
        >>> print(result.score)
        85
    """
    # Implementatie met inline commentaar voor complexe logica
    # Bereken eerst de basis score
    base_score = calculate_base_score(definition)
    
    # Pas ontologische categorisatie toe volgens 6-stappen protocol
    ontology_score = apply_ontology_rules(definition, term)
```

#### Inline Comments

- Nederlands voor business logic
- Engels voor technische implementatie details
- Gebruik `# TODO (YYYY-MM-DD):` voor todo's

```python
# Controleer of het begrip een cirkelredenering bevat
if term.lower() in definition.lower():
    # TODO (2025-01-18): Implementeer slimmere detectie voor vervoegingen
    return ValidationError("SAM-01: Cirkelredenering gedetecteerd")

# Technical: Use batch processing for performance
batch_size = 100  # Process definitions in batches
```

### Testing

#### Test File Naming
- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName>`
- Test methods: `test_<method_name>_<scenario>`

```python
# tests/unit/test_definition_service.py
class TestUnifiedDefinitionService:
    def test_generate_definition_with_valid_input(self):
        """Test dat definitie generatie werkt met valide input."""
        pass
        
    def test_generate_definition_raises_on_empty_term(self):
        """Test dat lege term een ValidationError geeft."""
        pass
```

#### Test Coverage
- Minimum: 80% coverage nastreven
- Focus op business logic coverage
- UI code mag lager (60%)

### Project Structure

```
src/
├── __init__.py
├── services/          # Business logic services
├── ai_toetsing/      # Validation rules
├── ui/               # Streamlit UI components
├── models/           # Data models
├── repositories/     # Data access layer
├── utils/            # Shared utilities
└── config/           # Configuration
```

### Git Conventions

#### Branch Naming
- `feature/beschrijving` - nieuwe features
- `bugfix/issue-nummer` - bug fixes
- `refactor/module-naam` - refactoring
- `hotfix/kritieke-fix` - productie fixes

#### Commit Messages
```
<type>: <korte beschrijving>

<Uitgebreide beschrijving in het Nederlands>

- Lijst van wijzigingen
- Breaking changes: ...
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `style`, `chore`

### Performance Guidelines

1. **Profile First**: Meet voor je optimaliseert
2. **Cache Wisely**: Cache dure operaties (AI calls)
3. **Async Where Possible**: Gebruik async voor I/O
4. **Batch Operations**: Groepeer database operaties

### Security Guidelines

1. **No Secrets in Code**: Gebruik environment variables
2. **Input Validation**: Valideer alle user input
3. **SQL Injection**: Gebruik parameterized queries
4. **Rate Limiting**: Implementeer rate limiting voor APIs

## Streamlit Specific

### Session State Management
```python
# Initialize session state properly
if 'definition_history' not in st.session_state:
    st.session_state.definition_history = []

# Use callbacks for state updates
def update_definition():
    st.session_state.current_definition = new_value
```

### Component Organization
- One component per file in `ui/components/`
- Reusable components in `ui/shared/`
- Keep business logic out of UI code

## AI/LLM Integration

### Prompt Engineering
1. Keep prompts in separate config files
2. Version control prompt changes
3. Document prompt structure
4. Test prompt variations

### Model Parameters
```python
# Centralize model configuration
MODEL_CONFIG = {
    "model": "gpt-4",
    "temperature": 0.3,  # Lager voor consistentie
    "max_tokens": 1500,
    "timeout": 30
}
```

## Code Review Checklist

- [ ] Code volgt Black formatting
- [ ] Type hints toegevoegd
- [ ] Docstrings voor public functions
- [ ] Tests toegevoegd/aangepast
- [ ] Geen hardcoded secrets
- [ ] Error handling adequaat
- [ ] Performance impact overwogen
- [ ] Nederlands commentaar voor business logic

## Enforcement

Deze standards worden gehandhaafd door:
1. Pre-commit hooks
2. CI/CD pipeline checks
3. Code review process
4. Automated linting

---
*Laatste update: 2025-01-18*