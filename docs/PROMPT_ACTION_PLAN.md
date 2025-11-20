# Prompt Optimalisatie - Actieplan

**Doel:** Token limit oplossen + clean codebase
**Investering:** ~7 uur
**Resultaat:** 8.283 → 6.233 tokens (ONDER LIMIT)

---

## ✅ GEDAAN

- [x] STR/INT migration (commit 3e9c6f57) → -2,043 tokens
- [x] KISS enforcement toegevoegd aan CLAUDE.md

---

## 📋 QUICK WINS (Week 1 - 7 uur)

### 1. Delete Forbidden Patterns (1u) → -500 tokens
**Issue:** DEF-157
**Wat:** Verwijder 189 hardcoded "verboden patronen" uit modules
**Waarom:** Validatieregels vangen deze al af, dus redundant

### 2. Move Metadata to UI (1.5u) → -600 tokens
**Issue:** DEF-158
**Wat:** Verplaats instructieteksten naar UI layer
**Waarom:** Hoort niet in prompt, is UI tekst

### 3. Filter Examples (1.5u) → -700 tokens
**Issue:** DEF-159
**Wat:** Toon alleen relevante voorbeelden per categorie
**Waarom:** Juridisch begrip ≠ wettelijk voorschrift voorbeelden

### 4. Merge Duplicates (1u) → -200 tokens
**Issue:** DEF-160
**Wat:** Consolideer dubbele instructies
**Waarom:** Zelfde info staat 2-3x in verschillende modules

### 5. Add Tests (2u)
**Wat:** Test coverage voor STR/INT migration + token count validatie
**Waarom:** Voorkom regressies, valideer -2,043 token claim

---

## 🎯 SUCCESS CRITERIA

- [ ] Token count: <6,500 (ONDER LIMIT)
- [ ] Alle tests passing
- [ ] Token reduction gemeten (niet geschat)
- [ ] Clean docs/ directory

---

## 📊 REALITY CHECK (Wat werkt al)

✅ **JSONBasedRulesModule** (commit af6c7fd3)
   - 5 rule modules geconsolideerd
   - 80% code reductie
   - Pattern proven & tests passing

✅ **RuleCache** (US-202)
   - 77% sneller, 81% minder memory
   - GEMETEN, niet geschat

✅ **STR/INT Migration** (commit 3e9c6f57)
   - 646 lines → 20 lines
   - ~2,043 tokens saved
   - Ready to test

---

## 🧹 CLEANUP (Optioneel - na quick wins)

- Archive 60+ analysis documenten naar `docs/archief/2025-11-analysis-bloat/`
- Keep alleen dit actieplan
- Reden: Analysis paralysis, KISS principle

---

## 🔗 LINKS

**Linear Issues:**
- DEF-157: Prompt Quick Wins (parent)
- DEF-158: Move metadata to UI
- DEF-159: Filter examples
- DEF-160: Merge duplicates

**Commits:**
- `3e9c6f57`: STR/INT migration
- `af6c7fd3`: JSON-based rules
- `c2c8633c`: RuleCache singleton

---

**Last updated:** 2025-11-18
**Status:** STR/INT committed ✅, Quick wins ready to implement
