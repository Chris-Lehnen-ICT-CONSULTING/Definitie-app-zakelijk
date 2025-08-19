# DefinitieAgent Module Overzicht

## 📚 Module Documentatie

Deze directory bevat gedetailleerde analyses van alle modules in het DefinitieAgent systeem.

### 🏗️ Architectuur Overzicht

```
UI Layer (Streamlit)
    ↓
Integration Layer (Duplicate Check & Workflow)
    ↓
Orchestration Layer (Iterative Improvement)
    ↓
Core Services (Generation, Validation, Web Lookup)
    ↓
Data Layer (Database, Cache, File Storage)
```

### 📁 Module Analyses

| Module | Bestand | Status | Beschrijving |
|--------|---------|---------|--------------|
| **AI Toetser** | [AI_TOETSER_MODULE_ANALYSIS.md](./AI_TOETSER_MODULE_ANALYSIS.md) | ✅ Actueel | Modulaire toetsing engine met 46 validators |
| **Config** | [CONFIG_MODULE_ANALYSIS.md](./CONFIG_MODULE_ANALYSIS.md) | ✅ Actueel | Configuratie management en toetsregels |
| **Database** | [DATABASE_MODULE_ANALYSIS.md](./DATABASE_MODULE_ANALYSIS.md) | ✅ Actueel | SQLite repository voor definities |
| **Generation** | [GENERATION_MODULE_ANALYSIS.md](./GENERATION_MODULE_ANALYSIS.md) | ✅ Actueel | AI-powered definitie generatie |
| **Orchestration** | [ORCHESTRATION_MODULE_ANALYSIS.md](./ORCHESTRATION_MODULE_ANALYSIS.md) | ✅ Actueel | Iteratieve verbetering workflow |
| **Services** | [SERVICES_MODULE_ANALYSIS.md](./SERVICES_MODULE_ANALYSIS.md) | ✅ Actueel | Unified service layer |
| **UI** | [UI_MODULE_ANALYSIS.md](./UI_MODULE_ANALYSIS.md) | ✅ Actueel | Streamlit user interface |
| **Utils** | [UTILS_MODULE_ANALYSIS.md](./UTILS_MODULE_ANALYSIS.md) | ✅ Actueel | Hulp utilities |
| **Validation** | [VALIDATION_MODULE_ANALYSIS.md](./VALIDATION_MODULE_ANALYSIS.md) | ✅ Actueel | Definitie validatie |
| **Voorbeelden** | [VOORBEELDEN_MODULE_ANALYSIS.md](./VOORBEELDEN_MODULE_ANALYSIS.md) | ✅ Actueel | Voorbeeld generatie |
| **Web Lookup** | [WEB_LOOKUP_MODULE_ANALYSIS.md](./WEB_LOOKUP_MODULE_ANALYSIS.md) | ✅ Actueel | Web zoekfunctionaliteit |

### 🔄 Generatie Flow

1. **Gebruiker invoer** → UI (`tabbed_interface.py`)
   - Context selectie
   - Begrip invoeren
   - "🚀 Genereer Definitie" knop

2. **Duplicate check** → Integration (`definitie_checker.py`)
   - Controleert bestaande definities
   - Biedt opties bij duplicaten

3. **Iteratieve verbetering** → Orchestration (`definitie_agent.py`)
   - Genereert definitie
   - Valideert tegen toetsregels
   - Verbetert tot max 5 iteraties

4. **AI generatie** → Generation (`definitie_generator.py`)
   - GPT-4 definitie creatie
   - Toetsregels als instructies
   - Context-aware prompting

5. **Validatie** → Validation (`definitie_validator.py`)
   - Controleert alle toetsregels
   - Genereert feedback

6. **Opslag** → Database (`definitie_repository.py`)
   - SQLite persistence
   - Versie beheer
   - Historie tracking

### 🚀 Quick Start voor Ontwikkelaars

#### Een nieuwe toetsregel toevoegen:
1. Maak JSON config in `config/toetsregels/regels/`
2. Maak Python validator in zelfde directory
3. Test met `python tools/run_maintenance.py`

#### UI component toevoegen:
1. Maak component in `ui/components/`
2. Registreer in `tabbed_interface.py`
3. Voeg tab toe aan interface

#### Service functionaliteit uitbreiden:
1. Update `unified_definition_service.py`
2. Voeg tests toe
3. Update deze documentatie

### 📊 Module Statistieken

- **Totaal modules**: 11 hoofdmodules
- **Toetsregels**: 46 modulaire validators
- **UI componenten**: 11 tab componenten
- **Test coverage**: ~80% (tests werkend)
- **Database tabellen**: 6 (definities, voorbeelden, etc.)

### 🔧 Onderhoud

Voor module-specifieke details, zie de individuele analyse bestanden.
Voor algemene ontwikkelrichtlijnen, zie `/CLAUDE.md`.

Laatste update: Juli 2025
