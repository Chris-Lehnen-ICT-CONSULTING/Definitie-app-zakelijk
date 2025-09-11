---
titel: EPIC-010 Gaps Analysis - Review Punten vs User Stories
aangemaakt: 2025-09-10
status: Analyse
---

# 📊 EPIC-010 Gaps Analysis

## Overzicht

Dit document analyseert of alle review punten uit het v2 plan gedekt zijn door user stories/bugs in EPIC-010.

## ✅ Gedekte Punten

### 1. UI Migratie + Wrapper Removal
**Review punt:** UI migratie en wrapper removal op dezelfde dag
**Gedekt door:** 
- ✅ US-043-B: Migreer UI naar Async Bridge
- ✅ US-043-C: Verwijder Deprecated Sync Methods
**Status:** Volledig gedekt, inclusief acceptance criteria

### 2. Legacy Routes Removal
**Review punt:** Elimineer service-laag bridging
**Gedekt door:**
- ✅ US-043: Remove Legacy Context Routes (hoofdstory)
- ✅ US-043 sub-stories voor specifieke onderdelen
**Status:** Volledig gedekt

### 3. E2E Testing
**Review punt:** End-to-end tests voor context flow
**Gedekt door:**
- ✅ US-050: Create End-to-End Context FLAAG Tests
- ✅ US-043-E: E2E Test Suite Update
**Status:** Volledig gedekt

### 4. CFR-BUG-014
**Review punt:** Fix synoniemen/antoniemen generatie
**Gedekt door:**
- ✅ CFR-BUG-014 genoemd in EPIC-010 (regel 336)
**Status:** Bug is geïdentificeerd maar GEEN dedicated user story

## ❌ Ontbrekende User Stories

### 1. CFR-BUG-014 Fix Implementation
**Review punt:** 
- Prompts met definitie + context toevoegen
- Retry logic (max 1 retry, accepteer <N op laatste)
- UI display zonder bullets
- Parser met komma-fallback

**Ontbreekt:** Dedicated user story voor bug fix
**Voorstel:** Maak US-051: Fix CFR-BUG-014 Synoniemen/Antoniemen Generatie

### 2. Timeout Config via rate_limit_config
**Review punt:** Gebruik bestaande rate_limit_config.py ipv nieuwe timeouts.yaml
**Gedekt door:** 
- ⚠️ US-043-D spreekt over timeouts.yaml (incorrect)
**Status:** User story bestaat maar moet aangepast worden
**Actie:** Update US-043-D om rate_limit_config.py te gebruiken

### 3. Orchestrator Async Voorbeelden
**Review punt:** Orchestrator moet genereer_alle_voorbeelden_async gebruiken
**Ontbreekt:** Geen specifieke user story
**Voorstel:** Maak US-052: Orchestrator Async Voorbeelden Migration

### 4. CI-Gates Implementation
**Review punt:** Blokkeer legacy patterns automatisch
**Ontbreekt:** Geen user story voor CI-gates
**Voorstel:** Maak US-053: Implement CI Gates tegen Legacy Patterns

## 📋 Nieuwe User Stories Nodig

### US-051: Fix CFR-BUG-014 Synoniemen/Antoniemen Generatie
**Epic:** EPIC-010
**Prioriteit:** KRITIEK
**Sprint:** 37
**Story Points:** 5

**Acceptance Criteria:**
- [ ] Prompts bevatten definitie + context
- [ ] Max 1 retry bij te weinig items
- [ ] Accepteer <N op laatste poging (geen infinite loop)
- [ ] Parser ondersteunt komma-gescheiden fallback
- [ ] UI toont synoniemen/antoniemen zonder bullets
- [ ] Consistent 3-5 items gegenereerd

### US-052: Orchestrator Async Voorbeelden Migration
**Epic:** EPIC-010
**Prioriteit:** HOOG
**Sprint:** 37
**Story Points:** 3

**Acceptance Criteria:**
- [ ] Orchestrator V2 gebruikt genereer_alle_voorbeelden_async
- [ ] Geen _run_async_safe in orchestrator
- [ ] Geen asyncio.run in services
- [ ] Tests aangepast voor async flow

### US-053: Implement CI Gates tegen Legacy Patterns
**Epic:** EPIC-010
**Prioriteit:** MEDIUM
**Sprint:** 37
**Story Points:** 2

**Acceptance Criteria:**
- [ ] GitHub Actions workflow voor pattern checking
- [ ] Blokkeer generation_result imports
- [ ] Blokkeer overall_score references
- [ ] Blokkeer domein field usage
- [ ] Blokkeer asyncio.run in services
- [ ] Fail CI bij violations

## 📝 Aan te Passen User Stories

### US-043-D: Implementeer Robuuste Timeouts
**Wijziging nodig:**
- Gebruik `get_endpoint_timeout` uit `rate_limit_config.py`
- GEEN nieuwe timeouts.yaml file
- Update async_bridge om rate_limit_config te gebruiken

## 🎯 Samenvatting

**Goed gedekt:**
- UI migratie strategie ✅
- Legacy route removal ✅
- E2E testing ✅

**Ontbreekt/Aanpassen:**
- CFR-BUG-014 implementatie story ❌
- Timeout config approach (US-043-D aanpassen) ⚠️
- Orchestrator async migration ❌
- CI-gates implementation ❌

**Actie vereist:**
1. Maak 3 nieuwe user stories (US-051, US-052, US-053)
2. Update US-043-D voor rate_limit_config gebruik
3. Update EPIC-010 met nieuwe stories in Sprint 37 planning