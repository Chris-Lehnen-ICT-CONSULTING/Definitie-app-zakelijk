# DefinitieAgent 2.3 🚀

**Nederlandse AI-powered Definitie Generator voor Juridische en Overheidscontexten**

[![Version](https://img.shields.io/badge/version-2.3.0-blue.svg)](./CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-87%25%20broken-red.svg)](./tests/)
[![License](https://img.shields.io/badge/license-Private-red.svg)]()

## 🎯 Overzicht

DefinitieAgent is een AI-applicatie voor het genereren van hoogwaardige Nederlandse definities volgens strenge overheidsstandaarden. Het systeem gebruikt GPT-4 met 46 kwaliteitsregels en biedt een modulaire architectuur voor uitbreidbaarheid.

### ✨ Kernfuncties

- 🤖 **AI Definitie Generatie** met GPT-4 en 6-stappen ontologisch protocol
- 📋 **46 Kwaliteitsregels** voor validatie en toetsing
- 🏗️ **Modulaire Architectuur** met UnifiedDefinitionService
- 🌐 **Web Lookup** voor context verrijking
- 📄 **Document Upload** voor kennisbasis uitbreiding
- ⚡ **Smart Caching** en performance optimalisatie
- 🖥️ **10 Streamlit UI Tabs** (30% functioneel)

## 🚀 Quick Start

Zie [Quick Start Guide](docs/setup/quick-start.md) voor gedetailleerde installatie instructies.

```bash
# Clone repository
git clone <repository-url>
cd Definitie-app

# Setup environment
cp .env.example .env
# Edit .env met je OpenAI API key

# Install dependencies
pip install -r requirements.txt

# Start applicatie
streamlit run src/app.py
```

## 📁 Project Structuur

```
definitie-app/
├── 📄 README.md              # Dit bestand
├── 📄 SETUP.md               # Quick start guide
├── 📄 CONTRIBUTING.md        # Development guidelines
├── 📄 CHANGELOG.md           # Version history
├── 📄 CLAUDE.md              # AI coding standards
├── 🔧 .env.example           # Environment template
│
├── 📁 src/                   # Source code
│   ├── services/             # UnifiedDefinitionService
│   ├── ai_toetsing/          # 46 validators
│   ├── tabs/                 # 10 UI tabs
│   └── app.py                # Main entry
│
├── 📁 docs/                  # Documentatie
│   ├── README.md             # Docs index
│   ├── brownfield-architecture.md
│   ├── requirements/         # Roadmap & backlog
│   └── analysis/             # Technische analyses
│
├── 📁 tests/                 # Test suites (87% broken)
└── 📁 data/                  # Database & uploads
```

## 📊 Project Status

### ✅ Werkend (v2.3)
- Services consolidatie voltooid (3→1)
- Basis definitie generatie
- AI toetsing met JSON validators
- Database persistence
- 3 van 10 UI tabs functioneel

### 🚧 In Progress
- UI tabs completeness (70% ontbreekt)
- Content enrichment (synoniemen, antoniemen)
- Test suite reparatie (87% broken)
- Performance monitoring

### 📈 6-Weken Roadmap

Week 1-2: **Quick Wins**
- Database concurrent access fix
- Web lookup UTF-8 encoding
- UI quick fixes

Week 3-4: **Feature Completeness**
- AI content generatie
- Prompt optimalisatie (35k → 10k)

Week 5-6: **Testing & Stabilisatie**
- Manual test protocol
- Documentatie updates

Zie [docs/requirements/ROADMAP.md](docs/requirements/ROADMAP.md) voor details.

## 🧪 Testing

**⚠️ Let op: Test suite is grotendeels broken (87% failing)**

```bash
# Werkende tests only
pytest tests/test_rate_limiter.py
pytest tests/ai_toetsing/test_toetsing_flow.py -k "validation"

# Manual testing wordt aanbevolen
# Zie docs/testing/ voor test scenarios
```

## 📖 Documentatie

- [Brownfield Architecture](docs/brownfield-architecture.md) - Actuele systeem architectuur
- [Roadmap](docs/requirements/ROADMAP.md) - 6-weken development plan
- [Backlog](docs/BACKLOG.md) - 77+ items met quick wins
- [Analyses](docs/analysis/) - Technische documentatie

## 🤝 Contributing

Zie [CONTRIBUTING.md](CONTRIBUTING.md) voor development guidelines.

**Quick Wins voor nieuwe contributors:**
- GPT temperatuur naar config file (2 uur)
- Streamlit widget key generator (2 uur)
- Plain text export (4 uur)
- Help tooltips (3 uur)

## 🔧 Development

### Features First Aanpak
- Legacy code = specificatie
- Werkende features > perfecte code
- Manual testing acceptabel
- Pragmatische oplossingen

### Coding Standards
- Nederlandse comments voor business logica
- Type hints waar mogelijk
- UnifiedDefinitionService pattern volgen
- Zie [CLAUDE.md](CLAUDE.md) voor AI guidelines

## 📞 Support

- Check [Setup Guide](SETUP.md) voor installatie
- Zie [Roadmap](docs/requirements/ROADMAP.md) voor planning
- Browse [Architecture](docs/brownfield-architecture.md) voor technische details
- Review [Backlog](docs/BACKLOG.md) voor open taken

## 📜 License

Private project. All rights reserved.

---

**DefinitieAgent v2.3** - Features First Development  
*"Legacy code is de specificatie"* 🚀