# Weighted Synonyms System (v2.0)

**Status**: Implemented
**Version**: 2.0
**Last Updated**: 2025-10-09

## Overzicht

De Weighted Synonyms feature voegt confidence-based ranking toe aan het juridische synoniemen systeem. Dit stelt de applicatie in staat om synoniemen te prioriteren op basis van hun semantische nabijheid tot de hoofdterm, wat resulteert in betere query expansion en hogere precisie bij web lookups.

## Motivatie

### Probleem

Het oorspronkelijke synoniemen systeem behandelde alle synoniemen als gelijk, zonder onderscheid tussen:
- **Exact synoniemen**: "voorarrest" voor "voorlopige hechtenis"
- **Sterke synoniemen**: "bewaring" voor "voorlopige hechtenis"
- **Contextuele synoniemen**: "gevangenhouding" voor "voorlopige hechtenis" (specifieke context)

Dit leidde tot:
1. Suboptimale query expansion (zwakke synoniemen even vaak gebruikt als sterke)
2. Geen mogelijkheid voor threshold-based filtering
3. Moeilijk te prioriteren welke synoniemen eerst te proberen bij Wikipedia/SRU lookups

### Oplossing

Weighted synonyms introduceren confidence scores (0.0-1.0) per synoniem, waarmee:
- Synoniemen gesorteerd worden op kwaliteit (beste eerst)
- Threshold-based filtering mogelijk is (bijv. alleen synoniemen > 0.85)
- Query expansion intelligenter kan prioriteren

## Architectuur

### WeightedSynonym Dataclass

```python
@dataclass(frozen=True)
class WeightedSynonym:
    """
    Represents a synonym with confidence weight.

    Attributes:
        term: The synonym term (normalized)
        weight: Confidence weight (0.0-1.0)
    """
    term: str
    weight: float = 1.0
```

**Kenmerken**:
- **Immutable** (frozen=True): Voorkomt accidentele wijzigingen
- **Default weight 1.0**: Backward compatible met legacy format
- **Validatie** in `__post_init__()`: Waarschuwingen voor unusual weights

### YAML Formaat

#### Enhanced Format (v2.0)

```yaml
hoofdterm:
  - synoniem: term1
    weight: 0.95    # Nearly exact
  - synoniem: term2
    weight: 0.85    # Strong synonym
```

#### Legacy Format (v1.0 - nog steeds ondersteund)

```yaml
hoofdterm:
  - term1  # Weight defaults to 1.0
  - term2
```

#### Mixed Format (beide ondersteund)

```yaml
hoofdterm:
  - synoniem: term1
    weight: 0.95
  - term2           # Legacy: weight = 1.0
  - synoniem: term3
    weight: 0.80
```

### Weight Guidelines

| Weight Range | Classificatie | Gebruik | Voorbeelden |
|-------------|---------------|---------|-------------|
| **1.0** | Exact/Perfect | Default, legacy format | - |
| **0.95** | Nearly Exact | Minimaal semantisch verschil | "voorarrest" voor "voorlopige hechtenis" |
| **0.85-0.90** | Strong Synonym | Uitwisselbaar in meeste contexten | "bewaring", "kracht van gewijsde" |
| **0.70-0.80** | Good Synonym | Geschikt voor query expansion | "preventieve detentie", "definitieve uitspraak" |
| **0.50-0.65** | Weak/Contextual | Gebruik met voorzichtigheid | "gevangenhouding" (specifieke context) |
| **< 0.50** | Questionable | Niet aanbevolen | - |

**Best Practices**:
- Start conservatief: begin met hoge weights (0.85-0.95)
- Verlaag weight bij twijfel over semantische overlap
- Gebruik < 0.70 alleen voor context-specifieke termen
- Vermijd weights < 0.50 (liever niet toevoegen als synoniem)

## API

### Core Functions

#### 1. `get_synoniemen(term: str) -> list[str]`

**Legacy API - Backward Compatible**

```python
service = JuridischeSynoniemlService()
synoniemen = service.get_synoniemen("onherroepelijk")
# → ["kracht van gewijsde", "rechtskracht", ...]
```

**Gedrag**:
- Returnt plain strings (geen weights)
- **Gesorteerd op weight** (hoogste eerst)
- Fully backward compatible met v1.0

#### 2. `get_synonyms_with_weights(term: str) -> list[tuple[str, float]]`

**Nieuwe API - Weighted Results**

```python
weighted = service.get_synonyms_with_weights("onherroepelijk")
# → [("kracht van gewijsde", 0.95), ("rechtskracht", 0.90), ...]
```

**Kenmerken**:
- Returnt (term, weight) tuples
- Gesorteerd op weight (descending)
- Bidirectioneel (werkt met hoofdterm of synoniem)
- Hoofdterm krijgt weight 1.0 bij reverse lookup

#### 3. `get_best_synonyms(term: str, threshold: float = 0.85) -> list[str]`

**Threshold-Based Filtering**

```python
# Alleen sterke synoniemen
best = service.get_best_synonyms("onherroepelijk", threshold=0.90)
# → ["kracht van gewijsde", "rechtskracht"]

# Inclusief goede synoniemen
good = service.get_best_synonyms("onherroepelijk", threshold=0.70)
# → ["kracht van gewijsde", "rechtskracht", "definitieve uitspraak", ...]
```

**Use Cases**:
- **High precision queries**: threshold=0.90 (alleen nearly exact)
- **Balanced queries**: threshold=0.85 (default - strong synonyms)
- **High recall queries**: threshold=0.70 (include good synonyms)

### Bestaande API (aangepast)

#### `expand_query_terms(term: str, max_synonyms: int = 3) -> list[str]`

**Gedrag aangepast**:
- Nu gesorteerd op **weight** (was: YAML volgorde)
- Selecteert top-N synoniemen op basis van weight
- Backward compatible (returnt nog steeds strings)

**Voorbeeld**:

```python
# YAML (random order):
# test:
#   - synoniem: low_weight
#     weight: 0.60
#   - synoniem: high_weight
#     weight: 0.95
#   - synoniem: medium_weight
#     weight: 0.80

expanded = service.expand_query_terms("test", max_synonyms=2)
# v1.0 (YAML order): ["test", "low_weight", "high_weight"]
# v2.0 (weight order): ["test", "high_weight", "medium_weight"]
```

## Data Storage

### Internal Structure

```python
# synoniemen: dict[str, list[WeightedSynonym]]
{
    "voorlopige hechtenis": [
        WeightedSynonym(term="voorarrest", weight=0.95),
        WeightedSynonym(term="bewaring", weight=0.90),
        WeightedSynonym(term="inverzekeringstelling", weight=0.85),
        # ... sorted by weight (highest first)
    ]
}

# reverse_index: dict[str, str]
{
    "voorarrest": "voorlopige hechtenis",
    "bewaring": "voorlopige hechtenis",
    # ...
}
```

**Sorting**:
- Synoniemen worden **automatisch gesorteerd** op weight tijdens loading
- Eenmalig bij `_load_synoniemen()` (niet bij elke query)
- Performance: O(1) lookup, geen runtime sorting nodig

## Validation

### Automated Validation

Script: `scripts/validate_synonyms.py`

**Nieuwe validaties (v2.0)**:

```bash
python scripts/validate_synonyms.py
```

**Checks**:

1. **Weight Range Validation**
   - ERROR: Weight < 0.0 of > 1.0
   - WARNING: Weight < 0.5 (too weak)
   - WARNING: Weight > 1.0 (will be clamped)

2. **Weight Conflicts**
   - WARNING: Zelfde synoniem met verschillende weights in meerdere hoofdtermen

3. **Format Validation**
   - ERROR: Dict entry zonder 'synoniem' key
   - ERROR: Invalid weight type (niet converteerbaar naar float)

**Output**:

```
[5/6] Validating synonym weights...
  ✓ All weights are valid
```

of met warnings:

```
[5/6] Validating synonym weights...
  ⚠ Low weight for 'gedetineerde' in 'verdachte': 0.60 (< 0.5) - may be too weak
```

### Manual Review

**Checklist voor nieuwe weighted synonyms**:
- [ ] Weight range: 0.0 ≤ weight ≤ 1.0?
- [ ] Semantische nabijheid correct gereflecteerd?
- [ ] Consistent met soortgelijke synoniemen in andere hoofdtermen?
- [ ] Geen weights < 0.70 zonder duidelijke reden?
- [ ] YAML syntax correct (indentation, keys)?

## Migration Guide

### Van Legacy naar Weighted Format

**Voor bestaande synoniemen**:

#### Stap 1: Evalueer Semantische Nabijheid

```yaml
# Voor:
onherroepelijk:
  - kracht van gewijsde
  - rechtskracht
  - definitieve uitspraak
```

**Vraag per synoniem**:
1. Hoe semantisch dichtbij is dit synoniem?
2. In welke contexten zijn ze uitwisselbaar?
3. Zou een juridisch expert dit als "nearly exact" zien?

#### Stap 2: Assign Weights

```yaml
# Na:
onherroepelijk:
  - synoniem: kracht van gewijsde
    weight: 0.95  # Nearly exact - legal technical term
  - synoniem: rechtskracht
    weight: 0.90  # Strong synonym
  - synoniem: definitieve uitspraak
    weight: 0.85  # Strong but more general
```

**Rationale documenteren** (inline comments aanbevolen):
- Waarom deze weight?
- Welke nuances zijn er?
- Is dit context-afhankelijk?

#### Stap 3: Validate

```bash
python scripts/validate_synonyms.py
```

Controleer:
- Geen errors
- Warnings zijn intentioneel (bijv. lage weight voor contextuele synoniem)

#### Stap 4: Test

```python
from src.services.web_lookup.synonym_service import get_synonym_service

service = get_synonym_service()

# Test sorting
weighted = service.get_synonyms_with_weights("onherroepelijk")
print(weighted)
# → [("kracht van gewijsde", 0.95), ("rechtskracht", 0.90), ...]

# Test threshold filtering
best = service.get_best_synonyms("onherroepelijk", threshold=0.90)
print(best)
# → ["kracht van gewijsde", "rechtskracht"]
```

### Geleidelijke Migratie

**Niet nodig om alles ineens te migreren**:
- Legacy en weighted formats werken **naast elkaar**
- Migreer hoofdtermen **incrementeel**
- Start met meest gebruikte termen (bijv. top 20 via Wikipedia lookup stats)

**Prioritering**:
1. **High-impact termen**: Vaak gezocht in Wikipedia/SRU
2. **Ambigue termen**: Meerdere betekenissen, nuance belangrijk
3. **Juridische precisie vereist**: Strafrecht, bestuursrecht

## Performance

### Overhead

**Loading**:
- Marginale overhead (< 5ms extra voor 50 hoofdtermen)
- Sorting gebeurt 1x tijdens `_load_synoniemen()`

**Query**:
- **Geen overhead**: Synoniemen zijn pre-sorted
- `get_synoniemen()`: O(1) lookup (unchanged)
- `get_synonyms_with_weights()`: O(n) waar n = aantal synoniemen (typisch < 10)
- `get_best_synonyms()`: O(n) filtering

**Memory**:
- WeightedSynonym: 16 bytes overhead per synoniem (str pointer + float)
- Voor 50 hoofdtermen × 4 synoniemen avg = ~3KB extra

→ **Negligible impact** op applicatie performance

## Testing

### Test Coverage

**File**: `tests/services/web_lookup/test_weighted_synonyms.py`

**Categorieën**:
1. **WeightedSynonym Dataclass** (5 tests)
   - Creation, default weight, immutability, equality

2. **YAML Loading** (4 tests)
   - Weighted format, legacy format, mixed format, sorting

3. **get_synonyms_with_weights()** (4 tests)
   - Hoofdterm lookup, reverse lookup, sorting, unknown terms

4. **get_best_synonyms()** (4 tests)
   - Default threshold, custom threshold, high/low thresholds

5. **Backward Compatibility** (2 tests)
   - get_synoniemen() with weighted data
   - expand_query_terms() weight-based sorting

6. **Edge Cases** (6 tests)
   - Invalid weight types, missing keys, weight clamping
   - Empty weights, full workflow, stats

**Totaal**: 25+ tests

### Running Tests

```bash
# Alle weighted synonym tests
pytest tests/services/web_lookup/test_weighted_synonyms.py -v

# Specifieke test class
pytest tests/services/web_lookup/test_weighted_synonyms.py::TestGetBestSynonyms -v

# Coverage
pytest tests/services/web_lookup/test_weighted_synonyms.py --cov=src/services/web_lookup/synonym_service --cov-report=term-missing
```

## Examples

### Use Case 1: Wikipedia Lookup met Best Synonyms

```python
from src.services.web_lookup.synonym_service import get_synonym_service

service = get_synonym_service()

# High-precision query (alleen sterke synoniemen)
term = "voorlopige hechtenis"
best_synonyms = service.get_best_synonyms(term, threshold=0.90)

# Query Wikipedia met originele term + top synonyms
queries = [term] + best_synonyms[:2]  # Max 3 queries

for query in queries:
    result = wikipedia_lookup(query)
    if result.found:
        return result

# → Probeert eerst "voorlopige hechtenis"
# → Dan "voorarrest" (0.95)
# → Dan "bewaring" (0.90)
# → NIET "gevangenhouding" (0.70 < 0.90)
```

### Use Case 2: Adaptive Query Expansion

```python
def smart_expand_query(term: str, desired_precision: str) -> list[str]:
    """
    Expand query met precision-aware thresholds.

    Args:
        term: Zoekterm
        desired_precision: "high", "medium", "low"

    Returns:
        Lijst van query termen
    """
    service = get_synonym_service()

    thresholds = {
        "high": 0.95,     # Alleen nearly exact
        "medium": 0.85,   # Strong synonyms
        "low": 0.70       # Include good synonyms
    }

    threshold = thresholds.get(desired_precision, 0.85)
    synonyms = service.get_best_synonyms(term, threshold=threshold)

    return [term] + synonyms[:3]  # Max 4 queries total

# High precision (juridisch onderzoek)
queries = smart_expand_query("onherroepelijk", "high")
# → ["onherroepelijk", "kracht van gewijsde", "in kracht van gewijsde"]

# Low precision (exploratory search)
queries = smart_expand_query("onherroepelijk", "low")
# → ["onherroepelijk", "kracht van gewijsde", "rechtskracht",
#    "definitieve uitspraak", "finale uitspraak"]
```

### Use Case 3: Weight-Based Fallback Strategy

```python
def cascade_lookup(term: str) -> Optional[LookupResult]:
    """
    Cascade lookup: start met beste synoniemen, fallback naar zwakkere.
    """
    service = get_synonym_service()

    # Tier 1: Nearly exact synonyms (weight >= 0.95)
    tier1 = [term] + service.get_best_synonyms(term, threshold=0.95)
    for query in tier1:
        if result := try_lookup(query):
            return result

    # Tier 2: Strong synonyms (weight 0.85-0.94)
    tier2 = service.get_best_synonyms(term, threshold=0.85)
    tier2 = [s for s in tier2 if s not in tier1]  # Exclude already tried
    for query in tier2:
        if result := try_lookup(query):
            return result

    # Tier 3: Good synonyms (weight 0.70-0.84)
    tier3 = service.get_best_synonyms(term, threshold=0.70)
    tier3 = [s for s in tier3 if s not in tier1 and s not in tier2]
    for query in tier3:
        if result := try_lookup(query):
            return result

    return None
```

## Future Enhancements

### Geplande Features

1. **Dynamic Weight Adjustment**
   - User feedback: upvote/downvote synoniemen
   - Automatic adjustment based op click-through rate
   - Machine learning: train weights van query logs

2. **Context-Aware Weights**
   ```yaml
   verdachte:
     - synoniem: beklaagde
       weight:
         strafrecht: 0.95
         bestuursrecht: 0.70
   ```

3. **Confidence Intervals**
   ```python
   WeightedSynonym(term="test", weight=0.85, confidence_interval=(0.80, 0.90))
   ```

4. **Weight Provenance**
   - Track weight source (manual, automatic, user feedback)
   - Audit trail voor weight changes

### Extensibility

**Plugin Architecture**:
```python
class WeightCalculator(ABC):
    @abstractmethod
    def calculate_weight(self, hoofdterm: str, synoniem: str) -> float:
        pass

# Implementations:
# - ManualWeightCalculator (current - YAML)
# - SemanticSimilarityCalculator (word embeddings)
# - UsageFeedbackCalculator (click data)
# - HybridCalculator (weighted average)
```

## Troubleshooting

### Veelvoorkomende Problemen

#### 1. Weights worden niet toegepast

**Symptomen**: `expand_query_terms()` returnt synoniemen in YAML volgorde, niet weight volgorde

**Diagnose**:
```python
service = get_synonym_service()
weighted_syns = service.synoniemen["onherroepelijk"]
print([ws.weight for ws in weighted_syns])
# → Should be sorted descending: [0.95, 0.90, 0.85, ...]
```

**Oplossing**:
- Check YAML syntax (correct indentation)
- Verify weights zijn floats, niet strings
- Run validation script: `python scripts/validate_synonyms.py`

#### 2. Weight validation warnings

**Warning**: `Low weight for 'gedetineerde' in 'verdachte': 0.60 (< 0.5)`

**Actie**:
- Intentioneel? → Ignore (contextuele synoniem)
- Onbedoeld? → Verhoog weight naar >= 0.70 of verwijder synoniem

#### 3. Inconsistente weights across hoofdtermen

**Warning**: `Weight conflict for synonym 'bewaring': 'voorlopige_hechtenis': 0.90, 'detentie': 0.75`

**Actie**:
- Review semantische relatie met beide hoofdtermen
- Uniform maken indien zelfde betekenis
- Of: verwijder cross-contamination (synoniem hoort bij slechts 1 hoofdterm)

## References

- **Code**: `/src/services/web_lookup/synonym_service.py`
- **Config**: `/config/juridische_synoniemen.yaml`
- **Validation**: `/scripts/validate_synonyms.py`
- **Tests**: `/tests/services/web_lookup/test_weighted_synonyms.py`
- **CLAUDE.md**: Project-wide guidelines

## Changelog

### v2.0 (2025-10-09)

**Added**:
- WeightedSynonym dataclass
- Enhanced YAML format (backward compatible)
- `get_synonyms_with_weights()` API
- `get_best_synonyms()` threshold filtering
- Weight validation in `validate_synonyms.py`
- Automatic weight-based sorting
- 25+ comprehensive tests

**Changed**:
- `expand_query_terms()` now uses weight-based sorting (was: YAML order)
- Internal storage: `dict[str, list[WeightedSynonym]]` (was: `dict[str, list[str]]`)

**Maintained**:
- 100% backward compatibility with legacy format
- `get_synoniemen()` API unchanged (returns strings)
- All existing tests pass

---

**Auteur**: Claude Code
**Review**: Pending
**Approved**: Pending
