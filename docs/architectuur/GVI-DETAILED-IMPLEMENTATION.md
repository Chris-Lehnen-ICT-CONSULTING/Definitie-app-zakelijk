# GVI Detailed Implementation Guide

**Versie**: 1.0
**Datum**: 2025-08-25
**Doel**: Stap-voor-stap implementatie per functionaliteit

---

## 📋 Week 0: UI Decoupling - Detailed Steps

### Dag 1-2: Extract Business Logic naar Services

#### 1. CategoryService Implementation
```bash
# Create new file
touch src/services/category_service.py
```

**Stappen:**
1. Identificeer alle category-gerelateerde business logic in `definition_generator_tab.py`
2. Extract naar service:
```python
class CategoryService:
    def __init__(self, repository: DefinitieRepository):
        self.repository = repository

    def update_category(self, definition_id: int, new_category: str) -> bool:
        # Business logic from _update_category method
        # Add validation, logging, events
```
3. Update UI om service te gebruiken:
```python
# OLD: self._update_category(new_category, generation_result)
# NEW: self.category_service.update_category(definitie.id, new_category)
```
4. Test schrijven: `tests/test_category_service.py`

#### 2. WorkflowService Implementation
**Locatie**: `src/services/workflow_service.py` (bestaat al!)

**Stappen:**
1. Review bestaande `workflow_service.py`
2. Extract `_submit_for_review` logic uit UI
3. Integreer met bestaande service:
```python
def submit_for_review(self, definition_id: int, user: str = "web_user") -> bool:
    return self.change_status(
        definition_id,
        DefinitieStatus.REVIEW,
        user,
        "Submitted for review"
    )
```
4. Update UI aanroep
5. Test toevoegen aan `tests/test_workflow_service.py`

#### 3. ExportService Implementation
**Locatie**: `src/services/export_service.py` (nieuw)

**Stappen:**
1. Extract alle export logic uit `_export_definition`
2. Creëer service interface:
```python
class ExportService:
    def export_to_txt(self, definition_id: int) -> tuple[bool, str, bytes]:
        # All export logic here
        pass

    def export_to_pdf(self, definition_id: int) -> tuple[bool, str, bytes]:
        # Future PDF export
        pass
```
3. Verplaats data preparatie naar service
4. Update UI voor simpele download button
5. Tests: `tests/test_export_service.py`

### Dag 3: Create Service Facade

#### DefinitionUIService Implementation
**Locatie**: `src/services/definition_ui_service.py`

**Stappen:**
1. Creëer facade pattern:
```python
class DefinitionUIService:
    def __init__(
        self,
        category_service: CategoryService,
        workflow_service: WorkflowService,
        export_service: ExportService,
        selection_service: DefinitionSelectionService
    ):
        self.category = category_service
        self.workflow = workflow_service
        self.export = export_service
        self.selection = selection_service
```

2. Update `definition_generator_tab.py` constructor:
```python
def __init__(self, checker: DefinitieChecker, ui_service: DefinitionUIService):
    self.checker = checker
    self.ui_service = ui_service
```

3. Wire up in main app via dependency injection

### Dag 4-5: Replace Legacy Services

#### 1. Modern Web Lookup Integration
**Files**:
- `src/services/service_factory.py`
- `src/services/web_lookup/modern_web_lookup_service.py`

**Stappen:**
1. Update imports in `unified_definition_generator.py`:
```python
# OLD
from services.legacy_web_lookup_service import LegacyWebLookupService

# NEW
from services.service_factory import ServiceFactory
```

2. Change instantiation:
```python
# OLD
self.web_lookup = LegacyWebLookupService()

# NEW
self.web_lookup = ServiceFactory.create_web_lookup_service()
```

3. Update async handling waar nodig
4. Remove legacy fallback code

#### 2. Implement Adapter Pattern
**Locatie**: `src/ui/adapters/agent_result_adapter.py`

**Stappen:**
1. Create adapter interface:
```python
class AgentResultAdapter:
    @staticmethod
    def create(result: Any) -> 'IAgentResult':
        if isinstance(result, dict):
            return DictAgentResult(result)
        return LegacyAgentResult(result)
```

2. Replace all `is_dict` checks in UI:
```python
# OLD
if isinstance(agent_result, dict):
    definitie = agent_result.get("definitie_gecorrigeerd")
else:
    definitie = agent_result.final_definitie

# NEW
adapter = AgentResultAdapter.create(agent_result)
definitie = adapter.get_corrected_definition()
```

3. Test beide formats
4. Plan legacy format deprecation

---

## 📋 Week 1: GVI Cable Fixes - Detailed Steps

### Dag 1-2: Rode Kabel - Feedback Integration

#### Fix feedback_history Parameter
**File**: `services/definition_generator_prompts.py`

**Stappen:**
1. Locate `build_prompt` method (~line 89)
2. Add feedback integration:
```python
def build_prompt(self, request, context, rules, feedback_history=None):
    prompt = self._base_prompt(request, context, rules)

    if feedback_history:
        prompt += "\n\n## Eerdere pogingen en feedback:\n"
        for attempt in feedback_history[-3:]:  # Last 3 attempts
            prompt += f"\nPoging: {attempt['definition']}\n"
            prompt += f"Problemen: {', '.join(attempt['violations'])}\n"
            prompt += f"Verbeter: {', '.join(attempt['suggestions'])}\n"
        prompt += "\nVermijd deze fouten in de nieuwe definitie.\n"

    return prompt
```

3. Update `unified_definition_generator.py` om feedback door te geven
4. Test met mock feedback data
5. Verify in logs dat feedback wordt gebruikt

### Dag 3-4: Gele Kabel - Impliciete Context

#### Make Context Implicit
**File**: `prompt_builder/prompt_builder.py`

**Stappen:**
1. Find context building (~line 193)
2. Create implicit context mapper:
```python
def _make_context_implicit(self, contexts: List[str]) -> List[str]:
    implicit_map = {
        'NP': [
            "- Gebruik terminologie uit het strafrechtelijk domein",
            "- Focus op opsporings- en handhavingsaspecten"
        ],
        'OM': [
            "- Focus op vervolgings- en beslissingsaspecten"
        ],
        # etc...
    }
```

3. Replace explicit context mentions
4. Add rule: "NIET expliciet vermelden: NP, OM, DJI"
5. Test CON-01 compliance

### Dag 5: Blauwe Kabel - Preventieve Validatie

#### Build Preventive Constraints
**File**: `services/unified_definition_generator.py`

**Stappen:**
1. Add constraint builder method:
```python
def _build_preventive_constraints(self, validation_rules: List[Rule]) -> str:
    rule_map = {
        'STR-01': "Begin de definitie met een zelfstandig naamwoord",
        'CON-01': "Vermeld GEEN organisatienamen expliciet",
        # etc...
    }
```

2. Integrate in prompt generation
3. Test each rule preventively
4. Measure reduction in validation failures

---

## 📋 Week 2: Service Activation - Detailed Steps

### Dag 1-2: Security Middleware

**File**: `src/security/security_middleware.py`

**Stappen:**
1. Review existing middleware
2. Create FastAPI integration:
```python
app.add_middleware(SecurityMiddleware)
```
3. Configure rate limiting
4. Test security features
5. Monitor performance impact

### Dag 3-4: Validation Engine as Service

**Directory**: `src/toetsregels/`

**Stappen:**
1. Create validation service wrapper
2. Expose via API endpoint
3. Integrate with generation pipeline
4. Enable/disable rules via config
5. Performance test all 45 rules

### Dag 5: A/B Testing Framework

**File**: `src/services/ab_testing_framework.py`

**Stappen:**
1. Configure experiments
2. Set up metrics collection
3. Create comparison dashboard
4. Run legacy vs modern tests
5. Document performance gains

---

## 📋 Testing Strategy per Component

### Unit Tests
```bash
# Per service
pytest tests/test_category_service.py -v
pytest tests/test_workflow_service.py -v
pytest tests/test_export_service.py -v

# Per cable fix
pytest tests/test_feedback_integration.py -v
pytest tests/test_implicit_context.py -v
pytest tests/test_preventive_validation.py -v
```

### Integration Tests
```bash
# Full flow
pytest tests/test_gvi_integration.py -v

# UI tests
pytest tests/test_ui_service_integration.py -v
```

### Performance Tests
```python
# Measure before/after
- Response time: 8-12s → <5s
- First-time-right: 60% → 90%
- API costs: baseline → -50%
```

---

## 🚀 Rollout Strategy

### Phase 1: Development (Week 0-1)
- Feature flags voor elke cable fix
- Lokale testing environment
- Code reviews per component

### Phase 2: Staging (Week 2)
- Deploy naar test environment
- A/B testing met subset users
- Performance monitoring

### Phase 3: Production (Week 3)
- Gradual rollout (10% → 50% → 100%)
- Monitor metrics closely
- Rollback plan ready

---

## 📊 Success Criteria per Functionaliteit

| Functionaliteit | Success Criteria | Measurement |
|----------------|------------------|-------------|
| Category Update | No direct DB access from UI | Code review |
| Workflow Status | All transitions via service | Audit log |
| Export | Clean separation of concerns | Test coverage |
| Web Lookup | Legacy removed, modern active | Performance test |
| Feedback | Used in prompts | Log analysis |
| Context | No explicit mentions | CON-01 rate |
| Validation | Preventive rules active | Error reduction |

---

*Dit document complementeert het GVI Implementation Plan met concrete implementatie stappen.*
