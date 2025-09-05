#!/usr/bin/env python3
"""Analyze all requirements for verification report."""

import os
import re
import json
from pathlib import Path
from collections import defaultdict, Counter
import yaml

def parse_requirement_file(filepath):
    """Parse a single requirement file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse frontmatter
    frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not frontmatter_match:
        return None

    try:
        frontmatter = yaml.safe_load(frontmatter_match.group(1))
    except:
        return None

    # Extract body sections
    body = content[frontmatter_match.end():]

    # Extract acceptance criteria
    criteria_match = re.search(r'## Acceptatiecriteria.*?\n(.*?)(?=##|\Z)', body, re.DOTALL)
    criteria = criteria_match.group(1).strip() if criteria_match else ""

    # Extract conflicts
    conflicts_match = re.search(r'## Conflicten.*?\n(.*?)(?=##|\Z)', body, re.DOTALL)
    conflicts = conflicts_match.group(1).strip() if conflicts_match else ""

    return {
        'id': frontmatter.get('id'),
        'title': frontmatter.get('title'),
        'type': frontmatter.get('type'),
        'priority': frontmatter.get('priority'),
        'status': frontmatter.get('status'),
        'sources': frontmatter.get('sources', []),
        'links': frontmatter.get('links', {}),
        'criteria': criteria,
        'conflicts': conflicts,
        'filepath': str(filepath)
    }

def analyze_requirements():
    """Analyze all requirements."""
    req_dir = Path('/Users/chrislehnen/Projecten/Definitie-app/docs/requirements')
    requirements = []

    # Parse all requirement files
    for req_file in sorted(req_dir.glob('REQ-*.md')):
        if req_file.name == 'REQ-000.md':
            continue  # Skip template

        req_data = parse_requirement_file(req_file)
        if req_data:
            requirements.append(req_data)

    # Statistics
    stats = {
        'total': len(requirements),
        'by_type': Counter(r['type'] for r in requirements),
        'by_priority': Counter(r['priority'] for r in requirements),
        'by_status': Counter(r['status'] for r in requirements),
    }

    # Issues found
    issues = {
        'missing_sources': [],
        'invalid_epics': [],
        'invalid_stories': [],
        'missing_criteria': [],
        'no_smart_criteria': [],
        'orphaned_reqs': [],
        'duplicates': defaultdict(list),
        'status_inconsistencies': []
    }

    # Check each requirement
    for req in requirements:
        # Check for missing sources
        if not req['sources']:
            issues['missing_sources'].append(req['id'])

        # Check for missing acceptance criteria
        if not req['criteria']:
            issues['missing_criteria'].append(req['id'])
        elif not any(word in req['criteria'].lower() for word in ['moet', 'binnen', 'maximaal', 'minimaal']):
            issues['no_smart_criteria'].append(req['id'])

        # Check for orphaned requirements (no epic/story links)
        if not req['links'].get('epics') and not req['links'].get('stories'):
            issues['orphaned_reqs'].append(req['id'])

    # Find potential duplicates by title similarity
    title_groups = defaultdict(list)
    for req in requirements:
        # Normalize title for comparison
        normalized = req['title'].lower().replace(' ', '').replace('-', '')
        title_groups[normalized[:10]].append(req['id'])

    for group in title_groups.values():
        if len(group) > 1:
            issues['duplicates'][','.join(group)] = 'Similar titles detected'

    return requirements, stats, issues

def check_file_existence(requirements):
    """Check if referenced source files exist."""
    base_path = Path('/Users/chrislehnen/Projecten/Definitie-app')
    missing_files = defaultdict(list)

    for req in requirements:
        for source in req['sources']:
            filepath = base_path / source['path']
            if not filepath.exists():
                missing_files[req['id']].append(source['path'])

    return missing_files

def validate_epic_story_links(requirements):
    """Validate epic and story links."""
    # Load master stories document
    master_file = Path('/Users/chrislehnen/Projecten/Definitie-app/docs/stories/MASTER-EPICS-USER-STORIES.md')

    valid_epics = set()
    valid_stories = set()

    if master_file.exists():
        with open(master_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract epic numbers (Epic 1, Epic 2, etc.)
        epic_matches = re.findall(r'Epic (\d+):', content, re.IGNORECASE)
        valid_epics = {f'EPIC-{int(num):03d}' for num in epic_matches}

        # Extract story numbers
        story_matches = re.findall(r'Story (\d+\.\d+):', content, re.IGNORECASE)
        valid_stories = {f'US-{story}' for story in story_matches}

        # Also check for CFR stories
        cfr_matches = re.findall(r'Story (CFR\.\d+):', content, re.IGNORECASE)
        valid_stories.update(cfr_matches)

    invalid_links = defaultdict(dict)

    for req in requirements:
        # Check epics
        for epic in req['links'].get('epics', []):
            if epic not in valid_epics:
                if 'invalid_epics' not in invalid_links[req['id']]:
                    invalid_links[req['id']]['invalid_epics'] = []
                invalid_links[req['id']]['invalid_epics'].append(epic)

        # Check stories
        for story in req['links'].get('stories', []):
            if story not in valid_stories and not story.startswith('PER-'):
                if 'invalid_stories' not in invalid_links[req['id']]:
                    invalid_links[req['id']]['invalid_stories'] = []
                invalid_links[req['id']]['invalid_stories'].append(story)

    return invalid_links, valid_epics, valid_stories

def analyze_domain_requirements():
    """Analyze domain-specific requirements (REQ-013 to REQ-022)."""
    domain_reqs = []
    for i in range(13, 23):
        req_file = Path(f'/Users/chrislehnen/Projecten/Definitie-app/docs/requirements/REQ-{i:03d}.md')
        if req_file.exists():
            req_data = parse_requirement_file(req_file)
            if req_data:
                domain_reqs.append(req_data)

    domain_issues = {
        'missing_dutch_context': [],
        'no_astra_nora_ref': [],
        'no_justice_ref': []
    }

    for req in domain_reqs:
        content = req['criteria'] + ' ' + str(req.get('conflicts', ''))

        # Check for Dutch terminology
        if not any(word in content.lower() for word in ['nederlandse', 'juridisch', 'wetgeving', 'recht']):
            domain_issues['missing_dutch_context'].append(req['id'])

        # Check for ASTRA/NORA references
        if 'astra' not in content.lower() and 'nora' not in content.lower():
            domain_issues['no_astra_nora_ref'].append(req['id'])

    return domain_issues

def main():
    """Main analysis function."""
    print("Starting Requirements Verification Analysis...")
    print("=" * 80)

    # Analyze requirements
    requirements, stats, issues = analyze_requirements()

    # Check file existence
    missing_files = check_file_existence(requirements)

    # Validate epic/story links
    invalid_links, valid_epics, valid_stories = validate_epic_story_links(requirements)

    # Analyze domain requirements
    domain_issues = analyze_domain_requirements()

    # Generate report
    print("\n## VERIFICATION REPORT")
    print("=" * 80)

    print("\n### 1. OVERVIEW STATISTICS")
    print(f"Total requirements analyzed: {stats['total']}")
    print(f"\nBy Type:")
    for type_name, count in stats['by_type'].items():
        print(f"  - {type_name}: {count}")

    print(f"\nBy Priority:")
    for priority, count in stats['by_priority'].items():
        print(f"  - {priority}: {count}")

    print(f"\nBy Status:")
    for status, count in stats['by_status'].items():
        print(f"  - {status}: {count}")

    print("\n### 2. CRITICAL ISSUES")
    print("-" * 40)

    if missing_files:
        print(f"\n❌ Missing Source Files ({len(missing_files)} requirements affected):")
        for req_id, files in sorted(missing_files.items())[:10]:
            print(f"  - {req_id}: {files[0]}")
            if len(files) > 1:
                for f in files[1:3]:
                    print(f"           {f}")

    if invalid_links:
        print(f"\n❌ Invalid Epic/Story Links ({len(invalid_links)} requirements affected):")
        for req_id, link_issues in sorted(invalid_links.items())[:10]:
            print(f"  - {req_id}:")
            if 'invalid_epics' in link_issues:
                print(f"    Invalid epics: {link_issues['invalid_epics']}")
            if 'invalid_stories' in link_issues:
                print(f"    Invalid stories: {link_issues['invalid_stories']}")

    if issues['orphaned_reqs']:
        print(f"\n⚠️ Orphaned Requirements (no epic/story links): {len(issues['orphaned_reqs'])}")
        print(f"  {', '.join(issues['orphaned_reqs'][:10])}")

    print("\n### 3. QUALITY ISSUES")
    print("-" * 40)

    if issues['missing_criteria']:
        print(f"\n⚠️ Missing Acceptance Criteria: {len(issues['missing_criteria'])} requirements")
        print(f"  {', '.join(issues['missing_criteria'][:10])}")

    if issues['no_smart_criteria']:
        print(f"\n⚠️ Non-SMART Criteria: {len(issues['no_smart_criteria'])} requirements")
        print(f"  {', '.join(issues['no_smart_criteria'][:10])}")

    if issues['duplicates']:
        print(f"\n⚠️ Potential Duplicates: {len(issues['duplicates'])} groups")
        for group, reason in list(issues['duplicates'].items())[:5]:
            print(f"  - {group}: {reason}")

    print("\n### 4. DOMAIN-SPECIFIC ISSUES")
    print("-" * 40)

    if domain_issues['missing_dutch_context']:
        print(f"\n⚠️ Domain reqs missing Dutch context: {len(domain_issues['missing_dutch_context'])}")
        print(f"  {', '.join(domain_issues['missing_dutch_context'])}")

    if domain_issues['no_astra_nora_ref']:
        print(f"\n⚠️ Domain reqs without ASTRA/NORA ref: {len(domain_issues['no_astra_nora_ref'])}")
        print(f"  {', '.join(domain_issues['no_astra_nora_ref'])}")

    print("\n### 5. SUMMARY")
    print("-" * 40)

    total_issues = (len(missing_files) + len(invalid_links) + len(issues['orphaned_reqs']) +
                   len(issues['missing_criteria']) + len(issues['no_smart_criteria']))

    print(f"\n📊 Total Issues Found: {total_issues}")
    print(f"  - Critical (must fix): {len(missing_files) + len(invalid_links)}")
    print(f"  - Warnings (should fix): {len(issues['orphaned_reqs']) + len(issues['missing_criteria'])}")
    print(f"  - Quality improvements: {len(issues['no_smart_criteria']) + len(issues['duplicates'])}")

    print("\n✅ Valid Epic IDs found in MASTER-EPICS-USER-STORIES.md:")
    print(f"  {', '.join(sorted(valid_epics))}")

    print("\n✅ Valid Story IDs found:")
    print(f"  {', '.join(sorted(valid_stories)[:20])}...")

    # Export detailed results to JSON
    results = {
        'stats': {k: dict(v) if isinstance(v, Counter) else v for k, v in stats.items()},
        'missing_files': dict(missing_files),
        'invalid_links': dict(invalid_links),
        'issues': {k: v for k, v in issues.items() if v},
        'domain_issues': domain_issues
    }

    with open('/Users/chrislehnen/Projecten/Definitie-app/docs/requirements/verification_results.json', 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n📄 Detailed results saved to verification_results.json")

if __name__ == "__main__":
    main()
