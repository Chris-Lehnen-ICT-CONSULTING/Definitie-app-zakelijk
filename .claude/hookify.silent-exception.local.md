---
name: silent-exception
enabled: true
event: file
action: block
conditions:
  - field: file_content
    operator: regex_match
    # Detecteert silent exception patronen: except Exception: pass/return/...
    # Reden: 150+ cleanup fixes nodig geweest (DEF-187, DEF-215, DEF-219, DEF-229, DEF-248)
    pattern: except\s+(Exception|BaseException)\s*:?\s*\n\s*(pass|return\s|return$|\.\.\.)
---

**SILENT EXCEPTION GEDETECTEERD**

Je schrijft een `except Exception: pass/return/...` patroon. Dit is **verboden** in deze codebase.

**Waarom geblokkeerd:**
Silent exceptions verbergen fouten en maken debugging onmogelijk. We hebben 150+ van deze patronen moeten opruimen (zie Linear: DEF-187, DEF-215, DEF-219, DEF-229, DEF-248).

**Correcte alternatieven:**

1. **Specificeer het exception type:**
   ```python
   except (TypeError, ValueError) as e:
       logger.warning(f"Context: {e}")
   ```

2. **Voeg logging toe bij brede catch:**
   ```python
   except Exception as e:
       logger.exception("Unexpected error in [context]")
       raise  # of return met logging
   ```

3. **Gebruik contextlib.suppress met comment:**
   ```python
   # Intentioneel: [reden waarom suppress OK is]
   with contextlib.suppress(KeyError):
       del cache[key]
   ```

**Zie ook:** CLAUDE.md en `docs/analysis/SILENT_FAILURES_INVENTORY.md`
