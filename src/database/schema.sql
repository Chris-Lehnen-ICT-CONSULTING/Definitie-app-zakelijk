-- Database schema voor Definitie Management Systeem
-- Supports SQLite and PostgreSQL

-- ========================================
-- CORE TABLES
-- ========================================

-- Definities tabel - hoofd entiteit
CREATE TABLE definities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Kern informatie
    begrip VARCHAR(255) NOT NULL,
    definitie TEXT NOT NULL,
    categorie VARCHAR(50) NOT NULL CHECK (categorie IN ('type', 'proces', 'resultaat', 'exemplaar')),
    
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
    
    -- Unique constraint voor begrip + context combinatie (per versie)
    UNIQUE(begrip, organisatorische_context, juridische_context, status)
);

-- Index voor snelle lookups
CREATE INDEX idx_definities_begrip ON definities(begrip);
CREATE INDEX idx_definities_context ON definities(organisatorische_context, juridische_context);
CREATE INDEX idx_definities_status ON definities(status);
CREATE INDEX idx_definities_categorie ON definities(categorie);
CREATE INDEX idx_definities_created_at ON definities(created_at);

-- ========================================
-- SUPPORTING TABLES
-- ========================================

-- Definitie geschiedenis voor audit trail
CREATE TABLE definitie_geschiedenis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    definitie_id INTEGER NOT NULL REFERENCES definities(id) ON DELETE CASCADE,
    
    -- Snapshot van definitie op moment van wijziging
    begrip VARCHAR(255) NOT NULL,
    definitie_oude_waarde TEXT,
    definitie_nieuwe_waarde TEXT,
    
    -- Change metadata
    wijziging_type VARCHAR(50) NOT NULL CHECK (wijziging_type IN ('created', 'updated', 'status_changed', 'approved', 'archived')),
    wijziging_reden TEXT,
    
    -- User info
    gewijzigd_door VARCHAR(255),
    gewijzigd_op TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Context snapshot
    context_snapshot TEXT -- JSON van complete context op moment van wijziging
);

CREATE INDEX idx_geschiedenis_definitie_id ON definitie_geschiedenis(definitie_id);
CREATE INDEX idx_geschiedenis_datum ON definitie_geschiedenis(gewijzigd_op);

-- Tags/labels voor definitie categorisering
CREATE TABLE definitie_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    definitie_id INTEGER NOT NULL REFERENCES definities(id) ON DELETE CASCADE,
    tag_naam VARCHAR(100) NOT NULL,
    tag_waarde VARCHAR(255),
    
    -- Metadata
    toegevoegd_door VARCHAR(255),
    toegevoegd_op TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(definitie_id, tag_naam)
);

CREATE INDEX idx_tags_definitie_id ON definitie_tags(definitie_id);
CREATE INDEX idx_tags_naam ON definitie_tags(tag_naam);

-- Externe bron configuratie
CREATE TABLE externe_bronnen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Bron informatie
    bron_naam VARCHAR(255) NOT NULL UNIQUE,
    bron_type VARCHAR(50) NOT NULL CHECK (bron_type IN ('database', 'api', 'file', 'manual')),
    bron_url VARCHAR(500),
    
    -- Configuratie
    configuratie TEXT, -- JSON configuratie voor deze bron
    
    -- Credentials (encrypted)
    api_key_encrypted VARCHAR(500),
    gebruikersnaam VARCHAR(255),
    
    -- Status
    actief BOOLEAN NOT NULL DEFAULT TRUE,
    laatste_sync TIMESTAMP,
    laatste_sync_status VARCHAR(50),
    
    -- Metadata
    aangemaakt_op TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    aangemaakt_door VARCHAR(255)
);

-- Import/Export logs
CREATE TABLE import_export_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Operatie info
    operatie_type VARCHAR(50) NOT NULL CHECK (operatie_type IN ('import', 'export')),
    bron_bestemming VARCHAR(255) NOT NULL,
    
    -- Resultaten
    aantal_verwerkt INTEGER NOT NULL DEFAULT 0,
    aantal_succesvol INTEGER NOT NULL DEFAULT 0,
    aantal_gefaald INTEGER NOT NULL DEFAULT 0,
    
    -- Details
    bestand_pad VARCHAR(500),
    formaat VARCHAR(50), -- json, csv, xml, sql
    fouten_details TEXT, -- JSON array van fouten
    
    -- Metadata
    gestart_op TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    voltooid_op TIMESTAMP,
    gestart_door VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed', 'cancelled'))
);

CREATE INDEX idx_logs_operatie_type ON import_export_logs(operatie_type);
CREATE INDEX idx_logs_datum ON import_export_logs(gestart_op);

-- ========================================
-- VIEWS VOOR CONVENIENCE
-- ========================================

-- View voor actieve (niet-gearchiveerde) definities
CREATE VIEW actieve_definities AS
SELECT * FROM definities 
WHERE status != 'archived'
ORDER BY begrip, created_at DESC;

-- View voor vastgestelde definities
CREATE VIEW vastgestelde_definities AS
SELECT * FROM definities 
WHERE status = 'established'
ORDER BY begrip, approved_at DESC;

-- View voor definitie statistieken
CREATE VIEW definitie_statistieken AS
SELECT 
    categorie,
    organisatorische_context,
    status,
    COUNT(*) as aantal,
    AVG(validation_score) as gemiddelde_score,
    MIN(created_at) as eerste_definitie,
    MAX(updated_at) as laatste_update
FROM definities
GROUP BY categorie, organisatorische_context, status;

-- ========================================
-- TRIGGERS VOOR DATA INTEGRITEIT
-- ========================================

-- Trigger voor automatische updated_at
CREATE TRIGGER update_definities_timestamp 
    AFTER UPDATE ON definities
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE definities SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger voor geschiedenis logging
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
            'juridische_context', NEW.juridische_context
        )
    );
END;

-- ========================================
-- SAMPLE DATA (voor testing)
-- ========================================

-- Voorbeelden van statuses en categorieën
INSERT INTO definities (
    begrip, definitie, categorie, organisatorische_context, juridische_context,
    status, validation_score, created_by, source_type
) VALUES 
(
    'verificatie', 
    'Proces waarbij identiteitsgegevens systematisch worden gecontroleerd tegen authentieke bronregistraties',
    'proces',
    'DJI',
    'strafrecht',
    'established',
    0.95,
    'system',
    'generated'
),
(
    'registratie',
    'Handeling waarbij gegevens worden vastgelegd in een gestructureerd systeem voor latere raadpleging',
    'proces',
    'OM',
    '',
    'draft',
    0.78,
    'system',
    'generated'
);

-- Sample tags
INSERT INTO definitie_tags (definitie_id, tag_naam, tag_waarde, toegevoegd_door) VALUES
(1, 'prioriteit', 'hoog', 'admin'),
(1, 'thema', 'identiteit', 'admin'),
(2, 'prioriteit', 'medium', 'admin'),
(2, 'thema', 'data_management', 'admin');