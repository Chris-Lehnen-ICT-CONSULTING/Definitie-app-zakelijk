#!/usr/bin/env python3
"""Verify that requirement fixes have been properly applied."""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple
import json

# Base path
BASE_PATH = Path("/Users/chrislehnen/Projecten/Definitie-app")
REQUIREMENTS_PATH = BASE_PATH / "docs" / "requirements"

def check_file_exists(file_path: str) -> bool:
    """Check if a source file actually exists."""
    if "TODO" in file_path:
        return True  # Special case for auth service
    full_path = BASE_PATH / file_path
    return full_path.exists()

def analyze_requirement(file_path: Path) -> Dict:
    """Analyze a single requirement file for issues."""
    issues = []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    req_id = file_path.stem

    # Check epic format (should be EPIC-00X)
    epic_pattern = r'EPIC-(\d+)'
    epic_matches = re.findall(epic_pattern, content)
    for match in epic_matches:
        if len(match) == 1:  # Single digit, should be 3
            issues.append(f"Epic format issue: EPIC-{match} should be EPIC-00{match}")
        elif len(match) == 2:
            issues.append(f"Epic format issue: EPIC-{match} should be EPIC-0{match}")

    # Check source files exist
    source_pattern = r'path:\s*([^\n]+)'
    source_matches = re.findall(source_pattern, content)
    for source in source_matches:
        source = source.strip()
        if source and not source.startswith("docs/") and not source == "all":
            if not check_file_exists(source) and "TODO" not in source:
                issues.append(f"Missing source file: {source}")

    # Check for invalid story references
    invalid_stories = ["US-6.5", "US-6.6", "US-8.1", "US-8.2", "US-8.3"]
    for story in invalid_stories:
        if story in content:
            issues.append(f"Invalid story reference: {story}")

    # Check for SMART criteria in high priority requirements
    if "Priority: High" in content or "priority: high" in content:
        if "## SMART Criteria" not in content:
            issues.append("Missing SMART criteria for high priority requirement")

    # Check domain context for domain requirements
    req_num = int(req_id.replace("REQ-", ""))
    if 13 <= req_num <= 22:
        if "## Domain Context" not in content and "ASTRA" not in content:
            issues.append("Missing domain context for domain requirement")

    # Extract status
    status_match = re.search(r'[Ss]tatus:\s*(\w+)', content)
    status = status_match.group(1) if status_match else "Unknown"

    return {
        "id": req_id,
        "status": status,
        "issues": issues,
        "issue_count": len(issues)
    }

def main():
    """Main verification function."""
    print("Verifying requirement fixes...")
    print("=" * 80)

    # Get all requirement files
    req_files = sorted(REQUIREMENTS_PATH.glob("REQ-*.md"))

    results = []
    total_issues = 0
    requirements_with_issues = 0

    for req_file in req_files:
        result = analyze_requirement(req_file)
        results.append(result)

        if result["issues"]:
            requirements_with_issues += 1
            total_issues += result["issue_count"]
            print(f"\n{result['id']} (Status: {result['status']}):")
            for issue in result["issues"]:
                print(f"  - {issue}")

    # Summary statistics
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    print(f"Total requirements analyzed: {len(req_files)}")
    print(f"Requirements with issues: {requirements_with_issues}")
    print(f"Requirements without issues: {len(req_files) - requirements_with_issues}")
    print(f"Total issues found: {total_issues}")

    # Issue breakdown
    issue_types = {}
    for result in results:
        for issue in result["issues"]:
            if "Epic format" in issue:
                issue_type = "Epic format issues"
            elif "Missing source file" in issue:
                issue_type = "Missing source files"
            elif "Invalid story" in issue:
                issue_type = "Invalid story references"
            elif "SMART criteria" in issue:
                issue_type = "Missing SMART criteria"
            elif "domain context" in issue:
                issue_type = "Missing domain context"
            else:
                issue_type = "Other issues"

            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1

    print("\nISSUE BREAKDOWN:")
    for issue_type, count in sorted(issue_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {issue_type}: {count}")

    # Status breakdown
    status_counts = {}
    for result in results:
        status = result["status"]
        status_counts[status] = status_counts.get(status, 0) + 1

    print("\nSTATUS BREAKDOWN:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")

    # Success rate
    success_rate = ((len(req_files) - requirements_with_issues) / len(req_files)) * 100
    print(f"\nSUCCESS RATE: {success_rate:.1f}%")

    # Save detailed report
    report_path = REQUIREMENTS_PATH / "fix_verification_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            "summary": {
                "total_requirements": len(req_files),
                "requirements_with_issues": requirements_with_issues,
                "total_issues": total_issues,
                "success_rate": success_rate
            },
            "issue_breakdown": issue_types,
            "status_breakdown": status_counts,
            "details": results
        }, f, indent=2)

    print(f"\nDetailed report saved to: {report_path}")

if __name__ == "__main__":
    main()
