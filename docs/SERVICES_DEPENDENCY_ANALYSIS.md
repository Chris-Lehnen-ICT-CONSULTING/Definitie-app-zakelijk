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
**Total imports: 9 unique imports**

#### External dependencies (6):
- `json`
- `logging`
- `sqlite3`
- `contextlib` (contextmanager)
- `datetime` (datetime)
- `typing` (Any, Dict, List, Optional)

#### Service layer imports (1):
- `services.interfaces` (Definition, DefinitionRepositoryInterface)

#### Other module imports (2):
- `database.definitie_repository` (DefinitieRecord, DefinitieRepository as LegacyRepository, DefinitieStatus, SourceType)

### 4. definition_validator.py
**Total imports: 8 unique imports**

#### External dependencies (3):
- `logging`
- `dataclasses` (dataclass, field)
- `typing` (Any, Dict, List, Optional, Set)

#### Service layer imports (1):
- `services.interfaces` (Definition, DefinitionValidatorInterface, ValidationResult)

#### Other module imports (2):
- `toetsregels.manager` (get_toetsregel_manager)
- `validation.definitie_validator` (DefinitieValidator)

### 5. container.py
**Total imports: 11 unique imports**

#### External dependencies (3):
- `logging`
- `os`
- `typing` (Any, Dict, Optional)

#### Service layer imports (8):
- `services.unified_definition_generator` (UnifiedDefinitionGenerator)
- `services.definition_generator_config` (UnifiedGeneratorConfig, GPTConfig, QualityConfig, MonitoringConfig)
- `services.definition_orchestrator` (DefinitionOrchestrator, OrchestratorConfig)
- `services.definition_repository` (DefinitionRepository)
- `services.definition_validator` (DefinitionValidator, ValidatorConfig)
- `services.interfaces` (DefinitionGeneratorInterface, DefinitionOrchestratorInterface, DefinitionRepositoryInterface, DefinitionValidatorInterface, WebLookupServiceInterface)
- `services.modern_web_lookup_service` (ModernWebLookupService)

## Dependency Matrix

| Service | Generator | Orchestrator | Repository | Validator | Container | Interfaces | External Modules |
|---------|-----------|--------------|------------|-----------|-----------|------------|------------------|
| **unified_definition_generator** | - | ❌ | ❌ | ❌ | ❌ | ✅ | utils, opschoning, prompt_builder, domain, hybrid_context |
| **definition_orchestrator** | ✅ (interface) | - | ✅ (interface) | ✅ (interface) | ❌ | ✅ | voorbeelden |
| **definition_repository** | ❌ | ❌ | - | ❌ | ❌ | ✅ | database |
| **definition_validator** | ❌ | ❌ | ❌ | - | ❌ | ✅ | toetsregels, validation |
| **container** | ✅ | ✅ | ✅ | ✅ | - | ✅ | ❌ |

## Circular Dependencies

**No circular dependencies detected** ✅

The architecture follows a clean dependency pattern:
1. All services depend on `interfaces` (good abstraction)
2. `container` depends on all concrete implementations (expected for DI)
3. `orchestrator` depends on other services through interfaces only (good practice)
4. No service depends on `container` (proper inversion of control)

## God Object Analysis

### 1. **unified_definition_generator.py** - ⚠️ POTENTIAL GOD OBJECT
- **483 lines of code**
- **24 unique imports**
- **Multiple responsibilities:**
  - Configuration management
  - Component initialization
  - Context building (multiple strategies)
  - Prompt building
  - Generation logic
  - Enhancement
  - Caching
  - Monitoring
  - Statistics tracking
  - Legacy compatibility

**Recommendation**: This service violates Single Responsibility Principle. Consider breaking down into:
- GenerationEngine (core generation logic)
- ContextBuilder (context strategies)
- GenerationEnhancer (enhancement logic)
- GenerationMonitor (monitoring/stats)

### 2. **definition_orchestrator.py** - ✅ WELL-DESIGNED
- **564 lines of code**
- **11 unique imports**
- Clear single responsibility: orchestrating the workflow
- Delegates actual work to injected services
- Good separation of concerns

### 3. **definition_repository.py** - ✅ WELL-DESIGNED
- **428 lines of code**
- **9 unique imports**
- Single responsibility: data persistence
- Clean adapter pattern over legacy repository
- No business logic contamination

### 4. **definition_validator.py** - ✅ WELL-DESIGNED
- **349 lines of code**
- **8 unique imports**
- Single responsibility: validation logic
- Clean integration with existing validation rules
- Good abstraction over legacy validator

### 5. **container.py** - ✅ WELL-DESIGNED
- **283 lines of code**
- **11 unique imports**
- Single responsibility: dependency injection
- Clean factory pattern
- Good configuration management

## Key Findings

1. **Clean Architecture**: The services follow dependency inversion principle well, depending on interfaces rather than concrete implementations.

2. **No Circular Dependencies**: The dependency graph is acyclic, which is excellent for maintainability.

3. **God Object Issue**: The `unified_definition_generator.py` shows signs of being a God Object with too many responsibilities and dependencies.

4. **Good Abstraction**: All services properly use the interface layer for communication.

5. **Legacy Integration**: Services cleanly wrap legacy functionality without exposing it to the service layer.

## Recommendations

1. **Refactor unified_definition_generator.py**:
   - Extract context building into a separate service
   - Extract monitoring/statistics into a separate service
   - Extract enhancement logic into its own service
   - Keep only core generation logic in the main service

2. **Consider extracting common patterns**:
   - Statistics tracking appears in multiple services
   - Configuration patterns could be standardized

3. **Reduce external dependencies**:
   - The generator has many direct dependencies on other modules
   - Consider using more dependency injection for these

4. **Standardize error handling**:
   - Each service has its own error handling approach
   - Consider a common error handling strategy