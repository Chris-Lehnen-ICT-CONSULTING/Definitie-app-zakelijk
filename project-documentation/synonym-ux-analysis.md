# UX Analysis: Synonym Management "Best of 3 Worlds"

**Date**: October 9, 2025
**Role**: Product Manager
**Focus**: User Experience & Workflow Optimization

---

## Executive Summary

User currently manages synonyms across **3 disconnected systems**, causing friction, duplication, and maintenance overhead. This analysis proposes a **unified UX** that combines the best aspects of each system while minimizing user actions and maximizing quality.

**Goal**: Single source of truth with automatic sync, minimal manual intervention, and clear feedback loops.

---

## The 3 Worlds: Current State Analysis

### World 1: YAML File (`juridische_synoniemen.yaml`)
**What it is**: Manual, human-curated synonym database (50 terms, 184 synonyms)

**Current Usage**:
- Used by `JuridischeSynoniemlService` for web lookup query expansion
- Supports weighted synonyms (confidence 0.0-1.0)
- Bidirectional lookup (term → synonyms, synonym → term)
- Read by `ModernWebLookupService` during definition generation

**Strengths**:
- ✅ High precision (95%+ - manually curated)
- ✅ Weighted synonyms for confidence-based ranking
- ✅ Version controlled (git)
- ✅ Used in production by web lookup

**Pain Points**:
- ❌ Manual YAML editing (error-prone)
- ❌ No validation feedback during editing
- ❌ No visibility into usage/effectiveness
- ❌ Requires developer skills (YAML syntax)

**User Actions**:
1. Open `juridische_synoniemen.yaml` in text editor
2. Manually add synonym under hoofdterm
3. Save file (hope syntax is correct)
4. Restart app to see changes (no hot reload)

---

### World 2: Database + Approval Workflow (`synonym_suggestions` table)
**What it is**: AI-generated suggestions with human approval workflow

**Current Usage**:
- GPT-4 generates synonym candidates with confidence + rationale
- Stored in `synonym_suggestions` table (status: pending/approved/rejected)
- Streamlit UI (`/synonym_review`) for approval workflow
- `SynonymWorkflow` orchestrates suggest → approve → YAML update

**Strengths**:
- ✅ Scalable (AI generates 5-8 candidates per term)
- ✅ Context-aware (uses existing definitions)
- ✅ Human-in-the-loop prevents hallucinations
- ✅ Rationale for transparency
- ✅ Bulk operations (approve all >0.9 confidence)
- ✅ Revert functionality (undo approvals)

**Pain Points**:
- ❌ Disconnected from YAML (manual sync required)
- ❌ No visibility into YAML usage during approval
- ❌ Approved suggestions don't auto-update production
- ❌ Rejection feedback not used to improve future suggestions

**User Actions**:
1. Navigate to `/synonym_review` page
2. Generate suggestions for term (GPT-4 call)
3. Review pending suggestions (read rationale, check confidence)
4. Approve/Reject/Revert individual suggestions
5. **MANUAL**: Copy approved synonyms to YAML file
6. **MANUAL**: Restart app to use new synonyms

---

### World 3: Definition Examples (implicit synonyms)
**What it is**: Synonym usage demonstrated in definition examples

**Current Usage**:
- Definitions stored in `definities` table have `voorbeelden` field
- Examples often use synonyms naturally: "De verdachte (beklaagde) werd vrijgesproken"
- Not explicitly tracked as synonyms but provide usage context

**Strengths**:
- ✅ Real-world usage examples
- ✅ Context-aware (shows synonym in sentence)
- ✅ Quality validation (if example is good, synonym is good)

**Pain Points**:
- ❌ Not extracted/indexed as synonyms
- ❌ No bidirectional link (example → synonym → YAML)
- ❌ Valuable synonym data locked in unstructured text

**User Actions**:
1. Write definition
2. Add example using synonym naturally
3. No further action (synonym not captured)

---

## Current User Pain Points (Prioritized)

### Critical (Blocking Daily Work)
1. **Duplicate Entry**: User must enter synonyms in BOTH DB and YAML manually
2. **No Auto-Sync**: Approved DB suggestions don't update YAML automatically
3. **No Validation Feedback**: YAML syntax errors only discovered on app crash
4. **Context Loss**: Approved synonyms lose their rationale/confidence in YAML

### High (Causes Frustration)
5. **No Usage Analytics**: User doesn't know which synonyms are actually used
6. **Manual Restart Required**: Changes require app restart (no hot reload)
7. **No Bidirectional View**: Can't see "where is this synonym used?" in UI
8. **Rejection Waste**: Rejected suggestions don't improve future prompts

### Medium (Quality of Life)
9. **No Conflict Detection**: YAML can have duplicate entries across hoofdtermen
10. **No Synonym Suggestions in Definition UI**: User writes definition but doesn't see relevant synonyms
11. **No Batch YAML Import**: Can't import external synonym lists easily

---

## Ideal User Workflow: "Best of 3 Worlds"

### The Vision
**Single source of truth (Database) with automatic YAML sync and inline usage feedback**

```
┌─────────────────────────────────────────────────────────────┐
│                     SINGLE SOURCE OF TRUTH                   │
│                  Database (synonym_suggestions)              │
│                                                              │
│  Status: pending → approved → active (in YAML)              │
│  Metadata: confidence, rationale, usage_count, last_used    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ├──→ Auto-Sync to YAML (on approve)
                           ├──→ Track usage in web_lookup
                           └──→ Show in Definition Generator UI
```

---

## Unified User Workflow (Proposed)

### UC1: User Generates Definition (Uses Synonyms)

**Current Flow** (Painful):
1. User enters term "verdachte"
2. Clicks "Genereer"
3. GPT-4 generates definition
4. Web lookup uses YAML synonyms (beklaagde, beschuldigde)
5. User has NO visibility that synonyms were used

**Ideal Flow** (Seamless):
1. User enters term "verdachte"
2. **NEW**: UI shows "3 synoniemen gevonden: beklaagde, beschuldigde, aangeklaagde"
3. Clicks "Genereer"
4. **NEW**: Progress indicator: "Web lookup gebruikt synoniemen: beklaagde (3 hits), beschuldigde (1 hit)"
5. Definition generated
6. **NEW**: Sidebar shows "Synoniemen gebruikt in deze definitie" with usage stats

**UI Mock**:
```
┌─────────────────────────────────────────────────────────────┐
│ Term: verdachte                                              │
│ 💡 3 synoniemen gevonden: beklaagde (conf: 0.95), ...       │
│                                                              │
│ [Genereer Definitie]                                        │
│                                                              │
│ ⚡ Web lookup:                                               │
│   ✓ beklaagde → 3 resultaten (Wikipedia, Rechtspraak)      │
│   ✓ beschuldigde → 1 resultaat (Overheid.nl)               │
│   ✗ aangeklaagde → 0 resultaten                            │
└─────────────────────────────────────────────────────────────┘
```

---

### UC2: User Manages Synonyms (Approval)

**Current Flow** (Disconnected):
1. User navigates to `/synonym_review`
2. Clicks "Genereer Suggesties" for term
3. Reviews pending suggestions
4. Approves good ones
5. **MANUAL**: Opens YAML file
6. **MANUAL**: Copy-pastes approved synonyms
7. **MANUAL**: Restarts app

**Ideal Flow** (Automated):
1. User stays in Definition Generator tab
2. **NEW**: Inline suggestion appears: "💡 GPT-4 vindt 2 nieuwe synoniemen voor 'verdachte': beklaagde (0.92), beschuldigde (0.88) [Review]"
3. Clicks [Review] → opens inline approval dialog
4. Approves with 1 click
5. **AUTOMATIC**: DB updated to "approved" status
6. **AUTOMATIC**: YAML regenerated with new synonym
7. **AUTOMATIC**: Synonym immediately available (no restart)

**Alternative (Batch Mode)**:
1. User navigates to `/synonym_review` (optional)
2. Bulk generates suggestions for all terms
3. Uses filters: "High confidence only (>0.85)"
4. Bulk approves with confirmation
5. **AUTOMATIC**: All approved synonyms synced to YAML
6. **AUTOMATIC**: Changes live immediately

**UI Mock (Inline Approval)**:
```
┌─────────────────────────────────────────────────────────────┐
│ 💡 Nieuwe synoniemen gevonden!                              │
│                                                              │
│ Term: verdachte                                              │
│                                                              │
│ ✓ beklaagde (confidence: 0.92)                              │
│   Rationale: "Formele term in strafrecht"                   │
│   [✓ Approve] [✗ Reject] [✎ Edit]                          │
│                                                              │
│ ✓ beschuldigde (confidence: 0.88)                           │
│   Rationale: "Algemene term voor verdachte persoon"         │
│   [✓ Approve] [✗ Reject] [✎ Edit]                          │
│                                                              │
│ [Approve All] [Reject All] [Later]                          │
└─────────────────────────────────────────────────────────────┘
```

---

### UC3: User Adds New Term

**Current Flow** (Manual):
1. User realizes term needs synonyms
2. Opens YAML file
3. Adds entry manually
4. Restarts app

**Ideal Flow** (AI-Assisted):
1. User enters new term in Definition Generator
2. **NEW**: UI detects term not in synonym DB
3. **NEW**: Popup: "Geen synoniemen gevonden. [Genereer met AI] [Toevoegen handmatig] [Overslaan]"
4. User clicks [Genereer met AI]
5. GPT-4 generates suggestions (uses existing definition as context)
6. Inline approval dialog appears
7. User approves best candidates
8. **AUTOMATIC**: Synonyms added to DB + YAML

**UI Mock (Proactive Suggestion)**:
```
┌─────────────────────────────────────────────────────────────┐
│ ⚠️ Term "hoger beroep" heeft geen synoniemen                │
│                                                              │
│ Wil je GPT-4 synoniemen laten genereren?                    │
│                                                              │
│ [🤖 Genereer met AI] [✎ Handmatig toevoegen] [Overslaan]   │
└─────────────────────────────────────────────────────────────┘
```

---

### UC4: System Does Web Lookup (Uses Synonyms)

**Current Flow** (Silent):
1. User clicks "Genereer"
2. Web lookup uses synonyms from YAML
3. Results returned (user has no visibility)

**Ideal Flow** (Transparent):
1. User clicks "Genereer"
2. **NEW**: Progress indicator shows:
   - "Wikipedia: verdachte (0 hits) → beklaagde (3 hits) ✓"
   - "Rechtspraak: verdachte (5 hits) ✓"
3. **NEW**: After generation, "Web Lookup Report" tab:
   - "5 bronnen gebruikt, 2 synoniemen effectief"
   - Bar chart: which synonyms got most hits
4. **NEW**: System logs usage → updates `usage_count` in DB
5. **NEW**: Low-performing synonyms flagged for review

**UI Mock (Web Lookup Report)**:
```
┌─────────────────────────────────────────────────────────────┐
│ 📊 Web Lookup Rapport                                       │
│                                                              │
│ Term: verdachte                                              │
│                                                              │
│ Synoniemen gebruikt:                                         │
│ ✓ beklaagde      → 8 resultaten  ████████                  │
│ ✓ beschuldigde   → 3 resultaten  ███                        │
│ ✗ aangeklaagde   → 0 resultaten                             │
│                                                              │
│ Aanbeveling: "aangeklaagde" niet effectief, overweeg       │
│              verwijderen of vervangen                        │
│                                                              │
│ [Review Synoniem] [Dismiss]                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## UI/UX Recommendations

### Screen Structure (Revised)

#### 1. Definition Generator Tab (Enhanced)
**Current**: Simple form with term input + context selector + generate button
**New**: Add inline synonym management

**Components to Add**:
- **Synonym Indicator**: Shows "X synoniemen gevonden" below term input
- **Synonym Preview**: Expandable list of available synonyms with confidence
- **Inline Approval**: Popup for new AI suggestions (no navigation required)
- **Web Lookup Report**: Collapsible panel showing synonym usage after generation

**Wireframe**:
```
┌─────────────────────────────────────────────────────────────┐
│ [Genereer Definitie Tab]                                    │
│                                                              │
│ Term: ________________  [Context: ▼]  [Genereer]           │
│ 💡 3 synoniemen | [Bekijk] [Genereer meer]                 │
│                                                              │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ 📋 Definitie Resultaat                                   ││
│ │ ...                                                      ││
│ └─────────────────────────────────────────────────────────┘│
│                                                              │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ 📊 Web Lookup Rapport                                    ││
│ │ [Expand ▼]                                               ││
│ └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

#### 2. Synonym Review Tab (Streamlined)
**Current**: Standalone page `/synonym_review` with generate + approve workflow
**New**: Focus on bulk operations + analytics (keep for power users)

**Keep**:
- ✅ Statistics panel (total, pending, approval rate)
- ✅ Filters (status, confidence threshold)
- ✅ Bulk approve/reject with confirmation
- ✅ Revert functionality

**Add**:
- **Usage Analytics**: "Top 10 most-used synonyms"
- **Low-performing Synonyms**: "5 synoniemen met 0 hits in laatste 30 dagen"
- **Auto-Review Queue**: "12 high-confidence suggestions (>0.9) klaar voor auto-approve"
- **YAML Sync Status**: "Laatste sync: 2 min geleden | 3 pending changes"

**Wireframe**:
```
┌─────────────────────────────────────────────────────────────┐
│ [Synonym Review & Management Tab]                           │
│                                                              │
│ ┌──────┬──────┬──────┬──────┬──────────┐                  │
│ │ 📊 50│ ⏳ 12│ ✅ 35│ ❌ 3 │ 🔄 Sync  │                  │
│ │ Total│Pndng│Aprved│Rjctd │ 2m ago   │                  │
│ └──────┴──────┴──────┴──────┴──────────┘                  │
│                                                              │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ 💡 12 high-confidence suggestions ready                  ││
│ │ [Auto-Approve All >0.9] [Review Manually]               ││
│ └─────────────────────────────────────────────────────────┘│
│                                                              │
│ Filters: [Status ▼] [Min Conf: ━━━━●━━] [Term: ____]     │
│                                                              │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ 📋 Pending Suggestions (12)                              ││
│ │ [Bulk Actions ▼]                                         ││
│ │ ...                                                      ││
│ └─────────────────────────────────────────────────────────┘│
│                                                              │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ 📊 Analytics                                             ││
│ │ [Expand ▼]                                               ││
│ └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

#### 3. Synonym Settings (New - Optional)
**Purpose**: Configure automation rules + view YAML health

**Features**:
- Auto-approve threshold slider (e.g., "Auto-approve if confidence > 0.95")
- YAML health report (duplicates, conflicts, unused synonyms)
- Import/Export (bulk YAML → DB sync)
- Hot reload toggle (enable/disable auto-sync without restart)

---

### Automation Recommendations

#### Where to Automate (High Priority)
1. **DB → YAML Sync**: On approve, auto-write to YAML (already implemented in `YAMLConfigUpdater`)
2. **Usage Tracking**: Log every synonym used in web lookup → update `usage_count`
3. **Low-performer Detection**: Weekly job flags synonyms with 0 hits in 30 days
4. **High-confidence Auto-approve**: Suggestions >0.95 confidence → auto-approve with notification
5. **Hot Reload**: Watch YAML file changes → reload `JuridischeSynoniemlService` without restart

#### Where to Keep Human Control (Critical)
1. **Final Approval**: Human must approve/reject AI suggestions (NO full automation)
2. **Conflict Resolution**: If synonym exists in different hoofdterm, require manual choice
3. **Rationale Override**: User can edit GPT-4 rationale before approval
4. **Bulk Operations**: Require explicit confirmation (no silent bulk actions)
5. **Revert Decisions**: User can undo approvals with reason

---

## Best of 3 Worlds: Integration Strategy

### What to Take from Each World

#### From World 1 (YAML) ✅
- **Weighted synonyms** (confidence-based ranking)
- **Bidirectional lookup** (term ↔ synonym)
- **Git version control** (audit trail)
- **Production usage** (already integrated in web lookup)

**Action**: Keep YAML as **generated artifact** (DB is source of truth)

---

#### From World 2 (Database + Workflow) ✅
- **AI generation** (scalable, context-aware)
- **Approval workflow** (human-in-the-loop quality gate)
- **Rationale transparency** (explain why synonym is good)
- **Bulk operations** (efficient review)
- **Revert functionality** (undo mistakes)

**Action**: Enhance with **usage analytics** and **inline approval**

---

#### From World 3 (Definition Examples) ✅
- **Context-aware usage** (synonym in natural sentence)
- **Quality validation** (good example = good synonym)
- **Real-world proof** (synonym actually used in legal text)

**Action**: Extract synonyms from examples → suggest as candidates

---

### Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE                            │
│  (Definition Generator + Synonym Review + Settings)          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                 SYNONYM WORKFLOW SERVICE                     │
│  (SynonymWorkflow - already exists, enhance with tracking)  │
└──────────┬───────────────┬──────────────┬───────────────────┘
           │               │              │
           ▼               ▼              ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ GPT4Suggester│  │ YAMLUpdater  │  │UsageTracker  │
│ (existing)   │  │ (existing)   │  │ (NEW)        │
└──────────────┘  └──────────────┘  └──────────────┘
           │               │              │
           ▼               ▼              ▼
┌─────────────────────────────────────────────────────────────┐
│              DATABASE (synonym_suggestions)                  │
│  Columns: id, hoofdterm, synoniem, confidence, rationale,   │
│           status, usage_count, last_used, context_data      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼ (auto-sync on approve)
┌─────────────────────────────────────────────────────────────┐
│           YAML FILE (juridische_synoniemen.yaml)            │
│  (Generated artifact, not manually edited)                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼ (used by)
┌─────────────────────────────────────────────────────────────┐
│        JuridischeSynoniemlService (web lookup)              │
│  (Already integrated in ModernWebLookupService)             │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1)
**Goal**: Establish DB as single source of truth

1. **Add `usage_count` + `last_used` columns to `synonym_suggestions`**
   - Migration: `ALTER TABLE synonym_suggestions ADD COLUMN usage_count INTEGER DEFAULT 0, last_used TIMESTAMP`
2. **Implement `UsageTracker` service**
   - Hook into `ModernWebLookupService.lookup()`
   - On synonym use → increment `usage_count`, update `last_used`
3. **Test auto-sync** (already implemented in `YAMLConfigUpdater`)
   - Verify approve → YAML update works correctly
   - Add rollback test (YAML corruption → restore from DB)

**Deliverable**: Database tracks synonym usage, YAML auto-syncs

---

### Phase 2: Inline UI (Week 2)
**Goal**: Surface synonyms in Definition Generator

1. **Add synonym indicator to Definition Generator tab**
   - Show "X synoniemen gevonden" below term input
   - Expandable list with confidence scores
2. **Implement inline approval dialog**
   - Component: `InlineSynonymApprovalDialog`
   - Trigger: "Genereer meer synoniemen" button
   - Actions: Approve/Reject/Edit/Later
3. **Add web lookup report panel**
   - Collapsible section after definition generation
   - Show synonym usage stats (hits per synonym)

**Deliverable**: User can manage synonyms without leaving Definition Generator

---

### Phase 3: Analytics & Automation (Week 3)
**Goal**: Proactive synonym management

1. **Add analytics to Synonym Review tab**
   - Top 10 most-used synonyms
   - Low-performers (0 hits in 30 days)
   - Approval rate trends
2. **Implement auto-approve for high-confidence**
   - Configurable threshold (default: 0.95)
   - Notification: "3 synoniemen auto-approved (conf >0.95)"
   - User can disable in settings
3. **Build YAML health checker**
   - Detect duplicates across hoofdtermen
   - Flag conflicts (same synonym → different hoofdterm)
   - Suggest cleanups

**Deliverable**: System proactively suggests improvements

---

### Phase 4: Context Integration (Week 4)
**Goal**: Extract synonyms from definition examples

1. **Implement example parser**
   - NLP: Extract parenthetical synonyms: "verdachte (beklaagde)"
   - Pattern: `term (synonym)` or `synonym (term)`
2. **Suggest synonyms from examples**
   - After saving definition with examples
   - Notification: "2 synoniemen gevonden in voorbeelden, toevoegen?"
3. **Bidirectional link**
   - Show "Gebruikt in 3 definities" in Synonym Review tab
   - Click → view definitions using this synonym

**Deliverable**: Examples become synonym source

---

## Success Metrics

### User Experience (UX)
- ✅ **Time to add synonym**: 2 min (manual YAML) → 10 sec (inline approval)
- ✅ **Actions to approve synonym**: 7 steps → 1 click
- ✅ **Restart required**: YES (current) → NO (hot reload)
- ✅ **Visibility into usage**: NONE → Full analytics

### Quality Metrics
- ✅ **Precision maintained**: >90% (human approval required)
- ✅ **Coverage increase**: 50 terms → 150+ terms (200% growth)
- ✅ **Low-performer detection**: Manual → Automated weekly report
- ✅ **YAML health**: No duplicates/conflicts (automated checker)

### Maintenance Burden
- ✅ **Weekly maintenance time**: 2h → 30 min (75% reduction)
- ✅ **Manual YAML edits**: Daily → Never (DB is source)
- ✅ **Sync errors**: 10% failure rate → <1% (automated rollback)

---

## Risk Mitigation

### Risk 1: Auto-Sync YAML Corruption
**Mitigation**:
- Git version control (rollback to previous YAML)
- YAML validator before write (syntax check)
- Backup before sync (copy to `juridische_synoniemen.yaml.bak`)
- Test coverage for `YAMLConfigUpdater` (already exists)

### Risk 2: High-Confidence Auto-Approve Errors
**Mitigation**:
- User can disable auto-approve in settings
- Notification shows what was auto-approved
- Easy revert (1-click undo)
- Weekly report: "Review 5 auto-approved synonyms"

### Risk 3: Usage Tracking Performance Impact
**Mitigation**:
- Async logging (no blocking web lookup)
- Batch updates (update DB every 10 uses, not every use)
- Index `usage_count` + `last_used` columns
- Monitor query performance

### Risk 4: User Overwhelm (Too Many Features)
**Mitigation**:
- **Phase rollout**: Ship Phase 1 → 2 → 3 → 4 (not all at once)
- **Progressive disclosure**: Hide analytics behind "Advanced" tab
- **Smart defaults**: Auto-approve threshold 0.95 (conservative)
- **Onboarding**: "New synonym features!" popup with quick tour

---

## Decision Matrix: What to Build First?

| Feature | Impact | Effort | Priority |
|---------|--------|--------|----------|
| **DB → YAML Auto-Sync** | 🔥🔥🔥 | Low (exists) | **P0** (Phase 1) |
| **Usage Tracking** | 🔥🔥🔥 | Medium | **P0** (Phase 1) |
| **Inline Approval Dialog** | 🔥🔥 | Medium | **P1** (Phase 2) |
| **Web Lookup Report** | 🔥🔥 | Low | **P1** (Phase 2) |
| **Analytics Dashboard** | 🔥 | Medium | **P2** (Phase 3) |
| **Auto-Approve High-Conf** | 🔥 | Low | **P2** (Phase 3) |
| **Example Parser** | 🔥 | High | **P3** (Phase 4) |

**Recommendation**: Start with **Phase 1 + Phase 2** for maximum UX impact with minimal risk.

---

## Conclusion: The "Best of 3 Worlds"

### World 1 (YAML) → **Generated Artifact**
- Keep for git history and production use
- Never manually edit (DB is source)
- Auto-sync on approve

### World 2 (Database + Workflow) → **Single Source of Truth**
- All synonyms live here
- Enhanced with usage analytics
- Inline approval for minimal friction

### World 3 (Examples) → **Quality Signal + Data Source**
- Extract synonyms from examples (Phase 4)
- Use as validation: "Synonym used in 5 definitions = high quality"
- Bidirectional link for transparency

**Result**: User gets scalable AI generation (World 2), high quality curation (World 1), and real-world validation (World 3) in a **unified, frictionless workflow**.

---

## Next Steps

1. **Stakeholder Review**: Product Owner approval on phased roadmap
2. **Technical Spike**: Validate usage tracking performance impact (1 day)
3. **Design Review**: Wireframes for inline approval dialog (2 days)
4. **Phase 1 Kickoff**: Implement DB enhancements + auto-sync (Week 1)

**Questions?** Contact Product Manager for clarification or prioritization adjustments.
