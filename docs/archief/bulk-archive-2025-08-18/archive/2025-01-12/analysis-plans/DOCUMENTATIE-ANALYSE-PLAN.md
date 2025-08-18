# 📚 Documentatie Analyse & Opschoning Plan

**Doel**: Schoon schip maken voor de volgende fase door alle documentatie te reviewen
**Methode**: Per map/submap beoordelen op relevantie en volledigheid

## 🎯 Analyse Strategie

Voor elk document bepalen we:
1. **STATUS**: Keep / Archive / Delete / Update
2. **ACTIE**: Wat moet er gebeuren?
3. **MASTER-TODO**: Missen er items in MASTER-TODO.md?
4. **PRIORITEIT**: Hoog / Medium / Laag

## 📁 Map Structuur Analyse

### STAP 1: .bmad-core/ (BMAD Framework)
**Inhoud**: 80+ bestanden (agents, workflows, templates)
**Analyse focus**:
- [ ] Is BMAD nog relevant voor dit project?
- [ ] Gebruiken we de agents/workflows actief?
- [ ] Kunnen we deze map archiveren?

### STAP 2: docs/architecture/
**Inhoud**: ADRs, tech stack, coding standards
**Analyse focus**:
- [ ] Zijn alle ADRs nog actueel?
- [ ] Klopt de architectuur documentatie met de nieuwe services?
- [ ] Missen er architectuur beslissingen?

### STAP 3: docs/stories/
**Inhoud**: 7 EPICs + gearchiveerde stories
**Analyse focus**:
- [ ] Zijn EPICs gesynchroniseerd met MASTER-TODO?
- [ ] Kunnen gearchiveerde stories weg?
- [ ] Missen er acceptance criteria in MASTER-TODO?

### STAP 4: docs/testing/
**Inhoud**: Coverage reports, test strategies
**Analyse focus**:
- [ ] Zijn test rapporten actueel?
- [ ] Welke test documentatie is nog relevant?
- [ ] Missen er test requirements in MASTER-TODO?

### STAP 5: docs/ (root niveau)
**Inhoud**: Planning docs (backlog, roadmap, PRD, etc.)
**Analyse focus**:
- [ ] Welke planning docs zijn deprecated door MASTER-TODO?
- [ ] Wat moet gearchiveerd worden?
- [ ] Missen er items uit deze docs in MASTER-TODO?

### STAP 6: Overige mappen
- docs/development/
- docs/migration/
- docs/project-management/
- docs/setup/
- docs/technical/
- docs/daily-standups/

## 🔄 Werkwijze per Stap

### Voor elke map:
1. **Inventory**: Lijst alle bestanden
2. **Quick Scan**: Bepaal relevantie (1-5 schaal)
3. **Deep Dive**: Voor relevante docs (4-5)
4. **Extract**: Haal missende items voor MASTER-TODO
5. **Decide**: Keep/Archive/Delete
6. **Document**: Noteer beslissing + rationale

## 📊 Beslissingsmatrix

| Relevantie | Actie | Voorbeeld |
|------------|-------|-----------|
| 5 - Kritiek actueel | KEEP + Update indien nodig | Architectuur diagrammen |
| 4 - Belangrijk | KEEP + Review | Test strategy |
| 3 - Mogelijk nuttig | ARCHIVE | Oude ADRs |
| 2 - Weinig relevant | ARCHIVE | BMAD templates |
| 1 - Niet relevant | DELETE | Oude standups |

## 🗂️ Voorgestelde Nieuwe Structuur

```
docs/
├── active/           # Alleen actieve documentatie
│   ├── architecture/ # Actuele architectuur
│   ├── testing/      # Test requirements
│   └── setup/        # Setup guides
├── archive/          # Historische referentie
│   ├── planning/     # Oude roadmaps, backlogs
│   ├── bmad/         # BMAD framework
│   └── stories/      # Afgesloten epics
└── MASTER-TODO.md    # Single source of truth
```

## ⏱️ Tijdsinschatting

- **STAP 1 (.bmad-core)**: 30 minuten
- **STAP 2 (architecture)**: 45 minuten  
- **STAP 3 (stories)**: 30 minuten
- **STAP 4 (testing)**: 30 minuten
- **STAP 5 (root docs)**: 45 minuten
- **STAP 6 (overige)**: 30 minuten

**Totaal**: ~3.5 uur

## 🚀 Start

Begin met STAP 1 of kies een specifieke map om mee te starten.
Na elke stap documenteren we:
- Wat gevonden
- Wat toegevoegd aan MASTER-TODO
- Wat gearchiveerd/verwijderd

---
*Dit plan helpt ons systematisch door alle documentatie te gaan zonder iets te missen*