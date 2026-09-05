#!/usr/bin/env bash
#
# Auto-backup script for definities.db
#
# Backs up database with timestamp to prevent data loss
# Can be run manually or via cron/launchd
#
# Usage:
#   ./scripts/auto_backup_database.sh
#
# Setup hourly backups via cron:
#   crontab -e
#   Add: 0 * * * * /path/to/Definitie-app/scripts/auto_backup_database.sh

set -euo pipefail

# Configuration
# pwd -P: fysiek pad, de backuphelper weigert symlinks in het pad (DEF-663).
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
DB_PATH="$PROJECT_ROOT/data/definities.db"
BACKUP_DIR="$PROJECT_ROOT/data/backups/auto"
MAX_BACKUPS=24  # Keep 24 hourly backups (1 day)
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Project-Python voor de gedeelde WAL-veilige backuphelper (DEF-663):
# expliciete PYTHON, anders de project-venv, anders python3.
if [ -z "${PYTHON:-}" ]; then
    if [ -x "$PROJECT_ROOT/.venv/bin/python" ]; then
        PYTHON="$PROJECT_ROOT/.venv/bin/python"
    else
        PYTHON="python3"
    fi
fi

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo -e "${RED}❌ Database niet gevonden: $DB_PATH${NC}"
    exit 1
fi

# Check database integrity
echo -e "${GREEN}🔍 Checking database integrity...${NC}"
if ! sqlite3 "$DB_PATH" "PRAGMA integrity_check;" | grep -q "ok"; then
    echo -e "${RED}❌ Database integrity check FAILED!${NC}"
    exit 1
fi

# Get database size and record count
DB_SIZE=$(du -h "$DB_PATH" | cut -f1)
RECORD_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM definities;")

echo -e "${GREEN}📊 Database stats:${NC}"
echo -e "   Size: $DB_SIZE"
echo -e "   Definities: $RECORD_COUNT"

# Create backup filename
BACKUP_NAME="definities_backup_${TIMESTAMP}.db"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

# Perform backup (DEF-663): SQLite Online Backup API vanuit één read-only
# snapshot (WAL-veilig), verificatie (integrity_check + kernschema + manifest)
# vóór publicatie, en nooit een bestaand backupbestand overschrijven. Bij een
# fout laat de helper geen eindbestand achter.
echo -e "${GREEN}💾 Creating backup: $BACKUP_NAME${NC}"
if ! PYTHONPATH="$PROJECT_ROOT/src" "$PYTHON" -m database.sqlite_backup "$DB_PATH" "$BACKUP_PATH"; then
    echo -e "${RED}❌ Backup FAILED (geen backupbestand gepubliceerd)${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Backup verified and published: $BACKUP_PATH${NC}"

# Cleanup old backups (keep last MAX_BACKUPS)
echo -e "${GREEN}🧹 Cleaning old backups (keeping last $MAX_BACKUPS)...${NC}"
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/definities_backup_*.db 2>/dev/null | wc -l | tr -d ' ')

if [ "$BACKUP_COUNT" -gt "$MAX_BACKUPS" ]; then
    OLD_COUNT=$((BACKUP_COUNT - MAX_BACKUPS))
    echo -e "${YELLOW}   Removing $OLD_COUNT old backups${NC}"

    ls -1t "$BACKUP_DIR"/definities_backup_*.db | tail -n +"$((MAX_BACKUPS + 1))" | while read -r old_backup; do
        echo -e "   🗑️  Removing: $(basename "$old_backup")"
        rm -f "$old_backup"
    done
else
    echo -e "   ✅ No cleanup needed ($BACKUP_COUNT backups)"
fi

# Create latest symlink
LATEST_LINK="$BACKUP_DIR/latest.db"
rm -f "$LATEST_LINK"
ln -s "$BACKUP_NAME" "$LATEST_LINK"

# Summary
echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ BACKUP COMPLETED${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "Backup: $BACKUP_NAME"
echo -e "Location: $BACKUP_DIR"
echo -e "Backups kept: $(ls -1 "$BACKUP_DIR"/definities_backup_*.db 2>/dev/null | wc -l | tr -d ' ')"
echo -e "${GREEN}════════════════════════════════════════${NC}"

# Exit successfully
exit 0
