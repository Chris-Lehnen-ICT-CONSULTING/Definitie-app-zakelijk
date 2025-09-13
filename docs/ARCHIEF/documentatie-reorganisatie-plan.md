# 📋 Plan: Documentatie Reorganisatie DefinitieAgent

**Aangemaakt**: 2025-08-19
**Bijgewerkt**: 2025-08-21
**Status**: Te Implementeren
**Prioriteit**: Medium

## 🎯 Doel
Requirements en architectuur documentatie scheiden voor betere onderhoudbaarheid en duidelijkheid.

## 📊 Huidige Situatie (BIJGEWERKT)
```
docs/
├── REQUIREMENTS_AND_FEATURES_COMPLETE.md (87 features, actueel)
├── archief/
│   └── requirements/
│       └── prd.md (verouderd, bevat architectuur)
├── architectuur/
│   ├── README.md (bestaat al met uitgebreide inhoud)
│   ├── _archive/2025-08-20-reorganization/
│   │   └── ARCHITECTURE_VISUALIZATION_DETAILED.html
│   └── [enterprise/solution/governance docs]
└── brownfield-architecture.md (BESTAAT NIET - moet verwijderd worden uit README)
```

## 🔄 Voorgestelde Reorganisatie

### Stap 1: PRD Archivering
```bash
# Markeer als verouderd in docs/archief/requirements/prd.md:
# "⚠️ VEROUDERD DOCUMENT - Gebruik REQUIREMENTS_AND_FEATURES_COMPLETE.md"
# Behoud locatie in archief voor historische referentie
```

### Stap 2: Requirements Document Opschonen
- Verifieer dat `REQUIREMENTS_AND_FEATURES_COMPLETE.md` geen architectuur details bevat
- Voeg sectie toe: "Voor technische implementatie zie `/docs/architectuur/`"
- Fix: gebruik UPPERCASE versie overal (niet lowercase)

### Stap 3: README.md Fixes
Verwijder/update deze onjuiste verwijzingen:
- `brownfield-architecture.md` → BESTAAT NIET, verwijderen
- `requirements_and_features_complete.md` → `REQUIREMENTS_AND_FEATURES_COMPLETE.md`
- `ARCHITECTURE_VISUALIZATION_DETAILED.html` → pad updaten naar archief locatie

### Stap 4: README.md Update
Update hoofdstukken in README.md:

```markdown
## 📚 Documentatie

### Requirements & Features
- **Complete Requirements & Features** - Alle user stories, epics en feature status
  - 87 features gedefinieerd
  - 9 epics met acceptance criteria
  - Real-time status tracking

### Technische Architectuur
- **[Architectuur Overzicht](../architectuur/README.md)** - Index van alle architectuur documentatie
- **[Enterprise Architecture](../architectuur/ENTERPRISE_ARCHITECTURE.md)** - Business & strategie
- **[Solution Architecture](../architectuur/SOLUTION_ARCHITECTURE.md)** - Technische implementatie
- **Legacy Migratie** - 10-weken migratie roadmap

### Quick Links
- 🎯 Wat moet er nog gebeuren? - 60% features nog niet gestart
- 🔒 Security Requirements - KRITIEK: 0% geïmplementeerd
- 🚀 Roadmap - 4 fasen implementatie plan
```

### Stap 5: Andere Referentie Updates
- `.bmad-core/` → Update story templates met juiste doc verwijzingen
- Verwijder alle verwijzingen naar niet-bestaande `brownfield-architecture.md`

## 📁 Eindresultaat Structuur
```
/
├── README.md ← Bijgewerkt met correcte verwijzingen
├── docs/
│   ├── REQUIREMENTS_AND_FEATURES_COMPLETE.md ← SINGLE SOURCE voor requirements
│   ├── LEGACY_CODE_MIGRATION_ROADMAP.md
│   ├── architectuur/
│   │   ├── README.md ← BESTAAT AL met goede inhoud
│   │   ├── ENTERPRISE_ARCHITECTURE.md
│   │   ├── SOLUTION_ARCHITECTURE.md
│   │   ├── PRODUCT_DELIVERY_TRACKER.md
│   │   ├── ARCHITECTURE_GOVERNANCE.md
│   │   └── _archive/
│   │       └── 2025-08-20-reorganization/
│   └── archief/
│       └── requirements/
│           └── prd.md ← Met deprecation notice
```

## ✅ Verificatie Checklist
- [ ] README.md verwijst naar juiste documenten
- [ ] Geen requirements duplicatie tussen documenten
- [ ] Geen architectuur info in requirements doc
- [ ] Alle architectuur info geconsolideerd
- [ ] Cross-references correct
- [ ] Team geïnformeerd over nieuwe structuur

## 🚀 Impact
- **Nieuwe teamleden**: Vinden direct de juiste docs via README
- **Developers**: Kijken in `/architectuur/` voor technische details
- **Product Owners**: Gebruiken `requirements_and_features_complete.md`
- **Iedereen**: README.md als startpunt voor navigatie

## 📅 Implementatie
Dit plan moet worden uitgevoerd door iemand met toegang tot de documentatie bestanden. Alle stappen zijn non-destructief en bewaren bestaande informatie.
