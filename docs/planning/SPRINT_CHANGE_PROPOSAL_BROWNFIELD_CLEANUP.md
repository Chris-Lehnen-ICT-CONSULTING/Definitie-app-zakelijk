# Sprint Change Proposal: Brownfield Cleanup & Quality Infrastructure

**Date:** 2025-09-30
**Type:** Course Correction / Technical Debt Resolution
**Status:** Pending Approval
**Owner:** Architecture Team

---

## Executive Summary

Het DefinitieAgent project heeft een **60-80% discrepantie** tussen gedocumenteerde architectuur/werkwijze en daadwerkelijke implementatie. Dit resulteert in developer confusion, architecture violations, process breakdown, en ongecontroleerde technical debt accumulation.

**Recommended Action:** Dedicated 4-5 week brownfield cleanup initiative (EPIC-025) met 3 gefaseerde sprints om documentatie/code alignment te herstellen van 60% → 90% en quality enforcement te implementeren.

**Trade-off:** Feature development (EPIC-017) wordt gepauzeerd voor 4-5 weken in ruil voor sustainable development foundation.

---

## 1. Identified Issue

### Core Problem Statement

**60-80% discrepancy** tussen gedocumenteerde architectuur/werkwijze en daadwerkelijke implementatie, veroorzaakt door:

1. **Aspirational Documentation Presented as Current State**
   - Architecture docs beschrijven microservices, Kubernetes, PostgreSQL als "current"
   - Reality: Streamlit monolith, SQLite, service-oriented modules
   - 3000+ regels "dead documentation" (beschrijft niet-geïmplementeerde infrastructure)

2. **Architecture Violations**
   - 14 UI bestanden importeren direct vanuit database layer (omzeilen service layer)
   - 5 bestanden overschrijden 500-regel limiet dramatisch (2-4.7x over)
   - Deprecated naming conventions nog in gebruik (organizational_context vs organisatorische_context)

3. **Process Breakdown**
   - TDD workflow gedocumenteerd maar 80% mismatch met actual commits
   - 5.2% van stories heeft review document (moet 100% zijn)
   - Pre-commit hooks niet afgedwongen in CI

4. **Agent Instruction Conflicts**
   - 3 verschillende instruction bronnen (CLAUDE.md, UNIFIED_INSTRUCTIONS.md, AGENTS.md)
   - Unclear precedence en overlapping rules
   - Agent name mismatches tussen systemen

### Evidence

**Multi-Agent Analysis Results:**

- **📚 Doc Auditor:** 6 US-ID duplicaties, 270 canonical conflicts, INDEX.md 55→270 story mismatch
- **🏗️ Code Architect:** 5 files 2-4.7x over limiet (max 2339 LOC), 2066 LOC resilience duplicatie
- **⚙️ Process Guardian:** 72 scripts misplaced, 4 pre-commit vs 14 CI workflows, 80% workflow mismatch
- **🔍 Architecture Coherence:** 60% alignment score, 3000+ regels aspirational infrastructure docs

**Impact:**
- Blocked progress (impossible to add features consistently)
- Developer confusion (niet duidelijk welke regels/patterns te volgen)
- Quality gate bypass (geen enforcement)
- Technical debt compounds (geen sustainable foundation)

---

## 2. Epic Impact

### Current Epic (EPIC-017 - Active)

**Status:** Must be **PAUSED** for 4-5 weeks during cleanup

**Rationale:**
- Adding V2 iterative improvements to unstable codebase increases technical debt
- Risk of introducing new violations without enforcement gates
- Clean foundation required before feature expansion

**Action:**
- Update EPIC-017 status: Active → Deferred
- Add note: "Blocked by EPIC-025 (Brownfield Cleanup)"
- Expected resume: Week 6 (post-cleanup)

### Future Epics (19 Remaining)

**Status:** **NO SCOPE CHANGES** - all epics remain valid

**Impact:**
- Execution delay: Start after cleanup complete
- Better foundation: Cleaner basis voor implementation
- Higher velocity: Reduced technical debt friction

### New Epic Required

**EPIC-025: Brownfield Cleanup & Quality Infrastructure**

**Scope:**
- Duration: 4-5 weken (3 sprints)
- Priority: **P0** (blocker voor alle andere work)
- Stories: 7 (US-426 → US-434)
- Effort: ~91 hours

**Goals:**
1. Documentation/code alignment: 60% → 90%
2. Architecture violations: 14 → 0
3. Process enforcement: Automated quality gates
4. Agent clarity: 3 instruction sources → 1 unified approach

### Epic Status Standardization

**Current:** 12 different status values in use
- Active, active, ACTIVE
- Completed, completed, Voltooid
- Deferred, DEFERRED
- IN_UITVOERING, TE_DOEN, READY, Open, Nog te bepalen, proposed

**Target:** 4 canonical values
- `active` - Currently being worked on
- `completed` - Done and validated
- `deferred` - Paused/blocked
- `proposed` - Planned but not started

---

## 3. Artifact Impact

### Documents Requiring Updates

| Artifact | Impact | Changes Needed | Effort | Priority |
|----------|--------|----------------|--------|----------|
| **ENTERPRISE_ARCHITECTURE.md** | Major | Add AS-IS vs TO-BE sections, remove microservices claims | 4h | P0 |
| **SOLUTION_ARCHITECTURE.md** | Major | Move 3000+ lines infra to ROADMAP doc | 8h | P0 |
| **TECHNICAL_ARCHITECTURE.md** | Major | Update tech stack (SQLite), remove K8s/Docker/Terraform | 6h | P0 |
| **CLAUDE.md** | Medium | Resolve UNIFIED conflict, add agent mapping | 2h | P1 |
| **UNIFIED_INSTRUCTIONS.md** | Medium | Clarify precedence, deduplicate overlap | 2h | P1 |
| **INDEX.md** | Medium | Update counts (55→270), sync directory structure | 2h | P1 |
| **CANONICAL_LOCATIONS.md** | Low | Add missing dirs, update structure | 1h | P2 |
| **PRD (NEW)** | Medium | Create Brownfield Cleanup PRD | 4h | P1 |
| **270+ US files** | Medium | Normalize frontmatter (canonical, status) | 8h | P1 |
| **Scripts directory** | Low | Reorganize 72 files to subdirs | 1h | P2 |

**Total Documentation Effort:** ~38 hours

### Architecture Coherence Issues

**Current Alignment:** 60%

**Major Gaps:**
- Infrastructure as Code (K8s/Terraform): Documented but not implemented
- Database stack: PostgreSQL/Redis/Kafka documented, SQLite actual
- Microservices: 12 services documented, monolith actual
- Monitoring: Prometheus/ELK/Jaeger documented, basic logging actual

**Target Alignment:** 90% (realistic with AS-IS/TO-BE distinction)

---

## 4. Recommended Path Forward

### Selected Option: Option 3 - PRD MVP Review (Phased Rollout)

**Rationale:**

✅ **Structurele fixes met automation** (sustainable, prevents regression)
✅ **Clear scope met dedicated epic** (trackable progress)
✅ **Root cause oplossing** (niet alleen symptomen)
✅ **Long-term ROI** (4-5 weken → jaren clean development)

**Rejected Alternatives:**

❌ **Option 1 (Direct Adjustment):** Lost symptomen maar niet onderliggende proces issues, risk van half-fixed state
❌ **Option 2 (Rollback):** Recente commits zijn GOEDE refactoring, brownfield issues niet recent

### Trade-off Analysis

**Cost:**
- 4-5 weken feature development delay
- EPIC-017 paused
- ~91 hours effort investment

**Benefit:**
- 90% doc/code alignment (from 60%)
- Zero architecture violations (from 14)
- Enforced quality gates (automated)
- Resolved agent confusion
- Sustainable development foundation

**ROI:** After cleanup, feature velocity INCREASES (less technical debt friction)

---

## 5. Sprint Breakdown

### Sprint 1: Foundation Fixes (Week 1-2, ~35h)

**US-426: Fix Documentation Critical Issues**
- Fix 6 US-ID duplicaties (US-201→US-205, US-417)
- Update INDEX.md counts (55→270 stories)
- Normalize 270+ frontmatter files
- Reorganiseer scripts directory (72→subdirs)
- **Owner:** 📚 Doc Auditor Agent | **Effort:** 13h

**US-427: Split Gigantic UI Components**
- `definition_generator_tab.py`: 2339→3x ~700 LOC
- `definitie_repository.py`: 1800→3x ~600 LOC
- `tabbed_interface.py`: 1733→5x ~350 LOC
- **Owner:** 🏗️ Code Architect Agent | **Effort:** 20h

**US-428: Resolve Agent Instruction Conflicts**
- Update CLAUDE.md (add agent mapping)
- Clarify UNIFIED_INSTRUCTIONS precedence
- Document agent name translations
- **Owner:** ⚙️ Process Guardian Agent | **Effort:** 2h

**Sprint 1 Deliverables:**
- ✅ Zero US-ID conflicts
- ✅ All files < 800 LOC
- ✅ Single agent instruction source of truth
- ✅ Clean scripts organization

---

### Sprint 2: Process Enforcement (Week 3, ~24h)

**US-429: Implement CI Quality Gates**
- Add pre-commit verification job to CI
- Run preflight-checks.sh in GitHub Actions
- Block commits without pre-commit execution
- Add branch name validation
- **Owner:** ⚙️ Process Guardian Agent | **Effort:** 8h

**US-430: Extend Pre-commit Hooks**
- Add ruff check (local linting)
- Add pytest smoke tests
- Add forbidden pattern checks
- Add file size validation (500 LOC warning)
- **Owner:** 🏗️ Code Architect Agent | **Effort:** 6h

**US-431: Workflow Validation Automation**
- Create workflow-guard.py script
- Add phase-tracker.py for TDD workflow
- Create wip_tracker.sh for backlog visibility
- Add review-reminder post-commit hook
- **Owner:** ⚙️ Process Guardian Agent | **Effort:** 10h

**Sprint 2 Deliverables:**
- ✅ CI enforces pre-commit hooks
- ✅ 10+ automated quality checks active
- ✅ Workflow violations blocked automatically
- ✅ Real-time WIP visibility

---

### Sprint 3: Documentation Alignment (Week 4-5, ~32h)

**US-432: Update Architecture Documents**
- EA: Add AS-IS vs TO-BE distinction
- SA: Move 3000+ lines to INFRASTRUCTURE_ROADMAP.md
- TA: Update tech stack (SQLite reality)
- Create IMPLEMENTATION_STATUS.md dashboard
- **Owner:** 🔍 Architecture Coherence Agent | **Effort:** 18h

**US-433: Consolidate Code Duplicatie**
- Consolideer resilience modules (4→1, 2066→800 LOC)
- Remove exports/ duplicate directory
- Merge technical/→technisch/
- Replace print() met logging (top 5 files)
- **Owner:** 🏗️ Code Architect Agent | **Effort:** 10h

**US-434: Create Brownfield Cleanup PRD**
- Define new MVP goals
- Document success criteria
- Create epic/story breakdown
- Add to requirements traceability
- **Owner:** 📚 Doc Auditor Agent | **Effort:** 4h

**Sprint 3 Deliverables:**
- ✅ Architecture docs 90% aligned
- ✅ Code duplicatie reduced 70%
- ✅ NEW PRD canonical
- ✅ IMPLEMENTATION_STATUS dashboard live

---

## 6. Success Criteria

### Quantitative Targets

| Metric | Baseline | Target | Validation Method |
|--------|----------|--------|-------------------|
| **Doc/Code Alignment** | 60% | 90% | Coherence check script |
| **Files > 500 LOC** | 5 | 0 | `find src -name "*.py" -exec wc -l` |
| **Architecture Violations** | 14 | 0 | Grep for `from database.` in UI |
| **US-ID Conflicts** | 6 | 0 | `rg "^id: US-" \| uniq -d` |
| **Code Duplicatie (LOC)** | 2066 | <900 | Count resilience module lines |
| **CI Quality Checks** | 4 | 10+ | `pre-commit run --all` count |
| **Epic Status Values** | 12 | 4 | `grep "^status:" EPIC-*.md \| uniq` |
| **Agent Instruction Sources** | 3 | 1 | Unified approach documented |

### Qualitative Targets

✅ **Developer Onboarding:** New developer can understand codebase in < 2 days (from weeks)
✅ **Feature Velocity:** Post-cleanup features implement 30% faster (less debt friction)
✅ **Agent Clarity:** Agents know which instructions to follow without conflicts
✅ **Sustainable Foundation:** Quality gates prevent future regression

---

## 7. Risk Management

### High Risks

**Risk 1: Feature Pressure (Likelihood: HIGH)**
- **Impact:** Cleanup abandoned for urgent features
- **Mitigation:** Clear stakeholder communication upfront
- **Contingency:** Hotfix branch strategy for urgent features
- **Owner:** BMad Master

**Risk 2: Agent Context Loss (Likelihood: MEDIUM)**
- **Impact:** Agent can't continue story execution
- **Mitigation:** Detailed handoff documents per sprint
- **Contingency:** Re-run agent analysis (30 min)
- **Owner:** BMad Master

**Risk 3: Breaking Changes (Likelihood: MEDIUM)**
- **Impact:** Application doesn't start after refactoring
- **Mitigation:** Small atomic commits, smoke tests
- **Contingency:** Git revert to last stable commit
- **Owner:** Code Architect Agent

### Rollback Plan

**Trigger Scenarios:**
1. Sprint 1 < 50% complete at week 2 → Extend 1 week
2. Application breaks → Git revert + incremental rollout
3. Stakeholder pressure → Hotfix branch strategy
4. < 30% progress after Sprint 1 → Consider aborting

**Rollback Threshold:** If after 2 weeks < 30% progress, reassess approach

---

## 8. Agent Handoff Plan

### Agent Assignments

| Agent | Stories | Primary Responsibility |
|-------|---------|----------------------|
| **📚 Doc Auditor** | US-426, US-434 | Documentation fixes, PRD creation |
| **🏗️ Code Architect** | US-427, US-430, US-433 | Code refactoring, file splits, consolidation |
| **⚙️ Process Guardian** | US-428, US-429, US-431 | Workflow enforcement, automation |
| **🔍 Architecture Coherence** | US-432 | Architecture doc alignment |

### Handoff Sequence

**Sprint 1 Start (Week 1):**
- BMad Master → 📚 Doc Auditor (US-426)
- BMad Master → 🏗️ Code Architect (US-427)
- BMad Master → ⚙️ Process Guardian (US-428)

**Sprint 2 Start (Week 3):**
- Code Architect → Process Guardian (primary)
- Handoff: US-429, US-430, US-431

**Sprint 3 Start (Week 4):**
- Process Guardian → Architecture Coherence + Doc Auditor
- Handoff: US-432, US-433, US-434

### Daily Standup Format (Async)

**Agent Report Template:**
```
🤖 [Agent Name] Daily Report - [Date]

✅ Completed Yesterday:
- [Task 1]
- [Task 2]

🔄 Working On Today:
- [Task 1]
- [Task 2]

🚧 Blockers:
- [Blocker 1] (if any)

📊 Progress: [Story ID] [XX]% complete
```

---

## 9. Timeline & Milestones

### Week-by-Week Breakdown

**Week 0 (This Week):**
- User approval
- Execute quick wins (2h)
- Create EPIC-025 + 7 stories

**Week 1-2 (Sprint 1):**
- US-426, US-427, US-428
- Daily agent reports
- Sprint 1 review (end of week 2)

**Week 3 (Sprint 2):**
- US-429, US-430, US-431
- CI gates go live
- Sprint 2 review (end of week 3)

**Week 4-5 (Sprint 3):**
- US-432, US-433, US-434
- Architecture updates finalized
- Final validation & review

**Week 6:**
- Resume EPIC-017
- Normal feature development velocity restored

### Key Milestones

| Milestone | Date | Success Criteria |
|-----------|------|------------------|
| **Kickoff Complete** | Day 2 | EPIC-025 + stories created |
| **Sprint 1 Review** | Week 2 end | 80% targets met |
| **Sprint 2 Review** | Week 3 end | 90% targets met |
| **Sprint 3 Complete** | Week 5 end | 100% targets met |
| **EPIC-017 Resume** | Week 6 | Feature development restored |

---

## 10. Quick Wins (Parallel Track)

**Can be executed IMMEDIATELY (Today):**

1. **Fix datum typo** (5 min)
   - File: `TDD_TO_DEPLOYMENT_WORKFLOW.md` line 5
   - Change: "30-01-2025" → "30-09-2025"

2. **Remove empty directories** (5 min)
   ```bash
   find docs/backlog -type d -empty -delete
   ```

3. **Merge technical/ → technisch/** (15 min)
   ```bash
   mv docs/technical/* docs/technisch/
   rmdir docs/technical
   ```

4. **Archive development/ directory** (10 min)
   ```bash
   mv docs/development docs/archief/2025-09/development
   ```

5. **Add minimal frontmatter** (1h)
   ```bash
   bash scripts/add-frontmatter.sh
   ```

**Total Quick Wins:** ~2 hours
**Impact:** Immediate visible improvement, momentum builder

---

## 11. Approval Required

### Decision Points

**Please approve/reject the following:**

- [ ] **APPROVE** - Pause EPIC-017 for 4-5 weeks
- [ ] **APPROVE** - Create EPIC-025 (Brownfield Cleanup)
- [ ] **APPROVE** - Resource allocation (~91h effort)
- [ ] **APPROVE** - Agent assignments (4 agents)
- [ ] **APPROVE** - Success criteria (8 quantitative targets)
- [ ] **APPROVE** - Phased rollout approach (3 sprints)

### Signature

**Prepared By:** BMad Master (Change Navigation Agent)
**Date:** 2025-09-30
**Status:** Awaiting Approval

**Approved By:** ________________
**Date:** ________________

---

## 12. Next Steps (Post-Approval)

**Immediate Actions:**

1. Execute Quick Wins (2h)
2. Create EPIC-025 in backlog
3. Create 7 user stories (US-426→US-434)
4. Update EPIC-017 status (Active→Deferred)
5. Assign stories to agents
6. Schedule Sprint 1 kickoff

**Communication Plan:**

- Stakeholder announcement (why feature pause)
- Team notification (sprint structure)
- Daily async standup setup
- Weekly progress reports

---

## Appendix A: Agent Analysis Summary

See separate document: `AGENT_ANALYSIS_SUMMARY.md`

## Appendix B: Story Details

See individual story files in `/docs/backlog/EPIC-025/US-XXX/`

## Appendix C: Validation Scripts

All validation scripts referenced in this document available in `/scripts/validation/`

---

**End of Sprint Change Proposal**
