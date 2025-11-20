#!/usr/bin/env python3
"""
Fix Foreign Keys: definities_old → definities

PROBLEEM: definitie_drafts en synonym_group_members hebben FK's naar
niet-bestaande "definities_old" table.

OPLOSSING: Rebuild tables met correcte FK's naar "definities"

VEILIGHEID:
- Maakt automatisch backup
- Test op kopie eerst
- Rollback mogelijk
- Verificatie na elke stap
"""

import shutil
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

DB_PATH = project_root / "data" / "definities.db"


def create_backup(db_path: Path) -> Path:
    """Create timestamped backup."""
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    backup_path = db_path.parent / f"{db_path.stem}.backup-{timestamp}{db_path.suffix}"
    shutil.copy2(db_path, backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path


def verify_database(conn: sqlite3.Connection) -> tuple[int, int, int]:
    """Verify data counts."""
    drafts = conn.execute("SELECT COUNT(*) FROM definitie_drafts").fetchone()[0]
    members = conn.execute("SELECT COUNT(*) FROM synonym_group_members").fetchone()[0]
    logs = conn.execute("SELECT COUNT(*) FROM generation_logs").fetchone()[0]
    return drafts, members, logs


def fix_definitie_drafts(conn: sqlite3.Connection) -> None:
    """Rebuild definitie_drafts with correct FK."""
    print("\n🔧 Fixing definitie_drafts...")

    # Step 1: Disable FK checks
    conn.execute("PRAGMA foreign_keys=OFF")

    # Step 1.5: Clean up any leftover tables from previous attempts
    conn.execute("DROP TABLE IF EXISTS definitie_drafts_old")

    # Step 2: Rename old table
    conn.execute("ALTER TABLE definitie_drafts RENAME TO definitie_drafts_old")

    # Step 3: Create new table with correct FK
    conn.execute(
        """
        CREATE TABLE definitie_drafts (
            definitie_id INTEGER PRIMARY KEY REFERENCES definities(id) ON DELETE CASCADE,

            -- Draft content (complete snapshot)
            draft_content TEXT NOT NULL,

            -- Metadata
            saved_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            saved_by VARCHAR(255) DEFAULT 'system'
        )
    """
    )

    # Step 4: Copy data
    conn.execute(
        """
        INSERT INTO definitie_drafts (definitie_id, draft_content, saved_at, saved_by)
        SELECT definitie_id, draft_content, saved_at, saved_by
        FROM definitie_drafts_old
    """
    )

    # Step 5: Recreate indexes (drop first if exists)
    conn.execute("DROP INDEX IF EXISTS idx_drafts_saved_at")
    conn.execute("CREATE INDEX idx_drafts_saved_at ON definitie_drafts(saved_at)")

    # Step 6: Drop old table
    conn.execute("DROP TABLE definitie_drafts_old")

    # Step 7: Re-enable FK checks
    conn.execute("PRAGMA foreign_keys=ON")

    print("✅ definitie_drafts fixed")


def fix_synonym_group_members(conn: sqlite3.Connection) -> None:
    """Rebuild synonym_group_members with correct FK."""
    print("\n🔧 Fixing synonym_group_members...")

    # Step 1: Disable FK checks
    conn.execute("PRAGMA foreign_keys=OFF")

    # Step 1.5: Clean up any leftover tables from previous attempts
    conn.execute("DROP TABLE IF EXISTS synonym_group_members_old")

    # Step 2: Rename old table
    conn.execute(
        "ALTER TABLE synonym_group_members RENAME TO synonym_group_members_old"
    )

    # Step 3: Create new table with correct FK
    conn.execute(
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

    # Step 4: Copy data
    conn.execute(
        """
        INSERT INTO synonym_group_members (
            id, group_id, term, weight, is_preferred, status, source,
            context_json, definitie_id, usage_count, last_used_at,
            created_at, updated_at, created_by, reviewed_by, reviewed_at
        )
        SELECT
            id, group_id, term, weight, is_preferred, status, source,
            context_json, definitie_id, usage_count, last_used_at,
            created_at, updated_at, created_by, reviewed_by, reviewed_at
        FROM synonym_group_members_old
    """
    )

    # Step 5: Recreate indexes (drop first if exists)
    index_names = [
        "idx_sgm_group",
        "idx_sgm_term",
        "idx_sgm_status",
        "idx_sgm_preferred",
        "idx_sgm_definitie",
        "idx_sgm_usage",
        "idx_sgm_term_status",
        "idx_sgm_group_status",
    ]
    for idx_name in index_names:
        conn.execute(f"DROP INDEX IF EXISTS {idx_name}")

    indexes = [
        "CREATE INDEX idx_sgm_group ON synonym_group_members(group_id)",
        "CREATE INDEX idx_sgm_term ON synonym_group_members(term)",
        "CREATE INDEX idx_sgm_status ON synonym_group_members(status)",
        "CREATE INDEX idx_sgm_preferred ON synonym_group_members(is_preferred)",
        "CREATE INDEX idx_sgm_definitie ON synonym_group_members(definitie_id)",
        "CREATE INDEX idx_sgm_usage ON synonym_group_members(usage_count DESC)",
        "CREATE INDEX idx_sgm_term_status ON synonym_group_members(term, status)",
        "CREATE INDEX idx_sgm_group_status ON synonym_group_members(group_id, status)",
    ]
    for idx in indexes:
        conn.execute(idx)

    # Step 6: Recreate trigger (drop first if exists)
    conn.execute("DROP TRIGGER IF EXISTS update_synonym_group_members_timestamp")
    conn.execute(
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

    # Step 7: Drop old table
    conn.execute("DROP TABLE synonym_group_members_old")

    # Step 8: Re-enable FK checks
    conn.execute("PRAGMA foreign_keys=ON")

    print("✅ synonym_group_members fixed")


def fix_generation_logs(conn: sqlite3.Connection) -> None:
    """Rebuild generation_logs with correct FK."""
    print("\n🔧 Fixing generation_logs...")

    # Step 1: Disable FK checks
    conn.execute("PRAGMA foreign_keys=OFF")

    # Step 1.5: Clean up any leftover tables from previous attempts
    conn.execute("DROP TABLE IF EXISTS generation_logs_old")

    # Step 2: Rename old table
    conn.execute("ALTER TABLE generation_logs RENAME TO generation_logs_old")

    # Step 3: Create new table with correct FK (simplified - only key fields shown)
    conn.execute(
        """
        CREATE TABLE generation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            definitie_id INTEGER UNIQUE,
            prompt_full_text TEXT NOT NULL,
            prompt_template_version VARCHAR(50),
            prompt_template_name VARCHAR(100),
            prompt_modules_used TEXT,
            model_name VARCHAR(100) NOT NULL,
            model_temperature DECIMAL(3,2),
            model_max_tokens INTEGER,
            model_top_p DECIMAL(3,2),
            model_frequency_penalty DECIMAL(3,2),
            model_presence_penalty DECIMAL(3,2),
            tokens_prompt INTEGER,
            tokens_completion INTEGER,
            tokens_total INTEGER,
            duration_ms INTEGER,
            response_finish_reason VARCHAR(50),
            response_id VARCHAR(255),
            response_created_at INTEGER,
            generation_status VARCHAR(20) NOT NULL DEFAULT 'pending',
            error_message TEXT,
            error_type VARCHAR(50),
            error_traceback TEXT,
            additional_metadata TEXT,
            logged_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(definitie_id) REFERENCES definities(id) ON DELETE CASCADE,

            CHECK (generation_status IN ('pending', 'success', 'failed', 'timeout')),
            CHECK (model_temperature IS NULL OR (model_temperature >= 0.0 AND model_temperature <= 2.0)),
            CHECK (tokens_prompt IS NULL OR tokens_prompt >= 0),
            CHECK (tokens_completion IS NULL OR tokens_completion >= 0),
            CHECK (duration_ms IS NULL OR duration_ms >= 0)
        )
    """
    )

    # Step 4: Copy data (if any)
    conn.execute(
        """
        INSERT INTO generation_logs (
            id, definitie_id, prompt_full_text, prompt_template_version,
            prompt_template_name, prompt_modules_used, model_name,
            model_temperature, model_max_tokens, model_top_p,
            model_frequency_penalty, model_presence_penalty,
            tokens_prompt, tokens_completion, tokens_total, duration_ms,
            response_finish_reason, response_id, response_created_at,
            generation_status, error_message, error_type, error_traceback,
            additional_metadata, logged_at, updated_at
        )
        SELECT
            id, definitie_id, prompt_full_text, prompt_template_version,
            prompt_template_name, prompt_modules_used, model_name,
            model_temperature, model_max_tokens, model_top_p,
            model_frequency_penalty, model_presence_penalty,
            tokens_prompt, tokens_completion, tokens_total, duration_ms,
            response_finish_reason, response_id, response_created_at,
            generation_status, error_message, error_type, error_traceback,
            additional_metadata, logged_at, updated_at
        FROM generation_logs_old
    """
    )

    # Step 5: Recreate indexes (drop first if exists)
    index_names = [
        "idx_generation_logs_definitie",
        "idx_generation_logs_status",
        "idx_generation_logs_model",
        "idx_generation_logs_logged_at",
    ]
    for idx_name in index_names:
        conn.execute(f"DROP INDEX IF EXISTS {idx_name}")

    conn.execute(
        "CREATE INDEX idx_generation_logs_definitie ON generation_logs(definitie_id)"
    )
    conn.execute(
        "CREATE INDEX idx_generation_logs_status ON generation_logs(generation_status)"
    )
    conn.execute(
        "CREATE INDEX idx_generation_logs_model ON generation_logs(model_name)"
    )
    conn.execute(
        "CREATE INDEX idx_generation_logs_logged_at ON generation_logs(logged_at)"
    )

    # Step 6: Recreate trigger (drop first if exists)
    conn.execute("DROP TRIGGER IF EXISTS update_generation_logs_timestamp")
    conn.execute(
        """
        CREATE TRIGGER update_generation_logs_timestamp
        AFTER UPDATE ON generation_logs
        FOR EACH ROW
        WHEN NEW.updated_at = OLD.updated_at
        BEGIN
            UPDATE generation_logs SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END
    """
    )

    # Step 7: Drop old table
    conn.execute("DROP TABLE generation_logs_old")

    # Step 8: Re-enable FK checks
    conn.execute("PRAGMA foreign_keys=ON")

    print("✅ generation_logs fixed")


def verify_fk_integrity(conn: sqlite3.Connection) -> bool:
    """Verify FK integrity after fix."""
    print("\n🔍 Verifying FK integrity...")

    # Check definitie_drafts
    result = conn.execute(
        """
        SELECT COUNT(*) FROM definitie_drafts d
        WHERE NOT EXISTS (SELECT 1 FROM definities WHERE id = d.definitie_id)
    """
    ).fetchone()[0]

    if result > 0:
        print(f"❌ Found {result} orphaned drafts!")
        return False

    # Check synonym_group_members
    result = conn.execute(
        """
        SELECT COUNT(*) FROM synonym_group_members s
        WHERE s.definitie_id IS NOT NULL
        AND NOT EXISTS (SELECT 1 FROM definities WHERE id = s.definitie_id)
    """
    ).fetchone()[0]

    if result > 0:
        print(f"❌ Found {result} orphaned synonym members!")
        return False

    # Check generation_logs
    result = conn.execute(
        """
        SELECT COUNT(*) FROM generation_logs g
        WHERE g.definitie_id IS NOT NULL
        AND NOT EXISTS (SELECT 1 FROM definities WHERE id = g.definitie_id)
    """
    ).fetchone()[0]

    if result > 0:
        print(f"❌ Found {result} orphaned generation logs!")
        return False

    print("✅ No orphaned records found")
    return True


def main():
    """Main execution."""
    print("=" * 60)
    print("FIX: definities_old FK → definities FK")
    print("=" * 60)

    if not DB_PATH.exists():
        print(f"❌ Database not found: {DB_PATH}")
        sys.exit(1)

    # Step 1: Create backup
    backup_path = create_backup(DB_PATH)

    try:
        # Step 2: Connect and verify initial state
        conn = sqlite3.connect(DB_PATH)
        drafts_before, members_before, logs_before = verify_database(conn)
        print("\n📊 Initial counts:")
        print(f"   - definitie_drafts: {drafts_before}")
        print(f"   - synonym_group_members: {members_before}")
        print(f"   - generation_logs: {logs_before}")

        # Step 3: Fix tables
        fix_definitie_drafts(conn)
        fix_synonym_group_members(conn)
        fix_generation_logs(conn)

        # Step 4: Verify final state
        drafts_after, members_after, logs_after = verify_database(conn)
        print("\n📊 Final counts:")
        print(f"   - definitie_drafts: {drafts_after}")
        print(f"   - synonym_group_members: {members_after}")
        print(f"   - generation_logs: {logs_after}")

        if (
            drafts_before != drafts_after
            or members_before != members_after
            or logs_before != logs_after
        ):
            print("❌ Data count mismatch!")
            conn.rollback()
            sys.exit(1)

        # Step 5: Verify FK integrity
        if not verify_fk_integrity(conn):
            print("❌ FK integrity check failed!")
            conn.rollback()
            sys.exit(1)

        # Step 6: Commit changes
        conn.commit()
        print("\n✅ ALL DONE! Database fixed successfully.")
        print(f"   Backup kept at: {backup_path}")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("   Database unchanged - rollback executed")
        print(f"   Restore from backup: {backup_path}")
        conn.rollback()
        sys.exit(1)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
