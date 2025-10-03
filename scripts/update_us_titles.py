#!/usr/bin/env python3
"""
Update all User Story titles to include descriptive information.
Scans all US-*.md files and updates the titel field with US-ID + description.
"""

import re
from pathlib import Path


def extract_description(content: str, us_id: str) -> str:
    """Extract a short description from the user story content."""
    lines = content.split("\n")

    # Try to find description from various sections
    description = ""

    # Check for "Als ... wil ik ..." pattern
    for i, line in enumerate(lines):
        if line.startswith("Als ") or line.startswith("## Als "):
            # Extract user story format
            story_line = line.replace("## ", "").strip()
            if len(story_line) > 10 and len(story_line) < 150:
                description = story_line
                break

    # Check for Summary/Doel section
    if not description:
        in_summary = False
        for line in lines:
            if (
                "summary" in line.lower()
                or "doel" in line.lower()
                or "objective" in line.lower()
            ):
                in_summary = True
                continue
            if in_summary and line.strip() and not line.startswith("#"):
                description = line.strip()
                if len(description) > 20:
                    break

    # Check first meaningful paragraph after frontmatter
    if not description:
        past_frontmatter = False
        for line in lines:
            if line.strip() == "---" and not past_frontmatter:
                past_frontmatter = True
                continue
            if (
                past_frontmatter
                and line.strip()
                and not line.startswith("#")
                and len(line.strip()) > 20
            ):
                description = line.strip()
                if len(description) < 200:
                    break

    # Truncate if too long
    if description and len(description) > 120:
        description = description[:117] + "..."

    return description or "User story implementation"


def update_us_title(file_path: Path):
    """Update a single user story file with descriptive title."""
    content = file_path.read_text(encoding="utf-8")

    # Extract US-ID from filename
    us_id_match = re.search(r"(US-\d+)", file_path.name)
    if not us_id_match:
        print(f"⚠️  Skipping {file_path}: no US-ID in filename")
        return False

    us_id = us_id_match.group(1)

    # Check if title already has US-ID prefix
    title_match = re.search(r'^titel:\s*"?([^"\n]+)"?', content, re.MULTILINE)
    if title_match:
        current_title = title_match.group(1)
        if current_title.startswith(f"{us_id}:"):
            print(f"✓  Skipping {us_id}: already has descriptive title")
            return False

    # Extract description
    description = extract_description(content, us_id)

    # Create new title
    new_title = f'"{us_id}: {description}"'

    # Update title field
    if title_match:
        # Replace existing titel field
        old_title_line = title_match.group(0)
        new_title_line = f"titel: {new_title}"
        updated_content = content.replace(old_title_line, new_title_line, 1)
    else:
        # Add titel field after id field in frontmatter
        id_match = re.search(r"(^id:\s*" + us_id + r")", content, re.MULTILINE)
        if id_match:
            insert_pos = content.find("\n", id_match.end())
            updated_content = (
                content[: insert_pos + 1]
                + f"titel: {new_title}\n"
                + content[insert_pos + 1 :]
            )
        else:
            print(f"⚠️  Skipping {us_id}: no id field found")
            return False

    # Write updated content
    file_path.write_text(updated_content, encoding="utf-8")
    print(f"✅ Updated {us_id}: {description[:60]}...")
    return True


def main():
    """Main function to update all user stories."""
    backlog_dir = Path("docs/backlog")

    if not backlog_dir.exists():
        print(f"❌ Error: {backlog_dir} not found!")
        return

    # Find all US-*.md files
    us_files = list(backlog_dir.glob("EPIC-*/US-*/US-*.md"))
    us_files.extend(
        backlog_dir.glob("EPIC-*/US-*.md")
    )  # Some might be directly in EPIC dir

    print(f"Found {len(us_files)} user story files\n")

    updated_count = 0
    for us_file in sorted(us_files):
        if update_us_title(us_file):
            updated_count += 1

    print(f"\n✅ Updated {updated_count} user stories")
    print(
        f"⏭️  Skipped {len(us_files) - updated_count} user stories (already have descriptive titles)"
    )


if __name__ == "__main__":
    main()
