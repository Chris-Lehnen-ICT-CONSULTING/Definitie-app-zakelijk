# Epic 6: Prompt Optimalisatie

**Epic Goal**: Reduceer prompt grootte van 35k naar <10k karakters.

**Business Value**: 50% kosten reductie, 40% snellere responses.

**Total Story Points**: 10

**Target Sprint**: 4

## Current State

- Huidige prompt size: ~35,000 karakters
- Bevat: 500 lines examples, 200 lines rules, 100 lines context
- Cost per request: ~€0.35
- Response time: 8-12 seconden

## Target State

- Target prompt size: <10,000 karakters (71% reductie)
- Smart context selection
- Cost per request: ~€0.10
- Response time: <5 seconden

## Stories

### STORY-006-01: Analyseer Huidige Prompts

**Story Points**: 2

**Als een** developer  
**wil ik** prompt usage analyseren  
**zodat** ik optimization opportunities zie.

#### Acceptance Criteria
- [ ] Token usage report per prompt type
- [ ] Redundantie analyse
- [ ] Cost breakdown
- [ ] Optimization targets identified

#### Analysis Tasks
```python
class PromptAnalyzer:
    """Analyze prompt usage and optimization opportunities."""
    
    def analyze_prompts(self) -> PromptAnalysisReport:
        prompts = self.get_recent_prompts(days=7)
        
        report = {
            'total_prompts': len(prompts),
            'avg_tokens': self._calculate_avg_tokens(prompts),
            'token_distribution': self._analyze_distribution(prompts),
            'redundancy_analysis': self._find_redundancies(prompts),
            'cost_analysis': self._calculate_costs(prompts),
            'optimization_potential': self._identify_optimizations(prompts)
        }
        
        return PromptAnalysisReport(**report)
    
    def _find_redundancies(self, prompts: List[Prompt]) -> Dict:
        """Find repeated sections across prompts."""
        # Analyze common patterns
        common_sections = {}
        
        for prompt in prompts:
            sections = self._extract_sections(prompt.content)
            for section in sections:
                hash_key = hashlib.md5(section.encode()).hexdigest()
                common_sections[hash_key] = common_sections.get(hash_key, 0) + 1
        
        # Find sections that appear in >80% of prompts
        total = len(prompts)
        redundant = {
            k: v for k, v in common_sections.items() 
            if v / total > 0.8
        }
        
        return redundant
```

#### Expected Findings
- Examples section: 15k chars (can reduce to 3k)
- Rules section: 8k chars (can reduce to 2k)
- Context section: 5k chars (can be dynamic)
- Boilerplate: 7k chars (can template)

---

### STORY-006-02: Implementeer Dynamic Prompts

**Story Points**: 5

**Als een** developer  
**wil ik** context-aware prompt building  
**zodat** alleen relevante info gestuurd wordt.

#### Acceptance Criteria
- [ ] Template systeem voor prompts
- [ ] Dynamic example selection
- [ ] Context compression algoritme
- [ ] Prompt size <10k chars

#### Implementation Design
```python
class DynamicPromptBuilder:
    """Build optimized prompts based on context."""
    
    def __init__(self):
        self.templates = self._load_templates()
        self.example_bank = self._load_examples()
        self.rule_sets = self._load_rules()
    
    def build_prompt(
        self, 
        term: str, 
        context: str,
        requirements: Dict
    ) -> str:
        # Select base template
        template = self._select_template(context)
        
        # Get relevant examples (max 3)
        examples = self._select_examples(term, context, limit=3)
        
        # Get applicable rules only
        rules = self._select_rules(context, requirements)
        
        # Compress context
        compressed_context = self._compress_context(context)
        
        # Build final prompt
        prompt = template.format(
            term=term,
            context=compressed_context,
            examples=self._format_examples(examples),
            rules=self._format_rules(rules)
        )
        
        # Verify size
        if len(prompt) > 10000:
            prompt = self._further_compress(prompt)
        
        return prompt
    
    def _select_examples(self, term: str, context: str, limit: int) -> List[Example]:
        """Select most relevant examples using embeddings."""
        # Calculate similarity scores
        term_embedding = self.get_embedding(term)
        
        scored_examples = []
        for example in self.example_bank:
            score = cosine_similarity(term_embedding, example.embedding)
            if example.context == context:
                score *= 1.5  # Boost same context
            scored_examples.append((score, example))
        
        # Return top N
        scored_examples.sort(key=lambda x: x[0], reverse=True)
        return [ex for _, ex in scored_examples[:limit]]
```

#### Optimization Strategies

1. **Template Variables**
```python
OPTIMIZED_TEMPLATE = """
Genereer een {style} definitie voor: {term}

Context: {compressed_context}

Belangrijkste regels:
{selected_rules}

Relevante voorbeelden:
{dynamic_examples}

Definitie:"""
```

2. **Rule Compression**
```python
# Instead of listing all 46 rules
RULE_SETS = {
    'juridisch': "Focus op juridische precisie, vermijd vage termen",
    'algemeen': "Helder, begrijpelijk, geen jargon",
    'technisch': "Exact, met technische termen waar nodig"
}
```

3. **Example Selection**
- Use semantic search to find relevant examples
- Maximum 3 examples instead of 20+
- Shorter examples (50 words max)

---

### STORY-006-03: A/B Test Nieuwe Prompts

**Story Points**: 3

**Als een** product owner  
**wil ik** quality metrics vergelijken  
**zodat** kwaliteit behouden blijft.

#### Acceptance Criteria
- [ ] A/B test framework
- [ ] Quality metrics dashboard
- [ ] Statistical significance check
- [ ] Rollback capability

#### A/B Test Framework
```python
class PromptABTest:
    """A/B testing framework for prompt optimization."""
    
    def __init__(self, test_name: str, traffic_split: float = 0.1):
        self.test_name = test_name
        self.traffic_split = traffic_split
        self.metrics_collector = MetricsCollector()
        
    def should_use_variant(self, user_id: str) -> bool:
        """Determine if user gets variant (B) or control (A)."""
        # Consistent assignment based on user ID
        hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        return (hash_value % 100) < (self.traffic_split * 100)
    
    def track_result(self, variant: str, result: DefinitionResult):
        """Track metrics for analysis."""
        metrics = {
            'variant': variant,
            'response_time': result.response_time,
            'token_count': result.token_count,
            'validation_score': result.validation_score,
            'user_feedback': result.user_feedback,
            'cost': result.estimated_cost
        }
        
        self.metrics_collector.record(self.test_name, metrics)
    
    def analyze_results(self) -> ABTestReport:
        """Analyze test results for significance."""
        control_metrics = self.metrics_collector.get_metrics(
            self.test_name, variant='A'
        )
        variant_metrics = self.metrics_collector.get_metrics(
            self.test_name, variant='B'
        )
        
        report = ABTestReport()
        
        # Statistical tests
        for metric in ['response_time', 'validation_score', 'cost']:
            t_stat, p_value = stats.ttest_ind(
                control_metrics[metric],
                variant_metrics[metric]
            )
            
            report.add_comparison(
                metric=metric,
                control_mean=np.mean(control_metrics[metric]),
                variant_mean=np.mean(variant_metrics[metric]),
                p_value=p_value,
                significant=(p_value < 0.05)
            )
        
        return report
```

#### Test Protocol

1. **Week 1**: 10% traffic to optimized prompts
2. **Week 2**: If no quality degradation, increase to 25%
3. **Week 3**: Full rollout if metrics positive

#### Success Criteria
- Validation scores: No decrease (p > 0.05)
- Response time: -40% or better (p < 0.01)
- Cost: -50% or better (p < 0.01)
- User complaints: No increase

## Definition of Done (Epic Level)

- [ ] Prompt size consistently <10k chars
- [ ] Cost reduction verified in production
- [ ] Response time <5 seconds P95
- [ ] A/B test shows no quality degradation
- [ ] Monitoring dashboard active
- [ ] Rollback procedure tested

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Quality degradation | High | A/B test with gradual rollout |
| Context loss | Medium | Semantic similarity matching |
| Edge case failures | Low | Fallback to full prompt |

## Cost Analysis

### Current State (per 1000 requests)
- Prompt tokens: 35M tokens
- Cost: €350
- Response time: 10s average

### Target State (per 1000 requests)
- Prompt tokens: 10M tokens
- Cost: €100
- Response time: 4s average

### ROI
- Monthly savings: €2,500 (at 10k requests/month)
- Implementation cost: 10 story points
- Payback period: <2 weeks

## Success Metrics

- Prompt size reduction: 71%
- Cost reduction: 70%
- Speed improvement: 60%
- Quality maintenance: 100%

---
*Epic owner: AI/Backend Team*  
*Last updated: 2025-01-18*