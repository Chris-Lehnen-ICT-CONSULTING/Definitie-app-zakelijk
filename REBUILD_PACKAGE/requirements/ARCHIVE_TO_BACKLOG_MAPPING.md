---
owner: development-team
applies_to: definitie-app@current
last_verified: 2025-10-02
generated: 2025-09-12 09:40:32
source: docs/backlog/requirements/REQUIREMENTS_AND_FEATURES_COMPLETE.md
method: refined mapping (domain→EPIC + fuzzy titelmatch + force-cover)
---
# Archief → Backlog Mapping (Verfijnd)

## Epics
| Archief Epic | Status | Backlog Epic/Opmerking |
|---|---|---|
| EPIC-001 — Basis Definitie Generatie ✅ (90% Compleet) | AANWEZIG | docs/backlog/EPIC-001 |
| EPIC-002 — Kwaliteitstoetsing ✅ (85% Compleet) | AANWEZIG | docs/backlog/EPIC-002 |
| EPIC-003 — Content Verrijking 🔄 (30% Compleet) | AANWEZIG | docs/backlog/EPIC-003 |
| EPIC-004 — User Interface ❌ (30% Compleet) | AANWEZIG | docs/backlog/EPIC-004 |
| EPIC-005 — Export & Import ❌ (10% Compleet) | AANWEZIG | docs/backlog/EPIC-005 |
| EPIC-006 — Beveiliging & Auth ❌ (0% Compleet) | AANWEZIG | docs/backlog/EPIC-006 |
| EPIC-007 — Prestaties & Scaling 🔄 (20% Compleet) | AANWEZIG | docs/backlog/EPIC-007 |
| EPIC-008 — Web Lookup Module 🔄 (10% Compleet) | HERNOEMD -> EPIC-003 | docs/backlog/EPIC-003 |
| EPIC-009 — Advanced Features ❌ (5% Compleet) | AANWEZIG | docs/backlog/EPIC-009 |

## Items (Features/Stories)
| ID | Story | Archiefstatus | EPIC | Gedekt | Beste US |
|---|---|---|---|---|---|
| DEF-001 | Als gebruiker wil ik een begrip kunnen invoeren | ✅ Compleet | EPIC-001 | Nee | - |
| DEF-002 | Als gebruiker wil ik context kunnen selecteren | ✅ Compleet | EPIC-001 | Nee | docs/backlog/EPIC-001/US-001/US-001.md |
| DEF-003 | Als gebruiker wil ik een AI-gegenereerde definitie krijgen | ✅ Compleet | EPIC-001 | Ja | docs/backlog/EPIC-001/US-001/US-001.md |
| DEF-004 | Als gebruiker wil ik de kwaliteitsscore zien | ✅ Compleet | EPIC-001 | Nee | - |
| DEF-005 | Als gebruiker wil ik duplicate check | 🔄 In Progress | EPIC-001 | Nee | docs/backlog/EPIC-001/US-002/US-002.md |
| KWA-001 | Als gebruiker wil ik gedetailleerde validatie zien | ✅ Compleet | EPIC-002 | Ja | docs/backlog/EPIC-002/US-006/US-006.md |
| KWA-002 | Als gebruiker wil ik suggesties voor verbetering | ✅ Compleet | EPIC-002 | Nee | - |
| KWA-003 | Als gebruiker wil ik iteratieve verbetering | ✅ Compleet | EPIC-002 | Nee | - |
| KWA-004 | Als gebruiker wil ik custom toetsregels | ❌ Niet Gestart | EPIC-002 | Nee | docs/backlog/EPIC-002/US-007/US-007.md |
| ENR-001 | Als gebruiker wil ik synoniemen zien | ✅ Compleet | EPIC-003 | Nee | docs/backlog/EPIC-003/US-079/US-079.md |
| ENR-002 | Als gebruiker wil ik antoniemen zien | ✅ Compleet | EPIC-003 | Nee | docs/backlog/EPIC-003/US-079/US-079.md |
| ENR-003 | Als gebruiker wil ik voorbeeldzinnen | 🔄 In Progress | EPIC-003 | Ja | - |
| ENR-004 | Als gebruiker wil ik praktijkvoorbeelden | ❌ Niet Gestart | EPIC-003 | Ja | - |
| ENR-005 | Als gebruiker wil ik tegenvoorbeelden | ❌ Niet Gestart | EPIC-003 | Ja | - |
| ENR-006 | Als gebruiker wil ik toelichting | ❌ Niet Gestart | EPIC-003 | Ja | - |
| UI-001 | Als gebruiker wil ik definitie generator tab | ✅ Compleet | EPIC-004 | Ja | docs/backlog/EPIC-004/US-025/US-025.md |
| UI-002 | Als gebruiker wil ik history tab | ✅ Compleet | EPIC-004 | Nee | docs/backlog/EPIC-004/US-021/US-021.md |
| UI-003 | Als gebruiker wil ik export tab | ✅ Compleet | EPIC-004 | Nee | docs/backlog/EPIC-004/US-136/US-136.md |
| UI-004 | Als gebruiker wil ik web lookup tab | ❌ Niet Gestart | EPIC-004 | Nee | - |
| UI-005 | Als gebruiker wil ik expert review tab | ❌ Niet Gestart | EPIC-004 | Ja | docs/backlog/EPIC-004/US-067/US-067.md |
| UI-006 | Als gebruiker wil ik prompt viewer tab | ❌ Niet Gestart | EPIC-004 | Nee | - |
| UI-007 | Als gebruiker wil ik monitoring tab | ❌ Niet Gestart | EPIC-004 | Nee | docs/backlog/EPIC-004/US-022/US-022.md |
| UI-008 | Als gebruiker wil ik management tab | ❌ Niet Gestart | EPIC-004 | Nee | docs/backlog/EPIC-004/US-021/US-021.md |
| UI-009 | Als gebruiker wil ik orchestration tab | ❌ Niet Gestart | EPIC-004 | Nee | - |
| UI-010 | Als gebruiker wil ik quality control tab | 🔄 In Progress | EPIC-004 | Nee | docs/backlog/EPIC-004/US-136/US-136.md |
| UI-011 | Als gebruiker wil ik datum voorstel veld | ❌ Niet Gestart | EPIC-004 | Nee | docs/backlog/EPIC-004/US-068/US-068.md |
| UI-012 | Als gebruiker wil ik voorgesteld door veld | ❌ Niet Gestart | EPIC-004 | Ja | - |
| UI-013 | Als gebruiker wil ik ketenpartners selectie | ❌ Niet Gestart | EPIC-004 | Nee | - |
| UI-014 | Als gebruiker wil ik ontologische score zien | 🔄 In Progress | EPIC-004 | Nee | docs/backlog/EPIC-004/US-136/US-136.md |
| UI-015 | Als gebruiker wil ik voorkeursterm selectie | ❌ Niet Gestart | EPIC-004 | Ja | - |
| EXP-001 | Als gebruiker wil ik TXT export | ✅ Compleet | EPIC-005 | Nee | docs/backlog/EPIC-005/US-137/US-137.md |
| EXP-002 | Als gebruiker wil ik Word export | ❌ Niet Gestart | EPIC-005 | Ja | docs/backlog/EPIC-005/US-137/US-137.md |
| EXP-003 | Als gebruiker wil ik PDF export | ❌ Niet Gestart | EPIC-005 | Nee | docs/backlog/EPIC-005/US-137/US-137.md |
| EXP-004 | Als gebruiker wil ik Excel export | ❌ Niet Gestart | EPIC-005 | Ja | docs/backlog/EPIC-005/US-062/US-062.md |
| EXP-005 | Als gebruiker wil ik JSON export | 🔄 In Progress | EPIC-005 | Ja | docs/backlog/EPIC-005/US-137/US-137.md |
| IMP-001 | Als gebruiker wil ik CSV import | ❌ Niet Gestart | EPIC-005 | Nee | docs/backlog/EPIC-005/US-137/US-137.md |
| IMP-002 | Als gebruiker wil ik document upload | 🔄 In Progress | EPIC-005 | Nee | docs/backlog/EPIC-005/US-137/US-137.md |
| SEC-001 | Als admin wil ik gebruikers authenticatie | ❌ Niet Gestart | EPIC-006 | Nee | docs/backlog/EPIC-006/US-141/US-141.md |
| SEC-002 | Als admin wil ik role-based access | ❌ Niet Gestart | EPIC-006 | Nee | docs/backlog/EPIC-006/US-140/US-140.md |
| SEC-003 | Als admin wil ik API key management | ❌ Niet Gestart | EPIC-006 | Nee | docs/backlog/EPIC-006/US-140/US-140.md |
| SEC-004 | Als gebruiker wil ik data encryptie | ❌ Niet Gestart | EPIC-006 | Nee | - |
| SEC-005 | Als admin wil ik audit logging | ❌ Niet Gestart | EPIC-006 | Ja | docs/backlog/EPIC-006/US-027/US-027.md |
| PER-001 | Als gebruiker wil ik <5 sec response | ❌ Niet Gestart | EPIC-007 | Nee | docs/backlog/EPIC-007/US-142/US-142.md |
| PER-002 | Als gebruiker wil ik caching | 🔄 In Progress | EPIC-007 | Nee | docs/backlog/EPIC-007/US-142/US-142.md |
| PER-003 | Als admin wil ik horizontal scaling | ❌ Niet Gestart | EPIC-007 | Nee | docs/backlog/EPIC-007/US-063/US-063.md |
| PER-004 | Als gebruiker wil ik async processing | 🔄 In Progress | EPIC-007 | Ja | docs/backlog/EPIC-007/US-063/US-063.md |
| PER-005 | Als admin wil ik database optimization | ✅ Compleet | EPIC-007 | Ja | docs/backlog/EPIC-007/US-145/US-145.md |
| WEB-001 | Als gebruiker wil ik externe bronnen zoeken | 🔄 In Progress | EPIC-003 | Ja | docs/backlog/EPIC-003/US-135/US-135.md |
| WEB-002 | Als gebruiker wil ik bron validatie | ❌ Niet Gestart | EPIC-003 | Ja | docs/backlog/EPIC-003/US-135/US-135.md |
| WEB-003 | Als gebruiker wil ik automatische verrijking | ❌ Niet Gestart | EPIC-003 | Nee | docs/backlog/EPIC-003/US-135/US-135.md |
| WEB-004 | Als gebruiker wil ik bron attributie | ❌ Niet Gestart | EPIC-003 | Nee | docs/backlog/EPIC-003/US-135/US-135.md |
| ADV-001 | Als gebruiker wil ik bulk operations | ❌ Niet Gestart | EPIC-009 | Nee | docs/backlog/EPIC-009/US-060/US-060.md |
| ADV-002 | Als gebruiker wil ik version control | ❌ Niet Gestart | EPIC-009 | Nee | - |
| ADV-003 | Als gebruiker wil ik collaboration | ❌ Niet Gestart | EPIC-009 | Nee | - |
| ADV-004 | Als gebruiker wil ik API access | 🔄 In Progress | EPIC-009 | Nee | - |
| ADV-005 | Als gebruiker wil ik custom workflows | ❌ Niet Gestart | EPIC-009 | Nee | - |
