# Prompt Architectuur & Redundantie Analyse

**Geanalyseerd bestand:** `/Users/chrislehnen/Downloads/_Definitie_Generatie_prompt-7.txt`
**Analyse datum:** 2025-11-07
**Huidige lengte:** 419 regels
**Probleemdiagnose:** Massieve redundantie, conflicterende instructies, onduidelijke structuur

---

## 1. STRUCTUUR ANALYSE

### Hoofdsecties Overzicht

| Sectie | Regels | Doel | Redundantie Score |
|--------|--------|------|-------------------|
| **Introductie** | 1-10 | Basis rol & vereisten | 🟢 Uniek |
| **Output Format** | 11-16 | Technische specs | 🟢 Uniek |
| **Definitie Kwaliteit** | 17-22 | Algemene taalregels | 🟡 Overlapt met ARAI |
| **Grammatica Regels** | 24-61 | Specifieke grammatica | 🟡 Overlapt met VER |
| **Context Info** | 63-69 | Organisatorisch/juridisch | 🟢 Uniek |
| **Betekenislaag (ESS-02)** | 70-109 | Ontologische categorieën | 🔴 **CONFLICTEERT** met 293-335 |
| **Templates** | 110-124 | Voorbeeldstructuren | 🟢 Nuttig |
| **Validatieregels** | 125-292 | 45 gestructureerde regels | 🟢 Core logica |
| **Veelgemaakte Fouten** | 293-335 | Verboden starts | 🔴 **MASSIVE OVERLAP** |
| **Context Verboden** | 336-351 | Context-specifiek | 🟢 Uniek |
| **Kwaliteitsmetrieken** | 353-379 | Technische limieten | 🟢 Uniek |
| **Finale Instructies** | 380-419 | Opdracht + checklist | 🟡 Herhaalt eerdere regels |

### Logische Flow Problemen

**KRITIEKE ISSUE: Broken Narrative Arc**

```
Lijn 73-77:   "Start NOOIT met 'is een' of koppelwerkwoorden!"
              "MOET een zelfstandig naamwoord zijn"

Lijn 87-92:   "PROCES CATEGORIE - KICK-OFF opties:"
              "activiteit waarbij..." ✅
              "handeling die..." ✅
              "proces waarin..." ✅

Lijn 293-335: "❌ Start niet met 'proces waarbij'"
              "❌ Start niet met 'handeling die'"

=> DIRECTE CONTRADICTIE!
```

**Flow Volgorde Issues:**

1. **Ontologische categorie wordt 3x uitgelegd:**
   - Lijn 70-109: Uitgebreide uitleg met voorbeelden
   - Lijn 143: ESS-02 regel verwijzing
   - Lijn 389-390: Finale checklist

2. **"Geen lidwoord" wordt 6x herhaald:**
   - Lijn 13, 134, 294, 320-322, 386

3. **Templates komen TE LAAT:**
   - Templates (110-124) komen NA ontologische uitleg
   - Beter: Eerst templates, dan specifieke regels

---

## 2. REDUNDANTIE MATRIX

### Overlappende Instructies (Gedetailleerd)

#### **"Geen Lidwoord" Herhaling (6x)**

| Locatie | Formulering | Noodzaak |
|---------|-------------|----------|
| Lijn 13 | "Geen punt aan het einde" | ✅ FORMAT |
| Lijn 134 | ARAI-06: "geen lidwoord, geen koppelwerkwoord" | ✅ REGEL |
| Lijn 294 | "❌ Begin niet met lidwoorden" | ❌ DUPLICATE |
| Lijn 320-322 | "❌ Start niet met 'de', 'het', 'een'" | ❌ DUPLICATE |
| Lijn 386 | Checklist: "geen lidwoord/koppelwerkwoord" | ❌ DUPLICATE |

**Optimalisatie:** KEEP alleen lijn 134 (ARAI-06 regel), DELETE rest

#### **"Geen Koppelwerkwoord" Herhaling (5x)**

| Locatie | Formulering | Noodzaak |
|---------|-------------|----------|
| Lijn 78 | "Start NOOIT met 'is een'" | ✅ ESS-02 context |
| Lijn 134 | ARAI-06: "geen koppelwerkwoord" | ✅ REGEL |
| Lijn 295 | "❌ Gebruik geen koppelwerkwoord aan het begin" | ❌ DUPLICATE |
| Lijn 301-318 | Lijst van 18 verboden koppelwerkwoorden | ❌ OVERKILL |
| Lijn 344 | Tabel: "Koppelwerkwoorden aan het begin ✅" | ❌ DUPLICATE |

**Optimalisatie:** KEEP lijn 134 + top 5 voorbeelden, DELETE rest

#### **Ontologische Categorie Conflict (KRITIEK!)**

| Locatie | Instructie | Type |
|---------|-----------|------|
| **Lijn 73-77** | "start met: 'activiteit waarbij', 'handeling die', 'proces waarin'" | ✅ VOORSCHRIFT |
| **Lijn 87-92** | "KICK-OFF opties: 'activiteit waarbij...', 'handeling die...', 'proces waarin...'" | ✅ VOORSCHRIFT |
| **Lijn 323-325** | "❌ Start niet met 'proces waarbij', 'handeling die'" | ❌ **CONTRADICTIE** |

**ROOT CAUSE:**
Lijn 323-325 is bedoeld om **standalone** gebruik te verbieden (bijv. "proces waarbij gegevens worden verzameld" zonder specificatie van TYPE proces).
Maar dit CONFLICTEERT met de KICK-OFF template die juist "activiteit waarbij..." vereist.

**OPLOSSING:**
- DELETE lijn 323-329 volledig
- Vervang door: "Start met specifieke kick-off (activiteit/handeling/proces), niet met generieke containerbegrippen zonder toespitsing"

#### **Enkelvoud Regel (4x)**

| Locatie | Formulering |
|---------|-------------|
| Lijn 26-31 | "🔸 Enkelvoud als standaard" (uitgebreid) |
| Lijn 289 | VER-01: "Term in enkelvoud" |
| Lijn 290 | VER-02: "Definitie in enkelvoud" |
| Lijn 300 | "❌ Gebruik enkelvoud" |

**Optimalisatie:** KEEP lijn 26-31 (duidelijke uitleg), condense VER regels

---

## 3. COMPLEXITEIT ANALYSE

### Lengte Metrics

```
Totaal regels:           419
Effectieve regels:       ~250 (na duplicate removal)
Potentiële reductie:     40% (169 regels)

Sectie Verdeling:
- Validatieregels:       168 regels (40%) ← CORE, KEEP
- Veelgemaakte Fouten:   43 regels (10%)  ← 80% CUT
- Grammatica:            37 regels (9%)   ← MERGE
- Ontologie:             39 regels (9%)   ← SIMPLIFY
- Rest:                  132 regels (32%) ← OPTIMIZE
```

### Complexiteit Score per Sectie

| Sectie | Lines | Redundantie | Essentialiteit | Actie |
|--------|-------|-------------|----------------|-------|
| **Validatieregels (125-292)** | 168 | 🟢 Low | 🔴 HIGH | KEEP 95% |
| **Veelgemaakte Fouten (293-335)** | 43 | 🔴 HIGH | 🟡 MEDIUM | CUT 80% |
| **Ontologie (70-109)** | 39 | 🟡 MEDIUM | 🔴 HIGH | SIMPLIFY |
| **Grammatica (24-61)** | 37 | 🟡 MEDIUM | 🔴 HIGH | MERGE |
| **Templates (110-124)** | 14 | 🟢 Low | 🔴 HIGH | KEEP 100% |
| **Finale Instructies (380-419)** | 39 | 🔴 HIGH | 🟡 MEDIUM | CUT 60% |

### Essentiële vs Nice-to-Have

#### **CORE Requirements (MUST KEEP)**

1. **Validatieregels (ARAI/CON/ESS/STR/INT/SAM/VER)** - 168 regels
   - Dit is de **business logica**, kan niet worden verkort
   - Bevat gestructureerde toetsregels met voorbeelden
   - Enkele optimalisatie: STR-01 (lijn 151-157) overlapt met ARAI-06

2. **Ontologische Categorieën (ESS-02)** - 39 regels
   - KRITIEK voor correcte definitie structuur
   - Moet worden GESIMPLIFICEERD, niet verwijderd
   - Verwijder conflict met lijn 323-325

3. **Templates** - 14 regels
   - Concrete voorbeelden zijn waardevol
   - KEEP volledig

4. **Output Format** - 6 regels
   - Technische vereisten
   - KEEP volledig

#### **NICE-TO-HAVE (CAN BE CUT/CONDENSED)**

1. **Veelgemaakte Fouten (293-335)** - 43 regels
   - 80% is DUPLICATE van eerdere regels
   - CUT naar 8-10 regels (alleen unieke voorbeelden)

2. **Finale Instructies (380-419)** - 39 regels
   - Bevat veel redundantie met eerdere secties
   - CUT naar 15 regels (alleen checklist + metadata)

3. **Grammatica Regels (24-61)** - 37 regels
   - Overlap met VER-01, VER-02, VER-03
   - MERGE met VER sectie

4. **Kwaliteitsmetrieken (353-379)** - 26 regels
   - Nuttige metadata, maar kan worden COMPRESSED
   - CUT naar 10 regels

---

## 4. CONFLICTERENDE INSTRUCTIES

### Conflict #1: Ontologische Kick-Off vs Verboden Starts

**Locatie:** Lijn 73-92 vs 323-329

**Probleem:**
```
VOORSCHRIFT (lijn 73-92):
✅ "activiteit waarbij..."
✅ "handeling die..."
✅ "proces waarin..."

VERBOD (lijn 323-325):
❌ "Start niet met 'proces waarbij'"
❌ "Start niet met 'handeling die'"
```

**Impact:** AI krijgt tegengestelde instructies, resulteert in onvoorspelbaar gedrag

**Oplossing:**
```
DELETE lijn 323-329 volledig

VERVANG door (toevoegen bij ESS-02):
"⚠️ Gebruik SPECIFIEKE kick-off termen:
  ✅ 'activiteit waarbij [specifieke actor] [specifieke actie]'
  ❌ 'proces waarbij' (zonder verdere toespitsing)

  Voorbeeld:
  ✅ 'activiteit waarbij gegevens worden verzameld door directe waarneming'
  ❌ 'proces waarbij iets gebeurt'
"
```

### Conflict #2: Containerbegrippen Verbod vs Template Gebruik

**Locatie:** Lijn 127-128 (ARAI-02) vs Lijn 112-113 (Templates)

**Probleem:**
```
ARAI-02: "Vermijd vage containerbegrippen"
         "Lexicale containerbegrippen vermijden"

Template (lijn 113): "[Handeling/activiteit] waarbij [actor/systeem]..."
```

**Verduidelijking Nodig:**
"Activiteit" is TOEGESTAAN in kick-off positie (genus proximum), maar VERBODEN als standalone definitie.

**Oplossing:**
```
TOEVOEGEN bij ARAI-02:
"⚠️ Uitzondering: Containerbegrippen ZIJN toegestaan als genus proximum
    (kick-off term), MITS gevolgd door specificerende differentia specifica.

    ✅ 'activiteit waarbij [specifieke actor] [specifieke actie] uitvoert'
    ❌ 'activiteit die belangrijk is'
"
```

### Conflict #3: ESS-01 vs STR-06

**Locatie:** Lijn 142 vs 187-191

**Probleem:**
```
ESS-01: "Essentie, niet doel"
STR-06: "Essentie ≠ informatiebehoefte"

Beide zeggen HETZELFDE, maar met andere voorbeelden.
```

**Oplossing:**
```
MERGE beide regels:

"🔹 ESS-01 / STR-06 - Essentie, niet doel of informatiebehoefte
- Een definitie geeft WAT het begrip is, niet WAARVOOR het gebruikt wordt
- Toetsvraag: Beschrijft de definitie de aard/kenmerken, niet het doel of de behoefte?
  ✅ beveiligingsmaatregel: voorziening die ongeautoriseerde toegang voorkomt
  ❌ beveiligingsmaatregel: voorziening om ongeautoriseerde toegang te voorkomen
  ✅ proces dat beslissers identificeert
  ❌ proces om beslissers te kunnen informeren
"
```

---

## 5. PRIORITERING & OPTIMALISATIE STRATEGIE

### Fase 1: KRITIEKE FIXES (HIGH PRIORITY)

**Impact:** Verwijder conflicterende instructies die AI kapot maken

| Actie | Locatie | Reductie | Effort |
|-------|---------|----------|--------|
| **DELETE lijn 323-329** | Ontologische conflict | -7 regels | 5 min |
| **MERGE ESS-01 + STR-06** | Duplicate "essentie" regel | -6 regels | 10 min |
| **DELETE lijn 294-322** | Veelgemaakte fouten overlap | -29 regels | 5 min |
| **SIMPLIFY lijn 380-400** | Finale instructies redundantie | -15 regels | 10 min |

**Totaal:** -57 regels (14% reductie) in 30 minuten

### Fase 2: STRUCTURELE OPTIMALISATIE (MEDIUM PRIORITY)

**Impact:** Verbeter leesbaarheid en logische flow

| Actie | Locatie | Reductie | Effort |
|-------|---------|----------|--------|
| **MERGE Grammatica + VER** | Lijn 24-61 + 289-291 | -20 regels | 20 min |
| **CONDENSE Kwaliteitsmetrieken** | Lijn 353-379 | -16 regels | 15 min |
| **SIMPLIFY Ontologie** | Lijn 70-109 | -10 regels | 20 min |
| **REORGANIZE Validatieregels** | Lijn 125-292 | 0 regels | 30 min |

**Totaal:** -46 regels (11% reductie) in 1.5 uur

### Fase 3: CONTENT REFINEMENT (LOW PRIORITY)

**Impact:** Polish en finesse

| Actie | Locatie | Reductie | Effort |
|-------|---------|----------|--------|
| **REMOVE duplicate voorbeelden** | Diverse secties | -15 regels | 30 min |
| **OPTIMIZE bullet formatting** | Alle secties | -10 regels | 20 min |
| **ADD missing cross-references** | Validatieregels | 0 regels | 30 min |

**Totaal:** -25 regels (6% reductie) in 1.5 uur

---

## 6. CONCRETE OPTIMALISATIE ROADMAP

### Target Metrics

```
HUIDIGE STAAT:
- Totaal regels: 419
- Redundantie: ~40%
- Conflicten: 3 kritieke
- Token count: ~7.250 (schatting)

DOEL STAAT:
- Totaal regels: 290 (-31%)
- Redundantie: <10%
- Conflicten: 0
- Token count: ~4.500 (-38%)
```

### Optimalisatie Fasering

#### **Week 1: Critical Fixes**

**Dag 1-2: Conflict Resolution**
- [ ] DELETE lijn 323-329 (ontologische conflict)
- [ ] ADD verduidelijking bij ESS-02 over kick-off gebruik
- [ ] MERGE ESS-01 + STR-06
- [ ] TEST prompt met 10 voorbeeldbegrippen

**Dag 3-4: Duplicate Removal**
- [ ] DELETE lijn 294-322 (veelgemaakte fouten)
- [ ] KEEP alleen top 5 verboden starts bij ARAI-06
- [ ] CONDENSE finale instructies (lijn 380-400)
- [ ] TEST prompt met edge cases

**Dag 5: Validation**
- [ ] Draai volledige validatieregel test suite
- [ ] Check backwards compatibility met bestaande definities
- [ ] Measure token reduction

#### **Week 2: Structural Optimization**

**Dag 1-2: Section Merging**
- [ ] MERGE Grammatica (24-61) met VER (289-291)
- [ ] Reorganiseer in logische volgorde:
  1. Output Format
  2. Grammatica/VER (merged)
  3. Ontologie (ESS-02)
  4. Templates
  5. Validatieregels (ARAI/CON/ESS/STR/INT/SAM)
- [ ] TEST nieuwe structuur

**Dag 3-4: Content Condensing**
- [ ] CONDENSE Kwaliteitsmetrieken (353-379)
- [ ] SIMPLIFY Ontologie (70-109)
- [ ] OPTIMIZE voorbeelden (max 2 ✅ + 2 ❌ per regel)

**Dag 5: Final Polish**
- [ ] ADD cross-references tussen gerelateerde regels
- [ ] VERIFY alle validatieregels nog aanwezig
- [ ] CREATE version comparison document

#### **Week 3: Testing & Rollout**

**Dag 1-3: Integration Testing**
- [ ] Test met 50 diverse begrippen (proces/type/resultaat/exemplaar)
- [ ] Compare output v7 vs v8
- [ ] Check voor regressies in definitiekwaliteit

**Dag 4-5: Documentation & Deployment**
- [ ] UPDATE prompt generation code
- [ ] CREATE migration guide
- [ ] DEPLOY nieuwe prompt versie

---

## 7. CORE REQUIREMENTS DISTILLATIE

### Absolute Essentials (CANNOT BE REMOVED)

1. **Validatieregels (ARAI/CON/ESS/STR/INT/SAM/VER)** - 168 regels
   - Business logica kernstuk
   - Gestructureerd met voorbeelden
   - Enige optimalisatie: merge duplicates

2. **Ontologische Categorieën (ESS-02)** - 25 regels (na optimalisatie)
   - Proces/Type/Resultaat/Exemplaar onderscheid
   - Kick-off templates met voorbeelden
   - KRITIEK voor structuur correctheid

3. **Output Format Vereisten** - 6 regels
   - Technische specs (één zin, geen punt, etc.)
   - Niet-negocieerbaar

4. **Templates & Voorbeelden** - 14 regels
   - Concrete guidance voor AI
   - Bewezen effectief in praktijk

**Totaal CORE:** ~213 regels (51% van huidige prompt)

### Nice-to-Have maar Valuable

1. **Grammatica Regels** - 15 regels (na merge met VER)
   - Enkelvoud, actieve vorm, tegenwoordige tijd
   - Kan worden CONDENSED maar niet VERWIJDERD

2. **Context Instructies** - 10 regels
   - Organisatorisch/juridisch context verwerken
   - Nodig voor contextspecifieke definities

3. **Kwaliteitsmetrieken** - 10 regels (na condensing)
   - Karakterlimieten, complexiteitsindicatoren
   - Nuttig voor debugging

**Totaal NICE-TO-HAVE:** ~35 regels (8% van huidige prompt)

### Can Be Removed (Redundant/Low-Value)

1. **Veelgemaakte Fouten (293-335)** - Meeste is duplicate
   - KEEP: Top 5 verboden starts
   - DELETE: Rest (35 regels)

2. **Finale Instructies (380-400)** - Herhaalt eerdere regels
   - KEEP: Checklist (10 regels)
   - DELETE: Redundante vragen (15 regels)

3. **Duplicate Voorbeelden** - Scattered door prompt
   - Consolideer naar max 2 ✅ + 2 ❌ per regel
   - DELETE: Overbodige herhaling (20 regels)

**Totaal REMOVABLE:** ~70 regels (17% van huidige prompt)

---

## 8. WERKELIJKE NOODZAAK ANALYSE

### Categorisering per Urgentie

#### 🔴 CRITICAL (Must Fix Immediately)

**Reden:** Broken prompt door conflicten

1. **Ontologische Conflict (lijn 73-92 vs 323-329)**
   - AI krijgt tegengestelde instructies
   - Resulteert in onvoorspelbare output
   - **FIX:** DELETE lijn 323-329, ADD verduidelijking

2. **Duplicate "Geen Lidwoord" (6x herhaling)**
   - Token waste zonder toegevoegde waarde
   - Verhoogt prompt complexity score onnodig
   - **FIX:** KEEP alleen ARAI-06, DELETE rest

#### 🟡 HIGH (Should Fix This Sprint)

**Reden:** Significante kwaliteitsverbetering

1. **Veelgemaakte Fouten Sectie (lijn 293-335)**
   - 80% overlap met eerdere regels
   - 43 regels kunnen worden gereduceerd naar 8
   - **FIX:** DELETE redundantie, KEEP unieke voorbeelden

2. **ESS-01 + STR-06 Merge**
   - Beide regels zeggen hetzelfde
   - Verwarrend voor AI (welke volgen?)
   - **FIX:** MERGE naar één geconsolideerde regel

3. **Grammatica + VER Merge**
   - Lijn 24-61 overlapt met lijn 289-291
   - Kan worden gecombineerd zonder informatieverlies
   - **FIX:** MERGE beide secties

#### 🟢 MEDIUM (Nice to Have)

**Reden:** Verbetert leesbaarheid/efficiency

1. **Kwaliteitsmetrieken Condensing**
   - 26 regels kunnen naar 10 zonder functieverlies
   - Metadata is nuttig maar te verbose
   - **FIX:** CONDENSE naar essentie

2. **Ontologie Simplificatie**
   - 39 regels kunnen naar 25 met betere structuur
   - Voorbeelden zijn goed, maar te veel herhaling
   - **FIX:** SIMPLIFY zonder content loss

3. **Finale Instructies Cleanup**
   - 39 regels naar 15 door duplicate removal
   - Checklist is waardevol, maar rest is redundant
   - **FIX:** TRIM naar essentials

#### 🔵 LOW (Future Enhancement)

**Reden:** Polish en finesse

1. **Cross-Reference System**
   - Voeg links toe tussen gerelateerde regels
   - Helpt AI navigeren tussen secties
   - **FIX:** ADD hyperlinks (indien ondersteund)

2. **Voorbeelden Optimalisatie**
   - Consolideer naar max 2 ✅ + 2 ❌ per regel
   - Verbetert scan-baarheid
   - **FIX:** OPTIMIZE voorbeelden

---

## 9. IMPACT ASSESSMENT

### Token Reduction Schatting

```
HUIDIGE STAAT (v7):
- Totaal regels: 419
- Geschat tokens: ~7.250
- Redundantie: ~40%

NA FASE 1 (Critical Fixes):
- Totaal regels: 362 (-57)
- Geschat tokens: ~6.200 (-1.050, -14%)
- Redundantie: ~25%

NA FASE 2 (Structural):
- Totaal regels: 316 (-103)
- Geschat tokens: ~5.400 (-1.850, -26%)
- Redundantie: ~15%

NA FASE 3 (Polish):
- Totaal regels: 290 (-129)
- Geschat tokens: ~4.500 (-2.750, -38%)
- Redundantie: <10%
```

### Risico Analyse

| Actie | Risico | Mitigatie |
|-------|--------|-----------|
| DELETE lijn 323-329 | 🟢 LOW | Conflicteert met ESS-02, safe to remove |
| MERGE ESS-01 + STR-06 | 🟢 LOW | Beide regels identiek, merge is safe |
| DELETE Veelgemaakte Fouten | 🟡 MEDIUM | Test met edge cases na removal |
| MERGE Grammatica + VER | 🟡 MEDIUM | Verify geen informatie verloren gaat |
| CONDENSE Kwaliteitsmetrieken | 🟢 LOW | Metadata, niet kritiek voor output |
| SIMPLIFY Ontologie | 🟡 MEDIUM | Core functionaliteit, extensive testing needed |

### Backwards Compatibility

**Verwachting:** 95%+ backwards compatible

**Redenen:**
1. Core validatieregels blijven intact
2. Templates blijven behouden
3. Ontologische categorieën worden VERBETERD (conflict fix)
4. Alleen redundantie wordt verwijderd

**Test Strategy:**
1. Draai 50 bestaande definities door v7 en v8
2. Compare outputs met diff tool
3. Flaggen significante verschillen
4. Manuele review van afwijkingen

---

## 10. CONCLUSIES & AANBEVELINGEN

### Hoofdbevindingen

1. **Massieve Redundantie (40%)**: 169 van 419 regels zijn duplicate of near-duplicate
2. **3 Kritieke Conflicten**: Tegengestelde instructies voor ontologie, containerbegrippen, essentie
3. **Onduidelijke Structuur**: Logische flow is verbroken door slechte sectie volgorde
4. **Token Waste**: ~2.750 tokens (38%) kunnen worden geëlimineerd zonder functieverlies

### CRITICAL Actions (Must Do)

```bash
# FASE 1: CRITICAL FIXES (30 minuten)
1. DELETE lijn 323-329  # Fix ontologische conflict
2. DELETE lijn 294-322  # Remove duplicate verboden starts
3. MERGE ESS-01 + STR-06  # Consolidate duplicate regel
4. TRIM lijn 380-400 → 15 regels  # Cleanup finale instructies

EXPECTED RESULT:
- 419 → 362 regels (-14%)
- 7.250 → 6.200 tokens (-14%)
- 3 conflicten → 0 conflicten
```

### HIGH Priority Actions (Should Do)

```bash
# FASE 2: STRUCTURAL OPTIMIZATION (1.5 uur)
1. MERGE Grammatica (24-61) + VER (289-291)
2. CONDENSE Kwaliteitsmetrieken (353-379) → 10 regels
3. SIMPLIFY Ontologie (70-109) → 25 regels
4. REORGANIZE secties in logische volgorde

EXPECTED RESULT:
- 362 → 316 regels (-25% vs origineel)
- 6.200 → 5.400 tokens (-26% vs origineel)
- Redundantie: 40% → 15%
```

### MEDIUM Priority (Nice to Have)

```bash
# FASE 3: POLISH (1.5 uur)
1. OPTIMIZE voorbeelden (max 2✅ + 2❌ per regel)
2. ADD cross-references tussen gerelateerde regels
3. VERIFY backwards compatibility met test suite

EXPECTED RESULT:
- 316 → 290 regels (-31% vs origineel)
- 5.400 → 4.500 tokens (-38% vs origineel)
- Redundantie: 15% → <10%
```

### Definitief Advies

**START MET:** Fase 1 (Critical Fixes)
**REDEN:** 30 minuten werk, 14% reductie, 100% conflict removal
**RISICO:** Minimaal (alleen duplicate removal)

**DAARNA:** Fase 2 (Structural Optimization)
**REDEN:** 1.5 uur werk, totaal 26% reductie, veel betere leesbaarheid
**RISICO:** Medium (test met 50 begrippen vereist)

**OPTIONEEL:** Fase 3 (Polish)
**REDEN:** 1.5 uur werk, totaal 31% reductie, perfectie
**RISICO:** Low (alleen formatting changes)

---

## BIJLAGEN

### Bijlage A: Volledige Duplicate Mapping

```
DUPLICATE #1: "Geen lidwoord"
- Lijn 13: Output format
- Lijn 134: ARAI-06 regel
- Lijn 294: Veelgemaakte fouten intro
- Lijn 320-322: Specifieke verboden
- Lijn 386: Checklist

ACTIE: KEEP lijn 134, DELETE rest

DUPLICATE #2: "Geen koppelwerkwoord"
- Lijn 78: ESS-02 context
- Lijn 134: ARAI-06 regel
- Lijn 295: Veelgemaakte fouten intro
- Lijn 301-318: 18 specifieke verboden
- Lijn 344: Tabel samenvatting

ACTIE: KEEP lijn 134 + top 5 voorbeelden, DELETE rest

DUPLICATE #3: "Enkelvoud regel"
- Lijn 26-31: Grammatica uitleg
- Lijn 289-290: VER-01 + VER-02
- Lijn 300: Veelgemaakte fouten

ACTIE: KEEP lijn 26-31, MERGE VER, DELETE lijn 300

DUPLICATE #4: "Essentie niet doel"
- Lijn 142: ESS-01
- Lijn 187-191: STR-06

ACTIE: MERGE naar één regel met beide voorbeelden
```

### Bijlage B: Conflict Resolution Details

**CONFLICT #1: Ontologische Kick-Off**

```diff
HUIDIGE STAAT (CONFLICTEREND):

Lijn 73-77:
+ "start met: 'activiteit waarbij...', 'handeling die...', 'proces waarin...'"

Lijn 323-325:
- "❌ Start niet met 'proces waarbij'"
- "❌ Start niet met 'handeling die'"

NIEUWE STAAT (RESOLVED):

Lijn 73-77: KEEP (unchanged)
Lijn 323-329: DELETE volledig

TOEVOEGEN bij ESS-02:
"⚠️ Gebruik SPECIFIEKE kick-off, niet generiek:
  ✅ 'activiteit waarbij gegevens worden verzameld door directe waarneming'
  ❌ 'proces waarbij iets gebeurt' (te vaag)

  De kick-off moet meteen toespitsen op het specifieke begrip."
```

**CONFLICT #2: Containerbegrippen**

```diff
HUIDIGE STAAT (ONDUIDELIJK):

ARAI-02: "Vermijd vage containerbegrippen"
Template: "[Handeling/activiteit] waarbij..."

=> Wanneer mag "activiteit" WEL?

NIEUWE STAAT (VERDUIDELIJKT):

TOEVOEGEN bij ARAI-02:
"⚠️ Uitzondering: Containerbegrippen ZIJN toegestaan als genus proximum
    (kick-off), MITS direct gevolgd door specificerende differentia.

    ✅ 'activiteit waarbij [specifieke actor] [specifieke actie]'
    ❌ 'activiteit die plaatsvindt' (te vaag)
    ❌ 'proces' (geen toespitsing)"
```

### Bijlage C: Recommended Section Order

```
NIEUWE STRUCTUUR (Logische Flow):

1. INTRODUCTIE (1-10)
   └─ Basis rol & vereisten

2. OUTPUT FORMAT (11-16)
   └─ Technische specs

3. GRAMMATICA & VORM (MERGED: 24-61 + 289-291)
   └─ Enkelvoud, actieve vorm, tegenwoordige tijd, afkortingen

4. ONTOLOGISCHE CATEGORIEËN (70-109, SIMPLIFIED)
   └─ Proces/Type/Resultaat/Exemplaar
   └─ Kick-off templates
   └─ Voorbeelden

5. TEMPLATES (110-124)
   └─ Concrete structuren

6. VALIDATIEREGELS (125-288, OPTIMIZED)
   └─ ARAI (Algemeen)
   └─ CON (Context)
   └─ ESS (Essentie, MERGED ESS-01+STR-06)
   └─ STR (Structuur)
   └─ INT (Integriteit)
   └─ SAM (Samenhang)

7. CONTEXT INFO (63-69 + 336-351)
   └─ Organisatorisch/juridisch
   └─ Context-specifieke verboden

8. KWALITEITSMETRIEKEN (353-379, CONDENSED)
   └─ Karakterlimieten
   └─ Complexiteitsindicatoren

9. FINALE INSTRUCTIES (380-419, TRIMMED)
   └─ Opdracht
   └─ Checklist (condensed)
   └─ Metadata
```

---

**EINDE ANALYSE**

**Volgende Stap:** Implementatie planning - zie `/docs/planning/` voor concrete refactor roadmap.
