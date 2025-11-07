# PROMPT V8 IMPLEMENTATION PLAN
**Project:** DefinitieAgent Prompt Optimization
**Van:** v7 (7.250 tokens) → v8 (2.650 tokens)
**Timeline:** 3 weken
**Effort:** 16 uur totaal

---

## 🎯 DOELSTELLINGEN

1. **Token Reductie:** 7.250 → 2.650 (-63%)
2. **Conflict Resolution:** 10 → 0 conflicten
3. **LLM Compliance:** 60% → 90%
4. **Generatie Snelheid:** 4-5s → 2-3s
5. **Kwaliteit Score:** 6.5/10 → 8.5/10

---

## 📋 FASE 1: QUICK WINS (Week 1, 4 uur)

### 1.1 Verwijder Dubbele Validatieregels

**Bestanden om aan te passen:**
```python
# src/services/prompts/modules/arai_rules_module.py
# src/services/prompts/modules/con_rules_module.py
# src/services/prompts/modules/ess_rules_module.py
# src/services/prompts/modules/integrity_rules_module.py
# src/services/prompts/modules/sam_rules_module.py
# src/services/prompts/modules/structure_rules_module.py
# src/services/prompts/modules/ver_rules_module.py
```

**Van:**
```python
def execute(self, context: ModuleContext) -> List[str]:
    manager = get_cached_toetsregel_manager()
    all_rules = manager.get_all_regels()

    for regel_key, regel_data in sorted_rules:
        sections.extend(self._format_rule(regel_key, regel_data))
        # Voegt 50-100 tokens per regel toe
```

**Naar:**
```python
def execute(self, context: ModuleContext) -> List[str]:
    # Alleen high-level principes, geen individuele regels
    return [
        "### ✅ Algemene Regels (ARAI):",
        "- Begin met zelfstandig naamwoord (geen werkwoord/koppelwerkwoord)",
        "- Vermijd vage containerbegrippen zonder specificatie",
        "- Essentie beschrijven, niet het doel",
        "- Volledige validatie gebeurt automatisch na generatie",
        ""
    ]
```

**Impact:** -3.500 tokens (48% reductie)

### 1.2 Fix Critical Conflicts

**Bestand:** `src/services/prompts/modules/error_prevention_module.py`

**Wijziging regel 323-329:**
```python
# VOOR:
"❌ Start niet met 'proces waarbij'",
"❌ Start niet met 'handeling die'",

# NA:
"❌ Start niet met koppelwerkwoord + categorie:",
"   - 'is een proces waarbij' (FOUT)",
"   - 'betreft een handeling die' (FOUT)",
"✅ WEL toegestaan zonder koppelwerkwoord:",
"   - 'activiteit waarbij' (GOED)",
"   - 'handeling waarin' (GOED)",
```

### 1.3 Consolideer Verboden Lijst

**Bestand:** `src/services/prompts/modules/error_prevention_module.py`

**Van:** 42 individuele verboden (regels 294-335)

**Naar:**
```python
def _build_error_section(self) -> List[str]:
    return [
        "### ✅ APPROVED START PATTERNS:",
        "",
        "**PROCES:** [activiteit/handeling] waarbij [actor] [actie] uitvoert",
        "**TYPE:** [soort/categorie] [bovenbegrip] met kenmerk",
        "**RESULTAAT:** [uitkomst] van [proces] dat [functie]",
        "",
        "🚫 VERMIJD: Koppelwerkwoorden ('is'), lidwoorden ('de/het'), term-herhaling",
        ""
    ]
```

**Impact:** -750 tokens

### 1.4 Test & Valideer

```bash
# Test script
python scripts/test_prompt_generation.py \
    --begrippen "integriteit,sanctie,toezicht,evaluatie" \
    --compare-versions v7,v8-quick \
    --metrics tokens,conflicts,quality
```

---

## 📋 FASE 2: STRUCTURELE REFACTOR (Week 2, 8 uur)

### 2.1 Implementeer Inverted Pyramid Template

**Nieuw bestand:** `src/services/prompts/templates/inverted_pyramid.py`

```python
class InvertedPyramidTemplate:
    """
    Nieuwe prompt structuur:
    1. Mission Statement (50 tokens)
    2. Golden Rules (300 tokens)
    3. Templates (400 tokens)
    4. Refinement (800 tokens)
    5. Checklist (100 tokens)
    """

    def build(self, context: PromptContext) -> str:
        sections = [
            self._build_mission(context),
            self._build_golden_rules(),
            self._build_templates(context.category),
            self._build_refinement_rules(),
            self._build_checklist()
        ]
        return "\n\n".join(sections)
```

### 2.2 Conditional Module Loading

**Bestand:** `src/services/prompts/modules/prompt_orchestrator.py`

```python
def build_prompt(self, context: ModuleContext) -> str:
    # Filter modules based on context
    active_modules = self._get_active_modules(context)

    def _get_active_modules(self, context: ModuleContext) -> List[str]:
        """Only load modules relevant for this request."""

        # Always include core
        modules = ["expertise", "output_specification", "task"]

        # Conditional modules
        if context.has_context_info():
            modules.append("context_awareness")

        if context.get_complexity() > 0.7:
            modules.append("grammar")
            modules.append("metrics")

        if context.requires_templates():
            modules.append("template")
            modules.append("semantic_categorisation")

        # Only include 2-3 most relevant rule modules
        if context.focus_area == "structure":
            modules.append("structure_rules")
        elif context.focus_area == "integrity":
            modules.append("integrity_rules")
        else:
            modules.append("ess_rules")  # Default to essential rules

        return modules
```

### 2.3 Static Module Caching

**Bestand:** `src/services/prompts/cache/module_cache.py`

```python
import streamlit as st

class ModuleCache:
    """Cache static module outputs that don't change per request."""

    @st.cache_data(ttl=3600)
    def get_grammar_output(self) -> str:
        """Grammar rules don't change - cache for 1 hour."""
        from ..modules.grammar_module import GrammarModule
        return GrammarModule().execute(ModuleContext())

    @st.cache_data(ttl=3600)
    def get_error_prevention_output(self) -> str:
        """Error patterns are static - cache."""
        from ..modules.error_prevention_module import ErrorPreventionModule
        return ErrorPreventionModule().execute(ModuleContext())
```

### 2.4 Implementeer Priority Signaling

**Update alle regel modules met prioriteit:**

```python
class EssRulesModule(BasePromptModule):
    def execute(self, context: ModuleContext) -> List[str]:
        return [
            "### 🔴 KRITIEKE REGELS (Must-Have):",
            "- **ESS-02:** Ontologische categorie expliciet",
            "- **ESS-01:** Essentie, niet doel",
            "",
            "### 🟡 BELANGRIJKE REGELS (Should-Have):",
            "- **ESS-03:** Instanties uniek onderscheidbaar",
            "",
            "### 🟢 NICE-TO-HAVE (Polish):",
            "- **ESS-04:** Toetsbaarheid",
            "- **ESS-05:** Voldoende onderscheidend",
        ]
```

---

## 📋 FASE 3: VALIDATIE & DEPLOYMENT (Week 3, 4 uur)

### 3.1 A/B Testing Framework

**Nieuw:** `scripts/ab_test_prompts.py`

```python
import asyncio
from typing import Dict, List

class PromptABTest:
    def __init__(self):
        self.test_begrippen = [
            # Proces begrippen
            "observatie", "registratie", "evaluatie",
            # Type begrippen
            "sanctie", "maatregel", "voorziening",
            # Resultaat begrippen
            "besluit", "uitspraak", "rapport",
            # Edge cases
            "AVG", "DJI", "re-integratie"
        ]

    async def run_test(self) -> Dict:
        results = {
            "v7": await self.test_version("v7"),
            "v8": await self.test_version("v8")
        }
        return self.compare_results(results)
```

### 3.2 Kwaliteitsmetrics

```python
class QualityMetrics:
    """Meet definitie kwaliteit volgens standaarden."""

    def measure(self, definition: str, prompt_version: str) -> Dict:
        return {
            "tokens_used": self.count_tokens(prompt_version),
            "generation_time": self.time_generation(),
            "validation_pass": self.run_validation(definition),
            "expert_score": self.get_expert_review(definition),
            "conflicts_detected": self.detect_conflicts(),
            "rule_compliance": self.check_rule_compliance(definition)
        }
```

### 3.3 Rollout Strategy

**Stap 1: Shadow Mode (Week 3, Dag 1-2)**
```python
# Beide versies draaien, v8 alleen voor metrics
if FEATURE_FLAGS.get("prompt_v8_shadow"):
    v7_result = generate_with_v7(begrip)
    v8_result = generate_with_v8(begrip)
    log_comparison(v7_result, v8_result)
    return v7_result  # Gebruik nog v7
```

**Stap 2: Canary Release (Week 3, Dag 3-4)**
```python
# 10% van requests gebruikt v8
if random.random() < 0.1:
    return generate_with_v8(begrip)
else:
    return generate_with_v7(begrip)
```

**Stap 3: Full Rollout (Week 3, Dag 5)**
```python
# 100% v8 met fallback
try:
    return generate_with_v8(begrip)
except Exception as e:
    logger.warning(f"V8 failed, falling back: {e}")
    return generate_with_v7(begrip)
```

---

## 🧪 TEST SCENARIOS

### Scenario 1: Basis Proces Definitie
```python
test_case = {
    "begrip": "integriteit",
    "context": {"organisatorisch": "test"},
    "expected_start": "activiteit waarbij",
    "max_tokens": 3000,
    "must_validate": ["ESS-02", "STR-01", "INT-01"]
}
```

### Scenario 2: Complex met Juridische Context
```python
test_case = {
    "begrip": "sanctie",
    "context": {
        "juridisch": "Wetboek van Strafrecht",
        "wettelijk": "Art. 9 Sr"
    },
    "expected_category": "resultaat",
    "max_tokens": 3500
}
```

### Scenario 3: Edge Case - Afkorting
```python
test_case = {
    "begrip": "AVG",
    "expected_contains": "Algemene Verordening Gegevensbescherming",
    "max_chars": 350
}
```

---

## 📊 SUCCESS CRITERIA

### Go/No-Go Decision Matrix

| Criterium | Target | No-Go Threshold | Measurement |
|-----------|--------|-----------------|-------------|
| Token Reductie | >50% | <30% | Automated |
| Conflicten | 0 | >2 | Automated |
| Validatie Success | >85% | <70% | Automated |
| Expert Score | >8.0 | <7.0 | Manual (3 experts) |
| Generatie Tijd | <3s | >5s | Automated |
| Error Rate | <5% | >10% | Automated |

### Rollback Triggers
- Expert score < 7.0
- Validatie success < 70%
- Error rate > 10%
- User complaints > 3 binnen 24 uur

---

## 🚀 DEPLOYMENT CHECKLIST

### Pre-Deployment (Week 2, Dag 5)
- [ ] Code review door senior developer
- [ ] Unit tests voor alle nieuwe modules
- [ ] Integration tests voor prompt building flow
- [ ] Performance benchmarks uitgevoerd
- [ ] A/B test framework operational

### Deployment Day (Week 3, Dag 5)
- [ ] Feature flags configured
- [ ] Rollback procedure documented
- [ ] Monitoring dashboard actief
- [ ] Hotfix procedure ready
- [ ] Team briefing completed

### Post-Deployment (Week 4)
- [ ] Monitor metrics dagelijks
- [ ] Collect user feedback
- [ ] Fine-tune edge cases
- [ ] Document lessons learned
- [ ] Plan v8.1 improvements

---

## 📈 EXPECTED OUTCOMES

### Week 1 (Quick Wins)
- **Tokens:** 7.250 → 5.000 (-31%)
- **Conflicts:** 10 → 0
- **Effort:** 4 uur
- **Risk:** Laag

### Week 2 (Structural)
- **Tokens:** 5.000 → 3.000 (-58%)
- **Module efficiency:** +40%
- **Effort:** 8 uur
- **Risk:** Medium

### Week 3 (Optimization)
- **Tokens:** 3.000 → 2.650 (-63%)
- **Quality score:** 6.5 → 8.5
- **Effort:** 4 uur
- **Risk:** Laag

---

## 🔧 TECHNICAL DEPENDENCIES

### Required Updates
1. `CachedToetsregelManager` - Ensure cache works with summary mode
2. `ModularValidationService` - Verify works without prompt rules
3. `PromptServiceV2` - Support both v7 and v8 templates
4. `SessionStateManager` - Store prompt version preference

### New Components
1. `InvertedPyramidTemplate` - New prompt structure
2. `ModuleCache` - Static content caching
3. `PromptABTest` - Testing framework
4. `QualityMetrics` - Measurement system

---

## 👥 TEAM & RESPONSIBILITIES

### Development Team
- **Lead Developer:** Implement Phase 1 & 2
- **QA Engineer:** Design test scenarios, run A/B tests
- **Domain Expert:** Review generated definitions, score quality

### Stakeholders
- **Product Owner:** Go/No-Go decision
- **End Users:** Feedback tijdens canary release

---

## 📝 NOTES & RISKS

### Risks
1. **Kwaliteit degradatie** - Mitigatie: Extensive A/B testing
2. **Unexpected conflicts** - Mitigatie: Shadow mode first
3. **Performance regression** - Mitigatie: Cache static content
4. **User resistance** - Mitigatie: Gradual rollout

### Opportunities
1. **Further optimization** - Track which modules are most valuable
2. **Personalization** - User-specific prompt configurations
3. **Learning system** - Use validation results to improve prompts

---

**Document Status:** Ready for Review
**Next Step:** Technical Review Meeting
**Decision Needed:** Approve Phase 1 Quick Wins