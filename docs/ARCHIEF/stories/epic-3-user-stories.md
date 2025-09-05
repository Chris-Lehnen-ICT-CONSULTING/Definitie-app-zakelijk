---
canonical: true
status: active
owner: product
last_verified: 2025-09-03
applies_to: definitie-app@v2.3
document_type: user-stories
epic: epic-3-web-lookup-modernization
priority: high
sprint: UAT-2025-09
---

# Epic 3: Web Lookup Modernization - User Stories

**Epic Goal**: Moderniseer de web lookup functionaliteit voor betere context verrijking met externe bronnen
**UAT Deadline**: 20 september 2025
**Geschatte Effort**: 6-8 dagen totaal
**Huidige Status**: 30% compleet (contract & backbone klaar)

---

## 📊 Story Overview

| Story ID | Titel | Status | Priority | Points | UAT Must |
|----------|-------|--------|----------|---------|----------|
| WEB-3.1 | Sources in Preview | 🔄 In Progress | P1 | 3 | ✅ |
| WEB-3.2 | Wikipedia Integration | ⏳ Ready | P1 | 2 | ✅ |
| WEB-3.3 | SRU Overheid Integration | ⏳ Ready | P1 | 2 | ✅ |
| WEB-3.4 | Source Display UI | ⏳ Ready | P1 | 2 | ✅ |
| WEB-3.5 | Prompt Augmentation | ✅ Done | P2 | 3 | ✅ |
| WEB-3.6 | Caching Layer | ⏳ Ready | P2 | 2 | ⚠️ |
| WEB-3.7 | Export with Sources | ⏳ Ready | P2 | 1 | ⚠️ |
| WEB-3.8 | Juridisch Priority | 📋 Planned | P3 | 2 | ❌ |
| WEB-3.9 | Multi-provider Search | 📋 Planned | P3 | 3 | ❌ |
| WEB-3.10 | Source Quality Scoring | 📋 Planned | P3 | 2 | ❌ |

**Totaal voor UAT**: 9 story points (4-5 dagen)
**Nice to have**: 13 story points (6-7 dagen)

---

## 🎯 User Stories Detail

### Story WEB-3.1: Sources in Preview (In Progress)
**Als** gebruiker
**Wil ik** bronnen zien tijdens preview generatie
**Zodat** ik weet welke externe informatie gebruikt wordt

**Acceptance Criteria:**
- [ ] Sources worden opgeslagen in definition.metadata["sources"]
- [ ] UI toont sources tijdens preview (niet alleen na save)
- [ ] Legacy wrapper volledig verwijderd
- [ ] Sources blijven persistent na opslaan
- [ ] Geen duplicaat lookups bij preview → save flow

**Technical Notes:**
- Verwijder LegacyGenerationResult wrapper
- DirectResult approach implementeren
- Metadata flow van orchestrator → UI fixen

**Effort**: 3 points (4 uur werk remaining)
**Status**: IMPLEMENTING - Legacy wrapper removal

---

### Story WEB-3.2: Wikipedia Integration
**Als** gebruiker
**Wil ik** relevante Wikipedia informatie bij mijn definitie
**Zodat** ik encyclopedische context heb

**Acceptance Criteria:**
- [ ] Wikipedia NL API werkend
- [ ] Fallback naar Wikipedia EN indien NL niet beschikbaar
- [ ] Max 500 chars snippet extractie
- [ ] Sanitization van HTML/wiki markup
- [ ] Score based op relevantie (0.0-1.0)
- [ ] Error handling voor timeout/rate limits

**Technical Notes:**
```python
# Implementatie in src/services/web_lookup/providers/wikipedia.py
class WikipediaProvider(BaseProvider):
    def search(term: str) -> List[WebLookupResult]
    # Use existing adapter pattern
```

**Effort**: 2 points (1 dag)
**Dependencies**: Contract implementation (✅ Done)

---

### Story WEB-3.3: SRU Overheid Integration
**Als** juridisch medewerker
**Wil ik** officiële overheidsbronnen bij definities
**Zodat** ik wettelijke context kan valideren

**Acceptance Criteria:**
- [ ] SRU protocol correct geïmplementeerd
- [ ] Overheid.nl catalog doorzoeken
- [ ] Rechtspraak.nl integratie
- [ ] BWB identifiers extractie
- [ ] Autoritatieve markering (is_authoritative=true)
- [ ] Juridisch gewicht scoring (legal_weight)

**Technical Notes:**
- Fix bestaande 404 errors in SRU
- Implementeer proper XML parsing
- Cache juridische lookups langer (24h)

**Effort**: 2 points (1 dag)
**Risk**: SRU API instabiliteit

---

### Story WEB-3.4: Source Display UI
**Als** gebruiker
**Wil ik** gebruikte bronnen zien in de interface
**Zodat** ik de herkomst kan verifiëren

**Acceptance Criteria:**
- [ ] Bronnen sectie in definitie detail view
- [ ] Clickable links naar originele bronnen
- [ ] Visual indicator voor gebruikt in prompt (✓)
- [ ] Provider logo/icon weergave
- [ ] Datum van ophalen tonen
- [ ] Score/relevantie indicator

**UI Mockup:**
```
📚 Gebruikte Bronnen (3)
├── ✓ Wikipedia NL - "Definitie" (95% relevant)
├── ✓ Overheid.nl - "Wet op..." (87% relevant)
└── ○ Rechtspraak.nl - "Uitspraak..." (72% relevant)
```

**Effort**: 2 points (1 dag)
**Dependencies**: WEB-3.1 completion

---

### Story WEB-3.5: Prompt Augmentation (✅ DONE)
**Als** systeem
**Wil ik** relevante context injecteren in prompts
**Zodat** de AI betere definities genereert

**Acceptance Criteria:**
- [x] Token budget respecteren (max 1000 tokens)
- [x] Top-K sources selectie (K=3 default)
- [x] Context positie configureerbaar
- [x] Source attributie in prompt
- [x] Juridische bronnen prioriteit

**Status**: GEÏMPLEMENTEERD in PromptServiceV2

---

### Story WEB-3.6: Caching Layer
**Als** systeem
**Wil ik** lookup resultaten cachen
**Zodat** performance optimaal blijft

**Acceptance Criteria:**
- [ ] Redis cache configuratie
- [ ] TTL per provider type (Wiki=1h, SRU=24h)
- [ ] Cache key op normalized term
- [ ] Stale-while-revalidate strategie
- [ ] Cache metrics/monitoring
- [ ] Manual cache clear optie

**Technical Notes:**
```python
@st.cache_data(ttl=3600)
def cached_lookup(term: str, provider: str) -> List[WebLookupResult]
```

**Effort**: 2 points (1 dag)
**Priority**: P2 - Nice to have voor UAT

---

### Story WEB-3.7: Export with Sources
**Als** gebruiker
**Wil ik** bronvermelding in exports
**Zodat** definities traceerbaar zijn

**Acceptance Criteria:**
- [ ] TXT export bevat bronnenlijst
- [ ] Word export met hyperlinks
- [ ] PDF export met voetnoten
- [ ] JSON export bevat volledig metadata
- [ ] Configureerbaar per export type

**Export Format Example:**
```
BRONNEN:
[1] Wikipedia NL - "Definitie" - https://nl.wikipedia.org/...
[2] Overheid.nl - "Wet op..." - https://wetten.overheid.nl/...
```

**Effort**: 1 point (0.5 dag)
**Priority**: P2 - Nice to have

---

### Story WEB-3.8: Juridisch Priority (Future)
**Als** juridisch specialist
**Wil ik** juridische bronnen voorrang geven
**Zodat** wettelijke definities leidend zijn

**Acceptance Criteria:**
- [ ] Configureerbare provider weights
- [ ] Juridische bronnen 2x gewicht
- [ ] BWB linking voor wetsartikelen
- [ ] ECLI linking voor jurisprudentie
- [ ] Kamerstuk referenties

**Effort**: 2 points
**Status**: POST-UAT

---

### Story WEB-3.9: Multi-provider Search (Future)
**Als** power user
**Wil ik** meerdere bronnen parallel doorzoeken
**Zodat** ik comprehensive resultaten krijg

**Acceptance Criteria:**
- [ ] Parallel provider execution
- [ ] Configurable provider list
- [ ] Result merging/deduplication
- [ ] Provider health monitoring
- [ ] Fallback chain configuration

**Effort**: 3 points
**Status**: POST-UAT

---

### Story WEB-3.10: Source Quality Scoring (Future)
**Als** kwaliteitsmanager
**Wil ik** bron betrouwbaarheid scoren
**Zodat** alleen quality sources gebruikt worden

**Acceptance Criteria:**
- [ ] Authority scoring algorithm
- [ ] Recency weighting
- [ ] Citation count integration
- [ ] User feedback incorporation
- [ ] Quality threshold configuration

**Effort**: 2 points
**Status**: POST-UAT

---

## 🚀 Implementation Plan voor UAT

### Week 1 (4-6 Sep): Foundation
**Doel**: Basis web lookup werkend

1. **Dag 1**: Complete WEB-3.1 (Sources in Preview)
   - Legacy wrapper removal (2 uur)
   - Test metadata flow (2 uur)

2. **Dag 2**: WEB-3.2 (Wikipedia Integration)
   - API connection (4 uur)
   - Snippet extraction (4 uur)

3. **Dag 3**: WEB-3.3 (SRU Integration)
   - Fix 404 errors (4 uur)
   - XML parsing (4 uur)

### Week 2 (9-13 Sep): UI & Polish
**Doel**: Gebruiker kan bronnen zien

4. **Dag 4**: WEB-3.4 (Source Display)
   - UI componenten (4 uur)
   - Styling & icons (4 uur)

5. **Dag 5**: Testing & Bug fixes
   - Integration tests (4 uur)
   - Performance tuning (4 uur)

### Week 3 (16-20 Sep): Optional
6. **IF TIME**: WEB-3.6 (Caching)
7. **IF TIME**: WEB-3.7 (Export)

---

## ✅ Definition of Done

Een story is DONE wanneer:
1. Code geïmplementeerd volgens contract
2. Unit tests >80% coverage
3. Integration test passing
4. UI getest in Chrome/Firefox
5. Documentatie bijgewerkt
6. Code review completed
7. Merged naar main branch

---

## 📊 Risk Matrix

| Risk | Impact | Kans | Mitigatie |
|------|--------|------|-----------|
| SRU API instabiel | High | Medium | Fallback naar cache |
| Wikipedia rate limits | Medium | Low | Implement throttling |
| Performance degradatie | High | Low | Caching layer |
| UI complexity | Medium | Medium | Simplify voor UAT |

---

## 🎯 Success Metrics

- **Minimaal 2 bronnen** werkend voor UAT (Wiki + SRU)
- **Sources zichtbaar** in UI tijdens preview
- **Response tijd** <2s voor lookups (met cache)
- **Zero duplicaat** lookups in preview→save flow
- **100% traceerbaarheid** van gebruikte bronnen

---

*Document aangemaakt: 3 september 2025*
*Epic Owner: Product Team*
*Technical Lead: Development Team*
*Voor UAT: Focus op WEB-3.1 t/m WEB-3.4*
