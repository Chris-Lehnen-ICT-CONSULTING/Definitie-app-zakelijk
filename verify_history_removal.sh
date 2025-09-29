#!/bin/bash
#
# Quick verification script for History Tab removal
# Run this from project root after removing History tab
#

set -e

echo "🔍 Starting History Tab Removal Verification..."
echo "============================================="
echo ""

# Make scripts executable
chmod +x scripts/testing/verify_history_removal.sh
chmod +x scripts/testing/verify_history_removal.py

# Check current state
echo "📋 Checking current state..."
if grep -q "from ui.components.history_tab import HistoryTab" src/ui/tabbed_interface.py 2>/dev/null; then
    echo "⚠️  WARNING: HistoryTab import still present!"
    echo "   Please remove the History tab first."
    echo ""
    echo "   Required changes in src/ui/tabbed_interface.py:"
    echo "   1. Remove: from ui.components.history_tab import HistoryTab"
    echo "   2. Remove: self.history_tab = HistoryTab(self.repository)"
    echo "   3. Remove: 'history' from self.tab_config"
    echo "   4. Remove: elif tab_key == 'history': self.history_tab.render()"
    echo ""
    exit 1
else
    echo "✅ HistoryTab import not found (good!)"
fi

# Run Python verification
echo ""
echo "🐍 Running Python verification..."
python scripts/testing/verify_history_removal.py --verify

# Run test suite if it exists
if [ -f "tests/test_history_removal.py" ]; then
    echo ""
    echo "🧪 Running test suite..."
    pytest tests/test_history_removal.py -v --tb=short || true
fi

# Summary
echo ""
echo "============================================="
echo "📊 VERIFICATION COMPLETE"
echo "============================================="
echo ""
echo "✅ Automated verification complete!"
echo ""
echo "📝 NEXT STEPS:"
echo "1. Review the verification report above"
echo "2. Start the application: streamlit run src/main.py"
echo "3. Complete manual UI testing:"
echo "   - Verify all tabs work"
echo "   - Confirm NO History tab visible"
echo "   - Check for console errors"
echo ""
echo "📄 Full documentation: docs/testing/HISTORY_REMOVAL_VERIFICATION.md"
echo ""