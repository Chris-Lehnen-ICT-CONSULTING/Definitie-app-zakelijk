# AI Code Reviewer 🤖

Automated code review system with AI integration and BMAD Method support.

## Features (v2.0.0)

- 🔍 **Multi-tool Integration**: Ruff, Black, MyPy, Bandit
- 🔄 **Auto-fix Loop**: Up to 5 iterations of automatic fixes  
- 🛡️ **Enhanced Security Scanning**: Improved SQL injection detection with context-aware false positive filtering
- 🎯 **Framework Support**: Streamlit, Django, Flask, Generic
- 🎭 **Complete BMAD Integration**: Post-edit hooks, agent detection, seamless workflow
- 🔗 **Universal Post-Edit Hooks**: Automatic quality checks after any BMAD agent code changes
- 🤖 **AI Agent Auto-Detection**: Claude Code, GitHub Copilot, BMAD agents
- 📊 **Metrics Tracking**: Performance and quality metrics
- ⚡ **Fast Setup**: One-command project setup
- 🧪 **Hook Testing**: Built-in testing for BMAD post-edit functionality

## Quick Start

### Installation

```bash
pip install ai-code-reviewer
```

### Basic Usage

```bash
# Run code review in current project
ai-code-review

# Setup project for AI code review
ai-code-review setup --install-templates --setup-hooks

# Setup BMAD integration  
ai-code-review init-bmad
```

### Configuration

Create `.ai-review-config.yaml` in your project root:

```yaml
max_iterations: 5
source_dirs: ["src/"]
framework: "streamlit"  # streamlit, django, flask, generic
docstring_language: "dutch"  # dutch, english
custom_checks: true
custom_check_types:
  - "sql_safety"
  - "framework_patterns"
```

## Advanced Usage

### CLI Commands

```bash
# Run with specific settings
ai-code-review --max-iterations 3 --framework django

# Update to latest version
ai-code-review update

# Check for updates only
ai-code-review update --check-only

# Setup git hooks
ai-code-review setup --setup-hooks

# BMAD Method integration
ai-code-review init-bmad

# Test BMAD post-edit hook (v2.0.0)
ai-code-review test-hook --ai-agent Quinn

# Run review with specific AI agent
ai-code-review --ai-agent Claude --max-iterations 5
```

### Programmatic Usage

```python
from ai_code_reviewer import AICodeReviewer
import asyncio

# Configure reviewer
config = {
    'max_iterations': 5,
    'source_dirs': ['src/'],
    'framework': 'streamlit',
    'custom_checks': True
}

reviewer = AICodeReviewer(
    project_root="./my-project",
    config=config
)

# Run review
result = asyncio.run(reviewer.run_review_cycle())

if result.passed:
    print("✅ All checks passed!")
else:
    print(f"❌ Found {len(result.issues)} issues")
```

## Framework Support

### Streamlit Projects
- Session state usage patterns
- Widget interaction checks  
- Performance optimizations

### Django Projects
- Model validation
- View security patterns
- Template safety checks

### Flask Projects
- Route security
- Template injection prevention
- Database query validation

### Generic Projects
- Code quality standards
- Security best practices
- Documentation requirements

## BMAD Method Integration (v2.0.0)

The package provides complete integration with the BMAD Method including universal post-edit hooks:

```bash
# Setup BMAD integration
ai-code-review init-bmad

# Test post-edit hook functionality
ai-code-review test-hook --ai-agent James

# In BMAD, use the task:
*execute-code-review
```

### Universal Post-Edit Hooks

All BMAD agents now automatically trigger code review after Edit/MultiEdit operations:

- **James** (dev): Triggers review after code implementations
- **Winston** (architect): Triggers review after architectural changes  
- **Quinn** (qa): Built-in *auto-review command + post-edit hooks
- **All other agents**: Automatic quality checks after code modifications

### AI Agent Auto-Detection (Enhanced)

The system automatically detects AI agents:
- **Claude Code**: Detected as "claude" or "Claude"
- **GitHub Copilot**: Detected as "copilot" 
- **BMAD Agents**: Quinn, James, Winston, Sarah, Marcus, Taylor, Alex, Jordan
- **Environment Variables**: `AI_AGENT_NAME`, `BMAD_AGENT_NAME`
- **Default**: Falls back to "manual"

## Configuration Options

### Core Settings
- `max_iterations`: Maximum auto-fix iterations (default: 5)
- `source_dirs`: Directories to scan (default: ["src/"])
- `framework`: Target framework for specialized checks
- `custom_checks`: Enable custom security/quality checks

### Custom Checks
- `sql_safety`: SQL injection vulnerability detection
- `docstring_language`: Enforce docstring language consistency
- `framework_patterns`: Framework-specific pattern validation

### Enhanced False Positive Filtering (v2.0.0)
Multi-layer intelligent filtering prevents false positives in:
- Logging statements (logger., log., logging.)
- Error messages (raise, exception handling)
- UI display strings (st.write, st.success, print statements)
- Debug output (debug_info, log_message)
- Context-aware detection (surrounding code analysis)
- Extended context window (100+ characters before/after)

## Git Integration

### Pre-commit Hooks

```bash
# Install pre-commit hooks
ai-code-review setup --setup-hooks

# Manual pre-commit setup
pip install pre-commit
pre-commit install
```

### GitHub Actions

```yaml
name: AI Code Review
on: [push, pull_request]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.8'
      - name: Install AI Code Reviewer
        run: pip install ai-code-reviewer
      - name: Run Code Review
        run: ai-code-review --ai-agent "github-actions"
```

## Auto-Updates

The package supports automatic updates:

```bash
# Check for updates
ai-code-review update --check-only

# Update to latest version  
ai-code-review update

# Auto-update notifications
# Shown when new versions are available
```

## Metrics and Reporting

Each review generates:
- **Review Report**: Detailed findings in `review_report.md`
- **Metrics Tracking**: Performance and quality metrics
- **Exit Codes**: 0 for success, 1 for failure

### Sample Report

```markdown
# 🤖 AI Code Review Report

**Date**: 2024-01-15 10:30:00
**Status**: ✅ PASSED  
**Iterations**: 3
**Auto-fixes Applied**: 7
**Duration**: 12.3 seconds

## Metrics
- Total issues found: 12
- Issues auto-fixed: 7
- Review efficiency: 58.3%
```

## Troubleshooting

### Common Issues

**Tools not found**:
```bash
pip install ruff black mypy bandit
```

**Config file issues**:
```bash
ai-code-review setup --install-templates
```

**Git hooks not working**:
```bash
ai-code-review setup --setup-hooks
```

### Verbose Output

```bash
ai-code-review --verbose
```

## 🏗️ Package Development & Distribution

### Build Package

```bash
# Install build dependencies
pip install build twine

# Build package
python -m build

# Test locally
pip install dist/ai_code_reviewer-2.0.0-py3-none-any.whl

# Upload to PyPI
python -m twine upload dist/*
```

### Using Makefile (Recommended)

```bash
# Quick build and test
make quick-test

# Full quality checks
make check-all

# Upload to Test PyPI
make upload-test

# Upload to PyPI
make upload
```

### For End Users

```bash
# Install from PyPI
pip install ai-code-reviewer

# Verify installation
ai-code-review --version

# Quick setup
ai-code-review setup --install-templates
```

See [INSTALL.md](INSTALL.md) for detailed installation instructions and [BUILD.md](BUILD.md) for complete build documentation.

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Changelog

### v2.0.0 (2025-08-15)
- 🎭 **Complete BMAD Integration**: Universal post-edit hooks voor alle agents
- 🛡️ **Enhanced Security**: Verbeterde SQL injection detectie met context-aware filtering
- 🤖 **AI Agent Auto-Detection**: Automatische detectie van Claude, Copilot, BMAD agents
- 🔗 **Post-Edit Hooks**: Alle BMAD agents triggeren automatisch code review na wijzigingen
- 🧪 **Hook Testing**: `test-hook` commando voor BMAD functionaliteit testing
- 📊 **Extended Context**: Verbeterde false positive filtering met 100+ character context
- ⚙️ **Multi-layer Detection**: Specificke context checks voor UI, logging, error handling
- 🔧 **Agent Integration**: Support voor Quinn *auto-review command
- 📝 **Enhanced Reporting**: Uitgebreide feedback in Nederlands
- 🚀 **Improved Performance**: Optimized review cycle met betere auto-fix detection

### v1.0.0
- Initial release
- Multi-tool integration
- BMAD Method support
- Auto-update functionality
- Framework-specific checks