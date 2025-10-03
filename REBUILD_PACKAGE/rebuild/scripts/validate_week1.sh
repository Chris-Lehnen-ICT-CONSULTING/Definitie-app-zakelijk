#!/bin/bash
echo "=== Week 1 Validation ==="

# Check YAML files
echo "Checking YAML configs..."
yaml_count=$(find config/validation_rules -name "*.yaml" 2>/dev/null | wc -l)
echo "  Found: $yaml_count YAML files"
echo "  Expected: 46"
if [ "$yaml_count" -ge 46 ]; then
    echo "  ✓ PASS"
else
    echo "  ✗ FAIL"
fi

# Check workflows
echo ""
echo "Checking workflows..."
workflow_count=$(ls docs/business-logic/workflows/*.md 2>/dev/null | wc -l)
echo "  Found: $workflow_count workflows"
echo "  Expected: 3+"
if [ "$workflow_count" -ge 3 ]; then
    echo "  ✓ PASS"
else
    echo "  ✗ FAIL"
fi

# Check baseline
echo ""
echo "Checking baseline..."
if [ -f "docs/business-logic/baseline/baseline_42_definitions.json" ]; then
    echo "  ✓ PASS - Baseline file exists"
else
    echo "  ✗ FAIL - Baseline file missing"
fi

echo ""
echo "=== Validation Complete ==="
