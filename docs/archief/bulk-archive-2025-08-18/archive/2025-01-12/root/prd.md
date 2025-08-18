# DefinitieAgent Brownfield Enhancement PRD

## Introduction

This document outlines the architectural approach for enhancing DefinitieAgent with complete legacy feature parity in the new modular structure. Its primary goal is to serve as the guiding blueprint for AI-driven development to restore all legacy functionality while ensuring seamless integration with the existing system.

**Relationship to Existing Architecture:**
This document supplements existing project architecture by defining how legacy features will be restored and UI completeness achieved. It respects the "Features First" philosophy where legacy code serves as the specification.

### Change Log

| Change | Date | Version | Description | Author |
|--------|------|---------|-------------|--------|
| Initial Draft | 2025-07-17 | 1.0 | Complete PRD with architecture analysis | BMad Orchestrator |

## Intro Project Analysis and Context

### Existing Project Overview

#### Analysis Source
- Document-project output available at: `/Users/chrislehnen/Projecten/Definitie-app/docs/brownfield-architecture.md`
- Comprehensive codebase analysis completed
- All project documentation reviewed and consolidated

#### Current Project State
Het DefinitieAgent project is een AI-powered Nederlandse definitie generator voor juridische en overheidscontexten. Het systeem gebruikt GPT-4 om definities te genereren die voldoen aan 46 kwaliteitsregels. De applicatie heeft succesvol een services consolidatie ondergaan (3→1 UnifiedDefinitionService) maar mist nog 70% van de legacy UI functionaliteit en heeft een grotendeels broken test suite (87% failing).

### Available Documentation Analysis

#### Available Documentation
Document-project analysis available - using existing technical documentation

Key documents available:
- ✓ Tech Stack Documentation 
- ✓ Source Tree/Architecture 
- ✓ Coding Standards (partial - CLAUDE.md)
- ✓ API Documentation 
- ✓ External API Documentation 
- ✓ UX/UI Guidelines 
- ✓ Technical Debt Documentation 
- ✓ Migration roadmap, quick wins lijst

### Enhancement Scope Definition

#### Enhancement Type
- ✓ Major Feature Modification
- ✓ UI/UX Overhaul
- ✓ Bug Fix and Stability Improvements

#### Enhancement Description
Het volledig operationeel maken van alle legacy functionaliteiten in de nieuwe modulaire structuur. Dit omvat het herstellen van ontbrekende UI componenten (70%), implementeren van content enrichment features, en het repareren van de test suite om een stabiele ontwikkelomgeving te garanderen.

#### Impact Assessment
- ✓ Major Impact (architectural changes required)

### Goals and Background Context

#### Goals
- Alle legacy features werkend maken in nieuwe modulaire architectuur
- 10 Streamlit UI tabs volledig functioneel maken (nu 30%)
- Content enrichment services implementeren (synoniemen, antoniemen, toelichting)
- Test suite repareren van 87% broken naar minimaal 60% coverage
- Quick wins implementeren voor directe gebruikerswaarde

#### Background Context
Na een succesvolle services consolidatie naar UnifiedDefinitionService mist de applicatie nog kritieke legacy functionaliteit. De "Features First" aanpak heeft geresulteerd in werkende kernfunctionaliteit maar incomplete UI en ontbrekende features. Met de solide modulaire basis is het nu tijd om alle legacy features te herstellen en het systeem productie-klaar te maken.

## Requirements

### Functional Requirements

- **FR1**: Alle 10 Streamlit UI tabs moeten volledig functioneel zijn (nu 3/10)
- **FR2**: Legacy content enrichment features moeten werken in nieuwe architectuur (synoniemen, antoniemen, toelichting)
- **FR3**: Prompt viewer met copy functionaliteit moet beschikbaar zijn
- **FR4**: Metadata velden moeten geactiveerd worden (code bestaat al)
- **FR5**: Export functionaliteit voor plain text, Excel, en PDF
- **FR6**: Ontologische score visualisatie moet zichtbaar zijn in UI
- **FR7**: Developer tools tab met logging toggle functionaliteit
- **FR8**: Aangepaste definitie editing mogelijkheid

### Non-Functional Requirements

- **NFR1**: Response tijd < 5 seconden (nu 8-12 sec)
- **NFR2**: Prompt grootte < 10k karakters (nu 35k)
- **NFR3**: Test coverage minimaal 60% (nu 14-40%)
- **NFR4**: Database concurrent access zonder locks
- **NFR5**: UTF-8 encoding correct in web lookup
- **NFR6**: Manual test protocol documentatie compleet

### Compatibility Requirements

- **CR1**: Bestaande database schema blijft compatible
- **CR2**: Legacy API endpoints blijven werken via wrappers
- **CR3**: UI componenten volgen Streamlit patterns
- **CR4**: Import structuur gestandaardiseerd (geen 3 verschillende stijlen)

## User Interface Enhancement Goals

### Integration with Existing UI

De nieuwe UI componenten moeten naadloos integreren met het bestaande Streamlit framework:

- **Streamlit Session State**: Alle nieuwe componenten gebruiken session state voor data persistence
- **Widget Key Management**: Fix de widget key generator bug voor stabiele UI
- **Consistent Styling**: Volg bestaande Streamlit theming en layout patterns
- **Tab Navigation**: Behoud de 10-tab structuur maar maak ze functioneel

### Modified/New Screens and Views

**Te activeren tabs:**
1. **Prompt Viewer Tab** - Toon gebruikte prompts met copy functie
2. **Aangepaste Definitie Tab** - Editor voor definitie aanpassing
3. **Developer Tools Tab** - Logging viewer en debug opties
4. **Expert Review Tab** - Review workflow implementatie
5. **Externe Bronnen Tab** - Document upload verbetering
6. **Orchestratie Tab** - Multi-agent coordinatie view
7. **Management Tab** - Systeem configuratie UI

### UI Consistency Requirements

- Alle tabs moeten dezelfde layout structuur volgen
- Error handling via st.error() consistentie
- Loading states via st.spinner() voor alle async operations
- Success feedback via st.success() na acties
- Help tooltips bij complexe features

## Technical Architecture Analysis

### Current Architecture (AS-IS)

#### System Overview
Het DefinitieAgent systeem heeft recent een succesvolle consolidatie ondergaan maar bevindt zich nog in een hybride staat tussen legacy en modern architectuur.

#### Core Components

**1. Service Layer** ✅ **GECONSOLIDEERD**
```
UnifiedDefinitionService (Singleton)
├── Sync/Async processing support
├── Legacy compatibility wrappers
├── AUTO/MODERN/LEGACY/HYBRID modes
└── Centralized business logic
```

**2. AI & Validation Layer** ⚠️ **PARTIALLY MIGRATED**
```
├── ai_toetsing/
│   ├── 46 JSON validators ✅
│   ├── Python validator implementations ✅
│   └── Orchestration service ✅
├── ai_agents/ (BROKEN)
│   └── Content enrichment missing ❌
```

**3. UI Layer** 🔴 **30% FUNCTIONAL**
```
10 Streamlit Tabs:
├── ✅ Definitie Generatie (basic)
├── ✅ Geschiedenis
├── ✅ Export (basic)
├── ⚠️ Kwaliteitscontrole (partial)
├── ❌ Prompt Viewer
├── ❌ Aangepaste Definitie
├── ❌ Developer Tools
└── ❌ 3 andere tabs
```

**4. Data Layer** ✅ **MODERN**
```
├── SQLAlchemy ORM
├── Repository Pattern
├── SQLite Database
└── Migration support
```

#### Current Technical Debt

1. **Import Path Chaos**: 3 verschillende import stijlen
2. **Config Fragmentation**: 4 config systemen zonder centrale authority
3. **Test Suite**: 87% tests broken
4. **Performance**: 8-12 sec response tijd, 35k prompt size
5. **Encoding Issues**: UTF-8 problemen in web lookup

### Brownfield Specific Constraints

#### Legacy Dependencies
- **Legacy UI Code**: `centrale_module_definitie_kwaliteit_legacy.py` (1,088 lines)
- **Legacy Core**: `core_legacy.py` (2,025 lines) met alle toetsregels
- **Session State**: Legacy session state management moet behouden blijven
- **Export Formats**: Legacy export functionaliteit exact repliceren

#### Integration Touchpoints
1. **Database**: SQLite schema moet backward compatible blijven
2. **File System**: Export paths en cache locaties gefixeerd
3. **Config Files**: Legacy config keys moeten blijven werken
4. **UI State**: Streamlit session keys moeten identiek blijven

#### Migration Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|-------------|---------|------------|
| Session state corruption | High | High | Incremental migration per tab |
| Export format mismatch | Medium | Medium | Side-by-side testing |
| Performance degradation | Low | High | Profile before/after |
| Widget key conflicts | High | Low | Fix key generator first |
| Data loss during migration | Low | Critical | Backup + rollback strategy |

### Target Architecture (TO-BE)

#### System Goals
- 100% UI functionaliteit
- Alle legacy features werkend
- <5 sec response tijd
- 60%+ test coverage
- Gestandaardiseerde architectuur

#### Enhanced Components

**1. Service Layer** (Minor Updates)
```
UnifiedDefinitionService
├── Content Enrichment Integration ➕
├── Performance Optimizations ➕
├── Simplified Prompt Builder ➕
└── Enhanced Caching ➕
```

**2. New Content Services** 🆕
```
ContentEnrichmentService
├── Synoniemen Generator
├── Antoniemen Generator
├── Toelichting Generator
└── Legacy Feature Parity
```

**3. Complete UI Layer** 🎯
```
All 10 Tabs Functional:
├── Enhanced Definitie Generatie
│   ├── Prompt Viewer Component
│   ├── Metadata Fields
│   └── Copy Functionality
├── Aangepaste Definitie Editor
├── Developer Console
└── All Other Tabs Activated
```

### Gap Analysis

| Component | Current State | Target State | Gap | Effort |
|-----------|--------------|--------------|-----|--------|
| Services | Consolidated ✅ | + Enrichment | Content features | 1 week |
| UI Tabs | 30% working | 100% working | 7 tabs | 2 weeks |
| Testing | 87% broken | 60% coverage | Fix + new tests | 1 week |
| Performance | 8-12 sec | <5 sec | Optimization | 1 week |
| Config | 4 systems | 1 unified | Consolidation | 3 days |

### Migration Strategy

#### Phase 1: Quick Wins (Week 1)
1. Fix database concurrent access
2. Resolve UTF-8 encoding
3. Activate metadata fields
4. Add prompt viewer

#### Phase 2: Feature Restoration (Week 2-3)
1. Implement ContentEnrichmentService
2. Port legacy enrichment logic
3. Activate remaining UI tabs
4. Add definition editor

#### Phase 3: Quality & Performance (Week 4-5)
1. Fix import standardization
2. Unify config systems
3. Optimize prompts (35k→10k)
4. Implement caching strategy

#### Phase 4: Testing & Stability (Week 6)
1. Repair test suite
2. Add integration tests
3. Document manual test scenarios
4. Performance profiling

## Technical Constraints and Integration Requirements

### Existing Technology Stack

**Languages**: Python 3.8+
**Frameworks**: Streamlit 1.29.0, FastAPI (optional)
**Database**: SQLite via SQLAlchemy 2.0.25
**Infrastructure**: Local deployment, geen cloud
**External Dependencies**: OpenAI API 1.12.0, httpx 0.26.0, Pydantic 2.5.3

### Integration Approach

**Database Integration Strategy**: 
- Behoud huidige SQLAlchemy models
- Voeg indexes toe voor performance
- Implementeer connection pooling voor concurrent access

**API Integration Strategy**: 
- OpenAI calls via centralized AI service
- Rate limiting via smart_rate_limiter
- Retry logic met exponential backoff

**Frontend Integration Strategy**: 
- Nieuwe UI componenten als separate Python modules
- Integratie via tab registry in main app
- Session state management voor cross-tab data

**Testing Integration Strategy**: 
- Fix import paths eerst
- Voeg pytest fixtures voor common test data
- Mock OpenAI calls in tests

### Code Organization and Standards

**File Structure Approach**: 
- Nieuwe features in dedicated submodules
- Components folder voor herbruikbare UI delen
- Utils uitbreiden voor shared functionality

**Naming Conventions**: 
- snake_case voor files en functies
- PascalCase voor classes
- UPPER_CASE voor constants
- Nederlandse functienamen voor business logic

**Coding Standards**: 
- Type hints verplicht voor public functions
- Docstrings in Nederlands voor business logic
- Black formatter voor consistentie
- Import sorting met isort

**Documentation Standards**: 
- README per nieuwe module
- Inline comments voor complexe logica
- API documentatie voor nieuwe endpoints
- Changelog updates per feature

### Deployment and Operations

**Build Process Integration**: 
- Geen build process (Python interpreted)
- Requirements.txt voor dependencies
- Virtual environment aanbevolen

**Deployment Strategy**: 
- Manual deployment via streamlit run
- Geen CI/CD pipeline aanwezig
- Database migraties handmatig

**Monitoring and Logging**: 
- Structured logging naar logs/ folder
- Performance metrics in cache/
- Error tracking via try/except blocks

**Configuration Management**: 
- Consolideer naar single config system
- Environment variables voor secrets
- Config files voor applicatie settings

### Risk Assessment and Mitigation

**Technical Risks**: 
- Import path chaos kan builds breken
- Legacy code dependencies fragiel
- Test suite repair kan regressies introduceren

**Integration Risks**: 
- Services consolidatie kan edge cases missen
- UI state management tussen tabs complex
- Database locks bij concurrent access

**Deployment Risks**: 
- Geen rollback mechanisme
- Manual deployment error-prone
- Database corruptie mogelijk

**Mitigation Strategies**: 
- Stapsgewijze implementatie met manual testing
- Database backups voor elke major change
- Feature flags voor nieuwe functionaliteit
- Uitgebreide logging voor debugging

## Epic and Story Structure

### Epic Approach

**Epic Structure Decision**: 7 focused epics met kleinere user stories (1-5 story points) voor betere beheersbaarheid, duidelijke sprint planning, en incrementele value delivery. Totaal 41 stories verdeeld over 6 sprints.

### Epic Overview

| Epic | Focus | Business Value | Sprint | Story Points |
|------|-------|----------------|--------|--------------|
| 1 | Database & Infrastructure | Stabiliteit & Schaalbaarheid | 1 | 7 |
| 2 | Web Lookup Module | Kritieke Feature Herstel | 1-2 | 10 |
| 3 | UI Quick Wins | Gebruikerstevredenheid | 2 | 8 |
| 4 | Content Enrichment | Rijkere Definities | 2-3 | 11 |
| 5 | Tab Activatie | Complete Functionaliteit | 3-4 | 21 |
| 6 | Prompt Optimalisatie | Kosten & Performance | 4 | 10 |
| 7 | Test Suite | Kwaliteit & Vertrouwen | 5-6 | 18 |
| **Totaal** | | | **6 sprints** | **85 pts** |

## Epic 1: Database & Infrastructure Stabilisatie

**Epic Goal**: Stabiliseer de technische basis voor betrouwbare multi-user toegang zonder data verlies of locks.

**Business Value**: Voorkomt productie issues, maakt applicatie schaalbaar voor meerdere gebruikers.

**Sprint**: 1 (7 story points totaal)

### Story 1.1: Enable SQLite WAL Mode (3 pts)
**Als een** developer  
**wil ik** WAL mode activeren voor de SQLite database  
**zodat** meerdere gebruikers tegelijk kunnen lezen zonder locks.

**Acceptance Criteria:**
- [ ] PRAGMA journal_mode=WAL uitgevoerd bij startup
- [ ] Connection string aangepast met juiste settings
- [ ] Geen "database is locked" errors bij 5 concurrent reads
- [ ] Rollback plan gedocumenteerd

### Story 1.2: Fix Connection Pooling (2 pts)
**Als een** developer  
**wil ik** proper connection pooling configureren  
**zodat** database resources efficiënt gebruikt worden.

**Acceptance Criteria:**
- [ ] Pool size: 20, max overflow: 40
- [ ] Connection timeout: 30 seconden
- [ ] Pool pre-ping enabled voor connection health
- [ ] Monitoring voor pool usage

### Story 1.3: Database UTF-8 Encoding (2 pts)
**Als een** developer  
**wil ik** UTF-8 encoding forceren voor alle database operaties  
**zodat** Nederlandse tekst correct opgeslagen wordt.

**Acceptance Criteria:**
- [ ] PRAGMA encoding='UTF-8' actief
- [ ] Alle text columns correct encoded
- [ ] Test met ë, ï, ü, é, à, §, €, © karakters
- [ ] Bestaande data gemigreerd indien nodig

## Epic 2: Web Lookup Module Herstel

**Epic Goal**: Consolideer en fix de 5 broken web lookup implementaties tot één werkende service.

**Business Value**: Herstel kritieke functionaliteit voor juridische bronnen lookup.

**Sprint**: 1-2 (10 story points totaal)

### Story 2.1: Analyse & Cleanup Broken Files (2 pts)
**Als een** developer  
**wil ik** alle web lookup files analyseren  
**zodat** ik weet wat te behouden en wat te verwijderen.

**Acceptance Criteria:**
- [ ] Lijst van 5 files met functionaliteit analyse
- [ ] Identificatie van beste implementatie onderdelen
- [ ] Cleanup plan voor broken files
- [ ] Documentatie van encoding issues

### Story 2.2: Implementeer Nieuwe Web Lookup Service (5 pts)
**Als een** developer  
**wil ik** één consolidated web lookup service  
**zodat** encoding correct werkt voor alle bronnen.

**Acceptance Criteria:**
- [ ] Nieuwe web_lookup_service.py geïmplementeerd
- [ ] UTF-8 support voor requests en responses
- [ ] Error handling voor network issues
- [ ] Support voor wetten.nl, officielebekendmakingen.nl, rechtspraak.nl

### Story 2.3: Integreer met UI & Test (3 pts)
**Als een** gebruiker  
**wil ik** web lookup resultaten zien in de UI  
**zodat** ik juridische bronnen kan raadplegen.

**Acceptance Criteria:**
- [ ] Web Lookup tab volledig functioneel
- [ ] Nederlandse tekst correct weergegeven
- [ ] Loading states en error feedback
- [ ] Resultaten caching voor performance

## Epic 3: UI Quick Wins

**Epic Goal**: Verbeter direct zichtbare UI issues voor betere gebruikerservaring.

**Business Value**: Verhoog gebruikerstevredenheid met kleine maar impactvolle fixes.

**Sprint**: 2 (8 story points totaal)

### Story 3.1: Fix Widget Key Generator (2 pts)
**Als een** developer  
**wil ik** unieke widget keys genereren  
**zodat** Streamlit geen duplicate key errors geeft.

**Acceptance Criteria:**
- [ ] Widget key generator functie gefixt
- [ ] Geen duplicate key warnings in console
- [ ] Keys persistent over reruns
- [ ] Unit test voor key generator

### Story 3.2: Activeer Term Input Field (1 pt)
**Als een** gebruiker  
**wil ik** direct een term invoeren op de homepage  
**zodat** ik snel kan beginnen.

**Acceptance Criteria:**
- [ ] Input field prominent op homepage
- [ ] Enter key triggert definitie generatie
- [ ] Placeholder text met voorbeeld
- [ ] Focus op page load

### Story 3.3: Fix Session State Persistence (3 pts)
**Als een** gebruiker  
**wil ik** dat mijn data bewaard blijft  
**zodat** ik niet opnieuw moet invoeren na reload.

**Acceptance Criteria:**
- [ ] Form data persist bij page reload
- [ ] Tab selectie blijft behouden
- [ ] Definitie geschiedenis beschikbaar
- [ ] Clear session optie toegevoegd

### Story 3.4: Toon Metadata Velden (2 pts)
**Als een** gebruiker  
**wil ik** metadata van definities zien  
**zodat** ik context heb over de gegenereerde content.

**Acceptance Criteria:**
- [ ] Context type zichtbaar (juridisch/algemeen/etc)
- [ ] Model versie getoond
- [ ] Temperature setting zichtbaar
- [ ] Timestamp van generatie

## Epic 4: Content Enrichment Service

**Epic Goal**: Voeg synoniemen, antoniemen en voorbeelden toe aan definities.

**Business Value**: Lever rijkere, meer educatieve definities aan gebruikers.

**Sprint**: 2-3 (11 story points totaal)

### Story 4.1: Implementeer Synonym Service (3 pts)
**Als een** gebruiker  
**wil ik** synoniemen zien bij definities  
**zodat** ik alternatieven ken.

**Acceptance Criteria:**
- [ ] 3-5 synoniemen per definitie
- [ ] Context-aware selectie
- [ ] Nederlandse taal support
- [ ] Fallback bij geen synoniemen

### Story 4.2: Implementeer Antonym Service (3 pts)
**Als een** gebruiker  
**wil ik** antoniemen zien waar relevant  
**zodat** ik tegenstellingen begrijp.

**Acceptance Criteria:**
- [ ] Antoniemen alleen waar zinvol
- [ ] Duidelijke UI indicatie
- [ ] Skip voor abstracte begrippen
- [ ] Quality check op relevantie

### Story 4.3: Genereer Voorbeeldzinnen (3 pts)
**Als een** gebruiker  
**wil ik** voorbeeldzinnen zien  
**zodat** ik het gebruik begrijp.

**Acceptance Criteria:**
- [ ] 3-5 voorbeeldzinnen per definitie
- [ ] Verschillende contexten gedekt
- [ ] Grammaticaal correct Nederlands
- [ ] Relevantie voor doelgroep

### Story 4.4: UI Integratie Enrichments (2 pts)
**Als een** gebruiker  
**wil ik** enrichments overzichtelijk zien  
**zodat** de interface niet cluttered wordt.

**Acceptance Criteria:**
- [ ] Expandable/collapsible secties
- [ ] Duidelijke labels per enrichment type
- [ ] Optie om enrichments te verbergen
- [ ] Export inclusief enrichments

## Epic 5: Tab Activatie

**Epic Goal**: Maak alle 10 UI tabs volledig functioneel.

**Business Value**: Unlock volledige applicatie functionaliteit voor power users.

**Sprint**: 3-4 (21 story points totaal)

### Story 5.1: Activeer Management Tab (3 pts)
**Als een** admin  
**wil ik** systeem settings beheren  
**zodat** ik de applicatie kan configureren.

**Acceptance Criteria:**
- [ ] Temperature defaults instelbaar
- [ ] Model selectie opties
- [ ] Rate limiting configuratie
- [ ] Settings persistent

### Story 5.2: Activeer Orchestration Tab (5 pts)
**Als een** power user  
**wil ik** multi-agent workflows bouwen  
**zodat** ik complexe taken kan automatiseren.

**Acceptance Criteria:**
- [ ] Agent selectie interface
- [ ] Workflow builder UI
- [ ] Execution monitoring
- [ ] Results aggregatie

### Story 5.3: Activeer Monitoring Tab (3 pts)
**Als een** developer  
**wil ik** systeem metrics zien  
**zodat** ik performance kan monitoren.

**Acceptance Criteria:**
- [ ] API call counts
- [ ] Response time graphs
- [ ] Error rate tracking
- [ ] Cost calculator

### Story 5.4: Activeer External Sources Tab (3 pts)
**Als een** gebruiker  
**wil ik** documenten uploaden  
**zodat** ik eigen bronnen kan gebruiken.

**Acceptance Criteria:**
- [ ] Drag-drop file upload
- [ ] PDF, DOCX, TXT support
- [ ] Progress indicators
- [ ] Document management

### Story 5.5: Activeer Web Lookup Tab (2 pts)
**Als een** gebruiker  
**wil ik** online bronnen doorzoeken  
**zodat** ik actuele informatie heb.

**Acceptance Criteria:**
- [ ] Depends on Epic 2 completion
- [ ] Search interface werkend
- [ ] Results weergave
- [ ] Bron attributie

### Story 5.6: Activeer Prompt Viewer Tab (2 pts)
**Als een** developer  
**wil ik** gebruikte prompts zien  
**zodat** ik kan debuggen en leren.

**Acceptance Criteria:**
- [ ] Toon laatste 10 prompts
- [ ] Copy-to-clipboard functie
- [ ] Token count weergave
- [ ] Prompt templates zichtbaar

### Story 5.7: Activeer Custom Definition Tab (3 pts)
**Als een** gebruiker  
**wil ik** definities kunnen aanpassen  
**zodat** ik maatwerk kan leveren.

**Acceptance Criteria:**
- [ ] Rich text editor
- [ ] Version history
- [ ] Save/load functionaliteit
- [ ] Validatie na aanpassing

## Epic 6: Prompt Optimalisatie

**Epic Goal**: Reduceer prompt grootte van 35k naar <10k karakters.

**Business Value**: 50% kosten reductie, 40% snellere responses.

**Sprint**: 4 (10 story points totaal)

### Story 6.1: Analyseer Huidige Prompts (2 pts)
**Als een** developer  
**wil ik** prompt usage analyseren  
**zodat** ik optimization opportunities zie.

**Acceptance Criteria:**
- [ ] Token usage report per prompt type
- [ ] Redundantie analyse
- [ ] Cost breakdown
- [ ] Optimization targets identified

### Story 6.2: Implementeer Dynamic Prompts (5 pts)
**Als een** developer  
**wil ik** context-aware prompt building  
**zodat** alleen relevante info gestuurd wordt.

**Acceptance Criteria:**
- [ ] Template systeem voor prompts
- [ ] Dynamic example selection
- [ ] Context compression algoritme
- [ ] Prompt size <10k chars

### Story 6.3: A/B Test Nieuwe Prompts (3 pts)
**Als een** product owner  
**wil ik** quality metrics vergelijken  
**zodat** kwaliteit behouden blijft.

**Acceptance Criteria:**
- [ ] A/B test framework
- [ ] Quality metrics dashboard
- [ ] Statistical significance check
- [ ] Rollback capability

## Epic 7: Test Suite Restoration

**Epic Goal**: Creëer betrouwbare test coverage voor confident development.

**Business Value**: Minder bugs, snellere development cycles, team confidence.

**Sprint**: 5-6 (18 story points totaal)

### Story 7.1: Fix Import Paths (2 pts)
**Als een** developer  
**wil ik** consistente imports  
**zodat** tests kunnen draaien.

**Acceptance Criteria:**
- [ ] Alle imports werkend
- [ ] Geen circular dependencies
- [ ] Import style guide
- [ ] Auto-fix script

### Story 7.2: Create Test Fixtures (3 pts)
**Als een** developer  
**wil ik** herbruikbare test data  
**zodat** tests consistent zijn.

**Acceptance Criteria:**
- [ ] Definition fixtures
- [ ] User fixtures
- [ ] Validation result fixtures
- [ ] Mock API responses

### Story 7.3: Fix Unit Tests Core (5 pts)
**Als een** developer  
**wil ik** werkende unit tests  
**zodat** business logic gedekt is.

**Acceptance Criteria:**
- [ ] Service layer tests
- [ ] Validator tests
- [ ] 80% coverage target
- [ ] Fast execution (<30s)

### Story 7.4: Add Integration Tests (5 pts)
**Als een** developer  
**wil ik** end-to-end tests  
**zodat** user flows getest zijn.

**Acceptance Criteria:**
- [ ] Happy path scenarios
- [ ] Error scenarios
- [ ] UI interaction tests
- [ ] API integration tests

### Story 7.5: Setup CI Pipeline (3 pts)
**Als een** team  
**willen wij** automated testing  
**zodat** bugs vroeg gevangen worden.

**Acceptance Criteria:**
- [ ] Tests run on commit
- [ ] Coverage reports
- [ ] Build status badges
- [ ] Failed test notifications

## Sprint Planning

### Sprint Velocity & Capacity
- **Team Size**: 2 developers
- **Sprint Length**: 2 weken
- **Velocity Target**: 14-16 story points per sprint
- **Buffer**: 10% voor bugs en ondersteuning

### Sprint Overview

| Sprint | Focus Areas | Story Points | Key Deliverables |
|--------|-------------|--------------|------------------|
| 1 | Database & Web Lookup Start | 14 | Stabiele multi-user toegang, web lookup analyse |
| 2 | UI Quick Wins & Enrichment | 14 | Zichtbare UI verbeteringen, synoniemen |
| 3 | Content & Tab Activatie | 16 | Complete enrichment, eerste tabs actief |
| 4 | Tabs & Prompt Optimalisatie | 15 | Meer tabs, 70% kosten reductie |
| 5 | Testing Foundation | 13 | Import fixes, fixtures, unit tests |
| 6 | Test Completion | 13 | Integration tests, CI/CD pipeline |

### Definition of Done (Global)
Voor elke story:
- [ ] Code review completed
- [ ] Unit tests geschreven (waar applicable)
- [ ] Documentatie bijgewerkt
- [ ] Geen regressie in bestaande features
- [ ] UI getest op happy path
- [ ] Performance impact gemeten

### Release Planning
- **Sprint 1-2**: Foundation Release (Database stabiel, basis UI fixes)
- **Sprint 3-4**: Feature Complete Release (Alle tabs, enrichment)
- **Sprint 5-6**: Quality Release (Tests, monitoring, productie-ready)

## Checklist Results Report

*To be completed by architect-checklist execution*

## Next Steps

### Story Manager Handoff

Voor de Story Manager om verder te werken met deze brownfield enhancement:

- Referentie: Deze PRD met focus op legacy feature parity
- Eerste story: Database fixes (BLOCKER voor andere werk)
- Key requirement: Alle legacy features moeten werken
- Verificatie: Manual testing protocol voor elke story
- Constraint: Behoud backward compatibility

Prioriteit volgorde:
1. Database & encoding fixes (blockers)
2. UI quick wins (direct zichtbaar)
3. Content enrichment (core feature)
4. Complete UI activation
5. Performance optimization
6. Test suite (voor maintenance)

### Developer Handoff

Voor developers die beginnen met implementatie:

- Start met docs/brownfield-architecture.md voor context
- Volg UnifiedDefinitionService patterns
- Check legacy code in src/services/legacy/ voor specs
- Test manual eerst, automated tests zijn broken
- Commit kleine, werkende increments

Quick start:
```bash
cd /Users/chrislehnen/Projecten/Definitie-app
cp .env.example .env
# Add OpenAI key
pip install -r requirements.txt
streamlit run src/app.py
```