#!/usr/bin/env python3
"""Validate the epic/story migration."""

import re
from pathlib import Path

import yaml


def extract_frontmatter(filepath):
    """Extract YAML frontmatter from markdown file."""
    with open(filepath) as f:
        content = f.read()

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                return yaml.safe_load(parts[1])
            except:
                return {}
    return {}


def validate_migration():
    """Validate the complete migration."""
    base_dir = Path("/Users/chrislehnen/Projecten/Definitie-app/docs")
    epics_dir = base_dir / "epics"
    stories_dir = base_dir / "stories"
    requirements_dir = base_dir / "requirements"

    print("=" * 60)
    print("EPIC/STORY MIGRATION VALIDATION REPORT")
    print("=" * 60)

    # Check epic files
    epic_files = list(epics_dir.glob("EPIC-*.md"))
    print(f"\n✅ Epic Files: {len(epic_files)} found")

    # Check naming convention
    for epic in epic_files:
        if re.match(r"EPIC-\d{3}-[\w-]+\.md", epic.name):
            print(f"  ✅ {epic.name} - correct naming")
        else:
            print(f"  ❌ {epic.name} - incorrect naming")

    # Check story files
    story_files = list(stories_dir.glob("US-*.md"))
    print(f"\n✅ Story Files: {len(story_files)} found")

    # Check requirement files
    req_files = list(requirements_dir.glob("REQ-*.md"))
    print(f"\n✅ Requirement Files: {len(req_files)} found")

    # Validate cross-references
    print("\n📋 Cross-Reference Validation:")

    # Collect all story IDs from epics
    stories_in_epics = set()
    for epic in epic_files:
        meta = extract_frontmatter(epic)
        if "stories" in meta:
            stories = meta["stories"]
            if isinstance(stories, list):
                for story in stories:
                    if isinstance(story, str):
                        story_id = story.split()[0] if " " in story else story
                        stories_in_epics.add(story_id)

    # Collect all epic references from stories
    epics_from_stories = set()
    for story in story_files:
        meta = extract_frontmatter(story)
        if "epic" in meta:
            epics_from_stories.add(meta["epic"])

    # Collect all requirement references
    requirements_referenced = set()
    for epic in epic_files:
        meta = extract_frontmatter(epic)
        if "requirements" in meta and isinstance(meta["requirements"], list):
            requirements_referenced.update(meta["requirements"])

    for story in story_files:
        meta = extract_frontmatter(story)
        if "requirements" in meta and isinstance(meta["requirements"], list):
            requirements_referenced.update(meta["requirements"])

    print(f"  Stories referenced in epics: {len(stories_in_epics)}")
    print(f"  Epics referenced from stories: {len(epics_from_stories)}")
    print(f"  Requirements referenced: {len(requirements_referenced)}")

    # Check for orphaned stories
    actual_story_ids = {f.stem for f in story_files}
    orphaned = actual_story_ids - stories_in_epics
    if orphaned:
        print(f"\n⚠️  Orphaned stories (not in any epic): {orphaned}")
    else:
        print("\n✅ All stories are linked to epics")

    # Check for missing stories
    missing = stories_in_epics - actual_story_ids
    if missing:
        print(f"⚠️  Missing story files: {missing}")
    else:
        print("✅ All referenced stories exist")

    # Check requirements exist
    actual_req_ids = {f.stem for f in req_files}
    missing_reqs = requirements_referenced - actual_req_ids
    if missing_reqs:
        print(f"⚠️  Missing requirement files: {missing_reqs}")
    else:
        print("✅ All referenced requirements exist")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Epics: {len(epic_files)}")
    print(f"Stories: {len(story_files)}")
    print(f"Requirements: {len(req_files)}")
    print("Cross-references validated: ✅")

    if not orphaned and not missing and not missing_reqs:
        print("\n🎉 MIGRATION SUCCESSFUL - All validations passed!")
    else:
        print("\n⚠️  MIGRATION COMPLETE - Some issues need attention")


if __name__ == "__main__":
    validate_migration()
