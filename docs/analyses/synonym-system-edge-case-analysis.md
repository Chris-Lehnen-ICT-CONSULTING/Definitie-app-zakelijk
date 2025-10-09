# Synonym Management System - Edge Case & Bug Analysis

## Executive Summary

Deze analyse identificeert potentiële problemen, edge cases, en bugs in het voorgestelde synonym management systeem voor DefinitieAgent. Het systeem gebruikt een database-first approach met AI fallback voor synonym generatie en management.

## Systeem Architectuur Context

### Huidige Situatie
- **YAML-based**: `config/juridische_synoniemen.yaml` met weighted synonyms
- **Service**: `JuridischeSynoniemlService` als singleton met caching
- **Integratie**: Web lookup service gebruikt synoniemen voor query expansion

### Voorgestelde Flow
```
IF term heeft geen synoniemen in DB:
    CALL OpenAI API voor 5 synoniemen
    USE voor web lookup + definitie
ELSE:
    GET synoniemen uit DB (voorkeursterm eerst)
    IF count < 5:
        CALL OpenAI voor aanvulling
    USE top 5 voor beide doelen
```

## 1. Race Conditions

### 1.1 Concurrent Synonym Requests
**Probleem**: Meerdere gelijktijdige requests voor dezelfde term kunnen leiden tot dubbele API calls en database writes.

**Scenario**:
```python
# Thread 1 & 2 tegelijk:
synoniemen = repo.get_suggestions_for_hoofdterm("verdachte")
if not synoniemen:
    # Beide threads komen hier
    gpt_results = await gpt4.suggest_synonyms("verdachte")
    # Dubbele inserts → unique constraint violation
```

- **Waarschijnlijkheid**: HIGH (Streamlit reruns, multiple users)
- **Impact**: MAJOR (API kosten, database errors)
- **Detectie**: Monitor `UNIQUE constraint failed` errors in logs
- **Preventie**:
  ```python
  # In-memory request deduplication
  class SynonymService:
      def __init__(self):
          self._pending_requests = {}  # term -> asyncio.Future
          self._request_lock = asyncio.Lock()

      async def get_or_generate(self, term):
          async with self._request_lock:
              if term in self._pending_requests:
                  return await self._pending_requests[term]

              future = asyncio.Future()
              self._pending_requests[term] = future

          try:
              result = await self._generate_synonyms(term)
              future.set_result(result)
              return result
          finally:
              del self._pending_requests[term]
  ```
- **Testing**: Concurrent load testing met locust/pytest-asyncio

### 1.2 Cache Invalidation Race
**Probleem**: Cache update tijdens read operation kan inconsistente state opleveren.

**Scenario**:
```python
# Thread 1: Reading from cache
cached = self.synoniemen.get("onherroepelijk")

# Thread 2: Invalidating cache na DB update
self.synoniemen.clear()
self._load_synoniemen()

# Thread 1: Gebruikt stale data
return cached  # Mogelijk None of outdated
```

- **Waarschijnlijkheid**: MEDIUM (Cache TTL windows)
- **Impact**: MINOR (Temporary inconsistency)
- **Detectie**: Add cache version tracking
- **Preventie**: Gebruik read-write locks of immutable cache replacement
- **Testing**: Stress test met rapid cache invalidations

### 1.3 Database Write Conflicts
**Probleem**: SQLite WAL mode conflicts bij concurrent writes.

- **Waarschijnlijkheid**: LOW (WAL mode handles most cases)
- **Impact**: MINOR (Retry mechanism exists)
- **Detectie**: Monitor `database is locked` errors
- **Preventie**: Connection pooling met retry logic
- **Testing**: Concurrent write stress tests

## 2. Memory & Performance Issues

### 2.1 Unbounded Cache Growth
**Probleem**: Cache groeit onbeperkt bij veel unieke termen.

**Scenario**:
```python
# Elke nieuwe term wordt gecached
for term in zeer_grote_dataset:
    synoniemen = service.get_synoniemen(term)
    # Cache groeit lineair met unieke termen
```

- **Waarschijnlijkheid**: HIGH (Production usage)
- **Impact**: MAJOR (Memory exhaustion)
- **Detectie**: Monitor memory usage, cache size metrics
- **Preventie**:
  ```python
  from functools import lru_cache
  from cachetools import TTLCache

  class BoundedSynonymCache:
      def __init__(self, maxsize=10000, ttl=3600):
          self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
  ```
- **Testing**: Memory profiling met grote datasets

### 2.2 N+1 Query Problem
**Probleem**: Loop over termen triggert individuele DB queries.

**Scenario**:
```python
# UI code
for begrip in alle_begrippen:  # 100+ items
    suggestions = repo.get_suggestions_for_hoofdterm(begrip)
    # 100+ separate queries
```

- **Waarschijnlijkheid**: HIGH (Batch processing, export)
- **Impact**: MAJOR (Performance degradation)
- **Detectie**: SQL query logging, slow query analysis
- **Preventie**:
  ```python
  def get_bulk_suggestions(self, hoofdtermen: list[str]):
      placeholders = ','.join('?' * len(hoofdtermen))
      query = f"""
          SELECT * FROM synonym_suggestions
          WHERE hoofdterm IN ({placeholders})
          ORDER BY hoofdterm, confidence DESC
      """
      return self._execute_query(query, hoofdtermen)
  ```
- **Testing**: Performance tests met batch operations

### 2.3 API Rate Limiting Cascade
**Probleem**: Rate limit hit veroorzaakt retry storm.

**Scenario**:
```python
# Bulk processing hits rate limit
for term in terms[:100]:
    try:
        await gpt4.suggest(term)  # Hit rate limit at term 50
    except RateLimitError:
        await asyncio.sleep(1)
        retry()  # All subsequent calls fail fast
```

- **Waarschijnlijkheid**: MEDIUM (Batch operations)
- **Impact**: MAJOR (Complete failure of batch)
- **Detectie**: Rate limit error patterns in logs
- **Preventie**:
  ```python
  class AdaptiveRateLimiter:
      def __init__(self):
          self.delay = 1.0
          self.last_success = time.time()

      async def execute(self, func):
          await asyncio.sleep(self.delay)
          try:
              result = await func()
              self.delay = max(0.5, self.delay * 0.9)  # Speed up
              return result
          except RateLimitError:
              self.delay = min(60, self.delay * 2)  # Back off
              raise
  ```
- **Testing**: Rate limit simulation tests

### 2.4 Cold Start Latency
**Probleem**: Eerste request na idle periode is traag.

- **Waarschijnlijkheid**: HIGH (Development, low traffic)
- **Impact**: MINOR (User experience)
- **Detectie**: Response time monitoring
- **Preventie**: Warmup tijdens container init, connection pooling
- **Testing**: Cold start benchmarks

## 3. Data Consistency Issues

### 3.1 YAML vs Database Sync
**Probleem**: Migratie periode met dubbele sources of truth.

**Scenario**:
```python
# YAML heeft: verdachte -> [beklaagde, beschuldigde]
# DB heeft: verdachte -> [aangeklaagde, verdacht persoon]
# Which one wins?
```

- **Waarschijnlijkheid**: HIGH (During migration)
- **Impact**: CRITICAL (Wrong synonyms used)
- **Detectie**: Data validation scripts
- **Preventie**:
  ```python
  class MigrationSynonymService:
      def __init__(self):
          self.migration_mode = True

      def get_synoniemen(self, term):
          db_syns = self._get_from_db(term)
          yaml_syns = self._get_from_yaml(term)

          if self.migration_mode:
              # Merge strategy: DB overrides YAML
              return db_syns if db_syns else yaml_syns
          return db_syns
  ```
- **Testing**: Migration validation tests

### 3.2 Orphaned Synonyms
**Probleem**: Synoniemen zonder hoofdterm na deletes.

**Scenario**:
```sql
-- Hoofdterm deleted but synonyms remain
DELETE FROM definities WHERE begrip = 'oude_term';
-- synonym_suggestions still has entries for 'oude_term'
```

- **Waarschijnlijkheid**: MEDIUM (Manual operations)
- **Impact**: MINOR (Storage waste)
- **Detectie**: Orphan detection query
- **Preventie**: Cascade deletes, referential integrity
- **Testing**: Deletion scenario tests

### 3.3 Conflicting Preferred Terms
**Probleem**: Multiple terms claiming same synonym as preferred.

**Scenario**:
```yaml
aanhouding:
  - arrestatie (preferred)

vrijheidsberoving:
  - arrestatie (also preferred?)
```

- **Waarschijnlijkheid**: MEDIUM (Human error)
- **Impact**: MAJOR (Incorrect term selection)
- **Detectie**: Validation on insert/update
- **Preventie**: Unique constraint on preferred synonyms
- **Testing**: Conflict detection tests

## 4. Edge Cases

### 4.1 Empty/Null OpenAI Responses
**Probleem**: API returns geen bruikbare synoniemen.

**Scenario**:
```python
response = await openai.complete(prompt)
# response.choices[0].text = ""
# of response = {"error": "content_filter"}
```

- **Waarschijnlijkheid**: LOW (But happens)
- **Impact**: MAJOR (No fallback)
- **Detectie**: Response validation
- **Preventie**:
  ```python
  def validate_gpt_response(response):
      if not response or not response.choices:
          raise EmptyResponseError()

      text = response.choices[0].text.strip()
      if not text or len(text) < 3:
          raise InvalidResponseError()

      # Parse and validate JSON structure
      try:
          synonyms = json.loads(text)
          if not isinstance(synonyms, list) or len(synonyms) == 0:
              raise InvalidFormatError()
      except json.JSONDecodeError:
          raise ParseError()
  ```
- **Testing**: Mock empty responses

### 4.2 Network Timeouts During Critical Flow
**Probleem**: Timeout tijdens definitie generatie flow.

**Scenario**:
```python
# User clicks "Generate"
definition = await generate_definition(term)  # Works
synonyms = await fetch_synonyms(term)  # Timeout!
# Incomplete result shown to user
```

- **Waarschijnlijkheid**: MEDIUM (Network issues)
- **Impact**: MAJOR (Incomplete results)
- **Detectie**: Timeout monitoring
- **Preventie**: Circuit breaker pattern, graceful degradation
- **Testing**: Network fault injection

### 4.3 Circular Synonym References
**Probleem**: A→B→C→A synonym chains.

**Scenario**:
```yaml
rechtsmiddel:
  synoniemen: [beroep]
beroep:
  synoniemen: [hoger_beroep]
hoger_beroep:
  synoniemen: [rechtsmiddel]  # Circular!
```

- **Waarschijnlijkheid**: LOW (Manual curation)
- **Impact**: MAJOR (Infinite loops)
- **Detectie**: Graph cycle detection
- **Preventie**:
  ```python
  def detect_cycles(self, term, visited=None):
      if visited is None:
          visited = set()

      if term in visited:
          return True  # Cycle detected

      visited.add(term)
      for synonym in self.get_synoniemen(term):
          if self.detect_cycles(synonym, visited.copy()):
              return True
      return False
  ```
- **Testing**: Cycle detection unit tests

### 4.4 Unicode & Special Characters
**Probleem**: Synoniemen met speciale karakters breken parsing.

**Scenario**:
```python
# Synonym: "café's" or "naïef" or "§ 1.2"
yaml.safe_load(content)  # Encoding error
json.dumps(synonym)  # Unicode escape issues
```

- **Waarschijnlijkheid**: MEDIUM (Dutch legal terms)
- **Impact**: MINOR (Display issues)
- **Detectie**: Unicode validation
- **Preventie**: Proper encoding handling, normalization
- **Testing**: Unicode test suite

### 4.5 Case Sensitivity Issues
**Probleem**: Inconsistent casing leidt tot duplicates.

**Scenario**:
```python
# Database has both:
- "Verdachte"
- "verdachte"
- "VERDACHTE"
```

- **Waarschijnlijkheid**: HIGH (User input)
- **Impact**: MINOR (Duplicates)
- **Detectie**: Case-insensitive duplicate check
- **Preventie**: Normalize on insert, case-insensitive indices
- **Testing**: Case variation tests

## 5. Integration Bugs

### 5.1 Service Initialization Order
**Probleem**: Services initialized in wrong order.

**Scenario**:
```python
# Container initialization
synonym_service = SynonymService()  # Needs DB
db_service = DatabaseService()  # Not ready yet!
```

- **Waarschijnlijkheid**: MEDIUM (Refactoring)
- **Impact**: CRITICAL (Startup failure)
- **Detectie**: Dependency validation
- **Preventie**: Explicit dependency injection
- **Testing**: Initialization order tests

### 5.2 Streamlit Rerun State Issues
**Probleem**: State lost tussen reruns.

**Scenario**:
```python
# User edits synonym
st.session_state.edited_synonyms = [...]
# Page rerun triggered
# State lost if not properly persisted
```

- **Waarschijnlijkheid**: HIGH (Streamlit nature)
- **Impact**: MAJOR (Data loss)
- **Detectie**: State persistence checks
- **Preventie**: Proper session state management
- **Testing**: Rerun simulation tests

### 5.3 Cache vs Session Conflicts
**Probleem**: Global cache conflicts met user session.

**Scenario**:
```python
# User 1 approves synonym
cache.update(term, new_synonyms)

# User 2 still sees old cached version
display(cache.get(term))  # Stale!
```

- **Waarschijnlijkheid**: MEDIUM (Multi-user)
- **Impact**: MINOR (Temporary)
- **Detectie**: Cache consistency monitoring
- **Preventie**: User-scoped caching
- **Testing**: Multi-user scenarios

## 6. Production Issues

### 6.1 Rollback Scenarios
**Probleem**: Rollback na partial migration.

**Scenario**:
```sql
-- Migration 50% complete
-- Error occurs
-- How to rollback?
-- Which synonyms were migrated?
```

- **Waarschijnlijkheid**: LOW (One-time migration)
- **Impact**: CRITICAL (Data corruption)
- **Detectie**: Migration checkpoints
- **Preventie**: Transactional migration, backup first
- **Testing**: Rollback procedures

### 6.2 Partial Migration States
**Probleem**: System in inconsistent state tijdens migration.

- **Waarschijnlijkheid**: MEDIUM (Migration window)
- **Impact**: MAJOR (Wrong results)
- **Detectie**: Migration status tracking
- **Preventie**: Feature flags, gradual rollout
- **Testing**: Migration state tests

### 6.3 Feature Flag Toggle Bugs
**Probleem**: Feature flag changes cause unexpected behavior.

**Scenario**:
```python
if FEATURE_FLAGS.use_db_synonyms:
    return db_service.get()
else:
    return yaml_service.get()
# What if flag changes mid-session?
```

- **Waarschijnlijkheid**: LOW (Controlled)
- **Impact**: MAJOR (Inconsistency)
- **Detectie**: Flag change monitoring
- **Preventie**: Session-stable flags
- **Testing**: Flag toggle tests

## Recommended Testing Strategy

### Unit Tests
```python
class TestSynonymEdgeCases:
    def test_concurrent_requests(self):
        """Test race condition handling"""

    def test_empty_api_response(self):
        """Test empty OpenAI response"""

    def test_circular_references(self):
        """Test cycle detection"""

    def test_unicode_handling(self):
        """Test special characters"""
```

### Integration Tests
```python
class TestSynonymIntegration:
    def test_db_yaml_precedence(self):
        """Test migration mode precedence"""

    def test_cache_invalidation(self):
        """Test cache consistency"""

    def test_service_initialization(self):
        """Test startup sequence"""
```

### Load Tests
```python
class TestSynonymLoad:
    def test_concurrent_users(self):
        """Simulate 100 concurrent users"""

    def test_bulk_processing(self):
        """Process 10,000 terms"""

    def test_memory_growth(self):
        """Monitor memory over time"""
```

### Chaos Engineering
```python
class TestSynonymChaos:
    def test_network_failures(self):
        """Inject network failures"""

    def test_partial_responses(self):
        """Simulate partial API responses"""

    def test_database_locks(self):
        """Simulate database contention"""
```

## Monitoring & Alerting

### Key Metrics
1. **API Latency**: p50, p95, p99 for OpenAI calls
2. **Cache Hit Rate**: Should be > 80%
3. **Database Query Time**: Alert if > 100ms
4. **Memory Usage**: Alert if > 80% of limit
5. **Error Rate**: Alert if > 1% of requests

### Log Patterns
```python
# Success pattern
logger.info(f"Synonym generated: term={term}, count={len(synonyms)}, source={source}")

# Error pattern
logger.error(f"Synonym generation failed: term={term}, error={e}, retry={retry_count}")

# Performance pattern
logger.debug(f"Cache lookup: term={term}, hit={cache_hit}, time_ms={elapsed}")
```

## Mitigation Priority Matrix

| Issue | Likelihood | Impact | Priority | Mitigation Effort |
|-------|------------|--------|----------|------------------|
| Concurrent requests | HIGH | MAJOR | P0 | Medium |
| Unbounded cache | HIGH | MAJOR | P0 | Low |
| N+1 queries | HIGH | MAJOR | P0 | Medium |
| YAML/DB sync | HIGH | CRITICAL | P0 | High |
| Empty API response | LOW | MAJOR | P1 | Low |
| Circular references | LOW | MAJOR | P1 | Medium |
| Unicode issues | MEDIUM | MINOR | P2 | Low |
| Case sensitivity | HIGH | MINOR | P2 | Low |

## Conclusion

Het synonym management systeem heeft verschillende kritieke edge cases die moeten worden aangepakt:

1. **Immediate actie vereist (P0)**:
   - Request deduplication implementeren
   - Cache bounds instellen
   - Bulk query optimalisatie
   - Migration strategy bepalen

2. **Belangrijke mitigaties (P1)**:
   - API response validation
   - Cycle detection
   - Graceful degradation

3. **Nice-to-have (P2)**:
   - Unicode normalization
   - Case handling

De meeste issues zijn op te lossen met bekende patterns (caching, locking, validation). De grootste risico's liggen in de migration periode en concurrent access patterns.

## Aanbevelingen

1. **Start met een feature flag**: Gradual rollout met mogelijkheid tot rollback
2. **Implementeer request deduplication eerst**: Voorkomt meeste race conditions
3. **Gebruik TTL cache met size limit**: Lost memory issues op
4. **Bouw comprehensive logging**: Voor production debugging
5. **Test met production-like load**: Voorkom surprises

Deze analyse biedt een solide basis voor het implementeren van een robuust synonym management systeem.