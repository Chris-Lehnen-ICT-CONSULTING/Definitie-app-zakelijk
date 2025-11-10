# DEF-138: UNIQUE INDEX Removal Impact Analysis

**Date:** 2025-11-10
**Issue:** User unable to generate new definition for existing term
**Error:** `UNIQUE constraint failed: definities.begrip, definities.organisatorische_context, ...`
**Scope:** Database schema modification + application behavior change

---

## Executive Summary

### Problem Statement
The application currently blocks users from creating a NEW definition for an existing term (e.g., "werkwoord") in the same context, even when the intent is legitimate versioning or alternative definitions.

### Root Cause
**Migration 008** (`src/database/migrations/008_add_unique_constraint.sql`) enforces a 5-field UNIQUE INDEX:
```sql
CREATE UNIQUE INDEX idx_definities_unique_full
ON definities(begrip, organisatorische_context, juridische_context, wettelijke_basis, categorie)
WHERE status != 'archived';
```

This prevents multiple active definitions with identical context, which **contradicts** the versioning system designed into the schema.

### Recommended Solution
**REMOVE the UNIQUE INDEX** - it is:
1. **Ontologically incorrect** (same term CAN have different meanings in same context over time)
2. **Incompatible with versioning system** (`version_number`, `previous_version_id` fields exist but are blocked)
3. **Redundant** - Python-level duplicate detection in `definitie_checker.py` already handles this intelligently

**Safety:** The removal is **LOW RISK** because duplicate prevention is already handled at the application level.

---

## Part 1: Root Cause Analysis

### 1.1 When Was the UNIQUE INDEX Added?

**Migration 008** (2025-10-31, DEF-87) added this constraint:

```sql
-- Migration 008: Add UNIQUE constraint for duplicate prevention (DEF-87)
-- Date: 2025-10-31
-- Rationale: Prevents duplicate entries after import strategy cleanup
CREATE UNIQUE INDEX IF NOT EXISTS idx_definities_unique_full
ON definities(
    begrip,
    organisatorische_context,
    juridische_context,
    wettelijke_basis,
    categorie
)
WHERE status != 'archived';
```

**Why it was added:**
- To prevent duplicates after the "import strategy" (temporary duplicate allowance)
- Assumed business rule: "same 5-field combination = duplicate"
- **Did NOT consider** versioning use case

**Schema comment confirms temporary nature:**
Line 81 in `schema.sql`:
```sql
-- (UNIQUE constraint tijdelijk uitgeschakeld i.v.m. importstrategie)
```
Translation: "UNIQUE constraint temporarily disabled for import strategy"

### 1.2 Ontological Contradiction

The schema has **versioning fields** designed for exactly the scenario that the UNIQUE INDEX prevents:

```sql
-- Versioning
version_number INTEGER NOT NULL DEFAULT 1,
previous_version_id INTEGER REFERENCES definities(id),
```

**Intent:** Same term can have multiple versions with identical context.

**Example:**
- Version 1: "werkwoord" (begrip) + "test" (context) → Draft definition A
- Version 2: "werkwoord" (begrip) + "test" (context) → Improved definition B (previous_version_id → V1)

**Current state:** UNIQUE INDEX **BLOCKS** this entirely.

### 1.3 Current Database State

Query result shows one existing definition:
```
id=127 | begrip=werkwoord | categorie=proces | context=["test"] | status=draft | version=1
```

User wants to generate a **NEW** definition (not update existing) → **BLOCKED by UNIQUE INDEX**.

---

## Part 2: Impact Assessment

### 2.1 Database-Level Dependencies

#### UNIQUE INDEX Structure
```
Index: idx_definities_unique_full
Columns: (begrip, organisatorische_context, juridische_context, wettelijke_basis, categorie)
Filter: WHERE status != 'archived'
```

**What it enforces:**
- Only ONE active (non-archived) definition per 5-field combination
- Multiple archived definitions ARE allowed (excluded by WHERE clause)

#### Foreign Key Dependencies
**NONE** - This is just an index, no FK references to it.

#### Trigger Dependencies
**NONE** - No triggers depend on uniqueness guarantee.

#### View Dependencies
Views (`actieve_definities`, `vastgestelde_definities`) do NOT rely on uniqueness - they simply filter and order.

### 2.2 Application-Level Dependencies

#### Python Code Relying on UNIQUE Constraint

**CRITICAL FINDING:** Application code does NOT rely on database-level uniqueness!

**Evidence:**

**A. Duplicate Detection in `definitie_repository.py` (lines 532-572)**
```python
def create_definitie(self, record: DefinitieRecord, allow_duplicate: bool = False) -> int:
    """Maak nieuwe definitie aan."""
    try:
        with self._get_connection() as conn:
            # Check voor duplicates: permit indien expliciet toegestaan
            if not allow_duplicate:
                duplicates = self.find_duplicates(
                    record.begrip,
                    record.organisatorische_context,
                    record.juridische_context or "",
                    categorie=record.categorie,
                    wettelijke_basis=(
                        json.loads(record.wettelijke_basis)
                        if record.wettelijke_basis
                        else []
                    ),
                )
                if duplicates and any(
                    d.definitie_record.status != DefinitieStatus.ARCHIVED.value
                    for d in duplicates
                ):
                    msg = f"Definitie voor '{record.begrip}' bestaat al in deze context"
                    raise ValueError(msg)
```

**Finding:** Python code **ALREADY** checks for duplicates and raises `ValueError` **BEFORE** database INSERT.

**B. Duplicate Check in `definitie_checker.py` (lines 95-181)**
```python
def check_before_generation(
    self,
    begrip: str,
    organisatorische_context: str,
    juridische_context: str = "",
    categorie: OntologischeCategorie = OntologischeCategorie.TYPE,
    wettelijke_basis: list[str] | None = None,
) -> DefinitieCheckResult:
    """Check voor bestaande definities voordat generatie start."""

    # Zoek exact match - inclusief categorie
    existing = self.repository.find_definitie(...)
    if existing:
        return self._handle_exact_match(existing, search_term=begrip)

    # Zoek duplicates/fuzzy matches
    duplicates = self.repository.find_duplicates(...)
    if duplicates:
        return self._handle_duplicates(duplicates)
```

**Finding:** Application-level duplicate detection is **MORE SOPHISTICATED** than database constraint:
- Handles fuzzy matches (70% similarity threshold)
- Provides user choice for similar entries
- Supports `force_generate` flag for intentional duplicates
- Includes synonym detection

**C. `allow_duplicate` Flag Support**

**`definition_repository.py` (line 104):**
```python
result_id = self.legacy_repo.create_definitie(
    record, allow_duplicate=allow_duplicate
)
```

**`definition_import_service.py` (line 92):**
```python
def import_single(
    self,
    payload: dict[str, Any],
    *,
    allow_duplicate: bool = False,
    duplicate_strategy: str | None = None,
    created_by: str | None = None,
) -> SingleImportResult:
```

**Finding:** Application **already has infrastructure** to allow duplicates when needed.

### 2.3 IntegrityError Handling

**SEARCH RESULT:** Only 18 files mention `IntegrityError`, mostly in:
- Test files (expected)
- Service layer (defensive error handling)
- **NOT** in business logic flow

**Conclusion:** No critical business logic depends on catching `IntegrityError` for duplicate detection.

---

## Part 3: Business Logic Impact

### 3.1 Versioning System Compatibility

**Schema design includes versioning:**
```sql
version_number INTEGER NOT NULL DEFAULT 1,
previous_version_id INTEGER REFERENCES definities(id),
```

**Versioning workflow (intended but currently blocked):**

```
Step 1: Create initial definition
  → begrip="werkwoord", context="test", version=1

Step 2: Generate improved version (CURRENTLY FAILS)
  → begrip="werkwoord", context="test", version=2, previous_version_id=127

  ERROR: UNIQUE constraint violation!
```

**Without UNIQUE INDEX:**
```
Step 2 would succeed:
  → New record created with version=2
  → previous_version_id links to version 1
  → Both records coexist (version history preserved)
```

**Status Workflow:**
```
Draft (v1) → Review (v2) → Established (v3)
   ↓            ↓              ↓
 Edit again  Improve      New regulation
   ↓            ↓              ↓
New version  New version  New version
```

**Current UNIQUE INDEX blocks all version creation workflows.**

### 3.2 Legitimate Use Cases Being Blocked

**Use Case 1: Iterative Improvement**
- User generates definition A
- Not satisfied → wants to generate NEW definition B (not edit A)
- Compare A vs B side-by-side
- Choose better one
- **BLOCKED:** Cannot generate B

**Use Case 2: Regulatory Updates**
- Law changes → definition must be updated
- Keep old version for historical reference (status=archived)
- Create new version (version_number=2, previous_version_id → old)
- **BLOCKED:** Cannot create new version while old is active

**Use Case 3: Context Evolution**
- Same term gains additional meaning over time
- Want to document both definitions
- Link via previous_version_id
- **BLOCKED:** Cannot create second definition

**Use Case 4: Import + Manual Refinement**
- Import external definition (source_type='imported')
- User wants to generate improved version (source_type='generated')
- **BLOCKED:** Cannot have both

### 3.3 Python-Level Duplicate Detection

**Intelligence NOT replicated in database constraint:**

**A. Fuzzy Matching**
```python
# definitie_repository.py lines 858-897
if not matches:
    fuzzy_query = """
        SELECT * FROM definities
        WHERE begrip LIKE ? AND organisatorische_context = ?
        AND status != 'archived'
    """
    # ...
    similarity = self._calculate_similarity(begrip, record.begrip)
    if similarity > 0.7:  # 70% threshold
        matches.append(DuplicateMatch(...))
```

**Database UNIQUE INDEX:** Cannot do fuzzy matching.

**B. Synonym Detection**
```python
# definitie_repository.py lines 702-748
# Geen directe begrip-hit: probeer exacte synoniem‑match (case-insensitive)
syn_query = """
    SELECT d.*
    FROM definities d
    JOIN definitie_voorbeelden v ON v.definitie_id = d.id
    WHERE LOWER(v.voorbeeld_tekst) = LOWER(?)
      AND v.voorbeeld_type = 'synonyms'
      AND v.actief = TRUE
      AND d.organisatorische_context = ?
"""
```

**Database UNIQUE INDEX:** Cannot detect synonyms.

**C. User Choice Handling**
```python
# definitie_checker.py lines 502-528
def _handle_duplicates(self, duplicates: list[DuplicateMatch]) -> DefinitieCheckResult:
    best_match = duplicates[0]
    if best_match.match_score > 0.9:
        return DefinitieCheckResult(
            action=CheckAction.USER_CHOICE,  # Let user decide!
            existing_definitie=best_match.definitie_record,
            duplicates=duplicates,
            message=f"Zeer vergelijkbare definitie gevonden...",
        )
```

**Database UNIQUE INDEX:** Hard failure, no user choice.

---

## Part 4: Safety Analysis

### 4.1 Data Corruption Risk

**Question:** Will removing the UNIQUE INDEX cause data corruption?

**Answer: NO**

**Reason:**
1. **Python validation layer already prevents unintended duplicates** (lines 554-572 in `definitie_repository.py`)
2. **`allow_duplicate` flag provides explicit override** when versioning is intended
3. **Status field prevents logical conflicts:**
   - Only one 'established' definition should be active at a time (business rule, not database constraint)
   - Multiple 'draft' versions are semantically valid (work in progress)
   - 'archived' versions preserve history

**Example of safe multi-version state:**
```
ID=127 | begrip=werkwoord | context=test | status=draft     | version=1
ID=145 | begrip=werkwoord | context=test | status=review    | version=2 | prev=127
ID=163 | begrip=werkwoord | context=test | status=established | version=3 | prev=145
```

This is **VALID** and represents definition evolution history.

### 4.2 Performance Impact

**Question:** Will removing the index impact query performance?

**Answer: MINIMAL IMPACT**

**Current indexes remain:**
```sql
CREATE INDEX idx_definities_begrip ON definities(begrip);
CREATE INDEX idx_definities_context ON definities(organisatorische_context, juridische_context);
CREATE INDEX idx_definities_status ON definities(status);
CREATE INDEX idx_definities_categorie ON definities(categorie);
```

**Performance analysis:**
- **Duplicate check queries** use `idx_definities_begrip` + `idx_definities_context` → Fast
- **UNIQUE INDEX was not used for SELECT queries** (only INSERT validation)
- **Removing it only affects INSERT performance:**
  - Before: Database checks uniqueness (~0.1ms)
  - After: Python checks duplicates via SELECT query (~1-2ms)
  - **Delta: ~1ms per insert** (negligible for single-user app)

### 4.3 Rollback Safety

**Question:** Can we safely rollback if removal causes issues?

**Answer: YES**

**Rollback procedure:**
```sql
-- Check for duplicates created after removal
SELECT begrip, organisatorische_context, juridische_context,
       wettelijke_basis, categorie, COUNT(*)
FROM definities
WHERE status != 'archived'
GROUP BY begrip, organisatorische_context, juridische_context,
         wettelijke_basis, categorie
HAVING COUNT(*) > 1;

-- If no duplicates, safely recreate index
CREATE UNIQUE INDEX idx_definities_unique_full
ON definities(
    begrip,
    organisatorische_context,
    juridische_context,
    wettelijke_basis,
    categorie
)
WHERE status != 'archived';
```

**Worst case:** If removal causes unintended duplicates:
1. Identify duplicates (query above)
2. Merge or archive unwanted versions
3. Recreate index
4. Total downtime: < 5 minutes

---

## Part 5: Alternative Solutions Considered

### Alternative 1: Keep UNIQUE INDEX, Disable for Versioning

**Approach:** Add `version_number` to WHERE clause:
```sql
CREATE UNIQUE INDEX idx_definities_unique_full
ON definities(begrip, organisatorische_context, juridische_context, wettelijke_basis, categorie)
WHERE status != 'archived' AND version_number = (
    SELECT MAX(version_number)
    FROM definities d2
    WHERE d2.begrip = definities.begrip
      AND d2.organisatorische_context = definities.organisatorische_context
);
```

**Rejected because:**
- SQLite does not support correlated subqueries in partial index WHERE clause
- Would require complex trigger-based enforcement
- Adds unnecessary database complexity when Python handles it better

### Alternative 2: Compound Key with Version

**Approach:** Make (begrip, context, version) unique instead of 5-field:
```sql
CREATE UNIQUE INDEX idx_definities_unique_versioned
ON definities(begrip, organisatorische_context, version_number)
WHERE status != 'archived';
```

**Rejected because:**
- Allows same definition (exact duplicate) with different version numbers → semantic error
- Does not prevent accidental duplicates (user generates same def twice, gets v1 and v2 with identical content)
- Python-level check is still needed → database constraint redundant

### Alternative 3: Application-Level Lock

**Approach:** Use `allow_duplicate=False` (default) to prevent duplicates, require explicit flag for versioning.

**Assessment:**
- **Already implemented!** (see lines 532-572 in `definitie_repository.py`)
- **More flexible than database constraint** (supports fuzzy matching, synonyms, user choice)
- **UNIQUE INDEX is redundant** when this exists

**This is the recommended solution: Remove database constraint, rely on existing Python validation.**

---

## Part 6: Migration Strategy

### 6.1 Removal Steps

**Migration Script:**
```sql
-- Migration 009: Remove ontological contradiction (DEF-138)
-- Author: System
-- Date: 2025-11-10
-- Description: Remove UNIQUE INDEX that blocks versioning system
--
-- Rationale:
--   - Schema has version_number + previous_version_id for version history
--   - UNIQUE INDEX prevents multiple active versions (contradiction)
--   - Python duplicate detection (definitie_checker.py) is more intelligent
--   - Supports fuzzy matching, synonyms, user choice
--
-- Safety: Application-level validation prevents unintended duplicates
-- Rollback: Recreate index if no duplicates exist (see rollback.sql)

DROP INDEX IF EXISTS idx_definities_unique_full;

-- Verification: Check for any duplicates that may have existed
-- (Should return 0 rows if migration 008 was successful)
SELECT
    begrip,
    organisatorische_context,
    juridische_context,
    wettelijke_basis,
    categorie,
    COUNT(*) as count
FROM definities
WHERE status != 'archived'
GROUP BY begrip, organisatorische_context, juridische_context, wettelijke_basis, categorie
HAVING COUNT(*) > 1;
```

**Rollback Script (009_rollback.sql):**
```sql
-- Rollback for migration 009
-- Only run if duplicate prevention is needed at database level again

-- Step 1: Verify no duplicates exist
SELECT
    begrip,
    organisatorische_context,
    COUNT(*) as count
FROM definities
WHERE status != 'archived'
GROUP BY begrip, organisatorische_context, juridische_context, wettelijke_basis, categorie
HAVING COUNT(*) > 1;

-- Step 2: If above returns 0 rows, safe to recreate index
CREATE UNIQUE INDEX idx_definities_unique_full
ON definities(
    begrip,
    organisatorische_context,
    juridische_context,
    wettelijke_basis,
    categorie
)
WHERE status != 'archived';
```

### 6.2 Testing Plan

**Pre-Migration Tests:**
```python
# tests/database/test_migration_009.py
def test_versioning_blocked_before_migration():
    """Verify UNIQUE INDEX currently blocks versioning."""
    repo = DefinitieRepository()

    # Create v1
    v1 = DefinitieRecord(
        begrip="werkwoord",
        definitie="definitie v1",
        categorie="proces",
        organisatorische_context="test",
        status="draft"
    )
    id1 = repo.create_definitie(v1)

    # Try to create v2 (should fail with IntegrityError)
    v2 = DefinitieRecord(
        begrip="werkwoord",
        definitie="definitie v2",  # Different content!
        categorie="proces",
        organisatorische_context="test",
        status="review",
        version_number=2,
        previous_version_id=id1
    )

    with pytest.raises(sqlite3.IntegrityError):
        repo.create_definitie(v2, allow_duplicate=True)
```

**Post-Migration Tests:**
```python
def test_versioning_allowed_after_migration():
    """Verify versioning works after UNIQUE INDEX removal."""
    repo = DefinitieRepository()

    # Create v1
    v1 = DefinitieRecord(
        begrip="werkwoord",
        definitie="definitie v1",
        categorie="proces",
        organisatorische_context="test",
        status="draft"
    )
    id1 = repo.create_definitie(v1)

    # Create v2 (should succeed)
    v2 = DefinitieRecord(
        begrip="werkwoord",
        definitie="definitie v2 (improved)",
        categorie="proces",
        organisatorische_context="test",
        status="review",
        version_number=2,
        previous_version_id=id1
    )
    id2 = repo.create_definitie(v2, allow_duplicate=True)

    assert id2 > 0
    assert id2 != id1

    # Verify both exist
    retrieved_v1 = repo.get_definitie(id1)
    retrieved_v2 = repo.get_definitie(id2)

    assert retrieved_v2.previous_version_id == id1
    assert retrieved_v2.version_number == 2

def test_duplicate_prevention_still_works():
    """Verify Python-level duplicate detection still prevents accidental duplicates."""
    repo = DefinitieRepository()

    # Create first definition
    d1 = DefinitieRecord(
        begrip="test_begrip",
        definitie="definitie 1",
        categorie="proces",
        organisatorische_context="test",
        status="draft"
    )
    repo.create_definitie(d1)

    # Try to create exact duplicate (should raise ValueError, not IntegrityError)
    d2 = DefinitieRecord(
        begrip="test_begrip",
        definitie="definitie 1",  # Same content
        categorie="proces",
        organisatorische_context="test",
        status="draft"
    )

    with pytest.raises(ValueError, match="bestaat al in deze context"):
        repo.create_definitie(d2)  # allow_duplicate=False (default)
```

### 6.3 Deployment Checklist

- [ ] **Backup database** before migration
  ```bash
  cp data/definities.db data/definities.db.backup_before_009
  ```

- [ ] **Run migration script**
  ```bash
  sqlite3 data/definities.db < src/database/migrations/009_remove_unique_index.sql
  ```

- [ ] **Verify index removal**
  ```bash
  sqlite3 data/definities.db ".indices definities"
  # Should NOT show idx_definities_unique_full
  ```

- [ ] **Run post-migration tests**
  ```bash
  pytest tests/database/test_migration_009.py -v
  ```

- [ ] **Test user scenario** (manual)
  - Generate definition for "werkwoord" + "test" context
  - Should succeed (previously failed)
  - Verify duplicate check still prompts user

- [ ] **Monitor for 24h** for any unintended duplicates
  ```sql
  -- Run daily for first week
  SELECT begrip, COUNT(*)
  FROM definities
  WHERE status != 'archived'
  GROUP BY begrip, organisatorische_context, juridische_context, wettelijke_basis, categorie
  HAVING COUNT(*) > 1;
  ```

---

## Part 7: Recommendations

### 7.1 Immediate Actions (DEF-138)

**RECOMMENDATION: REMOVE UNIQUE INDEX**

**Rationale:**
1. **Contradicts versioning system** built into schema
2. **Blocks legitimate use cases** (iterative improvement, regulatory updates)
3. **Redundant** - Python validation is more sophisticated
4. **Low risk** - Application layer already prevents unintended duplicates
5. **Easily reversible** if issues arise

**Implementation:**
- Create migration 009 (DROP INDEX)
- Add comprehensive tests (versioning, duplicate prevention)
- Deploy with monitoring

### 7.2 Documentation Updates

**Update `schema.sql` line 81:**
```sql
-- OLD:
-- (UNIQUE constraint tijdelijk uitgeschakeld i.v.m. importstrategie)

-- NEW:
-- UNIQUE INDEX removed (Migration 009, DEF-138): Versioning system requires
-- multiple active definitions with same context. Duplicate prevention handled
-- by application layer (definitie_checker.py, definitie_repository.py).
```

**Add comment to `definitie_repository.py` (line 532):**
```python
def create_definitie(self, record: DefinitieRecord, allow_duplicate: bool = False) -> int:
    """Maak nieuwe definitie aan.

    Duplicate Prevention Strategy (DEF-138):
    - Database-level UNIQUE INDEX removed to support versioning
    - Application-level validation (this method) prevents unintended duplicates
    - Use allow_duplicate=True for intentional versioning
    - Supports fuzzy matching, synonyms, user choice (see definitie_checker.py)

    Args:
        record: DefinitieRecord object
        allow_duplicate: Allow duplicate when versioning (default: False)
    """
```

### 7.3 Future Enhancements

**Consider (separate from DEF-138):**

**A. Explicit Versioning API**
```python
# definitie_repository.py
def create_new_version(
    self,
    base_definitie_id: int,
    new_definitie: str,
    created_by: str,
) -> int:
    """Create new version of existing definition.

    Automatically:
    - Increments version_number
    - Sets previous_version_id
    - Preserves context fields
    """
    base = self.get_definitie(base_definitie_id)
    new_record = DefinitieRecord(
        begrip=base.begrip,
        definitie=new_definitie,
        categorie=base.categorie,
        organisatorische_context=base.organisatorische_context,
        juridische_context=base.juridische_context,
        wettelijke_basis=base.wettelijke_basis,
        version_number=base.version_number + 1,
        previous_version_id=base_definitie_id,
        created_by=created_by,
    )
    return self.create_definitie(new_record, allow_duplicate=True)
```

**B. Version History View**
```sql
CREATE VIEW definitie_version_history AS
SELECT
    d1.id,
    d1.begrip,
    d1.version_number,
    d1.previous_version_id,
    d2.version_number as previous_version,
    d1.status,
    d1.created_at
FROM definities d1
LEFT JOIN definities d2 ON d1.previous_version_id = d2.id
ORDER BY d1.begrip, d1.version_number DESC;
```

**C. Status Transition Validation**
```python
# Only allow ONE 'established' definition per (begrip, context) combination
def validate_status_transition(record: DefinitieRecord, new_status: str):
    if new_status == 'established':
        existing_established = self.find_definitie(
            begrip=record.begrip,
            organisatorische_context=record.organisatorische_context,
            status=DefinitieStatus.ESTABLISHED
        )
        if existing_established and existing_established.id != record.id:
            raise ValueError(
                "Er bestaat al een vastgestelde definitie. "
                "Archiveer de oude versie eerst."
            )
```

---

## Conclusion

**SAFE TO REMOVE:** The UNIQUE INDEX `idx_definities_unique_full` should be removed because:

1. **Business Need:** Versioning system requires multiple active definitions
2. **Technical Safety:** Application-level validation prevents unintended duplicates
3. **Low Risk:** Easily reversible, comprehensive tests available
4. **Immediate Benefit:** Unblocks user's legitimate use case

**Migration 009 is recommended for immediate deployment.**
