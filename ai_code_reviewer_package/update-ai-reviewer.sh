#!/bin/bash
# Script om ai-code-reviewer te updaten in een ander project
# Gebruik: ./update-ai-reviewer.sh [git-url] [branch]

set -e

GIT_URL=${1:-"https://github.com/jouw-username/Definitie-app.git"}
BRANCH=${2:-"main"}

echo "🔄 AI Code Reviewer Updater"
echo "========================"
echo "Git URL: $GIT_URL"
echo "Branch: $BRANCH"
echo ""

# Check huidige versie
if command -v ai-code-review &> /dev/null; then
    CURRENT_VERSION=$(ai-code-review --version 2>/dev/null || echo "onbekend")
    echo "📋 Huidige versie: $CURRENT_VERSION"
else
    echo "⚠️  AI Code Reviewer is nog niet geïnstalleerd"
fi

# Update of installeer
echo "\n📦 Installeren/updaten vanaf Git..."
pip install --upgrade "git+${GIT_URL}@${BRANCH}#subdirectory=ai_code_reviewer_package"

# Verificatie
if command -v ai-code-review &> /dev/null; then
    NEW_VERSION=$(ai-code-review --version 2>/dev/null || echo "onbekend")
    echo "\n✅ Succesvol geïnstalleerd!"
    echo "🆕 Nieuwe versie: $NEW_VERSION"
    echo "\n🚀 Je kunt nu gebruiken:"
    echo "   ai-code-review"
    echo "   ai-review"
    echo "   setup-ai-review"
else
    echo "\n❌ Installatie mislukt!"
    exit 1
fi