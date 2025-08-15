#!/bin/bash
# Setup script voor AI Code Review systeem
# Installeert alle benodigde tools en configureert hooks

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Setting up AI Code Review System${NC}"
echo "=================================="

# Check Python version
echo -e "\n${BLUE}Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo -e "\n${BLUE}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "\n${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate

# Install required tools
echo -e "\n${BLUE}Installing development tools...${NC}"

# Create requirements-dev.txt if not exists
if [ ! -f "requirements-dev.txt" ]; then
    echo -e "${YELLOW}Creating requirements-dev.txt...${NC}"
    cat > requirements-dev.txt << EOF
# Code Quality Tools
ruff>=0.1.5
black>=23.1.0
mypy>=1.0.0
bandit[toml]>=1.7.5

# Testing
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-asyncio>=0.21.0

# Pre-commit
pre-commit>=3.5.0

# Metrics & Visualization
pandas>=2.0.0
streamlit>=1.28.0

# Type stubs
types-requests
types-python-dateutil
EOF
fi

# Install requirements
pip install -r requirements-dev.txt

# Setup pre-commit
echo -e "\n${BLUE}Setting up pre-commit...${NC}"

# Create .pre-commit-config.yaml if not exists
if [ ! -f ".pre-commit-config.yaml" ]; then
    echo -e "${YELLOW}Creating .pre-commit-config.yaml...${NC}"
    cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.5
    hooks:
      - id: ruff
        args: [--fix]
  
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
        language_version: python3.11
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        exclude: ^(tests/|docs/)
  
  - repo: https://github.com/PyCQA/bandit
    rev: '1.7.5'
    hooks:
      - id: bandit
        args: ['-ll', '-i']
        exclude: ^(tests/|docs/)
EOF
fi

# Install pre-commit hooks
pre-commit install

# Setup git hooks
echo -e "\n${BLUE}Setting up git hooks...${NC}"

# Copy AI pre-commit hook
if [ -f "scripts/ai-pre-commit" ]; then
    echo "Installing AI pre-commit hook..."
    cp scripts/ai-pre-commit .git/hooks/ai-pre-commit
    chmod +x .git/hooks/ai-pre-commit
    
    # Create wrapper that calls both hooks
    cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Wrapper to call both pre-commit and AI review

# Check for AI agent commit
if [ -n "$AI_AGENT_COMMIT" ]; then
    exec .git/hooks/ai-pre-commit
else
    # Regular pre-commit
    exec pre-commit run --all-files
fi
EOF
    chmod +x .git/hooks/pre-commit
    echo -e "${GREEN}✅ Git hooks installed${NC}"
else
    echo -e "${YELLOW}⚠️  AI pre-commit script not found${NC}"
fi

# Create pyproject.toml if not exists
if [ ! -f "pyproject.toml" ]; then
    echo -e "\n${BLUE}Creating pyproject.toml...${NC}"
    cat > pyproject.toml << EOF
[tool.ruff]
line-length = 88
target-version = "py311"
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "N",    # pep8-naming
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "DTZ",  # flake8-datetimez
    "ISC",  # flake8-implicit-str-concat
    "PIE",  # flake8-pie
    "RET",  # flake8-return
    "SIM",  # flake8-simplify
    "PTH",  # flake8-use-pathlib
]
ignore = ["E501"]  # Line too long - handled by black

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]  # Unused imports in init files

[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  # Directories
  \.git
  | \.mypy_cache
  | \.pytest_cache
  | __pycache__
  | venv
  | build
  | dist
)/
'''

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
strict_optional = true

[tool.bandit]
exclude_dirs = ["tests", "venv"]
skips = ["B101"]  # Skip assert_used test

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_functions = ["test_*"]
addopts = "-ra -q --strict-markers"
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
]

[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*", "*/venv/*", "*/__pycache__/*"]

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
fail_under = 80
EOF
fi

# Create AI review config
echo -e "\n${BLUE}Creating AI review configuration...${NC}"
cat > .ai-review-config.yaml << EOF
# AI Code Review Configuration
max_iterations: 5
auto_fix_enabled: true

checks:
  - ruff
  - black
  - mypy
  - bandit
  - pytest
  
thresholds:
  coverage_min: 80
  complexity_max: 10
  
custom_checks:
  dutch_docstrings: true
  sql_injection_prevention: true
  streamlit_patterns: true
  
ai_agents:
  claude:
    model: claude-3-opus-20240229
    temperature: 0.3
  github_copilot:
    enabled: true
  manual:
    enabled: true
    
reporting:
  save_reports: true
  report_path: "review_reports/"
  metrics_tracking: true
  dashboard_enabled: true
EOF

# Create directories
echo -e "\n${BLUE}Creating directories...${NC}"
mkdir -p review_reports
mkdir -p .bmad-core/{tasks,templates,checklists,data}

# Test the setup
echo -e "\n${BLUE}Testing setup...${NC}"

# Test imports
echo "Testing tool availability..."
python3 -c "import ruff" && echo "✅ Ruff" || echo "❌ Ruff"
python3 -c "import black" && echo "✅ Black" || echo "❌ Black"
python3 -c "import mypy" && echo "✅ MyPy" || echo "❌ MyPy"
python3 -c "import bandit" && echo "✅ Bandit" || echo "❌ Bandit"
python3 -c "import pandas" && echo "✅ Pandas" || echo "❌ Pandas"
python3 -c "import streamlit" && echo "✅ Streamlit" || echo "❌ Streamlit"

# Make scripts executable
echo -e "\n${BLUE}Making scripts executable...${NC}"
chmod +x scripts/ai_code_reviewer.py
chmod +x scripts/ai_metrics_tracker.py

# Final message
echo -e "\n${GREEN}✅ AI Code Review System Setup Complete!${NC}"
echo -e "\n${BLUE}Usage:${NC}"
echo "1. For AI commits: AI_AGENT_COMMIT=1 git commit -m 'AI: message'"
echo "2. Run manual review: python scripts/ai_code_reviewer.py"
echo "3. View metrics: python scripts/ai_metrics_tracker.py dashboard"
echo "4. For Quinn: *execute-code-review"
echo -e "\n${YELLOW}Note: Activate the virtual environment with: source venv/bin/activate${NC}"