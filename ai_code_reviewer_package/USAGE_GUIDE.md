# AI Code Reviewer - Gebruikshandleiding

## Installatie in Nieuw Project

### 1. Basis Installatie

```bash
# Ga naar je project
cd /pad/naar/jouw/project

# Installeer vanaf Definitie-app
pip install -e /Users/chrislehnen/Projecten/Definitie-app/ai_code_reviewer_package
```

### 2. Project Setup

```bash
# Initialiseer AI review
ai-code-review setup

# Dit creëert .ai-review-config.yaml met detectie van:
# - Framework (Django/Flask/Streamlit/etc)
# - Source directories
# - Standaard configuratie
```

## Dagelijks Gebruik

### Basis Code Review

```bash
# Run review in huidige directory
ai-code-review

# Of expliciet
ai-code-review review
```

### Met Opties

```bash
# Limiteer iteraties
ai-code-review --max-iterations 3

# Specificeer directories
ai-code-review --source-dirs src/ lib/ tests/

# Kies framework checks
ai-code-review --framework django
```

## Configuratie Aanpassen

Edit `.ai-review-config.yaml`:

```yaml
# Voorbeeld voor Django project
max_iterations: 5
source_dirs:
  - apps/
  - core/
  - utils/
custom_checks: true
docstring_language: dutch  # of english
framework: django
custom_check_types:
  - sql_safety
  - docstring_language
  - framework_patterns
false_positive_filters:
  - logger.
  - log.
  - print(
  - errors.append
```

## BMAD Integratie

Voor projecten met BMAD:

```bash
# Setup BMAD integratie
ai-code-review init-bmad

# Test de hook
ai-code-review test-hook --ai-agent MyAgent
```

## Updates

### Quick Update Script

1. Kopieer script naar je project:
```bash
cp /Users/chrislehnen/Projecten/Definitie-app/ai_code_reviewer_package/quick-update.sh .
```

2. Update wanneer nodig:
```bash
./quick-update.sh
```

### Alternatief: Direct Update

```bash
# Herinstalleer vanaf source
pip install -e /Users/chrislehnen/Projecten/Definitie-app/ai_code_reviewer_package --upgrade
```

## Workflow Voorbeelden

### 1. Voor Nieuwe Feature

```bash
# Schrijf je code
# ...

# Check kwaliteit
ai-code-review

# AI fixt automatisch issues
# Review de changes
git diff

# Commit als tevreden
git add .
git commit -m "feat: nieuwe feature met AI review"
```

### 2. Pre-Commit Hook

Voeg aan `.git/hooks/pre-commit`:

```bash
#!/bin/bash
echo "Running AI Code Review..."
ai-code-review --max-iterations 3
```

### 3. CI/CD Pipeline

In GitHub Actions:

```yaml
- name: AI Code Review
  run: |
    pip install -e ./ai_code_reviewer_package
    ai-code-review --max-iterations 5
```

## Troubleshooting

### Package niet gevonden?
```bash
# Check installatie
pip list | grep ai-code-reviewer

# Herinstalleer
pip uninstall ai-code-reviewer
pip install -e /Users/chrislehnen/Projecten/Definitie-app/ai_code_reviewer_package
```

### Command niet gevonden?
```bash
# Check of scripts directory in PATH staat
which ai-code-review

# Voeg toe aan PATH indien nodig
export PATH="$PATH:$(python -m site --user-base)/bin"
```

### Review vindt geen files?
```bash
# Check config
cat .ai-review-config.yaml

# Pas source_dirs aan naar je project structuur
```