---
aangemaakt: 01-01-2025
applies_to: definitie-app@current
astra_compliance: true
bijgewerkt: 05-09-2025
canonical: true
completion: 30%
id: EPIC-003
last_verified: 05-09-2025
nora_compliance: true
note: Episch Verhaal 8 (Web Lookup Module) has been merged into this epic
owner: business-analyst
prioriteit: HOOG
stakeholders:
- Justid (terminology authority)
- Rechtspraak (legal sources)
- OM (Openbaar Ministerie (OM) context)
- KB (National Library - SRU provider)
status: IN_UITVOERING
stories:
- US-014
- US-015
- US-016
- US-017
- US-018
- US-019
- US-061
target_release: v1.1
titel: Content Verrijking / Web Lookup
vereisten:
- REQ-021
- REQ-039
- REQ-040
---



# EPIC-003: Content Verrijking / Web Lookup

## Managementsamenvatting

External source integration for definition enrichment. This epic enables the system to consult authoritative sources like Wikipedia and SRU to enrich definitions with context, examples, and references.

**Business Case:** Legal professionals in the Dutch justitieketen require definitions that are not only accurate but also enriched with authoritative context, historical background, and relevant examples. By integrating with trusted external sources like Wikipedia (for general context) and SRU databases (for legal precedents and official documents), the system provides comprehensive definitions that meet the HOOG standards required by OM officier van justities, DJI officials, and Rechtspraak judges. This enrichment is essential for creating definitions that can withstand legal scrutiny and serve as authoritative references in judicial proceedings.

## Bedrijfswaarde

- **Primary Value**: Enrich definitions with authoritative sources
- **Quality**: Add credible references and context from justice-Goedgekeurd sources
- **Compliance**: Meet ASTRA data quality standards and NORA exchange protocols
- **User Satisfaction**: Provide comprehensive definitions voor juridisch medewerkers bij OM, DJI, Rechtspraak, Justid en CJIB
- **Chain Integration**: Enable cross-referencing with Rechtspraak jurisprudence
- **Legal Authority**: StrengDan definitions with case law and statutory references
- **Measurable Outcomes**:
  - 90% of definitions include external references
  - 100% source attribution compliance
  - 50% reduction in manual research time
  - Zero privacy violations in production

## Succesmetrieken (SMART)

- [ ] **Specifiek**: 90% of definitions enriched with at least 2 external sources
- [ ] **Meetbaar**: < 3 second total lookup response time (including all providers)
- [ ] **Haalbaar**: 99% source attribution accuracy with automated validation
- [ ] **Relevant**: Zero privacy violations validatied by BIR beveiliging audit
- [ ] **Tijdgebonden**: Full Implementatie within Q1 2025
- [ ] **Justice-specific**: 100% compatibility with Rechtspraak ECLI lookups
- [ ] **ASTRA-compliant**: Full audit trail for all external data access

## Gebruikersverhalen Overzicht

### US-014: Modern Web Lookup Implementatie ⏳
**Status:** IN_UITVOERING
**Prioriteit:** HOOG
**Verhaalpunten:** 13
**Sprint:** current

**Gebruikersverhaal:**
As a juridische definitie author
wil ik to enrich definitions with external sources
zodat definitions have authoritative references and context

**Implementatie:**
- ModernWebLookupService in `src/services/web_lookup_service.py`
- Configuration in `config/web_lookup_defaults.yaml`
- Provider abstraction for extensibility

### US-015: Wikipedia API Integration ⏳
**Status:** IN_UITVOERING
**Prioriteit:** HOOG
**Verhaalpunten:** 5
**Sprint:** current

**Gebruikersverhaal:**
As a legal researcher
wil ik Wikipedia content integrated
zodat definitions include encyclopedic context

**Acceptatiecriteria:**
1. gegeven a legal term
   wanneer Wikipedia is queried
   dan Dutch language results are prioritized
2. gegeven Wikipedia content is retrieved
   wanneer processing for inclusion
   dan only introduction and legal sections are extracted

### US-016: SRU Legal Database Integration 📋
**Status:** Nog te bepalen
**Prioriteit:** HOOG
**Verhaalpunten:** 8
**Afhankelijkheden:** US-014

**Gebruikersverhaal:**
As a officier van justitie (OM)
wil ik access to official legal databases
zodat definitions reference authoritative legal sources

**Acceptatiecriteria:**
1. gegeven a legal term
   wanneer SRU databases are queried
   dan KB and Rechtspraak sources are searched
2. gegeven legal documents are found
   wanneer processing results
   dan ECLI numbers and case summaries are extracted

### US-017: Content Validation & Filtering 📋
**Status:** Nog te bepalen
**Prioriteit:** KRITIEK
**Verhaalpunten:** 8
**Afhankelijkheden:** US-015, US-016

**Gebruikersverhaal:**
As a Compliance Officer
wil ik all external content validatied
zodat no inappropriate or sensitive data enters the system

**Acceptatiecriteria:**
1. gegeven external content is received
   wanneer validation runs
   dan PII is detected and removed
2. gegeven content passes validation
   wanneer storing in system
   dan audit trail is aangemaakt

### US-018: Source Attribution System 📋
**Status:** Nog te bepalen
**Prioriteit:** HOOG
**Verhaalpunten:** 5
**Afhankelijkheden:** US-014

**Gebruikersverhaal:**
Als juridisch medewerker bij het OM/DJI/Rechtspraak
wil ik clear source attribution
zodat I can verify and cite references

**Acceptatiecriteria:**
1. gegeven enriched content is displayed
   wanneer viewing sources
   dan full attribution with timestamps is shown
2. gegeven multiple sources are used
   wanneer generating attribution
   dan sources are ranked by reliability

### US-019: Cache Management 📋
**Status:** Nog te bepalen
**Prioriteit:** GEMIDDELD
**Verhaalpunten:** 5
**Afhankelijkheden:** US-014

**Gebruikersverhaal:**
Als systeembeheerder binnen de justitieketen
wil ik efficient cache management
zodat Prestaties is optimal and data is fresh

**Acceptatiecriteria:**
1. gegeven external content is fetched
   wanneer storing in cache
   dan 15-minute TTL is enforced
2. gegeven cache size limits
   wanneer cache is full
   dan LRU eviction is applied

## Technical Design

### Architecture Components

```
User Request → Web Lookup Service
                    ↓
            Provider Selection
           (Wikipedia, SRU)
                    ↓
            Parallel Queries
                    ↓
            Content Validation
                    ↓
            Attribution & Filtering
                    ↓
            Cache Results
                    ↓
            Enriched Content
```

### Provider Configuration

- **Wikipedia**: Weight 0.7, Dutch language priority
- **SRU**: Weight 1.0, Legal sources priority
- **Timeout**: 5 seconds per provider
- **Cache TTL**: 15 minutes

## Afhankelijkheden

### Internal Afhankelijkheden
- **EPIC-001**: Definition generation (provides terms for lookup)
- **EPIC-002**: Validation framework (validaties enriched content)
- **EPIC-007**: Prestaties infrastructure (caching layer)

### External Afhankelijkheden
- Wikipedia API access (Dutch language endpoints)
- KB (Koninklijke Bibliotheek) SRU service
- Rechtspraak jurisprudence database API
- Justid terminology service (for term validation)

### Technical Afhankelijkheden
- Redis for distributed caching
- Content sanitization libraries
- PII detection algorithms
- Rate limiting middleware

## Risico's & Mitigaties

| Risk | Impact | Likelihood | Mitigation | Eigenaar |
|------|--------|------------|------------|-------|
| API Rate Limits | HOOG | GEMIDDELD | Redis caching, exponential backoff, quota monitoring | DevOps |
| Content Quality | GEMIDDELD | LAAG | Multi-layer validation, manual review triggers | QA Team |
| Privacy Leaks (AVG) | KRITIEK | LAAG | PII scanner, data masking, BIR audit compliance | beveiliging |
| Source Availability | GEMIDDELD | GEMIDDELD | Circuit breakers, fallback providers, health checks | SRE |
| Legal Misattribution | HOOG | LAAG | Source verification, ECLI validation, manual review | Legal |
| KB/Rechtspraak Sync | HOOG | GEMIDDELD | Daily sync jobs, Versie tracking, change alerts | Integration |

## Compliance Notities

### ASTRA vereisten
- ✅ External system integration patterns (loose coupling)
- ✅ Data quality standards (validation layer)
- ✅ beveiliging guidelines for external data (sanitization)
- ⏳ Audit trail for external lookups (implement logging)
- ⏳ Service registry integration (register providers)
- ⏳ Chain authenticatie (Justid SSO integration)

### NORA Standards
- ✅ Government data exchange standards (StUF/REST)
- ✅ Privacy protection measures (AVG compliant)
- ⏳ Source attribution vereisten (implement metadata)
- ⏳ Data retention policies (15-min cache, 90-day logs)
- ⏳ Accessibility standards (WCAG 2.1 for attributions)
- ⏳ Open standards compliance (JSON-LD for metadata)

### Justice Domain vereisten
- ⏳ Rechtspraak ECLI format support
- ⏳ OM case reference integration
- ⏳ DJI beveiliging classification respect
- ⏳ Justid terminology alignment
- ⏳ CJIB penalty term validation

## Related Epische Verhalen

- **<!-- BROKEN LINK: EPIC-008 -->**: Web Lookup Module (MERGED) - All functionality from Episch Verhaal 8 has been consoliDatumd here

## Definitie van Gereed

- [ ] Wikipedia integration complete with Dutch priority
- [ ] SRU integration complete (KB + Rechtspraak)
- [ ] Content validation geïmplementeerd with PII scanning
- [ ] Privacy filters operational (AVG compliant)
- [ ] Redis caching system deployed with monitoring
- [ ] Source attribution working with ECLI support
- [ ] Prestaties benchmarks met (< 3s total)
- [ ] BIR beveiliging review passed
- [ ] Justid terminology validation integrated
- [ ] Integration tests with justitieketen systems
- [ ] User acceptance by OM/DJI/Rechtspraak
- [ ] Documentatie compleet with examples
- [ ] Monitoring dashboards operational
- [ ] Fallback mechanisms tested

## Wijzigingslog

| Datum | Versie | Wijzigingen |
|------|---------|---------|
| 01-01-2025 | 1.0 | Episch Verhaal aangemaakt |
| 05-09-2025 | 1.x | Vertaald naar Nederlands met justitie context |
| 01-09-2025 | 1.1 | Episch Verhaal 8 merged into Episch Verhaal 3 |
| 05-09-2025 | 1.2 | Status: 30% complete |

## Gerelateerde Documentatie

- [Web Lookup Config](../../technisch/web_lookup_config.md)
- Modern Web Lookup Service: `src/services/modern_web_lookup_service.py` (implementation)
- Privacy Guidelines: See ASTRA/NORA compliance sections above

## Stakeholder Goedkeuring

- Business Eigenaar (Justid): ⏳ In afwachting
- Technisch Lead: ⏳ In afwachting
- beveiliging Officer (BIR): ⏳ In afwachting
- Privacy Officer (FG): ⏳ In afwachting
- OM Representative: ⏳ In afwachting
- Rechtspraak Architect: ⏳ In afwachting
- KB Integration Team: ⏳ In afwachting
- DJI Compliance: ⏳ In afwachting

---

*This epic is part of the DefinitieAgent project and folLAAGs ASTRA/NORA guidelines for justice domain systems.*
