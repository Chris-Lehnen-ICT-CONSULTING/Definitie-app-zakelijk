# Epic 3: Modern Web Lookup (Aangescherpt Plan)

**Epic Goal**: Werkende, deterministische web lookup die LLM-prompt verbetert en gebruikte bronnen transparant toont en bewaart (MVP zonder DB-migratie).

**Business Value**:
- Betere definitie kwaliteit door verrijkte context voor LLM
- Transparante bronverantwoording voor gebruikers
- Juridische compliance door traceerbare bronnen
- Deterministische ranking en deduplicatie

**Acceptance Criteria**:
- [ ] Provider adapters returnen uniform WebLookupResult contract
- [ ] Deterministische ranking met config weights en tiebreakers
- [ ] Bronnen opgeslagen in metadata.sources (geen DB migratie)
- [ ] UI toont bronnen uit metadata (geen eigen lookup)
- [ ] Prompt augmentatie respecteert token budget
- [ ] Juridische bronnen geprioriteerd indien enabled
- [ ] Offline tests groen (geen netwerk in CI)

## Progress Status (2025-09-03)

### ✅ Done
- Contract & normalisatie‑backbone geïmplementeerd
- Config‑gedreven weights en scoring
- Deterministische ranking & deduplicatie
- Orchestrator‑integratie (fase 2.5)
- Provenance tracking via `metadata.sources` (top‑K `used_in_prompt`)
- UI rendert bronnen vanuit `metadata.sources`
- Unit & integratie (mocked) tests groen
- Prompt‑augmentatie integratie in PromptServiceV2 (config‑gedreven)
- E2E‑verificatie van zichtbare prompt‑injectie (tokenbudget/prioritering)

### 🔄 In Progress - Story 3.1: Metadata First, Prompt Second
- **Status**: IMPLEMENTING
- **Focus**: Legacy wrapper removal in service_factory.py
- **Doel**: Sources zichtbaar maken in UI tijdens preview
- **Approach**: Optie B - Clean solution (verwijder LegacyGenerationResult)

### 📋 Next
- Complete Story 3.1 implementatie (2-4 uur)
- Provider-neutraliteit in prompt ("Bron 1" i.p.v. "wikipedia")
- Juridische citatie formatting voor autoritatieve bronnen
- UI feedback bij geen bronnen
- Legacy fallback‑resten volledig verwijderen

## Context & Requirements

### Huidige Situatie
- **5 verschillende implementaties** in legacy code (633+ regels)
- **ModernWebLookupService** partially implemented
- **Geen bronverantwoording** in UI of database
- **Encoding problemen** in legacy code
- **Caching ontbreekt** in moderne implementatie

### Doel
Web lookup moet:
1. **Context verrijken** voor betere LLM prompts (primair)
2. **Bronnen vastleggen** voor transparantie (secundair)
3. **Duplicaten detecteren** voordat nieuwe definities gemaakt worden
4. **Juridische bronnen** prioriteren bij relevante begrippen

### Scope
- **IN SCOPE**:
  - Adapters → normalisatie → ranking/dedup
  - Orchestrator-enrichment → prompt-augmentatie
  - UI-render vanuit metadata → offline E2E tests
  - Legacy cleanup (na groene E2E)

- **OUT OF SCOPE (nu)**:
  - Nieuwe DB-tabel voor bronnen (volgende sprint)
  - Geavanceerde caching/rate-limiting
  - Nieuwe lookup bronnen toevoegen
  - Real-time updates van bronnen

## Technical Design

### Unified Contract (CRITICAL - Fase 0)
```python
@dataclass
class WebLookupResult:
    # Core Fields (Codex + Improvements)
    provider: str           # "wikipedia", "sru_overheid", etc
    source_label: str       # "Wikipedia NL", "Overheid.nl"
    title: str             # Artikel/document titel
    url: str               # Absolute URL (validated)
    snippet: str           # Gesaneerd, max 500 chars, escaped
    score: float           # 0.0-1.0 normalized

    # Usage Tracking
    used_in_prompt: bool   # Explicitly tracked
    position_in_prompt: int # Order in context pack

    # Metadata
    retrieved_at: datetime
    content_hash: str      # SHA256 voor deduplicatie
    error: Optional[str]   # Error taxonomy: TIMEOUT|NETWORK|PARSE|RATE_LIMIT

    # Juridisch (Nederlandse Overheid specifiek)
    legal_refs: list[str]  # ECLI, wetsartikelen, AMvB
    is_authoritative: bool # Overheid.nl/rechtspraak.nl = true
    legal_weight: float    # Voor CON-02 compliance

    # Linguistic (Legacy preservation)
    is_plurale_tantum: bool      # Meervoudsdetectie
    requires_singular_check: bool # Validatie hint

    # Caching
    cache_key: str         # provider:query_normalized:context_hash
    ttl_seconds: int       # Provider-specific TTL
```

### Ranking & Deduplication Rules
```python
# Deterministic ranking
final_score = provider_weight × normalized_score

# Tiebreakers (in order):
1. final_score DESC
2. is_authoritative DESC (juridisch eerst)
3. title ASC
4. url ASC

# Deduplication:
- Primary: canonical URL (normalized)
- Secondary: content_hash
- Keep: highest final_score
```

### Error Taxonomy
```python
class LookupErrorType(Enum):
    TIMEOUT = "Provider timeout exceeded"
    NETWORK = "Network connection failed"
    PARSE = "Response parsing failed"
    RATE_LIMIT = "Rate limit exceeded"
    AUTH = "Authentication failed"
    INVALID_RESPONSE = "Invalid/empty response"
```

### Content Sanitization Policy
```yaml
sanitization:
  strip_tags: [script, style, iframe, object, embed, form]
  block_protocols: [javascript, data, vbscript]
  escape: [html_entities, unicode_control]
  normalize:
    - collapse_whitespace
    - remove_empty_lines
    - trim_length: 500
  url_validation:
    - must_be_absolute
    - allowed_protocols: [http, https]
    - domain_allowlist: # Optional
      - "*.overheid.nl"
      - "*.rechtspraak.nl"
      - "wikipedia.org"
```

### Database Schema (Fase 2 - After MVP)
```sql
-- Pragmatic schema - essentials only, metadata as JSON
CREATE TABLE definitie_bronnen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    definitie_id INTEGER REFERENCES definities(id),

    -- Essentials only
    source_type VARCHAR(50) NOT NULL,
    url TEXT NOT NULL,
    title VARCHAR(500),
    snippet TEXT,
    score DECIMAL(3,2),
    used_in_prompt BOOLEAN DEFAULT FALSE,

    -- Flexible metadata as JSON
    metadata JSON,  -- legal_refs, cache_info, linguistic_data, etc.

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_definitie_id (definitie_id),
    INDEX idx_source_type (source_type),
    INDEX idx_used_in_prompt (definitie_id, used_in_prompt)
);
```

### MVP Approach (Fase 1.5 - No DB Migration)
```python
# Store in Definition.metadata.sources
definition.metadata = {
    "sources": [
        {
            "provider": "wikipedia",
            "title": "...",
            "url": "...",
            "snippet": "...",
            "score": 0.85,
            "used_in_prompt": True,
            "retrieved_at": "2025-01-09T10:00:00Z"
        }
    ],
    # Other metadata...
}
```

### Provider Configuration
```yaml
web_lookup:
  enabled: true
  cache:
    ttl_default: 3600
    max_entries: 1000

  providers:
    wikipedia:
      enabled: true
      weight: 0.7
      timeout: 5
      cache_ttl: 7200
      min_score: 0.3
      max_results: 3

    sru_overheid:
      enabled: true
      weight: 1.0  # Hoogste voor juridisch
      timeout: 5
      cache_ttl: 3600
      min_score: 0.4
      max_results: 5

    wiktionary:
      enabled: true
      weight: 0.5
      timeout: 3
      cache_ttl: 86400
      max_results: 2
```

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Legacy code breaking | Medium | High | Feature flag, parallel run |
| External API downtime | High | Medium | Aggressive caching, fallbacks |
| Performance degradation | Low | High | Parallellisatie, monitoring |
| Encoding issues | Medium | Low | UTF-8 normalization layer |
| Rate limiting by APIs | Medium | Medium | Per-provider limiters |

## Dependencies

- **External APIs**: Wikipedia, Wiktionary, Overheid.nl SRU
- **Internal**: PromptServiceV2, ValidationOrchestratorV2
- **Database**: SQLite migration required
- **UI**: Streamlit components update

## Success Metrics

- **Performance**: P95 latency <500ms (cached), <3s (uncached)
- **Availability**: >99% uptime excluding external API issues
- **Quality**: >80% of definitions have relevant sources
- **Coverage**: 100% backward compatibility with legacy

### Context-Wet Mapping (Nederlandse Overheid)
```yaml
context_mappings:
  DJI: ["Pbw", "Penitentiaire beginselenwet", "WvSr"]
  OM: ["WvSv", "Wetboek van Strafvordering"]
  Rechtspraak: ["Rv", "Wetboek van Burgerlijke Rechtsvordering"]
  CJIB: ["Wahv", "Mulder"]
  IND: ["Vw", "Vreemdelingenwet"]
```

### Caching Strategy
```yaml
cache:
  strategy: "stale-while-revalidate"
  grace_period: 300  # 5 min stale OK while refreshing
  background_refresh: true
  key_pattern: "{provider}:{query_normalized}:{context_hash}"
  storage: "memory"  # or "redis" for production
  limits:
    max_entries: 1000
    max_memory_mb: 100
```

---

## Story 3.0: Contract Validation & Specification (NEW - Fase 0)

Als een **architect**,
Wil ik **het web lookup contract volledig gespecificeerd en gevalideerd hebben**,
Zodat **alle implementaties exact dezelfde interface gebruiken zonder latere refactoring**.

### Acceptance Criteria
1. WebLookupResult contract volledig gedefinieerd
2. Error taxonomy vastgesteld
3. Ranking & deduplication rules gedocumenteerd
4. Sanitization policy gespecificeerd
5. Context-wet mappings voor Nederlandse overheid
6. Contract review met stakeholders completed

### Deliverables
- [ ] `docs/technical/web-lookup-contract-v1.0.md`
- [ ] `src/services/web_lookup/contracts.py` (types only)
- [ ] `config/web_lookup_defaults.yaml`
- [ ] Contract validation checklist
- [ ] Sign-off van tech lead

### Definition of Done
- [ ] Contract peer reviewed
- [ ] No ambiguities in specification
- [ ] All edge cases documented
- [ ] Backwards compatibility verified

### Estimated Effort: 0.5 dag

---

## Story 3.1a: Metadata MVP Implementation (SPLIT - Fase 1.5)

Als een **developer**,
Wil ik **bronnen opslaan in metadata zonder database migration**,
Zodat **we snel een werkende MVP hebben zonder schema changes**.

### Acceptance Criteria
1. Sources stored in Definition.metadata.sources array
2. No database schema changes required
3. Sources persist with definition
4. Export includes sources from metadata
5. Backward compatible with existing metadata structure
6. No performance degradation

### Technical Tasks
- [ ] Update Definition model to handle metadata.sources
- [ ] Create source serialization/deserialization logic
- [ ] Update repository save/load for metadata
- [ ] Ensure export_service reads from metadata
- [ ] Write unit tests for metadata persistence

### Definition of Done
- [ ] Sources persist in metadata
- [ ] No database changes
- [ ] Export contains sources
- [ ] All tests passing

### Estimated Effort: 0.5 dag

---

## Story 3.1b: Database Migration (LATER - Fase 2)

Als een **developer**,
Wil ik **bronnen in een dedicated database tabel opslaan**,
Zodat **we robuuste querying en reporting kunnen doen**.

### Acceptance Criteria
1. Database migration voor definitie_bronnen tabel
2. Repository methods voor CRUD operations
3. Migration from metadata to database
4. Backwards compatibility maintained
5. Query performance optimized with indexes

### Technical Tasks
- [ ] Write migration `migrations/004_add_definitie_bronnen.sql`
- [ ] Implement BronnenRepository
- [ ] Create data migration script (metadata → DB)
- [ ] Add database indexes
- [ ] Performance testing

### Definition of Done
- [ ] Migration tested on production-like data
- [ ] No data loss during migration
- [ ] Query performance <100ms
- [ ] Rollback procedure documented

### Estimated Effort: 1 dag

---

## Story 3.2: Provider Adapters & Caching Layer

Als een **system**,
Wil ik **unified adapters voor alle lookup providers met caching**,
Zodat **externe API calls geminimaliseerd worden en performance verbetert**.

### Acceptance Criteria
1. Adapters voor alle 7 legacy bronnen
2. Unified interface implementation voor elke adapter
3. TTL cache per provider + query
4. Content sanitization (HTML/XSS stripping)
5. Juridische referentie extraction
6. Rate limiting per provider

### Technical Tasks
- [ ] Refactor WikipediaAdapter naar unified contract
- [ ] Refactor SRUAdapter (Overheid.nl)
- [ ] Implement WiktionaryAdapter
- [ ] Implement remaining 4 legacy adapters
- [ ] Create CacheManager met TTL en LRU eviction
- [ ] Add content sanitization utilities
- [ ] Implement rate limiters per provider
- [ ] Add juridische regex patterns
- [ ] Write integration tests met mocked responses

### Provider Priority
1. **Wikipedia** - Algemene context (weight: 0.7)
2. **SRU/Overheid** - Juridische bronnen (weight: 1.0)
3. **Wiktionary** - Taalkundige info (weight: 0.5)
4. **Others** - Legacy compatibility

### Definition of Done
- [ ] All adapters return WebLookupResult
- [ ] Cache hit ratio >70% in tests
- [ ] No external API calls in unit tests
- [ ] Rate limiting verified
- [ ] Performance benchmarks documented

### Estimated Effort: 3-4 dagen

---

## Story 3.3: UI Integration & Bronverantwoording

Als een **gebruiker**,
Wil ik **de gebruikte bronnen zien bij mijn gegenereerde definitie**,
Zodat **ik de herkomst en betrouwbaarheid kan beoordelen**.

### Acceptance Criteria
1. Bronnen sectie in definition_generator_tab
2. Expandable list met titel, bron, URL
3. Snippet weergave (max 200 chars in UI)
4. Confidence/score indicators
5. DEV_MODE toont extra metadata
6. Graceful handling van lege bronnen
7. Loading states tijdens lookup

### UI Components
```python
# In definition_generator_tab.py
if generation_result.get("sources"):
    st.markdown("### 📚 Gebruikte Bronnen")
    for source in sources:
        with st.expander(f"{source.source_label}: {source.title}"):
            st.write(f"**URL:** {source.url}")
            st.write(f"**Fragment:** {source.snippet[:200]}...")
            if DEV_MODE:
                st.caption(f"Score: {source.score:.2f}")
```

### Technical Tasks
- [ ] Update definition_generator_tab.py
- [ ] Create bronnen display component
- [ ] Add loading spinners
- [ ] Implement error boundaries
- [ ] Add DEV_MODE debug info
- [ ] Style with CSS for readability
- [ ] Add accessibility labels
- [ ] Write UI tests

### Definition of Done
- [ ] UI displays sources correctly
- [ ] All URLs are clickable
- [ ] Graceful degradation without sources
- [ ] Responsive design verified
- [ ] Accessibility standards met

### Estimated Effort: 2 dagen

---

## Story 3.4: Prompt Integration & Export Enhancement

Als een **system**,
Wil ik **bronnen integreren in de prompt context en exports**,
Zodat **de LLM betere definities genereert en exports compleet zijn**.

### Acceptance Criteria
1. Context pack building met top-K sources
2. Sources marked met used_in_prompt=true
3. Prompt template integratie
4. Export formats (JSON/TXT) bevatten bronnen
5. Provenance tracking through full chain
6. Token budget management

### Context Pack Strategy
```python
def build_context_pack(
    sources: list[WebLookupResult],
    max_tokens: int = 1000
) -> tuple[str, list[WebLookupResult]]:
    """Build context for prompt with source tracking."""
    # Sort by score, take top-K within token budget
    # Mark used sources with used_in_prompt=true
    # Return formatted context + used sources
```

### Export Format
```json
{
  "definitie": {
    "begrip": "...",
    "definitie": "...",
    "bronnen": [
      {
        "bron": "Wikipedia NL",
        "titel": "...",
        "url": "...",
        "gebruikt": true
      }
    ]
  }
}
```

### Technical Tasks
- [ ] Update PromptServiceV2 voor context pack
- [ ] Implement source tracking through chain
- [ ] Update export_service.py
- [ ] Add bronnen to JSON export
- [ ] Add bronnen to TXT export
- [ ] Token counting utilities
- [ ] Write integration tests

### Definition of Done
- [ ] Sources appear in prompts
- [ ] Exports contain sources
- [ ] Token budget not exceeded
- [ ] Provenance chain complete
- [ ] All formats tested

### Estimated Effort: 2 dagen

---

## Implementation Phases (Aangescherpt)

### Fase 1: Provider Adapters op Contract (1-1.5u)
- **Wikipedia adapter**: Return uniform WebLookupResult
  - provider, source_label, title, url, snippet (gesaneerd)
  - score (genormaliseerd 0-1), is_authoritative=false
  - retrieved_at, content_hash
- **SRU adapter**: Idem contract met is_authoritative=true
- **ModernWebLookupService**:
  - Gebruik config weights/min_score_threshold
  - Pas rank_and_dedup toe
  - Markeer top-K used_in_prompt

### Fase 2: E2E zonder Netwerk (1-1.5u)
- **Orchestrator integratie** (enable_web_lookup=true):
  - Mock adapters
  - Verify metadata.sources gevuld
  - Top-K marked used_in_prompt=true
- **Prompt augmentatie** (via config):
  - Injecteer ≤ K snippets
  - Respecteer token budget
  - Geen prompt-corruptie
- **UI verificatie**:
  - Render metadata.sources
  - Geen eigen lookup pad

### Fase 3: Legacy Cleanup (0.5u) - NA GROENE E2E
- Verwijder lege `src/web_lookup/` directory
- Remove/guard legacy fallback in ModernWebLookupService
- Verwijder ongebruikte imports

### Fase 4: Tests & Acceptatie (0.5u)
- Unit tests (offline): adapters → contract
- Orchestrator E2E met mocks
- UI smoke test: bronnen-sectie correct

## Configuratie (Instelbaar)

```yaml
web_lookup:
  prompt_augmentation:
    enabled: false  # Feature flag
    max_snippets: 3
    max_tokens_per_snippet: 100
    total_token_budget: 400
    position: after_context  # before_examples | after_context | prepend
    prioritize_juridical: true
    section_header: "### Contextinformatie uit bronnen:"
    snippet_separator: "\n- "

orchestrator:
  enable_web_lookup: true
  web_lookup_top_k: 3

providers:
  wikipedia:
    weight: 0.7
    min_score: 0.3
  sru_overheid:
    weight: 1.0  # Juridisch authoritative
    min_score: 0.4
```

## Concrete TODO's (Geprioriteerd)

1. Fix Wikipedia adapter contract compliance (voeg o.a. `content_hash`, `is_authoritative` toe)
2. Fix SRU adapter contract compliance (idem contractvelden)
3. Add sanitization to adapter outputs (hard sanitization policy toepassen)
4. Create offline end-to-end test with mocked providers (deterministisch)
5. Test orchestrator web lookup integration (metadata.sources/used_in_prompt)
6. Implement token-safe prompt augmentation (config‑gedreven)
7. Add juridical prioritization for snippets (stabiele tiebreakers)
8. Remove legacy fallback code from modern service (geen directory cleanup vereist)

## Risico's & Mitigatie

- **Token lengte**: Heuristiek 4 chars ≈ 1 token + harde char-cap
- **Drift**: Orchestrator bepaalt ranking/used_in_prompt; prompt-laag herordent niet
- **Cleanup**: Pas uitvoeren na groene E2E tests

## Test Strategy & TDD Suite

### Test-Driven Development Approach

Voor Epic 3 hanteren we een strikt TDD proces: **schrijf tests VOORDAT de implementatie begint**.

### Test Categories & Coverage Targets

| Component | Coverage Target | Priority |
|-----------|----------------|----------|
| WebLookupResult Contract | 100% | Critical |
| Provider Adapters | 95% | High |
| Caching Layer | 90% | High |
| Ranking & Deduplication | 100% | Critical |
| Content Sanitization | 100% | Critical |
| UI Components | 80% | Medium |
| Export Integration | 85% | Medium |

### Phase 0: Contract Validation Tests (WRITE FIRST)

```python
# tests/services/web_lookup/test_contracts.py
import pytest
from datetime import datetime
from src.services.web_lookup.contracts import WebLookupResult, LookupErrorType

class TestWebLookupResultContract:
    """Test suite voor WebLookupResult dataclass contract."""

    def test_required_fields_validation(self):
        """Test dat alle required fields aanwezig moeten zijn."""
        with pytest.raises(TypeError):
            # Missing required fields
            WebLookupResult(provider="wikipedia")

    def test_score_normalization(self):
        """Test score moet tussen 0.0 en 1.0 zijn."""
        result = WebLookupResult(
            provider="wikipedia",
            source_label="Wikipedia NL",
            title="Test",
            url="https://example.com",
            snippet="Test snippet",
            score=0.85,
            used_in_prompt=False,
            position_in_prompt=0,
            retrieved_at=datetime.now(),
            content_hash="abc123"
        )
        assert 0.0 <= result.score <= 1.0

    def test_url_validation(self):
        """Test dat URL absolute moet zijn."""
        with pytest.raises(ValueError):
            WebLookupResult(
                provider="test",
                url="/relative/path",  # Should fail
                # ... other required fields
            )

    def test_snippet_max_length(self):
        """Test snippet truncation naar 500 chars."""
        long_snippet = "x" * 1000
        result = WebLookupResult(
            snippet=long_snippet,
            # ... other fields
        )
        assert len(result.snippet) <= 500

    def test_error_taxonomy(self):
        """Test error types uit de taxonomy."""
        for error_type in LookupErrorType:
            result = WebLookupResult(
                error=error_type.value,
                # ... other fields
            )
            assert result.error in [e.value for e in LookupErrorType]
```

### Phase 1: Provider Adapter Tests

```python
# tests/services/web_lookup/test_wikipedia_adapter.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.services.web_lookup.wikipedia_adapter import WikipediaAdapter

class TestWikipediaAdapter:
    """TDD tests voor Wikipedia adapter."""

    @pytest.fixture
    def adapter(self):
        return WikipediaAdapter()

    @pytest.fixture
    def mock_wikipedia_response(self):
        """Mock Wikipedia API response."""
        return {
            "query": {
                "pages": {
                    "12345": {
                        "title": "Gevangenis",
                        "extract": "Een gevangenis is een gebouw...",
                        "fullurl": "https://nl.wikipedia.org/wiki/Gevangenis"
                    }
                }
            }
        }

    @pytest.mark.asyncio
    async def test_successful_lookup(self, adapter, mock_wikipedia_response):
        """Test succesvolle Wikipedia lookup."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = AsyncMock(
                status_code=200,
                json=lambda: mock_wikipedia_response
            )

            results = await adapter.lookup("gevangenis", {})

            assert len(results) > 0
            assert results[0].provider == "wikipedia"
            assert results[0].source_label == "Wikipedia NL"
            assert "gevangenis" in results[0].title.lower()
            assert results[0].url.startswith("https://")

    @pytest.mark.asyncio
    async def test_timeout_handling(self, adapter):
        """Test timeout error handling."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = asyncio.TimeoutError()

            results = await adapter.lookup("test", {})

            assert len(results) == 1
            assert results[0].error == LookupErrorType.TIMEOUT.value

    @pytest.mark.asyncio
    async def test_html_sanitization(self, adapter):
        """Test HTML stripping uit content."""
        mock_response = {
            "extract": "<script>alert('xss')</script>Clean content"
        }

        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = AsyncMock(json=lambda: mock_response)

            results = await adapter.lookup("test", {})

            assert "<script>" not in results[0].snippet
            assert "Clean content" in results[0].snippet
```

### Phase 1.5: Cache Layer Tests

```python
# tests/services/web_lookup/test_cache.py
import pytest
import time
from src.services.web_lookup.cache import SimpleCache, CacheKey

class TestSimpleCache:
    """TDD tests voor caching layer."""

    def test_cache_hit(self):
        """Test cache hit scenario."""
        cache = SimpleCache(max_entries=10)
        key = CacheKey.generate("wikipedia", "test", {})
        value = ["cached_result"]

        cache.set(key, value, ttl=60)
        cached = cache.get(key)

        assert cached == value

    def test_cache_expiration(self):
        """Test TTL expiration."""
        cache = SimpleCache()
        key = "test_key"

        cache.set(key, "value", ttl=0.1)  # 100ms TTL
        time.sleep(0.2)

        assert cache.get(key) is None

    def test_lru_eviction(self):
        """Test LRU eviction bij max entries."""
        cache = SimpleCache(max_entries=2)

        cache.set("key1", "value1", ttl=60)
        cache.set("key2", "value2", ttl=60)
        cache.set("key3", "value3", ttl=60)  # Should evict key1

        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

    def test_stale_while_revalidate(self):
        """Test stale-while-revalidate strategy."""
        cache = SimpleCache(grace_period=5)

        cache.set("key", "value", ttl=1)
        time.sleep(1.5)  # Past TTL but within grace

        value, needs_refresh = cache.get_with_grace("key")
        assert value == "value"
        assert needs_refresh is True
```

### Phase 2: Ranking & Deduplication Tests

```python
# tests/services/web_lookup/test_ranking.py
import pytest
from src.services.web_lookup.ranking import rank_results, deduplicate

class TestRankingDeterminism:
    """Test deterministische ranking."""

    def test_identical_input_same_output(self):
        """Test dat identieke input altijd zelfde volgorde geeft."""
        results = [
            WebLookupResult(score=0.8, provider="wikipedia", ...),
            WebLookupResult(score=0.8, provider="wiktionary", ...),
            WebLookupResult(score=0.8, provider="overheid", ...)
        ]

        ranked1 = rank_results(results.copy(), {})
        ranked2 = rank_results(results.copy(), {})

        assert [r.provider for r in ranked1] == [r.provider for r in ranked2]

    def test_tiebreaker_rules(self):
        """Test tiebreaker volgorde: score > authoritative > title > url."""
        results = [
            WebLookupResult(score=0.5, is_authoritative=False, title="B", ...),
            WebLookupResult(score=0.5, is_authoritative=True, title="A", ...),
            WebLookupResult(score=0.8, is_authoritative=False, title="C", ...)
        ]

        ranked = rank_results(results, {})

        assert ranked[0].score == 0.8  # Highest score first
        assert ranked[1].is_authoritative == True  # Then authoritative
        assert ranked[2].title == "B"  # Then by title

    def test_juridisch_context_boost(self):
        """Test juridische bronnen krijgen boost."""
        context = {"juridisch": True}
        results = [
            WebLookupResult(score=0.5, is_authoritative=False, ...),
            WebLookupResult(score=0.5, is_authoritative=True, ...)
        ]

        ranked = rank_results(results, context)

        assert ranked[0].is_authoritative == True
        assert ranked[0].final_score > ranked[1].final_score
```

### Phase 3: Content Sanitization Tests

```python
# tests/services/web_lookup/test_sanitization.py
import pytest
from src.services.web_lookup.sanitization import sanitize_content

class TestContentSanitization:
    """Test content sanitization voor security."""

    @pytest.mark.parametrize("input,expected", [
        ("<script>alert('xss')</script>text", "text"),
        ("<iframe src='evil.com'></iframe>", ""),
        ("javascript:alert(1)", ""),
        ("<a href='javascript:void(0)'>link</a>", "link"),
        ("Normal text with &lt;entities&gt;", "Normal text with <entities>")
    ])
    def test_xss_prevention(self, input, expected):
        """Test XSS attack prevention."""
        sanitized = sanitize_content(input)
        assert sanitized == expected

    def test_url_validation(self):
        """Test URL validation en normalisatie."""
        valid_urls = [
            "https://example.com",
            "http://test.nl",
            "https://sub.domain.com/path"
        ]
        invalid_urls = [
            "javascript:alert(1)",
            "data:text/html,<script>",
            "vbscript:msgbox",
            "/relative/path"
        ]

        for url in valid_urls:
            assert validate_url(url) is True

        for url in invalid_urls:
            assert validate_url(url) is False
```

### Phase 3.5: UI Component Tests

```python
# tests/ui/test_render_sources_section.py
import pytest
import streamlit as st
from unittest.mock import Mock, patch, MagicMock
from src.ui.components.definition_generator_tab import DefinitionGeneratorTab

class TestRenderSourcesSection:
    """Tests voor bestaande _render_sources_section method."""

    @pytest.fixture
    def tab(self):
        """Create DefinitionGeneratorTab instance."""
        with patch('streamlit.session_state', {}):
            return DefinitionGeneratorTab()

    def test_render_sources_from_metadata(self, tab):
        """Test rendering sources uit metadata.sources."""
        metadata = {
            "sources": [
                {
                    "provider": "wikipedia",
                    "source_label": "Wikipedia NL",
                    "title": "Gevangenis",
                    "url": "https://nl.wikipedia.org/wiki/Gevangenis",
                    "snippet": "Een gevangenis is een gebouw...",
                    "score": 0.85,
                    "used_in_prompt": True
                }
            ]
        }

        with patch('streamlit.expander') as mock_expander:
            tab._render_sources_section(metadata, None)

            # Verify expander created with correct title
            mock_expander.assert_called_with(
                "Wikipedia NL: Gevangenis",
                expanded=False
            )

    def test_render_multiple_sources(self, tab):
        """Test rendering multiple sources sorted by score."""
        metadata = {
            "sources": [
                {"score": 0.5, "provider": "wiktionary", ...},
                {"score": 0.9, "provider": "overheid", ...},
                {"score": 0.7, "provider": "wikipedia", ...}
            ]
        }

        with patch('streamlit.expander'):
            tab._render_sources_section(metadata, None)

            # Verify sources sorted by score descending
            rendered_order = [s["provider"] for s in metadata["sources"]]
            assert rendered_order[0] == "overheid"  # Highest score

    def test_dev_mode_shows_extra_info(self, tab):
        """Test DEV_MODE shows score and position."""
        metadata = {
            "sources": [{
                "score": 0.85,
                "position_in_prompt": 1,
                "used_in_prompt": True,
                ...
            }]
        }

        with patch('os.getenv', return_value="true"):
            with patch('streamlit.caption') as mock_caption:
                tab._render_sources_section(metadata, None)

                # Verify debug info shown
                mock_caption.assert_any_call("Score: 0.85")
                mock_caption.assert_any_call("Position in prompt: 1")

    def test_empty_sources_graceful(self, tab):
        """Test graceful handling of empty sources."""
        metadata = {"sources": []}

        with patch('streamlit.info') as mock_info:
            tab._render_sources_section(metadata, None)

            mock_info.assert_called_with("Geen bronnen gevonden")
```

### Phase 4: Integration Tests

```python
# tests/integration/test_web_lookup_flow.py
import pytest
from src.services.web_lookup.service import ModernWebLookupService

class TestWebLookupIntegration:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_full_lookup_flow(self):
        """Test complete lookup → rank → dedupe → pack flow."""
        service = ModernWebLookupService()

        # Perform lookup
        results = await service.lookup_enriched(
            query="gevangenis",
            context={"organisatie": "DJI", "juridisch": True}
        )

        # Verify contract
        assert all(isinstance(r, WebLookupResult) for r in results)

        # Verify ranking
        scores = [r.final_score for r in results]
        assert scores == sorted(scores, reverse=True)

        # Verify deduplication
        urls = [r.url for r in results]
        assert len(urls) == len(set(urls))

        # Verify context pack
        context_pack, used = service.build_context_pack(results)
        assert all(r.used_in_prompt for r in used)
        assert len(context_pack) <= 1000  # Token limit
```

### Performance Benchmarks

```python
# tests/performance/test_benchmarks.py
import pytest
import time
from statistics import mean, stdev

class TestPerformanceBenchmarks:
    """Performance benchmark tests."""

    @pytest.mark.benchmark
    def test_cached_lookup_performance(self, benchmark):
        """Benchmark cached lookup performance."""
        service = ModernWebLookupService()

        # Prime cache
        service.lookup("test", {})

        # Benchmark cached lookup
        result = benchmark(service.lookup, "test", {})

        assert benchmark.stats["mean"] < 0.5  # <500ms P95

    @pytest.mark.benchmark
    def test_parallel_lookup_performance(self, benchmark):
        """Test parallel provider lookup performance."""
        service = ModernWebLookupService()

        def parallel_lookup():
            return service.lookup_all_providers("test", {})

        result = benchmark(parallel_lookup)

        assert benchmark.stats["max"] < 3.0  # <3s worst case
```

### Mock Response Fixtures

```python
# tests/fixtures/mock_responses.py
import pytest
from pathlib import Path
import json

@pytest.fixture
def wikipedia_fixtures():
    """Load Wikipedia mock responses."""
    fixtures_dir = Path(__file__).parent / "wikipedia"
    return {
        "success": json.loads((fixtures_dir / "success.json").read_text()),
        "empty": json.loads((fixtures_dir / "empty.json").read_text()),
        "error": json.loads((fixtures_dir / "error.json").read_text())
    }

@pytest.fixture
def overheid_fixtures():
    """Load Overheid.nl SRU mock responses."""
    fixtures_dir = Path(__file__).parent / "overheid"
    return {
        "pbw": (fixtures_dir / "pbw.xml").read_text(),
        "wvsr": (fixtures_dir / "wvsr.xml").read_text(),
        "empty": (fixtures_dir / "empty.xml").read_text()
    }
```

### Test Execution Strategy

```bash
# Run tests in order of dependency
pytest tests/services/web_lookup/test_contracts.py -v  # First: contracts
pytest tests/services/web_lookup/test_*.py -v          # Then: units
pytest tests/integration/ -v                           # Then: integration
pytest tests/performance/ -v --benchmark-only          # Finally: performance

# Coverage report
pytest --cov=src/services/web_lookup --cov-report=html --cov-report=term

# Watch mode for TDD
pytest-watch tests/services/web_lookup/ --runner="pytest -xvs"
```

## Implementation Plan (REVISED with TDD)

### Fase 0: Contract & Specification (0.5 dag)
- **FIRST**: Write all contract validation tests ✅
- Define WebLookupResult contract to pass tests
- Get stakeholder sign-off on test cases

### Fase 1: Core Service (1-2 dagen)
- **Day 1 Morning**: Write Wikipedia adapter tests
- **Day 1 Afternoon**: Implement Wikipedia adapter to pass tests
- **Day 2 Morning**: Write SRU/Overheid adapter tests
- **Day 2 Afternoon**: Implement SRU adapter to pass tests

### Fase 1.5: Quick Win Provenance (0.5 dag)
- Write metadata storage tests
- Implement Story 3.1a to pass tests
- Write UI component tests
- Implement Story 3.3 to pass tests

### Fase 2: Database & Robustness (1 dag)
- Write migration tests
- Implement Story 3.1b database migration
- Write performance tests
- Optimize to meet benchmarks

### Fase 3: Full Implementation (1-2 dagen)
- Write tests for remaining 5 providers
- Implement providers to pass tests
- Write deduplication tests
- Implement dedup to pass tests

### Fase 4: Quality & Testing (0.5-1 dag)
- Complete integration test suite
- Performance benchmark validation
- Documentation generation from tests
- CI/CD pipeline integration

### Total Estimated Effort: 4-7 dagen (met TDD approach)

## MVP Definition (Fase 0-1.5)

**Minimal Viable Product in 2 dagen:**
- ✅ Contract defined
- ✅ Wikipedia + Overheid.nl working
- ✅ Sources in metadata (no DB)
- ✅ Basic UI shows sources
- ✅ Export includes sources
- ✅ Deterministic ranking
- ✅ Basic caching

**This delivers immediate value without:**
- ❌ Database changes
- ❌ All 7 providers
- ❌ Complex caching
- ❌ Duplicate detection

## Monitoring & Success Tracking

### KPIs
- Cache hit ratio: >70%
- Lookup latency P95: <500ms (cached)
- Source availability: >95%
- User satisfaction: Sources helpful rating

### Dashboards
- Provider availability status
- Cache performance metrics
- API rate limit usage
- Error rates by provider

## Rollout Strategy

1. **Phase 1**: Deploy behind feature flag (DEV_MODE)
2. **Phase 2**: Enable for test users (10%)
3. **Phase 3**: Gradual rollout (25%, 50%, 100%)
4. **Phase 4**: Deprecate legacy code

## Documentation Requirements

- [ ] Update architecture diagrams
- [ ] API documentation for WebLookupService
- [ ] User guide for bronnen interpretation
- [ ] Runbook for provider issues

## Final Acceptance Criteria (Combined)

### Fase 1 (MVP)
- [ ] Uniform contract implemented
- [ ] Wikipedia + Overheid.nl operational
- [ ] Deterministic ranking (tiebreakers work)
- [ ] Cache hit >60% in tests
- [ ] Offline tests 100% passing
- [ ] Sources in metadata.sources

### Fase 2 (Integration)
- [ ] UI shows sources with title/url/snippet
- [ ] Export contains structured sources
- [ ] DEV_MODE shows debug info
- [ ] Database migration complete
- [ ] No data loss during migration

### Fase 3 (Complete)
- [ ] All 7 providers operational
- [ ] Duplicate detection active (0.7 threshold)
- [ ] Juridische refs extracted
- [ ] Context-wet mapping works
- [ ] P95 latency <500ms (cached)
- [ ] Stale-while-revalidate caching

### Quality Gates
- [ ] No uncaught exceptions
- [ ] Error taxonomy implemented
- [ ] Sanitization policy enforced
- [ ] URL validation active
- [ ] Deterministic results verified
- [ ] Performance benchmarks met

---

*Generated: 2025-01-09*
*Epic Owner: Development Team*
*Status: Planning*
*Estimated Total: 4-7 dagen (MVP in 2 dagen)*
