# GVI Detailed Implementation Guide

**Versie**: 1.1
**Datum**: 2025-08-25 (Updated)
**Doel**: Stap-voor-stap implementatie per functionaliteit
**Status Update**: ServiceAdapter strategie gedocumenteerd

---

## 🔄 Status Update Summary

### Completed ✅
- **CategoryService**: Phase 1-3 refactoring complete
- **RegenerationService**: Rode kabel fix geïmplementeerd
- **ServiceAdapter**: Alternative implementation voor backward compatibility
- **Legacy Service Removal**: UnifiedDefinitionGenerator verwijderd

### In Progress 🚧
- **UI Migration**: Gradual updates naar V2 format
- **WorkflowService**: Partial implementation ✅ **submit_for_review COMPLETED**

### Recently Completed ✅
- **Session State Elimination**: Clean architecture services implemented
- **DataAggregationService**: Services independent of UI state
- **ExportService**: Multiple format support (TXT/JSON/CSV) 
- **DefinitionUIService**: UI Facade pattern implemented

### Pending ⏳
- **Phase 6**: Complete adapter removal (Week 11-12)
- **Direct UI integration**: Remove LegacyGenerationResult dependencies
- **Full service decoupling**: Extract remaining business logic

---

## 📋 Week 0: UI Decoupling - Detailed Steps

### Dag 1-2: Extract Business Logic naar Services

#### 1. CategoryService Implementation ✅ COMPLETED
```bash
# Create new file
touch src/services/category_service.py
```

**Status**: ✅ Geïmplementeerd in Phase 1-3 van category refactoring
- CategoryService met v2 interface
- CategoryStateManager voor UI state
- RegenerationService voor category-aware regeneration

**Geleerde lessen**:
- ServiceAdapter pattern werkt goed voor backward compatibility
- UI heeft tijd nodig voor volledige migratie
- Gradual migration voorkomt breaking changes

#### 2. WorkflowService Implementation ✅ COMPLETED
**Locatie**: `src/services/workflow_service.py` (bestaat al!)

**Status**: ✅ **COMPLETED** - `submit_for_review` method geïmplementeerd en getest

**Implementatie:**
```python
def submit_for_review(
    self, definition_id: int, user: str = "web_user", notes: str | None = None
) -> dict[str, Any]:
    """Submit een definitie voor review (DRAFT → REVIEW)."""
    return self.prepare_status_change(
        definition_id=definition_id,
        current_status=DefinitionStatus.DRAFT.value,
        new_status=DefinitionStatus.REVIEW.value,
        user=user,
        notes=notes or "Submitted for review via web interface",
    )
```

**Tests**: ✅ All tests pass in `tests/services/test_workflow_service.py`

#### 3. Session State Elimination - Clean Architecture Services ✅ COMPLETED
**Datum**: 2025-08-25
**Status**: ✅ **FULLY IMPLEMENTED**

**Problem Solved**: Services waren gekoppeld aan UI session state → onmogelijk te testen, tight coupling

**Solution**: Data Aggregation + Service Facade + Adapter Pattern

**Implemented Components:**

##### a. DataAggregationService ✅
**Locatie**: `src/services/data_aggregation_service.py`
```python
class DataAggregationService:
    def aggregate_definitie_for_export(
        self, 
        definitie_id: int = None,
        definitie_record: DefinitieRecord = None,
        additional_data: dict = None  # UI data als parameter
    ) -> DefinitieExportData:
        # NO SessionStateManager imports!
        # Aggregates data from repository + UI data
```

##### b. ExportService ✅ 
**Locatie**: `src/services/export_service.py`
```python
class ExportService:
    def export_definitie(
        self,
        definitie_id: int,
        additional_data: dict,  # From UI
        format: ExportFormat  # TXT/JSON/CSV
    ) -> str:
        # Pure business logic, multiple formats
        # NO UI dependencies
```

##### c. DefinitionUIService ✅
**Locatie**: `src/ui/services/definition_ui_service.py`
```python
class DefinitionUIService:
    def export_definition(
        self,
        definitie_id: int,
        ui_data: dict,
        format: str
    ) -> dict[str, Any]:
        # UI-friendly facade
        # Error handling + success messages
```

##### d. UIComponentsAdapter ✅
**Locatie**: `src/ui/components_adapter.py`
```python
class UIComponentsAdapter:
    def export_definition(self, format: str) -> bool:
        # Bridge to legacy UI
        ui_data = self._collect_ui_data_for_export()  # SessionState → dict
        result = self.service.export_definition(ui_data=ui_data)
        # Handle UI display
```

**Service Container Integration ✅**:
- Added to `ServiceContainer` with dependency injection
- Enhanced `ServiceAdapter` with export methods
- Backward compatibility maintained

**Testing Results ✅**:
- ✅ 6/6 DataAggregationService tests pass
- ✅ 8/9 ExportService tests pass (1 skipped - cleanup complexity)
- ✅ 8/8 Integration tests pass
- ✅ 0 SessionStateManager imports in business services
- ✅ 100% testable without UI mocks

**Usage Examples:**
```python
# For new code (clean)
service = get_definition_service()
result = service.export_definition(
    definition_id=1, 
    ui_data={"expert_review": "Good"}, 
    format="json"
)

# For legacy UI (backward compatible)
from ui.components_adapter import get_ui_adapter
adapter = get_ui_adapter()
success = adapter.export_definition(format="txt")
```

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

#### 2. Implement Adapter Pattern ✅ ALTERNATIVE IMPLEMENTATION
**Status**: ✅ Geïmplementeerd als ServiceAdapter in service_factory.py

**Huidige situatie**:
- Geen aparte AgentResultAdapter class
- ServiceAdapter biedt complete backward compatibility
- LegacyGenerationResult wrapt nieuwe service responses

**Waarom anders dan gepland**:
- Centralized adapter logic is cleaner
- Minder conversie code nodig
- UI hoeft niet aangepast voor adapter pattern

**Code locatie**: `src/services/service_factory.py`
```python
class ServiceAdapter:
    """Wraps V2 services met legacy interface"""
    def generate_definition(self, **kwargs):
        # Convert legacy naar V2 format
        # Call V2 service
        # Convert response naar LegacyGenerationResult
```

**Next steps**:
- Phase 6 van migration roadmap voor adapter removal
- Gradual UI component updates
- Maintain backward compatibility tot alle UI is gemigreerd

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

#### RegenerationService Implementation (COMPLETED)
**File**: `services/regeneration_service.py`

**Wat is geïmplementeerd:**
1. **RegenerationContext dataclass** - Houdt regeneratie context bij
   - begrip, old_category, new_category, previous_definition
   - `to_feedback_entry()` method voor GVI Rode Kabel integratie

2. **RegenerationService class** - Beheert category-aware regeneratie
   - `set_regeneration_context()` - Activeer regeneratie modus
   - `enhance_prompt_with_context()` - Voeg categorie context aan prompts toe
   - `get_feedback_history()` - Integratie met UnifiedPromptBuilder

3. **Database Layer Updates**:
   - UNIQUE constraint nu: (begrip, organisatorische_context, categorie)
   - `find_definitie()` met optionele categorie parameter
   - `find_duplicates()` met categorie filtering

4. **UI Components**:
   - `CategoryRegenerationHelper` - Dialoog voor regeneratie keuze
   - `RegenerationHandler` - State management voor regeneratie flow

**Integration met bestaande systemen:**
```python
# In UnifiedDefinitionGenerator
if regeneration_service.get_active_context():
    feedback_history = regeneration_service.get_feedback_history()
    prompt = prompt_builder.build_prompt(
        request, context, rules,
        feedback_history=feedback_history
    )
```

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

## 🧪 Category-Aware Regeneration Test Results

### Manual Test Suite Results:
1. **Repository Category-Aware Tests** ✅
   - `find_definitie()` met categorie parameter werkt
   - `find_duplicates()` filtert correct op categorie
   - Verschillende categorieën = geen duplicaat

2. **DefinitieChecker Integration** ✅
   - Category-aware duplicate detection geïntegreerd
   - CheckAction.CATEGORY_DIFFERS voor verschillende categorieën

3. **End-to-End Regeneration Flow** ✅
   - Gebruiker kan categorie wijzigen
   - Regeneratie optie wordt getoond
   - Nieuwe definitie met nieuwe categorie zonder blokkering

4. **Edge Cases** ✅
   - None categorie handling
   - Empty string categorie
   - Special characters in categorie

### Performance Impact:
- Geen merkbare performance degradatie
- Query's blijven snel door indexed columns

---

*Dit document complementeert het GVI Implementation Plan met concrete implementatie stappen.*
