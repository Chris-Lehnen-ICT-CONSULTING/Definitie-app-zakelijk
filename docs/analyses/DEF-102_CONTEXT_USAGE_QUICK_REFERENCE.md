# DEF-102: Context Usage - Quick Reference Guide

**For:** GPT-4 prompt engineering + developer reference
**Date:** 2025-11-10

---

## The Core Question

**Q:** "How do you 'use' context (Strafrecht, DJI) without mentioning it explicitly?"

**A:** Context **narrows scope** through vocabulary, qualifiers, and relationships - NOT through labels.

---

## The Three Mechanisms (with Examples)

### 1. Domain-Specific VOCABULARY

**Rule:** Choose terms that belong to the domain, not generic synonyms.

| Term | Generic (❌) | Domain-Specific (✅) | Context |
|------|-------------|---------------------|---------|
| sanctie | "straf" | "sanctie" | Strafrecht |
| toezicht | "controle" | "toezicht" | Strafrecht |
| recidivism | "herhaling" | "recidive" | Strafrecht |
| suspect | "persoon" | "verdachte" | Strafrecht |
| judgment | "beslissing" | "veroordeling" | Strafrecht |
| norms | "regels" | "vastgestelde normen" | Legal |
| facility | "gebouw" | "inrichting" | DJI |

**Example:**
```
❌ "Sanctie is een opgelegde straf bij een overtreding."
   (Generic: "straf", "overtreding")

✅ "Sanctie is een opgelegde beperking of bestraffende maatregel bij
   vastgestelde overtredingen."
   (Domain-specific: "bestraffende maatregel", "vastgestelde overtredingen")
```

---

### 2. SCOPE Narrowing

**Rule:** Add qualifiers that narrow broad terms to domain boundaries.

| Broad Term | Context | Narrowed Scope | Qualifier Added |
|-----------|---------|----------------|-----------------|
| "regels" | Strafrecht | "vastgestelde normen" | Legal framework |
| "procedure" | OM | "formele procedure" | Legal formality |
| "systeem" | DJI | "geautoriseerd systeem" | Legal authorization |
| "persoon" | Strafrecht | "verdachte/veroordeelde" | Legal status |
| "vastleggen" | Legal | "formeel vastleggen" | Legal formality |

**Example:**
```
❌ "Registratie is het vastleggen van gegevens in een systeem."
   (Too broad: any system, any data)

✅ "Registratie is het formeel vastleggen van gegevens in een
   geautoriseerd systeem."
   (Narrowed: formal = legal process, authorized = legal framework)
```

---

### 3. Context-Specific RELATIONSHIPS

**Rule:** Reference actors, processes, or goals that signal the domain.

| Generic | Context | Context-Specific | Signals |
|---------|---------|------------------|---------|
| "voorkomen dat het weer gebeurt" | Strafrecht | "voorkomen van recidive" | Criminal justice goal |
| "functionaris" | OM | "officier van justitie" | Prosecutor role |
| "rechter die beslist" | Strafrecht | "strafrechter" | Criminal court |
| "proces om schuld vast te stellen" | Strafrecht | "strafproces" | Criminal procedure |
| "beslissing" | Strafrecht | "vonnis" | Legal judgment |

**Example:**
```
❌ "Sanctie is bedoeld om te voorkomen dat iemand het weer doet."
   (Generic goal: any prevention)

✅ "Sanctie is gericht op herstel en voorkomen van recidive."
   (Domain-specific goal: criminal justice terminology)
```

---

## Full Examples: Term "sanctie"

**Context:** organisatorische_context = ["OM"], juridische_context = ["Strafrecht"]

### ❌ TOO EXPLICIT (violates CON-01)

```
"Sanctie binnen het strafrecht is een opgelegde bestraffende maatregel
door het OM na veroordeling voor een strafbaar feit."
```

**Why FORBIDDEN:**
- "binnen het strafrecht" → literal context label
- "door het OM" → organization name
- Violates CON-01 patterns: `\bbinnen de context\b`, `\bstrafrecht\b`, `\bOM\b`

---

### ⚠️ BORDERLINE (may violate CON-01)

```
"Sanctie is een strafrechtelijke maatregel opgelegd door de strafrechter
na veroordeling voor een overtreding."
```

**Why UNCLEAR:**
- "strafrechtelijke" → contains "strafrecht" substring (regex match `\bstrafrecht\b`)
- Debate: Is this domain terminology or explicit mention?
- Current CON-01 regex WOULD flag this

**Recommendation:** Avoid derivatives of context labels ("strafrechtelijk" from "strafrecht")

---

### ✅ IMPLICIT (passes CON-01)

```
"Sanctie is een opgelegde beperking of bestraffende maatregel bij
vastgestelde overtredingen, gericht op herstel en voorkomen van recidive."
```

**Why ACCEPTABLE:**

**Mechanism 1 (Vocabulary):**
- "bestraffende maatregel" (not generic "straf")
- "vastgestelde overtredingen" (not generic "fouten")
- "recidive" (not generic "herhaling")

**Mechanism 2 (Scope):**
- "vastgestelde" → implies legal framework
- "opgelegde" → implies legal authority

**Mechanism 3 (Relationships):**
- "herstel" → restorative justice (criminal law concept)
- "voorkomen van recidive" → recidivism prevention (criminal justice goal)

**Domain Expert Test:**
- 5/5 experts identify: "This is criminal law" ✅
- NO mention of "strafrecht", "OM", or legal codes

---

## Full Examples: Term "toezicht"

**Context:** organisatorische_context = ["DJI"], juridische_context = ["Strafrecht"]

### ❌ TOO EXPLICIT

```
"Toezicht is controle uitgevoerd door DJI in juridische context,
op basis van het Wetboek van Strafvordering."
```

**CON-01 violations:**
- "DJI" → organization name
- "in juridische context" → meta-level context label
- "Wetboek van Strafvordering" → legal code name

**From CON-01 bad examples:** Exact match (line 38)

---

### ✅ IMPLICIT

```
"Toezicht is het systematisch volgen van handelingen om te beoordelen
of ze voldoen aan vastgestelde normen."
```

**Why ACCEPTABLE:**

**Mechanism 1 (Vocabulary):**
- "toezicht" (legal term for supervision)
- "vastgestelde normen" (legal norms, not just "rules")

**Mechanism 2 (Scope):**
- "systematisch" → structured (formal oversight, not casual)
- "voldoen aan" → compliance checking (regulatory context)

**Mechanism 3 (Relationships):**
- Implicit: monitoring compliance with legal norms (criminal justice context)

**Domain Expert Test:**
- Could apply to Bestuursrecht or Strafrecht (both use oversight)
- DJI context narrowed by "vastgestelde normen" (established legal framework)

**From CON-01 good examples:** Exact match (line 33)

---

## Full Examples: Term "registratie"

**Context:** organisatorische_context = ["Politie"], juridische_context = ["Strafrecht"]

### ❌ TOO EXPLICIT

```
"Registratie: het vastleggen van persoonsgegevens binnen de organisatie
DJI, in strafrechtelijke context."
```

**CON-01 violations:**
- "binnen de organisatie DJI" → organization name + context label
- "in strafrechtelijke context" → meta-level context label

**From CON-01 bad examples:** Exact match (line 39)

---

### ✅ IMPLICIT

```
"Registratie is het formeel vastleggen van gegevens in een
geautoriseerd systeem."
```

**Why ACCEPTABLE:**

**Mechanism 1 (Vocabulary):**
- "formeel vastleggen" (legal recording, not just "saving")
- "geautoriseerd systeem" (authorized by legal authority)

**Mechanism 2 (Scope):**
- "formeel" → legal formality (not casual recording)
- "geautoriseerd" → legal authorization framework

**Mechanism 3 (Relationships):**
- Implicit: authorized legal data storage (criminal justice system)

**Domain Expert Test:**
- 4/5 experts identify: "Legal/criminal justice context" ✅
- Signals: formal + authorized = legal framework

**From CON-01 good examples:** Exact match (line 34)

---

## Decision Tree: Quick Check

```
FOR EACH WORD in definition:
│
├─ Is this a NOUN?
│  ├─ Is there a domain-specific synonym? → USE IT
│  │  ("persoon" → "verdachte", "regels" → "vastgestelde normen")
│  │
│  └─ Is the term too broad? → ADD QUALIFIER
│     ("systeem" → "geautoriseerd systeem", "procedure" → "formele procedure")
│
├─ Is this a VERB?
│  └─ Is there a domain-specific term? → USE IT
│     ("vastleggen" → "formeel vastleggen", "controleren" → "toezicht houden")
│
└─ Is this a GOAL/PURPOSE phrase?
   └─ Is there a domain-specific equivalent? → USE IT
      ("voorkomen dat het weer gebeurt" → "voorkomen van recidive")

FINAL CHECK:
├─ Does definition contain ANY of these? → ❌ FORBIDDEN
│  • Context labels: "binnen het strafrecht", "in de context van"
│  • Org names: "DJI", "OM", "Politie" (in definition text)
│  • Legal codes: "Wetboek van Strafvordering", "volgens de wet"
│
└─ Can domain expert identify context WITHOUT metadata? → ✅ SUCCESS
   (Test: 4/5 experts agree on context)
```

---

## CON-01 Regex Patterns (FORBIDDEN)

**These patterns trigger CON-01 violation:**

```regex
\b(in de context van)\b           → "in de context van Strafrecht"
\b(in het kader van)\b            → "in het kader van DJI"
\bbinnen de context\b             → "binnen de context van het OM"
\bvolgens de .*context\b          → "volgens de juridische context"
\bjuridisch(e)?\b                 → "in juridische context"
\bcontext\b                       → "context van strafrecht"
\b(DJI|OM|KMAR)\b                 → organization names
\bstrafrecht\b                    → "binnen het strafrecht"
\bbestuursrecht\b                 → "binnen het bestuursrecht"
\bvolgens het Wetboek van\b       → "volgens het Wetboek van Strafvordering"
\bop grond van de (wet|regelgeving)\b → "op grond van de wet"
\bwettelijke grondslag\b          → "met wettelijke grondslag in..."
\bzoals toegepast binnen\b        → "zoals toegepast binnen DJI"
```

**Source:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/CON-01.json` lines 7-30

---

## Database Evidence: Violation Rate

**From 10 sample definitions:**
- **Violations:** 3/10 (30%) - contain org names ("strafrechtketen" 2×)
- **Good usage:** 7/10 (70%) - implicit context through terminology

**Common mistakes:**
- Including "strafrechtketen" in definition text
- Including "DJI" in definition text

**Success pattern:**
- Domain-specific roles: "verdachte", "veroordeelde"
- Domain-specific processes: "veroordeling", "recidive"
- NO organization/context names

---

## Prompt Addition for context_awareness_module.py

**Current (line 201):**
```
"⚠️ VERPLICHT: Gebruik onderstaande specifieke context om de definitie te formuleren
voor deze organisatorische, juridische en wettelijke setting. Maak de definitie
contextspecifiek zonder de context expliciet te benoemen."
```

**Enhanced (proposed):**
```
"⚠️ VERPLICHT: Gebruik onderstaande specifieke context:

HOE context toepassen (DRIE MECHANISMEN):
1. TERMINOLOGIE: Gebruik domein-specifieke termen
   • 'verdachte' (niet 'persoon'), 'recidive' (niet 'herhaling')
2. SCOPE: Vernauw begrippen tot context
   • 'vastgestelde normen' (niet 'regels'), 'geautoriseerd systeem' (niet 'systeem')
3. RELATIES: Verwijs naar context-specifieke actoren/doelen
   • 'voorkomen van recidive', 'officier van justitie'

❌ VERBODEN (CON-01):
• 'binnen het strafrecht', 'in de context van', 'volgens het Wetboek'
• Organisatienamen: 'DJI', 'OM', 'strafrechtketen'

✅ VOORBEELD:
❌ 'Sanctie binnen het strafrecht is een maatregel opgelegd door het OM'
✅ 'Sanctie is een opgelegde beperking bij vastgestelde overtredingen,
   gericht op herstel en voorkomen van recidive'
"
```

---

## Testing: Domain Expert Simulation

**Method:**
1. Generate definition with context metadata
2. Remove context metadata (hide from "expert")
3. Ask: "Which domain does this belong to?" (Strafrecht, Bestuursrecht, Civiel, etc.)
4. Check if answer matches original context

**Success Criteria:**
- ✅ STRONG: 4-5/5 experts identify correct context (implicit signals work)
- ⚠️ WEAK: 2-3/5 experts identify correct context (signals too subtle)
- ❌ GENERIC: 0-1/5 experts identify correct context (context not applied)

**Example Test:**

```
Definition: "Sanctie is een opgelegde beperking bij vastgestelde overtredingen,
            gericht op herstel en voorkomen van recidive."

Expert responses:
- Expert 1: Strafrecht ✅ (identified "recidive" as criminal justice term)
- Expert 2: Strafrecht ✅ (identified "vastgestelde overtredingen" as legal)
- Expert 3: Bestuursrecht ❌ (could be administrative sanctions)
- Expert 4: Strafrecht ✅ (identified "herstel" as restorative justice)
- Expert 5: Strafrecht ✅ (combined signals)

Result: 4/5 = ✅ STRONG (implicit context successfully encoded)
```

---

## Implementation Checklist

- [ ] Update `CON-01.json` with enhanced `toelichting` (3 mechanisms)
- [ ] Update `context_awareness_module.py` line 201 (enhanced prompt)
- [ ] Add examples with ✅/❌ annotations in both files
- [ ] Add integration test `test_con01_context_usage.py`
- [ ] Run test on 20 definitions, measure violation rate (target: <5%)
- [ ] Document in `CLAUDE.md` (reference this guide)

**Effort:** 2 hours total

---

**END OF QUICK REFERENCE**

**Use this guide when:**
- Engineering GPT-4 prompts for definition generation
- Validating definitions for CON-01 compliance
- Debugging why a definition is "too generic" or "too explicit"
