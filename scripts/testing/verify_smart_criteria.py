#!/usr/bin/env python3
"""
Script om SMART criteria compliance te verifiëren in documentatie.
Verify SMART criteria compliance in documentation.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

def check_smart_criteria(file_path: Path) -> Dict[str, bool]:
    """Check if file contains SMART criteria elements."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().lower()

    smart_checks = {
        'specific': False,
        'measurable': False,
        'achievable': False,
        'relevant': False,
        'time_bound': False
    }

    # Check for SMART section
    has_smart_section = 'smart criteria' in content or 'acceptatiecriteria' in content

    # Specific - look for concrete descriptions
    specific_patterns = [
        r'\bmoel\b', r'\bmoet\b', r'\bzal\b', r'\bkan\b',
        r'\bfunctionaliteit\b', r'\bfeature\b', r'\bsysteem\b'
    ]
    smart_checks['specific'] = any(re.search(p, content) for p in specific_patterns)

    # Measurable - look for metrics
    measurable_patterns = [
        r'\d+\s*(seconden?|minuten?|uur|%|gebruikers?|items?|records?)',
        r'\b(binnen|maximaal|minimaal|minder dan|meer dan)\s+\d+',
        r'\b(percentage|aantal|hoeveelheid|responstijd)\b'
    ]
    smart_checks['measurable'] = any(re.search(p, content) for p in measurable_patterns)

    # Achievable - look for feasibility indicators
    achievable_patterns = [
        r'\b(haalbaar|realiseerbaar|mogelijk|implementeerbaar)\b',
        r'\b(gebruik(t|en)?|met|via|door)\b.*\b(technologie|framework|library|service)\b'
    ]
    smart_checks['achievable'] = any(re.search(p, content) for p in achievable_patterns)

    # Relevant - look for business value
    relevant_patterns = [
        r'\b(zodat|omdat|waardoor|voor|belangrijk|kritiek|essentieel|noodzakelijk)\b',
        r'\b(gebruiker|klant|organisatie|justitie|om|dji|rechtspraak|justid|cjib)\b'
    ]
    smart_checks['relevant'] = any(re.search(p, content) for p in relevant_patterns)

    # Time-bound - look for time constraints
    time_patterns = [
        r'\b(deadline|sprint|release|versie|v\d+\.\d+|q\d|kwartaal|maand|week)\b',
        r'\b(voor|na|tijdens|binnen|uiterlijk|gereed)\b.*\b(datum|periode|tijd)\b'
    ]
    smart_checks['time_bound'] = any(re.search(p, content) for p in time_patterns)

    # Give credit if has explicit SMART section
    if has_smart_section:
        for key in smart_checks:
            smart_checks[key] = True

    return smart_checks

def analyze_directory(directory: Path, pattern: str) -> Dict:
    """Analyze all files in directory for SMART compliance."""
    results = {
        'total_files': 0,
        'fully_compliant': 0,
        'partial_compliant': 0,
        'non_compliant': 0,
        'criteria_scores': defaultdict(int),
        'files_needing_improvement': []
    }

    for file_path in directory.glob(pattern):
        if file_path.is_file() and not file_path.name.startswith('.'):
            results['total_files'] += 1

            smart_checks = check_smart_criteria(file_path)
            compliance_count = sum(smart_checks.values())

            # Track individual criteria
            for criterion, met in smart_checks.items():
                if met:
                    results['criteria_scores'][criterion] += 1

            # Categorize compliance
            if compliance_count == 5:
                results['fully_compliant'] += 1
            elif compliance_count >= 3:
                results['partial_compliant'] += 1
            else:
                results['non_compliant'] += 1
                results['files_needing_improvement'].append({
                    'file': file_path.name,
                    'score': compliance_count,
                    'missing': [k for k, v in smart_checks.items() if not v]
                })

    return results

def main():
    """Main execution function."""
    project_root = Path('/Users/chrislehnen/Projecten/Definitie-app')

    print("🔍 SMART Criteria Compliance Verificatie")
    print("=" * 60)

    directories = [
        (project_root / 'docs' / 'requirements', 'REQ-*.md'),
        (project_root / 'docs' / 'epics', 'EPIC-*.md'),
        (project_root / 'docs' / 'stories', 'US-*.md'),
    ]

    overall_stats = {
        'total_files': 0,
        'fully_compliant': 0,
        'partial_compliant': 0,
        'non_compliant': 0
    }

    for directory, pattern in directories:
        if directory.exists():
            print(f"\n📁 Analyzing {directory.name}...")
            results = analyze_directory(directory, pattern)

            # Update overall stats
            for key in overall_stats:
                overall_stats[key] += results[key]

            # Print directory results
            print(f"  Total files: {results['total_files']}")
            print(f"  ✅ Fully compliant (5/5): {results['fully_compliant']}")
            print(f"  ⚠️  Partial compliant (3-4/5): {results['partial_compliant']}")
            print(f"  ❌ Non-compliant (<3/5): {results['non_compliant']}")

            if results['criteria_scores']:
                print(f"\n  Criteria coverage:")
                for criterion, count in sorted(results['criteria_scores'].items()):
                    percentage = (count / results['total_files'] * 100) if results['total_files'] > 0 else 0
                    print(f"    - {criterion.capitalize()}: {count}/{results['total_files']} ({percentage:.1f}%)")

            # Show files needing improvement (top 5)
            if results['files_needing_improvement']:
                print(f"\n  Files needing improvement (worst {min(5, len(results['files_needing_improvement']))}):")
                for item in results['files_needing_improvement'][:5]:
                    print(f"    - {item['file']} (score: {item['score']}/5)")
                    print(f"      Missing: {', '.join(item['missing'])}")

    # Print overall summary
    print("\n" + "=" * 60)
    print("📊 OVERALL SUMMARY")
    print(f"Total documents analyzed: {overall_stats['total_files']}")
    print(f"✅ Fully SMART compliant: {overall_stats['fully_compliant']} ({overall_stats['fully_compliant']/overall_stats['total_files']*100:.1f}%)")
    print(f"⚠️  Partially compliant: {overall_stats['partial_compliant']} ({overall_stats['partial_compliant']/overall_stats['total_files']*100:.1f}%)")
    print(f"❌ Non-compliant: {overall_stats['non_compliant']} ({overall_stats['non_compliant']/overall_stats['total_files']*100:.1f}%)")

    # Determine overall status
    compliance_rate = (overall_stats['fully_compliant'] + overall_stats['partial_compliant']) / overall_stats['total_files'] * 100

    print(f"\n🎯 Overall Compliance Rate: {compliance_rate:.1f}%")
    if compliance_rate >= 90:
        print("✅ EXCELLENT - Documentation meets SMART criteria standards")
    elif compliance_rate >= 70:
        print("⚠️  GOOD - Most documentation is SMART compliant")
    else:
        print("❌ NEEDS IMPROVEMENT - Significant SMART criteria gaps")

    return overall_stats

if __name__ == "__main__":
    main()
