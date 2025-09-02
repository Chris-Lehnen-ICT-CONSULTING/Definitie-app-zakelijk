---
canonical: false
status: archived
last_verified: 2025-09-02
notes: Historisch (V1). Voor actuele afhankelijkheden: zie Modular Validation Service en V2 orchestrator in Solution Architecture.
---

# Services Dependency Graph (Historisch – V1)

## Visual Dependency Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         External Modules                          │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐            │
│  │   utils     │  │  opschoning  │  │prompt_builder│            │
│  └──────┬──────┘  └──────┬───────┘  └──────┬──────┘            │
│         │                 │                  │                    │
│  ┌──────▼─────────────────▼─────────────────▼──────┐            │
│  │          unified_definition_generator            │            │
│  │                                                  │            │
│  │  Components:                                     │            │
│  │  - HybridContextManager                         │            │
│  │  - UnifiedPromptBuilder                         │            │
│  │  - DefinitionEnhancer                           │            │
│  │  - Monitor                                      │            │
│  └──────────────────────┬──────────────────────────┘            │
│                         │                                        │
└─────────────────────────┼────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Service Layer (Interfaces)                    │
│  ┌────────────────────────────────────────────────────────┐    │
│  │                      interfaces.py                      │    │
│  │  - DefinitionGeneratorInterface                       │    │
│  │  - DefinitionValidatorInterface                       │    │
│  │  - DefinitionRepositoryInterface                      │    │
│  │  - DefinitionOrchestratorInterface                    │    │
│  │  - WebLookupServiceInterface                          │    │
│  └───────┬──────────┬──────────┬──────────┬─────────────┘    │
│          │          │          │          │                    │
│          ▼          ▼          ▼          ▼                    │
│  ┌───────────┐ ┌───────────┐ ┌────────────┐ ┌──────────────┐ │
│  │Generator  │ │Validator  │ │Repository  │ │Web Lookup    │ │
│  │Service    │ │Service    │ │Service     │ │Service       │ │
│  └─────┬─────┘ └─────┬─────┘ └─────┬──────┘ └──────┬───────┘ │
│        │             │             │                │          │
└────────┼─────────────┼─────────────┼────────────────┼──────────┘
         │             │             │                │
         ▼             ▼             ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    definition_orchestrator.py                    │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐           │
│  │  Generator  │  │  Validator  │  │  Repository  │           │
│  │ (interface) │  │ (interface) │  │ (interface)  │           │
│  └─────────────┘  └─────────────┘  └──────────────┘           │
│                                                                  │
│  Orchestrates: Generation → Validation → Enrichment → Storage   │
└──────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                         container.py                             │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Dependency Injection Container               │   │
│  │                                                          │   │
│  │  Creates and manages:                                    │   │
│  │  - UnifiedDefinitionGenerator                           │   │
│  │  - DefinitionValidator                                  │   │
│  │  - DefinitionRepository                                 │   │
│  │  - DefinitionOrchestrator                               │   │
│  │  - ModernWebLookupService                               │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Dependency Flow Details

### 1. External → Service Layer
```
External Modules ──► unified_definition_generator ──► interfaces
                                                         │
toetsregels ──────► definition_validator ───────────────┤
                                                         │
database ──────────► definition_repository ──────────────┤
                                                         │
voorbeelden ───────► definition_orchestrator ───────────┘
```

### 2. Service Layer Internal Dependencies
```
interfaces <──── All Services depend on interfaces
    │
    ├──► DefinitionGeneratorInterface ◄─── implemented by ─── UnifiedDefinitionGenerator
    ├──► ValidationServiceInterface ◄──── implemented by ─── ModularValidationService (V2)
    ├──► DefinitionRepositoryInterface ◄── implemented by ─── DefinitionRepository
    ├──► DefinitionOrchestratorInterface ◄─ implemented by ─── DefinitionOrchestrator
    └──► WebLookupServiceInterface ◄────── implemented by ─── ModernWebLookupService
```

### 3. Orchestrator Dependencies (Through Interfaces)
```
DefinitionOrchestrator
    │
    ├──► DefinitionGeneratorInterface (injected)
    ├──► DefinitionValidatorInterface (injected)
    └──► DefinitionRepositoryInterface (injected)
```

### 4. Container Dependencies (Concrete Implementations)
```
ServiceContainer
    │
    ├──► UnifiedDefinitionGenerator (creates)
    ├──► ModularValidationService (creates)
    ├──► DefinitionRepository (creates)
    ├──► DefinitionOrchestrator (creates with dependencies)
    └──► ModernWebLookupService (creates)
```

## Complexity Analysis

### Service Complexity Scores (based on dependencies and responsibilities)

| Service | Import Count | Dependency Count | Responsibility Count | Complexity Score |
|---------|--------------|------------------|---------------------|------------------|
| unified_definition_generator | 24 | 9 external modules | 10+ | **HIGH (8/10)** |
| definition_orchestrator | 11 | 3 services (via interface) | 4 | **MEDIUM (5/10)** |
| definition_repository | 9 | 1 external module | 2 | **LOW (3/10)** |
| definition_validator | 8 | 2 external modules | 2 | **LOW (3/10)** |
| container | 11 | 4 services (concrete) | 2 | **MEDIUM (4/10)** |

## God Object Pattern Detection

### unified_definition_generator.py - **GOD OBJECT DETECTED** 🚨

**Evidence:**
1. **High import count**: 24 unique imports (highest among all services)
2. **Multiple concerns**:
   - Configuration management
   - Context building (3+ strategies)
   - Prompt generation
   - API communication
   - Result enhancement
   - Caching logic
   - Monitoring/statistics
   - Legacy compatibility
3. **Deep module coupling**: Direct dependencies on 9+ external modules
4. **Large surface area**: 483 lines with 15+ public/private methods

**Impact:**
- Hard to test in isolation
- Changes ripple across multiple features
- Difficult to understand full behavior
- High cognitive load for maintenance

### Recommended Refactoring

```
Current (God Object):
UnifiedDefinitionGenerator
    ├── Configuration
    ├── Context Building
    ├── Prompt Building
    ├── Generation
    ├── Enhancement
    ├── Caching
    ├── Monitoring
    └── Statistics

Proposed (Single Responsibility):
GenerationService
    └── generate()

ContextService
    └── build_context()

PromptService
    └── build_prompt()

EnhancementService
    └── enhance()

CacheService
    └── get() / set()

MonitoringService
    └── track()
```
