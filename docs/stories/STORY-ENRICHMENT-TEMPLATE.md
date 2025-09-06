# User Story Enrichment Template

## Required Sections for Complete Story

### 1. Frontmatter (Complete)
```yaml
---
id: US-XXX
epic: EPIC-XXX-onderwerp
title: Concrete descriptive title
status: todo/in_progress/done
priority: critical/high/medium/low
story_points: X (based on complexity)
sprint: current/backlog/completed
dependencies: [US-XXX, US-YYY] or []
created: 2025-01-XX
updated: 2025-09-05
assigned_to: development-team/testing-team
requirements: [REQ-XXX, REQ-YYY]
---
```

### 2. User Story (Clear roles and benefits)
**As a** [specific role: legal professional/developer/product owner/administrator]
**I want** [specific feature with clear scope]
**So that** [measurable business value]

### 3. Problem Statement (NEW - Add context)
**Current Situation:**
- Specific problem with metrics (e.g., "7,250 tokens per request")
- Impact on users/system
- Root cause if known

**Desired Outcome:**
- Target metrics (e.g., "< 3,000 tokens")
- Success indicators

### 4. Acceptance Criteria (SMART and Testable)
Minimum 3 criteria in Given/When/Then format:

#### Criterion 1: [Functional Requirement]
**Given** [specific initial state]
**When** [specific action]
**Then** [measurable outcome]

#### Criterion 2: [Performance Requirement]
**Given** [load condition]
**When** [operation performed]
**Then** [response time < X ms]

#### Criterion 3: [Edge Case Handling]
**Given** [edge condition]
**When** [unusual input]
**Then** [graceful handling]

### 5. Technical Implementation (Specific)
```markdown
## Implementation Approach
1. **Step 1**: [Specific action in specific file]
2. **Step 2**: [Next action with location]
3. **Step 3**: [Integration step]

## Code Locations
- Primary files: `src/services/xxx.py`, `src/ui/tabs/yyy.py`
- Key functions: `function_name()`, `class.method()`
- Config files: `config/xxx.yaml`

## Technical Decisions
- Pattern to use: [Singleton/Factory/Observer]
- Libraries needed: [existing or new]
- Data structures: [specific choices]
```

### 6. Domain & Compliance (Justice context)
```markdown
## Domain Rules
- ASTRA requirement: [specific rule]
- NORA guideline: [specific principle]
- Justice chain: [OM/DJI/Rechtspraak impact]

## Security & Privacy
- Security: [specific measure]
- Privacy: [AVG/GDPR consideration]
- Audit: [logging requirement]
```

### 7. Test Scenarios (Concrete)
```markdown
## Test Coverage Required

### Unit Tests
1. **Test**: `test_function_with_valid_input()`
   - Input: `{"term": "vonnis", "context": "strafrecht"}`
   - Expected: Definition object with Dutch legal text
   - Assert: Length > 50 chars, contains "straf"

2. **Test**: `test_function_with_invalid_input()`
   - Input: `{"term": "", "context": None}`
   - Expected: ValidationError raised
   - Assert: Error message contains "required"

### Integration Tests
1. **Test**: `test_end_to_end_flow()`
   - Setup: Initialize all services
   - Action: Generate definition with validation
   - Assert: Response time < 5s, validation passes

### Performance Tests
1. **Test**: `test_performance_under_load()`
   - Setup: 100 concurrent requests
   - Measure: Response time, memory usage
   - Assert: p95 < 200ms, memory < 500MB
```

### 8. Definition of Done (Checklist)
```markdown
## Definition of Done
- [ ] Code implemented following patterns in codebase
- [ ] Unit tests written (coverage > 80%)
- [ ] Integration tests passing
- [ ] Performance benchmarks met
- [ ] Security review completed
- [ ] Documentation updated (code + user)
- [ ] Code review approved by 2 developers
- [ ] Acceptance criteria validated by PO
- [ ] Deployed to test environment
- [ ] No critical SonarQube issues
```

### 9. Risks & Mitigation
```markdown
## Risks
1. **Risk**: [e.g., Breaking existing functionality]
   - Probability: Medium
   - Impact: High
   - Mitigation: Feature flag for gradual rollout

2. **Risk**: [e.g., Performance degradation]
   - Probability: Low
   - Impact: Medium
   - Mitigation: Load testing before release
```

### 10. Notes & References
```markdown
## Additional Context
- Related PRs: #123, #456
- Documentation: [link to design doc]
- Spike results: [link to investigation]
- Customer feedback: [ticket numbers]
```

---

## Example Applied to US-029

### Before (Generic):
"As a legal professional I want prompt token optimization"

### After (Enriched):
"As a product owner I want to reduce OpenAI API token usage from 7,250 to <3,000 tokens per request So that we save 60% on API costs while maintaining definition quality"

With specific implementation steps, test cases, and measurable success criteria.
