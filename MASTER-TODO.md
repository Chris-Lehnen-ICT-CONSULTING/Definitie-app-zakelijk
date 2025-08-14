# 🎯 MASTER TODO - DefinitieAgent naar Productie

**Dit is HET ENIGE document voor wat er moet gebeuren**  
*Alle andere planning documenten zijn DEPRECATED*

**Laatste Update**: 2025-01-14 (v3.1 - Web Lookup ✅ + Service Architecture 87%)  
**Deadline**: Flexibel - focus op werkende kernfuncties  
**Status**: 20% compleet  
**Filosofie**: Belangrijkste features eerst, timeline is indicatief

> **UPDATE v3**: Items met 🆕 zijn toegevoegd uit gap analyse ONTBREKENDE-FUNCTIONALITEITEN.md
> **UPDATE v3.1**: Web Lookup Module volledig gerefactored, Service Architecture 85%→87%

## 🔴 KRITIEK - Blockers voor Productie (Week 1-2)

### 1. Service Refactoring Afmaken
**Status**: 87% compleet  
**Prioriteit**: EERST - Foundation voor alles
**Nog te doen**:
- [x] WebLookupService geïmplementeerd met DI
- [ ] ExamplesService consolideren
- [ ] Feature flags volledig implementeren
- [ ] Legacy code cleanup (na verificatie)
- [ ] Performance profiling nieuwe services
- [ ] Documentatie updaten voor overige services
**Deadline**: Week 1 - Maandag/Dinsdag

### 2. Database Concurrent Access & UTF-8
**Probleem**: SQLite locks bij 2+ gebruikers  
**Oplossing**: 
```python
# In database/definitie_repository.py
- [ ] Implementeer WAL mode
- [ ] Add connection pooling  
- [ ] Test met 10 concurrent users
```
**Deadline**: Week 1

### 3. Web Lookup Module ✅
**Status**: COMPLEET
**Oplossing**:
```python
# Geconsolideerd naar services/web_lookup_service.py
- [x] 5 bestaande versies geanalyseerd
- [x] Unified WebLookupService gemaakt
- [x] UTF-8 encoding gefixed
- [x] Rate limiting toegevoegd (10 req/min per bron)
- [x] Caching geïmplementeerd (1 uur TTL)
- [x] Tests geschreven
- [x] Documentatie bijgewerkt
```
**Voltooid**: Week 1

### 4. Test Infrastructure & Failing Tests
**Probleem**: Import paths broken + 7 orchestrator tests failing  
**Oplossing**:
```python
# EERST infrastructure
- [ ] Fix import paths in alle test files
- [ ] Create test fixtures voor common data
- [ ] Setup test database
# DAN fixes
- [ ] Fix async mock issues
- [ ] Update interface tests
- [ ] Ensure 100% tests passing
```
- [ ] Basic CI/CD setup (GitHub Actions)
**Deadline**: Week 1

### 5. Definitie Generatie Perfectie
**Probleem**: Kernfunctie moet 100% betrouwbaar zijn
**Oplossing**:
```python
# KRITIEK: temperature = 0 voor consistentie
- [ ] Zet GPT temperature naar 0 (niet 0.7)
- [ ] Optimaliseer prompt voor Nederlandse juridische definities
- [ ] Test output consistentie (10x zelfde input = zelfde output)
- [ ] Implementeer fallback bij API failures
```
**Deadline**: Week 1-2

### 6. 46 Toetscriteria Verbetering
**Probleem**: Alle toetsregels moeten perfect werken
**Oplossing**:
- [ ] Doorloop ALLE 46 toetsregels één voor één
- [ ] Fix false positives/negatives per regel
- [ ] Documenteer edge cases per regel
- [ ] Voeg toetsregels toe aan AI system prompt
- [ ] Test met juridische corpus (min. 100 definities)
**Specifiek**:
```python
# Prioriteit toetsregels om te fixen:
# ESS-03: Essentie matching
# CON-01: Consistentie termen
# ARA-06/07: Verboden beginconstructies
# SAM-regels: Samengestelde termen
```
**Deadline**: Week 2-3

### 6b. Ontologie 6-Stappen Protocol 🆕
**Probleem**: Ontologische categorisering niet geïmplementeerd
**Oplossing**:
- [ ] Implementeer 6-stappen protocol uit docs
- [ ] Integreer in definitie generatie flow
- [ ] UI voor ontologie categorie display
- [ ] Validatie op ontologische correctheid
**Details**:
```python
# Stap 1: Bepaal hoofdcategorie (SUBSTANTIE, EIGENSCHAP, etc.)
# Stap 2: Identificeer identiteitscriteria
# Stap 3: Bepaal persistentiecriteria
# Stap 4: Analyseer relaties
# Stap 5: Pas definitietemplate toe
# Stap 6: Valideer ontologische correctheid
```
**Deadline**: Week 2

## 🟡 BELANGRIJK - Core Functionaliteit (Week 2-4)

### 7. Automatische Hertoetsing
**Probleem**: Na aanpassing moet opnieuw getoetst worden
**Oplossing**:
- [ ] Auto-trigger toetsing na edit
- [ ] Track welke regels eerder faalden
- [ ] UI feedback tijdens hertoetsing
**Deadline**: Week 2

### 8. UI Tabs Activeren (Nu 3/10 werkend)
- [ ] **Management Tab** - Systeem configuratie UI
- [ ] **Monitoring Tab** - Performance metrics  
- [ ] **External Sources Tab** - Document upload
- [ ] **Web Lookup Tab** - Zoek interface
- [ ] **Prompt Viewer Tab** - Debug tool
- [ ] **Custom Definition Tab** - Edit mogelijkheid
- [ ] **Orchestration Tab** - Multi-agent workflows
**Deadline**: Week 3-4

### 9. Performance Optimalisatie
**Doel**: 8-12 sec → <5 sec response  
- [ ] Prompt size: 35k → <10k karakters
- [ ] Implement caching layer
- [ ] Optimize database queries
- [ ] Add progress indicators
**Deadline**: Week 4

### 10. Content Enrichment Services
- [ ] SynonymService (3-5 per definitie)
- [ ] AntonymService (context-aware)
- [ ] ExampleService (3-5 voorbeelden)
- [ ] Integreer in UI
**Deadline**: Week 3

### 10b. AI Bron Transparantie 🆕
**Probleem**: Gebruikers zien niet welke bronnen/prompts gebruikt zijn
**Oplossing**:
- [ ] Toon gebruikte prompts per generatie stap
- [ ] Display confidence scores per bron
- [ ] Context documenten die meewogen
- [ ] Export mogelijkheid voor audit
**Deadline**: Week 3

### 10c. Versie Control UI 🆕
**Probleem**: Database ondersteunt versies maar UI niet
**Oplossing**:
- [ ] Versie geschiedenis viewer
- [ ] Diff tussen versies
- [ ] Rollback functionaliteit
- [ ] Branch/merge voor reviews
**Deadline**: Week 3-4

## 🟢 NICE TO HAVE - Quick Wins (Week 1 Friday + Week 2-5)

### 11. UI/UX Verbeteringen
**Start Week 1 Friday voor snelle waarde!**
- [ ] Fix widget duplicate key errors (2 uur)
- [ ] Verbeter term input field (4 uur)
- [ ] Session state persistence (4 uur)
- [ ] Metadata velden display (aanmaakdatum, versie, bron)
- [ ] Nederlandse error messages (2 uur)
- [ ] Keyboard shortcuts (2 uur)
- [ ] Loading indicators (1 uur)
- [ ] Ontologische score visualisatie (4 uur) 🆕
- [ ] Prompt template library (2 uur) 🆕

### 12. Configuratie
- [ ] GPT temperature → config.yaml (30 min)
- [ ] Model selectie in UI (2 uur)
- [ ] Rate limit settings (1 uur)
- [ ] Export templates (4 uur)
- [ ] Batch import wizard (4 uur) 🆕
- [ ] Performance cache setup (2 uur) 🆕

## 🔵 LAATSTE FASE - Productie Ready (Week 5-6)

### 13. Documentatie
- [ ] API documentatie genereren
- [ ] Gebruikershandleiding updaten
- [ ] Deployment guide schrijven
- [ ] Troubleshooting guide

### 14. Testing & Kwaliteit
- [ ] Integration tests voor critical paths:
  - Complete definitie flow (term → generatie → toetsing → export)
  - Concurrent users scenario (5+ gebruikers)
  - Web lookup + definitie integratie
- [ ] A/B testing framework voor prompts:
  - Vergelijk oude (35k) vs nieuwe (<10k) prompts
  - Meet: snelheid, kwaliteit, kosten
  - Minimum 50 test definities
- [ ] Automated smoke tests
- [ ] Performance benchmarks
- [ ] Security audit
- [ ] Load testing (10+ users)

### 14b. Audit & Compliance 🆕
**Probleem**: Geen audit trail voor compliance
**Oplossing**:
- [ ] Immutable audit log implementatie
- [ ] Wie/wat/wanneer tracking voor alle acties
- [ ] Export functie voor compliance rapporten
- [ ] Retention policy configuratie
**Deadline**: Week 5

### 15. Deployment
- [ ] Production config files
- [ ] Backup procedures
- [ ] Monitoring setup
- [ ] Rollback plan

### 15b. Production Monitoring 🆕
**Probleem**: Geen proactieve monitoring/alerting
**Oplossing**:
- [ ] Health check endpoint (/health)
- [ ] Performance alerts setup
- [ ] Error rate monitoring
- [ ] OpenAI cost tracking dashboard
**Deadline**: Week 6

### 15c. API & Integraties 🆕
**Probleem**: Geen programmatische toegang
**Oplossing**:
- [ ] API key management systeem
- [ ] Rate limiting per API key
- [ ] OpenAPI/Swagger documentatie
- [ ] Python SDK basis
**Deadline**: Week 6+

## 📊 Progress Tracking

```
Kritiek:    [###-------] 30%  (Web Lookup ✅, Service Refactoring 87%)
Belangrijk: [----------] 0%  
Nice to Have:[----------] 0%
Laatste Fase:[----------] 0%

TOTAAL:     [##--------] 20%
```

## ✅ Definition of Done - Productie Ready

**Harde Eisen**:
- [ ] 10+ concurrent users zonder crashes
- [ ] Alle 10 UI tabs functioneel
- [x] Web lookup werkt voor juridische bronnen ✅
- [ ] Response tijd <7 seconden
- [ ] 0 failing tests
- [x] UTF-8 overal correct ✅
- [ ] **ALLE 46 toetsregels werkend zonder false positives**
- [ ] **Definitie generatie 100% consistent (temp=0)**
- [ ] **CI/CD pipeline actief**
- [ ] **Ontologie 6-stappen protocol geïmplementeerd** 🆕
- [ ] **AI bronnen transparant voor gebruiker** 🆕
- [ ] **Audit trail voor compliance** 🆕

**Kwaliteitseisen**:
- [ ] Test coverage >60%
- [ ] Documentatie compleet
- [ ] Security check passed
- [ ] Performance stabiel
- [ ] Health monitoring actief 🆕

## 🚨 Beslissingen Nodig

1. **PostgreSQL migratie** - Wel/niet doen? (impact op week 1)
2. **Docker deployment** - Requirement of nice-to-have?
3. **Monitoring tool** - Welke? (Sentry, DataDog, custom?)
4. **Multi-tenant support** - MVP of later? 🆕
5. **Enterprise features** - Welke prioriteit? 🆕

## 📝 Dagelijkse Updates

### 2025-01-14 (Dinsdag)
✅ **Web Lookup Module (Item 3)** - VOLTOOID
- WebLookupService interface en implementatie
- UTF-8 encoding issues opgelost  
- 4 duplicate/broken files verwijderd
- Rate limiting (10 req/min) + Caching (1 uur TTL)
- Tests geschreven (>90% coverage)
- ServiceContainer en ServiceAdapter geüpdatet
- Documentatie bijgewerkt in bestaande docs

🚧 **Service Refactoring** - Van 85% naar 87%
- WebLookupService toegevoegd aan DI container
- Nog te doen: ExamplesService, Feature flags, Performance profiling

## 📅 Week Planning

### Week 1 - Foundation + CI/CD
Ma-Di: Item 1 (Service Refactoring 87% → 100%) + Basic CI/CD setup
Di: ✅ Item 3 (Web Lookup) VOLTOOID
Wo-Do: Items 2, 4 (Database, Test infra)
Do: Item 5 (Definitie generatie temp=0)
Vr: Item 11 deel 1 (UI Quick Wins voor direct resultaat)

### Week 2 - Kernfuncties Perfectie
Focus: Item 6 (46 toetsregels verbeteren) + Items 6b (Ontologie), 7, 11, 12 (Quick wins)

### Week 3 - Features I
Focus: Item 6 afmaken + Items 8 (deel 1), 10, 10b (AI transparantie), 10c (Versie UI)

### Week 4 - Features II + Testing
Focus: Items 8 (deel 2), 9 + A/B testing framework

### Week 5 - Testing & Integratie
Focus: Items 13, 14, 14b (Audit) (incl. integration tests critical paths)

### Week 6+ - Deploy & Buffer
Focus: Item 15, 15b (Monitoring), 15c (API) + buffer + beslissingen implementeren

**Nota**: Timeline is flexibel - kernfuncties moeten perfect werken

## 🔮 TOEKOMSTIGE EPICS (Na MVP)

### EPIC: Enterprise Features
- Multi-tenant support
- Advanced RBAC
- SSO integratie
- Custom workflows

### EPIC: Advanced Analytics
- ML model performance tracking
- Definitie kwaliteit trends
- Usage analytics dashboard
- Cost optimization AI

### EPIC: Integraties
- MS Word plugin
- Juridische databases
- Workflow tools
- Export naar standards

---

**BELANGRIJK**: 
- Dit document is de ENIGE bron van waarheid
- Update wekelijks op vrijdag
- Oude planning docs zijn DEPRECATED (inclusief ONTBREKENDE-FUNCTIONALITEITEN.md)
- Bij twijfel: check dit document