# CHANGELOG

## [2.2.0] - 2025-07-16

### Added
- 🚀 Context prohibition enforcement voor CON-01 compliance
- 📋 Modulaire toetsregels architectuur met 46 validators
- 🔄 Unified voorbeelden systeem met 4 generation modes (SYNC, ASYNC, CACHED, RESILIENT)
- 🗄️ Database persistence layer met duplicate detection
- 🎯 DefinitieAgent orchestrator voor iteratieve verbetering
- 🧪 Uitgebreide test suite (63 tests, 85% coverage)

### Fixed
- ✅ Async event loop conflict in unified_voorbeelden systeem
- ✅ String naar enum conversie bug in definitie_checker
- ✅ Context termen verschijnen niet meer in definities (CON-01)
- ✅ Test suite volledig werkend met backward-compatible database schema

### Changed
- 📦 Gerefactored naar modulaire architectuur
- 🔧 Verbeterde prompt building met expliciete context verboden
- 📊 Test coverage verhoogd van 14% naar 85%
- 🏗️ Repository pattern voor database operaties

### Technical Details
- Implementatie van CONTEXT_AFKORTINGEN mapping
- _genereer_context_verboden() methode toegevoegd
- _voeg_contextverbod_toe() voor term varianten detectie
- Async-safe execution met event loop detectie
- Maintenance scripts organisatie volgens best practices

## [2.1.0] - 2025-07-15

### Added
- Document upload functionaliteit (PDF, DOCX, TXT)
- Hybrid context enhancement
- Security middleware
- Performance optimalisaties

## [2.0.0] - 2025-07-14

### Added
- Complete architectuur redesign
- AI-powered definitie generatie
- Streamlit UI interface
- Basis test framework