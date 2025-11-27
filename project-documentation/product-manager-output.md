# Product Manager Analyse: Issue Prioritering DefinitieAgent

**Datum:** 2025-11-27
**Auteur:** Product Manager (AI-assisted)
**Versie:** 2.0
**Project:** DefinitieAgent - Juridische Definitie Generator

---

## Executive Summary

### Elevator Pitch
DefinitieAgent genereert juridische definities met GPT-4, maar de huidige prompt kwaliteit scoort slechts 5.2/10 door conflicterende regels en cognitieve overload.

### Problem Statement
De solo developer heeft 30+ issues in verschillende staten, zonder duidelijke prioritering. De kern-vraag: **welk issue levert de meeste waarde op in de kortste tijd?**

### Aanbeveling
**Start met DEF-154** (30 min, Quick Win), gevolgd door **DEF-186 Stap 1+2** (35 min), dan **DEF-183/DEF-184** (30 min totaal). Daarna pas DEF-38 (groot issue).

### Success Metrics
- Definitie kwaliteit: 5.2/10 naar 7.0/10 (binnen 2 weken)
- Token efficiency: -25% prompt tokens
- Development velocity: 3-4 issues/week

---

## Analyse Resultaten

### RICE Score Berekening

| Issue | Reach | Impact | Confidence | Effort (h) | RICE Score |
|-------|-------|--------|------------|------------|------------|
| **DEF-154** | 100% | 2 | 90% | 0.5 | **360** |
| DEF-186 (Stap 1+2) | 100% | 3 | 90% | 0.6 | **450** |
| DEF-183 | 10% | 1 | 90% | 0.25 | 36 |
| DEF-184 | 10% | 1 | 90% | 0.25 | 36 |
| DEF-38 | 100% | 4 | 70% | 14 | 20 |
| DEF-123 | 100% | 2 | 60% | 5 | 24 |
| DEF-135 | 100% | 2 | 70% | 5 | 28 |
| DEF-185 | 50% | 1 | 80% | 5 | 8 |

**Conclusie:** DEF-186 en DEF-154 hebben verreweg de hoogste RICE scores.

---

### MoSCoW Classificatie

#### Must Have (Week 1)
| Issue | Reden | Effort |
|-------|-------|--------|
| DEF-154 | Verwijdert conflicterende instructies die GPT-4 verwarren | 30 min |
| DEF-186 (Stap 1+2) | +25-35% kwaliteitsverbetering, vervangt DEF-149 | 35 min |
| Close DEF-149 | Superseded door DEF-186 | 5 min |

#### Should Have (Week 2-3)
| Issue | Reden | Effort |
|-------|-------|--------|
| DEF-183 | Fix singleton bypass DUP_01.py | 15 min |
| DEF-184 | Fix singleton bypass synonym_service | 15 min |
| DEF-38 (Quick Wins) | PROCES + EXEMPLAAR fixes (4 uur) | 4 uur |

#### Could Have (Week 4-6)
| Issue | Reden | Effort |
|-------|-------|--------|
| DEF-135 | Transform validation rules to instructions | 5 uur |
| DEF-123 | Context-aware module loading | 5 uur |
| DEF-106 | Create PromptValidator | 2 uur |

#### Won't Have (Defer)
| Issue | Reden |
|-------|-------|
| DEF-179 | 16 uur UI refactoring - no user-facing benefit |
| DEF-180 | Docstring coverage - nice to have |
| DEF-117 | Repository refactoring - no urgency |

---

### Dependency Analysis

```
DEF-186 ────────> Replaces DEF-149 (CLOSE DEF-149)
    |
    v
DEF-38 (Quick Wins) ────────> DEF-40 (depends on DEF-38)
    |
    v
DEF-135 ────────> DEF-106 (validator needs instruction-style rules)
```

**Critical Path:**
1. DEF-154 (independent, do first)
2. DEF-186 (replaces DEF-149)
3. DEF-38 Quick Wins (enables DEF-40)
4. DEF-135 (enables better validation)

---

### Quick Wins Matrix

| Issue | Impact | Effort | ROI | Priority |
|-------|--------|--------|-----|----------|
| DEF-154 | HIGH | 30 min | EXCELLENT | 1 |
| DEF-186 (Step 1) | HIGH | 5 min | EXCELLENT | 2 |
| DEF-186 (Step 2) | HIGH | 30 min | EXCELLENT | 3 |
| DEF-183 | LOW | 15 min | GOOD | 4 |
| DEF-184 | LOW | 15 min | GOOD | 5 |
| DEF-182 | LOW | 1 uur | MEDIUM | 6 |

---

### User Value vs Technical Debt Matrix

```
                    HIGH USER VALUE
                         |
    DEF-38 (kwaliteit)   |   DEF-186 (context)
    DEF-40 (categories)  |   DEF-154 (contradictions)
                         |
LOW TECH DEBT ───────────┼─────────── HIGH TECH DEBT
                         |
    DEF-135 (transform)  |   DEF-185 (duplicate services)
    DEF-106 (validator)  |   DEF-183/184 (singletons)
                         |
                    LOW USER VALUE
```

**Focus Quadrant:** HIGH USER VALUE + LOW TECH DEBT = DEF-186, DEF-154

---

## JSON Output

```json
{
  "recommended_first_issue": "DEF-154",
  "rationale": "Highest RICE score (360) for a 30-minute task. Removes conflicting word_type_advice from ExpertiseModule that confuses GPT-4. Zero dependencies, immediate quality improvement. After completing DEF-154, immediately proceed to DEF-186 Step 1+2 (35 min total) for +25-35% quality boost.",
  "rice_scores": {
    "DEF-154": 360,
    "DEF-186_steps_1_2": 450,
    "DEF-183": 36,
    "DEF-184": 36,
    "DEF-38": 20,
    "DEF-123": 24,
    "DEF-135": 28,
    "DEF-185": 8
  },
  "moscow_classification": {
    "must_have": ["DEF-154", "DEF-186", "CLOSE:DEF-149"],
    "should_have": ["DEF-183", "DEF-184", "DEF-38_quick_wins"],
    "could_have": ["DEF-135", "DEF-123", "DEF-106", "DEF-40"],
    "wont_have": ["DEF-179", "DEF-180", "DEF-117"]
  },
  "dependency_order": [
    "DEF-154 (independent - START HERE)",
    "DEF-186 Step 1+2 (replaces DEF-149)",
    "CLOSE DEF-149 (superseded)",
    "DEF-183 (singleton fix)",
    "DEF-184 (singleton fix)",
    "DEF-38 Quick Wins (4h subset)",
    "DEF-135 (after DEF-38)",
    "DEF-106 (after DEF-135)"
  ],
  "quick_wins": [
    {
      "issue": "DEF-154",
      "effort": "30 min",
      "impact": "Remove contradictions",
      "tokens_saved": 100
    },
    {
      "issue": "DEF-186 Step 1",
      "effort": "5 min",
      "impact": "Priority boost context module",
      "tokens_saved": 0
    },
    {
      "issue": "DEF-186 Step 2",
      "effort": "30 min",
      "impact": "+25-35% quality",
      "tokens_saved": 150
    },
    {
      "issue": "DEF-183",
      "effort": "15 min",
      "impact": "Fix singleton bypass",
      "tokens_saved": 0
    },
    {
      "issue": "DEF-184",
      "effort": "15 min",
      "impact": "Fix singleton bypass",
      "tokens_saved": 0
    }
  ],
  "90_day_roadmap": [
    {
      "week": "1",
      "theme": "Quick Wins",
      "issues": ["DEF-154", "DEF-186 Step 1+2", "CLOSE DEF-149"],
      "expected_quality": "5.2 -> 6.0",
      "effort_hours": 1.5
    },
    {
      "week": "2",
      "theme": "Singleton Fixes + DEF-38 Start",
      "issues": ["DEF-183", "DEF-184", "DEF-38 PROCES fix", "DEF-38 EXEMPLAAR fix"],
      "expected_quality": "6.0 -> 6.5",
      "effort_hours": 6
    },
    {
      "week": "3-4",
      "theme": "DEF-38 Completion",
      "issues": ["DEF-38 TYPE fix", "DEF-38 BFO foundations"],
      "expected_quality": "6.5 -> 7.0",
      "effort_hours": 10
    },
    {
      "week": "5-6",
      "theme": "Instruction Optimization",
      "issues": ["DEF-135", "DEF-123"],
      "expected_quality": "7.0 -> 7.5",
      "effort_hours": 10
    },
    {
      "week": "7-8",
      "theme": "Validation & Automation",
      "issues": ["DEF-106", "DEF-40"],
      "expected_quality": "7.5 -> 8.0",
      "effort_hours": 8
    },
    {
      "week": "9-12",
      "theme": "Technical Debt Reduction",
      "issues": ["DEF-185", "DEF-182", "DEF-186 Step 3"],
      "expected_quality": "8.0 (stable)",
      "effort_hours": 10
    }
  ]
}
```

---

## Feature Specifications

### Feature: DEF-154 - Remove Conflicting word_type_advice

**User Story:** Als definitie-gebruiker wil ik consistente instructies krijgen zodat GPT-4 niet verward raakt door conflicterende adviezen.

**Acceptance Criteria:**
- Given ExpertiseModule is geladen, when word_type_advice method wordt aangeroepen, then geen output (method verwijderd)
- Given een deverbaal woord, when definitie wordt gegenereerd, then alleen ontologische categorie bepaalt format
- Edge case: werkwoorden krijgen GEEN "definieer als proces" advice meer

**Priority:** P0 - Quick Win met hoogste RICE
**Dependencies:** Geen
**Technical Constraints:** Behoud _bepaal_woordsoort() voor andere modules
**UX Considerations:** Geen UI impact, alleen prompt quality

---

### Feature: DEF-186 - Context Mechanism Teaching

**User Story:** Als definitie-gebruiker wil ik dat GPT-4 context IMPLICIET verwerkt via 3 mechanismen (vocabulaire, scope, relaties) in plaats van patroon-herkenning.

**Acceptance Criteria:**
- Given context module priority is 90, when prompt wordt gebouwd, then context instructies verschijnen voor grammar (priority 80)
- Given 3 mechanismen zijn toegevoegd, when strafrechtelijke term wordt gegenereerd, then "recidive" verschijnt ipv "herhaling"
- Edge case: bij geen context, minimale instructies toch aanwezig

**Priority:** P0 - Vervangt DEF-149 met 4x betere ROI
**Dependencies:** DEF-149 moet gesloten worden
**Technical Constraints:** Maximaal +150 tokens
**UX Considerations:** Definitie kwaliteit direct zichtbaar voor gebruiker

---

## Critical Questions Checklist

- [x] Zijn er bestaande oplossingen? **Ja, DEF-149 bestaat maar is inferieur aan DEF-186**
- [x] Wat is de minimum viable versie? **DEF-154 + DEF-186 Step 1+2 = 1.5 uur**
- [x] Potentiele risico's? **DEF-38 is 14 uur - kan scope creep veroorzaken**
- [x] Platform-specifieke requirements? **Streamlit SessionStateManager constraints**
- [ ] GAPS: Hoeveel definities worden nu gegenereerd per dag/week?
- [ ] GAPS: Wat is de huidige user satisfaction score?
- [ ] GAPS: Zijn er concrete deadlines of stakeholder verwachtingen?

---

## Aanbevolen Eerste Actie

### Vandaag (1.5 uur totaal):

1. **DEF-154** (30 min)
   - Open `src/services/prompts/modules/expertise_module.py`
   - Verwijder `_build_word_type_advice()` method (lines 169-185)
   - Verwijder invocation in `execute()` (lines 86-88)
   - Run tests

2. **DEF-186 Step 1** (5 min)
   - Open `src/services/prompts/modules/context_awareness_module.py`
   - Wijzig `priority=70` naar `priority=90` (line 38)

3. **DEF-186 Step 2** (30 min)
   - Voeg IMPLICIT_CONTEXT_MECHANISMS toe aan alle 3 context niveaus
   - Run tests

4. **Close DEF-149** (5 min)
   - Linear: Mark as "Superseded by DEF-186"
   - State: Duplicate/Canceled

5. **DEF-183 + DEF-184** (30 min)
   - Fix singleton bypasses
   - Run tests

**Verwacht resultaat:** Kwaliteit 5.2 -> 6.0 in 1.5 uur werk.

---

## Appendix: Issue Status Update Recommendations

| Issue | Current State | Recommended Action |
|-------|---------------|-------------------|
| DEF-149 | In Progress | CLOSE (Superseded by DEF-186) |
| DEF-186 | Backlog | MOVE to In Progress |
| DEF-154 | In Progress | START (highest priority) |
| DEF-38 | In Progress | CONTINUE after Quick Wins |
| DEF-123 | In Progress | PAUSE (lower priority) |
| DEF-135 | In Progress | PAUSE (depends on DEF-38) |
| DEF-106 | In Progress | PAUSE (depends on DEF-135) |
| DEF-40 | In Progress | PAUSE (depends on DEF-38) |

---

## Appendix B: Blocking Issues Analysis

### Issues Currently "In Progress" (7 stuks)
Het feit dat 7 issues tegelijk "In Progress" zijn is een rode vlag voor een solo developer:

| Issue | Days in Progress | Recommendation |
|-------|-----------------|----------------|
| DEF-38 | 40+ dagen | CONTINUE - core issue |
| DEF-149 | 17 dagen | CLOSE - superseded |
| DEF-154 | 14 dagen | FINISH TODAY |
| DEF-123 | 20 dagen | PAUSE - lower priority |
| DEF-135 | 20 dagen | PAUSE - depends on DEF-38 |
| DEF-106 | 23 dagen | PAUSE - depends on DEF-135 |
| DEF-40 | 40+ dagen | PAUSE - depends on DEF-38 |

**Aanbeveling:** Reduceer "In Progress" naar max 2 issues tegelijk (WIP limit).

---

## Appendix C: Linear Backlog Cleanup Actions

### Immediate Actions (vandaag)
1. DEF-149: Change state to "Duplicate" with note "Superseded by DEF-186"
2. DEF-186: Move to "In Progress"
3. DEF-154: Finish implementation

### This Week Actions
4. DEF-123, DEF-135, DEF-106, DEF-40: Move back to "Backlog" (paused)
5. DEF-183, DEF-184: Move to "In Progress" after DEF-154

### Backlog Grooming (weekend)
6. Review all "No Priority" issues (12 stuks) - assign priority
7. Close stale issues (>60 dagen zonder activiteit)
8. Update estimates based on actual effort

---

*Document gegenereerd: 2025-11-27*
*Analyse methode: RICE + MoSCoW + Dependency Mapping + User Value Matrix*
*Data bron: Linear API real-time query*
