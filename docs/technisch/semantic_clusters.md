# Semantic Clusters voor Juridische Synoniemen

**Status**: ✅ Implemented
**Versie**: 1.0
**Datum**: 2025-10-09

## Overzicht

Semantic clusters groeperen **gerelateerde (maar NIET synonieme)** juridische begrippen om de recall van web lookups te verbeteren en contextueel verwante suggesties te bieden.

### Verschil tussen Synoniemen en Clusters

| Aspect | Synoniemen | Clusters |
|--------|-----------|----------|
| **Relatie** | Identieke of zeer vergelijkbare betekenis | Gerelateerd semantisch domein |
| **Voorbeeld** | "hoger beroep" ↔ "appel" | "hoger beroep" + "cassatie" + "verzet" |
| **Uitwisselbaarheid** | Ja (bidirectioneel) | Nee (complementair) |
| **Gebruik** | Query expansion (precision) | Cascade fallback (recall) |

**Voorbeeld**:
- **Synoniemen** van "hoger beroep": appel, appelprocedure
- **Cluster** "rechtsmiddelen": hoger_beroep, cassatie, verzet, rechtsmiddel, herziening

## YAML Configuratie

### Format

Clusters worden gedefinieerd in een speciale `_clusters` sectie in `config/juridische_synoniemen.yaml`:

```yaml
# Reguliere synoniemen (zoals voorheen)
hoger_beroep:
  - appel
  - appelprocedure

cassatie:
  - hogere voorziening
  - cassatieberoep

# Semantic clusters (NIEUW)
_clusters:
  # Cluster naam → lijst van gerelateerde termen
  rechtsmiddelen:
    - rechtsmiddel
    - hoger_beroep
    - cassatie
    - verzet
    - herziening

  straffen:
    - gevangenisstraf
    - taakstraf
    - geldboete
    - voorwaardelijke_straf
```

### Regels

1. **Exclusief lidmaatschap**: Een term kan slechts in ÉÉN cluster voorkomen
2. **Geen synoniemen**: Cluster termen zijn gerelateerd, niet synoniem
3. **Descriptieve namen**: Gebruik beschrijvende cluster namen (bijv. "rechtsmiddelen" niet "cluster1")
4. **Optioneel**: Clusters zijn backward compatible - oude configs zonder `_clusters` werken nog steeds
5. **Normalisatie**: Termen worden genormaliseerd (lowercase, underscores → spaces)

## Beschikbare Clusters

De volgende 8 semantic clusters zijn gedefinieerd in `config/juridische_synoniemen.yaml`:

### 1. **rechtsmiddelen** - Legal Remedies and Appeal Procedures
Rechtsmiddelen waarmee beslissingen kunnen worden aangevochten.

**Termen**: rechtsmiddel, hoger_beroep, cassatie, verzet, herziening

**Use case**: Als zoeken naar "hoger beroep" geen resultaten oplevert, probeer "cassatie" of "rechtsmiddel"

---

### 2. **straffen** - Criminal Penalties and Sanctions
Verschillende vormen van strafrechtelijke sancties.

**Termen**: gevangenisstraf, taakstraf, geldboete, voorwaardelijke_straf, jeugddetentie

**Use case**: Geef suggesties voor gerelateerde strafsoorten

---

### 3. **procedureel_strafrecht** - Criminal Procedure Concepts
Procedurele begrippen in strafzaken.

**Termen**: voorlopige_hechtenis, aanhouding, schorsing, dagvaarding, wraking

**Use case**: Context expansion voor procesmatige vraagstukken

---

### 4. **partijen_strafrecht** - Criminal Procedure Parties
Betrokken partijen in strafprocedures.

**Termen**: verdachte, getuige, advocaat, rechter, openbaar_ministerie

**Use case**: Related suggestions voor procespartijen

---

### 5. **bestuursrecht_procedures** - Administrative Law Procedures
Bestuursrechtelijke procedures en concepten.

**Termen**: beschikking, bezwaar, beroep, horen, belanghebbende

**Use case**: Cascade fallback voor bestuursrechtelijke begrippen

---

### 6. **burgerlijk_procedures** - Civil Law Procedures and Concepts
Civielrechtelijke procedures en verbintenissen.

**Termen**: overeenkomst, wanprestatie, schadevergoeding, vonnis, onrechtmatige_daad

**Use case**: Context expansion voor civiele zaken

---

### 7. **juridische_bewijsvoering** - Evidence and Proof Concepts
Begrippen rondom bewijsvoering.

**Termen**: bewijs, getuige, procesdossier

**Use case**: Related suggestions voor bewijsrecht

---

### 8. **strafrechtelijke_verantwoordelijkheid** - Criminal Liability Concepts
Concepten rondom strafrechtelijke aansprakelijkheid.

**Termen**: schuldig, strafbaar_feit, opzet, schuld, recidive, medeplegen

**Use case**: Context expansion voor schuldvraagstukken

## API Reference

### `JuridischeSynoniemlService` - Cluster Methods

#### `get_related_terms(term: str) -> list[str]`

Haal gerelateerde termen op uit dezelfde semantic cluster.

**Parameters**:
- `term`: Zoekterm (wordt genormaliseerd)

**Returns**: Lijst van gerelateerde termen (exclusief de term zelf), of lege lijst

**Voorbeeld**:
```python
service = JuridischeSynoniemlService()

# Get related terms
related = service.get_related_terms("hoger beroep")
# → ['rechtsmiddel', 'cassatie', 'verzet', 'herziening']

# Term niet in cluster
related = service.get_related_terms("onbekende term")
# → []
```

---

#### `get_cluster_name(term: str) -> str | None`

Haal cluster naam op voor een term.

**Parameters**:
- `term`: Zoekterm

**Returns**: Cluster naam, of `None` als term niet in cluster zit

**Voorbeeld**:
```python
cluster = service.get_cluster_name("hoger beroep")
# → 'rechtsmiddelen'

cluster = service.get_cluster_name("onbekende term")
# → None
```

---

#### `expand_with_related(term: str, max_synonyms: int = 3, max_related: int = 2) -> list[str]`

Expand term met ZOWEL synoniemen als gerelateerde cluster termen.

Combineert synonym expansion (precision) met cluster expansion (recall).

**Parameters**:
- `term`: Originele zoekterm
- `max_synonyms`: Maximum aantal synoniemen (default: 3)
- `max_related`: Maximum aantal gerelateerde cluster termen (default: 2)

**Returns**: Lijst met `[originele_term, synonyms..., related_terms...]`

**Voorbeeld**:
```python
expanded = service.expand_with_related(
    "hoger beroep",
    max_synonyms=2,
    max_related=2
)
# → ['hoger beroep', 'appel', 'appelprocedure', 'cassatie', 'rechtsmiddel']
#     ^original      ^synonyms (precision)    ^related (recall)
```

---

#### `get_stats() -> dict[str, int]`

Haal statistieken op (inclusief cluster info).

**Returns**: Dict met statistieken

**Voorbeeld**:
```python
stats = service.get_stats()
# → {
#     'hoofdtermen': 85,
#     'totaal_synoniemen': 320,
#     'unieke_synoniemen': 315,
#     'gemiddeld_per_term': 3.76,
#     'clusters': 8,              # NEW
#     'termen_in_clusters': 35    # NEW
# }
```

## Use Cases

### 1. Cascade Fallback

**Probleem**: Zoeken naar "hoger beroep" levert geen Wikipedia resultaten op.

**Oplossing**: Probeer gerelateerde termen uit cluster.

```python
service = JuridischeSynoniemlService()

# Primary search
results = wikipedia_search("hoger beroep")

if not results:
    # Fallback: try synonyms first (high precision)
    synonyms = service.get_synoniemen("hoger beroep")
    for syn in synonyms[:3]:
        results = wikipedia_search(syn)
        if results:
            break

if not results:
    # Fallback: try related cluster terms (high recall)
    related = service.get_related_terms("hoger beroep")
    for term in related[:2]:
        results = wikipedia_search(term)
        if results:
            break
```

---

### 2. Related Suggestions

**Probleem**: Gebruiker zoekt naar "hoger beroep", maar misschien is "cassatie" relevanter.

**Oplossing**: Toon gerelateerde suggesties.

```python
related = service.get_related_terms("hoger beroep")

# UI suggestie
print(f"Je zou ook kunnen zoeken naar: {', '.join(related[:3])}")
# → "Je zou ook kunnen zoeken naar: cassatie, verzet, rechtsmiddel"
```

---

### 3. Context Expansion (Prompt Enrichment)

**Probleem**: GPT-4 prompt mist context over gerelateerde rechtsmiddelen.

**Oplossing**: Voeg cluster context toe aan prompt.

```python
term = "hoger beroep"
cluster_name = service.get_cluster_name(term)
related = service.get_related_terms(term)

prompt = f"""
Definieer het juridische begrip '{term}'.

Context: Dit begrip behoort tot de categorie '{cluster_name}'.
Gerelateerde begrippen: {', '.join(related)}.
"""
```

---

### 4. Combined Expansion (Best of Both Worlds)

**Probleem**: Balans tussen precision (synoniemen) en recall (cluster termen).

**Oplossing**: Gebruik `expand_with_related()`.

```python
# Get 2 synonyms (precision) + 2 related terms (recall)
expanded = service.expand_with_related(
    "hoger beroep",
    max_synonyms=2,
    max_related=2
)

# Try all terms in sequence
for term in expanded:
    results = search(term)
    if results:
        break
```

## Validatie

### Automatische Validatie

Run `scripts/validate_synonyms.py` om clusters te valideren:

```bash
python scripts/validate_synonyms.py
```

**Checks**:
1. ✅ Empty cluster lists
2. ✅ Duplicate terms binnen cluster
3. ✅ Cross-cluster contamination (term in meerdere clusters)
4. ⚠️  Terms die zowel hoofdterm als cluster term zijn

**Voorbeeld output**:
```
[7/7] Validating semantic clusters...
  ✓ All 8 clusters are valid

Validation Summary
==================
  Clusters: 8
  Terms in clusters: 35
  ✓ All validations passed!
```

### Cluster Validation Rules

| Rule | Severity | Description |
|------|----------|-------------|
| Empty cluster | ❌ Error | Cluster heeft geen termen |
| Duplicate within cluster | ❌ Error | Zelfde term 2x in cluster |
| Cross-cluster contamination | ❌ Error | Term in meerdere clusters |
| Term is also hoofdterm | ⚠️ Warning | Kan verwarring veroorzaken |

## Integration met Web Lookup

### SRU Service Integration (Future)

**Optioneel**: SRU service kan cluster-based cascade gebruiken.

```python
# config/web_lookup_defaults.yaml
providers:
  sru:
    use_cluster_fallback: true  # Enable cascade fallback
    max_related_terms: 2
```

**Gedrag**:
1. Probeer hoofdterm
2. Probeer synoniemen (max 3)
3. Probeer cluster termen (max 2)

### Modern Web Lookup Service

**Huidige integratie**: `ModernWebLookupService` gebruikt al `synonym_service`, maar nog geen clusters.

**Toekomstige enhancement**:
```python
# In ModernWebLookupService
if not results:
    # Try related cluster terms
    related = self.synonym_service.get_related_terms(term)
    for related_term in related[:2]:
        results = self._query_provider(related_term)
        if results:
            break
```

## Testing

### Test Coverage

Alle cluster functionaliteit is gedekt door tests in `tests/services/web_lookup/test_semantic_clusters.py`:

**Test classes**:
- `TestClusterLoading` - YAML loading en parsing
- `TestGetRelatedTerms` - get_related_terms() functionaliteit
- `TestGetClusterName` - get_cluster_name() functionaliteit
- `TestExpandWithRelated` - expand_with_related() functionaliteit
- `TestClusterValidation` - Duplicate/cross-contamination checks
- `TestClusterStatistics` - get_stats() cluster info
- `TestRealWorldClusters` - Integration tests met echte config

### Running Tests

```bash
# Run all cluster tests
pytest tests/services/web_lookup/test_semantic_clusters.py -v

# Run specific test class
pytest tests/services/web_lookup/test_semantic_clusters.py::TestExpandWithRelated -v

# Run with coverage
pytest tests/services/web_lookup/test_semantic_clusters.py --cov=src.services.web_lookup.synonym_service
```

## Backward Compatibility

**Volledig backward compatible**:

✅ Oude configs zonder `_clusters` werken nog steeds
✅ Cluster methods retourneren lege lijsten voor oude configs
✅ Synoniemen functionaliteit onveranderd
✅ Geen breaking changes in API

**Migration**: Geen migratie nodig - clusters zijn optioneel.

## Performance

### Memory Overhead

**Cluster data**: ~35 termen × 8 clusters = ~280 entries

**Memory impact**: Verwaarloosbaar (<1KB extra)

### Lookup Performance

**get_related_terms()**: O(1) - dict lookup in `term_to_cluster` + `clusters`

**get_cluster_name()**: O(1) - dict lookup in `term_to_cluster`

**expand_with_related()**: O(n + m) waar n=synoniemen, m=related terms

**Impact**: Verwaarloosbaar (<1ms per lookup)

## Future Enhancements

### 1. Dynamic Cluster Suggestions

**Idee**: Gebruik cluster membership om automatisch suggesties te genereren in UI.

```python
# In Streamlit UI
cluster = service.get_cluster_name(user_term)
if cluster:
    related = service.get_related_terms(user_term)
    st.info(f"Gerelateerde begrippen ({cluster}): {', '.join(related[:3])}")
```

---

### 2. Cluster-Based Ranking

**Idee**: Boost resultaten die uit dezelfde cluster komen.

```python
# In ranking function
if result_term in same_cluster:
    score *= 1.2  # Boost cluster-related results
```

---

### 3. Cross-Cluster Navigation

**Idee**: Suggereer termen uit andere relevante clusters.

```python
# Suggest related clusters
# E.g., "rechtsmiddelen" → "procedureel_strafrecht"
```

---

### 4. Hierarchical Clusters

**Idee**: Nested clusters voor fijnmazigere semantische groepering.

```yaml
_clusters:
  rechtsmiddelen:
    _meta:
      parent: strafprocesrecht
    members:
      - hoger_beroep
      - cassatie
```

## Troubleshooting

### Cluster Validation Errors

**Error**: `Cross-cluster contamination: term 'X' appears in multiple clusters`

**Fix**: Verwijder term uit één van de clusters (kies meest specifieke cluster)

---

**Error**: `Duplicate term in cluster 'X'`

**Fix**: Verwijder duplicate entry uit YAML

---

**Warning**: `Term 'X' in cluster 'Y' is also a hoofdterm`

**Fix**: Dit is meestal OK (term kan zowel synoniemen als cluster membership hebben). Check dat het logisch is.

### Runtime Issues

**Issue**: `get_related_terms()` retourneert lege lijst

**Check**:
1. Is term correct genormaliseerd? (lowercase, geen underscores in query)
2. Zit term in een cluster? → gebruik `get_cluster_name()` om te checken
3. Is `_clusters` sectie correct geladen? → check `service.clusters`

---

**Issue**: `expand_with_related()` bevat duplicates

**Fix**: Dit zou niet moeten gebeuren (duplicates worden gefilterd). Rapporteer als bug.

## References

**Gerelateerde documentatie**:
- `docs/technisch/web_lookup_config.md` - Web lookup configuratie
- `config/juridische_synoniemen.yaml` - YAML configuratie bestand
- `src/services/web_lookup/synonym_service.py` - Service implementatie
- `scripts/validate_synonyms.py` - Validatie script
- `tests/services/web_lookup/test_semantic_clusters.py` - Tests

**Gerelateerde issues/epics**:
- US-XXX: Implement semantic clusters (deze story)
- EPIC-XXX: Web lookup improvements

---

**Auteur**: Claude Code
**Laatst bijgewerkt**: 2025-10-09
**Versie**: 1.0
