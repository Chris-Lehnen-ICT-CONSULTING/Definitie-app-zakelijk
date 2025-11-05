# DEF-102 Prompt Contradiction Architecture Map
## Complete Reconnaissance for Critical Blocking Issue

**Generated:** 2025-01-04  
**Thoroughness:** VERY THOROUGH  
**Mission:** Map complete prompt architecture for contradiction resolution

---

## 🎯 EXECUTIVE SUMMARY

**Severity:** BLOCKING - System UNUSABLE due to 5 contradictions  
**Architecture:** 16 prompt modules coordinated by `PromptOrchestrator`  
**Total Lines:** 4,419 lines across all modules  
**Contradiction Sources:** 5 distinct conflicts across 4 modules + JSON configs

---

## 📁 COMPLETE MODULE INVENTORY (16 Modules)

### Core Infrastructure
```
prompt_orchestrator.py      414 lines  Priority: N/A (orchestrator)
base_module.py              207 lines  Priority: N/A (base class)
```

### Content Generation Modules
```
expertise_module.py         199 lines  Priority: 90 (highest)
output_specification_module.py  174 lines  Priority: 85
grammar_module.py           255 lines  Priority: 80
context_awareness_module.py 432 lines  Priority: 70
semantic_categorisation_module.py  257 lines  Priority: N/A
template_module.py          250 lines  Priority: 60
```

### Validation Rule Modules (7 categories)
```
arai_rules_module.py        128 lines  Priority: 75
con_rules_module.py         128 lines  Priority: N/A
ess_rules_module.py         128 lines  Priority: 75  ⚠️ CONTRADICTION SOURCE
sam_rules_module.py         128 lines  Priority: N/A
structure_rules_module.py   329 lines  Priority: 65  ⚠️ CONTRADICTION SOURCE
integrity_rules_module.py   314 lines  Priority: N/A  ⚠️ CONTRADICTION SOURCE
ver_rules_module.py         128 lines  Priority: N/A
```

### Final Instructions
```
error_prevention_module.py  262 lines  Priority: N/A  ⚠️ CONTRADICTION SOURCE
metrics_module.py           326 lines  Priority: 50
definition_task_module.py   299 lines  Priority: 40
```

---

## 🔥 5 CONTRADICTIONS MAPPED

### CONTRADICTION #1: "is" - ESS-02 vs STR-01 + error_prevention
**Rule Conflict:** ESS-02 REQUIRES "is een" vs STR-01 + error_prevention FORBID "is"

**📍 Location 1A - ESS-02 JSON Config (REQUIRES "is")**
```
File: src/toetsregels/regels/ESS-02.json
Lines: 7-22

Content:
  "herkenbaar_patronen_type": [
    "\\b(is een|betreft een) (categorie|soort|klasse)\\b",  ← REQUIRES "is een"
  ],
  "herkenbaar_patronen_particulier": [
    "\\b(is een) exemplaar\\b",  ← REQUIRES "is een"
  ],
  "herkenbaar_patronen_proces": [
    "\\b(is een|betreft een) (proces|activiteit|handeling)\\b",  ← REQUIRES "is een"
  ],
  "goede_voorbeelden_proces": [
    "Observatie is een activiteit waarbij...",  ← REQUIRES "is een"
    "Interview is een activiteit waarbij..."     ← REQUIRES "is een"
  ]
```

**📍 Location 1B - Semantic Categorisation Module (REQUIRES "is")**
```
File: src/services/prompts/modules/semantic_categorisation_module.py
Lines: 136-257

CRITICAL INSTRUCTIONS (Lines 138-143):
- 'is een activiteit waarbij...'    ← REQUIRES "is een"
- 'is het resultaat van...'         ← REQUIRES "is"
- 'betreft een specifieke soort...' ← Alternative
- 'is een exemplaar van...'         ← REQUIRES "is een"

CATEGORY GUIDANCE (Lines 180-257):
Proces: 'is een activiteit waarbij...'  ← REQUIRES "is een"
Type: 'is een soort...'                 ← REQUIRES "is een"
Resultaat: 'is het resultaat van...'    ← REQUIRES "is"
Exemplaar: 'is een specifiek exemplaar' ← REQUIRES "is een"

EXAMPLES (Lines 195-236):
- validatie: proces waarbij...
- toezicht: activiteit waarbij...
- sanctie: maatregel die volgt op...
```

**📍 Location 1C - STR-01 JSON (FORBIDS "is")**
```
File: src/toetsregels/regels/STR-01.json
Lines: 7-22

  "herkenbaar_patronen": [
    "^is\\b",     ← FORBIDS "is" at start
  ],
  "foute_voorbeelden": [
    "is een maatregel die recidive voorkomt",  ← "is een" marked WRONG
  ]
```

**📍 Location 1D - Error Prevention Module (FORBIDS "is")**
```
File: src/services/prompts/modules/error_prevention_module.py
Lines: 143-194

Line 147: "- ❌ Gebruik geen koppelwerkwoord aan het begin ('is', 'betekent', 'omvat')"
Line 158: "is",  ← In forbidden starters list
```

**Impact:** CRITICAL - GPT-4 receives contradictory instructions:
- ESS-02: "Use 'is een activiteit'"
- STR-01: "Never start with 'is'"
- Result: Model confused, produces inconsistent definitions

---

### CONTRADICTION #2: "proces/activiteit" - ARAI-02 vs ESS-02
**Rule Conflict:** ARAI-02 FORBIDS "proces/activiteit" vs ESS-02 REQUIRES them

**📍 Location 2A - ARAI-02 JSON (FORBIDS "proces/activiteit")**
```
File: src/toetsregels/regels/ARAI-02.json
Lines: 4-20

  "uitleg": "De definitie mag geen containerbegrippen bevatten...",
  "toelichting": "Containerbegrippen zoals 'activiteit', 'proces'...",
  "herkenbaar_patronen": [
    "\\bproces\\b(?!\\s+dat|\\s+van)",      ← FORBIDS "proces"
    "\\bactiviteit\\b(?!\\s+die|\\s+van)", ← FORBIDS "activiteit"
  ],
  "foute_voorbeelden": [
    "proces ter ondersteuning",
    "activiteit binnen het systeem"
  ]
```

**📍 Location 2B - ARAI Rules Module (FORBIDS via JSON loading)**
```
File: src/services/prompts/modules/arai_rules_module.py
Lines: 53-92

Loads ARAI-02.json via:
  manager = get_cached_toetsregel_manager()
  all_rules = manager.get_all_regels()
  arai_rules = {k: v for k, v in all_rules.items() if k.startswith("ARAI")}
```

**📍 Location 2C - ESS-02 Requires "proces/activiteit"**
```
File: src/services/prompts/modules/semantic_categorisation_module.py
Lines: 180-197

PROCES CATEGORIE - Focus op HANDELING en VERLOOP:
- 'is een activiteit waarbij...'     ← REQUIRES "activiteit"
- 'is het proces waarin...'          ← REQUIRES "proces"
- 'behelst de handeling van...'
- 'omvat de stappen die...'

VOORBEELDEN van procesbegrippen:
- validatie: proces waarbij...        ← REQUIRES "proces"
- toezicht: activiteit waarbij...     ← REQUIRES "activiteit"
- sanctionering: het proces van...    ← REQUIRES "proces"
```

**Impact:** HIGH - For "proces" category terms:
- ARAI-02: "Avoid 'proces' and 'activiteit'"
- ESS-02: "Use 'is een activiteit waarbij' or 'is het proces waarin'"
- Result: Model cannot satisfy both rules

---

### CONTRADICTION #3: "die/waarbij" - Line 151 vs Templates
**Rule Conflict:** error_prevention FORBIDS "die/waarin" vs templates USE them

**📍 Location 3A - Error Prevention (FORBIDS "die")**
```
File: src/services/prompts/modules/error_prevention_module.py
Lines: 143-153

Line 151: "- ❌ Vermijd bijzinnen zoals 'die', 'waarin', 'zoals'"
Line 262: "| Bijzinconstructies  | ✅ | Vermijd 'die', 'waarin', 'zoals' enz. |"
```

**📍 Location 3B - Template Module (USES "die")**
```
File: src/services/prompts/modules/template_module.py
Lines: 155-250

Line 201: "- [begrip]: [categorie] die/dat [onderscheidend kenmerk]"  ← USES "die/dat"
Line 214: "- maatregel: soort interventie die..."                      ← USES "die"
Line 222: "- sanctie: maatregel die volgt op..."                       ← USES "die"
```

**📍 Location 3C - Semantic Categorisation (USES "die")**
```
File: src/services/prompts/modules/semantic_categorisation_module.py
Lines: 185-235

Line 214: "- maatregel: soort interventie die..."  ← USES "die"
Line 222: "- sanctie: maatregel die volgt op..."   ← USES "die"
```

**📍 Location 3D - INT-08 Allows "die" in Exception Context**
```
File: src/services/prompts/modules/integrity_rules_module.py
Lines: 297-300

Line 297: "uitzondering voor onderdelen die de definitie specifieker maken 
           (bijv. relatieve bijzinnen)."
```

**Impact:** MEDIUM-HIGH - Templates use "die" but error_prevention forbids it:
- error_prevention: "Vermijd 'die'"
- Templates: "Use 'maatregel die volgt op'"
- INT-08: "Exception for relative clauses"
- Result: Inconsistent guidance on relative clauses

---

### CONTRADICTION #4: "een" - Line 146 vs ESS-02 Templates
**Rule Conflict:** error_prevention FORBIDS "een" vs templates REQUIRE "is een"

**📍 Location 4A - Error Prevention (FORBIDS "een")**
```
File: src/services/prompts/modules/error_prevention_module.py
Lines: 143-194

Line 146: "- ❌ Begin niet met lidwoorden ('de', 'het', 'een')"
Line 179: "een",  ← In forbidden starters list
Lines 188-191:
    "een belangrijk",
    "een essentieel",
    "een vaak gebruikte",
    "een veelvoorkomende",
```

**📍 Location 4B - ESS-02 Templates (REQUIRE "een")**
```
File: src/services/prompts/modules/semantic_categorisation_module.py
Lines: 138-257

Line 140: "- 'is een activiteit waarbij...'   ← REQUIRES "een"
Line 143: "- 'is een exemplaar van...'        ← REQUIRES "een"
Line 182: "- 'is een activiteit waarbij...'   ← REQUIRES "een"
Line 200: "- 'is een soort...'                ← REQUIRES "een"
Line 202: "- 'is een type...'                 ← REQUIRES "een"
```

**Impact:** CRITICAL - Same as Contradiction #1, bundled with "is" issue:
- error_prevention: "Don't start with 'een'"
- ESS-02: "Use 'is een activiteit'" 
- Result: Templates directly contradict forbidden list

---

### CONTRADICTION #5: Context Usage - Implicit vs Explicit
**Rule Conflict:** "Don't mention context" vs "Use specific context"

**📍 Location 5A - Context Awareness (REQUIRES Context Use)**
```
File: src/services/prompts/modules/context_awareness_module.py
Lines: 186-279

Line 201: "⚠️ VERPLICHT: Gebruik onderstaande specifieke context..."
Line 241: "⚠️ BELANGRIJKE INSTRUCTIE: Gebruik onderstaande context..."
Line 277: "⚠️ INSTRUCTIE: Formuleer de definitie specifiek voor ... context"
```

**📍 Location 5B - Error Prevention (FORBIDS Context Mention)**
```
File: src/services/prompts/modules/error_prevention_module.py
Lines: 196-248

Lines 226-246: Context-specific FORBIDDEN patterns:
  "- Gebruik de term '{org}' of een variant daarvan niet letterlijk..."
  "- Vermijd expliciete vermelding van juridisch context..."
  "- Vermijd expliciete vermelding van wetboek..."

Line 108: "🚫 Let op: context en bronnen mogen niet letterlijk of 
           herleidbaar in de definitie voorkomen."
```

**Impact:** MEDIUM - Vague guidance on context integration:
- context_awareness: "Use context to make definition specific"
- error_prevention: "Don't mention context literally"
- Result: Unclear HOW to use context without mentioning it

---

## 🔄 MODULE EXECUTION ORDER

**Orchestrator Logic:**
```
File: src/services/prompts/modules/prompt_orchestrator.py
Lines: 347-372

DEFAULT MODULE ORDER (Lines 354-372):
1. expertise               (Priority: 90)
2. output_specification    (Priority: 85)
3. grammar                 (Priority: 80)
4. context_awareness       (Priority: 70)
5. semantic_categorisation (ESS-02 guidance)  ⚠️ Contradiction source
6. template                (Priority: 60)     ⚠️ Contradiction source
   --- VALIDATION RULES ---
7. arai_rules              (Priority: 75)     ⚠️ Contradiction source
8. con_rules
9. ess_rules               (Priority: 75)     ⚠️ Contradiction source
10. structure_rules        (Priority: 65)     ⚠️ Contradiction source
11. integrity_rules                           ⚠️ Contradiction source
12. sam_rules
13. ver_rules
14. error_prevention                          ⚠️ Contradiction source
15. metrics               (Priority: 50)
16. definition_task       (Priority: 40)

CRITICAL: semantic_categorisation runs BEFORE validation rules
→ Establishes "is een" pattern
→ Then structure_rules FORBIDS "is"
→ ORDER AMPLIFIES CONTRADICTION!
```

---

## 🎯 EXISTING EXCEPTION HANDLING PATTERNS

**Search Results:**
```bash
grep -r "(EXCEPTION|UITZONDERING|unless|except when|behalve|tenzij)" modules/
```

**Found Patterns:**

### 1. **INT-08 - Positive Formulation Exception**
```
File: src/services/prompts/modules/integrity_rules_module.py
Lines: 297-300

"Een definitie wordt in principe positief geformuleerd, 
 uitzondering voor onderdelen die de definitie specifieker maken 
 (bijv. relatieve bijzinnen)."
```
**Pattern:** "uitzondering voor [condition]"

### 2. **Grammar Module - Singular/Plural Exception**
```
File: src/services/prompts/modules/grammar_module.py
Line 136

"- Gebruik enkelvoud tenzij het begrip specifiek een meervoud aanduidt"
```
**Pattern:** "[rule] tenzij [condition]"

### 3. **Output Specification - Jargon Exception**
```
File: src/services/prompts/modules/output_specification_module.py
Line 171

"- Vermijd jargon tenzij noodzakelijk voor het vakgebied"
```
**Pattern:** "Vermijd X tenzij Y"

### 4. **Metrics Module - Non-alphanumeric Exception**
```
File: src/services/prompts/modules/metrics_module.py
Line 289

"# Check voor niet-alfanumerieke karakters (behalve spaties en koppeltekens)"
```
**Pattern:** "X (behalve Y en Z)"

**✅ CONCLUSION:** Exception patterns EXIST and are USED in 4 modules!
**Recommended Pattern:** "tenzij [condition]" or "uitzondering voor [context]"

---

## 🔗 INTEGRATION POINTS FOR FIXES

### Critical Integration Points:

**1. ModularPromptAdapter (Entry Point)**
```
File: src/services/prompts/modular_prompt_adapter.py
Lines: 42-88

Function: get_cached_orchestrator()
- Singleton pattern
- Registers all 16 modules
- Integration point: Add exception configuration here
```

**2. Module Configuration System**
```
File: src/services/prompts/modular_prompt_adapter.py
Lines: 136-150

Function: _convert_config_to_module_configs()
- Converts PromptComponentConfig to module configs
- Integration point: Add exception_handling config
```

**3. Shared State Between Modules**
```
File: src/services/prompts/modules/base_module.py
Lines: 70-130

Class: ModuleContext
Methods:
- get_shared(key, default)
- set_shared(key, value)

Integration point: Share ontological_category to enable conditional rules
```

**4. Dependency Resolution**
```
File: src/services/prompts/modules/prompt_orchestrator.py
Lines: 97-141

Function: resolve_execution_order()
- Kahn's algorithm for topological sort
- Integration point: Ensure semantic_categorisation runs before rules
```

---

## 📊 CONTRADICTION DEPENDENCY GRAPH

```
ModuleContext.ontological_category
    │
    ├─> semantic_categorisation_module.py (Sets "proces"/"type"/"resultaat")
    │   └─> Instructs: "Use 'is een activiteit'" ⚠️
    │
    ├─> error_prevention_module.py (Reads context)
    │   └─> Forbids: "'is', 'een', 'proces', 'activiteit', 'die'" ⚠️
    │
    ├─> ess_rules_module.py (Loads ESS-02.json)
    │   └─> Pattern: "\\b(is een|betreft een)" ⚠️
    │
    ├─> arai_rules_module.py (Loads ARAI-02.json)
    │   └─> Forbids: "\\bproces\\b", "\\bactiviteit\\b" ⚠️
    │
    ├─> structure_rules_module.py (Hardcoded STR-01)
    │   └─> Forbids: "^is\\b" ⚠️
    │
    └─> template_module.py (Provides examples)
        └─> Uses: "maatregel die...", "proces waarbij..." ⚠️

CRITICAL PATH: semantic_categorisation → error_prevention → structure_rules
CONFLICT AMPLIFICATION: Each module reinforces contradictions
```

---

## 🛠️ FIX INTEGRATION STRATEGY

### Recommended Fix Points (Priority Order):

**1. HIGHEST PRIORITY - ESS-02 Module (semantic_categorisation)**
```
Action: Add conditional exception clauses based on ontological_category
Location: Lines 136-257
Strategy: "Use 'activiteit waarbij' INSTEAD OF 'is een activiteit'"
```

**2. HIGH PRIORITY - Error Prevention Module**
```
Action: Add ontological_category exceptions to forbidden patterns
Location: Lines 143-194
Strategy: Forbid "is een" EXCEPT when ontological_category is set
```

**3. HIGH PRIORITY - STR-01 Module (structure_rules)**
```
Action: Add exception for ESS-02 category markers
Location: Lines 132-151
Strategy: "Avoid 'is' EXCEPT for ontological category markers"
```

**4. MEDIUM PRIORITY - ARAI-02 Module (arai_rules)**
```
Action: Update JSON to allow "proces/activiteit" with proper continuation
Location: src/toetsregels/regels/ARAI-02.json
Strategy: Keep regex patterns, add exception note in "uitleg"
```

**5. LOW PRIORITY - Template Module**
```
Action: Add "(uitzondering: relatieve bijzinnen)" to examples
Location: Lines 155-250
Strategy: Document why "die" is allowed in specific contexts
```

---

## 📝 EXACT LINE NUMBERS FOR FIXES

### semantic_categorisation_module.py
```
Line 140: "- 'is een activiteit waarbij...'
REPLACE WITH: "- 'activiteit waarbij...' (uitzondering: mag beginnen met 'is een' voor categoriemarkering)"

Line 182-183: PROCES guidance
ADD BEFORE: "⚠️ UITZONDERING voor ESS-02: 'proces' en 'activiteit' zijn toegestaan in deze context"
```

### error_prevention_module.py
```
Line 147: "- ❌ Gebruik geen koppelwerkwoord aan het begin ('is', 'betekent', 'omvat')"
REPLACE WITH: "- ❌ Gebruik geen koppelwerkwoord aan het begin ('is', 'betekent', 'omvat'), 
               tenzij gevolgd door ontologische categorie (bijv. 'is een activiteit waarbij')"

Line 151: "- ❌ Vermijd bijzinnen zoals 'die', 'waarin', 'zoals'"
REPLACE WITH: "- ❌ Vermijd bijzinnen zoals 'die', 'waarin', 'zoals', 
               behalve in relatieve bijzinnen die specificeren"
```

### ARAI-02.json
```
Line 4-5: "uitleg" field
ADD: "Uitzondering: 'proces' en 'activiteit' zijn toegestaan wanneer gevolgd door 
      specificerende relativizin (bijv. 'proces dat', 'activiteit die')"
```

### structure_rules_module.py (STR-01)
```
Line 137-139: STR-01 rule text
ADD after line 139: "Uitzondering: 'is een' is toegestaan voor ontologische categoriemarkering 
                     (bijv. 'is een activiteit waarbij', 'is een soort')."
```

---

## 📚 REFERENCE FILES FOR BUSINESS LOGIC

**Validation Rules Storage:**
```
JSON Configs:     src/toetsregels/regels/*.json (45 files)
Python Impls:     src/toetsregels/regels/*.py (45 files)
Cache Manager:    src/toetsregels/cached_manager.py
Rule Cache:       src/toetsregels/rule_cache.py
```

**Module Loading:**
```
Entry Point:      src/services/prompts/prompt_service_v2.py
Adapter:          src/services/prompts/modular_prompt_adapter.py
Orchestrator:     src/services/prompts/modules/prompt_orchestrator.py
```

**Configuration:**
```
Component Config: src/services/prompts/modular_prompt_builder.py (PromptComponentConfig)
Generator Config: src/services/definition_generator_config.py (UnifiedGeneratorConfig)
```

---

## ✅ RECONNAISSANCE COMPLETE

**Total Files Analyzed:** 26 Python files + 3 JSON configs  
**Total Lines Analyzed:** ~5,000 lines  
**Contradictions Mapped:** 5 (all locations identified)  
**Exception Patterns Found:** 4 existing patterns  
**Fix Points Identified:** 5 critical integration points  
**Exact Line Numbers:** Documented for all contradictions

**Next Steps:**
1. Review this architecture map with team
2. Prioritize fixes (ESS-02 → error_prevention → STR-01)
3. Implement exception clauses using "tenzij" pattern
4. Test with 45 validation rules
5. Verify no new contradictions introduced

**Risk Assessment:**
- Fixes are SURGICAL (5-10 lines per module)
- Exception patterns already exist in codebase
- No breaking changes to orchestrator logic
- Backwards compatible with existing rules

---

**Generated for:** DEF-102 (BLOCKING)  
**Architecture Version:** Modular v2.0  
**Reconnaissance Depth:** VERY THOROUGH ✅
