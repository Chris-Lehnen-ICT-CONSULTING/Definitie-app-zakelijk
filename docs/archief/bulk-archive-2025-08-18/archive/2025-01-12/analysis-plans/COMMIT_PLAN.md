# Commit Plan - Grote Documentatie Update

## Overzicht Wijzigingen

We hebben vandaag gedaan:
1. Complete architectuur analyse
2. BMAD compliance documentatie
3. Epic herstructurering (6 mega-stories → 7 epics met 41 stories)
4. ADRs toegevoegd
5. Dev-load files voor AI agents
6. Immediate action plan
7. Refactoring plan

## Voorgestelde Commit Structuur

### Commit 1: BMAD Compliance & Architecture Docs
```bash
git add docs/architecture/
git add docs/BMAD-compliance-report.md
git add docs/ARCHITECTURE_ANALYSIS.md
git add .ai/

git commit -m "docs: Implementeer BMAD compliance en architectuur documentatie

- Voeg BMAD-required files toe (coding-standards, tech-stack, source-tree)
- Creëer 3 dev-load files voor AI agent context
- Voeg architectuur analyse toe met technische schuld assessment
- Documenteer alle architectural decisions (ADR-001 t/m ADR-005)
- Bereik 100% BMAD compliance

BREAKING CHANGE: UnifiedDefinitionService gemarkeerd als problematisch
"
```

### Commit 2: Epic Restructure & Stories
```bash
git add docs/stories/
git add docs/epic-restructure-proposal.md
git add docs/prd.md

git commit -m "feat: Herstructureer 6 mega-stories naar 7 epics met 41 stories

- Splits grote stories (3-13 pts) op in kleine stories (1-5 pts)
- Creëer 7 focused epics met duidelijke business value
- Voeg complete sprint planning toe (6 sprints, ~14 pts per sprint)
- Archiveer oude mega-stories voor referentie
- Update PRD met nieuwe epic structuur

Epics:
1. Database & Infrastructure (7 pts)
2. Web Lookup Module (10 pts)
3. UI Quick Wins (8 pts)
4. Content Enrichment (11 pts)
5. Tab Activation (21 pts)
6. Prompt Optimization (10 pts)
7. Test Suite (18 pts)
"
```

### Commit 3: Action Plans & Next Steps
```bash
git add docs/IMMEDIATE-ACTION-PLAN.md
git add docs/REFACTORING-ACTION-PLAN.md
git add COMMIT_PLAN.md

git commit -m "docs: Voeg concrete actieplannen toe voor week 1

- Immediate action plan met 3 kritieke beslissingen
- Refactoring plan voor UnifiedDefinitionService (4 weken)
- Week 1 prioriteiten aangepast voor refactoring beslissing
- Go/No-Go criteria voor sprint 1

Beslissing: Direct refactoren naar clean services (ADR-005)
"
```

### Commit 4: Cleanup
```bash
# Verwijder oude/moved files
git add -A

git commit -m "chore: Cleanup oude documentatie en duplicaten

- Verwijder gedupliceerde docs uit root
- Consolideer log directories
- Verwijder temp Office files
- Organiseer alle docs volgens BMAD structuur
"
```

## Commands om uit te voeren:

```bash
# 1. Bekijk eerst wat er precies gaat gebeuren
git status

# 2. Als je akkoord bent, voer dan de commits uit in volgorde
# (zie hierboven)

# 3. Push naar remote
git push origin feature/consolidate-services

# 4. Maak een PR voor review
```

## Belangrijk!

- Deze commits bevatten ALLEEN documentatie wijzigingen
- Geen code changes (behalve mogelijk .gitignore)
- Elke commit heeft een duidelijk doel
- Gebruik conventional commits format
