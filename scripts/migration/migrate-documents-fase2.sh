#!/bin/bash

# Document Migratie Script Fase 2 voor DefinitieAgent
# Dit script ruimt de overgebleven documenten in root op
# Gebruik: ./scripts/migrate-documents-fase2.sh [--dry-run|--execute]

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

echo -e "${BLUE}=== Document Migratie Script - Fase 2 ===${NC}"
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

# Migreer architectuur documenten
migrate_architecture_docs() {
    echo -e "\n${BLUE}Architectuur documenten migreren...${NC}"

    # Enterprise Architecture documenten
    if [ -f "EA_SA_ANALYSIS_WORKFLOW.md" ]; then
        move_file "EA_SA_ANALYSIS_WORKFLOW.md" "docs/architectuur/workflows/ea-sa-analyse-workflow.md"
    fi
    if [ -f "EA_SA_ENTERPRISE_ANALYSIS_REPORT.md" ]; then
        move_file "EA_SA_ENTERPRISE_ANALYSIS_REPORT.md" "docs/architectuur/_archive/ea-sa-enterprise-analyse-rapport.md"
    fi

    # Architectuur analyses
    if [ -f "ARCHITECTURE_IMPLEMENTATION_ANALYSIS.md" ]; then
        move_file "ARCHITECTURE_IMPLEMENTATION_ANALYSIS.md" "docs/architectuur/_archive/architectuur-implementatie-analyse.md"
    fi
    if [ -f "architecture_audit_report.md" ]; then
        move_file "architecture_audit_report.md" "docs/architectuur/_archive/architectuur-audit-rapport.md"
    fi
    if [ -f "complete_architecture_analysis_report.md" ]; then
        move_file "complete_architecture_analysis_report.md" "docs/architectuur/_archive/complete-architectuur-analyse-rapport.md"
    fi

    # Service architectuur
    if [ -f "SERVICE_ARCHITECTUUR_WORKFLOW.md" ]; then
        move_file "SERVICE_ARCHITECTUUR_WORKFLOW.md" "docs/architectuur/workflows/service-architectuur-workflow.md"
    fi
    if [ -f "DEFINITION_GENERATION_ARCHITECTURE_ANALYSIS.md" ]; then
        move_file "DEFINITION_GENERATION_ARCHITECTURE_ANALYSIS.md" "docs/architectuur/definitie service/definitie-generatie-architectuur-analyse.md"
    fi

    # Root cause analyses
    if [ -f "VISUAL_ROOT_CAUSE_ANALYSIS.md" ]; then
        move_file "VISUAL_ROOT_CAUSE_ANALYSIS.md" "docs/analyse/visuele-root-cause-analyse.md"
    fi
    if [ -f "VISUAL_ROOT_CAUSE_ANALYSIS_UITGEBREID.md" ]; then
        move_file "VISUAL_ROOT_CAUSE_ANALYSIS_UITGEBREID.md" "docs/analyse/visuele-root-cause-analyse-uitgebreid.md"
    fi
}

# Migreer workflow documenten
migrate_workflow_docs() {
    echo -e "\n${BLUE}Workflow documenten migreren...${NC}"

    if [ -f "TEST_CATEGORY_WORKFLOW.md" ]; then
        move_file "TEST_CATEGORY_WORKFLOW.md" "docs/workflows/test-categorie-workflow.md"
    fi
}

# Migreer technische documentatie
migrate_technical_docs() {
    echo -e "\n${BLUE}Technische documentatie migreren...${NC}"

    if [ -f "EXTRACTED_VALIDATION_RULES.md" ]; then
        move_file "EXTRACTED_VALIDATION_RULES.md" "docs/technisch/geextraheerde-validatie-regels.md"
    fi
    if [ -f "PYTHON_BESTANDEN_OVERZICHT.md" ]; then
        move_file "PYTHON_BESTANDEN_OVERZICHT.md" "docs/technisch/python-bestanden-overzicht.md"
    fi
    if [ -f "module_dependency_report.md" ]; then
        move_file "module_dependency_report.md" "docs/technisch/module-afhankelijkheid-rapport.md"
    fi
}

# Migreer reviews en rapporten
migrate_reviews() {
    echo -e "\n${BLUE}Reviews en rapporten migreren...${NC}"

    if [ -f "review_report.md" ]; then
        move_file "review_report.md" "docs/reviews/review-rapport.md"
    fi
    if [ -f "session_state_analysis_report.md" ]; then
        move_file "session_state_analysis_report.md" "docs/analyse/session-state-analyse-rapport.md"
    fi
}

# Migreer data bestanden
migrate_data_files() {
    echo -e "\n${BLUE}Data bestanden migreren...${NC}"

    if [ -f "service_dependencies.json" ]; then
        move_file "service_dependencies.json" "reports/analysis/service-afhankelijkheden.json"
    fi
    if [ -f "dependency_analysis.py" ]; then
        move_file "dependency_analysis.py" "scripts/analysis/dependency_analysis.py"
    fi
}

# Maak benodigde directories
create_directories() {
    echo -e "\n${BLUE}Benodigde mappen aanmaken...${NC}"

    local dirs=(
        "docs/architectuur/workflows"
        "docs/architectuur/definitie service"
        "docs/analyse"
        "docs/technisch"
        "docs/reviews"
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

# Controle op database bestanden
check_database_files() {
    echo -e "\n${BLUE}Database bestanden controleren...${NC}"

    if [ -f "definities.db" ]; then
        echo -e "${YELLOW}⚠️  Waarschuwing:${NC} definities.db staat in root"
        echo "   Dit is waarschijnlijk de productie database"
        echo "   Overweeg om deze te verplaatsen naar data/database/"
        echo "   OF voeg toe aan .gitignore als dit een lokale database is"
    fi
}

# Toon overzicht van wat blijft staan
show_remaining_files() {
    echo -e "\n${BLUE}Bestanden die in root blijven:${NC}"
    echo "✓ README.md"
    echo "✓ CONTRIBUTING.md"
    echo "✓ CHANGELOG.md"
    echo "✓ LICENSE (als die er is)"
    echo "✓ pyproject.toml"
    echo "✓ requirements.txt"
    echo "✓ requirements-dev.txt"
    echo "✓ .gitignore"
    echo "✓ .env.example"
}

# Main execution
main() {
    echo -e "${BLUE}Start document migratie fase 2...${NC}\n"

    create_directories
    migrate_architecture_docs
    migrate_workflow_docs
    migrate_technical_docs
    migrate_reviews
    migrate_data_files
    check_database_files

    echo -e "\n${BLUE}Migratie overzicht:${NC}"
    if [ "$MODE" == "dry-run" ]; then
        echo -e "${YELLOW}Dit was een dry run. Geen bestanden zijn verplaatst.${NC}"
        echo -e "Om uit te voeren: ${GREEN}./scripts/migrate-documents-fase2.sh --execute${NC}"
    else
        echo -e "${GREEN}Migratie fase 2 succesvol afgerond!${NC}"
        echo -e "\nVolgende stappen:"
        echo -e "1. Controleer de database locatie"
        echo -e "2. Voer uit: ${YELLOW}git add -A${NC}"
        echo -e "3. Voer uit: ${YELLOW}git commit -m \"refactor: fase 2 document organisatie\"${NC}"
    fi

    show_remaining_files
}

# Run the migration
main
