# Execute Code Review

Execute a comprehensive code review following the 7-phase protocol with AI-powered auto-fix capabilities.

## Task Configuration
```yaml
type: review
complexity: high
estimated_time: 30-60 minutes
requires_interaction: true
ai_enhanced: true
```

## Prerequisites
- Python development tools installed (ruff, black, mypy, bandit)
- Access to source code
- Optional: AI agent configured

## Execution Steps

### 1. Initialize Review Session
```bash
# Ensure we're in the project root
cd /Users/chrislehnen/Projecten/Definitie-app

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️ Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install development dependencies
echo "📦 Installing development dependencies..."
pip install -r requirements-dev.txt

# Check required tools
which ruff black mypy bandit || echo "⚠️ Some tools missing"
```

### 2. Select Review Scope
**What would you like to review?**
- [ ] Specific story/component
- [ ] Recent changes (git diff)
- [ ] Full codebase scan
- [ ] Custom file selection

### 3. Run Automated Review
```bash
# Execute the AI Code Reviewer
python scripts/ai_code_reviewer.py \
  --max-iterations 5 \
  --project-root . \
  --ai-agent "${AI_AGENT:-manual}"
```

### 4. Review Protocol Phases

#### Phase 1: Quick Existence Check (5 min)
- ✓ Files exist and are accessible
- ✓ No syntax errors
- ✓ Documentation present
- ✓ Type hints included

#### Phase 2: Dependency Analysis (10 min)
- ✓ All imports resolve
- ✓ No circular dependencies
- ✓ Version compatibility
- ✓ Proper dependency injection

#### Phase 3: Functionality Test (20 min)
- ✓ Code runs without errors
- ✓ Happy path works
- ✓ Edge cases handled
- ✓ Error handling present

#### Phase 4: Integration Check (15 min)
- ✓ Integrates with other components
- ✓ Interfaces properly used
- ✓ Data flow correct
- ✓ Side effects managed

#### Phase 5: Test Suite Verification (10 min)
- ✓ Tests run successfully
- ✓ Coverage adequate (≥80%)
- ✓ No skipped tests
- ✓ Meaningful assertions

#### Phase 6: Security & Performance (15 min)
**Security Checks:**
- ✓ Input validation complete
- ✓ No SQL injection risks
- ✓ Authentication/authorization correct
- ✓ Secrets properly managed

**Performance Checks:**
- ✓ Database queries optimized
- ✓ No N+1 problems
- ✓ Caching implemented
- ✓ Async where needed

#### Phase 7: Code Quality Metrics (10 min)
- ✓ Cyclomatic complexity < 10
- ✓ Method length < 50 lines
- ✓ DRY principle followed
- ✓ SOLID principles applied

### 5. Process Review Results

The AI Code Reviewer will:
1. **Auto-fix** formatting and linting issues
2. **Generate feedback** for complex issues
3. **Create report** with all findings
4. **Update metrics** for tracking

### 6. Update Story/Documentation

Based on review results, update:
- [ ] QA Results section in story file
- [ ] Technical debt log
- [ ] Team knowledge base
- [ ] Review metrics dashboard

## Review Output Format

```markdown
# Component: [Name]
**Review Date**: [YYYY-MM-DD]
**Reviewer**: Quinn (AI-Enhanced)
**Protocol Version**: 2.0
**Status**: [PASSED/FAILED/PARTIAL]

## Risk Assessment
- **Business Impact**: [HIGH/MEDIUM/LOW]
- **Security Risk**: [CRITICAL/HIGH/MEDIUM/LOW]
- **Technical Debt**: €[amount]
- **Performance Impact**: [metrics]

## Findings

### ✅ What Works
- [List with metrics]

### ❌ What Doesn't Work
- [List with root cause]

### ⚠️ Partially Working
- [With specific conditions]

## Action Items
1. 🔴 **CRITICAL**: [Security/data loss issues]
2. 🟠 **HIGH**: [Business blocking issues]
3. 🟡 **MEDIUM**: [Performance/UX issues]
4. 🟢 **LOW**: [Technical debt items]
```

## Integration with BMAD Workflow

This task integrates with:
- `create-doc` task for generating review reports
- `review-story` task for story-specific reviews
- Technical preferences from `data/technical-preferences.md`

## Automation Scripts

### Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit
if [ -n "$AI_AGENT_COMMIT" ]; then
    echo "🤖 AI Agent commit detected..."
    python scripts/ai_code_reviewer.py --max-iterations 3
fi
```

### CI/CD Integration
```yaml
# .github/workflows/ai-review.yml
name: AI Code Review
on: [pull_request]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run AI Review
        run: |
          pip install -r requirements-dev.txt
          python scripts/ai_code_reviewer.py
```

## Success Criteria

Review is complete when:
- [ ] All blocking issues resolved
- [ ] Auto-fixes applied where possible
- [ ] Report generated and saved
- [ ] Metrics updated
- [ ] Story/docs updated with results

## Tips & Tricks

1. **For faster reviews**: Focus on changed files only
2. **For thorough reviews**: Run full codebase scan monthly
3. **For AI agents**: Provide clear context in prompts
4. **For teams**: Share review reports in standups

---

*Remember: The goal is continuous improvement, not perfection!*
