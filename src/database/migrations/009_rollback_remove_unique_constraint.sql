-- Rollback Migration 009: Restore UNIQUE constraint
-- Author: System (emergency rollback)
-- Date: 2025-11-10
-- Description: Restores the UNIQUE INDEX that was removed in migration 009.
--
-- WARNING: This rollback will FAIL if duplicate records exist in database!
--          Run cleanup script BEFORE rolling back.
--
-- Prerequisites:
--   - No duplicate records in definities table (status != 'archived')
--   - Run verification query below to check for duplicates first
--
-- Verification query (MUST return 0 rows before rollback):
-- SELECT begrip, organisatorische_context, juridische_context,
--        wettelijke_basis, categorie, COUNT(*) as count
-- FROM definities
-- WHERE status != 'archived'
-- GROUP BY begrip, organisatorische_context, juridische_context,
--          wettelijke_basis, categorie
-- HAVING COUNT(*) > 1;
--
-- If duplicates exist, clean them up first:
-- Option 1: Manual cleanup (keep most recent, archive others)
-- Option 2: Merge duplicates (combine information, archive old ones)
-- Option 3: Delete duplicates (if they are truly redundant)

-- Restore the UNIQUE INDEX (exact copy from migration 008)
CREATE UNIQUE INDEX IF NOT EXISTS idx_definities_unique_full
ON definities(
    begrip,
    organisatorische_context,
    juridische_context,
    wettelijke_basis,
    categorie
)
WHERE status != 'archived';

-- Verification query (should return 1):
-- SELECT COUNT(*) FROM sqlite_master
-- WHERE type='index' AND name='idx_definities_unique_full';

-- If this migration fails with "UNIQUE constraint failed":
-- 1. Duplicates exist in the database
-- 2. Run the verification query above to find them
-- 3. Clean up duplicates manually
-- 4. Retry this migration
