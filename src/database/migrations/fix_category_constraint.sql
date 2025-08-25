-- Migration: Fix Category-Aware Unique Constraint
--
-- Problem: The current UNIQUE constraint prevents multiple definitions
-- with the same begrip+context but different categories, blocking
-- legitimate category-based regeneration.
--
-- Solution: Update UNIQUE constraint to include categorie field.

-- Step 1: Create new table with updated constraint
CREATE TABLE definities_new (
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

    -- UPDATED: Category-aware unique constraint (includes categorie)
    -- This allows multiple definitions for the same begrip+context with different categories
    UNIQUE(begrip, organisatorische_context, juridische_context, categorie, status)
);

-- Step 2: Copy data from old table to new table
INSERT INTO definities_new SELECT * FROM definities;

-- Step 3: Drop old table
DROP TABLE definities;

-- Step 4: Rename new table to original name
ALTER TABLE definities_new RENAME TO definities;

-- Step 5: Recreate indexes
CREATE INDEX idx_definities_begrip ON definities(begrip);
CREATE INDEX idx_definities_context ON definities(organisatorische_context, juridische_context);
CREATE INDEX idx_definities_status ON definities(status);
CREATE INDEX idx_definities_categorie ON definities(categorie);
CREATE INDEX idx_definities_created_at ON definities(created_at);
CREATE INDEX idx_definities_datum_voorstel ON definities(datum_voorstel);

-- Step 6: Recreate triggers (they reference the table)
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
