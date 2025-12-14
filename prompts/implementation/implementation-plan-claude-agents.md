# Implementatieplan: Claude Code Agents Optimalisatie

> **Doel**: Concrete implementatie van de aanbevelingen uit ANALYSIS-REPORT-claude-code-agents.md
> **Basis**: 12 acties met ≥50% consensus, geprioriteerd naar impact en effort
> **Versie**: 1.0

---

## Execution Mode

| Setting | Value |
|---------|-------|
| **ULTRATHINK** | Nee - Implementatie, geen analyse |
| **MULTIAGENT** | Nee - Sequentiële uitvoering |
| **CONSENSUS** | N/A - Implementatie fase |

---

## Prioritering Matrix

| Priority | Criteria | Acties |
|----------|----------|--------|
| **P0** | <30 min, high impact, no dependencies | 4 Quick Wins |
| **P1** | 2-4h, enables other work | 2 Short Term |
| **P2** | 4-8h, standalone value | 2 Short Term |
| **P3** | >8h, strategic | 4 Long Term |

---

## P0: Quick Wins (Direct Implementeerbaar)

### P0.1: Dutch Keywords Toevoegen aan Hookify Pattern

**Status**: Ready
**Effort**: 15 min
**Consensus**: 100%

**Huidige Pattern**:
```regex
(?i)\b(analy[sz]e|analyseer|onderzoek|audit|review|code.?review|pr.?review|implementeer|implement|bouw|build|maak|create|add|refactor|migreer|migrate|fix|repareer|los.?op|debug|patch|corrigeer|correct)\b
```

**Nieuwe Pattern** (uitgebreid):
```regex
(?i)\b(analy[sz]e|analyseer|onderzoek|audit|evalueer|beoordeel|review|code.?review|pr.?review|controleer|bekijk|implementeer|implement|bouw|build|maak|create|add|refactor|migreer|migrate|ontwikkel|fix|repareer|los.?op|debug|patch|corrigeer|correct|herstel)\b
```

**Toegevoegde Keywords**:
- `evalueer`, `beoordeel` (analyse)
- `controleer`, `bekijk` (review)
- `ontwikkel` (implementatie)
- `herstel` (fix)

**Bestand**: `.claude/hookify.prompt-first-workflow.local.md`

---

### P0.2: CLAUDE.md Prompt-First Rule Update

**Status**: Already Done ✓
**Verificatie**: Regel 41 bevat "(enforced via hookify rule)"

---

### P0.3: Remove "Be Comprehensive" Anti-Pattern

**Status**: Ready
**Effort**: 20 min
**Consensus**: 100%

**Actie**: Zoek en vervang in alle prompts:
- "be comprehensive" → "focus on TOP 3-5 items"
- "volledig" zonder scope → "TOP 5" of "belangrijkste"
- Open-ended vragen → Bounded vragen

**Bestanden te checken**:
- `prompts/*.md`
- `CLAUDE.md`

---

### P0.4: Output Templates Toevoegen aan Prompts

**Status**: Ready
**Effort**: 30 min
**Consensus**: 100%

**Actie**: Voeg explicit output format toe aan:
- `prompts/TEMPLATE-deep-analysis.md` (al aanwezig ✓)
- Nieuwe prompts die gegenereerd worden

---

## P1: Short Term - Enablers

### P1.1: Create `/generate-prompt` Slash Command

**Status**: Ready
**Effort**: 2h
**Consensus**: 100%
**Dependencies**: None

**Bestand**: `.claude/commands/generate-prompt.md`

**Specificatie**:
```yaml
---
name: generate-prompt
description: Generate structured multiagent prompt for current task
arguments:
  - name: task
    description: Brief description of the task
    required: true
---
```

**System Prompt Content**:
- Lees TEMPLATE-deep-analysis.md v2.0
- Classificeer task type (Analyse/Review/Implementatie/Fix)
- Selecteer agents volgens matrix
- Genereer complete prompt
- Sla op in /prompts/

---

### P1.2: Document Agent Chaining Patterns

**Status**: Ready
**Effort**: 2h
**Consensus**: 92%
**Dependencies**: None

**Bestand**: `docs/guidelines/AGENTS.md` (update)

**Toe te voegen sectie**:
```markdown
## Agent Chaining Patterns

| Workflow | Chain | Context Passing |
|----------|-------|-----------------|
| Bug Fix | debug-specialist → full-stack-developer → code-reviewer | Issue IDs |
| New Feature | Plan → code-architect → full-stack-developer → pr-review-toolkit:* | Design docs |
| Code Review | Explore → code-reviewer → pr-test-analyzer | File refs |
| Refactoring | Explore → code-simplifier → code-reviewer | Change scope |
```

---

## P2: Short Term - Standalone Value

### P2.1: Phase 0 Context Gathering Pattern

**Status**: Ready
**Effort**: 3h
**Consensus**: 100%
**Dependencies**: P1.1

**Actie**: Voeg Phase 0 toe aan alle multiagent prompts:
```markdown
## Phase 0: Context Gathering (ALWAYS FIRST)

**Agents**: Explorer + Researcher (parallel)

**Explorer Output**:
- Codebase structure relevant to task
- File inventory
- Dependency map

**Researcher Output** (if external research needed):
- Perplexity findings
- Context7 documentation
- Best practices

**Context Reference ID**: `phase0-{task-slug}`
```

---

### P2.2: Validation Checklist in Template

**Status**: Ready
**Effort**: 1h
**Consensus**: 92%
**Dependencies**: None

**Bestand**: `prompts/TEMPLATE-deep-analysis.md`

**Toe te voegen sectie**:
```markdown
## Pre-Execution Validation

Before executing this prompt, verify:

| Check | Status |
|-------|--------|
| [ ] No `[PLACEHOLDER]` text remaining | |
| [ ] Minimum 4 agents configured | |
| [ ] All agents have vote weights | |
| [ ] Consensus thresholds defined | |
| [ ] Output format specified | |
| [ ] Execution command present | |
```

---

## P3: Long Term - Strategic

### P3.1: Dutch Toetsregels Analyst Agent

**Status**: Design needed
**Effort**: 8-12h
**Consensus**: 92%
**Dependencies**: None

**Bestand**: `.claude/agents/toetsregels-analyst.md`

**Capabilities**:
- Understand 45 validation rules in `config/toetsregels/`
- Analyze rule effectiveness
- Suggest new rules based on Dutch linguistic patterns
- Validate rule JSON structure

---

### P3.2: Streamlit Specialist Agent

**Status**: Design needed
**Effort**: 8-12h
**Consensus**: 92%
**Dependencies**: None

**Bestand**: `.claude/agents/streamlit-specialist.md`

**Capabilities**:
- SessionStateManager patterns
- Widget lifecycle management
- Key-only widget enforcement
- Streamlit anti-pattern detection

---

### P3.3: Context Caching Between Sessions

**Status**: Research needed
**Effort**: 12-16h
**Consensus**: 85%
**Dependencies**: P2.1

**Concept**:
- Cache Phase 0 output to `/prompts/cache/`
- TTL: 24h for docs, invalidate on git commit
- Reduce repeated exploration

---

### P3.4: Extend Hookify for Command Invocation

**Status**: Plugin modification required
**Effort**: 16-24h
**Consensus**: 78%
**Dependencies**: Hookify plugin architecture

**Concern** (EE): High complexity, may not be worth it given behavior-based workaround works.

---

## Execution Order

```
Phase A: Quick Wins (vandaag)
├── P0.1: Dutch keywords (15 min)
├── P0.3: Remove anti-patterns (20 min)
└── P0.4: Output templates check (30 min)

Phase B: Enablers (deze week)
├── P1.1: /generate-prompt command (2h)
└── P1.2: Document chaining patterns (2h)

Phase C: Enhancements (volgende week)
├── P2.1: Phase 0 pattern (3h)
└── P2.2: Validation checklist (1h)

Phase D: Strategic (backlog)
├── P3.1: Toetsregels agent
├── P3.2: Streamlit agent
├── P3.3: Context caching
└── P3.4: Hookify extension
```

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Prompt-first adoption | >80% of analysis tasks | Manual tracking |
| Token efficiency | -25% avg | Compare before/after |
| Time to first agent output | -50% | Parallelization effect |
| Dutch keyword coverage | 100% common terms | Pattern testing |

---

## Risico's en Mitigaties

| Risico | Impact | Mitigatie |
|--------|--------|-----------|
| Hookify pattern te breed | False positives | Test met edge cases |
| /generate-prompt te complex | Low adoption | Keep simple, iterate |
| Agent chaining niet gevolgd | Inconsistent quality | Document in CLAUDE.md |

---

## Direct Uitvoeren: P0 Quick Wins

De volgende acties worden nu direct geïmplementeerd:
1. ✓ P0.2: CLAUDE.md al bijgewerkt
2. → P0.1: Dutch keywords toevoegen
3. → P0.3: Anti-patterns scannen
4. → P0.4: Templates valideren
