# EPIC-012: Legacy Orchestrator Refactoring

## Epic Overview
**ID**: EPIC-012
**Titel**: Refactor legacy orchestrators met behoud van business kennis
**Status**: TODO
**Priority**: HIGH - NEXT UP
**Created**: 2025-01-10
**Updated**: 2025-09-11
**Progress**: US-061 COMPLETED - Business kennis geëxtraheerd en gedocumenteerd
**Decision (2025-09-11)**: Start met US-064 vóór US-062 voor maximale waarde
**Follow-up**: Zie [EPIC-014](../EPIC-014/EPIC-014.md) voor implementatie van geëxtraheerde business logic
**Owner**: Development Team
**Sprint Planning**: Week 2 September 2025 (Na EPIC-010 completion)

## Business Value
De applicatie bevat waardevolle business logica verspreid over 8 legacy bestanden. Deze refactoring zal:
- **Business kennis consolideren** in moderne V2 architectuur
- **Intelligente feedback logica behouden** met 11+ validatie mappings
- **Performance optimalisaties integreren** uit legacy code
- **Code kwaliteit verbeteren** zonder functionaliteit verlies
- **Single source of truth** creëren voor orchestration

## Scope
### In Scope
- Extractie en documentatie van alle business regels uit legacy
- Refactoring van business logica naar moderne V2 services
- Consolidatie van 8 legacy bestanden naar geïntegreerde V2 modules
- Behoud van alle intelligente algoritmes (feedback, status, improvement)
- Creatie van nieuwe services waar nodig voor business logica

### Out of Scope
- Backwards compatibility (single user applicatie)
- Database migraties
- UI redesign
- Feature toevoegingen

## Technical Context

### Legacy Components te REFACTOREN (niet verwijderen!)
1. **DefinitionOrchestrator V1** (`src/services/definition_orchestrator.py`) - 530 regels
   - Bevat: Status bepaling algoritme, update flow, stats tracking
2. **DefinitieAgent System** (`src/orchestration/definitie_agent.py`) - 1034 regels
   - Bevat: FeedbackBuilder, iterative improvement, performance optimalisaties
3. **Legacy Generator Modules** (6 bestanden):
   - `definition_generator_config.py` - Business configuratie parameters
   - `definition_generator_context.py` - EnrichedContext management
   - `definition_generator_enhancement.py` - Enhancement business rules ⚠️ **Bevat domein field references**
   - `definition_generator_prompts.py` - Prompt building intelligence
   - `definition_generator_cache.py` - Performance optimalisaties
   - `definition_generator_monitoring.py` - Metrics en monitoring logica

**Note:** Deze modules bevatten de domein field references die door CI gates zijn gedetecteerd.

### Waardevolle Business Kennis te EXTRAHEREN en BEHOUDEN
- **FeedbackBuilder** met 11 violation mappings
- **Status bepaling** (draft/review/established)
- **Iterative improvement** met stop criteria
- **Performance optimalisaties** (voorbeelden caching)
- **Update flow** met selective validation
- **Audit trail** (originele tekst opslag)

## User Stories

| ID | Titel | Priority | Points | Status |
|----|-------|----------|--------|--------|
| US-061 | Extract en documenteer business kennis uit legacy | CRITICAL | 5 | **COMPLETED** ✅ |
| US-064 | Consolideer orchestration logica | HIGH | 8 | TODO | NEXT |
| US-062 | Refactor FeedbackBuilder naar moderne service | CRITICAL | 8 | TODO |
| US-063 | Integreer legacy config en context in V2 | HIGH | 5 | TODO |
| US-065 | Moderniseer UI dependencies | MEDIUM | 3 | TODO |
| US-066 | Verwijder Legacy DefinitieAgent uit Integratie/UI | HIGH | 5 | TODO |
| US-067 | ServiceFactory Stateless Maken | HIGH | 3 | TODO |
| US-068 | Verwijder Domein Restanten | MEDIUM | 3 | TODO |
| US-069 | Archiveer V1 Orchestrator | MEDIUM | 8 | TODO |
| US-070 | Refactor Category State Manager | MEDIUM | 3 | TODO |
| US-071 | Resilience-consolidatie naar één module | MEDIUM | 5 | TODO |
| US-072 | Export-consolidatie en mappen-opschoning | MEDIUM | 3 | TODO |
| US-073 | Config-harmonisatie, verwijderen dotenv | HIGH | 3 | TODO |
| US-074 | Import-hygiëne, geen sys.path-hacks | HIGH | 5 | TODO |
| US-075 | Centraliseer async/sync-bridging | HIGH | 5 | TODO |
| US-076 | Validators JSON-first + basisklasse | MEDIUM | 8 | TODO |
| US-078 | Test-hygiëne, scheiding bron/test | LOW | 2 | TODO |

**Totaal Story Points**: 51 (was 29) + 31 (US-071..US-076, US-078) = 82

## Dependencies
- Geen externe dependencies
- V2 orchestrator moet volledig functioneel zijn (✅ compleet)
- Alle tests moeten groen zijn voor start
- EPIC-010 fixes moeten eerst geïmplementeerd zijn voor consistente context flow

## Relatie met EPIC-010
De nieuwe user stories (US-066 t/m US-070) zijn geïdentificeerd tijdens de EPIC-010 analyse:
- **US-066**: Lost inconsistente context/voorbeelden flow op door DefinitieAgent te verwijderen
- **US-067**: Garandeert stateless services principe van EPIC-010
- **US-068**: Verwijdert verwarring rond context model (domein vs moderne velden)
- **US-069**: Consolideert orchestration naar V2-only
- **US-070**: Scheidt UI concerns van service layer

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Verlies business kennis | HIGH | LOW | Uitgebreide documentatie en extractie fase |
| Onduidelijke business rules | MEDIUM | MEDIUM | Business logic eerst documenteren, dan refactoren |
| Performance degradatie | MEDIUM | LOW | Legacy optimalisaties analyseren en overnemen |
| Incomplete refactoring | HIGH | LOW | Stapsgewijze aanpak met verificatie |

## Definition of Done
- [ ] Alle business kennis gedocumenteerd en geëxtraheerd
- [ ] Legacy code gerefactored naar V2 architectuur
- [ ] FeedbackBuilder volledig geïntegreerd in V2
- [ ] Status bepaling algoritme behouden in V2
- [ ] Iterative improvement logica werkend in V2
- [ ] Alle tests groen
- [ ] Performance gelijk of beter
- [ ] Business logica documentatie compleet

## Success Metrics
- **Business kennis behoud**: 100% van intelligente algoritmes
- **Code kwaliteit**: Moderne V2 patterns overal
- **Performance**: Gelijk of beter dan legacy
- **Functionaliteit**: Alle features blijven werken
- **Documentatie**: Elke business rule gedocumenteerd

## Implementation Plan

### Phase 1: Business Knowledge Extraction (US-061)
**Week 1** - Documenteer alle business logica
- Analyseer en documenteer FeedbackBuilder algoritmes
- Extract status bepaling regels
- Document iterative improvement logica
- Identificeer alle performance optimalisaties

### Phase 2: Orchestration Consolidation (US-064)
**Week 1-2** - Verenig orchestration logica (PRIORITY FIRST)
- Integreer iterative improvement haakjes in V2
- Implementeer update_definition flow (edit → re‑validate)
- Consolideer stats tracking

### Phase 3: FeedbackBuilder Refactoring (US-062)
**Week 2-3** - Kritieke service ná US‑064
- Creëer FeedbackServiceV2 met 11 mappings (Fase 1)
- Integreer violation feedback (post‑validatie hook in DefinitionOrchestratorV2)
- Implementeer pattern suggestions en prioritering
- A/B test vs legacy en uitbreiden via mapping‑config

### Phase 3: Config & Context Integration (US-063)
**Week 2** - Consolideer configuratie
- Merge UnifiedGeneratorConfig naar V2
- Refactor EnrichedContext naar ContextServiceV2
- Behoud alle business parameters

### Phase 4: Config & Context Integration (US-063)
**Week 3** - Consolideer configuratie
- Merge UnifiedGeneratorConfig naar V2
- Refactor EnrichedContext naar ContextServiceV2
- Behoud alle business parameters

### Phase 5: UI Modernization (US-065)
**Week 3** - Update dependencies
- Refactor imports naar V2 services
- Test UI met nieuwe services
- Verificatie complete functionaliteit

## Notes
- **REFACTORING, geen backwards compatibility** - single user applicatie
- **Business kennis is prioriteit #1** - eerst extraheren, dan refactoren
- **Legacy code pas verwijderen** na verificatie dat alle kennis behouden is
- **Documenteer elke business regel** tijdens extractie
- **Test driven refactoring** - eerst tests voor business logica, dan refactoren

## Related Documentation
- Code Audit
- EPIC-010 - Related context flow refactoring
- US-043 - Related legacy context routes removal
- US-056 - Related legacy session state removal
- V2 Architecture
- Migration Guidelines
