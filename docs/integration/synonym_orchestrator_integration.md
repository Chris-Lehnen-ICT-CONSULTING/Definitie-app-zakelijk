# SynonymOrchestrator Integration Guide

**Status:** PHASE 2.1 Complete - Ready for ServiceContainer Integration
**Date:** 2025-10-09
**Architecture:** Synonym Orchestrator Architecture v3.1

---

## Overview

Deze guide beschrijft hoe SynonymOrchestrator geïntegreerd wordt in de ServiceContainer
en hoe de cache invalidation callbacks geconfigureerd worden.

## Components Created

### 1. GPT4SynonymSuggester (Placeholder)

**Location:** `src/services/gpt4_synonym_suggester.py`

**Status:** Placeholder implementation (returns empty list)

```python
from services.gpt4_synonym_suggester import GPT4SynonymSuggester

suggester = GPT4SynonymSuggester()
suggestions = await suggester.suggest_synonyms("voorlopige hechtenis")
# Returns: [] (placeholder)
```

**Future Work:** Implement GPT-4 API integration in later phase

### 2. SynonymOrchestrator (Complete)

**Location:** `src/services/synonym_orchestrator.py`

**Features:**
- ✅ TTL cache met thread-safe locking
- ✅ Governance policy enforcement (STRICT vs PRAGMATIC)
- ✅ GPT-4 enrichment flow (with placeholder)
- ✅ Cache invalidation callbacks
- ✅ Comprehensive error handling
- ✅ Metrics tracking (hit rate, stats)

**Lines of Code:** ~450 lines

---

## ServiceContainer Integration

### Step 1: Add Imports

Add to `src/services/container.py`:

```python
from services.synonym_orchestrator import SynonymOrchestrator
from services.gpt4_synonym_suggester import GPT4SynonymSuggester
from repositories.synonym_registry import get_synonym_registry
```

### Step 2: Initialize Services

Add method to ServiceContainer class:

```python
def _init_synonym_services(self):
    """Initialize synonym-related services."""
    # Get registry instance
    registry = get_synonym_registry(self.db_path)

    # Create GPT-4 suggester
    gpt4_suggester = GPT4SynonymSuggester()

    # Create orchestrator
    self.synonym_orchestrator = SynonymOrchestrator(registry, gpt4_suggester)

    # Register cache invalidation callback
    registry.register_invalidation_callback(
        self.synonym_orchestrator.invalidate_cache
    )

    logger.info("Synonym orchestrator initialized with cache invalidation callback")
```

### Step 3: Call During Container Init

Add to `ServiceContainer.__init__()`:

```python
def __init__(self, db_path: str = "data/definities.db", ...):
    # ... existing init code ...

    # Initialize synonym services
    self._init_synonym_services()

    # ... rest of init ...
```

### Step 4: Add Getter Method

Add property to ServiceContainer:

```python
@property
def synonym_orchestrator(self) -> SynonymOrchestrator:
    """Get synonym orchestrator instance."""
    return self._synonym_orchestrator

@synonym_orchestrator.setter
def synonym_orchestrator(self, value: SynonymOrchestrator):
    """Set synonym orchestrator instance."""
    self._synonym_orchestrator = value
```

---

## Cache Invalidation Flow

### Callback Registration

```
┌─────────────────────────────────────────────────┐
│         ServiceContainer.__init__()             │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│     registry.register_invalidation_callback(    │
│       orchestrator.invalidate_cache             │
│     )                                            │
└─────────────────────────────────────────────────┘
```

### Invalidation Trigger

```
User edits synonym → registry.add_group_member()
                    ↓
                registry._trigger_invalidation(term)
                    ↓
                orchestrator.invalidate_cache(term)
                    ↓
                Cache entry deleted
                    ↓
                Next query = cache MISS → fresh data
```

---

## Usage Examples

### Basic Query

```python
from services.container import ServiceContainer

container = ServiceContainer()
orchestrator = container.synonym_orchestrator

# Query synonyms
synonyms = orchestrator.get_synonyms_for_lookup(
    term="voorlopige hechtenis",
    max_results=5,
    min_weight=0.7
)

print(f"Found {len(synonyms)} synonyms")
for syn in synonyms:
    print(f"  - {syn.term} (weight: {syn.weight}, status: {syn.status})")
```

### Enrichment Flow

```python
import asyncio

# Ensure minimum synonyms (with GPT-4 enrichment if needed)
synonyms, ai_pending_count = await orchestrator.ensure_synonyms(
    term="voorlopige hechtenis",
    min_count=5,
    context={
        'definitie': "Een vrijheidsbenemende maatregel...",
        'tokens': ["strafrecht", "strafvordering"],
        'domain': 'strafrecht'
    }
)

print(f"Found {len(synonyms)} synonyms")
print(f"Added {ai_pending_count} AI suggestions (pending review)")
```

### Cache Metrics

```python
# Get cache stats
stats = orchestrator.get_cache_stats()
print(f"Cache hit rate: {stats['hit_rate']:.1%}")
print(f"Cache size: {stats['size']}/{stats['max_size']}")
print(f"Hits: {stats['hits']}, Misses: {stats['misses']}")

# Health check
health = orchestrator.get_health_check()
print(f"Status: {health['status']}")
if health.get('warnings'):
    print(f"Warnings: {health['warnings']}")
```

---

## Configuration

### Config File Location

`config/synonym_config.yaml`

### Example Configuration

```yaml
synonym_configuration:
  # Governance policy
  policy: strict  # strict | pragmatic

  # Enrichment settings
  min_synonyms: 5
  gpt4_timeout: 30
  gpt4_max_retries: 3

  # Cache settings
  cache_ttl: 3600  # 1 hour
  cache_max_size: 1000

  # Weight thresholds
  min_weight: 0.7
  preferred_threshold: 0.95
```

### Environment Variable Override

```bash
export SYNONYM_CONFIG_PATH=/path/to/custom/config.yaml
```

---

## Testing

### Manual Testing Script

See: `scripts/test_synonym_orchestrator_manual.py`

Run:
```bash
python scripts/test_synonym_orchestrator_manual.py
```

### Unit Tests (Future)

Will be added in PHASE 1.5:
- `tests/services/test_synonym_orchestrator.py`
- `tests/services/test_gpt4_synonym_suggester.py`

---

## Monitoring

### Logging

Two loggers are used:

1. **Standard logger** (`synonym_orchestrator`):
   - Cache hits/misses
   - Query operations
   - Errors

2. **Enrichment logger** (`synonym_enrichment`):
   - GPT-4 enrichment start/complete
   - Duration tracking
   - Timeout/failure events

### Log Format

```
2025-10-09 14:32:15 - INFO - Cache HIT for 'voorlopige hechtenis' (returned 5 results)
2025-10-09 14:32:16 - INFO - Found 5 synonyms for 'voorlopige hechtenis' (statuses: ['active'], min_weight: 0.7)
2025-10-09 14:32:45 - INFO - Starting GPT-4 enrichment for 'term' (only 2 found, need 5)
2025-10-09 14:32:53 - INFO - Enrichment complete for 'term': 3 suggestions added, duration: 8.2s
```

### Metrics to Monitor

| Metric | Target | Alert |
|--------|--------|-------|
| Cache hit rate | > 80% | < 60% |
| GPT-4 success rate | > 95% | < 90% |
| Avg enrichment time | < 10s | > 20s |
| Cache size | < 1000 | > 950 |

---

## Troubleshooting

### Issue: Low Cache Hit Rate

**Symptoms:** `cache_hit_rate < 0.5`

**Solutions:**
1. Check TTL: `cache_ttl_seconds` te laag?
2. Check invalidation: Te veel manual edits?
3. Increase cache size: `cache_max_size` verhogen

### Issue: GPT-4 Timeout

**Symptoms:** `asyncio.TimeoutError` in enrichment_logger

**Solutions:**
1. Increase timeout: `gpt4_timeout_seconds` verhogen (max 300s)
2. Check GPT-4 API status
3. Review network latency

### Issue: Cache Memory Growth

**Symptoms:** Cache size blijft groeien

**Solutions:**
1. Check eviction: LRU logic werkend?
2. Lower max_size: `cache_max_size` verlagen
3. Lower TTL: `cache_ttl_seconds` verlagen

---

## Next Steps

### PHASE 2.2: Façade Layer

Create `JuridischeSynoniemService` wrapper:
- `src/services/web_lookup/synonym_service.py`
- Backward compatible API
- Delegate to orchestrator

### PHASE 2.3: Definition Generation Integration

Update `DefinitionGenerationOrchestrator`:
- Call `ensure_synonyms()` before web lookup
- Pass enriched synonyms to web lookup service
- Display AI pending count in UI

### PHASE 2.4: Unit Tests

Create test suite:
- `tests/services/test_synonym_orchestrator.py`
- Mock registry and GPT-4
- Test cache logic, TTL, invalidation
- Test governance policy enforcement

---

## Architecture Compliance

### Checklist

- [x] TTL cache implemented with expiration check
- [x] Thread-safe cache operations (RLock)
- [x] Governance policy enforcement (STRICT vs PRAGMATIC)
- [x] Cache metrics (hit rate, stats)
- [x] GPT-4 enrichment flow (placeholder)
- [x] Cache invalidation callback
- [x] Error handling comprehensive
- [x] Type hints on all methods
- [x] Logging throughout
- [x] Uses SynonymConfiguration
- [x] Uses SynonymRegistry correctly
- [x] Health check endpoint
- [x] Follows CLAUDE.md standards

**Status:** ✅ **PHASE 2.1 COMPLETE**

---

*Generated: 2025-10-09*
*Architecture: Synonym Orchestrator v3.1*
*Implementation: PHASE 2.1 - Business Logic Layer*
