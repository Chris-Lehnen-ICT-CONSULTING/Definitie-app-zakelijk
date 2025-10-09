# Juridisch Ranker - Quick Reference

## TL;DR

Keywords and boost factors are now in YAML config files. Old code still works, but use the new pattern for new code.

## Quick Start

### Old Way (Still Works)
```python
from services.web_lookup.juridisch_ranker import JURIDISCHE_KEYWORDS

if "wetboek" in JURIDISCHE_KEYWORDS:
    print("Juridisch keyword")
```

### New Way (Recommended)
```python
from services.web_lookup.juridisch_ranker import get_ranker_config

config = get_ranker_config()
keywords = config.keywords  # set of 45 keywords
boost = config.boost_factors["juridische_bron"]  # 1.2
```

## Configuration Files

### Keywords: `config/juridische_keywords.yaml`
```yaml
algemeen:        # 14 keywords
strafrecht:      # 10 keywords
burgerlijk:      # 6 keywords
bestuursrecht:   # 6 keywords
procesrecht:     # 5 keywords
wetten:          # 4 keywords (sr, sv, rv, bw)
```
**Total:** 45 keywords

### Boost Factors: `config/web_lookup_defaults.yaml`
```yaml
juridical_boost:
  juridische_bron: 1.2       # rechtspraak.nl, overheid.nl
  keyword_per_match: 1.1     # per juridisch keyword
  keyword_max_boost: 1.3     # max keyword boost
  artikel_referentie: 1.15   # Art. X, Artikel Y
  lid_referentie: 1.05       # lid 2, tweede lid
  context_match: 1.1         # per context token
  context_max_boost: 1.3     # max context boost
  juridical_flag: 1.15       # is_juridical flag
```

## Environment Variables

```bash
# Override keywords config
export JURIDISCH_KEYWORDS_CONFIG="/path/to/keywords.yaml"

# Override defaults (including boost factors)
export WEB_LOOKUP_CONFIG="/path/to/defaults.yaml"
```

## Common Tasks

### Add New Keywords
1. Edit `config/juridische_keywords.yaml`
2. Add to appropriate category
3. Restart app (or wait for hot reload in future)

### Adjust Boost Factors
1. Edit `config/web_lookup_defaults.yaml`
2. Modify values in `juridical_boost` section
3. Restart app

### Check Current Config
```python
config = get_ranker_config()
print(f"Keywords: {len(config.keywords)}")  # 45
print(f"Factors: {config.boost_factors}")
```

### Validate Migration
```bash
python scripts/validate_juridisch_keywords_migration.py
```

## API Reference

### `get_ranker_config()`
Returns singleton config instance.

**Parameters:**
- `keywords_path` (str, optional): Custom keywords YAML path
- `defaults_path` (str, optional): Custom defaults YAML path

**Returns:** `JuridischRankerConfig`

### `JuridischRankerConfig`

**Attributes:**
- `keywords` (set[str]): 45 normalized juridische keywords
- `boost_factors` (dict): 8 configurable boost factors

**Methods:**
- `_normalize_term(term)`: Normalize term (lowercase, strip, underscore→space)

### Module-level Functions

**Unchanged APIs (use config internally):**
- `is_juridische_bron(url: str) -> bool`
- `count_juridische_keywords(text: str) -> int`
- `contains_artikel_referentie(text: str) -> bool`
- `contains_lid_referentie(text: str) -> bool`
- `calculate_juridische_boost(result, context=None) -> float`
- `boost_juridische_resultaten(results, context=None) -> list`
- `get_juridische_score(result) -> float`

## Troubleshooting

### Config Not Loading?
Check logs for warnings:
```
WARNING: Keywords config niet gevonden: ...
INFO: Geladen: 45 fallback keywords
```

### Performance Issues?
Config is singleton - loaded once at startup (~10-20ms).

### Keywords Not Working?
Verify normalization (lowercase, no underscores):
```python
config = get_ranker_config()
print("wetboek" in config.keywords)  # True
print("Wetboek" in config.keywords)  # False (not normalized)
```

## Testing

Run tests:
```bash
pytest tests/services/web_lookup/test_juridisch_ranker.py -v
```

Run validation:
```bash
python scripts/validate_juridisch_keywords_migration.py
```

## Migration Status

✅ All 64 tests passing
✅ All validation checks passed
✅ 100% backwards compatible
✅ Zero breaking changes

## See Also

- **Full Documentation:** `docs/technisch/juridisch_ranker_migration.md`
- **Migration Summary:** `docs/technisch/MIGRATION_SUMMARY_JURIDISCH_RANKER.md`
- **Similar Pattern:** `src/services/web_lookup/synonym_service.py`
