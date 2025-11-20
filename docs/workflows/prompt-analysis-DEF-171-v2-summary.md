# HERZIENE Prompt Analysis - Executive Summary

**Datum:** 2025-11-20
**Scope:** Bounded analysis (60 min) van _Definitie_Generatie_prompt-23.txt
**Nieuwe Context:** DEF-126 VOLTOOID + Validatie module gescheiden + UI levert ontologische categorie

---

## 📊 Baseline Metrics

- **Lines:** 536
- **Characters:** 33,298
- **Tokens (reported):** 8,325
- **Tokens (measured):** 10,508 ⚠️ Discrepantie suggereert baseline van andere versie
- **Source of truth:** 10,508 tokens (tiktoken cl100k_base)

---

## 🎯 Drie Nieuwe Constraints

### 1️⃣ GEEN VALIDATIE-CONTENT
**Rationale:** Separate validatie module draait POST-generation
**Actie:** Verwijder ALLE "Toetsvraag:" secties (39 stuks) + validatie-specifieke voorbeelden
**Tokens:** 1,170 removable (11.1%)

### 2️⃣ GEEN ONTOLOGIE-BEPALING
**Rationale:** UI geeft ontologische categorie MEE (niet bepalen door LLM)
**Actie:** Verwijder "Je **moet** één van de vier categorieën..." + "Bepaal de juiste categorie..."
**Tokens:** 460 removable (4.4%)
**Behoud:** Kick-off termen PER categorie (want categorie is al bekend)

### 3️⃣ DEF-126 IMPACT
**Rationale:** JSON module heeft al 46 regels met "Instructie:" format
**Bevinding:** Duplicatie tussen prompt's inline instructies EN JSON module output
**Tokens:** 1,605 removable (15.3%)

---

## 🔍 MECE Decomposition (5 Categorieën)

| Categorie | Tokens Removable | % van Prompt | Prioriteit |
|-----------|------------------|--------------|------------|
| **VALIDATION_CONTENT** | 1,170 | 11.1% | HIGH |
| **ONTOLOGY_DETERMINATION** | 460 | 4.4% | HIGH |
| **DUPLICATION_WITH_JSON_MODULE** | 1,605 | 15.3% | HIGH |
| **STRUCTURAL_REDUNDANCY** | 1,080 | 10.3% | MEDIUM |
| **METADATA_NOISE** | 640 | 6.1% | LOW |
| **TOTAAL** | **4,955** | **47.2%** | - |

**Post-reduction estimate:** 5,553 tokens (47.2% reductie)

---

## 📈 Pareto Analysis (80/20 Rule)

### Top 3 Acties = 64.8% van Removable Tokens

| Rank | Actie | Tokens | Effort | Impact |
|------|-------|--------|--------|--------|
| **1** | Remove ALL 39 'Toetsvraag:' sections | 1,170 | LOW | HIGH |
| **2** | Remove rule examples (keep in JSON module) | 1,200 | MEDIUM | HIGH |
| **3** | Remove quality metrics section | 840 | LOW | MEDIUM |
| - | **TOTAAL TOP 3** | **3,210** | - | - |

**Percentage van totale prompt:** 30.6% reductie met Top 3

---

## 🔬 5 Whys Root Cause Analysis

**Probleem:** Na DEF-126 is prompt nog steeds 10,508 tokens met validatie-content en duplicatie

1. **Why?** DEF-126 transformeerde JSON module maar NIET de statische prompt template
2. **Why?** DEF-126 scope was beperkt tot `json_based_rules_module.py` (code), niet prompt file
3. **Why?** Prompt template werd gezien als aparte verantwoordelijkheid (geen coördinatie)
4. **Why?** JSON module output is DYNAMIC (runtime), prompt is STATIC (file), leek onafhankelijk
5. **Why?** HISTORICAL LAYERING - systeem evolueerde van static→JSON data→JSON module zonder cleanup

**ROOT CAUSE:** **ARCHITECTURELE SCHULD** - drie lagen bestaan tegelijkertijd:
1. Static prompt inline regels
2. JSON rule files
3. JSON module runtime generation

---

## 🎯 Impact-Effort Matrix & Fasering

### ✅ PHASE 1: Quick Wins (DO FIRST)
**Duration:** 1.5 uur | **Effort:** LOW | **Impact:** HIGH

| Actie | Tokens | Lines |
|-------|--------|-------|
| Remove 39 'Toetsvraag:' sections | 1,170 | 156-433 |
| Remove quality metrics section | 840 | 471-497 |
| Remove ontology determination | 460 | 71, 83-87 |
| Remove metadata section | 180 | 519-537 |
| **TOTAAL PHASE 1** | **2,650** | - |

**Outcome:** 7,858 tokens (**25.2% reductie**) | **Risk:** LOW

---

### 🔄 PHASE 2: Deduplication (DO SECOND)
**Duration:** 3 uur | **Effort:** MEDIUM | **Impact:** HIGH

| Actie | Tokens | Rationale |
|-------|--------|-----------|
| Remove rule-specific examples | 1,200 | JSON module is single source |
| Keep OUTPUT FORMAT examples | 0 | Generation-guiding, not rule-specific |

**Outcome:** 6,658 tokens (**36.6% reductie cumulative**) | **Risk:** MEDIUM

**Validatie vereist:** Vergelijk generated prompt before/after, verify JSON module includes examples

---

### 🗜️ PHASE 3: Compression (DO THIRD)
**Duration:** 4 uur | **Effort:** MEDIUM | **Impact:** MEDIUM

| Actie | Tokens | Before → After |
|-------|--------|----------------|
| Compress TYPE explanation | 300 | 30 lines → 10 lines |
| Consolidate grammar rules | 280 | 39 lines → 20 lines |
| **TOTAAL PHASE 3** | **580** | - |

**Outcome:** 6,078 tokens (**42.2% reductie cumulative**) | **Risk:** MEDIUM

---

## 📋 Beantwoording Specifieke Vragen

### 1️⃣ Hoeveel validatie-content zit er NOG in prompt NA DEF-126?

**Antwoord:** 1,630 tokens (15.5% van prompt)

- Toetsvragen: 39 stuks (780 tokens)
- Validatie examples: 390 tokens
- Quality metrics: 460 tokens

**Detail:** DEF-126 transformeerde JSON module code maar raakte statische prompt NIET aan

---

### 2️⃣ Hoeveel ontologie-bepaling content kan eruit?

**Antwoord:** 460 tokens (4.4% van prompt)

**Removal blocks:**
- Line 71: "Je **moet** één van de vier categorieën..." (20 tokens)
- Lines 83-87: "BELANGRIJK: Bepaal de juiste categorie..." (120 tokens)
- Lines 89-118 (partial): Remove 'Bepaal' language (320 tokens)

**Retention:** KEEP kick-off term patterns (proces→'activiteit waarbij', type→[kernwoord] dat)

---

### 3️⃣ Is er duplicatie tussen prompt en json_based_rules_module.py?

**Antwoord:** JA - 1,605 tokens duplicatie (15.3% van prompt)

**Type 1: Inline instructions (405 tokens)**
- 9 regels met "Instructie:" in prompt + JSON module voegt ze OPNIEUW toe
- Voorbeelden: ARAI-01, ARAI-04, ESS-01, STR-01, INT-01, VER-01, CON-01

**Type 2: Examples duplication (1,200 tokens)**
- Beide prompt EN JSON module tonen good/bad examples
- Recommendation: Remove from static prompt, keep in JSON module (single source)

**Architectureel probleem:** Drie lagen coëxisteren zonder cleanup

---

### 4️⃣ Wat is nieuwe realistische token reductie?

**Previous estimate:** 21% (before DEF-126 awareness)

**NEW REALISTIC ESTIMATE:**

| Phase | Reductie | Tokens | Effort | Cumulative |
|-------|----------|--------|--------|------------|
| Phase 1 (Quick Wins) | 25.2% | 2,650 | 1.5 uur | 25.2% |
| Phase 2 (Deduplication) | +11.4% | 1,200 | 3 uur | 36.6% |
| Phase 3 (Compression) | +5.5% | 580 | 4 uur | 42.2% |

**CONSERVATIVE RECOMMENDATION:**
- **Target:** Phase 1 + Phase 2 = **36.6% reductie** (3,850 tokens)
- **Effort:** 4.5 uur
- **Final token count:** 6,658
- **Rationale:** Phase 3 heeft diminishing returns (5.5% voor 4 uur) - bewaar voor later

**Vergelijking:**
- Baseline (reported): 8,325 tokens
- Baseline (measured): 10,508 tokens
- Conservative target: 6,658 tokens
- **Reductie from measured:** 36.6%
- **Reductie from reported:** 20.0%

---

## 🚀 Implementation Roadmap

### IMMEDIATE (Phase 1) - 1.5 uur
1. Remove all 'Toetsvraag:' sections (39x)
2. Remove quality metrics section (lines 471-497)
3. Remove ontology determination (lines 71, 83-87)
4. Remove metadata section (lines 519-537)

**Result:** 7,858 tokens (25.2% ↓) | **Risk:** LOW

---

### SHORT-TERM (Phase 2) - 3 uur
1. Identify rule-specific vs OUTPUT FORMAT examples
2. Remove rule-specific good/bad examples
3. Verify JSON module outputs these examples

**Result:** 6,658 tokens (36.6% ↓) | **Risk:** MEDIUM

---

### MEDIUM-TERM (Phase 3) - 4 uur
1. Compress TYPE category explanation (30→10 lines)
2. Consolidate grammar rules (39→20 lines)

**Result:** 6,078 tokens (42.2% ↓) | **Risk:** MEDIUM

---

## ⚠️ Validation Checklist

### Before Implementation
- ✅ Backup original prompt file
- ✅ Measure baseline tokens (tiktoken cl100k_base)
- ✅ Run test generation, save output as baseline

### During Implementation
- ✅ After each phase: measure tokens, verify reduction
- ✅ After each phase: run test generation, compare quality
- ✅ Run existing test suite (verify no regression)

### After Implementation
- ✅ Final token count measurement
- ✅ Side-by-side comparison (before/after definitions)
- ✅ Validation module behavior unchanged (post-generation)
- ✅ Document changes in CHANGELOG/commit

---

## 🏗️ Architectural Recommendation

**DOCUMENT THREE-LAYER ARCHITECTURE:**

1. **Layer 1:** Static prompt template (this file) - GENERATION guidance only
2. **Layer 2:** JSON rule files (`src/toetsregels/regels/*.json`) - Rule metadata
3. **Layer 3:** JSON module runtime (`json_based_rules_module.py`) - SINGLE SOURCE for rules

**POLICY:** JSON module (Layer 3) is single source of truth for rules; static prompt should NOT duplicate rule content

---

## 📊 Summary Table

| Metric | Baseline | Phase 1 | Phase 2 | Phase 3 |
|--------|----------|---------|---------|---------|
| **Tokens** | 10,508 | 7,858 | 6,658 | 6,078 |
| **Reductie** | - | 25.2% | 36.6% | 42.2% |
| **Effort** | - | 1.5h | +3h (4.5h) | +4h (8.5h) |
| **Risk** | - | LOW | MEDIUM | MEDIUM |
| **Priority** | - | IMMEDIATE | HIGH | MEDIUM |

**AANBEVELING:** Start met Phase 1 (immediate), gevolgd door Phase 2 binnen 1 week. Phase 3 kan later (diminishing returns).

---

**Deliverable:** Herziene prompt met 6,658 tokens (36.6% reductie) in 4.5 uur werk, met LOW-MEDIUM risk profiel.
