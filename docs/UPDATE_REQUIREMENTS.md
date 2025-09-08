---
aangemaakt: '08-09-2025'
applies_to: definitie-app@v2
bijgewerkt: '08-09-2025'
canonical: true
last_verified: 05-09-2025
owner: documentation
prioriteit: immediate
status: active
---



# UPDATE REQUIREMENTS - Post-Consolidation Documentation Fixes

## Executive Summary

Na de grote architectuur consolidatie (September 2025) zijn er nog verschillende documenten met verouderde references. Dit document inventariseert alle noodzakelijke updates en prioriteert deze volgens impact.

## 🔴 KRITIEK - Immediate Action Required

### 1. Non-Existent Directory References
**Problem**: Meerdere documenten verwijzen naar `/docs/architectuur/beslissingen/` die niet meer bestaat.

**Affected Files**:
- `/docs/architectuur/SOLUTION_ARCHITECTURE.md` (line 2784)
- `/docs/architectuur/ENTERPRISE_ARCHITECTURE.md` (line 768)
- `/docs/guidelines/CANONICAL_LOCATIONS.md` (line 21)
- `/docs/workflows/validation_orchestrator_rollout.md`
- `/docs/README.md` (line 13, 64)

**Fix**: Remove or update references to point to ADR sections within the main architecture documents.

### 2. Broken File References
**Problem**: References naar niet-bestaande bestanden.

**Affected Files**:
- `/docs/architectuur/TECHNICAL_ARCHITECTURE.md`:
  - Line: References `V2_AI_SERVICE_MIGRATIE_ANALYSE.md` (archived)
  - Line: References `../technisch/service-container.md` (doesn't exist)
  - Line: References `../technisch/AI_CONFIGURATION_GUIDE.md` (doesn't exist)

- `/docs/prd.md`:
  - References `V2_AI_SERVICE_MIGRATIE_BROWNFIELD.md`

- Multiple files reference `validation_orchestrator_v2.md` (archived):
  - `/docs/technisch/error_catalog_validation.md`
  - `/docs/development/validation_orchestrator_implementation.md`
  - `/docs/workflows/validation_orchestrator_rollout.md`
  - `/docs/architectuur/contracts/validation_result_contract.md`

**Fix**: Update to point to relevant sections in consolidated architecture documents.

## 🟡 HOOG - Should Fix Soon

### 3. Outdated Cross-References
**Problem**: Architecture documents still have old naming in cross-references.

**Current Status**:
- ENTERPRISE_ARCHITECTURE.md ✅ Correct frontmatter
- SOLUTION_ARCHITECTURE.md ⚠️ Needs check
- TECHNICAL_ARCHITECTURE.md ⚠️ Needs check

**Fix**: Ensure all three documents use consistent cross-reference naming.

### 4. CANONICAL_LOCATIONS.md Inconsistencies
**Problem**: Still lists `/docs/architectuur/beslissingen/` as Active.

**Fix**:
- Remove beslissingen directory reference (line 21)
- Update to clarify ADRs are now embedded in main documents
- Add note about consolidated architecture

## 🟢 GEMIDDELD - General Cleanup

### 5. Testen Documents
**Files to check**:
- `/docs/testing/CONSOLIDATION_VALIDATION_REPORT.md` - Has broken links
- `/docs/testing/PER-007-test-scenarios.md` - Check for outdated refs

### 6. Werkstroom Documents
**Files to update**:
- `/docs/workflows/TDD_TO_DEPLOYMENT_WORKFLOW.md`
- `/docs/workflows/validation_orchestrator_rollout.md`

### 7. Review Documents
**Old reviews referencing pre-consolidation structure**:
- `/docs/reviews/2025-08-28_full_code_review/CHECKLIST_DOCS.md`
- Contains references to old ADR files in beslissingen/

## 🔵 LAAG - Documentation Polish

### 8. CHANGELOG.md
- Contains CFR/PER-007 references that could be clarified
- Not broken, but could add context about consolidation

### 9. Archive References
- Various files reference archived documents
- Consider adding "(archived)" suffix to make clear

## Implementatie Plan

### Phase 1: Critical Fixes (Immediate)
**Time Estimate**: 1-2 hours
1. Remove all references to `/docs/architectuur/beslissingen/` directory
2. Fix broken file paths in TECHNICAL_ARCHITECTURE.md
3. Update validation_orchestrator_v2.md references

### Phase 2: High Prioriteit (Today)
**Time Estimate**: 1 hour
1. Update CANONICAL_LOCATIONS.md
2. Fix cross-references between architecture documents
3. Update prd.md references

### Phase 3: Medium Prioriteit (This Week)
**Time Estimate**: 2 hours
1. Review and update all testing documents
2. Update workflow documents
3. Clean up review documents

### Phase 4: Low Prioriteit (As Time Permits)
**Time Estimate**: 30 minutes
1. Polish CHANGELOG.md
2. Add archive indicators where helpful

## Validation Checklist

After fixes, verify:
- [ ] No grep results for "beslissingen/" outside archive
- [ ] No broken internal links (use link checker)
- [ ] All three architecture docs have matching cross-refs
- [ ] CANONICAL_LOCATIONS.md reflects actual structure
- [ ] No references to non-existent files
- [ ] All frontmatter is complete and accurate

## Search Commands for Verification

```bash
# Find all beslissingen references
grep -r "beslissingen/" docs --include="*.md" | grep -v archief

# Find potential broken paths
grep -r "validation_orchestrator_v2\.md" docs --include="*.md" | grep -v archief
grep -r "V2_AI_SERVICE" docs --include="*.md" | grep -v archief

# Check for old architecture file names
grep -r "EA\.md\|SA\.md\|TA\.md" docs --include="*.md" | grep -v archief

# Find CFR references
grep -r "CFR-" docs --include="*.md" | grep -v archief
```

## Notes

- De consolidatie was succesvol maar liet enkele "loose ends" achter
- Focus op het verwijderen van references naar niet-bestaande directories
- Veel documenten zijn al correct, alleen kleine updates nodig
- Archive structure is goed, alleen actieve documenten need fixes

---
Generated: 05-09-2025
Next Review: After Phase 2 completion


### Compliance Referenties

- **ASTRA Controls:**
  - ASTRA-QUA-001: Kwaliteitsborging
  - ASTRA-SEC-002: Beveiliging by Design
- **NORA Principes:**
  - NORA-BP-07: Herbruikbaarheid
  - NORA-BP-12: Betrouwbaarheid
- **GEMMA Referenties:**
  - GEMMA-ARC-03: Architectuur patterns
- **Justice Sector:**
  - DJI/OM integratie vereisten
  - Rechtspraak compatibiliteit
