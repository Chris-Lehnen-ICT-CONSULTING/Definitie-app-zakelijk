# DEF-102: CONTEXT USAGE Contradiction - Complete Analysis

**Analysis Date:** 2025-11-10
**Analyst:** Debug Specialist (Claude Code)
**Issue:** "Must use context but cannot make it traceable"
**Status:** ANALYZED - Framework provided

---

## Executive Summary

**THE CONTRADICTION (from DEF-102):**
> "Must use context but cannot make it traceable - Unclear how to apply 'Strafrecht' without mentioning it"

**ROOT CAUSE:** This is NOT a logical contradiction - it's an **ambiguity in operational definition**. The requirement is clear (be context-specific without explicit mention), but the **implementation mechanism** is underspecified.

**RESOLUTION:** Define concrete criteria for "implicit context usage" with teachable examples for GPT-4.

---

## 1. The Problem Dissected

### 1.1 What the Rules Say

**CON-01 Requirement:**
```
"Formuleer de definitie zó dat deze past binnen de opgegeven context(en),
zonder deze expliciet te benoemen in de definitie zelf."
```

**Context Awareness Module (line 201):**
```
"⚠️ VERPLICHT: Gebruik onderstaande specifieke context om de definitie te formuleren
voor deze organisatorische, juridische en wettelijke setting. Maak de definitie
contextspecifiek zonder de context expliciet te benoemen."
```

### 1.2 The Confusion

**Question:** How do you "use" context if you can't mention it?

**The Gap:** No concrete guidance on **what actions** the LLM should take to "apply" context implicitly.

---

## 2. Understanding "Implicit vs Explicit"

### 2.1 Definitions

**EXPLICIT Context Usage** (FORBIDDEN by CON-01):
- **Direct labels:** "binnen het strafrecht", "in de context van DJI"
- **Meta-level:** "in juridische context", "volgens operationele definities"
- **Organization names:** "volgens DJI-richtlijnen", "door het OM"

**IMPLICIT Context Usage** (REQUIRED by CON-01):
- **Domain-specific terminology:** Words that naturally belong to the context
- **Scope narrowing:** Defining boundaries specific to the domain
- **Context-specific actors/processes:** Roles/procedures that signal the domain
- **Implicit relationships:** Connections to domain-specific entities

### 2.2 The Mechanism: Context Shapes Scope, Not Labels

**Key Insight:** Context doesn't ADD information to the definition - it NARROWS the scope.

```
Generic Definition (no context):
"Toezicht is het observeren van handelingen om naleving te beoordelen."
↓ TOO BROAD (applies to any supervision in any domain)

Context-Specific Definition (Strafrecht context):
"Toezicht is het systematisch volgen van handelingen om te beoordelen
of ze voldoen aan vastgestelde normen."
↓ NARROWED SCOPE (implicitly criminal law: "vastgestelde normen" = laws)
```

**The narrowing is implicit:**
- "vastgestelde normen" = implies legal/regulatory context (not just any norms)
- "systematisch volgen" = implies formal oversight (not casual observation)
- "om te beoordelen" = implies judgment authority (not just monitoring)

---

## 3. TEST CASES: Explicit vs Implicit

### Test Case 1: "sanctie" (Term: sanction)

**Context Provided:** organisatorische_context = ["OM"], juridische_context = ["Strafrecht"]

#### ❌ TOO EXPLICIT (violates CON-01)

```
"Sanctie binnen het strafrecht is een opgelegde bestraffende maatregel
na veroordeling voor een strafbaar feit."
         ^^^^^^^^^^^^^^^^^^^
         LITERAL CONTEXT MENTION
```

**Why FORBIDDEN:**
- "binnen het strafrecht" = direct context label
- Makes definition context-DEPENDENT (only valid with qualifier)
- Reader can TRACE context from the text

**CON-01 Pattern Match:** `\bbinnen de context\b`, `\bstrafrecht\b`

---

#### ⚠️ BORDERLINE (unclear - may violate CON-01)

```
"Sanctie is een strafrechtelijke maatregel opgelegd door de strafrechter
na veroordeling voor een overtreding."
              ^^^^^^^^^^^^^^^^^
              DOMAIN LABEL AS ADJECTIVE
```

**Why UNCLEAR:**
- "strafrechtelijke" = derived from "strafrecht" (domain label as adjective)
- Technically CON-01 forbids `\bstrafrecht\b` pattern (regex match)
- BUT: Is this "explicit mention" or just domain-specific terminology?

**Debate:**
- **Strict interpretation:** FORBIDDEN (contains "strafrecht" substring)
- **Pragmatic interpretation:** ALLOWED (using domain terminology ≠ naming context)

**Current regex:** `\bstrafrecht\b` would catch this (word boundary match)

---

#### ✅ IMPLICIT (good - passes CON-01)

```
"Sanctie is een opgelegde correctie of beperking bij vastgestelde overtredingen,
gericht op herstel en het voorkomen van herhaling."
```

**Why ACCEPTABLE:**
- "vastgestelde overtredingen" = implies legal violations (domain-specific scope)
- "opgelegde" = implies authority to impose (criminal justice context)
- "herstel en voorkomen van herhaling" = recidivism prevention (criminal law goal)
- NO literal mention of "strafrecht", "strafrechtelijk", or "OM"

**How context is implicit:**
- "overtredingen" (not "violations" in general) → legal domain
- "herstel" → restorative justice concept (criminal law)
- "voorkomen van herhaling" → recidivism (criminal justice terminology)

**A domain expert (legal professional) would identify:** "This is criminal law territory" WITHOUT seeing the word "strafrecht".

---

### Test Case 2: "toezicht" (Term: supervision)

**Context:** organisatorische_context = ["DJI"], juridische_context = ["Strafrecht"]

#### ❌ TOO EXPLICIT

```
"Toezicht is controle uitgevoerd door DJI in juridische context,
op basis van het Wetboek van Strafvordering."
                        ^^^        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                     ORG NAME    LITERAL LEGAL CODE MENTION
```

**CON-01 violations:**
- "DJI" → organizational context named
- "in juridische context" → meta-level context label
- "Wetboek van Strafvordering" → specific legal code (traceable)

**From CON-01 bad examples (line 38):** Exact match!

---

#### ✅ IMPLICIT

```
"Toezicht is het systematisch volgen van handelingen om te beoordelen
of ze voldoen aan vastgestelde normen."
```

**How context shapes this:**
- **Generic "supervision"** could be: parent watching child, teacher monitoring class
- **DJI/Strafrecht "toezicht"** narrowed to: formal monitoring of compliance with norms
- "vastgestelde normen" = established rules (implies regulatory/legal framework)
- "systematisch volgen" = structured oversight (not casual observation)

**From CON-01 good examples (line 33):** Exact match!

---

### Test Case 3: "registratie" (Term: registration)

**Context:** organisatorische_context = ["Politie"], juridische_context = ["Strafrecht"]

#### ❌ TOO EXPLICIT

```
"Registratie: het vastleggen van persoonsgegevens binnen de organisatie DJI,
in strafrechtelijke context."
                                        ^^^                    ^^^^^^^^^^^^^^^^^^^^^
                                     ORG NAME              CONTEXT LABEL
```

**CON-01 violations:**
- "binnen de organisatie DJI" → organizational context named
- "in strafrechtelijke context" → meta-level context label

**From CON-01 bad examples (line 39):** Exact match!

---

#### ✅ IMPLICIT

```
"Registratie is het formeel vastleggen van gegevens in een geautoriseerd systeem."
```

**How context shapes this:**
- **Generic "registration":** any data recording (attendance, membership, etc.)
- **Politie/Strafrecht "registratie":** narrowed to formal, authorized systems
- "formeel vastleggen" = official recording (implies legal/regulatory framework)
- "geautoriseerd systeem" = authorized system (implies authority and compliance)

**Context signals:**
- "formeel" → legal formality
- "geautoriseerd" → authorization framework (criminal justice system)
- Combined: implies secure, compliant, legally valid data storage

**From CON-01 good examples (line 34):** Exact match!

---

## 4. The Implicit Context Framework

### 4.1 Three Mechanisms for Implicit Context

#### Mechanism 1: Domain-Specific Terminology

**What:** Use words that naturally belong to the context domain.

**Examples:**

| Context | Generic Term | Domain-Specific Term | Why Implicit? |
|---------|-------------|---------------------|---------------|
| Strafrecht | "punishment" | "sanctie" | Legal terminology |
| Strafrecht | "repeat" | "recidive" | Criminal justice term |
| Strafrecht | "decision" | "veroordeling" | Legal judgment term |
| DJI | "building" | "inrichting" | Prison facility term |
| OM | "suspect" | "verdachte" | Legal procedure term |

**Rule:** Choose the term that a domain expert would use, not the everyday synonym.

---

#### Mechanism 2: Scope Narrowing

**What:** Define boundaries that are specific to the context domain.

**Examples:**

| Generic Scope | Context | Narrowed Scope | How Narrowed? |
|--------------|---------|----------------|---------------|
| "regels" (any rules) | Strafrecht | "vastgestelde normen" (established norms) | Implies legal framework |
| "procedure" (any process) | OM | "formele procedure" (formal procedure) | Adds legal formality |
| "persoon" (any person) | Strafrecht | "verdachte" (suspect) | Legal status |
| "gebouw" (any building) | DJI | "geautoriseerde inrichting" (authorized facility) | Legal authorization |

**Rule:** Replace broad terms with narrower, domain-specific equivalents.

---

#### Mechanism 3: Context-Specific Relationships

**What:** Reference actors, processes, or goals specific to the context.

**Examples:**

| Context | Generic | Context-Specific | Why Signals Context? |
|---------|---------|------------------|---------------------|
| Strafrecht | "stop it happening again" | "voorkomen van recidive" | Criminal justice goal |
| DJI | "person in charge" | "directeur van de inrichting" | Prison facility role |
| OM | "decision maker" | "officier van justitie" | Prosecutor role |
| Strafrecht | "process to decide guilt" | "strafproces" | Criminal procedure |

**Rule:** Reference domain-specific actors and goals without naming the organization/law.

---

### 4.2 The Validation Test

**Question:** "Can a domain expert identify which context this definition belongs to, WITHOUT seeing the context label?"

**Test:**
1. Remove all context metadata (organisatorische_context, juridische_context)
2. Show definition to 5 legal domain experts
3. Ask: "Which legal domain does this belong to?" (Strafrecht, Bestuursrecht, Civiel recht, etc.)

**Success Criteria:**
- ≥4/5 experts correctly identify context → ✅ IMPLICIT (context successfully encoded)
- 2-3/5 experts correct → ⚠️ WEAK (context signals too subtle)
- ≤1/5 experts correct → ❌ TOO GENERIC (context not applied)

**Example:**

```
Definition: "Sanctie is een opgelegde correctie bij vastgestelde overtredingen,
gericht op herstel en voorkomen van recidive."

Expert 1: Strafrecht ✅
Expert 2: Strafrecht ✅
Expert 3: Bestuursrecht ❌ (could be administrative sanctions)
Expert 4: Strafrecht ✅
Expert 5: Strafrecht ✅

Result: 4/5 = ✅ IMPLICIT (strong context signal)
```

---

## 5. Database Evidence: Real-World Examples

### 5.1 Good Implicit Context (from database)

**Example 1: "grondslag"**
```
Context: organisatorische_context = ["Strafrechtketen"], juridische_context = ["Strafrecht"]

Definition: "Verdenking of veroordeling die de strafrechtketen het recht geeft
identiteitsgegevens in de strafrechtketen te verwerken"
```

**Analysis:**
- ❌ **VIOLATION!** Contains "strafrechtketen" (2x) - literal organizational context
- **CON-01 Pattern Match:** `\bstrafrecht\b` (substring match)
- **Should be:** "Verdenking of veroordeling die het recht geeft identiteitsgegevens te verwerken"

**Root Cause:** GPT-4 included organizational context name (strafrechtketen) in definition.

---

**Example 2: "identiteitsbehandeling"**
```
Context: organisatorische_context = ["Strafrechtketen"], juridische_context = ["Strafrecht"]

Definition: "Het geheel van activiteiten en voorzieningen in de strafrechtketen
om de juiste en rechtmatige verwerking van identiteitsgegevens van verdachten
en veroordeelden te borgen."
```

**Analysis:**
- ❌ **VIOLATION!** Contains "in de strafrechtketen" - literal organizational context
- ✅ **IMPLICIT signals:** "verdachten en veroordeelden" (criminal justice actors)
- **Should be:** Remove "in de strafrechtketen", keep "verdachten en veroordeelden"

---

**Example 3: "toets"** (from first database result)
```
Context: organisatorische_context = ["OM"], juridische_context = []

Definition: "Type beoordeling met een vastgestelde methodiek waarbij een deskundige
of geautoriseerde functionaris een objectieve vaststelling doet van de aanwezigheid,
geldigheid of juistheid van een feit, gegeven of situatie op basis van vooraf
bepaalde criteria."
```

**Analysis:**
- ✅ **NO VIOLATION** - No mention of "OM" or context labels
- ✅ **IMPLICIT signals:**
  - "geautoriseerde functionaris" → formal authority (legal context)
  - "objectieve vaststelling" → legal determination
  - "feit, gegeven of situatie" → legal evidence terminology
  - "vooraf bepaalde criteria" → procedural standards (legal framework)

**Verdict:** ✅ EXCELLENT EXAMPLE - Context implicit through terminology and scope.

---

### 5.2 Observations from Database

**Statistics (from 10 samples):**
- **CON-01 violations:** 3/10 (30%) - contain organizational context names
- **Good implicit usage:** 7/10 (70%) - use domain terminology effectively

**Common violations:**
- "strafrechtketen" in definition (2x)
- "DJI" in definition (mentioned in CON-01 forbidden patterns)

**Success pattern:**
- Use of domain-specific roles ("verdachte", "veroordeelde", "officier")
- Use of domain-specific processes ("veroordeling", "verdenking", "recidive")
- NO literal organization/context names

---

## 6. Framework for GPT-4: Teachable Criteria

### 6.1 The Three Rules

**RULE 1: Domain Vocabulary Selection**
```
FOR EACH WORD in definition:
  IF generic synonym exists (e.g., "person" vs "verdachte"):
    → Choose the domain-specific term
  IF domain-neutral term possible (e.g., "rule" vs "norm"):
    → Choose the legally precise term ("vastgestelde norm")
```

**RULE 2: Scope Narrowing via Qualifiers**
```
FOR EACH NOUN in definition:
  IF too broad for context (e.g., "procedure"):
    → Add domain-specific qualifier ("formele procedure", "gerechtelijke procedure")
  IF actor/role mentioned:
    → Use domain-specific role ("verdachte" not "persoon")
```

**RULE 3: Context Signal via Relationships**
```
IF definition describes a process:
  → Reference domain-specific goal (e.g., "voorkomen van recidive")
IF definition describes an entity:
  → Reference domain-specific framework (e.g., "geautoriseerd door bevoegde instantie")
```

---

### 6.2 The Checklist for GPT-4

**Before generating definition, check:**

- [ ] **Terminology:** Are all nouns/verbs domain-specific, not generic?
  - ❌ "controle" → ✅ "toezicht"
  - ❌ "persoon" → ✅ "verdachte"

- [ ] **Scope:** Are all broad terms narrowed to domain scope?
  - ❌ "regels" → ✅ "vastgestelde normen"
  - ❌ "systeem" → ✅ "geautoriseerd systeem"

- [ ] **Actors:** Are roles domain-specific, not generic?
  - ❌ "functionaris" → ✅ "officier van justitie"
  - ❌ "beslisser" → ✅ "rechter"

- [ ] **Goals:** Are purposes domain-specific?
  - ❌ "voorkomen van herhaling" → ✅ "voorkomen van recidive"
  - ❌ "herstel van schade" → ✅ "herstel van benadeelde partij"

- [ ] **NO explicit labels:**
  - ❌ "binnen het strafrecht"
  - ❌ "in de context van DJI"
  - ❌ "volgens het Wetboek van Strafvordering"

---

### 6.3 Decision Tree for Context Application

```
START: Generate definition for term X with context [Org Y, Legal Z]

↓
STEP 1: Identify generic definition (no context)
  Example: "Sanctie is een opgelegde correctie"

↓
STEP 2: For each word, ask: "Is this domain-specific enough?"
  - "sanctie" → YES (legal term)
  - "opgelegde" → YES (implies authority)
  - "correctie" → NO (too generic - could be any correction)

↓
STEP 3: Replace generic words with domain-specific equivalents
  - "correctie" → "beperking of bestraffende maatregel" (legal scope)

↓
STEP 4: Add context-specific scope narrowing
  - Add: "bij vastgestelde overtredingen" (legal violations, not just any violations)
  - Add: "gericht op herstel en voorkomen van recidive" (criminal justice goal)

↓
STEP 5: Validate - Does definition pass CON-01?
  - Check regex patterns (no literal context mentions)
  - Check domain expert test (≥4/5 identify context correctly)

↓
END: Context-specific definition without explicit mention
  "Sanctie is een opgelegde beperking of bestraffende maatregel bij
   vastgestelde overtredingen, gericht op herstel en voorkomen van recidive."
```

---

## 7. Updated CON-01 Operational Definition

### 7.1 Current Rule (Ambiguous)

```json
"uitleg": "Formuleer de definitie zó dat deze past binnen de opgegeven context(en),
zonder deze expliciet te benoemen in de definitie zelf."
```

**Problem:** "past binnen" is vague - HOW to make it fit?

---

### 7.2 Proposed Enhanced Rule

```json
"uitleg": "Formuleer de definitie zó dat deze past binnen de opgegeven context(en),
zonder deze expliciet te benoemen in de definitie zelf.",

"toelichting_enhanced": "Een definitie is contextspecifiek wanneer:
1. TERMINOLOGIE: Gebruik van domein-specifieke termen in plaats van generieke synoniemen
2. SCOPE: Expliciete vernauwing tot het toepassingsgebied van de context
3. RELATIES: Verwijzingen naar context-specifieke actoren, processen of doelen

Deze context mag niet letterlijk worden herhaald (bijv. 'binnen het strafrecht',
'door het OM', 'volgens het Wetboek van Strafvordering'). De context moet
**impliciet doorklinken** door:
- Gebruik van juridische termen die tot het domein behoren (bijv. 'verdachte', 'recidive')
- Vernauwing van scope (bijv. 'vastgestelde normen' i.p.v. 'regels')
- Verwijzing naar domein-specifieke rollen/processen (bijv. 'veroordeling', 'strafproces')

VALIDATIE: Een definitie is contextspecifiek als een domeinexpert (zonder context metadata
te zien) kan bepalen in welke context deze geldt.",

"foute_voorbeelden_uitgebreid": [
  "Toezicht is controle uitgevoerd door DJI in juridische context [❌ org name + context label]",
  "Sanctie binnen het strafrecht is een maatregel [❌ literal context mention]",
  "Registratie volgens het Wetboek van Strafvordering [❌ specific legal code named]",
  "Maatregel zoals toegepast binnen de strafrechtketen [❌ organizational context named]"
],

"goede_voorbeelden_uitgebreid": [
  "Toezicht is het systematisch volgen van handelingen om te beoordelen of ze voldoen
   aan vastgestelde normen. [✅ 'vastgestelde normen' signals legal context implicitly]",

  "Sanctie is een opgelegde beperking of bestraffende maatregel bij vastgestelde
   overtredingen, gericht op herstel en voorkomen van recidive.
   [✅ 'recidive' = criminal justice term, no explicit 'strafrecht' mention]",

  "Registratie is het formeel vastleggen van gegevens in een geautoriseerd systeem.
   [✅ 'formeel', 'geautoriseerd' signal legal framework without naming it]"
]
```

---

## 8. Implementation in Context Awareness Module

### 8.1 Current Prompt (Line 201)

```python
"⚠️ VERPLICHT: Gebruik onderstaande specifieke context om de definitie te formuleren
voor deze organisatorische, juridische en wettelijke setting. Maak de definitie
contextspecifiek zonder de context expliciet te benoemen."
```

**Problem:** No guidance on HOW to do this.

---

### 8.2 Enhanced Prompt (Proposed)

```python
"⚠️ VERPLICHT: Gebruik onderstaande specifieke context om de definitie te formuleren:

HOE context toepassen (DRIE MECHANISMEN):
1. TERMINOLOGIE: Gebruik domein-specifieke termen (bijv. 'verdachte' i.p.v. 'persoon')
2. SCOPE: Vernauw begrippen tot context (bijv. 'vastgestelde normen' i.p.v. 'regels')
3. RELATIES: Verwijs naar context-specifieke actoren/doelen (bijv. 'voorkomen van recidive')

❌ VERBODEN (CON-01):
- Context labels: 'binnen het strafrecht', 'in de context van'
- Organisatienamen: 'DJI', 'OM', 'strafrechtketen' (in definition text)
- Wettelijke codes: 'Wetboek van Strafvordering', 'volgens de wet'

✅ TOEGESTAAN:
- Domein termen: 'verdachte', 'recidive', 'sanctie'
- Vernauwde scope: 'vastgestelde normen', 'geautoriseerd systeem'
- Context-specifieke rollen: 'officier van justitie', 'rechter'

TOETS: Kan een expert zonder context metadata zien in welke context deze definitie hoort?
"
```

---

## 9. Success Metrics

### 9.1 CON-01 Compliance Rate

**Before enhancement:**
- Database shows: 30% CON-01 violations (3/10 samples contain org names)

**After enhancement:**
- Target: <5% CON-01 violations
- Measure: Automated regex check on new definitions

---

### 9.2 Context Signal Strength

**Test:** Domain expert identification rate

**Method:**
1. Generate 20 definitions with context
2. Remove context metadata
3. Ask 5 legal experts: "Which domain?" (Strafrecht, Bestuursrecht, etc.)
4. Calculate agreement rate

**Target:**
- ≥80% of definitions: ≥4/5 experts agree (strong signal)
- ≤10% of definitions: ≤2/5 experts agree (weak signal)

---

### 9.3 Terminology Precision

**Measure:** % of definitions using domain-specific terms vs generic terms

**Examples:**
- "verdachte" vs "persoon" → domain-specific ✅
- "vastgestelde normen" vs "regels" → domain-specific ✅
- "recidive" vs "herhaling" → domain-specific ✅

**Target:** ≥70% of nouns/verbs in definitions are domain-specific (not generic)

---

## 10. Comparison: This vs Other DEF-102 Contradictions

### 10.1 Contradiction Type

| Contradiction | Type | Severity | Resolvable? |
|--------------|------|----------|------------|
| **#1: "is" usage deadlock** | LOGICAL PARADOX | CRITICAL | YES - Exception clause |
| **#2: Container terms** | LOGICAL PARADOX | HIGH | YES - Exception clause |
| **#5: Context usage** | **AMBIGUITY** | **MEDIUM** | **YES - Enhanced guidance** |

**Key Difference:**
- Contradictions #1-#4: **Logical impossibilities** (mutually exclusive rules)
- Contradiction #5: **Operational ambiguity** (unclear implementation)

---

### 10.2 Resolution Strategy

| Contradiction | Fix Type | Effort |
|--------------|----------|--------|
| **#1-#4** | Add exception clauses (5 lines × 3 modules) | 3 hours |
| **#5** | Enhance guidance + examples (update CON-01, context_awareness_module) | 2 hours |

**Total effort:** 5 hours for all DEF-102 contradictions

---

## 11. Recommendation

### 11.1 Update CON-01.json

**File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/CON-01.json`

**Changes:**
1. Add `toelichting_enhanced` field with three mechanisms
2. Expand `goede_voorbeelden` with WHY explanations (✅ annotations)
3. Expand `foute_voorbeelden` with WHY explanations (❌ annotations)

**Effort:** 1 hour (add ~100 lines JSON)

---

### 11.2 Update context_awareness_module.py

**File:** `/Users/chrislehnen/Projecten/Definitie-app/src/services/prompts/modules/context_awareness_module.py`

**Changes:**
1. Line 201: Replace with enhanced prompt (3 mechanisms + examples)
2. Add inline examples for each mechanism

**Effort:** 30 minutes (replace 1 line with 20 lines)

---

### 11.3 Add Integration Test

**File:** `tests/integration/test_context_usage.py` (NEW)

**Test cases:**
```python
def test_con01_no_explicit_context_labels():
    """Verify generated definitions don't contain forbidden context labels."""
    # Test CON-01 regex patterns

def test_con01_domain_expert_identification():
    """Verify domain experts can identify context from definition."""
    # 5 expert simulation test

def test_con01_terminology_precision():
    """Verify definitions use domain-specific terms, not generic."""
    # Check term selection
```

**Effort:** 1 hour (3 test cases)

---

## 12. Conclusion

### 12.1 The Answer to "How to Apply Context"

**THE MECHANISM:**

Context **narrows the scope** of the definition through:
1. **Vocabulary selection** - domain-specific terms vs generic terms
2. **Scope qualifiers** - narrowing broad concepts to domain boundaries
3. **Implicit relationships** - referencing domain-specific actors/goals

**WITHOUT:**
- Context labels ("binnen het strafrecht")
- Organization names ("DJI", "OM")
- Legal code mentions ("Wetboek van Strafvordering")

---

### 12.2 Why This Isn't a Contradiction

**It's NOT impossible:** Many database definitions successfully do this (70% pass CON-01)

**It's just underspecified:** GPT-4 needs concrete guidance on:
- WHAT to do (three mechanisms)
- HOW to do it (decision tree)
- WHEN successful (domain expert test)

---

### 12.3 Resolution Path

**Phase 1: Documentation (1.5 hours)**
- [ ] Update CON-01.json with enhanced guidance
- [ ] Update context_awareness_module.py with three mechanisms

**Phase 2: Validation (1 hour)**
- [ ] Add integration tests for CON-01 compliance
- [ ] Run tests on 20 generated definitions

**Phase 3: Measurement (ongoing)**
- [ ] Track CON-01 violation rate (target: <5%)
- [ ] Track domain expert identification rate (target: >80%)

---

**END OF CONTEXT USAGE ANALYSIS**

**Status:** Ready to implement enhanced CON-01 guidance alongside DEF-102 exception clauses.
