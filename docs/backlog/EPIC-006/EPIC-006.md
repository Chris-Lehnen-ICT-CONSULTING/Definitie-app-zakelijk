---
id: EPIC-006
titel: "EPIC-006: Security Baseline - Minimale safeguards voor single-user deployments"
status: active
prioriteit: HOOG
aangemaakt: 01-01-2025
bijgewerkt: 05-09-2025
owner: product-development
applies_to: definitie-app@current
canonical: true
last_verified: 05-09-2025
vereisten:
  - REQ-044
  - REQ-045
  - REQ-047
  - REQ-063
stories:
  - US-140
  - US-029
  - US-030
  - US-031
  - US-032
astra_compliance: true
completion: 10%
target_release: v1.1
---



# EPIC-006: Security Baseline

## Managementsamenvatting

Deze epic borgt de minimale beveiligingsmaatregelen die nodig zijn voor een single-user/single-developer setup. Focuspunten: direct falen bij ontbrekende of ongeldige API-sleutels, standaard HTTP-beveiligingsheaders, privacyvriendelijke logging en routinele dependency/secrets-scans. Zwaardere enterprise-controls (RBAC, SSO, uitgebreide audittrail) zijn naar het archief verplaatst.

## Bedrijfswaarde
- **Snelle detectie van misconfiguraties**: gebruiker ziet meteen wat hij moet herstellen
- **Privacybescherming**: gevoelige data komt niet in logs of exports terecht
- **Beheersbare risico’s**: regressies in dependencies of lekken worden vroegtijdig gesignaleerd

## Succesmetrieken
- [ ] Startup blokkeert binnen 3s bij ongeldige API key (US-140)
- [ ] Alle responses bevatten beveiligingsheaders (CSP, HSTS, X-Frame, X-Content) en request rate-limiting (US-029)
- [ ] Logs tonen geen PII of secrets; retentie ≤ 30 dagen (US-030)
- [ ] CI-pipeline draait dependency audit + secrets-scan op main en feature branches (US-031)
- [ ] Encryptie-at-rest geconfigureerd of aantoonbaar niet nodig voor lokale opslag (US-032 – stretch)

## Story-overzicht
- **US-140 – API key validatie bij startup**  
  Minimalistische health-check met duidelijke foutmeldingen en optionele retry zonder herstart.
- **US-029 – Security headers & rate limiting**  
  Streamlit/fastapi config uitbreiden met standaard headers, throttling en baseline tests.
- **US-030 – Logging redactie & retentie**  
  Introduceer central logging helper die PII maskt en logretentie/rotatie afdwingt.
- **US-031 – Secrets/dependency audits in CI**  
  Automatiseer `pip-audit`, `safety` en `detect-secrets` of alternatief script; rapportage in pipeline-artifacts.
- **US-032 – Encryptie at rest (stretch)**  
  Onderzoek SQLite + dossierencryptie; markeer als optioneel wanneer opslag op vertrouwde laptop blijft.

## Afbakening
- Geen user management, RBAC of SSO (verplaatst naar `_archive/enterprise/`)
- Audit trail en forensische logging vallen buiten dit baseline bereik
- Geen hosting-specifieke hardening (infrastructurele maatregelen liggen bij toekomstige opschalingsstappen)

## Deliverables
1. Checklist “Security Baseline” opgenomen in releaseproces
2. Tests/scripts voor headers, logging en scans toegevoegd aan `scripts/security/`
3. Documentatie in `docs/security-baseline.md` (nieuw) met configuratie-instructies voor lokale omgevingen
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
- [ ] Startup validation geïmplementeerd
- [ ] SSO integration complete
- [ ] Audit logging operational
- [ ] beveiliging scan passed
- [ ] Penetration test passed
- [ ] Compliance review Goedgekeurd
- [ ] Incident response plan ready

## Wijzigingslog

| Datum | Versie | Wijzigingen |
|------|---------|---------|
| 01-01-2025 | 1.0 | Episch Verhaal aangemaakt |
| 05-09-2025 | 1.x | Vertaald naar Nederlands met justitie context |
| 04-09-2025 | 1.1 | API keys secured |
| 05-09-2025 | 1.2 | Status: 40% complete |

## Gerelateerde Documentatie

- beveiliging Architecture
- Audit Logging Design
- Justice SSO Integration

## Stakeholder Goedkeuring

- beveiliging Officer: ⏳ In progress
- Privacy Officer: ❌ Not started
- Compliance Officer: ❌ Not started
- Operations Team: ⏳ In progress

---

*This epic is part of the DefinitieAgent project and folLAAGs ASTRA/NORA/BIR guidelines for justice domain systems.*
