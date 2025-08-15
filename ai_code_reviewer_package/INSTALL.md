# AI Code Reviewer - Installatie Instructies

## 📦 Package Publicatie & Installatie

### Voor Package Ontwikkelaars

#### 1. Build Package Lokaal

```bash
cd ai_code_reviewer_package/

# Install build dependencies
pip install build twine

# Build package
python -m build
```

Dit creëert:
- `dist/ai_code_reviewer-2.0.0.tar.gz` (source distributie)
- `dist/ai_code_reviewer-2.0.0-py3-none-any.whl` (wheel distributie)

#### 2. Test Package Lokaal

```bash
# Install locally voor testen
pip install dist/ai_code_reviewer-2.0.0-py3-none-any.whl

# Test CLI
ai-code-review --help
ai-code-review test-hook --ai-agent TestAgent
```

#### 3. Upload naar PyPI

**Test PyPI (aanbevolen eerst):**
```bash
# Upload naar Test PyPI
python -m twine upload --repository testpypi dist/*

# Test installatie vanaf Test PyPI
pip install --index-url https://test.pypi.org/simple/ ai-code-reviewer
```

**Productie PyPI:**
```bash
# Upload naar PyPI
python -m twine upload dist/*
```

### Voor End Users

#### Basis Installatie

```bash
# Installeer vanaf PyPI
pip install ai-code-reviewer

# Verify installatie
ai-code-review --version
```

#### Development Installatie

```bash
# Met alle optionele dependencies
pip install ai-code-reviewer[all]

# Of specifieke framework support
pip install ai-code-reviewer[streamlit]
pip install ai-code-reviewer[dev]
```

#### Installatie voor Specifieke Frameworks

**Streamlit Projecten:**
```bash
pip install ai-code-reviewer[streamlit]
ai-code-review setup --framework streamlit
```

**Django Projecten:**
```bash
pip install ai-code-reviewer
ai-code-review setup --framework django
```

**Flask Projecten:**
```bash
pip install ai-code-reviewer  
ai-code-review setup --framework flask
```

## 🚀 Quick Start na Installatie

### 1. Setup Nieuw Project

```bash
cd your-project/
ai-code-review setup --install-templates --setup-hooks
```

### 2. Eerste Review

```bash
ai-code-review
```

### 3. BMAD Integratie (optioneel)

```bash
ai-code-review init-bmad
ai-code-review test-hook --ai-agent Quinn
```

## 🔄 Update Workflow

### Automatische Update Notificaties

Het package controleert automatisch op updates:

```bash
# Check voor updates
ai-code-review update --check-only

# Update naar laatste versie
ai-code-review update
```

### Manual Update

```bash
pip install --upgrade ai-code-reviewer
```

## 🏗️ Development Setup

Voor ontwikkelaars die willen bijdragen:

```bash
# Clone repository
git clone https://github.com/ChrisLehnen/ai-code-reviewer.git
cd ai-code-reviewer/

# Install in development mode
pip install -e .

# Install development dependencies  
pip install -e .[dev]

# Run tests
pytest

# Build package
python -m build
```

## 🔧 Tool Dependencies

Het package installeert automatisch alle benodigde tools:

- **ruff** (>=0.1.5) - Linting
- **black** (>=23.1.0) - Code formatting  
- **mypy** (>=1.0.0) - Type checking
- **bandit** (>=1.7.5) - Security scanning
- **pyyaml** (>=6.0) - Config parsing

## 🐛 Troubleshooting Installatie

### Common Issues

**Permission Errors:**
```bash
pip install --user ai-code-reviewer
```

**Tool Not Found:**
```bash
# Verify PATH
which ai-code-review

# Reinstall
pip uninstall ai-code-reviewer
pip install ai-code-reviewer
```

**Config Issues:**
```bash
# Reset config
ai-code-review setup --install-templates
```

### Platform-Specific

**Windows:**
```bash
# Use pip with --user flag
pip install --user ai-code-reviewer

# Add to PATH manually indien nodig
```

**macOS:**  
```bash
# Standard pip installatie werkt
pip install ai-code-reviewer

# Voor BMAD integratie, ensure bash available
which bash
```

**Linux:**
```bash
# Standard installatie
pip install ai-code-reviewer

# Voor system-wide installatie (sudo)  
sudo pip install ai-code-reviewer
```

## 📋 Verificatie Checklist

Na installatie, controleer:

- [ ] `ai-code-review --version` toont v2.0.0
- [ ] `ai-code-review --help` toont alle commands
- [ ] `ai-code-review setup` werkt in test directory
- [ ] `ruff --version` werkt (dependency check)
- [ ] `black --version` werkt (dependency check)
- [ ] `ai-code-review test-hook --ai-agent Test` werkt (BMAD check)

## 🔄 Continuous Integration

Voor CI/CD pipelines:

**GitHub Actions:**
```yaml
steps:
  - name: Install AI Code Reviewer
    run: pip install ai-code-reviewer
  
  - name: Run Code Review
    run: ai-code-review --ai-agent "github-actions"
```

**GitLab CI:**
```yaml
before_script:
  - pip install ai-code-reviewer

test:
  script:
    - ai-code-review --ai-agent "gitlab-ci"
```

**Azure DevOps:**
```yaml
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.8'
- script: |
    pip install ai-code-reviewer
    ai-code-review --ai-agent "azure-devops"
```

## 🏷️ Version Management

Het package volgt semantic versioning:

- **v2.x.x**: Major features, BMAD integration
- **v2.0.x**: Bug fixes, minor improvements
- **v2.x.0**: New features, backward compatible

Updates worden automatisch gedetecteerd tijdens runtime.