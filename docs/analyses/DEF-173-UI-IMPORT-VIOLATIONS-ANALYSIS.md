# DEF-173: UI Import Violations Analysis

## ROOT CAUSE
SessionStateManager is a thin wrapper around Streamlit's session_state dictionary that exists in ui/ because it imports `streamlit as st`, but is being imported by services/database/utils layers for UI progress flags (validating_definition, saving_to_database, generating_definition). These imports violate layer separation but use "soft-fail" pattern to remain testable.

## ARCHITECTURAL ANALYSIS

### Current Location: `src/ui/session_state.py`
**Why it's in ui/:**
- Imports `streamlit as st` (line 11) - only Streamlit API used is `st.session_state`
- Has one UI-specific method: `initialize_session_state()` calls `ui.cached_services.initialize_services_once()` (line 80)
- Contains `force_cleanup_voorbeelden()` that directly manipulates `st.session_state` (DEF-110)
- Documented as "ONLY module allowed to touch st.session_state" (CLAUDE.md)

### Dependencies (what it depends on):
1. **Streamlit**: `import streamlit as st` - ONLY uses `st.session_state` (42 times)
2. **ui.cached_services**: `initialize_services_once()` - called during initialization
3. **ui.helpers.context_adapter**: `get_context_adapter()` - lazy import in `get_context_dict()` (line 206)

### Dependents (who depends on it):
**Total violations: 8 imports across 4 files**

1. **services/orchestrators/validation_orchestrator_v2.py (4 imports)**:
   - Lines 81, 130, 159, 205
   - Usage: Set/clear `validating_definition` flag for UI progress indicators
   - Pattern: Try-except "soft-fail if session state unavailable (e.g., in tests)"

2. **services/service_factory.py (1 import)**:
   - Line 471
   - Usage: Set/clear `generating_definition` flag
   - Pattern: Try-except soft-fail

3. **database/definitie_repository.py (2 imports)**:
   - Lines 552, 621
   - Usage: Set/clear `saving_to_database` flag
   - Pattern: Try-except soft-fail

4. **utils/voorbeelden_debug.py (1 import)**:
   - Line 103
   - Usage: Debug logging of session state for voorbeelden
   - Pattern: Try-except with early return if unavailable

### UI-Specific Code: YES
- `initialize_session_state()` - calls UI layer service initialization
- `force_cleanup_voorbeelden()` - widget cleanup for Streamlit reruns
- `get_export_data()` - aggregates UI form data
- `update_definition_results()`, `update_ai_content()` - UI result storage

**BUT**: Core get/set methods are generic key-value operations:
```python
get_value(key, default) → st.session_state.get(key, default)
set_value(key, value) → st.session_state[key] = value
```

## VIOLATION PATTERN ANALYSIS

**All 8 violations follow identical pattern:**
```python
try:
    from ui.session_state import SessionStateManager
    SessionStateManager.set_value("operation_flag", True/False)
except Exception:
    pass  # Soft-fail if session state unavailable (e.g., in tests)
```

**Purpose**: UI progress indicators for async operations:
- `validating_definition` - shows validation spinner
- `generating_definition` - shows generation spinner
- `saving_to_database` - shows save spinner

**Why soft-fail works:**
- Services remain testable without Streamlit context
- UI presence is optional (CLI/API usage scenarios)
- No business logic depends on these flags

## SOLUTION EVALUATION

### Option A: Move SessionStateManager to src/state/
**Effort: 6-8 hours**

**What needs to move:**
1. Extract core StateManager (200 LOC):
   - `get_value()`, `set_value()`, `clear_value()`
   - Generic state operations (no UI-specific logic)

2. Leave in ui/session_state.py (150 LOC):
   - `initialize_session_state()` - UI initialization
   - `force_cleanup_voorbeelden()` - widget cleanup
   - `update_definition_results()`, etc. - UI data aggregation
   - Imports new StateManager from src/state/

**Implementation:**
```
src/state/
  ├── __init__.py
  └── state_manager.py  # 200 LOC - NO streamlit import
      - BaseStateManager (abstract: get/set/clear)
      - StreamlitStateManager (concrete: wraps st.session_state)

src/ui/
  └── session_state.py  # 150 LOC - keeps Streamlit import
      - SessionStateManager (facade to state.StreamlitStateManager)
      - UI-specific methods (initialize, cleanup, update)
```

**Changes needed:**
- 8 imports: `from state.state_manager import StateManager`
- Pre-commit hook: Allow state/ layer
- Tests: Mock StateManager instead of SessionStateManager

**Pros:**
- Fixes layer violations (services → state, NOT services → ui)
- Maintains testability (soft-fail pattern preserved)
- No business logic changes
- StateManager becomes reusable (future FastAPI backend?)

**Cons:**
- Still tightly coupled to Streamlit's state dictionary
- Doesn't improve abstraction (still a thin wrapper)
- Two classes needed (BaseStateManager + StreamlitStateManager)
- CLAUDE.md updates: "SessionStateManager is ONLY..." → outdated

**Risks:**
- Circular dependency with ui.cached_services (initializes services)
- Breaking 49+ UI files importing SessionStateManager
- Tests expect SessionStateManager name

---

### Option B: Extract StateManager Interface
**Effort: 12-16 hours**

**Architecture:**
```python
# src/state/interfaces.py
class IStateManager(Protocol):
    def get(key: str, default: Any = None) -> Any: ...
    def set(key: str, value: Any) -> None: ...
    def clear(key: str) -> None: ...

# src/state/streamlit_state.py
class StreamlitStateBackend(IStateManager):
    """Streamlit-backed state (current behavior)"""
    def get(key, default): return st.session_state.get(key, default)
    def set(key, value): st.session_state[key] = value

# src/state/memory_state.py
class InMemoryStateBackend(IStateManager):
    """Dict-backed state (for tests/CLI)"""
    def __init__(self): self._state = {}
    def get(key, default): return self._state.get(key, default)
    def set(key, value): self._state[key] = value

# src/state/manager.py
class StateManager:
    _backend: IStateManager = None  # Injected

    @classmethod
    def set_backend(cls, backend: IStateManager): ...

    @classmethod
    def get_value(cls, key, default=None):
        return cls._backend.get(key, default)
```

**Usage in services:**
```python
# No more try-except needed!
from state.manager import StateManager
StateManager.set_value("validating_definition", True)
```

**Initialization:**
```python
# In main.py (Streamlit app)
from state.manager import StateManager
from state.streamlit_state import StreamlitStateBackend
StateManager.set_backend(StreamlitStateBackend())

# In tests
from state.manager import StateManager
from state.memory_state import InMemoryStateBackend
StateManager.set_backend(InMemoryStateBackend())
```

**Changes needed:**
- Create 4 new files: interfaces.py, manager.py, streamlit_state.py, memory_state.py
- Refactor ui/session_state.py → delegate to StateManager
- Update all 8 violation sites (remove try-except)
- Update 49+ UI imports (SessionStateManager → StateManager)
- Update tests (inject InMemoryStateBackend)
- Update CLAUDE.md (new architecture)

**Pros:**
- Clean abstraction (testable without mocking)
- Removes try-except soft-fail hacks
- Backend-agnostic (supports FastAPI/CLI)
- Proper dependency injection pattern
- Layer violations fixed with clean interface

**Cons:**
- Significant refactor (49+ files touched)
- Runtime overhead (backend indirection)
- More complex initialization (backend must be set before use)
- Overkill for single-backend system (only Streamlit used)
- Still doesn't fix tight coupling to session state pattern

**Risks:**
- Breaking changes across entire UI layer
- Initialization order critical (backend MUST be set first)
- Forget to set backend → runtime errors
- Test setup becomes more complex

---

### Option C: Full DI Pattern (Inject StateManager into Services)
**Effort: 20-30 hours**

**Architecture:**
```python
# Remove all direct StateManager imports from services

# src/services/orchestrators/validation_orchestrator_v2.py
class ValidationOrchestratorV2:
    def __init__(
        self,
        validation_service: ModularValidationService,
        state_manager: IStateManager | None = None  # Injected!
    ):
        self.state_manager = state_manager

    async def validate_text(self, text, begrip, context):
        if self.state_manager:
            self.state_manager.set("validating_definition", True)
        try:
            # ... validation logic ...
        finally:
            if self.state_manager:
                self.state_manager.set("validating_definition", False)

# src/services/container.py (ServiceContainer)
def __init__(self, state_manager: IStateManager | None = None):
    self.state_manager = state_manager

def get_validation_orchestrator(self):
    return ValidationOrchestratorV2(
        validation_service=self.get_validation_service(),
        state_manager=self.state_manager  # Propagate
    )
```

**Initialization:**
```python
# In main.py
state = StreamlitStateBackend()
container = ServiceContainer(state_manager=state)

# In tests
state = InMemoryStateBackend()
container = ServiceContainer(state_manager=state)
```

**Changes needed:**
- Update ServiceContainer constructor (add state_manager param)
- Update 6+ service constructors (ValidationOrchestratorV2, ServiceFactory, etc.)
- Remove 8 direct SessionStateManager imports
- Update ui/cached_services.py initialization
- Update all container creation sites
- Update 30+ tests (inject state_manager)

**Pros:**
- Textbook dependency injection (no imports, pure injection)
- Services fully testable without mocking
- No hidden dependencies
- Explicit state management contract
- Easy to swap backends (FastAPI, Redis, etc.)

**Cons:**
- MASSIVE refactor (100+ files touched)
- Breaking changes cascade through entire codebase
- Container initialization becomes complex
- Boilerplate: every service must accept + store state_manager
- Over-engineered for 8 progress flag usages

**Risks:**
- HIGH regression risk (100+ files changed)
- Tests break across the board
- Initialization order nightmares
- Forgot to inject → None checks everywhere
- Performance overhead (extra param in every service call)

---

## RECOMMENDATION: Option A (Move to src/state/)

**Why:**
1. **Effort/Benefit ratio**: 6-8h for clear layer compliance vs 12-30h for marginal improvements
2. **Minimal risk**: Only 8 import changes + create new module (vs 49-100+ files)
3. **Preserves testability**: Soft-fail pattern still works, just cleaner location
4. **Incremental improvement**: Can evolve to Option B later if FastAPI backend needed
5. **Aligns with CLAUDE.md philosophy**: "NO backwards compat" BUT "avoid massive refactors"

**What makes it sufficient:**
- Fixes the architectural violation (services → state, NOT services → ui)
- StateManager.get/set abstraction is backend-agnostic (even if only Streamlit used now)
- UI-specific code stays in ui/ (initialize, cleanup, update methods)
- Tests remain simple (mock state.StateManager instead of ui.SessionStateManager)

**What it doesn't fix (but that's OK):**
- Tight coupling to session state pattern (not a problem - it's the persistence layer)
- Try-except soft-fail pattern (actually a feature for testability!)
- Streamlit dependency (not going away - this is a Streamlit app)

**Implementation Plan (6-8h):**

**Phase 1: Create State Layer (2h)**
```
src/state/
  ├── __init__.py
  │   from .state_manager import StateManager
  │   __all__ = ["StateManager"]
  │
  └── state_manager.py (200 LOC)
      class StateManager:
          """Generic key-value state backend (Streamlit-backed)"""
          @staticmethod
          def get_value(key, default=None): ...
          @staticmethod
          def set_value(key, value): ...
          @staticmethod
          def clear_value(key): ...
```

**Phase 2: Update Violations (2h)**
```python
# services/orchestrators/validation_orchestrator_v2.py (4 sites)
- from ui.session_state import SessionStateManager
+ from state import StateManager

- SessionStateManager.set_value("validating_definition", True)
+ StateManager.set_value("validating_definition", True)

# Same for service_factory.py (1), definitie_repository.py (2), voorbeelden_debug.py (1)
```

**Phase 3: Refactor UI Session State (2h)**
```python
# src/ui/session_state.py (keep 150 LOC UI-specific code)
from state import StateManager

class SessionStateManager:
    """UI-specific session state with Streamlit widget support"""

    # Delegate core operations to StateManager
    get_value = StateManager.get_value
    set_value = StateManager.set_value
    clear_value = StateManager.clear_value

    # Keep UI-specific methods
    @staticmethod
    def initialize_session_state(): ...  # Calls cached_services

    @staticmethod
    def force_cleanup_voorbeelden(prefix): ...  # Widget cleanup

    @staticmethod
    def update_definition_results(...): ...  # UI aggregation
```

**Phase 4: Update Tests + Docs (2h)**
- Update 6 test files mocking SessionStateManager → mock StateManager
- Update CLAUDE.md Table 3 (Import Rules): `state/` layer allowed by all
- Update pre-commit hook: Allow `from state import`
- Run full test suite (pytest + pre-commit)

**Phase 5: Validation (1h)**
- Smoke test: Run app, generate definition, validate
- Check logs: No import errors
- Verify spinners work: Progress flags updating correctly
- Git grep: No remaining `from ui.session_state` in services/database/utils

**Total: 9h** (includes buffer)

---

## ALTERNATIVE: Do Nothing (0h)

**Arguments FOR keeping status quo:**
1. **It works**: Soft-fail pattern proven reliable for 6+ months
2. **Low priority**: No user-facing impact, no performance issue
3. **Technical debt**: Accepted in solo dev for velocity
4. **Future refactor**: Wait until FastAPI backend requirement (if ever)

**Arguments AGAINST:**
1. **Pre-commit violations**: Manual overrides needed
2. **Confusing architecture**: "Services can import UI??"
3. **Sets bad precedent**: Other violations creep in
4. **Hard to explain**: New devs confused by layer mixing

## EFFORT ESTIMATES

| Option | Time | Files Changed | Risk | Value |
|--------|------|---------------|------|-------|
| A: Move to src/state/ | 6-8h | 10 (8 violations + 2 new files) | LOW | HIGH |
| B: Interface extraction | 12-16h | 55+ (49 UI + 6 new) | MEDIUM | MEDIUM |
| C: Full DI | 20-30h | 100+ | HIGH | LOW |
| Do Nothing | 0h | 0 | None | None |

## RISKS

### Option A Risks:
- ⚠️ **Circular dependency**: state/ → ui/cached_services? (NO - state has no UI imports)
- ⚠️ **Test breakage**: 6 test files mock SessionStateManager (EASY FIX - update mocks)
- ⚠️ **Import confusion**: Two managers? (NO - SessionStateManager delegates to StateManager)

### Option B Risks:
- 🔴 **Backend initialization**: Forget to set backend → runtime crash
- 🔴 **Test complexity**: Every test needs backend setup
- ⚠️ **Breaking changes**: 49 UI files import SessionStateManager

### Option C Risks:
- 🔴 **Massive regression**: 100+ files changed, high bug risk
- 🔴 **Container complexity**: ServiceContainer initialization nightmare
- 🔴 **Test cascade**: Every test must inject state_manager
- ⚠️ **Performance**: Extra parameter passing overhead

## FINAL RECOMMENDATION

**Execute Option A: Move to src/state/** (6-8h)

**Rationale:**
1. Fixes architectural violation with minimal risk
2. Preserves all existing behavior (soft-fail, testability)
3. Incremental step toward cleaner architecture
4. Can evolve to Option B if requirements change (FastAPI, Redis)
5. Solo dev velocity: "Fix it properly, but don't overengineer"

**Next Steps:**
1. Get user approval (DEF-173 scope)
2. Create feature branch `DEF-173-state-layer`
3. Execute 5-phase plan
4. PR review: Focus on import changes + tests
5. Merge: Update CLAUDE.md to document new state/ layer
