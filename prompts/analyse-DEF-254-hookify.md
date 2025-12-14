# DEF-254 Hookify Rules Implementation - Analyse Prompt

## Execution Mode
- **ULTRATHINK**: Ja
- **MULTIAGENT**: 6 agents
- **CONSENSUS**: Vereist

## Agent Configuratie

| Agent | Rol | Verantwoordelijkheid |
|-------|-----|---------------------|
| Explorer | Codebase Verkenner | Map bestaande hookify structuur, CLAUDE.md constraints, pre-commit overlap |
| Code Reviewer | Kwaliteitsanalist | Review gap-analysis kwaliteit, regex patterns, best practices |
| Architect | Structuur Designer | Regel design patterns, event keuzes, file/prompt/bash routing |
| PM | Product Manager | Prioriteit validatie, effort schatting, acceptatie criteria |
| Complexity Checker | Complexiteitsanalist | Complexiteit per regel, onderhoudbaarheid, false positive risico |
| Silent Failure Hunter | Edge Case Detective | Regex edge cases, bypass scenarios, silent failures in enforcement |

## Opdracht

Analyseer Linear issue DEF-254 om de implementatie van 8 hookify regels voor CLAUDE.md enforcement te plannen.

**Scope:**
- Gap analysis: `prompts/hookify-gap-analysis.md`
- Bestaande regel: `.claude/hookify.prompt-first-workflow.local.md`
- CLAUDE.md constraints: §Critical Rules, §Canonical Names, §File Locations
- Te creëren: 8 nieuwe `.claude/hookify.*.local.md` bestanden

**Uit te sluiten:**
- Pre-commit hooks (geen overlap)
- Implementatie zelf (alleen analyse)

## Context

**Codebase:** Definitie-app (Dutch AI Definition Generator)
**Doel:** Automatische enforcement van CLAUDE.md constraints via prompt-time interventie
**Prioriteit:** High (Priority 2 in Linear)

## Fasen

### Fase 1: Verkenning (Explorer)
- Lees en analyseer `prompts/hookify-gap-analysis.md`
- Map `.claude/hookify.prompt-first-workflow.local.md` als referentie
- Identificeer alle CLAUDE.md constraints die enforcement nodig hebben
- Check pre-commit hooks voor overlap vermijding

### Fase 2: Analyse (Code Reviewer + Architect + Complexity Checker)
- **Code Reviewer**: Valideer regex patterns uit gap analysis, identificeer verbeteringen
- **Architect**: Evalueer event keuzes (file vs prompt vs bash), ontwerp consistente structuur
- **Complexity Checker**: Beoordeel complexiteit per regel, identificeer high-risk patterns

### Fase 3: Risk Assessment (Silent Failure Hunter + PM)
- **Silent Failure Hunter**: Identificeer edge cases, bypass scenarios, false positives/negatives
- **PM**: Valideer effort estimates, prioriteiten, acceptatie criteria volledigheid

### Fase 4: Synthese (PM + Architect)
- Consolideer bevindingen naar implementatie roadmap
- Prioriteer regels op basis van impact/effort
- Identificeer afhankelijkheden tussen regels

### Fase 5: Consensus Verificatie
- Alle agents reviewen finale analyse
- Valideer bevindingen cross-agent
- Resolve tegenstrijdigheden
- Bepaal confidence level per aanbeveling

## Output Format

### 1. Executive Summary (PM)
- Top 3 bevindingen
- Kritieke risico's
- Go/No-Go per prioriteit tier (P1/P2/P3)

### 2. Technische Analyse

**Per regel:**
| Regel | Event | Regex Kwaliteit | Complexiteit | Risico | Aanbeveling |
|-------|-------|-----------------|--------------|--------|-------------|

**Overlap check:**
- Pre-commit hooks die al coverage bieden
- Aanbevelingen voor deduplicatie

### 3. Implementatie Roadmap (Architect)
- Volgorde van implementatie
- Afhankelijkheden
- Test strategie per regel

### 4. Consensus Rapport
- Agent agreement level per bevinding (%)
- Afwijkende meningen met onderbouwing
- Finale validatie status

## Constraints

- Analyseer ALLEEN de gespecificeerde scope
- Geen code wijzigingen implementeren
- Focus op objectieve bevindingen
- Onderbouw claims met concrete voorbeelden uit codebase
