# Changelog

All notable changes to DefinitieAgent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **Cognitive Complexity Reduction** (`examples_block.py`): Refactored monolithic function to comply with SonarQube standards
  - Reduced `render_examples_block()` complexity from 152 to ≤5 (97% reduction)
  - Extracted 12 focused helper functions with single responsibilities
  - Main function reduced from 392 lines to 41 lines (90% reduction)
  - Zero behavioral changes - all business logic preserved
  - Improved testability: 11 independently testable functions
  - Better maintainability: Clear separation of concerns (validation, generation, display, edit, persistence)
  - Related: SonarQube code quality improvements
- **CSV Export Delimiter Migration**: Changed from pipe (`|`) to semicolon (`;`) for voorbeelden fields
  - Affects: `voorbeeld_zinnen`, `praktijkvoorbeelden`, `tegenvoorbeelden`
  - Rationale: Dutch CSV standard compliance + prevents re-import failures with pipe characters in legal text
  - **Breaking**: Old CSV exports with pipe delimiter cannot be re-imported
  - Workaround: Manual find/replace ` | ` → `; ` in old CSVs before import
  - Related: DEF-43 export system improvements

### Added
- Comprehensive integration tests for export functionality (658 lines)
  - Full coverage for TXT, CSV, JSON export formats
  - Excel export validation (encoding, timezone handling)
  - Helper method testing for `_generate_export_path()` and `_prepare_export_data()`
  - Related: DEF-43
- Helper methods in `DefinitieRepository` for cleaner export logic
  - `_generate_export_path()`: Centralized filename generation with timestamp
  - `_prepare_export_data()`: Data transformation for export formats
  - 68.6% code duplication reduction in export methods

### Fixed
- **Examples Block Save Handler** (DEF-52): Critical fixes and code simplification in `examples_block.py`
  - Added type-safe helper functions: `_get_with_fallback()` and `_get_toelichting()`
  - Widget values now properly fallback to session state (fixes empty widgets after rerun)
  - Type validation for all inputs with graceful error handling
  - Comprehensive logging for debugging (warning/error/info levels)
  - User-friendly validation: won't save if no voorbeeldzinnen present
  - 62% complexity reduction via helper function extraction
  - Improved error messages (separate ValueError and Exception handling)
- Exception handling in `export_definitie()` method (DEF-43)
  - User-friendly Dutch error messages
  - Proper error logging
  - Graceful failure handling for file I/O errors
- Excel export timezone-aware datetime handling
  - Fixed `TypeError` when writing datetime objects to Excel
  - Converts `datetime` to string before Excel export

### Removed
- **History Tab Removal** (US-412): Removed unused history tab UI component (-453 LOC)
  - Tab functionality was not in active use
  - Database structure and audit triggers preserved
  - See [migration guide](docs/migrations/history_tab_removal.md) for details
  - Future inline history implementation planned in US-411

### Preserved
- Database table `definitie_geschiedenis` remains intact
- All audit triggers continue to function
- Historical data fully preserved and accessible via SQL

### Documentation
- Added comprehensive migration guide for history tab removal
- Created US-411 specification for future modern inline history
- Created US-412 documentation for history tab removal
- Updated EPIC-021 with removal rationale and future plans

## [2.3.0] - 2025-09-19

### Changed
- V1→V2 migration fully completed
- All legacy code removed
- Clean V2 architecture implemented

### Added
- US-064 Definition Edit Interface
  - Version history support
  - Auto-save functionality
  - 100% test coverage achieved

## [2.2.0] - 2025-09-12

### Added
- Document upload support for context enrichment
  - DOCX and PDF text extraction
  - Smart snippet injection into prompts
  - Configurable via environment variables
  - Source attribution in generated definitions

### Security
- Basic security measures implemented
- Pre-commit hooks for code quality

### Quality
- Automated CI/CD quality gates via GitHub Actions
- No TODO/FIXME/HACK comments policy enforced
- Ruff linting integrated

## [2.1.0] - 2025-08-XX

### Added
- 45+ validation rules for definition quality
- ModularValidationService architecture
- ApprovalGatePolicy (EPIC-016) for validation thresholds

### Changed
- Migrated to service-oriented architecture
- Implemented dependency injection pattern

## [2.0.0] - 2025-07-XX

### Added
- Streamlit-based UI
- Multi-tab interface (Generate, Edit, Review, Config)
- SQLite database for persistence
- Web lookup integration (Wikipedia, SRU)

### Changed
- Complete rewrite from V1
- Migrated from CLI to web interface

## [1.0.0] - 2025-06-XX

### Added
- Initial release
- GPT-4 powered definition generation
- Basic validation rules
- Command-line interface