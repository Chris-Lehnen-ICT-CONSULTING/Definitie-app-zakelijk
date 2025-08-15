# AI Code Reviewer v2.0.0 - Gebruikshandleiding

## 🆕 Nieuw in v2.0.0

- **Universal BMAD Post-Edit Hooks**: Automatische code review na elke wijziging door BMAD agents
- **Enhanced Security Scanning**: Verbeterde SQL injection detectie met context-aware filtering  
- **AI Agent Auto-Detection**: Automatische herkenning van Claude Code, Copilot, en BMAD agents
- **Hook Testing**: Nieuwe `test-hook` command voor BMAD functionaliteit
- **Extended Context**: 100+ character context window voor betere false positive filtering

## 📦 Installatie en Setup

### 1. Package Installeren

```bash
pip install ai-code-reviewer
```

### 2. Project Setup

```bash
# Ga naar je project directory
cd /path/to/your/project

# Setup AI code review
ai-code-review setup --install-templates --setup-hooks
```

Dit creëert:
- `.ai-review-config.yaml` - Project configuratie
- `.pre-commit-config.yaml` - Git hooks configuratie  
- `pyproject.toml` - Tool configuratie (indien niet aanwezig)

## 🚀 Basis Gebruik

### Code Review Uitvoeren

```bash
# Basic review
ai-code-review

# Met specifieke instellingen
ai-code-review --max-iterations 3 --framework django

# Met custom config
ai-code-review --config my-config.yaml
```

### BMAD Integratie (v2.0.0)

```bash
# Setup BMAD integratie
ai-code-review init-bmad

# Test post-edit hooks
ai-code-review test-hook --ai-agent Quinn

# In BMAD gebruik dan:
*execute-code-review
```

**Nieuwe Post-Edit Hooks**: Alle BMAD agents triggeren nu automatisch code review na Edit/MultiEdit operaties!

## ⚙️ Configuratie

### Project Configuratie (`.ai-review-config.yaml`)

```yaml
# Basis instellingen
max_iterations: 5
source_dirs: ["src/"]
framework: "streamlit"  # streamlit, django, flask, generic

# Custom checks
custom_checks: true
custom_check_types:
  - "sql_safety"
  - "framework_patterns" 
  - "docstring_language"

# Taal instellingen
docstring_language: "dutch"  # dutch, english

# False positive filters
false_positive_filters:
  - "logger."
  - "print("
  - "st.error"
```

### Framework-Specifieke Setup

**Django:**
```yaml
framework: "django"
source_dirs: ["."]
custom_check_types: ["sql_safety", "django_patterns"]
docstring_language: "english"
```

**Flask:**
```yaml
framework: "flask"
source_dirs: ["."] 
custom_check_types: ["sql_safety", "flask_patterns"]
docstring_language: "english"
```

**Streamlit:**
```yaml
framework: "streamlit"
source_dirs: ["src/"]
custom_check_types: ["sql_safety", "streamlit_patterns"]
docstring_language: "dutch"
```

## 🔄 Auto-Update Systeem

```bash
# Check voor updates
ai-code-review update --check-only

# Update naar laatste versie
ai-code-review update
```

Het systeem toont automatisch meldingen wanneer er nieuwe versies beschikbaar zijn.

## 🎯 Voor Verschillende Projecten

### Nieuwe Project Setup

```bash
# 1. Ga naar project
cd /path/to/new/project

# 2. Setup AI review
ai-code-review setup --install-templates --setup-hooks

# 3. Run eerste review
ai-code-review

# 4. Commit configuratie
git add .ai-review-config.yaml .pre-commit-config.yaml
git commit -m "Add AI code review configuration"
```

### Bestaand Project Migratie

```bash
# 1. Install package
pip install ai-code-reviewer

# 2. Run setup (detecteert automatisch framework)
ai-code-review setup --install-templates

# 3. Pas configuratie aan voor jouw project
nano .ai-review-config.yaml

# 4. Test run
ai-code-review --max-iterations 1

# 5. Setup git hooks  
ai-code-review setup --setup-hooks
```

## 📊 Output en Rapportage

### Review Rapport

Na elke review wordt `review_report.md` gegenereerd:

```markdown
# 🤖 AI Code Review Report

**Status**: ✅ PASSED
**Iterations**: 2  
**Auto-fixes Applied**: 5
**Duration**: 8.3 seconds

## Issues Fixed
- Ruff: 3 linting issues
- Black: 2 formatting issues

## Metrics  
- Review efficiency: 100%
- Zero blocking issues
```

### Exit Codes

- `0` = Review passed, geen issues
- `1` = Review failed, issues gevonden

## 🔧 Advanced Features

### Programmatic Usage

```python
from ai_code_reviewer import AICodeReviewer
import asyncio

config = {
    'max_iterations': 3,
    'source_dirs': ['src/'],
    'framework': 'django',
    'custom_checks': True
}

reviewer = AICodeReviever(project_root=".", config=config)
result = asyncio.run(reviewer.run_review_cycle())

print(f"Passed: {result.passed}")
print(f"Issues: {len(result.issues)}")
```

### CI/CD Integratie

**GitHub Actions:**
```yaml
- name: AI Code Review
  run: |
    pip install ai-code-reviewer
    ai-code-review --ai-agent "github-actions"
```

**GitLab CI:**
```yaml
code-review:
  script:
    - pip install ai-code-reviewer  
    - ai-code-review --ai-agent "gitlab-ci"
```

## 🎭 BMAD Method Integratie

### Setup

```bash
ai-code-review init-bmad
```

Dit creëert:
- `.bmad-core/tasks/execute-code-review.md`
- `.bmad-core/config/agent-environment.sh`
- `.bmad-core/init.sh`

### Agent Detectie

Het systeem detecteert automatisch:
- **Claude Code**: `"claude"`
- **GitHub Copilot**: `"copilot"`
- **Quinn BMAD**: `"quinn"`
- **Fallback**: `"bmad-agent"`

### Usage in BMAD

```
*execute-code-review
```

Agent voert automatisch uit:
1. Quality checks
2. Auto-fixes waar mogelijk
3. Rapport generatie
4. Feedback voor remaining issues

## 🐛 Troubleshooting

### Veelvoorkomende Problemen

**"Tools not found"**
```bash
pip install ruff black mypy bandit
```

**"No source directories"**
```yaml
# In .ai-review-config.yaml
source_dirs: [".", "src/", "app/"]
```

**Git hooks werken niet**
```bash
ai-code-review setup --setup-hooks
chmod +x .git/hooks/pre-commit
```

**Config problemen**
```bash
ai-code-review setup --install-templates
```

### Debug Mode

```bash
ai-code-review --verbose
```

## 📈 Metrics en Performance  

### Review Metrics

- **Efficiency**: Percentage auto-fixed issues
- **Speed**: Review duration in seconds
- **Coverage**: Files/directories scanned
- **Quality**: Issues per category

### Performance Tips

1. **Scope beperken**: Gebruik specifieke `source_dirs`
2. **Tools optimaliseren**: Gebruik `.ruff.toml` voor project specifics
3. **False positives**: Tune `false_positive_filters`
4. **Max iterations**: Lower voor snellere reviews

## 🔄 Updates en Maintenance

### Auto-Update Workflow

1. Systeem check elke run voor updates
2. Melding bij nieuwe versie
3. `ai-code-review update` om te upgraden
4. Backwards compatibility gegarandeerd

### Package Onderhoud

- **Versioning**: Semantic versioning
- **Changelog**: Alle wijzigingen gedocumenteerd  
- **Migration**: Automatische config migratie
- **Support**: GitHub issues voor hulp

Dit package maakt het mogelijk om je code review methodiek eenvoudig te distribueren en up-to-date te houden!