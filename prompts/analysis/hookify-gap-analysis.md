# Hookify Gap Analysis - Definitie-app

> **Vraag**: Welke hookify regels zijn er en welke zou je kunnen/moeten maken als je de CLAUDE.md en overige instructies voor Claude Code analyseert van dit project?

---

## Execution Mode

**ULTRATHINK**: Activeer extended reasoning voor rule design.

**MULTIAGENT STRATEGY**: Lanceer 5 gespecialiseerde agenten parallel.

**CONSENSUS REQUIRED**: Alleen regels met ≥60% consensus worden aanbevolen.

---

## Agent Configuratie

| # | Agent Role | Type | Focus Area | Vote Weight |
|---|------------|------|------------|-------------|
| 1 | **Code Reviewer** | `code-reviewer` | Anti-patterns detectie, code quality enforcement | 1.5x |
| 2 | **Architect** | `feature-dev:code-architect` | Architecture constraints, layer separation | 2.0x |
| 3 | **Complexity Checker** | `code-simplifier` | Over-engineering prevention, KISS | 1.5x |
| 4 | **Silent Failure Hunter** | `pr-review-toolkit:silent-failure-hunter` | Error handling patterns | 1.0x |
| 5 | **Explorer** | `Explore` | Codebase verkenning, bestaande patronen | 0.5x |

---

## Opdracht

Analyseer alle Claude Code instructiebestanden en bepaal:
1. Welke hookify regels bestaan er al?
2. Welke regels zijn nodig om CLAUDE.md constraints automatisch af te dwingen?
3. Welke regels voorkomen veelvoorkomende fouten in dit project?

### Scope

| Aspect | Waarde |
|--------|--------|
| **Doel** | Hookify regel inventarisatie + gap analysis |
| **Bestanden** | CLAUDE.md, .claude/*, .pre-commit-config.yaml, src/ui/ |
| **Diepte** | DIEPGAAND |
| **Output** | Regel inventaris + Aanbevelingen met prioriteit |

---

## Context

- **Project**: Definitie-app (Dutch AI Definition Generator)
- **Technologie**: Python 3.11+, Streamlit, GPT-4, SQLite
- **Constraints**: Solo developer, geen backwards compatibility nodig

### Hookify Capabilities

| Event | Wanneer | Match Op |
|-------|---------|----------|
| `prompt` | Gebruiker typt prompt | Prompt tekst |
| `file` | Claude schrijft/edit bestand | `file_path`, `new_text` |
| `bash` | Claude voert bash uit | `command` |
| `stop` | Claude is klaar met antwoord | Volledige response |

### Bestaande Hookify Regels

| Regel | Event | Pattern | Status |
|-------|-------|---------|--------|
| `prompt-first-workflow` | prompt | `\b(analyseer\|analyse\|...\|fix)\b` | ✅ Actief |

---

## Fase 1: Instructie Analyse

### 1.1 Agent Assignments

**Agent 1 (Code Reviewer):**
```
Analyseer CLAUDE.md voor afdwingbare code quality regels:
- Welke patterns zijn verboden?
- Welke naming conventions zijn verplicht?
- Welke imports zijn niet toegestaan?

Return:
- Lijst van afdwingbare regels
- Pattern suggesties (regex)
- Severity per regel (warn/block)
- VOTE op regels van andere agents
```

**Agent 2 (Architect):**
```
Analyseer CLAUDE.md voor architecture constraints:
- Layer separation (services mag ui niet importeren)
- File location rules (geen bestanden in root)
- Import restrictions
- Canonical names enforcement

Return:
- Architecture regels die hookify kan afdwingen
- File path patterns
- VOTE op architecture-related regels
```

**Agent 3 (Complexity Checker):**
```
Analyseer voor complexity/KISS enforcement:
- Over-engineering patterns
- Backwards compatibility hacks (verboden)
- Large change thresholds (>100 lines, >5 files)

Return:
- Complexity prevention regels
- VOTE op of regels zelf niet te complex zijn
```

**Agent 4 (Silent Failure Hunter):**
```
Analyseer voor error handling enforcement:
- Silent exception patterns
- Empty catch blocks
- Missing error propagation

Return:
- Error handling regels
- Patterns die silent failures veroorzaken
- VOTE op urgentie van regels
```

**Agent 5 (Explorer):**
```
Verken de codebase voor:
- .pre-commit-config.yaml (bestaande checks)
- Actuele anti-pattern voorbeelden in code
- Overlap met bestaande tooling (ruff, black)

Return:
- Bestaande enforcement mechanisms
- Gaps die hookify kan vullen
- PROVIDE CONTEXT voor andere agents
```

### 1.2 Specifieke Vragen

1. Welke CLAUDE.md regels worden al door pre-commit/ruff/black afgedwongen?
2. Welke regels zijn ALLEEN via hookify afdwingbaar (runtime/prompt-time)?
3. Wat is de ROI per regel (impact vs. complexity)?

---

## Fase 2: Bekende Constraints uit CLAUDE.md

| Constraint | Sectie | Detecteerbaar? | Hookify Event |
|------------|--------|----------------|---------------|
| SessionStateManager only | Critical Rules | ✅ `st\.session_state\[` | file |
| No files in root | Critical Rules | ✅ Write naar `^/[^/]+\.(py\|json)$` | file |
| Ask for >100 lines / >5 files | Critical Rules | ⚠️ Moeilijk | stop |
| Key-only widget pattern | Streamlit Patterns | ✅ `value=.*key=` | file |
| Forbidden names (V1) | Canonical Names | ✅ `ValidationOrchestrator[^V]` | file |
| Database only in data/ | File Locations | ✅ `.db` buiten `data/` | file |
| No backwards compat hacks | Code Style | ⚠️ Moeilijk | file |

---

## Fase 3: Consensus Building

### 3.1 Voting Criteria

Per voorgestelde regel:
1. Is het pattern correct? (JA/NEE)
2. Is de regel nodig? (ESSENTIAL/NICE_TO_HAVE/OVERKILL)
3. Is de severity juist? (AGREE/TOO_HIGH/TOO_LOW)
4. Prioriteit? (P1/P2/P3)

### 3.2 Consensus Thresholds

| Type | Minimum |
|------|---------|
| BLOCK rules | ≥75% |
| WARN rules | ≥60% |
| Optional rules | ≥50% |

---

## Output Format

```markdown
# Hookify Gap Analysis Report

## Executive Summary
[Key findings - bestaande regels + top aanbevelingen]

## 1. Bestaande Regels

| # | Naam | Event | Status | Effectiviteit |
|---|------|-------|--------|---------------|

## 2. Aanbevolen Nieuwe Regels

### P1 - Kritiek

#### [REGEL NAAM]
**Consensus**: X%
**Event**: [type]
**Pattern**: `[regex]`
**Action**: [warn/block]
**Rationale**: [waarom nodig]

**Hookify file content:**
```markdown
---
name: [naam]
enabled: true
event: [event]
pattern: [pattern]
action: [action]
---

[Waarschuwingsbericht]
```

### P2 - Belangrijk
...

### P3 - Nice-to-have
...

## 3. Afgewezen Regels

| Regel | Reden |
|-------|-------|

## 4. Overlap met Pre-commit

| Check | Tool | Hookify nodig? |
|-------|------|----------------|

## 5. Implementation Roadmap

1. [ ] ...
```

---

## Constraints

- **Praktisch**: Geen false positives
- **Solo Developer**: Geen overhead
- **Geen overlap**: Skip wat pre-commit al doet

---

## Input Bestanden

1. `CLAUDE.md`
2. `.claude/hookify.*.local.md`
3. `.pre-commit-config.yaml`
4. `src/ui/session_state.py`
5. `pyproject.toml`

---

## Execution Command

```
Phase 1: Parallel → Agents 1-5 (instructie analyse)
Phase 2: Sequential → Pattern design
Phase 3: Parallel → Consensus voting
Phase 4: Sequential → Report generatie
```
