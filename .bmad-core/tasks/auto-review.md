# auto-review

## Auto Code Review Task voor Quinn Agent

**Doel**: Voer automatisch volledige AI code review loop uit om alle code quality issues op te lossen.

### Task Flow:

#### Stap 1: Setup AI Agent Environment
```bash
export AI_AGENT_COMMIT=1
export AI_AGENT_NAME="Quinn"
```

#### Stap 2: Run AI Code Review Loop
```bash
python scripts/ai_code_reviewer.py --max-iterations 5 --ai-agent Quinn
```

#### Stap 3: Analyseer Resultaten
- Check review_report.md voor remaining issues
- Log performance metrics naar console
- Rapporteer success/failure status

#### Stap 4: Commit Changes (indien succesvol)
```bash
git add .
git commit -m "🧪 Quinn: Automated code quality fixes

- Fixed all BLOCKING security issues
- Applied auto-fixes for formatting and linting
- Resolved undefined names and import issues
- Improved code quality metrics

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Success Criteria:
- ✅ Alle BLOCKING issues opgelost
- ✅ IMPORTANT issues geminimaliseerd
- ✅ Auto-fixes succesvol toegepast
- ✅ Geen runtime crashes door undefined names
- ✅ Security vulnerabilities gepatched

### Output:
- Updated code files met quality improvements
- Comprehensive review rapport
- Metrics van performance
- Git commit met alle changes

### Fout Handling:
Als AI review loop faalt:
1. Rapporteer specifieke blocking issues
2. Geef handmatige fix suggesties
3. Log detailed error informatie
4. Stop commit proces tot issues resolved

**CRITICAL**: Deze task MOET automatisch uitgevoerd worden wanneer Quinn code quality issues aanpakt.
