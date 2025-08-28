# Coding Standards - DefinitieAgent

## Overzicht

Dit document beschrijft de coding standards en conventies voor het DefinitieAgent project. Deze standards zorgen voor consistentie, leesbaarheid en onderhoudbaarheid van de codebase.

## Algemene Principes

1. **Clarity over Cleverness**: Code moet leesbaar en begrijpelijk zijn
2. **Consistency**: Volg bestaande patronen in de codebase
3. **Documentation**: Documenteer complexe logica en publieke interfaces
4. **Testing**: Schrijf tests voor nieuwe functionaliteit

## Python Code Standards

### Code Formatting

- **Formatter**: Black (line-length: 88)
- **Import Sorter**: Ruff (isort compatible)
- **Python Version**: 3.10+

```python
# Correct
from typing import Optional, List
import asyncio

from src.services.base import BaseService
from src.domain.models import Definition


# Incorrect
import asyncio
from typing import Optional, List
from src.services.base import BaseService
from src.domain.models import Definition
```

### Linting Rules

We gebruiken Ruff met de volgende rule sets:
- E (pycodestyle errors)
- F (Pyflakes)
- I (isort)
- N (pep8-naming)
- UP (pyupgrade)
- S (flake8-bandit security)
- B (flake8-bugbear)
- A (flake8-builtins)
- COM (flake8-commas)
- C4 (flake8-comprehensions)
- T10 (flake8-debugger)
- EM (flake8-errmsg)
- ISC (flake8-implicit-str-concat)
- ICN (flake8-import-conventions)
- T20 (flake8-print)
- PT (flake8-pytest-style)
- RET (flake8-return)
- SIM (flake8-simplify)
- TD (flake8-todos)
- FIX (flake8-fixme)
- ERA (eradicate)
- PL (Pylint)
- RUF (Ruff-specific rules)

### Type Hints

Gebruik type hints voor alle publieke functies en methoden:

```python
# Correct
async def generate_definition(
    term: str,
    context: Optional[str] = None,
    category: DefinitionCategory = DefinitionCategory.TYPE
) -> Definition:
    """Generate a legal definition for the given term."""
    ...

# Incorrect
async def generate_definition(term, context=None, category="type"):
    """Generate a legal definition for the given term."""
    ...
```

### Naming Conventions

- **Classes**: PascalCase (e.g., `DefinitionOrchestrator`)
- **Functions/Methods**: snake_case (e.g., `generate_definition`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_RETRIES`)
- **Private**: Prefix with underscore (e.g., `_internal_method`)

### Async/Await Patterns

```python
# Correct - Gebruik async/await voor I/O operations
async def fetch_definition(self, term: str) -> Definition:
    async with self.session as session:
        result = await session.execute(query)
        return result.scalar_one_or_none()

# Incorrect - Blocking I/O in async context
async def fetch_definition(self, term: str) -> Definition:
    # DON'T: This blocks the event loop
    result = requests.get(f"/api/definitions/{term}")
    return result.json()
```

## Architecture Patterns

### Service Layer Pattern

```python
class DefinitionService(BaseService):
    """Service for managing definitions."""

    def __init__(
        self,
        repository: DefinitionRepository,
        ai_service: AIServiceInterface,
        validator: DefinitionValidator
    ):
        self._repository = repository
        self._ai_service = ai_service
        self._validator = validator

    async def create_definition(
        self,
        request: CreateDefinitionRequest
    ) -> Definition:
        """Create a new definition."""
        # Validate input
        validated_data = await self._validator.validate(request)

        # Generate via AI
        ai_response = await self._ai_service.generate(validated_data)

        # Persist
        return await self._repository.save(ai_response)
```

### Error Handling

```python
# Correct - Specific error handling
try:
    result = await ai_service.generate(prompt)
except RateLimitError as e:
    logger.warning(f"Rate limit hit: {e}")
    await asyncio.sleep(e.retry_after)
    return await self.retry_with_backoff(prompt)
except AIServiceError as e:
    logger.error(f"AI service error: {e}")
    raise DefinitionGenerationError(f"Could not generate definition: {e}")

# Incorrect - Generic catch-all
try:
    result = await ai_service.generate(prompt)
except Exception as e:
    logger.error(f"Error: {e}")
    raise
```

### Dependency Injection

```python
# Correct - Dependencies injected
class OrchestrationService:
    def __init__(
        self,
        ai_service: AIServiceInterface,
        cache: CacheInterface,
        metrics: MetricsInterface
    ):
        self._ai_service = ai_service
        self._cache = cache
        self._metrics = metrics

# Incorrect - Hard dependencies
class OrchestrationService:
    def __init__(self):
        self._ai_service = OpenAIService()  # Hard-coded dependency
        self._cache = RedisCache()         # Hard-coded dependency
        self._metrics = PrometheusMetrics() # Hard-coded dependency
```

## Documentation Standards

### Docstrings

Gebruik Google-style docstrings:

```python
def calculate_confidence_score(
    definition: Definition,
    validation_results: List[ValidationResult]
) -> float:
    """Calculate confidence score for a definition.

    Args:
        definition: The definition to score
        validation_results: Results from validation rules

    Returns:
        Confidence score between 0.0 and 1.0

    Raises:
        ValueError: If validation_results is empty
    """
    if not validation_results:
        raise ValueError("Cannot calculate score without validation results")

    # Implementation...
```

### Code Comments

**BELANGRIJK**: Alle code moet voorzien worden van inline commentaar in het Nederlands dat uitlegt wat de code doet voor niet-programmeurs.

```python
# Correct - Legt uit WAT en WAAROM in begrijpelijke taal
# We wachten steeds langer tussen pogingen om de server niet te overbelasten
# Eerste poging: 0.1 seconde, tweede: 0.2, derde: 0.4, enz. (max 60 seconden)
wacht_tijd = min(2 ** poging * 0.1, 60.0)

# Ook correct - Stap voor stap uitleg
# Bereken hoeveel definities we vandaag al hebben gegenereerd
aantal_vandaag = haal_aantal_definities_op(datum=vandaag())
# Controleer of we onder het dagelijkse limiet zitten (maximaal 1000)
if aantal_vandaag >= DAGELIJKS_LIMIET:
    # We hebben het limiet bereikt, geef een foutmelding
    raise LimietBereiktFout("Dagelijks limiet van 1000 definities bereikt")

# Incorrect - Te technisch of ontbrekend commentaar
retry_delay = 2 ** attempt * 0.1  # Geen uitleg
```

#### Richtlijnen voor Commentaar

1. **Schrijf voor niet-programmeurs**: Stel je voor dat je het uitlegt aan een collega zonder programmeerkennis
2. **Leg elke belangrijke stap uit**: Wat doet deze regel code?
3. **Gebruik Nederlandse termen**: Vermijd technisch jargon waar mogelijk
4. **Geef context**: Waarom is deze code nodig?
5. **Voorbeelden helpen**: Geef concrete voorbeelden bij complexe logica

```python
# Voorbeeld van goed gedocumenteerde functie
def bereken_vertrouwensscore(definitie: Definitie, validatie_resultaten: List[ValidatieResultaat]) -> float:
    """
    Berekent hoe betrouwbaar een definitie is op basis van validatieresultaten.

    Een definitie krijgt een score tussen 0.0 (onbetrouwbaar) en 1.0 (zeer betrouwbaar).
    De score wordt bepaald door het percentage geslaagde validaties.

    Args:
        definitie: De definitie waarvan we de betrouwbaarheid willen weten
        validatie_resultaten: Lijst met resultaten van alle validatietests

    Returns:
        Een getal tussen 0.0 en 1.0 dat aangeeft hoe betrouwbaar de definitie is

    Raises:
        FoutmeldinWaarde: Als er geen validatieresultaten zijn
    """
    # Controleer eerst of we wel validatieresultaten hebben
    if not validatie_resultaten:
        raise FoutmeldinWaarde("Kan geen score berekenen zonder validatieresultaten")

    # Tel hoeveel validaties geslaagd zijn
    aantal_geslaagd = 0
    for resultaat in validatie_resultaten:
        # Als deze validatie geslaagd is, tel hem mee
        if resultaat.geslaagd:
            aantal_geslaagd += 1

    # Bereken het percentage geslaagde validaties
    # Bijvoorbeeld: 8 van de 10 geslaagd = 0.8 (80%)
    totaal_aantal = len(validatie_resultaten)
    vertrouwensscore = aantal_geslaagd / totaal_aantal

    # Geef de score terug
    return vertrouwensscore
```

## Testing Standards

### Test Organization

```
tests/
├── unit/           # Fast, isolated unit tests
├── integration/    # Tests with real dependencies
├── e2e/           # End-to-end user scenarios
└── fixtures/      # Test data and mocks
```

### Test Naming

```python
# Pattern: test_{method_name}_{scenario}_{expected_result}

def test_generate_definition_valid_input_returns_definition():
    """Test that valid input produces a definition."""
    ...

def test_generate_definition_empty_term_raises_validation_error():
    """Test that empty term raises ValidationError."""
    ...
```

### Test Structure (AAA Pattern)

```python
async def test_definition_caching():
    # Arrange
    service = DefinitionService(mock_ai, mock_cache)
    term = "contract"

    # Act
    result1 = await service.generate(term)
    result2 = await service.generate(term)  # Should hit cache

    # Assert
    assert result1 == result2
    mock_ai.generate.assert_called_once()  # AI only called once
    mock_cache.get.assert_called_with(f"definition:{term}")
```

## Security Standards

### Input Validation

```python
# Always validate and sanitize user input
def create_definition(self, user_input: str) -> Definition:
    # Sanitize input
    clean_input = self._sanitizer.clean(user_input)

    # Validate format
    if not self._validator.is_valid_term(clean_input):
        raise ValidationError("Invalid term format")

    # Proceed with clean, validated input
    return self._generate_definition(clean_input)
```

### Secret Management

```python
# Correct - Use environment variables
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise ConfigurationError("OPENAI_API_KEY not set")

# Incorrect - Hardcoded secrets
api_key = "sk-1234567890abcdef"  # NEVER DO THIS
```

## Performance Standards

### Caching

```python
# Use caching for expensive operations
@cached(ttl=3600)
async def get_enriched_definition(term: str) -> EnrichedDefinition:
    """Get definition with expensive enrichments."""
    base = await self.get_definition(term)
    enrichments = await self.fetch_enrichments(base)
    return EnrichedDefinition(base, enrichments)
```

### Batch Operations

```python
# Correct - Batch operations for efficiency
async def process_terms(self, terms: List[str]) -> List[Definition]:
    """Process multiple terms efficiently."""
    tasks = [self.generate_definition(term) for term in terms]
    return await asyncio.gather(*tasks)

# Incorrect - Sequential processing
async def process_terms(self, terms: List[str]) -> List[Definition]:
    """Process terms one by one."""
    results = []
    for term in terms:
        result = await self.generate_definition(term)
        results.append(result)
    return results
```

## Language Standards

### Taal Conventies

- **Code**: Nederlands (variabelen, functies, classes)
- **Comments**: Nederlands, begrijpelijk voor niet-programmeurs
- **Docstrings**: Nederlands
- **User-facing strings**: Nederlands
- **Technische termen**: Nederlands waar mogelijk

```python
# Correct
class ValidatieRegel:
    """Basisklasse voor validatieregels."""

    def valideer(self, definitie: Definitie) -> ValidatieResultaat:
        """
        Controleert of de definitie aan deze regel voldoet.

        Deze functie kijkt of de definitie een beschrijving heeft.
        Als er geen beschrijving is, wordt de definitie afgekeurd.
        """
        # Controleer of de definitie wel een beschrijving heeft
        if not definitie.beschrijving:
            # Geen beschrijving gevonden, dus de definitie is ongeldig
            return ValidatieResultaat(
                geldig=False,
                bericht="Definitie moet een beschrijving hebben"
            )
```

## Git Commit Standards

### Commit Messages

Format: `<type>(<scope>): <subject>`

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Build/tool changes

Examples:
```
feat(orchestrator): add async support for V2 pipeline
fix(validation): handle None values in ARAI rules
docs(api): update endpoint documentation
refactor(services): extract AI interface to separate module
```

## Code Review Checklist

- [ ] Code follows formatting standards (Black, Ruff)
- [ ] Type hints are present and correct
- [ ] Public methods have docstrings
- [ ] Complex logic is commented
- [ ] Tests are included for new functionality
- [ ] Security considerations addressed
- [ ] Performance impact considered
- [ ] No hardcoded secrets or credentials
- [ ] Error handling is appropriate
- [ ] Code is DRY (Don't Repeat Yourself)

## Exceptions and Edge Cases

### Legacy Code

Voor legacy code (V1) die nog niet gemigreerd is:
1. Markeer met `# TODO: Migrate to V2 pattern`
2. Documenteer waarom het nog niet gemigreerd is
3. Plan migratie in backlog

### Performance-Critical Sections

Voor performance-kritieke code:
1. Documenteer performance requirements
2. Include benchmarks in tests
3. Consider sync alternatives waar async overhead te groot is

### External Dependencies

Voor externe integraties:
1. Wrap in adapter pattern
2. Mock in tests
3. Document rate limits en constraints

## Tools en Automation

### Pre-commit Hooks

```yaml
repos:
  - repo: https://github.com/psf/black
    hooks:
      - id: black
        language_version: python3.10

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
```

### CI/CD Checks

- Code formatting (Black)
- Linting (Ruff)
- Type checking (mypy)
- Test coverage (>80%)
- Security scanning (bandit via Ruff S rules)

---

Deze coding standards zijn een levend document. Suggesties voor verbeteringen kunnen via pull requests worden ingediend.
