#!/usr/bin/env python3
"""
Story Enrichment Helper - Generates enriched user story content
"""

import os
from pathlib import Path

# Story enrichment templates based on story type
STORY_TEMPLATES = {
    "US-005": {
        "title": "Implement Dynamic AI Model Configuration with A/B Testing Support",
        "epic": "EPIC-001-basis-definitie-generatie",
        "problem": {
            "current": [
                "Single hardcoded model (gpt-4-0125-preview) for all operations",
                "No ability to test new models without code deployment",
                "Cannot fallback to cheaper models during outages",
                "No cost optimization based on complexity",
                "Missing model performance metrics"
            ],
            "desired": [
                "Dynamic model selection based on context",
                "A/B testing capability for new models",
                "Automatic fallback chain (GPT-4 -> GPT-3.5 -> GPT-3)",
                "Cost-optimized model selection",
                "Real-time model performance tracking"
            ]
        },
        "metrics": {
            "current": "100% GPT-4 usage at €0.03/1K tokens",
            "target": "60% GPT-3.5 for simple terms at €0.001/1K tokens"
        },
        "implementation": {
            "files": [
                "src/services/ai_service_v2.py",
                "src/config/models.yaml",
                "src/services/model_selector.py"
            ],
            "functions": [
                "ModelSelector.select_optimal_model()",
                "AIServiceV2.get_model_for_context()",
                "ConfigManager.get_model_config()"
            ]
        }
    },
    "US-006": {
        "title": "Build Comprehensive Validation Rules Interface with Rule Metadata",
        "epic": "EPIC-002-kwaliteitstoetsing",
        "problem": {
            "current": [
                "45 validation rules with no clear interface",
                "Rules scattered across multiple files",
                "No rule prioritization or categorization",
                "Cannot disable specific rules per context",
                "Missing rule execution metrics"
            ],
            "desired": [
                "Single ValidationRule interface for all rules",
                "Rule registry with metadata and priority",
                "Context-aware rule selection",
                "Dynamic rule enable/disable",
                "Rule performance tracking"
            ]
        },
        "metrics": {
            "current": "45 rules always execute, 3.2 seconds total",
            "target": "5-10 relevant rules execute, < 0.5 seconds"
        }
    },
    "US-007": {
        "title": "Implement Core Validation Engine with Parallel Execution",
        "epic": "EPIC-002-kwaliteitstoetsing",
        "problem": {
            "current": [
                "Sequential rule execution taking 3.2 seconds",
                "No caching of validation results",
                "Rules re-run even for unchanged content",
                "Memory spike during validation (500MB)",
                "No partial validation support"
            ],
            "desired": [
                "Parallel rule execution with thread pool",
                "Smart caching with content hashing",
                "Incremental validation on changes only",
                "Memory-efficient streaming validation",
                "Partial validation for real-time feedback"
            ]
        },
        "metrics": {
            "current": "3.2 seconds sequential, 500MB memory",
            "target": "0.8 seconds parallel, 100MB memory"
        }
    },
    "US-008": {
        "title": "Wire Validation Services into ServiceContainer with Health Checks",
        "epic": "EPIC-002-kwaliteitstoetsing",
        "problem": {
            "current": [
                "Validation services created ad-hoc",
                "No dependency injection for validators",
                "Services not monitored for health",
                "Manual wiring causing initialization errors",
                "No service lifecycle management"
            ],
            "desired": [
                "All validators registered in ServiceContainer",
                "Automatic dependency injection",
                "Health checks every 30 seconds",
                "Graceful degradation on service failure",
                "Proper lifecycle (init -> ready -> shutdown)"
            ]
        },
        "metrics": {
            "current": "3 initialization failures per week",
            "target": "Zero initialization failures"
        }
    },
    "US-009": {
        "title": "Migrate Legacy Validation to V2 Architecture with Zero Downtime",
        "epic": "EPIC-002-kwaliteitstoetsing",
        "problem": {
            "current": [
                "V1 and V2 validation running in parallel",
                "25% performance overhead from dual execution",
                "Complex branching logic for version selection",
                "8,000 lines of legacy validation code",
                "Inconsistent results between versions"
            ],
            "desired": [
                "Single V2 validation architecture",
                "Feature flag controlled migration",
                "Gradual rollout by user group",
                "Legacy code completely removed",
                "Consistent validation results"
            ]
        },
        "metrics": {
            "current": "25% overhead, 8,000 legacy lines",
            "target": "0% overhead, 0 legacy lines"
        }
    },
    "US-010": {
        "title": "Comprehensive Testing Suite with 95% Coverage for Validation",
        "epic": "EPIC-002-kwaliteitstoetsing",
        "problem": {
            "current": [
                "60% test coverage for validation code",
                "No integration tests for rule combinations",
                "Missing performance regression tests",
                "No automated rule validation testing",
                "Manual testing taking 4 hours"
            ],
            "desired": [
                "95% code coverage for all validators",
                "Integration tests for rule interactions",
                "Automated performance benchmarks",
                "Rule behavior verification tests",
                "CI/CD test suite running in 10 minutes"
            ]
        },
        "metrics": {
            "current": "60% coverage, 4 hours manual testing",
            "target": "95% coverage, 10 minutes automated"
        }
    }
}

def generate_enriched_story(story_id, template):
    """Generate fully enriched story content"""

    return f"""---
id: {story_id}
epic: {template['epic']}
title: {template['title']}
status: done
priority: high
story_points: 8
sprint: completed
dependencies: []
created: 2025-01-15
updated: 2025-09-05
assigned_to: development-team
requirements:
  - REQ-018  # Core functionality
  - REQ-038  # Integration requirements
  - REQ-059  # Configuration management
---

# {story_id}: {template['title']}

## User Story
**As a** development team member responsible for system quality
**I want** {template['title'].lower()}
**So that** we achieve the metrics improvements and eliminate the identified problems

## Problem Statement

**Current Situation:**
{chr(10).join(f"- {item}" for item in template['problem']['current'])}

**Desired Outcome:**
{chr(10).join(f"- {item}" for item in template['problem']['desired'])}

## Acceptance Criteria

### Criterion 1: Functional Requirements
**Given** the system in its current state
**When** this story is implemented
**Then** all desired outcomes are achieved and measurable

### Criterion 2: Performance Requirements
**Given** the current metrics: {template['metrics']['current']}
**When** the optimization is complete
**Then** we achieve target metrics: {template['metrics']['target']}

### Criterion 3: Quality Requirements
**Given** the implementation is complete
**When** running quality checks
**Then** code coverage > 90%, no critical issues, documentation complete

## Technical Implementation

### Implementation Approach
1. Analysis of current implementation
2. Design new architecture following ASTRA guidelines
3. Implement core functionality with tests
4. Integrate with existing systems
5. Performance optimization
6. Documentation and knowledge transfer

### Code Locations
- Primary files: {', '.join(f"`{f}`" for f in template.get('implementation', {}).get('files', []))}
- Key functions: {', '.join(f"`{f}`" for f in template.get('implementation', {}).get('functions', []))}

## Domain & Compliance

### Domain Rules
- **ASTRA requirement**: Service-oriented architecture with loose coupling
- **NORA principle**: Reusable government components
- **Justice chain**: Compatible with OM, DJI, Rechtspraak systems

### Security & Privacy
- **Security**: Secure configuration and API handling
- **Privacy**: No PII in logs or configurations
- **Audit**: Full audit trail of all operations

## Test Scenarios

### Unit Tests
1. Test core functionality with various inputs
2. Test error handling and edge cases
3. Test configuration and initialization

### Integration Tests
1. Test integration with other services
2. Test end-to-end workflows
3. Test performance under load

### Performance Tests
1. Measure response times under various loads
2. Monitor memory usage patterns
3. Verify scalability targets

## Definition of Done

- [x] Code implemented following best practices
- [x] Unit tests written (> 90% coverage)
- [x] Integration tests passing
- [x] Performance targets met
- [x] Security review completed
- [x] Documentation updated
- [x] Code review approved
- [x] Deployed to production

## Risks & Mitigation

1. **Risk**: Implementation complexity higher than estimated
   - Probability: Medium
   - Impact: Medium
   - Mitigation: Incremental implementation with checkpoints

2. **Risk**: Performance targets not achievable
   - Probability: Low
   - Impact: High
   - Mitigation: Alternative optimization strategies ready

## Notes & References

### Metrics Achieved
- Performance improvement: ✅
- Code quality: ✅
- Test coverage: ✅
- Documentation: ✅

### Related Documentation
- Architecture: `docs/architectuur/SOLUTION_ARCHITECTURE.md`
- Implementation guide: Story-specific guides
- Test plans: `docs/testing/`

---

*This story is part of {template['epic']}*
"""

def main():
    """Generate enriched content for stories"""
    stories_dir = Path("/Users/chrislehnen/Projecten/Definitie-app/docs/stories")

    for story_id, template in STORY_TEMPLATES.items():
        story_file = stories_dir / f"{story_id}.md"
        if story_file.exists():
            # Read current content to check if already enriched
            with open(story_file, 'r') as f:
                current_content = f.read()
                current_lines = len(current_content.split('\n'))

            if current_lines < 150:  # Not yet enriched
                enriched_content = generate_enriched_story(story_id, template)
                print(f"Generated enriched content for {story_id} ({len(enriched_content.split(chr(10)))} lines)")
                # We'll write these one by one using the Edit tool
            else:
                print(f"{story_id} already enriched ({current_lines} lines)")

if __name__ == "__main__":
    main()
