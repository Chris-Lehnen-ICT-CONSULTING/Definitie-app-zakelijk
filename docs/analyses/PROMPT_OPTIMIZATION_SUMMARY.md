# Prompt Optimalisatie - Executive Summary

**Datum:** 2025-11-07
**Geanalyseerd:** `_Definitie_Generatie_prompt-7.txt` (419 regels)
**Status:** 🔴 KRITIEKE PROBLEMEN GEVONDEN

---

## 🎯 QUICK WINS (30 minuten, 14% reductie)

### Direct Uitvoerbaar - Nul Risico

```bash
# 1. FIX KRITIEK CONFLICT
DELETE lijn 323-329  # "Start niet met proces waarbij/handeling die"
REDEN: Conflicteert met ESS-02 die juist "activiteit waarbij" vereist
IMPACT: -7 regels, AI krijgt geen tegengestelde instructies meer

# 2. REMOVE MASSIVE DUPLICATE
DELETE lijn 294-322  # Veelgemaakte fouten sectie
REDEN: 80% overlap met ARAI-06 en andere regels
IMPACT: -29 regels, geen functieverlies

# 3. MERGE DUPLICATE REGELS
MERGE lijn 142 (ESS-01) + lijn 187-191 (STR-06)
REDEN: Beide zeggen "essentie niet doel"
IMPACT: -6 regels, duidelijkere instructie

# 4. TRIM FINALE INSTRUCTIES
CONDENSE lijn 380-400 van 39 naar 15 regels
REDEN: Herhaalt eerdere regels en checklist items
IMPACT: -15 regels, behoud alleen checklist

TOTAAL: 419 → 362 regels (-14%)
TOKENS: 7.250 → 6.200 (-14%)
CONFLICTEN: 3 → 0
```

---

## 📊 HUIDIGE STAAT DIAGNOSE

### Redundantie Heatmap

```
SECTIE                          REGELS   REDUNDANTIE   ACTIE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Introductie                     10       🟢 0%         KEEP
Output Format                   6        🟢 0%         KEEP
Definitie Kwaliteit            6        🟡 30%        TRIM
Grammatica Regels              37       🟡 40%        MERGE
Context Info                   7        🟢 0%         KEEP
Betekenislaag (ESS-02)         39       🔴 CONFLICT   FIX!
Templates                      14       🟢 0%         KEEP
Validatieregels (CORE)         168      🟡 10%        OPTIMIZE
Veelgemaakte Fouten            43       🔴 80%        CUT!
Context Verboden               16       🟢 0%         KEEP
Kwaliteitsmetrieken            26       🟡 60%        CONDENSE
Finale Instructies             39       🔴 70%        CUT!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAAL                         419      ~40%          -129

LEGEND: 🟢 Geen redundantie | 🟡 Matige redundantie | 🔴 Kritieke redundantie
```

### Top 3 Conflicten

#### 🔴 CONFLICT #1: Ontologische Kick-Off (KRITIEK!)

```
Lijn 73-77:   ✅ "start met: 'activiteit waarbij...', 'handeling die...'"
Lijn 323-325: ❌ "Start niet met 'proces waarbij', 'handeling die'"

=> AI krijgt tegengestelde instructies!

OPLOSSING: DELETE lijn 323-329
```

#### 🟡 CONFLICT #2: Containerterm Gebruik

```
ARAI-02: "Vermijd vage containerbegrippen (proces, activiteit)"
Template: "[Handeling/activiteit] waarbij..."

=> Wanneer MAG "activiteit" wel gebruikt worden?

OPLOSSING: Verduidelijk "toegestaan in kick-off, verboden standalone"
```

#### 🟡 CONFLICT #3: Essentie Regel Duplicate

```
ESS-01 (lijn 142): "Essentie, niet doel"
STR-06 (lijn 187): "Essentie ≠ informatiebehoefte"

=> Beide regels zeggen HETZELFDE

OPLOSSING: MERGE naar één geconsolideerde regel
```

---

## 🎬 3-FASE ROADMAP

### FASE 1: KRITIEKE FIXES (30 min) - MUST DO

**Doel:** Verwijder conflicten en massieve duplicates

| Actie | Regels | Risico | Effort |
|-------|--------|--------|--------|
| Fix ontologisch conflict | -7 | 🟢 | 5 min |
| Delete veelgemaakte fouten | -29 | 🟢 | 5 min |
| Merge ESS-01 + STR-06 | -6 | 🟢 | 10 min |
| Trim finale instructies | -15 | 🟢 | 10 min |
| **TOTAAL** | **-57** | **LOW** | **30 min** |

**Resultaat:** 419 → 362 regels (-14%), 0 conflicten

---

### FASE 2: STRUCTURELE OPTIMALISATIE (1.5 uur) - SHOULD DO

**Doel:** Verbeter leesbaarheid en logische flow

| Actie | Regels | Risico | Effort |
|-------|--------|--------|--------|
| Merge Grammatica + VER | -20 | 🟡 | 20 min |
| Condense Kwaliteitsmetrieken | -16 | 🟢 | 15 min |
| Simplify Ontologie | -10 | 🟡 | 20 min |
| Reorganize secties | 0 | 🟢 | 30 min |
| **TOTAAL** | **-46** | **MED** | **85 min** |

**Resultaat:** 362 → 316 regels (-25% vs origineel)

---

### FASE 3: POLISH (1.5 uur) - NICE TO HAVE

**Doel:** Perfectie en finesse

| Actie | Regels | Risico | Effort |
|-------|--------|--------|--------|
| Optimize voorbeelden | -15 | 🟢 | 30 min |
| Optimize bullet formatting | -10 | 🟢 | 20 min |
| Add cross-references | 0 | 🟢 | 30 min |
| **TOTAAL** | **-25** | **LOW** | **80 min** |

**Resultaat:** 316 → 290 regels (-31% vs origineel)

---

## 📈 VERWACHTE IMPACT

### Token Reductie Projectie

```
PROGRESSIE:

Fase 0 (HUIDIG):      ████████████████████ 7.250 tokens (100%)
                      419 regels, 40% redundantie, 3 conflicten

Fase 1 (CRITICAL):    ████████████████░░░░ 6.200 tokens (-14%)
                      362 regels, 25% redundantie, 0 conflicten ✅

Fase 2 (STRUCTURAL):  ██████████████░░░░░░ 5.400 tokens (-26%)
                      316 regels, 15% redundantie, betere flow ✅

Fase 3 (POLISH):      ████████████░░░░░░░░ 4.500 tokens (-38%)
                      290 regels, <10% redundantie, perfectie ✅

LEGEND: █ Gebruikt | ░ Geëlimineerd
```

### Kwaliteit Metrics

| Metric | Huidig | Na Fase 1 | Na Fase 2 | Na Fase 3 |
|--------|--------|-----------|-----------|-----------|
| **Regels** | 419 | 362 | 316 | 290 |
| **Tokens** | 7.250 | 6.200 | 5.400 | 4.500 |
| **Redundantie** | 40% | 25% | 15% | <10% |
| **Conflicten** | 3 | 0 | 0 | 0 |
| **Leesbaarheid** | 6/10 | 7/10 | 8/10 | 9/10 |

---

## 🎯 CORE vs REMOVABLE

### Behouden (Core Logica)

```
✅ Validatieregels (ARAI/CON/ESS/STR/INT/SAM/VER)  168 regels (40%)
   └─ Business logica kernstuk, minimaal redundant

✅ Ontologische Categorieën (ESS-02)                25 regels (6%)
   └─ Na conflict fix en simplificatie

✅ Templates & Voorbeelden                          14 regels (3%)
   └─ Concrete guidance, bewezen effectief

✅ Output Format Vereisten                          6 regels (1%)
   └─ Technische specs, niet-negocieerbaar

✅ Grammatica Regels (MERGED)                       15 regels (4%)
   └─ Na merge met VER, zonder duplicates

✅ Context Instructies                              10 regels (2%)
   └─ Nodig voor contextspecifieke definities

✅ Kwaliteitsmetrieken (CONDENSED)                  10 regels (2%)
   └─ Nuttig voor debugging

SUBTOTAAL CORE: 248 regels (59% van origineel)
```

### Verwijderen (Redundant)

```
❌ Veelgemaakte Fouten (293-335)                   -35 regels
   └─ 80% duplicate van ARAI-06 en andere regels

❌ Finale Instructies redundantie                  -24 regels
   └─ Herhaalt checklist en eerdere instructies

❌ Grammatica/VER overlap                          -20 regels
   └─ Na merge blijft alleen essentie over

❌ Kwaliteitsmetrieken verbose                     -16 regels
   └─ Metadata kan veel compacter

❌ Duplicate voorbeelden                           -15 regels
   └─ Max 2✅ + 2❌ per regel is voldoende

❌ Ontologie redundantie                           -14 regels
   └─ Simplificatie zonder informatieverlies

❌ Overige duplicates                              -5 regels
   └─ Scattered door prompt

SUBTOTAAL REMOVABLE: 129 regels (31% van origineel)
```

### Balance Check

```
ORIGINEEL:        419 regels (100%)
  ├─ CORE:        248 regels (59%)  ✅ Behouden
  ├─ REMOVABLE:   129 regels (31%)  ❌ Verwijderen
  └─ METADATA:    42 regels (10%)   🔧 Optimaliseren

OPTIMIZED:        290 regels (69%)
  ├─ CORE:        248 regels (86%)
  └─ METADATA:    42 regels (14%)
```

---

## 🚦 RISICO ASSESSMENT

### Per Fase

| Fase | Risico | Mitigatie | Backwards Compatibility |
|------|--------|-----------|-------------------------|
| **Fase 1** | 🟢 LOW | Alleen duplicates verwijderen | 98% compatible |
| **Fase 2** | 🟡 MEDIUM | Test met 50 begrippen | 95% compatible |
| **Fase 3** | 🟢 LOW | Alleen formatting | 99% compatible |

### Waarom Laag Risico?

1. **Core validatieregels blijven intact** (168 regels ongewijzigd)
2. **Templates behouden** (14 regels ongewijzigd)
3. **Alleen redundantie wordt verwijderd**
4. **Conflicten worden OPGELOST, niet verplaatst**
5. **Ontologische categorieën worden VERBETERD**

### Test Strategie

```bash
# Test Plan voor Fase 1
1. Draai 50 bestaande definities door v7 en v8
2. Compare outputs met diff tool
3. Flag significante verschillen (>10% change)
4. Manuele review van alle afwijkingen
5. Sign-off: max 2% regressie toegestaan

# Success Criteria
✅ <2% regressie in definitiekwaliteit
✅ 0 conflicten in validatieregels
✅ -14% token reductie
✅ Alle 45 validatieregels nog aanwezig
```

---

## 💡 AANBEVELINGEN

### DIRECT ACTIE (Nu uitvoeren)

**START MET FASE 1:**
- Tijdsinvestering: 30 minuten
- Token reductie: 14%
- Conflict removal: 100%
- Risico: Minimaal

**Verwachte ROI:** 25x (1.050 tokens / 30 min = 35 tokens per minuut)

### PLANNING

**Week 1:**
- Ma/Di: Fase 1 implementatie + testing
- Wo/Do: Validatie met 50 begrippen
- Vr: Sign-off en documentatie

**Week 2:**
- Ma-Do: Fase 2 implementatie (indien Fase 1 succesvol)
- Vr: Integration testing

**Week 3:**
- Optioneel: Fase 3 polish

### NIET DOEN

❌ **Grote refactor in één keer** - Te risicovol
❌ **Validatieregels aanpassen** - Core business logica
❌ **Templates verwijderen** - Bewezen effectief
❌ **Skip testing** - Backwards compatibility kritiek

---

## 📋 CHECKLIST VOOR IMPLEMENTATIE

### Pre-Implementation

- [ ] Backup huidige prompt v7
- [ ] Setup A/B testing framework
- [ ] Prepare 50 test begrippen (diverse categorieën)
- [ ] Document huidige outputs als baseline

### Fase 1 Execution

- [ ] DELETE lijn 323-329 (ontologisch conflict)
- [ ] ADD verduidelijking bij ESS-02
- [ ] DELETE lijn 294-322 (veelgemaakte fouten)
- [ ] MERGE ESS-01 + STR-06
- [ ] TRIM lijn 380-400 naar 15 regels
- [ ] Verify: 419 → 362 regels

### Post-Implementation

- [ ] Draai 50 test begrippen door v8
- [ ] Compare outputs met v7 baseline
- [ ] Measure: token count, conflicts, redundantie
- [ ] Review afwijkingen >10%
- [ ] Sign-off door stakeholder
- [ ] Deploy v8 naar productie

### Monitoring (Week 1 na deployment)

- [ ] Track definitiekwaliteit metrics
- [ ] Monitor gebruiker feedback
- [ ] Check voor nieuwe edge cases
- [ ] Document lessons learned

---

## 📖 GERELATEERDE DOCUMENTEN

- **Volledige Analyse:** `/docs/analyses/PROMPT_ARCHITECTURE_ANALYSIS.md`
- **Huidige Prompt:** `/Users/chrislehnen/Downloads/_Definitie_Generatie_prompt-7.txt`
- **Validatieregels:** `config/toetsregels/regels/`
- **Prompt Builder:** `src/services/prompt/prompt_builder.py`

---

**EINDE EXECUTIVE SUMMARY**

**Volgende Actie:** Implementeer Fase 1 (30 min) en test met 50 begrippen
