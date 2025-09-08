# Definitie-app Documentatie

Welkom bij de centrale documentatie hub voor het Definitie-app project.

## 🧭 Navigatie

Start hier: [INDEX.md](./INDEX.md) — centrale overzichtspagina voor alle documentatie.

## 🗂️ Documentatie Structuur

### [architectuur/](./architectuur/)
Canonical architecture documentatie (geconsolideerd September 2025)
- **[ENTERPRISE_ARCHITECTURE.md](./architectuur/ENTERPRISE_ARCHITECTURE.md)** - Business & strategic view
- **[SOLUTION_ARCHITECTURE.md](./architectuur/SOLUTION_ARCHITECTURE.md)** - Solution design patterns
- **[TECHNICAL_ARCHITECTURE.md](./architectuur/TECHNICAL_ARCHITECTURE.md)** - Implementatie details
- [templates/](./architectuur/templates/) - Architecture templates
<!-- ADRs zijn geïntegreerd in de canonical architecture documenten EA/SA/TA -->

### [technisch/](./technisch/)
Gedetailleerde technische documentatie
- Module analyses
- API specificaties
- Configuratie guides
- Error catalogus

### [reviews/](./reviews/)
Code quality en review documentatie
- Code reviews
- Prestaties analyses
- Beveiliging assessments

### [workflows/](./workflows/)
Development workflows en processen
- TDD to Uitrol workflow
- Validation orchestrator rollout
- Development guides

### [guidelines/](./guidelines/)
Project-wide guidelines en standards (7 documenten)
- Documentation policies en standards
- Development workflows
- Agent guidelines
- AI configuration guides

### [archief/](./archief/)
Historische documentatie en referentie materiaal
- [2025-09-architectuur-consolidatie/](./archief/2025-09-architectuur-consolidatie/) - Sept 2025 consolidatie (89 docs)
- Oude versies en legacy documentatie

### [stories/](./backlog/stories/)
User stories en epics
- Master epics en user stories document
- Episch Verhaal tracking en status

## 📍 Snelle Navigatie

**Voor Developers:**
- [Technical Documentation](./technisch/)
- [Architecture Documents](./architectuur/)
- [Development Workflows](./workflows/)

**Voor Architecten:**
- [Enterprise Architecture](./architectuur/ENTERPRISE_ARCHITECTURE.md) - Business view
- [Solution Architecture](./architectuur/SOLUTION_ARCHITECTURE.md) - Solution design
- [Technical Architecture](./architectuur/TECHNICAL_ARCHITECTURE.md) - Tech stack

**Voor Product Owners:**
- [Architecture Decisions](./architectuur/) - See EA/SA/TA documents
- [Master Epische Verhalen & Stories](./backlog/stories/MASTER-EPICS-USER-STORIES.md) - Single source of truth
- [Code Reviews](./reviews/) - Review documentatie

**Voor Operations:**
- [TDD to Uitrol Werkstroom](./guidelines/TDD_TO_DEPLOYMENT_WORKFLOW.md) - Complete workflow
- [Web Lookup Config](./technisch/web_lookup_config.md) - Configuration guide

## 🎯 Belangrijke Documenten

- Master TODO - Taken en planning (integrated in stories)
- Validation Rules - 46 toetsregels (see config/toetsregels/)
- 6-Stappen Protocol - Definitie methodologie (archived)

## ✅ Consolidatie Status (September 2025)

Documentatie consolidatie is **compleet**:
- **89 architecture docs → 3 canonical documents**
- **Guidelines gecentraliseerd** in [/guidelines/](./guidelines/)
- **Templates gescheiden** van documentatie
- Zie [CANONICAL_LOCATIONS.md](./guidelines/CANONICAL_LOCATIONS.md) voor officiële locaties

## 🔍 Zoeken

Gebruik `grep -r "search term" .` OM door alle documentatie te zoeken.

## 📝 Bijdragen

1. Volg de canonieke locaties in [guidelines/CANONICAL_LOCATIONS.md](./guidelines/CANONICAL_LOCATIONS.md)
2. Check eerst [guidelines/DOCUMENT-CREATION-WORKFLOW.md](./guidelines/DOCUMENT-CREATION-WORKFLOW.md)
3. Vermijd het creëren van duplicaten - zoek eerst!
4. Update deze README bij structuur wijzigingen

## 📅 Laatste Update

5 September 2025 - Architectuur consolidatie compleet, guidelines gecentraliseerd
