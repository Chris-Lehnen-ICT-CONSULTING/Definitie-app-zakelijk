# CONTRIBUTING — DefinitieAgent

> Code-conventies aanvullend op `.claude/rules/patterns.md` (architectuur), `.claude/rules/streamlit-patterns.md` (UI) en `.claude/rules/project-rules.md` (kritieke regels).

## Type-safety

### `typing.cast()` policy (sinds DEF-408)

Sinds DEF-408 draait `mypy src/services` blokkerend in CI. `typing.cast()` is een type-checker no-op: het verandert niets aan runtime. Het is een **belofte** aan mypy zonder bewijs. Misbruik = silent bug-amplifier.

**Regel:** Elke nieuwe `cast()` MOET een comment dragen die onderbouwt waarom de runtime-vorm gegarandeerd is. Zonder comment = niet mergen.

#### Acceptabele patterns met onderbouwing

| Pattern | Onderbouwing in comment | Voorbeeld |
|---------|------------------------|-----------|
| In-place gebouwde dict | "X is in deze functie zelf gebouwd, past binnen total=False TypedDict" | `validation/types.py:289` |
| SQL met INTEGER PRIMARY KEY | "kolom is INTEGER PRIMARY KEY, runtime gegarandeerd int" | `rag/rag_service.py:82` |
| DI singleton | "interne factory, returns altijd Y" | `services/container.py:931` |
| Module-config lookup | "config.yaml schema controleert dit" | `ai/model_router.py:85` |

#### Anti-patterns (afkeuren in review)

- `cast()` op externe data zonder voorafgaande validatie → gebruik runtime-check (zie `_assert_validation_result_keys` in `validation/types.py`)
- `cast()` om mypy error te onderdrukken zonder begrip van waarom mypy klaagt
- `cast(Any, ...)` — zinloos, drop de cast
- Generieke `# type: ignore` zonder error-code → gebruik `# type: ignore[specific-code]` met reden

### `assert` vs `if-raise` voor invarianten

`assert` statements worden weggeoptimaliseerd onder `python -O` (PYTHONOPTIMIZE=1). **Gebruik geen assert voor invarianten waarvan de schending tot runtime data-corruptie kan leiden.**

Gebruik in plaats daarvan:

```python
# Slecht — verdwijnt onder -O:
assert cursor.lastrowid is not None, "lastrowid mag niet None zijn"

# Goed — altijd actief:
if cursor.lastrowid is None:
    raise RuntimeError("INSERT gaf geen lastrowid terug")
```

`assert` mag wel voor:
- Test-asserts (`pytest` gebruikt het zelf)
- Dev-only sanity checks die geen impact hebben op data-integriteit

### `# type: ignore` policy

- ALTIJD met error-code: `# type: ignore[arg-type]`, niet naakte `# type: ignore`
- ALTIJD met comment waarom: `# type: ignore[arg-type]  # SDK quirk: <reden>`
- Bij SDK-upgrade: review of de ignore nog nodig is

## Testing

Zie `.claude/rules/patterns.md` Anti-patronen + `CLAUDE.md` Verificatie bij oplevering.

## File-protection

Zie `.claude/rules/project-rules.md` voor harde regels (geen bestanden in project root, SessionStateManager only, etc.).
