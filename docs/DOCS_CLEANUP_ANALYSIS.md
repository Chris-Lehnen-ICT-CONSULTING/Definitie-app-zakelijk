# 🧹 Docs Cleanup - Multi-Agent Analyse

**Datum:** 29 januari 2025  
**Analysemethode:** Multi-agent perspectief (PM, Architect, Developer, QA)  
**Doel:** Opschonen docs map - alleen essentiële docs behouden, rest archiveren

---

## 📊 Huidige Situatie - Shocking Stats

| Categorie | Aantal | Status | Actie |
|-----------|--------|--------|-------|
| **portal/rendered/** | 957 HTML | 🔴 BUILD OUTPUT | DELETE (niet archiveren!) |
| **backlog/** | 558 MD | 🟡 Selectief | Archiveer afgesloten EPICs |
| **analyses/** | 67 MD | 🟡 Verouderd | Archiveer >90%, behoud actieve |
| **planning/** | 41 MD | 🟡 Crisis docs | Archiveer >80% |
| **testing/** | 29 MD | 🟢 Deels actueel | Behoud actieve, archiveer oude |
| **technisch/** | 31 MD | 🟡 Mixed | Consolideer + archiveer |
| **reviews/** | 22 MD | 🟠 Verouderd | Archiveer alles |
| **guidelines/** | 13 MD | 🟢 ESSENTIEEL | VOLLEDIG BEHOUDEN |
| **architectuur/** | 35 files | 🟡 Bloat | Behoud 3 canonical + templates |

**TOTAAL:** 1700+ bestanden waarvan **>70% kan weg!**

---

## 🎭 Multi-Agent Perspectief Analyse

### 👔 Product Manager Perspectief

**Wat heeft strategische waarde?**

#### ✅ BEHOUDEN (13 documenten):
1. `/prd.md` - Stabilization MVP PRD (ACTIEF)
2. `/backlog/brief.md` - Project brief
3. `/backlog/requirements/` - **ALLEEN actieve requirements**
   - Requirements met status `active` of `proposed`
   - Gearchiveerde requirements → `archief/requirements/`
4. `/backlog/EPIC-*/` - **ALLEEN actieve EPICs:**
   - EPIC-013 (Portal) - IN_UITVOERING
   - EPIC-014 (Business Logic) - ACTIVE
   - EPIC-016, -017, -018, -019, -021, -022, -023, -025 - ACTIVE
   - EPIC-026 (Stabilization) - PROPOSED
5. `/guidelines/DOCUMENTATION_POLICY.md`
6. `/guidelines/WORKFLOW_LIBRARY.md`
7. `/compliance/` - Alle 5 bestanden (ASTRA/NORA compliance is wettelijk)

#### ❌ ARCHIVEREN:
- `/backlog/EPIC-001/` tot `/EPIC-012/` - COMPLETED (naar `archief/2025-01/epics-completed/`)
- `/backlog/EPIC-020-PHOENIX/` - LEGACY approach
- `/backlog/_archive/` - Naar main archief
- `/backlog/dashboard/` - Vervangen door Portal (naar `archief/2025-01/legacy-dashboards/`)
- `/planning/` - 95% crisis/recovery docs (naar `archief/2025-01/crisis-planning/`)
  - **UITZONDERING:** Behoud `BROWNFIELD_RECOVERY_PLAN.md` (referentie)

---

### 🏗️ Architect Perspectief

**Wat zijn canonical architecture documents?**

#### ✅ BEHOUDEN (10 documenten):
1. `/architectuur/ENTERPRISE_ARCHITECTURE.md` ⭐ CANONICAL
2. `/architectuur/SOLUTION_ARCHITECTURE.md` ⭐ CANONICAL
3. `/architectuur/TECHNICAL_ARCHITECTURE.md` ⭐ CANONICAL
4. `/architectuur/templates/` - 3 architecture templates
5. `/architectuur/README.md` - Architecture index
6. `/architectuur/decisions/` - 2 ADR summaries (recent)
7. `/guidelines/CANONICAL_LOCATIONS.md` - Location definitions

#### ❌ ARCHIVEREN (25 documenten):
- `/architectuur/cache-monitoring-*.md` - Specifiek feature design (→ `archief/2025-01/feature-designs/`)
- `/architectuur/lazy-loading-design.md` - Specifiek feature design
- `/architectuur/performance-baseline-*.md` - Vervangen door monitoring
- `/architectuur/provider-weighting-*.md` - Feature-specifiek
- `/architectuur/structured-logging-architecture.md` - Geïmplementeerd
- `/architectuur/synonym-*.md` - Feature-specifiek (naar `archief/2025-01/synonym-designs/`)
- `/architectuur/ontological_classifier_*.md` - Feature-specifiek
- `/architectuur/v2_validator_*.md` - Legacy V2 docs
- `/architectuur/voorbeelden-*.md` - Implementatievoorbeelden (code is de waarheid)
- `/architectuur/contracts/` - Oude contracten (→ code is canonical)
- `/architectuur/definitie service/` - Onduidelijk, archiveren

**RATIONALE:**
- De 3 canonical docs bevatten de complete architectuur
- Feature-specifieke designs horen niet in architecture/ maar in feature documentation
- Geïmplementeerde designs: code is de waarheid, docs zijn historisch

---

### 💻 Developer Perspectief

**Wat gebruik je dagelijks?**

#### ✅ BEHOUDEN (20 documenten):
1. `/guidelines/` - **ALLE 13 bestanden** (daily reference)
2. `/handleidingen/ontwikkelaars/` - 5 developer handbooks
3. `/technisch/module-afhankelijkheid-rapport.md` - Actuele dependency analyse
4. `/api/modular-validation-service-api.md` - API reference
5. `/quick-reference/` - 2 quick ref docs
6. `/snippets/CODEX_PROMPT_PRESETS.md` - Prompt library
7. `/workflows/` - 1 workflow doc (check actualiteit)

#### ❌ ARCHIVEREN:
- `/analyses/` - **64 van 67 bestanden** (bug analyses zijn historisch)
  - **BEHOUD:** Laatste 3 README/SUMMARY docs als index
  - Rest → `archief/2025-01/bug-analyses/`
- `/technisch/` - 28 van 31 docs (feature-specific)
  - Behoud alleen: dependency rapport + 2 recent docs
  - Rest → `archief/2025-01/technical-docs/`
- `/reviews/` - Alle 22 code reviews (→ `archief/2025-01/code-reviews/`)
- `/examples/` - 4 code examples (code in repo is canonical)
- `/frontend/AI-FRONTEND-PROMPT-NL.md` - Verouderd prompt (→ archief)
- `/migration/` - 3 migration docs (completed → archief)
- `/migrations/history_tab_removal.md` - Completed (→ archief)
- `/implementation/` - 8 van 10 docs (completed features)
  - Behoud alleen actieve implementation plans
- `/handovers/` - 1 handover doc (completed → archief)

---

### 🧪 QA Perspectief

**Welke test documentatie is actueel?**

#### ✅ BEHOUDEN (8 documenten):
1. `/testing/TESTING_GUIDE.md` - Master guide
2. `/testing/README.md` - Test index
3. `/testing/BUSINESS_RULES.md` - Core rules
4. `/testing/US-427-coverage-baseline.md` - Recent baseline (jan 2025)
5. `/testing/requirements-test-plan.md` - If up-to-date
6. `/testing/EPIC-010-test-strategy.md` - Active EPIC testing
7. `/testing/TEST_SUITE_IMPROVEMENT_PLAN.md` - Roadmap
8. `/guidelines/TDD_TO_DEPLOYMENT_WORKFLOW.md` - TDD workflow

#### ❌ ARCHIVEREN (21 documenten):
- `/testing/EPIC_010_TEST_SUITE_SUMMARY.md` - Completed
- `/testing/EPIC-010-FASE-2-summary.md` - Completed fase
- `/testing/PER-007-*.md` - Completed feature testing
- `/testing/HISTORY_*.md` - Completed feature removal verification
- `/testing/CONSOLIDATION_*.md` - One-time consolidation reports
- `/testing/TEST_AUDIT_REPORT.md` - Snapshot, not evergreen
- `/testing/test-results-2025-01-09.md` - Specific date results
- `/testing/WEB_LOOKUP_*.md` - Feature-specific testing
- Alle andere test summaries en reports
- **RATIONALE:** Test code is canonical, test docs zijn historisch

---

## 🗑️ KRITIEK: Portal Rendered Cleanup

### ❌ COMPLETE VERWIJDERING (niet archiveren!):

```bash
# VERWIJDER VOLLEDIG - dit is build output:
rm -rf docs/portal/rendered/

# Voeg toe aan .gitignore:
echo "docs/portal/rendered/" >> .gitignore
```

**WAAROM:**
- Dit zijn gegenereerde HTML bestanden (build artifacts)
- Kunnen op elk moment opnieuw gegenereerd worden via `generate_portal.py`
- Nemen 957 bestanden in beslag
- Horen niet in version control

**BEHOUDEN in portal/:**
- `index.html` - Portal UI
- `portal.js`, `portal.css` - Portal assets
- `viewer.html` - Document viewer
- `config/sources.yaml` - Portal config
- `README.md` - Portal documentatie
- `portal-index.json` - Generated index (optioneel, kan ook naar gitignore)

---

## 📦 Archivering Strategie

### Nieuwe Archief Structuur:

```
docs/archief/2025-01-cleanup/
├── bug-analyses/           # 64 analyse docs
├── code-reviews/           # 22 review docs
├── crisis-planning/        # 39 planning docs
├── epics-completed/        # EPIC-001 t/m EPIC-012
├── feature-designs/        # 20 feature-specific architecture docs
├── legacy-dashboards/      # Oude HTML dashboards
├── test-reports/           # 21 test docs
├── technical-docs/         # 28 technical docs
├── implementation-completed/  # 8 completed implementation docs
└── README.md               # Index van gearchiveerde content
```

### Archivering Regels:

1. **Datum-gebaseerd:** Gebruik `2025-01-cleanup` voor deze grote cleanup
2. **Categoriseer:** Groepeer op type (niet willekeurig)
3. **Index:** Maak `README.md` in elk archief met lijst + reden
4. **Niet verwijderen:** Alles blijft bewaard in archief
5. **Reversible:** Via git kan alles terug als nodig

---

## ✅ Finale Behouden Structuur

```
docs/
├── 📄 prd.md                    # Product Requirements
├── 📄 INDEX.md                  # Navigation hub
├── 📄 README.md                 # Project overview
│
├── 📁 guidelines/               # 13 bestanden - VOLLEDIG BEHOUDEN
│   └── * (alle bestanden)
│
├── 📁 architectuur/             # 10 bestanden (van 35)
│   ├── ENTERPRISE_ARCHITECTURE.md
│   ├── SOLUTION_ARCHITECTURE.md
│   ├── TECHNICAL_ARCHITECTURE.md
│   ├── README.md
│   ├── decisions/ (2 files)
│   └── templates/ (3 files)
│
├── 📁 backlog/                  # Alleen actieve items
│   ├── brief.md
│   ├── requirements/            # Alleen active/proposed
│   ├── EPIC-013/ t/m EPIC-026/  # 10 actieve EPICs
│   └── [epic subdirectories met US/BUG]
│
├── 📁 compliance/               # 5 bestanden - VOLLEDIG BEHOUDEN
│   └── * (ASTRA/NORA/Justice compliance)
│
├── 📁 testing/                  # 8 bestanden (van 29)
│   ├── TESTING_GUIDE.md
│   ├── README.md
│   ├── BUSINESS_RULES.md
│   ├── US-427-coverage-baseline.md
│   ├── requirements-test-plan.md
│   ├── EPIC-010-test-strategy.md
│   ├── TEST_SUITE_IMPROVEMENT_PLAN.md
│   └── (+ TDD workflow in guidelines/)
│
├── 📁 handleidingen/            # 6 bestanden - BEHOUDEN
│   ├── gebruikers/ (1)
│   └── ontwikkelaars/ (5)
│
├── 📁 technisch/                # 3 bestanden (van 31)
│   ├── module-afhankelijkheid-rapport.md
│   └── [2 recent docs]
│
├── 📁 api/                      # 1 bestand (van 2)
│   └── modular-validation-service-api.md
│
├── 📁 quick-reference/          # 2 bestanden - BEHOUDEN
│
├── 📁 snippets/                 # 1 bestand - BEHOUDEN
│   └── CODEX_PROMPT_PRESETS.md
│
├── 📁 portal/                   # 7 bestanden (zonder rendered/)
│   ├── index.html
│   ├── portal.js
│   ├── portal.css
│   ├── viewer.html
│   ├── config/sources.yaml
│   └── README.md
│
└── 📁 archief/
    ├── 2025-01-cleanup/         # NIEUWE grote cleanup
    │   ├── bug-analyses/
    │   ├── code-reviews/
    │   ├── crisis-planning/
    │   ├── epics-completed/
    │   ├── feature-designs/
    │   ├── legacy-dashboards/
    │   ├── test-reports/
    │   ├── technical-docs/
    │   ├── implementation-completed/
    │   └── README.md
    │
    └── [bestaande archieven...]
```

---

## 📈 Impact Statistieken

| Metric | Voor | Na | Reductie |
|--------|------|-----|----------|
| **Totaal bestanden** | ~1700 | ~120 | **93%** ↓ |
| **portal/** | 957 | 7 | **99%** ↓ |
| **backlog/** | 558 | ~200 | **64%** ↓ |
| **analyses/** | 67 | 3 | **96%** ↓ |
| **planning/** | 41 | 1 | **98%** ↓ |
| **testing/** | 29 | 8 | **72%** ↓ |
| **technisch/** | 31 | 3 | **90%** ↓ |
| **reviews/** | 22 | 0 | **100%** ↓ |
| **architectuur/** | 35 | 10 | **71%** ↓ |
| **guidelines/** | 13 | 13 | **0%** (behouden!) |

**RESULTAAT:** Van ~1700 naar ~120 essentiële documenten = **93% reductie!**

---

## 🎯 Execution Plan

### Fase 1: Voorbereiding (30 min)
1. Create cleanup branch: `git checkout -b docs-cleanup-2025-01`
2. Create archive structure: `mkdir -p docs/archief/2025-01-cleanup/{bug-analyses,code-reviews,...}`
3. Update .gitignore: Add `docs/portal/rendered/`

### Fase 2: Critical Cleanup (15 min)
1. **DELETE portal rendered:** `rm -rf docs/portal/rendered/`
2. Commit: "Remove generated portal HTML (build artifacts)"

### Fase 3: Archivering (2 uur)
Voor elke categorie:
1. Move files: `git mv docs/[category]/[files] docs/archief/2025-01-cleanup/[category]/`
2. Create category README with index
3. Commit per category: "Archive [category]: [reason]"

**Volgorde:**
1. analyses/ (64 files)
2. reviews/ (22 files)
3. planning/ (39 files)
4. testing/ (21 files)
5. technisch/ (28 files)
6. architectuur/ (25 files)
7. backlog/EPIC-001 t/m EPIC-012 + legacy (12 directories)
8. Overige (implementation/, examples/, migration/, etc.)

### Fase 4: Update INDEX.md (30 min)
1. Update structure in INDEX.md
2. Remove references to archived docs
3. Add link to archive index

### Fase 5: Validatie (30 min)
1. Check for broken links in remaining docs
2. Verify portal still works (regenerate if needed)
3. Test key workflows still accessible

### Fase 6: Commit & Review (30 min)
1. Final commit: "Docs cleanup: 93% reduction, keep only essential docs"
2. Create PR with this analysis as description
3. Self-review before merge

**TOTAL TIME ESTIMATE:** 4 uur

---

## ⚠️ Risico's & Mitigaties

| Risico | Impact | Mitigatie |
|--------|--------|-----------|
| Broken links | Medium | Link validation pass na cleanup |
| Portal regeneration needed | Low | Run `generate_portal.py` na cleanup |
| Accidental deletion essential doc | High | Git branch + review before merge |
| Team confusion | Medium | Update INDEX.md + announce in standup |
| Need archived doc | Low | Easy git restore, alles bewaard in archief |

---

## 🚀 Next Steps

1. **Review this analysis** - Confirm approach with team
2. **Execute cleanup** - Follow execution plan
3. **Regenerate portal** - `python scripts/docs/generate_portal.py`
4. **Update workflows** - Ensure CI/CD still works
5. **Monitor** - Watch for issues in first week
6. **Document** - Add lessons learned to guidelines

---

## 📝 Lessons Learned (voor toekomstig gebruik)

1. **Build artifacts don't belong in docs/** - Use .gitignore
2. **Bug analyses expire** - Archive after fix is deployed
3. **Feature designs expire** - Code becomes the canonical source
4. **Test reports expire** - Only keep latest baselines
5. **Crisis plans expire** - Archive after crisis resolved
6. **Guidelines are evergreen** - Keep updated, never archive
7. **Completed EPICs should archive** - Only active work in backlog
8. **One canonical architecture doc per level** - Feature specifics go elsewhere

---

**Conclusie:** Door consequent multi-agent perspectief toe te passen kunnen we van 1700 naar 120 documenten, een **93% reductie**, waarbij alle essentiële documentatie behouden blijft en toegankelijk is via een heldere structuur.

