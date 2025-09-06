---
id: EPIC-006
title: beveiliging & Auth
canonical: true
status: IN_UITVOERING
owner: business-analyst
last_verified: 2025-09-05
applies_to: definitie-app@current
priority: KRITIEK
target_release: v1.0
aangemaakt: 2025-01-01
bijgewerkt: 2025-09-05
completion: 40%
stories:
  - US-024  # API Key Validation at Startup
  - US-025  # API Key beveiliging Fix (GEREED)
  - US-026  # Environment variable configuration (GEREED)
  - US-027  # Component-specific AI configuration beveiliging (GEREED)
vereisten:
  - REQ-044  # Justice SSO Integration
  - REQ-045  # Audit Logging System
  - REQ-047  # Backup and Restore Functionality
  - REQ-063  # Rate Limiting Per User
  - REQ-071  # beveiliging Testing
  - REQ-081  # Data Archival Strategy
astra_compliance: true
---

# EPIC-006: beveiliging & Auth

## Managementsamenvatting

beveiliging compliance and data protection for the DefinitieAgent system. This epic ensures the application meets justitiesector beveiliging vereisten, protects sensitive data, and implements proper authenticatie and authorization.

## Bedrijfswaarde

- **Primary Value**: Protect sensitive legal data and definitions
- **Compliance**: Meet AVG/GDPR and justitiesector vereisten
- **Trust**: Build user confidence through beveiliging
- **Risk Mitigation**: Prevent data breaches and unauthorized access

## Succesmetrieken

- ✅ Zero exposed API keys in code
- ✅ 100% environment-based configuration
- [ ] API key validation on startup
- [ ] Complete audit trail
- [ ] Justice SSO integration
- [ ] Zero beveiliging vulnerabilities (OWASP top 10)

## Gebruikersverhalen Overzicht

### US-024: API Key Validation at Startup
**Status:** Nog te bepalen
**Prioriteit:** HOOG
**Story Points:** 3

**Gebruikersverhaal:**
Als systeembeheerder binnen de justitieketen
wil ik API keys valiDatumd at application startup
zodat configuration errors are caught early and don't cause runtime failures

**Acceptatiecriteria:**
1. gegeven the application starts
   wanneer OpenAI API key is configured
   dan the key is valiDatumd via test API call
2. gegeven an invalid API key is detected
   wanneer application initialization occurs
   dan clear error message is shown and startup is halted
3. gegeven a valid API key
   wanneer application starts
   dan initialization continues normally

**Domain Rules:**
- Comply with NORA beveiliging guidelines for credential management
- FolLAAG ASTRA patterns for configuration validation
- No sensitive data in error messages or logs

**Implementatie Notes:**
- beveiliging: Never log full API keys (only last 4 chars)
- Privacy: No API key in error tracking
- Prestaties: Validation timeout of 5 seconds
- Location: Add to `src/services/container.py` initialization

### US-025: API Key beveiliging Fix ✅
**Status:** GEREED
**Prioriteit:** KRITIEK
**Story Points:** 5

**Implementatie:**
- Removed all hardcoded API keys
- Moved to environment variables
- Added .env.example file
- UpDatumd documentation

### US-026: Environment Variable Configuration ✅
**Status:** GEREED
**Prioriteit:** HOOG
**Story Points:** 3

**Implementatie:**
- All sensitive config via env vars
- ConfigManager for centralized access
- Validation of required variables
- Default values for non-sensitive config

### US-027: Component-specific AI Configuration beveiliging ✅
**Status:** GEREED
**Prioriteit:** GEMIDDELD
**Story Points:** 5

**Implementatie:**
- Separate config per component
- No API keys in component configs
- Encrypted storage for sensitive data
- Access control via ServiceContainer

## beveiliging Architecture

### Authenticatie FLAAG
```
User Access
    ↓
Justice SSO (Planned)
    ↓
Token Validation
    ↓
Session Creation
    ↓
Role Assignment
    ↓
Access Granted
```

### Authorization Model
```
Resources
    ├── Definitions (CRUD)
    ├── validatieregels (Read)
    ├── Web Lookup (Execute)
    ├── Export (Execute)
    └── Admin Functions (Admin only)

Roles
    ├── Viewer (Read only)
    ├── Editor (CRUD definitions)
    ├── Validator (Run validations)
    └── Admin (All permissions)
```

## beveiliging Controls

### Application beveiliging
- ✅ API key protection
- ✅ Environment-based config
- ✅ Input validation
- ⏳ SQL injection prevention
- ⏳ XSS protection
- ❌ CSRF tokens
- ❌ Rate limiting
- ❌ Session management

### Data beveiliging
- ✅ Encrypted API communication
- ⏳ Database encryption at rest
- ⏳ Backup encryption
- ❌ Field-level encryption for PII
- ❌ Data retention policies
- ❌ Secure deletion

### Infrastructure beveiliging
- ✅ HTTPS only
- ⏳ beveiliging headers
- ⏳ Content beveiliging Policy
- ❌ Web Application Firewall
- ❌ DDoS protection
- ❌ Intrusion detection

## Audit vereisten

### Events to Log
- User authenticatie (success/failure)
- Definition CRUD operations
- Validation executions
- Export/Import operations
- Configuration Wijzigingen
- beveiliging events

### Log Format
```json
{
  "timestamp": "ISO 8601",
  "event_type": "string",
  "user_id": "uuid",
  "session_id": "uuid",
  "resource": "string",
  "action": "string",
  "result": "success|failure",
  "metadata": {}
}
```

## Afhankelijkheden

- Justice SSO system integration
- Audit logging infrastructure
- beveiliging scanning tools
- Penetration testing resources

## Risico's & Mitigaties

| Risk | Impact | Mitigation |
|------|--------|------------|
| API Key Exposure | KRITIEK | Environment variables, key rotation |
| Data Breach | KRITIEK | Encryption, access controls |
| Insider Threat | HOOG | Audit logging, least privilege |
| Supply Chain | GEMIDDELD | Dependency scanning, vendoring |

## Compliance vereisten

### AVG/GDPR
- ⏳ Privacy by design
- ⏳ Data minimization
- ❌ Right to erasure
- ❌ Data portability
- ❌ Consent management

### justitiesector
- ❌ Justid integration
- ❌ Chain authorization
- ❌ beveiliging baseline justice
- ❌ Incident response plan

### NORA/ASTRA
- ✅ Configuration management
- ⏳ beveiliging architecture
- ⏳ Identity management
- ❌ beveiliging monitoring

## Definitie van Gereed

- [ ] All API keys secured
- [ ] Startup validation implemented
- [ ] SSO integration complete
- [ ] Audit logging operational
- [ ] beveiliging scan passed
- [ ] Penetration test passed
- [ ] Compliance review Goedgekeurd
- [ ] Incident response plan ready

## Wijzigingslog

| Datum | Versie | Wijzigingen |
|------|---------|---------|
| 2025-01-01 | 1.0 | Epic aangemaakt |
| 2025-09-05 | 1.x | Vertaald naar Nederlands met justitie context |
| 2025-09-04 | 1.1 | API keys secured |
| 2025-09-05 | 1.2 | Status: 40% complete |

## Gerelateerde Documentatie

- [beveiliging Architecture](../architectuur/beveiliging_architecture.md)
- [Audit Logging Design](../technisch/audit_logging.md)
- [Justice SSO Integration](../integration/justice_sso.md)

## Stakeholder Goedkeuring

- beveiliging Officer: ⏳ In progress
- Privacy Officer: ❌ Not started
- Compliance Officer: ❌ Not started
- Operations Team: ⏳ In progress

---

*This epic is part of the DefinitieAgent project and folLAAGs ASTRA/NORA/BIR guidelines for justice domain systems.*
