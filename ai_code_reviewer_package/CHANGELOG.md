# Changelog - AI Code Reviewer

## [2.1.0] - 2025-08-15

### Added
- Enhanced auto-fix capabilities met autoflake, isort en autopep8
- Verbeterde import ordering en unused import removal
- Automatische bare except fixes
- Quinn QA architect integration
- Multi-tool verbeterloop voor maximale effectiviteit

### Dependencies Added
- autoflake>=2.0.0
- isort>=5.12.0
- autopep8>=2.0.0

### Fixed
- Versie inconsistenties in package configuratie
- Ontbrekende dependencies in setup.py

## [2.0.0] - 2025-08-14

### Added
- Universal BMAD post-edit hooks
- Enhanced SQL injection detection
- AI agent auto-detection
- Context-aware false positive filtering
- Extended BMAD integration

### Changed
- Complete architectuur herziening voor BMAD Method ondersteuning
- Verbeterde hook integratie voor continue kwaliteitsbewaking

## [1.0.0] - Initial Release

### Added
- Basis AI code review functionaliteit
- Integratie met Anthropic Claude
- Automatische code fixes
- Configureerbare review cycles