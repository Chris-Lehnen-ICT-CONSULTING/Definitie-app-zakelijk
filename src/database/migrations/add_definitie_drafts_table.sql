-- Migration: Add definitie_drafts table for single auto-save slot per definition
-- Date: 2025-10-04
-- Purpose: Separate auto-save from version history to reduce UI clutter

-- Create drafts table with REPLACE INTO support (one draft per definition)
CREATE TABLE IF NOT EXISTS definitie_drafts (
    definitie_id INTEGER PRIMARY KEY REFERENCES definities(id) ON DELETE CASCADE,

    -- Draft content (complete snapshot)
    draft_content TEXT NOT NULL, -- JSON snapshot of all fields

    -- Metadata
    saved_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    saved_by VARCHAR(255) DEFAULT 'system'
);

CREATE INDEX IF NOT EXISTS idx_drafts_saved_at ON definitie_drafts(saved_at);

-- Migrate existing auto_save entries from geschiedenis to drafts
-- Keep only the LATEST auto_save per definitie_id
INSERT OR REPLACE INTO definitie_drafts (definitie_id, draft_content, saved_at, saved_by)
SELECT
    dg.definitie_id,
    dg.context_snapshot,
    dg.gewijzigd_op,
    dg.gewijzigd_door
FROM definitie_geschiedenis dg
INNER JOIN (
    -- Get latest auto_save per definitie_id
    SELECT definitie_id, MAX(gewijzigd_op) as max_datum
    FROM definitie_geschiedenis
    WHERE wijziging_type = 'auto_save'
    GROUP BY definitie_id
) latest ON dg.definitie_id = latest.definitie_id AND dg.gewijzigd_op = latest.max_datum
WHERE dg.wijziging_type = 'auto_save';

-- Clean up old auto_save entries from geschiedenis (keep history clean)
DELETE FROM definitie_geschiedenis WHERE wijziging_type = 'auto_save';
