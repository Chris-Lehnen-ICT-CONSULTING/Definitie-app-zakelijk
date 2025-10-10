# Synonym Orchestrator Architecture v3.1
## Unified Synonym Management met Graph-Based Registry

**Status:** Final Design - Ready for Implementation
**Version:** 3.1
**Date:** 2025-10-09
**Authors:** Multi-Agent Consensus Review (PO, Architect, Developer, QA, Security)

---

## 📋 Executive Summary

### Problem Statement

De huidige synoniemen infrastructuur is gefragmenteerd over drie ongecoördineerde bronnen:
1. **`juridische_synoniemen.yaml`** - Statisch bestand voor weblookup
2. **`synonym_suggestions` DB tabel** - GPT-4 suggesties pending review
3. **`definitie_voorbeelden` DB tabel** - Handmatige synoniemen per definitie

Dit leidt tot:
- Geen single source of truth
- Sync problemen tussen bronnen
- Suboptimale weblookup (mist AI-suggesties)
- Complexe maintenance (YAML + DB dual-write)

### Solution

**Unified Graph-Based Registry** met orchestrator-laag:

```
┌─────────────────────────────────────────────────┐
│           SynonymOrchestrator                   │
│  (TTL Cache + Governance Policy + GPT-4 Sync)  │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│         SynonymRegistry (Graph-Based)           │
│                                                  │
│  synonym_groups          synonym_group_members  │
│  ├─ id                   ├─ group_id (FK)      │
│  ├─ canonical_term       ├─ term               │
│  └─ domain               ├─ weight (0.0-1.0)   │
│                          ├─ status (lifecycle)  │
│                          ├─ source (origin)     │
│                          └─ definitie_id (scope)│
└─────────────────────────────────────────────────┘
```

**Key Benefits:**
- ✅ Single source of truth (registry)
- ✅ Symmetrische synoniemen (geen hoofdterm hiërarchie)
- ✅ Sync GPT-4 aanvulling vóór definitiegeneratie (betere weblookup)
- ✅ TTL cache met invalidatie (performance)
- ✅ Configurable governance (strict/pragmatic policy)
- ✅ Geen backwards compatibility nodig (YAML recent toegevoegd)

---

## 🎭 Multi-Agent Consensus Review

### Drie Nieuwe Inzichten (Game Changers)

1. **Geen YAML Backwards Compatibility**
   - YAML file is pas enkele uren oud
   - Volledige verwijdering mogelijk → -500 regels code
   - `JuridischeSynoniemService` wordt pure registry façade

2. **Graph-Based Synoniemen Model**
   - Symmetrische groepen (peers, geen hiërarchie)
   - Bidirectionele lookup via JOIN (elegant)
   - Toekomstbestendig (metadata op groep-niveau)

3. **Sync GPT-4 Aanvulling VÓÓR Definitiegeneratie**
   - Check registry: <5 synoniemen? → GPT-4 call (sync OK!)
   - Weblookup krijgt complete synoniemenset direct
   - Eenvoudiger dan async background jobs

### Agent Consensus

| Agent | Verdict | Rationale |
|-------|---------|-----------|
| **PO (Sarah)** | ✅ Approved | UX win: één klik = definitie + synoniemen + weblookup |
| **Architect (Eva)** | ✅ Approved | Clean design, geen async complexity, graph model zuiver |
| **Developer (James)** | ✅ Approved | Straightforward implementatie, deterministische tests |
| **QA (Quinn)** | ✅ Approved | Testbaar, geen race conditions, duidelijke flows |
| **Security (Morgan)** | ✅ Approved | Configurable governance, audit trail, RBAC ready |

**Unanimous Consensus Bereikt** 🎉

### Governance Policy Decision

**Vraag:** Gebruikt weblookup `ai_pending` synoniemen direct of na approval?

**Consensus:** Model 1 (Strict) met configuratie override
- Default: `SYNONYM_POLICY = "strict"` (alleen approved)
- Admin kan switchen naar `"pragmatic"` (ai_pending ook toegestaan)
- Rationale: Governance > UX voor compliance, maar flexibiliteit behouden

---

## 🗄️ Schema Design (Graph-Based)

### Database Tables

```sql
-- Synonym Groups (expliciete groepering van gerelateerde termen)
CREATE TABLE synonym_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_term TEXT NOT NULL UNIQUE,  -- "Voorkeurs" term voor display
    domain TEXT,                           -- "strafrecht", "civielrecht", etc. (optional)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT
);

-- Synonym Group Members (alle synoniemen als peers)
CREATE TABLE synonym_group_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    term TEXT NOT NULL,

    -- Weighting & Priority
    weight REAL DEFAULT 1.0 CHECK(weight >= 0.0 AND weight <= 1.0),
    is_preferred BOOLEAN DEFAULT FALSE,  -- Top-5 priority flag

    -- Lifecycle Status
    status TEXT NOT NULL DEFAULT 'active',
        -- active: In gebruik, beschikbaar voor queries
        -- ai_pending: GPT-4 suggestie, wacht op approval
        -- rejected_auto: Afgewezen door reviewer
        -- deprecated: Niet meer gebruikt (manual edit removed)

    -- Source Tracking
    source TEXT NOT NULL,
        -- db_seed: Initiële migratie vanuit oude DB
        -- manual: Handmatig toegevoegd door gebruiker
        -- ai_suggested: GPT-4 suggestie
        -- imported_yaml: Migratie vanuit juridische_synoniemen.yaml (legacy)

    -- Context & Rationale
    context_json TEXT,  -- {"rationale": "...", "model": "gpt-4", "temperature": 0.3}

    -- Scoping (global vs per-definitie)
    definitie_id INTEGER,  -- NULL = global, anders scoped to definitie

    -- Analytics
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,

    -- Audit Trail
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    reviewed_by TEXT,
    reviewed_at TIMESTAMP,

    -- Constraints
    FOREIGN KEY(group_id) REFERENCES synonym_groups(id) ON DELETE CASCADE,
    FOREIGN KEY(definitie_id) REFERENCES definities(id) ON DELETE CASCADE,
    UNIQUE(group_id, term)  -- Een term kan maar 1x per groep
);

-- Indexes voor performance
CREATE INDEX idx_sgm_group ON synonym_group_members(group_id);
CREATE INDEX idx_sgm_term ON synonym_group_members(term);
CREATE INDEX idx_sgm_status ON synonym_group_members(status);
CREATE INDEX idx_sgm_preferred ON synonym_group_members(is_preferred);
CREATE INDEX idx_sgm_definitie ON synonym_group_members(definitie_id);
CREATE INDEX idx_sgm_usage ON synonym_group_members(usage_count DESC);
```

### Example Data

```sql
-- Group 1: Voorlopige hechtenis groep
INSERT INTO synonym_groups (id, canonical_term, domain)
VALUES (1, 'voorlopige hechtenis', 'strafrecht');

-- Members (symmetrisch - geen hiërarchie!)
INSERT INTO synonym_group_members (group_id, term, weight, status, source) VALUES
    (1, 'voorlopige hechtenis', 1.0, 'active', 'manual'),        -- Canonical term zelf
    (1, 'voorarrest', 0.95, 'active', 'imported_yaml'),          -- Sterk synoniem
    (1, 'bewaring', 0.90, 'active', 'imported_yaml'),
    (1, 'inverzekeringstelling', 0.88, 'ai_pending', 'ai_suggested'),  -- Wacht op review
    (1, 'detentie', 0.82, 'ai_pending', 'ai_suggested');
```

### Bidirectional Lookup Query

```sql
-- Haal alle synoniemen voor term "voorarrest" (inclusief canonical):
SELECT
    m2.term,
    m2.weight,
    m2.status,
    m2.is_preferred
FROM synonym_group_members m1
JOIN synonym_group_members m2 ON m1.group_id = m2.group_id
WHERE m1.term = 'voorarrest'
  AND m2.term != 'voorarrest'  -- Exclude zelf
  AND m2.status = 'active'
  AND (m2.definitie_id IS NULL OR m2.definitie_id = ?)  -- Global + scoped
ORDER BY m2.is_preferred DESC, m2.weight DESC, m2.usage_count DESC;
```

---

## 🔧 Core Components

### 1. SynonymRegistry (Data Access Layer)

```python
# src/repositories/synonym_registry.py

class SynonymRegistry:
    """
    Data access layer voor synonym groups & members.

    Responsibilities:
    - CRUD operations op synonym_groups & synonym_group_members
    - Bidirectionele lookup (term → groep → alle members)
    - Cache invalidation callbacks
    - Statistics & health checks
    """

    def __init__(self, db_path: str = "data/definities.db"):
        self.db_path = db_path
        self._invalidation_callbacks: list[callable] = []

    # === GROUP OPERATIONS ===

    def get_or_create_group(
        self,
        canonical_term: str,
        domain: str | None = None,
        created_by: str = "system"
    ) -> SynonymGroup:
        """Find existing group or create new one."""
        pass

    def find_group_by_term(self, term: str) -> SynonymGroup | None:
        """Find group containing this term (any member)."""
        pass

    # === MEMBER OPERATIONS ===

    def add_group_member(
        self,
        group_id: int,
        term: str,
        weight: float = 1.0,
        status: str = 'active',
        source: str = 'manual',
        definitie_id: int | None = None,
        context_json: str | None = None,
        created_by: str = "system"
    ) -> int:
        """Add member to group + trigger invalidation."""
        member_id = self._add_group_member_db(...)

        # Trigger cache invalidation
        group = self.get_group(group_id)
        if group:
            self._trigger_invalidation(group.canonical_term)

        return member_id

    def get_group_members(
        self,
        group_id: int,
        statuses: list[str] | None = None,
        min_weight: float = 0.0,
        filters: dict | None = None,
        order_by: list[str] | None = None,
        limit: int | None = None
    ) -> list[SynonymGroupMember]:
        """Query members with flexible filtering."""
        pass

    def update_member_status(
        self,
        member_id: int,
        new_status: str,
        reviewed_by: str,
        reviewed_at: datetime | None = None
    ):
        """Update status + trigger invalidation."""
        self._update_member_status_db(...)

        # Trigger invalidation
        member = self.get_member(member_id)
        group = self.get_group(member.group_id)
        if group:
            self._trigger_invalidation(group.canonical_term)

    # === CACHE INVALIDATION ===

    def register_invalidation_callback(self, callback: callable):
        """Register callback voor cache updates."""
        self._invalidation_callbacks.append(callback)

    def _trigger_invalidation(self, term: str):
        """Trigger alle callbacks."""
        for callback in self._invalidation_callbacks:
            try:
                callback(term)
            except Exception as e:
                logger.error(f"Invalidation callback failed: {e}")

    # === STATISTICS ===

    def get_statistics(self) -> dict:
        """Registry health metrics."""
        return {
            'total_groups': self._count_groups(),
            'total_members': self._count_members(),
            'avg_members_per_group': self._avg_members(),
            'by_status': self._count_by_status(),
            'by_source': self._count_by_source(),
            'orphaned_members': self._count_orphaned(),
            'unused_synonyms': self._count_unused()
        }
```

### 2. SynonymOrchestrator (Business Logic Layer)

```python
# src/services/synonym_orchestrator.py

class SynonymOrchestrator:
    """
    Business logic voor synonym operations.

    Responsibilities:
    - Get synonyms met governance policy enforcement
    - TTL caching met invalidatie
    - GPT-4 enrichment (sync tijdens definitiegeneratie)
    - Usage tracking
    """

    def __init__(
        self,
        registry: SynonymRegistry,
        gpt4_suggester: GPT4SynonymSuggester
    ):
        self.registry = registry
        self.gpt4_suggester = gpt4_suggester
        self.config = get_synonym_config()  # Centraal!

        # TTL Cache: {term: (synonyms, timestamp)}
        self._cache: dict[str, tuple[list, datetime]] = {}
        self._cache_lock = threading.RLock()
        self._cache_hits = 0
        self._cache_misses = 0

    def get_synonyms_for_lookup(
        self,
        term: str,
        max_results: int = 5,
        min_weight: float | None = None
    ) -> list[WeightedSynonym]:
        """
        Get synonyms met TTL cache + governance.

        Priority:
        1. Preferred members (is_preferred=TRUE)
        2. Active members (status='active', weight >= threshold)
        3. AI pending (ONLY if policy='pragmatic')
        """
        term_normalized = term.lower().strip()

        # Check cache
        if self._is_cached(term_normalized):
            self._cache_hits += 1
            return self._get_from_cache(term_normalized)[:max_results]

        # Cache miss - query registry
        self._cache_misses += 1

        # Determine statuses (governance policy!)
        statuses = ['active']
        if self.config.policy == SynonymPolicy.PRAGMATIC:
            statuses.append('ai_pending')

        # Query
        min_weight = min_weight or self.config.min_weight_for_weblookup
        synonyms = self.registry.get_synonyms(
            term=term_normalized,
            statuses=statuses,
            min_weight=min_weight,
            order_by=['is_preferred DESC', 'weight DESC', 'usage_count DESC'],
            limit=max_results * 2  # Cache extra
        )

        # Store in cache
        self._store_in_cache(term_normalized, synonyms)

        return synonyms[:max_results]

    async def ensure_synonyms(
        self,
        term: str,
        min_count: int = 5,
        context: dict | None = None
    ) -> tuple[list[WeightedSynonym], int]:
        """
        Ensure term has min_count synoniemen (GPT-4 sync OK!).

        Called VÓÓRdat definitiegeneratie start.

        Returns:
            (synonyms, ai_pending_count)
        """
        # Check existing
        existing = self.get_synonyms_for_lookup(term, max_results=10)

        if len(existing) >= min_count:
            enrichment_logger.info(f"Cache hit for '{term}' (has {len(existing)} >= {min_count})")
            return existing[:min_count], 0  # ✅ Fast path

        # Slow path: GPT-4 enrichment (sync blocking OK - user clicked "Genereer")
        enrichment_logger.info(
            f"Starting GPT-4 enrichment for '{term}' (only {len(existing)} found)"
        )

        start_time = datetime.now()

        try:
            ai_suggestions = await asyncio.wait_for(
                self.gpt4_suggester.suggest_synonyms(
                    term=term,
                    definitie=context.get('definitie') if context else None,
                    context=context.get('tokens') if context else None
                ),
                timeout=self.config.gpt4_timeout_seconds
            )

            duration = (datetime.now() - start_time).total_seconds()

            # Save as ai_pending (NOT active - requires approval!)
            group = self.registry.get_or_create_group(
                canonical_term=term,
                created_by='gpt4_enrichment'
            )

            ai_count = 0
            for suggestion in ai_suggestions:
                self.registry.add_group_member(
                    group_id=group.id,
                    term=suggestion.synoniem,
                    weight=suggestion.confidence,
                    status='ai_pending',  # Governance gate!
                    source='ai_suggested',
                    context_json=json.dumps({
                        'rationale': suggestion.rationale,
                        'model': 'gpt-4-turbo',
                        'triggered_by': 'definition_generation'
                    }),
                    created_by='gpt4_suggester'
                )
                ai_count += 1

            enrichment_logger.info(
                f"Enrichment complete for '{term}': "
                f"{ai_count} suggestions, duration: {duration:.2f}s"
            )

            # Re-fetch (nu met ai_pending if policy allows)
            enriched = self.get_synonyms_for_lookup(term, max_results=10)

            return enriched[:min_count], ai_count

        except asyncio.TimeoutError:
            duration = (datetime.now() - start_time).total_seconds()
            enrichment_logger.error(
                f"GPT-4 timeout for '{term}' after {duration:.2f}s"
            )
            return existing, 0  # Fail gracefully

        except Exception as e:
            enrichment_logger.error(f"GPT-4 enrichment failed for '{term}': {e}")
            return existing, 0

    def invalidate_cache(self, term: str | None = None):
        """Invalidate cache (called by registry callbacks)."""
        with self._cache_lock:
            if term:
                term_normalized = term.lower().strip()
                if term_normalized in self._cache:
                    del self._cache[term_normalized]
                    logger.info(f"Cache invalidated for '{term}'")
            else:
                self._cache.clear()
                logger.info("Cache flushed (all entries)")

    @property
    def cache_hit_rate(self) -> float:
        """Cache performance metric."""
        total = self._cache_hits + self._cache_misses
        return self._cache_hits / total if total > 0 else 0.0
```

### 3. JuridischeSynoniemService (Façade)

```python
# src/services/web_lookup/synonym_service.py (REFACTORED)

class JuridischeSynoniemService:
    """
    Backward compatible façade over SynonymOrchestrator.

    Existing callers blijven werken zonder wijzigingen!
    """

    def __init__(self, orchestrator: SynonymOrchestrator):
        self.orchestrator = orchestrator

    # === BACKWARD COMPATIBLE API ===

    def get_synoniemen(self, term: str) -> list[str]:
        """Haal synoniemen (legacy API)."""
        weighted = self.orchestrator.get_synonyms_for_lookup(
            term=term,
            max_results=8,  # Historical default
            min_weight=0.7
        )
        return [ws.term for ws in weighted if ws.term != term]

    def get_synonyms_with_weights(self, term: str) -> list[tuple[str, float]]:
        """Weighted synonyms (v2.0 compat)."""
        weighted = self.orchestrator.get_synonyms_for_lookup(term, max_results=8)
        return [(ws.term, ws.weight) for ws in weighted if ws.term != term]

    def expand_query_terms(self, term: str, max_synonyms: int = 3) -> list[str]:
        """Query expansion."""
        weighted = self.orchestrator.get_synonyms_for_lookup(term, max_results=max_synonyms)
        return [term] + [ws.term for ws in weighted]

    def has_synoniemen(self, term: str) -> bool:
        """Check if term has synonyms."""
        return len(self.get_synoniemen(term)) > 0
```

### 4. Central Config Management

```python
# src/config/synonym_config.py

from enum import Enum
from dataclasses import dataclass

class SynonymPolicy(Enum):
    STRICT = "strict"        # Alleen approved synoniemen
    PRAGMATIC = "pragmatic"  # AI-pending ook toegestaan

@dataclass
class SynonymConfiguration:
    # Governance
    policy: SynonymPolicy = SynonymPolicy.STRICT

    # Enrichment
    min_synonyms_threshold: int = 5
    gpt4_timeout_seconds: int = 30
    gpt4_max_retries: int = 3

    # Caching
    cache_ttl_seconds: int = 3600  # 1 hour
    cache_max_size: int = 1000

    # Weights
    min_weight_for_weblookup: float = 0.7
    preferred_weight_threshold: float = 0.95

    @classmethod
    def from_yaml(cls, path: str) -> "SynonymConfiguration":
        """Load from config/synonym_config.yaml."""
        pass

# Singleton access
_config: SynonymConfiguration | None = None

def get_synonym_config() -> SynonymConfiguration:
    global _config
    if _config is None:
        _config = SynonymConfiguration.from_yaml("config/synonym_config.yaml")
    return _config
```

```yaml
# config/synonym_config.yaml

synonym_configuration:
  policy: strict  # strict | pragmatic
  min_synonyms: 5
  gpt4_timeout: 30
  cache_ttl: 3600
  min_weight: 0.7
  preferred_threshold: 0.95
```

---

## 🔄 Integration Flows

### Flow 1: Definitiegeneratie met Synoniemen Enrichment

```python
# src/services/definition_generation_orchestrator.py

class DefinitionGenerationOrchestrator:
    async def generate_definition(self, term: str, context: dict) -> dict:
        """
        Generate definition met synonym enrichment.

        Flow:
        1. Ensure synonyms (GPT-4 if needed) ← NIEUW!
        2. Web lookup (with complete synonym set)
        3. GPT-4 definition generation
        4. Return definition + synonym metadata
        """
        result = {}

        # PHASE 1: Synonym Enrichment (sync GPT-4 OK)
        synonyms, ai_pending_count = await self.synonym_orchestrator.ensure_synonyms(
            term=term,
            min_count=5,
            context=context
        )

        result['synonyms'] = [s.term for s in synonyms]
        result['ai_pending_count'] = ai_pending_count

        # PHASE 2: Web Lookup (with enriched synonyms!)
        web_results = await self.web_lookup_service.lookup(
            LookupRequest(
                term=term,
                synonyms=[s.term for s in synonyms],  # Complete set!
                context=context.get('tokens'),
                max_results=10
            )
        )

        result['web_results'] = web_results

        # PHASE 3: GPT-4 Definition Generation
        definition = await self.definition_generator.generate(
            term=term,
            context=context,
            web_sources=web_results
        )

        result['definition'] = definition
        result['metadata'] = {
            'synonyms_used': len(synonyms),
            'ai_pending_used': ai_pending_count if policy_allows else 0,
            'web_sources_found': len(web_results)
        }

        return result
```

### Flow 2: Manual Edit Definitie-Editor

```python
# src/repositories/definitie_repository.py (UPDATED)

class DefinitieRepository:
    def save_voorbeelden(
        self,
        definitie_id: int,
        voorbeelden_dict: dict,
        gegenereerd_door: str = "system",
        voorkeursterm: str | None = None
    ) -> list[int]:
        """
        Save voorbeelden + sync synoniemen naar registry.

        UPDATED: Triggert registry sync!
        """
        # Save to definitie_voorbeelden (legacy)
        saved_ids = self._save_voorbeelden_legacy(...)

        # Sync synoniemen naar registry (NIEUW!)
        synoniemen = voorbeelden_dict.get('synoniemen', [])
        if synoniemen:
            self._sync_synonyms_to_registry(
                definitie_id=definitie_id,
                synoniemen=synoniemen,
                edited_by=gegenereerd_door
            )

        return saved_ids

    def _sync_synonyms_to_registry(
        self,
        definitie_id: int,
        synoniemen: list[str],
        edited_by: str
    ):
        """
        Sync manual synoniemen naar registry (scoped to definitie_id).

        Logic:
        1. Find/create group voor definitie.begrip
        2. Add/update synoniemen als active (source=manual, definitie_id=X)
        3. Deprecate synoniemen in group met definitie_id=X maar NIET in input
        4. Cache invalidation
        """
        definitie = self.get_definitie(definitie_id)
        registry = ServiceContainer.get_instance().get_synonym_registry()

        group = registry.get_or_create_group(
            canonical_term=definitie.begrip,
            created_by=edited_by
        )

        # Get existing manual members for this definitie
        existing = registry.get_group_members(
            group_id=group.id,
            filters={'definitie_id': definitie_id, 'source': 'manual'}
        )

        existing_terms = {m.term: m for m in existing}
        input_terms = {s.strip().lower() for s in synoniemen if s.strip()}

        # Add/update from input
        for syn in synoniemen:
            syn_normalized = syn.strip().lower()
            if not syn_normalized:
                continue

            if syn_normalized in existing_terms:
                # Reactivate if deprecated
                member = existing_terms[syn_normalized]
                if member.status == 'deprecated':
                    registry.update_member_status(
                        member_id=member.id,
                        new_status='active',
                        reviewed_by=edited_by
                    )
            else:
                # Add new
                registry.add_group_member(
                    group_id=group.id,
                    term=syn_normalized,
                    weight=1.0,  # Manual = high confidence
                    status='active',
                    source='manual',
                    definitie_id=definitie_id,  # SCOPED!
                    created_by=edited_by
                )

        # Deprecate removed (NOT in input)
        for term, member in existing_terms.items():
            if term not in input_terms and member.status == 'active':
                registry.update_member_status(
                    member_id=member.id,
                    new_status='deprecated',
                    reviewed_by=edited_by
                )

        # Cache invalidation (automatic via callback)
        logger.info(f"Synced {len(synoniemen)} manual synonyms for definitie {definitie_id}")
```

### Flow 3: AI-Synoniemen Review (UX)

```
User: Klikt "Genereer Definitie"
    ↓
[SPINNER: "Synoniemen controleren..."]
ensure_synonyms() → <5? GPT-4 call (5-15s)
    ↓
[SPINNER: "Externe bronnen zoeken..."]
Web lookup met synoniemen
    ↓
[SPINNER: "Definitie genereren..."]
GPT-4 definitie
    ↓
[RESULT DISPLAYED]
    ↓
📊 Metadata Block:
┌─────────────────────────────────────────────┐
│ ✅ Definitie gegenereerd                     │
│                                              │
│ 📚 Synoniemen gebruikt: 5                   │
│ ⚠️  3 nieuwe AI-synoniemen gevonden         │
│    [Review Synoniemen] [Later]              │
└─────────────────────────────────────────────┘

User klikt [Review Synoniemen]:
    ↓
Pop-up met pending synoniemen:
┌─────────────────────────────────────────────┐
│ 🤖 AI-Gegenereerde Synoniemen Review        │
│                                              │
│ ✅ inverzekeringstelling (0.88)             │
│    Rationale: Strafvorderlijke maatregel... │
│    [✓ Goedkeuren] [✗ Afwijzen]              │
│                                              │
│ [Alles Goedkeuren] [Later Reviewen]         │
└─────────────────────────────────────────────┘
```

---

## 📦 Migration Strategy

### Three Sources → Unified Registry

```python
# scripts/migrate_synonyms_to_registry.py

class SynonymMigration:
    """Migrate all sources to graph-based registry."""

    def migrate_all(self, dry_run: bool = True) -> dict:
        """
        Migrate:
        1. juridische_synoniemen.yaml (if exists - legacy)
        2. synonym_suggestions (approved only)
        3. definitie_voorbeelden (per-definitie manual)
        """
        stats = {
            'groups_created': 0,
            'members_added': 0,
            'yaml_imported': 0,
            'db_approved': 0,
            'definitie_voorbeelden': 0,
            'conflicts': []
        }

        # 1. YAML (if exists)
        if self.yaml_path.exists():
            yaml_data = self._load_yaml()
            for hoofdterm, synoniemen in yaml_data.items():
                group = self.registry.get_or_create_group(
                    canonical_term=hoofdterm,
                    created_by='yaml_migration'
                )
                stats['groups_created'] += 1

                for syn in synoniemen:
                    if not dry_run:
                        self.registry.add_group_member(
                            group_id=group.id,
                            term=syn['synoniem'] if isinstance(syn, dict) else syn,
                            weight=syn.get('weight', 1.0) if isinstance(syn, dict) else 1.0,
                            status='active',
                            source='imported_yaml',
                            created_by='yaml_migration'
                        )
                    stats['members_added'] += 1
                    stats['yaml_imported'] += 1

        # 2. Approved DB suggestions
        approved = self.synonym_repo.get_suggestions_by_status(
            SuggestionStatus.APPROVED
        )
        for suggestion in approved:
            group = self.registry.get_or_create_group(
                canonical_term=suggestion.hoofdterm,
                created_by='db_migration'
            )

            if not dry_run:
                self.registry.add_group_member(
                    group_id=group.id,
                    term=suggestion.synoniem,
                    weight=suggestion.confidence,
                    status='active',
                    source='ai_suggested',
                    context_json=suggestion.context_data,
                    reviewed_by=suggestion.reviewed_by,
                    created_by='db_migration'
                )
            stats['members_added'] += 1
            stats['db_approved'] += 1

        # 3. Definitie voorbeelden (scoped to definitie)
        all_defs = self.definitie_repo.search_definities(limit=None)
        for definitie in all_defs:
            voorbeelden = self.definitie_repo.get_voorbeelden_by_type(definitie.id)
            synoniemen = voorbeelden.get('synonyms', [])

            if not synoniemen:
                continue

            group = self.registry.get_or_create_group(
                canonical_term=definitie.begrip,
                created_by='definitie_migration'
            )

            for syn in synoniemen:
                if not dry_run:
                    self.registry.add_group_member(
                        group_id=group.id,
                        term=syn,
                        weight=1.0,
                        status='active',
                        source='manual',
                        definitie_id=definitie.id,  # SCOPED!
                        created_by='definitie_migration'
                    )
                stats['members_added'] += 1
                stats['definitie_voorbeelden'] += 1

        return stats

# CLI usage:
# python scripts/migrate_synonyms_to_registry.py --dry-run  # Preview
# python scripts/migrate_synonyms_to_registry.py --execute  # Run
```

---

## 🧪 Testing Strategy

### Unit Tests

```python
# tests/services/test_synonym_orchestrator.py

class TestSynonymOrchestrator:
    def test_get_synonyms_cache_hit(self, mock_registry):
        """Verify cache hit doesn't query registry."""
        orchestrator = SynonymOrchestrator(mock_registry, Mock())

        # Prime cache
        orchestrator.get_synonyms_for_lookup("test", max_results=5)

        # Second call = cache hit
        result = orchestrator.get_synonyms_for_lookup("test", max_results=5)

        # Registry called only once
        assert mock_registry.get_synonyms.call_count == 1
        assert orchestrator.cache_hit_rate == 0.5  # 1 hit, 1 miss

    @pytest.mark.asyncio
    async def test_ensure_synonyms_enrichment(self, mock_registry, mock_gpt4):
        """Verify GPT-4 enrichment when <5 synonyms."""
        mock_registry.get_synonyms.return_value = [Mock(term="syn1")]  # Only 1
        mock_gpt4.suggest_synonyms.return_value = [
            Mock(synoniem="syn2", confidence=0.9),
            Mock(synoniem="syn3", confidence=0.85)
        ]

        orchestrator = SynonymOrchestrator(mock_registry, mock_gpt4)

        result, ai_count = await orchestrator.ensure_synonyms("test", min_count=5)

        # GPT-4 called (enrichment triggered)
        mock_gpt4.suggest_synonyms.assert_called_once()
        assert ai_count == 2

    def test_governance_policy_strict(self, mock_registry):
        """Verify strict policy excludes ai_pending."""
        mock_config = Mock(policy=SynonymPolicy.STRICT, min_weight=0.7)

        orchestrator = SynonymOrchestrator(mock_registry, Mock())
        orchestrator.config = mock_config

        orchestrator.get_synonyms_for_lookup("test")

        # Verify statuses parameter
        call_args = mock_registry.get_synonyms.call_args
        assert 'ai_pending' not in call_args.kwargs['statuses']
```

### Integration Tests

```python
# tests/integration/test_synonym_flow_e2e.py

class TestSynonymFlowE2E:
    @pytest.mark.asyncio
    async def test_definition_generation_with_enrichment(self, db, gpt4_service):
        """E2E: Definitiegeneratie → enrichment → weblookup → result."""
        # Setup: Empty registry
        registry = SynonymRegistry(db_path=db)
        orchestrator = SynonymOrchestrator(registry, gpt4_service)

        # Generate definition
        gen_orchestrator = DefinitionGenerationOrchestrator(
            synonym_orchestrator=orchestrator,
            web_lookup_service=...,
            definition_generator=...
        )

        result = await gen_orchestrator.generate_definition(
            term="voorlopige hechtenis",
            context={"domain": "strafrecht"}
        )

        # Verify flow
        assert result['definition'] is not None
        assert len(result['synonyms']) >= 5  # Enrichment worked
        assert result['ai_pending_count'] > 0  # GPT-4 added suggestions
        assert len(result['web_results']) > 0  # Weblookup used synonyms

    def test_manual_edit_sync_to_registry(self, db):
        """Verify manual edit in definitie-editor syncs to registry."""
        repo = DefinitieRepository(db_path=db)
        registry = SynonymRegistry(db_path=db)

        # Create definitie
        definitie_id = repo.create_definitie(
            DefinitieRecord(begrip="test", definitie="...")
        )

        # Manual edit: add synoniemen
        repo.save_voorbeelden(
            definitie_id=definitie_id,
            voorbeelden_dict={
                'synoniemen': ['syn1', 'syn2', 'syn3']
            },
            gegenereerd_door='user'
        )

        # Verify in registry
        group = registry.find_group_by_term("test")
        assert group is not None

        members = registry.get_group_members(
            group_id=group.id,
            filters={'definitie_id': definitie_id}
        )
        assert len(members) == 3
        assert all(m.source == 'manual' for m in members)
```

### Performance Tests

```python
# tests/performance/test_synonym_cache.py

def test_cache_performance_under_load(benchmark):
    """Verify cache hit rate under concurrent load."""
    orchestrator = SynonymOrchestrator(...)

    def query_synonyms():
        terms = ["term1", "term2", "term3"] * 100
        for term in terms:
            orchestrator.get_synonyms_for_lookup(term)

    benchmark(query_synonyms)

    # Target: >80% hit rate
    assert orchestrator.cache_hit_rate > 0.80
```

---

## 📊 Monitoring & KPIs

### Key Performance Indicators

| **KPI** | **Target** | **Alert Threshold** | **Query** |
|---------|-----------|---------------------|-----------|
| Cache Hit Rate | > 80% | < 60% | `orchestrator.cache_hit_rate` |
| GPT-4 Success Rate | > 95% | < 90% | Parse `logs/synonym_enrichment.log` |
| Avg Enrichment Time | < 10s | > 20s | Log analysis |
| Pending Review Count | < 100 | > 500 (backlog) | `SELECT COUNT(*) FROM synonym_group_members WHERE status='ai_pending'` |
| Approval Rate | > 70% | < 50% | `SELECT status, COUNT(*) FROM ... GROUP BY status` |
| Orphaned Members | 0 | > 0 (integrity issue) | `SELECT COUNT(*) FROM ... LEFT JOIN ... WHERE g.id IS NULL` |

### Logging

```python
# Dedicated logger voor enrichment
enrichment_logger = logging.getLogger('synonym_enrichment')
handler = logging.FileHandler('logs/synonym_enrichment.log')
enrichment_logger.addHandler(handler)

# Log format:
# 2025-10-09 14:32:15 - INFO - Starting GPT-4 enrichment for 'voorlopige hechtenis'
# 2025-10-09 14:32:23 - INFO - Enrichment complete: 3 suggestions, duration: 8.2s
# 2025-10-09 14:32:45 - ERROR - GPT-4 timeout for 'term' after 30.1s
```

### Metrics Dashboard (Streamlit)

```python
# src/ui/pages/synonym_metrics.py

def render_synonym_metrics_dashboard():
    st.title("📊 Synonym System Metrics")

    # Cache Performance
    cache_stats = orchestrator.get_cache_stats()
    st.metric("Cache Hit Rate", f"{cache_stats['hit_rate']:.1%}")

    # GPT-4 Enrichment
    enrichment_stats = parse_enrichment_logs(hours=24)
    st.metric("Success Rate", f"{enrichment_stats['success_rate']:.1%}")

    # Approval Workflow
    approval_stats = registry.get_approval_statistics()
    st.metric("Pending Review", approval_stats['pending_count'])

    # Top Used Synonyms
    top_synonyms = registry.get_top_used_synonyms(limit=10)
    st.dataframe(top_synonyms)
```

---

## 🚀 Implementation Roadmap

### PHASE 1: Foundation (Week 1-2)
- [ ] **Schema**: Create synonym_groups + synonym_group_members tables
- [ ] **Registry**: Implement SynonymRegistry CRUD + callbacks
- [ ] **Config**: Build SynonymConfiguration + YAML loader
- [ ] **Migration**: Script met dry-run mode (3 bronnen)
- [ ] **Tests**: Unit tests registry + config

**Deliverable:** Working registry with migration script (dry-run validated)

### PHASE 2: Orchestrator & Cache (Week 3)
- [ ] **Orchestrator**: Build met TTL cache + invalidation
- [ ] **Façade**: Refactor JuridischeSynoniemService → wrapper
- [ ] **Integration**: Wire callbacks in ServiceContainer
- [ ] **Tests**: Integration tests (cache, invalidation)

**Deliverable:** Orchestrator working with cache (>80% hit rate in tests)

### PHASE 3: Definition Generation Flow (Week 4)
- [ ] **Pre-enrichment**: Integrate ensure_synonyms() in generator
- [ ] **UX**: Implement pending review UI (popup/expander)
- [ ] **Manual Edit**: Sync definitie-editor → registry
- [ ] **Tests**: E2E tests (generation → enrichment → review)

**Deliverable:** Complete flow: generatie → enrichment → weblookup → review

### PHASE 4: Monitoring & Cleanup (Week 5)
- [ ] **Logging**: Setup enrichment_logger + file handler
- [ ] **Metrics**: Build Streamlit dashboard
- [ ] **Cleanup**: Remove YAML + YAMLConfigUpdater
- [ ] **Tests**: Full regression suite

**Deliverable:** Production-ready system met monitoring

### PHASE 5: Migration & Cutover (Week 6)
- [ ] **Dry-run**: Execute migration (review output)
- [ ] **Execute**: Run production migration
- [ ] **Validation**: Verify 3 sources migrated correctly
- [ ] **Monitor**: 48h monitoring (cache, errors, approvals)

**Deliverable:** System in production, old sources retired

---

## 📈 Success Metrics

| **Metric** | **Before** | **Target After** |
|-----------|-----------|------------------|
| Data Sources | 3 (fragmented) | 1 (unified) |
| Code Complexity | High (YAML sync, async) | Medium (sync flow, TTL cache) |
| Cache Hit Rate | N/A | > 80% |
| Avg Definition Gen Time | ~20s | ~15s (with cache) |
| Test Coverage | Partial | 100% (deterministic) |
| Manual Review Backlog | N/A | < 100 pending |
| User Flow Steps | 2 (separate review) | 1 (integrated) |

---

## 🔐 Security & Governance

### Role-Based Access Control (Future)

```python
# Future: RBAC voor registry mutations
class SynonymRegistry:
    def approve_suggestion(self, member_id: int, approved_by: str):
        # Check role
        if not has_permission(approved_by, 'approve_synonyms'):
            raise PermissionError("User lacks approve_synonyms permission")

        self.update_member_status(member_id, 'active', approved_by)
```

### Audit Trail

Alle mutations worden gelogd:
- `created_by`, `reviewed_by`, `created_at`, `reviewed_at`
- `context_json` bevat rationale + model info
- Status transitions (ai_pending → active/rejected)
- Usage tracking (`usage_count`, `last_used_at`)

---

## 📚 References

### Code Locations

- **Registry**: `src/repositories/synonym_registry.py`
- **Orchestrator**: `src/services/synonym_orchestrator.py`
- **Façade**: `src/services/web_lookup/synonym_service.py`
- **Config**: `src/config/synonym_config.py`
- **Migration**: `scripts/migrate_synonyms_to_registry.py`
- **Tests**: `tests/services/test_synonym_*`

### Related Documents

- `CLAUDE.md` - Project guidelines
- `docs/architectuur/SOLUTION_ARCHITECTURE.md` - Overall architecture
- `docs/backlog/EPIC-XXX/` - Related epics/stories

### External Dependencies

- GPT-4 Turbo (via `GPT4SynonymSuggester`)
- SQLite (graph-based schema)
- Streamlit (metrics dashboard)

---

## ✅ Approval

**Status:** ✅ **APPROVED** - Unanimous Consensus

All agents (PO, Architect, Developer, QA, Security) approve this design for implementation.

**Next Steps:** Start PHASE 1 (Foundation)

---

*Generated: 2025-10-09*
*Version: 3.1 (Final)*
*Review Status: Multi-Agent Consensus Approved*
