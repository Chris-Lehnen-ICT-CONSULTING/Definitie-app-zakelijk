---
canonical: true
status: master-document
owner: development
last_verified: 2025-09-04
document_type: master-epics
priority: critical
sprint: UAT-2025-09
---

# 📚 MASTER DOCUMENT: Alle Epics & User Stories - DefinitieAgent

Dit is het centrale document met ALLE epics en user stories voor het DefinitieAgent project.

---

## 📊 Epic Overview Dashboard

**Business Value**: €1,000+/maand besparing bij volledig geïmplementeerd
**Performance Impact**: 50% snellere response tijd verwacht
**UAT Deadline**: 20 September 2025

| Epic | Naam | Completion | Priority | Stories |
|------|------|------------|----------|---------|
| **Epic 1** | Basis Definitie Generatie | 90% | ✅ Done | 5 stories |
| **Epic 2** | Kwaliteitstoetsing | 85% | ✅ Done | 10 stories |
| **Epic 3** | Content Verrijking & Web Lookup | 30% | 🔥 HIGH | 19 stories |
| **Epic 4** | User Interface | 30% | 📋 Medium | 15 stories |
| **Epic 5** | Export & Import | 10% | 📋 Low | 7 stories |
| **Epic 6** | Security & Auth | 0% | 🚨 CRITICAL | 5 stories |
| **Epic 7** | Performance & Scaling | 20% | 🔥 HIGH | 16 stories |
| **Epic 8** | Web Lookup Module (Legacy) | 10% | ⚠️ Merge → Epic 3 | 4 stories |
| **Epic 9** | Advanced Features | 5% | 🕐 Post-UAT | 5 stories |

**Totaal**: 86 User Stories (+19 toegevoegd)

---

# 📋 EPIC 1: BASIS DEFINITIE GENERATIE (90% Compleet)

**Doel**: Core functionaliteit voor het genereren van AI-powered definities

| Story ID | Titel | Status | Priority | Acceptance Criteria | Notes |
|----------|-------|--------|----------|-------------------|-------|
| **DEF-001** | Begrip invoeren | ✅ Compleet | P0 | • Min 3, max 100 chars<br>• Input validatie<br>• Geen speciale tekens | Werkend in productie |
| **DEF-002** | Context selecteren | ✅ Compleet | P0 | • Organisatorische context<br>• Juridische context<br>• Wettelijke basis | Multi-select mogelijk |
| **DEF-003** | AI-genereerde definitie | ✅ Compleet | P0 | • Response < 15 sec<br>• Min 80% kwaliteitsscore<br>• Error handling | GPT-4 integratie |
| **DEF-004** | Kwaliteitsscore weergeven | ✅ Compleet | P0 | • Score 0-100<br>• Kleurcodering<br>• Details per regel | 46 toetsregels |
| **DEF-005** | Duplicate check | 🔄 In Progress | P1 | • Check vóór generatie<br>• Similarity score<br>• Suggesties tonen | Backend klaar, UI ontbreekt |

---

# 📋 EPIC 2: KWALITEITSTOETSING (85% Compleet)

**Doel**: Validatie systeem met 46 toetsregels voor kwaliteitsborging

| Story ID | Titel | Status | Priority | Acceptance Criteria | Notes |
|----------|-------|--------|----------|-------------------|-------|
| **KWA-001** | Gedetailleerde validatie | ✅ Compleet | P0 | • Per regel resultaat<br>• Ernst niveau<br>• Uitleg bij fouten | 45/46 regels werkend |
| **KWA-002** | Suggesties voor verbetering | ✅ Compleet | P0 | • Concrete suggesties<br>• Direct toepasbaar<br>• Prioriteit weergave | AI-powered |
| **KWA-003** | Iteratieve verbetering | ✅ Compleet | P0 | • Max 3 iteraties<br>• Score tracking<br>• History behoud | IterativeDefinitionAgent |
| **KWA-004** | Custom toetsregels | ❌ Niet Gestart | P2 | • UI voor regel creatie<br>• Syntax validatie<br>• Test mogelijkheid | Backlog |
| **KWA-005** | Preventieve validatie | ❌ Niet Gestart | P1 | • Validate tijdens typen<br>• Real-time feedback<br>• Quick fixes | Efficiency boost |
| **KWA-006** | Bulk validatie | ❌ Niet Gestart | P2 | • Meerdere definities<br>• Batch rapport<br>• Export resultaten | Enterprise feature |
| **KWA-007** | Validatie templates | ❌ Niet Gestart | P2 | • Herbruikbare sets<br>• Context-specifiek<br>• Import/export | Configuratie |
| **KWA-008** | Validatie geschiedenis | ❌ Niet Gestart | P2 | • Track wijzigingen<br>• Score trends<br>• Analytics | Monitoring |
| **KWA-009** | Validatie API | ❌ Niet Gestart | P3 | • REST endpoint<br>• Webhook support<br>• Rate limiting | Integration |
| **KWA-010** | Validatie dashboard | ❌ Niet Gestart | P2 | • Statistieken<br>• Trends<br>• Rapporten | Management tool |

---

# 📋 EPIC 3: CONTENT VERRIJKING & WEB LOOKUP (30% Compleet)

**Doel**: Externe bronnen integratie en content verrijking - "METADATA EERST, PROMPT DAARNA"

| Story ID | Titel | Status | Priority | Acceptance Criteria | Notes |
|----------|-------|--------|----------|-------------------|-------|
| **ENR-001** | Synoniemen | ✅ Compleet | P1 | • Min 3 synoniemen<br>• Context-aware<br>• Kwaliteitscheck | 5 items standaard |
| **ENR-002** | Antoniemen | ✅ Compleet | P2 | • Min 2 antoniemen<br>• Relevantie check<br>• Optional field | 5 items standaard |
| **ENR-003** | Voorbeeldzinnen | 🔄 In Progress | P1 | • 3-5 zinnen<br>• Verschillende contexten<br>• Begrijpelijk | Backend klaar |
| **ENR-004** | Praktijkvoorbeelden | ❌ Niet Gestart | P2 | • Real-world cases<br>• Sector specifiek<br>• Bronvermelding | UI ontbreekt |
| **ENR-005** | Tegenvoorbeelden | ❌ Niet Gestart | P2 | • Wat het NIET is<br>• Veelvoorkomende fouten<br>• Helder onderscheid | Template bestaat |
| **ENR-006** | Toelichting | ❌ Niet Gestart | P2 | • Uitgebreide uitleg<br>• Achtergrond info<br>• Bronnen | Prompt bestaat |
| **WEB-3.1** | Sources Visibility in UI | ✅ Compleet | P0 | • Bronnen in metadata["sources"]<br>• UI toont bronnen<br>• Provider labels | **Implementatie:**<br>• `definition_orchestrator_v2.py:190-256`: Web lookup pre-step<br>• `definition_orchestrator_v2.py:443`: Sources in metadata<br>• `definition_generator_tab.py:750-816`: _render_sources_section<br>• `prompt_service_v2.py:288`: Provider-neutraal "Bron X" |
| **WEB-3.2** | Fix Context Flow (3 velden) | 🔴 TODO | P0 | • Alle 3 contextvelden in prompt<br>• Correct gecombineerd<br>• Logging compleet | **JOUW ISSUE #1**<br>**Probleem:** Alleen organisatorische_context komt mee<br>**Fix locatie:** `definition_generator_context.py:237-258`<br>**Oplossing:**<br>```python<br>context = {<br>  "organisatorische_context": self.organisatorische_context,<br>  "juridische_context": self.juridische_context,<br>  "wettelijke_basis": self.wettelijke_basis<br>}<br>``` |
| **WEB-3.3** | Prompt uit Metadata | 🔴 TODO | P0 | • Prompt uit metadata["sources"]<br>• Niet uit context["web_lookup"]<br>• Single source of truth | **JOUW ISSUE #4**<br>**Probleem:** Prompt gebruikt context["web_lookup"] i.p.v. metadata<br>**Fix:** Prompt service moet metadata["sources"] gebruiken<br>**Code:**<br>```python<br>sources = agent_result.get("metadata", {}).get("sources", [])<br>selected = [s for s in sources if s.get("used_in_prompt")]<br>``` |
| **WEB-3.4** | Wikipedia Adapter | ❌ Niet Gestart | P1 | • Contract compliant<br>• Content hash<br>• Is_authoritative flag | Ready to implement |
| **WEB-3.5** | SRU/Overheid Adapter | ❌ Niet Gestart | P1 | • XML parsing<br>• BWB identifiers<br>• Legal metadata | Juridische bronnen |
| **WEB-3.6** | Export met Bronnen | ❌ Niet Gestart | P2 | • JSON/TXT export<br>• Sources included<br>• Formatting correct | Quick win |
| **WEB-3.7** | Caching Layer | ❌ Niet Gestart | P1 | • TTL cache<br>• Provider-specifiek<br>• Cache invalidatie | Performance |
| **WEB-3.8** | Provider Monitoring | ❌ Niet Gestart | P2 | • Latency tracking<br>• Success rates<br>• Fallbacks | Observability |
| **WEB-3.9** | Content Sanitization | ❌ Niet Gestart | P1 | • XSS preventie<br>• HTML cleaning<br>• Safe rendering | Security |
| **WEB-3.10** | Ranking Algorithm | ❌ Niet Gestart | P1 | • Relevance scoring<br>• Authority weight<br>• Deduplication | Quality |
| **WEB-3.11** | Legal Metadata Parser | ❌ Niet Gestart | P1 | • ECLI extractie<br>• Artikel parsing<br>• Citation format | Juridisch |
| **WEB-3.12** | Source Attribution | ❌ Niet Gestart | P2 | • Proper citations<br>• License info<br>• Copyright | Compliance |
| **WEB-3.13** | Wiktionary Integration | ❌ Niet Gestart | P3 | • Dictionary lookups<br>• Etymology<br>• Translations | Enrichment |

---

# 📋 EPIC 4: USER INTERFACE (30% Compleet)

**Doel**: Alle UI tabs en gebruikersinteractie elementen

## UI Tabs

| Story ID | Titel | Status | Priority | Acceptance Criteria | Notes |
|----------|-------|--------|----------|-------------------|-------|
| **UI-001** | Definitie generator tab | ✅ Compleet | P0 | • Invoervelden<br>• Generate knop<br>• Resultaat display | Hoofdtab werkend |
| **UI-002** | History tab | ✅ Compleet | P0 | • Alle definities<br>• Filters<br>• Zoeken | Basis functionaliteit |
| **UI-003** | Export tab | ✅ Compleet | P1 | • TXT export<br>• Template keuze<br>• Download | Alleen TXT |
| **UI-004** | Web lookup tab | ❌ Niet Gestart | P2 | • Externe bronnen<br>• Resultaten tonen<br>• Bron validatie | Tab is leeg |
| **UI-005** | Expert review tab | ❌ Niet Gestart | P2 | • Review workflow<br>• Commentaar<br>• Goedkeuring | Backend ontbreekt |
| **UI-006** | Prompt viewer tab | ❌ Niet Gestart | P2 | • Toon prompts<br>• Debug info<br>• Token count | Development tool |
| **UI-007** | Monitoring tab | ❌ Niet Gestart | P2 | • Performance metrics<br>• API kosten<br>• Usage stats | Dashboard ontbreekt |
| **UI-008** | Management tab | ❌ Niet Gestart | P2 | • User management<br>• Settings<br>• Backups | Admin functionaliteit |
| **UI-009** | Orchestration tab | ❌ Niet Gestart | P3 | • Bulk operations<br>• Scheduling<br>• Workflows | Enterprise feature |
| **UI-010** | Quality control tab | 🔄 In Progress | P1 | • Toetsregel beheer<br>• Statistieken<br>• Configuratie | Deels werkend |

## UI Elements

| Story ID | Titel | Status | Priority | Acceptance Criteria | Notes |
|----------|-------|--------|----------|-------------------|-------|
| **UI-011** | Datum voorstel veld | ❌ Niet Gestart | P3 | • Datepicker<br>• Validatie<br>• Opslaan | Metadata veld |
| **UI-012** | Voorgesteld door veld | ❌ Niet Gestart | P3 | • Tekstveld<br>• Autocomplete<br>• Historie | Metadata veld |
| **UI-013** | Ketenpartners selectie | ❌ Niet Gestart | P2 | • Multi-select<br>• 8 opties<br>• Opslaan | ZM, DJI, KMAR, etc |
| **UI-014** | Ontologische score | 🔄 In Progress | P1 | • 4 categorieën<br>• Visualisatie<br>• Uitleg | Backend klaar |
| **UI-015** | Voorkeursterm selectie | ❌ Niet Gestart | P3 | • Uit synoniemen<br>• Radio buttons<br>• Opslaan | Bij synoniemen sectie |

---

# 📋 EPIC 5: EXPORT & IMPORT (10% Compleet)

**Doel**: Data exchange functionaliteit voor verschillende formaten

| Story ID | Titel | Status | Priority | Acceptance Criteria | Notes |
|----------|-------|--------|----------|-------------------|-------|
| **EXP-001** | TXT export | ✅ Compleet | P0 | • Platte tekst<br>• Template based<br>• UTF-8 | Werkend |
| **EXP-002** | Word export | ❌ Niet Gestart | P2 | • .docx format<br>• Styling behoud<br>• Template | python-docx needed |
| **EXP-003** | PDF export | ❌ Niet Gestart | P2 | • A4 format<br>• Logo mogelijk<br>• Watermark optie | ReportLab needed |
| **EXP-004** | Excel export | ❌ Niet Gestart | P3 | • Filters<br>• Grafieken<br>• Multi-sheet | Bulk export |
| **EXP-005** | JSON export | 🔄 In Progress | P1 | • Valid JSON<br>• Schema compliant<br>• Streaming | Backend ready |
| **IMP-001** | CSV import | ❌ Niet Gestart | P3 | • Bulk import<br>• Validatie<br>• Error rapport | Template needed |
| **IMP-002** | Document upload | 🔄 In Progress | P2 | • PDF/Word/TXT<br>• Context extractie<br>• Deduplicatie | DocumentProcessor exists |

---

# 📋 EPIC 6: SECURITY & AUTH (0% Compleet) 🚨

**Doel**: Security implementatie - KRITIEK ONTBREKEND!

| Story ID | Titel | Status | Priority | Acceptance Criteria | Notes |
|----------|-------|--------|----------|-------------------|-------|
| **SEC-001** | Gebruikers authenticatie | ❌ Niet Gestart | P0 | • Login/logout<br>• Password policy<br>• Session timeout | **KRITIEK MISSING** |
| **SEC-002** | Role-based access (RBAC) | ❌ Niet Gestart | P0 | • Admin/User/Viewer<br>• Permissions<br>• Audit trail | **KRITIEK MISSING** |
| **SEC-003** | API key management | ❌ Niet Gestart | P1 | • Generate keys<br>• Revoke access<br>• Usage limits | External access |
| **SEC-004** | Data encryptie | ❌ Niet Gestart | P1 | • At rest<br>• In transit<br>• Key rotation | SQLite plain text! |
| **SEC-005** | Audit logging | ❌ Niet Gestart | P1 | • Alle acties<br>• Timestamps<br>• User tracking | Compliance |

---

# 📋 EPIC 7: PERFORMANCE & SCALING (20% Compleet)

**Doel**: Optimalisatie voor snelheid en schaalbaarheid - INCLUSIEF JOUW ISSUES

| Story ID | Titel | Status | Priority | Acceptance Criteria | Notes |
|----------|-------|--------|----------|-------------------|-------|
| **PER-001** | Response tijd < 5 sec | ❌ Niet Gestart | P0 | • 95 percentile<br>• Monitoring<br>• Alerts | Nu 8-12 sec |
| **PER-002** | Caching implementatie | 🔄 In Progress | P0 | • Redis ready<br>• Hit rate >70%<br>• TTL config | Alleen in-memory nu |
| **PER-003** | Horizontal scaling | ❌ Niet Gestart | P2 | • Load balancing<br>• Session affinity<br>• Health checks | Kubernetes ready |
| **PER-004** | Async processing | 🔄 In Progress | P1 | • Queue based<br>• Progress updates<br>• Retry logic | Celery planned |
| **PER-005** | Database optimization | ✅ Compleet | P1 | • WAL mode<br>• Indexes<br>• Vacuum | SQLite optimized |
| **PER-006** | Prompt Token Reductie | 🔴 TODO | P0 | • 7,250 → 1,250 tokens<br>• 83% reductie<br>• Kwaliteit behoud | Prompt optimalisatie |
| **PER-007** | Context Flow Fix | 🔴 TODO | P0 | • Alle 3 contextvelden<br>• Juridisch + wettelijk<br>• Correct in prompt | **JOUW ISSUE #1** (Duplicate van WEB-3.2)<br>**Impact:** Definities missen 67% van context info<br>**Effort:** 1 dag<br>**Test:** Verify alle 3 velden in prompt aanwezig |
| **PER-008** | Toetsregel → Prompt Mapping | 🔴 TODO | P0 | • 45 YAML files<br>• Per regel instructie<br>• Context variaties | **JOUW ISSUE #2**<br>**Implementatie Plan:**<br>1. Create `config/prompt-instructions/{category}/{rule}.yaml`<br>2. YAML structuur:<br>```yaml<br>rule_id: ARAI-01<br>instruction: "Start NOOIT met werkwoord"<br>contexts:<br>  juridisch: "Juridische begrippen met substantief"<br>  dji: "Detentie-begrippen als naamwoord"<br>```<br>3. New `RulePromptMappingService`<br>4. Integration in prompt_service_v2.py |
| **PER-009** | Ontologie als Instructie | 🔴 TODO | P1 | • Geen vraagstelling<br>• Als INSTRUCTIE<br>• Per categorie | **JOUW ISSUE #3**<br>**Probleem:** "Wat is de ontologische categorie?" (fout)<br>**Oplossing:** "INSTRUCTIE: Definieer als {categorie}"<br>**Categorieën:**<br>• PROCES: handeling/activiteit<br>• OBJECT: fysiek/conceptueel ding<br>• ACTOR: persoon/organisatie<br>• TOESTAND: status/conditie |
| **PER-010** | Service Container Caching | ❌ Niet Gestart | P0 | • 6x → 1x init<br>• @st.cache_resource<br>• 50% sneller | Quick win |
| **PER-011** | Prompt Caching | ❌ Niet Gestart | P1 | • Cache built prompts<br>• Context-aware<br>• TTL strategy | Efficiency |
| **PER-012** | Result Caching | ❌ Niet Gestart | P1 | • Cache definitions<br>• Similarity check<br>• Smart invalidate | Deduplication |
| **PER-013** | Database Connection Pool | ❌ Niet Gestart | P2 | • Connection reuse<br>• Pool management<br>• Timeout handling | Scalability |
| **PER-014** | Memory Optimization | ❌ Niet Gestart | P2 | • Reduce footprint<br>• Garbage collection<br>• Stream processing | Resources |
| **PER-015** | API Rate Limiting | ❌ Niet Gestart | P1 | • Token bucket<br>• Per-user limits<br>• Backpressure | Protection |
| **PER-016** | Load Balancing | ❌ Niet Gestart | P3 | • Round robin<br>• Health checks<br>• Failover | Enterprise |

---

# 📋 EPIC 8: WEB LOOKUP MODULE - LEGACY (10% Compleet)

**Doel**: Legacy web lookup - WORDT GEMERGED MET EPIC 3

| Story ID | Titel | Status | Priority | Acceptance Criteria | Notes |
|----------|-------|--------|----------|-------------------|-------|
| **WEB-001** | Externe bronnen zoeken | 🔄 In Progress | P1 | • Multiple sources<br>• Relevantie ranking<br>• Caching | 5 broken implementations |
| **WEB-002** | Bron validatie | ❌ Niet Gestart | P2 | • Authority check<br>• Datum check<br>• Quality score | Planned |
| **WEB-003** | Automatische verrijking | ❌ Niet Gestart | P2 | • Context toevoegen<br>• Merge results<br>• Deduplicatie | AI-powered |
| **WEB-004** | Bron attributie | ❌ Niet Gestart | P2 | • Citaten<br>• Links<br>• Licentie info | Legal requirement |

---

# 📋 EPIC 9: ADVANCED FEATURES (5% Compleet)

**Doel**: Enterprise features voor post-UAT

| Story ID | Titel | Status | Priority | Acceptance Criteria | Notes |
|----------|-------|--------|----------|-------------------|-------|
| **ADV-001** | Bulk operations | ❌ Niet Gestart | P3 | • Multi-select<br>• Batch processing<br>• Progress bar | Enterprise |
| **ADV-002** | Version control | ❌ Niet Gestart | P3 | • Historie<br>• Diff view<br>• Rollback | Git-like |
| **ADV-003** | Collaboration | ❌ Niet Gestart | P3 | • Comments<br>• Mentions<br>• Notifications | Teams feature |
| **ADV-004** | API access | 🔄 In Progress | P2 | • REST endpoints<br>• Documentation<br>• Rate limiting | FastAPI migration |
| **ADV-005** | Custom workflows | ❌ Niet Gestart | P3 | • Drag & drop<br>• Conditions<br>• Actions | Workflow engine |

---

# 🎯 UAT PRIORITEIT RANKING (20 September 2025)

## 🔥 WEEK 1 (4-6 Sept): KRITIEKE FIXES

| Priority | Epic | Story | Effort | Impact |
|----------|------|-------|--------|---------|
| **P0** | 7 | PER-007: Context Flow Fix | 1 dag | Alle 3 velden werkend |
| **P0** | 3 | WEB-3.2: Context Flow Fix | 1 dag | Zelfde als PER-007 |
| **P0** | 3 | WEB-3.3: Prompt uit Metadata | 1 dag | Single source of truth |
| **P0** | 7 | PER-010: Service Caching | 0.5 dag | 50% performance boost |
| **P0** | 6 | SEC-001: Basic Auth | 1 dag | Minimale security |

## 📋 WEEK 2 (9-13 Sept): STRUCTURELE VERBETERINGEN

| Priority | Epic | Story | Effort | Impact |
|----------|------|-------|--------|---------|
| **P1** | 7 | PER-008: Toetsregel Mapping | 2 dagen | 45 regel instructies |
| **P1** | 7 | PER-009: Ontologie Instructie | 1 dag | Betere kwaliteit |
| **P1** | 7 | PER-006: Token Reductie | 1.5 dag | 83% minder tokens |
| **P1** | 3 | WEB-3.4: Wikipedia Adapter | 1 dag | Externe bronnen |
| **P1** | 3 | WEB-3.5: SRU Adapter | 1 dag | Juridische bronnen |

## ✨ WEEK 3 (16-20 Sept): UAT READINESS

| Priority | Epic | Story | Effort | Impact |
|----------|------|-------|--------|---------|
| **P2** | 3 | WEB-3.6: Export Bronnen | 0.5 dag | Completeness |
| **P2** | 5 | EXP-005: JSON Export | 0.5 dag | Data exchange |
| **P2** | 4 | UI-014: Ontologie Score | 0.5 dag | UI verbetering |
| **P2** | - | Integration Testing | 2 dagen | Kwaliteit |
| **P2** | - | UAT Preparation | 1 dag | Readiness |

---

## 📋 TECHNISCHE SPECIFICATIES

### Architectuur Componenten
| Component | Status | Locatie | Notes |
|-----------|--------|---------|-------|
| **DefinitionOrchestratorV2** | ✅ Actief | `src/services/orchestrators/definition_orchestrator_v2.py` | Hoofd coördinator |
| **ModernWebLookupService** | 🔄 Deels | `src/services/web_lookup/modern_web_lookup_service.py` | 5 broken implementations |
| **PromptServiceV2** | ✅ Actief | `src/services/prompts/prompt_service_v2.py` | Prompt builder |
| **ModularValidationService** | ✅ Actief | `src/services/validation/modular_validation_service.py` | 45/46 regels |
| **ServiceContainer** | ✅ Actief | `src/services/container.py` | DI container, 6x init probleem |

### Database Schema
```sql
-- data/definities.db (SQLite)
CREATE TABLE definitions (
    id INTEGER PRIMARY KEY,
    term TEXT NOT NULL,
    definition TEXT NOT NULL,
    metadata JSON,  -- Hier komen sources in
    created_at TIMESTAMP,
    score REAL
);
```

### Web Lookup Config
```yaml
# config/web_lookup_defaults.yaml
providers:
  wikipedia:
    enabled: true
    weight: 0.7
    min_score: 0.5
  sru_overheid:
    enabled: true
    weight: 1.0  # Juridisch = hogere weight
    min_score: 0.6
```

### Performance Bottlenecks
| Issue | Impact | Solution | Effort |
|-------|--------|----------|--------|
| Service 6x init | +3 sec startup | @st.cache_resource | 2 uur |
| Prompt tokens | 7,250 tokens | Deduplicatie | 1 dag |
| No caching | Elke keer opnieuw | Redis/in-memory | 1 dag |
| Sync processing | Blocking UI | Async/queue | 2 dagen |

---

## 🔧 IMPLEMENTATIE DETAILS PER STORY

### WEB-3.2: Context Flow Fix - Implementatie Stappen
1. **Locate:** `src/services/definition_generator_context.py:237-258`
2. **Update _build_base_context():**
   ```python
   def _build_base_context(self):
       return {
           "organisatorische_context": self.organisatorische_context or "",
           "juridische_context": self.juridische_context or "",
           "wettelijke_basis": self.wettelijke_basis or "",
           "combined": self._combine_all_contexts()
       }
   ```
3. **Update prompt templates** om alle 3 velden te gebruiken
4. **Add logging:** Log alle 3 context velden
5. **Test:** Verify in gegenereerde prompt

### PER-008: Toetsregel Mapping - Directory Structure
```
config/
├── prompt-instructions/
│   ├── arai/
│   │   ├── ARAI-01.yaml
│   │   ├── ARAI-02.yaml
│   │   └── ...
│   ├── con/
│   │   └── CON-01.yaml
│   ├── ess/
│   └── ...
```

### PER-009: Ontologie Instructies - Templates
```python
ONTOLOGY_INSTRUCTIONS = {
    "PROCES": """INSTRUCTIE: Definieer als PROCES (handeling/activiteit)
    - Focus op WAT er gebeurt
    - Beschrijf begin- en eindtoestand
    - Gebruik werkwoordstam als basis""",

    "OBJECT": """INSTRUCTIE: Definieer als OBJECT (ding/entiteit)
    - Focus op WAT het is
    - Beschrijf kenmerken en eigenschappen
    - Gebruik zelfstandig naamwoord""",

    "ACTOR": """INSTRUCTIE: Definieer als ACTOR (persoon/rol)
    - Focus op WIE en diens verantwoordelijkheden
    - Beschrijf bevoegdheden en taken""",

    "TOESTAND": """INSTRUCTIE: Definieer als TOESTAND (status/conditie)
    - Focus op de situatie/staat
    - Beschrijf wanneer deze van toepassing is"""
}
```

---

# 📊 SUMMARY METRICS

## Totaal Stories per Status
- ✅ **Compleet**: 18 stories (21%)
- 🔄 **In Progress**: 11 stories (13%)
- 🔴 **TODO (Jouw issues)**: 6 stories (7%)
- ❌ **Niet Gestart**: 51 stories (59%)
- **TOTAAL**: 86 stories

## Effort voor UAT (Jouw Issues)
- Context Flow Fix: 1 dag
- Prompt uit Metadata: 1 dag
- Toetsregel Mapping: 2 dagen
- Ontologie Instructie: 1 dag
- Token Reductie: 1.5 dag
- **TOTAAL**: 6.5 dagen

## Grootste Risico's
1. 🚨 **Security (Epic 6)**: 0% compleet = KRITIEK
2. 🔴 **Context Flow**: Alleen 1/3 velden werkend
3. ⚠️ **Performance**: 8-12 sec response tijd
4. 📋 **UI Tabs**: 70% ontbreekt

---

**Document Status**: Master Reference - SINGLE SOURCE OF TRUTH
**Laatste Update**: 4 September 2025 (v2.0 - Volledig)
**Owner**: Development Team
**UAT Deadline**: 20 September 2025

## 📋 Change Log
- v2.0 (4 Sept): +19 stories toegevoegd, business value toegevoegd
- v1.0 (4 Sept): Initiele consolidatie van alle epics

## ⚠️ SINGLE SOURCE OF TRUTH

Dit is het **COMPLETE MASTER DOCUMENT** voor het DefinitieAgent project. Dit document bevat:

✅ **Epic & Story Tracking:**
- Alle 86 user stories met real-time status
- Acceptance criteria per story
- Priority rankings (P0/P1/P2/P3)
- Effort schattingen in dagen

✅ **Technische Implementatie:**
- Code locaties voor elke fix (file:line)
- Database schema's en migrations
- Config file voorbeelden (YAML)
- API contracts en data structures

✅ **Implementatie Guides:**
- Step-by-step instructies per story
- Code snippets met voor/na voorbeelden
- Directory structures
- Test requirements en coverage targets

✅ **Performance & Optimalisatie:**
- Token reductie analyse (7,250 → 1,250 = 83% reductie)
- Performance bottlenecks & solutions
- Caching strategies (Redis, in-memory)
- Business value: €1,000+/maand besparing

✅ **Architectuur Details:**
- Component overzicht met status
- Service dependencies
- Database schema (SQLite)
- Config structures

**STATUS:** Dit document vervangt ALLE andere epic/story documenten:
- ❌ ~~epic-3-metadata-eerst-actieplan.md~~ → Inhoud nu hierin
- ❌ ~~epic-7-performance-optimization.md~~ → Inhoud nu hierin
- ❌ ~~prompt-refactoring/*.md~~ → Details nu hierin
- ❌ ~~REQUIREMENTS_AND_FEATURES_COMPLETE.md~~ → Stories nu hierin

**GEBRUIK:** Raadpleeg ALLEEN dit document voor:
- Sprint planning
- Story status
- Implementatie details
- UAT voorbereiding
- Development werk
- Progress tracking
