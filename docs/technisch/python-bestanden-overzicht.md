# VOLLEDIG PYTHON BESTANDEN OVERZICHT - DefinitieAgent

> ⚠️ **Dit overzicht is verouderd — gebruik het niet als bron van waarheid.**
> Gemeten op 2026-08-07 (DEF-600): **38 van de 97 genoemde bestanden bestaan niet meer**
> in `src/`, en de LOC-getallen lopen ver achter (`container.py` staat op 439 terwijl het
> er 1067 zijn; `service_factory.py` 379 vs 790). Ook `definition_orchestrator.py` is
> vervangen door `definition_orchestrator_v2.py`.
>
> De ✅ **ACTIEF**-markering is daardoor onbetrouwbaar: `ab_testing_framework.py` stond
> hier als "actief" terwijl het nooit door iets werd geïmporteerd.
>
> Voor de actuele stand: `find src -name "*.py" | xargs wc -l` en
> `python scripts/detect_orphan_modules.py`. Actualisatie van dit document staat
> getrackt; verwijderde bestanden zijn er tot die tijd handmatig uit gehaald.

## 📊 PROJECT STATISTIEKEN
> Onderstaande cijfers dateren van de oorspronkelijke inventarisatie. Werkelijke stand
> op 2026-08-07: **366 bestanden, 94.602 LOC** in `src/`.

- **Totaal Python bestanden**: 337 bestanden
- **Totaal regels code**: 85,476 LOC
- **Hoofdfunctie**: AI-gedreven juridische definitie generator
- **Architectuur**: Service-oriented met afhankelijkheid injection
- **Entry point**: `src/main.py`

---

## 🏗️ KERNARCHITECTUUR - SRC/SERVICES/ (24 bestanden, 10,006 LOC)

### 🎯 ORCHESTRATION & CONTAINER
| Bestand | LOC | Status | Functionaliteit |
|---------|-----|---------|----------------|
| `container.py` | 439 | ✅ **ACTIEF** | Dependency injection container - hart van de service architectuur |
| `definition_orchestrator.py` | 678 | ✅ **ACTIEF** | Hoofd orchestrator voor definitie workflow en AI pipeline |
| `service_factory.py` | 379 | ✅ **ACTIEF** | Factory pattern voor service instantiatie |
| `workflow_service.py` | 695 | ✅ **ACTIEF** | Business logic workflow management |

### 🤖 AI DEFINITION GENERATION PIPELINE
| Bestand | LOC | Status | Functionaliteit |
|---------|-----|---------|----------------|
| `definition_generator_cache.py` | 601 | ✅ **ACTIEF** | Cache systeem voor AI-gegenereerde definities |
| `definition_generator_config.py` | 347 | ✅ **ACTIEF** | Configuratie voor AI model parameters |
| `definition_generator_context.py` | 456 | ✅ **ACTIEF** | Context management voor definitie generatie |
| `definition_generator_enhancement.py` | 560 | ✅ **ACTIEF** | Enhancement pipeline voor AI output |
| `definition_generator_monitoring.py` | 414 | ✅ **ACTIEF** | Prestaties monitoring van AI systeem |
| `definition_generator_prompts.py` | 657 | ✅ **ACTIEF** | AI prompt management en templates |

### 💾 DATA & REPOSITORY LAYER
| Bestand | LOC | Status | Functionaliteit |
|---------|-----|---------|----------------|
| `definition_repository.py` | 473 | ✅ **ACTIEF** | Database repository pattern - hoofd data access |
| `null_repository.py` | 81 | ✅ **ACTIEF** | Null object pattern voor testing |
| `duplicate_detection_service.py` | 231 | ✅ **ACTIEF** | Detectie van duplicate definities |
| `data_aggregation_service.py` | 347 | ✅ **ACTIEF** | Data aggregatie service |

### ✅ QUALITY & VALIDATION
| Bestand | LOC | Status | Functionaliteit |
|---------|-----|---------|----------------|
| `definition_validator.py` | 357 | ✅ **ACTIEF** | Hoofdvalidatie service voor definities |
| `cleaning_service.py` | 277 | ✅ **ACTIEF** | AI output opschoning en normalisatie |

### 🔍 EXTERNAL INTEGRATION
| Bestand | LOC | Status | Functionaliteit |
|---------|-----|---------|----------------|
| `modern_web_lookup_service.py` | 433 | ⚠️ **GEDEELTELIJK** | Web lookup - backend werkt, UI integratie ontbreekt |
| `web_lookup/sru_service.py` | - | ✅ **ACTIEF** | SRU (Search/Retrieve via URL) service integratie |
| `web_lookup/wikipedia_service.py` | - | ✅ **ACTIEF** | Wikipedia API integratie |

### 📊 UTILITIES & SUPPORT
| Bestand | LOC | Status | Functionaliteit |
|---------|-----|---------|----------------|
| `export_service.py` | 312 | ✅ **ACTIEF** | Export naar TXT, JSON, CSV formaten |
| `regeneration_service.py` | 129 | ✅ **ACTIEF** | Definitie regeneratie workflow |
| `category_service.py` | 169 | ✅ **ACTIEF** | Categorie management en operations |
| `category_state_manager.py` | 47 | ✅ **ACTIEF** | State management voor categorieën |
| `interfaces.py` | 547 | ✅ **ACTIEF** | Service interface definities |

---

## 🖥️ GEBRUIKERSINTERFACE - SRC/UI/ (8 bestanden, 12,167 LOC)

### 🎨 HOOFD UI CONTROLLER
| Bestand | LOC | Status | Functionaliteit |
|---------|-----|---------|----------------|
| `tabbed_interface.py` | 1,313 | ✅ **KERN ACTIEF** | Hoofdcontroller voor tabbed Streamlit interface |
| `session_state.py` | - | ✅ **ACTIEF** | Streamlit sessie status management |
| `cache_manager.py` | - | ✅ **ACTIEF** | UI cache management |
| `async_progress.py` | - | ✅ **ACTIEF** | Asynchrone progress indicators |
| `components_adapter.py` | - | ✅ **ACTIEF** | Adapter voor component integratie |

### 🧩 UI COMPONENTEN (12 bestanden)
| Bestand | Status | Functionaliteit |
|---------|---------|----------------|
| `definition_generator_tab.py` | ✅ **ACTIEF** | Hoofdtab voor definitie generatie workflow |
| `expert_review_tab.py` | ✅ **ACTIEF** | Expert review en approval workflow |
| `export_tab.py` | ✅ **ACTIEF** | Export functionaliteit interface |
| `external_sources_tab.py` | ✅ **ACTIEF** | Externe bronnen management interface |
| `history_tab.py` | ✅ **ACTIEF** | Definitie geschiedenis en versioning |
| `management_tab.py` | ✅ **ACTIEF** | Systeembeheer interface |
| `monitoring_tab.py` | ✅ **ACTIEF** | System monitoring dashboard |
| `orchestration_tab.py` | ✅ **ACTIEF** | Werkstroom orchestration interface |
| `quality_control_tab.py` | ✅ **ACTIEF** | Kwaliteitscontrole dashboard |
| `web_lookup_tab.py` | ❌ **PROBLEEM** | Web lookup interface - toont geen resultaten |
| `context_selector.py` | ✅ **ACTIEF** | Context selectie component |
| `category_regeneration_helper.py` | ✅ **ACTIEF** | Categorie regeneratie helper |

### ⚠️ LEGACY UI
| Bestand | Status | Functionaliteit |
|---------|---------|----------------|
| `components.py` | 🔄 **WORDT VERVANGEN** | Legacy components - wordt gemigreerd naar components/ |

---

## 🧪 VALIDATIESYSTEEM - SRC/TOETSREGELS/ (100+ bestanden, 13,632 LOC)

### 📋 CORE MANAGEMENT (4 bestanden)
| Bestand | LOC | Status | Functionaliteit |
|---------|-----|---------|----------------|
| `manager.py` | - | ✅ **ACTIEF** | Validatie regel management systeem |
| `loader.py` | - | 🔄 **LEGACY** | Legacy regel loader |
| `adapter.py` | - | ✅ **ACTIEF** | Interface adapter voor regel systeem |

### 📏 VALIDATIEREGELS (38 regels x 2 implementaties = 76 bestanden)

#### **ARAI - AI Response Adequacy & Intelligence (6 regels)**
| Regel | Implementatie | Validator | Status |
|-------|--------------|-----------|---------|
| `ARAI-01` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - AI response adequacy check |
| `ARAI-02` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - AI intelligence validation |
| `ARAI-03` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Response completeness |
| `ARAI-04` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Context awareness |
| `ARAI-05` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Reasoning quality |
| `ARAI-06` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Output consistency |

#### **CON - Consistency Validation (2 regels)**
| Regel | Implementatie | Validator | Status |
|-------|--------------|-----------|---------|
| `CON-01` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Internal consistency |
| `CON-02` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Cross-reference consistency |

#### **ESS - Essential Content Validation (5 regels)**
| Regel | Implementatie | Validator | Status |
|-------|--------------|-----------|---------|
| `ESS-01` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Essential content presence |
| `ESS-02` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Content relevance |
| `ESS-03` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Content accuracy |
| `ESS-04` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Content completeness |
| `ESS-05` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Content precision |

#### **INT - Integration & Interface Validation (9 regels)**
| Regel | Implementatie | Validator | Status |
|-------|--------------|-----------|---------|
| `INT-01` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - System integration |
| `INT-02` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Interface consistency |
| `INT-03` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Data flow validation |
| `INT-04` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - API compliance |
| `INT-05` | ❌ **ONTBREEKT** | ❌ **ONTBREEKT** | 🚨 **MISSING** - Integration completeness |
| `INT-06` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Error handling |
| `INT-07` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Prestaties validation |
| `INT-08` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Beveiliging compliance |
| `INT-09` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Scalability validation |

#### **SAM - Semantic Accuracy & Meaning (8 regels)**
| Regel | Implementatie | Validator | Status |
|-------|--------------|-----------|---------|
| `SAM-01` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Semantic accuracy |
| `SAM-02` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Meaning preservation |
| `SAM-03` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Context relevance |
| `SAM-04` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Terminology consistency |
| `SAM-05` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Conceptual clarity |
| `SAM-06` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Logical coherence |
| `SAM-07` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Semantic completeness |
| `SAM-08` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Meaning accuracy |

#### **STR - Structure & Formatting (9 regels)**
| Regel | Implementatie | Validator | Status |
|-------|--------------|-----------|---------|
| `STR-01` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Document structure |
| `STR-02` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Formatting compliance |
| `STR-03` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Layout consistency |
| `STR-04` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Header structure |
| `STR-05` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Content organization |
| `STR-06` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Citation format |
| `STR-07` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Reference structure |
| `STR-08` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Numbering system |
| `STR-09` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Visual presentation |

#### **VER - Verification & Completeness (3 regels)**
| Regel | Implementatie | Validator | Status |
|-------|--------------|-----------|---------|
| `VER-01` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Content verification |
| `VER-02` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Completeness check |
| `VER-03` | ✅ regels/ | ✅ validators/ | ✅ **ACTIEF** - Quality assurance |

---

## 💾 DATABASE LAYER - SRC/DATABASE/ (3 bestanden, 1,674 LOC)

| Bestand | LOC | Status | Functionaliteit |
|---------|-----|---------|----------------|
| `definitie_repository.py` | - | ✅ **ACTIEF** | Hoofd database access layer met repository pattern |
| `migrate_database.py` | - | ✅ **ACTIEF** | Database migratie management |
| `__init__.py` | - | ✅ **ACTIEF** | Package initialization |

---

## 🔧 CONFIGURATIE - SRC/CONFIG/ (6 bestanden, 1,590 LOC)

| Bestand | LOC | Status | Functionaliteit |
|---------|-----|---------|----------------|
| `config_manager.py` | - | ✅ **ACTIEF** | Centrale configuratie management |
| `config_loader.py` | - | ✅ **ACTIEF** | YAML/JSON configuratie laden |
| `config_adapters.py` | - | ✅ **ACTIEF** | Configuration adapters voor verschillende formaten |
| `rate_limit_config.py` | - | ✅ **ACTIEF** | Rate limiting configuratie |
| `verboden_woorden.py` | - | ✅ **ACTIEF** | Verboden woorden lijst voor content filtering |

---

## 🛠️ UTILITIES - SRC/UTILS/ (11 bestanden, 4,572 LOC)

### 🔄 RESILIENCE & RETRY
| Bestand | LOC | Status | Functionaliteit |
|---------|-----|---------|----------------|
| `resilience.py` | - | ✅ **ACTIEF** | Basis foutafhandeling en retry logic |
| `optimized_resilience.py` | - | ✅ **ACTIEF** | Geoptimaliseerde resilience patterns |
| `integrated_resilience.py` | - | ✅ **ACTIEF** | Geïntegreerde resilience systeem |
| `enhanced_retry.py` | - | ✅ **ACTIEF** | Enhanced retry mechanismen |
| `smart_rate_limiter.py` | - | ✅ **ACTIEF** | Intelligente rate limiting |

### 📊 MONITORING & PERFORMANCE
| Bestand | LOC | Status | Functionaliteit |
|---------|-----|---------|----------------|
| `performance_monitor.py` | - | ✅ **ACTIEF** | Prestaties monitoring en metrics |
| `async_api.py` | - | ✅ **ACTIEF** | Asynchrone API utilities |
| `cache.py` | - | ✅ **ACTIEF** | Cache management systeem |

### 🚨 ERROR HANDLING
| Bestand | LOC | Status | Functionaliteit |
|---------|-----|---------|----------------|
| `exceptions.py` | - | ✅ **ACTIEF** | Custom exception handling en error types |

🔍 **MOGELIJKE DUPLICATIE**: Meerdere resilience implementaties - consolidatie mogelijk.

---

## 🏛️ DOMEINLOGICA - SRC/DOMAIN/ (2 folders + files, 802 LOC)

### 📚 ONTOLOGIE & CATEGORISATIE
| Bestand | LOC | Status | Functionaliteit |
|---------|-----|---------|----------------|
| `ontological_categories.py` | - | ✅ **ACTIEF** | Ontologische categorisatie systeem |
| `autoriteit/betrouwbaarheid.py` | - | ✅ **ACTIEF** | Autoriteit en betrouwbaarheid validatie |
| `juridisch/patronen.py` | - | ✅ **ACTIEF** | Juridische patronen herkenning |
| `linguistisch/pluralia_tantum.py` | - | ✅ **ACTIEF** | Nederlandse linguïstische regels |

---

## 📚 VOORBEELDSYSTEEM - SRC/VOORBEELDEN/ (5 bestanden, 1,518 LOC)

| Bestand | LOC | Status | Functionaliteit |
|---------|-----|---------|----------------|
| `voorbeelden.py` | - | 🔄 **LEGACY** | Basis voorbeelden systeem |
| `unified_voorbeelden.py` | - | ✅ **ACTIEF** | Unified voorbeelden API |
| `async_voorbeelden.py` | - | ✅ **ACTIEF** | Asynchrone voorbeelden laden |
| `cached_voorbeelden.py` | - | ✅ **ACTIEF** | Gecachte voorbeelden systeem |

🔍 **DUPLICATIE GEDETECTEERD**: Meerdere implementaties van voorbeelden systeem.

---

## 🔍 VALIDATIE LAYER - SRC/VALIDATION/ (5 bestanden, 3,277 LOC)

| Bestand | LOC | Status | Functionaliteit |
|---------|-----|---------|----------------|
| `definitie_validator.py` | - | ✅ **ACTIEF** | Hoofd definitie validatie systeem |
| `dutch_text_validator.py` | - | ✅ **ACTIEF** | Nederlandse tekst validatie |
| `input_validator.py` | - | ✅ **ACTIEF** | Input sanitization en validatie |
| `sanitizer.py` | - | ✅ **ACTIEF** | Text sanitization utilities |

---

## 🧪 TESTSYSTEEM - TESTS/ (59 bestanden, 21,297 LOC)

### 🔧 CORE TESTING INFRASTRUCTURE
| Category | Bestanden | Status | Functionaliteit |
|----------|-----------|---------|----------------|
| **Unit Tests** | 14 bestanden | ✅ **ACTIEF** | Unit testing voor individuele componenten |
| **Integration Tests** | 10 bestanden | ✅ **ACTIEF** | Integratie testing tussen services |
| **Services Tests** | 14 bestanden | ✅ **ACTIEF** | Service layer testing |
| **Functionality Tests** | 5 bestanden | ✅ **ACTIEF** | End-to-end functionaliteit testing |
| **Beveiliging Tests** | 2 bestanden | ✅ **ACTIEF** | Beveiliging validatie testing |
| **Rate Limiting Tests** | 9 bestanden | ✅ **ACTIEF** | Rate limiting systeem testing |
| **Prestaties Tests** | 2 bestanden | ✅ **ACTIEF** | Prestaties benchmark testing |
| **UI Tests** | 1 bestand | ✅ **ACTIEF** | User interface testing |

### 🛠️ MANUAL TESTING
| Bestand | Status | Functionaliteit |
|---------|---------|----------------|
| `manual_test_*.py` (6 bestanden) | ✅ **ACTIEF** | Handmatige test scripts voor debugging |

---

## 🤖 AUTOMATION - SCRIPTS/ (13 bestanden)

### 📊 CODE QUALITY & REVIEW
| Bestand | Status | Functionaliteit |
|---------|---------|----------------|
| `ai_code_reviewer.py` | ✅ **ACTIEF** | AI-powered code review systeem |
| `enhanced_ai_reviewer.py` | ✅ **ACTIEF** | Enhanced AI reviewer met meer features |
| `architecture_validator.py` | ✅ **ACTIEF** | Architecture validation en compliance |
| `architecture_sync.py` | ✅ **ACTIEF** | Architecture synchronization tools |

### 🚀 PERFORMANCE & BENCHMARKS
| Directory/Bestand | Status | Functionaliteit |
|-------------------|---------|----------------|
| `benchmarks/` | ✅ **ACTIEF** | Prestaties benchmarking scripts |
| `update_feature_status.py` | ✅ **ACTIEF** | Feature status tracking automation |

---

## 🧰 TOOLS & MAINTENANCE - TOOLS/ (3 bestanden)

| Bestand | Status | Functionaliteit |
|---------|---------|----------------|
| `run_maintenance.py` | ✅ **ACTIEF** | Maintenance runner voor automated tasks |
| `maintenance/fix_naming_consistency.py` | ✅ **ACTIEF** | Naming consistency fixer tool |

---

## 🏠 ROOT UTILITIES (8 bestanden, 851 LOC)

| Bestand | LOC | Status | Functionaliteit |
|---------|-----|---------|----------------|
| `analyze_dependencies.py` | 139 | ✅ **ACTIEF** | Service afhankelijkheid analysis tool |
| `afhankelijkheid_analysis.py` | 141 | ✅ **ACTIEF** | Circulaire afhankelijkheid detectie |
| `code_review_tool.py` | 164 | ✅ **ACTIEF** | Code review automation tool |
| `security_review.py` | 76 | ✅ **ACTIEF** | Beveiliging review utilities |
| `trace_prompt_decision.py` | 74 | ✅ **ACTIEF** | Debug tool voor AI prompt beslissingen |
| `test_categorie_complete_flow.py` | 143 | ✅ **ACTIEF** | Complete flow test voor categorieën |
| `test_legacy_activation.py` | 62 | ✅ **ACTIEF** | Legacy system activation tests |
| `test_ontological_integration.py` | 52 | ✅ **ACTIEF** | Ontological integration tests |

---

## 📈 USAGE & STATUS ANALYSE

### ✅ INTENSIEF GEBRUIKTE MODERNE CODE (HOOG PRIORITY)
1. **`src/services/`** - Kernarchitectuur, volledig actief
2. **`src/ui/tabbed_interface.py`** - Hoofd UI controller
3. **`src/toetsregels/`** - Volledig validatiesysteem (37/38 regels)
4. **`src/database/`** - Actieve database layer
5. **`src/utils/`** - Hergebruikte utilities
6. **`tests/`** - Uitgebreid testsysteem

### ⚠️ LEGACY/TRANSITIONAL CODE (GEMIDDELD PRIORITY)
1. **`src/ui/components.py`** - Wordt vervangen door components/
2. **`src/voorbeelden/voorbeelden.py`** - Legacy voorbeelden systeem
3. **`src/config/`** - Mix van legacy en moderne configuratie

### 🔍 MOGELIJKE DUPLICATIES (CONSOLIDATIE NODIG)
1. **Resilience Systems** - 4 verschillende implementaties in utils/
2. **Voorbeelden Systems** - 4 verschillende implementaties
3. **Code Review Tools** - 2 verschillende AI reviewers

### 🚨 KRITIEKE ISSUES
1. **`INT-05` ONTBREEKT** - Validatieregel niet geïmplementeerd
2. **Web Lookup UI** - Backend werkt, UI integratie faalt
3. **Bare Exceptions** - 8 bare except clauses (security risk)
4. **Import Errors** - E402 import errors in legacy modules

### 💡 ARCHITECTUUR KWALITEIT
- **Sterke service-oriented architecture** met clean afhankelijkheid injection
- **Uitgebreid validatiesysteem** met 37/38 geïmplementeerde regels
- **Moderne testing approach** met 21K+ LOC aan tests
- **Good separation of concerns** tussen UI, services, en domain logic

---

## 🎯 AANBEVELINGEN

### 1. **CONSOLIDATIE PRIORITEITEN**
- Merge resilience implementaties naar één unified systeem
- Consolideer voorbeelden systems naar unified API
- Elimineer legacy components waar mogelijk

### 2. **MISSING IMPLEMENTATIONS**
- Implementeer ontbrekende INT-05 validatieregel
- Fix WebLookup UI integratie
- Vervang bare exceptions met specifieke error handling

### 3. **ARCHITECTUUR VERBETERING**
- Continue service architecture migration
- Improve afhankelijkheid injection patterns
- Enhance error handling consistency

Dit overzicht toont een **professionele, uitgebreide codebase** met sterke architecturale fundamenten maar met enkele legacy elementen die consolidatie behoeven.
