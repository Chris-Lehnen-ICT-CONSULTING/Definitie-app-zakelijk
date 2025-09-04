# Development Environment Setup for BMAD Agents

## Important: Two Requirements Files

This project uses two separate requirements files:

### requirements.txt
- **Purpose**: Production dependencies only
- **Used by**: End users, deployment, Docker
- **Contains**: streamlit, openai, pandas, etc.

### requirements-dev.txt
- **Purpose**: Development and testing tools
- **Used by**: Developers, CI/CD, code review
- **Contains**: pytest, ruff, black, mypy, pre-commit, etc.

## Setup Instructions for BMAD Agents

When starting development work, ALWAYS:

```bash
# 1. Create/activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install BOTH requirements files
pip install -r requirements.txt -r requirements-dev.txt
# OR just dev (includes main requirements)
pip install -r requirements-dev.txt

# 3. Install pre-commit hooks
pre-commit install

# 4. Verify tools are available
which ruff black pytest mypy
```

## Common Issues

1. **"ruff: command not found"** - You need to install requirements-dev.txt
2. **Pre-commit failing** - Run `pre-commit install` after pip install
3. **Import errors in tests** - Make sure PYTHONPATH includes project root

## For Story Development

Before running any linting or tests:
```bash
source venv/bin/activate
pip install -r requirements-dev.txt
```

This ensures all development tools are available for code quality checks.
