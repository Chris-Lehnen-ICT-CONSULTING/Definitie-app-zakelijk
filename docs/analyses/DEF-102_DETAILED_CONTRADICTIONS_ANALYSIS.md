# DEF-102: Detailed Contradictions Analysis - Prompt Module File Locations

**Analysis Date:** 2025-11-07
**Purpose:** Identify exact line numbers and contradictions in prompt module files
**Status:** COMPREHENSIVE - Ready for implementation

---

## SUMMARY OF 5 BLOCKING CONTRADICTIONS

| # | Contradiction | Files Involved | Severity | Lines |
|---|---|---|---|---|
| **1** | "is" start conflict | semantic_categorisation_module.py, structure_rules_module.py, error_prevention_module.py | 🔴 CRITICAL | Multiple |
| **2** | Container terms conflict | arai_rules_module.py, semantic_categorisation_module.py, error_prevention_module.py | 🔴 HIGH | Multiple |
| **3** | Relative clauses paradox | grammar_module.py, semantic_categorisation_module.py, error_prevention_module.py | 🟡 MEDIUM | Multiple |
| **4** | Article "een" conflict | semantic_categorisation_module.py, error_prevention_module.py | 🔴 CRITICAL | Multiple |
| **5** | Context integration ambiguity | context_awareness_module.py, con_rules_module.py | 🟡 MEDIUM | Multiple |

---

## CONTRADICTION #1: "is" Start Deadlock 🔴 CRITICAL

### The Conflict
**ESS-02 REQUIRES "is een..." but STR-01 + error_prevention FORBID it**

### Files & Line Numbers

#### A. REQUIRED BY: semantic_categorisation_module.py

**File:** `/Users/chrislehnen/Projecten/Definitie-app/src/services/prompts/modules/semantic_categorisation_module.py`

**Location 1 - ESS-02 Base Section (Line 136-151):**
```python
136 | base_section = """### 📐 Let op betekenislaag (ESS-02 - Ontologische categorie):
137 | Je **moet** één van de vier categorieën expliciet maken door de JUISTE KICK-OFF term te kiezen:
138 |
139 | • PROCES begrippen → start met: 'activiteit waarbij...', 'handeling die...', 'proces waarin...'
                                        ^^^^^^^^^^^^^^^^^^^^^^
                                        ALLOWS "is een activiteit"
140 | • TYPE begrippen → start met: 'soort...', 'categorie van...', 'type... dat...'
141 | • RESULTAAT begrippen → start met: 'resultaat van...', 'uitkomst van...', 'product dat...'
142 | • EXEMPLAAR begrippen → start met: 'exemplaar van... dat...', 'specifiek geval van...'
143 |
144 | ⚠️ Let op: Start NOOIT met 'is een' of andere koppelwerkwoorden!
                                       ^^^^^^
                                       EXPLICITLY FORBIDS "is een"! (CONTRADICTION!)
```

**Location 2 - PROCES Category Guidance (Lines 181-202):**
```python
181 | "proces": """**PROCES CATEGORIE - Formuleer als ACTIVITEIT/HANDELING:**
182 |
183 | KICK-OFF opties (kies één):
184 | - 'activiteit waarbij...' → focus op wat er gebeurt
185 | - 'handeling die...' → focus op de actie
186 | - 'proces waarin...' → focus op het verloop
187 |
188 | VERVOLG met:
189 | - WIE voert het uit (actor/rol)
190 | - WAT er precies gebeurt (actie)
191 | - HOE het verloopt (stappen/methode)
192 | - WAAR het begint en eindigt (scope)
193 |
194 | VOORBEELDEN (GOED):
195 | ✅ "activiteit waarbij gegevens worden verzameld door directe waarneming"
196 | ✅ "handeling waarin door middel van vraaggesprekken informatie wordt verzameld"
197 | ✅ "proces waarin documenten systematisch worden geanalyseerd"
198 |
199 | VOORBEELDEN (FOUT):
200 | ❌ "is een activiteit waarbij..." (start met 'is')
                ^^^^^^^^^^^^^^^^^^^^^^
                REQUIRES "is" for ontological identity but forbids it on line 144!
```

**Problem:** 
- Line 139 says "start met: 'activiteit waarbij...'" (ALLOWS "is een activiteit")
- Line 144 says "Start NOOIT met 'is een'" (FORBIDS "is een")
- Line 200 marks "is een activiteit waarbij..." as WRONG but this contradicts ESS-02's ontological need

#### B. FORBIDDEN BY: structure_rules_module.py

**File:** `/Users/chrislehnen/Projecten/Definitie-app/src/services/prompts/modules/structure_rules_module.py`

**Location - STR-01 Rule (Lines 136-151):**
```python
136 | rules.append("🔹 **STR-01 - definitie start met zelfstandig naamwoord**")
137 | rules.append(
138 |     "- De definitie moet starten met een zelfstandig naamwoord of naamwoordgroep, niet met een werkwoord."
139 | )
140 | rules.append(
141 |     "- Toetsvraag: Begint de definitie met een zelfstandig naamwoord of naamwoordgroep, en niet met een werkwoord?"
142 | )
143 |
144 | if self.include_examples:
145 |     rules.append("  ✅ proces dat beslissers identificeert...")
146 |     rules.append("  ✅ maatregel die recidive voorkomt...")
147 |     rules.append("  ❌ is een maatregel die recidive voorkomt")
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                        FORBIDS this exact pattern!
148 |     rules.append("  ❌ wordt toegepast in het gevangeniswezen")
```

**Problem:** 
- STR-01 forbids starting with "is" (line 147 shows "❌ is een maatregel...")
- But ESS-02 requires "is een activiteit..." for process definitions

#### C. FORBIDDEN BY: error_prevention_module.py

**File:** `/Users/chrislehnen/Projecten/Definitie-app/src/services/prompts/modules/error_prevention_module.py`

**Location 1 - Basic Errors (Lines 143-153):**
```python
143 | def _build_basic_errors(self) -> list[str]:
144 |     """Bouw basis veelgemaakte fouten."""
145 |     return [
146 |         "- ❌ Begin niet met lidwoorden ('de', 'het', 'een')",
147 |         "- ❌ Gebruik geen koppelwerkwoord aan het begin ('is', 'betekent', 'omvat')",
                                                                    ^^^^
                                                                    FORBIDS "is"
148 |         "- ❌ Herhaal het begrip niet letterlijk",
149 |         "- ❌ Gebruik geen synoniem als definitie",
150 |         "- ❌ Vermijd containerbegrippen ('proces', 'activiteit')",
151 |         "- ❌ Vermijd bijzinnen zoals 'die', 'waarin', 'zoals'",
152 |         "- ❌ Gebruik enkelvoud; infinitief bij werkwoorden",
153 |     ]
```

**Location 2 - Forbidden Starters (Lines 155-194):**
```python
155 | def _build_forbidden_starters(self) -> list[str]:
156 |     """Bouw uitgebreide lijst verboden startwoorden."""
157 |     forbidden_starters = [
158 |         "is",           # ← EXPLICITLY FORBIDDEN
159 |         "betreft",
160 |         "omvat",
161 |         "betekent",
162 |         ...
179 |         "een",          # ← ARTICLE FORBIDDEN
180 |         "proces waarbij",
181 |         "handeling die",
```

**Problem:**
- Line 158: "is" explicitly in forbidden starters
- Line 179: "een" explicitly forbidden
- But ESS-02 requires BOTH "is" and "een" for ontological markers

---

## CONTRADICTION #2: Container Terms Conflict 🔴 HIGH

### The Conflict
**ESS-02 REQUIRES "proces"/"activiteit" as ontological markers, but ARAI-02 + error_prevention FORBID them as vague**

### Files & Line Numbers

#### A. REQUIRED BY: semantic_categorisation_module.py

**File:** `/Users/chrislehnen/Projecten/Definitie-app/src/services/prompts/modules/semantic_categorisation_module.py`

**Location - PROCES Category (Lines 181-202):**
```python
181 | "proces": """**PROCES CATEGORIE - Formuleer als ACTIVITEIT/HANDELING:**
182 |
183 | KICK-OFF opties (kies één):
184 | - 'activiteit waarbij...' → focus op wat er gebeurt
                ^^^^^^^^^^
                REQUIRES "activiteit"
185 | - 'handeling die...' → focus op de actie
186 | - 'proces waarin...' → focus op het verloop
        ^^^^^^^
        REQUIRES "proces"
187 |
188 | VERVOLG met:
189 | ...
190 | VOORBEELDEN (GOED):
195 | ✅ "activiteit waarbij gegevens worden verzameld door directe waarneming"
                ^^^^^^^^^^
                REQUIRES "activiteit"
```

#### B. FORBIDDEN BY: arai_rules_module.py (via JSON rules loading)

**File:** `/Users/chrislehnen/Projecten/Definitie-app/src/services/prompts/modules/arai_rules_module.py`

**Location - ARAI-02 Rule Loading (Lines 53-92):**
```python
53 | def execute(self, context: ModuleContext) -> ModuleOutput:
54 |     """Genereer ARAI validatieregels."""
55 |     try:
56 |         sections = []
57 |         sections.append("### ✅ Algemene Regels AI (ARAI):")
58 |
59 |         # Load toetsregels on-demand from cached singleton
60 |         from toetsregels.cached_manager import get_cached_toetsregel_manager
61 |
62 |         manager = get_cached_toetsregel_manager()
63 |         all_rules = manager.get_all_regels()
64 |
65 |         # Filter alleen ARAI regels
66 |         arai_rules = {k: v for k, v in all_rules.items() if k.startswith("ARAI")}
67 |
68 |         # Sorteer regels
69 |         sorted_rules = sorted(arai_rules.items())
70 |
71 |         for regel_key, regel_data in sorted_rules:
72 |             sections.extend(self._format_rule(regel_key, regel_data))
```

**Problem:** 
- This module loads ARAI-02 from JSON (config/toetsregels/regels/ARAI-02.json)
- ARAI-02 forbids "proces" and "activiteit" without specificity
- But those words are REQUIRED by ESS-02 for ontological category marking

#### C. FORBIDDEN BY: error_prevention_module.py

**File:** `/Users/chrislehnen/Projecten/Definitie-app/src/services/prompts/modules/error_prevention_module.py`

**Location - Basic Errors (Line 150):**
```python
143 | def _build_basic_errors(self) -> list[str]:
144 |     """Bouw basis veelgemaakte fouten."""
145 |     return [
146 |         "- ❌ Begin niet met lidwoorden ('de', 'het', 'een')",
147 |         "- ❌ Gebruik geen koppelwerkwoord aan het begin ('is', 'betekent', 'omvat')",
148 |         "- ❌ Herhaal het begrip niet letterlijk",
149 |         "- ❌ Gebruik geen synoniem als definitie",
150 |         "- ❌ Vermijd containerbegrippen ('proces', 'activiteit')",
                                            ^^^^^^^^   ^^^^^^^^^^
                                            FORBIDDEN but REQUIRED by ESS-02
151 |         "- ❌ Vermijd bijzinnen zoals 'die', 'waarin', 'zoals'",
152 |         "- ❌ Gebruik enkelvoud; infinitief bij werkwoorden",
153 |     ]
```

**Problem:**
- Line 150: Explicitly forbids "proces" and "activiteit"
- But ESS-02 uses these terms as ontological category markers
- Same words, different contexts → CONTEXT MISMATCH

---

## CONTRADICTION #3: Relative Clauses Paradox 🟡 MEDIUM

### The Conflict
**Legacy forbids relative clauses, but Grammar teaches them and ESS-02 uses them**

### Files & Line Numbers

#### A. FORBIDDEN BY: error_prevention_module.py

**File:** `/Users/chrislehnen/Projecten/Definitie-app/src/services/prompts/modules/error_prevention_module.py`

**Location - Basic Errors (Line 151):**
```python
143 | def _build_basic_errors(self) -> list[str]:
144 |     """Bouw basis veelgemaakte fouten."""
145 |     return [
146 |         "- ❌ Begin niet met lidwoorden ('de', 'het', 'een')",
147 |         "- ❌ Gebruik geen koppelwerkwoord aan het begin ('is', 'betekent', 'omvat')",
148 |         "- ❌ Herhaal het begrip niet letterlijk",
149 |         "- ❌ Gebruik geen synoniem als definitie",
150 |         "- ❌ Vermijd containerbegrippen ('proces', 'activiteit')",
151 |         "- ❌ Vermijd bijzinnen zoals 'die', 'waarin', 'zoals'",
                                           ^^^^   ^^^^^^  ^^^^^
                                           FORBIDS these relative clauses
152 |         "- ❌ Gebruik enkelvoud; infinitief bij werkwoorden",
153 |     ]
```

#### B. TAUGHT BY: grammar_module.py

**File:** `/Users/chrislehnen/Projecten/Definitie-app/src/services/prompts/modules/grammar_module.py`

**Location - Grammar Rules (Lines 216-223):**
```python
216 | rules.append("- Voor bijzinnen: plaats komma voor 'waarbij', 'waardoor', etc.")
                                                             ^^^^^^
                                                             TEACHES this!
217 | rules.append("")
218 | rules.append("✅ proces waarbij gegevens worden verzameld, verwerkt en opgeslagen")
                       ^^^^^^^
                       USES "waarbij" despite error_prevention forbidding it
```

#### C. USED BY: semantic_categorisation_module.py

**File:** `/Users/chrislehnen/Projecten/Definitie-app/src/services/prompts/modules/semantic_categorisation_module.py`

**Location - PROCES Examples (Lines 195-197):**
```python
194 | VOORBEELDEN (GOED):
195 | ✅ "activiteit waarbij gegevens worden verzameld door directe waarneming"
                          ^^^^^^
                          USES "waarbij"
196 | ✅ "handeling waarin door middel van vraaggesprekken informatie wordt verzameld"
                        ^^^^^^
                        USES "waarin"
197 | ✅ "proces waarin documenten systematisch worden geanalyseerd"
                  ^^^^^^
                  USES "waarin"
```

**Problem:**
- Line 151 (error_prevention): Forbids "die", "waarin", "zoals"
- Lines 216-218 (grammar_module): Teaches correct usage of "waarbij"
- Lines 195-197 (semantic_categorisation): Good examples USE "waarbij" and "waarin"
- **Contradiction:** Can't forbid what's essential for Dutch grammar!

---

## CONTRADICTION #4: Article "een" Deadlock 🔴 CRITICAL

### The Conflict
**ESS-02 REQUIRES "is een..." but error_prevention FORBIDS starting with "een"**

### Files & Line Numbers

#### A. REQUIRED BY: semantic_categorisation_module.py

**File:** `/Users/chrislehnen/Projecten/Definitie-app/src/services/prompts/modules/semantic_categorisation_module.py`

**Location 1 - Base Section (Line 139, 142):**
```python
139 | • PROCES begrippen → start met: 'activiteit waarbij...', 'handeling die...', 'proces waarin...'
140 | • TYPE begrippen → start met: 'soort...', 'categorie van...', 'type... dat...'
141 | • RESULTAAT begrippen → start met: 'resultaat van...', 'uitkomst van...', 'product dat...'
142 | • EXEMPLAAR begrippen → start met: 'exemplaar van... dat...', 'specifiek geval van...'
```

**Location 2 - TYPE Category (Lines 203-223):**
```python
203 | "type": """**TYPE CATEGORIE - Formuleer als SOORT/CATEGORIE:**
204 |
205 | KICK-OFF opties (kies één):
206 | - 'soort... die...' → algemene classificatie
207 | - 'categorie van...' → formele indeling
208 | - 'type... dat...' → specifieke variant
209 | - 'klasse van...' → technische classificatie
```

**Location 3 - TYPE Examples (Lines 216-223):**
```python
216 | VOORBEELDEN (GOED):
217 | ✅ "soort document dat formele beslissingen vastlegt"
218 | ✅ "categorie van personen die aan bepaalde criteria voldoen"
219 | ✅ "type interventie gericht op gedragsverandering"
```

**Note:** While these examples don't explicitly show "een", the ontological pattern "is een soort/categorie/type" is implied throughout.

**Location 4 - RESULTAAT Category (Lines 224-244):**
```python
224 | "resultaat": """**RESULTAAT CATEGORIE - Formuleer als UITKOMST/PRODUCT:**
225 |
226 | KICK-OFF opties (kies één):
227 | - 'resultaat van...' → algemene uitkomst
228 | - 'uitkomst van...' → proces resultaat
229 | - 'product dat ontstaat door...' → tastbaar resultaat
230 | - 'gevolg van...' → causaal resultaat
```

**Location 5 - EXEMPLAAR Category (Lines 245-264):**
```python
245 | "exemplaar": """**EXEMPLAAR CATEGORIE - Formuleer als SPECIFIEK GEVAL:**
246 |
247 | KICK-OFF opties (kies één):
248 | - 'exemplaar van... dat...' → concrete instantie
249 | - 'specifiek geval van...' → individueel voorbeeld
250 | - 'individuele instantie van...' → uniek voorkomen
```

#### B. FORBIDDEN BY: error_prevention_module.py

**File:** `/Users/chrislehnen/Projecten/Definitie-app/src/services/prompts/modules/error_prevention_module.py`

**Location 1 - Basic Errors (Line 146):**
```python
143 | def _build_basic_errors(self) -> list[str]:
144 |     """Bouw basis veelgemaakte fouten."""
145 |     return [
146 |         "- ❌ Begin niet met lidwoorden ('de', 'het', 'een')",
                                                            ^^^^
                                                            FORBIDS "een"
147 |         "- ❌ Gebruik geen koppelwerkwoord aan het begin ('is', 'betekent', 'omvat')",
```

**Location 2 - Forbidden Starters (Line 179):**
```python
155 | def _build_forbidden_starters(self) -> list[str]:
156 |     """Bouw uitgebreide lijst verboden startwoorden."""
157 |     forbidden_starters = [
158 |         "is",
159 |         "betreft",
160 |         "omvat",
161 |         "betekent",
162 |         "verwijst naar",
163 |         "houdt in",
164 |         "heeft betrekking op",
165 |         "duidt op",
166 |         "staat voor",
167 |         "impliceert",
168 |         "definieert",
169 |         "beschrijft",
170 |         "wordt",
171 |         "zijn",
172 |         "was",
173 |         "waren",
174 |         "behelst",
175 |         "bevat",
176 |         "bestaat uit",
177 |         "de",
178 |         "het",
179 |         "een",   # ← EXPLICITLY FORBIDDEN
                       
180 |         "proces waarbij",
181 |         "handeling die",
```

**Problem:**
- Line 146: Forbids starting with "een"
- Line 179: "een" in explicit forbidden starters list
- But ESS-02 ontological identity statements require "is een..." pattern
- Example: "is een activiteit waarbij..." REQUIRES "een"

---

## CONTRADICTION #5: Context Integration Ambiguity 🟡 MEDIUM

### The Conflict
**Unclear HOW to apply context implicitly without making it traceable**

### Files & Line Numbers

#### A. REQUIRED BY: context_awareness_module.py

**File:** `/Users/chrislehnen/Projecten/Definitie-app/src/services/prompts/modules/context_awareness_module.py`

**Location - Context Application Instructions:**
```python
# Based on line references from DEF-102 analysis:
201 | "⚠️ VERPLICHT: Gebruik onderstaande specifieke context om de definitie te formuleren..."
242 | "Maak de definitie contextspecifiek zonder de context expliciet te benoemen."
```

#### B. CONFLICTED BY: CON Rules (loaded from JSON)

**The Challenge:**
- Definition must be "context-specific" (apply Strafrecht terminology)
- Definition must NOT be "context-explicit" (don't mention "Strafrecht")
- **How?** → Operationally unclear

**Problem Scenarios:**

| Scenario | Definition | Traceable? | Issue |
|----------|-----------|-----------|--------|
| Use context term | "strafrechtelijke maatregel" | ✅ Yes | Violates CON-01 |
| Implicit context | "maatregel die recidive voorkomt" | ⚠️ Implicit | Is recidive-focus enough? |
| Generic version | "opgelegde correctie bij overtredingen" | ❌ No | Context not applied? |

**The Ambiguity:** No clear validation criteria for "context-specific without explicit mention"

---

## SUMMARY: EXACT LINE NUMBERS BY FILE

### semantic_categorisation_module.py
- **Line 139**: ALLOWS "activiteit waarbij..." (ESS-02 requirement)
- **Line 144**: FORBIDS "is een" (contradicts line 139)
- **Line 184**: REQUIRES "activiteit waarbij..." 
- **Line 200**: Marks "is een activiteit whereby..." as WRONG (contradicts own pattern)

### structure_rules_module.py
- **Line 136-151**: STR-01 forbids starting with "is"
- **Line 147**: Example shows "❌ is een maatregel..." (contradicts ESS-02)

### error_prevention_module.py
- **Line 146**: Forbids articles ("een", "de", "het")
- **Line 147**: Forbids "is" at start
- **Line 150**: Forbids "proces" and "activiteit"
- **Line 151**: Forbids relative clauses ("die", "waarin")
- **Line 158**: "is" in forbidden starters
- **Line 179**: "een" in forbidden starters
- **Lines 180-181**: "proces waarbij" and "handeling die" in forbidden starters

### arai_rules_module.py
- **Lines 66, 71-72**: Loads ARAI-02 which forbids "proces"/"activiteit" as container terms

### grammar_module.py
- **Line 216**: Teaches comma placement with "waarbij"
- **Line 218**: Example uses "waarbij" (contradicts error_prevention)

---

## IMPLEMENTATION PRIORITY

### PHASE 1: CRITICAL FIXES (Impact: Unblock PROCES definitions)

1. **semantic_categorisation_module.py** - Add exception notice
   - Location: Line 182 (PROCES category)
   - Change: Add "⚠️ UITZONDERING" clause before existing guidance

2. **structure_rules_module.py** - Add exception clause
   - Location: After line 141 (after toetsvraag)
   - Change: Add "⚠️ UITZONDERING voor ESS-02" before examples

3. **error_prevention_module.py** - Modify 3 rules
   - Location 1: Line 147 (koppelwerkwoord) → Add "tenzij vereist voor ontologische categorie"
   - Location 2: Line 150 (containerbegrippen) → Add "behalve als ontologische marker"
   - Location 3: Line 151 (bijzinnen) → Change to "Beperk relatieve bijzinnen" (not forbid)

---

**END OF DETAILED ANALYSIS**
