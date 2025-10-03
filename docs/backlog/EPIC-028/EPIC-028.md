# EPIC-028: Feature Cleanup & UI Simplification

**Epic Owner:** Product Owner
**Created:** 2025-10-03
**Status:** 🟢 READY
**Priority:** HIGH
**Effort:** 13 story points

---

## 📋 Epic Doel

Verwijder afleidende en redundante features uit DefinitieAgent om focus te leggen op core functionaliteit: betere definities genereren en betrouwbaar toetsen.

---

## 🎯 Business Value

**Probleem:**
- Applicatie heeft 8 tabs → verwarrend voor gebruikers
- 2,030 LOC bloat code → moeilijk te onderhouden
- Features overlappen → onduidelijk welke te gebruiken
- Developer velocity laag → veel complexiteit

**Oplossing:**
- Reduceer naar 4 core tabs
- Verwijder 5 redundante features
- Verhoog focus op waarde-creërende functionaliteit

**Impact:**
- 50% minder UI complexity
- 37% LOC reductie in UI layer
- Snellere development velocity
- Betere user experience

---

## 🔍 Scope

### ✂️ Te Verwijderen Features

1. **Orchestration Tab** — Deprecated, V2 orchestrator doet dit
2. **Duplicate Context Selectors** — 3 implementaties, keep 1
3. **Monitoring Tab** — Developer tool, niet voor eindgebruikers
4. **Web Lookup Tab** — Redundant, al geïntegreerd
5. **Category Regeneration Service** — Redundant workflow

### ✅ Te Behouden Features

- Definitie Generatie Tab
- Edit Tab
- Expert Review Tab
- Import/Export/Beheer Tab
- Validation Rules System
- Ontological Analyzer (CORE - blijft compleet)
- Document Upload & Hybrid Context
- Voorbeelden Generation
- UFO Categories

---

## 📊 User Stories

| ID | Story | Priority | Effort |
|----|-------|----------|--------|
| US-441 | Remove Orchestration Tab | HIGH | 2 SP |
| US-442 | Remove Duplicate Context Selectors | HIGH | 2 SP |
| US-443 | Remove Monitoring Tab | HIGH | 2 SP |
| US-444 | Remove Web Lookup Tab | MEDIUM | 2 SP |
| US-445 | Remove Regeneration Service | HIGH | 3 SP |
| US-446 | Integration Testing Post-Removal | HIGH | 2 SP |

**Total:** 13 story points

---

## ✅ Acceptance Criteria (Epic Level)

- [ ] Alle 5 features volledig verwijderd
- [ ] UI heeft nog 4 tabs (Generator, Edit, Expert Review, Import/Export)
- [ ] Alle bestaande tests blijven groen
- [ ] Geen broken imports of references
- [ ] Feature flags opgeruimd
- [ ] ~2,030 LOC verwijderd
- [ ] Documentatie bijgewerkt

---

## 🚧 Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Broken dependencies | MEDIUM | HIGH | Pre-scan imports, run tests after elk removal |
| Lost functionality | LOW | HIGH | User verification: alle kept features werken |
| Test failures | MEDIUM | MEDIUM | Fix incrementeel, één feature tegelijk |

---

## 📅 Timeline

**Duration:** 1 sprint (2-3 dagen)

**Phase 1:** User Stories (Dag 1)
**Phase 2:** Execution (Dag 1-2)
**Phase 3:** Testing & Verification (Dag 2-3)

---

## 📎 Related Epics

- **EPIC-027:** Multi-LLM Support (volgt na cleanup)
- **EPIC-025:** Process Enforcement (parallel track)

---

## 📝 Notes

Deze cleanup maakt de codebase klaar voor EPIC-027 (Multi-LLM Support). Door complexity te verlagen, kunnen we sneller itereren op core features.
