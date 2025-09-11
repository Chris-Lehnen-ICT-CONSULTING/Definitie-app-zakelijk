---
titel: Handover Document - EPIC-010 Afronding
aangemaakt: 2025-09-10
status: 85% voltooid
prioriteit: KRITIEK
sprint: 37
---

# 📋 Handover Document - EPIC-010 Context Flow Refactoring

## 🎯 Executive Summary

EPIC-010 is **85% voltooid** met de kern architectuur volledig werkend. De applicatie is stabiel en functioneel, met context propagatie 100% werkend. De resterende 15% betreft het volledig uitfaseren van deprecated sync wrappers in Sprint 37.

## 📊 Huidige Status

### ✅ Wat is Voltooid (85%)

1. **Context Propagatie (100%)**
   - UI context bereikt AI prompts correct
   - List-based velden werken volledig
   - "Anders..." optie werkt zonder crashes

2. **Framework Separatie (100%)**
   - `ServiceContextAdapter` is framework-neutraal
   - `UI ContextAdapter` handelt Streamlit af
   - Geen streamlit imports in services

3. **V2-Only Pad (100%)**
   - Legacy fallback volledig verwijderd
   - Feature flags zijn UI-only
   - Services hebben geen UI dependencies

4. **Test Coverage**
   - 71 tests passed, 5 skipped
   - 60+ test files aangepast voor domein removal
   - Core functionaliteit volledig getest

### ⚠️ Wat Resteert (15%)

1. **Deprecated Sync Wrappers**
   - `generate_definition_sync()` in ServiceFactory
   - `search_web_sources()` in ServiceFactory
   - Beide met DEPRECATED markers
   - UI gebruikt deze nog direct

2. **UI Migratie naar Async Bridge**
   - `ui/helpers/async_bridge.py` bestaat en werkt
   - UI code moet gemigreerd worden
   - Timeouts moeten geconfigureerd worden

## 🐛 Actieve Bugs

### CFR-BUG-014: Synoniemen/Antoniemen Incorrect
- **Locatie**: `docs/backlog/epics/EPIC-010/CFR-BUG-014-synoniemen-antoniemen/`
- **Impact**: HOOG - Genereert 2/5 synoniemen, formatting issues
- **Vermoedelijke oorzaak**: Prompt module of parser issue
- **Te onderzoeken**:
  - `src/services/prompts/modules/synoniemen_module.py`
  - `src/services/prompts/modules/antoniemen_module.py`
  - `src/voorbeelden/voorbeelden_service.py`

## 🚀 Sprint 37 - Actieplan voor Afronding

### Week 1: UI Migratie Voorbereiden
```python
# 1. Maak feature branch
git checkout -b feature/sprint-37-async-completion

# 2. Implementeer timeout configuratie
# config/timeouts.yaml
timeouts:
  generation: 30
  web_lookup: 15
  export: 10
  validation: 5

# 3. Update async_bridge met config
from config_manager import get_config
timeouts = get_config().timeouts
```

### Week 2: UI Componenten Migreren

#### Stap 1: Update UI Imports
```python
# Van:
from services.service_factory import get_definition_service
factory = get_definition_service()
result = factory.generate_definition_sync(...)

# Naar:
from services.service_factory import get_definition_service
from ui.helpers.async_bridge import generate_definition_sync
factory = get_definition_service()
result = generate_definition_sync(factory, ...)
```

#### Stap 2: Migreer Per Component
**Te migreren bestanden:**
1. `src/ui/tabbed_interface.py` (2 calls)
2. `src/ui/components/definition_generator_tab.py` (1 call)
3. Andere tab componenten die sync methods gebruiken

### Week 3: Cleanup & Testing

#### Stap 1: Verwijder Deprecated Methods
```python
# In service_factory.py - VERWIJDER:
def generate_definition_sync(...)
def search_web_sources(...)
```

#### Stap 2: Run Full Test Suite
```bash
# Verificatie queries
rg -n "generate_definition_sync" src/
rg -n "search_web_sources" src/
rg -n "asyncio.run" src/services/
pytest tests/ -v
```

## 📝 Belangrijke Bestanden & Locaties

### Core Files om te Wijzigen:
- `src/services/service_factory.py` - Verwijder sync wrappers
- `src/ui/tabbed_interface.py` - Migreer naar async_bridge
- `src/ui/components/definition_generator_tab.py` - Migreer naar async_bridge
- `src/ui/helpers/async_bridge.py` - Voeg config timeouts toe

### Documentatie om bij te Werken:
- `docs/backlog/EPIC-010/EPIC-010.md` - Update naar 100%
- `docs/architectuur/SOLUTION_ARCHITECTURE.md` - Document async pattern
- `CHANGELOG.md` - Document breaking changes

### Test Files:
- `tests/services/test_service_factory.py` - Update na removal
- `tests/ui/test_async_bridge.py` - Nieuwe tests voor timeouts
- `tests/integration/test_context_flow_epic_cfr.py` - E2E tests

## ⚠️ Risico's & Mitigatie

| Risico | Impact | Mitigatie |
|--------|--------|-----------|
| UI breekt na sync removal | HOOG | Test elke UI component na migratie |
| Timeout te agressief | MEDIUM | Start met 30s, monitor productie |
| Async overhead | LAAG | Profile voor/na, <100ms acceptable |
| Regressies in tests | MEDIUM | Fix tests voor removal |

## 🔍 Verificatie Checklist

### Voor Merge:
- [ ] Alle UI componenten gebruiken async_bridge
- [ ] Geen sync wrappers in ServiceFactory
- [ ] Geen `asyncio.run` in services
- [ ] Geen `run_coroutine_threadsafe` buiten async_bridge
- [ ] Alle tests groen
- [ ] Performance benchmark <100ms overhead
- [ ] CFR-BUG-014 opgelost

### Verificatie Commands:
```bash
# 1. Check voor streamlit in services
rg -n "import streamlit" src/services/
# Verwacht: 0 results

# 2. Check voor sync patterns
rg -n "generate_definition_sync|search_web_sources" src/
# Verwacht: alleen in async_bridge.py

# 3. Check voor async anti-patterns
rg -n "asyncio\.run|run_coroutine_threadsafe" src/services/
# Verwacht: 0 results

# 4. Run tests
pytest tests/services/ -v
pytest tests/ui/ -v
```

## 💡 Tips voor Implementatie

1. **Gefaseerde Migratie**: Migreer één UI component per keer
2. **Feature Flags**: Gebruik UI feature flags voor rollback
3. **Monitor Logs**: Check voor timeout errors in productie
4. **Backup Plan**: Houd branch met sync wrappers tot alles werkt

## 📞 Contact & Resources

- **EPIC-010 Main Doc**: `docs/backlog/EPIC-010/EPIC-010.md`
- **Sprint 37 Planning**: Zie sectie "Sprint 37 Planning" in EPIC-010
- **Architecture Docs**: `docs/architectuur/`
- **Previous Work**: Commits 827d7d4..88a60f8

## 🎯 Definition of Done

EPIC-010 is volledig afgerond wanneer:
1. ✅ Context propagatie 100% werkend
2. ✅ Geen streamlit imports in services  
3. ⬜ Geen sync wrappers in ServiceFactory
4. ⬜ Alle UI gebruikt async_bridge
5. ⬜ Timeouts geconfigureerd en getest
6. ⬜ CFR-BUG-014 opgelost
7. ⬜ Documentatie bijgewerkt
8. ⬜ Alle tests groen

---

**Geschatte tijd voor afronding**: 1 sprint (3 weken)
**Complexiteit**: Medium
**Business Value**: Hoog (clean architecture, maintainability)