# 🚀 What I'm Working On

**Last Updated**: 2025-10-07

## Current Task
- [ ] Ship EPIC-016 (Beheer & Configuratie Console)

## Quick Navigation - Architecture Reference

### Core Features (Where Things Live)

| Feature | Primary File | Line/Section |
|---------|-------------|--------------|
| **Validation** | `src/services/validation/modular_validation_service.py` | Core validation logic |
| **Generation** | `src/services/orchestrators/definition_orchestrator_v2.py` | Definition generation flow |
| **Prompt Building** | `src/services/prompts/prompt_service_v2.py` | Prompt orchestration |
| **Ontology Classification** | `src/services/classification/ontology_classifier.py` | UFO classification |
| **UI Entry Point** | `src/ui/tabbed_interface.py` | Main Streamlit app |
| **Database** | `src/database/definitie_repository.py` | Data persistence |
| **Service Container** | `src/services/container.py` | DI container |

### UI Components (Streamlit Tabs)

| Tab | File | Key Functions |
|-----|------|---------------|
| **Generator** | `src/ui/components/definition_generator_tab.py` | Generation workflow (2,351 LOC) |
| **Edit** | `src/ui/components/definition_edit_tab.py` | Edit existing definitions |
| **Review** | `src/ui/components/expert_review_tab.py` | Expert review interface |
| **Validation View** | `src/ui/components/validation_view.py` | Validation results display |
| **Examples** | `src/ui/components/examples_block.py` | Example sentence generation |

### Configuration

| Type | File | Purpose |
|------|------|---------|
| **Main Config** | `config/config.yaml` | Primary application config |
| **Validation Rules** | `config/toetsregels/regels/*.json` | 45 validation rules |
| **Cache** | `config/cache_config.yaml` | Caching strategy |
| **Logging** | `config/logging_config.yaml` | Log levels & formats |
| **Approval Gate** | `config/approval_gate.yaml` | Validation gate policy (EPIC-016) |

### Testing

| Type | Directory | Run Command |
|------|-----------|-------------|
| **All Tests** | `tests/` | `pytest` |
| **Smoke Tests** | `tests/smoke/` | `pytest -m smoke` |
| **Unit Tests** | `tests/services/` | `pytest -m unit` |
| **Integration** | `tests/integration/` | `pytest -m integration` |
| **Performance** | `tests/performance/` | `pytest -m performance` |

## Known Issues

### Fixed (2025-10-07)
- ✅ Hardcoded API key in old config file (removed)
- ✅ Import errors in test suite (wrapped monitoring imports)

### Active Issues
- [ ] Performance measurement mixes cold start + full render (see `src/main.py:91-123`)
- [ ] Some test files timeout (e.g., `test_voorbeelden_contract.py`)

## Recent Changes (Last 7 Days)

### 2025-10-07
- Fixed security breach (hardcoded API key in `.old` file)
- Fixed test import errors (lazy monitoring imports)
- Created WORKING.md navigation guide

### 2025-10-06
- US-202: Container caching optimization (77% faster startup, 81% less memory)
- Fixed 5x toetsregels duplication in rule modules

### Earlier
- 78% startup performance improvement
- Container singleton fix
- Sidebar UI cleanup

## Quick Commands

### Development
```bash
# Start app
bash scripts/run_app.sh

# Run tests (fast)
pytest -m smoke -x

# Check code quality
ruff check src
```

### Debugging
```bash
# Run specific test
pytest tests/services/test_definition_generator.py -x

# Clear cache
streamlit cache clear

# Check database
sqlite3 data/definities.db "SELECT COUNT(*) FROM definities;"
```

## Architecture Quick Tips

### Adding a New Service
1. Define in `src/services/<name>.py`
2. Add to `ServiceContainer` in `src/services/container.py`
3. Use via `container.<service_name>()`

### Adding a Validation Rule
1. Create JSON: `config/toetsregels/regels/CAT-##.json`
2. Create Python: `src/toetsregels/regels/CAT_##.py`
3. Add to `config/toetsregels.json`

### Finding Where Code Lives
- **Ctrl+F in this file** for quick architecture lookup
- **Validation** = `modular_validation_service.py`
- **Generation** = `definition_orchestrator_v2.py`
- **Prompts** = `prompt_service_v2.py`
- **UI** = `tabbed_interface.py` + `components/`

## Solo Developer Notes

### What NOT to Do
- ❌ Don't split the God Object (2,351 LOC tab) - Streamlit state management becomes harder
- ❌ Don't add UI tests - Manual testing (45 sec) is faster than automated (60 sec + 24 hours setup)
- ❌ Don't refactor "layer violations" - Direct UI→DB access is fine for solo dev
- ❌ Don't chase 100% test coverage - Focus on critical business logic (45 validation rules)

### What TO Focus On
- ✅ Fix bugs that block you
- ✅ Add tests for complex business logic (validation rules, AI integration)
- ✅ Performance issues that slow daily work
- ✅ Security issues (API keys, data leaks)
- ✅ Ship features!

## Links

- **Project README**: `README.md`
- **Architecture**: `docs/architectuur/ENTERPRISE_ARCHITECTURE.md`
- **Backlog**: `docs/backlog/` (or use GitHub Issues)
- **Recent Analysis**: `docs/analyses/SOLO_DEVELOPER_REANALYSIS.md`

---

**Remember**: You're a solo developer. Perfect code < shipped features. Fix what hurts, ignore what's theoretical. 🚀
