# Prompts Directory

Deze directory bevat herbruikbare prompts voor AI-gestuurde analyses en taken.

---

## Workflow Instructie

**BELANGRIJK**: Wanneer de gebruiker een opdracht geeft die valt onder een van de volgende categorieën:

- **Analyse** (codebase analyse, performance analyse, security audit, etc.)
- **Review** (code review, PR review, architecture review, etc.)
- **Implementatie** (nieuwe feature, refactoring, migratie, etc.)
- **Fix** (bug fix, security fix, performance fix, etc.)

**VRAAG EERST:**

> "Wil je dat ik eerst een gestructureerde prompt genereer voor deze taak?
>
> Dit kan helpen met:
> - Multiagent aanpak (meerdere gespecialiseerde agents parallel)
> - ULTRATHINK modus voor diepgaande analyse
> - Consensus framework tussen agents
> - Gestructureerde output en deliverables
>
> **Opties:**
> 1. Ja, genereer een prompt (opslaan in `/prompts/`)
> 2. Nee, voer direct uit
> 3. Ja, genereer EN voer direct uit"

### Wanneer WEL prompt genereren (aanbevolen):

| Situatie | Reden |
|----------|-------|
| Complexe analyse (>5 bestanden) | Multiagent coverage nodig |
| Kritieke wijzigingen | Consensus verificatie belangrijk |
| Onbekend terrein | Research agents kunnen helpen |
| Herhaalbare taak | Prompt kan hergebruikt worden |
| Kwaliteitsborging nodig | Meerdere reviewers parallel |

### Wanneer NIET prompt genereren:

| Situatie | Reden |
|----------|-------|
| Simpele fix (<10 regels) | Overhead niet waard |
| Duidelijke opdracht | Direct uitvoeren is sneller |
| Tijdskritiek | Prompt generatie kost tijd |
| Eerder vergelijkbare prompt | Hergebruik bestaande |

---

## Beschikbare Prompts

| Bestand | Doel | Agents |
|---------|------|--------|
| `TEMPLATE-deep-analysis.md` | **Template** - Herbruikbaar voor elke diepgaande analyse | 4-10 agents |
| `prompt-engineering-analysis.md` | Analyse van prompt-generatie architectuur | 10 agents |

---

## Prompt Template Structuur

Elke prompt moet de volgende secties bevatten:

```markdown
# [Titel]

## Execution Mode
- ULTRATHINK: ja/nee
- MULTIAGENT: aantal agents
- CONSENSUS: vereist/optioneel

## Agent Configuratie
[Tabel met agents, types, focus areas, vote weights]

## Opdracht
[Concrete taakbeschrijving]

## Context
[Relevante achtergrond]

## Fasen
[Stapsgewijze uitvoering]

## Consensus Framework (indien van toepassing)
[Voting regels, thresholds, dissent handling]

## Output Format
[Verwachte deliverables]

## Constraints
[Beperkingen en randvoorwaarden]

## Execution Command
[Hoe de prompt uit te voeren]
```

---

## Multiagent Configuratie Opties

### Standaard Agent Types

| Agent | Type | Wanneer gebruiken |
|-------|------|-------------------|
| Code Reviewer | `code-reviewer` | Code quality, patterns |
| Tester | `pr-review-toolkit:pr-test-analyzer` | Test coverage |
| Architect | `feature-dev:code-architect` | Architecture design |
| Product Manager | `product-manager` | Business value |
| Complexity Checker | `code-simplifier` | Over-engineering detectie |
| Silent Failure Hunter | `pr-review-toolkit:silent-failure-hunter` | Error handling |
| Type Analyst | `pr-review-toolkit:type-design-analyzer` | Type safety |
| Debug Specialist | `debug-specialist` | Logging, debugging |
| Explorer | `Explore` | Codebase verkenning |
| Researcher | `general-purpose` | External research |

### Aanbevolen Agent Combinaties

| Taak Type | Aanbevolen Agents | Totaal |
|-----------|-------------------|--------|
| Code Review | CR, TE, CC, SFH | 4 |
| Architecture Analysis | AR, CR, CC, EX | 4 |
| Bug Fix | DS, SFH, CR, TE | 4 |
| New Feature | AR, CR, TE, PM, CC | 5 |
| Security Audit | SFH, CR, TA, DS | 4 |
| Performance Analysis | DS, AR, CC, EX | 4 |
| Full Analysis | Alle 10 agents | 10 |

---

## Consensus Thresholds

| Severity | Minimum Consensus |
|----------|-------------------|
| CRITICAL | ≥75% |
| HIGH | ≥70% |
| MEDIUM | ≥60% |
| LOW | ≥50% |
| SUGGESTION | ≥40% |

---

## Gebruik

### Bestaande prompt uitvoeren:

```
Voer de prompt uit: prompts/prompt-engineering-analysis.md
```

### Nieuwe prompt genereren:

```
Genereer een prompt voor: [beschrijving van de taak]
```

### Prompt aanpassen:

```
Pas de prompt aan met: [wijzigingen]
```
