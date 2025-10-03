---
id: EPIC-026-LOGIC-EXTRACTION-DECISION-TREE
epic: EPIC-026
phase: 1
created: 2025-10-02
owner: senior-developer
status: draft
---

# Hardcoded Logic Extraction - Decision Tree

**Purpose:** Visual decision framework for extraction sequence and approach

---

## Decision 1: Should We Extract Hardcoded Logic?

```
┌─────────────────────────────────────────────────────────────┐
│ QUESTION: Is hardcoded business logic blocking refactoring? │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Analyze Impact  │
                    └─────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌─────────────┐
│ LOW Impact   │    │ MEDIUM Impact    │    │ HIGH Impact │
│ (<50 LOC)    │    │ (50-200 LOC)     │    │ (200+ LOC)  │
└──────────────┘    └──────────────────┘    └─────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌─────────────┐
│ SKIP         │    │ CONSIDER         │    │ EXTRACT     │
│ Extract later│    │ Extract if time  │    │ IMMEDIATELY │
└──────────────┘    └──────────────────┘    └─────────────┘
                                                    │
                                                    ▼
                                            ┌───────────────┐
                                            │ OUR SITUATION │
                                            │ 250+ LOC      │
                                            │ 93 instances  │
                                            │ CRITICAL!     │
                                            └───────────────┘
```

**OUR ANSWER:** ✅ YES - Extract immediately (250+ LOC, 93 instances, blocks refactoring)

---

## Decision 2: When Should We Extract?

```
┌─────────────────────────────────────────────────────────┐
│ QUESTION: Extract BEFORE, DURING, or AFTER refactoring? │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Evaluate Options│
                    └─────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌─────────────┐
│ BEFORE       │    │ DURING           │    │ AFTER       │
│ Refactoring  │    │ Refactoring      │    │ Refactoring │
└──────────────┘    └──────────────────┘    └─────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌─────────────┐
│ PROS:        │    │ PROS:            │    │ PROS:       │
│ • Lower risk │    │ • Faster overall │    │ • Services  │
│ • Simpler    │    │ • Single phase   │    │   separated │
│ • Testable   │    │                  │    │   first     │
│              │    │ CONS:            │    │             │
│ CONS:        │    │ • HIGH RISK!     │    │ CONS:       │
│ • +2 weeks   │    │ • 2 changes at   │    │ • Hardcoded │
│              │    │   once           │    │   logic in  │
│              │    │ • Hard to debug  │    │   NEW code  │
│              │    │ • Cannot test    │    │ • Must      │
│              │    │   independently  │    │   refactor  │
│              │    │                  │    │   AGAIN     │
└──────────────┘    └──────────────────┘    └─────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌─────────────┐
│ RISK: LOW    │    │ RISK: CRITICAL   │    │ RISK: HIGH  │
│ Timeline: +2 │    │ Timeline: +0     │    │ Timeline: +3│
└──────────────┘    └──────────────────┘    └─────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌─────────────┐
│ ✅ CHOSEN    │    │ ❌ REJECTED      │    │ ❌ REJECTED │
└──────────────┘    └──────────────────┘    └─────────────┘
```

**OUR ANSWER:** ✅ EXTRACT BEFORE refactoring (parallel track)

---

## Decision 3: Parallel or Sequential?

```
┌──────────────────────────────────────────────────┐
│ QUESTION: Can extraction run parallel to design? │
└──────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Check Resources │
                    └─────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌─────────────┐
│ PARALLEL     │    │ SEQUENTIAL       │    │ HYBRID      │
│ (2 people)   │    │ (1 person)       │    │ (overlap)   │
└──────────────┘    └──────────────────┘    └─────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌─────────────┐
│ PROS:        │    │ PROS:            │    │ PROS:       │
│ • Faster     │    │ • No resource    │    │ • Flexible  │
│ • Design +   │    │   conflicts      │    │ • Lower     │
│   Extract    │    │ • Simpler coord. │    │   resource  │
│   overlap    │    │                  │    │   needs     │
│              │    │ CONS:            │    │             │
│ CONS:        │    │ • Slower (4 wks) │    │ CONS:       │
│ • 2 devs     │    │ • Blocks Phase 2 │    │ • Complex   │
│   needed     │    │   longer         │    │   timing    │
└──────────────┘    └──────────────────┘    └─────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌─────────────┐
│ Timeline:    │    │ Timeline:        │    │ Timeline:   │
│ 2 weeks      │    │ 4 weeks          │    │ 3 weeks     │
└──────────────┘    └──────────────────┘    └─────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌─────────────┐
│ ✅ CHOSEN    │    │ ❌ REJECTED      │    │ ⚠️ BACKUP   │
│ (if 2 devs   │    │ (too slow)       │    │ (if 1 dev)  │
│  available)  │    │                  │    │             │
└──────────────┘    └──────────────────┘    └─────────────┘
```

**OUR ANSWER:** ✅ PARALLEL (if 2 devs available), otherwise HYBRID

---

## Decision 4: Which Logic to Extract First?

```
┌───────────────────────────────────────────────────┐
│ QUESTION: Rule reasoning or pattern matching?    │
└───────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Analyze Priority│
                    └─────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌─────────────┐
│ RULE         │    │ PATTERN          │    │ BOTH        │
│ REASONING    │    │ MATCHING         │    │ PARALLEL    │
│ FIRST        │    │ FIRST            │    │             │
└──────────────┘    └──────────────────┘    └─────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌─────────────┐
│ COMPLEXITY:  │    │ COMPLEXITY:      │    │ COMPLEXITY: │
│ MEDIUM       │    │ HIGH             │    │ VERY HIGH   │
│ 13 rules     │    │ 42 patterns      │    │ 55 total    │
│ 1 method     │    │ 3 methods        │    │ 4 methods   │
│              │    │                  │    │             │
│ IMPACT:      │    │ IMPACT:          │    │ IMPACT:     │
│ definition_  │    │ tabbed_          │    │ Both files  │
│ generator_   │    │ interface        │    │             │
│ tab          │    │                  │    │             │
│              │    │ DUPLICATION:     │    │ RISK:       │
│              │    │ 100% (3 methods!)│    │ Too much    │
│              │    │                  │    │ at once     │
└──────────────┘    └──────────────────┘    └─────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌─────────────┐
│ ✅ CHOSEN    │    │ ⚠️ SECOND WEEK   │    │ ❌ REJECTED │
│ Week 1       │    │ Week 2           │    │ (too risky) │
└──────────────┘    └──────────────────┘    └─────────────┘
```

**OUR ANSWER:** ✅ Rule Reasoning FIRST (Week 1), then Pattern Matching (Week 2)

**Rationale:**
- Rule reasoning is simpler (1 method vs 3 methods)
- Lower duplication (1 method vs 100% duplication)
- Builds config infrastructure first
- Pattern extraction can reuse config loader

---

## Decision 5: How to Handle Backward Compatibility?

```
┌──────────────────────────────────────────────────┐
│ QUESTION: Ensure zero behavior change during?   │
└──────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Choose Strategy │
                    └─────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌─────────────┐
│ FACADE       │    │ FEATURE FLAG     │    │ DIRECT      │
│ WRAPPER      │    │ TOGGLE           │    │ REPLACEMENT │
└──────────────┘    └──────────────────┘    └─────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌─────────────┐
│ APPROACH:    │    │ APPROACH:        │    │ APPROACH:   │
│ Old method   │    │ Config toggle    │    │ Delete old  │
│ delegates to │    │ between old/new  │    │ Replace     │
│ new service  │    │                  │    │ with new    │
│              │    │                  │    │             │
│ PROS:        │    │ PROS:            │    │ PROS:       │
│ • Zero risk  │    │ • Easy rollback  │    │ • Clean     │
│ • Easy test  │    │ • A/B testing    │    │ • No debt   │
│ • Rollback   │    │                  │    │             │
│              │    │ CONS:            │    │ CONS:       │
│ CONS:        │    │ • Complex        │    │ • HIGH RISK │
│ • Thin layer│    │ • Tech debt      │    │ • No        │
│   remains    │    │ • Must remove    │    │   rollback  │
│              │    │   later          │    │             │
└──────────────┘    └──────────────────┘    └─────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌─────────────┐
│ ✅ CHOSEN    │    │ ⚠️ OVERKILL     │    │ ❌ REJECTED │
│ Thin wrapper │    │ (not needed)     │    │ (too risky) │
└──────────────┘    └──────────────────┘    └─────────────┘
```

**OUR ANSWER:** ✅ FACADE WRAPPER (thin delegation layer)

**Implementation:**
```python
# Keep old method signature
def _build_pass_reason(self, rule_id, text, begrip):
    """Thin wrapper - delegates to service."""
    service = get_rule_reasoning_service()
    return service.build_pass_reason(rule_id, text, begrip)
```

---

## Decision 6: How to Validate Extraction?

```
┌──────────────────────────────────────────────────┐
│ QUESTION: How to ensure behavior is unchanged?  │
└──────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Choose Test     │
                    │ Strategy        │
                    └─────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌─────────────┐
│ UNIT TESTS   │    │ INTEGRATION      │    │ BOTH        │
│ ONLY         │    │ TESTS ONLY       │    │             │
└──────────────┘    └──────────────────┘    └─────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌─────────────┐
│ PROS:        │    │ PROS:            │    │ PROS:       │
│ • Fast       │    │ • End-to-end     │    │ • Complete  │
│ • Isolated   │    │ • Catches all    │    │   coverage  │
│              │    │   regressions    │    │ • Fast unit │
│ CONS:        │    │                  │    │   + E2E int │
│ • Misses     │    │ CONS:            │    │             │
│   integration│    │ • Slow           │    │ CONS:       │
│   issues     │    │ • Setup heavy    │    │ • More work │
│              │    │                  │    │             │
└──────────────┘    └──────────────────┘    └─────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌─────────────┐
│ ❌ REJECTED  │    │ ⚠️ NOT ENOUGH    │    │ ✅ CHOSEN   │
└──────────────┘    └──────────────────┘    └─────────────┘
                                                    │
                                                    ▼
                                    ┌───────────────────────┐
                                    │ TEST STRATEGY:        │
                                    │                       │
                                    │ 1. Unit tests (fast)  │
                                    │    - Config loading   │
                                    │    - Service logic    │
                                    │    - 100% coverage    │
                                    │                       │
                                    │ 2. Backward compat    │
                                    │    - Old vs new       │
                                    │    - 11+ test cases   │
                                    │    - Parametrized     │
                                    │                       │
                                    │ 3. Integration tests  │
                                    │    - UI → Service     │
                                    │    - Zero regressions │
                                    │                       │
                                    │ 4. Performance        │
                                    │    - <10% overhead    │
                                    │    - Benchmarks       │
                                    └───────────────────────┘
```

**OUR ANSWER:** ✅ BOTH (unit + integration + backward compat + performance)

---

## Decision 7: Rollback Strategy

```
┌──────────────────────────────────────────────────┐
│ QUESTION: What if extraction fails?             │
└──────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Define Failure  │
                    │ Conditions      │
                    └─────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌─────────────┐
│ Tests fail   │    │ Performance bad  │    │ Timeline    │
│              │    │                  │    │ overrun     │
└──────────────┘    └──────────────────┘    └─────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌─────────────┐
│ ROLLBACK     │    │ OPTIMIZE         │    │ DESCOPE     │
│ IMMEDIATELY  │    │ OR ROLLBACK      │    │ OR EXTEND   │
└──────────────┘    └──────────────────┘    └─────────────┘
        │                     │                     │
        └─────────────────────┴─────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ ROLLBACK STEPS  │
                    └─────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────┐
    │ 1. Revert service integration commits       │
    │ 2. Restore hardcoded logic in UI methods    │
    │ 3. Re-run tests (confirm rollback)          │
    │ 4. Root cause analysis                      │
    │ 5. Update plan with fixes                   │
    │ 6. Schedule retry                           │
    └─────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ WHY ROLLBACK    │
                    │ IS EASY:        │
                    │                 │
                    │ • Thin wrapper  │
                    │ • Old code kept │
                    │ • Git branches  │
                    │ • Fast tests    │
                    └─────────────────┘
```

**OUR ANSWER:** ✅ Easy rollback via thin wrapper + git revert

---

## Final Decision Summary

| Decision | Question | Answer | Rationale |
|----------|----------|--------|-----------|
| **1. Extract?** | Should we extract logic? | ✅ YES | 250+ LOC, blocks refactoring |
| **2. When?** | Before/during/after refactor? | ✅ BEFORE | Lower risk, testable |
| **3. Parallel?** | Parallel or sequential? | ✅ PARALLEL | Faster (if 2 devs) |
| **4. Order?** | Which logic first? | ✅ Rules → Patterns | Simpler → Complex |
| **5. Compat?** | Backward compatibility? | ✅ Facade wrapper | Zero behavior change |
| **6. Testing?** | Test strategy? | ✅ Unit + Integration | Complete coverage |
| **7. Rollback?** | Rollback plan? | ✅ Git revert + thin wrapper | Easy recovery |

---

## Visual Timeline

```
EPIC-026 Phase 1: Design (Days 1-5)
═══════════════════════════════════════
Day 1: ✅ definitie_repository
Day 2: ✅ definition_generator_tab + tabbed_interface
Day 3: ⏳ web_lookup_service + validation_orchestrator_v2
Day 4: ⏳ Service boundary design
Day 5: ⏳ Migration plan

PARALLEL: Logic Extraction (Weeks 1-2)
═══════════════════════════════════════
Week 1: Rule Reasoning
├── Day 1-2: Config schema + loader
├── Day 3-4: RuleReasoningService
└── Day 5: Integration + tests

Week 2: Pattern Matching
├── Day 6-7: Pattern config schema
├── Day 8-9: OntologicalPatternService
└── Day 10: Integration + cleanup

EPIC-026 Phase 2: Extraction (Weeks 3-8)
═══════════════════════════════════════
DEPENDS ON: Logic extraction COMPLETE ✅
Week 3: LOW-RISK services
Week 4: MEDIUM-RISK services
Week 5-6: HIGH-RISK services
Week 7-8: CRITICAL services (god methods)
```

---

## Risk Decision Tree

```
┌─────────────────────────────────┐
│ Will logic extraction succeed?  │
└─────────────────────────────────┘
                │
                ▼
        ┌───────────────┐
        │ Assess Risks  │
        └───────────────┘
                │
    ┌───────────┼───────────┐
    ▼           ▼           ▼
┌────────┐  ┌────────┐  ┌────────┐
│ Config │  │Behavior│  │Perf.   │
│ Load   │  │ Change │  │ Impact │
└────────┘  └────────┘  └────────┘
    │           │           │
    ▼           ▼           ▼
┌────────┐  ┌────────┐  ┌────────┐
│MEDIUM  │  │MEDIUM  │  │LOW     │
│Impact  │  │Impact  │  │Impact  │
└────────┘  └────────┘  └────────┘
    │           │           │
    ▼           ▼           ▼
┌────────┐  ┌────────┐  ┌────────┐
│Schema  │  │Backward│  │Config  │
│Valid.  │  │Compat  │  │Caching │
│Tests   │  │Tests   │  │        │
└────────┘  └────────┘  └────────┘
    │           │           │
    └───────────┴───────────┘
                │
                ▼
        ┌───────────────┐
        │ ALL MITIGATED │
        │               │
        │ ✅ PROCEED   │
        └───────────────┘
```

---

## Go/No-Go Criteria

**GO Criteria (all must be met):**
- ✅ 2 developers available (senior dev + code architect)
- ✅ 2-week timeline acceptable
- ✅ EPIC-026 Phase 2 can wait for extraction
- ✅ Backward compatibility is mandatory
- ✅ Rollback plan accepted
- ✅ Config infrastructure can be built in 2 days
- ✅ Tests can be written in parallel

**NO-GO Criteria (any triggers stop):**
- ❌ Only 1 developer available (extend to 3-4 weeks)
- ❌ Cannot delay EPIC-026 Phase 2
- ❌ Backward compatibility not required (DANGEROUS!)
- ❌ No time for comprehensive testing
- ❌ Config infrastructure not feasible

**OUR STATUS:** ✅ ALL GO CRITERIA MET - PROCEED WITH EXTRACTION

---

**Status:** DRAFT - Decision Framework
**Full Plan:** See `hardcoded_logic_extraction_plan.md`
**Summary:** See `hardcoded_logic_extraction_summary.md`
**Author:** Senior Developer
**Date:** 2025-10-02
