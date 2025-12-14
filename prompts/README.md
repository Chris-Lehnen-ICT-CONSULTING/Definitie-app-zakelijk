# Prompts Directory

Deze directory bevat herbruikbare prompts voor AI-gestuurde analyses en taken.

---

## Directory Structuur

```
prompts/
├── README.md              # Deze documentatie
├── templates/             # Herbruikbare prompt templates
│   └── TEMPLATE-deep-analysis.md
├── analysis/              # Analyse prompts
├── review/                # Code review prompts
├── implementation/        # Implementatie/development prompts
├── fix/                   # Bug fix prompts
└── quick/                 # Snelle, simpele prompts
```

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
> - **Ja**: Ik voer `prompt-forge forge "<taak>" -r` uit (multi-agent review, aanbevolen)
> - **Nee**: Ik voer direct uit
> - **Ja + Uitvoeren**: Ik genereer prompt EN voer direct uit"

### prompt-forge CLI

```bash
# Standaard met multi-agent review (aanbevolen)
prompt-forge forge "<taak beschrijving>" -r

# Met extra context
prompt-forge forge "<taak>" -c "<context>" -r

# Batch mode (non-interactief)
prompt-forge forge "<taak>" -r -b

# Demo mode (geen API kosten)
prompt-forge forge "<taak>" -d
```

Zie `CLAUDE.md` §Prompt-First Workflow voor volledige documentatie.

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

### Templates

| Bestand | Doel | Agents |
|---------|------|--------|
| `templates/TEMPLATE-deep-analysis.md` | Herbruikbaar template voor elke diepgaande analyse | 4-10 |

### Analysis Prompts

| Bestand | Doel |
|---------|------|
| `analysis/prompt-engineering-analysis.md` | Analyse van prompt-generatie architectuur |
| `analysis/claude-code-agents-analysis.md` | Analyse van Claude Code agents |
| `analysis/hookify-gap-analysis.md` | Gap analyse van hookify |
| `analysis/hookify-rules-analysis.md` | Analyse van hookify rules |
| `analysis/bmad-prompt-writer-analysis.md` | Analyse van BMAD prompt writer |
| `analysis/prompt-first-enforcement-analysis.md` | Analyse van prompt-first enforcement |
| `analysis/subagent-inventory-analysis.md` | Inventarisatie van subagents |
| `analysis/ANALYSIS-REPORT-claude-code-agents.md` | Rapport: Claude Code agents analyse |

### Implementation Prompts

| Bestand | Doel |
|---------|------|
| `implementation/agent-consistency-system.md` | Systeem voor agent output consistentie |
| `implementation/linear-hookify-implementation.md` | Linear + Hookify implementatie |
| `implementation/implementation-plan-claude-agents.md` | Implementatieplan voor agents |
| `implementation/prompt-generator-subagent-spec.md` | Specificatie voor prompt generator subagent |

### Review Prompts

(Nog geen prompts - gebruik `templates/TEMPLATE-deep-analysis.md` als basis)

### Fix Prompts

(Nog geen prompts - gebruik `templates/TEMPLATE-deep-analysis.md` als basis)

### Quick Prompts

(Nog geen prompts - voor snelle, simpele taken)

---

## Opslag Regels

| Prompt Type | Submap | Voorbeeld |
|-------------|--------|-----------|
| Analyse prompt | `analysis/` | `analysis/security-audit.md` |
| Review prompt | `review/` | `review/pr-review-feature-x.md` |
| Implementatie prompt | `implementation/` | `implementation/new-feature.md` |
| Fix prompt | `fix/` | `fix/bug-123.md` |
| Snelle prompt | `quick/` | `quick/rename-function.md` |
| Template | `templates/` | `templates/TEMPLATE-review.md` |

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
| Prompt Generator | `prompt-forge forge -r` | Prompt generatie (CLI tool) |

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
| CRITICAL | >=75% |
| HIGH | >=70% |
| MEDIUM | >=60% |
| LOW | >=50% |
| SUGGESTION | >=40% |

---

## Gebruik

### Bestaande prompt uitvoeren:

```
Voer de prompt uit: prompts/analysis/claude-code-agents-analysis.md
```

### Nieuwe prompt genereren:

```bash
# Via CLI (aanbevolen)
prompt-forge forge "beschrijving van de taak" -r

# Of vraag Claude om het uit te voeren
```

### Prompt aanpassen:

```
Pas de prompt aan met: [wijzigingen]
```
