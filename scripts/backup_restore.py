#!/usr/bin/env python3
"""
Database Backup and Restore Utility

Features:
- Create timestamped backups
- Compress backups with gzip
- Restore from backup
- Verify backup integrity
- Clean old backups (retention policy)
- List available backups
"""

import argparse
import gzip
import logging
import shutil
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/backup_restore.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class DatabaseBackupManager:
    """Manages database backups and restores."""

    def __init__(
        self, db_path: str, backup_dir: str = "data/backups", compress: bool = True
    ):
        """
        Initialize backup manager.

        Args:
            db_path: Path to the database file
            backup_dir: Directory to store backups
            compress: Whether to compress backups with gzip
        """
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        self.compress = compress

        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Validate database exists
        if not self.db_path.exists():
            msg = f"Database not found: {self.db_path}"
            raise FileNotFoundError(msg)

    def create_backup(self, description: str = "") -> Path:
        """
        Create a backup of the database.

        Args:
            description: Optional description for the backup

        Returns:
            Path to the created backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"definities_backup_{timestamp}"

        if description:
            # Sanitize description for filename
            safe_desc = "".join(
                c for c in description if c.isalnum() or c in ("-", "_")
            )[:50]
            backup_name = f"{backup_name}_{safe_desc}"

        backup_path = self.backup_dir / f"{backup_name}.db"

        logger.info(f"Creating backup: {backup_path}")

        try:
            # Use SQLite's backup API for consistency
            source_conn = sqlite3.connect(str(self.db_path))
            backup_conn = sqlite3.connect(str(backup_path))

            with backup_conn:
                source_conn.backup(backup_conn)

            source_conn.close()
            backup_conn.close()

            # Compress if requested
            if self.compress:
                compressed_path = backup_path.with_suffix(".db.gz")
                logger.info(f"Compressing backup: {compressed_path}")

                with (
                    open(backup_path, "rb") as f_in,
                    gzip.open(compressed_path, "wb") as f_out,
                ):
                    shutil.copyfileobj(f_in, f_out)

                # Remove uncompressed file
                backup_path.unlink()
                backup_path = compressed_path

            # Verify backup
            if self.verify_backup(backup_path):
                logger.info(f"Backup created successfully: {backup_path}")
                logger.info(
                    f"Backup size: {backup_path.stat().st_size / 1024 / 1024:.2f} MB"
                )
                return backup_path
            logger.error("Backup verification failed")
            backup_path.unlink()
            msg = "Backup verification failed"
            raise RuntimeError(msg)

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            if backup_path.exists():
                backup_path.unlink()
            raise

    def restore_backup(
        self, backup_path: Path, create_backup_before_restore: bool = True
    ) -> bool:
        """
        Restore database from backup.

        Args:
            backup_path: Path to backup file
            create_backup_before_restore: Create backup of current DB before restore

        Returns:
            True if restore successful
        """
        if not backup_path.exists():
            msg = f"Backup not found: {backup_path}"
            raise FileNotFoundError(msg)

        logger.info(f"Restoring from backup: {backup_path}")

        try:
            # Create backup of current database before restore
            if create_backup_before_restore and self.db_path.exists():
                logger.info("Creating safety backup before restore...")
                safety_backup = self.create_backup(description="pre_restore_safety")
                logger.info(f"Safety backup created: {safety_backup}")

            # Decompress if needed
            temp_backup = backup_path
            if backup_path.suffix == ".gz":
                temp_backup = backup_path.with_suffix("")
                logger.info("Decompressing backup...")

                with (
                    gzip.open(backup_path, "rb") as f_in,
                    open(temp_backup, "wb") as f_out,
                ):
                    shutil.copyfileobj(f_in, f_out)

            # Verify backup before restore
            if not self.verify_backup(temp_backup):
                logger.error("Backup verification failed, aborting restore")
                if temp_backup != backup_path:
                    temp_backup.unlink()
                return False

            # Perform restore
            logger.info(f"Restoring to: {self.db_path}")
            shutil.copy2(temp_backup, self.db_path)

            # Cleanup temp file if we decompressed
            if temp_backup != backup_path:
                temp_backup.unlink()

            # Verify restored database
            if self._verify_database(self.db_path):
                logger.info("Database restored successfully")
                return True
            logger.error("Restored database verification failed")
            return False

        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            raise

    def verify_backup(self, backup_path: Path) -> bool:
        """
        Verify backup integrity.

        Args:
            backup_path: Path to backup file

        Returns:
            True if backup is valid
        """
        try:
            # Decompress if needed
            temp_path = backup_path
            if backup_path.suffix == ".gz":
                temp_path = backup_path.with_suffix("")
                with (
                    gzip.open(backup_path, "rb") as f_in,
                    open(temp_path, "wb") as f_out,
                ):
                    shutil.copyfileobj(f_in, f_out)

            # Verify database
            result = self._verify_database(temp_path)

            # Cleanup temp file
            if temp_path != backup_path:
                temp_path.unlink()

            return result

        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            return False

    def list_backups(self) -> list[tuple[Path, datetime, int]]:
        """
        List all available backups.

        Returns:
            List of tuples (path, timestamp, size_bytes)
        """
        backups = []

        for backup_file in self.backup_dir.glob("definities_backup_*.db*"):
            timestamp = datetime.fromtimestamp(backup_file.stat().st_mtime)
            size = backup_file.stat().st_size
            backups.append((backup_file, timestamp, size))

        # Sort by timestamp, newest first
        backups.sort(key=lambda x: x[1], reverse=True)

        return backups

    def clean_old_backups(
        self, days: int = 30, keep_minimum: int = 5, dry_run: bool = False
    ) -> int:
        """
        Clean old backups based on retention policy.

        Args:
            days: Delete backups older than this many days
            keep_minimum: Always keep at least this many recent backups
            dry_run: If True, only show what would be deleted

        Returns:
            Number of backups deleted
        """
        logger.info(
            f"Cleaning backups older than {days} days (keeping minimum {keep_minimum})"
        )

        backups = self.list_backups()
        cutoff_date = datetime.now() - timedelta(days=days)

        deleted_count = 0

        for i, (backup_path, timestamp, _size) in enumerate(backups):
            # Keep minimum number of recent backups
            if i < keep_minimum:
                logger.debug(f"Keeping recent backup: {backup_path.name}")
                continue

            # Delete old backups
            if timestamp < cutoff_date:
                if dry_run:
                    logger.info(f"Would delete: {backup_path.name} ({timestamp})")
                else:
                    logger.info(
                        f"Deleting old backup: {backup_path.name} ({timestamp})"
                    )
                    backup_path.unlink()
                deleted_count += 1

        if dry_run:
            logger.info(f"Dry run: would delete {deleted_count} backups")
        else:
            logger.info(f"Deleted {deleted_count} old backups")

        return deleted_count

    @staticmethod
    def _verify_database(db_path: Path) -> bool:
        """Verify database integrity."""
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Run integrity check
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()

            conn.close()

            if result and result[0] == "ok":
                logger.debug(f"Database integrity check passed: {db_path}")
                return True
            logger.error(f"Database integrity check failed: {result}")
            return False

        except sqlite3.Error as e:
            logger.error(f"Database verification failed: {e}")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Database backup and restore utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a backup
  python scripts/backup_restore.py backup

  # Create a backup with description
  python scripts/backup_restore.py backup --description "before_migration"

  # List all backups
  python scripts/backup_restore.py list

  # Restore from a specific backup
  python scripts/backup_restore.py restore data/backups/definities_backup_20250102_143022.db.gz

  # Clean old backups (dry run)
  python scripts/backup_restore.py clean --days 30 --dry-run

  # Clean old backups (actual)
  python scripts/backup_restore.py clean --days 30 --keep-minimum 10
        """,
    )

    parser.add_argument(
        "action",
        choices=["backup", "restore", "list", "verify", "clean"],
        help="Action to perform",
    )

    parser.add_argument(
        "backup_file", nargs="?", help="Backup file path (for restore/verify actions)"
    )

    parser.add_argument(
        "--db-path",
        type=str,
        default="data/definities.db",
        help="Database file path (default: data/definities.db)",
    )

    parser.add_argument(
        "--backup-dir",
        type=str,
        default="data/backups",
        help="Backup directory (default: data/backups)",
    )

    parser.add_argument("--description", type=str, help="Description for the backup")

    parser.add_argument(
        "--no-compress", action="store_true", help="Do not compress backups"
    )

    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Days to keep backups (for clean action, default: 30)",
    )

    parser.add_argument(
        "--keep-minimum",
        type=int,
        default=5,
        help="Minimum number of backups to keep (default: 5)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without doing it",
    )

    parser.add_argument(
        "--no-safety-backup",
        action="store_true",
        help="Do not create safety backup before restore",
    )

    args = parser.parse_args()

    # Ensure log directory exists
    Path("logs").mkdir(exist_ok=True)

    try:
        manager = DatabaseBackupManager(
            db_path=args.db_path,
            backup_dir=args.backup_dir,
            compress=not args.no_compress,
        )

        if args.action == "backup":
            backup_path = manager.create_backup(description=args.description or "")
            print(f"Backup created: {backup_path}")
            sys.exit(0)

        elif args.action == "restore":
            if not args.backup_file:
                logger.error("Backup file required for restore action")
                sys.exit(1)

            backup_path = Path(args.backup_file)
            success = manager.restore_backup(
                backup_path, create_backup_before_restore=not args.no_safety_backup
            )
            sys.exit(0 if success else 1)

        elif args.action == "list":
            backups = manager.list_backups()

            if not backups:
                print("No backups found")
            else:
                print(f"\nFound {len(backups)} backups:\n")
                for backup_path, timestamp, size in backups:
                    size_mb = size / 1024 / 1024
                    print(f"  {backup_path.name}")
                    print(f"    Date: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"    Size: {size_mb:.2f} MB")
                    print()

            sys.exit(0)

        elif args.action == "verify":
            if not args.backup_file:
                logger.error("Backup file required for verify action")
                sys.exit(1)

            backup_path = Path(args.backup_file)
            if manager.verify_backup(backup_path):
                print(f"Backup is valid: {backup_path}")
                sys.exit(0)
            else:
                print(f"Backup is invalid: {backup_path}")
                sys.exit(1)

        elif args.action == "clean":
            manager.clean_old_backups(
                days=args.days, keep_minimum=args.keep_minimum, dry_run=args.dry_run
            )
            sys.exit(0)

    except Exception as e:
        logger.error(f"Operation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
