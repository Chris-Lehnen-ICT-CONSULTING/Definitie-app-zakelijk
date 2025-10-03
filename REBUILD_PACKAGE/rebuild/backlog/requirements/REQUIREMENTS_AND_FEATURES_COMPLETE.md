---
canonical: false
status: archived
owner: documentation-team
last_verified: 11-09-2025
applies_to: definitie-app@current
note: Deze pagina is gearchiveerd; gebruik de individuele REQ-bestanden en dashboards.
---

# DefinitieAgent - Complete Vereisten & Features Document (GEARCHIVEERD)

> Let op: Dit document was een ‘living document’ tijdens de vroege fase. De canonieke bron voor vereisten is nu per‑bestand in `docs/backlog/requirements/REQ-XXX.md`, met overzichten via de Traceability Matrix en dashboards in `docs/backlog/dashboard/`. Gebruik dit document enkel als historisch overzicht.

## 📋 Document Informatie
- **Laatste update**: 19-08-2025 (historisch)
- **Status**: Gearchiveerd (zie opmerking hierboven)
- **Doel**: Historisch overzicht; actuele bron is per‑REQ + dashboards

---

## 🎯 Project Overzicht

### Missie
DefinitieAgent is een AI-powered tool voor het genereren van hoogwaardige Nederlandse definities voor juridische en overheidscontexten, gebruik makend van GPT-4 en 46 kwaliteitsregels.

### Kernwaarden
- **Kwaliteit**: Elke definitie moet voldoen aan strenge kwaliteitsnormen
- **Consistentie**: Uniforme definities binnen organisaties
- **Efficiëntie**: Van dagen naar minuten voor definitie creatie
- **Transparantie**: Inzichtelijke validatie en bronvermelding

---

## 📊 Feature Status Overzicht

### Completion Metrics
- **Totaal Features**: 87
- **Compleet**: 23 (26%)
- **In Progress**: 12 (14%)
- **Niet Gestart**: 52 (60%)

### Per Categorie
| Categorie | Compleet | In Progress | Niet Gestart | Totaal |
|-----------|----------|-------------|--------------|---------|
| Core Functionaliteit | 15 | 3 | 5 | 23 |
| UI/UX | 3 | 2 | 25 | 30 |
| Export/Import | 1 | 2 | 7 | 10 |
| Beveiliging | 0 | 1 | 5 | 6 |
| Prestaties | 2 | 3 | 5 | 10 |
| Infrastructure | 2 | 1 | 5 | 8 |

---

## 🚀 Epische Verhalen & Gebruikersverhalen

### Episch Verhaal 1: Basis Definitie Generatie ✅ (90% Compleet)

#### Gebruikersverhalen
| ID | Story | Status | Acceptatiecriteria | Notes |
|----|-------|--------|-------------------|-------|
| DEF-001 | Als gebruiker wil ik een begrip kunnen invoeren | ✅ Compleet | - Min 3, max 100 karakters<br>- Validatie op input<br>- Geen speciale tekens | Werkend in productie |
| DEF-002 | Als gebruiker wil ik context kunnen selecteren | ✅ Compleet | - Organisatorische context<br>- Juridische context<br>- Wettelijke basis | Multi-select mogelijk |
| DEF-003 | Als gebruiker wil ik een AI-gegenereerde definitie krijgen | ✅ Compleet | - Response < 15 sec<br>- Minimaal 80% kwaliteitsscore<br>- Foutafhandeling | GPT-4 integratie |
| DEF-004 | Als gebruiker wil ik de kwaliteitsscore zien | ✅ Compleet | - Score 0-100<br>- Kleurcodering<br>- Details per regel | 46 toetsregels actief |
| DEF-005 | Als gebruiker wil ik duplicate check | 🔄 In Progress | - Check voor generatie<br>- Similarity score<br>- Suggesties tonen | Backend klaar, UI ontbreekt |

### Episch Verhaal 2: Kwaliteitstoetsing ✅ (85% Compleet)

#### Gebruikersverhalen
| ID | Story | Status | Acceptatiecriteria | Notes |
|----|-------|--------|-------------------|-------|
| KWA-001 | Als gebruiker wil ik gedetailleerde validatie zien | ✅ Compleet | - Per regel resultaat<br>- Ernst aangeven<br>- Uitleg bij fout | 45/46 regels werkend |
| KWA-002 | Als gebruiker wil ik suggesties voor verbetering | ✅ Compleet | - Concrete suggesties<br>- Direct toepasbaar<br>- Prioriteit aangeven | AI-powered suggesties |
| KWA-003 | Als gebruiker wil ik iteratieve verbetering | ✅ Compleet | - Max 3 iteraties<br>- Score verbetering<br>- History tracking | IterativeDefinitionAgent |
| KWA-004 | Als gebruiker wil ik custom toetsregels | ❌ Niet Gestart | - UI voor regel creatie<br>- Validatie syntax<br>- Test mogelijkheid | In backlog |

### Episch Verhaal 3: Content Verrijking 🔄 (30% Compleet)

#### Gebruikersverhalen
| ID | Story | Status | Acceptatiecriteria | Notes |
|----|-------|--------|-------------------|-------|
| ENR-001 | Als gebruiker wil ik synoniemen zien | ✅ Compleet | - Min 3 synoniemen<br>- Context-aware<br>- Kwaliteitscheck | Fixed: nu 5 items |
| ENR-002 | Als gebruiker wil ik antoniemen zien | ✅ Compleet | - Min 2 antoniemen<br>- Relevantie check<br>- Optional field | Fixed: nu 5 items |
| ENR-003 | Als gebruiker wil ik voorbeeldzinnen | 🔄 In Progress | - 3-5 zinnen<br>- Verschillende contexten<br>- Begrijpelijk | Backend klaar |
| ENR-004 | Als gebruiker wil ik praktijkvoorbeelden | ❌ Niet Gestart | - Real-world cases<br>- Sector specifiek<br>- Bronvermelding | UI ontbreekt |
| ENR-005 | Als gebruiker wil ik tegenvoorbeelden | ❌ Niet Gestart | - Wat het NIET is<br>- Veelvoorkomende fouten<br>- Helder onderscheid | Template bestaat |
| ENR-006 | Als gebruiker wil ik toelichting | ❌ Niet Gestart | - Uitgebreide uitleg<br>- Achtergrond info<br>- Bronnen | Prompt bestaat |

### Episch Verhaal 4: User Interface ❌ (30% Compleet)

#### Gebruikersverhalen - Tabs
| ID | Story | Status | Acceptatiecriteria | Notes |
|----|-------|--------|-------------------|-------|
| UI-001 | Als gebruiker wil ik definitie generator tab | ✅ Compleet | - Invoervelden<br>- Generate knop<br>- Resultaat display | Hoofdtab werkend |
| UI-002 | Als gebruiker wil ik history tab | ✅ Compleet | - Alle definities<br>- Filters<br>- Zoeken | Basis functionaliteit |
| UI-003 | Als gebruiker wil ik export tab | ✅ Compleet | - TXT export<br>- Template keuze<br>- Download | Alleen TXT werkend |
| UI-004 | Als gebruiker wil ik web lookup tab | ❌ Niet Gestart | - Externe bronnen<br>- Resultaten tonen<br>- Bron validatie | Tab leeg |
| UI-005 | Als gebruiker wil ik expert review tab | ❌ Niet Gestart | - Review workflow<br>- Commentaar<br>- Goedkeuring | Backend ontbreekt |
| UI-006 | Als gebruiker wil ik prompt viewer tab | ❌ Niet Gestart | - Toon prompts<br>- Debug info<br>- Token count | Planned |
| UI-007 | Als gebruiker wil ik monitoring tab | ❌ Niet Gestart | - Prestaties metrics<br>- API kosten<br>- Usage stats | Dashboard ontbreekt |
| UI-008 | Als gebruiker wil ik management tab | ❌ Niet Gestart | - User management<br>- Settings<br>- Backups | Admin functionaliteit |
| UI-009 | Als gebruiker wil ik orchestration tab | ❌ Niet Gestart | - Bulk operations<br>- Scheduling<br>- Workflows | Enterprise feature |
| UI-010 | Als gebruiker wil ik quality control tab | 🔄 In Progress | - Toetsregel beheer<br>- Statistieken<br>- Configuratie | Deels werkend |

#### Gebruikersverhalen - UI Elements
| ID | Story | Status | Acceptatiecriteria | Notes |
|----|-------|--------|-------------------|-------|
| UI-011 | Als gebruiker wil ik datum voorstel veld | ❌ Niet Gestart | - Datepicker<br>- Validatie<br>- Opslaan | Metadata veld |
| UI-012 | Als gebruiker wil ik voorgesteld door veld | ❌ Niet Gestart | - Tekstveld<br>- Autocomplete<br>- Historie | Metadata veld |
| UI-013 | Als gebruiker wil ik ketenpartners selectie | ❌ Niet Gestart | - Multi-select<br>- 8 opties<br>- Opslaan | ZM, DJI, KMAR, etc |
| UI-014 | Als gebruiker wil ik ontologische score zien | 🔄 In Progress | - 4 categorieën<br>- Visualisatie<br>- Uitleg | Backend calculation klaar |
| UI-015 | Als gebruiker wil ik voorkeursterm selectie | ❌ Niet Gestart | - Uit synoniemen<br>- Radio buttons<br>- Opslaan | Bij synoniemen sectie |

### Episch Verhaal 5: Export & Import ❌ (10% Compleet)

#### Gebruikersverhalen
| ID | Story | Status | Acceptatiecriteria | Notes |
|----|-------|--------|-------------------|-------|
| EXP-001 | Als gebruiker wil ik TXT export | ✅ Compleet | - Platte tekst<br>- Template based<br>- UTF-8 | Werkend |
| EXP-002 | Als gebruiker wil ik Word export | ❌ Niet Gestart | - .docx format<br>- Styling behoud<br>- Template | python-docx needed |
| EXP-003 | Als gebruiker wil ik PDF export | ❌ Niet Gestart | - A4 format<br>- Logo mogelijk<br>- Watermark optie | ReportLab needed |
| EXP-004 | Als gebruiker wil ik Excel export | ❌ Niet Gestart | - Filters<br>- Grafieken<br>- Multi-sheet | Bulk export |
| EXP-005 | Als gebruiker wil ik JSON export | 🔄 In Progress | - Valid JSON<br>- Schema compliant<br>- Streaming | Backend ready |
| IMP-001 | Als gebruiker wil ik CSV import | ❌ Niet Gestart | - Bulk import<br>- Validatie<br>- Error rapport | Template needed |
| IMP-002 | Als gebruiker wil ik document upload | 🔄 In Progress | - PDF/Word/TXT<br>- Context extractie<br>- Deduplicatie | DocumentProcessor exists |

### Episch Verhaal 6: Beveiliging & Auth ❌ (0% Compleet)

#### Gebruikersverhalen
| ID | Story | Status | Acceptatiecriteria | Notes |
|----|-------|--------|-------------------|-------|
| SEC-001 | Als admin wil ik gebruikers authenticatie | ❌ Niet Gestart | - Login/logout<br>- Password policy<br>- Session timeout | Critical missing |
| SEC-002 | Als admin wil ik role-based access | ❌ Niet Gestart | - Admin/User/Viewer<br>- Permissions<br>- Audit trail | RBAC needed |
| SEC-003 | Als admin wil ik API key management | ❌ Niet Gestart | - Generate keys<br>- Revoke access<br>- Usage limits | For external access |
| SEC-004 | Als gebruiker wil ik data encryptie | ❌ Niet Gestart | - At rest<br>- In transit<br>- Key rotation | SQLite encryption |
| SEC-005 | Als admin wil ik audit logging | ❌ Niet Gestart | - Alle acties<br>- Timestamps<br>- User tracking | Compliance |

### Episch Verhaal 7: Prestaties & Scaling 🔄 (20% Compleet)

#### Gebruikersverhalen
| ID | Story | Status | Acceptatiecriteria | Notes |
|----|-------|--------|-------------------|-------|
| PER-001 | Als gebruiker wil ik <5 sec response | ❌ Niet Gestart | - 95 percentile<br>- Monitoring<br>- Alerts | Nu 8-12 sec |
| PER-002 | Als gebruiker wil ik caching | 🔄 In Progress | - Redis ready<br>- Hit rate >70%<br>- TTL config | Basic in-memory nu |
| PER-003 | Als admin wil ik horizontal scaling | ❌ Niet Gestart | - Load balancing<br>- Session affinity<br>- Health checks | Kubernetes ready |
| PER-004 | Als gebruiker wil ik async processing | 🔄 In Progress | - Queue based<br>- Progress updates<br>- Retry logic | Celery planned |
| PER-005 | Als admin wil ik database optimization | ✅ Compleet | - WAL mode<br>- Indexes<br>- Vacuum | SQLite optimized |

### Episch Verhaal 8: Web Lookup Module 🔄 (10% Compleet)

> Archief-notitie: Dit episch verhaal is in de actuele backlog ondergebracht bij `EPIC-003` (Content Verrijking & Web Lookup). Gebruik EPIC-003 voor planning en status.

#### Gebruikersverhalen
| ID | Story | Status | Acceptatiecriteria | Notes |
|----|-------|--------|-------------------|-------|
| WEB-001 | Als gebruiker wil ik externe bronnen zoeken | 🔄 In Progress | - Multiple sources<br>- Relevantie ranking<br>- Caching | 5 broken implementations |
| WEB-002 | Als gebruiker wil ik bron validatie | ❌ Niet Gestart | - Authority check<br>- Datum check<br>- Quality score | Planned |
| WEB-003 | Als gebruiker wil ik automatische verrijking | ❌ Niet Gestart | - Context toevoegen<br>- Merge results<br>- Deduplicatie | AI-powered |
| WEB-004 | Als gebruiker wil ik bron attributie | ❌ Niet Gestart | - Citaten<br>- Links<br>- Licentie info | Legal vereiste |

### Episch Verhaal 9: Advanced Features ❌ (5% Compleet)

#### Gebruikersverhalen
| ID | Story | Status | Acceptatiecriteria | Notes |
|----|-------|--------|-------------------|-------|
| ADV-001 | Als gebruiker wil ik bulk operations | ❌ Niet Gestart | - Multi-select<br>- Batch processing<br>- Progress bar | Enterprise |
| ADV-002 | Als gebruiker wil ik version control | ❌ Niet Gestart | - Historie<br>- Diff view<br>- Rollback | Git-like |
| ADV-003 | Als gebruiker wil ik collaboration | ❌ Niet Gestart | - Comments<br>- Mentions<br>- Notifications | Teams feature |
| ADV-004 | Als gebruiker wil ik API access | 🔄 In Progress | - REST endpoints<br>- Documentation<br>- Rate limiting | FastAPI migration |
| ADV-005 | Als gebruiker wil ik custom workflows | ❌ Niet Gestart | - Drag & drop<br>- Conditions<br>- Actions | Werkstroom engine |

---

## 🎯 Non-Functional Vereisten

### Prestaties Vereisten
| Requirement | Current | Target | Prioriteit |
|-------------|---------|---------|----------|
| Response Time | 8-12s | <5s | High |
| Concurrent Users | 1 | 10+ | High |
| Uptime | 95% | 99.9% | Medium |
| Database Size | <100MB | <10GB | Medium |
| Memory Usage | 2GB | <4GB | Low |

### Quality Vereisten
| Requirement | Current | Target | Prioriteit |
|-------------|---------|---------|----------|
| Test Coverage | 11-40% | >80% | High |
| Code Quality Score | C | A | Medium |
| Documentation | 40% | 100% | Medium |
| API Response Consistency | 90% | 99% | High |
| Error Rate | 5% | <1% | High |

### Beveiliging Vereisten
| Requirement | Status | Prioriteit | Notes |
|-------------|--------|----------|-------|
| Authentication | ❌ Missing | Critical | No auth system |
| Authorization | ❌ Missing | Critical | No RBAC |
| Data Encryption | ❌ Missing | High | SQLite plain text |
| Input Validation | ✅ Basic | Medium | Some validation |
| OWASP Compliance | ❌ No | High | Beveiliging audit needed |
| API Beveiliging | ❌ No | High | No rate limiting |

### Usability Vereisten
| Requirement | Status | Target | Prioriteit |
|-------------|--------|---------|----------|
| UI Responsiveness | ✅ Good | Excellent | Medium |
| Mobile Support | ❌ No | Responsive | Low |
| Accessibility | ❌ No | WCAG 2.1 AA | Medium |
| Multi-language | ❌ No | NL/EN | Low |
| Help Documentation | ❌ No | Complete | High |

---

## 📈 Technical Specifications

### Current Architecture
- **Framework**: Streamlit (monolithic)
- **Database**: SQLite (single file)
- **AI Model**: OpenAI GPT-4
- **Language**: Python 3.11
- **Uitrol**: Single instance
- **Code Usage**: 35% actief, 65% ongebruikt (119/222 files)

### Identified Architecture Issues (Augustus 2025)
| Issue | Impact | Prioriteit | Solution |
|-------|--------|----------|----------|
| Feedback integration broken | 40% rejection rate | HOOG | Fix prompt_builder to use feedback_history |
| CON-01 violations | Quality issues | HOOG | Implement implicit context handling |
| Duplicate validation rules | 91 files (46 duplicates) | GEMIDDELD | Consolidate to shared implementation |
| No caching | 8-12s response time | HOOG | Implement Redis cache layer |
| 65% unused code | Maintenance burden | GEMIDDELD | Activate existing microservice components |

### Target Architecture
- **Framework**: FastAPI (microservices)
- **Database**: PostgreSQL (clustered)
- **Cache**: Redis
- **Queue**: RabbitMQ/Celery
- **Container**: Docker/Kubernetes
- **Monitoring**: Prometheus/Grafana

### Ready-to-Activate Components (Ongebruikt)
| Component | Location | Status | Purpose |
|-----------|----------|--------|---------|
| Beveiliging Middleware | `security/security_middleware.py` | 100% Complete | Threat detection, rate limiting |
| A/B Testen Framework | `services/ab_testing_framework.py` | Complete | Feature rollout, metrics |
| Config Manager | `config/config_manager.py` | Complete | Centralized configuration |
| Async API Layer | `utils/async_api.py` | Complete | Async request handling |
| 46 Validators | `toetsregels/validators/` | Complete (duplicated) | Validation rules |

### Integration Points
| System | Purpose | Status | Prioriteit |
|--------|---------|--------|----------|
| OpenAI API | Definition generation | ✅ Active | Critical |
| Ketenpartner APIs | Data exchange | ❌ Planned | High |
| Document Services | PDF/Word generation | ❌ Planned | Medium |
| Authentication Provider | SSO/LDAP | ❌ Planned | High |
| Monitoring Services | APM/Logs | ❌ Planned | Medium |

---

## 🗓️ Implementatie Roadmap

### Phase 0: Quality First (Weeks 1-2) - NEW PRIORITY
- [ ] Fix feedback integration in prompt_builder
- [ ] Implement implicit context handling (CON-01)
- [ ] Enable preventive validation
- [ ] Achieve 90% first-time-right target
- [ ] Consolidate duplicate validation rules

### Phase 1: Foundation (Weeks 3-6) - Updated
- [x] Fix critical bugs
- [x] Stabilize core features
- [ ] Activate unused security middleware
- [ ] Implement authentication
- [ ] Fix all UI tabs
- [ ] Complete test suite

### Phase 2: Enhancement (Weeks 5-8)
- [ ] Content enrichment features
- [ ] Export functionality
- [ ] Web lookup integration
- [ ] Prestaties optimization
- [ ] Beveiliging hardening

### Phase 3: Scale (Weeks 9-12)
- [ ] Microservices migration
- [ ] Container deployment
- [ ] Monitoring setup
- [ ] Load testing
- [ ] Documentation

### Phase 4: Enterprise (Weeks 13-16)
- [ ] Multi-tenant support
- [ ] Advanced workflows
- [ ] API marketplace
- [ ] Partner integrations
- [ ] Production deployment

---

## 📊 Success Metrics

### Key Prestaties Indicators (KPIs)
| Metric | Current | Target | Deadline |
|--------|---------|---------|----------|
| First-Time-Right | 60% | 90% | Week 2 (Prioriteit!) |
| Feature Completion | 26% | 100% | Q4 2025 |
| Test Coverage | 11% | 80% | Q3 2025 |
| Response Time | 8-12s | <3s | Q3 2025 |
| Code Utilization | 35% | 80% | Q4 2025 |
| User Satisfaction | Unknown | >4.5/5 | Q4 2025 |
| API Uptime | 95% | 99.9% | Q4 2025 |

### Definition of Done
- [ ] Feature geïmplementeerd according to acceptatiecriteria
- [ ] Unit tests written (>80% coverage)
- [ ] Integration tests passed
- [ ] Documentation updated
- [ ] Code reviewed and approved
- [ ] Prestaties benchmarks met
- [ ] Beveiliging scan passed
- [ ] Deployed to staging
- [ ] User acceptance testing passed
- [ ] Deployed to production

---

## 📋 Backlog Items

### BLG-CLN-001: Intelligent Definitie Opschoning Systeem
- **Status**: 📋 Todo
- **Prioriteit**: 🔴 Hoog
- **Geschatte Effort**: 8-16 uur
- **aangemaakt**: 25-08-2025
- **Aanvrager**: Code Debugger (via gebruiker feedback)

#### Probleemstelling
Het huidige opschoningssysteem is gebaseerd op een statische lijst van verboden woorden. Dit vereist constant onderhoud en mist nieuwe variaties.

#### Voorgestelde Oplossing
1. **AI-Gedreven Opschoning**: Gebruik GPT OM intelligent op te schonen volgens Nederlandse wetgevingstechniek
2. **Pattern-Based Detectie**: Grammaticale patterns i.p.v. woorden
3. **Hybride Aanpak**: Combineer rules met AI fallback

#### Acceptatiecriteria
- Geen handmatige updates meer nodig voor nieuwe koppelwerkwoorden
- 95%+ success rate op definitie opschoning
- Backward compatible met bestaande systeem
- Max 2 seconden voor opschoning

---


### SMART Acceptatiecriteria

- **Specifiek:** [Exact gedrag dat moet worden gerealiseerd]
- **Meetbaar:**
  - Response tijd: < 200ms voor UI acties
  - Processing tijd: < 5 seconden voor generatie
  - Success rate: > 95% voor validaties
- **Acceptabel:** Haalbaar binnen huidige architectuur
- **Relevant:** Direct gerelateerd aan gebruikersbehoefte
- **Tijdgebonden:** Gerealiseerd binnen huidige sprint


## 🔄 Change Log

### Versie 1.0 (Current)
- Basic definition generation
- Simple validation
- Text export
- 3 working tabs

### Versie 2.0 (Planned Q2 2024)
- All features geïmplementeerd
- Microservices architecture
- Full security implementation
- Enterprise ready

---

## 📞 Stakeholders

### Product Eigenaar
- Verantwoordelijk voor prioritering
- Acceptatie criteria bepalen
- Sprint planning

### Development Team
- Feature implementatie
- Testen
- Documentation

### Users
- Juridische professionals
- Beleidsmedewerkers
- Ketenpartners (OM, ZM, DJI, etc.)

### Management
- Budget approval
- Resource allocation
- Strategic direction


### Compliance Referenties

- **ASTRA Controls:**
  - ASTRA-QUA-001: Kwaliteitsborging
  - ASTRA-SEC-002: Beveiliging by Design
- **NORA Principes:**
  - NORA-BP-07: Herbruikbaarheid
  - NORA-BP-12: Betrouwbaarheid
- **GEMMA Referenties:**
  - GEMMA-ARC-03: Architectuur patterns
- **Justice Sector:**
  - DJI/OM integratie vereisten
  - Rechtspraak compatibiliteit
