# Export Architecture Problem - Visual Diagram

## Current State: Bifurcated Export Paths

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DefinitieRecord (31 fields)                      │
│  Database: data/definities.db - schema.sql defines 31 fields       │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
         ┌──────────▼─────────┐        ┌─────────▼──────────┐
         │  PATH 1: BULK      │        │ PATH 2: SINGLE     │
         │  Import/Export Tab │        │ Generator Tab      │
         └──────────┬─────────┘        └─────────┬──────────┘
                    │                             │
         ┌──────────▼─────────┐        ┌─────────▼──────────────────┐
         │  FormatExporter    │        │  UIComponentsAdapter       │
         │  (UI Component)    │        │  (Service Bridge)          │
         └──────────┬─────────┘        └─────────┬──────────────────┘
                    │                             │
         ┌──────────▼─────────┐        ┌─────────▼──────────────────┐
         │ CUSTOM EXPORT      │        │  ExportService             │
         │ IMPLEMENTATION     │        │  (Service Layer)           │
         └──────────┬─────────┘        └─────────┬──────────────────┘
                    │                             │
         ┌──────────▼─────────┐        ┌─────────▼──────────────────┐
         │  • _to_dataframe() │        │  DataAggregationService    │
         │  • _generate_txt() │        │  + export_txt.py           │
         └──────────┬─────────┘        └─────────┬──────────────────┘
                    │                             │
         ┌──────────▼─────────┐        ┌─────────▼──────────────────┐
         │   8 FIELDS ❌      │        │   15+ FIELDS ✅            │
         │                    │        │                            │
         │ • begrip           │        │ • begrip                   │
         │ • definitie        │        │ • definitie                │
         │ • categorie        │        │ • categorie                │
         │ • org_context      │        │ • org_context              │
         │ • status           │        │ • juridische_context ✅    │
         │ • validation_score │        │ • wettelijke_basis ✅      │
         │ • created_at       │        │ • voorkeursterm ✅         │
         │ • updated_at       │        │ • ufo_categorie ✅         │
         │                    │        │ • validation_issues ✅     │
         │ MISSING 23 FIELDS! │        │ • approved_by/at ✅        │
         │ 74% DATA LOSS      │        │ • voorbeelden ✅           │
         │                    │        │ • synoniemen ✅            │
         │                    │        │ • + many more...           │
         └────────────────────┘        └────────────────────────────┘
              CSV/Excel/JSON                 TXT/JSON/CSV
            (Bulk Operations)              (Single Definition)
```

## Problem Summary

### Architectural Issue: Duplicate Export Implementations

```
ISSUE: Two separate codepaths, no code reuse

FormatExporter                   ExportService
     │                                │
     ├─ Minimal field set             ├─ Comprehensive field set
     ├─ Reimplements TXT export       ├─ Reuses export_txt.py
     ├─ Custom DataFrame logic        ├─ Uses DataAggregationService
     └─ No service layer              └─ Clean architecture
```

### User Impact: "Export is beperkt"

```
USER EXPECTATION:                  ACTUAL RESULT:
┌────────────────┐                ┌────────────────┐
│ Export ALL     │                │ Export SOME    │
│ definition     │      ❌        │ definition     │
│ data from      │   ───────▶     │ data from      │
│ database       │                │ database       │
│                │                │                │
│ 31 fields      │                │ 8 fields       │
│ 100% coverage  │                │ 26% coverage   │
└────────────────┘                └────────────────┘
        │                                │
        │                                │
        ▼                                ▼
  "I need legal context         "Export doesn't have
   and approval data             juridische_context!?"
   in my export"                 - User complaint
```

## Proposed Solution: Unified Export Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DefinitieRecord (31 fields)                      │
│         + NEW: to_export_dict() method (28 user-facing)             │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
         ┌──────────▼─────────┐        ┌─────────▼──────────┐
         │  PATH 1: BULK      │        │ PATH 2: SINGLE     │
         │  Import/Export Tab │        │ Generator Tab      │
         └──────────┬─────────┘        └─────────┬──────────┘
                    │                             │
         ┌──────────▼─────────┐        ┌─────────▼──────────┐
         │  FormatExporter    │        │ UIComponentsAdapter│
         │  REFACTORED ✅     │        │  (unchanged)       │
         └──────────┬─────────┘        └─────────┬──────────┘
                    │                             │
                    └──────────────┬──────────────┘
                                   │
                         ┌─────────▼──────────────────┐
                         │   ExportService            │
                         │   ENHANCED ✅              │
                         │                            │
                         │ + export_definitions_bulk()│
                         └─────────┬──────────────────┘
                                   │
                         ┌─────────▼──────────────────┐
                         │ DataAggregationService     │
                         │ + export_txt.py            │
                         │ + DefinitieRecord methods  │
                         └─────────┬──────────────────┘
                                   │
                         ┌─────────▼──────────────────┐
                         │   28 FIELDS ✅             │
                         │   (All user-facing data)   │
                         │                            │
                         │ Excludes only internal:    │
                         │ • last_exported_at         │
                         │ • export_destinations      │
                         │ • (deprecated fields)      │
                         └────────────────────────────┘
                            TXT/CSV/Excel/JSON
                           (All Export Paths)
```

## Key Changes

### 1. Single Export Authority
```
BEFORE:                          AFTER:
FormatExporter ─┐                FormatExporter ─┐
                ├─ export logic                  │
ExportService ──┘                                ├─▶ ExportService
                                                 │   (SINGLE source)
UIAdapter ──────▶ ExportService  UIAdapter ─────┘
```

### 2. Field Coverage Validation
```
NEW: Automated Test
┌────────────────────────────────┐
│ test_export_field_coverage()   │
│                                │
│ record_fields = 31             │
│ internal_fields = 3            │
│ expected_export = 28           │
│                                │
│ actual_export = count_fields() │
│                                │
│ assert actual == expected ✅   │
└────────────────────────────────┘
```

### 3. Backward Compatibility
```
DefinitieRecord.to_export_dict(mode='full')    → 28 fields
DefinitieRecord.to_export_dict(mode='legacy')  → 8 fields (if needed)
DefinitieRecord.to_export_dict(mode='minimal') → 5 fields (core only)
```

## Migration Impact

### Before vs After Comparison

```
EXPORT FILE SIZE:                DATA COVERAGE:

Before: ~5KB per definition      Before: 26% (8/31 fields)
After:  ~15KB per definition     After:  90% (28/31 fields)

Growth: ~3x                      Improvement: +246%
Impact: Acceptable               User Value: HIGH
```

### Stakeholder Impact

```
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│ Legal Team     │  │ Data Analysts  │  │ Auditors       │
├────────────────┤  ├────────────────┤  ├────────────────┤
│ ✅ Gets legal  │  │ ✅ Full data   │  │ ✅ Approval    │
│    context     │  │    for analysis│  │    trail       │
│ ✅ Wettelijke  │  │ ✅ Source info │  │ ✅ Version     │
│    basis       │  │ ✅ Validation  │  │    history     │
└────────────────┘  └────────────────┘  └────────────────┘
```

## Conclusion

**Problem:** Architectural bifurcation leading to 74% data loss
**Solution:** Unify through service layer with comprehensive field mapping
**Effort:** 7.5 hours
**Risk:** LOW (with rollback plan)
**Value:** HIGH (resolves user complaint, improves data quality)
