# Implementation Summary: Juridische Synoniemen & Query Optimization

**Date**: Oct 8, 2025
**Feature**: Wikipedia/Overheid.nl Web Lookup Improvements
**Goal**: 80% → 90% coverage via synoniemen + context-aware ranking

---

## ✅ Deliverables

### 1. Juridische Synoniemen Database
**File**: `/config/juridische_synoniemen.yaml`

- **60+ juridische begrippen** met 200+ synoniemen
- **Categorieën**: Strafrecht, Bestuursrecht, Burgerlijk recht, Procesrecht
- **Format**: YAML met bidirectionele lookup support
- **Voorbeelden**:
  - `onherroepelijk` → kracht van gewijsde, rechtskracht, definitieve uitspraak
  - `voorlopige_hechtenis` → voorarrest, bewaring, inverzekeringstelling
  - `verdachte` → beklaagde, beschuldigde, aangeklaagde

### 2. JuridischeSynoniemlService
**File**: `/src/services/web_lookup/synonym_service.py`

**Capabilities**:
- ✅ Bidirectionele lookup (term ↔ synoniemen)
- ✅ Query expansion (term + top-N synoniemen)
- ✅ Text analysis (vind juridische termen in tekst)
- ✅ Singleton pattern voor performance
- ✅ Graceful degradation (werkt zonder YAML)

**API**:
```python
service.get_synoniemen("onherroepelijk")  # → ["kracht van gewijsde", ...]
service.expand_query_terms("verdachte", max_synonyms=3)  # → ["verdachte", "beklaagde", ...]
service.has_synoniemen("voorlopige hechtenis")  # → True
service.get_stats()  # → {'hoofdtermen': 60, 'totaal_synoniemen': 220}
```

### 3. Wikipedia Synonym Fallback
**File**: `/src/services/web_lookup/wikipedia_service.py`

**Changes**:
- ✅ Toegevoegd: `__init__(enable_synonyms=True)` parameter
- ✅ Synonym service initialization in constructor
- ✅ Fallback logic in `lookup()` methode na primaire search
- ✅ Probeert max 3 synoniemen bij failure
- ✅ Logging voor debug/monitoring

**Flow**:
```
1. Primaire search "voorlopige hechtenis"
2. FAIL → trigger synonym fallback
3. Try "voorarrest" → SUCCESS
4. Return result met originele term preserved
```

### 4. SRU Synonym Query Expansion
**File**: `/src/services/web_lookup/sru_service.py`

**Changes**:
- ✅ Toegevoegd: `__init__(enable_synonyms=True)` parameter
- ✅ Query 0: Juridische synoniemen OR-query (NIEUW)
- ✅ Geplaatst VOOR bestaande Query 1-6 cascade
- ✅ Circuit breaker compatible (telt mee voor threshold)
- ✅ Alleen actief als `has_synoniemen(term) == True`

**Query 0 structure**:
```cql
(cql.serverChoice any "term") OR
(cql.serverChoice any "synoniem1") OR
(cql.serverChoice any "synoniem2") OR
(cql.serverChoice any "synoniem3")
```

### 5. JuridischRanker
**File**: `/src/services/web_lookup/juridisch_ranker.py`

**Boost factors**:
- ✅ Juridische bron (rechtspraak.nl, overheid.nl): **1.2x**
- ✅ `is_juridical` flag: **1.15x**
- ✅ Juridisch keyword (per keyword, max 1.3x): **1.1x**
- ✅ Artikel-referentie (Art. X): **1.15x**
- ✅ Lid-referentie: **1.05x**
- ✅ Context token match: **1.1x**

**Juridische keywords**: 50+ keywords (wetboek, artikel, verdachte, veroordeling, etc.)

**API**:
```python
boosted = boost_juridische_resultaten(results, context=["Sv", "strafrecht"])
score = get_juridische_score(result)  # 0.0 - 1.0
is_juridisch = is_juridische_bron("https://rechtspraak.nl/...")  # True
```

### 6. ModernWebLookupService Integration
**File**: `/src/services/modern_web_lookup_service.py`

**Changes**:
- ✅ Integrated `boost_juridische_resultaten()` in ranking pipeline
- ✅ Placed AFTER context filtering, BEFORE result limiting
- ✅ Extracts context tokens (jur + wet) voor ranking
- ✅ Graceful degradation (continues zonder boost bij errors)

**Ranking pipeline**:
```
1. rank_and_dedup()
2. context_filter.filter_results()
3. boost_juridische_resultaten()  ← NIEUW
4. limit(max_results)
```

### 7. Configuration
**File**: `/config/web_lookup_defaults.yaml`

**Added section**:
```yaml
web_lookup:
  synonyms:
    enabled: true
    config_path: "config/juridische_synoniemen.yaml"
    max_synonyms_per_query: 3
    juridical_boost:
      juridische_bron: 1.2
      keyword_per_match: 1.1
      artikel_referentie: 1.15
      lid_referentie: 1.05
      context_match: 1.1
```

### 8. Documentation
**Files**:
- ✅ `/docs/technisch/web_lookup_synoniemen.md` - Comprehensive tech docs (8000+ words)
- ✅ Inline docstrings in alle nieuwe modules
- ✅ Code comments voor complexe logica
- ✅ Usage examples in docstrings

---

## 🏗️ Architecture

```
ModernWebLookupService (orchestrator)
  ├── WikipediaService
  │   ├── _search_page()
  │   └── [SYNONYM FALLBACK] → JuridischeSynoniemlService
  │
  ├── SRUService
  │   ├── search()
  │   │   ├── [Query 0: SYNONYM EXPANSION] → JuridischeSynoniemlService
  │   │   ├── Query 1: DC fields
  │   │   ├── Query 2-6: Existing cascade
  │   │   └── Circuit breaker
  │
  └── [RANKING PIPELINE]
      ├── rank_and_dedup()
      ├── context_filter.filter_results()
      └── boost_juridische_resultaten() → JuridischRanker
```

---

## 📊 Expected Impact

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| **Overall Coverage** | 80% | 90% | **+10%** |
| **Juridische begrippen** | 75% | 88% | **+13%** |
| **Wikipedia fallback success** | 15% | 35% | **+20%** |
| **SRU synonym hits** | N/A | 25% | NEW |

**Query overhead**:
- Wikipedia: +0-3 queries (only on primary failure)
- SRU: +1 query (Query 0, only for terms with synonyms)
- Latency: +50-200ms (only when fallback activates)

---

## 🧪 Testing Strategy

### Unit Tests (To Be Created)

```bash
# Synonym service
tests/web_lookup/test_synonym_service.py
  - test_bidirectional_lookup()
  - test_expand_query_terms()
  - test_has_synoniemen()
  - test_yaml_loading()

# Juridisch ranker
tests/web_lookup/test_juridisch_ranker.py
  - test_boost_calculation()
  - test_juridische_keywords()
  - test_artikel_detection()
  - test_context_matching()

# Wikipedia integration
tests/web_lookup/test_wikipedia_synonyms.py
  - test_synonym_fallback()
  - test_primary_search_success()
  - test_no_synonyms_available()

# SRU integration
tests/web_lookup/test_sru_synonyms.py
  - test_query_0_expansion()
  - test_circuit_breaker_with_synonyms()
  - test_synonym_or_query()
```

### Integration Tests

```bash
tests/web_lookup/test_synonym_integration.py
  - test_end_to_end_lookup()
  - test_ranking_pipeline()
  - test_context_aware_boost()
```

### Manual Testing

```python
# Test juridische term met synoniemen
python scripts/test_web_lookup.py "voorlopige hechtenis" --context "Sv"

# Test ranking boost
python scripts/test_web_lookup.py "onherroepelijk" --show-scores

# Test synonym expansion
python scripts/test_web_lookup.py "verdachte" --debug
```

---

## 🚀 Deployment Checklist

- [x] Code implemented
- [x] Synoniemen database created (60+ terms)
- [x] Configuration updated
- [x] Documentation written
- [ ] Unit tests created
- [ ] Integration tests created
- [ ] Manual testing performed
- [ ] Code review
- [ ] Performance benchmarking
- [ ] Deployment to staging
- [ ] A/B testing (optional)
- [ ] Production deployment

---

## 🐛 Known Limitations

1. **Synoniemen database incomplete**
   - Start: 60 termen
   - Doel: 200 termen
   - Action: Iteratief uitbreiden op basis van feedback

2. **No ML-based expansion**
   - Huidige implementatie: statische YAML
   - Future: embeddings-based dynamic expansion

3. **No synonym confidence scoring**
   - Alle synoniemen krijgen gelijke weight
   - Future: weighted synoniemen op basis van relevantie

4. **Circuit breaker conflicts**
   - Query 0 telt mee voor empty result threshold
   - Kan early termination veroorzaken voor rare terms
   - Mitigation: verhoogde threshold naar 4

---

## 🔍 Monitoring

### Key Metrics

Track in logs/analytics:

1. **Synonym usage rate**
   - % queries die synonym fallback triggeren
   - Which synoniemen worden het meest gebruikt

2. **Success rate**
   - % synonym fallbacks die resulteren in hit
   - Per synonym success rate

3. **Ranking impact**
   - Average boost factor
   - % results met juridische boost > 1.1x

4. **Performance**
   - Latency impact van synonym queries
   - Circuit breaker activation rate

### Log Analysis

```bash
# Grep voor synonym fallback usage
grep "synoniemen fallback" logs/web_lookup.log | wc -l

# Grep voor Query 0 success
grep "Synoniemen query SUCCESS" logs/web_lookup.log

# Grep voor juridische boost
grep "Juridische ranking boost applied" logs/web_lookup.log
```

---

## 📝 Next Steps

### Short-term (Week 1-2)

1. **Create unit tests** voor alle nieuwe modules
2. **Manual testing** met 20+ juridische termen
3. **Performance benchmarking** (latency, circuit breaker)
4. **Code review** met team

### Mid-term (Week 3-4)

1. **Expand synoniemen database** naar 100+ termen
2. **A/B testing** in staging environment
3. **Fine-tune boost factors** op basis van feedback
4. **Monitor metrics** in production

### Long-term (Month 2-3)

1. **User feedback loop** - track welke synoniemen werken
2. **ML-based expansion** - train embeddings op juridische corpus
3. **Domain-specific tuning** - separate sets voor strafrecht/bestuursrecht
4. **Synonym confidence scoring** - weighted expansion

---

## 🤝 Dependencies

### Python Packages

- `PyYAML` - Voor synoniemen config loading
- `aiohttp` - Voor async Wikipedia/SRU calls (bestaand)

### Configuration Files

- `config/juridische_synoniemen.yaml` - Synoniemen database
- `config/web_lookup_defaults.yaml` - Feature config

### Services

- `WikipediaService` - Modified voor synonym fallback
- `SRUService` - Modified voor Query 0 expansion
- `ModernWebLookupService` - Modified voor juridische ranking

---

## 📚 References

- **Tech docs**: `/docs/technisch/web_lookup_synoniemen.md`
- **Synoniemen DB**: `/config/juridische_synoniemen.yaml`
- **Implementation**: See "Deliverables" section above

---

**Implementation Status**: ✅ **COMPLETE**
**Testing Status**: ⏳ **PENDING**
**Deployment Status**: ⏳ **PENDING**

---

**Implementor**: Claude Code
**Date**: Oct 8, 2025
**Review**: Pending
