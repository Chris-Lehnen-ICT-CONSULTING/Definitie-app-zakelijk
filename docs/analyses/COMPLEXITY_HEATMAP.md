# COMPLEXITY HEATMAP - VISUAL ANALYSIS

**Generated:** November 6, 2025

This document provides visual representations of complexity hotspots in DefinitieAgent.

---

## COMPLEXITY HEATMAP BY FILE

```
🚨 = CRITICAL (Complexity >8/10) - Immediate action required
⚠️  = HIGH (Complexity 6-8/10) - Plan refactoring
✅ = GOOD (Complexity <6/10) - Acceptable

┌─────────────────────────────────────────────────────────────────┐
│ UI LAYER                                                        │
├─────────────────────────────────────────────────────────────────┤
│ definition_generator_tab.py    🚨🚨🚨🚨🚨🚨🚨🚨🚨 9.5/10 (2,412 LOC) │
│   ├─ _render_sources_section()    [Complexity: 108] 🚨          │
│   ├─ _render_generation_results() [Complexity: 68]  🚨          │
│   └─ _update_category()           [Complexity: 26]  ⚠️           │
│                                                                 │
│ definition_edit_tab.py         🚨🚨🚨🚨🚨🚨🚨🚨   8.5/10 (1,604 LOC) │
│   ├─ _render_search_results()     [Complexity: 36]  🚨          │
│   ├─ _render_editor()             [Complexity: 29]  🚨          │
│   └─ render()                     [Complexity: 17]  ⚠️           │
│                                                                 │
│ expert_review_tab.py           ⚠️⚠️⚠️⚠️⚠️⚠️⚠️    7.5/10 (1,417 LOC) │
│   ├─ _render_review_queue()       [Complexity: 27]  ⚠️           │
│   └─ _render_review_actions()     [Complexity: 21]  ⚠️           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ DATABASE LAYER                                                  │
├─────────────────────────────────────────────────────────────────┤
│ definitie_repository.py        ⚠️⚠️⚠️⚠️⚠️⚠️⚠️    7.0/10 (2,131 LOC) │
│   ├─ find_duplicates()            [Complexity: 21]  ⚠️           │
│   ├─ _sync_synonyms_to_registry() [Complexity: 20]  ⚠️           │
│   └─ save_voorbeelden()           [Complexity: 19]  ⚠️           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ SERVICE LAYER                                                   │
├─────────────────────────────────────────────────────────────────┤
│ definition_orchestrator_v2.py  ⚠️⚠️⚠️⚠️⚠️⚠️      6.5/10 (1,231 LOC) │
│   └─ 11-phase orchestration flow  [Acceptable]                 │
│                                                                 │
│ modular_validation_service.py  ⚠️⚠️⚠️⚠️⚠️⚠️      6.0/10 (1,631 LOC) │
│   └─ 46 rules orchestration       [Acceptable]                 │
│                                                                 │
│ interfaces.py                   ⚠️⚠️⚠️⚠️⚠️⚠️      6.5/10 (1,212 LOC) │
│   └─ 31 abstractions in 1 file   [Needs organization]          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ INFRASTRUCTURE LAYER                                            │
├─────────────────────────────────────────────────────────────────┤
│ CONFIG OVER-PROLIFERATION      🚨🚨🚨🚨🚨🚨🚨🚨   8.0/10 (5,291 LOC) │
│   ├─ 18 config files                                            │
│   ├─ 5.8% config-to-code ratio  (target: 1-2%)                 │
│   └─ 60-70% unused options                                     │
│                                                                 │
│ UTILITY SPRAWL                 ⚠️⚠️⚠️⚠️⚠️⚠️⚠️    7.0/10 (6,028 LOC) │
│   ├─ 19 utility modules                                         │
│   ├─ 5 resilience modules (80% duplicate)                      │
│   └─ 6.6% utility-to-code ratio (target: 3-4%)                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## CYCLOMATIC COMPLEXITY DISTRIBUTION

```
Distribution of 174 analyzed functions:

Simple (<5)          ████████████░░░░░░░░░░  45 (26%) ✅
Manageable (5-10)    ████████████████████░░  68 (39%) ✅
Watch (10-15)        █████████░░░░░░░░░░░░░  32 (18%) ⚠️
Refactor (15-25)     ██████░░░░░░░░░░░░░░░░  22 (13%) ⚠️
CRITICAL (>25)       ██░░░░░░░░░░░░░░░░░░░░   7 (4%)  🚨

                     0%        50%       100%
```

**Critical Functions (Complexity >25):**
1. `_render_sources_section` - **108** 🚨🚨🚨
2. `_render_generation_results` - **68** 🚨🚨
3. `_render_search_results` - **36** 🚨
4. `_render_editor` - **29** 🚨
5. `_render_review_queue` - **27** ⚠️
6. `_update_category` - **26** ⚠️
7. `find_duplicates` - **21** ⚠️

---

## FUNCTION SIZE DISTRIBUTION

```
Functions by LOC:

<50 lines       ██████████████████░░░░░░░░░░  130 (75%) ✅
50-100 lines    █████░░░░░░░░░░░░░░░░░░░░░░░   27 (16%) ⚠️
100-200 lines   ███░░░░░░░░░░░░░░░░░░░░░░░░░   12 (7%)  ⚠️
>200 lines      █░░░░░░░░░░░░░░░░░░░░░░░░░░░    5 (3%)  🚨

                0%          50%         100%
```

**Largest Functions (>200 LOC):**
1. `_render_sources_section` - **297** 🚨
2. `_render_editor` - **273** 🚨
3. `_render_review_queue` - **270** 🚨
4. `save_voorbeelden` - **251** 🚨
5. `_render_search_results` - **186** ⚠️

---

## COMPLEXITY VS SIZE QUADRANT

```
                High Complexity
                      ▲
                      │
         [CRITICAL]   │   [CRITICAL]
         Refactor     │   Refactor
         Immediately  │   + Test
                      │
   Small ─────────────┼─────────────> Large
   Size              │              Size
                      │
         [Good]       │   [Watch]
         Keep as-is   │   Consider
                      │   Splitting
                      ▼
                Low Complexity


Position of Key Functions:

🚨 _render_sources_section (108, 297)      [Top-Right: CRITICAL - Large + Complex]
🚨 _render_generation_results (68, 369)    [Top-Right: CRITICAL - Large + Complex]
🚨 _render_search_results (36, 186)        [Top-Right: CRITICAL - Large + Complex]
🚨 _render_editor (29, 273)                [Top-Right: CRITICAL - Large + Complex]
⚠️  find_duplicates (21, 148)              [Top-Right: Watch - Medium + Complex]
⚠️  save_voorbeelden (19, 251)             [Top-Right: Watch - Large + Medium]
✅ Most other functions                     [Bottom-Left: Good - Small + Simple]
```

**Interpretation:**
- **Top-Right Quadrant (🚨):** Large + Complex = CRITICAL - Refactor immediately
- **Top-Left Quadrant:** Small + Complex = Refactor logic, extract to helper
- **Bottom-Right Quadrant (⚠️):** Large + Simple = Consider splitting for readability
- **Bottom-Left Quadrant (✅):** Small + Simple = GOOD - Keep as-is

---

## NESTING DEPTH HEATMAP

```
Max Nesting Depth Analysis:

Definition Generator Tab:
  _render_sources_section:      ████████ 8 levels 🚨
  _render_generation_results:   ███████  7 levels 🚨
  _update_category:             ██████   6 levels ⚠️

Definition Edit Tab:
  _render_editor:               ███████  7 levels 🚨
  _render_search_results:       ██████   6 levels ⚠️

Repository:
  find_duplicates:              █████    5 levels ⚠️
  save_voorbeelden:             █████    5 levels ⚠️

Target:                         ████     4 levels ✅

Legend:
█ = 1 nesting level
Target: <4 levels
Acceptable: 4-5 levels
High: 6-7 levels
Critical: 8+ levels
```

---

## LOC DISTRIBUTION BY LAYER

```
Total Codebase: 91,157 LOC

┌──────────────────────────────────────────────────────┐
│                                                      │
│  Services (37%)     ████████████████████             │
│  33,852 LOC         ✅ Well-organized                 │
│                                                      │
│  Validation (25%)   █████████████                    │
│  22,508 LOC         ✅ Modular (46 rules)             │
│                                                      │
│  UI (15%)           ████████                         │
│  13,346 LOC         🚨 God objects detected          │
│                                                      │
│  Utils (7%)         ███                              │
│  6,028 LOC          ⚠️  Utility sprawl                │
│                                                      │
│  Config (6%)        ███                              │
│  5,291 LOC          🚨 Over-configured               │
│                                                      │
│  Database (5%)      ███                              │
│  4,910 LOC          ⚠️  Business logic leakage        │
│                                                      │
│  Other (11%)        ██████                           │
│  10,513 LOC         ✅ Acceptable                     │
│                                                      │
└──────────────────────────────────────────────────────┘

0%              25%              50%
```

---

## OVER-ENGINEERING INDICATORS

```
Config Over-Proliferation:
Current:  ████████████████████░░░░░░░░░░  5,291 LOC (5.8%)
Target:   ████░░░░░░░░░░░░░░░░░░░░░░░░░░  1,823 LOC (2.0%)
Excess:   ████████████████░░░░░░░░░░░░░░  +3,468 LOC (+190%)

Utility Sprawl:
Current:  ████████████████░░░░░░░░░░░░░░  6,028 LOC (6.6%)
Target:   ████████░░░░░░░░░░░░░░░░░░░░░░  3,646 LOC (4.0%)
Excess:   ████████░░░░░░░░░░░░░░░░░░░░░░  +2,382 LOC (+65%)

Resilience Duplication:
Current:  █████████████████████████░░░░░  2,515 LOC (5 modules)
Target:   ████████████░░░░░░░░░░░░░░░░░░  1,264 LOC (1 module)
Excess:   █████████████░░░░░░░░░░░░░░░░░  +1,251 LOC (+99%)
```

---

## SIMPLIFICATION IMPACT VISUALIZATION

```
Before vs After Simplification:

Max Cyclomatic Complexity:
Before: ████████████████████████████████████████████████████████  108
After:  ███████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   15
Impact: ▼ 86% reduction

Avg Cyclomatic Complexity:
Before: ████████████░░░░░░░░░░░░░░░░░░░░  12.5
After:  ████████░░░░░░░░░░░░░░░░░░░░░░░░   8.0
Impact: ▼ 36% reduction

Files >1,500 LOC:
Before: ██████░░░░░░░░░░  6 files
After:  ██░░░░░░░░░░░░░░  2 files
Impact: ▼ 67% reduction

Config Files:
Before: ██████████████████░░░░  18 files
After:  ████████░░░░░░░░░░░░░░   8 files
Impact: ▼ 56% reduction

Overall Complexity Score (Lower is better):
Before: ████████░░░░░░░░░░░░░░░░░░░░░░  4.2/10
After:  █████░░░░░░░░░░░░░░░░░░░░░░░░░  2.5/10
Impact: ▼ 40% improvement
```

---

## EFFORT VS IMPACT MATRIX

```
                High Impact
                     ▲
                     │
    [Quick Wins]     │     [High Priority]
    Do First!        │     Plan carefully
                     │
    • Consolidate    │     • Decompose UI
      resilience     │       god objects
      (20h, 50%)     │       (40-60h, 56%)
                     │
    • Consolidate    │     • Extract repo
      config         │       logic
      (16h, 34%)     │       (16-24h, 44%)
                     │
Low ─────────────────┼────────────────────> High
Effort              │                    Effort
                     │
    [Nice-to-have]   │     [Watch]
    If time permits  │     Assess ROI
                     │
    • Organize       │     • Full UI rewrite
      interfaces     │       (avoid!)
      (12h, 26%)     │
                     │
                     ▼
                Low Impact


Recommended Order:
1. Quick Wins (Top-Left): 52-60h, high impact
2. High Priority (Top-Right): 56-84h, critical fixes
3. Nice-to-have (Bottom-Left): 16-18h, polish
```

---

## ROADMAP VISUALIZATION

```
Week 0  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        Current State
        • Max Complexity: 108
        • Config LOC: 5,291
        • Utility LOC: 6,028
        • Complexity Score: 4.2/10

        ▼

Week 1-2 ╔════════════════════════════════╗
         ║ Consolidate Resilience (20h)  ║
         ╚════════════════════════════════╝
         • 5 modules → 1 module
         • 2,515 → 1,264 LOC (50%)

         ▼

Week 3-4 ╔════════════════════════════════╗
         ║ Consolidate Config (16h)      ║
         ╚════════════════════════════════╝
         • 18 files → 8 files
         • 5,291 → 3,500 LOC (34%)

         ▼

Week 5-6 ╔════════════════════════════════╗
         ║ Extract God Methods (16-24h)  ║
         ╚════════════════════════════════╝
         • Complexity 108 → 15 (86%)
         • Complexity 68 → 10 (85%)

         ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
         Phase 1 Complete ✅
         • Complexity Score: 3.5/10 (-17%)
         • LOC Reduction: ~3,700 lines

         ▼

Week 7-10 ╔═══════════════════════════════════╗
          ║ Decompose UI God Objects (40-60h) ║
          ╚═══════════════════════════════════╝
          • definition_generator_tab: 2,412 → 800
          • definition_edit_tab: 1,604 → 900
          • expert_review_tab: 1,417 → 700

          ▼

Week 11-12 ╔═══════════════════════════════════╗
           ║ Extract Repository Logic (16-24h) ║
           ╚═══════════════════════════════════╝
           • definitie_repository: 2,131 → 1,200
           • Extract algorithms to services

           ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
           Phase 2 Complete ✅
           • Complexity Score: 2.8/10 (-20%)
           • LOC Reduction: ~4,000 lines

           ▼

Week 13-16 ╔═══════════════════════════════╗
           ║ Polish & Cleanup (16-18h)    ║
           ╚═══════════════════════════════╝
           • Organize interface file
           • Consolidate caching
           • Documentation

           ▼

Week 16  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
         Target State ✅
         • Max Complexity: 15 (-86%)
         • Config LOC: 3,500 (-34%)
         • Utility LOC: 3,777 (-37%)
         • Complexity Score: 2.5/10 (-40%)
         • Total LOC Reduction: 8,500 lines (9.3%)
```

---

## SUCCESS CRITERIA CHECKLIST

```
□ Phase 1 Complete (Weeks 1-8):
  ✓ Resilience modules: 5 → 1
  ✓ Config files: 18 → 8
  ✓ Max complexity: 108 → 15
  ✓ Complexity score: 4.2 → 3.5

□ Phase 2 Complete (Weeks 9-16):
  ✓ UI files >1,500 LOC: 3 → 0
  ✓ Repository complexity: 21 → 5
  ✓ Test coverage: 50% → 70%
  ✓ Complexity score: 3.5 → 2.8

□ Phase 3 Complete (Weeks 17-20):
  ✓ Interface file: organized into 5 modules
  ✓ Caching modules: 2 → 1
  ✓ Documentation: updated
  ✓ Complexity score: 2.8 → 2.5

□ Final Success Criteria:
  ✓ No god methods (complexity >25)
  ✓ All files <1,500 LOC
  ✓ Config ratio <3%
  ✓ Utility ratio <5%
  ✓ Overall complexity score <3.0/10
```

---

**Visual Analysis Complete**
**Next Steps:** Review full report `/docs/analyses/COMPLEXITY_ANALYSIS.md`
