# Requirements Fix Action Plan

**Priority:** IMMEDIATE
**Estimated Time:** 4-6 hours for critical fixes
**Impact:** Restores requirements traceability and accuracy

## Phase 1: Critical Fixes (Do Today)

### 1.1 Fix Epic Format Issues (30 minutes)

**Affected Files:** REQ-023 through REQ-037 and others

**Quick Fix Script:**
```bash
# Fix EPIC-2 to EPIC-002 format
for file in REQ-*.md; do
  sed -i.bak 's/EPIC-2/EPIC-002/g' "$file"
  sed -i.bak 's/\[EPIC-\([0-9]\)\]/[EPIC-00\1]/g' "$file"
done

# Verify changes
grep -h "epics:" REQ-*.md | sort -u
```

### 1.2 Update Source File References (2 hours)

**File Mapping Updates Needed:**

```yaml
# Old → New mappings
corrections:
  REQ-001:
    old: src/services/auth_service.py
    new: # No auth service exists - remove or mark as TODO

  REQ-004:
    old: src/ui/tabs/generatie_tab.py
    new: src/ui/tabs/generation_tab.py

  REQ-005:
    old: src/database/repositories/definition_repository.py
    new: src/services/definition_repository.py

  REQ-013 to REQ-037:
    old: config/toetsregels/regels/*.json
    new: src/toetsregels/regels/*.py

  REQ-018:
    old: src/services/unified_definition_generator.py
    new: src/services/definition_generator.py

  REQ-020:
    old: src/services/validation/validation_orchestrator_v2.py
    new: src/services/validation/orchestrator_v2.py
```

### 1.3 Fix Story References (1 hour)

**Invalid Stories to Remove/Update:**
- US-6.5 → Remove (doesn't exist)
- US-6.6 → Remove (doesn't exist)
- US-8.1, US-8.2, US-8.3 → Change to US-3.1 (web lookup stories)
- Add CFR.1 through CFR.6 where context flow is mentioned

### 1.4 Status Corrections (30 minutes)

**Change from "Done" to "In Progress":**
- REQ-005: SQL Injection Prevention (repository missing)
- REQ-018: Core Definition Generation (service renamed)
- REQ-022: Export Functionality (tab missing)
- REQ-023 through REQ-037: If JSON rules referenced

## Phase 2: High Priority Improvements (This Week)

### 2.1 Add SMART Criteria Template

Create template for missing criteria:
```markdown
## Acceptatiecriteria (SMART)

- **Specifiek:** [What exactly should happen]
- **Meetbaar:** [Metric with number, e.g., "< 5 seconds", "> 95%"]
- **Acceptabel:** [Why this is reasonable]
- **Relevant:** [How it supports the requirement]
- **Tijdgebonden:** [When or how often, e.g., "within 24 hours", "every request"]
```

### 2.2 Priority Requirements to Fix First

Focus on these high-impact requirements:
1. REQ-001: Authentication (security critical)
2. REQ-008: Performance (user experience)
3. REQ-023-037: Validation rules (core functionality)
4. REQ-038-039: External integrations (GPT-4, Wikipedia)

### 2.3 Domain Context Additions

For REQ-013 through REQ-022, add:
- Nederlandse rechtsterminologie
- ASTRA requirement references (e.g., "ASTRA-QUA-001")
- NORA principles (e.g., "NORA-BP-07")
- Justice sector specific requirements

## Phase 3: Automation & Prevention (Next Sprint)

### 3.1 Validation Script

```python
# requirements_validator.py
def validate_requirement(req_file):
    issues = []

    # Check source files exist
    for source in req['sources']:
        if not Path(source['path']).exists():
            issues.append(f"Missing file: {source['path']}")

    # Check epic format
    for epic in req['links']['epics']:
        if not re.match(r'EPIC-\d{3}', epic):
            issues.append(f"Invalid epic format: {epic}")

    # Check SMART criteria
    if 'moet' not in req['criteria']:
        issues.append("Missing measurable criteria")

    return issues
```

### 3.2 CI/CD Integration

Add GitHub Action:
```yaml
name: Validate Requirements
on:
  push:
    paths:
      - 'docs/requirements/*.md'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: python scripts/validate_requirements.py
```

## Quick Wins Checklist

- [ ] Run epic format fix script
- [ ] Update validation rule references (.json → .py)
- [ ] Remove non-existent story references
- [ ] Fix "Done" status for unimplemented requirements
- [ ] Add SMART criteria to REQ-001 through REQ-010
- [ ] Update MASTER-EPICS-USER-STORIES.md references
- [ ] Add Dutch context to domain requirements
- [ ] Create requirements validation script
- [ ] Document new file locations in CANONICAL_LOCATIONS.md

## Verification Commands

After fixes, run these checks:

```bash
# Check all source files exist
grep -h "path:" REQ-*.md | sed 's/.*path: //' | while read f; do
  [ -f "../../$f" ] || echo "Missing: $f"
done

# Verify epic format
grep -h "EPIC-" REQ-*.md | grep -v "EPIC-00" || echo "All epics properly formatted"

# Check for orphaned requirements
for req in REQ-*.md; do
  grep -q "epics:\|stories:" "$req" || echo "Orphaned: $req"
done
```

## Expected Outcomes

After completing Phase 1:
- ✅ All epic references properly formatted
- ✅ Source files correctly referenced or marked TODO
- ✅ No false "Done" status
- ✅ Valid story links only

After completing Phase 2:
- ✅ All high-priority requirements have SMART criteria
- ✅ Domain requirements include Dutch legal context
- ✅ Clear traceability from requirements to implementation

After completing Phase 3:
- ✅ Automated validation prevents future issues
- ✅ CI/CD catches problems before merge
- ✅ Requirements stay synchronized with code

---

**Note:** Save original files before bulk updates:
```bash
tar -czf requirements_backup_$(date +%Y%m%d).tar.gz REQ-*.md
```
