# Silent Exception Hookify Regel Implementatie

## Execution Mode
- **ULTRATHINK**: Nee (simpele taak)
- **MULTIAGENT**: Nee (1 bestand, duidelijke spec)
- **CONSENSUS**: Nee

## Opdracht

Implementeer een hookify regel die voorkomt dat Claude silent exception patronen schrijft.

**Te blokkeren patronen:**
```python
except Exception:
    pass

except Exception:
    return {}

except Exception:
    return None

except Exception:
    ...
```

## Context

**Codebase:** Definitie-app
**Reden:** 150+ silent exception fixes waren nodig (DEF-187, DEF-215, DEF-219, DEF-229, DEF-248). Preventie is beter dan cleanup.
**Referentie:** Bestaande regel `.claude/hookify.prompt-first-workflow.local.md`

## Implementatie

### Bestand: `.claude/hookify.silent-exception.local.md`

```yaml
---
name: silent-exception
enabled: true
event: file
pattern: "except\\s+(Exception|BaseException)\\s*:?\\s*(\\n\\s*)?(pass|return|\\.\\.\\.)"
action: block
---
```

### Waarschuwingstekst (na frontmatter):

```markdown
🚫 **SILENT EXCEPTION GEDETECTEERD**

Je schrijft een `except Exception: pass/return` patroon. Dit is verboden in deze codebase.

**Waarom:** Silent exceptions verbergen fouten en maken debugging onmogelijk.
We hebben 150+ van deze patronen moeten opruimen (zie DEF-187, DEF-215).

**Oplossing:**
1. Specificeer het exception type: `except ValueError:`
2. Voeg logging toe: `logger.exception("Context: what failed")`
3. Of gebruik `contextlib.suppress()` met comment waarom

**Voorbeeld:**
```python
# ❌ FOUT
except Exception:
    pass

# ✅ GOED
except (TypeError, ValueError) as e:
    logger.warning(f"Context: {e}")
```
```

## Verificatie

Na implementatie:
1. Test met een file die `except Exception: pass` bevat → moet blokkeren
2. Test met `except ValueError: pass` → moet NIET blokkeren
3. Test met `except Exception as e: logger.error(e)` → moet NIET blokkeren

## Constraints

- Gebruik bestaande hookify format (zie prompt-first-workflow regel)
- Alleen `event: file` (niet prompt)
- `action: block` (niet warn)
