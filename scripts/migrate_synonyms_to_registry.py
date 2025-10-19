#!/usr/bin/env python3
"""
Synonym Migration Script - PHASE 1.4

Migrate all synonym data from 3 sources to unified graph-based registry:
1. juridische_synoniemen.yaml (if exists - legacy)
2. synonym_suggestions table (approved only)
3. definitie_voorbeelden table (per-definitie manual)

Architecture Specification:
    docs/architectuur/synonym-orchestrator-architecture-v3.1.md
    Lines 814-913: Migration strategy and data sources

Usage:
    # Preview migration (safe, no writes)
    python scripts/migrate_synonyms_to_registry.py --dry-run

    # Execute migration
    python scripts/migrate_synonyms_to_registry.py --execute

    # Rollback migration
    python scripts/migrate_synonyms_to_registry.py --rollback

    # With custom paths
    python scripts/migrate_synonyms_to_registry.py --execute --db-path data/test.db
"""

import argparse
import json
import logging
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Install with: pip install pyyaml")
    sys.exit(1)

from repositories.synonym_registry import SynonymRegistry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(project_root / "logs" / "synonym_migration.log"),
    ],
)
logger = logging.getLogger(__name__)


class MigrationStatistics:
    """Track migration statistics and conflicts."""

    def __init__(self):
        self.groups_created: int = 0
        self.members_added: int = 0
        self.yaml_imported: int = 0
        self.db_approved: int = 0
        self.definitie_voorbeelden: int = 0
        self.conflicts: list[str] = []
        self.errors: list[str] = []
        self.skipped: int = 0
        self.start_time: float = time.time()

        # Track by source
        self.by_source: dict[str, int] = defaultdict(int)

        # Track groups and members for deduplication
        self.processed_groups: dict[str, int] = {}  # canonical_term -> group_id
        self.processed_members: set[tuple[int, str]] = set()  # (group_id, term)

    def add_conflict(self, message: str):
        """Add conflict detection message."""
        self.conflicts.append(message)
        logger.warning(f"CONFLICT: {message}")

    def add_error(self, message: str):
        """Add error message."""
        self.errors.append(message)
        logger.error(f"ERROR: {message}")

    def duration(self) -> float:
        """Get duration in seconds."""
        return time.time() - self.start_time

    def summary(self) -> dict[str, Any]:
        """Get summary statistics."""
        return {
            "groups_created": self.groups_created,
            "members_added": self.members_added,
            "yaml_imported": self.yaml_imported,
            "db_approved": self.db_approved,
            "definitie_voorbeelden": self.definitie_voorbeelden,
            "by_source": dict(self.by_source),
            "conflicts": len(self.conflicts),
            "errors": len(self.errors),
            "skipped": self.skipped,
            "duration_seconds": round(self.duration(), 2),
        }


class SynonymMigration:
    """
    Migrate all synonym sources to graph-based registry.

    Architecture Reference:
        Lines 814-913: SynonymMigration class specification
    """

    def __init__(
        self,
        db_path: str,
        yaml_path: str | None = None,
        verbose: bool = False,
    ):
        """
        Initialize migration.

        Args:
            db_path: Path to SQLite database
            yaml_path: Path to YAML file (optional)
            verbose: Enable verbose logging
        """
        self.db_path = Path(db_path)
        self.yaml_path = Path(yaml_path) if yaml_path else None
        self.verbose = verbose

        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        # Verify database exists
        if not self.db_path.exists():
            msg = f"Database not found: {self.db_path}"
            raise FileNotFoundError(msg)

        self.registry = SynonymRegistry(str(self.db_path))
        self.stats = MigrationStatistics()

        logger.info(f"Initialized migration with database: {self.db_path}")

    def migrate_all(self, dry_run: bool = True) -> dict[str, Any]:
        """
        Migrate all three data sources.

        Args:
            dry_run: If True, simulate migration without writes

        Returns:
            Dictionary with migration statistics

        Architecture Reference:
            Lines 817-826: migrate_all() method specification
        """
        mode = "DRY-RUN" if dry_run else "EXECUTE"
        logger.info(f"Starting migration in {mode} mode")
        logger.info("=" * 80)

        try:
            # Source 1: YAML file (if exists)
            self._migrate_yaml_file(dry_run)

            # Source 2: synonym_suggestions table (approved only)
            self._migrate_synonym_suggestions(dry_run)

            # Source 3: definitie_voorbeelden table (per-definitie manual)
            self._migrate_definitie_voorbeelden(dry_run)

            # Validation (only if executed)
            if not dry_run:
                validation = self._validate_migration()
                logger.info("=" * 80)
                logger.info("VALIDATION RESULTS:")
                for key, value in validation.items():
                    logger.info(f"  {key}: {value}")

            # Print summary
            self._print_summary(dry_run)

            return self.stats.summary()

        except Exception as e:
            logger.error(f"Migration failed: {e}", exc_info=True)
            self.stats.add_error(f"Migration failed: {e}")
            raise

    def _migrate_yaml_file(self, dry_run: bool):
        """
        Migrate Source 1: juridische_synoniemen.yaml (legacy).

        Structure:
            hoofdterm:
              - synoniem: term
                weight: 0.95

        Args:
            dry_run: If True, only count without writing
        """
        logger.info("")
        logger.info("SOURCE 1: juridische_synoniemen.yaml (Legacy)")
        logger.info("-" * 80)

        # Check if YAML file exists
        if not self.yaml_path or not self.yaml_path.exists():
            logger.info(f"YAML file not found: {self.yaml_path or 'not specified'}")
            logger.info("Skipping Source 1")
            return

        # Load YAML
        try:
            with open(self.yaml_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception as e:
            self.stats.add_error(f"Failed to load YAML file: {e}")
            return

        if not data:
            logger.info("YAML file is empty")
            return

        logger.info(f"Loaded {len(data)} hoofdtermen from YAML")

        # Process each hoofdterm
        processed = 0
        for hoofdterm, synoniemen in data.items():
            if not synoniemen:
                continue

            # Normalize hoofdterm (underscores to spaces)
            canonical_term = hoofdterm.replace("_", " ")

            try:
                # Get or create group
                if dry_run:
                    # Simulate: check if already processed
                    if canonical_term not in self.stats.processed_groups:
                        self.stats.processed_groups[canonical_term] = len(
                            self.stats.processed_groups
                        )
                        self.stats.groups_created += 1
                    group_id = self.stats.processed_groups[canonical_term]
                else:
                    # Execute: actually create group
                    group = self.registry.get_or_create_group(
                        canonical_term=canonical_term,
                        domain=None,
                        created_by="migration_yaml",
                    )
                    group_id = group.id
                    if canonical_term not in self.stats.processed_groups:
                        self.stats.processed_groups[canonical_term] = group_id
                        self.stats.groups_created += 1

                # Add each synoniem as member
                for item in synoniemen:
                    if not isinstance(item, dict):
                        continue

                    synoniem = item.get("synoniem", "").strip()
                    weight = float(item.get("weight", 1.0))

                    if not synoniem:
                        continue

                    # Check for duplicates
                    member_key = (group_id, synoniem)
                    if member_key in self.stats.processed_members:
                        self.stats.add_conflict(
                            f"Duplicate member in YAML: '{synoniem}' "
                            f"in group '{canonical_term}'"
                        )
                        self.stats.skipped += 1
                        continue

                    if dry_run:
                        # Simulate
                        self.stats.processed_members.add(member_key)
                        self.stats.members_added += 1
                        self.stats.yaml_imported += 1
                        self.stats.by_source["imported_yaml"] += 1
                    else:
                        # Execute
                        try:
                            self.registry.add_group_member(
                                group_id=group_id,
                                term=synoniem,
                                weight=weight,
                                status="active",
                                source="imported_yaml",
                                definitie_id=None,  # Global
                                context_json=json.dumps({"origin": "yaml_migration"}),
                                created_by="migration_yaml",
                            )
                            self.stats.processed_members.add(member_key)
                            self.stats.members_added += 1
                            self.stats.yaml_imported += 1
                            self.stats.by_source["imported_yaml"] += 1
                        except ValueError as e:
                            self.stats.add_error(
                                f"Failed to add member '{synoniem}' to "
                                f"group '{canonical_term}': {e}"
                            )
                            self.stats.skipped += 1

                processed += 1
                if processed % 10 == 0:
                    logger.info(f"Processed {processed}/{len(data)} hoofdtermen...")

            except Exception as e:
                self.stats.add_error(f"Failed to process '{hoofdterm}': {e}")
                continue

        logger.info(f"Completed Source 1: {self.stats.yaml_imported} members from YAML")

    def _migrate_synonym_suggestions(self, dry_run: bool):
        """
        Migrate Source 2: synonym_suggestions table (approved only).

        Fields: hoofdterm, synoniem, confidence, status, context_data, reviewed_by

        Args:
            dry_run: If True, only count without writing
        """
        logger.info("")
        logger.info("SOURCE 2: synonym_suggestions table (DB - approved only)")
        logger.info("-" * 80)

        # Check if table exists
        with self.registry._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='synonym_suggestions'
                """
            )
            if not cursor.fetchone():
                logger.info("synonym_suggestions table not found")
                logger.info("Skipping Source 2")
                return

            # Count approved suggestions
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM synonym_suggestions WHERE status = 'approved'"
            )
            total = cursor.fetchone()["count"]
            logger.info(f"Found {total} approved suggestions")

            if total == 0:
                logger.info("No approved suggestions to migrate")
                return

            # Fetch all approved suggestions
            cursor = conn.execute(
                """
                SELECT
                    hoofdterm, synoniem, confidence, context_data,
                    reviewed_by, reviewed_at, created_at
                FROM synonym_suggestions
                WHERE status = 'approved'
                ORDER BY hoofdterm, confidence DESC
                """
            )
            suggestions = cursor.fetchall()

        logger.info(f"Processing {len(suggestions)} approved suggestions...")

        processed = 0
        for row in suggestions:
            hoofdterm = row["hoofdterm"].strip()
            synoniem = row["synoniem"].strip()
            confidence = float(row["confidence"])
            context_data = row["context_data"]
            reviewed_by = row["reviewed_by"]
            reviewed_at = row["reviewed_at"]

            try:
                # Get or create group
                if dry_run:
                    if hoofdterm not in self.stats.processed_groups:
                        self.stats.processed_groups[hoofdterm] = len(
                            self.stats.processed_groups
                        )
                        self.stats.groups_created += 1
                    group_id = self.stats.processed_groups[hoofdterm]
                else:
                    group = self.registry.get_or_create_group(
                        canonical_term=hoofdterm,
                        domain=None,
                        created_by="migration_suggestions",
                    )
                    group_id = group.id
                    if hoofdterm not in self.stats.processed_groups:
                        self.stats.processed_groups[hoofdterm] = group_id
                        self.stats.groups_created += 1

                # Check for duplicates
                member_key = (group_id, synoniem)
                if member_key in self.stats.processed_members:
                    self.stats.add_conflict(
                        f"Duplicate member in suggestions: '{synoniem}' "
                        f"in group '{hoofdterm}'"
                    )
                    self.stats.skipped += 1
                    continue

                # Prepare context JSON
                if context_data:
                    try:
                        context = json.loads(context_data)
                        context["reviewed_by"] = reviewed_by
                        context["reviewed_at"] = reviewed_at
                        context["origin"] = "synonym_suggestions"
                        context_json = json.dumps(context)
                    except json.JSONDecodeError:
                        context_json = json.dumps(
                            {
                                "reviewed_by": reviewed_by,
                                "reviewed_at": reviewed_at,
                                "origin": "synonym_suggestions",
                            }
                        )
                else:
                    context_json = json.dumps(
                        {
                            "reviewed_by": reviewed_by,
                            "reviewed_at": reviewed_at,
                            "origin": "synonym_suggestions",
                        }
                    )

                if dry_run:
                    self.stats.processed_members.add(member_key)
                    self.stats.members_added += 1
                    self.stats.db_approved += 1
                    self.stats.by_source["ai_suggested"] += 1
                else:
                    try:
                        self.registry.add_group_member(
                            group_id=group_id,
                            term=synoniem,
                            weight=confidence,  # Use confidence as weight
                            status="active",  # Already approved
                            source="ai_suggested",
                            definitie_id=None,  # Global
                            context_json=context_json,
                            created_by="migration_suggestions",
                        )
                        self.stats.processed_members.add(member_key)
                        self.stats.members_added += 1
                        self.stats.db_approved += 1
                        self.stats.by_source["ai_suggested"] += 1
                    except ValueError as e:
                        self.stats.add_error(
                            f"Failed to add member '{synoniem}' to "
                            f"group '{hoofdterm}': {e}"
                        )
                        self.stats.skipped += 1

                processed += 1
                if processed % 10 == 0:
                    percentage = (processed / total) * 100
                    logger.info(f"Processed {processed}/{total} ({percentage:.1f}%)...")

            except Exception as e:
                self.stats.add_error(
                    f"Failed to process suggestion '{hoofdterm}' -> '{synoniem}': {e}"
                )
                continue

        logger.info(
            f"Completed Source 2: {self.stats.db_approved} members from suggestions"
        )

    def _migrate_definitie_voorbeelden(self, dry_run: bool):
        """
        Migrate Source 3: definitie_voorbeelden table (per-definitie manual).

        Fields: definitie_id, voorbeeld_type='synonyms', voorbeeld_tekst

        Note: These are SCOPED to definitie_id (not global)

        Args:
            dry_run: If True, only count without writing
        """
        logger.info("")
        logger.info("SOURCE 3: definitie_voorbeelden table (per-definitie manual)")
        logger.info("-" * 80)

        with self.registry._get_connection() as conn:
            # Check if table exists
            cursor = conn.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='definitie_voorbeelden'
                """
            )
            if not cursor.fetchone():
                logger.info("definitie_voorbeelden table not found")
                logger.info("Skipping Source 3")
                return

            # Fetch all definitions with synonym examples
            cursor = conn.execute(
                """
                SELECT
                    dv.definitie_id,
                    dv.voorbeeld_tekst,
                    d.begrip
                FROM definitie_voorbeelden dv
                JOIN definities d ON d.id = dv.definitie_id
                WHERE dv.voorbeeld_type = 'synonyms' AND dv.actief = TRUE
                ORDER BY dv.definitie_id
                """
            )
            voorbeelden = cursor.fetchall()

        if not voorbeelden:
            logger.info("No synonym examples found in definitie_voorbeelden")
            return

        logger.info(f"Found {len(voorbeelden)} synonym example entries")

        processed = 0
        for row in voorbeelden:
            definitie_id = row["definitie_id"]
            begrip = row["begrip"].strip()
            voorbeeld_tekst = row["voorbeeld_tekst"].strip()

            # Parse voorbeelden (may be multiple per entry)
            # Could be JSON array or comma-separated
            synoniemen = self._parse_voorbeelden(voorbeeld_tekst)

            if not synoniemen:
                continue

            try:
                # Get or create group for this begrip
                if dry_run:
                    if begrip not in self.stats.processed_groups:
                        self.stats.processed_groups[begrip] = len(
                            self.stats.processed_groups
                        )
                        self.stats.groups_created += 1
                    group_id = self.stats.processed_groups[begrip]
                else:
                    group = self.registry.get_or_create_group(
                        canonical_term=begrip,
                        domain=None,
                        created_by="migration_voorbeelden",
                    )
                    group_id = group.id
                    if begrip not in self.stats.processed_groups:
                        self.stats.processed_groups[begrip] = group_id
                        self.stats.groups_created += 1

                # Add each synoniem (SCOPED to definitie_id!)
                for synoniem in synoniemen:
                    synoniem = synoniem.strip()
                    if not synoniem:
                        continue

                    # Check for duplicates (including definitie_id in key)
                    member_key = (group_id, synoniem)
                    if member_key in self.stats.processed_members:
                        self.stats.add_conflict(
                            f"Duplicate member in voorbeelden: '{synoniem}' "
                            f"in group '{begrip}' (definitie {definitie_id})"
                        )
                        self.stats.skipped += 1
                        continue

                    context_json = json.dumps(
                        {
                            "origin": "definitie_voorbeelden",
                            "definitie_id": definitie_id,
                            "scoped": True,
                        }
                    )

                    if dry_run:
                        self.stats.processed_members.add(member_key)
                        self.stats.members_added += 1
                        self.stats.definitie_voorbeelden += 1
                        self.stats.by_source["manual"] += 1
                    else:
                        try:
                            self.registry.add_group_member(
                                group_id=group_id,
                                term=synoniem,
                                weight=1.0,  # Default weight for manual
                                status="active",
                                source="manual",
                                definitie_id=definitie_id,  # SCOPED!
                                context_json=context_json,
                                created_by="migration_voorbeelden",
                            )
                            self.stats.processed_members.add(member_key)
                            self.stats.members_added += 1
                            self.stats.definitie_voorbeelden += 1
                            self.stats.by_source["manual"] += 1
                        except ValueError as e:
                            self.stats.add_error(
                                f"Failed to add member '{synoniem}' to "
                                f"group '{begrip}': {e}"
                            )
                            self.stats.skipped += 1

                processed += 1
                if processed % 10 == 0:
                    logger.info(f"Processed {processed}/{len(voorbeelden)} entries...")

            except Exception as e:
                self.stats.add_error(
                    f"Failed to process voorbeelden for definitie {definitie_id}: {e}"
                )
                continue

        logger.info(
            f"Completed Source 3: {self.stats.definitie_voorbeelden} members "
            "from voorbeelden"
        )

    def _parse_voorbeelden(self, text: str) -> list[str]:
        """
        Parse voorbeelden text (may be JSON array or comma-separated).

        Args:
            text: Raw text from database

        Returns:
            List of synonym terms
        """
        # Try JSON first
        try:
            data = json.loads(text)
            if isinstance(data, list):
                return [str(item).strip() for item in data]
        except json.JSONDecodeError:
            pass

        # Fall back to comma-separated or newline-separated
        if "," in text:
            return [s.strip() for s in text.split(",") if s.strip()]
        if "\n" in text:
            return [s.strip() for s in text.split("\n") if s.strip()]
        # Single term
        return [text.strip()] if text.strip() else []

    def _validate_migration(self) -> dict[str, Any]:
        """
        Validate migration results (only after execution).

        Returns:
            Dictionary with validation statistics
        """
        stats = self.registry.get_statistics()

        # Check for orphaned members (should be 0)
        with self.registry._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT COUNT(*) as count
                FROM synonym_group_members m
                WHERE NOT EXISTS (
                    SELECT 1 FROM synonym_groups g WHERE g.id = m.group_id
                )
                """
            )
            orphaned_members = cursor.fetchone()["count"]

            # Check for groups without members
            cursor = conn.execute(
                """
                SELECT COUNT(*) as count
                FROM synonym_groups g
                WHERE NOT EXISTS (
                    SELECT 1 FROM synonym_group_members m WHERE m.group_id = g.id
                )
                """
            )
            empty_groups = cursor.fetchone()["count"]

        validation = {
            "total_groups": stats["total_groups"],
            "total_members": stats["total_members"],
            "members_by_source": stats.get("members_by_source", {}),
            "members_by_status": stats.get("members_by_status", {}),
            "orphaned_members": orphaned_members,
            "groups_without_members": empty_groups,
            "avg_group_size": stats.get("avg_group_size", 0.0),
        }

        # Warnings
        if orphaned_members > 0:
            logger.warning(f"Found {orphaned_members} orphaned members!")
        if empty_groups > 0:
            logger.warning(f"Found {empty_groups} empty groups!")

        return validation

    def _print_summary(self, dry_run: bool):
        """Print migration summary."""
        mode = "DRY-RUN" if dry_run else "EXECUTION"
        logger.info("")
        logger.info("=" * 80)
        logger.info(f"MIGRATION {mode} SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Duration: {self.stats.duration():.2f} seconds")
        logger.info("")
        logger.info("GROUPS & MEMBERS:")
        logger.info(f"  Groups created: {self.stats.groups_created}")
        logger.info(f"  Members added: {self.stats.members_added}")
        logger.info("")
        logger.info("BY SOURCE:")
        logger.info(f"  YAML imported: {self.stats.yaml_imported}")
        logger.info(f"  DB approved suggestions: {self.stats.db_approved}")
        logger.info(f"  Definitie voorbeelden: {self.stats.definitie_voorbeelden}")
        logger.info("")
        logger.info("SOURCE BREAKDOWN:")
        for source, count in self.stats.by_source.items():
            logger.info(f"  {source}: {count}")
        logger.info("")
        logger.info("ISSUES:")
        logger.info(f"  Conflicts detected: {len(self.stats.conflicts)}")
        logger.info(f"  Errors encountered: {len(self.stats.errors)}")
        logger.info(f"  Items skipped: {self.stats.skipped}")

        if self.stats.conflicts:
            logger.info("")
            logger.info("CONFLICT DETAILS:")
            for conflict in self.stats.conflicts[:10]:  # Show first 10
                logger.info(f"  - {conflict}")
            if len(self.stats.conflicts) > 10:
                logger.info(f"  ... and {len(self.stats.conflicts) - 10} more")

        if self.stats.errors:
            logger.info("")
            logger.info("ERROR DETAILS:")
            for error in self.stats.errors[:10]:  # Show first 10
                logger.info(f"  - {error}")
            if len(self.stats.errors) > 10:
                logger.info(f"  ... and {len(self.stats.errors) - 10} more")

        logger.info("=" * 80)

    def rollback(self) -> dict[str, Any]:
        """
        Rollback migration by deleting all migrated data.

        This is safe: only deletes groups created by migration.

        Returns:
            Dictionary with rollback statistics
        """
        logger.info("=" * 80)
        logger.info("ROLLBACK: Deleting migrated data")
        logger.info("=" * 80)

        with self.registry._get_connection() as conn:
            # Count what will be deleted
            cursor = conn.execute(
                """
                SELECT COUNT(*) as count FROM synonym_groups
                WHERE created_by LIKE 'migration_%'
                """
            )
            groups_to_delete = cursor.fetchone()["count"]

            cursor = conn.execute(
                """
                SELECT COUNT(*) as count FROM synonym_group_members m
                JOIN synonym_groups g ON g.id = m.group_id
                WHERE g.created_by LIKE 'migration_%'
                """
            )
            members_to_delete = cursor.fetchone()["count"]

            logger.info(f"Will delete {groups_to_delete} groups")
            logger.info(f"Will delete {members_to_delete} members")

            # Execute deletion (CASCADE will delete members)
            cursor = conn.execute(
                """
                DELETE FROM synonym_groups
                WHERE created_by LIKE 'migration_%'
                """
            )
            groups_deleted = cursor.rowcount

            logger.info(f"Deleted {groups_deleted} groups (and their members)")

        rollback_stats = {
            "groups_deleted": groups_deleted,
            "members_deleted": members_to_delete,
        }

        logger.info("=" * 80)
        logger.info("ROLLBACK COMPLETE")
        logger.info("=" * 80)

        return rollback_stats


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate synonym data from 3 sources to unified registry",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview migration (safe, no writes)
  python scripts/migrate_synonyms_to_registry.py --dry-run

  # Execute migration
  python scripts/migrate_synonyms_to_registry.py --execute

  # Rollback migration
  python scripts/migrate_synonyms_to_registry.py --rollback

  # With custom paths
  python scripts/migrate_synonyms_to_registry.py --execute \\
      --db-path data/test.db \\
      --yaml-path config/my_synonyms.yaml
        """,
    )

    # Mode selection (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview migration (no database writes)",
    )
    mode_group.add_argument(
        "--execute",
        action="store_true",
        help="Execute migration (writes to database)",
    )
    mode_group.add_argument(
        "--rollback",
        action="store_true",
        help="Rollback migration (delete migrated data)",
    )

    # Path configuration
    parser.add_argument(
        "--db-path",
        default="data/definities.db",
        help="Path to SQLite database (default: data/definities.db)",
    )
    parser.add_argument(
        "--yaml-path",
        default="config/juridische_synoniemen.yaml",
        help="Path to YAML file (default: config/juridische_synoniemen.yaml)",
    )

    # Options
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging (DEBUG level)",
    )

    args = parser.parse_args()

    # Resolve paths relative to project root
    db_path = project_root / args.db_path
    yaml_path = project_root / args.yaml_path if args.yaml_path else None

    # Initialize migration
    try:
        migration = SynonymMigration(
            db_path=str(db_path),
            yaml_path=str(yaml_path) if yaml_path else None,
            verbose=args.verbose,
        )
    except FileNotFoundError as e:
        logger.error(f"ERROR: {e}")
        sys.exit(1)

    # Execute based on mode
    try:
        if args.rollback:
            # Rollback mode
            rollback_stats = migration.rollback()
            print("\nRollback completed successfully!")
            print(f"Deleted {rollback_stats['groups_deleted']} groups")
            print(f"Deleted {rollback_stats['members_deleted']} members")
            sys.exit(0)
        else:
            # Dry-run or execute mode
            results = migration.migrate_all(dry_run=args.dry_run)

            if args.dry_run:
                print("\n" + "=" * 80)
                print("DRY-RUN COMPLETED - No data was written to database")
                print("=" * 80)
                print("\nTo execute migration, run with --execute flag:")
                print("  python scripts/migrate_synonyms_to_registry.py --execute")
            else:
                print("\n" + "=" * 80)
                print("MIGRATION COMPLETED SUCCESSFULLY")
                print("=" * 80)

            # Exit with error code if there were errors
            if results["errors"] > 0:
                print(f"\nWARNING: Migration completed with {results['errors']} errors")
                sys.exit(1)
            else:
                sys.exit(0)

    except Exception as e:
        logger.error(f"FATAL ERROR: {e}", exc_info=True)
        print("\n" + "=" * 80)
        print("MIGRATION FAILED")
        print("=" * 80)
        print(f"Error: {e}")
        print("\nCheck logs/synonym_migration.log for details")
        sys.exit(1)


if __name__ == "__main__":
    main()
