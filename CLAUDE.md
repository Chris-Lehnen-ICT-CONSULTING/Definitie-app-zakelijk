# CLAUDE.md (DefinitieAgent Instructions)

*Version: 4.0 | Last Updated: 2025-01-18 | Status: Active | Optimized for token efficiency*

**Optimization:** v3.0 → v4.0 (1,700 tokens saved, 20% reduction)

---

## ⚡ ULTRA-TL;DR (30 Second Activation)

**5 Non-Negotiable Rules:**
1. **Files in root:** NO (except README, requirements, config)
2. **SessionStateManager:** ONLY access via SessionStateManager
3. **Approval gate:** >100 lines OR >5 files → Ask first
4. **No backwards compat:** Refactor in place (solo dev!)
5. **BMad Method:** Type `/BMad:agents:*` (loads on-demand, 57K tokens)

**Architecture:** ServiceContainer + ValidationOrchestratorV2 + 45 rules
**Database:** ONLY `data/definities.db`
**Tests:** Run after EVERY change (60%+ coverage)

**→ Next:** §Quick Lookup for instant answers | §Deep Dive for details

---

## 🔍 Quick Lookup Tables (Instant Answers)

### Table 1: File Location Matrix

| File Type | ❌ FORBIDDEN | ✅ REQUIRED | Example |
|-----------|--------------|-------------|---------|
| Tests | Project root | `tests/` subdirs | `test_foo.py` → `tests/unit/test_foo.py` |
| Scripts | Project root | `scripts/` subdirs | `backup.sh` → `scripts/maintenance/backup.sh` |
| Logs | Project root | `logs/` + archive | `app.log` → `logs/app.log` |
| Databases | Anywhere | `data/` ONLY | Any `*.db` → `data/definities.db` |
| Docs | Root or scattered | `docs/` hierarchy | `PLAN.md` → `docs/planning/PLAN.md` |

### Table 2: Canonical Name Reference

| ✅ CORRECT | ❌ FORBIDDEN | Location | Type |
|------------|--------------|----------|------|
| `ValidationOrchestratorV2` | V1, ValidationOrchestrator | `src/services/validation/` | Class |
| `UnifiedDefinitionGenerator` | DefinitionGenerator | `src/services/generation/` | Class |
| `ModularValidationService` | ValidationService | `src/services/validation/` | Class |
| `SessionStateManager` | session_state, StateManager | `src/ui/` | Class |
| `organisatorische_context` | organizational_context | Database/config | Variable |
| `juridische_context` | legal_context | Database/config | Variable |
| `data/definities.db` | Root or anywhere | `data/` ONLY | File |

### Table 3: Import Rules Matrix

| Layer | ✅ CAN Import | ❌ CANNOT Import | Reason |
|-------|---------------|------------------|--------|
| `services/` | services/, utils/, config/ | ui/, streamlit | Layer separation |
| `ui/` | services/, utils/, streamlit | - | UI can use all |
| `toetsregels/` | config/, utils/ | ui/, services/ (except via DI) | Domain isolation |
| `database/` | utils/ | ui/, services/ (except via DI) | Infrastructure |
| `utils/` | Standard library only | ALL project modules | Utility layer |

### Table 4: Streamlit Widget Patterns

| Pattern | Status | Example | Result |
|---------|--------|---------|--------|
| Key-only | ✅ CORRECT | `st.text_area("Label", key="my_key")` | Session state drives value |
| Value + key | ❌ FORBIDDEN | `st.text_area("Label", value=data, key="my_key")` | Race condition! |
| Direct session_state | ❌ FORBIDDEN | `st.session_state["my_key"]` | Use SessionStateManager |
| SessionStateManager | ✅ CORRECT | `SessionStateManager.get_value("my_key")` | Centralized, safe |
| State before widget | ✅ CORRECT | `set_value() → st.widget()` | Proper init |
| Widget before state | ❌ FORBIDDEN | `st.widget() → set_value()` | Too late! |

**Pre-commit enforcement:** `scripts/check_streamlit_patterns.py` detects violations
**Full patterns:** `docs/guidelines/STREAMLIT_PATTERNS.md`

### Table 5: Testing Strategy

| Test Type | Location | Coverage | When | Priority |
|-----------|----------|----------|------|----------|
| Unit | `tests/unit/` | 80%+ | After every change | HIGH |
| Integration | `tests/integration/` | 60%+ | Before commit | MEDIUM |
| Smoke | `tests/smoke/` | N/A | After merge, CI/CD | HIGH |
| Debug | `tests/debug/` | N/A | Issue investigation | As needed |

**High-coverage modules (run after refactors):**
- `tests/services/test_definition_generator.py` (99%)
- `tests/services/test_definition_validator.py` (98%)
- `tests/services/test_definition_repository.py` (100%)

### Table 6: Decision Tree Matrix

| User Request | Check | Action | Reference |
|--------------|-------|--------|-----------|
| "Fix bug" | Component known? | HOTFIX workflow | →UNIFIED §WORKFLOW |
| "Add feature" | Scope clear? | FULL_TDD workflow | →UNIFIED §WORKFLOW |
| ">100 lines change" | - | Show structure + ask approval | →UNIFIED §APPROVAL |
| "Import streamlit in services/" | - | REFUSE → suggest async_bridge | §Import Rules |
| "Access st.session_state" | - | Use SessionStateManager | §SessionStateManager |

### Table 7: Error Resolution Matrix

| Error | Cause | Solution | Reference |
|-------|-------|----------|-----------|
| Import error | Forbidden pattern | Check Import Rules Matrix | §Table 3 |
| Session state error | Direct access | Use SessionStateManager | §SessionStateManager |
| File location error | Wrong directory | Check File Location Matrix | §Table 1 |
| Naming error | Wrong canonical name | Check Canonical Name Reference | §Table 2 |

### Table 8: Performance Status (Quick Reference)

| Issue | Status | Fix | Date |
|-------|--------|-----|------|
| Rules 45x reload | ✅ FIXED | RuleCache | Oct 2025 |
| Service 2x init | ✅ FIXED | Singleton | Oct 2025 |
| PromptOrchestrator 2x | ✅ FIXED | Unified cache | Oct 2025 |
| Prompt tokens 7.2K | ⏳ OPEN | Deduplication | Planned |

**Details:** `docs/reports/toetsregels-caching-fix.md`

### Table 9: Common Commands

| Command | Purpose | When |
|---------|---------|------|
| `bash scripts/run_app.sh` | Start app (recommended) | Development |
| `pytest -q` | Run tests (quiet) | After changes |
| `make test` | Run tests via Makefile | CI/CD |
| `make lint` | Lint + format checks | Before commit |
| `pre-commit run --all-files` | Run all hooks | Manual validation |

### Table 10: Architecture Quick Map

```
src/
├── main.py                     # Entry point
├── services/
│   ├── container.py           # ServiceContainer (DI)
│   ├── validation/
│   │   ├── modular_validation_service.py  # 45 rules
│   │   └── validation_orchestrator_v2.py  # Orchestration
│   ├── generation/
│   │   └── unified_definition_generator.py
│   └── ai/
│       └── ai_service_v2.py   # GPT-4 integration
├── ui/
│   ├── tabs/                  # Streamlit UI
│   └── session_state.py       # SessionStateManager
├── toetsregels/
│   ├── regels/                # Validation logic
│   └── rule_cache.py          # RuleCache (TTL: 3600s)
└── database/
    ├── schema.sql
    └── migrations/

data/
└── definities.db              # SQLite (ONLY here!)
```

---

## 🎯 Critical Rules (Action-Oriented)

### 🔴 Project Root Policy (STRICT!)

**NO files in project root, except:**
- README.md, CONTRIBUTING.md, CLAUDE.md
- requirements.txt, requirements-dev.txt
- Config: pyproject.toml, pytest.ini, .pre-commit-config.yaml

**MOVE immediately:**
- `test_*.py` → `tests/` subdirs
- `*.sh` → `scripts/` subdirs
- `*.log` → `logs/`
- `*.db` → `data/`
- `HANDOVER*.md` → `docs/archief/handovers/`

**Check:** `~/.ai-agents/quality-gates.yaml` §forbidden_locations

### 🔴 SessionStateManager (MANDATORY)

**RULE:** SessionStateManager is the ONLY module that may touch `st.session_state`

```python
# ✅ CORRECT
from ui.session_state import SessionStateManager
value = SessionStateManager.get_value("my_key", default="")

# ❌ FORBIDDEN
import streamlit as st
value = st.session_state["my_key"]  # NEVER!
```

**Exception:** App initialization in `main.py` only

### 🔴 NO Backwards Compatibility

- Single-user app, NOT in production
- Refactor in place, preserve business logic
- NO feature flags, migration paths, deprecation warnings
- Focus: improve code, NOT compatibility

### 🔴 NO God Objects

**FORBIDDEN:** `dry_helpers.py` or "catch-all" utility modules

**SOLUTION:** Specific modules
- `utils/type_helpers.py` - Type conversions
- `utils/dict_helpers.py` - Dictionary operations
- `utils/validation_helpers.py` - Validation utilities

### 🤖 BMad Method Integration (On-Demand)

**AGENTS.md is NOT loaded by default** - contains 57K tokens for BMad workflows.

**To use BMad agents:** Type `/BMad:agents:bmad-master` (loads on first invocation)

**Why:** 95% of conversations don't use BMad - loading wastes 77% of token budget.

### 🔍 Bounded Analysis Workflow (On-Demand, Project-Specific)

**Pattern:** Structured two-phase optimization workflow

**Available workflows:**

#### Phase 1: Analysis (60 min MAX)
- **Prompt Optimization:** `docs/workflows/bounded-prompt-analysis.md`
- **Codebase Health:** `docs/workflows/bounded-codebase-analysis.md`
- **Framework:** 5 Whys + Pareto (80/20) + MECE + Impact-Effort Matrix
- **Output:** `~/Downloads/analysis-output.json` with TOP 3 issues

#### Phase 2: Implementation (2h MAX, 3 fixes)
- **File:** `docs/workflows/implement-prompt-fixes.md`
- **Input:** JSON from Phase 1
- **Pattern:** ReAct (Reason → Act → Observe → Decide)
- **Output:** Code changes + validation report

**When to use:**
- ✅ User says: "optimize prompt", "reduce tokens", "bottleneck analysis"
- ✅ Performance issue with unclear root cause
- ✅ Multiple interrelated issues needing prioritization
- ✅ User requests: "systematic approach", "comprehensive analysis"

**Do NOT use:**
- ❌ Single clear bug (use HOTFIX workflow)
- ❌ User provides clear requirements (skip analysis, implement directly)
- ❌ <100 lines change with known solution (overkill)

**Multiagent integration:**
- **Analysis:** Optional (Perplexity for research, Context7 for docs, debug-specialist for root cause)
- **Implementation:** Optional (code-reviewer for scoring, code-simplifier for complexity)
- **Ultrathink checks:** MANDATORY (§EFFORT <10h, §KISS no enterprise, §PROTOTYPE 30min)

**Quick start:**
```bash
# Analysis phase
Read: docs/workflows/bounded-prompt-analysis.md
Input: [prompt file or codebase path]
Time: 60 minutes HARD STOP

# Implementation phase
Read: docs/workflows/implement-prompt-fixes.md
Input: ~/Downloads/analysis-output.json
Time: 2 hours (3 fixes max)
```

**See also:** `~/.ai-agents/UNIFIED_INSTRUCTIONS.md` §BOUNDED_ANALYSIS for cross-project framework

---

## 📚 Cross-Reference Guide

**For general rules:** `~/.ai-agents/UNIFIED_INSTRUCTIONS.md`

| Topic | UNIFIED Section | What You Find |
|-------|----------------|---------------|
| Approval Thresholds | §APPROVAL LADDER | Complete decision tree |
| Workflow Selection | §WORKFLOW MATRIX | ANALYSIS/HOTFIX/FULL_TDD/REFACTOR/BOUNDED_ANALYSIS |
| Bounded Analysis | §BOUNDED_ANALYSIS | Framework, triggers, multiagent + ultrathink |
| Canonical Naming | §NAMING CONVENTIONS | Full name list |
| Forbidden Imports | §FORBIDDEN PATTERNS | Import blacklist |
| Multiagent Workflows | §MULTIAGENT PATTERNS | When & how |

**This document (CLAUDE.md) adds:**
- DefinitieAgent architecture
- Project root policy (strict!)
- Database locations
- Streamlit UI patterns
- Performance context

**Precedence:** UNIFIED > CLAUDE.md > quality-gates.yaml

---

## 🏗️ Architecture Overview

**Service-Oriented with Dependency Injection (ServiceContainer)**

**Key Services:**
- **ValidationOrchestratorV2:** Main orchestration (45 rules)
- **ModularValidationService:** Rule management
- **UnifiedDefinitionGenerator:** Core generation
- **AIServiceV2:** GPT-4 integration
- **PromptServiceV2:** Modular prompts
- **ModernWebLookupService:** External sources (Wikipedia, SRU)

**Caching (US-202):**
- **RuleCache:** Bulk loading, TTL 3600s (`@cached` decorator)
- **CachedToetsregelManager:** Singleton manager
- **Performance:** 77% faster, 81% less memory

**Database:**
- SQLite: `data/definities.db` (ONLY location!)
- Schema: `src/database/schema.sql`
- Migrations: `src/database/migrations/`
- UTF-8 encoding for Dutch text

---

## 🎨 Streamlit UI Patterns (Critical!)

### Key-Only Widget Pattern (MANDATORY)

```python
# ✅ CORRECT: Key-only
st.text_area("Label", key="edit_23_field")

# ❌ WRONG: value + key → Race condition!
st.text_area("Label", value=data, key="edit_23_field")
```

**Why:** Widgets with `value` + `key` retain internal state over `st.rerun()`, causing stale data.

### State Initialization Order

```python
# ✅ CORRECT: State BEFORE widget
SessionStateManager.set_value("my_key", "default")
st.text_area("Label", key="my_key")

# ❌ WRONG: Widget before state
st.text_area("Label", key="my_key")
SessionStateManager.set_value("my_key", "default")  # Too late!
```

### Pre-Commit Enforcement

Hook `streamlit-anti-patterns` detects:
- ❌ `value` + `key` combinations
- ❌ Direct `st.session_state` in UI modules
- ⚠️  Generic widget keys (conflicts)

**Test:** `python scripts/check_streamlit_patterns.py`

**Full guide:** `docs/guidelines/STREAMLIT_PATTERNS.md`

---

## 🧪 Development Patterns

### Lazy Import Pattern (Circular Dependency Fix)

**ONLY when circular import unavoidable after restructure**

| Use Case | Implementation | Example |
|----------|----------------|---------|
| module_a ↔ module_b | Import inside function | session_state.py:205 |

**Prefer:** Restructure > DI > Extract shared > Lazy import (last resort)

**Reference:** DEF-84 documents pattern from DEF-73

### Code Style

- Python 3.11+ with type hints
- Ruff + Black (88 char lines)
- Dutch comments for business logic
- English for technical code
- Canonical names (see Table 2)

---

## 🔧 Common Operations

```bash
# Start app
bash scripts/run_app.sh

# Tests
pytest -q                      # Quick
pytest tests/services/test_definition_generator.py  # Specific

# Quality
make lint
python -m ruff check src config

# Pre-commit
pre-commit run --all-files
```

---

## 🐛 Debugging Quick Checks

| Issue | Check | Solution |
|-------|-------|----------|
| Service init | `st.session_state.service_container` | Singleton exists? |
| Validation errors | Enable debug logging | `modular_validation_service.py` |
| API rate limits | Check `logs/api_calls.json` | Monitor usage |
| Memory issues | Monitor cache size | `st.session_state` |
| Import errors | `python -m py_compile <file>` | Syntax check |

---

## 📁 Important File Locations

- **Main:** `src/main.py`
- **Container:** `src/services/container.py`
- **Rules:** `src/toetsregels/regels/` + `config/toetsregels/regels/`
- **UI:** `src/ui/tabs/`
- **Database:** `data/definities.db`
- **Logs:** `logs/`
- **Exports:** `exports/`

---

## 🔗 Documentation References

**Core Architecture:**
- `docs/architectuur/ARCHITECTURE.md` - Solo dev patterns, tech stack
- `docs/architectuur/validation_orchestrator_v2.md` - Validation system
- `docs/guidelines/CANONICAL_LOCATIONS.md` - File organization

**Implementation Guides:**
- `docs/guidelines/STREAMLIT_PATTERNS.md` - UI patterns (DEF-56 lessons)
- `docs/technisch/web_lookup_config.md` - Web lookup
- `docs/testing/validation_orchestrator_testplan.md` - Test strategy

**Project Info:**
- `docs/brief.md` - Project brief
- `docs/prd.md` - Requirements
- `docs/INDEX.md` - Complete doc index

**Current Work:**
- `docs/backlog/EPIC-XXX/` - Epic docs
- `docs/refactor-log.md` - Refactor history

---

## 🎯 Workflow Reminders

**Definition Generation Flow:**
1. User input → ServiceContainer
2. ValidationOrchestratorV2 → 45 rules
3. UnifiedDefinitionGenerator → GPT-4
4. ModularValidationService → Post-gen validation
5. SessionStateManager → Store results
6. UI update

**Debugging Protocol:**
1. Service init → Check session_state
2. Validation → Enable debug logging
3. API limits → Check logs
4. Memory → Monitor cache
5. Imports → py_compile

---

**For detailed workflows, approval thresholds, and naming conventions:**
→ `~/.ai-agents/UNIFIED_INSTRUCTIONS.md`

**For BMad Method workflows (57K tokens, load on-demand only):**
→ Type `/BMad:agents:bmad-master`

---

*Version 4.0 optimized for 20% token reduction while preserving 100% critical information.*
*Changes: ULTRA-TL;DR added, 10 quick lookup tables, compressed over-explained sections, removed duplications.*
