---
canonical: false
status: active
owner: development
last_verified: 2025-09-03
applies_to: definitie-app@v2.3
document_type: user-stories
epic: epic-7-performance-scaling
parent_doc: epic-7-performance-optimization
priority: critical
sprint: UAT-2025-09
---

# Epic 7: Prompt Optimization - User Stories Detail

**Sprint Goal**: Reduceer prompt tokens met 83% voor betere performance en lagere kosten
**Business Value**: €1,000+/maand besparing + 50% snellere responses
**Technical Debt Addressed**: 40% prompt duplicatie, 5+ tegenstrijdigheden

---

## 📊 Story Overview Dashboard

| Story | Title | Points | Priority | Status | Impact |
|-------|-------|--------|----------|---------|--------|
| PROMPT-4.1 | Consolidate Duplicates | 3 | P1 | 📋 Ready | -2,000 tokens |
| PROMPT-4.2 | Fix Contradictions | 2 | P1 | 📋 Ready | Quality++ |
| PROMPT-4.3 | Context Composition | 3 | P1 | 📋 Ready | -3,000 tokens |
| PROMPT-4.4 | Smart Caching | 2 | P2 | 📋 Ready | Speed++ |
| PROMPT-4.5 | Priority System | 2 | P2 | 📋 Ready | Flexibility |
| PROMPT-4.6 | Analytics | 1 | P3 | 📋 Planned | Insights |

**Total Points**: 13 (10 for UAT, 3 optional)

---

## 🎯 Detailed User Stories

### PROMPT-4.1: Consolidate Duplicate Rules (DAY 1 - Morning)

**User Story:**
> Als AI systeem wil ik geen duplicate instructies ontvangen zodat ik efficiënter kan werken

**Current Situation:**
```text
Regels 432-473: 42x "Start niet met [woord]"
Regels 119-140: 3x containerbegrip uitleg
Regels 147-160: 2x identieke modale werkwoord regels
Regels 66-99 + 202-229: 3x ontologie uitleg
```

**Consolidation Plan:**

#### A. "Start niet met..." Consolidatie
```python
# VAN: 42 regels (2,100 karakters)
"Start niet met 'de'"
"Start niet met 'het'"
"Start niet met 'een'"
... (39 meer)

# NAAR: 1 compacte regel (300 karakters)
FORBIDDEN_STARTS = """
⚠️ VERBODEN BEGIN:
- Lidwoorden: de, het, een
- Koppelwerkwoorden: is, zijn, wordt, betreft
- Actiewerkwoorden: verwijst naar, houdt in
- Vage constructies: proces waarbij, type van
"""
```
**Besparing: 1,800 karakters (450 tokens)**

#### B. ARAI-02 Familie Consolidatie
```python
# VAN: 3 overlappende regels
ARAI-02: "Vermijd vage containerbegrippen..."
ARAI-02SUB1: "Lexicale containerbegrippen zoals..."
ARAI-02SUB2: "Ambtelijke containerbegrippen..."

# NAAR: 1 geïntegreerde regel
ARAI-02 = """
Geen vage containerbegrippen:
- Lexicaal: aspect, ding, iets
- Ambtelijk: proces, voorziening (zonder specificatie)
✓ OK: systeem voor beslisregistratie
✗ FOUT: voorziening die iets doet
"""
```
**Besparing: 600 karakters (150 tokens)**

#### C. Ontologie Consolidatie
```python
# VAN: 3 separate uitleggen
# NAAR: 1 compacte matrix
ONTOLOGY_MATRIX = """
Object: concrete/abstract entiteit (persoon, document)
Handeling: actie/proces (arrestatie, beoordeling)
Toestand: status/conditie (vrijheid, detentie)
Eigenschap: kenmerk/attribuut (strafbaar, wettelijk)
"""
```
**Besparing: 800 karakters (200 tokens)**

**Acceptance Criteria:**
- [x] Identificeer alle duplicaties
- [ ] Consolideer naar single source
- [ ] Test output kwaliteit
- [ ] Verify token reductie
- [ ] Update prompt templates

**Technical Implementation:**
```python
# src/services/prompt_optimizer.py
class PromptOptimizer:
    def consolidate_duplicates(self, prompt: str) -> str:
        consolidated = self.merge_start_rules(prompt)
        consolidated = self.merge_arai_family(consolidated)
        consolidated = self.merge_ontology(consolidated)
        return consolidated

    def verify_consolidation(self, original: str, optimized: str):
        assert count_tokens(optimized) < count_tokens(original) * 0.6
        assert quality_score(optimized) >= quality_score(original)
```

---

### PROMPT-4.2: Fix Contradictions (DAY 1 - Afternoon)

**User Story:**
> Als AI model wil ik eenduidige instructies zodat ik consistente output kan genereren

**Identified Contradictions:**

#### Contradiction 1: Haakjes Gebruik
```text
CONFLICT:
- Regel 14: "Geen haakjes voor toelichtingen"
- Regel 53: "Plaats afkortingen tussen haakjes"

RESOLUTION:
"Haakjes ALLEEN voor afkortingen na eerste gebruik:
✓ Dienst Justitiële Inrichtingen (DJI)
✗ maatregel (corrigerend of preventief)"
```

#### Contradiction 2: Context Explicitering
```text
CONFLICT:
- Regel 63: "VERPLICHTE CONTEXT: Organisatorisch"
- Regel 64: "zonder deze expliciet te benoemen"

RESOLUTION:
"Context IMPLICIET verwerken in definitie:
✓ 'detentieplaatsing' (impliceert DJI context)
✗ 'detentieplaatsing binnen DJI' (expliciet = fout)"
```

#### Contradiction 3: Regel Prioriteit
```text
NEW HIERARCHY:
1. CRITICAL: Structuur regels (altijd)
2. HIGH: Domein specifiek (indien relevant)
3. MEDIUM: Stijl regels (indien ruimte)
4. LOW: Voorbeelden (optioneel)
```

**Implementation:**
```python
class ContradictionResolver:
    def resolve_conflicts(self, rules: List[Rule]) -> List[Rule]:
        # Remove conflicting rules
        rules = self.remove_contradiction_pairs(rules)

        # Apply priority hierarchy
        rules = self.apply_priority_order(rules)

        # Add conflict resolution notes
        rules = self.add_resolution_context(rules)

        return rules
```

---

### PROMPT-4.3: Context-Aware Composition (DAY 2)

**User Story:**
> Als systeem wil ik alleen relevante regels laden zodat de prompt context-specifiek is

**Context Detection:**
```python
@dataclass
class DefinitionContext:
    term: str
    organization: str  # OM, DJI, Rechtspraak
    domain: str       # juridisch, operationeel, administratief
    complexity: str   # simpel, normaal, complex

    @property
    def rule_categories(self) -> List[str]:
        if self.domain == "juridisch":
            return ["ARAI", "CON", "VER"]
        elif self.organization == "DJI":
            return ["ARAI", "SAM", "INT"]
        return ["ARAI", "STR", "ESS"]
```

**Dynamic Prompt Building:**
```python
class ContextAwarePromptBuilder:
    def build_prompt(self, context: DefinitionContext) -> str:
        # Base instructions (always included)
        prompt = self.load_base_instructions()  # 500 tokens

        # Context-specific rules
        relevant_rules = self.filter_rules_by_context(context)  # 400 tokens

        # Select best examples
        examples = self.select_examples(context, max_examples=2)  # 350 tokens

        return self.optimize_token_usage(prompt, relevant_rules, examples)

    def filter_rules_by_context(self, context: DefinitionContext):
        rules = []
        for category in context.rule_categories:
            rules.extend(self.rules_by_category[category])
        return self.deduplicate(rules)
```

**Context Examples:**
```python
# Juridisch context (OM)
prompt_juridisch = """
Focus: Wettelijke precisie en juridische consistentie
Regels: ARAI-basis, VER-volledig, CON-impliciet
Voorbeelden: [strafbaar feit, vervolging]
"""

# Operationeel context (DJI)
prompt_dji = """
Focus: Operationele duidelijkheid en uitvoerbaarheid
Regels: ARAI-basis, SAM-integratie, INT-specificatie
Voorbeelden: [detentie, verlof]
"""

# Administratief context
prompt_admin = """
Focus: Procesbeschrijving en administratieve accuraatheid
Regels: ARAI-basis, STR-structuur, ESS-volledigheid
Voorbeelden: [registratie, archivering]
"""
```

---

### PROMPT-4.4: Smart Caching Layer (DAY 3 - Morning)

**User Story:**
> Als systeem wil ik geoptimaliseerde prompts cachen voor snelle hergebruik

**Cache Strategy:**
```python
import hashlib
from typing import Optional

class PromptCache:
    def __init__(self):
        self.cache = {}
        self.ttl = 3600  # 1 hour

    def get_cache_key(self, context: DefinitionContext) -> str:
        """Generate deterministic cache key"""
        key_parts = [
            context.organization,
            context.domain,
            context.complexity
        ]
        return hashlib.md5("_".join(key_parts).encode()).hexdigest()

    @st.cache_data(ttl=3600)
    def get_or_build_prompt(self, context: DefinitionContext) -> str:
        cache_key = self.get_cache_key(context)

        if cache_key in self.cache:
            self.metrics.cache_hit()
            return self.cache[cache_key]

        self.metrics.cache_miss()
        prompt = self.build_prompt(context)
        self.cache[cache_key] = prompt
        return prompt
```

**Cache Metrics:**
```python
{
    "cache_size": 15,
    "hit_rate": 0.85,
    "avg_build_time_ms": 45,
    "avg_cached_time_ms": 2,
    "memory_usage_mb": 0.5
}
```

---

### PROMPT-4.5: Rule Priority System (DAY 3 - Afternoon)

**User Story:**
> Als systeem wil ik regels prioriteren binnen token budget

**Priority Implementation:**
```python
class RulePrioritizer:
    PRIORITY_TOKENS = {
        "CRITICAL": 300,  # Must have
        "HIGH": 200,      # Should have
        "MEDIUM": 150,    # Nice to have
        "LOW": 100        # Optional
    }

    def prioritize_within_budget(self, rules: List[Rule], budget: int = 1250):
        prioritized = []
        remaining_budget = budget

        for priority in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            priority_rules = [r for r in rules if r.priority == priority]

            for rule in priority_rules:
                rule_tokens = count_tokens(rule.text)
                if remaining_budget >= rule_tokens:
                    prioritized.append(rule)
                    remaining_budget -= rule_tokens
                else:
                    self.log_excluded_rule(rule, "budget_exceeded")

        return prioritized
```

---

## 📈 Implementation Tracking

### Day 1 (4 Sep): Consolidation & Fixes
```
Morning (4 hrs):
[ ] PROMPT-4.1: Consolidate duplicates
    [ ] Identify all duplications
    [ ] Create consolidated rules
    [ ] Test quality maintenance

Afternoon (4 hrs):
[ ] PROMPT-4.2: Fix contradictions
    [ ] Resolve haakjes conflict
    [ ] Resolve context conflict
    [ ] Implement priority hierarchy

Result: 7,250 → 4,000 tokens (45% reduction)
```

### Day 2 (5 Sep): Smart Composition
```
Morning (4 hrs):
[ ] PROMPT-4.3: Context detection
    [ ] Define context types
    [ ] Implement detection logic
    [ ] Map rules to contexts

Afternoon (4 hrs):
[ ] PROMPT-4.3: Dynamic building
    [ ] Build prompt composer
    [ ] Test different contexts
    [ ] Verify output quality

Result: 4,000 → 2,000 tokens (50% reduction)
```

### Day 3 (6 Sep): Optimization & Polish
```
Morning (4 hrs):
[ ] PROMPT-4.4: Caching
    [ ] Implement cache layer
    [ ] Add metrics tracking
    [ ] Test cache efficiency

Afternoon (4 hrs):
[ ] PROMPT-4.5: Priority system
    [ ] Define priority levels
    [ ] Implement budget allocation
    [ ] Test graceful degradation

Result: 2,000 → 1,250 tokens (37.5% reduction)
```

---

## ✅ Success Criteria

### Quantitative Metrics
- [ ] Token count ≤ 1,250 (from 7,250)
- [ ] Response time < 5s (from 8-12s)
- [ ] API cost < €0.03 per generation (from €0.15)
- [ ] Cache hit rate > 80%
- [ ] Zero contradictions in prompt

### Qualitative Metrics
- [ ] Definition quality score ≥ 80%
- [ ] All validation rules still enforced
- [ ] Output consistency maintained
- [ ] Team approval on changes

---

## 🔧 Testing Strategy

### Unit Tests
```python
def test_consolidation():
    original = load_original_prompt()
    optimized = optimizer.consolidate_duplicates(original)
    assert count_tokens(optimized) < count_tokens(original) * 0.6

def test_no_contradictions():
    rules = load_optimized_rules()
    conflicts = detector.find_contradictions(rules)
    assert len(conflicts) == 0

def test_context_composition():
    context = DefinitionContext("arrestatie", "OM", "juridisch")
    prompt = builder.build_prompt(context)
    assert "VER-" in prompt  # Juridische regels included
    assert "SAM-" not in prompt  # DJI regels excluded
```

### Integration Tests
```python
def test_quality_maintained():
    test_terms = ["arrestatie", "detentie", "vonnis"]
    for term in test_terms:
        old_result = generate_with_old_prompt(term)
        new_result = generate_with_optimized_prompt(term)
        assert quality_score(new_result) >= quality_score(old_result) * 0.95
```

---

## 📊 Monitoring Dashboard Mock

```
┌─────────────────────────────────────────┐
│        Prompt Optimization Metrics       │
├─────────────────────────────────────────┤
│ Token Reduction:  83% ▓▓▓▓▓▓▓▓░░ 7250→1250│
│ Response Time:    65% ▓▓▓▓▓▓░░░░ 12s→4s  │
│ Cost Savings:     80% ▓▓▓▓▓▓▓▓░░ €1500→€300│
│ Cache Hit Rate:   85% ▓▓▓▓▓▓▓▓▓░         │
│ Quality Score:    82% ▓▓▓▓▓▓▓▓░░         │
└─────────────────────────────────────────┘
```

---

*Document created: 3 september 2025*
*Epic owner: Development Team*
*Business sponsor: Product Management*
