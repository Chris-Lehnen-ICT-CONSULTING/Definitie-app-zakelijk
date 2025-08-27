# Prompt System Runtime Analysis

## Executive Summary

The prompt system has multiple layers and strategies, but at runtime **the modular system IS being used** through a complex chain of adapters and facades. However, this is wrapped in multiple layers of backwards compatibility, creating confusion about what's actually executing.

## Runtime Flow Analysis

### 1. Entry Point Flow
```
UI (tabbed_interface.py)
  → ServiceAdapter (service_factory.py)
    → ServiceContainer.orchestrator() [Can be V1 or V2]
      → DefinitionOrchestratorV2 (if USE_V2_ORCHESTRATOR=true)
        → PromptServiceV2
          → UnifiedPromptBuilder
            → ModularPromptAdapter (via ModularPromptBuilder alias)
              → PromptOrchestrator + 12 modules
```

### 2. Configuration Control Points

#### Environment Variables
- `USE_V2_ORCHESTRATOR`: Controls V1 vs V2 orchestrator (default: false)
- `USE_NEW_SERVICES`: Controls service architecture (default: true in UI)
- `APP_ENV`: Controls config profile (production/development/testing)

#### Key Decision Points
1. **ServiceContainer.orchestrator()** (line 198-244):
   - Checks `USE_V2_ORCHESTRATOR` env var
   - Falls back to V1 orchestrator by default
   - V2 creates PromptServiceV2 which uses modular system

2. **UnifiedPromptBuilder._select_strategy()** (line 624-663):
   - ALWAYS selects "modular" if available (line 628)
   - Falls back to legacy only if modular unavailable
   - This means modular is ALWAYS used when available

### 3. Actual Runtime Behavior

#### When V2 Orchestrator is Used:
1. PromptServiceV2 creates UnifiedPromptBuilder
2. UnifiedPromptBuilder ALWAYS selects ModularPromptBuilder
3. ModularPromptBuilder is an alias for ModularPromptAdapter
4. ModularPromptAdapter creates PromptOrchestrator with 12 modules
5. **Result: Full modular system with all 12 modules**

#### When V1 Orchestrator is Used:
1. DefinitionOrchestrator uses UnifiedPromptBuilder directly
2. UnifiedPromptBuilder STILL selects ModularPromptBuilder
3. Same flow as above
4. **Result: Still uses modular system!**

### 4. Dead Code Paths

#### Never Reached:
- `core_instructions_v2.py` - Never imported or used
- `LegacyPromptBuilder` - Only used if modular unavailable (never happens)
- `BasicPromptBuilder` - Only fallback if modular fails
- `ContextAwarePromptBuilder` - Never selected due to modular priority

#### Facades and Aliases:
- `ModularPromptBuilder` class is just an alias to `ModularPromptAdapter`
- Original `modular_prompt_builder.py` backed up, replaced with facade
- Multiple layers of backwards compatibility wrappers

### 5. The Modular System IS Active

Evidence the modular system is running:
1. `_select_strategy()` always returns "modular" when available
2. `ModularPromptAdapter` initializes `PromptOrchestrator` with 12 modules
3. Logs show "ModularPromptAdapter geïnitialiseerd"
4. All 12 modules are registered and executed

The confusion comes from:
- Multiple abstraction layers
- Backwards compatibility facades
- Module aliasing (ModularPromptBuilder → ModularPromptAdapter)
- V1 orchestrator is default but still uses modular prompts

### 6. Performance Impact

The layered architecture creates overhead:
```
UI Request
  → ServiceAdapter (sync wrapper around async)
    → Orchestrator (async/sync conversion)
      → PromptService (another layer)
        → UnifiedPromptBuilder (strategy selection)
          → ModularPromptAdapter (facade)
            → PromptOrchestrator (actual implementation)
              → 12 Modules (parallel execution possible)
```

Each layer adds:
- Function call overhead
- Async/sync conversions
- Object creation
- Logging statements

### 7. Recommendations

1. **Remove Abstraction Layers**: The facades and adapters add confusion without value
2. **Direct Module Usage**: Call PromptOrchestrator directly without 5 intermediate layers
3. **Clean Dead Code**: Remove unused prompt builders and strategies
4. **Simplify Configuration**: One flag to control prompt strategy, not multiple
5. **Document Reality**: Update docs to reflect actual runtime behavior

## Conclusion

The modular prompt system IS being used at runtime, but it's wrapped in so many layers of abstraction and backwards compatibility that it's hard to see. The system would benefit from removing these unnecessary layers and calling the modular system directly.
