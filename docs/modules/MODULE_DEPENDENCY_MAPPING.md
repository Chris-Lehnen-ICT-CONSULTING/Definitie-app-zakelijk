# Module Dependency Mapping

## Overzicht
Dit document beschrijft de dependencies tussen alle prompt modules en hun executie volgorde.

## Module Architectuur

### 8 Core Prompt Modules

1. **ExpertiseModule**
   - Verantwoordelijkheid: Expert rol definitie en basis instructies
   - Output: Rol beschrijving, taak specificatie
   - Dependencies: Geen
   - Maps to: Component 1 (deel 1)

2. **OutputSpecificationModule**
   - Verantwoordelijkheid: Output format requirements en woordsoort advies
   - Output: Format vereisten, woordsoort-specifiek advies
   - Dependencies: Geen
   - Maps to: Component 1 (deel 2)

3. **ContextAwarenessModule**
   - Verantwoordelijkheid: Verwerk organisatorische en domein context
   - Output: Context sectie met organisatie/domein info
   - Dependencies: Geen
   - Maps to: Component 2

4. **SemanticCategorisationModule**
   - Verantwoordelijkheid: ESS-02 ontologische categorie instructies
   - Output: Category-specific guidance voor type/proces/resultaat/exemplaar
   - Dependencies: Geen (maar gebruikt context metadata)
   - Maps to: Component 3

5. **QualityRulesModule**
   - Verantwoordelijkheid: Alle 24 validatie/toetsregels
   - Output: Gestructureerde validatieregels met voorbeelden
   - Dependencies: Geen
   - Maps to: Component 4

6. **ErrorPreventionModule**
   - Verantwoordelijkheid: Verboden patronen en veelgemaakte fouten
   - Output: Context-aware verboden lijst
   - Dependencies: ContextAwarenessModule (voor context-specifieke verboden)
   - Maps to: Component 5

7. **DefinitionTaskModule**
   - Verantwoordelijkheid: Finale instructies, checklist en metadata
   - Output: Opdracht formulering, quality checks, traceerbaarheid
   - Dependencies: SemanticCategorisationModule (voor categorie in checks)
   - Maps to: Component 6

8. **GrammarModule**
   - Verantwoordelijkheid: Grammaticale regels en schrijfstijl
   - Output: Taalkundige richtlijnen
   - Dependencies: OutputSpecificationModule (voor woordsoort info)
   - Maps to: Nieuw (niet in legacy)

### Orchestrator

**PromptOrchestrator**
- Verantwoordelijkheid: Coördineer alle modules, beheer executie flow
- Dependencies: Alle 8 modules

## Dependency Graph

```
┌─────────────────────┐     ┌──────────────────────────┐     ┌────────────────────────┐
│  ExpertiseModule    │     │ OutputSpecificationModule │     │ ContextAwarenessModule │
│  (geen deps)        │     │ (geen deps)              │     │ (geen deps)            │
└─────────────────────┘     └────────────┬─────────────┘     └───────────┬────────────┘
                                         │                                 │
                                         ▼                                 ▼
                            ┌─────────────────────┐            ┌───────────────────────┐
                            │   GrammarModule    │            │ ErrorPreventionModule │
                            │ (deps: OutputSpec) │            │ (deps: Context)       │
                            └─────────────────────┘            └───────────────────────┘

┌──────────────────────────────┐                      ┌─────────────────────┐
│ SemanticCategorisationModule │                      │  QualityRulesModule │
│ (geen deps, wel context)     │                      │  (geen deps)        │
└────────────┬─────────────────┘                      └─────────────────────┘
             │
             ▼
┌─────────────────────────┐
│  DefinitionTaskModule   │
│ (deps: SemanticCat)     │
└─────────────────────────┘

                    Alle modules
                         │
                         ▼
              ┌───────────────────┐
              │ PromptOrchestrator │
              └───────────────────┘
```

## Executie Volgorde

### Parallelle Executie Mogelijk (Fase 1)
Deze modules hebben geen dependencies en kunnen parallel draaien:
1. ExpertiseModule
2. OutputSpecificationModule
3. ContextAwarenessModule
4. SemanticCategorisationModule
5. QualityRulesModule

### Sequentiële Executie Vereist (Fase 2)
Deze modules zijn afhankelijk van outputs uit Fase 1:
6. GrammarModule (needs OutputSpecificationModule)
7. ErrorPreventionModule (needs ContextAwarenessModule)
8. DefinitionTaskModule (needs SemanticCategorisationModule)

### Suggested Execution Order
```
1. Start: Initialize ModuleContext with begrip, enriched_context, config
2. Fase 1 (Parallel):
   - Execute ExpertiseModule
   - Execute OutputSpecificationModule
   - Execute ContextAwarenessModule
   - Execute SemanticCategorisationModule
   - Execute QualityRulesModule
3. Fase 2 (Sequential based on deps):
   - Execute GrammarModule
   - Execute ErrorPreventionModule
   - Execute DefinitionTaskModule
4. End: Combine all outputs in order
```

## Inter-Module Communication

### Shared State Keys
Modules communiceren via `ModuleContext.shared_state`:

- `word_type`: Set by OutputSpecificationModule, used by GrammarModule
- `organization_contexts`: Set by ContextAwarenessModule, used by ErrorPreventionModule
- `domain_contexts`: Set by ContextAwarenessModule, used by ErrorPreventionModule
- `ontological_category`: Set by SemanticCategorisationModule, used by DefinitionTaskModule
- `character_limit_warning`: Set by OutputSpecificationModule, used by DefinitionTaskModule

### Module Output Metadata
Elke module moet deze metadata in output stoppen:
- `execution_time_ms`: Hoe lang de module draaide
- `character_count`: Lengte van gegenereerde content
- `tokens_estimate`: Geschatte tokens voor LLM
- `warnings`: Eventuele waarschuwingen

## Implementation Priority

### High Priority (Core Functionaliteit)
1. PromptOrchestrator - Zonder dit werkt niets
2. ExpertiseModule - Basis rol definitie
3. SemanticCategorisationModule - Kern ESS-02 logic
4. QualityRulesModule - Alle validatieregels

### Medium Priority (Belangrijke Features)
5. ContextAwarenessModule - Context verwerking
6. ErrorPreventionModule - Verboden patronen
7. DefinitionTaskModule - Finale instructies

### Lower Priority (Nice to Have)
8. OutputSpecificationModule - Format specs
9. GrammarModule - Extra grammatica regels

## Testing Strategy

### Unit Tests per Module
- Test elke module in isolatie
- Mock dependencies via shared_state
- Valideer output format en content

### Integration Tests
- Test module combinations
- Valideer dependency flow
- Check shared state propagation

### End-to-End Tests
- Test complete prompt generatie
- Vergelijk met legacy output
- Performance benchmarks

## Migration Path

1. **Phase 1**: Implement PromptOrchestrator skeleton
2. **Phase 2**: Migrate existing component methods to modules
3. **Phase 3**: Add new functionality (GrammarModule)
4. **Phase 4**: Feature toggle between old and new
5. **Phase 5**: Full cutover to modular system
