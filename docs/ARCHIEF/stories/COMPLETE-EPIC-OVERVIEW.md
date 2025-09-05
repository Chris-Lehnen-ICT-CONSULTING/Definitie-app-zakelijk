---
canonical: true
status: active
owner: development
last_verified: 2025-09-04
document_type: epic-overview
priority: reference
---

# 📊 COMPLEET EPIC OVERZICHT - DefinitieAgent

Dit document geeft een volledig overzicht van alle 9 epics in het DefinitieAgent project, inclusief wat er al geïmplementeerd is en wat nog moet gebeuren.

---

## 🎯 Epic Status Dashboard

| Epic | Naam | Status | Completion | UAT Priority |
|------|------|--------|------------|--------------|
| **Epic 1** | Basis Definitie Generatie | ✅ | 90% | Done |
| **Epic 2** | Kwaliteitstoetsing | ✅ | 85% | Done |
| **Epic 3** | Content Verrijking / Web Lookup | 🔄 | 30% | **HIGH** |
| **Epic 4** | User Interface | ❌ | 30% | Medium |
| **Epic 5** | Export & Import | ❌ | 10% | Low |
| **Epic 6** | Security & Auth | 🚨 | 0% | **CRITICAL** |
| **Epic 7** | Performance & Scaling | 🔄 | 20% | **HIGH** |
| **Epic 8** | Web Lookup Module | 🔄 | 10% | Merged → Epic 3 |
| **Epic 9** | Advanced Features | ❌ | 5% | Post-UAT |

---

## Epic 1: Basis Definitie Generatie ✅ (90% Compleet)

### Wat zit erin:
De **kern functionaliteit** van het systeem - het genereren van definities met AI.

### Wat is klaar:
- ✅ **DEF-001**: Begrip invoeren (3-100 chars, validatie)
- ✅ **DEF-002**: Context selecteren (organisatorisch, juridisch, wettelijk)
- ✅ **DEF-003**: AI-generatie met GPT-4 (<15 sec response)
- ✅ **DEF-004**: Kwaliteitsscore weergave (0-100, kleurcodering)

### Wat ontbreekt:
- 🔄 **DEF-005**: Duplicate check (backend klaar, UI ontbreekt)

**Impact**: Dit is de basis waarop alles rust. 90% werkend betekent dat de core app functioneert.

---

## Epic 2: Kwaliteitstoetsing ✅ (85% Compleet)

### Wat zit erin:
Het **validatie systeem** met 46 toetsregels die elke definitie checken.

### Wat is klaar:
- ✅ **KWA-001**: Gedetailleerde validatie per regel
- ✅ **KWA-002**: AI-powered suggesties voor verbetering
- ✅ **KWA-003**: Iteratieve verbetering (max 3 iteraties)
- ✅ 45 van 46 toetsregels werkend

### Wat ontbreekt:
- ❌ **KWA-004**: Custom toetsregels UI
- ❌ 1 toetsregel nog niet geïmplementeerd

**Impact**: Validatie werkt goed, maar individuele prompt-instructies per regel ontbreken (zie jouw requirement).

---

## Epic 3: Content Verrijking / Web Lookup 🔄 (30% Compleet)

### Wat zit erin:
**Externe bronnen** raadplegen en content **verrijken** met synoniemen, voorbeelden, etc.

### Wat is klaar:
- ✅ **ENR-001**: Synoniemen (5 items)
- ✅ **ENR-002**: Antoniemen (5 items)
- ✅ **Story 3.1**: Metadata sources visibility (September 2025)

### Wat ontbreekt:
- 🔄 **ENR-003**: Voorbeeldzinnen (backend klaar, UI niet)
- ❌ **ENR-004**: Praktijkvoorbeelden
- ❌ **ENR-005**: Tegenvoorbeelden
- ❌ **ENR-006**: Toelichting
- 🔴 **WEB-3.2**: Context flow fix (3 velden) - JOUW ISSUE #1
- 🔴 **WEB-3.3**: Prompt uit metadata - JOUW ISSUE #2

**Impact**: Dit is waar jouw "metadata eerst, prompt daarna" thuishoort!

---

## Epic 4: User Interface ❌ (30% Compleet)

### Wat zit erin:
Alle **UI tabs** en **gebruikersinteractie** elementen.

### Wat is klaar:
- ✅ **UI-001**: Definitie generator tab (hoofdtab)
- ✅ **UI-002**: History tab (basis)
- ✅ **UI-003**: Export tab (alleen TXT)

### Wat ontbreekt (7 tabs!):
- ❌ **UI-004**: Web lookup tab (leeg)
- ❌ **UI-005**: Expert review tab
- ❌ **UI-006**: Prompt viewer tab
- ❌ **UI-007**: Monitoring tab
- ❌ **UI-008**: Management tab
- ❌ **UI-009**: Orchestration tab
- 🔄 **UI-010**: Quality control tab (deels)

### UI Elementen ontbreken:
- ❌ **UI-011**: Datum voorstel veld
- ❌ **UI-012**: Voorgesteld door veld
- ❌ **UI-013**: Ketenpartners selectie (ZM, DJI, KMAR, etc.)
- 🔄 **UI-014**: Ontologische score (backend klaar)
- ❌ **UI-015**: Voorkeursterm selectie

**Impact**: 70% van de UI functionaliteit ontbreekt. Veel tabs zijn leeg shells.

---

## Epic 5: Export & Import ❌ (10% Compleet)

### Wat zit erin:
Alle **data export/import** functionaliteit voor verschillende formaten.

### Wat is klaar:
- ✅ **EXP-001**: TXT export

### Wat ontbreekt:
- ❌ **EXP-002**: Word export (.docx)
- ❌ **EXP-003**: PDF export
- ❌ **EXP-004**: Excel export
- 🔄 **EXP-005**: JSON export (backend ready)
- ❌ **IMP-001**: CSV import
- 🔄 **IMP-002**: Document upload (DocumentProcessor bestaat)

**Impact**: Alleen basis TXT export werkt. Geen bulk operaties mogelijk.

---

## Epic 6: Security & Auth 🚨 (0% Compleet - KRITIEK!)

### Wat zit erin:
Alle **security features** - authenticatie, autorisatie, encryptie.

### Wat is klaar:
- ❌ NIETS!

### Wat ontbreekt ALLES:
- ❌ **SEC-001**: Gebruikers authenticatie (login/logout)
- ❌ **SEC-002**: Role-based access control (RBAC)
- ❌ **SEC-003**: API key management
- ❌ **SEC-004**: Data encryptie
- ❌ **SEC-005**: Audit logging

**Impact**: De app heeft GEEN SECURITY! Iedereen kan alles. SQLite is plain text.

**Note**: Er is wel een `security/security_middleware.py` (100% compleet) maar die wordt niet gebruikt!

---

## Epic 7: Performance & Scaling 🔄 (20% Compleet)

### Wat zit erin:
Alle **performance optimalisaties** en **schaalbaarheid**.

### Wat is klaar:
- ✅ **PER-005**: Database optimization (WAL mode, indexes)
- ✅ Story 3.1: Basis caching

### Wat ontbreekt:
- ❌ **PER-001**: <5 sec response (nu 8-12 sec)
- 🔄 **PER-002**: Caching (alleen in-memory, geen Redis)
- ❌ **PER-003**: Horizontal scaling
- 🔄 **PER-004**: Async processing (Celery planned)
- 🔴 **PER-006**: Prompt token reductie - JOUW REQUIREMENT
- 🔴 **PER-007**: Context flow fix - JOUW ISSUE #1
- 🔴 **PER-008**: Toetsregel mapping - JOUW ISSUE #2
- 🔴 **PER-009**: Ontologie als instructie - JOUW ISSUE #3

**Impact**: Dit is waar jouw performance issues thuishoren!

---

## Epic 8: Web Lookup Module 🔄 (10% Compleet)

### Wat zit erin:
Legacy web lookup functionaliteit (wordt **gemerged met Epic 3**).

### Status:
- 🔄 **WEB-001**: 5 broken implementations gevonden
- ❌ **WEB-002**: Bron validatie
- ❌ **WEB-003**: Automatische verrijking
- ❌ **WEB-004**: Bron attributie

**Impact**: Deze epic wordt opgegeven en gemerged met Epic 3.

---

## Epic 9: Advanced Features ❌ (5% Compleet)

### Wat zit erin:
**Enterprise features** voor na de UAT - collaboratie, workflows, API's.

### Wat is klaar:
- 🔄 **ADV-004**: API access (FastAPI migration started)

### Wat ontbreekt:
- ❌ **ADV-001**: Bulk operations
- ❌ **ADV-002**: Version control
- ❌ **ADV-003**: Collaboration (comments, mentions)
- ❌ **ADV-005**: Custom workflows

**Impact**: Dit is voor later, niet UAT-relevant.

---

## 🎯 JOUW SPECIFIEKE ISSUES - Waar Ze Thuishoren

### Issue 1: Context Flow (3 velden)
**Epic**: 3 of 7
**Story**: WEB-3.2 of PER-007
**Probleem**: Alleen organisatorische_context komt mee, juridische_context en wettelijke_basis niet

### Issue 2: Toetsregel → Prompt Mapping
**Epic**: 7 (Performance)
**Story**: PER-008
**Probleem**: Geen individuele prompt instructies per toetsregel (45 regels)

### Issue 3: Ontologie als Instructie
**Epic**: 7 (Performance)
**Story**: PER-009
**Probleem**: Ontologie wordt als vraag gesteld i.p.v. instructie

### Issue 4: Metadata Eerst, Prompt Daarna
**Epic**: 3 (Content Verrijking)
**Story**: WEB-3.3
**Probleem**: Prompt gebruikt context["web_lookup"] i.p.v. metadata["sources"]

---

## 📈 SAMENVATTEND

### Wat werkt goed:
1. **Basis generatie** (Epic 1) - 90% klaar
2. **Validatie** (Epic 2) - 85% klaar
3. **Hoofdtab UI** - Functioneel

### Grootste problemen:
1. **Security** (Epic 6) - 0% = KRITIEK RISICO
2. **UI Tabs** (Epic 4) - 70% ontbreekt
3. **Performance** (Epic 7) - 8-12 sec response tijd
4. **Context flow** - Jouw issue #1
5. **Export/Import** (Epic 5) - Alleen TXT werkt

### UAT Prioriteiten (20 september):
1. 🔥 **Epic 3**: Metadata eerst flow (jouw requirements)
2. 🔥 **Epic 7**: Performance fixes (context, prompt optimalisatie)
3. ⚠️ **Epic 6**: Minimale security (authenticatie)
4. 📋 **Epic 4**: Kritieke UI tabs

### Ongebruikte Assets (65% code niet actief!):
- Security middleware (100% compleet, niet gebruikt)
- A/B testing framework (compleet, niet gebruikt)
- Config manager (compleet, niet gebruikt)
- 46 duplicate validators (kunnen geconsolideerd)
- Microservice componenten (klaar voor activatie)

---

**Conclusie**: Het project heeft een sterke basis (Epic 1-2) maar mist kritieke componenten voor productie. De focus moet liggen op jouw "metadata eerst" requirements (Epic 3), performance (Epic 7) en minimale security (Epic 6) voor UAT.
