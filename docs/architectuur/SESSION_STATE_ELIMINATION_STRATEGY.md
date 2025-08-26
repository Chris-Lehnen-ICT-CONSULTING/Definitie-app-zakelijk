# Session State Elimination Strategy

## Overzicht

Dit document beschrijft de bewezen strategie voor het elimineren van session state dependencies uit business services, terwijl backward compatibility behouden blijft. Deze aanpak is succesvol toegepast in de Definitie-app en kan worden hergebruikt voor vergelijkbare refactoring uitdagingen.

## Probleem Definitie

### Symptomen van Session State Lekkage
- Services die direct `SessionStateManager` importeren
- Business logic gekoppeld aan UI state
- Moeilijk testbare services
- Circular dependencies tussen UI en business layers
- Violation van Clean Architecture principes

### Architecturale Issues
```python
# PROBLEMATISCH PATROON
class ExportService:
    def export_definition(self):
        # ❌ Direct UI dependency
        data = SessionStateManager.get_export_data()
        # ❌ Business logic gekoppeld aan UI state
```

## Oplossings Strategie

### 1. Data Aggregation Service Pattern

Creëer een service die data verzamelt uit verschillende bronnen zonder UI dependencies:

```python
@dataclass
class ExportData:
    """Clean data container zonder UI dependencies."""
    begrip: str
    definitie: str
    metadata: dict[str, Any]
    context: dict[str, list[str]]
    # ... meer velden

class DataAggregationService:
    """Centraliseert data verzameling."""

    def __init__(self, repository: Repository):
        self.repository = repository  # Alleen dependency injection

    def aggregate_for_export(
        self,
        record_id: Optional[int] = None,
        record: Optional[Record] = None,
        additional_data: Optional[dict] = None
    ) -> ExportData:
        """Aggregeert data uit verschillende bronnen."""
        # Haal data op uit database
        if record is None and record_id:
            record = self.repository.get_by_id(record_id)

        # Merge met additional data (van UI)
        export_data = ExportData(...)
        if additional_data:
            self._merge_additional_data(export_data, additional_data)

        return export_data
```

### 2. Service Layer Pattern

Bouw business services bovenop de data aggregation service:

```python
class ExportService:
    """Clean export service zonder UI dependencies."""

    def __init__(
        self,
        repository: Repository,
        data_service: DataAggregationService
    ):
        self.repository = repository
        self.data_service = data_service

    def export_to_format(
        self,
        record_id: int = None,
        additional_data: dict = None,
        format: str = "json"
    ) -> str:
        """Export zonder session state dependencies."""
        # Aggregeer data
        export_data = self.data_service.aggregate_for_export(
            record_id=record_id,
            additional_data=additional_data
        )

        # Export naar gewenst formaat
        return self._export_to_format(export_data, format)
```

### 3. UI Facade Pattern

Creëer een facade die UI operaties afhandelt zonder business logic:

```python
class UIService:
    """Facade voor UI operaties."""

    def __init__(
        self,
        repository: Repository,
        export_service: ExportService,
        # ... andere services
    ):
        self.repository = repository
        self.export_service = export_service

    def export_from_ui(
        self,
        record_id: int = None,
        ui_data: dict = None,
        format: str = "json"
    ) -> dict[str, Any]:
        """UI-friendly export method."""
        try:
            # Transform UI data naar clean format
            clean_data = self._prepare_ui_data(ui_data)

            # Delegate naar business service
            result_path = self.export_service.export_to_format(
                record_id=record_id,
                additional_data=clean_data,
                format=format
            )

            return {
                "success": True,
                "path": result_path,
                "message": "Export succesvol"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Export mislukt"
            }
```

### 4. Adapter Pattern voor Backward Compatibility

Gebruik adapters om bestaande interfaces te behouden:

```python
class UIComponentsAdapter:
    """Adapter tussen legacy UI en nieuwe services."""

    def __init__(self):
        self.ui_service = get_ui_service()

    def export_definition_legacy(self, format: str = "txt") -> bool:
        """Legacy compatible export method."""
        try:
            # Verzamel data uit session state (tijdelijk)
            ui_data = self._collect_from_session_state()

            # Roep nieuwe service aan
            result = self.ui_service.export_from_ui(
                ui_data=ui_data,
                format=format
            )

            # Handle result voor UI
            if result["success"]:
                st.success(result["message"])
                return True
            else:
                st.error(result["message"])
                return False

        except Exception as e:
            st.error(f"Fout: {e}")
            return False

    def _collect_from_session_state(self) -> dict:
        """Verzamel UI data (temporary bridge)."""
        return {
            "field1": SessionStateManager.get_value("field1"),
            "field2": SessionStateManager.get_value("field2"),
            # ... etc
        }
```

### 5. Service Container Integration

Integreer nieuwe services in de DI container:

```python
class ServiceContainer:
    def data_aggregation_service(self):
        if "data_service" not in self._instances:
            repo = self.repository()
            self._instances["data_service"] = DataAggregationService(repo)
        return self._instances["data_service"]

    def export_service(self):
        if "export_service" not in self._instances:
            repo = self.repository()
            data_service = self.data_aggregation_service()
            self._instances["export_service"] = ExportService(repo, data_service)
        return self._instances["export_service"]

    def ui_service(self):
        if "ui_service" not in self._instances:
            repo = self.repository()
            export_service = self.export_service()
            self._instances["ui_service"] = UIService(repo, export_service)
        return self._instances["ui_service"]
```

## Implementation Roadmap

### Phase 1: Preparation
1. **Analyse current session state usage**
   ```bash
   grep -r "SessionStateManager" src/ --include="*.py"
   ```

2. **Identify data flows**
   - Welke data wordt opgeslagen in session state?
   - Waar wordt deze data gebruikt?
   - Welke business logic is afhankelijk van UI state?

3. **Design clean data structures**
   ```python
   @dataclass
   class CleanDataStructure:
       # Pure data, geen UI objecten
       field1: str
       field2: list[str]
       metadata: dict[str, Any]
   ```

### Phase 2: Service Creation
1. **Create Data Aggregation Service**
   - Centraliseer data verzameling
   - Geen UI dependencies
   - Testbare interface

2. **Create Business Services**
   - Build bovenop data service
   - Pure business logic
   - Framework agnostic

3. **Create UI Facade**
   - UI-friendly interface
   - Error handling
   - Result transformation

### Phase 3: Integration
1. **Add to Service Container**
   - Dependency injection
   - Singleton management
   - Configuration support

2. **Create Adapters**
   - Backward compatibility
   - Gradual migration
   - Legacy interface preservation

3. **Update existing adapters**
   - Extend ServiceAdapter
   - Add new methods
   - Maintain compatibility

### Phase 4: Testing
1. **Unit Tests**
   ```python
   def test_service_without_session_state():
       # Pure data input
       service = DataService(mock_repo)
       result = service.aggregate_data(
           record_id=1,
           additional_data={"clean": "data"}
       )
       assert result.field1 == "expected"
   ```

2. **Integration Tests**
   ```python
   def test_no_session_state_imports():
       import inspect
       source = inspect.getsource(service_module)
       assert "SessionStateManager" not in source
   ```

3. **Boundary Tests**
   ```python
   def test_clean_architecture_boundaries():
       service = BusinessService()
       assert not hasattr(service, 'session_state')
       assert not hasattr(service, 'ui_components')
   ```

### Phase 5: Migration
1. **Create UI Adapters**
   - Bridge legacy UI
   - Temporary session state collection
   - Clean service calls

2. **Update UI Components** (geleidelijk)
   ```python
   # Legacy (keep working)
   def render_export_button_legacy():
       if SessionStateManager.has_data():
           # ... legacy code

   # New (optional)
   def render_export_button_new():
       adapter = get_ui_adapter()
       adapter.export_definition(format="json")
   ```

3. **Feature Flags**
   ```python
   USE_CLEAN_SERVICES = os.getenv("USE_CLEAN_SERVICES", "true")

   if USE_CLEAN_SERVICES:
       render_export_button_new()
   else:
       render_export_button_legacy()
   ```

## Testing Strategy

### 1. Service Isolation Tests
```python
def test_service_isolation():
    """Services moeten werken zonder externe dependencies."""
    service = DataService(mock_repository)

    # Pure data input
    result = service.process_data({"clean": "input"})

    # Verifiable output
    assert isinstance(result, CleanDataStructure)
    assert result.field1 == "expected_value"
```

### 2. No UI Dependencies Tests
```python
def test_no_ui_imports():
    """Services mogen geen UI modules importeren."""
    import inspect
    from services import business_service

    source = inspect.getsource(business_service)

    # Verify no UI imports
    ui_modules = ["streamlit", "SessionStateManager", "ui.components"]
    for module in ui_modules:
        assert module not in source
```

### 3. Architecture Boundary Tests
```python
def test_architecture_boundaries():
    """Test dat layers correct gescheiden zijn."""
    # Services layer
    service = BusinessService()
    assert not hasattr(service, 'render')
    assert not hasattr(service, 'session_state')

    # UI layer mag services gebruiken
    ui_adapter = UIAdapter()
    assert hasattr(ui_adapter, 'service')
```

### 4. Integration Tests
```python
def test_end_to_end_without_session_state():
    """Test complete flow zonder session state."""
    # Arrange: Clean input data
    input_data = {"field": "value"}

    # Act: Through service chain
    result = service_factory.create_service().process(input_data)

    # Assert: Expected output
    assert result["success"] is True
```

## Benefits

### Immediate Benefits
- **Testability**: Services kunnen getest worden met pure data
- **Decoupling**: UI en business logic zijn onafhankelijk
- **Flexibility**: Services kunnen gebruikt worden in verschillende contexts

### Long-term Benefits
- **Maintainability**: Clearer separation of concerns
- **Scalability**: Services kunnen hergebruikt worden
- **Framework Independence**: Business logic niet gebonden aan UI framework

## Common Pitfalls

### 1. Incomplete Data Transfer
**Problem**: Vergeten om alle benodigde data mee te geven
```python
# ❌ Incomplete
ui_data = {"field1": value}  # field2 ontbreekt

# ✅ Complete
ui_data = self._collect_all_ui_data()
```

### 2. Hidden UI Dependencies
**Problem**: Indirecte dependencies via imports
```python
# ❌ Hidden dependency
from utils.helpers import get_current_user  # gebruikt session state intern

# ✅ Explicit dependency
def process_data(user: str, data: dict):
    # Explicit parameter
```

### 3. Mixing Concerns in Adapters
**Problem**: Business logic in adapter layer
```python
# ❌ Business logic in adapter
class UIAdapter:
    def export(self):
        data = self._collect_ui_data()
        # ❌ Complex business logic hier
        processed = self._complex_processing(data)
        return self.service.export(processed)

# ✅ Adapter is thin
class UIAdapter:
    def export(self):
        data = self._collect_ui_data()
        # ✅ Delegate alles naar service
        return self.service.export_from_ui(data)
```

## Monitoring Success

### Metrics to Track
1. **Import Analysis**: Aantal services met UI imports
2. **Test Coverage**: Percentage unit tests zonder mocks
3. **Code Coupling**: Cyclomatic complexity tussen layers
4. **Migration Progress**: Percentage legacy UI code vervangen

### Success Criteria
- [ ] Geen SessionStateManager imports in services
- [ ] Alle services unit testbaar zonder UI mocks
- [ ] UI componenten kunnen services gebruiken zonder legacy code
- [ ] Backward compatibility behouden voor bestaande features

## Conclusion

Deze session state elimination strategy biedt een bewezen aanpak voor het refactoren van tightly-coupled UI/business logic naar een clean, testable architecture. Door gebruik te maken van data aggregation services, facades, en adapters kunnen we geleidelijk migreren zonder breaking changes.

**Key Takeaway**: Start met data aggregation, bouw clean services, gebruik adapters voor compatibility, en migreer geleidelijk.

## References

- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Facade Pattern](https://refactoring.guru/design-patterns/facade)
- [Adapter Pattern](https://refactoring.guru/design-patterns/adapter)
- [Strangler Fig Pattern](https://martinfowler.com/bliki/StranglerFigApplication.html)
