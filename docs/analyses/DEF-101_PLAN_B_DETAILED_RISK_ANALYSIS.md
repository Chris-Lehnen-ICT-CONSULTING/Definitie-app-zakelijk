# DEF-101: Plan B - Detailed Risk Analysis
## Complete Risk Assessment with Concrete Mitigation Strategies

**Document Version:** 1.0
**Date:** 2025-11-10
**Author:** Debug Specialist
**Status:** READY FOR REVIEW

---

## 📋 Executive Summary

This document provides comprehensive risk analysis for all 9 issues in Plan B (EPIC-015 Prompt Quality Improvements). Each issue includes:
- Detailed technical and business risks
- Concrete severity/probability scores
- Actionable mitigation strategies
- Specific detection methods
- Clear rollback procedures
- Testing strategies

**Overall Plan Assessment:**
- **Total Duration:** 3 weeks (28 hours effort)
- **HIGH RISK Issues:** 2 (DEF-104, DEF-123)
- **MEDIUM RISK Issues:** 3 (DEF-102, DEF-126, DEF-124)
- **LOW RISK Issues:** 4 (DEF-103, DEF-105, DEF-106, DEF-107)
- **Point of No Return:** After DEF-126 (Week 1 end)
- **Recommended Approach:** Sequential execution with validation gates

---

## 🎯 Risk Analysis Per Issue

---

### DEF-102: Fix 5 Blocking Contradictions

**Effort:** 3 hours | **Risk Level:** MEDIUM | **Week:** 1

#### Technical Risks

**Risk 1: ESS-02 Exception Clause Too Broad**
- **Severity:** 7/10 (High impact on definition quality)
- **Probability:** 40% (Complex linguistic rules, edge cases exist)
- **Impact Example:** If exception allows "is een activiteit" universally, non-PROCES definitions might incorrectly use it. Example: "aanhouding is een activiteit..." (should be "handelwijze waarbij...").
- **Detection Method:**
  1. Run test suite with 10 definitions per ontological category (40 total)
  2. Check ESS-02 validation pass rate - should be ~90% (same as baseline)
  3. Manually review 5 PROCES definitions for "is een activiteit" usage
  4. Check if TYPE/RESULTAAT definitions incorrectly use process patterns
- **Mitigation:**
  1. Add ontological category check in ESS-02 exception logic: `if marker == "proces" and "is een activiteit" in definition`
  2. Create test cases: "afspraak is een activiteit" (TYPE - should FAIL), "verhoor is een activiteit waarbij..." (PROCES - should PASS)
  3. Add counter-examples in exception clause docstring
  4. Monitor first 50 definitions post-deploy for false positives
- **Rollback:** `git revert <commit>`, redeploy takes 5 min, no data loss (only validation logic change)

**Risk 2: Container Exemption Misused**
- **Severity:** 6/10 (Medium - affects definition clarity)
- **Probability:** 35% (Ambiguity between vague vs ontological use)
- **Impact Example:** Vague definitions like "notificatie is een proces dat plaatsvindt" pass validation (should fail - vague container), while "verhoor is een proces waarbij gecontroleerd wordt" passes (correct - ontological marker).
- **Detection Method:**
  1. Search corpus for "is een proces dat" (vague pattern) vs "is een proces waarbij" (specific pattern)
  2. False positive threshold: < 5% of PROCES definitions should use vague patterns
  3. Manual review: 10 definitions with "proces" - categorize as ontological vs vague
- **Mitigation:**
  1. Clarify exception text: "behalve als ontologische marker gevolgd door specifieke handeling"
  2. Add validation: require "waarbij/waarin" after "is een proces" (not "dat/die")
  3. Test cases: "beoordeling is een proces dat gebeurt" (FAIL), "beoordeling is een proces waarbij beoordeeld wordt" (PASS)
  4. Document in error_prevention_module.py line 138 with examples
- **Rollback:** Simple revert, 5 min, no cascade effects

**Risk 3: Relative Clause Ambiguity**
- **Severity:** 5/10 (Medium - affects readability)
- **Probability:** 30% (Grammar rules are nuanced)
- **Impact Example:** "waarbij" becomes overused in every definition, reducing variety. Or "die" is still rejected when it adds precision: "persoon die verantwoordelijk is".
- **Detection Method:**
  1. Count "waarbij" frequency in 100 definitions - should be < 60% (not universal)
  2. Check "die" usage in definitions - some should pass if adding precision
  3. Readability score: definitions should vary in structure
- **Mitigation:**
  1. Clarify rule: "Vermijd bijzinnen, behalve wanneer nodig voor precisie"
  2. Add guidance: "Gebruik 'waarbij' voor processen, 'met' voor eigenschappen"
  3. Test edge cases: "medewerker die verantwoordelijk is" (precise - PASS), "document die belangrijk is" (vague - FAIL)
  4. Update error_prevention line 151 with nuanced examples
- **Rollback:** Safe revert, isolated change

**Risk 4: Cross-Module Inconsistency**
- **Severity:** 8/10 (Critical - modules give conflicting guidance)
- **Probability:** 50% (5 modules modified, easy to miss synchronization)
- **Impact Example:** ESS-02 says "use 'is een activiteit'", STR-01 says "never start with 'is'", error_prevention says "koppelwerkwoord verboden" → AI gets 3 conflicting instructions, produces random results.
- **Detection Method:**
  1. Grep search: "start met 'is'" across all 5 modules (semantic_categorisation, structure_rules, error_prevention, arai_rules)
  2. Generate 20 definitions - check consistency: all PROCES should use "is een activiteit", none should be rejected by STR-01
  3. Check prompt output for contradictory statements (automated via PromptValidator in DEF-106)
- **Mitigation:**
  1. Create EXCEPTION_HIERARCHY document in docs/: ESS-02 (Tier 1) > STR-01 (Tier 2) > error_prevention (Tier 3)
  2. Add cross-reference comments in each module: "# Exception: See ESS-02 for ontological markers"
  3. Implement integration test: test_ontological_exception_consistency.py
  4. Test with 10 PROCES definitions - verify all modules allow "is een activiteit"
- **Rollback:** Moderate complexity - need to revert all 5 modules simultaneously (use git revert --no-commit for batch revert)

#### Business Risks

**Risk 1: User Confusion from Relaxed Rules**
- **Severity:** 6/10 (Medium - affects trust)
- **Probability:** 25% (Users accustomed to strict validation)
- **User Impact:** Users see "is een activiteit" in definitions and report as bug ("I thought 'is' was forbidden!"). Confidence in system drops.
- **Detection:**
  1. Monitor support tickets for "validation missed error" reports
  2. Track user acceptance rate: % of generated definitions accepted without edit
  3. Survey 5 power users: "Do definitions feel correct?"
- **Mitigation:**
  1. Add tooltip in UI: "⚠️ Ontological exceptions: 'is een activiteit' allowed for PROCES definitions"
  2. Update validation report to show: "✓ ESS-02 exception applied (ontological marker)"
  3. Create FAQ document: "Why does my definition start with 'is'?"
  4. Gradual rollout: enable for admin user first (1 week), then all users
- **Fallback:** If confusion > 30% in week 1, revert to strict rules + schedule user training session

**Risk 2: Definition Quality Regression**
- **Severity:** 7/10 (High - core product quality)
- **Probability:** 20% (Exceptions might lower the bar)
- **User Impact:** More definitions pass validation but are actually lower quality (vague, imprecise). Users don't trust system anymore.
- **Detection:**
  1. Compare quality metrics: baseline (current) vs post-DEF-102
  2. Metric: Avg confidence score should stay ≥ 0.85 (current baseline)
  3. Sample 50 definitions - expert review: % "actually good" should be ≥ 80%
  4. Track rejection rate in Vaststellen phase - should not increase > 10%
- **Mitigation:**
  1. Implement PromptValidator (DEF-106) BEFORE deploying DEF-102
  2. Add quality gates: if confidence < 0.7, escalate to Expert Review
  3. Monitor for 2 weeks post-deploy - weekly quality report
  4. If quality drops > 15%, immediately revert + root cause analysis
- **Fallback:** Rollback to strict rules + implement graduated exceptions (start with 1 category, expand gradually)

#### Testing Strategy

**Pre-Deployment Tests:**
1. **test_ess02_ontological_exceptions.py**: Validate ESS-02 allows "is een activiteit" only for PROCES marker
2. **test_str01_exception_clause.py**: Verify STR-01 doesn't block ESS-02 patterns
3. **test_error_prevention_contradictions.py**: Check error_prevention allows ontological markers
4. **test_cross_module_consistency.py**: Integration test - all 5 modules aligned

**Golden Reference Tests:**
- Test suite: Create `tests/fixtures/def102_golden_definitions.json`
- Sample size: 40 definitions (10 per ontological category)
- Categories: TYPE, PARTICULIER, PROCES, RESULTAAT
- Pass threshold: ≥ 90% must pass (same as current baseline)
- Example cases:
  - PROCES: "verhoor is een activiteit waarbij een verdachte wordt bevraagd" (PASS)
  - TYPE: "afspraak is een activiteit" (FAIL - TYPE using PROCES pattern)
  - RESULTAAT: "besluit is het resultaat van besluitvorming" (PASS)

**Edge Cases to Test:**
1. **Ambiguous ontological category**: "aanhouding" (could be PROCES or RESULTAAT) - definition should force one category
2. **Nested containers**: "proces dat een activiteit omvat" - should FAIL (double vague container)
3. **Legitimate 'is' use**: "is een categorie personen" (TYPE) vs "is een activiteit" (PROCES) - both should PASS
4. **Cross-category pollution**: TYPE definition using PROCES pattern - should FAIL

**Post-Deployment Monitoring:**
- **Metric 1**: ESS-02 pass rate → Should stay ~90% (±5% tolerance)
- **Metric 2**: "is een" usage in definitions → Should be 40-60% (not 0%, not 100%)
- **Metric 3**: False positive rate (vague containers passing) → Alert if > 10%
- **Metric 4**: User rejection rate (definitions not accepted) → Alert if increase > 15%
- **Monitoring period**: 2 weeks with daily checks

#### Rollback Plan

**Complexity:** EASY
**Time to rollback:** 10 minutes (5 files to revert)
**Procedure:**
1. Identify commit SHA for DEF-102 implementation
2. `git revert --no-commit <SHA>` (stages revert without committing)
3. Verify with `git diff --staged` - should show 5 files changed
4. `git commit -m "rollback(DEF-102): revert contradiction fixes due to <reason>"`
5. Deploy: `bash scripts/run_app.sh` (automatic restart)
6. **Verification:** Generate 10 PROCES definitions - should now FAIL validation (strict rules restored)

**Data Loss Risk:** NO
- Only validation logic changed, no database schema or data modifications
- Existing definitions in database unaffected
- Users can continue working during rollback (< 1 min downtime)

---

### DEF-103: Categorize 42 Forbidden Patterns

**Effort:** 2 hours | **Risk Level:** LOW | **Week:** 1

#### Technical Risks

**Risk 1: Categorization Misses Patterns**
- **Severity:** 4/10 (Low - doesn't break functionality)
- **Probability:** 25% (Subjective categorization)
- **Impact Example:** "aspect" categorized as "vague nouns" but acts like "relative clause" in some contexts. Cognitive load reduction goal not achieved.
- **Detection Method:**
  1. Review categorization: each of 42 patterns assigned to exactly 1 category
  2. Test cross-category ambiguity: search definitions for patterns used in multiple ways
  3. User survey (5 users): "Is the grouping clear and helpful?"
- **Mitigation:**
  1. Use linguistic framework for categorization (syntax vs semantics vs pragmatics)
  2. Allow 1-2 patterns in multiple categories if genuinely ambiguous
  3. Add clarifying examples per category: "Vague nouns: aspect, element (lack specificity)"
  4. Document rationale in error_prevention_module.py comments
- **Rollback:** Trivial - just remove category headers, keep flat list

**Risk 2: Cognitive Load NOT Actually Reduced**
- **Severity:** 5/10 (Medium - goal not met)
- **Probability:** 40% (Subjective improvement, hard to measure)
- **Impact Example:** 42 patterns still feel like 42 patterns, just with headers. AI still sees all 42 in prompt, doesn't benefit from grouping.
- **Detection Method:**
  1. Compare prompt token count: before vs after (should be ~same, just +50 tokens for headers)
  2. AI definition quality: no improvement expected (this is UI improvement, not logic)
  3. User feedback: "Does the prompt feel more organized?" (qualitative)
- **Mitigation:**
  1. Set realistic expectations: this is DOCUMENTATION improvement, not performance improvement
  2. Consider follow-up: DEF-123 will actually reduce cognitive load (context-aware loading)
  3. Add visual separators in prompt: "\n---\n" between categories
  4. If no perceived benefit after 1 week, consider reverting (low cost to keep, low benefit)
- **Fallback:** Keep implementation but deprioritize - no harm in organized list

#### Business Risks

**Risk 1: User Perception - "Nothing Changed"**
- **Severity:** 3/10 (Low - cosmetic issue)
- **Probability:** 60% (Users might not notice)
- **User Impact:** Users expect performance improvement but see only structural change. Disappointment.
- **Detection:** User feedback: "What changed?" vs "Oh, that's clearer now"
- **Mitigation:**
  1. Clear communication: "DEF-103 is a STRUCTURAL improvement (prep for DEF-123)"
  2. Don't announce as major release - bundle with DEF-102
  3. Frame as "foundation for Week 2 improvements"
- **Fallback:** No fallback needed - harmless change

#### Testing Strategy

**Pre-Deployment Tests:**
1. **test_forbidden_patterns_categorization.py**: Verify all 42 patterns categorized
2. **test_category_headers_in_prompt.py**: Check prompt contains category headers
3. **Visual inspection**: Compare error_prevention_module output before/after

**Golden Reference Tests:**
- No golden reference needed (structure change only)
- Validate: Prompt still contains all 42 patterns (none lost during refactor)

**Edge Cases to Test:**
1. **Empty category**: If category has 0 patterns, should not appear in prompt
2. **Single-item category**: Should still have header (consistency)

**Post-Deployment Monitoring:**
- **Metric 1**: Prompt length → Should increase ~50 tokens (category headers), no more
- **Metric 2**: Definition quality → Should be identical (no logic change)
- **Metric 3**: Execution time → Should be identical (±5ms)

#### Rollback Plan

**Complexity:** TRIVIAL
**Time to rollback:** 3 minutes
**Procedure:**
1. `git revert <commit>` (single commit)
2. Restart app
3. Verify: error_prevention output is flat list again

**Data Loss Risk:** NO

---

### DEF-126: Transform 7 Rule Modules to Instruction Tone

**Effort:** 5 hours | **Risk Level:** MEDIUM | **Week:** 1

#### Technical Risks

**Risk 1: Tone Transformation Weakens Validation**
- **Severity:** 8/10 (Critical - defeats purpose of rules)
- **Probability:** 35% (Subjective transformation, easy to go too far)
- **Impact Example:**
  - Before: "❌ Gebruik GEEN koppelwerkwoord aan het begin"
  - After (too weak): "Overweeg om niet te starten met een koppelwerkwoord"
  - Result: AI ignores instruction, produces invalid definitions
- **Detection Method:**
  1. Compare validation pass rates: before vs after (should be ~same)
  2. Generate 100 definitions - check forbidden pattern frequency:
     - "start met 'is'": should be < 5% (currently ~3%)
     - "bevat lidwoord": should be < 10% (currently ~7%)
  3. A/B test: same 10 definitions with old vs new prompts - measure diff
- **Mitigation:**
  1. Use IMPERATIVE mood: "Formuleer..." (command) not "Je zou kunnen..." (suggestion)
  2. Keep prohibition strength: Replace "❌ GEEN" with "Voorkom" (avoid) not "Overweeg te vermijden" (consider avoiding)
  3. Test each transformation with 5 definitions before committing
  4. Create transformation guidelines doc: "Instruction Tone Principles"
  5. Peer review: have 2nd person validate tone maintains authority
- **Rollback:** Moderate effort - need to revert 7 files with ~200 char changes each

**Risk 2: Manual Transformation Errors**
- **Severity:** 6/10 (Medium - creates inconsistency)
- **Probability:** 45% (Human error across 7 modules × ~20 rules = 140 transformations)
- **Impact Example:**
  - Typos: "Vormuleer" instead of "Formuleer"
  - Incomplete transformation: 3 rules in module still use validation tone
  - Lost meaning: "Vermijd abstracte containerbegrippen" → "Wees specifiek" (too vague)
- **Detection Method:**
  1. Automated check: grep for residual validation keywords ("toetsing", "valideert", "scoort")
  2. Consistency check: all rules in module use same tone pattern
  3. Manual review: read entire prompt output for jarring transitions
- **Mitigation:**
  1. Create transformation script: `scripts/check_instruction_tone.py`
  2. Checklist per module: ☐ No "toetsing" keywords ☐ Imperative verbs ☐ Consistent structure
  3. Transform 1 module → test → next module (not all at once)
  4. Use find-replace for common patterns: "Toetsvraag:" → "Focus:", "valideer" → "zorg voor"
  5. Git commit per module (enables granular rollback)
- **Rollback:** Moderate - use git log to find last commit per module, revert individually

**Risk 3: Inconsistent Phrasing Across Modules**
- **Severity:** 5/10 (Medium - UX issue)
- **Probability:** 50% (7 different modules, easy to diverge)
- **Impact Example:**
  - ARAI module: "Formuleer de definitie zo dat..."
  - ESS module: "Zorg ervoor dat de definitie..."
  - CON module: "Schrijf de definitie zodanig dat..."
  - Result: Disjointed prompt, AI confused by style shifts
- **Detection Method:**
  1. Extract instruction verbs from all 7 modules: should use 80% same verbs
  2. Read full prompt output - check for style consistency
  3. Token analysis: measure vocabulary diversity (should not spike)
- **Mitigation:**
  1. Define 5 standard instruction verbs: "Formuleer", "Voorkom", "Gebruik", "Vermijd", "Zorg voor"
  2. Template: "[Verb] de definitie [qualifier]: [specific instruction]"
  3. Example: "Formuleer de definitie met een zelfstandig naamwoord aan het begin"
  4. Apply template to all 7 modules before committing
  5. Create `docs/guidelines/INSTRUCTION_TONE_TEMPLATE.md`
- **Rollback:** Easy - revert all 7 modules as batch

#### Business Risks

**Risk 1: Users Perceive Rules as "Optional"**
- **Severity:** 7/10 (High - undermines system authority)
- **Probability:** 30% (If tone is too soft)
- **User Impact:** Users think rules are suggestions, ignore validation failures. Quality drops.
- **Detection:**
  1. User behavior: rejection rate in Vaststellen phase (should stay ~10%)
  2. Support tickets: "Why did validation fail if rule was just a suggestion?"
- **Mitigation:**
  1. Maintain consequence framing: "Formuleer X, anders [consequence]"
  2. Keep visual severity indicators: ❌, ⚠️, ✅ (not just text)
  3. Validation report still shows PASS/FAIL (not "considered/ignored")
- **Fallback:** Add disclaimer: "Deze instructies zijn verplicht voor validatie"

#### Testing Strategy

**Pre-Deployment Tests:**
1. **test_instruction_tone_consistency.py**: Check all modules use imperative mood
2. **test_validation_strength_maintained.py**: Generate definitions, compare pass rates
3. **test_instruction_verb_vocabulary.py**: Verify standard verbs used 80%+
4. **Manual review**: Read full prompt - check flow and consistency

**Golden Reference Tests:**
- Test suite: Reuse existing golden definitions (should produce same results)
- Sample size: 50 definitions (existing validated definitions)
- Pass threshold: ≥ 95% same results as before (±5% acceptable variance)

**Edge Cases to Test:**
1. **Ambiguous instruction**: "Gebruik enkelvoud" - does AI still apply to werkwoorden (infinitief)?
2. **Tone mismatch**: One harsh "❌ VERBODEN" in sea of friendly "Formuleer" - feels jarring
3. **Lost nuance**: "tenzij" exception clauses - ensure still present after transformation

**Post-Deployment Monitoring:**
- **Metric 1**: Definition quality score → Should be identical (±3%)
- **Metric 2**: Forbidden pattern frequency → Should be identical (±5%)
- **Metric 3**: User acceptance rate → Should stay ≥ 80%
- **Metric 4**: Average confidence → Should stay ≥ 0.85

#### Rollback Plan

**Complexity:** MEDIUM (7 files)
**Time to rollback:** 15 minutes
**Procedure:**
1. Create rollback script: `scripts/rollback_def126.sh`
2. Script reverts commits for all 7 modules (git revert <SHA1> <SHA2> ... <SHA7>)
3. Test with 5 definitions - verify validation tone restored
4. Deploy

**Data Loss Risk:** NO

---

### DEF-104: Reorganize Module Execution Order

**Effort:** 3 hours | **Risk Level:** HIGH | **Week:** 2

#### Technical Risks

**Risk 1: Dependency Breaks - Module A Expects Data from Module B**
- **Severity:** 9/10 (CRITICAL - breaks prompt generation)
- **Probability:** 60% (15 modules with complex dependencies)
- **Impact Example:**
  - definition_task_module expects `context.get_shared("ontological_category")` from semantic_categorisation_module
  - If execution order puts definition_task BEFORE semantic_categorisation → `None` returned → prompt generation fails
  - Error: "KeyError: 'ontological_category'" or silent failure (empty section)
- **Detection Method:**
  1. Run dependency analyzer: `python -m services.prompts.modules.prompt_orchestrator --analyze-deps`
  2. Check execution order against dependency graph: modules should only reference shared_state set by previous modules
  3. Integration test: generate 20 definitions with new order - check for None/empty sections
  4. Log analysis: check for "Module X validation failed: missing shared state Y"
- **Mitigation:**
  1. **MANDATORY**: Use orchestrator's `resolve_execution_order()` - don't hardcode order
  2. Document dependencies in each module's `get_dependencies()` method
  3. Add assertions in module `execute()`:
     ```python
     ontological_cat = context.get_shared("ontological_category")
     assert ontological_cat is not None, "semantic_categorisation must run before definition_task"
     ```
  4. Create dependency diagram: `docs/architectuur/MODULE_DEPENDENCY_GRAPH.md`
  5. Test suite: `test_execution_order_dependencies.py` - verify no module accesses missing shared_state
- **Rollback:** EASY - revert to `_get_default_module_order()` in prompt_orchestrator.py line 354

**Risk 2: Metadata No Longer Available When Needed**
- **Severity:** 7/10 (High - affects traceability)
- **Probability:** 40% (Metadata usage is scattered)
- **Impact Example:**
  - definition_task_module (runs LAST) builds metadata section with info from all prior modules
  - If module X moves later in order, its metadata isn't available yet
  - Result: Incomplete metadata in final prompt (missing rule counts, execution times)
- **Detection Method:**
  1. Check metadata completeness: prompt should contain `execution_metadata` with all module stats
  2. Compare metadata before/after reorder: should have same keys
  3. Test: generate 10 definitions, inspect `get_execution_metadata()` output
- **Mitigation:**
  1. definition_task_module should ALWAYS be LAST (explicitly documented)
  2. Metadata collection happens AFTER all module execution (already implemented in orchestrator line 193-204)
  3. Add validation: if metadata missing keys, log warning
  4. Test: `test_metadata_completeness.py`
- **Rollback:** EASY - revert order change

**Risk 3: Prompt Generation Fails Silently**
- **Severity:** 10/10 (CRITICAL - system unusable)
- **Probability:** 25% (Orchestrator has error handling, but edge cases exist)
- **Impact Example:**
  - New order causes ModuleExecutionError in batch 2
  - Orchestrator catches exception, returns empty string for that module
  - Final prompt is incomplete but doesn't crash - user gets garbage definition
  - Users lose trust, system appears broken
- **Detection Method:**
  1. Check logs for "Module execution error" warnings
  2. Prompt length check: before avg 7250 tokens, after should be similar (±500)
  3. Test 50 definitions: 0% should have empty sections
- **Mitigation:**
  1. Make orchestrator fail LOUDLY: if ANY module fails, raise exception (don't continue)
  2. Add prompt validation: `assert len(prompt) > 5000, "Prompt suspiciously short"`
  3. UI alert: "Prompt generation failed - contact support"
  4. Implement PromptValidator (DEF-106) to catch incomplete prompts
  5. Staging test: deploy to test environment, generate 100 definitions, check all succeed
- **Rollback:** URGENT - immediate revert if silent failures detected

#### Business Risks

**Risk 1: Definition Quality Degrades Due to Suboptimal Order**
- **Severity:** 8/10 (High - core product quality)
- **Probability:** 35% (Order matters for AI instruction following)
- **User Impact:** Definitions become less precise, validation pass rate drops, users frustrated.
- **Detection:**
  1. Compare quality metrics: 50 definitions before vs after
  2. Confidence score: should stay ≥ 0.85 (baseline)
  3. Validation pass rate: should stay ≥ 90%
  4. User acceptance: should stay ≥ 80%
- **Mitigation:**
  1. A/B test new order for 1 week: 50% users old order, 50% new order
  2. Metrics dashboard: track quality metrics in real-time
  3. Rollback trigger: if quality drops >10% for 3 consecutive days, auto-revert
  4. Expert review: sample 20 definitions from new order, manual quality assessment
- **Fallback:** Revert to old order + analyze which modules should be reordered (iterative approach)

#### Testing Strategy

**Pre-Deployment Tests:**
1. **test_execution_order_dependencies.py**: Verify no module accesses missing shared_state
2. **test_module_execution_success_rate.py**: 100 definitions should generate 100% success
3. **test_prompt_completeness.py**: Check all expected sections present in prompt
4. **test_metadata_integrity.py**: Verify metadata has all expected keys

**Golden Reference Tests:**
- Test suite: 50 existing definitions
- Expectation: 95%+ produce IDENTICAL results (order change shouldn't affect output)
- If results differ: root cause analysis - is difference acceptable?

**Edge Cases to Test:**
1. **Circular dependency**: Module A depends on B, B depends on A (should be caught by orchestrator)
2. **Missing optional dependency**: Module X optionally uses data from Y - should gracefully handle absence
3. **Batch execution**: Parallel modules in new order - verify no race conditions

**Post-Deployment Monitoring:**
- **Metric 1**: Module execution success rate → 100% (0 failures allowed)
- **Metric 2**: Prompt generation time → Should be ±10% of baseline (no performance regression)
- **Metric 3**: Prompt length → Should be ±5% of baseline (7250 tokens)
- **Metric 4**: Definition quality score → Should be ≥ baseline (0.85)

#### Rollback Plan

**Complexity:** EASY
**Time to rollback:** 5 minutes
**Procedure:**
1. Revert prompt_orchestrator.py `_get_default_module_order()` to original order
2. Optionally: revert definition_task_module restructure (if that was part of DEF-104)
3. Restart app
4. Test: generate 10 definitions - verify prompt format restored

**Data Loss Risk:** NO
- Only execution order changed, no database impact
- Existing definitions unaffected

---

### DEF-106: Create PromptValidator

**Effort:** 2 hours | **Risk Level:** LOW | **Week:** 2

#### Technical Risks

**Risk 1: False Positives - Blocks Valid Prompts**
- **Severity:** 7/10 (High - breaks functionality)
- **Probability:** 30% (Validation rules might be too strict)
- **Impact Example:**
  - Validator checks "prompt must contain all 7 rule modules"
  - Edge case: context-aware loading (DEF-123) legitimately skips CON_rules
  - Result: Valid prompt blocked, definition generation fails
- **Detection Method:**
  1. Test with 100 diverse definitions (various contexts, categories)
  2. False positive rate: should be 0% (validator should NEVER block valid prompt)
  3. Log all validation failures for manual review
- **Mitigation:**
  1. Start with LOOSE validation rules: only check critical issues
  2. Critical checks:
     - Prompt length > 1000 chars
     - Contains "Formuleer de definitie van **{begrip}**"
     - Contains at least 1 validation rule module
     - No duplicate sections (text appears 2x)
  3. Don't validate module count (allows context-aware loading flexibility)
  4. Use WARN level (not ERROR) for soft failures - log but don't block
  5. Implement flag: `strict_mode=False` by default
- **Rollback:** Disable validator (set `validate_prompt=False` in config)

**Risk 2: False Negatives - Misses Issues**
- **Severity:** 4/10 (Low - doesn't break, but misses bugs)
- **Probability:** 40% (Catching all edge cases is hard)
- **Impact Example:**
  - Validator checks for duplicate sections
  - Doesn't catch: same content with slightly different formatting
  - Result: Bloated 9000-token prompt passes validation
- **Detection Method:**
  1. Inject known bad prompts (test cases): empty sections, duplicates, etc.
  2. Validator should catch ≥ 80% of synthetic issues
  3. Real-world issues: monitor logs for problems validator missed
- **Mitigation:**
  1. Iterative improvement: start simple, add rules as issues discovered
  2. Use fuzzy matching for duplicates: Levenshtein distance > 90% = duplicate
  3. Log all validation warnings (even soft failures) for analysis
  4. Quarterly review: "What issues did validator miss this quarter?"
- **Fallback:** Accept that validator won't catch everything - it's a safety net, not a guarantee

**Risk 3: Performance Overhead**
- **Severity:** 3/10 (Low - adds latency)
- **Probability:** 25% (Validation is cheap, but 100+ definitions = noticeable)
- **Impact Example:**
  - Validator adds 50ms per prompt
  - Bulk generation (100 definitions) adds 5 seconds total
  - User perception: "System feels slower"
- **Detection Method:**
  1. Benchmark: time prompt generation with/without validator
  2. Target: < 20ms overhead per prompt
- **Mitigation:**
  1. Optimize checks: use regex compilation, simple string operations
  2. Cache validation results: if prompt unchanged, skip revalidation
  3. Parallel validation: run validator async while AI generates definition
  4. Make validator optional: `enable_prompt_validation=True` in config (can disable if slow)
- **Fallback:** Disable validator in production if overhead > 50ms

#### Business Risks

**Risk 1: Dev Time vs Value Tradeoff**
- **Severity:** 2/10 (Low - opportunity cost)
- **Probability:** 50% (Validator might not catch many real issues)
- **User Impact:** 2 hours spent on validator, might catch 1-2 issues per month. Low ROI.
- **Detection:** Track validator catches: "Issues prevented" count
- **Mitigation:**
  1. Set success criteria: validator should catch ≥ 5 issues in first 3 months
  2. If ROI is low, consider removing validator after trial period
  3. Alternatively: expand validator scope to catch more issue types
- **Fallback:** Accept low ROI if validator provides peace of mind (insurance policy)

#### Testing Strategy

**Pre-Deployment Tests:**
1. **test_prompt_validator_false_positives.py**: 100 valid prompts → 0 should fail
2. **test_prompt_validator_catches_issues.py**: 20 synthetic bad prompts → 16+ should fail (80%)
3. **test_prompt_validator_performance.py**: Overhead < 20ms per validation

**Golden Reference Tests:**
- Test suite: Existing 50 definitions
- All should PASS validation (100% success rate)

**Edge Cases to Test:**
1. **Empty prompt**: Should FAIL
2. **Minimal prompt**: Only task, no rules → Should WARN
3. **Duplicate sections**: Same module content 2x → Should FAIL
4. **Context-aware skipped module**: 6 modules instead of 7 → Should PASS

**Post-Deployment Monitoring:**
- **Metric 1**: Validation pass rate → Should be ≥ 99% (few failures expected)
- **Metric 2**: Validation overhead → Should be < 20ms
- **Metric 3**: Issues caught → Track count (goal: ≥ 5 in 3 months)

#### Rollback Plan

**Complexity:** TRIVIAL
**Time to rollback:** 2 minutes
**Procedure:**
1. Set `enable_prompt_validation=False` in config
2. Restart app (or hot-reload config if supported)
3. Validator is bypassed, no impact on functionality

**Data Loss Risk:** NO

---

### DEF-123: Context-Aware Module Loading

**Effort:** 5 hours | **Risk Level:** HIGH | **Week:** 2

#### Technical Risks

**Risk 1: Wrong Modules Skipped - Missing Critical Content**
- **Severity:** 10/10 (CRITICAL - broken definitions)
- **Probability:** 50% (Context relevance is subjective, easy to get wrong)
- **Impact Example:**
  - Definition for "verhoor" (PROCES) in context "Politie" (NP)
  - Context-aware logic skips CON_rules (context rules) because context_score < 0.3
  - Result: CON-02 rule not in prompt → AI misses context-specific guidance → definition too generic
  - User rejects definition, trust lost
- **Detection Method:**
  1. Compare definition quality: context-aware vs always-load
  2. Test 50 definitions with strong context (org=NP, jur=Strafrecht) - should reference context appropriately
  3. Check if skipped modules are actually relevant (manual review)
  4. User acceptance rate: should not drop > 10%
- **Mitigation:**
  1. **START CONSERVATIVE**: Only skip modules with 0 context (not < 0.3)
  2. Whitelist "always load" modules: expertise, output_specification, grammar, semantic_categorisation, definition_task (core modules)
  3. Only apply context-aware loading to: CON_rules, [domain_rules if exists], web_lookup_specific
  4. Add override: user can force "load all modules" via checkbox
  5. Log skipped modules: `logger.info(f"Skipped {module_id} due to context_score={score}")`
  6. A/B test: 50% users get context-aware, 50% always-load - compare metrics
- **Rollback:** EASY - set `context_aware_loading=False` in config

**Risk 2: Context Score Threshold Too High/Low**
- **Severity:** 8/10 (High - affects all definitions)
- **Probability:** 60% (Threshold is arbitrary, requires tuning)
- **Impact Example:**
  - **Too high (0.7)**: Most modules skipped, prompts too short (2000 tokens), definitions too generic
  - **Too low (0.1)**: Few modules skipped, no performance benefit, defeats purpose of DEF-123
- **Detection Method:**
  1. Track skip rate: % definitions where ≥ 1 module skipped (target: 30-50%)
  2. Prompt length distribution: should reduce avg length 10-20% (7250 → 6000-6500 tokens)
  3. Quality metrics: should stay ≥ baseline (no quality loss)
- **Mitigation:**
  1. Make threshold configurable: `context_relevance_threshold=0.3` in config
  2. Implement threshold tuning experiment:
     - Week 1: threshold=0.5 (strict)
     - Week 2: threshold=0.3 (moderate)
     - Week 3: threshold=0.1 (loose)
     - Compare metrics, choose optimal
  3. Adaptive threshold: if quality drops, automatically raise threshold
  4. Per-module thresholds: CON_rules=0.2 (lower), domain_rules=0.5 (higher)
- **Rollback:** Adjust threshold via config (no code change)

**Risk 3: Cache Invalidation Bugs**
- **Severity:** 9/10 (CRITICAL - stale prompts)
- **Probability:** 35% (Caching context-dependent data is tricky)
- **Impact Example:**
  - User generates definition for "verhoor" with context NP
  - Context-aware loading caches: "Skip CON_rules for NP context"
  - User changes context to OM, regenerates
  - Cache not invalidated → still skips CON_rules → wrong prompt for OM context
  - Result: Definition for "verhoor@OM" uses cached NP logic
- **Detection Method:**
  1. Test: generate definition with context A, change context to B, regenerate
  2. Verify: module loading decision reflects context B (not cached A)
  3. Check cache keys: should include context hash
- **Mitigation:**
  1. **CRITICAL**: Include context in cache key: `f"modules_{begrip}_{context_hash}"`
  2. Context hash: `hashlib.md5(json.dumps(sorted(context.items()))).hexdigest()`
  3. Cache expiration: 1 hour TTL (context might change)
  4. Add cache invalidation on context change: `cache.clear_pattern(f"modules_{begrip}_*")`
  5. Test suite: `test_context_change_invalidates_cache.py`
- **Rollback:** Disable context-aware caching: `cache_module_decisions=False`

**Risk 4: Fundamental Architecture Change - Breaks Assumptions**
- **Severity:** 8/10 (High - affects multiple systems)
- **Probability:** 40% (Other code might assume all modules always load)
- **Impact Example:**
  - PromptValidator (DEF-106) checks "prompt must contain 7 rule modules"
  - Context-aware loading skips 2 modules → validator fails
  - Or: Metadata reporting expects 16 modules → breaks when only 13 load
- **Detection Method:**
  1. Run full test suite after implementing DEF-123
  2. Check for hardcoded module count assumptions: `grep -r "len(modules) == 16" src/`
  3. Integration test: generate definition with context → verify all downstream systems work
- **Mitigation:**
  1. Update PromptValidator: check for "≥ 5 modules" not "== 16"
  2. Update metadata reporting: use `len(loaded_modules)` not hardcoded count
  3. Add field to metadata: `"context_aware_loading": True, "skipped_modules": ["CON_rules"]`
  4. Document architecture change in `docs/architectuur/MODULE_LOADING_STRATEGY.md`
  5. Update all references to assume variable module count
- **Rollback:** MODERATE complexity - need to revert + fix validator/metadata logic

#### Business Risks

**Risk 1: Definition Quality Drops Due to Missing Context Rules**
- **Severity:** 9/10 (CRITICAL - breaks core value proposition)
- **Probability:** 40% (Context rules are important)
- **User Impact:** Definitions become generic, don't reflect organizational specifics. Users lose primary benefit of system.
- **Detection:**
  1. User acceptance rate: should stay ≥ 80%
  2. Expert review: 20 definitions with strong context - should all be context-appropriate
  3. Rejection reasons: track "not specific enough for our org" feedback
- **Mitigation:**
  1. **NEVER skip CON_rules** if any context present (org, jur, or wet)
  2. Implement quality gate: if confidence < 0.7 AND context present, force reload with all modules
  3. User feedback: "Was this definition specific enough for [context]?" (Yes/No)
  4. If "No" > 20%, revert context-aware loading
- **Fallback:** Revert to always-load all modules + implement token reduction via DEF-124 (static caching) instead

**Risk 2: Performance Benefit NOT Realized**
- **Severity:** 5/10 (Medium - wasted effort)
- **Probability:** 35% (Token reduction might not translate to speed/cost savings)
- **User Impact:** 5 hours dev time spent, but generation time still 4-5 seconds. No user-visible benefit.
- **Detection:**
  1. Measure generation time: before vs after (target: 10-15% reduction)
  2. Measure API costs: tokens sent to GPT-4 (target: 15-20% reduction)
  3. User perception: "Does system feel faster?" (subjective)
- **Mitigation:**
  1. Set realistic expectations: 15% token reduction = ~0.5-1 sec faster (not dramatic)
  2. Quantify cost savings: $X saved per 1000 definitions
  3. If no measurable benefit, deprioritize or revert
- **Fallback:** Keep implementation but don't advertise as "performance improvement" (call it "prompt optimization")

#### Testing Strategy

**Pre-Deployment Tests:**
1. **test_context_aware_module_loading.py**: Verify modules skipped/loaded based on context_score
2. **test_context_cache_invalidation.py**: Context change → cache invalidated
3. **test_quality_with_context_aware_loading.py**: 50 definitions with context → quality ≥ baseline
4. **test_module_loading_edge_cases.py**: 0 context, partial context, full context scenarios

**Golden Reference Tests:**
- Test suite: 50 definitions (25 with strong context, 25 with weak/no context)
- Pass threshold: Quality ≥ 90% of baseline
- Context-appropriate: Expert review 10 strong-context definitions → all should reflect context

**Edge Cases to Test:**
1. **No context**: Should load all modules (fallback)
2. **Partial context**: org=NP but no jur/wet → Should load CON_rules (org is enough)
3. **Conflicting context**: org=NP + jur=Bestuursrecht (unusual combo) → Should load both
4. **Context change mid-session**: Generate with NP, switch to OM, regenerate → Different modules loaded

**Post-Deployment Monitoring:**
- **Metric 1**: Skip rate → 30-50% of definitions should skip ≥ 1 module
- **Metric 2**: Prompt length → Should reduce 10-20% (7250 → 6000-6500 tokens)
- **Metric 3**: Generation time → Should reduce 10-15% (4.5 → 3.8-4.0 sec)
- **Metric 4**: Definition quality → Should stay ≥ 0.85 confidence
- **Metric 5**: User acceptance → Should stay ≥ 80%

#### Rollback Plan

**Complexity:** MEDIUM
**Time to rollback:** 10 minutes
**Procedure:**
1. Set `context_aware_loading=False` in prompt_orchestrator config
2. Restart app
3. Verify: all modules load for all definitions (check logs)
4. Test: generate 10 definitions with context → should contain all module sections
5. If PromptValidator was updated, revert validator changes too

**Data Loss Risk:** NO
- Only affects prompt generation logic
- Existing definitions unaffected

---

### DEF-105: Add Visual Priority Badges

**Effort:** 2 hours | **Risk Level:** LOW | **Week:** 3

#### Technical Risks

**Risk 1: Wrong Tier Assignments**
- **Severity:** 4/10 (Low - cosmetic but misleading)
- **Probability:** 25% (Tier assignments are subjective)
- **Impact Example:**
  - ARAI-01 assigned TIER 2 (medium) but is actually critical (TIER 1)
  - Users ignore it thinking it's less important
  - Result: More ARAI-01 violations in definitions
- **Detection Method:**
  1. Review tier assignments with domain expert
  2. Check validation failure rates per rule - high-failure rules should be TIER 1
  3. User feedback: "Is TIER 1/2/3 labeling accurate?"
- **Mitigation:**
  1. Use existing priority field from JSON: `config.get("prioriteit")` → map to TIER
  2. Mapping: "hoog" → TIER 1, "medium" → TIER 2, "laag" → TIER 3
  3. Document mapping in `docs/guidelines/RULE_PRIORITY_MAPPING.md`
  4. Validate: all ESS rules should be TIER 1, all VER rules TIER 2-3
  5. If uncertain, default to TIER 1 (safer to over-prioritize)
- **Rollback:** Remove badges, revert to text priority

**Risk 2: Visual Clutter**
- **Severity:** 3/10 (Low - UX issue)
- **Probability:** 40% (Adding badges to 45 rules = 45 new visual elements)
- **Impact Example:**
  - Prompt becomes visually noisy: 🥇 TIER 1 🥇 everywhere
  - Users suffer emoji fatigue, start ignoring ALL badges
  - Result: Badges lose effectiveness, become decoration
- **Detection Method:**
  1. Review prompt output - does it feel cluttered?
  2. User feedback: "Are badges helpful or distracting?"
  3. Token count: should only add ~100 tokens (45 badges × 2 chars)
- **Mitigation:**
  1. Use SUBTLE badges: [T1], [T2], [T3] instead of 🥇🥈🥉
  2. Only show TIER 1 badges (most important), hide TIER 2-3
  3. Group by tier: "### TIER 1 Rules:" section header (fewer repeated badges)
  4. Make configurable: `show_priority_badges=True` in config (can disable)
- **Fallback:** Simplify to single "CRITICAL" badge for top 10 rules only

**Risk 3: Test Failures - Output Format Changed**
- **Severity:** 5/10 (Medium - breaks CI/CD)
- **Probability:** 60% (Tests check exact prompt output)
- **Impact Example:**
  - Test expects: "🔹 **ESS-02 - Ontologische categorie**"
  - Actual output: "🥇 TIER 1 | 🔹 **ESS-02 - Ontologische categorie**"
  - Result: 20 tests fail due to string mismatch
- **Detection Method:**
  1. Run test suite locally before committing
  2. Check CI/CD pipeline status
- **Mitigation:**
  1. Use REGEX in tests: `assert re.search(r"ESS-02.*Ontologische", prompt)`
  2. Don't test exact badge format (test presence, not format)
  3. Update golden reference outputs: regenerate expected strings
  4. Add badge-specific tests: `test_priority_badges_present.py`
- **Rollback:** Update tests to match original format (remove badge assertions)

#### Business Risks

**Risk 1: Users Don't Use Badges**
- **Severity:** 2/10 (Low - no harm, just wasted effort)
- **Probability:** 50% (Users might not find badges useful)
- **User Impact:** 2 hours dev time spent on feature nobody uses.
- **Detection:** Track if users ask about badge meaning or ignore them
- **Mitigation:**
  1. Add tooltip: "TIER 1 rules are critical for validation"
  2. User onboarding: explain tier system
  3. If no usage after 1 month, consider removing
- **Fallback:** Accept that badges are "nice to have" not critical

#### Testing Strategy

**Pre-Deployment Tests:**
1. **test_priority_badges_present.py**: Verify badges appear in prompt output
2. **test_tier_mapping_correct.py**: Check "hoog" → TIER 1, "medium" → TIER 2, "laag" → TIER 3
3. **test_prompt_format_unchanged.py**: Ensure badges don't break prompt structure

**Golden Reference Tests:**
- Test suite: Regenerate expected outputs with badges
- Visual review: Check prompt with badges looks good

**Edge Cases to Test:**
1. **Missing priority in JSON**: Should default to TIER 2 or TIER 3 (not crash)
2. **Invalid priority**: "super-high" not recognized → Should default to TIER 2

**Post-Deployment Monitoring:**
- **Metric 1**: Prompt length → Should increase ~100 tokens (minimal)
- **Metric 2**: User engagement → Do users mention badges in feedback?
- **Metric 3**: Test pass rate → Should be 100% (tests updated)

#### Rollback Plan

**Complexity:** TRIVIAL
**Time to rollback:** 5 minutes
**Procedure:**
1. Revert badge additions in 7 rule modules
2. Revert test updates
3. Restart app

**Data Loss Risk:** NO

---

### DEF-124: Static Module Caching

**Effort:** 2 hours | **Risk Level:** MEDIUM | **Week:** 3

#### Technical Risks

**Risk 1: Stale Cache - Static Module Changes Not Reflected**
- **Severity:** 8/10 (High - users see old content)
- **Probability:** 50% (Cache invalidation is hard)
- **Impact Example:**
  - Dev updates expertise_module guidance text
  - Module cached from yesterday with old text
  - Users generate definitions with outdated instructions
  - Definition quality suffers, users confused why changes not visible
- **Detection Method:**
  1. Check module modification time vs cache timestamp
  2. Test: update module file → regenerate definition → verify new content used
  3. Log cache hits/misses: should see cache miss after module update
- **Mitigation:**
  1. **Cache key includes module file mtime**: `f"{module_id}_{os.path.getmtime(module_file)}"`
  2. Alternatively: cache version number in module: `VERSION = "1.2.3"` → include in cache key
  3. Cache TTL: 1 hour (stale cache auto-expires)
  4. Manual cache clear: `cache.clear_pattern("modules_*")` after deploys
  5. Dev mode: disable caching (`enable_module_cache=False` when DEBUG=True)
- **Rollback:** Disable caching: `enable_module_cache=False` in config

**Risk 2: Cache Size Grows Unbounded**
- **Severity:** 6/10 (Medium - memory leak)
- **Probability:** 30% (Depends on cache implementation)
- **Impact Example:**
  - Each definition caches 16 module outputs × 500 chars = 8KB per definition
  - 1000 definitions per day × 30 days = 240MB cache
  - Eventually: out of memory error, app crashes
- **Detection Method:**
  1. Monitor cache size: `cache.get_stats()` → check memory usage
  2. Set alert: if cache > 100MB, investigate
  3. Check cache eviction: are old entries being removed?
- **Mitigation:**
  1. Use LRU cache: oldest entries auto-evicted when limit reached
  2. Set max cache size: 10MB or 1000 entries (whichever lower)
  3. Cache only static modules (expertise, grammar, output_spec), not dynamic ones (context_awareness, definition_task)
  4. Cache TTL: 1 hour (prevents long-term accumulation)
  5. Monitoring: log cache size every hour
- **Rollback:** Disable caching or reduce cache size limit

**Risk 3: Cache Invalidation Bugs - Wrong Content Served**
- **Severity:** 9/10 (CRITICAL - data corruption)
- **Probability:** 25% (Cache keys might collide)
- **Impact Example:**
  - Cache key: `f"module_{module_id}"`
  - User A generates definition for "verhoor" → caches grammar_module
  - User B generates definition for "aanhouding" → gets User A's cached grammar_module (if keys collide)
  - Result: Definition for "aanhouding" uses grammar rules for "verhoor"
- **Detection Method:**
  1. Test: generate 2 definitions concurrently → verify no cross-contamination
  2. Check cache keys: should be unique per (module, context, begrip)
  3. Log cache hits: inspect logs for suspicious patterns
- **Mitigation:**
  1. **CRITICAL**: Cache key MUST include all varying factors:
     ```python
     cache_key = f"module_{module_id}_{begrip}_{context_hash}_{module_version}"
     ```
  2. For truly static modules (expertise, grammar), can omit begrip/context
  3. Test suite: `test_cache_isolation.py` - verify no key collisions
  4. Use namespaced cache: separate cache per user session (if multi-user)
- **Rollback:** Disable caching immediately if data corruption detected

#### Business Risks

**Risk 1: Minimal Performance Benefit**
- **Severity:** 3/10 (Low - wasted effort)
- **Probability:** 40% (Module generation is already fast)
- **User Impact:** 2 hours dev time, but generation time only improves 50ms (not noticeable).
- **Detection:**
  1. Benchmark: generation time with/without caching
  2. Target: ≥ 100ms reduction (noticeable by users)
  3. Cost savings: token reduction → API cost (not applicable here - same tokens sent to GPT-4)
- **Mitigation:**
  1. Set realistic expectations: caching saves 50-100ms per definition (not dramatic)
  2. Benefit compounds: 100 definitions = 5-10 seconds saved
  3. If benefit < 50ms, consider removing caching (not worth complexity)
- **Fallback:** Keep caching but don't advertise as "performance improvement"

#### Testing Strategy

**Pre-Deployment Tests:**
1. **test_module_caching_hit_rate.py**: Generate 10 definitions → check cache hit rate ≥ 50%
2. **test_cache_invalidation_on_module_update.py**: Update module → verify cache miss
3. **test_cache_isolation.py**: Concurrent definitions → no cross-contamination
4. **test_cache_size_limit.py**: Generate 1000 definitions → verify cache size < 10MB

**Golden Reference Tests:**
- Test suite: 50 definitions with caching enabled
- Should produce IDENTICAL results to without caching (100% match)

**Edge Cases to Test:**
1. **Cache cold start**: First definition → all cache misses
2. **Cache warm**: Second definition → all cache hits (for static modules)
3. **Module update mid-session**: Cache invalidated properly?

**Post-Deployment Monitoring:**
- **Metric 1**: Cache hit rate → Should be 40-60% (some hits, some misses)
- **Metric 2**: Generation time → Should reduce 50-100ms
- **Metric 3**: Cache size → Should stay < 10MB
- **Metric 4**: Cache invalidation errors → Should be 0 (no stale content)

#### Rollback Plan

**Complexity:** TRIVIAL
**Time to rollback:** 2 minutes
**Procedure:**
1. Set `enable_module_cache=False` in prompt_orchestrator config
2. Restart app (or hot-reload config)
3. Verify: no cache hits in logs

**Data Loss Risk:** NO

---

### DEF-107: Documentation & Tests

**Effort:** 4 hours | **Risk Level:** LOW | **Week:** 3

#### Technical Risks

**Risk 1: Incomplete Test Coverage**
- **Severity:** 5/10 (Medium - false confidence)
- **Probability:** 40% (Easy to miss edge cases)
- **Impact Example:**
  - Tests cover happy path: ESS-02 exception works for PROCES
  - Miss edge case: ESS-02 exception misused for TYPE definitions
  - Result: Bug ships to production despite "passing tests"
- **Detection Method:**
  1. Measure test coverage: `pytest --cov` → should be ≥ 80% for modified modules
  2. Review test cases: do they cover edge cases from risk analysis?
  3. Run mutation testing: change code → tests should fail
- **Mitigation:**
  1. Create test matrix: each risk identified in this document = ≥ 1 test case
  2. Test categories:
     - Unit tests: individual module behavior
     - Integration tests: module interactions (DEF-104 order, DEF-123 loading)
     - End-to-end tests: full definition generation with all changes
  3. Test edge cases explicitly:
     - `test_ess02_exception_not_misused_for_type.py`
     - `test_context_aware_loading_with_no_context.py`
  4. Peer review: have another person review test coverage
- **Rollback:** N/A (documentation/tests don't need rollback)

**Risk 2: Documentation Out of Sync with Code**
- **Severity:** 4/10 (Low - causes confusion)
- **Probability:** 50% (Code evolves faster than docs)
- **Impact Example:**
  - Documentation says: "ESS-02 exception applies to all process definitions"
  - Code actually: only applies if marker == "proces" (stricter)
  - Result: Developers/users confused by mismatch
- **Detection Method:**
  1. Code review: verify doc examples match actual behavior
  2. Run doc examples as tests: doctest or code snippets in test suite
  3. Check for outdated references: grep for old module names, deprecated patterns
- **Mitigation:**
  1. Link docs to code: include file paths and line numbers in documentation
  2. Example: "See `src/services/prompts/modules/semantic_categorisation_module.py:182`"
  3. Automated doc tests: extract code examples from docs → run as tests
  4. Quarterly doc review: schedule "docs sync" task
  5. Use version control: docs in same repo as code (already done)
- **Rollback:** Update docs to match reverted code

**Risk 3: Tests Too Brittle**
- **Severity:** 6/10 (Medium - high maintenance cost)
- **Probability:** 45% (Testing exact strings is fragile)
- **Impact Example:**
  - Test checks: `assert "🔹 **ESS-02" in prompt`
  - Change badge format: `assert "TIER 1 | 🔹 **ESS-02" in prompt`
  - Result: Test breaks, requires update despite no functional change
- **Detection Method:**
  1. Track test maintenance: how often do tests break due to non-functional changes?
  2. CI/CD failure rate: should be < 5% false positives
- **Mitigation:**
  1. Test behavior, not implementation:
     - ❌ `assert prompt.startswith("### ✅ Algemene Regels")`
     - ✅ `assert "ESS-02" in prompt and "ontologische" in prompt.lower()`
  2. Use regex for format-insensitive matching
  3. Test outcomes: definition quality, not prompt format
  4. Snapshot testing: store expected output, flag if changes (but allow approval of intentional changes)
- **Rollback:** Accept some test brittleness as cost of thorough testing

#### Business Risks

**Risk 1: Documentation Effort vs Utility**
- **Severity:** 2/10 (Low - opportunity cost)
- **Probability:** 30% (Docs might not be read)
- **User Impact:** 4 hours spent on docs that nobody reads.
- **Detection:** Track doc views (if docs are HTML) or ask users "Did you read the docs?"
- **Mitigation:**
  1. Focus on high-value docs: troubleshooting, edge cases, FAQs
  2. Link docs from error messages: "See DEF-102_GUIDE.md for ESS-02 exceptions"
  3. Short, actionable docs (not lengthy tomes)
- **Fallback:** Accept that docs are insurance policy (even if rarely used, valuable when needed)

#### Testing Strategy

**Pre-Deployment Tests:**
1. **Run full test suite**: `pytest --cov=src --cov-report=html`
2. **Coverage threshold**: ≥ 80% for modules modified in Plan B
3. **Manual test run**: Execute all edge cases identified in this risk analysis
4. **Doc review**: Read all new docs, verify accuracy

**Test Files to Create:**
1. `tests/integration/test_def102_contradictions.py` (20 test cases)
2. `tests/integration/test_def104_module_order.py` (15 test cases)
3. `tests/integration/test_def123_context_aware_loading.py` (25 test cases)
4. `tests/unit/test_prompt_validator.py` (10 test cases)
5. `tests/smoke/test_plan_b_full_flow.py` (5 end-to-end scenarios)

**Documentation to Create:**
1. `docs/guidelines/DEF-102_ESS02_EXCEPTION_GUIDE.md` (1 page)
2. `docs/architectuur/MODULE_LOADING_STRATEGY.md` (2 pages)
3. `docs/guidelines/INSTRUCTION_TONE_TEMPLATE.md` (1 page)
4. `docs/testing/PLAN_B_TEST_STRATEGY.md` (3 pages)
5. Update `CLAUDE.md` with Plan B changes

**Post-Deployment Monitoring:**
- **Metric 1**: Test pass rate → Should be 100%
- **Metric 2**: Test coverage → Should be ≥ 80% for modified modules
- **Metric 3**: Documentation views → Track if docs are accessed

#### Rollback Plan

**Complexity:** N/A (tests/docs don't affect production)
**Time to rollback:** 0 minutes
**Procedure:** Keep tests and docs even if code is reverted (they document lessons learned)

**Data Loss Risk:** NO

---

## 🔥 Cumulative Risk Analysis

### Week 1 Compound Risks

**Scenario: DEF-102 Exception Too Broad + DEF-126 Tone Too Weak**
- **Combined Impact:** ESS-02 allows "is een activiteit" broadly + instruction tone sounds optional
- **Result:** AI ignores ESS-02 guidance, produces TYPE definitions with PROCES patterns
- **Severity:** 9/10 (Critical quality regression)
- **Mitigation:**
  1. Test DEF-102 + DEF-126 together BEFORE merging both
  2. If quality drops > 15%, revert BOTH (not just one)
  3. A/B test: deploy DEF-102 alone for 3 days, then add DEF-126

**Scenario: DEF-102 Cross-Module Inconsistency + DEF-103 Categorization Confusion**
- **Combined Impact:** 5 modules give conflicting guidance + 42 patterns in confusing categories
- **Result:** Prompt is chaotic, AI produces random results
- **Severity:** 7/10 (High cognitive load)
- **Mitigation:**
  1. Deploy DEF-103 FIRST (categorization), THEN DEF-102 (logic changes)
  2. PromptValidator checks for contradictory instructions
  3. Manual review: read full prompt after both implemented

### Week 2 Compound Risks

**Scenario: DEF-104 Breaks Flow + DEF-123 Skips Wrong Modules**
- **Combined Impact:** New execution order breaks dependencies + context-aware loading skips critical modules
- **Result:** Prompt generation fails or produces incomplete prompts
- **Severity:** 10/10 (System unusable)
- **Probability:** 30% (Two HIGH RISK issues, lots of interaction)
- **Recovery Time:** 20-30 minutes (revert both, test, redeploy)
- **Mitigation:**
  1. **NEVER deploy DEF-104 and DEF-123 same day**
  2. Deploy DEF-104, stabilize for 3 days, THEN deploy DEF-123
  3. If DEF-104 breaks, rollback BEFORE starting DEF-123
  4. Staging environment: test DEF-104 + DEF-123 together for 1 week before production

**Scenario: DEF-123 Cache Bug + DEF-124 Cache Bug**
- **Combined Impact:** Context-aware caching broken + static module caching broken
- **Result:** Stale prompts everywhere, users see wrong content
- **Severity:** 9/10 (Critical data integrity issue)
- **Mitigation:**
  1. Implement DEF-123 caching first, test thoroughly
  2. Only start DEF-124 after DEF-123 cache is proven stable
  3. Use different cache namespaces: `cache:context_aware:*` vs `cache:static_modules:*`
  4. If either breaks, disable BOTH caches (safe fallback)

### Week 3 Compound Risks

**Week 3 is LOW RISK**: DEF-105, DEF-124, DEF-107 are mostly independent
- DEF-105 (badges) is cosmetic, doesn't affect logic
- DEF-124 (caching) can be disabled without breaking system
- DEF-107 (tests/docs) doesn't affect production

### Cross-Week Compound Risks

**Point of No Return: After DEF-126 (End of Week 1)**
- **Why:** DEF-126 transforms 7 modules × ~20 rules = 140 transformations
- **Rollback Complexity:** Need to revert 7 files with manual text changes
- **If Week 2 Fails:** Reverting Week 1 becomes painful (7 files × 2 weeks of changes)
- **Mitigation:**
  1. Ensure Week 1 is ROCK SOLID before starting Week 2
  2. Freeze Week 1 code: no changes to DEF-102/103/126 during Week 2/3
  3. If Week 2 has major issues, accept Week 1 changes as sunk cost (don't revert)

---

## 🚧 Critical Dependencies

### Blocking Relationships

**DEF-102 Blocks DEF-126:**
- If DEF-102 exception logic is wrong, DEF-126 tone transformation makes it worse
- Example: "Gebruik 'is een activiteit' tenzij..." (bad exception) + "Overweeg..." (weak tone) = disaster
- **Solution:** Validate DEF-102 thoroughly before starting DEF-126

**DEF-104 Blocks DEF-123:**
- If DEF-104 execution order breaks dependencies, DEF-123 context-aware loading will compound issues
- Example: Definition task runs before semantic categorisation → no ontological_category → context-aware loading can't decide which modules to skip
- **Solution:** Stabilize DEF-104 for 3-5 days before starting DEF-123

**DEF-106 Blocks DEF-123:**
- PromptValidator (DEF-106) might assume all 16 modules always load
- Context-aware loading (DEF-123) violates this assumption → validator fails
- **Solution:** Implement DEF-106 AFTER DEF-123, or design DEF-106 to handle variable module count

**DEF-123 Enables DEF-124:**
- Context-aware loading (DEF-123) determines which modules are static vs dynamic
- Static module caching (DEF-124) only caches truly static modules
- **Solution:** Implement DEF-124 AFTER DEF-123 is stable

### Parallel Execution Risks

**NEVER PARALLELIZE:**
1. **DEF-102 + DEF-126**: Both modify error_prevention_module → merge conflicts
2. **DEF-104 + DEF-123**: Both modify prompt_orchestrator → conflicts + compounded breakage
3. **DEF-102 + DEF-104**: DEF-102 changes module content, DEF-104 changes order → unpredictable results

**SAFE TO PARALLELIZE:**
1. **DEF-103 + DEF-105**: Both cosmetic changes, different files
2. **DEF-106 + DEF-107**: Validator creation + tests/docs (different domains)

**CONDITIONALLY SAFE:**
1. **DEF-102 + DEF-103**: If developers coordinate on error_prevention_module edits (DEF-102 changes logic, DEF-103 adds headers)

---

## 📊 Risk Heatmap

| Issue | Technical Risk | Business Risk | Rollback Complexity | Overall Risk |
|-------|----------------|---------------|---------------------|--------------|
| **DEF-102** | 7/10 | 6/10 | EASY | **MEDIUM** |
| **DEF-103** | 3/10 | 2/10 | TRIVIAL | **LOW** |
| **DEF-126** | 7/10 | 5/10 | MEDIUM | **MEDIUM** |
| **DEF-104** | 9/10 | 7/10 | EASY | **HIGH** |
| **DEF-106** | 5/10 | 2/10 | TRIVIAL | **LOW** |
| **DEF-123** | 9/10 | 8/10 | MEDIUM | **HIGH** |
| **DEF-105** | 3/10 | 2/10 | TRIVIAL | **LOW** |
| **DEF-124** | 7/10 | 3/10 | TRIVIAL | **MEDIUM** |
| **DEF-107** | 4/10 | 2/10 | N/A | **LOW** |

### Risk Distribution

- **HIGH RISK**: 2 issues (DEF-104, DEF-123) - 22% of issues, 36% of effort
- **MEDIUM RISK**: 3 issues (DEF-102, DEF-126, DEF-124) - 33% of issues, 36% of effort
- **LOW RISK**: 4 issues (DEF-103, DEF-105, DEF-106, DEF-107) - 45% of issues, 28% of effort

### Week Risk Profile

- **Week 1**: 1 MEDIUM + 2 MEDIUM/LOW = **Moderate Risk**
- **Week 2**: 2 HIGH + 1 LOW = **High Risk** (⚠️ Critical week)
- **Week 3**: 3 LOW = **Low Risk**

---

## 🛡️ Mitigation Strategy Summary

### Prevention (Before Implementation)

1. **Staging Environment**: Deploy to test environment first, run 100 definitions
2. **A/B Testing**: 50% users get new code, 50% get old code - compare metrics
3. **Feature Flags**: Ability to disable changes via config (no redeploy needed)
4. **Code Review**: 2nd developer reviews all HIGH RISK issues
5. **Dependency Analysis**: Run orchestrator's dependency checker before each deploy

### Detection (During Implementation)

1. **Automated Testing**: 80%+ coverage for modified modules, integration tests for interactions
2. **Monitoring Dashboard**: Real-time metrics for quality, performance, errors
3. **Log Analysis**: Daily review of logs for warnings, errors, anomalies
4. **User Feedback**: Survey 5 power users weekly: "How's the system working?"
5. **Expert Review**: Sample 20 definitions per week, manual quality assessment

### Response (After Issues Detected)

1. **Rollback Procedures**: Documented step-by-step for each issue (see individual rollback plans)
2. **Escalation Path**: Define triggers: "If metric X drops >Y%, revert immediately"
3. **Post-Mortem**: After any rollback, document what went wrong, how to prevent future issues
4. **Iterative Improvement**: If rollback needed, implement in smaller increments (e.g., DEF-102 one contradiction at a time)

---

## 📅 Recommended Execution Plan

### Week 1: Foundation (Low-Medium Risk)

**Monday:**
- Deploy DEF-103 (categorization) - 2h
- Test with 20 definitions
- If stable, proceed

**Tuesday:**
- Deploy DEF-102 (contradictions) - 3h
- Test extensively (40 definitions, 10 per category)
- Monitor all day for issues

**Wednesday-Thursday:**
- Stabilization period for DEF-102
- Fix any edge cases discovered
- Prepare DEF-126

**Friday:**
- Deploy DEF-126 (tone transformation) - 5h
- Test DEF-102 + DEF-126 together (50 definitions)
- Monitor weekend for issues

### Week 2: High Risk (Sequential, Not Parallel)

**Monday-Tuesday:**
- Deploy DEF-104 (execution order) - 3h
- Test thoroughly (100 definitions)
- **DO NOT PROCEED to DEF-123 if any issues**

**Wednesday:**
- Stabilization day for DEF-104
- Fix bugs, monitor metrics

**Thursday-Friday:**
- Deploy DEF-106 (validator) - 2h (prep for DEF-123)
- Deploy DEF-123 (context-aware loading) - 5h
- Test extensively (50 definitions with various contexts)
- Monitor weekend

### Week 3: Cleanup (Low Risk)

**Monday:**
- Deploy DEF-105 (badges) - 2h
- Visual review, user feedback

**Tuesday:**
- Deploy DEF-124 (caching) - 2h
- Performance benchmarks

**Wednesday-Friday:**
- DEF-107 (tests + docs) - 4h
- Final integration testing
- Prepare handover document

---

## 🎯 Success Criteria

### Definition Quality (Non-Negotiable)
- ✅ Confidence score: ≥ 0.85 (baseline)
- ✅ Validation pass rate: ≥ 90% (baseline)
- ✅ User acceptance rate: ≥ 80%
- ✅ Expert review: ≥ 80% "actually good" definitions

### Performance (Goals)
- ✅ Generation time: ≤ 4.5 seconds (current) or 10% faster
- ✅ Token usage: 10-20% reduction (DEF-123)
- ✅ Prompt length: 6000-6500 tokens (from 7250)

### System Stability (Non-Negotiable)
- ✅ Prompt generation success rate: 100% (0 failures)
- ✅ Module execution errors: 0 per 100 definitions
- ✅ Rollback-free deployment: Ideally 0 rollbacks, max 1 rollback per week

### Testing & Documentation (Quality Gates)
- ✅ Test coverage: ≥ 80% for modified modules
- ✅ Integration tests: ≥ 90% pass rate
- ✅ Documentation completeness: All HIGH RISK issues documented

---

## 🚨 Rollback Triggers (Auto-Revert Conditions)

### Immediate Rollback (No Questions Asked)
1. **Prompt generation failure rate > 5%** (system broken)
2. **Data corruption detected** (wrong content served to users)
3. **Definition quality drops > 20%** (unacceptable regression)
4. **Validation pass rate < 70%** (too strict or too loose)

### Rollback After 24h Observation
1. **Quality drops 10-20%** (significant but not critical)
2. **User acceptance < 70%** (users rejecting most definitions)
3. **Performance regression > 20%** (slower than before)
4. **Cache errors > 10 per day** (caching is buggy)

### Rollback After 1 Week
1. **No measurable benefit** (effort not justified)
2. **Unresolved edge cases** (corner cases breaking frequently)
3. **High maintenance cost** (requires constant fixes)

---

## 📝 Conclusion

Plan B is **FEASIBLE** but requires **DISCIPLINED EXECUTION**:

### Key Recommendations

1. **Sequential, Not Parallel**: Deploy issues one at a time, especially HIGH RISK issues (DEF-104, DEF-123)
2. **Week 2 is Critical**: DEF-104 + DEF-123 are highest risk - allocate extra time, test thoroughly
3. **Point of No Return**: After DEF-126 (Week 1 end), rollback becomes painful - ensure Week 1 is solid before proceeding
4. **Feature Flags**: Implement ability to disable DEF-123 (context-aware loading) and DEF-124 (caching) via config
5. **Staging First**: Deploy to test environment, run 100-200 definitions before production
6. **Monitoring**: Set up automated alerts for quality/performance regressions
7. **Rollback Readiness**: Have rollback procedures documented and tested BEFORE deploying each issue

### Risk Mitigation Priority

**Top 3 Risks to Mitigate:**
1. **DEF-104 + DEF-123 Compound Failure** (10/10 severity) → Deploy 3+ days apart
2. **DEF-102 Cross-Module Inconsistency** (8/10 severity) → Implement PromptValidator first
3. **DEF-123 Cache Invalidation Bugs** (9/10 severity) → Thorough testing with context changes

**If You Only Have Time for 3 Mitigations:**
1. Create dependency diagram for DEF-104 (prevent module execution order bugs)
2. Implement cache key with context hash for DEF-123 (prevent stale cache bugs)
3. Add integration test suite for DEF-102 (prevent cross-module contradictions)

**Confidence Level:** 75% - Plan is solid, but Week 2 has high uncertainty. Success depends on careful testing and willingness to rollback if needed.

---

**END OF RISK ANALYSIS**
