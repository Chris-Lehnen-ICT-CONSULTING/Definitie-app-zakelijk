# Coding Standards - DefinitieAgent

## Wijzigingshistorie

- 2025-08-28: Consistentie en veiligheid
  - Python versie gesynchroniseerd naar 3.11+
  - Loggingvoorbeelden gecorrigeerd (`logger.warning/error`)
  - Caching-decorator voorbeeld aansluitend op project (`cached`)
  - NL‑naamgeving aangescherpt met uitzonderingen voor externe API’s/logging
  - Inline commentaar richtlijn genuanceerd (focus op complexe/business‑kritieke logica)
  - Security- en concurrency‑richtlijnen toegevoegd

## Overzicht

Dit document beschrijft de coding standards en conventies voor het DefinitieAgent project. Deze standards zorgen voor consistentie, leesbaarheid en onderhoudbaarheid van de codebase.

## Algemene Principes

1. **Duidelijkheid boven Slimheid**: Code moet leesbaar en begrijpelijk zijn voor iedereen
2. **Consistentie**: Volg bestaande patronen in de codebase
3. **Documentatie**: Documenteer ALLE code met Nederlandse commentaren voor niet-programmeurs
4. **Testing**: Schrijf tests voor nieuwe functionaliteit
5. **Nederlands**: Gebruik Nederlandse namen voor eigen code (variabelen, functies, classes) en schrijf commentaar/docstrings in het Nederlands. Uitzonderingen: externe API’s, logging‑levels, HTTP‑methoden en protocollen blijven Engels.

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

- **Classes**: PascalCase in Nederlands (bijv. `DefinitieOrchestrator`)
- **Functions/Methods**: snake_case in Nederlands (bijv. `genereer_definitie`)
- **Constants**: UPPER_SNAKE_CASE in Nederlands (bijv. `MAX_POGINGEN`)
- **Private**: Prefix met underscore (bijv. `_interne_methode`)

Voorbeelden:
```python
# Classes
class DefinitieService:  # NIET: DefinitionService
class ValidatieRegel:    # NIET: ValidationRule

# Functies
def genereer_definitie():     # NIET: generate_definition
def valideer_invoer():         # NIET: validate_input

# Constanten
MAX_POGINGEN = 3               # NIET: MAX_RETRIES
DAGELIJKS_LIMIET = 1000       # NIET: DAILY_LIMIT
```

### Async/Await Patterns

```python
# Correct - Gebruik async/await voor I/O operaties
async def haal_definitie_op(self, term: str) -> Definitie:
    """Haalt een definitie op uit de database voor de gegeven term."""
    # Maak verbinding met de database
    async with self.sessie as sessie:
        # Voer de zoekopdracht uit in de database
        resultaat = await sessie.execute(zoekopdracht)
        # Geef het eerste resultaat terug (of None als er geen is)
        return resultaat.scalar_one_or_none()

# Incorrect - Blokkerende I/O in async context
async def haal_definitie_op(self, term: str) -> Definitie:
    # FOUT: Dit blokkeert het hele programma
    resultaat = requests.get(f"/api/definities/{term}")
    return resultaat.json()
```

## Architecture Patterns

### Service Layer Pattern

```python
class DefinitieService(BasisService):
    """Service voor het beheren van juridische definities."""

    def __init__(
        self,
        repository: DefinitieRepository,
        ai_service: AIServiceInterface,
        validator: DefinitieValidator
    ):
        # Bewaar de verschillende componenten die we nodig hebben
        self._repository = repository    # Voor database operaties
        self._ai_service = ai_service   # Voor AI gegenereerde content
        self._validator = validator     # Voor het controleren van invoer

    async def maak_definitie(
        self,
        aanvraag: MaakDefinitieAanvraag
    ) -> Definitie:
        """Maakt een nieuwe juridische definitie aan."""
        # Stap 1: Controleer of de aanvraag geldig is
        gevalideerde_data = await self._validator.valideer(aanvraag)

        # Stap 2: Laat de AI een definitie genereren
        ai_antwoord = await self._ai_service.genereer(gevalideerde_data)

        # Stap 3: Sla de definitie op in de database
        return await self._repository.bewaar(ai_antwoord)
```

### Error Handling

```python
# Correct - Specifieke foutafhandeling
try:
    # Probeer een definitie te genereren via de AI service
    resultaat = await ai_service.genereer(prompt)
except RateLimietFout as e:
    # We hebben te veel verzoeken gedaan, wacht even
    logger.warning("Rate limiet bereikt: %s", e)
    # Wacht het aantal seconden dat de API aangeeft
    await asyncio.sleep(e.wacht_seconden)
    # Probeer opnieuw met langzamere snelheid
    return await self.probeer_opnieuw_met_vertraging(prompt)
except AIServiceFout as e:
    # Er ging iets mis met de AI service
    logger.error("AI service fout: %s", e, exc_info=True)
    # Geef een duidelijke foutmelding door
    raise DefinitieGeneratieFout(f"Kon geen definitie genereren: {e}")

# Incorrect - Algemene catch-all (vangt alle fouten)
try:
    resultaat = await ai_service.genereer(prompt)
except Exception as e:
    # FOUT: We weten niet wat er mis ging
    logger.fout(f"Fout: {e}")
    raise
```

### Dependency Injection

```python
# Correct - Afhankelijkheden worden meegegeven (dependency injection)
class OrchestratieService:
    def __init__(
        self,
        ai_service: AIServiceInterface,
        cache: CacheInterface,
        metrics: MetricsInterface
    ):
        # Services worden van buitenaf meegegeven
        self._ai_service = ai_service      # AI service voor tekst generatie
        self._cache = cache                # Cache voor snelheid
        self._metrics = metrics            # Metrics voor monitoring

# Incorrect - Harde afhankelijkheden (vast in code)
class OrchestratieService:
    def __init__(self):
        # FOUT: Services worden hier aangemaakt (niet flexibel)
        self._ai_service = OpenAIService()  # Vast gekoppeld aan OpenAI
        self._cache = RedisCache()         # Vast gekoppeld aan Redis
        self._metrics = PrometheusMetrics() # Vast gekoppeld aan Prometheus
```

## Documentation Standards

### Docstrings

Gebruik Google-style docstrings:

```python
def bereken_vertrouwensscore(
    definitie: Definitie,
    validatie_resultaten: List[ValidatieResultaat]
) -> float:
    """Berekent vertrouwensscore voor een definitie.

    Args:
        definitie: De definitie om te scoren
        validatie_resultaten: Resultaten van validatieregels

    Returns:
        Vertrouwensscore tussen 0.0 en 1.0

    Raises:
        ValueError: Als validatie_resultaten leeg is
    """
    # Controleer of we validatie resultaten hebben
    if not validatie_resultaten:
        raise ValueError("Kan geen score berekenen zonder validatie resultaten")

    # Implementatie...
```

### Code Comments

**BELANGRIJK**: Voor complexe of business‑kritieke logica schrijf inline commentaar in het Nederlands dat uitlegt wat de code doet en waarom, gericht op niet‑programmeurs. Voor triviale code volstaat duidelijke naamgeving.

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
        ValueError: Als er geen validatieresultaten zijn
    """
    # Controleer eerst of we wel validatieresultaten hebben
    if not validatie_resultaten:
        raise ValueError("Kan geen score berekenen zonder validatieresultaten")

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
# Patroon: test_{methode_naam}_{scenario}_{verwacht_resultaat}

def test_genereer_definitie_geldige_invoer_geeft_definitie():
    """Test dat geldige invoer een definitie oplevert."""
    ...

def test_genereer_definitie_lege_term_geeft_validatie_fout():
    """Test dat een lege term een ValidatieFout geeft."""
    ...
```

### Test Structure (AAA Pattern)

```python
async def test_definitie_caching():
    # Arrange (Voorbereiden)
    # Maak een test service met nep AI en cache
    service = DefinitieService(nep_ai, nep_cache)
    term = "contract"

    # Act (Uitvoeren)
    # Vraag twee keer dezelfde definitie op
    resultaat1 = await service.genereer(term)
    resultaat2 = await service.genereer(term)  # Moet uit cache komen

    # Assert (Controleren)
    # Beide resultaten moeten hetzelfde zijn
    assert resultaat1 == resultaat2
    # De AI moet maar één keer aangeroepen zijn
    nep_ai.genereer.assert_called_once()
    # De cache moet gebruikt zijn voor de term
    nep_cache.haal_op.assert_called_with(f"definitie:{term}")
```

## Security Standards

### Input Validation

```python
# Valideer en zuiver altijd gebruikersinvoer
def maak_definitie(self, gebruiker_invoer: str) -> Definitie:
    # Stap 1: Maak de invoer schoon (verwijder gevaarlijke tekens)
    schone_invoer = self._zuiveraar.zuiver(gebruiker_invoer)

    # Stap 2: Controleer of het formaat klopt
    if not self._validator.is_geldige_term(schone_invoer):
        # De term voldoet niet aan onze regels
        raise ValidatieFout("Ongeldig term formaat")

    # Stap 3: Ga verder met de schoongemaakte en gevalideerde invoer
    return self._genereer_definitie(schone_invoer)
```

### Secret Management

```python
# Correct - Gebruik omgevingsvariabelen voor geheime sleutels
# Haal de API sleutel op uit de omgevingsvariabelen
api_sleutel = os.environ.get("OPENAI_API_KEY")
# Controleer of de sleutel wel bestaat
if not api_sleutel:
    raise ConfiguratieFout("OPENAI_API_KEY niet ingesteld")

# Incorrect - Hardgecodeerde geheimen
api_sleutel = "sk-1234567890abcdef"  # NOOIT DOEN! Dit is een veiligheidsrisico
```

## Performance Standards

### Caching

```python
# Gebruik caching voor dure operaties
from utils.cache import cached

@cached(ttl=3600)  # Cache voor 1 uur (3600 seconden)
async def haal_verrijkte_definitie_op(term: str) -> VerrijkteDefinitie:
    """Haalt definitie op met extra informatie (duurt lang)."""
    # Stap 1: Haal de basis definitie op
    basis = await self.haal_definitie_op(term)
    # Stap 2: Zoek extra informatie op (dit kost veel tijd)
    verrijkingen = await self.haal_verrijkingen_op(basis)
    # Stap 3: Combineer alles in een verrijkte definitie
    return VerrijkteDefinitie(basis, verrijkingen)
```

### Batch Operations

```python
# Correct - Batch operaties voor efficiëntie
async def verwerk_termen(self, termen: List[str]) -> List[Definitie]:
    """Verwerkt meerdere termen tegelijk (snel)."""
    # Maak een lijst van taken die tegelijk uitgevoerd kunnen worden
    taken = [self.genereer_definitie(term) for term in termen]
    # Voer alle taken tegelijk uit (parallel)
    return await asyncio.gather(*taken)

# Incorrect - Sequentiële verwerking (langzaam)
async def verwerk_termen(self, termen: List[str]) -> List[Definitie]:
    """Verwerkt termen één voor één."""
    resultaten = []
    # FOUT: Dit doet elke term na elkaar (traag)
    for term in termen:
        resultaat = await self.genereer_definitie(term)
        resultaten.append(resultaat)
    return resultaten
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

- [ ] Code volgt formatting standards (Black, Ruff)
- [ ] Type hints zijn aanwezig en correct
- [ ] Alle publieke methoden hebben Nederlandse docstrings
- [ ] ALLE code heeft Nederlandse inline commentaar voor niet-programmeurs
- [ ] Complexe logica is extra uitgebreid gedocumenteerd
- [ ] Variabelen, functies en classes hebben Nederlandse namen
- [ ] Tests zijn toegevoegd voor nieuwe functionaliteit
- [ ] Security overwegingen zijn geadresseerd
- [ ] Performance impact is overwogen
- [ ] Geen hardgecodeerde geheimen of credentials
- [ ] Foutafhandeling is passend
- [ ] Code is DRY (Don't Repeat Yourself - Herhaal jezelf niet)

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

## Security Coding Standards

- Geen `bare except`; vang specifieke excepties en geef context.
- Nooit secrets hardcoderen; gebruik `.env`/secret store; log geen secrets/PII.
- Valideer en sanitize alle invoer (XSS/SQLi); gebruik bestaande validator/sanitizer.
- Gebruik TLS; verifieer certificaten standaard.
- Principle of least privilege voor DB/API‑sleutels en service accounts.

## Docstring Stijl en Tools

- Docstrings in Nederlands, Google‑style (Sphinx Napoleon compatibel).
- Documenteer parameters, returnwaarden en uitzonderingen consequent.
- Gebruik type hints als bron voor documentatiegeneratie.

## Versies en Tools (bron van waarheid)

- Python: 3.11+
- Formatter: Black (line‑length 88)
- Linter: Ruff (regels zoals geconfigureerd in `pyproject.toml`)

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
