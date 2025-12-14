# Linear Issue: Hookify Rules Implementation

> **Doel**: Maak een Linear issue aan voor de volledige implementatie van het hookify regelsysteem op basis van de gap analysis.

---

## Execution Mode

**SINGLE AGENT**: Linear MCP tool
**OUTPUT**: Linear issue URL

---

## Linear Issue Specificatie

### Title
```
Hookify Rules Implementation - CLAUDE.md Enforcement Automation
```

### Description

```markdown
## Samenvatting

Implementeer 8 hookify regels om CLAUDE.md constraints automatisch af te dwingen. Dit sluit gaps in de huidige pre-commit coverage en voegt prompt-time interventie toe.

## Context

**Gap Analysis uitgevoerd**: `prompts/hookify-gap-analysis.md`
**Huidige status**: 1 regel actief (`prompt-first-workflow`)
**Doel**: 8 nieuwe regels met multiagent consensus ≥60%

## Deliverables

### P1 - Kritiek (Sprint 1)

| Regel | Event | Doel |
|-------|-------|------|
| `no-root-files` | file | Blokkeer bestanden in project root |
| `forbidden-class-names` | file | Enforce V2 canonical names |
| `silent-exception-swallowing` | file | Blokkeer `except Exception: return` |

### P2 - Belangrijk (Sprint 2)

| Regel | Event | Doel |
|-------|-------|------|
| `large-change-warning` | prompt | Waarschuw bij grote refactoring requests |
| `database-location-enforcement` | file | Database alleen in `data/` |
| `forbidden-context-names` | file | Nederlandse context namen |
| `wrong-file-location` | file | Tests in `tests/`, scripts in `scripts/` |

### P3 - Nice-to-have (Backlog)

| Regel | Event | Doel |
|-------|-------|------|
| `backwards-compat-comments` | file | Waarschuw bij legacy comments |

## Acceptance Criteria

- [ ] Alle 8 `.claude/hookify.*.local.md` bestanden aangemaakt
- [ ] Regels getest met voorbeelden die WEL en NIET triggeren
- [ ] Geen overlap met bestaande pre-commit hooks
- [ ] Documentatie in `prompts/README.md` bijgewerkt

## Technische Details

**Hookify regel format:**
```markdown
---
name: regel-naam
enabled: true
event: file|prompt|bash|stop
pattern: regex-pattern
action: warn|block
---

Waarschuwingsbericht met context en oplossing.
```

**Bestanden:**
- `.claude/hookify.no-root-files.local.md`
- `.claude/hookify.forbidden-class-names.local.md`
- `.claude/hookify.silent-exception.local.md`
- `.claude/hookify.large-change.local.md`
- `.claude/hookify.database-location.local.md`
- `.claude/hookify.context-names.local.md`
- `.claude/hookify.file-location.local.md`
- `.claude/hookify.backwards-compat.local.md`

## Referenties

- Gap Analysis: `prompts/hookify-gap-analysis.md`
- Bestaande regel: `.claude/hookify.prompt-first-workflow.local.md`
- CLAUDE.md constraints: `CLAUDE.md` §Critical Rules, §Canonical Names, §File Locations

## Effort Estimate

| Fase | Effort |
|------|--------|
| P1 regels | 2h |
| P2 regels | 2h |
| P3 regels | 0.5h |
| Testing | 1h |
| Documentatie | 0.5h |
| **Totaal** | **6h** |

## Labels

- `enhancement`
- `automation`
- `developer-experience`
```

### Team
```
DEF (Definitie-app team)
```

### Priority
```
2 (High)
```

### Estimate
```
3 points
```

---

## Execution Command

```
Gebruik de Linear MCP tool om dit issue aan te maken:

mcp__linear-mcp__linear_create_issue({
  title: "Hookify Rules Implementation - CLAUDE.md Enforcement Automation",
  description: <bovenstaande description>,
  teamId: <DEF team ID>,
  priority: 2
})
```

---

## Post-Creation

Na aanmaken van het Linear issue:
1. Return de issue URL
2. Voeg subtasks toe voor elke regel (optioneel)
3. Link aan bestaande issues (DEF-* nummering)
