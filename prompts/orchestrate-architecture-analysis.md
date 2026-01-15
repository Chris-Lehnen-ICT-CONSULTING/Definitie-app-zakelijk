---
prompt_id: architecture-analysis
version: "1.0.0"
compatible_models: ["claude-opus-4-5", "claude-sonnet-4"]
requires_ultrathink: true
generated_at: "2026-01-14T17:24:44.462089"
---

# Ultra-Deep Architecture Analysis
## Orchestrator + 98 Subagent Architecture (3 per Deelgebied)

---

## Execution Context

**Target:** src codebase (/Users/chrislehnen/Projecten/Definitie-app/src)
**Architecture:** 1 Orchestrator + 98 Subagents (3 per deelgebied)
**Per Deelgebied:** Code Reviewer + Full Stack Developer + Architecture Reviewer
**Mode:** Ultrathink Executive Analysis
**Output:** Structured findings with consensus voting

---

## Orchestrator Instructions

Je bent de **Ultra-Deep Architecture Analysis Orchestrator**. Je coördineert 98 parallelle subagents die elk een specifiek deelgebied analyseren.

### Agent Architecture

```
                    ┌─────────────────────┐
                    │    ORCHESTRATOR     │
                    │  (Hoofdcontext)     │
                    └─────────┬───────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │ Gebied 1│    ...   │ Gebied N│    ...   │Gebied 31│
   └─────────┘          └─────────┘          └─────────┘
```

### Orchestrator Protocol

1. **Spawn alle 98 subagents parallel** via Task() tool in één message
2. **Per deelgebied:** 3 agents met hun specifieke focus
3. **Wacht op alle resultaten** - elke subagent retourneert max 250 woorden
4. **Merge results** - combineer bevindingen per deelgebied met voting
5. **Aggregeer en deduplicate** over alle 31 deelgebieden
6. **Prioriteer op impact** (Critical > High > Medium > Low)
7. **Genereer geconsolideerd rapport**

### Context Management Rules

- Je hoofdcontext bevat ALLEEN coördinatie en synthese
- Elke subagent krijgt ALLEEN context voor hun deelgebied
- Subagents returnen compacte summaries (max 250 woorden)
- Totale synthese budget: ~6000 tokens

---

## Agent Configuratie

| # | Agent Role | Subagent Type | Focus Area | Vote Weight |
|---|------------|---------------|------------|-------------|
| A | **Code Reviewer** | `code-reviewer` | Code quality, Best practices, Maintainability | 1.0x |
| B | **Full Stack Developer** | `full-stack-developer` | Implementation, Edge cases, Integration | 1.0x |
| C | **Architecture Reviewer** | `architecture-reviewer` | Architecture, Patterns, Scalability | 1.2x |

**Per Deelgebied:** 3 agents × 31 deelgebieden = 98 subagents
**Totaal Vote Weight per Deelgebied:** 3.2x

---

## Consensus Framework

### Consensus Regels

1. **60% meerderheid vereist** - minimaal 2 van 3 agents moeten issue bevestigen
2. **Gewogen stemming** - zie weights in Agent Configuratie
3. **CRITICAL issues:** Alle agents MOETEN agree
4. **Dissent wordt gedocumenteerd** - minderheidsstandpunt wordt vermeld in rapport

### Severity Criteria

| Severity | Vereiste |
|----------|----------|
| CRITICAL | All 3 agents identify same missing node + confirmed by Linear issue |
| HIGH | 2/3 majority + AST Parser confirms missing node |
| MEDIUM | 2/3 majority on missing relationship or documentation |
| LOW | At least 1 agent flags + potential diagram improvement |
| INFO | Documentation enhancement suggestion |


### Voting Matrix Template

Per deelgebied wordt deze matrix ingevuld:

```
| Finding | Agent A | Agent B | Agent C | Weighted | Status |
|---------|---------|---------|---------|----------|--------|
| [desc]  | +1      | +1      | +1      | MAX      | ✅ FULL CONSENSUS |
| [desc]  | +1      | +1      | -1      | ≥60%    | ✅ ACCEPTED (2/3) |
| [desc]  | +1      | -1      | +1      | ≥60%    | ✅ ACCEPTED (2/3) |
| [desc]  | -1      | +1      | +1      | ≥60%    | ✅ ACCEPTED (2/3) |
| [desc]  | +1      | -1      | -1      | <60%    | ⚠️ MINORITY |
| [desc]  | -1      | -1      | -1      | 0%       | ❌ REJECTED |

Threshold: ≥60% = ACCEPTED, <60% = MINORITY/REJECTED
```

### Cross-Validation Protocol

```
Agent A (focus: quality)    Agent B (focus: fixes)    Agent C (focus: design)
       │                           │                          │
       ├── Vindt issue ───────────►├── Geeft fix? ───────────►├── Bevestigt impact?
       │                           │        │                 │        │
       │                           │        │                 │        ├─► ACCEPTED
       │                           │        │                 │        │
       │                           │        │                 │        └─► 2/3 CONSENSUS
       │                           │        │                 │
       │                           │        └── Geen fix ─────┴─► NEEDS_IMPLEMENTATION
       │                           │
       │◄── Cross-check ───────────┤
       │                           │
       └── Synthesis ──────────────┴───────────────────────────────► FINAL REPORT
```

---

## Subagent Failure Handling

### Failure Scenarios

Als een subagent faalt, timeout, of malformed output geeft:

| Situatie | Actie | Status |
|----------|-------|--------|
| 1 agent van trio faalt | Ga door met andere 2 agents | `PARTIAL` |
| 2 agents van trio falen | Ga door met 1 agent | `DEGRADED` |
| Alle agents van deelgebied falen | Skip deelgebied | `SKIPPED` |
| Timeout (>60s) | Behandel als failure | `TIMEOUT` |
| Malformed output | Parse met regex fallback | `DEGRADED` |

### Minimum Viable Analysis

- **Minimaal 70%** van deelgebieden moeten minimaal 2 agents hebben
- **Monster files** MOETEN minimaal 2 agents hebben
- Bij <70% coverage: rapporteer `INCOMPLETE_ANALYSIS` warning

### Coverage Warning Template

Bij incomplete coverage, voeg toe aan rapport:

```
⚠️ COVERAGE WARNING:
- Deelgebied X: PARTIAL (Agent 1C timeout, 2/3 agents)
- Deelgebied Y: DEGRADED (2 agents failed, 1/3 agents)
- Deelgebied Z: SKIPPED (alle agents failed)

Overall Coverage: X/Y deelgebieden (Z%)
```

### Retry Strategy

1. **Eerste poging faalt**: Wacht 5 seconden, retry 1x
2. **Retry faalt**: Markeer als FAILED, ga door
3. **Nooit blocken**: Andere agents moeten door kunnen gaan

### Output Parsing Fallback

Als XML parsing faalt, probeer regex:

```python
# Primary: XML parsing
<agent_output.*?>(.*?)</agent_output>

# Fallback: Section headers
## TOP \d+ .*?:\n(.*?)(?=##|$)

# Last resort: Bullet points
^\d+\.\s+\[.*?\].*$
```

---

## Subagent Verification Protocol

**KRITIEK**: Subagent tool "success" berichten garanderen NIET dat file edits naar disk zijn geschreven.
Elke subagent MOET zijn werk verifiëren voordat completion wordt gerapporteerd.

### Verification Rules

1. **NOOIT blind vertrouwen** op tool success responses
2. **ALTIJD verifiëren** na elke file write/edit operatie
3. **EXPLICIET rapporteren** of verificatie slaagde of faalde
4. **BIJ FALEN**: Re-run de operatie, NIET doorgaan met volgende stap

### Git-Based Verification

Na ELKE file operatie, voer uit:

```bash
# Check of bestand is gewijzigd
git status --short path/to/modified/file.py

# Verwacht output bij success:
#  M path/to/modified/file.py   (modified)
# ?? path/to/new/file.py        (new file)

# Als GEEN output: edit is NIET gepersisteerd!
```

**Interpretatie:**
| Output | Betekenis | Actie |
|--------|-----------|-------|
| ` M file.py` | File modified (staged) | Verificatie OK |
| `M  file.py` | File modified (unstaged) | Verificatie OK |
| `?? file.py` | New untracked file | Verificatie OK |
| `(geen output)` | **GEEN WIJZIGING** | **RE-RUN EDIT** |

### Subagent Verification Checklist

Na elke code wijziging, doorloop deze checklist:

```
[ ] 1. GREP voor verwachte pattern
      grep -n "expected_pattern" path/to/file
      -> Als niet gevonden: EDIT NIET TOEGEPAST

[ ] 2. LEES gewijzigde regels
      Read file met offset/limit rond gewijzigde locatie
      -> Controleer of nieuwe code aanwezig is

[ ] 3. CHECK git status (indien git repo)
      git status --short
      -> Modified files moeten verschijnen

[ ] 4. RAPPORTEER verificatie resultaat
      -> "VERIFIED: [pattern] found at line X"
      -> "FAILED: [pattern] not found, re-running edit"
```

### Verificatie Output Format

Elke subagent MOET eindigen met een verificatie block:

```xml
<verification>
  <status>VERIFIED|FAILED|PARTIAL</status>
  <checks>
    <check name="grep_pattern" result="PASS|FAIL">
      <command>grep -n "useCallback" ForgeView.tsx</command>
      <output>Line 5: import { useCallback } from 'react'</output>
    </check>
    <check name="git_status" result="PASS|FAIL">
      <command>git status --short</command>
      <output>M web/frontend/src/components/Forge/ForgeView.tsx</output>
    </check>
  </checks>
  <files_modified>
    <file path="path/to/file.py" verified="true|false"/>
  </files_modified>
</verification>
```

### Re-Run Protocol bij Verificatie Falen

Als verificatie faalt:

```
Poging 1 (origineel):
  -> Edit tool rapporteert "success"
  -> Verificatie: grep niet gevonden
  -> Status: EDIT NIET GEPERSISTEERD

Poging 2 (retry):
  -> WACHT 2 seconden
  -> Herhaal exact dezelfde edit operatie
  -> Verificatie opnieuw uitvoeren
  -> Als succesvol: doorgaan
  -> Als faalt: poging 3

Poging 3+ (max 2 retries):
  -> Bij herhaald falen na 2 pogingen:
  -> STOP subagent taak
  -> Rapporteer ESCALATION naar orchestrator
  -> Geef details: welke edit, welke verificatie, alle outputs
```

### Escalation Template

```xml
<escalation>
  <type>VERIFICATION_FAILED</type>
  <task>Beschrijving van de taak</task>
  <attempted_edit>
    <file>path/to/file.py</file>
    <operation>ADD|MODIFY|DELETE</operation>
    <expected_pattern>verwachte code/pattern</expected_pattern>
  </attempted_edit>
  <attempts>2</attempts>
  <error_details>
    Alle verificatie outputs en error messages
  </error_details>
  <recommendation>
    Mogelijke oorzaak en suggestie voor handmatige fix
  </recommendation>
</escalation>
```

### Orchestrator Validation Protocol

De orchestrator MOET elke subagent response valideren:

1. **Parse verification block**
   - Check voor `<verification>` tag in response
   - Als ontbreekt: behandel als UNVERIFIED

2. **Validate status**
   ```python
   if verification.status == "FAILED":
       # Log failure
       # Consider re-spawning subagent
       # Mark area as NEEDS_MANUAL_REVIEW

   if verification.status == "PARTIAL":
       # Some edits succeeded, some failed
       # Include in report with warning
   ```

3. **Cross-check file modifications**
   - Na ALLE subagents compleet
   - Run `git status` om alle wijzigingen te zien
   - Vergelijk met geclaimde wijzigingen per subagent
   - Flag discrepancies

4. **Final Validation Checklist**
   ```
   [ ] Alle subagents hebben verification block
   [ ] Geen FAILED statuses (of documented escalations)
   [ ] git status toont verwachte wijzigingen
   [ ] Geen onverwachte file changes
   ```

### Known Failure Modes

| Symptoom | Waarschijnlijke Oorzaak | Oplossing |
|----------|------------------------|-----------|
| Edit "success" maar geen wijziging | Context isolation | Re-run edit in nieuwe context |
| Wijziging op verkeerde branch | Branch switch door subagent | Check branch, cherry-pick indien nodig |
| Partial edit (helft van wijziging) | Tool timeout | Re-run complete edit |
| File created maar leeg | Write tool fout | Re-run met expliciete content |

---

## Deelgebied 1: Ontologie (~293 LOC)

### Files
- `ontologie/*.py`

### Agent 1A: Code Reviewer - Ontologie

```python
Task(
    subagent_type="code-reviewer",
    description="Ontologie Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Ontologie

## Target: ontologie/*.py (~293 LOC)

Je bent een **Code Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Code quality
- Best practices
- Maintainability
</ultrathink>

## FOCUS AREAS
- Code quality
- Best practices
- Maintainability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 1B: Full Stack Developer - Ontologie

```python
Task(
    subagent_type="full-stack-developer",
    description="Ontologie Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Ontologie

## Target: ontologie/*.py (~293 LOC)

Je bent een **Full Stack Developer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Implementation
- Edge cases
- Integration
</ultrathink>

## FOCUS AREAS
- Implementation
- Edge cases
- Integration

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 1C: Architecture Reviewer - Ontologie

```python
Task(
    subagent_type="architecture-reviewer",
    description="Ontologie Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Ontologie

## Target: ontologie/*.py (~293 LOC)

Je bent een **Architecture Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Architecture
- Patterns
- Scalability
</ultrathink>

## FOCUS AREAS
- Architecture
- Patterns
- Scalability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

---

## Deelgebied 2: Ui (~2,584 LOC) (MONSTER FILE)

### Files
- `ui/*.py`

### Agent 2A: Code Reviewer - Ui

```python
Task(
    subagent_type="code-reviewer",
    description="Ui Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Ui

## Target: ui/*.py (~2,584 LOC)

Je bent een **Code Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Code quality
- Best practices
- Maintainability
</ultrathink>

## FOCUS AREAS
- Code quality
- Best practices
- Maintainability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 2B: Full Stack Developer - Ui

```python
Task(
    subagent_type="full-stack-developer",
    description="Ui Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Ui

## Target: ui/*.py (~2,584 LOC)

Je bent een **Full Stack Developer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Implementation
- Edge cases
- Integration
</ultrathink>

## FOCUS AREAS
- Implementation
- Edge cases
- Integration

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 2C: Architecture Reviewer - Ui

```python
Task(
    subagent_type="architecture-reviewer",
    description="Ui Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Ui

## Target: ui/*.py (~2,584 LOC)

Je bent een **Architecture Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Architecture
- Patterns
- Scalability
</ultrathink>

## FOCUS AREAS
- Architecture
- Patterns
- Scalability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 2D: Code Simplifier - Ui

```python
Task(
    subagent_type="code-simplifier",
    description="Ui Code Simplifier Analysis",
    prompt="""
# CODE SIMPLIFIER ANALYSIS: Ui

## Target: ui/*.py (~2,584 LOC)

Je bent een **Code Simplifier** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Complexity
- Refactoring
- Splitting
</ultrathink>

## FOCUS AREAS
- Complexity
- Refactoring
- Splitting

## OUTPUT FORMAT (MAX 300 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

---

## Deelgebied 3: Components (~5,981 LOC) (MONSTER FILE)

### Files
- `ui/components/*.py`

### Agent 3A: Code Reviewer - Components

```python
Task(
    subagent_type="code-reviewer",
    description="Components Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Components

## Target: ui/components/*.py (~5,981 LOC)

Je bent een **Code Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Code quality
- Best practices
- Maintainability
</ultrathink>

## FOCUS AREAS
- Code quality
- Best practices
- Maintainability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 3B: Full Stack Developer - Components

```python
Task(
    subagent_type="full-stack-developer",
    description="Components Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Components

## Target: ui/components/*.py (~5,981 LOC)

Je bent een **Full Stack Developer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Implementation
- Edge cases
- Integration
</ultrathink>

## FOCUS AREAS
- Implementation
- Edge cases
- Integration

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 3C: Architecture Reviewer - Components

```python
Task(
    subagent_type="architecture-reviewer",
    description="Components Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Components

## Target: ui/components/*.py (~5,981 LOC)

Je bent een **Architecture Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Architecture
- Patterns
- Scalability
</ultrathink>

## FOCUS AREAS
- Architecture
- Patterns
- Scalability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 3D: Code Simplifier - Components

```python
Task(
    subagent_type="code-simplifier",
    description="Components Code Simplifier Analysis",
    prompt="""
# CODE SIMPLIFIER ANALYSIS: Components

## Target: ui/components/*.py (~5,981 LOC)

Je bent een **Code Simplifier** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Complexity
- Refactoring
- Splitting
</ultrathink>

## FOCUS AREAS
- Complexity
- Refactoring
- Splitting

## OUTPUT FORMAT (MAX 300 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

---

## Deelgebied 4: Database (~1,664 LOC) (MONSTER FILE)

### Files
- `database/*.py`

### Agent 4A: Code Reviewer - Database

```python
Task(
    subagent_type="code-reviewer",
    description="Database Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Database

## Target: database/*.py (~1,664 LOC)

Je bent een **Code Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Code quality
- Best practices
- Maintainability
</ultrathink>

## FOCUS AREAS
- Code quality
- Best practices
- Maintainability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 4B: Full Stack Developer - Database

```python
Task(
    subagent_type="full-stack-developer",
    description="Database Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Database

## Target: database/*.py (~1,664 LOC)

Je bent een **Full Stack Developer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Implementation
- Edge cases
- Integration
</ultrathink>

## FOCUS AREAS
- Implementation
- Edge cases
- Integration

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 4C: Architecture Reviewer - Database

```python
Task(
    subagent_type="architecture-reviewer",
    description="Database Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Database

## Target: database/*.py (~1,664 LOC)

Je bent een **Architecture Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Architecture
- Patterns
- Scalability
</ultrathink>

## FOCUS AREAS
- Architecture
- Patterns
- Scalability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 4D: Code Simplifier - Database

```python
Task(
    subagent_type="code-simplifier",
    description="Database Code Simplifier Analysis",
    prompt="""
# CODE SIMPLIFIER ANALYSIS: Database

## Target: database/*.py (~1,664 LOC)

Je bent een **Code Simplifier** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Complexity
- Refactoring
- Splitting
</ultrathink>

## FOCUS AREAS
- Complexity
- Refactoring
- Splitting

## OUTPUT FORMAT (MAX 300 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

---

## Deelgebied 5: Tools (~543 LOC)

### Files
- `tools/*.py`

### Agent 5A: Code Reviewer - Tools

```python
Task(
    subagent_type="code-reviewer",
    description="Tools Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Tools

## Target: tools/*.py (~543 LOC)

Je bent een **Code Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Code quality
- Best practices
- Maintainability
</ultrathink>

## FOCUS AREAS
- Code quality
- Best practices
- Maintainability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 5B: Full Stack Developer - Tools

```python
Task(
    subagent_type="full-stack-developer",
    description="Tools Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Tools

## Target: tools/*.py (~543 LOC)

Je bent een **Full Stack Developer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Implementation
- Edge cases
- Integration
</ultrathink>

## FOCUS AREAS
- Implementation
- Edge cases
- Integration

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 5C: Architecture Reviewer - Tools

```python
Task(
    subagent_type="architecture-reviewer",
    description="Tools Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Tools

## Target: tools/*.py (~543 LOC)

Je bent een **Architecture Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Architecture
- Patterns
- Scalability
</ultrathink>

## FOCUS AREAS
- Architecture
- Patterns
- Scalability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

---

## Deelgebied 6: Ai Toetser (~238 LOC)

### Files
- `ai_toetser/*.py`
- `ai_toetser/validators/*.py`

### Agent 6A: Code Reviewer - Ai Toetser

```python
Task(
    subagent_type="code-reviewer",
    description="Ai Toetser Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Ai Toetser

## Target: ai_toetser/*.py, ai_toetser/validators/*.py (~238 LOC)

Je bent een **Code Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Code quality
- Best practices
- Maintainability
</ultrathink>

## FOCUS AREAS
- Code quality
- Best practices
- Maintainability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 6B: Full Stack Developer - Ai Toetser

```python
Task(
    subagent_type="full-stack-developer",
    description="Ai Toetser Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Ai Toetser

## Target: ai_toetser/*.py, ai_toetser/validators/*.py (~238 LOC)

Je bent een **Full Stack Developer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Implementation
- Edge cases
- Integration
</ultrathink>

## FOCUS AREAS
- Implementation
- Edge cases
- Integration

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 6C: Architecture Reviewer - Ai Toetser

```python
Task(
    subagent_type="architecture-reviewer",
    description="Ai Toetser Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Ai Toetser

## Target: ai_toetser/*.py, ai_toetser/validators/*.py (~238 LOC)

Je bent een **Architecture Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Architecture
- Patterns
- Scalability
</ultrathink>

## FOCUS AREAS
- Architecture
- Patterns
- Scalability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

---

## Deelgebied 7: Config (~1,126 LOC)

### Files
- `config/*.py`

### Agent 7A: Code Reviewer - Config

```python
Task(
    subagent_type="code-reviewer",
    description="Config Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Config

## Target: config/*.py (~1,126 LOC)

Je bent een **Code Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Code quality
- Best practices
- Maintainability
</ultrathink>

## FOCUS AREAS
- Code quality
- Best practices
- Maintainability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 7B: Full Stack Developer - Config

```python
Task(
    subagent_type="full-stack-developer",
    description="Config Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Config

## Target: config/*.py (~1,126 LOC)

Je bent een **Full Stack Developer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Implementation
- Edge cases
- Integration
</ultrathink>

## FOCUS AREAS
- Implementation
- Edge cases
- Integration

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 7C: Architecture Reviewer - Config

```python
Task(
    subagent_type="architecture-reviewer",
    description="Config Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Config

## Target: config/*.py (~1,126 LOC)

Je bent een **Architecture Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Architecture
- Patterns
- Scalability
</ultrathink>

## FOCUS AREAS
- Architecture
- Patterns
- Scalability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

---

## Deelgebied 8: Security (~561 LOC)

### Files
- `security/*.py`

### Agent 8A: Code Reviewer - Security

```python
Task(
    subagent_type="code-reviewer",
    description="Security Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Security

## Target: security/*.py (~561 LOC)

Je bent een **Code Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Code quality
- Best practices
- Maintainability
</ultrathink>

## FOCUS AREAS
- Code quality
- Best practices
- Maintainability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 8B: Full Stack Developer - Security

```python
Task(
    subagent_type="full-stack-developer",
    description="Security Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Security

## Target: security/*.py (~561 LOC)

Je bent een **Full Stack Developer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Implementation
- Edge cases
- Integration
</ultrathink>

## FOCUS AREAS
- Implementation
- Edge cases
- Integration

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 8C: Architecture Reviewer - Security

```python
Task(
    subagent_type="architecture-reviewer",
    description="Security Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Security

## Target: security/*.py (~561 LOC)

Je bent een **Architecture Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Architecture
- Patterns
- Scalability
</ultrathink>

## FOCUS AREAS
- Architecture
- Patterns
- Scalability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

---

## Deelgebied 9: Integration (~593 LOC)

### Files
- `integration/*.py`

### Agent 9A: Code Reviewer - Integration

```python
Task(
    subagent_type="code-reviewer",
    description="Integration Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Integration

## Target: integration/*.py (~593 LOC)

Je bent een **Code Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Code quality
- Best practices
- Maintainability
</ultrathink>

## FOCUS AREAS
- Code quality
- Best practices
- Maintainability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 9B: Full Stack Developer - Integration

```python
Task(
    subagent_type="full-stack-developer",
    description="Integration Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Integration

## Target: integration/*.py (~593 LOC)

Je bent een **Full Stack Developer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Implementation
- Edge cases
- Integration
</ultrathink>

## FOCUS AREAS
- Implementation
- Edge cases
- Integration

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 9C: Architecture Reviewer - Integration

```python
Task(
    subagent_type="architecture-reviewer",
    description="Integration Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Integration

## Target: integration/*.py (~593 LOC)

Je bent een **Architecture Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Architecture
- Patterns
- Scalability
</ultrathink>

## FOCUS AREAS
- Architecture
- Patterns
- Scalability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

---

## Deelgebied 10: Hybrid Context (~1,178 LOC)

### Files
- `hybrid_context/*.py`

### Agent 10A: Code Reviewer - Hybrid Context

```python
Task(
    subagent_type="code-reviewer",
    description="Hybrid Context Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Hybrid Context

## Target: hybrid_context/*.py (~1,178 LOC)

Je bent een **Code Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Code quality
- Best practices
- Maintainability
</ultrathink>

## FOCUS AREAS
- Code quality
- Best practices
- Maintainability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 10B: Full Stack Developer - Hybrid Context

```python
Task(
    subagent_type="full-stack-developer",
    description="Hybrid Context Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Hybrid Context

## Target: hybrid_context/*.py (~1,178 LOC)

Je bent een **Full Stack Developer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Implementation
- Edge cases
- Integration
</ultrathink>

## FOCUS AREAS
- Implementation
- Edge cases
- Integration

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 10C: Architecture Reviewer - Hybrid Context

```python
Task(
    subagent_type="architecture-reviewer",
    description="Hybrid Context Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Hybrid Context

## Target: hybrid_context/*.py (~1,178 LOC)

Je bent een **Architecture Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Architecture
- Patterns
- Scalability
</ultrathink>

## FOCUS AREAS
- Architecture
- Patterns
- Scalability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

---

## Deelgebied 11: Utils (~2,982 LOC)

### Files
- `utils/*.py`

### Agent 11A: Code Reviewer - Utils

```python
Task(
    subagent_type="code-reviewer",
    description="Utils Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Utils

## Target: utils/*.py (~2,982 LOC)

Je bent een **Code Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Code quality
- Best practices
- Maintainability
</ultrathink>

## FOCUS AREAS
- Code quality
- Best practices
- Maintainability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 11B: Full Stack Developer - Utils

```python
Task(
    subagent_type="full-stack-developer",
    description="Utils Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Utils

## Target: utils/*.py (~2,982 LOC)

Je bent een **Full Stack Developer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Implementation
- Edge cases
- Integration
</ultrathink>

## FOCUS AREAS
- Implementation
- Edge cases
- Integration

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 11C: Architecture Reviewer - Utils

```python
Task(
    subagent_type="architecture-reviewer",
    description="Utils Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Utils

## Target: utils/*.py (~2,982 LOC)

Je bent een **Architecture Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Architecture
- Patterns
- Scalability
</ultrathink>

## FOCUS AREAS
- Architecture
- Patterns
- Scalability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

---

## Deelgebied 12: Repositories (~848 LOC)

### Files
- `repositories/*.py`

### Agent 12A: Code Reviewer - Repositories

```python
Task(
    subagent_type="code-reviewer",
    description="Repositories Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Repositories

## Target: repositories/*.py (~848 LOC)

Je bent een **Code Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Code quality
- Best practices
- Maintainability
</ultrathink>

## FOCUS AREAS
- Code quality
- Best practices
- Maintainability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 12B: Full Stack Developer - Repositories

```python
Task(
    subagent_type="full-stack-developer",
    description="Repositories Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Repositories

## Target: repositories/*.py (~848 LOC)

Je bent een **Full Stack Developer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Implementation
- Edge cases
- Integration
</ultrathink>

## FOCUS AREAS
- Implementation
- Edge cases
- Integration

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 12C: Architecture Reviewer - Repositories

```python
Task(
    subagent_type="architecture-reviewer",
    description="Repositories Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Repositories

## Target: repositories/*.py (~848 LOC)

Je bent een **Architecture Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Architecture
- Patterns
- Scalability
</ultrathink>

## FOCUS AREAS
- Architecture
- Patterns
- Scalability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

---

## Deelgebied 13: Models (~228 LOC)

### Files
- `models/*.py`

### Agent 13A: Code Reviewer - Models

```python
Task(
    subagent_type="code-reviewer",
    description="Models Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Models

## Target: models/*.py (~228 LOC)

Je bent een **Code Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Code quality
- Best practices
- Maintainability
</ultrathink>

## FOCUS AREAS
- Code quality
- Best practices
- Maintainability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 13B: Full Stack Developer - Models

```python
Task(
    subagent_type="full-stack-developer",
    description="Models Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Models

## Target: models/*.py (~228 LOC)

Je bent een **Full Stack Developer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Implementation
- Edge cases
- Integration
</ultrathink>

## FOCUS AREAS
- Implementation
- Edge cases
- Integration

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 13C: Architecture Reviewer - Models

```python
Task(
    subagent_type="architecture-reviewer",
    description="Models Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Models

## Target: models/*.py (~228 LOC)

Je bent een **Architecture Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Architecture
- Patterns
- Scalability
</ultrathink>

## FOCUS AREAS
- Architecture
- Patterns
- Scalability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

---

## Deelgebied 14: Cli (~201 LOC)

### Files
- `cli/*.py`

### Agent 14A: Code Reviewer - Cli

```python
Task(
    subagent_type="code-reviewer",
    description="Cli Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Cli

## Target: cli/*.py (~201 LOC)

Je bent een **Code Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Code quality
- Best practices
- Maintainability
</ultrathink>

## FOCUS AREAS
- Code quality
- Best practices
- Maintainability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 14B: Full Stack Developer - Cli

```python
Task(
    subagent_type="full-stack-developer",
    description="Cli Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Cli

## Target: cli/*.py (~201 LOC)

Je bent een **Full Stack Developer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Implementation
- Edge cases
- Integration
</ultrathink>

## FOCUS AREAS
- Implementation
- Edge cases
- Integration

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 14C: Architecture Reviewer - Cli

```python
Task(
    subagent_type="architecture-reviewer",
    description="Cli Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Cli

## Target: cli/*.py (~201 LOC)

Je bent een **Architecture Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Architecture
- Patterns
- Scalability
</ultrathink>

## FOCUS AREAS
- Architecture
- Patterns
- Scalability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

---

## Deelgebied 15: Document Processing (~602 LOC)

### Files
- `document_processing/*.py`

### Agent 15A: Code Reviewer - Document Processing

```python
Task(
    subagent_type="code-reviewer",
    description="Document Processing Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Document Processing

## Target: document_processing/*.py (~602 LOC)

Je bent een **Code Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Code quality
- Best practices
- Maintainability
</ultrathink>

## FOCUS AREAS
- Code quality
- Best practices
- Maintainability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 15B: Full Stack Developer - Document Processing

```python
Task(
    subagent_type="full-stack-developer",
    description="Document Processing Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Document Processing

## Target: document_processing/*.py (~602 LOC)

Je bent een **Full Stack Developer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Implementation
- Edge cases
- Integration
</ultrathink>

## FOCUS AREAS
- Implementation
- Edge cases
- Integration

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 15C: Architecture Reviewer - Document Processing

```python
Task(
    subagent_type="architecture-reviewer",
    description="Document Processing Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Document Processing

## Target: document_processing/*.py (~602 LOC)

Je bent een **Architecture Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Architecture
- Patterns
- Scalability
</ultrathink>

## FOCUS AREAS
- Architecture
- Patterns
- Scalability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

---

## Deelgebied 16: Opschoning (~69 LOC)

### Files
- `opschoning/*.py`

### Agent 16A: Code Reviewer - Opschoning

```python
Task(
    subagent_type="code-reviewer",
    description="Opschoning Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Opschoning

## Target: opschoning/*.py (~69 LOC)

Je bent een **Code Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Code quality
- Best practices
- Maintainability
</ultrathink>

## FOCUS AREAS
- Code quality
- Best practices
- Maintainability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 16B: Full Stack Developer - Opschoning

```python
Task(
    subagent_type="full-stack-developer",
    description="Opschoning Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Opschoning

## Target: opschoning/*.py (~69 LOC)

Je bent een **Full Stack Developer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Implementation
- Edge cases
- Integration
</ultrathink>

## FOCUS AREAS
- Implementation
- Edge cases
- Integration

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 16C: Architecture Reviewer - Opschoning

```python
Task(
    subagent_type="architecture-reviewer",
    description="Opschoning Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Opschoning

## Target: opschoning/*.py (~69 LOC)

Je bent een **Architecture Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Architecture
- Patterns
- Scalability
</ultrathink>

## FOCUS AREAS
- Architecture
- Patterns
- Scalability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

---

## Deelgebied 17: Orchestration (~138 LOC)

### Files
- `orchestration/*.py`

### Agent 17A: Code Reviewer - Orchestration

```python
Task(
    subagent_type="code-reviewer",
    description="Orchestration Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Orchestration

## Target: orchestration/*.py (~138 LOC)

Je bent een **Code Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Code quality
- Best practices
- Maintainability
</ultrathink>

## FOCUS AREAS
- Code quality
- Best practices
- Maintainability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 17B: Full Stack Developer - Orchestration

```python
Task(
    subagent_type="full-stack-developer",
    description="Orchestration Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Orchestration

## Target: orchestration/*.py (~138 LOC)

Je bent een **Full Stack Developer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Implementation
- Edge cases
- Integration
</ultrathink>

## FOCUS AREAS
- Implementation
- Edge cases
- Integration

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 17C: Architecture Reviewer - Orchestration

```python
Task(
    subagent_type="architecture-reviewer",
    description="Orchestration Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Orchestration

## Target: orchestration/*.py (~138 LOC)

Je bent een **Architecture Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Architecture
- Patterns
- Scalability
</ultrathink>

## FOCUS AREAS
- Architecture
- Patterns
- Scalability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

---

## Deelgebied 18: Api (~71 LOC)

### Files
- `api/*.py`

### Agent 18A: Code Reviewer - Api

```python
Task(
    subagent_type="code-reviewer",
    description="Api Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Api

## Target: api/*.py (~71 LOC)

Je bent een **Code Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Code quality
- Best practices
- Maintainability
</ultrathink>

## FOCUS AREAS
- Code quality
- Best practices
- Maintainability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 18B: Full Stack Developer - Api

```python
Task(
    subagent_type="full-stack-developer",
    description="Api Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Api

## Target: api/*.py (~71 LOC)

Je bent een **Full Stack Developer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Implementation
- Edge cases
- Integration
</ultrathink>

## FOCUS AREAS
- Implementation
- Edge cases
- Integration

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 18C: Architecture Reviewer - Api

```python
Task(
    subagent_type="architecture-reviewer",
    description="Api Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Api

## Target: api/*.py (~71 LOC)

Je bent een **Architecture Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Architecture
- Patterns
- Scalability
</ultrathink>

## FOCUS AREAS
- Architecture
- Patterns
- Scalability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

---

## Deelgebied 19: Export (~83 LOC)

### Files
- `export/*.py`

### Agent 19A: Code Reviewer - Export

```python
Task(
    subagent_type="code-reviewer",
    description="Export Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Export

## Target: export/*.py (~83 LOC)

Je bent een **Code Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Code quality
- Best practices
- Maintainability
</ultrathink>

## FOCUS AREAS
- Code quality
- Best practices
- Maintainability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 19B: Full Stack Developer - Export

```python
Task(
    subagent_type="full-stack-developer",
    description="Export Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Export

## Target: export/*.py (~83 LOC)

Je bent een **Full Stack Developer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Implementation
- Edge cases
- Integration
</ultrathink>

## FOCUS AREAS
- Implementation
- Edge cases
- Integration

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 19C: Architecture Reviewer - Export

```python
Task(
    subagent_type="architecture-reviewer",
    description="Export Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Export

## Target: export/*.py (~83 LOC)

Je bent een **Architecture Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Architecture
- Patterns
- Scalability
</ultrathink>

## FOCUS AREAS
- Architecture
- Patterns
- Scalability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

---

## Deelgebied 20: Monitoring (~860 LOC)

### Files
- `monitoring/*.py`

### Agent 20A: Code Reviewer - Monitoring

```python
Task(
    subagent_type="code-reviewer",
    description="Monitoring Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Monitoring

## Target: monitoring/*.py (~860 LOC)

Je bent een **Code Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Code quality
- Best practices
- Maintainability
</ultrathink>

## FOCUS AREAS
- Code quality
- Best practices
- Maintainability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 20B: Full Stack Developer - Monitoring

```python
Task(
    subagent_type="full-stack-developer",
    description="Monitoring Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Monitoring

## Target: monitoring/*.py (~860 LOC)

Je bent een **Full Stack Developer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Implementation
- Edge cases
- Integration
</ultrathink>

## FOCUS AREAS
- Implementation
- Edge cases
- Integration

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 20C: Architecture Reviewer - Monitoring

```python
Task(
    subagent_type="architecture-reviewer",
    description="Monitoring Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Monitoring

## Target: monitoring/*.py (~860 LOC)

Je bent een **Architecture Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Architecture
- Patterns
- Scalability
</ultrathink>

## FOCUS AREAS
- Architecture
- Patterns
- Scalability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

---

## Deelgebied 21: Voorbeelden (~1,675 LOC)

### Files
- `voorbeelden/*.py`

### Agent 21A: Code Reviewer - Voorbeelden

```python
Task(
    subagent_type="code-reviewer",
    description="Voorbeelden Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Voorbeelden

## Target: voorbeelden/*.py (~1,675 LOC)

Je bent een **Code Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Code quality
- Best practices
- Maintainability
</ultrathink>

## FOCUS AREAS
- Code quality
- Best practices
- Maintainability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 21B: Full Stack Developer - Voorbeelden

```python
Task(
    subagent_type="full-stack-developer",
    description="Voorbeelden Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Voorbeelden

## Target: voorbeelden/*.py (~1,675 LOC)

Je bent een **Full Stack Developer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Implementation
- Edge cases
- Integration
</ultrathink>

## FOCUS AREAS
- Implementation
- Edge cases
- Integration

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 21C: Architecture Reviewer - Voorbeelden

```python
Task(
    subagent_type="architecture-reviewer",
    description="Voorbeelden Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Voorbeelden

## Target: voorbeelden/*.py (~1,675 LOC)

Je bent een **Architecture Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Architecture
- Patterns
- Scalability
</ultrathink>

## FOCUS AREAS
- Architecture
- Patterns
- Scalability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

---

## Deelgebied 22: Pages (~614 LOC)

### Files
- `pages/*.py`

### Agent 22A: Code Reviewer - Pages

```python
Task(
    subagent_type="code-reviewer",
    description="Pages Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Pages

## Target: pages/*.py (~614 LOC)

Je bent een **Code Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Code quality
- Best practices
- Maintainability
</ultrathink>

## FOCUS AREAS
- Code quality
- Best practices
- Maintainability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 22B: Full Stack Developer - Pages

```python
Task(
    subagent_type="full-stack-developer",
    description="Pages Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Pages

## Target: pages/*.py (~614 LOC)

Je bent een **Full Stack Developer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Implementation
- Edge cases
- Integration
</ultrathink>

## FOCUS AREAS
- Implementation
- Edge cases
- Integration

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 22C: Architecture Reviewer - Pages

```python
Task(
    subagent_type="architecture-reviewer",
    description="Pages Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Pages

## Target: pages/*.py (~614 LOC)

Je bent een **Architecture Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Architecture
- Patterns
- Scalability
</ultrathink>

## FOCUS AREAS
- Architecture
- Patterns
- Scalability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

---

## Deelgebied 23: Domain (~505 LOC)

### Files
- `domain/context/*.py`
- `domain/juridisch/*.py`
- `domain/autoriteit/*.py`
- `domain/linguistisch/*.py`
- `domain/*.py`

### Agent 23A: Code Reviewer - Domain

```python
Task(
    subagent_type="code-reviewer",
    description="Domain Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Domain

## Target: domain/context/*.py, domain/juridisch/*.py, ... (~505 LOC)

Je bent een **Code Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Code quality
- Best practices
- Maintainability
</ultrathink>

## FOCUS AREAS
- Code quality
- Best practices
- Maintainability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 23B: Full Stack Developer - Domain

```python
Task(
    subagent_type="full-stack-developer",
    description="Domain Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Domain

## Target: domain/context/*.py, domain/juridisch/*.py, ... (~505 LOC)

Je bent een **Full Stack Developer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Implementation
- Edge cases
- Integration
</ultrathink>

## FOCUS AREAS
- Implementation
- Edge cases
- Integration

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 23C: Architecture Reviewer - Domain

```python
Task(
    subagent_type="architecture-reviewer",
    description="Domain Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Domain

## Target: domain/context/*.py, domain/juridisch/*.py, ... (~505 LOC)

Je bent een **Architecture Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Architecture
- Patterns
- Scalability
</ultrathink>

## FOCUS AREAS
- Architecture
- Patterns
- Scalability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

---

## Deelgebied 24: Regels (~3,304 LOC)

### Files
- `toetsregels/regels/*.py`

### Agent 24A: Code Reviewer - Regels

```python
Task(
    subagent_type="code-reviewer",
    description="Regels Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Regels

## Target: toetsregels/regels/*.py (~3,304 LOC)

Je bent een **Code Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Code quality
- Best practices
- Maintainability
</ultrathink>

## FOCUS AREAS
- Code quality
- Best practices
- Maintainability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 24B: Full Stack Developer - Regels

```python
Task(
    subagent_type="full-stack-developer",
    description="Regels Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Regels

## Target: toetsregels/regels/*.py (~3,304 LOC)

Je bent een **Full Stack Developer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Implementation
- Edge cases
- Integration
</ultrathink>

## FOCUS AREAS
- Implementation
- Edge cases
- Integration

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 24C: Architecture Reviewer - Regels

```python
Task(
    subagent_type="architecture-reviewer",
    description="Regels Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Regels

## Target: toetsregels/regels/*.py (~3,304 LOC)

Je bent een **Architecture Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Architecture
- Patterns
- Scalability
</ultrathink>

## FOCUS AREAS
- Architecture
- Patterns
- Scalability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

---

## Deelgebied 25: Validators (~3,244 LOC)

### Files
- `toetsregels/validators/*.py`

### Agent 25A: Code Reviewer - Validators

```python
Task(
    subagent_type="code-reviewer",
    description="Validators Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Validators

## Target: toetsregels/validators/*.py (~3,244 LOC)

Je bent een **Code Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Code quality
- Best practices
- Maintainability
</ultrathink>

## FOCUS AREAS
- Code quality
- Best practices
- Maintainability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 25B: Full Stack Developer - Validators

```python
Task(
    subagent_type="full-stack-developer",
    description="Validators Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Validators

## Target: toetsregels/validators/*.py (~3,244 LOC)

Je bent een **Full Stack Developer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Implementation
- Edge cases
- Integration
</ultrathink>

## FOCUS AREAS
- Implementation
- Edge cases
- Integration

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 25C: Architecture Reviewer - Validators

```python
Task(
    subagent_type="architecture-reviewer",
    description="Validators Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Validators

## Target: toetsregels/validators/*.py (~3,244 LOC)

Je bent een **Architecture Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Architecture
- Patterns
- Scalability
</ultrathink>

## FOCUS AREAS
- Architecture
- Patterns
- Scalability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

---

## Deelgebied 26: Services (~10,127 LOC) (MONSTER FILE)

### Files
- `services/*.py`

### Agent 26A: Code Reviewer - Services

```python
Task(
    subagent_type="code-reviewer",
    description="Services Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Services

## Target: services/*.py (~10,127 LOC)

Je bent een **Code Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Code quality
- Best practices
- Maintainability
</ultrathink>

## FOCUS AREAS
- Code quality
- Best practices
- Maintainability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 26B: Full Stack Developer - Services

```python
Task(
    subagent_type="full-stack-developer",
    description="Services Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Services

## Target: services/*.py (~10,127 LOC)

Je bent een **Full Stack Developer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Implementation
- Edge cases
- Integration
</ultrathink>

## FOCUS AREAS
- Implementation
- Edge cases
- Integration

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 26C: Architecture Reviewer - Services

```python
Task(
    subagent_type="architecture-reviewer",
    description="Services Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Services

## Target: services/*.py (~10,127 LOC)

Je bent een **Architecture Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Architecture
- Patterns
- Scalability
</ultrathink>

## FOCUS AREAS
- Architecture
- Patterns
- Scalability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 26D: Code Simplifier - Services

```python
Task(
    subagent_type="code-simplifier",
    description="Services Code Simplifier Analysis",
    prompt="""
# CODE SIMPLIFIER ANALYSIS: Services

## Target: services/*.py (~10,127 LOC)

Je bent een **Code Simplifier** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Complexity
- Refactoring
- Splitting
</ultrathink>

## FOCUS AREAS
- Complexity
- Refactoring
- Splitting

## OUTPUT FORMAT (MAX 300 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

---

## Deelgebied 27: Orchestrators (~1,104 LOC)

### Files
- `services/orchestrators/*.py`

### Agent 27A: Code Reviewer - Orchestrators

```python
Task(
    subagent_type="code-reviewer",
    description="Orchestrators Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Orchestrators

## Target: services/orchestrators/*.py (~1,104 LOC)

Je bent een **Code Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Code quality
- Best practices
- Maintainability
</ultrathink>

## FOCUS AREAS
- Code quality
- Best practices
- Maintainability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 27B: Full Stack Developer - Orchestrators

```python
Task(
    subagent_type="full-stack-developer",
    description="Orchestrators Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Orchestrators

## Target: services/orchestrators/*.py (~1,104 LOC)

Je bent een **Full Stack Developer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Implementation
- Edge cases
- Integration
</ultrathink>

## FOCUS AREAS
- Implementation
- Edge cases
- Integration

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 27C: Architecture Reviewer - Orchestrators

```python
Task(
    subagent_type="architecture-reviewer",
    description="Orchestrators Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Orchestrators

## Target: services/orchestrators/*.py (~1,104 LOC)

Je bent een **Architecture Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Architecture
- Patterns
- Scalability
</ultrathink>

## FOCUS AREAS
- Architecture
- Patterns
- Scalability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

---

## Deelgebied 28: Validation (~2,962 LOC) (MONSTER FILE)

### Files
- `services/validation/*.py`

### Agent 28A: Code Reviewer - Validation

```python
Task(
    subagent_type="code-reviewer",
    description="Validation Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Validation

## Target: services/validation/*.py (~2,962 LOC)

Je bent een **Code Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Code quality
- Best practices
- Maintainability
</ultrathink>

## FOCUS AREAS
- Code quality
- Best practices
- Maintainability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 28B: Full Stack Developer - Validation

```python
Task(
    subagent_type="full-stack-developer",
    description="Validation Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Validation

## Target: services/validation/*.py (~2,962 LOC)

Je bent een **Full Stack Developer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Implementation
- Edge cases
- Integration
</ultrathink>

## FOCUS AREAS
- Implementation
- Edge cases
- Integration

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 28C: Architecture Reviewer - Validation

```python
Task(
    subagent_type="architecture-reviewer",
    description="Validation Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Validation

## Target: services/validation/*.py (~2,962 LOC)

Je bent een **Architecture Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Architecture
- Patterns
- Scalability
</ultrathink>

## FOCUS AREAS
- Architecture
- Patterns
- Scalability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 28D: Code Simplifier - Validation

```python
Task(
    subagent_type="code-simplifier",
    description="Validation Code Simplifier Analysis",
    prompt="""
# CODE SIMPLIFIER ANALYSIS: Validation

## Target: services/validation/*.py (~2,962 LOC)

Je bent een **Code Simplifier** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Complexity
- Refactoring
- Splitting
</ultrathink>

## FOCUS AREAS
- Complexity
- Refactoring
- Splitting

## OUTPUT FORMAT (MAX 300 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

---

## Deelgebied 29: Web Lookup (~2,772 LOC)

### Files
- `services/web_lookup/*.py`

### Agent 29A: Code Reviewer - Web Lookup

```python
Task(
    subagent_type="code-reviewer",
    description="Web Lookup Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Web Lookup

## Target: services/web_lookup/*.py (~2,772 LOC)

Je bent een **Code Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Code quality
- Best practices
- Maintainability
</ultrathink>

## FOCUS AREAS
- Code quality
- Best practices
- Maintainability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 29B: Full Stack Developer - Web Lookup

```python
Task(
    subagent_type="full-stack-developer",
    description="Web Lookup Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Web Lookup

## Target: services/web_lookup/*.py (~2,772 LOC)

Je bent een **Full Stack Developer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Implementation
- Edge cases
- Integration
</ultrathink>

## FOCUS AREAS
- Implementation
- Edge cases
- Integration

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 29C: Architecture Reviewer - Web Lookup

```python
Task(
    subagent_type="architecture-reviewer",
    description="Web Lookup Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Web Lookup

## Target: services/web_lookup/*.py (~2,772 LOC)

Je bent een **Architecture Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Architecture
- Patterns
- Scalability
</ultrathink>

## FOCUS AREAS
- Architecture
- Patterns
- Scalability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

---

## Deelgebied 30: Modules (~1,824 LOC)

### Files
- `services/prompts/modules/*.py`

### Agent 30A: Code Reviewer - Modules

```python
Task(
    subagent_type="code-reviewer",
    description="Modules Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Modules

## Target: services/prompts/modules/*.py (~1,824 LOC)

Je bent een **Code Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Code quality
- Best practices
- Maintainability
</ultrathink>

## FOCUS AREAS
- Code quality
- Best practices
- Maintainability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 30B: Full Stack Developer - Modules

```python
Task(
    subagent_type="full-stack-developer",
    description="Modules Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Modules

## Target: services/prompts/modules/*.py (~1,824 LOC)

Je bent een **Full Stack Developer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Implementation
- Edge cases
- Integration
</ultrathink>

## FOCUS AREAS
- Implementation
- Edge cases
- Integration

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 30C: Architecture Reviewer - Modules

```python
Task(
    subagent_type="architecture-reviewer",
    description="Modules Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Modules

## Target: services/prompts/modules/*.py (~1,824 LOC)

Je bent een **Architecture Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Architecture
- Patterns
- Scalability
</ultrathink>

## FOCUS AREAS
- Architecture
- Patterns
- Scalability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

---

## Deelgebied 31: Validation (~2,532 LOC)

### Files
- `validation/*.py`

### Agent 31A: Code Reviewer - Validation

```python
Task(
    subagent_type="code-reviewer",
    description="Validation Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Validation

## Target: validation/*.py (~2,532 LOC)

Je bent een **Code Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Code quality
- Best practices
- Maintainability
</ultrathink>

## FOCUS AREAS
- Code quality
- Best practices
- Maintainability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 31B: Full Stack Developer - Validation

```python
Task(
    subagent_type="full-stack-developer",
    description="Validation Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Validation

## Target: validation/*.py (~2,532 LOC)

Je bent een **Full Stack Developer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Implementation
- Edge cases
- Integration
</ultrathink>

## FOCUS AREAS
- Implementation
- Edge cases
- Integration

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

### Agent 31C: Architecture Reviewer - Validation

```python
Task(
    subagent_type="architecture-reviewer",
    description="Validation Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Validation

## Target: validation/*.py (~2,532 LOC)

Je bent een **Architecture Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Architecture
- Patterns
- Scalability
</ultrathink>

## FOCUS AREAS
- Architecture
- Patterns
- Scalability

## OUTPUT FORMAT (MAX 250 WOORDEN)

```xml
<agent_output>
  <health_score>X.X/10</health_score>
  <findings>
    <finding severity="CRITICAL|HIGH|MEDIUM|LOW|INFO">
      <location file="path/file.py" line="123"/>
      <description>Clear description of the issue</description>
      <evidence><![CDATA[code snippet]]></evidence>
      <recommendation>Specific fix suggestion</recommendation>
      <impact>Why this matters</impact>
    </finding>
  </findings>
</agent_output>
```

**VERIFICATIE VEREIST**: Na elke file edit:
1. `grep -n "expected_pattern" file` - Controleer aanwezigheid
2. `git status --short` - Controleer modificatie
3. Rapporteer: `<verification status="VERIFIED|FAILED"/>`
Bij falen: RE-RUN edit, NIET doorgaan.
""",
    model="opus"
)
```

---

## Synthesis Protocol

### Step 1: Voting per Deelgebied

Voor elk van de 31 deelgebieden, vul de voting matrix in met alle bevindingen.

### Step 2: Merge Results

Combineer bevindingen per deelgebied:
- **FULL CONSENSUS**: Alle agents agree → Hoogste prioriteit
- **ACCEPTED (60%+)**: 2/3 agree → Normale prioriteit
- **MINORITY**: <60% → Documenteer als "mogelijke issue"

### Step 3: Cross-Deelgebied Deduplicatie

Identificeer issues die meerdere deelgebieden raken:
- Merge duplicates met verwijzing naar alle relevante locaties
- Verhoog severity als issue cross-cutting is

### Step 4: Global Prioritization

Sorteer op: `severity × consensus_weight × impact`

**Prioriteit Berekening:**
```
CRITICAL + FULL CONSENSUS = P1 (Immediate)
CRITICAL + ACCEPTED       = P2 (High)
HIGH + FULL CONSENSUS     = P2 (High)
HIGH + ACCEPTED           = P3 (Medium)
MEDIUM + any              = P4 (Low)
LOW + any                 = P5 (Backlog)
```

### Step 5: Generate Final Report

**Inclusief:**
1. Executive Summary (max 200 woorden)
2. Overall Health Score (gewogen gemiddelde)
3. Top 10 Issues (gesorteerd op prioriteit)
4. Per-deelgebied scores
5. Dissenting opinions (minority views)
6. Recommended action sequence

### Final Report Template

```markdown
# [Orchestrator Type] Report

## Executive Summary
[2-3 zinnen over overall status]

## Health Scores
| Deelgebied | Score | Status |
|------------|-------|--------|
| ...        | X/10  | ✅/⚠️/❌ |

**Overall Score:** X.X/10

## Top Issues

### P1: Immediate Action Required
1. [Issue] - file:line
   - Consensus: X/3 agents
   - Impact: [description]
   - Fix: [recommendation]

### P2: High Priority
...

## Minority Views
[Issues flagged by 1 agent but not accepted by consensus]

## Action Sequence
1. [First action]
2. [Second action]
...
```

---