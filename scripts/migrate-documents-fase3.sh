#\!/bin/bash

# Document Migratie Script Fase 3 voor DefinitieAgent
# Dit script ruimt de laatste bestanden in root op
# Gebruik: ./scripts/migrate-documents-fase3.sh [--dry-run|--execute]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default to dry-run mode
MODE="dry-run"
if [ "$1" == "--execute" ]; then
    MODE="execute"
fi

echo -e "${BLUE}=== Document Migratie Script - Fase 3 ===${NC}"
echo -e "Mode: ${YELLOW}$MODE${NC}\n"

# Function to move a file
move_file() {
    local source=$1
    local dest=$2

    if [ "$MODE" == "execute" ]; then
        # Create destination directory if it doesn't exist
        mkdir -p "$(dirname "$dest")"
        mv "$source" "$dest"
        echo -e "${GREEN}✓${NC} Verplaatst: $source → $dest"
    else
        echo -e "${YELLOW}Zou verplaatsen:${NC} $source → $dest"
    fi
}

# Migreer analyse documenten
migrate_analysis_docs() {
    echo -e "\n${BLUE}Analyse documenten migreren...${NC}"

    if [ -f "modular_prompt_system_analysis.md" ]; then
        move_file "modular_prompt_system_analysis.md" "docs/architectuur/modular-prompt-system-analyse.md"
    fi
}

# Migreer test bestanden
migrate_test_files() {
    echo -e "\n${BLUE}Test bestanden migreren...${NC}"

    if [ -f "test_modular_prompts.py" ]; then
        move_file "test_modular_prompts.py" "tests/integration/test_modular_prompts.py"
    fi
    if [ -f "test_output.log" ]; then
        move_file "test_output.log" "logs/test_output.log"
    fi
}

# Maak benodigde directories
create_directories() {
    echo -e "\n${BLUE}Benodigde mappen aanmaken...${NC}"

    local dirs=(
        "logs"
    )

    for dir in "${dirs[@]}"; do
        if [ "$MODE" == "execute" ]; then
            mkdir -p "$dir"
            echo -e "${GREEN}✓${NC} Map aangemaakt: $dir"
        else
            echo -e "${YELLOW}Zou aanmaken:${NC} $dir"
        fi
    done
}

# Toon overzicht van wat blijft staan
show_remaining_files() {
    echo -e "\n${BLUE}Bestanden die in root blijven:${NC}"
    echo "✓ README.md"
    echo "✓ CONTRIBUTING.md" 
    echo "✓ CHANGELOG.md"
    echo "✓ pyproject.toml"
    echo "✓ requirements.txt"
    echo "✓ requirements-dev.txt"
    echo "✓ .gitignore"
    echo "✓ cache/ (tijdelijke bestanden)"
    echo "✓ exports/ (gegenereerde exports)"
    echo "✓ venv/ (virtual environment)"
}

# Main execution
main() {
    echo -e "${BLUE}Start document migratie fase 3...${NC}\n"

    create_directories
    migrate_analysis_docs
    migrate_test_files

    echo -e "\n${BLUE}Migratie overzicht:${NC}"
    if [ "$MODE" == "dry-run" ]; then
        echo -e "${YELLOW}Dit was een dry run. Geen bestanden zijn verplaatst.${NC}"
        echo -e "Om uit te voeren: ${GREEN}./scripts/migrate-documents-fase3.sh --execute${NC}"
    else
        echo -e "${GREEN}Migratie fase 3 succesvol afgerond\!${NC}"
        echo -e "\nVolgende stappen:"
        echo -e "1. Voer uit: ${YELLOW}git add -A${NC}"
        echo -e "2. Voer uit: ${YELLOW}git commit -m \"refactor: fase 3 document organisatie - laatste opruiming\"${NC}"
        echo -e "\nDe root directory is nu volledig opgeruimd\! 🎉"
    fi

    show_remaining_files
}

# Run the migration
main
