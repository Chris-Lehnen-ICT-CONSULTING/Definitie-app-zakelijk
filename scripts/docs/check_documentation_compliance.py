#!/usr/bin/env python3
"""
Check documentation compliance with standards defined in DOCUMENTATION_POLICY.md
"""

import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import yaml

# Required frontmatter fields
REQUIRED_FRONTMATTER = {
    "canonical",  # true|false
    "status",  # active|draft|archived
    "owner",  # architecture|validation|platform|product|domain
    "last_verified",  # YYYY-MM-DD or DD-MM-YYYY
    "applies_to",  # definitie-app@version
}

VALID_STATUS = {
    "active",
    "draft",
    "archived",
    "ACTIEF",
    "CONCEPT",
    "GEARCHIVEERD",
    "IN_UITVOERING",
    "VOLTOOID",
    "WACHTEND",
    "GEBLOKKEERD",
    "KRITIEK",
}
VALID_OWNERS = {
    "architecture",
    "validation",
    "platform",
    "product",
    "domain",
    "business-analyst",
    "technical-lead",
    "development",
}


def find_docs_directory() -> Path:
    """Find the docs directory relative to script location."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    docs_dir = project_root / "docs"

    if not docs_dir.exists():
        raise FileNotFoundError(f"Docs directory not found at {docs_dir}")

    return docs_dir


def extract_frontmatter(content: str) -> dict | None:
    """Extract YAML frontmatter from markdown content."""
    if not content.startswith("---"):
        return None

    try:
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter_str = parts[1].strip()
            if frontmatter_str:
                return yaml.safe_load(frontmatter_str)
    except yaml.YAMLError:
        return None

    return None


def check_date_format(date_str: str) -> tuple[bool, str]:
    """Check if date is in correct format and not too old."""
    formats = ["%Y-%m-%d", "%d-%m-%Y", "%d-%m-%Y"]

    for fmt in formats:
        try:
            date = datetime.strptime(date_str, fmt)
            days_old = (datetime.now() - date).days

            if days_old > 90:
                return True, f"Last verified > 90 days ago ({days_old} days)"
            return True, "OK"
        except ValueError:
            continue

    return False, "Invalid date format"


def check_canonical_uniqueness(canonical_docs: dict[str, list[Path]]) -> list[str]:
    """Check for multiple canonical documents per subject."""
    issues = []
    for subject, docs in canonical_docs.items():
        if len(docs) > 1:
            doc_list = ", ".join(str(d.relative_to(d.parent.parent)) for d in docs)
            issues.append(f"Multiple canonical docs for '{subject}': {doc_list}")
    return issues


def analyze_file(file_path: Path, docs_dir: Path) -> dict:
    """Analyze a single markdown file for compliance."""
    issues = []
    warnings = []
    info = {}

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Extract frontmatter
        frontmatter = extract_frontmatter(content)

        if frontmatter is None:
            # Check if this is a special file that doesn't need frontmatter
            special_files = ["README.md", "INDEX.md", "CHANGELOG.md", "CLAUDE.md"]
            if file_path.name not in special_files and ".backup" not in str(file_path):
                issues.append("Missing frontmatter")
        else:
            # Check required fields
            missing_fields = REQUIRED_FRONTMATTER - set(frontmatter.keys())
            if missing_fields:
                # Some files may have alternative fields
                alternative_checks = []
                if "id" in frontmatter:  # Epic/Story/Requirement files
                    alternative_checks.extend(["canonical", "applies_to"])
                if "titel" in frontmatter or "title" in frontmatter:
                    alternative_checks.append("owner")

                # Remove alternatives from missing
                missing_fields = missing_fields - set(alternative_checks)

                if missing_fields:
                    issues.append(
                        f"Missing frontmatter fields: {', '.join(missing_fields)}"
                    )

            # Check field values
            if "status" in frontmatter:
                if frontmatter["status"] not in VALID_STATUS:
                    warnings.append(f"Invalid status: '{frontmatter['status']}'")

            if "owner" in frontmatter:
                if frontmatter["owner"] not in VALID_OWNERS:
                    warnings.append(f"Non-standard owner: '{frontmatter['owner']}'")

            if "last_verified" in frontmatter:
                valid, msg = check_date_format(str(frontmatter["last_verified"]))
                if not valid:
                    issues.append(msg)
                elif msg != "OK":
                    warnings.append(msg)

            if "canonical" in frontmatter:
                info["canonical"] = frontmatter.get("canonical", False)
                info["subject"] = frontmatter.get("subject") or file_path.stem

        # Check for broken links
        broken_links = []
        link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
        for match in re.finditer(link_pattern, content):
            link_text, link_url = match.groups()
            if link_url.startswith("../") or link_url.startswith("./"):
                # Relative link - check if file exists
                target = file_path.parent / link_url
                if not target.exists() and not link_url.startswith("http"):
                    broken_links.append(f"{link_text} -> {link_url}")

        if broken_links:
            issues.append(
                f"Broken links: {', '.join(broken_links[:3])}"
            )  # Show first 3

        # Check markdown structure
        lines = content.split("\n")
        h1_count = sum(1 for line in lines if line.startswith("# "))
        if h1_count > 1:
            warnings.append(f"Multiple H1 headers ({h1_count})")

    except Exception as e:
        issues.append(f"Error reading file: {e}")

    return {
        "file": str(file_path.relative_to(docs_dir)),
        "issues": issues,
        "warnings": warnings,
        "info": info,
    }


def main():
    """Main function to check documentation compliance."""
    docs_dir = find_docs_directory()

    print("Documentation Compliance Check")
    print("=" * 70)
    print(f"Checking documentation in: {docs_dir}")
    print("Policy: DOCUMENTATION_POLICY.md standards")
    print("-" * 70)

    # Collect all results
    all_results = []
    canonical_docs = defaultdict(list)

    # Check all markdown files
    for md_file in docs_dir.rglob("*.md"):
        # Skip backup files and archive
        if any(
            x in str(md_file)
            for x in [".backup", ".normbackup", "/archief/", "/archive/"]
        ):
            continue

        result = analyze_file(md_file, docs_dir)
        all_results.append(result)

        # Track canonical documents
        if result["info"].get("canonical"):
            subject = result["info"].get("subject", md_file.stem)
            canonical_docs[subject].append(md_file)

    # Check canonical uniqueness
    canonical_issues = check_canonical_uniqueness(canonical_docs)

    # Generate report
    files_with_issues = [r for r in all_results if r["issues"]]
    files_with_warnings = [r for r in all_results if r["warnings"]]
    compliant_files = [r for r in all_results if not r["issues"] and not r["warnings"]]

    print("\n## Compliance Summary")
    print(f"Total files checked: {len(all_results)}")
    print(f"Fully compliant: {len(compliant_files)}")
    print(f"Files with issues: {len(files_with_issues)}")
    print(f"Files with warnings: {len(files_with_warnings)}")

    if canonical_issues:
        print(f"\n## Canonical Conflicts ({len(canonical_issues)})")
        for issue in canonical_issues[:5]:  # Show first 5
            print(f"  - {issue}")

    if files_with_issues:
        print("\n## Critical Issues (showing first 10)")
        for result in files_with_issues[:10]:
            print(f"\n  {result['file']}:")
            for issue in result["issues"]:
                print(f"    ❌ {issue}")

    if files_with_warnings:
        print("\n## Warnings (showing first 10)")
        for result in files_with_warnings[:10]:
            if result not in files_with_issues[:10]:  # Don't repeat files
                print(f"\n  {result['file']}:")
                for warning in result["warnings"]:
                    print(f"    ⚠️  {warning}")

    # Write detailed report
    report_path = docs_dir / "docs-compliance-check.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write(f"generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write("canonical: false\n")
        f.write("status: active\n")
        f.write("owner: validation\n")
        f.write(f"last_verified: {datetime.now().strftime('%Y-%m-%d')}\n")
        f.write("applies_to: definitie-app@current\n")
        f.write("---\n\n")
        f.write("# Documentation Compliance Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")

        f.write("## Summary\n\n")
        f.write(f"- **Total files checked:** {len(all_results)}\n")
        f.write(f"- **Fully compliant:** {len(compliant_files)}\n")
        f.write(f"- **Files with issues:** {len(files_with_issues)}\n")
        f.write(f"- **Files with warnings:** {len(files_with_warnings)}\n")
        f.write(f"- **Canonical conflicts:** {len(canonical_issues)}\n\n")

        if canonical_issues:
            f.write("## Canonical Conflicts\n\n")
            for issue in canonical_issues:
                f.write(f"- {issue}\n")
            f.write("\n")

        if files_with_issues:
            f.write("## Files with Issues\n\n")
            for result in files_with_issues:
                f.write(f"### {result['file']}\n")
                for issue in result["issues"]:
                    f.write(f"- ❌ {issue}\n")
                f.write("\n")

        if files_with_warnings:
            f.write("## Files with Warnings\n\n")
            for result in files_with_warnings:
                f.write(f"### {result['file']}\n")
                for warning in result["warnings"]:
                    f.write(f"- ⚠️ {warning}\n")
                f.write("\n")

        f.write("## Compliant Files\n\n")
        f.write(
            f"{len(compliant_files)} files are fully compliant with documentation standards.\n"
        )

    print("\n✅ Detailed report saved to: docs-compliance-check.md")

    return 0


if __name__ == "__main__":
    exit(main())
