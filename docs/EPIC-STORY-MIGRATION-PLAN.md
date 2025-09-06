# 📋 EPIC-STORY MIGRATION PLAN

**Document Type:** Migration & Consolidation Strategy
**Version:** 1.0.0
**Status:** DRAFT
**Created:** 2025-09-05
**Owner:** Business Analyst Justice
**Applies To:** Definitie-app Project Management System

---

## Executive Summary

### Huidige Situatie
Het Definitie-app project heeft momenteel een **gefragmenteerde epic/story documentatie structuur** met significante inconsistenties en duplicaties:

- **1 Master Document**: `MASTER-EPICS-USER-STORIES.md` met 10 epics en 51+ stories
- **27 Losse Epic Files**: Verspreid over verschillende directories
- **30+ Story Files**: Inconsistent genummerd en gestructureerd
- **87 Requirements**: In individuele REQ-XXX.md bestanden (werkt wel goed)
- **Meerdere Archieven**: Met verborgen/vergeten epics en stories

### Kernprobleem
**Geen enkele bron van waarheid** - verschillende teams werken met verschillende documenten, waardoor:
- ⚠️ Duplicatie van werk
- ⚠️ Inconsistente statussen
- ⚠️ Verloren requirements
- ⚠️ Onvolledige traceability voor ASTRA/NORA compliance
- ⚠️ Merge conflicts bij updates

### Voorgestelde Oplossing
Migratie naar een **moderne, schaalbare backlog structuur** met:
- Individuele bestanden per epic/story (zoals requirements)
- Volledige frontmatter metadata
- Automatisch gegenereerde INDEX dashboards
- Business Analyst Justice agent voor beheer
- CI/CD validatie en quality gates

---

## 📊 Volledige Inventarisatie

### A. Master Document Content
**Locatie:** `/docs/stories/MASTER-EPICS-USER-STORIES.md`

| Epic ID | Title | Stories | Status | Priority |
|---------|-------|---------|--------|----------|
| Epic 1 | Basis Definitie Generatie | 5 | ✅ 100% Complete | HIGH |
| Epic 2 | Kwaliteitstoetsing | 8 | ✅ 100% Complete | HIGH |
| Epic 3 | Content Verrijking / Web Lookup | 1 | 🔄 30% In Progress | HIGH |
| Epic 4 | User Interface | 6 | 🔄 30% In Progress | MEDIUM |
| Epic 5 | Export & Import | 3 | ❌ 10% TODO | LOW |
| Epic 6 | Security & Auth | 4 | 🔄 40% In Progress | CRITICAL |
| Epic 7 | Performance & Scaling | 8 | 🔄 35% In Progress | HIGH |
| Epic 8 | Web Lookup Module | - | MERGED with Epic 3 | - |
| Epic 9 | Advanced Features | 6 | ❌ 5% TODO | LOW |
| Epic CFR | Context Flow Refactoring | 6 | 🚨 0% CRITICAL | CRITICAL |

**Totaal:** 10 actieve epics, 47 stories in master document

### B. Losse Epic/Story Documenten

#### Active Directory (`/docs/stories/`)
```
- epic-2-story-2.1-validation-interface.md ⚠️ DUPLICAAT
- epic-2-story-2.2-core-implementation.md ⚠️ DUPLICAAT
- epic-2-story-2.3-container-wiring.md ⚠️ DUPLICAAT
- epic-2-story-2.4-integration-migration.md ⚠️ DUPLICAAT
- epic-2-story-2.5-testing-qa.md ⚠️ DUPLICAAT
- epic-2-story-2.6-production-rollout.md ⚠️ DUPLICAAT
```
**Status:** Alle 6 files zijn duplicaten van content in MASTER document

#### Archief Directory (`/docs/archief/`)

##### Requirements Archief (`/docs/archief/requirements/`)
```
- EPIC-001-database-infrastructure.md 🆕 NIET IN MASTER
- EPIC-002-web-lookup-module.md ⚠️ Merged with Epic 3
- EPIC-003-ui-quick-wins.md 🆕 NIET IN MASTER
- EPIC-004-content-enrichment.md ⚠️ Overlap met Epic 3
- EPIC-005-tab-activation.md ⚠️ Overlap met Epic 4
- EPIC-006-prompt-optimization.md 🆕 NIET IN MASTER
- EPIC-007-test-suite-restoration.md 🆕 NIET IN MASTER
```
**Bevinding:** 4 epics in archief die NIET in master document staan!

##### Stories Archief (`/docs/archief/stories/`)
```
- COMPLETE-EPIC-OVERVIEW.md 📊 BELANGRIJK: Volledig overzicht alle 9 epics
- epic-1-story-1.3-v1-orchestrator-elimination.md
- epic-2-story-2.1-validation-interface.md
- epic-2-story-2.2-core-implementation.md
- epic-2-story-2.3-modular-validation-service.md
- epic-2-story-2.3-verhaal.md ⚠️ Duplicaat/variant
- epic-2-story-2.4-integration-migration.md
- epic-2-story-2.5-testing-qa.md
- epic-2-story-2.6-production-rollout.md
- epic-3-web-lookup-modernization.md
- epic-3-implementation-tracker.md
- epic-3-metadata-eerst-actieplan.md
- epic-3-user-stories.md
- epic-7-performance-optimization.md
- epic-7-prompt-optimization-detail.md
- epic-7-prompt-stories-detail.md
- story-2.4-status-2025-01-10.md
- story-3.1-implementation-status.md
- story-3.1-metadata-first-prompt-second.md
```
**Status:** Mix van duplicaten, varianten en unieke content. COMPLETE-EPIC-OVERVIEW.md bevat een 9-epic structuur!

##### Bulk Archive (`/docs/archief/bulk-archive-2025-08-18/`)
```
- STORY-001-database-encoding-fixes.md 🆕
- STORY-002-ui-quick-wins.md 🆕
- STORY-003-content-enrichment.md
- STORY-004-ui-tabs-completion.md
- STORY-005-prompt-optimization.md 🆕
- STORY-006-test-suite-restoration.md 🆕
```
**Bevinding:** Alternatieve story nummering met unieke content

### C. Inconsistentie Analyse

#### ⚠️ Kritieke Inconsistenties

1. **Dubbele Nummering Systemen**
   - Master: Story 1.1, 2.1, etc. (epic.story format)
   - Archief: STORY-001, STORY-002 (sequentieel)
   - Geen US-XXX format zoals voorgesteld
   - COMPLETE-EPIC-OVERVIEW gebruikt weer andere nummering

2. **Verborgen/Vergeten Epics**
   - EPIC-001: Database Infrastructure (in archief, niet in master)
   - EPIC-003: UI Quick Wins (in archief, niet in master)
   - EPIC-006: Prompt Optimization (in archief, niet in master)
   - EPIC-007: Test Suite Restoration (in archief, niet in master)
   - **Epic 8**: Web Lookup Module (MERGED met Epic 3 volgens COMPLETE-EPIC-OVERVIEW)
   - **Epic 9**: Advanced Features (5% compleet volgens COMPLETE-EPIC-OVERVIEW)
   - **Epic CFR**: Context Flow Refactoring (0% CRITICAL in master)

3. **Master Document Discrepanties**
   - MASTER-EPICS-USER-STORIES.md: 10 epics
   - COMPLETE-EPIC-OVERVIEW.md (archief): 9 epics met andere statussen
   - Verschillende completion percentages tussen documenten

4. **Status Conflicten**
   - Epic 2 stories: "Ready" in losse files, "DONE" in master
   - Epic 6 (Security): 0% in COMPLETE-EPIC-OVERVIEW, 40% in master
   - Story 2.4: Verschillende statussen in verschillende documenten

5. **Metadata Inconsistenties**
   - Sommige files hebben frontmatter, andere niet
   - Verschillende owner attributies
   - Inconsistente priority levels
   - Canonical flags zonder betekenis

6. **Missing Traceability**
   - Geen links tussen epics en requirements in veel gevallen
   - Dependencies niet consistent gedocumenteerd
   - Code references ontbreken vaak
   - Geen ASTRA/NORA mappings

---

## 🔍 Verborgen Epics & Stories Uit Archief (NIEUWE VONDSTEN)

### Diep Archief Ontdekkingen

#### 1. Workflows Archief (`/docs/archief/2025-01-workflows/`)
- **story-2.3-implementation-handover.md**: Bevat handover documentatie voor Story 2.3
  - Status: Branch `feat/story-2.3-container-wiring` bestaat niet meer
  - Actie: Controleren of functionaliteit geïmplementeerd is

#### 2. Consolidatie Archief (`/docs/archief/2025-09-architectuur-consolidatie/`)
- **EPIC-MANAGEMENT-ARCHITECTURE-REVIEW.md**: Management epic voor architectuur review
  - Niet vermeld in master of COMPLETE-EPIC-OVERVIEW
  - Mogelijk een meta-epic voor governance

#### 3. Deep Bulk Archive (`/docs/archief/bulk-archive-2025-08-18/archive/2025-01-12/stories/archive/`)
Bevat 6 STORY-XXX documenten met alternatieve nummering:
- STORY-001: Database encoding fixes (= Epic 1?)
- STORY-002: UI quick wins (= Epic 3?)
- STORY-003: Content enrichment (= Epic 3?)
- STORY-004: UI tabs completion (= Epic 4?)
- STORY-005: Prompt optimization (= Epic 6?)
- STORY-006: Test suite restoration (= Epic 7?)

**⚠️ Deze lijken een ALTERNATIEVE epic structuur te vertegenwoordigen!**

### Inconsistentie Matrix

| Document | Aantal Epics | Nummering | Status Info | Locatie |
|----------|--------------|-----------|-------------|---------|
| MASTER-EPICS-USER-STORIES | 10 | Epic 1-9 + CFR | Detailed | /docs/stories/ |
| COMPLETE-EPIC-OVERVIEW | 9 | Epic 1-9 | % complete | /docs/archief/stories/ |
| Requirements Archief | 7 | EPIC-001 t/m 007 | Stories + AC | /docs/archief/requirements/ |
| Bulk Archive Stories | 6 | STORY-001 t/m 006 | Alternative | /docs/archief/bulk-archive/ |

### Kritieke Bevindingen

1. **Minimaal 3 verschillende epic structuren** gevonden in archief
2. **Epic 8 (Web Lookup)** bestaat wel maar is gemerged met Epic 3
3. **Epic CFR (Context Flow Refactoring)** alleen in master, nergens anders
4. **EPIC-001 t/m EPIC-007** in archief gebruiken andere nummering dan master
5. **25+ story documenten** in archief zonder duidelijke relatie tot master

---

## 🎯 Concreet Stappenplan voor Consolidatie

### Phase 1: Voorbereiding (Week 1, Days 1-2)

#### Dag 1: Backup & Inventarisatie
```bash
# 1. Volledige backup maken
cp -r docs/ docs-backup-$(date +%Y%m%d)/

# 2. Inventory script draaien
python scripts/inventory_stories.py > inventory.json

# 3. Duplicaten detecteren
python scripts/find_duplicates.py

# 4. Gap analyse
python scripts/gap_analysis.py
```

#### Dag 2: Directory Structure Setup
```bash
# Nieuwe structuur aanmaken
mkdir -p docs/epics
mkdir -p docs/stories
mkdir -p docs/backlog
mkdir -p docs/sprints

# Template files aanmaken
cp templates/EPIC_TEMPLATE.md docs/epics/
cp templates/STORY_TEMPLATE.md docs/stories/
```

### Phase 2: Epic Migratie (Week 1, Days 3-4)

#### Stap 1: Master Epics Extractie
Voor elke epic in MASTER document:
1. Creëer `/docs/epics/EPIC-XXX.md`
2. Voeg volledige frontmatter toe
3. Kopieer epic content uit master
4. Voeg ontbrekende metadata toe

#### Stap 2: Verborgen Epics Integratie
Voor epics in archief maar niet in master:
1. Review business value
2. Besluit: activeren of archiveren
3. Bij activeren: nieuw EPIC-XXX.md maken
4. Update epic INDEX

#### Stap 3: Epic INDEX Generatie
```markdown
# docs/epics/INDEX.md
Auto-generated dashboard met:
- Epic overview table
- Dependency graph
- Progress tracking
- Roadmap view
```

### Phase 3: Story Migratie (Week 1, Day 5 - Week 2, Day 2)

#### Stap 1: Story ID Normalisatie
```python
# Conversion mapping
OLD: Story 1.1 → NEW: US-001
OLD: Story 2.1 → NEW: US-006
OLD: STORY-001 → NEW: US-052
```

#### Stap 2: Story Files Creatie
Voor elke story:
1. Creëer `/docs/stories/US-XXX.md`
2. Volledig frontmatter toevoegen
3. Content uit master/archief mergen
4. Acceptance criteria valideren
5. Test requirements toevoegen

#### Stap 3: Cross-Reference Update
- Update epic files met story links
- Link stories naar requirements
- Update code references
- Valideer bidirectionele links

### Phase 4: Integratie & Validatie (Week 2, Days 3-4)

#### Quality Gates Implementation
```yaml
# .github/workflows/backlog-validation.yml
name: Backlog Validation
on: [push, pull_request]
jobs:
  validate:
    - Check frontmatter completeness
    - Verify ID uniqueness
    - Validate cross-references
    - Check status consistency
    - Generate reports
```

#### Automated Dashboards
```python
# scripts/generate_dashboards.py
- Sprint planning dashboard
- Velocity metrics
- Burndown charts
- Dependency matrix
- ASTRA compliance report
```

### Phase 5: Business Analyst Agent Setup (Week 2, Day 5)

#### Agent Configuratie
```yaml
# ~/.claude/agents/business-analyst-justice.md
- Epic/story management capabilities
- ASTRA/NORA compliance checking
- Automated story creation
- Status tracking
- Sprint planning support
```

#### Agent Training
- Load alle epic/story templates
- Configure domain rules
- Setup automation scripts
- Test story creation flow

### Phase 6: Rollout & Training (Week 3)

#### Team Training Sessions
1. **Developers**: Nieuwe story structure
2. **Architects**: Epic management
3. **Testers**: Test coverage tracking
4. **Product Owner**: Dashboard usage

#### Documentation Updates
- Update CLAUDE.md met nieuwe structure
- Update README.md
- Create migration guide
- Update CI/CD pipelines

---

## 🚨 Risico's en Mitigaties

### Risico 1: Data Verlies
**Impact:** HIGH
**Kans:** MEDIUM
**Mitigatie:**
- Complete backup voor start
- Incrementele migratie
- Rollback procedure gedocumenteerd
- Git history behouden

### Risico 2: Team Disruption
**Impact:** MEDIUM
**Kans:** HIGH
**Mitigatie:**
- Gefaseerde rollout
- Training vooraf
- Dual-mode periode (oude + nieuwe)
- Clear communication plan

### Risico 3: Tool Integration Failures
**Impact:** HIGH
**Kans:** LOW
**Mitigatie:**
- Test integraties in staging
- Fallback naar manual processes
- Gradual feature enablement

### Risico 4: Compliance Gaps
**Impact:** CRITICAL
**Kans:** LOW
**Mitigatie:**
- ASTRA checklist validatie
- Justice domain expert review
- Automated compliance reports
- Audit trail maintenance

---

## 📅 Geschatte Tijdlijn

### Week 1 (5-9 Sept 2025)
- **Ma-Di**: Voorbereiding & Setup
- **Wo-Do**: Epic Migratie
- **Vr**: Story Migratie Start

### Week 2 (12-16 Sept 2025)
- **Ma-Di**: Story Migratie Completion
- **Wo-Do**: Integratie & Validatie
- **Vr**: Agent Setup

### Week 3 (19-23 Sept 2025)
- **Ma-Di**: Team Training
- **Wo-Do**: Production Rollout
- **Vr**: Monitoring & Adjustments

### Week 4 (26-30 Sept 2025)
- **Ma**: Master Document Deprecation
- **Di-Vr**: Stabilization & Support

---

## 🤖 Business Analyst Justice Agent Configuratie

### Voorgestelde Agent Capabilities

#### 1. Story Management
```python
class StoryManager:
    def create_story(title, epic_id, priority):
        # Generate US-XXX ID
        # Create file with template
        # Update INDEX
        # Link to epic

    def update_status(story_id, new_status):
        # Update frontmatter
        # Refresh dashboards
        # Notify stakeholders
```

#### 2. Compliance Checking
```python
class ComplianceChecker:
    def validate_astra(story):
        # Check traceability
        # Verify justice requirements
        # Generate compliance report

    def validate_nora(story):
        # Architecture alignment
        # Security requirements
        # Privacy compliance
```

#### 3. Sprint Planning
```python
class SprintPlanner:
    def plan_sprint(capacity, priorities):
        # Select stories
        # Check dependencies
        # Assign resources
        # Generate sprint plan
```

### ASTRA/NORA/GEMMA Integratie

#### ASTRA Requirements Mapping
```yaml
ASTRA-001: Traceability
  Implementation: All stories linked to requirements
  Validation: Automated link checking

ASTRA-002: Justice Chain Integration
  Implementation: Domain metadata in frontmatter
  Validation: Chain impact analysis

ASTRA-003: Audit Trail
  Implementation: Git history + metadata
  Validation: Compliance reports
```

#### NORA Standards Compliance
```yaml
NORA-P001: Privacy by Design
  Check: PII handling in stories

NORA-S001: Security Requirements
  Check: Security criteria in acceptance

NORA-A001: Architecture Alignment
  Check: Technical notes match patterns
```

#### GEMMA Integration Points
```yaml
GEMMA-REF: Referentie Componenten
  Link: Story technical notes

GEMMA-PROC: Proces Standaarden
  Link: Story workflows

GEMMA-DATA: Data Standaarden
  Link: Data model requirements
```

---

## 📊 Success Metrics

### Quantitative Metrics
| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Story Duplication | >30% | 0% | Dedup script |
| Merge Conflicts | 5/week | <1/week | Git stats |
| Story Creation Time | 30 min | 5 min | Time tracking |
| Compliance Score | Unknown | 100% | ASTRA validator |
| Traceability | ~60% | 100% | Link checker |

### Qualitative Metrics
- **Developer Satisfaction**: Survey voor/na migratie
- **Product Owner Efficiency**: Time to decision metrics
- **Audit Readiness**: Compliance officer assessment
- **Team Velocity**: Sprint completion rates

---

## 📝 Implementatie Checklist

### Pre-Migration
- [ ] Backup complete codebase
- [ ] Inventory all stories/epics
- [ ] Identify duplicates
- [ ] Create migration scripts
- [ ] Setup new directory structure
- [ ] Create templates

### During Migration
- [ ] Extract epics from master
- [ ] Create individual epic files
- [ ] Extract stories from master
- [ ] Create individual story files
- [ ] Normalize story IDs
- [ ] Update cross-references
- [ ] Validate frontmatter
- [ ] Generate INDEX files

### Post-Migration
- [ ] Run validation scripts
- [ ] Update CI/CD pipelines
- [ ] Configure agent
- [ ] Train team
- [ ] Update documentation
- [ ] Monitor adoption
- [ ] Gather feedback
- [ ] Iterate improvements

### Deprecation
- [ ] Mark master as deprecated
- [ ] Add redirect notices
- [ ] Archive after 30 days
- [ ] Clean old references

---

## 🔄 Rollback Procedure

Als migratie faalt:
1. **Immediate**: Restore van backup
2. **Communicate**: Team informeren
3. **Analyze**: Root cause analysis
4. **Adjust**: Plan aanpassen
5. **Retry**: Nieuwe poging met fixes

```bash
# Rollback script
./scripts/rollback_migration.sh --backup-date 20250905
```

---

## 📞 Contact & Support

### Migration Team
- **Lead**: Business Analyst Justice Agent
- **Technical**: Development Team
- **Compliance**: Justice Domain Expert
- **Support**: DevOps Team

### Escalation Path
1. Team Lead
2. Product Owner
3. Architecture Board
4. Steering Committee

---

## 📎 Appendices

### A. Migration Scripts
- `inventory_stories.py`: Story inventory generation
- `migrate_epics.py`: Epic extraction and creation
- `migrate_stories.py`: Story extraction and creation
- `validate_migration.py`: Post-migration validation
- `generate_dashboards.py`: Dashboard generation

### B. Templates
- `EPIC_TEMPLATE.md`: Standard epic template
- `STORY_TEMPLATE.md`: Standard story template
- `SPRINT_PLAN_TEMPLATE.md`: Sprint planning template

### C. Reference Documents
- ASTRA Guidelines: [Link]
- NORA Framework: [Link]
- GEMMA Standards: [Link]
- Justice Architecture Patterns: [Link]

---

**Document Status:** DRAFT - Awaiting Review
**Next Review:** 2025-09-06
**Approval Required From:** Product Owner, Architecture Board

*Dit migratieplan is opgesteld door de Business Analyst Justice agent en dient als leidraad voor de consolidatie van de epic/story documentatie structuur.*
