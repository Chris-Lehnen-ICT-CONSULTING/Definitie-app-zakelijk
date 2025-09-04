---
canonical: false
status: active
owner: development
last_verified: 2025-09-03
applies_to: definitie-app@v2.3
document_type: epic
epic: epic-7-performance-scaling
parent_doc: epic-7-performance-optimization
priority: critical
sprint: UAT-2025-09
---

# Epic 7: Prompt Optimization - Detailed Breakdown

**Epic Goal**: Reduceer prompt tokens van 7,250 naar 1,250 (83% reductie) voor betere performance en lagere kosten
**UAT Deadline**: 20 september 2025
**Geschatte Effort**: 3-4 dagen totaal
**Business Value**: €500-1000/maand besparing op API kosten + 50% snellere response tijd

---

## 🔴 Huidige Problemen

### Token Inefficiëntie
- **Huidige prompt**: 7,250 tokens (~29,000 karakters)
- **Duplicaties**: 40% van prompt is redundant
- **Tegenstrijdigheden**: 5+ conflicterende regels
- **Performance impact**: 8-12s response tijd
- **Kosten**: ~€0.15 per definitie generatie

### Concrete Issues
1. **42 "Start niet met..." regels** (525 tokens)
2. **3x ontologie uitleg** (600 tokens)
3. **Duplicate validatie regels** (800 tokens)
4. **Verbose regel beschrijvingen** (1,500 tokens)
5. **Onnodige voorbeelden** (1,000 tokens)

---

## 📊 Optimalisatie Strategie

### Target Architectuur
```
Oud: Monolithische prompt (7,250 tokens)
     ↓
Nieuw: Context-aware compositie (1,250 tokens)
     ├── Base prompt (500 tokens)
     ├── Context-specific rules (400 tokens)
     └── Relevant examples (350 tokens)
```

### Token Budget
| Component | Huidig | Target | Reductie |
|-----------|--------|---------|----------|
| Base instructions | 2,000 | 500 | 75% |
| Validation rules | 3,500 | 400 | 89% |
| Examples | 1,500 | 350 | 77% |
| Context | 250 | 0 | 100% |
| **TOTAAL** | **7,250** | **1,250** | **83%** |

---

## 🎯 User Stories

### Story PROMPT-4.1: Consolidate Duplicate Rules ⚡
**Als** systeem
**Wil ik** duplicate regels consolideren
**Zodat** de prompt efficiënter wordt

**Acceptance Criteria:**
- [ ] 42 "Start niet met..." → 5 regels
- [ ] ARAI-02 familie → 1 geconsolideerde regel
- [ ] ARAI-04 duplicaten → 1 regel
- [ ] Ontologie 3x uitleg → 1x compact
- [ ] Token reductie: 2,000+ tokens

**Implementation:**
```python
# In src/services/prompt_service_v2.py
def consolidate_rules():
    # Group similar rules
    # Remove redundancy
    # Create compact format
```

**Effort**: 3 points (1 dag)
**Priority**: P1 - Quick Win

---

### Story PROMPT-4.2: Fix Contradictions
**Als** AI model
**Wil ik** geen tegenstrijdige instructies
**Zodat** ik consistente output genereer

**Acceptance Criteria:**
- [ ] Haakjes regel: alleen voor afkortingen
- [ ] Context regel: impliciet verwerken
- [ ] Prioriteit hiërarchie gedefinieerd
- [ ] Conflict resolution logic
- [ ] Test voor consistentie

**Conflicts to Resolve:**
1. Haakjes: Regel 14 vs 53-61
2. Context: Regel 63-64 vs 178-186
3. Werkwoorden: overlappende regels

**Effort**: 2 points (0.5 dag)
**Priority**: P1 - Blocker

---

### Story PROMPT-4.3: Context-Aware Composition
**Als** systeem
**Wil ik** alleen relevante regels includen
**Zodat** de prompt context-specifiek is

**Acceptance Criteria:**
- [ ] Detect context type (juridisch/organisatorisch)
- [ ] Load alleen relevante validatie regels
- [ ] Skip irrelevante voorbeelden
- [ ] Dynamic prompt building
- [ ] Cache composed prompts

**Implementation:**
```python
@dataclass
class PromptContext:
    organization: str  # OM, DJI, etc
    domain: str       # juridisch, operationeel
    complexity: str   # simpel, complex

def compose_prompt(context: PromptContext) -> str:
    base = load_base_prompt()
    rules = filter_rules_by_context(context)
    examples = select_examples(context, max=2)
    return optimize(base + rules + examples)
```

**Effort**: 3 points (1 dag)
**Priority**: P1 - Core

---

### Story PROMPT-4.4: Smart Caching Layer
**Als** systeem
**Wil ik** geoptimaliseerde prompts cachen
**Zodat** compositie tijd minimaal is

**Acceptance Criteria:**
- [ ] Cache key op context combinatie
- [ ] TTL configureerbaar (default 1h)
- [ ] Memory efficient storage
- [ ] Cache hit rate >80%
- [ ] Invalidatie bij regel updates

**Implementation:**
```python
@st.cache_data(ttl=3600)
def get_optimized_prompt(
    term: str,
    organization: str,
    domain: str
) -> str:
    context = PromptContext(organization, domain)
    return compose_prompt(context)
```

**Effort**: 2 points (0.5 dag)
**Priority**: P2 - Performance

---

### Story PROMPT-4.5: Rule Priority System
**Als** validatie systeem
**Wil ik** regel prioriteiten respecteren
**Zodat** belangrijke regels voorrang krijgen

**Acceptance Criteria:**
- [ ] Priority levels: CRITICAL, HIGH, MEDIUM, LOW
- [ ] Token budget allocation per priority
- [ ] Graceful degradation bij token limit
- [ ] Essential rules always included
- [ ] Logging van excluded rules

**Priority Matrix:**
```
CRITICAL (always): 300 tokens
- Geen lidwoord start
- Genus proximum + differentia
- Context impliciet

HIGH (if space): 200 tokens
- Specifieke validaties
- Domein regels

MEDIUM/LOW (optional): 150 tokens
- Voorbeelden
- Edge cases
```

**Effort**: 2 points (0.5 dag)
**Priority**: P2 - Enhancement

---

### Story PROMPT-4.6: Monitoring & Analytics
**Als** product owner
**Wil ik** prompt efficiency metrics
**Zodat** ik ROI kan meten

**Acceptance Criteria:**
- [ ] Token count per request
- [ ] Cache hit rate
- [ ] Response time correlation
- [ ] Cost calculation
- [ ] Dashboard in monitoring tab

**Metrics to Track:**
```python
{
    "prompt_tokens": 1250,
    "cached": true,
    "composition_time_ms": 5,
    "rules_included": 15,
    "rules_excluded": 30,
    "estimated_cost": 0.025
}
```

**Effort**: 1 point (0.5 dag)
**Priority**: P3 - Nice to have

---

## 🚀 Implementation Plan

### Dag 1 (4 Sep): Foundation
**Focus**: Quick wins voor 50% reductie
- [ ] PROMPT-4.1: Consolidate duplicates (morning)
- [ ] PROMPT-4.2: Fix contradictions (afternoon)
- [ ] Test: Verify output quality maintained

**Expected Result**: 7,250 → 4,000 tokens

### Dag 2 (5 Sep): Smart Composition
**Focus**: Context-aware system
- [ ] PROMPT-4.3: Context detection (morning)
- [ ] PROMPT-4.3: Dynamic composition (afternoon)
- [ ] Integration test with real definitions

**Expected Result**: 4,000 → 2,000 tokens

### Dag 3 (6 Sep): Optimization
**Focus**: Final optimization & caching
- [ ] PROMPT-4.4: Caching implementation
- [ ] PROMPT-4.5: Priority system
- [ ] Performance testing

**Expected Result**: 2,000 → 1,250 tokens

### Dag 4 (Optional): Monitoring
- [ ] PROMPT-4.6: Analytics dashboard
- [ ] Documentation update
- [ ] Team demo

---

## ✅ Definition of Done

- [ ] Token count ≤ 1,250
- [ ] Response time < 5 seconds
- [ ] Quality score unchanged (>80%)
- [ ] All tests passing
- [ ] Zero contradictions
- [ ] Cache working
- [ ] Documentation updated

---

## 📊 Success Metrics

| Metric | Baseline | Target | Actual |
|--------|----------|---------|---------|
| Token count | 7,250 | 1,250 | TBD |
| Response time | 8-12s | <5s | TBD |
| API cost/month | €1,500 | €250 | TBD |
| Cache hit rate | 0% | >80% | TBD |
| Quality score | 82% | >80% | TBD |

---

## 🔧 Technical Implementation Details

### File Structure
```
src/services/prompt_service_v2.py
├── consolidate_rules()
├── resolve_contradictions()
├── compose_prompt()
└── cache_prompt()

config/prompts/
├── base_prompt.yaml
├── rules_consolidated.yaml
└── examples_curated.yaml
```

### Key Code Changes

#### 1. Consolidate "Start niet met..." Rules
```python
# Van: 42 individuele regels
# Naar:
FORBIDDEN_STARTS = {
    "articles": ["de", "het", "een"],
    "verbs": ["is", "zijn", "wordt", "betreft"],
    "constructs": ["proces waarbij", "type van"]
}
```

#### 2. Context-Aware Loading
```python
def get_relevant_rules(context: Dict) -> List[Rule]:
    if context["domain"] == "juridisch":
        return load_juridical_rules()
    elif context["organization"] == "DJI":
        return load_dji_rules()
    return load_base_rules()
```

#### 3. Smart Token Budgeting
```python
def optimize_prompt(base: str, rules: List, budget: int = 1250):
    essential = filter_priority(rules, "CRITICAL")
    remaining_budget = budget - count_tokens(base + essential)

    if remaining_budget > 200:
        add_rules = filter_priority(rules, "HIGH")[:remaining_budget]

    return base + essential + add_rules
```

---

## 🎯 Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Quality degradation | HIGH | A/B test old vs new |
| Cache invalidation issues | MEDIUM | TTL + manual clear |
| Context detection errors | MEDIUM | Fallback to full prompt |
| Team resistance | LOW | Show cost savings |

---

*Epic created: 3 september 2025*
*Owner: Development Team*
*Review: 6 september 2025*
