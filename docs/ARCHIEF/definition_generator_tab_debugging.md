# 🐛 Debugging Guide: definition_generator_tab.py

## Common Issues & Solutions

### 1. **"Definitie niet zichtbaar" Issue**

**Symptoom**: Gebruiker ziet geen definitie of alleen één versie

**Debug Steps**:
```python
# Voeg debug logging toe in _render_generation_results
logger.info(f"Agent result type: {type(agent_result)}")
logger.info(f"Is dict: {isinstance(agent_result, dict)}")
if isinstance(agent_result, dict):
    logger.info(f"Keys in dict: {list(agent_result.keys())}")
    logger.info(f"Has origineel: {'definitie_origineel' in agent_result}")
    logger.info(f"Has gecorrigeerd: {'definitie_gecorrigeerd' in agent_result}")
```

**Mogelijke oorzaken**:
1. Legacy format wordt gebruikt (geen dict)
2. Keys ontbreken in dict
3. UI state niet correct geüpdatet

### 2. **Session State Corruption**

**Symptoom**: Oude data blijft hangen, verkeerde resultaten

**Debug Steps**:
```python
# Voeg session state debugger toe
def debug_session_state():
    st.sidebar.markdown("### 🐛 Session State Debug")

    critical_keys = [
        "last_generation_result",
        "last_check_result",
        "selected_definition",
        "begrip",
        "determined_category"
    ]

    for key in critical_keys:
        value = SessionStateManager.get_value(key)
        if value:
            st.sidebar.write(f"**{key}**: {type(value).__name__}")
            if isinstance(value, dict):
                st.sidebar.write(f"  Keys: {list(value.keys())[:5]}")
```

### 3. **Type Mismatch Errors**

**Symptoom**: AttributeError of KeyError exceptions

**Prevention Pattern**:
```python
# Safe attribute/key access pattern
def safe_get_score(agent_result):
    """Veilig score ophalen ongeacht format."""
    if isinstance(agent_result, dict):
        return agent_result.get("validation_score",
               agent_result.get("final_score", 0.0))
    elif hasattr(agent_result, "final_score"):
        return agent_result.final_score
    else:
        logger.warning(f"Unknown agent_result format: {type(agent_result)}")
        return 0.0
```

### 4. **Export Failures**

**Symptoom**: Export knop werkt niet of geeft foutmelding

**Debug Checklist**:
1. ✓ Export directory bestaat?
2. ✓ Write permissions?
3. ✓ Alle required session state values aanwezig?
4. ✓ Import paths correct?

```python
# Enhanced export debug
def debug_export_data():
    """Check of alle export data aanwezig is."""
    required_fields = [
        "begrip", "definitie_gecorrigeerd", "organisatorische_context",
        "beoordeling_gen", "voorbeeld_zinnen"
    ]

    missing = []
    for field in required_fields:
        if not SessionStateManager.get_value(field):
            missing.append(field)

    if missing:
        st.error(f"❌ Missing export data: {', '.join(missing)}")
        return False
    return True
```

### 5. **Category Update Not Working**

**Symptoom**: Ontologische categorie update wordt niet opgeslagen

**Debug Pattern**:
```python
def _update_category_with_logging(self, new_category: str, generation_result: dict):
    """Update met uitgebreide logging."""
    logger.info(f"Updating category from {generation_result.get('determined_category')} to {new_category}")

    # Check database connection
    try:
        repo = get_definitie_repository()
        logger.info("Database connection OK")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        st.error("❌ Kan geen verbinding maken met database")
        return

    # Update with verification
    saved_record = generation_result.get("saved_record")
    if saved_record and hasattr(saved_record, 'id'):
        try:
            # Get fresh record
            fresh_record = repo.get_definitie(saved_record.id)
            if fresh_record:
                fresh_record.categorie = new_category
                success = repo.update_definitie(fresh_record)
                logger.info(f"Category update success: {success}")
        except Exception as e:
            logger.exception("Category update failed")
```

## 🔍 Performance Profiling

### Identify Slow Sections
```python
import time
from functools import wraps

def profile_method(func):
    """Decorator voor performance profiling."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start

        if duration > 0.5:  # Log slow operations
            logger.warning(f"{func.__name__} took {duration:.2f}s")

        return result
    return wrapper

# Usage
@profile_method
def _render_generation_results(self, generation_result):
    # Method implementation
```

### Memory Leak Detection
```python
import gc
import sys

def check_memory_usage():
    """Check voor memory leaks in session state."""

    # Count objects
    obj_counts = {}
    for obj in gc.get_objects():
        obj_type = type(obj).__name__
        obj_counts[obj_type] = obj_counts.get(obj_type, 0) + 1

    # Check session state size
    session_size = sys.getsizeof(st.session_state)

    # Waarschuwing bij grote session state
    if session_size > 1_000_000:  # 1MB
        st.warning(f"⚠️ Session state is groot: {session_size:,} bytes")

    # Top memory users
    sorted_counts = sorted(obj_counts.items(), key=lambda x: x[1], reverse=True)
    st.write("Top 10 object types in memory:")
    for obj_type, count in sorted_counts[:10]:
        st.write(f"- {obj_type}: {count:,}")
```

## 🛠️ Quick Fixes

### 1. Fix Unused Parameter Warning
```python
# Before
def _edit_existing_definition(self, definitie: DefinitieRecord):
    st.info("🔄 Navigating to edit interface...")

# After
def _edit_existing_definition(self, definitie: DefinitieRecord):
    st.info(f"🔄 Navigating to edit interface for definitie {definitie.id}...")
    SessionStateManager.set_value("edit_definition_id", definitie.id)
```

### 2. Fix Import Inside Function
```python
# Move to top of file
import os
import traceback
from export.export_txt import exporteer_naar_txt
from database.definitie_repository import get_definitie_repository
from ui.components.prompt_debug_section import PromptDebugSection
```

### 3. Fix Loop Variable Not Used
```python
# Before
for i, voorbeeld in enumerate(voorbeelden["practical"], 1):
    st.info(voorbeeld)

# After
for voorbeeld in voorbeelden["practical"]:
    st.info(voorbeeld)
```

## 🚨 Production Issues Checklist

Als de UI niet werkt in productie:

1. **Check API Response Format**
   - Is de API response format veranderd?
   - Zijn alle expected keys aanwezig?

2. **Verify Feature Flags**
   - Is USE_NEW_SERVICES flag correct?
   - Match UI expectations met backend service?

3. **Session State Reset**
   ```python
   # Emergency session state reset
   if st.button("🚨 Reset Session (Debug)"):
       for key in list(st.session_state.keys()):
           del st.session_state[key]
       st.rerun()
   ```

4. **Check Browser Console**
   - JavaScript errors?
   - Network failures?
   - CORS issues?

## 📊 Monitoring Recommendations

1. **Add Structured Logging**
```python
import structlog

logger = structlog.get_logger()

# Log met context
logger.info("generation_completed",
    begrip=begrip,
    score=score,
    duration=duration,
    format_type="dict" if is_dict else "legacy"
)
```

2. **Add Health Checks**
```python
def health_check():
    """UI component health check."""
    checks = {
        "session_state": len(st.session_state) < 100,
        "database": check_db_connection(),
        "api": check_api_availability()
    }

    return all(checks.values()), checks
```

3. **User Action Tracking**
```python
def track_user_action(action: str, details: dict = None):
    """Track user interactions voor debugging."""
    timestamp = datetime.now().isoformat()

    action_log = SessionStateManager.get_value("action_log", [])
    action_log.append({
        "timestamp": timestamp,
        "action": action,
        "details": details or {}
    })

    # Keep last 50 actions
    if len(action_log) > 50:
        action_log = action_log[-50:]

    SessionStateManager.set_value("action_log", action_log)
```

Deze debugging guide helpt bij het snel identificeren en oplossen van problemen in productie.
