---
canonical: true
status: active
owner: architecture
last_verified: 2025-09-08
applies_to: definitie-app@v2
document_type: gap-analysis
---

# Compliance Gap Analysis

## Executive Summary

Dit document identificeert en analyseert compliance gaps in het DefinitieAgent project ten opzichte van justice sector standaarden (ASTRA, NORA), wettelijke vereisten (AVG, BIO, Wjsg), en organisatie-specifieke eisen (OM, DJI, Rechtspraak, Justid). De analyse toont kritieke gaps die productie-deployment kunnen blokkeren.

## Gap Severity Levels

- 🔴 **KRITIEK**: Blokkeert productie deployment, wettelijke non-compliance
- 🟠 **HOOG**: Significant risico, moet voor go-live opgelost zijn
- 🟡 **MEDIUM**: Belangrijk voor volledige compliance, kan gefaseerd
- 🟢 **LAAG**: Nice-to-have, optimalisatie mogelijkheid

## Critical Compliance Gaps

### 1. Security & Authentication Gaps

#### GAP-001: Justice SSO Integration Ontbreekt 🔴
- **Requirement**: REQ-001, REQ-029
- **Standard**: ASTRA-SEC-002, ASTRA-SEC-014
- **Impact**: Geen productie deployment mogelijk zonder Justice SSO
- **Current State**: Basic authentication placeholder
- **Target State**: Volledig geïntegreerde Justice SSO (SAML 2.0/OAuth2)
- **Affected Orgs**: Alle (DJI, OM, Rechtspraak, Justid)
- **Resolution**:
  ```python
  # Required implementation in src/auth/
  - sso_integration.py      # Justice SSO SAML/OAuth handler
  - identity_federation.py  # Multi-org identity management
  - session_manager.py      # Secure session handling
  - mfa_support.py         # Multi-factor authentication
  ```
- **Timeline**: Q1 2025 (Sprint 37-39)
- **Dependencies**: Justid SSO team, PKI certificates

#### GAP-002: Audit Logging Niet Compliant 🔴
- **Requirement**: REQ-024
- **Standard**: ASTRA-AUD-001, ASTRA-AUD-002
- **Legal**: Wjsg Art. 35, AVG Art. 30
- **Current State**: Basic application logging
- **Target State**: Forensische audit trail met immutability
- **Affected Orgs**: OM (kritiek), DJI (kritiek), Justid
- **Resolution**:
  ```python
  # Required components
  - Immutable log store (append-only)
  - Cryptographic log chaining
  - Who/What/When/Where/Why tracking
  - Log retention policy (10-20 jaar)
  - Audit log export voor forensisch onderzoek
  ```
- **Timeline**: Q1 2025 (Sprint 38)

#### GAP-003: Data Classification System Ontbreekt 🔴
- **Requirement**: REQ-025
- **Standard**: ASTRA-DATA-009, ASTRA-SEC-013
- **Legal**: BIO, Wjsg Art. 22
- **Current State**: Geen data rubricering
- **Target State**: Automatische classificatie (Openbaar/Intern/Vertrouwelijk/Geheim)
- **Affected Orgs**: DJI (justitiabelen), OM (strafzaken), Justid (screening)
- **Resolution**:
  - Metadata tagging systeem
  - Automatische classificatie engine
  - Access control per rubricering niveau
  - Encryption per sensitivity level
- **Timeline**: Q2 2025 (Sprint 40-41)

### 2. Integration & Architecture Gaps

#### GAP-004: Justice Chain Interfaces Niet Geïmplementeerd 🟠
- **Requirement**: REQ-015, REQ-030
- **Standard**: ASTRA-INT-001, ASTRA-INT-009
- **Current State**: Standalone applicatie
- **Target State**: Volledig geïntegreerd in justice chain
- **Affected Systems**:
  - GPS (OM) - XML berichten
  - TULP (DJI) - REST services
  - GPS-RM (Rechtspraak) - SOAP/REST
  - JDS (Justid) - Service bus
- **Resolution**:
  ```yaml
  interfaces:
    om:
      protocol: REST/SOAP
      format: JSON/XML
      auth: mTLS + OAuth2
    dji:
      protocol: REST
      format: JSON
      auth: SAML 2.0
    rechtspraak:
      protocol: REST
      format: JSON/XML
      auth: API Key + TLS
    justid:
      protocol: REST/SOAP
      format: JSON/XML
      auth: PKI + OAuth2
  ```
- **Timeline**: Q2 2025 (Sprint 41-43)

#### GAP-005: ASTRA Architecture Documentation Incompleet 🟠
- **Requirement**: REQ-013
- **Standard**: ASTRA-GOV-001, ASTRA-DOC-001
- **Current State**: Basis architectuur docs
- **Target State**: Volledige ASTRA-compliant documentatie
- **Missing Documents**:
  - Project Start Architecture (PSA)
  - Solution Architecture Document (SAD)
  - Infrastructure Architecture
  - Security Architecture
  - Data Architecture
- **Resolution**: Complete architecture documentation suite
- **Timeline**: Q1 2025 (Sprint 37-38)

### 3. Data & Privacy Gaps

#### GAP-006: AVG/GDPR Compliance Documentatie Ontbreekt 🔴
- **Legal**: AVG Art. 30, 35
- **Standard**: NORA-BP-15, BIO
- **Current State**: Geen privacy documentatie
- **Target State**: Complete DPIA, verwerkingsregister, privacy statement
- **Required Documents**:
  - Data Protection Impact Assessment (DPIA)
  - Verwerkingsregister Art. 30 AVG
  - Privacy Statement
  - Verwerkersovereenkomsten
  - Data breach procedure
- **Timeline**: Q1 2025 (Sprint 37)

#### GAP-007: Bewaartermijnen Niet Geconfigureerd 🟠
- **Requirement**: REQ-021
- **Legal**: Archiefwet, sector-specifieke termijnen
- **Current State**: Onbeperkte data retentie
- **Target State**: Automatische data lifecycle management
- **Required Retention**:
  - OM: 10 jaar (strafzaken)
  - DJI: 20 jaar (detentie gegevens)
  - Rechtspraak: 5-10 jaar (uitspraken)
  - Justid: 5 jaar (screening)
- **Timeline**: Q2 2025 (Sprint 40)

### 4. Quality & Testing Gaps

#### GAP-008: Security Testing Ontbreekt 🔴
- **Requirement**: REQ-039
- **Standard**: ASTRA-TEST-004, ASTRA-SEC-015
- **Legal**: BIO verplichtingen
- **Current State**: Alleen functionele tests
- **Target State**: Continue security testing pipeline
- **Required Tests**:
  - OWASP ZAP scanning
  - Dependency vulnerability scanning
  - Static code analysis (SAST)
  - Dynamic analysis (DAST)
  - Penetration testing (yearly)
- **Timeline**: Q1 2025 (Sprint 38-39)

#### GAP-009: Performance Testing Niet Uitgevoerd 🟡
- **Requirement**: REQ-008, REQ-009, REQ-038
- **Standard**: ASTRA-PER-001, ASTRA-TEST-003
- **Current State**: Geen load/stress testing
- **Target State**: Automated performance testing
- **Required Metrics**:
  - Response time < 5s (generation)
  - UI response < 200ms
  - 1000 concurrent users
  - 10,000 requests/hour
- **Timeline**: Q2 2025 (Sprint 42)

### 5. Operational Gaps

#### GAP-010: Monitoring & Alerting Ontbreekt 🟠
- **Standard**: ASTRA-OPS-001, NORA-BP-17
- **Current State**: Geen productie monitoring
- **Target State**: 24/7 monitoring met alerting
- **Required Components**:
  - Application Performance Monitoring (APM)
  - Security Information Event Management (SIEM)
  - Uptime monitoring
  - Error tracking
  - Compliance dashboard
- **Timeline**: Q2 2025 (Sprint 43)

## Compliance Gap Matrix

| Gap ID | Area | Severity | Legal Risk | Business Impact | Resolution Effort |
|--------|------|----------|------------|-----------------|-------------------|
| GAP-001 | SSO Integration | 🔴 KRITIEK | HIGH | Blocks production | 3-4 weeks |
| GAP-002 | Audit Logging | 🔴 KRITIEK | HIGH | Legal liability | 2-3 weeks |
| GAP-003 | Data Classification | 🔴 KRITIEK | HIGH | Data breach risk | 3-4 weeks |
| GAP-004 | Chain Integration | 🟠 HOOG | MEDIUM | Limited functionality | 4-6 weeks |
| GAP-005 | ASTRA Docs | 🟠 HOOG | LOW | Approval delay | 2 weeks |
| GAP-006 | GDPR Docs | 🔴 KRITIEK | HIGH | €20M fine risk | 1-2 weeks |
| GAP-007 | Retention Policy | 🟠 HOOG | MEDIUM | Compliance issue | 2 weeks |
| GAP-008 | Security Testing | 🔴 KRITIEK | HIGH | Security breaches | 2-3 weeks |
| GAP-009 | Performance Test | 🟡 MEDIUM | LOW | User experience | 1-2 weeks |
| GAP-010 | Monitoring | 🟠 HOOG | MEDIUM | Operational risk | 2-3 weeks |

## Resolution Roadmap

### Sprint 37 (Immediate - Week 1-2)
- [ ] GAP-006: Start DPIA and privacy documentation
- [ ] GAP-005: Begin ASTRA architecture documentation
- [ ] GAP-001: Initiate Justice SSO integration planning

### Sprint 38 (Week 3-4)
- [ ] GAP-002: Implement forensic audit logging
- [ ] GAP-008: Setup security testing pipeline
- [ ] GAP-005: Complete architecture documentation

### Sprint 39 (Week 5-6)
- [ ] GAP-001: Complete SSO integration development
- [ ] GAP-008: Execute first security scan
- [ ] GAP-003: Design data classification system

### Sprint 40 (Week 7-8)
- [ ] GAP-003: Implement data classification
- [ ] GAP-007: Configure retention policies
- [ ] GAP-004: Start chain integration development

### Sprint 41-43 (Q2 2025)
- [ ] GAP-004: Complete chain integrations
- [ ] GAP-009: Execute performance testing
- [ ] GAP-010: Deploy monitoring infrastructure

## Risk Assessment

### High Risk Items (Must Fix Before Production)

| Risk | Current State | Required State | Consequence if Not Fixed |
|------|--------------|----------------|-------------------------|
| No Justice SSO | Basic auth | Federated SSO | **Cannot deploy** - No access for justice users |
| No audit trail | App logs only | Forensic logging | **Legal liability** - Wjsg/AVG violations, no evidence trail |
| No data classification | All data same | Rubricering system | **Data breach** - Sensitive data exposure |
| No GDPR compliance | Undocumented | Full DPIA/docs | **€20M fine** - AVG Article 83 penalties |
| No security testing | Untested | Continuous testing | **Security breach** - Reputation damage, liability |

### Medium Risk Items (Should Fix Soon)

| Risk | Impact | Mitigation |
|------|--------|------------|
| Limited integration | Reduced functionality | Phased rollout per organization |
| No monitoring | Blind operations | Manual checks until automated |
| Performance unknown | User complaints | Set expectations, optimize later |

## Compliance Checklist

### Legal Requirements ❌
- [ ] AVG/GDPR compliance documentation
- [ ] Wjsg compliance for justice data
- [ ] BIO baseline implementation
- [ ] Archiefwet retention policies
- [ ] eIDAS for digital identity

### Technical Standards ⚠️
- [x] NORA principles (partial)
- [ ] ASTRA framework (incomplete)
- [ ] GEMMA architecture (not started)
- [x] OWASP Top 10 (basic coverage)
- [ ] Justice chain standards (not implemented)

### Organizational Requirements ❌
- [ ] OM integration requirements
- [ ] DJI security requirements
- [ ] Rechtspraak API standards
- [ ] Justid identity management

### Operational Readiness ❌
- [ ] 24/7 monitoring capability
- [ ] Incident response procedures
- [ ] Disaster recovery plan
- [ ] Service level agreements
- [ ] Change management process

## Budget & Resource Requirements

### Development Resources
- **SSO Integration**: 2 developers × 4 weeks = 8 person-weeks
- **Audit System**: 1 developer × 3 weeks = 3 person-weeks
- **Chain Integration**: 3 developers × 6 weeks = 18 person-weeks
- **Security Hardening**: 2 developers × 4 weeks = 8 person-weeks
- **Total Development**: ~37 person-weeks

### Infrastructure Costs
- **Monitoring Tools**: €2,000/month
- **Security Scanning**: €1,500/month
- **HSM/PKI**: €3,000 setup + €500/month
- **Audit Storage**: €1,000/month
- **Total Monthly**: ~€5,000

### External Services
- **Security Audit**: €15,000 (one-time)
- **Penetration Test**: €10,000 (yearly)
- **DPIA Consultant**: €5,000 (one-time)
- **Compliance Audit**: €8,000 (yearly)

## Success Criteria

### Minimum Viable Compliance (MVC) for Production
1. ✅ Justice SSO operational
2. ✅ Forensic audit logging active
3. ✅ Data classification implemented
4. ✅ GDPR documentation complete
5. ✅ Security baseline achieved
6. ✅ One justice org integrated

### Full Compliance Target
1. ✅ All 4 justice organizations integrated
2. ✅ Complete ASTRA/NORA compliance
3. ✅ Automated security testing
4. ✅ 24/7 monitoring operational
5. ✅ All retention policies automated
6. ✅ Performance SLAs met

## Recommendations

### Immediate Actions (This Week)
1. **Schedule meeting** with Justid for SSO integration requirements
2. **Start DPIA** with privacy officer/DPO
3. **Document** current security measures for BIO baseline
4. **Contact** each justice org for integration specifications

### Short Term (Next Month)
1. **Implement** audit logging system
2. **Deploy** security scanning pipeline
3. **Complete** ASTRA documentation
4. **Design** data classification scheme

### Medium Term (Next Quarter)
1. **Integrate** with all justice systems
2. **Deploy** monitoring infrastructure
3. **Execute** penetration testing
4. **Achieve** BIO certification

## Escalation Path

### For Critical Gaps
1. **Level 1**: Development Team Lead
2. **Level 2**: Product Owner + Security Officer
3. **Level 3**: CTO + Compliance Officer
4. **Level 4**: Executive Board + Legal Counsel

### Approval Required From
- **Justice SSO**: Justid Architecture Board
- **Chain Integration**: Justice Chain Coordination Committee
- **Security Measures**: CISO + Security Board
- **GDPR Compliance**: Data Protection Officer
- **Production Deployment**: Change Advisory Board

## Conclusion

Het DefinitieAgent project heeft **10 significante compliance gaps** waarvan **5 kritiek** zijn voor productie deployment. De geschatte effort voor volledige compliance is **37 person-weeks** met een infrastructure investering van **€5,000/maand** en eenmalige kosten van **€38,000**.

### Go/No-Go Decision Criteria
- **NO-GO** zonder: SSO, Audit logging, GDPR docs, Security testing
- **LIMITED-GO** mogelijk met: Enkele org integratie, basis monitoring
- **FULL-GO** vereist: Alle gaps opgelost, volledige compliance

### Recommended Path Forward
1. **Phase 1** (Q1 2025): Fix kritieke gaps, achieve MVC
2. **Phase 2** (Q2 2025): Complete integrations, full compliance
3. **Phase 3** (Q3 2025): Optimization and certification

## Change Log
- 2025-09-08: Initial gap analysis completed
- 2025-09-08: Identified 10 major compliance gaps
- 2025-09-08: Created resolution roadmap and budget estimate
