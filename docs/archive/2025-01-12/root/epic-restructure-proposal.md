# Epic Herstructurering Voorstel - DefinitieAgent

## Analyse Huidige Situatie

De huidige PRD heeft 1 mega-epic met 6 "stories" die eigenlijk sub-epics zijn:
- Stories zijn te groot (3-13 story points)
- Scope is te breed per story
- Niet uitvoerbaar in 1 sprint
- Mix van technische en functionele requirements

## Voorgestelde Epic Structuur

### Epic 1: Database & Infrastructure Stabilisatie
**Goal**: Stabiliseer de technische basis voor betrouwbare multi-user toegang
**Business Value**: Voorkomt productie issues, maakt schaling mogelijk
**Sprint**: 1

#### Stories:
1. **Enable SQLite WAL Mode** (3 pts)
   - Als developer wil ik WAL mode activeren zodat concurrent reads mogelijk zijn
   - AC: WAL mode actief, geen locks bij 5 users

2. **Fix Connection Pooling** (2 pts)
   - Als developer wil ik proper connection pooling zodat resources efficiënt gebruikt worden
   - AC: Pool size 20, overflow 40, timeout 30s

3. **Database UTF-8 Encoding** (2 pts)
   - Als developer wil ik UTF-8 forceren zodat Nederlandse tekst correct opgeslagen wordt
   - AC: Pragma encoding UTF-8, alle text fields correct

### Epic 2: Web Lookup Module Herstel
**Goal**: Consolideer en fix de broken web lookup functionaliteit
**Business Value**: Kritieke feature voor juridische definities werkt weer
**Sprint**: 1-2

#### Stories:
1. **Analyse & Cleanup Broken Files** (2 pts)
   - Als developer wil ik broken files identificeren zodat ik weet wat te consolideren
   - AC: Lijst van 5 files, analyse van verschillen

2. **Implementeer Nieuwe Web Lookup Service** (5 pts)
   - Als developer wil ik één werkende lookup service zodat encoding correct is
   - AC: UTF-8 support, proper error handling, httpx client

3. **Integreer met UI & Test** (3 pts)
   - Als gebruiker wil ik web lookup resultaten zien zodat ik juridische bronnen kan raadplegen
   - AC: Tab werkt, Nederlandse tekst correct, 3 bronnen ondersteund

### Epic 3: UI Quick Wins
**Goal**: Verbeter direct zichtbare UI issues voor betere UX
**Business Value**: Gebruikerstevredenheid verhogen met kleine fixes
**Sprint**: 2

#### Stories:
1. **Fix Widget Key Generator** (2 pts)
   - Als developer wil ik stabiele widget keys zodat UI niet crashed
   - AC: Geen duplicate key errors, consistent keys

2. **Activeer Term Input Field** (1 pt)
   - Als gebruiker wil ik direct een term kunnen invoeren op de homepage
   - AC: Input field zichtbaar, enter key werkt

3. **Fix Session State Persistence** (3 pts)
   - Als gebruiker wil ik dat mijn data bewaard blijft bij page reload
   - AC: Form data persist, tab state persist

4. **Toon Metadata Velden** (2 pts)
   - Als gebruiker wil ik metadata zien zodat ik context heb
   - AC: Context type, model, temperature zichtbaar

### Epic 4: Content Enrichment Service
**Goal**: Voeg waarde toe aan definities met synoniemen en voorbeelden
**Business Value**: Rijkere, meer bruikbare definities voor gebruikers
**Sprint**: 2-3

#### Stories:
1. **Implementeer Synonym Service** (3 pts)
   - Als gebruiker wil ik synoniemen zien zodat ik alternatieven ken
   - AC: 3-5 synoniemen per definitie, context-aware

2. **Implementeer Antonym Service** (3 pts)
   - Als gebruiker wil ik antoniemen zien zodat ik tegenstellingen begrijp
   - AC: Waar relevant antoniemen tonen

3. **Genereer Voorbeeldzinnen** (3 pts)
   - Als gebruiker wil ik voorbeelden zien zodat ik gebruik begrijp
   - AC: 3-5 voorbeeldzinnen per definitie

4. **UI Integratie Enrichments** (2 pts)
   - Als gebruiker wil ik enrichments mooi gepresenteerd zien
   - AC: Expandable sections, clean layout

### Epic 5: Tab Activatie (Per Tab)
**Goal**: Maak alle 10 UI tabs functioneel
**Business Value**: Volledige functionaliteit beschikbaar voor power users
**Sprint**: 3-4

#### Stories (per tab 1 story):
1. **Activeer Management Tab** (3 pts)
2. **Activeer Orchestration Tab** (5 pts)
3. **Activeer Monitoring Tab** (3 pts)
4. **Activeer External Sources Tab** (3 pts)
5. **Activeer Web Lookup Tab** (2 pts) - depends on Epic 2
6. **Activeer Prompt Viewer Tab** (2 pts)
7. **Activeer Custom Definition Tab** (3 pts)

### Epic 6: Prompt Optimalisatie
**Goal**: Reduceer prompt size voor betere performance en lagere kosten
**Business Value**: 50% kosten reductie, 40% snellere responses
**Sprint**: 4

#### Stories:
1. **Analyseer Huidige Prompts** (2 pts)
   - Als developer wil ik prompt usage begrijpen zodat ik kan optimaliseren
   - AC: Report van token usage, redundantie analyse

2. **Implementeer Dynamic Prompts** (5 pts)
   - Als developer wil ik context-aware prompts zodat alleen relevante info gestuurd wordt
   - AC: Prompt <10k chars, template systeem

3. **A/B Test Nieuwe Prompts** (3 pts)
   - Als PO wil ik quality metrics zodat ik weet dat kwaliteit behouden blijft
   - AC: Test framework, metrics dashboard

### Epic 7: Test Suite Restoration
**Goal**: Creëer betrouwbare test coverage voor confident development
**Business Value**: Minder bugs, snellere development, team confidence
**Sprint**: 4-5

#### Stories:
1. **Fix Import Paths** (2 pts)
   - Als developer wil ik consistente imports zodat tests kunnen draaien
   - AC: Alle imports werken, geen circular deps

2. **Create Test Fixtures** (3 pts)
   - Als developer wil ik test data zodat ik consistent kan testen
   - AC: Fixtures voor definitions, users, validations

3. **Fix Unit Tests Core** (5 pts)
   - Als developer wil ik werkende unit tests voor business logic
   - AC: Services getest, 80% coverage

4. **Add Integration Tests** (5 pts)
   - Als developer wil ik end-to-end tests voor kritieke flows
   - AC: Happy path getest, error cases getest

5. **Setup CI Pipeline** (3 pts)
   - Als team wil ik automated testing zodat we bugs vroeg vangen
   - AC: Tests run on commit, coverage reports

## Sprint Planning

### Sprint 1 (2 weken)
- Epic 1: Database & Infrastructure (7 pts)
- Epic 2: Web Lookup - Stories 1-2 (7 pts)
**Total**: 14 points

### Sprint 2 (2 weken)
- Epic 2: Web Lookup - Story 3 (3 pts)
- Epic 3: UI Quick Wins (8 pts)
- Epic 4: Content Enrichment - Story 1 (3 pts)
**Total**: 14 points

### Sprint 3 (2 weken)
- Epic 4: Content Enrichment - Stories 2-4 (8 pts)
- Epic 5: Tab Activatie - Stories 1-2 (8 pts)
**Total**: 16 points

### Sprint 4 (2 weken)
- Epic 5: Tab Activatie - Stories 3-5 (8 pts)
- Epic 6: Prompt Optimalisatie - Stories 1-2 (7 pts)
**Total**: 15 points

### Sprint 5 (2 weken)
- Epic 5: Tab Activatie - Stories 6-7 (5 pts)
- Epic 6: Prompt Optimalisatie - Story 3 (3 pts)
- Epic 7: Test Suite - Stories 1-2 (5 pts)
**Total**: 13 points

### Sprint 6 (2 weken)
- Epic 7: Test Suite - Stories 3-5 (13 pts)
**Total**: 13 points

## Voordelen van deze Structuur

1. **Kleinere Stories**: 1-5 story points per story
2. **Focus per Sprint**: Duidelijke deliverables
3. **Dependencies Clear**: Web lookup voor tab, etc.
4. **Incremental Value**: Elke sprint levert werkende features
5. **Risk Mitigation**: Technische basis eerst
6. **Measurable Progress**: 41 stories totaal vs 6 mega-stories

## Next Steps

1. Review & goedkeuring van epic structuur
2. Gedetailleerde story schrijven per epic
3. Verfijnen van story points na team input
4. Backlog grooming sessie plannen
5. Sprint 1 planning meeting

---
*Dit voorstel vervangt de huidige "1 epic, 6 stories" structuur met 7 focused epics en 41 kleinere stories*