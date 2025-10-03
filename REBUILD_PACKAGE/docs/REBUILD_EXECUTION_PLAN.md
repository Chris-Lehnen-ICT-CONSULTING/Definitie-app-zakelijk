# DefinitieAgent Rebuild Execution Plan

## Executive Summary

**Project:** DefinitieAgent Complete Rebuild
**Duration:** 9-10 weeks (45-50 working days)
**Effort:** 360-400 hours total
**Target:** Production-ready AI-powered legal definition generator
**Team Size:** 1 developer (domain knowledge: 2 months experience)

### Key Metrics

| Metric | Current | Target | Reduction |
|--------|---------|--------|-----------|
| **Total LOC** | 83,319 | ~25,000 | 70% |
| **Service Layers** | 6+ | 3 | 50% |
| **Dependencies** | Complex web | Clean DI | 80% simpler |
| **Response Time** | 5-10s | <2s | 60-80% faster |
| **Test Coverage** | 60% | 85%+ | 40% increase |
| **Documentation** | 400+ pages | Maintained | 100% coverage |

### Tech Stack

**Backend:**
- FastAPI (Python 3.11+)
- PostgreSQL (or SQLite for simplicity)
- Redis (caching)
- Alembic (migrations)

**Frontend:**
- Streamlit (Phase 1 - quick MVP)
- Optional React (Phase 2 - if needed)

**Infrastructure:**
- Docker + docker-compose
- GitHub Actions (CI/CD)
- pytest + coverage

**AI/ML:**
- OpenAI GPT-4 (generation)
- LangChain (optional - if needed)

### Success Criteria

**Week 4 (MVP Gate):**
- [ ] 46 validation rules working
- [ ] Basic generation (1 definition)
- [ ] 90%+ baseline validation pass
- [ ] <3s generation time

**Week 7 (Feature Parity Gate):**
- [ ] All 11 generation phases
- [ ] Web lookup integration
- [ ] Duplicate detection
- [ ] Export functionality

**Week 9 (Production Ready Gate):**
- [ ] 42 baseline definitions validate
- [ ] <2s average response time
- [ ] 85%+ test coverage
- [ ] Zero critical bugs

### Deliverables

1. **Business Logic Assets** (Week 1)
   - 46 validation rules (YAML configs)
   - 11-phase generation workflow (documented)
   - Prompt templates (extracted)
   - Test baseline (42 definitions)

2. **Modern Platform** (Week 2)
   - Docker environment
   - FastAPI backend skeleton
   - Database + migrations
   - CI/CD pipeline

3. **Core Engine** (Week 3-4)
   - AI service (OpenAI integration)
   - Validation engine
   - Generation orchestrator
   - Database layer

4. **Advanced Features** (Week 5-6)
   - Context management
   - Web lookup (Wikipedia, SRU)
   - Duplicate detection
   - Regeneration workflows

5. **User Interface** (Week 7-8)
   - Streamlit UI
   - Data migration
   - Export functionality

6. **Quality Assurance** (Week 9)
   - Integration tests
   - Performance validation
   - Bug fixes
   - Production prep

### Risk Management

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Business logic extraction incomplete | Medium | High | Week 1 validation gate + daily reviews |
| AI API rate limits | Low | Medium | Implement retry logic + caching |
| Performance degradation | Medium | High | Continuous benchmarking + Week 4/7/9 gates |
| Data migration issues | Low | Medium | Week 8 migration testing + rollback plan |
| Scope creep | Medium | High | Strict adherence to plan + buffer week |

---

## Week 1: Business Logic Extraction & Finalization
**Goal:** Extract ALL business logic from current codebase into portable, documented formats
**Hours:** 40 hours (8h/day × 5 days)
**Success Criteria:** Complete extraction of 46 rules + 11 phases + prompts + test data

### Day 1 - Monday: Validation Rules Extraction (8h)

#### Morning Session (4h): Setup & Rule Discovery

**Tasks:**
1. Create project structure for extracted logic
2. Scan current codebase for ALL validation rules
3. Document each rule's location and implementation
4. Create extraction templates

**Commands:**
```bash
# Navigate to project
cd /Users/chrislehnen/Projecten/Definitie-app

# Create extraction workspace
mkdir -p rebuild/extracted/{validation,generation,prompts,tests,docs}
mkdir -p rebuild/extracted/validation/{arai,con,ess,int,sam,str,ver,dup}

# Count validation rules
find src/toetsregels/regels -name "*.py" | wc -l
# Expected: ~46 files

# List all validation rules
ls -1 src/toetsregels/regels/*.py > rebuild/extracted/validation/rules_inventory.txt

# Check for JSON configs
find config -name "*.json" | grep -i toets
```

**File: rebuild/extracted/validation/EXTRACTION_TEMPLATE.yaml**
```yaml
# Validation Rule Extraction Template
id: "RULE-ID"  # e.g., ARAI-01
category: "CATEGORY"  # ARAI, CON, ESS, INT, SAM, STR, VER, DUP
priority: "high|medium|low"
enabled: true

metadata:
  naam: "Rule Name in Dutch"
  uitleg: "Detailed explanation"
  version: "1.0"
  last_updated: "2025-10-02"

implementation:
  type: "regex|pattern|logic|ai"
  patterns: []  # Regex patterns if applicable
  logic_description: "Human-readable logic"
  code_reference: "src/toetsregels/regels/RULE-ID.py"

validation:
  input_fields:
    - definitie
    - begrip
    - context
  output:
    success: boolean
    message: string
    score: float  # 0.0-1.0

examples:
  good:
    - "Example of passing definition"
  bad:
    - "Example of failing definition"

generation_hints:
  - "Instruction 1 for AI generator"
  - "Instruction 2 for AI generator"

test_cases:
  - input:
      definitie: "Test definition"
      begrip: "test"
    expected:
      success: true
      score: 1.0
```

**Validation Checklist:**
- [ ] Extraction directory structure created
- [ ] All 46 rule files identified
- [ ] Template validated (YAML syntax)
- [ ] Git commit: "chore: setup business logic extraction workspace"

**Deliverable:** Clean workspace + complete rule inventory

---

#### Afternoon Session (4h): Extract ARAI Rules (7 rules)

**Tasks:**
1. Extract ARAI-01 through ARAI-06 + ARAI-02SUB1, ARAI-02SUB2, ARAI-04SUB1
2. Document patterns, logic, and examples
3. Create test cases for each rule
4. Validate YAML syntax

**Commands:**
```bash
# Extract ARAI-01 (example)
cat src/toetsregels/regels/ARAI-01.py

# Create YAML config
cat > rebuild/extracted/validation/arai/ARAI-01.yaml << 'EOF'
id: "ARAI-01"
category: "ARAI"
priority: "high"
enabled: true

metadata:
  naam: "Geen werkwoorden als kern"
  uitleg: "Een definitie mag niet beginnen met een werkwoord als kernwoord. Definities beschrijven wat iets IS, niet wat het DOET."
  version: "1.0"
  last_updated: "2025-10-02"
  author: "Extracted from legacy system"

implementation:
  type: "regex"
  patterns:
    - '\b(is|zijn|wordt|worden|kan|mag|moet|zal|heeft|hebben)\b'
  logic_description: |
    1. Check if definition starts with verb patterns
    2. Cross-reference with good/bad examples
    3. Return pass/fail with specific message
  code_reference: "src/toetsregels/regels/ARAI-01.py"

  good_patterns:
    - "^(Een|Een|De|Het) [a-z]+"  # Starts with article
  bad_patterns:
    - "^(Is|Zijn|Wordt|Worden)"  # Starts with verb

validation:
  input_fields:
    - definitie
    - begrip
  output:
    success: boolean
    message: string
    score: float

examples:
  good:
    - "Een proces waarbij identiteitsgegevens worden gecontroleerd"
    - "De handeling waarbij data wordt vastgelegd"
  bad:
    - "Is een proces waarbij..."
    - "Wordt gebruikt om..."

generation_hints:
  - "Begin definitie met lidwoord (Een/De/Het)"
  - "Gebruik zelfstandig naamwoord als kernwoord"
  - "Vermijd werkwoorden aan het begin"
  - "Formuleer als 'X is een Y' structuur"

test_cases:
  - name: "Valid definition with article"
    input:
      definitie: "Een systematische controle van identiteitsgegevens"
      begrip: "verificatie"
    expected:
      success: true
      score: 1.0
      message_contains: "✔️ ARAI01"

  - name: "Invalid definition with verb"
    input:
      definitie: "Is een proces waarbij gegevens worden gecontroleerd"
      begrip: "verificatie"
    expected:
      success: false
      score: 0.0
      message_contains: "❌ ARAI01"

  - name: "Edge case - starts with werkwoord"
    input:
      definitie: "Wordt gebruikt om identiteit te verifiëren"
      begrip: "verificatie"
    expected:
      success: false
      score: 0.0

performance:
  max_execution_time_ms: 50
  complexity: "O(n)"  # Linear with definition length
EOF

# Validate YAML syntax
python3 << 'PYTHON'
import yaml
with open('rebuild/extracted/validation/arai/ARAI-01.yaml', 'r') as f:
    config = yaml.safe_load(f)
    print(f"✓ Valid YAML for {config['id']}")
    print(f"  Priority: {config['priority']}")
    print(f"  Test cases: {len(config['test_cases'])}")
PYTHON
```

**Script: rebuild/scripts/extract_rule.py**
```python
#!/usr/bin/env python3
"""Extract validation rule from Python file to YAML config."""

import ast
import re
import yaml
from pathlib import Path

def extract_rule(rule_file: Path) -> dict:
    """Extract rule metadata from Python file."""

    with open(rule_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse Python AST
    tree = ast.parse(content)

    # Extract class name (e.g., ARAI01Validator)
    validator_class = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and 'Validator' in node.name:
            validator_class = node
            break

    if not validator_class:
        raise ValueError(f"No validator class found in {rule_file}")

    # Extract docstring
    docstring = ast.get_docstring(validator_class) or ""

    # Extract patterns from validate method
    patterns = []
    for node in ast.walk(validator_class):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and 'patroon' in target.id.lower():
                    # Extract pattern values
                    pass  # TODO: implement pattern extraction

    # Build config dict
    rule_id = rule_file.stem  # e.g., ARAI-01
    category = rule_id.split('-')[0]

    config = {
        'id': rule_id,
        'category': category,
        'priority': 'medium',  # Default, will be updated manually
        'enabled': True,
        'metadata': {
            'naam': docstring.split('\n')[0] if docstring else rule_id,
            'uitleg': docstring,
            'version': '1.0',
            'code_reference': str(rule_file.relative_to(Path.cwd()))
        },
        'implementation': {
            'type': 'regex',  # Default
            'patterns': patterns,
            'logic_description': 'To be documented'
        },
        'validation': {
            'input_fields': ['definitie', 'begrip', 'context'],
            'output': {
                'success': 'boolean',
                'message': 'string',
                'score': 'float'
            }
        },
        'examples': {
            'good': [],
            'bad': []
        },
        'generation_hints': [],
        'test_cases': []
    }

    return config

if __name__ == '__main__':
    import sys

    if len(sys.argv) != 2:
        print("Usage: extract_rule.py <rule_file.py>")
        sys.exit(1)

    rule_file = Path(sys.argv[1])
    config = extract_rule(rule_file)

    # Write YAML
    output_dir = Path('rebuild/extracted/validation') / config['category'].lower()
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{config['id']}.yaml"
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)

    print(f"✓ Extracted {config['id']} → {output_file}")
```

**Commands to extract all ARAI rules:**
```bash
# Make script executable
chmod +x rebuild/scripts/extract_rule.py

# Extract all ARAI rules
for rule in src/toetsregels/regels/ARAI-*.py; do
    python rebuild/scripts/extract_rule.py "$rule"
done

# Verify extraction
ls -lh rebuild/extracted/validation/arai/
# Expected: 9 YAML files (ARAI-01 to ARAI-06 + subs)

# Validate all YAML files
for yaml_file in rebuild/extracted/validation/arai/*.yaml; do
    python -c "import yaml; yaml.safe_load(open('$yaml_file'))" && echo "✓ $yaml_file"
done
```

**Manual Refinement Checklist:**
- [ ] ARAI-01: Verify patterns, add test cases
- [ ] ARAI-02: Document logic, add examples
- [ ] ARAI-03: Extract generation hints
- [ ] ARAI-04: Add edge cases
- [ ] ARAI-05: Document business rationale
- [ ] ARAI-06: Validate test coverage
- [ ] ARAI-02SUB1: Document parent relationship
- [ ] ARAI-02SUB2: Document parent relationship
- [ ] ARAI-04SUB1: Document parent relationship

**Validation:**
```bash
# Count test cases across all ARAI rules
python3 << 'PYTHON'
import yaml
from pathlib import Path

total_tests = 0
for yaml_file in Path('rebuild/extracted/validation/arai').glob('*.yaml'):
    with open(yaml_file) as f:
        config = yaml.safe_load(f)
        tests = len(config.get('test_cases', []))
        print(f"{config['id']}: {tests} test cases")
        total_tests += tests

print(f"\nTotal ARAI test cases: {total_tests}")
# Target: 27+ test cases (3 per rule minimum)
PYTHON
```

**Deliverable:**
- 9 YAML configs for ARAI rules
- Minimum 27 test cases
- Complete pattern documentation

**End of Day 1 Commit:**
```bash
git add rebuild/extracted/validation/arai/
git commit -m "feat(extraction): extract ARAI validation rules (9 rules, 27+ tests)"
```

---

### Day 2 - Tuesday: Complete Validation Rules Extraction (8h)

#### Morning Session (4h): CON, ESS, VER Rules (9 rules)

**Tasks:**
1. Extract CON-01, CON-02 (consistency rules)
2. Extract ESS-01 through ESS-05 (essence rules)
3. Extract VER-01 through VER-03 (clarity rules)

**Commands:**
```bash
# Extract CON rules (2 rules)
for rule in src/toetsregels/regels/CON-*.py; do
    python rebuild/scripts/extract_rule.py "$rule"
done

# Extract ESS rules (5 rules)
for rule in src/toetsregels/regels/ESS-*.py; do
    python rebuild/scripts/extract_rule.py "$rule"
done

# Extract VER rules (3 rules - note: might be 2, verify)
for rule in src/toetsregels/regels/VER-*.py; do
    python rebuild/scripts/extract_rule.py "$rule"
done

# Verify extraction
echo "CON rules:" && ls rebuild/extracted/validation/con/
echo "ESS rules:" && ls rebuild/extracted/validation/ess/
echo "VER rules:" && ls rebuild/extracted/validation/ver/
```

**Manual Refinement Focus:**
- **CON-01**: Consistency with existing definitions (duplicate detection logic)
- **CON-02**: Internal consistency (no self-contradictions)
- **ESS-01 to ESS-05**: Essence rules (capturing core meaning)
- **VER-01 to VER-03**: Clarity rules (unambiguous language)

**Validation Checklist:**
- [ ] CON rules: Minimum 6 test cases (3 per rule)
- [ ] ESS rules: Minimum 15 test cases (3 per rule)
- [ ] VER rules: Minimum 9 test cases (3 per rule)
- [ ] All patterns documented
- [ ] Generation hints extracted
- [ ] Examples complete (good + bad)

---

#### Afternoon Session (4h): STR, SAM, INT Rules (27 rules)

**Tasks:**
1. Extract STR-01 through STR-09 (structure rules)
2. Extract SAM-01 through SAM-08 (composition rules)
3. Extract INT-01 through INT-10 (interpretation rules)

**Commands:**
```bash
# Extract STR rules (9 rules)
for rule in src/toetsregels/regels/STR-*.py; do
    python rebuild/scripts/extract_rule.py "$rule"
done

# Extract SAM rules (8 rules)
for rule in src/toetsregels/regels/SAM-*.py; do
    python rebuild/scripts/extract_rule.py "$rule"
done

# Extract INT rules (10 rules)
for rule in src/toetsregels/regels/INT-*.py; do
    python rebuild/scripts/extract_rule.py "$rule"
done

# Generate extraction summary
python3 << 'PYTHON'
import yaml
from pathlib import Path
from collections import defaultdict

categories = defaultdict(list)

for yaml_file in Path('rebuild/extracted/validation').rglob('*.yaml'):
    with open(yaml_file) as f:
        config = yaml.safe_load(f)
        category = config['category']
        categories[category].append(config['id'])

print("Validation Rules Extraction Summary")
print("=" * 50)
for category in sorted(categories.keys()):
    rules = categories[category]
    print(f"{category}: {len(rules)} rules")
    for rule in sorted(rules):
        print(f"  - {rule}")

total = sum(len(rules) for rules in categories.values())
print(f"\nTotal: {total} rules extracted")
print(f"Target: 46 rules")
print(f"Status: {'✓ COMPLETE' if total >= 46 else '⚠ INCOMPLETE'}")
PYTHON
```

**Validation:**
```bash
# Count total test cases
python3 << 'PYTHON'
import yaml
from pathlib import Path

total_tests = 0
by_category = {}

for yaml_file in Path('rebuild/extracted/validation').rglob('*.yaml'):
    with open(yaml_file) as f:
        config = yaml.safe_load(f)
        category = config['category']
        tests = len(config.get('test_cases', []))

        if category not in by_category:
            by_category[category] = 0
        by_category[category] += tests
        total_tests += tests

print("Test Cases by Category")
print("=" * 50)
for category in sorted(by_category.keys()):
    print(f"{category}: {by_category[category]} tests")

print(f"\nTotal test cases: {total_tests}")
print(f"Target: 138+ (3 per rule minimum)")
print(f"Status: {'✓ COMPLETE' if total_tests >= 138 else '⚠ INCOMPLETE'}")
PYTHON
```

**Deliverable:**
- 46 YAML configs (all validation rules)
- 138+ test cases
- Complete pattern documentation
- Generation hints for AI

**End of Day 2 Commit:**
```bash
git add rebuild/extracted/validation/
git commit -m "feat(extraction): complete validation rules extraction (46 rules, 138+ tests)"
```

---

### Day 3 - Wednesday: Generation Workflow Extraction (8h)

#### Morning Session (4h): 11-Phase Generation Workflow

**Tasks:**
1. Document 11-phase generation workflow
2. Extract prompt templates for each phase
3. Document dependencies between phases
4. Create workflow execution plan

**File: rebuild/extracted/generation/GENERATION_WORKFLOW.yaml**
```yaml
name: "DefinitieAgent Generation Workflow"
version: "2.0"
description: "11-phase AI-powered legal definition generation workflow"

phases:
  - id: "phase-01"
    name: "Context Gathering"
    order: 1
    dependencies: []
    description: "Collect all context information needed for generation"

    inputs:
      - begrip (required)
      - ontologische_categorie (optional)
      - organisatorische_context (optional)
      - juridische_context (optional)
      - wettelijke_basis (optional)
      - existing_definitions (optional)

    outputs:
      - context_bundle (dict)
      - web_lookup_results (optional)

    actions:
      - validate_inputs
      - fetch_existing_definitions
      - perform_web_lookup (if enabled)
      - build_context_bundle

    estimated_time: "500ms"

  - id: "phase-02"
    name: "Prompt Construction"
    order: 2
    dependencies: ["phase-01"]
    description: "Build AI prompt with context and validation rules"

    inputs:
      - context_bundle (from phase-01)
      - validation_rules (46 rules)
      - generation_hints (from rules)

    outputs:
      - prompt_text (string)
      - prompt_metadata (dict)

    actions:
      - load_prompt_template
      - inject_context
      - inject_validation_rules
      - inject_examples
      - inject_hints

    estimated_time: "200ms"

    prompt_structure:
      - system_message: "Role definition for AI"
      - context_section: "Business context and requirements"
      - rules_section: "46 validation rules with examples"
      - hints_section: "Generation guidelines"
      - output_format: "Expected JSON structure"

  - id: "phase-03"
    name: "AI Generation"
    order: 3
    dependencies: ["phase-02"]
    description: "Call OpenAI API to generate definition"

    inputs:
      - prompt_text (from phase-02)

    outputs:
      - raw_definition (string)
      - generation_metadata (dict)

    actions:
      - call_openai_api
      - parse_response
      - extract_definition_text

    configuration:
      model: "gpt-4"
      temperature: 0.3
      max_tokens: 500
      timeout: 30

    estimated_time: "2000ms"
    retry_strategy:
      max_retries: 3
      backoff_multiplier: 2

  - id: "phase-04"
    name: "Text Cleaning"
    order: 4
    dependencies: ["phase-03"]
    description: "Clean and normalize generated text"

    inputs:
      - raw_definition (from phase-03)

    outputs:
      - cleaned_definition (string)
      - cleaning_report (dict)

    actions:
      - remove_extra_whitespace
      - normalize_punctuation
      - fix_capitalization
      - remove_artifacts

    estimated_time: "50ms"

  - id: "phase-05"
    name: "Validation"
    order: 5
    dependencies: ["phase-04"]
    description: "Run all 46 validation rules"

    inputs:
      - cleaned_definition (from phase-04)
      - begrip (original)
      - context_bundle (from phase-01)

    outputs:
      - validation_result (ValidationResult)
      - detailed_scores (dict)
      - failing_rules (list)

    actions:
      - run_validation_rules (parallel if possible)
      - aggregate_scores
      - identify_failures
      - generate_feedback

    estimated_time: "500ms"

    scoring:
      overall_score: "weighted average of all rules"
      weights:
        high_priority: 1.0
        medium_priority: 0.7
        low_priority: 0.4

  - id: "phase-06"
    name: "Quality Gate"
    order: 6
    dependencies: ["phase-05"]
    description: "Decide if definition meets quality threshold"

    inputs:
      - validation_result (from phase-05)

    outputs:
      - gate_decision (pass|fail|retry)
      - gate_feedback (string)

    actions:
      - check_minimum_score (threshold: 0.7)
      - check_critical_rules (high priority must pass)
      - decide_next_action

    thresholds:
      auto_accept: 0.85
      retry_threshold: 0.7
      auto_reject: 0.5

    estimated_time: "10ms"

  - id: "phase-07"
    name: "Regeneration (if needed)"
    order: 7
    dependencies: ["phase-06"]
    description: "Retry generation with feedback if quality gate fails"

    inputs:
      - gate_decision (from phase-06)
      - failing_rules (from phase-05)
      - previous_attempt (from phase-03)

    outputs:
      - improved_definition (string)
      - retry_count (int)

    actions:
      - build_feedback_prompt
      - inject_failing_rules_context
      - retry_ai_generation

    configuration:
      max_retries: 2
      retry_strategy: "feedback_loop"

    estimated_time: "2000ms per retry"

  - id: "phase-08"
    name: "Example Generation"
    order: 8
    dependencies: ["phase-06"]  # Only if gate passes
    description: "Generate practical examples for the definition"

    inputs:
      - accepted_definition (from phase-06)
      - begrip (original)

    outputs:
      - examples (list of strings)
      - example_types (list: sentence, practical, counter)

    actions:
      - generate_sentence_example
      - generate_practical_example
      - generate_counter_example (optional)

    configuration:
      num_examples: 3
      example_types:
        - sentence  # Definition used in a sentence
        - practical  # Real-world application
        - counter  # What it's NOT

    estimated_time: "1500ms"

  - id: "phase-09"
    name: "Metadata Enrichment"
    order: 9
    dependencies: ["phase-08"]
    description: "Add metadata and related information"

    inputs:
      - accepted_definition (from phase-06)
      - begrip (original)
      - context_bundle (from phase-01)

    outputs:
      - enriched_definition (Definition object)

    actions:
      - add_synonyms (from web lookup)
      - add_related_terms
      - add_legal_references
      - compute_metadata

    estimated_time: "300ms"

  - id: "phase-10"
    name: "Duplicate Detection"
    order: 10
    dependencies: ["phase-09"]
    description: "Check for duplicates or very similar definitions"

    inputs:
      - enriched_definition (from phase-09)
      - existing_definitions (from database)

    outputs:
      - duplicate_check_result (dict)
      - similar_definitions (list)
      - similarity_scores (dict)

    actions:
      - compute_text_similarity (TF-IDF or embeddings)
      - check_exact_duplicates
      - find_near_duplicates (threshold: 0.9)

    configuration:
      similarity_threshold: 0.9
      max_similar_to_return: 5

    estimated_time: "400ms"

  - id: "phase-11"
    name: "Persistence"
    order: 11
    dependencies: ["phase-10"]
    description: "Save definition to database"

    inputs:
      - enriched_definition (from phase-09)
      - duplicate_check_result (from phase-10)

    outputs:
      - saved_definition (Definition with ID)
      - database_record (dict)

    actions:
      - create_database_record
      - save_definition
      - save_examples
      - save_validation_results
      - create_audit_trail

    estimated_time: "200ms"

workflow_metadata:
  total_phases: 11
  estimated_total_time: "5000-7000ms"
  target_time: "2000ms"

  optimization_targets:
    - "Parallel validation rules (phase-05)"
    - "Cache prompt templates (phase-02)"
    - "Batch database operations (phase-11)"
    - "Optional web lookup (phase-01)"

  error_handling:
    retry_phases: [3, 7]  # AI generation phases
    rollback_phases: [11]  # Database operations
    degraded_mode: "Skip optional phases (8, 9, 10)"
```

**Commands:**
```bash
# Create generation workflow documentation
mkdir -p rebuild/extracted/generation/{phases,prompts,templates}

# Validate workflow YAML
python3 << 'PYTHON'
import yaml

with open('rebuild/extracted/generation/GENERATION_WORKFLOW.yaml', 'r') as f:
    workflow = yaml.safe_load(f)

print(f"Workflow: {workflow['name']}")
print(f"Version: {workflow['version']}")
print(f"Phases: {len(workflow['phases'])}")

for phase in workflow['phases']:
    print(f"  {phase['order']}. {phase['name']}")
    print(f"     Dependencies: {phase['dependencies']}")
    print(f"     Est. time: {phase['estimated_time']}")

print(f"\nTotal estimated time: {workflow['workflow_metadata']['estimated_total_time']}")
print(f"Target time: {workflow['workflow_metadata']['target_time']}")
PYTHON
```

---

#### Afternoon Session (4h): Prompt Template Extraction

**Tasks:**
1. Extract current prompt templates
2. Identify prompt components (system, context, rules, output)
3. Document prompt injection points
4. Create modular prompt library

**File: rebuild/extracted/generation/prompts/SYSTEM_PROMPT.md**
```markdown
# System Prompt Template

## Role Definition

You are a specialized AI assistant for generating Dutch legal definitions.

Your expertise:
- Dutch legal terminology
- Ontological categorization (UFO/OntoUML)
- Juridische precisie
- Consistent terminology usage

Your task:
Generate a clear, precise, and legally sound definition for the given term.

## Quality Requirements

The definition MUST:
1. Be in Dutch language
2. Follow the 46 validation rules (provided below)
3. Be clear and unambiguous
4. Use consistent terminology
5. Be 1-3 sentences maximum
6. Start with an article (Een/De/Het), not a verb
7. Describe WHAT something IS, not what it DOES

## Ontological Categories

Definitions should match one of these categories:
- **ENT** (Entiteit): Types, classes, objects
- **ACT** (Activiteit): Processes, actions, procedures
- **REL** (Relatie): Relationships between entities
- **ATT** (Attribuut): Properties, characteristics
- **AUT** (Autorisatie): Authorizations, permissions
- **STA** (Status): States, phases
- **OTH** (Overig): Other

## Output Format

Return ONLY a JSON object with this structure:
```json
{
  "definitie": "The generated definition text",
  "confidence": 0.95,
  "ontologische_categorie": "ENT",
  "rationale": "Brief explanation of approach"
}
```

## Important Rules

- Do NOT include metadata in the definition itself
- Do NOT use passive voice excessively
- Do NOT start with verbs
- Do NOT make it longer than necessary
- DO use clear, precise language
- DO match the ontological category
- DO consider the legal context
```

**File: rebuild/extracted/generation/prompts/CONTEXT_TEMPLATE.md**
```markdown
# Context Injection Template

## Term to Define

**Begrip:** {{begrip}}

## Business Context

{{#if organisatorische_context}}
**Organisatorische Context:** {{organisatorische_context}}
{{/if}}

{{#if juridische_context}}
**Juridische Context:** {{juridische_context}}
{{/if}}

{{#if wettelijke_basis}}
**Wettelijke Basis:** {{wettelijke_basis}}
{{/if}}

{{#if ontologische_categorie}}
**Voorgestelde Categorie:** {{ontologische_categorie}}
{{/if}}

## Related Information

{{#if web_lookup_results}}
### External Sources

**Wikipedia Summary:**
{{web_lookup_results.wikipedia}}

**SRU Registry:**
{{web_lookup_results.sru}}
{{/if}}

{{#if existing_definitions}}
### Existing Similar Definitions

{{#each existing_definitions}}
- **{{this.begrip}}:** {{this.definitie}}
{{/each}}
{{/if}}

## Your Task

Generate a definition for "{{begrip}}" that:
1. Matches the {{ontologische_categorie}} category
2. Fits the {{organisatorische_context}} context
3. Complies with all validation rules below
4. Is distinct from existing definitions
```

**File: rebuild/extracted/generation/prompts/RULES_INJECTION.md**
```markdown
# Validation Rules Injection

## 46 Validation Rules You Must Follow

{{#each validation_rules}}
### {{this.id}}: {{this.metadata.naam}}

**Priority:** {{this.priority}}

**Rule:** {{this.metadata.uitleg}}

**Good Examples:**
{{#each this.examples.good}}
- {{this}}
{{/each}}

**Bad Examples (AVOID):**
{{#each this.examples.bad}}
- {{this}}
{{/each}}

**Generation Hints:**
{{#each this.generation_hints}}
- {{this}}
{{/each}}

---
{{/each}}

## Critical Rules (High Priority)

Focus especially on these high-priority rules:
{{#each high_priority_rules}}
- **{{this.id}}:** {{this.metadata.naam}}
{{/each}}
```

**Commands:**
```bash
# Extract current prompts from codebase
grep -r "system.*prompt" src/ --include="*.py" -A 10 > rebuild/extracted/generation/prompts/current_prompts.txt

# Find prompt construction code
grep -r "PromptService" src/ --include="*.py" | head -20

# Document prompt structure
cat > rebuild/extracted/generation/prompts/PROMPT_STRUCTURE.yaml << 'EOF'
name: "DefinitieAgent Prompt Structure"
version: "2.0"

components:
  - name: "system_message"
    order: 1
    size_estimate: "500 tokens"
    file: "SYSTEM_PROMPT.md"

  - name: "context_injection"
    order: 2
    size_estimate: "200-500 tokens"
    file: "CONTEXT_TEMPLATE.md"
    variables:
      - begrip
      - organisatorische_context
      - juridische_context
      - wettelijke_basis
      - ontologische_categorie
      - web_lookup_results
      - existing_definitions

  - name: "validation_rules"
    order: 3
    size_estimate: "4000-5000 tokens"
    file: "RULES_INJECTION.md"
    optimization:
      - "Only inject rules relevant to ontological category"
      - "Summarize low-priority rules"
      - "Use examples sparingly"

  - name: "output_format"
    order: 4
    size_estimate: "100 tokens"
    content: |
      Return JSON with: definitie, confidence, ontologische_categorie, rationale

total_size:
  current: "7250 tokens"
  target: "3000-4000 tokens"
  reduction: "45-60%"

optimization_strategies:
  - name: "Contextual Rule Filtering"
    description: "Only inject rules relevant to the ontological category"
    expected_reduction: "30%"

  - name: "Example Deduplication"
    description: "Remove duplicate examples across rules"
    expected_reduction: "15%"

  - name: "Rule Summarization"
    description: "Summarize low-priority rules instead of full text"
    expected_reduction: "20%"

  - name: "Template Caching"
    description: "Cache static parts of prompt"
    expected_reduction: "N/A (performance gain)"
EOF

# Validate prompt structure
python3 -c "import yaml; print(yaml.safe_load(open('rebuild/extracted/generation/prompts/PROMPT_STRUCTURE.yaml')))"
```

**Deliverable:**
- Complete 11-phase workflow documentation
- Prompt templates (system, context, rules, output)
- Prompt optimization strategy
- Estimated token counts

**End of Day 3 Commit:**
```bash
git add rebuild/extracted/generation/
git commit -m "feat(extraction): document 11-phase generation workflow + prompt templates"
```

---

### Day 4 - Thursday: Test Baseline Extraction (8h)

#### Morning Session (4h): Extract 42 Production Definitions

**Tasks:**
1. Export 42 production definitions from database
2. Document each definition's context and metadata
3. Create validation baseline
4. Generate test fixtures

**Commands:**
```bash
# Export definitions from current database
sqlite3 /Users/chrislehnen/Projecten/Definitie-app/data/definities.db << 'SQL' > rebuild/extracted/tests/production_definitions.json
.mode json
.output rebuild/extracted/tests/production_definitions.json
SELECT
    id,
    begrip,
    definitie,
    categorie,
    organisatorische_context,
    juridische_context,
    wettelijke_basis,
    validation_score,
    status,
    created_at
FROM definities
WHERE status IN ('established', 'review')
ORDER BY validation_score DESC
LIMIT 42;
.output stdout
SQL

# Count extracted definitions
python3 << 'PYTHON'
import json

with open('rebuild/extracted/tests/production_definitions.json', 'r') as f:
    definitions = json.load(f)

print(f"Extracted {len(definitions)} production definitions")
print("\nDefinitions by category:")

from collections import Counter
categories = Counter(d['categorie'] for d in definitions)
for cat, count in categories.most_common():
    print(f"  {cat}: {count}")

print("\nDefinitions by status:")
statuses = Counter(d['status'] for d in definitions)
for status, count in statuses.most_common():
    print(f"  {status}: {count}")

print("\nAverage validation score:")
scores = [d['validation_score'] for d in definitions if d['validation_score']]
if scores:
    avg_score = sum(scores) / len(scores)
    print(f"  {avg_score:.2f}")
PYTHON
```

**File: rebuild/extracted/tests/BASELINE_VALIDATION.yaml**
```yaml
name: "DefinitieAgent Baseline Validation Test Suite"
version: "1.0"
description: "42 production definitions used for regression testing"

metadata:
  extracted_date: "2025-10-02"
  source_database: "data/definities.db"
  total_definitions: 42
  selection_criteria:
    - status: ["established", "review"]
    - validation_score: ">= 0.7"
    - ordered_by: "validation_score DESC"

test_objectives:
  - "Ensure new system validates at least 90% of baseline definitions"
  - "Verify no regression in validation scores"
  - "Confirm generation quality matches or exceeds baseline"
  - "Validate performance (<2s per definition)"

success_criteria:
  minimum_pass_rate: 0.90  # 90% of definitions must pass
  minimum_avg_score: 0.80  # Average score must be >= 0.80
  maximum_time_per_definition: 2000  # milliseconds
  zero_critical_failures: true

test_categories:
  high_quality:
    description: "Definitions with score >= 0.9"
    count: 15
    expected_pass_rate: 1.0  # 100% must pass

  medium_quality:
    description: "Definitions with score 0.7-0.9"
    count: 20
    expected_pass_rate: 0.90  # 90% must pass

  edge_cases:
    description: "Complex or borderline definitions"
    count: 7
    expected_pass_rate: 0.70  # 70% must pass (allowed to fail some)

reporting:
  format: "junit_xml"
  output_file: "baseline_validation_report.xml"
  include_details: true
  compare_with_previous: true
```

**Script: rebuild/scripts/create_test_fixtures.py**
```python
#!/usr/bin/env python3
"""Create pytest fixtures from production definitions."""

import json
from pathlib import Path

def create_fixtures(definitions_file: Path, output_dir: Path):
    """Generate pytest fixtures for baseline testing."""

    with open(definitions_file, 'r') as f:
        definitions = json.load(f)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Group by category
    by_category = {}
    for defn in definitions:
        cat = defn['categorie']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(defn)

    # Create fixture file
    fixture_file = output_dir / 'baseline_fixtures.py'

    with open(fixture_file, 'w', encoding='utf-8') as f:
        f.write('"""Pytest fixtures for baseline validation tests."""\n\n')
        f.write('import pytest\n')
        f.write('from typing import List, Dict\n\n')

        # All definitions fixture
        f.write('@pytest.fixture\n')
        f.write('def baseline_definitions() -> List[Dict]:\n')
        f.write('    """All 42 baseline definitions."""\n')
        f.write(f'    return {json.dumps(definitions, indent=4, ensure_ascii=False)}\n\n')

        # Category fixtures
        for category, defs in by_category.items():
            fixture_name = f'baseline_definitions_{category.lower()}'
            f.write(f'@pytest.fixture\n')
            f.write(f'def {fixture_name}() -> List[Dict]:\n')
            f.write(f'    """Baseline definitions for category: {category}."""\n')
            f.write(f'    return {json.dumps(defs, indent=4, ensure_ascii=False)}\n\n')

        # High-quality subset
        high_quality = [d for d in definitions if d.get('validation_score', 0) >= 0.9]
        f.write('@pytest.fixture\n')
        f.write('def baseline_high_quality() -> List[Dict]:\n')
        f.write('    """High-quality baseline definitions (score >= 0.9)."""\n')
        f.write(f'    return {json.dumps(high_quality, indent=4, ensure_ascii=False)}\n\n')

        # Edge cases
        edge_cases = [d for d in definitions if d.get('validation_score', 1.0) < 0.8]
        f.write('@pytest.fixture\n')
        f.write('def baseline_edge_cases() -> List[Dict]:\n')
        f.write('    """Edge case baseline definitions (score < 0.8)."""\n')
        f.write(f'    return {json.dumps(edge_cases, indent=4, ensure_ascii=False)}\n\n')

    print(f"✓ Created fixture file: {fixture_file}")
    print(f"  Total definitions: {len(definitions)}")
    print(f"  Categories: {len(by_category)}")
    print(f"  High quality: {len(high_quality)}")
    print(f"  Edge cases: {len(edge_cases)}")

if __name__ == '__main__':
    definitions_file = Path('rebuild/extracted/tests/production_definitions.json')
    output_dir = Path('rebuild/extracted/tests/fixtures')

    create_fixtures(definitions_file, output_dir)
```

**Commands:**
```bash
# Create test fixtures
python rebuild/scripts/create_test_fixtures.py

# Verify fixtures
python3 << 'PYTHON'
import sys
sys.path.insert(0, 'rebuild/extracted/tests/fixtures')

from baseline_fixtures import (
    baseline_definitions,
    baseline_high_quality,
    baseline_edge_cases
)

all_defs = baseline_definitions()
high_qual = baseline_high_quality()
edge = baseline_edge_cases()

print(f"Total baseline definitions: {len(all_defs)}")
print(f"High quality (>= 0.9): {len(high_qual)}")
print(f"Edge cases (< 0.8): {len(edge)}")
PYTHON
```

---

#### Afternoon Session (4h): Document Business Logic & Patterns

**Tasks:**
1. Document hardcoded patterns (250 LOC worth)
2. Extract business rules from orchestrators (880 LOC)
3. Create business logic catalog
4. Document decision trees and workflows

**File: rebuild/extracted/docs/BUSINESS_LOGIC_CATALOG.md**
```markdown
# Business Logic Catalog

## Overview

This document catalogs all business logic extracted from the DefinitieAgent codebase.

**Total Business Logic:**
- 46 validation rules
- 11 generation phases
- 250 LOC hardcoded patterns
- 880 LOC orchestration logic

## Validation Rules (46 rules)

See `validation/` directory for complete YAML configs.

### Rule Categories

| Category | Rules | Priority Distribution | Total Test Cases |
|----------|-------|----------------------|------------------|
| ARAI | 9 | High: 6, Medium: 3 | 27+ |
| CON | 2 | High: 2 | 6+ |
| ESS | 5 | High: 4, Medium: 1 | 15+ |
| INT | 10 | High: 3, Medium: 5, Low: 2 | 30+ |
| SAM | 8 | High: 2, Medium: 4, Low: 2 | 24+ |
| STR | 9 | Medium: 7, Low: 2 | 27+ |
| VER | 3 | High: 2, Medium: 1 | 9+ |

**Total:** 46 rules, 138+ test cases

## Generation Workflow (11 phases)

See `generation/GENERATION_WORKFLOW.yaml` for complete documentation.

**Phase Summary:**
1. Context Gathering (500ms)
2. Prompt Construction (200ms)
3. AI Generation (2000ms)
4. Text Cleaning (50ms)
5. Validation (500ms)
6. Quality Gate (10ms)
7. Regeneration (2000ms if needed)
8. Example Generation (1500ms)
9. Metadata Enrichment (300ms)
10. Duplicate Detection (400ms)
11. Persistence (200ms)

**Total Time:** 5-7 seconds (target: <2 seconds)

## Hardcoded Patterns (250 LOC)

### Text Cleaning Patterns

```yaml
whitespace_normalization:
  - pattern: '\s+'
    replacement: ' '
    description: "Collapse multiple spaces"

  - pattern: '^\s+|\s+$'
    replacement: ''
    description: "Trim leading/trailing whitespace"

punctuation_fixes:
  - pattern: '\s+([.,;:!?])'
    replacement: '$1'
    description: "Remove space before punctuation"

  - pattern: '([.,;:!?])([A-Z])'
    replacement: '$1 $2'
    description: "Add space after punctuation before capital"

capitalization:
  - pattern: '^([a-z])'
    replacement: lambda m: m.group(1).upper()
    description: "Capitalize first letter"

dutch_specific:
  - pattern: '\b(een|de|het)\s+([A-Z])'
    replacement: lambda m: m.group(1) + ' ' + m.group(2).lower()
    description: "Lowercase after article unless proper noun"
```

### Validation Patterns

```yaml
verb_detection:
  patterns:
    - '\b(is|zijn|wordt|worden|kan|mag|moet|zal|heeft|hebben)\b'
  context: "ARAI-01 rule"

definition_structure:
  patterns:
    - '^(Een|De|Het)\s+\w+'  # Good: starts with article
    - '^(Is|Zijn|Wordt)'  # Bad: starts with verb
  context: "STR rules"

legal_references:
  patterns:
    - '\b(artikel|art\.|lid|onderdeel)\s+\d+'
    - '\b(wet|besluit|regeling|verordening)\b'
  context: "Legal context detection"
```

### Duplicate Detection Patterns

```yaml
similarity_thresholds:
  exact_match: 1.0
  near_duplicate: 0.95
  similar: 0.80
  related: 0.60

text_normalization:
  - lowercase all text
  - remove punctuation
  - remove stopwords (Dutch)
  - stem words (Dutch stemmer)

comparison_methods:
  - method: "exact_match"
    description: "Character-by-character comparison"

  - method: "levenshtein_distance"
    description: "Edit distance normalized by length"
    threshold: 0.95

  - method: "tfidf_cosine"
    description: "TF-IDF vectors + cosine similarity"
    threshold: 0.80

  - method: "embedding_similarity"
    description: "Semantic embeddings (optional)"
    model: "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    threshold: 0.85
```

## Orchestration Logic (880 LOC)

### Validation Orchestrator

```python
# Core validation orchestration logic
async def validate_definition(
    self,
    definition: Definition,
    context: ValidationContext
) -> ValidationResult:
    """
    Orchestrates validation of a definition.

    Logic:
    1. Pre-clean text (if cleaning service available)
    2. Build context dict from ValidationContext
    3. Call underlying validation service
    4. Ensure schema compliance
    5. Return ValidationResult

    Error handling:
    - Degraded result on exception
    - Log all errors
    - Include correlation ID
    """
    correlation_id = str(context.correlation_id or uuid.uuid4())

    try:
        # Pre-cleaning
        text = definition.definitie
        if self.cleaning_service:
            cleaned = await self.cleaning_service.clean_definition(definition)
            text = cleaned.cleaned_text

        # Build context
        context_dict = self._build_context_dict(context)

        # Validate
        result = await self.validation_service.validate_definition(
            begrip=definition.begrip,
            text=text,
            ontologische_categorie=definition.ontologische_categorie,
            context=context_dict
        )

        # Ensure compliance
        return ensure_schema_compliance(result, correlation_id)

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return create_degraded_result(error=str(e), correlation_id=correlation_id)
```

### Generation Orchestrator

```python
# Core generation orchestration logic
async def generate_definition(
    self,
    begrip: str,
    context: GenerationContext
) -> GenerationResult:
    """
    Orchestrates 11-phase definition generation.

    Phases:
    1. Gather context (web lookup, existing definitions)
    2. Build prompt (system + context + rules + hints)
    3. Call AI (GPT-4 with retry logic)
    4. Clean text (normalization, artifact removal)
    5. Validate (46 rules)
    6. Quality gate (threshold check)
    7. Regenerate if needed (feedback loop, max 2 retries)
    8. Generate examples (3 types)
    9. Enrich metadata (synonyms, related terms)
    10. Duplicate detection (similarity check)
    11. Persist (database + audit trail)

    Performance targets:
    - Total time: <2s (without optional phases)
    - AI call: <2s
    - Validation: <500ms

    Error handling:
    - Retry AI calls (max 3 attempts)
    - Degrade gracefully (skip optional phases)
    - Return partial results on failure
    """
    start_time = time.time()

    # Phase 1: Context
    context_bundle = await self._gather_context(begrip, context)

    # Phase 2: Prompt
    prompt = self._build_prompt(begrip, context_bundle)

    # Phase 3: AI Generation
    raw_definition = await self._call_ai(prompt)

    # Phase 4: Cleaning
    cleaned = self._clean_text(raw_definition)

    # Phase 5-6: Validation + Gate
    validation_result = await self._validate(cleaned, begrip, context_bundle)

    # Phase 7: Regeneration if needed
    if validation_result.score < 0.7 and self.retry_count < 2:
        return await self._regenerate_with_feedback(
            begrip, context_bundle, validation_result
        )

    # Phase 8-10: Enrich (optional)
    if validation_result.score >= 0.7:
        examples = await self._generate_examples(cleaned, begrip)
        enriched = self._enrich_metadata(cleaned, begrip, context_bundle)
        duplicate_check = await self._check_duplicates(enriched)

    # Phase 11: Persist
    saved = await self._persist(enriched)

    elapsed = time.time() - start_time

    return GenerationResult(
        definition=saved,
        validation_result=validation_result,
        elapsed_time=elapsed
    )
```

### Decision Trees

```yaml
quality_gate_decision:
  input: validation_score

  decision_tree:
    - condition: score >= 0.85
      action: auto_accept
      next_phase: example_generation

    - condition: 0.70 <= score < 0.85
      action: accept_with_review
      next_phase: example_generation
      flag: requires_review

    - condition: 0.50 <= score < 0.70
      action: retry_with_feedback
      next_phase: regeneration
      max_retries: 2

    - condition: score < 0.50
      action: reject
      next_phase: error_handling
      message: "Definition quality too low"

regeneration_strategy:
  input: failing_rules

  decision_tree:
    - condition: high_priority_failures > 0
      action: regenerate_with_critical_feedback
      prompt_injection: critical_rules_only

    - condition: medium_priority_failures > 3
      action: regenerate_with_focused_feedback
      prompt_injection: failing_rules_summary

    - condition: low_priority_failures_only
      action: accept_with_warnings
      next_phase: example_generation
```

## Business Rules

### Rule: Minimum Validation Score

```yaml
rule_id: "BR-001"
name: "Minimum Validation Score for Acceptance"
description: "Definition must meet minimum score threshold to be accepted"

logic:
  auto_accept_threshold: 0.85
  review_threshold: 0.70
  retry_threshold: 0.50
  auto_reject_threshold: 0.50

weights:
  high_priority_rule: 1.0
  medium_priority_rule: 0.7
  low_priority_rule: 0.4

calculation: |
  overall_score = (
    sum(rule.score * rule.weight for rule in all_rules) /
    sum(rule.weight for rule in all_rules)
  )
```

### Rule: Duplicate Detection

```yaml
rule_id: "BR-002"
name: "Duplicate Definition Prevention"
description: "Prevent creation of duplicate or near-duplicate definitions"

logic:
  exact_duplicate_threshold: 1.0  # Block
  near_duplicate_threshold: 0.95  # Warn + require confirmation
  similar_threshold: 0.80  # Show as suggestion

actions:
  exact_match:
    action: "block"
    message: "Exact duplicate found for begrip '{begrip}'"

  near_duplicate:
    action: "warn"
    message: "Very similar definition found (similarity: {score})"
    require_confirmation: true

  similar:
    action: "suggest"
    message: "Similar definitions found"
    show_in_ui: true
```

### Rule: Context Requirement

```yaml
rule_id: "BR-003"
name: "Context Required for Generation"
description: "Certain ontological categories require specific context"

requirements:
  ENT:  # Entiteit
    required: []
    optional: [organisatorische_context, juridische_context]

  ACT:  # Activiteit
    required: []
    optional: [organisatorische_context, juridische_context, wettelijke_basis]

  AUT:  # Autorisatie
    required: [wettelijke_basis]
    optional: [organisatorische_context, juridische_context]

  REL:  # Relatie
    required: []
    optional: [organisatorische_context]
```

## Performance Budgets

```yaml
performance_budgets:
  phase_1_context_gathering:
    target: 500ms
    maximum: 1000ms

  phase_2_prompt_construction:
    target: 200ms
    maximum: 500ms

  phase_3_ai_generation:
    target: 2000ms
    maximum: 5000ms

  phase_5_validation:
    target: 500ms
    maximum: 1000ms

  phase_8_examples:
    target: 1500ms
    maximum: 3000ms

  total_workflow:
    target: 2000ms
    maximum: 5000ms
    degraded_mode: 10000ms
```

## Data Constraints

```yaml
database_constraints:
  definitie:
    max_length: 1000
    min_length: 20
    allowed_characters: "Dutch UTF-8 + punctuation"

  begrip:
    max_length: 255
    min_length: 2
    unique: false  # Multiple definitions per begrip allowed

  validation_score:
    min: 0.0
    max: 1.0
    decimal_places: 2

  status:
    allowed_values: [draft, review, established, archived]
    default: draft
    transitions:
      draft: [review, archived]
      review: [established, draft, archived]
      established: [archived, review]
      archived: []  # Terminal state
```
