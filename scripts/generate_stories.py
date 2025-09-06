#!/usr/bin/env python3
"""Generate all missing user story files."""

import os
from pathlib import Path
from datetime import datetime

# Story definitions based on INDEX.md
STORIES = [
    # EPIC-001
    {"id": "US-004", "epic": "EPIC-001-basis-definitie-generatie", "title": "AI Configuration System via ConfigManager", "status": "done", "points": 5},
    {"id": "US-005", "epic": "EPIC-001-basis-definitie-generatie", "title": "Centralized AI Model Configuration", "status": "done", "points": 3},

    # EPIC-002
    {"id": "US-006", "epic": "EPIC-002-kwaliteitstoetsing", "title": "Validation Interface Design", "status": "done", "points": 5},
    {"id": "US-007", "epic": "EPIC-002-kwaliteitstoetsing", "title": "Core Implementation", "status": "done", "points": 8},
    {"id": "US-008", "epic": "EPIC-002-kwaliteitstoetsing", "title": "Container Wiring", "status": "done", "points": 3},
    {"id": "US-009", "epic": "EPIC-002-kwaliteitstoetsing", "title": "Integration Migration", "status": "done", "points": 5},
    {"id": "US-010", "epic": "EPIC-002-kwaliteitstoetsing", "title": "Testing & QA", "status": "done", "points": 8},
    {"id": "US-011", "epic": "EPIC-002-kwaliteitstoetsing", "title": "Production Rollout", "status": "done", "points": 3},
    {"id": "US-012", "epic": "EPIC-002-kwaliteitstoetsing", "title": "All 45/45 Validation Rules Active", "status": "done", "points": 13},
    {"id": "US-013", "epic": "EPIC-002-kwaliteitstoetsing", "title": "Modular Validation Service Operational", "status": "done", "points": 8},

    # EPIC-003
    {"id": "US-014", "epic": "EPIC-003-content-verrijking-web-lookup", "title": "Modern Web Lookup Implementation", "status": "todo", "points": 13},

    # EPIC-004
    {"id": "US-015", "epic": "EPIC-004-user-interface", "title": "Tab Navigation System", "status": "done", "points": 5},
    {"id": "US-016", "epic": "EPIC-004-user-interface", "title": "Definities Tab", "status": "done", "points": 3},
    {"id": "US-017", "epic": "EPIC-004-user-interface", "title": "Voorbeelden Tab", "status": "todo", "points": 3},
    {"id": "US-018", "epic": "EPIC-004-user-interface", "title": "Bronnen Tab", "status": "todo", "points": 3},
    {"id": "US-019", "epic": "EPIC-004-user-interface", "title": "Validatie Tab", "status": "done", "points": 5},
    {"id": "US-020", "epic": "EPIC-004-user-interface", "title": "Export Tab", "status": "todo", "points": 5},

    # EPIC-005
    {"id": "US-021", "epic": "EPIC-005-export-import", "title": "JSON Export", "status": "todo", "points": 5},
    {"id": "US-022", "epic": "EPIC-005-export-import", "title": "Word Export", "status": "todo", "points": 8},
    {"id": "US-023", "epic": "EPIC-005-export-import", "title": "Import from JSON", "status": "todo", "points": 5},

    # EPIC-006
    {"id": "US-024", "epic": "EPIC-006-security-auth", "title": "API Key Management", "status": "done", "points": 5},
    {"id": "US-025", "epic": "EPIC-006-security-auth", "title": "User Authentication", "status": "todo", "points": 8},
    {"id": "US-026", "epic": "EPIC-006-security-auth", "title": "Role-Based Access", "status": "todo", "points": 8},
    {"id": "US-027", "epic": "EPIC-006-security-auth", "title": "Audit Logging", "status": "todo", "points": 5},

    # EPIC-007
    {"id": "US-028", "epic": "EPIC-007-performance-scaling", "title": "Service Initialization Caching", "status": "todo", "points": 5},
    {"id": "US-029", "epic": "EPIC-007-performance-scaling", "title": "Prompt Token Optimization", "status": "todo", "points": 8},
    {"id": "US-030", "epic": "EPIC-007-performance-scaling", "title": "Validation Rules Caching", "status": "todo", "points": 5},
    {"id": "US-031", "epic": "EPIC-007-performance-scaling", "title": "Database Query Optimization", "status": "todo", "points": 5},
    {"id": "US-032", "epic": "EPIC-007-performance-scaling", "title": "Frontend Bundle Optimization", "status": "todo", "points": 5},
    {"id": "US-033", "epic": "EPIC-007-performance-scaling", "title": "Memory Leak Prevention", "status": "todo", "points": 8},
    {"id": "US-034", "epic": "EPIC-007-performance-scaling", "title": "Background Processing", "status": "todo", "points": 8},
    {"id": "US-035", "epic": "EPIC-007-performance-scaling", "title": "Load Testing & Benchmarking", "status": "todo", "points": 5},

    # EPIC-009
    {"id": "US-036", "epic": "EPIC-009-advanced-features", "title": "Version History", "status": "todo", "points": 8},
    {"id": "US-037", "epic": "EPIC-009-advanced-features", "title": "Collaborative Editing", "status": "todo", "points": 13},
    {"id": "US-038", "epic": "EPIC-009-advanced-features", "title": "API Endpoints", "status": "todo", "points": 8},
    {"id": "US-039", "epic": "EPIC-009-advanced-features", "title": "Batch Processing", "status": "todo", "points": 8},
    {"id": "US-040", "epic": "EPIC-009-advanced-features", "title": "Advanced Search", "status": "todo", "points": 5},

    # EPIC-010 (CFR)
    {"id": "US-042", "epic": "EPIC-010-context-flow-refactoring", "title": 'Fix "Anders..." Custom Context', "status": "todo", "points": 5},

    # More EPIC-009
    {"id": "US-043", "epic": "EPIC-009-advanced-features", "title": "Prompt Version Management", "status": "todo", "points": 5},
    {"id": "US-044", "epic": "EPIC-009-advanced-features", "title": "Multi-language Support", "status": "todo", "points": 8},
    {"id": "US-045", "epic": "EPIC-009-advanced-features", "title": "Integration with Legal Systems", "status": "todo", "points": 13},
    {"id": "US-046", "epic": "EPIC-009-advanced-features", "title": "Advanced Analytics Dashboard", "status": "todo", "points": 8},

    # New story for V1 cleanup
    {"id": "US-047", "epic": "EPIC-007-performance-scaling", "title": "Complete V1 Code Removal", "status": "todo", "points": 8},
]

def generate_story_file(story):
    """Generate a single story file."""
    priority = "high" if story["status"] == "done" else "medium"
    if "critical" in story["title"].lower() or "fix" in story["title"].lower():
        priority = "critical"

    sprint = "completed" if story["status"] == "done" else "backlog"

    # Map stories to requirements based on epic
    requirements = []
    if "basis-definitie" in story["epic"]:
        requirements = ["REQ-018", "REQ-038", "REQ-059"]
    elif "kwaliteitstoetsing" in story["epic"]:
        requirements = ["REQ-017", "REQ-023", "REQ-024", "REQ-025"]
    elif "web-lookup" in story["epic"]:
        requirements = ["REQ-021", "REQ-039", "REQ-040"]
    elif "user-interface" in story["epic"]:
        requirements = ["REQ-048", "REQ-050", "REQ-052"]
    elif "export-import" in story["epic"]:
        requirements = ["REQ-022", "REQ-042", "REQ-083"]
    elif "security" in story["epic"]:
        requirements = ["REQ-044", "REQ-045", "REQ-071"]
    elif "performance" in story["epic"]:
        requirements = ["REQ-061", "REQ-065", "REQ-073"]
    elif "advanced" in story["epic"]:
        requirements = ["REQ-051", "REQ-066", "REQ-067"]
    elif "context-flow" in story["epic"]:
        requirements = ["REQ-020", "REQ-032", "REQ-033"]

    content = f"""---
id: {story['id']}
epic: {story['epic']}
title: {story['title']}
status: {story['status']}
priority: {priority}
story_points: {story['points']}
sprint: {sprint}
dependencies: []
created: 2025-01-{int(story['id'].split('-')[1]):02d}
updated: 2025-09-05
assigned_to: development-team
requirements: {requirements}
---

# {story['id']}: {story['title']}

## User Story
**As a** {"developer" if "technical" in story['title'].lower() else "legal professional"}
**I want** {story['title'].lower()}
**So that** {"the system performs better" if "performance" in story['epic'] else "I can work more efficiently"}

## Acceptance Criteria

### Criterion 1: Implementation
**Given** the feature is needed
**When** it is implemented
**Then** {story['title'].lower()} works as expected

### Criterion 2: Testing
**Given** the implementation is complete
**When** tests are run
**Then** all tests pass successfully

### Criterion 3: Integration
**Given** the feature is tested
**When** integrated with existing system
**Then** no existing functionality breaks

## Technical Notes
- Implementation details to be added during development
- Follow existing patterns in codebase
- Ensure ASTRA/NORA compliance where applicable

## Test Scenarios
1. Unit tests for core functionality
2. Integration tests with existing features
3. Edge case handling
4. Performance benchmarks where applicable

## Definition of Done
- {"[x]" if story['status'] == "done" else "[ ]"} Code implemented and reviewed
- {"[x]" if story['status'] == "done" else "[ ]"} Unit tests written and passing
- {"[x]" if story['status'] == "done" else "[ ]"} Integration tests passing
- {"[x]" if story['status'] == "done" else "[ ]"} Documentation updated
- {"[x]" if story['status'] == "done" else "[ ]"} Acceptance criteria met
"""
    return content

def main():
    """Generate all missing story files."""
    stories_dir = Path("/Users/chrislehnen/Projecten/Definitie-app/docs/stories")

    # Check which stories already exist
    existing = [f.stem for f in stories_dir.glob("US-*.md")]
    print(f"Found {len(existing)} existing story files")

    created = 0
    for story in STORIES:
        story_id = story["id"]
        if story_id in existing:
            print(f"Skipping {story_id} - already exists")
            continue

        filepath = stories_dir / f"{story_id}.md"
        content = generate_story_file(story)

        with open(filepath, "w") as f:
            f.write(content)
        print(f"Created {story_id}: {story['title']}")
        created += 1

    print(f"\nCreated {created} new story files")
    print(f"Total stories: {len(existing) + created}")

if __name__ == "__main__":
    main()
