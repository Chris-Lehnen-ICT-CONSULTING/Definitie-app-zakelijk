# REBUILD_PACKAGE - Preparation Checklist

**Purpose:** Fix critical gaps before starting Week 1 Day 1
**Duration:** 3-5 days
**Status:** 🔴 Not Started

---

## Overview

This checklist covers the 3-5 days of preparation work needed BEFORE Week 1 Day 1 can begin.

**Why needed?** Package has great docs but missing artifacts (scripts, configs, baseline data).

---

## Day -3: Baseline & Workspace Setup

### Morning (4h): Export Baseline Definitions

**Goal:** Get whatever baseline data exists from current database

- [ ] **Check actual definition count**
  ```bash
  cd /Users/chrislehnen/Projecten/Definitie-app
  sqlite3 data/definities.db "SELECT COUNT(*) FROM definities WHERE status IN ('established', 'review');"
  # Current result: 1 (not 42 as plan assumes!)
  ```

- [ ] **Export ALL available definitions**
  ```bash
  mkdir -p REBUILD_PACKAGE/rebuild/extracted/tests/

  sqlite3 data/definities.db << 'SQL' > REBUILD_PACKAGE/rebuild/extracted/tests/baseline_definitions.json
  .mode json
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
    created_at,
    updated_at
  FROM definities
  WHERE status NOT IN ('deleted', 'archived')
  ORDER BY validation_score DESC;
  SQL
  ```

- [ ] **Analyze baseline quality**
  ```bash
  python3 << 'PYTHON'
  import json

  with open('REBUILD_PACKAGE/rebuild/extracted/tests/baseline_definitions.json', 'r') as f:
      definitions = json.load(f)

  print(f"Total definitions: {len(definitions)}")
  print(f"\nBy category:")
  from collections import Counter
  cats = Counter(d['categorie'] for d in definitions)
  for cat, count in cats.most_common():
      print(f"  {cat}: {count}")

  print(f"\nBy status:")
  statuses = Counter(d['status'] for d in definitions)
  for status, count in statuses.most_common():
      print(f"  {status}: {count}")

  scores = [d['validation_score'] for d in definitions if d['validation_score']]
  if scores:
      print(f"\nValidation scores:")
      print(f"  Average: {sum(scores)/len(scores):.2f}")
      print(f"  Min: {min(scores):.2f}")
      print(f"  Max: {max(scores):.2f}")
  PYTHON
  ```

- [ ] **Document actual baseline count**
  ```bash
  # Update this in plan:
  echo "ACTUAL BASELINE: X definitions (not 42)" >> REBUILD_PACKAGE/BASELINE_README.md
  echo "Adjust Week 1 expectations accordingly" >> REBUILD_PACKAGE/BASELINE_README.md
  ```

- [ ] **Decision: Generate synthetic data?**
  - If baseline < 10 definitions → Consider generating test data
  - If baseline 10-20 → Acceptable for testing
  - If baseline > 20 → Good enough

**Deliverable:** `REBUILD_PACKAGE/rebuild/extracted/tests/baseline_definitions.json`

---

### Afternoon (4h): Create Workspace Structure

**Goal:** Set up all directories needed for Week 1

- [ ] **Create extraction workspace**
  ```bash
  cd REBUILD_PACKAGE

  # Validation extraction
  mkdir -p rebuild/extracted/validation/{arai,con,ess,int,sam,str,ver,dup}

  # Generation extraction
  mkdir -p rebuild/extracted/generation/{phases,prompts,workflows}

  # Test data
  mkdir -p rebuild/extracted/tests/{fixtures,baseline}

  # Documentation
  mkdir -p rebuild/extracted/docs

  # Scripts
  mkdir -p rebuild/scripts

  # Logs
  mkdir -p logs/daily
  ```

- [ ] **Create config directories**
  ```bash
  mkdir -p config/validation_rules/{arai,con,ess,int,sam,str,ver,dup}
  mkdir -p config/prompts
  mkdir -p config/settings
  ```

- [ ] **Verify structure**
  ```bash
  tree -L 3 rebuild/
  tree -L 2 config/
  tree -L 1 logs/
  ```

- [ ] **Create .gitkeep files**
  ```bash
  find rebuild -type d -empty -exec touch {}/.gitkeep \;
  find config -type d -empty -exec touch {}/.gitkeep \;
  ```

- [ ] **Initialize progress tracking**
  ```bash
  cat > PROGRESS.md << 'EOF'
  # Rebuild Progress Tracker

  ## Preparation Phase (Days -3 to 0)
  - [ ] Day -3: Baseline export + workspace setup
  - [ ] Day -2: Extraction script + config templates
  - [ ] Day -1: Generation artifacts + validation
  - [ ] Day 0: Testing + Go/No-Go decision

  ## Week 1: Business Logic Extraction
  - [ ] Day 1: ARAI rules extraction
  - [ ] Day 2: All 46 rules extraction
  - [ ] Day 3: Generation workflow
  - [ ] Day 4: Baseline testing
  - [ ] Day 5: Week 1 gate review
  EOF
  ```

**Deliverable:** Complete workspace structure

---

## Day -2: Scripts & Config Templates

### Morning (4h): Extraction Script

**Goal:** Create working script to extract validation rules

- [ ] **Create extraction script skeleton**
  ```bash
  cat > rebuild/scripts/extract_rule.py << 'PYTHON'
  #!/usr/bin/env python3
  """Extract validation rule from Python file to YAML config."""

  import ast
  import re
  import yaml
  from pathlib import Path
  from typing import Dict, List

  def extract_rule(rule_file: Path) -> Dict:
      """Extract rule metadata from Python validation file."""

      with open(rule_file, 'r', encoding='utf-8') as f:
          content = f.read()

      # Parse Python AST
      try:
          tree = ast.parse(content)
      except SyntaxError as e:
          print(f"Error parsing {rule_file}: {e}")
          return None

      # Extract rule ID from filename (e.g., ARAI-01.py -> ARAI-01)
      rule_id = rule_file.stem
      category = rule_id.split('-')[0]

      # Find validator class
      validator_class = None
      for node in ast.walk(tree):
          if isinstance(node, ast.ClassDef) and 'Validator' in node.name:
              validator_class = node
              break

      if not validator_class:
          print(f"No validator class in {rule_file}")
          return None

      # Extract docstring
      docstring = ast.get_docstring(validator_class) or ""
      lines = docstring.split('\n')
      naam = lines[0] if lines else rule_id
      uitleg = docstring if len(docstring) > 0 else "To be documented"

      # Build config
      config = {
          'id': rule_id,
          'category': category,
          'priority': 'medium',  # Manual review needed
          'enabled': True,

          'metadata': {
              'naam': naam.strip(),
              'uitleg': uitleg.strip(),
              'version': '1.0',
              'last_updated': '2025-10-02',
              'code_reference': str(rule_file)
          },

          'implementation': {
              'type': 'regex',  # Default - manual review needed
              'patterns': [],  # Manual extraction needed
              'logic_description': 'See code_reference for implementation'
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
              'good': [],  # Manual entry needed
              'bad': []    # Manual entry needed
          },

          'generation_hints': [],  # Manual entry needed

          'test_cases': []  # Manual entry needed
      }

      return config

  def main():
      import sys

      if len(sys.argv) != 2:
          print("Usage: extract_rule.py <rule_file.py>")
          print("Example: extract_rule.py src/toetsregels/regels/ARAI-01.py")
          sys.exit(1)

      rule_file = Path(sys.argv[1])

      if not rule_file.exists():
          print(f"File not found: {rule_file}")
          sys.exit(1)

      config = extract_rule(rule_file)

      if not config:
          print("Failed to extract rule")
          sys.exit(1)

      # Determine output location
      category = config['category'].lower()
      output_dir = Path('REBUILD_PACKAGE/config/validation_rules') / category
      output_dir.mkdir(parents=True, exist_ok=True)

      output_file = output_dir / f"{config['id']}.yaml"

      # Write YAML
      with open(output_file, 'w', encoding='utf-8') as f:
          yaml.dump(config, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

      print(f"✓ Extracted {config['id']} → {output_file}")
      print(f"  Name: {config['metadata']['naam']}")
      print(f"  Category: {config['category']}")
      print(f"  ⚠️  Manual review needed: patterns, examples, test cases")

  if __name__ == '__main__':
      main()
  PYTHON

  chmod +x rebuild/scripts/extract_rule.py
  ```

- [ ] **Test extraction script**
  ```bash
  cd /Users/chrislehnen/Projecten/Definitie-app

  # Test on one rule
  python3 REBUILD_PACKAGE/rebuild/scripts/extract_rule.py src/toetsregels/regels/ARAI-01.py

  # Verify output
  cat REBUILD_PACKAGE/config/validation_rules/arai/ARAI-01.yaml
  ```

- [ ] **Extract 2-3 rules as proof of concept**
  ```bash
  python3 REBUILD_PACKAGE/rebuild/scripts/extract_rule.py src/toetsregels/regels/ARAI-02.py
  python3 REBUILD_PACKAGE/rebuild/scripts/extract_rule.py src/toetsregels/regels/CON-01.py
  ```

**Deliverable:** Working extraction script + 3 sample YAMLs

---

### Afternoon (4h): Config Templates

**Goal:** Create templates for all config types

- [ ] **Validation rule template** (already have via script)

- [ ] **Create ontological patterns config**
  ```bash
  cat > config/ontological_patterns.yaml << 'YAML'
  # Ontological Category Detection Patterns
  # Extracted from: src/ui/tabbed_interface.py L354-418

  version: "1.0"
  last_updated: "2025-10-02"

  patterns:
    proces:
      suffixes:
        - "atie"
        - "eren"
        - "ing"
      examples:
        - "verificatie"
        - "registratie"
        - "autoriseren"

    type:
      keywords:
        - "bewijs"
        - "document"
        - "middel"
      examples:
        - "identiteitsbewijs"
        - "machtiging"

    resultaat:
      keywords:
        - "besluit"
        - "uitslag"
        - "rapport"
      examples:
        - "vergunning"
        - "beschikking"

    exemplaar:
      keywords:
        - "specifiek"
        - "individueel"
      examples:
        - "persoon"
        - "instantie"

  fallback_logic:
    - level_1: "Check suffix patterns"
    - level_2: "Check keyword presence"
    - level_3: "Default to 'type'"
  YAML
  ```

- [ ] **Create validation thresholds config**
  ```bash
  cat > config/validation_thresholds.yaml << 'YAML'
  # Validation Thresholds and Weights

  version: "1.0"

  quality_gates:
    auto_accept: 0.85
    review_required: 0.70
    retry_threshold: 0.50
    auto_reject: 0.50

  rule_weights:
    high_priority: 1.0
    medium_priority: 0.7
    low_priority: 0.4

  length_constraints:
    min_chars: 50
    max_chars: 500
    optimal_min: 100
    optimal_max: 300

  sentence_constraints:
    max_sentences: 3
    recommended: 2

  confidence_levels:
    high: 0.8
    medium: 0.5
    low: 0.3
  YAML
  ```

- [ ] **Create duplicate detection config**
  ```bash
  cat > config/duplicate_detection.yaml << 'YAML'
  # Duplicate Detection Configuration

  version: "1.0"

  thresholds:
    exact_match: 1.0      # Block - exact duplicate
    near_duplicate: 0.95  # Warn - very similar
    similar: 0.80         # Show - related
    jaccard_similarity: 0.70  # Hardcoded in current system

  methods:
    - name: "exact_match"
      enabled: true
      weight: 1.0

    - name: "levenshtein"
      enabled: true
      threshold: 0.95
      weight: 0.8

    - name: "jaccard"
      enabled: true
      threshold: 0.70
      weight: 0.9

    - name: "tfidf_cosine"
      enabled: false  # Optional
      threshold: 0.80
      weight: 0.7

  text_normalization:
    lowercase: true
    remove_punctuation: true
    remove_stopwords: true
    stemming: false  # Dutch stemmer not configured yet
  YAML
  ```

- [ ] **Create remaining config templates**
  ```bash
  # voorbeelden_type_mapping.yaml
  # workflow_transitions.yaml
  # ui_thresholds.yaml
  # (Can be minimal placeholders for now)
  ```

**Deliverable:** 7 config template files

---

## Day -1: Generation Artifacts & Validation

### Morning (4h): Generation Workflow Files

**Goal:** Pre-populate generation workflow documentation

- [ ] **Copy workflow from execution plan**
  ```bash
  # Extract GENERATION_WORKFLOW.yaml from docs/REBUILD_EXECUTION_PLAN.md lines 636-945
  # and save to rebuild/extracted/generation/GENERATION_WORKFLOW.yaml
  ```

- [ ] **Create prompt templates**
  ```bash
  # Extract from docs/REBUILD_EXECUTION_PLAN.md:
  # - Lines 983-1043 → rebuild/extracted/generation/prompts/SYSTEM_PROMPT.md
  # - Lines 1045-1098 → rebuild/extracted/generation/prompts/CONTEXT_TEMPLATE.md
  # - Lines 1100-1137 → rebuild/extracted/generation/prompts/RULES_INJECTION.md
  ```

- [ ] **Document prompt structure**
  ```bash
  # Extract lines 1147-1207 from execution plan
  # → rebuild/extracted/generation/prompts/PROMPT_STRUCTURE.yaml
  ```

**Deliverable:** 4 generation artifact files

---

### Afternoon (4h): Baseline Validation

**Goal:** Capture OLD system validation results

- [ ] **Create baseline validation script**
  ```bash
  cat > rebuild/scripts/capture_old_validation.py << 'PYTHON'
  #!/usr/bin/env python3
  """Capture validation results from OLD system for baseline comparison."""

  import json
  import sys
  from pathlib import Path

  # Add current src to path
  sys.path.insert(0, '/Users/chrislehnen/Projecten/Definitie-app/src')

  from services.validation.modular_validation_service import ModularValidationService

  def main():
      # Load baseline definitions
      baseline_file = Path('REBUILD_PACKAGE/rebuild/extracted/tests/baseline_definitions.json')

      with open(baseline_file, 'r') as f:
          definitions = json.load(f)

      print(f"Validating {len(definitions)} baseline definitions...")

      # Initialize validation service
      # (May need to adjust imports based on actual codebase structure)
      validator = ModularValidationService()

      results = []

      for defn in definitions:
          print(f"Validating: {defn['begrip']}")

          try:
              # Run validation
              result = validator.validate_definition(
                  begrip=defn['begrip'],
                  text=defn['definitie'],
                  ontologische_categorie=defn.get('categorie'),
                  context={}
              )

              results.append({
                  'id': defn['id'],
                  'begrip': defn['begrip'],
                  'validation_score': result.overall_score,
                  'passed': result.passed,
                  'failed_rules': [r.rule_id for r in result.failures],
                  'warnings': [r.rule_id for r in result.warnings]
              })

          except Exception as e:
              print(f"Error validating {defn['begrip']}: {e}")
              results.append({
                  'id': defn['id'],
                  'begrip': defn['begrip'],
                  'error': str(e)
              })

      # Save results
      output_file = Path('REBUILD_PACKAGE/rebuild/extracted/tests/old_validation_results.json')
      with open(output_file, 'w') as f:
          json.dump(results, f, indent=2, ensure_ascii=False)

      print(f"\n✓ Saved validation results to {output_file}")

      # Summary
      passed = sum(1 for r in results if r.get('passed'))
      print(f"\nSummary:")
      print(f"  Total: {len(results)}")
      print(f"  Passed: {passed}")
      print(f"  Failed: {len(results) - passed}")

  if __name__ == '__main__':
      main()
  PYTHON

  chmod +x rebuild/scripts/capture_old_validation.py
  ```

- [ ] **Run baseline validation capture**
  ```bash
  cd /Users/chrislehnen/Projecten/Definitie-app
  python3 REBUILD_PACKAGE/rebuild/scripts/capture_old_validation.py
  ```

- [ ] **Review validation results**
  ```bash
  cat REBUILD_PACKAGE/rebuild/extracted/tests/old_validation_results.json | jq '.[] | {begrip, passed, score: .validation_score}'
  ```

**Deliverable:** `old_validation_results.json` for comparison

---

## Day 0: Testing & Go/No-Go Decision

### Morning (3h): Validation

- [ ] **Test extraction script on 5 more rules**
  ```bash
  for rule in ARAI-03 ARAI-04 ESS-01 STR-01 VER-01; do
      python3 REBUILD_PACKAGE/rebuild/scripts/extract_rule.py \
          src/toetsregels/regels/${rule}.py
  done
  ```

- [ ] **Verify YAML syntax**
  ```bash
  for yaml in REBUILD_PACKAGE/config/validation_rules/*/*.yaml; do
      python3 -c "import yaml; yaml.safe_load(open('$yaml'))" && echo "✓ $yaml" || echo "✗ $yaml"
  done
  ```

- [ ] **Check workspace structure**
  ```bash
  tree -L 3 REBUILD_PACKAGE/rebuild/
  tree -L 2 REBUILD_PACKAGE/config/
  ```

- [ ] **Validate baseline data quality**
  ```bash
  python3 << 'PYTHON'
  import json

  # Check baseline
  with open('REBUILD_PACKAGE/rebuild/extracted/tests/baseline_definitions.json') as f:
      baseline = json.load(f)

  print(f"Baseline definitions: {len(baseline)}")
  print(f"Status: {'✓ OK' if len(baseline) >= 5 else '✗ TOO FEW'}")

  # Check validation results
  with open('REBUILD_PACKAGE/rebuild/extracted/tests/old_validation_results.json') as f:
      results = json.load(f)

  print(f"Validation results: {len(results)}")
  print(f"Match: {'✓ OK' if len(results) == len(baseline) else '✗ MISMATCH'}")
  PYTHON
  ```

---

### Afternoon (2h): Go/No-Go Decision

- [ ] **Review checklist completion**

**Minimum GO Criteria:**
- [ ] Baseline exported (any count ≥ 5)
- [ ] Extraction script works (tested on 5+ rules)
- [ ] Config templates created (7 files)
- [ ] Workspace structure complete
- [ ] Old validation results captured
- [ ] Progress tracking initialized

**Current Status:**
- Total criteria: 6
- Completed: ___ / 6
- **Decision: GO / NO-GO?**

---

### Decision Options

#### ✅ GO (All 6 criteria met)
**Action:**
- Start Week 1 Day 1 tomorrow
- Follow REBUILD_EXECUTION_PLAN.md as written
- Adjust baseline expectations (use actual count, not 42)

#### ⚠️ PARTIAL GO (4-5 criteria met)
**Action:**
- Start Week 1 with known gaps
- Extend Week 1 by 1-2 days
- Complete missing prep work in parallel

#### 🔴 NO-GO (< 4 criteria met)
**Action:**
- Continue preparation for 1-2 more days
- Reschedule Week 1 start
- Identify and fix blockers

---

## Final Deliverables Checklist

Before declaring "READY FOR WEEK 1":

### Data
- [ ] `rebuild/extracted/tests/baseline_definitions.json` (any count)
- [ ] `rebuild/extracted/tests/old_validation_results.json`

### Scripts
- [ ] `rebuild/scripts/extract_rule.py` (working)
- [ ] `rebuild/scripts/capture_old_validation.py` (executed)

### Configs
- [ ] `config/validation_rules/{arai,con,ess,int,sam,str,ver}/` (5-10 sample YAMLs)
- [ ] `config/ontological_patterns.yaml`
- [ ] `config/validation_thresholds.yaml`
- [ ] `config/duplicate_detection.yaml`

### Generation Artifacts
- [ ] `rebuild/extracted/generation/GENERATION_WORKFLOW.yaml`
- [ ] `rebuild/extracted/generation/prompts/SYSTEM_PROMPT.md`
- [ ] `rebuild/extracted/generation/prompts/CONTEXT_TEMPLATE.md`
- [ ] `rebuild/extracted/generation/prompts/RULES_INJECTION.md`

### Workspace
- [ ] All directories created with proper structure
- [ ] `.gitkeep` files in empty dirs
- [ ] `PROGRESS.md` initialized

### Documentation
- [ ] `BASELINE_README.md` with actual counts
- [ ] Updated expectations documented
- [ ] Gaps acknowledged and tracked

---

## Summary

**Days:** -3, -2, -1, 0 (4 days total, can compress to 3)
**Effort:** 30-40 hours
**Outcome:** Ready to execute Week 1 Day 1 with confidence

**Key Success Factor:** Realistic expectations based on actual baseline data, not assumed 42 definitions.

---

**Last Updated:** 2025-10-02
**Status:** Template - needs execution
**Next Action:** Begin Day -3 checklist
