# EPIC-010 Verfijnd Implementatieplan - Context Flow & Orchestration Fixes

## Overzicht
Verfijnd actieplan op basis van review feedback.

**Datum**: 2025-01-10  
**Status**: READY FOR IMPLEMENTATION  
**Geschatte doorlooptijd**: 2-3 dagen

---

## Prioriteit 1: Voorbeelden UI Bug - Logging & Diagnose 🔴 KRITIEK

### Verfijnde Logging Implementatie

#### Environment Flag Setup
```bash
# Start met debug logging
DEBUG_EXAMPLES=true OPENAI_API_KEY="$OPENAI_API_KEY_PROD" streamlit run src/main.py
```

#### Logging Points met Generation ID & Counts

```python
# 1. src/services/orchestrators/definition_orchestrator_v2.py:439
if os.getenv('DEBUG_EXAMPLES'):
    logger.info(
        "[EXAMPLES-A] V2 generated | gen_id=%s | begrip=%s | keys=%s | counts=%s",
        generation_id,
        sanitized_request.begrip,
        list(voorbeelden.keys()) if isinstance(voorbeelden, dict) else "NOT_DICT",
        {k: len(v) if isinstance(v, (list, str)) else "INVALID" 
         for k, v in (voorbeelden or {}).items()}
    )

# 2. src/services/service_factory.py:260
if os.getenv('DEBUG_EXAMPLES'):
    logger.info(
        "[EXAMPLES-B] Adapter | gen_id=%s | metadata.voorbeelden=%s | ui_keys=%s",
        metadata.get('generation_id'),
        "present" if metadata.get("voorbeelden") else "missing",
        list((voorbeelden or {}).keys()) if isinstance(voorbeelden, dict) else "NOT_DICT"
    )

# 3. src/ui/tabbed_interface.py - VOOR SessionStateManager.set_value
if os.getenv('DEBUG_EXAMPLES'):
    logger.info(
        "[EXAMPLES-C] Pre-store | gen_id=%s | voorbeelden=%s | counts=%s",
        agent_result.get('metadata', {}).get('generation_id'),
        "present" if agent_result.get("voorbeelden") else "missing",
        {k: len(v) if isinstance(v, (list, str)) else "INVALID" 
         for k, v in (agent_result.get("voorbeelden") or {}).items()}
    )

# 4. src/ui/tabbed_interface.py - NA SessionStateManager.set_value
if os.getenv('DEBUG_EXAMPLES'):
    stored = SessionStateManager.get_value("last_generation_result", {})
    logger.info(
        "[EXAMPLES-C2] Post-store | gen_id=%s | stored.voorbeelden=%s",
        stored.get('metadata', {}).get('generation_id'),
        "present" if stored.get("voorbeelden") else "missing"
    )

# 5. src/ui/components/definition_generator_tab.py:940
if os.getenv('DEBUG_EXAMPLES'):
    logger.info(
        "[EXAMPLES-D] UI-render | gen_id=%s | voorbeelden=%s | counts=%s",
        agent_result.get('metadata', {}).get('generation_id'),
        "present" if voorbeelden else "missing",
        {k: len(v) if isinstance(v, (list, str)) else "INVALID" 
         for k, v in (voorbeelden or {}).items()}
    )
```

### Diagnose Protocol
1. Start app met `DEBUG_EXAMPLES=true`
2. Genereer definitie voor "verdachte"
3. Analyseer logs: A→B→C→C2→D
4. Identificeer waar voorbeelden leeg wordt

### Interpretatie Matrix
| Leeg bij | Oorzaak | Fix |
|----------|---------|-----|
| A | Generator probleem | Check unified_voorbeelden |
| B | Metadata doorvoer | Check orchestrator→adapter |
| C | Pre-store constructie | Check agent_result building |
| C2 | State overschrijving | Check SessionState logic |
| D | Render pad | Check conditionele UI logic |

---

## Prioriteit 2: Cache Strategy - Voorbereiding 🟡 BELANGRIJK

### Verfijnde Cache Key Design

```python
def _generate_cache_key(self, *args, **kwargs) -> str:
    """Generate robust cache key with versioning."""
    
    # Extract key components
    if args and hasattr(args[0], 'example_type'):
        request = args[0]
        key_parts = [
            "v2",  # Version salt for schema changes
            request.example_type.value,
            hashlib.md5(request.begrip.lower().encode()).hexdigest()[:8],
            hashlib.md5(request.definitie.encode()).hexdigest()[:8],
            str(request.max_examples),
            request.model or "default",
            str(request.temperature or 0.7)[:3],
            hashlib.md5(json.dumps(request.context_dict, sort_keys=True).encode()).hexdigest()[:8]
        ]
    else:
        # Fallback for other cache uses
        key_parts = [
            "v2",
            hashlib.md5(str(args).encode()).hexdigest()[:16],
            hashlib.md5(json.dumps(kwargs, sort_keys=True, default=str).encode()).hexdigest()[:16]
        ]
    
    return "|".join(key_parts)
```

### Verfijnde TTL Matrix

```python
CACHE_TTL_BY_TYPE = {
    ExampleType.SYNONIEMEN: 14400,      # 4 uur - zeer stabiel
    ExampleType.ANTONIEMEN: 14400,      # 4 uur - zeer stabiel
    ExampleType.VOORBEELDZINNEN: 3600,  # 1 uur - redelijk stabiel
    ExampleType.PRAKTIJKVOORBEELDEN: 1800,  # 30 min - context gevoelig
    ExampleType.TEGENVOORBEELDEN: 1800,     # 30 min - context gevoelig
    ExampleType.TOELICHTING: 1800           # 30 min - zeer context specifiek
}

# Cache invalidatie bij schema changes
CACHE_SCHEMA_VERSION = "2025-01-10-v1"  # Bump bij wijzigingen
```

### Cache Monitoring

```python
@dataclass
class CacheMetrics:
    hit_rate: float  # Target: >40% voor synoniemen/antoniemen
    avg_latency_ms: float  # Target: -20% vs baseline
    type_distribution: dict[str, int]  # Verificatie geen cross-type hits
```

---

## Prioriteit 3: Context Harmonisatie Fix 🟢 MINOR

### Concrete Fix

**File**: `src/ui/tabbed_interface.py`  
**Regels**: 919-921

```python
# VOOR:
contexten = {
    "organisatorisch": org_context,
    "juridisch": jur_context,
    "wettelijk": context_data.get("wettelijke_basis", []),  # ❌ Inconsistent
}

# NA:
contexten = {
    "organisatorisch": org_context,
    "juridisch": jur_context,
    "wettelijk": wet_context,  # ✅ Consistent met prompt flow
}
```

### Verificatie
- Validatie module krijgt exact dezelfde context als prompt flow
- Geen functionele wijziging, alleen harmonisatie

---

## Prioriteit 4: Legacy Routes Documentatie & Feature Flags 🟢 DOCUMENTATIE

### Integration Checker Marking

```python
# src/integration/definitie_checker.py
ENABLE_LEGACY_AGENT = os.getenv('ENABLE_LEGACY_AGENT', 'false').lower() == 'true'

def generate_definition(self, ...):
    if ENABLE_LEGACY_AGENT:
        # TODO: US-043/US-066 - Legacy DefinitieAgent pad
        logger.warning("Using legacy DefinitieAgent - migrate to V2")
        return self.agent.generate_definition(...)
    else:
        # V2 pad - standaard
        return self.generate_with_integrated_service(...)
```

### Orchestration Tab UI Banner

```python
# src/ui/components/orchestration_tab.py
def render(self):
    st.warning("⚠️ Legacy Orchestration Tab - Gebruik Definition Generator tab voor V2")
    
    if not os.getenv('ENABLE_LEGACY_TAB', 'false').lower() == 'true':
        st.info("Tab uitgeschakeld. Set ENABLE_LEGACY_TAB=true om te activeren.")
        return
    
    # Legacy rendering...
```

---

## Design Notes

### Cache Key Ontwerp Rationale
- **Version salt**: Schema wijzigingen invalideren oude entries
- **Hash lengtes**: 8 chars voor balans tussen uniqueness en key size
- **Context hash**: Voorkomt cache pollution bij verschillende contexts
- **Model/temp**: Verschillende modellen/temps = verschillende outputs

### TTL Rationale
- **Synoniemen/Antoniemen**: 4 uur - taal verandert niet snel
- **Voorbeeldzinnen**: 1 uur - redelijk stabiel
- **Praktijk/Tegen**: 30 min - context afhankelijk
- **Toelichting**: 30 min - zeer specifiek

---

## Acceptatiecriteria (Meetbaar)

### Voorbeelden Bug
- ✅ Logs tonen consistente keys/sizes door A→B→C→C2→D
- ✅ UI toont alle 6 typen
- ✅ Counts = DEFAULT_EXAMPLE_COUNTS
- ✅ Generation ID consistent door hele flow

### Cache (Bij Herinschakeling)
- ✅ Hit rate >40% voor synoniemen/antoniemen
- ✅ P95 latency -20% vs baseline
- ✅ Geen cross-type cache hits
- ✅ Cache metrics dashboard beschikbaar

### Stateless Services
- ✅ 0 streamlit imports in src/services/
- ✅ CI check fail bij UI dependencies in services
- ✅ Alle config via DI/constructor

### Legacy Routes
- ✅ Feature flags default "false"
- ✅ UI banners voor legacy tabs
- ✅ 0 referenties naar DefinitieAgent in default flow
- ✅ Monitoring voor legacy route gebruik

---

## Risico Mitigatie

### Test Impact
- **Risico**: Tests falen door legacy removal
- **Mitigatie**: Pariteits-suite met V1/V2 vergelijking

### Cache Herinschakeling
- **Risico**: Performance regressie
- **Mitigatie**: Gradual rollout met monitoring

### UI Voorbeelden
- **Risico**: Fix breekt andere UI delen
- **Mitigatie**: Feature flag voor rollback

---

## CI/CD Checks

```yaml
# .github/workflows/epic-010-checks.yml
- name: Check No UI Dependencies in Services
  run: |
    if grep -r "import streamlit" src/services/; then
      echo "ERROR: Streamlit imports found in services"
      exit 1
    fi

- name: Check Legacy Routes Disabled
  run: |
    if ! grep "ENABLE_LEGACY_AGENT.*false" src/integration/definitie_checker.py; then
      echo "ERROR: Legacy agent not disabled by default"
      exit 1
    fi
```

---

## Volgende Stappen

1. **Vandaag**: Implementeer debug logging met env flag
2. **Vandaag**: Run diagnose, rapporteer waar voorbeelden leeg wordt
3. **Morgen**: Implementeer cache key/TTL design (niet activeren)
4. **Morgen**: Apply context harmonisatie (1 regel)
5. **Overmorgen**: Feature flags voor legacy routes
6. **Later**: Activeer cache na succesvolle tests