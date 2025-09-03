# Implementatieplan - Gerefactorde Prompt Integratie

## Executive Summary
Refactoring van prompt.txt van 7250 naar ~1250 tokens (-83%) met behoud van alle functionaliteit.

## Fase 1: Voorbereiding

### 1.1 Backup Huidige Situatie
```bash
# Backup originele prompt
cp logs/prompt.txt logs/prompt_backup_20250903.txt

# Backup prompt builder
cp src/services/prompts/modular_prompt_builder.py \
   src/services/prompts/modular_prompt_builder_backup.py
```

### 1.2 Test Suite Uitbreiden
```python
# tests/test_prompt_refactoring.py
class TestPromptRefactoring:
    def test_token_count_reduction(self):
        """Verify token count < 2000"""

    def test_no_contradictions(self):
        """Verify haakjes regel consistency"""

    def test_no_duplications(self):
        """Verify geen duplicate 'start niet met' regels"""

    def test_ontology_single_definition(self):
        """Verify ontologie wordt 1x uitgelegd"""
```

## Fase 2: Implementatie

### 2.1 Nieuwe Prompt Module Structuur
```python
# src/services/prompts/refactored_modules/

core_prompt.py          # Sectie 1-2: Rol & Kernregels
definition_structure.py # Sectie 3: Definitie Structuur
restrictions.py        # Sectie 4: Verboden
context_handler.py     # Sectie 5: Context Verwerking
quality_checker.py     # Sectie 6: Kwaliteitscheck
```

### 2.2 Modular Prompt Builder Aanpassing
```python
class RefactoredPromptBuilder:
    """Geoptimaliseerde prompt builder met 83% token reductie"""

    def __init__(self):
        self.sections = {
            'role': CorePrompt(),           # 50 tokens
            'rules': CoreRules(),            # 500 tokens
            'structure': DefinitionStructure(), # 300 tokens
            'restrictions': Restrictions(),  # 200 tokens
            'context': ContextHandler(),     # 100 tokens
            'quality': QualityChecker()      # 100 tokens
        }

    def build(self, begrip: str, context: dict) -> str:
        """Build prompt met max 1250 tokens"""
        prompt_parts = []

        # Altijd: Rol & Kernregels
        prompt_parts.append(self.sections['role'].render())
        prompt_parts.append(self.sections['rules'].render())

        # Ontologie bepaling
        category = self._determine_ontology(begrip)
        prompt_parts.append(
            self.sections['structure'].render(category)
        )

        # Restricties
        prompt_parts.append(self.sections['restrictions'].render())

        # Context indien aanwezig
        if context:
            prompt_parts.append(
                self.sections['context'].render(context)
            )

        # Quality check
        prompt_parts.append(self.sections['quality'].render())

        return '\n\n'.join(prompt_parts)
```

### 2.3 Configuratie Update
```yaml
# config/prompt_settings.yaml
prompt:
  version: "2.0"
  max_tokens: 1250
  structure:
    role_tokens: 50
    rules_tokens: 500
    structure_tokens: 300
    restrictions_tokens: 200
    context_tokens: 100
    quality_tokens: 100

  features:
    token_optimization: true
    duplicate_removal: true
    contradiction_resolution: true
    hierarchical_structure: true
```

## Fase 3: Validatie

### 3.1 A/B Testing
```python
# scripts/ab_test_prompts.py
test_terms = [
    "slachtoffer",
    "toezicht",
    "sanctionering",
    "registratie",
    "maatregel"
]

results = {
    'old_prompt': {},
    'new_prompt': {}
}

for term in test_terms:
    # Test met oude prompt
    old_def = generate_with_old_prompt(term)
    results['old_prompt'][term] = {
        'definition': old_def,
        'tokens': count_tokens(old_prompt),
        'quality_score': evaluate_quality(old_def)
    }

    # Test met nieuwe prompt
    new_def = generate_with_new_prompt(term)
    results['new_prompt'][term] = {
        'definition': new_def,
        'tokens': count_tokens(new_prompt),
        'quality_score': evaluate_quality(new_def)
    }

# Genereer rapport
generate_comparison_report(results)
```

### 3.2 Kwaliteitsmetrieken
```python
def evaluate_prompt_quality(definition: str) -> dict:
    return {
        'starts_correctly': not starts_with_forbidden(definition),
        'single_sentence': is_single_sentence(definition),
        'no_parentheses': has_no_explanatory_parentheses(definition),
        'ontology_clear': has_clear_ontology(definition),
        'context_implicit': context_not_explicit(definition),
        'length_optimal': 150 <= len(definition) <= 350,
        'no_modality': has_no_modal_verbs(definition),
        'measurable': has_measurable_criteria(definition)
    }
```

## Fase 4: Deployment

### 4.1 Gefaseerde Uitrol
```python
# src/services/prompt_selector.py
class PromptSelector:
    def __init__(self, rollout_percentage: int = 0):
        self.rollout_percentage = rollout_percentage

    def select_prompt_builder(self, user_id: str = None):
        """Gradually rollout new prompt"""
        if self.rollout_percentage == 0:
            return OldPromptBuilder()
        elif self.rollout_percentage == 100:
            return RefactoredPromptBuilder()
        else:
            # Use hash for consistent selection per user
            if hash(user_id) % 100 < self.rollout_percentage:
                return RefactoredPromptBuilder()
            return OldPromptBuilder()
```

**Rollout Schedule:**
- Week 1: 10% gebruikers (monitoring)
- Week 2: 25% gebruikers (feedback)
- Week 3: 50% gebruikers (validatie)
- Week 4: 100% gebruikers (volledig)

### 4.2 Monitoring
```python
# monitoring/prompt_metrics.py
METRICS_TO_TRACK = {
    'token_usage': {
        'old_prompt_avg': None,
        'new_prompt_avg': None,
        'reduction_percentage': None
    },
    'response_time': {
        'old_prompt_p50': None,
        'new_prompt_p50': None,
        'improvement': None
    },
    'quality_scores': {
        'old_prompt_avg': None,
        'new_prompt_avg': None,
        'categories': ['structure', 'content', 'grammar']
    },
    'error_rate': {
        'old_prompt': None,
        'new_prompt': None
    }
}
```

## Fase 5: Documentatie & Training

### 5.1 Update Documentatie
- [x] `docs/refactor-log.md` - Technische details refactoring
- [x] `docs/PROMPT_REFACTORING_COMPARISON.md` - Voor/na vergelijking
- [x] `docs/PROMPT_REFACTORING_IMPLEMENTATION.md` - Dit document
- [ ] `README.md` - Update met nieuwe prompt structuur
- [ ] `docs/api/PROMPT_API.md` - API documentatie update

### 5.2 Team Communicatie
```markdown
## Prompt Optimalisatie - Team Update

**Wat:** Prompt gerefactored van 7250 naar 1250 tokens
**Waarom:** Kosten reductie, betere performance, geen duplicatie
**Impact:** Geen functionele wijzigingen, alleen optimalisatie
**Wanneer:** Gefaseerde uitrol over 4 weken
**Actie:** Review A/B test resultaten week 1
```

## Risico's & Mitigatie

| Risico | Impact | Kans | Mitigatie |
|--------|--------|------|-----------|
| Output kwaliteit degradeert | Hoog | Laag | A/B testing, rollback mogelijk |
| Onverwachte edge cases | Medium | Medium | Uitgebreide test suite |
| Context handling verschilt | Medium | Laag | Expliciete context tests |
| Ontologie bepaling faalt | Hoog | Laag | Fallback naar default |

## Success Criteria

✅ Token gebruik -80% of meer
✅ Response tijd -30% of meer
✅ Kwaliteitsscore gelijk of beter
✅ Geen toename error rate
✅ Positieve gebruikersfeedback

## Rollback Plan

Bij kritieke issues:
1. `prompt_selector.rollout_percentage = 0`
2. Restore `modular_prompt_builder_backup.py`
3. Analyse logs voor root cause
4. Fix & retry met kleinere rollout

## Conclusie

Deze gefaseerde implementatie minimaliseert risico terwijl we 83% token reductie realiseren met behoud van alle functionaliteit. De hierarchische structuur maakt toekomstige aanpassingen eenvoudiger.
