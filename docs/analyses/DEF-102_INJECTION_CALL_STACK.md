# DEF-102: Exacte Functie Injection Call Stack Analyse

**Datum:** 2025-11-04
**Status:** Complete trace van alle 5 contradictions
**Doel:** Laat EXACT zien welke functie welk contradictie-deel injecteert

---

## 🎯 Overzicht

Dit document traced de **exacte call stack** van de PromptOrchestrator naar de specifieke functies die de **5 contradicterende delen** van de prompt injecteren.

---

## 📋 Call Stack Structuur

```
PromptOrchestrator.build_prompt()          # src/services/prompts/modules/prompt_orchestrator.py:143
    ↓
resolve_execution_order()                   # Lijn 169 - bepaalt module volgorde
    ↓
_execute_module(module_id, context)        # Lijn 213 - execute elke module
    ↓
module.execute(context)                     # Lijn 243 - roept specifieke module aan
    ↓
[SPECIFIEKE MODULE FUNCTIE]                 # Hier wordt de prompt tekst gegenereerd
```

---

## 🔴 Contradiction #1: "is" Usage Deadlock

### ✅ REQUIRES "is" (ESS-02)

**Call Stack:**
```
PromptOrchestrator.build_prompt()
    → _execute_module("semantic_categorisation", context)
    → SemanticCategorisationModule.execute(context)
    → _build_ess02_section(categorie)
    → _get_category_specific_guidance("proces")
```

**Exacte Injectie Functie:**
- **File:** `src/services/prompts/modules/semantic_categorisation_module.py`
- **Function:** `_get_category_specific_guidance(categorie: str) -> str | None`
- **Lijnen:** **180-197** (PROCES category)

**Geïnjecteerde Tekst (Lijn 182-185):**
```python
"proces": """**PROCES CATEGORIE - Focus op HANDELING en VERLOOP:**
Gebruik formuleringen zoals:
- 'is een activiteit waarbij...'      # ← VEREIST "is"!
- 'is het proces waarin...'            # ← VEREIST "is"!
- 'behelst de handeling van...'
- 'omvat de stappen die...'
```

**Ook in base section (Lijn 140-144):**
```python
base_section = """### 📐 Let op betekenislaag (ESS-02 - Ontologische categorie):
Je **moet** één van de vier categorieën expliciet maken:
Gebruik formuleringen zoals:
- 'is een activiteit waarbij...'       # ← VEREIST "is"!
- 'is het resultaat van...'            # ← VEREIST "is"!
```

---

### ❌ FORBIDS "is" (STR-01 + error_prevention)

#### A. STR-01 Regel

**Call Stack:**
```
PromptOrchestrator.build_prompt()
    → _execute_module("structure_rules", context)
    → StructureRulesModule.execute(context)
    → _build_str01_rule()
```

**Exacte Injectie Functie:**
- **File:** `src/services/prompts/modules/structure_rules_module.py`
- **Function:** `_build_str01_rule() -> list[str]`
- **Lijnen:** **132-151**

**Geïnjecteerde Tekst (Lijn 136-148):**
```python
rules.append("🔹 **STR-01 - definitie start met zelfstandig naamwoord**")
rules.append(
    "- De definitie moet starten met een zelfstandig naamwoord of naamwoordgroep, niet met een werkwoord."
)

if self.include_examples:
    rules.append("  ❌ is een maatregel die recidive voorkomt")  # ← VERBIEDT "is"!
```

#### B. Error Prevention Lijst

**Call Stack:**
```
PromptOrchestrator.build_prompt()
    → _execute_module("error_prevention", context)
    → ErrorPreventionModule.execute(context)
    → _build_forbidden_starters()
```

**Exacte Injectie Functie:**
- **File:** `src/services/prompts/modules/error_prevention_module.py`
- **Function:** `_build_forbidden_starters() -> list[str]`
- **Lijnen:** **155-194**

**Geïnjecteerde Tekst (Lijn 157-194):**
```python
forbidden_starters = [
    "is",                    # ← EXPLICIETE VERBOD regel 1!
    "betreft",
    "omvat",
    # ... rest
]

return [f"- ❌ Start niet met '{starter}'" for starter in forbidden_starters]
# Resulteert in: "- ❌ Start niet met 'is'"
```

**Ook in basic errors (Lijn 143-153):**
```python
def _build_basic_errors(self) -> list[str]:
    return [
        "- ❌ Begin niet met lidwoorden ('de', 'het', 'een')",
        "- ❌ Gebruik geen koppelwerkwoord aan het begin ('is', 'betekent', 'omvat')",  # ← VERBIEDT "is"!
        # ...
    ]
```

---

## 🔴 Contradiction #2: Container Terms Conflict

### ❌ FORBIDS "proces", "activiteit" (ARAI-02)

**Call Stack:**
```
PromptOrchestrator.build_prompt()
    → _execute_module("error_prevention", context)
    → ErrorPreventionModule.execute(context)
    → _build_basic_errors()
```

**Exacte Injectie Functie:**
- **File:** `src/services/prompts/modules/error_prevention_module.py`
- **Function:** `_build_basic_errors() -> list[str]`
- **Lijn:** **143-153** (lijn 150 specifiek)

**Geïnjecteerde Tekst (Lijn 150):**
```python
return [
    "- ❌ Begin niet met lidwoorden ('de', 'het', 'een')",
    "- ❌ Gebruik geen koppelwerkwoord aan het begin ('is', 'betekent', 'omvat')",
    "- ❌ Herhaal het begrip niet letterlijk",
    "- ❌ Gebruik geen synoniem als definitie",
    "- ❌ Vermijd containerbegrippen ('proces', 'activiteit')",  # ← VERBIEDT!
    # ...
]
```

---

### ✅ USES "proces", "activiteit" (ESS-02 templates)

**Call Stack:** (Zelfde als Contradiction #1)
```
PromptOrchestrator.build_prompt()
    → _execute_module("semantic_categorisation", context)
    → SemanticCategorisationModule.execute(context)
    → _build_ess02_section(categorie)
    → _get_category_specific_guidance("proces")
```

**Exacte Injectie Functie:**
- **File:** `src/services/prompts/modules/semantic_categorisation_module.py`
- **Function:** `_get_category_specific_guidance(categorie: str) -> str | None`
- **Lijnen:** **180-197**

**Geïnjecteerde Tekst (Lijn 182-184):**
```python
"proces": """**PROCES CATEGORIE - Focus op HANDELING en VERLOOP:**
Gebruik formuleringen zoals:
- 'is een activiteit waarbij...'       # ← GEBRUIKT "activiteit"!
- 'is het proces waarin...'            # ← GEBRUIKT "proces"!
```

---

## 🟡 Contradiction #3: Relative Clauses Paradox

### ❌ FORBIDS "die", "waarbij"

**Call Stack:**
```
PromptOrchestrator.build_prompt()
    → _execute_module("error_prevention", context)
    → ErrorPreventionModule.execute(context)
    → _build_basic_errors()
```

**Exacte Injectie Functie:**
- **File:** `src/services/prompts/modules/error_prevention_module.py`
- **Function:** `_build_basic_errors() -> list[str]`
- **Lijn:** **151**

**Geïnjecteerde Tekst:**
```python
"- ❌ Vermijd bijzinnen zoals 'die', 'waarin', 'zoals'"  # ← VERBIEDT "die"!
```

---

### ✅ USES "die", "waarbij" (ESS-02 + templates)

**Call Stack:** (Zelfde als Contradiction #1)

**Exacte Injectie Functie:**
- **File:** `src/services/prompts/modules/semantic_categorisation_module.py`
- **Lijnen:** **182, 196, etc.**

**Geïnjecteerde Tekst:**
```python
- 'is een activiteit waarbij...'          # ← GEBRUIKT "waarbij"!
- 'activiteit waarbij systematisch gevolgd wordt...'  # ← GEBRUIKT "waarbij"!
- 'maatregel die volgt op...'             # ← GEBRUIKT "die"!
```

---

## 🔴 Contradiction #4: Article "een"

### ❌ FORBIDS "een"

**Call Stack:**
```
PromptOrchestrator.build_prompt()
    → _execute_module("error_prevention", context)
    → ErrorPreventionModule.execute(context)
    → _build_basic_errors()
```

**Exacte Injectie Functie:**
- **File:** `src/services/prompts/modules/error_prevention_module.py`
- **Function:** `_build_basic_errors() -> list[str]`
- **Lijn:** **146**

**Geïnjecteerde Tekst:**
```python
"- ❌ Begin niet met lidwoorden ('de', 'het', 'een')"  # ← VERBIEDT "een"!
```

**Ook in forbidden_starters (Lijn 178-179):**
```python
forbidden_starters = [
    # ...
    "de",
    "het",
    "een",    # ← EXPLICIETE VERBOD!
    # ...
]
```

---

### ✅ USES "een" (ESS-02)

**Call Stack:** (Zelfde als Contradiction #1)

**Exacte Injectie Functie:**
- **File:** `src/services/prompts/modules/semantic_categorisation_module.py`
- **Lijnen:** **140-144, 182-185, etc.**

**Geïnjecteerde Tekst:**
```python
- 'is een activiteit waarbij...'       # ← GEBRUIKT "een"! (66.7% van patronen)
- 'is een soort...'
- 'is een categorie van...'
```

---

## 🟡 Contradiction #5: Context Usage Ambiguity

### ❌ FORBIDS Explicit Context

**Call Stack:**
```
PromptOrchestrator.build_prompt()
    → _execute_module("error_prevention", context)
    → ErrorPreventionModule.execute(context)
    → _build_context_forbidden(org_contexts, jur_contexts, wet_contexts)
```

**Exacte Injectie Functie:**
- **File:** `src/services/prompts/modules/error_prevention_module.py`
- **Function:** `_build_context_forbidden(...) -> list[str]`
- **Lijnen:** **196-248**

**Geïnjecteerde Tekst (Lijn 226-246):**
```python
# Organisatorische context verboden (Lijn 224-234)
for org in org_contexts:
    forbidden.append(
        f"- Gebruik de term '{org}' of een variant daarvan niet letterlijk in de definitie."
    )

# Juridische context verboden (Lijn 236-240)
for jur in jur_contexts:
    forbidden.append(
        f"- Vermijd expliciete vermelding van juridisch context '{jur}' in de definitie."
    )

# Wettelijke basis verboden (Lijn 242-246)
for wet in wet_contexts:
    forbidden.append(
        f"- Vermijd expliciete vermelding van wetboek '{wet}' in de definitie."
    )
```

**Laatste waarschuwing (Lijn 107-109):**
```python
sections.append(
    "\n🚫 Let op: context en bronnen mogen niet letterlijk of herleidbaar in de definitie voorkomen."
)
```

---

### ✅ REQUIRES Context Usage (CON-01)

**Probleem:** CON-01 zegt "context-specific" maar geeft GEEN operationele definitie van HOE context te gebruiken zonder het "traceable" te maken.

**Deze regel is NIET expliciet geïnjecteerd in een module**, maar is implied in:
- ContextAwarenessModule (set contexts)
- Validation rules (check context relevance)

**Operational Gap:**
- User moet context gebruiken ("Strafrecht")
- User mag "Strafrecht" niet noemen
- GEEN voorbeeld van HOE dit te doen

---

## 📊 Module Execution Order (Probleem Amplifier)

**Default Module Order (Lijn 354-372):**

```python
return [
    "expertise",                    # 1
    "output_specification",         # 2
    "grammar",                      # 3
    "context_awareness",            # 4
    "semantic_categorisation",      # 5 ← ZEGT: "gebruik 'is een activiteit'"
    "template",                     # 6
    "arai_rules",                   # 7
    "con_rules",                    # 8
    "ess_rules",                    # 9
    "structure_rules",              # 10 ← ZEGT: "niet starten met 'is'"
    "integrity_rules",              # 11
    "sam_rules",                    # 12
    "ver_rules",                    # 13
    "error_prevention",             # 14 ← ZEGT: "- ❌ Start niet met 'is'"
    "metrics",                      # 15
    "definition_task",              # 16
]
```

**Probleem:**
- ESS-02 (lijn 140-144, 182-185) zegt EERST: "gebruik 'is een activiteit'"
- STR-01 (lijn 147) zegt LATER: "❌ is een maatregel"
- error_prevention (lijn 157) zegt LAATSTE: "❌ Start niet met 'is'"

**Gevolg:** GPT-4 krijgt EERST instructie A, daarna instructie NOT-A → cognitive dissonance!

---

## 🎯 Critical Insight: Function Locations

### Priority 1: ESS-02 Exception Clause Toevoegen

**Target Function:**
- **File:** `src/services/prompts/modules/semantic_categorisation_module.py`
- **Function:** `_get_category_specific_guidance(categorie: str)`
- **Lijnen:** **180-197** (PROCES category)
- **Action:** Add exception notice BOVEN line 182

```python
# TOEVOEGEN (voor lijn 182):
"""
⚠️ EXCEPTION voor Ontologische Categorie (ESS-02):
Bij PROCES categorieën MAG je starten met:
- "is een activiteit waarbij..."
- "is het proces waarin..."
Dit is de ENIGE uitzondering op STR-01 en error_prevention regels.
"""
```

### Priority 2: STR-01 Exception Clause Toevoegen

**Target Function:**
- **File:** `src/services/prompts/modules/structure_rules_module.py`
- **Function:** `_build_str01_rule()`
- **Lijnen:** **132-151**
- **Action:** Add exception NA line 139

```python
# TOEVOEGEN (na lijn 139):
rules.append("⚠️ UITZONDERING: Bij ontologische categorie marking (ESS-02) MAG 'is een activiteit/proces/resultaat' gebruikt worden.")
```

### Priority 3: error_prevention Exception Clause

**Target Function:**
- **File:** `src/services/prompts/modules/error_prevention_module.py`
- **Function:** `_build_basic_errors()`
- **Lijnen:** **143-153**
- **Action:** Modify line 147

```python
# WIJZIG lijn 147 van:
"- ❌ Gebruik geen koppelwerkwoord aan het begin ('is', 'betekent', 'omvat')",

# NAAR:
"- ❌ Gebruik geen koppelwerkwoord aan het begin ('is', 'betekent', 'omvat') tenzij vereist voor ontologische categorie (ESS-02)",
```

### Priority 4: ARAI-02 Container Terms Exemption

**Target Function:**
- **File:** `src/services/prompts/modules/error_prevention_module.py`
- **Function:** `_build_basic_errors()`
- **Lijnen:** **150**
- **Action:** Modify line 150

```python
# WIJZIG lijn 150 van:
"- ❌ Vermijd containerbegrippen ('proces', 'activiteit')",

# NAAR:
"- ❌ Vermijd containerbegrippen ('proces', 'activiteit') behalve als ontologische marker (ESS-02)",
```

### Priority 5: Relative Clauses Clarification

**Target Function:**
- **File:** `src/services/prompts/modules/error_prevention_module.py`
- **Function:** `_build_basic_errors()`
- **Lijnen:** **151**
- **Action:** Modify line 151

```python
# WIJZIG lijn 151 van:
"- ❌ Vermijd bijzinnen zoals 'die', 'waarin', 'zoals'",

# NAAR:
"- ❌ Beperk bijzinnen ('die', 'waarin', 'waarbij'). Gebruik ALLEEN wanneer: (1) Nodig voor ontologische categorie (ESS-02), (2) Essentieel voor specificiteit",
```

---

## 🎯 Summary: Exact Injection Points

| Contradiction | Module | Function | Lijnen | Action |
|---------------|--------|----------|--------|--------|
| #1: "is" (REQUIRES) | `semantic_categorisation_module.py` | `_get_category_specific_guidance()` | 180-197 | Add exception notice |
| #1: "is" (FORBIDS) | `structure_rules_module.py` | `_build_str01_rule()` | 132-151 | Add exception clause |
| #1: "is" (FORBIDS) | `error_prevention_module.py` | `_build_basic_errors()` | 147 | Modify with "tenzij ESS-02" |
| #2: Container (FORBIDS) | `error_prevention_module.py` | `_build_basic_errors()` | 150 | Add "behalve ontologische marker" |
| #2: Container (USES) | `semantic_categorisation_module.py` | `_get_category_specific_guidance()` | 182-184 | (Blijft zoals is) |
| #3: Relative (FORBIDS) | `error_prevention_module.py` | `_build_basic_errors()` | 151 | Clarify with conditions |
| #4: "een" (FORBIDS) | `error_prevention_module.py` | `_build_basic_errors()` | 146 | (Blijft - geldt niet voor ESS-02 pattern) |
| #5: Context | `error_prevention_module.py` | `_build_context_forbidden()` | 196-248 | Add operational examples |

---

## 🚀 Implementation Strategy

1. **Start met Priority 1:** ESS-02 exception clause (semantic_categorisation_module.py)
2. **Dan Priority 2:** STR-01 exception (structure_rules_module.py)
3. **Dan Priority 3-5:** error_prevention modifications
4. **Test na elke wijziging:** Generate prompt en check for contradictions

**Estimated Effort:** 3 uur (zoals gespecificeerd in DEF-102)

---

**Document Compleet** ✅
Nu heb je EXACT welke functie welk deel injecteert, met regelnummers en call stacks!
