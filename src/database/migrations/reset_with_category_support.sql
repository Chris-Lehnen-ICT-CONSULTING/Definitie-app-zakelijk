-- Migration: Reset Database with Full Category Support
--
-- Since existing data is only test data, we can simply:
-- 1. Drop existing table
-- 2. Recreate with updated schema supporting all ontological categories
-- 3. Recreate indexes and triggers

-- Step 1: Drop existing table (test data can be lost)
DROP TABLE IF EXISTS definities;

-- Step 2: Recreate table with full ontological category support
CREATE TABLE definities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Kern informatie
    begrip VARCHAR(255) NOT NULL,
    definitie TEXT NOT NULL,
    categorie VARCHAR(50) NOT NULL CHECK (categorie IN (
        -- Basis categorieën (legacy support)
        'type', 'proces', 'resultaat', 'exemplaar',
        -- Uitgebreide ontologische categorieën
        'ENT',    -- Entiteit (type/klasse)
        'ACT',    -- Activiteit (proces/handeling)
        'REL',    -- Relatie (verband tussen entiteiten)
        'ATT',    -- Attribuut (eigenschap/kenmerk)
        'AUT',    -- Autorisatie (bevoegdheid/rechten)
        'STA',    -- Status (toestand/fase)
        'OTH'     -- Overig (niet-gecategoriseerd)
    )),

    -- Context informatie
    organisatorische_context VARCHAR(255) NOT NULL,
    juridische_context VARCHAR(255),

    -- Status management
    status VARCHAR(50) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'review', 'established', 'archived')),

    -- Versioning
    version_number INTEGER NOT NULL DEFAULT 1,
    previous_version_id INTEGER REFERENCES definities(id),

    -- Validation informatie
    validation_score DECIMAL(3,2),
    validation_date TIMESTAMP,
    validation_issues TEXT, -- JSON array van validation issues

    -- Source tracking
    source_type VARCHAR(50) DEFAULT 'generated' CHECK (source_type IN ('generated', 'imported', 'manual')),
    source_reference VARCHAR(500),
    imported_from VARCHAR(255),

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_by VARCHAR(255),

    -- Approval workflow
    approved_by VARCHAR(255),
    approved_at TIMESTAMP,
    approval_notes TEXT,

    -- Export tracking
    last_exported_at TIMESTAMP,
    export_destinations TEXT, -- JSON array van export locaties

    -- Legacy metadata fields
    datum_voorstel DATE,
    ketenpartners TEXT, -- JSON array van ketenpartner namen

    -- FIXED: Category-aware unique constraint (includes categorie)
    -- This allows multiple definitions for the same begrip+context with different categories
    UNIQUE(begrip, organisatorische_context, juridische_context, categorie, status)
);

-- Step 3: Recreate indexes
CREATE INDEX idx_definities_begrip ON definities(begrip);
CREATE INDEX idx_definities_context ON definities(organisatorische_context, juridische_context);
CREATE INDEX idx_definities_status ON definities(status);
CREATE INDEX idx_definities_categorie ON definities(categorie);
CREATE INDEX idx_definities_created_at ON definities(created_at);
CREATE INDEX idx_definities_datum_voorstel ON definities(datum_voorstel);

-- Step 4: Recreate triggers
CREATE TRIGGER update_definities_timestamp
    AFTER UPDATE ON definities
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE definities SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER log_definitie_changes
    AFTER UPDATE ON definities
    FOR EACH ROW
BEGIN
    INSERT INTO definitie_geschiedenis (
        definitie_id, begrip, definitie_oude_waarde, definitie_nieuwe_waarde,
        wijziging_type, gewijzigd_door, context_snapshot
    ) VALUES (
        NEW.id, NEW.begrip, OLD.definitie, NEW.definitie,
        CASE
            WHEN OLD.status != NEW.status THEN 'status_changed'
            WHEN OLD.definitie != NEW.definitie THEN 'updated'
            ELSE 'updated'
        END,
        NEW.updated_by,
        json_object(
            'oude_status', OLD.status,
            'nieuwe_status', NEW.status,
            'organisatorische_context', NEW.organisatorische_context,
            'juridische_context', NEW.juridische_context,
            'categorie', NEW.categorie
        )
    );
END;
