# CLAUDE.md - DefinitieAgent

> **EXTENSIE** op `~/.claude/CLAUDE.md` (moeder)  
> Definieer hier ALLEEN project-specifieke zaken

---

## Project Info

| Item | Waarde |
|------|--------|
| **Key** | DEF |
| **Repo** | github.com/Chris-Lehnen-ICT-CONSULTING/Definitie-app-zakelijk |
| **Linear Team** | DEF |
| **Doel** | Dutch AI-powered Definition Generator voor overheidsorganisaties |

---

## Tech Stack

| Component | Technologie |
|-----------|-------------|
| **Taal** | Python 3.11+ |
| **Framework** | Streamlit |
| **AI** | GPT-4 (OpenAI API) |
| **Database** | SQLite (`data/definities.db`) |
| **Testing** | pytest |
| **Linting** | Ruff + Black (88 char) |

---

## Quick Reference

### Build & Run
```bash
bash scripts/run_app.sh              # Start app (aanbevolen)
streamlit run src/main.py            # Alternatief
```

### Testing
```bash
make test                            # Fast subset, fail-fast
pytest -q                            # Alle tests
pytest tests/path/test_file.py::test_name  # Enkele test
pytest -q -m unit                    # Unit tests only
pytest -q -m integration             # Integration tests
make test-cov                        # Met coverage
```

### Linting
```bash
make lint                            # Ruff + Black checks
python -m ruff check src config      # Ruff only
pre-commit run --all-files           # Alle pre-commit hooks
```

### Prompt Generation
```bash
prompt-forge forge "idee" -r         # Multi-agent reviewed (aanbevolen)
prompt-forge forge "idee" -c "ctx"   # Met extra context
prompt-forge re-review               # Re-review bestaande prompt
```

---

## Kritieke Regels (Project-Specifiek)

1. **Geen bestanden in project root** - Alleen: README.md, CLAUDE.md, requirements*.txt, pyproject.toml, pytest.ini, .pre-commit-config.yaml
2. **SessionStateManager ONLY** - Nooit `st.session_state` direct aanspreken
3. **Database locatie** - Alleen `data/definities.db`, nergens anders
4. **Geen backwards compatibility** - Solo dev app, refactor in place

---

## Prompt-First Workflow

Bij taken die matchen op: **analyseer, review, implementeer, fix** → vraag eerst:

```
Wil je dat ik eerst een gestructureerde prompt genereer voor deze taak?
- Ja: prompt-forge forge "<taak>" -r
- Nee: Direct uitvoeren
- Ja + Uitvoeren: Beide
```

**Skip toegestaan bij:** <10 regels, 1 bestand, duidelijke oplossing.

---

## Architectuur

```
src/
├── main.py                           # Streamlit entry point
├── services/
│   ├── container.py                  # ServiceContainer (DI)
│   ├── validation/
│   │   ├── validation_orchestrator_v2.py   # 45 toetsregels orchestratie
│   │   └── modular_validation_service.py   # Rule management
│   ├── generation/
│   │   └── unified_definition_generator.py # Core generation
│   └── ai/
│       └── ai_service_v2.py          # GPT-4 integration
├── ui/
│   ├── tabs/                         # Streamlit UI tabs
│   └── session_state.py              # SessionStateManager
├── toetsregels/
│   ├── regels/                       # 45 validation rule implementations
│   └── rule_cache.py                 # RuleCache (TTL: 3600s)
└── database/
    ├── schema.sql                    # SQLite schema
    └── migrations/
```

### Key Services

| Service | Doel |
|---------|------|
| `ServiceContainer` | Dependency injection, singleton management |
| `ValidationOrchestratorV2` | Orchestreert 45 toetsregels |
| `UnifiedDefinitionGenerator` | Core definitie generatie |
| `AIServiceV2` | GPT-4 API integratie |
| `SessionStateManager` | Gecentraliseerde Streamlit state |
| `RuleCache` | Bulk rule loading met TTL caching |

### Layer Separation

| Layer | Mag Importeren | Mag NIET Importeren |
|-------|----------------|---------------------|
| `services/` | services/, utils/, config/ | ui/, streamlit |
| `ui/` | services/, utils/, streamlit | - |
| `toetsregels/` | config/, utils/ | ui/, services/ |
| `database/` | utils/ | ui/, services/ |
| `utils/` | Standard library only | ALLES |

---

## Streamlit Patterns

### Key-Only Widget Pattern (Verplicht)
```python
# GOED: Key-only, session state drives value
st.text_area("Label", key="my_key")

# FOUT: value + key veroorzaakt race conditions
st.text_area("Label", value=data, key="my_key")
```

### SessionStateManager (Altijd Gebruiken)
```python
# GOED
from ui.session_state import SessionStateManager
value = SessionStateManager.get_value("my_key", default="")
SessionStateManager.set_value("my_key", "new_value")

# FOUT - Nooit st.session_state direct
st.session_state["my_key"]  # Verboden
```

---

## Canonical Names (V2 Architectuur)

| Correct | Verboden |
|---------|----------|
| `ValidationOrchestratorV2` | V1, ValidationOrchestrator |
| `UnifiedDefinitionGenerator` | DefinitionGenerator |
| `ModularValidationService` | ValidationService |
| `SessionStateManager` | session_state, StateManager |
| `organisatorische_context` | organizational_context |
| `juridische_context` | legal_context |

---

## Bestandslocaties

| Type | Verplichte Locatie |
|------|--------------------|
| Tests | `tests/` subdirs |
| Scripts | `scripts/` subdirs |
| Logs | `logs/` |
| Database | `data/definities.db` (ENIGE) |
| Docs | `docs/` hierarchy |

---

## Domein Kennis

### Wat is DefinitieAgent?
Een AI-tool voor Nederlandse overheidsorganisaties om juridische definities te genereren en valideren tegen **45 toetsregels** (validation rules).

### Belangrijke Concepten
- **Toetsregels** - 45 validatieregels voor definitiekwaliteit
- **Organisatorische context** - Context van de organisatie die de definitie gebruikt
- **Juridische context** - Wettelijke context waarin de definitie valt

---

## Linear MCP Quirks

| Tool | Issue | Workaround |
|------|-------|------------|
| `linear_bulk_update_issues` | Array van IDs faalt | Call met single-item array per issue |

**State IDs (DEF team):**
- Done: `da2a38d2-e9cb-4b62-b033-f8c80cb0a2f9`
- In Progress: `d6b9b0ac-7e60-495c-8c9e-5389de5fd000`
- Backlog: `0ae3e1f7-cf4c-4421-8d4c-a199823897f8`

---

## Extended Instructions

Voor complexe workflows, laad `~/.ai-agents/UNIFIED_INSTRUCTIONS.md` bij:
- Multiagent patterns
- BOUNDED_ANALYSIS framework
- MCP integration (Perplexity, Context7)

---

*Laatste update: januari 2025*  
*Extendeert: ~/.claude/CLAUDE.md (BMAD v2)*
