# 🔄 Code Review Workflow Guide

## Overview

This document describes the complete code review workflow from creating a PR to merging code. It serves as a practical guide for both authors and reviewers.

## 👤 For PR Authors

### Before Creating a PR

#### 1. Self-Review Checklist
```bash
# Run all quality checks locally
make quality

# Verify specific areas
make lint      # Code style
make test      # All tests pass
make coverage  # Coverage ≥ 80%
make security  # No vulnerabilities
```

#### 2. Pre-PR Questions
- [ ] Does my code follow the project's architecture?
- [ ] Have I added/updated tests?
- [ ] Is the documentation updated?
- [ ] Have I checked for security implications?
- [ ] Will this change break existing functionality?

#### 3. Prepare Your Branch
```bash
# Ensure branch is up to date
git checkout main
git pull origin main
git checkout feature/your-feature
git rebase main

# Clean up commits (optional but recommended)
git rebase -i main
```

### Creating the PR

#### PR Title Format
```
<type>(<scope>): <subject>

Types: feat, fix, docs, style, refactor, perf, test, chore
Scope: component or area affected
Subject: imperative mood, lowercase, no period
```

Examples:
- `feat(auth): add two-factor authentication`
- `fix(api): handle null values in response`
- `refactor(database): optimize query performance`

#### PR Description Template
```markdown
## Description
Brief description of what this PR does and why.

## Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Changes Made
- Bullet point list of specific changes
- Include technical details where relevant
- Mention any algorithms or approaches used

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

### Test Evidence
```bash
# Include test output or screenshots
pytest tests/test_new_feature.py -v
# Output showing tests pass
```

## Breaking Changes
List any breaking changes and migration steps required.

## Checklist
- [ ] My code follows the project style guidelines
- [ ] I have performed a self-review
- [ ] I have commented my code where necessary
- [ ] I have updated the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix/feature works
- [ ] New and existing unit tests pass locally
- [ ] Any dependent changes have been merged

## Related Issues
Closes #123
Relates to #456

## Screenshots (if applicable)
Add screenshots for UI changes
```

### After Creating the PR

1. **Monitor CI/CD Checks**
   - Fix any failing automated checks immediately
   - Don't wait for review if CI is red

2. **Be Responsive**
   - Check for feedback at least twice daily
   - Respond to all comments (even if just with 👍)
   - Ask for clarification if feedback is unclear

3. **Update Efficiently**
   ```bash
   # Add new commits for review feedback
   git add .
   git commit -m "address review feedback: <specific change>"

   # After approval, squash if requested
   git rebase -i main
   ```

## 👥 For Reviewers

### Review Preparation

1. **Understand Context**
   - Read PR description thoroughly
   - Check linked issues
   - Review commit messages
   - Understand the why, not just the what

2. **Set Up Locally (for complex changes)**
   ```bash
   # Fetch and checkout PR branch
   git fetch origin pull/123/head:pr-123
   git checkout pr-123

   # Run tests locally
   make test
   ```

### Review Process

#### 1. Automated Checks First
Before diving into code:
- ✅ CI/CD passing?
- ✅ Test coverage adequate?
- ✅ No security warnings?
- ✅ Linting clean?

#### 2. High-Level Review (5 minutes)
- Architecture alignment
- Design patterns appropriateness
- Breaking changes identified
- Performance implications

#### 3. Detailed Code Review (using protocol)
Follow the phases from [Code Review Protocol](CODE_REVIEW_PROTOCOL.md):
1. **Phase 1-2**: Structure & Dependencies (5-15 min)
2. **Phase 3-4**: Functionality & Integration (20-35 min)
3. **Phase 5-7**: Tests, Security, Quality (10-35 min)

#### 4. Leaving Feedback

##### Comment Format
```python
# 🔴 BLOCKING: Must fix before merge
# Clear explanation of the issue
# Suggestion for how to fix
# Link to documentation if relevant

# 🟡 IMPORTANT: Should fix, but not blocking
# Explanation of concern
# Impact if not addressed

# 🟢 SUGGESTION: Consider for improvement
# Optional enhancement idea

# 💡 QUESTION: Seeking clarification
# Not a criticism, genuinely curious

# 👍 PRAISE: Highlight good work
# Positive reinforcement matters!
```

##### Effective Feedback Examples

**Good Feedback:**
```python
# 🔴 BLOCKING: SQL Injection vulnerability
# The user input 'search_term' is directly interpolated into the SQL query.
# This allows SQL injection attacks.
#
# Suggested fix:
# query = "SELECT * FROM items WHERE name = %s"
# cursor.execute(query, (search_term,))
#
# See: https://owasp.org/www-community/attacks/SQL_Injection
```

**Poor Feedback:**
```python
# This is wrong
# (No explanation, no suggestion)
```

### Review Checklist

#### Security (CRITICAL)
- [ ] No hardcoded secrets/credentials
- [ ] Input validation present
- [ ] SQL queries parameterized
- [ ] Authentication/authorization correct
- [ ] No unsafe operations (eval, exec)

#### Functionality
- [ ] Code does what PR claims
- [ ] Edge cases handled
- [ ] Error handling appropriate
- [ ] Backwards compatibility maintained

#### Code Quality
- [ ] Clear naming conventions
- [ ] No code duplication
- [ ] Appropriate abstractions
- [ ] SOLID principles followed

#### Testing
- [ ] Tests cover new functionality
- [ ] Tests are meaningful (not just coverage)
- [ ] Edge cases tested
- [ ] Mocks used appropriately

#### Performance
- [ ] No obvious bottlenecks
- [ ] Database queries optimized
- [ ] Caching used where appropriate
- [ ] Memory usage reasonable

### After Review

1. **Summarize Decision**
   ```markdown
   ## Review Summary
   ✅ Approved with minor suggestions

   Great implementation of the feature! A few non-blocking suggestions above.
   The SQL injection issue must be fixed before merge, but otherwise looks good.

   Please address the blocking issue and consider the suggestions.
   ```

2. **Set Appropriate Status**
   - ✅ **Approve**: Ready to merge after CI passes
   - 💬 **Comment**: Feedback provided, re-review not needed
   - ❌ **Request Changes**: Blocking issues must be addressed

## 📊 Review Metrics & Goals

### For Authors
- **PR Size**: < 400 lines changed (prefer smaller PRs)
- **Response Time**: < 4 hours during work hours
- **Iteration Count**: Aim for approval in ≤ 2 rounds

### For Reviewers
- **Initial Response**: < 24 hours (target < 4 hours)
- **Review Thoroughness**: Cover all checklist items
- **Feedback Quality**: 80% actionable, 20% educational

## 🔄 Special Scenarios

### Hotfixes
```bash
# For critical production issues
git checkout -b hotfix/critical-issue main
# Make minimal fix
# PR title: "hotfix: <description>"
# Tag reviewers immediately
# Can merge with 1 approval + passing CI
```

### Large PRs
- Break into smaller PRs if possible
- If not, provide review guide:
  ```markdown
  ## Review Guide
  1. Start with src/auth/* - new authentication logic
  2. Then src/api/* - API changes to support auth
  3. Finally tests/* - comprehensive test suite

  Key decisions:
  - Used JWT for stateless auth (see auth/jwt.py)
  - Added rate limiting (see api/middleware.py)
  ```

### Conflicting Opinions
1. Discuss in PR comments
2. If unresolved, schedule sync discussion
3. Document decision in PR
4. Create ADR if architectural decision

## 🎯 Best Practices

### For Everyone
- **Be Kind**: We're all on the same team
- **Be Specific**: Vague feedback helps no one
- **Be Timely**: Blocked PRs block progress
- **Be Learning**: Every review is a learning opportunity

### Common Anti-patterns to Avoid
- ❌ Nitpicking on style (use linters)
- ❌ Scope creep ("while you're at it...")
- ❌ Demanding perfection for non-critical code
- ❌ Leaving "fix this" without explanation
- ❌ Ignoring PR for days

### Pro Tips
- 💡 Review in IDE for complex changes
- 💡 Use GitHub suggested changes for simple fixes
- 💡 Batch comments before submitting
- 💡 Check reviewer's other comments first
- 💡 Appreciate good code when you see it

## 📚 Additional Resources

- [Code Review Protocol](CODE_REVIEW_PROTOCOL.md) - Detailed review phases
- [Quick Reference Card](./code-review-quick-reference.md) - Common issues
- [Automated Review Setup](./automated-review-setup.md) - Tool configuration
- [Google's Code Review Guide](https://google.github.io/eng-practices/review/)

---

*Remember: The goal is to ship quality code efficiently, not to achieve perfection!*
