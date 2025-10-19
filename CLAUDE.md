# CLAUDE.md

Dit bestand biedt richtlijnen aan Claude Code bij het werken met code in deze repository.

## 🎯 Agent Instruction Hierarchy & Precedence

### Instruction Priority (Highest → Lowest)

1. **`~/.ai-agents/UNIFIED_INSTRUCTIONS.md`** - Cross-project generieke regels (PRIMAIR)
2. **`CLAUDE.md` (dit document)** - DefinitieAgent project-specifieke regels
3. **`~/.ai-agents/quality-gates.yaml`** - Forbidden patterns & quality checks
4. **`~/.ai-agents/agent-mappings.yaml`** - Agent name translations
5. **`AGENTS.md`** - BMad Method workflows (alleen voor BMad agents)

### Werkwijze
- **ALTIJD begin met UNIFIED_INSTRUCTIONS.md** voor basis regels
- **Gebruik CLAUDE.md** voor DefinitieAgent-specifieke patterns
- **Bij conflicten**: UNIFIED > CLAUDE.md > quality-gates > mappings
- **Check preflight**: Run `~/.ai-agents/preflight-checks.sh` voor wijzigingen

### Agent Name Mapping (Cross-Platform)

| Workflow Role | TDD Workflow | Codex | Claude Code | BMad Method |
|---------------|--------------|-------|-------------|-------------|
| **Documentation** | doc-auditor | Documentor | Analysis mode | bmad-analyst |
| **Architecture** | architect / justice-architecture-designer | Architect | Design mode | bmad-architect |
| **Development** | dev / implementor | Developer | Implementation | bmad-dev |
| **Code Quality** | code-architect | Refactor Agent | Review mode | bmad-reviewer |
| **Process** | process-guardian | QA/Process | Workflow mode | bmad-pm |
| **Testing** | test-engineer | Test Engineer | Test mode | bmad-tester |

**Gebruik deze mapping bij:**
- Handoffs tussen agents
- Cross-platform documentatie
- Workflow referenties

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

### 🚫 VERBODEN PATTERNS - ANTI-PATTERNS

#### GOD OBJECT / CATCH-ALL HELPERS
- **VERBODEN: `dry_helpers.py` of vergelijkbare "alles-in-één" utility modules**
- **PROBLEEM**: DRY principe ≠ alles in één bestand stoppen
- **GEVOLG**: Onduidelijke verantwoordelijkheden, verborgen dependencies, moeilijk te testen
- **OPLOSSING**: Splits naar specifieke modules met duidelijke verantwoordelijkheden:
  - `utils/type_helpers.py` - Voor type conversies (`ensure_list`, `ensure_dict`)
  - `utils/dict_helpers.py` - Voor dictionary operations (`safe_dict_get`)
  - `utils/validation_helpers.py` - Voor validatie utilities
  - GEEN vage "helpers" modules!

#### SESSION STATE MANAGEMENT
- **REGEL**: `SessionStateManager` is de ENIGE module die `st.session_state` mag aanraken
- **VERBODEN**: Directe `st.session_state` toegang in andere modules
- **VERBODEN**: Session state functies in utility modules
- **GEVOLG**: Circulaire dependencies, recursie problemen, inconsistente state management
- **OPLOSSING**: ALLE session state toegang via `SessionStateManager.get_value()` / `set_value()`


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

**Caching Strategie (US-202):**
- **RuleCache** (`src/toetsregels/rule_cache.py`): Bulk loading met `@cached` decorator (TTL: 3600s)
- **CachedToetsregelManager** (`src/toetsregels/cached_manager.py`): Singleton manager met RuleCache
- **loader.py**: Gebruikt `get_cached_toetsregel_manager()` voor 1x loading i.p.v. 10x
- **Performance**: 77% sneller, 81% minder memory voor regel loading

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

### Opgeloste Problemen ✅

1. **Validatieregels**: ~~45x herladen per sessie~~ → ✅ **OPGELOST** (US-202, 2025-10-06)
   - Was: 10x laden tijdens startup (900% overhead)
   - Nu: 1x laden + cache reuse via `CachedToetsregelManager` en `RuleCache`
   - Verbetering: 77% sneller, 81% minder memory
   - Zie: `docs/reports/toetsregels-caching-fix.md`

### Bekende Problemen (Open)

1. ~~**Service Initialisatie**: Services worden 2-3x geïnitialiseerd door Streamlit reruns~~ ✅ **OPGELOST (US-202, Oct 7 2025)**
   - Was: ServiceContainer #1 (cached) + #2 (custom config)
   - Oorzaak: Dubbele cache mechanismen zonder cache_key unificatie
   - Nu: Single singleton met unified cache_key (commits `c2c8633c`, `49848881`)
   - Zie: `docs/analyses/DOUBLE_CONTAINER_ANALYSIS.md`

2. ~~**PromptOrchestrator**: 2x initialisatie met 16 modules elk~~ ✅ **OPGELOST (US-202, Oct 7 2025)**
   - Was: 2x initialisatie door duplicate container initialization
   - Oorzaak: PATH 2 was ServiceContainer duplication (fixed by `c2c8633c`, `49848881`)
   - Nu: 1x initialization tijdens app startup
   - Bewijs: Log analysis Oct 7, 2025
   - Zie: `docs/reports/prompt-orchestrator-duplication-analysis.md`

3. **Prompt Tokens**: 7.250 tokens met duplicaties
   - Oplossing: Implementeer prompt caching en deduplicatie (nog niet geïmplementeerd)

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

## CI/CD Pipeline & GitHub Workflow Management

### 🔄 Systematische Aanpak voor CI/CD Fixes

**Principe:** Behandel CI failures als technical debt met prioritering en fasering

**Proces (zie `docs/analyses/CI_FAILURES_ANALYSIS.md`):**

1. **Analyse Fase**
   - Documenteer alle CI failures systematisch
   - Categoriseer per priority: HIGH (security, core), MEDIUM (quality), LOW (docs)
   - Identificeer pre-existing vs nieuwe issues
   - Schat effort per fix (uren)

2. **Prioritering & Planning**
   - **Phase 1 (Week 1):** Security (gitleaks, pip-audit) - KRITIEK
   - **Phase 2 (Week 1-2):** Core tests & compatibility - BELANGRIJK  
   - **Phase 3 (Week 2):** Quality gates - NICE TO HAVE
   - **Phase 4 (Week 2-3):** Documentation & non-blocking - OPTIONEEL

3. **Systematisch Fixen**
   - Werk per fase, niet random
   - Fix related issues samen (bijv. alle script paths in één PR)
   - Update analysis document met progress
   - Commit messages met context: `fix(security): ...`, `fix(ci): ...`

4. **Documentatie & Preventie**
   - Update `CI_FAILURES_ANALYSIS.md` met completed phases
   - Documenteer lessons learned in `GITHUB_BEST_PRACTICES.md`
   - Implementeer preventieve maatregelen (Dependabot, branch protection)
   - Track metrics (% workflows passing, avg CI time)

### 📋 GitHub Best Practices Framework

**Document:** `docs/analyses/GITHUB_BEST_PRACTICES.md`

**Quick Wins (Do First):**
1. Branch protection voor `main` (30 min)
2. Dependabot setup (20 min) ✅ DONE
3. Issue templates (1 uur) ✅ DONE
4. Auto-labeling (10 min)

**Prioriteiten:**
- 🔴 HIGH: Branch protection, required status checks, Dependabot
- 🟡 MEDIUM: Issue templates, PR automation, workflow optimization
- 🟢 LOW: Release automation, project boards, advanced metrics

**Success Metrics:**
- % workflows passing (target: 80%+)
- Average CI time (target: < 5 min)
- Time to patch vulnerabilities (target: < 7 days)
- PR size (target: < 500 lines)

### 🤖 Geautomatiseerde Workflows

**Dependabot:** `.github/dependabot.yml`
- Weekly updates (Maandag 09:00 Python, 10:00 GitHub Actions)
- Grouped updates voor efficient review
- Auto-assign naar reviewer
- Conventional commits: `build(deps):` / `ci(deps):`

**Issue Templates:** `.github/ISSUE_TEMPLATE/`
- Bug reports (structured YAML)
- Feature requests (met impact assessment)
- Template chooser configuration

**GitHub Actions:**
- **CI**: Python 3.11, smoke tests, coverage rapportage
- **Security**: Gitleaks, pip-audit (REQUIRED to pass)
- **Quality Gates**: Pre-commit, linting, pattern detection
- **Architecture Sync**: Documentatie consistentie checks
- **Feature Status**: Geautomatiseerde voortgang tracking

### 🎯 CI/CD Checklist voor Nieuwe Features

**Voor elke nieuwe feature/fix:**
- [ ] Branch protection configured (main branch)
- [ ] Required status checks defined (Security, CI)
- [ ] PR template gebruikt
- [ ] Conventional commits (`feat:`, `fix:`, `docs:`, `ci:`)
- [ ] Tests toegevoegd/updated
- [ ] CI passing before merge
- [ ] Security scans clean
- [ ] Documentation updated

**Bij CI failures:**
- [ ] Check `docs/analyses/CI_FAILURES_ANALYSIS.md` voor bekende issues
- [ ] Determine: pre-existing of nieuwe issue?
- [ ] Pre-existing → Add to backlog, not blocking
- [ ] Nieuwe issue → Fix immediately, don't merge broken CI
- [ ] Update analysis document met nieuwe findings

### 📚 Belangrijke CI/CD Documenten

- **`docs/analyses/CI_FAILURES_ANALYSIS.md`** - Complete CI failures analyse & roadmap
- **`docs/analyses/GITHUB_BEST_PRACTICES.md`** - GitHub optimization guide
- **`.github/dependabot.yml`** - Dependency update automation
- **`.github/ISSUE_TEMPLATE/`** - Issue templates voor consistentie
- **`.github/workflows/`** - All CI/CD workflow definitions

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
