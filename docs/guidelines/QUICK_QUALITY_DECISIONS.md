# Quick Quality Decision Card
**Solo Developer Edition - 30 Second Reference**

When ruff complains, use this chart:

## Fix Now (Blocks work)
- ✅ **B904** - Missing `from err` → Add exception chaining
- ✅ **DTZ** - datetime.now() → Add timezone
- ✅ **EM101/102** - String exceptions → Use variable

## Fix When Touching Code
- 🟨 **ARG002** - Unused arg → Prefix with `_` or remove
- 🟨 **RUF012** - Mutable class attr → Add `ClassVar[...]`
- 🟨 **PLW2901** - Loop variable overwrite → Rename variable

## Ignore (Not Worth Time)
- ⏭️ **I001** - Import sorting → Auto-fix with `ruff check --fix`
- ⏭️ **SIM102** - Nested if → Leave if clearer
- ⏭️ **RUF003** - Comment chars → Ignore

## Never Fix (Intentional)
- 🛑 **PLC0415** - Lazy imports → **Performance feature, keep it**
- 🛑 **PLW0603** - Global state → **Single-user app, keep it**
- 🛑 **PLC2401** - Non-ASCII names → **Dutch domain, keep it**
- 🛑 **N999** - Module naming → **Works fine, keep it**
- 🛑 **PLR0911/0912/0915** - Complex functions → **Domain complexity, keep it**

---

## One-Line Decision Tree

```
Does it cause bugs? → Fix now
Will I edit this file today? → Fix then
Is it just style? → Ignore
Is it flagging intentional design? → Keep & disable rule
```

---

## Ruff Config to Copy-Paste

Add to `pyproject.toml`:

```toml
[tool.ruff.lint]
ignore = ["PLC0415", "PLW0603", "ARG002", "PLC2401", "N999", "PLR0911", "PLR0912", "PLR0915", "SIM102", "RUF003"]
select = ["B904", "EM", "DTZ", "F", "E", "W"]
```

---

## Remember

**Default action for any linting issue: DON'T FIX IT**

Your time is better spent shipping features. Only fix what actively hurts.
