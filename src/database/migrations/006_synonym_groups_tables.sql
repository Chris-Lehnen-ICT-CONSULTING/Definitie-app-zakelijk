-- Migration: Add synonym_groups and synonym_group_members tables voor graph-based synonym system
-- Created: 2025-10-09
-- Purpose: Implements unified graph-based synonym registry (Architecture v3.1)
--
-- Architecture: Synonym Orchestrator Architecture v3.1
-- - Graph-based model: symmetrische groepen (peers, geen hiërarchie)
-- - Bidirectionele lookup via JOIN
-- - Supports lifecycle management (active, ai_pending, rejected, deprecated)
-- - Source tracking (db_seed, manual, ai_suggested, imported_yaml)
-- - Scoped synoniemen (global vs per-definitie via definitie_id FK)
-- - Usage analytics & audit trail
--
-- Related: docs/architectuur/synonym-orchestrator-architecture-v3.1.md

-- ========================================
-- SYNONYM GROUPS TABLE
-- ========================================
-- Expliciete groepering van gerelateerde termen
-- Elke groep heeft een canonical_term ("voorkeurs" term voor display)
CREATE TABLE IF NOT EXISTS synonym_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Core Information
    canonical_term TEXT NOT NULL UNIQUE,  -- "Voorkeurs" term voor display
    domain TEXT,                           -- "strafrecht", "civielrecht", etc. (optional)

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT
);

-- ========================================
-- SYNONYM GROUP MEMBERS TABLE
-- ========================================
-- Alle synoniemen als peers (geen hiërarchie!)
-- Bidirectionele lookup via self-join op group_id
CREATE TABLE IF NOT EXISTS synonym_group_members (
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

-- ========================================
-- INDEXES FOR PERFORMANCE
-- ========================================
-- Optimized voor bidirectionele lookups en filtering

-- Group lookup (find all members in a group)
CREATE INDEX IF NOT EXISTS idx_sgm_group
ON synonym_group_members(group_id);

-- Term lookup (find group containing term)
CREATE INDEX IF NOT EXISTS idx_sgm_term
ON synonym_group_members(term);

-- Status filtering (active, ai_pending, etc.)
CREATE INDEX IF NOT EXISTS idx_sgm_status
ON synonym_group_members(status);

-- Preferred filtering (top-5 priority)
CREATE INDEX IF NOT EXISTS idx_sgm_preferred
ON synonym_group_members(is_preferred);

-- Definitie scoping (global vs scoped queries)
CREATE INDEX IF NOT EXISTS idx_sgm_definitie
ON synonym_group_members(definitie_id);

-- Usage analytics (most-used synonyms)
CREATE INDEX IF NOT EXISTS idx_sgm_usage
ON synonym_group_members(usage_count DESC);

-- Composite index for common query pattern (term + status)
CREATE INDEX IF NOT EXISTS idx_sgm_term_status
ON synonym_group_members(term, status);

-- Composite index for group + status queries
CREATE INDEX IF NOT EXISTS idx_sgm_group_status
ON synonym_group_members(group_id, status);

-- ========================================
-- TRIGGERS FOR DATA INTEGRITY
-- ========================================

-- Trigger voor automatische updated_at op synonym_groups
CREATE TRIGGER IF NOT EXISTS update_synonym_groups_timestamp
    AFTER UPDATE ON synonym_groups
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE synonym_groups
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

-- Trigger voor automatische updated_at op synonym_group_members
CREATE TRIGGER IF NOT EXISTS update_synonym_group_members_timestamp
    AFTER UPDATE ON synonym_group_members
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE synonym_group_members
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

-- ========================================
-- VERIFICATION QUERIES (commented out)
-- ========================================
-- Voor handmatige checks na migratie

-- Verify tables exist:
-- SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'synonym_%';

-- Verify indexes:
-- SELECT name FROM sqlite_master WHERE type='index' AND tbl_name IN ('synonym_groups', 'synonym_group_members');

-- Check foreign key integrity:
-- PRAGMA foreign_key_check(synonym_group_members);

-- Example: Bidirectional lookup query
-- Haal alle synoniemen voor term "voorarrest" (inclusief canonical):
-- SELECT
--     m2.term,
--     m2.weight,
--     m2.status,
--     m2.is_preferred
-- FROM synonym_group_members m1
-- JOIN synonym_group_members m2 ON m1.group_id = m2.group_id
-- WHERE m1.term = 'voorarrest'
--   AND m2.term != 'voorarrest'  -- Exclude zelf
--   AND m2.status = 'active'
--   AND (m2.definitie_id IS NULL OR m2.definitie_id = ?)  -- Global + scoped
-- ORDER BY m2.is_preferred DESC, m2.weight DESC, m2.usage_count DESC;
