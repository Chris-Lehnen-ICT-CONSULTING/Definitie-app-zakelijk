# Changelog

All notable changes to DefinitieAgent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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