# DefinitieAgent 2.1 🚀

**Nederlandse AI-powered Definitie Generator met Hybrid Context Enhancement**

[![Test Coverage](https://img.shields.io/badge/coverage-14%25-yellow.svg)](./build/coverage/)
[![Tests](https://img.shields.io/badge/tests-37%2B%20passing-brightgreen.svg)](./tests/)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-Private-red.svg)]()

## 🎯 Overzicht

DefinitieAgent is een geavanceerde AI-applicatie voor het genereren van hoogwaardige Nederlandse definities met hybrid context verrijking door document upload en web lookup integratie.

### ✨ Hoofdfuncties v2.1
- 🤖 **AI-Powered Definitie Generatie** (GPT-4/3.5 Turbo)
- 📄 **Document Upload & Processing** (PDF, DOCX, TXT)
- 🔄 **Hybrid Context Enhancement** (Document + Web sources)
- ⚡ **Performance Optimized** (Caching, Rate limiting)
- 🔐 **Security Hardened** (Input validation, Threat detection)
- 🧪 **Comprehensive Testing** (37+ tests, 14% coverage)

## 📁 Project Structuur

```
definitie-app/
├── 📁 docs/                     # Documentatie
│   ├── architecture/            # Architectuur docs
│   ├── requirements/            # Requirements & roadmap
│   ├── testing/                 # Test documentatie
│   ├── configuration/           # Config docs
│   ├── domain/                  # Domein kennis
│   └── samples/                 # Voorbeeld documenten
│
├── 📁 src/                      # Source code
│   ├── ai_toetser/             # AI validatie engine
│   ├── document_processing/     # Document processing
│   ├── hybrid_context/         # Context verrijking
│   ├── security/               # Security middleware
│   ├── ui/                     # Streamlit interface
│   └── main.py                 # Hoofdapplicatie
│
├── 📁 tests/                    # Test suites
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   ├── performance/            # Performance tests
│   └── security/               # Security tests
│
├── 📁 data/                     # Data storage
│   ├── database/               # SQLite database
│   ├── uploads/                # Uploaded documents
│   └── cache/                  # Performance cache
│
├── 📁 config/                   # Configuration
├── 📁 exports/                  # Generated exports
├── 📁 logs/                     # Application logs
├── 📁 build/                    # Build artifacts
└── 📁 tools/                    # Development tools
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key
- SQLite 3

### Installation
```bash
# Clone repository
git clone <repository-url>
cd definitie-app

# Install dependencies
pip install -r requirements.txt

# Setup database
python src/tools/setup_database.py

# Configure API keys
cp config/config_default.yaml config/config_development.yaml
# Edit config_development.yaml with your API keys
```

### Run Application
```bash
# Start Streamlit interface
streamlit run src/main.py

# Or use the convenience script
./tools/start_definitie_webinterface.command
```

## 🧪 Testing

### Run All Tests
```bash
# All test suites
pytest tests/

# Specific test types
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests  
pytest tests/performance/   # Performance tests
pytest tests/security/      # Security tests
```

### Test Coverage
```bash
# Generate coverage report
pytest --cov=src tests/
pytest --cov=src --cov-report=html tests/

# View coverage
open build/coverage/index.html
```

## 📖 Documentatie

- **🏗️ [Architectuur](docs/architecture/ARCHITECTURE.md)** - Complete systeem architectuur
- **📋 [Requirements](docs/requirements/)** - Project requirements en roadmap
- **🧪 [Testing](docs/testing/)** - Test strategie en resultaten
- **⚙️ [Configuratie](docs/configuration/)** - Setup en configuratie
- **📚 [Domein](docs/domain/)** - Begrippenkader en voorbeelden

## 🔧 Development

### Development Environment
```bash
# Development configuratie
export ENVIRONMENT=development

# Run tests tijdens development
pytest tests/unit/ --watch

# Debug modus
streamlit run src/main.py --debug
```

### Code Quality
```bash
# Linting (indien geconfigureerd)
flake8 src/
black src/

# Type checking (indien geconfigureerd)  
mypy src/
```

## 📊 Features & Status

### ✅ Geïmplementeerd
- [x] AI Definitie Generatie (GPT-4/3.5)
- [x] Document Upload (PDF, DOCX, TXT)
- [x] Hybrid Context Enhancement
- [x] Performance Optimization
- [x] Security Middleware
- [x] Comprehensive Testing
- [x] Streamlit UI Interface

### 🚧 In Development
- [ ] Advanced AI Testing (25% coverage target)
- [ ] CI/CD Pipeline
- [ ] Production Monitoring
- [ ] API Documentation

### 📈 Roadmap
- [ ] Multi-language Support
- [ ] Advanced Document Types
- [ ] Real-time Collaboration
- [ ] Cloud Deployment

## 🔐 Security

- **Input Validation**: XSS, SQL injection prevention
- **Rate Limiting**: API abuse protection  
- **Threat Detection**: Malicious content detection
- **Audit Logging**: Security event tracking

## 📈 Performance

- **Caching**: Multi-level caching strategy
- **Async Processing**: Non-blocking operations
- **Rate Limiting**: Smart request throttling
- **Monitoring**: Performance metrics tracking

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Development Guidelines
- Follow existing code style
- Add tests for new features
- Update documentation
- Ensure security compliance

## 📞 Support

Voor vragen of problemen:
- Check [documentatie](docs/)
- Review [test resultaten](docs/testing/)
- Bekijk [architectuur](docs/architecture/)

## 📜 License

Private project. All rights reserved.

---

**DefinitieAgent v2.1** - Geavanceerde Nederlandse AI Definitie Generator  
Gebouwd met ❤️ voor hoogwaardige definitie kwaliteit