#!/bin/bash

# Document Migratie Script voor DefinitieAgent
# Dit script organiseert alle documenten volgens de nieuwe structuur
# Gebruik: ./scripts/migrate-documents.sh [--dry-run|--execute]

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

echo -e "${BLUE}=== Document Migration Script ===${NC}"
echo -e "Mode: ${YELLOW}$MODE${NC}\n"

# Create directory structure
create_directories() {
    local dirs=(
        "reports/analysis"
        "reports/validation"
        "reports/visualizations"
        "scripts/analysis"
        "scripts/maintenance"
        "scripts/testing"
        "docs/guides"
        "docs/api"
        "docs/meeting-notes"
        "docs/archief/2025-01"
    )

    for dir in "${dirs[@]}"; do
        if [ "$MODE" == "execute" ]; then
            mkdir -p "$dir"
            echo -e "${GREEN}✓${NC} Created: $dir"
        else
            echo -e "${YELLOW}Would create:${NC} $dir"
        fi
    done
}

# Function to move a file
move_file() {
    local source=$1
    local dest=$2

    if [ "$MODE" == "execute" ]; then
        # Create destination directory if it doesn't exist
        mkdir -p "$(dirname "$dest")"
        mv "$source" "$dest"
        echo -e "${GREEN}✓${NC} Moved: $source → $dest"
    else
        echo -e "${YELLOW}Would move:${NC} $source → $dest"
    fi
}

# Migrate Python scripts from root
migrate_python_scripts() {
    echo -e "\n${BLUE}Migrating Python scripts...${NC}"

    # Analysis scripts
    local analysis_scripts=(
        "analyze_core_module.py"
        "analyze_dependencies.py"
        "analyze_modular_structure.py"
        "module_dependency_analysis.py"
        "compare_modules.py"
    )

    for script in "${analysis_scripts[@]}"; do
        if [ -f "$script" ]; then
            move_file "$script" "scripts/analysis/$script"
        fi
    done

    # Test scripts
    for file in test_*.py; do
        if [ -f "$file" ]; then
            move_file "$file" "tests/regression/$file"
        fi
    done

    # Tool scripts
    if [ -f "code_review_tool.py" ]; then
        move_file "code_review_tool.py" "scripts/maintenance/code_review_tool.py"
    fi
    if [ -f "security_review.py" ]; then
        move_file "security_review.py" "scripts/maintenance/security_review.py"
    fi
    if [ -f "trace_prompt_decision.py" ]; then
        move_file "trace_prompt_decision.py" "scripts/analysis/trace_prompt_decision.py"
    fi
}

# Migrate reports
migrate_reports() {
    echo -e "\n${BLUE}Migrating reports...${NC}"

    # JSON reports
    for file in *.json; do
        if [ -f "$file" ] && [[ "$file" == *"report"* || "$file" == *"analysis"* ]]; then
            move_file "$file" "reports/analysis/$file"
        fi
    done

    # HTML visualizations
    for file in *.html; do
        if [ -f "$file" ]; then
            move_file "$file" "reports/visualizations/$file"
        fi
    done
}

# Migrate documentation
migrate_documentation() {
    echo -e "\n${BLUE}Migrating documentation...${NC}"

    # Workflow and planning docs
    local workflow_docs=(
        "DOCUMENTATIE_REORGANISATIE_PLAN.md"
        "MIGRATION_ROADMAP.md"
        "PHASE_6_IMPLEMENTATION_CHECKLIST.md"
    )

    for doc in "${workflow_docs[@]}"; do
        if [ -f "$doc" ]; then
            # Convert to English lowercase naming
            local new_name=$(echo "$doc" | tr '[:upper:]' '[:lower:]' | sed 's/_/-/g')
            move_file "$doc" "docs/workflows/$new_name"
        fi
    done

    # Architecture docs
    local arch_docs=(
        "ARCHITECTURE_COMPLETION_REPORT.md"
        "MULTI_AGENT_ROOT_CAUSE_ANALYSIS.md"
    )

    for doc in "${arch_docs[@]}"; do
        if [ -f "$doc" ]; then
            local new_name=$(echo "$doc" | tr '[:upper:]' '[:lower:]' | sed 's/_/-/g')
            move_file "$doc" "docs/architecture/$new_name"
        fi
    done

    # Security and analysis docs to guides
    if [ -f "SECURITY_AND_FEEDBACK_ANALYSIS.md" ]; then
        move_file "SECURITY_AND_FEEDBACK_ANALYSIS.md" "docs/guides/security-and-feedback-analysis.md"
    fi
    if [ -f "TRUE_MODULAR_SYSTEM_DEPLOYMENT.md" ]; then
        move_file "TRUE_MODULAR_SYSTEM_DEPLOYMENT.md" "docs/architecture/true-modular-system-deployment.md"
    fi
}

# Update .gitignore
update_gitignore() {
    echo -e "\n${BLUE}Updating .gitignore...${NC}"

    if ! grep -q "^reports/" .gitignore 2>/dev/null; then
        if [ "$MODE" == "execute" ]; then
            echo -e "\n# Generated reports\nreports/" >> .gitignore
            echo -e "${GREEN}✓${NC} Added reports/ to .gitignore"
        else
            echo -e "${YELLOW}Would add:${NC} reports/ to .gitignore"
        fi
    fi
}

# Main execution
main() {
    echo -e "${BLUE}Starting document migration...${NC}\n"

    create_directories
    migrate_python_scripts
    migrate_reports
    migrate_documentation
    update_gitignore

    echo -e "\n${BLUE}Migration summary:${NC}"
    if [ "$MODE" == "dry-run" ]; then
        echo -e "${YELLOW}This was a dry run. No files were moved.${NC}"
        echo -e "To execute the migration, run: ${GREEN}./scripts/migrate-documents.sh --execute${NC}"
    else
        echo -e "${GREEN}Migration completed successfully!${NC}"
        echo -e "\nNext steps:"
        echo -e "1. Run: ${YELLOW}git add -A${NC}"
        echo -e "2. Run: ${YELLOW}git commit -m \"refactor: reorganize project documentation\"${NC}"
        echo -e "3. Update any broken links in documentation"
    fi
}

# Run the migration
main
