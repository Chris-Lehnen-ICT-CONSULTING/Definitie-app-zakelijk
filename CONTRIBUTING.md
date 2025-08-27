# 🤝 Contributing to DefinitieAgent

Bedankt voor je interesse in het bijdragen aan DefinitieAgent! Deze guide helpt je op weg.

## 📋 Development Process

### 1. Voor je begint

- Lees de [SETUP.md](SETUP.md) voor installatie instructies
- Bekijk de [Roadmap](docs/requirements/ROADMAP.md) voor geplande features
- Check de [Backlog](docs/BACKLOG.md) voor open taken
- Lees [README.md](README.md) voor AI-specifieke coding guidelines (BMAD methode)

### 2. Development Workflow

```bash
# 1. Fork het project
# 2. Clone je fork
git clone https://github.com/jouw-username/Definitie-app.git

# 3. Maak een feature branch
git checkout -b feature/jouw-feature-naam

# 4. Ontwikkel je feature
# 5. Test je wijzigingen

# 6. Commit met duidelijke message
git commit -m "feat: Voeg synoniemen generatie toe"

# 7. Push naar je fork
git push origin feature/jouw-feature-naam

# 8. Open een Pull Request
```

## 📊 Code Quality Status (2025-08-19)

- **Ruff errors**: 799 (vooral code style)
- **Kritieke errors**: 0 (F821 undefined names opgelost ✅)
- **Import hygiene**: Automatisch gesorteerd ✅
- **Pre-commit hooks**: Actief en werkend ✅

Focus op het toevoegen van nieuwe features, niet op het fixen van alle style issues.

## 🎯 Code Guidelines

### Python Style

- Gebruik Black formatter: `black src/`
- Gebruik Ruff voor linting: `ruff check . --fix`
- Pre-commit hooks zijn actief (automatische formatting)
- Type hints VERPLICHT voor nieuwe code
- Nederlandse comments voor business logica
- Engelse variabele/functie namen
- Python 3.11+ vereist

```python
def generate_definition(term: str, context: Optional[str] = None) -> Definition:
    """Genereer een definitie voor de gegeven term.

    Args:
        term: De term om te definiëren
        context: Optionele context voor betere definities

    Returns:
        Definition object met gegenereerde content
    """
    # Valideer input volgens Nederlandse overheidsstandaarden
    if not is_valid_term(term):
        raise ValidationError("Term voldoet niet aan vereisten")
```

### Testing

- Schrijf tests voor nieuwe functionaliteit
- Fix broken tests waar mogelijk
- Manual testing is acceptabel (Features First aanpak)

```bash
# Run tests
pytest tests/

# Run specifieke test
pytest tests/test_feature.py::test_specific_case
```

### Commit Messages

Gebruik conventional commits:
- `feat:` - Nieuwe feature
- `fix:` - Bug fix
- `docs:` - Documentatie updates
- `refactor:` - Code refactoring
- `test:` - Test toevoegingen/fixes
- `chore:` - Onderhoud taken

## 🔍 Waar te beginnen?

### Quick Wins (< 4 uur)
1. GPT temperatuur naar config file
2. Streamlit widget key generator bug
3. Plain text export functie
4. Help tooltips toevoegen

### Voor Beginners
- Documentatie updates
- UI text verbeteringen
- Simple bug fixes
- Test reparaties

### Voor Gevorderden
- Service consolidatie afmaken
- Content enrichment features
- Performance optimalisaties
- Architectuur verbeteringen

## 📝 Pull Request Checklist

- [ ] Code volgt project conventies
- [ ] Tests toegevoegd/aangepast (waar mogelijk)
- [ ] Documentatie bijgewerkt
- [ ] Geen gevoelige data in code
- [ ] Manual testing uitgevoerd
- [ ] PR beschrijving is duidelijk

## 🐛 Bug Reports

Bij het rapporteren van bugs, include:
1. Stappen om te reproduceren
2. Verwacht gedrag
3. Werkelijk gedrag
4. Screenshots (indien relevant)
5. Environment details

## 💡 Feature Requests

Voor nieuwe features:
1. Check eerst de [Roadmap](docs/requirements/ROADMAP.md)
2. Beschrijf use case
3. Geef voorbeelden
4. Overweeg impact op bestaande features

## 🚫 Wat NIET te doen

- Grote architectuur refactors zonder overleg
- Breaking changes zonder migratie pad
- Verwijderen van "legacy" code (het werkt!)
- Force push naar main branch

## 📞 Contact

- GitHub Issues voor bugs/features
- Discussions voor vragen
- Email voor security issues

# 📁 Document Organisatie

Alle documenten moeten in de juiste mappen worden geplaatst volgens onderstaande structuur:

```
docs/
├── architectuur/           # Architectuur documentatie
│   ├── workflows/          # Architectuur workflows
│   ├── definitie service/  # Service-specifieke architectuur
│   └── _archive/           # Verouderde architectuur docs
├── workflows/              # Algemene workflow beschrijvingen  
├── analyse/                # Analyse rapporten
├── requirements/           # Requirements & planning
├── technisch/              # Technische documentatie
├── reviews/                # Review rapporten
└── archief/                # Algemeen archief

scripts/
├── analyse/                # Nederlandse analyse scripts
├── analysis/               # Legacy Engelse scripts
├── maintenance/            # Onderhoud scripts
├── hooks/                  # Pre-commit hooks
└── migrate-*.sh            # Migratie scripts

reports/
├── analysis/               # Analyse rapporten (JSON)
├── visualizations/         # HTML visualisaties
└── exports/                # Gegenereerde exports

tests/
├── integration/            # Integratie tests
├── unit/                   # Unit tests  
├── data/                   # Test data bestanden
└── fixtures/               # Test fixtures
```

## Bestand Naamgeving Conventies

- **Nederlandse bestandsnamen** voor nieuwe bestanden
- **kleine-letters-met-streepjes** naamgeving
- **Geen documenten in root** (behalve README, LICENSE, etc.)
- **Pre-commit hook** controleert automatisch bestand locaties

## Document Migratie Scripts

We hebben 3 migratie scripts om documenten te organiseren:
- `scripts/migrate-documents.sh` - Fase 1: Basis organisatie
- `scripts/migrate-documents-fase2.sh` - Fase 2: Architectuur & technische docs
- `scripts/migrate-documents-fase3.sh` - Fase 3: Laatste opruiming

Bij twijfel: gebruik `--dry-run` optie om te zien wat er zou gebeuren.

## 🙏 Credits

Alle contributors worden vermeld in het project. Bedankt voor je bijdrage!

---
*Laatste update: 27 januari 2025*
