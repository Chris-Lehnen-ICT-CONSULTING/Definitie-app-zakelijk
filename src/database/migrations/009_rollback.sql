-- Rollback for Migration 009: Recreate UNIQUE INDEX (DEF-138)
-- Date: 2025-11-10
-- Description: Rollback versioning enablement if issues occur
--
-- WARNING: This rollback will FAIL if any version history has been created
-- since migration 009 was applied (multiple active definitions with same context)
--
-- Prerequisites:
--   1. No duplicates exist (run verification query below)
--   2. All version history must be merged/archived first
--   3. Business approval to disable versioning system
--
-- Only run this if you need to restore database-level duplicate prevention
-- and are willing to sacrifice versioning capability.

-- Step 1: VERIFICATION - Check for duplicates created after migration 009
-- Copy output before proceeding!
SELECT
    begrip,
    organisatorische_context,
    juridische_context,
    wettelijke_basis,
    categorie,
    COUNT(*) as duplicate_count,
    GROUP_CONCAT(id) as definition_ids,
    GROUP_CONCAT(status) as statuses,
    GROUP_CONCAT(version_number) as versions
FROM definities
WHERE status != 'archived'
GROUP BY begrip, organisatorische_context, juridische_context, wettelijke_basis, categorie
HAVING COUNT(*) > 1;

-- Step 2: If above query returns rows, you must choose which versions to keep
-- Example cleanup (MODIFY AS NEEDED):
--
-- Option A: Keep highest version, archive rest
-- UPDATE definities SET status = 'archived'
-- WHERE id IN (
--     SELECT d1.id
--     FROM definities d1
--     JOIN (
--         SELECT begrip, organisatorische_context, MAX(version_number) as max_version
--         FROM definities
--         WHERE status != 'archived'
--         GROUP BY begrip, organisatorische_context
--     ) d2 ON d1.begrip = d2.begrip
--         AND d1.organisatorische_context = d2.organisatorische_context
--     WHERE d1.version_number < d2.max_version
--       AND d1.status != 'archived'
-- );
--
-- Option B: Manual review - identify and update specific IDs
-- UPDATE definities SET status = 'archived' WHERE id IN (127, 145, ...);

-- Step 3: Verify no duplicates remain
SELECT COUNT(*) as remaining_duplicates
FROM (
    SELECT begrip, organisatorische_context, juridische_context, wettelijke_basis, categorie
    FROM definities
    WHERE status != 'archived'
    GROUP BY begrip, organisatorische_context, juridische_context, wettelijke_basis, categorie
    HAVING COUNT(*) > 1
);
-- MUST return 0 before proceeding!

-- Step 4: Recreate UNIQUE INDEX (ONLY if Step 3 shows 0 duplicates)
CREATE UNIQUE INDEX idx_definities_unique_full
ON definities(
    begrip,
    organisatorische_context,
    juridische_context,
    wettelijke_basis,
    categorie
)
WHERE status != 'archived';

-- Step 5: Verify index creation
SELECT name, sql
FROM sqlite_master
WHERE type = 'index'
  AND name = 'idx_definities_unique_full';

-- Rollback complete
-- WARNING: Versioning system is now DISABLED again
-- Users will get UNIQUE constraint errors when trying to create new versions
