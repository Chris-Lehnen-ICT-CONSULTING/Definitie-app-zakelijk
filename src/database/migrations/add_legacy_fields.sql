-- Migration script om legacy velden toe te voegen voor backward compatibility
-- Deze velden worden gebruikt door de UI maar missen in het nieuwe schema

-- Voeg datum_voorstel toe (datum waarop definitie is voorgesteld)
ALTER TABLE definities ADD COLUMN datum_voorstel TIMESTAMP;

-- Voeg ketenpartners toe (JSON array van ketenpartners die akkoord zijn)
ALTER TABLE definities ADD COLUMN ketenpartners TEXT;

-- Update bestaande records met default waardes
UPDATE definities 
SET datum_voorstel = created_at 
WHERE datum_voorstel IS NULL;

-- Voeg index toe voor snelle queries op datum_voorstel
CREATE INDEX idx_definities_datum_voorstel ON definities(datum_voorstel);