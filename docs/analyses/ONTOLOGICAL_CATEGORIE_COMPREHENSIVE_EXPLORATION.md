# Ontologische Categorie Implementation - Comprehensive Exploration

**Date**: 2025-11-03  
**Status**: Complete Investigation  
**Scope**: Very Thorough Deep Dive  

---

## Executive Summary

The **ontologische_categorie** (ontological category) feature is **extensively implemented** throughout DefinitieAgent, spanning:

- ✅ **Domain Models**: Two systems (TYPE/PROCES/RESULTAAT/EXEMPLAAR) AND (U/F/O classification)
- ✅ **Validation**: ESS-02 rule fully implemented with regex pattern matching
- ✅ **Data Flow**: Category flows through entire generation pipeline
- ✅ **Prompt Integration**: Used for template selection and context hints
- ✅ **Database**: Stored and retrieved properly
- ❌ **UI Widget**: No user-facing category selector found
- ❌ **Blocking Behavior**: Validation runs but doesn't prevent generation
- ❓ **DEF-39/DEF-13 Status**: Requirements not located; implementation status unclear

---

## 1. TWO Ontological Category Systems

### 1.1 System A: TYPE/PROCES/RESULTAAT/EXEMPLAAR

**Type**: 4-category classification for juridische definitions  
**Location**: `/src/domain/ontological_categories.py`

```python
class OntologischeCategorie(Enum):
    """Ontologische categorieën (van generation implementatie)."""
    TYPE = "type"              # Soort/klasse begrip
    PROCES = "proces"          # Activiteit/handeling
    RESULTAAT = "resultaat"    # Uitkomst/bevinding
    EXEMPLAAR = "exemplaar"    # Specifiek geval
```

**Usage Context**:
- GenerationRequest.ontologische_categorie field
- Prompt template selection
- Definition validation (ESS-02 rule)
- Database storage

**Database Field Name**: `categorie` (not `ontologische_categorie`)  
**Mapping**: Done in `definition_orchestrator_v2.py` (DEF-53 fix)

### 1.2 System B: U/F/O Classification (UNIVERSEEL/FUNCTIONEEL/OPERATIONEEL)

**Type**: 3-level ontological classification  
**Location**: `/src/services/classification/ontological_classifier.py`

```python
class OntologicalLevel(Enum):
    """Ontologische niveaus voor juridische begrippen."""
    UNIVERSEEL = "U"       # Universal concepts (Persoon, Datum)
    FUNCTIONEEL = "F"      # Functional/domain-specific (Overeenkomst)
    OPERATIONEEL = "O"     # Organization-specific (Aanvraag vergunning X)
```

**Purpose**: AI-based classification BEFORE definition generation  
**Not** for naming the database field; separate from System A

**Key Insight**: These are TWO DIFFERENT systems serving different purposes!

---

## 2. Domain Model & Data Structures

### 2.1 GenerationRequest Interface

**File**: `/src/services/interfaces.py` (lines 147-200+)

```python
@dataclass
class GenerationRequest:
    """Request object voor het genereren van een definitie."""
    id: str
    begrip: str
    ontologische_categorie: str | None = None    # ← The field
    organisatorische_context: list[str] | None = None
    juridische_context: list[str] | None = None
    wettelijke_basis: list[str] | None = None
    context: str | None = None
    actor: str = "system"
    legal_basis: str = "legitimate_interest"
```

**Critical Note**: Field is **OPTIONAL** (nullable)  
This is key to understanding why DEF-39 (if it requires blocking) is not fully implemented.

### 2.2 Definition Domain Object

**File**: `/src/services/interfaces.py` (Definition interface)

**Fields**:
- `categorie`: String field matching database schema
- `ontologische_categorie`: Property or derived from `categorie`

**Storage Path**: Database `categorie` column

---

## 3. Validation Rule: ESS-02

### 3.1 Rule Metadata

**File**: `/src/toetsregels/regels/ESS-02.json`

```json
{
  "id": "ESS_02",
  "naam": "Ontologische categorie expliciteren (type / particulier / proces / resultaat)",
  "uitleg": "Indien een begrip meerdere ontologische categorieën kan aanduiden, 
            moet uit de definitie ondubbelzinnig blijken welke van deze vier bedoeld wordt",
  "prioriteit": "hoog",
  "aanbeveling": "verplicht",  ← MARKED AS MANDATORY
  "type": "polysemie"
}
```

**Recognition Patterns**:
- Type: `"is een categorie", "soort", "klasse"`
- Particulier: `"exemplaar", "specifiek exemplaar"`
- Proces: `"proces", "activiteit", "handeling"`
- Resultaat: `"is het resultaat van", "uitkomst"`

### 3.2 Validator Implementation

**File**: `/src/toetsregels/regels/ESS-02.py`

**Logic Flow**:
1. Check metadata override (marker field in context)
2. Apply regex patterns for category detection
3. Count detected categories (0, 1, 2+)
4. Return pass/fail based on count:
   - 0 detected: FAIL (insufficient clarity)
   - 1 detected: PASS ✓
   - 2+ detected: FAIL (ambiguous)

**Score Calculation**:
- Pass: 1.0
- Fail: 0.0

### 3.3 CRITICAL FINDING: NOT BLOCKING

**Current Behavior**:
```
ESS-02 violation detected
  ↓
Recorded in validation_details.violations[]
  ↓
Counted in overall score calculation
  ↓
Definition saved ANYWAY (success=True)
```

**Validation Results Type**: `ValidationDetailsDict` (V2 contract)
```python
class ValidationDetailsDict(TypedDict):
    overall_score: float    # 0.0-1.0 (ESS-02 fail lowers this)
    is_acceptable: bool     # True if score >= 0.6 (not definition-blocking)
    violations: list[...]   # ESS-02 listed here
    passed_rules: list[...]
```

**Acceptance Logic**: Definition acceptable if:
- Score >= 0.6 (60%)
- No CRITICAL severity violations
- ESS-02 = MEDIUM or LOW severity (not CRITICAL)

**⚠️ IMPLICATION**: Even with ESS-02 failure, definition is marked `is_acceptable=True` and saved.

---

## 4. Data Flow: Complete Journey

### 4.1 UI Input Phase

**Missing Component**: No user UI widget for category selection found!

**Inferred Flow**:
1. User enters term (begrip) in definition_generator_tab
2. User selects context (org/jur/wet) via enhanced_context_manager_selector
3. GenerationRequest created from form inputs
4. `ontologische_categorie` field: **WHERE IS THIS SET?**

**Possible Sources**:
- Default value (need to find where)
- AI classification via OntologicalClassifier
- External API call
- Backend-provided hint

### 4.2 Generation Request Creation

**Location**: `definition_generator_tab.py` or upstream

**Missing**: Actual code location where category is assigned

### 4.3 AI Classification (Optional)

**Location**: `src/services/container.py` (lines 293-328)

```python
def ontological_classifier(self):
    """Get or create OntologicalClassifier instance (U/F/O classifier)."""
    # Singleton instance created
    # Usage: result = await classifier.classify(begrip, org_ctx, jur_ctx)
```

**If category is None**:
- (Not found in code - need to verify)
- OntologicalClassifier.classify() should be called
- Result.to_string_level() provides classification

**Current Status**: Code path exists but unclear if wired into UI flow

### 4.4 Orchestration & Generation

**File**: `/src/services/orchestrators/definition_orchestrator_v2.py`

**Line ~296-299**:
```python
logger.info(
    f"Generation {generation_id}: Starting orchestration for '{request.begrip}' "
    f"with category '{request.ontologische_categorie}'"  # ← Logs category
)
```

**Line ~323**:
```python
feedback_history = await self.feedback_engine.get_feedback_for_request(
    sanitized_request.begrip, 
    sanitized_request.ontologische_categorie  # ← Passed to feedback
)
```

**Line ~467+**: Category passed to prompt service

### 4.5 Prompt Building

**File**: `/src/services/prompts/prompt_service_v2.py`

**Components**:
- `semantic_categorisation_module.py` - Uses category for semantic analysis
- Prompt template selected based on `ontologische_categorie`
- Category hint added to prompt: `"Dit begrip is een {category}. Houd hier rekening mee in de definitie."`

### 4.6 Validation

**File**: `/src/services/orchestrators/validation_orchestrator_v2.py`

**Line ~validation call**:
```python
validation_result = await validation_service.validate(
    definitie=...,
    ontologische_categorie=request.ontologische_categorie,  # ← Passed
    context=context
)
```

**ESS-02 Execution**:
- ModularValidationService calls ESS02Validator.validate()
- Result recorded but NOT blocking
- Definition proceeds regardless

### 4.7 Storage

**File**: `/src/services/orchestrators/definition_orchestrator_v2.py` (lines ~670)

```python
repository.save(
    Definition(
        categorie=request.ontologische_categorie,  # Stored in DB
        ...
    )
)
```

---

## 5. UI Components: What Exists

### 5.1 Definition Generator Tab

**File**: `/src/ui/components/definition_generator_tab.py`

**Functionality**:
- Displays generation results
- Shows validation score
- Shows category IF provided (read-only)
- Performs duplicate checking

**Missing**: No widget to INPUT category

### 5.2 Enhanced Context Manager Selector

**File**: `/src/ui/components/enhanced_context_manager_selector.py`

**What It Does**:
- Selector for organisatorische context (OM, ZM, DJI, etc.)
- Selector for juridische context (Strafrecht, Civiel recht, etc.)
- Selector for wettelijke basis (WvSr, Awb, etc.)

**Extensible**: Pattern could be used for category selector, but NOT implemented

### 5.3 UI Gaps Identified

**Gap 1: No Category Selector Widget**
- Users cannot select category
- Category must come from elsewhere (AI, default, API)

**Gap 2: No AI Suggestion Display**
- OntologicalClassifier exists
- No UI shows classification results
- No override mechanism visible

---

## 6. OntologicalClassifier Service (U/F/O)

### 6.1 Service Definition

**File**: `/src/services/classification/ontological_classifier.py` (85-291 lines)

**Class**: `OntologicalClassifier`

**Methods**:
- `async classify(begrip, org_context, jur_context) → ClassificationResult`
- `async classify_batch(begrippen, shared_context) → dict`
- `async validate_existing_definition(begrip, claimed_level, definition_text) → (bool, str)`

### 6.2 Classification Result

**Type**: `ClassificationResult` dataclass

```python
@dataclass
class ClassificationResult:
    level: OntologicalLevel              # U/F/O
    confidence: float                    # 0.0-1.0
    confidence_level: ClassificationConfidence  # HIGH/MEDIUM/LOW
    rationale: str                       # Explanation
    scores: dict[str, float]             # {U: 0.8, F: 0.15, O: 0.05}
    metadata: dict | None = None

    def to_string_level(self) -> str:
        """Converteer naar string voor GenerationRequest.ontologische_categorie"""
        return self.level.value  # Returns "U" or "F" or "O"
```

### 6.3 AI-Powered Classification

**Prompt Built**: (lines ~148-169)
```
Classificeer het volgende juridische begrip in een ontologisch niveau:

Begrip: {begrip}

Ontologische niveaus:
- U (Universeel): Universele begrippen die overal gelden
- F (Functioneel): Functionele begrippen domein-specifiek maar org-onafhankelijk
- O (Operationeel): Operationele begrippen organisatie-specifiek

Geef antwoord in JSON formaat:
{
    "level": "U/F/O",
    "confidence": 0.0-1.0,
    "rationale": "Uitleg",
    "scores": {"U": ..., "F": ..., "O": ...}
}
```

**Model**: GPT-4 (via AIServiceV2)  
**Temperature**: 0.3 (consistent/deterministic)

### 6.4 Container Registration

**File**: `/src/services/container.py` (lines 293-328)

```python
def ontological_classifier(self):
    """Get or create OntologicalClassifier instance (U/F/O classifier)."""
    if "ontological_classifier" not in self._instances:
        from services.classification.ontological_classifier import OntologicalClassifier
        
        ai_service = AIServiceV2(...)
        self._instances["ontological_classifier"] = OntologicalClassifier(ai_service)
    
    return self._instances["ontological_classifier"]
```

**Intended Usage**:
```python
classifier = container.ontological_classifier()
result = await classifier.classify(begrip, org_ctx, jur_ctx)
request.ontologische_categorie = result.to_string_level()
```

**Status**: ✅ Infrastructure ready  
**Status**: ❓ Integration with UI unclear

---

## 7. Complete File Inventory

### Core Domain & Models
- **`/src/domain/ontological_categories.py`** - OntologischeCategorie enum (4 values)

### Database Layer
- **`/src/database/schema.sql`** - `categorie` column definition
- **`/src/database/definitie_repository.py`** - Database mapping & access
- **`/src/services/definition_repository.py`** - Repository interface

### Validation (Toetsregels)
- **`/src/toetsregels/regels/ESS-02.json`** - Rule metadata & patterns
- **`/src/toetsregels/regels/ESS-02.py`** - Validator implementation (ESS02Validator class)

### Classification Service (U/F/O)
- **`/src/services/classification/ontological_classifier.py`** - OntologicalClassifier (85-291 lines)
- **`/src/services/classification/__init__.py`** - Module exports

### Service Container & Orchestration
- **`/src/services/container.py`** - DI registration (ontological_classifier method, line 293)
- **`/src/services/orchestrators/definition_orchestrator_v2.py`** - Main flow
- **`/src/services/orchestrators/validation_orchestrator_v2.py`** - Validation context

### Prompt & Generation
- **`/src/services/prompts/prompt_service_v2.py`** - Category in prompt selection
- **`/src/services/prompts/modules/semantic_categorisation_module.py`** - Category semantics

### Service Interfaces
- **`/src/services/interfaces.py`** - GenerationRequest definition (line ~147-200)

### UI Components
- **`/src/ui/components/definition_generator_tab.py`** - Generation tab (no category selector)
- **`/src/ui/components/enhanced_context_manager_selector.py`** - Context selectors (pattern for category)
- **`/src/ui/session_state.py`** - Session state management

### Tests
- **`/tests/test_ontological_category_fix.py`** - Category tests (comprehensive)
- **`/tests/test_modular_prompt_builder.py`** - ESS-02 in prompts

### Example/Documentation
- **`/docs/examples/classifier_integration_ui.py`** - Example usage (shows integration pattern)
- **`/docs/examples/service_adapter_with_classifier.py`** - Example adapter pattern

---

## 8. Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          USER INTERFACE                         │
│                                                                 │
│  ┌──────────────────┐     ┌──────────────────────────────┐    │
│  │ Term Input       │     │ Context Selection            │    │
│  │ (Definition Gen) │──→  │ (org/jur/wet selectors)      │    │
│  └──────────────────┘     └──────────────────────────────┘    │
│           │                          │                         │
│           └──────────────┬───────────┘                         │
│                          │                                     │
│      MISSING: Category Selector Widget                        │
│                          │                                     │
└──────────────────────────┼──────────────────────────────────┘
                           │
                           ↓
         ┌─────────────────────────────────┐
         │  GenerationRequest Created      │
         │  - begrip: "Overeenkomst"       │
         │  - ontologische_categorie: ???  │ ← WHERE SET?
         │  - org/jur/wet contexts         │
         └─────────────────────────────────┘
                           │
              ┌────────────┴──────────────┐
              │                           │
              ↓                           ↓
    ┌──────────────────┐        ┌───────────────────┐
    │ Use Default?     │        │ AI Classify?      │
    │ (if exists)      │        │ OntologicalClass- │
    │                  │        │ ifier.classify()  │
    └──────────────────┘        └───────────────────┘
              │                           │
              └────────────┬──────────────┘
                           │
                           ↓
         ┌─────────────────────────────────┐
         │ Definition Orchestrator V2      │
         │ - Logs category usage           │
         │ - Passes to prompt service      │
         └─────────────────────────────────┘
                           │
                           ↓
         ┌─────────────────────────────────┐
         │ Prompt Service V2               │
         │ - Template selected by category │
         │ - Category hint added to prompt │
         │ - Semantic categorisation       │
         └─────────────────────────────────┘
                           │
                           ↓
         ┌─────────────────────────────────┐
         │ AI Service (GPT-4)              │
         │ - Generates definition          │
         └─────────────────────────────────┘
                           │
                           ↓
         ┌─────────────────────────────────┐
         │ Validation Orchestrator V2      │
         │ - Runs ESS-02 validation        │
         │ - Category passed to validators │
         └─────────────────────────────────┘
                           │
                           ↓
         ┌─────────────────────────────────┐
         │ ESS-02 Validator                │
         │ - Pattern detection             │
         │ - Ambiguity check               │
         │ - Records violation if fail     │
         │ ⚠️ NOT BLOCKING!                │
         └─────────────────────────────────┘
                           │
                           ↓
         ┌─────────────────────────────────┐
         │ Definition Repository           │
         │ - Save definition               │
         │ - Store category in DB          │
         │ - categorie = request.          │
         │   ontologische_categorie        │
         └─────────────────────────────────┘
                           │
                           ↓
         ┌─────────────────────────────────┐
         │ Database (SQLite)               │
         │ - categorie column              │
         │ - Value: type|proces|resultaat  │
         │   |exemplaar|None               │
         └─────────────────────────────────┘
```

---

## 9. Key Findings

### What's Fully Implemented ✅

1. **Domain Enums**: OntologischeCategorie (TYPE/PROCES/RESULTAAT/EXEMPLAAR)
2. **U/F/O Classifier**: Complete OntologicalClassifier service with AI backing
3. **Validation Rule ESS-02**: Full regex pattern matching, proper scoring
4. **Data Flow**: Category flows through entire generation pipeline
5. **Prompt Integration**: Category used for template selection and hints
6. **Database Storage**: Category persisted and retrieved
7. **Service Container**: DI setup for classifier and all components
8. **Test Coverage**: Comprehensive tests for category handling

### What's Missing or Incomplete ❌

1. **No UI Category Selector Widget**
   - Users cannot select category
   - No visible input field
   - No dropdown menu
   - Pattern exists (context selectors) but not implemented

2. **Category Not Blocking Generation (DEF-39?)**
   - ESS-02 runs but doesn't prevent save
   - Definition marked acceptable even if category ambiguous
   - No "category required" validation
   - Field is optional/nullable

3. **No AI Suggestion Display (DEF-13?)**
   - OntologicalClassifier exists
   - No UI shows recommendations
   - No confidence display
   - No override mechanism

4. **Missing Category Default Logic**
   - Where does default category come from?
   - What happens when null?
   - Fallback behavior unclear

5. **Classification Integration Unclear**
   - Code path exists in container
   - Not clear if actually called from UI
   - No logs or traces found

---

## 10. Answering Key Questions

### Q1: Is definition generation **blocked** when ontologische_categorie is missing?
**A**: **NO** - Category field is optional/nullable, and even ESS-02 failures don't block generation.

### Q2: Is there a **UI widget** for category selection?
**A**: **NO** - No user-facing selector found. Pattern could be based on context manager selector.

### Q3: Is there **AI-suggested category** with user override?
**A**: **PARTIAL** - OntologicalClassifier exists with AI backing, but UI integration unclear.

### Q4: Where is ontologische_categorie set/validated?
**A**: Multiple places:
- GenerationRequest field (optional)
- Potential AI classification (OntologicalClassifier)
- Validation: ESS-02 rule
- Storage: Database `categorie` field

### Q5: Are DEF-39 and DEF-13 implemented?
**A**: **UNKNOWN** - Epic/Story documents not located. Implementation status based on inferences.

---

## 11. Architecture Assessment

### Strengths
- Clean separation of concerns (U/F/O vs TYPE/PROCES/RESULTAAT)
- Enum-based domain prevents mistakes
- Category flows naturally through pipeline
- Validation rule properly implemented
- AI classification service ready

### Weaknesses
- Dual naming confusion (ontologische_categorie vs categorie)
- No user control/visibility of category
- Validation marked "verplicht" but not actually blocking
- AI classification exists but orphaned from UI
- ESS-02 failure doesn't prevent save despite importance

### Risks
- Users may be confused about what category is used
- Invalid category combinations possible
- Definition quality may suffer without proper category hint
- ESS-02 rule effectiveness undermined by non-blocking behavior

---

## 12. Recommended Next Steps

### For DEF-39 (If Requirement Is: Block Without Category)
1. **Find the epic/story** to confirm requirement
2. **Make category REQUIRED**: Change GenerationRequest field to non-optional
3. **Add UI widget**: Category dropdown selector (similar to context selector)
4. **Implement blocking**: Check category before save, reject if missing

### For DEF-13 (If Requirement Is: AI-Suggest Category)
1. **Find the epic/story** to confirm requirement
2. **Wire UI integration**: Show OntologicalClassifier results in UI
3. **Add suggestion display**: Show confidence and rationale
4. **Implement override**: Allow user to accept/reject/modify suggestion

### For General Improvement
1. **Rename field consistently**: Use `ontologische_categorie` everywhere (not just `categorie`)
2. **Make ESS-02 blocking**: Prevent save if category ambiguous
3. **Add category to duplicates**: Consider category when finding similar definitions
4. **Improve logging**: Log category selection and confidence

---

## 13. File Location Quick Reference

| Component | File | Line(s) |
|-----------|------|---------|
| Enum Definition | `/src/domain/ontological_categories.py` | 11-17 |
| Request Interface | `/src/services/interfaces.py` | ~147 |
| ESS-02 Rule | `/src/toetsregels/regels/ESS-02.py` | 1-250+ |
| U/F/O Classifier | `/src/services/classification/ontological_classifier.py` | 85-291 |
| Container Registration | `/src/services/container.py` | 293-328 |
| Orchestration | `/src/services/orchestrators/definition_orchestrator_v2.py` | Multiple |
| Validation | `/src/services/orchestrators/validation_orchestrator_v2.py` | Multiple |
| Prompt Building | `/src/services/prompts/prompt_service_v2.py` | Multiple |
| UI Display | `/src/ui/components/definition_generator_tab.py` | Multiple |
| Tests | `/tests/test_ontological_category_fix.py` | 1-217 |

---

## 14. Appendix: Code Snippets

### A. GenerationRequest with Category

```python
@dataclass
class GenerationRequest:
    """Request object voor het genereren van een definitie."""
    id: str
    begrip: str
    ontologische_categorie: str | None = None  # ← Nullable!
    organisatorische_context: list[str] | None = None
    juridische_context: list[str] | None = None
    wettelijke_basis: list[str] | None = None
    context: str | None = None
    actor: str = "system"
    legal_basis: str = "legitimate_interest"
```

### B. ESS-02 Validation Pattern Matching

```python
def validate(self, definitie: str, begrip: str, context: dict | None = None) \
  → tuple[bool, str, float]:
    # 0️⃣ Metadata-override if provided
    # 1️⃣ Explicit failure examples per category
    # 2️⃣ Category detection via regex patterns
    # 3️⃣ One category → ✔️ pass
    # 4️⃣ Multiple categories → ❌ fail (ambiguous)
    # 5️⃣ No hits → Good examples per category
```

### C. OntologicalClassifier Integration

```python
def ontological_classifier(self):
    """Get or create OntologicalClassifier instance (U/F/O classifier)."""
    if "ontological_classifier" not in self._instances:
        ai_service = AIServiceV2(...)
        self._instances["ontological_classifier"] = OntologicalClassifier(ai_service)
    return self._instances["ontological_classifier"]

# Usage:
classifier = container.ontological_classifier()
result = await classifier.classify(begrip, org_ctx, jur_ctx)
request.ontologische_categorie = result.to_string_level()
```

### D. Category in Orchestrator

```python
logger.info(
    f"Generation {generation_id}: Starting orchestration for '{request.begrip}' "
    f"with category '{request.ontologische_categorie}'"
)

# ... later ...

repository.save(
    Definition(
        categorie=request.ontologische_categorie,  # Stored in DB
        # ... other fields ...
    )
)
```

---

## 15. Conclusion

The **ontologische_categorie** feature is **well-architected** with:
- Clear domain models (2 separate systems)
- Complete validation logic (ESS-02)
- Full data flow integration
- AI classification capability

However, it's **incomplete from a user perspective**:
- No UI for category selection/display
- Validation doesn't block despite "verplicht" marking
- AI classification exists but integration unclear

**Status**: Foundation complete, user-facing features need completion.

