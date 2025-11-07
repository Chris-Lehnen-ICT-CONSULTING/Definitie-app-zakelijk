# Prompt v8 Implementatie Plan - Fase 1 (Critical Fixes)

**Versie:** v7 → v8
**Target:** -14% tokens, 0 conflicten
**Effort:** 30 minuten
**Risico:** 🟢 LOW

---

## 🎯 OVERZICHT WIJZIGINGEN

### Totaal Impact

```
VOOR (v7):
- Regels: 419
- Tokens: ~7.250
- Conflicten: 3 kritiek
- Redundantie: 40%

NA (v8 Fase 1):
- Regels: 362 (-57, -14%)
- Tokens: ~6.200 (-1.050, -14%)
- Conflicten: 0 (-3, -100%)
- Redundantie: 25% (-15pp)
```

### 4 Concrete Wijzigingen

1. **FIX Ontologisch Conflict** - DELETE lijn 323-329 (-7 regels)
2. **REMOVE Duplicate Fouten** - DELETE lijn 294-322 (-29 regels)
3. **MERGE Duplicate Regels** - MERGE lijn 142 + 187-191 (-6 regels)
4. **TRIM Finale Instructies** - CONDENSE lijn 380-400 (-15 regels)

---

## 🔧 CONCRETE WIJZIGINGEN

Zie volledige analyse in:
- `/docs/analyses/PROMPT_ARCHITECTURE_ANALYSIS.md` (Sectie 4: Conflicterende Instructies)
- `/docs/analyses/PROMPT_OPTIMIZATION_SUMMARY.md` (Quick Wins sectie)

---

## ✅ IMPLEMENTATIE CHECKLIST

### Pre-Implementation (10 min)

- [ ] Backup huidige prompt naar `/config/prompts/prompt_v7_backup.txt`
- [ ] Create v8 werkbestand in `/config/prompts/prompt_v8_draft.txt`
- [ ] Selecteer 50 test begrippen
- [ ] Run v7 baseline

### Implementation (30 min)

- [ ] Wijziging #1: DELETE lijn 323-329, ADD verduidelijking bij ESS-02
- [ ] Wijziging #2: DELETE lijn 294-335, UPDATE ARAI-06
- [ ] Wijziging #3: MERGE ESS-01 + STR-06
- [ ] Wijziging #4: DELETE lijn 394-400, CONDENSE checklist

### Post-Implementation (30 min)

- [ ] Verify regel count: ~381
- [ ] Run 10 test begrippen
- [ ] Compare met v7 baseline
- [ ] Manual review afwijkingen

---

**Zie volledige details in:** `/docs/analyses/PROMPT_ARCHITECTURE_ANALYSIS.md`
