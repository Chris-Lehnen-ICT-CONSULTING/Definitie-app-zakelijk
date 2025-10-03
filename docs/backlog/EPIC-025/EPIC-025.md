---
aangemaakt: 2025-09-30
applies_to: definitie-app@current
astra_compliance: false
bijgewerkt: 2025-09-30
canonical: true
completion: 0%
id: EPIC-025
last_verified: 2025-09-30
owner: architecture
prioriteit: P0
status: active
stories:
- US-426
- US-427
- US-428
- US-429
- US-430
- US-431
- US-432
- US-433
- US-434
target_release: v2.1
titel: "EPIC-025: Brownfield Cleanup - 60→90% doc/code alignment, 10+ CI gates, zero architecture violations (3 sprints)"
vereisten:
- REQ-089
- REQ-090
---

# EPIC-025: Brownfield Cleanup & Quality Infrastructure

## Epic Overview

**ID:** EPIC-025
**Titel:** Brownfield Cleanup & Quality Infrastructure
**Status:** ACTIVE
**Priority:** P0 (Blocker)
**Created:** 2025-09-30
**Owner:** Architecture Team
**Target Release:** v2.1

## Problem Statement

Het DefinitieAgent project heeft een **60-80% discrepantie** tussen gedocumenteerde architectuur/werkwijze en daadwerkelijke implementatie, resulterend in:

- Developer confusion (3 conflicterende instruction bronnen)
- Architecture violations (14 UI files met directe DB access)
- Process breakdown (TDD workflow niet toegepast, 5.2% review coverage)
- Code bloat (5 bestanden 2-4.7x over limiet, 2066 LOC duplicatie)

Dit blokkeert consistent feature development en accumuleert technical debt ongecontroleerd.

## Business Value

### Direct Benefits

1. **Developer Productivity** (+30%)
   - Onboarding tijd: Weken → Dagen
   - Feature velocity verhoogd door minder technical debt friction
   - Clear patterns & practices documented

2. **Code Quality** (+90% alignment)
   - Zero architecture violations
   - All files < 500 LOC (maintainable)
   - Automated quality gates prevent regression

3. **Documentation Reliability** (60% → 90%)
   - Architecture docs match reality
   - Developers trust documentation
   - Onboarding material accurate

4. **Process Enforcement** (Automated)
   - 10+ quality checks in CI
   - Pre-commit hooks enforced
   - Workflow violations blocked

### Risk Reduction

- **Reduced regression risk:** Smaller, tested files
- **Improved maintainability:** Clear ownership & patterns
- **Sustainable foundation:** Quality gates prevent future debt
- **Agent clarity:** No conflicting instructions

## Scope

### In Scope

**Sprint 1: Foundation Fixes (Week 1-2)**
- Fix 6 US-ID duplicaties
- Split 5 gigantic files (>500 LOC)
- Resolve 3 agent instruction conflicts
- Reorganize 72 misplaced scripts

**Sprint 2: Process Enforcement (Week 3)**
- Implement CI quality gates
- Extend pre-commit hooks (4→10+ checks)
- Add workflow validation automation
- Create WIP tracking tools

**Sprint 3: Documentation Alignment (Week 4-5)**
- Update architecture documents (EA/SA/TA)
- Consolidate code duplicatie (2066→800 LOC)
- Create brownfield cleanup PRD
- Generate IMPLEMENTATION_STATUS dashboard

### Out of Scope

- **Feature development:** EPIC-017 deferred tot na cleanup
- **Microservices migration:** Remains aspirational/roadmap
- **Infrastructure as Code:** K8s/Terraform blijft TO-BE
- **Database migration:** SQLite → PostgreSQL (future)
- **UI redesign:** Streamlit UI blijft unchanged

## Goals & Success Criteria

### Quantitative Targets

| Metric | Baseline | Target | Validation |
|--------|----------|--------|------------|
| Doc/Code Alignment | 60% | 90% | Coherence check script |
| Files > 500 LOC | 5 | 0 | `find src -exec wc -l` |
| Architecture Violations | 14 | 0 | Grep forbidden imports |
| US-ID Conflicts | 6 | 0 | `rg "^id: US-" \| uniq -d` |
| Code Duplicatie LOC | 2066 | <900 | Count resilience modules |
| CI Quality Checks | 4 | 10+ | pre-commit hook count |
| Epic Status Values | 12 | 4 | Canonical status values |

### Qualitative Targets

- ✅ New developer can understand codebase in < 2 days
- ✅ Feature velocity increases 30% post-cleanup
- ✅ Agents know which instructions to follow
- ✅ Quality gates prevent future regression

## Dependencies

### Blocked By
- None (kan direct starten)

### Blocks
- **EPIC-017:** Iteratieve Verbeteringen (paused tot cleanup compleet)
- **Future feature epics:** Require clean foundation

### Requires
- Multi-agent analysis complete ✅
- Sprint Change Proposal approved (pending)
- Stakeholder buy-in for 4-5 week feature pause

## Timeline

**Duration:** 4-5 weken (3 sprints)

**Sprint Breakdown:**
- **Week 1-2 (Sprint 1):** Foundation fixes (~35h)
- **Week 3 (Sprint 2):** Process enforcement (~24h)
- **Week 4-5 (Sprint 3):** Documentation alignment (~32h)

**Total Effort:** ~91 hours

**Milestone Dates:**
- Sprint 1 Review: End of Week 2
- Sprint 2 Review: End of Week 3
- Sprint 3 Complete: End of Week 5
- EPIC-017 Resume: Week 6

## User Stories

### Sprint 1: Foundation Fixes

- **US-426:** Fix Documentation Critical Issues (Doc Auditor, 13h)
- **US-427:** Split Gigantic UI Components (Code Architect, 20h)
- **US-428:** Resolve Agent Instruction Conflicts (Process Guardian, 2h)

### Sprint 2: Process Enforcement

- **US-429:** Implement CI Quality Gates (Process Guardian, 8h)
- **US-430:** Extend Pre-commit Hooks (Code Architect, 6h)
- **US-431:** Workflow Validation Automation (Process Guardian, 10h)

### Sprint 3: Documentation Alignment

- **US-432:** Update Architecture Documents (Architecture Coherence, 18h)
- **US-433:** Consolidate Code Duplicatie (Code Architect, 10h)
- **US-434:** Create Brownfield Cleanup PRD (Doc Auditor, 4h)

## Risks & Mitigation

### High Risks

**Risk 1: Feature Pressure**
- Likelihood: HIGH
- Impact: Cleanup abandoned for urgent features
- Mitigation: Clear stakeholder communication upfront
- Contingency: Hotfix branch strategy

**Risk 2: Agent Context Loss**
- Likelihood: MEDIUM
- Impact: Story execution blocked
- Mitigation: Detailed handoff documents
- Contingency: Re-run agent analysis

**Risk 3: Breaking Changes**
- Likelihood: MEDIUM
- Impact: Application doesn't start
- Mitigation: Small atomic commits, smoke tests
- Contingency: Git revert strategy

### Rollback Plan

**Trigger:** < 30% progress after Sprint 1
**Action:** Reassess approach, consider aborting
**Owner:** BMad Master

## Acceptance Criteria

### Definition of Done (Epic Level)

- [ ] All 7 user stories completed and validated
- [ ] All quantitative targets met (8/8)
- [ ] 10-test validation suite passes (100%)
- [ ] Architecture docs updated and reviewed
- [ ] CI quality gates active and enforced
- [ ] Documentation generated (IMPLEMENTATION_STATUS, ROADMAP)
- [ ] Sprint retrospective complete
- [ ] EPIC-017 unblocked and ready to resume

### Validation Tests

**Week 2 (Sprint 1):**
```bash
rg "^id: US-" docs/backlog | sort | uniq -d  # No duplicates
find src -name "*.py" -exec wc -l {} \; | awk '$1 > 500'  # No oversized
grep -c "conflict" CLAUDE.md  # Zero conflicts
```

**Week 3 (Sprint 2):**
```bash
gh workflow list | grep -c "preflight"  # >= 1
pre-commit run --all-files 2>&1 | grep -c "Passed"  # >= 10
ls scripts/workflow-guard.py scripts/wip_tracker.sh  # Exist
```

**Week 5 (Sprint 3 - FINAL):**
```bash
python scripts/coherence_check.py  # >= 90%
find src/utils -name "*resilience*.py" | wc -l  # 1-2 (was 4-5)
ls docs/architectuur/IMPLEMENTATION_STATUS.md  # Exists
```

## Notes

### Related Documentation

- **Sprint Change Proposal:** `docs/planning/SPRINT_CHANGE_PROPOSAL_BROWNFIELD_CLEANUP.md`
- **Agent Analysis:** `docs/planning/AGENT_ANALYSIS_SUMMARY.md`
- **Correct-Course Checklist:** `.bmad-core/checklists/change-checklist.md` (completed)

### Quick Wins (Parallel Track)

Can be executed immediately while planning sprints:

1. Fix datum typo in TDD_TO_DEPLOYMENT_WORKFLOW.md (5 min)
2. Remove empty directories (5 min)
3. Merge technical/ → technisch/ (15 min)
4. Archive development/ directory (10 min)
5. Add minimal frontmatter to 20 files (1h)

**Total:** ~2 hours, immediate impact

### Communication Plan

- **Stakeholder announcement:** Why feature pause (sent before Sprint 1)
- **Team notification:** Sprint structure & expectations
- **Daily async standups:** Agent progress reports
- **Weekly progress reports:** Metrics dashboard updates
- **Sprint reviews:** End of week 2, 3, 5

---

**Status:** Ready for approval and execution
**Next Action:** User approval → Create 7 user stories → Sprint 1 kickoff
