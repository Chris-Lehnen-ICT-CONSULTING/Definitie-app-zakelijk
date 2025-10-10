#!/bin/bash
# Database Backup Script
# Maakt een timestamped backup van de SQLite database

set -e  # Exit on error

# Configuratie
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_PATH="${PROJECT_ROOT}/data/definities.db"
BACKUP_DIR="${PROJECT_ROOT}/data/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/definities_backup_${TIMESTAMP}.db"

# Kleuren voor output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "================================================"
echo "  Database Backup Script"
echo "================================================"
echo ""

# Check of database bestaat
if [ ! -f "$DB_PATH" ]; then
    echo -e "${RED}ERROR: Database niet gevonden: $DB_PATH${NC}"
    exit 1
fi

# Maak backup directory aan indien niet bestaat
mkdir -p "$BACKUP_DIR"

# Toon database info
DB_SIZE=$(du -h "$DB_PATH" | cut -f1)
echo -e "${YELLOW}Database:${NC} $DB_PATH"
echo -e "${YELLOW}Grootte:${NC}  $DB_SIZE"
echo -e "${YELLOW}Backup:${NC}   $BACKUP_FILE"
echo ""

# Maak backup met SQLite's .backup commando (meest betrouwbaar)
echo "Backup maken..."
sqlite3 "$DB_PATH" ".backup '${BACKUP_FILE}'"

# Verify backup
if [ -f "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}✓ Backup succesvol gemaakt${NC}"
    echo -e "${YELLOW}Backup grootte:${NC} $BACKUP_SIZE"

    # Verify integrity van backup
    echo ""
    echo "Backup integriteit controleren..."
    if sqlite3 "$BACKUP_FILE" "PRAGMA integrity_check;" | grep -q "ok"; then
        echo -e "${GREEN}✓ Backup integriteit OK${NC}"
    else
        echo -e "${RED}⚠ WARNING: Backup integriteit check gefaald${NC}"
        exit 1
    fi

    # Toon aantal tabellen in backup
    TABLE_COUNT=$(sqlite3 "$BACKUP_FILE" "SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
    echo -e "${YELLOW}Tabellen in backup:${NC} $TABLE_COUNT"

    echo ""
    echo "================================================"
    echo -e "${GREEN}BACKUP COMPLEET${NC}"
    echo "================================================"
    echo ""
    echo "Backup locatie: $BACKUP_FILE"
    echo ""
    echo "Om te restoren:"
    echo "  cp \"$BACKUP_FILE\" \"$DB_PATH\""
    echo ""

    # Lijst recent backups
    echo "Recente backups:"
    ls -lht "$BACKUP_DIR" | head -6

else
    echo -e "${RED}ERROR: Backup maken gefaald${NC}"
    exit 1
fi
