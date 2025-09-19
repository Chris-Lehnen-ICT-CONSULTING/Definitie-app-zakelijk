# CHANGELOG

## [2.4.0] - 2025-09-19

### 🎯 Major Achievement: V1→V2 Architecture Migration Complete

#### Changed
- **Complete V1 Architecture Elimination**
  - Removed all legacy fallback methods from `definition_orchestrator_v2.py` (69 lines)
  - Previously deleted V1 service files (~1000 lines total)
  - Achieved 100% V2 implementation across entire codebase
  - Zero V1 symbol references remaining

#### Fixed
- Database schema warning: Added table existence check before CREATE TABLE
- ToetsregelManager float conversion error: Added None checking for weight conversions
- Eliminated all startup warnings

#### Architecture Impact
- **Code Reduction**: ~1069 lines of legacy code removed
- **Performance**: Cleaner execution paths without fallback logic
- **Maintainability**: Single architecture to maintain (V2 only)
- **Testing**: Clear V2-only test strategy

#### Documentation
- Created comprehensive migration documentation (now archived)
- Updated refactor-log.md with complete migration details
- Verified all Python files compile successfully

## [2.3.0] - 2025-09-12

### Added
- US-064: Definition Edit Interface with version history
- Auto-save functionality for edits
- 100% test coverage for edit features

## [2.2.0] - 2025-09-11

### Added
- EPIC-010: Context Flow 100% completed
- CI/CD gates against legacy patterns
- 7 blocked patterns enforcement

### Changed
- Services now async-only with sync wrappers removed
- UI uses `async_bridge.py` for sync↔async bridging
- Feature flags managed via `ui/helpers/feature_toggle.py`

## [2.1.0] - Previous

### Added
- Initial V2 architecture components
- ModularValidationService with 45 validation rules
- ValidationOrchestratorV2
- ServiceContainer with dependency injection

### Changed
- Progressive migration from V1 to V2 services
- Improved prompt engineering with PromptServiceV2