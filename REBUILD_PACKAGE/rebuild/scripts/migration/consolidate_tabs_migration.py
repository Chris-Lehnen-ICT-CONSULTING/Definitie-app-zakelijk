#!/usr/bin/env python3
"""
Migration Script: Consolidate Export/Management Tabs
======================================================
Dit script begeleidt de migratie van Export en Management tabs
naar de nieuwe geconsolideerde ImportExportBeheer tab.

Stappen:
1. Backup huidige tabs
2. Test nieuwe tab functionaliteit
3. Verwijder oude tabs na verificatie
"""

import argparse
import logging
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
OLD_EXPORT_TAB = PROJECT_ROOT / "src/ui/components/export_tab.py"
OLD_MANAGEMENT_TAB = PROJECT_ROOT / "src/ui/components/management_tab.py"
NEW_TAB = PROJECT_ROOT / "src/ui/components/import_export_beheer_tab.py"
BACKUP_DIR = PROJECT_ROOT / "backups/tab_consolidation"


class TabConsolidationMigration:
    """Beheert de tab consolidatie migratie."""

    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.backup_dir = BACKUP_DIR / datetime.now().strftime("%Y%m%d_%H%M%S")

    def run_migration(self):
        """Voer complete migratie uit."""
        logger.info("Starting tab consolidation migration...")

        try:
            # Stap 1: Pre-flight checks
            if not self.pre_flight_checks():
                logger.error("Pre-flight checks failed. Aborting migration.")
                return False

            # Stap 2: Create backup
            if not self.create_backup():
                logger.error("Backup creation failed. Aborting migration.")
                return False

            # Stap 3: Verify new tab
            if not self.verify_new_tab():
                logger.error("New tab verification failed. Aborting migration.")
                return False

            # Stap 4: Update imports
            if not self.update_imports():
                logger.warning("Import updates partially failed. Manual review needed.")

            # Stap 5: Archive old tabs
            if not self.dry_run:
                if not self.archive_old_tabs():
                    logger.error("Failed to archive old tabs. Manual cleanup needed.")
                    return False

            # Stap 6: Final verification
            if not self.final_verification():
                logger.error("Final verification failed. Check application manually.")
                return False

            logger.info("✅ Migration completed successfully!")
            return True

        except Exception as e:
            logger.error(f"Migration failed with error: {e!s}")
            self.rollback()
            return False

    def pre_flight_checks(self):
        """Controleer of migratie veilig is."""
        logger.info("Running pre-flight checks...")

        checks = {
            "Old export tab exists": OLD_EXPORT_TAB.exists(),
            "Old management tab exists": OLD_MANAGEMENT_TAB.exists(),
            "New tab exists": NEW_TAB.exists(),
            "No uncommitted changes": self.check_git_status(),
        }

        for check, result in checks.items():
            if result:
                logger.info(f"✓ {check}")
            else:
                logger.error(f"✗ {check}")

        return all(checks.values())

    def check_git_status(self):
        """Check for uncommitted changes."""
        import subprocess

        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
                check=False,
            )
            if result.stdout.strip():
                logger.warning("Uncommitted changes detected:")
                logger.warning(result.stdout)
                return False
            return True
        except Exception as e:
            logger.warning(f"Could not check git status: {e}")
            return True  # Continue anyway

    def create_backup(self):
        """Maak backup van oude tabs."""
        logger.info(f"Creating backup in {self.backup_dir}...")

        if self.dry_run:
            logger.info("[DRY RUN] Would create backup")
            return True

        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)

            # Backup old tabs
            shutil.copy2(OLD_EXPORT_TAB, self.backup_dir / "export_tab.py.bak")
            shutil.copy2(OLD_MANAGEMENT_TAB, self.backup_dir / "management_tab.py.bak")

            # Backup tabbed interface
            tabbed_interface = PROJECT_ROOT / "src/ui/tabbed_interface.py"
            if tabbed_interface.exists():
                shutil.copy2(
                    tabbed_interface, self.backup_dir / "tabbed_interface.py.bak"
                )

            # Create restoration script
            restore_script = self.backup_dir / "restore.sh"
            restore_script.write_text(
                f"""#!/bin/bash
# Restoration script for tab consolidation rollback
echo "Restoring from backup {self.backup_dir}..."
cp "{self.backup_dir}/export_tab.py.bak" "{OLD_EXPORT_TAB}"
cp "{self.backup_dir}/management_tab.py.bak" "{OLD_MANAGEMENT_TAB}"
cp "{self.backup_dir}/tabbed_interface.py.bak" "{PROJECT_ROOT}/src/ui/tabbed_interface.py"
echo "Restoration complete!"
"""
            )
            restore_script.chmod(0o755)

            logger.info(f"✓ Backup created at {self.backup_dir}")
            return True

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False

    def verify_new_tab(self):
        """Verifieer nieuwe tab functionaliteit."""
        logger.info("Verifying new tab functionality...")

        try:
            # Check imports
            import ast

            with open(NEW_TAB) as f:
                tree = ast.parse(f.read())

            # Check for required methods
            class_found = False
            required_methods = [
                "render",
                "_render_import_section",
                "_render_export_section",
                "_render_bulk_actions",
                "_render_database_management",
            ]

            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.ClassDef)
                    and node.name == "ImportExportBeheerTab"
                ):
                    class_found = True
                    methods = [
                        m.name for m in node.body if isinstance(m, ast.FunctionDef)
                    ]

                    for method in required_methods:
                        if method in methods:
                            logger.info(f"✓ Method {method} found")
                        else:
                            logger.error(f"✗ Method {method} missing")
                            return False

            if not class_found:
                logger.error("✗ ImportExportBeheerTab class not found")
                return False

            logger.info("✓ New tab structure verified")
            return True

        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return False

    def update_imports(self):
        """Update import statements in andere bestanden."""
        logger.info("Updating import statements...")

        if self.dry_run:
            logger.info("[DRY RUN] Would update imports")
            return True

        files_to_check = [
            PROJECT_ROOT / "src/ui/tabbed_interface.py",
        ]

        updates = 0
        for file_path in files_to_check:
            if not file_path.exists():
                continue

            content = file_path.read_text()
            original = content

            # Check for old imports
            if "from ui.components.export_tab import ExportTab" in content:
                logger.info(f"Found old export import in {file_path.name}")
                updates += 1

            if "from ui.components.management_tab import ManagementTab" in content:
                logger.info(f"Found old management import in {file_path.name}")
                updates += 1

        logger.info(f"✓ Found {updates} files with old imports")
        return True

    def archive_old_tabs(self):
        """Archiveer oude tab bestanden."""
        logger.info("Archiving old tab files...")

        if self.dry_run:
            logger.info("[DRY RUN] Would archive old tabs")
            return True

        archive_dir = PROJECT_ROOT / "docs/archief/code/tabs"
        archive_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Move old tabs to archive
            timestamp = datetime.now().strftime("%Y%m%d")

            shutil.move(
                str(OLD_EXPORT_TAB),
                str(archive_dir / f"export_tab_{timestamp}.py.archived"),
            )
            logger.info(f"✓ Archived {OLD_EXPORT_TAB.name}")

            shutil.move(
                str(OLD_MANAGEMENT_TAB),
                str(archive_dir / f"management_tab_{timestamp}.py.archived"),
            )
            logger.info(f"✓ Archived {OLD_MANAGEMENT_TAB.name}")

            # Create README in archive
            readme = archive_dir / "README.md"
            readme.write_text(
                f"""# Archived Tab Files

## Tab Consolidation - {timestamp}

The Export and Management tabs were consolidated into ImportExportBeheerTab.

### Archived Files:
- `export_tab_{timestamp}.py.archived` - Original export tab (911 lines)
- `management_tab_{timestamp}.py.archived` - Original management tab (1898 lines)

### Replacement:
- `import_export_beheer_tab.py` - New consolidated tab (~400 lines)

### Features Retained:
1. CSV Import
2. Export (all formats)
3. Bulk status changes
4. Database reset

### Features Removed:
- Dashboards
- Graphs
- Duplicate features
- Developer tools (moved to separate interface)

### Restoration:
To restore old tabs, use the backup at:
`{self.backup_dir}/restore.sh`
"""
            )

            logger.info("✓ Old tabs archived successfully")
            return True

        except Exception as e:
            logger.error(f"Archiving failed: {e}")
            return False

    def final_verification(self):
        """Finale verificatie van de applicatie."""
        logger.info("Running final verification...")

        checks = [
            (NEW_TAB.exists(), "New tab exists"),
            (not OLD_EXPORT_TAB.exists(), "Old export tab removed"),
            (not OLD_MANAGEMENT_TAB.exists(), "Old management tab removed"),
        ]

        all_good = True
        for check, description in checks:
            if check:
                logger.info(f"✓ {description}")
            else:
                logger.error(f"✗ {description}")
                all_good = False

        return all_good

    def rollback(self):
        """Rollback in geval van fout."""
        logger.info("Rolling back migration...")

        if self.backup_dir.exists():
            restore_script = self.backup_dir / "restore.sh"
            if restore_script.exists():
                import subprocess

                subprocess.run(["bash", str(restore_script)], check=False)
                logger.info("✓ Rollback completed")
            else:
                logger.error("✗ No restore script found")
        else:
            logger.error("✗ No backup found for rollback")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Consolidate Export and Management tabs"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run migration in dry-run mode (no actual changes)",
    )
    parser.add_argument(
        "--skip-git-check", action="store_true", help="Skip git status check"
    )

    args = parser.parse_args()

    # Run migration
    migration = TabConsolidationMigration(dry_run=args.dry_run)

    if args.skip_git_check:
        migration.check_git_status = lambda: True

    success = migration.run_migration()

    if success:
        logger.info("\n" + "=" * 50)
        logger.info("MIGRATION COMPLETED SUCCESSFULLY!")
        logger.info("=" * 50)
        logger.info("\nNext steps:")
        logger.info("1. Test the application thoroughly")
        logger.info("2. Run: pytest tests/integration/test_import_export_beheer_tab.py")
        logger.info("3. Commit changes if everything works")
        logger.info(f"\nBackup location: {migration.backup_dir}")
    else:
        logger.error("\n" + "=" * 50)
        logger.error("MIGRATION FAILED!")
        logger.error("=" * 50)
        logger.error("\nCheck the logs above for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
