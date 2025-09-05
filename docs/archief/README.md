# Architecture Decision Records (ADRs)

Deze folder bevat alle Architecture Decision Records voor het DefinitieAgent project. ADRs documenteren belangrijke architectuur beslissingen, de context waarin ze genomen zijn, en de gevolgen ervan.

## Waarom ADRs?

- **Kennisbehoud**: Documenteert waarom beslissingen genomen zijn
- **Transparantie**: Maakt besluitvorming proces inzichtelijk
- **Learning**: Leer van eerdere beslissingen
- **Onboarding**: Helpt nieuwe teamleden context te begrijpen

## ADR Index

| ADR | Titel | Status | Datum | Samenvatting |
|-----|-------|--------|-------|--------------|
| [ADR-001](ADR-001-monolithische-structuur.md) | Behoud Monolithische Structuur | Geaccepteerd | 2025-07-17 | Keuze voor modular monolith i.p.v. microservices voor simpliciteit |
| [ADR-002](ADR-002-features-first-development.md) | Features First Development | Geaccepteerd | 2025-07-17 | Prioriteit aan gebruikersfunctionaliteit boven technische perfectie |
| [ADR-003](ADR-003-legacy-code-als-specificatie.md) | Legacy Code als Specificatie | Geaccepteerd | 2025-07-17 | Legacy code behandelen als de officiële specificatie |
| [ADR-004](ADR-004-incrementele-migratie-strategie.md) | Incrementele Migratie Strategie | Geaccepteerd | 2025-07-17 | Strangler Fig pattern voor zero-downtime migratie |

## ADR Template

Voor nieuwe ADRs, gebruik het volgende template:

```markdown
# ADR-XXX: [Titel]

**Status:** [Proposed | Geaccepteerd | Afgewezen | Vervangen door ADR-YYY]
**Datum:** [YYYY-MM-DD]
**Deciders:** [Namen of rollen]

## Context
[Beschrijf de situatie en achtergrond]

## Probleemstelling
[Wat is de specifieke vraag of probleem?]

## Beslissing
[De genomen beslissing]

## Rationale
[Waarom deze beslissing?]

## Gevolgen
### Positief
- ✅ [Positief gevolg]

### Negatief
- ❌ [Negatief gevolg]

### Neutraal
- 🔄 [Neutraal gevolg]

## Alternatieven Overwogen
[Welke andere opties waren er?]

## Review Triggers
[Wanneer moet deze beslissing heroverwogen worden?]

## Gerelateerde Beslissingen
[Links naar gerelateerde ADRs]

## Status Updates
[Track wijzigingen in de beslissing]

## Referenties
[Links naar relevante resources]
```

## Status Types

- **Proposed**: Onder discussie
- **Geaccepteerd**: Actieve beslissing
- **Afgewezen**: Niet gekozen
- **Vervangen**: Superseded door nieuwe ADR
- **Deprecated**: Niet meer relevant

## Best Practices

1. **Immutability**: ADRs wijzig je niet, maak een nieuwe als beslissing verandert
2. **Conciseness**: Houd ADRs beknopt en to-the-point
3. **Context**: Leg voldoende context vast voor toekomstige lezers
4. **Traceability**: Link gerelateerde ADRs aan elkaar
5. **Actionable**: Maak consequenties concreet en uitvoerbaar

## Contributie Process

1. Maak nieuwe ADR met volgend nummer
2. Status = "Proposed"
3. Discussie in team meeting of PR
4. Update status naar "Geaccepteerd" of "Afgewezen"
5. Voeg toe aan index in deze README

## Resources

- [Documenting Architecture Decisions - Michael Nygard](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- [ADR Tools](https://github.com/npryce/adr-tools)
- [ADR GitHub Organization](https://adr.github.io/)
