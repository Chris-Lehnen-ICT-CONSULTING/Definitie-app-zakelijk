# Architecture Reorganization Archive - 2025-08-20

## Reason for Archiving
Deze documenten zijn gearchiveerd als onderdeel van de architectuur documentatie reorganisatie om duplicaten te verwijderen en een duidelijke scheiding tussen EA en SA te creëren.

## Archived Documents

### Merged into EA/SA
1. **ARCHITECTURE_COMPLETE_AS-IS_TO-BE.md**
   - Product Portfolio Status → Enterprise Architecture Section 8
   - Feature Implementation Details → Solution Architecture Section 12
   - Technical Debt Analysis → Solution Architecture Section 13
   - Transformed remainder → PRODUCT_DELIVERY_TRACKER.md

### Duplicate Visualizations
2. **AS-IS-TO-BE-ARCHITECTURE.html** - Duplicate, less complete than markdown
3. **AS-IS-TO-BE-ARCHITECTURE-DETAILED.html** - Duplicate visualization
4. **ARCHITECTURE_VISUALIZATION_DETAILED.html** - Outdated visualization
5. **ARCHITECTURE_OVERVIEW.html** - Too limited, covered by other docs

### Completed/Duplicate Documents
6. **SOLUTION_ARCHITECTURE_COMPLETE.md** - Merged into SOLUTION_ARCHITECTURE.md
7. **REORGANIZATION_PLAN.md** - Superseded by WERKPLAN_EA_SA_REORGANISATIE.md
8. **OVERLAP_ANALYSIS_EA_SA.md** - Analysis complete, results implemented

### Static Dashboards
9. **ENTERPRISE_ARCHITECTURE_DASHBOARD.html** - To be generated dynamically
10. **SOLUTION_ARCHITECTURE_DASHBOARD.html** - To be generated dynamically
11. **sync-dashboard.html** - Can be generated from sync-state.json
12. **README_FEATURE_STATUS.md** - Instructions moved to main README

## Recovery
All documents are preserved in this archive folder and can be recovered if needed.

## New Structure
- Enterprise Architecture: Contains business view including product status
- Solution Architecture: Contains technical implementation and debt analysis
- PRODUCT_DELIVERY_TRACKER.md: Live sprint tracking document
- Reduced from 30+ to ~15 active documents (50% reduction)
