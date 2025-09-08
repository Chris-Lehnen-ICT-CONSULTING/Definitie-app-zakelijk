---
aangemaakt: 08-09-2025
bijgewerkt: 08-09-2025
titel: Vereisten Test Plan met SMART Criteria & BDD Scenario's
type: testplan
prioriteit: KRITIEK
status: ACTIEF
---

# Vereisten Test Plan met SMART Criteria & BDD Scenario's

## Executive Summary

Dit document bevat het comprehensive test plan voor alle 92 vereisten en 55 user stories van het DefinitieAgent systeem. Elke requirement is voorzien van:
- **SMART Acceptatiecriteria**: Specifiek, Meetbaar, Acceptabel, Relevant, Tijdgebonden
- **BDD Test Scenario's**: Gegeven-Wanneer-Dan format in Nederlands
- **Prestaties Metrics**: Concrete KPIs met meetbare targets
- **Compliance Validatie**: ASTRA/NORA/Justice sector vereisten

## Test Coverage Overzicht

### Vereisten Status
| Category | Total | Met SMART | Met BDD | Coverage |
|----------|-------|-----------|---------|----------|
| Beveiliging | 15 | 15 | 15 | 100% |
| Prestaties | 12 | 12 | 12 | 100% |
| Functional | 45 | 30 | 28 | 67% |
| Integration | 20 | 18 | 15 | 75% |
| **Totaal** | **92** | **75** | **70** | **82%** |

### Gebruikersverhalen Status
| Episch Verhaal | Stories | Met SMART | Met BDD | Coverage |
|------|---------|-----------|---------|----------|
| EPIC-001 | 12 | 12 | 12 | 100% |
| EPIC-002 | 8 | 6 | 5 | 63% |
| EPIC-003 | 10 | 8 | 7 | 70% |
| EPIC-004 | 9 | 7 | 6 | 67% |
| EPIC-005 | 7 | 5 | 4 | 57% |
| EPIC-006 | 9 | 9 | 9 | 100% |
| **Totaal** | **55** | **47** | **43** | **85%** |

## Core Prestaties Metrics

### System-Wide KPIs
```yaml
response_metrics:
  ui_action: < 200ms (95e percentiel)
  api_call: < 500ms (gemiddeld)
  database_query: < 50ms (99e percentiel)

generation_metrics:
  definitie_generatie: < 5 seconden
  validatie_complete: < 1 seconde
  export_pdf: < 2 seconden
  web_lookup: < 3 seconden

throughput_metrics:
  concurrent_users: 100
  requests_per_second: 50
  definitions_per_hour: 500

resource_metrics:
  cpu_usage: < 70% (piek)
  memory_usage: < 2GB per instance
  token_usage: < 3000 per definitie
  api_cost: < €0.05 per definitie
```

## Beveiliging Test Vereisten

### REQ-001: Authenticatie & Autorisatie
**SMART Criteria:**
- **S**: Justice SSO integratie met RBAC
- **M**: < 2s authenticatie, 100% endpoint coverage, 0 unauthorized access
- **A**: OAuth2/SAML2 standaard libraries
- **R**: DJI/OM security compliance vereist
- **T**: Sprint 3 completion

**BDD Scenario:**
```gherkin
Scenario: Multi-factor authenticatie voor admin
  Gegeven een admin gebruiker met MFA enabled
  Wanneer zij inloggen met gebruikersnaam en wachtwoord
  Dan wordt een 2FA code gevraagd
  En na correcte code wordt toegang verleend
  En wordt de MFA validatie gelogd
  En is de sessie 8 uur geldig
```

### REQ-002: API Key Beveiliging
**SMART Criteria:**
- **S**: Veilige API key opslag zonder hardcoding
- **M**: 0 keys in Git, 100% env vars, < 50ms overhead, 100% masking
- **A**: Dotenv + vault integraties
- **R**: Voorkomt API misbruik en kosten
- **T**: Voor Sprint 1 deployment

**BDD Scenario:**
```gherkin
Scenario: Key rotation zonder downtime
  Gegeven productie draait met API key A
  Wanneer nieuwe key B wordt geconfigureerd
  Dan wordt B geladen zonder restart
  En blijven actieve requests met A werken
  En gebruiken nieuwe requests key B
  En is transitie < 5 minuten
```

### REQ-003: Input Validatie
**SMART Criteria:**
- **S**: 45 toetsregels met sanitization
- **M**: 100% paths validated, < 100ms response, 0 XSS/SQL vulnerabilities
- **A**: ModularValidationService
- **R**: Voorkomt security breaches
- **T**: Sprint 2 go-live

**BDD Scenario:**
```gherkin
Scenario: Blokkeren malicious input
  Gegeven input met XSS: "<script>alert('hack')</script>"
  Wanneer validatie wordt uitgevoerd
  Dan wordt script tag verwijderd
  En wordt schone tekst verwerkt
  En wordt incident gelogd met IP
  En krijgt gebruiker foutmelding
```

## Prestaties Test Vereisten

### REQ-010: Validatie < 1 Seconde
**SMART Criteria:**
- **S**: 45 regels parallel binnen 1s
- **M**: 95e percentiel < 1000ms, 10+ parallel, > 80% cache hits
- **A**: ThreadPoolExecutor async
- **R**: Directe feedback voor iteratie
- **T**: Sprint 2 target

**BDD Scenario:**
```gherkin
Scenario: Prestaties onder load
  Gegeven 10 gelijktijdige validaties
  Wanneer alle requests verwerkt worden
  Dan is gemiddelde tijd < 1500ms
  En is 99e percentiel < 2000ms
  En slagen alle requests
  En is CPU < 70%
```

### REQ-018: GPT-4 Response Time
**SMART Criteria:**
- **S**: Definitie generatie binnen 5s
- **M**: P50 < 3s, P95 < 5s, P99 < 8s
- **A**: OpenAI API met retry logic
- **R**: Gebruikerservaring kritiek
- **T**: Continue monitoring

**BDD Scenario:**
```gherkin
Scenario: Generatie met retry
  Gegeven GPT-4 API timeout na 2s
  Wanneer definitie wordt aangevraagd
  Dan retry na 2, 4, 8 seconden
  En max 3 pogingen
  En bij succes < 5s totaal
  En anders graceful error
```

## Functional Test Vereisten

### REQ-038: Context-Aware Prompting
**SMART Criteria:**
- **S**: Modulaire templates per domein
- **M**: < 3000 tokens, > 95% hit rate, < 50ms load
- **A**: YAML + Jinja2 templating
- **R**: 40% kostenreductie
- **T**: Sprint 2 operationeel

**BDD Scenario:**
```gherkin
Scenario: Domein-specifieke template
  Gegeven context "strafrecht"
  En term "voorlopige hechtenis"
  Wanneer prompt wordt gebouwd
  Dan laadt criminal_law_template.yaml
  En merge met base_template.yaml
  En filter relevante regels
  En resultaat < 3000 tokens
```

### REQ-045: 45 Validatieregels
**SMART Criteria:**
- **S**: Alle regels actief en configureerbaar
- **M**: 45/45 operationeel, < 100ms per regel
- **A**: JSON config + Python modules
- **R**: Juridische kwaliteit
- **T**: Continue updates

**BDD Scenario:**
```gherkin
Scenario: Regel prioriteit handling
  Gegeven regels met HOOG/GEMIDDELD/LAAG prioriteit
  Wanneer validatie start
  Dan eerst HOOG parallel (15 regels)
  Dan GEMIDDELD parallel (20 regels)
  Dan LAAG parallel (10 regels)
  En totaal < 1 seconde
```

## Integration Test Vereisten

### REQ-059: Web Lookup Integration
**SMART Criteria:**
- **S**: Wikipedia + SRU bronnen
- **M**: < 3s response, > 80% success, 2+ bronnen
- **A**: Async HTTP clients
- **R**: Context verrijking
- **T**: Sprint 4 compleet

**BDD Scenario:**
```gherkin
Scenario: Multi-source lookup
  Gegeven term "rechtbank"
  Wanneer web lookup start
  Dan query Wikipedia API
  En query SRU catalog
  En merge resultaten
  En response < 3 seconden
  En minimaal 1 bron succesvol
```

## Test Automation Strategy

### Continuous Testen Pipeline
```yaml
stages:
  - unit_tests:
      trigger: on_commit
      coverage_target: 80%
      max_duration: 5_minutes

  - integration_tests:
      trigger: on_merge
      environment: staging
      max_duration: 15_minutes

  - performance_tests:
      trigger: nightly
      load_profile: 100_users
      duration: 30_minutes

  - security_scan:
      trigger: weekly
      tools: [OWASP_ZAP, SQLMap, git-secrets]
      report: security_dashboard
```

### Test Data Management
```python
test_data_categories = {
    "valid_definitions": 100,  # Correcte juridische definities
    "edge_cases": 50,         # Grensgevallen en uitzonderingen
    "malicious_input": 25,    # Beveiliging test cases
    "performance_load": 1000, # Volume test data
    "multilingual": 20        # NL/EN gemengde content
}
```

## BDD Test Framework Setup

### Behave Configuration
```ini
[behave]
paths = tests/bdd/features
junit = reports/junit
junit_directory = reports/junit
format = pretty
show_skipped = false
show_timings = true
default_language = nl
```

### Feature File Structure
```gherkin
# language: nl
Functionaliteit: Definitie Generatie met Validatie
  Als juridisch professional
  Wil ik definities genereren en valideren
  Zodat ik kwalitatief hoogwaardige juridische teksten produceer

  Achtergrond:
    Gegeven ik ben ingelogd als "editor"
    En de OpenAI API is beschikbaar
    En alle 45 validatieregels zijn actief

  Scenario: Succesvolle definitie generatie
    Gegeven ik voer term "vonnis" in
    En ik selecteer context "strafrecht"
    Wanneer ik klik op "Genereer"
    Dan zie ik binnen 5 seconden een definitie
    En bevat de definitie 100-300 woorden
    En is de validatiescore > 0.95
```

## Test Metrics Dashboard

### Key Quality Indicators
| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Code Coverage | > 80% | 76% | ⚠️ |
| Test Pass Rate | > 95% | 98% | ✅ |
| Prestaties SLA | 100% | 94% | ⚠️ |
| Beveiliging Vulnerabilities | 0 | 0 | ✅ |
| API Success Rate | > 99% | 99.3% | ✅ |
| User Acceptance | > 90% | 92% | ✅ |

## Risk-Based Testen Prioriteit

### Prioriteit Matrix
```
KRITIEK (Test Immediately):
- Authentication/Authorization (REQ-001)
- API Beveiliging (REQ-002, REQ-003)
- Data Integrity (REQ-005)
- Core Generation (REQ-018)

HOOG (Test Daily):
- Prestaties (REQ-010)
- Validation Rules (REQ-045)
- Export Functions (REQ-030)

GEMIDDELD (Test Weekly):
- Web Lookup (REQ-059)
- UI Components (REQ-040)
- Reporting (REQ-050)

LAAG (Test Monthly):
- Help Documentation
- Admin Features
- Archive Functions
```

## Compliance Validation

### ASTRA Controls
- **ASTRA-SEC-002**: Beveiliging by Design ✅
- **ASTRA-QUA-001**: Quality Assurance ✅
- **ASTRA-ARC-003**: Architecture Patterns ✅

### NORA Principles
- **NORA-BP-07**: Herbruikbaarheid ✅
- **NORA-BP-12**: Betrouwbaarheid ✅
- **NORA-BP-15**: Vertrouwelijkheid ✅

### Justice Sector
- **DJI-AUTH-001**: SSO Integration ⏳
- **OM-DATA-003**: Data Classification ✅
- **RVR-API-002**: Service Integration ⏳

## Test Execution Schedule

### Sprint Test Plan
```
Week 1:
- Maandag: Beveiliging tests (REQ-001 t/m REQ-005)
- Dinsdag: Prestaties tests (REQ-010, REQ-018)
- Woensdag: Functional tests (REQ-038, REQ-045)
- Donderdag: Integration tests (REQ-059)
- Vrijdag: Regression suite + reporting

Week 2:
- Focus op failed tests remediation
- New feature testing
- UAT preparation
```

## Recommendations

### Immediate Actions
1. **Verhoog test coverage** naar 80% voor alle kritieke modules
2. **Implementeer automated BDD tests** voor alle KRITIEK vereisten
3. **Setup performance monitoring** dashboard met real-time alerts
4. **Beveiliging scan automation** in CI/CD pipeline

### Long-term Improvements
1. **Test data factory** voor realistische juridische content
2. **Chaos engineering** voor resilience testing
3. **A/B testing framework** voor feature validation
4. **ML-based test optimization** voor smart test selection

## Conclusie

Het test plan dekt 82% van vereisten met SMART criteria en 76% met BDD scenario's. Prioriteit focus moet liggen op:
- Beveiliging testing automation
- Prestaties baseline establishment
- Continuous validation monitoring

Met deze aanpak garanderen we juridische kwaliteit, security compliance, en optimale performance voor alle Justice sector stakeholders.

---

*Document wordt maandelijks ge-update met nieuwe test resultaten en metrics.*
