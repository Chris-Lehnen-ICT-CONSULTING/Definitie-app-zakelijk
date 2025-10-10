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

    -- Context informatie (canoniek als JSON arrays in TEXT)
    organisatorische_context TEXT NOT NULL DEFAULT '[]', -- JSON array
    juridische_context TEXT NOT NULL DEFAULT '[]',       -- JSON array
    wettelijke_basis TEXT NOT NULL DEFAULT '[]',         -- JSON array

    -- UFO-categorie (OntoUML/UFO metamodel) — optioneel selectievak in UI
    ufo_categorie TEXT CHECK (ufo_categorie IN (
        'Kind','Event','Role','Phase','Relator','Mode','Quantity','Quality',
        'Subkind','Category','Mixin','RoleMixin','PhaseMixin','Abstract','Relatie','Event Composition'
    )),

    -- Procesmatige velden
    toelichting_proces TEXT, -- Procesmatige toelichting/opmerkingen (voor review/validatie notities)

    -- Status management
    status VARCHAR(50) NOT NULL DEFAULT 'draft' CHECK (status IN ('imported', 'draft', 'review', 'established', 'archived')),

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

    -- Voorkeursterm op definitie‑niveau (single source of truth)
    voorkeursterm TEXT

    -- (UNIQUE constraint tijdelijk uitgeschakeld i.v.m. importstrategie)
);

-- Index voor snelle lookups
CREATE INDEX idx_definities_begrip ON definities(begrip);
CREATE INDEX idx_definities_context ON definities(organisatorische_context, juridische_context);
CREATE INDEX idx_definities_status ON definities(status);
CREATE INDEX idx_definities_categorie ON definities(categorie);
CREATE INDEX idx_definities_created_at ON definities(created_at);
CREATE INDEX idx_definities_datum_voorstel ON definities(datum_voorstel);

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
    wijziging_type VARCHAR(50) NOT NULL CHECK (wijziging_type IN ('created', 'updated', 'status_changed', 'approved', 'archived', 'auto_save')),
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
            'juridische_context', NEW.juridische_context,
            'wettelijke_basis', NEW.wettelijke_basis
        )
    );
END;

-- Voorbeelden tabel - voor gegenereerde voorbeelden bij definities
CREATE TABLE definitie_voorbeelden (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Referentie naar definitie
    definitie_id INTEGER NOT NULL REFERENCES definities(id) ON DELETE CASCADE,

    -- Voorbeeld informatie
    voorbeeld_type VARCHAR(50) NOT NULL CHECK (voorbeeld_type IN ('sentence', 'practical', 'counter', 'synonyms', 'antonyms', 'explanation')),
    voorbeeld_tekst TEXT NOT NULL,
    voorbeeld_volgorde INTEGER DEFAULT 1,

    -- Voorkeursterm indicator verwijderd; voorkeursterm wordt op definitie‑niveau opgeslagen

    -- Generation metadata
    gegenereerd_door VARCHAR(50) DEFAULT 'system',
    generation_model VARCHAR(50),
    generation_parameters TEXT, -- JSON met generation parameters

    -- Status
    actief BOOLEAN NOT NULL DEFAULT TRUE,
    beoordeeld BOOLEAN NOT NULL DEFAULT FALSE,
    beoordeeling VARCHAR(50), -- 'goed', 'matig', 'slecht'
    beoordeeling_notities TEXT,
    beoordeeld_door VARCHAR(255),
    beoordeeld_op TIMESTAMP,

    -- Metadata
    aangemaakt_op TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    bijgewerkt_op TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(definitie_id, voorbeeld_type, voorbeeld_volgorde)
);

CREATE INDEX idx_voorbeelden_definitie_id ON definitie_voorbeelden(definitie_id);
CREATE INDEX idx_voorbeelden_type ON definitie_voorbeelden(voorbeeld_type);
CREATE INDEX idx_voorbeelden_actief ON definitie_voorbeelden(actief);

-- Trigger voor bijgewerkt_op timestamp
CREATE TRIGGER update_voorbeelden_timestamp
    AFTER UPDATE ON definitie_voorbeelden
    FOR EACH ROW
    WHEN NEW.bijgewerkt_op = OLD.bijgewerkt_op
BEGIN
    UPDATE definitie_voorbeelden SET bijgewerkt_op = CURRENT_TIMESTAMP WHERE id = NEW.id;
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

-- ========================================
-- SYNONYM SYSTEM (GRAPH-BASED)
-- ========================================
-- Architecture: Synonym Orchestrator Architecture v3.1
-- Purpose: Unified graph-based synonym registry
-- Related: docs/architectuur/synonym-orchestrator-architecture-v3.1.md

-- Synonym Groups (expliciete groepering van gerelateerde termen)
CREATE TABLE synonym_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Core Information
    canonical_term TEXT NOT NULL UNIQUE,  -- "Voorkeurs" term voor display
    domain TEXT,                           -- "strafrecht", "civielrecht", etc. (optional)

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT
);

-- Synonym Group Members (alle synoniemen als peers - geen hiërarchie!)
CREATE TABLE synonym_group_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Group Relationship
    group_id INTEGER NOT NULL,
    term TEXT NOT NULL,

    -- Weighting & Priority
    weight REAL DEFAULT 1.0 CHECK(weight >= 0.0 AND weight <= 1.0),
    is_preferred BOOLEAN DEFAULT FALSE,  -- Top-5 priority flag

    -- Lifecycle Status
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN (
        'active',         -- In gebruik, beschikbaar voor queries
        'ai_pending',     -- GPT-4 suggestie, wacht op approval
        'rejected_auto',  -- Afgewezen door reviewer
        'deprecated'      -- Niet meer gebruikt (manual edit removed)
    )),

    -- Source Tracking
    source TEXT NOT NULL CHECK(source IN (
        'db_seed',        -- Initiële migratie vanuit oude DB
        'manual',         -- Handmatig toegevoegd door gebruiker
        'ai_suggested',   -- GPT-4 suggestie
        'imported_yaml'   -- Migratie vanuit juridische_synoniemen.yaml (legacy)
    )),

    -- Context & Rationale
    context_json TEXT,  -- JSON: {"rationale": "...", "model": "gpt-4", "temperature": 0.3}

    -- Scoping (global vs per-definitie)
    definitie_id INTEGER,  -- NULL = global, anders scoped to definitie

    -- Analytics
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,

    -- Audit Trail
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    reviewed_by TEXT,
    reviewed_at TIMESTAMP,

    -- Constraints
    FOREIGN KEY(group_id) REFERENCES synonym_groups(id) ON DELETE CASCADE,
    FOREIGN KEY(definitie_id) REFERENCES definities(id) ON DELETE CASCADE,
    UNIQUE(group_id, term)  -- Een term kan maar 1x per groep
);

-- Indexes voor performance (bidirectionele lookups)
CREATE INDEX idx_sgm_group ON synonym_group_members(group_id);
CREATE INDEX idx_sgm_term ON synonym_group_members(term);
CREATE INDEX idx_sgm_status ON synonym_group_members(status);
CREATE INDEX idx_sgm_preferred ON synonym_group_members(is_preferred);
CREATE INDEX idx_sgm_definitie ON synonym_group_members(definitie_id);
CREATE INDEX idx_sgm_usage ON synonym_group_members(usage_count DESC);
CREATE INDEX idx_sgm_term_status ON synonym_group_members(term, status);
CREATE INDEX idx_sgm_group_status ON synonym_group_members(group_id, status);

-- Triggers voor automatische timestamps
CREATE TRIGGER update_synonym_groups_timestamp
    AFTER UPDATE ON synonym_groups
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE synonym_groups SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER update_synonym_group_members_timestamp
    AFTER UPDATE ON synonym_group_members
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE synonym_group_members SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
