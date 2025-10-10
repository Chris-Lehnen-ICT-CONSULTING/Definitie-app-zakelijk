"""
Migration script to add synonym_groups and synonym_group_members tables.

This migration implements the schema from PHASE 1.1 (lines 354-444 in schema.sql).
"""

import sqlite3
from pathlib import Path

# Database path
project_root = Path(__file__).parent.parent
db_path = project_root / "data" / "definities.db"


def run_migration():
    """Run migration to add synonym tables."""
    print(f"Connecting to database: {db_path}")

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        # Check if tables already exist
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name IN ('synonym_groups', 'synonym_group_members')
            """
        )
        existing = [row[0] for row in cursor.fetchall()]

        if existing:
            print(f"Tables already exist: {existing}")
            print("Skipping migration.")
            return

        print("Creating synonym_groups table...")
        cursor.execute(
            """
            CREATE TABLE synonym_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                -- Core Information
                canonical_term TEXT NOT NULL UNIQUE,
                domain TEXT,

                -- Metadata
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT
            )
            """
        )

        print("Creating synonym_group_members table...")
        cursor.execute(
            """
            CREATE TABLE synonym_group_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                -- Group Relationship
                group_id INTEGER NOT NULL,
                term TEXT NOT NULL,

                -- Weighting & Priority
                weight REAL DEFAULT 1.0 CHECK(weight >= 0.0 AND weight <= 1.0),
                is_preferred BOOLEAN DEFAULT FALSE,

                -- Lifecycle Status
                status TEXT NOT NULL DEFAULT 'active' CHECK(status IN (
                    'active',
                    'ai_pending',
                    'rejected_auto',
                    'deprecated'
                )),

                -- Source Tracking
                source TEXT NOT NULL CHECK(source IN (
                    'db_seed',
                    'manual',
                    'ai_suggested',
                    'imported_yaml'
                )),

                -- Context & Rationale
                context_json TEXT,

                -- Scoping (global vs per-definitie)
                definitie_id INTEGER,

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
                UNIQUE(group_id, term)
            )
            """
        )

        print("Creating indexes...")
        cursor.execute("CREATE INDEX idx_sgm_group ON synonym_group_members(group_id)")
        cursor.execute("CREATE INDEX idx_sgm_term ON synonym_group_members(term)")
        cursor.execute("CREATE INDEX idx_sgm_status ON synonym_group_members(status)")
        cursor.execute(
            "CREATE INDEX idx_sgm_preferred ON synonym_group_members(is_preferred)"
        )
        cursor.execute(
            "CREATE INDEX idx_sgm_definitie ON synonym_group_members(definitie_id)"
        )
        cursor.execute(
            "CREATE INDEX idx_sgm_usage ON synonym_group_members(usage_count DESC)"
        )
        cursor.execute(
            "CREATE INDEX idx_sgm_term_status ON synonym_group_members(term, status)"
        )
        cursor.execute(
            "CREATE INDEX idx_sgm_group_status ON synonym_group_members(group_id, status)"
        )

        print("Creating triggers...")
        cursor.execute(
            """
            CREATE TRIGGER update_synonym_groups_timestamp
                AFTER UPDATE ON synonym_groups
                FOR EACH ROW
                WHEN NEW.updated_at = OLD.updated_at
            BEGIN
                UPDATE synonym_groups SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            """
        )

        cursor.execute(
            """
            CREATE TRIGGER update_synonym_group_members_timestamp
                AFTER UPDATE ON synonym_group_members
                FOR EACH ROW
                WHEN NEW.updated_at = OLD.updated_at
            BEGIN
                UPDATE synonym_group_members SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            """
        )

        conn.commit()
        print("✓ Migration completed successfully!")

        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"\nAll tables in database: {', '.join(sorted(tables))}")

    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    run_migration()
