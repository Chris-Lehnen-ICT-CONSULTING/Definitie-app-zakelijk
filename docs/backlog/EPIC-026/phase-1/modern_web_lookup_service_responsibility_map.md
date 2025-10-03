---
id: EPIC-026-RESPONSIBILITY-MAP-MODERN-WEB-LOOKUP
epic: EPIC-026
phase: 1
day: 3
analyzed_file: src/services/modern_web_lookup_service.py
created: 2025-10-02
owner: code-architect
status: complete
---

# Responsibility Map: modern_web_lookup_service.py

**Analysis Date:** 2025-10-02
**File Path:** `src/services/modern_web_lookup_service.py`
**File Size:** 1,019 LOC
**Methods Count:** 19 methods (8 async)
**Complexity:** **HIGH** (Async orchestration with multiple providers)

---

## Executive Summary

### Key Findings

- **Well-Structured Async Service:** Clean separation between providers
- **5 Service Boundaries** geïdentificeerd (Configuration, Orchestration, Providers, Utilities, Contract)
- **Good Test Coverage:** Unit, integration, end-to-end, smoke tests
- **6 Importers:** Moderate coupling
- **Strangler Fig Pattern:** Geleidelijke vervanging van legacy code
- **Provider Diversity:** Wikipedia, Wiktionary, SRU Overheid, Rechtspraak, Wetgeving

### Refactoring Complexity: **MEDIUM** (6/10)

**Factors supporting migration:**
- Clear async/await patterns
- Provider abstraction via SourceConfig
- Interface-based design (WebLookupServiceInterface)
- Good test coverage
- Strangler Fig migration pattern already in use

**Factors increasing complexity:**
- 8 async methods with concurrent execution
- Multiple provider implementations (MediaWiki, SRU, REST, Scraping)
- Legacy fallback logic
- Complex ranking & deduplication
- Context token classification heuristics

---

## File Statistics

### Code Metrics
| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| **Total LOC** | 1,019 | <500 | ❌ Over (2x) |
| **Methods** | 19 | <20 | ✅ Just under |
| **Async Methods** | 8 | N/A | ℹ️ High async usage |
| **Classes** | 2 | N/A | ✅ Good (SourceConfig + Service) |
| **Importers** | 6 | N/A | ⚠️ Moderate coupling |
| **Test Files** | 10+ | N/A | ✅ Excellent coverage |

### Dependency Analysis

**Direct Imports (10+):**
```python
# External
import asyncio
import logging
from dataclasses import dataclass
from typing import Any
from hashlib import sha256

# Internal Services
from .interfaces import (
    JuridicalReference,
    LookupRequest,
    LookupResult,
    WebLookupServiceInterface,
    WebSource,
)

# Domain (optional with fallback)
from domain.autoriteit.betrouwbaarheid import BetrouwbaarheidsCalculator, BronType

# Service Internal
from .web_lookup.config_loader import load_web_lookup_config
from .web_lookup.ranking import rank_and_dedup, _canonical_url
```

**Importers (6 files):**
```
(Need to check actual importers via grep)
```

**Test Coverage (Excellent):**
```
tests/unit/test_modern_web_lookup_service_error_handling.py
tests/integration/test_modern_web_lookup_end_to_end.py
tests/ui/test_web_lookup_timeout_smoke.py
tests/ui/test_web_lookup_health_smoke.py
tests/ui/test_web_lookup_wetgeving_parked_smoke.py
tests/unit/web_lookup/ (directory)
+ more...
```

---

## Method Inventory (19 Methods)

### 1. Initialization & Configuration (2 methods)
```python
__init__()                                                         # L64   - Initialize service with sources
_setup_sources() -> None                                           # L81   - Configure 6 lookup sources
```

### 2. Main Orchestration (1 async method)
```python
async lookup(request: LookupRequest) -> list[LookupResult]        # L241  - Main lookup orchestrator
```

### 3. Provider Routing (1 async method)
```python
async _lookup_source(term, source_name, request)                  # L377  - Route to appropriate provider
```

### 4. Provider Implementations (5 async methods)
```python
async _lookup_mediawiki(term, config, request)                    # L419  - MediaWiki API (Wikipedia, Wiktionary)
async _lookup_sru(term, config, request)                          # L597  - SRU protocol (Overheid, Wetgeving)
async _lookup_scraping(term, config, request)                     # L706  - Web scraping fallback
async _lookup_rest(term, config, request)                         # L715  - REST API (Rechtspraak)
async _legacy_fallback(term, source_name, request)                # L753  - Legacy implementation fallback
```

### 5. Source Determination (1 method)
```python
_determine_sources(request: LookupRequest) -> list[str]           # L338  - Determine which sources to query
```

### 6. Context Parsing (1 method)
```python
_classify_context_tokens(context) -> tuple[list, list, list]      # L177  - Parse org/jur/wet context tokens
```

### 7. Contract Conversion (2 methods)
```python
_convert_legacy_result(legacy_result) -> LookupResult             # L776  - Convert legacy to modern format
_to_contract_dict(result: LookupResult) -> dict[str, Any]         # L843  - Convert to contract dict for ranking
```

### 8. Source Management (2 methods)
```python
get_available_sources() -> list[WebSource]                        # L801  - List available sources
validate_source(text: str) -> WebSource                           # L815  - Validate source configuration
```

### 9. Provider Detection (2 methods)
```python
_infer_provider_key(result: LookupResult) -> str                  # L924  - Infer provider from result
_determine_source_type(text: str) -> BronType                     # L938  - Determine BronType (wet/jur/etc)
```

### 10. Utility Methods (3 methods)
```python
find_juridical_references(text: str) -> list[JuridicalReference]  # L950  - Extract juridical references
detect_duplicates(results, threshold) -> list[tuple]              # L969  - Detect duplicate results
_calculate_similarity(text1, text2) -> float                      # L990  - Calculate text similarity
```

### 11. Configuration (2 methods)
```python
enable_legacy_fallback(enabled: bool = True) -> None              # L1004 - Toggle legacy fallback
get_source_status() -> dict[str, dict[str, Any]]                  # L1009 - Get source status info
async lookup_single_source(term, source) -> LookupResult | None   # L795  - Lookup single source (public API)
```

---

## Responsibility Boundaries (5 Services)

### 1️⃣ **SOURCE CONFIGURATION Service** (~170 LOC)

**Purpose:** Manage source configuration and initialization

**Methods (2):**
- `__init__()` - Initialize service, load config
- `_setup_sources()` - Configure 6 sources (Wikipedia, Wiktionary, Wetgeving, Overheid, Rechtspraak, Overheid Zoek)

**Configuration Sources (6):**
```python
"wikipedia": SourceConfig(
    base_url="https://nl.wikipedia.org/api/rest_v1",
    api_type="mediawiki",
    confidence_weight=0.8,
    is_juridical=False
)

"wiktionary": SourceConfig(
    base_url="https://nl.wiktionary.org/w/api.php",
    api_type="mediawiki",
    confidence_weight=0.9
)

"wetgeving": SourceConfig(
    base_url="https://wetten.overheid.nl/SRU/Search",
    api_type="sru",
    confidence_weight=0.9,
    is_juridical=True
)

"overheid": SourceConfig(
    base_url="https://repository.overheid.nl",
    api_type="sru",
    confidence_weight=1.0,
    is_juridical=True
)

"rechtspraak": SourceConfig(
    base_url="https://data.rechtspraak.nl",
    api_type="rest",
    confidence_weight=0.95,
    is_juridical=True
)

"overheid_zoek": SourceConfig(
    base_url="https://zoekservice.overheid.nl",
    api_type="sru",
    confidence_weight=0.9,
    is_juridical=True
)
```

**Dependencies:**
- `web_lookup.config_loader` - Load YAML config
- `domain.autoriteit.betrouwbaarheid` - Optional domain module

**Business Logic:**
- Config loading with fallback to defaults
- Provider weight configuration (0.8-1.0 range)
- Enabled/disabled toggling per source
- Domain module availability check (DOMAIN_AVAILABLE flag)

**Complexity:** LOW-MEDIUM
- Straightforward configuration
- Good fallback handling
- Optional domain integration

---

### 2️⃣ **LOOKUP ORCHESTRATION Service** (~350 LOC)

**Purpose:** Orchestrate concurrent lookups across multiple providers

**Methods (4 async):**
- `async lookup(request)` - Main orchestrator
- `async _lookup_source(term, source_name, request)` - Route to provider
- `_determine_sources(request)` - Determine which sources to query
- `async lookup_single_source(term, source)` - Single source lookup (public API)

**Orchestration Flow:**
1. Determine sources based on request (juridical filter, specific source, etc.)
2. Create async tasks for each enabled source
3. Execute concurrent lookups via `asyncio.gather()`
4. Filter successful results
5. Rank & deduplicate via `rank_and_dedup()`
6. Return final results

**Dependencies:**
- `asyncio` - Concurrent execution
- `web_lookup.ranking` - Ranking & deduplication
- Provider methods (_lookup_mediawiki, _lookup_sru, etc.)

**Business Logic:**
- Source selection based on:
  - `request.sources` (specific sources requested)
  - `request.only_juridical` (filter to juridical sources)
  - All sources if no filter
- Concurrent execution with exception handling
- Ranking by confidence weights
- Deduplication by canonical URL or content hash

**Complexity:** **HIGH**
- Async orchestration complexity
- Multiple execution paths
- Error aggregation from concurrent tasks
- Ranking & deduplication logic

---

### 3️⃣ **PROVIDER IMPLEMENTATIONS Service** (~400 LOC)

**Purpose:** Implement specific provider lookups (MediaWiki, SRU, REST, Scraping)

**Methods (5 async):**
- `async _lookup_mediawiki(term, config, request)` - Wikipedia, Wiktionary
- `async _lookup_sru(term, config, request)` - Overheid, Wetgeving
- `async _lookup_rest(term, config, request)` - Rechtspraak
- `async _lookup_scraping(term, config, request)` - Web scraping
- `async _legacy_fallback(term, source_name, request)` - Legacy wrapper

**Provider Details:**

**MediaWiki (Wikipedia/Wiktionary):**
- REST API v1 for Wikipedia
- MediaWiki API for Wiktionary
- Extract summary/definition
- Parse links, categories

**SRU (Overheid/Wetgeving):**
- SRU protocol queries
- XML parsing
- Extract metadata, content
- Juridical reference extraction

**REST (Rechtspraak):**
- ECLI-based queries
- JSON responses
- Court decision metadata

**Scraping (Fallback):**
- HTML scraping when API unavailable
- BeautifulSoup/lxml parsing
- Heuristic content extraction

**Legacy Fallback:**
- Wrapper for old implementation
- Conversion to modern format via `_convert_legacy_result()`
- Only enabled when `_legacy_fallback_enabled = True`

**Dependencies:**
- External APIs (Wikipedia, Overheid, etc.)
- `web_lookup.providers.*` - Provider-specific logic (imported dynamically)
- `_convert_legacy_result()` - Legacy conversion

**Complexity:** **VERY HIGH**
- 5 different API/protocol implementations
- XML/JSON/HTML parsing
- Error handling per provider
- Legacy compatibility layer
- Dynamic imports

---

### 4️⃣ **CONTEXT & CLASSIFICATION Service** (~150 LOC)

**Purpose:** Parse and classify context tokens, determine source types

**Methods (3):**
- `_classify_context_tokens(context)` - Parse org/jur/wet context
- `_determine_source_type(text)` - Determine BronType
- `find_juridical_references(text)` - Extract juridical refs

**Context Token Classification:**
Classifies tokens into 3 categories:
- **Organisatorisch:** OM, ZM, DJI, JUSTID, KMAR, CJIB, Reclassering
- **Juridisch:** recht, civiel, bestuursrecht, strafrecht
- **Wettelijk:** wet, wetboek, AWB, Sv, Sr, Rv

**Normalization & Deduplication:**
- Synonym mapping (e.g., "Sv" → "Wetboek van Strafvordering")
- Deduplication while preserving order
- Case-insensitive matching

**Source Type Determination:**
Maps text to `BronType`:
- WETGEVING
- JURISPRUDENTIE
- BELEID
- LITERATUUR

**Dependencies:**
- `domain.autoriteit.betrouwbaarheid.BronType` (optional)
- Hardcoded org/jur/wet keyword lists

**Business Logic:**
- Heuristic-based classification
- Domain-specific abbreviations (OM, AWB, Sv, etc.)
- Fallback to "organisatorisch" for unknown tokens

**Complexity:** MEDIUM
- Hardcoded heuristics (NOT data-driven)
- Synonym mapping logic
- Deduplication algorithm

**⚠️ ISSUE:** Hardcoded keyword lists - should be configurable

---

### 5️⃣ **CONTRACT & UTILITY Service** (~200 LOC)

**Purpose:** Contract conversion, similarity detection, source management

**Methods (8):**
- `_convert_legacy_result(legacy)` - Convert legacy to modern
- `_to_contract_dict(result)` - Convert to contract dict
- `_infer_provider_key(result)` - Infer provider from result
- `get_available_sources()` - List sources
- `validate_source(text)` - Validate source
- `detect_duplicates(results, threshold)` - Detect duplicates
- `_calculate_similarity(text1, text2)` - Calculate similarity
- `enable_legacy_fallback(enabled)` - Toggle legacy
- `get_source_status()` - Get source status

**Contract Conversion:**
- Legacy format → Modern `LookupResult`
- Modern `LookupResult` → Contract dict (for ranking)
- Snippet sanitization (max 500 chars)
- URL canonicalization

**Similarity Detection:**
- Text similarity calculation (simple ratio-based)
- Duplicate detection with threshold (default 0.8)
- Used for deduplication

**Source Management:**
- List available sources with metadata
- Validate source configuration
- Get source status (enabled/disabled, weights)

**Dependencies:**
- `web_lookup.ranking._canonical_url` - URL normalization
- `hashlib.sha256` - Content hashing for dedup

**Complexity:** MEDIUM
- Multiple conversion formats
- Sanitization logic
- Similarity algorithm (simple but effective)

---

## Cross-Cutting Concerns

### 1. Async/Await Patterns
**Usage:** 8 async methods
- Main orchestration (lookup)
- Provider implementations (5 methods)
- Single source lookup
- Legacy fallback

**Pattern:** `asyncio.gather()` for concurrent execution

**Risk:** Proper error handling needed for concurrent tasks

### 2. Error Handling
**Patterns:**
- Try/except in async tasks
- Return exceptions via `asyncio.gather(return_exceptions=True)`
- Filter exceptions from results
- Log warnings for failed lookups

**Risk:** Some errors silently ignored

### 3. Legacy Compatibility
**Strangler Fig Pattern:**
- Modern implementations alongside legacy
- `_legacy_fallback()` wrapper
- Conversion via `_convert_legacy_result()`
- Toggle via `enable_legacy_fallback()`

**Status:** Legacy disabled by default (`_legacy_fallback_enabled = False`)

### 4. Configuration Management
**Sources:**
- YAML config via `config_loader`
- Fallback to hardcoded defaults
- Provider weights configurable
- Enabled/disabled per source

**Risk:** Config errors fall back to defaults (might hide issues)

### 5. Provider Weights
**Configured weights:**
- Wikipedia: 0.8
- Wiktionary: 0.9
- Wetgeving: 0.9
- Overheid: 1.0
- Rechtspraak: 0.95

**Used for:** Ranking results in `rank_and_dedup()`

---

## Service Boundary Design (Proposed)

### 🎯 Target Architecture

```
modern_web_lookup_service.py (ORCHESTRATOR ONLY - ~200 LOC)
├── Source selection logic (~50 LOC)
├── Async orchestration (~100 LOC)
└── Result aggregation (~50 LOC)

NEW Services:
├── SourceConfigurationService (~170 LOC)
│   ├── Load config
│   ├── Setup sources
│   └── Manage weights
│
├── ProviderRegistryService (~150 LOC)
│   ├── Register providers
│   ├── Route to provider
│   └── Manage lifecycle
│
├── MediaWikiProviderService (~120 LOC)
│   ├── Wikipedia lookup
│   ├── Wiktionary lookup
│   └── Extract content
│
├── SRUProviderService (~120 LOC)
│   ├── Overheid lookup
│   ├── Wetgeving lookup
│   └── XML parsing
│
├── RESTProviderService (~100 LOC)
│   ├── Rechtspraak lookup
│   └── JSON parsing
│
├── ScrapingProviderService (~80 LOC)
│   ├── HTML scraping
│   └── Content extraction
│
├── ContextClassificationService (~150 LOC)
│   ├── Token classification
│   ├── Synonym mapping
│   └── Source type detection
│   └── NOTE: Extract keywords to config
│
├── ResultRankingService (ALREADY EXISTS)
│   └── In web_lookup.ranking module
│
└── ContractConversionService (~150 LOC)
    ├── Legacy conversion
    ├── Contract dict conversion
    └── Similarity detection
```

---

## Migration Complexity Assessment

### Complexity Rating: **MEDIUM** (6/10)

**Factors Supporting Migration:**
✅ Already uses interface-based design (`WebLookupServiceInterface`)
✅ Strangler Fig pattern in use (legacy fallback ready to remove)
✅ Excellent test coverage (unit, integration, e2e, smoke)
✅ Clear provider abstraction via `SourceConfig`
✅ Async patterns are consistent
✅ Good separation: config, orchestration, providers, utils

**Factors Increasing Complexity:**
❌ 1,019 LOC in single file (2x threshold)
❌ 8 async methods with concurrent execution
❌ 5 different provider implementations (MediaWiki, SRU, REST, Scraping, Legacy)
❌ Hardcoded context classification (org/jur/wet keywords)
❌ Complex ranking & deduplication logic
❌ Dynamic imports for provider modules
❌ 6 importers (moderate coupling)

### Migration Risk Areas

1. **Async Orchestration**
   - `asyncio.gather()` with multiple providers
   - Risk: Breaking concurrent execution flow

2. **Provider Implementations**
   - 5 different API/protocol implementations
   - Risk: Each provider needs separate service

3. **Legacy Compatibility**
   - Strangler Fig pattern with fallback
   - Risk: Removing legacy too early

4. **Hardcoded Heuristics**
   - Context classification keywords
   - Risk: Moving to config breaks existing logic

5. **Ranking Integration**
   - Tight coupling to `web_lookup.ranking` module
   - Risk: Contract format changes

---

## Recommended Extraction Order

### Phase 1: CONFIGURATION (Week 1)
1. **SourceConfigurationService** (LOW, ~170 LOC)
   - Extract config loading
   - Source setup
   - Provider weights
   - **Benefit:** Centralize configuration

### Phase 2: CONTEXT CLASSIFICATION (Week 1)
2. **ContextClassificationService** (MEDIUM, ~150 LOC)
   - Extract token classification
   - **IMPORTANT:** First move keywords to config
   - Then extract service logic
   - **Benefit:** Data-driven classification

### Phase 3: PROVIDER EXTRACTION (Week 2-3)
3. **MediaWikiProviderService** (MEDIUM, ~120 LOC)
   - Wikipedia + Wiktionary
   - Clear API boundaries

4. **SRUProviderService** (MEDIUM, ~120 LOC)
   - Overheid + Wetgeving
   - XML parsing logic

5. **RESTProviderService** (LOW-MEDIUM, ~100 LOC)
   - Rechtspraak
   - JSON parsing

6. **ScrapingProviderService** (MEDIUM, ~80 LOC)
   - HTML scraping fallback
   - Less critical (can defer)

### Phase 4: CONTRACT & UTILITIES (Week 3)
7. **ContractConversionService** (MEDIUM, ~150 LOC)
   - Legacy conversion
   - Contract dict conversion
   - Similarity detection

### Phase 5: REGISTRY & ORCHESTRATION (Week 4)
8. **ProviderRegistryService** (MEDIUM-HIGH, ~150 LOC)
   - Register all providers
   - Route to appropriate provider
   - Manage provider lifecycle

9. **Reduce Orchestrator** (MEDIUM-HIGH, ~200 LOC)
   - Keep only orchestration logic
   - Delegate everything to services
   - Clean async/await flow

---

## Testing Strategy

### Current Coverage: **EXCELLENT**
- Unit tests: error handling, individual providers
- Integration tests: end-to-end lookup flows
- Smoke tests: timeout, health, wetgeving
- UI tests: tab integration

### Migration Testing Strategy

**Phase 1 (Before Extraction):**
1. Document current behavior
   - All 6 sources working
   - Ranking & deduplication
   - Context classification
   - Legacy fallback (if enabled)

**Phase 2 (During Extraction):**
2. Service-specific tests
   - SourceConfiguration: 90%+ (config loading)
   - ContextClassification: 95%+ (heuristics)
   - Each provider: 90%+ (API integration)
   - ContractConversion: 85%+ (format conversion)

**Phase 3 (After Extraction):**
3. Integration tests
   - Full lookup flow still works
   - All 6 sources return results
   - Ranking produces same output
   - Performance not degraded

**Phase 4 (Regression Prevention):**
4. Add golden tests
   - Known term → expected results
   - Provider weight changes → expected ranking
   - Context tokens → expected classification

---

## Dependencies & Side Effects

### External Dependencies
1. **External APIs (6):**
   - Wikipedia REST API
   - Wiktionary MediaWiki API
   - Wetten.overheid.nl SRU
   - Repository.overheid.nl SRU
   - Data.rechtspraak.nl REST
   - Zoekservice.overheid.nl SRU

2. **Service Layer:**
   - `web_lookup.config_loader` - YAML config
   - `web_lookup.ranking` - Ranking & dedup
   - `web_lookup.providers.*` - Provider modules (dynamic import)

3. **Domain (Optional):**
   - `domain.autoriteit.betrouwbaarheid` - BronType, Calculator
   - Fallback if unavailable (DOMAIN_AVAILABLE flag)

### Side Effects

**Network Calls:**
- 6 concurrent API requests per lookup
- Timeout: 30s per source
- Max retries: 3 per source

**Caching:**
- None implemented (each lookup is fresh)
- **Opportunity:** Add caching layer

**Debug State:**
- `_debug_attempts` list (per-call)
- `_last_debug` dict
- Used for troubleshooting

**Legacy State:**
- `_legacy_fallback_enabled` flag (default False)
- Can be toggled via `enable_legacy_fallback()`

---

## Key Insights & Recommendations

### 🎯 Strengths

1. **Clean Async Design**
   - Consistent async/await patterns
   - Proper use of `asyncio.gather()` for concurrency
   - Error handling via return_exceptions

2. **Provider Abstraction**
   - `SourceConfig` dataclass for configuration
   - Clear routing logic via `_lookup_source()`
   - Extensible: easy to add new providers

3. **Strangler Fig Pattern**
   - Modern implementations alongside legacy
   - Ready to remove legacy when confident
   - Good migration strategy

4. **Excellent Test Coverage**
   - Unit, integration, e2e, smoke tests
   - Covers error cases
   - Performance testing (timeout)

### ⚠️ Areas for Improvement

1. **File Too Large**
   - 1,019 LOC (2x threshold)
   - Should split into provider services

2. **Hardcoded Heuristics**
   - Context classification keywords hardcoded
   - Should be in config/database
   - Not data-driven

3. **No Caching**
   - Every lookup hits external APIs
   - Opportunity for caching layer
   - Could reduce latency & API costs

4. **Dynamic Imports**
   - Provider modules imported on-demand
   - Harder to track dependencies
   - Consider explicit imports

### 📋 Immediate Actions

**Before Refactoring:**
1. ✅ Extract context keywords to config
2. ✅ Document all provider response formats
3. ✅ Add caching layer (optional but recommended)
4. ✅ Create provider interface contract

**During Refactoring:**
1. ✅ Extract providers one-by-one
2. ✅ Keep orchestration working throughout
3. ✅ Test each provider independently
4. ✅ Maintain async patterns

**After Refactoring:**
1. ✅ Remove legacy fallback code
2. ✅ Consolidate provider registration
3. ✅ Optimize concurrent execution
4. ✅ Add performance monitoring

---

## Comparative Analysis

### vs Other Files Analyzed

| Metric | modern_web_lookup | definitie_repository | definition_generator_tab | tabbed_interface |
|--------|-------------------|----------------------|--------------------------|------------------|
| **LOC** | 1,019 | 1,815 | 2,525 | 1,793 |
| **Methods** | 19 | 41 | 60 | 39 |
| **Services** | 5 | 6 | 8 | 7 |
| **Async Methods** | 8 | 0 | 0 | 1 |
| **Complexity** | HIGH | MEDIUM | VERY HIGH | VERY HIGH |
| **Test Coverage** | EXCELLENT | EXCELLENT | POOR | ZERO |

**Observation:** modern_web_lookup_service has:
- ✅ Smaller than UI files (good!)
- ✅ Excellent test coverage (unlike UI files)
- ✅ Clear service boundaries (better than UI)
- ⚠️ High async complexity (unique challenge)
- ⚠️ Still over LOC threshold (but not critically)

**Pattern:** Services layer has BETTER structure than UI layer
- Clearer responsibilities
- Better tested
- More modular design

---

## Migration Checklist

### Pre-Migration
- [ ] Extract context keywords to config YAML
- [ ] Document all provider response formats
- [ ] Map current test coverage (already excellent)
- [ ] Create provider interface contract
- [ ] (Optional) Add caching layer

### Service Extraction (4 weeks)
- [ ] Week 1: SourceConfiguration + ContextClassification
- [ ] Week 2: MediaWiki + SRU providers
- [ ] Week 3: REST + Scraping + ContractConversion
- [ ] Week 4: ProviderRegistry + Orchestrator reduction

### Post-Migration
- [ ] All tests pass (unit, integration, e2e, smoke)
- [ ] Orchestrator reduced to <200 LOC
- [ ] No legacy fallback code
- [ ] Provider registration centralized
- [ ] Performance metrics maintained/improved

### Success Criteria
- ✅ All 6 sources still working
- ✅ Ranking produces same results
- ✅ Performance not degraded
- ✅ Test coverage maintained (>90%)
- ✅ Orchestrator <200 LOC
- ✅ Providers are separate, testable services

---

## Appendix: Provider Details

### Wikipedia Provider
- **API:** REST API v1
- **Endpoint:** `https://nl.wikipedia.org/api/rest_v1/page/summary/{term}`
- **Response:** JSON with summary, extract, links
- **Weight:** 0.8

### Wiktionary Provider
- **API:** MediaWiki API
- **Endpoint:** `https://nl.wiktionary.org/w/api.php`
- **Response:** JSON/XML with definition, etymology
- **Weight:** 0.9

### Wetgeving Provider
- **API:** SRU (Search/Retrieve via URL)
- **Endpoint:** `https://wetten.overheid.nl/SRU/Search`
- **Response:** XML with legal texts
- **Weight:** 0.9
- **Juridical:** Yes

### Overheid Provider
- **API:** SRU
- **Endpoint:** `https://repository.overheid.nl`
- **Response:** XML with government documents
- **Weight:** 1.0 (highest)
- **Juridical:** Yes

### Rechtspraak Provider
- **API:** REST
- **Endpoint:** `https://data.rechtspraak.nl`
- **Response:** JSON with court decisions
- **Weight:** 0.95
- **Juridical:** Yes

### Scraping Provider
- **Type:** HTML scraping (fallback)
- **Use:** When API unavailable
- **Libraries:** BeautifulSoup/lxml
- **Weight:** Configurable

---

**Analysis Complete**
**Next Steps:** Map validation_orchestrator_v2.py

---

**Analyst:** BMad Master (executing Code Architect workflow)
**Date:** 2025-10-02
**Phase:** EPIC-026 Phase 1 (Design)
**Day:** 3 of 5
