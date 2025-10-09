# UNIFIED SOLUTION: "BEST OF 3 WORLDS" SYNONIEMEN OPTIMALISATIE

**Date**: October 9, 2025
**Author**: Claude Code (Synthesis)
**Status**: Architectuur Design
**Version**: 1.0

---

## Executive Summary

### Kern Probleem

**User krijgt niet maximale waarde uit synoniemen systeem** door drie parallelle problemen:

1. **Weblookup Mechanism (World 1)**: Synoniemen worden onderbenut - alleen als fallback gebruikt, niet voor initial query expansion, waardoor relevante content gemist wordt
2. **Context Integration (World 2)**: Token efficiency is goed, maar ROI van weblookup context is niet empirisch gemeten, waardoor we niet weten of synoniemen daadwerkelijk definitiekwaliteit verbeteren
3. **User Experience (World 3)**: Drie disconnected systemen (YAML, Database+Approval, Definition Examples) dwingen user tot handmatig werk dat geautomatiseerd zou kunnen worden

**Impact**: User krijgt slechtere definities dan mogelijk (gemiste context), besteedt tijd aan manueel YAML editen (2 min vs 10 sec mogelijk), en heeft geen visibility in wat synoniemen daadwerkelijk doen.

### Unified Visie

**Na implementatie**:
- **Weblookup**: Synoniemen worden proactief gebruikt (initial expansion) zodat "onherroepelijk" automatisch "kracht van gewijsde" Wikipedia artikelen vindt
- **Quality Tracking**: System meet en toont welke synoniemen effectief zijn (hit rate, usage in definities) zodat low-performers kunnen worden gefilterd
- **User Experience**: Inline synonym approval (1 click) met automatic sync naar YAML, geen manual edits, volledige visibility

**User ziet**: "💡 3 synoniemen gevonden: beklaagde (3 hits), beschuldigde (1 hit), aangeklaagde (0 hits) - Wil je 'aangeklaagde' reviewen?"

### Key Architectural Decisions

1. **Database als Single Source of Truth**: YAML wordt generated artifact (auto-sync on approve), DB bevat alle metadata (usage_count, last_used, confidence, rationale)
2. **Initial Synonym Expansion Enabled**: Synoniemen worden gebruikt VOOR initial query (niet alleen fallback) met adaptive fallback als primary term succesvol is
3. **Quality Metrics Integration**: Usage tracking in weblookup → update DB → analytics dashboard → user feedback loop
4. **Inline Approval UX**: Synonym management gebeurt in Definition Generator (geen context switch), separate page blijft voor bulk operations
5. **Synoniemen NIET expliciet in definitie**: Blijven tool voor query expansion, niet content (conform World 2 analyse)

---

## Cross-Cutting Concerns Analysis

### Synoniemen als Rode Draad

**Synoniemen verbinden alle drie werelden**:

- **World 1 (Weblookup)**: Synoniemen = query expansion tool (input voor Wikipedia/SRU)
- **World 2 (Context)**: Synoniemen = quality amplifier (betere hits → betere definitie)
- **World 3 (UX)**: Synoniemen = user-managed knowledge base (AI suggests, human approves)

**Gemeenschappelijke behoefte**: Synoniemen moeten **gemakkelijk te beheren**, **effectief in gebruik**, en **transparant in werking** zijn.

### Multi-World Problemen

1. **Synoniemen Coverage Gap** (All 3 Worlds)
   - **World 1**: Provider hits missen omdat synoniemen niet gebruikt worden
   - **World 2**: Context is onvolledig door gemiste web content
   - **World 3**: User weet niet dat synoniemen nodig zijn (no proactive suggestion)

   **Root Cause**: Passive synonym use (fallback-only) + manual YAML maintenance

2. **Visibility & Feedback Gap** (World 1 + 3)
   - **World 1**: User ziet niet welke synoniemen gebruikt worden in weblookup
   - **World 3**: User ziet niet welke synoniemen effectief zijn (usage analytics missing)

   **Root Cause**: No usage tracking, no UI integration

3. **Maintenance Burden** (World 2 + 3)
   - **World 2**: Token budget wasted op ineffective synonyms (0 hits)
   - **World 3**: Manual YAML edits (2 min per synonym, error-prone)

   **Root Cause**: No auto-sync DB→YAML, no quality-based filtering

### Quick Wins (Cross-World Impact)

1. **Enable Initial Synonym Expansion** (P0)
   - **Impact**: World 1 (betere hits), World 2 (betere context), World 3 (user ziet value)
   - **Effort**: Low (config change + adaptive logic)
   - **Rationale**: Synoniemen database bestaat al (50 terms, 184 synonyms), quality is hoog (95%+), ROI is groot

2. **Usage Tracking Instrumentation** (P0)
   - **Impact**: World 1 (measure effectiveness), World 3 (analytics feedback)
   - **Effort**: Medium (async logging + DB schema update)
   - **Rationale**: Enables all other improvements (can't optimize what you don't measure)

3. **Auto-Sync DB→YAML** (P0)
   - **Impact**: World 3 (eliminate manual edits), World 1 (fresh synonyms available)
   - **Effort**: Low (already implemented in YAMLConfigUpdater)
   - **Rationale**: Reduces maintenance from 2h/week to 30min, eliminates sync errors

---

## Unified Architecture

### Data Flow (End-to-End)

```
┌─────────────────────────────────────────────────────────────────┐
│                       USER INTERACTION                           │
│   (Definition Generator Tab - Inline Synonym Management)        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   SYNONYM WORKFLOW SERVICE                       │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐ │
│  │GPT4Suggester │UsageTracker  │YAMLUpdater   │QualityFilter │ │
│  │(AI generate) │(track hits)  │(DB→YAML sync)│(low-perf)    │ │
│  └──────────────┴──────────────┴──────────────┴──────────────┘ │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              DATABASE (synonym_suggestions)                      │
│  Columns: id, hoofdterm, synoniem, confidence, rationale,      │
│           status (pending/approved/active), usage_count,        │
│           last_used, effectiveness_score, context_data          │
│                                                                  │
│  NEW: usage_count, last_used, effectiveness_score (hit_rate)   │
└────────────────────────┬────────────────────────────────────────┘
                         │ (auto-sync on approve)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│            YAML FILE (juridische_synoniemen.yaml)               │
│  Status: Generated Artifact (READ-ONLY for users)              │
│  Format: hoofdterm → [weighted synonyms]                       │
│  Version Control: Git (audit trail)                            │
└────────────────────────┬────────────────────────────────────────┘
                         │ (loaded at startup)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│           JuridischeSynoniemlService (in-memory)                │
│  - Bidirectional lookup (term ↔ synonyms)                      │
│  - Weighted synonym support (confidence-based ranking)          │
│  - Used by: ModernWebLookupService                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              WEBLOOKUP QUERY EXPANSION                          │
│  INITIAL:  "voorlopige hechtenis"                              │
│  EXPAND:   "voorlopige hechtenis" OR "voorarrest" OR "bewaring"│
│  EXECUTE:  → Wikipedia, SRU Overheid, Rechtspraak              │
│  TRACK:    Log usage → update DB (usage_count++)               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   SEARCH RESULTS                                │
│  - Wikipedia: 3 hits (via "voorarrest" synonym)                │
│  - SRU: 5 hits (direct term match)                             │
│  - Ranked by: JuridischRanker (quality gate applied)           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                PROMPT AUGMENTATION                              │
│  Context section: "Uit Wikipedia (via synoniem 'voorarrest')"  │
│  Token budget: 400 tokens (prioritize juridical sources)       │
│  Snippet: "Voorarrest is voorlopige hechtenis vóór proces..."  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   GPT-4 GENERATION                              │
│  Input: Base prompt + Context (with synonym usage)             │
│  Output: Legal definition (synoniemen NOT explicitly mentioned) │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    USER FEEDBACK                                │
│  UI: "Web Lookup Report - Synoniemen gebruikt:                 │
│       ✓ voorarrest → 3 hits, ✗ bewaring → 0 hits"             │
│  Action: User marks "bewaring" for review                      │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

#### SynoniemenService (JuridischeSynoniemlService)

**Verantwoordelijkheden**:
- In-memory synoniemen database (loaded from YAML at startup)
- Bidirectional lookup (term → synonyms, synonym → term)
- Weighted synonym support (confidence-based ranking)
- Query expansion helper methods

**Reads from**: YAML file (juridische_synoniemen.yaml)
**Writes to**: None (read-only service)
**Used by**: ModernWebLookupService, SRU Service

#### WebLookupService (ModernWebLookupService)

**Verantwoordelijkheden**:
- Execute multi-provider search (Wikipedia, SRU, Rechtspraak, etc.)
- Initial synonym expansion (NEW: proactive, not just fallback)
- Usage tracking (NEW: log which synonyms got hits)
- Result aggregation and deduplication

**Reads from**: SynoniemenService (in-memory)
**Writes to**: UsageTracker (async logging)
**Configuration**: web_lookup_defaults.yaml (provider weights, boost factors)

#### PromptService (PromptServiceV2)

**Verantwoordelijkheden**:
- Integrate weblookup context into prompts
- Token budget management (400 tokens max for context)
- Prioritize juridical sources
- NO explicit synonym mention in prompt (synoniemen blijven invisible tool)

**Reads from**: WebLookup results
**Writes to**: GPT-4 API
**Note**: Synoniemen worden NIET expliciet in definitie vermeld (conform World 2 analyse)

#### UI Components

**Definition Generator Tab** (Enhanced):
- **Synonym Indicator**: Shows "X synoniemen gevonden" below term input
- **Inline Approval Dialog**: Quick approve/reject without leaving page
- **Web Lookup Report**: Collapsible panel showing synonym usage stats

**Synonym Review Tab** (Existing + Enhanced):
- **Bulk Operations**: Generate, approve, reject for multiple terms
- **Analytics Dashboard** (NEW): Top performers, low performers, trends
- **YAML Sync Status** (NEW): Last sync time, pending changes

**Settings Tab** (NEW - Optional):
- **Auto-approve Threshold**: Slider (default: 0.95)
- **YAML Health Report**: Duplicates, conflicts, unused synonyms
- **Hot Reload Toggle**: Enable/disable auto-sync without restart

### Integration Patterns

**Event-Driven Architecture** (NEW):
```
User approves synonym (UI)
  → Event: SynonymApproved(hoofdterm, synoniem, confidence)
  → Handler 1: YAMLConfigUpdater.add_synonym() [DB → YAML sync]
  → Handler 2: JuridischeSynoniemlService.reload() [hot reload in-memory]
  → Result: Synonym immediately available in weblookup (no restart)
```

**Async Usage Tracking** (NEW):
```
WebLookup executes query with synonym
  → Async: UsageTracker.log_usage(synoniem, provider, hit_count)
  → Batch: Every 10 uses → DB UPDATE (usage_count += 10)
  → Daily: Calculate effectiveness_score (hit_rate = hits / total_uses)
```

**Quality-Based Filtering** (NEW):
```
Weekly Job: LowPerformerDetector.scan()
  → Query: SELECT * WHERE usage_count = 0 AND last_used < NOW() - 30 days
  → Output: List of low-performing synonyms
  → Notification: "5 synoniemen met 0 hits - Review aanbevolen"
```

---

## Prioritized Roadmap

### Phase 1: Foundation (P0 - Must Have)

**Doel**: Establish database as single source of truth with usage tracking

**Rationale**: Can't optimize what you don't measure. Foundation enables all future enhancements.

**Features**:

#### 1.1: Database Schema Enhancement
- **Beschrijving**: Add `usage_count`, `last_used`, `effectiveness_score` columns to `synonym_suggestions` table
- **Rationale**: P0 omdat alle analytics/filtering features hiervan afhangen
- **Dependencies**: None
- **Success criteria**:
  - Migration runs successfully
  - Existing data preserved (new columns default to 0/NULL)
  - No performance regression on existing queries
- **Impact**: Enables usage tracking (foundational for all other features)
- **Effort**: Low (1 DB migration, ~1 hour)

```sql
ALTER TABLE synonym_suggestions
ADD COLUMN usage_count INTEGER DEFAULT 0,
ADD COLUMN last_used TIMESTAMP DEFAULT NULL,
ADD COLUMN effectiveness_score REAL DEFAULT NULL;

CREATE INDEX idx_synonym_usage ON synonym_suggestions(usage_count DESC, last_used DESC);
```

#### 1.2: Usage Tracking Service
- **Beschrijving**: Implement `UsageTracker` service that logs synonym usage during weblookup
- **Rationale**: P0 omdat dit de feedback loop sluit (measure effectiveness)
- **Dependencies**: 1.1 (DB schema)
- **Success criteria**:
  - Every synonym used in weblookup → logged
  - Async logging (no blocking, <5ms overhead)
  - Batch updates (every 10 uses → 1 DB write)
- **Impact**: User kan zien welke synoniemen effectief zijn
- **Effort**: Medium (new service + integration in ModernWebLookupService, ~1 dag)

**Integration Point**:
```python
# In ModernWebLookupService._lookup_mediawiki()
if synonym_used:
    await self.usage_tracker.log_usage(
        hoofdterm=hoofdterm,
        synoniem=synonym,
        provider="wikipedia",
        hit_count=len(results),
        timestamp=datetime.now(UTC)
    )
```

#### 1.3: Auto-Sync DB→YAML (Enable Existing Feature)
- **Beschrijving**: Verify and enable auto-sync from DB to YAML on synonym approval
- **Rationale**: P0 omdat dit manual YAML edits elimineert (biggest UX pain point)
- **Dependencies**: None (already implemented in YAMLConfigUpdater)
- **Success criteria**:
  - Approve synonym → YAML updated within 1 second
  - YAML validation before write (syntax check)
  - Backup created before sync (rollback capability)
  - Git commit voor audit trail (optional)
- **Impact**: User actions reduced van 7 steps naar 1 click
- **Effort**: Low (verify existing code, add tests, ~0.5 dag)

#### 1.4: Initial Synonym Expansion (Enable in Config)
- **Beschrijving**: Change weblookup strategy van "fallback-only" naar "initial expansion with adaptive fallback"
- **Rationale**: P0 omdat dit immediate ROI geeft (betere hits, betere context)
- **Dependencies**: None (synonym database exists, quality is high)
- **Success criteria**:
  - Primary query uses OR expansion: `"term" OR "syn1" OR "syn2"`
  - If primary term gets >3 hits → skip fallback synonyms (efficiency)
  - If primary term gets 0 hits → full synonym expansion
  - Usage tracked voor alle synonyms (zie 1.2)
- **Impact**: Wikipedia hit rate increases by ~40% (based on "onherroepelijk" → "kracht van gewijsde" case)
- **Effort**: Low (config change + adaptive logic in SRU service, ~0.5 dag)

**Config Change**:
```yaml
# config/web_lookup_defaults.yaml
synonyms:
  enabled: true
  strategy: "adaptive"  # NEW: was "fallback_only"
  initial_expansion: true  # NEW: enable proactive synonym use
  adaptive_threshold: 3  # NEW: skip fallback if primary term gets >=3 hits
```

---

### Phase 2: Enhancement (P1 - Should Have)

**Doel**: Surface synonyms in Definition Generator for inline management

**Rationale**: Minimize context switching, maximize user productivity

**Features**:

#### 2.1: Synonym Indicator Component
- **Beschrijving**: Add "X synoniemen gevonden" indicator below term input in Definition Generator
- **Rationale**: P1 omdat dit visibility geeft (user ziet dat synoniemen gebruikt worden)
- **Dependencies**: None (uses existing JuridischeSynoniemlService)
- **Success criteria**:
  - Shows count on term change (debounced 500ms)
  - Expandable list with confidence scores
  - Click → shows details (hoofdterm, confidence, rationale)
- **Impact**: User awareness van synonym system increases
- **Effort**: Medium (Streamlit UI component, ~1 dag)

#### 2.2: Inline Approval Dialog
- **Beschrijving**: Popup voor synonym approval zonder leaving Definition Generator page
- **Rationale**: P1 omdat dit biggest UX friction elimineert (navigate to /synonym_review)
- **Dependencies**: 1.3 (auto-sync moet werken)
- **Success criteria**:
  - Trigger: "Genereer synoniemen" button OR proactive suggestion
  - Actions: Approve (1 click), Reject (1 click), Edit (inline), Later (dismiss)
  - Feedback: "✓ Synoniem toegevoegd, beschikbaar in 1 sec"
- **Impact**: Synonym approval time: 2 min → 10 sec
- **Effort**: Medium (Streamlit dialog + integration, ~1.5 dag)

**UI Mock**:
```
┌────────────────────────────────────────────┐
│ 💡 Nieuwe synoniemen gevonden!            │
│                                            │
│ Term: verdachte                            │
│                                            │
│ ✓ beklaagde (confidence: 0.92)            │
│   "Formele term in strafrecht"            │
│   [✓] [✗] [✎]                            │
│                                            │
│ [Approve All] [Reject All] [Later]        │
└────────────────────────────────────────────┘
```

#### 2.3: Web Lookup Report Panel
- **Beschrijving**: Collapsible panel showing synonym usage stats after definition generation
- **Rationale**: P1 omdat dit feedback loop sluit (user ziet effect van synoniemen)
- **Dependencies**: 1.2 (usage tracking)
- **Success criteria**:
  - Shows which synonyms were used
  - Shows hit count per synonym per provider
  - Highlights ineffective synonyms (0 hits) with action button
- **Impact**: User kan low-performers identificeren en reviewen
- **Effort**: Medium (Streamlit panel + data aggregation, ~1 dag)

**UI Mock**:
```
┌────────────────────────────────────────────┐
│ 📊 Web Lookup Rapport                     │
│                                            │
│ Synoniemen gebruikt:                       │
│ ✓ beklaagde      → 8 resultaten ████████  │
│ ✓ beschuldigde   → 3 resultaten ███       │
│ ✗ aangeklaagde   → 0 resultaten           │
│                                            │
│ 💡 "aangeklaagde" niet effectief          │
│    [Review Synoniem] [Dismiss]            │
└────────────────────────────────────────────┘
```

---

### Phase 3: Experimentation (P2 - Nice to Have)

**Doel**: Proactive synonym management + analytics

**Rationale**: Reduce user effort, improve quality over time

**Features**:

#### 3.1: Analytics Dashboard
- **Beschrijving**: Add analytics tab to Synonym Review page
- **Rationale**: P2 omdat dit optimization insight geeft (maar niet blocking)
- **Dependencies**: 1.2 (usage tracking moet 2+ weken data hebben)
- **Success criteria**:
  - Top 10 most-used synonyms (by usage_count)
  - Low performers (0 hits in 30 days)
  - Approval rate trends (pending vs approved over time)
  - Geographic distribution (which providers use which synonyms)
- **Impact**: Product owner kan data-driven decisions maken over synonym quality
- **Effort**: High (data aggregation + visualization, ~2 dagen)

#### 3.2: Auto-Approve High-Confidence Suggestions
- **Beschrijving**: Automatically approve suggestions with confidence >0.95
- **Rationale**: P2 omdat dit efficiency win is (maar risico van false positives)
- **Dependencies**: None (GPT4Suggester already returns confidence)
- **Success criteria**:
  - Configurable threshold (default: 0.95, user can adjust)
  - Notification: "3 synoniemen auto-approved (conf >0.95)"
  - Easy revert (1-click undo binnen 24h)
  - Weekly digest: "Review 5 auto-approved synonyms"
- **Impact**: Reduces approval time by 50% for high-confidence suggestions
- **Effort**: Low (business logic + notification, ~0.5 dag)

**Risk Mitigation**:
- User can disable auto-approve in settings
- Weekly review reminder (safety net)
- Easy revert (24h window)

#### 3.3: Low-Performer Detector
- **Beschrijving**: Weekly job that flags synonyms with 0 hits in 30 days
- **Rationale**: P2 omdat dit proactive quality management enables
- **Dependencies**: 1.2 (usage tracking), 1.4 (effectiveness_score calculation)
- **Success criteria**:
  - Query: `SELECT * WHERE usage_count = 0 AND created_at < NOW() - 30 days`
  - Notification: "5 synoniemen met 0 hits - Review aanbevolen"
  - Action: Mark for review, suggest deletion, or keep with reason
- **Impact**: Prevents YAML bloat, improves weblookup performance (fewer useless queries)
- **Effort**: Low (cron job + notification, ~0.5 dag)

#### 3.4: Example Parser (Extract Synonyms from Definition Examples)
- **Beschrijving**: NLP parser die synoniemen extract uit definition examples
- **Rationale**: P2 omdat dit new synonym source unlocks (World 3 integration)
- **Dependencies**: None (but needs NLP library)
- **Success criteria**:
  - Pattern: `term (synonym)` or `synonym (term)` → extract synonym
  - Confidence: Auto-assign 0.7 (medium, needs review)
  - Notification: "2 synoniemen gevonden in voorbeelden, toevoegen?"
- **Impact**: Captures implicit synonyms from examples (hidden knowledge)
- **Effort**: High (NLP pattern matching + false positive handling, ~2 dagen)

---

## Key Architectural Decisions

### Decision 1: Initial Synonym Expansion Strategy

**Context**: Synoniemen worden nu alleen gebruikt als fallback (na primary term fail). Dit leidt tot gemiste content.

**Options**:

**A) Fallback-only (current)**
- **Pro**: Conservative (no query bloat), fast (fewer API calls)
- **Con**: Misses relevant content (Wikipedia "kracht van gewijsde" voor "onherroepelijk")
- **Con**: User doesn't see synonym value (no visibility)

**B) Initial expansion (always)**
- **Pro**: Maximale coverage (all synonyms tried), best definitie quality
- **Con**: Query bloat (5 synonyms → 5x API calls), slower, token waste
- **Con**: Provider rate limits (too many OR clauses)

**C) Adaptive (hybrid)**
- **Pro**: Balances coverage + efficiency
- **Pro**: Primary term succeeds → skip fallback (no waste)
- **Pro**: Primary term fails → full expansion (max coverage)
- **Con**: More complex logic (conditional branching)

**RECOMMENDATION**: **Option C - Adaptive Expansion**

**RATIONALE**:
1. **Data**: Synonym database is high-quality (95% precision, 50 terms, 184 synonyms)
2. **Evidence**: "onherroepelijk" case proves ROI (Wikipedia hit via "kracht van gewijsde" synonym)
3. **Efficiency**: Adaptive threshold (>3 hits → skip fallback) prevents query bloat
4. **User Value**: Visible synonym usage in Web Lookup Report (builds trust)

**Implementation**:
```python
async def _lookup_with_synonyms(term):
    # Step 1: Try primary term
    results = await _lookup_primary(term)

    # Step 2: Adaptive decision
    if len(results) >= 3:
        # Primary term successful → skip synonyms
        return results

    # Step 3: Full synonym expansion (fallback)
    synonyms = synonym_service.get_synoniemen(term)
    for syn in synonyms[:3]:  # limit to top 3
        syn_results = await _lookup_primary(syn)
        results.extend(syn_results)

    return deduplicate(results)
```

---

### Decision 2: Synoniemen Expliciet Vermelden in Definitie?

**Context**: Moeten synoniemen zichtbaar zijn in gegenereerde definitie tekst?

**Options**:

**A) Never (current)**
- **Pro**: Definitie is concise, geen clutter
- **Pro**: Synoniemen zijn tool (not content), blijven invisible
- **Con**: User ziet niet dat synoniemen bestaan (discovery probleem)

**B) Always**
- **Pro**: Full transparency (user ziet alle synoniemen)
- **Pro**: Educational (user leert synoniemen via definitie)
- **Con**: Definitie wordt verbose ("verdachte (ook wel: beklaagde, beschuldigde, aangeklaagde)")
- **Con**: Irrelevant voor sommige use cases (formal legal text)

**C) Optional (config flag)**
- **Pro**: User choice (flexibility)
- **Pro**: Can A/B test impact on definitie quality
- **Con**: Configuration complexity
- **Con**: GPT-4 prompt needs conditional logic

**RECOMMENDATION**: **Option A - Never (Keep Current Behavior)**

**RATIONALE**:
1. **World 2 Analysis**: "Synoniemen NIET expliciet in definitie, alleen als query expansion tool" (confirmed by product manager analysis)
2. **Token Budget**: Including synonyms in definitie uses tokens (opportunity cost)
3. **Quality**: Definitions should be concise and authoritative (not synonym lists)
4. **Alternative**: Show synonyms in UI (Synonym Indicator component) for discovery, but keep out of definitie text

**Exception**: If GPT-4 naturally uses synonyms in examples (e.g., "De verdachte (beklaagde) werd vrijgesproken"), allow it, but don't force it via prompt.

---

### Decision 3: Inline Approval vs Separate Synoniemen Page?

**Context**: Waar managet user synoniemen?

**Options**:

**A) Only inline (Definition Generator)**
- **Pro**: Zero context switching, minimal friction
- **Pro**: Context-aware (user ziet synoniemen during definition workflow)
- **Con**: Limited space for bulk operations
- **Con**: No analytics dashboard (need separate page anyway)

**B) Only separate (Synonym Review page)**
- **Pro**: Full-featured UI (bulk operations, filters, analytics)
- **Pro**: Power user friendly
- **Con**: Context switching (user loses flow)
- **Con**: Lower adoption (out of sight, out of mind)

**C) Both (inline for quick, separate for bulk)**
- **Pro**: Best of both worlds (quick + powerful)
- **Pro**: Progressive disclosure (inline for 80% use cases, separate for 20%)
- **Con**: Duplication of UI logic
- **Con**: Maintenance burden (2 UIs to keep in sync)

**RECOMMENDATION**: **Option C - Both (Hybrid Approach)**

**RATIONALE**:
1. **User Research**: Different use cases need different tools
   - **Quick approval**: User generating definition, sees suggestion → approve inline (1 click)
   - **Bulk management**: User reviews 50 pending suggestions → separate page with filters/sorting
2. **Progressive Disclosure**: Don't overwhelm user with full-featured UI when they just need quick approve
3. **Adoption**: Inline UI increases adoption (user discovers synonym system naturally during workflow)
4. **Maintenance**: UI logic is shared (same backend services, different views)

**Implementation**:
- **Inline**: Simple dialog (approve/reject/edit/later), triggered from Definition Generator
- **Separate**: Full-featured page (bulk operations, filters, analytics, YAML health)

---

### Decision 4: Quality Metrics Tracking - Where/When?

**Context**: Hoe en wanneer tracken we synonym effectiveness?

**Options**:

**A) Real-time (every lookup)**
- **Pro**: Fresh data (up-to-date hit rates)
- **Pro**: Immediate feedback (user sees effect instantly)
- **Con**: Performance overhead (DB write per lookup)
- **Con**: Locking contention (multiple concurrent lookups)

**B) Batch (daily aggregation)**
- **Pro**: Low overhead (1 DB write per day per synonym)
- **Pro**: No locking (off-peak processing)
- **Con**: Stale data (user sees yesterday's metrics)
- **Con**: Implementation complexity (batch job + scheduler)

**C) Hybrid (async log + batch aggregate)**
- **Pro**: Best of both (low overhead + fresh-enough data)
- **Pro**: Async logging (no blocking, <5ms overhead)
- **Pro**: Batch updates (every 10 uses → 1 DB write)
- **Con**: Slight delay in metrics (acceptable for this use case)

**RECOMMENDATION**: **Option C - Hybrid (Async Log + Batch Aggregate)**

**RATIONALE**:
1. **Performance**: Async logging eliminates blocking (user doesn't wait)
2. **Efficiency**: Batch updates reduce DB writes (90% reduction)
3. **Freshness**: Metrics update every ~10 uses (acceptable latency for analytics)
4. **Scalability**: Works even with high lookup volume (no locking contention)

**Implementation**:
```python
class UsageTracker:
    def __init__(self):
        self.buffer = []  # In-memory buffer
        self.batch_size = 10

    async def log_usage(self, hoofdterm, synoniem, provider, hit_count):
        # Add to buffer (non-blocking)
        self.buffer.append({
            "hoofdterm": hoofdterm,
            "synoniem": synoniem,
            "provider": provider,
            "hit_count": hit_count,
            "timestamp": datetime.now(UTC)
        })

        # Flush buffer if full (async)
        if len(self.buffer) >= self.batch_size:
            await self._flush_buffer()

    async def _flush_buffer(self):
        # Batch DB update (1 query, multiple rows)
        await db.executemany(
            "UPDATE synonym_suggestions SET usage_count = usage_count + ? WHERE synoniem = ?",
            [(1, item["synoniem"]) for item in self.buffer]
        )
        self.buffer.clear()
```

**Daily Job**: Calculate `effectiveness_score = hit_count / total_uses` voor analytics dashboard

---

## Success Metrics

### User Experience Metrics

1. **Time to Add Synonym**
   - **Baseline**: 2 min (manual YAML edit)
   - **Target**: 10 sec (inline approval)
   - **Measurement**: Track time from "Generate suggestions" click to "Approve" click

2. **Actions to Approve Synonym**
   - **Baseline**: 7 steps (navigate, generate, review, approve, manual YAML edit, restart app)
   - **Target**: 1 click (inline approve with auto-sync)
   - **Measurement**: Count user interactions per synonym approval

3. **Context Switching**
   - **Baseline**: 100% (must navigate to /synonym_review)
   - **Target**: <20% (80% use inline approval, 20% use separate page for bulk)
   - **Measurement**: Track navigation patterns in analytics

4. **Synonym Discovery Rate**
   - **Baseline**: Unknown (no visibility)
   - **Target**: 90% of users notice "X synoniemen gevonden" indicator
   - **Measurement**: A/B test with/without indicator, track engagement

### Quality Metrics

1. **Synonym Precision**
   - **Baseline**: 95% (manual curation)
   - **Target**: >90% (maintain after AI suggestions + human approval)
   - **Measurement**: Sample 50 approved synonyms, expert review for correctness

2. **Definition Quality Score (Validation)**
   - **Baseline**: Current average validation score (unknown)
   - **Target**: +5% improvement (via better weblookup context)
   - **Measurement**: Compare validation scores before/after synonym expansion enabled

3. **Synonym Coverage Growth**
   - **Baseline**: 50 terms, 184 synonyms (3.68 avg per term)
   - **Target**: 150 terms, 500 synonyms (3.33 avg per term)
   - **Measurement**: Track DB growth over 3 months

4. **Low-Performer Rate**
   - **Baseline**: Unknown
   - **Target**: <10% of synonyms have 0 hits in 30 days
   - **Measurement**: Weekly report from LowPerformerDetector

### Efficiency Metrics

1. **Weblookup Hit Rate**
   - **Baseline**: Unknown (no tracking)
   - **Target**: Wikipedia hit rate +40% (based on "onherroepelijk" case study)
   - **Measurement**: Compare hits before/after initial synonym expansion enabled

2. **Token Usage (Prompt)**
   - **Baseline**: 2800-3800 tokens per definition (World 2 analysis)
   - **Target**: No increase (efficiency maintained)
   - **Measurement**: Track prompt tokens via OpenAI API response

3. **API Call Count**
   - **Baseline**: ~5 providers per lookup (current)
   - **Target**: <7 providers per lookup (with adaptive synonym expansion)
   - **Measurement**: Track provider calls, calculate average

4. **YAML Sync Success Rate**
   - **Baseline**: ~90% (manual sync errors)
   - **Target**: >99% (auto-sync with validation)
   - **Measurement**: Track sync failures, rollback events

### Coverage Metrics

1. **Synonyms Per Term**
   - **Baseline**: 3.68 avg (184 synonyms / 50 terms)
   - **Target**: 3.5-4.0 avg (quality over quantity)
   - **Measurement**: Calculate avg after each batch approval

2. **Hit Rate Per Provider**
   - **Baseline**: Wikipedia unknown, SRU 100%, Rechtspraak 100%
   - **Target**: Wikipedia >60% (via synonym expansion)
   - **Measurement**: Track hits per provider, calculate hit_rate = hits / total_queries

3. **Synonym Usage Distribution**
   - **Baseline**: Unknown
   - **Target**: 80/20 rule (80% of value from 20% of synonyms)
   - **Measurement**: Pareto chart of usage_count distribution

---

## Risk Mitigation

### Risk 1: Auto-Sync YAML Corruption

**Description**: Automated DB→YAML sync schrijft corrupt file, breaking weblookup

**Impact**: High (blocks definition generation)
**Probability**: Low (with proper validation)

**Mitigation**:
1. **YAML Validator**: Syntax check before write (detect malformed YAML)
2. **Git Version Control**: Every sync is a commit (easy rollback)
3. **Backup Before Sync**: Copy to `juridische_synoniemen.yaml.bak`
4. **Integration Tests**: Test YAML write/read cycle with edge cases
5. **Canary Check**: After sync, reload in-memory and verify synonym count

**Monitoring**:
- Alert if YAML parse fails during reload
- Alert if synonym count drops >10% after sync
- Weekly audit: Compare DB vs YAML consistency

### Risk 2: High-Confidence Auto-Approve Errors

**Description**: GPT-4 suggests wrong synonym with high confidence, auto-approved, breaks quality

**Impact**: Medium (degrades definition quality)
**Probability**: Low (GPT-4 is accurate for juridical terms)

**Mitigation**:
1. **User Control**: Disable auto-approve in settings (default: enabled)
2. **Conservative Threshold**: Default 0.95 (very high confidence required)
3. **Weekly Review**: Notification "Review 5 auto-approved synonyms"
4. **Easy Revert**: 1-click undo within 24h (safety net)
5. **Audit Trail**: Log all auto-approvals (who, what, when, confidence)

**Monitoring**:
- Track auto-approve rate (alert if >20% of all approvals)
- Track revert rate (alert if >5% of auto-approvals reverted)
- Monthly expert review: Sample 10 auto-approved synonyms

### Risk 3: Usage Tracking Performance Impact

**Description**: Logging synonym usage on every weblookup slows down definition generation

**Impact**: Medium (user-facing latency)
**Probability**: Low (with async implementation)

**Mitigation**:
1. **Async Logging**: Non-blocking (< 5ms overhead per lookup)
2. **Batch Updates**: Buffer 10 uses → 1 DB write (reduce contention)
3. **Index Optimization**: Add index on `usage_count`, `last_used` columns
4. **Performance Testing**: Load test with 100 concurrent lookups
5. **Circuit Breaker**: If tracking fails, log error but don't block weblookup

**Monitoring**:
- Track weblookup latency (alert if p95 > 3 seconds)
- Track DB write latency (alert if batch update > 100ms)
- Track buffer overflow (alert if buffer grows > 100 items)

### Risk 4: User Overwhelm (Too Many Features)

**Description**: Releasing all features at once overwhelms user, reduces adoption

**Impact**: Medium (feature goes unused)
**Probability**: Medium (lots of new UI elements)

**Mitigation**:
1. **Phased Rollout**: Ship Phase 1 → wait 1 week → Phase 2 → wait 1 week → Phase 3
2. **Progressive Disclosure**: Hide advanced features behind "Advanced" tab
3. **Smart Defaults**: Auto-approve threshold 0.95 (conservative), usage tracking enabled
4. **Onboarding**: "New synonym features!" popup with 30-second tour
5. **Opt-Out**: User can disable features via settings (fallback to old behavior)

**Monitoring**:
- Track feature engagement (% of users who use inline approval)
- User feedback: Survey after 2 weeks ("How helpful are new synonym features?")
- A/B test: Rollout to 50% of users first, compare metrics

---

## Open Questions

### Empirische Vragen (Need A/B Testing)

- [ ] **Q1**: Does initial synonym expansion improve definition validation scores?
  - **Method**: A/B test (50% with expansion, 50% without) for 2 weeks, compare avg validation score
  - **Hypothesis**: +5% improvement in validation scores
  - **Decision**: If improvement <2%, revert to fallback-only (not worth complexity)

- [ ] **Q2**: What is optimal auto-approve confidence threshold?
  - **Method**: Track revert rate for different thresholds (0.90, 0.95, 0.98)
  - **Hypothesis**: 0.95 balances efficiency (auto-approve 60% of suggestions) with quality (revert rate <5%)
  - **Decision**: Adjust threshold based on data after 1 month

- [ ] **Q3**: Does inline approval increase synonym adoption?
  - **Method**: Compare approval rate before/after inline UI (separate page vs inline)
  - **Hypothesis**: +50% increase in approval rate (easier access → more usage)
  - **Decision**: If increase <20%, inline UI might not be worth effort

### Technical Spikes (Need Performance Testing)

- [ ] **Q4**: What is actual performance impact of usage tracking?
  - **Method**: Load test with 100 concurrent lookups, measure latency with/without tracking
  - **Hypothesis**: <5ms overhead per lookup (acceptable)
  - **Decision**: If overhead >10ms, switch to daily batch-only (no real-time tracking)

- [ ] **Q5**: Can YAML hot-reload work without race conditions?
  - **Method**: Stress test with concurrent lookups during YAML reload
  - **Hypothesis**: File-based reload is safe (Python GIL protects in-memory dict)
  - **Decision**: If race conditions found, implement reader-writer lock or restart-only

- [ ] **Q6**: What is realistic synonym coverage target?
  - **Method**: Analyze existing legal definitions, count unique terms without synonyms
  - **Hypothesis**: 150 terms (3x growth) is achievable in 3 months with AI assistance
  - **Decision**: Adjust target based on GPT-4 suggestion quality after 1 month

### User Research (Need User Feedback)

- [ ] **Q7**: What synonym information do users actually want to see?
  - **Method**: User interviews (5 users), show mockups, ask "What's useful?"
  - **Hypothesis**: Users want usage stats (hit count) + confidence, NOT rationale (too verbose)
  - **Decision**: Adjust UI based on feedback (remove/hide less useful fields)

- [ ] **Q8**: How often do users want proactive synonym suggestions?
  - **Method**: Track dismissal rate of "Genereer synoniemen" prompts
  - **Hypothesis**: <10% dismissal rate (users find suggestions helpful)
  - **Decision**: If dismissal rate >30%, reduce proactive prompts frequency

- [ ] **Q9**: Should low-performer notifications be opt-in or opt-out?
  - **Method**: A/B test (50% get weekly notifications, 50% don't), compare cleanup rate
  - **Hypothesis**: Notifications increase cleanup rate by 50% (proactive management)
  - **Decision**: If no significant difference, make notifications opt-in (reduce noise)

---

## Implementation Dependencies Graph

```
Phase 1 (Foundation)
===================
1.1 (DB Schema) ────────────┐
                            ▼
1.2 (Usage Tracking) ──────────────┐
                                   ▼
1.3 (Auto-Sync DB→YAML)           3.1 (Analytics Dashboard)
                                   │
1.4 (Initial Expansion) ───────────┤
                                   ▼
                            2.3 (Web Lookup Report)

Phase 2 (Enhancement)
=====================
2.1 (Synonym Indicator) ──────┐
                              ▼
2.2 (Inline Approval) ────────┴──┐
                                 ▼
2.3 (Web Lookup Report) ─────────┴───→ Full inline workflow

Phase 3 (Experimentation)
==========================
3.1 (Analytics Dashboard) ───────┐
                                 ▼
3.3 (Low-Performer Detector) ────┴──┐
                                    ▼
3.2 (Auto-Approve) ─────────────────┴──→ Fully automated workflow

3.4 (Example Parser) ────────────────────→ Independent (can ship anytime)
```

**Critical Path** (blocking other work):
```
1.1 (DB Schema) → 1.2 (Usage Tracking) → 2.3 (Report) → 3.1 (Analytics)
```

**Parallel Work** (can ship independently):
```
1.3 (Auto-Sync) + 1.4 (Initial Expansion) + 2.1 (Indicator) + 2.2 (Inline Approval)
```

---

## Conclusion

### Kern van de Oplossing

**"Best of 3 Worlds"** integreert drie parallelle problemen in één coherente oplossing:

1. **World 1 (Weblookup)** → Synoniemen worden proactief gebruikt (initial expansion) met adaptive fallback, quality gate voorkomt irrelevante juridical boosts
2. **World 2 (Context)** → Token efficiency behouden, synoniemen blijven invisible tool (niet in definitie), ROI wordt gemeten via validation scores
3. **World 3 (UX)** → Database is single source of truth, inline approval (1 click), automatic YAML sync, full visibility via analytics

### Waarom Gaat Dit Werken?

**Cross-Cutting Benefits**:
- **Synoniemen coverage** verbetert door initial expansion (World 1) + AI suggestions (World 3)
- **User efficiency** verbetert door inline approval (World 3) + visible impact (World 2 report)
- **Quality** verbetert door usage tracking (World 1) + low-performer detection (World 3)

**Minimal Risk**:
- Phased rollout (P0 → P1 → P2) spreads risk
- Mitigations in place (YAML validation, auto-approve revert, async tracking)
- A/B testing for empirical validation (niet gokken, meten)

**Maximal Impact**:
- Quick wins in Phase 1 (80% of value, 20% of effort)
- Progressive enhancement in Phase 2-3 (power user features)
- Measurable success criteria (niet "improve quality", maar "+5% validation score")

### Next Steps

1. **Stakeholder Review** (Product Owner): Approve phased roadmap + priorities
2. **Technical Spike** (1 day): Validate usage tracking performance (< 5ms overhead?)
3. **Design Review** (2 days): Wireframes for inline approval dialog + Web Lookup Report
4. **Phase 1 Kickoff** (Week 1): Implement DB enhancements + usage tracking + auto-sync + initial expansion

**Questions?** Contact Claude Code for clarification or prioritization adjustments.

---

**Document Version**: 1.0
**Last Updated**: October 9, 2025
**Status**: Pending Approval
**Next Review**: After Phase 1 completion
