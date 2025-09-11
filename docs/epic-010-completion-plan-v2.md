---
titel: EPIC-010 Direct Refactor Plan v2 - Sprint 37
aangemaakt: 2025-09-10
status: Planning - REVIEWED
prioriteit: KRITIEK
approach: DIRECT REFACTOR - GEEN BACKWARDS COMPATIBILITY
---

# 🚀 EPIC-010 Direct Refactor Plan v2 - Sprint 37

## Executive Summary

Dit document bevat het **aangepaste** 5-daagse direct refactor plan op basis van review feedback. Belangrijkste wijzigingen:
- UI migratie + wrapper removal op **dezelfde dag** om breaking UI te voorkomen
- Gebruik bestaande `rate_limit_config.py` voor timeouts (geen nieuwe timeouts.yaml)
- Async cleanup in orchestrator (geen sync bridging in services)
- CI-gates tegen legacy patterns

## ⚡ Direct Refactor Strategie

### Core Principes
- **Single-user app**: Errors tijdens refactor zijn OK
- **Direct refactor**: Alles in één keer aanpassen
- **Fix wat breekt**: Geen workarounds, gewoon oplossen
- **Clean architecture**: Business logica behouden, tech debt elimineren

## 📅 5-Daags Actieplan (AANGEPAST)

### Dag 1: UI Migratie + Wrapper Removal + Bug Fix

**KRITIEK: UI migratie en wrapper removal SAMEN om gebroken UI te voorkomen**

#### Ochtend: CFR-BUG-014 Fix (2 uur)

**Bestanden:** `src/voorbeelden/unified_voorbeelden.py`

**1. Verbeter prompts voor synoniemen/antoniemen:**
```python
if request.example_type == ExampleType.SYNONIEMEN:
    return f"""Voor het begrip '{begrip}' met de volgende definitie:
{definitie}

Context: {context_text if context_text else 'Algemeen juridisch'}

Geef EXACT {request.max_examples} synoniemen of verwante termen.
BELANGRIJK: 
- PRECIES {request.max_examples} items, niet meer en niet minder
- Één synoniem per regel
- GEEN nummering, bullets, streepjes of andere formatting
- Als er geen {request.max_examples} perfecte synoniemen zijn, gebruik verwante termen"""
```

**2. Enforce + retry logic:**
```python
async def _generate_with_retry(self, request: ExampleRequest, max_retries: int = 1):
    """Generate met 1 retry bij incorrect aantal."""
    for attempt in range(max_retries + 1):
        result = await self._generate_async(request)
        
        if request.example_type in [ExampleType.SYNONIEMEN, ExampleType.ANTONIEMEN]:
            expected = request.max_examples
            
            # Trim excess
            if len(result) > expected:
                return result[:expected]
            
            # Accept on last attempt (avoid infinite loops)
            if len(result) >= expected or attempt == max_retries:
                if len(result) < expected:
                    logger.warning(f"Accepting {len(result)}/{expected} items after {attempt+1} attempts")
                return result
                
            # Retry with enhanced prompt
            request.extra_instruction = f"Je gaf {len(result)} items, maar er zijn EXACT {expected} nodig."
    
    return result
```

**3. UI display fix:**
```python
# In UI rendering, verwijder bullets voor synoniemen/antoniemen
if example_type in ["synoniemen", "antoniemen"]:
    # Geen "• " prefix, gewoon de items
    for item in examples:
        st.write(item)  # Zonder bullet
else:
    # Andere types kunnen bullets hebben
    for item in examples:
        st.write(f"• {item}")
```

#### Middag: UI Migratie + Service Cleanup (4 uur)

**SAMEN uitvoeren om breaking UI te voorkomen:**

**Stap 1: Update alle UI imports (30 min):**
```bash
# Identificeer alle aanpassingen nodig
rg -l "generate_definition_sync|search_web_sources" src/ui/ --glob "!async_bridge.py"
```

**Voor elk bestand:**
```python
# Van:
from services.service_factory import get_definition_service
result = factory.generate_definition_sync(begrip, context, **kwargs)

# Naar:
from services.service_factory import get_definition_service
from ui.helpers.async_bridge import generate_definition_sync
result = generate_definition_sync(factory, begrip, context, **kwargs)
```

**Stap 2: Direct verwijder deprecated methods (30 min):**
```python
# In service_factory.py - VERWIJDER:
# - generate_definition_sync() op regel 404-444
# - search_web_sources() op regel 447-472
```

**Stap 3: Test & fix runtime errors (3 uur):**
```bash
# Start app en fix errors real-time
OPENAI_API_KEY="$OPENAI_API_KEY_PROD" streamlit run src/main.py
```

### Dag 2: Async Cleanup in Services

#### Ochtend: Orchestrator Async Fix (3 uur)

**Probleem:** Orchestrator V2 gebruikt sync `genereer_alle_voorbeelden()` binnen async flow

**Fix in `definition_orchestrator_v2.py`:**
```python
# Van:
voorbeelden = self.voorbeelden_service.genereer_alle_voorbeelden(
    begrip, definitie, context_dict
)

# Naar:
voorbeelden = await self.voorbeelden_service.genereer_alle_voorbeelden_async(
    begrip, definitie, context_dict
)
```

**Verwijder `_run_async_safe` uit services:**
```bash
# Vind alle sync bridging in services
rg "_run_async_safe|asyncio\.run" src/services/ --glob "!async_bridge.py"

# Voor elke match: refactor naar proper async
```

#### Middag: Timeout Integratie met rate_limit_config (3 uur)

**Gebruik bestaande `src/config/rate_limit_config.py`:**

**Update async_bridge.py:**
```python
from config.rate_limit_config import get_endpoint_timeout

def generate_definition_sync(service_factory, begrip: str, context_dict: dict, **kwargs):
    """Gebruik endpoint-specifieke timeout uit rate_limit_config."""
    timeout = get_endpoint_timeout('definition_generation')  # Was: hardcoded 30
    return run_async(
        service_factory.generate_definition(begrip, context_dict, **kwargs),
        timeout=timeout
    )

def search_web_sources_sync(service_factory, term: str, sources: list | None = None):
    """Gebruik endpoint-specifieke timeout uit rate_limit_config."""
    timeout = get_endpoint_timeout('web_search')  # Was: hardcoded 15
    # ... rest of implementation
```

**Voeg missing endpoints toe aan rate_limit_config.py:**
```python
ENDPOINT_CONFIGS["web_search"] = EndpointConfig(
    tokens_per_second=2.0,
    bucket_capacity=10,
    burst_capacity=5,
    target_response_time=3.0,
    timeout=15.0,
)
```

### Dag 3: CI-Gates & Legacy Pattern Cleanup

#### Ochtend: Implementeer CI-Gates (2 uur)

**Maak `.github/workflows/epic-010-gates.yml`:**
```yaml
name: EPIC-010 Legacy Pattern Gates

on: [push, pull_request]

jobs:
  check-legacy-patterns:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Check voor legacy imports
        run: |
          # Blokkeer oude patterns
          ! grep -r "from src.models.generation_result import" src/ || exit 1
          ! grep -r "\.overall_score" src/ || exit 1
          ! grep -r "request\.context[^_]" src/ || exit 1  # context als string
          ! grep -r "domein" src/ --include="*.py" || exit 1
          
      - name: Check voor async anti-patterns in services
        run: |
          # asyncio.run alleen toegestaan in async_bridge
          ! grep -r "asyncio\.run" src/services/ || exit 1
          ! grep -r "run_coroutine_threadsafe" src/services/ || exit 1
          
      - name: Check voor directe sync wrapper calls
        run: |
          # Geen directe calls buiten async_bridge
          FILES=$(grep -r "generate_definition_sync\|search_web_sources" src/ui/ --include="*.py" | grep -v async_bridge | grep -v "from.*async_bridge")
          if [ -n "$FILES" ]; then
            echo "Found direct sync wrapper calls:"
            echo "$FILES"
            exit 1
          fi
```

#### Middag: Elimineer Gevonden Legacy Patterns (4 uur)

```bash
# Systematisch verwijder legacy patterns
rg "generation_result|overall_score|best_iteration" src/
rg "request\.context[^_]" src/  # context als string ipv dict
rg "domein" src/ --type py

# Fix elke gevonden instance
```

### Dag 4: Test Suite Reparatie

#### Hele Dag: Fix Tests & Mocks

```bash
# 1. Capture alle failures
pytest tests/ -v > test_failures.txt 2>&1

# 2. Common fixes:
#    - Mock async_bridge ipv service_factory sync methods
#    - Update imports voor verwijderde modules
#    - Fix async test patterns

# 3. Focus op kritieke modules
pytest tests/services/test_service_factory.py  # Update voor removed methods
pytest tests/services/test_orchestrator_v2.py  # Fix async voorbeelden calls
pytest tests/ui/  # Update voor async_bridge usage

# 4. Run tot alles groen is
while ! pytest tests/ -q; do
    echo "Fixing next test..."
done
```

### Dag 5: Verificatie & Documentatie

#### Ochtend: Final Verificatie (3 uur)

**Verificatie checklist:**
```bash
# 1. UI callsites check
echo "=== Checking UI uses async_bridge ==="
! rg "factory\.generate_definition_sync" src/ui/
! rg "factory\.search_web_sources" src/ui/

# 2. Services async check  
echo "=== Checking services are properly async ==="
! rg "asyncio\.run|_run_async_safe" src/services/

# 3. Synoniemen/antoniemen check
echo "=== Testing examples generation ==="
python -c "
from src.voorbeelden.unified_voorbeelden import UnifiedVoorbeeldenService
from src.voorbeelden.interfaces import ExampleRequest, ExampleType
service = UnifiedVoorbeeldenService()
for etype in [ExampleType.SYNONIEMEN, ExampleType.ANTONIEMEN]:
    req = ExampleRequest(
        begrip='contract',
        definitie='Een overeenkomst',
        context_dict={},
        example_type=etype,
        max_examples=5
    )
    result = service.generate(req)
    print(f'{etype}: {len(result.examples)} items')
    assert len(result.examples) >= 3  # Minimum acceptable
"

# 4. Orchestrator async check
echo "=== Checking orchestrator uses async voorbeelden ==="
rg "genereer_alle_voorbeelden_async" src/services/orchestrators/

# 5. Full app test
OPENAI_API_KEY="$OPENAI_API_KEY_PROD" streamlit run src/main.py
```

#### Middag: Documentatie Update (3 uur)

**Update bestanden:**
1. `docs/backlog/EPIC-010/EPIC-010.md` → Status: 100%
2. `CHANGELOG.md` → Document breaking changes
3. Verwijder obsolete docs:
   - `docs/handover-epic-010-completion.md`
   - `docs/epic-010-completion-plan.md` (vervangen door v2)

## ✅ Definition of Done

### Dag 1 Checklist:
- [ ] CFR-BUG-014: synoniemen/antoniemen zonder bullets, retry logic
- [ ] UI gebruikt async_bridge voor alle calls
- [ ] Deprecated methods verwijderd uit ServiceFactory
- [ ] App draait zonder errors

### Dag 2 Checklist:
- [ ] Orchestrator gebruikt `genereer_alle_voorbeelden_async`
- [ ] Geen `_run_async_safe` in services
- [ ] Timeouts via `get_endpoint_timeout` uit rate_limit_config

### Dag 3 Checklist:
- [ ] CI-gates actief tegen legacy patterns
- [ ] Geen generation_result, overall_score, domein references
- [ ] Geen asyncio.run in services

### Dag 4 Checklist:
- [ ] Alle tests groen
- [ ] Mocks updated voor async_bridge

### Dag 5 Checklist:
- [ ] Verificatie script succesvol
- [ ] EPIC-010: 100% COMPLETE
- [ ] Documentatie bijgewerkt

## 🎯 Key Metrics

| Metric | Target | Verificatie |
|--------|--------|-------------|
| Synoniemen/Antoniemen | ≥3 items, geen bullets | Test script |
| UI Stability | 0 crashes | Manual test |
| Async Compliance | 0 sync bridges in services | grep check |
| Legacy Patterns | 0 occurrences | CI gates |
| Test Coverage | ≥ baseline | pytest coverage |

## 💪 Voordelen Direct Refactor v2

1. **Geen gebroken UI**: Migratie + removal samen
2. **Hergebruik bestaande config**: rate_limit_config.py
3. **Clean async**: Services volledig async
4. **CI protection**: Gates tegen regressie
5. **5 dagen totaal**: Efficiënt en gefocust

## 🚨 Risk Mitigatie

| Risico | Mitigatie |
|--------|-----------|
| UI breekt | Dag 1: migratie + removal samen |
| Te weinig synoniemen | 1 retry, accepteer <N op laatste poging |
| Dubbele timeouts | Gebruik alleen rate_limit_config |
| Legacy pattern regressie | CI-gates blokkeren bad patterns |

## 📝 Final Notes

Dit v2 plan integreert alle review feedback:
- UI migratie gebeurt SAMEN met wrapper removal (Dag 1)
- Orchestrator gebruikt async voorbeelden (Dag 2)
- Timeouts via bestaande rate_limit_config (geen nieuwe yaml)
- CI-gates beschermen tegen regressie (Dag 3)
- Synoniemen/antoniemen: retry + geen bullets in UI

**Remember**: Direct refactor = fix wat breekt, geen workarounds!