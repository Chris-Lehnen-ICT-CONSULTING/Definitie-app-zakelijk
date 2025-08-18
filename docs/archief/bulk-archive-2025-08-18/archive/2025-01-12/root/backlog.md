# DefinitieAgent Backlog

## 📊 Overzicht

**Totaal items**: 77+ backlog items gevonden
**Status verdeling**:
- ✅ Done: 3 items
- 🔄 In Progress: 5 items  
- 📝 To Do: 69+ items

**Laatste update**: 2025-01-18  
**Volgende review**: Planning sprint 5

---

## ✅ Voltooide Items

### Recente Fixes (Juli 2025)
- **Temperature Config Fix**: Voorkom dat None overrides de temperature defaults overschrijven ✅ (commit 41ba17d)
- **Voorkeursterm Selectie**: Voeg oorspronkelijk begrip toe als optie bij voorkeursterm selectie ✅ (commit a3f4bee)
- **Services Consolidatie**: 3 services samengevoegd naar UnifiedDefinitionService ✅

### Ontologische Categorie Verbetering
- **ID**: ONTOLOGIE-001
- **Status**: **VOLTOOID** (2025-01-17)
- **Nieuwe methode**: 6-stappen wetenschappelijk protocol geïmplementeerd
- **Resultaat**: Wetenschappelijk gefundeerde ontologische categorisering met 80%+ accuracy

### Toetsregels Implementatie
- **BLG-INT-07-001**: Toetsregel INT-07 geïmplementeerd ✅
- **BLG-STR-01-002**: Toetsregel STR-01 toegevoegd ✅

---

## 🔄 In Progress

### 🚀 Performance & AI Optimalisatie

#### BLG-PRM-009: Versnellen definitiegeneratie en AI-toetsing
- **Prioriteit**: Hoog
- **Sprint**: 4
- **Probleem**: GPT-4 is traag, AI-calls worden sequentieel uitgevoerd
- **Oplossing**: 
  - Parallelle AI-calls implementeren
  - Toggle voor GPT-4 vs GPT-3.5/GPT-4o
  - Performance logging toevoegen
- **Status**: In ontwikkeling

### 🔧 Configuratie & Settings

#### GPT-Temp-Config: Temperatuur centraal beheren
- **Prioriteit**: Hoog (quick win)
- **Sprint**: 1
- **Doel**: Temperatuurparameter uit code halen naar config
- **Status**: Doing

#### Backlogitem_instelbare_temperatuur_per_prompt
- **Prioriteit**: Midden
- **Sprint**: 4
- **Doel**: UI slider voor dynamische temperatuur per opdracht
- **Status**: Doing

---

## 📝 To Do Items (Geprioriteerd)

### 🚨 High Priority (Sprint 4-5)

#### AI & Toetsing Verbeteringen

**BLG-AI-TOETSING-001**: Voeg toetsregels toe aan AI-prompt
- **Impact**: AI genereert nu content die vaak toetsregels schendt
- **Oplossing**: Integreer toetsregels direct in prompts
- **Bestanden**: prompt_generator.py, toetsregels.json

**BLG-ARAI06**: Synchroniseer detectie verboden beginconstructies
- **Probleem**: Verschil tussen toetsing en opschoning logica
- **Oplossing**: Centrale regex module voor consistentie

**BLG-ARAI07**: Controleer verbod op beginwoorden
- **Doel**: Detecteer "is", "de", begrip zelf aan begin definitie
- **Impact**: Verbeterde definitiekwaliteit

**BLG-AUTO-RETOETS**: Automatische hertoetsing na aanpassing
- **Probleem**: Alleen oorspronkelijke output wordt getoetst
- **Oplossing**: Live hertoetsing bij wijzigingen in UI

#### Validatie & Toetsregels

**BLG-ESS03-AANPASSING**: Verfijn ESS-03 toetsregel
- **Doel**: Betere detectie essentie en kenmerken
- **Prioriteit**: Hoog

**BLG-CON-01**: Consistentiecontrole termen
- **Doel**: Detecteer inconsistent gebruik termen in definitie
- **Impact**: Hogere kwaliteit juridische teksten

### 📊 Medium Priority (Sprint 5-6)

#### UI/UX Verbeteringen

**BLG-UI-011**: Voeg goedkeuringsvelden per veld toe
- **Doel**: Expliciete akkoord-knop per definitieveld
- **Impact**: Betere traceerbaarheid goedkeuringen

**BLG-UI-PAGINATION**: Paginering voor lange resultaten
- **Probleem**: UI traag bij >30 toetsregels
- **Oplossing**: 10 items per pagina met navigatie

**BLG-KEY-UNIEK**: Fix Streamlit duplicate key errors
- **Doel**: Automatische unieke widget keys
- **Impact**: Stabielere UI zonder conflicts

**BLG-MULTISELECT**: Bulk acties voor begrippen
- **Doel**: Selecteer meerdere begrippen voor batch operaties
- **Bestanden**: ui_helpers.py

#### Export & Rapportage

**BLG-EXPORT-PDF**: PDF export per begrip
- **Doel**: Printklare versie enkele definitie
- **Format**: Professionele layout met metadata

**BLG-EXPORT-EXCEL**: Uitgebreide Excel export
- **Doel**: Volledige dataset met filters en grafieken
- **Extra**: Pivot tables voor analyse

**BLG-JSONL-DOWNLOAD-002**: Verbeterde JSONL export
- **Doel**: Streaming download grote datasets
- **Impact**: Memory-efficient export

#### Bronnen & Context

**BLG-BRONNEN-01**: Bronnenbeheer systeem
- **Doel**: Centrale opslag gebruikte bronnen
- **Features**: Versioning, metadata, search

**BLG-BRON-BEHEER-UI**: UI voor bronnenbeheer
- **Doel**: Upload, categoriseer, beheer bronnen
- **Impact**: Betere traceerbaarheid

**Backlogitem_Lookup_Bronvermelding_Artikelniveau**
- **Doel**: Specifieke artikelverwijzingen in bronnen
- **Status**: Doing

### 🔧 Technical Debt & Testing

#### Testing & Quality

**BLG-SMOKETEST-CI**: Automatische smoke tests
- **Prioriteit**: Hoog
- **Doel**: CI/CD pipeline met basis tests
- **Coverage**: Definitiegeneratie, toetsing, exports

**BLG-SIMULATIE-TEST**: Simulatie test framework
- **Doel**: Test edge cases met gesimuleerde data
- **Impact**: Betere test coverage

**BLG-VB-TESTLOG**: Verbeterde test logging
- **Doel**: Gedetailleerde test resultaten
- **Format**: Structured logging met context

#### Code Quality

**BLG-VERB-WORD-MODULE**: Centrale verboden woorden module
- **Doel**: DRY principe voor pattern matching
- **Impact**: Consistente detectie

**BLG-REGEL-AANPASSER-MODULE**: Dynamische regel configuratie
- **Doel**: Toetsregels aanpasbaar zonder code wijziging
- **Format**: JSON/YAML configuratie

### 🎯 Future Enhancements

#### Advanced AI Features

**BLG-RAG-001**: RAG implementatie voor context
- **Doel**: Gebruik eigen documenten als context
- **Tech**: Vector database + retrieval

**BLG-PROMPTLEREN-001**: Lerende prompts
- **Doel**: Prompts verbeteren op basis feedback
- **Method**: Fine-tuning of few-shot learning

**BLG-FB-LOOP**: Feedback loop generator-validator
- **Doel**: Automatisch verbeteren definities
- **Impact**: Hogere first-time-right score

#### Integraties

**BLG-KETENPARTNER-UI**: Ketenpartner integratie
- **Doel**: Deel definities met externe systemen
- **Protocol**: REST API of webhooks

**BLG-CONTEXTBEHEER-UI**: Context management UI
- **Doel**: Beheer verschillende contexts/domeinen
- **Features**: Templates, inheritance, versioning

---

## 🚫 Verouderde/Duplicate Items

### Geïdentificeerde Duplicaten
- Temperatuur configuratie: 3 overlappende items
- UI feedback: Meerdere vergelijkbare items
- Export functionaliteit: Overlap tussen formats

### Te Consolideren
1. Alle temperatuur-gerelateerde items → 1 configuratie epic
2. UI approval items → 1 UI/UX verbetering epic
3. Export items → 1 export framework epic

---

## 📈 Quick Wins

1. **GPT-Temp-Config**: Temperatuur naar config (1-2 uur werk)
2. **BLG-KEY-UNIEK**: Widget key helper functie (2-3 uur)
3. **BLG-LOG-VIEWER-001**: Simpele log viewer in UI (3-4 uur)
4. **BLG-TXT-EXP**: Plain text export optie (1-2 uur)

---

## 🔗 Dependencies

### Kritieke Paden
1. **AI Optimalisatie** → Performance tests → Monitoring
2. **Toetsregels** → Centrale module → UI feedback
3. **Export** → Formatting → Templates → Batch processing
4. **RAG** → Vector DB → Document upload → Context search

### Blokkeringen
- UI pagination geblokkeerd door widget key issues
- RAG implementatie wacht op document upload functionaliteit
- Feedback loop heeft eerst betere logging nodig

---

## 📋 Sprint Planning Suggestie

### Sprint 5 (2 weken)
**Focus**: Performance & UI Stabiliteit
1. BLG-PRM-009: Performance optimalisatie (afmaken)
2. BLG-KEY-UNIEK: Widget key fixes (quick win)
3. BLG-AUTO-RETOETS: Automatische hertoetsing
4. BLG-UI-011: Goedkeuringsvelden
5. BLG-SMOKETEST-CI: Basis CI/CD pipeline

### Sprint 6 (2 weken)
**Focus**: Export & Rapportage
1. BLG-EXPORT-PDF: PDF export
2. BLG-EXPORT-EXCEL: Excel export
3. BLG-JSONL-DOWNLOAD-002: Streaming JSONL
4. BLG-UI-PAGINATION: Paginering implementeren
5. BLG-LOG-VIEWER-001: Log viewer in UI

### Sprint 7 (2 weken)
**Focus**: AI & Toetsing Verbetering
1. BLG-AI-TOETSING-001: Toetsregels in prompts
2. BLG-ARAI06 + BLG-ARAI07: Verboden constructies
3. BLG-ESS03-AANPASSING: Essentie detectie
4. BLG-CON-01: Consistentie controle
5. BLG-VERB-WORD-MODULE: Centrale pattern module

### Backlog Grooming Needed
- Consolideer overlappende items
- Prioriteer op basis van gebruikersfeedback
- Verfijn effort schattingen
- Update dependencies

---

## 🏷️ Labels & Categorieën

### Categorie Tags
- `bug`: Defecten en fouten
- `feature`: Nieuwe functionaliteit
- `enhancement`: Verbeteringen bestaande features
- `tech-debt`: Technische schuld
- `performance`: Performance optimalisaties
- `ui-ux`: User interface/experience
- `ai-ml`: AI/ML gerelateerd
- `validation`: Toetsing en validatie
- `export`: Export functionaliteit
- `testing`: Test gerelateerd
- `documentation`: Documentatie updates

### Prioriteit Tags
- `p0-critical`: Blokkerend/kritiek
- `p1-high`: Hoge prioriteit
- `p2-medium`: Medium prioriteit
- `p3-low`: Lage prioriteit
- `quick-win`: Snel te realiseren

### Effort Tags
- `xs`: < 1 dag
- `s`: 1-2 dagen
- `m`: 3-5 dagen
- `l`: 1-2 weken
- `xl`: > 2 weken