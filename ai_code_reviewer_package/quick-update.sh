#!/bin/bash
# Quick update script voor ai-code-reviewer in andere projecten
# Plaats dit script in je andere projecten voor makkelijke updates

set -e

SOURCE_DIR="/Users/chrislehnen/Projecten/Definitie-app/ai_code_reviewer_package"

echo "🔄 AI Code Reviewer Quick Updater"
echo "================================="

# Check of source directory bestaat
if [ ! -d "$SOURCE_DIR" ]; then
    echo "❌ Source directory niet gevonden: $SOURCE_DIR"
    echo "💡 Pas SOURCE_DIR aan in dit script naar de juiste locatie"
    exit 1
fi

# Haal huidige versie op
if command -v ai-code-review &> /dev/null; then
    CURRENT=$(ai-code-review --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo "onbekend")
    echo "📦 Huidige versie: $CURRENT"
fi

# Update vanaf lokale source
echo "\n🔧 Installeren vanaf lokale source..."
pip install -e "$SOURCE_DIR" --upgrade

# Verificatie
if command -v ai-code-review &> /dev/null; then
    NEW=$(ai-code-review --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo "onbekend")
    echo "\n✅ Update succesvol!"
    echo "🆕 Nieuwe versie: $NEW"
    echo "\n📝 Beschikbare commando's:"
    echo "  ai-code-review         - Run code review"
    echo "  ai-code-review setup   - Setup project"
    echo "  ai-code-review update  - Check for updates"
    echo "  ai-review             - Alias voor ai-code-review"
else
    echo "\n❌ Update mislukt!"
    exit 1
fi