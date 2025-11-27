# Linear Backlog Cleanup Plan

**Datum:** 27 november 2025
**Doel:** Backlog up-to-date en lean krijgen
**Totaal issues geanalyseerd:** ~95 issues (niet-Done)

---

## Executive Summary

| Categorie | Aantal | Actie |
|-----------|--------|-------|
| Te verwijderen (WRONG APPROACH/Duplicate) | 4 | Cancel |
| Stale "In Progress" (>4 weken) | 6 | Review & update |
| Mogelijk verouderd (>3 weken oud) | 15+ | Review relevantie |
| Overlappende issues (consolideren) | 12+ | Merge/link |
| Recent & relevant | ~60 | Behouden |

---

## 1. DIRECT TE CANCELEN (4 issues)

### Expliciet gemarkeerd als verkeerde aanpak:

| Issue | Titel | Reden |
|-------|-------|-------|
| **DEF-131** | [WRONG APPROACH] Remove validation rules | Issue zelf zegt: "CANCEL immediately" |
| **DEF-134** | [WRONG APPROACH] Compress validation rules | Issue zelf zegt: "CANCEL immediately" |

### Gemarkeerd als duplicate in andere issues:

| Issue | Titel | Reden |
|-------|-------|-------|
| **DEF-186** | (niet gevonden in results) | Genoemd als "Duplicate" in DEF-188 |
| **DEF-149** | (niet gevonden in results) | Genoemd als "Canceled" in DEF-188 |

**Actie:** Cancel deze 4 issues met status "Canceled" of "Duplicate"

---

## 2. STALE "IN PROGRESS" ISSUES (6 issues)

Issues die al >4 weken "In Progress" staan zonder activiteit:

| Issue | Titel | In Progress sinds | Aanbeveling |
|-------|-------|-------------------|-------------|
| **DEF-38** | Kritieke Issues in Ontologische Promptinjecties | 17 okt | Review: nog actief bezig? Anders → Backlog |
| **DEF-40** | Optimaliseer category-specific prompt injecties | 17 okt | Review: nog actief bezig? Anders → Backlog |
| **DEF-154** | Remove conflicting word_type_advice | 13 nov | Recent, waarschijnlijk OK |
| **DEF-123** | Implement context-aware module loading | 7 nov | Review progress |
| **DEF-135** | Transform validation rules to instructions | 7 nov | Review progress |
| **DEF-106** | Create PromptValidator (Automated QA) | 4 nov | Review progress |

**Actie:** Review of deze daadwerkelijk actief zijn. Zo niet → terug naar Backlog of Done als klaar.

---

## 3. OVERLAPPENDE/DUPLICATE ISSUES (consolideren)

### 3.1 Code Cleanup Cluster (DEF-189 familie)
DEF-189 is parent met 4 sub-issues die al gelinkt zijn:

| Parent | Sub-issues |
|--------|------------|
| DEF-189 | DEF-194, DEF-195, DEF-196, DEF-197 |

**Status:** Goed gestructureerd, behouden als is.

### 3.2 Prompt Contradictions Cluster
Meerdere issues over dezelfde prompt contradictions:

| Issue | Focus |
|-------|-------|
| DEF-146 | ESS-02 'is' usage + article contradiction (P0) |
| DEF-147 | Exempt ontological markers from ARAI-02 |
| DEF-148 | Clarify relative clause usage |
| DEF-150 | Categorize 42 forbidden patterns |

**Aanbeveling:** Consolideer naar één Epic of link als sub-issues.

### 3.3 Data Loss Bugs Cluster
Overlappende bugs over voorbeelden/definities niet opslaan:

| Issue | Focus | Status |
|-------|-------|--------|
| DEF-52 | Voorbeelden niet opgeslagen na generatie | Backlog |
| DEF-53 | repository.save() method missing | Backlog |
| DEF-56 | Voorbeelden niet opgeslagen in Bewerk tab | Backlog |

**Aanbeveling:** Check of dit dezelfde root cause is. Mogelijk 1 issue met 2 duplicates.

### 3.4 Performance Optimization Cluster
Veel overlappende performance issues:

| Issue | Focus |
|-------|-------|
| DEF-60 | Lazy loading 5 optional services |
| DEF-61 | Merge PromptOrchestrator layers |
| DEF-62 | Replace Context managers with dataclass |
| DEF-65 | ServiceContainer slimming |
| DEF-90/DEF-94 | ValidationOrchestrator lazy loading |
| DEF-92 | Performance regression analysis |

**Aanbeveling:** Maak één Performance Epic en link deze als sub-issues.

### 3.5 God Object Refactoring Cluster

| Issue | Target |
|-------|--------|
| DEF-70 | ServiceContainer (818 LOC) |
| DEF-71 | DefinitieRepository (2,101 LOC) |
| DEF-113 | Extreme complexity hotspot (CC 108) |
| DEF-114 | UI God Objects (5,433 LOC) |
| DEF-192 | God Class Refactoring |

**Aanbeveling:** DEF-192 lijkt de nieuwe umbrella issue. Cancel of link de oudere specifieke issues.

---

## 4. MOGELIJK VEROUDERDE ISSUES (review nodig)

Issues ouder dan 3 weken die mogelijk niet meer relevant zijn:

| Issue | Titel | Aangemaakt | Review vraag |
|-------|-------|------------|--------------|
| DEF-39 | Blokkeer definitie generatie als categorie ontbreekt | 17 okt | Al geïmplementeerd? |
| DEF-45 | Voorbeelden moeten specifiek aansluiten | 27 okt | Nog relevant? |
| DEF-46 | Cleanup requirements.txt | 28 okt | Al gedaan? |
| DEF-47-51 | Variabele detectie cluster | 28 okt | Nog prioriteit? |
| DEF-54 | Eliminate Dual Repository | 29 okt | Nog relevant? |
| DEF-57 | Add UI Integration Tests | 30 okt | Nog prioriteit? |
| DEF-58 | Fix 24 Streamlit Anti-patterns | 30 okt | Al gefixed? |
| DEF-59 | Gitleaks False Positives | 30 okt | Al gefixed? |
| DEF-63 | Consolidate 3 Definition services | 30 okt | Nog relevant? |
| DEF-64 | Flatten Manager pattern | 30 okt | Nog relevant? |
| DEF-68 | Silent Context Validation Exception | 30 okt | CRITICAL - nog open? |
| DEF-72 | Directory Proliferation | 30 okt | Nog relevant? |
| DEF-80 | Fix 1951 pre-commit linting issues | 30 okt | Gedaan in DEF-186? |

---

## 5. CRITICAL/P0 ISSUES - PRIORITEIT CHECK

Deze issues zijn gemarkeerd als Critical maar staan nog open:

| Issue | Titel | Status | Aanbeveling |
|-------|-------|--------|-------------|
| DEF-52 | Voorbeelden niet opgeslagen (P0) | Backlog | **Escalate of verify fixed** |
| DEF-53 | repository.save() missing (P0) | Backlog | **Escalate of verify fixed** |
| DEF-56 | Voorbeelden in Bewerk tab (P0) | Backlog | **Escalate of verify fixed** |
| DEF-68 | Silent Exception Swallowing (CRITICAL) | Backlog | **Escalate of verify fixed** |
| DEF-112 | Streamlit Anti-pattern Data Loss | Backlog | **Review urgency** |

**Actie:** Verifieer of deze P0 issues nog bestaan. Als ja → direct oppakken. Als nee → Done.

---

## 6. PROJECT-GEBONDEN ISSUES

### Integrated Prompt Improvement Strategy Project
11 issues (DEF-157 t/m DEF-168) horen bij dit project:

| Phase | Issues |
|-------|--------|
| Phase 1 | DEF-157, DEF-158, DEF-159, DEF-160, DEF-161, DEF-162 |
| Phase 2 | DEF-163, DEF-164, DEF-165, DEF-166 |
| Phase 3 | DEF-167 |
| Phase 4 | DEF-168 |

**Aanbeveling:** Behouden als coherent project. Review of project nog actief is.

---

## 7. AANBEVOLEN ACTIES

### Onmiddellijk (vandaag):
1. **Cancel DEF-131 en DEF-134** (expliciet wrong approach)
2. **Verify DEF-186 en DEF-149** status (mogelijk al canceled)
3. **Review 6 stale "In Progress"** issues - update status

### Deze week:
4. **Verify P0/Critical bugs** (DEF-52, DEF-53, DEF-56, DEF-68) - zijn deze gefixed?
5. **Consolideer prompt contradiction cluster** (DEF-146-150) naar Epic
6. **Consolideer data loss bugs** (DEF-52, DEF-53, DEF-56) - check root cause

### Volgende sprint:
7. **Create Performance Epic** en link DEF-60, 61, 62, 65, 90, 92, 94
8. **Review God Object cluster** - DEF-192 vs DEF-70, 71, 113, 114
9. **Review 15+ mogelijk verouderde issues** (>3 weken oud)

---

## 8. CLEANUP CHECKLIST

- [ ] DEF-131 → Canceled
- [ ] DEF-134 → Canceled
- [ ] DEF-186 → Verify status (Duplicate?)
- [ ] DEF-149 → Verify status (Canceled?)
- [ ] DEF-38 → Review In Progress status
- [ ] DEF-40 → Review In Progress status
- [ ] DEF-52, 53, 56 → Verify if fixed or escalate
- [ ] DEF-68 → Verify if fixed or escalate
- [ ] Prompt contradiction cluster → Create Epic
- [ ] Performance cluster → Create Epic
- [ ] God Object cluster → Consolidate
- [ ] 15+ oude issues → Individual review

---

## 9. VERWACHTE RESULTAAT

**Voor cleanup:**
- ~95 open issues
- 6 stale "In Progress"
- Onduidelijke prioriteiten
- Overlappende issues

**Na cleanup:**
- ~70-75 open issues (-20-25%)
- 0 stale "In Progress"
- Duidelijke Epics voor grote clusters
- Gevalideerde P0 issues
