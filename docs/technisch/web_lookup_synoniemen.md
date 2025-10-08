# Juridische Synoniemen & Query Optimization

**Status**: ✅ Geïmplementeerd (Oct 2025)
**Doel**: Verhoog web lookup coverage van 80% → 90% via juridische synoniemen en context-aware ranking

---

## Overzicht

Deze feature voegt drie nieuwe capabilities toe aan de web lookup stack:

1. **Juridische Synoniemen Database** - 60+ juridische begrippen met synoniemen
2. **Synonym Expansion** - Automatische query diversificatie voor Wikipedia + SRU
3. **Juridische Ranking Boost** - Context-aware prioritering van juridische content

**Impact**: Verwachte coverage verhoging van 80% naar 90% voor juridische begrippen.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  ModernWebLookupService                      │
│                     (Orchestrator)                           │
└───────────────┬─────────────────────────────────┬───────────┘
                │                                 │
        ┌───────▼────────┐              ┌────────▼──────────┐
        │ WikipediaService│              │   SRUService      │
        │                │              │                   │
        │ + Synonym      │              │ + Synonym Query 0 │
        │   Fallback     │              │   Expansion       │
        └───────┬────────┘              └────────┬──────────┘
                │                                │
                └────────┬───────────────────────┘
                         │
                ┌────────▼─────────────────┐
                │ JuridischeSynoniemlService│
                │                           │
                │ + Bidirectionele lookup   │
                │ + Query expansion         │
                └────────┬──────────────────┘
                         │
                ┌────────▼──────────────────┐
                │ juridische_synoniemen.yaml│
                │                           │
                │ 60+ begrippen + synoniemen│
                └───────────────────────────┘

                ┌───────────────────────────┐
                │  JuridischRanker          │
                │                           │
                │ + Keyword boost           │
                │ + Artikel-ref boost       │
                │ + Context matching        │
                └───────────────────────────┘
```

---

## Component 1: Juridische Synoniemen Database

**File**: `/config/juridische_synoniemen.yaml`

### Structuur

```yaml
# Hoofdterm (met underscores)
onherroepelijk:
  - kracht van gewijsde
  - rechtskracht
  - in kracht van gewijsde
  - definitieve uitspraak

voorlopige_hechtenis:
  - voorarrest
  - bewaring
  - inverzekeringstelling
```

### Categorieën

- **Strafrecht (Sv/Sr)**: verdachte, dagvaarding, schuldig, strafbaar feit, etc.
- **Bestuursrecht (Awb)**: beschikking, bezwaar, beroep, belanghebbende
- **Burgerlijk recht (BW/Rv)**: overeenkomst, wanprestatie, schadevergoeding
- **Procesrecht**: hoger beroep, cassatie, vonnis, getuige
- **Algemene begrippen**: rechtspersoon, verjaring, redelijkheid, opzet

**Totaal**: 60+ hoofdtermen met 200+ synoniemen

### Synoniemen toevoegen

1. Edit `config/juridische_synoniemen.yaml`
2. Voeg hoofdterm toe met underscores (`_`) voor spaties
3. Voeg synoniemen toe als YAML lijst
4. Service laadt automatisch bij herstart

**Voorbeeld**:

```yaml
nieuwe_term:
  - synoniem1
  - synoniem2
  - synoniem3
```

---

## Component 2: JuridischeSynoniemlService

**File**: `/src/services/web_lookup/synonym_service.py`

### Features

#### Bidirectionele Lookup

```python
service = get_synonym_service()

# Forward: hoofdterm → synoniemen
service.get_synoniemen("onherroepelijk")
# → ["kracht van gewijsde", "rechtskracht", ...]

# Reverse: synoniem → andere synoniemen + hoofdterm
service.get_synoniemen("kracht van gewijsde")
# → ["onherroepelijk", "rechtskracht", "in kracht van gewijsde", ...]
```

#### Query Expansion

```python
# Expand term met max N synoniemen voor query diversificatie
expanded = service.expand_query_terms("voorlopige hechtenis", max_synonyms=3)
# → ["voorlopige hechtenis", "voorarrest", "bewaring", "inverzekeringstelling"]
```

#### Check Synoniemen

```python
# Check of term synoniemen heeft
if service.has_synoniemen("verdachte"):
    # Gebruik synonym expansion
```

#### Text Analysis

```python
# Vind alle juridische termen in tekst
text = "De verdachte kreeg een onherroepelijke veroordeling"
matches = service.find_matching_synoniemen(text)
# → {
#     'verdachte': ['beklaagde', 'beschuldigde', ...],
#     'onherroepelijke': ['kracht van gewijsde', ...]
# }
```

### Singleton Pattern

```python
from .synonym_service import get_synonym_service

# Singleton instance (hergebruikt across calls)
service = get_synonym_service()

# Custom config path (creates new instance)
service = get_synonym_service(config_path="/custom/path/synoniemen.yaml")
```

---

## Component 3: Wikipedia Synonym Fallback

**File**: `/src/services/web_lookup/wikipedia_service.py`

### Workflow

```
1. Primaire search: "voorlopige hechtenis"
   ↓ (geen resultaten)

2. Synonym fallback enabled?
   ↓ YES

3. Expand query: ["voorarrest", "bewaring", "inverzekeringstelling"]
   ↓

4. Try synonym 1: "voorarrest"
   ↓ (SUCCESS!)

5. Return result
```

### Code

```python
# Enable synonym fallback (default: True)
async with WikipediaService(enable_synonyms=True) as wiki:
    result = await wiki.lookup("voorlopige hechtenis")
    # Probeert automatisch synoniemen als primaire search faalt

# Disable synonym fallback
async with WikipediaService(enable_synonyms=False) as wiki:
    result = await wiki.lookup("voorlopige hechtenis")
    # Alleen primaire search, geen fallback
```

### Logging

```
INFO: Wikipedia lookup voor term: voorlopige hechtenis
INFO: Primaire Wikipedia search gefaald, probeer synoniemen voor: voorlopige hechtenis
DEBUG: Wikipedia synonym fallback: probeer 'voorarrest'
INFO: Wikipedia match gevonden via synoniem: 'voorarrest' voor 'voorlopige hechtenis'
```

---

## Component 4: SRU Synonym Query Expansion

**File**: `/src/services/web_lookup/sru_service.py`

### Query 0: Juridische Synoniemen (NIEUW)

**Positie**: Eerste query (voor bestaande Query 1-6 cascade)

**Wanneer**: Alleen als `has_synoniemen(term) == True`

**Query structuur**:

```cql
(cql.serverChoice any "voorlopige hechtenis") OR
(cql.serverChoice any "voorarrest") OR
(cql.serverChoice any "bewaring") OR
(cql.serverChoice any "inverzekeringstelling")
```

### Query Cascade (Updated)

1. **Query 0**: Juridische synoniemen expansion (NIEUW)
2. **Query 1**: DC-velden (title/subject/description)
3. **Query 2**: serverChoice all
4. **Query 3**: Hyphen variant
5. **Query 4**: serverChoice any
6. **Query 5**: Prefix wildcard
7. **Query 6**: Partial words

### Circuit Breaker

- **Threshold**: 4 lege resultaten (configurable per provider)
- **Gedrag**: Stop cascade na N consecutive empty results
- **Query 0 telt mee** voor circuit breaker

### Code

```python
# Enable synonym expansion (default: True)
async with SRUService(enable_synonyms=True) as sru:
    results = await sru.search("voorlopige hechtenis", endpoint="overheid")
    # Probeert eerst synonym query (Query 0) als term synoniemen heeft

# Disable synonym expansion
async with SRUService(enable_synonyms=False) as sru:
    results = await sru.search("voorlopige hechtenis", endpoint="overheid")
    # Skip Query 0, start meteen bij Query 1
```

### Logging

```
INFO: Query 0: Juridische synoniemen expansion voor 'voorlopige hechtenis'
DEBUG: Synoniemen query: (cql.serverChoice any "voorlopige hechtenis") OR (cql.serverChoice any "voorarrest") OR ...
INFO: Synoniemen query SUCCESS: 3 resultaten voor 'voorlopige hechtenis'
```

---

## Component 5: Juridische Ranking Boost

**File**: `/src/services/web_lookup/juridisch_ranker.py`

### Boost Factoren

| Factor | Boost | Beschrijving |
|--------|-------|--------------|
| Juridische bron (rechtspraak.nl, overheid.nl) | **1.2x** | URL domain check |
| `source.is_juridical = True` | **1.15x** | Metadata flag |
| Juridisch keyword (per keyword) | **1.1x** | Max 1.3x (3 keywords) |
| Artikel-referentie (Art. X) | **1.15x** | Regex match |
| Lid-referentie | **1.05x** | Regex match |
| Context token match | **1.1x** | Per context match |

**Combinatie**: Factoren worden vermenigvuldigd (max ~1.8x boost mogelijk)

### Juridische Keywords

```python
JURIDISCHE_KEYWORDS = {
    # Algemeen: wetboek, artikel, recht, rechter, vonnis, ...
    # Strafrecht: verdachte, beklaagde, veroordeling, ...
    # Burgerlijk: overeenkomst, schadevergoeding, ...
    # Bestuursrecht: beschikking, bezwaar, beroep, ...
    # Procesrecht: procedure, hoger beroep, cassatie, ...
    # Wetten: sr, sv, rv, bw, awb
}
```

### Artikel/Lid Detection

**Artikel patterns**:
- `Artikel 123`
- `Art. 12a`
- `artikel 5`

**Lid patterns**:
- `lid 2`
- `tweede lid`
- `eerste lid`

### Usage

```python
from .juridisch_ranker import boost_juridische_resultaten

# Boost results met juridische ranking
boosted = boost_juridische_resultaten(
    results,
    context=["Sv", "strafrecht"]  # Optionele context voor extra boost
)

# Results zijn nu gesorteerd op gebooste confidence
```

### Context Matching

Als context tokens worden meegegeven, krijgen results extra boost:

```python
# Context: ["Sv", "strafrecht"]
# Definitie: "... het Wetboek van Strafvordering (Sv) bepaalt ..."
# → Extra 1.1x boost voor "Sv" match
# → Extra 1.1x boost voor "strafrecht" (impliciete match)
# → Totaal context boost: 1.21x
```

---

## Component 6: ModernWebLookupService Integration

**File**: `/src/services/modern_web_lookup_service.py`

### Ranking Pipeline

```
1. Concurrent lookups (Wikipedia, SRU, Wiktionary, etc.)
   ↓
2. rank_and_dedup() - Provider weight ranking
   ↓
3. context_filter.filter_results() - Context relevance
   ↓
4. boost_juridische_resultaten() - Juridische boost ← NIEUW
   ↓
5. Limiteer tot max_results
   ↓
6. Return final_results
```

### Context Token Classification

```python
# Context: "OM | Sv | strafrecht"
org, jur, wet = self._classify_context_tokens(context)

# org = ["OM"]           → Organisatorisch
# jur = ["strafrecht"]   → Juridisch
# wet = ["Sv"]           → Wettelijk (gemapped naar "Wetboek van Strafvordering")

# Combined voor juridische ranking
context_tokens = jur + wet  # ["strafrecht", "Wetboek van Strafvordering", "Sv"]
```

---

## Configuration

**File**: `/config/web_lookup_defaults.yaml`

```yaml
web_lookup:
  # Juridische synoniemen (NIEUW)
  synonyms:
    enabled: true
    config_path: "config/juridische_synoniemen.yaml"
    max_synonyms_per_query: 3

    # Juridische ranking boost factoren
    juridical_boost:
      juridische_bron: 1.2
      keyword_per_match: 1.1
      artikel_referentie: 1.15
      lid_referentie: 1.05
      context_match: 1.1

  providers:
    wikipedia:
      enabled: true
      weight: 0.7

    sru_overheid:
      enabled: true
      weight: 1.0  # Hoogste voor juridische content
```

### Environment Variables

```bash
# Disable synoniemen (voor debugging)
DISABLE_WEB_LOOKUP_SYNONYMS=1

# Custom synoniemen config
SYNONYM_CONFIG_PATH=/custom/path/synoniemen.yaml
```

---

## Testing

### Unit Tests

```bash
# Test synonym service
pytest tests/web_lookup/test_synonym_service.py

# Test juridische ranker
pytest tests/web_lookup/test_juridisch_ranker.py

# Test Wikipedia synonym fallback
pytest tests/web_lookup/test_wikipedia_synonyms.py

# Test SRU synonym expansion
pytest tests/web_lookup/test_sru_synonyms.py
```

### Integration Tests

```bash
# Test volledige lookup pipeline
pytest tests/web_lookup/test_synonym_integration.py
```

### Manual Testing

```python
import asyncio
from src.services.modern_web_lookup_service import ModernWebLookupService
from src.services.interfaces import LookupRequest

async def test_synonym_lookup():
    service = ModernWebLookupService()

    # Test juridische term met synoniemen
    request = LookupRequest(
        term="voorlopige hechtenis",
        context="Sv | strafrecht",
        max_results=5
    )

    results = await service.lookup(request)

    for r in results:
        print(f"Source: {r.source.name} (confidence: {r.source.confidence:.2f})")
        print(f"Definition: {r.definition[:100]}...")
        print("---")

asyncio.run(test_synonym_lookup())
```

---

## Performance Impact

### Expected Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Coverage** | 80% | 90% | +10% |
| **Juridische begrippen recall** | 75% | 88% | +13% |
| **Wikipedia fallback success** | 15% | 35% | +20% |
| **SRU synonym hits** | N/A | 25% | NEW |

### Query Overhead

- **Wikipedia**: +0-3 extra queries (alleen bij primaire search failure)
- **SRU**: +1 query (Query 0, alleen voor termen met synoniemen)
- **Latency**: +50-200ms (alleen bij fallback activation)

### Circuit Breaker Protection

- Max 4 consecutive empty results (configurable)
- Voorkomt excessive querying bij termen zonder resultaten

---

## Debugging

### Logging

**Enable debug logging**:

```python
import logging
logging.getLogger("src.services.web_lookup").setLevel(logging.DEBUG)
```

**Key log messages**:

```
# Wikipedia synonym fallback
INFO: Primaire Wikipedia search gefaald, probeer synoniemen voor: [term]
DEBUG: Wikipedia synonym fallback: probeer '[synonym]'
INFO: Wikipedia match gevonden via synoniem: '[synonym]' voor '[term]'

# SRU synonym expansion
INFO: Query 0: Juridische synoniemen expansion voor '[term]'
DEBUG: Synoniemen query: (cql.serverChoice any "...") OR ...
INFO: Synoniemen query SUCCESS: N resultaten voor '[term]'

# Juridische ranking
INFO: Juridische ranking boost applied to N results
DEBUG: Boosted '[term]' from 0.85 to 0.95 (boost: 1.12x)
```

### Synonym Service Stats

```python
from src.services.web_lookup.synonym_service import get_synonym_service

service = get_synonym_service()
stats = service.get_stats()

print(stats)
# {
#   'hoofdtermen': 60,
#   'totaal_synoniemen': 220,
#   'unieke_synoniemen': 220,
#   'gemiddeld_per_term': 3.67
# }
```

---

## Troubleshooting

### Issue: Geen synoniemen gevonden

**Check**:
1. `config/juridische_synoniemen.yaml` bestaat?
2. Term staat in YAML met underscores? (`voorlopige_hechtenis`)
3. YAML valid? Run `python -c "import yaml; yaml.safe_load(open('config/juridische_synoniemen.yaml'))"`

### Issue: Synoniemen niet gebruikt

**Check**:
1. `enable_synonyms=True` in WikipediaService/SRUService?
2. Logging enabled? Check `INFO: synoniemen fallback` messages
3. Circuit breaker triggered early? Check circuit breaker logs

### Issue: Slechte ranking

**Check**:
1. Juridische ranking enabled in ModernWebLookupService?
2. Context tokens correct geclassificeerd? (Check `_classify_context_tokens`)
3. Juridische keywords up-to-date in `juridisch_ranker.py`?

---

## Future Improvements

1. **ML-based Synonym Expansion**
   - Train embeddings op juridische corpus
   - Dynamische synoniemen generatie

2. **User Feedback Loop**
   - Track welke synoniemen leiden tot goede matches
   - Auto-tune synonym rankings

3. **Domain-Specific Tuning**
   - Separate synoniemen sets voor strafrecht, bestuursrecht, civiel
   - Context-aware synonym selection

4. **Synonym Confidence Scoring**
   - Niet alle synoniemen zijn even relevant
   - Weighted synonym expansion

---

## References

- **Synoniemen database**: `/config/juridische_synoniemen.yaml`
- **Service code**: `/src/services/web_lookup/synonym_service.py`
- **Ranker code**: `/src/services/web_lookup/juridisch_ranker.py`
- **Wikipedia integration**: `/src/services/web_lookup/wikipedia_service.py`
- **SRU integration**: `/src/services/web_lookup/sru_service.py`
- **Orchestrator**: `/src/services/modern_web_lookup_service.py`
- **Config**: `/config/web_lookup_defaults.yaml`

---

**Last Updated**: Oct 2025
**Maintainer**: DefinitieAgent Team
