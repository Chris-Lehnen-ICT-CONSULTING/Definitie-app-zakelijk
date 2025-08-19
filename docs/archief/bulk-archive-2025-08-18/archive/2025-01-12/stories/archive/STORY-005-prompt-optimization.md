# STORY-005: Prompt Optimization for Performance

## User Story
Als een **system administrator**
wil ik dat prompts geoptimaliseerd zijn naar <10k karakters
zodat de response tijd verbetert en API kosten dalen.

## Acceptance Criteria
- [ ] Prompt size gereduceerd van 35k naar <10k karakters
- [ ] Response tijd verbeterd naar <5 seconden
- [ ] Geen verlies van definitie kwaliteit
- [ ] Validatie scores blijven gelijk of beter
- [ ] Token usage reporting geïmplementeerd
- [ ] A/B testing mogelijk tussen oude en nieuwe prompts

## Technical Notes

### Current Prompt Analysis
```python
# Current prompt structure (35k chars)
CURRENT_PROMPT = """
[500 lines of examples]
[200 lines of rules]
[100 lines of context]
[Actual request]
"""

# Target structure (<10k chars)
OPTIMIZED_PROMPT = """
[Core rules only - 50 lines]
[Minimal examples - 20 lines]
[Compressed context - 10 lines]
[Focused request]
"""
```

### Optimization Strategies

1. **Rule Compression**
   ```python
   # Instead of listing all 46 rules in prompt
   RULE_SUMMARY = """
   Schrijf een definitie die:
   - Geen cirkelredeneringen bevat
   - Begint met hoofdletter, eindigt met punt
   - 20-500 woorden lang is
   - Objectief en neutraal is
   - Context-appropriate terminologie gebruikt
   """
   ```

2. **Dynamic Example Selection**
   ```python
   def select_relevant_examples(term: str, context: str) -> List[str]:
       # Only include examples similar to current term
       all_examples = load_examples()
       relevant = filter_by_similarity(all_examples, term, context)
       return relevant[:3]  # Max 3 examples
   ```

3. **Context Compression**
   ```python
   def compress_context(context: str) -> str:
       # Extract key information only
       if len(context) > 200:
           return summarize(context, max_length=200)
       return context
   ```

4. **Template Variables**
   ```python
   PROMPT_TEMPLATE = """
   Genereer een {style} definitie voor '{term}'.
   Context: {compressed_context}

   Belangrijkste regels:
   {rule_summary}

   Voorbeelden:
   {dynamic_examples}

   Definitie:
   """
   ```

### Implementation Plan
1. Analyze current prompts to identify redundancy
2. Create compressed rule summaries
3. Implement dynamic example selection
4. Build template system with variables
5. A/B test new prompts against old
6. Monitor quality metrics

### Performance Monitoring
```python
class PromptMonitor:
    def track_request(self, prompt: str, response: str):
        metrics = {
            'prompt_chars': len(prompt),
            'prompt_tokens': count_tokens(prompt),
            'response_time': measure_time(),
            'model': get_model(),
            'cost_estimate': calculate_cost()
        }
        log_metrics(metrics)
```

## QA Notes

### Test Scenarios
1. **Size Verification**
   - Generate 100 prompts
   - Verify all <10k characters
   - Check token counts

2. **Quality Comparison**
   - Generate definitions with old/new prompts
   - Compare validation scores
   - Human review of quality

3. **Performance Test**
   - Measure response times
   - Compare API costs
   - Check system load

4. **Edge Cases Test**
   - Very long terms
   - Complex contexts
   - Special characters
   - Multiple languages

### A/B Testing Plan
- 10% traffic to new prompts initially
- Monitor quality metrics for 1 week
- Gradual rollout if metrics stable
- Full rollback capability

### Expected Behavior
- 70% reduction in prompt size
- 40% reduction in response time
- No degradation in quality scores
- 50% reduction in API costs

## Definition of Done
- [ ] Prompt templates refactored
- [ ] Dynamic selection implemented
- [ ] Size consistently <10k chars
- [ ] Performance targets met
- [ ] A/B testing framework ready
- [ ] Monitoring dashboard created
- [ ] Documentation updated

## Priority
**Medium** - Performance improvement

## Estimated Effort
**8 story points** - 3-4 days of development

## Sprint
Sprint 3 - Performance & Testing

## Dependencies
- Token counting library (tiktoken)
- A/B testing framework
- Metrics collection system

## Risks
- Quality degradation if too aggressive
- Complex implementation
- Testing overhead

## Notes
- Start with conservative optimization
- Keep old prompts for rollback
- Consider prompt caching
- Monitor OpenAI rate limits

---
*Story generated from PRD Epic 2: AI & Content Generatie*
