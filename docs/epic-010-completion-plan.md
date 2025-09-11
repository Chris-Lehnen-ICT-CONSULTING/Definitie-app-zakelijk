---
titel: EPIC-010 Direct Refactor Plan - Sprint 37
aangemaakt: 2025-09-10
updated: 2025-09-10
status: Planning
prioriteit: KRITIEK
approach: DIRECT REFACTOR - GEEN BACKWARDS COMPATIBILITY
---

# 🚀 EPIC-010 Direct Refactor Plan - Sprint 37

## Executive Summary

Dit document beschrijft de DIRECTE refactor aanpak om EPIC-010 af te ronden in **5 dagen** i.p.v. 11 dagen. We volgen het "REFACTOR, GEEN BACKWARDS COMPATIBILITY" principe uit CLAUDE.md - alles wordt in één keer aangepast zonder migratiepaden.

## 📊 Analyse Huidige Situatie

### 1. Sync Wrapper Status (service_factory.py)

**Gevonden deprecated methods:**
- `generate_definition_sync()` op regel 404
- `search_web_sources()` op regel 447

**Kenmerken:**
- Beide gebruiken `asyncio.run()` voor sync-async conversie
- Gemarkeerd met "DEPRECATED" en "TODO: Remove after UI migration"
- Worden direct aangeroepen vanuit UI componenten

### 2. Async Bridge Status (ui/helpers/async_bridge.py)

**Bestaande functionaliteit:**
- ✅ `run_async()` - Centrale async-to-sync conversie met timeout support
- ✅ `generate_definition_sync()` - Wrapper voor definitie generatie
- ✅ `search_web_sources_sync()` - Wrapper voor web lookup
- ✅ Event loop detectie en thread-safe execution

**Ontbrekende functionaliteit:**
- ⚠️ Gecentraliseerde timeout configuratie
- ⚠️ Monitoring en metrics

### 3. CFR-BUG-014 Analyse

**Probleem:** Synoniemen/antoniemen generatie produceert inconsistente aantallen

**Gevonden issues:**
1. **Prompt formaat** (regel 485-492 in unified_voorbeelden.py):
   - Prompts vragen om "EXACT X items"
   - Geen context of definitie meegegeven (alleen begrip)
   - Te simpele instructies voor complexe termen

2. **Parsing logic:**
   - Parser verwacht items op nieuwe regels
   - Geen fallback voor komma-gescheiden lijsten
   - Geen validatie op aantal geretourneerde items

3. **Response handling:**
   - max_tokens=2000 voor sync, 1500 voor async (inconsistent)
   - Geen retry bij te weinig items

## ⚡ Direct Refactor Strategie

### Waarom Direct Refactor?

Per CLAUDE.md principes:
- **Single-user applicatie** - geen externe gebruikers
- **Development omgeving** - errors tijdens refactor zijn acceptabel
- **Clean code focus** - geen legacy baggage
- **Fast feedback** - problemen direct zichtbaar en oplosbaar

### Voorbereiding (30 minuten)

```bash
# 1. Commit huidige staat voor rollback optie
git add -A
git commit -m "chore: checkpoint voor EPIC-010 direct refactor"

# 2. Maak refactor branch
git checkout -b refactor/epic-010-direct-completion

# 3. Identificeer alle te wijzigen locaties
echo "=== Sync wrapper calls in UI ==="
rg "generate_definition_sync|search_web_sources" src/ui/ --glob "!async_bridge.py"

echo "=== Deprecated methods in services ==="
rg "def (generate_definition_sync|search_web_sources)" src/services/

echo "=== Direct asyncio.run usage ==="
rg "asyncio\.run" src/ --glob "!async_bridge.py"
```

## 📅 5-Daags Actieplan

### Dag 1: CFR-BUG-014 Fix + Service Cleanup

#### Ochtend: Bug Fix (2 uur)

**Bestanden om aan te passen:**
- `src/voorbeelden/unified_voorbeelden.py`

**Acties:**
1. Verbeter prompts voor synoniemen/antoniemen (voeg definitie + context toe)
2. Fix parser met komma-fallback
3. Voeg retry logic toe
4. Maak max_tokens consistent (2000 voor beide)

#### Middag: Service Cleanup (4 uur)

**Bestanden om aan te passen:**
- `src/services/service_factory.py` - VERWIJDER deprecated methods
- `src/ui/helpers/async_bridge.py` - Verificeer dat replacements werken

**Acties:**
```python
# In service_factory.py - VERWIJDER deze methods volledig:
# - generate_definition_sync() op regel 404-444
# - search_web_sources() op regel 447-472

# Geen deprecation warnings, geen comments - gewoon weg!
```

### Dag 2: UI Direct Refactor

#### Ochtend: Alle UI Imports Updaten (3 uur)

**Search & Replace Strategie:**

```bash
# 1. Identificeer alle files die aanpassing nodig hebben
rg -l "generate_definition_sync|search_web_sources" src/ui/ --glob "!async_bridge.py"

# 2. Voor elk bestand, pas het import pattern aan:
```

**Van:**
```python
from services.service_factory import get_definition_service

def some_handler():
    factory = get_definition_service()
    result = factory.generate_definition_sync(begrip, context, **kwargs)
```

**Naar:**
```python
from services.service_factory import get_definition_service
from ui.helpers.async_bridge import generate_definition_sync

def some_handler():
    factory = get_definition_service()
    result = generate_definition_sync(factory, begrip, context, **kwargs)
```

#### Middag: Test & Fix (3 uur)

```bash
# 1. Start de app en kijk wat breekt
OPENAI_API_KEY="$OPENAI_API_KEY_PROD" streamlit run src/main.py

# 2. Voor elke error:
#    - Fix de import/call
#    - Test opnieuw
#    - Repeat

# 3. Test alle tabs systematisch:
#    - Definitie Generator tab
#    - Validatie tab
#    - Export functionaliteit
#    - Web lookup
```

### Dag 3: Timeout Config + Async Cleanup

#### Ochtend: Implementeer Timeout Config (2 uur)

**1. Voeg timeout config toe aan config_default.yaml:**
```yaml
# Voeg toe aan config/config_default.yaml
timeouts:
  definition_generation: 30.0
  example_generation: 15.0
  validation: 10.0
  web_lookup: 15.0
  ui_default: 30.0
```

**2. Update async_bridge.py met config loading:**
- Laad timeouts uit config
- Pas toe op alle wrapper functions

#### Middag: Verwijder Alle Async Anti-patterns (4 uur)

```bash
# 1. Vind alle directe asyncio.run usage
rg "asyncio\.run" src/ --glob "!async_bridge.py"

# 2. Voor elke gevonden locatie:
#    - Vervang met async_bridge.run_async()
#    - OF refactor naar proper async flow

# 3. Verwijder onnodige async complexity
rg "run_coroutine_threadsafe" src/ --glob "!async_bridge.py"
```

### Dag 4: Test Suite Reparatie

#### Hele Dag: Fix Alle Failing Tests

```bash
# 1. Run alle tests en capture failures
pytest tests/ -v > test_failures.txt 2>&1

# 2. Common fixes nodig:
#    - Update mocks voor verwijderde sync methods
#    - Fix imports die niet meer bestaan
#    - Update test calls naar async_bridge

# 3. Focus op high-value test modules:
pytest tests/services/test_definition_generator.py    # 99% coverage
pytest tests/services/test_definition_validator.py    # 98% coverage
pytest tests/services/test_service_factory.py        # Fix voor removed methods

# 4. Itereer tot alles groen is
while ! pytest tests/ -q; do
    # Fix next failing test
    # Re-run
done
```

### Dag 5: Documentatie & Final Verification

#### Ochtend: Update Documentatie (2 uur)

**Te updaten files:**
- `docs/backlog/EPIC-010/EPIC-010.md` → Status: 100% COMPLETE
- `docs/architectuur/SOLUTION_ARCHITECTURE.md` → Document async pattern
- `CHANGELOG.md` → Document breaking changes
- Verwijder `docs/handover-epic-010-completion.md` (niet meer nodig)

#### Middag: Final Testing (4 uur)

```bash
# 1. Full app test
OPENAI_API_KEY="$OPENAI_API_KEY_PROD" streamlit run src/main.py

# 2. Test elke functionaliteit:
#    - Genereer definitie
#    - Valideer definitie
#    - Genereer voorbeelden (vooral synoniemen/antoniemen!)
#    - Export naar PDF/Word
#    - Web lookup

# 3. Performance check
#    - Moet even snel zijn als voorheen
#    - Geen merkbare async overhead

# 4. Final commit
git add -A
git commit -m "feat: complete EPIC-010 - direct refactor zonder backwards compatibility"
```

## ✅ Definition of Done Checklist

#### Na Dag 1:
- [ ] CFR-BUG-014 opgelost (test: 5/5 synoniemen)
- [ ] Deprecated methods verwijderd uit ServiceFactory
- [ ] App start zonder errors

#### Na Dag 2:
- [ ] Alle UI imports gebruik async_bridge
- [ ] Geen directe factory.generate_definition_sync() calls meer
- [ ] App volledig functioneel

#### Na Dag 3:
- [ ] Timeout config werkend
- [ ] Geen asyncio.run buiten async_bridge
- [ ] Geen run_coroutine_threadsafe buiten async_bridge

#### Na Dag 4:
- [ ] Alle tests groen
- [ ] Test coverage minimaal gelijk gebleven

#### Na Dag 5:
- [ ] EPIC-010 status: 100% COMPLETE
- [ ] Documentatie bijgewerkt
- [ ] Final test: alle functionaliteit werkt

## 🎯 Key Success Metrics

| Metric | Target | Hoe Meten |
|--------|--------|-----------|
| Synoniemen/Antoniemen | 5/5 consistent | Test script |
| Test Pass Rate | 100% | pytest |
| Performance | <100ms overhead | Time measurements |
| Code Cleanliness | 0 deprecated | grep searches |
| App Stability | 0 crashes | Manual testing |

## 💪 Voordelen van Direct Refactor

1. **Sneller klaar**: 5 dagen i.p.v. 11 dagen
2. **Cleaner code**: Geen legacy baggage
3. **Minder complex**: Geen migration paths
4. **Direct feedback**: Errors meteen zichtbaar
5. **Geen technical debt**: Alles in één keer goed

## 🚫 Wat We NIET Doen

- ❌ Deprecation warnings
- ❌ Backwards compatibility layers
- ❌ Feature flags voor migratie
- ❌ Gefaseerde rollout
- ❌ Legacy support
- ❌ Migration helpers
- ❌ Compatibility tests

## ✅ Wat We WEL Doen

- ✅ Direct refactoren
- ✅ Breaking changes accepteren
- ✅ Tests fixen die breken
- ✅ Business logica behouden
- ✅ Clean architecture
- ✅ Fast iteration

## 📝 Final Notes

Dit plan volgt het "REFACTOR, GEEN BACKWARDS COMPATIBILITY" principe uit CLAUDE.md. We accepteren dat dingen tijdelijk breken tijdens development en fixen ze meteen. Dit is efficiënter voor een single-user development applicatie.

**Remember**: Als iets breekt, fix het. Geen workarounds, geen compatibility layers - gewoon de juiste oplossing implementeren.
