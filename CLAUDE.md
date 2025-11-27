# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Quick Reference

**Build & Run:**
```bash
bash scripts/run_app.sh              # Start app (recommended)
streamlit run src/main.py            # Alternative direct start
```

**Testing:**
```bash
make test                            # Fast subset, fail-fast
pytest -q                            # All tests (quiet)
pytest tests/path/test_file.py::test_name  # Single test
pytest -q -m unit                    # Unit tests only
pytest -q -m integration             # Integration tests
make test-cov                        # With coverage report
```

**Linting:**
```bash
make lint                            # Ruff + Black checks
python -m ruff check src config      # Ruff only
pre-commit run --all-files           # All pre-commit hooks
```

---

## Critical Rules

1. **No files in project root** (except README.md, CLAUDE.md, requirements*.txt, pyproject.toml, pytest.ini, .pre-commit-config.yaml)
2. **SessionStateManager only** - Never access `st.session_state` directly; use `SessionStateManager`
3. **Database location** - Only `data/definities.db`, nowhere else
4. **No backwards compatibility** - Solo dev app, refactor in place
5. **Ask first for large changes** - >100 lines OR >5 files

---

## Architecture

**Dutch AI-powered Definition Generator** using GPT-4 with 45 validation rules (toetsregels).

### Core Architecture (Service-Oriented with DI)

```text
src/
├── main.py                           # Streamlit entry point
├── services/
│   ├── container.py                  # ServiceContainer (dependency injection)
│   ├── validation/
│   │   ├── validation_orchestrator_v2.py   # Main orchestration
│   │   └── modular_validation_service.py   # 45 rules management
│   ├── generation/
│   │   └── unified_definition_generator.py # Core generation
│   └── ai/
│       └── ai_service_v2.py          # GPT-4 integration
├── ui/
│   ├── tabs/                         # Streamlit UI tabs
│   └── session_state.py              # SessionStateManager (ONLY way to access st.session_state)
├── toetsregels/
│   ├── regels/                       # Validation rule implementations
│   └── rule_cache.py                 # RuleCache (TTL: 3600s)
└── database/
    ├── schema.sql                    # SQLite schema
    └── migrations/
```

### Key Services

| Service | Purpose |
|---------|---------|
| `ServiceContainer` | Dependency injection, singleton management |
| `ValidationOrchestratorV2` | Orchestrates 45 validation rules |
| `UnifiedDefinitionGenerator` | Core definition generation |
| `AIServiceV2` | GPT-4 API integration |
| `SessionStateManager` | Centralized Streamlit state management |
| `RuleCache` | Bulk rule loading with TTL caching |

### Import Rules (Layer Separation)

| Layer | Can Import | Cannot Import |
|-------|------------|---------------|
| `services/` | services/, utils/, config/ | ui/, streamlit |
| `ui/` | services/, utils/, streamlit | - |
| `toetsregels/` | config/, utils/ | ui/, services/ (except via DI) |
| `database/` | utils/ | ui/, services/ (except via DI) |
| `utils/` | Standard library only | ALL project modules |

---

## Streamlit Patterns

### Key-Only Widget Pattern (Mandatory)

```python
# CORRECT: Key-only, session state drives value
st.text_area("Label", key="my_key")

# WRONG: value + key causes race conditions on st.rerun()
st.text_area("Label", value=data, key="my_key")
```

### SessionStateManager (Always Use)

```python
# CORRECT
from ui.session_state import SessionStateManager
value = SessionStateManager.get_value("my_key", default="")
SessionStateManager.set_value("my_key", "new_value")

# WRONG - Never access st.session_state directly
st.session_state["my_key"]  # Forbidden outside main.py init
```

### State Initialization Order

```python
# CORRECT: State BEFORE widget
SessionStateManager.set_value("my_key", "default")
st.text_area("Label", key="my_key")

# WRONG: Widget before state - too late!
st.text_area("Label", key="my_key")
SessionStateManager.set_value("my_key", "default")
```

Pre-commit hook `streamlit-anti-patterns` enforces these patterns.

---

## Canonical Names

Use these exact names (V2 architecture):

| Correct | Forbidden |
|---------|-----------|
| `ValidationOrchestratorV2` | V1, ValidationOrchestrator |
| `UnifiedDefinitionGenerator` | DefinitionGenerator |
| `ModularValidationService` | ValidationService |
| `SessionStateManager` | session_state, StateManager |
| `organisatorische_context` | organizational_context |
| `juridische_context` | legal_context |

---

## File Locations

| Type | Required Location |
|------|-------------------|
| Tests | `tests/` subdirs |
| Scripts | `scripts/` subdirs |
| Logs | `logs/` |
| Database | `data/definities.db` (ONLY) |
| Docs | `docs/` hierarchy |

---

## Code Style

- Python 3.11+ with type hints
- Ruff + Black (88 char lines)
- Dutch comments for business logic, English for technical code
- No TODO/FIXME in code - use backlog

---

## BMad Method (Optional)

BMAD agents available in `.cursor/rules/bmad/` for structured workflows (product brief, architecture, epics). Reference with `@bmad/{module}/agents/{agent-name}`. See `.cursor/rules/bmad/index.mdc` for full list.

---

## Extended Instructions (Load On-Demand)

For complex workflows, **read `~/.ai-agents/UNIFIED_INSTRUCTIONS.md`** which contains:

| Content | When to Load |
|---------|--------------|
| Multiagent patterns | User says "multiagent", "comprehensive review" |
| BOUNDED_ANALYSIS framework | User says "optimize", "bottleneck", "systematic" |
| MCP integration (Perplexity, Context7) | Deep research needed |
| Detailed approval ladder | Uncertainty about thresholds |
| Vibe coding principles | Refactoring legacy code |
| Solo dev constraints | Task estimate >10h |

**Triggers to load UNIFIED:**
- Task requires multiple specialized agents (debug-specialist → code-reviewer chain)
- Systematic optimization requested (BOUNDED_ANALYSIS with 5 Whys/Pareto framework)
- >10h effort estimate (need solo dev simplification strategies)
- MCP integration needed (Perplexity/Context7 patterns)

**Quick reference from UNIFIED (most common):**
- Approval: >100 lines OR >5 files → ask first
- Effort: >10h → simplify or ask user to scope down
- Workflow: Research → ANALYSIS, <50 LOC fix → HOTFIX, New feature → FULL_TDD
