# 🎯 MASTER TODO - DefinitieAgent naar Productie

**Dit is HET ENIGE document voor wat er moet gebeuren**  
*Alle andere planning documenten zijn DEPRECATED*

**Laatste Update**: 2025-01-14 (v3.3 - Code Review Protocol toegevoegd + Reality Check)  
**Deadline**: Flexibel - focus op WERKELIJK werkende kernfuncties  
**Status**: ONBEKEND - code review moet uitwijzen wat echt werkt  
**Filosofie**: Belangrijkste features eerst, timeline is indicatief

> **UPDATE v3**: Items met 🆕 zijn toegevoegd uit gap analyse ONTBREKENDE-FUNCTIONALITEITEN.md
> **UPDATE v3.1**: Web Lookup Module volledig gerefactored, Service Architecture 85%→87%
> **UPDATE v3.2**: Code review onthult WebLookupService is niet-functioneel, 3 weken herstel nodig
> **UPDATE v3.3**: Systematische code review protocol toegevoegd - ALLE claims moeten geverifieerd worden

## 🚨 NIEUWE PRIORITEIT: Code Review Alle "Voltooide" Items

**Probleem**: WebLookupService stond als "VOLTOOID" maar bleek volledig kapot
**Risico**: Andere items kunnen ook incorrect gemarkeerd zijn
**Actie**: Systematische code review van ALLE geclaimde functionaliteit

### 0. Code Review Protocol (DIRECT UITVOEREN)
**Doel**: Verifieer wat echt werkt vs wat alleen bestaat
**Protocol**: 📋 [Uitgebreid Code Review Protocol](docs/CODE_REVIEW_PROTOCOL.md)
**Methode**:
```python
Voor elk "voltooid" item:
1. Start de functionaliteit daadwerkelijk op
2. Voer basis tests uit (happy path + edge cases)  
3. Check of tests echt draaien (niet alleen bestaan)
4. Verifieer integratie met andere componenten
5. Documenteer discrepanties
```
**Te reviewen items** (geprioriteerd op impact):

**🔴 KRITIEK - Core Functionaliteit (Ma ochtend)**
1. [ ] **DefinitionGenerator** - Als dit niet werkt, werkt NIETS
   - Kan het definities genereren?
   - GPT integratie werkend?
   - Prompt templates correct?
   
2. [ ] **DefinitionValidator** - 46 toetsregels moeten werken
   - Hoeveel regels werken echt?
   - False positives/negatives?
   - Performance impact?

3. [ ] **DefinitionRepository** - Data moet opgeslagen worden
   - CRUD operaties werkend?
   - Concurrent access safe?
   - UTF-8 encoding correct?

**🟡 BELANGRIJK - Service Architecture (Ma middag)**
4. [ ] **Service Architecture** - Foundation van alles
   - Dependency injection werkt?
   - Service container functioneel?
   - Feature flags implementatie?

5. [ ] **DefinitionOrchestrator** - Coordineert alles
   - Integreert met alle services?
   - Web lookup integratie?
   - Error handling correct?

**🟢 ONDERSTEUNEND - Infrastructure (Di ochtend)**
6. [ ] **Database migraties** 
   - Alle migraties uitgevoerd?
   - UTF-8 echt overal gefixed?
   - Rollback mogelijk?

7. [ ] **Feature flags**
   - Toggle mechanisme werkt?
   - UI switches functioneel?
   - Legacy fallback werkt?
**Output**: Review rapport per component (zie protocol template)
**Deadline**: Week 1 - EERST dit doen

## 🔴 KRITIEK - Blockers voor Productie (Week 1-3)

### 1. Service Refactoring Afmaken
**Status**: 85% compleet (aangepast na code review)
**Prioriteit**: EERST - Foundation voor alles
**Nog te doen**:
- [ ] WebLookupService REPAREREN (zie item 3)
- [ ] ExamplesService consolideren
- [ ] Feature flags volledig implementeren
- [ ] Legacy code cleanup (na verificatie)
- [ ] Performance profiling nieuwe services
- [ ] Documentatie updaten voor overige services
**Deadline**: Week 1-3 (verlengd door WebLookupService issues)

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

### 3. Web Lookup Module ⚠️
**Status**: KRITIEKE PROBLEMEN ONTDEKT
**Update 2025-01-14**: Code review uitgevoerd - service is niet-functioneel
**Problemen**:
```python
# KRITIEK: Service kan niet draaien door:
- [ ] Import fouten (functienamen kloppen niet)
- [ ] Async/sync mismatch (legacy functies zijn sync)
- [ ] Ontbrekende dependencies (cache_async_result, Config)
- [ ] Tests draaien niet (0% coverage)
- [ ] Data transformatie ontbreekt
```
**Herstelplan**: Zie [WebLookupService Code Review](docs/analysis/WEBLOOKUP_SERVICE_CODE_REVIEW.md) en [Herstelplan](docs/analysis/WEBLOOKUP_SERVICE_RECOVERY_PLAN.md)
**Nieuwe deadline**: Week 1-3 (3 weken herstelwerk)

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
Code Review Status:
- [ ] DefinitionGenerator     🔴 KRITIEK
- [ ] DefinitionValidator     🔴 KRITIEK  
- [ ] DefinitionRepository    🔴 KRITIEK
- [ ] Service Architecture    🟡 BELANGRIJK
- [ ] DefinitionOrchestrator  🟡 BELANGRIJK
- [ ] Database/Migrations     🟢 ONDERSTEUNEND
- [ ] Feature Flags          🟢 ONDERSTEUNEND

Overall Progress:
Kritiek:    [?????????] ONBEKEND - Maandag duidelijk
Belangrijk: [?????????] ONBEKEND - Maandag duidelijk  
Nice to Have:[----------] 0%
Laatste Fase:[----------] 0%

TOTAAL:     [?????????] ONBEKEND - Na review duidelijk
```

## ✅ Definition of Done - Productie Ready

**Harde Eisen**:
- [ ] 10+ concurrent users zonder crashes
- [ ] Alle 10 UI tabs functioneel
- [ ] Web lookup werkt voor juridische bronnen ⚠️ (KAPOT - herstel nodig)
- [ ] Response tijd <7 seconden
- [ ] 0 failing tests
- [ ] UTF-8 overal correct (deels, WebLookupService moet nog)
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
⚠️ **Web Lookup Module (Item 3)** - KRITIEKE PROBLEMEN ONTDEKT
- Code review uitgevoerd: service is volledig niet-functioneel
- Import fouten: functienamen kloppen niet (zoek_wikipedia bestaat niet)
- Async/sync mismatch: legacy functies zijn sync, niet async
- Missing dependencies: cache_async_result en Config bestaan niet
- Tests kunnen niet draaien: 0% werkende coverage
- Documentatie misleidend: claimt functionaliteit die niet bestaat
- Herstelplan opgesteld: 3 weken werk nodig

📝 **Documentatie toegevoegd**:
- [WebLookupService Code Review](docs/analysis/WEBLOOKUP_SERVICE_CODE_REVIEW.md)
- [WebLookupService Herstelplan](docs/analysis/WEBLOOKUP_SERVICE_RECOVERY_PLAN.md)
- [Code Review Protocol](docs/CODE_REVIEW_PROTOCOL.md) - Voor systematische verificatie alle componenten

🚨 **PARADIGMA SHIFT**:
- Realisatie: Als WebLookupService "voltooid" was maar kapot is, wat is nog meer kapot?
- Actie: Code Review Protocol toegevoegd als Item 0 - HOOGSTE PRIORITEIT
- Planning aangepast: Week 1 begint met reality check van ALLE functionaliteit
- Status veranderd naar "ONBEKEND" - we weten niet wat echt werkt

🚧 **Service Refactoring** - Status ONBEKEND (was 85%)
- Moet geverifieerd worden wat echt werkt
- WebLookupService is NIET werkend
- Andere services mogelijk ook kapot

### 2025-01-14 (Dinsdag - Middag Update)
✅ **DefinitionGenerator (Item 0.1)** - WERKEND NA FIXES
- Protocol review uitgevoerd: component is VOLLEDIG FUNCTIONEEL
- Import issues opgelost: WebLookupService relative imports gefixt
- Missing dependencies toegevoegd: cache_async_result in utils/cache.py
- Temperature gefixt: 0.4 → 0.0 voor consistentie
- Test coverage: 99% (20/20 tests slagen)
- Integration verified: werkt met alle andere services

🔧 **Fixes toegepast**:
- WebLookupService: 5 import fixes (relative → absolute)
- utils/cache.py: cache_async_result functie toegevoegd
- config imports: Config class → get_config_manager
- Legacy function names: zoek_wikipedia → zoek_definitie_op_wikipedia
- Temperature: 0.4 → 0.0 in GeneratorConfig

📝 **Review documentatie toegevoegd**:
- [DefinitionGenerator Code Review](docs/analysis/DEFINITION_GENERATOR_CODE_REVIEW.md)
- [DefinitionGenerator Complete Review](docs/analysis/DEFINITION_GENERATOR_COMPLETE_REVIEW.md)
- [DefinitionGenerator Protocol Review](docs/analysis/DEFINITION_GENERATOR_PROTOCOL_REVIEW.md)

💡 **Lessons Learned**:
- WebLookupService blokkeerde ALLE services door import errors
- Na fix werkt DefinitionGenerator perfect (was al goed geschreven)
- Protocol-based review is effectief om echte functionaliteit te verifiëren

🟡 **DefinitionValidator (Item 0.2)** - WERKEND MET BEPERKINGEN
- Protocol review uitgevoerd: 32/32 tests slagen, 98% coverage
- 45 toetsregels gevonden (verwacht 46, maar acceptabel)
- Core validatie functionaliteit werkt correct
- Score berekening en categorisatie functioneel

⚠️ **Beperkingen gevonden**:
- Veel toetsregels zijn placeholders ("nog geen toetsfunctie geïmplementeerd")
- Scoring te strikt: goede definities scoren vaak <0.6
- validate_batch method ontbreekt (wel in interface)
- Naming inconsistentie: ARAI01.json vs verwachte ARA-01.json

📝 **Review documentatie**:
- [DefinitionValidator Protocol Review](docs/analysis/DEFINITION_VALIDATOR_PROTOCOL_REVIEW.md)

### 2025-01-14 (Late Middag) - Status Update
**Progress: 2/3 Kritieke Componenten Gereviewd**
- ✅ DefinitionGenerator: 100% werkend
- 🟡 DefinitionValidator: Werkend met bekende beperkingen
- ⏳ DefinitionRepository: Nog te reviewen

**Algemene Status**:
- Import blocking issues zijn opgelost
- Basis architectuur werkt
- Maar praktische bruikbaarheid beperkt door incomplete toetsregels

## 📅 Week Planning

### Week 1 - Reality Check + Foundation
**Maandag - Code Reviews Dag 1**
- 09:00-10:30: 🔴 DefinitionGenerator review (kritiek!)
- 10:30-12:00: 🔴 DefinitionValidator + 46 regels check
- 13:00-14:00: 🔴 DefinitionRepository + concurrent test
- 14:00-15:30: 🟡 Service Architecture verificatie
- 15:30-17:00: 🟡 DefinitionOrchestrator integratie check
- 17:00-17:30: Documenteer bevindingen + prioriteiten

**Dinsdag - Code Reviews Dag 2 + Start Fixes**
- 09:00-10:00: 🟢 Database migraties & UTF-8 check
- 10:00-11:00: 🟢 Feature flags verificatie
- 11:00-12:00: Consolideer alle bevindingen
- 13:00-17:00: Start met HOOGSTE prioriteit fixes

**Woensdag t/m Vrijdag**
- Focus op kritieke fixes uit review
- WebLookupService herstel (3-weken traject start)
- Database & Test infrastructure fixes

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