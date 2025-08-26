# ARCHIVED - Services Directory Dependency Analysis

**ARCHIVE NOTICE**: This document has been archived on 2025-08-26 as it references the deprecated UnifiedDefinitionGenerator. The current architecture uses DefinitionOrchestrator as the central orchestration service.

**Original Date**: Unknown
**Reason for Archive**: References outdated architecture components
**Current Replacement**: See CURRENT_ARCHITECTURE_OVERVIEW.md for the updated service architecture

---

# Services Directory Dependency Analysis

## Import Count Summary

### 1. unified_definition_generator.py
**Total imports: 24 unique imports**

#### External dependencies (7):
- `asyncio`
- `logging`
- `dataclasses` (dataclass)
- `enum` (Enum)
- `typing` (Any, Dict, List, Optional, Tuple)

#### Service layer imports (8):
- `services.interfaces` (Definition, DefinitionGeneratorInterface, GenerationRequest)
- `services.definition_generator_config` (UnifiedGeneratorConfig)
- `services.definition_generator_context` (HybridContextManager)
- `services.definition_generator_prompts` (UnifiedPromptBuilder)
- `services.definition_generator_monitoring` (get_monitor)
- `services.definition_generator_enhancement` (DefinitionEnhancer)
- `services.modern_web_lookup_service` (ModernWebLookupService)

#### Other module imports (9):
- `utils.exceptions` (handle_api_error)
- `opschoning.opschoning` (opschonen)
- `prompt_builder.prompt_builder` (stuur_prompt_naar_gpt)
- `domain.ontological_categories` (OntologischeCategorie)
- `hybrid_context.hybrid_context_engine` (get_hybrid_context_engine) - conditional
- Legacy web_lookup imports (commented out)

### 2. definition_orchestrator.py
**Total imports: 11 unique imports**

#### External dependencies (6):
- `asyncio`
- `logging`
- `dataclasses` (dataclass, field)
- `datetime` (datetime)
- `enum` (Enum)
- `typing` (Any, Dict, List, Optional)

#### Service layer imports (5):
- `services.interfaces` (Definition, DefinitionGeneratorInterface, DefinitionOrchestratorInterface, DefinitionRepositoryInterface, DefinitionResponse, DefinitionValidatorInterface, GenerationRequest, ValidationResult)
- `services.modern_web_lookup_service` (ModernWebLookupService) - conditional

#### Other module imports (0):
- `voorbeelden.unified_voorbeelden` (genereer_alle_voorbeelden_async) - conditional

### 3. definition_repository.py
**Total imports: 13 unique imports**

#### External dependencies (7):
- `sqlite3`
- `logging`
- `datetime` (datetime)
- `pathlib` (Path)
- `typing` (Any, Dict, List, Optional)
- `json`

#### Service layer imports (2):
- `services.interfaces` (Definition, DefinitionRepositoryInterface)

#### Other module imports (4):
- `database.base_repository` (BaseRepository)
- `database.database` (get_database_manager, DatabaseManager)
- `utils.exceptions` (handle_database_error)
- `utils.logger` (log_execution_time) - conditional

### 4. definition_validator.py
**Total imports: 12 unique imports**

#### External dependencies (6):
- `logging`
- `concurrent.futures` (ThreadPoolExecutor)
- `dataclasses` (dataclass)
- `datetime` (datetime)
- `typing` (Any, Dict, List, Optional)

#### Service layer imports (3):
- `services.interfaces` (Definition, DefinitionValidatorInterface, ValidationResult)
- Toetsregels integration (conditional imports)

#### Other module imports (3):
- Various toetsregels imports (conditional)

### 5. Other Services Summary

#### modern_web_lookup_service.py (17 imports)
- Heavy external dependencies (aiohttp, BeautifulSoup, etc.)
- Clean interface implementation
- No cross-service dependencies

#### cleaning_service.py (5 imports)
- Minimal dependencies
- Clean interface implementation
- Uses opschoning module

#### definition_generator_*.py files
- Supporting modules for the generator
- Low external dependencies
- Well encapsulated

## Dependency Health Analysis

### Good Patterns ✅
1. **Interface-based design**: All major services implement interfaces
2. **Minimal cross-service dependencies**: Services mostly independent
3. **Conditional imports**: Used to prevent circular dependencies
4. **Clean external dependencies**: Well-defined external library usage

### Areas of Concern ⚠️
1. **unified_definition_generator.py has too many imports (24)**: Consider breaking down
2. **Direct module imports**: Some services import from other modules directly
3. **Conditional imports**: While solving circular deps, they indicate design issues

### Recommendations 🔧
1. **Reduce unified_definition_generator.py complexity**: Split into smaller services
2. **Use dependency injection**: Instead of direct imports
3. **Create facades**: For complex external integrations
4. **Standardize error handling**: Consistent exception handling across services

## Import Visualization

```
unified_definition_generator.py (24 imports)
├── External (7)
├── Service Layer (8)
└── Other Modules (9)

definition_orchestrator.py (11 imports)
├── External (6)
├── Service Layer (5)
└── Other Modules (0)

definition_repository.py (13 imports)
├── External (7)
├── Service Layer (2)
└── Other Modules (4)
```

## Service Interaction Matrix

| Service | Depends On | Used By |
|---------|------------|----------|
| unified_definition_generator | config, context, prompts, monitoring, enhancement, web_lookup | orchestrator |
| definition_orchestrator | generator, validator, repository, web_lookup | UI/API |
| definition_repository | database, base_repository | orchestrator, all services |
| definition_validator | toetsregels | orchestrator |
| modern_web_lookup_service | none | generator, orchestrator |
| cleaning_service | opschoning | generator |
