# DEF-253 Quick Wins Implementatie

## Execution Mode
- **ULTRATHINK**: Ja
- **MULTIAGENT**: 5 agents
- **CONSENSUS**: Vereist voor acceptance

## Agent Configuratie

| Agent | Rol | Verantwoordelijkheid |
|-------|-----|---------------------|
| Explorer | Codebase Verkenner | Identificeer alle referenties naar te verwijderen modules + locaties silent exceptions |
| Developer | Implementatie | Voer deletions uit, voeg logging toe |
| Code Reviewer | Kwaliteit | Controleer geen broken imports, verify logging format |
| Tester | Validatie | Run tests, check geen regressies |
| PM | Acceptatie | Valideer completeness tegen DEF-253 criteria |

## Opdracht

Implementeer de quick wins uit DEF-253:

### Deel 1: Dead Code Removal (~428 LOC)

1. **Delete MetricsModule** (99 LOC)
   - Locatie: `src/prompt_components/modules/`
   - Reden: Disabled in DEF-171, nooit meer gebruikt

2. **Delete ErrorPreventionModule** (259 LOC)
   - Locatie: `src/prompt_components/modules/`
   - Reden: Redundant met JSONBasedRulesModule (DEF-169)

3. **Delete CompositeModule** (70 LOC)
   - Locatie: `src/prompt_components/modules/`
   - Reden: Ongebruikt, nooit getracked

### Deel 2: Silent Exception Logging (3 locaties)

- Identificeer 3 silent exceptions die logging missen
- Voeg structured logging toe met:
  - `logger.exception()` of `logger.error(..., exc_info=True)`
  - Context (welke operatie, welke input)
  - Correlation ID indien beschikbaar

## Context

**Codebase:** Definitie-app (Dutch AI Definition Generator)
**Gerelateerde Issues:** DEF-253 (parent), DEF-171, DEF-169
**Prioriteit:** Medium (quick wins, technische schuld reductie)

## Fasen

### Fase 1: Verkenning (Explorer)

- [ ] Identificeer alle imports/referenties naar MetricsModule
- [ ] Identificeer alle imports/referenties naar ErrorPreventionModule
- [ ] Identificeer alle imports/referenties naar CompositeModule
- [ ] Scan voor silent exceptions: `except:` of `except Exception:` zonder logging
- [ ] Maak lijst van 3 hoogste prioriteit silent exceptions

### Fase 2: Implementatie (Developer + Code Reviewer)

- [ ] Verwijder MetricsModule + alle referenties
- [ ] Verwijder ErrorPreventionModule + alle referenties
- [ ] Verwijder CompositeModule + alle referenties
- [ ] Voeg logging toe aan 3 silent exceptions
- [ ] Code Reviewer valideert elke wijziging real-time

### Fase 3: Testing (Tester)

- [ ] Run `make test` - alle tests moeten slagen
- [ ] Run `make lint` - geen nieuwe warnings
- [ ] Verify geen broken imports in hele codebase
- [ ] Verify logging output bij triggered exceptions (indien mogelijk)

### Fase 4: Acceptance (PM + alle agents)

- [ ] Alle 3 modules verwijderd
- [ ] Alle referenties opgeruimd
- [ ] 3 silent exceptions hebben nu logging
- [ ] Tests groen
- [ ] Lint clean
- [ ] Geen regressies

## Output Format

1. **Wijzigingen Rapport**
   - Lijst van verwijderde bestanden
   - Lijst van gewijzigde bestanden (referentie cleanup + logging)
   - LOC verwijderd vs toegevoegd

2. **Silent Exception Fixes**
   - Per fix: locatie, oude code, nieuwe code, rationale

3. **Validatie Status**
   - Test resultaten
   - Lint resultaten
   - Consensus status per agent

## Constraints

- **Geen feature changes** - alleen deletions en logging toevoegingen
- **Geen refactoring** - focus op de specifieke taken
- **Follow existing patterns** - gebruik bestaande logging conventies
- **Dutch comments** waar business logic relevant is
- **Commit message format**: `fix(cleanup): [beschrijving]` of `chore(dead-code): [beschrijving]`
