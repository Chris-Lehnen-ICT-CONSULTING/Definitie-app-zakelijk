#!/bin/bash

# ============================================================================
# Ultra-Simpel Archivering Script - Definitie-app
# ============================================================================
# Doel: Verplaats ALLE oude/deprecated docs naar docs/archief/ (plat, geen subdirs)
# Mode: DRY-RUN by default (gebruik --execute om echt uit te voeren)
# ============================================================================

set -euo pipefail

# Kleuren
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Config
DRY_RUN=true
LOG_FILE="docs/archivering_$(date +%Y%m%d_%H%M%S).log"

# Parse arguments
for arg in "$@"; do
  case $arg in
    --execute)
      DRY_RUN=false
      ;;
    --help)
      echo "Usage: $0 [--execute]"
      echo "  --execute  Voer echt uit (default is dry-run)"
      exit 0
      ;;
  esac
done

# Functie voor logging
log_action() {
    if [ "$DRY_RUN" = true ]; then
        echo -e "${BLUE}[DRY-RUN]${NC} $1"
    else
        echo -e "${GREEN}[EXECUTE]${NC} $1"
        echo "[$(date)] $1" >> "$LOG_FILE"
    fi
}

echo "============================================================================"
echo "📚 Ultra-Simpel Archivering Script"
echo "============================================================================"
echo "Mode: $([ "$DRY_RUN" = true ] && echo "DRY-RUN" || echo "EXECUTE")"
echo ""

# Maak archief directory als die niet bestaat
if [ "$DRY_RUN" = false ]; then
    mkdir -p docs/archief
fi

ARCHIVED=0

echo -e "${BLUE}=== Te archiveren documenten ===${NC}"
echo ""

# 1. ALLE bestanden met LEGACY, DEPRECATED, OLD, ARCHIVED in de naam
for file in $(find docs -type f \( -name "*LEGACY*" -o -name "*DEPRECATED*" -o -name "*OLD*" -o -name "*ARCHIVED*" \) 2>/dev/null); do
    # Skip als het al in archief staat
    if [[ "$file" == docs/archief/* ]]; then
        continue
    fi

    filename=$(basename "$file")

    if [ "$DRY_RUN" = true ]; then
        log_action "Would move: $file → docs/archief/$filename"
    else
        mv "$file" "docs/archief/$filename"
        log_action "Moved: $file → docs/archief/$filename"
    fi
    ((ARCHIVED++))
done

# 2. ALLE reorganisatie plannen
for file in $(find docs -type f \( -name "*REORGANIZATION*" -o -name "*REORGANISATIE*" -o -name "*reorganization*" \) 2>/dev/null); do
    # Skip ons eigen script en INDEX.md
    if [[ "$file" == *"archiveer"* ]] || [[ "$file" == *"reorganize"* ]] || [[ "$file" == "docs/INDEX.md" ]]; then
        continue
    fi
    # Skip als het al in archief staat
    if [[ "$file" == docs/archief/* ]]; then
        continue
    fi

    filename=$(basename "$file")

    if [ "$DRY_RUN" = true ]; then
        log_action "Would move: $file → docs/archief/$filename"
    else
        mv "$file" "docs/archief/$filename"
        log_action "Moved: $file → docs/archief/$filename"
    fi
    ((ARCHIVED++))
done

# 3. Hele directories die we niet meer nodig hebben
OBSOLETE_DIRS=(
    "docs/evaluations"
    "docs/reviews"
    "docs/modules"
    "docs/analyse"
    "docs/analysis"
)

for dir in "${OBSOLETE_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        # Verplaats alle files in die directory naar archief
        for file in "$dir"/*; do
            if [ -f "$file" ]; then
                filename=$(basename "$file")

                if [ "$DRY_RUN" = true ]; then
                    log_action "Would move: $file → docs/archief/$filename"
                else
                    mv "$file" "docs/archief/$filename"
                    log_action "Moved: $file → docs/archief/$filename"
                fi
                ((ARCHIVED++))
            fi
        done

        # Verwijder lege directory
        if [ "$DRY_RUN" = true ]; then
            log_action "Would remove empty dir: $dir"
        else
            rmdir "$dir" 2>/dev/null && log_action "Removed empty dir: $dir"
        fi
    fi
done

# 4. Specifieke oude workflows (behoud alleen de 2 actieve)
KEEP_WORKFLOWS=(
    "validation_orchestrator_rollout.md"
    "test-categorie-workflow.md"
)

if [ -d "docs/workflows" ]; then
    for file in docs/workflows/*.md; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")

            # Check of we dit moeten behouden
            keep=false
            for keeper in "${KEEP_WORKFLOWS[@]}"; do
                if [[ "$filename" == "$keeper" ]]; then
                    keep=true
                    break
                fi
            done

            if [ "$keep" = false ]; then
                if [ "$DRY_RUN" = true ]; then
                    log_action "Would move: $file → docs/archief/$filename"
                else
                    mv "$file" "docs/archief/$filename"
                    log_action "Moved: $file → docs/archief/$filename"
                fi
                ((ARCHIVED++))
            fi
        fi
    done
fi

echo ""
echo -e "${GREEN}=== SAMENVATTING ===${NC}"
echo ""
echo "📊 Aantal gearchiveerde documenten: $ARCHIVED"
echo "📁 Archief locatie: docs/archief/"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}⚠️  DIT WAS EEN DRY-RUN${NC}"
    echo "Geen wijzigingen doorgevoerd."
    echo ""
    echo "Om echt uit te voeren:"
    echo -e "  ${GREEN}bash $0 --execute${NC}"
else
    echo -e "${GREEN}✅ ARCHIVERING VOLTOOID${NC}"
    echo "Alle oude documenten staan nu in docs/archief/"
fi

echo ""
echo "============================================================================"
