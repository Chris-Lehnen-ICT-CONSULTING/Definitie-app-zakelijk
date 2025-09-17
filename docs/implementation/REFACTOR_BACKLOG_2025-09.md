# 🔧 Refactor Backlog - Sprint 37 Preparation
**Generated:** 2025-09-16
**Priority:** HIGH
**Target:** Sprint 37 (voor legacy deprecation deadline)

## 🎯 Quick Wins (Day 1)
| Task | Effort | Impact | Files |
|------|--------|--------|-------|
| Unify ValidationResult types | 2h | HIGH | `src/validation/types.py` (new), 3 validator files |
| Fix Workflow adapter | 1h | MEDIUM | `src/services/definition_workflow_service.py:update_status()` |
| Replace sync wrapper calls | 2h | HIGH | 3 files met `generate_definition_sync` |
| Cache ServiceContainer | 30m | HIGH | `@st.cache_resource` in UI components |

## 📋 Priority Patches (Day 2-3)

### Patch 1: ValidationResult Consolidation
```python
# NEW: src/validation/types.py
@dataclass
class ValidationResult:
    is_valid: bool
    score: float = 0.0
    violations: list[ValidationViolation] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

# Update imports in:
# - src/validation/input_validator.py
# - src/validation/definitie_validator.py
# - src/validation/dutch_text_validator.py
```

### Patch 2: Async Bridge Update
```python
# UPDATE: src/ui/components/definition_generator_tab.py
# REMOVE: service_result = generate_definition_sync(...)
# ADD:
from ui.helpers.async_bridge import run_async
service_result = run_async(
    service_adapter.generate_definition(begrip, context_dict),
    timeout=120
)
```

### Patch 3: Draft Management Implementation
```python
# UPDATE: src/services/definition_repository.py
def get_or_create_draft(self, begrip: str, context: dict) -> int:
    """Garandeer één draft per combinatie."""
    with self._transaction() as conn:
        try:
            cursor = conn.execute(
                "INSERT INTO definities (begrip, organisatorische_context, "
                "juridische_context, categorie, status) VALUES (?, ?, ?, ?, ?)",
                (begrip, context.get("organisatorische_context"),
                 context.get("juridische_context", ""),
                 context.get("categorie", "proces"), "draft")
            )
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Draft exists, fetch it
            ...
```

## 🚀 Deployment Checklist

### Pre-Sprint 37
- [ ] Run `bash scripts/check-legacy-patterns.sh` - moet 0 warnings geven
- [ ] ValidationResult types geconsolideerd
- [ ] Alle `generate_definition_sync` calls vervangen
- [ ] ServiceContainer caching actief
- [ ] Draft management werkend (US-064)

### Testing Voordat Live
```bash
# Quick validation
pytest tests/services/test_service_factory.py -v
pytest tests/ui/test_async_bridge.py -v
pytest tests/validation/ -k "ValidationResult" -v

# Legacy pattern check
bash scripts/check-legacy-patterns.sh

# Performance check
python scripts/validation/validation-status-updater.py
```

## 📊 Impact Analysis

| Component | Voor | Na | Verbetering |
|-----------|------|-----|-------------|
| Service Init | 6x per session | 1x cached | 83% reductie |
| Validation Types | 3 verschillende | 1 unified | 100% consistent |
| Async Handling | Mixed sync/async | Pure async bridge | Clean architecture |
| Draft Management | Session state | Database-driven | Stateless |
| CI Gates | 1 warning | 0 warnings | Sprint 37 ready |

## 🔍 Verificatie Commands

```bash
# Check geen legacy patterns
rg "generation_result" src/ui --type py
rg "\.best_iteration" src --type py
rg "asyncio\.run" src/services --type py
rg "import streamlit" src/services --type py

# Check nieuwe patterns
rg "from ui.helpers.async_bridge import run_async" src/ui --type py
rg "ValidationResult" src/validation/types.py

# Database schema check
sqlite3 data/definities.db ".schema definities" | grep UNIQUE
```

## ⚠️ Rollback Plan

Als iets misgaat:
1. Git stash changes: `git stash`
2. Restore ServiceFactory sync wrappers (tijdelijk)
3. Re-enable legacy ValidationResult imports
4. Report issues in backlog voor volgende sprint

## 📝 Notes

- **BELANGRIJK:** Geen nieuwe backwards compatibility toevoegen
- Focus op refactor, niet op nieuwe features
- Test coverage moet minimaal gelijk blijven
- Alle changes via feature branch, niet direct op main

---
*Sprint 37 Deadline Compliance - Zero Legacy Patterns Required*