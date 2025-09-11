# 📋 EPIC-STORY MIGRATION PLAN

**Document Type:** Migration & Consolidation Strategy
**Versie:** 1.0.0
**Status:** CONCEPT
**Created:** 05-09-2025
**Eigenaar:** Business Analyst Justice
**Van Toepassing Op:** Definitie-app Project Management System

---

## Executive Summary

### Huidige Situatie
Het Definitie-app project heeft momenteel een **gefragmenteerde epic/story documentatie structuur** met significante inconsistenties en duplicaties:

- **1 Master Document**: `MASTER-EPICS-USER-STORIES.md` met 10 epics en 51+ stories
- **27 Losse Episch Verhaal Files**: Verspreid over verschillende directories
- **30+ Story Files**: Inconsistent genummerd en gestructureerd
- **87 Vereisten**: In individuele REQ-XXX.md bestanden (werkt wel goed)
- **Meerdere Archieven**: Met verborgen/vergeten epics en stories

### Kernprobleem
**Geen enkele bron van waarheid** - verschillende teams werken met verschillende documenten, waardoor:
- ⚠️ Duplicatie van werk
- ⚠️ Inconsistente statussen
- ⚠️ Verloren vereistes
- ⚠️ Onvolledige traceability voor ASTRA/NORA compliance
- ⚠️ Merge conflicts bij updates

### Voorgestelde Oplossing
Migratie naar een **moderne, schaalbare backlog structuur** met:
- Individuele bestanden per epic/story (zoals vereistes)
- Volledige frontmatter metadata
- Automatisch gegenereerde INDEX dashboards
- Business Analyst Justice agent voor beheer
- CI/CD validatie en quality gates

---

## 📊 Volledige Inventarisatie

### A. Master Document Content
**Locatie:** `/docs/backlog/stories/MASTER-EPICS-USER-STORIES.md`

| Episch Verhaal ID | Title | Stories | Status | Prioriteit |
|---------|-------|---------|--------|----------|
| Episch Verhaal 1 | Basis Definitie Generatie | 5 | ✅ 100% Complete | HOOG |
| Episch Verhaal 2 | Kwaliteitstoetsing | 8 | ✅ 100% Complete | HOOG |
| Episch Verhaal 3 | Content Verrijking / Web Lookup | 1 | 🔄 30% In Progress | HOOG |
| Episch Verhaal 4 | User Interface | 6 | 🔄 30% In Progress | GEMIDDELD |
| Episch Verhaal 5 | Export & Import | 3 | ❌ 10% TODO | LAAG |
| Episch Verhaal 6 | Beveiliging & Auth | 4 | 🔄 40% In Progress | KRITIEK |
| Episch Verhaal 7 | Prestaties & Scaling | 8 | 🔄 35% In Progress | HOOG |
| Episch Verhaal 8 | Web Lookup Module | - | MERGED with Episch Verhaal 3 | - |
| Episch Verhaal 9 | Advanced Features | 6 | ❌ 5% TODO | LAAG |
| Episch Verhaal CFR | Context Flow Refactoring | 6 | 🚨 0% KRITIEK | KRITIEK |

**Totaal:** 10 actieve epics, 47 stories in master document

### B. Losse Episch Verhaal/Story Documenten

#### Active Directory (`/docs/backlog/stories/`)
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

##### Vereisten Archief (`/docs/archief/vereistes/`)
```
- EPIC-001-database-infrastructure.md 🆕 NIET IN MASTER
- EPIC-002-web-lookup-module.md ⚠️ Merged with Episch Verhaal 3
- EPIC-003-ui-quick-wins.md 🆕 NIET IN MASTER
- EPIC-004-content-enrichment.md ⚠️ Overlap met Episch Verhaal 3
- EPIC-005-tab-activation.md ⚠️ Overlap met Episch Verhaal 4
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
- story-2.4-status-10-01-2025.md
- story-3.1-implementation-status.md
- story-3.1-metadata-first-prompt-second.md
```
**Status:** Mix van duplicaten, varianten en unieke content. COMPLETE-EPIC-OVERVIEW.md bevat een 9-epic structuur!

##### Bulk Archive (`/docs/archief/bulk-archive-18-08-2025/`)
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

2. **Verborgen/Vergeten Epische Verhalen**
   - EPIC-001: Database Infrastructure (in archief, niet in master)
   - EPIC-003: UI Quick Wins (in archief, niet in master)
   - EPIC-006: Prompt Optimization (in archief, niet in master)
   - EPIC-007: Test Suite Restoration (in archief, niet in master)
   - **Episch Verhaal 8**: Web Lookup Module (MERGED met Episch Verhaal 3 volgens COMPLETE-EPIC-OVERVIEW)
   - **Episch Verhaal 9**: Advanced Features (5% compleet volgens COMPLETE-EPIC-OVERVIEW)
   - **Episch Verhaal CFR**: Context Flow Refactoring (0% KRITIEK in master)

3. **Master Document Discrepanties**
   - MASTER-EPICS-USER-STORIES.md: 10 epics
   - COMPLETE-EPIC-OVERVIEW.md (archief): 9 epics met andere statussen
   - Verschillende completion percentages tussen documenten

4. **Status Conflicten**
   - Episch Verhaal 2 stories: "Ready" in losse files, "DONE" in master
   - Episch Verhaal 6 (Beveiliging): 0% in COMPLETE-EPIC-OVERVIEW, 40% in master
   - Story 2.4: Verschillende statussen in verschillende documenten

5. **Metadata Inconsistenties**
   - Sommige files hebben frontmatter, andere niet
   - Verschillende owner attributies
   - Inconsistente priority levels
   - Canonical flags zonder betekenis

6. **Missing Traceability**
   - Geen links tussen epics en vereistes in veel gevallen
   - Afhankelijkheden niet consistent gedocumenteerd
   - Code references ontbreken vaak
   - Geen ASTRA/NORA mappings

---

## 🔍 Verborgen Epische Verhalen & Stories Uit Archief (NIEUWE VONDSTEN)

### Diep Archief Ontdekkingen

#### 1. Workflows Archief (`/docs/archief/2025-01-workflows/`)
- **story-2.3-implementation-handover.md**: Bevat handover documentatie voor Story 2.3
  - Status: Branch `feat/story-2.3-container-wiring` bestaat niet meer
  - Actie: Controleren of functionaliteit geïmplementeerd is

#### 2. Consolidatie Archief (`/docs/archief/2025-09-architectuur-consolidatie/`)
- **EPIC-MANAGEMENT-ARCHITECTURE-REVIEW.md**: Management epic voor architectuur review
  - Niet vermeld in master of COMPLETE-EPIC-OVERVIEW
  - Mogelijk een meta-epic voor governance

#### 3. Deep Bulk Archive (`/docs/archief/bulk-archive-18-08-2025/archive/12-01-2025/stories/archive/`)
Bevat 6 STORY-XXX documenten met alternatieve nummering:
- STORY-001: Database encoding fixes (= Episch Verhaal 1?)
- STORY-002: UI quick wins (= Episch Verhaal 3?)
- STORY-003: Content enrichment (= Episch Verhaal 3?)
- STORY-004: UI tabs completion (= Episch Verhaal 4?)
- STORY-005: Prompt optimization (= Episch Verhaal 6?)
- STORY-006: Test suite restoration (= Episch Verhaal 7?)

**⚠️ Deze lijken een ALTERNATIEVE epic structuur te vertegenwoordigen!**

### Inconsistentie Matrix

| Document | Aantal Epische Verhalen | Nummering | Status Info | Locatie |
|----------|--------------|-----------|-------------|---------|
| MASTER-EPICS-USER-STORIES | 10 | Episch Verhaal 1-9 + CFR | Detailed | /docs/backlog/stories/ |
| COMPLETE-EPIC-OVERVIEW | 9 | Episch Verhaal 1-9 | % complete | /docs/archief/stories/ |
| Vereisten Archief | 7 | EPIC-001 t/m 007 | Stories + AC | /docs/archief/vereistes/ |
| Bulk Archive Stories | 6 | STORY-001 t/m 006 | Alternative | /docs/archief/bulk-archive/ |

### Kritieke Bevindingen

1. **Minimaal 3 verschillende epic structuren** gevonden in archief
2. **Episch Verhaal 8 (Web Lookup)** bestaat wel maar is gemerged met Episch Verhaal 3
3. **Episch Verhaal CFR (Context Flow Refactoring)** alleen in master, nergens anders
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
cp templates/EPIC_TEMPLATE.md docs/backlog/epics/
cp templates/STORY_TEMPLATE.md docs/backlog/stories/
```

### Phase 2: Episch Verhaal Migratie (Week 1, Days 3-4)

#### Stap 1: Master Epische Verhalen Extractie
Voor elke epic in MASTER document:
1. Creëer `/docs/backlog/epics/EPIC-XXX.md`
2. Voeg volledige frontmatter toe
3. Kopieer epic content uit master
4. Voeg ontbrekende metadata toe

#### Stap 2: Verborgen Epische Verhalen Integratie
Voor epics in archief maar niet in master:
1. Review business value
2. Besluit: activeren of archiveren
3. Bij activeren: nieuw EPIC-XXX.md maken
4. Update epic INDEX

#### Stap 3: Episch Verhaal INDEX Generatie
```markdown
# docs/backlog/epics/INDEX.md
Auto-generated dashboard met:
- Episch Verhaal overview table
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
1. Creëer `/docs/backlog/EPIC-XXX/US-XXX/US-XXX.md`
2. Volledig frontmatter toevoegen
3. Content uit master/archief mergen
4. Acceptance criteria valideren
5. Test vereistes toevoegen

#### Stap 3: Cross-Reference Update
- Update epic files met story links
- Link stories naar vereistes
- Update code references
- Valideer bidirectionele links

### Phase 4: Integratie & Validatie (Week 2, Days 3-4)

#### Quality Gates Implementatie
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
- Episch Verhaal/story management capabilities
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
2. **Architects**: Episch Verhaal management
3. **Testers**: Test coverage tracking
4. **Product Eigenaar**: Dashboard usage

#### Documentation Updates
- Update CLAUDE.md met nieuwe structure
- Update README.md
- Create migration guide
- Update CI/CD pipelines

---

## 🚨 Risico's en Mitigaties

### Risico 1: Data Verlies
**Impact:** HOOG
**Kans:** GEMIDDELD
**Mitigatie:**
- Complete backup voor start
- Incrementele migratie
- Rollback procedure gedocumenteerd
- Git history behouden

### Risico 2: Team Disruption
**Impact:** GEMIDDELD
**Kans:** HOOG
**Mitigatie:**
- Gefaseerde rollout
- Training vooraf
- Dual-mode periode (oude + nieuwe)
- Clear communication plan

### Risico 3: Tool Integration Failures
**Impact:** HOOG
**Kans:** LAAG
**Mitigatie:**
- Test integraties in staging
- Fallback naar manual processes
- Gradual feature enablement

### Risico 4: Compliance Gaps
**Impact:** KRITIEK
**Kans:** LAAG
**Mitigatie:**
- ASTRA checklist validatie
- Justice domain expert review
- Automated compliance reports
- Audit trail maintenance

---

## 📅 Geschatte Tijdlijn

### Week 1 (5-9 Sept 2025)
- **Ma-Di**: Voorbereiding & Setup
- **Wo-Do**: Episch Verhaal Migratie
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
        # Verify justice vereistes
        # Generate compliance report

    def validate_nora(story):
        # Architecture alignment
        # Beveiliging vereistes
        # Privacy compliance
```

#### 3. Sprint Planning
```python
class SprintPlanner:
    def plan_sprint(capacity, priorities):
        # Select stories
        # Check afhankelijkheden
        # Assign resources
        # Generate sprint plan
```

### ASTRA/NORA/GEMMA Integratie

#### ASTRA Vereisten Mapping
```yaml
ASTRA-001: Traceability
  Implementatie: All stories linked to vereistes
  Validation: Automated link checking

ASTRA-002: Justice Chain Integration
  Implementatie: Domain metadata in frontmatter
  Validation: Chain impact analysis

ASTRA-003: Audit Trail
  Implementatie: Git history + metadata
  Validation: Compliance reports
```

#### NORA Standards Compliance
```yaml
NORA-P001: Privacy by Design
  Check: PII handling in stories

NORA-S001: Beveiliging Vereisten
  Check: Beveiliging criteria in acceptance

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
  Link: Data model vereistes
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
- **Product Eigenaar Efficiency**: Time to decision metrics
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
2. Product Eigenaar
3. Architecture Board
4. Steering Committee

---

## 📎 Appendices

### A. Migration Scripts
- `inventory_stories.py`: Story inventory generation
- `migrate_epics.py`: Episch Verhaal extraction and creation
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

**Document Status:** CONCEPT - Awaiting Review
**Next Review:** 06-09-2025
**Approval Required From:** Product Eigenaar, Architecture Board

*Dit migratieplan is opgesteld door de Business Analyst Justice agent en dient als leidraad voor de consolidatie van de epic/story documentatie structuur.*
