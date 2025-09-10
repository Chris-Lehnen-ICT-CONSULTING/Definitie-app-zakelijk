# EPIC-010 Implementatieplan - Context Flow & Orchestration Fixes

## Overzicht
Dit document bevat het gedetailleerde actieplan voor het oplossen van de functioneel relevante issues in EPIC-010.

**Datum**: 2025-01-10
**Status**: READY FOR IMPLEMENTATION
**Geschatte doorlooptijd**: 2-3 dagen

## Prioriteit 1: Voorbeelden UI Bug Fix 🔴 KRITIEK

### Probleem
Voorbeelden worden gegenereerd maar alleen prompts zijn zichtbaar in UI, niet de content.

### Root Cause Analyse Stappen

#### Stap 1: Debug Logging Implementatie (30 min)
Voeg tijdelijke debug logging toe op 4 kritieke punten:

```python
# 1. src/services/orchestrators/definition_orchestrator_v2.py:439
# Na voorbeelden generatie, voor metadata assignment
logger.info(
    "V2: voorbeelden generated for %s: keys=%s sizes=%s", 
    sanitized_request.begrip,
    list(voorbeelden.keys()) if isinstance(voorbeelden, dict) else type(voorbeelden),
    {k: (len(v) if isinstance(v, list) else len(v) if isinstance(v, str) else type(v).__name__) 
     for k, v in (voorbeelden or {}).items()}
)

# 2. src/services/service_factory.py:260
# In to_ui_response() na metadata.get("voorbeelden")
logger.debug(
    "Adapter: metadata.voorbeelden present=%s keys=%s",
    bool(metadata.get("voorbeelden")),
    list((metadata.get("voorbeelden") or {}).keys()) if isinstance(metadata.get("voorbeelden"), dict) else type(metadata.get("voorbeelden"))
)

# 3. src/ui/components/definition_generator_tab.py:940
# Voor _render_voorbeelden_section() aanroep
voorbeelden = agent_result.get("voorbeelden", {})
logger.debug(
    "UI: voorbeelden present=%s keys=%s sizes=%s",
    bool(voorbeelden),
    list((voorbeelden or {}).keys()) if isinstance(voorbeelden, dict) else type(voorbeelden),
    {k: (len(v) if isinstance(v, list) else len(v) if isinstance(v, str) else type(v).__name__) 
     for k, v in (voorbeelden or {}).items()}
)

# 4. src/ui/tabbed_interface.py (bij session state opslag)
logger.debug(
    "UI-store: voorbeelden keys=%s sizes=%s",
    list((agent_result.get("voorbeelden") or {}).keys()) if isinstance(agent_result.get("voorbeelden"), dict) else type(agent_result.get("voorbeelden")),
    {k: (len(v) if isinstance(v, list) else len(v) if isinstance(v, str) else type(v).__name__) 
     for k, v in (agent_result.get("voorbeelden") or {}).items()}
)
```

#### Stap 2: Test Scenario (15 min)
1. Start app met: `OPENAI_API_KEY="$OPENAI_API_KEY_PROD" PYTHONPATH=. streamlit run src/main.py --logger.level=debug`
2. Genereer definitie voor "verdachte"
3. Analyseer logs in volgorde: V2 → Adapter → UI-store → UI-render
4. Identificeer waar voorbeelden leeg worden

#### Stap 3: Fix Implementatie (1-2 uur)
Gebaseerd op logging resultaten, mogelijke fixes:
- Als leeg in V2: Check unified_voorbeelden generator
- Als leeg in Adapter: Check metadata doorvoer
- Als leeg in UI-store: Check agent_result constructie
- Als leeg in UI-render: Check conditionele rendering logica

### Verificatie
- [ ] Alle 6 voorbeeldtypes zichtbaar (voorbeeldzinnen, praktijk, tegen, synoniemen, antoniemen, toelichting)
- [ ] Correcte aantallen (5 voor synoniemen/antoniemen, 3 voor anderen, 1 voor toelichting)
- [ ] Prompts EN content beide zichtbaar

---

## Prioriteit 2: Cache Strategy Fix 🟡 BELANGRIJK

### Probleem
Cache key mist `example_type` waardoor verschillende types dezelfde cache entry gebruiken.

### Implementatie

#### Stap 1: Update Cache Key Generation (30 min)
**File**: `src/utils/cache.py`

```python
# Regel 79-88 vervangen door:
def _generate_cache_key(self, *args, **kwargs) -> str:
    """Generate cache key from function arguments including example_type."""
    # Extract example_type if present in args or kwargs
    example_type = None
    if args and hasattr(args[0], 'example_type'):
        example_type = args[0].example_type.value if hasattr(args[0].example_type, 'value') else str(args[0].example_type)
    elif 'example_type' in kwargs:
        example_type = kwargs['example_type']
    
    # Build key components
    key_parts = {
        "args": args,
        "kwargs": sorted(kwargs.items()),
        "example_type": example_type  # Explicitly include
    }
    
    content = json.dumps(key_parts, sort_keys=True, default=str)
    return hashlib.md5(content.encode()).hexdigest()
```

#### Stap 2: Implementeer TTL per Type (20 min)
**File**: `src/voorbeelden/unified_voorbeelden.py`

Voeg toe na regel 45:
```python
# Cache TTL configuratie per example type
CACHE_TTL_BY_TYPE = {
    ExampleType.SYNONIEMEN: 7200,      # 2 uur - verandert zelden
    ExampleType.ANTONIEMEN: 7200,      # 2 uur - verandert zelden  
    ExampleType.VOORBEELDZINNEN: 3600, # 1 uur - kan variëren
    ExampleType.PRAKTIJKVOORBEELDEN: 1800, # 30 min - context-afhankelijk
    ExampleType.TEGENVOORBEELDEN: 1800,    # 30 min - context-afhankelijk
    ExampleType.TOELICHTING: 900           # 15 min - zeer context-specifiek
}
```

#### Stap 3: Re-enable Caching (10 min)
Verwijder de cache disable in unified_voorbeelden.py en gebruik TTL:
```python
@cached(ttl=lambda req: CACHE_TTL_BY_TYPE.get(req.example_type, 3600))
def _generate_cached(self, request: ExampleRequest) -> list[str]:
    """Cached generation with type-specific TTL."""
    # Existing implementation
```

### Verificatie
- [ ] Test met zelfde begrip, verschillende example_types
- [ ] Verify verschillende cache keys worden gegenereerd
- [ ] Check dat synoniemen/antoniemen altijd 5 items returnen
- [ ] Verify cache hits in logs

---

## Prioriteit 3: Context Harmonisatie Fix 🟢 MINOR

### Probleem
Kleine inconsistentie in UI validatie context mapping.

### Implementatie (5 min)

**File**: `src/ui/tabbed_interface.py`
**Regel**: 921

```python
# VOOR (regel 921):
"wettelijk": context_data.get("wettelijke_basis", []),

# NA:
"wettelijk": wet_context,  # EPIC-010: Consistente variabele gebruik
```

### Verificatie
- [ ] Validatie gebruikt dezelfde context als generatie
- [ ] Geen functionele wijziging in gedrag
- [ ] Context consistent door hele flow

---

## Prioriteit 4: Legacy Routes Documentatie 🟢 DOCUMENTATIE

### Voor US-043 (Legacy routes removal)

#### Stap 1: Markeer Legacy in Code (10 min)

**File**: `src/integration/definitie_checker.py`
Voeg comment toe boven regels 205 en 255:
```python
# TODO: US-043 - Legacy DefinitieAgent pad, gebruik generate_with_integrated_service() voor V2
agent_result = self.agent.generate_definition(...)
```

**File**: `src/ui/components/orchestration_tab.py`
Voeg comment toe boven regel 48:
```python
# TODO: US-043 - Legacy DefinitieAgent gebruik, migreer naar V2 orchestrator
self.agent = self.DefinitieAgent(max_iterations=1)
```

#### Stap 2: Documenteer V2 Alternatief (15 min)

Maak notitie in code:
```python
# V2 ALTERNATIEF:
# from services.service_factory import get_definition_service
# service = get_definition_service()
# result = service.generate_definition(...)
```

---

## Test Protocol

### Smoke Test (5 min)
1. Genereer definitie voor "verdachte"
2. Check alle voorbeelden zichtbaar
3. Check synoniemen = 5 items
4. Valideer context wordt gebruikt

### Regression Test (10 min)
1. Test "Anders..." optie met custom context
2. Test meerdere begrippen achter elkaar
3. Check cache werkt (tweede keer sneller)
4. Verify geen errors in logs

### Performance Test (5 min)
1. Meet generatie tijd eerste keer
2. Meet generatie tijd met cache (moet <100ms zijn)
3. Check memory usage stabiel

---

## Rollout Plan

### Dag 1
- [ ] Implementeer debug logging (30 min)
- [ ] Run test scenario's (15 min)
- [ ] Identificeer root cause voorbeelden bug
- [ ] Implementeer fix voor voorbeelden (1-2 uur)
- [ ] Test voorbeelden fix

### Dag 2  
- [ ] Implementeer cache key fix (30 min)
- [ ] Implementeer TTL per type (20 min)
- [ ] Re-enable caching (10 min)
- [ ] Test cache functionaliteit
- [ ] Fix context harmonisatie (5 min)

### Dag 3
- [ ] Documenteer legacy routes (25 min)
- [ ] Run volledig test protocol
- [ ] Update documentatie
- [ ] Commit changes met duidelijke messages

---

## Success Criteria

- ✅ Alle voorbeelden types zichtbaar in UI
- ✅ Cache werkt correct met verschillende example types
- ✅ Context consistent door hele flow
- ✅ Legacy routes gedocumenteerd voor US-043
- ✅ Geen regressies in bestaande functionaliteit
- ✅ Performance gelijk of beter

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Voorbeelden fix breekt andere UI | HIGH | Uitgebreide testing, feature flag indien nodig |
| Cache fix veroorzaakt inconsistenties | MEDIUM | Gradual rollout, monitor cache hit rate |
| Context fix breekt validatie | LOW | Minimale change, goed getest |

---

## Notes

- Debug logging kan verwijderd worden na fix
- Cache monitoring blijft aan voor observability
- Legacy routes worden in EPIC-012 volledig gerefactored
- Overweeg feature flag voor cache re-enabling