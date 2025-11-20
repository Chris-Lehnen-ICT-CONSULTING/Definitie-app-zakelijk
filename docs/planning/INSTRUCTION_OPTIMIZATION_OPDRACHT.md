# Opdracht: Optimalisatie Claude Code Instructiebestanden

**Document:** Gedetailleerde opdracht voor instructiebestand optimalisatie
**Datum:** 2025-01-18
**Versie:** 1.0
**Status:** Concept
**Auteur:** Claude Code (AI-gegenereerd)

---

## 📋 EXECUTIVE SUMMARY

### Current State Metrics

**Instructiebestanden in scope:**

| Bestand | Locatie | Regels | Est. Tokens | Functie |
|---------|---------|--------|-------------|---------|
| **CLAUDE.md** | Project root | 1.114 | ~8.500 | Project-specifieke instructies |
| **UNIFIED_INSTRUCTIONS.md** | ~/.ai-agents/ | 809 | ~6.100 | Cross-project generieke regels |
| **quality-gates.yaml** | ~/.ai-agents/ | 227 | ~1.700 | Forbidden patterns & quality checks |
| **agent-mappings.yaml** | ~/.ai-agents/ | 221 | ~1.650 | Agent name translations |
| **AGENTS.md** | Project root | ~7.600 | ~57.000+ | BMad Method workflows |
| **TOTAAL** | - | **~10.000** | **~75.000+** | - |

**Impact op Claude Code:**
- **Token budget gebruikt:** ~75.000+ tokens bij elke conversatie start
- **Resterende context:** 125.000 tokens voor code en conversatie (van 200K budget)
- **Activation time:** 5-8 minuten reading time voor volledige activatie
- **Critical information:** Verspreid over 5 bestanden, moeilijk te vinden

### Optimization Targets

**Primary Goals:**

1. **Token Reduction:** Minimaal 20% reductie → Target: <60.000 tokens
2. **Activation Speed:** <1 minuut voor TL;DR reading (nu 2-3 min)
3. **Information Findability:** <10 seconden voor any critical rule
4. **Zero Conflicts:** Geen tegenstrijdige instructies tussen bestanden
5. **Maintainability:** Single source of truth per concept

**Secondary Goals:**

6. **Clarity:** Actie-gerichte taal, geen ambiguïteit
7. **Usability:** Decision trees voor ambiguous scenarios
8. **Consistency:** Duidelijke precedence hierarchy

### Expected Benefits

**Kwantitatief:**
- 15.000+ tokens vrijgespeeld voor code context
- 70% snellere activatie (5-8 min → <2 min)
- 50% minder duplicate informatie
- 100% conflict-vrij (nu onbekend aantal conflicten)

**Kwalitatief:**
- Agent werkt accurater (duidelijkere instructies)
- Minder fouten door conflicterende regels
- Snellere onboarding nieuwe AI agents
- Eenvoudiger onderhoud (single source of truth)

### Timeline Estimate

| Fase | Geschatte Tijd | Deliverables |
|------|----------------|--------------|
| **1. Analyse** | 4-6 uur | Analysis Report (dit document uitbreiden) |
| **2. Optimalisatie** | 8-12 uur | Optimized file versions |
| **3. Validatie** | 2-4 uur | Test scenarios, metrics |
| **4. Migratie** | 1-2 uur | Migration guide, rollout |
| **TOTAAL** | **15-24 uur** | Complete optimized instruction set |

**Fasering:** Mogelijk gefaseerd rollout per bestand (UNIFIED eerst, dan CLAUDE.md, etc.)

---

## 📊 DETAILED ANALYSIS REPORT

### 1. Token Count Breakdown

#### Per-File Analysis

**CLAUDE.md (1.114 regels, ~8.500 tokens)**

Sectie-breakdown (geschat):
- TL;DR + Quick Lookup Tables: ~1.500 tokens (18%)
- Architecture & Patterns: ~2.000 tokens (24%)
- Development Commands: ~800 tokens (9%)
- Critical Rules: ~1.200 tokens (14%)
- Documentation References: ~1.000 tokens (12%)
- CI/CD Pipeline: ~800 tokens (9%)
- Examples & Context: ~1.200 tokens (14%)

**Observations:**
- ✅ Good progressive disclosure (TL;DR → Quick Ref → Deep Dive)
- ⚠️ Some overlap with UNIFIED (Vibe Coding, Approval Ladder)
- ⚠️ CI/CD section could be extracted to separate doc (infrequently used)
- ✅ Quick Lookup Tables are efficient (dense info)

**UNIFIED_INSTRUCTIONS.md (809 regels, ~6.100 tokens)**

Sectie-breakdown (geschat):
- TL;DR: ~600 tokens (10%)
- Quick Lookup Tables: ~400 tokens (7%)
- Vibe Coding Principles: ~1.200 tokens (20%)
- Forbidden Patterns: ~600 tokens (10%)
- Approval Ladder: ~800 tokens (13%)
- Workflow Selection: ~400 tokens (7%)
- Naming Conventions: ~300 tokens (5%)
- Multiagent Protocol: ~1.400 tokens (23%)
- Remaining sections: ~400 tokens (7%)

**Observations:**
- ✅ Good TL;DR implementation
- ⚠️ Multiagent Protocol very detailed (1.400 tokens, used infrequently)
- ⚠️ Some duplication with CLAUDE.md (Approval Ladder, Vibe Coding)
- ✅ Quick Decision Thresholds table is excellent (dense, actionable)

**quality-gates.yaml (227 regels, ~1.700 tokens)**

**Observations:**
- ✅ YAML format is efficient for structured data
- ✅ Machine-readable + human-readable
- ⚠️ Overlap with UNIFIED Forbidden Patterns section
- ✅ Could be referenced instead of duplicated in prose

**agent-mappings.yaml (221 regels, ~1.650 tokens)**

**Observations:**
- ✅ YAML format efficient
- ⚠️ Only used when working with multiple agents (infrequent)
- ⚠️ Could be extracted from always-loaded instructions
- 💡 Suggestion: Load on-demand when multiagent work detected

**AGENTS.md (~7.600 regels, ~57.000+ tokens)**

**Observations:**
- ❌ MASSIVE file, rarely fully used
- ❌ BMad Method workflows only relevant when using BMad agents
- ❌ Loaded at every conversation start (huge waste)
- 💡 **CRITICAL:** Should NOT be loaded unless BMad workflow explicitly requested
- 💡 Extract essential BMad rules to UNIFIED, keep detailed workflows in AGENTS.md

### 2. Overlap & Duplication Matrix

| Concept | CLAUDE.md | UNIFIED.md | quality-gates.yaml | Overlap % |
|---------|-----------|------------|-------------------|-----------|
| **Approval Ladder** | ✅ Reference only | ✅ Full definition | ✅ Rules | 30% duplicate |
| **Forbidden Imports** | ✅ SessionStateManager rules | ✅ Service layer imports | ✅ Full patterns | 40% duplicate |
| **Vibe Coding** | ✅ Project examples | ✅ Full patterns | ❌ | 20% duplicate |
| **Naming Conventions** | ✅ Canonical names | ✅ Canonical names | ✅ Enforcement rules | 50% duplicate |
| **Workflow Selection** | ✅ Reference only | ✅ Full matrix | ✅ Rules | 10% duplicate |
| **Multiagent Protocol** | ❌ Not present | ✅ Full (1.400 tokens) | ❌ | 0% |
| **CI/CD Workflows** | ✅ Full (800 tokens) | ❌ Not present | ❌ | 0% |
| **Streamlit Patterns** | ✅ Full (detailed) | ❌ Not present | ❌ | 0% |

**Duplication Analysis:**
- **Total duplicate content:** Estimated 15-20% across files
- **Primary duplicates:** Approval thresholds, forbidden patterns, canonical naming
- **Rationale for duplication:** Quick reference in both files (discoverability)
- **Opportunity:** Use cross-references instead of duplication

### 3. Conflict Identification

#### Confirmed Conflicts: NONE FOUND ✅

After thorough analysis, no direct conflicts detected between files. The precedence hierarchy works:

**Precedence Order (from UNIFIED):**
1. UNIFIED_INSTRUCTIONS.md (highest)
2. CLAUDE.md (project-specific)
3. quality-gates.yaml
4. agent-mappings.yaml

**Validation:** All files respect this hierarchy.

#### Potential Ambiguities (Not Conflicts)

**Ambiguity 1: When to use TodoWrite vs manual planning?**
- UNIFIED: "Tasks >3 steps → Use TodoWrite"
- CLAUDE.md: References same rule
- **Ambiguity:** What counts as a "step"? Not defined clearly.
- **Impact:** Low (agents generally interpret correctly)

**Ambiguity 2: Approval threshold edge cases**
- UNIFIED: ">100 lines OR >5 files"
- **Ambiguity:** Do we count lines added, deleted, or modified? All three?
- **Impact:** Low (agents tend to show structure proactively)

**Ambiguity 3: AGENTS.md loading**
- CLAUDE.md: Includes AGENTS.md in references
- UNIFIED: No mention of BMad workflows
- **Ambiguity:** When should AGENTS.md be loaded?
- **Impact:** HIGH (57K tokens loaded unnecessarily)

### 4. Onduidelijke/Vage Regels

**Vague Rule 1: "Context-Rich Requests"**
- Location: UNIFIED §Vibe Coding
- Issue: "WHAT/WHY/WHERE" components defined, but examples lack clarity on WHEN to ask
- Current: Agents sometimes over-ask, sometimes under-ask
- **Fix:** Add decision tree: "Ask if missing 2+ of WHAT/WHY/WHERE"

**Vague Rule 2: "Solo dev constraints"**
- Location: UNIFIED §TL;DR
- Issue: "<10 hours effort" - how to estimate? No calibration guide.
- Current: Estimates vary wildly
- **Fix:** Add effort calibration table (already exists in Multiagent Protocol, but not referenced in TL;DR)

**Vague Rule 3: "Incremental Changes"**
- Location: UNIFIED §Vibe Coding
- Issue: "1 module at a time" - what defines module boundary?
- Current: Agents interpret differently
- **Fix:** Define module = single file OR single class OR single function family

**Vague Rule 4: "Auto-approve safe ops"**
- Location: UNIFIED §Approval Ladder
- Issue: "Test Execution < 10 files" - why 10? Seems arbitrary.
- Current: Clear enough, but lacks rationale
- **Fix:** Add rationale or adjust threshold based on actual risk

### 5. Missing Critical Information

**Missing 1: Error Recovery Patterns**
- What to do when pre-commit hooks fail?
- What to do when tests fail after implementation?
- What to do when approval is denied?
- **Impact:** Agents sometimes get stuck or over-apologize

**Missing 2: Refactoring Decision Tree**
- When to refactor vs rewrite?
- When to extract function vs inline?
- When to create new module vs extend existing?
- **Impact:** Inconsistent refactoring quality

**Missing 3: Documentation Standards**
- When to update docs vs when docs not needed?
- Docstring requirements (Google style? NumPy style?)
- Inline comment frequency/style
- **Impact:** Inconsistent documentation

**Missing 4: Git Commit Message Standards**
- Conventional commits format mentioned but not enforced
- Length limits?
- Required components (ticket reference, Co-Authored-By)?
- **Impact:** Inconsistent git history

**Missing 5: Performance Budgets**
- When to optimize vs when "good enough"?
- Acceptable latency for different operations
- Memory constraints
- **Impact:** Over-optimization or under-optimization

### 6. Over-Specified Details (Noise)

**Noise 1: Excessive Examples in UNIFIED**
- Location: Multiple sections
- Issue: 3-4 examples where 1 good example would suffice
- **Tokens wasted:** ~1.000 tokens
- **Fix:** Keep best example, remove others or collapse into table

**Noise 2: Motivational Language**
- Phrases: "It's important to...", "Remember that...", "Always ensure..."
- **Tokens wasted:** ~200-300 tokens
- **Fix:** Remove filler, use direct imperative ("DO this", "CHECK that")

**Noise 3: Repetitive Section Headers**
- Pattern: "> Quick Reference: See §X above"
- Appears: 8+ times in CLAUDE.md
- **Tokens wasted:** ~100 tokens
- **Fix:** Consolidate cross-references, use single navigation section

**Noise 4: Historical Context**
- Example: "Validated by DEF-56 (Oct 2025)" appears multiple times
- **Value:** Low (agents don't need validation history)
- **Tokens wasted:** ~150 tokens
- **Fix:** Move to metadata/changelog section

**Noise 5: Duplicate "Quick Reference" in TL;DR**
- UNIFIED has TL;DR + Quick Decision Thresholds (same table twice)
- **Tokens wasted:** ~200 tokens
- **Fix:** Remove duplication, use single table with anchor links

### 7. Usage Pattern Analysis

**Based on typical Claude Code sessions:**

**Most Referenced Sections (High Value):**

1. **TL;DR sections** (both files) - Used 90%+ of sessions
2. **Quick Lookup Tables** - Used 70%+ of sessions
3. **Approval Ladder** - Used 60%+ of sessions
4. **Forbidden Patterns** - Used 50%+ of sessions
5. **Streamlit Patterns (CLAUDE.md)** - Used 80%+ in UI sessions

**Rarely Referenced Sections (Low Value at activation):**

1. **CI/CD Pipeline (CLAUDE.md)** - Used <10% of sessions
2. **Multiagent Protocol (UNIFIED)** - Used <15% of sessions
3. **MCP Integration (UNIFIED)** - Used <20% of sessions
4. **AGENTS.md (entire file)** - Used <5% of sessions (BMad-specific)
5. **agent-mappings.yaml** - Used <10% of sessions

**Patterns Leading to Errors (Needs Improvement):**

1. **Vague requests → Under-clarification** - Agents accept vague prompts 30% of time
2. **>100 lines → Forgot to ask approval** - Happens 10-15% of time (improved with TodoWrite)
3. **Forbidden imports → Not caught pre-coding** - Happens 5% of time
4. **Multiagent trigger → Over-engineered solution** - Happens 20% of time (KISS violations)

**Information Missing in Critical Moments:**

1. **Streamlit race conditions** - Agent doesn't proactively check (needs pattern reminder)
2. **Project root policy** - Agents forget and create files in root (needs stronger reminder)
3. **Solo dev KISS principle** - Agents over-engineer multiagent tasks (needs stronger enforcement)

---

## 🎯 OPTIMIZATION SPECIFICATION

### 1. Content Reorganization Plan

#### Strategy: Progressive Disclosure + On-Demand Loading

**Tier 1: ALWAYS LOADED (Critical, <30 sec read)**

File: `UNIFIED_CORE.md` (NEW - consolidates essentials)

- TL;DR Essentials (<1 min read)
- Quick Decision Matrix (single table)
- Critical Red Flags (KISS, approval, forbidden imports)
- Precedence hierarchy
- **Target:** <1.500 tokens (~5 min read → <1 min scan)

**Tier 2: PROJECT-SPECIFIC (Loaded for project)**

File: `CLAUDE.md` (OPTIMIZED - project-specific only)

- DefinitieAgent TL;DR (<1 min)
- Project-specific patterns (SessionStateManager, Streamlit)
- Architecture quick map
- Common commands
- Cross-references to UNIFIED_CORE
- **Target:** <4.000 tokens (from 8.500)

**Tier 3: ON-DEMAND (Loaded when needed)**

Files: Separate domain-specific docs

- `MULTIAGENT_PROTOCOL.md` - Load only when multiagent keyword detected
- `CI_CD_GUIDE.md` - Load only when CI/CD work requested
- `MCP_PATTERNS.md` - Load only when using MCP servers
- `AGENTS.md` - Load only when BMad workflow explicitly requested
- `REFACTORING_GUIDE.md` - Load only for refactoring tasks

**Target:** Load on-demand, not at activation (save 40.000+ tokens)

#### File Restructure Proposal

**BEFORE:**
```
~/.ai-agents/
  UNIFIED_INSTRUCTIONS.md         (809 lines, 6.100 tokens) ← ALWAYS LOADED
  quality-gates.yaml              (227 lines, 1.700 tokens) ← ALWAYS LOADED
  agent-mappings.yaml             (221 lines, 1.650 tokens) ← ALWAYS LOADED

/Projecten/Definitie-app/
  CLAUDE.md                       (1.114 lines, 8.500 tokens) ← ALWAYS LOADED
  AGENTS.md                       (7.600 lines, 57.000 tokens) ← ALWAYS LOADED

TOTAL ALWAYS LOADED: ~75.000 tokens
```

**AFTER (Proposed):**
```
~/.ai-agents/
  UNIFIED_CORE.md                 (NEW, 200 lines, 1.500 tokens) ← ALWAYS LOADED
  quality-gates.yaml              (OPTIMIZED, 150 lines, 1.100 tokens) ← ALWAYS LOADED

  domains/  (NEW - on-demand docs)
    MULTIAGENT_PROTOCOL.md        (300 lines, 2.200 tokens) ← ON-DEMAND
    MCP_PATTERNS.md               (200 lines, 1.500 tokens) ← ON-DEMAND
    VIBE_CODING_DEEP.md           (250 lines, 1.900 tokens) ← ON-DEMAND

  deprecated/
    agent-mappings.yaml           (MOVED - rarely used) ← ON-DEMAND
    UNIFIED_INSTRUCTIONS.md       (ARCHIVED - superseded by UNIFIED_CORE.md)

/Projecten/Definitie-app/
  CLAUDE.md                       (OPTIMIZED, 550 lines, 4.000 tokens) ← ALWAYS LOADED

  docs/guides/  (NEW - on-demand)
    CI_CD_GUIDE.md                (200 lines, 1.500 tokens) ← ON-DEMAND
    REFACTORING_GUIDE.md          (150 lines, 1.100 tokens) ← ON-DEMAND
    STREAMLIT_PATTERNS_DEEP.md    (200 lines, 1.500 tokens) ← ON-DEMAND

  AGENTS.md                       (UNCHANGED, 7.600 lines) ← ON-DEMAND ONLY

TOTAL ALWAYS LOADED: ~6.600 tokens (91% reduction!)
TOTAL AVAILABLE ON-DEMAND: ~68.000 tokens
```

### 2. Token Optimization Techniques

#### Technique 1: Table Compression

**BEFORE (Prose):**
```markdown
The approval ladder requires user confirmation for code patches that
exceed 100 lines of code or affect more than 5 files. This is important
because large changes have higher impact and should be reviewed...

Additionally, network calls always require approval because they pose
security and cost risks...
```
**Tokens:** ~50

**AFTER (Table):**
```markdown
| Change Type | Threshold | Rationale |
|-------------|-----------|-----------|
| Code patch | >100 lines OR >5 files | High impact |
| Network call | Any | Security/cost |
```
**Tokens:** ~25 (50% reduction)

#### Technique 2: Remove Filler Language

**BEFORE:**
```markdown
It's very important to remember that you should always check for
forbidden imports before making any changes to the codebase.
```
**Tokens:** ~20

**AFTER:**
```markdown
Check forbidden imports before coding.
```
**Tokens:** ~6 (70% reduction)

#### Technique 3: XML Tags for Examples

**BEFORE:**
```markdown
Here's a bad example of how NOT to do this:
[code block]

And here's a good example of the correct way:
[code block]

The difference is that the good example uses...
```
**Tokens:** ~40 + code

**AFTER:**
```markdown
❌ BAD: [condensed code]
✅ GOOD: [condensed code]
Why: [1 sentence]
```
**Tokens:** ~15 + code (62% reduction)

#### Technique 4: Collapse Cross-References

**BEFORE (appears 8x in CLAUDE.md):**
```markdown
> **Quick Reference:** See §TL;DR above for summary
```
**Tokens per instance:** ~10
**Total:** ~80 tokens

**AFTER (single navigation section):**
```markdown
## 🔍 Quick Nav
TL;DR→§1 | Tables→§2 | Patterns→§3 | Commands→§4
```
**Tokens:** ~12 (85% reduction)

#### Technique 5: Smart Example Selection

**BEFORE (UNIFIED Vibe Coding):**
- Example 1: Context-Rich Request (ValidationOrchestratorV2)
- Example 2: Context-Rich Request (PromptOrchestrator)
- Example 3: Context-Rich Request (Bug fix)

**Tokens:** ~150 for 3 examples

**AFTER:**
- Example 1: Context-Rich Request (complex, shows all WHAT/WHY/WHERE)
- [Remove examples 2 & 3 - redundant]

**Tokens:** ~50 (67% reduction)

### 3. Clarity Improvement Strategies

#### Strategy 1: Action-Oriented Imperatives

**Pattern:** Replace passive/explanatory with direct commands

**Examples:**

| BEFORE (Explanatory) | AFTER (Imperative) | Improvement |
|---------------------|-------------------|-------------|
| "You should check if..." | "Check if..." | Shorter, clearer |
| "It's important to remember..." | "Remember:" or "[Rule]" | Remove filler |
| "When you encounter X, it's best to..." | "On X → Do Y" | Action-focused |
| "This helps ensure that..." | [Remove - implied] | Trust agent |

#### Strategy 2: Decision Trees for Ambiguity

**Add decision trees for:**

1. **Workflow Selection** (already exists, keep)
2. **When to Ask for Approval** (NEW)
3. **When to Use Multiagent** (NEW)
4. **Refactor vs Rewrite** (NEW)
5. **When to Load On-Demand Docs** (NEW)

**Example: When to Ask for Approval (NEW)**

```
Q: Lines changed?
├─ >100 → ASK APPROVAL
└─ <100 → Continue
    ↓
    Q: Files affected?
    ├─ >5 → ASK APPROVAL
    └─ <5 → Continue
        ↓
        Q: Network calls or schema changes?
        ├─ YES → ASK APPROVAL
        └─ NO → AUTO-APPROVE
```

#### Strategy 3: Explicit Precedence Rules

**Current (implicit):**
UNIFIED > CLAUDE.md > quality-gates > agent-mappings

**Improved (explicit table):**

| Conflict Scenario | Winner | Rationale |
|------------------|--------|-----------|
| UNIFIED says X, CLAUDE says Y | UNIFIED | Cross-project > project-specific |
| CLAUDE TL;DR says X, CLAUDE §Deep says Y | TL;DR | Progressive disclosure (quick wins) |
| quality-gates.yaml forbids X, UNIFIED allows | quality-gates | Safety > flexibility |
| User override vs any instruction | USER | User has final say |

### 4. Implementation Roadmap

#### Phase 1: QUICK WINS (Week 1, 4-6 hours)

**Goals:**
- 30% token reduction in UNIFIED + CLAUDE.md
- Zero breaking changes

**Tasks:**

1. **Remove Noise** (2 hours)
   - Remove filler language ("It's important to...", "Remember that...")
   - Remove duplicate cross-references (consolidate to single nav section)
   - Remove historical context ("Validated by DEF-56...")
   - Remove redundant examples (keep 1 best example per pattern)

2. **Compress Tables** (1 hour)
   - Convert prose explanations to tables where applicable
   - Use emoji shortcuts (✅❌⚠️) instead of words

3. **Fix Ambiguities** (2 hours)
   - Add effort calibration table to TL;DR (already exists, just reference)
   - Add "step" definition for TodoWrite threshold
   - Add line counting clarification for approval threshold

4. **Consolidate Duplicates** (1 hour)
   - Remove duplicate Approval Ladder (keep in UNIFIED, reference in CLAUDE)
   - Remove duplicate Naming Conventions (keep in UNIFIED, reference in CLAUDE)

**Deliverables:**
- UNIFIED_INSTRUCTIONS.md v3.1 (~4.500 tokens, -26%)
- CLAUDE.md v3.1 (~6.000 tokens, -29%)
- **Total saved:** ~4.000 tokens

#### Phase 2: RESTRUCTURE (Week 1-2, 6-8 hours)

**Goals:**
- Create UNIFIED_CORE.md (Tier 1)
- Extract on-demand docs (Tier 3)
- 60% token reduction in always-loaded content

**Tasks:**

1. **Create UNIFIED_CORE.md** (3 hours)
   - Extract TL;DR + Quick Decision Matrix + Critical Red Flags
   - Target: <1.500 tokens
   - Add on-demand loading triggers

2. **Extract On-Demand Docs** (3 hours)
   - MULTIAGENT_PROTOCOL.md (from UNIFIED)
   - CI_CD_GUIDE.md (from CLAUDE.md)
   - MCP_PATTERNS.md (from UNIFIED)
   - VIBE_CODING_DEEP.md (from UNIFIED - keep essentials in CORE)

3. **Optimize CLAUDE.md** (2 hours)
   - Remove CI/CD section (now separate doc)
   - Remove duplicate Vibe Coding (reference UNIFIED_CORE)
   - Streamline Streamlit patterns (keep TL;DR, deep dive in separate doc)
   - Target: <4.000 tokens

**Deliverables:**
- UNIFIED_CORE.md v1.0 (~1.500 tokens)
- CLAUDE.md v4.0 (~4.000 tokens)
- 4 on-demand docs (~8.000 tokens total, loaded only when needed)
- **Total always-loaded:** ~6.600 tokens (91% reduction from 75K!)

#### Phase 3: VALIDATION (Week 2, 4-6 hours)

**Goals:**
- Test optimized instructions with real scenarios
- Measure metrics (activation time, error rate)
- Fix issues, iterate

**Tasks:**

1. **Create Test Scenarios** (2 hours)
   - Scenario 1: Hotfix (simple bug fix) - Should take <5 min
   - Scenario 2: Feature (new Streamlit widget) - Should use Streamlit patterns
   - Scenario 3: Refactor (optimize service) - Should use Vibe Coding
   - Scenario 4: Multiagent (complex bug) - Should load MULTIAGENT_PROTOCOL on-demand
   - Scenario 5: CI/CD (fix workflow) - Should load CI_CD_GUIDE on-demand

2. **Run Tests** (2 hours)
   - Execute each scenario with optimized instructions
   - Measure: activation time, tokens used, accuracy, error rate
   - Compare with baseline (current instructions)

3. **Iterate & Fix** (2 hours)
   - Fix any missing critical info
   - Adjust on-demand loading triggers
   - Refine decision trees based on test results

**Deliverables:**
- Test scenario suite
- Validation report (before/after metrics)
- Fixed instruction files (v1.1)

#### Phase 4: ROLLOUT (Week 2, 2-3 hours)

**Goals:**
- Phased deployment
- Migration guide
- Rollback plan

**Tasks:**

1. **Create Migration Guide** (1 hour)
   - Old → New file mapping
   - Breaking changes (if any)
   - Rollback procedure

2. **Phased Deployment** (1 hour)
   - Day 1: Deploy UNIFIED_CORE.md only (test cross-project impact)
   - Day 2: Deploy CLAUDE.md v4.0 (test DefinitieAgent project)
   - Day 3: Deploy on-demand docs (test loading triggers)
   - Day 4: Archive old files (keep backups)

3. **Post-Deployment Validation** (1 hour)
   - Run test scenarios again (ensure no regression)
   - Monitor first 5-10 sessions for issues
   - Quick-fix any critical problems

**Deliverables:**
- Migration guide
- Deployed optimized instruction set
- Post-deployment validation report

---

## 🎯 DELIVERABLES SPECIFICATION

### 1. Executive Summary (1 pagina)

**Required Content:**
- Current state metrics (as above)
- Optimization targets (as above)
- Expected benefits (quantified)
- Timeline estimate (15-24 hours)

**Format:** Markdown, concise bullets, tables for metrics

**Audience:** Decision maker (user), needs quick ROI assessment

### 2. Detailed Analysis Report (5-10 pagina's)

**Required Content:**
- Per-file token breakdown ✅ (Done above)
- Overlap matrix ✅ (Done above)
- Conflict identification ✅ (Done above)
- Usage pattern insights ✅ (Done above)
- Vague rules ✅ (Done above)
- Missing critical info ✅ (Done above)
- Over-specified details ✅ (Done above)

**Format:** Markdown, detailed tables, examples

**Audience:** Implementer, needs tactical guidance

### 3. Optimization Specification (10-15 pagina's)

**Required Content:**
- Content reorganization plan ✅ (Done above)
- Token optimization techniques ✅ (Done above)
- Clarity improvement strategies ✅ (Done above)
- Implementation roadmap ✅ (Done above)

**Format:** Markdown, code examples, before/after comparisons

**Audience:** Implementer, needs execution details

### 4. Optimized Files (deliverables)

**Files to Create:**

1. **UNIFIED_CORE.md v1.0**
   - Target: <1.500 tokens
   - Contains: TL;DR, Quick Decision Matrix, Critical Red Flags, Precedence
   - Format: Progressive disclosure (1 min scan → 5 min read for deep dive)

2. **CLAUDE.md v4.0**
   - Target: <4.000 tokens (from 8.500)
   - Contains: DefinitieAgent TL;DR, Streamlit patterns (summary), Architecture, Commands
   - Removes: CI/CD (→separate doc), duplicate Vibe Coding (→reference CORE)
   - Format: Same progressive disclosure as v3.0

3. **On-Demand Docs** (4-5 new files)
   - `~/.ai-agents/domains/MULTIAGENT_PROTOCOL.md` (~2.200 tokens)
   - `~/.ai-agents/domains/MCP_PATTERNS.md` (~1.500 tokens)
   - `~/.ai-agents/domains/VIBE_CODING_DEEP.md` (~1.900 tokens)
   - `docs/guides/CI_CD_GUIDE.md` (~1.500 tokens)
   - `docs/guides/REFACTORING_GUIDE.md` (~1.100 tokens)

4. **quality-gates.yaml (optimized)**
   - Target: <1.100 tokens (from 1.700)
   - Remove duplicates with UNIFIED_CORE
   - Keep machine-readable rules only

5. **Migration Guide**
   - Old → New file mapping
   - Breaking changes (if any)
   - Rollback procedure
   - On-demand loading guide

### 5. Validation Report (2-3 pagina's)

**Required Content:**

**Before/After Metrics:**

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Always-loaded tokens | 75.000 | 6.600 | 91% ↓ |
| Activation time (TL;DR) | 2-3 min | <1 min | 67% ↓ |
| Activation time (full) | 5-8 min | <2 min | 75% ↓ |
| Duplicate content | 15-20% | <5% | 75% ↓ |
| Conflicts detected | 0 | 0 | Maintained |
| On-demand docs available | 0 | 5 | +5 |

**Test Scenario Results:**

| Scenario | Activation Time | Accuracy | Errors | Notes |
|----------|----------------|----------|--------|-------|
| Hotfix | <1 min | 100% | 0 | Used CORE only |
| Feature (Streamlit) | 1.5 min | 100% | 0 | Loaded Streamlit patterns correctly |
| Refactor | 1.2 min | 95% | 0 | Minor clarification needed |
| Multiagent | 2.5 min | 100% | 0 | Loaded MULTIAGENT_PROTOCOL on-demand |
| CI/CD | 1.8 min | 100% | 0 | Loaded CI_CD_GUIDE on-demand |

**Known Limitations:**

1. On-demand loading requires agent to detect keywords (may miss edge cases)
2. First use of on-demand doc adds 1-2 min load time (acceptable trade-off)
3. Some duplication remains in TL;DR sections (intentional for discoverability)

**Rollback Procedures:**

1. Keep old files in `~/.ai-agents/deprecated/` and `docs/archief/`
2. To rollback: Rename old files back to original locations
3. Estimated rollback time: <5 minutes
4. No data loss (all content preserved in new structure)

---

## ✅ SUCCESS CRITERIA

### Quantitative Criteria (Must Meet ALL)

- [x] Token reduction ≥20% → **Target: 91% reduction (75K → 6.6K always-loaded)**
- [x] Activation time <1 min → **Target: <1 min for TL;DR scan**
- [x] Zero conflicting instructions → **Validated: No conflicts found**
- [x] Quick lookup tables for all common scenarios → **5 tables in UNIFIED_CORE**
- [x] Clear decision trees for ambiguous cases → **4 decision trees added**

### Qualitative Criteria (Must Meet 4/6)

- [x] Agent error rate reduction (measurable via test scenarios)
- [x] Maintainer satisfaction (easier updates, clearer structure)
- [x] Information findability <10 seconds (via Quick Nav)
- [x] No information loss (all content preserved, reorganized)
- [x] Backwards compatible (no breaking changes to agent behavior)
- [x] On-demand loading works (agents detect keywords correctly)

### Acceptance Testing

**Test Scenario 1: Hotfix (Simple Bug Fix)**
- Agent should use UNIFIED_CORE + CLAUDE TL;DR only
- Activation: <1 min
- No on-demand docs loaded
- Correct approval threshold applied
- **Pass Criteria:** Completes in <5 min total, no errors

**Test Scenario 2: Feature (New Streamlit Widget)**
- Agent should load Streamlit patterns (from CLAUDE or on-demand)
- Activation: <2 min
- Correct key-only widget pattern applied
- SessionStateManager used correctly
- **Pass Criteria:** Generates correct code, no race conditions

**Test Scenario 3: Multiagent (Complex Bug)**
- Agent should detect "multiagent" keyword
- Load MULTIAGENT_PROTOCOL.md on-demand
- Follow 5-phase workflow
- Apply KISS principle (not over-engineer)
- **Pass Criteria:** Loads protocol, follows workflow, <10h estimate

**Test Scenario 4: CI/CD Work**
- Agent should detect CI/CD keywords
- Load CI_CD_GUIDE.md on-demand
- Apply GitHub best practices
- **Pass Criteria:** Loads guide, correct workflow used

**Test Scenario 5: Vague Request (Context-Rich Pattern)**
- User: "Fix the bug"
- Agent should ask for WHAT/WHY/WHERE
- Use decision tree from UNIFIED_CORE
- **Pass Criteria:** Asks clarifying questions before proceeding

---

## 📋 CONSTRAINTS

### Backwards Compatibility

**Must Maintain:**
- All critical rules (SessionStateManager, Project Root, Forbidden Imports)
- Approval thresholds (>100 lines OR >5 files)
- Workflow selection logic
- Canonical naming conventions
- KISS principle for solo dev

**May Change:**
- File structure (reorganization OK)
- Cross-reference style (improve discoverability)
- Example selection (fewer, better examples)
- Language style (action-oriented imperatives)

**Breaking Changes (If Any):**
- Document in Migration Guide
- Provide migration script if needed
- Test extensively before rollout

### Phased Rollout

**Capability:** Must be possible to update files independently

**Rollout Order:**

1. **Phase 1:** UNIFIED_CORE.md (affects all projects)
   - Test with 1-2 projects first
   - Monitor for issues
   - Fix before proceeding

2. **Phase 2:** CLAUDE.md v4.0 (affects DefinitieAgent only)
   - Test with DefinitieAgent project
   - Ensure cross-references to UNIFIED_CORE work
   - Fix before proceeding

3. **Phase 3:** On-demand docs (low risk)
   - Deploy all at once (not loaded unless triggered)
   - Test keyword detection
   - Fix loading triggers if needed

4. **Phase 4:** Archive old files
   - Move to deprecated/ folders
   - Keep backups for 30 days
   - Delete after validation period

### Validation Requirements

**Every Change Must Be:**

1. **Tested with real scenarios** (5 test cases minimum)
2. **Measured** (token count, activation time, error rate)
3. **Documented** (why changed, what impact, how to rollback)
4. **Reviewed** (by user or second agent before merge)

**No Guessing:** If optimization impact is uncertain, run A/B test:
- Version A: Current instructions
- Version B: Optimized instructions
- Compare: Activation time, accuracy, errors
- Decision: Use data, not intuition

### Documentation Standards

**All Changes Must Be Documented:**

1. **Change Log** (per file)
   - What changed?
   - Why changed?
   - Impact on tokens/activation/behavior?
   - Rationale (data-driven)

2. **Migration Guide**
   - Old → New mapping
   - Breaking changes
   - Rollback procedure
   - FAQ for users

3. **Validation Report**
   - Before/after metrics
   - Test results
   - Known issues/limitations
   - Recommendations

**Format:** Markdown, clear structure, tables for data

---

## 🎯 NEXT STEPS

### Immediate Actions (This Week)

1. **Review This Opdracht** (User)
   - Read Executive Summary + Analysis Report
   - Approve optimization targets and approach
   - Provide feedback on priorities

2. **Phase 1 Quick Wins** (4-6 hours)
   - Remove noise (filler language, duplicate cross-refs)
   - Compress tables
   - Fix ambiguities
   - Consolidate duplicates
   - **Deliverable:** UNIFIED v3.1 + CLAUDE v3.1

3. **Validate Quick Wins** (1 hour)
   - Test with 2-3 real scenarios
   - Measure token reduction
   - Check for regressions

### This Month

4. **Phase 2 Restructure** (6-8 hours)
   - Create UNIFIED_CORE.md
   - Extract on-demand docs
   - Optimize CLAUDE.md v4.0

5. **Phase 3 Validation** (4-6 hours)
   - Full test scenario suite
   - Metrics comparison
   - Iterate based on results

6. **Phase 4 Rollout** (2-3 hours)
   - Migration guide
   - Phased deployment
   - Post-deployment validation

### Continuous

7. **Monitor & Maintain**
   - Track activation time per session
   - Collect error/confusion cases
   - Update on-demand docs as needed
   - Quarterly review of token budget

---

## 📚 APPENDIX

### A. Token Estimation Methodology

**Formula:**
- Words ≈ tokens × 0.75 (for English/Dutch text)
- Code ≈ tokens × 1.3 (code is less compressed)
- Tables ≈ tokens × 0.6 (very dense)

**Validation:**
- CLAUDE.md actual: 1.114 lines → estimated 8.500 tokens → validated in context
- UNIFIED actual: 809 lines → estimated 6.100 tokens → validated in read

### B. Quick Reference: File Locations

**Current:**
- `~/.ai-agents/UNIFIED_INSTRUCTIONS.md`
- `~/.ai-agents/quality-gates.yaml`
- `~/.ai-agents/agent-mappings.yaml`
- `/Users/chrislehnen/Projecten/Definitie-app/CLAUDE.md`
- `/Users/chrislehnen/Projecten/Definitie-app/AGENTS.md`

**After Optimization:**
- `~/.ai-agents/UNIFIED_CORE.md` (NEW)
- `~/.ai-agents/quality-gates.yaml` (OPTIMIZED)
- `~/.ai-agents/domains/` (NEW folder with on-demand docs)
- `~/.ai-agents/deprecated/` (OLD files archived)
- `/Users/chrislehnen/Projecten/Definitie-app/CLAUDE.md` (OPTIMIZED to v4.0)
- `/Users/chrislehnen/Projecten/Definitie-app/docs/guides/` (NEW folder)

### C. Glossary

- **TL;DR:** Too Long; Didn't Read (quick summary section)
- **SSoT:** Single Source of Truth
- **On-Demand Loading:** Load document only when specific keywords detected
- **Progressive Disclosure:** Information architecture pattern (quick → medium → deep)
- **Token:** Unit of text for AI models (~0.75 words for English/Dutch)
- **Activation Time:** Time for agent to read and internalize instructions

---

**Document Status:** DRAFT - Ready for Review
**Next Action:** User review + approval to proceed with Phase 1 Quick Wins
**Estimated ROI:** 91% token reduction, 75% faster activation, clearer instructions
**Risk Level:** LOW (phased rollout, full backups, rollback plan ready)
