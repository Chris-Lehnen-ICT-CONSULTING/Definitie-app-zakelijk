# Duplicate Code Analysis Report

## Executive Summary
This report identifies duplicate and similar code patterns in the DefinitieAgent codebase. Several areas show redundancy that could be consolidated to improve maintainability.

## 1. Multiple Definition Generator Implementations

### Found Duplicates:
- **`src/definitie_generator/generator.py`** - Original implementation
- **`src/generation/definitie_generator.py`** - New enhanced implementation

### Analysis:
Both files implement definition generation with OpenAI integration but use different approaches:
- Original: Direct OpenAI client initialization, simpler structure
- New: Lazy loading of OpenAI, advanced features (hybrid context, ontological categories)

### Recommendation:
Consolidate into single module, keeping the advanced features from the new implementation.

## 2. Multiple Voorbeelden (Example) Generation Modules

### Found Duplicates:
- **`src/voorbeelden/voorbeelden.py`** - Original synchronous implementation
- **`src/voorbeelden/async_voorbeelden.py`** - Async version for performance
- **`src/voorbeelden/cached_voorbeelden.py`** - Cached version
- **`src/voorbeelden/unified_voorbeelden.py`** - Unified system combining all approaches

### Analysis:
Each module implements the same functionality with different optimization strategies:
- All generate example sentences, synonyms, antonyms, and explanations
- Different approaches: sync, async, cached, unified
- Multiple OpenAI client initializations

### Recommendation:
Use only `unified_voorbeelden.py` which already combines all approaches. Remove the other three modules.

## 3. Multiple OpenAI API Integration Points

### Found Instances:
- **7 different files** initialize their own OpenAI client:
  - `src/ai_toetser/core.py`
  - `src/prompt_builder/prompt_builder.py`
  - `src/voorbeelden/voorbeelden.py`
  - `src/voorbeelden/cached_voorbeelden.py`
  - `src/definitie_generator/generator.py`
  - `src/generation/definitie_generator.py`
  - `src/utils/async_api.py` (AsyncOpenAI)

### Recommendation:
Create a single OpenAI client manager that provides both sync and async clients to all modules.

## 4. Duplicate Config Loading Mechanisms

### Found Patterns:
- **`src/config/config_loader.py`** - Original config loading functions
- **`src/config/config_manager.py`** - New singleton ConfigManager
- **`src/config/toetsregel_manager.py`** - Specialized for toetsregels
- **`src/config/toetsregels_adapter.py`** - Adapter pattern for backward compatibility

### Analysis:
Multiple ways to load the same configuration files, especially `toetsregels.json`.

### Recommendation:
Standardize on ConfigManager and ToetsregelManager, remove legacy loaders.

## 5. Multiple Validation/Toetsing Implementations

### Found Duplicates:
- **`src/ai_toetser/toetser.py`** - Simple forbidden words checker
- **`src/ai_toetser/modular_toetser.py`** - New modular validation orchestrator
- **`src/ai_toetser/core.py`** - Original monolithic validator
- **`src/validation/definitie_validator.py`** - Intelligent validation with feedback
- **`src/validatie_toetsregels/validator.py`** - Rule validation

### Analysis:
Different validation approaches for similar purposes:
- Some focus on forbidden words
- Others implement full rule-based validation
- Overlap in functionality but different architectures

### Recommendation:
Consolidate around the modular architecture, keeping specialized validators as plugins.

## 6. Empty Placeholder Files

### Found:
- **`src/web_lookup/bron_lookup.py`** - 0 bytes
- **`src/web_lookup/definitie_lookup.py`** - 0 bytes

### Recommendation:
Remove empty files or implement planned functionality.

## 7. Test File Duplicates

### Found in Root:
- **`test_ai_content_generation.py`** - In root directory
- **`test_voorbeelden_module.py`** - In root directory
- **`test_metadata_fields.py`** - In root directory

### Recommendation:
Move all test files to `tests/` directory for consistency.

## Priority Actions

1. **High Priority**: Consolidate OpenAI client initialization
2. **High Priority**: Use only `unified_voorbeelden.py` for example generation
3. **Medium Priority**: Merge definition generators into single module
4. **Medium Priority**: Standardize config loading approach
5. **Low Priority**: Clean up empty files and organize test files

## Code Consolidation Benefits

- Reduced maintenance overhead
- Consistent behavior across modules
- Better resource management (single OpenAI client)
- Easier testing and debugging
- Clearer code organization