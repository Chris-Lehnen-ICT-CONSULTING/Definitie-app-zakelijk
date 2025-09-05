---
canonical: true
status: active
owner: architecture
last_verified: 2025-09-04
applies_to: definitie-app@v2
document_type: workflow
---

# 📝 Document Creation & Management Workflow

Dit document beschrijft de **verplichte workflow** voor het maken, updaten en archiveren van documenten in het DefinitieAgent project.

---

## 🚨 GOLDEN RULE: Check Before Create

**NOOIT** direct een nieuw document maken. **ALTIJD** eerst checken of het al bestaat!

---

## 📋 Document Creation Workflow

### STAP 1: 🔍 Search for Existing Content
```bash
# Zoek in alle docs naar je onderwerp
grep -r "jouw onderwerp" docs/

# Zoek naar bestandsnamen
ls docs/**/*relevante-term*.md

# Check specifieke directories
ls docs/stories/*.md
ls docs/architectuur/*.md
```

### STAP 2: 📚 Check Master Documents
```bash
# Check het MASTER epics document
cat docs/stories/MASTER-EPICS-USER-STORIES.md | grep "jouw onderwerp"

# Check de documentatie index
cat docs/INDEX.md | grep "jouw onderwerp"

# Check canonieke locaties
cat docs/CANONICAL_LOCATIONS.md
```

### STAP 3: 🗂️ Check Archive
```bash
# Check of het in het archief staat
ls docs/archief/
ls docs/archief/stories/
ls docs/archief/architecture/
```

### STAP 4: ✅ Decision Tree

```
Document gevonden?
├── JA → UPDATE het bestaande document
│   ├── Check `last_verified` datum
│   ├── Update content
│   └── Update frontmatter
│
└── NEE → Mag je het maken?
    ├── Is het een epic/story? → NEIN! Update MASTER-EPICS-USER-STORIES.md
    ├── Is het een duplicate? → NEIN! Update het origineel
    └── Echt nieuw? → Ga naar STAP 5
```

### STAP 5: 📁 Create in Correct Location

**Check eerst:** `docs/CANONICAL_LOCATIONS.md`

| Type Document | Locatie |
|--------------|---------|
| Epics & Stories | `docs/stories/MASTER-EPICS-USER-STORIES.md` (UPDATE ONLY) |
| Architecture (EA/SA/TA) | `docs/architectuur/` |
| ADRs | `Geïntegreerd in EA/SA/TA docs` |
| Module docs | `docs/technische-referentie/modules/` |
| Reviews | `docs/reviews/` |
| Requirements | `docs/requirements/` |
| Test docs | `docs/testing/` |

### STAP 6: ✍️ Add Required Frontmatter

```yaml
---
canonical: true           # Is dit DE bron voor dit onderwerp?
status: active           # active/draft/archived
owner: development       # architecture/validation/platform/product/domain
last_verified: 2025-09-04  # YYYY-MM-DD
applies_to: definitie-app@v2  # Scope/versie
document_type: guide     # epic/story/adr/guide/analysis/etc.
---
```

### STAP 7: 🔗 Update References

- [ ] Update `docs/INDEX.md` met link naar nieuw document
- [ ] Update relevante master documenten
- [ ] Add cross-references waar nodig
- [ ] Check dat alle links werken

---

## 📦 Archiving Workflow

### GEBRUIK ALLEEN `/docs/archief/`

```bash
# GOED ✅
mv docs/stories/old-story.md docs/archief/stories/

# FOUT ❌
mkdir docs/archive  # NOOIT!
mkdir docs/old      # NOOIT!
mkdir docs/archief2 # NOOIT!
```

### Archive Structuur
```
docs/archief/
├── stories/        # Oude epics en stories
├── architecture/   # Oude architectuur docs
├── requirements/   # Oude requirements
├── REFERENTIE/    # Referentie materiaal
└── HISTORISCH/    # Historische docs
```

---

## 🚫 Common Mistakes to Avoid

### ❌ DEZE FOUTEN MAKEN ROMMEL:

1. **Nieuwe epic/story document maken**
   - FOUT: `docs/stories/epic-8-new-feature.md`
   - GOED: Update `docs/stories/MASTER-EPICS-USER-STORIES.md`

2. **Archive map maken**
   - FOUT: `mkdir docs/archive` of `docs/old`
   - GOED: Gebruik `/docs/archief/`

3. **Duplicate met andere naam**
   - FOUT: `validation-v2.md` naast `validation-orchestrator.md`
   - GOED: Update het origineel of archiveer oude versie

4. **Geen frontmatter**
   - FOUT: Document zonder metadata
   - GOED: Altijd frontmatter toevoegen

5. **Verkeerde locatie**
   - FOUT: Story in `/docs/` root
   - GOED: Check `CANONICAL_LOCATIONS.md`

---

## ✅ Best Practices

### Document Hygiene
- 🔍 **Search First**: Altijd zoeken voor maken
- 📝 **Update > Create**: Liever updaten dan nieuw maken
- 📁 **Right Location**: Gebruik canonieke locaties
- 🏷️ **Metadata**: Altijd frontmatter toevoegen
- 🔗 **Link It**: Update INDEX.md en cross-references
- 🗓️ **Date It**: `last_verified` bijhouden
- 📦 **Archive Smart**: Alleen `/docs/archief/` gebruiken

### Voor AI/Claude
```bash
# Deze commands ALTIJD uitvoeren voor document creatie:
grep -r "onderwerp" docs/
cat docs/stories/MASTER-EPICS-USER-STORIES.md | grep "onderwerp"
cat docs/INDEX.md | grep "onderwerp"
cat docs/CANONICAL_LOCATIONS.md
ls docs/archief/
```

---

## 📊 Quick Reference Card

| Actie | Command |
|-------|---------|
| Search content | `grep -r "term" docs/` |
| Search filenames | `ls docs/**/*term*.md` |
| Check master | `cat docs/stories/MASTER-EPICS-USER-STORIES.md` |
| Check index | `cat docs/INDEX.md` |
| Check locations | `cat docs/CANONICAL_LOCATIONS.md` |
| Archive properly | `mv file.md docs/archief/category/` |
| Never do | `mkdir docs/archive` ❌ |

---

## 🔧 Enforcement

### Git Pre-commit Hooks (Suggested)
```bash
#!/bin/bash
# Check for duplicate documents
# Check for docs outside canonical locations
# Check for missing frontmatter
# Warn about new epic/story files
```

### CI/CD Checks
- Detect multiple `canonical: true` for same topic
- Warn if creating outside canonical locations
- Block new archive/old directories
- Check frontmatter completeness

---

**Remember**: Een clean project begint met discipline. Check eerst, maak later!
