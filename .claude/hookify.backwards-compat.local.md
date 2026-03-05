---
name: backwards-compat
enabled: true
event: file
action: warn
conditions:
  - field: file_content
    operator: regex_match
    # Detecteert backwards-compatibility hacks die niet nodig zijn in een solo-dev project:
    # - # removed/deleted comments
    # - # deprecated comments
    # - _unused_ prefix variabelen
    # - # legacy/backwards compat comments
    # - re-export patterns voor backwards compat
    pattern: (#\s*(removed|deleted|deprecated|legacy|backwards?\s*compat)|_unused_\w+|#\s*kept\s+for\s+(backwards?\s*)?compat|#\s*re-?export)
---

**BACKWARDS COMPATIBILITY HACK GEDETECTEERD**

Dit project is een **solo-developer applicatie** zonder externe gebruikers. Backwards compatibility hacks zijn niet nodig.

**Gedetecteerde patronen:**

| Patroon | Probleem |
|---------|----------|
| `# removed` / `# deleted` | Verwijder gewoon de code |
| `# deprecated` | Refactor in place |
| `_unused_var` | Delete unused code |
| `# kept for backwards compat` | Niet nodig, refactor |
| `# re-export for compat` | Niet nodig |

**Correcte aanpak:**
```python
# WRONG - backwards compat comment
# removed: old_function()
_unused_old_var = None  # kept for backwards compat

# CORRECT - gewoon verwijderen
# (geen code nodig - delete it!)
```

**Waarom deze regel:**
- Solo-dev project: geen externe API consumers
- Dead code maakt de codebase moeilijker te begrijpen
- "Backwards compat" comments worden nooit opgeruimd

**CLAUDE.md regel:**
> **No backwards compatibility** - Solo dev app, refactor in place

**Zie:** CLAUDE.md §Critical Rules
