---
prompt_id: architecture-analysis
version: "1.0.0"
compatible_models: ["claude-opus-4-5", "claude-sonnet-4"]
requires_ultrathink: true
generated_at: "2026-01-15T09:56:56.406889"
---

# Ultra-Deep Architecture Analysis
## Orchestrator + 90 Subagent Architecture (3 per Deelgebied)

---

## Execution Context

**Target:** Project: definitie-app
**Architecture:** 1 Orchestrator + 90 Subagents (3 per deelgebied)
**Per Deelgebied:** Code Reviewer + Full Stack Developer + Architecture Reviewer
**Mode:** Ultrathink Executive Analysis
**Output:** Structured findings with consensus voting

---

## Orchestrator Instructions

Je bent de **Ultra-Deep Architecture Analysis Orchestrator**. Je coördineert 90 parallelle subagents die elk een specifiek deelgebied analyseren.

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

1. **Spawn alle 90 subagents parallel** via Task() tool in één message
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

**Per Deelgebied:** 3 agents × 31 deelgebieden = 90 subagents
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

## Deelgebied 1: Services Core (DI & Interfaces) (~2,807 LOC)

### Files
- `services/container.py`
- `services/service_factory.py`
- `services/interfaces.py`

### Agent 1A: Code Reviewer - Services Core (DI & Interfaces)

```python
Task(
    subagent_type="code-reviewer",
    description="Services Core (DI & Interfaces) Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Services Core (DI & Interfaces)

## Target: services/container.py, services/service_factory.py, ... (~2,807 LOC)

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

### Agent 1B: Full Stack Developer - Services Core (DI & Interfaces)

```python
Task(
    subagent_type="full-stack-developer",
    description="Services Core (DI & Interfaces) Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Services Core (DI & Interfaces)

## Target: services/container.py, services/service_factory.py, ... (~2,807 LOC)

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

### Agent 1C: Architecture Reviewer - Services Core (DI & Interfaces)

```python
Task(
    subagent_type="architecture-reviewer",
    description="Services Core (DI & Interfaces) Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Services Core (DI & Interfaces)

## Target: services/container.py, services/service_factory.py, ... (~2,807 LOC)

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

## Deelgebied 2: Definition Repository & Edit (~2,543 LOC)

### Files
- `services/definition_repository.py`
- `services/definition_edit_service.py`
- `services/definition_edit_repository.py`
- `services/definition_import_service.py`

### Agent 2A: Code Reviewer - Definition Repository & Edit

```python
Task(
    subagent_type="code-reviewer",
    description="Definition Repository & Edit Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Definition Repository & Edit

## Target: services/definition_repository.py, services/definition_edit_service.py, ... (~2,543 LOC)

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

### Agent 2B: Full Stack Developer - Definition Repository & Edit

```python
Task(
    subagent_type="full-stack-developer",
    description="Definition Repository & Edit Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Definition Repository & Edit

## Target: services/definition_repository.py, services/definition_edit_service.py, ... (~2,543 LOC)

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

### Agent 2C: Architecture Reviewer - Definition Repository & Edit

```python
Task(
    subagent_type="architecture-reviewer",
    description="Definition Repository & Edit Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Definition Repository & Edit

## Target: services/definition_repository.py, services/definition_edit_service.py, ... (~2,543 LOC)

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

## Deelgebied 3: Definition Generation (~2,459 LOC)

### Files
- `services/definition_generator_*.py`
- `services/unified_definition_generator.py`

### Agent 3A: Code Reviewer - Definition Generation

```python
Task(
    subagent_type="code-reviewer",
    description="Definition Generation Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Definition Generation

## Target: services/definition_generator_*.py, services/unified_definition_generator.py (~2,459 LOC)

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

### Agent 3B: Full Stack Developer - Definition Generation

```python
Task(
    subagent_type="full-stack-developer",
    description="Definition Generation Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Definition Generation

## Target: services/definition_generator_*.py, services/unified_definition_generator.py (~2,459 LOC)

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

### Agent 3C: Architecture Reviewer - Definition Generation

```python
Task(
    subagent_type="architecture-reviewer",
    description="Definition Generation Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Definition Generation

## Target: services/definition_generator_*.py, services/unified_definition_generator.py (~2,459 LOC)

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

## Deelgebied 4: UFO Pattern Matching (~2,072 LOC) (MONSTER FILE)

### Files
- `services/ufo_pattern_matcher.py`
- `services/ufo_classifier_service.py`

### Agent 4A: Code Reviewer - UFO Pattern Matching

```python
Task(
    subagent_type="code-reviewer",
    description="UFO Pattern Matching Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: UFO Pattern Matching

## Target: services/ufo_pattern_matcher.py, services/ufo_classifier_service.py (~2,072 LOC)

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

### Agent 4B: Code Simplifier - UFO Pattern Matching

```python
Task(
    subagent_type="code-simplifier",
    description="UFO Pattern Matching Code Simplifier Analysis",
    prompt="""
# CODE SIMPLIFIER ANALYSIS: UFO Pattern Matching

## Target: services/ufo_pattern_matcher.py, services/ufo_classifier_service.py (~2,072 LOC)

Je bent een **Code Simplifier** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Complexity reduction
- Refactoring
- Splitting
</ultrathink>

## FOCUS AREAS
- Complexity reduction
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

### Agent 4C: Architecture Reviewer - UFO Pattern Matching

```python
Task(
    subagent_type="architecture-reviewer",
    description="UFO Pattern Matching Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: UFO Pattern Matching

## Target: services/ufo_pattern_matcher.py, services/ufo_classifier_service.py (~2,072 LOC)

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

## Deelgebied 5: Workflow Services (~1,380 LOC)

### Files
- `services/workflow_service.py`
- `services/definition_workflow_service.py`

### Agent 5A: Code Reviewer - Workflow Services

```python
Task(
    subagent_type="code-reviewer",
    description="Workflow Services Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Workflow Services

## Target: services/workflow_service.py, services/definition_workflow_service.py (~1,380 LOC)

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

### Agent 5B: Full Stack Developer - Workflow Services

```python
Task(
    subagent_type="full-stack-developer",
    description="Workflow Services Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Workflow Services

## Target: services/workflow_service.py, services/definition_workflow_service.py (~1,380 LOC)

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

### Agent 5C: Architecture Reviewer - Workflow Services

```python
Task(
    subagent_type="architecture-reviewer",
    description="Workflow Services Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Workflow Services

## Target: services/workflow_service.py, services/definition_workflow_service.py (~1,380 LOC)

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

## Deelgebied 6: Export & Synonym Services (~1,448 LOC)

### Files
- `services/export_service.py`
- `services/synonym_orchestrator.py`

### Agent 6A: Code Reviewer - Export & Synonym Services

```python
Task(
    subagent_type="code-reviewer",
    description="Export & Synonym Services Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Export & Synonym Services

## Target: services/export_service.py, services/synonym_orchestrator.py (~1,448 LOC)

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

### Agent 6B: Full Stack Developer - Export & Synonym Services

```python
Task(
    subagent_type="full-stack-developer",
    description="Export & Synonym Services Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Export & Synonym Services

## Target: services/export_service.py, services/synonym_orchestrator.py (~1,448 LOC)

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

### Agent 6C: Architecture Reviewer - Export & Synonym Services

```python
Task(
    subagent_type="architecture-reviewer",
    description="Export & Synonym Services Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Export & Synonym Services

## Target: services/export_service.py, services/synonym_orchestrator.py (~1,448 LOC)

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

## Deelgebied 7: AB Testing & Data Aggregation (~1,021 LOC)

### Files
- `services/ab_testing_framework.py`
- `services/data_aggregation_service.py`

### Agent 7A: Code Reviewer - AB Testing & Data Aggregation

```python
Task(
    subagent_type="code-reviewer",
    description="AB Testing & Data Aggregation Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: AB Testing & Data Aggregation

## Target: services/ab_testing_framework.py, services/data_aggregation_service.py (~1,021 LOC)

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

### Agent 7B: Full Stack Developer - AB Testing & Data Aggregation

```python
Task(
    subagent_type="full-stack-developer",
    description="AB Testing & Data Aggregation Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: AB Testing & Data Aggregation

## Target: services/ab_testing_framework.py, services/data_aggregation_service.py (~1,021 LOC)

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

### Agent 7C: Architecture Reviewer - AB Testing & Data Aggregation

```python
Task(
    subagent_type="architecture-reviewer",
    description="AB Testing & Data Aggregation Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: AB Testing & Data Aggregation

## Target: services/ab_testing_framework.py, services/data_aggregation_service.py (~1,021 LOC)

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

## Deelgebied 8: Web Lookup Services (~4,692 LOC)

### Files
- `services/web_lookup/*.py`

### Agent 8A: Code Reviewer - Web Lookup Services

```python
Task(
    subagent_type="code-reviewer",
    description="Web Lookup Services Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Web Lookup Services

## Target: services/web_lookup/*.py (~4,692 LOC)

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

### Agent 8B: Full Stack Developer - Web Lookup Services

```python
Task(
    subagent_type="full-stack-developer",
    description="Web Lookup Services Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Web Lookup Services

## Target: services/web_lookup/*.py (~4,692 LOC)

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

### Agent 8C: Architecture Reviewer - Web Lookup Services

```python
Task(
    subagent_type="architecture-reviewer",
    description="Web Lookup Services Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Web Lookup Services

## Target: services/web_lookup/*.py (~4,692 LOC)

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

## Deelgebied 9: Prompt Services (~4,796 LOC)

### Files
- `services/prompts/**/*.py`

### Agent 9A: Code Reviewer - Prompt Services

```python
Task(
    subagent_type="code-reviewer",
    description="Prompt Services Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Prompt Services

## Target: services/prompts/**/*.py (~4,796 LOC)

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

### Agent 9B: Full Stack Developer - Prompt Services

```python
Task(
    subagent_type="full-stack-developer",
    description="Prompt Services Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Prompt Services

## Target: services/prompts/**/*.py (~4,796 LOC)

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

### Agent 9C: Architecture Reviewer - Prompt Services

```python
Task(
    subagent_type="architecture-reviewer",
    description="Prompt Services Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Prompt Services

## Target: services/prompts/**/*.py (~4,796 LOC)

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

## Deelgebied 10: Validation Services (~4,356 LOC)

### Files
- `services/validation/*.py`

### Agent 10A: Code Reviewer - Validation Services

```python
Task(
    subagent_type="code-reviewer",
    description="Validation Services Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Validation Services

## Target: services/validation/*.py (~4,356 LOC)

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

### Agent 10B: Full Stack Developer - Validation Services

```python
Task(
    subagent_type="full-stack-developer",
    description="Validation Services Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Validation Services

## Target: services/validation/*.py (~4,356 LOC)

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

### Agent 10C: Architecture Reviewer - Validation Services

```python
Task(
    subagent_type="architecture-reviewer",
    description="Validation Services Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Validation Services

## Target: services/validation/*.py (~4,356 LOC)

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

## Deelgebied 11: Service Orchestrators (~1,596 LOC)

### Files
- `services/orchestrators/*.py`

### Agent 11A: Code Reviewer - Service Orchestrators

```python
Task(
    subagent_type="code-reviewer",
    description="Service Orchestrators Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Service Orchestrators

## Target: services/orchestrators/*.py (~1,596 LOC)

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

### Agent 11B: Full Stack Developer - Service Orchestrators

```python
Task(
    subagent_type="full-stack-developer",
    description="Service Orchestrators Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Service Orchestrators

## Target: services/orchestrators/*.py (~1,596 LOC)

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

### Agent 11C: Architecture Reviewer - Service Orchestrators

```python
Task(
    subagent_type="architecture-reviewer",
    description="Service Orchestrators Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Service Orchestrators

## Target: services/orchestrators/*.py (~1,596 LOC)

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

## Deelgebied 12: Toetsregels Core (~1,599 LOC)

### Files
- `toetsregels/*.py`

### Agent 12A: Code Reviewer - Toetsregels Core

```python
Task(
    subagent_type="code-reviewer",
    description="Toetsregels Core Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Toetsregels Core

## Target: toetsregels/*.py (~1,599 LOC)

Je bent een **Code Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Rule consistency
- Dutch language
- Error messages
</ultrathink>

## FOCUS AREAS
- Rule consistency
- Dutch language
- Error messages

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

### Agent 12B: Full Stack Developer - Toetsregels Core

```python
Task(
    subagent_type="full-stack-developer",
    description="Toetsregels Core Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Toetsregels Core

## Target: toetsregels/*.py (~1,599 LOC)

Je bent een **Full Stack Developer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Edge cases
- Performance
- Test coverage
</ultrathink>

## FOCUS AREAS
- Edge cases
- Performance
- Test coverage

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

## Deelgebied 13: Toetsregels Implementaties (~6,499 LOC)

### Files
- `toetsregels/regels/*.py`

### Agent 13A: Code Reviewer - Toetsregels Implementaties

```python
Task(
    subagent_type="code-reviewer",
    description="Toetsregels Implementaties Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Toetsregels Implementaties

## Target: toetsregels/regels/*.py (~6,499 LOC)

Je bent een **Code Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Rule consistency
- Dutch language
- Error messages
</ultrathink>

## FOCUS AREAS
- Rule consistency
- Dutch language
- Error messages

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

### Agent 13B: Full Stack Developer - Toetsregels Implementaties

```python
Task(
    subagent_type="full-stack-developer",
    description="Toetsregels Implementaties Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Toetsregels Implementaties

## Target: toetsregels/regels/*.py (~6,499 LOC)

Je bent een **Full Stack Developer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Edge cases
- Performance
- Test coverage
</ultrathink>

## FOCUS AREAS
- Edge cases
- Performance
- Test coverage

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

## Deelgebied 14: Toetsregels Validators (~6,383 LOC)

### Files
- `toetsregels/validators/*.py`

### Agent 14A: Code Reviewer - Toetsregels Validators

```python
Task(
    subagent_type="code-reviewer",
    description="Toetsregels Validators Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Toetsregels Validators

## Target: toetsregels/validators/*.py (~6,383 LOC)

Je bent een **Code Reviewer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Rule consistency
- Dutch language
- Error messages
</ultrathink>

## FOCUS AREAS
- Rule consistency
- Dutch language
- Error messages

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

### Agent 14B: Full Stack Developer - Toetsregels Validators

```python
Task(
    subagent_type="full-stack-developer",
    description="Toetsregels Validators Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Toetsregels Validators

## Target: toetsregels/validators/*.py (~6,383 LOC)

Je bent een **Full Stack Developer** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Edge cases
- Performance
- Test coverage
</ultrathink>

## FOCUS AREAS
- Edge cases
- Performance
- Test coverage

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

## Deelgebied 15: Definition Generator Tab (~2,528 LOC) (MONSTER FILE)

### Files
- `ui/components/definition_generator_tab.py`

### Agent 15A: Code Reviewer - Definition Generator Tab

```python
Task(
    subagent_type="code-reviewer",
    description="Definition Generator Tab Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Definition Generator Tab

## Target: ui/components/definition_generator_tab.py (~2,528 LOC)

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

### Agent 15B: Code Simplifier - Definition Generator Tab

```python
Task(
    subagent_type="code-simplifier",
    description="Definition Generator Tab Code Simplifier Analysis",
    prompt="""
# CODE SIMPLIFIER ANALYSIS: Definition Generator Tab

## Target: ui/components/definition_generator_tab.py (~2,528 LOC)

Je bent een **Code Simplifier** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Complexity reduction
- Refactoring
- Splitting
</ultrathink>

## FOCUS AREAS
- Complexity reduction
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

### Agent 15C: Architecture Reviewer - Definition Generator Tab

```python
Task(
    subagent_type="architecture-reviewer",
    description="Definition Generator Tab Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Definition Generator Tab

## Target: ui/components/definition_generator_tab.py (~2,528 LOC)

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

## Deelgebied 16: Definition Edit Tab (~1,905 LOC) (MONSTER FILE)

### Files
- `ui/components/definition_edit_tab.py`

### Agent 16A: Code Reviewer - Definition Edit Tab

```python
Task(
    subagent_type="code-reviewer",
    description="Definition Edit Tab Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Definition Edit Tab

## Target: ui/components/definition_edit_tab.py (~1,905 LOC)

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

### Agent 16B: Code Simplifier - Definition Edit Tab

```python
Task(
    subagent_type="code-simplifier",
    description="Definition Edit Tab Code Simplifier Analysis",
    prompt="""
# CODE SIMPLIFIER ANALYSIS: Definition Edit Tab

## Target: ui/components/definition_edit_tab.py (~1,905 LOC)

Je bent een **Code Simplifier** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Complexity reduction
- Refactoring
- Splitting
</ultrathink>

## FOCUS AREAS
- Complexity reduction
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

### Agent 16C: Architecture Reviewer - Definition Edit Tab

```python
Task(
    subagent_type="architecture-reviewer",
    description="Definition Edit Tab Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Definition Edit Tab

## Target: ui/components/definition_edit_tab.py (~1,905 LOC)

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

## Deelgebied 17: Expert Review Tab (~1,440 LOC) (MONSTER FILE)

### Files
- `ui/components/expert_review_tab.py`

### Agent 17A: Code Reviewer - Expert Review Tab

```python
Task(
    subagent_type="code-reviewer",
    description="Expert Review Tab Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Expert Review Tab

## Target: ui/components/expert_review_tab.py (~1,440 LOC)

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

### Agent 17B: Code Simplifier - Expert Review Tab

```python
Task(
    subagent_type="code-simplifier",
    description="Expert Review Tab Code Simplifier Analysis",
    prompt="""
# CODE SIMPLIFIER ANALYSIS: Expert Review Tab

## Target: ui/components/expert_review_tab.py (~1,440 LOC)

Je bent een **Code Simplifier** met executive focus.

<ultrathink>
Analyseer DIEPGAAND. Focus op:
- Complexity reduction
- Refactoring
- Splitting
</ultrathink>

## FOCUS AREAS
- Complexity reduction
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

### Agent 17C: Architecture Reviewer - Expert Review Tab

```python
Task(
    subagent_type="architecture-reviewer",
    description="Expert Review Tab Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Expert Review Tab

## Target: ui/components/expert_review_tab.py (~1,440 LOC)

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

## Deelgebied 18: UI Core (~3,926 LOC)

### Files
- `ui/*.py`

### Agent 18A: Code Reviewer - UI Core

```python
Task(
    subagent_type="code-reviewer",
    description="UI Core Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: UI Core

## Target: ui/*.py (~3,926 LOC)

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

### Agent 18B: Full Stack Developer - UI Core

```python
Task(
    subagent_type="full-stack-developer",
    description="UI Core Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: UI Core

## Target: ui/*.py (~3,926 LOC)

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

### Agent 18C: Architecture Reviewer - UI Core

```python
Task(
    subagent_type="architecture-reviewer",
    description="UI Core Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: UI Core

## Target: ui/*.py (~3,926 LOC)

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

## Deelgebied 19: UI Components (Misc) (~2,800 LOC)

### Files
- `ui/components/*.py`
- `ui/components/**/*.py`

### Agent 19A: Code Reviewer - UI Components (Misc)

```python
Task(
    subagent_type="code-reviewer",
    description="UI Components (Misc) Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: UI Components (Misc)

## Target: ui/components/*.py, ui/components/**/*.py (~2,800 LOC)

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

### Agent 19B: Full Stack Developer - UI Components (Misc)

```python
Task(
    subagent_type="full-stack-developer",
    description="UI Components (Misc) Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: UI Components (Misc)

## Target: ui/components/*.py, ui/components/**/*.py (~2,800 LOC)

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

### Agent 19C: Architecture Reviewer - UI Components (Misc)

```python
Task(
    subagent_type="architecture-reviewer",
    description="UI Components (Misc) Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: UI Components (Misc)

## Target: ui/components/*.py, ui/components/**/*.py (~2,800 LOC)

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

## Deelgebied 20: UI Tabs & Helpers (~2,027 LOC)

### Files
- `ui/tabs/*.py`
- `ui/tabs/**/*.py`
- `ui/helpers/*.py`

### Agent 20A: Code Reviewer - UI Tabs & Helpers

```python
Task(
    subagent_type="code-reviewer",
    description="UI Tabs & Helpers Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: UI Tabs & Helpers

## Target: ui/tabs/*.py, ui/tabs/**/*.py, ... (~2,027 LOC)

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

### Agent 20B: Full Stack Developer - UI Tabs & Helpers

```python
Task(
    subagent_type="full-stack-developer",
    description="UI Tabs & Helpers Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: UI Tabs & Helpers

## Target: ui/tabs/*.py, ui/tabs/**/*.py, ... (~2,027 LOC)

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

### Agent 20C: Architecture Reviewer - UI Tabs & Helpers

```python
Task(
    subagent_type="architecture-reviewer",
    description="UI Tabs & Helpers Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: UI Tabs & Helpers

## Target: ui/tabs/*.py, ui/tabs/**/*.py, ... (~2,027 LOC)

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

## Deelgebied 21: Database Layer (~5,676 LOC)

### Files
- `database/*.py`
- `database/**/*.py`

### Agent 21A: Code Reviewer - Database Layer

```python
Task(
    subagent_type="code-reviewer",
    description="Database Layer Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Database Layer

## Target: database/*.py, database/**/*.py (~5,676 LOC)

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

### Agent 21B: Full Stack Developer - Database Layer

```python
Task(
    subagent_type="full-stack-developer",
    description="Database Layer Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Database Layer

## Target: database/*.py, database/**/*.py (~5,676 LOC)

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

### Agent 21C: Architecture Reviewer - Database Layer

```python
Task(
    subagent_type="architecture-reviewer",
    description="Database Layer Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Database Layer

## Target: database/*.py, database/**/*.py (~5,676 LOC)

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

## Deelgebied 22: Domain Models (~1,325 LOC)

### Files
- `domain/**/*.py`
- `models/*.py`
- `ontologie/*.py`

### Agent 22A: Code Reviewer - Domain Models

```python
Task(
    subagent_type="code-reviewer",
    description="Domain Models Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Domain Models

## Target: domain/**/*.py, models/*.py, ... (~1,325 LOC)

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

### Agent 22B: Full Stack Developer - Domain Models

```python
Task(
    subagent_type="full-stack-developer",
    description="Domain Models Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Domain Models

## Target: domain/**/*.py, models/*.py, ... (~1,325 LOC)

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

### Agent 22C: Architecture Reviewer - Domain Models

```python
Task(
    subagent_type="architecture-reviewer",
    description="Domain Models Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Domain Models

## Target: domain/**/*.py, models/*.py, ... (~1,325 LOC)

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

## Deelgebied 23: Utils: Resilience & Retry (~1,630 LOC)

### Files
- `utils/resilience.py`
- `utils/integrated_resilience.py`
- `utils/enhanced_retry.py`

### Agent 23A: Code Reviewer - Utils: Resilience & Retry

```python
Task(
    subagent_type="code-reviewer",
    description="Utils: Resilience & Retry Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Utils: Resilience & Retry

## Target: utils/resilience.py, utils/integrated_resilience.py, ... (~1,630 LOC)

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

### Agent 23B: Full Stack Developer - Utils: Resilience & Retry

```python
Task(
    subagent_type="full-stack-developer",
    description="Utils: Resilience & Retry Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Utils: Resilience & Retry

## Target: utils/resilience.py, utils/integrated_resilience.py, ... (~1,630 LOC)

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

### Agent 23C: Architecture Reviewer - Utils: Resilience & Retry

```python
Task(
    subagent_type="architecture-reviewer",
    description="Utils: Resilience & Retry Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Utils: Resilience & Retry

## Target: utils/resilience.py, utils/integrated_resilience.py, ... (~1,630 LOC)

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

## Deelgebied 24: Utils: Caching & Rate Limiting (~1,314 LOC)

### Files
- `utils/cache.py`
- `utils/smart_rate_limiter.py`

### Agent 24A: Code Reviewer - Utils: Caching & Rate Limiting

```python
Task(
    subagent_type="code-reviewer",
    description="Utils: Caching & Rate Limiting Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Utils: Caching & Rate Limiting

## Target: utils/cache.py, utils/smart_rate_limiter.py (~1,314 LOC)

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

### Agent 24B: Full Stack Developer - Utils: Caching & Rate Limiting

```python
Task(
    subagent_type="full-stack-developer",
    description="Utils: Caching & Rate Limiting Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Utils: Caching & Rate Limiting

## Target: utils/cache.py, utils/smart_rate_limiter.py (~1,314 LOC)

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

### Agent 24C: Architecture Reviewer - Utils: Caching & Rate Limiting

```python
Task(
    subagent_type="architecture-reviewer",
    description="Utils: Caching & Rate Limiting Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Utils: Caching & Rate Limiting

## Target: utils/cache.py, utils/smart_rate_limiter.py (~1,314 LOC)

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

## Deelgebied 25: Utils: Core Utilities (~2,067 LOC)

### Files
- `utils/*.py`

### Agent 25A: Code Reviewer - Utils: Core Utilities

```python
Task(
    subagent_type="code-reviewer",
    description="Utils: Core Utilities Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Utils: Core Utilities

## Target: utils/*.py (~2,067 LOC)

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

### Agent 25B: Full Stack Developer - Utils: Core Utilities

```python
Task(
    subagent_type="full-stack-developer",
    description="Utils: Core Utilities Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Utils: Core Utilities

## Target: utils/*.py (~2,067 LOC)

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

### Agent 25C: Architecture Reviewer - Utils: Core Utilities

```python
Task(
    subagent_type="architecture-reviewer",
    description="Utils: Core Utilities Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Utils: Core Utilities

## Target: utils/*.py (~2,067 LOC)

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

## Deelgebied 26: Configuration (~2,095 LOC)

### Files
- `config/*.py`

### Agent 26A: Code Reviewer - Configuration

```python
Task(
    subagent_type="code-reviewer",
    description="Configuration Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Configuration

## Target: config/*.py (~2,095 LOC)

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

### Agent 26B: Full Stack Developer - Configuration

```python
Task(
    subagent_type="full-stack-developer",
    description="Configuration Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Configuration

## Target: config/*.py (~2,095 LOC)

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

### Agent 26C: Architecture Reviewer - Configuration

```python
Task(
    subagent_type="architecture-reviewer",
    description="Configuration Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Configuration

## Target: config/*.py (~2,095 LOC)

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

## Deelgebied 27: Voorbeelden System (~4,946 LOC)

### Files
- `voorbeelden/*.py`
- `voorbeelden/**/*.py`

### Agent 27A: Code Reviewer - Voorbeelden System

```python
Task(
    subagent_type="code-reviewer",
    description="Voorbeelden System Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Voorbeelden System

## Target: voorbeelden/*.py, voorbeelden/**/*.py (~4,946 LOC)

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

### Agent 27B: Full Stack Developer - Voorbeelden System

```python
Task(
    subagent_type="full-stack-developer",
    description="Voorbeelden System Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Voorbeelden System

## Target: voorbeelden/*.py, voorbeelden/**/*.py (~4,946 LOC)

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

### Agent 27C: Architecture Reviewer - Voorbeelden System

```python
Task(
    subagent_type="architecture-reviewer",
    description="Voorbeelden System Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Voorbeelden System

## Target: voorbeelden/*.py, voorbeelden/**/*.py (~4,946 LOC)

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

## Deelgebied 28: Monitoring (~1,298 LOC)

### Files
- `monitoring/*.py`

### Agent 28A: Code Reviewer - Monitoring

```python
Task(
    subagent_type="code-reviewer",
    description="Monitoring Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Monitoring

## Target: monitoring/*.py (~1,298 LOC)

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

### Agent 28B: Full Stack Developer - Monitoring

```python
Task(
    subagent_type="full-stack-developer",
    description="Monitoring Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Monitoring

## Target: monitoring/*.py (~1,298 LOC)

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

### Agent 28C: Architecture Reviewer - Monitoring

```python
Task(
    subagent_type="architecture-reviewer",
    description="Monitoring Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Monitoring

## Target: monitoring/*.py (~1,298 LOC)

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

## Deelgebied 29: Validation Root (~3,557 LOC)

### Files
- `validation/*.py`

### Agent 29A: Code Reviewer - Validation Root

```python
Task(
    subagent_type="code-reviewer",
    description="Validation Root Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Validation Root

## Target: validation/*.py (~3,557 LOC)

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

### Agent 29B: Full Stack Developer - Validation Root

```python
Task(
    subagent_type="full-stack-developer",
    description="Validation Root Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Validation Root

## Target: validation/*.py (~3,557 LOC)

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

### Agent 29C: Architecture Reviewer - Validation Root

```python
Task(
    subagent_type="architecture-reviewer",
    description="Validation Root Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Validation Root

## Target: validation/*.py (~3,557 LOC)

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

## Deelgebied 30: Hybrid Context (~1,178 LOC)

### Files
- `hybrid_context/*.py`

### Agent 30A: Code Reviewer - Hybrid Context

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

### Agent 30B: Full Stack Developer - Hybrid Context

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

### Agent 30C: Architecture Reviewer - Hybrid Context

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

## Deelgebied 31: Miscellaneous Modules (~2,667 LOC)

### Files
- `security/*.py`
- `integration/*.py`
- `cli/*.py`
- `api/*.py`
- `tools/*.py`
- `document_processing/*.py`
- `export/*.py`

### Agent 31A: Code Reviewer - Miscellaneous Modules

```python
Task(
    subagent_type="code-reviewer",
    description="Miscellaneous Modules Code Reviewer Analysis",
    prompt="""
# CODE REVIEWER ANALYSIS: Miscellaneous Modules

## Target: security/*.py, integration/*.py, ... (~2,667 LOC)

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

### Agent 31B: Full Stack Developer - Miscellaneous Modules

```python
Task(
    subagent_type="full-stack-developer",
    description="Miscellaneous Modules Full Stack Developer Analysis",
    prompt="""
# FULL STACK DEVELOPER ANALYSIS: Miscellaneous Modules

## Target: security/*.py, integration/*.py, ... (~2,667 LOC)

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

### Agent 31C: Architecture Reviewer - Miscellaneous Modules

```python
Task(
    subagent_type="architecture-reviewer",
    description="Miscellaneous Modules Architecture Reviewer Analysis",
    prompt="""
# ARCHITECTURE REVIEWER ANALYSIS: Miscellaneous Modules

## Target: security/*.py, integration/*.py, ... (~2,667 LOC)

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