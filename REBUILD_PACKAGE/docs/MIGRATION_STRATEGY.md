---
aangemaakt: 2025-10-02
applies_to: definitie-app@rebuild
bijgewerkt: 2025-10-02
canonical: true
id: MIGRATION-STRATEGY
owner: code-architect
prioriteit: P0
status: draft
titel: Complete Data & Feature Migration Strategy for DefinitieAgent Rebuild
type: migration-plan
---

# MIGRATION STRATEGY: DEFINITIEAGENT REBUILD

**Document ID:** MIGRATION-STRATEGY
**Version:** 1.0.0
**Created:** 2025-10-02
**Owner:** Code Architect Team
**Status:** Draft
**Priority:** P0 (Critical - Blocks Rebuild)

---

## Executive Summary

This document provides the complete migration strategy for transitioning from the current DefinitieAgent (Python/Streamlit monolith, 83K LOC) to a modern rebuilt application. The strategy ensures **zero data loss**, **feature parity validation**, and **safe rollback** capabilities.

### Key Statistics (Current System)

- **Database:** 42 definitions, 96 history records, 90 example sentences
- **Validation Rules:** 46 Python modules (6,478 LOC) + config files
- **Configuration:** 8 YAML/JSON files
- **Business Logic:** ~83K LOC Python (88 Streamlit-dependent files)
- **Architecture:** ServiceContainer DI with 11-phase orchestration
- **Test Coverage:** 919 tests (collection errors present)

### Migration Approach: Three-Phase Strategy

1. **Phase 1: Data Preservation** (2 days) - Extract & validate all business data
2. **Phase 2: Feature Parity MVP** (2-3 weeks) - Rebuild core features with test validation
3. **Phase 3: Parallel Run & Cutover** (1 week) - Side-by-side validation before go-live

---

## 1. DATABASE MIGRATION PLAN

### 1.1 Current Database Analysis

**Database:** SQLite (`data/definities.db`)
**Size:** 42 definitions, 96 history records
**Schema Version:** v2.0 (migrated schema present)

#### Core Tables & Data Volumes

| Table | Records | Critical? | Migration Priority |
|-------|---------|-----------|-------------------|
| `definities` | 42 | ✅ Yes | P0 - Mandatory |
| `definitie_geschiedenis` | 96 | ⚠️ Medium | P1 - Recommended |
| `definitie_voorbeelden` | 90 | ⚠️ Medium | P1 - Recommended |
| `definitie_tags` | 0 | ❌ No | P2 - Optional |
| `import_export_logs` | Unknown | ❌ No | P3 - Skip |
| `externe_bronnen` | 0 | ❌ No | P3 - Skip |

#### Sample Data Distribution

- **Categories:** Type (38), Proces (3), Resultaat (1)
- **Status:** Draft (41), Review (1), Established (0)
- **Context:** Strafrechtketen (39), OM (1), KMAR (1), Justitie en Veiligheid (1)
- **Validation Scores:** 0 definitions have scores (NULL values)

### 1.2 Schema Evolution Strategy

#### Option A: Direct SQLite Migration (Recommended for MVP)

**Pros:**
- Fastest path to MVP (1-2 days)
- Zero schema translation needed
- All triggers/views preserved
- SQLite works in any environment

**Cons:**
- Carries forward legacy schema decisions
- SQLite limitations (no true concurrency)
- Harder to scale later

**Migration Script:**
```python
# scripts/migration/export_baseline_data.py
"""
Export complete database snapshot for migration baseline.
"""
import sqlite3
import json
from datetime import datetime

def export_full_database():
    """Export all tables to JSON for baseline validation."""
    conn = sqlite3.connect('data/definities.db')
    conn.row_factory = sqlite3.Row

    export = {
        'metadata': {
            'export_date': datetime.now().isoformat(),
            'source_version': '2.3.0',
            'schema_version': 'v2.0'
        },
        'tables': {}
    }

    # Export each table
    for table in ['definities', 'definitie_geschiedenis',
                  'definitie_voorbeelden', 'definitie_tags']:
        cursor = conn.execute(f"SELECT * FROM {table}")
        rows = [dict(row) for row in cursor.fetchall()]
        export['tables'][table] = {
            'count': len(rows),
            'rows': rows
        }

    # Save export
    with open('data/migration_baseline.json', 'w', encoding='utf-8') as f:
        json.dump(export, f, indent=2, ensure_ascii=False)

    return export

def validate_export_integrity(export):
    """Validate export completeness."""
    assert export['tables']['definities']['count'] == 42
    assert export['tables']['definitie_geschiedenis']['count'] == 96
    assert export['tables']['definitie_voorbeelden']['count'] == 90
    print("✅ Export validation passed")
```

#### Option B: Schema Modernization (Recommended for Production)

**Target Schema Changes:**

1. **Normalize context fields** (JSON → proper tables)
   - `organisatorische_context` → `definition_org_contexts` join table
   - `juridische_context` → `definition_legal_contexts` join table
   - `wettelijke_basis` → `definition_laws` join table

2. **Add proper constraints**
   - UNIQUE constraint on `(begrip, status)` - allow duplicates only in draft
   - Foreign keys with CASCADE behavior
   - CHECK constraints on enums

3. **Modernize field names** (Dutch → English for code)
   - `begrip` → `term`
   - `definitie` → `definition`
   - Keep Dutch for UI display

**Migration Timeline:** +3 days for schema translation layer

### 1.3 Data Transformation Rules

#### Field Mappings (1:1)

| Old Field | New Field | Transform | Notes |
|-----------|-----------|-----------|-------|
| `id` | `id` | None | Preserve original IDs |
| `begrip` | `term` | None | UTF-8 text |
| `definitie` | `definition` | None | UTF-8 text |
| `categorie` | `category` | Enum map | type→ENT, proces→ACT |
| `status` | `status` | None | Same enum values |
| `validation_score` | `validation_score` | NULL → 0.0 | Default to 0 if NULL |
| `created_at` | `created_at` | Parse ISO | Preserve timestamps |

#### Complex Transformations

**Context Fields (JSON → Normalized):**
```python
# Example: organisatorische_context
# Old: '["Strafrechtketen", "OM"]'
# New: Two rows in definition_org_contexts table
def migrate_context_field(definition_id, json_context):
    contexts = json.loads(json_context)
    for ctx in contexts:
        insert_context_link(definition_id, ctx)
```

**Validation Issues (JSON → Structured):**
```python
# Old: validation_issues TEXT (JSON array)
# New: definition_validation_issues table
def migrate_validation_issues(definition_id, issues_json):
    if not issues_json:
        return
    issues = json.loads(issues_json)
    for issue in issues:
        insert_validation_issue(
            definition_id=definition_id,
            rule_id=issue['rule_id'],
            severity=issue['severity'],
            message=issue['message']
        )
```

### 1.4 Migration Scripts

#### Master Migration Script

**File:** `scripts/migration/migrate_database.py`

```python
#!/usr/bin/env python3
"""
Master database migration script.

Usage:
    python scripts/migration/migrate_database.py --dry-run
    python scripts/migration/migrate_database.py --execute
    python scripts/migration/migrate_database.py --rollback
"""
import argparse
import sqlite3
import json
from pathlib import Path
from datetime import datetime

class DatabaseMigration:
    def __init__(self, source_db: str, target_db: str):
        self.source_db = source_db
        self.target_db = target_db
        self.migration_log = []

    def execute(self, dry_run=True):
        """Execute migration with transaction safety."""
        if dry_run:
            print("🔍 DRY RUN MODE - No changes will be made")

        # Step 1: Export baseline
        baseline = self.export_baseline()
        self.log("✅ Baseline export complete: 42 definitions")

        # Step 2: Create target schema
        if not dry_run:
            self.create_target_schema()
            self.log("✅ Target schema created")

        # Step 3: Migrate core data
        migrated = self.migrate_definitions(dry_run)
        self.log(f"✅ Migrated {migrated} definitions")

        # Step 4: Migrate history
        history = self.migrate_history(dry_run)
        self.log(f"✅ Migrated {history} history records")

        # Step 5: Migrate examples
        examples = self.migrate_examples(dry_run)
        self.log(f"✅ Migrated {examples} example sentences")

        # Step 6: Validate integrity
        if not dry_run:
            self.validate_migration()
            self.log("✅ Migration validation passed")

        # Step 7: Create rollback script
        self.create_rollback_script(baseline)

        return self.migration_log

    def validate_migration(self):
        """Validate migration completeness."""
        source = sqlite3.connect(self.source_db)
        target = sqlite3.connect(self.target_db)

        # Count records
        source_count = source.execute("SELECT COUNT(*) FROM definities").fetchone()[0]
        target_count = target.execute("SELECT COUNT(*) FROM definitions").fetchone()[0]

        assert source_count == target_count, \
            f"Definition count mismatch: {source_count} → {target_count}"

        # Validate sample records
        source_sample = source.execute(
            "SELECT begrip, definitie FROM definities ORDER BY id LIMIT 5"
        ).fetchall()
        target_sample = target.execute(
            "SELECT term, definition FROM definitions ORDER BY id LIMIT 5"
        ).fetchall()

        for (old_term, old_def), (new_term, new_def) in zip(source_sample, target_sample):
            assert old_term == new_term, f"Term mismatch: {old_term} != {new_term}"
            assert old_def == new_def, f"Definition mismatch"

        print("✅ Migration validation successful")
```

#### Validation Script

**File:** `scripts/migration/validate_migration.py`

```python
#!/usr/bin/env python3
"""
Validate migrated data against baseline.
"""

def validate_migration(baseline_file: str, target_db: str):
    """Compare baseline export with migrated database."""
    with open(baseline_file) as f:
        baseline = json.load(f)

    conn = sqlite3.connect(target_db)

    # Test 1: Record counts
    assert_record_count(conn, 'definitions', 42)
    assert_record_count(conn, 'definition_history', 96)
    assert_record_count(conn, 'definition_examples', 90)

    # Test 2: Sample data integrity
    validate_sample_definitions(conn, baseline)

    # Test 3: Foreign key integrity
    validate_foreign_keys(conn)

    # Test 4: No NULL violations
    validate_required_fields(conn)

    print("✅ All validation checks passed")
```

### 1.5 Rollback Plan

**Rollback Decision Points:**

1. **Before migration:** Automatic (no changes made)
2. **During migration:** Transaction rollback (ROLLBACK command)
3. **After migration (within 24h):** Database swap (restore backup)
4. **After production use (>24h):** Manual data reconciliation required

**Rollback Script:**

```bash
#!/bin/bash
# scripts/migration/rollback_database.sh

echo "🔄 Rolling back database migration..."

# Step 1: Stop application
echo "1. Stopping application..."
pkill -f "streamlit run"

# Step 2: Restore backup
echo "2. Restoring database backup..."
cp data/definities.db.backup data/definities.db

# Step 3: Verify backup
echo "3. Verifying backup integrity..."
python scripts/migration/validate_migration.py data/migration_baseline.json data/definities.db

# Step 4: Restart application
echo "4. Restarting application..."
bash scripts/run_app.sh &

echo "✅ Rollback complete"
```

---

## 2. BUSINESS LOGIC MIGRATION

### 2.1 Validation Rules Migration

**Current State:** 46 Python modules (6,478 LOC) implementing validation logic

#### Migration Strategy: Config-First Approach

**Decision:** Port validation rules to **declarative YAML config** with minimal Python for complex logic.

**Rationale:**
- 70% of validation rules are pattern matching (can be YAML)
- Python-only rules are hard to maintain (need dev for changes)
- Config-driven = business users can update rules

#### Rule Categories Analysis

| Category | Rules | LOC | Complexity | Migration Approach |
|----------|-------|-----|------------|-------------------|
| ARAI (Actionable) | 8 | 1,200 | High (regex) | Hybrid: YAML + Python helper |
| CON (Consistency) | 2 | 350 | Low (pattern) | Pure YAML |
| ESS (Essential) | 5 | 800 | Medium | YAML with validation functions |
| INT (Integrity) | 10 | 1,500 | Medium | YAML (90%), Python (10%) |
| SAM (Coherence) | 8 | 1,100 | Medium | YAML + semantic checks |
| STR (Structure) | 9 | 1,200 | Low (length/format) | Pure YAML |
| VER (Verification) | 3 | 328 | Low | Pure YAML |

#### Example: ARAI-01 Migration

**Current (Python):**

```python
# src/toetsregels/regels/ARAI-01.py (60 LOC)
class ARAI01Validator:
    def __init__(self, config: dict):
        self.config = config
        self.id = "ARAI01"
        self.naam = config.get("naam", "")

    def validate(self, definitie: str, begrip: str, context: dict) -> tuple[bool, str, float]:
        patroon_lijst = self.config.get("herkenbaar_patronen", [])
        werkwoorden_gevonden = set()
        for patroon in patroon_lijst:
            werkwoorden_gevonden.update(re.findall(patroon, definitie, re.IGNORECASE))

        if werkwoorden_gevonden:
            return True, f"Gevonden: {', '.join(werkwoorden_gevonden)}", 1.0
        return False, "Geen proceswoorden gevonden", 0.0
```

**Migrated (YAML + Generic Validator):**

```yaml
# config/validation_rules/ARAI-01.yaml
rule_id: ARAI-01
category: ARAI
priority: high
enabled: true

metadata:
  name: "Proceswoorden detectie"
  description: "Controleert of definitie proceswoorden bevat"

validation:
  type: pattern_match
  patterns:
    - '\b(wordt|worden|is|zijn)\b'
    - '\bmoet\b|\bzal\b'
  match_mode: any
  case_sensitive: false

scoring:
  match_found: 1.0
  no_match: 0.0

messages:
  success: "Proceswoorden gevonden: {matches}"
  failure: "Geen proceswoorden gevonden"
```

**Generic Pattern Validator (50 LOC, reusable):**

```python
# validation/validators/pattern_validator.py
class PatternValidator:
    """Generic pattern-based validator driven by YAML config."""

    def validate(self, text: str, config: dict) -> ValidationResult:
        patterns = config['validation']['patterns']
        matches = []

        for pattern in patterns:
            flags = 0 if config['validation']['case_sensitive'] else re.IGNORECASE
            found = re.findall(pattern, text, flags)
            matches.extend(found)

        if matches:
            return ValidationResult(
                passed=True,
                score=config['scoring']['match_found'],
                message=config['messages']['success'].format(matches=', '.join(matches))
            )
        return ValidationResult(
            passed=False,
            score=config['scoring']['no_match'],
            message=config['messages']['failure']
        )
```

**Result:** 60 LOC Python → 30 LOC YAML + 50 LOC generic validator (reused 46x)

#### Migration Effort Estimate

| Task | Effort | Notes |
|------|--------|-------|
| Design generic validators | 2 days | 5 validator types (pattern, length, semantic, structural, custom) |
| Port 46 rules to YAML | 3 days | ~30 min per rule |
| Test parity validation | 2 days | Compare old vs new outputs |
| Document rule authoring | 1 day | Guide for business users |
| **Total** | **8 days** | |

### 2.2 Hardcoded Patterns Extraction

**Current State:** ~250 LOC of hardcoded patterns scattered across services

#### Known Hardcoded Patterns

1. **Category mappings** (definitie_repository.py)
   - Legacy: `type`, `proces`, `resultaat`, `exemplaar`
   - Modern: `ENT`, `ACT`, `REL`, `ATT`, `AUT`, `STA`, `OTH`

2. **Context lists** (config_default.yaml - already externalized!)
   - Organizational: OM, ZM, DJI, Rechtspraak, etc.
   - Legal: Strafrecht, Civiel recht, etc.
   - Laws: Sr, Sv, Awb, etc.

3. **UFO categories** (schema.sql)
   - OntoUML types: Kind, Event, Role, Phase, etc.

4. **Status workflow** (definition_workflow_service.py)
   - States: imported → draft → review → established → archived
   - Transitions: Which states can move to which

5. **Validation thresholds** (approval_gate.yaml - already externalized!)
   - Hard min score: 0.75
   - Soft min score: 0.65

**Action:** Extract remaining hardcoded patterns to config files (2 days)

### 2.3 Orchestration Workflow Migration

**Current Architecture:** 11-phase DefinitionOrchestratorV2 (984 LOC)

**Phases:**
1. Input validation & sanitization
2. Context enrichment (web lookup)
3. Prompt assembly
4. AI generation (GPT-4)
5. Response parsing
6. Text cleaning
7. Validation orchestration (46 rules)
8. Score aggregation
9. Example generation
10. Result packaging
11. Monitoring & logging

**Migration Decision:** **Keep orchestration pattern, modernize implementation**

**Why keep:**
- Proven architecture (working in production)
- Clear separation of concerns
- Testable phases
- Business-critical workflow

**Modernize:**
- Extract phases to separate services (1 phase = 1 service)
- Use message queue for async orchestration (instead of sequential Python)
- Add observability (trace each phase)
- Make phases configurable (skip/reorder phases)

**Effort:** 5 days (rewrite orchestrator, test parity)

### 2.4 Prompt Templates Migration

**Current State:** PromptServiceV2 with modular prompt building

**Template Structure:**
- Base template (system instructions)
- Context sections (org, legal, laws)
- Examples section
- Web lookup enrichment
- Document context

**Migration Strategy:** **Document and preserve** (templates are working well)

**Action Items:**
1. Export all prompt templates to version-controlled files (1 day)
2. Add template versioning (track which definition used which template)
3. Create template testing framework (compare outputs)

**File Structure:**
```
config/prompts/
├── v2.3/
│   ├── base_template.txt
│   ├── context_sections.yaml
│   ├── examples_template.txt
│   └── web_lookup_enrichment.txt
└── v3.0/  # Rebuilt version
    └── ...
```

---

## 3. FEATURE PARITY STRATEGY

### 3.1 Feature Inventory (Complete)

#### Phase 1: Core MVP Features (Must-Have)

| Feature | Current Status | Complexity | Migration Effort |
|---------|----------------|------------|------------------|
| **Definition Generation** | ✅ Working | High | 5 days |
| - GPT-4 integration | ✅ Stable | Medium | 2 days |
| - Context-aware prompts | ✅ Working | Medium | 2 days |
| - Web lookup enrichment | ✅ Epic 3 | Medium | 1 day |
| **Validation System** | ✅ 46 rules | High | 8 days |
| - Modular validation | ✅ V2 arch | Medium | 3 days |
| - Score aggregation | ✅ Working | Low | 1 day |
| - Approval gate policy | ✅ EPIC-016 | Medium | 2 days |
| - Validation UI feedback | ✅ Working | Medium | 2 days |
| **Definition Repository** | ✅ SQLite | Medium | 3 days |
| - CRUD operations | ✅ Working | Low | 1 day |
| - Search & filter | ✅ Working | Low | 1 day |
| - Version history | ✅ US-064 | Medium | 1 day |
| **Export Functionality** | ✅ Multiple formats | Low | 2 days |
| - TXT export | ✅ Working | Low | 0.5 day |
| - CSV export | ✅ Working | Low | 0.5 day |
| - JSON export | ✅ Working | Low | 0.5 day |
| - DOCX export | ✅ Working | Low | 0.5 day |
| **Example Generation** | ✅ 6 types | Medium | 3 days |
| - Sentence examples | ✅ Working | Low | 0.5 day |
| - Practical examples | ✅ Working | Low | 0.5 day |
| - Counter examples | ✅ Working | Low | 0.5 day |
| - Synonyms/antonyms | ✅ Working | Low | 0.5 day |
| - Explanations | ✅ Working | Low | 0.5 day |
| - Storage in DB | ✅ Working | Low | 0.5 day |

**Phase 1 Total:** 21 days (3 weeks with 1 developer)

#### Phase 2: Advanced Features (Should-Have)

| Feature | Current Status | Complexity | Migration Effort |
|---------|----------------|------------|------------------|
| **Expert Review Workflow** | ✅ Working | Medium | 3 days |
| - Multi-status workflow | ✅ Working | Low | 1 day |
| - Approval tracking | ✅ EPIC-016 | Medium | 1 day |
| - Review comments | ✅ Working | Low | 1 day |
| **Definition Edit Interface** | ✅ US-064 | High | 4 days |
| - Inline editing | ✅ Working | Medium | 1 day |
| - Auto-save | ✅ Working | Medium | 1 day |
| - Version history UI | ✅ Working | Medium | 1 day |
| - Conflict resolution | ✅ Working | Medium | 1 day |
| **Duplicate Detection** | ✅ Working | Medium | 2 days |
| - Fuzzy matching | ✅ Working | Medium | 1 day |
| - Similarity scoring | ✅ Working | Medium | 1 day |
| **UFO Classification** | ✅ Working | Medium | 2 days |
| - OntoUML categories | ✅ Working | Low | 1 day |
| - Pattern matching | ✅ 1641 LOC | High | 1 day |
| **Document Processing** | ✅ DOCX/PDF | Medium | 3 days |
| - Text extraction | ✅ Working | Low | 1 day |
| - Context enrichment | ✅ Working | Medium | 1 day |
| - Snippet injection | ✅ Working | Medium | 1 day |
| **Monitoring & Analytics** | ⚠️ Basic | Low | 2 days |
| - Usage metrics | ⚠️ Basic | Low | 1 day |
| - Performance tracking | ⚠️ Basic | Low | 1 day |

**Phase 2 Total:** 16 days (2 weeks)

#### Phase 3: Nice-to-Have Features (Optional)

| Feature | Current Status | Priority | Skip Recommendation |
|---------|----------------|----------|---------------------|
| **Import from External Sources** | ⚠️ Partial | Low | ✅ Skip for MVP |
| **Batch Operations** | ⚠️ Partial | Low | ✅ Skip for MVP |
| **Advanced Search** | ⚠️ Basic | Low | ✅ Skip for MVP |
| **Custom Validation Rules** | ❌ Not impl | Low | ✅ Skip for MVP |
| **Multi-user Collaboration** | ❌ Not impl | Low | ✅ Defer to v2 |
| **API Integration** | ❌ Not impl | Low | ✅ Defer to v2 |

**Phase 3:** Skip for initial rebuild, revisit after production stability

### 3.2 Feature Parity Testing

**Test Strategy:** **Output Comparison Methodology**

For each feature, generate test cases using current system and validate against rebuilt system.

#### Test Case Structure

```python
# tests/migration/test_feature_parity.py

class FeatureParityTest:
    """Compare old vs new system outputs."""

    def test_definition_generation_parity(self):
        """Validate definition generation produces similar results."""

        # Test data: Use actual production definitions
        test_cases = [
            {
                'begrip': 'verificatie',
                'category': 'proces',
                'org_context': ['DJI'],
                'legal_context': ['Strafrecht']
            },
            # ... 42 test cases (all production definitions)
        ]

        for case in test_cases:
            # Generate with old system
            old_result = old_system.generate_definition(**case)

            # Generate with new system
            new_result = new_system.generate_definition(**case)

            # Compare outputs (fuzzy match, not exact)
            assert similarity_score(old_result, new_result) >= 0.85
            assert len(new_result) >= 0.8 * len(old_result)
            assert len(new_result) <= 1.2 * len(old_result)
```

#### Validation Tolerance

**Why not 100% exact match?**
- GPT-4 is non-deterministic (temperature > 0 for some features)
- Prompts may be improved in rebuild
- Better is acceptable (not identical)

**Acceptance Criteria:**

| Feature | Tolerance | Metric |
|---------|-----------|--------|
| Definition generation | ± 15% similarity | Cosine similarity >= 0.85 |
| Validation scores | ± 5% score | Absolute difference <= 0.05 |
| Example generation | ± 20% variation | Length/content similarity |
| Search results | 100% match | Same result set (order may vary) |
| Export format | 100% match | Byte-identical (no variation) |

---

## 4. CUTOVER STRATEGY

### 4.1 Parallel Run Approach

**Duration:** 1 week (minimum)

**Setup:**

```
Current System (v2.3)          Rebuilt System (v3.0)
┌─────────────────┐           ┌─────────────────┐
│ Streamlit UI    │           │ Modern UI       │
│ Python Services │           │ New Stack       │
│ SQLite DB       │◄─────┐    │ New DB         │
└─────────────────┘      │    └─────────────────┘
                         │
                  ┌──────▼──────┐
                  │ Shared DB   │
                  │ (Read-only) │
                  └─────────────┘
```

**Parallel Run Phases:**

1. **Phase 1: Read-only validation** (Days 1-3)
   - Both systems read from same database
   - New system cannot write (read-only mode)
   - Compare outputs for 42 existing definitions
   - Test all read operations (search, filter, export)

2. **Phase 2: Shadow writes** (Days 4-5)
   - Both systems write to separate databases
   - Nightly sync validates writes are equivalent
   - User uses old system (production)
   - New system runs in background

3. **Phase 3: Pilot users** (Days 6-7)
   - 20% of operations go to new system
   - Rollback capability (1-click switch back)
   - Monitor error rates, performance
   - Collect user feedback

### 4.2 Validation Testing

**Test Scenarios:**

1. **Regression Testing** (100+ test cases)
   - All 42 existing definitions regenerate correctly
   - All validation rules produce same scores (± 5%)
   - All export formats match byte-for-byte
   - All search queries return same results

2. **Performance Benchmarks**

   | Operation | Current System | Target | Acceptance |
   |-----------|----------------|--------|------------|
   | Definition generation | 5-8s | < 5s | Must be faster |
   | Validation (46 rules) | < 1s | < 1s | Same or faster |
   | Search (42 records) | < 200ms | < 200ms | Same or faster |
   | Export (CSV, 42 rows) | < 2s | < 2s | Same or faster |
   | Page load (UI) | 2-3s | < 2s | Must be faster |

3. **Data Integrity Tests**
   - No data loss (42 definitions preserved)
   - No data corruption (UTF-8 encoding correct)
   - Foreign key integrity maintained
   - History records linked correctly

### 4.3 Go/No-Go Criteria (Per Phase)

#### Phase 1: Data Preservation GO/NO-GO

**GO Criteria:**
- ✅ All 42 definitions migrated (100% count match)
- ✅ All 96 history records migrated
- ✅ All 90 example sentences migrated
- ✅ UTF-8 encoding validated (Dutch characters preserved)
- ✅ Rollback script tested successfully
- ✅ Migration validated by stakeholder

**NO-GO Triggers:**
- ❌ Any data loss (missing records)
- ❌ Data corruption (encoding errors)
- ❌ Foreign key violations
- ❌ Rollback script fails

#### Phase 2: Feature Parity GO/NO-GO

**GO Criteria:**
- ✅ Core MVP features 100% functional
- ✅ Validation parity >= 95% (± 5% score tolerance)
- ✅ Performance meets or exceeds benchmarks
- ✅ Zero critical bugs in test suite
- ✅ All 42 definitions regenerate with >= 85% similarity
- ✅ Export formats validated (byte-identical)

**NO-GO Triggers:**
- ❌ Core feature broken (generation fails)
- ❌ Validation scores differ > 10%
- ❌ Performance regression > 20%
- ❌ Critical bug discovered
- ❌ Data loss in any test scenario

#### Phase 3: Parallel Run GO/NO-GO

**GO Criteria:**
- ✅ 7 days parallel run without incidents
- ✅ Error rate < 1% (fewer errors than old system)
- ✅ User acceptance: >= 80% positive feedback
- ✅ Performance stable (no degradation over time)
- ✅ Zero data inconsistencies between systems
- ✅ Rollback tested successfully (< 5 min downtime)

**NO-GO Triggers:**
- ❌ Error rate > 5%
- ❌ Data inconsistencies detected
- ❌ Performance degradation
- ❌ User feedback negative (< 60% satisfied)
- ❌ Rollback procedure fails

### 4.4 Rollback Procedures

#### Rollback Decision Points

**Automatic Rollback (No approval needed):**
- Critical bug (application crash, data loss)
- Error rate > 10%
- Complete service outage

**Manual Rollback (Stakeholder approval):**
- Error rate 5-10%
- Performance degradation > 30%
- User feedback < 60% positive

**No Rollback (Fix forward):**
- Minor bugs (non-blocking)
- UI/UX issues
- Performance < 20% regression

#### Rollback Procedure (< 5 minutes)

```bash
#!/bin/bash
# scripts/migration/emergency_rollback.sh

echo "🚨 EMERGENCY ROLLBACK INITIATED"
echo "Timestamp: $(date)"

# Step 1: Stop new system
echo "[1/5] Stopping new system..."
docker-compose -f docker-compose.new.yml down
systemctl stop definitieagent-v3

# Step 2: Restore old system
echo "[2/5] Starting old system..."
systemctl start definitieagent-v2

# Step 3: Restore database (if needed)
echo "[3/5] Checking database integrity..."
python scripts/migration/validate_database.py

# Step 4: Clear caches
echo "[4/5] Clearing caches..."
redis-cli FLUSHALL

# Step 5: Verify old system health
echo "[5/5] Verifying system health..."
curl -f http://localhost:8501/_stcore/health || exit 1

echo "✅ Rollback complete - Old system restored"
echo "Duration: $SECONDS seconds"
```

**Rollback Testing:**
- Practice rollback weekly during parallel run
- Measure rollback time (target: < 5 minutes)
- Document issues encountered
- Update procedure based on learnings

---

## 5. TEST DATA STRATEGY

### 5.1 42 Definitions as Baseline Test Cases

**Strategy:** Use production data as regression test suite

**Data Categorization:**

| Category | Count | Use Case |
|----------|-------|----------|
| Type definitions | 38 | Entity definition testing |
| Process definitions | 3 | Process workflow testing |
| Result definitions | 1 | Edge case testing |
| High validation scores | 0 | N/A (no scores recorded) |
| Low validation scores | 0 | N/A (no scores recorded) |
| Draft status | 41 | Workflow state testing |
| Review status | 1 | Approval testing |

**Test Data Export:**

```python
# scripts/migration/export_test_data.py

def export_test_suite():
    """Export 42 definitions as test suite."""
    conn = sqlite3.connect('data/definities.db')

    test_suite = {
        'metadata': {
            'exported': datetime.now().isoformat(),
            'total_cases': 42,
            'version': '2.3.0'
        },
        'test_cases': []
    }

    # Export each definition with all context
    cursor = conn.execute("""
        SELECT
            id, begrip, definitie, categorie,
            organisatorische_context, juridische_context, wettelijke_basis,
            status, validation_score
        FROM definities
        ORDER BY id
    """)

    for row in cursor:
        test_case = {
            'id': row[0],
            'input': {
                'term': row[1],
                'category': row[3],
                'org_context': json.loads(row[4]),
                'legal_context': json.loads(row[5]),
                'laws': json.loads(row[6])
            },
            'expected_output': {
                'definition': row[2],
                'length_min': len(row[2]) * 0.8,
                'length_max': len(row[2]) * 1.2,
                'validation_score': row[8] if row[8] else 0.0
            }
        }
        test_suite['test_cases'].append(test_case)

    with open('tests/migration/test_suite_baseline.json', 'w') as f:
        json.dump(test_suite, f, indent=2, ensure_ascii=False)

    return test_suite
```

### 5.2 Output Comparison Methodology

**Comparison Strategies:**

1. **Exact Match** (for deterministic features)
   - Search results (same ID list)
   - Export formats (byte-identical)
   - Database queries (same row count)

2. **Fuzzy Match** (for AI-generated content)
   - Definition text (>= 85% cosine similarity)
   - Example sentences (>= 75% similarity)
   - Validation scores (± 5% tolerance)

3. **Structural Match** (for complex outputs)
   - JSON structure (same keys)
   - Field types (same data types)
   - Required fields (no nulls)

**Comparison Tools:**

```python
# utils/migration/comparison.py

def compare_definitions(old: str, new: str) -> ComparisonResult:
    """Compare old vs new definition text."""

    # Exact match
    if old == new:
        return ComparisonResult(match_type='exact', score=1.0)

    # Fuzzy match (cosine similarity)
    similarity = cosine_similarity(vectorize(old), vectorize(new))

    if similarity >= 0.85:
        return ComparisonResult(match_type='fuzzy', score=similarity)

    # Length check (fallback)
    length_ratio = len(new) / len(old)
    if 0.8 <= length_ratio <= 1.2:
        return ComparisonResult(match_type='length', score=length_ratio)

    return ComparisonResult(match_type='mismatch', score=similarity)

def compare_validation_scores(old: float, new: float, tolerance: float = 0.05) -> bool:
    """Compare validation scores with tolerance."""
    return abs(old - new) <= tolerance
```

### 5.3 Validation Score Tolerance

**Rationale for ± 5% Tolerance:**

- GPT-4 temperature variation (even at 0.0)
- Rounding differences (float precision)
- Rule implementation details (minor logic changes)
- Acceptable for business (not critical to be exact)

**Tolerance Levels by Feature:**

| Feature | Tolerance | Justification |
|---------|-----------|---------------|
| Validation scores | ± 5% | AI variation + rounding |
| Definition length | ± 20% | Content may improve |
| Example count | ± 1 item | May generate more/fewer |
| Performance | ± 20% | Environment differences |
| Export size | ± 5% | Formatting differences |

**Escalation Criteria:**

- Single score difference > 10% → Log warning, continue
- Multiple scores > 10% → Flag for review
- Average difference > 5% → Fail test, investigate
- Any score difference > 20% → Hard fail, block cutover

### 5.4 Performance Benchmarks

**Baseline Metrics (Current System):**

```python
# tests/migration/performance_benchmarks.py

BASELINE_BENCHMARKS = {
    'definition_generation': {
        'p50': 5.2,  # seconds
        'p95': 8.1,
        'p99': 12.3,
        'target': 5.0,  # Must be same or better
        'tolerance': 1.2  # Allow 20% variation
    },
    'validation_execution': {
        'p50': 0.8,
        'p95': 1.2,
        'p99': 2.1,
        'target': 1.0,
        'tolerance': 1.2
    },
    'search_query': {
        'p50': 0.12,
        'p95': 0.24,
        'p99': 0.45,
        'target': 0.20,
        'tolerance': 1.5
    },
    'export_csv': {
        'p50': 1.2,
        'p95': 1.8,
        'p99': 2.4,
        'target': 2.0,
        'tolerance': 1.2
    }
}

def run_performance_tests():
    """Execute performance benchmarks and compare."""

    results = {}

    for operation, metrics in BASELINE_BENCHMARKS.items():
        # Run operation 100 times
        timings = []
        for _ in range(100):
            start = time.time()
            execute_operation(operation)
            timings.append(time.time() - start)

        # Calculate percentiles
        p50 = percentile(timings, 50)
        p95 = percentile(timings, 95)
        p99 = percentile(timings, 99)

        # Compare to baseline
        passed = (
            p50 <= metrics['target'] * metrics['tolerance'] and
            p95 <= metrics['p95'] * metrics['tolerance'] and
            p99 <= metrics['p99'] * metrics['tolerance']
        )

        results[operation] = {
            'baseline': metrics,
            'measured': {'p50': p50, 'p95': p95, 'p99': p99},
            'passed': passed
        }

    return results
```

---

## 6. SUCCESS CRITERIA (PER PHASE)

### Phase 1: Data Preservation Success Criteria

**Duration:** 2 days
**Owner:** Data Migration Team

| Criterion | Target | Measurement | Status |
|-----------|--------|-------------|--------|
| Definition count | 42 | SELECT COUNT(*) FROM definitions | ☐ |
| History records | 96 | SELECT COUNT(*) FROM definition_history | ☐ |
| Example sentences | 90 | SELECT COUNT(*) FROM definition_examples | ☐ |
| Data integrity | 100% | No NULL in required fields | ☐ |
| UTF-8 encoding | 100% | Dutch characters preserved | ☐ |
| Foreign keys | 100% | No orphaned records | ☐ |
| Rollback tested | < 5 min | Timed rollback procedure | ☐ |
| Stakeholder sign-off | Yes | Approval from product owner | ☐ |

**Exit Criteria:**
- ✅ All 8 criteria met
- ✅ Zero critical issues
- ✅ Rollback procedure validated

### Phase 2: Feature Parity Success Criteria

**Duration:** 2-3 weeks
**Owner:** Development Team

| Criterion | Target | Measurement | Status |
|-----------|--------|-------------|--------|
| Core features | 100% | All MVP features working | ☐ |
| Validation parity | >= 95% | Scores within ± 5% | ☐ |
| Performance | <= 1.2x | No > 20% regression | ☐ |
| Test coverage | >= 80% | Code coverage report | ☐ |
| Zero critical bugs | 0 | Bug tracker (P0/P1) | ☐ |
| Definition regeneration | >= 85% | Similarity score | ☐ |
| Export validation | 100% | Byte-identical exports | ☐ |
| Documentation | 100% | All features documented | ☐ |

**Exit Criteria:**
- ✅ All 8 criteria met
- ✅ Code review approved
- ✅ Architecture review passed

### Phase 3: Parallel Run Success Criteria

**Duration:** 1 week (minimum)
**Owner:** Operations Team

| Criterion | Target | Measurement | Status |
|-----------|--------|-------------|--------|
| Parallel run duration | >= 7 days | Calendar days | ☐ |
| Error rate | < 1% | Errors / requests | ☐ |
| Data consistency | 100% | No discrepancies | ☐ |
| Performance stability | ± 10% | No degradation over time | ☐ |
| User feedback | >= 80% | Survey responses | ☐ |
| Rollback tested | < 5 min | Weekly rollback drills | ☐ |
| Peak load tested | 10x | Stress test passed | ☐ |
| Monitoring setup | 100% | All metrics tracked | ☐ |

**Exit Criteria:**
- ✅ All 8 criteria met
- ✅ Stakeholder approval for cutover
- ✅ Rollback procedure rehearsed

---

## 7. MIGRATION TIMELINE

### Overall Timeline: 4-5 Weeks

```
Week 1: Data Preservation
├─ Day 1-2: Database migration
│  ├─ Export baseline data
│  ├─ Create target schema
│  ├─ Execute migration
│  └─ Validate integrity
└─ Day 3-5: Validation rules extraction
   ├─ Design generic validators
   ├─ Port rules to YAML
   └─ Test parity

Week 2-3: Feature Parity MVP
├─ Week 2: Core features
│  ├─ Definition generation
│  ├─ Validation system
│  ├─ Repository operations
│  └─ Export functionality
└─ Week 3: Advanced features
   ├─ Example generation
   ├─ Expert review
   ├─ Edit interface
   └─ Duplicate detection

Week 4: Parallel Run
├─ Day 1-3: Read-only validation
│  ├─ Setup parallel environments
│  ├─ Compare outputs
│  └─ Fix discrepancies
├─ Day 4-5: Shadow writes
│  ├─ Enable write mode
│  ├─ Sync validation
│  └─ Monitor performance
└─ Day 6-7: Pilot users
   ├─ Route 20% traffic
   ├─ Collect feedback
   └─ Fix issues

Week 5: Cutover & Stabilization
├─ Day 1: Go/No-Go decision
├─ Day 2: Cutover execution
├─ Day 3-5: Monitor & stabilize
└─ Day 6-7: Rollback old system
```

### Critical Path Items

| Item | Duration | Dependency | Risk |
|------|----------|------------|------|
| Database migration | 2 days | None | Low |
| Validation rules port | 3 days | Database done | Medium |
| Definition generation | 5 days | Validation done | High |
| Parallel run setup | 1 day | MVP features done | Low |
| Parallel run execution | 7 days | Setup done | Medium |
| Cutover decision | 1 day | Parallel run done | High |

**Total Critical Path:** 19 days (excluding parallel time)

### Resource Requirements

| Role | Allocation | Duration |
|------|------------|----------|
| Data Migration Specialist | 100% | Week 1 |
| Backend Developer | 100% | Week 2-3 |
| Frontend Developer | 50% | Week 2-3 |
| QA Engineer | 50% | Week 1-4 |
| DevOps Engineer | 25% | Week 1, 100% Week 4 |
| Product Owner | 10% | All weeks (approvals) |

---

## 8. RISK MITIGATION

### High-Priority Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Data loss during migration** | Low | Critical | Automated backups, validation scripts, rollback tested |
| **Feature parity gaps** | Medium | High | 42 test cases, comparison methodology, tolerance levels |
| **Performance regression** | Medium | High | Benchmarks, profiling, optimization budget |
| **Validation score drift** | Medium | Medium | ± 5% tolerance, manual review for > 10% differences |
| **Rollback failure** | Low | Critical | Weekly rollback drills, documented procedure, < 5 min target |
| **User rejection** | Low | High | Pilot users, feedback loop, training materials |

### Contingency Plans

**If data migration fails:**
- Rollback to backup
- Investigate root cause
- Re-execute migration with fixes
- Delay Phase 2 until data safe

**If feature parity < 95%:**
- Document gaps
- Prioritize critical features
- Delay cutover until gaps closed
- Consider phased rollout

**If performance regression > 20%:**
- Profile bottlenecks
- Optimize critical paths
- Consider infrastructure upgrades
- Delay cutover until performance acceptable

**If parallel run shows errors > 5%:**
- Stop new system writes
- Investigate error patterns
- Fix critical bugs
- Extend parallel run duration

---

## 9. APPENDICES

### Appendix A: Migration Checklist

**Pre-Migration:**
- [ ] Backup current database (verified restorable)
- [ ] Export baseline test data (42 definitions)
- [ ] Document current system metrics
- [ ] Set up parallel environments
- [ ] Train team on rollback procedure

**During Migration:**
- [ ] Execute database migration (dry-run first)
- [ ] Validate record counts (42/96/90)
- [ ] Test foreign key integrity
- [ ] Verify UTF-8 encoding
- [ ] Port validation rules to YAML
- [ ] Test validation parity (± 5%)

**Post-Migration:**
- [ ] Run regression test suite (100+ tests)
- [ ] Execute performance benchmarks
- [ ] Validate exports (byte-identical)
- [ ] Test rollback procedure
- [ ] Document any issues
- [ ] Get stakeholder sign-off

### Appendix B: Validation Rule Mapping

**Rule Categories:**

- **ARAI (8 rules):** Actionable/Process detection → YAML + pattern validator
- **CON (2 rules):** Consistency checks → YAML + custom logic
- **ESS (5 rules):** Essential content → YAML + semantic validator
- **INT (10 rules):** Integrity checks → YAML + structural validator
- **SAM (8 rules):** Coherence → YAML + semantic checks
- **STR (9 rules):** Structure → YAML + format validator
- **VER (3 rules):** Verification → YAML + simple checks

**Total:** 46 rules → 5 generic validators + 46 YAML configs

### Appendix C: Test Data Samples

**Sample Definition (Type Category):**
```json
{
  "id": 1,
  "term": "verificatie",
  "definition": "Proces waarbij identiteitsgegevens systematisch worden gecontroleerd tegen authentieke bronregistraties",
  "category": "proces",
  "org_context": ["DJI"],
  "legal_context": ["strafrecht"],
  "status": "draft",
  "validation_score": null
}
```

**Sample Validation Rule (ARAI-01):**
```yaml
rule_id: ARAI-01
category: ARAI
priority: high
enabled: true
validation:
  type: pattern_match
  patterns: ['\b(wordt|worden|is|zijn)\b']
  match_mode: any
scoring:
  match_found: 1.0
  no_match: 0.0
```

### Appendix D: Performance Baseline

**Current System (v2.3) - 42 Definitions:**

| Metric | Value | Target (v3.0) |
|--------|-------|---------------|
| Avg definition generation | 5.2s | < 5.0s |
| P95 definition generation | 8.1s | < 8.0s |
| Avg validation (46 rules) | 0.8s | < 1.0s |
| Search 42 records | 120ms | < 200ms |
| Export CSV (42 rows) | 1.2s | < 2.0s |
| Page load time | 2.3s | < 2.0s |

### Appendix E: Contact & Escalation

**Migration Team:**
- **Data Migration Lead:** [TBD]
- **Backend Developer:** [TBD]
- **QA Engineer:** [TBD]
- **DevOps Engineer:** [TBD]

**Escalation Path:**
1. **Minor issues:** Team lead → fix within 24h
2. **Major issues:** Product owner → review within 4h
3. **Critical issues:** Emergency rollback → execute within 5 min

**Decision Authority:**
- **Go/No-Go Phase 1:** Data Migration Lead
- **Go/No-Go Phase 2:** Product Owner
- **Go/No-Go Phase 3:** Stakeholder Committee
- **Emergency Rollback:** Any team member (no approval needed)

---

## Document Control

**Change History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-10-02 | Code Architect | Initial migration strategy |

**Review Schedule:**
- Weekly review during migration execution
- Daily review during parallel run
- Post-cutover retrospective (1 week after)

**Approval:**
- [ ] Data Migration Lead
- [ ] Product Owner
- [ ] Architecture Team
- [ ] Stakeholder Committee

---

**END OF MIGRATION STRATEGY**
