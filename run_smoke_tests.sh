#!/bin/bash
# Quick smoke test runner for V2 validation

echo "🔥 Running Validation V2 Smoke Tests..."
echo "=================================="

# Set DEV_MODE for testing
export DEV_MODE=true

# Run the smoke test
python -m pytest tests/smoke/test_validation_v2_smoke.py -v --tb=short

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All smoke tests passed!"
else
    echo ""
    echo "❌ Some smoke tests failed"
    exit 1
fi
