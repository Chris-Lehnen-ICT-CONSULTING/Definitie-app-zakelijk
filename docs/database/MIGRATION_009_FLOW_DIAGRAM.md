# Migration 009 - Flow Diagram & Decision Tree

## Migration Flow Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    CURRENT STATE                             │
│  (Migration 008 Applied - UNIQUE INDEX Exists)              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ User Request: "Allow duplicate definitions"
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                 DECISION POINT                               │
│  Should we remove UNIQUE INDEX constraint?                   │
│                                                              │
│  Factors:                                                    │
│  ✓ Schema.sql line 81: "temporarily disabled"               │
│  ✓ Python code already handles duplicates                   │
│  ✓ Import strategy needs flexibility                        │
│  ✓ Fully reversible (just an INDEX)                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Decision: YES - Remove constraint
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              MIGRATION 009 DESIGN                            │
│                                                              │
│  1. Design document written       ✓                         │
│  2. Migration SQL created         ✓                         │
│  3. Rollback SQL created          ✓                         │
│  4. Tests written                 ✓                         │
│  5. Cleanup script verified       ✓                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Ready for execution
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│           EXECUTION: PRE-FLIGHT                              │
│                                                              │
│  1. Backup database               □                         │
│  2. Run pre-migration tests       □                         │
│  3. Verify UNIQUE INDEX exists    □                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ All checks pass
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│         EXECUTION: APPLY MIGRATION                           │
│                                                              │
│  SQL: DROP INDEX IF EXISTS idx_definities_unique_full;       │
│                                                              │
│  Duration: < 1 second                                        │
│  Risk: LOW (reversible)                                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Migration applied
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│         EXECUTION: POST-FLIGHT                               │
│                                                              │
│  1. Verify INDEX removed          □                         │
│  2. Run post-migration tests      □                         │
│  3. Run regression tests          □                         │
│  4. Smoke test via UI             □                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ All tests pass
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    NEW STATE                                 │
│  (Migration 009 Applied - UNIQUE INDEX Removed)              │
│                                                              │
│  Behavior:                                                   │
│  • Duplicates CAN be created (with allow_duplicate=True)     │
│  • Python check STILL warns users                           │
│  • UI shows warning dialog (user can override)              │
└─────────────────────────────────────────────────────────────┘
```

---

## Decision Tree: Handling Duplicate Definitions

### After Migration 009

```
User creates definition
         │
         ▼
    ┌─────────┐
    │ Python  │
    │ Checks  │
    │find_dup │
    └────┬────┘
         │
         ▼
    Duplicates? ──NO──▶ Create definition
         │                    │
        YES                   ▼
         │              SUCCESS ✓
         ▼
    ┌─────────────────────────┐
    │  UI Shows Warning        │
    │  "Similar def exists"    │
    │                          │
    │  Options:                │
    │  [Cancel] [Create Anyway]│
    └───────┬─────────┬────────┘
            │         │
       User │         │ User
      clicks│         │clicks
      Cancel│         │Create
            │         │Anyway
            ▼         ▼
         CANCEL   Set allow_duplicate=True
            │         │
            ▼         ▼
      No action   Create definition
                       │
                       ▼
                  SUCCESS ✓
                (duplicate created)
```

### Before Migration 009 (Current State)

```
User creates definition
         │
         ▼
    ┌─────────┐
    │Database │
    │ UNIQUE  │
    │  Check  │
    └────┬────┘
         │
         ▼
    Duplicates? ──NO──▶ Create definition
         │                    │
        YES                   ▼
         │              SUCCESS ✓
         ▼
    DATABASE ERROR
    (UNIQUE constraint failed)
         │
         ▼
    UI shows generic error
    (user confused)
```

---

## Error Handling Flow

### Scenario 1: Normal Duplicate Detection (After Migration)

```
create_definitie(record, allow_duplicate=False)
    │
    ▼
Python: find_duplicates()
    │
    ▼
Duplicates found? ──NO──▶ INSERT INTO definities
    │                           │
   YES                          ▼
    │                      SUCCESS
    ▼
raise ValueError("bestaat al")
    │
    ▼
Caught by UI → Show warning dialog
    │
    ▼
User confirms → Retry with allow_duplicate=True
    │
    ▼
INSERT INTO definities (no Python check)
    │
    ▼
SUCCESS (duplicate created)
```

### Scenario 2: Force Duplicate (After Migration)

```
create_definitie(record, allow_duplicate=True)
    │
    ▼
Skip find_duplicates() check
    │
    ▼
INSERT INTO definities directly
    │
    ▼
SUCCESS (duplicate created)
    │
    ▼
Log: "allow_duplicate=True used"
```

### Scenario 3: Rollback Failure (Duplicates Exist)

```
Apply rollback migration
    │
    ▼
CREATE UNIQUE INDEX ...
    │
    ▼
Duplicates exist in table?
    │
    ├─NO──▶ INDEX created
    │           │
    │           ▼
    │       SUCCESS
    │
   YES
    │
    ▼
sqlite3.IntegrityError
    │
    ▼
ERROR: "UNIQUE constraint failed"
    │
    ▼
Must clean up duplicates first:
    │
    ▼
python scripts/cleanup_duplicates.py --execute
    │
    ▼
Retry rollback migration
    │
    ▼
SUCCESS
```

---

## Testing Flow

### Pre-Migration Tests

```
test_unique_index_exists()
    │
    ▼
Query: SELECT name FROM sqlite_master WHERE name='idx_definities_unique_full'
    │
    ▼
Result should be: 'idx_definities_unique_full'
    │
    ▼
✓ PASS: INDEX exists

test_duplicate_blocked_by_database()
    │
    ▼
Create definition 1 → SUCCESS
    │
    ▼
Create definition 2 (duplicate) → ValueError
    │
    ▼
✓ PASS: Duplicate blocked
```

### Post-Migration Tests

```
test_unique_index_removed()
    │
    ▼
Apply migration 009
    │
    ▼
Query: SELECT COUNT(*) FROM sqlite_master WHERE name='idx_definities_unique_full'
    │
    ▼
Result should be: 0
    │
    ▼
✓ PASS: INDEX removed

test_duplicate_allowed_with_flag()
    │
    ▼
Create definition 1 → SUCCESS
    │
    ▼
Create definition 2 (allow_duplicate=True) → SUCCESS
    │
    ▼
Verify both exist → BOTH FOUND
    │
    ▼
✓ PASS: Duplicate allowed

test_python_guard_still_blocks_without_flag()
    │
    ▼
Create definition 1 → SUCCESS
    │
    ▼
Create definition 2 (allow_duplicate=False) → ValueError
    │
    ▼
✓ PASS: Python guard works
```

---

## Rollback Decision Tree

```
Need to rollback?
    │
    ├─NO──▶ Continue monitoring
    │
   YES
    │
    ▼
Duplicates exist?
    │
    ├─NO──▶ Direct rollback
    │           │
    │           ▼
    │       Restore backup OR
    │       Apply rollback migration
    │           │
    │           ▼
    │       SUCCESS
    │
   YES
    │
    ▼
How many duplicates?
    │
    ├─Few (<5)──▶ Manual cleanup
    │                 │
    │                 ▼
    │             Archive duplicates manually
    │                 │
    │                 ▼
    │             Apply rollback migration
    │                 │
    │                 ▼
    │             SUCCESS
    │
    └─Many (>5)──▶ Automated cleanup
                      │
                      ▼
                  python scripts/cleanup_duplicates.py --preview
                      │
                      ▼
                  python scripts/cleanup_duplicates.py --execute
                      │
                      ▼
                  Apply rollback migration
                      │
                      ▼
                  SUCCESS
```

---

## Monitoring Flow (Post-Migration)

```
Day 1: Immediate Check
    │
    ▼
Application logs OK?
    │
    ├─NO──▶ Investigate errors
    │           │
    │           ▼
    │       Consider rollback
    │
   YES
    │
    ▼
Duplicate creation works?
    │
    ├─NO──▶ Check Python code
    │           │
    │           ▼
    │       Fix + Deploy
    │
   YES
    │
    ▼
Week 1: Daily Monitoring
    │
    ▼
Count duplicates:
grep "allow_duplicate=True" logs/app.log
    │
    ▼
Duplicate rate?
    │
    ├─<5%──▶ ✓ NORMAL
    │
    ├─5-10%──▶ ⚠ MONITOR CLOSELY
    │               │
    │               ▼
    │           Review usage patterns
    │
    └─>10%──▶ ❌ INVESTIGATE
                    │
                    ▼
                UI confusion?
                    │
                    ├─YES──▶ Improve UI warnings
                    │
                    └─NO──▶ Check for bugs
                                │
                                ▼
                            Fix + Deploy OR Rollback
```

---

## State Transition Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                BEFORE MIGRATION 008                          │
│  Constraint: NONE (comment in schema.sql only)               │
│  Behavior: Duplicates allowed (unintended)                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ Migration 008 (2025-10-31)
                        │ ADD UNIQUE INDEX
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              AFTER MIGRATION 008 (Current)                   │
│  Constraint: UNIQUE INDEX on 5 fields                        │
│  Behavior: Duplicates blocked by database                    │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ Migration 009 (2025-11-10)
                        │ DROP UNIQUE INDEX
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              AFTER MIGRATION 009 (New)                       │
│  Constraint: NONE (application-level only)                   │
│  Behavior: Duplicates allowed (with user confirmation)       │
└─────────────────────────────────────────────────────────────┘
                        │
                        │ Optional: Rollback
                        │ (if needed)
                        ▼
┌─────────────────────────────────────────────────────────────┐
│           AFTER ROLLBACK (Back to Migration 008)             │
│  Constraint: UNIQUE INDEX restored                           │
│  Behavior: Duplicates blocked by database                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Symbols Legend

- ✓ Complete / Success
- □ Pending / To Do
- ⚠ Warning / Monitor
- ❌ Error / Failed
- ▶ Action / Decision
- │ Flow continues
- ┌─┐ Process box
- └─┘ Process box

---

**END OF FLOW DIAGRAM**
