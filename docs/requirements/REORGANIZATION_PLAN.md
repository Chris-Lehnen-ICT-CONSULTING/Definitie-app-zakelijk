# 🧹 Project Reorganisatie Plan

## 📊 Huidige Situatie
De projectstructuur is rommelig geworden met:
- **Dubbele bestanden** (definities.db in 2 locaties)
- **Losse documentatie** op root level (12+ .md bestanden)
- **Gemixte data** (exports in meerdere mappen)
- **Test chaos** (tests in src/ én tests/)
- **Cache chaos** (cache in 3 locaties)
- **Onduidelijke organisatie** (docs verspreid)

## 🎯 Voorgestelde Nieuwe Structuur

```
definitie-app/
├── 📁 docs/                           # Alle documentatie
│   ├── 📁 architecture/               # Architectuur documentatie
│   │   ├── ARCHITECTURE.md            # Hoofddocument
│   │   ├── definitie-agent-architecture.html
│   │   └── diagrams/                  # Mermaid/andere diagrammen
│   ├── 📁 requirements/               # Requirements & planning
│   │   ├── PROJECT_STATUS.md
│   │   ├── IMPLEMENTATION_SUMMARY.md
│   │   └── roadmap/                   # Alle roadmap items
│   ├── 📁 testing/                    # Test documentatie
│   │   ├── TEST_RESULTS_SUMMARY.md
│   │   ├── TEST_ANALYSIS_REPORT.md
│   │   └── TESTING_IMPLEMENTATION.md
│   ├── 📁 configuration/              # Config documentatie
│   │   ├── CONFIG_DOCUMENTATION.md
│   │   └── CLAUDE.md
│   ├── 📁 domain/                     # Domein documentatie
│   │   ├── begrippen.xlsx
│   │   ├── Begrippenkader Identiteitsbehandeling.csv
│   │   └── Definities Identiteitsbehandeling.docx
│   └── 📁 samples/                    # Voorbeeld documenten
│       └── inhoudelijke documenten om te uploaden in de tool/
│
├── 📁 src/                            # Source code (SCHOON)
│   ├── 📁 ai_toetser/
│   ├── 📁 config/
│   ├── 📁 document_processing/
│   ├── 📁 hybrid_context/
│   ├── 📁 security/
│   ├── 📁 ui/
│   ├── 📁 validation/
│   ├── 📁 web_lookup/
│   └── main.py
│
├── 📁 tests/                          # Alle tests (GECONSOLIDEERD)
│   ├── 📁 unit/
│   ├── 📁 integration/
│   ├── 📁 performance/
│   ├── 📁 security/
│   ├── conftest.py
│   └── pytest.ini
│
├── 📁 data/                           # Alle data files
│   ├── 📁 database/
│   │   └── definities.db             # ENKEL HIER
│   ├── 📁 uploads/
│   │   └── documents/
│   └── 📁 cache/                      # Centrale cache
│
├── 📁 config/                         # Configuration files
│   ├── config_default.yaml
│   ├── config_development.yaml
│   ├── config_production.yaml
│   └── config_testing.yaml
│
├── 📁 exports/                        # Output files
│   ├── 📁 definitions/
│   ├── 📁 reports/
│   └── 📁 samples/
│
├── 📁 logs/                           # Log files
│   ├── 📁 application/
│   ├── 📁 security/
│   └── 📁 performance/
│
├── 📁 scripts/                        # Utility scripts
│   ├── setup/
│   ├── migration/
│   └── deployment/
│
├── 📁 build/                          # Build artifacts
│   ├── 📁 coverage/                   # htmlcov verhuist hier
│   ├── 📁 release/
│   └── 📁 temp/
│
├── 📁 tools/                          # Development tools
│   └── start_definitie_webinterface.command
│
├── requirements.txt
├── README.md                          # Korte project intro
└── .gitignore
```

## 🚀 Reorganisatie Steps

### Step 1: Documentatie Consolideren
```bash
# Maak documentatie structuur
mkdir -p docs/{architecture,requirements,testing,configuration,domain,samples}

# Verplaats architectuur docs
mv data/definitie-agent-architecture.html docs/architecture/
mv ARCHITECTURE.md docs/architecture/

# Verplaats requirements docs
mv PROJECT_STATUS.md docs/requirements/
mv IMPLEMENTATION_SUMMARY.md docs/requirements/
mv docs/roadmap/ docs/requirements/roadmap/

# Verplaats test docs
mv TEST_RESULTS_SUMMARY.md docs/testing/
mv TEST_ANALYSIS_REPORT.md docs/testing/
mv TESTING_IMPLEMENTATION.md docs/testing/

# Verplaats config docs
mv CONFIG_DOCUMENTATION.md docs/configuration/
mv CLAUDE.md docs/configuration/

# Verplaats domein docs
mv docs/begrippen.xlsx docs/domain/
mv "docs/Begrippenkader Identiteitsbehandeling.csv" docs/domain/
mv "docs/Definities Identiteitsbehandeling.docx" docs/domain/

# Verplaats samples
mv "docs/inhoudelijke documenten om te uploaden in de tool/" docs/samples/
```

### Step 2: Source Code Opschonen
```bash
# Verwijder dubbele tests
rm -rf src/tests/

# Consolideer cache
mkdir -p data/cache/
mv cache/* data/cache/ 2>/dev/null || true
mv src/cache/* data/cache/ 2>/dev/null || true
rm -rf cache/ src/cache/

# Verplaats database
mkdir -p data/database/
mv definities.db data/database/ 2>/dev/null || true
rm -f src/definities.db

# Verplaats uploads
mkdir -p data/uploads/documents/
mv data/uploaded_documents/* data/uploads/documents/ 2>/dev/null || true
mv src/data/uploaded_documents/* data/uploads/documents/ 2>/dev/null || true
rm -rf data/uploaded_documents/ src/data/uploaded_documents/
```

### Step 3: Tests Reorganiseren
```bash
# Organiseer tests per type
mkdir -p tests/{unit,integration,performance,security}

# Verplaats performance tests
mv tests/test_performance_comprehensive.py tests/performance/
mv tests/test_performance.py tests/performance/

# Verplaats security tests  
mv tests/test_async_security_comprehensive.py tests/security/
mv tests/test_security_comprehensive.py tests/security/

# Verplaats integration tests
mv tests/test_integration_comprehensive.py tests/integration/
mv tests/test_hybrid_context_comprehensive.py tests/integration/
mv tests/test_comprehensive_system.py tests/integration/

# Unit tests blijven in tests/unit/
mv tests/test_*.py tests/unit/ 2>/dev/null || true
```

### Step 4: Build & Logs Opschonen
```bash
# Verplaats coverage reports
mkdir -p build/coverage/
mv htmlcov/* build/coverage/ 2>/dev/null || true
rm -rf htmlcov/

# Organiseer logs
mkdir -p logs/{application,security,performance}
mv log/* logs/application/ 2>/dev/null || true
mv logs/security_log_* logs/security/ 2>/dev/null || true
mv src/log/* logs/application/ 2>/dev/null || true
rm -rf log/ src/log/

# Organiseer exports
mkdir -p exports/{definitions,reports,samples}
mv exports/definitie_*.txt exports/definitions/ 2>/dev/null || true
mv exports/*.json exports/samples/ 2>/dev/null || true
```

### Step 5: Scripts & Tools
```bash
# Verplaats scripts
mkdir -p scripts/{setup,migration,deployment}
mv scripts/* scripts/setup/ 2>/dev/null || true
mv src/scripts/* scripts/migration/ 2>/dev/null || true

# Verplaats tools
mkdir -p tools/
mv scripts/start_definitie_webinterface.command tools/
```

### Step 6: Root Cleanup
```bash
# Verwijder losse docs van root
rm -f ARCHITECTURE_DIAGRAMS.md
rm -f CLEANUP_REPORT.md  
rm -f DOCUMENT_UPLOAD_IMPLEMENTATION.md
rm -f UI_ANALYSE.md
rm -f PROMPT_ANALYSIS_RECOMMENDATIONS.txt

# Update gitignore
echo "
# Build artifacts
build/
*.pyc
__pycache__/

# Data files
data/cache/
data/database/*.db-journal
data/uploads/

# Logs
logs/

# Exports
exports/definitions/
exports/reports/

# OS files
.DS_Store
" >> .gitignore
```

## ✅ Voordelen Nieuwe Structuur

### 📖 Documentatie
- **Georganiseerd per type** (architecture, requirements, testing)
- **Makkelijk te vinden** en onderhouden
- **Logische hiërarchie** voor verschillende stakeholders

### 🔧 Source Code  
- **Schone src/** directory zonder tests/cache/data
- **Duidelijke module scheiding**
- **Geen dubbele bestanden**

### 🧪 Testing
- **Tests georganiseerd per type** (unit, integration, performance, security)
- **Makkelijk om specifieke test suites te draaien**
- **Duidelijke test strategie**

### 💾 Data Management
- **Centrale data directory** met subdirectories
- **Geen verspreide databases**
- **Georganiseerde uploads en cache**

### 📊 Build & Deploy
- **Build artifacts gescheiden**
- **Duidelijke logs organisatie**
- **Tools en scripts georganiseerd**

## 🚨 Risico's & Mitigatie

### Mogelijke Issues:
1. **Import paths** kunnen breken
2. **Config paths** moeten worden aangepast  
3. **Test discovery** moet worden geconfigureerd
4. **Deployment scripts** moeten worden bijgewerkt

### Mitigatie:
1. **Gradual migration** - stap voor stap uitvoeren
2. **Tests draaien** na elke stap
3. **Config updates** documenteren
4. **Backup maken** voor reorganisatie

## 🎯 Uitvoering Plan

### Fase 1: Voorbereiding
- [ ] Backup maken van huidige project
- [ ] Git commit van huidige staat
- [ ] Plan reviewen met team

### Fase 2: Documentatie (Veilig)
- [ ] Documentatie reorganiseren
- [ ] README bijwerken
- [ ] Documentatie testen

### Fase 3: Data & Cache (Medium risico)
- [ ] Data directories consolideren
- [ ] Cache locaties bijwerken
- [ ] Database paths testen

### Fase 4: Source & Tests (Hoog risico)
- [ ] Import paths analyseren
- [ ] Tests reorganiseren
- [ ] Alle tests uitvoeren
- [ ] Config paths aanpassen

### Fase 5: Final Cleanup
- [ ] Build artifacts verplaatsen
- [ ] Scripts organiseren  
- [ ] .gitignore bijwerken
- [ ] Final tests

Wil je dat ik deze reorganisatie uitvoer? Ik stel voor om stap voor stap te gaan en na elke stap te controleren dat alles nog werkt.