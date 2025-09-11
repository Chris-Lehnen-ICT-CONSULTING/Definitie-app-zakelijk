# 🚀 EPIC-STORY MIGRATIE - UITVOERINGSPLAN

**Type:** Stap-voor-stap Executie Plan
**Status:** KLAAR TO EXECUTE
**Geschatte Tijd:** 8-12 uur werk
**Prioriteit:** KRITIEK

---

## 📋 EXACT PLAN - WAT GAAN WE DOEN?

### Het Probleem
- **10 epics** in MASTER document
- **7 EPIC-XXX files** in archief (andere nummering)
- **9 epics** in COMPLETE-EPIC-OVERVIEW (andere statussen)
- **47+ stories** verspreid over 30+ losse files
- **Geen enkele betrouwbare bron van waarheid**

### De Oplossing
1. **MASTER-EPICS-USER-STORIES.md blijft leidend** (is meest recent)
2. **Reconcilieer alle epics** naar één consistent systeem
3. **Migreer naar individuele files** per epic/story
4. **Archiveer duplicaten** naar `/docs/archief/2025-09-epic-migration/`

---

## ✅ STAP 1: RECONCILIATIE (30 minuten)

### Wat gaan we doen:
Alle epics uit verschillende bronnen samenvoegen naar één waarheid.

### Episch Verhaal Reconciliatie Tabel:

| Master Episch Verhaal | Archief EPIC-XXX | COMPLETE-EPIC Status | BESLUIT | Nieuwe ID |
|-------------|------------------|---------------------|---------|-----------|
| Episch Verhaal 1: Basis Definitie | - | ✅ 90% | BEHOUDEN | EPIC-001 |
| Episch Verhaal 2: Kwaliteitstoetsing | - | ✅ 85% | BEHOUDEN | EPIC-002 |
| Episch Verhaal 3: Content/Web Lookup | EPIC-004 (overlap) | 🔄 30% | MERGE | EPIC-003 |
| Episch Verhaal 4: User Interface | EPIC-005 (overlap) | ❌ 30% | MERGE | EPIC-004 |
| Episch Verhaal 5: Export & Import | - | ❌ 10% | BEHOUDEN | EPIC-005 |
| Episch Verhaal 6: Beveiliging & Auth | - | 🚨 0% | BEHOUDEN | EPIC-006 |
| Episch Verhaal 7: Prestaties | - | 🔄 20% | BEHOUDEN | EPIC-007 |
| Episch Verhaal 8: (merged → Episch Verhaal 3) | EPIC-002 | Merged | SKIP | - |
| Episch Verhaal 9: Advanced Features | - | ❌ 5% | BEHOUDEN | EPIC-009 |
| Episch Verhaal CFR: Context Flow | - | - | BEHOUDEN | EPIC-010 |
| - | EPIC-001: Database | - | TOEVOEGEN | EPIC-011 |
| - | EPIC-003: UI Quick | - | MERGE → 4 | - |
| - | EPIC-006: Prompt Opt | - | TOEVOEGEN | EPIC-012 |
| - | EPIC-007: Test Suite | - | TOEVOEGEN | EPIC-013 |

**Resultaat: 13 definitieve epics**

### Commando's:
```bash
# Maak reconciliatie rapport
echo "# Episch Verhaal Reconciliatie Rapport - $(date)" > reconciliation.md
echo "Van 10+7+9 bronnen naar 13 definitieve epics" >> reconciliation.md
```

---

## ✅ STAP 2: BACKUP & SETUP (15 minuten)

### Wat gaan we doen:
Volledige backup maken en nieuwe directory structuur opzetten.

### Commando's:
```bash
# 1. Volledige backup
cp -r docs/ docs-backup-$(date +%Y%m%d-%H%M%S)/

# 2. Maak nieuwe structuur
mkdir -p docs/epics
mkdir -p docs/stories
mkdir -p docs/backlog
mkdir -p docs/sprints
mkdir -p docs/archief/2025-09-epic-migration

# 3. Verificatie
ls -la docs/ | grep -E "epics|stories|backlog|sprints"
```

---

## ✅ STAP 3: EPIC EXTRACTIE (2 uur)

### Wat gaan we doen:
Voor elk van de 13 epics een individueel bestand maken.

### Voor elke epic:

#### A. Extract uit MASTER document:
```bash
# Script: extract_epic.py
python scripts/extract_epic.py \
  --source docs/backlog/stories/MASTER-EPICS-USER-STORIES.md \
  --epic-id "Episch Verhaal 1" \
  --output docs/backlog/EPIC-001/EPIC-001.md
```

#### B. Episch Verhaal Template:
```markdown
---
id: EPIC-001
title: Basis Definitie Generatie
status: GEREED
priority: HOOG
owner: development
created: 01-01-2025
updated: 05-09-2025
completion: 100%
stories: [US-001, US-002, US-003, US-004, US-005]
vereistes: [REQ-001, REQ-002, REQ-003]
astra_compliance: true
---

# EPIC-001: Basis Definitie Generatie

## Beschrijving
[Kopieer uit MASTER]

## Bedrijfswaarde
[Kopieer uit MASTER]

## Acceptatiecriteria
[Kopieer uit MASTER]

## Stories
[Link naar story files]

## Afhankelijkheden
[Uit analysis]

## Status Updates
[Historie]
```

#### C. Merge archief content:
```bash
# Voor epics met archief equivalent
python scripts/merge_epic_content.py \
  --primary docs/backlog/EPIC-003/EPIC-003.md \
  --archive docs/archief/vereistes/EPIC-004-content-enrichment.md \
  --output docs/backlog/EPIC-003/EPIC-003.md
```

---

## ✅ STAP 4: STORY MIGRATIE (3 uur)

### Wat gaan we doen:
47+ stories uit MASTER extracten naar individuele US-XXX.md files.

### Story Nummering Conversie:
| Oud Format | Nieuw Format | File |
|------------|--------------|------|
| Story 1.1 | US-001 | docs/backlog/stories/US-001.md |
| Story 1.2 | US-002 | docs/backlog/stories/US-002.md |
| Story 2.1 | US-006 | docs/backlog/stories/US-006.md |
| ... | ... | ... |

### Script Executie:
```bash
# Extract alle stories
python scripts/extract_all_stories.py \
  --source docs/backlog/stories/MASTER-EPICS-USER-STORIES.md \
  --output-dir docs/backlog/stories/ \
  --format US-XXX

# Output:
# Created: docs/backlog/stories/US-001.md (Episch Verhaal 1, Story 1.1)
# Created: docs/backlog/stories/US-002.md (Episch Verhaal 1, Story 1.2)
# ...
```

---

## ✅ STAP 5: DUPLICATEN ARCHIVEREN (1 uur)

### Wat gaan we doen:
Alle oude/duplicate files naar archief verplaatsen.

### Commando's:
```bash
# 1. Verplaats duplicate epic files
mv docs/backlog/stories/epic-*.md docs/archief/2025-09-epic-migration/

# 2. Verplaats oude story files
mv docs/backlog/stories/story-*.md docs/archief/2025-09-epic-migration/

# 3. Document wat gearchiveerd is
ls docs/archief/2025-09-epic-migration/ > archived-files.txt
```

---

## ✅ STAP 6: INDEX GENERATIE (30 minuten)

### Wat gaan we doen:
Automatische INDEX.md files genereren voor overzicht.

### Episch Verhaal INDEX (`docs/backlog/epics/INDEX.md`):
```bash
python scripts/generate_epic_index.py \
  --input-dir docs/backlog/epics/ \
  --output docs/backlog/epics/INDEX.md
```

### Story INDEX (`docs/backlog/stories/INDEX.md`):
```bash
python scripts/generate_story_index.py \
  --input-dir docs/backlog/stories/ \
  --output docs/backlog/stories/INDEX.md
```

---

## ✅ STAP 7: VALIDATIE (1 uur)

### Wat gaan we doen:
Controleren dat niets verloren is gegaan.

### Validatie Checks:
```bash
# 1. Tel epics
echo "Epische Verhalen in nieuwe structuur:"
ls docs/backlog/epics/EPIC-*.md | wc -l  # Moet 13 zijn

# 2. Tel stories
echo "Stories in nieuwe structuur:"
ls docs/backlog/stories/US-*.md | wc -l  # Moet 47+ zijn

# 3. Check links
python scripts/validate_links.py docs/backlog/epics/ docs/backlog/stories/

# 4. Check frontmatter
python scripts/validate_frontmatter.py docs/backlog/epics/ docs/backlog/stories/

# 5. Genereer rapport
python scripts/migration_report.py > migration-report.md
```

---

## ✅ STAP 8: MASTER ARCHIVEREN (15 minuten)

### Wat gaan we doen:
MASTER document archiveren (niet verwijderen!).

### Commando's:
```bash
# 1. Kopieer naar archief met datum
cp docs/backlog/stories/MASTER-EPICS-USER-STORIES.md \
   docs/archief/2025-09-epic-migration/MASTER-EPICS-USER-STORIES-$(date +%Y%m%d).md

# 2. Update MASTER met verwijzing
cat > docs/backlog/stories/MASTER-EPICS-USER-STORIES.md << 'EOF'
# MASTER EPICS & USER STORIES

⚠️ **DEPRECATED**: Dit document is gemigreerd naar individuele bestanden.

## Nieuwe Locaties:
- **Epische Verhalen**: `/docs/backlog/epics/EPIC-XXX.md`
- **Stories**: `/docs/backlog/stories/US-XXX.md`
- **Dashboard**: `/docs/backlog/epics/INDEX.md`

## Archief:
Originele versie: `/docs/archief/2025-09-epic-migration/MASTER-EPICS-USER-STORIES-20250905.md`

---
*Gemigreerd op: 05-09-2025*
EOF
```

---

## ✅ STAP 9: TEAM COMMUNICATIE (30 minuten)

### Wat gaan we doen:
Team informeren over nieuwe structuur.

### Acties:
1. **Stuur announcement**:
```markdown
Subject: Episch Verhaal/Story Documentatie Gemigreerd

Team,

De epic/story documentatie is gemigreerd naar een nieuwe structuur:

OUDE locatie:
- docs/backlog/stories/MASTER-EPICS-USER-STORIES.md (monoliet)

NIEUWE locaties:
- docs/backlog/epics/EPIC-XXX.md (13 epic files)
- docs/backlog/stories/US-XXX.md (47 story files)
- docs/backlog/epics/INDEX.md (dashboard)

Voordelen:
✅ Geen merge conflicts meer
✅ Betere traceability
✅ ASTRA/NORA compliant
✅ Individuele file ownership

Archief van oude structuur: docs/archief/2025-09-epic-migration/
```

2. **Update documentatie**:
- README.md
- CONTRIBUTING.md
- docs/INDEX.md

---

## ✅ STAP 10: CI/CD SETUP (1 uur)

### Wat gaan we doen:
Automation toevoegen voor kwaliteit.

### GitHub Actions:
```yaml
# .github/workflows/epic-validation.yml
name: Episch Verhaal/Story Validation

on:
  pull_request:
    paths:
      - 'docs/backlog/epics/*.md'
      - 'docs/backlog/stories/*.md'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Validate Frontmatter
        run: python scripts/validate_frontmatter.py

      - name: Check Links
        run: python scripts/validate_links.py

      - name: Update INDEX
        run: |
          python scripts/generate_epic_index.py
          python scripts/generate_story_index.py
```

---

## 📊 SUCCES CRITERIA

Na voltooiing moet je hebben:

✅ **13 epic files** in `/docs/backlog/epics/EPIC-XXX.md`
✅ **47+ story files** in `/docs/backlog/stories/US-XXX.md`
✅ **2 INDEX files** voor dashboards
✅ **0 duplicaten** in actieve directories
✅ **100% frontmatter** compliance
✅ **Archief** met alle oude versies
✅ **Team geïnformeerd** via announcement
✅ **CI/CD validatie** actief

---

## 🚨 ROLLBACK PLAN

Als er iets fout gaat:

```bash
# 1. Stop alle wijzigingen
git stash

# 2. Restore backup
rm -rf docs/
cp -r docs-backup-[timestamp]/ docs/

# 3. Commit restore
git add docs/
git commit -m "ROLLBACK: Restore pre-migration state"

# 4. Informeer team
echo "Migration rolled back due to: [REASON]"
```

---

## ⏱️ TIJDLIJN

| Fase | Tijd | Status |
|------|------|--------|
| Stap 1: Reconciliatie | 30 min | ⏳ |
| Stap 2: Backup & Setup | 15 min | ⏳ |
| Stap 3: Episch Verhaal Extractie | 2 uur | ⏳ |
| Stap 4: Story Migratie | 3 uur | ⏳ |
| Stap 5: Archivering | 1 uur | ⏳ |
| Stap 6: INDEX Generatie | 30 min | ⏳ |
| Stap 7: Validatie | 1 uur | ⏳ |
| Stap 8: Master Archief | 15 min | ⏳ |
| Stap 9: Communicatie | 30 min | ⏳ |
| Stap 10: CI/CD | 1 uur | ⏳ |
| **TOTAAL** | **10 uur** | |

---

*Dit plan is klaar voor executie. Begin met Stap 1: Reconciliatie.*
