# 📚 Project Documentatie Analyse Plan (Zonder BMAD)

**Doel**: Analyseer alleen PROJECT-specifieke documentatie voor opschoning
**Scope**: docs/ folder (GEEN .bmad-core)
**Output**: Wat houden, archiveren, updaten + missende items voor MASTER-TODO

## 🎯 Documenten Overzicht

### 📁 docs/architecture/ (11 bestanden)
```
- 5 ADRs (Architecture Decision Records)
- complete-architecture-diagram.md
- tech-stack.md
- coding-standards.md
- dev-load-1/2/3.md (waarschuwingen)
- source-tree.md
```

### 📁 docs/stories/ (15 bestanden)
```
- 7 EPIC-XXX.md (actieve epics)
- 6 STORY-XXX.md in archive/ (oude mega-stories)
- README.md (overzicht)
```

### 📁 docs/testing/ (10 bestanden)
```
- coverage reports
- test-strategy.md
- integration test findings
- day1/day2 analyses
```

### 📁 docs/ root (15+ planning docs)
```
Kritieke documenten:
- MASTER-TODO.md ✅ (onze single source of truth)
- backlog.md (77+ items)
- roadmap.md (6-weken plan)
- prd.md (requirements)
- IMMEDIATE-ACTION-PLAN.md
- REFACTORING-ACTION-PLAN.md
- ARCHITECTURE_ANALYSIS.md
- ontologie-6-stappen.md
```

### 📁 Overige folders
```
- docs/technical/ (api, database, validation)
- docs/setup/ (quick-start, development)
- docs/development/ (ai-instructions)
- docs/migration/ (legacy-reference)
```

## 🔄 Analyse Aanpak Per Map

### STAP 1: docs/architecture/
**Prioriteit**: HOOG
**Focus vragen**:
1. Kloppen de 5 ADRs nog met huidige beslissingen?
2. Is het architectuur diagram bijgewerkt voor nieuwe services?
3. Zijn dev-load waarschuwingen verwerkt in MASTER-TODO?
4. Mist deployment/monitoring architectuur?

### STAP 2: docs/stories/
**Prioriteit**: MEDIUM
**Focus vragen**:
1. Alle EPIC stories in MASTER-TODO aanwezig?
2. Acceptance criteria compleet overgenomen?
3. Archive stories kunnen permanent weg?
4. Technical notes meegenomen?

### STAP 3: docs/testing/
**Prioriteit**: MEDIUM
**Focus vragen**:
1. Welke test docs zijn nog actueel?
2. Coverage reports up-to-date?
3. Test requirements in MASTER-TODO?
4. Integration test plan aanwezig?

### STAP 4: docs/ root planning
**Prioriteit**: HOOG
**Focus vragen**:
1. Welke docs zijn deprecated door MASTER-TODO?
2. Missen er items uit backlog.md (77+)?
3. Is ARCHITECTURE_ANALYSIS.md verwerkt?
4. Kan alles behalve MASTER-TODO gearchiveerd?

### STAP 5: Technical & Setup
**Prioriteit**: LAAG
**Focus vragen**:
1. API docs actueel met nieuwe services?
2. Database schema klopt nog?
3. Setup guides werkend?
4. 46 validatie regels gedocumenteerd?

## 📊 Beslissingsmatrix

| Document Type | Waarschijnlijke Actie | Reden |
|--------------|----------------------|--------|
| Planning docs | ARCHIVE | MASTER-TODO vervangt deze |
| EPICs | CHECK → ARCHIVE | Na sync met MASTER-TODO |
| ADRs | KEEP | Historische beslissingen |
| Architecture | UPDATE | Moet nieuwe services tonen |
| Test reports | SELECTIEF KEEP | Alleen recente/relevante |
| Setup guides | KEEP + UPDATE | Altijd nodig |

## 🚀 Start Volgorde

**Voorgesteld**:
1. **EERST**: docs/ root - grootste impact, meeste overlap
2. **DAN**: architecture/ - technische correctheid
3. **DAARNA**: stories/ - completeness check
4. **TOT SLOT**: testing/ & overige

## ⏱️ Tijdsinschatting
- Root docs analyse: 45 min
- Architecture: 30 min
- Stories check: 30 min
- Testing: 20 min
- Overige: 15 min

**Totaal**: ~2.5 uur

---
Waar wil je mee beginnen?