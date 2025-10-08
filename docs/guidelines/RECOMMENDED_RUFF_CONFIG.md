# Recommended Ruff Configuration Update
**Based on Pragmatic Improvement Roadmap**

## Current State Analysis

Your current `pyproject.toml` already has good pragmatic ignores:
- ✅ PLC0415 (lazy imports) - Already ignored
- ✅ ARG002 (unused args) - Already ignored
- ✅ N999 (module naming) - Already ignored
- ✅ PLW0603 (global state) - Already ignored

**Good work!** Your configuration already reflects pragmatic solo-developer priorities.

## Recommended Additions

Add these to your existing `ignore` list in `pyproject.toml`:

```toml
[tool.ruff.lint]
ignore = [
    # Existing (keep these)
    "E402",    # Module level import not at top of file
    "E501",    # Line too long - handled by Black
    "PLR0913", # Too many arguments
    "PLR2004", # Magic value used in comparison
    "PGH003",  # Use specific rule codes when ignoring type issues
    "PLC0415", # Import outside top-level - intentional lazy loading
    "ARG002",  # Unused method argument - interface compliance
    "N999",    # Invalid module name - legacy naming
    "PLW0603", # Global statement - singleton patterns

    # NEW: Add these based on roadmap
    "PLC2401", # Non-ASCII variable names - Dutch domain terms are intentional
    "PLR0911", # Too many return statements - domain complexity is real
    "PLR0912", # Too many branches - domain complexity is real
    "PLR0915", # Too many statements - domain complexity is real
    "SIM102",  # Nested if statements - sometimes clearer than combined
    "RUF003",  # Ambiguous unicode in comments - doesn't affect functionality
    "PD901",   # Avoid using generic 'df' for pandas DataFrames - too strict
    "ARG001",  # Unused function argument - often interface requirements
]
```

## Keep Enabled (These Catch Real Bugs)

Make sure these are still in your `select` list:

```toml
select = [
    "E",     # pycodestyle errors
    "F",     # pyflakes
    "B",     # flake8-bugbear (includes B904 - exception chaining)
    "DTZ",   # flake8-datetimez (timezone issues)
    "EM",    # flake8-errmsg (exception message format)
    "UP",    # pyupgrade
    "C4",    # flake8-comprehensions
    "ISC",   # flake8-implicit-str-concat
    "PIE",   # flake8-pie
    "RET",   # flake8-return
    "PGH",   # pygrep-hooks
    "RUF",   # ruff-specific rules (except ignored ones)
]
```

## Updated Per-File Ignores

Your current per-file ignores are good. Consider adding:

```toml
[tool.ruff.lint.per-file-ignores]
# Existing (keep these)
"__init__.py" = ["F401", "E402"]
"test_*.py" = ["F401", "E402"]
"*_test.py" = ["F401", "E402"]
"**/archief/**/*.py" = ["ALL"]
"**/ARCHIEF/**/*.py" = ["ALL"]
"**/archive/**/*.py" = ["ALL"]

# NEW: Complex business logic files
"src/orchestration/definitie_agent.py" = ["PLR0912", "PLR0915"]
"src/document_processing/document_extractor.py" = ["PLR0911"]
"src/export/export_txt.py" = ["PLR0915"]
"src/hybrid_context/smart_source_selector.py" = ["PLR0912"]
"src/integration/definitie_checker.py" = ["PLR0915", "PLR0911"]

# Services with intentional patterns
"src/services/container.py" = ["PLC0415", "PLW0603"]
"src/api/feature_status_api.py" = ["PLW0603"]
"src/document_processing/document_processor.py" = ["PLW0603"]

# Domain model files (Dutch names are correct)
"src/domain/**/*.py" = ["PLC2401"]
"src/toetsregels/**/*.py" = ["PLC2401"]
```

## Complete Recommended pyproject.toml Section

```toml
[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "F",    # pyflakes
    "I",    # isort
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "DTZ",  # flake8-datetimez
    "EM",   # flake8-errmsg
    "ISC",  # flake8-implicit-str-concat
    "PIE",  # flake8-pie
    "RET",  # flake8-return
    "PGH",  # pygrep-hooks
    "RUF",  # ruff-specific rules
]

ignore = [
    # Style (handled by Black or not important)
    "E402",    # Module level import not at top of file
    "E501",    # Line too long - handled by Black
    "PLR2004", # Magic value used in comparison
    "PGH003",  # Use specific rule codes when ignoring type issues

    # Intentional architecture patterns (single-user app)
    "PLC0415", # Import outside top-level - lazy loading for performance
    "PLW0603", # Global statement - singleton patterns for single-user

    # Interface & domain design
    "ARG001",  # Unused function argument - interface requirements
    "ARG002",  # Unused method argument - interface requirements
    "N999",    # Invalid module name - legacy conventions work fine
    "PLC2401", # Non-ASCII names - Dutch legal domain terms

    # Complexity (domain complexity is real)
    "PLR0911", # Too many return statements
    "PLR0912", # Too many branches
    "PLR0913", # Too many arguments
    "PLR0915", # Too many statements

    # Simplification (sometimes wrong)
    "SIM102",  # Nested if - sometimes clearer

    # Low-value warnings
    "RUF003",  # Ambiguous unicode in comments
    "PD901",   # Generic DataFrame names
]

# Allow autofix for all enabled rules
fixable = ["ALL"]
unfixable = []

[tool.ruff.lint.per-file-ignores]
# Test files
"__init__.py" = ["F401", "E402"]
"test_*.py" = ["F401", "E402", "PLR2004"]
"*_test.py" = ["F401", "E402", "PLR2004"]

# Archive/legacy (ignore everything)
"**/archief/**/*.py" = ["ALL"]
"**/ARCHIEF/**/*.py" = ["ALL"]
"**/archive/**/*.py" = ["ALL"]

# Complex business logic (domain complexity)
"src/orchestration/definitie_agent.py" = ["PLR0912", "PLR0915"]
"src/document_processing/document_extractor.py" = ["PLR0911"]
"src/export/export_txt.py" = ["PLR0915"]
"src/hybrid_context/smart_source_selector.py" = ["PLR0912"]
"src/integration/definitie_checker.py" = ["PLR0915", "PLR0911"]

# Services with singleton patterns
"src/services/container.py" = ["PLC0415", "PLW0603"]
"src/api/feature_status_api.py" = ["PLW0603"]
"src/document_processing/document_processor.py" = ["PLW0603"]
"src/hybrid_context/hybrid_context_engine.py" = ["PLW0603"]
"src/monitoring/api_monitor.py" = ["PLW0603"]
"src/security/security_middleware.py" = ["PLW0603"]

# Domain models (Dutch terminology)
"src/domain/**/*.py" = ["PLC2401"]
"src/toetsregels/**/*.py" = ["PLC2401"]

[tool.ruff.lint.pylint]
max-args = 8          # Increased from 7 - some services need more
max-branches = 15     # Increased from 12 - domain complexity
max-returns = 8       # Increased from 6 - document processing
max-statements = 60   # Increased from 50 - complex workflows
```

## Expected Results After Update

Running `ruff check src config` should report:

**Before:** 869 issues
**After:** ~50-100 issues (mostly real bugs and opportunities)

**Breakdown:**
- ~20 TIER 0 issues (fix now): B904, DTZ, EM
- ~30-80 TIER 1 issues (fix when touching): RUF012, PLW2901, etc.
- ~700+ false positives: Ignored via config ✅

## Quick Test Commands

```bash
# Check only critical security issues
ruff check src config --select B904,DTZ,EM

# Check with new config (should be much cleaner)
ruff check src config

# Auto-fix safe issues
ruff check src config --fix

# Generate clean report for CI
ruff check src config --output-format=github
```

## CI Integration

Update your CI workflow to focus on critical issues:

```yaml
# .github/workflows/ci.yml
- name: Lint (Critical Only)
  run: |
    ruff check src config --select B904,DTZ,EM --output-format=github

- name: Lint (Full)
  run: |
    ruff check src config --output-format=github
  continue-on-error: true  # Don't block on style issues
```

## Benefits of This Config

1. **Focus on Real Issues:** Catches bugs, not style preferences
2. **Respects Architecture:** Acknowledges intentional design decisions
3. **Solo-Developer Friendly:** Doesn't enforce team conventions unnecessarily
4. **Performance-Aware:** Keeps lazy loading and singleton patterns
5. **Domain-Appropriate:** Allows Dutch legal terminology
6. **Low Noise:** ~85% reduction in false positive warnings

## Migration Plan

1. **Backup current config:** `cp pyproject.toml pyproject.toml.backup`
2. **Update pyproject.toml** with new ignore rules
3. **Run ruff:** `ruff check src config` - verify ~50-100 issues remain
4. **Fix TIER 0 issues:** `ruff check src config --select B904,DTZ,EM`
5. **Commit:** "config: update ruff to focus on pragmatic issues"

## Maintenance

**Monthly:** Run `ruff check src config --statistics` to track trends
**When adding rules:** Ask "Does this catch real bugs?" If no, ignore it
**When removing ignores:** Ask "Will this waste my time?" If yes, keep it ignored

---

**Remember:** The best linting config is one that helps you ship features faster, not one that follows every best practice. Your current config is already pretty good - these updates just make it excellent for solo development.
