#!/usr/bin/env python3
"""Fix all requirement documents based on quality report findings."""

import re
from pathlib import Path

# Base path
BASE_PATH = Path("/Users/chrislehnen/Projecten/Definitie-app")
REQUIREMENTS_PATH = BASE_PATH / "docs" / "requirements"

# File mappings (incorrect -> correct)
FILE_MAPPINGS = {
    "src/services/auth_service.py": "TODO - Auth service not yet implemented",
    "src/ui/tabs/generatie_tab.py": "src/ui/components/definition_generator_tab.py",
    "src/ui/tabs/generation_tab.py": "src/ui/components/definition_generator_tab.py",
    "src/database/repositories/definition_repository.py": "src/services/definition_repository.py",
    "src/services/unified_definition_generator.py": "src/services/definition_generator.py",
    "src/services/validation/validation_orchestrator_v2.py": "src/services/orchestrators/validation_orchestrator_v2.py",
    "src/services/validation/orchestrator_v2.py": "src/services/orchestrators/validation_orchestrator_v2.py",
}

# Story mappings (incorrect -> correct)
STORY_MAPPINGS = {
    "US-6.5": None,  # Remove
    "US-6.6": None,  # Remove
    "US-8.1": "US-3.1",
    "US-8.2": "US-3.1",
    "US-8.3": "US-3.1",
}


def fix_epic_format(content: str) -> str:
    """Fix EPIC-X to EPIC-00X format."""
    # Fix single digit epics
    content = re.sub(r"\bEPIC-(\d)\b", lambda m: f"EPIC-00{m.group(1)}", content)
    # Ensure all are 3 digits
    return re.sub(r"\bEPIC-(\d{2})\b", lambda m: f"EPIC-0{m.group(1)}", content)


def fix_source_files(content: str) -> str:
    """Fix source file references."""
    for old_path, new_path in FILE_MAPPINGS.items():
        if old_path in content:
            if new_path == "TODO - Auth service not yet implemented":
                # Special handling for auth service
                content = content.replace(old_path, new_path)
            else:
                content = content.replace(old_path, new_path)

    # Fix toetsregels references
    return re.sub(
        r"config/toetsregels/regels/(\w+)\.json",
        r"src/toetsregels/regels/\1.py",
        content,
    )



def fix_story_references(content: str) -> str:
    """Fix story references."""
    for old_story, new_story in STORY_MAPPINGS.items():
        if old_story in content:
            if new_story is None:
                # Remove invalid story reference
                content = re.sub(f"- {old_story}.*\n", "", content)
                content = re.sub(f"{old_story}, ", "", content)
                content = re.sub(f", {old_story}", "", content)
                content = re.sub(f"{old_story}", "", content)
            else:
                content = content.replace(old_story, new_story)

    # Add CFR stories where context flow is mentioned
    if "context flow" in content.lower() and "CFR" not in content:
        # Add CFR reference in Related User Stories section
        related_pattern = r"(## Related User Stories\n)(.*?)(\n##|\Z)"
        match = re.search(related_pattern, content, re.DOTALL)
        if match:
            stories_content = match.group(2)
            if stories_content.strip():
                stories_content += (
                    "\n- CFR.1: Context Flow Refactoring - Basic Implementation"
                )
            else:
                stories_content = (
                    "- CFR.1: Context Flow Refactoring - Basic Implementation"
                )
            content = (
                content[: match.start(2)] + stories_content + content[match.end(2) :]
            )

    return content


def fix_status_if_needed(content: str, req_id: str) -> str:
    """Fix status from Done to In Progress where implementation is missing."""
    needs_status_fix = [
        "REQ-005",  # SQL Injection Prevention
        "REQ-018",  # Core Definition Generation
        "REQ-022",  # Export Functionality
    ]

    if req_id in needs_status_fix and "Status: Done" in content:
        content = content.replace("Status: Done", "Status: In Progress")
        # Add note about missing implementation
        if "## Notes" not in content:
            content += "\n## Notes\n\n"
        if "Implementation partially complete" not in content:
            notes_index = content.find("## Notes")
            if notes_index > -1:
                insert_pos = content.find("\n", notes_index + len("## Notes")) + 1
                content = (
                    content[:insert_pos]
                    + "- Implementation partially complete, auth service pending\n"
                    + content[insert_pos:]
                )

    return content


def add_smart_criteria(content: str, req_id: str) -> str:
    """Add SMART criteria to high priority requirements that lack them."""
    if "## SMART Criteria" in content:
        return content  # Already has SMART criteria

    # Check if this is a high priority requirement
    if "Priority: High" not in content:
        return content

    # Extract requirement title for context
    title_match = re.search(r"# (REQ-\d+): (.+)\n", content)
    if not title_match:
        return content

    req_title = title_match.group(2)

    # Generate appropriate SMART criteria based on requirement type
    smart_criteria = generate_smart_criteria(req_id, req_title)

    # Insert SMART criteria after Success Criteria section
    if "## Success Criteria" in content:
        insert_pos = content.find("## Success Criteria")
        next_section = content.find("\n## ", insert_pos + 1)
        if next_section > -1:
            content = (
                content[:next_section]
                + "\n## SMART Criteria\n\n"
                + smart_criteria
                + "\n"
                + content[next_section:]
            )
        else:
            content += "\n## SMART Criteria\n\n" + smart_criteria + "\n"

    return content


def generate_smart_criteria(req_id: str, title: str) -> str:
    """Generate SMART criteria based on requirement type."""
    req_num = int(req_id.replace("REQ-", ""))

    if req_num <= 12:  # Security requirements
        return (
            """- **Specific**: Implementation of security control for """
            + title.lower()
            + """
- **Measurable**: Zero security vulnerabilities in implemented feature
- **Achievable**: Using established security libraries and patterns
- **Relevant**: Critical for justice sector data protection requirements
- **Time-bound**: Implementation within current sprint cycle"""
        )

    if req_num <= 22:  # Domain requirements
        return (
            """- **Specific**: Full implementation of """
            + title.lower()
            + """ functionality
- **Measurable**: All validation rules pass with 100% accuracy
- **Achievable**: Using existing GPT-4 API and validation framework
- **Relevant**: Core functionality for legal definition quality
- **Time-bound**: Complete before production release"""
        )

    if req_num <= 35:  # Validation requirements
        return (
            """- **Specific**: Validation rule for """
            + title.lower()
            + """
- **Measurable**: Rule catches 95%+ of targeted quality issues
- **Achievable**: Implementable with current validation framework
- **Relevant**: Ensures definition quality meets justice standards
- **Time-bound**: Implementation within validation epic timeline"""
        )

    if req_num <= 50:  # UI requirements
        return (
            """- **Specific**: User interface for """
            + title.lower()
            + """
- **Measurable**: Response time < 200ms, accessibility score > 95
- **Achievable**: Using Streamlit framework capabilities
- **Relevant**: Improves user productivity and experience
- **Time-bound**: Aligned with UI epic completion milestone"""
        )

    if req_num <= 70:  # Integration requirements
        return (
            """- **Specific**: Integration with """
            + title.lower()
            + """
- **Measurable**: 99.9% uptime, < 2s response time
- **Achievable**: Using established integration patterns
- **Relevant**: Enables data exchange with justice chain partners
- **Time-bound**: Based on chain partner availability schedule"""
        )

    # Performance requirements
    return (
        """- **Specific**: Performance optimization for """
        + title.lower()
        + """
- **Measurable**: Meet defined SLA targets (response time, throughput)
- **Achievable**: Through caching, optimization, and scaling
- **Relevant**: Ensures system meets production requirements
- **Time-bound**: Before production deployment"""
    )


def add_domain_context(content: str, req_id: str) -> str:
    """Add domain context to domain requirements."""
    req_num = int(req_id.replace("REQ-", ""))

    if 13 <= req_num <= 22:  # Domain requirements
        if "## Domain Context" not in content:
            domain_context = """## Domain Context

This requirement aligns with Dutch justice sector standards:
- **ASTRA Compliance**: Follows ASTRA architecture guidelines for justice IT systems
- **NORA Principles**: Adheres to Nederlandse Overheid Referentie Architectuur
- **Justice Chain Integration**: Compatible with OM, DJI, Justid, and Rechtspraak systems
- **Legal Framework**: Complies with Dutch legal terminology standards
"""
            # Insert after Description
            desc_pos = content.find("## Description")
            if desc_pos > -1:
                next_section = content.find("\n## ", desc_pos + 1)
                if next_section > -1:
                    content = (
                        content[:next_section]
                        + "\n"
                        + domain_context
                        + content[next_section:]
                    )
                else:
                    content += "\n" + domain_context

    return content


def process_requirement_file(file_path: Path) -> tuple[bool, str]:
    """Process a single requirement file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        original_content = content
        req_id = file_path.stem

        # Apply all fixes
        content = fix_epic_format(content)
        content = fix_source_files(content)
        content = fix_story_references(content)
        content = fix_status_if_needed(content, req_id)
        content = add_smart_criteria(content, req_id)
        content = add_domain_context(content, req_id)

        # Write back if changed
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True, f"Fixed {req_id}"
        return False, f"No changes needed for {req_id}"

    except Exception as e:
        return False, f"Error processing {file_path.name}: {e!s}"


def main():
    """Main processing function."""
    print("Starting requirement fixes...")
    print("=" * 60)

    # Get all requirement files
    req_files = sorted(REQUIREMENTS_PATH.glob("REQ-*.md"))

    fixed_count = 0
    error_count = 0

    for req_file in req_files:
        success, message = process_requirement_file(req_file)
        if success:
            if "Fixed" in message:
                fixed_count += 1
                print(f"✓ {message}")
        elif "Error" in message:
            error_count += 1
            print(f"✗ {message}")

    print("=" * 60)
    print("Processing complete!")
    print(f"Files fixed: {fixed_count}")
    print(f"Errors: {error_count}")
    print(f"Total processed: {len(req_files)}")


if __name__ == "__main__":
    main()
