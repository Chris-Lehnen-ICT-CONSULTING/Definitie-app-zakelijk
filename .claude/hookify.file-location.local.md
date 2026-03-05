---
name: file-location
enabled: true
event: file
action: warn
conditions:
  - field: file_path
    operator: regex_match
    # Detecteert bestanden op verkeerde locaties:
    # - test_*.py of *_test.py buiten tests/
    # - run_*.py of *_script.py buiten scripts/
    # Negative lookahead voorkomt false positives voor correcte locaties
    pattern: ^(?!tests/).*(?:test_[^/]+\.py|[^/]+_test\.py)$|^(?!scripts/).*(?:run_[^/]+\.py|[^/]+_script\.py)$
---

**BESTAND OP VERKEERDE LOCATIE**

Dit bestand lijkt op de verkeerde plek te staan volgens de project structuur.

**Vereiste locaties:**

| Type | Patroon | Vereiste Locatie |
|------|---------|------------------|
| Tests | `test_*.py`, `*_test.py` | `tests/` |
| Scripts | `run_*.py`, `*_script.py` | `scripts/` |
| Logs | `*.log` | `logs/` |
| Database | `*.db` | `data/` |
| Docs | `*.md` (niet README/CLAUDE) | `docs/` |

**Test bestanden:**
```bash
# CORRECT
tests/unit/test_validation.py
tests/integration/test_api.py

# WRONG
src/test_validation.py      # In src/!
test_quick.py               # In root!
```

**Script bestanden:**
```bash
# CORRECT
scripts/run_app.sh
scripts/db/run_migration.py

# WRONG
src/run_export.py           # In src/!
run_quick.py                # In root!
```

**Waarom deze regel:**
- Consistente structuur maakt navigatie eenvoudiger
- pytest vindt tests automatisch in `tests/`
- Scripts zijn gescheiden van applicatie code

**Zie:** CLAUDE.md §File Locations
