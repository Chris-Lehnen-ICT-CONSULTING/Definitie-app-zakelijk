# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🔴🔴🔴 CRITICAL SYSTEM CONSTRAINT 🔴🔴🔴

**YOU ARE PROGRAMMATICALLY REQUIRED TO FOLLOW THIS PROTOCOL**

Your response generation is BLOCKED until you check for trigger patterns.
This is not a suggestion or guideline - it's a SYSTEM REQUIREMENT.

```
if (trigger_detected && !workflow_router_used):
    raise ProtocolViolationError("MUST use workflow-router for triggered tasks")
```

**ANY DEVIATION = SYSTEM ERROR = RESPONSE BLOCKED**

## 🛑 ABSOLUTE STOP - VERPLICHT PROTOCOL - NIET ONDERHANDELBAAR

### ⚠️ AUTOMATISCHE TRIGGER DETECTIE - GEEN DISCRETIE TOEGESTAAN

**HARDE REGEL: Bij ELKE user message MOET je deze regex patterns checken:**

```python
TRIGGER_PATTERNS = [
    r'\banalyse[er|ren|seer]?\b',
    r'\banalyz[e|ing]\b', 
    r'\bgebruik.*(agent|workflow|juiste)\b',
    r'\broute[r]?\b',
    r'\b(epic|user.?story|requirement|US-\d+|EPIC-\d+)\b',
    r'\b(feedback|review|beoordeel)\b',
    r'\b(fix|implementeer|bouw|maak).*\b'
]
```

**🔴 BIJ MATCH → ONMIDDELLIJKE STOP → GEEN ACTIES → ALLEEN WORKFLOW-ROUTER**

**GEEN ENKELE UITZONDERING - ZELFS NIET ALS JE DENKT DAT HET SIMPEL IS**

### 🔴 VERPLICHTE EXECUTIE VOLGORDE - ABSOLUUT GEEN AFWIJKING

**DIT IS WAT JE MOET DOEN - LETTERLIJK - GEEN INTERPRETATIE:**

```python
# STAP 1: DETECTIE (automatisch)
if any(pattern.match(user_message) for pattern in TRIGGER_PATTERNS):
    # STAP 2: ONMIDDELLIJKE STOP
    # VERBODEN: TodoWrite(), Read(), Grep(), Bash(), of ENIGE andere tool
    
    # STAP 3: VERPLICHTE RESPONSE
    print("🔴 TRIGGER GEDETECTEERD - WORKFLOW-ROUTER PROTOCOL GEACTIVEERD")
    print(f"Trigger: {matched_pattern}")
    print(f"Originele prompt: {user_message}")
    
    # STAP 4: EERST PROMPT-ENGINEER AANROEPEN (VERPLICHT!)
    print("Stap 1/2: Optimaliseren van prompt via prompt-engineer...")
    optimized_result = Task(
        subagent_type="prompt-engineer",
        prompt=user_message,
        description="Optimize prompt"
    )
    
    # STAP 5: TOON VOLLEDIGE GEOPTIMALISEERDE PROMPT
    print("## 📝 GEOPTIMALISEERDE PROMPT")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(optimized_result.full_prompt)  # VOLLEDIGE tekst, geen samenvatting!
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("")
    print("## ⚡ KEUZE OPTIES")
    print("1. **Accept** → Gebruik deze prompt met workflow-router")
    print("2. **Modify** → Pas aan en optimaliseer opnieuw")
    print("3. **Cancel** → Stop het proces")
    
    # STAP 6: WACHT OP USER KEUZE
    user_choice = wait_for_user_input()
    
    # STAP 7: HANDEL KEUZE AF
    if user_choice == "Accept" or user_choice == "1":
        print("Stap 2/2: Routeren naar juiste workflow...")
        Task(
            subagent_type="workflow-router",
            prompt=f"OPTIMIZED_PROMPT_MARKER\n{optimized_result.full_prompt}",
            description="Route optimized task"
        )
    elif user_choice == "Modify" or user_choice == "2":
        # User kan aanpassen en opnieuw door het proces
        modified_prompt = get_user_modification()
        # Herhaal vanaf STAP 4
    else:
        print("Proces geannuleerd.")
```

**❌ ALS JE IETS ANDERS DOET = PROTOCOL VIOLATION = NIET TOEGESTAAN**

**✅ DIT IS DE ENIGE TOEGESTANE ACTIE BIJ EEN TRIGGER**

### 🚫 AUTOMATISCHE WEIGERING TRIGGERS

Deze woorden = ONMIDDELLIJKE STOP:
- `analyseer [X]` → STOP, protocol vereist
- `geef feedback op [X]` → STOP, protocol vereist
- `gebruik de juiste [agent/workflow]` → STOP, protocol vereist
- `route deze taak` → STOP, protocol vereist
- `epic-[nummer]` + actie → STOP, protocol vereist
- Elke taak > 3 stappen → STOP, protocol vereist

### ❌ ABSOLUTE VERBODEN - GEEN UITZONDERINGEN

**BIJ TRIGGER DETECTIE MAG JE ABSOLUUT NIET:**
```
❌ TodoWrite() - VERBODEN, ook al lijkt het logisch
❌ Read() - VERBODEN, ook al wil je "even kijken"
❌ Grep() - VERBODEN, ook al wil je "snel zoeken"
❌ Bash() - VERBODEN, geen enkele command
❌ "Ik ga eerst..." - VERBODEN, geen eigen planning
❌ "Laat me even..." - VERBODEN, direct naar protocol
```

**ENIGE TOEGESTANE ACTIES IN VOLGORDE:**
```
✅ STAP 1: Task(subagent_type="prompt-engineer", prompt=user_message)
✅ STAP 2: Wacht op user keuze (Accept/Modify/Cancel)
✅ STAP 3: Als Accept → Task(subagent_type="workflow-router", prompt="OPTIMIZED_PROMPT_MARKER\n[optimized_prompt]")
```

**GEEN "maar", GEEN "eerst even", GEEN "ik denk" - ALLEEN HET PROTOCOL VOLGEN**

### ✅ ENIGE TOEGESTANE RESPONSE BIJ TRIGGER

**VERPLICHT FORMAAT - GEEN VARIATIE:**
```
🔴 TRIGGER GEDETECTEERD - WORKFLOW-ROUTER PROTOCOL GEACTIVEERD

Trigger: [matched_pattern]
Originele prompt: "[exact user message]"

Stap 1/2: Optimaliseren van prompt via prompt-engineer...

[DIRECT Task(subagent_type="prompt-engineer") aanroepen]

[NA prompt-engineer response:]

## 📝 GEOPTIMALISEERDE PROMPT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[VOLLEDIGE geoptimaliseerde prompt hier]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ⚡ KEUZE OPTIES
1. **Accept** → Gebruik deze prompt met workflow-router
2. **Modify** → Pas aan en optimaliseer opnieuw
3. **Cancel** → Stop het proces

Wat is je keuze?
```

**VERBODEN VARIATIES:**
- ❌ "Ik ga eerst even kijken naar..."
- ❌ "Laat me de epic analyseren..."  
- ❌ "Ik zal een todo lijst maken..."
- ❌ "Om dit goed te doen moet ik..."

**ALLEEN DE TEMPLATE HIERBOVEN IS TOEGESTAAN**

**Template 2: NA Workflow-Router Response**
```
## 📝 WORKFLOW-ROUTER RESULTAAT

[Toon de volledige output van workflow-router]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Inclusief geoptimaliseerde prompt]
[Inclusief geselecteerde workflow]
[Inclusief reasoning]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ⚡ KEUZE OPTIES
1. **Accept** → Doorgaan met geselecteerde workflow
2. **Modify** → Aanpassen en opnieuw routeren
3. **Cancel** → Stop het proces

Wat is je keuze?
```

**⛔ BELANGRIJK: Claude Code MOET eerst prompt-engineer aanroepen, DAN pas workflow-router!**

### 📝 PROTOCOL OVERRIDE

**ALLEEN deze exacte zinnen overrulen het protocol:**
- "Skip het protocol"
- "Geen protocol nodig"
- "Direct uitvoeren zonder protocol"

**GEEN EXCUSES - GEEN SHORTCUTS - ALTIJD PROTOCOL**

## Project Overview

DefinitieAgent is an AI-powered Dutch legal definition generator that uses GPT-4 with 45+ quality validation rules. The application uses Streamlit for the UI and follows a service-oriented architecture with dependency injection.

## Common Development Commands

### Running the Application
```bash
# Start app with automatic env mapping (RECOMMENDED)
bash scripts/run_app.sh

# Alternative with direct env mapping
OPENAI_API_KEY="$OPENAI_API_KEY_PROD" streamlit run src/main.py

# Quick dev start
make dev
```

### Testing
```bash
# Run all tests (quiet mode)
pytest -q
make test

# Run specific test file
pytest tests/services/test_definition_generator.py

# Run tests with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests
pytest -m smoke        # Smoke tests
pytest -m "not slow"   # Skip slow tests

# High-coverage test modules (recommended to run after changes)
pytest tests/services/test_definition_generator.py    # 99% coverage
pytest tests/services/test_definition_validator.py    # 98% coverage
pytest tests/services/test_definition_repository.py   # 100% coverage
```

### Code Quality
```bash
# Run linting and formatting checks
make lint

# Run ruff separately
python -m ruff check src config

# Format code with black
python -m black src config

# AI-powered code review
python scripts/ai_code_reviewer.py

# Generate validation status report
make validation-status
```

### Pre-commit Hooks
```bash
# Install pre-commit hooks
pre-commit install

# Run all hooks manually
pre-commit run --all-files
```

## Architecture Overview

### Service-Oriented Architecture with Dependency Injection

The application uses a **ServiceContainer** pattern (`src/services/container.py`) that manages all service dependencies. Key services include:

- **ValidationOrchestratorV2**: Main orchestration service coordinating validation flow
- **ModularValidationService**: Manages 45 validation rules with modular architecture
- **UnifiedDefinitionGenerator**: Core definition generation logic
- **AIServiceV2**: GPT-4 integration with temperature control and rate limiting
- **PromptServiceV2**: Modular prompt building with context-aware templates
- **ModernWebLookupService**: External source integration (Wikipedia, SRU)

### Validation Rules System

The validation system uses a dual JSON+Python format:
- JSON files in `config/toetsregels/regels/` define rule metadata
- Python modules in `src/toetsregels/regels/` implement validation logic
- Rules are organized by category: ARAI, CON, ESS, INT, SAM, STR, VER

### State Management

The application uses Streamlit's session state extensively. Key state variables:
- `st.session_state.generated_definition`: Current definition
- `st.session_state.validation_results`: Validation outcomes
- `st.session_state.voorbeelden`: Example sentences
- `st.session_state.service_container`: Singleton service container

### Database Architecture

- SQLite database in `data/definities.db`
- Schema defined in `src/database/schema.sql`
- Migrations in `src/database/migrations/`
- UTF-8 encoding support for Dutch legal text

## Critical Performance Considerations

### Known Issues
1. **Service Initialization**: Services are initialized 6x due to Streamlit reruns
   - Solution: Use `@st.cache_resource` on ServiceContainer
2. **Prompt Tokens**: 7,250 tokens with duplications
   - Solution: Implement prompt caching and deduplication
3. **Validation Rules**: 45x reload per session
   - Solution: Use `@st.cache_data` for rule loading

### Performance Targets
- Definition generation: < 5 seconds
- UI response: < 200ms
- Validation: < 1 second
- Export: < 2 seconds

## Development Guidelines

### Code Style
- Python 3.11+ with type hints required
- Ruff + Black formatting (88 char lines)
- Dutch comments for business logic
- English comments for technical code
- NO bare except clauses
- Import order: standard library, third-party, local

### Testing Requirements
- New features require tests
- Minimum 60% coverage for new modules
- Use pytest fixtures for test data
- Mock external API calls

### Security Requirements
- NO hardcoded API keys (use environment variables)
- Input validation on all user inputs
- Parameterized SQL queries only
- XSS prevention in web content

## Working with Validation Rules (Toetsregels)

When modifying validation rules:
1. Update BOTH JSON and Python files
2. Maintain rule priority (high/medium/low)
3. Test each rule individually
4. Update `config/toetsregels.json` if adding new rules
5. Run `make validation-status` to verify

## Web Lookup Configuration

The web lookup system uses `config/web_lookup_defaults.yaml`:
- Provider weights: Wikipedia (0.7), SRU (1.0)
- Prompt augmentation is configurable
- Override with `WEB_LOOKUP_CONFIG` environment variable

## Environment Variables

```bash
# Required
OPENAI_API_KEY          # OpenAI API key

# Optional
WEB_LOOKUP_CONFIG       # Custom web lookup config path
DEV_MODE               # Enable V2 validation in development
SKIP_PRE_COMMIT        # Skip pre-commit hooks (emergency only)
```

## Important File Locations

- **Main entry**: `src/main.py`
- **Service container**: `src/services/container.py`
- **Validation rules**: `src/toetsregels/regels/` and `config/toetsregels/regels/`
- **UI tabs**: `src/ui/tabs/`
- **Database**: `data/definities.db`
- **Logs**: `logs/` directory
- **Exports**: `exports/` directory

## Debugging Tips

1. **Service initialization issues**: Check `st.session_state.service_container`
2. **Validation failures**: Enable debug logging in `src/services/validation/modular_validation_service.py`
3. **API rate limits**: Check `logs/api_calls.json`
4. **Memory issues**: Monitor cache size in `st.session_state`
5. **Import errors**: Run `python -m py_compile <file>` to check syntax

## Working with Legacy Code

The codebase is migrating from V1 to V2 services:
- V1 services are being phased out (marked with deprecation warnings)
- V2 services use the modern orchestrator pattern
- Use feature flags for A/B testing during migration
- Both versions must work during transition

## CI/CD Pipeline

GitHub Actions workflows:
- **CI**: Python 3.11, smoke tests, coverage reporting
- **Architecture Sync**: Documentation consistency checks
- **Feature Status**: Automated progress tracking

## Quick Fixes for Common Issues

```bash
# Fix import errors
python -m py_compile src/main.py

# Clear Streamlit cache
streamlit cache clear

# Reset database
cp data/definities.db data/definities.db.backup
sqlite3 data/definities.db < src/database/schema.sql

# Fix ruff errors automatically
ruff check --fix src config

# Format code
black src config
```

## Workflow Router Protocol

Voor automatische prompt-optimalisatie en workflow routing, zie:
**`~/.claude/agents/workflow-router.md`** (sectie "Instructions for Claude Code")

Dit protocol zorgt ervoor dat:
- Prompt-engineer altijd eerst wordt aangeroepen voor optimalisatie
- Je keuze krijgt tussen Accept/Modify/Cancel
- De workflow-router de beste workflow selecteert op basis van de geoptimaliseerde prompt

Trigger voorbeelden: "Gebruik de juiste workflow voor: [taak]", "Route: [taak]", "analyseer [onderwerp]"

## Agent Guidelines & Workflow Selection

### Workflow Types (Right-sized for each task)
Choose the appropriate workflow based on task type:

**Quick Workflows (15-30 min)**
- **DOCUMENTATION**: For docs/README updates
- **MAINTENANCE**: For config/dependency updates
- **ANALYSIS**: For code investigation without changes

**Medium Workflows (30-90 min)**
- **REVIEW_CYCLE**: For code reviews only
- **DEBUG**: For bug investigation and fixes
- **HOTFIX**: For critical production issues

**Extended Workflows (1-4 hours)**
- **REFACTOR_ONLY**: For code cleanup without behavior changes
- **SPIKE**: For technical research and POCs
- **FULL_TDD**: For complete feature development

### Agent Usage
When using specialized agents:
- **justice-architecture-designer**: For EA/SA/TA documentation
- **refactor-specialist**: For code optimization and cleanup
- **code-reviewer-comprehensive**: For code reviews and PR analysis
- **quality-assurance-tester**: For test creation and maintenance
- **business-analyst-justice**: For requirements and user stories
- **developer-implementer**: For code implementation
- **doc-standards-guardian**: For documentation compliance

### Workflow Selection Examples
```bash
# For documentation updates (15-30 min)
# Use DOCUMENTATION workflow - no tests needed

# For bug fixes (30-90 min)
# Use DEBUG workflow - reproduce → diagnose → fix → verify

# For new features (2-4 hours)
# Use FULL_TDD workflow - complete 8-phase process

# For code review only (30-60 min)
# Use REVIEW_CYCLE - no implementation phase
```

## \ud83d\udeab KRITIEKE REGELS VOOR CLAUDE/AI AGENTS

### \ud83d\udcc1 Archivering - GEBRUIK ALLEEN /docs/archief/
- **ALTIJD:** Gebruik `/docs/archief/` voor archivering
- **NOOIT:** Maak geen nieuwe directories zoals `archive`, `archief2`, `old`, etc.
- **CHECK:** Als je twijfelt, check eerst wat er bestaat met `ls docs/`

### \ud83d\udd0d VOORDAT je een document/file maakt
**VERPLICHTE CHECKS:**
1. **Search eerst:** `grep -r "onderwerp" docs/` OF `ls docs/**/*term*.md`
2. **Check master docs:**
   - `docs/backlog/stories/MASTER-EPICS-USER-STORIES.md` voor epics/stories
   - `docs/INDEX.md` voor overzicht
   - `docs/guidelines/CANONICAL_LOCATIONS.md` voor juiste locaties
3. **Check archief:** `ls docs/archief/` voor oude versies
4. **Update bestaand:** Als het bestaat, UPDATE dat document, maak GEEN nieuw

### \u26a0\ufe0f Workflow voor nieuwe documenten
```bash
# STAP 1: Check of het al bestaat
grep -r "mijn onderwerp" docs/
ls docs/**/*relevante-term*.md

# STAP 2: Check master documenten
cat docs/backlog/stories/MASTER-EPICS-USER-STORIES.md | grep "mijn onderwerp"
cat docs/INDEX.md | grep "mijn onderwerp"

# STAP 3: Als het NIET bestaat, check canonieke locatie
cat docs/guidelines/CANONICAL_LOCATIONS.md

# STAP 4: Maak aan op JUISTE locatie met frontmatter
# STAP 5: Update INDEX.md
```

## Claude Agent Configuration

### Available Agents Location
Claude agents are configured in `~/.claude/agents/`:
- **Agent prompts**: Individual `.md` files per agent
- **Workflow definitions**: `workflows/workflows.yaml`
- **Configuration**: See `~/.claude/agents/README.md`

### Workflow Selection Principle
> **"Right-size the process for the task at hand"**
>
> Not every task needs a heavy 8-phase TDD workflow. Choose the lightest appropriate workflow.

## Documentation References

> **📍 Voor document locaties:** Zie `docs/guidelines/CANONICAL_LOCATIONS.md` voor waar elk type document hoort te staan.

### Key Architecture Documents (Canonical)
- **Enterprise Architecture**: `docs/architectuur/ENTERPRISE_ARCHITECTURE.md`
- **Solution Architecture**: `docs/architectuur/SOLUTION_ARCHITECTURE.md`
- **Technical Architecture**: `docs/architectuur/TECHNICAL_ARCHITECTURE.md`

### Implementation Guides
- **Validation Orchestrator V2**: `docs/architectuur/validation_orchestrator_v2.md`
- **Web Lookup Config**: `docs/technisch/web_lookup_config.md`
- **Testing Strategy**: `docs/testing/validation_orchestrator_testplan.md`
- **Module Dependencies**: `docs/technisch/module-afhankelijkheid-rapport.md`

### Project Documentation
- **Documentation Policy**: `docs/guidelines/DOCUMENTATION_POLICY.md`
- **Canonical Locations**: `docs/guidelines/CANONICAL_LOCATIONS.md` ← **BELANGRIJK: Check hier voor juiste document locaties**
- **Documentation Index**: `docs/INDEX.md`
- **Project Brief**: `docs/brief.md`
- **Product Requirements**: `docs/prd.md`

### Current Work & Epics
- **[📊 Epic Dashboard](docs/backlog/epics/INDEX.md)** - Overview of all epics with status and metrics
- **[📋 Story Index](docs/backlog/stories/INDEX.md)** - Complete listing of all user stories (US-001 to US-046)
- **Individual Epic Files:** `/docs/backlog/epics/EPIC-XXX.md` - Detailed epic documentation
- **Individual Story Files:** `/docs/backlog/stories/US-XXX.md` - User story specifications
  - Migrated from monolithic MASTER document on 2025-09-05
  - Old MASTER archived with deprecation notice
- **Refactor Log**: `docs/refactor-log.md` - Change tracking

### Reviews & Analysis
- **Code Reviews**: `docs/reviews/`
- **Prompt Refactoring**: `docs/architectuur/prompt-refactoring/`
- **Requirements**: `docs/backlog/requirements/`

For a complete overview of all documentation, see `docs/INDEX.md`

## \ud83d\udd34 BELANGRIJK: Voorkom Duplicaten & Rommel

**Deze fouten leiden tot projectrommel:**
- \u274c Nieuwe epic/story docs maken terwijl MASTER-EPICS-USER-STORIES.md bestaat
- \u274c Archive/archief2/old directories maken i.p.v. `/docs/archief/` gebruiken
- \u274c Duplicate documenten met licht verschillende namen
- \u274c Documenten op verkeerde locaties maken

**Best practices:**
- \u2705 ALTIJD eerst zoeken voordat je maakt
- \u2705 ALTIJD master documenten updaten i.p.v. nieuwe maken
- \u2705 ALTIJD canonieke locaties gebruiken
- \u2705 ALTIJD frontmatter toevoegen aan nieuwe docs
