---
aangemaakt: 01-01-2025
applies_to: definitie-app@current
astra_compliance: true
bijgewerkt: 05-09-2025
canonical: true
completion: 100%
id: EPIC-001
last_verified: 05-09-2025
owner: business-analyst
prioriteit: HOOG
status: Voltooid
stories:
- US-001
- US-002
- US-003
- US-004
- US-005
target_release: v1.0
titel: Basis Definitie Generatie
vereisten:
- REQ-018
- REQ-038
- REQ-059
- REQ-078
- REQ-079
- REQ-082
---



# EPIC-001: Basis Definitie Generatie

## Managementsamenvatting

Kernfunctionaliteit voor het genereren van juridische definities met GPT-4. Deze epic dekt de basis van het DefinitieAgent systeem, waarmee geautomatiseerde generatie van Nederlandse juridische definities met AI-ondersteuning mogelijk wordt.

**⚠️ DEPRECATION NOTICE:** De UnifiedDefinitionGenerator wordt vervangen door moderne V2 orchestrators. Zie EPIC-012 voor de refactoring van alle legacy generator modules naar de nieuwe architectuur.

## Bedrijfswaarde

- **Primaire Waarde**: Geautomatiseerde generatie van hoogwaardige juridische definities
- **Tijdsbesparing**: Reduceert definitiecreatie van uren naar seconden
- **Kwaliteit**: Consistente toepassing van juridische terminologiestandaarden
- **Compliance**: ASTRA/NORA/BIR compliant vanaf het begin

## Succesmetrieken

- ✅ Definitiegeneratie responstijd < 5 seconden
- ✅ 95% nauwkeurigheid in gebruik juridische terminologie
- ✅ Geen hardcoded configuratiewaarden
- ✅ 100% omgevingsgebaseerde configuratie

## Traceability Matrix

### Vereisten → Gebruikersverhalen

| Requirement | Gebruikersverhaal | Beschrijving | Status |
|------------|------------|--------------|--------|
| REQ-018 | US-001 | GPT-4 integratie voor definitiegeneratie | ✅ Voltooid |
| REQ-038 | US-001, US-002 | Context-aware prompting | ✅ Voltooid |
| REQ-059 | US-003 | Prompt template management | ✅ Voltooid |
| REQ-078 | US-001, US-004 | Response tijd < 5 seconden | ✅ Voltooid |
| REQ-079 | US-001, US-005 | 95% nauwkeurigheid | ✅ Voltooid |
| REQ-082 | US-002 | Omgevingsconfiguratie | ✅ Voltooid |

### Gebruikersverhalen → Implementatie

| Gebruikersverhaal | Component | Module | Test Coverage |
|------------|-----------|--------|---------------|
| US-001 | UnifiedDefinitionGenerator (DEPRECATED - zie EPIC-012) | src/services/definition_generator.py | 99% |
| US-002 | ServiceContainer | src/services/container.py | 95% |
| US-003 | PromptServiceV2 | src/services/prompt_service_v2.py | 92% |
| US-004 | Prestaties optimalisatie | Multiple modules | 88% |
| US-005 | ValidationOrchestratorV2 | src/services/validation/validation_orchestrator_v2.py | 98% |

## ASTRA/NORA Compliance

### ASTRA Richtlijnen
- ✅ **Modulaire architectuur**: Service-oriented design met dependency injection
- ✅ **Herbruikbaarheid**: Generieke services voor alle justitieketens
- ✅ **Schaalbaarheid**: Horizontaal schaalbaar via container deployment
- ✅ **Beveiliging**: API key management via environment variables

### NORA Principes
- ✅ **NP01 - Proactief**: Anticipeert op toekomstige behoeften met extensible architecture
- ✅ **NP02 - Vindbaar**: Alle definities doorzoekbaar en categoriseerbaar
- ✅ **NP03 - Toegankelijk**: Web-based interface, platform-onafhankelijk
- ✅ **NP04 - Standaarden**: Gebruikt open standaarden (REST, JSON, SQLite)
- ✅ **NP05 - Gebundeld**: Eén systeem voor alle justitiepartners

## Gebruikersverhalen Overzicht

### US-001: Basic Definition Generation via GPT-4 ✅
**Status:** GEREED
**Prioriteit:** HOOG
**Verhaalpunten:** 8

**Gebruikersverhaal:**
Als juridisch medewerker bij het OM/DJI/Rechtspraak
wil ik to generate definitions using AI
zodat I can quickly create consistent juridische definities

**Implementatie:**
- Core generator in `src/services/definition_generator.py`
- OpenAI integration via `src/services/ai_service_v2.py`
- Full GPT-4 support with temperature control

### US-002: Prompt Template System ✅
**Status:** GEREED
**Prioriteit:** HOOG
**Verhaalpunten:** 5

**Gebruikersverhaal:**
Als systeembeheerder binnen de justitieketen
wil ik configurable prompt templates
zodat prompts can be adjusted without code Wijzigingen

**Implementatie:**
- Modular prompt service: `src/services/prompt_service_v2.py`
- Template configuration in `config/prompts/`
- Context-aware template selection

### US-003: V1 Orchestrator Elimination ✅
**Status:** GEREED
**Prioriteit:** HOOG
**Verhaalpunten:** 13

**Gebruikersverhaal:**
Als ontwikkelaar binnen de justitieketen
wil ik a single, modern orchestration system
zodat the codebase is maintainable and consistent

**Implementatie:**
- V2 orchestrator fully operational
- V1 code removed from production paths
- Migration Voltooid 04-09-2025

### US-004: AI Configuration System via ConfigManager ✅
**Status:** GEREED
**Prioriteit:** GEMIDDELD
**Verhaalpunten:** 5

**Gebruikersverhaal:**
Als systeembeheerder binnen de justitieketen
wil ik component-specific AI configuration
zodat each component can have optimized settings

**Implementatie:**
- ConfigManager in `src/config/config_manager.py`
- Component configs in `config/ai/components/`
- Dynamic configuration loading

### US-005: Centralized AI Model Configuration ✅
**Status:** GEREED
**Prioriteit:** GEMIDDELD
**Verhaalpunten:** 3

**Gebruikersverhaal:**
Als ontwikkelaar binnen de justitieketen
wil ik centralized model configuration
zodat there are no hardcoded defaults

**Implementatie:**
- All models defined in configuration
- Environment variable overrides supported
- No hardcoded "gpt-4" strings remain

## Afhankelijkheden

- OpenAI API access (GPT-4)
- Environment configuration system
- Validation framework (Episch Verhaal 2)

## Risico's & Mitigaties

| Risk | Impact | Mitigation |
|------|--------|------------|
| API Rate Limits | HOOG | Implemented rate limiting and retry logic |
| Model Wijzigingen | GEMIDDELD | Abstracted model selection via config |
| Cost Overruns | GEMIDDELD | Token usage monitoring geïmplementeerd |

## Technische Architectuur

```
User Input → UI Layer → Generation Request
                ↓
        ServiceContainer
                ↓
    UnifiedDefinitionGenerator
                ↓
    PromptServiceV2 + AIServiceV2
                ↓
            GPT-4 API
                ↓
        Generated Definition
```

## testdekking

- Unit Tests: 95% coverage
- Integration Tests: Complete
- E2E Tests: Automated via CI/CD
- Prestaties Tests: < 5s response validatied

## Compliance Notities

### ASTRA Compliance
- ✅ Service-oriented architecture
- ✅ Loose coupling via interfaces
- ✅ Configuration externalization
- ✅ Audit logging geïmplementeerd

### NORA Standards
- ✅ Government IT architecture principles
- ✅ beveiliging by design
- ✅ Privacy protection measures
- ✅ Accessibility standards

## Definitie van Gereed

- [x] All user stories Voltooid
- [x] testdekking > 90%
- [x] Prestaties benchmarks met
- [x] beveiliging review passed
- [x] Documentatie compleet
- [x] ASTRA/NORA/BIR compliance verified
- [x] productie deployment successful

## Wijzigingslog

| Datum | Versie | Wijzigingen |
|-------|--------|-------------|
| 01-01-2025 | 1.0 | Episch Verhaal aangemaakt |
| 05-09-2025 | 1.x | Vertaald naar Nederlands met justitie context |
| 04-09-2025 | 1.1 | V1 orchestrator geëlimineerd |
| 05-09-2025 | 1.2 | Gemarkeerd als 100% voltooid |
| 05-09-2025 | 1.3 | Vertaald naar Nederlands met justitie context |

## Gerelateerde Documentatie

- [Solution Architecture](../../architectuur/SOLUTION_ARCHITECTURE.md)
- [Technische Architectuur](../../architectuur/TECHNICAL_ARCHITECTURE.md)
- [Validation Orchestrator V2](../archief/2025-09-architectuur-consolidatie/misc/validation_orchestrator_v2.md)

## Stakeholder Goedkeuring

- Business Eigenaar: ✅ Goedgekeurd (04-09-2025)
- Technisch Lead: ✅ Goedgekeurd (04-09-2025)
- beveiliging Officer: ✅ Goedgekeurd (04-09-2025)
- Compliance Officer: ✅ Goedgekeurd (04-09-2025)

---

*This epic is part of the DefinitieAgent project and folLAAGs ASTRA/NORA/BIR guidelines for justice domain systems.*
