# DefinitieAgent - Nederlandse AI Definitie Generator 🧠

**AI-powered definitie generator voor overheidsgebruik met uitgebreide validatie en context verrijking**

[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)
[![Coverage](https://img.shields.io/badge/coverage-11%25-red.svg)](./tests/)
[![License](https://img.shields.io/badge/license-Private-red.svg)]()
[![Status](https://img.shields.io/badge/status-Production%20Ready-green.svg)]()

## 🎯 Overzicht

DefinitieAgent is een geavanceerde Streamlit-applicatie voor het genereren van hoogwaardige Nederlandse definities voor overheidsgebruik. De applicatie combineert AI-gegenereerde definities met regelgebaseerde validatie en ondersteunt meerdere contexten (organisatorisch, juridisch, wettelijk).

### ✨ Kernfuncties
- 🤖 **AI-Definitie Generatie** (GPT-4 met geoptimaliseerde prompts)
- 📊 **50+ Validatieregels** (CON, ESS, STR, INT, SAM, VER, ARAI)
- 🔍 **Web Lookup** (8 Nederlandse definitiebronnen)
- 📝 **Voorbeeldgeneratie** (zinnen, praktijk, tegenvoorbeelden)
- 📋 **Expert Review** systeem
- 📤 **Export functionaliteit** (TXT, JSON, CSV)
- 🔒 **Verboden woorden** management
- 📊 **Uitgebreide logging** en audit trail

## 🚨 Huidige Status - Technische Schuld

> **⚠️ BELANGRIJK**: Deze applicatie draait in productie maar heeft significante technische schuld. Zie [CODEBASE_DIAGNOSE_EN_VERBETERPLAN.md](CODEBASE_DIAGNOSE_EN_VERBETERPLAN.md) voor details.

### 🔴 Kritieke Issues
- **Monolithische core**: `ai_toetser/core.py` (1984 lijnen)
- **Duplicate modules**: export/exports, log/logs, definitie_generator
- **~~Web lookup duplicates~~**: ✅ OPGELOST - 5 implementaties geconsolideerd naar WebLookupService
- **Onvolledige migratie**: Legacy vs moderne architectuur
- **Memory leaks**: Unbounded cache growth
- **Security risico's**: API keys in logs, geen input validation

### 🟢 Service Architecture Progress (87% compleet)

De nieuwe clean architecture met dependency injection is grotendeels geïmplementeerd:

#### ✅ Voltooide Services:
- **DefinitionGenerator** - AI-powered definitie generatie
- **DefinitionValidator** - Validatie met 46 toetsregels
- **DefinitionRepository** - Database operaties
- **DefinitionOrchestrator** - Workflow coördinatie
- **WebLookupService** - Geconsolideerde web lookup (7 bronnen)

#### 🚧 In Development:
- **ExamplesService** - Voorbeelden generatie
- **ExportService** - Multi-format export
- **DocumentService** - Document processing
- **MonitoringService** - Performance monitoring
- **CacheService** - Cross-cutting caching

Gebruik: `export USE_NEW_SERVICES=true` of UI toggle in sidebar

### 🟡 Architectuur Problemen
- **Test coverage**: 11% (target: 85%)
- **Performance**: ~3s response time
- **Singleton overuse**: Moeilijk te testen
- **Mixed responsibilities**: UI + business logic

## 📁 Werkelijke Project Structuur

```
definitie-app/
├── 📁 src/                           # Hoofdapplicatie
│   ├── ai_toetser/                   # ⚠️ MONOLITH (1984 lijnen)
│   │   └── core.py                   # Alle validatie in één bestand
│   ├── services/                     # ✅ GECONSOLIDEERD (3→1)
│   │   └── unified_definition_service.py
│   ├── generation/                   # AI definitie generatie
│   ├── validation/                   # Regel validatie
│   ├── voorbeelden/                  # ✅ GEUNIFICEERD
│   ├── web_lookup/                   # 8 Nederlandse bronnen
│   ├── database/                     # SQLite repository
│   ├── ui/                          # 🚧 INCOMPLETE (moderne architectuur)
│   ├── config/                      # Configuratie management
│   ├── utils/                       # Utilities (3x implementaties)
│   │
│   ├── centrale_module_definitie_kwaliteit.py  # 🔴 LEGACY MAIN (1089 lijnen)
│   └── main.py                      # 🆕 MODERNE ENTRY POINT (63 lijnen)
│
├── 📁 kleinere modules/              # 17 support modules
│   ├── export/ & exports/           # ⚠️ DUPLICATE
│   ├── log/ & logs/                 # ⚠️ DUPLICATE
│   ├── cache/, security/, tools/    # Basis implementaties
│   └── [13 meer...]                 # Zie SMALLER_MODULES_ANALYSIS.md
│
├── 📁 config/                       # Configuratie bestanden
│   ├── toetsregels.json            # 50+ validatieregels
│   ├── verboden_woorden.json       # Verboden startwoorden
│   └── context_wet_mapping.json    # Context mappings
│
├── 📁 log/                         # Logging (CSV, JSON, JSONL)
├── 📁 data/                        # Data storage
├── 📁 cache/                       # Performance cache
└── 📁 tests/                       # ⚠️ MINIMAL (11% coverage)
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- OpenAI API key
- SQLite 3

### Installation
```bash
# Clone repository
git clone <repository-url>
cd definitie-app

# Install dependencies
pip install -r requirements.txt

# Setup environment
echo "OPENAI_API_KEY=your-key-here" > .env
```

### Run Application
```bash
# Start legacy interface (volledig functioneel)
streamlit run src/centrale_module_definitie_kwaliteit.py

# Start moderne interface (skeleton only)
streamlit run src/main.py
```

## 🧪 Testing

### Huidige Test Status
```bash
# Run bestaande tests
pytest tests/

# Coverage report
pytest --cov=src tests/
# Huidige coverage: 11%
```

### Test Issues
- **Monoliths**: Moeilijk te testen
- **Singletons**: Global state problemen
- **Mock dependencies**: Ontbreken
- **Integration tests**: Minimaal

## 📖 Documentatie

### 🎯 **Start Hier**
- **[📋 Complete Diagnose](CODEBASE_DIAGNOSE_EN_VERBETERPLAN.md)** - Technische schuld analyse
- **[📚 Documentatie Index](DOCUMENTATION_INDEX.md)** - Alle documentatie overzicht
- **[🧹 Cleanup Status](CODEBASE_CLEANUP_STATUS.md)** - Huidige opruimingsvoortgang

### 🏗️ **Module Analyses**
- **[🤖 AI Toetser](src/ai_toetser/AI_TOETSER_MODULE_ANALYSIS.md)** - Monolithische validator
- **[⚙️ Services](src/services/SERVICES_MODULE_ANALYSIS.md)** - Geconsolideerde services (87% compleet)
- **[🔍 Web Lookup](WEB_LOOKUP_CONSOLIDATION_ANALYSIS.md)** - ✅ VOLTOOID - Geconsolideerd naar WebLookupService
- **[🖥️ UI](src/ui/UI_MODULE_ANALYSIS.md)** - Gebruikersinterface
- **[📊 Database](src/database/DATABASE_MODULE_ANALYSIS.md)** - Repository pattern
- **[🔧 Utils](src/utils/UTILS_MODULE_ANALYSIS.md)** - Utility functies
- **[📝 Voorbeelden](src/voorbeelden/VOORBEELDEN_MODULE_ANALYSIS.md)** - Voorbeeldgeneratie
- **[⚙️ Config](src/config/CONFIG_MODULE_ANALYSIS.md)** - Configuratie management
- **[📋 Kleinere Modules](src/SMALLER_MODULES_ANALYSIS.md)** - 17 support modules
- **[🏠 Root Files](src/SRC_ROOT_ANALYSIS.md)** - Legacy vs moderne architectuur

## 🔧 Development

### Huidige Development Issues
```bash
# Monolith debugging
# ai_toetser/core.py is 1984 lijnen - zeer moeilijk te debuggen

# Duplicate imports
# Meerdere modules met zelfde functionaliteit

# Memory issues
# Unbounded cache growth in productie
```

### Development Environment
```bash
# Development mode
export ENVIRONMENT=development

# Enable debug logging
export DEBUG=true

# Run with auto-reload
streamlit run src/centrale_module_definitie_kwaliteit.py --server.runOnSave true
```

## 📊 Werkelijke Features Status

### ✅ **Volledig Functioneel**
- [x] AI Definitie Generatie (GPT-4, geoptimaliseerde prompts)
- [x] 50+ Validatieregels (CON, ESS, STR, INT, SAM, VER, ARAI)
- [x] Web Lookup (8 Nederlandse bronnen)
- [x] Voorbeeldgeneratie (zinnen, praktijk, tegenvoorbeelden)
- [x] Expert Review systeem
- [x] Export functionaliteit (TXT)
- [x] Verboden woorden management
- [x] Uitgebreide logging (CSV, JSON, JSONL)
- [x] Three-tab interface (AI, Aangepast, Expert)

### 🚧 **Gedeeltelijk Werkend**
- [~] Services consolidatie (3→1 deels voltooid)
- [~] Moderne UI architectuur (skeleton only)
- [~] Test coverage (11% - zeer laag)
- [~] Performance optimization (basis caching)

### 🔴 **Kritieke Problemen**
- [x] Monolithische core (1984 lijnen)
- [x] Duplicate modules (export/exports, log/logs)
- [x] Memory leaks (unbounded cache)
- [x] Security vulnerabilities (API keys in logs)
- [x] Incomplete migration (legacy vs modern)

### 📈 **Roadmap (na Technical Debt)**
- [ ] Complete monolith refactoring
- [ ] Duplicate module elimination
- [ ] Modern architecture completion
- [ ] Security hardening
- [ ] Performance optimization
- [ ] Test coverage > 85%

## 🔐 Security Issues

### 🚨 **Huidige Vulnerabilities**
- **API keys** in session state en logs
- **Geen input validation** 
- **Pickle deserialization** risico's
- **Direct file operations** zonder sanitization
- **No authentication** system

### 🛡️ **Security Roadmap**
- Input validation overal
- API key management
- Rate limiting
- Audit logging
- Authentication system

## 📈 Performance Issues

### 🐌 **Huidige Bottlenecks**
- **Startup time**: Alle 50+ regels laden
- **Response time**: ~3 seconden
- **Memory usage**: Unbounded cache growth
- **Database**: Geen connection pooling

### ⚡ **Performance Roadmap**
- Lazy loading van regels
- Redis caching
- Database optimization
- Async processing

## 🤝 Contributing

### Voordat je begint
1. **Lees de diagnose**: [CODEBASE_DIAGNOSE_EN_VERBETERPLAN.md](CODEBASE_DIAGNOSE_EN_VERBETERPLAN.md)
2. **Kies een module**: Zie module analyses
3. **Volg het verbeterplan**: 16-weken roadmap beschikbaar

### Development Guidelines
- **Refactor incrementeel**: Geen big bang changes
- **Test coverage**: Voeg tests toe voor nieuwe code
- **Documenteer alles**: Update module analyses
- **Performance eerst**: Geen nieuwe features zonder optimization

## 📞 Support

### Voor Bugs/Issues
- **Monolith issues**: Zie AI_TOETSER_MODULE_ANALYSIS.md
- **Performance**: Zie CODEBASE_DIAGNOSE_EN_VERBETERPLAN.md
- **Architecture**: Zie SRC_ROOT_ANALYSIS.md

### Voor Development
- **Module specifiek**: Zie individuele module analyses
- **Algemeen**: Zie DOCUMENTATION_INDEX.md

## 📜 License

Private project. All rights reserved.

---

## ⚠️ Belangrijke Waarschuwing

**Deze applicatie draait in productie maar heeft significante technische schuld.**

- **Monolithische code** (1984 lijnen in één bestand)
- **Duplicate functionaliteit** (3+ implementaties)
- **Memory leaks** (unbounded cache growth)
- **Security risico's** (API keys in logs)
- **Lage test coverage** (11%)

**Zie [CODEBASE_DIAGNOSE_EN_VERBETERPLAN.md](CODEBASE_DIAGNOSE_EN_VERBETERPLAN.md) voor complete analyse en 16-weken verbeterplan.**

---

**DefinitieAgent** - Functioneel maar heeft refactoring nodig  
Status: **Production Ready** ⚠️ met **Technical Debt**