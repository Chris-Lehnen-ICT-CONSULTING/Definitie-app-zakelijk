# US-205: Token Optimization & Caching Implementation

**Note**: Er is een nummering conflict. Dit document beschrijft de ECHTE US-205 volgens EPIC-020.
Het bestaande US-205.md gaat over God Class refactoring en hoort bij US-207.

---
id: US-205
epic_id: EPIC-020-PHOENIX
title: Token Optimization & Caching Implementation
status: READY
priority: HIGH
story_points: 8
assignee: team
created_date: 2025-01-18
updated_date: 2025-01-18
labels: [phoenix, performance, optimization, tokens, cost-reduction]
dependencies:
  - US-203 (Token analysis - COMPLETED)
---

## User Story
**Als** product owner
**Wil ik** de geanalyseerde token optimalisaties geïmplementeerd hebben
**Zodat** we van 7.250 naar <3.000 tokens per prompt gaan en 60% kosten besparen

## Context
US-203 heeft aangetoond dat 61% token reductie haalbaar is door:
- Module consolidatie (17→7 modules): -2.000 tokens
- Context-aware loading: -1.200 tokens
- Validatieregel deduplicatie: -1.000 tokens
- Smart example selection: -800 tokens

## Acceptance Criteria

### Must Have
- [ ] Token count ≤3.000 voor alle definitie types
- [ ] Module consolidatie geïmplementeerd (17→7)
- [ ] Context-aware module loading werkend
- [ ] Geen kwaliteitsverlies in definities (>95% validation pass rate)

### Should Have
- [ ] Dynamic example selection
- [ ] Prompt template caching
- [ ] Token usage monitoring dashboard

## Technical Implementation

### Phase 1: Module Consolidatie (2 dagen)
Consolideer 17 modules naar 7:

```python
# NEW: src/services/prompts/modules/consolidated/

core_validation_module.py      # ARAI + ESS + SAM + VER
structure_quality_module.py    # STR + INT + grammar
context_processing_module.py   # context_awareness + CON + semantic
output_format_module.py        # output_spec + template
task_expertise_module.py       # definition_task + expertise
quality_control_module.py      # error_prevention + metrics
base_module.py                 # unchanged
```

### Phase 2: Context-Aware Loading (1 dag)
```python
class ModuleSelector:
    def select_modules(self, begrip_type: str) -> List[Module]:
        """Load alleen relevante modules per begrip type."""

        if begrip_type == "proces":
            return [
                self.core_validation,
                self.context_processing,
                self.task_expertise
            ]  # Skip structure_quality, output_format

        elif begrip_type == "object":
            return [
                self.core_validation,
                self.structure_quality,
                self.output_format
            ]  # Skip process-specific modules
```

### Phase 3: Rule Deduplication (1 dag)
```python
class RuleDeduplicator:
    def deduplicate(self, rules: List[Rule]) -> List[Rule]:
        """Remove overlapping validation rules."""

        # Merge similar rules
        merged = self.merge_similar(rules)

        # Remove redundant examples
        cleaned = self.remove_duplicate_examples(merged)

        return cleaned[:15]  # Max 15 most important rules
```

### Phase 4: Smart Example Selection (1 dag)
```python
class ExampleSelector:
    def select_relevant(self, term: str, max_count: int = 3) -> List[str]:
        """Select only most relevant examples."""

        # Use semantic similarity
        examples = self.rank_by_similarity(term, self.all_examples)

        # Return top N
        return examples[:max_count]
```

## Test Strategy

### Quality Tests
```python
def test_definition_quality_maintained():
    """Ensure optimized prompts maintain quality."""

    for test_term in TEST_TERMS:
        old_result = generate_with_old_prompt(test_term)
        new_result = generate_with_optimized_prompt(test_term)

        assert similarity(old_result, new_result) > 0.95
        assert validation_score(new_result) >= validation_score(old_result)
```

### Performance Tests
```python
def test_token_reduction():
    """Verify token count stays under 3000."""

    for test_case in TEST_CASES:
        prompt = build_optimized_prompt(test_case)
        tokens = count_tokens(prompt)

        assert tokens <= 3000
```

## Rollout Plan

### Week 2 Schedule
- **Maandag**: Module consolidatie development
- **Dinsdag**: Module consolidatie testing & integration
- **Woensdag**: Context-aware loading implementation
- **Donderdag**: Rule deduplication & example selection
- **Vrijdag**: A/B testing & quality validation

## Success Metrics
- Token usage: 7.250 → ≤3.000 (-59%)
- API costs: €0.15 → €0.06 per generatie (-60%)
- Response time: 5s → <3s (-40%)
- Quality score: ≥4.5/5 maintained

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|---------|-----------|
| Quality degradation | HIGH | A/B testing, gradual rollout |
| Module conflicts | MEDIUM | Comprehensive integration tests |
| Performance issues | LOW | Caching, lazy loading |

## Notes
- Dit is de IMPLEMENTATIE van het onderzoek uit US-203
- Focus op quick wins eerst (module consolidatie)
- Quality monitoring is kritiek tijdens rollout