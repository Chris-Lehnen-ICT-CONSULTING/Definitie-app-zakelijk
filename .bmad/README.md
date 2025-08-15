# BMAD Integration with Code Review

## Automatic Code Review for BMAD Agents

All code changes made by BMAD agents automatically go through our code review and improvement loop.

### How it works:

1. **BMAD agent makes code changes**
2. **Post-code-change hook triggers** (`.bmad/hooks/post-code-change.sh`)
3. **Automatic review runs**:
   - Ruff linting
   - Black formatting  
   - MyPy type checking
   - Bandit security scan
   - Pytest execution
4. **If issues found**:
   - Auto-fix formatting (Black, Ruff)
   - Generate feedback for agent
   - Loop up to 5 times
5. **On success**: Changes are committed

### For BMAD Agent Developers:

To ensure your agent triggers the review:

```bash
# In your agent's code execution:
export BMAD_AGENT_NAME="YourAgentName"
export BMAD_COMMIT_MESSAGE="feat: implement feature X"

# Make code changes...

# Trigger the hook
.bmad/hooks/post-code-change.sh
```

### Manual Override:

If needed, bypass the review (use sparingly!):
```bash
export SKIP_AI_REVIEW=1
git commit -m "emergency: hotfix"
```

### Monitoring:

Check agent performance:
```bash
python scripts/ai-metrics-dashboard.py
```

---

*This ensures all BMAD-generated code meets our quality standards!*