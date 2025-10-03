#!/bin/bash
# REBUILD_PACKAGE File Extraction Guide
# Automatically extract templated files from documentation
# Generated: 2025-10-02

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=================================================="
echo "REBUILD_PACKAGE File Extraction Tool"
echo "=================================================="
echo ""

# Set base directory
BASE_DIR="/Users/chrislehnen/Projecten/Definitie-app"
PACKAGE_DIR="$BASE_DIR/REBUILD_PACKAGE"

# Check if REBUILD_PACKAGE exists
if [ ! -d "$PACKAGE_DIR" ]; then
    echo -e "${RED}ERROR: REBUILD_PACKAGE directory not found at $PACKAGE_DIR${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Found REBUILD_PACKAGE at $PACKAGE_DIR${NC}"
echo ""

# ============================================
# PHASE 1: P0 - Week 1 Day 1 Blockers
# ============================================

echo "=================================================="
echo "PHASE 1: Creating P0 Items (Week 1 Blockers)"
echo "=================================================="
echo ""

# 1. Create extract_rule.py
echo -e "${YELLOW}[1/7] Creating rebuild/scripts/extract_rule.py...${NC}"
mkdir -p "$BASE_DIR/rebuild/scripts"

cat > "$BASE_DIR/rebuild/scripts/extract_rule.py" << 'PYTHON_SCRIPT'
#!/usr/bin/env python3
"""Extract validation rule from Python file to YAML config."""

import ast
import re
import yaml
from pathlib import Path
import sys

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
PYTHON_SCRIPT

chmod +x "$BASE_DIR/rebuild/scripts/extract_rule.py"
echo -e "${GREEN}✓ Created extract_rule.py${NC}"
echo ""

# 2. Create config directory structure
echo -e "${YELLOW}[2/7] Creating config/validation_rules/ structure...${NC}"
mkdir -p "$BASE_DIR/config/validation_rules"/{arai,con,ess,int,sam,str,ver,dup}
echo -e "${GREEN}✓ Created directory structure${NC}"
echo ""

# 3. Create ARAI-01.yaml example
echo -e "${YELLOW}[3/7] Creating config/validation_rules/arai/ARAI-01.yaml...${NC}"

cat > "$BASE_DIR/config/validation_rules/arai/ARAI-01.yaml" << 'YAML_RULE'
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

performance:
  max_execution_time_ms: 50
  complexity: "O(n)"
YAML_RULE

echo -e "${GREEN}✓ Created ARAI-01.yaml example${NC}"
echo ""

# 4. Create prompt templates
echo -e "${YELLOW}[4/7] Creating prompt templates...${NC}"
mkdir -p "$BASE_DIR/rebuild/extracted/generation/prompts"

# 4a. SYSTEM_PROMPT.md
cat > "$BASE_DIR/rebuild/extracted/generation/prompts/SYSTEM_PROMPT.md" << 'PROMPT1'
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
PROMPT1

# 4b. CONTEXT_TEMPLATE.md
cat > "$BASE_DIR/rebuild/extracted/generation/prompts/CONTEXT_TEMPLATE.md" << 'PROMPT2'
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
PROMPT2

# 4c. RULES_INJECTION.md
cat > "$BASE_DIR/rebuild/extracted/generation/prompts/RULES_INJECTION.md" << 'PROMPT3'
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
PROMPT3

echo -e "${GREEN}✓ Created 3 prompt templates${NC}"
echo ""

# 5. Create create_test_fixtures.py
echo -e "${YELLOW}[5/7] Creating rebuild/scripts/create_test_fixtures.py...${NC}"

cat > "$BASE_DIR/rebuild/scripts/create_test_fixtures.py" << 'PYTHON_FIXTURES'
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
PYTHON_FIXTURES

chmod +x "$BASE_DIR/rebuild/scripts/create_test_fixtures.py"
echo -e "${GREEN}✓ Created create_test_fixtures.py${NC}"
echo ""

# 6. Create validate_week1.sh
echo -e "${YELLOW}[6/7] Creating scripts/validate_week1.sh...${NC}"
mkdir -p "$BASE_DIR/scripts"

cat > "$BASE_DIR/scripts/validate_week1.sh" << 'VALIDATE_SCRIPT'
#!/bin/bash
echo "=== Week 1 Validation ==="

# Check YAML files
echo "Checking YAML configs..."
yaml_count=$(find config/validation_rules -name "*.yaml" 2>/dev/null | wc -l)
echo "  Found: $yaml_count YAML files"
echo "  Expected: 46"
if [ "$yaml_count" -ge 46 ]; then
    echo "  ✓ PASS"
else
    echo "  ✗ FAIL"
fi

# Check workflows
echo ""
echo "Checking workflows..."
workflow_count=$(ls docs/business-logic/workflows/*.md 2>/dev/null | wc -l)
echo "  Found: $workflow_count workflows"
echo "  Expected: 3+"
if [ "$workflow_count" -ge 3 ]; then
    echo "  ✓ PASS"
else
    echo "  ✗ FAIL"
fi

# Check baseline
echo ""
echo "Checking baseline..."
if [ -f "docs/business-logic/baseline/baseline_42_definitions.json" ]; then
    echo "  ✓ PASS - Baseline file exists"
else
    echo "  ✗ FAIL - Baseline file missing"
fi

echo ""
echo "=== Validation Complete ==="
VALIDATE_SCRIPT

chmod +x "$BASE_DIR/scripts/validate_week1.sh"
echo -e "${GREEN}✓ Created validate_week1.sh${NC}"
echo ""

# 7. Create .env.example
echo -e "${YELLOW}[7/7] Creating .env.example...${NC}"

cat > "$BASE_DIR/.env.example" << 'ENV_EXAMPLE'
# ==============================================
# DefinitieAgent v2.0 Environment Configuration
# ==============================================

# ----------------------------------------------
# Environment
# ----------------------------------------------
ENVIRONMENT=development  # development, staging, production
DEBUG=false
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# ----------------------------------------------
# API Configuration
# ----------------------------------------------
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_RELOAD=true  # Auto-reload on code changes (dev only)

# ----------------------------------------------
# OpenAI Configuration
# ----------------------------------------------
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.3
OPENAI_MAX_TOKENS=500
OPENAI_TIMEOUT=30  # Seconds

# ----------------------------------------------
# Database (SQLite for simplicity)
# ----------------------------------------------
DATABASE_URL=sqlite:///./data/definities.db

# ----------------------------------------------
# Validation Configuration
# ----------------------------------------------
VALIDATION_RULES_DIR=config/validation_rules
VALIDATION_AUTO_ACCEPT_THRESHOLD=0.85
VALIDATION_REVIEW_THRESHOLD=0.70
VALIDATION_REJECT_THRESHOLD=0.50

# ----------------------------------------------
# Generation Configuration
# ----------------------------------------------
GENERATION_MAX_RETRIES=2
GENERATION_TIMEOUT=10  # Seconds
GENERATION_ENABLE_WEB_LOOKUP=true

# ----------------------------------------------
# Logging
# ----------------------------------------------
LOG_FILE_PATH=logs/app.log
LOG_FILE_MAX_SIZE=10485760  # 10MB
LOG_FILE_BACKUP_COUNT=10
ENV_EXAMPLE

echo -e "${GREEN}✓ Created .env.example${NC}"
echo ""

# ============================================
# SUMMARY
# ============================================

echo "=================================================="
echo "EXTRACTION COMPLETE!"
echo "=================================================="
echo ""
echo -e "${GREEN}✓ Created 7 critical files (P0):${NC}"
echo "  1. rebuild/scripts/extract_rule.py"
echo "  2. config/validation_rules/ (structure)"
echo "  3. config/validation_rules/arai/ARAI-01.yaml"
echo "  4. rebuild/extracted/generation/prompts/SYSTEM_PROMPT.md"
echo "  5. rebuild/extracted/generation/prompts/CONTEXT_TEMPLATE.md"
echo "  6. rebuild/extracted/generation/prompts/RULES_INJECTION.md"
echo "  7. rebuild/scripts/create_test_fixtures.py"
echo "  8. scripts/validate_week1.sh"
echo "  9. .env.example"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Test extraction script:"
echo "     cd $BASE_DIR"
echo "     python rebuild/scripts/extract_rule.py src/toetsregels/regels/ARAI-02.py"
echo ""
echo "  2. Extract all ARAI rules:"
echo "     for rule in src/toetsregels/regels/ARAI-*.py; do"
echo "       python rebuild/scripts/extract_rule.py \"\$rule\""
echo "     done"
echo ""
echo "  3. Start Week 1 Day 1 execution!"
echo ""
echo -e "${GREEN}Week 1 is now UNBLOCKED! ✓${NC}"
echo ""
