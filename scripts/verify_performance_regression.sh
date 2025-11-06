#!/bin/bash
# Performance Regression Verification Script
# Checks for symptoms of DEF-110 rerun cascade issue

LOG_FILE="${1:-logs/app.log}"

echo "=== Performance Regression Verification ==="
echo "Log file: $LOG_FILE"
echo ""

# Check 1: RuleCache loading count
echo "1. RuleCache Load Count (expected: 1, issue: 4+)"
RULE_LOADS=$(grep -c "Loading.*regel files" "$LOG_FILE" 2>/dev/null || echo "0")
echo "   Result: $RULE_LOADS loads"
if [ "$RULE_LOADS" -gt 1 ]; then
    echo "   ❌ FAIL: Multiple loads detected (expected 1)"
else
    echo "   ✅ PASS: Single load as expected"
fi
echo ""

# Check 2: Context cleaning count
echo "2. Context Cleaning Count (expected: 1, issue: 4+)"
CLEAN_COUNT=$(grep -c "Context state cleaned" "$LOG_FILE" 2>/dev/null || echo "0")
echo "   Result: $CLEAN_COUNT cleanings"
if [ "$CLEAN_COUNT" -gt 1 ]; then
    echo "   ❌ FAIL: Multiple cleanings detected (rerun cascade)"
else
    echo "   ✅ PASS: Single cleaning as expected"
fi
echo ""

# Check 3: Render regression
echo "3. Render Time Regression (expected: <200ms, issue: >10000ms)"
MAX_RENDER=$(grep "streamlit_render_ms" "$LOG_FILE" | grep -v "is_heavy_operation.*true" | grep -oE '[0-9]+\.[0-9]+' | sort -n | tail -1)
if [ -n "$MAX_RENDER" ]; then
    echo "   Result: ${MAX_RENDER}ms max render time"
    if (( $(echo "$MAX_RENDER > 200" | bc -l) )); then
        echo "   ❌ FAIL: Render time exceeds 200ms threshold"
    else
        echo "   ✅ PASS: Render time within normal range"
    fi
else
    echo "   ⚠️  SKIP: No render metrics found in log"
fi
echo ""

# Check 4: Force clean warnings
echo "4. Force Clean Warnings (expected: 0 in render(), OK in Edit Tab)"
FORCE_CLEAN=$(grep -c "FORCE CLEAN requested" "$LOG_FILE" 2>/dev/null || echo "0")
echo "   Result: $FORCE_CLEAN force clean calls"
if [ "$FORCE_CLEAN" -gt 10 ]; then
    echo "   ❌ FAIL: Too many force cleans (likely in render())"
elif [ "$FORCE_CLEAN" -gt 0 ]; then
    echo "   ⚠️  WARN: Some force cleans detected (check if definition switches)"
else
    echo "   ✅ PASS: No unexpected force cleans"
fi
echo ""

# Check 5: ServiceContainer init count
echo "5. ServiceContainer Init Count (expected: 1, issue: 2+)"
CONTAINER_INIT=$(grep -c "ServiceContainer instance initialized" "$LOG_FILE" 2>/dev/null || echo "0")
echo "   Result: $CONTAINER_INIT initializations"
if [ "$CONTAINER_INIT" -gt 1 ]; then
    echo "   ❌ FAIL: Multiple container initializations"
else
    echo "   ✅ PASS: Single container initialization"
fi
echo ""

# Summary
echo "=== Summary ==="
FAIL_COUNT=0
PASS_COUNT=0

[ "$RULE_LOADS" -gt 1 ] && ((FAIL_COUNT++)) || ((PASS_COUNT++))
[ "$CLEAN_COUNT" -gt 1 ] && ((FAIL_COUNT++)) || ((PASS_COUNT++))
[ -n "$MAX_RENDER" ] && [ $(echo "$MAX_RENDER > 200" | bc -l) -eq 1 ] && ((FAIL_COUNT++)) || ((PASS_COUNT++))
[ "$FORCE_CLEAN" -gt 10 ] && ((FAIL_COUNT++)) || ((PASS_COUNT++))
[ "$CONTAINER_INIT" -gt 1 ] && ((FAIL_COUNT++)) || ((PASS_COUNT++))

echo "Passed: $PASS_COUNT"
echo "Failed: $FAIL_COUNT"

if [ "$FAIL_COUNT" -gt 0 ]; then
    echo ""
    echo "❌ REGRESSION DETECTED"
    echo "See docs/analyses/PERFORMANCE_REGRESSION_2025-11-06.md for details"
    exit 1
else
    echo ""
    echo "✅ NO REGRESSION DETECTED"
    exit 0
fi
