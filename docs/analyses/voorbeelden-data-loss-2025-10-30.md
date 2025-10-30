# Data Loss Analyse: Voorbeelden Verlies 2025-10-30

**Status:** ✅ OPGELOST
**Datum incident:** 2025-10-30 15:43
**Datum herstel:** 2025-10-30 17:00
**Impact:** 10 definities, 130 voorbeelden tijdelijk verloren

## 📋 Executive Summary

Op 30 oktober 2025 om 15:43 zijn bij 10 recent aangemaakte definities (ID's 79-91) alle voorbeelden verloren gegaan, behalve de "sentence" voorbeelden. Dit betrof:
- Praktijkvoorbeelden
- Tegenvoorbeelden
- Synoniemen
- Antoniemen
- Toelichtingen

**Root cause:** Git branch switch terwijl database nog in git tracking zat, waardoor database werd overschreven met oudere versie.

**Recovery:** Succesvol hersteld uit TXT export bestanden (130 voorbeelden).

## 🔍 Timeline

| Tijd | Event | Details |
|------|-------|---------|
| **10:10-12:55** | Definities aangemaakt | ID's 79-91 aangemaakt met volledige voorbeelden |
| **15:43** | ⚠️ **Data loss** | Git checkout van `feature/DEF-54` → `main` overschrijft database |
| **15:50-16:32** | Gedeeltelijke regeneratie | Alleen "sentence" voorbeelden opnieuw gegenereerd |
| **16:28-16:46** | Preventie geïmplementeerd | Database uit git gehaald (.gitignore) |
| **17:00** | ✅ **Recovery compleet** | 130 voorbeelden hersteld uit export files |

## 🔬 Root Cause Analysis

### Directe Oorzaak

```bash
# Git reflog toont:
HEAD@{2025-10-30 15:43:22 +0100}: checkout: moving from feature/DEF-54 to main
```

De database `data/definities.db` zat op dat moment nog in git tracking. Bij de branch switch werd het bestand overschreven met de versie van `main`, die **alleen "sentence" voorbeelden** bevatte voor deze definities.

### Onderliggende Problemen

1. **Database in Git**
   - `data/definities.db` werd getrackt in repository
   - Branch switches overschrijven lokale database wijzigingen
   - Geen warning bij data loss

2. **Incomplete Export tijdens Ontwikkeling**
   - Geen automatische backup voor elke definitie save
   - TXT exports waren wel aanwezig, maar handmatig

3. **Geen Validatie op Voorbeelden Compleetheid**
   - Geen check of alle 6 voorbeeld typen aanwezig zijn
   - Geen alerting bij ontbrekende voorbeelden

## 📊 Impact Analysis

### Betroffen Definities

| ID | Begrip | Aangemaakt | Verloren Voorbeelden |
|----|--------|------------|---------------------|
| 79 | biografisch identiteitskenmerk | 2025-10-29 10:27 | 13 |
| 82 | biometrie | 2025-10-29 11:54 | 13 |
| 83 | biometrisch identiteitskenmerk | 2025-10-29 12:10 | 13 |
| 84 | digitaal identiteitsmiddel | 2025-10-29 12:21 | 13 |
| 85 | digitaal identiteitsbewijs | 2025-10-29 12:35 | 13 |
| 86 | digitaal identiteitsbewijs | 2025-10-29 12:37 | 13 |
| 87 | identiteit vaststellen | 2025-10-29 12:50 | 13 |
| 88 | identiteit vaststellen | 2025-10-29 12:55 | 13 |
| 90 | identiteit bepalen | 2025-10-30 09:49 | 13 |
| 91 | identiteit verifiëren en verrijken | 2025-10-30 10:10 | 13 |
| **TOTAAL** | **10 definities** | | **130 voorbeelden** |

### Voorbeeld Type Breakdown (per definitie)

- **Sentence examples:** 3 (✅ behouden)
- **Practical examples:** 1 (❌ verloren, ✅ hersteld)
- **Counter examples:** 1 (❌ verloren, ✅ hersteld)
- **Synonyms:** 5 (❌ verloren, ✅ hersteld)
- **Antonyms:** 5 (❌ verloren, ✅ hersteld)
- **Explanation:** 1 (❌ verloren, ✅ hersteld)

## 🔧 Recovery Process

### 1. Detection

```sql
-- Identificeer definities zonder alle voorbeeld typen
SELECT d.id, d.begrip,
       GROUP_CONCAT(DISTINCT v.voorbeeld_type) as types_present
FROM definities d
LEFT JOIN definitie_voorbeelden v ON d.id = v.definitie_id
WHERE d.created_at >= '2025-10-29'
GROUP BY d.id
HAVING COUNT(DISTINCT v.voorbeeld_type) < 6;
```

### 2. Recovery Script

Nieuw script: `scripts/recover_voorbeelden.py`

**Features:**
- Parse ALLE voorbeeld typen uit TXT export format
- Dry-run mode voor verificatie
- Detectie van bestaande voorbeelden (geen duplicates)
- Detailed progress logging

**Resultaat:**
```
✅ RECOVERY COMPLEET!
   Hersteld: 130 voorbeelden
```

### 3. Verification

```sql
-- Verificatie: alle definities hebben 6 voorbeeld typen
SELECT definitie_id, COUNT(DISTINCT voorbeeld_type) as type_count
FROM definitie_voorbeelden
WHERE definitie_id IN (79, 82, 83, 84, 85, 86, 87, 88, 90, 91)
GROUP BY definitie_id;
-- Result: Alle definities hebben type_count = 6 ✅
```

## 🛡️ Preventie Maatregelen

### Geïmplementeerd (2025-10-30)

1. **Database uit Git** ✅
   ```bash
   # Commit bbac2a71: "fix: stop tracking data/definities.db"
   echo "data/definities.db" >> .gitignore
   git rm --cached data/definities.db
   ```

2. **Auto-Backup Systeem** ✅ (EPIC-016, commit 82e6a256)
   - Automatische backups bij elke definitie save
   - Locatie: `data/backups/auto/`
   - Rolling backup met symlink naar `latest.db`

### Aanbevolen Verbeteringen

3. **Voorbeelden Compleetheid Check** (TODO)
   ```python
   # Pre-save validatie: check alle 6 voorbeeld typen aanwezig
   REQUIRED_EXAMPLE_TYPES = {'sentence', 'practical', 'counter',
                              'synonyms', 'antonyms', 'explanation'}

   def validate_voorbeelden_complete(definitie_id: int) -> bool:
       present_types = get_voorbeeld_types(definitie_id)
       missing = REQUIRED_EXAMPLE_TYPES - present_types
       if missing:
           logger.warning(f"Definitie {definitie_id} mist: {missing}")
           return False
       return True
   ```

4. **Database Integrity Check** (TODO)
   - Pre-commit hook: check database niet in staging area
   - Startup check: verify database file timestamp > last commit
   - Alert bij onverwachte database resets

5. **Export Enhancement** (TODO)
   - Automatische export bij "Vaststellen" status
   - Versioned exports: `definitie_{id}_v{version}.txt`
   - Metadata tracking: laatst geëxporteerde versie

## 📈 Lessons Learned

### Do's ✅

1. **Export bestanden zijn goud waard** - TXT exports maakten recovery mogelijk
2. **Database uit git houden** - Voorkomt branch switch issues
3. **Gestructureerde recovery scripts** - Dry-run + verification essentieel
4. **Git reflog is je friend** - Precies kunnen traceren wat er gebeurde

### Don'ts ❌

1. **NOOIT binary data files in git** - Databases, images, etc. horen in .gitignore
2. **Niet aannemen dat backups compleet zijn** - Oude backup had zelfde probleem
3. **Geen silent partial regeneration** - Als voorbeelden verloren gaan, alert!

## 🔗 Related Issues

- **DEF-68:** Database tracking preventie (commit bbac2a71)
- **EPIC-016:** Auto-backup systeem (commit 82e6a256)
- **DEF-54:** Feature branch waar data loss begon

## 📝 Action Items

- [x] Database uit git tracking halen
- [x] Recovery script maken en uitvoeren
- [x] Verificatie van herstel
- [x] Documentatie van incident
- [ ] Voorbeelden compleetheid check implementeren
- [ ] Database integrity pre-commit hook
- [ ] Enhanced export systeem met versioning
- [ ] Monitoring dashboard voor data completeness

## 🔍 Verification Commands

```bash
# Check welke definities incomplete voorbeelden hebben
sqlite3 data/definities.db "
SELECT definitie_id, COUNT(DISTINCT voorbeeld_type) as types
FROM definitie_voorbeelden
WHERE actief = 1
GROUP BY definitie_id
HAVING types < 6;
"

# Recovery script uitvoeren
python3 scripts/recover_voorbeelden.py

# Verificatie na recovery
sqlite3 data/definities.db "
SELECT definitie_id, voorbeeld_type, COUNT(*) as cnt
FROM definitie_voorbeelden
WHERE definitie_id IN (79, 82, 83, 84, 85, 86, 87, 88, 90, 91)
AND actief = 1
GROUP BY definitie_id, voorbeeld_type
ORDER BY definitie_id, voorbeeld_type;
"
```

## 📚 References

- Recovery script: `scripts/recover_voorbeelden.py`
- Export bestanden: `exports/definities_export_20251029_*.txt`
- Git reflog: commits bbac2a71, 247af330, 82e6a256
- Database schema: `src/database/schema.sql` (definitie_voorbeelden tabel)
