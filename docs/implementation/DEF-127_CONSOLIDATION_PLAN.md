# DEF-127: Module Consolidation Plan
## Reducing Cognitive Load from 19 Modules to <15 Core Concepts

### Current State Analysis (19 Modules)

#### Module Categories and Overlaps

1. **Validation Rule Modules (7 modules - MAJOR OVERLAP)**
   - arai_rules_module.py - General quality guidelines
   - con_rules_module.py - Context-specific rules
   - ess_rules_module.py - Essence validation
   - integrity_rules_module.py - Completeness validation
   - sam_rules_module.py - Coherence between terms
   - structure_rules_module.py - Grammatical/structural validation
   - ver_rules_module.py - Grammatical form validation

   **Overlap**: All generate validation rules with similar structure, just different categories

2. **Language & Grammar Modules (3 modules - OVERLAP)**
   - grammar_module.py - Grammar and writing style
   - structure_rules_module.py - Grammatical structure (STR rules)
   - ver_rules_module.py - Grammatical form (VER rules)

   **Overlap**: Grammar and structure_rules have significant overlap

3. **Output & Format Modules (2 modules - PARTIAL OVERLAP)**
   - output_specification_module.py - Output format and limits
   - template_module.py - Definition templates and patterns

   **Overlap**: Both deal with formatting, could be merged

4. **Context Processing (2 modules - KEEP SEPARATE)**
   - context_awareness_module.py - Context richness scoring
   - semantic_categorisation_module.py - Ontological category guidance

   **Rationale**: Different responsibilities, low overlap

5. **Core Instruction Modules (3 modules - KEEP)**
   - expertise_module.py - Expert role definition
   - definition_task_module.py - Final instructions and checklist
   - error_prevention_module.py - Quality instructions

   **Rationale**: Core functionality with distinct purposes

6. **Metrics & Monitoring (1 module - KEEP)**
   - metrics_module.py - Quality metrics and scoring

   **Rationale**: Unique functionality

### Proposed Consolidation (<15 Concepts)

#### Phase 1: Merge Validation Rules (7 → 2)
**Before**: 7 separate validation rule modules
**After**: 2 consolidated modules

1. **unified_validation_rules_module.py**
   - Combines: arai, con, ess, sam, integrity rules
   - Why: All have same structure, just different rule categories
   - Method: Single module with category parameter

2. **linguistic_rules_module.py**
   - Combines: structure_rules (STR) + ver_rules (VER) + grammar
   - Why: All deal with linguistic/grammatical validation
   - Method: Unified grammar and form validation

#### Phase 2: Merge Output Formatting (2 → 1)
**Before**: output_specification + template modules
**After**: 1 consolidated module

3. **output_format_module.py**
   - Combines: output_specification + template
   - Why: Both handle output formatting and structure
   - Method: Single module for all output concerns

#### Phase 3: Keep Core Modules (8 modules remain)
4. **expertise_module.py** - Core role definition (KEEP)
5. **context_awareness_module.py** - Context processing (KEEP)
6. **semantic_categorisation_module.py** - Ontological guidance (KEEP)
7. **error_prevention_module.py** - Quality instructions (KEEP)
8. **definition_task_module.py** - Task instructions (KEEP)
9. **metrics_module.py** - Quality metrics (KEEP)

#### Infrastructure (Not counted in 15 limit)
- base_module.py - Base class (infrastructure)
- prompt_orchestrator.py - Orchestration (infrastructure)
- __init__.py - Package initialization (infrastructure)

### Final Module Count: 9 Core Concepts (< 15 ✓)

### Implementation Strategy

#### Step 1: Create Unified Validation Module
```python
class UnifiedValidationRulesModule(BasePromptModule):
    """Unified module for all validation rule categories."""

    def __init__(self, categories: list[str] = None):
        # Load rules for specified categories
        # Default to all: ['ARAI', 'CON', 'ESS', 'SAM', 'INT']
```

#### Step 2: Create Linguistic Rules Module
```python
class LinguisticRulesModule(BasePromptModule):
    """Combined linguistic, grammar, and form validation."""

    def __init__(self):
        # Combines STR, VER, and general grammar rules
```

#### Step 3: Create Output Format Module
```python
class OutputFormatModule(BasePromptModule):
    """Unified output formatting and templates."""

    def __init__(self):
        # Combines output specs and templates
```

#### Step 4: Update Orchestrator
- Update PromptOrchestrator to use new consolidated modules
- Maintain same output quality with fewer modules

### Migration Path

1. **Create new modules** alongside existing ones
2. **Test new modules** to ensure same output quality
3. **Update orchestrator** to use new modules
4. **Deprecate old modules** (comment out imports)
5. **Remove old modules** after verification

### Benefits of Consolidation

1. **Reduced Cognitive Load**: 19 → 9 modules (53% reduction)
2. **Less Duplication**: Single source for validation rules
3. **Easier Maintenance**: Fewer files to update
4. **Clearer Structure**: Logical grouping by function
5. **Better Performance**: Fewer module initializations

### Validation Strategy

To ensure no functionality is lost:
1. Generate prompts with old system
2. Generate prompts with new system
3. Compare outputs - should be identical
4. Run all existing tests
5. Add new integration tests for consolidated modules

### Risk Mitigation

- Keep old modules initially (just unused)
- Extensive testing before removal
- Document all consolidation decisions
- Maintain backward compatibility in outputs