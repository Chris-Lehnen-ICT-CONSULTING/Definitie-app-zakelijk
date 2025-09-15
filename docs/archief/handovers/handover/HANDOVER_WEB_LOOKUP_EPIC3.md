# 📋 Overdracht Document - Episch Verhaal 3: Web Lookup Modernization

## 🎯 Executive Summary

Dit document bevat alle informatie voor het implementeren van Episch Verhaal 3: Web Lookup Modernization. Het doel is OM de web lookup service te moderniseren voor betere definitie-generatie via LLM context verrijking, met volledige bronverantwoording en provenance tracking.

**Geschatte doorlooptijd:** 4-7 dagen totaal (MVP in 2 dagen)
**Status:** Ready for implementation
**Document datum:** 09-01-2025

## 📊 Current Situation

### Wat We Hebben
- **5 legacy implementaties** verspreid over meerdere files (633+ regels code)
- **ModernWebLookupService** partially geïmplementeerd (alleen Wikipedia/SRU)
- **HybridContextEngine** kan web context gebruiken
- **Geen bronverantwoording** in UI of database
- **Encoding problemen** in legacy code (UTF-8 issues)
- **Geen caching** in moderne implementatie

### Kritieke Legacy Files
```
src/web_lookup/
├── lookup.py (475 lines) - 7 bronnen implementaties
├── bron_lookup.py (633 lines) - Validatie & scoring
├── definitie_lookup.py (717 lines) - Duplicate detection
├── juridische_lookup.py (89 lines) - Juridische regex patterns
└── [various _broken/_encoding_issue variants]
```

### Probleem Statement
1. **Geen unified contract** - Elke provider eigen format
2. **Geen provenance tracking** - Bronnen worden niet opgeslagen
3. **Prestaties issues** - Geen caching, sequentiële calls
4. **UI geeft geen bronnen weer** - Gebruiker ziet niet wat gebruikt is
5. **Export mist bronnen** - Geen bronverantwoording in exports

## 🚀 Implementatie Roadmap

### Fase 0: Contract & Specification (0.5 dag) ⭐ START HIER

**Doel:** Volledig gespecificeerd contract voordat code geschreven wordt

**Deliverables:**
1. Create `docs/technical/web-lookup-contract-v1.0.md`
2. Create `src/services/web_lookup/contracts.py`:

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum

class LookupErrorType(Enum):
    TIMEOUT = "Provider timeout exceeded"
    NETWORK = "Network connection failed"
    PARSE = "Response parsing failed"
    RATE_LIMIT = "Rate limit exceeded"
    AUTH = "Authentication failed"
    INVALID_RESPONSE = "Invalid/empty response"

@dataclass
class WebLookupResult:
    # Core Fields (REQUIRED)
    provider: str           # "wikipedia", "sru_overheid"
    source_label: str       # "Wikipedia NL", "Overheid.nl"
    title: str             # Article title
    url: str               # Absolute URL (validated)
    snippet: str           # Sanitized, max 500 chars
    score: float           # 0.0-1.0 normalized

    # Usage Tracking (REQUIRED)
    used_in_prompt: bool
    position_in_prompt: int

    # Metadata (REQUIRED)
    retrieved_at: datetime
    content_hash: str      # SHA256 for dedup
    error: Optional[str]   # Error from LookupErrorType

    # Juridisch (Nederlandse Overheid)
    legal_refs: List[str] = None
    is_authoritative: bool = False
    legal_weight: float = 0.0

    # Linguistic (Legacy preservation)
    is_plurale_tantum: bool = False

    # Caching
    cache_key: str = ""
    ttl_seconds: int = 3600
```

3. Create `config/web_lookup_defaults.yaml` (deze wordt door de app standaard gebruikt; optioneel kun je met `WEB_LOOKUP_CONFIG=/pad/naar/config.yaml` overschrijven):

```yaml
web_lookup:
  enabled: true

  cache:
    strategy: "stale-while-revalidate"
    grace_period: 300
    default_ttl: 3600
    max_entries: 1000

  sanitization:
    strip_tags: [script, style, iframe, object, embed, form]
    block_protocols: [javascript, data, vbscript]
    max_snippet_length: 500

  providers:
    wikipedia:
      enabled: true
      weight: 0.7
      timeout: 5
      cache_ttl: 7200
      min_score: 0.3

    sru_overheid:
      enabled: true
      weight: 1.0  # Highest for juridisch
      timeout: 5
      cache_ttl: 3600
      min_score: 0.4

  context_mappings:
    DJI: ["Pbw", "WvSr"]
    OM: ["WvSv"]
    Rechtspraak: ["Rv"]
```

**✅ Definition of Done:**
- [ ] Contract reviewed by tech lead
- [ ] No ambiguities in specification
- [ ] Config file created and validated

### Fase 1: Core Service Implementatie (1-2 dagen)

**Dag 1: Wikipedia Adapter**

1. **Refactor WikipediaService** (`src/services/web_lookup/wikipedia_service.py`):
```python
class WikipediaAdapter:
    async def lookup(self, query: str, context: dict) -> List[WebLookupResult]:
        # 1. Call Wikipedia API
        # 2. Normalize to WebLookupResult
        # 3. Apply sanitization
        # 4. Calculate score
        # 5. Add to cache
        return results
```

2. **Implement Basic Cache**:
```python
class SimpleCache:
    def __init__(self, max_entries=1000):
        self._cache = {}  # key -> (value, expires_at)
        self._max_entries = max_entries

    def get(self, key: str) -> Optional[Any]:
        # Check TTL, return if valid

    def set(self, key: str, value: Any, ttl: int):
        # Store with expiration
```

**Dag 2: SRU/Overheid.nl Adapter**

1. **Refactor SRUService** (`src/services/web_lookup/sru_service.py`)
2. **Add Rate Limiting**:
```python
class RateLimiter:
    def __init__(self, max_per_minute=10):
        self._calls = []
        self._max = max_per_minute

    async def acquire(self):
        # Wait if limit reached
```

3. **Juridische Ref Extraction**:
```python
JURIDISCHE_PATTERNS = [
    r"artikel\s+(\d+[a-z]?)\s+(?:van\s+)?(?:de\s+)?([\w\s]+wet)",
    r"art\.\s*(\d+[a-z]?(?::\d+)?)\s+(\w+)",
    # etc.
]
```

### Fase 1.5: Quick Win Provenance (0.5 dag)

**No Database Changes!** Store in metadata:

1. **Update Definition Storage**:
```python
# In DefinitionRepository.save()
definition.metadata = {
    "sources": [
        {
            "provider": result.provider,
            "title": result.title,
            "url": result.url,
            "snippet": result.snippet,
            "score": result.score,
            "used_in_prompt": result.used_in_prompt,
            "retrieved_at": result.retrieved_at.isoformat()
        }
        for result in lookup_results
    ],
    # Other metadata...
}
```

2. **Basic UI Display** (`src/ui/components/definition_generator_tab.py`):
```python
# After definition generation
if generation_result.get("metadata", {}).get("sources"):
    st.markdown("### 📚 Gebruikte Bronnen")

    sources = generation_result["metadata"]["sources"]
    for source in sources:
        if source.get("used_in_prompt"):
            with st.expander(f"{source['provider']}: {source['title'][:50]}..."):
                st.write(f"**URL:** {source['url']}")
                st.write(f"**Fragment:** {source['snippet'][:200]}...")
                if os.getenv("DEV_MODE"):
                    st.caption(f"Score: {source['score']:.2f}")
```

3. **Update Export** (`src/services/export_service.py`):
```python
# In export_to_json()
export_data["bronnen"] = definition.metadata.get("sources", [])
```

### Fase 2: Database Migration (1 dag) - OPTIONAL

**Only after MVP is working!**

1. **Create Migration** (`migrations/004_add_definitie_bronnen.sql`):
```sql
CREATE TABLE IF NOT EXISTS definitie_bronnen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    definitie_id INTEGER REFERENCES definities(id),
    source_type VARCHAR(50) NOT NULL,
    url TEXT NOT NULL,
    title VARCHAR(500),
    snippet TEXT,
    score DECIMAL(3,2),
    used_in_prompt BOOLEAN DEFAULT FALSE,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_definitie_id (definitie_id)
);
```

2. **Data Migration Script**:
```python
# Migrate from metadata to DB
for definition in all_definitions:
    if definition.metadata.get("sources"):
        for source in definition.metadata["sources"]:
            insert_into_definitie_bronnen(definition.id, source)
```

### Fase 3: Full Implementatie (1-2 dagen)

Add remaining 5 providers:
- Wiktionary
- Ensie.nl
- Wetten.nl
- Strafrechtketen.nl
- Kamerstukken.nl

### Fase 4: Testen & Quality (0.5-1 dag)

Create offline tests with mocked responses.

## 🔧 Technical Implementatie Details

### Ranking Algorithm
```python
def rank_results(results: List[WebLookupResult], context: dict) -> List[WebLookupResult]:
    # 1. Apply provider weights
    for result in results:
        provider_weight = config["providers"][result.provider]["weight"]
        result.final_score = provider_weight * result.score

        # 2. Boost juridisch for legal context
        if context.get("juridisch") and result.is_authoritative:
            result.final_score *= 1.5

    # 3. Sort with tiebreakers
    return sorted(results, key=lambda r: (
        -r.final_score,      # Higher score first
        -r.is_authoritative, # Juridisch first
        r.title,            # Alphabetical
        r.url               # URL as final tiebreaker
    ))
```

### Deduplication
```python
def deduplicate(results: List[WebLookupResult]) -> List[WebLookupResult]:
    seen_urls = {}
    seen_hashes = {}
    deduped = []

    for result in results:
        canonical_url = normalize_url(result.url)

        if canonical_url in seen_urls:
            # Keep highest score
            if result.final_score > seen_urls[canonical_url].final_score:
                seen_urls[canonical_url] = result
        elif result.content_hash in seen_hashes:
            # Same content, different URL
            if result.final_score > seen_hashes[result.content_hash].final_score:
                seen_hashes[result.content_hash] = result
        else:
            seen_urls[canonical_url] = result
            seen_hashes[result.content_hash] = result
            deduped.append(result)

    return deduped
```

### Context Pack Building
```python
def build_context_pack(
    results: List[WebLookupResult],
    max_tokens: int = 1000
) -> Tuple[str, List[WebLookupResult]]:
    context_parts = []
    used_results = []
    token_count = 0

    for i, result in enumerate(results):
        snippet_tokens = estimate_tokens(result.snippet)
        if token_count + snippet_tokens > max_tokens:
            break

        context_parts.append(
            f"[{result.source_label}] {result.title}: {result.snippet}"
        )
        result.used_in_prompt = True
        result.position_in_prompt = i
        used_results.append(result)
        token_count += snippet_tokens

    return "\n\n".join(context_parts), used_results
```

## ⚠️ Critical Implementatie Notities

### 1. Start Small
- **Begin with Wikipedia only**
- Get full flow working end-to-end
- Dan add SRU/Overheid.nl
- Other providers last

### 2. No Breaking Changes
- Keep existing interfaces intact
- ModernWebLookupService should still work
- Don't modify existing database schema (use metadata)

### 3. Testen Strategy
```python
# Use mocked responses for all tests
@patch('httpx.AsyncClient.get')
async def test_wikipedia_lookup(mock_get):
    mock_get.return_value = Mock(
        status_code=200,
        json=lambda: {"extract": "Test content"}
    )

    result = await adapter.lookup("test")
    assert result[0].provider == "wikipedia"
    assert result[0].snippet == "Test content"
```

### 4. Feature Flags
```python
# Check if web lookup is enabled
if os.getenv("WEB_LOOKUP_ENABLED", "false").lower() == "true":
    results = await lookup_service.lookup(query)
else:
    results = []  # Graceful degradation
```

### 5. Error Handling
```python
try:
    results = await provider.lookup(query)
except asyncio.TimeoutError:
    logger.warning(f"Provider {provider} timed out")
    return WebLookupResult(
        provider=provider,
        error=LookupErrorType.TIMEOUT,
        # ... minimal fields
    )
```

## 📊 Success Metrics

### MVP Success (Fase 0-1.5)
- [ ] Contract defined and approved
- [ ] Wikipedia lookup returns WebLookupResult
- [ ] Results stored in metadata.sources
- [ ] UI shows at least 1 source
- [ ] Export contains sources
- [ ] Zero database changes

### Full Success (All Phases)
- [ ] All 7 providers working
- [ ] Cache hit rate >60%
- [ ] P95 latency <500ms (cached)
- [ ] Sources shown in UI for >80% definitions
- [ ] Duplicate detection working
- [ ] No encoding issues

## 🚨 Common Pitfalls to Avoid

1. **Don't start with database** - Use metadata first
2. **Don't implement all providers at once** - Wikipedia first
3. **Don't forget determinism** - Same input = same output
4. **Don't skip sanitization** - XSS risk is real
5. **Don't forget legacy patterns** - Preserve juridische regex
6. **Don't break existing code** - Keep interfaces intact

## 📞 Resources & Support

### Key Files to Review
- `src/services/modern_web_lookup_service.py` - Current implementation
- `src/web_lookup/lookup.py` - Legacy with 7 providers
- `src/hybrid_context/hybrid_context_engine.py` - How context is used
- `docs/backlog/stories/epic-3-web-lookup-modernization.md` - Full epic

### Test Commands
```bash
# Test Wikipedia adapter
python -m pytest tests/services/web_lookup/test_wikipedia_adapter.py -v

# Test with DEV_MODE
DEV_MODE=true WEB_LOOKUP_ENABLED=true streamlit run src/main.py

# Check metadata storage
sqlite3 data/definities.db "SELECT metadata FROM definities WHERE id=X"
```

### Quick Validation Checklist

**After Fase 0:**
- [ ] Contract file exists
- [ ] Config file valid YAML
- [ ] Types importable

**After Fase 1:**
- [ ] Wikipedia returns results
- [ ] Cache reduces API calls
- [ ] Sanitization removes HTML

**After Fase 1.5:**
- [ ] Sources in metadata
- [ ] UI shows sources
- [ ] Export has sources

**After Fase 2:**
- [ ] DB table created
- [ ] Data migrated
- [ ] Queries work

## 💡 Tips for Success

1. **Use the contract strictly** - Don't deviate from WebLookupResult
2. **Test offline first** - Mock all external calls
3. **Log everything** - Especially provider errors
4. **Cache aggressively** - APIs are slow
5. **Keep legacy tests** - They document business rules
6. **Ask questions early** - Contract ambiguities = bugs later

## 🎯 Day 1 Checklist

Morning:
- [ ] Read this document completely
- [ ] Review Episch Verhaal 3 document
- [ ] Check out feature branch
- [ ] Create contract file
- [ ] Get contract reviewed

Afternoon:
- [ ] Implement WebLookupResult class
- [ ] Create Wikipedia adapter skeleton
- [ ] Write first unit test
- [ ] Implement normalize_to_result()
- [ ] Test with real Wikipedia API

End of Day:
- [ ] Wikipedia returns WebLookupResult
- [ ] Basic caching works
- [ ] Unit tests passing
- [ ] Commit and push

---

*Generated: 09-01-2025*
*For: Next Developer*
*By: Development Team*
*Questions: Check Episch Verhaal 3 document or ask in team chat*

**Remember: MVP in 2 dagen is achievable if you follow this plan!** 🚀
