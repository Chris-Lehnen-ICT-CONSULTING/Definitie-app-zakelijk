# 🇳🇱 Workflow: Project Bestandsnamen Vernederlandsing

## 🎯 Doel
Alle project bestanden systematisch hernoemen naar Nederlandse namen, inclusief het aanpassen van alle code referenties, imports, en documentatie verwijzingen.

## ⚠️ Waarschuwing
Dit is een **zeer impactvolle operatie** die het hele project raakt. Een grondige voorbereiding en stapsgewijze aanpak is essentieel.

## 📊 Impact Analyse

### Geschatte Omvang:
- **~150+ Python bestanden** om te hernoemen
- **~2000+ import statements** aan te passen
- **~500+ functie/class referenties** te updaten
- **Alle test bestanden** moeten mee veranderen
- **Configuratie bestanden** aanpassen
- **Documentatie links** updaten

## 📖 Vertaal Woordenboek

### Core Services
```
definition_service → definitie_service
web_lookup_service → web_opzoek_service
validation_service → validatie_service
cache_service → cache_service (blijft)
config_manager → configuratie_beheerder
orchestration → orkestratie
```

### UI Componenten
```
definition_generator_tab → definitie_generator_tab
web_lookup_tab → web_opzoek_tab
history_tab → geschiedenis_tab
expert_review_tab → expert_beoordeling_tab
toetsregels_tab → toetsregels_tab (al Nederlands)
admin_tab → beheer_tab
```

### Utilities
```
file_utils → bestand_hulpmiddelen
text_utils → tekst_hulpmiddelen
validation_utils → validatie_hulpmiddelen
logger → logger (blijft)
decorators → decorateurs
```

### Models
```
definition_model → definitie_model
validation_result → validatie_resultaat
cache_entry → cache_item
```

## 🔄 Workflow Fases

### Fase 1: Voorbereiding & Inventarisatie
**Duur:** 2-3 uur

1. **Volledige Backup**
   ```bash
   # Maak volledige project backup
   cp -r /pad/naar/project /pad/naar/backup-$(date +%Y%m%d-%H%M%S)
   git add -A && git commit -m "backup: voor grote hernoeming operatie"
   git tag backup-voor-vernederlandsing
   ```

2. **Dependency Mapping**
   ```bash
   # Genereer dependency graaf
   python scripts/analyse/dependency_mapper.py > afhankelijkheden.json
   ```

3. **Import Analyse**
   ```bash
   # Vind alle imports
   rg "^from|^import" --type py > alle-imports.txt
   ```

### Fase 2: Test Suite Voorbereiding
**Duur:** 1-2 uur

```bash
# Zorg dat alle tests werken VOOR de migratie
pytest --tb=short > test-resultaten-voor.txt

# Als tests falen, fix deze eerst!
```

### Fase 3: Geautomatiseerde Hernoeming Script
**Duur:** 4-6 uur ontwikkeling

```python
# scripts/hernoem-naar-nederlands.py

import os
import re
from pathlib import Path
import json
import shutil

class ProjectVernederlandser:
    def __init__(self):
        self.vertaal_dict = {
            # Services
            "definition_service": "definitie_service",
            "web_lookup_service": "web_opzoek_service",
            "validation_service": "validatie_service",
            "cache_service": "cache_service",
            "config_manager": "configuratie_beheerder",

            # Functies
            "generate_definition": "genereer_definitie",
            "validate_input": "valideer_invoer",
            "get_results": "krijg_resultaten",
            "save_to_cache": "bewaar_in_cache",

            # UI
            "definition_generator": "definitie_generator",
            "web_lookup": "web_opzoek",
            "history": "geschiedenis",
            "expert_review": "expert_beoordeling",

            # Utils
            "file_utils": "bestand_hulpmiddelen",
            "text_utils": "tekst_hulpmiddelen",
            "validation_utils": "validatie_hulpmiddelen"
        }

        self.import_replacements = []
        self.file_renames = []

    def analyseer_project(self):
        """Analyseer alle bestanden die hernoemd moeten worden"""
        pass

    def genereer_migratie_plan(self):
        """Maak gedetailleerd plan voor elke wijziging"""
        pass

    def voer_hernoeming_uit(self, dry_run=True):
        """Voer daadwerkelijke hernoeming uit"""
        pass

    def update_imports(self):
        """Update alle import statements"""
        pass

    def valideer_resultaat(self):
        """Controleer of alles nog werkt"""
        pass
```

### Fase 4: Stapsgewijze Migratie per Module
**Duur:** 2-3 dagen

#### Stap 1: Core Services (Dag 1)
```bash
# Begin met minst afhankelijke modules
python scripts/hernoem-naar-nederlands.py --module services/cache --dry-run
python scripts/hernoem-naar-nederlands.py --module services/cache --execute

# Test na elke module
pytest tests/services/test_cache_service.py
```

#### Stap 2: Utilities (Dag 1)
```bash
python scripts/hernoem-naar-nederlands.py --module utils --execute
pytest tests/utils/
```

#### Stap 3: Models & Config (Dag 2)
```bash
python scripts/hernoem-naar-nederlands.py --module models --execute
python scripts/hernoem-naar-nederlands.py --module config --execute
pytest tests/models/ tests/config/
```

#### Stap 4: UI Componenten (Dag 2)
```bash
python scripts/hernoem-naar-nederlands.py --module ui --execute
# Manual UI testing nodig
```

#### Stap 5: Orchestration & Main (Dag 3)
```bash
python scripts/hernoem-naar-nederlands.py --module orchestration --execute
python scripts/hernoem-naar-nederlands.py --module main --execute
```

### Fase 5: Post-Migratie Validatie
**Duur:** 3-4 uur

1. **Alle Tests Draaien**
   ```bash
   pytest --tb=short > test-resultaten-na.txt
   diff test-resultaten-voor.txt test-resultaten-na.txt
   ```

2. **Import Validatie**
   ```bash
   python -m py_compile **/*.py  # Syntax check
   mypy src/  # Type checking
   ```

3. **Documentatie Updates**
   ```bash
   # Update alle .md bestanden met nieuwe bestandsnamen
   python scripts/update-documentatie-links.py
   ```

4. **UI Testing**
   ```bash
   streamlit run src/main.py
   # Test elke tab handmatig
   ```

### Fase 6: Configuratie & Deployment Updates
**Duur:** 1-2 uur

1. **Update configuratie bestanden**
   - `.env` aanpassen
   - `pyproject.toml` module namen
   - GitHub Actions workflows
   - Docker bestanden (indien aanwezig)

2. **Update deployment scripts**
   ```bash
   # Pas alle scripts aan die modules referen
   grep -r "definition_service" scripts/ | update
   ```

## 🚨 Rollback Plan

Als iets mis gaat:

```bash
# Optie 1: Git rollback
git reset --hard backup-voor-vernederlandsing

# Optie 2: Restore van backup
rm -rf /huidige/project
cp -r /backup/project /huidige/project

# Optie 3: Stapsgewijze revert
git revert HEAD~5..HEAD  # Revert laatste 5 commits
```

## 📋 Checklist per Module

- [ ] Backup gemaakt
- [ ] Tests werken voor migratie
- [ ] Dry-run uitgevoerd
- [ ] Bestanden hernoemd
- [ ] Imports aangepast
- [ ] Functie/class namen aangepast
- [ ] Tests werken na migratie
- [ ] Documentatie bijgewerkt
- [ ] Code review uitgevoerd

## 🔧 Hulp Scripts

### 1. Vind alle referenties
```bash
#!/bin/bash
# scripts/vind-referenties.sh
ZOEKTERM=$1
echo "=== Bestanden ==="
find . -name "*${ZOEKTERM}*" -type f | grep -v __pycache__
echo -e "\n=== In Code ==="
rg "$ZOEKTERM" --type py
echo -e "\n=== In Imports ==="
rg "from.*$ZOEKTERM|import.*$ZOEKTERM" --type py
```

### 2. Vervang in alle bestanden
```python
# scripts/vervang-overal.py
import fileinput
import sys

oud = sys.argv[1]
nieuw = sys.argv[2]

for line in fileinput.input(sys.argv[3:], inplace=True):
    print(line.replace(oud, nieuw), end='')
```

## ⏱️ Geschatte Tijdlijn

- **Dag 0**: Voorbereiding, backup, analyse (3-4 uur)
- **Dag 1**: Script ontwikkeling, test runs (6-8 uur)
- **Dag 2-4**: Module-voor-module migratie (4-6 uur per dag)
- **Dag 5**: Validatie, documentatie, afronding (4-5 uur)

**Totaal**: ~25-35 uur werk

## 💡 Tips

1. **Doe dit NIET op vrijdag** - Je wilt tijd hebben voor fixes
2. **Werk in kleine batches** - Niet alles tegelijk
3. **Test obsessief** - Na elke wijziging
4. **Commit vaak** - Kleine, reverteerbare commits
5. **Documenteer alles** - Wat je wijzigt en waarom
6. **Vraag Claude Code** - Bij elke twijfel over vertalingen

---
*Workflow aangemaakt: 2025-01-27*
