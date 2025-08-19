-- Migration: Add legacy metadata fields
-- Date: 2025-07-14
-- Purpose: Restore metadata fields from legacy application

-- Add datum_voorstel column
ALTER TABLE definities
ADD COLUMN datum_voorstel DATE;

-- Add voorgesteld_door column (use existing created_by if needed)
-- Note: created_by already exists, so we'll use that for voorgesteld_door

-- Add ketenpartners column (JSON array of partners)
ALTER TABLE definities
ADD COLUMN ketenpartners TEXT; -- JSON array of ketenpartner names

-- Update existing records with default values
UPDATE definities
SET datum_voorstel = DATE(created_at),
    ketenpartners = '[]'
WHERE datum_voorstel IS NULL;

-- Add index for datum_voorstel
CREATE INDEX idx_definities_datum_voorstel ON definities(datum_voorstel);
