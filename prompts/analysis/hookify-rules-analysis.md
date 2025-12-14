# Hookify Rules Analysis - Instructiedocumenten Scan

## Execution Mode

| Setting | Value |
|---------|-------|
| ULTRATHINK | Ja |
| MULTIAGENT | 4 agents |
| CONSENSUS | Optioneel (geen blocking decisions) |

---

## Agent Configuratie

| Agent | Type | Focus Area | Vote Weight |
|-------|------|------------|-------------|
| **Rules Extractor** | `Explore` | Identificeer expliciete regels en constraints | 30% |
| **Pattern Detector** | `code-reviewer` | Detecteer impliciete patronen en anti-patterns | 25% |
| **Hookify Specialist** | `general-purpose` | Vertaal regels naar hookify syntax | 25% |
| **Priority Ranker** | `product-manager` | Prioriteer op basis van impact/frequentie | 20% |

---

## Opdracht

Analyseer de volgende instructiedocumenten om potentiële hookify regels te identificeren:

1. **CLAUDE.md** - Project-specifieke regels voor Definitie-app
2. **~/.ai-agents/UNIFIED_INSTRUCTIONS.md** - Globale Claude Code instructies

### Deliverables

Voor elke geïdentificeerde regel, lever:

| Veld | Beschrijving |
|------|--------------|
| `name` | Regel naam (kebab-case) |
| `event` | Hook event type (bash/file/stop/prompt/all) |
| `pattern` | Regex pattern |
| `action` | warn of block |
| `bron` | Waar in document gevonden |
| `prioriteit` | P1 (kritiek) / P2 (belangrijk) / P3 (nice-to-have) |
| `rationale` | Waarom deze regel nuttig is |

---

## Context

### Huidige Hookify Regels (reeds geïmplementeerd)

| Regel | Event | Doel |
|-------|-------|------|
| `prompt-first-workflow` | prompt | Herinner aan prompt-first workflow bij analyse/review/fix taken |

### Hookify Capabilities

- **Events**: `bash`, `file`, `stop`, `prompt`, `all`
- **Actions**: `warn` (toon bericht), `block` (voorkom actie)
- **Patterns**: Python regex syntax
- **Conditions**: Geavanceerde matching op `file_path`, `new_text`, `command`, etc.

---

## Fasen

### Fase 1: Document Scanning (Rules Extractor)

Scan beide documenten op:

1. **Expliciete verboden** ("Never", "Nooit", "Forbidden", "WRONG")
2. **Verplichte patronen** ("Always", "Altijd", "Must", "CORRECT")
3. **Conditionals** ("Only if", "Alleen als", "Unless")
4. **Tabellen met Do/Don't**

### Fase 2: Pattern Extraction (Pattern Detector)

Voor elk gevonden item:

1. Bepaal welke tool/actie het betreft (Bash, Edit, Write, etc.)
2. Identificeer het detecteerbare patroon (regex)
3. Bepaal of het een waarschuwing of blokkade moet zijn

### Fase 3: Hookify Conversion (Hookify Specialist)

Converteer naar hookify formaat:

```yaml
name: rule-name
enabled: true
event: [bash|file|stop|prompt|all]
pattern: regex-here
action: [warn|block]
```

### Fase 4: Prioritization (Priority Ranker)

Prioriteer regels op:

| Criterium | Gewicht |
|-----------|---------|
| Frequentie van overtreding | 40% |
| Impact van overtreding | 35% |
| Eenvoud van implementatie | 25% |

---

## Output Format

### Tabel: Geïdentificeerde Regels

```markdown
| # | Name | Event | Pattern | Action | Priority | Source |
|---|------|-------|---------|--------|----------|--------|
| 1 | ... | ... | ... | ... | P1 | CLAUDE.md §X |
```

### Per Regel: Implementatie Template

```markdown
---
name: {name}
enabled: true
event: {event}
pattern: {pattern}
action: {action}
---

{Waarschuwingsbericht met context waarom deze regel bestaat}
```

### Samenvatting

- Totaal aantal regels per prioriteit
- Aanbevolen implementatievolgorde
- Eventuele conflicten of overlappingen

---

## Constraints

1. **Geen duplicaten** - Check of regel al bestaat in `.claude/`
2. **Geen false positives** - Patterns moeten specifiek genoeg zijn
3. **Nederlands waar relevant** - Waarschuwingsberichten in het Nederlands voor NL-specifieke regels
4. **Testbaar** - Elke regex moet getest worden met voorbeelden

---

## Te Scannen Documenten

### Document 1: CLAUDE.md
- Locatie: `/Users/chrislehnen/Projecten/Definitie-app/CLAUDE.md`
- Focus: Project-specifieke regels

### Document 2: UNIFIED_INSTRUCTIONS.md
- Locatie: `~/.ai-agents/UNIFIED_INSTRUCTIONS.md`
- Focus: Globale Claude Code gedragsregels

---

## Execution Command

```
Voer deze prompt uit met de 4 gedefinieerde agents.
Scan beide documenten en lever de gevraagde deliverables.
```
