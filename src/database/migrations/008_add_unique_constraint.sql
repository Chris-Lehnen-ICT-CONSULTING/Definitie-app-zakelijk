-- Migration 008: Add UNIQUE constraint for duplicate prevention (DEF-87)
-- Author: System (automated fix)
-- Date: 2025-10-31
-- Description: Enforces business rule that combination of 5 fields must be unique:
--              (begrip, organisatorische_context, juridische_context, wettelijke_basis, categorie)
--              This prevents duplicate entries that were previously allowed when the constraint
--              was temporarily disabled for import strategy.
--
-- Business Rule Rationale:
--   Same begrip can have different definitions based on:
--   - Different organisatorische_context (e.g., "Politie" vs "OM")
--   - Different juridische_context (e.g., "Strafrecht" vs "Bestuursrecht")
--   - Different wettelijke_basis (e.g., "Wetboek van Strafrecht" vs "Algemene wet bestuursrecht")
--   - Different categorie (e.g., "type" vs "proces" vs "resultaat")
--
-- Prerequisites:
-- - All duplicates must be cleaned up first (run scripts/cleanup_duplicates.py)
-- - Records with status='archived' are excluded from the constraint
--
-- Rollback: DROP INDEX IF EXISTS idx_definities_unique_full;

-- Add UNIQUE INDEX to enforce full 5-field uniqueness
-- Uses partial index to exclude archived records
CREATE UNIQUE INDEX IF NOT EXISTS idx_definities_unique_full
ON definities(
    begrip,
    organisatorische_context,
    juridische_context,
    wettelijke_basis,
    categorie
)
WHERE status != 'archived';

-- Verification query (should return 0):
-- SELECT COUNT(*) FROM (
--     SELECT begrip, organisatorische_context
--     FROM definities
--     WHERE status != 'archived'
--     GROUP BY begrip, organisatorische_context
--     HAVING COUNT(*) > 1
-- );
