# review-and-fix-code

Automatically review code for quality issues and fix them iteratively until all checks pass.

## Purpose
Perform comprehensive code review with automatic fixing of issues where possible, using the AI-powered review system.

## Elicit
- context: What specific files or directories should I review? (leave empty for entire project)
- focus: Any specific types of issues to focus on? (security/performance/style/all)

## Instructions

1. **Initialize Review**
   ```bash
   export BMAD_AGENT_NAME="$AGENT_NAME"
   ./scripts/bmad-agent-review.sh check
   ```

2. **Analyze Results**
   - Read `.bmad/agent-fix-instructions.md`
   - Categorize issues by severity (BLOCKING → IMPORTANT → SUGGESTION)

3. **Fix Issues Iteratively**
   For each issue in order of severity:
   
   a. **SQL Injection (BLOCKING)**
      - Find all f-strings in SQL queries
      - Replace with parameterized queries
      - Use the pattern provided in fix instructions
   
   b. **Type Errors (IMPORTANT)**
      - Add missing type hints
      - Fix type mismatches
      - Import missing types
   
   c. **Unused Imports (IMPORTANT)**
      - Remove imports listed as F401
      - Verify no side effects
   
   d. **Code Style (SUGGESTION)**
      - Apply formatting fixes
      - Update docstrings to Dutch

4. **Verify Each Fix**
   After each category of fixes:
   ```bash
   ./scripts/bmad-agent-review.sh check
   ```

5. **Complete When Clean**
   Continue until:
   - All BLOCKING issues resolved
   - Most IMPORTANT issues fixed
   - Review passes or only SUGGESTIONS remain

## Success Criteria

- [ ] No BLOCKING issues remain
- [ ] IMPORTANT issues reduced by >80%
- [ ] All automated tests still pass
- [ ] No new issues introduced

## Example Session

```
Agent: Starting code review...
[Runs review script]
Found: 14 SQL injection, 23 type errors, 45 unused imports

Fixing SQL injections first...
[Edits files with SQL queries]

Verifying fixes...
[Runs review again]
SQL injections: 0 ✅

Fixing type errors...
[Adds type hints]

Final review...
All checks passed! ✅
```

## Notes

- Always fix BLOCKING issues first
- Run review after each category of fixes
- Maximum 5 iterations to prevent infinite loops
- Create commit after successful review