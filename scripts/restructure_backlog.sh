#!/bin/bash

# Script om de backlog te herstructureren volgens nieuwe structuur:
# docs/backlog/EPIC-XXX/
#   ├── EPIC-XXX.md
#   ├── User Stories/
#   │   ├── US-XXX/
#   │   │   ├── US-XXX.md
#   │   │   └── bugs/
#   │   │       └── BUG-XXX/
#   │   │           └── BUG-XXX.md

set -e

BACKLOG_DIR="docs/backlog"
NEW_DIR="docs/backlog_new"

echo "🚀 Starting backlog restructure..."

# Maak nieuwe structuur
mkdir -p "$NEW_DIR"

# Lijst van EPICs
EPICS=(
  "EPIC-001:Basis Definitie Generatie"
  "EPIC-002:Kwaliteitstoetsing"
  "EPIC-003:Content Verrijking Web Lookup"
  "EPIC-004:User Interface"
  "EPIC-005:Export Import"
  "EPIC-006:Security Auth"
  "EPIC-007:Performance Scaling"
  "EPIC-009:Advanced Features"
  "EPIC-010:Context Flow Refactoring"
  "EPIC-011:Testing Infrastructure"
  "EPIC-012:Legacy Orchestrator Refactoring"
)

# Maak EPIC directories
for epic_info in "${EPICS[@]}"; do
  epic_id="${epic_info%%:*}"
  epic_name="${epic_info#*:}"
  
  echo "📁 Creating structure for $epic_id..."
  mkdir -p "$NEW_DIR/$epic_id/User Stories"
  
  # Kopieer EPIC file als deze bestaat
  if [ -f "$BACKLOG_DIR/epics/${epic_id}*.md" ]; then
    cp "$BACKLOG_DIR/epics/${epic_id}"*.md "$NEW_DIR/$epic_id/${epic_id}.md" 2>/dev/null || true
  fi
done

echo "📄 Moving User Stories to their EPICs..."

# Verplaats User Stories naar juiste EPIC
for us_file in $BACKLOG_DIR/stories/US-*.md; do
  if [ -f "$us_file" ]; then
    us_name=$(basename "$us_file" .md)
    epic=$(grep "^epic: " "$us_file" | cut -d' ' -f2 | cut -d'-' -f1-2)
    
    # Fix voor EPIC-006 variant
    if [[ "$epic" == "EPIC-006-beveiliging-auth" ]]; then
      epic="EPIC-006"
    fi
    
    if [ -n "$epic" ] && [ -d "$NEW_DIR/$epic" ]; then
      echo "  Moving $us_name to $epic..."
      mkdir -p "$NEW_DIR/$epic/User Stories/$us_name"
      mkdir -p "$NEW_DIR/$epic/User Stories/$us_name/bugs"
      cp "$us_file" "$NEW_DIR/$epic/User Stories/$us_name/${us_name}.md"
    else
      echo "  ⚠️  No epic found for $us_name (epic: $epic)"
      # Voor stories zonder epic, plaats in een UNASSIGNED map
      mkdir -p "$NEW_DIR/UNASSIGNED/User Stories/$us_name"
      mkdir -p "$NEW_DIR/UNASSIGNED/User Stories/$us_name/bugs"
      cp "$us_file" "$NEW_DIR/UNASSIGNED/User Stories/$us_name/${us_name}.md"
    fi
  fi
done

# Kopieer andere belangrijke directories
echo "📋 Copying other important directories..."
cp -r "$BACKLOG_DIR/dashboard" "$NEW_DIR/" 2>/dev/null || true
cp -r "$BACKLOG_DIR/requirements" "$NEW_DIR/" 2>/dev/null || true

# Kopieer index files
cp "$BACKLOG_DIR"/*.md "$NEW_DIR/" 2>/dev/null || true

# Verplaats bugs naar juiste User Stories (indien bekend)
echo "🐛 Organizing bugs..."

# Voor EPIC-010 bugs die we kennen
if [ -d "$BACKLOG_DIR/epics/EPIC-010/bugs" ]; then
  # CFR-BUG-014 hoort bij US-051 (synoniemen/antoniemen)
  if [ -d "$BACKLOG_DIR/epics/EPIC-010/bugs/CFR-BUG-014-synoniemen-antoniemen" ]; then
    mkdir -p "$NEW_DIR/EPIC-010/User Stories/US-051/bugs/CFR-BUG-014"
    cp -r "$BACKLOG_DIR/epics/EPIC-010/bugs/CFR-BUG-014-synoniemen-antoniemen"/* \
       "$NEW_DIR/EPIC-010/User Stories/US-051/bugs/CFR-BUG-014/" 2>/dev/null || true
  fi
  
  # CFR-BUG-015 hoort bij US-014 (web lookup)
  if [ -d "$BACKLOG_DIR/epics/EPIC-010/bugs/CFR-BUG-015-compat-web-lookup-title-attribute" ]; then
    mkdir -p "$NEW_DIR/EPIC-003/User Stories/US-014/bugs/CFR-BUG-015"
    cp -r "$BACKLOG_DIR/epics/EPIC-010/bugs/CFR-BUG-015-compat-web-lookup-title-attribute"/* \
       "$NEW_DIR/EPIC-003/User Stories/US-014/bugs/CFR-BUG-015/" 2>/dev/null || true
  fi
fi

echo "✅ Restructure complete!"
echo ""
echo "New structure created in: $NEW_DIR"
echo "Old structure preserved in: $BACKLOG_DIR"
echo ""
echo "To replace old with new:"
echo "  rm -rf $BACKLOG_DIR"
echo "  mv $NEW_DIR $BACKLOG_DIR"