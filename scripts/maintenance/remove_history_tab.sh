#!/bin/bash
# History Tab Removal Script - Safe and Atomic Operation
# Created: $(date +"%Y-%m-%d %H:%M:%S")

set -e  # Exit on any error
set -u  # Exit on undefined variable
set -o pipefail  # Propagate pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script configuration
PROJECT_ROOT="/Users/chrislehnen/Projecten/Definitie-app"
BACKUP_DIR="/tmp/history_tab_removal_$(date +%Y%m%d_%H%M%S)"
ROLLBACK_SCRIPT="${BACKUP_DIR}/rollback.sh"

echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   HISTORY TAB REMOVAL - Safe Removal Strategy${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""

# Phase 1: PREPARATION
echo -e "${YELLOW}▶ Phase 1: Preparation${NC}"

# Create backup directory
echo "  Creating backup directory: ${BACKUP_DIR}"
mkdir -p "${BACKUP_DIR}"

# Check current state
echo "  Checking current references..."
cd "${PROJECT_ROOT}"

# Count references
REF_COUNT=$(grep -r "HistoryTab\|history_tab" src/ --include="*.py" 2>/dev/null | wc -l || echo "0")
echo "  Found ${REF_COUNT} references to remove"

# Backup current state
echo "  Creating backups..."
cp src/ui/tabbed_interface.py "${BACKUP_DIR}/tabbed_interface.py.backup"

# Check if history_tab.py.backup exists and preserve it
if [ -f "src/ui/components/history_tab.py.backup" ]; then
    echo "  Preserving existing history_tab.py.backup"
    cp src/ui/components/history_tab.py.backup "${BACKUP_DIR}/history_tab.py.backup"
fi

# Create rollback script
echo "  Creating rollback script..."
cat > "${ROLLBACK_SCRIPT}" << 'ROLLBACK'
#!/bin/bash
# Rollback script for History Tab removal

echo "Rolling back History Tab removal..."

# Restore files
cp BACKUP_DIR/tabbed_interface.py.backup PROJECT_ROOT/src/ui/tabbed_interface.py

# Restore history tab backup if it existed
if [ -f "BACKUP_DIR/history_tab.py.backup" ]; then
    cp BACKUP_DIR/history_tab.py.backup PROJECT_ROOT/src/ui/components/history_tab.py.backup
fi

# Clear Streamlit cache
streamlit cache clear 2>/dev/null || true

echo "Rollback complete! Please restart the application."
ROLLBACK

# Replace placeholders in rollback script
sed -i.bak "s|BACKUP_DIR|${BACKUP_DIR}|g" "${ROLLBACK_SCRIPT}"
sed -i.bak "s|PROJECT_ROOT|${PROJECT_ROOT}|g" "${ROLLBACK_SCRIPT}"
rm "${ROLLBACK_SCRIPT}.bak"
chmod +x "${ROLLBACK_SCRIPT}"

echo -e "${GREEN}  ✓ Preparation complete${NC}"
echo ""

# Phase 2: CODE MODIFICATIONS
echo -e "${YELLOW}▶ Phase 2: Code Modifications${NC}"

# Create Python script for safe modifications
cat > "${BACKUP_DIR}/modify_code.py" << 'PYTHON_SCRIPT'
#!/usr/bin/env python3
"""Safe removal of History Tab references from tabbed_interface.py"""

import sys
import re
from pathlib import Path

def remove_history_tab_references(file_path):
    """Remove all History Tab references from the file"""

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.splitlines()

    # Track modifications
    modifications = []
    new_lines = []
    skip_next = False

    for i, line in enumerate(lines):
        line_num = i + 1

        # Skip import line
        if 'from ui.components.history_tab import HistoryTab' in line:
            modifications.append(f"Line {line_num}: Removed HistoryTab import")
            continue

        # Skip initialization line
        if 'self.history_tab = HistoryTab' in line:
            modifications.append(f"Line {line_num}: Removed HistoryTab initialization")
            continue

        # Skip history config block (multi-line)
        if '"history":' in line:
            modifications.append(f"Line {line_num}-{line_num+4}: Removed history tab config")
            # Skip this line and next 4 lines (the config block)
            skip_count = 4
            for j in range(skip_count):
                if i + j + 1 < len(lines):
                    # Don't add these lines
                    pass
            # Skip ahead
            for _ in range(skip_count):
                if i + 1 < len(lines):
                    lines[i + 1] = None  # Mark for skipping
            continue

        # Skip marked lines
        if line is None:
            continue

        # Skip history tab render block
        if 'elif tab_key == "history":' in line:
            modifications.append(f"Line {line_num}-{line_num+1}: Removed history tab render")
            # Skip this line and next line
            if i + 1 < len(lines):
                lines[i + 1] = None  # Mark next line for skipping
            continue

        # Add line if not marked for deletion
        new_lines.append(line)

    # Write modified content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
        if new_lines and not new_lines[-1].endswith('\n'):
            f.write('\n')

    return modifications

if __name__ == "__main__":
    file_path = Path("PROJECT_ROOT/src/ui/tabbed_interface.py")

    print("Modifying tabbed_interface.py...")

    try:
        modifications = remove_history_tab_references(file_path)

        print(f"Successfully applied {len(modifications)} modifications:")
        for mod in modifications:
            print(f"  - {mod}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
PYTHON_SCRIPT

# Replace placeholder
sed -i.bak "s|PROJECT_ROOT|${PROJECT_ROOT}|g" "${BACKUP_DIR}/modify_code.py"
rm "${BACKUP_DIR}/modify_code.py.bak"
chmod +x "${BACKUP_DIR}/modify_code.py"

# Run the Python modification script
echo "  Removing History Tab references from tabbed_interface.py..."
python3 "${BACKUP_DIR}/modify_code.py"

echo -e "${GREEN}  ✓ Code modifications complete${NC}"
echo ""

# Phase 3: CLEANUP
echo -e "${YELLOW}▶ Phase 3: Cleanup${NC}"

# Remove the backup file if it exists
if [ -f "src/ui/components/history_tab.py.backup" ]; then
    echo "  Removing history_tab.py.backup..."
    rm -f src/ui/components/history_tab.py.backup
fi

# Clean Python cache files
echo "  Cleaning Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true

# Clear Streamlit cache
echo "  Clearing Streamlit cache..."
streamlit cache clear 2>/dev/null || true

echo -e "${GREEN}  ✓ Cleanup complete${NC}"
echo ""

# Phase 4: VERIFICATION
echo -e "${YELLOW}▶ Phase 4: Verification${NC}"

# Check for remaining references
echo "  Checking for remaining references..."
REMAINING=$(grep -r "HistoryTab\|history_tab\|\"history\":" src/ --include="*.py" 2>/dev/null | grep -v "history_entry\|history_file\|rate_limit_history" | wc -l || echo "0")

if [ "$REMAINING" -eq "0" ]; then
    echo -e "${GREEN}  ✓ No History Tab references found${NC}"
else
    echo -e "${RED}  ⚠ Warning: Found ${REMAINING} possible remaining references${NC}"
    echo "  Run the following command to investigate:"
    echo "  grep -r 'HistoryTab\\|history_tab\\|\"history\":' src/ --include='*.py'"
fi

# Test Python syntax
echo "  Verifying Python syntax..."
python3 -m py_compile src/ui/tabbed_interface.py 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}  ✓ Python syntax valid${NC}"
else
    echo -e "${RED}  ✗ Python syntax error detected!${NC}"
    echo "  Run rollback script: ${ROLLBACK_SCRIPT}"
    exit 1
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   REMOVAL COMPLETE${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo "Summary:"
echo "  • Removed History Tab from tabbed_interface.py"
echo "  • Cleaned up cache files"
echo "  • Created backup at: ${BACKUP_DIR}"
echo "  • Rollback script: ${ROLLBACK_SCRIPT}"
echo ""
echo "Next steps:"
echo "  1. Start the application: streamlit run src/main.py"
echo "  2. Verify all tabs work correctly"
echo "  3. If issues occur, run: ${ROLLBACK_SCRIPT}"
echo ""