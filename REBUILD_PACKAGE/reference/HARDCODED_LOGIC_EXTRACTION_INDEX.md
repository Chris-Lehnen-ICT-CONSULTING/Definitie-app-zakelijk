---
id: EPIC-026-HARDCODED-LOGIC-EXTRACTION-INDEX
epic: EPIC-026
phase: 1
created: 2025-10-02
owner: senior-developer
status: draft
priority: CRITICAL
---

# Hardcoded Logic Extraction - Documentation Index

**Created:** 2025-10-02
**Purpose:** Navigation hub for all hardcoded logic extraction documentation
**Context:** Parallel track to EPIC-026 Phase 1 (Design)

---

## Quick Navigation

| Need | Document | Size | Audience |
|------|----------|------|----------|
| **Complete Analysis** | [Full Plan](#full-plan) | 58KB | Architects, Tech Leads |
| **Executive Summary** | [Summary](#summary) | 10KB | All stakeholders |
| **Decision Framework** | [Decision Tree](#decision-tree) | 31KB | Product Owners, Architects |
| **Developer Guide** | [Quick Reference](#quick-reference) | 13KB | Developers implementing |

---

## Document Overview

### 1. Full Plan (COMPREHENSIVE)

**File:** `hardcoded_logic_extraction_plan.md`
**Size:** 58KB (61,957 characters)
**Read Time:** ~30 minutes
**Audience:** Architects, senior developers, tech leads

**Purpose:** Complete, detailed analysis and migration strategy

**Contents:**
- **Part 1:** Hardcoded Logic Inventory
  - 13 rule reasoning heuristics (70 LOC)
  - 42 ontological patterns (93 instances, 100% duplication!)
  - Complete code examples from source files

- **Part 2:** Data-Driven Design
  - `rule_reasoning_config.yaml` schema (complete)
  - `category_patterns.yaml` schema (complete)
  - Config loading infrastructure with Pydantic validation

- **Part 3:** Migration Strategy
  - Extraction sequence decision (BEFORE refactoring)
  - Timeline (2 weeks parallel track)
  - Backward compatibility approach (facade pattern)

- **Part 4:** Integration with EPIC-026
  - Dependency timeline
  - Service extraction impact analysis
  - Complexity reduction metrics (-250 LOC!)

- **Part 5:** Testing Strategy
  - Config validation tests
  - Service logic tests (100% coverage)
  - Backward compatibility tests (11+ cases)

- **Part 6:** Risk Assessment
  - Risk matrix (7 identified risks)
  - Detailed mitigation strategies
  - Rollback plan

- **Part 7:** Success Criteria
  - Definition of Done (12 checkpoints)
  - Validation checklist (25 items)

- **Part 8:** Code Examples
  - Before/after comparisons
  - Complete implementations
  - LOC reduction analysis

**When to Read:**
- Planning extraction implementation
- Reviewing architecture decisions
- Understanding technical details
- Writing implementation tickets

---

### 2. Summary (TL;DR)

**File:** `hardcoded_logic_extraction_summary.md`
**Size:** 10KB
**Read Time:** ~5 minutes
**Audience:** All stakeholders

**Purpose:** Executive summary with key points only

**Contents:**
- The Problem (TL;DR)
  - 2 critical categories of hardcoded logic
  - 250+ LOC to extract
  - Blocks EPIC-026 refactoring

- The Solution (TL;DR)
  - Extract to YAML configs
  - New services: RuleReasoningService, OntologicalPatternService
  - Config infrastructure

- Timeline (TL;DR)
  - 2 weeks parallel track
  - Week 1: Rule reasoning
  - Week 2: Patterns

- Impact (TL;DR)
  - -245 LOC complexity reduction
  - +1 week net timeline impact
  - Data-driven from Day 1

- Code Examples (TL;DR)
  - Before: 70 LOC hardcoded
  - After: 5 LOC delegated
  - Pattern duplication eliminated

**When to Read:**
- First introduction to extraction plan
- Quick status updates
- Executive briefings
- Deciding whether to read full plan

---

### 3. Decision Tree (VISUAL FRAMEWORK)

**File:** `hardcoded_logic_extraction_decision_tree.md`
**Size:** 31KB
**Read Time:** ~15 minutes
**Audience:** Product owners, architects, decision-makers

**Purpose:** Visual decision framework with rationale

**Contents:**
- **Decision 1:** Should we extract logic? (YES - 250+ LOC critical)
- **Decision 2:** When to extract? (BEFORE refactoring)
- **Decision 3:** Parallel or sequential? (PARALLEL if 2 devs)
- **Decision 4:** Which logic first? (Rules → Patterns)
- **Decision 5:** Backward compatibility? (Facade wrapper)
- **Decision 6:** Testing strategy? (Unit + Integration + Backward compat)
- **Decision 7:** Rollback plan? (Git revert + thin wrapper)

**Visual Aids:**
- Decision trees with pros/cons
- Timeline Gantt chart
- Risk assessment flowchart
- Go/No-Go criteria

**When to Read:**
- Making go/no-go decisions
- Understanding trade-offs
- Reviewing approach rationale
- Stakeholder presentations

---

### 4. Quick Reference (DEVELOPER GUIDE)

**File:** `hardcoded_logic_extraction_quick_ref.md`
**Size:** 13KB
**Read Time:** ~7 minutes (keep handy during work!)
**Audience:** Developers implementing extraction

**Purpose:** Practical guide for day-to-day implementation

**Contents:**
- The Numbers (at a glance)
- Timeline (visual)
- Deliverables checklist (Week 1 + Week 2)
- File structure
- Config examples (copy-paste ready)
- Code migration pattern (before/after)
- Testing checklist
- Rollback plan (step-by-step)
- Common pitfalls & solutions
- Daily standup template
- Acceptance criteria
- Commands cheat sheet
- Success metrics

**When to Read:**
- Daily during implementation
- Writing tests
- Debugging issues
- Standups and status updates
- Code review preparation

**Print and Keep Handy!**

---

## Reading Path by Role

### For Architects & Tech Leads

**Recommended Reading Order:**
1. **Summary** (5 min) - Get context
2. **Full Plan** (30 min) - Understand complete strategy
3. **Decision Tree** (15 min) - Review decision rationale
4. **Quick Reference** (7 min) - Know what developers will use

**Total Time:** ~1 hour

**Focus Areas:**
- Part 2 (Data-Driven Design) - Schema design review
- Part 3 (Migration Strategy) - Extraction sequence
- Part 6 (Risk Assessment) - Mitigation strategies

---

### For Product Owners & Managers

**Recommended Reading Order:**
1. **Summary** (5 min) - Understand the problem
2. **Decision Tree** (15 min) - See trade-offs and decisions
3. **Full Plan - Part 4** (5 min) - Impact on EPIC-026 timeline

**Total Time:** ~25 minutes

**Focus Areas:**
- Timeline impact (+1 week net)
- Success criteria
- Risk mitigation
- Go/No-Go criteria

---

### For Developers (Implementers)

**Recommended Reading Order:**
1. **Summary** (5 min) - Quick context
2. **Quick Reference** (7 min) - Daily guide
3. **Full Plan - Parts 5 & 8** (15 min) - Testing & examples
4. **Full Plan - Part 2** (10 min) - Schema details as needed

**Total Time:** ~37 minutes (then use Quick Ref daily)

**Focus Areas:**
- Config schemas (Part 2)
- Code examples (Part 8)
- Testing strategy (Part 5)
- Common pitfalls (Quick Ref)

---

### For Code Reviewers

**Recommended Reading Order:**
1. **Quick Reference - Acceptance Criteria** (2 min)
2. **Full Plan - Part 7** (5 min) - Success criteria
3. **Full Plan - Part 5** (10 min) - Testing requirements

**Total Time:** ~17 minutes

**Focus Areas:**
- Definition of Done checklist
- Backward compatibility requirements
- Test coverage expectations
- Code quality standards

---

## Key Metrics Summary

| Metric | Value | Source |
|--------|-------|--------|
| **Hardcoded Logic** | 13 rules + 42 patterns = 55 items | Full Plan Part 1 |
| **Total LOC** | 250 LOC hardcoded | Full Plan Part 1 |
| **Duplication** | 93 instances (100% for patterns) | Full Plan Part 1 |
| **Timeline** | 2 weeks (10 working days) | Full Plan Part 3 |
| **Complexity Reduction** | -245 LOC in services | Full Plan Part 4 |
| **Test Coverage** | 100% (unit + integration) | Full Plan Part 5 |
| **Performance Overhead** | <10% | Full Plan Part 6 |
| **Risk Severity** | CRITICAL (6 MEDIUM, 1 HIGH) | Full Plan Part 6 |
| **Net Timeline Impact** | +1 week | Full Plan Part 4 |

---

## Document Sizes & Read Times

```
┌─────────────────────────────────────────────────────┐
│ Document Size Comparison                            │
├─────────────────────────────────────────────────────┤
│ Full Plan              ████████████████████  58 KB  │
│ Decision Tree          ████████████          31 KB  │
│ Quick Reference        ███████               13 KB  │
│ Summary                █████                 10 KB  │
│ This Index             ██                     6 KB  │
├─────────────────────────────────────────────────────┤
│ TOTAL                  ███████████████████  118 KB  │
└─────────────────────────────────────────────────────┘

Read Time Estimates:
├── Summary:        5 minutes   (executives)
├── Decision Tree: 15 minutes   (decision-makers)
├── Quick Ref:      7 minutes   (developers - daily)
├── Full Plan:     30 minutes   (architects - one-time)
└── This Index:     3 minutes   (everyone)
```

---

## Visual Overview

```
┌─────────────────────────────────────────────────────┐
│         HARDCODED LOGIC EXTRACTION DOCS             │
└─────────────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   SUMMARY    │ │ DECISION     │ │ QUICK REF    │
│   (10 KB)    │ │ TREE (31 KB) │ │ (13 KB)      │
│              │ │              │ │              │
│ TL;DR for    │ │ Visual       │ │ Developer    │
│ executives   │ │ decision     │ │ daily guide  │
│              │ │ framework    │ │              │
└──────────────┘ └──────────────┘ └──────────────┘
        │               │               │
        └───────────────┼───────────────┘
                        ▼
                ┌──────────────┐
                │  FULL PLAN   │
                │  (58 KB)     │
                │              │
                │ Complete     │
                │ analysis &   │
                │ strategy     │
                └──────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Part 1       │ │ Part 2       │ │ Part 3       │
│ Inventory    │ │ Design       │ │ Strategy     │
└──────────────┘ └──────────────┘ └──────────────┘
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Part 4       │ │ Part 5       │ │ Part 6       │
│ Integration  │ │ Testing      │ │ Risks        │
└──────────────┘ └──────────────┘ └──────────────┘
        ▼               ▼
┌──────────────┐ ┌──────────────┐
│ Part 7       │ │ Part 8       │
│ Success      │ │ Examples     │
└──────────────┘ └──────────────┘
```

---

## Document Status

| Document | Status | Owner | Reviewers | Approval |
|----------|--------|-------|-----------|----------|
| Full Plan | DRAFT | Senior Developer | Code Architect, Tech Lead | Pending |
| Summary | DRAFT | Senior Developer | All stakeholders | Pending |
| Decision Tree | DRAFT | Senior Developer | Product Owner, Architect | Pending |
| Quick Reference | DRAFT | Senior Developer | Developers | Pending |
| This Index | DRAFT | Senior Developer | All | Pending |

**Next Steps:**
1. Review all documents (Est. 2025-10-03)
2. Incorporate feedback
3. Get approvals
4. Begin implementation (Est. 2025-10-04)

---

## Cross-References to Other EPIC-026 Docs

**Phase 1 Design Documents:**
- `definitie_repository_responsibility_map.md` (Day 1)
- `definition_generator_tab_responsibility_map.md` (Day 2) ← **Rule reasoning here**
- `tabbed_interface_responsibility_map.md` (Day 2) ← **Patterns here**
- `modern_web_lookup_service_responsibility_map.md` (Day 3 - pending)
- `validation_orchestrator_v2_responsibility_map.md` (Day 3 - pending)

**Daily Updates:**
- `epic-026-day-1.md` (definitie_repository analysis)
- `epic-026-day-2.md` (discovered hardcoded logic issues!) ← **Triggered this work**
- `epic-026-day-3.md` (pending)

**This Extraction Plan:**
- Runs PARALLEL to Day 3-5 of Phase 1 (Design)
- Must COMPLETE before Phase 2 (Extraction) starts
- Reduces complexity for service extraction

---

## Integration Points

**Before Logic Extraction:**
```
definition_generator_tab.py (2,525 LOC)
├── 70 LOC hardcoded rule reasoning  ← EXTRACT TO CONFIG
├── Service boundaries: 8 services
└── Target: ValidationResultsPresentationService

tabbed_interface.py (1,793 LOC)
├── 180 LOC hardcoded patterns (3x duplication!) ← EXTRACT TO CONFIG
├── Service boundaries: 7 services
└── Target: OntologicalCategoryService
```

**After Logic Extraction:**
```
Services use config-driven logic:
├── ValidationResultsPresentationService
│   └── RuleReasoningService (from config)
└── OntologicalCategoryService
    └── OntologicalPatternService (from config)

Extracted services are:
✅ Data-driven
✅ Testable
✅ Maintainable
✅ Configurable (no code changes!)
```

---

## FAQ

**Q: Why is this a separate track and not part of EPIC-026 Phase 2?**
A: Logic extraction must happen BEFORE service extraction to avoid refactoring services twice. See Decision Tree, Decision 2.

**Q: Can we skip logic extraction and do it later?**
A: Not recommended. Extracted services would have hardcoded logic, requiring a second refactoring pass. See Full Plan Part 4.

**Q: What if we only have 1 developer?**
A: Extend timeline to 3-4 weeks sequential. See Decision Tree, Decision 3 (HYBRID approach).

**Q: How do we ensure zero behavior change?**
A: Comprehensive backward compatibility tests (11+ cases) compare old vs new output. See Full Plan Part 5.

**Q: What's the rollback plan?**
A: Git revert + thin wrapper approach makes rollback easy. See Quick Reference - Rollback Plan.

**Q: Why YAML instead of JSON?**
A: YAML is more human-readable and supports comments. Config schemas are complex (13 rules, 42 patterns). See Full Plan Part 2.

**Q: Do we need Pydantic for validation?**
A: YES. Catches config errors at load time, not at runtime. Critical for production stability. See Full Plan Part 2.3.

---

## Links & Resources

**Internal Documentation:**
- Full Plan: `hardcoded_logic_extraction_plan.md`
- Summary: `hardcoded_logic_extraction_summary.md`
- Decision Tree: `hardcoded_logic_extraction_decision_tree.md`
- Quick Reference: `hardcoded_logic_extraction_quick_ref.md`
- This Index: `HARDCODED_LOGIC_EXTRACTION_INDEX.md`

**EPIC-026 Context:**
- Main Epic: `docs/backlog/EPIC-026/EPIC-026.md`
- Phase 1: `docs/backlog/EPIC-026/phase-1/`
- Day 2 Report: `epic-026-day-2.md` (identified this issue)

**Related Systems:**
- Validation Rules: `src/toetsregels/regels/*.json` (53 files)
- Ontological Categories: `src/domain/ontological_categories.py`
- Service Container: `src/services/container.py`

**External References:**
- Pydantic Documentation: https://docs.pydantic.dev/
- YAML Specification: https://yaml.org/spec/1.2/spec.html

---

## Changelog

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-10-02 | 1.0.0 | Initial creation | Senior Developer |
| | | - Created 4 comprehensive documents | |
| | | - Total: 118 KB documentation | |
| | | - All documents in DRAFT status | |

---

## Approval Workflow

```
┌─────────────────────────────────────┐
│ 1. Review Period (2025-10-03)      │
│    ├── Code Architect               │
│    ├── Tech Lead                    │
│    ├── Product Owner                │
│    └── Senior Developers            │
└─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│ 2. Feedback Incorporation           │
│    └── Update all docs if needed    │
└─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│ 3. Approval (2025-10-03 EOD)        │
│    ├── Architecture: Approved?      │
│    ├── Timeline: Approved?          │
│    ├── Risk Mitigation: Approved?   │
│    └── Resources: Approved?         │
└─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│ 4. Status: APPROVED                 │
│    └── Ready for implementation     │
└─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│ 5. Implementation (2025-10-04)      │
│    └── Begin Week 1 (Rule Reasoning)│
└─────────────────────────────────────┘
```

---

## Contact Information

**Document Owner:** Senior Developer
**Epic Owner:** Code Architect (EPIC-026)
**Reviewers:**
- Code Architect (architecture review)
- Tech Lead (technical review)
- Product Owner (timeline/resource review)

**Questions & Feedback:**
- Slack: #epic-026-refactoring
- Issues: Tag with `epic-026` and `logic-extraction`
- Email: [team distribution list]

---

**This index serves as the central navigation hub for all hardcoded logic extraction documentation. Start here to find the right document for your needs!**

**Last Updated:** 2025-10-02
**Version:** 1.0.0
**Status:** DRAFT - Pending Review
