# Validatieregels Business Logic Extraction

**Extraction Date:** 2025-10-02
**Total Rules:** 53 validation rules
**Codebase:** DefinitieAgent - Dutch Legal Definition Generator

---

## Overview

### Rule Distribution by Category

| Category | Count | Priority Distribution | Purpose |
|----------|-------|----------------------|---------|
| **ARAI** | 9 | High: 1, Medium: 8 | Atomiciteit, Relevantie, Adequaatheid, Inconsistentie - Linguistic quality |
| **CON** | 3 | High: 3 | Consistentie - Context and source authenticity |
| **DUP** | 1 | High: 1 | Duplicate detection in database |
| **ESS** | 6 | High: 5, Medium: 1 | Essentie - Core meaning and distinguishing features |
| **INT** | 9 | High: 3, Medium: 6 | Intertekstueel - Internal clarity and comprehensibility |
| **SAM** | 8 | High: 4, Medium: 4 | Samenhang - Coherence and relationships |
| **STR** | 11 | High: 4, Medium: 7 | Structuur - Structural formatting |
| **VAL** | 3 | High: 3 | Validatie - Basic validation (empty, length) |
| **VER** | 3 | High: 1, Medium: 2 | Verduidelijking - Clarification rules |

### Total: 53 rules
- **Critical/High Priority:** 25 rules (47%)
- **Medium Priority:** 28 rules (53%)

### Architecture Overview

```
ModularValidationService
├── ToetsregelManager (rule loader)
├── 53 JSON rule definitions (src/toetsregels/regels/*.json)
├── 46 Python implementations (src/toetsregels/regels/*.py)
├── ValidationOrchestratorV2 (orchestration)
├── ApprovalGatePolicy (EPIC-016 - gate thresholds)
└── Aggregation logic (weighted scoring, category scores)
```

---

## ARAI Category (Atomiciteit, Relevantie, Adequaatheid, Inconsistentie)

### Purpose
Ensures linguistic quality, precision, and clarity. Prevents vague, ambiguous, or overly complex language in definitions.

---

### ARAI-01: Geen werkwoord als kern (afgeleid)

**Priority:** Medium
**Recommendation:** Optional
**Status:** Conceptual

#### Business Purpose
Prevents confusion between actions and concepts by ensuring the definition core is a noun, not a verb. Derived from ASTRA principle "Definitie ≠ beschrijving van gedrag" (Definition ≠ description of behavior).

#### Validation Logic
- **Pattern Detection:** Searches for verb patterns at the definition's core: `(is|zijn|doet|kan|heeft|hebben|wordt|vormt|creëert)`
- **Check:** Is the core a noun (not a verb)?
- **Good:** "proces dat beslissers identificeert", "instelling die zorg verleent"
- **Bad:** "Een systeem dat registreert...", "Een functie die uitvoert..."

#### Error Handling
- **Success:** "✔️ ARAI01: geen werkwoorden als kern gevonden"
- **Failure:** "❌ ARAI01: werkwoord(en) als kern gevonden ({werkwoorden})"
- **Score:** 1.0 (pass) | 0.0 (fail)

#### Dependencies
- Related to STR-01 (must start with noun)
- Conceptually linked to avoiding action-based definitions

---

### ARAI-02: Vermijd vage containerbegrippen

**Priority:** Medium
**Recommendation:** Optional
**Status:** Conceptual

#### Business Purpose
Prevents use of vague container terms ("aspect", "element", "activity", "process", "system") without further specification. Ensures definitions are informative and testable.

#### Validation Logic
- **Pattern Detection:**
  - `\bproces\b(?!\s+dat|\s+van)` - "proces" without "dat" or "van"
  - `\bactiviteit\b(?!\s+die|\s+van)` - "activiteit" without "die" or "van"
  - `\bsysteem\b(?!\s+dat|\s+voor)` - "systeem" without "dat" or "voor"
  - `\baspect\b`, `\belement\b` - unqualified container terms
- **Good:** "proces dat gegevens verzamelt voor analyse"
- **Bad:** "proces ter ondersteuning", "activiteit binnen het systeem"

#### Error Handling
- **Failure:** "❌ ARAI02: containerbegrip zonder specificatie gevonden"
- **Score:** 0.5 (warning) | 0.0 (fail)

#### Dependencies
- Has sub-rules: ARAI-02SUB1 (lexical containers), ARAI-02SUB2 (bureaucratic containers)

---

### ARAI-02SUB1: Lexicale containerbegrippen vermijden

**Priority:** Medium
**Recommendation:** Optional
**Status:** Conceptual

#### Business Purpose
Sub-rule of ARAI-02. Targets generic lexical terms like "aspect", "thing", "something", "element", "factor" that add no concrete meaning.

#### Validation Logic
- **Forbidden Terms:** `aspect`, `ding`, `iets`, `element`, `factor`
- **Good:** "maatregel die gericht is op risicobeheersing"
- **Bad:** "iets dat helpt bij het beheersen van risico's"

---

### ARAI-02SUB2: Ambtelijke containerbegrippen vermijden

**Priority:** Medium
**Recommendation:** Optional
**Status:** Conceptual

#### Business Purpose
Sub-rule of ARAI-02. Targets bureaucratic vague terms like "proces", "voorziening", "activiteit" when unspecified.

#### Validation Logic
- **Forbidden (unqualified):** `proces`, `aspect`, `element`, `voorziening`, `activiteit`, `ding(en)`
- **Good:** "systeem: geautomatiseerd hulpmiddel dat beslissingen registreert"
- **Bad:** "voorziening die iets mogelijk maakt"

---

### ARAI-03: Beperk gebruik van bijvoeglijke naamwoorden

**Priority:** Medium
**Recommendation:** Optional
**Status:** Conceptual

#### Business Purpose
Limits use of subjective or context-dependent adjectives ("effective", "important", "relevant", "adequate") that reduce objectivity and testability.

#### Validation Logic
- **Forbidden Adjectives:** `effectief`, `belangrijk`, `relevant`, `toereikend`, `adequaat`
- **Good:** "maatregel die leidt tot het voorkomen van recidive"
- **Bad:** "belangrijke maatregel ter bevordering van veiligheid"

#### Error Handling
- **Failure:** "❌ ARAI03: subjectieve bijvoeglijke naamwoorden gevonden"

---

### ARAI-04: Vermijd modale hulpwerkwoorden

**Priority:** Medium
**Recommendation:** Optional
**Status:** Conceptual

#### Business Purpose
Avoids modal auxiliary verbs ("kunnen", "mogen", "moeten", "zullen") that imply possibility, permission, or obligation. Definitions should describe what something *is*, not what it *could* or *should* be.

#### Validation Logic
- **Forbidden Modals:** `kan`, `kunnen`, `moet`, `moeten`, `mogen`, `zou`, `zullen`
- **Good:** "maatregel die toegang beperkt tot bevoegde personen"
- **Bad:** "maatregel die toegang kan beperken"

#### Dependencies
- Has sub-rule: ARAI-04SUB1
- Related to INT-06 (no explanatory clauses)

---

### ARAI-04SUB1: Beperk gebruik van modale werkwoorden

**Priority:** Medium
**Recommendation:** Optional
**Status:** Conceptual

#### Business Purpose
Sub-rule of ARAI-04. Reinforces avoidance of modals to prevent confusion about whether something is a characteristic or a precondition.

---

### ARAI-05: Vermijd impliciete aannames

**Priority:** Medium
**Recommendation:** Optional
**Status:** Conceptual

#### Business Purpose
Prevents implicit assumptions that require prior knowledge ("zoals gebruikelijk", "zoals bekend", "in het systeem"). Definitions must be self-contained and understandable without implicit references.

#### Validation Logic
- **Forbidden Phrases:** `zoals gebruikelijk`, `zoals bekend`, `in het systeem`, `de standaard`, `bekende procedure`
- **Good:** "procedure: vastgelegde reeks stappen die wordt uitgevoerd bij het registreren van incidenten"
- **Bad:** "procedure: zoals gebruikelijk uitgevoerd binnen het systeem"

#### Error Handling
- **Failure:** "❌ ARAI05: impliciete aannames gevonden"

#### Dependencies
- Related to INT-10 (no inaccessible background knowledge)

---

### ARAI-06: Correcte definitiestart

**Priority:** High
**Recommendation:** Mandatory
**Status:** Conceptual

#### Business Purpose
COMPOSITE RULE combining three common errors:
1. No article at start ("de", "het", "een")
2. No copula verb at start ("is", "omvat", "betekent")
3. No repetition of the term in the definition

Prevents circular definitions and ensures definitions start with the core noun.

#### Validation Logic
- **Forbidden Starts:** `^\s*(de|het|een)\s+`, `^\s*(is|omvat|betekent)\s+`
- **Good:** "proces waarbij toezicht plaatsvindt op naleving van wetgeving"
- **Bad:** "De maatregel is bedoeld voor naleving", "Het begrip betekent: een controlemechanisme"

#### Error Handling
- **Failure:** "❌ ARAI06: definitie start incorrect (lidwoord/koppelwerkwoord/herhaling)"
- **Score:** 0.0 (fail) | 1.0 (pass)

#### Dependencies
- Combines: STR-01 (start with noun), STR-02 (kick-off ≠ term), SAM-05 (no circular definitions)

---

## CON Category (Consistentie)

### Purpose
Ensures context-specific formulation without explicit naming, and basis in authentic sources. Critical for legal validity and reusability.

---

### CON-01: Contextspecifieke formulering zonder expliciete benoeming

**Priority:** High
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
**CRITICAL RULE FOR CONTEXT MANAGEMENT**

Ensures definitions are tailored to organizational, legal, and legislative context WITHOUT explicitly naming that context in the definition text. Context must be implicit, not explicit.

**DUPLICATE DETECTION:** During generation, checks for existing definitions with:
- Same term (begrip)
- Same synonyms (case-insensitive)
- Same context (organizational, legal, legislative basis - order-independent for legislative basis)

If duplicate found, displays warning with explanation (e.g., "Found via synonym ... with same context").

#### Validation Logic
- **Dynamic Context Check:** Extracts user-provided contexts:
  - `organisatorische_context` (organizational)
  - `juridische_context` (legal)
  - `wettelijke_basis` (legislative basis)
- **Forbidden Explicit References:**
  - `in de context van`, `in het kader van`, `binnen de context`
  - `juridisch`, `beleidsmatig`, `operationeel`, `technisch`
  - Organization names: `DJI`, `OM`, `ZM`, `KMAR`
  - Legal domains: `strafrecht`, `bestuursrecht`, `civiel recht`
  - Basis phrases: `op grond van de wet`, `met basis in de regeling`

#### Error Handling
- **Context Literally Found:** "❌ CON-01: opgegeven context letterlijk in definitie herkend ('{gevonden}')"
- **Broad Context Terms:** "🟡 CON-01: bredere contexttaal herkend, formulering mogelijk vaag" (score 0.5)
- **Duplicate Found:** "❌ CON-01: er bestaan meerdere definities voor dit begrip met dezelfde context (aantal: {cnt})"
- **Success:** "✔️ CON-01: geen expliciete contextverwijzing aangetroffen" (score 0.9)

#### Implementation Details
```python
# Duplicate detection logic (from CON01Validator)
def _as_str_one(val):
    if isinstance(val, list):
        return str(val[0]) if val else ""
    return str(val or "")

org = _as_str_one(contexten.get("organisatorische_context", []))
jur = _as_str_one(contexten.get("juridische_context", []))
wet = contexten.get("wettelijke_basis", [])
wet_list = wet if isinstance(wet, list) else []

if org or jur or wet_list:
    cnt = repo.count_exact_by_context(
        begrip=begrip,
        organisatorische_context=org,
        juridische_context=jur,
        wettelijke_basis=wet_list,
    )
    if cnt > 1:
        return (False, "❌ CON-01: duplicate found", 0.0)
```

#### Dependencies
- Critical for EPIC-016 context management
- Interacts with: DefinitieRepository.count_exact_by_context()
- Related to synonym handling in generation flow

---

### CON-02: Baseren op authentieke bron

**Priority:** High
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
Ensures definitions are based on authoritative or official sources (legislation, policy documents, standards). Guarantees reliability and reduces interpretation disputes.

#### Validation Logic
- **Source Indicators (General):**
  - `volgens (de|het)`, `zoals beschreven in`, `zoals bepaald in`, `conform`, `overeenkomstig`
  - `op grond van`, `ingevolge`
- **Source Patterns (Specific):**
  - Article references: `art. \d+`, `artikel \d+`
  - Legal codes: `AVG`, `Awb`, `WvSr`, `WvSv`
  - Document types: `Wetboek`, `Besluit`, `Regeling`, `Beleidsregel`, `Standaard`, `Verordening`
- **Good:** "gegevensverwerking: iedere handeling met gegevens zoals bedoeld in de AVG"
- **Bad:** "gegevensverwerking: handeling met gegevens (geen bron vermeld)"

#### Error Handling
- **No Source Found:** "❌ CON-02: geen authentieke bron/basis in definitietekst"
- **Source Found:** "✔️ CON-02: authentieke bron aangetroffen"

#### Implementation Details
```python
def _has_authentic_source_basis(text: str) -> bool:
    return bool(re.search(
        r"\b(volgens|conform|gebaseerd|bepaald|bedoeld|wet|regeling)\b",
        text, re.IGNORECASE
    ))
```

---

### CON-CIRC-001: Geen circulaire definitie

**Priority:** Medium
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
Prevents circular definitions where the term itself appears literally in the definition text.

#### Validation Logic
- **Check:** Does the term (begrip) appear literally in the definition?
- **Pattern:** `\b{re.escape(begrip)}\b` (case-insensitive word boundary match)
- **Fallback:** Naive contains check with spaces to mimic word boundary

#### Error Handling
- **Circular Found:** "❌ CON-CIRC-001: Definitie is circulair (begrip komt voor in tekst)"
- **Success:** "✔️ CON-CIRC-001: geen circulaire definitie" (score 1.0)

#### Implementation Details
```python
begrip = getattr(self, "_current_begrip", None)
if begrip:
    pattern = rf"\b{re.escape(str(begrip))}\b"
    found = bool(re.search(pattern, text_norm, re.IGNORECASE))
    if not found:
        # Fallback: naive contains check
        tn = f" {text_norm.lower()} "
        gb = f" {str(begrip).strip().lower()} "
        found = gb in tn
    if found:
        return 0.0, violation
return 1.0, None
```

#### Dependencies
- Related to ARAI-06, SAM-05
- Part of baseline internal rules

---

## DUP Category (Duplicate Detection)

### DUP-01: Geen duplicaat definities in database

**Priority:** High
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
Prevents storing identical or very similar definitions for the same term in the database. Improves data quality and prevents inconsistencies during later updates.

#### Validation Logic
- **Exact Match:** Normalized text comparison (lowercase, whitespace collapsed, trailing punctuation removed)
- **Similarity Check:** Jaccard similarity > 90% overlap triggers warning
- **Normalization:**
  ```python
  def _normalize_text(text):
      normalized = text.lower().strip()
      while normalized and normalized[-1] in ".,;:!?":
          normalized = normalized[:-1].strip()
      normalized = " ".join(normalized.split())
      return normalized
  ```
- **Similarity Calculation:** Word-based Jaccard index
  ```python
  def _calculate_similarity(text1, text2):
      words1 = set(text1.split())
      words2 = set(text2.split())
      intersection = words1.intersection(words2)
      union = words1.union(words2)
      return len(intersection) / len(union) if union else 0.0
  ```

#### Error Handling
- **Exact Duplicate:** "Exacte duplicate gevonden (ID: {id})"
- **High Similarity (>90%):** "Zeer vergelijkbare definitie gevonden ({similarity}% overlap, ID: {id})"
- **No Duplicate:** "Geen duplicates gevonden ({count} bestaande definities gecontroleerd)"

#### Dependencies
- Requires: DefinitieRepository.search_definitions()
- Soft-fail: Returns success if repository unavailable

---

## ESS Category (Essentie)

### Purpose
Ensures definitions capture the core meaning, distinguish concepts clearly, and are testable and unambiguous.

---

### ESS-01: Essentie, niet doel

**Priority:** High
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
Ensures definitions describe WHAT something is, not WHY it exists or WHAT it's used for. Focuses on nature and characteristics, not goals or purposes.

#### Validation Logic
- **Forbidden Purpose Patterns:**
  - `om te`, `met als doel`, `bedoeld om`, `bedoeld voor`
  - `teneinde`, `opdat`, `ten behoeve van`, `in het kader van`
  - `zodat`, `gericht op`
- **Good:** "meldpunt: instantie die meldingen registreert over strafbare feiten"
- **Bad:** "meldpunt: instantie om meldingen te kunnen verwerken"

#### Error Handling
- **Purpose Found:** "❌ ESS-01: doelpatroon '{match}' herkend in definitie"
- **Success:** "✔️ ESS-01: geen doelgerichte formuleringen aangetroffen"

---

### ESS-02: Ontologische categorie expliciteren

**Priority:** High
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
**CRITICAL FOR POLYSEMY RESOLUTION**

For terms that can denote multiple ontological categories, the definition must unambiguously indicate which of four is meant:
1. **Type (soort):** Category or class
2. **Particular (exemplaar):** Specific instance
3. **Process (proces/activiteit):** Activity or action
4. **Result (resultaat/uitkomst):** Outcome or product

#### Validation Logic
- **Pattern Sets (per category):**
  - **Type:** `(is een|betreft een) (categorie|soort|klasse)`
  - **Particular:** `(is een) exemplaar`, `specifiek exemplaar`, `particulier geval`
  - **Process:** `(is een|betreft een) (proces|activiteit|handeling|gebeurtenis)`
  - **Result:** `(is het resultaat van)`, `uitkomst`, `effect`, `product`, `resulteert in`
- **Ambiguity Check:** Multiple categories detected → error
- **Missing Check:** No category detected → error

#### Error Handling
- **Ambiguous:** "❌ ESS-02: Ambigu: meerdere categorieën herkend ({categories})"
- **Missing:** "❌ ESS-02: Geen duidelijke ontologische marker (type/particulier/proces/resultaat)"
- **Success:** "✔️ ESS-02: ontologische categorie eenduidig" (score 1.0)

#### Implementation Details
```python
def _eval_ess02(rule, text, ctx):
    # Compile per-category patterns once (cached)
    compiled_map = {
        "type": [re.compile(p, re.IGNORECASE) for p in rule["herkenbaar_patronen_type"]],
        "particulier": [...],
        "proces": [...],
        "resultaat": [...]
    }

    hits = {}
    for cat, pats in compiled_map.items():
        for pat in pats:
            if pat.search(text):
                hits[cat] = hits.get(cat, 0) + 1

    if len(hits) == 1:
        return 1.0, None  # Unambiguous
    if len(hits) > 1:
        return 0.0, ambiguity_violation
    return 0.0, missing_violation
```

#### Dependencies
- Marker override from context: `ctx.metadata.get("marker")`
- Cached compiled patterns for performance

---

### ESS-03: Instanties uniek onderscheidbaar (telbaarheid)

**Priority:** High
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
For countable nouns, definitions must contain criteria for uniquely identifying individual instances (serial number, license plate, VIN, ISBN, document ID) so different experts always arrive at the same count.

#### Validation Logic
- **Unique Identifiers Required:**
  - `serienummer`, `kenteken`, `VIN`, `ISBN`, `document-id`
  - `identificatienummer`, `registratienummer`, `objectnummer`, `inventarisnummer`
  - `uniek(e)`
- **Good:** "Een auto is een vierwielig motorvoertuig met een uniek chassisnummer (VIN) en kenteken"
- **Bad:** "Een auto is een vervoermiddel op vier wielen met een motor"

#### Error Handling
- **Missing:** "❌ ESS-03: Ontbreekt uniek identificatiecriterium"
- **Success:** "✔️ ESS-03: unieke identificatie mogelijk"

---

### ESS-04: Toetsbaarheid

**Priority:** Medium
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
Definitions must contain objectively testable elements (hard deadlines, numbers, percentages, measurable criteria). Without these, readers cannot objectively determine if something falls under the definition.

#### Validation Logic
- **Testable Elements:**
  - Deadlines: `binnen \d+ dagen?`, `uiterlijk na \d+ (dagen?|weken?)`
  - Percentages: `tenminste \d+%`, `minimaal \d+%`, `maximaal \d+%`
  - Criteria: `aan de hand van`, `objectieve criteria`, `controle op`, `waarneembare`, `toetsbaar`
- **Good:** "binnen 3 dagen nadat het verzoek is ingediend"
- **Bad:** "zo snel mogelijk na ontvangst", "zo veel mogelijk resultaten"

#### Error Handling
- **Missing:** "❌ ESS-04: Ontbreekt objectief toetsbaar element"
- **Success:** "✔️ ESS-04: toetsbare elementen aanwezig"

---

### ESS-05: Voldoende onderscheidend

**Priority:** High
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
Definitions must clarify what makes the term unique compared to other related terms in the same domain. Must contain explicit contrast, difference, or unique characteristics.

#### Validation Logic
- **Distinguishing Features:**
  - `onderscheidt zich door`, `specifiek voor`, `in tegenstelling tot`
  - `verschilt van`, `onderscheidend kenmerk`, `uniek kenmerk`
- **Good:** "Een vonnis onderscheidt zich van een arrest doordat het door een rechtbank wordt uitgesproken, niet door een hof"
- **Bad:** "Een vonnis is een beslissing van een rechter"

#### Error Handling
- **Missing:** "❌ ESS-05: Ontbreekt onderscheidend kenmerk"
- **Success:** "✔️ ESS-05: voldoende onderscheidend"

---

### ESS-CONT-001: Essentiële inhoud aanwezig

**Priority:** High
**Recommendation:** Mandatory
**Status:** Baseline Internal

#### Business Purpose
Baseline check for sufficient information density. Prevents overly terse definitions that lack substance.

#### Validation Logic
- **Minimum Words:** 6 words
- **Score Grading:**
  - < 6 words: 0.0 (fail)
  - < 12 words: 0.65 (minimal)
  - ≥ 12 words: 0.9 (pass)

#### Error Handling
- **Failure:** "❌ ESS-CONT-001: Essentiële inhoud ontbreekt of te summier"
- **Success:** "✔️ ESS-CONT-001: voldoende inhoud aanwezig"

#### Dependencies
- Part of baseline internal rules
- Weight: 1.0 (high importance)

---

## INT Category (Intertekstueel)

### Purpose
Ensures internal clarity, comprehensibility, and readability. Prevents complex structures, ambiguity, and inaccessible language.

---

### INT-01: Compacte en begrijpelijke zin

**Priority:** Medium
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
Ensures definitions are compact and formulated in a single clear sentence. Detects complexity indicators: subordinate clauses, enumerations, complex structures.

#### Validation Logic
- **Complexity Indicators:**
  - `,` (comma) - multiple clauses
  - `;` (semicolon) - complex separation
  - Conjunctions: `waarbij`, `welke`, `alsmede`, `indien`, `en`, `maar`, `of`
- **Score Degradation:** `score = max(0.0, 1.0 - (len(complexiteit) * 0.2))`
- **Good:** "proces dat gegevens verzamelt en analyseert"
- **Bad:** "proces waarbij gegevens verzameld worden, welke vervolgens geanalyseerd worden, alsmede..."

#### Error Handling
- **Complexity Found:** "❌ INT-01: complexe elementen gevonden ({elementen})"
- **With Bad Example:** "❌ INT-01: complexe elementen + lijkt op fout voorbeeld" (score 0.0)
- **Success:** "✔️ INT-01: geen complexe elementen herkend" (score 0.9)

---

### INT-02: Geen beslisregel

**Priority:** High
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
Definitions must not contain decision rules or conditional logic ("als...dan", "wanneer...dan"). They should describe what something IS, not under what conditions something applies.

#### Validation Logic
- **Forbidden Patterns:**
  - `\bals\b.*\bdan\b`, `\bwanneer\b.*\bdan\b`, `\bindien\b.*\bdan\b`
  - Conditional structures in definition
- **Good:** "sanctie: maatregel die volgt op normovertreding"
- **Bad:** "sanctie: als er een overtreding is, dan wordt een maatregel opgelegd"

---

### INT-03: Voornaamwoord-verwijzing duidelijk

**Priority:** Medium
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
Pronoun references ("deze", "die", "hij", "zij", "het") must be unambiguous and clearly refer to only one possible antecedent.

#### Validation Logic
- **Forbidden Ambiguous Pronouns:**
  - `\bdeze\b(?! (is|zijn|wordt|betreft))` - "deze" without clear verb
  - `\bdie\b(?! (is|zijn|wordt))` - "die" without clear context
  - `\bhij\b`, `\bzij\b`, `\bhet\b` - personal pronouns in definitions
- **Good:** "proces dat deze stappen uitvoert: ..."
- **Bad:** "proces met stappen die uitgevoerd worden. Deze zijn belangrijk"

---

### INT-04: Lidwoord-verwijzing duidelijk

**Priority:** Medium
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
Article references must be unambiguous, especially when using "de" or "het" to refer back to concepts.

#### Validation Logic
- **Check for ambiguous article use:** Articles must have clear antecedents
- Similar to INT-03 but for articles instead of pronouns

---

### INT-06: Definitie bevat geen toelichting

**Priority:** High
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
Definitions must not contain explanations, examples, or supplementary information. They should be pure definitions. Explanations belong in separate documentation.

#### Validation Logic
- **Forbidden Explanatory Patterns:**
  - `\b(bijvoorbeeld|bijv\.|bv\.|e\.g\.|i\.e\.)\b` - examples
  - `\b(dat wil zeggen|oftewel|met andere woorden)\b` - restatements
  - `\b(zie ook|vergelijk|conform)\b` - references
  - `\(.*\)` - parenthetical explanations (context-dependent)
- **Good:** "sanctie: maatregel die volgt op normovertreding"
- **Bad:** "sanctie: maatregel (bijvoorbeeld taakstraf of boete) die volgt op normovertreding"

---

### INT-07: Alleen toegankelijke afkortingen

**Priority:** Medium
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
Only commonly known abbreviations may be used without explanation. Domain-specific abbreviations must be spelled out or defined separately.

#### Validation Logic
- **Whitelist (allowed):** `NL`, `EU`, `VS`, `UK`, common ISO codes
- **Forbidden (without explanation):**
  - Domain-specific: `DJI`, `KMAR`, `ZM`, `OM` (unless in context field, not definition text)
  - Technical: `HTTP`, `API`, `SQL` (unless defined)
  - Must spell out first use: "Dienst Justitiële Inrichtingen (DJI)"

---

### INT-08: Positieve formulering

**Priority:** Medium
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
Definitions should use positive formulations rather than negative ones ("not", "no", "without"). Positive definitions are clearer and easier to understand.

#### Validation Logic
- **Forbidden Negative Patterns:**
  - `\bniet\b(?! (alleen|enkel))` - "niet" except in "niet alleen"
  - `\bgeen\b`, `\bnoch\b`, `\bnooit\b`
  - `\bzonder\b(?! (dat|welke))` - "zonder" as negation
- **Good:** "maatregel die aanwezig moet zijn bij alle transacties"
- **Bad:** "maatregel die niet mag ontbreken bij transacties"

---

### INT-09: Opsomming in extensionele definitie is limitatief

**Priority:** Medium
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
When a definition uses enumeration (extensional definition), the list must be exhaustive and closed. No "etc.", "en dergelijke", "o.a." allowed.

#### Validation Logic
- **Forbidden Non-Exhaustive Markers:**
  - `\bet cetera\b`, `\betc\.?\b`, `\ben dergelijke\b`
  - `\bo\.a\.?\b`, `\bonder andere\b`, `\bonder meer\b`
  - `\bvoor(al)? zoals\b`, `\bzeer(maal)?\\b.*zoals\b`
- **Good:** "kleuren: rood, groen of blauw" (closed list)
- **Bad:** "kleuren: rood, groen, blauw, etc." (open list)

---

### INT-10: Geen ontoegankelijke achtergrondkennis nodig

**Priority:** Medium
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
Definitions must be understandable without inaccessible domain knowledge. Avoid jargon, insider terms, or references to obscure concepts.

#### Validation Logic
- **Check for:**
  - Unexplained jargon
  - References to internal systems without context
  - Specialized terminology without definition
- **Related to:** ARAI-05 (implicit assumptions)

---

## SAM Category (Samenhang)

### Purpose
Ensures coherence and proper relationships between terms, qualifications, and definitions. Prevents contradictions and semantic drift.

---

### SAM-01: Kwalificatie leidt niet tot afwijking

**Priority:** Medium
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
Qualifications ("technical", "legal", "operational") must not lead to meanings that deviate from the generally accepted concept. Qualified terms should remain consistent with base meaning.

#### Validation Logic
- **Qualification Patterns:** `technisch`, `juridisch`, `operationeel`, `formeel`, `materieel`
- **Check:** Does qualification maintain semantic consistency?
- **Good:** "technisch delict: delict dat technische expertise vereist voor opsporing" (consistent)
- **Bad:** "technisch delict: handeling die technisch geoorloofd is maar juridisch strafbaar" (conflicting)

#### Error Handling
- **Bad Example Match:** "❌ SAM-01: kwalificatie leidt tot misleidende betekenisafwijking"
- **Qualification Found (no example):** "🟡 SAM-01: kwalificatie(s) gevonden ({list}), controleer consistentie" (score 0.5)
- **Success:** "✔️ SAM-01: geen misleidende kwalificaties"

---

### SAM-02: Kwalificatie omvat geen herhaling

**Priority:** High
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
**FOR QUALIFIED TERMS (e.g., "strafbaar delict")**

The definition must NOT repeat the base definition of the head term. Use genus+differentia: mention the head term briefly and add only the distinguishing criterion.

#### Validation Logic
- **Extract Head Term:** Last word of multi-word begrip (e.g., "delict" from "strafbaar delict")
- **Check 1:** Definition must not start with base term definition
  - Bad: "delict: ..." (defines base term, not qualified term)
- **Check 2:** Definition must not contain known base definition phrases
  - Bad: "delict binnen de grenzen van wettelijke strafbepaling" (repeats base definition)
- **Good:** "delict waarvoor straf kan worden opgelegd" (genus+differentia)

#### Implementation Details
```python
begrip_full = (getattr(self, "_current_begrip", "") or "").strip().lower()
parts = begrip_full.split()
if len(parts) >= 2:
    head = parts[-1]  # Last word is head term

    # Check 1: Definition starts with "head:"
    if text_l.startswith(f"{head}:"):
        return 0.0, violation("defines base term instead of qualified term")

    # Check 2: Heuristic detection of base definition repetition
    if head in text_l and ("binnen de grenzen van" in text_l or "wettelijke strafbepaling" in text_l):
        return 0.0, violation("contains parts of base definition")
```

---

### SAM-03: Definitieteksten niet nesten

**Priority:** Medium
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
Definitions must not nest other complete definitions within them. Each term should have its own separate definition.

#### Validation Logic
- **Forbidden:** "A: een X dat Y (waarbij Y: een Z is die...)" - nested definition
- **Good:** "A: een X dat Y heeft" + separate "Y: een Z die..."

---

### SAM-04: Begrip-samenstelling strijdt niet met samenstellende begrippen

**Priority:** High
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
**FOR COMPOUND TERMS (e.g., "procesmodel")**

The definition must start with the specializing component (genus) from the composition. For "procesmodel", should start with "model..." not "proces...".

#### Validation Logic
- **Extract First Token:** First word after `:` in definition
- **Check Compound:** If begrip is one word (no spaces), first token should be substring of begrip
- **Example:** "procesmodel: model van een proces" ✓
- **Bad:** "procesmodel: proces dat gemodelleerd is" ✗

#### Implementation Details
```python
begrip_full = (getattr(self, "_current_begrip", "") or "").strip().lower()
# Extract first word after ':'
first_token = text.split(":", 1)[1].strip().split()[0]

if " " not in begrip_full:  # Compound without space
    if first_token not in begrip_full:
        return 0.0, violation("does not start with specializing component")
```

---

### SAM-05: Geen cirkeldefinities

**Priority:** High
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
Prevents circular definitions where terms define each other in a loop (A defines B, B defines A). Also prevents self-reference.

#### Validation Logic
- **Direct Circularity:** Term appears in its own definition (handled by CON-CIRC-001)
- **Indirect Circularity:** A → B → A requires graph analysis of all definitions
- **Implementation:** Requires dependency graph of all terms (not implemented in single-rule validation)

---

### SAM-06: Één synoniem krijgt voorkeur

**Priority:** Medium
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
When synonyms exist, one should be designated as preferred term. All others should reference the preferred term.

#### Validation Logic
- **Metadata Check:** `ctx.metadata.get("is_preferred_term")`
- **If synonym:** Definition should state "Zie {preferred_term}" or similar
- **Implementation:** Requires synonym registry

---

### SAM-07: Geen betekenisverruiming binnen definitie

**Priority:** Medium
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
A definition must not broaden the meaning of a term beyond its established scope. Prevents semantic drift.

#### Validation Logic
- **Check for broadening phrases:**
  - `\b(en al het andere)\b`, `\b(en verder)\b`, `\b(en soortgelijke)\b`
  - `\b(ruimer gezien)\b`, `\b(in brede zin)\b`
- **Good:** "sanctie: maatregel die volgt op normovertreding"
- **Bad:** "sanctie: maatregel en al het andere dat gericht is op gedragsbeïnvloeding"

---

### SAM-08: Synoniemen hebben één definitie

**Priority:** High
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
Synonyms should share one definition, not have separate conflicting definitions. Ensures consistency.

#### Validation Logic
- **Database Check:** Query for synonyms of current term
- **Compare:** If synonyms exist with different definitions → warning
- **Enforcement:** During storage, link synonyms to single canonical definition

---

## STR Category (Structuur)

### Purpose
Ensures correct structural formatting of definitions: noun starts, no articles, no synonyms as definitions, proper follow-up.

---

### STR-01: Definitie start met zelfstandig naamwoord

**Priority:** High
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
Definitions must start with a noun (or noun phrase), not with a verb, article, or copula. Ensures definitions are reusable in different contexts.

#### Validation Logic
- **Forbidden Starts:**
  - `^\s*(is|wordt|betreft|omvat|betekent)\b` - starts with verb
  - `^\s*(de|het|een)\b` - starts with article
- **Check Body (after `:`):** First word after colon should be noun
- **Good:** "proces: reeks stappen..."
- **Bad:** "proces: is een reeks stappen...", "proces: de uitvoering van..."

#### Implementation Details
```python
body = text.strip()
if ":" in body:
    body = body.split(":", 1)[1].lstrip()
if re.match(r"^(is|de|het|een|wordt|betreft)\b", body, re.IGNORECASE):
    return 0.0, violation("starts with article or auxiliary verb")
```

---

### STR-02: Kick-off ≠ de term

**Priority:** High
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
The start (kick-off) of the definition must not be the term itself. Prevents tautology and circular structure.

#### Validation Logic
- **Check:** First significant word in definition should NOT be the term being defined
- **Related to:** CON-CIRC-001, ARAI-06

---

### STR-03: Definitie ≠ synoniem

**Priority:** High
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
A definition must not simply be a synonym without further explanation. "X: Y" where Y is a synonym is insufficient.

#### Validation Logic
- **Forbidden:** Single-word definitions that are known synonyms
- **Minimum:** Must add differentia or explanation beyond synonym
- **Good:** "gedetineerde: persoon die in detentie verblijft op grond van rechterlijke beslissing"
- **Bad:** "gedetineerde: gevangene" (synonym only)

---

### STR-04: Kick-off vervolgen met toespitsing

**Priority:** High
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
After the initial genus (kick-off noun), the definition must immediately follow with differentiation (differentia). No vague continuations.

#### Validation Logic
- **Structure Required:** `[genus] [die/dat/waarbij] [differentiating characteristic]`
- **Forbidden:** `[genus] [general description without specifics]`
- **Good:** "proces dat gegevens verwerkt voor analyse"
- **Bad:** "proces met diverse stappen"

---

### STR-05: Definitie ≠ constructie

**Priority:** Medium
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
A definition must not describe the construction or composition ("built from", "constructed with") but the concept itself.

#### Validation Logic
- **Forbidden Patterns:**
  - `\bsamengesteld uit\b`, `\bgebouwd met\b`, `\bconstrueerd van\b`
  - `\bbestaat uit\b` (when primary description)
- **Good:** "gebouw: constructie die beschutting biedt" (what it IS)
- **Bad:** "gebouw: constructie samengesteld uit muren en dak" (HOW it's built)

---

### STR-06: Essentie ≠ informatiebehoefte

**Priority:** Medium
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
A definition describes the essence of a concept, not the information needs about it. Don't confuse the concept with data/attributes about it.

#### Validation Logic
- **Forbidden:**
  - "X: informatie over Y"
  - "X: gegevens betreffende Y"
- **Good:** "persoon: natuurlijk individu met rechten en plichten"
- **Bad:** "persoon: gegevens over een natuurlijk individu" (describes data, not person)

---

### STR-07: Geen dubbele ontkenning

**Priority:** Medium
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
Double negatives create confusion. Use positive formulations.

#### Validation Logic
- **Forbidden:** `\bniet\b.*\bniet\b`, `\bniet\b.*\bgeen\b`, `\bgeen\b.*\bniet\b`
- **Good:** "maatregel die altijd aanwezig is"
- **Bad:** "maatregel die niet kan ontbreken" (double negative: not can not-be-present)

---

### STR-08: Dubbelzinnige 'en' is verboden

**Priority:** Medium
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
Ambiguous "and" (conjunctive/disjunctive ambiguity) must be avoided. Make clear if ALL criteria or ANY criterion is required.

#### Validation Logic
- **Check for:** Multiple "en" in criteria list without clear scope
- **Ambiguous:** "X die A en B of C" (unclear: (A and B) or C? or A and (B or C)?)
- **Clear:** "X die (A en B) of C", "X die A en (B of C)"

---

### STR-09: Dubbelzinnige 'of' is verboden

**Priority:** Medium
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
Ambiguous "or" must be avoided. Make clear if alternatives are mutually exclusive or inclusive.

#### Validation Logic
- **Check for:** Multiple "of" without clear scope or parentheses
- **Ambiguous:** "X die A of B of C" (unclear: exactly one? at least one?)
- **Clear:** "X die één van: A, B of C" (exclusive), "X die A, B of C" (inclusive with comma)

---

### STR-ORG-001: Zinsstructuur en redundantie

**Priority:** Medium
**Recommendation:** Recommended
**Status:** Baseline Internal

#### Business Purpose
Detects weak sentence structure or redundancy: overly long sentences with many commas, or contradictory phrasing.

#### Validation Logic
- **Long Run-on Sentence:** `chars > 300 AND commas >= 6`
- **Redundancy:** `\bsimpel\b.*\bcomplex\b|\bcomplex\b.*\bsimpel\b` (contradictory)
- **Score:** 0.9 (pass) | 0.0 (fail)

#### Implementation Details
```python
long_sentence = chars > 300 and text_norm.count(",") >= 6
redundancy = bool(re.search(
    r"\bsimpel\b.*\bcomplex\b|\bcomplex\b.*\bsimpel\b",
    text_norm, re.IGNORECASE
))
if long_sentence or redundancy:
    return 0.0, violation
```

---

### STR-TERM-001: Consistente terminologie (koppelteken)

**Priority:** Low
**Recommendation:** Recommended
**Status:** Baseline Internal

#### Business Purpose
Ensures consistent terminology usage, specifically hyphenation in compound terms (e.g., "HTTP-protocol" not "HTTP protocol").

#### Validation Logic
- **Check:** Known terms requiring hyphens
- **Example:** `HTTP protocol` → should be `HTTP-protocol`
- **Score:** 0.95 (pass) | 0.0 (fail for missing hyphen)

---

## VAL Category (Validatie)

### Purpose
Basic validation checks: empty text, minimum/maximum length. Baseline quality gates.

---

### VAL-EMP-001: Lege definitie is ongeldig

**Priority:** High
**Recommendation:** Mandatory
**Status:** Baseline Internal

#### Business Purpose
CRITICAL BASELINE CHECK: Definition text cannot be empty.

#### Validation Logic
- **Check:** `len(cleaned_text.strip()) == 0`
- **Score:** 0.0 (empty) | 0.9 (non-empty)

#### Error Handling
- **Empty:** "❌ VAL-EMP-001: Definitietekst is leeg"
- **Non-empty:** "✔️ VAL-EMP-001: tekst aanwezig"

#### Dependencies
- Weight: 1.0 (critical)
- Excluded from scoring (weight set to 0.0 in ModularValidationService)

---

### VAL-LEN-001: Minimale lengte (woorden/tekens)

**Priority:** High
**Recommendation:** Mandatory
**Status:** Baseline Internal

#### Business Purpose
Ensures definition has minimum substance: at least 5 words and 15 characters.

#### Validation Logic
- **Minimum:** 5 words AND 15 characters
- **Score Grading:**
  - < 5 words OR < 15 chars: 0.0 (fail)
  - < 12 words OR < 40 chars: 0.7 (short but acceptable)
  - < 25 words: 0.85 (good)
  - ≥ 25 words: 0.9 (very good)

#### Error Handling
- **Too Short:** "❌ VAL-LEN-001: Definitie is te kort"
- **Pass:** "✔️ VAL-LEN-001: voldoende lengte"

#### Dependencies
- Weight: 0.9
- Excluded from scoring (weight set to 0.0)

---

### VAL-LEN-002: Maximale lengte (woorden/tekens)

**Priority:** Low
**Recommendation:** Recommended
**Status:** Baseline Internal

#### Business Purpose
Prevents overly verbose definitions: maximum 80 words and 600 characters.

#### Validation Logic
- **Maximum:** 80 words AND 600 characters
- **Score Grading:**
  - > 80 words OR > 600 chars: 0.0 (fail - too long)
  - > 60 words OR > 450 chars: 0.85 (approaching limit)
  - ≤ 60 words: 0.95 (good length)

#### Error Handling
- **Too Long:** "❌ VAL-LEN-002: Definitie is te lang/overdadig"
- **Pass:** "✔️ VAL-LEN-002: binnen max lengte"

#### Dependencies
- Weight: 0.6
- Excluded from scoring (weight set to 0.0)

---

## VER Category (Verduidelijking)

### Purpose
Clarification rules: singular form, infinitive for verb terms.

---

### VER-01: Term in enkelvoud

**Priority:** High
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
Terms (lemmas) must be in singular form, except for "pluralia tantum" (nouns that only exist in plural, like "kosten", "hersenen").

#### Validation Logic
- **Plurale Tantum Whitelist:** `kosten`, `hersenen`, (extendable)
- **Heuristic:** Dutch plurals often end with `en` or `ens`
  - `\w+ens$` - likely plural (e.g., "gegevens" from "gegeven")
  - `\w+en$` - likely plural
- **Check:** If not in whitelist and matches plural pattern → fail

#### Implementation Details
```python
def _lemma_is_singular(begrip: str) -> bool:
    lemma = (begrip or "").strip().lower()
    plurale_tantum = {"kosten", "hersenen"}
    if lemma in plurale_tantum:
        return True
    if re.search(r"\w+ens$", lemma):
        return False  # Plural like "gegevens"
    return not bool(re.search(r"\w+en$", lemma))
```

#### Error Handling
- **Plural:** "❌ VER-01: Term (lemma) lijkt meervoud (geen plurale tantum)"
- **Singular:** "✔️ VER-01: term in enkelvoud"

---

### VER-02: Definitie in enkelvoud

**Priority:** Medium
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
The definition text itself should use singular forms, not plural, to maintain consistency with the singular term.

#### Validation Logic
- **Check definition text:** Should not use plural forms when singular term is defined
- **Example:** For "persoon", definition should use "persoon die..." not "personen die..."

---

### VER-03: Werkwoord-term in infinitief

**Priority:** Medium
**Recommendation:** Mandatory
**Status:** Definitive

#### Business Purpose
When the term itself is a verb (verb-term), it must be in infinitive form, not conjugated.

#### Validation Logic
- **Check Lemma:** If lemma is a verb (ends with verb patterns):
  - Conjugated forms end with `-t` or `-d` (e.g., "beoordeelt", "beoordeeld")
  - Infinitive forms end with `-en` (e.g., "beoordelen")
- **Pattern:** `r".+[td]$"` - likely conjugated if ends with t/d
- **Good:** "beoordelen: het proces van..."
- **Bad:** "beoordeelt: het proces van..." (conjugated)

#### Implementation Details
```python
lemma = str(getattr(self, "_current_begrip", "") or "").strip()
if lemma and re.search(r".+[td]$", lemma.lower()):
    return 0.0, violation("Werkwoord-term niet in infinitief")
return 1.0, None
```

#### Error Handling
- **Conjugated:** "❌ VER-03: Werkwoord-term niet in infinitief (eindigt op -t/-d)"
- **Suggestion:** "Gebruik de onbepaalde wijs (infinitief), bijv. 'beoordelen' i.p.v. 'beoordeelt'"

---

## Validation Orchestration

### ValidationOrchestratorV2

**Location:** `src/services/validation/validation_orchestrator_v2.py`
**Purpose:** Central orchestration service coordinating validation flow

#### Responsibilities
1. **Service Container Integration**
   - Retrieves ModularValidationService from DI container
   - Manages service lifecycle and dependencies

2. **Validation Flow**
   ```python
   async def validate_definition(begrip, text, context):
       # 1. Validate inputs
       # 2. Call ModularValidationService.validate_definition()
       # 3. Transform result to UI-friendly format
       # 4. Apply approval gate policy (EPIC-016)
       # 5. Return structured ValidationResult
   ```

3. **Result Transformation**
   - Maps internal validation schema to UI expectations
   - Adds user-friendly messages
   - Formats violations for display

4. **Error Handling**
   - Graceful degradation on service failures
   - Logs validation errors
   - Returns partial results when possible

---

### ModularValidationService

**Location:** `src/services/validation/modular_validation_service.py`
**Purpose:** Core validation engine executing all rules

#### Responsibilities

1. **Rule Loading**
   ```python
   def _load_rules_from_manager():
       all_rules = toetsregel_manager.get_all_regels()
       _internal_rules = list(all_rules.keys())  # All 53 rules
       _default_weights = {rule_id: _calculate_rule_weight(rule_data) for ...}
   ```

2. **Validation Execution**
   ```python
   async def validate_definition(begrip, text, context):
       # 1. Clean text (optional via cleaning_service)
       # 2. Build EvaluationContext
       # 3. Evaluate rules in deterministic order (sorted by code)
       # 4. Collect violations and scores
       # 5. Calculate weighted aggregate score
       # 6. Apply quality band scaling (length-based)
       # 7. Calculate category scores
       # 8. Evaluate acceptance gates
       # 9. Return ValidationResult dict
   ```

3. **Rule Evaluation**
   - **Baseline Internal Rules:** 7 rules (VAL-*, STR-*, ESS-CONT-001, CON-CIRC-001)
     - Hardcoded in service for safeguards
     - Evaluated via `_evaluate_rule()` method
   - **JSON-Defined Rules:** 53 rules (all categories)
     - Loaded from JSON configs
     - Evaluated via `_evaluate_json_rule()` method
     - Pattern matching, numeric constraints, special-case logic

4. **Scoring & Aggregation**
   ```python
   # Weighted score calculation
   overall_score = calculate_weighted_score(rule_scores, weights)

   # Quality band scaling (length-based penalty/bonus)
   if wcount < 12: scale = 0.75
   elif wcount < 20: scale = 0.9
   elif wcount > 100: scale = 0.85
   elif wcount > 60: scale = 0.9
   else: scale = 1.0
   overall_score = round(overall_score * scale, 2)

   # Category scores (by rule prefix)
   detailed_scores = {
       "taal": avg([scores for rule in ARAI/VER]),
       "juridisch": avg([scores for rule in ESS/VAL]),
       "structuur": avg([scores for rule in STR/INT]),
       "samenhang": avg([scores for rule in CON/SAM])
   }
   ```

5. **Acceptance Gates**
   ```python
   def _evaluate_acceptance_gates(overall, detailed, violations):
       gates_passed = []
       gates_failed = []

       # Critical violations check
       if no_critical_violations:
           gates_passed.append("no_critical_violations")

       # Overall threshold check
       if overall >= overall_threshold:
           gates_passed.append("overall>=0.75")

       # Category thresholds check
       for category in ["taal", "juridisch", "structuur", "samenhang"]:
           if detailed[category] < category_threshold:
               gates_failed.append(f"{category}<0.70")

       return {
           "acceptable": len(gates_failed) == 0,
           "gates_passed": gates_passed,
           "gates_failed": gates_failed
       }
   ```

6. **Soft Acceptance Floor**
   ```python
   # Less strict acceptance: soft floor at 0.65 if no blocking errors
   def _has_blocking_errors(violations):
       for v in violations:
           if v["severity"] == "error":
               code = v["code"]
               if code.startswith(("VAL-EMP", "CON-CIRC", "VAL-LEN-002", "LANG-", "STR-FORM-001")):
                   return True
       return False

   soft_ok = (overall >= 0.65) and (not _has_blocking_errors(violations))
   is_acceptable = acceptance_gate["acceptable"] or soft_ok
   ```

---

### ApprovalGatePolicy (EPIC-016)

**Location:** `src/services/validation/approval_gate_policy.py` (implied)
**Purpose:** Central policy for validation gates at "Vaststellen" (approval) step

#### Responsibilities

1. **Gate Configuration**
   - **Overall Threshold:** 0.75 (configurable via `config.thresholds.overall_accept`)
   - **Category Threshold:** 0.70 (configurable via `config.thresholds.category_accept`)
   - **Mode:** Strict / Lenient (future: UI-manageable)

2. **Required Fields Enforcement**
   - Ensures critical fields populated before approval
   - Checks context fields (organizational, legal, legislative)
   - Validates mandatory metadata

3. **Gate Evaluation**
   - Coordinates with ModularValidationService acceptance_gate result
   - Applies business rules for "Vaststellen" transition
   - Blocks approval if gates not passed

4. **Auditability**
   - All gate decisions logged
   - Configuration changes tracked
   - UI-visible gate status

---

### Aggregation Logic

**Location:** `src/services/validation/aggregation.py`
**Purpose:** Calculates weighted scores and determines acceptability

#### Key Functions

1. **calculate_weighted_score(rule_scores, weights)**
   ```python
   def calculate_weighted_score(scores: dict, weights: dict) -> float:
       weighted_sum = 0.0
       total_weight = 0.0
       for rule_id, score in scores.items():
           weight = weights.get(rule_id, 0.5)
           if weight > 0:
               weighted_sum += score * weight
               total_weight += weight
       return weighted_sum / total_weight if total_weight > 0 else 0.0
   ```

2. **determine_acceptability(score, threshold)**
   ```python
   def determine_acceptability(score: float, threshold: float) -> bool:
       return score >= threshold
   ```

3. **Weight Assignment**
   - **Priority-Based Weights:**
     - High priority: 1.0
     - Medium priority: 0.7
     - Low priority: 0.4
   - **Explicit Weights:** Some rules have explicit weights in JSON config
   - **Zero Weights (excluded from scoring):**
     - Baseline internal rules (VAL-*, STR-TERM-001, STR-ORG-001)
     - ARAI family (language-focused rules)

---

## Rule Dependencies & Relationships

### Composite Rules
- **ARAI-06** → Combines: STR-01, STR-02, SAM-05

### Parent-Child Rules
- **ARAI-02** → Sub-rules: ARAI-02SUB1, ARAI-02SUB2
- **ARAI-04** → Sub-rule: ARAI-04SUB1

### Related Rules (Conceptual)
- **ARAI-05** ↔ **INT-10** (implicit assumptions vs. inaccessible knowledge)
- **CON-CIRC-001** ↔ **SAM-05** (circular definitions)
- **ARAI-06** ↔ **STR-01** (noun start)
- **INT-01** ↔ **INT-06** (complexity vs. explanations)

### Category Overlaps
- **ESS-01** (essence not goal) ↔ **INT-06** (no explanations)
- **STR-06** (essence ≠ information need) ↔ **ESS-01** (essence not goal)

---

## Business Logic Summary by Theme

### 1. **Linguistic Quality (ARAI category)**
- Prevents vague language (container terms, adjectives, modals)
- Ensures noun-based definitions (not verb-based)
- Avoids implicit assumptions

### 2. **Context Management (CON category)**
- Context must be implicit, not explicit
- Duplicate detection on term + context + synonyms
- Requires authentic source basis

### 3. **Semantic Precision (ESS category)**
- Distinguishes ontological categories (type/particular/process/result)
- Requires testable elements and distinguishing features
- Ensures unique identification for countable terms

### 4. **Structural Integrity (STR category)**
- Definitions start with noun
- No articles, copulas, or self-reference at start
- Genus + differentia structure enforced

### 5. **Clarity & Comprehensibility (INT category)**
- Single sentence, compact structure
- No decision rules or explanations in definition
- Clear pronoun/article references

### 6. **Coherence (SAM category)**
- Qualifications maintain semantic consistency
- No repetition of base definitions in qualified terms
- Compound terms start with specializing component

### 7. **Basic Validation (VAL category)**
- Non-empty text
- Minimum/maximum length bounds
- Quality gates for approval

### 8. **Clarification (VER category)**
- Terms in singular form (except pluralia tantum)
- Verb terms in infinitive

---

## Critical Integration Points

### 1. **ToetsregelManager**
- Loads all 53 JSON rule definitions
- Provides `get_all_regels()` method
- Maps rule IDs to rule data

### 2. **DefinitieRepository**
- Used by CON-01 for duplicate detection
- Provides `count_exact_by_context()` method
- Enables cross-definition validation (SAM rules)

### 3. **CleaningService**
- Optional text cleaning before validation
- Normalizes whitespace, removes artifacts
- Used by ModularValidationService

### 4. **ServiceContainer (DI)**
- Manages service dependencies
- Injects ToetsregelManager, CleaningService, Config, Repository
- Ensures singleton pattern for validation service

### 5. **EPIC-016 Integration**
- ApprovalGatePolicy coordinates with validation results
- UI-manageable thresholds and required fields
- Auditability of validation decisions

---

## Performance Considerations

### 1. **Pattern Compilation**
- Regex patterns compiled once and cached
- Per-rule cache: `_compiled_json_cache`
- Per-category cache for ESS-02: `_compiled_ess02_cache`

### 2. **Deterministic Evaluation**
- Rules evaluated in sorted order (by code)
- Guarantees consistent results across runs
- Testable and reproducible

### 3. **Lazy Initialization**
- Repository initialized on first use (DUP-01)
- Avoids circular import issues
- Soft-fail on missing dependencies

### 4. **Batch Validation**
- `batch_validate()` method supports parallel execution
- Semaphore-based concurrency control
- Default: sequential (max_concurrency=1)

---

## Error Handling Philosophy

### 1. **Graceful Degradation**
- Missing services → skip optional checks
- Invalid patterns → log warning, continue
- Soft-fail on non-critical errors

### 2. **User-Friendly Messages**
- Emoji indicators: ✔️ (pass), ❌ (fail), 🟡 (warning)
- Dutch language messages
- Actionable suggestions in violation objects

### 3. **Structured Violations**
```python
violation = {
    "code": "RULE-ID",
    "severity": "error" | "warning",
    "severity_level": "critical" | "high" | "medium" | "low",
    "message": "User-friendly description",
    "description": "Same as message for consistency",
    "rule_id": "RULE-ID",
    "category": "taal" | "juridisch" | "structuur" | "samenhang",
    "suggestion": "Actionable fix suggestion",
    "metadata": {  # Optional
        "detected_pattern": "regex pattern that matched",
        "position": 42  # Character position in text
    }
}
```

---

## Test Coverage Insights

### High-Coverage Modules
1. **ModularValidationService:** Core validation logic
   - Deterministic rule evaluation
   - Weighted scoring
   - Acceptance gates

2. **DefinitionValidator (legacy):** 98% coverage
   - Individual rule implementations
   - Pattern matching

3. **DefinitieRepository:** 100% coverage
   - Duplicate detection
   - Context matching

### Test Categories
- **Unit Tests:** Individual rule validation
- **Integration Tests:** Full validation flow
- **Smoke Tests:** Basic functionality checks
- **Golden Tests:** Known good/bad examples

---

## Future Enhancement Opportunities

### 1. **Rule Extensibility**
- Plugin architecture for custom rules
- External rule repositories
- Dynamic rule loading

### 2. **Machine Learning Integration**
- Learn from user corrections
- Suggest rule weight adjustments
- Detect new anti-patterns

### 3. **Performance Optimization**
- Parallel rule evaluation (with dependency graph)
- Incremental validation (only changed parts)
- Cached validation results

### 4. **UI Enhancements**
- Interactive rule toggling
- Per-rule documentation inline
- Validation preview during editing

### 5. **Advanced Analytics**
- Rule effectiveness metrics
- Common violation patterns
- Quality trend analysis

---

## Documentation References

### Primary Sources
- **ASTRA Online:** https://www.astraonline.nl/ - Dutch legal definition standards
- **CLAUDE.md:** Project-specific guidelines
- **UNIFIED_INSTRUCTIONS.md:** Cross-project standards

### Implementation Files
- `src/services/validation/modular_validation_service.py` (1639 lines)
- `src/services/validation/validation_orchestrator_v2.py`
- `src/toetsregels/regels/*.py` (46 validators)
- `src/toetsregels/regels/*.json` (53 rule definitions)

### Related Documentation
- `docs/architectuur/validation_orchestrator_v2.md`
- `docs/testing/validation_orchestrator_testplan.md`
- `docs/architectuur/SOLUTION_ARCHITECTURE.md`

---

## Extraction Completeness Checklist

- [x] All 53 rules documented with business purpose
- [x] Validation logic detailed for each rule
- [x] Error handling patterns captured
- [x] Dependencies and relationships mapped
- [x] Orchestration architecture explained
- [x] Scoring and aggregation logic documented
- [x] Integration points identified
- [x] Performance considerations noted
- [x] Test coverage insights included
- [x] Future enhancement opportunities listed

---

**END OF VALIDATION RULES EXTRACTION**

*This document serves as the comprehensive source of truth for validation rule business logic during the rebuild process.*
