# ADR-005: Service Architecture Evolution - Van Monolith naar Clean Architecture

## Status
**Implemented** ✅

## Timeline
- **Oorspronkelijk voorstel:** December 2024 (UnifiedDefinitionService consolidatie)
- **Heroverweging:** Januari 2025 (Stop consolidatie, ga naar Clean Architecture)
- **Implementatie:** Augustus 2025 (Clean Architecture geïmplementeerd)

## Context

Het DefinitieAgent systeem was oorspronkelijk gebouwd met een monolithische `UnifiedDefinitionService` die alle functionaliteit bevatte. Dit leidde tot:
- Moeilijk testbare code (alles zat in één grote class)
- Tight coupling tussen verschillende verantwoordelijkheden
- Onduidelijke afhankelijkheden
- Complexe code die moeilijk te onderhouden was

### Waarom de Consolidatie Faalde

De poging om alles in één UnifiedDefinitionService te consolideren resulteerde in:
- Een "god object" anti-pattern
- Schending van het Single Responsibility Principle
- Toenemende complexiteit bij elke nieuwe feature
- Onmogelijk om componenten onafhankelijk te testen

## Decision

We besluiten om de monolithische UnifiedDefinitionService op te splitsen in gespecialiseerde services volgens Clean Architecture principes.

### Nieuwe Service Architectuur

```
┌─────────────────────────────────────────────────────┐
│                  Orchestrator                       │
│         (Coördineert het generatieproces)          │
└─────────────┬───────────────┬──────────────┬───────┘
              │               │              │
              v               v              v
    ┌─────────────┐  ┌──────────────┐  ┌────────────┐
    │  Generator  │  │  Validator   │  │ Repository │
    │  Service    │  │   Service    │  │  Service   │
    └─────────────┘  └──────────────┘  └────────────┘
```

### Service Verantwoordelijkheden

1. **GeneratorService**: Verantwoordelijk voor het genereren van definities
   - Template rendering
   - Definitie assemblage
   - Output formatting

2. **ValidatorService**: Valideert definities en toetsregels
   - Schema validatie
   - Business rule checking
   - Constraint verificatie

3. **RepositoryService**: Beheert data toegang
   - Definitie opslag/ophalen
   - Template management
   - Voorbeeld beheer

4. **DefinitionOrchestrator**: Coördineert het complete proces
   - Service orchestratie
   - Workflow management
   - Error handling

## Consequences

### Positief
- ✅ Betere testbaarheid - elke service kan onafhankelijk getest worden
- ✅ Loose coupling tussen componenten
- ✅ Duidelijke verantwoordelijkheden per service
- ✅ Makkelijker te onderhouden en uit te breiden
- ✅ Dependency Injection maakt services verwisselbaar
- ✅ Parallel development mogelijk door team

### Negatief
- ❌ Initiële refactoring effort was significant
- ❌ Meer classes en interfaces (complexiteit in structuur)
- ❌ Learning curve voor team members

### Neutraal
- 🔄 Dependency injection container nodig
- 🔄 Meer configuratie vereist
- 🔄 Interface definities tussen services

## Implementation Notes

De migratie is uitgevoerd in fases:
1. **Fase 1**: Interfaces gedefinieerd voor alle services
2. **Fase 2**: Services één voor één geëxtraheerd uit UnifiedDefinitionService
3. **Fase 3**: Dependency injection geïmplementeerd
4. **Fase 4**: Oude UnifiedDefinitionService verwijderd

### Backward Compatibility

Tijdens de migratie hebben we tijdelijk een facade pattern gebruikt om backward compatibility te behouden.

## Related ADRs

- ADR-001: Monolithische Structuur (oorspronkelijke architectuur)
- ADR-004: Incrementele Migratie Strategie (migration approach)

## Notes

Deze ADR consolideert de oorspronkelijke "heroverweging" beslissing en de uiteindelijke implementatie documentatie.