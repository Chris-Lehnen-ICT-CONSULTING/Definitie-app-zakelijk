#!/usr/bin/env bash
#
# Setup auto-backup via launchd (macOS)
#
# This script installs the launchd plist to run backups every hour

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🔧 DEFINITIE AUTO-BACKUP SETUP${NC}"
echo "════════════════════════════════════════"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLIST_SOURCE="$PROJECT_ROOT/scripts/com.definitieagent.backup.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/com.definitieagent.backup.plist"

# Ensure LaunchAgents directory exists
mkdir -p "$HOME/Library/LaunchAgents"

# Check if already installed
if [ -f "$PLIST_DEST" ]; then
    echo -e "${YELLOW}⚠️  Auto-backup is al geïnstalleerd${NC}"
    echo -e "   Wil je opnieuw installeren?"
    read -p "   (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ Geannuleerd${NC}"
        exit 0
    fi

    # Unload existing
    echo -e "${YELLOW}🔄 Unloading existing service...${NC}"
    launchctl unload "$PLIST_DEST" 2>/dev/null || true
    rm -f "$PLIST_DEST"
fi

# Copy plist
echo -e "${GREEN}📋 Installing launchd plist...${NC}"
cp "$PLIST_SOURCE" "$PLIST_DEST"

# Load service
echo -e "${GREEN}🚀 Loading service...${NC}"
launchctl load "$PLIST_DEST"

# Verify
if launchctl list | grep -q "com.definitieagent.backup"; then
    echo ""
    echo -e "${GREEN}════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ AUTO-BACKUP GEÏNSTALLEERD!${NC}"
    echo -e "${GREEN}════════════════════════════════════════${NC}"
    echo -e "Backup interval: Elk uur"
    echo -e "Backup locatie: data/backups/auto/"
    echo -e "Logs: logs/backup.log"
    echo ""
    echo -e "Commando's:"
    echo -e "  Check status: launchctl list | grep backup"
    echo -e "  Stop service: launchctl unload ~/Library/LaunchAgents/com.definitieagent.backup.plist"
    echo -e "  Start service: launchctl load ~/Library/LaunchAgents/com.definitieagent.backup.plist"
    echo -e "  View logs: tail -f logs/backup.log"
    echo -e "${GREEN}════════════════════════════════════════${NC}"
else
    echo -e "${RED}❌ Service load FAILED${NC}"
    echo -e "   Check logs: cat logs/backup.error.log"
    exit 1
fi
