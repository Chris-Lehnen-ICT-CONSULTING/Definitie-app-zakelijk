# Architectural Review: Ontological Classification Decoupling

**Date**: 2025-10-07
**Reviewer**: Claude Code (Architecture Review Mode)
**Subject**: Evaluation of Classification Placement in Definition Generation Flow
**Status**: 🔴 CRITICAL - Architectural Constraint Violation Detected

---

## Code Quality Score: 4/10

**Current Architecture**: Classification is embedded in definition generation flow (UI layer)
**Proposed Architecture (Option 2)**: Classification in ServiceAdapter
**Constraint**: "Ontologische classificatie is PRE-PROCESSING stap, los van definitie generatie"

**Score Breakdown**:
- **Separation of Concerns**: 2/10 (classification tightly coupled to generation)
- **Reusability**: 3/10 (cannot classify without generating)
- **Testability**: 5/10 (requires full generation flow to test classification)
- **Architectural Clarity**: 4/10 (unclear where classification responsibility lies)
- **Constraint Compliance**: 3/10 (classification not truly "pre-processing")

---

## 🔴 Critical Issues (Must Fix)

### [ISSUE-1]: Classification NOT Separate from Generation

**Current Situation (AS-IS)**:
```python
# tabbed_interface.py (UI layer)
async def generate_definition(self, begrip, context_data):
    # STAP 1: Bepaal categorie (IN generate_definition!)
    auto_categorie, reasoning, scores = await self._determine_ontological_category(...)

    # STAP 2: Genereer definitie (met categorie)
    service_result = await self.definition_service.generate_definition(
        begrip=begrip,
        categorie=auto_categorie,  # Classification result used
        ...
    )
```

**Proposed Solution (Option 2)**:
```python
# ServiceAdapter
async def generate_definition(self, begrip, context_dict, **kwargs):
    # Classification HIER (still inside generate_definition)
    categorie = self.ontology_classifier.classify(begrip)

    request = GenerationRequest(
        begrip=begrip,
        ontologische_categorie=categorie.value,
        ...
    )

    return await self.orchestrator.create_definition(request)
```

**Impact**: 🔴 **CRITICAL VIOLATION OF CONSTRAINT**

The constraint states: *"Ontologische classificatie is PRE-PROCESSING stap, **los van** definitie generatie"*

**Both implementations VIOLATE this constraint because**:
1. Classification happens INSIDE `generate_definition()` method
2. Classification cannot be invoked WITHOUT triggering definition generation
3. Classification is NOT a separate, reusable service
4. Cannot test classification independently from generation

**Solution**: See [BETTER ARCHITECTURE] section below

---

### [ISSUE-2]: Prompt Dependency Creates Tight Coupling

**Evidence from Orchestrator**:
```python
# definition_orchestrator_v2.py:423
prompt_result = await self.prompt_service.build_generation_prompt(
    sanitized_request,  # Contains ontologische_categorie
    feedback_history=feedback_history,
    context=context,
)
```

**Evidence from PromptService**:
```python
# prompt_service_v2.py:115-137
if request.ontologische_categorie:
    cat = request.ontologische_categorie.strip().lower()
    enriched_context.metadata["ontologische_categorie"] = cat

    # Mapping to semantic category for template selection
    mapping = {
        "proces": "Proces",
        "type": "Object",
        "resultaat": "Maatregel",
    }
    semantic = mapping.get(cat)
    if semantic:
        enriched_context.metadata["semantic_category"] = semantic
```

**Evidence from SemanticCategorisationModule**:
```python
# semantic_categorisation_module.py:86-93
categorie = context.get_metadata("ontologische_categorie")

# Sla categorie op voor andere modules
if categorie:
    context.set_shared("ontological_category", categorie)

# Bouw de ESS-02 sectie (category-specific guidance)
content = self._build_ess02_section(categorie)
```

**Impact**: 🔴 **TRUE DEPENDENCY CONFIRMED**

The category is **ESSENTIAL** for prompt generation because:
1. **SemanticCategorisationModule** (ESS-02) injects category-specific guidance into prompt
2. **TemplateModule** selects templates based on category (Proces/Object/Maatregel)
3. Without category, prompt lacks critical guidance for GPT-4

**This is NOT just metadata - it fundamentally shapes the prompt structure!**

**Conclusion**: Category MUST be determined BEFORE prompt building, confirming it's a true pre-processing step.

---

### [ISSUE-3]: Option 2 Does NOT Achieve True Separation

**Proposed Code (Option 2)**:
```python
# ServiceAdapter.generate_definition()
async def generate_definition(self, begrip, context_dict, **kwargs):
    # Classificatie HIER (niet in UI)
    categorie = self.ontology_classifier.classify(begrip)

    request = GenerationRequest(
        begrip=begrip,
        ontologische_categorie=categorie.value,
        ...
    )

    return await self.orchestrator.create_definition(request)
```

**Problem**: Classification is STILL embedded in `generate_definition()` flow!

**Reusability Test**:
```python
# Can I classify WITHOUT generating?
# NO - classification is private to generate_definition()

# What if I want to:
# 1. Pre-classify 100 terms for batch processing?
# 2. Show classification to user BEFORE generating?
# 3. Use classification in different context (e.g., validation)?

# ANSWER: NOT POSSIBLE with Option 2
```

**Impact**: 🔴 **OPTION 2 FAILS THE "LOS VAN" TEST**

---

## 🟡 Important Improvements (Strongly Recommended)

### [IMPROVEMENT-1]: TRUE Separation via Dedicated Service

**Better Approach - Variant B** (from your question):
```python
# ServiceAdapter with SEPARATE classification method
class ServiceAdapter:
    def __init__(self, container):
        self.orchestrator = container.definition_orchestrator()
        self.classifier = OntologyClassifier()  # Dedicated classifier

    # SEPARATE method for classification (true pre-processing)
    def classify_begrip(self, begrip: str, context: dict = None) -> CategoryResult:
        """Classify a term WITHOUT generating definition."""
        return self.classifier.classify(begrip, context)

    # Generation can use classification, but doesn't OWN it
    async def generate_definition(self, begrip, context_dict, **kwargs):
        # Check if category already provided (pre-classified)
        categorie = kwargs.get("categorie")

        # If not provided, classify as convenience
        if not categorie:
            result = self.classify_begrip(begrip, context_dict)
            categorie = result.level

        request = GenerationRequest(
            begrip=begrip,
            ontologische_categorie=categorie,
            ...
        )

        return await self.orchestrator.create_definition(request)
```

**Benefit**: Now classification is TRULY separate:
```python
# Use case 1: Classify without generating
result = service.classify_begrip("validatie")
# Returns: CategoryResult(level="PROCES", confidence=0.85, ...)

# Use case 2: Pre-classify, then generate later
category = service.classify_begrip("sanctie").level
# ... do other work ...
definition = await service.generate_definition("sanctie", context, categorie=category)

# Use case 3: Batch classification
categories = [service.classify_begrip(term) for term in terms]
```

**Current Approach**: `category = generate_definition(...).category` (wasteful!)
**Better Approach**: `category = classify_begrip(...)` (efficient, reusable)

---

### [IMPROVEMENT-2]: Make Classification Optional in GenerationRequest

**Current Problem**:
```python
# Orchestrator EXPECTS category to be present
# definition_orchestrator_v2.py:201
logger.info(f"...with category '{request.ontologische_categorie}'")

# Prompt service REQUIRES category for proper guidance
# semantic_categorisation_module.py:86
categorie = context.get_metadata("ontologische_categorie")
```

**Better Design**:
```python
# GenerationRequest with optional category
@dataclass
class GenerationRequest:
    begrip: str
    ontologische_categorie: Optional[str] = None  # Optional!
    # ... other fields

# Orchestrator handles missing category
class DefinitionOrchestratorV2:
    def __init__(self, ..., classifier: OntologyClassifier = None):
        self.classifier = classifier or OntologyClassifier()

    async def create_definition(self, request: GenerationRequest, ...):
        # PRE-PROCESSING: Ensure category is determined
        if not request.ontologische_categorie:
            result = self.classifier.classify(request.begrip)
            request.ontologische_categorie = result.level
            logger.info(f"Auto-classified: {result.level} (conf={result.confidence})")

        # Now proceed with prompt building (category guaranteed)
        prompt_result = await self.prompt_service.build_generation_prompt(...)
        ...
```

**Benefit**:
- Classification becomes **internal orchestrator concern**
- UI doesn't need to know about it
- ServiceAdapter can be thin pass-through
- Supports both: "UI pre-classifies" OR "Orchestrator auto-classifies"

---

## 🟢 Minor Suggestions (Nice to Have)

### [SUGGESTION-1]: Add Classification Result to Response Metadata

**Current**: Classification result is lost after use
**Better**: Include in response for transparency

```python
# DefinitionResponseV2
@dataclass
class DefinitionResponseV2:
    success: bool
    definition: Definition
    validation_result: ValidationResult
    metadata: dict
    classification: ClassificationResult = None  # NEW!

# Orchestrator
response = DefinitionResponseV2(
    success=True,
    definition=definition,
    validation_result=raw_validation,
    classification=classification_result,  # Include classification
    metadata={
        "ontological_category": categorie,
        "classification_confidence": classification_result.confidence,
        ...
    }
)
```

**Benefit**: UI can show "Why was this classified as PROCES? (confidence: 0.85)"

---

### [SUGGESTION-2]: Explicit Classification Service Interface

**Define clean contract**:
```python
# services/interfaces.py
class OntologyClassifierInterface(Protocol):
    """Interface for ontological classification."""

    def classify(
        self,
        begrip: str,
        context: Optional[dict] = None
    ) -> ClassificationResult:
        """Classify term to ontological category.

        Returns:
            ClassificationResult with level, confidence, rationale
        """
        ...

    def classify_batch(
        self,
        begrippen: List[str]
    ) -> List[ClassificationResult]:
        """Classify multiple terms efficiently."""
        ...
```

**Benefit**: Clear contract, mockable for tests, swappable implementations

---

## ⭐ Positive Highlights

1. **Handover Document Quality**: Excellent analysis with 3 clear options and trade-offs
2. **Constraint Identification**: Correctly identified that classification should be "los van" generation
3. **Evidence-Based Review**: Test results (93.3% accuracy) provide empirical validation
4. **Realistic Options**: All 3 options are implementable (not theoretical)
5. **Code Reduction**: Proposed refactor reduces code by 76% (1415 → 342 LOC)

---

## 📊 Summary

### Overall Assessment

**Current Architecture (AS-IS)**:
- ❌ Violates "pre-processing, los van generatie" constraint
- ❌ Classification tightly coupled to generation
- ❌ Cannot reuse classification independently
- ❌ 61 lines of business logic in UI layer

**Proposed Architecture (Option 2 - Original)**:
- ⚠️ Moves classification from UI to Service (good)
- ❌ Still embedded in `generate_definition()` method (bad)
- ❌ Still cannot classify without generating (constraint violation)
- ⚠️ Better than AS-IS but doesn't achieve true separation

**Recommended Architecture (Variant B - Enhanced Option 2)**:
- ✅ Classification is SEPARATE method (`classify_begrip()`)
- ✅ Can be used independently from generation
- ✅ Reusable for batch processing, pre-classification
- ✅ True "pre-processing step" as per constraint
- ✅ Maintains convenient integration with generation

### Key Learning Points

1. **"Los van" means STRUCTURALLY separate, not just "called before"**
   - Option 2 calls classification before generation (good)
   - But it's still inside the same method (bad)
   - Variant B makes it a separate public API (excellent)

2. **Prompt dependency confirms classification is pre-processing**
   - SemanticCategorisationModule NEEDS category for ESS-02 guidance
   - TemplateModule uses category for template selection
   - Category shapes the entire prompt structure
   - **Conclusion**: Category MUST be determined before prompt building

3. **Architectural purity vs. Pragmatism**
   - Option 3 (Orchestrator) is most "pure" but highest risk
   - Variant B (ServiceAdapter with separate method) is pragmatic AND correct
   - Choose Variant B for balance of quality and safety

---

## 📋 Recommended Implementation

### Phase 1: Core Refactor (6-8 hours)

**Step 1**: Create separate classification service (2h)
```python
# src/services/classification/ontology_classifier.py
class OntologyClassifier:
    """Dedicated classification service."""

    def classify(self, begrip: str, context: dict = None) -> ClassificationResult:
        # Use level_classifier.py internally
        scores = self._generate_scores(begrip)
        result = classify_level(scores, begrip, policy="gebalanceerd")
        return self._to_classification_result(result)
```

**Step 2**: Add to ServiceAdapter as separate method (1h)
```python
# src/services/service_factory.py
class ServiceAdapter:
    def classify_begrip(self, begrip: str, ...) -> ClassificationResult:
        """PUBLIC API for classification (separate from generation)."""
        return self.classifier.classify(begrip, ...)

    async def generate_definition(self, begrip, context_dict, **kwargs):
        # Use classification as convenience, not requirement
        categorie = kwargs.get("categorie") or self.classify_begrip(begrip).level
        ...
```

**Step 3**: Simplify UI (delete 61 lines of orchestration) (1h)
```python
# src/ui/tabbed_interface.py
def _handle_definition_generation(self, begrip, context_data):
    # OPTION A: Let service handle classification
    service_result = await self.definition_service.generate_definition(
        begrip=begrip,
        context_dict={...},
        # No category - service will classify
    )

    # OPTION B: Pre-classify and show to user (if desired)
    classification = self.definition_service.classify_begrip(begrip)
    st.info(f"Classified as: {classification.level} (confidence: {classification.confidence})")

    service_result = await self.definition_service.generate_definition(
        begrip=begrip,
        categorie=classification.level,  # Pass pre-classification
        ...
    )
```

**Step 4**: Update Orchestrator to handle optional category (2h)
```python
# src/services/orchestrators/definition_orchestrator_v2.py
async def create_definition(self, request: GenerationRequest, ...):
    # PRE-PROCESSING: Ensure category exists
    if not request.ontologische_categorie:
        result = self.classifier.classify(request.begrip)
        request = request.replace(ontologische_categorie=result.level)
        logger.info(f"Auto-classified: {result.level}")

    # Continue with existing flow
    prompt_result = await self.prompt_service.build_generation_prompt(...)
    ...
```

### Phase 2: Testing & Validation (4 hours)

**Unit Tests**:
```python
def test_classify_without_generating():
    """Can classify independently."""
    service = ServiceAdapter(...)
    result = service.classify_begrip("validatie")

    assert result.level == "PROCES"
    assert result.confidence > 0.7
    # No definition generated!

def test_generation_uses_classification():
    """Generation reuses classification."""
    service = ServiceAdapter(...)

    # Pre-classify
    cat = service.classify_begrip("sanctie").level

    # Generate with pre-classified category
    result = await service.generate_definition("sanctie", categorie=cat, ...)

    assert result.definition.ontologische_categorie == cat
```

**Integration Tests**:
```python
async def test_orchestrator_auto_classifies():
    """Orchestrator classifies when category missing."""
    request = GenerationRequest(begrip="besluit")  # No category

    response = await orchestrator.create_definition(request)

    # Orchestrator should have classified it
    assert response.definition.ontologische_categorie is not None
    assert response.classification is not None
```

---

## 🎯 VERDICT

### Constraint Compliance: ❌ FAILED

**Current (AS-IS)**: Classification embedded in UI.generate_definition() - **VIOLATES**
**Proposed (Option 2)**: Classification embedded in ServiceAdapter.generate_definition() - **STILL VIOLATES**
**Recommended (Variant B)**: Classification as separate ServiceAdapter.classify_begrip() - **✅ COMPLIES**

### Architecture Decision

**❌ DO NOT implement Option 2 as originally proposed**

It improves code organization (UI → Service) but **fails to achieve true separation**. Classification remains embedded in generation flow.

**✅ IMPLEMENT Variant B (Enhanced Option 2)**

```
ServiceAdapter:
  ├─ classify_begrip(begrip) → ClassificationResult  ✅ SEPARATE, REUSABLE
  └─ generate_definition(begrip, categorie=None) → DefinitionResponse
         └─ Uses classify_begrip() internally if categorie=None
```

**Benefits**:
- ✅ True pre-processing (can classify without generating)
- ✅ Reusable API (batch classification, UI pre-classification)
- ✅ Backward compatible (generation still works standalone)
- ✅ Constraint compliant ("los van definitie generatie")
- ✅ Lower risk than Option 3 (Orchestrator refactor)

### Implementation Timeline

- **Total Effort**: 10-12 hours (6-8h core + 4h testing)
- **Risk Level**: Medium (significant refactor but clear path)
- **Breaking Changes**: Minimal (additive API, backward compatible)
- **Code Reduction**: 76% (1415 → 342 LOC)
- **Performance**: 500x faster (no web lookups)

---

## 🚀 Next Steps

### IMMEDIATE (Before Implementation)

1. **Confirm Architecture Decision** with tech lead
   - Present Variant B (this review)
   - Get sign-off on separate `classify_begrip()` method
   - Agree on public API contract

2. **Create Spike/Prototype** (2 hours)
   - Implement `OntologyClassifier` class
   - Add `classify_begrip()` to ServiceAdapter
   - Test independently: `result = service.classify_begrip("validatie")`
   - Verify reusability before full refactor

3. **Write Architecture Decision Record** (ADR)
   - Document: "Why classification is separate from generation"
   - Rationale: Constraint compliance, reusability, testability
   - Consequences: New public API, clearer separation

### IMPLEMENTATION (After Approval)

1. **Phase 1**: Core refactor (6-8h)
   - See detailed steps above

2. **Phase 2**: Testing (4h)
   - Unit + integration tests
   - Regression tests (15 test cases)

3. **Phase 3**: Documentation (2h)
   - Update API docs
   - Add usage examples
   - Update HANDOVER with final decision

---

## 📎 References

### Files Reviewed

- `/src/ui/tabbed_interface.py` (lines 231-291, 698-866)
- `/src/services/service_factory.py` (ServiceAdapter)
- `/src/services/orchestrators/definition_orchestrator_v2.py` (lines 169-432)
- `/src/services/prompts/prompt_service_v2.py` (lines 84-194)
- `/src/services/prompts/modules/semantic_categorisation_module.py`
- `/docs/handovers/HANDOVER_ONTOLOGICAL_CLASSIFICATION_REFACTOR.md`

### Key Constraint

> **"Ontologische classificatie is PRE-PROCESSING stap, los van definitie generatie, omdat categorie de promptopbouw bepaalt"**

**Interpretation**:
- "PRE-PROCESSING" = happens BEFORE generation starts
- "LOS VAN" = structurally SEPARATE, can exist independently
- "omdat categorie de promptopbouw bepaalt" = true dependency confirmed

**Verdict**: Variant B (separate method) is the ONLY option that fully satisfies this constraint.

---

**END OF REVIEW**

*Generated by: Claude Code (Architecture Review Mode)*
*Date: 2025-10-07*
*Review Type: Architectural Constraint Compliance*
