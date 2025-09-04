#!/bin/bash

# Archive redundant CFR and PER-007 documentation
# This script consolidates overlapping documentation into historical archive

ARCHIVE_DIR="archief/2025-09-04-cfr-consolidation"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "=== Archiving Redundant CFR/PER-007 Documentation ==="
echo "Archive location: $ARCHIVE_DIR"
echo "Timestamp: $TIMESTAMP"

# Create archive directory
mkdir -p "$ARCHIVE_DIR"

# Create archive manifest
cat > "$ARCHIVE_DIR/ARCHIVE_MANIFEST.md" << EOF
# CFR/PER-007 Documentation Archive

**Archived:** $(date +"%Y-%m-%d %H:%M:%S")
**Reason:** Consolidated into single refactoring plan
**Superseded by:**
- CFR-CONSOLIDATED-REFACTOR-PLAN.md
- ADR-016-context-flow-consolidated.md

## Archived Documents

### PER-007 Documents
- PER-007-architectural-assessment.md
- PER-007-implementation-guide.md
- ADR-PER-007-context-flow-fix.md
- ../testing/PER-007-test-scenarios.md

### CFR Documents
- CFR-SOLUTION-OVERVIEW.md
- CFR-MIGRATION-STRATEGY.md
- EA-CFR.md
- SA-CFR.md
- TA-CFR.md
- ADR-CFR-001-context-flow-refactoring.md
- ../CFR-IMMEDIATE-WORKAROUNDS.md
- ../CFR-DOCUMENTATION-VALIDATION-REPORT.md

## Note
These documents are preserved for historical reference only.
Do not use for current implementation guidance.
EOF

# Archive PER-007 documents
echo "Archiving PER-007 documents..."
[ -f "PER-007-architectural-assessment.md" ] && mv "PER-007-architectural-assessment.md" "$ARCHIVE_DIR/"
[ -f "PER-007-implementation-guide.md" ] && mv "PER-007-implementation-guide.md" "$ARCHIVE_DIR/"
[ -f "beslissingen/ADR-PER-007-context-flow-fix.md" ] && mv "beslissingen/ADR-PER-007-context-flow-fix.md" "$ARCHIVE_DIR/"
[ -f "../testing/PER-007-test-scenarios.md" ] && mv "../testing/PER-007-test-scenarios.md" "$ARCHIVE_DIR/"

# Archive CFR documents
echo "Archiving CFR documents..."
[ -f "CFR-SOLUTION-OVERVIEW.md" ] && mv "CFR-SOLUTION-OVERVIEW.md" "$ARCHIVE_DIR/"
[ -f "CFR-MIGRATION-STRATEGY.md" ] && mv "CFR-MIGRATION-STRATEGY.md" "$ARCHIVE_DIR/"
[ -f "EA-CFR.md" ] && mv "EA-CFR.md" "$ARCHIVE_DIR/"
[ -f "SA-CFR.md" ] && mv "SA-CFR.md" "$ARCHIVE_DIR/"
[ -f "TA-CFR.md" ] && mv "TA-CFR.md" "$ARCHIVE_DIR/"
[ -f "beslissingen/ADR-CFR-001-context-flow-refactoring.md" ] && mv "beslissingen/ADR-CFR-001-context-flow-refactoring.md" "$ARCHIVE_DIR/"
[ -f "../CFR-IMMEDIATE-WORKAROUNDS.md" ] && mv "../CFR-IMMEDIATE-WORKAROUNDS.md" "$ARCHIVE_DIR/"
[ -f "../CFR-DOCUMENTATION-VALIDATION-REPORT.md" ] && mv "../CFR-DOCUMENTATION-VALIDATION-REPORT.md" "$ARCHIVE_DIR/"

# Update SOLUTION_ARCHITECTURE.md to reference new consolidated plan
echo "Updating SOLUTION_ARCHITECTURE.md references..."
if [ -f "SOLUTION_ARCHITECTURE.md" ]; then
    sed -i.bak \
        -e 's/PER-007[^)]*/CFR-CONSOLIDATED-REFACTOR-PLAN.md/g' \
        -e 's/CFR-SOLUTION-OVERVIEW/CFR-CONSOLIDATED-REFACTOR-PLAN/g' \
        -e 's/ADR-CFR-001/ADR-016/g' \
        -e 's/ADR-PER-007/ADR-016/g' \
        SOLUTION_ARCHITECTURE.md
    echo "Updated SOLUTION_ARCHITECTURE.md"
fi

# Create redirect notice files
echo "Creating redirect notices..."

cat > "PER-007-REDIRECT.md" << EOF
# Document Moved

This document has been consolidated into:
- [CFR-CONSOLIDATED-REFACTOR-PLAN.md](CFR-CONSOLIDATED-REFACTOR-PLAN.md)
- [ADR-016-context-flow-consolidated.md](beslissingen/ADR-016-context-flow-consolidated.md)

Historical version available in: $ARCHIVE_DIR/
EOF

cat > "CFR-REDIRECT.md" << EOF
# Document Moved

All CFR documentation has been consolidated into:
- [CFR-CONSOLIDATED-REFACTOR-PLAN.md](CFR-CONSOLIDATED-REFACTOR-PLAN.md)
- [ADR-016-context-flow-consolidated.md](beslissingen/ADR-016-context-flow-consolidated.md)

Historical versions available in: $ARCHIVE_DIR/
EOF

echo "=== Archive Complete ==="
echo "Next steps:"
echo "1. Review consolidated documents"
echo "2. Update any remaining references"
echo "3. Commit changes with message: 'refactor: consolidate CFR/PER-007 documentation'"
echo ""
echo "Documents consolidated into:"
echo "  - CFR-CONSOLIDATED-REFACTOR-PLAN.md (main implementation guide)"
echo "  - ADR-016-context-flow-consolidated.md (architectural decision)"
