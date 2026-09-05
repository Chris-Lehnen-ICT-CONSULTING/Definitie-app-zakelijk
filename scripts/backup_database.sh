#!/bin/bash
# Database Backup Script
# Maakt een timestamped backup van de SQLite database

set -e  # Exit on error

# Configuratie
# pwd -P: fysiek pad, de backuphelper weigert symlinks in het pad (DEF-663).
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
DB_PATH="${PROJECT_ROOT}/data/definities.db"
BACKUP_DIR="${PROJECT_ROOT}/data/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/definities_backup_${TIMESTAMP}.db"

# Project-Python voor de gedeelde WAL-veilige backuphelper (DEF-663):
# expliciete PYTHON, anders de project-venv, anders python3.
if [ -z "${PYTHON:-}" ]; then
    if [ -x "${PROJECT_ROOT}/.venv/bin/python" ]; then
        PYTHON="${PROJECT_ROOT}/.venv/bin/python"
    else
        PYTHON="python3"
    fi
fi

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

# Maak backup via de gedeelde helper (DEF-663): SQLite Online Backup API vanuit
# één read-only snapshot (WAL-veilig), verificatie (integrity_check +
# kernschema + manifest) vóór publicatie, nooit een bestaand bestand
# overschrijven. Bij een fout blijft er geen eindbestand achter.
echo "Backup maken..."
if ! PYTHONPATH="${PROJECT_ROOT}/src" "$PYTHON" -m database.sqlite_backup "$DB_PATH" "$BACKUP_FILE"; then
    echo -e "${RED}ERROR: Backup maken gefaald (geen backupbestand gepubliceerd)${NC}"
    exit 1
fi

# Toon resultaat
if [ -f "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}✓ Backup succesvol gemaakt en geverifieerd${NC}"
    echo -e "${YELLOW}Backup grootte:${NC} $BACKUP_SIZE"

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
    echo "Om te herstellen naar een NIEUWE database (nooit met cp over de live bron heen):"
    echo "  PYTHONPATH=\"${PROJECT_ROOT}/src\" \"$PYTHON\" -m database.sqlite_backup \"$BACKUP_FILE\" /pad/naar/nieuwe.db"
    echo "In-place herstel valt buiten dit script: zie scripts/backup_restore.py (DEF-666)."
    echo ""

    # Lijst recent backups
    echo "Recente backups:"
    ls -lht "$BACKUP_DIR" | head -6

else
    echo -e "${RED}ERROR: Backup maken gefaald${NC}"
    exit 1
fi
