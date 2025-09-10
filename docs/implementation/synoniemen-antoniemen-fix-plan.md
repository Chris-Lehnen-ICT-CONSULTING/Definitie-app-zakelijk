# Implementatieplan: Synoniemen/Antoniemen & Context Flow Fixes

## Overzicht
Dit document beschrijft het plan voor het oplossen van drie samenhangende problemen:
1. Cache strategie voor voorbeelden (synoniemen/antoniemen)
2. Context flow issues uit EPIC-010
3. Verificatie dat ChatGPT consistent 5 items teruggeeft

## ✅ UPDATE: Synoniemen/Antoniemen Werken!
**Status:** De vereenvoudigde prompts genereren nu correct 5 synoniemen en 5 antoniemen.

**Werkende oplossingen:**
- Vereenvoudigde prompts zonder overbodige context
- UI kan zowel lijsten als strings verwerken
- Parser krijgt correct example_type mee
- Cache tijdelijk uitgeschakeld

**Belangrijke bevinding:** Context komt WEL degelijk in de prompts terecht (zie docs/backlog prompts).
EPIC-010 context flow probleem lijkt dus niet te bestaan of al opgelost te zijn.

## 1. Betere Cache Strategie Implementeren

### Probleem
De huidige cache gebruikt alleen functie argumenten als key, maar mist het `example_type`.
Dit zorgt ervoor dat verschillende types (synoniemen vs antoniemen) dezelfde cache entry gebruiken.

### Oplossing

#### Stap 1: Update Cache Key Generation
**Locatie:** `src/utils/cache.py`
```python
def _generate_cache_key(self, func_name: str, request: ExampleRequest) -> str:
    """Generate unique cache key including example type."""
    key_parts = [
        func_name,
        request.begrip,
        request.example_type.value,  # BELANGRIJK: Include type
        str(request.max_examples),
        request.generation_mode.value
    ]
    return hashlib.md5("_".join(key_parts).encode()).hexdigest()
```

#### Stap 2: Implement TTL per Example Type
**Locatie:** `src/voorbeelden/unified_voorbeelden.py`
```python
CACHE_TTL_BY_TYPE = {
    ExampleType.SYNONIEMEN: 7200,      # 2 uur - verandert zelden
    ExampleType.ANTONIEMEN: 7200,      # 2 uur - verandert zelden
    ExampleType.VOORBEELDZINNEN: 3600, # 1 uur - kan variëren
    ExampleType.PRAKTIJKVOORBEELDEN: 1800, # 30 min - context-afhankelijk
    ExampleType.TEGENVOORBEELDEN: 1800,    # 30 min - context-afhankelijk
    ExampleType.TOELICHTING: 900           # 15 min - zeer context-specifiek
}
```

#### Stap 3: Re-enable Caching met Fix
```python
@cached(ttl=lambda req: CACHE_TTL_BY_TYPE.get(req.example_type, 3600))
def _generate_cached(self, request: ExampleRequest) -> list[str]:
    """Cached generation with type-specific TTL."""
    cache_key = self._generate_cache_key("voorbeelden", request)
    # Rest of implementation
```

### Verificatie
- Unit test met zelfde begrip, verschillende types
- Check dat cache keys verschillend zijn
- Verify TTL per type werkt correct

## 2. Context Flow Issues uit EPIC-010

### Analyse van het Probleem
Volgens EPIC-010 worden context velden (juridische_context, wettelijke_basis, organisatorische_context)
wel verzameld in de UI maar NIET doorgegeven aan de AI prompts.

### User Stories te Implementeren

#### US-041: Fix Context Field Mapping to Prompts (KRITIEK)
**Probleem:** Context verdwijnt tussen UI en prompt generatie

**Fix Locaties:**
1. `src/services/prompts/prompt_service_v2.py` (lines 158-176)
   - Update `_convert_request_to_context()` method
   - Map UI fields naar prompt context

2. `src/ui/tabbed_interface.py`
   - Verify context wordt correct doorgegeven in GenerationRequest

3. `src/services/definition_generator_context.py`
   - Ensure context fields zijn aanwezig in dataclass

**Implementatie:**
```python
def _convert_request_to_context(self, request: GenerationRequest) -> dict:
    """Convert request to context dict WITH all context fields."""
    return {
        'begrip': request.begrip,
        'organisatie': request.organisatie,
        # NIEUW: Map alle context velden
        'organisatorische_context': request.organisatorische_context or [],
        'juridische_context': request.juridische_context or [],
        'wettelijke_basis': request.wettelijke_basis or [],
    }
```

#### US-042: Fix "Anders..." Custom Context Option (KRITIEK)
**Probleem:** Custom context entry crashes met "default value not part of options"

**Fix Locatie:** `src/ui/components/context_selector.py` (lines 137-183)

**Implementatie:**
```python
def handle_custom_context(selected_values: list, custom_text: str) -> list:
    """Handle 'Anders...' option properly."""
    if "Anders..." in selected_values and custom_text:
        # Remove 'Anders...' from list
        selected_values = [v for v in selected_values if v != "Anders..."]
        # Add custom text
        selected_values.append(custom_text)
    return selected_values
```

#### US-043: Remove Legacy Context Routes (HOOG)
**Legacy routes te verwijderen:**
1. Direct `context` field (string) - DEPRECATED
2. `domein` field separate from context - DEPRECATED
3. V1 orchestrator context passing - REMOVED
4. Session state context storage - REFACTOR

**Implementatie:**
- Identificeer alle legacy paths
- Create migration functions
- Update alle references
- Remove deprecated code

### Data Flow Fix
**Huidige flow (BROKEN):**
```
UI → Session State → [LOST] → GenerationRequest → PromptService → Empty Prompt
```

**Target flow (FIXED):**
```
UI → Validated Context Lists → GenerationRequest → PromptService → Complete Prompt
```

## 3. Test Plan voor 5 Items Verificatie

### Automated Test Suite
**Locatie:** `tests/test_voorbeelden_generation.py`

```python
@pytest.mark.parametrize("begrip,expected_count", [
    ("verdachte", 5),
    ("rechter", 5),
    ("strafbaar feit", 5),
])
def test_synoniemen_always_returns_5(begrip, expected_count):
    """Verify synoniemen generation always returns exactly 5 items."""
    result = genereer_synoniemen(begrip, "", {})
    assert len(result) == expected_count
    assert all(isinstance(item, str) for item in result)
    assert all(len(item) > 1 for item in result)
```

### Manual Test Protocol
1. **Test verschillende begrippen:**
   - Simpele termen: "verdachte", "rechter"
   - Complexe termen: "strafbaar feit", "voorlopige hechtenis"
   - Rare termen: "hoger beroep", "cassatie"

2. **Test met/zonder context:**
   - Zonder context: alleen begrip
   - Met organisatorische context
   - Met juridische context
   - Met alle context types

3. **Test caching:**
   - Eerste request: check 5 items
   - Tweede request (cached): verify nog steeds 5 items
   - Clear cache, test opnieuw

### Monitoring & Logging
```python
# Add monitoring in _parse_response
if is_synonym_or_antonym:
    logger.info(f"Parsing {example_type}: Raw response has {len(lines)} lines")
    logger.info(f"After filtering: {len(examples)} items")
    if len(examples) != 5:
        logger.warning(f"Expected 5 {example_type} but got {len(examples)}")
```

## Implementatie Volgorde

### Fase 1: Quick Wins (1-2 uur)
1. ✅ Re-enable caching met betere key generation
2. ✅ Add debug logging voor monitoring
3. ✅ Create basic test suite

### Fase 2: Context Flow (3-4 uur)
1. ⏳ Fix US-041: Context field mapping
2. ⏳ Fix US-042: "Anders..." option
3. ⏳ Add context validation

### Fase 3: Clean-up (2-3 uur)
1. ⏳ Remove legacy routes (US-043)
2. ⏳ Consolidate context handling
3. ⏳ Update documentation

### Fase 4: Verificatie (1 uur)
1. ⏳ Run full test suite
2. ⏳ Manual testing protocol
3. ⏳ Performance check

## Success Criteria

### Technisch
- [ ] Cache keys bevatten example_type
- [ ] Context fields verschijnen in prompts
- [ ] "Anders..." optie werkt zonder crashes
- [ ] Altijd exact 5 synoniemen/antoniemen

### Business
- [ ] Definities bevatten juridische context
- [ ] Gebruikers kunnen custom context invoeren
- [ ] Performance blijft onder 5 seconden
- [ ] Zero context-gerelateerde errors in logs

## Risico's & Mitigatie

### Risico 1: Breaking Changes
**Mitigatie:** Gebruik feature flags voor geleidelijke rollout

### Risico 2: Performance Impact
**Mitigatie:** Monitor response times, optimaliseer cache TTL

### Risico 3: ChatGPT Inconsistentie
**Mitigatie:** Retry logic met fallback naar minder items

## Dependencies
- EPIC-010 implementation
- CFR-BUG-003 moet eerst opgelost zijn (GenerationResult import)
- Test framework moet operationeel zijn

## Geschatte Tijdsinvestering
- **Totaal:** 7-10 uur
- **Cache Fix:** 1-2 uur
- **Context Flow:** 3-4 uur
- **Testing:** 2-3 uur
- **Documentation:** 1 uur
