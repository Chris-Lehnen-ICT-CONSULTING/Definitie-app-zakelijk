#!/bin/bash

# ============================================================================
# Documentatie Archivering Script - Definitie-app
# ============================================================================
# Versie: 2.0 (Vereenvoudigd)
# Datum: 2025-08-29
# Doel: Archiveer oude/deprecated docs naar docs/archief/2025-08-29
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
ARCHIVE_DATE="2025-08-29"
DRY_RUN=true
VERBOSE=false
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="docs/archivering_${TIMESTAMP}.log"

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
      echo "  --execute  Voer archivering echt uit (default is dry-run)"
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

    if [ ! -f "$src" ] && [ ! -d "$src" ]; then
        log_warning "Source not found: $src"
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

# ============================================================================
# MAIN SCRIPT
# ============================================================================

echo "============================================================================"
echo "📚 Documentatie Archivering Script - Definitie-app"
echo "============================================================================"
echo "Mode: $([ "$DRY_RUN" = true ] && echo "DRY-RUN (veilig)" || echo "EXECUTE (wijzigingen worden doorgevoerd!)")"
echo "Archive date: ${ARCHIVE_DATE}"
echo "Log file: ${LOG_FILE}"
echo ""

# Stap 1: Analyseer huidige situatie
echo -e "${BLUE}=== STAP 1: Analyse ===${NC}"
echo ""

TOTAL_FILES=$(find "$DOCS_DIR" -type f \( -name "*.md" -o -name "*.txt" -o -name "*.pdf" -o -name "*.docx" \) | wc -l)
echo "Totaal aantal documenten: $TOTAL_FILES"

CURRENT_ARCHIEF=$(find "$DOCS_DIR/archief" -type f 2>/dev/null | wc -l || echo "0")
echo "Documenten in huidige archief/: $CURRENT_ARCHIEF"

LEGACY_COUNT=$(find "$DOCS_DIR" -type f \( -name "*LEGACY*" -o -name "*DEPRECATED*" -o -name "*OLD*" -o -name "*ARCHIVED*" \) 2>/dev/null | wc -l)
echo "Legacy/Deprecated documenten: $LEGACY_COUNT"

REORG_COUNT=$(find "$DOCS_DIR" -type f -name "*REORGANI*" 2>/dev/null | wc -l)
echo "Reorganisatie documenten: $REORG_COUNT"

echo ""

# Stap 2: Maak archief directory
echo -e "${BLUE}=== STAP 2: Archief Directory ===${NC}"
echo ""

create_directory "$DOCS_DIR/archief/$ARCHIVE_DATE"

echo ""

# Stap 3: Identificeer wat te archiveren
echo -e "${BLUE}=== STAP 3: Te Archiveren Documenten ===${NC}"
echo ""

# Lijsten maken van te archiveren items
echo "Categorieën om te archiveren:"
echo "  • Alle LEGACY/DEPRECATED/OLD/ARCHIVED bestanden"
echo "  • Alle reorganisatie plannen"
echo "  • Oude workflows (behalve validation_orchestrator_rollout.md en test-categorie-workflow.md)"
echo "  • Evaluations directory (oude evaluaties)"
echo "  • Reviews directory (afgeronde reviews)"
echo "  • Modules directory (oude analyses)"
echo "  • Analyse/analysis directories"
echo "  • Huidige archief/ directory → archief/$ARCHIVE_DATE/old-archief/"
echo ""

# Stap 4: Archiveer
echo -e "${BLUE}=== STAP 4: Archivering ===${NC}"
echo ""

ARCHIVED_COUNT=0

# Archiveer LEGACY/DEPRECATED/OLD/ARCHIVED files
for file in $(find "$DOCS_DIR" -type f \( -name "*LEGACY*" -o -name "*DEPRECATED*" -o -name "*OLD*" -o -name "*ARCHIVED*" \) 2>/dev/null); do
    rel_path="${file#$DOCS_DIR/}"
    # Skip als het al in archief staat
    if [[ "$rel_path" == archief/* ]]; then
        continue
    fi
    dest_path="$DOCS_DIR/archief/$ARCHIVE_DATE/$rel_path"
    move_file "$file" "$dest_path"
    ((ARCHIVED_COUNT++))
done

# Archiveer reorganisatie plannen
for file in $(find "$DOCS_DIR" -type f \( -name "*REORGANIZATION*" -o -name "*reorganization*" -o -name "*REORGANISATIE*" \) 2>/dev/null); do
    # Skip ons eigen script!
    if [[ "$file" == *"reorganize-docs"* ]]; then
        continue
    fi
    rel_path="${file#$DOCS_DIR/}"
    # Skip als het al in archief staat
    if [[ "$rel_path" == archief/* ]]; then
        continue
    fi
    filename=$(basename "$file")
    move_file "$file" "$DOCS_DIR/archief/$ARCHIVE_DATE/reorganization-attempts/$filename"
    ((ARCHIVED_COUNT++))
done

# Archiveer oude workflows (behoud alleen de 2 actieve)
if [ -d "$DOCS_DIR/workflows" ]; then
    for workflow in "$DOCS_DIR"/workflows/*.md; do
        if [ -f "$workflow" ]; then
            filename=$(basename "$workflow")
            # Skip de actieve workflows
            if [[ "$filename" != "validation_orchestrator_rollout.md" && "$filename" != "test-categorie-workflow.md" ]]; then
                move_file "$workflow" "$DOCS_DIR/archief/$ARCHIVE_DATE/workflows/$filename"
                ((ARCHIVED_COUNT++))
            fi
        fi
    done
fi

# Archiveer evaluations
if [ -d "$DOCS_DIR/evaluations" ]; then
    move_file "$DOCS_DIR/evaluations" "$DOCS_DIR/archief/$ARCHIVE_DATE/evaluations"
    ((ARCHIVED_COUNT+=5)) # Schatting
fi

# Archiveer reviews
if [ -d "$DOCS_DIR/reviews" ]; then
    move_file "$DOCS_DIR/reviews" "$DOCS_DIR/archief/$ARCHIVE_DATE/reviews"
    ((ARCHIVED_COUNT+=8)) # Schatting
fi

# Archiveer modules
if [ -d "$DOCS_DIR/modules" ]; then
    move_file "$DOCS_DIR/modules" "$DOCS_DIR/archief/$ARCHIVE_DATE/modules"
    ((ARCHIVED_COUNT+=9)) # Schatting
fi

# Archiveer analyse/analysis
if [ -d "$DOCS_DIR/analyse" ]; then
    move_file "$DOCS_DIR/analyse" "$DOCS_DIR/archief/$ARCHIVE_DATE/analyse"
    ((ARCHIVED_COUNT+=3)) # Schatting
fi

if [ -d "$DOCS_DIR/analysis" ]; then
    move_file "$DOCS_DIR/analysis" "$DOCS_DIR/archief/$ARCHIVE_DATE/analysis"
fi

# Verplaats huidige archief als die bestaat (niet ons nieuwe archief!)
if [ -d "$DOCS_DIR/archief" ] && [ "$CURRENT_ARCHIEF" -gt 0 ]; then
    # Check of het niet ons nieuwe archief is
    if [ ! -d "$DOCS_DIR/archief/$ARCHIVE_DATE" ] || [ "$DRY_RUN" = true ]; then
        # Verplaats alle subdirectories behalve degene die we net gemaakt hebben
        for item in "$DOCS_DIR/archief"/*; do
            if [ -d "$item" ] && [[ "$(basename "$item")" != "$ARCHIVE_DATE" ]]; then
                basename_item=$(basename "$item")
                move_file "$item" "$DOCS_DIR/archief/$ARCHIVE_DATE/old-archief/$basename_item"
            fi
        done
    fi
fi

echo ""

# Stap 5: Opruimen
echo -e "${BLUE}=== STAP 5: Opruimen ===${NC}"
echo ""

# Tel lege directories
EMPTY_DIRS=$(find "$DOCS_DIR" -type d -empty 2>/dev/null | grep -v archief | wc -l || echo "0")
if [ "$EMPTY_DIRS" -gt 0 ]; then
    if [ "$DRY_RUN" = true ]; then
        log_action "Would remove $EMPTY_DIRS empty directories"
        if [ "$VERBOSE" = true ]; then
            find "$DOCS_DIR" -type d -empty | grep -v archief
        fi
    else
        find "$DOCS_DIR" -type d -empty | grep -v archief | xargs -r rmdir
        log_action "Removed $EMPTY_DIRS empty directories"
    fi
fi

echo ""

# Stap 6: Samenvatting
echo -e "${GREEN}=== SAMENVATTING ===${NC}"
echo ""
echo "📊 Statistieken:"
echo "  - Totaal documenten: $TOTAL_FILES"
echo "  - Gearchiveerd: ~$ARCHIVED_COUNT documenten"
echo "  - Archief locatie: docs/archief/$ARCHIVE_DATE/"
echo "  - Lege directories opgeruimd: $EMPTY_DIRS"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}⚠️  DIT WAS EEN DRY-RUN${NC}"
    echo ""
    echo "Geen wijzigingen zijn doorgevoerd."
    echo "Om de archivering echt uit te voeren, gebruik:"
    echo ""
    echo "  ${GREEN}bash $0 --execute${NC}"
    echo ""
    echo "Review het log bestand voor details: $LOG_FILE"
else
    echo -e "${GREEN}✅ ARCHIVERING VOLTOOID${NC}"
    echo ""
    echo "Oude documenten zijn gearchiveerd naar:"
    echo "  docs/archief/$ARCHIVE_DATE/"
    echo ""
    echo "De actieve documentatie blijft op zijn plek."
    echo "Check het log bestand voor alle details: $LOG_FILE"
fi

echo ""
echo "============================================================================"
echo "Script voltooid op $(date)"
echo "============================================================================"
