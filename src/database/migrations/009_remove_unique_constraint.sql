-- Migration 009: Remove UNIQUE constraint to allow multiple definitions (DESIGN-2025-11-10)
-- Author: System (AI-assisted design)
-- Date: 2025-11-10
-- Description: Removes the UNIQUE INDEX constraint that was added in migration 008.
--              This allows multiple definitions with same attributes (begrip, context,
--              categorie, wettelijke_basis) to be created. Duplicate detection remains
--              at application level (Python code) as warning-only mechanism.
--
-- Business Rationale:
--   - The constraint was marked as temporary in schema.sql line 81
--   - Import strategy requires flexibility to create similar definitions
--   - Application-level duplicate detection provides better UX (warnings vs hard blocks)
--   - Users need ability to create contextually similar definitions
--
-- Prerequisites:
--   - Migration 008 must have been applied (UNIQUE INDEX exists)
--   - No code changes required (Python duplicate check remains)
--
-- Rollback: Re-apply migration 008 or use 009_rollback_remove_unique_constraint.sql

-- Drop the UNIQUE INDEX created in migration 008
DROP INDEX IF EXISTS idx_definities_unique_full;

-- Verification query (should return index count = 0):
-- SELECT COUNT(*) FROM sqlite_master
-- WHERE type='index' AND name='idx_definities_unique_full';

-- After this migration:
-- - Multiple definitions with identical attributes CAN be created
-- - Python code in definitie_repository.find_duplicates() still detects them
-- - UI will show warnings but allow creation (if user confirms)
-- - Database integrity relies on application logic (not SQL constraints)
