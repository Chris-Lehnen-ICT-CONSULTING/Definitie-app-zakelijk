# 🤖 Automated Code Review Setup

## Overview

This guide helps you set up automated code review tools that catch common issues before human review, saving time and ensuring consistent quality standards.

## 🎯 Goals

- **Catch issues early**: Find problems during development, not in review
- **Consistent standards**: Automated enforcement of coding standards
- **Save review time**: Focus human review on logic and architecture
- **Fast feedback**: Get instant feedback while coding

## 📦 Tool Stack

### 1. Pre-commit Hooks
Runs checks before each commit locally.

```bash
# Install pre-commit
pip install pre-commit

# Install the git hook scripts
pre-commit install

# Run against all files (initial setup)
pre-commit run --all-files
```

### 2. Linting Tools

#### Ruff (Fast Python Linter)
```bash
# Install
pip install ruff

# Run linting
ruff check .

# Auto-fix issues
ruff check --fix .

# Watch mode during development
ruff check --watch .
```

#### Black (Code Formatter)
```bash
# Install
pip install black

# Format code
black .

# Check without modifying
black --check .

# See what would change
black --diff .
```

#### MyPy (Type Checker)
```bash
# Install
pip install mypy

# Run type checking
mypy src/

# Strict mode
mypy --strict src/

# Generate report
mypy --html-report mypy-report src/
```

### 3. Security Scanning

#### Bandit
```bash
# Install
pip install bandit

# Scan for security issues
bandit -r src/

# Skip specific tests
bandit -r src/ -s B101,B601

# Output format
bandit -r src/ -f json -o bandit-report.json
```

#### Safety (Dependency Vulnerabilities)
```bash
# Install
pip install safety

# Check dependencies
safety check

# Check requirements file
safety check -r requirements.txt

# Full report
safety check --full-report
```

### 4. Code Quality Tools

#### Pylint
```bash
# Install
pip install pylint

# Run analysis
pylint src/

# Generate report
pylint src/ --output-format=json > pylint-report.json
```

#### Coverage.py
```bash
# Install
pip install coverage

# Run tests with coverage
coverage run -m pytest

# Generate report
coverage report

# HTML report
coverage html
```

## 📝 Configuration Files

### `.pre-commit-config.yaml`
```yaml
# See https://pre-commit.com for more information
repos:
  # Python code formatting
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11

  # Python linting
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.11
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  # Type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--ignore-missing-imports]

  # Security scanning
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.6
    hooks:
      - id: bandit
        args: [-s, B101]

  # YAML/JSON/TOML formatting
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-yaml
      - id: check-json
      - id: check-toml
      - id: end-of-file-fixer
      - id: trailing-whitespace
      - id: check-merge-conflict
      - id: check-added-large-files

  # Dockerfile linting
  - repo: https://github.com/hadolint/hadolint
    rev: v2.12.0
    hooks:
      - id: hadolint

  # SQL formatting
  - repo: https://github.com/sqlfluff/sqlfluff
    rev: 3.0.0a5
    hooks:
      - id: sqlfluff-lint
      - id: sqlfluff-fix
```

### `pyproject.toml`
```toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  # Directories
  \.eggs
  | \.git
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

[tool.ruff]
target-version = "py311"
line-length = 88
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "C",   # flake8-comprehensions
    "B",   # flake8-bugbear
    "UP",  # pyupgrade
    "S",   # bandit
    "A",   # flake8-builtins
    "DTZ", # flake8-datetimez
    "ICN", # flake8-import-conventions
    "PIE", # flake8-pie
    "PT",  # flake8-pytest-style
    "RET", # flake8-return
    "SIM", # flake8-simplify
    "ARG", # flake8-unused-arguments
]
ignore = [
    "E501",  # line too long (handled by black)
    "B008",  # do not perform function calls in argument defaults
    "C901",  # too complex
]

[tool.ruff.per-file-ignores]
"tests/*" = ["S101"]  # allow assert in tests

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[tool.coverage.run]
branch = true
source = ["src"]

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
fail_under = 80

[tool.coverage.html]
directory = "htmlcov"

[tool.pylint.messages_control]
disable = [
    "C0111",  # missing-docstring
    "C0103",  # invalid-name
    "R0903",  # too-few-public-methods
    "R0913",  # too-many-arguments
    "W0621",  # redefined-outer-name
]

[tool.bandit]
exclude_dirs = ["tests", "venv"]
skips = ["B101", "B601"]
```

### `.github/workflows/code-quality.yml`
```yaml
name: Code Quality

on:
  pull_request:
    branches: [ main, develop ]
  push:
    branches: [ main, develop ]

jobs:
  quality:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11]

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Cache pip packages
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-dev.txt

    - name: Run pre-commit hooks
      run: pre-commit run --all-files

    - name: Run tests with coverage
      run: |
        coverage run -m pytest
        coverage xml

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella

    - name: Security scan with bandit
      run: bandit -r src/ -f json -o bandit-report.json

    - name: Upload bandit results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: bandit-report
        path: bandit-report.json

    - name: Check dependencies with safety
      run: safety check --json > safety-report.json
      continue-on-error: true

    - name: Upload safety results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: safety-report
        path: safety-report.json
```

## 🚀 IDE Integration

### VS Code Settings
```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.linting.mypyEnabled": true,
  "python.linting.banditEnabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackPath": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[python]": {
    "editor.rulers": [88],
    "editor.defaultFormatter": "ms-python.black-formatter"
  }
}
```

### PyCharm Setup
1. **Black**: Settings → Tools → External Tools → Add Black
2. **Ruff**: Settings → Tools → External Tools → Add Ruff
3. **File Watchers**: Settings → Tools → File Watchers → Add for Black/Ruff
4. **Inspections**: Settings → Editor → Inspections → Python → Enable all

## 📊 Quality Gates

### Minimum Requirements
- **Coverage**: ≥ 80% for new code
- **Security**: No HIGH or CRITICAL vulnerabilities
- **Type Coverage**: 100% of public APIs typed
- **Linting**: Zero errors, warnings reviewed
- **Tests**: All passing, no skipped tests

### Recommended Targets
- **Coverage**: ≥ 90% overall
- **Cyclomatic Complexity**: < 10 per function
- **Maintainability Index**: > 20
- **Technical Debt Ratio**: < 5%

## 🔧 Makefile Commands

Create a `Makefile` for easy access:

```makefile
.PHONY: install lint format type-check security test coverage clean

install:
	pip install -r requirements-dev.txt
	pre-commit install

lint:
	ruff check src/ tests/
	pylint src/

format:
	black src/ tests/
	ruff check --fix src/ tests/

type-check:
	mypy src/

security:
	bandit -r src/
	safety check

test:
	pytest tests/ -v

coverage:
	coverage run -m pytest
	coverage report
	coverage html

quality: lint type-check security test

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage htmlcov .mypy_cache .pytest_cache .ruff_cache

pre-commit:
	pre-commit run --all-files
```

## 🎯 Getting Started

1. **Install all tools**:
   ```bash
   make install
   ```

2. **Run initial quality check**:
   ```bash
   make quality
   ```

3. **Fix auto-fixable issues**:
   ```bash
   make format
   ```

4. **Set up IDE integration** (see above)

5. **Commit with confidence**:
   ```bash
   git add .
   git commit -m "feat: add new feature"  # pre-commit runs automatically
   ```

## 📈 Monitoring Progress

### Local Reports
- Coverage: `open htmlcov/index.html`
- MyPy: `open mypy-report/index.html`
- Bandit: Review `bandit-report.json`

### CI/CD Dashboard
- Check GitHub Actions tab for run results
- Review artifacts for detailed reports
- Monitor trends over time

## 🆘 Troubleshooting

### Pre-commit fails
```bash
# Skip hooks temporarily (use sparingly!)
git commit --no-verify

# Run specific hook
pre-commit run black --all-files

# Update hooks
pre-commit autoupdate
```

### Type checking issues
```bash
# Ignore specific line
result = untypable_function()  # type: ignore

# Reveal type for debugging
reveal_type(some_variable)  # mypy will show the inferred type
```

### Performance issues
```bash
# Run tools in parallel
make -j4 quality

# Use faster alternatives
ruff check src/  # Instead of pylint for quick checks
```

---

*Remember: Automated tools are helpers, not replacements for thoughtful code review!*
