# Vibe Coding Pattern Catalog - DefinitieAgent

<!--
metadata:
  document_id: "vibe-coding-patterns"
  title: "Vibe Coding Pattern Catalog"
  version: "1.0.0"
  last_updated: "2025-01-27"
  author: "DefinitieAgent Team"
  status: "active"
  applies_to:
    - "Claude Sonnet 4.5"
    - "Claude Opus"
    - "GPT-4"
    - "GPT-4 Turbo"
  prerequisites:
    - "CLAUDE.md → Project Overzicht"
    - "UNIFIED_INSTRUCTIONS.md → APPROVAL LADDER"
    - "BMad Method basics (optional)"
  related_documents:
    - "CLAUDE.md → AI-Assisted Development"
    - "docs/methodologies/vibe-coding/GUIDE.md"
    - "docs/methodologies/vibe-coding/templates/"
  pattern_count: 9
  difficulty_range: ["beginner", "intermediate", "advanced"]
-->

## 📋 Overzicht

Dit document bevat de volledige catalog van Vibe Coding patterns voor DefinitieAgent. Vibe Coding is een intent-driven methodologie voor AI-assisted development die maximaliseert wat AI kan bereiken door strategische prompt patterns en brownfield-aware workflows.

**Voor een beknopt overzicht:** Zie `CLAUDE.md` → sectie "AI-Assisted Development met Vibe Coding"

---

## 🎯 Core Principes

<principle type="intent-driven" id="principle-intent">

### Intent-Driven Development

Focus op **WAT** je wil bereiken (doel), niet **HOE** technisch (implementatie).

**Waarom:**

- AI is excellent in pattern recognition en oplossingszoeken
- Technische specificatie beperkt AI creativiteit
- Intent geeft context voor betere beslissingen
- Natuurlijke taal werkt beter dan pseudo-code

**Voorbeeld:**

```text
❌ "Use functools.lru_cache decorator on get_rules function"
✅ "Reduce rule loading time from 10x to 1x during startup"
```

</principle>

<principle type="brownfield" id="principle-brownfield">

### Brownfield Context Awareness

DefinitieAgent is een brownfield project. Dit vereist speciale aandacht voor:

**Archaeology First:**

- Analyseer EERST bestaande code voordat wijzigen
- Begrijp WAAROM code geschreven is zoals het is
- Identificeer business logica vs technische debt

**Business Logic Preservation:**

- Extraheer business regels tijdens refactoring
- Documenteer domeinkennis in comments en docs
- Test business invariants na wijzigingen

**No Backwards Compatibility:**

- DefinitieAgent is single-user applicatie
- GEEN feature flags of parallelle V1/V2 paden
- Refactor direct, geen gradual migration
- Focus op code verbeteren, niet compatibility

**Surgical Strikes:**

- Kleine, focused changes i.p.v. complete rewrites
- Wijzig 1 concern per sessie
- Test na elke change, rollback if failures

</principle>

---

## 📖 Pattern Catalog

### Pattern 1: Context-Rich Requests

<pattern id="context-rich" category="prompting" difficulty="intermediate" token_budget="150">

#### Beschrijving

Context-rich requests leveren beste resultaten door AI volledige context te geven over locatie, probleem, verwacht gedrag, en oplossingsrichting.

#### Anti-Pattern

<example type="anti-pattern">

```text
❌ "Fix the validation bug"
```

**Problemen:**

- Geen context over welke validatie
- Geen locatie waar bug zit
- Geen beschrijving van bug behavior
- Geen verwacht gedrag

**Resultaat:** AI moet gissen, grote kans op verkeerde fix

</example>

#### Best Practice

<example type="best-practice">

```text
✅ "In ValidationOrchestratorV2, the 45 validation rules are
    being loaded 10x during startup (see init logs).
    Root cause: No caching in loader.py.

    Check US-202 analysis in docs/reports/toetsregels-caching-fix.md
    and implement RuleCache in src/toetsregels/rule_cache.py with
    @cached decorator for bulk loading (TTL: 3600s).

    Expected: 77% faster, 81% less memory.
    Test: pytest tests/services/test_definition_validator.py"
```

**Waarom beter:**

- Specificeert exact component (ValidationOrchestratorV2)
- Quantificeert probleem (10x laden, 45 regels)
- Geeft root cause (geen caching in loader.py)
- Verwijst naar analyse document (US-202)
- Specificeert oplossingsrichting (RuleCache + @cached)
- Geeft verwachte impact (77% faster, 81% less memory)
- Specificeert test (pytest command)

</example>

#### When to Use

**Altijd bij:**

- Complex refactoring tasks
- Performance optimalisaties met metrics
- Bug fixes in onbekende code
- Brownfield archaeology sessions

**Timing:**

- 5-15 minuten voorbereiding (gather context)
- Bespaart 30-60 minuten debug/trial-and-error

#### Pattern Components

<components>

1. **Component identificatie** - Waar zit het probleem?
2. **Probleem quantificatie** - Hoe erg is het? (metrics)
3. **Root cause** - Wat is de oorzaak? (als bekend)
4. **Referentie documenten** - Waar staat analyse?
5. **Oplossingsrichting** - Wat is de aanpak? (niet exact implementation)
6. **Expected impact** - Wat verwacht je te bereiken?
7. **Test criteria** - Hoe valideer je success?

</components>

#### Success Criteria

- ✅ AI begrijpt probleem first-try (geen clarifying questions)
- ✅ Oplossing werkt zonder iteraties
- ✅ Expected metrics bereikt (±10%)

#### Token Budget

**Target:** 120-180 tokens (~30-45 regels)

**Distribution:**

- Context: 40 tokens
- Problem description: 40 tokens
- Solution guidance: 40 tokens
- References: 30 tokens

</pattern>

---

### Pattern 2: Business-First Refactoring

<pattern id="business-first" category="refactoring" difficulty="advanced" token_budget="150">

#### Beschrijving

Business-first refactoring behoudt domeinkennis tijdens code restructuring. Focus op WAAROM code bestaat voordat je wijzigt HOE het geïmplementeerd is.

#### Anti-Pattern

<example type="anti-pattern">

```text
❌ "Refactor dry_helpers.py"
```

**Problemen:**

- Geen focus op business logica
- Risico op verloren domeinkennis
- Onduidelijk wat "refactor" betekent
- Geen guidance over responsibility split

**Resultaat:** Code wordt "schoner" maar business logica verdwijnt in process

</example>

#### Best Practice

<example type="best-practice">

```text
✅ "dry_helpers.py is a god object violating Single Responsibility Principle.

    Analysis shows 3 distinct business concerns:
    1. Type safety (ensure_list, ensure_dict)
       → Purpose: Guarantee downstream functions receive correct types
    2. Dictionary operations (safe_dict_get)
       → Purpose: Safe access to nested config without KeyErrors
    3. Validation utilities
       → Purpose: Input validation for user-provided data

    Refactor strategy:
    - Create utils/type_helpers.py for concern #1
    - Create utils/dict_helpers.py for concern #2
    - Create utils/validation_helpers.py for concern #3
    - Update all imports (expect ~15 files)
    - Run full test suite after each move

    PRESERVE business logic comments explaining WHY each function exists.
    Document extracted patterns in module docstrings.

    Estimate: 8 files modified, 45 minutes
    Show me proposed structure before executing."
```

**Waarom beter:**

- Identificeert specifieke concerns met business rationale
- Definieert duidelijke verantwoordelijkheden per module
- Expliciet: PRESERVE business logica
- Gefaseerde aanpak met testing
- "Show me first" voor approval

</example>

#### When to Use

- God object cleanup
- Legacy code modernization
- Business logic extraction
- Domain knowledge preservation

#### Pattern Components

<components>

1. **Identify concerns** - Welke business concerns zijn er?
2. **Document purpose** - WAAROM bestaat elke concern?
3. **Define modules** - Welke nieuwe modules? Wat is hun verantwoordelijkheid?
4. **Preservation strategy** - Hoe behoud je business kennis?
5. **Phased approach** - Volgorde van changes met testing
6. **Documentation requirements** - Wat moet gedocumenteerd?

</components>

#### Success Criteria

- ✅ Alle business logica behouden (0 functionaliteit verloren)
- ✅ Tests passing (100% na refactor)
- ✅ Business logic comments preserved/improved
- ✅ Clear module responsibilities (single concern per module)

#### Real Example from DefinitieAgent

**Scenario:** dry_helpers.py cleanup (November 2024)

**Prompt used:**

```text
"dry_helpers.py contains mixed responsibilities. Extract:
- Type conversions → utils/type_helpers.py
- Dict operations → utils/dict_helpers.py
Preserve all docstrings explaining business rules.
Run tests after each extraction."
```

**Outcome:**

- 8 files modified
- 0 test failures
- Business logica intact
- Time: 42 minutes (estimated: 45)

**Pattern used:** Business-First Refactoring + Show Me First

</pattern>

---

### Pattern 3: Incremental Changes

<pattern id="incremental" category="workflow" difficulty="beginner" token_budget="120">

#### Beschrijving

Incremental changes volgen DefinitieAgent filosofie: kleine stappen, meetbare progress, rollback mogelijk. GEEN big bang rewrites.

#### Anti-Pattern

<example type="anti-pattern">

```text
❌ "Rewrite the entire prompt system"
```

**Problemen:**

- Te grote scope (ondefinieerbaar)
- Geen rollback mogelijk
- Hoog risico bij failures
- Geen meetbare milestones

**Resultaat:** Days of work, unclear progress, stuck if issues arise

</example>

#### Best Practice

<example type="best-practice">

```text
✅ "Reduce PromptOrchestrator token usage from 7.250 to <5.000 tokens.

    Phased approach:

    Phase 1: Identify duplicates (30 min)
    - Analyze all prompt fragments
    - Find duplicate patterns
    - Document top 5 duplicates
    - Measure: List duplicates with token counts

    Phase 2: Implement shared cache (1 hour)
    - Create prompt_cache.py with deduplication
    - Integrate into PromptOrchestrator
    - Test with existing 45 validation rules
    - Measure: Token count after dedup

    Phase 3: Validate impact (30 min)
    - Run full test suite
    - Measure actual token reduction
    - Document in docs/reports/
    - Target: 7.250 → <5.000 tokens

    STOP after each phase if issues. Rollback if needed."
```

**Waarom beter:**

- Gefaseerd met duidelijke milestones
- Meetbare targets per fase
- Tijdsestimates per fase
- Test na elke fase
- Explicit rollback strategy

</example>

#### When to Use

- Performance optimalisaties
- Refactoring sessions
- Feature additions
- Risk-averse scenarios

#### Pattern Components

<components>

1. **Overall goal** - Wat is eindresultaat? (meetbaar)
2. **Phase breakdown** - 3-5 phases, elk 30-90 min
3. **Per-phase deliverable** - Wat levert fase op?
4. **Per-phase validation** - Hoe test je fase?
5. **Rollback strategy** - Wat als fase faalt?

</components>

#### Success Criteria

- ✅ Elk phase completes successfully
- ✅ Overall goal bereikt (metrics match target)
- ✅ Geen regressions (all tests passing)

</pattern>

---

### Pattern 4: Show Me First

<pattern id="show-me-first" category="workflow" difficulty="beginner" token_budget="80">

#### Beschrijving

"Show Me First" is safety pattern: AI toont proposed changes VOORDAT executing. Gebruik dit ALTIJD bij >100 lines changes (UNIFIED approval ladder).

#### Template

```text
"Before [ACTION], show me:
 1. [CURRENT STATE]
 2. [IDENTIFIED ISSUES]
 3. [PROPOSED NEW STATE]
 4. [IMPACT ANALYSIS]
 Then wait for approval."
```

#### Example

```text
"Before refactoring PromptServiceV2, show me:
 1. Current structure and responsibilities
 2. Identified duplication patterns
 3. Proposed new structure
 4. Impact analysis (files affected, test coverage)
 Then wait for approval."
```

#### When to Use

**MANDATORY bij:**

- >100 lines changes (UNIFIED APPROVAL LADDER)
- >5 files touched
- Schema changes
- Architectural changes

**RECOMMENDED bij:**

- Unfamiliar code
- Complex refactorings
- Production-critical code

#### Success Criteria

- ✅ AI toont proposed structure BEFORE executing
- ✅ User heeft tijd voor review
- ✅ Changes match approved proposal

</pattern>

---

### Pattern 5: Archaeology First

<pattern id="archaeology-first" category="analysis" difficulty="intermediate" token_budget="100">

#### Beschrijving

Archaeology First: Begrijp bestaande code VOORDAT wijzigen. Kritiek voor brownfield projects zoals DefinitieAgent.

#### Template

```text
"Analyze [COMPONENT] to understand:
 - [BUSINESS LOGIC QUESTION]
 - [ARCHITECTURE QUESTION]
 - [DEPENDENCY QUESTION]
 Document findings before suggesting changes."
```

#### Example

```text
"Analyze src/services/validation/ to understand:
 - Why 45 rules organized by ARAI/CON/ESS/INT/SAM/STR/VER categories?
 - Business logic behind priority levels (high/medium/low)?
 - Dependencies between validation rules?
 - Historical context: Why dual JSON+Python format?
 Document findings in analysis.md before suggesting changes."
```

#### When to Use

- Unknown codebase exploration
- Legacy code modernization
- Before major refactorings
- Business logic extraction

#### Success Criteria

- ✅ Business rationale documented
- ✅ Architecture decisions explained
- ✅ Dependencies mapped
- ✅ NO changes made during archaeology

</pattern>

---

### Pattern 6: Test-Driven Refactor

<pattern id="test-driven-refactor" category="testing" difficulty="advanced" token_budget="120">

#### Beschrijving

Test-Driven Refactor: Definieer constraints VOORDAT refactoring. Rollback bij test failures.

#### Template

```text
"Refactor [COMPONENT] with these constraints:
 1. MUST [HARD CONSTRAINT]
 2. CANNOT [FORBIDDEN ACTION]
 3. SHOULD [SOFT GOAL]
 4. Run tests after each change, rollback if failures"
```

#### Example

```text
"Refactor SessionStateManager with these constraints:
 1. MUST maintain 100% existing test coverage (currently 98%)
 2. CANNOT break st.session_state isolation rule
 3. SHOULD improve performance (current: 200ms, target: <150ms)
 4. Run tests after each change, rollback if failures

 Test command: pytest tests/utils/test_session_state.py -v"
```

#### When to Use

- Refactoring critical components
- When test coverage exists (>80%)
- Performance-sensitive code
- State management changes

#### Success Criteria

- ✅ All constraints satisfied (MUST, CANNOT, SHOULD)
- ✅ Zero test failures
- ✅ Performance target met (if specified)

</pattern>

---

## 🚫 Anti-Patterns

<anti_patterns>

### Anti-Pattern 1: Vague Requests

<anti_pattern type="vague-request" severity="high">

**Pattern:**

```text
❌ "Make it better"
❌ "Optimize the code"
❌ "Fix the bug"
```

**Waarom problematisch:**

- AI kan niet bepalen wat "better" betekent
- Geen context voor prioritization
- Resultaat kan conflicteren met jouw bedoeling

**Fix:**

```text
✅ "Reduce validation time from 5s to <2s"
✅ "Improve code readability: extract functions >50 lines"
✅ "Fix KeyError in config loading when 'optional_key' missing"
```

</anti_pattern>

### Anti-Pattern 2: Tech-First

<anti_pattern type="tech-first" severity="medium">

**Pattern:**

```text
❌ "Use functools.lru_cache"
❌ "Implement singleton pattern"
```

**Waarom problematisch:**

- AI volgt instructie blind
- Mist betere alternatieven
- Geen context waarom deze techniek

**Fix:**

```text
✅ "Cache rule loading to prevent 10x reload during startup"
✅ "Ensure only 1 ServiceContainer instance across app"
```

</anti_pattern>

### Anti-Pattern 3: No Context

<anti_pattern type="no-context" severity="high">

**Pattern:**

```text
❌ "Fix test_definition_generator.py"
```

**Waarom problematisch:**

- AI gist wat "fix" betekent
- Geen info over welke test faalt
- Geen verwacht gedrag

**Fix:**

```text
✅ "test_generate_with_examples fails with AttributeError:
    'NoneType' object has no attribute 'strip'.
    Expected: Generate definition with 3 examples.
    Root cause: examples list can be None but code expects list."
```

</anti_pattern>

### Anti-Pattern 4: Big Scope

<anti_pattern type="big-scope" severity="high">

**Pattern:**

```text
❌ "Optimize everything"
❌ "Refactor the entire codebase"
```

**Waarom problematisch:**

- Overwelming (AI + user)
- Geen meetbaar resultaat
- Hoog risico failures

**Fix:**

```text
✅ "Optimize ValidationOrchestrator: reduce from 5s to <2s"
✅ "Refactor god object: src/utils/dry_helpers.py → 3 focused modules"
```

</anti_pattern>

</anti_patterns>

---

## 🔗 Integration met Workflows

### Met BMad Method

**Relatie:**

- Vibe Coding = **HOW** to prompt agents (execution)
- BMad Method = **WHAT** to build (planning)

**Usage:**

- Gebruik Vibe patterns in BMad task execution
- Example: BMad task "Refactor validation module" → Use "Business-First Refactoring" pattern

### Met TDD Workflow (UNIFIED)

**Mapping:**

| UNIFIED Workflow | Vibe Pattern | When to Use |
|-----------------|--------------|-------------|
| ANALYSIS | Archaeology First | Unknown codebase |
| DOCUMENT | Context-Rich Request | Documentation updates |
| REFACTOR | Business-First + Test-Driven | Legacy code |
| FULL_TDD | Test-Driven Refactor | New features |
| HOTFIX | Context-Rich + Incremental | Bug fixes |

### Met UNIFIED Approval Ladder

**Rules:**

- **>100 lines change** → ALTIJD "Show Me First" pattern
- **>5 files touched** → Request impact analysis eerst
- **Schema changes** → Archaeology + approval voor uitvoering
- **Network calls** → Document API contract + error handling

---

## 📊 Pattern Testing & Validation

### Why Test Patterns?

Vibe Coding patterns werken verschillend per model/versie. Testing valideert effectiviteit.

### Test Process

<testing_framework>

#### 1. Baseline Metrics

Meet current state VOOR pattern application:

- Time (how long does task take manually?)
- Quality (how many bugs? test coverage?)
- Token usage (how many tokens consumed?)

#### 2. Apply Pattern

Gebruik documented Vibe pattern:

- Follow pattern template exact
- Record exact prompt used
- Note any deviations from template

#### 3. Measure Outcome

Compare tegen baseline:

- Time saved (%)
- Quality improvement (bugs prevented, coverage increased)
- Token efficiency (tokens used vs manual)

#### 4. Document

Record in `docs/methodologies/vibe-coding/results/`:

```yaml
pattern_id: "context-rich"
date: "2025-01-27"
model: "Claude Sonnet 4.5"
task_description: "Fix validation bug in US-202"
baseline:
  time_manual: "90 minutes"
  quality: "2 iterations needed"
  token_usage: "N/A"
with_pattern:
  time: "35 minutes"
  quality: "1 iteration, worked first try"
  token_usage: "450 tokens"
improvement:
  time_saved: "61%"
  quality: "50% fewer iterations"
success: true
notes: "Context-rich request eliminated debugging iterations"
```

</testing_framework>

### Success Criteria

**Pattern succeeds if:**

- ✅ Time saved: >20% improvement
- ✅ Code quality: Geen nieuwe bugs, tests passing
- ✅ Token efficiency: <10% token overhead vs manual
- ✅ Reproducibility: 3/3 trials successful

**Pattern fails if:**

- ❌ Time regression: Takes longer than manual
- ❌ Quality regression: Introduces bugs
- ❌ Token explosion: >50% more tokens than expected
- ❌ Inconsistent: Works 1/3 trials

### Failed Pattern Handling

**If pattern fails:**

1. Document in `vibe-coding/failed-patterns.md`
2. Analyze why:
   - Model limitation?
   - Wrong context?
   - Unclear prompt?
   - Task mismatch?
3. Update pattern OR deprecate
4. Share learnings met team

### Testing Schedule

**When to test:**

- After Claude/GPT-4 major updates (monthly check)
- After DefinitieAgent architecture changes
- When pattern used >10x (validate consistency)
- Before sharing pattern with team

**Metrics Tracking:**

```yaml
# docs/methodologies/vibe-coding/results/metrics.yaml
patterns:
  context-rich:
    tests_run: 15
    success_rate: 93.3%  # 14/15 successful
    avg_time_saved: 35%
    avg_token_usage: 450
    last_tested: "2025-01-27"
    test_model: "Claude Sonnet 4.5"
  business-first:
    tests_run: 8
    success_rate: 100%
    avg_time_saved: 28%
    avg_token_usage: 380
    last_tested: "2025-01-20"
    test_model: "Claude Sonnet 4.5"
```

---

## 🎯 Pattern Selection Guide

### Decision Matrix

| Scenario | Recommended Pattern | Difficulty | Avg Time |
|----------|-------------------|------------|----------|
| Unknown codebase | Archaeology First | Beginner | 1-2h |
| God object cleanup | Business-First Refactoring | Advanced | 2-4h |
| Performance issue | Context-Rich Request | Intermediate | 1-3h |
| Safe refactor | Test-Driven Refactor | Advanced | 2-5h |
| Large feature | Incremental Changes | Intermediate | 4-8h |
| Quick fix | Show Me First | Beginner | 30min-1h |
| Bug fix | Context-Rich + Incremental | Intermediate | 1-2h |
| Documentation | Archaeology First | Beginner | 30min-1h |

### By Difficulty Level

**Beginner:**

- Incremental Changes
- Show Me First
- Archaeology First (analysis only)

**Intermediate:**

- Context-Rich Requests
- Combination patterns (2 simple patterns)

**Advanced:**

- Business-First Refactoring
- Test-Driven Refactor
- Complex combinations (3+ patterns)

### Token Budget Guidelines

| Pattern Complexity | Token Budget | Example |
|-------------------|--------------|---------|
| Simple prompt | 50-100 | Show Me First |
| Intermediate | 100-200 | Context-Rich Request |
| Complex | 200-400 | Business-First Refactoring |
| Full specification | 400-600 | Test-Driven + Business-First combo |

---

## 📚 Resources

### Documentation

- **Complete guide**: `docs/methodologies/vibe-coding/GUIDE.md`
- **Prompt templates**: `docs/methodologies/vibe-coding/templates/`
- **Real examples**: `docs/methodologies/vibe-coding/examples/`
- **Testing results**: `docs/methodologies/vibe-coding/results/`

### External Resources

- **21 Vibe Tips**: `.ai-agents/vibe-coding/21-tips.md` (if exists)
- **Anthropic Prompt Engineering**: <https://docs.claude.com/en/docs/build-with-claude/prompt-engineering>
- **OpenAI Best Practices**: <https://help.openai.com/en/articles/6654000-best-practices-for-prompt-engineering>

### Related DefinitieAgent Docs

- **UNIFIED_INSTRUCTIONS.md** → APPROVAL LADDER (>100 lines rule)
- **CLAUDE.md** → Development Richtlijnen
- **BMad Method** → EPIC/Story planning
- **Refactor Log** → `docs/refactor-log.md`

---

## 🔄 Version History

### v1.0.0 (2025-01-27)

**Initial release:**

- 9 documented patterns (6 main + 3 supporting)
- XML semantic tags voor AI parsing
- Testing framework met metrics
- Real DefinitieAgent examples (US-202, dry_helpers.py)
- Integration met BMad + UNIFIED workflows
- Best practice compliant (token optimization, metadata, pronoun usage)

**Patterns included:**

1. Context-Rich Requests
2. Business-First Refactoring
3. Incremental Changes
4. Show Me First
5. Archaeology First
6. Test-Driven Refactor

**Anti-patterns documented:** 4 (Vague, Tech-First, No Context, Big Scope)

---

**Voor vragen of feedback:** Update `docs/methodologies/vibe-coding/PATTERNS.md` of contact DefinitieAgent team.
