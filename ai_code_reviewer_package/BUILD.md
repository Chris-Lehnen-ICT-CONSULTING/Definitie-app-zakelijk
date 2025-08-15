# AI Code Reviewer v2.0.0 - Build & Publicatie Instructies

## 🏗️ Package Build Process

### Pre-build Checklist

- [ ] `__version__` in `__init__.py` is `"2.0.0"`
- [ ] README.md bevat v2.0.0 features
- [ ] CHANGELOG is bijgewerkt
- [ ] Alle tests passed
- [ ] Code review cycle succesvol

### 1. Build Environment Setup

```bash
cd ai_code_reviewer_package/

# Install build dependencies
pip install --upgrade pip build twine

# Verify tools
python -m build --version
python -m twine --version
```

### 2. Clean Previous Builds

```bash
# Remove old distributions
rm -rf dist/ build/ *.egg-info/

# Clean Python cache
find . -type d -name __pycache__ -delete
find . -name "*.pyc" -delete
```

### 3. Build Package

```bash
# Build both source distribution and wheel
python -m build

# Verify build output
ls -la dist/
# Verwacht: 
# - ai_code_reviewer-2.0.0.tar.gz
# - ai_code_reviewer-2.0.0-py3-none-any.whl
```

### 4. Local Testing

```bash
# Create test environment
python -m venv test_env
source test_env/bin/activate  # Linux/Mac
# test_env\Scripts\activate  # Windows

# Install from wheel
pip install dist/ai_code_reviewer-2.0.0-py3-none-any.whl

# Test CLI
ai-code-review --version
ai-code-review --help
ai-code-review test-hook --ai-agent TestAgent

# Test import
python -c "from ai_code_reviewer import AICodeReviewer; print('Import successful')"

# Cleanup
deactivate
rm -rf test_env/
```

## 📤 Publicatie naar PyPI

### Test PyPI (Aanbevolen Eerst)

```bash
# Upload naar Test PyPI
python -m twine upload --repository testpypi dist/*

# Test installatie vanaf Test PyPI
pip install --index-url https://test.pypi.org/simple/ ai-code-reviewer==2.0.0

# Verify test installatie
ai-code-review --version
```

### Productie PyPI

```bash
# Upload naar PyPI
python -m twine upload dist/*

# Verify op PyPI
# https://pypi.org/project/ai-code-reviewer/
```

### PyPI Credentials Setup

**Via environment variables:**
```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-AgENdGVzdC5weXBpLm9yZy...
```

**Via .pypirc file:**
```ini
[distutils]
index-servers = pypi testpypi

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = pypi-AgENdGVzdC5weXBpLm9yZy...

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-AgENdGVzdC5weXBpLm9yZy...
```

## 🧪 Post-Publication Testing

### User Installation Testing

```bash
# Fresh environment test
python -m venv fresh_test
source fresh_test/bin/activate

# Install from PyPI
pip install ai-code-reviewer

# Full workflow test
mkdir test_project && cd test_project
ai-code-review setup --install-templates
echo "print('test')" > test.py
ai-code-review

# Cleanup
deactivate && rm -rf fresh_test/
```

### Framework-Specific Testing

**Streamlit Test:**
```bash
pip install ai-code-reviewer[streamlit]
ai-code-review setup --framework streamlit
```

**BMAD Integration Test:**
```bash
# Create .bmad-core structure
mkdir -p .bmad-core/utils
ai-code-review init-bmad
ai-code-review test-hook --ai-agent TestAgent
```

## 🔄 Continuous Integration Setup

### GitHub Actions Workflow

```yaml
# .github/workflows/build-publish.yml
name: Build and Publish

on:
  push:
    tags: ['v*']
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
          
      - name: Install dependencies
        run: |
          pip install --upgrade pip build twine
          
      - name: Build package
        run: python -m build
        
      - name: Test package
        run: |
          pip install dist/*.whl
          ai-code-review --version
          
      - name: Publish to Test PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.TEST_PYPI_API_TOKEN }}
        run: python -m twine upload --repository testpypi dist/*
        
      - name: Publish to PyPI
        if: startsWith(github.ref, 'refs/tags/v')
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: python -m twine upload dist/*
```

## 📊 Quality Checks

### Pre-publish Validation

```bash
# Run package linting
python -m ruff check ai_code_reviewer/

# Run security scan
python -m bandit -r ai_code_reviewer/

# Check package metadata
python setup.py check --metadata --strict

# Validate wheel
python -m pip install check-wheel-contents
check-wheel-contents dist/*.whl
```

### Documentation Validation

```bash
# Check README renders correctly on PyPI
python -m pip install readme_renderer
python -m readme_renderer README.md -o /tmp/readme.html

# Validate package description
twine check dist/*
```

## 🚀 Release Workflow

### 1. Version Bump

```bash
# Update version in __init__.py
sed -i 's/__version__ = ".*"/__version__ = "2.0.1"/' ai_code_reviewer/__init__.py

# Update CHANGELOG.md
echo "### v2.0.1" >> CHANGELOG.md
```

### 2. Git Tagging

```bash
# Commit version changes
git add ai_code_reviewer/__init__.py CHANGELOG.md
git commit -m "Release v2.0.1"

# Create and push tag
git tag v2.0.1
git push origin v2.0.1
```

### 3. Automated Build

GitHub Actions wordt automatisch getriggerd door de tag en:
1. Bouwt het package
2. Test de installatie
3. Publiceert naar Test PyPI
4. Publiceert naar PyPI (bij tag)

## 🔧 Troubleshooting Build Issues

### Common Problems

**Missing dependencies:**
```bash
pip install --upgrade setuptools wheel
```

**Twine upload errors:**
```bash
# Check credentials
twine check dist/*

# Verbose upload
twine upload --verbose dist/*
```

**Import errors na installatie:**
```bash
# Check package structure
tar -tzf dist/*.tar.gz | head -20

# Validate wheel
python -m zipfile -l dist/*.whl
```

### Build Environment Issues

**Windows specifieke fixes:**
```bash
# Use long path support
pip install --user ai-code-reviewer
```

**Permission issues:**
```bash
# Use user install
pip install --user build twine
python -m build --wheel --outdir dist/
```

## 📈 Monitoring & Updates

### Package Health Monitoring

- PyPI download statistics
- GitHub Issues voor bug reports
- User feedback via documentation

### Continuous Updates

```bash
# Regular dependency updates
pip-review --auto

# Security updates
pip-audit

# Version compatibility testing
tox
```

Deze build procedure zorgt ervoor dat je AI code review methodiek professioneel gedistribueerd kan worden en gebruikers altijd de laatste verbeteringen krijgen! 🚀