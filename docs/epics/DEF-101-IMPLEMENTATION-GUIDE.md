# DEF-101 EPIC Implementation Guide
**Last Updated:** 7 november 2025
**Total Effort:** 28 uur
**Expected Impact:** -63% token reduction (7250→2650)

## 🎯 Quick Start voor nieuwe developer

Als je DEF-101 oppakt, volg deze stappen:

### Stap 1: Lees deze documenten (30 min)
1. **Analysis:** `docs/analyses/PROMPT_COMPREHENSIVE_ANALYSIS_AND_IMPROVEMENT_PLAN.md`
2. **Architecture:** `docs/analyses/PROMPT_OPTIMIZATION_ANALYSIS.md`
3. **Implementation:** `docs/planning/PROMPT_V8_IMPLEMENTATION.md`

### Stap 2: Check Linear status
- **DEF-102** (Todo) - Begin hiermee! Fix 5 blocking contradictions
- **DEF-106** (Todo) - PromptValidator voor regression prevention
- Rest staat in Backlog

### Stap 3: Verwijder verkeerde issues
- **DEF-122** - CANCEL dit (verkeerde aanpak)
- **DEF-125** - CANCEL dit (verkeerde aanpak)
- Gebruik **DEF-126** voor validatieregel transformatie

---

## 📋 Complete Issue List (9 actieve issues)

### ORIGINELE CONTENT FIXES (DEF-102 t/m DEF-107)
| Issue | Titel | Status | Effort | Impact |
|-------|-------|--------|--------|--------|
| DEF-102 | Fix Blocking Contradictions | **Todo** ⚡ | 3u | System wordt usable |
| DEF-103 | Reduce Cognitive Load | Backlog | 2u | -750 tokens |
| DEF-104 | Reorganize Flow | Backlog | 3u | -800 tokens |
| DEF-105 | Visual Hierarchy | Backlog | 2u | Betere leesbaarheid |
| DEF-106 | PromptValidator | **Todo** ⚡ | 2u | Voorkomt regressie |
| DEF-107 | Documentation & Testing | Backlog | 4u | Maintainability |

### NIEUWE ARCHITECTURE FIXES (DEF-123, DEF-124, DEF-126)
| Issue | Titel | Status | Effort | Impact |
|-------|-------|--------|--------|--------|
| DEF-123 | Context-aware module loading | Backlog 🆕 | 5u | **-25% tokens** |
| DEF-124 | Cache static modules | Backlog 🆕 | 2u | **40% faster** |
| DEF-126 | Transform rules to instructions | Backlog 🆕 | 5u | **Betere generatie** |

---

## 🗓️ Implementatie Volgorde (BELANGRIJK!)

### WEEK 1: Critical Fixes (8 uur)
```
1. DEF-102 - Fix 5 blocking contradictions (3u)
   → Files: src/services/prompts/modules/error_prevention_module.py
   → Add exception clauses voor ESS-02

2. DEF-126 - Transform validation rules to instructions (5u)
   → Files: alle 7 regel modules (arai_rules_module.py, etc.)
   → Transform van "check X" naar "doe X"
   → NIET DEF-122/125 gebruiken!

3. DEF-103 - Reduce cognitive load (2u) [indien tijd]
   → 42 forbidden patterns → 7 categorieën
```

### WEEK 2: Structural Improvements (10 uur)
```
4. DEF-104 - Reorganize flow + Inverted Pyramid (3u)
   → Implement 5-level pyramid structure
   → Critical info first

5. DEF-123 - Context-aware module loading (5u)
   → Grootste token savings!
   → 16 modules altijd → 6-10 conditional

6. DEF-105 - Visual hierarchy (2u)
   → 3-tier priority badges
```

### WEEK 3: Quality & Performance (8 uur)
```
7. DEF-106 - PromptValidator (2u)
   → Automated QA checks
   → Detecteer contradictions

8. DEF-124 - Cache static modules (2u)
   → 40% performance boost
   → Streamlit caching

9. DEF-107 - Documentation & testing (4u)
   → Golden reference set
   → Regression tests
```

---

## 🔧 Technische Details

### Files om aan te passen
```
src/services/prompts/modules/
├── arai_rules_module.py     (DEF-126: transform to instructions)
├── con_rules_module.py      (DEF-126: transform to instructions)
├── ess_rules_module.py      (DEF-126: transform to instructions)
├── integrity_rules_module.py(DEF-126: transform to instructions)
├── sam_rules_module.py      (DEF-126: transform to instructions)
├── structure_rules_module.py(DEF-126: transform to instructions)
├── ver_rules_module.py      (DEF-126: transform to instructions)
├── error_prevention_module.py (DEF-102: add exception clauses)
├── prompt_orchestrator.py   (DEF-123: conditional loading)
└── [new] module_cache.py    (DEF-124: caching layer)
```

### Test Strategy
```python
# Voor elke change:
pytest tests/services/prompts/test_prompt_generation.py

# A/B testing:
python scripts/ab_test_prompts.py --v7 --v8 --terms 50

# Token counting:
python scripts/count_prompt_tokens.py --before --after
```

---

## ⚠️ Belangrijke Aandachtspunten

### 1. NIET DEF-122/125 gebruiken!
- DEF-122 wil regels VERWIJDEREN (verkeerd)
- DEF-125 wil regels COMPRIMEREN (verkeerd)
- **Gebruik DEF-126**: TRANSFORMEER naar instructies

### 2. Contradictions eerst oplossen
- Begin ALTIJD met DEF-102
- Systeem is nu UNUSABLE door 5 blocking contradictions
- Vooral ESS-02 "is" conflict is kritiek

### 3. Measure impact
- Token count voor/na elke change
- A/B test met 50 begrippen
- Validatie scores moeten gelijk blijven of beter

### 4. Validatieregels NIET aanpassen
- JSON files blijven intact
- Python validatie code blijft intact
- Alleen PRESENTATIE in prompt modules wijzigt

---

## 📊 Expected Results

### Na Week 1 (Critical)
- ✅ Systeem wordt usable (contradictions opgelost)
- ✅ Betere instructies voor LLM
- ✅ -750 tokens (cognitive load)

### Na Week 2 (Structural)
- ✅ -2800 tokens extra (conditional loading)
- ✅ Betere information flow
- ✅ Visual hierarchy

### Na Week 3 (Quality)
- ✅ Automated regression prevention
- ✅ 40% sneller
- ✅ Volledig gedocumenteerd

### TOTAAL
- **Van:** 7250 tokens, unusable, 100+ concepts
- **Naar:** 2650 tokens (-63%), usable, <15 concepts

---

## 🔗 Links

- **Linear EPIC:** https://linear.app/definitie-app/issue/DEF-101
- **Analysis Doc:** `/docs/analyses/PROMPT_OPTIMIZATION_ANALYSIS.md`
- **Implementation Plan:** `/docs/planning/PROMPT_V8_IMPLEMENTATION.md`

---

## Contact

Bij vragen over deze EPIC:
- Check Linear comment van 7 november 2025
- Review de analysis documenten
- Test met golden reference set: `/tests/fixtures/golden_definitions.json`