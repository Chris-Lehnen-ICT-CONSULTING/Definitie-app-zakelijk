# Rebuild Directory - Complete Package

**Created:** 2025-10-02
**Status:** ✅ READY FOR WEEK 1
**Purpose:** All rebuild-related artifacts in one location

---

## 📁 Directory Structure

```
rebuild/
├── README.md                    # This file
├── docs/                        # Strategic documents
│   ├── ARCHITECTURE_DECISION.md
│   ├── REQUIREMENTS_TRACEABILITY_MATRIX.md
│   └── PREPARATION_COMPLETE.md
├── scripts/                     # Extraction & automation scripts
│   ├── extract_rule.py
│   ├── create_test_fixtures.py
│   ├── validate_week1.sh
│   └── generate_traceability_matrix.py
├── extracted/                   # Extracted data from current system
│   ├── baseline/
│   │   ├── baseline_42_definitions.json
│   │   └── BASELINE_SUMMARY.md
│   └── generation/
│       └── prompts/
│           ├── SYSTEM_PROMPT.md
│           ├── CONTEXT_TEMPLATE.md
│           └── RULES_INJECTION.md
├── config/                      # Configuration files
│   └── validation_rules/
│       ├── README.md
│       ├── arai/
│       ├── con/
│       ├── ess/
│       ├── int/
│       ├── sam/
│       ├── str/
│       ├── ver/
│       └── dup/
└── templates/                   # Week 2+ implementation templates
    ├── README.md
    ├── docker/
    │   ├── docker-compose.yml
    │   └── .env.example
    ├── fastapi/
    │   └── main.py
    └── testing/
        └── pytest.ini
```

---

## 🎯 Quick Start

### Start Week 1 Day 1
```bash
cd rebuild

# Test extraction script
python scripts/extract_rule.py ../src/toetsregels/regels/ARAI-02.py

# Check baseline
cat extracted/baseline/BASELINE_SUMMARY.md

# Review architecture decision
cat docs/ARCHITECTURE_DECISION.md
```

### Week 2+ Setup
```bash
cd rebuild

# Copy templates to project root
cp templates/docker/docker-compose.yml ..
cp templates/docker/.env.example ../.env
cp templates/fastapi/main.py ../app/

# Setup infrastructure
docker-compose up -d
```

---

## 📊 Contents Summary

| Category | Files | Purpose |
|----------|-------|---------|
| **docs/** | 3 | Strategic decisions & tracking |
| **scripts/** | 4 | Extraction & automation |
| **extracted/** | 5 | Baseline data & prompts |
| **config/** | 9+ | Validation rule configs |
| **templates/** | 5+ | Implementation templates |
| **TOTAL** | **27+** | Complete rebuild package |

---

## 🚀 Usage by Week

**Week 1:** Use `scripts/` for extraction, `config/` for YAMLs
**Week 2:** Use `templates/docker/` for infrastructure
**Week 3-4:** Use `templates/fastapi/` for backend
**Week 9:** Use `extracted/baseline/` for validation

---

## ✅ Preparation Status

- ✅ 42 baseline definitions exported
- ✅ Architecture decision documented (OPTION B recommended)
- ✅ 109 requirements traced
- ✅ Extraction scripts functional
- ✅ Week 1 ready to start

**Next:** Review `docs/ARCHITECTURE_DECISION.md` and start Week 1!

---

## 📚 Backlog Directory Added

**Location:** `rebuild/backlog/`
**Content:** Complete project backlog (excluding portal)

### Backlog Structure
```
rebuild/backlog/
├── 25 EPICs (EPIC-001 through EPIC-026)
├── 492 markdown files (user stories, bugs, plans)
├── requirements/ (109 REQ-XXX files)
├── dashboard/ (backlog visualization)
└── brief.md (project brief)
```

**Total:** 538 files, 6.7 MB

### Quick Access
```bash
# View all EPICs
ls rebuild/backlog/EPIC-*/

# View specific EPIC
cat rebuild/backlog/EPIC-026/EPIC-026.md

# View requirements
ls rebuild/backlog/requirements/REQ-*.md

# View project brief
cat rebuild/backlog/brief.md
```

**Note:** Portal excluded (as requested) - pure markdown content only
