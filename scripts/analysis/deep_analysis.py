#!/usr/bin/env python3
"""Deep analysis of specific requirement issues."""

import os
import re
from pathlib import Path
from collections import defaultdict
import yaml

def check_epic_formatting():
    """Check if epic references have formatting issues."""
    req_dir = Path('/Users/chrislehnen/Projecten/Definitie-app/docs/requirements')
    epic_issues = defaultdict(list)

    # Check different epic formats
    for req_file in sorted(req_dir.glob('REQ-*.md')):
        if req_file.name == 'REQ-000.md':
            continue

        with open(req_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for different epic formats
        if 'EPIC-2' in content and 'EPIC-002' not in content:
            epic_issues['wrong_format'].append(req_file.name)
        if 'EPIC-02' in content:
            epic_issues['two_digit'].append(req_file.name)
        if 'Epic 2' in content:
            epic_issues['text_format'].append(req_file.name)

    return epic_issues

def find_conflicting_requirements():
    """Find requirements that explicitly conflict with each other."""
    req_dir = Path('/Users/chrislehnen/Projecten/Definitie-app/docs/requirements')
    conflicts = defaultdict(list)

    for req_file in sorted(req_dir.glob('REQ-*.md')):
        if req_file.name == 'REQ-000.md':
            continue

        with open(req_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Look for conflict sections
        if 'Conflicten' in content:
            conflict_match = re.search(r'## Conflicten.*?\n(.*?)(?=##|\Z)', content, re.DOTALL)
            if conflict_match:
                conflict_text = conflict_match.group(1).strip()
                if conflict_text and 'Geen conflicten' not in conflict_text and 'geen' not in conflict_text.lower():
                    # Extract REQ references
                    req_refs = re.findall(r'REQ-\d{3}', conflict_text)
                    if req_refs:
                        conflicts[req_file.name] = {
                            'conflicts_with': req_refs,
                            'description': conflict_text[:200]
                        }

    return conflicts

def check_validation_rules_coverage():
    """Check if all 45 validation rules are covered in requirements."""
    # List of all validation rule categories
    categories = ['ARAI', 'CON', 'ESS', 'INT', 'SAM', 'STR', 'VER']

    # Read validation requirements (REQ-023 to REQ-037)
    covered_rules = set()
    req_dir = Path('/Users/chrislehnen/Projecten/Definitie-app/docs/requirements')

    for i in range(23, 38):  # REQ-023 to REQ-037
        req_file = req_dir / f'REQ-{i:03d}.md'
        if req_file.exists():
            with open(req_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Look for rule references
            for cat in categories:
                if cat in content:
                    covered_rules.add(cat)

            # Look for specific rule numbers
            rule_refs = re.findall(r'regel[_ ]?(\d+)', content, re.IGNORECASE)
            covered_rules.update(rule_refs)

    # Check actual validation rules directory
    rules_dir = Path('/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels')
    actual_rules = []

    if rules_dir.exists():
        for rule_file in rules_dir.glob('*.py'):
            if rule_file.name != '__init__.py':
                actual_rules.append(rule_file.stem)

    return {
        'categories_covered': list(covered_rules),
        'total_actual_rules': len(actual_rules),
        'actual_rule_files': actual_rules[:10],  # Show first 10
        'validation_req_count': 15  # REQ-023 to REQ-037
    }

def check_status_implementation_mismatch():
    """Check for requirements marked as Done but not actually implemented."""
    req_dir = Path('/Users/chrislehnen/Projecten/Definitie-app/docs/requirements')
    base_path = Path('/Users/chrislehnen/Projecten/Definitie-app')

    mismatches = []

    for req_file in sorted(req_dir.glob('REQ-*.md')):
        if req_file.name == 'REQ-000.md':
            continue

        with open(req_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse frontmatter
        frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if frontmatter_match:
            try:
                frontmatter = yaml.safe_load(frontmatter_match.group(1))

                # Check if status is Done but source files don't exist
                if frontmatter.get('status') == 'Done':
                    sources = frontmatter.get('sources', [])
                    missing_sources = []

                    for source in sources:
                        source_path = base_path / source['path']
                        if not source_path.exists():
                            missing_sources.append(source['path'])

                    if missing_sources:
                        mismatches.append({
                            'req_id': frontmatter.get('id'),
                            'title': frontmatter.get('title'),
                            'missing_files': missing_sources
                        })
            except:
                pass

    return mismatches

def analyze_requirement_categories():
    """Analyze requirement distribution by category."""
    req_dir = Path('/Users/chrislehnen/Projecten/Definitie-app/docs/requirements')
    categories = defaultdict(list)

    category_patterns = {
        'Security': ['auth', 'security', 'xss', 'sql injection', 'encryption', 'owasp'],
        'Performance': ['response time', 'performance', 'cache', 'optimization', 'speed'],
        'Validation': ['validat', 'toets', 'regel', 'check'],
        'UI/UX': ['ui', 'interface', 'gebruiker', 'frontend', 'streamlit'],
        'Integration': ['api', 'integration', 'external', 'wikipedia', 'sru'],
        'Data': ['database', 'storage', 'export', 'import', 'backup'],
        'Domain': ['juridisch', 'definitie', 'nederlands', 'astra', 'nora'],
        'Architecture': ['architect', 'design', 'pattern', 'structure']
    }

    for req_file in sorted(req_dir.glob('REQ-*.md')):
        if req_file.name == 'REQ-000.md':
            continue

        with open(req_file, 'r', encoding='utf-8') as f:
            content = f.read().lower()

        req_id = req_file.stem

        # Categorize based on content
        for category, keywords in category_patterns.items():
            if any(keyword in content for keyword in keywords):
                categories[category].append(req_id)

    return categories

def main():
    """Run deep analysis."""
    print("\n## DEEP ANALYSIS OF REQUIREMENT ISSUES")
    print("=" * 80)

    # Check epic formatting
    epic_issues = check_epic_formatting()
    if epic_issues:
        print("\n### Epic Formatting Issues:")
        for issue_type, reqs in epic_issues.items():
            print(f"  - {issue_type}: {len(reqs)} requirements")
            if reqs:
                print(f"    Examples: {', '.join(reqs[:5])}")

    # Find conflicts
    conflicts = find_conflicting_requirements()
    if conflicts:
        print("\n### Requirements with Explicit Conflicts:")
        for req, conflict_info in conflicts.items():
            print(f"  - {req} conflicts with: {conflict_info['conflicts_with']}")
            print(f"    {conflict_info['description'][:100]}...")

    # Check validation coverage
    validation_coverage = check_validation_rules_coverage()
    print("\n### Validation Rules Coverage:")
    print(f"  - Total actual validation rules: {validation_coverage['total_actual_rules']}")
    print(f"  - Validation requirements: {validation_coverage['validation_req_count']} (REQ-023 to REQ-037)")
    print(f"  - Categories covered: {', '.join(validation_coverage['categories_covered'])}")
    print(f"  - Sample rule files: {', '.join(validation_coverage['actual_rule_files'])}")

    # Check status mismatches
    mismatches = check_status_implementation_mismatch()
    if mismatches:
        print(f"\n### Status Mismatches (marked Done but files missing): {len(mismatches)}")
        for mismatch in mismatches[:5]:
            print(f"  - {mismatch['req_id']}: {mismatch['title']}")
            print(f"    Missing: {mismatch['missing_files'][0]}")

    # Analyze categories
    categories = analyze_requirement_categories()
    print("\n### Requirement Distribution by Category:")
    for category, reqs in sorted(categories.items(), key=lambda x: -len(x[1])):
        print(f"  - {category}: {len(reqs)} requirements")
        print(f"    {', '.join(reqs[:8])}...")

    # Check for validation rule requirements specifically
    print("\n### Validation Rules Specific Check:")
    rules_dir = Path('/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels')

    # Get all rule files and categorize them
    rule_categories = defaultdict(list)
    for rule_file in rules_dir.glob('*.py'):
        if rule_file.name != '__init__.py':
            # Extract category from filename (e.g., ARAI_001.py -> ARAI)
            match = re.match(r'([A-Z]+)_', rule_file.name)
            if match:
                category = match.group(1)
                rule_categories[category].append(rule_file.name)

    print("\n  Actual validation rules by category:")
    for cat, rules in sorted(rule_categories.items()):
        print(f"    - {cat}: {len(rules)} rules")

    print("\n### Critical Path Requirements Check:")
    critical_reqs = ['REQ-001', 'REQ-002', 'REQ-008', 'REQ-023', 'REQ-038', 'REQ-039']
    req_dir = Path('/Users/chrislehnen/Projecten/Definitie-app/docs/requirements')

    for req_id in critical_reqs:
        req_file = req_dir / f'{req_id}.md'
        if req_file.exists():
            with open(req_file, 'r', encoding='utf-8') as f:
                content = f.read()

            frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
            if frontmatter_match:
                try:
                    fm = yaml.safe_load(frontmatter_match.group(1))
                    print(f"  {req_id}: {fm.get('title')} - Status: {fm.get('status')}")
                except:
                    pass

if __name__ == "__main__":
    main()
