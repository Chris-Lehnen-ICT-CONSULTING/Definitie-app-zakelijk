# Perplexity API Decision Summary

**Date**: 2025-10-09
**Decision**: ❌ **NO-GO**
**Alternative**: ✅ Fix Brave Search + Optimize Current Providers

---

## TL;DR

**Question**: Should we integrate Perplexity API for Nederlandse juridische definitie lookup?

**Answer**: **NO** - Perplexity offers NO significant advantage over current providers (Wikipedia, Overheid.nl, Rechtspraak.nl) and introduces costs ($5-180/month) + vendor lock-in without proven ROI.

**Better Alternative**: Fix Brave Search direct API (FREE 2k queries/month) + expand Wikipedia synoniemen database.

---

## Decision Matrix

| Criterion | Weight | Perplexity | Current Providers | Winner |
|-----------|--------|-----------|-------------------|---------|
| Cost | 0.25 | 2/10 ($) | 10/10 (FREE) | **Current** |
| NL Juridisch | 0.30 | 5/10 (?) | 9/10 (proven) | **Current** |
| Integration | 0.15 | 6/10 | 10/10 (done) | **Current** |
| Latency | 0.10 | 4/10 (2-4s) | 9/10 (0.5-2s) | **Current** |
| Reliability | 0.20 | 5/10 (AI risk) | 9/10 (authoritative) | **Current** |
| **TOTAL** | 1.00 | **4.3/10** | **9.1/10** | **Current Providers** |

**Threshold**: 6.0/10 required for GO → **4.3 < 6.0** = NO-GO

---

## Key Findings

### What Perplexity CAN'T do better:

❌ **Nederlandse juridische indexering** - No proof of better coverage than Wikipedia/Overheid.nl
❌ **Authoritative sources** - Overheid.nl (1.0 weight) > Perplexity (0.75 max)
❌ **Cost** - $5/1k queries vs FREE current providers
❌ **Latency** - 2-4s (LLM) vs 0.5-2s (current)
❌ **ECLI integration** - Rechtspraak.nl REST is faster + native
❌ **Free tier** - None (requires credit card)

### What Current Providers DO better:

✅ **Wikipedia + 476 weighted synoniemen** - "onherroepelijk" → "kracht van gewijsde" (proven Oct 2025)
✅ **Overheid.nl 100% hit rate** - Official government source
✅ **Rechtspraak.nl 100% hit rate** - Primary jurisprudence source
✅ **No cost, no vendor lock-in**
✅ **73-80% faster** after Oct 2025 optimizations (7.6s → 1.5-2s)

---

## Cost Comparison

### Perplexity API

**Search API**: $5 per 1,000 requests
**Sonar Pro (LLM)**: $6 per 1,000 requests + token costs

**Projected Costs**:
- Development: 10 queries/day → **$1.50/month** ($18/year)
- Production (100 users): 1k queries/day → **$150/month** ($1,800/year)

### Current Providers

**Total Cost**: **$0.00**

- Wikipedia API: FREE, unlimited
- Overheid.nl SRU: FREE, unlimited
- Rechtspraak.nl REST: FREE, unlimited

**ROI**: **NEGATIVE** (costs without proven benefit)

---

## Recommended Action Plan

### INSTEAD of Perplexity → DO THIS:

#### 1. Fix Brave Search (2-3 hours) - PRIORITY 1

**Problem**: MCP tool not working
**Solution**: Direct Brave API call (no MCP dependency)

```python
# Direct API implementation (no MCP wrapper)
async def brave_direct_search(query: str):
    response = await httpx.get(
        "https://api.search.brave.com/res/v1/web/search",
        headers={"X-Subscription-Token": BRAVE_API_KEY},
        params={"q": query, "count": 5}
    )
    return response.json()
```

**Benefits**:
- ✅ FREE TIER: 2,000 queries/month
- ✅ Same cost at scale: $5/1k (identical to Perplexity)
- ✅ No vendor lock-in (already implemented, just fix wrapper)
- ✅ Lower latency vs Perplexity (~1-2s vs 2-4s)

**Effort**: 2-3 uur vs 4-6 uur Perplexity
**Cost**: $0 vs $18-2,160/year Perplexity

---

#### 2. Expand Wikipedia Synoniemen (ongoing)

**Current**: 476 weighted synoniemen (v2.0)
**Target**: +100 synoniemen/month via GPT-4 suggest + approve workflow

**Already Implemented**:
```bash
python scripts/batch_suggest_synonyms.py data/test_terms.csv
```

**Benefits**:
- ✅ Proven effective (Oct 2025): "onherroepelijk" → "kracht van gewijsde"
- ✅ No ongoing cost (one-time GPT-4, human approval)
- ✅ Better ROI than paid API

**Effort**: 1-2 uur/batch (already in workflow)

---

#### 3. Implement Tiered Cascade (3-4 hours)

**Current**: All providers parallel (some timeout wasted)
**Proposed**: Early exit if sufficient results

```python
# Tier 1 (Authoritative): 2s timeout
results = await parallel_lookup([overheid, rechtspraak])
if len(results) >= 3:
    return results  # ← 60-70% queries exit here

# Tier 2 (Encyclopedia): 3s timeout
results += await parallel_lookup([wikipedia, brave])
return results
```

**Expected Impact**: 30-40% faster avg response time

---

## Risk Assessment

### Perplexity Risks

| Risk | Severity | Likelihood |
|------|----------|------------|
| Vendor lock-in | 🔴 HIGH | 🟡 MEDIUM |
| No ROI | 🔴 HIGH | 🔴 HIGH |
| Hallucination (Sonar) | 🔴 CRITICAL | 🟡 MEDIUM |
| Cost overrun | 🟡 MEDIUM | 🟡 MEDIUM |

**Overall**: 🔴 **HIGH RISK** (vendor lock-in + unproven ROI)

### Alternative Risks

| Risk | Severity | Likelihood |
|------|----------|------------|
| Brave API change | 🟡 MEDIUM | 🟢 LOW |
| Synoniemen maintenance | 🟢 LOW | 🟡 MEDIUM |
| Tiered cascade complexity | 🟢 LOW | 🟢 LOW |

**Overall**: 🟢 **LOW RISK** (manageable, no vendor lock-in)

---

## Test Case: "onherroepelijk" in Strafrecht Context

### Perplexity (Hypothetical)

```json
{
  "provider": "Perplexity Sonar Pro",
  "answer": "Een onherroepelijk vonnis is...",
  "sources": [
    "https://nl.wikipedia.org/wiki/...",  // ← SAME as current
    "https://www.rechtspraak.nl/..."     // ← SAME as current
  ],
  "cost": "$0.005",
  "latency": "2-4s",
  "hallucination_risk": "MEDIUM"
}
```

### Current Providers (After Oct 2025 Optimizations)

```json
{
  "results": [
    {
      "provider": "Wikipedia",
      "term": "Kracht van gewijsde",  // ← Synoniemen match
      "confidence": 0.88,
      "source": "https://nl.wikipedia.org/wiki/..."
    },
    {
      "provider": "Overheid.nl",
      "confidence": 0.85,
      "metadata": {"dc:identifier": "..."}
    },
    {
      "provider": "Rechtspraak.nl",
      "confidence": 0.82,
      "metadata": {"ecli": "ECLI:NL:HR:2023:456"}
    }
  ],
  "cost": "$0.00",
  "latency": "1.5-2.0s",
  "hit_rate": "100%"
}
```

**Conclusion**: Current providers deliver **SAME or BETTER results** at **ZERO cost** and **faster latency**.

---

## Final Recommendation

### Decision: ❌ NO-GO (Perplexity API)

**Rationale**:
1. 💰 Costs $18-2,160/year vs $0 current providers
2. 🇳🇱 No proven advantage for NL juridische content
3. 🔒 Vendor lock-in without exit strategy
4. 🐌 Slower than current providers (2-4s vs 1.5-2s)
5. 🎭 Hallucination risk unacceptable for juridische context

### Alternative: ✅ Fix Brave + Optimize Current

**Priority Actions**:
1. Fix Brave Search direct API (2-3 uur, FREE 2k/month)
2. Expand synoniemen database (ongoing, proven ROI)
3. Implement tiered cascade (3-4 uur, 30-40% faster)

**Expected Results**:
- Response time: -40% (cascade + caching)
- Recall: +15% (synoniemen + Brave fix)
- Quality: +20% (better ranking + filters)
- Cost: **$0**

---

## References

- **Full Analysis**: `docs/analyses/PERPLEXITY_API_FEASIBILITY_ANALYSIS.md`
- **Provider Strategy**: `docs/analyses/PROVIDER_PRIORITY_STRATEGY.md`
- **Current Config**: `config/web_lookup_defaults.yaml`
- **Synoniemen Database**: `config/juridische_synoniemen.yaml` (476 lines)

---

**Status**: ✅ DECISION DOCUMENTED
**Next Review**: 2025-Q2 (if market conditions change)
**Confidence**: 🟢 HIGH (based on cost/benefit analysis + current performance)
