# TDD to Deployment Workflow

## Overview
This document describes the complete workflow from TDD development to production deployment using the orchestrated agent system.

## Workflow Diagram

```
TODO → ANALYSIS → DESIGN → TEST-RED → DEV-GREEN → REVIEW → REFACTOR → TEST-CONFIRM → DONE
                                                                                         ↓
                                                                            DevOps Pipeline Orchestrator
                                                                                         ↓
                                                    BRANCH → COMMIT → PR → CI → RELEASE → DEPLOY → MONITOR
```

## Phase 1: TDD Development (TDD Orchestrator)

### 1.1 TODO → ANALYSIS
- **Agent**: business-analyst-justice
- **Output**: User story in MASTER-EPICS-USER-STORIES.md
- **Gate**: Complete scope and acceptance criteria

### 1.2 ANALYSIS → DESIGN
- **Agent**: justice-architecture-designer
- **Output**: EA/SA/TA documentation
- **Gate**: Architecture docs complete

### 1.3 DESIGN → TEST-RED
- **Agent**: quality-assurance-tester
- **Output**: Failing tests (unit + integration)
- **Commit**: `test(<ID>): add failing tests`
- **Gate**: Tests fail as expected

### 1.4 TEST-RED → DEV-GREEN
- **Agent**: developer-implementer
- **Output**: Minimal code to pass tests
- **Commit**: `feat(<ID>): implement feature`
- **Gate**: All tests green

### 1.5 DEV-GREEN → REVIEW
- **Agent**: code-reviewer-comprehensive
- **Output**: Review report in docs/reviews/
- **Gate**: No blocking issues

### 1.6 REVIEW → REFACTOR
- **Agent**: refactor-specialist
- **Output**: Optimized code, refactor log entry
- **Commit**: `refactor(<ID>): improve code quality`
- **Gate**: Tests still green

### 1.7 REFACTOR → TEST-CONFIRM
- **Agent**: quality-assurance-tester
- **Output**: All tests passing
- **Gate**: Complete test suite green

### 1.8 TEST-CONFIRM → DONE
- **Agent**: tdd-orchestrator
- **Output**: Status DONE in MASTER-EPICS-USER-STORIES.md
- **Trigger**: DevOps Pipeline Orchestrator

## Phase 2: Deployment Pipeline (DevOps Pipeline Orchestrator)

### 2.1 BRANCH_MANAGEMENT
- Create/update feature branch
- Sync with main branch
- Resolve conflicts if any
- **Command**: `git checkout -b feature/<ID>`

### 2.2 COMMIT_ORCHESTRATION
- Ensure semantic commits
- Bundle related changes
- Sign commits if required
- **Command**: `git commit -m "feat(<ID>): description"`

### 2.3 PR_LIFECYCLE
- Create pull request
- Add comprehensive description
- Request reviews
- Monitor approval status
- **Command**: `gh pr create --title "[<ID>] Feature"`

### 2.4 CI_VALIDATION
- Run complete test suite
- Check code coverage (≥60%)
- Run security scans
- Validate linting
- **Commands**:
  - `pytest --cov=src`
  - `python -m ruff check`
  - `python -m black --check`

### 2.5 DEPLOYMENT_PREP
- Generate version number
- Create changelog
- Prepare rollback plan
- Validate environment

### 2.6 RELEASE_MANAGEMENT
- Create release tag
- Generate release notes
- Create GitHub release
- **Command**: `git tag -a v<version>`

### 2.7 DEPLOYMENT
- Deploy to staging first
- Run health checks
- Deploy to production (with approval)
- Monitor deployment

### 2.8 POST_DEPLOYMENT
- Run smoke tests
- Monitor metrics
- Update documentation
- Notify team

## Integration Points

### Handoff from TDD to DevOps
When TDD Orchestrator reaches DONE:
1. TDD Orchestrator announces: "Story <ID> is DONE. Ready for DevOps Pipeline Orchestrator"
2. User triggers DevOps agent: `Task tool → devops-pipeline-orchestrator`
3. DevOps agent picks up story ID and begins deployment workflow

### Quality Gates
Each phase has strict gates that must pass:
- **TDD Gates**: Tests exist → Tests fail → Tests pass → Review passed
- **DevOps Gates**: CI passes → Coverage met → Approvals received → Health checks pass

### Rollback Triggers
Automatic rollback initiated when:
- Deployment health checks fail
- Smoke tests fail
- Error rate exceeds threshold
- Manual intervention requested

## Commands Reference

### TDD Phase Commands
```bash
# Run tests
pytest tests/unit/test_<ID>*.py
pytest tests/integration/test_<ID>*.py

# Check coverage
pytest --cov=src --cov-report=term-missing

# Lint and format
python -m ruff check src
python -m black src
```

### DevOps Phase Commands
```bash
# Git operations
git checkout -b feature/<ID>
git rebase main
git push --set-upstream origin feature/<ID>

# GitHub CLI
gh pr create --title "[<ID>] Title" --body "Description"
gh pr status
gh pr checks

# Release
git tag -a v<version> -m "Release v<version>"
gh release create v<version> --title "Release v<version>"

# Deployment
make deploy-staging
make deploy-production
```

## Error Handling

### TDD Phase Failures
- **Test failures**: Fix code and re-run
- **Review blocks**: Address feedback
- **Refactor breaks**: Revert and retry

### DevOps Phase Failures
- **CI failures**: Fix issues and re-push
- **Deployment failures**: Automatic rollback
- **Post-deploy issues**: Monitor and hotfix

## Best Practices

1. **Never skip TDD phases** - Each phase ensures quality
2. **Atomic commits** - One logical change per commit
3. **Comprehensive PR descriptions** - Include context and testing notes
4. **Stage before production** - Always test in staging first
5. **Monitor after deployment** - Watch metrics for 30 minutes post-deploy

## Example Workflow

```bash
# TDD Orchestrator completes story US-123
> "Story US-123 is DONE. Ready for DevOps Pipeline Orchestrator"

# Trigger DevOps Pipeline
> Task tool → devops-pipeline-orchestrator
> Input: "Deploy story US-123 to production"

# DevOps Pipeline executes:
1. Creates branch feature/US-123
2. Creates PR #456
3. CI runs and passes
4. PR approved by reviewer
5. Merges to main
6. Creates release v1.2.3
7. Deploys to staging
8. Runs smoke tests
9. Deploys to production
10. Monitors health

# Result
> "US-123 successfully deployed to production as v1.2.3"
```

## Monitoring & Metrics

Track these metrics across the workflow:
- **Lead time**: TODO → Production
- **Cycle time**: DEV-GREEN → Production
- **Test coverage**: Must maintain ≥60%
- **Deployment frequency**: Releases per week
- **MTTR**: Time to recover from failures
- **Change failure rate**: Failed deployments / total

## Documentation Updates

After deployment, update:
- `CHANGELOG.md` - Release notes
- `docs/deployments/` - Deployment record
- `README.md` - Version number
- `docs/stories/MASTER-EPICS-USER-STORIES.md` - Mark as DEPLOYED
