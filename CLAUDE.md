# CLAUDE.md

Dit bestand biedt richtlijnen aan Claude Code bij het werken met code in deze repository.

## 🎯 BELANGRIJKE UPDATE: Unified Agent Instructions

**Voor geharmoniseerde werking met Codex, volg ook:**
- **Primaire instructies**: `~/.ai-agents/UNIFIED_INSTRUCTIONS.md` (LEES DIT EERST!)
- **Kwaliteitsregels**: `~/.ai-agents/quality-gates.yaml` (forbidden patterns)
- **Tool mappings**: `~/.ai-agents/agent-mappings.yaml` (Claude ↔ Codex)
- **Preflight checks**: `~/.ai-agents/preflight-checks.sh` (run voor wijzigingen)

De unified instructions bevatten:
- ✅ Approval Ladder (wanneer toestemming vragen)
- 🚫 Forbidden Patterns (wat NOOIT te doen)
- 🔄 Workflow Selection (welke aanpak wanneer)
- 📝 Naming Conventions (juiste namen gebruiken)

**Bij conflicten**: Unified instructions > Dit document

## Project Overzicht

DefinitieAgent is een AI-gestuurde Nederlandse juridische definitiegenerator die GPT-4 gebruikt met 45+ kwaliteitsvalidatieregels. De applicatie gebruikt Streamlit voor de UI en volgt een service-georiënteerde architectuur met dependency injection.

## 📁 BACKLOG STRUCTUUR

**Voor de volledige backlog structuur regels:**
- EPIC → US-XXX → BUG-XXX hiërarchie
- ID uniekheid vereisten
- Directory structuur

**➡️ Zie:**
- `docs/guidelines/CANONICAL_LOCATIONS.md` voor backlog structuur
- `~/.ai-agents/UNIFIED_INSTRUCTIONS.md` voor naming conventions

## 🚫 KRITIEKE REGELS VOOR CLAUDE/AI

### 🔴 PROJECT ROOT - STRIKT BELEID

**NOOIT bestanden in project root plaatsen, behalve:**
- README.md, CONTRIBUTING.md, CLAUDE.md
- requirements.txt, requirements-dev.txt
- Config files: pyproject.toml, pytest.ini, .pre-commit-config.yaml

**VERBODEN in root - ALTIJD verplaatsen naar:**
- `test_*.py` → `tests/` (gebruik subdirs: unit/, integration/, smoke/, debug/)
- `*.sh` scripts → `scripts/` (gebruik subdirs: maintenance/, monitoring/, testing/)
- `*.log` files → `logs/` (archiveer oude logs in logs/archive/YYYY-MM/)
- `*.db` files → `data/` (oude databases naar data/old_databases/)
- `HANDOVER*.md` → `docs/archief/handovers/`
- `*PLAN*.md` → `docs/planning/`
- `*REPORT*` → `docs/reports/`

**Bij twijfel:** Check `~/.ai-agents/quality-gates.yaml` sectie "forbidden_locations"

### ⚠️ REFACTOREN, GEEN BACKWARDS COMPATIBILITY

- **🔴 GEEN BACKWARDS COMPATIBILITY CODE**
- **Dit is een single-user applicatie, NIET in productie**
- **REFACTOR code met behoud van businesskennis en logica**
- **Analyseer eerst wat code doet voordat je vervangt**
- **Extraheer businessregels en validaties tijdens refactoring**
- **Geen feature flags, migratiepaden of deprecation warnings**
- **Focus op: code verbeteren, NIET op compatibiliteit**
- **Business logica documenteren tijdens refactoring proces**


### 📁 Document & File Management

**Voor alle regels rondom:**
- Archivering → Gebruik `/docs/archief/`
- Document duplicatie preventie
- Approval requirements voor file operations

**➡️ Zie:** `~/.ai-agents/UNIFIED_INSTRUCTIONS.md` sectie "FORBIDDEN PATTERNS" en "APPROVAL LADDER"


## Veelgebruikte Development Commando's

### Applicatie Starten

```bash
# Start app met automatische env mapping (AANBEVOLEN)
bash scripts/run_app.sh

# Alternatief met directe env mapping
OPENAI_API_KEY="$OPENAI_API_KEY_PROD" streamlit run src/main.py

# Snelle dev start
make dev
```

### Testen

```bash
# Draai alle tests (stille modus)
pytest -q
make test

# Draai specifiek testbestand
pytest tests/services/test_definition_generator.py

# Draai tests met coverage
pytest --cov=src --cov-report=html

# Draai specifieke test categorieën
pytest -m unit          # Alleen unit tests
pytest -m integration   # Integratie tests
pytest -m smoke        # Smoke tests
pytest -m "not slow"   # Sla trage tests over

# Hoge-coverage test modules (aanbevolen na wijzigingen)
pytest tests/services/test_definition_generator.py    # 99% coverage
pytest tests/services/test_definition_validator.py    # 98% coverage
pytest tests/services/test_definition_repository.py   # 100% coverage
```

### Code Kwaliteit

```bash
# Draai linting en formatting checks
make lint

# Draai ruff apart
python -m ruff check src config

# Formatteer code met black
python -m black src config

# AI-gestuurde code review
python scripts/ai_code_reviewer.py

# Genereer validatie status rapport
make validation-status
```

### Pre-commit Hooks

```bash
# Installeer pre-commit hooks
pre-commit install

# Draai alle hooks handmatig
pre-commit run --all-files
```

## Architectuur Overzicht

### Service-Georiënteerde Architectuur met Dependency Injection

De applicatie gebruikt een **ServiceContainer** patroon (`src/services/container.py`) dat alle service dependencies beheert. Belangrijke services:

- **ValidationOrchestratorV2**: Hoofd orchestratie service die validatie flow coördineert
- **ModularValidationService**: Beheert 45 validatieregels met modulaire architectuur
- **ApprovalGatePolicy (EPIC-016)**: Centrale policy voor validatie‑gate bij Vaststellen (mode/drempels/vereiste velden); UI‑beheerbaar
- **UnifiedDefinitionGenerator**: Core definitie generatie logica
- **AIServiceV2**: GPT-4 integratie met temperatuur controle en rate limiting
- **PromptServiceV2**: Modulaire prompt building met context-aware templates
- **ModernWebLookupService**: Externe bron integratie (Wikipedia, SRU)

### Validatieregels Systeem

Het validatiesysteem gebruikt een duaal JSON+Python formaat:

- JSON bestanden in `config/toetsregels/regels/` definiëren regel metadata
- Python modules in `src/toetsregels/regels/` implementeren validatie logica
- Regels zijn georganiseerd per categorie: ARAI, CON, ESS, INT, SAM, STR, VER

### State Management

De applicatie gebruikt Streamlit's session state uitgebreid. Belangrijke state variabelen:

- `st.session_state.generated_definition`: Huidige definitie
- `st.session_state.validation_results`: Validatie uitkomsten
- `st.session_state.voorbeelden`: Voorbeeld zinnen
- `st.session_state.service_container`: Singleton service container
- Configuratie (EPIC‑016): Gate‑policy, validatieregels en contextopties worden centraal beheerd (DB/config) en via DI gelezen; wijzigingen zijn auditbaar en kunnen via UI worden aangepast.

### Database Architectuur

- SQLite database in `data/definities.db`
- Schema gedefinieerd in `src/database/schema.sql`
- Migraties in `src/database/migrations/`
- UTF-8 encoding ondersteuning voor Nederlandse juridische tekst
 - Enig toegestaan actief pad: `data/definities.db` (geen DB in root of elders)
 - Initialiseer/migreer via `schema.sql` en `src/database/migrate_database.py`
 - Verwijder stray `*.db`, `*.db-shm`, `*.db-wal` buiten `data/`
 - Fallback CREATE in code is een noodpad; gebruik primair `schema.sql`

## Kritieke Performance Overwegingen

### Bekende Problemen

1. **Service Initialisatie**: Services worden 6x geïnitialiseerd door Streamlit reruns
   - Oplossing: Gebruik `@st.cache_resource` op ServiceContainer
2. **Prompt Tokens**: 7.250 tokens met duplicaties
   - Oplossing: Implementeer prompt caching en deduplicatie
3. **Validatieregels**: 45x herladen per sessie
   - Oplossing: Gebruik `@st.cache_data` voor regel laden

### Performance Doelen

- Definitie generatie: < 5 seconden
- UI respons: < 200ms
- Validatie: < 1 seconde
- Export: < 2 seconden

## Development Richtlijnen

### Code Stijl

- Python 3.11+ met type hints verplicht
- Ruff + Black formatting (88 karakter regels)
- Nederlandse commentaren voor business logica
- Engelse commentaren voor technische code
- GEEN kale except clausules
- Import volgorde: standard library, third-party, lokaal

### Test Vereisten

- Nieuwe features vereisen tests
- Minimum 60% coverage voor nieuwe modules
- Gebruik pytest fixtures voor test data
- Mock externe API calls

### Security Vereisten

- GEEN hardcoded API keys (gebruik environment variabelen)
- Input validatie op alle gebruiker inputs
- Alleen geparametriseerde SQL queries
- XSS preventie in web content

## Werken met Validatieregels (Toetsregels)

Bij het wijzigen van validatieregels:

1. Update ZOWEL JSON als Python bestanden
2. Behoud regel prioriteit (high/medium/low)
3. Test elke regel individueel
4. Update `config/toetsregels.json` bij toevoegen nieuwe regels
5. Draai `make validation-status` ter verificatie

## Web Lookup Configuratie

Het web lookup systeem gebruikt `config/web_lookup_defaults.yaml`:

- Provider gewichten: Wikipedia (0.7), SRU (1.0)
- Prompt augmentatie is configureerbaar
- Override met `WEB_LOOKUP_CONFIG` environment variabele

## Environment Variabelen

```bash
# Verplicht
OPENAI_API_KEY          # OpenAI API key

# Optioneel
WEB_LOOKUP_CONFIG       # Custom web lookup config pad
DEV_MODE               # Schakel V2 validatie in tijdens development
SKIP_PRE_COMMIT        # Sla pre-commit hooks over (alleen noodgevallen)
```

## Belangrijke Bestandslocaties

- **Main entry**: `src/main.py`
- **Service container**: `src/services/container.py`
- **Validatieregels**: `src/toetsregels/regels/` en `config/toetsregels/regels/`
- **UI tabs**: `src/ui/tabs/`
- **Database**: `data/definities.db`
- **Logs**: `logs/` directory
- **Exports**: `exports/` directory

## Debugging Tips

1. **Service initialisatie problemen**: Check `st.session_state.service_container`
2. **Validatie fouten**: Schakel debug logging in bij `src/services/validation/modular_validation_service.py`
3. **API rate limits**: Check `logs/api_calls.json`
4. **Geheugen problemen**: Monitor cache grootte in `st.session_state`
5. **Import errors**: Draai `python -m py_compile <file>` om syntax te checken

## Werken met Legacy Code

Refactor, geen backwards compatibility:

- Geen feature flags of parallelle V1/V2 paden
- Verwijder verouderde paden zodra het nieuwe pad klaar is
- Behoud en documenteer businesslogica tijdens refactor

## CI/CD Pipeline

GitHub Actions workflows:

- **CI**: Python 3.11, smoke tests, coverage rapportage
- **Architecture Sync**: Documentatie consistentie checks
- **Feature Status**: Geautomatiseerde voortgang tracking

## Snelle Fixes voor Veelvoorkomende Problemen

```bash
# Fix import errors
python -m py_compile src/main.py

# Clear Streamlit cache
streamlit cache clear

# Reset database
cp data/definities.db data/definities.db.backup
sqlite3 data/definities.db < src/database/schema.sql

# Fix ruff errors automatisch
ruff check --fix src config

# Formatteer code
black src config
```

## Documentatie Referenties

> **📍 Voor document locaties:** Zie `docs/guidelines/CANONICAL_LOCATIONS.md` voor waar elk type document hoort te staan.

### Belangrijke Architectuur Documenten (Canoniek)

- **Enterprise Architectuur**: `docs/architectuur/ENTERPRISE_ARCHITECTURE.md`
- **Solution Architectuur**: `docs/architectuur/SOLUTION_ARCHITECTURE.md`
- **Technische Architectuur**: `docs/architectuur/TECHNICAL_ARCHITECTURE.md`

### Implementatie Handleidingen

- **Validation Orchestrator V2**: `docs/architectuur/validation_orchestrator_v2.md`
- **Web Lookup Config**: `docs/technisch/web_lookup_config.md`
- **Test Strategie**: `docs/testing/validation_orchestrator_testplan.md`
- **Module Afhankelijkheden**: `docs/technisch/module-afhankelijkheid-rapport.md`

### Project Documentatie

- **Documentatie Beleid**: `docs/guidelines/DOCUMENTATION_POLICY.md`
- **Canonieke Locaties**: `docs/guidelines/CANONICAL_LOCATIONS.md` ← **BELANGRIJK: Check hier voor juiste document locaties**
- **Documentatie Index**: `docs/INDEX.md`
- **Project Brief**: `docs/brief.md`
- **Product Requirements**: `docs/prd.md`

### Huidig Werk & Epics

- Centrale Portal: `docs/portal/index.html` (zoek, filter, planning, requirements)
- Individuele Epic: `docs/backlog/EPIC-XXX/EPIC-XXX.md`
- Individuele Story: `docs/backlog/EPIC-XXX/US-XXX/US-XXX.md`
- Bugs per Story: `docs/backlog/EPIC-XXX/US-XXX/BUG-XXX/BUG-XXX.md`
- Refactor Log: `docs/refactor-log.md`

### Reviews & Analyses

- **Code Reviews**: `docs/reviews/`
- **Prompt Refactoring**: `docs/architectuur/prompt-refactoring/`
- **Requirements**: `docs/backlog/requirements/`

Voor een compleet overzicht van alle documentatie, zie `docs/INDEX.md`
