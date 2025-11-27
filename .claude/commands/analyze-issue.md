# Linear Issue Analyse (Ultrathink + Multiagent)

Voer een diepgaande analyse uit op Linear issue **$ARGUMENTS** met ultrathink (Opus extended thinking) voor alle analyse-componenten.

---

## FASE 1: Issue Ophalen

Gebruik `mcp__linear-mcp__linear_search_issues` met query "$ARGUMENTS" om het issue op te halen.
Haal daarna de comments op met `mcp__linear-mcp__linear_get_issue_comments`.

Extraheer en toon:
- **Issue ID**: (bijv. DEF-123)
- **Titel**:
- **Status**:
- **Prioriteit**:
- **Beschrijving**:
- **Comments**: (samenvatting)
- **Aanmaakdatum**:

---

## FASE 2: Issue Classificatie

Bepaal het type issue:

| Type | Indicatoren |
|------|-------------|
| **Promptgeneratie** | "prompt", "GPT", "AI", "generatie", "template", "instructie", "LLM" |
| **Validatie/Toetsregels** | "validatie", "toetsregel", "regel", "check" |
| **UI/Streamlit** | "UI", "interface", "tab", "widget", "sessie" |
| **Database** | "database", "schema", "migratie", "data" |
| **Architectuur** | "refactor", "service", "container", "DI" |
| **Bug** | "bug", "error", "fout", "crash" |
| **Feature** | "feature", "nieuw", "toevoegen" |

---

## FASE 3: Promptgeneratie Check

**ALS het issue gaat over promptgeneratie of AI-generatie:**

> **STOP - Gebruikersinput Vereist**
>
> Dit issue gaat over promptgeneratie. Voor een accurate analyse heb ik een recent gegenereerde prompt nodig.
>
> **Vraag aan gebruiker via AskUserQuestion:**
> - "Dit issue gaat over promptgeneratie. Kun je een recent gegenereerde prompt delen?"
> - Optie 1: "Ik plak de prompt hieronder"
> - Optie 2: "De prompt staat in een bestand (geef pad)"
> - Optie 3: "Genereer een nieuwe testprompt nu"
>
> **Wacht op de prompt voordat je doorgaat naar Fase 4.**

---

## FASE 4: Codebase Context Verzamelen

**Gebruik directe tools** (Grep, Glob, Read) om relevante code te vinden:

1. **Grep** - Zoek naar keywords uit het issue in de codebase
2. **Glob** - Vind bestanden gerelateerd aan het issue-domein
3. **Read** - Lees de meest relevante bestanden

Verzamel:
- Relevante bestandspaden
- Huidige implementatie-status
- Recente git wijzigingen (`git log --oneline -10 -- [bestanden]`)

**Output**: Lijst van 3-10 relevante bestanden met hun functie.

---

## FASE 5: Ultrathink Multiagent Analyse

**KRITISCH: Alle agents moeten draaien met `model="opus"` voor extended thinking.**

Start **drie parallelle Task agents** met onderstaande configuratie:

### Agent 1: Technische Correctheid (Opus Ultrathink)

```
Task tool parameters:
- subagent_type: "code-reviewer"
- model: "opus"
- prompt: [zie onder]
```

**Prompt voor Agent 1:**
```
ULTRATHINK ANALYSE - Technische Correctheid

Neem uitgebreid de tijd om diep na te denken over dit Linear issue.

## Issue Details
- ID: [ID]
- Titel: [TITEL]
- Beschrijving: [BESCHRIJVING]

## Relevante Code
[BESTANDEN UIT FASE 4]

## Analyse Opdracht

Denk stap voor stap en zeer grondig na over:

1. **Code-Issue Alignment**
   - Bestaat de genoemde code/component daadwerkelijk?
   - Klopt de beschrijving met wat de code doet?
   - Zijn er technische termen verkeerd gebruikt?

2. **Implementatie Verificatie**
   - Is het beschreven probleem reproduceerbaar in de code?
   - Of: Is de beschreven feature haalbaar met de huidige architectuur?

3. **Technische Nauwkeurigheid**
   - Zijn bestandsnamen/paden correct?
   - Kloppen service-namen en class-namen?
   - Zijn dependencies correct benoemd?

## Output Vereist
- Technische correctheid score: 1-10
- Lijst van technische onjuistheden (indien aanwezig)
- Bewijs uit de code voor elke bevinding
```

---

### Agent 2: Actualiteit Check (Opus Ultrathink)

```
Task tool parameters:
- subagent_type: "general-purpose"
- model: "opus"
- prompt: [zie onder]
```

**Prompt voor Agent 2:**
```
ULTRATHINK ANALYSE - Actualiteit & Relevantie

Neem uitgebreid de tijd om diep na te denken over de actualiteit van dit issue.

## Issue Details
- ID: [ID]
- Titel: [TITEL]
- Beschrijving: [BESCHRIJVING]
- Aangemaakt: [DATUM]

## Relevante Code
[BESTANDEN UIT FASE 4]

## Analyse Opdracht

Denk stap voor stap en zeer grondig na over:

1. **Implementatie Status**
   - Is het beschreven probleem/feature al opgelost/gebouwd?
   - Zoek naar commits na de issue-datum die dit raken
   - Check of de genoemde code nog bestaat of is gerefactord

2. **Codebase Evolutie**
   - Zijn er grote architectuurwijzigingen geweest sinds het issue?
   - Is de context van het issue nog relevant?
   - Gebruik: git log --since="[ISSUE_DATUM]" -- [relevante bestanden]

3. **Issue Overlap**
   - Zijn er andere issues die hetzelfde probleem beschrijven?
   - Is dit issue een duplicaat of subset van iets anders?

## Output Vereist
- Status: ACTUEEL / VEROUDERD / DEELS_OPGELOST / DUPLICAAT
- Bewijs voor de status (commits, code snippets)
- Als VEROUDERD: wat heeft het opgelost?
```

---

### Agent 3: Kwaliteit & Volledigheid (Opus Ultrathink)

```
Task tool parameters:
- subagent_type: "debug-specialist"
- model: "opus"
- prompt: [zie onder]
```

**Prompt voor Agent 3:**
```
ULTRATHINK ANALYSE - Issue Kwaliteit

Neem uitgebreid de tijd om diep na te denken over de kwaliteit van dit issue.

## Issue Details
- ID: [ID]
- Titel: [TITEL]
- Beschrijving: [BESCHRIJVING]
- Prioriteit: [PRIORITEIT]

## Analyse Opdracht

Denk stap voor stap en zeer grondig na over:

1. **Duidelijkheid**
   - Is het probleem/doel helder omschreven?
   - Zou een developer dit kunnen oppakken zonder extra vragen?
   - Zijn er ambigue termen of onduidelijke verwijzingen?

2. **Scope & Afbakening**
   - Is de scope realistisch voor één issue?
   - Zijn er verborgen dependencies of voorwaarden?
   - Moet dit opgesplitst worden in meerdere issues?

3. **Acceptatiecriteria**
   - Zijn er duidelijke done-criteria?
   - Hoe weet je wanneer dit issue "klaar" is?
   - Zijn er edge cases benoemd?

4. **Prioriteit Assessment**
   - Klopt de prioriteit met de business impact?
   - Zijn er blokkers die eerst opgelost moeten?

## Output Vereist
- Kwaliteitsscore: 1-10
- Lijst van ontbrekende informatie
- Concrete verbeterpunten voor het issue
- Aanbeveling: GOED / HERSCHRIJVEN / OPSPLITSEN / MEER_INFO_NODIG
```

---

## FASE 6: Ultrathink Synthese

**Start een finale Opus agent** voor de synthese:

```
Task tool parameters:
- subagent_type: "general-purpose"
- model: "opus"
- prompt: [zie onder]
```

**Prompt voor Synthese Agent:**
```
ULTRATHINK SYNTHESE - Eindoordeel

Neem uitgebreid de tijd om alle analyses te combineren tot een coherent eindoordeel.

## Agent Resultaten

### Agent 1 - Technische Correctheid
[RESULTAAT AGENT 1]

### Agent 2 - Actualiteit
[RESULTAAT AGENT 2]

### Agent 3 - Kwaliteit
[RESULTAAT AGENT 3]

## Synthese Opdracht

Denk diep na over:

1. **Consistentie Check**
   - Zijn er tegenstrijdigheden tussen de agent-analyses?
   - Welke bevindingen versterken elkaar?

2. **Gewogen Oordeel**
   - Weeg de drie aspecten tegen elkaar af
   - Een technisch incorrect issue is erger dan een onduidelijk issue
   - Een verouderd issue maakt andere scores irrelevant

3. **Concrete Aanbevelingen**
   - Wat moet er gebeuren met dit issue?
   - Welke specifieke wijzigingen zijn nodig?

## Eindoordeel Categorieen

Kies precies één:

| Oordeel | Wanneer | Actie |
|---------|---------|-------|
| **READY** | Tech ≥7, Actueel, Kwal ≥6 | Kan direct opgepakt |
| **NEEDS_UPDATE** | Tech <7 of Kwal <6, maar Actueel | Issue bijwerken |
| **STALE** | Verouderd of Duplicaat | Sluiten/archiveren |
| **SPLIT** | Te grote scope | Opsplitsen in sub-issues |
| **BLOCKED** | Externe dependencies | Wachten + linken |

## Output Vereist

Geef output in exact dit format:

---
## Eindoordeel: [OORDEEL]

### Scores
| Aspect | Score |
|--------|-------|
| Technisch | X/10 |
| Actueel | [STATUS] |
| Kwaliteit | X/10 |

### Samenvatting
[2-3 zinnen over het issue en de conclusie]

### Aanbevolen Acties
1. [ ] [Concrete actie 1]
2. [ ] [Concrete actie 2]
3. [ ] [Concrete actie 3 indien nodig]

### Belangrijkste Bevindingen
- [Bevinding 1 met bewijs]
- [Bevinding 2 met bewijs]
- [Bevinding 3 met bewijs]
---
```

---

## FASE 7 (Optioneel): Promptgeneratie Deep-Dive

**Alleen als het issue over promptgeneratie gaat EN een prompt is aangeleverd:**

Start een extra Opus ultrathink agent:

```
Task tool parameters:
- subagent_type: "code-reviewer"
- model: "opus"
- prompt: [zie onder]
```

**Prompt:**
```
ULTRATHINK ANALYSE - Promptgeneratie Specifiek

## Issue
[ISSUE DETAILS]

## Aangeleverde Prompt
[DE GEGENEREERDE PROMPT]

## Relevante Prompt Code
- src/services/generation/
- config/toetsregels/

## Analyse Opdracht

Denk diep na over:

1. **Prompt-Issue Correlatie**
   - Toont de aangeleverde prompt het probleem uit het issue?
   - Of: Zou de voorgestelde feature de prompt verbeteren?

2. **Toetsregel Compliance**
   - Volgt de prompt de 45 toetsregels?
   - Welke regels worden geschonden (indien van toepassing)?

3. **Output Kwaliteit**
   - Is de gegenereerde definitie bruikbaar?
   - Wat zijn de tekortkomingen?

4. **Root Cause**
   - Wat is de daadwerkelijke oorzaak van het probleem?
   - Zit het in de prompt template, de toetsregels, of de AI service?

## Output
- Prompt kwaliteitsscore: 1-10
- Specifieke problemen gevonden
- Link naar issue: BEVESTIGD / ONTKRACHT / DEELS_RELEVANT
- Aanbeveling voor fix
```

---

## Output Format

Presenteer het eindresultaat aan de gebruiker als:

```markdown
# Linear Issue Analyse: [ID]

## TL;DR
**[OORDEEL]** - [Eén zin samenvatting]

## Scores
| Aspect | Score | Toelichting |
|--------|-------|-------------|
| Technisch | X/10 | [kort] |
| Actueel | STATUS | [kort] |
| Kwaliteit | X/10 | [kort] |

## Aanbevolen Acties
1. [ ] Actie
2. [ ] Actie

## Gedetailleerde Bevindingen

### Technische Analyse
[Samenvatting Agent 1]

### Actualiteit
[Samenvatting Agent 2]

### Kwaliteit
[Samenvatting Agent 3]

### Promptgeneratie (indien van toepassing)
[Samenvatting Fase 7]
```
