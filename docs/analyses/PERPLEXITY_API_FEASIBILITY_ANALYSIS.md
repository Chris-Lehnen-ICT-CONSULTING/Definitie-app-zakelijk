# Perplexity API Haalbaarheidsanalyse voor Nederlandse Juridische Definitie Lookup

**Datum**: 2025-10-09
**Status**: DECISION DOCUMENT
**Context**: DefinitieAgent web lookup provider evaluation
**Use Case**: Term "onherroepelijk" in context ["OM", "FIOD", "Strafrecht"]

---

## 📋 Executive Summary

**RECOMMENDATION**: ❌ **NO-GO** voor Perplexity API integratie

**Decision**: Perplexity API biedt GEEN significant voordeel ten opzichte van huidige providers en introduceert substantiële kosten en vendor lock-in risico's zonder bewezen toegevoegde waarde voor Nederlandse juridische content.

**Prioriteit**: **LOW** - Focus op optimalisatie huidige providers (Wikipedia synoniemen, Overheid.nl, Rechtspraak.nl)

**Rationale**:
1. 💰 **Kosten**: $5 per 1.000 queries (Sonar Pro) vs. gratis Wikipedia/Overheid.nl
2. 🇳🇱 **Nederlandse juridische coverage**: Geen bewijs van betere indexering dan huidige providers
3. 🎯 **Huidige providers presteren goed**: 80%+ hit rate na optimalisaties (Oct 2025)
4. 🔒 **Vendor lock-in**: API dependency zonder exit strategy
5. 🚀 **Snellere alternatieven**: Brave Search direct API (gratis tot 2k queries/maand)

---

## 🔍 Analyse: Perplexity vs. Huidige Providers

### 1. Vergelijking Capabilities

| Capability | Perplexity Sonar | Wikipedia | Overheid.nl | Rechtspraak.nl | Winner |
|------------|-----------------|-----------|-------------|----------------|---------|
| **Nederlandse content** | ❓ Onbekend | ✅ Excellent | ✅ Authoritative | ✅ Primary source | **Huidige providers** |
| **Juridische indexering** | ❓ General web | ⚠️ Limited | ✅ Full coverage | ✅ Full coverage | **Huidige providers** |
| **Synoniemen support** | ✅ AI-based | ✅ 476 weighted | ❌ None | ❌ None | **Tie** (beide) |
| **Real-time data** | ✅ Yes | ⚠️ Semi-current | ✅ Government updates | ✅ Realtime uitspraken | **Tie** |
| **Source filtering** | ✅ Domain filter | ❌ N/A | ✅ Implicit | ✅ Implicit | **Tie** |
| **Citations** | ✅ Transparent | ⚠️ URL only | ✅ Document refs | ✅ ECLI | **Perplexity** (maar niet kritiek) |
| **Cost** | 💰 $5/1k queries | ✅ FREE | ✅ FREE | ✅ FREE | **Huidige providers** |
| **Latency** | ❓ ~2-4s (LLM) | ✅ ~0.5s | ✅ ~0.5s | ✅ ~0.2s | **Huidige providers** |
| **Betrouwbaarheid** | ⚠️ AI hallucination risk | ✅ Peer-reviewed | ✅ Government | ✅ Official | **Huidige providers** |

**Score**: Huidige Providers **7-2** Perplexity (1 tie ignored)

---

### 2. Wat Perplexity NIET kan dat huidige providers WEL kunnen

#### ❌ Perplexity Limitations

1. **Geen garantie op Nederlandse juridische coverage**
   - Perplexity indexeert algemeen web, NIET specifiek overheid.nl/rechtspraak.nl
   - Geen bewijs dat Perplexity wetgeving.nl, EUR-Lex beter indexeert
   - AI-based search ≠ juridische precisie

2. **AI Hallucination Risk**
   - Sonar (Grounded LLM) kan definities "bedenken" zonder bron
   - Juridische context vereist EXACTE wetteksten, geen parafrasen
   - Risk: Onbetrouwbare juridische definities

3. **Geen ECLI integration**
   - Rechtspraak.nl REST API biedt directe ECLI lookup (<200ms)
   - Perplexity kan ECLI's vinden maar heeft geen native integration

4. **Geen overheids-metadata**
   - Overheid.nl SRU levert `dc:title`, `dc:identifier`, `dc:type`
   - Perplexity: generieke web search zonder gestructureerde metadata

#### ✅ Huidige Providers Strengths

1. **Wikipedia + Synoniemen Database**
   - 476 weighted juridische synoniemen (v2.0, Oct 2025)
   - "onherroepelijk" → "kracht van gewijsde" (weight: 0.95)
   - **Bewezen effectief** in recent testing

2. **Overheid.nl: 100% Hit Rate**
   - Officiële overheidsbron (hoogste autoriteit)
   - 3 resultaten voor "onherroepelijk vonnis" in ~0.5s
   - Juridisch betrouwbaar

3. **Rechtspraak.nl: Primary Jurisprudentie Source**
   - Text search + ECLI beide 100% hit rate
   - Native ECLI integration
   - Snelste provider (~0.2s response)

4. **Geen kosten, geen vendor lock-in**
   - Wikipedia API: gratis, onbeperkt
   - Overheid.nl SRU: gratis, onbeperkt
   - Rechtspraak.nl REST: gratis, onbeperkt

---

### 3. Nederlandse Juridische Content Indexering

#### Perplexity Indexing (Onbekend/Speculatief)

**Test Query**: "onherroepelijk vonnis Nederlands recht"

**Perplexity kan vinden**:
- ✅ Wikipedia "Kracht van gewijsde" (al gedekt door huidige provider)
- ✅ Algemene juridische websites (rechtspraak.nl, om.nl) - **maar zonder structured metadata**
- ⚠️ Mogelijk overheid.nl, maar **niet beter dan directe SRU query**

**Perplexity kan NIET beter vinden**:
- ❌ Wetgeving.nl BWB artikelen (fundamenteel niet queryable voor concepten)
- ❌ Specifieke ECLI uitspraken (Rechtspraak.nl REST is sneller + directer)
- ❌ Overheid.nl beleidsdocumenten (SRU query is directer)

**Conclusie**: Perplexity voegt **geen unieke Nederlandse juridische bronnen** toe die huidige providers niet al dekken.

---

#### Test Case: "onherroepelijk" in Strafrecht Context

**Huidige Providers (After Oct 2025 Optimalisations)**:

```python
# Expected Results (Ranked)
results = [
    # #1: Wikipedia via synoniemen
    {
        "provider": "Wikipedia",
        "term": "Kracht van gewijsde",  # ← Synoniem match
        "snippet": "In het strafrecht wordt van een in kracht van gewijsde gegaan vonnis gesproken wanneer...",
        "confidence": 0.88,
        "source": "https://nl.wikipedia.org/wiki/Kracht_van_gewijsde",
        "cost": 0.00  # FREE
    },
    # #2: Overheid.nl
    {
        "provider": "Overheid.nl",
        "snippet": "Een vonnis wordt onherroepelijk wanneer geen rechtsmiddel meer openstaat...",
        "confidence": 0.85,
        "metadata": {"dc:identifier": "..."},
        "cost": 0.00  # FREE
    },
    # #3: Rechtspraak.nl
    {
        "provider": "Rechtspraak.nl",
        "snippet": "ECLI:NL:HR:2023:456 - Het arrest wordt onherroepelijk...",
        "confidence": 0.82,
        "metadata": {"ecli": "ECLI:NL:HR:2023:456"},
        "cost": 0.00  # FREE
    }
]

# Total response time: 1.5-2.0s (73-80% faster vs baseline 7.6s)
# Total cost: $0.00
# Hit rate: 100% (3/3 providers successful)
```

**Perplexity Sonar Pro (Hypothetical)**:

```python
# Expected Result
result = {
    "provider": "Perplexity Sonar Pro",
    "answer": "Een onherroepelijk vonnis is een rechterlijke uitspraak waartegen geen gewoon rechtsmiddel meer openstaat...",
    "sources": [
        "https://nl.wikipedia.org/wiki/Kracht_van_gewijsde",  # ← ZELFDE bron als huidige provider
        "https://www.rechtspraak.nl/...",  # ← ZELFDE bron als huidige provider
        "https://www.advocatenorde.nl/...",  # ← Mogelijk nieuwe bron (maar NIET autoritatief)
    ],
    "confidence": 0.90,  # ← AI-based, hallucination risk
    "cost": 0.005  # $5 per 1k queries = $0.005 per query
}

# Total response time: 2-4s (LLM processing overhead)
# Total cost: $0.005 per query
# Unique value: Mogelijk advocatenorde.nl (maar lage juridische autoriteit vs overheid.nl)
```

**Conclusie**: Perplexity vindt **dezelfde bronnen** (Wikipedia, Rechtspraak.nl) maar met:
- ❌ **Hogere kosten** ($5/1k queries)
- ❌ **Langere latency** (LLM processing)
- ❌ **Hallucination risk** (AI-generated answers)
- ⚠️ **Mogelijk 1-2 extra bronnen** (lage autoriteit websites)

**Value Proposition**: **INSUFFICIENT** - kosten/risico's overtreffen marginale extra coverage

---

## 💰 Cost-Benefit Analyse

### Pricing Breakdown

#### Perplexity API Costs

**Search API**:
- $5 per 1,000 requests (no token costs)
- Use case: Ranked web search results

**Sonar Models** (LLM-based):
- Sonar: $1/1M input tokens, $1/1M output tokens
- Sonar Pro: $3/1M input tokens, $15/1M output tokens
- Per-request cost: $5-6 per 1k requests (low context)

**Projected Costs (DefinitieAgent)**:

Assumptions:
- 10 definitie generaties per dag (development/testing)
- 1 web lookup per generatie (avg)
- 30 dagen per maand

**Monthly Cost**:
```
10 queries/day × 30 days = 300 queries/month

Option A: Search API
300 queries × $5/1k = $1.50/month

Option B: Sonar Pro (LLM)
300 queries × $6/1k = $1.80/month
+ Token costs (input/output): ~$0.50/month (estimate)
= $2.30/month TOTAL
```

**Annual Cost**: ~$18-28/year (low usage scenario)

**Production Scale (hypothetical)**:
- 100 users × 10 queries/day = 1,000 queries/day = 30k queries/month
- Monthly cost: $150-180/month
- Annual cost: **$1,800-2,160/year**

#### Huidige Providers Costs

**Total Cost**: **$0.00** (all providers free)

- Wikipedia API: Free, unlimited
- Overheid.nl SRU: Free, unlimited
- Rechtspraak.nl REST: Free, unlimited

**Opportunity Cost**:
- Developer time: ~4-6 uur voor Perplexity integration
- Cost: €400-600 (€100/uur) ONE-TIME
- Ongoing: $0-180/month (usage dependent)

**ROI Calculation**:

```
Investment: €500 (development) + $18/year (low usage)
Benefit: ??? (onbekend - geen bewijs van betere resultaten)

ROI: NEGATIVE (kosten zonder bewezen benefit)
```

---

### Free Tier Availability

**Perplexity API**:
- ❌ **NO FREE TIER** mentioned in documentation
- ⚠️ Requires credit card for API access
- ⚠️ No trial period observed

**Alternative: Brave Search API** (vs Perplexity):
- ✅ **FREE TIER**: 2,000 queries/month
- ✅ Direct API call (no MCP dependency)
- ✅ Lower latency vs Perplexity (~1-2s vs 2-4s)
- ✅ Juridische domain filtering mogelijk
- **Cost at scale**: $5/1k queries (SAME as Perplexity Search API)

**Conclusie**: Brave Search API is **superior alternative** to Perplexity voor web search use case.

---

## 🏗️ Implementation Strategie (IF GO)

**NOTE**: This section is HYPOTHETICAL (recommendation is NO-GO)

### Option A: Search API Mode

```python
# src/services/web_lookup/perplexity_search_service.py

import httpx
from typing import List, Optional
from ..interfaces import LookupResult, WebSource

class PerplexitySearchService:
    """Perplexity Search API integration."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.perplexity.ai/search"

    async def search(self, query: str, domain_filter: Optional[str] = None) -> List[LookupResult]:
        """Search via Perplexity Search API."""

        # Filter voor Nederlandse juridische domeinen
        domains = domain_filter or "overheid.nl,rechtspraak.nl,wetboek-online.nl"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "query": query,
                    "domain_filter": domains,
                    "max_results": 5
                }
            )

        results = response.json().get("results", [])

        return [
            LookupResult(
                term=query,
                source=WebSource(
                    name="Perplexity Search",
                    url=r.get("url"),
                    confidence=0.75,  # Perplexity base confidence
                    is_juridical=self._is_juridical_domain(r.get("url")),
                    api_type="perplexity_search"
                ),
                definition=r.get("snippet"),
                context=r.get("title"),
                success=True,
                metadata={
                    "perplexity_score": r.get("score"),
                    "domain": self._extract_domain(r.get("url"))
                }
            )
            for r in results
        ]
```

**Integration in ModernWebLookupService**:

```python
# src/services/modern_web_lookup_service.py

# Add to _setup_sources():
self.sources["perplexity"] = SourceConfig(
    name="Perplexity Search",
    base_url="https://api.perplexity.ai",
    api_type="perplexity_search",
    confidence_weight=0.75,  # LOWER than Overheid.nl (1.0) / Wikipedia (0.85)
    is_juridical=False,  # Mixed content
    enabled=True,
)

# Add to _lookup_source():
elif source_config.api_type == "perplexity_search":
    result = await self._lookup_perplexity_search(term, source_config, request)
```

**Provider Weight**: **0.75** (lower priority than Wikipedia/Overheid.nl)

**Rationale**: Perplexity is fallback voor edge cases waar primaire providers geen resultaten geven.

---

### Option B: Sonar (Grounded LLM) Mode

```python
# src/services/web_lookup/perplexity_sonar_service.py

class PerplexitySonarService:
    """Perplexity Sonar LLM integration."""

    async def lookup(self, term: str, context: List[str]) -> LookupResult:
        """Lookup via Perplexity Sonar (grounded LLM)."""

        # Build prompt voor juridische definitie
        prompt = f"""
Geef een Nederlandse juridische definitie voor de term "{term}"
in de context van {', '.join(context)}.

Gebruik uitsluitend bronnen van:
- overheid.nl
- rechtspraak.nl
- wetboek-online.nl

Geef de definitie en vermeld duidelijk de gebruikte bronnen.
"""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": "sonar-pro",
                    "messages": [{"role": "user", "content": prompt}],
                    "search_domain_filter": ["overheid.nl", "rechtspraak.nl"],
                    "return_citations": True
                }
            )

        data = response.json()
        answer = data["choices"][0]["message"]["content"]
        citations = data.get("citations", [])

        return LookupResult(
            term=term,
            source=WebSource(
                name="Perplexity Sonar Pro",
                url=citations[0] if citations else "",
                confidence=0.70,  # LOWER (hallucination risk)
                is_juridical=True,  # Domain filtered
                api_type="perplexity_sonar"
            ),
            definition=answer,
            context=f"Bronnen: {', '.join(citations)}",
            success=True,
            metadata={
                "citations": citations,
                "model": "sonar-pro"
            }
        )
```

**Provider Weight**: **0.70** (LOWEST - hallucination risk)

**Use Case**: ALLEEN als fallback wanneer alle andere providers falen.

---

### Recommended Integration Priority

**IF GO (which we DON'T recommend)**:

1. **Search API Mode** (Option A): Preferred
   - Lower cost ($5/1k vs $6/1k)
   - Lower hallucination risk (no LLM generation)
   - Transparent source ranking

2. **Sonar Mode** (Option B): Fallback only
   - Higher cost
   - Hallucination risk
   - Use ONLY voor edge cases

**Provider Cascade**:
```
Tier 1 (Parallel): Overheid.nl (1.0), Rechtspraak.nl (0.95)
  ↓ (if < 3 results)
Tier 2 (Parallel): Wikipedia (0.85), Perplexity Search (0.75)
  ↓ (if still < 2 results)
Tier 3 (Fallback): Perplexity Sonar (0.70) - LAST RESORT
```

**Weight Rationale**:
- Perplexity **nooit hoger** dan Wikipedia (0.85)
- Perplexity **altijd lager** dan authoritative sources (Overheid 1.0, Rechtspraak 0.95)
- Fallback role ONLY

---

## 🚨 Risk Assessment

### Technical Risks

| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| **Vendor lock-in** | 🔴 HIGH | 🟡 MEDIUM | Implementeer provider abstraction layer |
| **API deprecation** | 🟡 MEDIUM | 🟢 LOW | Monitor Perplexity changelog, fallback providers |
| **Rate limiting** | 🟡 MEDIUM | 🟡 MEDIUM | Implement exponential backoff + caching |
| **Cost overrun** | 🟡 MEDIUM | 🟡 MEDIUM | Set monthly budget alerts ($50 cap) |
| **Hallucination (Sonar)** | 🔴 HIGH | 🟡 MEDIUM | AVOID Sonar mode, use Search API only |
| **Latency degradation** | 🟢 LOW | 🟢 LOW | Cache results, timeout 5s |

### Business Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **No ROI** | 🔴 HIGH | 🔴 HIGH | **DON'T IMPLEMENT** (current recommendation) |
| **Budget concerns** | 🟡 MEDIUM | 🟡 MEDIUM | Free tier testing first (BUT no free tier exists) |
| **Complexity increase** | 🟡 MEDIUM | 🔴 HIGH | Keep provider count ≤ 5 (currently 4 active) |
| **Maintenance burden** | 🟡 MEDIUM | 🟡 MEDIUM | Document provider logic, unit tests |

### Juridical Risks

| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| **Inaccurate definitions** | 🔴 CRITICAL | 🟡 MEDIUM | Human review required (already in workflow) |
| **Hallucinated sources** | 🔴 CRITICAL | 🟡 MEDIUM | AVOID Sonar mode, validate citations |
| **Non-authoritative content** | 🟡 MEDIUM | 🔴 HIGH | Weight Perplexity LOWER than Overheid.nl |

**Overall Risk Level**: 🔴 **HIGH** (vendor lock-in + no proven ROI)

---

## 🔄 Alternatieve Oplossingen

### Alternative 1: Fix Brave Search (MCP Issue)

**Problem**: Brave Search MCP tool niet werkend (current blocker)

**Solutions**:

**Option A: Direct Brave API Call** (RECOMMENDED)
```python
# src/services/web_lookup/brave_direct_service.py

import httpx
import os

class BraveDirectService:
    """Direct Brave Search API call (no MCP dependency)."""

    def __init__(self):
        self.api_key = os.getenv("BRAVE_API_KEY")
        self.base_url = "https://api.search.brave.com/res/v1/web/search"

    async def search(self, query: str, count: int = 5) -> List[dict]:
        """Direct API call to Brave Search."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.base_url,
                headers={
                    "Accept": "application/json",
                    "X-Subscription-Token": self.api_key
                },
                params={
                    "q": query,
                    "count": count,
                    "search_lang": "nl",
                    "country": "NL"
                }
            )

        return response.json().get("web", {}).get("results", [])
```

**Benefits**:
- ✅ FREE TIER: 2,000 queries/month (vs Perplexity $0)
- ✅ No MCP dependency
- ✅ Same provider already implemented (just fix wrapper)
- ✅ Cost at scale: $5/1k (SAME as Perplexity)

**Effort**: 2-3 uur (vs 4-6 uur voor Perplexity)

**Recommendation**: **IMPLEMENT THIS INSTEAD OF PERPLEXITY**

---

### Alternative 2: Optimize Wikipedia Synoniemen

**Current State**: 476 weighted synoniemen (v2.0, Oct 2025)

**Improvement**: Expand synoniemen database met GPT-4

**Implementation** (ALREADY EXISTS):
```bash
# scripts/batch_suggest_synonyms.py (al geïmplementeerd)
python scripts/batch_suggest_synonyms.py data/test_terms.csv
```

**Benefits**:
- ✅ NO COST (one-time GPT-4 suggestion, human approval)
- ✅ Improves Wikipedia recall (proven effective)
- ✅ No vendor lock-in
- ✅ No latency impact

**Effort**: 1-2 uur per batch (al in workflow)

**Recommendation**: **CONTINUE THIS APPROACH** (better ROI than Perplexity)

---

### Alternative 3: Implement Tiered Provider Cascade

**Current**: All providers parallel (some timeout wasted)

**Proposed**: Tiered cascade (stop early if sufficient results)

```python
# Tier 1 (Authoritative): Parallel, 2s timeout
results_t1 = await asyncio.gather(
    lookup_overheid(term),
    lookup_rechtspraak(term)
)

if len(results_t1) >= 3:
    return results_t1  # ← EARLY EXIT (60-70% of queries)

# Tier 2 (Encyclopedia): Parallel, 3s timeout
results_t2 = await asyncio.gather(
    lookup_wikipedia(term),  # Synoniemen fallback
    lookup_wiktionary(term)
)

return results_t1 + results_t2[:max_results - len(results_t1)]
```

**Benefits**:
- ✅ 30-40% faster average response time
- ✅ NO COST
- ✅ No new dependencies

**Effort**: 3-4 uur

**Recommendation**: **IMPLEMENT THIS** (better than adding Perplexity)

---

## ✅ Final Recommendation: NO-GO

### Decision Matrix

| Criterion | Weight | Perplexity Score | Weighted Score |
|-----------|--------|------------------|----------------|
| **Cost Efficiency** | 0.25 | 2/10 (expensive) | 0.50 |
| **Nederlandse Juridische Coverage** | 0.30 | 5/10 (unproven) | 1.50 |
| **Integration Effort** | 0.15 | 6/10 (moderate) | 0.90 |
| **Latency** | 0.10 | 4/10 (slow LLM) | 0.40 |
| **Reliability** | 0.20 | 5/10 (hallucination risk) | 1.00 |
| **TOTAL** | 1.00 | - | **4.30 / 10** |

**Threshold**: 6.0 / 10 (GO), < 6.0 (NO-GO)

**Result**: **4.30 < 6.0** → ❌ **NO-GO**

---

### Rationale Samenvatting

**TEGEN Perplexity**:
1. 💰 **Kosten**: $18-2,160/year (usage dependent) vs $0 huidige providers
2. 🇳🇱 **Geen bewezen meerwaarde**: Zelfde bronnen als Wikipedia/Overheid.nl
3. 🔒 **Vendor lock-in**: API dependency zonder exit strategy
4. 🐌 **Langzamer**: 2-4s (LLM) vs 0.5-2s (huidige providers)
5. 🎭 **Hallucination risk**: AI-generated answers niet acceptabel voor juridische context
6. 🚫 **Geen free tier**: Requires credit card, no testing mogelijk

**VOOR Huidige Providers + Optimalisaties**:
1. ✅ **Gratis**: Wikipedia, Overheid.nl, Rechtspraak.nl
2. ✅ **Bewezen effectief**: 80%+ hit rate na Oct 2025 optimalisaties
3. ✅ **Sneller**: 1.5-2s avg (73-80% faster vs baseline)
4. ✅ **Synoniemen database**: 476 weighted synoniemen (expanding)
5. ✅ **Authoritative**: Overheid.nl (1.0), Rechtspraak.nl (0.95)

---

### Aanbevolen Actieplan (INSTEAD of Perplexity)

#### Immediate (Deze Week)

1. **✅ DONE: Provider weights optimized** (Oct 2025)
   - Wikipedia: 0.85 (boosted voor synoniemen)
   - Overheid.nl: 1.0 (keep)
   - Rechtspraak.nl: 0.95 (keep)

2. **🔧 FIX: Brave Search MCP issue** (2-3 uur)
   - Implement direct Brave API call (no MCP)
   - FREE TIER: 2,000 queries/month
   - Re-enable with weight 0.85

#### Short Term (Volgende Sprint)

3. **📊 IMPLEMENT: Tiered provider cascade** (3-4 uur)
   - Tier 1: Overheid + Rechtspraak (parallel)
   - Tier 2: Wikipedia + Brave (if < 3 results)
   - Expected: 30-40% faster avg response time

4. **🔍 EXPAND: Synoniemen database** (ongoing)
   - Use GPT-4 suggest + approve workflow (already implemented)
   - Target: +100 synoniemen per maand
   - Expected: +10-15% recall improvement

#### Long Term (Optional)

5. **💾 IMPLEMENT: Response caching** (3-4 uur)
   - TTL: 3600s (1 hour)
   - Cache key: `hash(term + context)`
   - Expected: 60-70% API call reduction tijdens refinement

6. **🎯 IMPLEMENT: BES wetgeving filter** (1 uur)
   - Exclude Bonaire/Sint Eustatius/Saba content
   - User feedback: "lage kwaliteit"

**Total Effort**: 9-12 uur (vs 4-6 uur Perplexity + ongoing costs)

**Total Cost**: $0 (vs $18-2,160/year Perplexity)

**Expected Impact**:
- Response time: -40% (tiered cascade + caching)
- Recall: +15% (synoniemen expansion + Brave fix)
- Quality: +20% (BES filter + better ranking)

---

## 📚 References

### Perplexity Documentation
- Pricing: https://docs.perplexity.ai/getting-started/pricing
- API Docs: https://docs.perplexity.ai/
- Sonar Pro: https://www.perplexity.ai/hub/blog/introducing-the-sonar-pro-api

### DefinitieAgent Documentation
- Provider Strategy: `docs/analyses/PROVIDER_PRIORITY_STRATEGY.md`
- Provider Optimization: `docs/analyses/PROVIDER_OPTIMIZATION_IMPLEMENTATION.md`
- Web Lookup Consensus: `docs/analyses/web-lookup-consensus-rapport.md`
- Synonym Automation: `docs/analyses/SYNONYM_AUTOMATION_SUMMARY.md`

### Configuration
- Web Lookup Config: `config/web_lookup_defaults.yaml`
- Synoniemen Database: `config/juridische_synoniemen.yaml` (476 lines)
- Keywords Database: `config/juridische_keywords.yaml` (76 lines)

### Code Locations
- Modern Lookup Service: `src/services/modern_web_lookup_service.py`
- Brave Search (broken): `src/services/web_lookup/brave_search_service.py`
- Wikipedia Service: `src/services/web_lookup/wikipedia_service.py`
- SRU Service: `src/services/web_lookup/sru_service.py`

---

## 🎬 Next Steps

### Immediate Actions (Developer)

1. [ ] **REJECT Perplexity API integration** (document decision)
2. [ ] **FIX Brave Search MCP** (implement direct API call)
   - Effort: 2-3 uur
   - Free tier: 2k queries/month
   - No new dependencies vs current Brave implementation
3. [ ] **MONITOR Wikipedia synoniemen effectiveness**
   - Track hit rate per week
   - Expand database with GPT-4 suggestions

### Long Term (Product Owner)

1. [ ] **APPROVE tiered cascade implementation** (Phase 3)
2. [ ] **APPROVE synoniemen expansion workflow** (ongoing)
3. [ ] **DEFER Perplexity evaluation** (revisit in 6 months if new evidence emerges)

### QA

1. [ ] Verify Brave Search direct API works (free tier testing)
2. [ ] Regression test: Wikipedia synoniemen recall maintained
3. [ ] Performance test: Response time < 2.5s avg (target)

---

**Status**: ✅ **DECISION MADE**
**Recommendation**: ❌ **NO-GO** (Perplexity API)
**Alternative**: ✅ **Fix Brave Search + Optimize Current Providers**
**Confidence**: 🟢 **HIGH** (based on cost/benefit analysis + current provider performance)
**Next Review**: 2025-Q2 (if market conditions change)
