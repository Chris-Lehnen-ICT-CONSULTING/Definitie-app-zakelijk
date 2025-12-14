# Generate Structured Multiagent Prompt

Genereer een gestructureerde multiagent analyse prompt voor: **$ARGUMENTS**

---

## FASE 1: Taak Classificatie

Classificeer de taak in een van de volgende categorieën:

| Categorie | Keywords | Primaire Focus |
|-----------|----------|----------------|
| **ANALYSE** | analyseer, onderzoek, audit, evalueer, beoordeel | Begrip en inzicht |
| **REVIEW** | review, code review, PR review, controleer | Kwaliteitsbeoordeling |
| **IMPLEMENTATIE** | implementeer, bouw, maak, ontwikkel, refactor, migreer | Nieuwe functionaliteit |
| **FIX** | fix, repareer, los op, debug, corrigeer, herstel | Probleem oplossen |

**Gedetecteerde categorie**: [bepaal uit $ARGUMENTS]

---

## FASE 2: Scope Extractie

Uit "$ARGUMENTS", extraheer:

| Aspect | Waarde |
|--------|--------|
| **Onderwerp** | [wat moet er gebeuren] |
| **Bestanden** | [relevante bestanden/directories] |
| **Diepte** | Oppervlakkig / Medium / Diepgaand |
| **Output** | Rapport / Recommendations / Code changes |

---

## FASE 3: Agent Selectie

Selecteer agents op basis van taaktype:

### ANALYSE taken:
| Agent | Type | Weight | Focus |
|-------|------|--------|-------|
| Explorer | `Explore` | 0.5x | Codebase mapping |
| Architect | `feature-dev:code-architect` | 2.0x | Architecture patterns |
| Code Reviewer | `code-reviewer` | 1.5x | Code quality |
| Complexity Checker | `code-simplifier` | 1.5x | Over-engineering |
| Researcher | `general-purpose` | 1.0x | External research |
| PM | `product-manager` | 1.5x | Business context |

### REVIEW taken:
| Agent | Type | Weight | Focus |
|-------|------|--------|-------|
| Code Reviewer | `code-reviewer` | 1.5x | Code quality |
| Silent Failure Hunter | `pr-review-toolkit:silent-failure-hunter` | 1.0x | Error handling |
| Tester | `pr-review-toolkit:pr-test-analyzer` | 1.0x | Test coverage |
| Type Analyst | `pr-review-toolkit:type-design-analyzer` | 0.75x | Type safety |
| Debug Specialist | `debug-specialist` | 0.75x | Logging |

### IMPLEMENTATIE taken:
| Agent | Type | Weight | Focus |
|-------|------|--------|-------|
| Architect | `feature-dev:code-architect` | 2.0x | Design |
| Code Reviewer | `code-reviewer` | 1.5x | Quality |
| Tester | `pr-review-toolkit:pr-test-analyzer` | 1.0x | Testing |
| PM | `product-manager` | 1.5x | Requirements |
| Complexity Checker | `code-simplifier` | 1.5x | Simplicity |

### FIX taken:
| Agent | Type | Weight | Focus |
|-------|------|--------|-------|
| Debug Specialist | `debug-specialist` | 0.75x | Root cause |
| Silent Failure Hunter | `pr-review-toolkit:silent-failure-hunter` | 1.0x | Error patterns |
| Code Reviewer | `code-reviewer` | 1.5x | Fix quality |
| Tester | `pr-review-toolkit:pr-test-analyzer` | 1.0x | Regression |

**Minimum agents**: 4
**Maximum agents**: 10

---

## FASE 4: Prompt Generatie

Genereer de volledige prompt volgens `prompts/TEMPLATE-deep-analysis.md` v2.0:

### Structuur:
1. **Titel**: [Beschrijvende titel]
2. **Execution Mode**: ULTRATHINK/MULTIAGENT/CONSENSUS settings
3. **Agent Configuratie**: Tabel met geselecteerde agents + weights
4. **Opdracht**: 2-3 zinnen taakbeschrijving
5. **Scope**: Doel, Bestanden, Diepte, Output
6. **Context**: Huidige situatie, Probleemstelling, Gewenste eindsituatie
7. **Consensus Framework**: Thresholds per categorie
8. **Agent Assignments**: Per-agent opdrachten
9. **Output Format**: Verwacht rapport formaat
10. **Constraints**: Project en taak beperkingen
11. **Execution Command**: Fase-gebaseerde uitvoering

---

## FASE 5: Validatie

Controleer de gegenereerde prompt:

| Check | Status |
|-------|--------|
| [ ] Geen `[PLACEHOLDER]` tekst over |
| [ ] Minimum 4 agents geconfigureerd |
| [ ] Alle agents hebben vote weights |
| [ ] Consensus thresholds gedefinieerd |
| [ ] Output format gespecificeerd |
| [ ] Execution command aanwezig |

---

## FASE 6: Opslaan

**Bestandsnaam**: `prompts/{taak-slug}.md`

Gebruik Write tool om de prompt op te slaan.

**Na opslaan, vraag**:
> "Prompt opgeslagen in `/prompts/{filename}.md`
>
> **Samenvatting:**
> - Taaktype: {type}
> - Agents: {aantal} ({namen})
> - Consensus: {threshold}%
>
> Wil je de prompt nu uitvoeren?"

---

## Constraints

- Alle agents draaien op **opus** (tenzij expliciet anders)
- Solo developer context - geen team overhead
- Focus op actionable output
- Nederlandse taal voor prompt content
