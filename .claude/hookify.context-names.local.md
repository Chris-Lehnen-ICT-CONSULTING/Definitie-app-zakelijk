---
name: context-names
enabled: true
event: file
action: warn
conditions:
  - field: file_content
    operator: regex_match
    # Detecteert Engelse context namen die Nederlands moeten zijn
    # organizational_context → organisatorische_context
    # legal_context → juridische_context
    pattern: \b(organizational_context|legal_context)\b
---

**ENGELSE CONTEXT NAAM GEDETECTEERD**

Dit project gebruikt **Nederlandse** context namen voor domein-specifieke variabelen.

**Correcte namen:**

| Verboden (Engels) | Correct (Nederlands) |
|-------------------|---------------------|
| `organizational_context` | `organisatorische_context` |
| `legal_context` | `juridische_context` |

**Voorbeeld:**
```python
# CORRECT
organisatorische_context = "De gemeente Amsterdam..."
juridische_context = "Conform de Awb artikel 3:46..."

# WRONG
organizational_context = "..."  # Engels!
legal_context = "..."           # Engels!
```

**Waarom Nederlandse namen:**
- Dit is een Nederlandse applicatie voor Nederlandse gebruikers
- Domeinbegrippen in het Nederlands sluiten aan bij de business context
- Consistentie met bestaande codebase

**Zie:** CLAUDE.md §Canonical Names
