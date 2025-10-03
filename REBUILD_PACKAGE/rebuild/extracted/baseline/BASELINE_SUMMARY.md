# Baseline Data Export Summary

**Export Date:** 2025-10-02  
**Source Database:** data/definities.db  
**Export Location:** rebuild/extracted/baseline/

## Exported Data

### Definitions (definities)
- **Count:** 42 definitions
- **File:** baseline_42_definitions.json
- **Status Distribution:**
  - draft: 39
  - review: 2  
  - approved: 1

### Key Statistics
- **Average version:** 1.2
- **Source types:**
  - imported: 37
  - generated: 5
- **Categories:**
  - type: 38
  - proces: 3
  - resultaat: 1

## Usage

This baseline serves as the reference dataset for:
1. Week 1 validation rule extraction
2. Week 4 MVP validation (90%+ pass target)
3. Week 9 production validation (95%+ match)

## Next Steps

1. Create test fixtures from baseline:
   ```bash
   python rebuild/scripts/create_test_fixtures.py
   ```

2. Generate validation test suite:
   ```bash
   # 42 real + 100 synthetic = 142 test cases
   ```

3. Start Week 1 Day 1 extraction
