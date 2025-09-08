---
canonical: true
status: active
owner: architecture
last_verified: 2025-09-08
applies_to: claude-agents@v2
---

# Technical Analysis: Agent Workflow Architecture

## Executive Summary

This document provides a comprehensive technical analysis of the Claude agent workflow system, its architecture patterns, test structures, and integration points with the DefinitieAgent application.

## 1. Agent Architecture Overview

### 1.1 System Structure

```
~/.claude/agents/
├── README.md                    # Configuration overview
├── workflows/                   # Workflow definitions
│   ├── workflows.yaml          # Central workflow configuration
│   ├── prompt-refinement-loop.yaml
│   └── prompt-refinement-example.md
└── [agent-name].md             # 11 specialized agent prompts
```

### 1.2 Agent Categories

#### Orchestrators (1)
- **workflow-router**: Intelligent workflow selection based on task characteristics

#### Core Development Team (4)
- **business-analyst-justice**: Requirements analysis and user story creation
- **justice-architecture-designer**: EA/SA/TA documentation generation
- **developer-implementer**: Code implementation and development
- **quality-assurance-tester**: Testing and quality assurance

#### Quality & Optimization (3)
- **code-reviewer-comprehensive**: Code review and analysis
- **refactor-specialist**: Code improvement and optimization
- **doc-standards-guardian**: Documentation compliance verification

#### Support (3)
- **prompt-engineer**: Prompt optimization and refinement
- **devops-pipeline-orchestrator**: CI/CD and deployment management

## 2. Workflow Patterns

### 2.1 Workflow Types and Characteristics

| Workflow | Duration | Complexity | Primary Use Case | Phases |
|----------|----------|------------|------------------|---------|
| ANALYSIS | 20-30m | Low | Research without changes | INVESTIGATE → DOCUMENT |
| REVIEW_CYCLE | 30-60m | Medium | Code review only | REVIEW → SUGGEST |
| DOCUMENTATION | 15-30m | Low | Documentation updates | UPDATE → VERIFY |
| DEBUG | 30-90m | Medium | Bug investigation and fixes | REPRODUCE → DIAGNOSE → FIX → VERIFY |
| MAINTENANCE | 15-45m | Low | Config and dependency updates | ASSESS → UPDATE → VALIDATE |
| HOTFIX | 30-60m | High | Critical production fixes | TRIAGE → FIX → REVIEW → DEPLOY |
| REFACTOR_ONLY | 20-60m | Medium | Code improvements | PLAN → APPLY → VERIFY |
| SPIKE | 1-4h | High | Technical research | RESEARCH → PROTOTYPE → DOCUMENT |
| FULL_TDD | 2-4h | High | Complete feature development | 8-phase TDD cycle |

### 2.2 Workflow Selection Algorithm

```yaml
routing:
  rules:
    # Intent-based routing
    - intent: ["review", "check", "validate"]
      workflow: review_cycle

    # File-based routing
    - files: ["*.md", "*.txt"]
      only: true
      workflow: documentation

    # Risk-based routing
    - risk: "critical"
      urgency: "high"
      workflow: hotfix

    # Default fallback
    - default: true
      workflow: full_tdd
```

### 2.3 Gate System

Each workflow phase has gates that must be satisfied:
- **Mandatory gates**: Must be completed before phase transition
- **Optional gates**: Can be skipped with justification
- **Light gates**: Simplified validation for quick workflows

Example from DEBUG workflow:
```yaml
phases:
  - name: "REPRODUCE"
    gates:
      - issue_reproduced
      - steps_documented
  - name: "DIAGNOSE"
    gates:
      - root_cause_found
      - analysis_complete
```

## 3. Agent Prompt Patterns

### 3.1 Standard Agent Structure

```markdown
---
name: [agent-name]
description: [comprehensive description with examples]
model: inherit
color: [visual identifier]
---

[Agent role definition and expertise]

## Core Responsibilities
[Numbered list of primary duties]

## Working Methodology
[Step-by-step approach]

## Output Format
[Expected deliverables]

## Quality Standards
[Verification criteria]
```

### 3.2 Key Agent Patterns

#### Pattern 1: Role-Based Expertise
Each agent has a clearly defined role with specific domain expertise:
- Justice sector knowledge for `justice-architecture-designer`
- Testing expertise for `quality-assurance-tester`
- Optimization skills for `refactor-specialist`

#### Pattern 2: Input/Output Contracts
Agents define explicit contracts for inter-agent communication:
- Input requirements (format, validation)
- Output specifications (structure, metadata)
- Handoff protocols between agents

#### Pattern 3: Hallucination Prevention
Built-in constraints to prevent fabrication:
- "ALLEEN op basis van" patterns in Dutch agents
- Source verification requirements
- Explicit boundary definitions

## 4. Test Integration Patterns

### 4.1 Current Test Coverage

The codebase shows limited direct testing of agent workflows:
- No dedicated workflow test files found
- Agent patterns referenced only in `test_story_31_sources_metadata.py`
- Workflow service tests focus on status transitions, not agent orchestration

### 4.2 Recommended Test Patterns

#### Unit Tests for Workflow Selection
```python
class TestWorkflowRouter:
    def test_intent_based_routing(self):
        """Test that intents map to correct workflows."""
        router = WorkflowRouter()
        assert router.select("review this code") == "review_cycle"
        assert router.select("fix bug #123") == "debug"
        assert router.select("urgent production issue") == "hotfix"

    def test_file_based_routing(self):
        """Test file pattern matching."""
        router = WorkflowRouter()
        assert router.select("update README.md") == "documentation"
        assert router.select("modify config.yaml") == "maintenance"
```

#### Integration Tests for Agent Handoffs
```python
class TestAgentHandoffs:
    @pytest.mark.asyncio
    async def test_analyst_to_architect_handoff(self):
        """Test seamless handoff from business analyst to architect."""
        # Create user story with business analyst
        story_output = await invoke_agent("business-analyst-justice", task)

        # Transform via prompt engineer
        transformed = await invoke_agent("prompt-engineer", {
            "source": story_output,
            "target": "justice-architecture-designer"
        })

        # Pass to architect
        architecture = await invoke_agent("justice-architecture-designer", transformed)

        # Verify contract compliance
        assert validate_handoff_contract(story_output, architecture)
```

#### Workflow Gate Tests
```python
class TestWorkflowGates:
    def test_debug_workflow_gates(self):
        """Test that all gates in DEBUG workflow are validated."""
        workflow = WorkflowDefinition("debug")

        # Test REPRODUCE phase gates
        phase = workflow.phases["REPRODUCE"]
        assert phase.validate_gate("issue_reproduced", evidence)
        assert phase.validate_gate("steps_documented", docs)

        # Test phase transition
        assert workflow.can_transition("REPRODUCE", "DIAGNOSE")
```

## 5. Integration with DefinitieAgent

### 5.1 Service Architecture Alignment

The agent workflow system could integrate with existing services:

```python
# In service_factory.py
class WorkflowOrchestrator:
    def __init__(self, container: ServiceContainer):
        self.container = container
        self.router = WorkflowRouter()
        self.agents = AgentRegistry()

    async def execute_task(self, task: str, context: dict):
        # Route to appropriate workflow
        workflow = self.router.select(task)

        # Execute workflow phases
        for phase in workflow.phases:
            agents = phase.get_agents()
            results = await self.run_agents(agents, context)

            # Validate gates
            if not phase.validate_gates(results):
                raise WorkflowGateError(phase)

            context.update(results)

        return context
```

### 5.2 Potential Integration Points

1. **Validation Orchestrator**: Could use REVIEW_CYCLE workflow
2. **Web Lookup Service**: Could use SPIKE workflow for research
3. **Definition Generator**: Could use FULL_TDD workflow
4. **Documentation**: Could use DOCUMENTATION workflow

## 6. Performance Considerations

### 6.1 Workflow Metrics

Target performance metrics from workflows.yaml:
```yaml
metrics:
  efficiency:
    simple_tasks: "< 30 minutes"
    workflow_match_rate: "> 90%"
    override_frequency: "< 10%"
  quality:
    test_coverage: "> 80%"
    regression_rate: "< 2%"
```

### 6.2 Optimization Opportunities

1. **Parallel Agent Execution**: Some phases allow parallel execution
2. **Light Gates**: Simplified validation for low-risk tasks
3. **Workflow Caching**: Reuse workflow results for similar tasks
4. **Smart Routing**: Learn from override patterns to improve selection

## 7. Critical Observations

### 7.1 Strengths

1. **Right-sized Processes**: Different workflows for different task complexities
2. **Clear Agent Responsibilities**: Well-defined roles and boundaries
3. **Gate-based Quality Control**: Explicit validation at each phase
4. **Flexible Routing**: Multiple criteria for workflow selection

### 7.2 Gaps and Opportunities

1. **Test Coverage**: No dedicated tests for workflow execution
2. **Integration**: Not integrated with existing service architecture
3. **Monitoring**: No metrics collection for workflow performance
4. **Documentation**: Limited examples of actual workflow execution

### 7.3 Implementation Recommendations

1. **Create Workflow Test Suite**:
   - Unit tests for routing logic
   - Integration tests for agent handoffs
   - End-to-end tests for complete workflows

2. **Build Integration Layer**:
   - WorkflowOrchestrator service
   - Agent adapters for existing services
   - Metrics collection and reporting

3. **Enhance Documentation**:
   - Workflow execution examples
   - Agent handoff patterns
   - Integration guides

## 8. Workflow-Router Protocol

### 8.1 Two-Stage Optimization Process

The workflow-router uses a mandatory two-stage process:

1. **Stage 1: Prompt Engineering**
   - All prompts MUST first go through prompt-engineer
   - Optimizes for clarity, specificity, and actionability
   - User gets Accept/Modify/Cancel options

2. **Stage 2: Workflow Routing**
   - Only processes prompts marked with `OPTIMIZED_PROMPT_MARKER`
   - Selects optimal workflow based on optimized prompt
   - Initiates workflow execution

### 8.2 Critical Routing Constraint

The workflow-router is explicitly a ROUTING-ONLY system:
- MUST NOT execute or implement tasks
- MUST NOT analyze content directly
- MUST ONLY select and pass to appropriate workflow
- Job ends at workflow selection

## 9. Agent Usage Analysis

### 9.1 Active Agent Usage in Workflows

| Agent | Usage Count | Workflows |
|-------|-------------|-----------|
| `developer-implementer` | 10x | debug, maintenance, hotfix, refactor_only, spike, full_tdd |
| `quality-assurance-tester` | 7x | documentation, debug, maintenance, refactor_only, full_tdd |
| `refactor-specialist` | 4x | review_cycle, maintenance, refactor_only, full_tdd |
| `code-reviewer-comprehensive` | 4x | analysis, review_cycle, hotfix, full_tdd |
| `doc-standards-guardian` | 3x | analysis, documentation, spike |
| `business-analyst-justice` | 3x | analysis, hotfix, full_tdd |
| `justice-architecture-designer` | 2x | spike, full_tdd |
| `devops-pipeline-orchestrator` | 2x | hotfix, full_tdd |

### 9.2 Unused Agents

Two agents exist but are not used in workflow definitions:
1. **prompt-engineer**: Critical for prompt optimization protocol
2. **workflow-router**: Meta-orchestrator for workflow selection

These are special-purpose agents used outside the standard workflow patterns.

## 10. Conclusion

The agent workflow architecture represents a sophisticated approach to task automation with:
- Clear separation of concerns through specialized agents
- Flexible workflow selection based on task characteristics
- Quality gates ensuring consistent outcomes
- Optimization for both speed and quality

The system is well-designed but would benefit from:
- Comprehensive test coverage
- Deep integration with existing services
- Performance monitoring and optimization
- Extended documentation with real-world examples

## Appendix A: Agent Registry

| Agent | Primary Function | Key Patterns |
|-------|-----------------|--------------|
| workflow-router | Task routing | Intent/file/risk-based selection |
| prompt-engineer | Prompt optimization | Normalization, hallucination prevention |
| business-analyst-justice | Requirements | User stories, BDD scenarios |
| justice-architecture-designer | Architecture | EA/SA/TA documentation |
| developer-implementer | Implementation | Code generation, type hints |
| quality-assurance-tester | Testing | Coverage, regression prevention |
| code-reviewer-comprehensive | Review | Static analysis, best practices |
| refactor-specialist | Optimization | Code cleanup, performance |
| doc-standards-guardian | Documentation | Compliance, consistency |
| devops-pipeline-orchestrator | Deployment | CI/CD, rollback plans |

## Appendix B: Workflow Phase Patterns

Common phase patterns across workflows:
1. **Investigation Phase**: INVESTIGATE, RESEARCH, REPRODUCE
2. **Planning Phase**: PLAN, DESIGN, TRIAGE
3. **Implementation Phase**: FIX, APPLY, UPDATE, DEV-GREEN
4. **Validation Phase**: VERIFY, TEST-CONFIRM, VALIDATE
5. **Documentation Phase**: DOCUMENT, REPORT

## Appendix C: Test Strategy Recommendations

### Unit Test Coverage
- Workflow selection logic (90% coverage)
- Gate validation rules (100% coverage)
- Agent input/output contracts (85% coverage)

### Integration Test Coverage
- Agent handoffs (80% coverage)
- Workflow phase transitions (90% coverage)
- Error recovery mechanisms (75% coverage)

### End-to-End Test Coverage
- Complete workflow execution (70% coverage)
- Multi-agent collaboration (60% coverage)
- Performance benchmarks (baseline established)

---
*Generated by: SPIKE Workflow*
*Version: 2.0*
*Last Updated: 2025-09-08*
