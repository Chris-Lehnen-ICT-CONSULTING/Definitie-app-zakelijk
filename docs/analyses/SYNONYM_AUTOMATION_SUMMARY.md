# Automated Synonym Suggestion - Executive Summary

**Datum**: 8 oktober 2025
**Status**: Research Complete - Awaiting Approval
**Volledige analyse**: `docs/analyses/SYNONYM_AUTOMATION_ANALYSIS.md`

---

## Problem Statement

Huidige synoniemen database (50 termen, 184 synoniemen) is handmatig gecureerd en schaalt niet. Doel: automatiseer synonym suggestie voor 150+ juridische termen met behoud van kwaliteit.

---

## Recommended Solution: GPT-4 Suggest + Human Approve

### Why This Approach?

✅ **Beste balans** tussen kwaliteit (90-95% precision), schaalbaarheid (150+ termen) en onderhoudsbaarheid (30 min/week)
✅ **Context-aware** - gebruikt bestaande database definities voor betere suggesties
✅ **Zeer kostenefficiënt** - $3 one-time, $0.30/maand ongoing
✅ **Human-in-the-loop** - voorkomt GPT-4 hallucinations
✅ **Feedback loop** - rejected suggestions verbeteren volgende suggesties
✅ **Hergebruikt bestaande code** - AIServiceV2 reeds in project

### How It Works

```
1. GPT-4 genereert 5-8 synonym candidates per term (met confidence + rationale)
   ↓
2. Suggestions opgeslagen in database (status: pending)
   ↓
3. Curator reviewed in Streamlit UI (approve/reject/edit)
   ↓
4. Approved synoniemen → auto-update juridische_synoniemen.yaml
   ↓
5. Rejected synoniemen → feedback voor prompt improvement
```

### Expected Impact

| Metric | Current | After | Delta |
|--------|---------|-------|-------|
| Unieke termen | 50 | 150+ | **+200%** |
| Totaal synoniemen | 184 | 450+ | **+145%** |
| Coverage (web lookup) | 80% | 90%+ | **+10%** |
| Precision | 95% (manual) | 90-95% (GPT-4) | **Maintained** |
| Maintenance time | 2h/week | 30min/week | **-75%** |

### Cost Analysis

**One-time Setup**:
- 200 terms × $0.015 per term = **$3.00**

**Ongoing Maintenance**:
- 20 nieuwe termen/maand × $0.015 = **$0.30/maand**

**Total Year 1**: $3.00 + (12 × $0.30) = **$6.60**

**Extremely cost-efficient!**

---

## Alternative Approaches Considered

### 1. Wikipedia Redirects Mining
- **Pros**: Free, high precision (85-90%), quick win
- **Cons**: Limited coverage (only terms with Wikipedia page)
- **Verdict**: ✅ **Implement as Quick Win** (Week 1-2, +30-40 synoniemen)

### 2. Open Dutch WordNet
- **Pros**: Large dataset (117K synsets), free
- **Cons**: Not juridical-specific, low precision (60-70%)
- **Verdict**: ❌ Supplementary only

### 3. Wiktionary + EUROVOC Thesaurus
- **Pros**: Juridical-specific (EUROVOC), high quality
- **Cons**: Very complex implementation (8-12 days), EUROVOC focus on EU law
- **Verdict**: ❌ Too complex for current scope

### 4. Database Mining + Embeddings
- **Pros**: Reuses existing data, context-aware, cheap
- **Cons**: Limited to database terms (66), needs critical mass
- **Verdict**: ✅ **Use for quality validation** (Week 5-6)

---

## Implementation Roadmap

### Phase 1: Quick Win (Week 1-2)
**Wikipedia Redirects Extraction**
- Implement `WikipediaSynonymExtractor`
- Batch process 50 existing terms
- Export to pending suggestions
- **Deliverable**: +30-40 synoniemen

### Phase 2: Scaling (Week 3-4)
**GPT-4 Suggest + Approve Workflow**
- Implement `GPT4SynonymSuggester` service
- Database schema update (`synonym_suggestions` tabel)
- Streamlit review UI
- Batch processing for all database terms
- YAML auto-update on approval
- **Deliverable**: +100-150 synoniemen (pending review)

### Phase 3: Quality Assurance (Week 5-6)
**Database Mining + Validation**
- Implement embeddings-based similarity
- Consensus algorithm (definitie overlap + embeddings)
- Quality report generation
- Auto-detect missing synoniemen
- **Deliverable**: Quality report + 20-30 validated synoniemen

**Total Timeline**: 3-4 weeks (~15-18 days effort)

---

## Key Components

### 1. GPT-4 Prompt Template
```python
"""
Je bent een expert in Nederlands juridisch taalgebruik.
Genereer synoniemen voor: {term}

Context: {juridische_context}
Definitie: {definitie}

Vereisten:
- Juridisch correct
- Geschikt voor wetgeving.nl/rechtspraak.nl searches
- Formele + informele varianten
- Specifiek (geen algemene termen)

Output (JSON):
{
  "synoniemen": [
    {"term": "...", "confidence": 0.95, "rationale": "..."}
  ]
}
"""
```

### 2. Streamlit Review UI
- List pending suggestions
- Approve/Reject/Edit buttons
- Rationale display (explains why synonym suggested)
- Bulk operations (approve all high-confidence >0.9)
- Statistics dashboard

### 3. Database Schema
```sql
CREATE TABLE synonym_suggestions (
    id INTEGER PRIMARY KEY,
    hoofdterm TEXT NOT NULL,
    synoniem TEXT NOT NULL,
    confidence DECIMAL(3,2),
    rationale TEXT,
    status TEXT CHECK (status IN ('pending', 'approved', 'rejected')),
    reviewed_by TEXT,
    reviewed_at TIMESTAMP,
    rejection_reason TEXT
);
```

---

## Success Criteria

### Quality Gates
- ✅ Precision > 80% (approved / total suggested)
- ✅ Curator review time < 30 sec per suggestion
- ✅ Coverage improvement: 80% → 90%
- ✅ Manual audit: 20 random suggestions validated

### Monitoring Metrics
- Weekly precision tracking
- Monthly coverage reports
- Quarterly feedback loop (rejected → prompt improvement)

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| GPT-4 hallucinations | Human approval required, low temp (0.3), confidence scoring |
| Maintenance burden | Bulk operations, high-confidence auto-approve (>0.95) |
| YAML corruption | Automated backup, validation, version control |
| API cost overruns | Batch limits (50/day), cost monitoring, caching |

---

## Next Steps

### Immediate (This Week)
1. **Stakeholder review** - Approve strategy + budget ($5)
2. **Prototype** (Day 1-2) - Test GPT-4 prompt with 5 sample terms
3. **Decision point** (Day 3) - GO/NO-GO based on prototype

### Implementation (Week 1-6)
1. **Week 1-2**: Wikipedia Redirects (Quick Win)
2. **Week 3-4**: GPT-4 Suggest + Approve (Primary)
3. **Week 5-6**: Database Mining (Validation)

---

## Comparison Matrix

| Approach | Coverage | Precision | Cost | Complexity | Maintenance | Recommended |
|----------|----------|-----------|------|------------|-------------|-------------|
| **Wikipedia Redirects** | ⭐⭐⭐ | ⭐⭐⭐⭐ | FREE | Low (3-5d) | Low | ✅ Quick Win |
| **GPT-4 Suggest + Approve** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | $3-7 | Medium (5-8d) | Medium | ✅ **PRIMARY** |
| **Open Dutch WordNet** | ⭐⭐ | ⭐⭐ | FREE | Low (3-4d) | Very Low | ❌ Supplementary |
| **Wiktionary + EUROVOC** | ⭐⭐⭐ | ⭐⭐⭐⭐ | FREE | Very High (8-12d) | Low | ❌ Too complex |
| **Database Mining** | ⭐⭐ | ⭐⭐⭐ | <$1 | Medium (4-6d) | Low | ✅ Validation |

---

## Conclusion

**Recommended**: Hybride strategie met **GPT-4 Suggest + Human Approve** als primary approach, gevolgd door **Wikipedia Redirects** als quick win en **Database Mining** voor quality assurance.

**Expected ROI**:
- 200% meer synoniemen (50 → 150 termen)
- 75% minder onderhoud (2h → 30min/week)
- 10% hogere web lookup coverage (80% → 90%)
- Total cost: $6.60 per jaar

**Effort**: 15-18 dagen over 3-4 weken

---

**Status**: ✅ Ready for stakeholder review
**Full Analysis**: `docs/analyses/SYNONYM_AUTOMATION_ANALYSIS.md`
**Contact**: DefinitieAgent Development Team
