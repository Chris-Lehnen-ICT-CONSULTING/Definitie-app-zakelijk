# Category Update Refactoring Plan

**Status**: ✅ Phase 1-4 COMPLETE (2025-08-25)

## ✅ Wat is gedaan:

### Phase 1: Domain Models ✅
- `DefinitionCategory` - Type-safe category model
- `CategoryChangeResult` - Rich result object
- `CategoryUpdateEvent` - Voor toekomstige event-driven architecture

### Phase 2: Service Layer ✅
- `CategoryService.update_category_v2()` - Met audit trail
- Backwards compatible met legacy method
- Business rule validation
- Better error messages

### Phase 3: Session State Management ✅
- `CategoryStateManager` - Centralized state management
- UI heeft geen directe session state mutations meer
- Voorbereid voor event-driven architecture

### Phase 4: Category-Aware Duplicate Detection ✅
- **RegenerationService** - Context management voor category-aware regeneratie
- **Database Schema Update** - UNIQUE constraint nu inclusief `categorie` veld
- **Repository Updates** - `find_definitie()` en `find_duplicates()` met categorie parameter
- **UI Flow Enhancement** - Regeneratie optie bij categorie wijziging
- **Integration met GVI Rode Kabel** - Feedback loop voor betere prompts

## 📊 Resultaten:
- **Type Safety**: ✅ Domain models in plaats van tuples
- **Audit Trail**: ✅ User, timestamp, reason tracking
- **Testing**: ✅ 11 nieuwe tests + uitgebreide manual tests voor regeneratie
- **Maintainability**: ✅ Clean separation of concerns
- **Core Fix**: ✅ Categorie wijzigingen worden niet meer geblokkeerd door duplicate detection

## 🚀 Nieuwe Regeneratie Flow:

1. **Gebruiker wijzigt categorie** → CategoryService.update_category_v2()
2. **UI toont regeneratie optie** → CategoryRegenerationHelper component
3. **Gebruiker kiest regeneratie** → RegenerationService.set_regeneration_context()
4. **Nieuwe definitie generatie** → Met categorie-aware duplicate check
5. **Success** → Nieuwe definitie met juiste categorie zonder blokkering

## ⏸️ Future Phases (nice-to-have):

## 1. Session State Probleem

**Huidige code:**
```python
# In _update_category
generation_result["determined_category"] = new_category
SessionStateManager.set_value("last_generation_result", generation_result)
```

**Probleem**: Session state wordt gebruikt als data store

**Oplossing**: Event-driven architecture
```python
class CategoryUpdateEvent:
    def __init__(self, definition_id: int, old_category: str, new_category: str):
        self.definition_id = definition_id
        self.old_category = old_category
        self.new_category = new_category
        self.timestamp = datetime.now()

class EventBus:
    def publish(self, event: CategoryUpdateEvent):
        # Notify all subscribers
        pass
```

## 2. Ontology Integration

**Huidige situatie**:
- `OntologicalAnalyzer` bepaalt categorie
- Maar CategoryService weet hier niets van

**Oplossing**:
```python
class CategoryService:
    def __init__(self, repository, ontological_analyzer):
        self.repository = repository
        self.analyzer = ontological_analyzer

    async def determine_category(self, begrip: str, context: dict) -> tuple[str, dict]:
        """Bepaal categorie via ontological analyzer."""
        category, analysis = await self.analyzer.analyze(begrip, context)
        return category.value, analysis
```

## 3. Legacy Dependencies

### Te vervangen:
1. **DefinitieZoekerAdapter** → Direct `ModernWebLookupService` gebruik
2. **Session state voor category** → Domain events
3. **generation_result dict** → Typed domain model

### Nieuwe componenten nodig:
```python
@dataclass
class DefinitionCategory:
    """Domain model voor categorie."""
    code: str  # ENT, REL, etc.
    display_name: str
    reasoning: str
    confidence: float
    analysis_details: dict

class CategoryDomainService:
    """Business logic voor category operaties."""

    async def change_category(
        self,
        definition_id: int,
        new_category: str,
        user: str,
        reason: str
    ) -> CategoryChangeResult:
        # 1. Validate change allowed
        # 2. Create audit entry
        # 3. Update definition
        # 4. Publish event
        # 5. Return result
```

## 4. UI Decoupling

**Nu**: UI kent business logic details
**Doel**: UI alleen presentation

```python
# UI component
class CategoryPresenter:
    def __init__(self, category_service: CategoryService):
        self.service = category_service

    def render_category_section(self, definition_id: int):
        # Get current category
        category = self.service.get_current_category(definition_id)

        # Render UI
        st.info(f"Categorie: {category.display_name}")

        # Handle change
        if st.button("Wijzig"):
            new_cat = st.selectbox("Nieuwe categorie", self.service.get_categories())
            result = self.service.update_category(definition_id, new_cat)

            if result.success:
                st.success(result.message)
            else:
                st.error(result.error)
```

## 5. Testing Strategy

### Unit Tests Needed:
- [ ] CategoryDomainService tests
- [ ] Event publishing tests
- [ ] Legacy adapter removal tests

### Integration Tests:
- [ ] Full category change flow
- [ ] Ontology analyzer integration
- [ ] UI interaction tests

## Implementation Steps

### Phase 1: Domain Model (2 uur)
1. Create `DefinitionCategory` model
2. Create `CategoryChangeResult` model
3. Create `CategoryUpdateEvent`

### Phase 2: Service Layer (4 uur)
1. Extend CategoryService met ontology integration
2. Implement CategoryDomainService
3. Add event publishing

### Phase 3: Remove Legacy (2 uur)
1. Remove DefinitieZoekerAdapter
2. Remove session state usage
3. Replace generation_result dict

### Phase 4: UI Refactor (2 uur)
1. Create CategoryPresenter
2. Remove business logic from UI
3. Use only service calls

## Success Metrics

- [ ] Zero direct session state mutations for category
- [ ] All category changes via service layer
- [ ] Legacy adapters removed
- [ ] Full test coverage
- [ ] Event-driven updates working
