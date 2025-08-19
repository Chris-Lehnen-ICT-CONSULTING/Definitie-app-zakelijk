# DefinitieAgent - Complete Architectuur Overzicht AS-IS & TO-BE

## 📊 Overzicht

### Algemene Statistieken
- **Totaal Python bestanden**: 304
- **Source modules (src/)**: 220
- **Test modules**: 72
- **Scripts/Tools**: 12
- **Entry points**: 88
- **UI Tabs werkend**: ~30%
- **Test coverage**: 11%
- **Geplande roadmap**: 16 weken

## 🏗️ AS-IS Architectuur

### ✅ Actieve & Werkende Componenten

#### 🚀 Entry Point
| Bestand | Status | Beschrijving |
|---------|---------|--------------|
| `src/main.py` | ✅ Actief | Hoofdapplicatie met Streamlit interface |

#### 🖼️ UI Componenten
| Bestand | Status | Beschrijving |
|---------|---------|--------------|
| `ui/tabbed_interface.py` | ✅ Actief | Hoofd UI controller - beheert alle tabs |
| `ui/session_state.py` | ✅ Actief | Sessie beheer - houdt gebruikersdata bij |
| `ui/components/definition_generator_tab.py` | ✅ Actief | Definitie generator - hoofdfunctionaliteit |
| `ui/components/expert_review_tab.py` | ⚠️ Deels | Review workflow - UI bestaat, backend incomplete |
| `ui/components/export_tab.py` | ⚠️ Deels | Export - alleen TXT werkt |
| `ui/components/orchestration_tab.py` | ❌ Ongebruikt | Tijdelijk uitgeschakeld - compatibility issues |
| `ui/components/web_lookup_tab.py` | ❌ Ongebruikt | Backend bestaat, UI integratie ontbreekt |

#### ⚙️ Services (Nieuwe Architectuur)
| Bestand | Status | Beschrijving |
|---------|---------|--------------|
| `services/unified_definition_generator.py` | ✅ Actief | Centrale definitie generator |
| `services/definition_orchestrator.py` | ✅ Actief | Orchestratie service |
| `services/definition_repository.py` | ✅ Actief | Repository service layer |
| `services/definition_validator.py` | ✅ Actief | Validatie service |
| `services/container.py` | ✅ Actief | Dependency injection |
| `services/service_factory.py` | ✅ Actief | Service factory met feature flags |
| `services/web_lookup_service.py` | ⚠️ Deels | Web lookup - geen UI koppeling |

#### 🗄️ Database
| Bestand | Status | Beschrijving |
|---------|---------|--------------|
| `database/definitie_repository.py` | ✅ Actief | SQLAlchemy repository |
| `database/migrate_database.py` | ⚠️ Deels | Migratie tool |

#### 🤖 AI/ML Componenten
| Bestand | Status | Beschrijving |
|---------|---------|--------------|
| `ai_toetser/modular_toetser.py` | ✅ Actief | Moderne modulaire toetser |
| `ai_toetser/json_validator_loader.py` | ✅ Actief | JSON regel loader |
| `ai_toetser/toetser.py` | ⚠️ Deels | Legacy wrapper |

#### 🛠️ Utilities
| Bestand | Status | Beschrijving |
|---------|---------|--------------|
| `utils/smart_rate_limiter.py` | ✅ Actief | Intelligente rate limiting |
| `utils/integrated_resilience.py` | ✅ Actief | Retry & circuit breakers |
| `utils/cache.py` | ✅ Actief | In-memory caching |
| `utils/async_api.py` | ✅ Actief | Async API utilities |

### ❌ Ongebruikte/Orphaned Bestanden

#### Domain Modules (mogelijk ongebruikt)
- `domain/context/organisatie_wetten.py` - Niet geïmporteerd
- `domain/juridisch/patronen.py` - Niet in gebruik
- `domain/linguistisch/pluralia_tantum.py` - Orphaned

#### Dubbele Toetsregels (100+ bestanden!)
- `toetsregels/regels/*.py` - 50+ Python bestanden (overbodig - JSON versies bestaan)
- `toetsregels/validators/*.py` - 50+ duplicate validators (overbodig)

#### Legacy Modules
- `voorbeelden/async_voorbeelden.py` - Vervangen door unified versie
- `voorbeelden/cached_voorbeelden.py` - Vervangen door unified versie
- `web_lookup/` - Lege directory, services verplaatst

### 🧪 Test Suite Status
| Test Type | Status | Coverage |
|-----------|---------|----------|
| Unit tests | ⚠️ Deels | Veel gefaald door refactoring |
| Integration tests | ⚠️ Deels | Update nodig voor nieuwe architectuur |
| Service tests | ✅ Actief | Nieuwe tests voor service laag |
| Performance tests | ⚠️ Deels | Beperkt aanwezig |
| Security tests | ❌ Ontbreekt | Nog te implementeren |

## 🚀 TO-BE Architectuur

### 📅 Roadmap Overzicht (16 weken)

#### Phase 1: Foundation (Week 1-4) - Status: 30% voltooid
- [ ] WAL mode voor SQLite implementeren
- [ ] Unificeer configuratie systeem
- [ ] Repair test suite (target: 30% working)
- [ ] Setup CI/CD pipeline basis
- [ ] Basic authenticatie toevoegen

#### Phase 2: Service Decomposition (Week 5-8) - Status: 10% voltooid
- [ ] Extract PromptOptimizer service
- [ ] Implement ValidationOrchestrator
- [ ] Create ContentEnrichmentService
- [ ] Implement CacheManager
- [ ] Complete Facade pattern implementatie
- [ ] Elimineer God Object pattern

#### Phase 3: Feature Completion (Week 9-12) - Status: 0% voltooid
- [ ] Web Lookup UI Integration
- [ ] Prompt Viewer implementeren
- [ ] Aangepaste Definitie templates
- [ ] Developer Tools activeren
- [ ] Expert Review workflow
- [ ] Orchestratie engine
- [ ] Content enrichment service

#### Phase 4: Optimization & Scale (Week 13-16) - Status: 0% voltooid
- [ ] Redis caching implementatie
- [ ] Prompt optimization (<10k chars)
- [ ] Async processing verbeteren
- [ ] Database connection pooling
- [ ] Multi-tenant support
- [ ] Advanced monitoring
- [ ] PostgreSQL migration
- [ ] Horizontal scaling

### 📋 Epics & User Stories

#### EPIC-001: Database Infrastructure (7 story points)
| Story | Points | Beschrijving | Nieuwe Bestanden |
|-------|---------|--------------|------------------|
| STORY-001-01 | 3 | Enable SQLite WAL Mode | `database/wal_enabler.py` |
| STORY-001-02 | 2 | Fix Connection Pooling | `database/connection_pool.py` |
| STORY-001-03 | 2 | Database UTF-8 Encoding | - |

#### EPIC-002: Web Lookup Module (10 story points)
- Backend implementatie bestaat ✅
- UI integratie nodig ❌
- End-to-end testing nodig ❌

**Te bouwen:**
- `ui/components/web_lookup_tab.py` (activeren)

#### EPIC-003: UI Quick Wins (8 story points)
- Widget key fixes
- Loading states
- Error handling
- Responsive design

#### EPIC-004: Content Enrichment (11 story points)
**Nieuwe bestanden:**
- `services/content_enrichment_service.py`
- `services/synonym_service.py`
- `services/context_aggregator.py`

#### EPIC-005: Tab Activation (21 story points) - GROOTSTE EPIC!

**Te activeren tabs:**
| Tab | Beschrijving | Nieuw Bestand |
|-----|--------------|---------------|
| History Tab | Version history, change tracking | `ui/components/history_tab.py` ✅ |
| Quality Control Tab | Validation dashboard | `ui/components/quality_control_tab.py` ✅ |
| Expert Review Tab | Review workflow | Bestaand - backend nodig |
| Export Tab | Multiple formats | Bestaand - uitbreiden |
| External Sources Tab | Source configuration | `ui/components/external_sources_tab.py` ✅ |
| Monitoring Tab | Real-time metrics | `ui/components/monitoring_tab.py` ✅ |
| Orchestration Tab | Workflow designer | `ui/components/orchestration_designer.py` 🆕 |

#### EPIC-006: Prompt Optimization (10 story points)
**Nieuwe bestanden:**
- `services/prompt_optimizer.py`
- `services/token_counter.py`
- `services/context_pruner.py`

#### EPIC-007: Test Suite Restoration (18 story points)
- Unit test coverage naar 80%
- Integration tests
- Performance tests
- Security tests

### 🆕 Nieuwe Services TO-BE

#### Service Decomposition
| Service | Bestand | Beschrijving |
|---------|---------|--------------|
| PromptOptimizer | `services/prompt_optimizer.py` | Token reductie naar <10k |
| ValidationOrchestrator | `services/validation_orchestrator.py` | Centrale validatie orchestratie |
| ContentEnrichmentService | `services/content_enrichment_service.py` | Synoniemen, antoniemen, context |
| CacheManager | `services/cache_manager.py` | Redis distributed caching |
| MonitoringService | `services/monitoring_service.py` | Real-time metrics & alerting |

#### Infrastructure Services
| Service | Bestand | Beschrijving |
|---------|---------|--------------|
| AuthenticationService | `auth/authentication.py` | Basic auth implementatie |
| AuthorizationService | `auth/authorization.py` | RBAC implementatie |
| APISecurityService | `security/api_security.py` | API key management |

#### Export Services
| Service | Bestand | Beschrijving |
|---------|---------|--------------|
| ExcelExporter | `export/export_excel.py` | Excel export met formatting |
| PDFExporter | `export/export_pdf.py` | PDF templates |
| JSONLDExporter | `export/export_jsonld.py` | Linked data export |
| ExportAPI | `export/export_api.py` | REST API endpoints |

### 🎯 Success Criteria

| Criterium | AS-IS | TO-BE | Verbetering |
|-----------|-------|-------|-------------|
| **Performance** | 8-12 sec | <5 sec | 60% sneller |
| **UI Completeness** | 30% tabs | 100% tabs | 70% meer functionaliteit |
| **Test Coverage** | 11% | 80% | 7x betere coverage |
| **API Kosten** | Hoog | -70% | Significante besparing |
| **Concurrent Users** | 1 | 10+ | 10x schaalbaarheid |
| **Uptime** | 95% | 99% | Enterprise-ready |

### 🚨 Kritieke Issues

| Issue | Prioriteit | Impact | Oplossing |
|-------|------------|---------|-----------|
| Database locks | 🔴 Hoog | Multi-user blocking | WAL mode implementeren |
| Widget key duplicates | 🟠 Medium | UI crashes | Unique keys refactoring |
| Memory leaks | 🟠 Medium | Performance degradatie | Memory profiling & fixes |
| UTF-8 encoding | 🟡 Laag | Data integriteit | Database charset fix |
| Toetsregel ontbreekt (INT-05) | 🟠 Medium | Validatie incompleet | Regel toevoegen |

### 📦 Geconsolideerde Backlog

#### Hoge Prioriteit
- AI & Toetsing verbetering
- ARAI regel implementaties
- UI synchronisatie fixes
- Field UI approval systeem
- Database performance

#### Medium Prioriteit
- Excel/PDF export functionaliteit
- JSONL download
- Voorbeeldzinnen bewerking
- Synoniemen expansie
- Bronnen beheer systeem

#### Lage Prioriteit
- Log viewer implementatie
- RAG implementatie
- Smoke test CI/CD
- UI paginering
- Multi-select functionaliteit

### 💡 Aanbevelingen

1. **Verwijder dubbele toetsregels**: 100+ Python bestanden in `toetsregels/regels/` en `toetsregels/validators/` zijn overbodig
2. **Archiveer ongebruikte domain modules**: `domain/context/`, `domain/juridisch/`, `domain/linguistisch/` worden niet gebruikt
3. **Cleanup legacy voorbeelden**: `async_voorbeelden.py` en `cached_voorbeelden.py` zijn vervangen
4. **Prioriteer UI tab activatie**: 7 tabs wachten op implementatie - grootste gebruikerswaarde
5. **Implementeer WAL mode direct**: Lost database lock issues op voor multi-user
6. **Start met basis authenticatie**: Security is kritiek voor productie
7. **Focus op performance**: Response tijd van 8-12s naar <5s is hoofddoel
8. **Test coverage prioriteit**: Van 11% naar minimaal 50% in eerste fase

### 💰 Investering & ROI

- **Geschatte Investment**: 400-600 development uren
- **Team grootte**: 2-3 developers
- **Doorlooptijd**: 16 weken
- **ROI verwachting**:
  - 60% performance verbetering
  - 70% onderhoudskosten reductie
  - 70% API kosten reductie
  - 10x betere schaalbaarheid
- **Break-even**: 6-8 maanden na go-live

### 🔑 Next Steps

1. **Week 1-2: Emergency Fixes**
   - Fix import paths
   - Implement WAL mode
   - Fix widget duplicates
   - Add basic auth

2. **Week 3-4: Testing & Config**
   - Unify config system
   - Repair test suite (30% target)
   - Setup CI/CD basis
   - Document dev setup

3. **Week 5-8: Service Extraction**
   - Complete service decomposition
   - Implement facade pattern
   - Increase test coverage to 50%
   - Performance profiling

4. **Week 9-12: UI Completion**
   - Activate all 7 remaining tabs
   - Integrate web lookup with UI
   - Implement content enrichment
   - User acceptance testing

5. **Week 13-16: Scale & Deploy**
   - Redis caching
   - PostgreSQL migration
   - Kubernetes deployment
   - Production go-live

## 📊 Technische Schuld Overzicht

### Te verwijderen bestanden (150+)
- `toetsregels/regels/*.py` - 50+ bestanden
- `toetsregels/validators/*.py` - 50+ bestanden
- `domain/context/*.py` - 10+ bestanden
- `domain/juridisch/*.py` - 10+ bestanden
- `domain/linguistisch/*.py` - 10+ bestanden
- Legacy voorbeelden - 5+ bestanden
- Lege directories - 3+

### Code Quality Metrics
- **Huidige staat**: C+ (veel duplicatie, God objects)
- **Target staat**: B+ (clean architecture, SOLID)
- **Cyclomatic complexity**: Hoog → Medium
- **Code duplicatie**: 30% → <10%
- **Test coverage**: 11% → 80%

Dit document geeft een volledig overzicht van de AS-IS en TO-BE situatie van de DefinitieAgent applicatie, inclusief alle Python bestanden, hun status, en wat er nog gebouwd moet worden.
