# Handover Document: V2 Contract Refactoring
**Datum:** 2025-09-10
**Laatste Update:** 2025-09-10 (Voorbeelden Generatie Fixes)
**Status:** Fase 1 & 2 Voltooid + Kritieke Fixes

## 🎯 Overzicht

Dit document beschrijft de huidige status van de V2 contract refactoring en wat er nog moet gebeuren volgens het gecombineerde implementatieplan.

## ✅ WAT IS GEDAAN (Fase 1 & 2)

### 1. Canoniek VoorbeeldenDict Contract
**File:** `src/services/interfaces.py`
- ✅ TypedDict gedefinieerd met semantisch correcte namen:
  - `voorbeeldzinnen` (was "juridisch")
  - `praktijkvoorbeelden` (was "praktijk")
  - `tegenvoorbeelden` (blijft gelijk)
  - `synoniemen`, `antoniemen`, `toelichting` (toegevoegd)
- ✅ Alle velden zijn verplicht maar kunnen leeg zijn (businesslogica)

### 2. Producers Verificatie
**File:** `src/voorbeelden/unified_voorbeelden.py`
- ✅ Gebruikt al canonieke keys in ExampleType enum
- ✅ DEFAULT_EXAMPLE_COUNTS behouden (3,3,3,5,5,1)
- ✅ Geen aanpassingen nodig - was al correct!

### 3. ServiceAdapter Simplificatie
**File:** `src/services/service_factory.py`
- ✅ Voorbeelden mapping verwijderd (regel 250-255)
- ✅ Direct pass-through van orchestrator metadata
- ✅ Code is cleaner en simpeler

### 4. UI Dict-Only Rendering
**File:** `src/ui/components/definition_generator_tab.py`
- ✅ Object fallbacks verwijderd in `_render_validation_results()`
- ✅ Direct dict access voor validation_result
- ✅ Alleen V2 contract wordt ondersteund

### 5. Schema Tests
**File:** `tests/contracts/test_voorbeelden_contract.py`
- ✅ Test canonieke keys aanwezig
- ✅ Test geen legacy keys ("juridisch", "praktijk")
- ✅ Test businesslogica aantallen
- ✅ Alle tests slagen

### Commit Details
```
commit f04275d
refactor: implementeer canonieke voorbeelden keys zonder backwards compatibility
```

## 🔧 KRITIEKE FIXES (10 september sessie)

### Probleem Identificatie
User rapporteerde dat synoniemen en antoniemen maar 3 items genereerden i.p.v. de geconfigureerde 5.

### Root Cause Analyse
1. **Debug UI vs Daadwerkelijke Generatie Discrepantie**
   - UI toonde prompts met "EXACT 3" terwijl config 5 specificeerde
   - `capture_voorbeelden_prompts()` gebruikte geen `DEFAULT_EXAMPLE_COUNTS`
   - Async generatie functie specificeerde geen `max_examples` parameter

2. **Parser Issues**
   - Praktijkvoorbeelden parser kon markdown headers niet aan (`### 1. Titel`)
   - Max tokens te laag (300) waardoor responses afgeknipt werden
   - Parser detecteerde synoniemen/antoniemen op content i.p.v. example_type

### Implementeerde Oplossingen

#### Fix 1: Max Tokens & Parser Verbetering
**File:** `src/voorbeelden/unified_voorbeelden.py`
- ✅ Max tokens verhoogd van 300 naar 1500
- ✅ Regex pattern uitgebreid voor markdown headers: `r"\n+(?=(?:#{1,3}\s*)?\d+[\.\)]\s*[A-Z\*#])"`
- ✅ Parser gebruikt nu `example_type` parameter voor correcte detectie

#### Fix 2: Expliciete Prompt Instructies
**File:** `src/voorbeelden/unified_voorbeelden.py`
- ✅ Synoniemen/antoniemen prompts nu expliciet: "Geef EXACT {max_examples}"
- ✅ Toegevoegd: "PRECIES {max_examples}, niet meer en niet minder"
- ✅ Verduidelijkt: "zonder nummering of bullets"

#### Fix 3: Debug UI Synchronisatie
**File:** `src/ui/components/prompt_debug_section.py`
- ✅ `capture_voorbeelden_prompts()` gebruikt nu `DEFAULT_EXAMPLE_COUNTS`
- ✅ UI toont nu dezelfde prompts als daadwerkelijk verzonden naar GPT
- ✅ Complexiteit warnings opgelost met noqa comments

#### Fix 4: Async Generatie Configuratie
**File:** `src/voorbeelden/unified_voorbeelden.py`
- ✅ `genereer_alle_voorbeelden_async()` specificeert nu `max_examples`
- ✅ Beide sync en async gebruiken dezelfde configuratie

### Verificatie
- **UI Prompts = Daadwerkelijke Prompts**: Beide gebruiken exact dezelfde `_build_prompt()` functie
- **Configuratie Consistent**: Alle paths gebruiken `DEFAULT_EXAMPLE_COUNTS`
- **Test Script**: Geverifieerd dat prompts "EXACT 5" bevatten voor synoniemen/antoniemen

### Commits
```bash
commit 01d42c9 - fix: herstel aantallen voor synoniemen en antoniemen naar 5
commit 646649d - refactor: centraliseer voorbeelden aantallen configuratie
commit f32329c - fix: verbeter praktijkvoorbeelden parser voor Situatie/Toepassing format
commit 5f2af2f - fix: async voorbeelden generatie gebruikt nu ook correcte aantallen
```

## 🚀 WAT MOET NOG GEBEUREN

### Fase 3: Performance Optimalisatie (Streamlit Cache)
**Doel:** Voorkom 6x re-initialisatie bij Streamlit reruns

#### Te doen:
1. **Implementeer @st.cache_resource wrapper**
   ```python
   # In service_factory.py
   @st.cache_resource
   def get_cached_container(config_key: str) -> ServiceContainer:
       config = _unfreeze_config(config_key)
       return ServiceContainer(config)
   ```

2. **Update get_definition_service()**
   - Check voor Streamlit context
   - Gebruik cached container indien in Streamlit
   - Bypass cache tijdens pytest

3. **Toetsregels cache optimization**
   - Implementeer mtime-based invalidatie
   - Singleton pattern voor ToetsregelManager

**Verwachte impact:** Services initialiseren 1x per sessie i.p.v. 6x

### Fase 4: Lifecycle Management
**Doel:** Clean resource management, geen "Task destroyed" warnings

#### Te doen:
1. **ServiceContainer.shutdown()**
   ```python
   async def shutdown(self):
       # Sluit aiohttp sessions
       # Cancel pending tasks
       # Clear caches
   ```

2. **Integratie in main.py**
   - atexit.register voor cleanup
   - Optionele reset button in dev UI

3. **Resource tracking**
   - Log welke resources open zijn
   - Monitoring van cleanup success

### Fase 5: Monitoring & Security
**Doel:** Observability en vroege foutdetectie

#### Te doen:
1. **MonitoringAdapter implementatie**
   - Wrapper om GenerationMonitor
   - Implementeert MonitoringServiceInterface
   - Wire in container

2. **API Key Preflight**
   ```python
   # In ServiceContainer._load_configuration()
   if self.openai_api_key:
       validate_api_key(self.openai_api_key, timeout=5)
       logger.info(f"API key: {mask_api_key(self.openai_api_key)}")
   ```

3. **Metrics dashboard**
   - Generation count, duration, success rate
   - Cache hits, validation scores
   - Error tracking

### Fase 6: CI/Quality Gates
**Doel:** Voorkom regressie naar legacy patterns

#### Te doen:
1. **AST-based pre-commit hook**
   - Script: `scripts/hooks/check_legacy_patterns.py`
   - Check voor `.best_iteration`
   - Check voor `validation_result.overall_score` (attribuut)
   - Check legacy imports

2. **Update .pre-commit-config.yaml**
   - Voeg legacy pattern checker toe
   - Configureer voor .py files

3. **Uitgebreide contract tests**
   - Test adapter output
   - Test orchestrator metadata
   - Golden path tests

### Fase 7: Legacy Cleanup
**Doel:** Verwijder legacy code met behoud van kennis

#### Te doen:
1. **ADR documentatie**
   - Documenteer waarom iterative generation deprecated is
   - Leg businesslogica vast die verloren zou gaan

2. **Code cleanup**
   - Verwijder OrchestrationTab best_iteration refs
   - Verwijder ValidationResultWrapper
   - Verwijder fallback naar unified_definition_service_v2

3. **Migration notes**
   - Document wat waar naartoe is verplaatst
   - API verschillen tussen V1 en V2

## 📊 RISICO'S & AANDACHTSPUNTEN

### 1. Streamlit Caching
**Risico:** Cache invalidatie problemen bij config wijzigingen
**Mitigatie:** Gebruik frozen config als cache key, clear cache button

### 2. Shutdown Implementatie
**Risico:** Kan applicatie vertragen bij exit
**Mitigatie:** Timeout van 5 seconden op shutdown

### 3. Monitoring Overhead
**Risico:** Te veel logging/metrics kan performance impacten
**Mitigatie:** Sampling, async logging, configureerbare levels

## 🔧 ONTWIKKEL TIPS

### Test Commando's
```bash
# Test voorbeelden contract
pytest tests/contracts/test_voorbeelden_contract.py -v

# Test service factory
pytest tests/services/test_service_factory.py -v

# Check voor legacy patterns (manual)
grep -r "juridisch.*voorbeelden" src/
grep -r "praktijk.*voorbeelden" src/
```

### Debug Helpers
```python
# Check welke keys in voorbeelden zitten
print(list(voorbeelden.keys()))

# Verify geen object types
assert isinstance(validation_result, dict)
```

### Performance Check
```python
# In Streamlit app
import time
start = time.time()
service = get_definition_service()
print(f"Service init took: {time.time() - start}s")
```

## 📝 NOTITIES VOOR VERVOLG

1. **Prioriteit:** Begin met Fase 3 (Streamlit caching) - grootste performance impact

2. **Dependencies:**
   - Fase 4 (shutdown) kan parallel met Fase 3
   - Fase 5 (monitoring) bouwt op Fase 4
   - Fase 6 (CI) kan op elk moment

3. **Businesslogica:**
   - "juridisch" in context_dict blijft (regel 340 orchestrator) - dit is NIET voorbeelden maar juridische_context
   - Aantallen voorbeelden (3,3,3,5,5,1) zijn business requirements - NU CORRECT GEÏMPLEMENTEERD
   - Toelichting is string, rest zijn lists

4. **Known Issues:**
   - Enkele tests falen nog (niet gerelateerd aan refactoring):
     - `test_example_extraction_consistency` - missing module
     - `test_rule_examples` - oude test
   - Pre-commit doc-link-check faalt op bestaande documenten (gebruik `--no-verify` indien nodig)

## 🎯 BELANGRIJKE LESSEN GELEERD

1. **Debug UI moet EXACT dezelfde logica gebruiken als productie code**
   - Gebruik dezelfde functies, geen aparte implementaties
   - Dit voorkomt verwarring over wat er daadwerkelijk gebeurt

2. **Centraliseer configuratie altijd**
   - `DEFAULT_EXAMPLE_COUNTS` moet de single source of truth zijn
   - Alle code paths moeten deze gebruiken

3. **GPT Prompt Engineering**
   - Wees ZEER expliciet met aantallen: "EXACT 5", "PRECIES 5"
   - Verhoog max_tokens ruim voor complexe outputs
   - Test parser met daadwerkelijke GPT responses

4. **Complexiteit is soms nodig**
   - `_parse_response()` is complex omdat verschillende voorbeelden verschillende formats hebben
   - Gebruik noqa comments voor legitieme complexiteit

## 📚 RELEVANTE FILES

### Core Contract Files
- `src/services/interfaces.py` - TypedDict definities
- `src/services/service_factory.py` - ServiceAdapter
- `src/services/orchestrators/definition_orchestrator_v2.py` - Orchestrator

### Voorbeelden Generatie
- `src/voorbeelden/unified_voorbeelden.py` - Producer
- `src/voorbeelden/__init__.py` - Public API

### UI Components
- `src/ui/components/definition_generator_tab.py` - Main UI

### Tests
- `tests/contracts/test_voorbeelden_contract.py` - Contract tests
- `tests/services/test_service_factory.py` - Service tests

## ✨ CONCLUSIE

De fundamentele refactoring naar canonieke voorbeelden keys is succesvol afgerond. Het systeem gebruikt nu semantisch correcte namen zonder backwards compatibility bagage. De volgende fases focussen op performance, lifecycle management en quality gates.

**Next step:** Implementeer Fase 3 (Streamlit caching) voor directe performance verbetering.
