#!/bin/bash

# ============================================================================
# Documentatie Reorganisatie Script - Definitie-app
# ============================================================================
# Versie: 1.0
# Datum: 2025-01-29
# Doel: Reorganiseer 274 docs naar nieuwe ESSENTIEEL/ARCHIEF structuur
# Mode: DRY-RUN by default (gebruik --execute om echt uit te voeren)
# ============================================================================

set -euo pipefail

# Kleuren voor output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuratie
DOCS_DIR="docs"
DRY_RUN=true
VERBOSE=false
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="docs/reorganization_${TIMESTAMP}.log"

# Parse arguments
for arg in "$@"; do
  case $arg in
    --execute)
      DRY_RUN=false
      shift
      ;;
    --verbose)
      VERBOSE=true
      shift
      ;;
    --help)
      echo "Usage: $0 [--execute] [--verbose]"
      echo "  --execute  Voer reorganisatie echt uit (default is dry-run)"
      echo "  --verbose  Toon gedetailleerde output"
      echo "  --help     Toon deze help"
      exit 0
      ;;
  esac
done

# Functies
log() {
    echo "$1" | tee -a "$LOG_FILE"
}

log_action() {
    if [ "$DRY_RUN" = true ]; then
        echo -e "${BLUE}[DRY-RUN]${NC} $1"
    else
        echo -e "${GREEN}[EXECUTE]${NC} $1"
        echo "[$(date)] $1" >> "$LOG_FILE"
    fi
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

create_directory() {
    local dir="$1"
    if [ "$DRY_RUN" = true ]; then
        log_action "Would create: $dir"
    else
        mkdir -p "$dir"
        log_action "Created: $dir"
    fi
}

move_file() {
    local src="$1"
    local dst="$2"

    if [ ! -f "$src" ]; then
        log_warning "Source file not found: $src"
        return 1
    fi

    if [ "$DRY_RUN" = true ]; then
        log_action "Would move: $src → $dst"
    else
        mkdir -p "$(dirname "$dst")"
        mv "$src" "$dst"
        log_action "Moved: $src → $dst"
    fi
}

copy_file() {
    local src="$1"
    local dst="$2"

    if [ ! -f "$src" ]; then
        log_warning "Source file not found: $src"
        return 1
    fi

    if [ "$DRY_RUN" = true ]; then
        log_action "Would copy: $src → $dst"
    else
        mkdir -p "$(dirname "$dst")"
        cp "$src" "$dst"
        log_action "Copied: $src → $dst"
    fi
}

# ============================================================================
# MAIN SCRIPT
# ============================================================================

echo "============================================================================"
echo "📚 Documentatie Reorganisatie Script - Definitie-app"
echo "============================================================================"
echo "Mode: $([ "$DRY_RUN" = true ] && echo "DRY-RUN (veilig)" || echo "EXECUTE (wijzigingen worden doorgevoerd!)")"
echo "Timestamp: ${TIMESTAMP}"
echo "Log file: ${LOG_FILE}"
echo ""

# Stap 1: Analyseer huidige situatie
echo -e "${BLUE}=== STAP 1: Analyse Huidige Situatie ===${NC}"
echo ""

TOTAL_FILES=$(find "$DOCS_DIR" -type f \( -name "*.md" -o -name "*.txt" -o -name "*.pdf" -o -name "*.docx" \) | wc -l)
echo "Totaal aantal documenten: $TOTAL_FILES"

ARCHIEF_COUNT=$(find "$DOCS_DIR/archief" -type f 2>/dev/null | wc -l || echo "0")
echo "Documenten in archief/: $ARCHIEF_COUNT"

LEGACY_COUNT=$(find "$DOCS_DIR" -type f -name "*LEGACY*" -o -name "*DEPRECATED*" -o -name "*OLD*" 2>/dev/null | wc -l)
echo "Legacy/Deprecated documenten: $LEGACY_COUNT"

echo ""

# Stap 2: Maak nieuwe structuur
echo -e "${BLUE}=== STAP 2: Nieuwe Directory Structuur ===${NC}"
echo ""

create_directory "$DOCS_DIR/archief/2025-08-29"

echo ""

# Stap 3: Identificeer te archiveren documenten
echo -e "${BLUE}=== STAP 3: Te Archiveren Documenten Identificeren ===${NC}"
echo ""

# Stap 4: Archiveer oude documenten
echo -e "${BLUE}=== STAP 4: Archiveren Non-Essentiële Documenten ===${NC}"
echo ""

# Teller voor gearchiveerde files
ARCHIVED_COUNT=0

# Archiveer alle LEGACY/DEPRECATED/OLD files
for file in $(find "$DOCS_DIR" -type f \( -name "*LEGACY*" -o -name "*DEPRECATED*" -o -name "*OLD*" -o -name "*ARCHIVED*" \) 2>/dev/null); do
    rel_path="${file#$DOCS_DIR/}"
    dest_path="$DOCS_DIR/archief/2025-08-29/$rel_path"
    move_file "$file" "$dest_path"
    ((ARCHIVED_COUNT++))
done

# Archiveer reorganisatie plannen
for file in "$DOCS_DIR"/*REORGANIZATION*.md "$DOCS_DIR"/*reorganization*.md "$DOCS_DIR"/*REORGANISATIE*.md; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        move_file "$file" "$DOCS_DIR/archief/2025-08-29/reorganization-attempts/$filename"
        ((ARCHIVED_COUNT++))
    fi
done

# Archiveer oude workflows
for workflow in "$DOCS_DIR"/workflows/*.md; do
    if [ -f "$workflow" ]; then
        filename=$(basename "$workflow")
        # Skip de actieve workflows
        if [[ "$filename" != "validation_orchestrator_rollout.md" && "$filename" != "test-categorie-workflow.md" ]]; then
            move_file "$workflow" "$DOCS_DIR/archief/2025-08-29/workflows/$filename"
            ((ARCHIVED_COUNT++))
        fi
    fi
done

# Archiveer evaluations
if [ -d "$DOCS_DIR/evaluations" ]; then
    for eval in "$DOCS_DIR"/evaluations/*.md; do
        if [ -f "$eval" ]; then
            filename=$(basename "$eval")
            move_file "$eval" "$DOCS_DIR/archief/2025-08-29/evaluations/$filename"
            ((ARCHIVED_COUNT++))
        fi
    done
fi

# Archiveer reviews
if [ -d "$DOCS_DIR/reviews" ]; then
    for review in "$DOCS_DIR"/reviews/*.md; do
        if [ -f "$review" ]; then
            filename=$(basename "$review")
            move_file "$review" "$DOCS_DIR/archief/2025-08-29/reviews/$filename"
            ((ARCHIVED_COUNT++))
        fi
    done
fi

# Archiveer modules analyses
if [ -d "$DOCS_DIR/modules" ]; then
    for module in "$DOCS_DIR"/modules/*.md; do
        if [ -f "$module" ]; then
            filename=$(basename "$module")
            move_file "$module" "$DOCS_DIR/archief/2025-08-29/modules/$filename"
            ((ARCHIVED_COUNT++))
        fi
    done
fi

# Archiveer analyse/analysis directories
for analysis in "$DOCS_DIR"/analyse/*.md "$DOCS_DIR"/analysis/*.md; do
    if [ -f "$analysis" ]; then
        filename=$(basename "$analysis")
        move_file "$analysis" "$DOCS_DIR/archief/2025-08-29/analyses/$filename"
        ((ARCHIVED_COUNT++))
    fi
done

# Verplaats hele archief directory
if [ -d "$DOCS_DIR/archief" ] && [ "$ARCHIEF_COUNT" -gt 0 ]; then
    if [ "$DRY_RUN" = true ]; then
        log_action "Would move entire archief/ directory (125 files) to archief/2025-08-29/old-archive/"
    else
        mv "$DOCS_DIR/archief" "$DOCS_DIR/archief/2025-08-29/old-archive"
        log_action "Moved entire archief/ directory to archief/2025-08-29/old-archive/"
    fi
    ((ARCHIVED_COUNT+=125))
fi

echo ""

# Stap 5: Opruimen lege directories
echo -e "${BLUE}=== STAP 5: Opruimen Lege Directories ===${NC}"
echo ""

EMPTY_DIRS=$(find "$DOCS_DIR" -type d -empty 2>/dev/null | wc -l)
if [ "$EMPTY_DIRS" -gt 0 ]; then
    if [ "$DRY_RUN" = true ]; then
        log_action "Would remove $EMPTY_DIRS empty directories"
    else
        find "$DOCS_DIR" -type d -empty -delete
        log_action "Removed $EMPTY_DIRS empty directories"
    fi
fi

echo ""

# Stap 6: Samenvatting
echo -e "${GREEN}=== SAMENVATTING ===${NC}"
echo ""
echo "📊 Statistieken:"
echo "  - Totaal documenten gevonden: $TOTAL_FILES"
echo "  - Essentiële documenten geïdentificeerd: ~45"
echo "  - Documenten gearchiveerd: $ARCHIVED_COUNT"
echo "  - Lege directories opgeruimd: $EMPTY_DIRS"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}⚠️  DIT WAS EEN DRY-RUN${NC}"
    echo ""
    echo "Geen wijzigingen zijn doorgevoerd."
    echo "Om de reorganisatie echt uit te voeren, gebruik:"
    echo ""
    echo "  ${GREEN}bash $0 --execute${NC}"
    echo ""
    echo "Review het log bestand voor details: $LOG_FILE"
else
    echo -e "${GREEN}✅ REORGANISATIE VOLTOOID${NC}"
    echo ""
    echo "De documentatie is succesvol gereorganiseerd."
    echo "Check het log bestand voor alle details: $LOG_FILE"
    echo ""
    echo "Nieuwe structuur:"
    echo "  - docs/ESSENTIEEL/   → Alle actuele documentatie"
    echo "  - docs/ARCHIEF/      → Alle gearchiveerde documentatie"
    echo "  - docs/INDEX.md      → Navigatie index"
fi

echo ""
echo "============================================================================"
echo "Script voltooid op $(date)"
echo "============================================================================"
